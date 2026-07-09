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

"""The default (real) source readers for the fleet page (WS-A3).

Each reader wraps ONE upstream component's existing public API — never a
hand-rolled re-query of the underlying store (§5 constraint: "reuse the
existing API, do not query DuckDB by hand").  Imports are LAZY (inside
the functions, D-A3-5) so ``import loam.fleet_page`` succeeds with none
of the three source packages installed, and a genuinely-uninstalled
source degrades to a missing panel (ImportError propagates up to the
generate layer's per-source ``try/except``) rather than breaking module
load.

A reader RAISES on genuine unavailability (package missing, store
absent, read failed); it returns an EMPTY-but-present value (``{"runs":
[]}`` / ``[]``) when the source is present and simply has nothing.  The
generate layer maps a raise → "source unavailable" and an empty →
explicit empty state (AC.PAGE.3; §5 empty-vs-missing).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def read_fleet(roots: list[Path] | Path | str,
               *, stale_after_s: float = 300.0) -> dict:
    """Live + recent runs via WS-A2's ``collect_fleet`` (public API).

    Raises ``ImportError`` if the collector is not installed; any read
    error propagates — the generate layer treats either as an
    unavailable source."""
    from loam.fleet_collector import collect_fleet
    return collect_fleet(roots, stale_after_s=stale_after_s)


def read_cost_rows(*, window_days: int = 7,
                   config: Any | None = None) -> list[dict]:
    """This-window token cost via ``QueryAPI.cost_by_prompt`` (public
    API), returned as plain row dicts the renderer consumes.

    Token counts only — never ``estimated_usd`` (no pricing map is
    passed, so it is ``0.0``; a ``$0`` cost strip would be invented
    data, D-A3-4).  An empty store returns ``[]`` (present-but-empty),
    NOT a raise."""
    from loam.observability_aggregator import QueryAPI, open_store
    from loam.observability_aggregator.api import TimeRange
    store = open_store(config)
    try:
        api = QueryAPI(store)
        end = datetime.now()
        start = end - timedelta(days=window_days)
        costs = api.cost_by_prompt(time_range=TimeRange(start=start, end=end))
    finally:
        close = getattr(store, "close", None)
        if callable(close):
            close()
    rows: list[dict] = []
    for name, pc in costs.items():
        rows.append({
            "prompt_name": name,
            "input_tokens": getattr(pc, "input_tokens", 0),
            "output_tokens": getattr(pc, "output_tokens", 0),
            "call_count": getattr(pc, "call_count", 0),
        })
    return rows


def read_decisions(pm_dirs: list[Path] | Path | str) -> list[dict]:
    """The "needs a human" queue via ``load_decision_queue`` (public
    API), merged across one or more PM state dirs.

    A PM dir with no ``decision-queue.yaml`` contributes ``[]`` (empty is
    normal); a genuinely-missing package or a corrupted queue propagates
    up as an unavailable source."""
    from loam.per_project_pm.loader import load_decision_queue

    if isinstance(pm_dirs, (str, Path)):
        pm_dirs = [Path(pm_dirs)]
    else:
        pm_dirs = [Path(p) for p in pm_dirs]

    merged: list[dict] = []
    for pm_dir in pm_dirs:
        merged.extend(load_decision_queue(pm_dir))
    return merged


def discover_pm_dirs(root: Path | str) -> list[Path]:
    """Every per-project-pm state dir under ``root``.

    A PM dir is ``<workspace>/workspace/.loam/pms/<handle>/`` (carries a
    ``contract.yaml``).  Used by the CLI to feed ``read_decisions``
    without the caller enumerating handles."""
    root = Path(root)
    if not root.exists():
        return []
    seen: list[Path] = []
    for contract in root.rglob("contract.yaml"):
        pm_dir = contract.parent
        if pm_dir.parent.name == "pms" and pm_dir not in seen:
            seen.append(pm_dir)
    return seen
