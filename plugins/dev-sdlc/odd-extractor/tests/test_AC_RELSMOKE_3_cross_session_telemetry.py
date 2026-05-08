"""AC.RELSMOKE.3 — Cross-session SOFT smoke + telemetry-floor.

Per v0.2.3 Cycle 3 sub-plan-doc §3 AC.RELSMOKE.3.

Session A extracts + ratifies + caches; Session B reads cached state +
gate fires + watch detects drift. Audit entries across cycles
observable; SOC-2 floor preserved.
"""

from __future__ import annotations


import yaml

from loam_odd_extractor.incremental import run_incremental
from loam_odd_extractor.observability import list_entries as oe_list_entries
from loam_odd_extractor.state import compute_repo_id, extraction_dir

from _relsmoke_helpers import (
    setup_repo_from_fixture as _setup_repo_from_fixture,
    write_canned_objectives_and_map as _write_canned_objectives_and_map,
)


def test_session_a_caches_state_session_b_reads_it(tmp_path):
    """Session B reads cached objectives.yaml + backing-map.yaml + audit-log."""
    repo, repo_sha = _setup_repo_from_fixture(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    repo_id = compute_repo_id(repo)

    # --- Session A: write objectives + backing-map + run watch.
    _write_canned_objectives_and_map(workspace, repo_id, repo_sha)
    run_incremental(
        repo_path=repo,
        workspace_root=workspace,
        pm_runtime=None,
        dry_run=True,
    )

    # --- Session B (post-/clear): re-read state, no re-extraction.
    from loam_pr_safety import read_contract

    contract = read_contract(repo_id, workspace)
    assert len(contract.objectives) == 3
    # Backing-map round-trips.
    assert contract.backing_map.objective_count == 3
    # Audit-log entries from Session A still present.
    ext_dir = extraction_dir(workspace, repo_id)
    entries = oe_list_entries(ext_dir)
    assert len(entries) >= 1


def test_telemetry_floor_audit_event_kinds_observable(tmp_path):
    """Audit-log carries multiple cross-cycle event_kinds."""
    repo, repo_sha = _setup_repo_from_fixture(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    repo_id = compute_repo_id(repo)
    _write_canned_objectives_and_map(workspace, repo_id, repo_sha)

    run_incremental(
        repo_path=repo,
        workspace_root=workspace,
        pm_runtime=None,
        dry_run=True,
    )

    ext_dir = extraction_dir(workspace, repo_id)
    entries = oe_list_entries(ext_dir)
    event_kinds: set[str] = set()
    for entry_path in entries:
        data = yaml.safe_load(entry_path.read_text())
        event_kinds.add(data.get("event_kind", ""))
    # Cycle 3 incremental run records multiple kinds.
    assert "incremental_watch_run" in event_kinds
    assert "incremental_classification" in event_kinds
    assert "incremental_run_complete" in event_kinds  # AC.WATCHOBJ.5
    # incremental_proposal only fires when proposals exist; we don't
    # require it for the no-drift case (verified separately in the
    # smoke test that introduces drift).


def test_pr_safety_audit_log_records_objective_altitude_telemetry(tmp_path):
    """PR-safety audit-log entries carry objective-altitude payload."""
    from pathlib import Path as _P

    from loam_pr_safety import (
        read_contract,
        classify,
        decide,
        Diff,
        DiffEntry,
        Hunk,
    )
    from loam_pr_safety.audit import write_audit_entry, list_entries as pr_list

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
                file_path=_P("src/routes/users.js"),
                hunks=[
                    Hunk(old_start=5, old_lines=2, new_start=5, new_lines=2)
                ],
            )
        ],
    )
    decision = decide(
        classify(diff, contract),
        safety_profile="dev",
        extraction_id=contract.extraction_id,
    )

    write_audit_entry(
        workspace,
        event_kind="gate_decision",
        repo_id=repo_id,
        repo_sha=contract.repo_sha or "",
        decision=decision.action.value,
        requires_ratification=decision.requires_ratification,
        objective_ids_touched=[
            t.objective.objective_id for t in decision.touched_objectives
        ],
        objective_bands_touched={
            t.objective.objective_id: t.objective.confidence.value
            for t in decision.touched_objectives
        },
        extraction_id=contract.extraction_id,
        reason=decision.reason,
    )

    entries = pr_list(workspace)
    assert len(entries) >= 1
    last = yaml.safe_load(entries[-1].read_text())
    assert last["objective_ids_touched"] == ["O.users.1"]
    assert last["objective_bands_touched"] == {"O.users.1": "VERIFIED"}
    assert last["extraction_id"] == contract.extraction_id
