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

"""AC.O.7 — Workspace scaffold lands the new template content
unchanged at default-handle path.

A workspace bootstrap run via ``run_first_run_scaffold`` against a
tmpfs ``pos_root`` produces ``<workspace>/personas/<handle>/prompt.md``
whose body equals the framework template's ``prompt.md`` body
verbatim (modulo line-endings), and produces a
``<workspace>/personas/<handle>/contract.yaml`` whose parsed content
equals the framework template parsed content with only the
``handle`` field rewritten to the resolved handle and ``is_starter``
flipped to ``True``. No source edit to ``workspace-bootstrap/`` is
required for this AC to pass.

Plan: docs/plans/primary-persona-conversational-onboarding-and-default-archetype.md
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

# workspace_bootstrap is a sibling component; the test imports the
# scaffold runner via its package shape. The component's setup.cfg /
# pyproject installs it to the same .venv used by primary-persona,
# so the import works in the canonical CI environment. If the
# import fails (running primary-persona/tests/ in isolation), the
# test is skipped — this AC depends on cross-component installation
# which is the canonical dev shape.
workspace_bootstrap = pytest.importorskip(
    "loam.workspace_bootstrap.adapters.first_run_scaffold"
)
run_first_run_scaffold = workspace_bootstrap.run_first_run_scaffold
DEFAULT_PERSONA_HANDLE = workspace_bootstrap.DEFAULT_PERSONA_HANDLE


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATE_DIR = (
    REPO_ROOT / "framework" / "primary-persona" / "templates" / "persona-template"
)
TEMPLATE_PROMPT = TEMPLATE_DIR / "prompt.md"
TEMPLATE_CONTRACT = TEMPLATE_DIR / "contract.yaml"


def _run_scaffold(tmp_path: Path):
    pos_root = tmp_path / "pos_root"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return run_first_run_scaffold(
        pos_root=pos_root,
        workspace_root=workspace,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=tmp_path / "agents",
    ), workspace


def test_AC_O_7_scaffold_installs_persona_at_default_handle(tmp_path: Path):
    """The scaffold reports persona_installed=True and the persona
    directory lands at ``<workspace>/personas/<DEFAULT_HANDLE>/``."""
    result, workspace = _run_scaffold(tmp_path)
    assert result.persona_installed is True
    persona_dir = workspace / "workspace" / "personas" / DEFAULT_PERSONA_HANDLE
    assert persona_dir.is_dir()
    assert (persona_dir / "prompt.md").is_file()
    assert (persona_dir / "contract.yaml").is_file()


def test_AC_O_7_workspace_prompt_md_equals_template_body(tmp_path: Path):
    """The workspace's prompt.md body equals the framework
    template's prompt.md body verbatim."""
    _, workspace = _run_scaffold(tmp_path)
    workspace_prompt = (
        workspace / "workspace" / "personas" / DEFAULT_PERSONA_HANDLE / "prompt.md"
    ).read_text()
    template_body = TEMPLATE_PROMPT.read_text()
    assert workspace_prompt == template_body


def test_AC_O_7_workspace_contract_matches_template_except_handle_and_starter(
    tmp_path: Path,
):
    """The workspace's contract.yaml parses to a content equal to
    the template's parsed content with only handle + is_starter
    differing."""
    _, workspace = _run_scaffold(tmp_path)
    workspace_raw = yaml.safe_load(
        (workspace / "workspace" / "personas" / DEFAULT_PERSONA_HANDLE / "contract.yaml").read_text()
    )
    template_raw = yaml.safe_load(TEMPLATE_CONTRACT.read_text())

    # Mutations made by the scaffold:
    assert workspace_raw["handle"] == DEFAULT_PERSONA_HANDLE
    assert workspace_raw["is_starter"] is True

    # Every other key matches the template's value.
    for key, expected in template_raw.items():
        if key in ("handle", "is_starter"):
            continue
        assert workspace_raw.get(key) == expected, (
            f"workspace contract field {key!r} drifted from template; "
            f"workspace={workspace_raw.get(key)!r}, template={expected!r}"
        )

    # The workspace's contract carries no surplus keys beyond the
    # template's (sanity check — scaffold should not be adding new
    # fields).
    surplus = set(workspace_raw.keys()) - set(template_raw.keys()) - {"is_starter"}
    assert surplus == set(), (
        f"workspace contract has surplus keys: {surplus}"
    )


def test_AC_O_7_loaded_workspace_persona_is_loadable(tmp_path: Path):
    """The materialised workspace persona loads through the
    PersonaLoader without error (the contract validates, the
    prompt.md is present)."""
    from loam.primary_persona.loader import PersonaLoader

    _, workspace = _run_scaffold(tmp_path)
    loader = PersonaLoader(workspace, enforce_no_personas_in_core=False)
    primary = loader.primary()
    assert primary.handle == DEFAULT_PERSONA_HANDLE
    assert primary.contract.is_starter is True
    assert primary.contract.is_primary is True
    assert primary.prompt_text  # non-empty
