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

"""AC.WS.DEVIATE.1 — when a stream's expected state diverges from its
derived FBM STATE, a structured deviation record {stream, expected,
derived, evidence} is emitted to the memory-reality mismatch side-channel
(#71); if that channel's entry point is ABSENT the detection no-ops
fail-soft (never crashes the turn). #71 is pending — the seam is the
integration point."""

from __future__ import annotations

from loam.primary_persona.keep_pace import work_streams as ws
from loam.primary_persona.keep_pace import work_streams_surface as wss


def test_AC_WS_DEVIATE_1_divergence_emits_structured_record() -> None:
    stream = ws.WorkStream(slug="loam", attention="active",
                           objective="FBM overhaul complete and merged",
                           detail_path="d", projects=["loam"])
    captured = []
    # A derived STATE that reports unverified work => a deviation.
    rec = wss.emit_deviation(
        stream,
        "core = status unknown",
        emit=lambda r: captured.append(r),
    )
    assert rec is not None, "a real divergence must emit"
    assert captured, "the record routes to the channel sink"
    got = captured[0]
    assert got["stream"] == "loam"
    assert got["expected"] == "FBM overhaul complete and merged"
    assert "status unknown" in got["derived"]
    assert got["evidence"]  # carries the evidence trail


def test_AC_WS_DEVIATE_1_no_divergence_no_emit() -> None:
    stream = ws.WorkStream(slug="loam", attention="active", objective="o",
                           detail_path="d", projects=["loam"])
    captured = []
    rec = wss.emit_deviation(
        stream, "core = built (merged)", emit=lambda r: captured.append(r)
    )
    assert rec is None, "a clean (merged) STATE is not a deviation"
    assert not captured


def test_AC_WS_DEVIATE_1_absent_channel_no_ops_fail_soft() -> None:
    # #71's entry point is ABSENT today. With no emit override the seam
    # attempts the import, which fails, and NO-OPS — never raises.
    stream = ws.WorkStream(slug="loam", attention="active", objective="o",
                           detail_path="d", projects=["loam"])
    # Even on a divergence, the absent channel path returns None, no raise.
    rec = wss.emit_deviation(stream, "core = status unknown")
    assert rec is None, "absent #71 channel => fail-soft no-op (not a crash)"


def test_AC_WS_DEVIATE_1_erroring_channel_never_crashes_turn() -> None:
    stream = ws.WorkStream(slug="loam", attention="active",
                           objective="done", detail_path="d",
                           projects=["loam"])

    def boom(_r):
        raise RuntimeError("channel down")

    # A live-but-erroring channel must not crash the turn.
    rec = wss.emit_deviation(stream, "core = not built", emit=boom)
    assert rec is None


def test_AC_WS_DEVIATE_1_seam_runs_inside_block_render() -> None:
    # The deviation seam rides inside the block render and never breaks it.
    stream = ws.WorkStream(slug="loam", attention="active", objective="done",
                           detail_path="d", projects=["loam"])

    class _L:
        value = "unknown"

    class _C:
        name = "core"
        liveness = _L()

    class _R:
        components = [_C()]
        head_sha = "abc"

    seen = []
    block = wss.render_work_streams_block(
        streams=[stream],
        derive=lambda n: _R(),
        emit_deviation_fn=lambda s, st: seen.append((s.slug, st)),
    )
    assert block  # the block still renders
    assert seen and seen[0][0] == "loam", "the deviation seam fired for the stream"
