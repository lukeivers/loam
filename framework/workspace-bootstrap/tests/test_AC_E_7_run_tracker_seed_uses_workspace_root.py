"""AC.E.7 — `_run_tracker_seed` invokes `tracker_db_path_for` with
`workspace_root`, not `pos_root`.

Sub-plan E (two-modes-and-multi-workspace, amendment #42). The
helper inside ``first_run_scaffold`` that wires the tracker-seed
must compute the DB path from ``workspace_root`` so the seed and
amendment #40's contributor land on the same DB file.

The test injects a recording ``tracker_seed_runner`` that captures
the ``tracker_db_path`` argument the helper hands it, then asserts
the captured path is workspace-rooted (under ``workspace_root``) and
NOT pos_root-rooted.

Plan: docs/rebuild/plans/two-modes-and-multi-workspace/E-classify-workspace-replacement.md
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    run_first_run_scaffold,
)
from loam.workspace_bootstrap.adapters.tracker_seed import (
    TRACKER_DB_FILENAME,
    TrackerSeedResult,
)


class _RecordingRunner:
    """Records every kwarg dict the runner is invoked with."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __call__(self, **kwargs: Any) -> TrackerSeedResult:
        self.calls.append(kwargs)
        return TrackerSeedResult(
            seeded=False,
            reason="skipped_no_value_prop",
            classification=kwargs.get("classification", "user"),
            root_id=None,
            descendants_seeded=(),
            value_prop_source=None,
        )


def test_AC_E_7_runner_receives_workspace_rooted_db_path(tmp_path: Path) -> None:
    """The injected runner sees a ``tracker_db_path`` rooted under
    ``workspace_root``, not under ``pos_root``."""
    workspace = tmp_path / "ws-record"
    workspace.mkdir()
    pos_root = tmp_path / ".pos"
    agents = tmp_path / "LaunchAgents"

    runner = _RecordingRunner()
    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
        tracker_seed_runner=runner,
    )

    assert len(runner.calls) == 1, "tracker_seed_runner not invoked exactly once"
    db_path = Path(runner.calls[0]["tracker_db_path"])
    assert db_path.is_relative_to(workspace), (
        f"tracker_db_path is not workspace-rooted: {db_path}"
    )
    assert not db_path.is_relative_to(pos_root), (
        f"tracker_db_path is still pos_root-rooted: {db_path}"
    )


def test_AC_E_7_runner_receives_canonical_db_filename(tmp_path: Path) -> None:
    """The path's filename is ``objective_tracker.sqlite`` — the
    canonical DB filename (the constant amendment #40's contributor
    also uses)."""
    workspace = tmp_path / "ws-filename"
    workspace.mkdir()
    pos_root = tmp_path / ".pos"
    agents = tmp_path / "LaunchAgents"

    runner = _RecordingRunner()
    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
        tracker_seed_runner=runner,
    )

    db_path = Path(runner.calls[0]["tracker_db_path"])
    assert db_path.name == TRACKER_DB_FILENAME
    assert db_path == workspace / "workspace" / TRACKER_DB_FILENAME
