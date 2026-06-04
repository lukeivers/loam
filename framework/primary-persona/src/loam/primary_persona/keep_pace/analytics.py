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

"""ANALYTICS — the LAST WMS increment (increment 7).

A SMALL, conservatively-scoped set of genuinely-actionable insights
derived READ-ONLY over the inc-2 work-item event log + projection,
surfaced ON-DEMAND in plain language, transparent like the inc-4
prioritization reasons. This module builds NO new store, field, event
kind, query, lifecycle, lens, or per-turn block. It is ONE keep-pace
module composing two already-built read-only surfaces (Lens-1):

  - the PROJECTION (``query_projection_view`` via the shared
    ``load_work_items`` helper) — ``belongs_to_project`` /
    ``tagged_streams`` / ``status`` / ``last_transition_at`` / edges, for
    the pile-up + stuck insights;
  - the EVENT LOG (``runtime.store.all_events()`` — the typed historical
    stream carrying every ``ObjectiveCreated.created_at`` and terminal
    ``StatusTransitioned.created_at``) — the COMPLETE transition history,
    for the completion-vs-intake balance insight, which a current-state
    snapshot cannot reconstruct (AC.ANL.BALANCE.2).

The conservative THREE insights — each one CHANGES what the user does
next (the Lens-2 test; the rest are vanity for a single person and are
explicitly CUT, D-ANL.2):

  1. ``compute_pileup`` — WHERE work is piling up / stalling: open items
     grouped by project (or stream), ranked by count + collective
     staleness, naming the most-accumulated group with its plain reason
     (count + how long the oldest item has sat — the cycle-time as a
     SUPPORTING phrase only, D-ANL.5). (AC.ANL.PILEUP.*)
  2. ``compute_stuck`` — CHRONICALLY blocked / waiting items: items in
     ``blocked`` status or carrying an external-party ``waits_on`` edge
     past a staleness threshold, named with what they wait on.
     (AC.ANL.STUCK.*)
  3. ``compute_balance`` — COMPLETION-vs-INTAKE over a recent window:
     ``ObjectiveCreated`` vs terminal ``StatusTransitioned`` counts
     DERIVED OVER THE EVENT-LOG HISTORY (not a snapshot) in the window,
     phrased as a NON-judgmental orienting signal (RF #4). (AC.ANL.BALANCE.*)

``render_analytics_block`` composes the three into ONE concise capped
fail-soft block via the shared ``finalise_block`` discipline, each insight
a plain-language transparent sentence with zero internal vocabulary
(AC.ANL.SURFACE.2), honest-empty per-insight when there is no signal. It
is the ON-DEMAND production entry point — MIRRORS ``render_plate_block`` /
``render_goals_block`` and registers NO ``TriggerKind.turn`` contributor
(D-ANL.3 / AC.ANL.SURFACE.1).

The numeric thresholds (the "chronically" staleness floor, the pile-up
stalling cadence, the intake window) are calibrate-on-use METHOD-DEFAULTS,
not owner constants (D-ANL.6 — the F4 scope-confidence line: the SET of
insights is the owner's call, the constants are the builder's calibratable
default). A too-high threshold simply surfaces fewer insights (fail-quiet,
the safe direction for a low-confidence feature). The reference ``now`` is
an injectable method-default so the clock is deterministic in test and the
calibration seam is explicit; nothing here mutates the store or widens the
read-only surface.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

from .lens_render import finalise_block, load_work_items

# ---------------------------------------------------------------------
# Calibrate-on-use method-defaults (D-ANL.6 — NOT owner constants). A
# too-high threshold surfaces fewer insights (fail-quiet); widen on real
# use, mirroring inc-4's weights + #34's thresholds.
# ---------------------------------------------------------------------

# How long (days) an item must have sat untouched before it counts toward
# a group's "stalling" signal in the pile-up insight.
_PILEUP_STALE_DAYS = 14
# A group needs at least this many open items to be a meaningful pile-up
# (no "hottest of two evenly-spread items" theatre — AC.ANL.PILEUP.3).
_PILEUP_MIN_ITEMS = 3
# How long (days) a blocked / externally-waiting item must have sat before
# it is "chronically" stuck (AC.ANL.STUCK.1/.2). Recently-blocked items
# below this are normal and do NOT surface.
_STUCK_CHRONIC_DAYS = 7
# The recent window (days) the completion-vs-intake balance reads over.
_BALANCE_WINDOW_DAYS = 7
# How many chronically-stuck items the block names (Slice-D conciseness).
_STUCK_NAME_CAP = 3

_ANALYTICS_BLOCK_CHAR_CAP = 700

# Open (non-terminal) statuses — the work that can still pile up / stall.
_OPEN_STATUS_VALUES = frozenset(
    {"proposed", "active", "blocked", "owner_pending"}
)
# Terminal statuses — an item reaching one of these is "finished" for the
# completion-vs-intake balance (AC.ANL.BALANCE.1).
_TERMINAL_STATUS_VALUES = frozenset({"achieved", "abandoned"})


def _now(now: Optional[datetime]) -> datetime:
    """The reference clock — injectable method-default (deterministic in
    test; the explicit calibration seam in production)."""
    if now is not None:
        return now
    return datetime.now(timezone.utc)


def _parse_ts(raw: Any) -> Optional[datetime]:
    """Parse an ISO timestamp string to an aware ``datetime`` (UTC).

    Fail-soft: an absent / unparseable timestamp yields ``None`` (the
    caller treats it as "no age signal"), never a raise."""
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text)
    except (ValueError, TypeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _age_days(raw: Any, now: datetime) -> Optional[float]:
    """Whole-plus-fractional days between an ISO timestamp and ``now``.

    ``None`` when the timestamp is missing / unparseable."""
    dt = _parse_ts(raw)
    if dt is None:
        return None
    return (now - dt).total_seconds() / 86400.0


def _status_value(item: Any) -> str:
    return str(
        getattr(getattr(item, "status", None), "value", "")
        or getattr(item, "status", "")
        or ""
    )


def _edge_kind_value(edge: Any) -> str:
    return str(
        getattr(getattr(edge, "edge_kind", None), "value", "")
        or getattr(edge, "edge_kind", "")
        or ""
    )


def _plain_name(raw: Any) -> str:
    """Plain-language render of a slug-ish group key (mirrors the goals /
    lens slug->phrase convention). Zero internal vocabulary
    (AC.ANL.SURFACE.2): a project slug ``money-independence`` reads as
    ``money independence``."""
    return str(raw or "").strip().replace("-", " ")


def _humanize_age(days: float) -> str:
    """A plain-language age phrase (no raw numbers-as-IDs; an honest
    human duration). Supporting cycle-time phrasing only (D-ANL.5)."""
    d = int(round(days))
    if d <= 0:
        return "today"
    if d == 1:
        return "a day"
    if d < 7:
        return f"{d} days"
    if d < 14:
        return "about a week"
    if d < 21:
        return "about two weeks"
    if d < 31:
        return "a few weeks"
    if d < 60:
        return "over a month"
    return "a couple of months"


# ---------------------------------------------------------------------
# Insight 1 — where work is piling up / stalling (AC.ANL.PILEUP.*)
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PileUp:
    """The most-accumulated open-work group + its transparent reason.

    ``group`` is the plain-language project/stream name; ``open_count`` is
    how many open items sit under it; ``oldest_age_days`` is how long the
    oldest has sat (the supporting cycle-time phrase, D-ANL.5)."""

    group: str
    open_count: int
    oldest_age_days: Optional[float]

    def sentence(self) -> str:
        """The transparent plain-language insight (AC.ANL.PILEUP.2)."""
        base = f"Work is piling up under {self.group} — {self.open_count} open items"
        if self.oldest_age_days is not None and self.oldest_age_days >= 1:
            return f"{base}, and the oldest hasn't moved in {_humanize_age(self.oldest_age_days)}."
        return f"{base}."


def compute_pileup(
    items: list,
    *,
    now: Optional[datetime] = None,
    min_items: int = _PILEUP_MIN_ITEMS,
    stale_days: int = _PILEUP_STALE_DAYS,
) -> Optional[PileUp]:
    """Identify the project/stream where open work is most accumulating
    AND stalling — or ``None`` when there is no meaningful pile-up
    (AC.ANL.PILEUP.1/.3).

    Groups open items by ``belongs_to_project`` (falling back to the first
    tagged stream when an item is unbound). Ranks groups by open count,
    requiring (a) at least ``min_items`` open items AND (b) at least one
    item in the group stalled past ``stale_days`` — so an evenly-spread,
    nothing-stalled work set produces NO pile-up (no manufactured hottest
    group, AC.ANL.PILEUP.3). The ranking + grouping mechanism is the
    builder's call (the method-in-AC test passes)."""
    ref = _now(now)
    groups: dict[str, list[Any]] = {}
    for it in items:
        if _status_value(it) not in _OPEN_STATUS_VALUES:
            continue
        key = getattr(it, "belongs_to_project", None)
        if not key:
            streams = getattr(it, "tagged_streams", ()) or ()
            key = streams[0] if streams else None
        if not key:
            continue
        groups.setdefault(str(key), []).append(it)

    best: Optional[PileUp] = None
    best_rank: tuple = ()
    for key, members in groups.items():
        if len(members) < min_items:
            continue
        ages = [
            a
            for a in (_age_days(getattr(m, "last_transition_at", ""), ref) for m in members)
            if a is not None
        ]
        oldest = max(ages) if ages else None
        # A group must have at least one genuinely-stalled item to count
        # as a pile-up (AC.ANL.PILEUP.3 — no false hotspot).
        if oldest is None or oldest < stale_days:
            continue
        rank = (len(members), oldest)
        if not best or rank > best_rank:
            best_rank = rank
            best = PileUp(
                group=_plain_name(key),
                open_count=len(members),
                oldest_age_days=oldest,
            )
    return best


