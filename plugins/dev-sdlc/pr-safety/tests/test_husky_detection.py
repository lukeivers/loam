"""Husky detection heuristic — Surface #4."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from loam_pr_safety.installers import detect_husky, install_pre_commit


def _bare_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    return repo


def test_detect_husky_v6_runner_file_present(tmp_path: Path) -> None:
    repo = _bare_repo(tmp_path)
    (repo / ".husky" / "_").mkdir(parents=True)
    (repo / ".husky" / "_" / "husky.sh").write_text(
        "# husky runner\n", encoding="utf-8"
    )
    assert detect_husky(repo) is True


def test_detect_husky_v45_package_json_key(tmp_path: Path) -> None:
    repo = _bare_repo(tmp_path)
    (repo / "package.json").write_text(
        json.dumps({"name": "x", "husky": {"hooks": {}}}),
        encoding="utf-8",
    )
    assert detect_husky(repo) is True


def test_detect_husky_no_signals(tmp_path: Path) -> None:
    repo = _bare_repo(tmp_path)
    (repo / "package.json").write_text(
        json.dumps({"name": "x", "version": "1.0.0"}),
        encoding="utf-8",
    )
    assert detect_husky(repo) is False


def test_detect_husky_no_package_json_no_husky_dir(tmp_path: Path) -> None:
    repo = _bare_repo(tmp_path)
    assert detect_husky(repo) is False


def test_detect_husky_husky_dir_exists_but_no_runner(tmp_path: Path) -> None:
    """A `.husky/` dir with hooks but no `_/husky.sh` is NOT detected
    as husky-managed (could be a manually-organized hooks dir)."""
    repo = _bare_repo(tmp_path)
    (repo / ".husky").mkdir()
    (repo / ".husky" / "pre-commit").write_text(
        "#!/bin/sh\n", encoding="utf-8"
    )
    assert detect_husky(repo) is False


def test_detect_husky_malformed_package_json(tmp_path: Path) -> None:
    repo = _bare_repo(tmp_path)
    (repo / "package.json").write_text(
        "not valid json{}", encoding="utf-8"
    )
    assert detect_husky(repo) is False


def test_install_routes_to_husky_when_detected(
    repo_with_husky: Path, tmp_path: Path
) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / ".loam").mkdir()
    result = install_pre_commit(repo_with_husky, workspace_root=ws)
    assert result.husky_routed is True
    assert result.target_path.parent.name == ".husky"


def test_install_routes_to_husky_pkgjson_variant(
    repo_with_husky_via_pkgjson: Path, tmp_path: Path
) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / ".loam").mkdir()
    result = install_pre_commit(
        repo_with_husky_via_pkgjson, workspace_root=ws
    )
    assert result.husky_routed is True
