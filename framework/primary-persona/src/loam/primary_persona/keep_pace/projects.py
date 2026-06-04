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

"""The PROJECTS lens (WMS increment 2).

A VIEW over the unified L1 work-item graph: bounded efforts. The lens
loads work items that carry a ``belongs_to_project`` binding, groups
them by project, sorts within a project by ``priority``, and renders ONE
concise block within a hard character cap — composing the Slice-D
renderer discipline (the same cap + TTL + fail-soft the project-state
and streams lenses use), NOT a second wall of text (AC.PROJ.1).

For a project bound to a registered FBM project (loam / cairn / litrpg
today) the lens's surfaced STATE is composed from a FRESH
``derive_project_state`` call — the Slice-C production entry point —
never a stored/stale status string (AC.PROJ.2, mirrors the streams
lens's AC.WS.DERIVE.1). For a project bound to NO registered FBM project
(a Money / LitRPG-personal / Personal-Home effort with no repo) the lens
surfaces a staleness/cadence next-action AND is explicitly marked "no
ground-truth project bound" — it never fabricates a derived build-STATE
(AC.PROJ.3, the architecture §5 honest gap).

Lens-1: the STATE derivation is Slice C's, the renderer discipline is
Slice D's, the work-item store is the objective tracker (read through the
narrow read-only :class:`TrackerClient` Protocol — the lens NEVER widens
the protocol into a write surface). This module COMPOSES them; it
re-implements nothing.

Computed, not materialized (WMS-D2 / D-WMS2.3): a live query + the
per-turn Slice-D TTL cache for the derived STATE. No materialized
lens-index this cycle.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Optional

from .project_state import _LIVENESS_ORDER, _LIVENESS_PHRASE

# Reuse Slice D's cap + TTL exactly (the projects block is ONE concise
# block, not a second wall — AC.PROJ.1).
_PROJECTS_BLOCK_CHAR_CAP = 600
_PROJECTS_STATE_TTL_SECONDS = 60.0

# In-process TTL cache: project name -> (monotonic ts, derived record).
# Mirrors Slice D; a None record is NOT cached (a probe failure retries).
_PROJECTS_STATE_CACHE: dict[str, tuple[float, Any]] = {}

# The priority sort rank. Composes ON the existing tracker_context
# open-loop priority vocabulary (D-WMS2.5): lower rank = higher priority =
# sorted first. An item with no priority (or an unknown one) sorts last.
# The multi-signal WMS-D5 weighting is increment 4, not here.
_PRIORITY_RANK: dict[str, int] = {
    "owner_pending": 0,
    "active": 1,
    "proposed": 2,
}


def _derive_cached(name: str, *, now: Optional[float] = None) -> Any:
    """Derive a registered project's STATE record, TTL-cached, fail-soft.

    Returns the freshly-derived (or cached-within-TTL) record, or
    ``None`` when the name is unregistered OR any derivation error occurs
    (a missing ``loam_cli``, a git probe failure). A ``None`` is never
    cached. The ``loam_cli`` import is lazy + inside the try so an absent
    ``loam_cli`` degrades to ``None`` (no STATE), never an import-time
    crash (mirrors Slice D + the streams surfacer)."""
    ts = time.monotonic() if now is None else now
    cached = _PROJECTS_STATE_CACHE.get(name)
    if cached is not None and (ts - cached[0]) < _PROJECTS_STATE_TTL_SECONDS:
        return cached[1]
    try:
        from loam_cli.audit.registry import derive_project_state  # noqa: WPS433

        record = derive_project_state(name)
    except Exception:  # noqa: BLE001 — fail-soft; project omitted
        return None
    if record is None:
        return None
    _PROJECTS_STATE_CACHE[name] = (ts, record)
    return record


def _project_state_phrase(record: Any) -> str:
    """The concise STATE phrase for a derived record (Slice D grouping).

    Modules grouped by liveness class, BUILT classes leading. Returns
    ``""`` on a record with no rows. Fail-soft on a malformed row
    (mirrors the streams surfacer's ``_project_state_phrase``)."""
    groups: dict[str, list[str]] = {}
    try:
        rows = list(getattr(record, "components", ()) or ())
    except Exception:  # noqa: BLE001 — fail-soft; treat as no rows
        rows = []
    for row in rows:
        try:
            cls = str(getattr(getattr(row, "liveness", None), "value", "") or "")
            comp = str(getattr(row, "name", "") or "")
        except Exception:  # noqa: BLE001 — fail-soft; skip malformed row
            continue
        if not cls or not comp:
            continue
        groups.setdefault(cls, []).append(comp)
    if not groups:
        return ""

    def _order(cls: str) -> int:
        return (
            _LIVENESS_ORDER.index(cls)
            if cls in _LIVENESS_ORDER
            else len(_LIVENESS_ORDER)
        )

    parts: list[str] = []
    for cls in sorted(groups, key=_order):
        phrase = _LIVENESS_PHRASE.get(cls, cls)
        mods = ", ".join(groups[cls])
        parts.append(f"{mods} = {phrase}")
    return "; ".join(parts)


def _priority_key(item: Any) -> tuple[int, str]:
    """Sort key for a work item within a project (AC.PROJ.1).

    Lower priority-rank first; ties broken by goal text for a stable
    order. An item with no/unknown priority sorts after prioritised
    items."""
    pri = str(getattr(item, "priority", "") or "")
    rank = _PRIORITY_RANK.get(pri, len(_PRIORITY_RANK))
    goal = str(getattr(item, "goal", "") or "")
    return (rank, goal)


def _items_by_project(items: Any) -> dict[str, list[Any]]:
    """Group work items by their ``belongs_to_project`` binding, dropping
    items with no binding (the projects lens is bounded-effort only —
    AC.PROJ.1). Each project's items are sorted by priority."""
    groups: dict[str, list[Any]] = {}
    for it in items:
        proj = getattr(it, "belongs_to_project", None)
        if not proj:
            continue
        groups.setdefault(str(proj), []).append(it)
    for proj in groups:
        groups[proj].sort(key=_priority_key)
    return groups


def _staleness_next_action(items: list[Any]) -> str:
    """Next-action for an UNBOUND project (AC.PROJ.3) — never fabricates a
    derived build-STATE. Surfaces the count of open items + the honest
    "no ground-truth project bound" mark so the persona cannot mistake an
    unbound project for one with a derived STATE."""
    n = len(items)
    lead = ""
    for it in sorted(items, key=_priority_key):
        goal = str(getattr(it, "goal", "") or "").strip()
        if goal:
            lead = goal
            break
    lead_tail = f" — lead: {lead}" if lead else ""
    return (
        f"no ground-truth project bound — {n} open item(s), "
        f"track via work items{lead_tail}"
    )


def _project_line(
    project_name: str,
    items: list[Any],
    *,
    derive: Callable[[str], Any],
) -> str:
    """One concise line for a project (AC.PROJ.1 shape).

    For a project resolving to a registered FBM project, the STATE is
    composed from a FRESH ``derive`` call (AC.PROJ.2) — never a stored
    string. For a project with no registered FBM spec, the line carries a
    staleness/cadence next-action + the "no ground-truth project bound"
    mark (AC.PROJ.3)."""
    count = len(items)
    try:
        record = derive(project_name)
    except Exception:  # noqa: BLE001 — fail-soft; treat as unbound
        record = None
    if record is None:
        # AC.PROJ.3 — unbound: honest staleness mark, no faked STATE.
        return (
            f"  - {project_name} ({count} item(s)): "
            f"{_staleness_next_action(items)}"
        )
    phrase = _project_state_phrase(record)
    if not phrase:
        return (
            f"  - {project_name} ({count} item(s)): status unavailable "
            f"(bound project state could not be derived this turn)"
        )
    return f"  - {project_name} ({count} item(s)): {phrase}"


def render_projects_block(
    *,
    items: Optional[list] = None,
    now: Optional[float] = None,
    derive: Optional[Callable[[str], Any]] = None,
    tracker_factory: Optional[Callable[[], Any]] = None,
) -> str:
    """Render the CONCISE projects block (the production entry point — no
    pre-arranged state).

    Loads work items from the tracker (read-only ``query_projection_view``
    via the narrow protocol), groups them by ``belongs_to_project``, sorts
    within a project by priority, derives live STATE per FBM-bound project
    (AC.PROJ.2) or marks the unbound ones honestly (AC.PROJ.3), and
    renders one capped block (AC.PROJ.1). Fail-soft throughout: any
    boundary error or a no-content render returns ``""`` (no block).

    *items* overrides the tracker query (tests inject a work-item set).
    *derive* overrides the per-project derivation (tests inject a raising
    / fixture derivation); production uses the Slice-C TTL-cached
    derivation. *tracker_factory* overrides the default tracker resolution
    (tests / production-wiring). *now* pins the cache clock (tests)."""
    derive_fn = derive if derive is not None else (
        lambda n: _derive_cached(n, now=now)
    )
    try:
        if items is not None:
            work_items = list(items)
        else:
            work_items = _load_work_items(tracker_factory)
    except Exception:  # noqa: BLE001 — fail-soft; no items => no block
        return ""

    groups = _items_by_project(work_items)
    if not groups:
        return ""

    lines: list[str] = []
    for project_name in sorted(groups):
        try:
            line = _project_line(project_name, groups[project_name], derive=derive_fn)
        except Exception:  # noqa: BLE001 — fail-soft; omit this project
            continue
        if line:
            lines.append(line)

    if not lines:
        return ""

    block = (
        "[projects] Bounded efforts — STATE derived live (ground-truth, "
        "not prose):\n" + "\n".join(lines)
    )
    if len(block) > _PROJECTS_BLOCK_CHAR_CAP:
        block = block[:_PROJECTS_BLOCK_CHAR_CAP].rstrip()
    return block


def _load_work_items(tracker_factory: Optional[Callable[[], Any]]) -> list[Any]:
    """Load the work-item projections from the tracker (read-only).

    Lazily resolves the tracker through ``tracker_factory`` (or the
    default factory) and reads ``query_projection_view`` — the narrow
    read-only surface (no write/scope-binding method is touched). A None
    factory + an unresolvable tracker degrades to an empty list (no block),
    never an import-time crash (mirrors the sibling contributors)."""
    factory = tracker_factory if tracker_factory is not None else _default_tracker_factory
    client = factory()
    if client is None:
        return []
    try:
        projections = client.query_projection_view()
        return list(projections)
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            try:
                close()
            except Exception:  # noqa: BLE001 — best-effort cleanup
                pass


def _default_tracker_factory() -> Any:
    """Resolve the live tracker for the active workspace (read-only).

    Mirrors ``tracker_context``'s default factory: a lazy
    ``objective_tracker`` import inside the try so an absent component
    degrades to ``None`` (no block), never an import-time crash. The DB
    path is resolved from the workspace identity the same way the
    tracker-context contributor resolves it."""
    try:
        from ..tracker_context import (  # noqa: WPS433
            tracker_db_path_for,
        )
        from loam.objective_tracker.runtime import ObjectiveTracker  # noqa: WPS433
    except Exception:  # noqa: BLE001 — component absent; no block
        return None
    try:
        from pathlib import Path

        db_path = tracker_db_path_for(Path.cwd())
        if not Path(db_path).exists():
            return None
        return ObjectiveTracker(db_path=db_path)
    except Exception:  # noqa: BLE001 — unresolvable; no block
        return None


def build_projects_contributor(
    *,
    tracker_factory: Optional[Callable[[], Any]] = None,
) -> Callable[[dict], str]:
    """Return the keep-pace turn contributor (``fn(context: dict) -> str``).

    Surfaces the concise projects block on every turn. Fail-soft: any
    boundary error yields ``""`` (no block) so the composer's turn
    proceeds (the graceful-empty contract the sibling contributors
    honour)."""

    def contributor(context: dict) -> str:  # noqa: ARG001 — context unused (projects are global)
        try:
            return render_projects_block(tracker_factory=tracker_factory)
        except Exception:  # noqa: BLE001 — fail-soft; turn proceeds
            return ""

    return contributor


def register_projects_contributor(
    composer: object,
    *,
    name: str = "projects",
    tracker_factory: Optional[Callable[[], Any]] = None,
) -> Callable[[dict], str]:
    """Register the projects turn-contributor at ``TriggerKind.turn``.

    A SEPARATE named block from the streams lens (the two lenses are
    distinct VIEWS over the ONE work-item store — AC.WMS2.LIVE.1). Returns
    a ``str`` always (``""`` on no content) so ``_serialise_turn``'s
    ``text.strip()`` is safe."""
    from ..context_composer import TriggerKind  # noqa: WPS433

    fn = build_projects_contributor(tracker_factory=tracker_factory)
    composer.register(name=name, trigger_kind=TriggerKind.turn, fn=fn)
    return fn
