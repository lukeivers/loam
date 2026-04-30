"""AC.OSS-M6.4 — Stage gate enforces objective + AC presence before
advance.

Per plan §4 AC.OSS-M6.4: four named failure modes
(`artefact_not_found`, `no_objective`, `no_ac`, `terminal_stage`)
+ a passing case advances the project's current_stage.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.plugins.dev_sdlc import api
from loam.plugins.dev_sdlc.errors import (
    StageGateFailedError,
    TerminalStageError,
)


def _start(tmp_path: Path, methodology: str = "odd") -> Path:
    api.start_project(
        slug="proj",
        methodology=methodology,
        workspace_root=tmp_path,
    )
    return tmp_path / "projects" / "proj"


def test_advance_artefact_not_found_raises(tmp_path: Path) -> None:
    _start(tmp_path)
    with pytest.raises(StageGateFailedError) as exc:
        api.advance_stage(slug="proj", workspace_root=tmp_path)
    assert exc.value.reason == "artefact_not_found"
    assert exc.value.project == "proj"
    assert exc.value.stage == "research"


def test_advance_no_objective_raises(tmp_path: Path) -> None:
    proj_root = _start(tmp_path)
    artefact = proj_root / "research" / "proj.md"
    artefact.write_text(
        "# proj — research\n\n## Acceptance Criteria\n\n- one\n",
        encoding="utf-8",
    )
    with pytest.raises(StageGateFailedError) as exc:
        api.advance_stage(slug="proj", workspace_root=tmp_path)
    assert exc.value.reason == "no_objective"


def test_advance_no_ac_raises(tmp_path: Path) -> None:
    proj_root = _start(tmp_path)
    artefact = proj_root / "research" / "proj.md"
    artefact.write_text(
        "# proj — research\n\n## Objective\n\nDo a thing.\n",
        encoding="utf-8",
    )
    with pytest.raises(StageGateFailedError) as exc:
        api.advance_stage(slug="proj", workspace_root=tmp_path)
    assert exc.value.reason == "no_ac"


def test_advance_complete_artefact_advances_stage(
    tmp_path: Path,
) -> None:
    proj_root = _start(tmp_path)
    artefact = proj_root / "research" / "proj.md"
    artefact.write_text(
        "# proj — research\n\n"
        "## Objective\n\nDo a thing.\n\n"
        "## Acceptance Criteria\n\n- one observable outcome\n",
        encoding="utf-8",
    )
    result = api.advance_stage(slug="proj", workspace_root=tmp_path)
    assert result.from_stage == "research"
    assert result.to_stage == "spec"
    assert result.methodology == "odd"

    statuses = api.project_status(
        slug="proj", workspace_root=tmp_path
    )
    assert len(statuses) == 1
    assert statuses[0].current_stage == "spec"


def test_advance_complete_artefact_via_frontmatter(
    tmp_path: Path,
) -> None:
    """Frontmatter-form ODD: `objective:` + `acceptance_criteria:`
    list both supplied → gate passes."""
    proj_root = _start(tmp_path)
    artefact = proj_root / "research" / "proj.md"
    artefact.write_text(
        "---\n"
        "objective: 'Do a thing'\n"
        "acceptance_criteria:\n"
        "  - 'observable outcome'\n"
        "---\n\n"
        "Body.\n",
        encoding="utf-8",
    )
    result = api.advance_stage(slug="proj", workspace_root=tmp_path)
    assert result.to_stage == "spec"


def test_terminal_stage_advance_raises(tmp_path: Path) -> None:
    """Authoring an artefact at every stage + advancing through them
    leaves the project at `review` (terminal). Further advance
    raises TerminalStageError (gate is OK; advance refuses)."""
    proj_root = _start(tmp_path)
    body = (
        "## Objective\n\nDo a thing.\n\n"
        "## Acceptance Criteria\n\n- outcome\n"
    )
    for st in ("research", "spec", "plan", "build"):
        (proj_root / st / "proj.md").write_text(body, encoding="utf-8")
        api.advance_stage(slug="proj", workspace_root=tmp_path)
    statuses = api.project_status(
        slug="proj", workspace_root=tmp_path
    )
    assert statuses[0].current_stage == "review"
    # Author a review artefact too — gate would pass — but advance
    # raises TerminalStageError.
    (proj_root / "review" / "proj.md").write_text(body, encoding="utf-8")
    with pytest.raises(TerminalStageError):
        api.advance_stage(slug="proj", workspace_root=tmp_path)


def test_gate_check_returns_pass_without_advancing(
    tmp_path: Path,
) -> None:
    proj_root = _start(tmp_path)
    (proj_root / "research" / "proj.md").write_text(
        "## Objective\n\nDo it.\n\n## Acceptance Criteria\n\n- x\n",
        encoding="utf-8",
    )
    result = api.gate_check(slug="proj", workspace_root=tmp_path)
    assert result.passed is True
    assert result.reason is None
    # Stage didn't advance.
    statuses = api.project_status(
        slug="proj", workspace_root=tmp_path
    )
    assert statuses[0].current_stage == "research"


def test_gate_check_returns_failure_reason(tmp_path: Path) -> None:
    _start(tmp_path)
    result = api.gate_check(slug="proj", workspace_root=tmp_path)
    assert result.passed is False
    assert result.reason == "artefact_not_found"
