"""AC.PRSI.2 — Pre-push hook installer."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from loam_pr_safety.installers import (
    InstallConflictError,
    LOAM_PR_SAFETY_VERSION,
    install_pre_push,
)


def _setup_basic_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "-C", str(repo), "init", "-q"], check=True
    )
    return repo


def _setup_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / ".loam").mkdir()
    return ws


def test_install_creates_pre_push_hook(tmp_path: Path) -> None:
    repo = _setup_basic_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    result = install_pre_push(repo, workspace_root=ws)

    assert result.action == "created"
    assert result.target_path == repo / ".git" / "hooks" / "pre-push"
    assert result.target_path.exists()
    content = result.target_path.read_text(encoding="utf-8")
    assert "loam-pr-safety:managed:" in content
    assert LOAM_PR_SAFETY_VERSION in content
    mode = result.target_path.stat().st_mode
    assert mode & 0o111
    assert not result.husky_routed


def test_install_pre_push_idempotent(tmp_path: Path) -> None:
    repo = _setup_basic_repo(tmp_path)
    ws = _setup_workspace(tmp_path)

    r1 = install_pre_push(repo, workspace_root=ws)
    r2 = install_pre_push(repo, workspace_root=ws)
    assert r1.action == "created"
    assert r2.action == "noop"


def test_install_pre_push_husky(
    repo_with_husky: Path, tmp_path: Path
) -> None:
    ws = _setup_workspace(tmp_path)
    result = install_pre_push(repo_with_husky, workspace_root=ws)

    assert result.husky_routed
    assert result.target_path == repo_with_husky / ".husky" / "pre-push"
    content = result.target_path.read_text(encoding="utf-8")
    assert "husky.sh" in content


def test_install_pre_push_halts_on_conflict(tmp_path: Path) -> None:
    repo = _setup_basic_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    target = repo / ".git" / "hooks" / "pre-push"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("#!/bin/sh\necho lol\n", encoding="utf-8")

    with pytest.raises(InstallConflictError):
        install_pre_push(repo, workspace_root=ws)
