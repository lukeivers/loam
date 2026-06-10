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

"""AC.LIVI.3 — the fix does NOT regress the predecessor's
persona-IDENTITY binding or the ``_scaffold_persona_binding``
envelope: after the fix, a fresh ``loam init`` still writes
``<ws>/.claude/agents/<handle>.md`` (non-empty, references the handle)
+ ``settings.json`` carrying ``"agent": <handle>`` + both SessionStart
hooks present, exactly as the predecessor sealed — the fix is ADDITIVE
to interpreter resolution, not a rewrite of the binding surface.

Plan: docs/plans/loam-init-framework-venv-or-robust-interpreter.md
Ladders to AC.PO.1.

Verification: assert the predecessor AC.LIPW.{1,3} envelope/identity
invariants still hold on a real fresh bootstrap AFTER the venv-
provisioning fix. The predecessor's own AC.LIPW test suite green in the
same component sweep is the broader no-regression guarantee; this file
pins the specific identity + envelope invariants directly so a
regression in THIS amendment surfaces against THIS amendment's AC.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    DEFAULT_PERSONA_HANDLE,
)

@pytest.fixture(scope="module")
def fresh_init_workspace(
    tmp_path_factory: pytest.TempPathFactory,
    isolated_canonical_clone: Path,
) -> Path:
    # Bootstraps from conftest's isolated_canonical_clone, NOT the real
    # checkout (bootstrapping from the real checkout rewinds its main;
    # see the conftest fixture docstring).
    from loam.workspace_bootstrap.new_workspace import (
        bootstrap_new_workspace,
    )

    base = tmp_path_factory.mktemp("livi3")
    ws = base / "ws"
    bootstrap_new_workspace(
        new_ws_path=ws,
        canonical_source=str(isolated_canonical_clone),
        service_bootstrap=False,
        service_manager_dir_override=base / "LaunchAgents",
    )
    return ws


def test_AC_LIVI_3_agents_file_intact_nonempty_references_handle(
    fresh_init_workspace: Path,
) -> None:
    """Predecessor AC.LIPW.1 invariant preserved: the
    Claude-Code-discoverable agents file is still written, non-empty,
    and references the workspace persona handle."""
    agents_md = (
        fresh_init_workspace
        / ".claude"
        / "agents"
        / f"{DEFAULT_PERSONA_HANDLE}.md"
    )
    assert agents_md.is_file(), (
        f"REGRESSION: identity-binding artefact {agents_md} missing "
        "after the venv-provisioning fix"
    )
    text = agents_md.read_text(encoding="utf-8")
    assert text.strip(), ".claude/agents/<handle>.md is empty"
    assert f"name: {DEFAULT_PERSONA_HANDLE}" in text
    assert "# Persona prompt" in text


def test_AC_LIVI_3_settings_agent_key_intact(
    fresh_init_workspace: Path,
) -> None:
    """Predecessor amendment #37 invariant preserved: settings.json
    still selects the workspace persona as the default agent."""
    settings = json.loads(
        (fresh_init_workspace / ".claude" / "settings.json").read_text(
            encoding="utf-8"
        )
    )
    assert settings.get("agent") == DEFAULT_PERSONA_HANDLE, (
        f"REGRESSION: settings.json 'agent' key is "
        f"{settings.get('agent')!r}, expected {DEFAULT_PERSONA_HANDLE!r}"
    )


def test_AC_LIVI_3_both_sessionstart_hooks_still_present(
    fresh_init_workspace: Path,
) -> None:
    """Predecessor envelope invariant preserved: both SessionStart
    inner hooks (orchestrator supervisor + persona session-start emit)
    are still wired — the fix added the interpreter the hooks resolve
    to; it did NOT remove or rewrite the envelope."""
    settings = json.loads(
        (fresh_init_workspace / ".claude" / "settings.json").read_text(
            encoding="utf-8"
        )
    )
    commands = [
        h["command"]
        for entry in settings["hooks"]["SessionStart"]
        for h in entry["hooks"]
    ]
    joined = " || ".join(commands)
    assert "pos_session_start.py" in joined, (
        f"REGRESSION: orchestrator supervisor hook missing; "
        f"commands={commands}"
    )
    assert "primary_persona.cli session-start" in joined, (
        f"REGRESSION: persona session-start emit hook missing; "
        f"commands={commands}"
    )


def test_AC_LIVI_3_custom_handle_still_binds(
    tmp_path_factory: pytest.TempPathFactory,
    isolated_canonical_clone: Path,
) -> None:
    """Predecessor AC.LIPW.1 custom-handle invariant preserved under
    the fix (a non-default persona handle still binds + provisions)."""
    from loam.workspace_bootstrap.new_workspace import (
        bootstrap_new_workspace,
    )

    base = tmp_path_factory.mktemp("livi3-iris")
    ws = base / "ws"
    bootstrap_new_workspace(
        new_ws_path=ws,
        canonical_source=str(isolated_canonical_clone),
        persona_handle="iris",
        service_bootstrap=False,
        service_manager_dir_override=base / "LaunchAgents",
    )
    agents_md = ws / ".claude" / "agents" / "iris.md"
    assert agents_md.is_file() and agents_md.read_text().strip()
    settings = json.loads(
        (ws / ".claude" / "settings.json").read_text(encoding="utf-8")
    )
    assert settings.get("agent") == "iris"
    # And the fix's invariant holds for the custom handle too.
    assert (ws / "framework" / ".venv" / "bin" / "python").is_file()
