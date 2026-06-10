"""Per-request live intent understanding (S1 — AC.REQ.*).

The general build-from-intent path's FIRST stage: a vague build-shaped
ask, in the user's own words, is read LIVE (one bounded spawn-isolated
``claude -p`` call) and turned into:

  * an inferred end-intent surfaced back in plain language for
    confirmation — derived from THAT ask, never canned (AC.REQ.1);
  * a stated objective that echoes the ask's specifics (AC.REQ.3 —
    no objective text exists anywhere in pipeline source; two
    different asks produce two different objectives);
  * a bounded list of meaningful plain-language questions ONLY when
    the ask leaves a build-shaping decision genuinely open — an
    unambiguous ask proceeds with ZERO questions; never a spec
    interview (AC.REQ.2);
  * a proposed form factor (clickable app / command tool / background
    service) in plain language, surfaced at the confirm (AC.GEN.3's
    confirm half lives on this output).

Composes the sealed machinery (Lens 1): the model call goes through
``intake._claude_json`` — the SAME spawn-isolated, env-scrubbed,
subscription-routed ``claude -p`` primitive every other intake call
uses (AC.TPI.2/.3/.4 carried through; NO Anthropic SDK / API key).
The sealed first-run ``intent_extract`` seam fires at onboarding
intake only; THIS module is the per-request leg the plan's S1 names.

Honesty contract: when the live read fails (binary absent, timeout,
unparseable output) this stage raises
:class:`RequestUnderstandingUnavailable` — a build is never started
on an intent loam did not actually understand, and the failure is
surfaced plainly, never silently absorbed (the protection floor:
no inventing things).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from .intake import _claude_json

# AC.REQ.2 — the bounded cap on meaningful questions.  Never a spec
# interview: at most this many, and only when a build-shaping decision
# is genuinely open.
MAX_MEANINGFUL_QUESTIONS = 3

# The single generous wall-clock ceiling for the one bounded
# understanding call (terminal on timeout — the pipeline surfaces the
# failure; there is no retry path in this module).
UNDERSTAND_TIMEOUT_S = 300


class RequestUnderstandingUnavailable(RuntimeError):
    """The live intent read could not produce a usable understanding.

    Raised on dispatch failure / timeout / unparseable output.  The
    pipeline surfaces this plainly and does NOT build — starting a
    build on an un-understood intent would be the silent-invention
    failure the protection floor forbids.
    """


@dataclass(frozen=True)
class RequestIntent:
    """The live read of one build-shaped ask (AC.REQ.1/.2/.3).

    ``inferred_intent`` is the plain-language end-intent surfaced back
    for confirmation.  ``objective`` is the stated build objective
    derived from THIS ask (it echoes the ask's specifics).
    ``questions`` is the bounded list of meaningful questions —
    EMPTY when the ask is unambiguous (both halves of AC.REQ.2 are
    binding).  ``form_factor`` / ``form_factor_plain`` carry the
    proposed deliverable shape for the confirm (AC.GEN.3).
    ``ambiguous`` records whether the model found a build-shaping
    decision genuinely open.
    """

    ask: str
    inferred_intent: str
    objective: str
    questions: list[str] = field(default_factory=list)
    form_factor: str = ""
    form_factor_plain: str = ""
    ambiguous: bool = False

    def as_evidence(self) -> dict:
        return {
            "ask": self.ask,
            "inferred_intent": self.inferred_intent,
            "objective": self.objective,
            "questions": list(self.questions),
            "form_factor": self.form_factor,
            "form_factor_plain": self.form_factor_plain,
            "ambiguous": self.ambiguous,
        }


# The one bounded understanding prompt.  It carries the user's RAW ask
# verbatim — the inference is derived live from THAT ask (AC.REQ.1);
# no objective text, no domain assumption, no canned inference exists
# here (AC.REQ.3 / AC.GEN.2: this prompt is domain-blind).
_UNDERSTAND_PROMPT = """\
You are the intent-understanding step of a build pipeline. A user typed
this ask, in their own words:

\"\"\"{ask}\"\"\"

Read it and return ONLY a JSON object (no prose, no code fence) with
EXACTLY these keys:

  - "inferred_intent": 1-3 plain-language sentences stating what they
    actually want built and the end it serves — specific to THIS ask,
    echoing its concrete details in plain words a non-technical person
    would recognise as their own request. Never generic boilerplate.
  - "objective": one sentence stating the build objective, carrying
    the ask's specifics (the data, the task, the outcome they named).
  - "questions": a JSON array of plain-language questions — ONLY
    questions whose answers genuinely change what gets built (a
    build-shaping decision the ask leaves open). If the ask is clear
    enough to build from, return an EMPTY array. Never ask the user to
    write a spec; never ask about technology choices they would not
    care about. At most {max_q} questions, fewer is better.
  - "form_factor": one of "app" (something they click around in),
    "cli" (a command they run), or "service" (something that runs on
    its own) — your best read of the right shape for THIS ask.
  - "form_factor_plain": one plain sentence saying what that shape
    means for them (e.g. "you'll get a small program you run on a
    folder of files, and it writes the cleaned-up list next to them").

Honesty rules: infer only what the ask supports; where you are
guessing, that is exactly what a question is for. Do not invent
capabilities or data the user never mentioned.
"""


def _parse_understanding(ask: str, result_text: str) -> RequestIntent:
    """Parse the model's JSON read into a :class:`RequestIntent`.

    Tolerates a code fence; anything that does not yield a non-empty
    inferred intent + objective raises
    :class:`RequestUnderstandingUnavailable` (never a silent default —
    AC.REQ.1's inference is live or the stage honestly fails).
    """
    text = (result_text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise RequestUnderstandingUnavailable(
            f"intent read not JSON: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise RequestUnderstandingUnavailable("intent read not an object")

    inferred = str(payload.get("inferred_intent", "") or "").strip()
    objective = str(payload.get("objective", "") or "").strip()
    if not inferred or not objective:
        raise RequestUnderstandingUnavailable(
            "intent read produced an empty inference or objective — "
            "refusing to build on an un-understood ask"
        )

    raw_q = payload.get("questions") or []
    if not isinstance(raw_q, list):
        raw_q = []
    questions = [str(q).strip() for q in raw_q if str(q).strip()]
    # AC.REQ.2 — the bound is structural, not advisory.
    questions = questions[:MAX_MEANINGFUL_QUESTIONS]

    return RequestIntent(
        ask=ask,
        inferred_intent=inferred,
        objective=objective,
        questions=questions,
        form_factor=str(payload.get("form_factor", "") or "").strip(),
        form_factor_plain=str(
            payload.get("form_factor_plain", "") or "").strip(),
        ambiguous=bool(questions),
    )


def understand_request(
    ask: str,
    *,
    model: str = "sonnet",
    llm_json_fn=None,
    timeout: int = UNDERSTAND_TIMEOUT_S,
) -> RequestIntent:
    """Live per-request intent understanding (AC.REQ.1/.2/.3).

    ONE bounded model call on the raw ask.  ``llm_json_fn`` is the
    injectable dispatch seam (tests inject a deterministic double;
    production uses the sealed spawn-isolated ``_claude_json``).  The
    returned :class:`RequestIntent` carries the plain-language confirm
    surface, the derived objective, and the bounded questions.

    Raises :class:`RequestUnderstandingUnavailable` on any dispatch or
    parse failure — the pipeline surfaces it plainly; there is no
    silent fallback to a canned understanding.
    """
    if not (ask or "").strip():
        raise RequestUnderstandingUnavailable(
            "empty ask — nothing to understand"
        )
    dispatch = llm_json_fn if llm_json_fn is not None else _claude_json
    prompt = _UNDERSTAND_PROMPT.format(
        ask=ask.strip(), max_q=MAX_MEANINGFUL_QUESTIONS
    )
    try:
        envelope = dispatch(prompt, model=model, timeout=timeout)
    except RequestUnderstandingUnavailable:
        raise
    except Exception as exc:  # noqa: BLE001 — any dispatch failure is honest
        raise RequestUnderstandingUnavailable(
            f"intent-understanding dispatch failed: {exc}"
        ) from exc
    if not isinstance(envelope, dict):
        raise RequestUnderstandingUnavailable(
            "intent-understanding dispatch returned a non-envelope"
        )
    return _parse_understanding(ask.strip(), envelope.get("result") or "")


def build_confirm_text(
    intent: RequestIntent, answers: dict[str, str] | None = None
) -> str:
    """The plain-language confirm surfaced back to the user (AC.REQ.1).

    Built entirely from the live read (plus any answers the user gave
    to the meaningful questions) — no canned objective text lives here
    (AC.REQ.3).  The form-factor proposal is surfaced in plain words
    (AC.GEN.3's confirm half).
    """
    parts = [intent.inferred_intent.strip()]
    if intent.form_factor_plain:
        parts.append(intent.form_factor_plain.strip())
    if answers:
        noted = "; ".join(
            f"{a.strip()}" for a in answers.values() if a.strip()
        )
        if noted:
            parts.append(f"Taking into account what you told me: {noted}.")
    parts.append("Is that what you want? I'll build exactly that.")
    return "\n\n".join(p for p in parts if p)
