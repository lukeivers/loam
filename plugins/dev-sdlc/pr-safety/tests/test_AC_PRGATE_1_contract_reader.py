"""AC.PRGATE.1 — Contract reader consumes objectives.yaml + backing-map.yaml.

Per v0.2.3 Cycle 3 sub-plan-doc §3 AC.PRGATE.1.

Read Cycle 1+2 outputs directly. Legacy contract-draft.yaml.acs:
retired per master plan §6.2. v0.1.9 BandedAC altitude is not
supported — extraction must run Cycle 1 + Cycle 2 first.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam_odd_extractor.bands import ConfidenceBand
from loam_pr_safety import (
    BandedContract,
    ContractMalformedError,
    ContractMissingError,
    read_contract,
)


def test_read_contract_returns_objectives_at_altitude(
    workspace_with_objectives,
):
    """read_contract returns BandedContract carrying typed Objectives + BackingMap."""
    workspace_root, repo_id = workspace_with_objectives
    contract = read_contract(repo_id, workspace_root)
    assert isinstance(contract, BandedContract)
    assert contract.extraction_id == "synth-cycle-3-test"
    assert len(contract.objectives) == 3
    bands = [o.confidence for o in contract.objectives]
    assert ConfidenceBand.VERIFIED in bands
    assert ConfidenceBand.PLAUSIBLE in bands
    assert ConfidenceBand.HYPOTHESISED in bands
    # repo_sha picked up from VERIFIED objective.
    assert contract.repo_sha == "abc1234567890def"
    assert contract.override_count == 0


def test_read_contract_carries_backing_map(workspace_with_objectives):
    """BandedContract.backing_map is the typed Cycle 2 BackingMap."""
    workspace_root, repo_id = workspace_with_objectives
    contract = read_contract(repo_id, workspace_root)
    bm = contract.backing_map
    assert bm.objective_count == 3
    assert len(bm.entries) == 3
    auth_entry = next(
        e for e in bm.entries if e.objective_id == "O.auth.1"
    )
    assert len(auth_entry.evidence_rows) == 2
    paths = {r.path for r in auth_entry.evidence_rows}
    assert "tests/test_auth.py" in paths
    assert "app/auth.py" in paths


def test_read_contract_raises_on_missing_objectives(tmp_workspace):
    """ContractMissingError raised when objectives.yaml absent."""
    with pytest.raises(ContractMissingError):
        read_contract("nonexistent-repo-12345678", tmp_workspace)


def test_read_contract_raises_on_missing_backing_map(
    tmp_workspace, synthetic_objectives_dict
):
    """ContractMissingError raised when backing-map.yaml absent."""
    repo_id = "objectives-only-12345678"
    ext_dir = tmp_workspace / ".loam" / "extractions" / repo_id
    ext_dir.mkdir(parents=True)
    (ext_dir / "objectives.yaml").write_text(
        yaml.safe_dump(synthetic_objectives_dict, sort_keys=False),
        encoding="utf-8",
    )
    with pytest.raises(ContractMissingError):
        read_contract(repo_id, tmp_workspace)


def test_read_contract_raises_on_malformed_objective(
    tmp_workspace,
    synthetic_objectives_dict,
    synthetic_backing_map_dict,
):
    """Per-band evidence rule violation raises ContractMalformedError."""
    repo_id = "malformed-obj-12345678"
    ext_dir = tmp_workspace / ".loam" / "extractions" / repo_id
    ext_dir.mkdir(parents=True)
    bad = dict(synthetic_objectives_dict)
    bad_objs = [dict(o) for o in bad["objectives"]]
    # Strip evidence.repo_sha from the VERIFIED objective — should
    # fail per-band invariant.
    for o in bad_objs:
        if o["objective_id"] == "O.auth.1":
            o["evidence"] = dict(o["evidence"])
            o["evidence"]["repo_sha"] = None
    bad["objectives"] = bad_objs
    (ext_dir / "objectives.yaml").write_text(
        yaml.safe_dump(bad, sort_keys=False), encoding="utf-8"
    )
    (ext_dir / "backing-map.yaml").write_text(
        yaml.safe_dump(synthetic_backing_map_dict, sort_keys=False),
        encoding="utf-8",
    )
    with pytest.raises(ContractMalformedError):
        read_contract(repo_id, tmp_workspace)


def test_read_contract_applies_objective_overlay(workspace_with_objectives):
    """Overlay (kind=replace_verified_objective) is composed."""
    workspace_root, repo_id = workspace_with_objectives
    overlays_dir = (
        workspace_root
        / ".loam"
        / "pr-safety"
        / "contract-overrides"
        / repo_id
    )
    overlays_dir.mkdir(parents=True)
    overlay = {
        "schema_version": 2,
        "kind": "replace_verified_objective",
        "original_objective_id": "O.auth.1",
        "replacement_objective": {
            "objective_id": "O.auth.1",
            "text": (
                "Operators authenticate with password validation now "
                "deferred to a managed identity provider."
            ),
            "confidence": "PLAUSIBLE",
            "domain": "auth",
            "evidence": {
                "readme_excerpts": [
                    "Auth deferred to identity provider per ADR-007."
                ],
                "design_doc_refs": [],
                "test_name_refs": [],
                "survey_line_refs": [],
                "code_pattern_refs": [],
                "repo_sha": None,
                "rationale": "VERIFIED→PLAUSIBLE via override",
            },
        },
        "rationale": "Test override",
        "owner": "test@example.com",
        "commit_sha": "deadbeef",
        "repo_sha": "abc1234567890def",
        "applied_at": "2026-05-04T00:00:00+00:00",
    }
    (overlays_dir / "override-1.yaml").write_text(
        yaml.safe_dump(overlay, sort_keys=False), encoding="utf-8"
    )
    contract = read_contract(repo_id, workspace_root)
    assert contract.override_count == 1
    auth_objective = next(
        o for o in contract.objectives if o.objective_id == "O.auth.1"
    )
    assert auth_objective.confidence is ConfidenceBand.PLAUSIBLE


def test_read_contract_migrates_v1_overlay(workspace_with_objectives):
    """v0.1.9-shape overlay is auto-migrated with .v1.bak preserved."""
    workspace_root, repo_id = workspace_with_objectives
    overlays_dir = (
        workspace_root
        / ".loam"
        / "pr-safety"
        / "contract-overrides"
        / repo_id
    )
    overlays_dir.mkdir(parents=True)
    legacy_overlay = {
        "schema_version": 1,
        "kind": "replace_verified",  # v0.1.9 shape
        "original_ac_id": "AC.AUTH.1",
        "replacement_ac": {
            "ac_id": "AC.AUTH.1",
            "text": "Legacy AC text",
            "confidence": "PLAUSIBLE",
            "evidence": {
                "kind": "source",
                "citations": ["app/auth.py:10-25"],
                "repo_sha": None,
                "rationale": None,
            },
            "backing_files": ["app/auth.py"],
        },
        "rationale": "Legacy override",
        "owner": "legacy@example.com",
        "commit_sha": "0123abcd",
        "repo_sha": "abc1234567890def",
        "applied_at": "2026-04-01T00:00:00+00:00",
    }
    overlay_path = overlays_dir / "override-1.yaml"
    overlay_path.write_text(
        yaml.safe_dump(legacy_overlay, sort_keys=False), encoding="utf-8"
    )

    contract = read_contract(repo_id, workspace_root)
    # v0.1.9 overlay migrates to audit_only — no objective mutation.
    assert contract.override_count == 1
    # Original overlay backed up to .v1.bak.
    backup_path = overlay_path.with_suffix(overlay_path.suffix + ".v1.bak")
    assert backup_path.exists()
    backup_content = yaml.safe_load(backup_path.read_text())
    assert backup_content["kind"] == "replace_verified"
    # Migrated overlay carries audit_only kind.
    migrated = yaml.safe_load(overlay_path.read_text())
    assert migrated["kind"] == "audit_only"
    assert migrated["legacy_kind"] == "replace_verified"
