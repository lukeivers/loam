"""AC4 — idempotent on re-run.

After ``--apply`` succeeds, a second ``--apply`` (or ``--dry-run``)
detects no orphans and takes no action. Running twice produces no
errors and no double-action.
"""

from __future__ import annotations

import io
from pathlib import Path

from orphan_plist_cleanup.cli import main
from orphan_plist_cleanup.launchctl import BootoutResult


def _ok_bootout(label: str) -> BootoutResult:
    return BootoutResult(ok=True, returncode=0, stderr="")


def _bootout_must_not_fire(label: str) -> BootoutResult:
    raise AssertionError(
        f"launchctl bootout was called for {label!r} on the second "
        f"apply — orphans should already be remediated"
    )


class TestIdempotent:
    def test_second_apply_detects_no_orphans_and_does_nothing(
        self, launch_agents_dir: Path
    ) -> None:
        # AC4: first apply remediates; second apply finds nothing.
        rc1 = main(
            ["--apply", "--launch-agents-dir", str(launch_agents_dir)],
            stdout=io.StringIO(),
            stderr=io.StringIO(),
            platform="darwin",
            bootout_fn=_ok_bootout,
        )
        assert rc1 == 0

        # Snapshot disk state after first apply.
        files_after_first = sorted(p.name for p in launch_agents_dir.iterdir())

        # Second apply: bootout MUST NOT be invoked (the recorder
        # raises if it is). Exit 0. Disk state unchanged.
        stdout2 = io.StringIO()
        rc2 = main(
            ["--apply", "--launch-agents-dir", str(launch_agents_dir)],
            stdout=stdout2,
            stderr=io.StringIO(),
            platform="darwin",
            bootout_fn=_bootout_must_not_fire,
        )
        assert rc2 == 0
        assert stdout2.getvalue() == ""

        files_after_second = sorted(
            p.name for p in launch_agents_dir.iterdir()
        )
        assert files_after_first == files_after_second

    def test_dry_run_after_apply_lists_no_orphans(
        self, launch_agents_dir: Path
    ) -> None:
        # AC4 (dry-run side): after apply, dry-run finds nothing.
        rc1 = main(
            ["--apply", "--launch-agents-dir", str(launch_agents_dir)],
            stdout=io.StringIO(),
            stderr=io.StringIO(),
            platform="darwin",
            bootout_fn=_ok_bootout,
        )
        assert rc1 == 0

        stdout = io.StringIO()
        rc2 = main(
            ["--dry-run", "--launch-agents-dir", str(launch_agents_dir)],
            stdout=stdout,
            stderr=io.StringIO(),
            platform="darwin",
            bootout_fn=_bootout_must_not_fire,
        )
        assert rc2 == 0
        assert stdout.getvalue() == ""
