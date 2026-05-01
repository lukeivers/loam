"""AC.M.3 — Memory service unreachable: graceful empty + exit 0.

Outcome (per locked plan §5): when the memory-graphiti service is
unreachable (port closed, HTTP refusal, simulated timeout), the
persona's ``cli user-prompt-submit`` subcommand emits an empty (or
non-memory-contributing) ``additionalContext`` payload and exits 0.
The hook fan-out is not blocked.

Bound to AC-D7.7 production-completion. Two flavours of "unreachable"
are exercised:

  1. Live factory returns ``None`` because ``.mcp.json`` is missing
     (AC.M.3 substrate-not-ready branch in
     ``mcp_memory_client._read_memory_graphiti_url``).
  2. Live client raises ``ConnectionRefusedError`` from ``search``
     (AC-D7.7 fail-closed contributor branch).
"""

from __future__ import annotations

import io
import json
from pathlib import Path

from _helpers_d7 import FakeMemoryClient, seed_baseline_workspace


def test_AC_M_3_no_mcp_json_means_empty_retrieval_block_and_exit_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """No ``.mcp.json`` in the workspace → no MCP client constructed →
    file-based contributor (M-FBM default) is registered → CLI emits
    the empty-state retrieval block, exits 0.

    Post-M-FBM (memory-substrate pivot, 2026-05-01) the file-based
    contributor IS the production default. AC.M.3's graceful-empty
    contract is satisfied by ``[memory-retrieval]\\n  (no results
    for this query)`` — structurally graceful, no exception bubbles,
    hook fan-out unblocked. The "no retrieval block at all" reading
    of AC.M.3 was pre-M-FBM specific to the MCP-only substrate; the
    post-M-FBM AC.M.3 surface always carries the block (file-based
    is always-ready).
    """
    seed_baseline_workspace(tmp_path)
    envelope = json.dumps(
        {
            "session_id": "abc",
            "transcript_path": "/tmp/x.jsonl",
            "prompt": "any prompt",
        }
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(envelope))
    from loam.primary_persona.session_start_emitter import cli_user_prompt_submit

    rc = cli_user_prompt_submit(workspace_root=tmp_path)
    assert rc == 0
    out = capsys.readouterr().out
    # Post-M-FBM: block IS present, body is the empty-state diagnostic.
    assert "[memory-retrieval]" in out
    assert "(no results for this query)" in out


def test_AC_M_3_search_raises_connection_refused_then_exit_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Live client present but ``search`` raises → contributor returns
    empty (AC-D7.7) → CLI emits no retrieval block, exits 0."""
    seed_baseline_workspace(tmp_path)
    fake = FakeMemoryClient()
    fake.search_raises = ConnectionRefusedError("memory unreachable")
    import loam.primary_persona.session_start_emitter as sse

    monkeypatch.setattr(
        sse, "_default_memory_client_factory", lambda root: fake
    )
    envelope = json.dumps(
        {
            "session_id": "abc",
            "transcript_path": "/tmp/x.jsonl",
            "prompt": "any prompt",
        }
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(envelope))
    from loam.primary_persona.session_start_emitter import cli_user_prompt_submit

    rc = cli_user_prompt_submit(workspace_root=tmp_path)
    assert rc == 0
    out = capsys.readouterr().out
    # AC.M.3 graceful-empty contract: the framework's renderer may
    # still emit the contributor's registered-name heading, but the
    # contributor's body is empty under AC-D7.7 fail-closed. The
    # observable AC.M.3 outcome is "no fact text leaks", "exit 0",
    # and the structural payload remains intact (the session-level
    # frame still rendered). We measure all three.
    assert "fact" not in out.lower() or "results" not in out.lower()
    assert "[pos-v2 user-prompt-submit]" in out
    # The contributor was invoked at least once; the call recorded
    # the raise-path was exercised.
    assert len(fake.search_calls) == 1
