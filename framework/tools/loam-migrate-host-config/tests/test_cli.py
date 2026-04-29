"""CLI exit-code tests for the migration helper.

Cases 1, 2, 3 → exit 0. Case 4 → exit 2.
"""

from __future__ import annotations

from pathlib import Path

from loam_migrate_host_config.cli import main


def test_cli_case_1_migrated_returns_zero(tmp_path: Path) -> None:
    (tmp_path / ".pos").mkdir()
    rc = main(["--home", str(tmp_path)])
    assert rc == 0
    assert (tmp_path / ".loam").exists()


def test_cli_case_2_already_migrated_returns_zero(tmp_path: Path) -> None:
    (tmp_path / ".loam").mkdir()
    rc = main(["--home", str(tmp_path)])
    assert rc == 0


def test_cli_case_3_nothing_to_migrate_returns_zero(tmp_path: Path) -> None:
    rc = main(["--home", str(tmp_path)])
    assert rc == 0


def test_cli_case_4_conflict_returns_two(tmp_path: Path) -> None:
    (tmp_path / ".pos").mkdir()
    (tmp_path / ".loam").mkdir()
    rc = main(["--home", str(tmp_path)])
    assert rc == 2
    # Both dirs unchanged.
    assert (tmp_path / ".pos").exists()
    assert (tmp_path / ".loam").exists()
