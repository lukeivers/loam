"""AC.PRGATE.4 — Override flow at objective altitude.

Per v0.2.3 Cycle 3 sub-plan-doc §3 AC.PRGATE.4.
"""

from __future__ import annotations


import yaml

from loam_odd_extractor.bands import ConfidenceBand
from loam_odd_extractor.spec import (
    EvidenceRowRef,
    Objective,
    ObjectiveEvidence,
)

from loam_pr_safety import (
    ClassificationResult,
    Hunk,
    OverrideRequest,
    TouchedObjective,
    apply_override,
    recognise_override,
)
from loam_pr_safety.override import (
    _proposed_objectives_from_classification,
    build_override_request,
)


def _verified_objective() -> Objective:
    return Objective(
        objective_id="O.auth.1",
        text="Operators authenticate with password length validation enforced.",
        confidence=ConfidenceBand.VERIFIED,
        domain="auth",
        evidence=ObjectiveEvidence(
            readme_excerpts=["Auth supports password length"],
            test_name_refs=["tests/test_auth.py::test_password_length"],
            repo_sha="abc1234567890def",
        ),
    )


def _make_classification_with_verified() -> ClassificationResult:
    obj = _verified_objective()
    return ClassificationResult(
        touched_objectives=[
            TouchedObjective(
                objective=obj,
                touch_kind="evidence_line",
                touched_evidence_rows=[
                    EvidenceRowRef(
                        evidence_row_id="route:app/auth.py:10-25",
                        kind="route",
                        path="app/auth.py",
                        line_range=[10, 25],
                    )
                ],
                touched_hunks=[
                    Hunk(old_start=15, old_lines=3, new_start=15, new_lines=3)
                ],
            )
        ]
    )


def test_recognise_override_trailer():
    """Loam-Override trailer + flag → recognised with rationale."""
    msg = "fix(auth): tighten password rule\n\nLoam-Override: critical security fix\n"
    recognised, rationale = recognise_override(msg, override_flag=True)
    assert recognised is True
    assert rationale == "critical security fix"


def test_recognise_override_prefix():
    """contract-update: prefix + flag → recognised."""
    msg = "contract-update: deferring auth to identity provider"
    recognised, rationale = recognise_override(msg, override_flag=True)
    assert recognised is True
    assert "deferring auth" in rationale


def test_recognise_override_default_no_without_flag():
    """Default-no — flag=False → not recognised."""
    msg = "Loam-Override: ratl\n"
    recognised, rationale = recognise_override(msg, override_flag=False)
    assert recognised is False


def test_proposed_objectives_demote_verified_to_plausible():
    """VERIFIED-touched objective → proposed as PLAUSIBLE."""
    classification = _make_classification_with_verified()
    proposed = _proposed_objectives_from_classification(
        classification, repo_sha="abc"
    )
    assert len(proposed) == 1
    p = proposed[0]
    assert p.objective_id == "O.auth.1"
    assert p.confidence is ConfidenceBand.PLAUSIBLE
    # Domain + text preserved.
    assert p.domain == "auth"
    assert "password length" in p.text
    # Multi-source evidence preserved.
    assert p.evidence.readme_excerpts == ["Auth supports password length"]


def test_build_override_request_carries_originals_and_proposed():
    """build_override_request returns OverrideRequest with both lists."""
    classification = _make_classification_with_verified()
    request = build_override_request(
        classification,
        rationale="critical fix",
        owner="dev@example.com",
        commit_sha="abcdef",
        repo_sha="abc1234567890def",
    )
    assert isinstance(request, OverrideRequest)
    assert len(request.original_objectives) == 1
    assert request.original_objectives[0].confidence is ConfidenceBand.VERIFIED
    assert len(request.proposed_objectives) == 1
    assert request.proposed_objectives[0].confidence is ConfidenceBand.PLAUSIBLE


def test_apply_override_writes_overlay(tmp_workspace):
    """apply_override writes a Cycle 3 v2 overlay to disk."""
    classification = _make_classification_with_verified()
    request = build_override_request(
        classification,
        rationale="auth refactor approved",
        owner="dev@example.com",
        commit_sha="abcdef0123",
        repo_sha="abc1234567890def",
    )
    overlay_path = apply_override(
        request, workspace_root=tmp_workspace, repo_id="test-repo"
    )
    assert overlay_path.exists()
    assert overlay_path.name == "override-1.yaml"
    data = yaml.safe_load(overlay_path.read_text())
    assert data["schema_version"] == 2
    assert data["kind"] == "replace_verified_objective"
    assert data["original_objective_id"] == "O.auth.1"
    assert data["replacement_objective"]["confidence"] == "PLAUSIBLE"
    assert data["rationale"] == "auth refactor approved"


def test_overlay_round_trips_through_read_contract(
    tmp_workspace,
    synthetic_objectives_dict,
    synthetic_backing_map_dict,
):
    """Apply overlay, then read_contract should reflect the demotion."""
    repo_id = "round-trip-test-12345678"
    ext_dir = tmp_workspace / ".loam" / "extractions" / repo_id
    ext_dir.mkdir(parents=True)
    (ext_dir / "objectives.yaml").write_text(
        yaml.safe_dump(synthetic_objectives_dict, sort_keys=False),
        encoding="utf-8",
    )
    (ext_dir / "backing-map.yaml").write_text(
        yaml.safe_dump(synthetic_backing_map_dict, sort_keys=False),
        encoding="utf-8",
    )
    classification = _make_classification_with_verified()
    request = build_override_request(
        classification,
        rationale="round-trip test",
        owner="dev@example.com",
        commit_sha="abcdef",
        repo_sha="abc1234567890def",
    )
    apply_override(
        request, workspace_root=tmp_workspace, repo_id=repo_id
    )
    from loam_pr_safety import read_contract

    contract = read_contract(repo_id, tmp_workspace)
    auth_obj = next(
        o for o in contract.objectives if o.objective_id == "O.auth.1"
    )
    assert auth_obj.confidence is ConfidenceBand.PLAUSIBLE
    assert contract.override_count == 1
