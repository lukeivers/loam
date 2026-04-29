"""Shared test fixtures for workspace-bootstrap."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Callable

import pytest
import yaml


def write_manifest(path: Path, contributions: list, **extras: Any) -> Path:
    """Write a bootstrap.yaml at `path` with the given contributions list."""
    payload: dict[str, Any] = {
        "version": 1,
        "contributions": contributions,
    }
    payload.update(extras)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload))
    return path


@pytest.fixture
def write_manifest_fn() -> Callable[..., Path]:
    return write_manifest


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Standard test workspace with config/ and data/ subdirs."""
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    return tmp_path


# ---- D.4 fixtures (test_pos_new_workspace.py) -----------------------


def _git(args: list[str], *, cwd: Path) -> None:
    """Run git in ``cwd``; raise on non-zero exit. Used by fixture setup."""
    completed = subprocess.run(  # noqa: S603 — argv constructed
        ["git", *args],
        cwd=str(cwd),
        stdin=subprocess.DEVNULL,
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


def _make_fixture_canonical(
    root: Path,
    *,
    files: dict[str, str] | None = None,
    publish_framework_only: bool = True,
) -> Path:
    """Construct an ephemeral fixture canonical pos-v2 working tree.

    Initialises a git repo at ``root``, writes ``files`` (a mapping
    of relative path to content), and commits them. Returns ``root``.

    Defaults to a small representative file set when ``files`` is None
    (mirrors a stripped-down canonical layout — enough that the
    bootstrap's clone produces a non-trivial framework/ subtree but
    fast enough that test runtime is bounded).

    Single-framework restructure (amendment #67, AC.SFR.1):
    ``publish_framework_only=True`` (default) also synthesises the
    ``framework-only`` branch via ``pos-publish-framework-only`` so
    fixture canonicals match the post-restructure shape consumed by
    ``pos-new-workspace``. Tests verifying the failure mode when
    ``framework-only`` is absent pass ``publish_framework_only=False``.
    """
    if files is None:
        files = {
            "framework/workspace-sync/src/workspace_sync/__init__.py": (
                '"""Test fixture canonical workspace-sync package."""\n'
                "__version__ = \"0.0.0-fixture\"\n"
            ),
            "framework/workspace-bootstrap/src/workspace_bootstrap/__init__.py": (
                '"""Test fixture canonical workspace-bootstrap package."""\n'
            ),
            "framework/README.md": "# fixture canonical framework/\n",
            "docs/odd-methodology.md": "# fixture odd-methodology\n",
            "CLAUDE.md": "# fixture CLAUDE.md\n",
        }
    root.mkdir(parents=True, exist_ok=True)
    _git(["init", "--initial-branch=pos-v2"], cwd=root)
    _git(["config", "user.email", "fixture@local"], cwd=root)
    _git(["config", "user.name", "fixture"], cwd=root)
    for rel, content in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    _git(["add", "-A"], cwd=root)
    _git(["commit", "-m", "fixture canonical initial commit"], cwd=root)

    if publish_framework_only:
        # Compose on the synthesis tool to publish the framework-only
        # branch. The tool composes git plumbing (no working-tree
        # mutation), so the pos-v2 branch is unchanged post-call
        # (AC.SFR.5 binding: stranger-clones-canonical preserved).
        from loam.publish_framework_only.synth import (  # noqa: PLC0415
            synthesise_framework_only,
        )
        synthesise_framework_only(root)

    return root


@pytest.fixture
def make_fixture_canonical() -> Callable[..., Path]:
    """Factory fixture for constructing a fixture canonical repo.

    Tests call this with a target path (and optional file dict) and
    receive an absolute Path to a fresh git working tree. Mirrors the
    pattern in workspace-sync's `test_cli_d_shape.py` (D.3) so D.4's
    bootstrap tests can reuse the same canonical-shape.
    """
    return _make_fixture_canonical
