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

    AC.GR.3 — the milestone-on-the-path fields.  When refinement
    cannot make the user's *whole* aim directly measurable but derives
    a measurable goal ON THE PATH that the user agreed to:
      * `is_milestone` is True (the approved unit is a milestone, not
        the full done);
      * `milestone_toward` records the still-open fuzzy aim the
        milestone is a step toward (so the milestone never silently
        REPLACES the user's aim — the original intent stays visible
        as the open target);
      * `check_in_pending` is True (a check-in is structurally
        re-engaged after the milestone is achieved — the outcome is
        "milestone done, fuzzy aim still open, check-in due", NOT a
        terminal "done").
    AC.GR.1/.4 — `refinement_attempts` is the bounded attempt count
    actually spent (0 when refinement was not entered — a healthy
    derive on the first pass); `refinement_outcome` names which
    refinement leg produced this unit ("none" | "interactive" |
    "self" | "milestone" | "honest-negative") so the per-intent
    re-harden verdict is reconstructable from the outcome alone.
    Defaults keep every pre-refinement caller / test byte-unchanged
    (AC.GR.2 no-regression of the durable path).
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
    is_milestone: bool = False
    milestone_toward: str = ""
    check_in_pending: bool = False
    refinement_attempts: int = 0
    refinement_outcome: str = "none"

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
            "is_milestone": self.is_milestone,
            "milestone_toward": self.milestone_toward,
            "check_in_pending": self.check_in_pending,
            "refinement_attempts": self.refinement_attempts,
            "refinement_outcome": self.refinement_outcome,
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


# --- AC.GR.4: the explicit, finite refinement bound. --------------
# The refinement construct is NOT an unbounded re-derive loop (the
# binding foundation's "do your best to refine" is a *bounded* best —
# the bar is honest, not gamed).  At most this many measurability
# re-derive attempts run before the construct stops: the first pass is
# the interactive-or-self re-derive scoped to the measurability gap,
# the last is the milestone-on-the-path attempt; exhausting the bound
# without a faithful measurable goal OR an agreed milestone yields a
# definite honest-negative (AC.GR.1c / AC.GR.4 — an AC-satisfying
# outcome exactly as a successful refinement is).  Two is the minimum
# that lets the construct try BOTH "refine the whole goal measurable"
# and "fall back to a measurable milestone on the path" before it
# honestly concedes; it is deliberately small (a runaway loop is the
# poisoned-toolkit failure mode this bound prevents).
_REFINE_MAX_ATTEMPTS = 2


def _parse_derive_body(body: str) -> tuple[str, dict]:
    """Split a derive response into (plain_acceptance, machine_check).

    The derive contract is `plain text` + `---` + JSON.  This is the
    SAME fragile-format parse the healthy derive path uses (AC.PBF.1
    base) — factored out ONLY so a refinement re-derive parses its
    response identically to the first derive (no second, divergent
    parser).  A parse miss yields the `_parse_failed` marker exactly
    as before, so the defect detector is unchanged.
    """
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
    return plain_acceptance, mc


def _derive_defects(plain_acceptance: str, mc: dict) -> list[str]:
    """The empty/broken-done defect list (AC.PBF.1 logic, factored).

    Identical predicate to the sealed AC.PBF.1 inline block — an empty
    plain done, an unparsed machine-checkable, or an empty check
    command.  Factored so the refinement construct can ask "did this
    re-derive resolve the measurability defect?" with the SAME
    predicate the honest-refuse terminal used (no divergent notion of
    "broken").
    """
    check_cmd = ""
    if isinstance(mc, dict):
        check_cmd = str(mc.get("check_command") or "").strip()
    defects: list[str] = []
    if not plain_acceptance.strip():
        defects.append("the plain-English 'done' is empty")
    if isinstance(mc, dict) and mc.get("_parse_failed"):
        defects.append("the machine-checkable acceptance failed to parse")
    if not check_cmd:
        defects.append("the machine check command is empty")
    return defects


