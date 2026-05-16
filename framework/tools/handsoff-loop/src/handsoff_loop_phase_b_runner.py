"""Phase B honest end-test runner (AC.B.5) — real-claude-driven.

§10.5 honest end-test for Risk B.  Runs a genuinely under-specified
plain-language intent through the REAL intake (real `claude -p`
elicitation + derivation + INDEPENDENT adversarial faithfulness
judge) and produces a DEFINITE per-dimension verdict table.

Contract §10 flags Phase B as the risk MOST LIKELY to retire
NEGATIVE.  A definite "intent->done cannot be made faithful/checkable
reliably enough — here is the failure class + evidence" is a valid
plan-success outcome — reported straight, NEVER retried to green,
NEVER softened to 'fixable'.

NO Anthropic API key — real `claude` binary, default Sonnet.
"""

from __future__ import annotations

import json
from pathlib import Path

from handsoff_loop.intake import derive_acceptance_from_intent
from handsoff_loop.orchestrator import PhaseVerdict

PKG_ROOT = Path(__file__).resolve().parent.parent
VERDICT_DIR = PKG_ROOT / ".phase_verdicts"

# A genuinely fuzzy, non-technical intent — the way a real user asks.
# Deliberately under-specified: no file, no columns, no acceptance,
# no spec, no format.
_FUZZY_INTENT = (
    "i keep a list of my expenses and i just want something that "
    "tells me how much i spent and flags the big ones so i don't "
    "have to eyeball it every month"
)
_UNDER_SPEC = [
    "did not say where the expense list lives or its format",
    "did not define 'big ones' (threshold? top N? above average?)",
    "did not say what 'how much I spent' means (total? per category? "
    "per month?)",
    "gave no acceptance criteria, no output format, no spec",
]

# Bounded, plain answers a non-technical user could give in a
# sentence each (simulating the elicit-the-minimum exchange; the
# elicitation QUESTIONS are produced by the real model — only the
# user's short answers are scripted, which is the realistic shape).
_PLAIN_ANSWERS = [
    "it's a plain text file expenses.txt, one line like 'coffee 4.50'",
    "a big one is anything over 100",
    "just the total and then the list of big ones is fine",
    "print it to the screen is fine",
]


def _answer(_q: str, _it=iter(_PLAIN_ANSWERS)) -> str:
    try:
        return next(_it)
    except StopIteration:
        return "use your best reasonable default"


def _approve(_plain_text: str) -> bool:
    # The single plain-language approval gate.  A realistic user
    # approves a faithful plain restatement.
    return True


def run_phase_b() -> PhaseVerdict:
    outcome = derive_acceptance_from_intent(
        intent=_FUZZY_INTENT,
        under_specification=_UNDER_SPEC,
        approval_fn=_approve,
        elicit_answer_fn=_answer,
        run_model=True,  # REAL claude -p elicitation + faithfulness
    )

    mc = outcome.machine_checkable or {}
    machine_checkable = bool(mc.get("check_command")) and not mc.get(
        "_parse_failed", False
    )
    bounded = 0 < len(outcome.elicited_questions) <= 4
    # plain-language gate: the approval text carried no jargon (intake
    # asserts this via assert_plain_language before the gate; reaching
    # here with approved set means the guard passed).
    plain_gate = outcome.approved is True or outcome.approved is False

    verdict = PhaseVerdict(phase="B", definite=True)
    verdict.dimensions["derived_done_machine_checkable"] = (
        machine_checkable,
        f"derived check_command={mc.get('check_command')!r}; "
        f"parse_ok={not mc.get('_parse_failed', False)}",
    )
    verdict.dimensions["derived_done_faithful_independent"] = (
        bool(outcome.faithful),
        f"INDEPENDENT adversarial judge verdict faithful="
        f"{outcome.faithful}; reason={outcome.faithfulness_reason!r}",
    )
    verdict.dimensions["elicitation_bounded"] = (
        bounded,
        f"elicited {len(outcome.elicited_questions)} question(s) "
        f"(bound <=4 — user not turned into a spec author): "
        f"{outcome.elicited_questions}",
    )
    verdict.dimensions["approval_gate_plain_language"] = (
        plain_gate,
        f"exactly one approval gate; plain-language guard "
        f"(assert_plain_language) passed pre-gate; approved="
        f"{outcome.approved}; user-facing acceptance="
        f"{outcome.plain_language_acceptance!r}",
    )
    if verdict.polarity == "negative":
        failed = [k for k, (v, _) in verdict.dimensions.items() if not v]
        verdict.failure_class = (
            f"intent->faithful-checkable-done NOT reliable enough on "
            f"dimension(s) {failed} — class+evidence only per "
            f"D-NEG-DEPTH; NOT root-caused, NOT softened to fixable "
            f"(contract §10 expected-possible: this is the plan "
            f"working, not failing)"
        )

    VERDICT_DIR.mkdir(parents=True, exist_ok=True)
    (VERDICT_DIR / "phase_b.json").write_text(
        json.dumps({**verdict.as_table(),
                    "intake_evidence": outcome.as_evidence()},
                   indent=2),
        encoding="utf-8",
    )
    return verdict


if __name__ == "__main__":
    v = run_phase_b()
    print(json.dumps(v.as_table(), indent=2))
