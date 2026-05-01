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

"""IPC wiring — registers cost-governance methods on the shared IPCServer.

Wrap ordering (Luke's ruling #1, brief §"Critical discipline anchors" #2):

    cost first → reversibility second → safety third → orig_activate at core

Because each wrap captures the prior handler as its `orig_activate`,
registering in that order yields the call chain
`safety → reversibility → cost → orig_activate` at dispatch time.

This module MUST be invoked by the workspace bootstrap BEFORE
`reversibility_primitive.ipc_wiring.register_reversibility_ipc` and
`safety_layer.ipc_wiring.register_safety_ipc`. The composition test
in `tests/test_ipc_wrap_composition.py` locks the ordering in.
"""

from __future__ import annotations

from typing import Any, Callable

from loam.orchestrator.ipc import ApplicationError, IPCServer
from loam.scope_of_work import ScopeSpec

from . import observability as obs
from .ledger import CostLedger
from .spec import (
    CeilingAdjustment,
)


def register_cost_governance_ipc(
    *,
    server: IPCServer,
    ledger: CostLedger,
    spec_resolver: Callable[[str], ScopeSpec | None] | None = None,
) -> None:
    """Register the cost-governance IPC methods and activate_scope wrap.

    Parameters
    ----------
    server: shared IPCServer (orchestrator-constructed).
    ledger: CostLedger instance (pre-subscribed to ScopeRuntime events
        via `CostController.build`).
    spec_resolver: scope_id -> ScopeSpec | None. When absent, the
        activate-scope wrap still installs but skips the gate (the
        wrap still preserves the call chain for the downstream wraps).
    """

    # ---- cost.status -----------------------------------------------

    async def status(params: dict[str, Any]) -> dict[str, Any]:
        session_id = params.get("session_id") or ledger.default_session_id
        session_rollup = ledger.store.get_session_rollup(session_id)
        active = ledger.store.list_active_reservations(session_id=session_id)
        return {
            "session_id": session_id,
            "session_rollup": (
                session_rollup.model_dump() if session_rollup else None
            ),
            "active_reservations": [r.model_dump() for r in active],
            "config": ledger.config.model_dump(),
        }

    # ---- cost.scope ------------------------------------------------

    async def scope_status(params: dict[str, Any]) -> dict[str, Any]:
        scope_id = params.get("scope_id")
        if not isinstance(scope_id, str):
            raise ApplicationError(-32602, "scope_id (string) required")
        r = ledger.store.get_reservation(scope_id)
        return {"scope_id": scope_id, "reservation": r.model_dump() if r else None}

    # ---- cost.session ----------------------------------------------

    async def session_status(params: dict[str, Any]) -> dict[str, Any]:
        session_id = params.get("session_id") or ledger.default_session_id
        rollup = ledger.store.get_session_rollup(session_id)
        return {
            "session_id": session_id,
            "rollup": rollup.model_dump() if rollup else None,
        }

    # ---- cost.rolling ----------------------------------------------

    async def rolling_status(params: dict[str, Any]) -> dict[str, Any]:
        window_kind = params.get("window_kind")
        rollups = ledger.store.list_rolling_rollups(
            window_kind=window_kind if isinstance(window_kind, str) else None
        )
        return {
            "window_kind": window_kind,
            "rollups": [r.model_dump() for r in rollups],
        }

    # ---- cost.adjust_ceiling (C22) ---------------------------------

    async def adjust_ceiling(params: dict[str, Any]) -> dict[str, Any]:
        ceiling_kind = params.get("ceiling_kind")
        axis = params.get("axis")
        reason = params.get("reason")
        window_kind = params.get("window_kind")
        new_value = params.get("new_value")  # absolute value, not delta
        if ceiling_kind not in ("session", "rolling"):
            raise ApplicationError(
                -32602, "ceiling_kind must be 'session' or 'rolling'"
            )
        if axis not in ("time", "tokens", "money"):
            raise ApplicationError(
                -32602, "axis must be 'time' / 'tokens' / 'money'"
            )
        if not isinstance(reason, str) or not reason:
            raise ApplicationError(-32602, "reason (non-empty string) required")
        if new_value is not None and not isinstance(new_value, int):
            raise ApplicationError(-32602, "new_value must be int or null")
        if new_value is not None and new_value < 0:
            raise ApplicationError(-32602, "new_value must be >= 0 or null")

        adj = ledger.adjust_ceiling(
            ceiling_kind=ceiling_kind,
            axis=axis,
            window_kind=window_kind if isinstance(window_kind, str) else None,
            new_value=new_value if new_value is None else int(new_value),
            reason=reason,
        )
        return {"ok": True, "audit_record_id": adj.audit_record_id}

    # ---- cost.list_adjustments -------------------------------------

    async def list_adjustments(params: dict[str, Any]) -> dict[str, Any]:
        return {
            "adjustments": [
                a.model_dump()
                for a in ledger.store.list_ceiling_adjustments()
            ]
        }

    # ---- activate_scope wrap (innermost) ---------------------------

    orig_activate = server._handlers.get("activate_scope")

    async def wrapped_activate_scope(params: dict[str, Any]) -> Any:
        scope_id = params.get("scope_id")
        if (
            spec_resolver is not None
            and isinstance(scope_id, str)
        ):
            spec = spec_resolver(scope_id)
            if spec is not None:
                # Raises ApplicationError(-32060/-32061/-32062) on
                # refusal. Bubble up; orchestrator never runs.
                ledger.reserve_or_refuse(spec, scope_id=scope_id)
        if orig_activate is None:
            raise ApplicationError(
                -32601, "activate_scope not registered on orchestrator"
            )
        return await orig_activate(params)

    server.register("cost.status", status)
    server.register("cost.scope", scope_status)
    server.register("cost.session", session_status)
    server.register("cost.rolling", rolling_status)
    server.register("cost.adjust_ceiling", adjust_ceiling)
    server.register("cost.list_adjustments", list_adjustments)
    server.register("activate_scope", wrapped_activate_scope)
