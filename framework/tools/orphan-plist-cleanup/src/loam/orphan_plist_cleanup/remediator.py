"""Apply-mode remediation: bootout + rename-aside.

Backs AC3 (apply mode boots out and renames aside) and AC4
(idempotent on re-run — the rename-aside step is what makes the
second invocation a no-op).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from loam.orphan_plist_cleanup.detector import DetectedOrphan
from loam.orphan_plist_cleanup.launchctl import BootoutResult, bootout as _real_bootout


# Suffix appended to the renamed plist. The original ``.plist``
# extension is replaced wholesale (not appended-after) so the file
# no longer matches the orphan detection pattern in subsequent runs.
RENAME_SUFFIX = ".orphan-disabled.bak"


# Type for an injectable bootout callable — production passes the
# real one; tests pass a fake.
BootoutFn = Callable[[str], BootoutResult]


@dataclass(frozen=True)
class RemediationOutcome:
    """Result of remediating one orphan.

    ``ok`` is True when the bootout succeeded (or the service was
    already not loaded) AND the file was renamed-aside. ``ok`` is
    False when bootout failed; in that case the file is left in
    place and ``renamed_to`` is None.
    """

    orphan: DetectedOrphan
    bootout_result: BootoutResult
    renamed_to: Path | None
    ok: bool


def _rename_target(path: Path) -> Path:
    """Compute the rename-aside target path for an orphan plist.

    The original ``.plist`` extension is replaced wholesale by
    ``.orphan-disabled.bak`` — the resulting filename no longer
    matches the orphan detection pattern (which requires a trailing
    ``.plist``).
    """
    # ``with_suffix`` on a Path replaces the final suffix only; since
    # the orphan filename always ends in ``.plist`` (verified at
    # detection time), this swaps ``.plist`` -> ``.orphan-disabled.bak``.
    return path.with_suffix(RENAME_SUFFIX)


def remediate_one(
    orphan: DetectedOrphan,
    *,
    bootout_fn: BootoutFn = _real_bootout,
) -> RemediationOutcome:
    """Bootout + rename-aside one orphan.

    ``bootout_fn`` is injected for testing. Production callers use
    the default (which calls the real launchctl).
    """
    result = bootout_fn(orphan.label)
    if not result.ok:
        return RemediationOutcome(
            orphan=orphan,
            bootout_result=result,
            renamed_to=None,
            ok=False,
        )
    target = _rename_target(orphan.path)
    orphan.path.rename(target)
    return RemediationOutcome(
        orphan=orphan,
        bootout_result=result,
        renamed_to=target,
        ok=True,
    )
