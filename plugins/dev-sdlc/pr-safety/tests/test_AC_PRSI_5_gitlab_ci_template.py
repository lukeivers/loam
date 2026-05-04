"""AC.PRSI.5 — GitLab CI template installer."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam_pr_safety.installers import (
    InstallConflictError,
    install_ci_gitlab_ci,
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


def test_install_creates_gitlab_ci_file(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)

    result = install_ci_gitlab_ci(repo, workspace_root=ws)
    assert result.action == "created"
    target = repo / ".gitlab-ci.yml"
    assert target.exists()
    content = target.read_text(encoding="utf-8")
    assert "loam-pr-safety:managed:start:" in content
    assert "loam-pr-safety:managed:end" in content


def test_gitlab_ci_renders_yaml(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    install_ci_gitlab_ci(repo, workspace_root=ws)
    target = repo / ".gitlab-ci.yml"
    parsed = yaml.safe_load(target.read_text(encoding="utf-8"))
    assert "stages" in parsed
    assert "loam_pr_safety" in parsed
    job = parsed["loam_pr_safety"]
    assert job["stage"] == "test"
    assert "script" in job
    assert any("loam pr-safety gate" in s for s in job["script"])
    assert "rules" in job


def test_gitlab_ci_preserves_existing_content_with_block(tmp_path: Path) -> None:
    """Re-install with existing loam block in larger .gitlab-ci.yml
    refreshes IN-PLACE and preserves surrounding non-loam content."""
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    target = repo / ".gitlab-ci.yml"

    # First install creates clean file.
    install_ci_gitlab_ci(repo, workspace_root=ws)

    # Add existing non-loam content around the block.
    existing = target.read_text(encoding="utf-8")
    augmented = (
        "# Pre-existing user content above\n"
        "user_job:\n"
        "  stage: build\n"
        "  script:\n"
        "    - echo 'user job'\n"
        "\n"
        + existing
        + "\n# Pre-existing user content below\n"
        "another_user_job:\n"
        "  stage: test\n"
        "  script:\n"
        "    - echo 'another'\n"
    )
    target.write_text(augmented, encoding="utf-8")

    # Re-install should refresh in place WITHOUT mucking up surrounds
    # (or noop if version match).
    r = install_ci_gitlab_ci(repo, workspace_root=ws)
    assert r.action in ("noop", "refreshed")
    final = target.read_text(encoding="utf-8")
    assert "user_job:" in final
    assert "another_user_job:" in final
    assert "loam_pr_safety:" in final


def test_gitlab_ci_halts_on_conflict_no_block(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    target = repo / ".gitlab-ci.yml"
    target.write_text(
        "stages:\n  - build\nuser_job:\n  stage: build\n  script:\n    - true\n",
        encoding="utf-8",
    )

    with pytest.raises(InstallConflictError):
        install_ci_gitlab_ci(repo, workspace_root=ws)


def test_gitlab_ci_force_appends(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    target = repo / ".gitlab-ci.yml"
    target.write_text(
        "stages:\n  - build\nuser_job:\n  stage: build\n  script:\n    - true\n",
        encoding="utf-8",
    )

    result = install_ci_gitlab_ci(repo, workspace_root=ws, force=True)
    assert result.action == "force-replaced"
    final = target.read_text(encoding="utf-8")
    assert "loam-pr-safety:managed:start:" in final


def test_gitlab_ci_idempotent(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    r1 = install_ci_gitlab_ci(repo, workspace_root=ws)
    r2 = install_ci_gitlab_ci(repo, workspace_root=ws)
    assert r1.action == "created"
    assert r2.action == "noop"
