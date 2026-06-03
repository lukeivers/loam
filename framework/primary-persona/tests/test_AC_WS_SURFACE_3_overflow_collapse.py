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

"""AC.WS.SURFACE.3 — when the rendered block would exceed the cap,
active/deep-dived (ground-truth-bound) streams render in full and
paused/stale (unbound) streams collapse to a count; the cap is NEVER
exceeded (the F2 anti-bloat constraint as an AC)."""

from __future__ import annotations

from loam.primary_persona.keep_pace import work_streams as ws
from loam.primary_persona.keep_pace import work_streams_surface as wss


def _record():
    class _L:
        value = "merged"

    class _C:
        name = "core"
        liveness = _L()

    class _R:
        components = [_C()]
        head_sha = "abc"

    return _R()


def _many_streams():
    # Two bound (ground-truth) streams + several unbound stale streams with
    # long objectives that would overflow the cap if all rendered in full.
    bound = [
        ws.WorkStream(slug="loam", attention="active", objective="o",
                      detail_path="d", projects=["loam"]),
        ws.WorkStream(slug="cairn", attention="active", objective="o",
                      detail_path="d", projects=["cairn"]),
    ]
    stale = [
        ws.WorkStream(slug=f"unbound-{i}", attention="active",
                      objective="x" * 80, detail_path="d", projects=[],
                      cadence="weekly", last_touched="2026-01-01")
        for i in range(8)
    ]
    return bound + stale


def test_AC_WS_SURFACE_3_cap_never_exceeded() -> None:
    block = wss.render_work_streams_block(
        streams=_many_streams(), derive=lambda n: _record(),
        emit_deviation_fn=lambda s, st: None,
    )
    assert len(block) <= wss._STREAM_BLOCK_CHAR_CAP, (
        f"the cap is load-bearing — never exceeded; got {len(block)}"
    )


def test_AC_WS_SURFACE_3_bound_streams_survive_collapse() -> None:
    block = wss.render_work_streams_block(
        streams=_many_streams(), derive=lambda n: _record(),
        emit_deviation_fn=lambda s, st: None,
    )
    # The ground-truth-bound streams (the load-bearing signal) render in full.
    assert "- loam " in block
    assert "- cairn " in block
    # The stale/unbound streams collapse to a count, not spilled.
    assert "collapsed" in block or "paused" in block


def test_AC_WS_SURFACE_3_no_overflow_path_keeps_all_lines() -> None:
    # When the block fits, NO collapse happens — all non-paused lines show.
    small = [
        ws.WorkStream(slug="loam", attention="active", objective="o",
                      detail_path="d", projects=["loam"]),
        ws.WorkStream(slug="money", attention="active", objective="o",
                      detail_path="d", projects=[], cadence="weekly",
                      last_touched="2026-05-28"),
    ]
    block = wss.render_work_streams_block(
        streams=small, derive=lambda n: _record(),
        emit_deviation_fn=lambda s, st: None,
    )
    assert len(block) <= wss._STREAM_BLOCK_CHAR_CAP
    assert "- loam " in block
    assert "- money " in block  # unbound but fits => rendered, not collapsed
