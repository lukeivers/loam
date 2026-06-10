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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.RDM.1 — given a real-shape SubagentStart envelope (common fields
only) whose ``transcript_path`` names a real-shape JSONL transcript,
``parse_envelope`` derives ``task_text`` from the transcript's last
real user message — skipping tool_result-only records, the
local-command/caveat preambles, and ``<task-notification>`` synthetic
turns. Envelope ``prompt``/``task``/``description`` still win when
present; a missing/unreadable transcript yields empty task_text
(fail-soft, no raise).

The transcript fixture mirrors the REAL captured shape (Tier-0 probe,
2026-06-10, /tmp/loam-sas-probe captures): queue-operation /
attachment / ai-title records interleaved with
``{"type": ..., "message": {"role": ..., "content": ...}}`` turns.
"""

from __future__ import annotations

import json
from pathlib import Path

from loam.frame_kernel.bundle import parse_envelope

USER_ASK = "plan the Tilth raise workstream for next week"


def _user_record(text: str) -> dict:
    return {
        "type": "user",
        "message": {"role": "user", "content": text},
        "sessionId": "s-1",
        "cwd": "/tmp/ws",
    }


def _tool_result_record() -> dict:
    # A tool_result user record (the real shape: content is a list of
    # tool_result blocks — no text blocks).
    return {
        "type": "user",
        "message": {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_x",
                    "content": [{"type": "text", "text": "raw tool output"}],
                }
            ],
        },
        "sessionId": "s-1",
    }


def _real_shape_records(last_user_text: str = USER_ASK) -> list[dict]:
    return [
        {"type": "queue-operation", "operation": "enqueue", "sessionId": "s-1"},
        _user_record(last_user_text),
        {"type": "attachment", "attachment": {}, "sessionId": "s-1"},
        {"type": "ai-title", "aiTitle": "probe", "sessionId": "s-1"},
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "on it"}],
            },
            "sessionId": "s-1",
        },
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_x",
                        "name": "ToolSearch",
                        "input": {"query": "select:Task"},
                    }
                ],
            },
            "sessionId": "s-1",
        },
        _tool_result_record(),
    ]


def _write_transcript(tmp_path: Path, records: list[dict]) -> Path:
    p = tmp_path / "session.jsonl"
    p.write_text(
        "\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8"
    )
    return p


def _real_envelope(tmp_path: Path, transcript: Path) -> dict:
    # EXACTLY the captured real shape: the documented common six fields.
    return {
        "session_id": "s-1",
        "transcript_path": str(transcript),
        "cwd": str(tmp_path),
        "agent_id": "a-1",
        "agent_type": "general-purpose",
        "hook_event_name": "SubagentStart",
    }


def test_AC_RDM_1_last_real_user_message_is_the_task_text(
    tmp_path: Path,
) -> None:
    transcript = _write_transcript(tmp_path, _real_shape_records())
    ctx = parse_envelope(_real_envelope(tmp_path, transcript))
    assert ctx.task_text == USER_ASK, (
        "AC.RDM.1: the real-shape envelope (no dispatch-text fields) "
        "must derive task_text from the transcript's last real user "
        "message"
    )


def test_AC_RDM_1_envelope_fields_keep_first_priority(
    tmp_path: Path,
) -> None:
    transcript = _write_transcript(tmp_path, _real_shape_records())
    envelope = _real_envelope(tmp_path, transcript)
    envelope["prompt"] = "explicit dispatch text"
    ctx = parse_envelope(envelope)
    assert ctx.task_text == "explicit dispatch text", (
        "AC.RDM.1: an envelope dispatch-text field wins over the "
        "transcript derivation (forward-compat priority)"
    )


def test_AC_RDM_1_tool_result_only_records_skipped(tmp_path: Path) -> None:
    # The tool_result record is LAST; the derivation must reach back to
    # the real user ask before it.
    records = _real_shape_records()
    assert records[-1]["message"]["content"][0]["type"] == "tool_result"
    transcript = _write_transcript(tmp_path, records)
    ctx = parse_envelope(_real_envelope(tmp_path, transcript))
    assert ctx.task_text == USER_ASK


def test_AC_RDM_1_synthetic_turns_skipped(tmp_path: Path) -> None:
    records = _real_shape_records() + [
        _user_record(
            "Caveat: the messages below were generated by the user "
            "while running local commands."
        ),
        _user_record("<local-command-stdout>ok</local-command-stdout>"),
        _user_record(
            "[SYSTEM NOTIFICATION - NOT USER INPUT]\n"
            "<task-notification>\n<task-id>x</task-id>\n"
            "</task-notification>"
        ),
    ]
    transcript = _write_transcript(tmp_path, records)
    ctx = parse_envelope(_real_envelope(tmp_path, transcript))
    assert ctx.task_text == USER_ASK, (
        "AC.RDM.1: caveat / local-command / task-notification synthetic "
        "turns are not the user ask"
    )


def test_AC_RDM_1_missing_or_unreadable_transcript_fail_soft(
    tmp_path: Path,
) -> None:
    # Missing file.
    envelope = _real_envelope(tmp_path, tmp_path / "nope.jsonl")
    ctx = parse_envelope(envelope)
    assert ctx.task_text == ""
    # Non-JSONL garbage.
    garbage = tmp_path / "garbage.jsonl"
    garbage.write_bytes(b"\x00\xff not json \n{broken")
    ctx = parse_envelope(_real_envelope(tmp_path, garbage))
    assert ctx.task_text == ""
    # Workspace root still resolved from cwd in every case (the sealed
    # AC.EWR.1 behavior is untouched).
    assert ctx.workspace_root == Path(str(tmp_path))


def test_AC_RDM_1_no_user_message_yields_empty(tmp_path: Path) -> None:
    records = [
        {"type": "queue-operation", "operation": "enqueue", "sessionId": "s-1"},
        _tool_result_record(),
    ]
    transcript = _write_transcript(tmp_path, records)
    ctx = parse_envelope(_real_envelope(tmp_path, transcript))
    assert ctx.task_text == ""
