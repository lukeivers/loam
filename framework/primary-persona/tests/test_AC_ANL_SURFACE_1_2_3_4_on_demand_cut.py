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

"""AC.ANL.SURFACE.1/.2/.3/.4 — the on-demand surface + the vanity cut.

Plan §6 AC.ANL.SURFACE.*:
  - .1 ON-DEMAND: a render_analytics_block entry point exists; analytics
    registers NO TriggerKind.turn contributor (no new always-on block — the
    per-turn surface is unchanged from inc-6);
  - .2 zero internal vocabulary on every surfaced insight (no IDs / slugs /
    paths / enums / event kinds / numeric scores);
  - .3 char-capped via the shared finalise_block; fail-soft — a read error
    yields an empty result, never raises;
  - .4 the surface carries ONLY the conservative three insights — NO
    throughput number, velocity/burndown, cycle-time headline, bottleneck-
    edge count, or chart/time-series (the vanity cut, D-ANL.2).

The no-turn-registration check mirrors AC.LENS.2's precedent.
"""

from __future__ import annotations

import inspect
import re
from datetime import datetime, timedelta, timezone

from loam.primary_persona import session_start_emitter
from loam.primary_persona.keep_pace import analytics
from loam.primary_persona.keep_pace.analytics import render_analytics_block

from _wms4_store import make_item

_NOW = datetime(2026, 6, 4, 12, 0, 0, tzinfo=timezone.utc)


def _stale(days: int) -> str:
    return (_NOW - timedelta(days=days)).isoformat()


# ---- AC.ANL.SURFACE.1 — on-demand, no turn contributor ---------------


def test_AC_ANL_SURFACE_1_on_demand_entry_point_exists() -> None:
    assert callable(analytics.render_analytics_block)


def test_AC_ANL_SURFACE_1_module_exposes_no_turn_contributor() -> None:
    names = set(dir(analytics))
    assert not any(
        n.startswith("register_") or n.endswith("_contributor") for n in names
    ), (
        "analytics must NOT expose a turn-contributor surface — on-demand "
        f"only (AC.ANL.SURFACE.1); names={sorted(names)}"
    )


def test_AC_ANL_SURFACE_1_emitter_registers_no_analytics_turn_block() -> None:
    # The session-start emitter is UNCHANGED w.r.t. analytics — it registers
    # no analytics turn contributor (zero new always-on per-turn block).
    src = inspect.getsource(session_start_emitter)
    assert "analytics" not in src.lower(), (
        "the per-turn emitter must register NO analytics block (D-ANL.3 / "
        "AC.ANL.SURFACE.1 — analytics is on-demand)"
    )


# ---- AC.ANL.SURFACE.2 — zero internal vocabulary ---------------------


def test_AC_ANL_SURFACE_2_zero_internal_vocabulary() -> None:
    # A rich set across all three insights, then assert the rendered block
    # leaks no IDs / slugs / enums / paths / scores.
    items = [
        make_item(f"m{i}", goal=f"money task {i}", belongs_to_project="money-independence",
                  status="active", last_transition_at=_stale(20))
        for i in range(4)
    ] + [
        make_item("launch", goal="the launch", status="active",
                  last_transition_at=_stale(10),
                  edges_out=[("waits_on", None, "Eric")]),
    ]

    class _Ev:
        def __init__(self, kind, created_at, to_status=None):
            self.kind = kind
            self.created_at = created_at
            self.to_status = to_status

    class _S:
        def __init__(self, v):
            self.value = v

    events = [
        _Ev("objective_created", (_NOW - timedelta(days=1)).isoformat()),
        _Ev("objective_created", (_NOW - timedelta(days=2)).isoformat()),
        _Ev("status_transitioned", (_NOW - timedelta(days=1)).isoformat(), _S("achieved")),
    ]

    block = render_analytics_block(items=items, events=events, now=_NOW)
    assert block, "the block must render with this rich set"

    # No raw objective IDs (obj-… or the fixture m0/launch ids).
    assert "obj-" not in block
    assert not re.search(r"\bm\d\b", block), f"raw id leaked: {block!r}"
    # No raw slug (the hyphenated project key) — de-slugged to plain words.
    assert "money-independence" not in block
    assert "money independence" in block
    # No enum / event-kind tokens.
    for token in ("objective_created", "status_transitioned", "belongs_to_project",
                  "waits_on", "owner_pending", "last_transition_at"):
        assert token not in block, f"internal token leaked: {token!r}"
    # No filesystem path / numeric score artefact.
    assert ".py" not in block
    assert "score" not in block.lower()


# ---- AC.ANL.SURFACE.3 — capped + fail-soft ---------------------------


def test_AC_ANL_SURFACE_3_capped() -> None:
    # Many groups + many stuck items; the block stays under the cap.
    items = []
    for g in range(8):
        for i in range(4):
            items.append(
                make_item(f"{g}-{i}", goal=f"task {g} {i}",
                          belongs_to_project=f"project-{g}", status="active",
                          last_transition_at=_stale(30))
            )
    block = render_analytics_block(items=items, events=[], now=_NOW)
    assert len(block) <= 700, f"block exceeds the shared cap: len={len(block)}"


def test_AC_ANL_SURFACE_3_fail_soft_on_read_error() -> None:
    # A tracker_factory that raises must NOT propagate — fail-soft to "".
    def _boom():
        raise RuntimeError("store unreachable")

    block = render_analytics_block(tracker_factory=_boom, now=_NOW)
    assert block == "", "a read error must fail-soft to an empty block, never raise"


def test_AC_ANL_SURFACE_3_empty_store_no_block() -> None:
    block = render_analytics_block(items=[], events=[], now=_NOW)
    assert block == "", "no data -> no block (honest-empty)"


# ---- AC.ANL.SURFACE.4 — the vanity cut -------------------------------


def test_AC_ANL_SURFACE_4_no_vanity_metric_in_module_or_surface() -> None:
    # The render surface carries ONLY the three insights — no vanity metric.
    items = [
        make_item(f"m{i}", goal=f"task {i}", belongs_to_project="money",
                  status="active", last_transition_at=_stale(20))
        for i in range(4)
    ]
    block = render_analytics_block(items=items, events=[], now=_NOW)
    lower = block.lower()
    for vanity in ("velocity", "burndown", "burn-down", "throughput",
                   "cycle time", "cycle-time", "histogram", "chart",
                   "trend", "average", "per day", "/day"):
        assert vanity not in lower, (
            f"vanity metric '{vanity}' must not appear on the surface "
            f"(D-ANL.2 / AC.ANL.SURFACE.4); block={block!r}"
        )
    # And the module exposes NO derivation function for a cut vanity metric.
    names = {n.lower() for n in dir(analytics)}
    for banned in ("velocity", "burndown", "throughput", "histogram",
                   "bottleneck"):
        assert not any(banned in n for n in names), (
            f"the module must expose no '{banned}' derivation (the vanity cut)"
        )
