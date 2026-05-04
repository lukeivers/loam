"""AC.PRSG.5 — override-commit recognition + ratification flow."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam_odd_extractor.bands import (
    BandedAC,
    ConfidenceBand,
    Evidence,
)
from loam_pr_safety import (
    ClassificationResult,
    Hunk,
    OverrideRejectedError,
    OverrideRequest,
    TouchedAC,
    apply_override,
    recognise_override,
)
from loam_pr_safety.override import (
    build_override_request,
    run_override_ratification,
)


# ---- Recognition: trailer / prefix / both / neither ---------------


def test_recognise_via_trailer():
    msg = (
        "fix: tighten validation\n\n"
        "Original AC was overly strict.\n\n"
        "Loam-Override: Auth flow now opt-in for password rule\n"
    )
    recognised, rationale = recognise_override(msg, override_flag=True)
    assert recognised
    assert "opt-in for password rule" in rationale


def test_recognise_via_prefix():
    msg = "contract-update: relax password rule\n\nMore context here.\n"
    recognised, rationale = recognise_override(msg, override_flag=True)
    assert recognised
    assert rationale == "relax password rule"


def test_recognise_neither():
    msg = "feat: ordinary commit\n\nNot an override.\n"
    recognised, rationale = recognise_override(msg, override_flag=True)
    assert not recognised
    assert rationale == ""


def test_recognise_default_no_without_flag():
    """Decision I default-no — even an override-shaped commit must
    have --override flag. No silent promotion.
    """
    msg = (
        "contract-update: relax password rule\n\n"
        "Loam-Override: rationale here\n"
    )
    recognised, rationale = recognise_override(msg, override_flag=False)
    assert not recognised
    assert rationale == ""


def test_recognise_empty_trailer_falls_back_to_prefix():
    msg = (
        "contract-update: prefix-rationale\n\n"
        "Loam-Override:    \n"
    )
    recognised, rationale = recognise_override(msg, override_flag=True)
    assert recognised
    assert rationale == "prefix-rationale"


# ---- build_override_request -----------------------------------------


def test_build_override_request_from_verified_touched():
    verified = BandedAC(
        ac_id="AC.X.1",
        text="Some VERIFIED AC.",
        confidence=ConfidenceBand.VERIFIED,
        evidence=Evidence(
            kind="test",
            citations=["app/foo.py:10-20"],
            repo_sha="abc1234",
        ),
        backing_files=["app/foo.py"],
    )
    classification = ClassificationResult(
        touched_acs=[
            TouchedAC(
                ac=verified,
                touch_kind="citation_line",
                touched_hunks=[
                    Hunk(
                        old_start=12, old_lines=2, new_start=12, new_lines=3,
                        added_lines=["new"],
                    )
                ],
            )
        ]
    )
    req = build_override_request(
        classification,
        rationale="Refactor — old behaviour deprecated.",
        owner="Test User <test@example.com>",
        commit_sha="deadbeef",
        repo_sha="abc1234",
    )
    assert isinstance(req, OverrideRequest)
    assert len(req.original_acs) == 1
    assert req.original_acs[0].ac_id == "AC.X.1"
    # Proposed AC is the same id, downgraded to PLAUSIBLE.
    assert len(req.proposed_acs) == 1
    assert req.proposed_acs[0].ac_id == "AC.X.1"
    assert req.proposed_acs[0].confidence is ConfidenceBand.PLAUSIBLE


# ---- apply_override (overlay file writer) ----------------------------


def test_apply_override_writes_replace_verified_overlay(tmp_workspace):
    verified = BandedAC(
        ac_id="AC.X.1",
        text="VERIFIED AC.",
        confidence=ConfidenceBand.VERIFIED,
        evidence=Evidence(
            kind="test",
            citations=["app/foo.py:10"],
            repo_sha="abc1234",
        ),
        backing_files=["app/foo.py"],
    )
    plausible_replacement = BandedAC(
        ac_id="AC.X.1",
        text="VERIFIED AC (downgraded by override).",
        confidence=ConfidenceBand.PLAUSIBLE,
        evidence=Evidence(
            kind="source",
            citations=["app/foo.py:10"],
        ),
        backing_files=["app/foo.py"],
    )
    req = OverrideRequest(
        original_acs=[verified],
        proposed_acs=[plausible_replacement],
        rationale="downgrade rationale",
        owner="Test User",
        commit_sha="deadbeef",
        repo_sha="abc1234",
    )
    overlay_path = apply_override(
        req, workspace_root=tmp_workspace, repo_id="my-repo-12345678"
    )
    assert overlay_path.exists()
    data = yaml.safe_load(overlay_path.read_text(encoding="utf-8"))
    assert data["kind"] == "replace_verified"
    assert data["original_ac_id"] == "AC.X.1"
    assert data["replacement_ac"]["confidence"] == "PLAUSIBLE"


# ---- run_override_ratification end-to-end (with stub PM) -------------


@pytest.fixture
def stub_pm(tmp_path):
    """A real PMRuntime backed by an in-tmp PM directory.

    Uses the per-project-pm's testing convenience API. If the API
    isn't available, raise SkipTest.
    """
    pytest.importorskip("loam.per_project_pm")
    from loam.per_project_pm import PMRuntime, PMContract
    from loam.per_project_pm.contract import DecisionSurfacingPolicy

    pm_dir = tmp_path / "pm"
    pm_dir.mkdir()
    contract = PMContract(
        handle="test-pm",
        project_name="Test Project",
        project_kind="dev",
        owner_name="Test User",
        workspace_root=tmp_path,
        decision_surfacing_policy=DecisionSurfacingPolicy(
            max_questions_per_turn=3,
            require_owner_response=False,
            onboarding_mode=False,
        ),
    )
    pm = PMRuntime(contract=contract, pm_dir=pm_dir)
    return pm


def test_run_override_ratification_approved(stub_pm, tmp_workspace):
    verified = BandedAC(
        ac_id="AC.X.1",
        text="VERIFIED AC.",
        confidence=ConfidenceBand.VERIFIED,
        evidence=Evidence(
            kind="test",
            citations=["app/foo.py:10"],
            repo_sha="abc1234",
        ),
        backing_files=["app/foo.py"],
    )
    plausible = BandedAC(
        ac_id="AC.X.1",
        text="downgraded",
        confidence=ConfidenceBand.PLAUSIBLE,
        evidence=Evidence(
            kind="source",
            citations=["app/foo.py:10"],
        ),
        backing_files=["app/foo.py"],
    )
    req = OverrideRequest(
        original_acs=[verified],
        proposed_acs=[plausible],
        rationale="rationale",
        owner="Test User",
        commit_sha="deadbeef",
        repo_sha="abc1234",
    )

    def approver(sq):
        return (True, "approved")

    approved, response, overlay = run_override_ratification(
        req,
        pm=stub_pm,
        workspace_root=tmp_workspace,
        repo_id="my-repo",
        response_recorder=approver,
    )
    assert approved is True
    assert response == "approved"
    assert overlay is not None
    assert overlay.exists()


def test_run_override_ratification_rejected(stub_pm, tmp_workspace):
    verified = BandedAC(
        ac_id="AC.X.1",
        text="VERIFIED AC.",
        confidence=ConfidenceBand.VERIFIED,
        evidence=Evidence(
            kind="test",
            citations=["app/foo.py:10"],
            repo_sha="abc1234",
        ),
        backing_files=["app/foo.py"],
    )
    plausible = BandedAC(
        ac_id="AC.X.1",
        text="downgraded",
        confidence=ConfidenceBand.PLAUSIBLE,
        evidence=Evidence(
            kind="source",
            citations=["app/foo.py:10"],
        ),
        backing_files=["app/foo.py"],
    )
    req = OverrideRequest(
        original_acs=[verified],
        proposed_acs=[plausible],
        rationale="rationale",
        owner="Test User",
        commit_sha="deadbeef",
        repo_sha="abc1234",
    )

    def rejector(sq):
        return (False, "rejected — concern about regression")

    with pytest.raises(OverrideRejectedError):
        run_override_ratification(
            req,
            pm=stub_pm,
            workspace_root=tmp_workspace,
            repo_id="my-repo",
            response_recorder=rejector,
        )
