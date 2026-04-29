"""Migration logic — bootout + rename-aside for pre-M1c launchd labels.

Per AC.RNM-1c.3 of the M1c sub-plan: for each plist filename in
``~/Library/LaunchAgents/`` matching the pre-M1c live shape
``com.pos-v2.<slug>.<kind>.plist`` (4-segment), the helper:

  1. Issues ``launchctl bootout gui/<uid>/<label>``. Stderr fragments
     matching the "service not loaded" variant are treated as benign
     (the label may not be loaded if the user already restarted or
     manually booted out). Mirrors amendment #6's
     ``ServiceManagerRunner.bootstrap`` benign-stderr policy + the
     orphan-plist-cleanup tool's apply-mode policy.
  2. Renames the plist file from ``<base>.plist`` to
     ``<base>.label-rebrand-disabled.bak`` (extension replaced
     wholesale). The plist file is never deleted; recovery is
     ``mv <base>.label-rebrand-disabled.bak <base>.plist`` followed
     by re-running workspace first-run.

Out of scope:
  - pre-#6 single-segment shapes (``com.pos-v2.<single>.plist``,
    ``com.pos.<single>.plist``) — those are the orphan-plist-cleanup
    tool's mission. The two helpers are orthogonal.
  - writing new ``com.loam.<slug>.<kind>.plist`` files —
    workspace-bootstrap's first-run scaffold owns that path.

Idempotent: re-running the helper after success finds zero matches
(the renamed files no longer carry the ``.plist`` suffix that the
filename pattern matches against).
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable


# Filename suffix the renamed (booted-out) plist files receive.
RENAMED_SUFFIX = ".label-rebrand-disabled.bak"


# Stderr fragments launchctl emits when the target label is not
# currently loaded — treated as benign per amendment #6's policy.
_BENIGN_BOOTOUT_STDERR_FRAGMENTS: tuple[str, ...] = (
    "Could not find specified service",
    "No such process",
    "Boot-out failed: 5: Input/output error",
    "not loaded",
)


class MigrationOutcome(str, Enum):
    """Top-level result of a helper invocation."""

    NOTHING_TO_MIGRATE = "nothing_to_migrate"
    """No matching legacy plists found (clean machine or already
    migrated)."""

    MIGRATED = "migrated"
    """One or more legacy plists were processed cleanly."""

    PARTIAL_FAILURE = "partial_failure"
    """At least one legacy plist's bootout failed non-recoverably; the
    affected file was left in place. Other plists may have been
    processed cleanly."""


@dataclass(frozen=True)
class BootoutResult:
    """Result of a single ``launchctl bootout`` invocation."""

    label: str
    ok: bool
    returncode: int
    stderr: str


@dataclass(frozen=True)
class MigrationResult:
    """Aggregate result of a helper invocation."""

    outcome: MigrationOutcome
    processed: tuple[Path, ...] = field(default_factory=tuple)
    """Plist files that were booted out + renamed-aside cleanly."""

    failed: tuple[BootoutResult, ...] = field(default_factory=tuple)
    """Bootout failures (non-benign stderr) — files left in place."""

    @property
    def is_clean(self) -> bool:
        """True if outcome is NOTHING_TO_MIGRATE or MIGRATED."""
        return self.outcome is not MigrationOutcome.PARTIAL_FAILURE


def _is_legacy_namespaced_plist(name: str) -> bool:
    """Return True if ``name`` matches the pre-M1c live shape
    ``com.pos-v2.<slug>.<kind>.plist`` (4-segment).

    Pre-#6 single-segment shapes (``com.pos-v2.<single>.plist``,
    ``com.pos.<single>.plist``) are the orphan-plist-cleanup tool's
    mission — this predicate explicitly rejects them.
    """
    if not name.endswith(".plist"):
        return False
    label = name[: -len(".plist")]
    segments = label.split(".")
    # ``com.pos-v2.<slug>.<kind>`` -> 4 segments.
    return (
        len(segments) == 4
        and segments[0] == "com"
        and segments[1] == "pos-v2"
    )


def _bootout_via_launchctl(
    label: str,
    *,
    uid: int,
    launchctl_bin: str = "launchctl",
) -> BootoutResult:
    """Default bootout implementation — invokes the real launchctl.

    Tests pass a fake bootout_fn through ``migrate_launchd_labels``;
    this default is used in production.
    """
    proc = subprocess.run(
        [launchctl_bin, "bootout", f"gui/{uid}/{label}"],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    stderr = proc.stderr or ""
    if proc.returncode == 0:
        return BootoutResult(label=label, ok=True, returncode=0, stderr=stderr)
    benign = any(frag in stderr for frag in _BENIGN_BOOTOUT_STDERR_FRAGMENTS)
    return BootoutResult(
        label=label,
        ok=benign,
        returncode=proc.returncode,
        stderr=stderr,
    )


def migrate_launchd_labels(
    *,
    launch_agents_dir: Path | None = None,
    uid: int | None = None,
    bootout_fn: Callable[[str], BootoutResult] | None = None,
) -> MigrationResult:
    """Run the migration; return a :class:`MigrationResult`.

    Args:
        launch_agents_dir: override the LaunchAgents directory
            (testing). Defaults to ``~/Library/LaunchAgents/``.
        uid: override the user id passed to ``launchctl bootout``
            (testing). Defaults to ``os.getuid()``.
        bootout_fn: override the bootout implementation (testing).
            Defaults to a real-launchctl invoker.

    Behaviour per AC.RNM-1c.3:

      - If the directory does not exist, return NOTHING_TO_MIGRATE.
      - For each filename matching the pre-M1c 4-segment shape
        ``com.pos-v2.<slug>.<kind>.plist``: bootout (benign-stderr-as-
        success), then rename to ``<base>.label-rebrand-disabled.bak``.
      - On any non-recoverable bootout failure: leave that file in
        place (no rename), record the failure; continue processing
        remaining plists.
      - Outcome:
          NOTHING_TO_MIGRATE if zero matching plists found.
          MIGRATED if all matches processed cleanly.
          PARTIAL_FAILURE if at least one match's bootout failed.

    Idempotent: running twice in succession after a clean MIGRATED
    run finds zero matches (the renamed files no longer carry the
    ``.plist`` extension the filter matches).
    """
    agents_dir = (
        launch_agents_dir
        if launch_agents_dir is not None
        else Path.home() / "Library" / "LaunchAgents"
    )
    actual_uid = uid if uid is not None else os.getuid()
    bootout = bootout_fn if bootout_fn is not None else (
        lambda label: _bootout_via_launchctl(label, uid=actual_uid)
    )

    if not agents_dir.is_dir():
        return MigrationResult(outcome=MigrationOutcome.NOTHING_TO_MIGRATE)

    processed: list[Path] = []
    failed: list[BootoutResult] = []
    for entry in sorted(agents_dir.iterdir()):
        if not entry.is_file():
            continue
        if not _is_legacy_namespaced_plist(entry.name):
            continue
        label = entry.name[: -len(".plist")]
        result = bootout(label)
        if not result.ok:
            failed.append(result)
            continue
        # Rename the plist aside.
        renamed = entry.with_name(label + RENAMED_SUFFIX)
        entry.rename(renamed)
        processed.append(renamed)

    if processed and not failed:
        outcome = MigrationOutcome.MIGRATED
    elif not processed and not failed:
        outcome = MigrationOutcome.NOTHING_TO_MIGRATE
    else:
        outcome = MigrationOutcome.PARTIAL_FAILURE

    return MigrationResult(
        outcome=outcome,
        processed=tuple(processed),
        failed=tuple(failed),
    )
