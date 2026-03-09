import uuid
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.tontine.rotation import (
    OrphanHalfHandError,
    assign_positions,
    check_half_hand_pairing,
)


def _make_member(hands: str = "1") -> MagicMock:
    member = MagicMock()
    member.id = uuid.uuid4()
    member.user_id = uuid.uuid4()
    member.hands = Decimal(hands)
    member.turn_position = None
    return member


def test_assign_positions_single_member():
    m = _make_member("1")
    positions = assign_positions([m])
    assert positions[m.id] == 1


def test_assign_positions_three_members_one_hand():
    m1 = _make_member("1")
    m2 = _make_member("1")
    m3 = _make_member("1")
    positions = assign_positions([m1, m2, m3])
    assert positions[m1.id] == 1
    assert positions[m2.id] == 2
    assert positions[m3.id] == 3


def test_assign_positions_two_hands_takes_two_positions():
    m1 = _make_member("1")
    m2 = _make_member("2")
    m3 = _make_member("1")
    positions = assign_positions([m1, m2, m3])
    assert positions[m1.id] == 1
    assert positions[m2.id] == 2  # occupies 2 and 3
    assert positions[m3.id] == 4


def test_assign_positions_half_hands_paired():
    m1 = _make_member("1")
    m2 = _make_member("0.5")
    m3 = _make_member("0.5")
    positions = assign_positions([m1, m2, m3])
    assert positions[m1.id] == 1
    # Both half-hand members share the same position
    assert positions[m2.id] == positions[m3.id]
    assert positions[m2.id] == 2


def test_assign_positions_orphan_half_hand_raises():
    m1 = _make_member("1")
    m2 = _make_member("0.5")
    with pytest.raises(OrphanHalfHandError):
        assign_positions([m1, m2])


def test_assign_positions_mixed_hands():
    """Test complex scenario: 2 hands + 1 hand + 2 x ½ hands."""
    m_two = _make_member("2")
    m_one = _make_member("1")
    m_half_a = _make_member("0.5")
    m_half_b = _make_member("0.5")
    positions = assign_positions([m_two, m_one, m_half_a, m_half_b])

    # m_two at position 1, occupies 1 and 2
    assert positions[m_two.id] == 1
    # m_one at position 3
    assert positions[m_one.id] == 3
    # Half-hands share position 4
    assert positions[m_half_a.id] == 4
    assert positions[m_half_b.id] == 4
    # Total turns = 2 + 1 + 0.5 + 0.5 = 4
    assert max(positions.values()) == 4


def test_assign_positions_four_half_hands():
    """Four half-hand members form 2 pairs."""
    members = [_make_member("0.5") for _ in range(4)]
    positions = assign_positions(members)
    # Should have 2 unique positions
    unique_positions = set(positions.values())
    assert len(unique_positions) == 2


def test_assign_positions_total_turns():
    """Total positions must equal sum of hands."""
    m1 = _make_member("2")
    m2 = _make_member("1")
    m3 = _make_member("1")
    m4 = _make_member("0.5")
    m5 = _make_member("0.5")
    positions = assign_positions([m1, m2, m3, m4, m5])
    # 2 + 1 + 1 + 0.5 + 0.5 = 5 turns
    # m1 occupies pos 1,2 → last pos used is 2
    # m2 occupies pos 3
    # m3 occupies pos 4
    # m4+m5 share pos 5
    total_turns = 5
    all_positions = set()
    for member_id, pos in positions.items():
        member = next(m for m in [m1, m2, m3, m4, m5] if m.id == member_id)
        if member.hands == Decimal("2"):
            all_positions.add(pos)
            all_positions.add(pos + 1)
        else:
            all_positions.add(pos)
    assert len(all_positions) == total_turns


def test_check_half_hand_pairing_no_half_hands():
    m1 = _make_member("1")
    m2 = _make_member("2")
    result = check_half_hand_pairing([m1, m2])
    assert result["half_hand_count"] == 0
    assert result["pairs"] == 0
    assert result["has_orphan"] is False
    assert result["total_turns"] == 3


def test_check_half_hand_pairing_even():
    members = [_make_member("0.5") for _ in range(4)]
    result = check_half_hand_pairing(members)
    assert result["half_hand_count"] == 4
    assert result["pairs"] == 2
    assert result["has_orphan"] is False
    assert result["total_turns"] == 2


def test_check_half_hand_pairing_orphan():
    m1 = _make_member("1")
    m2 = _make_member("0.5")
    result = check_half_hand_pairing([m1, m2])
    assert result["has_orphan"] is True
    assert result["orphan_member_id"] == str(m2.id)
    assert result["total_turns"] == 1  # int(1.5) = 1