# ---------------------------------------------------------------------
# Insight 2 — chronically blocked / waiting items (AC.ANL.STUCK.*)
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class StuckItem:
    """One chronically-stuck item + what it waits on + how long."""

    goal: str
    waiting_on: Optional[str]
    age_days: Optional[float]

    def phrase(self) -> str:
        """The plain-language per-item phrase (AC.ANL.STUCK.1)."""
        who = f" on {self.waiting_on}" if self.waiting_on else ""
        if self.age_days is not None and self.age_days >= 1:
            return f"{self.goal} has been waiting{who} for {_humanize_age(self.age_days)}"
        return f"{self.goal} is stuck{who}"


def compute_stuck(
    items: list,
    *,
    now: Optional[datetime] = None,
    chronic_days: int = _STUCK_CHRONIC_DAYS,
    name_cap: int = _STUCK_NAME_CAP,
) -> list[StuckItem]:
    """Surface items that have been ``blocked`` or externally
    ``waits_on`` for longer than ``chronic_days`` — the forgotten-waiting
    nudge (AC.ANL.STUCK.1). Items blocked/waiting BELOW the threshold are
    normal and do NOT surface (AC.ANL.STUCK.2). An empty result is honest
    (AC.ANL.STUCK.3). The threshold + the edge/lifecycle read are the
    builder's call."""
    ref = _now(now)
    out: list[StuckItem] = []
    for it in items:
        status = _status_value(it)
        goal = str(getattr(it, "goal", "") or "").strip()
        if not goal:
            continue
        # The external party a waits_on edge names (an item waiting on
        # someone outside the work graph — the high-value forgotten case).
        party: Optional[str] = None
        for edge in getattr(it, "edges_out", ()) or ():
            if _edge_kind_value(edge) == "waits_on":
                p = getattr(edge, "party", None)
                if p:
                    party = str(p)
                    break
        is_waiting = status == "blocked" or party is not None
        if not is_waiting:
            continue
        age = _age_days(getattr(it, "last_transition_at", ""), ref)
        # Chronic-only: below the threshold is normal, do not surface
        # (AC.ANL.STUCK.2). A missing age is treated as not-yet-chronic
        # (fail-quiet — the safe direction).
        if age is None or age < chronic_days:
            continue
        out.append(StuckItem(goal=goal, waiting_on=party, age_days=age))
    # Oldest first (most-forgotten surfaces top), capped (Slice-D).
    out.sort(key=lambda s: s.age_days or 0.0, reverse=True)
    return out[:name_cap]


