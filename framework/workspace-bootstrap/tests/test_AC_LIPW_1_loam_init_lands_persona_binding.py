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

"""AC.LIPW.1 — a fresh `loam init` (no onboarding, no manual hook
install) carries a primary-persona binding surface Claude Code reads
at session start, such that an interactive `claude` session opened in
the workspace has the workspace's primary persona active on the first
user turn.

Plan: docs/plans/loam-init-persona-wiring-and-isolated-subloam-driver.md
Ladders to AC.PO.1 (translation-burden — a first-run workspace with a
dead persona is the maximal translation-burden failure).

Verification (outcome-shape; method is the builder's call):
  - Automated: drive the production scaffold path; assert a
    Claude-Code-discoverable persona-binding artefact exists +
    non-empty + references the workspace persona handle.
  - The bound surface is BOTH `.claude/agents/<handle>.md` (subagent
    discovery) AND the settings.json top-level `"agent": <handle>`
    key (amendment #37 — a fresh Claude Code session selects the
    workspace persona as its default agent => persona active turn
    one) + the SessionStart envelope carrying the persona emit.
"""

from __future__ import annotations

import json
from pathlib import Path

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    DEFAULT_PERSONA_HANDLE,
    run_first_run_scaffold,
)
from loam.workspace_bootstrap.new_workspace import (
    _scaffold_persona_binding,
)

LOAM_ROOT = Path(__file__).resolve().parents[3]


def _scaffold_and_bind(
    *, tmp_path: Path, handle: str = DEFAULT_PERSONA_HANDLE
) -> Path:
    """Run the production scaffold then the persona-binding extension
    (mirrors bootstrap_new_workspace's call site exactly)."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    run_first_run_scaffold(
        pos_root=tmp_path / ".pos",
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=tmp_path / "LaunchAgents",
        workspace_root=workspace,
        persona_handle=handle,
    )
    wrote = _scaffold_persona_binding(
        workspace_root=workspace, handle=handle, loam_root=LOAM_ROOT
    )
    assert wrote is True, "binding extension reported no write"
    return workspace


def test_AC_LIPW_1_agents_file_exists_nonempty_references_handle(
    tmp_path: Path,
) -> None:
    ws = _scaffold_and_bind(tmp_path=tmp_path)
    agents_md = ws / ".claude" / "agents" / f"{DEFAULT_PERSONA_HANDLE}.md"
    assert agents_md.exists(), f"missing binding artefact {agents_md}"
    text = agents_md.read_text()
    assert text.strip(), ".claude/agents/<handle>.md is empty"
    # References the workspace persona handle in the frontmatter.
    assert f"name: {DEFAULT_PERSONA_HANDLE}" in text
    # The persona prompt body is carried (not just a pointer).
    assert "# Persona prompt" in text


def test_AC_LIPW_1_settings_json_selects_persona_as_default_agent(
    tmp_path: Path,
) -> None:
    """The settings.json top-level `"agent"` key is the amendment #37
    surface that makes a fresh Claude Code session select the
    workspace persona as its default agent on turn one."""
    ws = _scaffold_and_bind(tmp_path=tmp_path)
    settings = ws / ".claude" / "settings.json"
    data = json.loads(settings.read_text())
    assert data.get("agent") == DEFAULT_PERSONA_HANDLE, (
        "settings.json must carry the persona handle as the default "
        f"agent; got {data.get('agent')!r}"
    )


def test_AC_LIPW_1_sessionstart_envelope_carries_persona_emit(
    tmp_path: Path,
) -> None:
    """The scaffolded settings.json SessionStart envelope carries the
    persona's session-start emit inner hook (the canonical-dev
    template's proven binding mechanism, now scaffolded — not a
    manual copy)."""
    ws = _scaffold_and_bind(tmp_path=tmp_path)
    data = json.loads((ws / ".claude" / "settings.json").read_text())
    session_start = data["hooks"]["SessionStart"]
    commands = [
        h["command"]
        for entry in session_start
        for h in entry["hooks"]
    ]
    assert any(
        "primary_persona.cli session-start" in c for c in commands
    ), f"persona session-start emit not wired; commands={commands}"


def test_AC_LIPW_1_custom_handle_binds(tmp_path: Path) -> None:
    ws = _scaffold_and_bind(tmp_path=tmp_path, handle="iris")
    agents_md = ws / ".claude" / "agents" / "iris.md"
    assert agents_md.exists() and agents_md.read_text().strip()
    data = json.loads((ws / ".claude" / "settings.json").read_text())
    assert data.get("agent") == "iris"
