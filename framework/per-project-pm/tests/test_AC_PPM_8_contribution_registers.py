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

"""AC.PPM.8 — PerProjectPMContribution registers correctly.

Per parent plan §5 + cycle-2 plan §4 Surface #6:
  - metadata: name='per_project_pm', phase=after_orchestrator_ready,
    after=('primary_persona',).
  - Entry-point discovery resolves the contribution class.
  - host.per_project_pm published as PerProjectPMRuntime.
  - runtime_for(pm_name) factory present + raises PMNotFoundError on
    unknown pm_name.
"""

from __future__ import annotations

import importlib.metadata
from pathlib import Path
from typing import Any

import pytest

from loam.per_project_pm.contribution import (
    PerProjectPMContribution,
    PerProjectPMRuntime,
)
from loam.per_project_pm.errors import PMNotFoundError
from loam.per_project_pm.runtime import PMRuntime


class _FakeHost:
    """Minimal stand-in for the BootstrapHost — only needs
    workspace_root + the open-attribute-surface convention."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root


def test_metadata_correct() -> None:
    md = PerProjectPMContribution.metadata
    assert md.name == "per_project_pm"
    # str-Enum match; per workspace_bootstrap.spec.Phase.
    assert md.phase.value == "after_orchestrator_ready"
    assert md.after == ("primary_persona",)


def test_contribute_publishes_host_per_project_pm(tmp_workspace: Path) -> None:
    host: Any = _FakeHost(tmp_workspace)
    contribution = PerProjectPMContribution()
    contribution.contribute(host)
    assert hasattr(host, "per_project_pm")
    assert isinstance(host.per_project_pm, PerProjectPMRuntime)
    assert host.per_project_pm.workspace_root == tmp_workspace


def test_runtime_for_factory_present_and_lazy(tmp_workspace: Path) -> None:
    host: Any = _FakeHost(tmp_workspace)
    PerProjectPMContribution().contribute(host)
    # Lazy: no PM authored yet; runtime_for raises PMNotFoundError.
    with pytest.raises(PMNotFoundError):
        host.per_project_pm.runtime_for("no-such-pm")


def test_runtime_for_returns_PMRuntime_when_authored(
    authored_pm: tuple[Path, str],
) -> None:
    workspace_root, pm_name = authored_pm
    host: Any = _FakeHost(workspace_root)
    PerProjectPMContribution().contribute(host)
    runtime = host.per_project_pm.runtime_for(pm_name)
    assert isinstance(runtime, PMRuntime)
    assert runtime.contract.handle == pm_name


def test_runtime_for_rejects_empty_pm_name(tmp_workspace: Path) -> None:
    host: Any = _FakeHost(tmp_workspace)
    PerProjectPMContribution().contribute(host)
    with pytest.raises(ValueError):
        host.per_project_pm.runtime_for("")


def test_entry_point_discovery() -> None:
    """The pyproject.toml entry-point declaration registers the class
    under the loam.bootstrap.contributions group, discoverable via
    importlib.metadata."""
    eps = importlib.metadata.entry_points(group="loam.bootstrap.contributions")
    matches = [ep for ep in eps if ep.name == "per_project_pm"]
    assert len(matches) == 1, (
        f"per_project_pm entry-point not registered. "
        f"Found in group: {[ep.name for ep in eps]}"
    )
    cls = matches[0].load()
    assert cls is PerProjectPMContribution
