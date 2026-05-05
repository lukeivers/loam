"""AC.OBJRAT.2 — PLAUSIBLE → VERIFIED on objective requires
explicit_yes + backing_evidence_cited.

- Refused without explicit_yes.
- Refused with empty backing.
- Refused with stale-cited row (not in backing-map entry).
- Accepted with STRONG row.
- Accepted with test-row passing test-asserts-outcome heuristic.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_odd_extractor import (
    BackingMap,
    BackingMapEntry,
    ConfidenceBand,
    EvidenceRowRef,
    Objective,
    ObjectiveEvidence,
    ObjectiveRatificationAction,
    RatificationRefusedError,
    apply_objective_ratification_action,
    promote_objective,
    is_test_asserts_outcome,
)


def _objective() -> Objective:
    return Objective(
        objective_id="O.dispute.1",
        text="Operators file refund disputes through the merchant portal at scale",
        confidence=ConfidenceBand.PLAUSIBLE,
        evidence=ObjectiveEvidence(readme_excerpts=["dispute"]),
        domain="dispute",
    )


def _backing_map_with_strong() -> BackingMap:
    return BackingMap(
        extraction_id="t",
        entries=[
            BackingMapEntry(
                objective_id="O.dispute.1",
                evidence_rows=[
                    EvidenceRowRef(
                        evidence_row_id="route:src/disputeRoutes.js:42",
                        kind="route",
                        path="src/disputeRoutes.js",
                        line_range=(42, 47),
                        confidence="STRONG",
                        language="jsts",
                    ),
                    EvidenceRowRef(
                        evidence_row_id="test:tests/dispute.spec.ts:1",
                        kind="test",
                        path="tests/dispute.spec.ts",
                        line_range=(1, 20),
                        symbol_name="operator should file dispute",
                        confidence="WEAK",
                        language="jsts",
                    ),
                ],
            ),
        ],
        orphan_rows=[],
        created_at="2026-05-04T12:00:00+00:00",
        total_evidence_rows=2,
        objective_count=1,
    )


# ---- Factory-side gate ---------------------------------------------


def test_factory_refuses_p_to_v_without_explicit_yes() -> None:
    with pytest.raises(RatificationRefusedError) as e:
        promote_objective(
            target_id="O.dispute.1",
            from_band=ConfidenceBand.PLAUSIBLE,
            to_band=ConfidenceBand.VERIFIED,
            # explicit_yes omitted
            backing_evidence_cited=["route:src/disputeRoutes.js:42"],
        )
    assert "explicit_yes" in str(e.value)


def test_factory_refuses_p_to_v_with_empty_backing() -> None:
    with pytest.raises(RatificationRefusedError) as e:
        promote_objective(
            target_id="O.dispute.1",
            from_band=ConfidenceBand.PLAUSIBLE,
            to_band=ConfidenceBand.VERIFIED,
            explicit_yes=True,
            backing_evidence_cited=[],
        )
    assert "backing_evidence_cited" in str(e.value)


def test_factory_accepts_p_to_v_with_explicit_yes_and_backing() -> None:
    a = promote_objective(
        target_id="O.dispute.1",
        from_band=ConfidenceBand.PLAUSIBLE,
        to_band=ConfidenceBand.VERIFIED,
        explicit_yes=True,
        backing_evidence_cited=["route:src/disputeRoutes.js:42"],
    )
    assert a.kind == "promote"


# ---- Apply-path defense-in-depth -----------------------------------


def test_apply_refuses_stale_cited_row(tmp_path: Path) -> None:
    obj = _objective()
    bm = _backing_map_with_strong()
    action = promote_objective(
        target_id="O.dispute.1",
        from_band=ConfidenceBand.PLAUSIBLE,
        to_band=ConfidenceBand.VERIFIED,
        explicit_yes=True,
        backing_evidence_cited=["route:src/MISSING.js:1"],  # not in BM
    )
    with pytest.raises(RatificationRefusedError) as e:
        apply_objective_ratification_action(
            action,
            objectives=[obj],
            backing_map=bm,
            workspace_root=tmp_path,
            repo_id="t",
        )
    assert "stale" in str(e.value).lower() or "not in backing_map" in str(e.value)


def test_apply_accepts_strong_row(tmp_path: Path) -> None:
    obj = _objective()
    bm = _backing_map_with_strong()
    action = promote_objective(
        target_id="O.dispute.1",
        from_band=ConfidenceBand.PLAUSIBLE,
        to_band=ConfidenceBand.VERIFIED,
        explicit_yes=True,
        backing_evidence_cited=["route:src/disputeRoutes.js:42"],
    )
    out = apply_objective_ratification_action(
        action,
        objectives=[obj],
        backing_map=bm,
        workspace_root=tmp_path,
        repo_id="t",
    )
    assert out["objectives"][0].confidence is ConfidenceBand.VERIFIED


def test_apply_accepts_test_row_with_outcome_heuristic(tmp_path: Path) -> None:
    """A WEAK kind=test row passes when its symbol_name has an
    outcome-verb + domain overlap.
    """
    obj = _objective()
    bm = _backing_map_with_strong()
    action = promote_objective(
        target_id="O.dispute.1",
        from_band=ConfidenceBand.PLAUSIBLE,
        to_band=ConfidenceBand.VERIFIED,
        explicit_yes=True,
        backing_evidence_cited=["test:tests/dispute.spec.ts:1"],
    )
    out = apply_objective_ratification_action(
        action,
        objectives=[obj],
        backing_map=bm,
        workspace_root=tmp_path,
        repo_id="t",
    )
    assert out["objectives"][0].confidence is ConfidenceBand.VERIFIED


def test_apply_refuses_weak_non_test_row(tmp_path: Path) -> None:
    """A WEAK kind!=test row never qualifies."""
    bm = BackingMap(
        extraction_id="t",
        entries=[
            BackingMapEntry(
                objective_id="O.dispute.1",
                evidence_rows=[
                    EvidenceRowRef(
                        evidence_row_id="model:src/Dispute.js:5",
                        kind="model",
                        path="src/Dispute.js",
                        confidence="WEAK",
                    ),
                ],
            ),
        ],
        orphan_rows=[],
        created_at="2026-05-04T12:00:00+00:00",
        total_evidence_rows=1,
        objective_count=1,
    )
    action = promote_objective(
        target_id="O.dispute.1",
        from_band=ConfidenceBand.PLAUSIBLE,
        to_band=ConfidenceBand.VERIFIED,
        explicit_yes=True,
        backing_evidence_cited=["model:src/Dispute.js:5"],
    )
    with pytest.raises(RatificationRefusedError):
        apply_objective_ratification_action(
            action,
            objectives=[_objective()],
            backing_map=bm,
            workspace_root=tmp_path,
            repo_id="t",
        )


def test_is_test_asserts_outcome_heuristic_basic() -> None:
    """The heuristic accepts verb + domain overlap; rejects neither."""
    assert is_test_asserts_outcome(
        "operator should file dispute",
        domain_tokens=["dispute"],
    )
    assert is_test_asserts_outcome(
        "expects refund completes",
        domain_tokens=["refund"],
    )
    # No verb match.
    assert not is_test_asserts_outcome(
        "dispute_route_returns_200",
        domain_tokens=["dispute"],
    )
    # No domain overlap.
    assert not is_test_asserts_outcome(
        "should fail",
        domain_tokens=["dispute"],
    )
    # Empty input.
    assert not is_test_asserts_outcome("")


def test_apply_p_to_v_constructed_directly_still_refused(tmp_path: Path) -> None:
    """Bypass factory: construct ObjectiveRatificationAction directly with
    explicit_yes=False; apply path defense-in-depth still refuses.
    """
    direct = ObjectiveRatificationAction(
        kind="promote",
        target_id="O.dispute.1",
        altitude="objective",
        from_band=ConfidenceBand.PLAUSIBLE,
        to_band=ConfidenceBand.VERIFIED,
        explicit_yes=False,
        backing_evidence_cited=("route:src/disputeRoutes.js:42",),
    )
    with pytest.raises(RatificationRefusedError):
        apply_objective_ratification_action(
            direct,
            objectives=[_objective()],
            backing_map=_backing_map_with_strong(),
            workspace_root=tmp_path,
            repo_id="t",
        )
