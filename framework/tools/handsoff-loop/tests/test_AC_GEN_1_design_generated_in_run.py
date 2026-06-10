"""AC.GEN.1 — tool, data shape, and gate GENERATED during the run (S3).

From the confirmed intent + grounding record, the pipeline derives the
objective and generates the deliverable's design: the tool plan, its
data shape, and its acceptance gate — none of which exists anywhere
before the run:

  * every design field flows from the live generation dispatch (a
    content-sensitive double proves the output is a function of THIS
    run's inputs — no pre-built design could pass);
  * gate artifacts are materialised OUTSIDE the build work dir, and a
    sub-task brief that quotes the gate text or names a gate file is a
    REFUSAL at generation time (frozen-unseen preserved by
    construction, before assert_unseen_by even runs);
  * an unusable design (empty gate / no verification files / no build
    plan) raises — there is no pre-built fallback, which is the point;
  * path traversal in generated gate paths is refused.

The born-during-the-run git/mtime evidence on a REAL run is
AC.GEN.OA (env-gated live + the S6 logged runs).

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
    resolve_command,
    write_gate_files,
)
from handsoff_loop.grounding import (  # noqa: E402
    GroundingOutcome,
    PractitionerNorm,
)
from handsoff_loop.request_intent import RequestIntent  # noqa: E402


def _intent(ask="sort the widget inventory"):
    return RequestIntent(
        ask=ask,
        inferred_intent=f"You want a tool for: {ask}",
        objective=f"objective derived from: {ask}",
    )


def _grounding():
    return GroundingOutcome(
        grounded=True, objective="obj",
        summary="Practitioners do it carefully.",
        norms=[PractitionerNorm(
            norm_id="N1", norm="Nothing is silently dropped.",
            source_url="https://example.org/a", source_title="A",
            http_status=200)],
        expert_gate_flags=["Edge pricing needs an expert."],
        record_path="/tmp/rec.md",
    )


def _design_payload(**overrides):
    base = {
        "tool_plan": "A small tool that does the work.",
        "data_shape": "Reads input.csv, writes output.csv.",
        "gate_plain": "Done when the output file lists every item once.",
        "gate_criteria": [
            {"criterion": "No input row is silently dropped.",
             "traceable_to": "N1"},
            {"criterion": "Output exists and is readable.",
             "traceable_to": ""},
        ],
        "gate_files": {
            "check.py": "import sys; sys.exit(0)\n",
            "sample/input.csv": "a,b\n1,2\n",
            "held_out/input.csv": "a,b\n3,4\n",
        },
        "check_command": "python3 {gate_dir}/check.py {work_dir} "
                         "{gate_dir}/sample/input.csv",
        "held_out_command": "python3 {gate_dir}/check.py {work_dir} "
                            "{gate_dir}/held_out/input.csv",
        "sub_tasks": [
            {"name": "build-tool",
             "brief": "Build tool.py reading input.csv per the shape.",
             "tighter_acceptance": "tool.py runs on a sample row."},
        ],
        "judge_scope": "Checks behavior on sample and held-out data "
                       "only; not on every possible file.",
    }
    base.update(overrides)
    return base


def _llm(payload):
    def _fn(prompt, *, model="sonnet", timeout=0):
        return {"result": json.dumps(payload)}
    return _fn


def test_design_flows_from_this_runs_inputs():
    captured = {}

    def _capturing_llm(prompt, *, model="sonnet", timeout=0):
        captured["prompt"] = prompt
        return {"result": json.dumps(_design_payload())}

    intent = _intent("sort the widget inventory")
    design = generate_design(intent, _grounding(),
                             llm_json_fn=_capturing_llm)
    # The generation saw THIS run's intent, objective, and norms.
    assert "sort the widget inventory" in captured["prompt"]
    assert "N1: Nothing is silently dropped." in captured["prompt"]
    assert design.objective == intent.objective
    assert design.tool_plan and design.data_shape and design.gate_plain
    # Expert-gate flags carry forward from the grounding record.
    assert design.expert_gate_flags == ["Edge pricing needs an expert."]


def test_gate_artifacts_materialise_outside_work_dir(tmp_path):
    design = generate_design(_intent(), _grounding(),
                             llm_json_fn=_llm(_design_payload()))
    gate_dir = tmp_path / "gate"
    work_dir = tmp_path / "work"
    written = write_gate_files(design, gate_dir=gate_dir)
    assert len(written) == 3
    assert (gate_dir / "check.py").exists()
    assert (gate_dir / "held_out" / "input.csv").exists()
    # None of the gate artifacts lives under the build work dir.
    assert not any(str(work_dir) in w for w in written)
    cmd = resolve_command(design.check_command,
                          gate_dir=gate_dir, work_dir=work_dir)
    assert str(gate_dir) in cmd and str(work_dir) in cmd
    assert "{gate_dir}" not in cmd and "{work_dir}" not in cmd


def test_brief_quoting_the_gate_is_refused():
    leaky = _design_payload()
    leaky["sub_tasks"] = [
        {"name": "build-tool",
         "brief": "Build it. Done when the output file lists every "
                  "item once.",  # quotes gate_plain verbatim
         "tighter_acceptance": "x"}]
    with pytest.raises(GenerationUnavailable, match="leaks the gate"):
        generate_design(_intent(), _grounding(), llm_json_fn=_llm(leaky))


def test_brief_naming_a_gate_file_is_refused():
    leaky = _design_payload()
    leaky["sub_tasks"] = [
        {"name": "build-tool",
         "brief": "Build it and make check.py pass.",
         "tighter_acceptance": "x"}]
    with pytest.raises(GenerationUnavailable, match="leaks the gate"):
        generate_design(_intent(), _grounding(), llm_json_fn=_llm(leaky))


def test_unusable_design_raises_no_prebuilt_fallback():
    for broken in (
        _design_payload(gate_plain=""),
        _design_payload(gate_files={}),
        _design_payload(tool_plan=""),
        _design_payload(sub_tasks=[]),
        _design_payload(check_command="python3 check.py"),  # unanchored
    ):
        with pytest.raises(GenerationUnavailable):
            generate_design(_intent(), _grounding(),
                            llm_json_fn=_llm(broken))


def test_gate_path_traversal_refused(tmp_path):
    evil = _design_payload(
        gate_files={"../outside.py": "print('escape')\n"})
    design = generate_design(_intent(), _grounding(), llm_json_fn=_llm(evil))
    with pytest.raises(GenerationUnavailable, match="escapes"):
        write_gate_files(design, gate_dir=tmp_path / "gate")
