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

"""AC.FJO.1 — the judge's stated objective comes from the SUBAGENT'S OWN
transcript (``agent_transcript_path``), never the parent transcript.

The 2026-06-10 live incident: the judge prompt carried the PARENT
session's first user message (an owner channel message) as the judged
subagent's objective, because ``read_subagent_result`` loaded the
envelope's ``transcript_path`` — which points at the PARENT transcript
(probe-verified, plan §2). This AC pins the corrected sources:

  * objective — the agent transcript's first user message (the literal
    dispatch prompt);
  * consequential cue — the agent transcript's tool uses (D-FJO.3);
  * result — envelope ``last_assistant_message`` first (the agent
    transcript's final assistant text is not reliably flushed at fire
    time), agent-transcript tail as fallback;
  * envelope objective fields keep first priority (forward-compat);
  * absent/unreadable ``agent_transcript_path`` degrades fail-soft —
    missing-markers, no cue, no judge spawn, and NEVER a parent
    -transcript fallback (no advisory beats a wrong advisory).
"""

from __future__ import annotations

import json
from pathlib import Path

from conftest import (
    PARENT_TRANSCRIPT_MARKER,
    make_stop_envelope,
    write_parent_transcript,
    write_transcript,
)

from loam.frame_kernel import frame_judge as fj


def test_objective_is_the_agent_transcripts_dispatch_prompt(
    real_kernel_workspace: Path,
) -> None:
    """The seed's stated objective is the agent transcript's first user
    message — and no parent-transcript content reaches the seed."""
    transcript = write_transcript(
        real_kernel_workspace / "agent.jsonl",
        objective="DISPATCH-PROMPT-fix-the-stop-judge-objective-source",
        result="the fix is in",
        consequential=True,
    )
    ctx = fj.parse_stop_envelope(
        make_stop_envelope(real_kernel_workspace, transcript)
    )
    result = fj.read_subagent_result(ctx)
    seed = fj.assemble_seed(result)

    assert result.objective == (
        "DISPATCH-PROMPT-fix-the-stop-judge-objective-source"
    )
    assert "DISPATCH-PROMPT-fix-the-stop-judge-objective-source" in seed
    assert PARENT_TRANSCRIPT_MARKER not in seed, (
        "the 2026-06-10 live bug regressed: parent-transcript content "
        "reached the judge seed"
    )


def test_envelope_objective_fields_keep_first_priority(
    real_kernel_workspace: Path,
) -> None:
    """An explicit envelope objective field still wins over the agent
    transcript (forward-compat, unchanged)."""
    transcript = write_transcript(
        real_kernel_workspace / "agent.jsonl",
        objective="transcript objective",
        result="r",
        consequential=True,
    )
    envelope = make_stop_envelope(real_kernel_workspace, transcript)
    envelope["prompt"] = "ENVELOPE-FIELD-OBJECTIVE-WINS"
    result = fj.read_subagent_result(fj.parse_stop_envelope(envelope))
    assert result.objective == "ENVELOPE-FIELD-OBJECTIVE-WINS"


def test_consequential_cue_reads_the_agent_transcript_only(
    real_kernel_workspace: Path,
) -> None:
    """A read-only subagent finish is NOT consequential even though the
    decoy PARENT transcript carries a Write cue (D-FJO.3) — the judge is
    never spawned."""
    transcript = write_transcript(
        real_kernel_workspace / "agent.jsonl",
        objective="just read things",
        result="read them",
        consequential=False,
    )
    envelope = make_stop_envelope(real_kernel_workspace, transcript)

    spawned: dict = {}

    def _recording_judge(prompt: str, **_kw) -> str:
        spawned["prompt"] = prompt
        return fj.VERDICT_OFF_FRAME

    surface = fj.evaluate(envelope, _run_judge=_recording_judge)
    assert surface is None
    assert "prompt" not in spawned, (
        "the cue was read off the PARENT transcript (its Write tool_use "
        "fired the gate for a read-only subagent)"
    )


