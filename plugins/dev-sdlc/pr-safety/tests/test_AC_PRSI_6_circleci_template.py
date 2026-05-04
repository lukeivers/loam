"""AC.PRSI.6 — CircleCI template installer."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam_pr_safety.installers import (
    InstallConflictError,
    install_ci_circleci,
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


def test_install_creates_circleci_config(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)

    result = install_ci_circleci(repo, workspace_root=ws)
    assert result.action == "created"
    target = repo / ".circleci" / "config.yml"
    assert target.exists()
    content = target.read_text(encoding="utf-8")
    assert "loam-pr-safety:managed:start:" in content


def test_circleci_renders_yaml(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    install_ci_circleci(repo, workspace_root=ws)
    target = repo / ".circleci" / "config.yml"
    parsed = yaml.safe_load(target.read_text(encoding="utf-8"))
    assert parsed["version"] == 2.1
    assert "jobs" in parsed
    assert "loam_pr_safety" in parsed["jobs"]
    job = parsed["jobs"]["loam_pr_safety"]
    assert "docker" in job
    assert "steps" in job
    # steps include checkout + install + run gate.
    step_strs = [str(s) for s in job["steps"]]
    assert any("checkout" in s for s in step_strs)
    assert any("loam pr-safety gate" in s for s in step_strs)


def test_circleci_idempotent(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    r1 = install_ci_circleci(repo, workspace_root=ws)
    r2 = install_ci_circleci(repo, workspace_root=ws)
    assert r1.action == "created"
    assert r2.action == "noop"


def test_circleci_halts_on_conflict(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    target = repo / ".circleci" / "config.yml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "version: 2.1\njobs:\n  user_job:\n    docker:\n      - image: x\n    steps:\n      - checkout\n",
        encoding="utf-8",
    )

    with pytest.raises(InstallConflictError):
        install_ci_circleci(repo, workspace_root=ws)


def test_circleci_force_appends(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    target = repo / ".circleci" / "config.yml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "version: 2.1\njobs:\n  user_job:\n    docker:\n      - image: x\n    steps:\n      - checkout\n",
        encoding="utf-8",
    )

    result = install_ci_circleci(repo, workspace_root=ws, force=True)
    assert result.action == "force-replaced"
    final = target.read_text(encoding="utf-8")
    assert "loam-pr-safety:managed:start:" in final
