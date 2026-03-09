from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tontine.models import TontineFrequency, TontineStatus
from app.tontine.schemas import TontineCreate

FUTURE_DATE = date.today() + timedelta(days=30)


@pytest.fixture
def mock_user():
    import uuid

    user = MagicMock()
    user.id = uuid.uuid4()
    return user


@pytest.fixture
def valid_tontine_data():
    return TontineCreate(
        name="Ma Tontine Test",
        hand_amount_cents=20000,
        frequency=TontineFrequency.MONTHLY,
        start_date=FUTURE_DATE,
        max_members=10,
        organizer_hands=Decimal("1"),
    )


def test_schema_valid_creation(valid_tontine_data):
    assert valid_tontine_data.name == "Ma Tontine Test"
    assert valid_tontine_data.hand_amount_cents == 20000
    assert valid_tontine_data.frequency == TontineFrequency.MONTHLY
    assert valid_tontine_data.organizer_hands == Decimal("1")


def test_schema_invalid_hands():
    with pytest.raises(ValueError, match="Hands must be 0.5, 1, or 2"):
        TontineCreate(
            name="Test",
            hand_amount_cents=10000,
            frequency=TontineFrequency.MONTHLY,
            start_date=FUTURE_DATE,
            organizer_hands=Decimal("3"),
        )


def test_schema_half_hand_valid():
    data = TontineCreate(
        name="Test",
        hand_amount_cents=10000,
        frequency=TontineFrequency.MONTHLY,
        start_date=FUTURE_DATE,
        organizer_hands=Decimal("0.5"),
    )
    assert data.organizer_hands == Decimal("0.5")


def test_schema_double_hand_valid():
    data = TontineCreate(
        name="Test",
        hand_amount_cents=10000,
        frequency=TontineFrequency.MONTHLY,
        start_date=FUTURE_DATE,
        organizer_hands=Decimal("2"),
    )
    assert data.organizer_hands == Decimal("2")


def test_schema_name_too_short():
    with pytest.raises(ValueError):
        TontineCreate(
            name="AB",
            hand_amount_cents=10000,
            frequency=TontineFrequency.MONTHLY,
            start_date=FUTURE_DATE,
        )


def test_schema_hand_amount_zero():
    with pytest.raises(ValueError):
        TontineCreate(
            name="Test",
            hand_amount_cents=0,
            frequency=TontineFrequency.MONTHLY,
            start_date=FUTURE_DATE,
        )


def test_schema_reserve_enabled_requires_percentage():
    with pytest.raises(ValueError, match="reserve_percentage is required"):
        TontineCreate(
            name="Test",
            hand_amount_cents=10000,
            frequency=TontineFrequency.MONTHLY,
            start_date=FUTURE_DATE,
            reserve_enabled=True,
            reserve_percentage=None,
        )


def test_schema_reserve_with_percentage():
    data = TontineCreate(
        name="Test",
        hand_amount_cents=10000,
        frequency=TontineFrequency.MONTHLY,
        start_date=FUTURE_DATE,
        reserve_enabled=True,
        reserve_percentage=Decimal("2.5"),
    )
    assert data.reserve_percentage == Decimal("2.5")


def test_schema_start_date_in_past():
    with pytest.raises(ValueError, match="Start date must be today or in the future"):
        TontineCreate(
            name="Test",
            hand_amount_cents=10000,
            frequency=TontineFrequency.MONTHLY,
            start_date=date.today() - timedelta(days=1),
        )


def test_schema_start_date_today_valid():
    data = TontineCreate(
        name="Test",
        hand_amount_cents=10000,
        frequency=TontineFrequency.MONTHLY,
        start_date=date.today(),
    )
    assert data.start_date == date.today()
