"""AC.M.8 — Re-firing Stop on the same turn does not double-write.

Outcome (per locked plan §5): given two consecutive Stop firings whose
``transcript_path`` and last-user-message both resolve to the same
turn (the second firing is a recursive / ``/compact`` /
interrupt-replay re-fire), exactly one ``add_episode`` lands at the
memory service across both firings. Dedupe mechanism is method
(D4: workspace-local ``<workspace>/.pos/last-turn-id`` marker); the
AC measures observable count.
"""

from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path
from typing import Any


def _write_transcript(path: Path) -> None:
    path.write_text(
        json.dumps({"role": "user", "content": "same prompt"}) + "\n"
        + json.dumps({"role": "assistant", "content": "ok"}) + "\n",
        encoding="utf-8",
    )


def _fire_stop(monkeypatch, calls: list, transcript: Path, workspace: Path, session_id: str) -> int:
    class _RecorderPopen:
        def __init__(self, args, **kwargs):
            calls.append({"args": args, **kwargs})

    monkeypatch.setattr(subprocess, "Popen", _RecorderPopen)
    envelope = json.dumps(
        {
            "session_id": session_id,
            "transcript_path": str(transcript),
            "stop_hook_active": True,  # the field is informational
        }
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(envelope))
    from src.stop_emitter import cli_stop

    return cli_stop(workspace_root=workspace)


def test_AC_M_8_two_consecutive_stops_same_turn_yield_one_spawn(
    tmp_path: Path, monkeypatch
) -> None:
    transcript = tmp_path / "tx.jsonl"
    _write_transcript(transcript)
    spawn_calls: list[dict[str, Any]] = []

    rc1 = _fire_stop(monkeypatch, spawn_calls, transcript, tmp_path, "s1")
    rc2 = _fire_stop(monkeypatch, spawn_calls, transcript, tmp_path, "s1")

    assert rc1 == 0
    assert rc2 == 0
    assert len(spawn_calls) == 1, (
        f"expected dedupe to one Popen call; got {len(spawn_calls)}"
    )
    # The marker file was written.
    marker = tmp_path / ".pos" / "last-turn-id"
    assert marker.exists()
    assert marker.read_text(encoding="utf-8").strip().startswith("s1:")


def test_AC_M_8_distinct_turns_each_spawn(
    tmp_path: Path, monkeypatch
) -> None:
    """A second Stop for a DIFFERENT user message should still spawn
    — dedupe keys on (session_id, user_message_hash), not session-id
    alone."""
    transcript_a = tmp_path / "a.jsonl"
    transcript_a.write_text(
        json.dumps({"role": "user", "content": "first"}) + "\n"
        + json.dumps({"role": "assistant", "content": "r1"}) + "\n",
        encoding="utf-8",
    )
    transcript_b = tmp_path / "b.jsonl"
    transcript_b.write_text(
        json.dumps({"role": "user", "content": "second"}) + "\n"
        + json.dumps({"role": "assistant", "content": "r2"}) + "\n",
        encoding="utf-8",
    )
    spawn_calls: list[dict[str, Any]] = []
    rc1 = _fire_stop(monkeypatch, spawn_calls, transcript_a, tmp_path, "s1")
    rc2 = _fire_stop(monkeypatch, spawn_calls, transcript_b, tmp_path, "s1")
    assert rc1 == 0 and rc2 == 0
    assert len(spawn_calls) == 2
