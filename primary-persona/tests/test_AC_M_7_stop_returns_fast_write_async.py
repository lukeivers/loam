"""AC.M.7 — Stop-hook returns in milliseconds; write completes async.

Outcome (per locked plan §5 + amendment J §4): the Stop-hook
subprocess returns (exit 0) within 200ms p95, independent of the
memory service's ``add_episode`` cost. The actual write completes
in a long-running worker process whose lifetime is independent of
the Stop subprocess.

**Amendment J shape change.** Pre-J the Stop hook detached a
per-turn ``subprocess.Popen`` child to drive the write; post-J it
enqueues a turn record under
``<workspace>/.pos/memory-write-queue/`` and returns. The actual
write runs out-of-band in a launchd-supervised worker
(``com.pos-v2.<slug>.memory-write-worker``).

This test asserts the post-J outcome:

  - cli_stop returns within the latency budget,
  - the queue directory contains exactly one entry whose payload
    carries the recovered turn content,
  - no detached subprocess was spawned (the per-turn Popen pattern
    is retired by amendment J / AC.J.2).

Pre-amendment-J Popen monkeypatch shape was method-coupled to the
detach implementation; AC.M.7's outcome — "returns fast, write
happens off-process" — is unchanged. AC.J.2 tightens the same
outcome with a structurally-different mechanism.
"""

from __future__ import annotations

import io
import json
import subprocess
import time
from pathlib import Path
from typing import Any


def _write_transcript(path: Path) -> None:
    path.write_text(
        json.dumps({"role": "user", "content": "fast"}) + "\n"
        + json.dumps({"role": "assistant", "content": "ok"}) + "\n",
        encoding="utf-8",
    )


def _read_queue_entries(workspace_root: Path) -> list[dict[str, Any]]:
    qdir = workspace_root / ".pos" / "memory-write-queue"
    if not qdir.exists():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(qdir.iterdir()):
        if path.is_file() and path.suffix == ".json":
            out.append(json.loads(path.read_text(encoding="utf-8")))
    return out


def test_AC_M_7_cli_stop_returns_under_200ms_and_enqueues(
    tmp_path: Path, monkeypatch
) -> None:
    """cli_stop returns fast (≤200ms) AND lands a queue entry whose
    payload carries the recovered turn content. AC.J.2 outcome:
    Stop-hook is no-block; write happens off-process."""
    transcript = tmp_path / "tx.jsonl"
    _write_transcript(transcript)

    # Track Popen calls to assert the post-J shape: NO detached
    # subprocess is spawned by the Stop hook (amendment J / AC.J.2
    # replaces the per-turn detach with a queue write).
    popen_calls: list[Any] = []
    monkeypatch.setattr(
        subprocess, "Popen", lambda *a, **k: popen_calls.append((a, k)) or object()
    )

    envelope = json.dumps(
        {
            "session_id": "s-fast",
            "transcript_path": str(transcript),
            "stop_hook_active": False,
        }
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(envelope))
    from src.stop_emitter import cli_stop

    started = time.monotonic()
    rc = cli_stop(workspace_root=tmp_path)
    elapsed_ms = (time.monotonic() - started) * 1000.0

    assert rc == 0
    assert elapsed_ms < 200.0, (
        f"cli_stop took {elapsed_ms:.1f}ms (budget 200ms)"
    )

    # AC.J.2 + AC.J.3: exactly one queue entry landed.
    entries = _read_queue_entries(tmp_path)
    assert len(entries) == 1, (
        f"expected exactly one queue entry; got {len(entries)}"
    )
    record = entries[0]
    assert record["session_id"] == "s-fast"
    assert record["user_message"] == "fast"
    assert record["assistant_reply"] == "ok"
    assert record["turn_id"].startswith("s-fast:")
    assert record["retry_count"] == 0

    # AC.J.2: the per-turn subprocess.Popen detach pattern is
    # retired. The Stop hook does NOT spawn anything.
    assert popen_calls == [], (
        "amendment J / AC.J.2 retires the per-turn Popen detach; "
        f"got {len(popen_calls)} unexpected Popen calls"
    )


def test_AC_M_7_skipped_paths_do_not_enqueue(
    tmp_path: Path, monkeypatch
) -> None:
    """When the transcript walk yields empty content, no queue entry
    lands. AC.M.7's "fast" guarantee is trivially met when zero work
    happens; AC.M.9 covers the no-op contract."""
    transcript = tmp_path / "tx.jsonl"
    transcript.write_text("", encoding="utf-8")

    popen_calls: list[Any] = []
    monkeypatch.setattr(
        subprocess, "Popen", lambda *a, **k: popen_calls.append((a, k)) or object()
    )

    envelope = json.dumps(
        {"session_id": "s", "transcript_path": str(transcript)}
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(envelope))
    from src.stop_emitter import cli_stop

    rc = cli_stop(workspace_root=tmp_path)
    assert rc == 0
    assert popen_calls == []
    assert _read_queue_entries(tmp_path) == []
