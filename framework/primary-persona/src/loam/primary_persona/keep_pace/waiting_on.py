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

"""The WAITING-ON lens (WMS increment 5).

A standalone named VIEW of what is waiting on ME (``owner_pending`` /
internal waits) vs on OTHERS (external-party ``waits_on``), rendered in
ONE concise capped fail-soft block (the Slice-D discipline).

The split is NOT re-implemented here. Increment 4's ``relational.py``
already computes the exact on-me / on-others split; increment 5 extracted
that split into the SHARED ``compute_waiting_split`` helper (D-WMS5.3),
and BOTH ``relational.py`` and this lens call it — there is exactly ONE
implementation of the split, consumed at two call sites (AC.WAIT.2 — the
reconciliation; re-implementing it would be the multi-surface drift the
whole WMS exists to prevent). This module is the standalone presentation
of that shared split; increment 6 (per-user lens choice) needs waiting-on
as a NAMED selectable lens, which is why it is formalised here.

Lens-1: the split is the shared helper's; the read-only factory + read
are the shared ``lens_render`` helper's; the cap is Slice-D; the
external-party wait query (``waiting_on_other``) is inc-2's, read
READ-ONLY. This module DERIVES + composes; it adds no storage and modifies
no store.

On-demand (D-WMS5.4): ``render_waiting_on_block`` is a production entry
point the persona renders when the waiting-on question is asked. It is NOT
registered as a ``TriggerKind.turn`` contributor (AC.LENS.2 — zero new
always-on per-turn blocks).
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from .lens_render import default_tracker_factory, finalise_block
from .waiting_split import compute_waiting_split

_WAITING_ON_BLOCK_CHAR_CAP = 600

# Open statuses the waiting-on lens considers (the owner_pending split is
# read from this set; the external-party rows come from the existing
# waiting_on_other query, which applies its own open filter).
_OPEN_STATUS_VALUES = frozenset(
    {"proposed", "active", "blocked", "owner_pending"}
)

# How many of each side the block names (Slice-D conciseness). A method
# default — the standalone lens can surface more than the relational
# block's combined-cap, but stays one concise block.
_WAITING_SIDE_CAP = 4


def _status_value(item: Any) -> str:
    return str(
        getattr(getattr(item, "status", None), "value", "")
        or getattr(item, "status", "")
        or ""
    )


def render_waiting_on_block(
    *,
    items: Optional[list] = None,
    tracker: Optional[Any] = None,
    tracker_factory: Optional[Callable[[], Any]] = None,
) -> str:
    """Render the CONCISE waiting-on block (the on-demand production entry
    point — no pre-arranged state).

    Resolves the live tracker READ-ONLY, reads the open work set, and
    computes the on-me / on-others split via the SHARED
    ``compute_waiting_split`` helper (the SAME one ``relational.py`` calls
    — AC.WAIT.2), rendering it as a standalone named block (AC.WAIT.1).
    Fail-soft: any boundary error or a no-content render returns ``""`` (no
    block — AC.LENS.1).

    *items* overrides the open-item read (tests inject a work-item set).
    *tracker* injects a resolved tracker (tests pass a live store); when
    absent it is resolved from *tracker_factory* or the shared default
    factory. The lens reads the tracker READ-ONLY and closes only a
    tracker it itself opened."""
    opened = False
    try:
        resolved = tracker
        if resolved is None:
            factory = (
                tracker_factory if tracker_factory is not None
                else default_tracker_factory
            )
            resolved = factory()
            opened = resolved is not None
        if resolved is None:
            return ""

        try:
            if items is not None:
                all_items = list(items)
            else:
                all_items = list(resolved.query_projection_view())
        except Exception:  # noqa: BLE001 — fail-soft; no items, no block
            return ""

        open_items = [
            it for it in all_items if _status_value(it) in _OPEN_STATUS_VALUES
        ]

        split = compute_waiting_split(
            resolved,
            open_items,
            mine_cap=_WAITING_SIDE_CAP,
            others_cap=_WAITING_SIDE_CAP,
        )
        if split.is_empty():
            return ""

        lines: list[str] = []
        if split.mine:
            lines.append(f"  on you to decide: {'; '.join(split.mine)}")
        if split.others:
            lines.append(f"  on others: {'; '.join(split.others)}")

        header = "[waiting on] What's waiting on you vs on someone else:"
        return finalise_block(
            header, lines, char_cap=_WAITING_ON_BLOCK_CHAR_CAP
        )
    except Exception:  # noqa: BLE001 — fail-soft; no block, turn proceeds
        return ""
    finally:
        if opened and resolved is not None:
            close = getattr(resolved, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:  # noqa: BLE001 — best-effort cleanup
                    pass
