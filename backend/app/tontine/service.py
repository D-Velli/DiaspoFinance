import secrets
import uuid
from decimal import Decimal

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    DiaspoFinanceError,
    ForbiddenError,
    NotFoundError,
    PlafondExceededError,
    TontineNotDraftError,
)
from app.tontine.models import (
    MemberRole,
    MemberStatus,
    Tontine,
    TontineMember,
    TontineStatus,
)
from app.tontine.schemas import TontineCreate, TontineUpdate
from app.user.models import User

logger = structlog.get_logger()


def _frequency_per_month(frequency: str) -> int:
    return {"weekly": 4, "biweekly": 2, "monthly": 1}[frequency]


async def create_tontine(db: AsyncSession, user: User, data: TontineCreate) -> Tontine:
    # Check max tontines per user
    count_q = select(func.count()).select_from(Tontine).where(Tontine.created_by == user.id)
    user_tontine_count = (await db.execute(count_q)).scalar() or 0
    if user_tontine_count >= settings.MAX_TONTINES_PER_USER:
        raise PlafondExceededError(
            message=f"Maximum {settings.MAX_TONTINES_PER_USER} tontines per user"
        )

    # Check hand amount ceiling
    if data.hand_amount_cents > settings.MAX_CONTRIBUTION_CENTS:
        raise PlafondExceededError(
            message=f"Hand amount cannot exceed {settings.MAX_CONTRIBUTION_CENTS // 100} CAD"
        )

    # Check monthly group ceiling if max_members defined
    if data.max_members:
        freq_mult = _frequency_per_month(data.frequency.value)
        monthly_total = data.hand_amount_cents * data.max_members * freq_mult
        if monthly_total > settings.MAX_MONTHLY_GROUP_CENTS:
            raise PlafondExceededError(
                message="Monthly group total exceeds regulatory ceiling of "
                f"{settings.MAX_MONTHLY_GROUP_CENTS // 100} CAD"
            )

    tontine = Tontine(
        name=data.name,
        hand_amount_cents=data.hand_amount_cents,
        frequency=data.frequency,
        start_date=data.start_date,
        max_members=data.max_members,
        max_pot_cents=data.max_pot_cents,
        status=TontineStatus.DRAFT,
        reserve_enabled=data.reserve_enabled,
        reserve_percentage=data.reserve_percentage if data.reserve_enabled else None,
        created_by=user.id,
    )
    db.add(tontine)
    await db.flush()

    # Add creator as organizer member
    member = TontineMember(
        user_id=user.id,
        tontine_id=tontine.id,
        role=MemberRole.ORGANIZER,
        status=MemberStatus.ACTIVE,
        hands=data.organizer_hands,
    )
    db.add(member)
    await db.commit()
    await db.refresh(tontine)

    logger.info(
        "tontine.created",
        tontine_id=str(tontine.id),
        name=tontine.name,
        created_by=str(user.id),
        hand_amount_cents=tontine.hand_amount_cents,
    )

    return tontine


async def get_tontine(db: AsyncSession, tontine_id: uuid.UUID) -> Tontine:
    result = await db.execute(select(Tontine).where(Tontine.id == tontine_id))
    tontine = result.scalar_one_or_none()
    if not tontine:
        raise NotFoundError(message="Tontine not found")
    return tontine


async def list_user_tontines(db: AsyncSession, user_id: uuid.UUID) -> list[Tontine]:
    result = await db.execute(
        select(Tontine)
        .join(TontineMember)
        .where(TontineMember.user_id == user_id)
        .order_by(Tontine.created_at.desc())
    )
    return list(result.scalars().all())


async def update_tontine(
    db: AsyncSession, tontine_id: uuid.UUID, user: User, data: TontineUpdate
) -> Tontine:
    tontine = await get_tontine(db, tontine_id)

    if tontine.status != TontineStatus.DRAFT:
        raise TontineNotDraftError()

    if tontine.created_by != user.id:
        raise ForbiddenError(message="Only the organizer can modify this tontine")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tontine, field, value)

    await db.commit()
    await db.refresh(tontine)

    logger.info("tontine.updated", tontine_id=str(tontine.id))
    return tontine


