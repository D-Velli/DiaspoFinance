from app.tontine.models import TontineStatus
from app.tontine.state_machine import can_transition


def test_draft_to_active():
    assert can_transition(TontineStatus.DRAFT, TontineStatus.ACTIVE) is True


def test_draft_to_cancelled():
    assert can_transition(TontineStatus.DRAFT, TontineStatus.CANCELLED) is True


def test_draft_to_collecting_invalid():
    assert can_transition(TontineStatus.DRAFT, TontineStatus.COLLECTING) is False


def test_active_to_collecting():
    assert can_transition(TontineStatus.ACTIVE, TontineStatus.COLLECTING) is True


def test_active_to_completed():
    assert can_transition(TontineStatus.ACTIVE, TontineStatus.COMPLETED) is True


def test_collecting_to_distributing():
    assert can_transition(TontineStatus.COLLECTING, TontineStatus.DISTRIBUTING) is True


def test_distributing_to_active():
    assert can_transition(TontineStatus.DISTRIBUTING, TontineStatus.ACTIVE) is True


def test_completed_is_terminal():
    assert can_transition(TontineStatus.COMPLETED, TontineStatus.ACTIVE) is False
    assert can_transition(TontineStatus.COMPLETED, TontineStatus.DRAFT) is False


def test_cancelled_is_terminal():
    assert can_transition(TontineStatus.CANCELLED, TontineStatus.ACTIVE) is False
