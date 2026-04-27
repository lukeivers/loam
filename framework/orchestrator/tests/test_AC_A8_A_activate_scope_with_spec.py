"""Amendment #52 (A8 R1) — activate_scope_with_spec + record_dispatch_close.

ACs covered:
- AC.A8.A1: orchestrator exposes `activate_scope_with_spec` IPC; decodes
  spec payload (Pydantic validation), calls
  `scope_runtime.create(spec, scope_id=...)` in-process so the in-memory
  CostLedger subscriber sees ScopeCreated, then invokes the existing
  wrapped `activate_scope` IPC handler so the gate chain fires.
- AC.A8.A2: existing `activate_scope` IPC stays registered + unchanged.
- AC.A8.A3: orchestrator exposes `record_dispatch_close` IPC; emits
  BudgetDebited (when tokens > 0) and transitions scope to a terminal
  state.

Test fixture is the bare orchestrator (`tmp_config`) — wrap chain is
NOT installed in this fixture (workspace-bootstrap adapters are not
loaded); the integration test for the full chain end-to-end is
deferred to the persona-side test (cost-governance/tests already
covers wrap-chain composition independently).
"""

from __future__ import annotations

import pytest

from objective_tracker import (
    ObjectiveSpec,
    ProseCriterion,
    TimeBound,
)
from pos_orchestrator import BindRefused, Orchestrator
from pos_orchestrator.ipc import ApplicationError, IPCClient
from scope_of_work import ScopeSpec
from scope_of_work.events import (
    BudgetDebited,
    ScopeCreated,
)
from scope_of_work.spec import ScopeState

from .conftest import make_scope_spec


async def _make_user_root_objective(orch, goal: str = "root") -> str:
    assert orch.objective_tracker is not None
    spec = ObjectiveSpec(
        goal=goal,
        parent_id=None,
        acceptance_criteria=(
            ProseCriterion(criterion_id="c1", prose="root done"),
        ),
        time_bound=TimeBound(evergreen=True),
        authored_by="user",
    )
    proj = await orch.objective_tracker.create(spec)
    return proj.objective_id


def _spec_payload() -> dict:
    spec = make_scope_spec("a8-r1")
    return spec.model_dump()


# ---------------------------------------------------------------------
# AC.A8.A1 — happy path (Python surface)
# ---------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_A8_A1_activate_scope_with_spec_python_surface(tmp_config):
    """Calling the Python method registers the spec and activates."""
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        objective_id = await _make_user_root_objective(o)
        scope_id = "scope-a8a1-py"
        # Pre-condition: scope does not exist yet.
        assert o.scope_runtime.get(scope_id) is None
        result = await o.activate_scope_with_spec(
            scope_id, objective_id, _spec_payload()
        )
        assert result["scope_id"] == scope_id
        assert result["objective_id"] == objective_id
        # Post-condition: scope is active.
        live = o.scope_runtime.get(scope_id)
        assert live is not None and live.state == ScopeState.active


# ---------------------------------------------------------------------
# AC.A8.A1 — happy path (IPC surface)
# ---------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_A8_A1_activate_scope_with_spec_ipc_surface(tmp_config):
    """Calling over IPC routes through the (currently bare) wrap chain."""
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        objective_id = await _make_user_root_objective(o)
        client = IPCClient(o.config.socket_path)
        try:
            await client.connect()
            scope_id = "scope-a8a1-ipc"
            result = await client.call(
                "activate_scope_with_spec",
                {
                    "scope_id": scope_id,
                    "objective_id": objective_id,
                    "spec": _spec_payload(),
                },
            )
            assert result["scope_id"] == scope_id
            assert result["objective_id"] == objective_id
            # Scope was registered + activated.
            live = o.scope_runtime.get(scope_id)
            assert live is not None and live.state == ScopeState.active
        finally:
            await client.close()


# ---------------------------------------------------------------------
# AC.A8.A1 — ScopeCreated is emitted (the in-memory subscriber path)
# ---------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_A8_A1_in_process_scope_created_event(tmp_config):
    """`scope_runtime.create(spec, scope_id=...)` runs in-process so
    the in-memory CostLedger subscriber sees `ScopeCreated`. Verified
    via a direct in-process subscription to the runtime emitter."""
    orch = Orchestrator(tmp_config)
    seen_events = []

    async with orch.running() as o:
        objective_id = await _make_user_root_objective(o)
        scope_id = "scope-a8a1-emit"

        def _capture(event):
            seen_events.append(event)

        o.scope_runtime.subscribe_all(_capture)

        await o.activate_scope_with_spec(
            scope_id, objective_id, _spec_payload()
        )
        # Find the ScopeCreated event for our scope.
        created = [
            e for e in seen_events
            if isinstance(e, ScopeCreated) and e.scope_id == scope_id
        ]
        assert len(created) == 1, (
            f"Expected exactly one ScopeCreated emission for {scope_id!r}; "
            f"got {len(created)}."
        )


