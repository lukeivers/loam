"""Four-wrap composition test (brief §"Critical discipline anchors" #2).

Registration order: orig → cost → reversibility → safety.
Dispatch chain: safety (outer) → reversibility → cost → orig_activate.

Three scenarios lock the chain in:

  1. Safety system-kill raises BEFORE reversibility/cost run (C refusal
     surfaces the safety reason, not the cost one).
  2. Reversibility refusal on a compensatable scope with no binding
     raises BEFORE cost's gate fires (so you don't reserve capacity
     on a scope that can't run).
  3. All three pass → orig_activate runs exactly once.

Mirrors `reversibility-primitive/tests/test_safety_wrap_composition.py`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from pos_orchestrator.ipc import ApplicationError, IPCServer
from primary_persona.introduction import ChannelKind
from scope_of_work import Budget, ReversibilityClass, ScopeRuntime, ScopeSpec, SuccessCriterion

from cost_governance import (
    CostLedger,
    CostStore,
    IPC_COST_SESSION_CEILING_EXCEEDED,
    register_cost_governance_ipc,
)
from reversibility_primitive import (
    IPC_REVERSIBILITY_MISSING_COMPENSATION,
    ReversibilityController,
    ReversibilityStore,
    RollbackNotifier,
    register_reversibility_ipc,
)
from reversibility_primitive.notification import ReversibilityChannel
from safety_layer import (
    AlwaysAskList,
    DEFAULT_DANGEROUS_OP_SUBSET,
    DEFAULT_FRAMEWORK_FLOOR,
    SafetyConfig,
    SafetyController,
    SafetyNotifier,
    SafetyStore,
)
from safety_layer.ipc_wiring import register_safety_ipc
from safety_layer.notification import SafetyChannel

from .conftest import build_config, make_spec


def _make_scope_runtime(tmp_path: Path) -> ScopeRuntime:
    return ScopeRuntime(
        tmp_path / "scope.sqlite", pending_extension_dir=tmp_path / "pe"
    )


def _make_safety_controller(tmp_path: Path, scope_runtime: ScopeRuntime) -> SafetyController:
    class _FakeOrch:
        def pause_activation(self, reason: str) -> None: ...
        def resume_activation(self) -> None: ...
        def request_stop(self) -> None: ...

    async def send(text: str) -> None: ...

    ch = SafetyChannel(
        kind=ChannelKind.personal_telegram, name="safety-active",
        send=send, is_active=True,
    )
    return SafetyController(
        scope_runtime=scope_runtime,
        orchestrator=_FakeOrch(),
        store=SafetyStore(tmp_path / "safety.sqlite"),
        ask_list=AlwaysAskList(
            version=1,
            framework_floor=DEFAULT_FRAMEWORK_FLOOR,
            workspace_additions=(),
            dangerous_op_subset=DEFAULT_DANGEROUS_OP_SUBSET,
        ),
        config=SafetyConfig(),
        notifier=SafetyNotifier(channels=[ch]),
    )


def _wire_four(
    *,
    server: IPCServer,
    tmp_path: Path,
    scope_runtime: ScopeRuntime,
    spec_by_id: dict[str, ScopeSpec],
    cost_config,
):
    def resolve(scope_id: str) -> ScopeSpec | None:
        return spec_by_id.get(scope_id)

    # Registration order: cost first (innermost), then reversibility,
    # then safety. Dispatch: safety → reversibility → cost → orig.
    cost_store = CostStore(tmp_path / "cost.sqlite")
    ledger = CostLedger(store=cost_store, config=cost_config)
    register_cost_governance_ipc(
        server=server, ledger=ledger, spec_resolver=resolve
    )

    rev_store = ReversibilityStore(tmp_path / "rev.sqlite")

    async def _rev_send(text: str) -> None: ...
    rev_ch = ReversibilityChannel(
        kind=ChannelKind.personal_telegram, name="rev-active",
        send=_rev_send, is_active=True,
    )
    rev_notifier = RollbackNotifier(channels=[rev_ch])
    rev_controller = ReversibilityController(
        store=rev_store, scope_runtime=scope_runtime, notifier=rev_notifier
    )
    register_reversibility_ipc(
        server=server,
        store=rev_controller.store,
        gate=rev_controller.gate,
        rollback_runtime=rev_controller.rollback_runtime,
        spec_resolver=resolve,
    )

    safety_ctrl = _make_safety_controller(tmp_path, scope_runtime)
    register_safety_ipc(
        server=server, controller=safety_ctrl, spec_resolver=resolve
    )
    return cost_store, ledger, rev_store, safety_ctrl


@pytest.mark.asyncio
async def test_four_wrap_composition_safety_fires_first(tmp_path: Path) -> None:
    """Safety system-kill surfaces before reversibility or cost."""
    server = IPCServer(tmp_path / "sock")
    orig_calls: list = []

    async def orig_activate(params: dict[str, Any]) -> dict[str, Any]:
        orig_calls.append(params)
        return {"ok": True}

    server.register("activate_scope", orig_activate)
    scope_runtime = _make_scope_runtime(tmp_path)

    # Cost ceiling that would refuse money=600 on its own.
    cost_config = build_config(session_money=500)

    # A fully_reversible spec — reversibility passes. Cost would fail
    # at 600 > 500. But we're going to trigger safety system-kill, which
    # must fire first.
    spec_by_id = {"s1": make_spec(money_cents=600)}

    cost_store, ledger, rev_store, safety_ctrl = _wire_four(
        server=server, tmp_path=tmp_path,
        scope_runtime=scope_runtime, spec_by_id=spec_by_id,
        cost_config=cost_config,
    )

    # Trigger system kill.
    await safety_ctrl.kill_engine.kill_system(
        reason="composition test", source="cli",
        nonce=safety_ctrl.kill_engine.request_system_kill_nonce(),
    )

    handler = server._handlers["activate_scope"]
    with pytest.raises(ApplicationError) as exc:
        await handler({"scope_id": "s1"})
    # Safety's system-kill code (-32042) fires, NOT cost (-32061).
    assert exc.value.code != IPC_COST_SESSION_CEILING_EXCEEDED
    assert orig_calls == []
    cost_store.close()
    rev_store.close()
    scope_runtime.close()


@pytest.mark.asyncio
async def test_four_wrap_composition_reversibility_fires_before_cost(
    tmp_path: Path,
) -> None:
    """Reversibility refusal surfaces before cost's gate runs.

    A compensatable scope with no binding + money that would refuse at
    cost → reversibility refuses first (-32050), cost gate does not
    execute, no reservation is written (C23 alignment: don't burn
    capacity on a scope that can't run).
    """
    server = IPCServer(tmp_path / "sock")

    async def orig_activate(params: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True}

    server.register("activate_scope", orig_activate)
    scope_runtime = _make_scope_runtime(tmp_path)

    cost_config = build_config(session_money=1000)

    # compensatable + no binding → reversibility refuses.
    spec = make_spec(money_cents=100, reversibility=ReversibilityClass.compensatable)
    spec_by_id = {"s1": spec}

    cost_store, ledger, rev_store, safety_ctrl = _wire_four(
        server=server, tmp_path=tmp_path,
        scope_runtime=scope_runtime, spec_by_id=spec_by_id,
        cost_config=cost_config,
    )

    handler = server._handlers["activate_scope"]
    with pytest.raises(ApplicationError) as exc:
        await handler({"scope_id": "s1"})
    assert exc.value.code == IPC_REVERSIBILITY_MISSING_COMPENSATION
    # Cost did NOT write a reservation.
    assert cost_store.get_reservation("s1") is None
    cost_store.close()
    rev_store.close()
    scope_runtime.close()


@pytest.mark.asyncio
async def test_four_wrap_composition_all_pass_forwards_to_orig(
    tmp_path: Path,
) -> None:
    """When safety + reversibility + cost all pass, orig_activate runs
    exactly once and a reservation is written."""
    server = IPCServer(tmp_path / "sock")
    orig_calls: list = []

    async def orig_activate(params: dict[str, Any]) -> dict[str, Any]:
        orig_calls.append(params)
        return {"ok": True, "forwarded": True}

    server.register("activate_scope", orig_activate)
    scope_runtime = _make_scope_runtime(tmp_path)

    cost_config = build_config(session_money=10_000, daily_money=10_000)
    spec = make_spec(
        money_cents=50,
        reversibility=ReversibilityClass.fully_reversible,
    )
    spec_by_id = {"s_ok": spec}

    cost_store, ledger, rev_store, safety_ctrl = _wire_four(
        server=server, tmp_path=tmp_path,
        scope_runtime=scope_runtime, spec_by_id=spec_by_id,
        cost_config=cost_config,
    )

    handler = server._handlers["activate_scope"]
    result = await handler({"scope_id": "s_ok"})
    assert result == {"ok": True, "forwarded": True}
    assert len(orig_calls) == 1
    # Cost wrote a reservation.
    assert cost_store.get_reservation("s_ok") is not None
    cost_store.close()
    rev_store.close()
    scope_runtime.close()