def _refine_toward_measurable(
    *,
    intent: str,
    prior_plain: str,
    prior_mc: dict,
    prior_reason: str,
    elicit_answer_fn,
    model: str,
    transcript: list[str],
) -> dict:
    """Bounded refine the unmeasurable derive toward measurability.

    The owner's three-tier behaviour, bounded (AC.GR.1/.2/.3/.4):

      1. **Interactive-refine first** (AC.GR.2) — re-ask the user a
         FEW plain measurability-gap questions via the existing
         `elicit_answer_fn` callback (the SAME bounded elicitation
         contract intake already has; the user is never turned into a
         spec author).  When a live user is reachable their answers
         scope a re-derive of a *faithful measurable whole goal*.
      2. **Self-refine** (AC.GR.2) — when no live user is reachable
         (`elicit_answer_fn is None` — the hands-off "just go" case),
         the model self-refines the whole goal into measurable
         form without further user input.
      3. **Milestone-on-the-path** (AC.GR.3) — when the whole aim
         still cannot be made directly measurable, derive a
         *measurable goal on the path* to it; the caller surfaces
         THAT milestone at the single approval gate and, on
         agreement, records it as a milestone toward the still-open
         fuzzy aim with a re-engaged check-in.

    Returns a dict the caller acts on:
      {"kind": "refined"|"milestone"|"honest-negative",
       "plain": str, "mc": dict, "outcome": str,
       "attempts": int, "milestone_toward": str, "reason": str}

    `kind == "refined"`  → a faithful measurable WHOLE goal; caller
        runs the normal approval + faithfulness path on it.
    `kind == "milestone"`→ a measurable milestone on the path; caller
        surfaces it at the gate, sets is_milestone + check_in_pending.
    `kind == "honest-negative"` → the bound was exhausted without a
        measurable goal or an agreed milestone; caller returns a
        definite honest-negative naming the goal class (AC.GR.4 —
        an AC-satisfying outcome, NOT retried, NOT a fake test).

    Bound: at most `_REFINE_MAX_ATTEMPTS` re-derive passes (AC.GR.4).
    Never fabricates a cheap stand-in test (the sealed `ceb629b`
    no-fake property is preserved — refinement re-derives a REAL
    measurable goal/milestone or honestly concedes; it never lowers
    the check to something trivially-true to force a pass).
    """
    transcript.append(
        f"[refine] entering bounded refinement (reason: {prior_reason})"
    )
    attempts = 0

    # --- Tier 1/2: interactive-refine first, else self-refine. -----
    # One bounded measurability-gap clarification.  If a live user is
    # reachable we ask a FEW plain questions about the measurability
    # gap specifically (NOT the original elicitation again — scoped to
    # "what would make 'done' checkable for this"); else we self-refine.
    refine_answers: dict[str, str] = {}
    interactive = elicit_answer_fn is not None
    if interactive:
        gap_prompt = (
            "A non-technical user asked for something whose 'done' "
            f"could not be pinned to a checkable test:\n\n  \"{intent}\"\n\n"
            f"The attempt so far is not measurable because: "
            f"{prior_reason}\n\n"
            "Ask ONLY the few plain questions whose answers would let "
            "you state a concrete, checkable 'done' — what specific "
            "observable result would mean this is actually achieved. "
            "Plain questions a non-technical person answers in a "
            "sentence; do NOT ask them to write a spec. Hard cap: at "
            "most 3 questions. One per line, nothing else."
        )
        env = _claude_json(gap_prompt, model=model)
        raw_gap_q = (env.get("result") or "").strip()
        gap_qs = [q.strip(" -•\t") for q in raw_gap_q.splitlines()
                  if q.strip()][:3]
        transcript.append(f"[refine-elicit] {raw_gap_q}")
        for q in gap_qs:
            refine_answers[q] = elicit_answer_fn(q)
            transcript.append(
                f"[refine-answer] {q} -> {refine_answers[q]}"
            )

    attempts += 1
    answers_block = (
        "\n".join(f"  - {q} -> {a}" for q, a in refine_answers.items())
        if refine_answers else "  (no live user — self-refining)"
    )
    redrive_prompt = (
        "A non-technical user asked for something whose 'done' could "
        f"not be made checkable:\n\n  \"{intent}\"\n\n"
        f"Why the prior attempt was not measurable: {prior_reason}\n"
        f"Prior non-measurable attempt (for context):\n"
        f"  plain: {prior_plain!r}\n"
        f"  check: {str((prior_mc or {}).get('check_command'))!r}\n\n"
        "Clarifying answers (empty if none — then refine it "
        f"yourself):\n{answers_block}\n\n"
        "Re-derive a FAITHFUL, genuinely measurable 'done' for the "
        "WHOLE goal — a check command that exits 0 ONLY when the "
        "user's actual outcome is really achieved (NOT a presence "
        "test for a setup file, NOT a --validate/dry-run flag, NOT "
        "an 'at least one X exists' proxy, NOT an always-true "
        "command). If — and only if — the whole goal genuinely "
        "cannot be made directly measurable even now, instead derive "
        "a measurable goal that is a real step ON THE PATH toward it "
        "(something concretely checkable that genuinely advances the "
        "user toward what they asked).\n\n"
        "Output exactly: plain text, then `---`, then a JSON object "
        "{\"check_command\": <single shell command, exits 0 iff the "
        "thing is really done>, \"spec\": <concise restatement>, "
        "\"is_milestone\": true|false, \"milestone_toward\": <if "
        "is_milestone, one plain sentence naming the still-open "
        "fuzzy aim this is a step toward; else \"\">}."
    )
    env = _claude_json(redrive_prompt, model=model)
    body = (env.get("result") or "").strip()
    transcript.append(f"[refine-derive#{attempts}] {body}")
    plain, mc = _parse_derive_body(body)
    defects = _derive_defects(plain, mc)

    if not defects:
        is_ms = bool(isinstance(mc, dict) and mc.get("is_milestone"))
        toward = ""
        if isinstance(mc, dict):
            toward = str(mc.get("milestone_toward") or "").strip()
        if is_ms:
            # --- Tier 3: a measurable milestone on the path. -------
            transcript.append(
                f"[refine] milestone-on-the-path derived (attempt "
                f"{attempts}); toward fuzzy aim: {toward!r}"
            )
            return {
                "kind": "milestone",
                "plain": plain,
                "mc": mc,
                "outcome": "milestone",
                "attempts": attempts,
                "milestone_toward": toward or intent,
                "reason": "",
            }
        transcript.append(
            f"[refine] refined to a measurable whole goal (attempt "
            f"{attempts})"
        )
        return {
            "kind": "refined",
            "plain": plain,
            "mc": mc,
            "outcome": "interactive" if interactive else "self",
            "attempts": attempts,
            "milestone_toward": "",
            "reason": "",
        }

    # --- Last bounded attempt: force a milestone-on-the-path. ------
    # The whole-goal re-derive still produced an empty/broken result.
    # Spend the remaining bound asking explicitly for a measurable
    # MILESTONE on the path (the binding foundation's explicit "pick a
    # measurable goal on the path" tier) before conceding.
    while attempts < _REFINE_MAX_ATTEMPTS:
        attempts += 1
        ms_prompt = (
            "A non-technical user asked for something whose full "
            f"'done' cannot be made directly checkable:\n\n"
            f"  \"{intent}\"\n\n"
            "Do NOT refuse and do NOT invent a fake/always-true "
            "test. Instead pick ONE measurable goal that is a real "
            "step ON THE PATH toward what they asked — something "
            "concretely checkable whose completion genuinely advances "
            "them toward the fuzzy aim. Output exactly: plain text "
            "describing that milestone in plain English, then `---`, "
            "then JSON {\"check_command\": <single shell command, "
            "exits 0 iff the milestone is really achieved — a REAL "
            "check, not a proxy>, \"spec\": <concise restatement>, "
            "\"is_milestone\": true, \"milestone_toward\": <one plain "
            "sentence naming the still-open fuzzy aim this milestone "
            "is a step toward>}."
        )
        env = _claude_json(ms_prompt, model=model)
        body = (env.get("result") or "").strip()
        transcript.append(f"[refine-milestone#{attempts}] {body}")
        plain, mc = _parse_derive_body(body)
        defects = _derive_defects(plain, mc)
        if not defects:
            toward = ""
            if isinstance(mc, dict):
                toward = str(mc.get("milestone_toward") or "").strip()
            transcript.append(
                f"[refine] milestone-on-the-path derived on the "
                f"bounded fallback (attempt {attempts})"
            )
            return {
                "kind": "milestone",
                "plain": plain,
                "mc": mc if isinstance(mc, dict) else {},
                "outcome": "milestone",
                "attempts": attempts,
                "milestone_toward": toward or intent,
                "reason": "",
            }

    # --- Bound exhausted: definite honest-negative (AC.GR.4). ------
    neg = (
        "Could not refine this request into a measurable goal even "
        "on the path after "
        f"{attempts} bounded refinement attempt(s): "
        + "; ".join(defects)
        + ". This goal class resisted measurement — refusing to "
        "fabricate a cheap stand-in test or loop unbounded "
        "(AC.GR.4: a definite honest-negative is a valid outcome, "
        "not a failure)."
    )
    transcript.append(f"[refine] honest-negative: {neg}")
    return {
        "kind": "honest-negative",
        "plain": prior_plain,
        "mc": prior_mc if isinstance(prior_mc, dict) else {},
        "outcome": "honest-negative",
        "attempts": attempts,
        "milestone_toward": "",
        "reason": neg,
    }


