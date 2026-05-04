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

"""Shared pytest fixtures for the per-project-pm test suite.

Provides:
  - ``tmp_workspace`` — a tmp_path-rooted workspace with the
    ``workspace/.loam/pms/`` directory NOT pre-created (the runtime
    creates lazily; D1 cold-state).
  - ``authored_pm`` — a tmp_workspace with a valid ``contract.yaml``
    authored at ``<ws>/workspace/.loam/pms/<handle>/contract.yaml``.
  - ``MIN_VALID_CONTRACT`` — a minimal valid contract dict for tests
    that author their own contract.yaml inline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml


MIN_VALID_CONTRACT_YAML: dict[str, Any] = {
    "schema_version": 1,
    "handle": "test-pm",
    "project_name": "test-project",
    "project_kind": "general",
    "owner_name": "Tester",
    # workspace_root is filled in per-fixture below since it must
    # match the actual tmp workspace path.
    "decision_surfacing_policy": {
        "onboarding_mode": False,
        "max_questions_per_turn": 1,
        "cool_down_seconds": 0,
        "require_owner_response": True,
    },
}


@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Path:
    """Tmp workspace root with ``workspace/`` subdir created (D.2
    canonical) but NO PMs authored.

    Tests that need to assert the D1 cold-state ("PM auto-loads but
    nothing authored yet") use this fixture.
    """
    ws = tmp_path / "test-workspace"
    ws.mkdir()
    (ws / "workspace").mkdir()
    return ws


@pytest.fixture
def authored_pm(tmp_workspace: Path) -> tuple[Path, str]:
    """Tmp workspace with a single authored PM contract.yaml.

    Returns ``(workspace_root, pm_name)``. The PM has an empty queue
    + no state.yaml (those are runtime-created on first write).
    """
    pm_name = "test-pm"
    pm_dir = tmp_workspace / "workspace" / ".loam" / "pms" / pm_name
    pm_dir.mkdir(parents=True)
    contract = dict(MIN_VALID_CONTRACT_YAML)
    contract["workspace_root"] = str(tmp_workspace)
    (pm_dir / "contract.yaml").write_text(yaml.safe_dump(contract))
    return tmp_workspace, pm_name
