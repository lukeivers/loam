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

"""The ON-MY-PLATE lens (WMS increment 5).

The "what should I actually be doing now" VIEW: a flat, priority-sorted
filter of what is ACTIVELY on the user. The D-WMS5.6 default filter:

  - INCLUDE items that are ``active`` or ``owner_pending`` (a decision the
    owner owes IS on the plate to action — D-WMS5.6 (1));
  - EXCLUDE ``blocked`` items (they are not actionable now);
  - EXCLUDE items waiting on an EXTERNAL party (their next move is not the
    owner's — the waiting-on lens shows them under a different framing);
  - EXCLUDE explicitly-deferred items (an owner set-aside);
  - EXCLUDE ``proposed`` (un-promoted / intake-pending) items — not yet
    committed work (D-WMS5.6 (2)).

The surviving set is ordered by inc-4's ``prioritize`` REUSED wholesale —
the SAME ranking + the SAME transparent plain-language reason, no second
priority logic (AC.PLATE.2). No numeric score reaches the surface; every
plate item carries a plain-language reason inherited from ``prioritize``
(AC.PLATE.3). Rendered in ONE concise capped fail-soft block (Slice-D).

Lens-1: the ordering + reason are ``prioritize.py``'s; the alignment
vocabulary is ``aligned_terms_from_objectives``'s; the read-only factory +
read + cap are the shared ``lens_render`` helper's; the work-item store is
read READ-ONLY. This module DERIVES + composes; it adds no storage and
modifies no store.

On-demand (D-WMS5.4): ``render_plate_block`` is a production entry point
the persona renders when the plate question is asked. It is NOT registered
as a ``TriggerKind.turn`` contributor (AC.LENS.2 — zero new always-on
per-turn blocks).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Optional

from .lens_render import finalise_block, load_work_items
from .prioritize import aligned_terms_from_objectives, prioritize

_PLATE_BLOCK_CHAR_CAP = 600

# The statuses that belong on the plate (D-WMS5.6): active work + the
# decisions the owner owes. NOT proposed (uncommitted), NOT blocked, NOT
# terminal.
_PLATE_STATUS_VALUES = frozenset({"active", "owner_pending"})

# Open statuses — the set a `waits_on` target must be in to still count as
# an unresolved blocker (mirrors inc-2 unblocked_next's open_states).
_OPEN_STATUS_VALUES = frozenset(
    {"proposed", "active", "blocked", "owner_pending"}
)

# How many plate items the block names (Slice-D conciseness). A method
# default — the priority sort means the most important survive the cap.
_PLATE_ITEM_CAP = 5


def _goal_text(item: Any) -> str:
    return str(getattr(item, "goal", "") or "").strip()


def _status_value(item: Any) -> str:
    return str(
        getattr(getattr(item, "status", None), "value", "")
        or getattr(item, "status", "")
        or ""
    )


def _edge_kind(e: Any) -> str:
    return str(
        getattr(getattr(e, "edge_kind", None), "value", None)
        or getattr(e, "edge_kind", "")
        or ""
    )


def _objective_id(item: Any) -> str:
    return str(getattr(item, "objective_id", "") or "")


def _is_waiting(item: Any, open_ids: frozenset[str]) -> bool:
    """True when the item is NOT actionable now — it waits on something
    unresolved (mirrors the inc-2 ``unblocked_next`` predicate, computed
    over the in-memory set so it holds on both the pure and live paths).

    An item waits when (a) it has a ``waits_on`` edge to an external party
    OR to an unresolved (still-open) internal target, or (b) it is the
    target of a ``blocks`` edge from an open item. Either way its next move
    is not the owner's right now, so it is OFF the plate (D-WMS5.6)."""
    for e in getattr(item, "edges_out", ()) or ():
        if _edge_kind(e) != "waits_on":
            continue
        if getattr(e, "party", None):
            return True  # external-party wait
        to_id = str(getattr(e, "to_id", "") or "")
        if to_id and to_id in open_ids:
            return True  # waits on an unresolved internal item
    for e in getattr(item, "edges_in", ()) or ():
        if _edge_kind(e) != "blocks":
            continue
        from_id = str(getattr(e, "from_id", "") or "")
        if from_id and from_id in open_ids:
            return True  # blocked by an open item (inverse direction)
    return False


