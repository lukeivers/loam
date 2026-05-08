"""AC.RELSMOKE.1 — Cold-state SOFT smoke on canonical jsts-playwright-app fixture.

Per v0.2.3 Cycle 3 sub-plan-doc §3 AC.RELSMOKE.1.

Stubbed Anthropic + canned objectives + canned backing-map. Verifies
end-to-end pipeline shape: extract → ratify → gate → watch with
typed-output assertions at each step.

Per master plan §5 — soft because fixture-driven (not a real LLM
pass against a real codebase). HARD smoke against rd-automation
deferred to v0.2.5.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor.bands import ConfidenceBand
from loam_odd_extractor.incremental import run_incremental
from loam_odd_extractor.spec import (
    Objective,
)
from loam_odd_extractor.state import compute_repo_id, extraction_dir


from _relsmoke_helpers import (
    setup_repo_from_fixture as _setup_repo_from_fixture,
    write_canned_objectives_and_map as _write_canned_objectives_and_map,
)


def test_cold_state_extract_yields_objectives_yaml_plus_backing_map(
    tmp_path,
):
    """Cold-state fixture extraction produces objectives.yaml + backing-map.yaml."""
    repo, repo_sha = _setup_repo_from_fixture(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    repo_id = compute_repo_id(repo)
    _write_canned_objectives_and_map(workspace, repo_id, repo_sha)
    ext_dir = extraction_dir(workspace, repo_id)

    # Files exist.
    assert (ext_dir / "objectives.yaml").exists()
    assert (ext_dir / "backing-map.yaml").exists()

    # Both load + validate.
    objs_data = yaml.safe_load(
        (ext_dir / "objectives.yaml").read_text(encoding="utf-8")
    )
    objectives = [Objective.model_validate(o) for o in objs_data["objectives"]]
    assert len(objectives) == 3
    bands = {o.confidence for o in objectives}
    assert bands == {
        ConfidenceBand.VERIFIED,
        ConfidenceBand.PLAUSIBLE,
        ConfidenceBand.HYPOTHESISED,
    }


def test_cold_state_pr_safety_reads_objectives_correctly(tmp_path):
    """PR-safety read_contract loads typed BandedContract from cold extraction."""
    from loam_pr_safety import read_contract, BandedContract

    repo, repo_sha = _setup_repo_from_fixture(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    repo_id = compute_repo_id(repo)
    _write_canned_objectives_and_map(workspace, repo_id, repo_sha)

    contract = read_contract(repo_id, workspace)
    assert isinstance(contract, BandedContract)
    assert len(contract.objectives) == 3
    assert contract.repo_sha == repo_sha


def test_cold_state_full_pipeline_extract_gate_watch(tmp_path):
    """End-to-end shape: extract → gate (HARD_BLOCK on V-touched) → watch."""
    from loam_pr_safety import (
        read_contract,
        classify,
        decide,
        GateAction,
        Diff,
        DiffEntry,
        Hunk,
    )

    repo, repo_sha = _setup_repo_from_fixture(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    repo_id = compute_repo_id(repo)
    _write_canned_objectives_and_map(workspace, repo_id, repo_sha)

    # Step 1: load contract (extract output).
    contract = read_contract(repo_id, workspace)

    # Step 2: synthesize diff overlapping VERIFIED objective backing
    # (src/routes/users.js:1-20).
    diff = Diff(
        from_sha="prior",
        to_sha="HEAD",
        entries=[
            DiffEntry(
                file_path=Path("src/routes/users.js"),
                hunks=[
                    Hunk(old_start=10, old_lines=3, new_start=10, new_lines=3)
                ],
            )
        ],
    )

    # Step 3: gate fires HARD_BLOCK; reason carries objective text.
    classification = classify(diff, contract)
    decision = decide(
        classification,
        safety_profile="dev",
        extraction_id=contract.extraction_id,
    )
    assert decision.action is GateAction.HARD_BLOCK
    assert "O.users.1" in decision.reason
    assert "user records" in decision.reason.lower()

    # Step 4: watch on no-changes → still_current.
    result = run_incremental(
        repo_path=repo,
        workspace_root=workspace,
        pm_runtime=None,
        dry_run=True,
    )
    # No drift since the contract's repo_sha matches HEAD.
    assert result.classification.still_current_count == 3
