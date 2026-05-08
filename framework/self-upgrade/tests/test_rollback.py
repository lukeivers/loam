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

"""D8 — rollback success + clean-failure tests.

The failed-rollback (rollback itself fails) scenario is exercised by
the manual destructive-test runbook per Luke's ruling; this module
covers the two in-CI paths: success-path and clean-failure-path.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from loam.self_upgrade.paths import Paths
from loam.self_upgrade.rollback import RollbackFailed, rollback
from loam.self_upgrade.snapshot import capture_substrate_snapshots


def _seed_substrate(p: Paths) -> None:
    """Populate every substrate path so snapshot has something to
    capture."""
    for sub in (
        p.scope_of_work_db,
        p.objective_tracker_db,
        p.orchestrator_db,
        p.degradation_db,
    ):
        sub.parent.mkdir(parents=True, exist_ok=True)
        sub.write_bytes(b"sqlite-original")
    p.memory_db.mkdir(parents=True, exist_ok=True)
    (p.memory_db / "memory.kuzu").write_bytes(b"kuzu-original")
    p.aggregator_db.parent.mkdir(parents=True, exist_ok=True)
    p.aggregator_db.write_bytes(b"duckdb-original")


def _make_release_tree(p: Paths, tag: str) -> Path:
    r = p.release_dir(tag)
    r.mkdir(parents=True, exist_ok=True)
    (r / "version.txt").write_text(tag)
    return r


@pytest.fixture
def ready_paths(tmp_path: Path, monkeypatch) -> Paths:
    monkeypatch.setenv("POS_BASE_DIR", str(tmp_path))
    p = Paths.from_env()
    _seed_substrate(p)
    # Snapshot the original state
    capture_substrate_snapshots(p, "pos-v2-v0.2.0", probe_fn=None)
    # Prior release + symlink pointing to staging (simulating a
    # post-swap state we now want to roll back)
    prior = _make_release_tree(p, "pos-v2-v0.1.0")
    staging = _make_release_tree(p, "pos-v2-v0.2.0")
    p.current_link.parent.mkdir(parents=True, exist_ok=True)
    if p.current_link.is_symlink():
        p.current_link.unlink()
    os.symlink(str(staging), str(p.current_link))
    return p


def test_rollback_restores_substrate(ready_paths: Paths) -> None:
    # Corrupt live state first (simulating a partially-applied upgrade)
    ready_paths.scope_of_work_db.write_bytes(b"corrupt")
    (ready_paths.memory_db / "memory.kuzu").write_bytes(b"corrupt")

    report = rollback(
        paths=ready_paths,
        tag="pos-v2-v0.2.0",
        prior_tag="pos-v2-v0.1.0",
        failing_clauses=["c"],
        clause_details={"c": {"reason": "memory drift"}},
    )
    assert report.success
    assert "substrates_restored" in report.steps_completed
    assert ready_paths.scope_of_work_db.read_bytes() == b"sqlite-original"
    assert (ready_paths.memory_db / "memory.kuzu").read_bytes() == b"kuzu-original"


def test_rollback_reverts_symlink(ready_paths: Paths) -> None:
    assert (
        ready_paths.current_link.resolve()
        == ready_paths.release_dir("pos-v2-v0.2.0").resolve()
    )
    rollback(
        paths=ready_paths,
        tag="pos-v2-v0.2.0",
        prior_tag="pos-v2-v0.1.0",
        failing_clauses=["g"],
        clause_details={},
    )
    assert (
        ready_paths.current_link.resolve()
        == ready_paths.release_dir("pos-v2-v0.1.0").resolve()
    )


def test_rollback_calls_orchestrator_restart(ready_paths: Paths) -> None:
    restarts = []
    rollback(
        paths=ready_paths,
        tag="pos-v2-v0.2.0",
        prior_tag="pos-v2-v0.1.0",
        failing_clauses=["a"],
        clause_details={},
        restart_orchestrator=lambda: restarts.append(1),
    )
    assert restarts == [1]


def test_rollback_writes_history_record(ready_paths: Paths) -> None:
    report = rollback(
        paths=ready_paths,
        tag="pos-v2-v0.2.0",
        prior_tag="pos-v2-v0.1.0",
        failing_clauses=["e"],
        clause_details={"e": {"reason": "silent schema bump"}},
    )
    record = ready_paths.rolled_back_json("pos-v2-v0.2.0")
    assert record.exists()
    data = json.loads(record.read_text())
    assert data["tag"] == "pos-v2-v0.2.0"
    assert data["failing_clauses"] == ["e"]
    assert data["success"] is True


def test_rollback_fails_when_snapshots_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("POS_BASE_DIR", str(tmp_path))
    p = Paths.from_env()
    _seed_substrate(p)
    # No snapshot taken
    prior = _make_release_tree(p, "pos-v2-v0.1.0")
    staging = _make_release_tree(p, "pos-v2-v0.2.0")
    p.current_link.parent.mkdir(parents=True, exist_ok=True)
    if p.current_link.is_symlink():
        p.current_link.unlink()
    os.symlink(str(staging), str(p.current_link))

    with pytest.raises(RollbackFailed) as exc:
        rollback(
            paths=p,
            tag="pos-v2-v0.2.0",
            prior_tag="pos-v2-v0.1.0",
            failing_clauses=["c"],
            clause_details={},
        )
    assert exc.value.report.success is False
    fail_record = p.history / "pos-v2-v0.2.0-rollback-failed.json"
    assert fail_record.exists()


def test_rollback_no_prior_tag_still_restores_substrate(ready_paths: Paths) -> None:
    ready_paths.scope_of_work_db.write_bytes(b"corrupt")
    report = rollback(
        paths=ready_paths,
        tag="pos-v2-v0.2.0",
        prior_tag=None,  # first upgrade — no prior to revert to
        failing_clauses=["c"],
        clause_details={},
    )
    assert report.success
    assert ready_paths.scope_of_work_db.read_bytes() == b"sqlite-original"


def test_rollback_round_trip_matches_pre_upgrade(ready_paths: Paths) -> None:
    """Success-path verification per D8 acceptance: post-rollback probe
    round-trips the pre-upgrade probe results.

    We use the substrate-hash probe (cheap, deterministic)."""
    from loam.self_upgrade.probes import post_upgrade_probe_hashes

    pre = post_upgrade_probe_hashes(ready_paths)

    # Simulate a "bad" upgrade then roll back
    ready_paths.scope_of_work_db.write_bytes(b"upgrade-wrote-this")
    (ready_paths.memory_db / "memory.kuzu").write_bytes(b"upgrade-wrote-this-too")

    rollback(
        paths=ready_paths,
        tag="pos-v2-v0.2.0",
        prior_tag="pos-v2-v0.1.0",
        failing_clauses=["c"],
        clause_details={},
    )
    post = post_upgrade_probe_hashes(ready_paths)
    assert pre == post, f"Round-trip mismatch: {pre} != {post}"
