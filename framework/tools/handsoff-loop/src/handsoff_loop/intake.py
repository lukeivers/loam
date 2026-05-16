"""Intent -> checkable-done intake leg.

Maps to:
  AC.B.1 — fuzzy-intent input (under-specified plain language; the
           under-specification is documented).
  AC.B.2 — elicit-the-minimum gate (only the missing decisions, in
           plain language, bounded — the user is NOT turned into a
           spec author).
  AC.B.3 — plain-language acceptance + exactly ONE plain-English
           approval gate before any build (no jargon/AC-IDs/spec
           syntax surfaced).
  AC.B.4 — derived-done is machine-checkable AND faithful: an
           independent check that the derived acceptance, if met,
           satisfies a reasonable reading of the original ask
           (guards the checkable-but-WRONG failure).

D-UNIT (ratified): one unit = one user-approved plain-language
objective with one frozen machine-checkable acceptance set; the loop
decomposes internally but the unit the user sees/approves is the
whole objective.  This module produces exactly that single unit.

The faithfulness check (AC.B.4) is an INDEPENDENT model judge — a
real `claude -p` subprocess (NO API key, default Sonnet) — that
NEVER sees the derived machine-checkable form's authoring rationale;
it is shown only (original plain-language intent, derived
plain-language acceptance) and asked, adversarially, whether meeting
the derived acceptance would satisfy a reasonable reading of the
original.  Its verdict is evidence for AC.B.5 (Phase B end-test) and
is reported either polarity, never retried to green.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class IntakeOutcome:
    """The single approved unit produced from fuzzy intent.

    `plain_language_acceptance` is the human-facing "done when: X
    works, Y is saved, Z opens" (AC.B.3 — no jargon).
    `machine_checkable` is the loop-consumable form (a check command
    + spec text, AC.B.4a).  `faithful` + `faithfulness_reason` carry
    the independent AC.B.4b verdict.  `elicited_questions` /
    `under_specification` document AC.B.1 / AC.B.2.
    """

    original_intent: str
    under_specification: list[str]
    elicited_questions: list[str]
    elicited_answers: dict[str, str]
    plain_language_acceptance: str
    machine_checkable: dict
    approved: bool
    faithful: bool
    faithfulness_reason: str
    transcript: list[str] = field(default_factory=list)

    def as_evidence(self) -> dict:
        return {
            "original_intent": self.original_intent,
            "under_specification": self.under_specification,
            "elicited_questions": self.elicited_questions,
            "elicited_answers": self.elicited_answers,
            "plain_language_acceptance": self.plain_language_acceptance,
            "machine_checkable": self.machine_checkable,
            "approved": self.approved,
            "faithful": self.faithful,
            "faithfulness_reason": self.faithfulness_reason,
        }


# Jargon the plain-language acceptance must NOT surface to the user
# (AC.B.3).  Surfacing any of these is a structural B.3 failure.
_JARGON_FORBIDDEN = (
    "AC.",
    "acceptance criterion",
    "pytest",
    "exit code",
    "sha256",
    "manifest",
    "seal",
    "ODD",
    "machine-checkable",
)


def assert_plain_language(text: str) -> None:
    """AC.B.3 guard: refuse if the user-facing acceptance carries jargon."""
    low = text.lower()
    hits = [j for j in _JARGON_FORBIDDEN if j.lower() in low]
    if hits:
        raise ValueError(
            f"Plain-language acceptance surfaced jargon {hits!r} — "
            f"AC.B.3 violation; the user must see plain English only."
        )


def _claude_json(prompt: str, *, model: str = "sonnet",
                  timeout: int = 300) -> dict:
    """Run a real `claude -p --output-format json` subprocess.

    NO Anthropic API key — real binary, default Sonnet.  Returns the
    parsed JSON envelope (carries `result` text + `total_cost_usd` /
    `usage` so cost is MEASURED, D-COST-BAND).
    """
    proc = subprocess.run(
        [
            "claude", "-p", prompt,
            "--model", model,
            "--output-format", "json",
            "--permission-mode", "bypassPermissions",
        ],
        capture_output=True, text=True, timeout=timeout,
    )
    raw = proc.stdout.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"result": raw, "_parse_failed": True,
                "_stderr": proc.stderr[-500:]}


def derive_acceptance_from_intent(
    *,
    intent: str,
    under_specification: list[str],
    approval_fn,
    elicit_answer_fn=None,
    model: str = "sonnet",
    run_model: bool = True,
) -> IntakeOutcome:
    """Turn fuzzy plain-language intent into one approved unit.

    AC.B.1..B.4 end to end.

    `approval_fn(plain_text) -> bool` is the SINGLE plain-English
    approval gate (AC.B.3) — exactly one, before any build.
    `elicit_answer_fn(question) -> str` answers the bounded
    elicit-the-minimum questions (AC.B.2); if None, elicitation is
    recorded but unanswered (used by the deterministic structural
    test).  `run_model=False` exercises the structure deterministically
    without spending a real sub-agent (the phase-B end-test sets it
    True for the real run).
    """
    transcript: list[str] = []

    # --- AC.B.2: elicit ONLY the missing decisions, bounded. -------
    if run_model:
        elicit_prompt = (
            "A non-technical user said, in plain language:\n\n"
            f"  \"{intent}\"\n\n"
            "This is under-specified. List ONLY the few missing "
            "decisions you must know to define a clear, checkable "
            "'done' — phrased as plain questions a non-technical "
            "person can answer in a sentence. Do NOT ask them to "
            "write a spec. Hard cap: at most 4 questions. Output one "
            "question per line, nothing else."
        )
        env = _claude_json(elicit_prompt, model=model)
        raw_q = (env.get("result") or "").strip()
        questions = [q.strip(" -•\t") for q in raw_q.splitlines()
                     if q.strip()][:4]
        transcript.append(f"[elicit] {raw_q}")
    else:
        questions = [
            "What should it do when given empty input?",
            "Where should the result be saved?",
        ]

    answers: dict[str, str] = {}
    for q in questions:
        if elicit_answer_fn is not None:
            answers[q] = elicit_answer_fn(q)
            transcript.append(f"[elicit-answer] {q} -> {answers[q]}")

    # --- Derive the unit: plain-language + machine-checkable. -------
    if run_model:
        derive_prompt = (
            "Original plain-language request from a non-technical "
            f"user:\n\n  \"{intent}\"\n\n"
            "Answers to clarifying questions:\n"
            + "\n".join(f"  - {q} -> {a}" for q, a in answers.items())
            + "\n\nProduce TWO things, separated by a line `---`:\n"
            "1. A plain-English 'done when:' statement a "
            "non-technical person can read (no jargon, no code, no "
            "test names) — what working software will visibly do.\n"
            "2. A JSON object: {\"check_command\": <a single shell "
            "command that exits 0 iff done>, \"spec\": <concise "
            "machine-checkable restatement>}.\n"
            "Output exactly: plain text, then `---`, then the JSON."
        )
        env = _claude_json(derive_prompt, model=model)
        body = (env.get("result") or "").strip()
        transcript.append(f"[derive] {body}")
        if "---" in body:
            plain_part, json_part = body.split("---", 1)
        else:
            plain_part, json_part = body, "{}"
        plain_acceptance = plain_part.strip()
        try:
            mc = json.loads(json_part.strip().strip("`").lstrip("json"))
        except json.JSONDecodeError:
            mc = {"check_command": "", "spec": json_part.strip(),
                  "_parse_failed": True}
    else:
        plain_acceptance = (
            "Done when: the program reads the file, produces the "
            "expected result for normal input, and clearly handles "
            "empty input without crashing."
        )
        mc = {"check_command": "python3 verify_test.py",
              "spec": "deterministic structural placeholder"}

    assert_plain_language(plain_acceptance)  # AC.B.3 hard guard

    # --- AC.B.3: exactly ONE plain-English approval gate. ----------
    approved = bool(approval_fn(plain_acceptance))
    transcript.append(f"[approval] approved={approved}")

    # --- AC.B.4b: INDEPENDENT faithfulness check. ------------------
    if run_model and approved:
        faith_prompt = (
            "Adversarial faithfulness check. A non-technical user "
            f"originally asked:\n\n  \"{intent}\"\n\n"
            "A 'done when' was derived and the user approved it:\n\n"
            f"  \"{plain_acceptance}\"\n\n"
            "Question: if software EXACTLY met that derived 'done "
            "when' and NOTHING more, would it satisfy a reasonable "
            "reading of the user's ORIGINAL request? Be adversarial — "
            "look for checkable-but-wrong gaps (the derived 'done' is "
            "met yet the user would say 'that's not what I asked "
            "for'). Answer strictly as JSON: {\"faithful\": "
            "true|false, \"reason\": <one sentence>}."
        )
        env = _claude_json(faith_prompt, model=model)
        fb = (env.get("result") or "").strip()
        transcript.append(f"[faithfulness] {fb}")
        try:
            fj = json.loads(fb.strip("`").lstrip("json").strip())
            faithful = bool(fj.get("faithful"))
            reason = str(fj.get("reason", ""))
        except json.JSONDecodeError:
            faithful = False
            reason = f"faithfulness judge output unparseable: {fb[:200]}"
    else:
        faithful = approved
        reason = ("deterministic structural path — real faithfulness "
                  "judge runs only in the phase-B end-test")

    return IntakeOutcome(
        original_intent=intent,
        under_specification=list(under_specification),
        elicited_questions=list(questions),
        elicited_answers=answers,
        plain_language_acceptance=plain_acceptance,
        machine_checkable=mc,
        approved=approved,
        faithful=faithful,
        faithfulness_reason=reason,
        transcript=transcript,
    )
