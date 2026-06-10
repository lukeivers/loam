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

"""AC.FJO.2 — the off-frame flag SELF-IDENTIFIES as a frame-judge
advisory naming the judged dispatch.

The 2026-06-10 incident's second half: the owner received a bare
OFF_FRAME verdict with no provenance — no indication of what produced
it or which dispatch it judged — and was warrantedly confused. The
advisory must be readable out of context: it names itself ("frame-judge
advisory"), the dispatch's agent flavor + subagent id, and a first-line
excerpt of the judged objective (all from authoritative envelope /
agent-transcript sources — D-FJO.2, never a parent Task-tool_use scan).
"""

from __future__ import annotations

from pathlib import Path

from conftest import make_stop_envelope, write_transcript

from loam.frame_kernel import frame_judge as fj


def _off_frame_judge(prompt: str, **_kw) -> str:
    return "result swapped in a self-diagnostic\n" + fj.VERDICT_OFF_FRAME


def test_advisory_names_itself_and_the_judged_dispatch(
    real_kernel_workspace: Path,
) -> None:
    """The systemMessage carries: 'frame-judge advisory', the agent
    flavor, the subagent id, and the judged objective's first line."""
    transcript = write_transcript(
        real_kernel_workspace / "agent.jsonl",
        objective=(
            "Report whether the injected memory tier populated.\n"
            "Second line that must not be required in the excerpt."
        ),
        result="self-diagnostic report",
        consequential=True,
    )
    envelope = make_stop_envelope(
        real_kernel_workspace,
        transcript,
        subagent_id="agent-d2a864",
        agent_type="general-purpose",
    )

    surface = fj.evaluate(envelope, _run_judge=_off_frame_judge)
    assert surface is not None
    message = surface["hookSpecificOutput"]["systemMessage"]

    assert "frame-judge advisory" in message, (
        "the flag must self-identify — a bare verdict reached the owner "
        "on 2026-06-10 with no provenance"
    )
    assert "general-purpose" in message, "names the dispatch's agent flavor"
    assert "agent-d2a864" in message, "names the judged subagent"
    assert "Report whether the injected memory tier populated." in message, (
        "carries a first-line excerpt of the judged objective"
    )
    assert "non-blocking" in message.lower()
    # Still the non-blocking surface shape (AC.SSFC.4 unchanged).
    assert "decision" not in surface["hookSpecificOutput"]


def test_long_objective_excerpt_is_truncated(
    real_kernel_workspace: Path,
) -> None:
    """A very long dispatch-prompt first line is excerpted, not dumped
    whole into the advisory."""
    long_line = "X" * 500
    transcript = write_transcript(
        real_kernel_workspace / "agent.jsonl",
        objective=long_line,
        result="r",
        consequential=True,
    )
    surface = fj.evaluate(
        make_stop_envelope(real_kernel_workspace, transcript),
        _run_judge=_off_frame_judge,
    )
    assert surface is not None
    message = surface["hookSpecificOutput"]["systemMessage"]
    assert "X" * 120 in message
    assert "X" * 121 not in message


def test_render_surface_without_result_still_renders(
) -> None:
    """``render_surface`` stays callable without a result (degraded /
    legacy call shape): the advisory renders without a task excerpt."""
    ctx = fj.StopContext(
        transcript_path=None,
        workspace_root=None,
        envelope_objective="",
        envelope_result="",
        subagent_id="sub-9",
        agent_type="loam-builder",
    )
    off = fj.render_surface(
        fj.Verdict(off_frame=True, reason="drifted", parsed=True), ctx
    )
    assert off is not None
    message = off["hookSpecificOutput"]["systemMessage"]
    assert "frame-judge advisory" in message
    assert "loam-builder" in message
    assert "sub-9" in message
    assert "task:" not in message, "no objective available -> no excerpt"


def test_missing_objective_marker_never_excerpted(
    real_kernel_workspace: Path,
) -> None:
    """The degraded missing-objective marker is not presented as the
    dispatch's task text."""
    import json

    # An agent transcript with no user message at all.
    agent = real_kernel_workspace / "no-user.jsonl"
    agent.write_text(
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "tool_use",
                            "name": "Write",
                            "input": {"file_path": "/tmp/d", "content": "x"},
                        }
                    ],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    surface = fj.evaluate(
        make_stop_envelope(real_kernel_workspace, agent),
        _run_judge=_off_frame_judge,
    )
    assert surface is not None
    message = surface["hookSpecificOutput"]["systemMessage"]
    assert fj.SEED_OBJECTIVE_MISSING_MARKER not in message
    assert "task:" not in message
