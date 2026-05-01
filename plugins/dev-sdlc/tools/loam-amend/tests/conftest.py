"""Shared fixtures for the loam amend test suite."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def scratch_repo(tmp_path: Path) -> Path:
    """Create a tiny throwaway git repo with one commit so baseline
    comparisons resolve. Tests that need seal-test files populate them
    on top of this scaffold.
    """
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "loam amend test"],
        cwd=tmp_path,
        check=True,
    )
    (tmp_path / "README.md").write_text("scratch\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "initial"], cwd=tmp_path, check=True
    )
    return tmp_path
