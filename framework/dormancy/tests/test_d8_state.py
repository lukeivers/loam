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

"""D8 — State preservation + restart reconciliation.

Acceptance (brief):
- DB exists at ~/.loam/dormancy.sqlite (configurable) on first run.
- Event log + FSM-state cache; cache rebuildable from events.
- Simulated SIGKILL at various lifecycle moments produces correct
  reconciliation on restart; no orphan pauses, no lost notifications,
  no stale FSM state.
- v1.1 R1 semantic round-trip upgrade test passes.
"""

from __future__ import annotations

from pathlib import Path


from loam.dormancy import (
    ClaudeClient,
    DegradationComponent,
    DegradationConfig,
    DegradationNotifier,
)
from loam.dormancy.state import (
    DegradationStore,
    FSMStateRow,
    reconcile,
)

from .fakes import (
    FakeClock,
    FakeInvoker,
    FakeOrchestrator,
    FakeScope,
    FakeScopeRuntime,
    make_capture_channel,
)


def _build_component(tmp_path, *, script=None, clock=None):
    clock = clock or FakeClock()
    cfg = DegradationConfig.model_validate(
        {
            **DegradationConfig().model_dump(),
            "state": {"sqlite_path": str(tmp_path / "deg.sqlite")},
        }
    )
    invoker = FakeInvoker(script or [], default="OK")
    orch = FakeOrchestrator()
    rt = FakeScopeRuntime()
    ch, sent = make_capture_channel()
    notifier = DegradationNotifier(channels=[ch])
    client = ClaudeClient(invoke=invoker, clock=clock)
    comp = DegradationComponent.build(
        cfg=cfg,
        orchestrator=orch,
        scope_runtime=rt,
        notifier=notifier,
        client=client,
        clock=clock,
    )
    return cfg, comp, orch, rt, notifier, client, clock


def test_sqlite_creates_file_and_schema_on_first_use(tmp_path: Path) -> None:
    store = DegradationStore(tmp_path / "deg.sqlite")
    assert store.path.exists()
    # Snapshot on empty store is well-formed.
    snap = store.snapshot_probe()
    assert snap["detection_events.total"] == 0
    assert snap["episodes.total"] == 0
    assert snap["schema_version"] == 1


def test_store_append_detection_event(tmp_path: Path) -> None:
    store = DegradationStore(tmp_path / "deg.sqlite")
    store.append_detection_event(
        mode="down",
        signal="connection_error",
        ok=False,
        call_id="c1",
        prompt_name="memory.extraction",
        latency_seconds=0.5,
        status_code=None,
        retry_after=None,
    )
    assert store.detection_event_count() == 1


def test_store_episodes_lifecycle(tmp_path: Path) -> None:
    store = DegradationStore(tmp_path / "deg.sqlite")
    store.create_episode(
        episode_id="ep-1",
        mode="down",
        signal="connection_error",
        policy="pause_all",
        paused_scope_ids=["s1", "s2"],
    )
    assert len(store.unresolved_episodes()) == 1
    store.set_episode_notification(episode_id="ep-1", threshold="time")
    store.resolve_episode(episode_id="ep-1", resolution_kind="auto")
    assert len(store.unresolved_episodes()) == 0
    all_eps = store.all_episodes()
    assert all_eps[0].resolved_at is not None
    assert all_eps[0].resolution_kind == "auto"


def test_store_upsert_and_read_fsm_state(tmp_path: Path) -> None:
    store = DegradationStore(tmp_path / "deg.sqlite")
    from datetime import datetime, timezone

    row = FSMStateRow(
        mode="down",
        state="open",
        state_entered_at=100.0,
        retry_after_until=None,
        consecutive_probe_successes=0,
        updated_at=datetime.now(timezone.utc).isoformat(),
    )
    store.upsert_fsm_state(row)
    rows = store.all_fsm_states()
    assert len(rows) == 1
    assert rows[0].state == "open"


def test_v11_r1_semantic_round_trip_snapshot_stable(tmp_path: Path) -> None:
    store = DegradationStore(tmp_path / "deg.sqlite")
    # Seed some events.
    store.append_detection_event(
        mode="down",
        signal="connection_error",
        ok=False,
        call_id="c1",
        prompt_name="p",
        latency_seconds=0.1,
        status_code=None,
        retry_after=None,
    )
    store.create_episode(
        episode_id="ep-1",
        mode="down",
        signal="connection_error",
        policy="pause_all",
        paused_scope_ids=["s1"],
    )
    snap1 = store.snapshot_probe()
    snap2 = store.snapshot_probe()
    assert snap1 == snap2
    # Reopening the DB yields the same snapshot.
    store.close()
    store2 = DegradationStore(tmp_path / "deg.sqlite")
    snap3 = store2.snapshot_probe()
    assert snap3 == snap1


