"""Legal status transitions for an objective.

Lifecycle (spec):

    proposed → active
    proposed → abandoned
    active   → achieved
    active   → abandoned
    achieved → active   (re_open; mandatory rationale)
    abandoned → active  (re_open; mandatory rationale)
"""

from __future__ import annotations

from .spec import ObjectiveStatus

LEGAL_TRANSITIONS: dict[ObjectiveStatus, set[ObjectiveStatus]] = {
    ObjectiveStatus.proposed: {
        ObjectiveStatus.active,
        ObjectiveStatus.abandoned,
    },
    ObjectiveStatus.active: {
        ObjectiveStatus.achieved,
        ObjectiveStatus.abandoned,
    },
    ObjectiveStatus.achieved: {
        ObjectiveStatus.active,
    },
    ObjectiveStatus.abandoned: {
        ObjectiveStatus.active,
    },
}

TERMINAL_STATES = {ObjectiveStatus.achieved, ObjectiveStatus.abandoned}


def is_legal(from_status: ObjectiveStatus, to_status: ObjectiveStatus) -> bool:
    return to_status in LEGAL_TRANSITIONS.get(from_status, set())


def is_terminal(status: ObjectiveStatus) -> bool:
    return status in TERMINAL_STATES