def _on_plate(item: Any, open_ids: frozenset[str], deferred: frozenset[str]) -> bool:
    """The D-WMS5.6 plate predicate (AC.PLATE.1).

    active/owner_pending, NOT waiting (on an external party, an unresolved
    internal item, or blocked by an open item), NOT explicitly deferred,
    NOT proposed/terminal."""
    if _status_value(item) not in _PLATE_STATUS_VALUES:
        return False
    if _is_waiting(item, open_ids):
        return False
    if deferred and _is_deferred(item, deferred):
        return False
    return True


def _is_deferred(item: Any, deferred: frozenset[str]) -> bool:
    """True when an explicit owner defer targets this item (by id, project
    binding, or goal-text mention — the same match shape ``prioritize``'s
    defer band uses)."""
    oid = str(getattr(item, "objective_id", "") or "").lower()
    proj = str(getattr(item, "belongs_to_project", "") or "").lower()
    goal = _goal_text(item).lower()
    for t in deferred:
        t = t.strip().lower()
        if not t:
            continue
        if t == oid or t == proj or (t in goal):
            return True
    return False


def render_plate_block(
    *,
    items: Optional[list] = None,
    objectives_text: Optional[str] = None,
    tracker_factory: Optional[Callable[[], Any]] = None,
    pinned: Optional[frozenset[str]] = None,
    deferred: Optional[frozenset[str]] = None,
    now: Optional[datetime] = None,
) -> str:
    """Render the CONCISE on-my-plate block (the on-demand production
    entry point — no pre-arranged state).

    Loads work items READ-ONLY, applies the D-WMS5.6 filter (AC.PLATE.1 —
    active/owner_pending, not blocked, not waiting-on-others, not
    deferred), passes the surviving set straight through ``prioritize``
    (AC.PLATE.2 — the SAME ranking + reason, no second logic), and renders
    the priority-sorted block with the inherited plain-language reasons
    (AC.PLATE.3 — no surfaced score). Fail-soft: any boundary error or a
    no-content render returns ``""`` (no block — AC.LENS.1).

    *items* overrides the tracker query. *objectives_text* overrides the
    OBJECTIVES read (the goal-alignment vocabulary ``prioritize`` uses).
    *pinned*/*deferred* are the owner hard-override targets passed through
    to ``prioritize`` (a deferred item is filtered OFF the plate; a pin
    floats its item). *now* pins the staleness clock."""
    try:
        if items is not None:
            work_items = list(items)
        else:
            work_items = load_work_items(tracker_factory)

        defers = deferred if deferred is not None else frozenset()
        # The open-item id set — an item "waits on" another only when that
        # target is still open (mirrors inc-2 unblocked_next: a terminal
        # blocker no longer blocks). Computed over the in-memory set so the
        # predicate holds on both the pure and live paths.
        open_ids = frozenset(
            _objective_id(it)
            for it in work_items
            if _status_value(it) in _OPEN_STATUS_VALUES and _objective_id(it)
        )
        on_plate = [it for it in work_items if _on_plate(it, open_ids, defers)]
        if not on_plate:
            return ""

        if objectives_text is not None:
            aligned = aligned_terms_from_objectives(objectives_text)
        else:
            aligned = _aligned_terms_from_live_objectives()
        clock = now if now is not None else datetime.now(timezone.utc)

        ranked = prioritize(
            on_plate,
            aligned_terms=aligned,
            pinned=pinned if pinned is not None else frozenset(),
            deferred=defers,
            now=clock,
        )

        lines: list[str] = []
        for r in ranked:
            goal = _goal_text(r.item)
            if not goal:
                continue
            lines.append(f"  {goal} — {r.reason}")
            if len(lines) >= _PLATE_ITEM_CAP:
                break

        header = (
            "[on your plate] What's actively on you now, most important "
            "first:"
        )
        return finalise_block(header, lines, char_cap=_PLATE_BLOCK_CHAR_CAP)
    except Exception:  # noqa: BLE001 — fail-soft; no block, turn proceeds
        return ""


def _aligned_terms_from_live_objectives() -> frozenset[str]:
    """Read the live OBJECTIVES.md for the goal-alignment vocabulary.

    Fail-soft: an absent / unreadable register yields an empty vocabulary
    (no alignment signal), never a crash — the four always-available
    priority signals carry the ordering. Mirrors the relational lens's
    live-objectives read."""
    try:
        from pathlib import Path

        from .objectives import user_scope_objectives_path  # noqa: WPS433

        path = user_scope_objectives_path()
        if not Path(path).exists():
            return frozenset()
        text = Path(path).read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001 — fail-soft; no alignment vocabulary
        return frozenset()
    return aligned_terms_from_objectives(text)
