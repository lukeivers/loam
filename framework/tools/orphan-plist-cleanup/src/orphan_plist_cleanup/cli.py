"""Command-line entry point for ``orphan-plist-cleanup``.

Backs AC2 (dry-run lists, does not mutate), AC3 (apply mode boots
out + renames aside), AC4 (idempotent), and AC6 (macOS-only refusal).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import IO, Sequence

from orphan_plist_cleanup import __version__, detector, remediator
from orphan_plist_cleanup.launchctl import bootout as _real_bootout


def _default_launch_agents_dir() -> Path:
    return Path.home() / "Library" / "LaunchAgents"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orphan-plist-cleanup",
        description=(
            "Detect and reversibly remediate pre-amendment-#6 orphan "
            "pos-v2 launchd plists in ~/Library/LaunchAgents/."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"orphan-plist-cleanup {__version__}",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="list detected orphans without taking any action (default)",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="bootout + rename-aside each detected orphan",
    )
    # ``--launch-agents-dir`` is a test seam, not a user-facing flag
    # for routine use. AC2/AC3/AC4 tests need to point the tool at a
    # tmp_path; production callers always use the default.
    parser.add_argument(
        "--launch-agents-dir",
        type=Path,
        default=None,
        help=argparse.SUPPRESS,
    )
    return parser


def _refuse_non_darwin(stderr: IO[str], platform: str) -> int:
    """AC6 — refuse on non-Darwin platforms with a clear error."""
    stderr.write(
        f"orphan-plist-cleanup: refused — this tool is macOS-only "
        f"(running on {platform!r}).\n"
    )
    return 2


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: IO[str] | None = None,
    stderr: IO[str] | None = None,
    platform: str | None = None,
    bootout_fn=_real_bootout,
) -> int:
    """Entry point. ``stdout``, ``stderr``, ``platform`` and
    ``bootout_fn`` are injected for testing; production callers use
    the defaults.
    """
    if stdout is None:
        stdout = sys.stdout
    if stderr is None:
        stderr = sys.stderr
    if platform is None:
        platform = sys.platform

    parser = _build_parser()
    args = parser.parse_args(argv)

    # AC6 — platform refusal. Performed before any filesystem access
    # so a Linux invocation cannot accidentally read a directory.
    if platform != "darwin":
        return _refuse_non_darwin(stderr, platform)

    launch_agents_dir = args.launch_agents_dir or _default_launch_agents_dir()
    orphans = list(detector.scan(launch_agents_dir))

    # AC2 — dry-run is the default. Treat absence of ``--apply`` as
    # dry-run regardless of whether ``--dry-run`` was passed.
    if not args.apply:
        for orphan in orphans:
            stdout.write(f"{orphan.path}\n")
        return 0

    # AC3 — apply mode.
    any_failed = False
    for orphan in orphans:
        outcome = remediator.remediate_one(orphan, bootout_fn=bootout_fn)
        if outcome.ok:
            stdout.write(
                f"booted out and renamed: {outcome.orphan.path} -> "
                f"{outcome.renamed_to}\n"
            )
        else:
            any_failed = True
            stderr.write(
                f"orphan-plist-cleanup: bootout failed for "
                f"{outcome.orphan.path} (label={outcome.orphan.label}, "
                f"rc={outcome.bootout_result.returncode}); file left in "
                f"place\nstderr: {outcome.bootout_result.stderr}\n"
            )
    return 1 if any_failed else 0
