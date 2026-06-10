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

"""★ AC.RDM.S (outcome-altitude) — the PRODUCTION hook entry-point
(``subagent_start_context.py`` as a subprocess, the AC.SACH.S /
AC.EWR.S pattern), driven with the REAL captured SubagentStart envelope
shape (common fields only — session_id / transcript_path / cwd /
agent_id / agent_type / hook_event_name; Tier-0 probe captures,
2026-06-10) plus a real-shape transcript fixture whose last user
message is relevant to a planted RULED decision record, emits an
``additionalContext`` whose MEMORY tier is NON-degraded and carries the
planted record.

outcome-altitude: true

This is the memory-tier twin of AC.EWR.S: that regression pinned the
microkernel tier on real envelopes; pre-fix, the memory tier STILL
degraded on every real dispatch because ``task_text`` was seeded only
from envelope fields (``prompt``/``task``/``description``) real
envelopes do not carry — no memory query ever ran. n=1 architectural
verdict (does the real envelope shape populate the memory tier AT
ALL?) per feedback_n1_architectural_vs_n3_statistical.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import REPO_ROOT

from loam.frame_kernel.bundle import MICROKERNEL_PRIME_MARKER
from loam.primary_persona.decision_ledger import write_decision
from loam.primary_persona.file_memory import memory_dir_for_workspace

_HOOK_PATH = (
    REPO_ROOT / "framework" / "frame-kernel" / "hooks" / "subagent_start_context.py"
)
_MEMORY_UNAVAILABLE_MARKER = "[memory unavailable — no live store or query]"

USER_ASK = "plan the Tilth raise workstream for next week"


def _venv_python() -> str:
    venv_py = REPO_ROOT / ".venv" / "bin" / "python"
    if venv_py.exists():
        return str(venv_py)
    return sys.executable


def _real_shape_transcript(path: Path) -> None:
    """A transcript fixture mirroring the REAL captured record shapes
    at SubagentStart fire time (queue-operation / user / attachment /
    ai-title / assistant / tool_result)."""
    records = [
        {"type": "queue-operation", "operation": "enqueue", "sessionId": "s-1"},
        {
            "type": "user",
            "message": {"role": "user", "content": USER_ASK},
            "sessionId": "s-1",
        },
        {"type": "attachment", "attachment": {}, "sessionId": "s-1"},
        {"type": "ai-title", "aiTitle": "probe", "sessionId": "s-1"},
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
        {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_x",
                        "content": [{"type": "text", "text": "ok"}],
                    }
                ],
            },
            "sessionId": "s-1",
        },
    ]
    path.write_text(
        "\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8"
    )


def test_AC_RDM_S_real_envelope_memory_tier_carries_planted_ruling(
    tmp_path: Path,
) -> None:
    """★ outcome-altitude: real-shape envelope + real-shape transcript
    fixture through the production hook subprocess — the planted ruled
    decision record reaches the injected memory tier."""
    ws = tmp_path / "ws"
    (ws / "kernel").mkdir(parents=True)
    (ws / "kernel" / "loam-microkernel.md").write_text(
        "# loam microkernel\nTHREE ROLES guard.\n", encoding="utf-8"
    )
    mem = memory_dir_for_workspace(ws)
    write_decision(
        mem,
        question="How large is the Tilth raise ask?",
        ruling="$750,000 at $4M post-money valuation",
        reasoning="AI-era raises differ; comp-heavy is fine founder-led.",
        entities=("Tilth", "raise"),
        source="telegram message 14053, 2026-06-07",
        workstream="tilth",
    )
    transcript = tmp_path / "parent-session.jsonl"
    _real_shape_transcript(transcript)

    # EXACTLY the captured real envelope shape — the documented common
    # six fields, nothing else.
    envelope = {
        "session_id": "s-1",
        "transcript_path": str(transcript),
        "cwd": str(ws),
        "agent_id": "a-1",
        "agent_type": "general-purpose",
        "hook_event_name": "SubagentStart",
    }

    proc = subprocess.run(
        [_venv_python(), str(_HOOK_PATH)],
        input=json.dumps(envelope),
        capture_output=True,
        text=True,
        timeout=60,
    )

    # (a) Fail-soft contract unchanged: exit 0, never blocks a dispatch.
    assert proc.returncode == 0, (
        f"production hook exited {proc.returncode}; stderr:\n{proc.stderr}"
    )

    payload = json.loads(proc.stdout)
    out = payload["hookSpecificOutput"]
    assert out["hookEventName"] == "SubagentStart"
    injected = out["additionalContext"]

    # (b) Bundle shape intact.
    assert MICROKERNEL_PRIME_MARKER in injected
    memory_tier = injected.split("=== relevant memory ===", 1)[1]

    # (c) ★ THE outcome-altitude assertion: the memory tier is
    #     NON-degraded on the real envelope shape and carries the
    #     planted ruling WHOLE. Pre-fix this failed: task_text was
    #     empty by construction and the tier rendered the
    #     unavailable-marker on every real dispatch.
    assert _MEMORY_UNAVAILABLE_MARKER not in memory_tier, (
        "REGRESSION (AC.RDM.S): the real envelope shape degraded the "
        "memory tier — no task text was derived from the transcript"
    )
    assert "$750,000 at $4M post-money valuation" in memory_tier
    assert "telegram message 14053" in memory_tier
