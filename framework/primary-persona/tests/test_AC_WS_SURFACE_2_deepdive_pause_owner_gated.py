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

"""AC.WS.SURFACE.2 — setting a stream to deep-dive surfaces it in full and
mutes every OTHER stream's staleness nudge; setting a stream to paused
removes its line and nudge; both are owner-gated (no automated path
mutates attention — KP5 discipline)."""

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


def test_AC_WS_SURFACE_2_deep_dive_mutes_other_nudges() -> None:
    streams = [
        ws.WorkStream(slug="loam", attention="deep-dive", objective="o",
                      detail_path="d", projects=["loam"]),
        ws.WorkStream(slug="cairn", attention="active", objective="o",
                      detail_path="d", projects=["cairn"]),
    ]
    block = wss.render_work_streams_block(
        streams=streams, derive=lambda n: _record(),
        emit_deviation_fn=lambda s, st: None,
    )
    # The deep-dived stream keeps its nudge; the OTHER stream's nudge is muted.
    loam_line = [ln for ln in block.splitlines() if "- loam " in ln][0]
    cairn_line = [ln for ln in block.splitlines() if "- cairn " in ln][0]
    assert "[deep-dive]" in loam_line
    assert "next:" in loam_line, "the deep-dived stream surfaces in full"
    assert "next:" not in cairn_line, (
        "every OTHER stream's staleness nudge is muted while one is deep-dived"
    )


def test_AC_WS_SURFACE_2_paused_drops_line() -> None:
    streams = [
        ws.WorkStream(slug="loam", attention="active", objective="o",
                      detail_path="d", projects=["loam"]),
        ws.WorkStream(slug="cairn", attention="paused", objective="o",
                      detail_path="d", projects=["cairn"]),
    ]
    block = wss.render_work_streams_block(
        streams=streams, derive=lambda n: _record(),
        emit_deviation_fn=lambda s, st: None,
    )
    assert "- cairn " not in block, "a paused stream's line is dropped"
    assert "paused" in block, "paused streams collapse to a count"


def test_AC_WS_SURFACE_2_attention_is_owner_gated() -> None:
    # KP5 discipline: attention is the ONLY owner-gated field (no
    # automated path mutates it).
    assert ws.field_class("attention") == "owner-gated"
    assert ws.field_class("last-touched") == "soft-auto"
    assert ws.field_class("objective") == "static"
