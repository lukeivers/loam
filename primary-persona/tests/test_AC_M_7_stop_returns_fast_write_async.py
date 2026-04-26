"""AC.M.7 — Stop-hook returns in milliseconds; write completes async.

Outcome (per locked plan §5): the Stop-hook subprocess returns
(exit 0) within 200ms p95, independent of the memory service's
``add_episode`` cost. The actual write completes in a detached
background process whose lifetime is independent of the Stop
subprocess.

D3 detachment shape: ``subprocess.Popen(..., start_new_session=True,
stdin/stdout/stderr=DEVNULL)``. We monkeypatch ``subprocess.Popen``
to a recording stub so the test does not actually fork; we assert:

  - cli_stop returns within the latency budget,
  - exactly one Popen call landed on the spawn_memory_write path,
  - it carried ``start_new_session=True`` and the DEVNULL streams.
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


def test_AC_M_7_cli_stop_returns_under_200ms_with_recording_popen(
    tmp_path: Path, monkeypatch
) -> None:
    transcript = tmp_path / "tx.jsonl"
    _write_transcript(transcript)

    calls: list[dict[str, Any]] = []

    class _RecorderPopen:
        def __init__(self, args, **kwargs):
            calls.append({"args": args, **kwargs})

    monkeypatch.setattr(subprocess, "Popen", _RecorderPopen)

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
    assert len(calls) == 1, "expected exactly one Popen detach call"
    assert calls[0]["start_new_session"] is True
    assert calls[0]["stdin"] == subprocess.DEVNULL
    assert calls[0]["stdout"] == subprocess.DEVNULL
    assert calls[0]["stderr"] == subprocess.DEVNULL
    args = calls[0]["args"]
    # The detached child invokes the persona CLI's memory-write
    # subcommand under the same Python interpreter.
    assert args[1:4] == ["-m", "primary_persona.cli", "memory-write"]


def test_AC_M_7_skipped_paths_do_not_spawn(
    tmp_path: Path, monkeypatch
) -> None:
    """When the transcript walk yields empty content, no Popen is
    invoked. AC.M.7's "fast" guarantee is trivially met when zero
    work happens; AC.M.9 covers the no-op contract."""
    transcript = tmp_path / "tx.jsonl"
    transcript.write_text("", encoding="utf-8")

    calls: list[Any] = []
    monkeypatch.setattr(
        subprocess, "Popen", lambda *a, **k: calls.append((a, k)) or object()
    )

    envelope = json.dumps(
        {"session_id": "s", "transcript_path": str(transcript)}
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(envelope))
    from src.stop_emitter import cli_stop

    rc = cli_stop(workspace_root=tmp_path)
    assert rc == 0
    assert calls == []
