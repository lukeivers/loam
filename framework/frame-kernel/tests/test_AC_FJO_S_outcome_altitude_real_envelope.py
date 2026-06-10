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

"""★ AC.FJO.S (outcome-altitude) — the PRODUCTION SubagentStop hook,
driven with the REAL captured envelope shape, composes a judge prompt
whose stated objective is the planted DISPATCH PROMPT — and NOT the
parent session's channel message (the 2026-06-10 live-incident replay,
inverted).

outcome-altitude: true

WHAT IS REAL vs STUBBED (F2, the AC.SSFC.S posture). The envelope is a
field-for-field replica of the REAL captured SubagentStop envelope (n=2
probe captures, 2026-06-10, Claude Code 2.1.170 — plan §2): all
thirteen fields, ``transcript_path`` pointing at a PARENT-session
fixture whose first user message is a channel-shaped owner message (the
live incident's leaked objective), ``agent_transcript_path`` pointing
at the subagent's own transcript fixture whose first user message is
the planted dispatch prompt — and, mirroring the verified fire-time
flush state, NO final assistant text record (run 1 of the probes) —
with ``last_assistant_message`` carrying the subagent's final output.
The PRODUCTION hook ``main()`` runs end-to-end with the REAL on-disk
kernel + the REAL ``spawn_isolated_claude`` argv/env construction; the
ONLY stub is the ``subprocess.run`` boundary inside the sealed spawn
surface (no API key; subscription-only), returning a canned verdict so
the production verdict-parse + advisory-render path runs for real.
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

from conftest import KERNEL_FILE, REPO_ROOT

from loam.frame_kernel import frame_judge as fj

_SPAWN_SRC = (
    Path(fj.__file__).resolve().parents[5]
    / "framework"
    / "tools"
    / "loam-spawn-isolation"
    / "src"
)
if str(_SPAWN_SRC) not in sys.path:
    sys.path.insert(0, str(_SPAWN_SRC))

import loam_spawn_isolation as iso_mod  # noqa: E402

_HOOK_PATH = (
    REPO_ROOT / "framework" / "frame-kernel" / "hooks" / "subagent_stop_frame_check.py"
)
_spec = importlib.util.spec_from_file_location("subagent_stop_frame_check", _HOOK_PATH)
assert _spec is not None and _spec.loader is not None
hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hook)

# The live incident's shape, replayed as fixtures.
_CHANNEL_MESSAGE = (
    '<channel source="plugin:discord:discord" message_id="1513987674" '
    'user="grassly">give me the current state and what is next</channel>'
)
_DISPATCH_PROMPT = (
    "PLANTED-DISPATCH-PROMPT: probe the injected memory tier and report "
    "(a) marker presence (b) microkernel reality (c) memory-tier records."
)
_SUBAGENT_RESULT = (
    "PLANTED-RESULT: report on the injected block — markers present, "
    "microkernel real, two decision records in the memory tier."
)


def _write_jsonl(path: Path, records: list[dict]) -> Path:
    path.write_text(
        "\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8"
    )
    return path


def _real_shape_fixtures(workspace: Path) -> dict:
    """The REAL captured envelope, field for field, over two real-shape
    transcript fixtures."""
    parent = _write_jsonl(
        workspace / "parent-session.jsonl",
        [
            {"type": "queue-operation"},
            {
                "type": "user",
                "message": {"role": "user", "content": _CHANNEL_MESSAGE},
            },
            {"type": "attachment"},
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "tool_use",
                            "name": "Task",
                            "input": {
                                "description": "memory probe",
                                "prompt": _DISPATCH_PROMPT,
                            },
                        }
                    ],
                },
            },
        ],
    )
    subagents_dir = workspace / "session-0000" / "subagents"
    subagents_dir.mkdir(parents=True, exist_ok=True)
    # Fire-time flush state per probe run 1: first user message = the
    # dispatch prompt; a consequential Write cue; NO final assistant
    # text record (the result travels on last_assistant_message).
    agent = _write_jsonl(
        subagents_dir / "agent-a46981ea4c06f4d4f.jsonl",
        [
            {
                "parentUuid": None,
                "isSidechain": True,
                "agentId": "a46981ea4c06f4d4f",
                "type": "user",
                "message": {"role": "user", "content": _DISPATCH_PROMPT},
                "userType": "external",
                "version": "2.1.170",
            },
            {"type": "attachment"},
            {"type": "attachment"},
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "tool_use",
                            "name": "Write",
                            "input": {
                                "file_path": "/tmp/probe-report.md",
                                "content": "x",
                            },
                        }
                    ],
                },
            },
            {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [
                        {"type": "tool_result", "content": "File created"}
                    ],
                },
            },
        ],
    )
    return {
        "session_id": "session-0000",
        "transcript_path": str(parent),
        "cwd": str(workspace),
        "permission_mode": "auto",
        "agent_id": "a46981ea4c06f4d4f",
        "agent_type": "general-purpose",
        "effort": {"level": "high"},
        "hook_event_name": "SubagentStop",
        "stop_hook_active": False,
        "agent_transcript_path": str(agent),
        "last_assistant_message": _SUBAGENT_RESULT,
        "background_tasks": [],
        "session_crons": [],
    }


class _FakeProc:
    def __init__(self, stdout: str) -> None:
        self.returncode = 0
        self.stdout = stdout
        self.stderr = ""


def _install_spawn_stub(monkeypatch, verdict_token: str, captured: dict) -> None:
    def _fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured["env"] = kwargs.get("env")
        body = json.dumps({"result": f"judged against the dispatch\n{verdict_token}"})
        return _FakeProc(body)

    monkeypatch.setattr(iso_mod.subprocess, "run", _fake_run)


def _run_hook(envelope: dict, monkeypatch) -> tuple[int, str]:
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(envelope)))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    rc = hook.main()
    return rc, out.getvalue()


def test_AC_FJO_S_judge_prompt_carries_the_dispatch_prompt_not_the_channel_message(
    real_kernel_workspace: Path, monkeypatch
) -> None:
    """★ outcome-altitude: production hook + real captured envelope shape
    → the composed judge prompt's objective is the planted dispatch
    prompt; the parent channel message never reaches it; the flag
    self-identifies."""
    envelope = _real_shape_fixtures(real_kernel_workspace)

    captured: dict = {}
    _install_spawn_stub(monkeypatch, fj.VERDICT_OFF_FRAME, captured)

    rc, out = _run_hook(envelope, monkeypatch)

    assert rc == 0
    assert "argv" in captured, (
        "the production hook did not reach the judge spawn on the real "
        "captured envelope shape"
    )

    # ★ THE assertions: the judge prompt's stated objective is the
    # subagent's actual dispatched task text (dispatch AC1/AC2)...
    prompt = captured["argv"][captured["argv"].index("-p") + 1]
    objective_block = prompt.split(fj.SEED_OBJECTIVE_MARKER, 1)[1].split(
        fj.SEED_RESULT_MARKER, 1
    )[0]
    assert _DISPATCH_PROMPT in objective_block, (
        "the stated-objective block must carry the dispatched subagent's "
        "actual task text"
    )
    # ...and the live incident's leak is gone: NO parent/channel content
    # anywhere in the judge prompt.
    assert _CHANNEL_MESSAGE not in prompt
    assert "give me the current state" not in prompt
    # The result travelled on last_assistant_message (fire-time flush
    # state: the agent transcript has no final assistant text).
    assert _SUBAGENT_RESULT in prompt
    # The real on-disk kernel seeded the judge.
    assert "THREE ROLES" in KERNEL_FILE.read_text(encoding="utf-8")
    assert "THREE ROLES" in prompt

    # The flag self-identifies (dispatch AC4 / AC.FJO.2): a human reading
    # it out of context knows what it is and what it judged.
    payload = json.loads(out)
    message = payload["hookSpecificOutput"]["systemMessage"]
    assert "frame-judge advisory" in message
    assert "general-purpose" in message
    assert "a46981ea4c06f4d4f" in message
    assert "PLANTED-DISPATCH-PROMPT" in message

    # Isolation construction stayed real (AC.SSFC.3 unchanged).
    argv = captured["argv"]
    assert "--strict-mcp-config" in argv
    assert "ANTHROPIC_API_KEY" not in (captured["env"] or {})


def test_AC_FJO_S_on_frame_control_still_silent(
    real_kernel_workspace: Path, monkeypatch
) -> None:
    """Control: same real-shape envelope, ON_FRAME verdict → silence
    (the non-blocking contract unchanged)."""
    envelope = _real_shape_fixtures(real_kernel_workspace)
    captured: dict = {}
    _install_spawn_stub(monkeypatch, fj.VERDICT_ON_FRAME, captured)

    rc, out = _run_hook(envelope, monkeypatch)
    assert rc == 0
    assert "argv" in captured
    assert out.strip() == ""
