"""Cycle lifecycle service — pre-start checks and cycle start."""

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import DiaspoFinanceError, ForbiddenError
from app.tontine.calendar import generate_rounds
from app.tontine.models import (
    MemberRole,
    MemberStatus,
    Tontine,
    TontineMember,
    TontineRound,
    TontineStatus,
)
from app.tontine.schemas import PreStartCheck, PreStartResponse
from app.tontine.service import get_tontine
from app.tontine.state_machine import can_transition

logger = structlog.get_logger()


async def _get_active_members_sorted(
    db: AsyncSession, tontine_id: uuid.UUID
) -> list[TontineMember]:
    """Get active/preview members sorted by turn_position."""
    result = await db.execute(
        select(TontineMember)
        .where(TontineMember.tontine_id == tontine_id)
        .where(TontineMember.status.in_([MemberStatus.ACTIVE, MemberStatus.PREVIEW]))
        .order_by(TontineMember.turn_position.asc().nullslast())
    )
    return list(result.scalars().all())


def _run_checks(
    tontine: Tontine, members: list[TontineMember]
) -> PreStartResponse:
    """Pure validation logic — no DB access."""
    blockers: list[PreStartCheck] = []
    warnings: list[PreStartCheck] = []

    if tontine.status != TontineStatus.DRAFT:
        blockers.append(PreStartCheck(
            code="NOT_DRAFT",
            message="La tontine doit être en brouillon pour démarrer",
            severity="error",
        ))

    if len(members) < 2:
        blockers.append(PreStartCheck(
            code="MINIMUM_MEMBERS",
            message=f"Au moins 2 membres requis ({len(members)} actuellement)",
            severity="error",
        ))

    unpositioned = [m for m in members if m.turn_position is None]
    if unpositioned:
        blockers.append(PreStartCheck(
            code="ORDER_NOT_DEFINED",
            message=f"{len(unpositioned)} membre(s) sans position dans la rotation",
            severity="error",
        ))

    half_hands = [m for m in members if m.hands == Decimal("0.5")]
    if len(half_hands) % 2 != 0:
        blockers.append(PreStartCheck(
            code="ORPHAN_HANDS",
            message=f"Nombre impair de demi-mains ({len(half_hands)}). Résoudre avant de démarrer.",
            severity="error",
        ))

    if 2 <= len(members) <= 3:
        warnings.append(PreStartCheck(
            code="FEW_MEMBERS",
            message=f"Seulement {len(members)} membres. Le risque est plus élevé.",
            severity="warning",
        ))

    if not tontine.reserve_enabled:
        warnings.append(PreStartCheck(
            code="NO_RESERVE",
            message="Aucune réserve de sécurité activée.",
            severity="warning",
        ))

    return PreStartResponse(
        can_start=len(blockers) == 0,
        blockers=blockers,
        warnings=warnings,
    )


async def pre_start_checks(
    db: AsyncSession, tontine_id: uuid.UUID
) -> PreStartResponse:
    """Run all pre-start validations. Returns blockers + warnings."""
    tontine = await get_tontine(db, tontine_id)
    members = await _get_active_members_sorted(db, tontine_id)
    return _run_checks(tontine, members)


async def start_cycle(
    db: AsyncSession,
    tontine_id: uuid.UUID,
    user_id: uuid.UUID,
    cycle_start_date: date | None = None,
) -> tuple[Tontine, list[TontineRound]]:
    """Start the tontine cycle atomically.

    1. Verify organizer
    2. Run pre-start checks
    3. Generate rounds
    4. Transition status draft → active
    5. Lock rotation order
    """
    # 1. Load tontine + members once
    tontine = await get_tontine(db, tontine_id)
    members = await _get_active_members_sorted(db, tontine_id)

    # 2. Verify organizer
    is_organizer = any(
        m.user_id == user_id and m.role == MemberRole.ORGANIZER
        for m in members
    )
    if not is_organizer:
        raise ForbiddenError(message="Seul l'organisateur peut démarrer le cycle")

    # 3. Pre-start checks (reuse loaded data)
    checks = _run_checks(tontine, members)
    if not checks.can_start:
        raise DiaspoFinanceError(
            code="START_BLOCKED",
            status_code=400,
            message="Conditions de démarrage non remplies",
        )

    # 4. Validate state transition
    if not can_transition(tontine.status, TontineStatus.ACTIVE):
        raise DiaspoFinanceError(
            code="INVALID_TRANSITION",
            status_code=409,
            message=f"Cannot transition from {tontine.status.value} to active",
        )

    # 5. Determine start date
    start = cycle_start_date or (date.today() + timedelta(days=1))
    if start < date.today():
        raise DiaspoFinanceError(
            code="INVALID_DATE",
            status_code=400,
            message="La date de démarrage doit être aujourd'hui ou dans le futur",
        )

    # 6. Generate rounds and persist
    rounds = generate_rounds(tontine, members, start)
    db.add_all(rounds)

    # 7. Update tontine
    tontine.status = TontineStatus.ACTIVE
    tontine.order_locked_at = datetime.now(timezone.utc)
    tontine.cycle_start_date = start

    await db.commit()
    await db.refresh(tontine)

    # 8. Re-query rounds with beneficiary eager-loaded (avoids N+1)
    rounds = await list_rounds(db, tontine_id)

    logger.info(
        "tontine.cycle_started",
        tontine_id=str(tontine_id),
        total_rounds=len(rounds),
        start_date=start.isoformat(),
        started_by=str(user_id),
    )

    return tontine, rounds


async def list_rounds(
    db: AsyncSession, tontine_id: uuid.UUID
) -> list[TontineRound]:
    """List all rounds for a tontine, ordered by round_number.

    Eager-loads beneficiary to avoid N+1 queries.
    """
    result = await db.execute(
        select(TontineRound)
        .options(selectinload(TontineRound.beneficiary))
        .where(TontineRound.tontine_id == tontine_id)
        .order_by(TontineRound.round_number)
    )
    return list(result.scalars().all())
