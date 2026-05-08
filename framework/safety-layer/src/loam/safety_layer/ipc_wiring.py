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

"""IPC wiring — registers safety methods on the shared IPCServer.

Per proposal §3.2: the workspace bootstrap wires the gates by
registering an override for `activate_scope` that calls
`SafetyController.check_gates(...)` BEFORE forwarding to the
orchestrator's existing `activate_scope` handler. This is consumption
of the sealed `IPCServer.register()` surface — the orchestrator object
is untouched (A15).

Registration order matters: the orchestrator registers its handlers
during `_register_ipc_methods()`; the workspace bootstrap runs AFTER
that (per orchestrator.py `_startup` lines 204/210). Calling
`server.register("activate_scope", wrapped)` overrides the orchestrator's
original handler for that method.
"""

from __future__ import annotations

from typing import Any, Callable

from loam.orchestrator.ipc import ApplicationError, IPCServer
from loam.scope_of_work import ScopeSpec

from .controller import (
    SafetyController,
)


def register_safety_ipc(
    *,
    server: IPCServer,
    controller: SafetyController,
    spec_resolver: Callable[[str], ScopeSpec | None] | None = None,
) -> None:
    """Register the safety-layer IPC methods on the shared IPCServer.

    Parameters
    ----------
    server: the IPCServer already created by the orchestrator.
    controller: the SafetyController instance.
    spec_resolver: optional callable from scope_id -> ScopeSpec. When
        the workspace constructs scopes with specs available in memory
        (the common case), the resolver returns the spec the gate
        should check. When not provided, the activation-wrap is
        installed but skips gate checks (A15 still holds).
    """

    engine = controller.kill_engine
    assert engine is not None

    # --- kill methods ---

    async def kill_scope(params: dict[str, Any]) -> dict[str, Any]:
        scope_id = params.get("scope_id")
        if not isinstance(scope_id, str):
            raise ApplicationError(-32602, "scope_id (string) required")
        reason = str(params.get("reason") or "ipc:kill_scope")
        record = await engine.kill_scope(
            scope_id=scope_id, reason=reason, source="ipc"
        )
        return {"ok": True, "level": record.level.value, "scope_id": scope_id}

    async def kill_session(params: dict[str, Any]) -> dict[str, Any]:
        reason = str(params.get("reason") or "ipc:kill_session")
        record = await engine.kill_session(reason=reason, source="ipc")
        return {
            "ok": True,
            "level": record.level.value,
            "cancelled": list(record.cancelled_scope_ids),
        }

    async def kill_system_request(params: dict[str, Any]) -> dict[str, Any]:
        nonce = engine.request_system_kill_nonce()
        return {"nonce": nonce}

    async def kill_system(params: dict[str, Any]) -> dict[str, Any]:
        reason = str(params.get("reason") or "ipc:kill_system")
        nonce = params.get("nonce")
        if not isinstance(nonce, str):
            raise ApplicationError(
                -32602, "kill_system requires 'nonce' from kill_system_request"
            )
        record = await engine.kill_system(
            reason=reason, source="ipc", nonce=nonce
        )
        return {
            "ok": True,
            "level": record.level.value,
            "cancelled": list(record.cancelled_scope_ids),
        }

    # --- ask-gate decision ---

    async def ask_gate_decide(params: dict[str, Any]) -> dict[str, Any]:
        spec_hash = params.get("spec_hash")
        decision = params.get("decision")
        if not isinstance(spec_hash, str) or not isinstance(decision, str):
            raise ApplicationError(-32602, "spec_hash + decision required")
        classes = params.get("action_classes") or []
        if not isinstance(classes, list):
            raise ApplicationError(-32602, "action_classes must be a list")
        record = controller.record_ask_decision(
            scope_spec_hash=spec_hash,
            decision=decision,
            action_classes=[str(c) for c in classes],
            scope_id=params.get("scope_id"),
            reasoning=params.get("reasoning"),
        )
        return {"ok": True, "state": record.state, "expires_at": record.expires_at}

    # --- status ---

    async def safety_status(params: dict[str, Any]) -> dict[str, Any]:
        active = controller.store.active_system_kill()
        kills = controller.store.list_kills()
        decisions = controller.store.list_decisions()
        return {
            "system_kill_active": active is not None,
            "system_kill": active.model_dump() if active is not None else None,
            "kill_count": len(kills),
            "pending_asks": [
                d.model_dump()
                for d in decisions
                if d.state == "pending"
            ],
            "money_threshold_cents": controller.config.money_threshold_cents,
        }

    async def clear_system_kill(params: dict[str, Any]) -> dict[str, Any]:
        reason = str(params.get("reason") or "cleared via IPC")
        ok = controller.store.clear_system_kill(reason=reason)
        from . import observability as obs
        if ok:
            obs.system_kill_cleared(reason=reason)
        return {"ok": ok}

    # --- activate_scope wrap ---

    orig_activate = server._handlers.get("activate_scope")

    async def wrapped_activate_scope(params: dict[str, Any]) -> Any:
        scope_id = params.get("scope_id")
        # 1. System-kill block — refuse every activation until cleared.
        if isinstance(scope_id, str):
            controller.refuse_if_system_killed(scope_id=scope_id)
        # 2. Safety-layer gate — only if a spec resolver is present AND
        #    the original orchestrator activate_scope handler is present.
        if spec_resolver is not None and isinstance(scope_id, str):
            spec = spec_resolver(scope_id)
            if spec is not None:
                await controller.check_gates(spec, scope_id=scope_id)
        # 3. Forward to the orchestrator's original handler.
        if orig_activate is None:
            raise ApplicationError(
                -32601, "activate_scope not registered on orchestrator"
            )
        return await orig_activate(params)

    server.register("safety.kill_scope", kill_scope)
    server.register("safety.kill_session", kill_session)
    server.register("safety.kill_system_request", kill_system_request)
    server.register("safety.kill_system", kill_system)
    server.register("safety.ask_gate_decide", ask_gate_decide)
    server.register("safety.status", safety_status)
    server.register("safety.clear_system_kill", clear_system_kill)
    server.register("activate_scope", wrapped_activate_scope)
