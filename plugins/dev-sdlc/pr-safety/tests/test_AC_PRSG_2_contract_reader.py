"""AC.PRSG.2 — banded-contract reader API."""

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


def test_read_contract_against_synthetic_fixture(workspace_with_contract):
    """read_contract returns a typed BandedContract with 3 banded ACs."""
    workspace_root, repo_id = workspace_with_contract
    contract = read_contract(repo_id, workspace_root)
    assert isinstance(contract, BandedContract)
    assert contract.extraction_id == "synthetic-prsafety-v0-1-9-c1"
    assert len(contract.acs) == 3
    bands = [ac.confidence for ac in contract.acs]
    assert ConfidenceBand.VERIFIED in bands
    assert ConfidenceBand.PLAUSIBLE in bands
    assert ConfidenceBand.HYPOTHESISED in bands
    assert contract.repo_sha == "abc1234567890def"  # from VERIFIED AC.
    assert contract.override_count == 0


def test_read_contract_raises_on_missing(tmp_workspace):
    """ContractMissingError raised when sidecar absent."""
    with pytest.raises(ContractMissingError):
        read_contract("nonexistent-repo-12345678", tmp_workspace)


def test_read_contract_raises_on_malformed_yaml(
    tmp_workspace, synthetic_contract_dict
):
    """Per-band evidence rule violation raises ContractMalformedError."""
    repo_id = "malformed-12345678"
    ext_dir = tmp_workspace / ".loam" / "extractions" / repo_id
    ext_dir.mkdir(parents=True)
    bad = synthetic_contract_dict.copy()
    # Take the VERIFIED AC and strip its repo_sha — should fail
    # AC.BANDS.2 evidence-rule.
    bad_acs = [dict(ac) for ac in bad["acs"]]
    for ac in bad_acs:
        if ac["ac_id"] == "AC.SYNTH.1":
            ac["evidence"] = dict(ac["evidence"])
            ac["evidence"]["repo_sha"] = None
    bad["acs"] = bad_acs
    (ext_dir / "contract-draft.yaml").write_text(
        yaml.safe_dump(bad), encoding="utf-8"
    )
    with pytest.raises(ContractMalformedError):
        read_contract(repo_id, tmp_workspace)


def test_read_contract_applies_overlay(workspace_with_contract):
    """Approved-override overlay is composed over the sidecar."""
    workspace_root, repo_id = workspace_with_contract
    overlays_dir = (
        workspace_root
        / ".loam"
        / "pr-safety"
        / "contract-overrides"
        / repo_id
    )
    overlays_dir.mkdir(parents=True)
    overlay = {
        "schema_version": 1,
        "kind": "replace_verified",
        "original_ac_id": "AC.SYNTH.1",
        "replacement_ac": {
            "ac_id": "AC.SYNTH.1",
            "text": "Password length validation now opt-in (overridden).",
            "confidence": "PLAUSIBLE",
            "evidence": {
                "kind": "source",
                "citations": ["app/auth.py:42-58"],
                "repo_sha": None,
                "rationale": None,
            },
            "backing_files": ["app/auth.py"],
        },
        "rationale": "Auth flow refactor — password rule moved to opt-in.",
        "owner": "Test User <test@example.com>",
        "commit_sha": "deadbeef",
        "repo_sha": "abc1234",
        "applied_at": "2026-05-04T13:00:00+00:00",
    }
    (overlays_dir / "override-1.yaml").write_text(
        yaml.safe_dump(overlay), encoding="utf-8"
    )
    contract = read_contract(repo_id, workspace_root)
    assert contract.override_count == 1
    # The original VERIFIED AC.SYNTH.1 is now PLAUSIBLE.
    ac_synth_1 = next(ac for ac in contract.acs if ac.ac_id == "AC.SYNTH.1")
    assert ac_synth_1.confidence is ConfidenceBand.PLAUSIBLE


def test_read_contract_promote_novel_overlay(workspace_with_contract):
    """promote_novel overlay extends the contract with a new AC."""
    workspace_root, repo_id = workspace_with_contract
    overlays_dir = (
        workspace_root
        / ".loam"
        / "pr-safety"
        / "contract-overrides"
        / repo_id
    )
    overlays_dir.mkdir(parents=True)
    overlay = {
        "schema_version": 1,
        "kind": "promote_novel",
        "replacement_ac": {
            "ac_id": "AC.NOVEL.1",
            "text": "New feature: user nicknames.",
            "confidence": "PLAUSIBLE",
            "evidence": {
                "kind": "source",
                "citations": ["app/users.py:100-120"],
                "repo_sha": None,
                "rationale": None,
            },
            "backing_files": ["app/users.py"],
        },
        "rationale": "Add nicknames as a new feature.",
        "owner": "Test User <test@example.com>",
        "commit_sha": "deadbeef",
        "repo_sha": "abc1234",
        "applied_at": "2026-05-04T13:00:00+00:00",
    }
    (overlays_dir / "override-1.yaml").write_text(
        yaml.safe_dump(overlay), encoding="utf-8"
    )
    contract = read_contract(repo_id, workspace_root)
    assert contract.override_count == 1
    assert len(contract.acs) == 4
    novel_ac = next(ac for ac in contract.acs if ac.ac_id == "AC.NOVEL.1")
    assert novel_ac.confidence is ConfidenceBand.PLAUSIBLE
