"""Amendment #36 — AC36.1 — Fresh-clone first-run produces a valid
persona directory.

Plan §4 AC36.1 outcomes (post-scaffold on a workspace with no
``personas/``):

- ``<workspace>/personas/<handle>/contract.yaml`` exists, non-empty.
- ``<workspace>/personas/<handle>/prompt.md`` exists, non-empty.
- ``PersonaLoader(workspace_root).load()`` returns a single
  ``LoadedPersona`` whose ``contract`` validates against the
  ``PersonaContract`` Pydantic model.

Maps to v1.0 line 153 (persona present every session — directory
existence prerequisite) → AC.PO.1.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.primary_persona.loader import PersonaLoader

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    DEFAULT_PERSONA_HANDLE,
    run_first_run_scaffold,
)


def _scaffold_fresh(
    *,
    tmp_path: Path,
    persona_handle: str = DEFAULT_PERSONA_HANDLE,
) -> tuple[Path, "object"]:
    """Run the scaffold against a fresh tmpfs workspace; return
    ``(workspace_root, scaffold_result)``."""
    workspace = tmp_path / "ws-fresh"
    workspace.mkdir()
    pos_root = tmp_path / ".pos"
    agents = tmp_path / "LaunchAgents"
    result = run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
        persona_handle=persona_handle,
    )
    return workspace, result


def test_AC36_1_fresh_scaffold_writes_persona_directory_files(
    tmp_path: Path,
) -> None:
    workspace, result = _scaffold_fresh(tmp_path=tmp_path)

    persona_dir = workspace / "workspace" / "personas" / DEFAULT_PERSONA_HANDLE
    contract_path = persona_dir / "contract.yaml"
    prompt_path = persona_dir / "prompt.md"

    assert contract_path.exists(), f"missing {contract_path}"
    assert prompt_path.exists(), f"missing {prompt_path}"
    assert contract_path.stat().st_size > 0, "contract.yaml is empty"
    assert prompt_path.stat().st_size > 0, "prompt.md is empty"

    # Result reports the install.
    assert result.persona_installed is True
    assert result.persona_dir == persona_dir.resolve()


def test_AC36_1_loader_validates_scaffolded_contract(tmp_path: Path) -> None:
    """``PersonaLoader(workspace_root).load()`` returns a single
    ``LoadedPersona`` for a freshly-scaffolded workspace."""
    workspace, _ = _scaffold_fresh(tmp_path=tmp_path)

    loader = PersonaLoader(workspace_root=workspace)
    loaded_personas = loader.load()

    assert len(loaded_personas) == 1
    only = loaded_personas[0]
    # Validate against the PersonaContract Pydantic model — already
    # implicit in `loader.load()` returning, but assert explicit
    # field shape so a future loader-internals refactor cannot
    # silently drop validation.
    assert only.contract.handle == DEFAULT_PERSONA_HANDLE
    assert only.contract.is_primary is True


def test_AC36_1_custom_handle_round_trips_through_loader(
    tmp_path: Path,
) -> None:
    """A non-default handle resolves into the persona-dir name and
    the contract handle field."""
    workspace, result = _scaffold_fresh(
        tmp_path=tmp_path, persona_handle="iris"
    )

    persona_dir = workspace / "workspace" / "personas" / "iris"
    assert persona_dir.is_dir()
    assert (persona_dir / "contract.yaml").is_file()
    assert (persona_dir / "prompt.md").is_file()

    loader = PersonaLoader(workspace_root=workspace)
    loaded = loader.load()
    assert len(loaded) == 1
    assert loaded[0].contract.handle == "iris"
    assert result.persona_installed is True
