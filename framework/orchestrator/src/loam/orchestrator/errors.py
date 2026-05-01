# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
    """Workspace ~/.loam/bootstrap.py is missing. Fail-closed per
    Luke's ruling in the brief."""


class BootstrapError(OrchestratorError):
    """Workspace ~/.loam/bootstrap.py raised on import or invocation."""


class IPCError(OrchestratorError):
    """IPC-layer error (socket + JSON-RPC)."""
