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

"""The REAL deep-role-research provider (N3 fast-follow / AC.DRR.* / AC.DRROUT.*).

This fills the seam N3 sealed (``deep_role_research.py``): given a user's
role + their explicit opt-in (both already established by the sealed intake —
this slice NEVER re-gates), it researches three axes —

  (i)  what makes someone EFFECTIVE at the role,
  (ii) what gets people PROMOTED to the next level,
  (iii) which EXISTING AI solutions loam could wrap or rebuild for the user,

then SYNTHESIZES the raw research into a SHORT, person-specific, actionable set
of leverage ideas and returns it through the sealed ``RoleResearchResult`` shape
with ``is_stub=False`` — which the intake's ``as_leverage_ideas()`` fold-back
consumes UNCHANGED.

**The over-reach guard applies TWICE** (the only user who reaches this seam is —
by the sealed intake's routing — already overwhelmed): (a) the research runs on a
BOUNDED budget (a small fixed round-trip ceiling — D-RES-2, not an unbounded
agent loop), and (b) the output is a SHORT, person-specific set of a FEW leverage
ideas (D-RES-2: at most ``MAX_LEVERAGE_IDEAS``), never the raw research, never a
dump that re-overwhelms the person the intake just coaxed out of overwhelm.

**The research primitive (D-RES-1 (a), RULED; CONVERTED — AC.RES1.1).** A
standalone Python provider is NOT a Claude session — it cannot import
``WebSearch`` / ``WebFetch`` / the ``Agent`` tool directly. Loam's standing rule
(``feedback_no_anthropic_api_key``) forbids the Anthropic SDK /
``ANTHROPIC_API_KEY`` path. The PRODUCTION source (:class:`InSessionResearchSource`)
COMPOSES the Claude-native research subagent as an IN-SESSION subagent (the Task
primitive), dispatched through a callable the live host session registers
(:func:`set_in_session_dispatcher`). In-session subagents are accounted against
the subscription plan limits — NOT the post-June-15 metered Agent SDK credit a
detached ``claude -p`` would draw from — and share the parent's MCP, so they
never re-load the Telegram plugin and cannot steal the operator's bot slot. The
converted path therefore NEVER touches the ``loam_spawn_isolation`` chokepoint
(no subprocess argv to isolate).

The RESIDUAL source (:class:`ClaudeSubagentResearchSource`) STAYS in this module
for the path that has no living parent session to fan an in-session subagent from
(it spawns the bounded ``claude -p`` subprocess through the MANDATED
``loam_spawn_isolation.spawn_isolated_claude`` primitive — ``--strict-mcp-config``
+ empty ``mcpServers`` + token/API-key-scrubbed env — so that spawn cannot steal
the operator's Telegram bot slot,
``feedback_spawned_claude_must_isolate_telegram_plugin``). The spawn-isolation
guard's scope NARROWS to residual-only; it is NOT deleted.

Both sources DEGRADE GRACEFULLY when the capability is unavailable (no in-session
dispatcher registered / dispatch failure / ``loam_spawn_isolation`` or the
``claude`` binary absent) — raising :class:`ResearchUnavailableError` so the
provider returns the same no-interrogation-by-weight fallback the N3 baseline
relied on (AC.DRRGRACE.1).

**Sync vs async (D-RES-3 (a), RULED).** The research runs SYNCHRONOUSLY at the
opt-in moment with a HARD timeout; on timeout / failure / unavailable primitive,
a clearly-marked fallback synthesis is returned (AC.DRRGRACE.1). Async
re-surfacing is a fast-follow on this fast-follow.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Callable, Protocol

from .deep_role_research import RoleResearchResult

# === In-session subagent dispatch seam (AC.RES1.1) ============================
#
# The standalone Python provider is NOT itself a Claude session — it cannot
# import the Task primitive directly. The LIVE host session that runs onboarding
# (the only context with the Task tool) registers a dispatcher callable here; the
# production research source resolves it at call time. A registered dispatcher is
# accounted against the subscription plan limits (in-session subagent billing),
# NOT the post-June-15 metered Agent SDK credit a detached `claude -p` would draw
# from — the whole motive of this slice.
#
# The dispatcher takes the bounded research prompt + the model name and returns
# the subagent's raw result TEXT (the JSON the prompt asks for, possibly fenced —
# parsed by the UNCHANGED _parse_research_envelope). No dispatcher registered →
# the in-session capability is unavailable → ResearchUnavailableError → the
# AC.DRRGRACE.1 fallback (the SAME degrade path the old `claude`-absent case
# took). This is the honest shape of "the provider is not a session": when no
# live session wired a dispatcher, it degrades exactly as before.

InSessionDispatcher = Callable[[str], str]

_in_session_dispatcher: InSessionDispatcher | None = None


def set_in_session_dispatcher(dispatcher: InSessionDispatcher) -> None:
    """Register the live host session's in-session subagent dispatcher.

    Called by the live Claude Code session that runs onboarding: it passes a
    callable ``(prompt: str) -> str`` that fans out an in-session subagent (the
    Task primitive) with that prompt and returns the subagent's raw result text.
    The production :class:`InSessionResearchSource` resolves this at call time so
    no intake call site has to thread the dispatcher through.
    """
    global _in_session_dispatcher
    _in_session_dispatcher = dispatcher


def get_in_session_dispatcher() -> InSessionDispatcher | None:
    """Return the registered in-session dispatcher, or ``None`` if none wired."""
    return _in_session_dispatcher


def clear_in_session_dispatcher() -> None:
    """Unregister the in-session dispatcher (test hygiene + session teardown)."""
    global _in_session_dispatcher
    _in_session_dispatcher = None

# --- D-RES-2 (a), RULED — the TIGHT budget + idea count (HARD caps). ----------
#
# Over-reach-guard-tight: enough to be useful to an overwhelmed user, short
# enough not to re-overwhelm. The research-subagent is TOLD to stay within
# MAX_RESEARCH_ROUNDTRIPS, and the provider makes at most that many research
# round-trips (AC.DRR.2). The synthesis surfaces at most MAX_LEVERAGE_IDEAS —
# one per axis at most — into the intake's close (AC.DRR.3).
MAX_RESEARCH_ROUNDTRIPS = 3
MAX_LEVERAGE_IDEAS = 3

# The hard wall-clock ceiling for the synchronous research dispatch (D-RES-3).
# On timeout the provider returns the AC.DRRGRACE.1 fallback rather than hanging.
DEFAULT_RESEARCH_TIMEOUT_SECONDS = 120.0

# The three sealed axes (the fixed contract — never widened in this slice).
AXES = ("effectiveness", "promotion_criteria", "existing_ai_tools")


# --- The research-source seam (the injectable boundary the AC tests drive). ---


@dataclass
class AxisResearch:
    """The structured intermediate a single bounded research round-trip yields
    for one axis. ``summary`` is the raw research finding (a few sentences);
    ``roundtrips`` is the number of search/fetch round-trips the subagent
    reported using for this axis (bound-enforcement telemetry — AC.DRR.2)."""

    axis: str
    summary: str
    roundtrips: int = 1


@dataclass
class RawRoleResearch:
    """The full three-axis raw research the synthesis folds into a few
    person-specific leverage ideas. Carries the per-axis findings + the total
    round-trips so the budget bound is observable (AC.DRR.2)."""

    role: str
    effectiveness: AxisResearch
    promotion_criteria: AxisResearch
    existing_ai_tools: AxisResearch

    @property
    def total_roundtrips(self) -> int:
        return (
            self.effectiveness.roundtrips
            + self.promotion_criteria.roundtrips
            + self.existing_ai_tools.roundtrips
        )


class ResearchUnavailableError(Exception):
    """The bounded research primitive could not produce a usable result.

    Raised by a ResearchSource when the ``claude`` binary / spawn-isolation
    primitive is absent, the dispatch fails, it times out, or it returns
    nothing parseable. The provider catches it and returns the AC.DRRGRACE.1
    clearly-marked fallback — it NEVER propagates out of ``research_role``.
    """


class ResearchSource(Protocol):
    """The bounded three-axis research primitive (the injectable boundary).

    Production: a bounded ``claude -p`` research-subagent (D-RES-1 (a)). Tests
    inject a deterministic source that exercises the SAME dispatch+parse+budget
    path without a live network call (AC.DRROUT.1's deterministic variant).

    Contract: return a :class:`RawRoleResearch` whose ``total_roundtrips`` is
    ``<= max_roundtrips``; raise :class:`ResearchUnavailableError` when no usable
    result can be produced within the budget.
    """

    def research(self, role: str, *, max_roundtrips: int) -> RawRoleResearch:  # pragma: no cover
        ...


# --- The production research source: a bounded claude -p research-subagent. ---

_RESEARCH_PROMPT = (
    "You are a bounded role-research subagent. Research the role: {role!r}.\n"
    "Use AT MOST {max_roundtrips} web search/fetch round-trips TOTAL across all "
    "three axes (this is a HARD budget — stay under it; a fast useful answer "
    "beats an exhaustive one).\n\n"
    "Research these three axes:\n"
    "  1. effectiveness: what habits + skills make someone effective in this role.\n"
    "  2. promotion_criteria: what tends to get people in this role promoted.\n"
    "  3. existing_ai_tools: which existing AI tools/solutions someone in this "
    "role could use (so loam could wrap them or take ideas to rebuild).\n\n"
    "Respond with ONLY a JSON object (no prose, no code fence), shape:\n"
    '{{"effectiveness": "<1-2 sentence finding>", '
    '"promotion_criteria": "<1-2 sentence finding>", '
    '"existing_ai_tools": "<1-2 sentence finding>", '
    '"roundtrips_used": <integer number of web round-trips you actually used>}}'
)


def _parse_research_envelope(role: str, result_text: str, max_roundtrips: int) -> RawRoleResearch:
    """Parse the research-subagent's JSON result into a RawRoleResearch.

    Tolerant of a ```json ... ``` fence wrapper (claude -p commonly fences).
    Raises ResearchUnavailableError on anything unparseable / missing an axis —
    the provider then returns the AC.DRRGRACE.1 fallback.
    """
    text = (result_text or "").strip()
    # Strip a markdown code fence if present.
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[len("json"):]
        text = text.strip()
    # Find the first JSON object if there is leading/trailing prose.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ResearchUnavailableError(
            f"research-subagent returned non-JSON for role {role!r}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ResearchUnavailableError(
            f"research-subagent envelope is not an object for role {role!r}"
        )
    summaries = {}
    for axis in AXES:
        value = payload.get(axis)
        if not isinstance(value, str) or not value.strip():
            raise ResearchUnavailableError(
                f"research-subagent missing/empty axis {axis!r} for role {role!r}"
            )
        summaries[axis] = value.strip()
    # The subagent reports the round-trips it used; clamp to the budget so a
    # mis-reported overshoot can still be observed (AC.DRR.2) but the recorded
    # per-axis telemetry never silently exceeds the cap.
    reported = payload.get("roundtrips_used")
    try:
        used = int(reported)
    except (TypeError, ValueError):
        used = max_roundtrips
    used = max(1, min(used, max_roundtrips))
    # Distribute the reported round-trips across the three axes (the budget is a
    # TOTAL ceiling, not per-axis); the first axis carries the remainder so the
    # sum equals the reported total and total_roundtrips stays <= the budget.
    per_axis, remainder = divmod(used, len(AXES))
    counts = [per_axis] * len(AXES)
    for i in range(remainder):
        counts[i] += 1
    # Guarantee each axis is recorded as having taken at least the research it
    # contributed (a 0 would understate); but never inflate past the total.
    return RawRoleResearch(
        role=role,
        effectiveness=AxisResearch("effectiveness", summaries["effectiveness"], counts[0]),
        promotion_criteria=AxisResearch(
            "promotion_criteria", summaries["promotion_criteria"], counts[1]
        ),
        existing_ai_tools=AxisResearch(
            "existing_ai_tools", summaries["existing_ai_tools"], counts[2]
        ),
    )


class ClaudeSubagentResearchSource:
    """RESIDUAL ResearchSource: a bounded ``claude -p`` research-subagent.

    **No longer the production default** (AC.RES1.1) — the production source is
    :class:`InSessionResearchSource`, which fans out an in-session subagent
    accounted against the subscription plan limits rather than the post-June-15
    metered Agent SDK credit a detached ``claude -p`` draws from. This class
    STAYS as the residual / explicit-opt-in mechanism: it is the only research
    source that runs WITHOUT a living parent session to dispatch an in-session
    subagent from, and keeping it preserves the ``loam_spawn_isolation`` guard's
    residual-only role (do NOT delete it — the launchd-sessionless residual `-p`
    path still needs the guard; deleting this would re-expose those spawns to the
    proven Telegram kill vector — plan §3 Surface #3 / H-3).

    Composes the Claude-native forked-research-subagent primitive via a
    subprocess spawned through the MANDATED ``loam_spawn_isolation`` primitive
    (D-RES-1 (a)). NO Anthropic API key — subscription-routed
    (``feedback_no_anthropic_api_key``). Spawn-isolated so it cannot steal the
    operator's Telegram bot slot
    (``feedback_spawned_claude_must_isolate_telegram_plugin``).

    LAZY-imports ``loam_spawn_isolation`` inside ``research`` (it is not a
    workspace-bootstrap dependency); on ImportError, a missing ``claude`` binary,
    a dispatch failure, or a timeout it raises :class:`ResearchUnavailableError`
    so the provider returns the AC.DRRGRACE.1 fallback.
    """

    def __init__(
        self,
        *,
        model: str = "sonnet",
        timeout_seconds: float = DEFAULT_RESEARCH_TIMEOUT_SECONDS,
    ) -> None:
        self._model = model
        self._timeout_seconds = timeout_seconds

    def research(self, role: str, *, max_roundtrips: int) -> RawRoleResearch:
        try:
            from loam_spawn_isolation import spawn_isolated_claude
        except ImportError as exc:  # pragma: no cover - environmental
            raise ResearchUnavailableError(
                f"loam_spawn_isolation not importable ({exc}); the bounded "
                "research-subagent cannot be spawned isolated — degrading to "
                "the fallback synthesis."
            ) from exc

        prompt = _RESEARCH_PROMPT.format(role=role, max_roundtrips=max_roundtrips)
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
        except Exception as exc:  # noqa: BLE001 — any spawn/timeout failure -> fallback
            raise ResearchUnavailableError(
                f"research-subagent dispatch failed for role {role!r}: {exc}"
            ) from exc

        if proc.returncode != 0:
            raise ResearchUnavailableError(
                f"research-subagent exited {proc.returncode} for role {role!r}: "
                f"{(proc.stderr or '')[:300]}"
            )
        raw = (proc.stdout or "").strip()
        try:
            envelope = json.loads(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            raise ResearchUnavailableError(
                f"research-subagent stdout not a claude -p JSON envelope for "
                f"role {role!r}: {exc}"
            ) from exc
        if not isinstance(envelope, dict):
            raise ResearchUnavailableError(
                f"research-subagent envelope not an object for role {role!r}"
            )
        result_text = envelope.get("result") or ""
        return _parse_research_envelope(role, result_text, max_roundtrips)


# --- The PRODUCTION research source: an in-session subagent (AC.RES1.1). ------


class InSessionResearchSource:
    """Production ResearchSource: a bounded IN-SESSION research subagent.

    The default the production provider uses (AC.RES1.1). Instead of spawning a
    detached ``claude -p`` subprocess, it dispatches the SAME bounded research
    prompt as an in-session subagent (the Task primitive) through the dispatcher
    the live host session registered via :func:`set_in_session_dispatcher`, and
    parses the subagent's result text through the UNCHANGED
    :func:`_parse_research_envelope`.

    **Why this is the win:** in-session subagents share the parent session — they
    are accounted against the subscription plan limits, NOT the post-June-15
    metered Agent SDK credit a ``claude -p`` spawn draws from. They also share
    the parent's MCP, so they do NOT re-load the Telegram plugin and SIGTERM the
    operator's bot-poller slot — the kill vector ``loam_spawn_isolation`` guards
    does not exist on this path, which is why the converted path NEVER touches
    the spawn-isolation chokepoint (no subprocess argv to isolate). NO Anthropic
    API key — the host session is subscription-routed
    (``feedback_no_anthropic_api_key``).

    **Graceful degradation (AC.RES1.3 / AC.DRRGRACE.1).** When no dispatcher is
    registered (running outside a live session, or the session never wired one),
    the dispatcher raises, or its result is unparseable, this raises
    :class:`ResearchUnavailableError` so the provider returns the clearly-marked
    fallback — the SAME degrade the old ``claude``-absent case produced. The
    provider is honestly not-a-session: with no live session, it degrades.
    """

    def __init__(self, *, model: str = "sonnet") -> None:
        self._model = model

    def research(self, role: str, *, max_roundtrips: int) -> RawRoleResearch:
        dispatcher = get_in_session_dispatcher()
        if dispatcher is None:
            raise ResearchUnavailableError(
                "no in-session subagent dispatcher registered — the bounded "
                "research subagent cannot be fanned out (running outside a live "
                "session, or the session has not wired one). Degrading to the "
                "fallback synthesis (AC.DRRGRACE.1)."
            )
        prompt = _RESEARCH_PROMPT.format(role=role, max_roundtrips=max_roundtrips)
        try:
            result_text = dispatcher(prompt)
        except Exception as exc:  # noqa: BLE001 — any dispatch failure -> fallback
            raise ResearchUnavailableError(
                f"in-session research subagent dispatch failed for role "
                f"{role!r}: {exc}"
            ) from exc
        # The in-session subagent returns its result text directly (the JSON the
        # prompt asks for, possibly fenced) — there is no `claude -p` JSON
        # envelope to unwrap; the parse path is shared with the residual source.
        return _parse_research_envelope(role, result_text, max_roundtrips)


# --- The synthesis: raw three-axis research -> a few person-specific ideas. ---


def _synthesize(raw: RawRoleResearch) -> RoleResearchResult:
    """Fold raw three-axis research into a SHORT, person-specific
    ``RoleResearchResult`` (``is_stub=False`` — AC.DRR.1).

    The synthesis IS the deliverable. The three axis fields carry the
    role-derived research; ``as_leverage_ideas()`` (the sealed fold-back) turns
    them into the surfaced ideas. Over-reach guard: short + references the role,
    never a dump (AC.DRR.3). Deterministic fold (no second LLM round-trip is
    needed to keep it short + person-specific — and an extra call would spend the
    budget the over-reach guard protects)."""
    role = raw.role
    return RoleResearchResult(
        role=role,
        effectiveness=raw.effectiveness.summary,
        promotion_criteria=raw.promotion_criteria.summary,
        existing_ai_tools=raw.existing_ai_tools.summary,
        is_stub=False,
    )


def _fallback_result(role: str) -> RoleResearchResult:
    """The AC.DRRGRACE.1 clearly-marked fallback (research primitive
    unavailable / timed out / unusable). Names the three axes for the role so
    the intake's close still surfaces >=1 leverage idea, marked ``is_stub=True``
    so the caller can tell it is a degraded-not-real result — NEVER raises,
    NEVER hangs, NEVER returns empty. Mirrors the N3 baseline's
    no-interrogation-by-weight protection, now at the real-provider layer."""
    return RoleResearchResult(
        role=role,
        effectiveness=(
            f"the habits + skills that make a {role} effective — a deeper "
            "research pass wasn't available just now, so here's a starting frame"
        ),
        promotion_criteria=(
            f"what tends to get a {role} recognised and promoted to the next level"
        ),
        existing_ai_tools=(
            f"AI tools a {role} could use that loam could wrap or rebuild for you"
        ),
        is_stub=True,
    )


# --- The real provider (satisfies the sealed ResearchProvider Protocol). ------


class RoleResearchProvider:
    """The REAL ``ResearchProvider`` (AC.DRR.* / AC.DRRSEAM.* / AC.DRROUT.*).

    Given a role: run a BOUNDED three-axis research pass (the injected
    ResearchSource, default = the ``claude -p`` research-subagent), then
    SYNTHESIZE a few person-specific leverage ideas, returning the sealed
    ``RoleResearchResult`` shape with ``is_stub=False``. On any research
    failure, return the AC.DRRGRACE.1 fallback (``is_stub=True``) — never raise,
    never hang.

    Implements the sealed ``ResearchProvider`` Protocol structurally
    (``research_role(role) -> RoleResearchResult``) so the intake's
    ``as_leverage_ideas()`` fold-back consumes it UNCHANGED (AC.DRRSEAM.1).
    """

    def __init__(
        self,
        *,
        research_source: ResearchSource | None = None,
        max_roundtrips: int = MAX_RESEARCH_ROUNDTRIPS,
        synthesize: Callable[[RawRoleResearch], RoleResearchResult] = _synthesize,
    ) -> None:
        self._source: ResearchSource = research_source or InSessionResearchSource()
        self._max_roundtrips = max_roundtrips
        self._synthesize = synthesize
        # Bound-enforcement telemetry the AC.DRR.2 test reads.
        self.last_roundtrips: int | None = None

    def research_role(self, role: str) -> RoleResearchResult:
        try:
            raw = self._source.research(role, max_roundtrips=self._max_roundtrips)
        except ResearchUnavailableError:
            self.last_roundtrips = None
            return _fallback_result(role)
        # Hard bound enforcement (AC.DRR.2): a source that overshoots the budget
        # is treated as unavailable — the bound is a HARD over-reach-guard
        # constraint, never silently exceeded (halt trigger #4).
        self.last_roundtrips = raw.total_roundtrips
        if raw.total_roundtrips > self._max_roundtrips:
            return _fallback_result(role)
        return self._synthesize(raw)


def make_default_research_provider() -> RoleResearchProvider:
    """Construct the production real provider (the IN-SESSION research subagent
    source, the tight D-RES-2 budget). This is what ``register_real_provider``
    registers behind ``deep_role_research.default_research_provider()``.

    AC.RES1.1: the default source is :class:`InSessionResearchSource` — no
    detached ``claude -p`` subprocess; the research is fanned out as an
    in-session subagent through the host-session-registered dispatcher
    (subscription-pool billing, not the metered Agent SDK credit)."""
    return RoleResearchProvider()
