"""Shared fixtures for Ruby/Rails adapter tests (v0.1.8 Cycle 3)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


_FIXTURE_SOURCE = (
    Path(__file__).parent.parent.parent / "fixtures" / "synthetic-rails"
)


@pytest.fixture
def synthetic_rails_repo(tmp_path: Path) -> Path:
    """A copy of the synthetic-rails fixture in a fresh tmp dir.

    The copy is initialised as a git repo with one committed snapshot
    so :func:`resolve_repo_sha` returns a deterministic SHA in tests.
    """
    target = tmp_path / "synthetic-rails"
    shutil.copytree(_FIXTURE_SOURCE, target)
    # Initialise as a git repo with a deterministic single commit.
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
         "commit", "--quiet", "-m", "synthetic-rails fixture"],
        cwd=target,
        check=True,
    )
    return target


@pytest.fixture
def synthetic_rails_repo_no_git(tmp_path: Path) -> Path:
    """A copy of the synthetic-rails fixture WITHOUT a git repo.

    Used to verify VERIFIED → PLAUSIBLE downgrade per AC.RAILS.3.
    """
    target = tmp_path / "synthetic-rails-no-git"
    shutil.copytree(_FIXTURE_SOURCE, target)
    return target


@pytest.fixture
def fixed_repo_sha() -> str:
    """A deterministic 40-char SHA used in tests that inject the SHA
    via monkeypatch (avoids dependence on git binary in some CI
    environments).
    """
    return "deadbeef" * 5


_CANONICAL_FIXTURE_SOURCE = (
    Path(__file__).parent.parent.parent / "fixtures" / "ruby-rails-payment"
)


@pytest.fixture
def canonical_ruby_rails_payment_repo(tmp_path: Path) -> Path:
    """A copy of the canonical ruby-rails-payment fixture in a fresh
    tmp dir (v0.1.8 Cycle 4b — AC.FIXTURES.2).

    The copy is initialised as a git repo with one committed snapshot
    so :func:`resolve_repo_sha` returns a deterministic SHA in tests.
    """
    target = tmp_path / "ruby-rails-payment"
    shutil.copytree(_CANONICAL_FIXTURE_SOURCE, target)
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
         "commit", "--quiet", "-m", "ruby-rails-payment fixture"],
        cwd=target,
        check=True,
    )
    return target


@pytest.fixture
def canonical_ruby_rails_payment_repo_no_git(tmp_path: Path) -> Path:
    """The canonical fixture without a git repo (for VERIFIED →
    PLAUSIBLE downgrade verification).
    """
    target = tmp_path / "ruby-rails-payment-no-git"
    shutil.copytree(_CANONICAL_FIXTURE_SOURCE, target)
    return target
