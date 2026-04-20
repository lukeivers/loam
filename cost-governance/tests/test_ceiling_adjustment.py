"""Ceiling adjustment via IPC — C22."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from pos_orchestrator.ipc import ApplicationError, IPCServer
from scope_of_work import ScopeSpec

from cost_governance import (
    CostLedger,
    CostStore,
    register_cost_governance_ipc,
)

from .conftest import build_config, make_spec


@pytest.mark.asyncio
async def test_C22_adjust_ceiling_writes_audit_and_updates_cache(
    tmp_path: Path,
) -> None:
    server = IPCServer(tmp_path / "sock")

    async def orig_activate(params: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True}

    server.register("activate_scope", orig_activate)

    store = CostStore(tmp_path / "cost.sqlite")
    config = build_config(session_money=1000)
    ledger = CostLedger(store=store, config=config)
    specs: dict[str, ScopeSpec] = {}

    def resolve(scope_id: str) -> ScopeSpec | None:
        return specs.get(scope_id)

    register_cost_governance_ipc(
        server=server, ledger=ledger, spec_resolver=resolve
    )

    adjust_handler = server._handlers["cost.adjust_ceiling"]
    result = await adjust_handler(
        {
            "ceiling_kind": "session",
            "axis": "money",
            "new_value": 2000,
            "reason": "monthly review",
        }
    )
    assert result["ok"] is True
    assert result["audit_record_id"] > 0

    # Audit record written.
    audits = store.list_ceiling_adjustments()
    assert len(audits) == 1
    assert audits[0].ceiling_kind == "session"
    assert audits[0].axis == "money"
    assert audits[0].new_value == 2000
    assert audits[0].reason == "monthly review"

    # In-memory cache updated — subsequent activation uses the new cap.
    assert ledger.config.session.money_cents == 2000

    # A scope that would have failed at cap=1000 now succeeds (1500 < 2000).
    specs["s_new"] = make_spec(money_cents=1500)
    handler = server._handlers["activate_scope"]
    await handler({"scope_id": "s_new"})

    # Active reservations are NOT re-checked by the adjustment.
    # Seed an active reservation at 1800 before tightening.
    # Tighten cap back to 1000 — the active reservation remains, the
    # adjustment applies to NEW activations only.
    await adjust_handler(
        {
            "ceiling_kind": "session",
            "axis": "money",
            "new_value": 1000,
            "reason": "tighten",
        }
    )
    r = store.get_reservation("s_new")
    assert r is not None
    assert r.state == "active"
    # New activation under the tightened cap fails.
    specs["s_next"] = make_spec(money_cents=500)
    with pytest.raises(ApplicationError):
        await handler({"scope_id": "s_next"})
    store.close()


@pytest.mark.asyncio
async def test_C22_adjust_rolling_ceiling_requires_window_kind(
    tmp_path: Path,
) -> None:
    server = IPCServer(tmp_path / "sock")

    async def orig_activate(params: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True}

    server.register("activate_scope", orig_activate)
    store = CostStore(tmp_path / "cost.sqlite")
    ledger = CostLedger(store=store, config=build_config())
    register_cost_governance_ipc(server=server, ledger=ledger)

    adjust_handler = server._handlers["cost.adjust_ceiling"]
    result = await adjust_handler(
        {
            "ceiling_kind": "rolling",
            "axis": "money",
            "window_kind": "daily",
            "new_value": 500,
            "reason": "test",
        }
    )
    assert result["ok"] is True

    # Cache was updated on the daily window.
    daily = next(r for r in ledger.config.rolling if r.window_kind == "daily")
    assert daily.money_cents == 500
    store.close()
