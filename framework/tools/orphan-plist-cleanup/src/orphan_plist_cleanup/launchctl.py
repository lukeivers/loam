"""Thin wrapper over ``launchctl bootout``.

Backs the launchctl side of AC3 (apply mode). Tests mock this
module's ``bootout`` function rather than the subprocess primitive.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass


# Stderr substrings launchd produces when the label is not currently
# loaded. Treated as success — consistent with amendment #6's
# ServiceManagerRunner.bootstrap policy.
_NOT_LOADED_VARIANTS = (
    "Could not find specified service",
    "Boot-out failed: 5: Input/output error",  # legacy variant
    "No such process",
    "Operation now in progress",  # macOS 14+ variant when the label
                                  # is queued for unload but not loaded
)


@dataclass(frozen=True)
class BootoutResult:
    """Outcome of a single ``launchctl bootout`` call.

    ``ok`` is True when the service was either successfully booted
    out OR was not loaded to begin with (idempotent). ``ok`` is
    False on any other launchctl failure.
    """

    ok: bool
    returncode: int
    stderr: str


def _is_not_loaded_stderr(stderr: str) -> bool:
    return any(variant in stderr for variant in _NOT_LOADED_VARIANTS)


def bootout(label: str, *, uid: int | None = None) -> BootoutResult:
    """Invoke ``launchctl bootout gui/<uid>/<label>`` and classify
    the result.

    ``uid`` defaults to the current effective UID. Tests inject a
    sentinel uid; production uses ``os.geteuid()``.
    """
    if uid is None:
        uid = os.geteuid()
    target = f"gui/{uid}/{label}"
    completed = subprocess.run(
        ["launchctl", "bootout", target],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode == 0:
        return BootoutResult(ok=True, returncode=0, stderr=completed.stderr)
    if _is_not_loaded_stderr(completed.stderr):
        return BootoutResult(
            ok=True, returncode=completed.returncode, stderr=completed.stderr
        )
    return BootoutResult(
        ok=False, returncode=completed.returncode, stderr=completed.stderr
    )
