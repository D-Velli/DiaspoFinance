from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_tontine(hand_amount_cents=20000, max_pot_cents=None, max_members=None, frequency="monthly"):
    tontine = MagicMock()
    tontine.hand_amount_cents = hand_amount_cents
    tontine.max_pot_cents = max_pot_cents
    tontine.max_members = max_members

    freq_mock = MagicMock()
    freq_mock.value = frequency
    tontine.frequency = freq_mock
    return tontine


def _make_stats(member_count=3, total_hands=Decimal("3"), pot_per_turn=60000):
    return {
        "member_count": member_count,
        "total_hands": total_hands,
        "pot_per_turn_cents": pot_per_turn,
    }


@pytest.mark.asyncio
@patch("app.tontine.service.get_tontine")
@patch("app.tontine.service.get_tontine_stats")
async def test_validate_join_capacity_ok(mock_stats, mock_get):
    """Member with 1 hand can join when no limits are hit."""
    from app.tontine.service import validate_join_capacity

    mock_get.return_value = _make_tontine()
    mock_stats.return_value = _make_stats()

    db = AsyncMock()
    result = await validate_join_capacity(db, MagicMock(), Decimal("1"))
    assert result["can_join"] is True


@pytest.mark.asyncio
@patch("app.tontine.service.get_tontine")
@patch("app.tontine.service.get_tontine_stats")
async def test_validate_join_tontine_full(mock_stats, mock_get):
    """Cannot join when max_members is reached."""
    from app.tontine.service import validate_join_capacity

    mock_get.return_value = _make_tontine(max_members=3)
    mock_stats.return_value = _make_stats(member_count=3)

    db = AsyncMock()
    result = await validate_join_capacity(db, MagicMock(), Decimal("1"))
    assert result["can_join"] is False
    assert result["reason"] == "TONTINE_FULL"


@pytest.mark.asyncio
@patch("app.tontine.service.get_tontine")
@patch("app.tontine.service.get_tontine_stats")
async def test_validate_join_insufficient_capacity(mock_stats, mock_get):
    """Cannot join with 2 hands when only 1 hand capacity remains."""
    from app.tontine.service import validate_join_capacity

    # max_pot = 80000 (800$), hand = 20000 (200$) → max 4 hands, 3 used → 1 remaining
    mock_get.return_value = _make_tontine(hand_amount_cents=20000, max_pot_cents=80000)
    mock_stats.return_value = _make_stats(total_hands=Decimal("3"))

    db = AsyncMock()
    result = await validate_join_capacity(db, MagicMock(), Decimal("2"))
    assert result["can_join"] is False
    assert result["reason"] == "INSUFFICIENT_CAPACITY"
    assert result["hands_remaining"] == 1.0


@pytest.mark.asyncio
@patch("app.tontine.service.get_tontine")
@patch("app.tontine.service.get_tontine_stats")
async def test_validate_join_half_hand_fits(mock_stats, mock_get):
    """Half hand can join when only 0.5 capacity remains."""
    # max_pot = 70000 (700$), hand = 20000 (200$) → max 3.5 hands, 3 used → 0.5 remaining
    mock_get.return_value = _make_tontine(hand_amount_cents=20000, max_pot_cents=70000)
    mock_stats.return_value = _make_stats(total_hands=Decimal("3"))

    from app.tontine.service import validate_join_capacity

    db = AsyncMock()
    result = await validate_join_capacity(db, MagicMock(), Decimal("0.5"))
    assert result["can_join"] is True


@pytest.mark.asyncio
@patch("app.tontine.service.get_tontine")
@patch("app.tontine.service.get_tontine_stats")
async def test_get_capacity_no_limit(mock_stats, mock_get):
    """Capacity with no max_pot returns null for remaining."""
    from app.tontine.service import get_capacity

    mock_get.return_value = _make_tontine()
    mock_stats.return_value = _make_stats()

    db = AsyncMock()
    result = await get_capacity(db, MagicMock())
    assert result["hands_remaining"] is None
    assert result["max_hands"] is None
    assert result["total_turns"] == 3
    assert result["estimated_weeks"] == 12  # 3 turns × 4 weeks (monthly)


@pytest.mark.asyncio
@patch("app.tontine.service.get_tontine")
@patch("app.tontine.service.get_tontine_stats")
async def test_get_capacity_with_max_pot(mock_stats, mock_get):
    """Capacity with max_pot shows remaining hands."""
    from app.tontine.service import get_capacity

    # max_pot = 100000 (1000$), hand = 20000 (200$) → max 5 hands
    mock_get.return_value = _make_tontine(hand_amount_cents=20000, max_pot_cents=100000)
    mock_stats.return_value = _make_stats(total_hands=Decimal("3"))

    db = AsyncMock()
    result = await get_capacity(db, MagicMock())
    assert result["max_hands"] == 5.0
    assert result["hands_remaining"] == 2.0
    assert result["total_turns"] == 3


@pytest.mark.asyncio
@patch("app.tontine.service.get_tontine")
@patch("app.tontine.service.get_tontine_stats")
async def test_get_capacity_weekly_duration(mock_stats, mock_get):
    """Weekly frequency gives shorter estimated duration."""
    from app.tontine.service import get_capacity

    mock_get.return_value = _make_tontine(frequency="weekly")
    mock_stats.return_value = _make_stats(total_hands=Decimal("4"))

    db = AsyncMock()
    result = await get_capacity(db, MagicMock())
    assert result["total_turns"] == 4
    assert result["estimated_weeks"] == 4  # 4 turns × 1 week


@pytest.mark.asyncio
@patch("app.tontine.service.get_tontine")
@patch("app.tontine.service.get_tontine_stats")
async def test_get_capacity_biweekly_duration(mock_stats, mock_get):
    """Biweekly frequency estimation."""
    from app.tontine.service import get_capacity

    mock_get.return_value = _make_tontine(frequency="biweekly")
    mock_stats.return_value = _make_stats(total_hands=Decimal("5"))

    db = AsyncMock()
    result = await get_capacity(db, MagicMock())
    assert result["total_turns"] == 5
    assert result["estimated_weeks"] == 10  # 5 turns × 2 weeks
