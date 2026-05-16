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
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from ._isolation import inject_isolation, isolated_env


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
#
# AC.PBF.3: each entry is matched as a *jargon token*, not a naive
# substring of `text.lower()`.  The naive-substring form crashed the
# whole intake non-deterministically on benign plain English — the
# acceptance-ID prefix "AC." (lowercased "ac.") matched the substring
# inside the ordinary word "Mac." (and "ODD" matched "odd", "seal"
# matched "sealed"/"reveal", etc.).  Each forbidden term is compiled
# to a word-boundary-anchored pattern so an ordinary word that merely
# *contains* the substring does NOT trip, while a genuine jargon token
# still does.  The acceptance-ID term is matched as its real ID shape
# (`AC.` immediately followed by an alphanumeric — the `AC.B.4` form),
# never the bare `ac.` inside ordinary words.  Behaviour is
# deterministic: the same plain "done" either always raises or never
# raises, independent of incidental phrasing.
_JARGON_PATTERNS = (
    # Acceptance-ID token: `AC.` followed by an alnum (AC.B.4, AC.PBF.1)
    # — NOT the `ac.` ending an ordinary word ("Mac.", "iMac.").
    ("AC.<id>", re.compile(r"\bAC\.[A-Za-z0-9]")),
    ("acceptance criterion",
     re.compile(r"\bacceptance criteri(?:on|a)\b", re.IGNORECASE)),
    ("pytest", re.compile(r"\bpytest\b", re.IGNORECASE)),
    ("exit code", re.compile(r"\bexit code\b", re.IGNORECASE)),
    ("sha256", re.compile(r"\bsha-?256\b", re.IGNORECASE)),
    ("manifest", re.compile(r"\bmanifest\b", re.IGNORECASE)),
    # `seal` as a loam-process jargon token — the seal verb/noun in its
    # amendment/manifest/commit collocation, NOT the ordinary English
    # verb ("seal the envelope", "seal the deal", "revealed",
    # "sealant").  The jargon sense always co-occurs with the loam
    # objects it acts on; the bare ordinary verb is plain English a
    # non-technical "done" may legitimately contain.
    ("seal",
     re.compile(
         r"\bseal(?:s|ed|ing)?\b[\s\w]{0,24}"
         r"\b(?:amendment|manifest|commit|component|cycle)\b"
         r"|\b(?:amendment|manifest|component|cycle)\s+seal",
         re.IGNORECASE)),
    # `ODD` the methodology acronym — uppercase token, NOT the ordinary
    # word "odd"/"oddly".
    ("ODD", re.compile(r"\bODD\b")),
    ("machine-checkable",
     re.compile(r"\bmachine[- ]checkable\b", re.IGNORECASE)),
)


