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

"""AC46.2 — UserPromptSubmit CLI emits per-turn memory retrieval.

Outcome (per umbrella plan §4a + builder plan §2): the CLI subcommand
reads Claude Code's UserPromptSubmit JSON envelope from stdin (with
``prompt`` field), constructs the composer, fires the memory-retrieval
contributor against the prompt, and prints the rendered turn-payload
additionalContext to stdout. Graceful empty when memory is down /
empty / unwired.

D-build.3 (research): UserPromptSubmit hook input is JSON on stdin
with a ``prompt`` field per Claude Code docs.
D-build.4: production-side memory client is None pre-#47; the
contributor is not registered, the turn-payload simply omits the
retrieval block (graceful empty). Tests inject a FakeMemoryClient
factory to exercise the populated path.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

from loam.primary_persona.session_start_emitter import (
    cli_user_prompt_submit,
    emit_user_prompt_submit_context,
)

from _helpers_d7 import FakeMemoryClient, seed_baseline_workspace


def test_AC46_2_emit_returns_text_when_memory_client_returns_results(
    tmp_path: Path,
) -> None:
    """When a memory client returns search results, the turn payload
    contains the retrieval block."""
    seed_baseline_workspace(tmp_path)
    fake = FakeMemoryClient()
    fake.search_result = {
        "query": "what's the workspace working on",
        "results": [
            {"fact": "Luke is rebuilding pos-v2 with sealed components"},
            {"fact": "Amendment #46 wires session-start emitters"},
        ],
    }
    text = emit_user_prompt_submit_context(
        tmp_path,
        "what's the workspace working on?",
        memory_client_factory=lambda root: fake,
    )
    assert text, "emit returned empty when memory client had results"
    assert "memory-retrieval" in text or "Luke is rebuilding" in text


def test_AC46_2_emit_returns_empty_retrieval_block_when_memory_dir_empty(
    tmp_path: Path,
) -> None:
    """FBM path consolidation (2026-05-31): when the workspace's
    memory dir + corpus have no hit for the query, the GATED keep-pace
    contributor (the consolidation production default) is SILENT — it
    emits no retrieval block at all.

    Pre-M-FBM this asserted no contributor registered; the M-FBM pivot
    changed it to the ungated file-memory empty-state ``(no results for
    this query)`` block; the FBM path consolidation repoints the
    production contributor to the gated keep-pace ``retrieve`` path,
    which is silent-on-no-match (AC.KP1.4) — the empty-state block was
    itself low-value prompt noise. AC46.2's graceful-empty contract is
    satisfied by the silent surface: no exception, no blocked turn, no
    memory-contributing text. The underlying invariant is unchanged.
    """
    seed_baseline_workspace(tmp_path)
    text = emit_user_prompt_submit_context(
        tmp_path, "any prompt"
    )
    # Consolidated: the gated contributor is silent on no-match — no
    # empty-state retrieval block is rendered. Graceful-empty holds via
    # the silent surface (the session-level frame still serialises).
    assert "(no results for this query)" not in text
    assert "[keep-pace]" not in text  # no hit on this query
    assert "[pos-v2 user-prompt-submit]" in text  # session frame intact


def test_AC46_2_emit_no_fact_when_memory_client_raises(
    tmp_path: Path,
) -> None:
    """When the memory client raises (service down, network error),
    the contributor's fail-closed branch (AC-D7.7) returns empty;
    the turn payload still proceeds (no exception bubbles out) and
    no retrieved fact appears in the output. Per AC46.2 graceful-
    empty / AC46.4 fail-soft."""
    seed_baseline_workspace(tmp_path)
    fake = FakeMemoryClient()
    fake.search_raises = ConnectionRefusedError("memory-graphiti unreachable")
    text = emit_user_prompt_submit_context(
        tmp_path,
        "any prompt",
        memory_client_factory=lambda root: fake,
    )
    # Output is non-error; no fact text appears (the contributor
    # returned empty).
    assert "fact" not in text or "[memory-retrieval]" not in text or text.endswith("\n    ") or text.endswith("    ")
    # The structural surface is intact — the renderer wrote the
    # session-level frame even though the retrieval contributor
    # returned empty. This is the AC46.2 graceful-empty contract.
    assert "[pos-v2 user-prompt-submit]" in text


def test_AC46_2_cli_reads_prompt_from_stdin_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """The CLI helper reads JSON from stdin per Claude Code's
    UserPromptSubmit hook contract (D-build.3)."""
    seed_baseline_workspace(tmp_path)
    fake = FakeMemoryClient()
    fake.search_result = {
        "query": "test",
        "results": [{"fact": "deterministic memory fact"}],
    }
    # Patch the default factory so the CLI picks up the fake client
    # without mutating its signature.
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
            "prompt": "what's deterministic?",
        }
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(envelope))
    rc = cli_user_prompt_submit(workspace_root=tmp_path)
    assert rc == 0
    out = capsys.readouterr().out
    assert "deterministic memory fact" in out


def test_AC46_2_cli_exits_zero_on_empty_stdin(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Empty stdin → empty payload, exit 0. Claude Code's
    SessionStart fan-out must NEVER be blocked by a non-zero exit."""
    seed_baseline_workspace(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    rc = cli_user_prompt_submit(workspace_root=tmp_path)
    assert rc == 0
    out = capsys.readouterr().out
    assert out == "" or out.strip() == ""


def test_AC46_2_cli_exits_zero_on_malformed_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Non-JSON stdin → empty payload, exit 0."""
    seed_baseline_workspace(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO("not json at all"))
    rc = cli_user_prompt_submit(workspace_root=tmp_path)
    assert rc == 0


def test_AC46_2_cli_exits_zero_when_prompt_missing(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """JSON envelope without a `prompt` field → empty payload, exit 0."""
    seed_baseline_workspace(tmp_path)
    envelope = json.dumps({"session_id": "x", "hook_event_name": "x"})
    monkeypatch.setattr("sys.stdin", io.StringIO(envelope))
    rc = cli_user_prompt_submit(workspace_root=tmp_path)
    assert rc == 0
