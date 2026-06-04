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

"""WMS Increment 3 — INTAKE: conversational work-capture (AC.INTK.*).

INTAKE is the translation-IN pillar of the work-management system. The user
states intent in natural language in an ordinary turn ("I also need to get the
rental paperwork going", "the launch waits on Eric's review") and a work item
appears in the increment-2 store, correctly placed, without the user ever
touching a tracker or holding an ID. The capture is LIGHT by default —
detect-and-PROPOSE (one plain-language "want me to track this?"), never a silent
auto-create, never a nag.

This module COMPOSES three existing seams; it re-implements none of them
(Lens-1 — compose, don't duplicate):

  - **The #56 LLM intent-extraction MECHANISM** (``loam_spawn_isolation.
    spawn_isolated_claude`` + the fail-soft-to-deterministic discipline +
    the ``{"result": …}`` envelope parse). The #56 ``intent_extract.py`` seam
    is ONBOARDING-shaped — its ``ExtractedIntent`` carries a stop/start
    ``disposition`` and its prompt asks for the one thing the user would love
    to STOP or START (plan §10 RF #1). Work-intake needs a DIFFERENT read
    (is-this-work + a plain title + a candidate stream/project + an optional
    waiting-on party), so this module supplies a WORK-SHAPED extractor
    (:class:`WorkIntentExtractor` + :class:`ClaudeWorkIntentExtractor`) reusing
    the spawn-isolation MECHANISM, NOT the onboarding prompt (D-INTK.4). It does
    NOT edit the sealed onboarding ``intent_extract.py`` contract (plan §8 #3).

  - **The #34 interaction-model** (``InteractionModel.cell_or_prior``). The
    aggressiveness — how readily a turn becomes a proposal — is a per-user
    preference cell ``work-tracking`` / ``intake-aggressiveness``
    (``off`` / ``light`` / ``eager``, default LIGHT). Intake READS the cell; it
    invents no threshold and adds no parse/render contract change (the area is a
    free-form ``## work-tracking`` section the existing parser already accepts —
    plan §8 #4).

  - **The increment-2 work-item store** (``ObjectiveTracker.create`` /
    ``start`` / ``mark_abandoned``). A detected item is a real work item created
    in the store's ``proposed`` (surfaced-not-committed) lifecycle state with
    ``LiftedFrom`` conversation provenance + a candidate stream/project; a
    plain-language confirm promotes it ``proposed → active``, a dismiss abandons
    it ``proposed → abandoned``. The store is CONSUMED via its existing API,
    NOT modified — increment 3 is single-component on ``primary-persona``
    (D-INTK.1 / plan §5). The ``proposed`` item IS the proposal state — there is
    no parallel intake-side pending queue (D-INTK.5).

Fail-soft is the load-bearing invariant. When the extractor declines
(unavailable, timeout, no usable read) intake surfaces NO proposal for that turn
and the turn proceeds normally (AC.INTK.DETECT.2). Silence is the safe failure
mode for a quality-LIFT layer — the don't-nag-aligned default, mirroring the FBM
load-filter affirmative-recognition precedent. The contributor is registered at
``TriggerKind.turn`` (the same seat the projects/streams lenses use); any
boundary error yields ``""`` so the composer's turn proceeds.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, Protocol

# ====================================================================
# The aggressiveness dial (#34) — the per-user, light-default cell
# ====================================================================

# The #34 area + axis the aggressiveness reads from (WMS-D4). A missing cell
# degrades to LIGHT (the openness-biased default the plan names) — intake never
# invents a threshold, and an unset matrix is the common case.
INTAKE_AREA = "work-tracking"
INTAKE_AXIS = "intake-aggressiveness"

# The ordered aggressiveness levels (D-INTK.2). ``off`` never proposes; ``light``
# (the DEFAULT) proposes only on a clear forward-looking work-intent signal;
# ``eager`` proposes on softer signals too.
AGGR_OFF = "off"
AGGR_LIGHT = "light"
AGGR_EAGER = "eager"
_VALID_AGGR = frozenset({AGGR_OFF, AGGR_LIGHT, AGGR_EAGER})
DEFAULT_AGGRESSIVENESS = AGGR_LIGHT


def resolve_aggressiveness(claude_home: Path | str | None = None) -> str:
    """Read the per-user intake aggressiveness from the #34 interaction-model.

    Reads ``work-tracking`` / ``intake-aggressiveness`` via
    ``InteractionModel.cell_or_prior``; an absent / empty / unrecognised cell
    degrades to :data:`DEFAULT_AGGRESSIVENESS` (light). Fail-open: any loader
    error yields the light default (the turn personalises as the un-set chain
    does). NEVER raises (AC.INTK.LIGHT.2)."""
    try:
        from .interaction_model import load_interaction_model  # noqa: WPS433

        model = load_interaction_model(claude_home)
        cell = model.cell_or_prior(INTAKE_AREA, INTAKE_AXIS)
        value = (getattr(cell, "value", "") or "").strip().lower()
    except Exception:  # noqa: BLE001 — fail-open to the light default
        return DEFAULT_AGGRESSIVENESS
    if value in _VALID_AGGR:
        return value
    return DEFAULT_AGGRESSIVENESS


# ====================================================================
# The WORK-SHAPED intent-extraction seam (D-INTK.4 / RF #1)
# ====================================================================
#
# Composes the #56 spawn-isolation MECHANISM with a WORK-shaped prompt + read.
# The #56 onboarding ``IntentExtractor`` Protocol is stop/start-shaped; this is
# the sibling work-shaped read (is-this-work + title + candidate placement +
# waits-on). The MECHANISM (spawn_isolated_claude, hard timeout, envelope parse,
# fail-soft) is reused verbatim; the onboarding ``intent_extract.py`` is NOT
# touched.

DEFAULT_WORK_INTENT_MODEL = "sonnet"
DEFAULT_WORK_INTENT_TIMEOUT_SECONDS = 45.0


@dataclass
class WorkIntent:
    """A work-shaped read of one conversational turn (AC.INTK.DETECT.1).

    ``is_work`` is the discriminator — True iff the turn carries a clear
    forward-looking piece of work the user mentions (a task, a follow-up, a
    thing to do, a blocker); False for a question, chatter, or a statement of
    fact. ``title`` is the SHORT plain-language title of the work in the user's
    words (no leading verb). ``candidate_stream`` / ``candidate_project`` are the
    optional placement hints (a work-stream tag and/or a project binding) when
    the turn implies one. ``waits_on`` is the optional waiting-on party when the
    turn names one. ``strength`` is the model's read of how clear the work-intent
    signal is — ``clear`` (a forward-looking, committed piece of work) vs ``soft``
    (a mention that could be a one-off / aside); the aggressiveness gate uses it
    (light proposes only ``clear``; eager proposes ``soft`` too)."""

    is_work: bool
    title: str = ""
    candidate_stream: str = ""
    candidate_project: str = ""
    waits_on: str = ""
    strength: str = "clear"

    @property
    def is_usable(self) -> bool:
        """A usable work read is a work-intent with a non-empty title."""
        return bool(self.is_work and self.title and self.title.strip())


class WorkIntentUnavailableError(Exception):
    """The bounded work-intent extraction could not produce a usable read.

    Raised when the spawn-isolation primitive is absent, the dispatch fails /
    times out, the output is unparseable, or the read is empty. Intake catches
    it and surfaces NO proposal for the turn — it NEVER propagates out of the
    turn path (AC.INTK.DETECT.2 fail-soft to silence)."""


class WorkIntentExtractor(Protocol):
    """The injectable boundary intake composes on (AC.INTK.DETECT.1).

    Input: the raw user turn text. Output: a :class:`WorkIntent`. Production
    registers :class:`ClaudeWorkIntentExtractor`; the default is
    :class:`DisabledWorkIntentExtractor` so the path is opt-in / off (and the
    ``off`` aggressiveness level) until a real extractor is installed."""

    def extract(self, turn_text: str) -> WorkIntent:  # pragma: no cover - structural
        ...


class DisabledWorkIntentExtractor:
    """The default extractor — always declines (mirrors #56 D-SEAM-1).

    Performs NO spawn and NO network call; raises
    :class:`WorkIntentUnavailableError` immediately so intake surfaces no
    proposal. Keeps the baseline featherlight + offline-clean; the real
    extractor is installed explicitly by the production wiring."""

    def extract(self, turn_text: str) -> WorkIntent:
        raise WorkIntentUnavailableError(
            "work-intent extraction disabled by default; register a real "
            "extractor to enable conversational work-capture"
        )


# The WORK-shaped prompt (NOT the #56 onboarding stop/start prompt). It is told
# to return ONLY a JSON object so the parse is deterministic. ONE scoped call
# (no tool use, no loop): the user's turn in, a structured work read out.
_WORK_EXTRACT_PROMPT = """\
You are loam's conversational work-capture step. You read ONE message a user \
just sent in an ordinary working conversation and decide whether it mentions a \
concrete piece of WORK the user needs to do — a task, a follow-up, a thing to \
get done, or a blocker they're waiting on — that is worth TRACKING as a work \
item.

Their message:
\"\"\"{turn_text}\"\"\"

Return ONLY a JSON object (no prose, no code fence) with EXACTLY these keys:
  - "is_work": true if the message mentions a concrete, forward-looking piece \
of work the user needs to do or is waiting on; false for a question, chatter, a \
statement of fact, a one-off request to do something right now (e.g. "reformat \
this paragraph"), or an opinion. Be CONSERVATIVE: when in doubt, false.
  - "title": if is_work, a SHORT plain-language title for the work in THEIR \
words (<= 10 words, no leading verb like "track"/"do" — just the thing, e.g. \
"rental paperwork" or "Q3 budget review"); otherwise "".
  - "candidate_stream": if the work clearly belongs to a recurring track / area \
the user works in (e.g. "money", "house", "writing"), a SHORT lowercase tag for \
it; otherwise "".
  - "candidate_project": if the work clearly belongs to a named project, a \
SHORT name for it; otherwise "".
  - "waits_on": if the work is BLOCKED on / waiting for a specific person or \
party named in the message, that party's short name; otherwise "".
  - "strength": "clear" if this is a clearly forward-looking, committed piece \
of work the user will need to come back to; "soft" if it's a mention that might \
just be an aside or a one-off and a cautious reader would hesitate to track it.

Read intent over keywords. Do NOT invent a project or stream that isn't implied.
"""


class ClaudeWorkIntentExtractor:
    """The real work-intent extractor — ONE bounded ``claude -p`` call.

    Reuses the #56 spawn-isolation MECHANISM verbatim: LAZY-imports
    ``loam_spawn_isolation`` inside ``extract`` (a separate package), dispatches
    a single scoped ``claude -p`` with a HARD timeout through the MANDATED
    ``spawn_isolated_claude`` (``--strict-mcp-config`` + empty mcpServers +
    ANTHROPIC_API_KEY / TELEGRAM_BOT_TOKEN scrubbed env), parses the
    ``{"result": …}`` envelope, and raises :class:`WorkIntentUnavailableError`
    on ANY failure so intake fails soft to silence. No Anthropic SDK, no API key
    — subscription-only via ``claude -p`` (``feedback_no_anthropic_api_key``)."""

    def __init__(
        self,
        *,
        model: str = DEFAULT_WORK_INTENT_MODEL,
        timeout_seconds: float = DEFAULT_WORK_INTENT_TIMEOUT_SECONDS,
    ) -> None:
        self._model = model
        self._timeout_seconds = timeout_seconds

    def extract(self, turn_text: str) -> WorkIntent:
        if not (turn_text or "").strip():
            raise WorkIntentUnavailableError("empty turn — nothing to extract")
        try:
            from loam_spawn_isolation import spawn_isolated_claude  # noqa: WPS433
        except ImportError as exc:  # pragma: no cover - environmental
            raise WorkIntentUnavailableError(
                f"loam_spawn_isolation not importable ({exc}); the bounded "
                "work-intent call cannot be spawned isolated — surfacing no "
                "proposal this turn."
            ) from exc

        prompt = _WORK_EXTRACT_PROMPT.format(turn_text=turn_text.strip())
        argv = [
            "claude",
            "-p",
            prompt,
            "--model",
            self._model,
            "--output-format",
            "json",
            "--permission-mode",
            "bypassPermissions",
        ]
        try:
            proc = spawn_isolated_claude(
                argv,
                capture_output=True,
                text=True,
                timeout=self._timeout_seconds,
            )
        except Exception as exc:  # noqa: BLE001 — any spawn/timeout failure -> silence
            raise WorkIntentUnavailableError(
                f"work-intent dispatch failed: {exc}"
            ) from exc
        if proc.returncode != 0:
            raise WorkIntentUnavailableError(
                f"work-intent subagent exited {proc.returncode}: "
                f"{(proc.stderr or '')[:300]}"
            )
        raw = (proc.stdout or "").strip()
        try:
            envelope = json.loads(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            raise WorkIntentUnavailableError(
                f"work-intent stdout not a claude -p JSON envelope: {exc}"
            ) from exc
        if not isinstance(envelope, dict):
            raise WorkIntentUnavailableError("work-intent envelope not an object")
        return _parse_work_intent(envelope.get("result") or "")


def _parse_work_intent(result_text: str) -> WorkIntent:
    """Parse the subagent's JSON result into a :class:`WorkIntent`.

    Tolerates a leading/trailing code fence the model occasionally adds. A
    ``is_work: false`` read is a VALID non-work result and is returned (it is the
    chatter/no-capture answer, AC.INTK.LIGHT.1); an unparseable result, or a
    work read with no usable title, raises :class:`WorkIntentUnavailableError`
    so intake surfaces no proposal."""
    text = (result_text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise WorkIntentUnavailableError(
            f"work-intent result not JSON: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise WorkIntentUnavailableError("work-intent result not an object")
    is_work = bool(payload.get("is_work", False))
    strength = str(payload.get("strength", "clear") or "clear").strip().lower()
    if strength not in ("clear", "soft"):
        strength = "clear"
    intent = WorkIntent(
        is_work=is_work,
        title=str(payload.get("title", "") or "").strip(),
        candidate_stream=str(payload.get("candidate_stream", "") or "").strip(),
        candidate_project=str(payload.get("candidate_project", "") or "").strip(),
        waits_on=str(payload.get("waits_on", "") or "").strip(),
        strength=strength,
    )
    # A non-work read is a valid "no capture" answer — return it so the gate can
    # produce ZERO proposals. A work read with no title is unusable (degrade to
    # silence rather than create a title-less item).
    if intent.is_work and not intent.is_usable:
        raise WorkIntentUnavailableError(
            "work-intent flagged work but produced no usable title"
        )
    return intent


# The default extractor intake resolves at CALL time. Production wiring swaps it
# for a real ClaudeWorkIntentExtractor; the default DECLINES so the path is
# opt-in (and the ``off`` aggressiveness level) until installed.
_DEFAULT_WORK_EXTRACTOR: WorkIntentExtractor = DisabledWorkIntentExtractor()


def default_work_intent_extractor() -> WorkIntentExtractor:
    """The extractor intake composes on — resolved at CALL time so a consumer
    can register a real extractor without the baseline importing it."""
    return _DEFAULT_WORK_EXTRACTOR


def register_work_intent_extractor(extractor: WorkIntentExtractor) -> None:
    """Swap the default work-intent extractor intake resolves at call time.

    The seam the production wiring fills to install the real
    :class:`ClaudeWorkIntentExtractor` WITHOUT the baseline importing it.
    Fail-soft is unaffected — intake still catches
    :class:`WorkIntentUnavailableError` whichever extractor is registered."""
    global _DEFAULT_WORK_EXTRACTOR
    _DEFAULT_WORK_EXTRACTOR = extractor


def reset_work_intent_extractor() -> None:
    """Restore the disabled (declines) default — test-hygiene seam so a test
    that registers a fake extractor can undo it without leaking module state."""
    global _DEFAULT_WORK_EXTRACTOR
    _DEFAULT_WORK_EXTRACTOR = DisabledWorkIntentExtractor()


# ====================================================================
# The aggressiveness gate (AC.INTK.LIGHT.*)
# ====================================================================


def gate_admits(intent: WorkIntent, aggressiveness: str) -> bool:
    """Whether a detected work intent becomes a proposal at this aggressiveness.

    - ``off`` — never (the user tracks manually).
    - ``light`` (default) — only a CLEAR forward-looking signal
      (``strength == "clear"``). A soft / aside mention is NOT proposed (the
      no-over-capture guard, AC.INTK.LIGHT.1).
    - ``eager`` — clear AND soft signals (a power user who wants aggressive
      capture, AC.INTK.LIGHT.2).

    A non-usable intent (not work, or no title) is never admitted."""
    if not intent.is_usable:
        return False
    if aggressiveness == AGGR_OFF:
        return False
    if aggressiveness == AGGR_EAGER:
        return True
    # light (and any unrecognised value, which resolve_aggressiveness already
    # collapses to light): clear signals only.
    return intent.strength == "clear"


# ====================================================================
# Dedup against open work items (AC.INTK.DEDUP.1) — conservative bias
# ====================================================================
#
# D-INTK.3: suppress a proposal ONLY on a HIGH-confidence near-duplicate of an
# OPEN item already in the store; when unsure, propose (a visible dismissable
# duplicate beats a silently-dropped genuinely-new item — the false-merge
# asymmetry, plan §10 RF #3). The match OUTCOME (a re-mention of an
# already-tracked thing does not create a duplicate) is the contract; the match
# method here is a normalised-token overlap with a high threshold — the
# builder's call within this ★ decision.

_OPEN_STATUSES = frozenset({"proposed", "active", "blocked", "owner_pending"})

# The high-confidence near-duplicate threshold (conservative). A candidate is
# suppressed only when its title's content tokens overlap an open item's title
# at or above this Jaccard ratio — a high bar so a merely-similar-sounding NEW
# item is still proposed.
_DEDUP_THRESHOLD = 0.8

# Tokens too generic to carry match signal (stripped before comparison so they
# don't inflate a spurious overlap).
_DEDUP_STOPWORDS = frozenset(
    {
        "the", "a", "an", "to", "of", "for", "and", "on", "in", "my", "our",
        "with", "get", "do", "need", "this", "that", "work", "item", "thing",
    }
)


def _normalise_tokens(title: str) -> frozenset[str]:
    """Lowercase content tokens of a title, stopwords + punctuation stripped."""
    raw = "".join(c.lower() if (c.isalnum() or c.isspace()) else " " for c in title)
    return frozenset(t for t in raw.split() if t and t not in _DEDUP_STOPWORDS)


def is_near_duplicate(candidate_title: str, open_titles: list[str]) -> bool:
    """High-confidence near-duplicate check (conservative, AC.INTK.DEDUP.1).

    True iff the candidate title's content-token set overlaps some OPEN item's
    title at or above the high :data:`_DEDUP_THRESHOLD` (Jaccard). Empty token
    sets never match (so a title that is all stopwords is never falsely merged).
    Biased to FALSE (propose) when unsure — a near-miss is proposed, not
    suppressed."""
    cand = _normalise_tokens(candidate_title)
    if not cand:
        return False
    for other in open_titles:
        existing = _normalise_tokens(other)
        if not existing:
            continue
        union = cand | existing
        if not union:
            continue
        overlap = len(cand & existing) / len(union)
        if overlap >= _DEDUP_THRESHOLD:
            return True
    return False


def _open_titles(work_items: list[Any]) -> list[str]:
    """The titles (goals) of the OPEN work items — the dedup comparison set."""
    titles: list[str] = []
    for item in work_items:
        status = getattr(getattr(item, "status", None), "value", None) or getattr(
            item, "status", ""
        )
        if str(status) in _OPEN_STATUSES:
            goal = (getattr(item, "goal", "") or "").strip()
            if goal:
                titles.append(goal)
    return titles


# ====================================================================
# The conversation-provenance pointer (AC.INTK.PROPOSE.2)
# ====================================================================

# The provenance source-doc marker that identifies an intake-captured item as
# lifted from conversation — distinct from FIDRAFT-graduated / dev-queue /
# owner-stated origins. Uses the existing ``LiftedFrom`` pointer; no store-side
# field is added (D-INTK.1).
CONVERSATION_ORIGIN = "conversation"


def _conversation_provenance(turn_marker: str) -> Any:
    """Build the ``LiftedFrom`` conversation-provenance pointer for a captured
    item. ``source_ac`` records the turn marker so the source turn is recoverable
    later (AC.INTK.PROPOSE.2). Returns None if the spec type is unavailable (the
    create still succeeds without provenance — fail-soft)."""
    try:
        from loam.objective_tracker.spec import LiftedFrom  # noqa: WPS433

        return LiftedFrom(
            source_doc=CONVERSATION_ORIGIN,
            source_ac=(turn_marker or "turn").strip() or "turn",
        )
    except Exception:  # noqa: BLE001 — provenance optional; create still works
        return None


# ====================================================================
# Propose + place (AC.INTK.PROPOSE.*) — create a `proposed` work item
# ====================================================================


@dataclass
class IntakeProposal:
    """The result of an intake turn that produced a proposal.

    Carries the plain-language proposal line surfaced to the user, the
    ``objective_id`` of the ``proposed`` work item created in the store (for the
    later confirm/dismiss), and the candidate placement. The ``proposed`` item
    IS the proposal state (D-INTK.5) — there is no parallel pending queue."""

    line: str
    objective_id: str
    title: str
    candidate_stream: str = ""
    candidate_project: str = ""


def render_proposal_line(intent: WorkIntent) -> str:
    """The ONE concise plain-language proposal line (AC.INTK.PROPOSE.1).

    Carries NO internal identifier, lifecycle enum, slug, or path — only the
    plain title + an optional placement hint + an optional waiting-on note. The
    outbound-guard hooks enforce zero-internal-vocab; this renderer never emits
    any."""
    title = intent.title.strip()
    place = ""
    if intent.candidate_project:
        place = f" under {intent.candidate_project}"
    elif intent.candidate_stream:
        place = f" under {intent.candidate_stream}"
    waits = ""
    if intent.waits_on:
        waits = f" (waiting on {intent.waits_on})"
    return f"Sounds like a new thing to track: \"{title}\"{place}{waits} — want me to keep it?"


async def create_proposed_item(
    tracker: Any,
    intent: WorkIntent,
    *,
    turn_marker: str = "turn",
) -> str:
    """Create a ``proposed`` work item from a work intent (AC.INTK.PROPOSE.1/.2).

    Builds an ``ObjectiveSpec`` (goal = the plain title, conversation
    provenance, candidate ``tagged_streams`` / ``belongs_to_project``) and calls
    the store's existing async ``create`` API — the store creates in ``proposed``
    (its lifecycle entry state). Returns the created item's ``objective_id``.
    The store is CONSUMED, not modified (D-INTK.1). NOT a silent commit to
    ``active`` — promotion happens only on a confirm (:func:`confirm_proposal`)."""
    from loam.objective_tracker.spec import (  # noqa: WPS433
        ObjectiveSpec,
        ProseCriterion,
        TimeBound,
    )

    streams: tuple[str, ...] = (
        (intent.candidate_stream,) if intent.candidate_stream else ()
    )
    spec = ObjectiveSpec(
        goal=intent.title.strip(),
        parent_id=None,
        acceptance_criteria=(
            ProseCriterion(criterion_id="intake", prose="captured from conversation"),
        ),
        time_bound=TimeBound(evergreen=True),
        authored_by="user",
        lifted_from=_conversation_provenance(turn_marker),
        belongs_to_project=intent.candidate_project or None,
        tagged_streams=streams,
        priority="proposed",
    )
    created = await tracker.create(spec)
    return created.objective_id


async def confirm_proposal(tracker: Any, objective_id: str) -> Any:
    """Promote a proposed item to ``active`` on a plain-language confirm.

    Drives the store's existing ``proposed → active`` transition
    (AC.INTK.CONFIRM.1). The item becomes a real tracked work item the lenses
    render."""
    return await tracker.start(objective_id, rationale="confirmed from conversation")


async def dismiss_proposal(tracker: Any, objective_id: str) -> Any:
    """Abandon a proposed item on a plain-language dismiss.

    Drives the store's existing ``proposed → abandoned`` transition
    (AC.INTK.CONFIRM.1). It does not surface in any lens afterwards."""
    return await tracker.mark_abandoned(
        objective_id, rationale="dismissed from conversation"
    )


# ====================================================================
# The intake turn driver (AC.INTK.*) — detect → gate → dedup → propose
# ====================================================================


async def intake_turn(
    turn_text: str,
    tracker: Any,
    *,
    extractor: Optional[WorkIntentExtractor] = None,
    claude_home: Path | str | None = None,
    turn_marker: str = "turn",
) -> Optional[IntakeProposal]:
    """Run ONE intake turn over the raw user text against the live store.

    The full intake pipeline (plan §7), fail-soft to no-proposal at every step:

    1. **Detect** — read the turn via the work-shaped extractor; on decline
       (``WorkIntentUnavailableError``) surface NO proposal (AC.INTK.DETECT.2).
    2. **Gate** — read the #34 aggressiveness cell (default light) and admit the
       intent only if the gate passes (off → never; light → clear signals only;
       eager → soft too) (AC.INTK.LIGHT.*).
    3. **Dedup** — suppress a high-confidence near-duplicate of an OPEN item
       (conservative; propose when unsure) (AC.INTK.DEDUP.1).
    4. **Propose + place** — create a ``proposed`` work item with conversation
       provenance + candidate placement and return the plain-language proposal
       (AC.INTK.PROPOSE.*).

    Returns an :class:`IntakeProposal` when a proposal was made (and the
    ``proposed`` item created), or ``None`` when no proposal is surfaced (not
    work, gated out, deduped, or extractor declined). NEVER raises out of the
    turn path — any error degrades to ``None``."""
    ext = extractor if extractor is not None else default_work_intent_extractor()

    # 1. Detect — fail-soft to no-proposal on decline.
    try:
        intent = ext.extract(turn_text)
    except WorkIntentUnavailableError:
        return None
    except Exception:  # noqa: BLE001 — any extractor error -> silence
        return None
    if not intent.is_usable:
        return None  # chatter / non-work read -> ZERO proposals

    # 2. Gate on the per-user aggressiveness (light default).
    aggressiveness = resolve_aggressiveness(claude_home)
    if not gate_admits(intent, aggressiveness):
        return None

    # 3. Dedup — conservative high-confidence near-duplicate suppression.
    try:
        open_items = list(tracker.query_projection_view())
    except Exception:  # noqa: BLE001 — store unreadable -> propose (don't drop)
        open_items = []
    if is_near_duplicate(intent.title, _open_titles(open_items)):
        return None

    # 4. Propose + place — create the `proposed` item, render the one line.
    objective_id = await create_proposed_item(
        tracker, intent, turn_marker=turn_marker
    )
    return IntakeProposal(
        line=render_proposal_line(intent),
        objective_id=objective_id,
        title=intent.title.strip(),
        candidate_stream=intent.candidate_stream,
        candidate_project=intent.candidate_project,
    )


# ====================================================================
# The keep-pace turn contributor (AC.INTK.PROPOSE.1) — the production seat
# ====================================================================


def _default_tracker_factory() -> Any:
    """Resolve the live tracker for the active workspace (read+write).

    Mirrors the projects/streams lenses' default factory: a lazy
    ``objective_tracker`` import inside the try so an absent component degrades
    to ``None`` (no proposal), never an import-time crash. The DB path is
    resolved from the workspace identity the same way the lenses resolve it —
    intake creates into the SAME live store the lenses read."""
    try:
        from ..tracker_context import tracker_db_path_for  # noqa: WPS433
        from loam.objective_tracker.runtime import ObjectiveTracker  # noqa: WPS433
    except Exception:  # noqa: BLE001 — component absent; no proposal
        return None
    try:
        db_path = tracker_db_path_for(Path.cwd())
        if not Path(db_path).exists():
            return None
        return ObjectiveTracker(db_path=db_path)
    except Exception:  # noqa: BLE001 — unresolvable; no proposal
        return None


def _run_intake_turn_sync(
    turn_text: str,
    *,
    tracker_factory: Optional[Callable[[], Any]] = None,
    extractor: Optional[WorkIntentExtractor] = None,
    claude_home: Path | str | None = None,
) -> Optional[IntakeProposal]:
    """Drive :func:`intake_turn` synchronously for the turn contributor.

    The keep-pace contributor seat is synchronous (``fn(context) -> str``) while
    the store API is async; this bridges them with a fresh event loop per turn
    (the per-turn cost is one bounded create at most). Fail-soft: any error
    yields ``None`` (no proposal). Resolves + closes the live tracker around the
    single turn."""
    import asyncio

    factory = (
        tracker_factory if tracker_factory is not None else _default_tracker_factory
    )
    tracker = factory()
    if tracker is None:
        return None
    try:
        return asyncio.run(
            intake_turn(
                turn_text,
                tracker,
                extractor=extractor,
                claude_home=claude_home,
            )
        )
    except Exception:  # noqa: BLE001 — fail-soft; no proposal
        return None
    finally:
        close = getattr(tracker, "close", None)
        if callable(close):
            try:
                close()
            except Exception:  # noqa: BLE001 — best-effort cleanup
                pass


def build_intake_contributor(
    *,
    tracker_factory: Optional[Callable[[], Any]] = None,
    extractor: Optional[WorkIntentExtractor] = None,
    claude_home: Path | str | None = None,
) -> Callable[[dict], str]:
    """Return the keep-pace turn contributor (``fn(context: dict) -> str``).

    Reads ``context["prompt"]`` (the raw user turn — AC.INTK.PROPOSE.1), runs
    the intake pipeline, and returns the ONE plain-language proposal line when a
    proposal was made, or ``""`` (no block) otherwise. Fail-soft: any boundary
    error yields ``""`` so the composer's turn proceeds (the graceful-empty
    contract the sibling contributors honour). The ``proposed`` work item is
    created as a side effect of a proposal (D-INTK.5)."""

    def contributor(context: dict) -> str:
        try:
            prompt = str((context or {}).get("prompt", "") or "")
            if not prompt.strip():
                return ""
            proposal = _run_intake_turn_sync(
                prompt,
                tracker_factory=tracker_factory,
                extractor=extractor,
                claude_home=claude_home,
            )
            return proposal.line if proposal is not None else ""
        except Exception:  # noqa: BLE001 — fail-soft; turn proceeds
            return ""

    return contributor


def register_intake_contributor(
    composer: object,
    *,
    name: str = "intake",
    tracker_factory: Optional[Callable[[], Any]] = None,
    extractor: Optional[WorkIntentExtractor] = None,
    claude_home: Path | str | None = None,
) -> Callable[[dict], str]:
    """Register the intake turn-contributor at ``TriggerKind.turn``.

    A SEPARATE named block from the projects/streams lenses (intake POPULATES
    the store the lenses render — the translation-IN pillar). Returns a ``str``
    always (``""`` on no proposal) so ``_serialise_turn``'s ``text.strip()`` is
    safe."""
    from ..context_composer import TriggerKind  # noqa: WPS433

    fn = build_intake_contributor(
        tracker_factory=tracker_factory,
        extractor=extractor,
        claude_home=claude_home,
    )
    composer.register(name=name, trigger_kind=TriggerKind.turn, fn=fn)
    return fn
