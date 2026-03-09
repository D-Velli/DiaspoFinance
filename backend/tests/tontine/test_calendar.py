"""Tests for calendar generation (round dates and beneficiary assignment)."""

import uuid
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.tontine.calendar import COLLECTION_ADVANCE_DAYS, generate_rounds
from app.tontine.models import TontineFrequency


def _make_tontine(frequency=TontineFrequency.MONTHLY, hand_amount_cents=20000):
    t = MagicMock()
    t.id = uuid.uuid4()
    t.frequency = frequency
    t.hand_amount_cents = hand_amount_cents
    return t


def _make_member(hands=Decimal("1"), position=1, user_id=None):
    m = MagicMock()
    m.user_id = user_id or uuid.uuid4()
    m.hands = hands
    m.turn_position = position
    return m


def test_generate_rounds_monthly_3_members():
    """3 members × 1 hand, monthly → 3 rounds, each 1 month apart."""
    tontine = _make_tontine(TontineFrequency.MONTHLY, 20000)
    members = [_make_member(Decimal("1"), i) for i in range(1, 4)]
    start = date(2026, 4, 1)

    rounds = generate_rounds(tontine, members, start)

    assert len(rounds) == 3
    # Distribution dates: Apr 1, May 1, Jun 1
    assert rounds[0].expected_distribution_date == date(2026, 4, 1)
    assert rounds[1].expected_distribution_date == date(2026, 5, 1)
    assert rounds[2].expected_distribution_date == date(2026, 6, 1)
    # Collection dates: J-2
    assert rounds[0].expected_collection_date == date(2026, 3, 30)
    assert rounds[1].expected_collection_date == date(2026, 4, 29)
    # Pot = total_hands(3) × hand_amount(200$) = 600$ = 60000 cents
    assert all(r.pot_expected_amount_cents == 60000 for r in rounds)


def test_generate_rounds_weekly():
    """Weekly frequency: 7 days apart."""
    tontine = _make_tontine(TontineFrequency.WEEKLY, 10000)
    members = [_make_member(Decimal("1"), i) for i in range(1, 3)]
    start = date(2026, 4, 6)  # Monday

    rounds = generate_rounds(tontine, members, start)

    assert len(rounds) == 2
    assert rounds[0].expected_distribution_date == date(2026, 4, 6)
    assert rounds[1].expected_distribution_date == date(2026, 4, 13)
    assert rounds[0].expected_collection_date == date(2026, 4, 4)


def test_generate_rounds_biweekly():
    """Biweekly frequency: 14 days apart."""
    tontine = _make_tontine(TontineFrequency.BIWEEKLY, 15000)
    members = [_make_member(Decimal("1"), i) for i in range(1, 4)]
    start = date(2026, 4, 1)

    rounds = generate_rounds(tontine, members, start)

    assert len(rounds) == 3
    assert rounds[0].expected_distribution_date == date(2026, 4, 1)
    assert rounds[1].expected_distribution_date == date(2026, 4, 15)
    assert rounds[2].expected_distribution_date == date(2026, 4, 29)


def test_generate_rounds_two_hand_member():
    """A 2-hand member gets 2 consecutive turns."""
    tontine = _make_tontine(TontineFrequency.MONTHLY, 10000)
    uid = uuid.uuid4()
    m1 = _make_member(Decimal("2"), 1, uid)      # 2 hands → 2 turns
    m2 = _make_member(Decimal("1"), 3)            # 1 hand → 1 turn
    members = [m1, m2]
    start = date(2026, 4, 1)

    rounds = generate_rounds(tontine, members, start)

    # Total hands = 3, so 3 turns: m1 gets rounds 1+2, m2 gets round 3
    assert len(rounds) == 3
    assert rounds[0].beneficiary_user_id == uid
    assert rounds[1].beneficiary_user_id == uid
    assert rounds[2].beneficiary_user_id == m2.user_id
    # Pot = 3 × 100$ = 300$ = 30000 cents
    assert all(r.pot_expected_amount_cents == 30000 for r in rounds)


def test_generate_rounds_half_hand_pair():
    """Two ½-hand members on same position share 1 turn."""
    tontine = _make_tontine(TontineFrequency.MONTHLY, 10000)
    m1 = _make_member(Decimal("0.5"), 1)
    m2 = _make_member(Decimal("0.5"), 1)  # same position (paired)
    m3 = _make_member(Decimal("1"), 2)
    members = [m1, m2, m3]
    start = date(2026, 4, 1)

    rounds = generate_rounds(tontine, members, start)

    # Total hands = 2, so 2 turns
    assert len(rounds) == 2
    # Position 1 → m1 as beneficiary (½ hand), position 2 → m3
    assert rounds[0].beneficiary_user_id == m1.user_id
    assert rounds[0].beneficiary_hands == Decimal("0.5")
    assert rounds[1].beneficiary_user_id == m3.user_id


def test_generate_rounds_monthly_end_of_month():
    """Monthly from Jan 31 → Feb 28 (not 30 days)."""
    tontine = _make_tontine(TontineFrequency.MONTHLY, 10000)
    members = [_make_member(Decimal("1"), i) for i in range(1, 3)]
    start = date(2026, 1, 31)

    rounds = generate_rounds(tontine, members, start)

    assert rounds[0].expected_distribution_date == date(2026, 1, 31)
    assert rounds[1].expected_distribution_date == date(2026, 2, 28)


def test_generate_rounds_round_numbers():
    """Round numbers start at 1 and increment."""
    tontine = _make_tontine()
    members = [_make_member(Decimal("1"), i) for i in range(1, 5)]
    start = date(2026, 4, 1)

    rounds = generate_rounds(tontine, members, start)

    assert [r.round_number for r in rounds] == [1, 2, 3, 4]


def test_generate_rounds_collection_j_minus_2():
    """Collection date is always 2 days before distribution."""
    tontine = _make_tontine()
    members = [_make_member(Decimal("1"), 1)]
    start = date(2026, 4, 1)

    rounds = generate_rounds(tontine, members, start)

    for r in rounds:
        assert r.expected_collection_date == r.expected_distribution_date - timedelta(
            days=COLLECTION_ADVANCE_DAYS
        )
