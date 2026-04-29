"""AC2 — dry-run lists, does not mutate.

Dry-run prints detected orphans (one per line), exits 0, performs no
``launchctl bootout``, renames no files, deletes no files. Running
dry-run twice produces identical output (idempotent on the read side).
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from orphan_plist_cleanup.cli import main
from orphan_plist_cleanup.launchctl import BootoutResult


def _fake_bootout_unreachable(label: str) -> BootoutResult:
    # AC2 forbids any launchctl invocation in dry-run. If this
    # function fires, the test fails immediately.
    raise AssertionError(
        f"launchctl bootout was called for {label!r} during dry-run"
    )


class TestDryRun:
    def test_dry_run_lists_orphans_on_stdout(
        self, launch_agents_dir: Path
    ) -> None:
        # AC2: detected orphans listed, one per line, with absolute
        # paths.
        stdout = io.StringIO()
        stderr = io.StringIO()
        rc = main(
            ["--dry-run", "--launch-agents-dir", str(launch_agents_dir)],
            stdout=stdout,
            stderr=stderr,
            platform="darwin",
            bootout_fn=_fake_bootout_unreachable,
        )
        assert rc == 0
        listed = {line for line in stdout.getvalue().splitlines() if line}

        expected_orphans = {
            str(launch_agents_dir / "com.pos-v2.memory-graphiti.plist"),
            str(launch_agents_dir / "com.pos-v2.orchestrator.plist"),
            str(launch_agents_dir / "com.pos.orchestrator.plist"),
        }
        assert listed == expected_orphans

        # Namespaced + unrelated plists must NOT appear in the
        # listing (AC5 + AC1 negative half).
        assert (
            str(launch_agents_dir / "com.loam.alpha.orchestrator.plist")
            not in listed
        )
        assert (
            str(launch_agents_dir / "com.apple.something.plist")
            not in listed
        )

    def test_dry_run_default_when_no_flag(self, launch_agents_dir: Path) -> None:
        # AC2: dry-run is the default — no flag at all behaves like
        # ``--dry-run``.
        stdout = io.StringIO()
        rc = main(
            ["--launch-agents-dir", str(launch_agents_dir)],
            stdout=stdout,
            stderr=io.StringIO(),
            platform="darwin",
            bootout_fn=_fake_bootout_unreachable,
        )
        assert rc == 0
        assert "com.pos-v2.memory-graphiti.plist" in stdout.getvalue()

    def test_dry_run_does_not_mutate_disk(
        self, launch_agents_dir: Path
    ) -> None:
        # AC2: no rename, no delete. Snapshot before and after must
        # be byte-identical for every file.
        before = {
            p.name: p.read_text() for p in launch_agents_dir.iterdir()
        }
        main(
            ["--dry-run", "--launch-agents-dir", str(launch_agents_dir)],
            stdout=io.StringIO(),
            stderr=io.StringIO(),
            platform="darwin",
            bootout_fn=_fake_bootout_unreachable,
        )
        after = {p.name: p.read_text() for p in launch_agents_dir.iterdir()}
        assert before == after

    def test_dry_run_twice_identical_output(
        self, launch_agents_dir: Path
    ) -> None:
        # AC2: second dry-run produces the same output (read-side
        # idempotency).
        out1 = io.StringIO()
        out2 = io.StringIO()
        for out in (out1, out2):
            rc = main(
                ["--dry-run", "--launch-agents-dir", str(launch_agents_dir)],
                stdout=out,
                stderr=io.StringIO(),
                platform="darwin",
                bootout_fn=_fake_bootout_unreachable,
            )
            assert rc == 0
        assert out1.getvalue() == out2.getvalue()

    def test_dry_run_on_empty_dir_exits_zero_with_no_output(
        self, empty_launch_agents_dir: Path
    ) -> None:
        # AC2: zero orphans -> zero output, exit 0.
        stdout = io.StringIO()
        rc = main(
            [
                "--dry-run",
                "--launch-agents-dir",
                str(empty_launch_agents_dir),
            ],
            stdout=stdout,
            stderr=io.StringIO(),
            platform="darwin",
            bootout_fn=_fake_bootout_unreachable,
        )
        assert rc == 0
        assert stdout.getvalue() == ""
