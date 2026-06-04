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

"""The GOALS lens (WMS increment 5).

A VIEW over the inc-2 work-item graph laddered against the user's stated
objectives (``OBJECTIVES.md``). Per ACTIVE objective it surfaces the open
work that advances it, NAMES any objective with no advancing work
("nothing is currently moving this goal"), and carries an
unattributed-open-work tail so no open item is silently dropped —
rendered in ONE concise capped fail-soft block (the Slice-D discipline).

The ladder is DERIVED, not stored (D-WMS5.2): the projection carries NO
``objective-slug`` binding (confirmed absent), so the lens computes the
ladder via the SAME alignment mechanism ``prioritize.py`` uses — an
item's goal text mentioning an active objective's slug (or its subgoal
labels) ladders it to that objective. This reuses the inc-4
``aligned_terms_from_objectives`` vocabulary discipline (the per-term
lowercased containment match), per objective. It fabricates NO ladder: an
item appears under an objective ONLY when a real alignment term connects
them (AC.GOAL.4, mirroring the relational honest-graph invariant).

Lens-1: the OBJECTIVES register loader is ``objectives.py``'s; the
alignment-term shape is ``prioritize.py``'s; the read-only factory + read
+ cap are the shared ``lens_render`` helper's; the work-item store is the
objective tracker (read READ-ONLY). This module DERIVES + composes; it
adds no storage and modifies no store.

On-demand (D-WMS5.4): ``render_goals_block`` is a production entry point
the persona renders when the goals question is asked. It is NOT registered
as a ``TriggerKind.turn`` contributor (AC.LENS.2 — zero new always-on
per-turn blocks).
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from .lens_render import finalise_block, load_work_items

_GOALS_BLOCK_CHAR_CAP = 600

# Open statuses the goals lens ladders (the work that can still advance a
# goal). Terminal items are not "moving" a goal.
_OPEN_STATUS_VALUES = frozenset(
    {"proposed", "active", "blocked", "owner_pending"}
)

# Per goal, how many advancing items the block names (Slice-D conciseness
# — the lens is ONE concise block, not a flat dump). A method default.
_PER_GOAL_ITEM_CAP = 3
# How many unattributed open items the honest-coverage tail names.
_UNATTRIBUTED_TAIL_CAP = 3


def _goal_text(item: Any) -> str:
    return str(getattr(item, "goal", "") or "").strip()


def _status_value(item: Any) -> str:
    return str(
        getattr(getattr(item, "status", None), "value", "")
        or getattr(item, "status", "")
        or ""
    )


def _objective_terms(obj: Any) -> frozenset[str]:
    """The lowercased alignment terms for ONE objective — its slug (as a
    slug and as a hyphen->space phrase) + its subgoal labels.

    Mirrors ``aligned_terms_from_objectives`` per objective so a goal that
    mentions the objective or one of its subgoals ladders to it. An empty
    set means no item can ladder to this objective (it surfaces as a
    no-work goal — AC.GOAL.2)."""
    terms: set[str] = set()
    slug = str(getattr(obj, "slug", "") or "").strip().lower()
    if slug:
        terms.add(slug)
        terms.add(slug.replace("-", " "))
    for sg in getattr(obj, "subgoals", ()) or ():
        label = str(sg or "").strip().lower()
        if label:
            terms.add(label)
            terms.add(label.replace("-", " "))
    return frozenset(t for t in terms if t)


def _item_aligns(item_goal_lower: str, terms: frozenset[str]) -> bool:
    """True when the item's goal text mentions one of the objective's
    terms (the real alignment signal — AC.GOAL.4 no-fabrication)."""
    if not item_goal_lower or not terms:
        return False
    for term in terms:
        if term and term in item_goal_lower:
            return True
    return False


def _load_active_objectives(objectives_text: Optional[str]) -> list[Any]:
    """Load the ACTIVE objectives from the OBJECTIVES register (READ-ONLY).

    ``objectives_text`` overrides the live register read (tests inject a
    fixture register). Fail-soft: an absent / unreadable register yields
    no objectives (the lens renders nothing), never a crash."""
    try:
        from .objectives import (  # noqa: WPS433
            load_objectives,
            load_user_scope_register,
        )

        if objectives_text is not None:
            objectives = load_objectives(objectives_text)
        else:
            objectives = load_user_scope_register()
    except Exception:  # noqa: BLE001 — fail-soft; no objectives, no block
        return []
    return [o for o in objectives if getattr(o, "is_active", lambda: False)()]


def render_goals_block(
    *,
    items: Optional[list] = None,
    objectives_text: Optional[str] = None,
    tracker_factory: Optional[Callable[[], Any]] = None,
) -> str:
    """Render the CONCISE goals block (the on-demand production entry
    point — no pre-arranged state).

    Loads work items READ-ONLY + the ACTIVE objectives, ladders each open
    item to the objective(s) its goal text aligns with (AC.GOAL.1),
    NAMES objectives with no advancing work (AC.GOAL.2), and carries an
    unattributed-open-work tail (AC.GOAL.3) so no item vanishes. Fabricates
    no ladder (AC.GOAL.4). Fail-soft throughout: any boundary error or a
    no-content render returns ``""`` (no block — AC.LENS.1).

    *items* overrides the tracker query (tests inject a work-item set).
    *objectives_text* overrides the OBJECTIVES register read.
    *tracker_factory* overrides the default tracker resolution."""
    try:
        objectives = _load_active_objectives(objectives_text)
        if not objectives:
            return ""

        if items is not None:
            work_items = list(items)
        else:
            work_items = load_work_items(tracker_factory)

        open_items = [
            it for it in work_items if _status_value(it) in _OPEN_STATUS_VALUES
        ]

        lines: list[str] = []
        attributed_ids: set[int] = set()
        for obj in objectives:
            terms = _objective_terms(obj)
            slug = str(getattr(obj, "slug", "") or "").strip()
            label = slug.replace("-", " ") if slug else "this goal"
            advancing: list[str] = []
            for it in open_items:
                if _item_aligns(_goal_text(it).lower(), terms):
                    g = _goal_text(it)
                    if g:
                        advancing.append(g)
                        attributed_ids.add(id(it))
            if advancing:
                named = "; ".join(advancing[:_PER_GOAL_ITEM_CAP])
                lines.append(f"  {label}: {named}")
            else:
                # AC.GOAL.2 — a no-work goal is NAMED, never omitted.
                lines.append(
                    f"  {label}: nothing is currently moving this goal"
                )

        # AC.GOAL.3 — open work laddering to NO objective surfaces as an
        # honest unattributed tail (nothing silently dropped).
        unattributed = [
            _goal_text(it)
            for it in open_items
            if id(it) not in attributed_ids and _goal_text(it)
        ]
        if unattributed:
            named = "; ".join(unattributed[:_UNATTRIBUTED_TAIL_CAP])
            lines.append(f"  not tied to a goal yet: {named}")

        header = (
            "[goals] Your goals + the work moving them "
            "(laddered from your objectives):"
        )
        return finalise_block(header, lines, char_cap=_GOALS_BLOCK_CHAR_CAP)
    except Exception:  # noqa: BLE001 — fail-soft; no block, turn proceeds
        return ""
