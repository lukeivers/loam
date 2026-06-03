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

"""AC.WS.DERIVE.1 — for a stream bound to >=1 registered project, the
surfaced STATE + next-action is composed from a FRESH derive_project_state
call (Slice C), never a stored/cached-stale string; changing the
underlying ground truth + re-reading reflects the change WITHOUT editing
the register."""

from __future__ import annotations

from loam.primary_persona.keep_pace import work_streams as ws
from loam.primary_persona.keep_pace import work_streams_surface as wss


def _record(comps):
    class _L:
        def __init__(self, v):
            self.value = v

    class _C:
        def __init__(self, n, v):
            self.name = n
            self.liveness = _L(v)

    class _R:
        def __init__(self, rows):
            self.components = [_C(n, v) for n, v in rows]
            self.head_sha = "deadbeef"

    return _R(comps)


def test_AC_WS_DERIVE_1_state_composed_from_fresh_derive() -> None:
    stream = ws.WorkStream(slug="loam", attention="active", objective="o",
                           detail_path="d", projects=["loam"])
    # The derive is called FRESH; the line carries the derived class.
    calls = {"n": 0}

    def derive(name):
        calls["n"] += 1
        return _record([("core", "merged")])

    line = wss.render_stream_line(stream, derive=derive)
    assert calls["n"] == 1, "the surfacer must call derive (not a stored string)"
    assert "built (merged)" in line
    assert "loam" in line


def test_AC_WS_DERIVE_1_ground_truth_change_reflects_without_register_edit() -> None:
    # The register entry is UNCHANGED across both reads; only the ground
    # truth the derive returns changes — and the surfaced STATE follows.
    stream = ws.WorkStream(slug="loam", attention="active", objective="o",
                           detail_path="d", projects=["loam"])

    state = {"phase": "sealed"}

    def derive(name):
        return _record([("core", state["phase"])])

    line_before = wss.render_stream_line(stream, derive=derive)
    assert "sealed" in line_before

    # Ground truth advances; the register is NOT touched.
    state["phase"] = "merged"
    line_after = wss.render_stream_line(stream, derive=derive)
    assert "built (merged)" in line_after
    assert line_after != line_before, (
        "a ground-truth change must change the surfaced STATE (derived, "
        "not stored)"
    )


def test_AC_WS_DERIVE_1_next_action_derived_from_state() -> None:
    # The next-action is derived from the STATE phrases, not stored.
    stream = ws.WorkStream(slug="loam", attention="active", objective="o",
                           detail_path="d", projects=["loam"])
    sealed_line = wss.render_stream_line(
        stream, derive=lambda n: _record([("core", "sealed")])
    )
    assert "merge the sealed work" in sealed_line
    unbuilt_line = wss.render_stream_line(
        stream, derive=lambda n: _record([("core", "unbuilt")])
    )
    assert "advance the not-built stage" in unbuilt_line
