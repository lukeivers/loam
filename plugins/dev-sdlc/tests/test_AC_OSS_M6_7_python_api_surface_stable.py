"""AC.OSS-M6.7 — Persona-invocable Python API surface stable.

Per plan §4 AC.OSS-M6.7: the public surface at
`loam.plugins.dev_sdlc.api` exposes five functions + four Pydantic
models with the recorded signatures.
"""

from __future__ import annotations

import inspect


def test_public_functions_importable() -> None:
    from loam.plugins.dev_sdlc.api import (  # noqa: F401
        advance_stage,
        gate_check,
        list_projects,
        project_status,
        start_project,
    )


def test_public_models_importable() -> None:
    from loam.plugins.dev_sdlc import (  # noqa: F401
        GateResult,
        ProjectHandle,
        ProjectStatus,
        StageAdvanceResult,
    )


def test_start_project_signature() -> None:
    from loam.plugins.dev_sdlc.api import start_project

    sig = inspect.signature(start_project)
    params = sig.parameters
    assert "slug" in params
    assert "methodology" in params
    assert params["methodology"].default == "odd"
    assert "workspace_root" in params
    assert params["workspace_root"].default is None


def test_advance_stage_signature() -> None:
    from loam.plugins.dev_sdlc.api import advance_stage

    sig = inspect.signature(advance_stage)
    assert "slug" in sig.parameters
    assert "workspace_root" in sig.parameters


def test_project_status_signature() -> None:
    from loam.plugins.dev_sdlc.api import project_status

    sig = inspect.signature(project_status)
    assert "slug" in sig.parameters
    assert sig.parameters["slug"].default is None


def test_gate_check_signature() -> None:
    from loam.plugins.dev_sdlc.api import gate_check

    sig = inspect.signature(gate_check)
    assert "slug" in sig.parameters
    assert "workspace_root" in sig.parameters


def test_list_projects_signature() -> None:
    from loam.plugins.dev_sdlc.api import list_projects

    sig = inspect.signature(list_projects)
    assert "workspace_root" in sig.parameters


def test_models_have_expected_fields() -> None:
    from loam.plugins.dev_sdlc import (
        GateResult,
        ProjectHandle,
        ProjectStatus,
        StageAdvanceResult,
    )

    assert set(ProjectHandle.model_fields.keys()) == {
        "slug",
        "methodology",
        "project_root",
        "current_stage",
    }
    assert set(StageAdvanceResult.model_fields.keys()) == {
        "slug",
        "from_stage",
        "to_stage",
        "methodology",
    }
    assert set(ProjectStatus.model_fields.keys()) == {
        "slug",
        "methodology",
        "current_stage",
        "project_root",
    }
    assert set(GateResult.model_fields.keys()) == {
        "slug",
        "stage",
        "passed",
        "reason",
        "detail",
    }
