"""Calendar generation for tontine cycles.

Generates the full schedule of rounds with collection and distribution dates.
"""

from datetime import date, timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta

from app.tontine.models import (
    RoundStatus,
    Tontine,
    TontineFrequency,
    TontineMember,
    TontineRound,
)

FREQUENCY_DELTA = {
    TontineFrequency.WEEKLY: relativedelta(weeks=1),
    TontineFrequency.BIWEEKLY: relativedelta(weeks=2),
    TontineFrequency.MONTHLY: relativedelta(months=1),
}

COLLECTION_ADVANCE_DAYS = 2  # J-2 before distribution


def _build_beneficiary_sequence(
    members_sorted: list[TontineMember],
) -> list[TontineMember]:
    """Build the ordered sequence of beneficiaries from sorted members.

    - 1 hand → 1 turn
    - 2 hands → 2 consecutive turns
    - ½ hand members sharing same position → appear once (co-beneficiaries)
    """
    sequence: list[TontineMember] = []
    seen_positions: set[int] = set()

    for member in members_sorted:
        pos = member.turn_position
        if pos is None:
            continue
        if pos in seen_positions:
            # Half-hand partner on same position — already covered
            continue
        seen_positions.add(pos)

        if member.hands == Decimal("2"):
            sequence.append(member)
            sequence.append(member)  # 2 consecutive turns
        else:
            # 1 hand or 0.5 hand (paired on same position)
            sequence.append(member)

    return sequence


def generate_rounds(
    tontine: Tontine,
    members_sorted: list[TontineMember],
    start_date: date,
) -> list[TontineRound]:
    """Generate the full calendar of rounds for a tontine cycle.

    Args:
        tontine: The tontine entity
        members_sorted: Members sorted by turn_position ASC
        start_date: The cycle start date (first distribution date)

    Returns:
        List of TontineRound entities (not yet persisted)
    """
    total_hands = sum(m.hands for m in members_sorted)
    pot_per_turn_cents = int(total_hands * tontine.hand_amount_cents)
    delta = FREQUENCY_DELTA[tontine.frequency]

    beneficiary_sequence = _build_beneficiary_sequence(members_sorted)

    rounds: list[TontineRound] = []
    for i, beneficiary in enumerate(beneficiary_sequence):
        distribution_date = start_date + (delta * i)
        collection_date = distribution_date - timedelta(days=COLLECTION_ADVANCE_DAYS)

        rounds.append(
            TontineRound(
                tontine_id=tontine.id,
                round_number=i + 1,
                beneficiary_user_id=beneficiary.user_id,
                beneficiary_hands=beneficiary.hands,
                expected_collection_date=collection_date,
                expected_distribution_date=distribution_date,
                pot_expected_amount_cents=pot_per_turn_cents,
                status=RoundStatus.PENDING,
            )
        )

    return rounds
