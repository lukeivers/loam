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

"""AC.SSFC.4 — an off-frame verdict SURFACES a flag to the dispatcher
naming the subagent + the inconsistency + the reason; an on-frame verdict
surfaces nothing (silent no-op). Off-frame is never silently passed.

The test feeds the judge path a stubbed off-frame verdict -> asserts a
surfaced flag (a ``systemMessage`` envelope) carrying the subagent id +
reason; feeds an on-frame verdict -> asserts no flag emitted.
"""

from __future__ import annotations

from pathlib import Path

from conftest import make_stop_envelope, write_transcript

from loam.frame_kernel import frame_judge as fj


def _consequential_envelope(workspace: Path) -> dict:
    transcript = write_transcript(
        workspace / "t.jsonl",
        objective="do the thing",
        result="here is the result",
        consequential=True,
    )
    return make_stop_envelope(workspace, transcript, subagent_id="sub-XYZ")


def test_off_frame_verdict_surfaces_flag(real_kernel_workspace: Path) -> None:
    """A stubbed OFF_FRAME verdict -> a non-blocking systemMessage naming
    the subagent + the judge reason."""
    def _off_frame_judge(prompt: str, **_kw) -> str:
        return "the result invents a different objective\n" + fj.VERDICT_OFF_FRAME

    surface = fj.evaluate(
        _consequential_envelope(real_kernel_workspace),
        _run_judge=_off_frame_judge,
    )

    assert surface is not None, "off-frame MUST surface (never silently pass)"
    out = surface["hookSpecificOutput"]
    assert out["hookEventName"] == fj.SUBAGENT_STOP_EVENT
    message = out["systemMessage"]
    assert "sub-XYZ" in message, "the surface names the subagent"
    assert "invents a different objective" in message, (
        "the surface carries the judge's reason"
    )
    assert "non-blocking" in message.lower(), "the surface is non-blocking"
    # It is NOT a hard-block decision (v1; D-SSFC.4).
    assert "decision" not in out


def test_on_frame_verdict_surfaces_nothing(real_kernel_workspace: Path) -> None:
    """A stubbed ON_FRAME verdict -> a silent no-op (no surface)."""
    def _on_frame_judge(prompt: str, **_kw) -> str:
        return "consistent with the core\n" + fj.VERDICT_ON_FRAME

    surface = fj.evaluate(
        _consequential_envelope(real_kernel_workspace),
        _run_judge=_on_frame_judge,
    )
    assert surface is None, "an on-frame verdict surfaces nothing"


def test_render_surface_directly_off_and_on() -> None:
    """render_surface: off-frame -> envelope; on-frame -> None."""
    ctx = fj.StopContext(
        transcript_path=None,
        workspace_root=None,
        envelope_objective="",
        envelope_result="",
        subagent_id="sub-1",
    )
    off = fj.render_surface(
        fj.Verdict(off_frame=True, reason="drifted", parsed=True), ctx
    )
    assert off is not None
    assert "sub-1" in off["hookSpecificOutput"]["systemMessage"]
    assert "drifted" in off["hookSpecificOutput"]["systemMessage"]

    on = fj.render_surface(
        fj.Verdict(off_frame=False, reason="", parsed=True), ctx
    )
    assert on is None
