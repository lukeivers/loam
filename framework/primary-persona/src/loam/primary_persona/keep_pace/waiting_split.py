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

"""The SHARED waiting-on-ME-vs-OTHERS split (WMS increment 5).

The single source of truth for "what's waiting on you vs on others",
EXTRACTED from increment-4's ``relational._waiting_rows`` so that BOTH
the relational lens and the standalone waiting-on lens (``waiting_on.py``)
read the SAME split — there is exactly ONE implementation of the split,
consumed at two call sites (the WMS reconciliation; D-WMS5.3 / AC.WAIT.2).

The split is computed off the EXISTING store surface, READ-ONLY:

  - **waiting on ME** = open items in ``owner_pending`` (shipped, the
    owner's call to rule on) — read off the projection ``status`` field.
  - **waiting on OTHERS** = open items carrying an external-party
    ``waits_on`` edge — read off the EXISTING ``waiting_on_other`` query.

The helper returns plain-language goal text + named parties, carrying NO
internal identifier, lifecycle enum, slug, path, or score (the
zero-internal-vocab invariant the relational/waiting-on renders inherit).
This module DERIVES + composes; it adds no storage and modifies no store.

Lens-1: the ``owner_pending`` status + the external-party ``waits_on``
edge + the ``waiting_on_other`` query all ALREADY exist (inc-2/inc-4) and
are read READ-ONLY here. The behaviour is byte-for-byte what
``relational._waiting_rows`` produced before the extraction (the
extraction is behaviour-preserving — AC.WAIT.3).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class WaitingSplit:
    """The on-ME / on-OTHERS waiting split (AC.WAIT.2).

    ``mine`` is the plain-language goal text of every ``owner_pending``
    open item (waiting on the owner to rule). ``others`` is one
    ``"<goal> (on <parties>)"`` string per external-party wait (waiting
    on someone else). Both are plain language — no enum, id, slug, or
    score. The lists are the SINGLE source both the relational lens and
    the standalone waiting-on lens render from."""

    mine: list[str] = field(default_factory=list)
    others: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.mine and not self.others


def _goal(item: Any) -> str:
    return str(getattr(item, "goal", "") or "").strip()


def _edge_kind(e: Any) -> str:
    return str(
        getattr(getattr(e, "edge_kind", None), "value", None)
        or getattr(e, "edge_kind", "")
        or ""
    )


def _status_value(item: Any) -> str:
    return str(
        getattr(getattr(item, "status", None), "value", "")
        or getattr(item, "status", "")
        or ""
    )


def _owner_pending_goals(open_items: list[Any]) -> list[str]:
    """The plain-language goals of the ``owner_pending`` items (waiting on
    ME). Read off the projection ``status`` field; goals only, no enum."""
    return [
        _goal(it)
        for it in open_items
        if _status_value(it) == "owner_pending" and _goal(it)
    ]


def _external_party_rows(tracker: Any) -> list[str]:
    """The ``"<goal> (on <parties>)"`` rows for external-party waits
    (waiting on OTHERS), off the EXISTING ``waiting_on_other`` query.

    Fail-soft: an unavailable query yields no rows (never a crash); a row
    with no goal or no named party is skipped (honest-graph — only a real
    external-party wait surfaces)."""
    try:
        others = list(tracker.waiting_on_other())
    except Exception:  # noqa: BLE001 — fail-soft; no external-wait row
        return []
    rows: list[str] = []
    for it in others:
        goal = _goal(it)
        parties = [
            str(getattr(e, "party", "") or "")
            for e in getattr(it, "edges_out", ()) or ()
            if _edge_kind(e) == "waits_on" and getattr(e, "party", None)
        ]
        if goal and parties:
            rows.append(f"{goal} (on {', '.join(parties)})")
    return rows


def compute_waiting_split(
    tracker: Any,
    open_items: list[Any],
    *,
    mine_cap: Optional[int] = None,
    others_cap: Optional[int] = None,
) -> WaitingSplit:
    """Compute the on-ME / on-OTHERS waiting split (AC.WAIT.2).

    The ONE shared computation both the relational lens and the
    standalone waiting-on lens call. ``open_items`` is the open work set
    (the ``owner_pending`` items are read from it); ``tracker`` supplies
    the EXISTING ``waiting_on_other`` query for the external-party rows.

    ``mine_cap``/``others_cap`` optionally bound how many of each surface
    (the relational lens caps both to keep its combined block concise; a
    dedicated waiting-on lens may pass a larger / no cap). A ``None`` cap
    returns the full set. Behaviour-preserving for the relational caller:
    with the inc-4 caps it returns exactly what ``_waiting_rows`` built."""
    mine = _owner_pending_goals(open_items)
    others = _external_party_rows(tracker)
    if mine_cap is not None:
        mine = mine[:mine_cap]
    if others_cap is not None:
        others = others[:others_cap]
    return WaitingSplit(mine=mine, others=others)


def waiting_rows_from_split(split: WaitingSplit) -> list[str]:
    """Render the split into the relational lens's EXACT row shape
    (AC.WAIT.3 — behaviour-preserving).

    Produces ``"  waiting on you: ..."`` / ``"  waiting on others: ..."``
    — byte-for-byte what ``relational._waiting_rows`` returned before the
    extraction, so the relational block is unchanged."""
    out: list[str] = []
    if split.mine:
        out.append(f"  waiting on you: {'; '.join(split.mine)}")
    if split.others:
        out.append(f"  waiting on others: {'; '.join(split.others)}")
    return out
