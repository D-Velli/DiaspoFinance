from app.tontine.models import TontineStatus

# Valid state transitions: {current_status: set(allowed_targets)}
TRANSITIONS: dict[TontineStatus, set[TontineStatus]] = {
    TontineStatus.DRAFT: {TontineStatus.ACTIVE, TontineStatus.CANCELLED},
    TontineStatus.ACTIVE: {
        TontineStatus.COLLECTING,
        TontineStatus.COMPLETED,
        TontineStatus.CANCELLED,
    },
    TontineStatus.COLLECTING: {TontineStatus.DISTRIBUTING},
    TontineStatus.DISTRIBUTING: {TontineStatus.ACTIVE},
    TontineStatus.COMPLETED: set(),
    TontineStatus.CANCELLED: set(),
}


def can_transition(current: TontineStatus, target: TontineStatus) -> bool:
    return target in TRANSITIONS.get(current, set())
