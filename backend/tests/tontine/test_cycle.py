"""Tests for cycle service — pre-start checks and start_cycle."""

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import DiaspoFinanceError, ForbiddenError
from app.tontine.models import MemberRole, MemberStatus, TontineStatus


def _make_tontine(status=TontineStatus.DRAFT, reserve=False):
    t = MagicMock()
    t.id = uuid.uuid4()
    t.status = status
    t.reserve_enabled = reserve
    t.hand_amount_cents = 20000
    t.frequency = MagicMock()
    t.frequency.value = "monthly"
    return t


def _make_member(hands=Decimal("1"), position=1, role=MemberRole.ORGANIZER):
    m = MagicMock()
    m.id = uuid.uuid4()
    m.user_id = uuid.uuid4()
    m.hands = hands
    m.turn_position = position
    m.role = role
    m.status = MemberStatus.ACTIVE
    return m


# --- Pre-start checks ---


@pytest.mark.asyncio
@patch("app.tontine.cycle_service.get_tontine")
@patch("app.tontine.cycle_service._get_active_members_sorted")
async def test_pre_start_all_ok(mock_members, mock_get):
    from app.tontine.cycle_service import pre_start_checks

    tontine = _make_tontine(reserve=True)
    mock_get.return_value = tontine
    mock_members.return_value = [
        _make_member(Decimal("1"), 1),
        _make_member(Decimal("1"), 2),
        _make_member(Decimal("1"), 3),
        _make_member(Decimal("1"), 4),
    ]

    db = AsyncMock()
    result = await pre_start_checks(db, tontine.id)

    assert result.can_start is True
    assert len(result.blockers) == 0


@pytest.mark.asyncio
@patch("app.tontine.cycle_service.get_tontine")
@patch("app.tontine.cycle_service._get_active_members_sorted")
async def test_pre_start_not_draft_blocker(mock_members, mock_get):
    from app.tontine.cycle_service import pre_start_checks

    tontine = _make_tontine(status=TontineStatus.ACTIVE)
    mock_get.return_value = tontine
    mock_members.return_value = [_make_member(), _make_member(position=2)]

    db = AsyncMock()
    result = await pre_start_checks(db, tontine.id)

    assert result.can_start is False
    codes = [b.code for b in result.blockers]
    assert "NOT_DRAFT" in codes


@pytest.mark.asyncio
@patch("app.tontine.cycle_service.get_tontine")
@patch("app.tontine.cycle_service._get_active_members_sorted")
async def test_pre_start_minimum_members_blocker(mock_members, mock_get):
    from app.tontine.cycle_service import pre_start_checks

    tontine = _make_tontine()
    mock_get.return_value = tontine
    mock_members.return_value = [_make_member()]  # Only 1 member

    db = AsyncMock()
    result = await pre_start_checks(db, tontine.id)

    assert result.can_start is False
    codes = [b.code for b in result.blockers]
    assert "MINIMUM_MEMBERS" in codes


@pytest.mark.asyncio
@patch("app.tontine.cycle_service.get_tontine")
@patch("app.tontine.cycle_service._get_active_members_sorted")
async def test_pre_start_order_not_defined_blocker(mock_members, mock_get):
    from app.tontine.cycle_service import pre_start_checks

    tontine = _make_tontine()
    mock_get.return_value = tontine
    m1 = _make_member(position=1)
    m2 = _make_member(position=None)  # No position
    mock_members.return_value = [m1, m2]

    db = AsyncMock()
    result = await pre_start_checks(db, tontine.id)

    assert result.can_start is False
    codes = [b.code for b in result.blockers]
    assert "ORDER_NOT_DEFINED" in codes


@pytest.mark.asyncio
@patch("app.tontine.cycle_service.get_tontine")
@patch("app.tontine.cycle_service._get_active_members_sorted")
async def test_pre_start_orphan_half_hands_blocker(mock_members, mock_get):
    from app.tontine.cycle_service import pre_start_checks

    tontine = _make_tontine()
    mock_get.return_value = tontine
    mock_members.return_value = [
        _make_member(Decimal("0.5"), 1),  # orphan — odd count
        _make_member(Decimal("1"), 2),
    ]

    db = AsyncMock()
    result = await pre_start_checks(db, tontine.id)

    assert result.can_start is False
    codes = [b.code for b in result.blockers]
    assert "ORPHAN_HANDS" in codes


@pytest.mark.asyncio
@patch("app.tontine.cycle_service.get_tontine")
@patch("app.tontine.cycle_service._get_active_members_sorted")
async def test_pre_start_few_members_warning(mock_members, mock_get):
    from app.tontine.cycle_service import pre_start_checks

    tontine = _make_tontine()
    mock_get.return_value = tontine
    mock_members.return_value = [
        _make_member(position=1),
        _make_member(position=2, role=MemberRole.MEMBER),
    ]

    db = AsyncMock()
    result = await pre_start_checks(db, tontine.id)

    assert result.can_start is True  # warnings are non-blocking
    codes = [w.code for w in result.warnings]
    assert "FEW_MEMBERS" in codes
    assert "NO_RESERVE" in codes


@pytest.mark.asyncio
@patch("app.tontine.cycle_service.get_tontine")
@patch("app.tontine.cycle_service._get_active_members_sorted")
async def test_pre_start_no_reserve_warning(mock_members, mock_get):
    from app.tontine.cycle_service import pre_start_checks

    tontine = _make_tontine(reserve=False)
    mock_get.return_value = tontine
    mock_members.return_value = [
        _make_member(position=i) for i in range(1, 6)
    ]

    db = AsyncMock()
    result = await pre_start_checks(db, tontine.id)

    assert result.can_start is True
    codes = [w.code for w in result.warnings]
    assert "NO_RESERVE" in codes
    assert "FEW_MEMBERS" not in codes  # 5 members is not "few"


# --- Start cycle ---


@pytest.mark.asyncio
@patch("app.tontine.cycle_service._get_active_members_sorted")
@patch("app.tontine.cycle_service.get_tontine")
async def test_start_cycle_blocked_raises(mock_get, mock_members):
    from app.tontine.cycle_service import start_cycle

    tontine = _make_tontine()
    mock_get.return_value = tontine

    # Only 1 member (organizer) — MINIMUM_MEMBERS blocker will trigger
    organizer = _make_member(role=MemberRole.ORGANIZER, position=1)
    mock_members.return_value = [organizer]

    db = AsyncMock()

    with pytest.raises(DiaspoFinanceError, match="Conditions de démarrage"):
        await start_cycle(db, tontine.id, organizer.user_id)


@pytest.mark.asyncio
@patch("app.tontine.cycle_service.get_tontine")
async def test_start_cycle_non_organizer_forbidden(mock_get):
    from app.tontine.cycle_service import start_cycle

    tontine = _make_tontine()
    mock_get.return_value = tontine

    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # not found as organizer
    db.execute.return_value = mock_result

    with pytest.raises(ForbiddenError, match="organisateur"):
        await start_cycle(db, tontine.id, uuid.uuid4())
