"""Orchestrator error types (framework-level)."""

from __future__ import annotations


class OrchestratorError(Exception):
    """Base class for orchestrator errors."""


class ScopeNotPending(OrchestratorError):
    """activate_scope was called on a scope not in `pending` state.

    The orchestrator refuses activation and keeps the scope as-is.
    """

    def __init__(self, scope_id: str, current_state: str) -> None:
        super().__init__(
            f"scope {scope_id!r} is {current_state!r}, not pending"
        )
        self.scope_id = scope_id
        self.current_state = current_state


class BindRefused(OrchestratorError):
    """bind_scope rejected the binding.

    Wraps the underlying objective-tracker error
    (UnresolvedObjectiveError or OrphanRootError) and adds the
    local event_id written to the bind_refused log.
    """

    def __init__(
        self,
        *,
        scope_id: str,
        objective_id: str,
        cause_kind: str,
        cause_message: str,
        event_id: int | None = None,
    ) -> None:
        super().__init__(
            f"bind_scope refused ({cause_kind}): {cause_message}"
        )
        self.scope_id = scope_id
        self.objective_id = objective_id
        self.cause_kind = cause_kind
        self.cause_message = cause_message
        self.event_id = event_id


class BootstrapMissing(OrchestratorError):
    """Workspace ~/.pos/bootstrap.py is missing. Fail-closed per
    Luke's ruling in the brief."""


class BootstrapError(OrchestratorError):
    """Workspace ~/.pos/bootstrap.py raised on import or invocation."""


class IPCError(OrchestratorError):
    """IPC-layer error (socket + JSON-RPC)."""