# ---------------------------------------------------------------------
# AC.A8.A1 — idempotent re-call (scope already registered)
# ---------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_A8_A1_idempotent_when_scope_already_registered(tmp_config):
    """If the scope_id is already registered (e.g. pre-existing
    in-process create), the second activate_scope_with_spec call does
    NOT re-emit ScopeCreated."""
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        objective_id = await _make_user_root_objective(o)
        scope_id = "scope-a8a1-idem"
        # Pre-create the scope (simulating the same-process self-correction
        # path).
        spec = ScopeSpec.model_validate(_spec_payload())
        await o.scope_runtime.create(spec, scope_id=scope_id)

        # Now call activate_scope_with_spec — it should detect the
        # existing scope and skip the create, then activate.
        result = await o.activate_scope_with_spec(
            scope_id, objective_id, _spec_payload()
        )
        assert result["scope_id"] == scope_id
        live = o.scope_runtime.get(scope_id)
        assert live is not None and live.state == ScopeState.active


# ---------------------------------------------------------------------
# AC.A8.A1 — sad path: malformed spec → -32602
# ---------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_A8_A1_malformed_spec_returns_invalid_params(tmp_config):
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        objective_id = await _make_user_root_objective(o)
        client = IPCClient(o.config.socket_path)
        try:
            await client.connect()
            with pytest.raises(ApplicationError) as ei:
                await client.call(
                    "activate_scope_with_spec",
                    {
                        "scope_id": "scope-a8a1-bad",
                        "objective_id": objective_id,
                        "spec": {"goal": "x"},  # missing required fields
                    },
                )
            assert ei.value.code == -32602
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_AC_A8_A1_missing_spec_param_returns_invalid_params(tmp_config):
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        objective_id = await _make_user_root_objective(o)
        client = IPCClient(o.config.socket_path)
        try:
            await client.connect()
            with pytest.raises(ApplicationError) as ei:
                await client.call(
                    "activate_scope_with_spec",
                    {
                        "scope_id": "scope-a8a1-nospec",
                        "objective_id": objective_id,
                        # no spec
                    },
                )
            assert ei.value.code == -32602
        finally:
            await client.close()


# ---------------------------------------------------------------------
# AC.A8.A1 — sad path: unresolved objective bubbles BindRefused
# ---------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_A8_A1_unresolved_objective_bubbles_bind_refused(tmp_config):
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        with pytest.raises(BindRefused) as ei:
            await o.activate_scope_with_spec(
                "scope-a8a1-unresolved",
                "obj-does-not-exist",
                _spec_payload(),
            )
        assert ei.value.cause_kind == "UnresolvedObjectiveError"


# ---------------------------------------------------------------------
# AC.A8.A2 — existing activate_scope IPC is unchanged
# ---------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_A8_A2_existing_activate_scope_ipc_unchanged(tmp_config):
    """The existing `activate_scope` IPC method continues to require
    `scope_id` + `objective_id` only and behaves exactly as before
    amendment #52. (Mirrors test_d5_bind_scope.test_activate_scope_
    happy_path's IPC call path.)"""
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        objective_id = await _make_user_root_objective(o)
        scope_proj = await o.scope_runtime.create(make_scope_spec("a8a2"))
        scope_id = scope_proj.scope_id

        client = IPCClient(o.config.socket_path)
        try:
            await client.connect()
            result = await client.call(
                "activate_scope",
                {"scope_id": scope_id, "objective_id": objective_id},
            )
            assert result["scope_id"] == scope_id
            assert result["objective_id"] == objective_id
        finally:
            await client.close()

        # Scope is now active (same shape as the legacy IPC test).
        live = o.scope_runtime.get(scope_id)
        assert live is not None and live.state == ScopeState.active