async def get_batch_stats(
    db: AsyncSession, tontines: list[Tontine]
) -> dict[uuid.UUID, dict]:
    """Get stats for multiple tontines in a single query (avoids N+1)."""
    if not tontines:
        return {}

    tontine_ids = [t.id for t in tontines]
    hand_map = {t.id: t.hand_amount_cents for t in tontines}

    result = await db.execute(
        select(
            TontineMember.tontine_id,
            func.count(TontineMember.id),
            func.coalesce(func.sum(TontineMember.hands), 0),
        )
        .where(TontineMember.tontine_id.in_(tontine_ids))
        .where(TontineMember.status == MemberStatus.ACTIVE)
        .group_by(TontineMember.tontine_id)
    )

    stats: dict[uuid.UUID, dict] = {}
    for row in result:
        tid = row[0]
        member_count = row[1]
        total_hands = Decimal(str(row[2]))
        stats[tid] = {
            "member_count": member_count,
            "total_hands": total_hands,
            "pot_per_turn_cents": int(total_hands * hand_map[tid]),
        }

    empty = {"member_count": 0, "total_hands": Decimal("0"), "pot_per_turn_cents": 0}
    for t in tontines:
        if t.id not in stats:
            stats[t.id] = empty

    return stats


async def get_tontine_members(
    db: AsyncSession, tontine_id: uuid.UUID
) -> list[TontineMember]:
    result = await db.execute(
        select(TontineMember).where(TontineMember.tontine_id == tontine_id)
    )
    return list(result.scalars().all())


async def get_tontine_stats(
    db: AsyncSession, tontine_id: uuid.UUID
) -> dict:
    """Get member_count, total_hands, pot_per_turn for a tontine."""
    result = await db.execute(
        select(
            func.count(TontineMember.id),
            func.coalesce(func.sum(TontineMember.hands), 0),
        )
        .where(TontineMember.tontine_id == tontine_id)
        .where(TontineMember.status == MemberStatus.ACTIVE)
    )
    row = result.one()
    member_count = row[0]
    total_hands = Decimal(str(row[1]))

    tontine = await get_tontine(db, tontine_id)
    pot_per_turn_cents = int(total_hands * tontine.hand_amount_cents)

    return {
        "member_count": member_count,
        "total_hands": total_hands,
        "pot_per_turn_cents": pot_per_turn_cents,
    }


async def get_capacity(db: AsyncSession, tontine_id: uuid.UUID) -> dict:
    """Get full capacity info: hands used, remaining, turns, estimated duration."""
    tontine = await get_tontine(db, tontine_id)
    stats = await get_tontine_stats(db, tontine_id)

    total_hands = stats["total_hands"]
    total_turns = int(total_hands)

    # Remaining capacity based on max_pot
    if tontine.max_pot_cents:
        max_hands = Decimal(tontine.max_pot_cents) / Decimal(tontine.hand_amount_cents)
        hands_remaining = max(Decimal("0"), max_hands - total_hands)
    else:
        max_hands = None
        hands_remaining = None

    # Estimated duration in weeks
    freq_weeks = {"weekly": 1, "biweekly": 2, "monthly": 4}
    weeks_per_turn = freq_weeks.get(tontine.frequency.value, 4)
    estimated_weeks = total_turns * weeks_per_turn

    # Determine if tontine is full
    is_full = False
    if tontine.max_members and stats["member_count"] >= tontine.max_members:
        is_full = True
    if hands_remaining is not None and hands_remaining <= Decimal("0"):
        is_full = True

    return {
        **stats,
        "max_hands": float(max_hands) if max_hands is not None else None,
        "hands_remaining": float(hands_remaining) if hands_remaining is not None else None,
        "max_members": tontine.max_members,
        "total_turns": total_turns,
        "estimated_weeks": estimated_weeks,
        "hand_amount_cents": tontine.hand_amount_cents,
        "frequency": tontine.frequency.value,
        "is_full": is_full,
    }


