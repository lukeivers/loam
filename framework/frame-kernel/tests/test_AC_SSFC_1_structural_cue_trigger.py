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

"""AC.SSFC.1 — the SubagentStop hook evaluates a CONSEQUENTIAL subagent
(it wrote a deliverable / mutated state — a structural cue on the
transcript) and does NOT spawn a judge for a trivial read-only finish.

The test drives the production ``evaluate`` entry-point with (a) a
transcript bearing a consequential cue -> the judge path is exercised
(the injected judge runs); (b) a transcript with no consequential cue ->
the judge path is NOT taken (the injected judge never runs / no spawn).
Asserts the trigger gates on the structural cue, not on every finish.

The cue SHAPE is what is asserted (wrote-deliverable / mutated-state),
not a specific cue list — the exact list is the build-time-empirical knob
(plan §6-Q1 / RF-5).
"""

from __future__ import annotations

from pathlib import Path

from conftest import make_stop_envelope, write_transcript

from loam.frame_kernel import frame_judge as fj


def _spy_judge():
    """A judge stub that records whether it was called + returns ON_FRAME."""
    calls: list[str] = []

    def _judge(prompt: str, **_kw) -> str:
        calls.append(prompt)
        return fj.VERDICT_ON_FRAME

    return _judge, calls


def test_consequential_finish_spawns_the_judge(
    real_kernel_workspace: Path,
) -> None:
    """A subagent that WROTE a deliverable (a Write tool_use cue) ->
    the judge path is exercised."""
    transcript = write_transcript(
        real_kernel_workspace / "consequential.jsonl",
        objective="write the report",
        result="done — wrote the report",
        consequential=True,
    )
    envelope = make_stop_envelope(real_kernel_workspace, transcript)
    judge, calls = _spy_judge()

    fj.evaluate(envelope, _run_judge=judge)

    assert len(calls) == 1, (
        "a consequential subagent finish must spawn the judge exactly once"
    )


def test_trivial_finish_does_not_spawn_the_judge(
    real_kernel_workspace: Path,
) -> None:
    """A read-only subagent (no write/mutation cue) -> the judge is NOT
    spawned (the gate keeps the check cheap)."""
    transcript = write_transcript(
        real_kernel_workspace / "trivial.jsonl",
        objective="read the file and report",
        result="the file says foo",
        consequential=False,
    )
    envelope = make_stop_envelope(real_kernel_workspace, transcript)
    judge, calls = _spy_judge()

    surface = fj.evaluate(envelope, _run_judge=judge)

    assert calls == [], (
        "a trivial read-only finish must NOT spawn the judge (the "
        "structural-cue gate)"
    )
    assert surface is None, "a trivial finish surfaces nothing"


def test_is_consequential_predicate_gates_on_write_cue() -> None:
    """The predicate fires on a Write tool_use, not on a read-only one."""
    write_records = [
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "name": "Edit", "input": {}},
                ],
            },
        }
    ]
    readonly_records = [
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "name": "Bash",
                        "input": {"command": "grep foo bar.txt"},
                    },
                ],
            },
        }
    ]
    assert fj.is_consequential(write_records) is True
    assert fj.is_consequential(readonly_records) is False


def test_mutating_bash_is_a_consequential_cue() -> None:
    """A mutating Bash (not a recognized read-only prefix) IS a cue."""
    records = [
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "name": "Bash",
                        "input": {"command": "rm -rf /tmp/x && loam amend apply"},
                    },
                ],
            },
        }
    ]
    assert fj.is_consequential(records) is True