def _judge_faithful(
    *,
    intent: str,
    plain_acceptance: str,
    mc: dict,
    model: str,
    transcript: list[str],
) -> tuple[bool, str]:
    """The INDEPENDENT AC.B.4b / AC.PBF.2 faithfulness judge call.

    Factored VERBATIM out of `derive_acceptance_from_intent` so the
    post-refinement re-judge uses the byte-identical judge (the
    AC.PBF.2-corrected prompt that carries the literal derived check
    command + spec + the adversarial proxy/plumbing question).  The
    judge process is UNCHANGED — same already-independent, already-
    isolated (`_claude_json` → `inject_isolation`), already-either-
    polarity `claude -p` subprocess; only its CALL SITES (now two:
    the first derive, and the post-refinement re-derive) changed, not
    its behaviour.  An unparseable judge → `(False, reason)`, never
    retried (the sealed either-polarity property).
    """
    faith_check_cmd = ""
    faith_spec = ""
    if isinstance(mc, dict):
        faith_check_cmd = str(mc.get("check_command") or "").strip()
        faith_spec = str(mc.get("spec") or "").strip()
    faith_prompt = (
        "Adversarial faithfulness check. A non-technical user "
        f"originally asked:\n\n  \"{intent}\"\n\n"
        "A 'done when' was derived and the user approved it:\n\n"
        f"  \"{plain_acceptance}\"\n\n"
        "The derived 'done' will actually be verified by running "
        "this exact machine check command, and ONLY this command "
        "decides whether the work is accepted:\n\n"
        f"  check command: {faith_check_cmd!r}\n"
        f"  machine spec : {faith_spec!r}\n\n"
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
        return bool(fj.get("faithful")), str(fj.get("reason", ""))
    except json.JSONDecodeError:
        return False, f"faithfulness judge output unparseable: {fb[:200]}"


def freeze_input_from_outcome(outcome: "IntakeOutcome") -> dict:
    """AC.GR.6 — the intake→loop seam read-path (milestone-leg only).

    The honesty of "the user agreed to measurable milestone M and the
    loop verified exactly M" requires the command the loop FREEZES and
    EXECUTES (`verify.FrozenAcceptance.check_argv`, run at
    `orchestrator.py` `verify(...)`) to be PROVABLY derived from the
    `IntakeOutcome.machine_checkable` the user agreed to at the single
    approval gate — NOT a separately hand-authored frozen-spec JSON
    unrelated to intake.  This function is that derivation: it returns
    the `freeze_acceptance(...)` keyword input computed *from the
    approved outcome itself*, so a caller (cli/orchestrator) freezes
    the agreed command rather than an unrelated one.

    The link is a read-path connection ONLY (the milestone leg's §3b
    prerequisite) — it does NOT change how `verify` decides done and
    does NOT touch decompose/dispatch/judge (AC.FOUND.0 untouched).

    Refuses (raises) when the outcome is not a sound freeze source:
    not approved, or no non-empty check command — so a poisoned/empty
    contract can NEVER reach the freeze the loop executes (the AC.PBF.1
    honesty property carried through the seam).  `content` is the
    user-approved plain-language acceptance, so a later
    `FrozenAcceptance.assert_unseen_by` / sha-pin operates on the
    agreed artefact.  `acceptance_id` embeds whether this unit is a
    milestone so the executed-vs-agreed identity is auditable.
    """
    if not isinstance(outcome, IntakeOutcome):
        raise TypeError(
            "freeze_input_from_outcome requires an IntakeOutcome"
        )
    if not outcome.approved:
        raise ValueError(
            "refusing to derive a freeze input from a non-approved "
            "intake outcome — the user never agreed to this unit "
            "(AC.GR.6: agreed-command == executed-command, provably)."
        )
    mc = outcome.machine_checkable or {}
    check_cmd = str(mc.get("check_command") or "").strip()
    if not check_cmd:
        raise ValueError(
            "refusing to derive a freeze input from an empty check "
            "command — an empty/poisoned contract must never reach "
            "the command the loop executes (AC.GR.6 / AC.PBF.1)."
        )
    kind = "milestone" if outcome.is_milestone else "whole"
    return {
        "acceptance_id": f"intake-{kind}",
        "content": outcome.plain_language_acceptance,
        "check_argv": ["/bin/sh", "-c", check_cmd],
        "held_out_argv": None,
    }


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

    # --- AC.GR.1: the honest-refuse terminal is now a refinement
    # ENTRY, not an exit.  The AC.PBF.1 defect predicate (factored to
    # `_derive_defects`) still detects an empty plain done / empty
    # check command / unparsed machine-checkable — the sealed `ceb629b`
    # honesty base is preserved (still NO silent `approved=True` on an
    # empty contract, still NO auto-retry rubber-stamp).  What changes:
    # instead of an immediate terminal `approved=False`, intake enters
    # the BOUNDED refinement construct (interactive-refine → self-refine
    # → milestone-on-the-path → definite honest-negative).  A bare
    # immediate refusal with NO refinement attempt no longer happens on
    # the real-model path; the deterministic structural path
    # (`run_model=False`) never has defects so it never enters
    # refinement — the durable AC.B.2 leg is byte-unchanged (AC.GR.2).
    refine_attempts = 0
    refine_outcome = "none"
    is_milestone = False
    milestone_toward = ""

    defects = _derive_defects(plain_acceptance, mc)
    if defects and run_model:
        pre_reason = (
            "Could not pin down a checkable 'done' for this request — "
            + "; ".join(defects)
        )
        res = _refine_toward_measurable(
            intent=intent,
            prior_plain=plain_acceptance,
            prior_mc=mc if isinstance(mc, dict) else {},
            prior_reason=pre_reason,
            elicit_answer_fn=elicit_answer_fn,
            model=model,
            transcript=transcript,
        )
        refine_attempts = res["attempts"]
        refine_outcome = res["outcome"]
        if res["kind"] == "honest-negative":
            # AC.GR.4 — a definite, evidence-naming honest-negative is
            # an AC-satisfying outcome exactly as a refinement is.  NOT
            # a fabricated cheap test, NOT an unbounded loop.
            return IntakeOutcome(
                original_intent=intent,
                under_specification=list(under_specification),
                elicited_questions=list(questions),
                elicited_answers=answers,
                plain_language_acceptance=plain_acceptance,
                machine_checkable=mc if isinstance(mc, dict) else {},
                approved=False,
                faithful=False,
                faithfulness_reason=res["reason"],
                transcript=transcript,
                refinement_attempts=refine_attempts,
                refinement_outcome="honest-negative",
            )
        # A refined whole goal OR a milestone on the path — both flow
        # through the SAME single approval gate + faithfulness check
        # below (the user approves exactly one unit; D-UNIT intact).
        plain_acceptance = res["plain"]
        mc = res["mc"]
        if res["kind"] == "milestone":
            is_milestone = True
            milestone_toward = res["milestone_toward"]
    elif defects:
        # Deterministic structural path can never reach here (the
        # placeholder derive has no defects); this branch is the
        # belt-and-braces honest refuse for a non-run_model defect,
        # preserving the AC.PBF.1 no-silent-approve property.
        reason = (
            "Could not pin down a checkable 'done' for this request — "
            + "; ".join(defects)
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
    # AC.GR.3: when this unit is a milestone-on-the-path, the gate is
    # framed as a milestone the loop will aim at FIRST (not the full
    # done) so the user's plain-language agreement is to *that
    # milestone* — surfaced here, not silently substituted.  In true
    # hands-off mode (`approval_fn` is the pre-authorised "just go"
    # standing agreement) this is the user's standing agreement to a
    # sensibly-derived milestone (D-GR-2).
    gate_text = plain_acceptance
    if is_milestone:
        gate_text = (
            f"{plain_acceptance}\n\n(This is a measurable milestone on "
            f"the way to: {milestone_toward}. I will aim at this first, "
            f"then check back to see what else is needed.)"
        )
    approved = bool(approval_fn(gate_text))
    transcript.append(
        f"[approval] approved={approved} "
        f"(milestone={is_milestone})"
    )

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
    #
    # AC.GR.1: when the judge returns `faithful=False` (a proxy/
    # plumbing check slipped through) AND refinement has not yet been
    # spent, that is a measurability failure, not a dead end — it
    # routes into the SAME bounded refinement construct (one entry,
    # one bound shared with the derive-defect entry).
    if run_model and approved:
        faithful, reason = _judge_faithful(
            intent=intent, plain_acceptance=plain_acceptance,
            mc=mc, model=model, transcript=transcript,
        )
        if not faithful and refine_outcome == "none":
            res = _refine_toward_measurable(
                intent=intent,
                prior_plain=plain_acceptance,
                prior_mc=mc if isinstance(mc, dict) else {},
                prior_reason=(
                    "the derived check is a proxy/plumbing stand-in "
                    f"(not faithful): {reason}"
                ),
                elicit_answer_fn=elicit_answer_fn,
                model=model,
                transcript=transcript,
            )
            refine_attempts = res["attempts"]
            refine_outcome = res["outcome"]
            if res["kind"] == "honest-negative":
                return IntakeOutcome(
                    original_intent=intent,
                    under_specification=list(under_specification),
                    elicited_questions=list(questions),
                    elicited_answers=answers,
                    plain_language_acceptance=plain_acceptance,
                    machine_checkable=mc if isinstance(mc, dict) else {},
                    approved=False,
                    faithful=False,
                    faithfulness_reason=res["reason"],
                    transcript=transcript,
                    refinement_attempts=refine_attempts,
                    refinement_outcome="honest-negative",
                )
            plain_acceptance = res["plain"]
            mc = res["mc"]
            if res["kind"] == "milestone":
                is_milestone = True
                milestone_toward = res["milestone_toward"]
            assert_plain_language(plain_acceptance)
            gate_text = plain_acceptance
            if is_milestone:
                gate_text = (
                    f"{plain_acceptance}\n\n(This is a measurable "
                    f"milestone on the way to: {milestone_toward}. I "
                    f"will aim at this first, then check back to see "
                    f"what else is needed.)"
                )
            approved = bool(approval_fn(gate_text))
            transcript.append(
                f"[approval-refined] approved={approved} "
                f"(milestone={is_milestone})"
            )
            if approved:
                faithful, reason = _judge_faithful(
                    intent=intent, plain_acceptance=plain_acceptance,
                    mc=mc, model=model, transcript=transcript,
                )
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
        is_milestone=is_milestone,
        milestone_toward=milestone_toward,
        check_in_pending=is_milestone and approved,
        refinement_attempts=refine_attempts,
        refinement_outcome=refine_outcome,
    )
