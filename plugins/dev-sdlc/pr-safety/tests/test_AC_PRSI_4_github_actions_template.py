"""AC.PRSI.4 — GitHub Actions CI template installer."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam_pr_safety.installers import (
    InstallConflictError,
    install_ci_github_actions,
)


def _setup_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    return repo


def _setup_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / ".loam").mkdir()
    return ws


def test_install_creates_workflow_file(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)

    result = install_ci_github_actions(repo, workspace_root=ws)

    assert result.action == "created"
    expected = repo / ".github" / "workflows" / "loam-pr-safety.yml"
    assert result.target_path == expected
    assert expected.exists()


def test_workflow_yaml_renders_validates(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)

    install_ci_github_actions(repo, workspace_root=ws)
    target = repo / ".github" / "workflows" / "loam-pr-safety.yml"
    parsed = yaml.safe_load(target.read_text(encoding="utf-8"))

    assert parsed["name"] == "loam-pr-safety"
    # YAML 1.1 parses `on:` as True (boolean alias). Accept either
    # the bool key or the string key.
    on_key = "on" if "on" in parsed else True
    on_val = parsed.get(on_key)
    assert "pull_request" in str(on_val), (
        f"expected pull_request trigger; got {on_val!r}"
    )
    assert "jobs" in parsed
    assert "gate" in parsed["jobs"]
    steps = parsed["jobs"]["gate"]["steps"]
    # Required steps: checkout, setup-python, install, run gate.
    step_names = [s.get("name", "") or "" for s in steps]
    assert any("Checkout" in n for n in step_names)
    assert any("Python" in n for n in step_names)
    assert any("Install" in n for n in step_names)
    assert any("gate" in n.lower() for n in step_names)


def test_workflow_idempotent(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)

    r1 = install_ci_github_actions(repo, workspace_root=ws)
    r2 = install_ci_github_actions(repo, workspace_root=ws)
    assert r1.action == "created"
    assert r2.action == "noop"


def test_workflow_halts_on_conflict(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    target = repo / ".github" / "workflows" / "loam-pr-safety.yml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "name: existing-non-loam\non: push\njobs: {}\n",
        encoding="utf-8",
    )

    with pytest.raises(InstallConflictError):
        install_ci_github_actions(repo, workspace_root=ws)


def test_workflow_force_replaces(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    target = repo / ".github" / "workflows" / "loam-pr-safety.yml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("name: existing\non: push\njobs: {}\n", encoding="utf-8")

    result = install_ci_github_actions(repo, workspace_root=ws, force=True)
    assert result.action == "force-replaced"
    assert result.backup_path is not None
    assert result.backup_path.exists()
    # New content is loam-managed.
    assert "loam-pr-safety:managed:" in target.read_text()


def test_workflow_dry_run(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    target = repo / ".github" / "workflows" / "loam-pr-safety.yml"

    result = install_ci_github_actions(repo, workspace_root=ws, dry_run=True)
    assert result.action == "dry-run"
    assert not target.exists()
