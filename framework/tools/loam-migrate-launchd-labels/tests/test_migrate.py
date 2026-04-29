"""AC.RNM-1c.3 — launchd-label migration helper contract.

Four named cases per the M1c sub-plan §4.AC.RNM-1c.3:

  1. Empty / fresh-machine LaunchAgents/ → NOTHING_TO_MIGRATE.
  2. One legacy 4-segment plist → MIGRATED (bootout + rename-aside).
  3. Multiple legacy 4-segment plists → MIGRATED for all.
  4. Bootout failure on one legacy plist → PARTIAL_FAILURE.

Plus an idempotency check: case 2 followed by re-invocation hits
case 1 (renamed files no longer match the filter).

Plus shape-discrimination checks: 3-segment pre-#6 orphans (the
orphan-plist-cleanup tool's mission) and post-M1c live shape
(``com.loam.<slug>.<kind>``) are NOT processed by this helper.
"""

from __future__ import annotations

from pathlib import Path

from loam_migrate_launchd_labels import (
    BootoutResult,
    MigrationOutcome,
    migrate_launchd_labels,
)
from loam_migrate_launchd_labels.migrate import (
    RENAMED_SUFFIX,
    _is_legacy_namespaced_plist,
)


# ---- Test doubles --------------------------------------------------


class _BootoutRecorder:
    """Test double for the launchctl bootout call."""

    def __init__(
        self,
        *,
        always_ok: bool = True,
        fail_for: set[str] | None = None,
    ) -> None:
        self.always_ok = always_ok
        self.fail_for = fail_for or set()
        self.called_with: list[str] = []

    def __call__(self, label: str) -> BootoutResult:
        self.called_with.append(label)
        if label in self.fail_for:
            return BootoutResult(
                label=label,
                ok=False,
                returncode=1,
                stderr="Permission denied",
            )
        return BootoutResult(label=label, ok=True, returncode=0, stderr="")


# ---- Filter discrimination ----------------------------------------


class TestFilter:
    def test_4_segment_pos_v2_is_legacy(self) -> None:
        assert _is_legacy_namespaced_plist(
            "com.pos-v2.alpha.memory-graphiti.plist"
        )
        assert _is_legacy_namespaced_plist(
            "com.pos-v2.alpha.orchestrator.plist"
        )
        assert _is_legacy_namespaced_plist(
            "com.pos-v2.alpha.memory-write-worker.plist"
        )

    def test_3_segment_pos_v2_is_not_legacy_namespaced(self) -> None:
        # Pre-#6 single-segment orphan — orphan-plist-cleanup's mission.
        assert not _is_legacy_namespaced_plist(
            "com.pos-v2.memory-graphiti.plist"
        )

    def test_3_segment_pos_is_not_legacy_namespaced(self) -> None:
        # v1-era single-segment orphan — orphan-plist-cleanup's mission.
        assert not _is_legacy_namespaced_plist("com.pos.orchestrator.plist")

    def test_post_m1c_live_shape_is_not_legacy(self) -> None:
        # Post-M1c live shape — must NOT be touched by the helper.
        assert not _is_legacy_namespaced_plist(
            "com.loam.alpha.memory-graphiti.plist"
        )

    def test_unrelated_plists_are_not_legacy(self) -> None:
        assert not _is_legacy_namespaced_plist("com.apple.something.plist")
        assert not _is_legacy_namespaced_plist("README.txt")
        assert not _is_legacy_namespaced_plist(
            "com.pos-v2.a.b.c.plist"  # 5 segments
        )


# ---- Migration outcomes -------------------------------------------


def _populate(
    agents: Path,
    *,
    legacy: tuple[str, ...] = (),
    keep: tuple[str, ...] = (),
) -> None:
    """Populate ``agents`` with named plist filenames + dummy bodies."""
    agents.mkdir(parents=True, exist_ok=True)
    for name in legacy + keep:
        (agents / name).write_text("<plist body/>")


