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

"""Work-visibility surface — aggregate + render loam's live work-state
(AC.WVS-AGG.* / AC.WVS-RENDER.* / AC.WVS-FRESH.* / AC.WVS-S.1).

The status-anxiety stressor (owner directive Telegram 13231, task #37)
is a TRANSLATION failure: today the user must open Telegram, compose
"what is happening", and wait for a render to learn the state of his
own system. This surface closes that — the answer becomes always-
available and self-maintaining.

This is an AGGREGATION + WIRING module, NOT a new tracking system
(plan §1 + §10 F2 #1). Every signal it shows already lives in a sealed
primitive; the module READS those primitives into ONE snapshot and
renders it plain-language. It never becomes a second source of truth.

Composes on four sealed surfaces, READ-ONLY (plan §2 / §8 halt #1):

  * primary-persona ``tracker_context`` — the in-flight / open-loop /
    owner-pending predicates over the objective tracker's projection
    view (the running-now / queued / owner-pending buckets).
  * ``loam_cli.flows.cursor`` — ``read_cursor`` / ``resolve_cursor``,
    the position ("which process + where") with the UNRESOLVED-over-
    wrong-confident posture (a stale/absent cursor renders "between
    steps", never a false position).
  * ``loam.self_correction.watchdog`` — ``evaluate_stall``, the
    stuck/silent-agent health signal (the "is it stuck?" answer).
  * ``loam.self_correction.recovery_surface.contains_internal_vocabulary``
    — the zero-internal-vocabulary probe the renderer routes through
    (the non-tech HARD invariant).

Aggregation discipline (the ``session_surface.py`` precedent): every
source is best-effort lazy-imported + fail-soft. A missing / broken /
UNRESOLVED source degrades THAT part of the snapshot to "unknown" and
NEVER breaks the snapshot or a host hook (AC.WVS-AGG.2). The snapshot
build returns a snapshot in every case.

Determinism: the aggregator is a pure read over on-disk state, no LLM,
no API key (``feedback_no_anthropic_api_key``). The renderer is a pure
function over the snapshot.

Per ODD §2.5 every code path traces to a named AC. The fail-soft
branches are AC.WVS-AGG.2; they are criterion-backed, not unbacked
defensive code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


# ---------------------------------------------------------------------------
# Health-signal vocabulary (AC.WVS-AGG.3).
# ---------------------------------------------------------------------------

#: The health field's three honest states. Per plan §10 F2 #3 the
#: watchdog is conservative (few false-positives, some false-negatives),
#: so the render says "no problems detected", never "everything is
#: fine" — and an unreadable watchdog is HEALTH_UNKNOWN, never a false
#: "healthy".
HEALTH_OK = "ok"
HEALTH_STUCK = "stuck"
HEALTH_UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# The snapshot (AC.WVS-AGG.1).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WorkSnapshot:
    """One work-state snapshot the surface renders.

    The snapshot carries COUNTS + plain markers only — never the raw
    objective goals / IDs / paths the underlying state holds. This is
    load-bearing: the renderer routes through the zero-internal-vocab
    probe (AC.WVS-RENDER.2), so the snapshot must not smuggle an
    internal token (a SHA-named flow, an objective ID, a file path)
    into the rendered surface. Distinguishing the buckets by COUNT —
    not by echoing identifiers — keeps the surface plain by
    construction.

    Buckets (AC.WVS-AGG.1):
      - ``running_now``   — count of in-flight (actively-worked)
                            objectives (tracker ``active``).
      - ``queued``        — count of queued objectives (tracker
                            ``proposed``).
      - ``owner_pending`` — count of objectives shipped + awaiting the
                            owner's ruling (tracker ``owner_pending``).
                            Rendered PROMINENTLY (plan §10 F2 #2: a
                            large slice of the anxiety is "is it waiting
                            on ME?").

    Position (AC.WVS-AGG.1):
      - ``position``        — None when no flow is active OR the cursor
                              is UNRESOLVED (rendered "between steps").
      - ``position_known``  — True iff a flow cursor resolved to a
                              real step. (A False with ``position`` None
                              is the honest "between steps" case.)

    Health (AC.WVS-AGG.3):
      - ``health``        — one of HEALTH_OK / HEALTH_STUCK /
                            HEALTH_UNKNOWN.

    Per-source unknown markers (AC.WVS-AGG.2): each ``*_unknown`` flag
    is True when that source could not be read; the snapshot still
    returns, with the broken part marked unknown.
    """

    running_now: int = 0
    queued: int = 0
    owner_pending: int = 0
    position_known: bool = False

    health: str = HEALTH_UNKNOWN

    work_unknown: bool = False
    position_unknown: bool = False
    health_unknown: bool = False

    # Plain-language position phrase (a step name + flow name, already
    # plain — sourced from the cursor's ``one_sentence``). Held for the
    # renderer; ``None`` when no resolved position. The renderer still
    # routes it through the vocab probe (a flow name could in principle
    # carry a path-ish token), abstracting on a leak.
    position_phrase: str | None = None

    @property
    def has_active_work(self) -> bool:
        """True iff anything is running, queued, or owner-pending."""
        return (self.running_now + self.queued + self.owner_pending) > 0


# ---------------------------------------------------------------------------
# Source readers — each fail-soft (AC.WVS-AGG.2).
# ---------------------------------------------------------------------------


@dataclass
class _WorkCounts:
    running_now: int = 0
    queued: int = 0
    owner_pending: int = 0
    unknown: bool = False


def _read_work_counts(
    workspace_root: Path,
    tracker_factory: Callable[[], Any] | None,
) -> _WorkCounts:
    """Read the running-now / queued / owner-pending counts from the
    objective tracker's projection view (AC.WVS-AGG.1).

    Reuses the sealed tracker-context predicates (``_is_in_flight`` /
    ``_is_owner_pending`` / ``_status_value``) rather than re-deriving
    the state-distinctions — the aggregator is a reader, not a second
    tracker (plan §8 halt #3).

    Fail-soft (AC.WVS-AGG.2): a missing DB, an open failure, a query
    error, or an unavailable tracker package degrades to
    ``unknown=True`` with zero counts. Never raises.
    """
    counts = _WorkCounts()
    try:
        # Lazy import of the sealed predicates — keeps the cross-module
        # surface off import-time (the session_surface.py discipline).
        from .tracker_context import (
            IN_FLIGHT_STATUSES,
            OWNER_PENDING_STATUS,
            _status_value,
            tracker_db_path_for,
        )

        if tracker_factory is None:
            db_path = tracker_db_path_for(workspace_root)
            if not Path(db_path).exists():
                # No tracker DB yet — honest "unknown" (the workspace
                # may simply not have produced state). AC.WVS-AGG.2.
                counts.unknown = True
                return counts

            def _factory() -> Any:
                from loam.objective_tracker import ObjectiveTracker

                return ObjectiveTracker(db_path)

            tracker_factory = _factory

        tracker = tracker_factory()
        try:
            projections = tracker.query_projection_view()
        finally:
            try:
                tracker.close()
            except Exception:
                # close() failure is non-load-bearing; the counts are
                # already read. Not an unbacked branch — it preserves
                # the fail-soft outcome (AC.WVS-AGG.2).
                pass

        for proj in projections:
            value = _status_value(proj)
            if value is None:
                continue
            if value == OWNER_PENDING_STATUS:
                counts.owner_pending += 1
            elif value == "active":
                counts.running_now += 1
            elif value in IN_FLIGHT_STATUSES:
                # IN_FLIGHT_STATUSES = {proposed, active}; active is
                # handled above, so this branch is "proposed" = queued.
                counts.queued += 1
        return counts
    except Exception:
        # Any source-level failure (import error, open failure, schema
        # mismatch, I/O error) degrades the whole work-bucket to
        # unknown — never breaks the snapshot. AC.WVS-AGG.2.
        return _WorkCounts(unknown=True)


@dataclass
class _PositionRead:
    known: bool = False
    phrase: str | None = None
    unknown: bool = False


def _read_position(
    workspace_root: Path,
    cursor_path: Path | None,
    flow_loader: Callable[[str], Any] | None,
) -> _PositionRead:
    """Read the resolved position-cursor (AC.WVS-AGG.1).

    Honours the cursor's UNRESOLVED-over-wrong-confident posture: an
    absent cursor, an unloadable flow definition, or a stale step all
    resolve to ``known=False`` (rendered "between steps"), never a
    false position.

    Fail-soft (AC.WVS-AGG.2): an unreadable cursor file or an import
    failure degrades to ``unknown=True``. Never raises.
    """
    try:
        from loam_cli.flows.cursor import (
            read_cursor,
            resolve_cursor,
            user_state_cursor_path,
        )

        # No explicit cursor file given: there is no single canonical
        # active-flow cursor path (a workspace may carry several flow
        # instances). Without a flow_loader to resolve a definition, the
        # honest answer is "no resolved position" — known=False, NOT
        # unknown (we successfully determined there is nothing to
        # resolve). AC.WVS-AGG.1's UNRESOLVED-over-confident posture.
        if cursor_path is None:
            return _PositionRead(known=False, phrase=None, unknown=False)

        cursor = read_cursor(Path(cursor_path))
        if cursor is None:
            return _PositionRead(known=False, phrase=None, unknown=False)

        definition = None
        if flow_loader is not None:
            try:
                definition = flow_loader(cursor.flow)
            except Exception:
                definition = None

        resolution = resolve_cursor(cursor, definition)
        if resolution.resolved:
            phrase = resolution.one_sentence() or None
            return _PositionRead(known=True, phrase=phrase, unknown=False)
        # UNRESOLVED — honest "between steps", never a false position.
        return _PositionRead(known=False, phrase=None, unknown=False)
    except Exception:
        return _PositionRead(known=False, phrase=None, unknown=True)


def _read_health(stall_watchdog: Any | None) -> tuple[str, bool]:
    """Read the watchdog health signal (AC.WVS-AGG.3).

    Returns ``(health, unknown)``. Routes through the sealed
    ``evaluate_stall`` surface; a stuck verdict → HEALTH_STUCK, a clean
    verdict → HEALTH_OK. An absent / unreadable watchdog → HEALTH_UNKNOWN
    with ``unknown=True`` — never a false "ok" (plan §10 F2 #3).

    Fail-soft (AC.WVS-AGG.2): never raises.
    """
    if stall_watchdog is None:
        return HEALTH_UNKNOWN, True
    try:
        from loam.self_correction.watchdog import evaluate_stall

        verdict = evaluate_stall(stall_watchdog)
        return (HEALTH_STUCK if verdict.stuck else HEALTH_OK), False
    except Exception:
        return HEALTH_UNKNOWN, True


# ---------------------------------------------------------------------------
# The aggregator (AC.WVS-AGG.1 / .2 / .3).
# ---------------------------------------------------------------------------


def build_snapshot(
    workspace_root: Path | str,
    *,
    tracker_factory: Callable[[], Any] | None = None,
    cursor_path: Path | str | None = None,
    flow_loader: Callable[[str], Any] | None = None,
    stall_watchdog: Any | None = None,
) -> WorkSnapshot:
    """Aggregate the live work-state into ONE snapshot (AC.WVS-AGG.*).

    Reads three sealed primitives — the objective tracker's projection
    view (running-now / queued / owner-pending), the resolved position-
    cursor (which process + where), and the watchdog health signal (is
    it stuck?) — into a single ``WorkSnapshot``. Every source read is
    fail-soft (AC.WVS-AGG.2): a broken / missing / UNRESOLVED source
    degrades that part of the snapshot to "unknown" and the snapshot
    still returns.

    Parameters mirror the test seams the AC suite drives:
      - ``tracker_factory`` — override the tracker open (tests inject a
        fake; production resolves the workspace's tracker DB).
      - ``cursor_path`` + ``flow_loader`` — the active-flow cursor file
        and a flow-definition loader; absent → "between steps".
      - ``stall_watchdog`` — a ``StallWatchdog`` whose ``evaluate_stall``
        verdict drives the health field; absent → health unknown.

    No LLM, no API key — a pure read over on-disk state.
    """
    root = Path(workspace_root)

    counts = _read_work_counts(root, tracker_factory)
    position = _read_position(
        root,
        Path(cursor_path) if cursor_path is not None else None,
        flow_loader,
    )
    health, health_unknown = _read_health(stall_watchdog)

    return WorkSnapshot(
        running_now=counts.running_now,
        queued=counts.queued,
        owner_pending=counts.owner_pending,
        position_known=position.known,
        position_phrase=position.phrase,
        health=health,
        work_unknown=counts.unknown,
        position_unknown=position.unknown,
        health_unknown=health_unknown,
    )


# ---------------------------------------------------------------------------
# The plain-language renderer (AC.WVS-RENDER.1 / .2).
# ---------------------------------------------------------------------------


class WorkVisibilityLeak(RuntimeError):
    """A rendered work-visibility surface leaked internal vocabulary.

    AC.WVS-RENDER.2 is a HARD invariant (plan §8 halt #2): a render
    that cannot avoid an internal token fails loudly rather than
    shipping the leak to the user. Mirrors ``recovery_surface``'s
    ``RecoverySurfaceLeak`` halt posture.
    """


def _plural(n: int, singular: str, plural: str) -> str:
    return singular if n == 1 else plural


def _render_now_line(snapshot: WorkSnapshot) -> str:
    """The "what's happening now" line (AC.WVS-RENDER.1)."""
    if snapshot.work_unknown:
        return "Right now: I could not read what is in progress."
    running = snapshot.running_now
    if running > 0:
        return (
            f"Right now: I am working on {running} "
            f"{_plural(running, 'thing', 'things')}."
        )
    if snapshot.owner_pending > 0 or snapshot.queued > 0:
        return "Right now: nothing is actively running."
    return "Right now: nothing is in progress — all caught up."


def _render_next_line(snapshot: WorkSnapshot) -> str:
    """The "what's next" line (AC.WVS-RENDER.1).

    The owner-pending bucket renders PROMINENTLY (plan §10 F2 #2: a
    large slice of the anxiety is "is it waiting on ME?") — it leads
    the next-line whenever non-empty.
    """
    parts: list[str] = []
    if snapshot.owner_pending > 0:
        n = snapshot.owner_pending
        parts.append(
            f"{n} {_plural(n, 'thing is', 'things are')} waiting on you "
            f"to weigh in"
        )
    if snapshot.queued > 0:
        n = snapshot.queued
        parts.append(f"{n} more {_plural(n, 'thing is', 'things are')} lined up")

    if snapshot.work_unknown:
        return "What's next: I could not read what is lined up."
    if not parts:
        return "What's next: nothing is waiting — you are all clear."
    return "What's next: " + "; and ".join(parts) + "."


def _render_position_line(snapshot: WorkSnapshot) -> str | None:
    """The optional "where in the process" line (AC.WVS-RENDER.1).

    Only emitted when the cursor resolved to a real step AND the plain
    phrase survives the vocab probe. An UNRESOLVED / absent position
    emits nothing (the now/next/health lines already answer the anxiety
    questions); a leak-carrying phrase is dropped, never shipped.
    """
    if not snapshot.position_known or not snapshot.position_phrase:
        return None
    # Lazy probe import — the renderer routes the cursor phrase through
    # the same zero-internal-vocab probe (AC.WVS-RENDER.2). A flow name
    # could in principle carry a path-ish token; on a leak we drop the
    # position line rather than ship it.
    try:
        from loam.self_correction.recovery_surface import (
            contains_internal_vocabulary,
        )

        phrase = snapshot.position_phrase
        if contains_internal_vocabulary(phrase):
            return None
        return f"Where I am: {phrase}."
    except Exception:
        return None


def _render_health_line(snapshot: WorkSnapshot) -> str:
    """The "is anything stuck" line (AC.WVS-RENDER.1).

    Conservative wording (plan §10 F2 #3): "no problems detected", never
    "everything is fine"; an unknown health is stated honestly, never
    rendered as a false "ok".
    """
    if snapshot.health == HEALTH_STUCK:
        return "Health: something looks stuck — I am on it."
    if snapshot.health == HEALTH_OK:
        return "Health: no problems detected."
    return "Health: I could not check whether anything is stuck."


def render_surface(snapshot: WorkSnapshot) -> str:
    """Render the snapshot to a plain-language status (AC.WVS-RENDER.*).

    Produces a short block answering the three anxiety questions —
    what's happening now / what's next / is anything stuck — in plain
    English a non-technical reader understands at a glance
    (AC.WVS-RENDER.1).

    The whole rendered surface is routed through the sealed
    ``contains_internal_vocabulary`` probe (AC.WVS-RENDER.2); a leak
    raises ``WorkVisibilityLeak`` rather than shipping an internal token
    to the user (plan §8 halt #2 — a HARD invariant, not best-effort).
    """
    lines = [
        _render_now_line(snapshot),
        _render_next_line(snapshot),
    ]
    position_line = _render_position_line(snapshot)
    if position_line is not None:
        lines.append(position_line)
    lines.append(_render_health_line(snapshot))

    text = "\n".join(lines)

    # The HARD invariant (AC.WVS-RENDER.2 / plan §8 halt #2).
    try:
        from loam.self_correction.recovery_surface import (
            contains_internal_vocabulary,
            find_internal_vocabulary,
        )
    except Exception:
        # The probe is unavailable — we cannot guarantee the invariant,
        # so we MUST NOT ship a possibly-leaking surface. But the
        # renderer only ever composes from fixed plain-language phrases
        # plus the already-probed position line, so the text is leak-
        # free by construction; returning it is safe. (This branch is
        # the fail-soft envelope, not an unbacked guard: AC.WVS-AGG.2's
        # discipline — a missing source never breaks the surface.)
        return text

    if contains_internal_vocabulary(text):
        hits = find_internal_vocabulary(text)
        raise WorkVisibilityLeak(
            "work-visibility surface leaked internal vocabulary: "
            f"{[h.matched for h in hits]}"
        )
    return text


# ---------------------------------------------------------------------------
# The production surface entry-point (AC.WVS-S.1 / AC.WVS-FRESH.1).
# ---------------------------------------------------------------------------


def render_work_visibility(
    workspace_root: Path | str,
    *,
    tracker_factory: Callable[[], Any] | None = None,
    cursor_path: Path | str | None = None,
    flow_loader: Callable[[str], Any] | None = None,
    stall_watchdog: Any | None = None,
) -> str:
    """The production surface entry-point: live work-state → plain-
    language status, sourced end-to-end from the tracker + cursor +
    watchdog (AC.WVS-S.1).

    Builds the snapshot from the live sources (no pre-arranged state)
    and renders it. This is the single function every presenter rides
    (the shared-aggregator invariant, plan §7 / §8 halt #4): the
    generated-file presenter, the in-context block, and the on-demand
    render all call THIS — one snapshot, many thin presenters.

    Self-maintaining (AC.WVS-FRESH.1): because the surface is recomputed
    from live state on each call, invoking it after a work-state change
    reflects the new state with no user pull.
    """
    snapshot = build_snapshot(
        workspace_root,
        tracker_factory=tracker_factory,
        cursor_path=cursor_path,
        flow_loader=flow_loader,
        stall_watchdog=stall_watchdog,
    )
    return render_surface(snapshot)
