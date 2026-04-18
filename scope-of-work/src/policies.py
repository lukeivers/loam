"""Lifecycle policy tables and stateless transition rules.

Kept separate from runtime.py to honour the 200-line file budget and
to make the legal-transition map easy to audit.
"""

from __future__ import annotations

from .spec import ScopeState


# Legal lifecycle transitions (proposal §2.1).
LEGAL_TRANSITIONS: dict[ScopeState, set[ScopeState]] = {
    ScopeState.proposed: {ScopeState.active, ScopeState.cancelled},
    ScopeState.active: {
        ScopeState.paused,
        ScopeState.completed,
        ScopeState.failed,
        ScopeState.cancelled,
        ScopeState.escalated,
    },
    ScopeState.paused: {
        ScopeState.active,
        ScopeState.completed,
        ScopeState.cancelled,
        ScopeState.failed,
    },
    ScopeState.escalated: {
        ScopeState.active,  # observer resolves and resumes
        ScopeState.completed,
        ScopeState.failed,
        ScopeState.cancelled,
    },
    ScopeState.completed: set(),
    ScopeState.failed: set(),
    ScopeState.cancelled: set(),
}

TERMINAL_STATES: frozenset[ScopeState] = frozenset(
    {ScopeState.completed, ScopeState.failed, ScopeState.cancelled}
)


def is_legal(from_state: ScopeState, to_state: ScopeState) -> bool:
    return to_state in LEGAL_TRANSITIONS.get(from_state, set())


def is_terminal(state: ScopeState) -> bool:
    return state in TERMINAL_STATES
