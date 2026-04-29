"""AC.M.8 — Re-firing Stop on the same turn does not double-write.

Outcome (per locked plan §5 + amendment J §4): given two consecutive
Stop firings whose ``transcript_path`` and last-user-message both
resolve to the same turn (the second firing is a recursive /
``/compact`` / interrupt-replay re-fire), exactly one ``add_episode``
lands at the memory service across both firings.

**Amendment J shape change.** Pre-J the dedupe surface was the
workspace-local ``last-turn-id`` marker file (D4) and the test
asserted exactly one Popen detach per dedupe pass. Post-J the
mechanism is two-line:

  - Line 1: same ``last-turn-id`` marker — a same-turn re-fire
    short-circuits before enqueue (D4 / AC.M.8).
  - Line 2: structural — the queue entry filename is keyed on
    ``turn_id``, so a marker-miss + repeat enqueue overwrites the
    same on-disk entry rather than producing a duplicate
    (amendment J / AC.J.7).

Both lines yield exactly one queue entry per turn. The AC measures
observable count.
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


def _read_queue_entries(workspace_root: Path) -> list[dict[str, Any]]:
    qdir = workspace_root / "workspace" / ".pos" / "memory-write-queue"
    if not qdir.exists():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(qdir.iterdir()):
        if path.is_file() and path.suffix == ".json":
            out.append(json.loads(path.read_text(encoding="utf-8")))
    return out


def _fire_stop(
    monkeypatch, popen_calls: list, transcript: Path, workspace: Path, session_id: str
) -> int:
    monkeypatch.setattr(
        subprocess, "Popen", lambda *a, **k: popen_calls.append((a, k)) or object()
    )
    envelope = json.dumps(
        {
            "session_id": session_id,
            "transcript_path": str(transcript),
            "stop_hook_active": True,  # the field is informational
        }
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(envelope))
    from loam.primary_persona.stop_emitter import cli_stop

    return cli_stop(workspace_root=workspace)


def test_AC_M_8_two_consecutive_stops_same_turn_yield_one_queue_entry(
    tmp_path: Path, monkeypatch
) -> None:
    """Two consecutive Stops with the same (session, user_message)
    produce exactly one queue entry — D4 marker dedupes the second
    fire. AC.J.2 + AC.M.8."""
    transcript = tmp_path / "tx.jsonl"
    _write_transcript(transcript)
    popen_calls: list[Any] = []

    rc1 = _fire_stop(monkeypatch, popen_calls, transcript, tmp_path, "s1")
    rc2 = _fire_stop(monkeypatch, popen_calls, transcript, tmp_path, "s1")

    assert rc1 == 0
    assert rc2 == 0
    # AC.J.7 + AC.M.8: exactly one queue entry exists for this turn.
    entries = _read_queue_entries(tmp_path)
    assert len(entries) == 1, (
        f"expected dedupe to one queue entry; got {len(entries)}"
    )
    # The marker file was written.
    marker = tmp_path / "workspace" / ".pos" / "last-turn-id"
    assert marker.exists()
    assert marker.read_text(encoding="utf-8").strip().startswith("s1:")
    # AC.J.2: no Popen detach pattern in either fire.
    assert popen_calls == []


def test_AC_M_8_distinct_turns_each_enqueue(
    tmp_path: Path, monkeypatch
) -> None:
    """A second Stop for a DIFFERENT user message lands its own queue
    entry — dedupe keys on (session_id, user_message_hash), not
    session-id alone."""
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
    popen_calls: list[Any] = []
    rc1 = _fire_stop(monkeypatch, popen_calls, transcript_a, tmp_path, "s1")
    rc2 = _fire_stop(monkeypatch, popen_calls, transcript_b, tmp_path, "s1")
    assert rc1 == 0 and rc2 == 0
    entries = _read_queue_entries(tmp_path)
    assert len(entries) == 2, (
        f"expected two queue entries (distinct turns); got {len(entries)}"
    )
    user_messages = sorted(e["user_message"] for e in entries)
    assert user_messages == ["first", "second"]


def test_AC_M_8_marker_miss_does_not_double_enqueue(
    tmp_path: Path, monkeypatch
) -> None:
    """AC.J.7 second-line dedupe: even if the workspace-local
    last-turn-id marker is missing (workspace-bootstrap race, marker
    deleted by the operator, etc.), a re-fire for the same turn
    overwrites the same on-disk queue entry — the filename is keyed
    on turn-id, so the queue size is exactly one per turn regardless
    of marker state."""
    transcript = tmp_path / "tx.jsonl"
    _write_transcript(transcript)
    popen_calls: list[Any] = []

    # First fire: lands a queue entry + writes marker.
    rc1 = _fire_stop(monkeypatch, popen_calls, transcript, tmp_path, "s1")
    assert rc1 == 0
    assert len(_read_queue_entries(tmp_path)) == 1

    # Operator-style marker deletion: the marker is best-effort per
    # #48 D4. Removing it simulates a workspace-bootstrap race or a
    # manual reset.
    (tmp_path / "workspace" / ".pos" / "last-turn-id").unlink()

    # Second fire: marker miss → re-enqueue. AC.J.7 says the on-disk
    # filename keyed on turn-id collapses this to ONE entry, not two.
    rc2 = _fire_stop(monkeypatch, popen_calls, transcript, tmp_path, "s1")
    assert rc2 == 0
    entries = _read_queue_entries(tmp_path)
    assert len(entries) == 1, (
        f"AC.J.7 dedupe-by-turn-id-filename violated; got "
        f"{len(entries)} entries"
    )
