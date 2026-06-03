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

"""AC.WS.SURFACE.1 — on a real turn the keep-pace lens surfaces ONE
concise block covering all non-paused streams, one short line per
stream, within a hard char cap; the block SUBSUMES (does not duplicate)
the Slice-D project-state block."""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.context_composer import TriggerKind
from loam.primary_persona.keep_pace import work_streams as ws
from loam.primary_persona.keep_pace import work_streams_surface as wss
from loam.primary_persona.session_start_emitter import build_session_composer


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


def _streams():
    return [
        ws.WorkStream(slug="loam", attention="active", objective="o",
                      detail_path="d", projects=["loam"]),
        ws.WorkStream(slug="cairn", attention="active", objective="o",
                      detail_path="d", projects=["cairn"]),
    ]


def test_AC_WS_SURFACE_1_one_block_one_line_per_stream() -> None:
    block = wss.render_work_streams_block(
        streams=_streams(),
        derive=lambda n: _record(),
        emit_deviation_fn=lambda s, st: None,
    )
    assert block.count("[work-streams]") == 1, "exactly ONE block"
    # one short line per stream (the two seeded slugs).
    assert "- loam " in block
    assert "- cairn " in block


def test_AC_WS_SURFACE_1_within_char_cap() -> None:
    block = wss.render_work_streams_block(
        streams=_streams(),
        derive=lambda n: _record(),
        emit_deviation_fn=lambda s, st: None,
    )
    assert len(block) <= wss._STREAM_BLOCK_CHAR_CAP, "the hard cap is never exceeded"


def test_AC_WS_SURFACE_1_subsumes_project_state_block() -> None:
    # The production composer registers ONE STATE turn-contributor
    # (work-streams), which SUBSUMES the bare project-state block — there
    # is not a second project-state block.
    ws_root = Path("/tmp/ws-surface-1-test")
    ws_root.mkdir(parents=True, exist_ok=True)
    composer = build_session_composer(
        ws_root,
        memory_client_factory=lambda _root: None,
        register_tracker=False,
    )
    names = [c.name for c in composer.contributors(trigger_kind=TriggerKind.turn)]
    assert "work-streams" in names
    assert "project-state" not in names, (
        "the project-state block must be SUBSUMED, not added as a second block"
    )
