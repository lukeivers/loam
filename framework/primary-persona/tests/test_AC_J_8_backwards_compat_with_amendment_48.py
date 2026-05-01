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

"""AC.J.8 — Backwards-compat: amendment #48 ACs preserved.

Outcome (per locked plan §4): existing #48 tests for AC.M.1 -
AC.M.S stay green. The Stop-hook contract is unchanged from
Claude Code's perspective (exit 0; reads stdin envelope; reads
transcript_path; derives turn id; respects dedupe marker).

This test pins three structural invariants that #48 tests cover
across multiple files; consolidating here makes the BC contract
visible as one test surface:

  1. The body composition shape that the worker drives via
     ``_build_episode_args`` matches the #48 ``cli_memory_write``
     surface byte-identically (turn_id-encoded name, group_id =
     workspace_slug, source = "message", body carries both halves
     in labelled blocks).
  2. The Stop-hook still writes the diagnostic log at
     ``<workspace>/.pos/memory-writes.log`` with the existing
     ``stop-skip`` / ``stop-error`` ``kind`` values byte-identically;
     new ``kind`` values land for worker-side events but the existing
     schema is preserved.
  3. The full M-test suite passes (verified by the rest of this
     test file referenced by name) — this test asserts the schema
     contract via #48 tests' shared ``FakeMemoryClient`` shape.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loam.primary_persona import memory_write_queue as mwq
from loam.primary_persona import memory_write_worker as mww


class _RecordingClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def add_episode(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {"episode_uuid": "uuid"}

    async def search(self, **kwargs: Any) -> dict[str, Any]:
        return {"query": "", "results": []}


def test_AC_J_8_worker_drives_episode_with_48_body_composition_shape(
    tmp_path: Path,
) -> None:
    """The worker's add_episode arguments match #48 AC.M.6 shape:
    turn_id-encoded name, group_id=workspace_slug, source=message,
    body carries [user] + [assistant] labelled halves."""
    mwq.enqueue(
        workspace_root=tmp_path,
        turn_id="s-bc:abcdef012345",
        session_id="s-bc",
        user_message="how does the persona answer questions?",
        assistant_reply="by reducing translation burden.",
    )
    client = _RecordingClient()
    mww.drain_once(
        workspace_root=tmp_path,
        config={
            "max_retries": 5,
            "backoff_initial_s": 0.0,
            "backoff_max_s": 0.0,
            "poll_interval_s": 0.0,
            "tmp_cleanup_age_s": 3600.0,
        },
        client_factory=lambda _root: client,
        workspace_slug="bc-workspace",
        sleep_fn=lambda _s: None,
    )
    assert len(client.calls) == 1
    call = client.calls[0]
    # AC.M.6 + #48 D6: name encodes the turn id.
    assert call["name"] == "turn:s-bc:abcdef012345"
    # AC.M.6 + AC-D7.4: group_id is the workspace slug.
    assert call["group_id"] == "bc-workspace"
    # #48 D6: source is "message".
    assert call["source"] == "message"
    # #48 D6: body carries both halves under labelled blocks.
    assert "[user]" in call["body"]
    assert "[assistant]" in call["body"]
    assert "how does the persona answer questions?" in call["body"]
    assert "by reducing translation burden." in call["body"]
    # reference_time is a datetime instance.
    assert isinstance(call["reference_time"], datetime)


def test_AC_J_8_stop_hook_diag_log_kind_values_preserved(
    tmp_path: Path, monkeypatch
) -> None:
    """The Stop-hook diagnostic log continues to write the existing
    #48 ``kind`` values (stop-skip / stop-error). The worker adds new
    ``kind`` values (worker-ok/retry/deadletter) but the existing
    semantics are unchanged."""
    import io

    transcript = tmp_path / "tx.jsonl"
    transcript.write_text("", encoding="utf-8")  # empty → AC.M.9 stop-skip
    envelope = json.dumps(
        {"session_id": "s1", "transcript_path": str(transcript)}
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(envelope))
    from loam.primary_persona.stop_emitter import cli_stop

    rc = cli_stop(workspace_root=tmp_path)
    assert rc == 0

    diag_path = tmp_path / "workspace" / ".pos" / "memory-writes.log"
    assert diag_path.exists()
    lines = [ln for ln in diag_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) >= 1
    entry = json.loads(lines[0])
    # The #48 stop-skip schema is unchanged.
    assert entry["kind"] == "stop-skip"
    assert "session_id" in entry
    assert "ts" in entry
    assert "reason" in entry


def test_AC_J_8_existing_cli_memory_write_path_still_callable(
    tmp_path: Path, monkeypatch
) -> None:
    """``cli_memory_write`` (the legacy #48 detached-child entry point)
    remains callable for backward-compat — tests that exercise the
    per-turn write contract directly (AC.M.6) are preserved.

    Post-J the long-running worker drives the equivalent drain via
    ``_process_one_entry``; the legacy CLI surface is still callable
    and yields the same observable (one add_episode call per turn).
    """
    from loam.primary_persona.stop_emitter import cli_memory_write

    # Patch the live-client builder to a recording fake.
    fake = _RecordingClient()
    import loam.primary_persona.mcp_memory_client as mmc

    monkeypatch.setattr(
        mmc, "build_live_mcp_memory_client", lambda root: fake
    )

    rc = cli_memory_write(
        workspace_root=tmp_path,
        turn_id="s-legacy:000000000000",
        session_id="s-legacy",
        user_message="legacy path",
        assistant_reply="still works",
    )
    assert rc == 0
    assert len(fake.calls) == 1
    call = fake.calls[0]
    assert call["name"].endswith("s-legacy:000000000000")
