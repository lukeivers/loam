"""AC6 — macOS-only; other platforms refuse loudly.

When invoked on a non-Darwin platform, the tool exits non-zero and
writes a single line on stderr naming the platform and the macOS-
only constraint. No filesystem reads are performed.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from orphan_plist_cleanup.cli import main
from orphan_plist_cleanup.launchctl import BootoutResult


def _bootout_must_not_fire(label: str) -> BootoutResult:
    raise AssertionError(
        "launchctl bootout was called on a non-Darwin platform"
    )


class TestPlatformRefusal:
    @pytest.mark.parametrize("platform", ["linux", "win32", "freebsd"])
    def test_non_darwin_refused(
        self, platform: str, launch_agents_dir: Path
    ) -> None:
        # AC6: non-Darwin -> non-zero exit, stderr message.
        stdout = io.StringIO()
        stderr = io.StringIO()
        rc = main(
            ["--dry-run", "--launch-agents-dir", str(launch_agents_dir)],
            stdout=stdout,
            stderr=stderr,
            platform=platform,
            bootout_fn=_bootout_must_not_fire,
        )
        assert rc != 0
        assert rc == 2
        assert "macOS-only" in stderr.getvalue()
        assert platform in stderr.getvalue()
        # stdout must be empty — the tool did not list anything.
        assert stdout.getvalue() == ""

    def test_non_darwin_refusal_does_not_read_filesystem(
        self, launch_agents_dir: Path
    ) -> None:
        # AC6: refusal happens BEFORE any filesystem read so a
        # foreign-platform invocation cannot mask the platform-
        # mismatch signal. Verify by deleting the directory between
        # parsing and execution — refusal should still happen
        # cleanly (no FileNotFoundError, no traceback).
        # Remove the directory; tool must still refuse cleanly.
        for entry in launch_agents_dir.iterdir():
            entry.unlink()
        launch_agents_dir.rmdir()

        stderr = io.StringIO()
        rc = main(
            ["--dry-run", "--launch-agents-dir", str(launch_agents_dir)],
            stdout=io.StringIO(),
            stderr=stderr,
            platform="linux",
            bootout_fn=_bootout_must_not_fire,
        )
        assert rc == 2
        assert "macOS-only" in stderr.getvalue()

    def test_darwin_passes_platform_check(
        self, launch_agents_dir: Path
    ) -> None:
        # Sanity: the platform check accepts ``"darwin"`` and the
        # dry-run proceeds normally.
        stdout = io.StringIO()
        rc = main(
            ["--dry-run", "--launch-agents-dir", str(launch_agents_dir)],
            stdout=stdout,
            stderr=io.StringIO(),
            platform="darwin",
            bootout_fn=_bootout_must_not_fire,
        )
        assert rc == 0
        # Some orphans should have been listed.
        assert stdout.getvalue() != ""
