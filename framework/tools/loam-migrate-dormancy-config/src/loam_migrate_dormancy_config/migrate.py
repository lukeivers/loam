"""Migration logic — pure function over filesystem state.

Per AC.RNM-1f.5 (M1f sub-plan §4): per-file four-case logic, idempotent,
no merge.

For each of the two file pairs (sqlite + yaml) independently:

  1. OLD_EXISTS_NEW_ABSENT: rename ``OLD`` → ``NEW``. For the SQLite
     case, also rename WAL + SHM siblings if present.
  2. NEW_EXISTS_OLD_ABSENT: already migrated; no-op.
  3. NEITHER: fresh machine; no-op.
  4. BOTH: conflict; halt without modification (this pair only).

The helper does NOT merge, copy, or modify file contents — case 1
performs ``os.rename()`` calls only. Cases 2/3 read filesystem state.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


LOAM_DIRNAME = ".loam"

OLD_SQLITE_FILENAME = "degradation.sqlite"
NEW_SQLITE_FILENAME = "dormancy.sqlite"

OLD_YAML_FILENAME = "degradation-config.yaml"
NEW_YAML_FILENAME = "dormancy-config.yaml"

SQLITE_SIBLING_SUFFIXES = ("-wal", "-shm")


class FilePairStatus(str, Enum):
    """Outcome of a single file-pair migration attempt."""

    MIGRATED = "migrated"  # case 1: rename happened
    ALREADY_MIGRATED = "already_migrated"  # case 2: only new file
    NOTHING_TO_MIGRATE = "nothing_to_migrate"  # case 3: neither file
    CONFLICT = "conflict"  # case 4: both files


@dataclass(frozen=True)
class FilePairResult:
    """Result of a single file-pair migration attempt."""

    status: FilePairStatus
    old_path: Path
    new_path: Path
    message: str
    siblings_renamed: tuple[Path, ...] = field(default_factory=tuple)

    @property
    def is_clean(self) -> bool:
        """True for cases 1, 2, 3 (clean exit). False for case 4 (conflict)."""
        return self.status is not FilePairStatus.CONFLICT


@dataclass(frozen=True)
class MigrationResult:
    """Combined result across both file pairs."""

    sqlite: FilePairResult
    yaml: FilePairResult

    @property
    def is_clean(self) -> bool:
        """True iff both file-pair results are clean (no CONFLICT)."""
        return self.sqlite.is_clean and self.yaml.is_clean

    @property
    def combined_message(self) -> str:
        """One-line-per-pair human-readable summary."""
        return (
            f"sqlite: {self.sqlite.message}\n"
            f"yaml:   {self.yaml.message}"
        )


def _migrate_one_pair(
    old_path: Path,
    new_path: Path,
    handle_sqlite_siblings: bool = False,
) -> FilePairResult:
    """Run the four-case logic for a single file pair.

    If ``handle_sqlite_siblings`` is True, also rename ``*-wal`` and
    ``*-shm`` sibling files when present (missing siblings tolerated).
    """
    old_exists = old_path.exists()
    new_exists = new_path.exists()

    if old_exists and not new_exists:
        # Case 1: rename.
        os.rename(old_path, new_path)
        siblings_renamed: list[Path] = []
        if handle_sqlite_siblings:
            for suffix in SQLITE_SIBLING_SUFFIXES:
                sibling_old = old_path.with_name(old_path.name + suffix)
                sibling_new = new_path.with_name(new_path.name + suffix)
                if sibling_old.exists():
                    os.rename(sibling_old, sibling_new)
                    siblings_renamed.append(sibling_new)
        sibling_note = ""
        if siblings_renamed:
            names = ", ".join(s.name for s in siblings_renamed)
            sibling_note = f" Renamed siblings: {names}."
        return FilePairResult(
            status=FilePairStatus.MIGRATED,
            old_path=old_path,
            new_path=new_path,
            message=(
                f"Migrated: {old_path} → {new_path}.{sibling_note} "
                "Re-run is safe (will report 'already migrated')."
            ),
            siblings_renamed=tuple(siblings_renamed),
        )

    if new_exists and not old_exists:
        # Case 2: already migrated.
        return FilePairResult(
            status=FilePairStatus.ALREADY_MIGRATED,
            old_path=old_path,
            new_path=new_path,
            message=f"Already migrated: {new_path} present, {old_path} absent.",
        )

    if not old_exists and not new_exists:
        # Case 3: nothing to migrate.
        return FilePairResult(
            status=FilePairStatus.NOTHING_TO_MIGRATE,
            old_path=old_path,
            new_path=new_path,
            message=(
                f"No file present at {old_path} or {new_path}. "
                "Nothing to migrate; first-run / dormancy will scaffold "
                f"{new_path} on next workspace bootstrap."
            ),
        )

    # Case 4: both exist — halt.
    return FilePairResult(
        status=FilePairStatus.CONFLICT,
        old_path=old_path,
        new_path=new_path,
        message=(
            f"CONFLICT: both {old_path} and {new_path} exist. "
            "Refusing to merge or clobber. Review the contents of each "
            "file; back up or remove one; then re-run this helper. "
            "(This usually means a prior partial migration attempt left "
            "both files in place.)"
        ),
    )


def migrate_dormancy_config(home: Path | None = None) -> MigrationResult:
    """Run the dormancy config-file migration; return :class:`MigrationResult`.

    Args:
        home: override the home directory (testing). Defaults to
            ``Path.home()``.

    Per-file four-case logic (sqlite + yaml independently):

    1. ``OLD_EXISTS_NEW_ABSENT`` → rename. ``MIGRATED``. SQLite case
       also renames WAL/SHM siblings if present.
    2. ``NEW_EXISTS_OLD_ABSENT`` → no-op. ``ALREADY_MIGRATED``.
    3. Neither exists → no-op. ``NOTHING_TO_MIGRATE``.
    4. Both exist → halt without modification. ``CONFLICT``.

    The function is idempotent: running it twice in succession after
    a case-1 run hits case 2 the second time. Running it after a
    case-4 halt produces case 4 again on that pair until the user
    resolves the conflict manually.

    Filesystem effect: at most three ``os.rename()`` calls per pair
    (case 1; one for the main file, two for SQLite WAL/SHM siblings).
    No merge, no copy, no content modification.
    """
    home_path = home if home is not None else Path.home()
    loam_dir = home_path / LOAM_DIRNAME

    sqlite_result = _migrate_one_pair(
        old_path=loam_dir / OLD_SQLITE_FILENAME,
        new_path=loam_dir / NEW_SQLITE_FILENAME,
        handle_sqlite_siblings=True,
    )
    yaml_result = _migrate_one_pair(
        old_path=loam_dir / OLD_YAML_FILENAME,
        new_path=loam_dir / NEW_YAML_FILENAME,
        handle_sqlite_siblings=False,
    )
    return MigrationResult(sqlite=sqlite_result, yaml=yaml_result)
