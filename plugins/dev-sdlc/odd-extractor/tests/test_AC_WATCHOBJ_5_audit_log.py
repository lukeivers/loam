"""AC.WATCHOBJ.5 — Audit-log per incremental run at objective altitude.

Per v0.2.3 Cycle 3 sub-plan-doc §3 AC.WATCHOBJ.5.

Additive payload (no schema-version bump); SOC-2 floor preserved.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from loam_odd_extractor.incremental import run_incremental
from loam_odd_extractor.observability import list_entries
from loam_odd_extractor.state import compute_repo_id, extraction_dir


def _git_init_with_file(repo_path: Path) -> str:
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
    (repo_path / "auth.py").write_text("x = 1\n")
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


def _write_seed(workspace: Path, repo_id: str, sha: str) -> None:
    ext = extraction_dir(workspace, repo_id)
    ext.mkdir(parents=True, exist_ok=True)
    objs = {
        "schema_version": 1,
        "extraction_id": repo_id,
        "repo_path": "/tmp/r",
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
                    "test_name_refs": ["tests/test_auth.py::test"],
                    "survey_line_refs": [],
                    "code_pattern_refs": [],
                    "repo_sha": sha,
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
                    }
                ],
            }
        ],
        "orphan_rows": [],
    }
    (ext / "objectives.yaml").write_text(
        yaml.safe_dump(objs, sort_keys=False), encoding="utf-8"
    )
    (ext / "backing-map.yaml").write_text(
        yaml.safe_dump(bm, sort_keys=False), encoding="utf-8"
    )


def test_incremental_run_complete_audit_entry_carries_objective_fields(
    tmp_path,
):
    """incremental_run_complete event_kind has objective-altitude fields."""
    repo = tmp_path / "repo"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    sha = _git_init_with_file(repo)
    repo_id = compute_repo_id(repo)
    _write_seed(workspace, repo_id, sha)

    result = run_incremental(
        repo_path=repo,
        workspace_root=workspace,
        pm_runtime=None,
        dry_run=True,
    )
    ext_dir = extraction_dir(workspace, repo_id)
    entries = list_entries(ext_dir)
    # Find the incremental_run_complete entry.
    completes = []
    for entry_path in entries:
        data = yaml.safe_load(entry_path.read_text())
        if data.get("event_kind") == "incremental_run_complete":
            completes.append(data)
    assert len(completes) >= 1
    notes = completes[-1]["notes"]
    assert "still_current_objective_count=" in notes
    assert "out_of_date_objective_count=" in notes
    assert "orphaned_objective_count=" in notes
    assert "backing_map_staleness_detected=" in notes
    assert "domain_batches_enqueued=" in notes
    assert "objectives_by_domain=" in notes


def test_audit_schema_version_unchanged(tmp_path):
    """No schema_version bump (additive payload only)."""
    repo = tmp_path / "repo"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    sha = _git_init_with_file(repo)
    repo_id = compute_repo_id(repo)
    _write_seed(workspace, repo_id, sha)

    run_incremental(
        repo_path=repo,
        workspace_root=workspace,
        pm_runtime=None,
        dry_run=True,
    )
    ext_dir = extraction_dir(workspace, repo_id)
    entries = list_entries(ext_dir)
    for entry in entries:
        data = yaml.safe_load(entry.read_text())
        assert data["schema_version"] == 1
