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

"""The RELATIONAL lens (WMS increment 4).

A per-turn VIEW that turns the inc-2 edge graph + its queries into the
answers that make the graph valuable, rendered in ONE concise capped
fail-soft block (the Slice-D renderer discipline). It answers, in plain
language:

  - **What's unblocked and ready to do next** — the PRIORITIZED
    ``unblocked_next`` output: the single top item with its transparent
    reason, plus a SHORT "also ready" tail (D-PRI.3 — single-top-plus-
    short-tail, NOT a flat dump). This is where prioritization
    (``prioritize.py``) and the relational web COMPOSE: "next" means the
    RIGHT next thing, with the *why*.
  - **What's blocked and on what** — a blocked item named with what it
    waits on, off the EXISTING ``waits_on``/``blocks`` edges.
  - **What's waiting on ME vs on OTHERS** — ``owner_pending`` / internal
    waits (mine) vs an external-``party`` ``waits_on`` (``waiting_on_other``).
  - **The decomposition tree** — a child's place under its parent, read
    off the EXISTING ``trace_to_root`` / ``parent_id`` tree.

The honest-graph invariant (AC.REL.4): no relationship is fabricated —
an item with no edges and no parent surfaces no blocked/waiting/
decomposition relationship.

Lens-1: the unblock/wait queries + the ancestry tree are inc-2's
(``unblocked_next`` / ``waiting_on_other`` / ``trace_to_root`` on the
``ObjectiveTracker`` runtime); the priority ordering + reason are
``prioritize.py``'s; the cap/TTL/fail-soft renderer discipline is
Slice-D's. This module COMPOSES them — it re-derives no graph traversal
and adds no storage (D-PRI.1). It reads the runtime queries READ-ONLY;
it NEVER widens the narrow ``TrackerClient`` Protocol into a write
surface.

Computed, not materialized (WMS-D2): a live query + the per-turn Slice-D
TTL cache for the rendered block. No materialized lens-index.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from .prioritize import (
    aligned_terms_from_objectives,
    prioritize,
)

# Slice-D renderer discipline: ONE concise block, hard char-cap + TTL.
_RELATIONAL_BLOCK_CHAR_CAP = 600
_RELATIONAL_TTL_SECONDS = 60.0

# How much the lens volunteers per turn (D-PRI.3 — single-top-plus-short
# -tail, NOT a flat dump). One top "next" + at most this many "also
# ready" items. A method default (the per-turn surface budget).
_ALSO_READY_TAIL = 2
# Caps on the secondary relational rows so the block stays concise.
_BLOCKED_ROW_CAP = 2
_WAITING_ROW_CAP = 2
_DECOMP_ROW_CAP = 1

# In-process TTL cache: a single rendered block (the lens is global, not
# per-item). Mirrors Slice-D; an empty render is NOT cached.
_RELATIONAL_CACHE: dict[str, tuple[float, str]] = {}
_CACHE_KEY = "relational-block"


def reset_cache() -> None:
    """Drop the per-turn TTL cache. Production uses the TTL window; tests
    call this between scenarios so a prior turn's block does not leak
    into the next (the cache is global + keyed on a single block)."""
    _RELATIONAL_CACHE.clear()


# ---------------------------------------------------------------------
# Plain-language helpers (zero internal vocab — AC.REL / AC.SURF).
# ---------------------------------------------------------------------


def _goal(item: Any) -> str:
    return str(getattr(item, "goal", "") or "").strip()


def _edge_kind(e: Any) -> str:
    return str(getattr(getattr(e, "edge_kind", None), "value", None) or
               getattr(e, "edge_kind", "") or "")


def _name_for_id(item_id: str, by_id: dict[str, Any]) -> str:
    """The human goal text for an item id, or a soft fallback that never
    leaks the raw id to the user (zero-internal-vocab — AC.REL/AC.PRI.4)."""
    target = by_id.get(item_id)
    if target is not None:
        g = _goal(target)
        if g:
            return g
    return "another item"


def _blocked_on_phrase(item: Any, by_id: dict[str, Any]) -> Optional[str]:
    """"X — waiting on Y" for an item with an unresolved ``waits_on`` edge
    (AC.REL.1). Returns None when the item waits on nothing (honest-graph
    — AC.REL.4)."""
    goal = _goal(item)
    if not goal:
        return None
    waits: list[str] = []
    for e in getattr(item, "edges_out", ()) or ():
        if _edge_kind(e) == "waits_on":
            party = getattr(e, "party", None)
            to_id = getattr(e, "to_id", None)
            if party:
                waits.append(str(party))
            elif to_id:
                waits.append(_name_for_id(str(to_id), by_id))
    if not waits:
        return None
    return f"{goal} — waiting on {', '.join(waits)}"


# ---------------------------------------------------------------------
# The relational answers (each off the EXISTING queries/edges).
# ---------------------------------------------------------------------


def _unblocked_next_rows(
    tracker: Any,
    *,
    by_id: dict[str, Any],
    aligned_terms,
    now: datetime,
) -> list[str]:
    """The PRIORITIZED unblocked-next rows (AC.REL.1 + D-PRI.3).

    Composes the EXISTING ``unblocked_next`` query (inc-2) with the
    ``prioritize.py`` ordering: the single top item with its transparent
    reason, then a SHORT "also ready" tail (no flat dump). Each row is
    plain language with the *why* — never a score (AC.PRI.4)."""
    try:
        unblocked = list(tracker.unblocked_next())
    except Exception:  # noqa: BLE001 — fail-soft; no unblocked row
        return []
    if not unblocked:
        return []
    ranked = prioritize(unblocked, aligned_terms=aligned_terms, now=now)
    if not ranked:
        return []
    rows: list[str] = []
    top = ranked[0]
    top_goal = _goal(top.item)
    if top_goal:
        rows.append(f"  next: {top_goal} — {top.reason}")
    tail = [r for r in ranked[1:] if _goal(r.item)][:_ALSO_READY_TAIL]
    if tail:
        names = "; ".join(_goal(r.item) for r in tail)
        rows.append(f"  also ready: {names}")
    return rows


def _blocked_rows(open_items: list[Any], by_id: dict[str, Any]) -> list[str]:
    """"blocked: X — waiting on Y" rows (AC.REL.1). Only items that
    actually wait on something appear (honest-graph — AC.REL.4)."""
    out: list[str] = []
    for it in open_items:
        phrase = _blocked_on_phrase(it, by_id)
        if phrase:
            out.append(f"  blocked: {phrase}")
        if len(out) >= _BLOCKED_ROW_CAP:
            break
    return out


def _waiting_rows(tracker: Any, open_items: list[Any]) -> list[str]:
    """The waiting-on-ME-vs-OTHERS split (AC.REL.2).

    "waiting on you" = items in ``owner_pending`` (shipped, the owner's
    call). "waiting on <party>" = an external-party ``waits_on`` (the
    EXISTING ``waiting_on_other`` query). Plain language, no enum."""
    out: list[str] = []
    # Waiting on YOU — owner_pending items (mine to rule on).
    mine = [
        _goal(it)
        for it in open_items
        if str(getattr(getattr(it, "status", None), "value", "")
                or getattr(it, "status", "")) == "owner_pending"
        and _goal(it)
    ]
    if mine:
        out.append(f"  waiting on you: {'; '.join(mine[:_WAITING_ROW_CAP])}")
    # Waiting on OTHERS — external-party waits (the existing query).
    try:
        others = list(tracker.waiting_on_other())
    except Exception:  # noqa: BLE001 — fail-soft; no external-wait row
        others = []
    party_rows: list[str] = []
    for it in others:
        goal = _goal(it)
        parties = [
            str(getattr(e, "party", "") or "")
            for e in getattr(it, "edges_out", ()) or ()
            if _edge_kind(e) == "waits_on" and getattr(e, "party", None)
        ]
        if goal and parties:
            party_rows.append(f"{goal} (on {', '.join(parties)})")
        if len(party_rows) >= _WAITING_ROW_CAP:
            break
    if party_rows:
        out.append(f"  waiting on others: {'; '.join(party_rows)}")
    return out


def _decomposition_rows(tracker: Any, open_items: list[Any]) -> list[str]:
    """The decomposition tree — a child's place under its parent
    (AC.REL.3), off the EXISTING ``trace_to_root`` ancestry. Only items
    that actually have a parent appear (honest-graph — AC.REL.4)."""
    out: list[str] = []
    for it in open_items:
        parent_id = getattr(it, "parent_id", None)
        goal = _goal(it)
        if not parent_id or not goal:
            continue
        try:
            chain = tracker.trace_to_root(getattr(it, "objective_id", ""))
        except Exception:  # noqa: BLE001 — fail-soft; skip this item
            continue
        # chain[0] is the item itself; the terminal root is last.
        root = chain[-1] if chain else None
        root_goal = _goal(root) if root is not None else ""
        if root_goal and root_goal != goal:
            out.append(f"  part of: {goal} → under {root_goal}")
        if len(out) >= _DECOMP_ROW_CAP:
            break
    return out


# ---------------------------------------------------------------------
# The render (ONE capped fail-soft block — AC.SURF.1 / AC.SURF.2).
# ---------------------------------------------------------------------

_OPEN_STATUS_VALUES = frozenset(
    {"proposed", "active", "blocked", "owner_pending"}
)


def _status_value(item: Any) -> str:
    return str(getattr(getattr(item, "status", None), "value", "")
               or getattr(item, "status", "") or "")


def render_relational_block(
    *,
    tracker_factory: Optional[Callable[[], Any]] = None,
    objectives_text: Optional[str] = None,
    now: Optional[float] = None,
    clock: Optional[datetime] = None,
) -> str:
    """Render the CONCISE relational block (the production entry point —
    no pre-arranged state).

    Resolves the live tracker READ-ONLY, composes the prioritized
    unblocked-next + the relational answers (blocked / waiting-on-me-vs-
    others / decomposition) off the EXISTING queries + edges, and renders
    ONE capped block (AC.SURF.1). Fail-soft throughout: any boundary
    error or a no-content render returns ``""`` (no block). TTL-cached so
    a turn within the window is a dict lookup (AC.SURF.2).

    *tracker_factory* overrides the default tracker resolution (tests
    inject a live store). *objectives_text* overrides the OBJECTIVES.md
    read (the goal-alignment vocabulary). *now* pins the cache clock;
    *clock* pins the staleness clock (tests / determinism)."""
    ts = time.monotonic() if now is None else now
    cached = _RELATIONAL_CACHE.get(_CACHE_KEY)
    if cached is not None and (ts - cached[0]) < _RELATIONAL_TTL_SECONDS:
        return cached[1]

    try:
        block = _render_uncached(
            tracker_factory=tracker_factory,
            objectives_text=objectives_text,
            clock=clock,
        )
    except Exception:  # noqa: BLE001 — fail-soft; no block, turn proceeds
        return ""

    if block:
        _RELATIONAL_CACHE[_CACHE_KEY] = (ts, block)
    return block


def _render_uncached(
    *,
    tracker_factory: Optional[Callable[[], Any]],
    objectives_text: Optional[str],
    clock: Optional[datetime],
) -> str:
    factory = (
        tracker_factory if tracker_factory is not None
        else _default_tracker_factory
    )
    tracker = factory()
    if tracker is None:
        return ""
    try:
        clk = clock if clock is not None else datetime.now(timezone.utc)
        aligned_terms = (
            aligned_terms_from_objectives(objectives_text)
            if objectives_text is not None
            else _aligned_terms_from_live_objectives()
        )

        # The open work set (read-only) — the relational answers operate
        # over open items. query_projection_view is the narrow read-only
        # surface; the unblock/wait/ancestry queries are runtime methods.
        try:
            all_items = list(tracker.query_projection_view())
        except Exception:  # noqa: BLE001 — fail-soft; no items, no block
            return ""
        open_items = [it for it in all_items if _status_value(it) in _OPEN_STATUS_VALUES]
        by_id = {
            str(getattr(it, "objective_id", "")): it for it in all_items
        }

        next_rows = _unblocked_next_rows(
            tracker, by_id=by_id, aligned_terms=aligned_terms, now=clk
        )
        blocked_rows = _blocked_rows(open_items, by_id)
        waiting_rows = _waiting_rows(tracker, open_items)
        decomp_rows = _decomposition_rows(tracker, open_items)

        rows = next_rows + blocked_rows + waiting_rows + decomp_rows
        if not rows:
            return ""

        block = (
            "[relational] What's next + what's blocking what "
            "(from the work graph):\n" + "\n".join(rows)
        )
        if len(block) > _RELATIONAL_BLOCK_CHAR_CAP:
            block = block[:_RELATIONAL_BLOCK_CHAR_CAP].rstrip()
        return block
    finally:
        close = getattr(tracker, "close", None)
        if callable(close):
            try:
                close()
            except Exception:  # noqa: BLE001 — best-effort cleanup
                pass


def _aligned_terms_from_live_objectives():
    """Read the live OBJECTIVES.md for the goal-alignment vocabulary.

    Fail-soft: an absent / unreadable register yields an empty vocabulary
    (no alignment signal), never a crash — the four always-available
    priority signals carry the ordering (RF #3)."""
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


def _default_tracker_factory() -> Any:
    """Resolve the live tracker for the active workspace (read-only).

    Mirrors the projects-lens factory: a lazy ``objective_tracker``
    import inside the try so an absent component degrades to ``None`` (no
    block), never an import-time crash. Returns the ``ObjectiveTracker``
    runtime (which carries the EXISTING unblocked_next / waiting_on_other
    / trace_to_root queries) — the lens reads them READ-ONLY and NEVER
    calls a write/scope-binding method."""
    try:
        from pathlib import Path

        from ..tracker_context import tracker_db_path_for  # noqa: WPS433
        from loam.objective_tracker.runtime import ObjectiveTracker  # noqa: WPS433
    except Exception:  # noqa: BLE001 — component absent; no block
        return None
    try:
        db_path = tracker_db_path_for(Path.cwd())
        if not Path(db_path).exists():
            return None
        return ObjectiveTracker(db_path=db_path)
    except Exception:  # noqa: BLE001 — unresolvable; no block
        return None


def build_relational_contributor(
    *,
    tracker_factory: Optional[Callable[[], Any]] = None,
) -> Callable[[dict], str]:
    """Return the keep-pace turn contributor (``fn(context: dict) -> str``).

    Surfaces the concise relational block on every turn. Fail-soft: any
    boundary error yields ``""`` (no block) so the composer's turn
    proceeds (the graceful-empty contract the sibling contributors
    honour)."""

    def contributor(context: dict) -> str:  # noqa: ARG001 — context unused (relational is global)
        try:
            return render_relational_block(tracker_factory=tracker_factory)
        except Exception:  # noqa: BLE001 — fail-soft; turn proceeds
            return ""

    return contributor


def register_relational_contributor(
    composer: object,
    *,
    name: str = "relational",
    tracker_factory: Optional[Callable[[], Any]] = None,
) -> Callable[[dict], str]:
    """Register the relational turn-contributor at ``TriggerKind.turn``.

    A SEPARATE named block from the projects / streams / intake lenses
    (distinct VIEWS over the ONE work-item store). Returns a ``str``
    always (``""`` on no content) so the composer's ``text.strip()`` is
    safe (the same seat the projects/intake contributors use —
    AC.SURF.1)."""
    from ..context_composer import TriggerKind  # noqa: WPS433

    fn = build_relational_contributor(tracker_factory=tracker_factory)
    composer.register(name=name, trigger_kind=TriggerKind.turn, fn=fn)
    return fn