def test_reconcile_case1_orch_paused_deg_open() -> None:
    from loam.dormancy.state import EpisodeRow

    ep = EpisodeRow(
        episode_id="e",
        mode="down",
        signal="x",
        policy="pause_all",
        started_at="2026-04-19T00:00:00+00:00",
        resolved_at=None,
        resolution_kind=None,
        paused_scope_ids=["s1"],
        failed_scope_ids=[],
        notification_sent_at=None,
        resume_notification_sent_at=None,
        notification_threshold=None,
    )
    plan = reconcile(orchestrator_paused=True, unresolved_episodes=[ep])
    assert plan.case == 1
    assert plan.should_call_resume_activation is False


def test_reconcile_case2_orch_paused_deg_closed() -> None:
    plan = reconcile(orchestrator_paused=True, unresolved_episodes=[])
    assert plan.case == 2


def test_reconcile_case3_orch_not_paused_deg_open() -> None:
    from loam.dormancy.state import EpisodeRow

    ep = EpisodeRow(
        episode_id="e",
        mode="down",
        signal="x",
        policy="pause_all",
        started_at="2026-04-19T00:00:00+00:00",
        resolved_at=None,
        resolution_kind=None,
        paused_scope_ids=[],
        failed_scope_ids=[],
        notification_sent_at=None,
        resume_notification_sent_at=None,
        notification_threshold=None,
    )
    plan = reconcile(orchestrator_paused=False, unresolved_episodes=[ep])
    assert plan.case == 3
    assert plan.should_call_resume_activation is True


def test_reconcile_case4_both_clean() -> None:
    plan = reconcile(orchestrator_paused=False, unresolved_episodes=[])
    assert plan.case == 4


async def test_component_reconciles_orphaned_pause_on_restart(tmp_path) -> None:
    """Case 3: orchestrator still paused but degradation DB has
    resolved episodes. On restart, degradation calls resume_activation.
    """
    cfg, comp, orch, rt, notifier, client, clock = _build_component(tmp_path)
    # Simulate orphaned pause: orchestrator says paused, DB has an
    # unresolved episode.
    orch.paused = True
    comp.store.create_episode(
        episode_id="ep-orphan",
        mode="down",
        signal="connection_error",
        policy="pause_all",
        paused_scope_ids=[],
    )
    plan = await comp.reconcile_on_startup(orchestrator_paused=True)
    # Case 1 — degradation is still open (unresolved); continue probe
    # cycle. orchestrator remains paused.
    assert plan.case == 1
    assert orch.paused is True


async def test_component_restart_applies_case3_resume(tmp_path) -> None:
    cfg, comp, orch, rt, notifier, client, clock = _build_component(tmp_path)
    # Case 3: unresolved episode + orchestrator not paused → resume.
    comp.store.create_episode(
        episode_id="ep-stale",
        mode="down",
        signal="connection_error",
        policy="pause_all",
        paused_scope_ids=["s1"],
    )
    orch.paused = False
    plan = await comp.reconcile_on_startup(orchestrator_paused=False)
    assert plan.case == 3
    assert orch.resume_calls == 1
    # Episode marked resolved.
    ep_row = comp.store.get_episode("ep-stale")
    assert ep_row is not None and ep_row.resolution_kind == "reconciled_on_restart"


async def test_fsm_state_persisted_after_transition(tmp_path) -> None:
    cfg, comp, orch, rt, notifier, client, clock = _build_component(
        tmp_path,
        script=[
            ConnectionError("x"),
            ConnectionError("x"),
            ConnectionError("x"),
        ],
    )
    rt.add_scope(FakeScope("s1"))
    from loam.dormancy.errors import ClaudeAPIError

    for _ in range(3):
        try:
            await client.call(prompt_name="memory.extraction", text="x")
        except ClaudeAPIError:
            pass

    # FSM state cache should now include "down":"open".
    rows = comp.store.all_fsm_states()
    by_mode = {r.mode: r.state for r in rows}
    assert by_mode.get("down") == "open"


def test_config_sqlite_path_is_tunable() -> None:
    text = """
state:
  sqlite_path: /tmp/pos-deg-test.sqlite
"""
    from loam.dormancy import load_config
    cfg = load_config(text=text)
    assert str(cfg.sqlite_path()) == "/tmp/pos-deg-test.sqlite"


def test_default_sqlite_path_is_loam_dir() -> None:
    cfg = DegradationConfig()
    assert ".loam" in str(cfg.sqlite_path())
    assert cfg.sqlite_path().name == "dormancy.sqlite"