def assert_plain_language(text: str) -> None:
    """AC.B.3 guard: refuse if the user-facing acceptance carries jargon.

    AC.PBF.3 — token-boundary matching, deterministic, no naive
    substring.  Ordinary words that merely contain a forbidden
    substring ("Mac." → "ac.", "odd" → "ODD", "revealed" → "seal")
    do NOT raise; genuine jargon tokens still do.
    """
    hits = [label for label, pat in _JARGON_PATTERNS if pat.search(text)]
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

    AC.TPI.2/.3/.4: telegram-poller-isolated.  The argv is wrapped with
    the empty-strict-MCP isolation (so this spawned `claude` cannot load
    the telegram plugin → cannot spawn a competing `bun server.ts` that
    SIGTERMs a concurrently-running operator session's single-consumer
    poller) and the env is scrubbed of the bot-token / API-key
    spellings.  Reuses the PROVEN subloam-driver mechanism via
    `_isolation` (no new isolation machinery).  The argv shape is
    unchanged — only the isolation flags + env scrub are added.
    """
    argv = inject_isolation([
        "claude", "-p", prompt,
        "--model", model,
        "--output-format", "json",
        "--permission-mode", "bypassPermissions",
    ])
    proc = subprocess.run(
        argv,
        capture_output=True, text=True, timeout=timeout,
        env=isolated_env(),
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

    # --- AC.PBF.1: refuse an empty/broken done BEFORE approval. ----
    # The derive step is format-fragile (it asks the model for plain
    # text + `---` + JSON; when the model deviates the parser yields an
    # empty plain "done" and/or an empty check command and/or an
    # unparsed machine-checkable).  Previously the approval gate ran on
    # that fragment and `bool(approval_fn(""))` could still return True,
    # silently freezing a poisoned/empty contract (hardening I2/I7).
    # The fix is an honest refuse-with-reason (D-PBF-A, adopted — NOT
    # an auto-retry: a silent retry re-introduces the rubber-stamp risk
    # by another path).  A non-approved outcome carrying the specific
    # reason is produced *before* the approval gate can be reached, so
    # an empty/garbage derivation can never surface as `approved=True`.
    _check_cmd = ""
    if isinstance(mc, dict):
        _check_cmd = str(mc.get("check_command") or "").strip()
    _derive_defects: list[str] = []
    if not plain_acceptance.strip():
        _derive_defects.append("the plain-English 'done' is empty")
    if isinstance(mc, dict) and mc.get("_parse_failed"):
        _derive_defects.append(
            "the machine-checkable acceptance failed to parse")
    if not _check_cmd:
        _derive_defects.append("the machine check command is empty")
    if _derive_defects:
        reason = (
            "Could not pin down a checkable 'done' for this request — "
            + "; ".join(_derive_defects)
            + ". Refusing rather than approving an empty or unparsed "
            "contract (AC.PBF.1)."
        )
        transcript.append(f"[refuse] {reason}")
        return IntakeOutcome(
            original_intent=intent,
            under_specification=list(under_specification),
            elicited_questions=list(questions),
            elicited_answers=answers,
            plain_language_acceptance=plain_acceptance,
            machine_checkable=mc if isinstance(mc, dict) else {},
            approved=False,
            faithful=False,
            faithfulness_reason=reason,
            transcript=transcript,
        )

    assert_plain_language(plain_acceptance)  # AC.B.3 hard guard

    # --- AC.B.3: exactly ONE plain-English approval gate. ----------
    approved = bool(approval_fn(plain_acceptance))
    transcript.append(f"[approval] approved={approved}")

    # --- AC.B.4b: INDEPENDENT faithfulness check. ------------------
    # AC.PBF.2 — the judge must assess the GROUND-TRUTH artefact (the
    # actual derived machine check command + spec), not only the
    # friendly plain-English summary.  Previously this prompt
    # interpolated only `intent` + `plain_acceptance`; the machine
    # check command (`mc["check_command"]` / `mc["spec"]`) — a live
    # local computed 30+ lines above — was never handed to the judge,
    # so the loop's own judge was structurally blind to its own
    # canonical failure mode: a cheap proxy/plumbing check (a presence
    # test for a one-time setup file, a `--validate` dry-run flag,
    # "≥1 filter exists") that exits 0 while the user's real outcome is
    # unmet (hardening I3/I6, both rubber-stamped).  This IS the
    # information-trust-ordering inversion: judge the ground truth, not
    # the loop's own self-narrated summary.  The judge process itself
    # is unchanged — same already-independent, already-isolated,
    # already-either-polarity `claude -p` subprocess; only WHAT it sees
    # and WHAT it is asked changes.
    if run_model and approved:
        _faith_check_cmd = ""
        _faith_spec = ""
        if isinstance(mc, dict):
            _faith_check_cmd = str(mc.get("check_command") or "").strip()
            _faith_spec = str(mc.get("spec") or "").strip()
        faith_prompt = (
            "Adversarial faithfulness check. A non-technical user "
            f"originally asked:\n\n  \"{intent}\"\n\n"
            "A 'done when' was derived and the user approved it:\n\n"
            f"  \"{plain_acceptance}\"\n\n"
            "The derived 'done' will actually be verified by running "
            "this exact machine check command, and ONLY this command "
            "decides whether the work is accepted:\n\n"
            f"  check command: {_faith_check_cmd!r}\n"
            f"  machine spec : {_faith_spec!r}\n\n"
            "Assess BOTH the plain 'done when' AND, adversarially, the "
            "machine check command above. The dangerous failure mode: "
            "the check command is a cheap PROXY or PLUMBING stand-in "
            "(a presence test for a one-time setup file, a dry-run / "
            "--validate flag, an 'at least one X exists' test, an "
            "always-true command) that exits 0 while the user's ACTUAL "
            "outcome is NOT achieved. Ask explicitly: could this exact "
            "command exit 0 while the user would still say 'that's not "
            "what I asked for'? If the plain 'done' reads fine but the "
            "machine command underneath would pass without the real "
            "outcome, that is NOT faithful. Answer strictly as JSON: "
            "{\"faithful\": true|false, \"reason\": <one sentence>}."
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
