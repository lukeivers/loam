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

"""AC.LIPW.3 — the existing post-onboarding write-back contract is
preserved. After a real onboarding grounding capture, the persona
identity is re-rendered from captured grounding exactly as before
this change. Part 1 adds a valid-from-turn-zero binding; it does NOT
regress `persist_grounding`.

Plan: docs/plans/loam-init-persona-wiring-and-isolated-subloam-driver.md
Ladders to AC.PO.1.

Verification:
  - Part 1's binding renders a placeholder identity from turn zero.
  - A subsequent `persist_grounding` (real onboarding) OVERWRITES the
    bound surface with the captured-grounding identity — the
    placeholder is gone, the captured names are present.
  - `persist_grounding` is imported + driven unchanged (no source
    edit to the amendment #50 onboarding write-back path).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from loam.primary_persona.contract import PersonaContract
from loam.primary_persona.loader import PersonaLoader
from loam.primary_persona.onboarding import (
    GroundingCapture,
    persist_grounding,
)

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    DEFAULT_PERSONA_HANDLE,
    run_first_run_scaffold,
)
from loam.workspace_bootstrap.new_workspace import (
    _scaffold_persona_binding,
)

LOAM_ROOT = Path(__file__).resolve().parents[3]


@dataclass
class _LoadedPersona:
    contract: PersonaContract
    directory: Path | None = None


def _scaffold_bind_then_ground(tmp_path: Path) -> Path:
    """Scaffold + Part-1 bind (placeholder identity), then run a real
    persist_grounding over the just-scaffolded starter persona."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    run_first_run_scaffold(
        pos_root=tmp_path / ".pos",
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=tmp_path / "LaunchAgents",
        workspace_root=workspace,
        persona_handle=DEFAULT_PERSONA_HANDLE,
    )
    _scaffold_persona_binding(
        workspace_root=workspace,
        handle=DEFAULT_PERSONA_HANDLE,
        loam_root=LOAM_ROOT,
    )
    agent_md = (
        workspace / ".claude" / "agents" / f"{DEFAULT_PERSONA_HANDLE}.md"
    )
    placeholder_bound = agent_md.read_text()
    # Sanity: the from-turn-zero binding is the placeholder identity
    # (not yet a real captured name).
    assert "Mara" not in placeholder_bound

    # Drive the real onboarding write-back over the scaffolded
    # starter persona (loader resolves the just-scaffolded contract).
    loaded = PersonaLoader(workspace_root=workspace).load()[0]
    persona = _LoadedPersona(
        contract=loaded.contract, directory=loaded.directory
    )
    persist_grounding(
        loaded_persona=persona,
        grounding=GroundingCapture(
            user_preferred_name="Luke",
            persona_given_name="Mara",
            single_point_of_contact="Coordinator for daily ops.",
            context_holder="Holds cross-session context.",
            escalation_judge="Routes irreversible moves.",
            dev_intent="no",
            captured_summary=("Heard about the day-walkthrough.",),
        ),
        contract_path=loaded.directory / "contract.yaml",
    )
    return agent_md


def test_AC_LIPW_3_persist_grounding_overwrites_placeholder_binding(
    tmp_path: Path,
) -> None:
    """After real onboarding, the bound surface reflects captured
    grounding (the placeholder identity is replaced — no regression
    to the #50 write-back contract)."""
    agent_md = _scaffold_bind_then_ground(tmp_path)
    body = agent_md.read_text()
    assert "Mara" in body, (
        "persist_grounding did not re-render the captured given_name "
        "over Part 1's placeholder binding — REGRESSION"
    )
    assert "{user_preferred_name}" not in body
    assert "{persona_given_name}" not in body


def test_AC_LIPW_3_contract_flips_is_starter_false_post_grounding(
    tmp_path: Path,
) -> None:
    """`persist_grounding`'s contract write-back (is_starter -> False)
    is unaffected by Part 1's from-turn-zero binding."""
    agent_md = _scaffold_bind_then_ground(tmp_path)
    workspace = agent_md.parents[2]
    reloaded = PersonaLoader(workspace_root=workspace).load()[0]
    assert reloaded.contract.is_starter is False
