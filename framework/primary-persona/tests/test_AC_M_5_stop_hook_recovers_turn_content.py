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

"""AC.M.5 — Stop-hook recovers user message + assistant reply from transcript.

Outcome (per locked plan §5): given a Stop envelope whose
``transcript_path`` points at a well-formed JSONL transcript carrying
at least one user message and one assistant reply, the Stop
subcommand extracts the most recent user message text AND the most
recent assistant reply text, derives a stable turn id from those +
``session_id``, and hands them to the turn-close write path.

Behaviour: the test asserts the write path was invoked with the
recovered content. We monkeypatch ``_spawn_memory_write`` so the
spawn doesn't actually fork; we assert it received the right kwargs.
"""

from __future__ import annotations

import io
import json
from pathlib import Path


def _write_transcript(path: Path, lines: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(ln) for ln in lines) + "\n", encoding="utf-8"
    )


def test_AC_M_5_recovers_user_and_assistant_from_nested_message_shape(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Claude Code current shape: ``{"type": "user"|"assistant",
    "message": {"role": ..., "content": ...}}``."""
    transcript = tmp_path / "tx.jsonl"
    _write_transcript(
        transcript,
        [
            {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": "what's the workspace working on?",
                },
            },
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "rebuilding pos-v2."}
                    ],
                },
            },
        ],
    )
    captured: dict = {}

    def _capture_spawn(**kw):
        captured.update(kw)

    import loam.primary_persona.stop_emitter as se

    monkeypatch.setattr(se, "_spawn_memory_write", _capture_spawn)
    envelope = json.dumps(
        {
            "session_id": "s-nested",
            "transcript_path": str(transcript),
            "stop_hook_active": False,
        }
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(envelope))
    from loam.primary_persona.stop_emitter import cli_stop

    rc = cli_stop(workspace_root=tmp_path)
    assert rc == 0
    assert captured["user_message"] == "what's the workspace working on?"
    assert captured["assistant_reply"] == "rebuilding pos-v2."
    assert captured["session_id"] == "s-nested"
    assert captured["turn_id"].startswith("s-nested:")


def test_AC_M_5_recovers_user_and_assistant_from_flat_role_shape(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Variant transcript shape: ``{"role": ..., "content": ...}``."""
    transcript = tmp_path / "tx.jsonl"
    _write_transcript(
        transcript,
        [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ],
    )
    captured: dict = {}
    import loam.primary_persona.stop_emitter as se

    monkeypatch.setattr(
        se, "_spawn_memory_write", lambda **kw: captured.update(kw)
    )
    envelope = json.dumps(
        {"session_id": "s-flat", "transcript_path": str(transcript)}
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(envelope))
    from loam.primary_persona.stop_emitter import cli_stop

    cli_stop(workspace_root=tmp_path)
    assert captured["user_message"] == "hi"
    assert captured["assistant_reply"] == "hello"


def test_AC_M_5_recovers_most_recent_pair_when_transcript_carries_history(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """The handler picks the LATEST assistant reply and its preceding
    user message — historical pairs in the transcript are ignored."""
    transcript = tmp_path / "tx.jsonl"
    _write_transcript(
        transcript,
        [
            {"role": "user", "content": "old user"},
            {"role": "assistant", "content": "old reply"},
            {"role": "user", "content": "fresh user"},
            {"role": "assistant", "content": "fresh reply"},
        ],
    )
    captured: dict = {}
    import loam.primary_persona.stop_emitter as se

    monkeypatch.setattr(
        se, "_spawn_memory_write", lambda **kw: captured.update(kw)
    )
    envelope = json.dumps(
        {"session_id": "s-hist", "transcript_path": str(transcript)}
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(envelope))
    from loam.primary_persona.stop_emitter import cli_stop

    cli_stop(workspace_root=tmp_path)
    assert captured["user_message"] == "fresh user"
    assert captured["assistant_reply"] == "fresh reply"


def test_AC_M_5_turn_id_is_stable_across_calls_for_same_user_message(
    tmp_path: Path,
) -> None:
    """``derive_turn_id`` is pure: same (session_id, user_message)
    yields the same id. AC.M.8's dedupe leans on this."""
    from loam.primary_persona.stop_emitter import derive_turn_id

    a = derive_turn_id(session_id="s1", user_message="hello")
    b = derive_turn_id(session_id="s1", user_message="hello")
    c = derive_turn_id(session_id="s1", user_message="different")
    assert a == b
    assert a != c
    # Format check: <session_id>:<12-hex-chars>
    sess, _, hashpart = a.partition(":")
    assert sess == "s1"
    assert len(hashpart) == 12