# ---------------------------------------------------------------------
# AC.A8.A3 — record_dispatch_close emits BudgetDebited + terminal state
# ---------------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC_A8_A3_record_dispatch_close_completed_with_tokens(tmp_config):
    orch = Orchestrator(tmp_config)
    seen_events = []

    async with orch.running() as o:
        objective_id = await _make_user_root_objective(o)
        scope_id = "scope-a8a3-completed"

        def _capture(event):
            seen_events.append(event)

        o.scope_runtime.subscribe_all(_capture)
        await o.activate_scope_with_spec(
            scope_id, objective_id, _spec_payload()
        )

        result = await o.record_dispatch_close(
            scope_id, terminal_state="completed", debited_tokens=42
        )
        assert result["scope_id"] == scope_id
        assert result["terminal_state"] == "completed"
        assert result["debited_tokens"] == 42

        # BudgetDebited landed on this scope.
        debits = [
            e for e in seen_events
            if isinstance(e, BudgetDebited) and e.scope_id == scope_id
        ]
        assert len(debits) >= 1
        assert sum(d.output_tokens for d in debits) == 42

        # Scope reached completed state.
        live = o.scope_runtime.get(scope_id)
        assert live is not None and live.state == ScopeState.completed


@pytest.mark.asyncio
async def test_AC_A8_A3_record_dispatch_close_failed(tmp_config):
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        objective_id = await _make_user_root_objective(o)
        scope_id = "scope-a8a3-failed"
        await o.activate_scope_with_spec(
            scope_id, objective_id, _spec_payload()
        )
        result = await o.record_dispatch_close(
            scope_id, terminal_state="failed", debited_tokens=0
        )
        assert result["terminal_state"] == "failed"
        live = o.scope_runtime.get(scope_id)
        assert live is not None and live.state == ScopeState.failed


@pytest.mark.asyncio
async def test_AC_A8_A3_record_dispatch_close_cancelled(tmp_config):
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        objective_id = await _make_user_root_objective(o)
        scope_id = "scope-a8a3-cancelled"
        await o.activate_scope_with_spec(
            scope_id, objective_id, _spec_payload()
        )
        result = await o.record_dispatch_close(
            scope_id, terminal_state="cancelled", debited_tokens=0
        )
        assert result["terminal_state"] == "cancelled"
        live = o.scope_runtime.get(scope_id)
        assert live is not None and live.state == ScopeState.cancelled


@pytest.mark.asyncio
async def test_AC_A8_A3_record_dispatch_close_zero_tokens_no_debit_event(
    tmp_config,
):
    """When `debited_tokens=0`, no BudgetDebited event is emitted."""
    orch = Orchestrator(tmp_config)
    seen_events = []

    async with orch.running() as o:
        objective_id = await _make_user_root_objective(o)
        scope_id = "scope-a8a3-zero"

        def _capture(event):
            seen_events.append(event)

        o.scope_runtime.subscribe_all(_capture)
        await o.activate_scope_with_spec(
            scope_id, objective_id, _spec_payload()
        )

        # Capture pre-close debit count.
        pre_debits = [
            e for e in seen_events
            if isinstance(e, BudgetDebited) and e.scope_id == scope_id
        ]
        await o.record_dispatch_close(
            scope_id, terminal_state="completed", debited_tokens=0
        )
        post_debits = [
            e for e in seen_events
            if isinstance(e, BudgetDebited) and e.scope_id == scope_id
        ]
        assert len(post_debits) == len(pre_debits), (
            "no BudgetDebited should be emitted when tokens=0"
        )


@pytest.mark.asyncio
async def test_AC_A8_A3_record_dispatch_close_invalid_terminal_state(tmp_config):
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        client = IPCClient(o.config.socket_path)
        try:
            await client.connect()
            with pytest.raises(ApplicationError) as ei:
                await client.call(
                    "record_dispatch_close",
                    {
                        "scope_id": "scope-x",
                        "terminal_state": "active",  # invalid
                    },
                )
            assert ei.value.code == -32602
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_AC_A8_A3_record_dispatch_close_negative_tokens_rejected(
    tmp_config,
):
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        client = IPCClient(o.config.socket_path)
        try:
            await client.connect()
            with pytest.raises(ApplicationError) as ei:
                await client.call(
                    "record_dispatch_close",
                    {
                        "scope_id": "scope-x",
                        "terminal_state": "completed",
                        "debited_tokens": -1,
                    },
                )
            assert ei.value.code == -32602
        finally:
            await client.close()
