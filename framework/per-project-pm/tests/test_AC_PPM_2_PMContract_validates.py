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

"""AC.PPM.2 — PMContract Pydantic model present + validates.

Per parent plan §5 + cycle-2 plan §4 Surface #4. PMContract carries
8 fields (5 required scalar; 1 nested policy with default; 2 advisory
tuples with default). Validation rejects:
  - empty handle
  - invalid project_kind
  - non-absolute workspace_root
with errors that name the offending field.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from loam.per_project_pm.contract import (
    DecisionSurfacingPolicy,
    PMContract,
)


def _valid_kwargs(**overrides: object) -> dict:
    base = {
        "handle": "test-pm",
        "project_name": "test-project",
        "project_kind": "general",
        "owner_name": "Tester",
        "workspace_root": Path("/tmp/test-workspace"),
    }
    base.update(overrides)
    return base


def test_construct_valid_contract() -> None:
    contract = PMContract(**_valid_kwargs())
    assert contract.handle == "test-pm"
    assert contract.project_name == "test-project"
    assert contract.project_kind == "general"
    assert contract.owner_name == "Tester"
    assert contract.workspace_root == Path("/tmp/test-workspace")
    # default-constructed policy
    assert isinstance(contract.decision_surfacing_policy, DecisionSurfacingPolicy)
    # default-empty advisory tuples
    assert contract.composes_with_skills == ()
    assert contract.composes_with_agents == ()


def test_reject_empty_handle() -> None:
    with pytest.raises(ValidationError) as excinfo:
        PMContract(**_valid_kwargs(handle=""))
    assert "handle" in str(excinfo.value)


def test_reject_invalid_project_kind() -> None:
    with pytest.raises(ValidationError) as excinfo:
        PMContract(**_valid_kwargs(project_kind="not-a-kind"))
    assert "project_kind" in str(excinfo.value)


def test_reject_non_absolute_workspace_root() -> None:
    with pytest.raises(ValidationError) as excinfo:
        PMContract(**_valid_kwargs(workspace_root=Path("relative/path")))
    assert "workspace_root" in str(excinfo.value)


def test_reject_empty_project_name() -> None:
    with pytest.raises(ValidationError) as excinfo:
        PMContract(**_valid_kwargs(project_name=""))
    assert "project_name" in str(excinfo.value)


def test_reject_empty_owner_name() -> None:
    with pytest.raises(ValidationError) as excinfo:
        PMContract(**_valid_kwargs(owner_name=""))
    assert "owner_name" in str(excinfo.value)


def test_reject_unknown_field() -> None:
    """extra='forbid' in model_config rejects typos in the contract."""
    with pytest.raises(ValidationError):
        PMContract(**_valid_kwargs(unknown_field="oops"))


def test_accept_advisory_compose_lists_as_lists() -> None:
    """YAML lists coerce to tuples (frozen)."""
    contract = PMContract(
        **_valid_kwargs(
            composes_with_skills=["dispatch-with-gates"],
            composes_with_agents=["loam-builder", "loam-reviewer"],
        )
    )
    assert contract.composes_with_skills == ("dispatch-with-gates",)
    assert contract.composes_with_agents == ("loam-builder", "loam-reviewer")


def test_contract_is_frozen() -> None:
    """Contract is immutable after construction; mutate via state files,
    not via mutating the contract object."""
    contract = PMContract(**_valid_kwargs())
    with pytest.raises(ValidationError):
        contract.handle = "new-handle"  # type: ignore[misc]


def test_each_project_kind_accepted() -> None:
    """Every documented project_kind value is valid."""
    for kind in ("dev", "writing", "research", "ops", "general"):
        contract = PMContract(**_valid_kwargs(project_kind=kind))
        assert contract.project_kind == kind


def test_workspace_root_string_coerced_to_path() -> None:
    """Pydantic v2 coerces str → Path; validator runs after coercion."""
    contract = PMContract(**_valid_kwargs(workspace_root="/tmp/another-ws"))
    assert isinstance(contract.workspace_root, Path)
    assert contract.workspace_root == Path("/tmp/another-ws")
