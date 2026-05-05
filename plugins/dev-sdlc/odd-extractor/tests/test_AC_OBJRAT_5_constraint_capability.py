"""AC.OBJRAT.5 — Constraint + capability ratification.

- Constraint promotion: only explicit_yes gate; no backing required.
- Capability serves-validator: refuses on dangling references.
- Capability serves-validator: refuses on H-band served objective at
  PLAUSIBLE→VERIFIED.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_odd_extractor import (
    Capability,
    CapabilityEvidence,
    ConfidenceBand,
    Constraint,
    ConstraintEvidence,
    Objective,
    ObjectiveEvidence,
    RatificationRefusedError,
    apply_objective_ratification_action,
    promote_capability,
    promote_constraint,
)


def test_constraint_p_to_v_only_needs_explicit_yes(tmp_path: Path) -> None:
    cons = Constraint(
        constraint_id="K.compliance.1",
        text="System SOC-2 compliant",
        bounds_kind="compliance",
        evidence=ConstraintEvidence(readme_excerpts=["soc2"]),
    )
    # Without explicit_yes:
    with pytest.raises(RatificationRefusedError):
        promote_constraint(
            target_id="K.compliance.1",
            from_band=ConfidenceBand.PLAUSIBLE,
            to_band=ConfidenceBand.VERIFIED,
            # no explicit_yes
        )
    # With explicit_yes — accepted.
    a = promote_constraint(
        target_id="K.compliance.1",
        from_band=ConfidenceBand.PLAUSIBLE,
        to_band=ConfidenceBand.VERIFIED,
        explicit_yes=True,
    )
    out = apply_objective_ratification_action(
        a,
        constraints=[cons],
        workspace_root=tmp_path,
        repo_id="t",
    )
    assert out["constraints"][0].constraint_id == "K.compliance.1"


def test_capability_serves_dangling_refused(tmp_path: Path) -> None:
    """Promotion blocks when the capability references an unknown
    objective_id.
    """
    cap = Capability(
        capability_id="C.alpha.1",
        text="Alpha capability",
        serves=["O.does-not-exist.1"],
        evidence=CapabilityEvidence(readme_excerpts=["x"]),
    )
    a = promote_capability(
        target_id="C.alpha.1",
        from_band=ConfidenceBand.HYPOTHESISED,
        to_band=ConfidenceBand.PLAUSIBLE,
    )
    with pytest.raises(RatificationRefusedError) as e:
        apply_objective_ratification_action(
            a,
            objectives=[],
            capabilities=[cap],
            workspace_root=tmp_path,
            repo_id="t",
        )
    assert "unknown objective" in str(e.value)


def test_capability_h_band_served_blocks_v_promotion(tmp_path: Path) -> None:
    """Capability cannot promote to VERIFIED while a served objective
    is HYPOTHESISED.
    """
    obj = Objective(
        objective_id="O.dispute.1",
        text="Operators file refund disputes through the merchant portal at scale",
        confidence=ConfidenceBand.HYPOTHESISED,  # H-band
        evidence=ObjectiveEvidence(rationale="LLM inferred"),
        domain="dispute",
    )
    cap = Capability(
        capability_id="C.dispute.1",
        text="dispute pipeline",
        serves=["O.dispute.1"],
        evidence=CapabilityEvidence(readme_excerpts=["x"]),
    )
    a = promote_capability(
        target_id="C.dispute.1",
        from_band=ConfidenceBand.PLAUSIBLE,
        to_band=ConfidenceBand.VERIFIED,
        explicit_yes=True,
    )
    with pytest.raises(RatificationRefusedError) as e:
        apply_objective_ratification_action(
            a,
            objectives=[obj],
            capabilities=[cap],
            workspace_root=tmp_path,
            repo_id="t",
        )
    assert "HYPOTHESISED" in str(e.value)


def test_capability_p_band_served_allows_v_promotion(tmp_path: Path) -> None:
    """When the served objective is at least PLAUSIBLE, capability
    promotion to VERIFIED is allowed (with explicit_yes).
    """
    obj = Objective(
        objective_id="O.dispute.1",
        text="Operators file refund disputes through the merchant portal at scale",
        confidence=ConfidenceBand.PLAUSIBLE,
        evidence=ObjectiveEvidence(readme_excerpts=["dispute"]),
        domain="dispute",
    )
    cap = Capability(
        capability_id="C.dispute.1",
        text="dispute pipeline",
        serves=["O.dispute.1"],
        evidence=CapabilityEvidence(readme_excerpts=["x"]),
    )
    a = promote_capability(
        target_id="C.dispute.1",
        from_band=ConfidenceBand.PLAUSIBLE,
        to_band=ConfidenceBand.VERIFIED,
        explicit_yes=True,
    )
    out = apply_objective_ratification_action(
        a,
        objectives=[obj],
        capabilities=[cap],
        workspace_root=tmp_path,
        repo_id="t",
    )
    assert out["capabilities"][0].capability_id == "C.dispute.1"
