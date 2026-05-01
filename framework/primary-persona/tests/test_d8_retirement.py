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

"""D8 — retirement.

Acceptance (brief D8):
- Retirement moves personas/<handle>/ to
  personas/_retired/<handle>-<timestamp>/.
- Active loader ignores _retired/*.
- Memory/scopes referencing the retired persona by ID continue to
  resolve via history (tested via presence of the directory contents
  at the new path — the file itself is still readable).
- Retirement emits an auditable event with the reason.
- A test asserts a retired persona cannot be reloaded without
  explicit un-retirement.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.primary_persona.loader import PersonaLoader, PersonaValidationError
from loam.primary_persona.retirement import (
    RetirementReason,
    RetirementRecord,
    retire_persona,
)

from tests.conftest import write_persona_dir


def test_retirement_moves_directory(workspace_with_primary: Path):
    # Add a second persona to retire (cannot retire the only primary).
    write_persona_dir(workspace_with_primary / "workspace" / "personas", "mara")
    assert (workspace_with_primary / "workspace" / "personas" / "mara").exists()

    record = retire_persona(
        workspace_root=workspace_with_primary,
        handle="mara",
        reason=RetirementReason.user_initiated,
    )

    assert isinstance(record, RetirementRecord)
    assert not (workspace_with_primary / "workspace" / "personas" / "mara").exists()
    # Record names the new directory.
    assert record.to_dir.exists()
    assert record.to_dir.parent.name == "_retired"
    # Files moved with it.
    assert (record.to_dir / "contract.yaml").exists()
    assert (record.to_dir / "prompt.md").exists()


def test_retired_persona_not_loaded_by_active_loader(
    workspace_with_primary: Path,
):
    write_persona_dir(workspace_with_primary / "workspace" / "personas", "mara")

    retire_persona(
        workspace_root=workspace_with_primary,
        handle="mara",
        reason=RetirementReason.user_initiated,
    )

    loader = PersonaLoader(
        workspace_with_primary, enforce_no_personas_in_core=False
    )
    loaded = loader.load()
    handles = [p.handle for p in loaded]
    assert "mara" not in handles
    assert handles == ["eve"]


def test_retired_persona_cannot_be_reloaded_by_handle(
    workspace_with_primary: Path,
):
    write_persona_dir(workspace_with_primary / "workspace" / "personas", "mara")
    retire_persona(
        workspace_root=workspace_with_primary,
        handle="mara",
        reason=RetirementReason.user_initiated,
    )
    loader = PersonaLoader(
        workspace_with_primary, enforce_no_personas_in_core=False
    )
    with pytest.raises(PersonaValidationError):
        loader.load_one("mara")


def test_retirement_of_nonexistent_raises(workspace_with_primary: Path):
    with pytest.raises(FileNotFoundError):
        retire_persona(
            workspace_root=workspace_with_primary,
            handle="nobody",
            reason=RetirementReason.user_initiated,
        )


def test_retirement_preserves_contract_contents(
    workspace_with_primary: Path,
):
    write_persona_dir(workspace_with_primary / "workspace" / "personas", "mara")
    record = retire_persona(
        workspace_root=workspace_with_primary,
        handle="mara",
        reason=RetirementReason.superseded,
    )
    # Contents intact (persona history for memory/scope references).
    text = (record.to_dir / "contract.yaml").read_text()
    assert "handle: mara" in text


def test_un_retirement_is_manual_move(workspace_with_primary: Path):
    """Brief D8: 'a retired persona cannot be reloaded without explicit
    un-retirement (moving the directory back).'"""
    write_persona_dir(workspace_with_primary / "workspace" / "personas", "mara")
    record = retire_persona(
        workspace_root=workspace_with_primary,
        handle="mara",
        reason=RetirementReason.user_initiated,
    )
    # Manually move back.
    import shutil

    target = workspace_with_primary / "workspace" / "personas" / "mara"
    shutil.move(str(record.to_dir), str(target))
    loader = PersonaLoader(
        workspace_with_primary, enforce_no_personas_in_core=False
    )
    loaded = loader.load_one("mara")
    assert loaded.handle == "mara"


def test_retirement_reason_carried_on_record(workspace_with_primary: Path):
    write_persona_dir(workspace_with_primary / "workspace" / "personas", "mara")
    for reason in RetirementReason:
        # re-create mara each time
        write_persona_dir(workspace_with_primary / "workspace" / "personas", "mara")
        record = retire_persona(
            workspace_root=workspace_with_primary,
            handle="mara",
            reason=reason,
        )
        assert record.reason == reason
