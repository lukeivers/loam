"""Concurrent activation serialisation — C16.

`IPCServer` dispatches methods in an asyncio event loop. Two concurrent
`activate_scope` calls whose combined reservations would exceed a
ceiling must not both succeed — the shared store sees the first
reservation's row as active before the second runs.

We exercise this via `asyncio.gather` with the wrap installed on the
IPCServer, confirming exactly one raises -32061 and the other
succeeds.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from loam.orchestrator.ipc import ApplicationError, IPCServer
from loam.scope_of_work import ScopeSpec

from loam.cost_governance import (
    CostLedger,
    CostStore,
    IPC_COST_SESSION_CEILING_EXCEEDED,
    register_cost_governance_ipc,
)

from .conftest import build_config, make_spec


@pytest.mark.asyncio
async def test_C16_concurrent_activation_serialised(tmp_path: Path) -> None:
    server = IPCServer(tmp_path / "sock")
    orig_ran: list[dict[str, Any]] = []

    async def orig_activate(params: dict[str, Any]) -> dict[str, Any]:
        orig_ran.append(params)
        return {"ok": True, "scope_id": params.get("scope_id")}

    server.register("activate_scope", orig_activate)

    store = CostStore(tmp_path / "cost.sqlite")
    config = build_config(session_money=1000)
    ledger = CostLedger(store=store, config=config)

    specs: dict[str, ScopeSpec] = {
        "s1": make_spec(money_cents=600),
        "s2": make_spec(money_cents=600),
    }

    def resolve(scope_id: str) -> ScopeSpec | None:
        return specs.get(scope_id)

    register_cost_governance_ipc(
        server=server, ledger=ledger, spec_resolver=resolve
    )

    handler = server._handlers["activate_scope"]

    results = await asyncio.gather(
        handler({"scope_id": "s1"}),
        handler({"scope_id": "s2"}),
        return_exceptions=True,
    )
    # Exactly one succeeded, one raised the session-ceiling error.
    successes = [r for r in results if isinstance(r, dict)]
    failures = [r for r in results if isinstance(r, ApplicationError)]
    assert len(successes) == 1
    assert len(failures) == 1
    assert failures[0].code == IPC_COST_SESSION_CEILING_EXCEEDED
    # Orchestrator's orig_activate ran exactly once.
    assert len(orig_ran) == 1
    store.close()
