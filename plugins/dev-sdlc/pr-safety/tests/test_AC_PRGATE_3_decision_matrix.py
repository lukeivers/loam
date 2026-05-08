"""AC.PRGATE.3 — Gate decision matrix at objective altitude.

Per v0.2.3 Cycle 3 sub-plan-doc §3 AC.PRGATE.3.

Pre-emption preserved (HARD_BLOCK > SURFACE_DECISION > DOCS_ONLY > PASS).
Production-stake honour preserved.
"""

from __future__ import annotations

from pathlib import Path


from loam_odd_extractor.bands import ConfidenceBand
from loam_odd_extractor.spec import EvidenceRowRef, Objective, ObjectiveEvidence

from loam_pr_safety import (
    ClassificationResult,
    GateAction,
    Hunk,
    NovelDiff,
    TouchedObjective,
    decide,
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


def _plausible_objective() -> Objective:
    return Objective(
        objective_id="O.orders.1",
        text="Operators place orders with line items that cascade-delete on order removal.",
        confidence=ConfidenceBand.PLAUSIBLE,
        domain="orders",
        evidence=ObjectiveEvidence(
            design_doc_refs=["docs/orders.md#cascade"],
        ),
    )


def _hypothesised_objective() -> Objective:
    return Objective(
        objective_id="O.payments.1",
        text="Operators retry failed charges with exponential backoff.",
        confidence=ConfidenceBand.HYPOTHESISED,
        domain="payments",
        evidence=ObjectiveEvidence(
            rationale="Inferred from comment in payment integration."
        ),
    )


def _make_touched(objective: Objective) -> TouchedObjective:
    return TouchedObjective(
        objective=objective,
        touch_kind="evidence_line",
        touched_evidence_rows=[
            EvidenceRowRef(
                evidence_row_id="route:test.py:1",
                kind="route",
                path="test.py",
                line_range=[1, 1],
            )
        ],
        touched_hunks=[
            Hunk(old_start=1, old_lines=1, new_start=1, new_lines=1)
        ],
    )


def test_verified_only_yields_hard_block():
    """V-only → HARD_BLOCK; reason names objective text."""
    obj = _verified_objective()
    cls = ClassificationResult(touched_objectives=[_make_touched(obj)])
    decision = decide(cls, safety_profile="dev", extraction_id="ext")
    assert decision.action is GateAction.HARD_BLOCK
    assert decision.requires_ratification is True
    # Reason renders objective TEXT not AC ID.
    assert "O.auth.1" in decision.reason
    assert "password length validation" in decision.reason
    # Backing row provenance in reason.
    assert "test.py:1" in decision.reason
    # Audit payload carries verified_objective_ids.
    assert "verified_objective_ids" in decision.audit_payload
    assert decision.audit_payload["verified_objective_ids"] == ["O.auth.1"]


def test_plausible_only_yields_surface_decision_with_pm_pair():
    """P-only → SURFACE_DECISION; PM pair has objective provenance."""
    obj = _plausible_objective()
    cls = ClassificationResult(touched_objectives=[_make_touched(obj)])
    decision = decide(cls, safety_profile="dev", extraction_id="ext1")
    assert decision.action is GateAction.SURFACE_DECISION
    assert decision.requires_ratification is False  # dev default
    assert len(decision.pm_batch_pairs) == 1
    q, p = decision.pm_batch_pairs[0]
    assert "O.orders.1" in q
    assert "cascade-delete" in q
    assert p == "pr-safety:plausible-objective:ext1:O.orders.1"


def test_hypothesised_only_yields_docs_only():
    """H-only → DOCS_ONLY; no PM pairs."""
    obj = _hypothesised_objective()
    cls = ClassificationResult(touched_objectives=[_make_touched(obj)])
    decision = decide(cls, safety_profile="dev", extraction_id="ext")
    assert decision.action is GateAction.DOCS_ONLY
    assert decision.requires_ratification is False
    assert decision.pm_batch_pairs == []


def test_novel_only_yields_surface_decision():
    """Novel-only → SURFACE_DECISION (consolidated)."""
    cls = ClassificationResult(
        novel=[
            NovelDiff(
                file_path=Path("src/new.py"),
                hunks=[Hunk(old_start=1, old_lines=0, new_start=1, new_lines=10)],
            )
        ]
    )
    decision = decide(cls, safety_profile="dev", extraction_id="ext")
    assert decision.action is GateAction.SURFACE_DECISION
    assert len(decision.pm_batch_pairs) == 1
    q, p = decision.pm_batch_pairs[0]
    assert p == "pr-safety:novel-diff:ext"


def test_mixed_v_plus_p_pre_empts_to_hard_block():
    """V + P → HARD_BLOCK (pre-emption order preserved)."""
    cls = ClassificationResult(
        touched_objectives=[
            _make_touched(_verified_objective()),
            _make_touched(_plausible_objective()),
        ]
    )
    decision = decide(cls, safety_profile="dev", extraction_id="ext")
    assert decision.action is GateAction.HARD_BLOCK


def test_production_stake_forces_ratification_on_surface_decision():
    """production-stake profile → requires_ratification=True on SURFACE_DECISION."""
    obj = _plausible_objective()
    cls = ClassificationResult(touched_objectives=[_make_touched(obj)])
    decision = decide(
        cls, safety_profile="production-stake", extraction_id="ext"
    )
    assert decision.action is GateAction.SURFACE_DECISION
    assert decision.requires_ratification is True


def test_require_ratification_flag_on_dev_forces_true():
    """--require-ratification on dev → requires_ratification=True."""
    obj = _plausible_objective()
    cls = ClassificationResult(touched_objectives=[_make_touched(obj)])
    decision = decide(
        cls,
        safety_profile="dev",
        extraction_id="ext",
        require_ratification=True,
    )
    assert decision.action is GateAction.SURFACE_DECISION
    assert decision.requires_ratification is True


def test_pass_when_no_touch_no_novel():
    """Untouched + no novel → PASS."""
    cls = ClassificationResult(touched_objectives=[], novel=[], untouched=True)
    decision = decide(cls, safety_profile="dev", extraction_id="ext")
    assert decision.action is GateAction.PASS
    assert decision.requires_ratification is False
