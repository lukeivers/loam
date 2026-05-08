"""AC.RELSMOKE.2 — Idempotent re-run smoke.

Per v0.2.3 Cycle 3 sub-plan-doc §3 AC.RELSMOKE.2.

Re-run extract / gate / watch on unchanged repo → same outputs
(modulo timestamps); identical GateDecision; empty watch proposals.
"""

from __future__ import annotations

from pathlib import Path


from loam_odd_extractor.incremental import run_incremental
from loam_odd_extractor.state import compute_repo_id

# Reuse setup helpers from RELSMOKE.1.
from _relsmoke_helpers import (
    setup_repo_from_fixture as _setup_repo_from_fixture,
    write_canned_objectives_and_map as _write_canned_objectives_and_map,
)


def test_idempotent_watch_re_run(tmp_path):
    """Two run_incremental calls on unchanged repo → same classification counts."""
    repo, repo_sha = _setup_repo_from_fixture(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    repo_id = compute_repo_id(repo)
    _write_canned_objectives_and_map(workspace, repo_id, repo_sha)

    result1 = run_incremental(
        repo_path=repo, workspace_root=workspace, pm_runtime=None, dry_run=True
    )
    result2 = run_incremental(
        repo_path=repo, workspace_root=workspace, pm_runtime=None, dry_run=True
    )
    assert (
        result1.classification.still_current_count
        == result2.classification.still_current_count
    )
    assert (
        result1.classification.out_of_date_count
        == result2.classification.out_of_date_count
    )
    assert (
        result1.classification.orphaned_count
        == result2.classification.orphaned_count
    )
    # Empty watch proposals on unchanged repo.
    assert result1.proposal_set.proposal_count == 0
    assert result2.proposal_set.proposal_count == 0


def test_idempotent_gate_decision(tmp_path):
    """Two gate calls on unchanged contract + diff → identical action."""
    from loam_pr_safety import (
        read_contract,
        classify,
        decide,
        Diff,
        DiffEntry,
        Hunk,
    )

    repo, repo_sha = _setup_repo_from_fixture(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    repo_id = compute_repo_id(repo)
    _write_canned_objectives_and_map(workspace, repo_id, repo_sha)

    contract = read_contract(repo_id, workspace)
    diff = Diff(
        from_sha="p",
        to_sha="HEAD",
        entries=[
            DiffEntry(
                file_path=Path("src/routes/users.js"),
                hunks=[
                    Hunk(old_start=5, old_lines=2, new_start=5, new_lines=2)
                ],
            )
        ],
    )
    d1 = decide(classify(diff, contract), safety_profile="dev", extraction_id="ext")
    d2 = decide(classify(diff, contract), safety_profile="dev", extraction_id="ext")
    assert d1.action is d2.action
    assert (
        [t.objective.objective_id for t in d1.touched_objectives]
        == [t.objective.objective_id for t in d2.touched_objectives]
    )
