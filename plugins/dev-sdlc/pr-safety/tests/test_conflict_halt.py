"""Conflict halt — Surface #3 + AC.PRSI.8 exit code 6."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from loam_pr_safety.installers import (
    InstallConflictError,
    install_ci_circleci,
    install_ci_github_actions,
    install_ci_gitlab_ci,
    install_pr_template,
    install_pre_commit,
    install_pre_push,
)


def _setup_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    return repo


def _setup_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / ".loam").mkdir()
    return ws


def test_pre_commit_conflict_writes_audit_entry(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    target = repo / ".git" / "hooks" / "pre-commit"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("#!/bin/sh\necho hi\n", encoding="utf-8")

    with pytest.raises(InstallConflictError):
        install_pre_commit(repo, workspace_root=ws)

    audit_dir = ws / ".loam" / "pr-safety" / "audit-log"
    entries = list(audit_dir.iterdir())
    assert len(entries) == 1
    data = yaml.safe_load(entries[0].read_text(encoding="utf-8"))
    assert data["event_kind"] == "install_conflict"
    assert data["decision"] == "conflict-halted"


def test_no_silent_overwrite_for_any_surface(tmp_path: Path) -> None:
    """No installer silently overwrites non-loam content."""
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    surfaces = [
        (
            install_pre_commit,
            repo / ".git" / "hooks" / "pre-commit",
            "#!/bin/sh\necho 1\n",
        ),
        (
            install_pre_push,
            repo / ".git" / "hooks" / "pre-push",
            "#!/bin/sh\necho 2\n",
        ),
        (
            install_ci_github_actions,
            repo / ".github" / "workflows" / "loam-pr-safety.yml",
            "name: x\non: push\njobs: {}\n",
        ),
        (
            install_ci_gitlab_ci,
            repo / ".gitlab-ci.yml",
            "stages: [build]\nuserjob:\n  stage: build\n  script:\n    - true\n",
        ),
        (
            install_ci_circleci,
            repo / ".circleci" / "config.yml",
            "version: 2.1\njobs:\n  x:\n    docker:\n      - image: y\n    steps:\n      - checkout\n",
        ),
        (
            install_pr_template,
            repo / ".github" / "pull_request_template.md",
            "## Custom team template\n\nLeftover.\n",
        ),
    ]
    for installer, target, original_content in surfaces:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(original_content, encoding="utf-8")
        with pytest.raises(InstallConflictError):
            installer(repo, workspace_root=ws)
        # File NOT overwritten.
        assert target.read_text(encoding="utf-8") == original_content, (
            f"surface {installer.__name__} silently overwrote "
            f"non-loam content at {target}"
        )


def test_force_creates_backup_for_pre_commit(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    target = repo / ".git" / "hooks" / "pre-commit"
    target.parent.mkdir(parents=True, exist_ok=True)
    original = "#!/bin/sh\necho original\n"
    target.write_text(original, encoding="utf-8")

    result = install_pre_commit(repo, workspace_root=ws, force=True)
    assert result.action == "force-replaced"
    assert result.backup_path is not None
    assert result.backup_path.exists()
    assert result.backup_path.read_text(encoding="utf-8") == original
    assert "loam-pr-safety:managed:" in target.read_text(encoding="utf-8")


def test_conflict_excerpt_truncated_to_200_chars(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    target = repo / ".git" / "hooks" / "pre-commit"
    target.parent.mkdir(parents=True, exist_ok=True)
    # Real content (echo lines, not just comments) so
    # `is_effectively_empty` returns False and conflict triggers.
    long_content = (
        "#!/bin/sh\n"
        + "# header comment\n"
        + ("echo line\n" * 100)
    )
    target.write_text(long_content, encoding="utf-8")

    with pytest.raises(InstallConflictError) as exc_info:
        install_pre_commit(repo, workspace_root=ws)
    assert len(exc_info.value.result.conflict_excerpt) <= 200
