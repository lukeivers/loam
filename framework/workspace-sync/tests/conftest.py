"""Shared pytest fixtures for workspace-sync tests.

D-migration D.3 (amendment #64): adds ``make_framework_workspace`` +
``make_advancing_canonical`` fixtures to construct git-merge-shaped
test workspaces.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

# Add src/ to path for editable imports when running against tree.
_HERE = Path(__file__).parent
sys.path.insert(0, str((_HERE.parent / "src").resolve()))
# Also add the tests directory itself so a test-side stub resolver
# can be imported via `importlib.import_module("_stub_resolver")`.
sys.path.insert(0, str(_HERE.resolve()))


def _git(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess:
    """Run ``git`` with hermetic-test config baked in."""
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _git_init(root: Path, *, branch: str = "pos-v2") -> None:
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "-q", "-b", branch, str(root)], check=True
    )
    _git(["config", "user.email", "t@t"], cwd=root)
    _git(["config", "user.name", "t"], cwd=root)
    _git(["config", "commit.gpgsign", "false"], cwd=root)


@pytest.fixture
def make_canonical_repo(tmp_path: Path):
    """Build a fresh git repo at <tmp>/canonical with seeded files.

    Returns a callable: ``make(files: dict[str, str]) -> Path``. The
    callable initialises a git repo on branch ``pos-v2`` (default
    branch under D), writes each path with the given content,
    commits, and returns the canonical root.
    """

    def _make(
        files: dict[str, str],
        *,
        name: str = "canonical",
        branch: str = "pos-v2",
    ) -> Path:
        root = tmp_path / name
        _git_init(root, branch=branch)
        for rel, content in files.items():
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        _git(["add", "-A"], cwd=root)
        _git(["commit", "-q", "-m", "seed"], cwd=root)
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
        root.mkdir(parents=True, exist_ok=True)
        if files:
            for rel, content in files.items():
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
        if seed_envelope:
            from loam.workspace_sync.sync_protected import write_default_if_absent
            (root / "workspace" / ".pos").mkdir(parents=True, exist_ok=True)
            write_default_if_absent(root)
        return root

    return _make


@pytest.fixture
def make_framework_workspace(tmp_path: Path, make_canonical_repo):
    """Build a fixture workspace shaped per D.3:
    ``<fixture-ws>/framework/`` is a git clone of a canonical repo;
    ``<fixture-ws>/workspace/`` carries any seeded workspace-state.

    Returns a callable: ``make(canonical_files, *, workspace_files,
    branch) -> tuple[fixture_ws, canonical_root]``.
    """

    def _make(
        canonical_files: dict[str, str],
        *,
        workspace_files: dict[str, str] | None = None,
        branch: str = "pos-v2",
        ws_name: str = "fixture_ws",
    ) -> tuple[Path, Path]:
        canonical_root = make_canonical_repo(
            canonical_files, name=f"{ws_name}_canonical", branch=branch
        )
        fixture_ws = tmp_path / ws_name
        fixture_ws.mkdir(parents=True, exist_ok=True)
        # Clone canonical into <fixture-ws>/framework/
        framework_root = fixture_ws / "framework"
        subprocess.run(
            [
                "git",
                "clone",
                "-q",
                "-b",
                branch,
                str(canonical_root),
                str(framework_root),
            ],
            check=True,
        )
        _git(["config", "user.email", "t@t"], cwd=framework_root)
        _git(["config", "user.name", "t"], cwd=framework_root)
        _git(
            ["config", "commit.gpgsign", "false"],
            cwd=framework_root,
        )
        # The clone defaults the remote to "origin"; rename to
        # "canonical" so D.3's CLI's idempotent remote-config sees
        # the existing remote at the expected name. (The CLI also
        # handles the "no canonical remote yet" case, but pre-naming
        # makes the test fixture closer to a steady-state workspace.)
        # Actually, leave the test surfaces clean: don't pre-name.
        # The CLI's _configure_canonical_remote will add "canonical"
        # as a SECOND remote, which is fine for tests.
        # Seed workspace-state.
        if workspace_files:
            for rel, content in workspace_files.items():
                target = fixture_ws / "workspace" / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
        # Seed sync-config so the CLI can resolve canonical without
        # an explicit --canonical flag.
        sync_config_path = (
            fixture_ws / "workspace" / ".pos" / "sync-config.yaml"
        )
        sync_config_path.parent.mkdir(parents=True, exist_ok=True)
        sync_config_path.write_text(
            f"canonical_source: {canonical_root}\n"
        )
        return fixture_ws, canonical_root

    return _make


@pytest.fixture
def advance_canonical(tmp_path: Path):
    """Advance an existing canonical repo with a new commit.

    Returns a callable:
    ``advance(canonical_root, files, message) -> new_sha``.
    """

    def _advance(
        canonical_root: Path,
        files: dict[str, str | None],
        *,
        message: str = "advance",
    ) -> str:
        for rel, content in files.items():
            target = canonical_root / rel
            if content is None:
                # Deletion.
                if target.exists():
                    target.unlink()
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
        _git(["add", "-A"], cwd=canonical_root)
        _git(["commit", "-q", "-m", message], cwd=canonical_root)
        completed = _git(["rev-parse", "HEAD"], cwd=canonical_root)
        return completed.stdout.strip()

    return _advance


@pytest.fixture
def workspace_commit(tmp_path: Path):
    """Make a commit on <fixture-ws>/framework/ (workspace-side edit).

    Returns a callable:
    ``commit(fixture_ws, files, message) -> new_sha``.
    """

    def _commit(
        fixture_ws: Path,
        files: dict[str, str],
        *,
        message: str = "workspace edit",
    ) -> str:
        framework = fixture_ws / "framework"
        for rel, content in files.items():
            target = framework / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        _git(["add", "-A"], cwd=framework)
        _git(["commit", "-q", "-m", message], cwd=framework)
        completed = _git(["rev-parse", "HEAD"], cwd=framework)
        return completed.stdout.strip()

    return _commit


@pytest.fixture
def sha256_of():
    def _h(s: str) -> str:
        return hashlib.sha256(s.encode("utf-8")).hexdigest()
    return _h
