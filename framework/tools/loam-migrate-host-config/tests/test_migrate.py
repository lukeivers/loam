"""AC.RNM-1b.3 — migration helper idempotency contract.

Four named cases per the M1b sub-plan §4.AC.RNM-1b.3:

  1. OLD_EXISTS_NEW_ABSENT: rename happens; result is MIGRATED.
  2. NEW_EXISTS_OLD_ABSENT: no-op; result is ALREADY_MIGRATED.
  3. NEITHER: no-op; result is NOTHING_TO_MIGRATE.
  4. BOTH: halt without modification; result is CONFLICT.

Plus a re-run idempotency check: case 1 followed by re-invocation
hits case 2.
"""

from __future__ import annotations

from pathlib import Path

from loam_migrate_host_config import migrate_host_config
from loam_migrate_host_config.migrate import MigrationStatus


def test_case_1_old_exists_new_absent_renames(tmp_path: Path) -> None:
    """Case 1: ``~/.pos/`` present, ``~/.loam/`` absent → rename."""
    old = tmp_path / ".pos"
    new = tmp_path / ".loam"
    old.mkdir()
    (old / "marker.txt").write_text("witness")

    result = migrate_host_config(home=tmp_path)

    assert result.status is MigrationStatus.MIGRATED
    assert result.is_clean
    assert not old.exists(), "old dir must be gone post-rename"
    assert new.exists(), "new dir must exist post-rename"
    assert (new / "marker.txt").read_text() == "witness", (
        "rename must preserve directory contents byte-identical"
    )
    assert "Migrated" in result.message


def test_case_2_new_exists_old_absent_already_migrated(tmp_path: Path) -> None:
    """Case 2: ``~/.loam/`` present, ``~/.pos/`` absent → no-op."""
    new = tmp_path / ".loam"
    new.mkdir()
    (new / "marker.txt").write_text("post-migrate")

    result = migrate_host_config(home=tmp_path)

    assert result.status is MigrationStatus.ALREADY_MIGRATED
    assert result.is_clean
    assert not (tmp_path / ".pos").exists()
    assert new.exists()
    assert (new / "marker.txt").read_text() == "post-migrate", (
        "case 2 must not modify content"
    )
    assert "Already migrated" in result.message


def test_case_3_neither_exists_nothing_to_migrate(tmp_path: Path) -> None:
    """Case 3: neither dir present → no-op."""
    # tmp_path is empty by default.
    result = migrate_host_config(home=tmp_path)

    assert result.status is MigrationStatus.NOTHING_TO_MIGRATE
    assert result.is_clean
    assert not (tmp_path / ".pos").exists()
    assert not (tmp_path / ".loam").exists()
    assert "Nothing to migrate" in result.message


def test_case_4_both_exist_halt_conflict(tmp_path: Path) -> None:
    """Case 4: both dirs present → halt; no modification."""
    old = tmp_path / ".pos"
    new = tmp_path / ".loam"
    old.mkdir()
    new.mkdir()
    (old / "old-marker.txt").write_text("old")
    (new / "new-marker.txt").write_text("new")

    result = migrate_host_config(home=tmp_path)

    assert result.status is MigrationStatus.CONFLICT
    assert not result.is_clean
    # Both dirs unchanged.
    assert old.exists()
    assert new.exists()
    assert (old / "old-marker.txt").read_text() == "old"
    assert (new / "new-marker.txt").read_text() == "new"
    assert "CONFLICT" in result.message


def test_idempotent_rerun_after_case_1_hits_case_2(tmp_path: Path) -> None:
    """Re-running the helper after a case-1 success hits case 2 (no-op)."""
    old = tmp_path / ".pos"
    old.mkdir()
    (old / "marker.txt").write_text("witness")

    first = migrate_host_config(home=tmp_path)
    assert first.status is MigrationStatus.MIGRATED

    # Re-run — should be safe.
    second = migrate_host_config(home=tmp_path)
    assert second.status is MigrationStatus.ALREADY_MIGRATED
    assert second.is_clean
    # Content still preserved.
    assert (tmp_path / ".loam" / "marker.txt").read_text() == "witness"


def test_idempotent_rerun_after_case_3_hits_case_3(tmp_path: Path) -> None:
    """Re-running on a fresh machine stays in case 3 (no state created)."""
    first = migrate_host_config(home=tmp_path)
    assert first.status is MigrationStatus.NOTHING_TO_MIGRATE

    second = migrate_host_config(home=tmp_path)
    assert second.status is MigrationStatus.NOTHING_TO_MIGRATE
    # No dirs created by the helper.
    assert not (tmp_path / ".pos").exists()
    assert not (tmp_path / ".loam").exists()


def test_case_4_repeats_until_resolved(tmp_path: Path) -> None:
    """Case 4 keeps producing CONFLICT until the user resolves manually."""
    (tmp_path / ".pos").mkdir()
    (tmp_path / ".loam").mkdir()

    first = migrate_host_config(home=tmp_path)
    assert first.status is MigrationStatus.CONFLICT

    second = migrate_host_config(home=tmp_path)
    assert second.status is MigrationStatus.CONFLICT
