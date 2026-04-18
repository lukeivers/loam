"""D2 — loader + validator.

Acceptance (brief D2):
- Valid persona loads cleanly.
- Invalid persona rejects with clear error naming the failing field.
- No persona directory present in workspace → session cannot start
  (deterministic, not advisory).
- Build-time check fails if any persona directory appears in pOS-core
  paths (core ships zero personas).
- Loader is stateless; reloading the same directory produces identical
  results.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.loader import (
    LoadedPersona,
    PersonaDirectoryNotFoundError,
    PersonaInCoreError,
    PersonaLoader,
    PersonaValidationError,
)

from tests.conftest import VALID_CONTRACT_YAML, write_persona_dir


# ---- valid load ------------------------------------------------------


def test_valid_persona_loads_cleanly(workspace_with_primary: Path):
    loader = PersonaLoader(
        workspace_with_primary, enforce_no_personas_in_core=False
    )
    loaded = loader.load()
    assert len(loaded) == 1
    p = loaded[0]
    assert isinstance(p, LoadedPersona)
    assert p.handle == "eve"
    assert p.given_name == "Eve"
    assert "persona prompt" in p.prompt_text


def test_primary_returns_is_primary_persona(workspace_with_primary: Path):
    loader = PersonaLoader(
        workspace_with_primary, enforce_no_personas_in_core=False
    )
    p = loader.primary()
    assert p.handle == "eve"
    assert p.contract.is_primary is True


# ---- failure modes ---------------------------------------------------


def test_no_personas_dir_raises(tmp_path: Path):
    # No `personas/` subdir at all.
    loader = PersonaLoader(tmp_path, enforce_no_personas_in_core=False)
    with pytest.raises(PersonaDirectoryNotFoundError):
        loader.load()


def test_empty_personas_dir_raises(workspace: Path):
    loader = PersonaLoader(workspace, enforce_no_personas_in_core=False)
    with pytest.raises(PersonaDirectoryNotFoundError):
        loader.load()


def test_missing_contract_file_rejects(workspace: Path):
    persona_dir = workspace / "personas" / "broken"
    persona_dir.mkdir(parents=True)
    # Only prompt.md, no contract.yaml.
    (persona_dir / "prompt.md").write_text("p")
    loader = PersonaLoader(workspace, enforce_no_personas_in_core=False)
    with pytest.raises(PersonaValidationError) as exc:
        loader.load()
    assert "contract.yaml" in str(exc.value)


def test_missing_prompt_file_rejects(workspace: Path):
    persona_dir = workspace / "personas" / "missing-prompt"
    persona_dir.mkdir(parents=True)
    (persona_dir / "contract.yaml").write_text(
        VALID_CONTRACT_YAML.replace("handle: eve", "handle: missing-prompt")
    )
    loader = PersonaLoader(workspace, enforce_no_personas_in_core=False)
    with pytest.raises(PersonaValidationError) as exc:
        loader.load()
    assert "prompt.md" in str(exc.value)


def test_invalid_contract_field_names_failing_field(workspace: Path):
    persona_dir = workspace / "personas" / "invalid"
    persona_dir.mkdir(parents=True)
    # Missing severity_vocabulary entirely.
    (persona_dir / "contract.yaml").write_text(
        "handle: invalid\n"
        "given_name: X\n"
        "responsibilities:\n"
        "  single_point_of_contact: a\n"
        "  context_holder: b\n"
        "  escalation_judge: c\n"
        "authority_boundary:\n"
        "  tier_a: defer\n"
        "  tier_b: defer\n"
        "  tier_c: execute\n"
        "  tier_d: execute\n"
        "escalation_taxonomy:\n"
        "  categories:\n"
        "    - c\n"
    )
    (persona_dir / "prompt.md").write_text("p")
    loader = PersonaLoader(workspace, enforce_no_personas_in_core=False)
    with pytest.raises(PersonaValidationError) as exc:
        loader.load()
    # Error message names the failing field (severity_vocabulary).
    assert "severity_vocabulary" in str(exc.value)


def test_handle_directory_mismatch_rejects(workspace: Path):
    # Directory name `x` but contract claims handle `y`.
    persona_dir = workspace / "personas" / "x"
    persona_dir.mkdir(parents=True)
    (persona_dir / "contract.yaml").write_text(
        VALID_CONTRACT_YAML.replace("handle: eve", "handle: y")
    )
    (persona_dir / "prompt.md").write_text("p")
    loader = PersonaLoader(workspace, enforce_no_personas_in_core=False)
    with pytest.raises(PersonaValidationError) as exc:
        loader.load()
    assert "handle" in str(exc.value) and "directory" in str(exc.value)


# ---- primary ambiguity -----------------------------------------------


def test_zero_primaries_rejects(workspace: Path):
    # Single persona with is_primary: false.
    write_persona_dir(
        workspace / "personas",
        "sidekick",
        yaml_override=VALID_CONTRACT_YAML.replace(
            "handle: eve", "handle: sidekick"
        ).replace("is_primary: true", "is_primary: false"),
    )
    loader = PersonaLoader(workspace, enforce_no_personas_in_core=False)
    with pytest.raises(PersonaValidationError) as exc:
        loader.primary()
    assert "is_primary" in str(exc.value)


def test_multiple_primaries_rejects(workspace: Path):
    write_persona_dir(workspace / "personas", "eve")
    # Second primary:
    write_persona_dir(
        workspace / "personas",
        "also-primary",
        yaml_override=VALID_CONTRACT_YAML.replace(
            "handle: eve", "handle: also-primary"
        ),
    )
    loader = PersonaLoader(workspace, enforce_no_personas_in_core=False)
    with pytest.raises(PersonaValidationError) as exc:
        loader.primary()
    assert "multiple" in str(exc.value).lower()


# ---- statelessness ---------------------------------------------------


def test_reload_produces_identical_results(workspace_with_primary: Path):
    loader = PersonaLoader(
        workspace_with_primary, enforce_no_personas_in_core=False
    )
    a = loader.load()
    b = loader.load()
    assert len(a) == len(b) == 1
    assert a[0].handle == b[0].handle
    assert a[0].contract.model_dump() == b[0].contract.model_dump()


def test_retired_personas_ignored(workspace_with_primary: Path):
    # Add a directory under _retired/ — it must not load.
    retired = workspace_with_primary / "personas" / "_retired" / "old-persona"
    retired.mkdir(parents=True)
    (retired / "contract.yaml").write_text(
        VALID_CONTRACT_YAML.replace("handle: eve", "handle: old-persona")
    )
    (retired / "prompt.md").write_text("x")

    loader = PersonaLoader(
        workspace_with_primary, enforce_no_personas_in_core=False
    )
    loaded = loader.load()
    handles = [p.handle for p in loaded]
    assert "old-persona" not in handles
    assert handles == ["eve"]


# ---- no personas in core ---------------------------------------------


def test_core_check_passes_for_template_dir(workspace_with_primary: Path):
    # With the core check enabled, the template (handle == example-persona)
    # is allowed. The check passes construction and load works.
    loader = PersonaLoader(workspace_with_primary, enforce_no_personas_in_core=True)
    loaded = loader.load()
    assert len(loaded) == 1


def test_core_check_fails_on_smuggled_persona(tmp_path: Path, monkeypatch):
    # Simulate a forbidden persona dir inside the framework tree.
    import src.loader as loader_mod

    fake_core = tmp_path / "primary-persona" / "src" / "_smuggled"
    fake_core.mkdir(parents=True)
    persona_dir = fake_core / "bad-one"
    persona_dir.mkdir()
    persona_dir.joinpath("contract.yaml").write_text(
        VALID_CONTRACT_YAML.replace("handle: eve", "handle: bad-one")
    )
    persona_dir.joinpath("prompt.md").write_text("x")

    # Monkeypatch the loader's __file__ to pretend it lives under the
    # fake_core tree.
    fake_loader_path = tmp_path / "primary-persona" / "src" / "loader.py"
    fake_loader_path.parent.mkdir(parents=True, exist_ok=True)
    fake_loader_path.write_text("")
    monkeypatch.setattr(loader_mod, "__file__", str(fake_loader_path))

    # Any workspace_root is fine; the check scans framework-core paths.
    ws = tmp_path / "ws"
    (ws / "personas").mkdir(parents=True)
    write_persona_dir(ws / "personas", "eve")

    with pytest.raises(PersonaInCoreError) as exc:
        PersonaLoader(ws, enforce_no_personas_in_core=True)
    assert "bad-one" in str(exc.value)
