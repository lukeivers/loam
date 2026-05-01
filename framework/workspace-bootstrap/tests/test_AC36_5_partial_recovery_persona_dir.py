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

"""Amendment #36 — AC36.5 — ``partial_recovery`` recognises the
persona directory as tracked.

Plan §4 AC36.5 outcomes:

- If the persona directory exists but the contract is malformed
  (e.g., interrupted write produced a zero-byte file), the scaffold
  surfaces a structured diagnostic naming the failure rather than
  silently overwriting or silently completing.
- The half-written file is NOT overwritten by the scaffold's
  recovery path.

D-build.4: extends the existing ``PartialScaffoldError`` with a
``kind`` sub-cause field rather than introducing a new exception
class so downstream H4 handlers continue to route uniformly.

Maps to hands-off-lifecycle H4 (partial-scaffold detection
convention) extended consistently to the persona-tree → AC.PO.1.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    DEFAULT_PERSONA_HANDLE,
    PartialScaffoldError,
    _install_persona_directory,
)


def _seed_half_written(workspace: Path, handle: str = DEFAULT_PERSONA_HANDLE) -> Path:
    """Create ``<workspace>/personas/<handle>/`` with a zero-byte
    ``contract.yaml`` — simulating an interrupted prior install.
    Returns the persona-dir path."""
    persona_dir = workspace / "workspace" / "personas" / handle
    persona_dir.mkdir(parents=True, exist_ok=True)
    (persona_dir / "contract.yaml").write_bytes(b"")
    return persona_dir


def test_AC36_5_zero_byte_contract_raises_structured_diagnostic(
    tmp_path: Path,
) -> None:
    """A persona-dir with a zero-byte ``contract.yaml`` raises
    ``PartialScaffoldError`` carrying ``kind="persona-scaffold-malformed"``
    and the persona-dir path in the data payload."""
    workspace = tmp_path / "ws-half"
    workspace.mkdir()
    persona_dir = _seed_half_written(workspace)

    with pytest.raises(PartialScaffoldError) as excinfo:
        _install_persona_directory(
            workspace_root=workspace,
            handle=DEFAULT_PERSONA_HANDLE,
        )

    err = excinfo.value
    assert err.data.get("kind") == "persona-scaffold-malformed"
    assert err.data.get("persona_dir") == str(persona_dir)
    assert "contract.yaml" in err.data.get("contract_path", "")
    assert "interrupted" in err.data.get("reason", "").lower()


def test_AC36_5_half_written_file_not_overwritten(tmp_path: Path) -> None:
    """The diagnostic raise leaves the zero-byte file in place — the
    scaffold does not silently overwrite the partial state."""
    workspace = tmp_path / "ws-half"
    workspace.mkdir()
    persona_dir = _seed_half_written(workspace)
    contract_path = persona_dir / "contract.yaml"
    pre_size = contract_path.stat().st_size

    with pytest.raises(PartialScaffoldError):
        _install_persona_directory(
            workspace_root=workspace,
            handle=DEFAULT_PERSONA_HANDLE,
        )

    assert contract_path.exists()
    assert contract_path.stat().st_size == pre_size


def test_AC36_5_missing_contract_in_existing_dir_raises(tmp_path: Path) -> None:
    """A persona-dir present without any ``contract.yaml`` at all is
    also a half-written state — the AC's "interrupted write"
    coverage includes the case where the rename completed but
    contract authoring crashed before the file was created."""
    workspace = tmp_path / "ws-no-contract"
    workspace.mkdir()
    persona_dir = workspace / "workspace" / "personas" / DEFAULT_PERSONA_HANDLE
    persona_dir.mkdir(parents=True)
    # Add only prompt.md — contract.yaml missing.
    (persona_dir / "prompt.md").write_text("placeholder")

    with pytest.raises(PartialScaffoldError) as excinfo:
        _install_persona_directory(
            workspace_root=workspace,
            handle=DEFAULT_PERSONA_HANDLE,
        )
    assert excinfo.value.data["kind"] == "persona-scaffold-malformed"