# ---------------------------------------------------------------------
# Insight 3 — completion-vs-intake balance (AC.ANL.BALANCE.*)
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class Balance:
    """Capture-vs-finish counts over a recent window (derived over the
    event-log history, AC.ANL.BALANCE.2)."""

    captured: int
    finished: int
    window_days: int

    @property
    def has_activity(self) -> bool:
        return self.captured > 0 or self.finished > 0

    def sentence(self) -> str:
        """A NON-judgmental orienting signal (RF #4) — never a scold
        (AC.ANL.BALANCE.1). Honest-empty when nothing happened
        (AC.ANL.BALANCE.3)."""
        window = "this week" if self.window_days == 7 else f"in the last {self.window_days} days"
        if not self.has_activity:
            return f"Nothing was captured or finished {window}."
        cap_word = "thing" if self.captured == 1 else "things"
        fin_word = "one" if self.finished == 1 else str(self.finished)
        finished_clause = (
            f"finished {fin_word}" if self.finished != 1 else "finished one"
        )
        base = (
            f"You captured {self.captured} {cap_word} and {finished_clause} {window}"
        )
        if self.captured > self.finished:
            return f"{base} — might be worth closing a few out."
        if self.finished >= self.captured and self.finished > 0:
            return f"{base} — you're keeping up."
        return f"{base}."


