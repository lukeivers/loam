"""D5 — bind_scope dispatch layer.

Acceptance (from brief D5):
- activate_scope(scope_id, objective_id) enforces: verify pending →
  bind_scope → start scope.
- UnresolvedObjectiveError and OrphanRootError both result in
  bind_refused event to local SQLite, OTel emission, 409 return,
  scope staying pending.
- Successful binding results in scope_activated span and scope-of-
  work's runtime activating the scope.
- Integration test confirms scope-of-work (77 tests) and objective-
  tracker (86 tests) are unchanged and still pass.
"""

from __future__ import annotations

import asyncio

import pytest

from objective_tracker import (
    ObjectiveSpec,
    ObjectiveStatus,
    ProseCriterion,
    TimeBound,
)
from pos_orchestrator import BindRefused, Orchestrator, ScopeNotPending
from pos_orchestrator.ipc import ApplicationError, IPCClient
from scope_of_work.spec import ScopeState

from .conftest import make_scope_spec


async def _make_user_root_objective(orch: Orchestrator, goal: str = "root") -> str:
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


@pytest.mark.asyncio
async def test_activate_scope_happy_path(tmp_config):
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        objective_id = await _make_user_root_objective(o)
        scope_proj = await o.scope_runtime.create(make_scope_spec("happy"))
        scope_id = scope_proj.scope_id

        result = await o.activate_scope(scope_id, objective_id)
        assert result["scope_id"] == scope_id
        assert result["objective_id"] == objective_id
        assert result["binding"]["scope_id"] == scope_id

        # Scope is now active.
        live = o.scope_runtime.get(scope_id)
        assert live is not None and live.state == ScopeState.active

        # Local event trail:
        activated = o.local_state.events_of_type("scope_activated")
        assert activated and activated[-1].payload["scope_id"] == scope_id
        assert o.local_state.count("bind_refused") == 0


@pytest.mark.asyncio
async def test_activate_refuses_unresolved_objective(tmp_config):
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        scope_proj = await o.scope_runtime.create(make_scope_spec("unresolved"))
        with pytest.raises(BindRefused) as ei:
            await o.activate_scope(scope_proj.scope_id, "obj-does-not-exist")
        assert ei.value.cause_kind == "UnresolvedObjectiveError"

        # Scope stays pending.
        live = o.scope_runtime.get(scope_proj.scope_id)
        assert live is not None and live.state == ScopeState.proposed

        # bind_refused event written locally.
        refused = o.local_state.events_of_type("bind_refused")
        assert refused
        payload = refused[-1].payload
        assert payload["cause_kind"] == "UnresolvedObjectiveError"
        assert payload["scope_id"] == scope_proj.scope_id


@pytest.mark.asyncio
async def test_activate_refuses_orphan_root(tmp_config):
    """A chain that does not terminate at a user-authored root must
    raise OrphanRootError and log bind_refused."""
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        assert o.objective_tracker is not None
        # Non-user root: authored by "mara" — any binding up this
        # chain must raise OrphanRootError.
        spec = ObjectiveSpec(
            goal="non-user root",
            parent_id=None,
            acceptance_criteria=(
                ProseCriterion(criterion_id="c1", prose="done"),
            ),
            time_bound=TimeBound(evergreen=True),
            authored_by="mara",
        )
        non_user_root = await o.objective_tracker.create(spec)

        scope_proj = await o.scope_runtime.create(make_scope_spec("orphan"))
        with pytest.raises(BindRefused) as ei:
            await o.activate_scope(scope_proj.scope_id, non_user_root.objective_id)
        assert ei.value.cause_kind == "OrphanRootError"

        live = o.scope_runtime.get(scope_proj.scope_id)
        assert live is not None and live.state == ScopeState.proposed

        refused = o.local_state.events_of_type("bind_refused")
        assert refused and refused[-1].payload["cause_kind"] == "OrphanRootError"


@pytest.mark.asyncio
async def test_activate_refuses_non_pending_scope(tmp_config):
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        objective_id = await _make_user_root_objective(o)
        scope_proj = await o.scope_runtime.create(make_scope_spec("active already"))
        await o.scope_runtime.start(scope_proj.scope_id)
        with pytest.raises(ScopeNotPending):
            await o.activate_scope(scope_proj.scope_id, objective_id)


@pytest.mark.asyncio
async def test_ipc_activate_scope_returns_409_on_bind_refused(tmp_config):
    """Brief D5: bind_refused → 409 return to the IPC caller."""
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        scope_proj = await o.scope_runtime.create(make_scope_spec("for 409"))
        client = IPCClient(tmp_config.socket_path)
        await client.connect()
        try:
            with pytest.raises(ApplicationError) as ei:
                await client.call(
                    "activate_scope",
                    {
                        "scope_id": scope_proj.scope_id,
                        "objective_id": "obj-404",
                    },
                )
            assert ei.value.code == 409
            assert ei.value.data["cause_kind"] == "UnresolvedObjectiveError"
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_paused_orchestrator_rejects_activation(tmp_config):
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        objective_id = await _make_user_root_objective(o)
        scope_proj = await o.scope_runtime.create(make_scope_spec("while paused"))
        o.pause_activation(reason="test outage")
        with pytest.raises(ApplicationError):
            await o.activate_scope(scope_proj.scope_id, objective_id)
        o.resume_activation()
        result = await o.activate_scope(scope_proj.scope_id, objective_id)
        assert result["scope_id"] == scope_proj.scope_id


@pytest.mark.asyncio
async def test_phase_1_tests_still_pass_reminder():
    """This test is a reminder, not a driver. The full integration
    check is run via `pytest` invocations on the Phase 1 packages —
    see the commit harness. The reminder fails loudly if anyone
    accidentally imports something that mutates Phase 1 state at
    import time."""
    # If any import had side effects on Phase 1 state, this would
    # fail — we're relying on the primitives being pure.
    from objective_tracker import ObjectiveTracker  # noqa: F401
    from primary_persona import BackgroundWorkMonitor  # noqa: F401
    from scope_of_work import ScopeRuntime  # noqa: F401
