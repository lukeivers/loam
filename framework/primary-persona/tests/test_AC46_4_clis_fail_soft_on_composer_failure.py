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

"""AC46.4 — CLIs are fail-soft on composer-construction failure.

Outcome: when the composer fails to construct (e.g., session-builder
raises, contributor registration raises, persona contract malformed),
both CLIs:

  - print either an empty payload OR a single diagnostic line
  - exit 0
  - do NOT raise
  - do NOT print a Python traceback to stdout

A non-zero exit would block Claude Code's hook fan-out; this is the
load-bearing fail-soft contract.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from loam.primary_persona.session_start_emitter import (
    cli_session_start,
    cli_user_prompt_submit,
    emit_session_start_context,
    emit_user_prompt_submit_context,
)


def _seed_invalid_workspace_with_unloadable_persona(root: Path) -> None:
    """Workspace whose personas/<handle>/contract.yaml is malformed
    so the loader raises ``PersonaValidationError``; the emitter must
    fail-soft (skip starter-pending registration) and proceed."""
    (root / "CLAUDE.md").write_text(
        "## Session-start discipline\n- `docs/odd-methodology.md`\n"
    )
    (root / "docs").mkdir()
    (root / "docs" / "odd-methodology.md").write_text("x")
    personas = root / "personas"
    personas.mkdir()
    bad = personas / "primary"
    bad.mkdir()
    (bad / "contract.yaml").write_text("not: { valid: yaml: at all : :\n")
    (bad / "prompt.md").write_text("# x\n")


def test_AC46_4_emit_returns_string_when_persona_unloadable(
    tmp_path: Path,
) -> None:
    """Malformed persona contract → starter-pending skipped, emit
    proceeds, returns a non-empty payload string."""
    _seed_invalid_workspace_with_unloadable_persona(tmp_path)
    text = emit_session_start_context(tmp_path)
    # Either non-empty (other contributors / session fields land) OR
    # empty (full-stop fail-soft) — both satisfy AC46.4. The contract
    # is "doesn't raise".
    assert isinstance(text, str)


def test_AC46_4_session_start_cli_exits_zero_on_persona_failure(
    tmp_path: Path,
) -> None:
    """session-start CLI exits 0 on persona-load failure."""
    _seed_invalid_workspace_with_unloadable_persona(tmp_path)
    rc = cli_session_start(workspace_root=tmp_path)
    assert rc == 0


def test_AC46_4_user_prompt_submit_cli_exits_zero_on_persona_failure(
    tmp_path: Path, monkeypatch
) -> None:
    """user-prompt-submit CLI exits 0 on persona-load failure."""
    _seed_invalid_workspace_with_unloadable_persona(tmp_path)
    envelope = json.dumps({"prompt": "test"})
    monkeypatch.setattr("sys.stdin", io.StringIO(envelope))
    rc = cli_user_prompt_submit(workspace_root=tmp_path)
    assert rc == 0


def test_AC46_4_session_start_cli_no_traceback_on_session_builder_raise(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """When the session-builder itself raises, the emit returns empty
    and the CLI prints nothing (no traceback)."""
    # Patch compose_session_fields to raise.
    import loam.primary_persona.session_start_emitter as sse

    def boom(workspace_root: Path):
        raise RuntimeError("synthetic session-builder failure")

    monkeypatch.setattr(sse, "compose_session_fields", boom)
    text = sse.emit_session_start_context(tmp_path)
    assert text == ""
    rc = sse.cli_session_start(workspace_root=tmp_path)
    assert rc == 0
    captured = capsys.readouterr()
    assert "Traceback" not in captured.out
    assert "RuntimeError" not in captured.out
    assert "synthetic" not in captured.out


def test_AC46_4_user_prompt_submit_cli_no_traceback_on_failure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """When emit_user_prompt_submit_context's underlying surface
    raises, the CLI prints nothing and exits 0 — no traceback."""
    import loam.primary_persona.session_start_emitter as sse

    def boom(workspace_root: Path):
        raise RuntimeError("synthetic failure")

    monkeypatch.setattr(sse, "compose_session_fields", boom)
    envelope = json.dumps({"prompt": "test"})
    monkeypatch.setattr("sys.stdin", io.StringIO(envelope))
    rc = sse.cli_user_prompt_submit(workspace_root=tmp_path)
    assert rc == 0
    captured = capsys.readouterr()
    assert "Traceback" not in captured.out


def test_AC46_4_clis_never_raise(tmp_path: Path, monkeypatch) -> None:
    """Both CLIs swallow every exception class via the outer
    fail-soft envelope."""
    # Pathological workspace_root — a file, not a directory.
    bad = tmp_path / "not-a-directory"
    bad.write_text("x")
    rc1 = cli_session_start(workspace_root=bad)
    assert rc1 == 0
    monkeypatch.setattr("sys.stdin", io.StringIO('{"prompt": "x"}'))
    rc2 = cli_user_prompt_submit(workspace_root=bad)
    assert rc2 == 0