def test_case_1_empty_launch_agents_dir_nothing_to_migrate(
    tmp_path: Path,
) -> None:
    """Empty / fresh-machine LaunchAgents → NOTHING_TO_MIGRATE."""
    agents = tmp_path / "LaunchAgents"
    agents.mkdir()

    recorder = _BootoutRecorder()
    result = migrate_launchd_labels(
        launch_agents_dir=agents, uid=501, bootout_fn=recorder
    )

    assert result.outcome is MigrationOutcome.NOTHING_TO_MIGRATE
    assert result.is_clean
    assert result.processed == ()
    assert result.failed == ()
    assert recorder.called_with == []


def test_case_1_missing_launch_agents_dir_nothing_to_migrate(
    tmp_path: Path,
) -> None:
    """Non-existent LaunchAgents dir → NOTHING_TO_MIGRATE (no raise)."""
    missing = tmp_path / "no-such-dir"
    recorder = _BootoutRecorder()
    result = migrate_launchd_labels(
        launch_agents_dir=missing, uid=501, bootout_fn=recorder
    )
    assert result.outcome is MigrationOutcome.NOTHING_TO_MIGRATE
    assert recorder.called_with == []


def test_case_2_one_legacy_plist_migrated(tmp_path: Path) -> None:
    """One pre-M1c 4-segment plist → bootout + rename."""
    agents = tmp_path / "LaunchAgents"
    _populate(
        agents,
        legacy=("com.pos-v2.alpha.memory-graphiti.plist",),
    )

    recorder = _BootoutRecorder()
    result = migrate_launchd_labels(
        launch_agents_dir=agents, uid=501, bootout_fn=recorder
    )

    assert result.outcome is MigrationOutcome.MIGRATED
    assert result.is_clean
    assert recorder.called_with == ["com.pos-v2.alpha.memory-graphiti"]
    # Original plist gone; .bak twin present.
    assert not (agents / "com.pos-v2.alpha.memory-graphiti.plist").exists()
    assert (
        agents
        / f"com.pos-v2.alpha.memory-graphiti{RENAMED_SUFFIX}"
    ).exists()


def test_case_3_multiple_legacy_plists_all_migrated(tmp_path: Path) -> None:
    """Multiple 4-segment plists → all booted out + renamed."""
    agents = tmp_path / "LaunchAgents"
    _populate(
        agents,
        legacy=(
            "com.pos-v2.alpha.memory-graphiti.plist",
            "com.pos-v2.alpha.orchestrator.plist",
            "com.pos-v2.alpha.memory-write-worker.plist",
        ),
        keep=(
            # Pre-#6 orphans — orphan-plist-cleanup's mission; must
            # NOT be touched by this helper.
            "com.pos-v2.memory-graphiti.plist",
            "com.pos.orchestrator.plist",
            # Post-M1c live shape — must NOT be touched.
            "com.loam.alpha.memory-graphiti.plist",
            # Unrelated plists.
            "com.apple.something.plist",
        ),
    )

    recorder = _BootoutRecorder()
    result = migrate_launchd_labels(
        launch_agents_dir=agents, uid=501, bootout_fn=recorder
    )

    assert result.outcome is MigrationOutcome.MIGRATED
    assert result.is_clean
    # Three legacy plists processed.
    assert set(recorder.called_with) == {
        "com.pos-v2.alpha.memory-graphiti",
        "com.pos-v2.alpha.orchestrator",
        "com.pos-v2.alpha.memory-write-worker",
    }
    for legacy_base in (
        "com.pos-v2.alpha.memory-graphiti",
        "com.pos-v2.alpha.orchestrator",
        "com.pos-v2.alpha.memory-write-worker",
    ):
        assert not (agents / f"{legacy_base}.plist").exists()
        assert (agents / f"{legacy_base}{RENAMED_SUFFIX}").exists()
    # The keep set is untouched.
    assert (agents / "com.pos-v2.memory-graphiti.plist").exists()
    assert (agents / "com.pos.orchestrator.plist").exists()
    assert (agents / "com.loam.alpha.memory-graphiti.plist").exists()
    assert (agents / "com.apple.something.plist").exists()


