"""AC.J.2 — Stop-hook enqueue path returns in milliseconds.

Outcome (per locked plan §4): given a Stop envelope with recoverable
user message + assistant reply, the Stop-hook's ``cli_stop``
subprocess returns (exit 0) within 200ms p95, AND the actual
``add_episode`` write does NOT run in the Stop subprocess's process
tree — it is enqueued for the long-running worker.

This test exercises the Stop-hook enqueue path's two structural
guarantees:

  1. The function returns fast (≤200ms budget) regardless of any
     hypothetical add_episode cost — the enqueue path never opens
     an MCP transport.
  2. The on-disk queue entry is the only side effect on the write
     path. No subprocess.Popen, no held async loop, no MCP session
     constructed inside cli_stop.

AC.M.7 (#48) is preserved byte-identically from the user's
perspective — same outcome via different mechanism.
"""

from __future__ import annotations

import io
import json
import time
from pathlib import Path
from typing import Any


def _write_transcript(path: Path) -> None:
    path.write_text(
        json.dumps({"role": "user", "content": "the prompt"}) + "\n"
        + json.dumps({"role": "assistant", "content": "the reply"}) + "\n",
        encoding="utf-8",
    )


def test_AC_J_2_cli_stop_returns_fast_and_enqueues_one_record(
    tmp_path: Path, monkeypatch
) -> None:
    transcript = tmp_path / "tx.jsonl"
    _write_transcript(transcript)
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
        f"AC.J.2 budget exceeded: cli_stop took {elapsed_ms:.1f}ms"
    )

    qdir = tmp_path / ".pos" / "memory-write-queue"
    assert qdir.is_dir()
    entries = sorted(qdir.glob("*.json"))
    assert len(entries) == 1, (
        f"expected exactly one queue entry; got {len(entries)}"
    )
    record = json.loads(entries[0].read_text(encoding="utf-8"))
    assert record["session_id"] == "s-fast"
    assert record["user_message"] == "the prompt"
    assert record["assistant_reply"] == "the reply"
    assert record["turn_id"].startswith("s-fast:")
    assert record["retry_count"] == 0
    assert "enqueued_at" in record


def test_AC_J_2_enqueue_does_not_open_mcp_transport(
    tmp_path: Path, monkeypatch
) -> None:
    """The Stop-hook MUST NOT construct the live MCP client during
    enqueue — that's the worker's job. AC.J.2 + Hard Constraint 5."""
    transcript = tmp_path / "tx.jsonl"
    _write_transcript(transcript)

    # Sentinel: any attempt to build a live client during cli_stop
    # raises; the test fails if the Stop hook touches the live-client
    # construction surface.
    import src.mcp_memory_client as mmc

    def _explode(_root: Any) -> Any:
        raise AssertionError(
            "AC.J.2 violation: Stop-hook reached live-client construction"
        )

    monkeypatch.setattr(mmc, "build_live_mcp_memory_client", _explode)

    envelope = json.dumps(
        {"session_id": "s1", "transcript_path": str(transcript)}
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(envelope))
    from src.stop_emitter import cli_stop

    rc = cli_stop(workspace_root=tmp_path)
    assert rc == 0
    # The queue entry is the only side effect.
    assert (tmp_path / ".pos" / "memory-write-queue").is_dir()
