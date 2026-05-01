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

"""AC.M.9 — Transcript unreadable / unrecognised: graceful no-op.

Outcome (per locked plan §5): given a Stop envelope whose
``transcript_path`` is missing, unreadable, malformed JSONL, or
contains no user message or no assistant reply (e.g., post-
``/compact`` shape or post-ESC-interrupt empty reply), the Stop
subcommand exits 0 and writes zero episodes. No traceback. No
partial-episode write.
"""

from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path


def _fire_stop(monkeypatch, transcript_path: str, workspace: Path) -> tuple[int, list]:
    spawn_calls: list = []

    class _RecorderPopen:
        def __init__(self, args, **kwargs):
            spawn_calls.append({"args": args, **kwargs})

    monkeypatch.setattr(subprocess, "Popen", _RecorderPopen)
    envelope = json.dumps(
        {"session_id": "s1", "transcript_path": transcript_path}
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(envelope))
    from loam.primary_persona.stop_emitter import cli_stop

    rc = cli_stop(workspace_root=workspace)
    return rc, spawn_calls


def test_AC_M_9_missing_transcript_no_spawn(
    tmp_path: Path, monkeypatch
) -> None:
    rc, spawn_calls = _fire_stop(
        monkeypatch, str(tmp_path / "missing.jsonl"), tmp_path
    )
    assert rc == 0
    assert spawn_calls == []


def test_AC_M_9_malformed_jsonl_no_spawn(
    tmp_path: Path, monkeypatch
) -> None:
    transcript = tmp_path / "bad.jsonl"
    transcript.write_text("{not valid json\n", encoding="utf-8")
    rc, spawn_calls = _fire_stop(monkeypatch, str(transcript), tmp_path)
    assert rc == 0
    assert spawn_calls == []


def test_AC_M_9_no_user_message_no_spawn(
    tmp_path: Path, monkeypatch
) -> None:
    transcript = tmp_path / "tx.jsonl"
    transcript.write_text(
        json.dumps({"role": "assistant", "content": "alone"}) + "\n",
        encoding="utf-8",
    )
    rc, spawn_calls = _fire_stop(monkeypatch, str(transcript), tmp_path)
    assert rc == 0
    assert spawn_calls == []


def test_AC_M_9_no_assistant_reply_no_spawn(
    tmp_path: Path, monkeypatch
) -> None:
    transcript = tmp_path / "tx.jsonl"
    transcript.write_text(
        json.dumps({"role": "user", "content": "lonely"}) + "\n",
        encoding="utf-8",
    )
    rc, spawn_calls = _fire_stop(monkeypatch, str(transcript), tmp_path)
    assert rc == 0
    assert spawn_calls == []


def test_AC_M_9_empty_assistant_content_treated_as_no_reply(
    tmp_path: Path, monkeypatch
) -> None:
    """ESC-interrupt shape: an assistant entry exists but its content
    list is empty. D11 graceful-no-op."""
    transcript = tmp_path / "tx.jsonl"
    transcript.write_text(
        json.dumps({"role": "user", "content": "ask"}) + "\n"
        + json.dumps({"role": "assistant", "content": []}) + "\n",
        encoding="utf-8",
    )
    rc, spawn_calls = _fire_stop(monkeypatch, str(transcript), tmp_path)
    assert rc == 0
    assert spawn_calls == []
