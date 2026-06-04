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

"""The SHARED lens render / factory helper (WMS increment 5).

The five keep-pace lenses (streams / projects / relational / goals /
plate / waiting-on) each share the Slice-D render discipline + the
read-only tracker factory: resolve the live tracker READ-ONLY, read the
work-item projections, and finalise ONE block under a hard char-cap. This
module factors THAT shared ~30-line boilerplate into one place so a new
lens does not copy-paste it (D-WMS5.5 — the owner's middle option: the
shared render/factory helper WITHOUT forcing a full lens-protocol onto
the five genuinely-different derive bodies).

It is NOT a lens protocol: each lens keeps its own derive body (projects
derive FBM STATE, goals derive an OBJECTIVES ladder, plate is a pure
prioritize-reuse, waiting-on is a state-split). This helper owns only the
parts that are byte-identical across them — the factory, the read, and
the cap-and-finalise — the Lens-1 "compose, don't duplicate" call.

Lens-1: the tracker factory mirrors the inc-2 ``tracker_context`` default
resolution exactly; the cap mirrors Slice-D. Everything is READ-ONLY —
the helper NEVER widens the narrow read-only ``TrackerClient`` surface
into a write path.
"""

from __future__ import annotations

from typing import Any, Callable, Optional


def default_tracker_factory() -> Any:
    """Resolve the live tracker for the active workspace (READ-ONLY).

    The single shared factory the lenses use (previously copy-pasted into
    each lens module): a lazy ``objective_tracker`` import inside the try
    so an absent component degrades to ``None`` (no block), never an
    import-time crash. The DB path is resolved from the workspace
    identity the same way the inc-2 ``tracker_context`` contributor
    resolves it. Returns the ``ObjectiveTracker`` runtime (carrying the
    EXISTING read queries) or ``None`` — the caller reads it READ-ONLY and
    NEVER calls a write / scope-binding method."""
    try:
        from pathlib import Path

        from ..tracker_context import tracker_db_path_for  # noqa: WPS433
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


def load_work_items(
    tracker_factory: Optional[Callable[[], Any]] = None,
) -> list[Any]:
    """Load the work-item projections from the tracker (READ-ONLY).

    The single shared read both the projects lens and the new lenses use:
    resolve the tracker through ``tracker_factory`` (or the shared default
    factory), read ``query_projection_view`` — the narrow read-only
    surface (no write / scope-binding method is touched) — and close what
    it opened. A ``None`` factory + an unresolvable tracker degrades to an
    empty list (no block), never an import-time crash."""
    factory = (
        tracker_factory if tracker_factory is not None
        else default_tracker_factory
    )
    client = factory()
    if client is None:
        return []
    try:
        return list(client.query_projection_view())
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            try:
                close()
            except Exception:  # noqa: BLE001 — best-effort cleanup
                pass


def finalise_block(header: str, lines: list[str], *, char_cap: int) -> str:
    """Assemble ONE concise block from a header + rows, capped (Slice-D).

    The single shared cap-and-finalise both new lenses use: returns ``""``
    when there are no rows (no block — the graceful-empty contract), else
    ``"<header>\\n<row>\\n<row>..."`` truncated to ``char_cap`` on the
    rstripped boundary (the Slice-D hard cap so a lens is ONE concise
    block, never a wall of text)."""
    if not lines:
        return ""
    block = header + "\n" + "\n".join(lines)
    if len(block) > char_cap:
        block = block[:char_cap].rstrip()
    return block
