"""AC.WATCHOBJ.4 — incremental.py engine reads objectives.yaml + backing-map.yaml.

Per v0.2.3 Cycle 3 sub-plan-doc §3 AC.WATCHOBJ.4.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from loam_odd_extractor.incremental import (
    ContractNotFoundError,
    IncrementalRunResult,
    run_incremental,
)
from loam_odd_extractor.state import compute_repo_id, extraction_dir


def _git_init_with_file(repo_path: Path, file_content: str = "x = 1\n") -> str:
    repo_path.mkdir(exist_ok=True)
    subprocess.run(["git", "-C", str(repo_path), "init", "-q"], check=True)
    subprocess.run(
        ["git", "-C", str(repo_path), "config", "user.email", "t@e.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_path), "config", "user.name", "T"],
        check=True,
    )
    (repo_path / "auth.py").write_text(file_content)
    subprocess.run(["git", "-C", str(repo_path), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(repo_path), "commit", "-q", "-m", "init"],
        check=True,
    )
    proc = subprocess.run(
        ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def _write_objectives_and_backing_map(
    workspace_root: Path, repo_id: str, repo_sha: str
) -> None:
    ext_dir = extraction_dir(workspace_root, repo_id)
    ext_dir.mkdir(parents=True, exist_ok=True)
    objs = {
        "schema_version": 1,
        "extraction_id": repo_id,
        "repo_path": "/tmp/repo",
        "created_at": "2026-05-04T00:00:00+00:00",
        "objectives": [
            {
                "objective_id": "O.auth.1",
                "text": "Operators authenticate with password length validation enforced.",
                "confidence": "VERIFIED",
                "domain": "auth",
                "evidence": {
                    "readme_excerpts": ["Auth supports password length"],
                    "design_doc_refs": [],
                    "test_name_refs": ["tests/test_auth.py::test_pl"],
                    "survey_line_refs": [],
                    "code_pattern_refs": [],
                    "repo_sha": repo_sha,
                    "rationale": None,
                },
            }
        ],
        "constraints": [],
        "capabilities": [],
    }
    bm = {
        "schema_version": 1,
        "extraction_id": repo_id,
        "created_at": "2026-05-04T00:00:00+00:00",
        "model_id": "stub",
        "cost_actual_cents": 0.0,
        "total_evidence_rows": 1,
        "objective_count": 1,
        "unmatched_objective_ids": [],
        "entries": [
            {
                "objective_id": "O.auth.1",
                "match_rationale": "test",
                "evidence_rows": [
                    {
                        "evidence_row_id": "route:auth.py:1",
                        "kind": "route",
                        "path": "auth.py",
                        "line_range": [1, 1],
                        "symbol_name": "x",
                        "language": "python",
                        "confidence": "STRONG",
                    }
                ],
            }
        ],
        "orphan_rows": [],
    }
    (ext_dir / "objectives.yaml").write_text(
        yaml.safe_dump(objs, sort_keys=False), encoding="utf-8"
    )
    (ext_dir / "backing-map.yaml").write_text(
        yaml.safe_dump(bm, sort_keys=False), encoding="utf-8"
    )


def test_run_incremental_returns_objective_altitude_classification(tmp_path):
    """run_incremental returns IncrementalRunResult with objective-altitude classification."""
    repo = tmp_path / "repo"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    sha = _git_init_with_file(repo)
    repo_id = compute_repo_id(repo)
    _write_objectives_and_backing_map(workspace, repo_id, sha)

    result = run_incremental(
        repo_path=repo,
        workspace_root=workspace,
        pm_runtime=None,
        dry_run=True,
    )
    assert isinstance(result, IncrementalRunResult)
    # No drift since SHA matches.
    assert result.classification.still_current_count == 1


def test_run_incremental_raises_on_missing_objectives_yaml(tmp_path):
    """ContractNotFoundError when objectives.yaml absent."""
    repo = tmp_path / "repo"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _git_init_with_file(repo)
    with pytest.raises(ContractNotFoundError):
        run_incremental(
            repo_path=repo,
            workspace_root=workspace,
            pm_runtime=None,
            dry_run=True,
        )


def test_run_incremental_raises_on_missing_backing_map(tmp_path):
    """ContractNotFoundError when objectives.yaml present but backing-map.yaml absent."""
    repo = tmp_path / "repo"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    sha = _git_init_with_file(repo)
    repo_id = compute_repo_id(repo)
    ext_dir = extraction_dir(workspace, repo_id)
    ext_dir.mkdir(parents=True)
    objs = {
        "schema_version": 1,
        "extraction_id": repo_id,
        "repo_path": "/tmp/repo",
        "created_at": "2026-05-04T00:00:00+00:00",
        "objectives": [],
        "constraints": [],
        "capabilities": [],
    }
    (ext_dir / "objectives.yaml").write_text(
        yaml.safe_dump(objs, sort_keys=False), encoding="utf-8"
    )
    with pytest.raises(ContractNotFoundError):
        run_incremental(
            repo_path=repo,
            workspace_root=workspace,
            pm_runtime=None,
            dry_run=True,
        )


def test_run_incremental_detects_line_drift(tmp_path):
    """File modified after prior_sha → out_of_date."""
    repo = tmp_path / "repo"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    prior_sha = _git_init_with_file(repo, "x = 1\n")
    repo_id = compute_repo_id(repo)
    _write_objectives_and_backing_map(workspace, repo_id, prior_sha)

    # Modify the file → new commit.
    (repo / "auth.py").write_text("x = 999  # changed\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", "update"],
        check=True,
    )

    result = run_incremental(
        repo_path=repo,
        workspace_root=workspace,
        pm_runtime=None,
        dry_run=True,
    )
    assert result.classification.out_of_date_count == 1
