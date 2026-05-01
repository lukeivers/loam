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

"""IPC wiring — registers reversibility methods on the shared IPCServer.

Wrap ordering (as finalised through Phase 3 and captured in
`cost-governance/src/ipc_wiring.py`):

    registration:  reversibility → safety → cost
    dispatch:      safety → reversibility → cost → orig_activate

Each wrap captures the prior handler as its `orig_activate`, so the
last-registered wrap runs first at dispatch time. Reversibility
registers BEFORE safety so that at dispatch, safety (system-kill,
ask-gate, dangerous-op) runs before reversibility's structural check.
Cost registers last so it runs innermost against `orig_activate`.

This module therefore MUST be invoked by the workspace bootstrap
BEFORE `safety_layer.ipc_wiring.register_safety_ipc`, which itself
must be invoked before `cost_governance` registration. The workspace
bootstrap documents the order; `tests/test_safety_wrap_composition.py`
locks it in with an integration test.

Docstring corrected 2026-04-20 per Luke's ruling during bootstrap
research — prior docstring claimed a pre-cost-governance two-wrap
chain. Code was and is correct; only the docstring was stale.
"""

from __future__ import annotations

from typing import Any, Callable

from loam.orchestrator.ipc import ApplicationError, IPCServer
from loam.scope_of_work import ScopeSpec

from .activation_gate import ActivationGate
from .rollback import (
    IPC_REVERSIBILITY_UNREGISTERED_HANDLE,
    RollbackRuntime,
)
from .spec import CompensationPathBinding, iso_now
from .store import ReversibilityStore
from . import observability as obs


def register_reversibility_ipc(
    *,
    server: IPCServer,
    store: ReversibilityStore,
    gate: ActivationGate,
    rollback_runtime: RollbackRuntime,
    spec_resolver: Callable[[str], ScopeSpec | None] | None = None,
) -> None:
    """Register reversibility IPC methods and the activate_scope wrap.

    Parameters
    ----------
    server: shared IPCServer (orchestrator-constructed).
    store: ReversibilityStore for bindings.
    gate: ActivationGate (composed with the safety resolver by the
        workspace bootstrap).
    rollback_runtime: RollbackRuntime for rollback.* methods.
    spec_resolver: scope_id -> ScopeSpec | None. When absent, the
        activate-scope wrap still installs but skips the gate (the
        wrap still preserves the call chain for downstream safety+orig).
    """

    # ---- reversibility.register_compensation ---------------------------

    async def register_compensation(params: dict[str, Any]) -> dict[str, Any]:
        scope_id = params.get("scope_id")
        handle = params.get("handle")
        if not isinstance(scope_id, str) or not isinstance(handle, str):
            raise ApplicationError(
                -32602, "scope_id (string) and handle (string) required"
            )
        idempotency_key = params.get("idempotency_key") or f"bind-{scope_id}-{handle}"
        binding = CompensationPathBinding(
            scope_id=scope_id,
            handle=handle,
            description=str(params.get("description") or ""),
            budget_seconds=params.get("budget_seconds"),
            idempotency_key=str(idempotency_key),
            registered_at=str(params.get("registered_at") or iso_now()),
            registered_by=str(params.get("registered_by") or "ipc"),
        )
        replaced, prior_handle = store.upsert_binding(binding)
        if replaced:
            obs.binding_replaced(
                scope_id=scope_id,
                prior_handle=prior_handle or "<unknown>",
                new_handle=handle,
            )
        else:
            obs.binding_registered(
                scope_id=scope_id,
                handle=handle,
                idempotency_key=binding.idempotency_key,
            )
        return {"ok": True, "binding_id": scope_id, "replaced": replaced}

    # ---- reversibility.list_handlers -----------------------------------

    async def list_handlers(params: dict[str, Any]) -> dict[str, Any]:
        return {
            "handlers": sorted(rollback_runtime.handlers.keys()),
            "bindings": [b.model_dump() for b in store.list_bindings()],
        }

    # ---- reversibility.rollback_scope ----------------------------------

    async def rollback_scope(params: dict[str, Any]) -> dict[str, Any]:
        scope_id = params.get("scope_id")
        if not isinstance(scope_id, str):
            raise ApplicationError(-32602, "scope_id (string) required")
        reason = str(params.get("reason") or "ipc:rollback_scope")
        idempotency_key = params.get("idempotency_key")
        record = await rollback_runtime.rollback(
            scope_id=scope_id,
            reason=reason,
            idempotency_key=idempotency_key if isinstance(idempotency_key, str) else None,
        )
        return {
            "ok": True,
            "scope_id": scope_id,
            "state": record.state,
            "outcome": record.outcome,
            "invocation_id": record.invocation_id,
        }

    # ---- reversibility.rollback_status ---------------------------------

    async def rollback_status(params: dict[str, Any]) -> dict[str, Any]:
        scope_id = params.get("scope_id")
        if not isinstance(scope_id, str):
            raise ApplicationError(-32602, "scope_id (string) required")
        rows = [
            r.model_dump()
            for r in store.list_invocations()
            if r.scope_id == scope_id
        ]
        return {"scope_id": scope_id, "invocations": rows}

    # ---- activate_scope wrap -------------------------------------------

    orig_activate = server._handlers.get("activate_scope")

    async def wrapped_activate_scope(params: dict[str, Any]) -> Any:
        scope_id = params.get("scope_id")
        # Skip gate when spec_resolver or scope_id are not available —
        # preserve the call chain in either case (matches safety's
        # shape).
        if spec_resolver is not None and isinstance(scope_id, str):
            spec = spec_resolver(scope_id)
            if spec is not None:
                # Raises ApplicationError(-32050) on refusal. Bubble
                # up; orchestrator never runs, safety never runs.
                gate.check(spec, scope_id=scope_id)
        if orig_activate is None:
            raise ApplicationError(
                -32601, "activate_scope not registered on orchestrator"
            )
        return await orig_activate(params)

    server.register("reversibility.register_compensation", register_compensation)
    server.register("reversibility.list_handlers", list_handlers)
    server.register("reversibility.rollback_scope", rollback_scope)
    server.register("reversibility.rollback_status", rollback_status)
    server.register("activate_scope", wrapped_activate_scope)
