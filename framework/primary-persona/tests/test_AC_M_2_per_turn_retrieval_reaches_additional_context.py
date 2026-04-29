"""AC.M.2 — Per-turn retrieval block reaches additionalContext.

Outcome (per locked plan §5): when the workspace's memory-graphiti
service is reachable AND contains at least one prior episode keyed to
the workspace's slug, the persona's ``cli user-prompt-submit``
subcommand for a crafted prompt that semantically overlaps the
seeded episode emits an ``additionalContext`` payload to stdout
that contains the retrieved episode's fact text.

This is AC-D7.1 production-completion. Pre-#48 the
``_default_memory_client_factory`` returned None; the contributor
was never registered; the turn-payload always omitted the retrieval
block. AC.M.2 measures the post-#48 outcome where the live client
is constructed and the retrieval block lands in stdout.

Determinism: monkeypatch the default factory to return a
``FakeMemoryClient`` configured with a deterministic search result.
The behaviour under test is "the wired-up factory path actually
flows the retrieval into stdout"; the live client's wire-format
conformance is AC.M.1's responsibility.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

from _helpers_d7 import FakeMemoryClient, seed_baseline_workspace


def test_AC_M_2_user_prompt_submit_emits_retrieval_block(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """When the live factory returns a working client carrying a
    seeded episode, the CLI's stdout includes the fact text."""
    seed_baseline_workspace(tmp_path)
    fake = FakeMemoryClient()
    fake.search_result = {
        "query": "what's the workspace working on",
        "results": [
            {
                "fact": "Luke is rebuilding pos-v2 with sealed components",
            }
        ],
    }
    # AC.M.2 measures the production-path factory: monkeypatch
    # _default_memory_client_factory so the CLI picks up the fake
    # without changing its production signature.
    import loam.primary_persona.session_start_emitter as sse

    monkeypatch.setattr(
        sse, "_default_memory_client_factory", lambda root: fake
    )
    envelope = json.dumps(
        {
            "session_id": "abc",
            "transcript_path": "/tmp/x.jsonl",
            "cwd": str(tmp_path),
            "permission_mode": "default",
            "hook_event_name": "UserPromptSubmit",
            "prompt": "what's the workspace working on?",
        }
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(envelope))
    from loam.primary_persona.session_start_emitter import cli_user_prompt_submit

    rc = cli_user_prompt_submit(workspace_root=tmp_path)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Luke is rebuilding pos-v2 with sealed components" in out
    # The search call landed once with the workspace slug as the
    # group_id (AC-D7.4 / AC.M.2 wiring). The slug is the sanitised
    # workspace basename (lowercase, alphanumerics + dashes only).
    from loam.primary_persona.memory_consumer import resolve_workspace_slug

    assert len(fake.search_calls) == 1
    assert fake.search_calls[0].group_ids == [
        resolve_workspace_slug(tmp_path)
    ]
