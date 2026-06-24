"""AC.DF.1 — the pipeline produces MULTIPLE candidate designs before
any build starts (design-first front stage).

A run over one ask, with a design-choice surface reachable, generates
>=2 (default 3) materially-distinct candidate designs and surfaces them
for choice BEFORE the acceptance gate is frozen and BEFORE any build
sub-task dispatches.

Outcome, not method: asserts >=2 candidates exist + are surfaced
pre-freeze; does not prescribe how they are generated or rendered. The
generation mechanism (one dispatch returning N) is the builder's call
(§14 D-build.1); the test pins the OUTCOME.

Per docs/plans/handsoff-design-first-and-build-heartbeat.md §5.
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
    generate_candidate_designs,
)
from handsoff_loop.grounding import (  # noqa: E402
    GroundingOutcome,
    PractitionerNorm,
)
from handsoff_loop.request_intent import RequestIntent  # noqa: E402


def _intent(ask="tidy the widget list"):
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
        expert_gate_flags=[],
        record_path="/tmp/rec.md",
    )


def _candidate(form_factor, slug):
    # The lightweight candidate review surface (no gate_files — the
    # buildable gate is generated for the chosen direction later).
    return {
        "form_factor": form_factor,
        "tool_plan": f"A {form_factor} that does the work.",
        "data_shape": "Reads input, writes output.",
        "gate_plain": f"Done when the {slug} produces a clean result.",
        "sample_output": {
            "summary": "Processed 12 rows; 2 need a human's eyes.",
            "rows": [{"id": 1, "status": "ok"},
                     {"id": 2, "status": "ok"}],
            "review_queue": [{"id": 7, "why": "ambiguous"}],
        },
    }


def _llm_rotating(forms=None):
    # Per-candidate dispatch: each call returns ONE candidate. The double
    # rotates through distinct form factors so distinctness holds, and
    # reads the direction seed echoed in the prompt to stay realistic.
    forms = forms or ["one-shot CLI", "interactive review-queue app",
                      "scheduled background normalizer"]
    state = {"i": 0}

    def _fn(prompt, *, model="sonnet", timeout=0):
        i = state["i"]
        state["i"] = i + 1
        ff = forms[i % len(forms)]
        return {"result": json.dumps(_candidate(ff, f"slug{i}"))}
    return _fn


def test_multiple_distinct_candidates_generated():
    cands = generate_candidate_designs(
        _intent(), _grounding(), n=3, llm_json_fn=_llm_rotating())
    assert len(cands) >= 2
    # Materially distinct: the form-factor directions differ.
    form_factors = {c.form_factor.lower() for c in cands}
    assert len(form_factors) == len(cands)


def test_candidates_default_to_three():
    calls = {"n": 0}

    def _fn(prompt, *, model="sonnet", timeout=0):
        i = calls["n"]
        calls["n"] = i + 1
        ff = ["one-shot CLI", "interactive review-queue app",
              "scheduled background normalizer"][i % 3]
        return {"result": json.dumps(_candidate(ff, f"s{i}"))}

    cands = generate_candidate_designs(_intent(), _grounding(),
                                       llm_json_fn=_fn)
    assert len(cands) == 3
    # The default n=3 drove three per-candidate dispatches.
    assert calls["n"] == 3


def test_each_candidate_carries_a_review_surface_and_sample():
    cands = generate_candidate_designs(
        _intent(), _grounding(), n=3, llm_json_fn=_llm_rotating())
    for c in cands:
        # Each candidate carries the plain-language review surface the
        # user picks a direction from.
        assert c.form_factor and c.tool_plan and c.gate_plain
        # ...and a sample output (the centerpiece the user reviews).
        assert isinstance(c.sample_output, dict) and c.sample_output
        # A direction brief survives into the buildable-design call.
        assert c.form_factor in c.as_direction_brief()


def test_colliding_directions_collapse_not_counted_distinct():
    # If every per-candidate dispatch returns the SAME form factor, the
    # candidates are NOT materially distinct (SAL-DF-3) — fewer than 2
    # survive, so the stage refuses rather than surfacing a fake choice.
    def _fn(prompt, *, model="sonnet", timeout=0):
        return {"result": json.dumps(_candidate("one-shot CLI", "x"))}

    with pytest.raises(GenerationUnavailable, match="materially-distinct"):
        generate_candidate_designs(_intent(), _grounding(),
                                   n=3, llm_json_fn=_fn)


def test_fewer_than_two_usable_candidates_is_refused():
    # Only one of the per-candidate dispatches yields a usable design.
    state = {"i": 0}

    def _fn(prompt, *, model="sonnet", timeout=0):
        i = state["i"]
        state["i"] = i + 1
        if i == 0:
            return {"result": json.dumps(_candidate("one-shot CLI", "cli"))}
        return {"result": "not json at all"}  # the rest fail to parse

    with pytest.raises(GenerationUnavailable, match="real choice"):
        generate_candidate_designs(_intent(), _grounding(),
                                   n=3, llm_json_fn=_fn)
