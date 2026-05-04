"""Shared fixtures for JS/TS/Playwright adapter tests
(v0.1.8 Cycle 4a).

Mirror of ``tests/lang/ruby/conftest.py`` (Cycle 3). Provides:

- :func:`jsts_playwright_app_repo` — a copy of the
  jsts-playwright-app fixture in a fresh tmp dir, initialized as a
  git repo with a deterministic single commit (so
  :func:`resolve_repo_sha` returns a stable value).
- :func:`jsts_playwright_app_repo_no_git` — same fixture without a
  git repo (used to verify VERIFIED→PLAUSIBLE downgrade).
- :func:`fixed_repo_sha` — deterministic SHA for monkeypatch tests.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


_FIXTURE_SOURCE = (
    Path(__file__).parent.parent.parent
    / "fixtures"
    / "jsts-playwright-app"
)


@pytest.fixture
def jsts_playwright_app_repo(tmp_path: Path) -> Path:
    """A copy of the jsts-playwright-app fixture in a fresh tmp dir.

    The copy is initialised as a git repo with one committed
    snapshot so :func:`resolve_repo_sha` returns a deterministic
    SHA in tests.
    """
    target = tmp_path / "jsts-playwright-app"
    shutil.copytree(_FIXTURE_SOURCE, target)
    subprocess.run(
        ["git", "init", "--quiet", "--initial-branch=main"],
        cwd=target,
        check=True,
    )
    subprocess.run(
        ["git", "-c", "user.email=test@example.com",
         "-c", "user.name=test",
         "add", "-A"],
        cwd=target,
        check=True,
    )
    subprocess.run(
        ["git", "-c", "user.email=test@example.com",
         "-c", "user.name=test",
         "commit", "--quiet", "-m", "jsts-playwright-app fixture"],
        cwd=target,
        check=True,
    )
    return target


@pytest.fixture
def jsts_playwright_app_repo_no_git(tmp_path: Path) -> Path:
    """A copy of the fixture WITHOUT a git repo.

    Used to verify VERIFIED → PLAUSIBLE downgrade per AC.JSTS.3.
    """
    target = tmp_path / "jsts-playwright-app-no-git"
    shutil.copytree(_FIXTURE_SOURCE, target)
    return target


@pytest.fixture
def fixed_repo_sha() -> str:
    """A deterministic 40-char SHA used in tests that inject the SHA
    via monkeypatch.
    """
    return "deadbeef" * 5
