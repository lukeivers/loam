"""CLI entry point for the launchd-label migration helper.

Console script ``loam-migrate-launchd-labels`` is registered in
``pyproject.toml``. Also runnable as
``python -m loam_migrate_launchd_labels``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import IO

from .migrate import (
    BootoutResult,
    MigrationOutcome,
    MigrationResult,
    migrate_launchd_labels,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="loam-migrate-launchd-labels",
        description=(
            "One-shot per-host migration: bootout pre-M1c "
            "com.pos-v2.<slug>.<kind> launchd labels and rename the "
            "plist files aside (.label-rebrand-disabled.bak). "
            "Idempotent (re-run is safe). Sibling helper to "
            "loam-migrate-host-config."
        ),
    )
    parser.add_argument(
        "--launch-agents-dir",
        default=None,
        help=(
            "Override the LaunchAgents directory the helper scans. "
            "Default: ~/Library/LaunchAgents/. "
            "Test/override hook only."
        ),
    )
    return parser


def _format_result(result: MigrationResult) -> str:
    """One-paragraph human-readable summary of a MigrationResult."""
    lines: list[str] = []
    if result.outcome is MigrationOutcome.NOTHING_TO_MIGRATE:
        lines.append(
            "No legacy com.pos-v2.<slug>.<kind>.plist files detected; "
            "nothing to migrate. Re-run is safe."
        )
    elif result.outcome is MigrationOutcome.MIGRATED:
        lines.append(
            f"Migrated {len(result.processed)} legacy launchd plist(s) "
            "(bootout + rename to .label-rebrand-disabled.bak):"
        )
        for path in result.processed:
            lines.append(f"  {path}")
        lines.append(
            "Recovery (if needed): rename a .label-rebrand-disabled.bak "
            "back to .plist and re-run workspace first-run."
        )
    else:  # PARTIAL_FAILURE
        if result.processed:
            lines.append(
                f"Processed {len(result.processed)} legacy plist(s) cleanly:"
            )
            for path in result.processed:
                lines.append(f"  {path}")
        lines.append(
            f"FAILED to bootout {len(result.failed)} legacy plist(s); "
            "files left in place:"
        )
        for fail in result.failed:
            lines.append(
                f"  {fail.label}: returncode={fail.returncode} "
                f"stderr={fail.stderr.strip()[-200:]!r}"
            )
    return "\n".join(lines)


def main(
    argv: list[str] | None = None,
    *,
    stdout: IO[str] | None = None,
    stderr: IO[str] | None = None,
    bootout_fn: object | None = None,
) -> int:
    """Entry point. Returns the process exit code.

    - 0 on NOTHING_TO_MIGRATE or MIGRATED (clean exits).
    - 1 on PARTIAL_FAILURE (at least one non-recoverable bootout).
    """
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr

    parser = _build_parser()
    args = parser.parse_args(argv)

    launch_agents_dir = (
        Path(args.launch_agents_dir)
        if args.launch_agents_dir is not None
        else None
    )

    # bootout_fn is for tests only — real CLI uses the launchctl
    # default in migrate.py.
    result = migrate_launchd_labels(
        launch_agents_dir=launch_agents_dir,
        bootout_fn=bootout_fn,  # type: ignore[arg-type]
    )

    summary = _format_result(result)
    if result.outcome is MigrationOutcome.PARTIAL_FAILURE:
        # Failure detail to stderr; processed-files summary to stdout.
        # Split heuristically: stderr gets lines starting with FAILED.
        for line in summary.splitlines():
            if line.startswith("FAILED") or line.startswith("  "):
                err.write(line + "\n")
            else:
                out.write(line + "\n")
        return 1

    out.write(summary + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
