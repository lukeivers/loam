"""Migration logic — pure function over filesystem state.

Per AC.RNM-1b.3 (M1b sub-plan §4): four cases, idempotent, no merge.

  1. OLD_EXISTS_NEW_ABSENT: rename ``~/.pos/`` → ``~/.loam/``.
  2. NEW_EXISTS_OLD_ABSENT: already migrated; no-op.
  3. NEITHER: fresh machine; no-op.
  4. BOTH: conflict; halt without modification.

The helper does NOT merge, copy, or modify file contents — case 1 is
a single ``os.rename()``. Cases 2/3 read filesystem state only.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


OLD_DIRNAME = ".pos"
NEW_DIRNAME = ".loam"


class MigrationStatus(str, Enum):
    """Outcome of a migration attempt."""

    MIGRATED = "migrated"  # case 1: rename happened
    ALREADY_MIGRATED = "already_migrated"  # case 2: only new dir
    NOTHING_TO_MIGRATE = "nothing_to_migrate"  # case 3: neither dir
    CONFLICT = "conflict"  # case 4: both dirs


@dataclass(frozen=True)
class MigrationResult:
    """Result of a migration attempt.

    Attributes:
        status: which of the four cases applied.
        old_path: the resolved ``~/.pos/`` path.
        new_path: the resolved ``~/.loam/`` path.
        message: one-line human-readable summary.
    """

    status: MigrationStatus
    old_path: Path
    new_path: Path
    message: str

    @property
    def is_clean(self) -> bool:
        """True for cases 1, 2, 3 (clean exit). False for case 4 (conflict)."""
        return self.status is not MigrationStatus.CONFLICT


def migrate_host_config(home: Path | None = None) -> MigrationResult:
    """Run the migration; return a :class:`MigrationResult`.

    Args:
        home: override the home directory (testing). Defaults to ``Path.home()``.

    The four cases per AC.RNM-1b.3:

    1. ``~/.pos/`` exists, ``~/.loam/`` does not → rename. ``MIGRATED``.
    2. ``~/.pos/`` does not exist, ``~/.loam/`` exists → no-op.
       ``ALREADY_MIGRATED``.
    3. Neither exists → no-op. ``NOTHING_TO_MIGRATE``.
    4. Both exist → halt without modification. ``CONFLICT``.

    The function is idempotent: running it twice in succession after a
    case-1 run hits case 2 the second time. Running it after a case-4
    halt produces case 4 again until the user resolves the conflict
    manually.

    Filesystem effect: at most one ``os.rename()`` (case 1). No merge,
    no copy, no content modification.
    """
    home_path = home if home is not None else Path.home()
    old_path = home_path / OLD_DIRNAME
    new_path = home_path / NEW_DIRNAME

    old_exists = old_path.exists()
    new_exists = new_path.exists()

    if old_exists and not new_exists:
        # Case 1: rename.
        os.rename(old_path, new_path)
        return MigrationResult(
            status=MigrationStatus.MIGRATED,
            old_path=old_path,
            new_path=new_path,
            message=(
                f"Migrated per-host config: {old_path} → {new_path}. "
                "Re-run is safe (will report 'already migrated')."
            ),
        )

    if new_exists and not old_exists:
        # Case 2: already migrated.
        return MigrationResult(
            status=MigrationStatus.ALREADY_MIGRATED,
            old_path=old_path,
            new_path=new_path,
            message=f"Already migrated: {new_path} present, {old_path} absent.",
        )

    if not old_exists and not new_exists:
        # Case 3: nothing to migrate.
        return MigrationResult(
            status=MigrationStatus.NOTHING_TO_MIGRATE,
            old_path=old_path,
            new_path=new_path,
            message=(
                f"No per-host state present at {old_path} or {new_path}. "
                "Nothing to migrate; first-run will scaffold "
                f"{new_path} on next workspace bootstrap."
            ),
        )

    # Case 4: both exist — halt.
    return MigrationResult(
        status=MigrationStatus.CONFLICT,
        old_path=old_path,
        new_path=new_path,
        message=(
            f"CONFLICT: both {old_path} and {new_path} exist. "
            "Refusing to merge or clobber. Review the contents of each "
            "directory; back up or remove one; then re-run this helper. "
            "(This usually means a prior partial migration attempt left "
            "both dirs in place.)"
        ),
    )
