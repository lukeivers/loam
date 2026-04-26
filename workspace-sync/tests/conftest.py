"""Shared pytest fixtures for workspace-sync tests."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

# Add src/ to path for editable imports when running against tree.
_HERE = Path(__file__).parent
sys.path.insert(0, str((_HERE.parent / "src").resolve()))


@pytest.fixture
def make_canonical_repo(tmp_path: Path):
    """Build a fresh git repo at <tmp>/canonical with seeded files.

    Returns a callable: ``make(files: dict[str, str]) -> Path``. The
    callable initialises a git repo, writes each path with the given
    content, commits, and returns the canonical root.
    """

    def _make(files: dict[str, str], *, name: str = "canonical") -> Path:
        root = tmp_path / name
        root.mkdir()
        subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
        subprocess.run(
            ["git", "-C", str(root), "config", "user.email", "t@t"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(root), "config", "user.name", "t"],
            check=True,
        )
        # Disable signing for hermetic tests.
        subprocess.run(
            ["git", "-C", str(root), "config", "commit.gpgsign", "false"],
            check=True,
        )
        for rel, content in files.items():
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
        subprocess.run(
            ["git", "-C", str(root), "commit", "-q", "-m", "seed"],
            check=True,
        )
        return root

    return _make


@pytest.fixture
def make_workspace(tmp_path: Path):
    """Build a workspace dir with optional seeded files + .pos/ scaffold."""

    def _make(
        files: dict[str, str] | None = None,
        *,
        name: str = "workspace",
        seed_envelope: bool = False,
    ) -> Path:
        root = tmp_path / name
        root.mkdir()
        # A `.git` marker is used by derive_workspace_root's fall-through;
        # tests opt in by passing files containing `.git/...`.
        if files:
            for rel, content in files.items():
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
        if seed_envelope:
            from workspace_sync.sync_protected import write_default_if_absent
            write_default_if_absent(root)
        return root

    return _make


@pytest.fixture
def sha256_of():
    def _h(s: str) -> str:
        return hashlib.sha256(s.encode("utf-8")).hexdigest()
    return _h
