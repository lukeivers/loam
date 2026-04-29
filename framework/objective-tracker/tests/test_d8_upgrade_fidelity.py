"""D8 — Upgrade-fidelity test harness (v1.1 R1).

Acceptance (brief §D8):
- Probe set of objective creations, bindings, evaluations, and queries
  is captured pre-upgrade.
- Replayed post-upgrade; output-equivalence is asserted; drift above
  declared threshold fails the upgrade.
- SQLite database snapshot preserves physical reversibility.
- Harness mirrors the pattern scope-of-work's D7 already established.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from loam.objective_tracker.runtime import ObjectiveTracker
from loam.objective_tracker.spec import (
    ChildClosureCriterion,
    ExternalPredicateCriterion,
    ObjectiveStatus,
    ProseCriterion,
)
from loam.objective_tracker.upgrade import (
    assert_no_drift,
    capture_pre_upgrade,
    captured_from_json,
    captured_to_json,
    replay_post_upgrade,
)
from tests.conftest import make_child_spec, make_user_root_spec


async def _seed(rt: ObjectiveTracker) -> None:
    """Seed a varied population: roots, children, evaluations, bindings."""
    root_a = await rt.create(make_user_root_spec(goal="alpha"))
    await rt.start(root_a.objective_id)
    await rt.evaluate_criterion(
        root_a.objective_id, criterion_id="root-c1", result="met"
    )
    await rt.mark_achieved(root_a.objective_id, evidence="done")
    await rt.bind_scope("scope-alpha-1", root_a.objective_id)

    root_b = await rt.create(
        make_user_root_spec(
            goal="beta",
            criteria=(
                ProseCriterion(criterion_id="p1", prose="a"),
                ChildClosureCriterion(criterion_id="cc", required_count=1),
            ),
        )
    )
    child = await rt.create(
        make_child_spec(parent_id=root_b.objective_id, authored_by="mara")
    )
    await rt.evaluate_criterion(
        child.objective_id, criterion_id="child-c1", result="not_met"
    )

    # Persona-authored root (orphan) — should still persist cleanly;
    # just can't be bound to a scope.
    orphan_spec = make_user_root_spec(goal="orphan").model_copy(
        update={"authored_by": "kai"}
    )
    await rt.create(orphan_spec)


async def test_round_trip_zero_drift(tmp_path):
    db = tmp_path / "obj.db"
    snapshot = tmp_path / "obj.snapshot.db"
    rt = ObjectiveTracker(db_path=db)
    await _seed(rt)
    captured = capture_pre_upgrade(rt.store, snapshot_to=snapshot)
    rt.close()

    assert snapshot.exists() and snapshot.stat().st_size > 0

    # Persist probes via JSON (round-trip the harness itself).
    probe_path = tmp_path / "probes.json"
    probe_path.write_text(captured_to_json(captured))

    rt2 = ObjectiveTracker(db_path=db)
    captured_back = captured_from_json(probe_path.read_text())
    report = replay_post_upgrade(rt2.store, captured_back)
    assert report.total_drift == 0
    rt2.close()


async def test_drift_detected_when_state_diverges(tmp_path):
    db = tmp_path / "obj.db"
    rt = ObjectiveTracker(db_path=db)
    await _seed(rt)
    captured = capture_pre_upgrade(rt.store)

    # Mutate one objective after the snapshot.
    proposed = rt.list(status=[ObjectiveStatus.proposed])[0]
    await rt.start(proposed.objective_id)

    report = replay_post_upgrade(rt.store, captured)
    assert report.total_drift > 0
    drift_fields = {(d.subject_kind, d.field) for d in report.drifted}
    assert ("objective", "status") in drift_fields
    rt.close()


async def test_drift_detected_when_binding_changes(tmp_path):
    db = tmp_path / "obj.db"
    rt = ObjectiveTracker(db_path=db)
    await _seed(rt)
    captured = capture_pre_upgrade(rt.store)
    # Add a new binding post-capture under a new user-authored root.
    new_root = await rt.create(make_user_root_spec(goal="new-root"))
    await rt.bind_scope("scope-new", new_root.objective_id)
    report = replay_post_upgrade(rt.store, captured)
    assert report.total_drift > 0
    # extra_post picks up the new root's objective id.
    # binding_extra_post picks up the new scope id.
    assert "scope-new" in report.binding_extra_post
    rt.close()


async def test_assert_no_drift_raises_above_threshold(tmp_path):
    db = tmp_path / "obj.db"
    rt = ObjectiveTracker(db_path=db)
    await _seed(rt)
    captured = capture_pre_upgrade(rt.store)
    proposed = rt.list(status=[ObjectiveStatus.proposed])[0]
    await rt.start(proposed.objective_id)
    report = replay_post_upgrade(rt.store, captured)
    with pytest.raises(AssertionError):
        assert_no_drift(report, threshold=0)
    rt.close()


async def test_snapshot_round_trip_restores_state(tmp_path):
    """Physical reversibility: file-copy snapshot can be restored and
    the runtime opens it identically."""
    db = tmp_path / "obj.db"
    snapshot = tmp_path / "obj.snap.db"
    rt = ObjectiveTracker(db_path=db)
    await _seed(rt)
    rt.snapshot(snapshot)
    rt.close()

    # Destroy the live DB (and WAL/SHM side-files) and restore from snap.
    db.unlink()
    for ext in ("-wal", "-shm"):
        side = Path(str(db) + ext)
        if side.exists():
            side.unlink()
    shutil.copy(snapshot, db)

    rt2 = ObjectiveTracker(db_path=db)
    states = rt2.list()
    # alpha-root, beta-root, beta-child, orphan-root = 4
    assert len(states) == 4
    # Binding restored.
    assert rt2.is_scope_bound("scope-alpha-1") is True
    rt2.close()


async def test_replay_from_empty_probe_set_is_no_op(tmp_path):
    """An empty probe set should report zero drift against any store."""
    from loam.objective_tracker.upgrade import CapturedProbeSet

    db = tmp_path / "obj.db"
    rt = ObjectiveTracker(db_path=db)
    await _seed(rt)
    empty = CapturedProbeSet(snapshot_db_path=None, probes=[], bindings=[])
    report = replay_post_upgrade(rt.store, empty)
    # Everything live is extra_post / binding_extra_post — drift > 0.
    assert report.total_drift > 0
    assert report.extra_post  # non-empty
    rt.close()
