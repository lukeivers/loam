"""D7 — upgrade-fidelity test harness (v1.1 R1).

Acceptance (brief D7):
- A probe set of scope creations, transitions, and queries is captured
  pre-upgrade.
- The same probes are replayed post-upgrade.
- Output-equivalence is asserted; drift above a declared threshold
  fails the upgrade.
- Sqlite database snapshot preserves physical reversibility alongside
  the semantic test.
"""

from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path

import pytest

from src.runtime import ScopeRuntime
from src.spec import Budget, ScopeState
from src.store import EventStore
from src.upgrade import (
    assert_no_drift,
    capture_pre_upgrade,
    captured_from_json,
    captured_to_json,
    replay_post_upgrade,
)
from tests.conftest import make_spec


async def _seed(rt: ScopeRuntime) -> None:
    """Seed a small population of scopes with varied histories."""
    a = await rt.create(make_spec(goal="alpha", owner_persona="eve"))
    await rt.start(a.scope_id)
    await rt.debit(a.scope_id, input_tokens=100, output_tokens=50, prompt_name="p1", model="claude")
    await rt.complete(a.scope_id, evaluations=[("c1", "met", None)])

    b = await rt.create(make_spec(goal="beta", budget=Budget(tokens=200)))
    await rt.start(b.scope_id)
    await rt.debit(b.scope_id, input_tokens=300)  # over budget → paused
    # Leave b paused with a pending extension request.

    c = await rt.create(make_spec(goal="gamma"))
    # c stays proposed.


async def test_round_trip_zero_drift(tmp_path):
    db = tmp_path / "scope.db"
    snapshot = tmp_path / "scope.snapshot.db"
    rt = ScopeRuntime(db_path=db, pending_extension_dir=tmp_path / "pending")
    await _seed(rt)
    captured = capture_pre_upgrade(rt.store, snapshot_to=snapshot)
    rt.close()

    # Snapshot exists and is non-empty.
    assert snapshot.exists() and snapshot.stat().st_size > 0

    # Persist the captured probe set as JSON (round-trip the harness too).
    probe_path = tmp_path / "probes.json"
    probe_path.write_text(captured_to_json(captured))

    # "Upgrade" — re-open the same DB with a fresh store + projector.
    # In a real upgrade the projector code may have changed; here the
    # determinism check is that the same code produces the same answer.
    rt2 = ScopeRuntime(db_path=db, pending_extension_dir=tmp_path / "pending2")
    captured_back = captured_from_json(probe_path.read_text())
    report = replay_post_upgrade(rt2.store, captured_back)
    assert report.total_drift == 0
    rt2.close()


async def test_drift_detection_when_state_diverges(tmp_path):
    db = tmp_path / "scope.db"
    rt = ScopeRuntime(db_path=db, pending_extension_dir=tmp_path / "pending")
    await _seed(rt)
    captured = capture_pre_upgrade(rt.store)

    # Mutate one scope after the snapshot to simulate post-upgrade drift.
    proj = rt.list(states=[ScopeState.proposed])[0]
    await rt.start(proj.scope_id)

    report = replay_post_upgrade(rt.store, captured)
    assert report.total_drift > 0
    drift_fields = {(d.scope_id, d.field) for d in report.drifted}
    assert any(f == "state" for _, f in drift_fields)
    rt.close()


async def test_assert_no_drift_raises_above_threshold(tmp_path):
    db = tmp_path / "scope.db"
    rt = ScopeRuntime(db_path=db, pending_extension_dir=tmp_path / "pending")
    await _seed(rt)
    captured = capture_pre_upgrade(rt.store)
    proj = rt.list(states=[ScopeState.proposed])[0]
    await rt.start(proj.scope_id)
    report = replay_post_upgrade(rt.store, captured)
    with pytest.raises(AssertionError):
        assert_no_drift(report, threshold=0)
    rt.close()


async def test_snapshot_round_trip_restores_state(tmp_path):
    """Physical reversibility: file-copy snapshot can be restored and
    the runtime opens it identically."""
    db = tmp_path / "scope.db"
    snapshot = tmp_path / "scope.snapshot.db"
    rt = ScopeRuntime(db_path=db, pending_extension_dir=tmp_path / "pending")
    await _seed(rt)
    rt.snapshot(snapshot)
    rt.close()

    # Pretend an upgrade went wrong; restore the snapshot over the live DB.
    db.unlink()
    # Also remove any side-files from the live DB.
    for ext in ("-wal", "-shm"):
        side = Path(str(db) + ext)
        if side.exists():
            side.unlink()
    shutil.copy(snapshot, db)

    rt2 = ScopeRuntime(db_path=db, pending_extension_dir=tmp_path / "pending2")
    # The seeded scopes are visible.
    states = rt2.list()
    assert len(states) == 3
    rt2.close()