def test_result_prefers_envelope_last_assistant_message(
    real_kernel_workspace: Path,
) -> None:
    """``last_assistant_message`` (probe-verified envelope field) wins
    over the agent-transcript tail; without it the tail is the
    fallback."""
    transcript = write_transcript(
        real_kernel_workspace / "agent.jsonl",
        objective="o",
        result="TAIL-RESULT",
        consequential=True,
    )
    with_envelope = make_stop_envelope(
        real_kernel_workspace,
        transcript,
        last_assistant_message="ENVELOPE-RESULT-WINS",
    )
    result = fj.read_subagent_result(fj.parse_stop_envelope(with_envelope))
    assert result.result == "ENVELOPE-RESULT-WINS"

    without_envelope = make_stop_envelope(real_kernel_workspace, transcript)
    result = fj.read_subagent_result(fj.parse_stop_envelope(without_envelope))
    assert result.result == "TAIL-RESULT"


def test_absent_agent_transcript_degrades_without_parent_fallback(
    real_kernel_workspace: Path,
) -> None:
    """An envelope with NO ``agent_transcript_path`` (older Claude Code)
    degrades fail-soft: missing-markers, not consequential, no judge
    spawn — NEVER a parent-transcript approximation."""
    parent = write_parent_transcript(
        real_kernel_workspace / "parent-only.jsonl"
    )
    envelope = {
        "hook_event_name": "SubagentStop",
        "transcript_path": str(parent),
        "cwd": str(real_kernel_workspace),
        "agent_id": "sub-legacy",
    }
    ctx = fj.parse_stop_envelope(envelope)
    assert ctx.agent_transcript_path is None
    result = fj.read_subagent_result(ctx)

    assert result.objective == fj.SEED_OBJECTIVE_MISSING_MARKER, (
        "the parent transcript's user message must NOT become the "
        "objective when the agent transcript is absent"
    )
    assert result.consequential is False

    spawned: dict = {}

    def _recording_judge(prompt: str, **_kw) -> str:
        spawned["prompt"] = prompt
        return fj.VERDICT_OFF_FRAME

    assert fj.evaluate(envelope, _run_judge=_recording_judge) is None
    assert "prompt" not in spawned


def test_unreadable_agent_transcript_fails_soft(
    real_kernel_workspace: Path,
) -> None:
    """A missing or non-JSONL agent transcript degrades (no raise)."""
    missing = make_stop_envelope(
        real_kernel_workspace, real_kernel_workspace / "nope.jsonl"
    )
    result = fj.read_subagent_result(fj.parse_stop_envelope(missing))
    assert result.objective == fj.SEED_OBJECTIVE_MISSING_MARKER
    assert result.consequential is False

    garbage = real_kernel_workspace / "garbage.jsonl"
    garbage.write_text("not json at all\n{{{\n", encoding="utf-8")
    result = fj.read_subagent_result(
        fj.parse_stop_envelope(make_stop_envelope(real_kernel_workspace, garbage))
    )
    assert result.objective == fj.SEED_OBJECTIVE_MISSING_MARKER


def test_real_captured_record_shape_parses(real_kernel_workspace: Path) -> None:
    """The agent transcript's real record flavor (probe capture: type/
    message/role/content + sidechain metadata) yields the dispatch
    prompt."""
    agent = real_kernel_workspace / "real-shape-agent.jsonl"
    records = [
        {
            "parentUuid": None,
            "isSidechain": True,
            "agentId": "a46981ea4c06f4d4f",
            "type": "user",
            "message": {"role": "user", "content": "REAL-SHAPE-DISPATCH-PROMPT"},
            "userType": "external",
            "version": "2.1.170",
        },
        {"type": "attachment"},
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "name": "Write",
                        "input": {"file_path": "/tmp/d.md", "content": "x"},
                    }
                ],
            },
        },
    ]
    agent.write_text(
        "\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8"
    )
    result = fj.read_subagent_result(
        fj.parse_stop_envelope(make_stop_envelope(real_kernel_workspace, agent))
    )
    assert result.objective == "REAL-SHAPE-DISPATCH-PROMPT"
    assert result.consequential is True
