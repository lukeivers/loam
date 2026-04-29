"""Tests for the dormancy config-file migration helper.

Per-file four-case coverage (sqlite + yaml independently) plus
SQLite WAL/SHM sibling-file handling. Mirrors the M1b
loam-migrate-host-config test shape.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_migrate_dormancy_config.migrate import (
    FilePairStatus,
    migrate_dormancy_config,
)


def _setup_home(tmp_path: Path) -> Path:
    """Create the ~/.loam/ dir and return the simulated $HOME."""
    home = tmp_path
    (home / ".loam").mkdir()
    return home


def test_case_3_neither_present(tmp_path):
    """Fresh machine: neither old nor new file exists."""
    home = _setup_home(tmp_path)
    result = migrate_dormancy_config(home=home)

    assert result.sqlite.status is FilePairStatus.NOTHING_TO_MIGRATE
    assert result.yaml.status is FilePairStatus.NOTHING_TO_MIGRATE
    assert result.is_clean


def test_case_1_sqlite_only(tmp_path):
    """Old sqlite file exists; rename to new path."""
    home = _setup_home(tmp_path)
    (home / ".loam" / "degradation.sqlite").write_bytes(b"sqlite-content")

    result = migrate_dormancy_config(home=home)

    assert result.sqlite.status is FilePairStatus.MIGRATED
    assert result.yaml.status is FilePairStatus.NOTHING_TO_MIGRATE
    assert (home / ".loam" / "dormancy.sqlite").exists()
    assert not (home / ".loam" / "degradation.sqlite").exists()
    assert (home / ".loam" / "dormancy.sqlite").read_bytes() == b"sqlite-content"
    assert result.is_clean


def test_case_1_yaml_only(tmp_path):
    """Old yaml file exists; rename to new path."""
    home = _setup_home(tmp_path)
    (home / ".loam" / "degradation-config.yaml").write_text("key: value\n")

    result = migrate_dormancy_config(home=home)

    assert result.sqlite.status is FilePairStatus.NOTHING_TO_MIGRATE
    assert result.yaml.status is FilePairStatus.MIGRATED
    assert (home / ".loam" / "dormancy-config.yaml").exists()
    assert not (home / ".loam" / "degradation-config.yaml").exists()
    assert (home / ".loam" / "dormancy-config.yaml").read_text() == "key: value\n"


def test_case_1_both_files(tmp_path):
    """Old sqlite and yaml files both exist; rename both."""
    home = _setup_home(tmp_path)
    (home / ".loam" / "degradation.sqlite").write_bytes(b"db")
    (home / ".loam" / "degradation-config.yaml").write_text("k: v\n")

    result = migrate_dormancy_config(home=home)

    assert result.sqlite.status is FilePairStatus.MIGRATED
    assert result.yaml.status is FilePairStatus.MIGRATED
    assert (home / ".loam" / "dormancy.sqlite").exists()
    assert (home / ".loam" / "dormancy-config.yaml").exists()


def test_case_1_sqlite_wal_shm_siblings(tmp_path):
    """SQLite WAL/SHM sibling-file handling — rename concurrently."""
    home = _setup_home(tmp_path)
    (home / ".loam" / "degradation.sqlite").write_bytes(b"db")
    (home / ".loam" / "degradation.sqlite-wal").write_bytes(b"wal")
    (home / ".loam" / "degradation.sqlite-shm").write_bytes(b"shm")

    result = migrate_dormancy_config(home=home)

    assert result.sqlite.status is FilePairStatus.MIGRATED
    assert (home / ".loam" / "dormancy.sqlite").exists()
    assert (home / ".loam" / "dormancy.sqlite-wal").exists()
    assert (home / ".loam" / "dormancy.sqlite-shm").exists()
    assert not (home / ".loam" / "degradation.sqlite").exists()
    assert not (home / ".loam" / "degradation.sqlite-wal").exists()
    assert not (home / ".loam" / "degradation.sqlite-shm").exists()
    assert len(result.sqlite.siblings_renamed) == 2


def test_case_1_sqlite_missing_wal_tolerated(tmp_path):
    """SQLite WAL/SHM siblings can be missing; case-1 still proceeds."""
    home = _setup_home(tmp_path)
    (home / ".loam" / "degradation.sqlite").write_bytes(b"db")
    # Only -wal present; -shm missing.
    (home / ".loam" / "degradation.sqlite-wal").write_bytes(b"wal")

    result = migrate_dormancy_config(home=home)

    assert result.sqlite.status is FilePairStatus.MIGRATED
    assert (home / ".loam" / "dormancy.sqlite-wal").exists()
    assert not (home / ".loam" / "dormancy.sqlite-shm").exists()
    assert len(result.sqlite.siblings_renamed) == 1


def test_case_2_already_migrated(tmp_path):
    """New file exists, old does not; no-op."""
    home = _setup_home(tmp_path)
    (home / ".loam" / "dormancy.sqlite").write_bytes(b"new-content")
    (home / ".loam" / "dormancy-config.yaml").write_text("k: v\n")

    result = migrate_dormancy_config(home=home)

    assert result.sqlite.status is FilePairStatus.ALREADY_MIGRATED
    assert result.yaml.status is FilePairStatus.ALREADY_MIGRATED
    assert result.is_clean


def test_case_4_sqlite_conflict(tmp_path):
    """Both sqlite files exist; halt without modification on that pair."""
    home = _setup_home(tmp_path)
    (home / ".loam" / "degradation.sqlite").write_bytes(b"old")
    (home / ".loam" / "dormancy.sqlite").write_bytes(b"new")

    result = migrate_dormancy_config(home=home)

    assert result.sqlite.status is FilePairStatus.CONFLICT
    assert (home / ".loam" / "degradation.sqlite").exists()
    assert (home / ".loam" / "dormancy.sqlite").exists()
    assert (home / ".loam" / "degradation.sqlite").read_bytes() == b"old"
    assert (home / ".loam" / "dormancy.sqlite").read_bytes() == b"new"
    assert not result.is_clean


def test_case_4_yaml_conflict(tmp_path):
    """Both yaml files exist; halt without modification on that pair."""
    home = _setup_home(tmp_path)
    (home / ".loam" / "degradation-config.yaml").write_text("old: 1\n")
    (home / ".loam" / "dormancy-config.yaml").write_text("new: 1\n")

    result = migrate_dormancy_config(home=home)

    assert result.yaml.status is FilePairStatus.CONFLICT
    assert not result.is_clean


def test_idempotent_case_1_then_case_2(tmp_path):
    """Running case-1, then re-running, yields case 2."""
    home = _setup_home(tmp_path)
    (home / ".loam" / "degradation.sqlite").write_bytes(b"db")
    (home / ".loam" / "degradation-config.yaml").write_text("k: v\n")

    first = migrate_dormancy_config(home=home)
    assert first.sqlite.status is FilePairStatus.MIGRATED
    assert first.yaml.status is FilePairStatus.MIGRATED

    second = migrate_dormancy_config(home=home)
    assert second.sqlite.status is FilePairStatus.ALREADY_MIGRATED
    assert second.yaml.status is FilePairStatus.ALREADY_MIGRATED


def test_combined_message_includes_both_pairs(tmp_path):
    """combined_message reports both sqlite and yaml results."""
    home = _setup_home(tmp_path)
    result = migrate_dormancy_config(home=home)

    assert "sqlite:" in result.combined_message
    assert "yaml:" in result.combined_message
