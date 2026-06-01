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


# A describe_work answer is a PURE non-answer only when it is SHORT and carries
# no role/task content at all ("I don't know", "nothing comes to mind", "I'm not
# sure"). A genuine role description that hedges ("I'm a paralegal — cite-checking
# … but I can't point to one thing") is NOT a pure non-answer: it has real role
# detail to mine. The describe_work rung gates on this (NOT the strict stop/start
# `_looks_empty`, which over-fired on the hedging — Bug-3 rerun3 regression).
_PURE_NON_ANSWER = re.compile(
    r"^\s*(?:uh+|um+|oh|well|honestly|i\s+mean)?[\s,]*"
    r"(?:i\s+(?:really\s+)?(?:don'?t|do\s+not)\s+know|"
    r"i'?m\s+not\s+sure|no\s+idea|nothing(?:\s+comes\s+to\s+mind)?|"
    r"not\s+sure|i\s+can'?t\s+think\s+of\s+anything|i\s+dunno)"
    r"[\s,.!?]*$",
    flags=re.IGNORECASE,
)


def _looks_like_pure_non_answer(answer: str) -> bool:
    """True only when the describe_work answer is a CONTENTLESS non-answer (no
    role noun, no named task) — a short 'I don't know' with nothing to mine. A
    role description that names a job/tasks (even while hedging) is NOT pure."""
    a = answer.strip()
    if not a:
        return True
    if _PURE_NON_ANSWER.match(a):
        return True
    # If a role noun or named task is extractable, there IS content to mine.
    if _named_task_from_description(a):
        return False
    # Short replies with a negated-knowledge tell and no extractable role are
    # pure non-answers; long descriptive replies are not.
    return len(a.split()) <= 8 and bool(re.search(r"\b(don'?t|do not)\s+know\b", a.lower()))


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
    # A BARE difficulty-assessment fragment a human emits after a lead dash
    # ("Oh, easy — writing listing descriptions"): once "Oh," is peeled the
    # residual "easy"/"simple"/"hard" is itself filler, not the item.
    r"(easy|simple|hard|tough|tricky|good question)|"
    r"that'?s a (mouthful|good question|hard one))\b[\s,.!?:;—–-]*",
    flags=re.IGNORECASE,
)
# A clause that, after lead-filler stripping, reduces to nothing but a
# difficulty-assessment word ("easy", "the easy one") carries no item — the
# clause loop skips it and reads the NEXT content-bearing clause (the Bug-1
# regression the rerun3 surfaced on the "Oh, easy — writing listing" opener).
_PURE_DIFFICULTY = re.compile(
    r"^(the\s+)?(easy|simple|hard|tough|tricky)(\s+one)?$",
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
# A want-span is NEGATED when the asserted want is "to NOT do X" / "to not have
# to X myself" — the user is asserting they want X done FOR them, not that they
# want to keep doing X. The negated span must distill the ASSERTED intent (the
# work the user wants offloaded), never the negated clause (AC.ONCLOSE.5). The
# residual after stripping the negation lead-in IS that asserted work.
_NEGATED_WANT_LEAD = re.compile(
    r"^(?:to\s+)?(?:just\s+)?not\s+(?:have\s+to\s+|be\s+)?",
    flags=re.IGNORECASE,
)
# An explicit "do it FOR me" assertion the user states inside a negated
# correction ("Can it just do the writing for me if I give it the basics?"). The
# span between the verb and "for me" is the asserted work to offload — preferred
# over the negated want when present (AC.ONCLOSE.5).
_DO_FOR_ME_SPAN = re.compile(
    r"\b(?:can\s+(?:it|you)\s+(?:just\s+)?|(?:could|would)\s+(?:it|you)\s+|"
    r"i\s+(?:just\s+)?want\s+(?:it|you)\s+to\s+|just\s+)"
    r"(?P<span>(?:do|write|draft|handle|make|build|format|prepare|create)\b"
    r"(?:\s+\w+){0,8}?)\s+for\s+me\b",
    flags=re.IGNORECASE,
)
# A leading REJECTION frame that the user OPENS a correction with to reject
# loam's misread — its content is the REJECTED framing, not the asserted intent,
# so the leading rejection CLAUSE(S) are dropped and the distiller reads the
# ASSERTED work that follows (AC.ONCLOSE.5). Two shapes:
#   (a) "it's/that's not that … / not about …" — the explicit negation frame.
#   (b) "uh — that didn't quite land right, no" / "no, not quite" / "not exactly"
#       — a bare rejection-of-the-proposal opener with no asserted item in it.
_NEGATED_CORRECTION_LEAD = re.compile(
    r"^(?:well,?\s+)?(?:it'?s|its|that'?s)\s+not\s+(?:that\s+|about\s+)?"
    r"[^.!?;—–]*?(?=[.!?;]|—|–|$)",
    flags=re.IGNORECASE,
)
# A bare rejection clause ("uh, that didn't quite land right, no", "no not quite",
# "not exactly", "that's not it") — dropped wholesale so the asserted span leads.
_REJECTION_LEAD = re.compile(
    r"^(?:uh+,?\s+|um+,?\s+|oh,?\s+|well,?\s+|no,?\s+|nope,?\s+)*"
    r"(?:that\s+(?:did|does)(?:n'?t| not)\s+(?:quite\s+)?(?:land|sound|seem|"
    r"feel|come out)\s*(?:right|quite right)?|"
    r"that'?s\s+not\s+(?:quite\s+)?(?:it|right)|not\s+(?:quite|exactly|really)|"
    r"that'?s\s+not\s+what\s+i\s+(?:meant|said))"
    r"[^.!?;—–]*?(?=[.!?;]|—|–|$)",
    flags=re.IGNORECASE,
)
# An asserted-intent span the user states AFTER a rejection ("What I was saying
# is the claim-summary write-ups are the thing…", "what I meant is X"). The span
# after the frame, up to the verb/clause boundary, is the asserted item.
_ASSERTED_AFTER_REJECTION = re.compile(
    r"\b(?:what\s+i\s+(?:was\s+saying|meant|mean|said)\s+(?:is|was)|"
    r"what\s+i\s+(?:actually\s+)?(?:want|need)\s+(?:is|help\s+with\s+is)|"
    r"the\s+(?:thing|part)\s+i\s+need\s+help\s+with\s+is)\s+"
    r"(?P<span>.+?)"
    r"(?=\s+(?:are|is)\s+the\s+thing|[.!?;]|—|–|\s+that'?s\s+(?:what|the)\b|$)",
    flags=re.IGNORECASE,
)
_DISTILL_MAX_WORDS = 12


# Verb + pronoun-only object ("write them", "do it", "handle those") — an
# asserted-work span that names no concrete noun. The close prefers a named-noun
# span over one of these so it lands on the person's actual item (AC.ONCLOSE.4).
_PRONOUN_OBJECT = re.compile(
    r"^\s*(?:write|writing|do|doing|handle|handling|make|making|draft|drafting|"
    r"format|formatting|finish|finishing)?\s*"
    r"(?:them|it|those|these|that|this|all|everything)\s*$",
    flags=re.IGNORECASE,
)


def _is_pronoun_only_object(span: str) -> bool:
    """True when the span's object is a bare pronoun ("write them", "do it") with
    no concrete noun — the close defers to a more specific named span."""
    return bool(_PRONOUN_OBJECT.match(span.strip()))


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
    # A correction that REJECTS loam's read then states the real intent ("that
    # didn't quite land right, no. What I was saying is the claim-summary
    # write-ups …") — pull the ASSERTED span after the rejection, never the
    # rejection phrase itself (Bug-2 rerun3 regression on variant B). Preferred
    # over every clause heuristic when present (AC.ONCLOSE.5).
    asserted = _ASSERTED_AFTER_REJECTION.search(text)
    if asserted:
        span = asserted.group("span").strip().rstrip(",.").strip()
        # Drop a leading article so "the claim-summary write-ups" -> distillable.
        span_words = span.split()
        if 0 < len(span_words) <= _DISTILL_MAX_WORDS:
            return span
        if span_words:
            return " ".join(span_words[:_DISTILL_MAX_WORDS])
    # Drop a leading negated-correction frame ("it's not that I have trouble
    # starting it") OR a bare rejection clause ("uh, that didn't quite land
    # right, no") so the distilled item is the ASSERTED intent that follows,
    # never the rejected framing the user is correcting (AC.ONCLOSE.5). Only the
    # OPENING rejection clause is dropped; later content is preserved.
    for _lead in (_REJECTION_LEAD, _NEGATED_CORRECTION_LEAD):
        decorrected = _lead.sub("", text).strip().lstrip(",.!?—– ").strip()
        if decorrected and decorrected != text:
            text = decorrected
            break
    # An explicit "do X for me" assertion ("Can it just do the writing for me?")
    # is the asserted work to offload — preferred over a negated want-span so a
    # negated correction distills the asserted intent, not the negated clause
    # (AC.ONCLOSE.5). BUT only when X names a concrete noun: a pronoun-only object
    # ("write THEM for me", "do IT for me") is less specific than a named want-span
    # in the same reply ("stop writing those listing descriptions"), so a
    # pronoun-only do-for-me defers to the want-span below (AC.ONCLOSE.4).
    do_for_me = _DO_FOR_ME_SPAN.search(text)
    if do_for_me:
        span = do_for_me.group("span").strip().rstrip(",").strip()
        span = re.sub(
            r"^(do|handle|make)\s+",  # "do the writing" -> "the writing"
            "",
            span,
            flags=re.IGNORECASE,
        ).strip() or span
        if not _is_pronoun_only_object(span):
            words = span.split()
            if 0 < len(words) <= _DISTILL_MAX_WORDS:
                return span
            if words:
                return " ".join(words[:_DISTILL_MAX_WORDS])
    # If the user states an explicit intent ("I want to stop writing those listing
    # descriptions"), that span IS the item — prefer it over clause heuristics.
    want = _WANT_SPAN.search(text)
    if want:
        span = want.group("span").strip().rstrip(",").strip()
        # A NEGATED want ("not have to write them myself") asserts the user wants
        # the work DONE FOR them — distill the work, not the negation. Strip the
        # negation lead-in so the residual is the asserted item (AC.ONCLOSE.5).
        span = _NEGATED_WANT_LEAD.sub("", span).strip() or span
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
    # Drop leading clauses that are nothing but conversational filler OR a bare
    # difficulty-assessment ("easy", "the easy one") — read the NEXT content
    # clause (Bug-1 rerun3 regression on "Oh, easy — writing listing").
    core = ""
    for clause in clauses:
        stripped = _strip_lead_filler(clause)
        if stripped and not _PURE_DIFFICULTY.match(stripped):
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
    """Build the SINGLE person-specific leverage idea that the close lands on
    (AC.ONINTAKE.6 + AC.ONCLOSE.2/.3/.4).

    Design constraints (the owner's onboarding spec):

      - ONE landed thing (AC.ONCLOSE.2) — this is the single close idea; nothing
        else is emitted as a co-equal close line.
      - person-SPECIFIC (AC.ONCLOSE.4) — references the user's NAMED item
        (``clean_item``), never a generic-assistant triad.
      - NO over-promised automation (AC.ONCLOSE.3) — the close proposes
        right-sized help scaled to what the person showed they want; it does NOT
        claim the thing "happens reliably without you having to push it forward."
        The recurring/elaborate version stays the opt-in ``one_level_up_offer``,
        never the default the close commits to.
    """
    core = (intent.clean_item or intent.raw_answer).strip().rstrip(".")
    if intent.disposition == Disposition.STOP:
        # Right-sized: loam can DO this for you when you ask — a proposal scaled
        # to the literal ask (offload the task), not a promise of unattended
        # recurrence (that's the opt-in offer).
        text = (
            f"Here's the one thing to start with: let loam take '{core}' off "
            f"your plate — you hand it the basics and loam does it for you, so "
            f"it stops eating the time you'd rather spend elsewhere."
        )
    else:
        text = (
            f"Here's the one thing to start with: let loam help you with "
            f"'{core}' — you bring what you've got and loam does the heavy part, "
            f"so it actually gets done without it being all on you."
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


# Gerund-led named tasks a user lists when describing their day ("cite-checking
# briefs", "drafting discovery requests", "writing up claim summaries"). The
# ladder mines ONE of these as the concrete thing to land on (AC.ONCLOSE.4) —
# the person's OWN named work, not a generic "status updates / formatting"
# triad. A leading verb + its object, captured up to a list/clause boundary.
_NAMED_TASK = re.compile(
    r"\b(?P<task>(?:cite-?checking|drafting|writing(?:\s+up)?|reviewing|"
    r"formatting|reconciling|chasing|filing|tracking|managing|organi[sz]ing|"
    r"keeping|calendaring|answering|preparing|summari[sz]ing|building|pulling|"
    r"handling|processing)\b(?:\s+\w+){1,4}?)"
    r"(?=[,.;]|—|–|\s+and\b|\s+so\b|\s+but\b|\s+for\b|$)",
    flags=re.IGNORECASE,
)


def _named_task_from_description(description: str) -> str | None:
    """Pull ONE concrete named task the user listed when describing their work
    ("cite-checking briefs") so the ladder can land on the person's OWN words,
    not a generic triad (AC.ONCLOSE.4). Returns None when no clear task surfaces
    (the close then falls back to a role-level framing)."""
    m = _NAMED_TASK.search(description)
    if not m:
        return None
    task = m.group("task").strip().rstrip(",").strip()
    return " ".join(task.split()[:5]) or None


def _leverage_from_role(role: str, *, named_task: str | None = None) -> LeverageIdea:
    """The SINGLE person-specific leverage idea the ladder lands on (AC.ONINTAKE.5
    + AC.ONCLOSE.2/.4).

    When the user named a concrete task ("cite-checking briefs"), the close lands
    on THAT — their own words — not a generic "status updates / formatting /
    chasing" triad (the genericisation rerun2 flagged on learned-this-person).
    The ``{role}`` slot is the extracted role NOUN, never the raw description
    (AC.INTAKE-ROLE.1)."""
    noun = _extract_role_noun(role)
    if named_task:
        text = (
            f"Here's the one thing to start with: let loam take '{named_task}' "
            f"off your plate — it's repetitive, it's a real chunk of a {noun}'s "
            f"day, and loam can do the grunt of it so you spend your time on the "
            f"part only a {noun} can do."
        )
        return LeverageIdea(text=text, references=named_task)
    text = (
        f"Here's the one thing to start with: pick the most repetitive part of "
        f"a {noun}'s day and let loam take the grunt of it off your plate, so "
        f"you spend your time on the part only a {noun} can do."
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
# The ladder's surface-and-check (AC.ONCLOSE.1): before landing the close on the
# day-derived/idea-vacuum paths, loam SURFACES the single inferred starting point
# as a checkable hypothesis the user can confirm or correct (the four-step loop's
# verify leg). ``{one_thing}`` is filled with the inferred concrete start.
_Q_LADDER_CHECK = (
    "Based on that, the single highest-leverage place to start looks like: "
    "{one_thing}. Want to start there? (yes / no — or tell me what to change)"
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
        # The leverage idea must reference the CORRECTED item. ``clean_item``
        # carries the distilled corrected item so the close lands on it (and a
        # negated correction lands the ASSERTED intent — AC.ONCLOSE.4/.5).
        proposal = ProposedEndIntent(
            slug=result.seeded_objective_slug,
            disposition=disposition,
            objective_text=result.seeded_objective_text,
            raw_answer=corrected,
            clean_item=corrected,
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

    # The describe_work rung's bar is ROLE DETAIL, not a clean stop/start: a
    # genuine role description ("I'm a paralegal — cite-checking, drafting
    # discovery requests …") carries a role noun AND/OR named tasks even when it
    # also hedges ("I don't know, I can't point to one thing"). The strict
    # stop/start `_looks_empty` over-fired on that hedging and dropped a real
    # role to the generic starter (Bug-3 rerun3 regression on variant C). Here we
    # gate on EXTRACTABLE role detail: a role noun or a named task means we have
    # enough to mine + offer the deep dive.
    role = _extract_role_noun(role_answer)
    named_task = _named_task_from_description(role_answer)
    has_role_detail = bool(named_task) or (
        bool(role) and not _looks_like_pure_non_answer(role_answer)
    )

    if not has_role_detail:
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

    result.described_role = role
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
        # Fold the research synthesis INTO the seed (the seed carries the role's
        # tooling/effectiveness axes); it is NOT emitted as extra co-equal close
        # ideas — the close lands on ONE thing (AC.ONCLOSE.2).
        result.seeded_objective_text = (
            f"Help the user (a {role}) start with the highest-leverage offload "
            f"in their day; deep-role-research surfaced: "
            f"{research.existing_ai_tools}"
        )

    # --- Surface-and-check, then land ONE thing (AC.ONCLOSE.1/.2). ---
    # The single inferred starting point: the named task if one surfaced, else a
    # role-level "most repetitive part of your day" framing.
    one_thing = (
        f"taking '{named_task}' off your plate"
        if named_task
        else f"taking the most repetitive part of a {role}'s day off your plate"
    )
    check = ask("ladder_check", _Q_LADDER_CHECK.format(one_thing=one_thing))
    if _is_no(check):
        # The user rejected the inferred start — do NOT force it; offer to come
        # at it again rather than landing a thing they declined.
        result.leverage_ideas.append(
            LeverageIdea(
                text=(
                    "No problem — we don't have to start there. Tell me which "
                    "part of your day you'd most like off your plate and we'll "
                    "start with that instead."
                ),
                references=role,
            )
        )
        return result
    if not _is_yes(check):
        # A correction names a DIFFERENT start — land on the corrected item.
        corrected = _distill_intent(check) or check.strip()
        named_task = corrected
        one_thing = f"taking '{corrected}' off your plate"
    # Land EXACTLY one close idea on the checked/corrected thing (AC.ONCLOSE.2).
    result.leverage_ideas.append(_leverage_from_role(role, named_task=named_task))

    return result
