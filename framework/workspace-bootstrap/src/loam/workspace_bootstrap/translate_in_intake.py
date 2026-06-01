# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""N3 translate-in intake — the operating loop (infer -> propose -> verify ->
learn) run on a BRAND-NEW user (slice N3 / AC.ONINTAKE.*).

This is the front door of the prime directive: per-user-tuned translation
STARTS here. For a brand-new user loam's inference is at its most fallible, so
the loop's VERIFICATION step is load-bearing above all (D-1 (a), RATIFIED):
the inferred end-intent is a HYPOTHESIS surfaced for confirmation, NEVER
silently written.

**The idea-quality continuum (the owner's framing — sets the effort the system
expends INVERSELY to the user's own idea-richness):**

  - CLEAR idea  -> capture it + go straight to the leverage close. NO fallback
                   ladder, NO research. (effort: minimal)
  - PARTIAL idea -> lean into what they said, draw out more, then propose.
  - NOTHING / overwhelmed -> the fallback ladder (describe-your-work ->
                   mine-the-role -> [opt-in] deep role-research). This is the
                   ONLY path that can reach the deep-research seam. (effort:
                   maximal — NEED-triggered, not a preference offered to everyone)

**The three load-bearing shapes (content of the loop's infer-leg):**

  1. the single STOP/START close (AC.ONINTAKE.1) — ONE concrete thing the user
     wants to STOP (slows them from what matters) or START (critical but
     can't/won't self-start). ONE thing — a list stresses people (the
     no-interrogation HARD constraint).
  2. the propose + verify gate (AC.ONINTAKE.2/.3) — an inferred end-intent is
     PROPOSED and CONFIRMED before any seed is written; reject vs confirm yields
     DIFFERENT outcomes (a print-and-ignore fake cannot pass).
  3. the over-reach guard (AC.ONINTAKE.4, D-3 (a)) — propose at most ONE level
     up from the literal ask, opt-in, never auto-built.

  ...all converging on the demonstrate-leverage close (AC.ONINTAKE.6): >=1
  concrete, person-SPECIFIC leverage idea referencing what the user said.

**Method is the builder's call (ODD).** The intake is a turn-by-turn
conversation driven by an injected ``Answerer`` (the same protocol the existing
capability ritual uses) — tests script it; the production CLI reads stdin. The
exact question WORDING/COUNT is deliberately NOT pinned (pinning it would be
method-in-AC); the AC pins bounded + closing-on-one + verified-before-seed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from .deep_role_research import (
    ResearchProvider,
    RoleResearchResult,
    default_research_provider,
)


class Answerer(Protocol):
    """Ask the user one question, return the raw answer (mirrors the existing
    onboarding ritual's ``Answerer`` protocol so the two compose under one
    ``loam init-intake`` orchestration). Tests inject a scripted instance; the
    production CLI implements via stdin."""

    def __call__(self, slug: str, prompt: str) -> str:  # pragma: no cover
        ...


class IdeaRichness(Enum):
    """Where the user sits on the idea-quality continuum (sets the effort)."""

    CLEAR = "clear"
    PARTIAL = "partial"
    EMPTY = "empty"


class Disposition(Enum):
    """STOP something, or START something — the single-close axis."""

    STOP = "stop"
    START = "start"
    UNKNOWN = "unknown"


# Phrases that signal an idea-vacuum user (can't name a stop/start thing). The
# continuum routes these to the fallback ladder; everything else is treated as
# at least a PARTIAL idea.
_EMPTY_SIGNALS = (
    "i can't think",
    "i cant think",
    "nothing",
    "no idea",
    "not sure",
    "dunno",
    "don't know",
    "dont know",
    "overwhelmed",
    "i'm new",
    "im new",
    "where do i start",
    "no clue",
    "",
)

# Regex signals for an idea-vacuum reply that survive natural-phrasing noise —
# inserted adverbs ("even"/"really"/"honestly") and conversational filler must
# NOT break the match the way the literal substring "don't know" did on
# "I don't even know where to start" (AC.INTAKE-VACUUM.1). Matched against a
# punctuation-normalised, whitespace-collapsed copy of the answer.
# Lead-sensitive: the negated-knowledge tell only signals a vacuum when the user
# OPENS with it. Matched against the opening clause only (see _looks_empty).
_EMPTY_REGEXES_LEAD = (
    # "(don't|can't|couldn't) [adverbs] (know|think|say|tell)" — the negated-
    # knowledge core, tolerant of intervening adverbs ("don't EVEN know").
    r"\b(do|does|did|don|dont|can|cant|could|couldn|would|wouldn|not)('?t)?\b"
    r"(\s+\w+){0,3}\s+(know|knew|think|say|tell|sure|idea|clue)\b",
    r"\bnot\s+sure\s+what\b",
    r"\b(i'?m|im)\s+(new|overwhelmed|lost)\b",
)

# Anywhere: unambiguous vacuum tells that mark a non-answer wherever they appear.
_EMPTY_REGEXES_ANYWHERE = (
    # "no idea / clue where to (start|begin)".
    r"\b(idea|clue)\b(\s+\w+){0,3}\s+(start|begin)\b",
    r"\bwhere (to|do i) (start|begin)\b",
    # "(just|i just|kind of) do my job" — the "nobody's asked me to think about
    # this" non-answer shape the adjuster produced.
    r"\b(just|kinda|kind of)\b(\s+\w+){0,3}\s+do(ing)?\s+my\s+job\b",
)

# HARD vacuum override: an explicit "nothing is broken / it's just everything /
# constant" tell marks a genuine idea-vacuum even when an activity LIST is
# present — the paralegal who lists tasks but says "I don't have a thing that's
# broken, it's just constant" IS a vacuum (route to the ladder + opt-in
# research). Beats the single-pain demotion below.
_HARD_VACUUM_REGEXES = (
    r"\bnothing('?s)?\s+(broken|wrong)\b",
    r"\bdon'?t\s+(really\s+)?have a thing\b",
    r"\bit'?s\s+(just\s+)?(more\s+)?(just\s+)?(sort of\s+)?constant\b",
    r"\bjust\s+everything\b",
    r"\beverything,?\s+all day\b",
)

# Single-pain demotion: a reply that SAYS "I don't know" but then singles out
# ONE concrete pain ("the thing that eats my day is the write-ups") is a
# day-derived PARTIAL idea, not a vacuum — it must NOT route to the deep-research
# ladder (the featherlight invariant: only a true idea-vacuum reaches research).
# This fixes the day-derived variant reaching research after the vacuum-classifier
# widening (AC.INTAKE-VACUUM.1).
_DERIVABLE_PAIN_REGEXES = (
    r"\beats? (up )?my (day|afternoon|evening|morning|time)\b",
    r"\bit eats\b",
    r"\bpiles? up\b",
    r"\bpile up\b",
    r"\bgrinding through\b",
    r"\bthe thing that\b(\s+\w+){0,4}\s+(is|eats|kills|gets|takes)\b",
    r"\btwo hours\b",
)

# Phrases that, in a stop/start answer, signal the user has a CLEAR concrete
# idea (rich + specific) — route straight to capture + the leverage close.
_CLEAR_SIGNALS_MIN_WORDS = 4

# Affirmative / negative tokens for the verify gate + opt-in gates.
_YES = (
    "y", "yes", "yeah", "yep", "yup", "yea", "sure", "ok", "okay", "confirm",
    "correct", "right", "absolutely", "definitely", "exactly", "totally",
)
_NO = ("n", "no", "nope", "nah", "wrong", "incorrect")

# Leading conversational filler a human emits before the actual yes/no
# ("Ha, ... yes", "Oh, sure", "I mean, yeah"). When the first word-token is one
# of these, the affirmation parser looks PAST it to the next meaningful token.
_AFFIRM_FILLER = frozenset(
    {
        "ha", "haha", "heh", "oh", "well", "hmm", "hmmm", "um", "uh", "so",
        "like", "i", "mean", "lol", "ah", "okay", "ok", "yeah",
    }
)
# An explicit agreement pivot that promotes a trailing affirmation to a clean yes
# ("Ha, that's a mouthful — but yes, basically!"). Only these promote an
# embedded affirmation — a bare "sure"/"yes" buried in "not sure"/"for sure"
# does NOT (those are caught by _CONTRA_SIGNALS or simply not pivoted).
_AGREE_PIVOTS = ("but yes", "but yeah", "but sure", "okay yes", "ok yes", "well yes")


@dataclass
class LeverageIdea:
    """A concrete, person-specific leverage idea (the demonstrate-leverage
    artefact — AC.ONINTAKE.6). ``references`` carries the user's stated item /
    role so a specificity probe can distinguish it from generic boilerplate."""

    text: str
    references: str  # the stop/start item or role this idea is built on

    def is_specific_to(self, token: str) -> bool:
        return token.lower() in self.text.lower() or token.lower() in (
            self.references.lower()
        )


@dataclass
class ProposedEndIntent:
    """The inferred end-intent the intake PROPOSES (distinct from the raw
    answers — the infer + propose legs; AC.ONINTAKE.2). The over-reach guard
    (AC.ONINTAKE.4) keeps ``one_level_up_offer`` an OPT-IN, never auto-seeded."""

    slug: str
    disposition: Disposition
    objective_text: str  # the proposed healthy-enablement shape
    raw_answer: str  # what the user literally said (for the not-a-verbatim-echo check)
    one_level_up_offer: str | None = None  # the opt-in "shall I make it recurring?"
    clean_item: str = ""  # the user's item with a leading disposition verb stripped


@dataclass
class IntakeResult:
    """Terminal state of a completed translate-in intake.

    The orchestrator reads this to drive the seed-writer; tests assert the
    operating-loop behaviour (continuum route / verify gate / leverage close /
    deep-research gate) against it.
    """

    richness: IdeaRichness
    proposal: ProposedEndIntent | None = None
    confirmed: bool = False
    # The CONFIRMED end-intent that gets seeded (None until the verify gate
    # passes; differs from ``proposal`` when the user corrected it).
    seeded_objective_slug: str | None = None
    seeded_objective_text: str | None = None
    leverage_ideas: list[LeverageIdea] = field(default_factory=list)
    # Fallback-ladder telemetry (AC.ONINTAKE.5 / AC.ONDEEP.1).
    reached_describe_work: bool = False
    described_role: str | None = None
    offered_deep_research: bool = False
    invoked_deep_research: bool = False
    research_result: RoleResearchResult | None = None
    transcript: list[tuple[str, str]] = field(default_factory=list)  # (slug, answer)

    @property
    def has_leverage_idea(self) -> bool:
        return bool(self.leverage_ideas)


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return "-".join(s.split("-")[:6]) or "first-objective"


def _tokens(answer: str) -> list[str]:
    """Lower-cased word-tokens with surrounding punctuation stripped.

    Real humans punctuate their affirmations — "Yeah, that'd help",
    "yes, basically!", "Sure." Splitting on whitespace then stripping
    non-alphanumerics off each word recovers the affirmation/negation intent
    regardless of leading or trailing punctuation (AC.INTAKE-AFFIRM.1)."""
    out = []
    for w in answer.strip().lower().split():
        t = re.sub(r"[^a-z0-9']", "", w).strip("'")
        if t:
            out.append(t)
    return out


def _leading_polarity(answer: str) -> str:
    """Classify the reply's affirmation polarity: "yes" / "no" / "" (neither).

    Punctuation-tolerant + filler-skipping: a reply that opens with a hedge
    interjection ("Ha, that's a mouthful — but yes, basically!") is still a
    confirmation, because the parser skips leading filler tokens and reads the
    first meaningful yes/no. A reply with a contradiction pivot ("not quite",
    "instead") is NOT a clean yes even if it contains "yes" — it routes to the
    correction branch. A substantive rewrite with no leading yes/no token
    ("actually I want X") returns "" so the caller treats it as a correction
    (AC.INTAKE-AFFIRM.1)."""
    toks = _tokens(answer)
    if not toks:
        return ""
    low = " ".join(toks)
    # The first NON-filler token is the strongest signal.
    for t in toks:
        if t in _YES:
            return "yes"
        if t in _NO:
            return "no"
        if t in _AFFIRM_FILLER:
            continue
        break  # a substantive non-filler token that is neither yes nor no
    # First meaningful token was substantive. An explicit agreement PIVOT
    # ("but yes, basically!") promotes it to a clean yes — even when the user
    # tacks on a restatement ("…I just want to stop X"), because the pivot is the
    # strong confirm signal. Absent a pivot, any hedge / contradiction signal
    # ("not sure", "sort of", "I want X") routes it to the correction branch — a
    # bare affirmation word buried in "not sure"/"for sure" is NOT a confirmation.
    if any(p in low for p in _AGREE_PIVOTS):
        return "yes"
    return ""


def _is_yes(answer: str) -> bool:
    return _leading_polarity(answer) == "yes"


def _is_no(answer: str) -> bool:
    return _leading_polarity(answer) == "no"


def _looks_empty(answer: str) -> bool:
    a = answer.strip().lower()
    if a == "":
        return True
    # Punctuation-normalised copy so "I don't even know where to start…" matches
    # the negated-knowledge regex the literal substring "don't know" missed
    # (AC.INTAKE-VACUUM.1). Apostrophes are preserved (don't / can't); other
    # punctuation collapses to spaces.
    norm = re.sub(r"[^a-z0-9']+", " ", a).strip()
    lead = " ".join(norm.split()[:12])
    # A vacuum SIGNAL from any source: a literal phrase, a lead-sensitive
    # negated-knowledge tell (opening clause only, so a substantive role
    # description with a late aside is NOT empty), or an unambiguous anywhere tell.
    has_signal = (
        any(sig and sig in a for sig in _EMPTY_SIGNALS if sig)
        or any(re.search(rx, lead) for rx in _EMPTY_REGEXES_LEAD)
        or any(re.search(rx, norm) for rx in _EMPTY_REGEXES_ANYWHERE)
    )
    if not has_signal:
        return False
    # An explicit "nothing's broken / it's just constant" tell is a true vacuum
    # even amid an activity list (the paralegal shape).
    if any(re.search(rx, norm) for rx in _HARD_VACUUM_REGEXES):
        return True
    # A single concrete derivable pain demotes the reply to a day-derived PARTIAL
    # idea (the claims-adjuster shape) so it does NOT reach the research ladder
    # (the featherlight invariant — only a true idea-vacuum reaches research).
    if any(re.search(rx, norm) for rx in _DERIVABLE_PAIN_REGEXES):
        return False
    return True


def _classify_richness(answer: str) -> IdeaRichness:
    """Route the user on the idea-quality continuum from their stop/start answer."""
    if _looks_empty(answer):
        return IdeaRichness.EMPTY
    word_count = len(answer.split())
    if word_count >= _CLEAR_SIGNALS_MIN_WORDS:
        return IdeaRichness.CLEAR
    return IdeaRichness.PARTIAL


def _detect_disposition(answer: str) -> Disposition:
    a = answer.lower()
    # Prefer the FIRST signal that appears so "stop doing X to start Y" reads stop.
    stop_at = min(
        (a.find(t) for t in ("stop", "quit", "less", "avoid", "hate", "tired of")
         if t in a),
        default=-1,
    )
    start_at = min(
        (a.find(t) for t in ("start", "begin", "should", "want to", "need to", "more")
         if t in a),
        default=-1,
    )
    if stop_at == -1 and start_at == -1:
        return Disposition.UNKNOWN
    if stop_at == -1:
        return Disposition.START
    if start_at == -1:
        return Disposition.STOP
    return Disposition.STOP if stop_at <= start_at else Disposition.START


# Leading conversational filler a real human opens with before the actual item
# ("Oh, that's an easy one —", "Honestly?", "Well,", "Ha,"). Stripped before the
# intent is distilled so the proposal reads as the item, not the preamble.
_LEAD_FILLER = re.compile(
    r"^(oh|ok|okay|well|so|hmm+|ha+|um+|uh+|honestly|look|see|right|yeah|yep|"
    r"i mean|you know|i guess|i think|i'd say|i would say|let me think|"
    r"that'?s (an? )?(easy|hard|good|tough|tricky)( one)?|"
    r"that'?s a (mouthful|good question|hard one))\b[\s,.!?:;—–-]*",
    flags=re.IGNORECASE,
)
# Trailing emphatic filler a human appends ("… is killing me", "… every evening",
# "… I just want it done") that is not part of the distilled item.
_TRAIL_FILLER = re.compile(
    r"\b(is|are|'?s)\s+(killing|driving|exhausting|destroying|wrecking)\s+me\b.*$",
    flags=re.IGNORECASE,
)
# A temporal / "sitting-there" preamble that precedes the actual action in a
# narrated reply ("every single night I'm sitting at my kitchen table writing up
# listing descriptions" → "writing up listing descriptions"). Dropped so the
# distilled phrase leads with the ACTION, not the scene-setting (AC.INTAKE-ECHO.1).
_ACTION_PREAMBLE = re.compile(
    r"^(every (single )?(night|evening|day|morning|afternoon|week)s?|"
    r"each (night|evening|day|morning|week)|all day|most of my day|honestly|"
    r"i'?m (always |constantly |usually |just )?)"
    r"[\w,'\s]*?\b"
    r"(sitting|stuck|grinding|spending|buried|stuck)\b[\w,'\s]*?\b"
    r"(?=(writing|drafting|formatting|chasing|reconciling|filing|tracking|"
    r"doing|making|handling|managing|answering|pulling|building|preparing))",
    flags=re.IGNORECASE,
)
# An explicit intent span the user states inside a correction / narration
# ("…I want to stop writing those listing descriptions myself…"). When present,
# the span after "want to" / "stop" / "start" / "to" is the distilled item.
_WANT_SPAN = re.compile(
    r"\b(?:i\s+(?:just\s+)?want\s+(?:to|you\s+to)|i'?d\s+(?:love|like)\s+to|"
    r"i\s+need\s+to)\s+(?P<span>.+?)"
    r"(?=[.!?;,]|—|–|\s+so\s+|\s+because\s+|\s+and\s+(?:have|get)\b|$)",
    flags=re.IGNORECASE,
)
_DISTILL_MAX_WORDS = 12


def _strip_lead_filler(text: str) -> str:
    """Iteratively peel stacked leading filler ("Oh, that's an easy one")."""
    prev = None
    cur = text.strip()
    while cur != prev:
        prev = cur
        cur = _LEAD_FILLER.sub("", cur).strip().lstrip(",").strip()
    return cur


def _distill_intent(answer: str) -> str:
    """Reduce a multi-sentence stop/start reply to a SHORT intent phrase
    (AC.INTAKE-ECHO.1) — never echo the whole reply into the proposal slot.

    Deterministic distillation: split on clause boundaries, drop leading clauses
    that are pure conversational filler ("Oh, that's an easy one"), take the
    first content-bearing clause, drop trailing emphatic filler ("… is killing
    me"), and cap at a bounded word budget. A reply that is already a short
    phrase passes through essentially unchanged."""
    text = answer.strip().rstrip(".!?").strip()
    # If the user states an explicit intent ("I want to stop writing those listing
    # descriptions"), that span IS the item — prefer it over clause heuristics.
    want = _WANT_SPAN.search(text)
    if want:
        span = want.group("span").strip().rstrip(",").strip()
        # Drop a leading disposition verb the enablement framing re-adds later.
        span = re.sub(
            r"^(stop|start|quit|begin|avoid)\s+(doing\s+|to\s+)?",
            "",
            span,
            flags=re.IGNORECASE,
        ).strip() or span
        span = _ACTION_PREAMBLE.sub("", span).strip()
        words = span.split()
        if 0 < len(words) <= _DISTILL_MAX_WORDS:
            return span
        if words:
            return " ".join(words[:_DISTILL_MAX_WORDS])
    clauses = [c.strip() for c in re.split(r"[.!?;]|—|–|\s-\s", text) if c.strip()]
    if not clauses:
        clauses = [text]
    # Drop leading clauses that are nothing but conversational filler.
    core = ""
    for clause in clauses:
        stripped = _strip_lead_filler(clause)
        if stripped:
            core = stripped
            break
    if not core:
        # Everything read as filler — fall back to the lead-stripped whole text.
        core = _strip_lead_filler(text) or text
    # Drop a temporal / "sitting-there" preamble so the ACTION leads.
    core = _ACTION_PREAMBLE.sub("", core).strip()
    core = _TRAIL_FILLER.sub("", core).strip().rstrip(",").strip()
    words = core.split()
    if len(words) > _DISTILL_MAX_WORDS:
        core = " ".join(words[:_DISTILL_MAX_WORDS])
    return core or text


def _propose_end_intent(answer: str, disposition: Disposition) -> ProposedEndIntent:
    """Infer + PROPOSE a healthy-enablement shape over the raw answer (NOT a
    verbatim echo — AC.ONINTAKE.2), bounded by the over-reach guard
    (AC.ONINTAKE.4: the recurring framework is an OPT-IN offer, never the
    proposal that gets seeded)."""
    # Distill a SHORT intent phrase first (AC.INTAKE-ECHO.1) so a real human's
    # multi-sentence reply does not get pasted verbatim into the proposal slot.
    distilled = _distill_intent(answer)
    # Strip a leading disposition verb the user already said, so the proposal
    # doesn't read "stop stop X" / "start start Y" (copy-edit; the verb is added
    # back by the enablement framing below).
    core_clean = re.sub(
        r"^(stop|start|quit|begin|avoid)\s+(doing\s+|to\s+)?",
        "",
        distilled,
        flags=re.IGNORECASE,
    ).strip() or distilled
    objective_text = (
        f"Help the user stop {core_clean} so it stops getting in the way of the "
        f"work that matters to them"
        if disposition == Disposition.STOP
        else f"Help the user reliably {core_clean} — the thing they know is "
        f"critical but find hard to self-start"
    )
    # Over-reach guard: ONE level up = offer to make it repeatable, OPT-IN only.
    # Quote the DISTILLED item (not the raw multi-sentence reply) — AC.INTAKE-ECHO.1.
    one_level_up = (
        f"Want me to make '{core_clean}' a repeatable thing loam handles for you, "
        f"rather than a one-off? (entirely optional — say no and we keep it simple)"
    )
    return ProposedEndIntent(
        slug=_slugify(core_clean),
        disposition=disposition,
        objective_text=objective_text,
        raw_answer=answer.strip(),
        one_level_up_offer=one_level_up,
        clean_item=core_clean,
    )


def _leverage_from_intent(intent: ProposedEndIntent) -> LeverageIdea:
    """Build a person-SPECIFIC leverage idea referencing the user's stated item
    (AC.ONINTAKE.6 — distinguishable from generic boilerplate)."""
    core = (intent.clean_item or intent.raw_answer).strip().rstrip(".")
    if intent.disposition == Disposition.STOP:
        text = (
            f"Here's what loam can do for you: take '{core}' off your plate — "
            f"loam can watch for it and handle it so you never have to think "
            f"about it again."
        )
    else:
        text = (
            f"Here's what loam can do for you: turn '{core}' into something that "
            f"happens reliably without you having to push it forward each time."
        )
    return LeverageIdea(text=text, references=core)


# Filler that leads a multi-sentence role description before the actual title
# ("I'm a paralegal …", "I work as a nurse …", "So basically I'm a teacher …").
_ROLE_TITLE = re.compile(
    r"\b(?:i'?m|i am|i work as|i'?m working as|my (?:job|role|title) is|"
    r"they call me)\s+(?:an?\s+)?(?P<title>[a-z][a-z' -]*?)"
    r"(?=\s+(?:at|in|for|with|so|and|but|—|–|,|;|\.|$))",
    flags=re.IGNORECASE,
)
_ROLE_MAX_WORDS = 4


def _extract_role_noun(role: str) -> str:
    """Reduce a (possibly multi-sentence) role description to a concise role NOUN
    (AC.INTAKE-ROLE.1) — never paste the whole job-description blob into the
    ``{role}`` slot. A reply that is already a bare title ("civil engineer")
    passes through unchanged."""
    text = role.strip().rstrip(".!?").strip()
    m = _ROLE_TITLE.search(text)
    if m:
        title = m.group("title").strip().rstrip(",").strip()
        if title:
            return " ".join(title.split()[-_ROLE_MAX_WORDS:])
    # No "I'm a X" frame — take the first clause and cap it so a long
    # description still collapses to a short noun-ish phrase.
    first_clause = re.split(r"[.!?;,]|—|–|\s-\s", text)[0].strip()
    words = first_clause.split()
    if len(words) > _ROLE_MAX_WORDS:
        first_clause = " ".join(words[:_ROLE_MAX_WORDS])
    return first_clause or text


def _leverage_from_role(role: str) -> LeverageIdea:
    """A person-specific leverage idea mined DIRECTLY from a described role
    (the ladder's mine-the-role rung — AC.ONINTAKE.5, before any deep research).

    The ``{role}`` slot is filled with the extracted role NOUN, not the raw
    multi-sentence description (AC.INTAKE-ROLE.1)."""
    noun = _extract_role_noun(role)
    text = (
        f"Here's what loam can do for a {noun}: take the repetitive parts of "
        f"that work — the status updates, the formatting, the chasing — and "
        f"handle them for you, so you spend your time on the part only a "
        f"{noun} can do."
    )
    return LeverageIdea(text=text, references=noun)


# --------------------------------------------------------------------
# Question wording (the builder's call per ODD — NOT pinned in any AC).
# --------------------------------------------------------------------

_Q_STOP_START = (
    "To get started, let's find ONE thing. What's one thing you'd love to "
    "STOP doing (because it slows you down from the work that matters), or "
    "START doing (because you know it's important but it's hard to get to)? "
    "Just one thing — whatever comes to mind."
)
_Q_CONFIRM = "Did I get that right? (yes / no — or tell me what to change)"
_Q_ONE_LEVEL_UP = ""  # filled from the proposal's opt-in offer at ask time
_Q_DESCRIBE_WORK = (
    "No worries — that's a hard question cold. Let's come at it differently: "
    "what do you do? Your job title + the day-to-day, or for personal use, "
    "what you'd most like a capable assistant to help with."
)
_Q_DEEP_OPT_IN = (
    "I can do a deeper dive — research what makes someone in your role most "
    "effective, what tends to get people promoted, and which tools could give "
    "you an edge — then bring you specific ideas. Want me to? (yes / no)"
)


def run_translate_in_intake(
    *,
    answerer: Answerer,
    research_provider: ResearchProvider | None = None,
) -> IntakeResult:
    """Run the operating loop on a brand-new user; return what to seed.

    The flow (the idea-quality continuum):

      1. Ask the single STOP/START question (AC.ONINTAKE.1).
      2. Classify richness (CLEAR / PARTIAL / EMPTY).
         - EMPTY -> the fallback ladder (describe-work -> mine-role ->
           [opt-in] deep-research). ONLY this path can reach the research seam
           (AC.ONDEEP.1 featherlight invariant).
         - CLEAR / PARTIAL -> infer + PROPOSE an end-intent (AC.ONINTAKE.2),
           surface the over-reach OPT-IN offer (AC.ONINTAKE.4), then run the
           VERIFY gate (AC.ONINTAKE.3): confirm vs reject yields DIFFERENT seed.
      3. Close on >=1 person-specific leverage idea (AC.ONINTAKE.6).

    The result carries the CONFIRMED end-intent to seed (or None if the user
    rejected outright and gave no usable correction) + the leverage idea(s).
    """
    provider = research_provider or default_research_provider()
    result = IntakeResult(richness=IdeaRichness.EMPTY)

    def ask(slug: str, prompt: str) -> str:
        ans = answerer(slug, prompt)
        result.transcript.append((slug, ans))
        return ans

    # --- 1. The single stop/start question. ---
    raw = ask("stop_start", _Q_STOP_START)
    result.richness = _classify_richness(raw)

    # --- 2a. Idea-vacuum -> the fallback ladder. ---
    if result.richness is IdeaRichness.EMPTY:
        return _run_fallback_ladder(ask, result, provider)

    # --- 2b. CLEAR / PARTIAL -> infer, propose, verify. ---
    disposition = _detect_disposition(raw)
    proposal = _propose_end_intent(raw, disposition)
    result.proposal = proposal

    # Surface the inferred proposal for VERIFICATION before any commit.
    confirm = ask(
        "confirm_proposal",
        f"It sounds like you want: {proposal.objective_text}.\n{_Q_CONFIRM}",
    )
    if _is_yes(confirm):
        result.confirmed = True
        result.seeded_objective_slug = proposal.slug
        result.seeded_objective_text = proposal.objective_text
    elif _is_no(confirm):
        # Outright reject with no correction -> nothing confirmed, nothing seeded.
        result.confirmed = False
    else:
        # A correction ("no, simpler" / "yes, and also...") REPLACES the seed —
        # the seed is gated on what the user VERIFIED, not the raw inference.
        # DISTILL the correction too (AC.INTAKE-ECHO.1) so the seed + the
        # leverage close carry the corrected ITEM, not a verbatim paste of the
        # whole reply (the residual the smoke re-run surfaced on variant A).
        corrected = _distill_intent(confirm) or confirm.strip()
        result.confirmed = True
        result.seeded_objective_slug = _slugify(corrected)
        result.seeded_objective_text = (
            f"Help the user with: {corrected} (as they corrected the proposal)"
        )
        # The leverage idea must reference the CORRECTED item.
        proposal = ProposedEndIntent(
            slug=result.seeded_objective_slug,
            disposition=disposition,
            objective_text=result.seeded_objective_text,
            raw_answer=corrected,
        )
        result.proposal = proposal

    # --- 3. The demonstrate-leverage close (only on a confirmed intent). ---
    if result.confirmed and result.proposal is not None:
        result.leverage_ideas.append(_leverage_from_intent(result.proposal))

    return result


def _run_fallback_ladder(
    ask,
    result: IntakeResult,
    provider: ResearchProvider,
) -> IntakeResult:
    """The graceful fallback ladder for an idea-vacuum user (AC.ONINTAKE.5).

    describe-your-work -> mine-the-role for ideas -> [OPT-IN] deep role-research.
    Each rung is reached ONLY if the prior didn't land. The deep-research seam
    (AC.ONDEEP.1) is reached ONLY from here, ONLY with real role detail AND an
    explicit opt-in — the featherlight invariant.
    """
    role_answer = ask("describe_work", _Q_DESCRIBE_WORK)
    result.reached_describe_work = True

    if _looks_empty(role_answer):
        # Still nothing — surface a gentle generic starting idea and stop (never
        # force the deep research on a user who gave no role detail; AC.ONDEEP.1).
        result.leverage_ideas.append(
            LeverageIdea(
                text=(
                    "Here's a simple place to start: many people have loam take "
                    "over their daily status update or inbox triage — small, "
                    "concrete, and it frees real time. We can start there."
                ),
                references="default-starter",
            )
        )
        return result

    # Reduce a (possibly multi-sentence) description to a concise role NOUN so
    # every downstream slot (idea text, seeded objective, research call) carries
    # the noun, never the raw blob (AC.INTAKE-ROLE.1).
    role = _extract_role_noun(role_answer)
    result.described_role = role
    # Mine the role DIRECTLY for ideas first (before ever offering the research).
    result.leverage_ideas.append(_leverage_from_role(role))
    # Seed a baseline objective from the described role so the run is useful.
    result.confirmed = True
    result.seeded_objective_slug = _slugify(role + "-leverage")
    result.seeded_objective_text = (
        f"Help the user (a {role}) find and offload the highest-leverage "
        f"repetitive parts of their work"
    )

    # The opt-in deepening — offered ONLY now (real role detail in hand).
    result.offered_deep_research = True
    opt_in = ask("deep_opt_in", _Q_DEEP_OPT_IN)
    if _is_yes(opt_in):
        result.invoked_deep_research = True
        research = provider.research_role(role)
        result.research_result = research
        for idea in research.as_leverage_ideas():
            result.leverage_ideas.append(LeverageIdea(text=idea, references=role))

    return result