def test_case_4_bootout_failure_partial_failure(tmp_path: Path) -> None:
    """A non-recoverable bootout failure leaves that file in place;
    other legacy plists are still processed; outcome is
    PARTIAL_FAILURE."""
    agents = tmp_path / "LaunchAgents"
    _populate(
        agents,
        legacy=(
            "com.pos-v2.alpha.memory-graphiti.plist",
            "com.pos-v2.alpha.orchestrator.plist",
        ),
    )

    recorder = _BootoutRecorder(
        fail_for={"com.pos-v2.alpha.memory-graphiti"}
    )
    result = migrate_launchd_labels(
        launch_agents_dir=agents, uid=501, bootout_fn=recorder
    )

    assert result.outcome is MigrationOutcome.PARTIAL_FAILURE
    assert not result.is_clean
    # Failed: file in place, no .bak.
    assert (agents / "com.pos-v2.alpha.memory-graphiti.plist").exists()
    assert not (
        agents
        / f"com.pos-v2.alpha.memory-graphiti{RENAMED_SUFFIX}"
    ).exists()
    # Other plist: processed cleanly.
    assert not (agents / "com.pos-v2.alpha.orchestrator.plist").exists()
    assert (
        agents / f"com.pos-v2.alpha.orchestrator{RENAMED_SUFFIX}"
    ).exists()
    # Failure recorded.
    assert len(result.failed) == 1
    assert result.failed[0].label == "com.pos-v2.alpha.memory-graphiti"
    assert result.failed[0].returncode == 1


def test_idempotent_rerun_after_migrated_hits_nothing(tmp_path: Path) -> None:
    """Re-running after a clean MIGRATED finds zero matches."""
    agents = tmp_path / "LaunchAgents"
    _populate(
        agents,
        legacy=("com.pos-v2.alpha.memory-graphiti.plist",),
    )

    recorder1 = _BootoutRecorder()
    first = migrate_launchd_labels(
        launch_agents_dir=agents, uid=501, bootout_fn=recorder1
    )
    assert first.outcome is MigrationOutcome.MIGRATED

    recorder2 = _BootoutRecorder()
    second = migrate_launchd_labels(
        launch_agents_dir=agents, uid=501, bootout_fn=recorder2
    )
    assert second.outcome is MigrationOutcome.NOTHING_TO_MIGRATE
    assert recorder2.called_with == []


def test_benign_bootout_stderr_treated_as_success(tmp_path: Path) -> None:
    """A bootout that returns non-zero with the 'service not loaded'
    stderr is treated as success (the label may have already been
    booted out by a prior run or manual cleanup)."""
    agents = tmp_path / "LaunchAgents"
    _populate(
        agents,
        legacy=("com.pos-v2.alpha.memory-graphiti.plist",),
    )

    def benign_bootout(label: str) -> BootoutResult:
        # Mirror what _bootout_via_launchctl produces when launchctl
        # returns non-zero with a benign stderr fragment.
        return BootoutResult(
            label=label,
            ok=True,  # benign stderr → ok=True per migrate._bootout_via_launchctl
            returncode=3,
            stderr="Boot-out failed: 113: Could not find specified service",
        )

    result = migrate_launchd_labels(
        launch_agents_dir=agents, uid=501, bootout_fn=benign_bootout
    )
    assert result.outcome is MigrationOutcome.MIGRATED
    assert result.is_clean
    # File renamed even though bootout returned non-zero (because the
    # benign-stderr policy treats it as success).
    assert (
        agents
        / f"com.pos-v2.alpha.memory-graphiti{RENAMED_SUFFIX}"
    ).exists()
