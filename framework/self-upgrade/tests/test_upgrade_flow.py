"""D5 + D6 + D8 + D9 — integration tests for the full upgrade flow.

Uses a synthetic adapter bundle so the tests don't need a live
orchestrator; every call the upgrade flow makes against the live
system is a method on ``FakeAdapters``.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from self_upgrade.config import UpgradeConfig
from self_upgrade.manifest import Manifest
from self_upgrade.paths import Paths
from self_upgrade.snapshot import capture_substrate_snapshots
from self_upgrade.upgrade import UpgradeResult, execute_upgrade


# ---- fake adapter --------------------------------------------------


@dataclass
class FakeDrift:
    passed: bool = True
    verdict_flip_fraction: float = 0.0
    mean_recall_delta: float = 0.0
    over_tolerance_fraction: float = 0.0


@dataclass
class FakeScopeDrift:
    total_drift: int = 0


@dataclass
class FakeSurvival:
    persona_identity: dict
    authority_boundary: dict
    current_scope_context: list
    pending_decisions: list
    recent_corrections: list

    def to_dict(self) -> dict:
        return {
            "persona_identity": self.persona_identity,
            "authority_boundary": self.authority_boundary,
            "current_scope_context": self.current_scope_context,
            "pending_decisions": self.pending_decisions,
            "recent_corrections": self.recent_corrections,
        }


@dataclass
class FakeAdapters:
    pid: int | None = 12345
    drain_after_calls: int = 1
    clause_a_result: bool = True
    memory_drift: FakeDrift = field(default_factory=FakeDrift)
    scope_drift: FakeScopeDrift = field(default_factory=FakeScopeDrift)
    objective_drift: FakeScopeDrift = field(default_factory=FakeScopeDrift)
    personas: dict[str, FakeSurvival] = field(default_factory=dict)
    restart_will_raise: bool = False
    boot_will_succeed: bool = True

    _drain_calls: int = 0
    paused: bool = False
    resumed: bool = False
    restart_count: int = 0

    def pause_activation(self, reason: str) -> None:
        self.paused = True

    def is_drained(self) -> bool:
        self._drain_calls += 1
        return self._drain_calls >= self.drain_after_calls

    def orchestrator_pid(self) -> int | None:
        return self.pid

    def restart_orchestrator(self) -> None:
        self.restart_count += 1
        if self.restart_will_raise:
            raise RuntimeError("launchctl exited non-zero")
        # After restart, "boot" — simulate the orchestrator coming back
        self._booted = True

    def is_orchestrator_up(self) -> bool:
        return self.boot_will_succeed

    def no_op_rpc(self) -> bool:
        return self.clause_a_result

    def resume_activation(self) -> None:
        self.resumed = True

    def post_survival_payloads(self) -> dict[str, Any]:
        return dict(self.personas)

    def post_memory_drift(self) -> Any:
        return self.memory_drift

    def post_scope_drift(self) -> Any:
        return self.scope_drift

    def post_objective_drift(self) -> Any:
        return self.objective_drift


def _good_survival() -> FakeSurvival:
    return FakeSurvival(
        persona_identity={"handle": "eve"},
        authority_boundary={"tier_a": "require"},
        current_scope_context=[],
        pending_decisions=[],
        recent_corrections=[],
    )


# ---- fixtures --------------------------------------------------------


@pytest.fixture
def populated_paths(tmp_path: Path, monkeypatch) -> Paths:
    """Paths with substrate dbs present (empty) + a prior release tree
    and a staging release tree with matching sha content."""
    monkeypatch.setenv("POS_BASE_DIR", str(tmp_path))
    p = Paths.from_env()

    # Substrate setup: write minimal empty files so snapshot can run
    for sub in (
        p.scope_of_work_db,
        p.objective_tracker_db,
        p.orchestrator_db,
        p.degradation_db,
    ):
        sub.parent.mkdir(parents=True, exist_ok=True)
        sub.write_bytes(b"fake-sqlite-bytes")
    p.memory_db.mkdir(parents=True, exist_ok=True)
    (p.memory_db / "memory.kuzu").write_bytes(b"fake-kuzu")
    p.aggregator_db.parent.mkdir(parents=True, exist_ok=True)
    p.aggregator_db.write_bytes(b"fake-duckdb")

    # Prior release tree + current symlink
    prior = p.release_dir("pos-v2-v0.1.0")
    prior.mkdir(parents=True)
    (prior / "README.md").write_text("prior\n")
    p.current_link.parent.mkdir(parents=True, exist_ok=True)
    import os
    if p.current_link.exists() or p.current_link.is_symlink():
        p.current_link.unlink()
    os.symlink(str(prior), str(p.current_link))

    return p


@pytest.fixture
def good_manifest_and_staging(populated_paths: Paths) -> tuple[Manifest, Path]:
    """Build a manifest where all file shas line up with a staging tree."""
    tag = "pos-v2-v0.2.0"
    staging = populated_paths.staging_dir(tag)
    staging.mkdir(parents=True)

    # Put two files with known content
    files: list[dict] = []
    for rel, content in [
        ("framework/a.py", b"print('a')\n"),
        ("framework/b.py", b"print('b')\n"),
    ]:
        f = staging / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(content)
        sha = hashlib.sha256(content).hexdigest()
        files.append({
            "path": rel,
            "expected_pre_sha": None,
            "expected_post_sha": sha,
            "change_kind": "new",
        })

    manifest = Manifest.model_validate({
        "release_tag": tag,
        "commit_sha": "abcdef1",
        "files": files,
        "component_schemas": [
            {"component": "memory", "version_pre": 3, "version_post": 3},
        ],
    })
    return manifest, staging


# ---- happy path -----------------------------------------------------


def test_upgrade_accept_happy_path(
    populated_paths: Paths, good_manifest_and_staging
) -> None:
    manifest, staging = good_manifest_and_staging
    adapters = FakeAdapters(personas={"eve": _good_survival()})

    result = execute_upgrade(
        manifest=manifest,
        paths=populated_paths,
        config=UpgradeConfig(),
        staging_dir=staging,
        prior_tag="pos-v2-v0.1.0",
        adapters=adapters,
    )

    assert result.accepted, result.halt_reason
    assert not result.rolled_back
    assert all(r["passed"] for r in result.clause_results.values())
    assert adapters.paused
    assert adapters.resumed
    assert adapters.restart_count == 1

    # accepted.json written
    accepted = populated_paths.accepted_json(manifest.release_tag)
    assert accepted.exists()
    data = json.loads(accepted.read_text())
    assert data["release_tag"] == manifest.release_tag
    assert all(r["passed"] for r in data["clause_verdicts"].values())


def test_upgrade_produces_pre_probe_and_post_probe_files(
    populated_paths: Paths, good_manifest_and_staging
) -> None:
    manifest, staging = good_manifest_and_staging
    adapters = FakeAdapters(personas={"eve": _good_survival()})
    execute_upgrade(
        manifest=manifest,
        paths=populated_paths,
        config=UpgradeConfig(),
        staging_dir=staging,
        prior_tag="pos-v2-v0.1.0",
        adapters=adapters,
    )
    assert populated_paths.pre_probe_json(manifest.release_tag).exists()
    assert populated_paths.post_probe_json(manifest.release_tag).exists()


# ---- failure paths (trigger rollback) -----------------------------


def test_upgrade_rolls_back_on_clause_a_failure(
    populated_paths: Paths, good_manifest_and_staging
) -> None:
    manifest, staging = good_manifest_and_staging
    adapters = FakeAdapters(
        personas={"eve": _good_survival()},
        clause_a_result=False,  # fail clause a
    )
    result = execute_upgrade(
        manifest=manifest,
        paths=populated_paths,
        config=UpgradeConfig(),
        staging_dir=staging,
        prior_tag="pos-v2-v0.1.0",
        adapters=adapters,
    )
    assert not result.accepted
    assert result.rolled_back
    assert result.rollback_success is True
    assert "a" in result.clause_results
    assert not result.clause_results["a"]["passed"]
    # After rollback, symlink points at prior release
    assert populated_paths.current_link.resolve() == populated_paths.release_dir(
        "pos-v2-v0.1.0"
    ).resolve()


def test_upgrade_rolls_back_on_clause_c_memory_drift(
    populated_paths: Paths, good_manifest_and_staging
) -> None:
    manifest, staging = good_manifest_and_staging
    adapters = FakeAdapters(
        personas={"eve": _good_survival()},
        memory_drift=FakeDrift(passed=False, over_tolerance_fraction=0.5),
    )
    result = execute_upgrade(
        manifest=manifest,
        paths=populated_paths,
        config=UpgradeConfig(),
        staging_dir=staging,
        prior_tag="pos-v2-v0.1.0",
        adapters=adapters,
    )
    assert not result.accepted
    assert result.rolled_back
    assert not result.clause_results["c"]["passed"]


def test_upgrade_halts_on_drain_timeout(
    populated_paths: Paths, good_manifest_and_staging
) -> None:
    manifest, staging = good_manifest_and_staging
    adapters = FakeAdapters(
        personas={"eve": _good_survival()},
        drain_after_calls=10_000,
    )
    cfg = UpgradeConfig(drain_timeout_seconds=0.2)
    result = execute_upgrade(
        manifest=manifest,
        paths=populated_paths,
        config=cfg,
        staging_dir=staging,
        prior_tag="pos-v2-v0.1.0",
        adapters=adapters,
    )
    assert not result.accepted
    # Drain timeout happens before swap — no rollback needed
    assert not result.rolled_back
    assert "drain_timeout" in (result.halt_reason or "")


def test_upgrade_halts_on_orchestrator_boot_failure(
    populated_paths: Paths, good_manifest_and_staging
) -> None:
    manifest, staging = good_manifest_and_staging
    adapters = FakeAdapters(
        personas={"eve": _good_survival()},
        boot_will_succeed=False,
    )
    cfg = UpgradeConfig(orchestrator_boot_timeout_seconds=0.2)
    result = execute_upgrade(
        manifest=manifest,
        paths=populated_paths,
        config=cfg,
        staging_dir=staging,
        prior_tag="pos-v2-v0.1.0",
        adapters=adapters,
    )
    assert not result.accepted
    assert result.rolled_back
    assert "boot_timeout" in (result.halt_reason or "")


def test_rollback_invoked_without_prior_tag_writes_rollback_failed(
    populated_paths: Paths, good_manifest_and_staging
) -> None:
    """Rollback with no prior tag still runs substrate restore; without
    symlink revert step, succeeds if substrate restore succeeds."""
    manifest, staging = good_manifest_and_staging
    adapters = FakeAdapters(
        personas={"eve": _good_survival()},
        clause_a_result=False,
    )
    result = execute_upgrade(
        manifest=manifest,
        paths=populated_paths,
        config=UpgradeConfig(),
        staging_dir=staging,
        prior_tag=None,  # no prior — first upgrade
        adapters=adapters,
    )
    assert not result.accepted
    assert result.rolled_back


# ---- progress callback ---------------------------------------------


def test_progress_callback_receives_every_stage(
    populated_paths: Paths, good_manifest_and_staging
) -> None:
    manifest, staging = good_manifest_and_staging
    adapters = FakeAdapters(personas={"eve": _good_survival()})
    stages: list[tuple[str, str]] = []

    def prog(stage: str, verdict: str, elapsed: float) -> None:
        stages.append((stage, verdict))

    execute_upgrade(
        manifest=manifest,
        paths=populated_paths,
        config=UpgradeConfig(),
        staging_dir=staging,
        prior_tag="pos-v2-v0.1.0",
        adapters=adapters,
        progress=prog,
    )
    names = [s[0] for s in stages]
    assert "pre_snapshot" in names
    assert "pre_probe" in names
    assert "pause_activation" in names
    assert "drain" in names
    assert "sigterm" in names
    assert "swap" in names
    assert "orchestrator_restart" in names
    assert "post_probe" in names
    assert "accept" in names
    # Every stage here should be 'ok'
    assert all(v == "ok" for _, v in stages)