async def validate_join_capacity(
    db: AsyncSession, tontine_id: uuid.UUID, requested_hands: Decimal
) -> dict:
    """Check if a member with requested_hands can join.

    Returns {"can_join": bool, "reason": str | None}.
    """
    tontine = await get_tontine(db, tontine_id)
    stats = await get_tontine_stats(db, tontine_id)
    total_hands = stats["total_hands"]

    # Check max_members
    if tontine.max_members and stats["member_count"] >= tontine.max_members:
        return {"can_join": False, "reason": "TONTINE_FULL"}

    # Check max_pot capacity
    if tontine.max_pot_cents:
        max_hands = Decimal(tontine.max_pot_cents) / Decimal(tontine.hand_amount_cents)
        if total_hands + requested_hands > max_hands:
            return {
                "can_join": False,
                "reason": "INSUFFICIENT_CAPACITY",
                "hands_remaining": float(max_hands - total_hands),
            }

    # Check monthly group ceiling
    freq_mult = _frequency_per_month(tontine.frequency.value)
    new_total_hands = total_hands + requested_hands
    monthly_total = int(new_total_hands * tontine.hand_amount_cents * freq_mult)
    if monthly_total > settings.MAX_MONTHLY_GROUP_CENTS:
        return {"can_join": False, "reason": "MONTHLY_LIMIT_EXCEEDED"}

    return {"can_join": True, "reason": None}


def _generate_invite_code() -> str:
    """Generate a short, URL-safe invite code."""
    return secrets.token_urlsafe(8)  # ~11 chars, e.g. "aB3x_Kf2mQ0"


async def generate_invite_link(
    db: AsyncSession, tontine_id: uuid.UUID, user_id: uuid.UUID
) -> str:
    """Generate or return existing invite code. Organizer only."""
    tontine = await get_tontine(db, tontine_id)

    if tontine.created_by != user_id:
        raise ForbiddenError(message="Only the organizer can generate invite links")

    if tontine.invite_code:
        return tontine.invite_code

    # Generate unique code with retry
    for _ in range(5):
        code = _generate_invite_code()
        existing = await db.execute(
            select(Tontine.id).where(Tontine.invite_code == code)
        )
        if not existing.scalar_one_or_none():
            tontine.invite_code = code
            await db.commit()
            await db.refresh(tontine)
            logger.info("invite.generated", tontine_id=str(tontine_id), code=code)
            return code

    raise DiaspoFinanceError(message="Failed to generate unique invite code")


async def regenerate_invite_link(
    db: AsyncSession, tontine_id: uuid.UUID, user_id: uuid.UUID
) -> str:
    """Regenerate a new invite code, invalidating the old one."""
    tontine = await get_tontine(db, tontine_id)

    if tontine.created_by != user_id:
        raise ForbiddenError(message="Only the organizer can regenerate invite links")

    for _ in range(5):
        code = _generate_invite_code()
        existing = await db.execute(
            select(Tontine.id).where(Tontine.invite_code == code)
        )
        if not existing.scalar_one_or_none():
            tontine.invite_code = code
            await db.commit()
            await db.refresh(tontine)
            logger.info("invite.regenerated", tontine_id=str(tontine_id), code=code)
            return code

    raise DiaspoFinanceError(message="Failed to generate unique invite code")


async def get_tontine_by_invite_code(db: AsyncSession, code: str) -> Tontine:
    """Get tontine by invite code (public endpoint).

    Only returns tontines in draft or active status.
    Cancelled/completed tontines return 404.
    """
    result = await db.execute(
        select(Tontine)
        .where(Tontine.invite_code == code)
        .where(Tontine.status.in_([TontineStatus.DRAFT, TontineStatus.ACTIVE]))
    )
    tontine = result.scalar_one_or_none()
    if not tontine:
        raise NotFoundError(message="Invalid or expired invite link")
    return tontine


async def is_member(db: AsyncSession, tontine_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(TontineMember.id)
        .where(TontineMember.tontine_id == tontine_id)
        .where(TontineMember.user_id == user_id)
    )
    return result.scalar_one_or_none() is not None
