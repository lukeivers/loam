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

"""AC46.3 — Missing-corpus structured diagnostic + sentinel.

Outcome: on a workspace with one or more baseline-corpus files absent,
``emit_session_start_context`` produces a payload whose:

  - ``corpus_gate_state`` sentinel is ``partial`` or ``missing``
    (depending on absence count)
  - serialised text names the missing paths (structured diagnostic)
  - both CLIs (session-start, user-prompt-submit) exit 0

The composer / session-builder produce these structurally — this test
exercises the runtime emit surface and confirms the diagnostic + the
sentinel reach the rendered text.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

from loam.primary_persona.session_start_emitter import (
    cli_session_start,
    cli_user_prompt_submit,
    emit_session_start_context,
)


def _seed_partial_workspace(root: Path) -> None:
    """Workspace with CLAUDE.md present but every baseline corpus file
    absent — sentinel should land at ``partial`` (CLAUDE.md present
    but the listed files are missing)."""
    (root / "CLAUDE.md").write_text(
        "# test workspace\n\n"
        "## Session-start discipline\n\n"
        "- `docs/odd-methodology.md`\n"
        "- `docs/odd-in-loam.md`\n"
        "\n---\n\n"
    )


def _seed_missing_workspace(root: Path) -> None:
    """Workspace with NO baseline files at all (CLAUDE.md absent;
    fallback list activates; every fallback path is missing).
    Sentinel should land at ``missing``."""
    # Don't write CLAUDE.md or any docs; the gate falls back to its
    # built-in baseline list and reports every path missing.
    pass


def test_AC46_3_partial_sentinel_when_some_corpus_present(
    tmp_path: Path,
) -> None:
    """Sentinel is ``partial`` when CLAUDE.md is present but listed
    files are absent."""
    _seed_partial_workspace(tmp_path)
    text = emit_session_start_context(tmp_path)
    assert text, "emit returned empty on partial corpus"
    assert "corpus_gate_state: partial" in text


def test_AC46_3_missing_paths_named_in_diagnostic(tmp_path: Path) -> None:
    """The serialised payload names the missing paths in a
    structured diagnostic block."""
    _seed_partial_workspace(tmp_path)
    text = emit_session_start_context(tmp_path)
    assert "missing_corpus_paths" in text or "MISSING" in text
    # The two listed paths are missing; both should be named.
    assert "docs/odd-methodology.md" in text
    assert "docs/odd-in-loam.md" in text


def test_AC46_3_missing_sentinel_when_no_corpus_present(
    tmp_path: Path,
) -> None:
    """Sentinel is ``missing`` when no baseline corpus file is
    present (CLAUDE.md absent → fallback list, every fallback path
    missing too)."""
    _seed_missing_workspace(tmp_path)
    text = emit_session_start_context(tmp_path)
    assert text, "emit returned empty on missing corpus"
    assert "corpus_gate_state: missing" in text


def test_AC46_3_session_start_cli_exits_zero_on_missing_corpus(
    tmp_path: Path,
) -> None:
    """session-start CLI exits 0 even when corpus is absent."""
    _seed_partial_workspace(tmp_path)
    rc = cli_session_start(workspace_root=tmp_path)
    assert rc == 0


def test_AC46_3_user_prompt_submit_cli_exits_zero_on_missing_corpus(
    tmp_path: Path, monkeypatch
) -> None:
    """user-prompt-submit CLI exits 0 even when corpus is absent."""
    _seed_partial_workspace(tmp_path)
    envelope = json.dumps({"prompt": "test"})
    monkeypatch.setattr("sys.stdin", io.StringIO(envelope))
    rc = cli_user_prompt_submit(workspace_root=tmp_path)
    assert rc == 0
