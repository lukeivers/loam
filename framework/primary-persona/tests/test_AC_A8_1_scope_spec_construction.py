"""AC.A8.1 — Wrapper constructs a valid `ScopeSpec` from a dispatch shape.

Given a dispatch shape carrying objective, constraints, halt
conditions, expected duration, task-shape category, reversibility
class, the wrapper's spec-construction surface returns a `ScopeSpec`
whose Pydantic validation passes and whose fields carry the inputs
verbatim (or in derived shape).
"""

from __future__ import annotations

from loam.primary_persona import DispatchShape
from loam.primary_persona.dispatch_wrapper import _build_scope_spec
from loam.scope_of_work import (
    Budget,
    ReversibilityClass,
    ScopeSpec,
    SuccessCriterion,
)


def test_AC_A8_1_constructs_valid_scope_spec_from_shape():
    shape = DispatchShape(
        objective="research the foo",
        constraints=("no LLM in the inner loop", "stay in /tmp"),
        halt_conditions=("foo found", "30s elapsed"),
        expected_duration_seconds=30.0,
        task_shape_category="moderate",
        reversibility_class="compensatable",
    )
    spec = _build_scope_spec(shape, owner_persona="primary")
    assert isinstance(spec, ScopeSpec)
    # Field-by-field verification.
    assert spec.goal == "research the foo"
    assert spec.constraints == (
        "no LLM in the inner loop",
        "stay in /tmp",
    )
    assert isinstance(spec.budget, Budget)
    assert spec.reversibility_class == ReversibilityClass.compensatable
    # SuccessCriterion derived per halt_condition.
    assert len(spec.success_criteria) == 2
    descriptions = {c.description for c in spec.success_criteria}
    assert "foo found" in descriptions
    assert "30s elapsed" in descriptions
    # Pydantic validation already passed (frozen model — instantiation
    # would have raised). Explicit re-check of the duration carry-through.
    assert spec.expected_duration_seconds == 30.0
    assert spec.owner_persona == "primary"


def test_AC_A8_1_synthetic_criterion_when_no_halt_conditions():
    """When halt_conditions is empty, the wrapper synthesises one
    success criterion naming the objective itself — at-least-one
    criterion is mandatory per AC.A8.1."""
    shape = DispatchShape(
        objective="trivial read",
        constraints=(),
        halt_conditions=(),
        expected_duration_seconds=2.0,
        task_shape_category="trivial",
    )
    spec = _build_scope_spec(shape)
    assert len(spec.success_criteria) >= 1
    assert isinstance(spec.success_criteria[0], SuccessCriterion)


def test_AC_A8_1_irreversible_class_passes_through():
    shape = DispatchShape(
        objective="external action",
        halt_conditions=("done",),
        expected_duration_seconds=10.0,
        task_shape_category="simple",
        reversibility_class="irreversible",
    )
    spec = _build_scope_spec(shape)
    assert spec.reversibility_class == ReversibilityClass.irreversible


def test_AC_A8_1_fully_reversible_class_passes_through():
    shape = DispatchShape(
        objective="read a file",
        halt_conditions=("file read",),
        expected_duration_seconds=1.0,
        task_shape_category="trivial",
        reversibility_class="fully_reversible",
    )
    spec = _build_scope_spec(shape)
    assert spec.reversibility_class == ReversibilityClass.fully_reversible
