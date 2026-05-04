"""D2 idempotency variant — 5+ install runs are noop for stable
content; loam-managed content detected via sentinel."""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from loam_pr_safety.installers import (
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
    subprocess.run(
        ["git", "-C", str(repo), "init", "-q"], check=True
    )
    return repo


def _setup_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / ".loam").mkdir()
    return ws


def test_d2_5x_install_pre_commit_noop_after_first(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)

    actions = []
    for _ in range(5):
        result = install_pre_commit(repo, workspace_root=ws)
        actions.append(result.action)

    assert actions[0] == "created"
    assert all(a == "noop" for a in actions[1:])


def test_d2_5x_install_all_byte_equal_content(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)

    install_funcs = [
        install_pre_commit,
        install_pre_push,
        install_ci_github_actions,
        install_ci_gitlab_ci,
        install_ci_circleci,
        install_pr_template,
    ]

    snapshots = []
    for run in range(5):
        round_snap = {}
        for fn in install_funcs:
            result = fn(repo, workspace_root=ws)
            round_snap[result.surface] = (
                result.target_path.read_text(encoding="utf-8")
            )
        snapshots.append(round_snap)

    # All 5 snapshots byte-equal.
    for r in range(1, 5):
        for surface, content in snapshots[r].items():
            assert content == snapshots[0][surface], (
                f"surface {surface} changed at run {r}"
            )


def test_d2_audit_log_records_noops_too(tmp_path: Path) -> None:
    """Each install (incl noops) writes one audit-log entry."""
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)

    install_pre_commit(repo, workspace_root=ws)
    install_pre_commit(repo, workspace_root=ws)
    install_pre_commit(repo, workspace_root=ws)

    audit_dir = ws / ".loam" / "pr-safety" / "audit-log"
    entries = list(audit_dir.iterdir())
    assert len(entries) == 3
    actions = []
    for p in sorted(entries):
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        actions.append(data["decision"])
    assert actions == ["created", "noop", "noop"]