def _events_in_window(events: list, *, since: datetime) -> list:
    out = []
    for ev in events:
        ts = _parse_ts(getattr(ev, "created_at", ""))
        if ts is not None and ts >= since:
            out.append(ev)
    return out


def compute_balance(
    events: list,
    *,
    now: Optional[datetime] = None,
    window_days: int = _BALANCE_WINDOW_DAYS,
) -> Balance:
    """Count items CAPTURED vs FINISHED over the recent window, derived
    OVER THE EVENT-LOG HISTORY (AC.ANL.BALANCE.1/.2).

    ``captured`` = ``ObjectiveCreated`` events in the window;
    ``finished`` = ``StatusTransitioned`` events transitioning INTO a
    terminal status in the window. This rides the event log, not the
    current-state snapshot — so an item created AND finished within the
    window counts in BOTH, which a snapshot count cannot reconstruct
    (AC.ANL.BALANCE.2). An empty window yields a zero/zero honest result
    (AC.ANL.BALANCE.3 — no divide-by-zero theatre). The event-log walk +
    the window are the builder's call."""
    ref = _now(now)
    since = ref - timedelta(days=window_days)
    window = _events_in_window(events, since=since)
    captured = 0
    finished = 0
    for ev in window:
        kind = str(getattr(ev, "kind", "") or "")
        if kind == "objective_created":
            captured += 1
        elif kind == "status_transitioned":
            to_status = str(
                getattr(getattr(ev, "to_status", None), "value", "")
                or getattr(ev, "to_status", "")
                or ""
            )
            if to_status in _TERMINAL_STATUS_VALUES:
                finished += 1
    return Balance(captured=captured, finished=finished, window_days=window_days)


# ---------------------------------------------------------------------
# The ON-DEMAND render (AC.ANL.SURFACE.*) — D-ANL.3, mirrors plate/goals.
# NO TriggerKind.turn contributor. Production entry point.
# ---------------------------------------------------------------------


