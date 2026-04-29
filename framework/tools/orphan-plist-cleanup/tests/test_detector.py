"""AC1 + AC5 — orphan detection by label-pattern, with positive guard
on workspace-slug-namespaced plists.

AC1: detector returns the pre-#6 single-segment shapes
(``com.pos-v2.<single>.plist``, ``com.pos.<single>.plist``) as
orphans, and does not return unrelated plists.

AC5: detector NEVER returns ``com.loam.<slug>.<kind>.plist``
(workspace-slug-namespaced post-M1c live shape) — those belong to live
workspaces.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.orphan_plist_cleanup.detector import (
    Classification,
    DetectedOrphan,
    classify_filename,
    is_orphan,
    scan,
)


class TestClassifyFilename:
    """Pure-function classification — covers AC1 + AC5."""

    @pytest.mark.parametrize(
        "name",
        [
            "com.pos-v2.memory-graphiti.plist",
            "com.pos-v2.orchestrator.plist",
            "com.pos-v2.kuzu.plist",
            "com.pos-v2.x.plist",  # minimal single segment
        ],
    )
    def test_orphan_v2_shape_classified_as_orphan(self, name: str) -> None:
        # AC1: pre-#6 pos-v2 single-segment is orphan_v2.
        assert classify_filename(name) is Classification.ORPHAN_V2

    @pytest.mark.parametrize(
        "name",
        [
            "com.pos.orchestrator.plist",
            "com.pos.something.plist",
        ],
    )
    def test_orphan_v1_shape_classified_as_orphan(self, name: str) -> None:
        # AC1: v1 single-segment under com.pos is also orphan.
        assert classify_filename(name) is Classification.ORPHAN_V1

    @pytest.mark.parametrize(
        "name",
        [
            "com.loam.alpha.memory-graphiti.plist",
            "com.loam.alpha.orchestrator.plist",
            "com.loam.fixture-x.memory-graphiti.plist",
            "com.loam.foo.bar.plist",
        ],
    )
    def test_namespaced_shape_is_not_orphan(self, name: str) -> None:
        # AC5: positive guard — workspace-slug-namespaced must classify
        # as NAMESPACED and ``is_orphan`` must return False. Post-M1c
        # the live shape is `com.loam.<slug>.<kind>`; the version suffix
        # was dropped concurrently with the brand rename.
        cls = classify_filename(name)
        assert cls is Classification.NAMESPACED
        assert is_orphan(cls) is False

    @pytest.mark.parametrize(
        "name",
        [
            "com.apple.something.plist",
            "com.example.user.daemon.plist",
            "homebrew.mxcl.something.plist",
            "README.txt",  # not even a plist
            "com.loam.plist",  # zero segments after prefix — too short
            "com.pos-v2.plist",  # zero segments after prefix — pre-M1c form
            "com.pos.plist",  # zero segments after prefix — v1 form
        ],
    )
    def test_unrelated_files_are_not_loam(self, name: str) -> None:
        # AC1's negative half: unrelated plists must not be flagged.
        cls = classify_filename(name)
        assert cls is Classification.NOT_LOAM
        assert is_orphan(cls) is False

    def test_overlong_loam_shape_is_not_orphan(self) -> None:
        # Defence-in-depth: a 5-segment ``com.loam.a.b.c.plist`` is
        # not a shape loam ever wrote and we leave it alone rather
        # than guess at intent.
        assert (
            classify_filename("com.loam.a.b.c.plist")
            is Classification.NOT_LOAM
        )


class TestScan:
    """Filesystem scan — covers AC1 (yields orphans, ignores
    namespaced + unrelated) on a populated tmp directory."""

    def test_scan_yields_only_orphans(self, launch_agents_dir: Path) -> None:
        # AC1 + AC5 together: scan returns ORPHAN_V2 + ORPHAN_V1
        # entries only. Namespaced and unrelated plists must not appear.
        results = list(scan(launch_agents_dir))
        names = {r.path.name for r in results}

        # Orphans must be present (AC1).
        assert "com.pos-v2.memory-graphiti.plist" in names
        assert "com.pos-v2.orchestrator.plist" in names
        assert "com.pos.orchestrator.plist" in names

        # Namespaced must NOT be present (AC5 — positive guard;
        # post-M1c the live shape is `com.loam.<slug>.<kind>`).
        assert "com.loam.alpha.memory-graphiti.plist" not in names
        assert "com.loam.alpha.orchestrator.plist" not in names

        # Unrelated must NOT be present (AC1 — negative half).
        assert "com.apple.something.plist" not in names
        assert "com.example.user.daemon.plist" not in names
        assert "README.txt" not in names

    def test_scan_yields_correct_label(self, launch_agents_dir: Path) -> None:
        # Each DetectedOrphan carries the launchd label (filename
        # minus ``.plist``) — used by remediator to bootout.
        results = {r.path.name: r for r in scan(launch_agents_dir)}
        memory_graphiti = results["com.pos-v2.memory-graphiti.plist"]
        assert memory_graphiti.label == "com.pos-v2.memory-graphiti"
        assert memory_graphiti.classification is Classification.ORPHAN_V2

        v1_orchestrator = results["com.pos.orchestrator.plist"]
        assert v1_orchestrator.label == "com.pos.orchestrator"
        assert v1_orchestrator.classification is Classification.ORPHAN_V1

    def test_scan_on_missing_directory_returns_no_orphans(
        self, tmp_path: Path
    ) -> None:
        # If LaunchAgents/ does not exist (pristine host that never
        # ran any launchd agent), scan must yield nothing — never
        # raise.
        missing = tmp_path / "does-not-exist"
        assert list(scan(missing)) == []

    def test_scan_on_empty_directory_returns_no_orphans(
        self, empty_launch_agents_dir: Path
    ) -> None:
        assert list(scan(empty_launch_agents_dir)) == []

    def test_detected_orphan_paths_are_absolute(
        self, launch_agents_dir: Path
    ) -> None:
        # Apply mode renames at the absolute path; downstream code
        # should not need to reconstruct it.
        for orphan in scan(launch_agents_dir):
            assert isinstance(orphan, DetectedOrphan)
            assert orphan.path.is_absolute()
            assert orphan.path.exists()
