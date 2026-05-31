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
    the GATED keep-pace turn contributor (FBM path-consolidation default)
    is registered → on a no-match query it is SILENT (emits no block);
    the CLI exits 0 and blocks nothing.

    FBM path consolidation (2026-05-31) repointed the production
    memory-retrieval contributor from the ungated file-memory path (which
    always rendered an empty-state ``[memory-retrieval]\\n  (no results
    for this query)`` block) to the gated keep-pace ``retrieve`` path,
    which is SILENT-on-no-match (AC.KP1.4) — the empty-state diagnostic
    block was itself low-value prompt noise. AC.M.3's graceful-empty
    contract is satisfied by the silent surface: exit 0, no exception,
    hook fan-out unblocked, no memory-contributing text. This matches the
    ORIGINAL AC.M.3 wording ("empty or non-memory-contributing payload");
    the intervening M-FBM empty-block reading is superseded.
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
    # Consolidated: the gated contributor is silent on no-match — no
    # retrieval block is rendered (no empty-state noise in the prompt).
    # The graceful-empty invariant holds: exit 0, no exception bubbled,
    # no memory-contributing text.
    assert "(no results for this query)" not in out
    assert "[keep-pace]" not in out  # no episode/corpus hit on this query


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
