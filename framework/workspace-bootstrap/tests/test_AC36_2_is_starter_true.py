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

"""Amendment #36 — AC36.2 — Scaffolded contract carries
``is_starter: true``.

Plan §4 AC36.2 outcomes:

- After ``model_validate`` of the scaffolded contract,
  ``contract.is_starter is True``.
- The on-disk YAML carries the ``is_starter: true`` line directly
  (the scaffold writes it explicitly; an audit of the YAML shows
  the flag rather than relying on a contract default).

Maps to v1.0 line 152 (low-friction onboarding) +
amendment #35 AC35.4 (elicitation flow recognises starter-flag) →
AC.PO.1.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam.primary_persona.loader import PersonaLoader

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    DEFAULT_PERSONA_HANDLE,
    run_first_run_scaffold,
)


def _scaffold_fresh(tmp_path: Path) -> Path:
    workspace = tmp_path / "ws-starter"
    workspace.mkdir()
    pos_root = tmp_path / ".pos"
    agents = tmp_path / "LaunchAgents"
    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
    )
    return workspace


def test_AC36_2_loaded_contract_has_is_starter_true(tmp_path: Path) -> None:
    """``loader.load()[0].contract.is_starter is True`` after scaffold."""
    workspace = _scaffold_fresh(tmp_path)

    loaded = PersonaLoader(workspace_root=workspace).load()
    assert len(loaded) == 1
    assert loaded[0].contract.is_starter is True


def test_AC36_2_yaml_text_carries_is_starter_true_line(tmp_path: Path) -> None:
    """The on-disk YAML string contains an ``is_starter: true`` entry —
    not a defaulted absent field. AC36.2 explicitly requires the
    scaffold to write the flag."""
    workspace = _scaffold_fresh(tmp_path)
    contract_path = (
        workspace / "workspace" / "personas" / DEFAULT_PERSONA_HANDLE / "contract.yaml"
    )
    text = contract_path.read_text()

    # Direct YAML-key check: parse and assert the field's presence.
    parsed = yaml.safe_load(text)
    assert isinstance(parsed, dict)
    assert "is_starter" in parsed, (
        "is_starter key not present in scaffolded contract.yaml"
    )
    assert parsed["is_starter"] is True

    # Also assert the literal line is present so a hand-audit of the
    # file shows the flag (the AC reasoning: "a future audit of the
    # YAML directly shows it").
    assert "is_starter: true" in text
