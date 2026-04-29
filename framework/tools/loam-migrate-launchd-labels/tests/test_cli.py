"""CLI exit-code + stdout-format tests for the launchd-label helper.

Cases NOTHING_TO_MIGRATE + MIGRATED → exit 0. Case PARTIAL_FAILURE
→ exit 1.
"""

from __future__ import annotations

import io
from pathlib import Path

from loam_migrate_launchd_labels.cli import main
from loam_migrate_launchd_labels.migrate import (
    BootoutResult,
    RENAMED_SUFFIX,
)


class _Recorder:
    def __init__(
        self,
        *,
        fail_for: set[str] | None = None,
    ) -> None:
        self.fail_for = fail_for or set()
        self.called_with: list[str] = []

    def __call__(self, label: str) -> BootoutResult:
        self.called_with.append(label)
        if label in self.fail_for:
            return BootoutResult(
                label=label, ok=False, returncode=1, stderr="Permission denied"
            )
        return BootoutResult(label=label, ok=True, returncode=0, stderr="")


def test_cli_nothing_to_migrate_returns_zero(tmp_path: Path) -> None:
    """Empty LaunchAgents dir → exit 0 + 'nothing to migrate' stdout."""
    agents = tmp_path / "LaunchAgents"
    agents.mkdir()
    stdout = io.StringIO()
    rc = main(
        ["--launch-agents-dir", str(agents)],
        stdout=stdout,
        stderr=io.StringIO(),
        bootout_fn=_Recorder(),
    )
    assert rc == 0
    assert "nothing to migrate" in stdout.getvalue().lower()


def test_cli_migrated_returns_zero(tmp_path: Path) -> None:
    """Legacy plists processed cleanly → exit 0 + 'Migrated N' stdout."""
    agents = tmp_path / "LaunchAgents"
    agents.mkdir()
    (agents / "com.pos-v2.alpha.memory-graphiti.plist").write_text("<plist/>")
    stdout = io.StringIO()
    rc = main(
        ["--launch-agents-dir", str(agents)],
        stdout=stdout,
        stderr=io.StringIO(),
        bootout_fn=_Recorder(),
    )
    assert rc == 0
    assert "Migrated 1 legacy" in stdout.getvalue()
    # Renamed file referenced in stdout.
    assert (
        f"com.pos-v2.alpha.memory-graphiti{RENAMED_SUFFIX}"
        in stdout.getvalue()
    )


def test_cli_partial_failure_returns_one(tmp_path: Path) -> None:
    """A bootout failure on at least one plist → exit 1."""
    agents = tmp_path / "LaunchAgents"
    agents.mkdir()
    (agents / "com.pos-v2.alpha.memory-graphiti.plist").write_text("<plist/>")
    stdout = io.StringIO()
    stderr = io.StringIO()
    rc = main(
        ["--launch-agents-dir", str(agents)],
        stdout=stdout,
        stderr=stderr,
        bootout_fn=_Recorder(fail_for={"com.pos-v2.alpha.memory-graphiti"}),
    )
    assert rc == 1
    # Failure detail surfaces on stderr.
    assert "FAILED" in stderr.getvalue()
    assert "com.pos-v2.alpha.memory-graphiti" in stderr.getvalue()
