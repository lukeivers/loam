"""Shared test fixtures for pos-publish-framework-only."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

import pytest


def _git(args: list[str], *, cwd: Path) -> str:
    completed = subprocess.run(  # noqa: S603
        ["git", *args],
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed in {cwd!s}: "
            f"{(completed.stderr or '').strip()!r}"
        )
    return completed.stdout.rstrip("\n")


def _make_fixture_canonical(
    root: Path,
    *,
    files: dict[str, str] | None = None,
    branch: str = "pos-v2",
) -> Path:
    """Construct a fixture canonical with framework/ + top-level docs."""
    if files is None:
        files = {
            "framework/cost-governance/__init__.py": (
                '"""fixture cost-governance"""\n'
            ),
            "framework/workspace-bootstrap/src/__init__.py": (
                '"""fixture workspace-bootstrap"""\n'
            ),
            "framework/tools/loam-mode/__init__.py": (
                '"""fixture loam-mode"""\n'
            ),
            "CLAUDE.md": "# fixture CLAUDE.md\n",
            "CLAUDE.dev.md": "# fixture CLAUDE.dev.md\n",
            "README.md": "# fixture README.md\n",
            "docs/odd-methodology.md": "# fixture odd-methodology\n",
            "docs/rebuild/STATE.md": "# fixture STATE.md\n",
        }
    root.mkdir(parents=True, exist_ok=True)
    _git(["init", f"--initial-branch={branch}"], cwd=root)
    _git(["config", "user.email", "fixture@local"], cwd=root)
    _git(["config", "user.name", "fixture"], cwd=root)
    for rel, content in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    _git(["add", "-A"], cwd=root)
    _git(["commit", "-m", "fixture canonical initial commit"], cwd=root)
    return root


@pytest.fixture
def make_fixture_canonical() -> Callable[..., Path]:
    return _make_fixture_canonical


@pytest.fixture
def git_run() -> Callable[..., str]:
    return _git
