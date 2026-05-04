"""Shared pytest fixtures for odd-extractor tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_odd_extractor.registry import clear_manual_registry


@pytest.fixture(autouse=True)
def _clean_registry() -> None:
    """Manual-registration registry is module-level / process-wide.

    Each test gets a fresh state so tests can register stub adapters
    without leaking into siblings.
    """
    clear_manual_registry()


@pytest.fixture
def fixture_repo(tmp_path: Path) -> Path:
    """A small synthetic repo: README + main.py + a sub-directory."""
    repo = tmp_path / "fixture-repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Fixture\n", encoding="utf-8")
    (repo / "main.py").write_text("print('hello')\n", encoding="utf-8")
    sub = repo / "src"
    sub.mkdir()
    (sub / "lib.py").write_text("def f():\n    return 42\n", encoding="utf-8")
    # Hidden directory + dependency directory — should be skipped.
    git = repo / ".git"
    git.mkdir()
    (git / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    cache = repo / "__pycache__"
    cache.mkdir()
    (cache / "junk.pyc").write_text("not python\n", encoding="utf-8")
    return repo


@pytest.fixture
def workspace_root(tmp_path: Path) -> Path:
    """A fresh workspace root for each test."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    return ws


# Fixed timestamp for deterministic-output tests.
FIXED_TS = "2026-05-04T12:00:00+00:00"
