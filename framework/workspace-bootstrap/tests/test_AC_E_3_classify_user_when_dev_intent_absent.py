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

"""AC.E.3 — `classify_workspace` returns "user" when dev_intent is
"absent".

Sub-plan E (two-modes-and-multi-workspace, amendment #42). When
``read_dev_intent`` returns ``"absent"`` (no contract on disk yet, a
starter-flagged contract carrying the ``"unanswered"`` sentinel, or a
malformed contract that fails to load), ``classify_workspace`` falls
back to ``"user"`` per locked owner ruling 4 — defensive default,
"shouldn't happen but defensively."

This is the documented behaviour at first-run scaffold time before
onboarding completes.

Plan: docs/rebuild/plans/two-modes-and-multi-workspace/E-classify-workspace-replacement.md
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.contract import PersonaContract
from loam.primary_persona.onboarding import dev_intent_storage_path

from loam.workspace_bootstrap.adapters.tracker_seed import (
    CLASSIFICATION_USER,
    classify_workspace,
)


def _starter_unanswered_contract_dict() -> dict:
    return {
        "handle": "iris",
        "given_name": "Iris",
        "contract_version": "1.0.0",
        "responsibilities": {
            "single_point_of_contact": "Coordinator.",
            "context_holder": "Holds context.",
            "escalation_judge": "Decides surfacing.",
        },
        "authority_boundary": {
            "tier_a": "defer",
            "tier_b": "defer",
            "tier_c": "execute",
            "tier_d": "execute",
        },
        "escalation_taxonomy": {"categories": ["x"]},
        "severity_vocabulary": {"labels": ["a", "b"]},
        "is_starter": True,
        "is_primary": True,
        # dev_intent omitted — defaults to "unanswered" per amendment
        # #41 contract surface.
    }


def test_AC_E_3_classify_user_when_no_personas_dir(tmp_path: Path) -> None:
    """A workspace with no ``personas/`` directory at all (the freshest
    possible state) classifies as ``"user"``."""
    workspace = tmp_path / "ws-fresh"
    workspace.mkdir()

    assert classify_workspace(workspace) == CLASSIFICATION_USER


def test_AC_E_3_classify_user_when_starter_contract_unanswered(
    tmp_path: Path,
) -> None:
    """A starter-flagged contract whose dev_intent is the
    ``"unanswered"`` sentinel — the state immediately after
    ``_install_persona_directory`` writes the template — classifies as
    ``"user"``."""
    workspace = tmp_path / "ws-starter"
    workspace.mkdir()
    personas_dir = dev_intent_storage_path(workspace)
    persona_dir = personas_dir / "iris"
    persona_dir.mkdir(parents=True)
    contract = PersonaContract.model_validate(
        _starter_unanswered_contract_dict()
    )
    (persona_dir / "contract.yaml").write_text(contract.to_yaml())

    assert classify_workspace(workspace) == CLASSIFICATION_USER


def test_AC_E_3_classify_user_when_contract_malformed(tmp_path: Path) -> None:
    """A malformed contract (yaml-load fails) is treated as absent by
    ``read_dev_intent`` and classifies as ``"user"`` — fail-soft."""
    workspace = tmp_path / "ws-malformed"
    workspace.mkdir()
    personas_dir = dev_intent_storage_path(workspace)
    persona_dir = personas_dir / "broken"
    persona_dir.mkdir(parents=True)
    (persona_dir / "contract.yaml").write_text("not: { valid yaml")

    assert classify_workspace(workspace) == CLASSIFICATION_USER
