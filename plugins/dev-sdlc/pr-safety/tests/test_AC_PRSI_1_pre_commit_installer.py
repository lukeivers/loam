"""AC.PRSI.1 — Pre-commit hook installer.

Per Cycle 2 plan-doc §4. Idempotent + husky-aware + halt-on-conflict
+ executable.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from loam_pr_safety.installers import (
    InstallConflictError,
    LOAM_PR_SAFETY_VERSION,
    install_pre_commit,
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


def test_install_creates_pre_commit_hook(tmp_path: Path) -> None:
    repo = _setup_basic_repo(tmp_path)
    ws = _setup_workspace(tmp_path)

    result = install_pre_commit(repo, workspace_root=ws)

    assert result.action == "created"
    assert result.target_path == repo / ".git" / "hooks" / "pre-commit"
    assert result.target_path.exists()
    content = result.target_path.read_text(encoding="utf-8")
    assert "loam-pr-safety:managed:" in content
    assert LOAM_PR_SAFETY_VERSION in content
    # executable bit set.
    mode = result.target_path.stat().st_mode
    assert mode & 0o111, f"hook not executable: mode={oct(mode)}"
    assert not result.husky_routed


def test_install_is_idempotent(tmp_path: Path) -> None:
    repo = _setup_basic_repo(tmp_path)
    ws = _setup_workspace(tmp_path)

    r1 = install_pre_commit(repo, workspace_root=ws)
    assert r1.action == "created"
    content_after_r1 = r1.target_path.read_text(encoding="utf-8")

    r2 = install_pre_commit(repo, workspace_root=ws)
    assert r2.action == "noop"
    assert r2.target_path.read_text(encoding="utf-8") == content_after_r1


def test_install_halts_on_non_loam_content(tmp_path: Path) -> None:
    repo = _setup_basic_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    target = repo / ".git" / "hooks" / "pre-commit"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "#!/bin/sh\necho 'pre-existing non-loam hook'\n",
        encoding="utf-8",
    )
    target.chmod(0o755)

    with pytest.raises(InstallConflictError) as exc_info:
        install_pre_commit(repo, workspace_root=ws)
    assert exc_info.value.result.is_conflict
    assert "non-loam content" in str(exc_info.value).lower()
    # File NOT overwritten.
    assert "pre-existing non-loam hook" in target.read_text()


def test_install_force_replaces_with_backup(tmp_path: Path) -> None:
    repo = _setup_basic_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    target = repo / ".git" / "hooks" / "pre-commit"
    target.parent.mkdir(parents=True, exist_ok=True)
    original_content = "#!/bin/sh\necho 'pre-existing'\n"
    target.write_text(original_content, encoding="utf-8")
    target.chmod(0o755)

    result = install_pre_commit(repo, workspace_root=ws, force=True)
    assert result.action == "force-replaced"
    assert result.backup_path is not None
    assert result.backup_path.exists()
    assert result.backup_path.read_text() == original_content
    # New hook content is loam-managed.
    assert "loam-pr-safety:managed:" in target.read_text()


def test_install_dry_run_does_not_write(tmp_path: Path) -> None:
    repo = _setup_basic_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    target = repo / ".git" / "hooks" / "pre-commit"

    result = install_pre_commit(repo, workspace_root=ws, dry_run=True)
    assert result.action == "dry-run"
    assert not target.exists()


def test_install_husky_routed(repo_with_husky: Path, tmp_path: Path) -> None:
    ws = _setup_workspace(tmp_path)
    result = install_pre_commit(repo_with_husky, workspace_root=ws)

    assert result.action == "created"
    assert result.husky_routed
    assert result.target_path == repo_with_husky / ".husky" / "pre-commit"
    assert result.target_path.exists()
    content = result.target_path.read_text(encoding="utf-8")
    assert "husky.sh" in content
    assert "loam-pr-safety:managed:" in content


def test_install_audit_logs(tmp_path: Path) -> None:
    repo = _setup_basic_repo(tmp_path)
    ws = _setup_workspace(tmp_path)

    install_pre_commit(repo, workspace_root=ws)

    audit_dir = ws / ".loam" / "pr-safety" / "audit-log"
    assert audit_dir.exists()
    entries = list(audit_dir.iterdir())
    assert len(entries) == 1
    import yaml
    payload = yaml.safe_load(entries[0].read_text(encoding="utf-8"))
    assert payload["event_kind"] == "install_pre_commit"
    assert payload["target_path"].endswith(".git/hooks/pre-commit")


def test_install_refresh_on_version_change(
    monkeypatch, tmp_path: Path
) -> None:
    repo = _setup_basic_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    target = repo / ".git" / "hooks" / "pre-commit"
    target.parent.mkdir(parents=True, exist_ok=True)
    # Pre-existing loam-managed hook with OLD version.
    old_content = (
        "#!/usr/bin/env bash\n"
        "# loam-pr-safety:managed:0.1.0\n"
        "echo old\n"
    )
    target.write_text(old_content, encoding="utf-8")
    target.chmod(0o755)

    result = install_pre_commit(repo, workspace_root=ws)
    assert result.action == "refreshed"
    assert result.prior_version == "0.1.0"
    new_content = target.read_text(encoding="utf-8")
    assert LOAM_PR_SAFETY_VERSION in new_content
