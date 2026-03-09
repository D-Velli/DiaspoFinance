"""Rotation order logic for tontines.

Handles random and manual ordering, half-hand pairing,
and position assignment based on hands count.

Position rules:
- 1 hand  → 1 turn position
- 2 hands → 2 consecutive positions
- ½ hand  → paired with another ½ hand on the same position
- Total turns = sum of all hands (integer)
"""

import random
import uuid
from decimal import Decimal

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, TontineNotDraftError
from app.tontine.models import (
    MemberRole,
    MemberStatus,
    Tontine,
    TontineMember,
    TontineStatus,
)

logger = structlog.get_logger()


class OrphanHalfHandError(Exception):
    """Raised when an odd number of half-hand members exists."""

    def __init__(self, member_ids: list[uuid.UUID]):
        self.member_ids = member_ids
        super().__init__(f"Orphan half-hand members: {member_ids}")


async def _get_tontine_and_check(
    db: AsyncSession, tontine_id: uuid.UUID, user_id: uuid.UUID
) -> Tontine:
    """Load tontine and verify it's draft + user is organizer."""
    result = await db.execute(select(Tontine).where(Tontine.id == tontine_id))
    tontine = result.scalar_one_or_none()
    if not tontine:
        from app.core.exceptions import NotFoundError

        raise NotFoundError(message="Tontine not found")

    if tontine.status != TontineStatus.DRAFT:
        raise TontineNotDraftError()

    # Check organizer role
    result = await db.execute(
        select(TontineMember)
        .where(TontineMember.tontine_id == tontine_id)
        .where(TontineMember.user_id == user_id)
        .where(TontineMember.role == MemberRole.ORGANIZER)
    )
    if not result.scalar_one_or_none():
        raise ForbiddenError(message="Only the organizer can manage rotation")

    return tontine


async def get_active_members(
    db: AsyncSession, tontine_id: uuid.UUID
) -> list[TontineMember]:
    """Get all active members of a tontine."""
    result = await db.execute(
        select(TontineMember)
        .where(TontineMember.tontine_id == tontine_id)
        .where(TontineMember.status == MemberStatus.ACTIVE)
        .order_by(TontineMember.joined_at)
    )
    return list(result.scalars().all())


def assign_positions(members: list[TontineMember]) -> dict[uuid.UUID, int]:
    """Assign turn positions based on hands.

    Returns a dict of {member_id: turn_position}.
    Half-hand members are paired and share the same position.
    Two-hand members get two consecutive positions (stored as the first one).
    """
    half_hand_members = [m for m in members if m.hands == Decimal("0.5")]
    one_hand_members = [m for m in members if m.hands == Decimal("1")]
    two_hand_members = [m for m in members if m.hands == Decimal("2")]

    # Check for orphan half-hands
    if len(half_hand_members) % 2 != 0:
        orphan_ids = [m.id for m in half_hand_members]
        raise OrphanHalfHandError(orphan_ids)

    positions: dict[uuid.UUID, int] = {}
    current_pos = 1

    # Build ordered list: iterate through members in their given order
    for member in members:
        if member.id in positions:
            continue  # already assigned (half-hand partner)

        if member.hands == Decimal("0.5"):
            # Find the next unassigned half-hand partner
            partner = next(
                (m for m in half_hand_members if m.id != member.id and m.id not in positions),
                None,
            )
            positions[member.id] = current_pos
            if partner:
                positions[partner.id] = current_pos
            current_pos += 1

        elif member.hands == Decimal("2"):
            positions[member.id] = current_pos
            current_pos += 2  # occupies 2 consecutive positions

        else:  # 1 hand
            positions[member.id] = current_pos
            current_pos += 1

    return positions


async def generate_random_rotation(
    db: AsyncSession, tontine_id: uuid.UUID, user_id: uuid.UUID
) -> list[dict]:
    """Generate a random rotation order for a draft tontine."""
    await _get_tontine_and_check(db, tontine_id, user_id)
    members = await get_active_members(db, tontine_id)

    # Shuffle members randomly
    shuffled = list(members)
    random.shuffle(shuffled)

    positions = assign_positions(shuffled)

    # Update database
    for member in members:
        member.turn_position = positions[member.id]
    await db.commit()

    logger.info("rotation.random_generated", tontine_id=str(tontine_id), turns=len(set(positions.values())))

    return await get_rotation(db, tontine_id)


async def set_manual_rotation(
    db: AsyncSession,
    tontine_id: uuid.UUID,
    user_id: uuid.UUID,
    member_order: list[uuid.UUID],
) -> list[dict]:
    """Set a manual rotation order. member_order is the desired sequence of member IDs."""
    await _get_tontine_and_check(db, tontine_id, user_id)
    members = await get_active_members(db, tontine_id)

    member_map = {m.id: m for m in members}

    # Validate all provided IDs are active members
    for mid in member_order:
        if mid not in member_map:
            from app.core.exceptions import ValidationError

            raise ValidationError(message=f"Member {mid} is not an active member of this tontine")

    # Validate all active members are included
    missing = set(member_map.keys()) - set(member_order)
    if missing:
        from app.core.exceptions import ValidationError

        raise ValidationError(
            message=f"Missing {len(missing)} active member(s) from rotation order"
        )

    # Reorder members according to the provided order
    ordered = [member_map[mid] for mid in member_order]
    positions = assign_positions(ordered)

    # Update database
    for member in members:
        member.turn_position = positions.get(member.id)
    await db.commit()

    logger.info("rotation.manual_set", tontine_id=str(tontine_id))

    return await get_rotation(db, tontine_id)


async def get_rotation(db: AsyncSession, tontine_id: uuid.UUID) -> list[dict]:
    """Get the current rotation order for a tontine."""
    members = await get_active_members(db, tontine_id)

    # Group by position
    assigned = [m for m in members if m.turn_position is not None]
    assigned.sort(key=lambda m: m.turn_position)  # type: ignore[arg-type]

    total_hands = sum(m.hands for m in members)

    result = []
    seen_positions: set[int] = set()

    for member in assigned:
        pos = member.turn_position
        if pos in seen_positions:
            # Half-hand partner — find the existing entry and add partner
            for entry in result:
                if entry["position"] == pos:
                    entry["members"].append({
                        "id": str(member.id),
                        "user_id": str(member.user_id),
                        "hands": float(member.hands),
                    })
                    break
        else:
            seen_positions.add(pos)
            entry = {
                "position": pos,
                "members": [{
                    "id": str(member.id),
                    "user_id": str(member.user_id),
                    "hands": float(member.hands),
                }],
            }
            # For 2-hand members, mark the second position too
            if member.hands == Decimal("2"):
                entry["occupies_positions"] = [pos, pos + 1]
            result.append(entry)

    return result


def check_half_hand_pairing(members: list[TontineMember]) -> dict:
    """Check if half-hand members can be properly paired.

    Returns a summary with pairing status and any orphan alerts.
    """
    half_hand_members = [m for m in members if m.hands == Decimal("0.5")]
    total_half = len(half_hand_members)
    pairs = total_half // 2
    has_orphan = total_half % 2 != 0

    return {
        "half_hand_count": total_half,
        "pairs": pairs,
        "has_orphan": has_orphan,
        "orphan_member_id": str(half_hand_members[-1].id) if has_orphan else None,
        "total_turns": int(sum(m.hands for m in members)),
    }
