"""AC.DGR.2 — the generated gate demonstrably reflects the grounding.

  * at least one gate criterion is traceable to a named practitioner
    norm (the record's norm ids) — a grounded run whose gate cites
    nothing is a REFUSAL, not a footnote;
  * a criterion citing a norm id that is NOT in the record is
    fabricated traceability — refused (claim-or-cite);
  * where research could not settle a judgment standard, the record's
    expert-gate flags carry through to the design in plain language
    instead of an invented standard;
  * an ungrounded run requires no traceability (there is nothing to
    trace to) — and never fakes any.

Per docs/plans/general-build-from-intent.md §6.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop.generative import (  # noqa: E402
    GenerationUnavailable,
    generate_design,
)
from handsoff_loop.grounding import (  # noqa: E402
    GroundingOutcome,
    PractitionerNorm,
)
from handsoff_loop.request_intent import RequestIntent  # noqa: E402


def _intent():
    return RequestIntent(ask="ask", inferred_intent="intent",
                         objective="the objective")


def _grounding(flags=()):
    return GroundingOutcome(
        grounded=True, objective="the objective", summary="summary",
        norms=[
            PractitionerNorm(norm_id="N1", norm="norm one",
                             source_url="https://x.org/1",
                             source_title="One", http_status=200),
            PractitionerNorm(norm_id="N2", norm="norm two",
                             source_url="https://x.org/2",
                             source_title="Two", http_status=200),
        ],
        expert_gate_flags=list(flags), record_path="/tmp/r.md")


def _payload(criteria):
    return {
        "tool_plan": "plan", "data_shape": "shape",
        "gate_plain": "done when correct",
        "gate_criteria": criteria,
        "gate_files": {"check.py": "pass\n"},
        "check_command": "python3 {gate_dir}/check.py {work_dir}",
        "held_out_command": "",
        "sub_tasks": [{"name": "t", "brief": "build the tool",
                       "tighter_acceptance": "ok"}],
        "judge_scope": "sample only",
    }


def _llm(criteria):
    def _fn(prompt, *, model="sonnet", timeout=0):
        return {"result": json.dumps(_payload(criteria))}
    return _fn


def test_traceable_criterion_accepted_and_recorded():
    design = generate_design(
        _intent(), _grounding(),
        llm_json_fn=_llm([
            {"criterion": "honors norm one", "traceable_to": "N1"},
            {"criterion": "from the ask", "traceable_to": ""}]))
    traced = [c for c in design.gate_criteria if c.traceable_to]
    assert [c.traceable_to for c in traced] == ["N1"]


def test_grounded_run_with_no_traceable_criterion_is_refused():
    with pytest.raises(GenerationUnavailable, match="traceable"):
        generate_design(
            _intent(), _grounding(),
            llm_json_fn=_llm([
                {"criterion": "from the ask", "traceable_to": ""}]))


def test_fabricated_norm_id_is_refused():
    with pytest.raises(GenerationUnavailable, match="fabricated"):
        generate_design(
            _intent(), _grounding(),
            llm_json_fn=_llm([
                {"criterion": "cites a ghost", "traceable_to": "N9"}]))


def test_expert_gate_flags_carry_into_the_design_not_invented_standards():
    design = generate_design(
        _intent(),
        _grounding(flags=["Tolerance for partial matches needs a "
                          "practitioner's call."]),
        llm_json_fn=_llm([
            {"criterion": "honors norm two", "traceable_to": "N2"}]))
    assert design.expert_gate_flags == [
        "Tolerance for partial matches needs a practitioner's call."]


def test_ungrounded_run_requires_no_traceability_and_fakes_none():
    ungrounded = GroundingOutcome(
        grounded=False, objective="the objective",
        ungrounded_reason="research unavailable")
    design = generate_design(
        _intent(), ungrounded,
        llm_json_fn=_llm([
            {"criterion": "from the ask", "traceable_to": ""}]))
    assert all(not c.traceable_to for c in design.gate_criteria)
    assert design.expert_gate_flags == []
