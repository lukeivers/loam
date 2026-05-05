"""AC.OBJX.8 — Altitude validator (programmatic + decision tree).

- Clear-pass row: classification = pass; decision = keep.
- Clear-fail row (symbol/file/line): classification = fail (§2);
  decision = restate-as-capability.
- Borderline row (purpose marker absent): classification =
  borderline; decision = downgrade if VERIFIED, keep otherwise.
- Decision tree applied per failed-axis.
- Drift halt at >30% fail rate.
"""

from __future__ import annotations

from loam_odd_extractor import (
    Capability,
    CapabilityEvidence,
    ConfidenceBand,
    Constraint,
    ConstraintEvidence,
    Objective,
    ObjectiveEvidence,
    validate_altitude,
)


def _good_objective(n: int = 1) -> Objective:
    return Objective(
        objective_id=f"O.dispute-flow.{n}",
        text=(
            "Operators file refund disputes against merchant portals "
            "at scale, replacing manual portal clickwork."
        ),
        confidence=ConfidenceBand.PLAUSIBLE,
        domain="dispute-flow",
        evidence=ObjectiveEvidence(readme_excerpts=["files refunds"]),
    )


def _bad_implementation_objective() -> Objective:
    """Names HTTP verb + route — fails §self-check 2."""
    return Objective(
        objective_id="O.bad-impl.1",
        text="Express GET /all-orders route exists at file.js:42",
        confidence=ConfidenceBand.HYPOTHESISED,
        domain="bad-impl",
        evidence=ObjectiveEvidence(
            code_pattern_refs=["file.js:42"],
            rationale="route shape",
        ),
    )


def _fact_objective() -> Objective:
    """States existence — fails §self-check 1."""
    return Objective(
        objective_id="O.bad-fact.1",
        text="Function processOrder() exists at src/orders/handler.py",
        confidence=ConfidenceBand.HYPOTHESISED,
        domain="bad-fact",
        evidence=ObjectiveEvidence(
            code_pattern_refs=["src/orders/handler.py"],
            rationale="function exists",
        ),
    )


def test_clear_pass_objective_keeps() -> None:
    o = _good_objective()
    report = validate_altitude(
        extraction_id="x", objectives=[o]
    )
    assert report.total_rows == 1
    assert report.pass_count == 1
    assert report.results[0].classification == "pass"
    assert report.results[0].decision == "keep"
    assert not report.drift_halt_triggered


def test_implementation_swap_failure_restates_as_capability() -> None:
    o = _bad_implementation_objective()
    report = validate_altitude(
        extraction_id="x", objectives=[o]
    )
    assert report.fail_count == 1
    r = report.results[0]
    assert r.classification == "fail"
    assert r.failed_check == 2
    assert r.decision == "restate-as-capability"
    assert report.restated_count == 1


def test_fact_failure_drops() -> None:
    """§1 fail (fact-as-objective) → drop."""
    o = _fact_objective()
    # Wait — the fact objective text starts with "Function processOrder()"
    # which actually fails §2 first (function-name marker). Let's
    # construct a true §1-only failure.
    report = validate_altitude(
        extraction_id="x",
        objectives=[
            Objective(
                objective_id="O.bad.1",
                text="No test coverage exists for this module currently",
                confidence=ConfidenceBand.HYPOTHESISED,
                domain="bad",
                evidence=ObjectiveEvidence(
                    rationale="missing tests",
                ),
            )
        ],
    )
    r = report.results[0]
    assert r.classification == "fail"
    assert r.failed_check == 1
    assert r.decision == "drop"


def test_drift_halt_triggers_at_above_threshold() -> None:
    """>30% fail rate flips ``drift_halt_triggered``."""
    objectives = [
        _bad_implementation_objective(),
        _bad_implementation_objective(),
        _good_objective(),  # 1 pass, 2 fail = 67% fail
    ]
    # Override IDs so they're unique.
    objectives[1] = objectives[1].model_copy(
        update={"objective_id": "O.bad-impl.2"}
    )
    report = validate_altitude(
        extraction_id="x", objectives=objectives
    )
    assert report.fail_count == 2
    assert report.drift_halt_triggered is True


def test_drift_halt_does_not_trigger_below_threshold() -> None:
    objectives = [
        _good_objective(1),
        _good_objective(2).model_copy(update={"objective_id": "O.dispute-flow.2"}),
        _good_objective(3).model_copy(update={"objective_id": "O.dispute-flow.3"}),
        _bad_implementation_objective(),  # 1 fail / 4 total = 25%
    ]
    report = validate_altitude(
        extraction_id="x", objectives=objectives
    )
    assert report.fail_count == 1
    assert report.drift_halt_triggered is False


def test_constraint_and_capability_classified_too() -> None:
    o = _good_objective()
    k = Constraint(
        constraint_id="K.compliance.1",
        text="System must satisfy SOC-2 audit trail",
        bounds_kind="compliance",
        evidence=ConstraintEvidence(readme_excerpts=["soc2"]),
    )
    c = Capability(
        capability_id="C.csv.1",
        text="CSV upload pipeline supports bulk dispute filing",
        serves=["O.dispute-flow.1"],
        evidence=CapabilityEvidence(readme_excerpts=["csv upload"]),
    )
    report = validate_altitude(
        extraction_id="x",
        objectives=[o],
        constraints=[k],
        capabilities=[c],
    )
    assert report.total_rows == 3
    kinds = {r.row_kind for r in report.results}
    assert kinds == {"objective", "constraint", "capability"}


def test_threshold_overridable() -> None:
    """``fail_threshold`` parameter accepts custom values."""
    objectives = [_bad_implementation_objective()]  # 100% fail
    report = validate_altitude(
        extraction_id="x", objectives=objectives, fail_threshold=0.99
    )
    # 100% > 99% → halt
    assert report.drift_halt_triggered is True
    report2 = validate_altitude(
        extraction_id="x", objectives=objectives, fail_threshold=1.5
    )
    # 100% < 150% → no halt
    assert report2.drift_halt_triggered is False
