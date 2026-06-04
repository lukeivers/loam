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

"""PRIORITIZATION (WMS increment 4) — a derived, TRANSPARENT,
calibrate-on-use multi-signal ordering over the inc-2 work graph.

A work item's rank is COMPUTED from five signals — never hand-stored
(architecture §4b, WMS-D5):

  1. the existing ``tracker_context`` open-loop priority-key (the
     ``priority`` projection field — D-WMS2.5);
  2. blocking-impact — how much downstream work the item unblocks, read
     off the EXISTING edge graph (``edges_in``/``edges_out`` + the
     ``unblocked_next`` query — inc-2);
  3. goal-alignment — does the item ladder up to a user-objective in
     ``OBJECTIVES.md`` (the KP5 ``Objective.subgoals`` ladder);
  4. recency/staleness — ``now − last_transition_at`` past cadence (the
     EXISTING ``last_transition_at`` projection field);
  5. explicit owner pin/defer — a HARD override ABOVE the blend (a pin
     floats its item first regardless of the computed signals; a defer
     demotes it below — architecture §4b "the user can always
     override").

The blend is TRANSPARENT: every ranked item carries a PLAIN-LANGUAGE
reason naming the dominant contributing signal ("next because the launch
is waiting on it" / "stale and nothing's blocking it"), never a
black-box numeric score (the Lens-2 non-tech trust value — AC.PRI.4).
The score stays internal; the reason carries no internal identifier,
lifecycle enum, slug, path, or number (the zero-internal-vocab
invariant).

The signal WEIGHTING is CALIBRATE-ON-USE: a tunable weight set
(:data:`DEFAULT_SIGNAL_WEIGHTS`), NOT an imported magic constant —
changing the weights changes the resulting order without a code edit
(the same Lens-4 discipline as #34's thresholds — AC.PRI.5). The build
picks a sensible default; the SIGNAL SET is the owner product-shape call
(D-PRI.2), the numeric weights are an autonomous calibratable
method-default.

Lens-1: every primitive this module reads ALREADY EXISTS and is consumed
READ-ONLY — the edge graph + ``unblocked_next``/``waiting_on_other``
(inc-2 runtime), the ``priority`` field + ``last_transition_at`` (inc-2
projection), the ``tracker_context`` open-loop rank, the
``OBJECTIVES.md`` subgoal ladder. This module DERIVES + composes; it adds
no storage and modifies no store (D-PRI.1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Optional

# ---------------------------------------------------------------------
# Calibrate-on-use signal weights (Lens-4 / WMS-D5 — AC.PRI.5).
#
# A TUNABLE set, NOT an imported magic number. Each weight scales one
# signal's contribution to the internal blend. The defaults are a
# sensible starting point the build picks; they calibrate on real use
# (a future per-user dial can read a #34 `work-tracking` cell). The
# OWNER call is the signal SET (D-PRI.2), not these numbers.
#
# Changing any weight changes the resulting order WITHOUT a code edit
# (a caller passes an alternate mapping into `prioritize` / the weight
# set is mutated) — that responsiveness is AC.PRI.5.
# ---------------------------------------------------------------------
PRIORITY_KEY_WEIGHT = "priority_key"
BLOCKING_IMPACT_WEIGHT = "blocking_impact"
GOAL_ALIGNMENT_WEIGHT = "goal_alignment"
STALENESS_WEIGHT = "staleness"

DEFAULT_SIGNAL_WEIGHTS: dict[str, float] = {
    # The existing open-loop priority-key (owner_pending > active >
    # proposed). A modest base — it orders comparable items but the
    # dependency/goal/staleness signals can outweigh it (AC.PRI.1).
    PRIORITY_KEY_WEIGHT: 1.0,
    # Blocking-impact dominates: an item that unblocks downstream work
    # is the highest-leverage "next" thing (the AC.WMS4.LIVE.1 outcome —
    # B, which unblocks C, beats an independent stale A).
    BLOCKING_IMPACT_WEIGHT: 3.0,
    # Goal-alignment: laddering up to a user-objective lifts an item
    # over an orphan of otherwise-equal signals.
    GOAL_ALIGNMENT_WEIGHT: 1.5,
    # Staleness: a stale item with nothing blocking surfaces, but does
    # not outrank an unblock-many item.
    STALENESS_WEIGHT: 1.0,
}

# The open-loop priority-key rank → a normalised [0, 1] signal value.
# Composes the EXISTING tracker_context vocabulary (owner_pending=0=
# highest). Lower rank = higher priority = higher signal value. An
# unknown/None priority contributes nothing.
_PRIORITY_RANK: dict[str, int] = {
    "owner_pending": 0,
    "active": 1,
    "proposed": 2,
}
_PRIORITY_RANK_MAX = max(_PRIORITY_RANK.values()) + 1

# Staleness cadence: an item untouched longer than this (in days) reads
# as fully stale (signal value 1.0); fresher items scale linearly. A
# method default, not an owner constant — it tunes with the weights.
_STALENESS_CADENCE_DAYS = 14.0

# Pin / defer band offsets. Pins float ABOVE every computed item; defers
# sink BELOW. These are bands, not weights — a pin is an owner
# instruction (a hard override), not a weighted hint (architecture §4b /
# AC.PRI.3).
_PIN_BAND = 0
_NORMAL_BAND = 1
_DEFER_BAND = 2


@dataclass(frozen=True)
class RankedItem:
    """One prioritised work item + its TRANSPARENT plain-language reason.

    ``item`` is the source ``ObjectiveProjection`` (or any duck-typed
    work item). ``reason`` is the plain-language *why* the item ranks
    where it does — the dominant contributing signal phrased for a
    non-technical reader, carrying NO internal identifier / enum / slug /
    path / score (AC.PRI.4). ``score`` is the INTERNAL blend value — it
    is NEVER surfaced to the user; it exists only so callers can verify
    the ordering is responsive (AC.PRI.2 / AC.PRI.5)."""

    item: Any
    reason: str
    score: float = field(compare=False, default=0.0)
    band: int = field(compare=False, default=_NORMAL_BAND)


# ---------------------------------------------------------------------
# Signal derivations (each a pure READ over the existing graph/state).
# ---------------------------------------------------------------------


def _goal_text(item: Any) -> str:
    return str(getattr(item, "goal", "") or "").strip()


def _priority_key_signal(item: Any) -> float:
    """Signal 1 — the existing open-loop priority-key, normalised.

    Higher = more important. An item with no/unknown priority
    contributes 0.0 (it neither lifts nor sinks)."""
    pri = str(getattr(item, "priority", "") or "")
    rank = _PRIORITY_RANK.get(pri)
    if rank is None:
        return 0.0
    # Invert: rank 0 (owner_pending) -> 1.0; the lowest rank -> a small
    # positive value (it is still a known priority).
    return (_PRIORITY_RANK_MAX - rank) / _PRIORITY_RANK_MAX


def _blocking_impact_count(item: Any) -> int:
    """How many OTHER items this item unblocks — read off the EXISTING
    edge graph (no traversal re-implementation; AC.REL/AC.PRI Lens-1).

    An item unblocks another when it is the ``from`` of a ``blocks`` edge
    (it blocks the target) OR the ``to`` of a ``waits_on`` edge (another
    item waits on it). Both mean: when THIS item lands, that downstream
    item is freed. Counts distinct downstream targets."""
    downstream: set[str] = set()
    for e in getattr(item, "edges_out", ()) or ():
        kind = getattr(getattr(e, "edge_kind", None), "value", None) or getattr(
            e, "edge_kind", None
        )
        if str(kind) == "blocks" or str(kind) == "WorkEdgeKind.blocks":
            tgt = getattr(e, "to_id", None)
            if tgt:
                downstream.add(str(tgt))
    for e in getattr(item, "edges_in", ()) or ():
        kind = getattr(getattr(e, "edge_kind", None), "value", None) or getattr(
            e, "edge_kind", None
        )
        if str(kind) == "waits_on" or str(kind) == "WorkEdgeKind.waits_on":
            src = getattr(e, "from_id", None)
            if src:
                downstream.add(str(src))
    return len(downstream)


def _blocking_impact_signal(item: Any, *, max_impact: int) -> float:
    """Signal 2 — blocking-impact, normalised against the busiest item."""
    if max_impact <= 0:
        return 0.0
    return min(1.0, _blocking_impact_count(item) / max_impact)


def _goal_alignment_signal(item: Any, *, aligned_terms: frozenset[str]) -> float:
    """Signal 3 — does the item ladder up to a user-objective.

    ``aligned_terms`` is the lowercased set of objective slugs + subgoal
    labels read from ``OBJECTIVES.md`` (the KP5 ladder). An item whose
    goal text mentions an active objective/subgoal aligns (1.0); an
    orphan contributes 0.0. Word-level containment keeps it a pure
    lookup, no NLP."""
    if not aligned_terms:
        return 0.0
    goal = _goal_text(item).lower()
    if not goal:
        return 0.0
    for term in aligned_terms:
        if term and term in goal:
            return 1.0
    return 0.0


def _staleness_signal(item: Any, *, now: datetime) -> float:
    """Signal 4 — recency/staleness off the EXISTING ``last_transition_at``.

    ``now − last_transition_at`` scaled by the cadence: an item untouched
    a full cadence reads fully stale (1.0); fresher scales down. A
    malformed/empty timestamp contributes 0.0 (fail-soft, never a
    crash)."""
    raw = str(getattr(item, "last_transition_at", "") or "").strip()
    if not raw:
        return 0.0
    try:
        ts = datetime.fromisoformat(raw)
    except (ValueError, TypeError):
        return 0.0
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    age_days = (now - ts).total_seconds() / 86400.0
    if age_days <= 0:
        return 0.0
    return min(1.0, age_days / _STALENESS_CADENCE_DAYS)


# ---------------------------------------------------------------------
# The reason (TRANSPARENT — AC.PRI.4). Names the dominant signal in
# plain language, no internal vocab.
# ---------------------------------------------------------------------


def _reason_for(
    item: Any,
    *,
    contributions: Mapping[str, float],
    band: int,
) -> str:
    """Plain-language *why* the item ranks where it does (AC.PRI.4).

    Names the dominant CONTRIBUTING signal — true to the real
    computation (RF #4: the reason is honest about WHY the computation
    ranked it, never a post-hoc justification). A pinned item says so; a
    deferred item says so. No score, slug, id, enum, or path leaks."""
    if band == _PIN_BAND:
        return "next because you pinned it"
    if band == _DEFER_BAND:
        return "set aside because you deferred it"

    # The dominant signal among the weighted contributions.
    if not contributions or all(v <= 0.0 for v in contributions.values()):
        return "next thing on the list — nothing else outranks it"
    dominant = max(contributions, key=lambda k: contributions[k])

    if dominant == BLOCKING_IMPACT_WEIGHT:
        n = _blocking_impact_count(item)
        if n == 1:
            return "next because something else is waiting on it"
        return f"next because {n} other things are waiting on it"
    if dominant == GOAL_ALIGNMENT_WEIGHT:
        return "next because it moves a goal you care about forward"
    if dominant == STALENESS_WEIGHT:
        return "next because it's gone stale and nothing's blocking it"
    if dominant == PRIORITY_KEY_WEIGHT:
        return "next because it's the highest-priority open item"
    return "next thing on the list — nothing else outranks it"


# ---------------------------------------------------------------------
# The blend (the ordering — AC.PRI.1 / AC.PRI.2 / AC.PRI.3 / AC.PRI.5).
# ---------------------------------------------------------------------


def _pin_band(item: Any, *, pinned: frozenset[str], deferred: frozenset[str]) -> int:
    """Resolve the hard-override band for an item (AC.PRI.3).

    Pins/defers are matched on the item's id OR its project binding OR a
    goal-text mention — a plain-language pin ("Money is the priority")
    floats every Money item. A pin wins over a defer (an explicit float
    beats an explicit sink if both somehow match)."""
    oid = str(getattr(item, "objective_id", "") or "")
    proj = str(getattr(item, "belongs_to_project", "") or "").lower()
    goal = _goal_text(item).lower()

    def _matches(targets: frozenset[str]) -> bool:
        for t in targets:
            t = t.strip().lower()
            if not t:
                continue
            if t == oid.lower() or t == proj or (t in goal):
                return True
        return False

    if _matches(pinned):
        return _PIN_BAND
    if _matches(deferred):
        return _DEFER_BAND
    return _NORMAL_BAND


def prioritize(
    items: Iterable[Any],
    *,
    weights: Optional[Mapping[str, float]] = None,
    aligned_terms: Optional[frozenset[str]] = None,
    pinned: Optional[frozenset[str]] = None,
    deferred: Optional[frozenset[str]] = None,
    now: Optional[datetime] = None,
) -> list[RankedItem]:
    """Produce the multi-signal ordering + a transparent reason per item.

    The CORE derivation (AC.PRI.1–5). Pure over its inputs — every signal
    is a READ over the projection graph / ``OBJECTIVES.md`` ladder; no
    store is touched.

    *weights* overrides the calibrate-on-use weight set (AC.PRI.5 —
    changing it changes the order without a code edit). *aligned_terms*
    is the lowercased objective/subgoal vocabulary (goal-alignment).
    *pinned*/*deferred* are the owner hard-override targets (AC.PRI.3).
    *now* pins the staleness clock (tests / determinism).

    Returns the items ordered best-first, each wrapped in a
    :class:`RankedItem` carrying the plain-language reason. The internal
    score is on the wrapper for caller verification but is NEVER part of
    the reason text (AC.PRI.4)."""
    w = dict(DEFAULT_SIGNAL_WEIGHTS)
    if weights is not None:
        w.update(weights)
    aligned = aligned_terms if aligned_terms is not None else frozenset()
    pins = pinned if pinned is not None else frozenset()
    defers = deferred if deferred is not None else frozenset()
    clock = now if now is not None else datetime.now(timezone.utc)

    item_list = list(items)
    if not item_list:
        return []

    max_impact = max((_blocking_impact_count(it) for it in item_list), default=0)

    ranked: list[RankedItem] = []
    for it in item_list:
        contributions = {
            PRIORITY_KEY_WEIGHT: w.get(PRIORITY_KEY_WEIGHT, 0.0)
            * _priority_key_signal(it),
            BLOCKING_IMPACT_WEIGHT: w.get(BLOCKING_IMPACT_WEIGHT, 0.0)
            * _blocking_impact_signal(it, max_impact=max_impact),
            GOAL_ALIGNMENT_WEIGHT: w.get(GOAL_ALIGNMENT_WEIGHT, 0.0)
            * _goal_alignment_signal(it, aligned_terms=aligned),
            STALENESS_WEIGHT: w.get(STALENESS_WEIGHT, 0.0)
            * _staleness_signal(it, now=clock),
        }
        score = sum(contributions.values())
        band = _pin_band(it, pinned=pins, deferred=defers)
        reason = _reason_for(it, contributions=contributions, band=band)
        ranked.append(
            RankedItem(item=it, reason=reason, score=score, band=band)
        )

    # Order: band first (pins float, defers sink — the HARD override),
    # then internal score descending, then goal text for a stable tie
    # break. The score never surfaces; only this ORDER + the reason do.
    ranked.sort(
        key=lambda r: (r.band, -r.score, _goal_text(r.item)),
    )
    return ranked


# ---------------------------------------------------------------------
# Goal-alignment vocabulary (the OBJECTIVES.md ladder — read-only).
# ---------------------------------------------------------------------


def aligned_terms_from_objectives(text: str) -> frozenset[str]:
    """Build the goal-alignment vocabulary from ``OBJECTIVES.md`` content.

    Reads the KP5 register (the EXISTING ``load_objectives`` loader) and
    returns the lowercased set of ACTIVE objective slugs + their subgoal
    labels. An item whose goal text mentions one of these ladders up
    (signal 3). Fail-soft: a malformed register yields an empty set (no
    alignment signal), never a crash."""
    try:
        from .objectives import load_objectives  # noqa: WPS433

        objectives = load_objectives(text)
    except Exception:  # noqa: BLE001 — fail-soft; no alignment vocabulary
        return frozenset()
    terms: set[str] = set()
    for obj in objectives:
        try:
            if not obj.is_active():
                continue
            slug = str(getattr(obj, "slug", "") or "").strip().lower()
            if slug:
                # The slug as a phrase (hyphens -> spaces) so a goal that
                # mentions "revenue independence" aligns to the
                # "revenue-independence" objective.
                terms.add(slug)
                terms.add(slug.replace("-", " "))
            for sg in getattr(obj, "subgoals", ()) or ():
                label = str(sg or "").strip().lower()
                if label:
                    terms.add(label)
        except Exception:  # noqa: BLE001 — fail-soft; skip malformed entry
            continue
    return frozenset(t for t in terms if t)