def _read_events(tracker_factory: Optional[Callable[[], Any]]) -> list:
    """Read the typed historical event stream READ-ONLY via
    ``runtime.store.all_events()`` (the EXISTING API — no new query, no
    store mutation). Fail-soft: an unresolvable tracker / a read error
    yields ``[]`` (the balance insight degrades to honest-empty, never a
    raise — AC.ANL.SURFACE.3)."""
    from .lens_render import default_tracker_factory

    factory = tracker_factory if tracker_factory is not None else default_tracker_factory
    client = factory()
    if client is None:
        return []
    try:
        store = getattr(client, "store", None)
        if store is None:
            return []
        return list(store.all_events())
    except Exception:  # noqa: BLE001 — fail-soft; no history, honest-empty
        return []
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            try:
                close()
            except Exception:  # noqa: BLE001 — best-effort cleanup
                pass


def render_analytics_block(
    *,
    items: Optional[list] = None,
    events: Optional[list] = None,
    tracker_factory: Optional[Callable[[], Any]] = None,
    now: Optional[datetime] = None,
    window_days: int = _BALANCE_WINDOW_DAYS,
) -> str:
    """Render the CONCISE analytics block (the ON-DEMAND production entry
    point — no pre-arranged state, D-ANL.3).

    Composes the conservative THREE insights — pile-up (AC.ANL.PILEUP),
    chronically-stuck (AC.ANL.STUCK), completion-vs-intake balance
    (AC.ANL.BALANCE) — into ONE capped block via ``finalise_block``, each
    a plain-language transparent sentence with zero internal vocabulary
    (AC.ANL.SURFACE.2), honest-empty per-insight when there is no signal
    (AC.ANL.PILEUP.3 / STUCK.3 / BALANCE.3). The surface carries ONLY these
    three insights — NO throughput number, velocity, cycle-time headline,
    bottleneck-edge count, or chart (AC.ANL.SURFACE.4 / D-ANL.2).

    Reads the projection + the event log READ-ONLY through the shared
    helpers. Fail-soft throughout: any boundary error or a fully-empty
    render returns ``""`` (no block, the caller proceeds — AC.ANL.SURFACE.3).
    This module registers NO ``TriggerKind.turn`` contributor — analytics
    is on-demand only (AC.ANL.SURFACE.1).

    *items* / *events* override the live reads (tests inject fixtures).
    *tracker_factory* overrides the default read-only tracker resolution.
    *now* overrides the reference clock (the calibration seam). *window_days*
    overrides the completion-vs-intake window (the calibratable balance
    default, D-ANL.6)."""
    try:
        if items is not None:
            work_items = list(items)
        else:
            work_items = load_work_items(tracker_factory)

        if events is not None:
            event_stream = list(events)
        else:
            event_stream = _read_events(tracker_factory)

        lines: list[str] = []

        # Insight 1 — pile-up (honest-empty: a no-signal set adds no line).
        pileup = compute_pileup(work_items, now=now)
        if pileup is not None:
            lines.append(f"  {pileup.sentence()}")

        # Insight 2 — chronically stuck (honest-empty: none -> no line).
        stuck = compute_stuck(work_items, now=now)
        for s in stuck:
            lines.append(f"  {s.phrase()}.")

        # Insight 3 — completion-vs-intake balance. Surfaced only when
        # there was activity in the window (honest-empty otherwise —
        # AC.ANL.BALANCE.3, no misleading zero-ratio line).
        balance = compute_balance(event_stream, now=now, window_days=window_days)
        if balance.has_activity:
            lines.append(f"  {balance.sentence()}")

        header = "[analytics] What you might be losing track of:"
        return finalise_block(header, lines, char_cap=_ANALYTICS_BLOCK_CHAR_CAP)
    except Exception:  # noqa: BLE001 — fail-soft; no block, turn proceeds
        return ""
