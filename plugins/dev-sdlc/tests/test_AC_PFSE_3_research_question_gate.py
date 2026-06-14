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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.PFSE.3 — a research-plan that omits any of the four research
questions cannot advance; the gate refuses.

Verification surface (plan §5): a research-plan fixture missing one
question is rejected by the gate THROUGH ITS PRODUCTION ENTRY-POINT
(`api.advance_stage` / `api.gate_check`); a complete one passes.

The four questions (canonical, docs/FUTURE_IDEAS.md Step 3): Claude-
leverage / Primary-persona / Harness / ODD. The gate is opt-in via a
`lens_research: true` frontmatter flag (feedback_odd_cdc_scope — the
lens questions are loam-feature-research discipline, not universal to
every ODD project); a plan without the flag is a generic ODD research
stage and is not gated by the four questions.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.plugins.dev_sdlc import api
from loam.plugins.dev_sdlc.errors import StageGateFailedError


_FRONTMATTER = (
    "---\n"
    "objective: 'Research the thing'\n"
    "acceptance_criteria:\n"
    "  - 'an observable outcome'\n"
    "lens_research: true\n"
    "---\n\n"
)

_FOUR_QUESTIONS = (
    "## Research questions\n\n"
    "### Claude-leverage\n\nLeans on the Stop hook event.\n\n"
    "### Primary-persona\n\nReduces translation burden by X.\n\n"
    "### Harness\n\nAdds a new guard to the toolkit.\n\n"
    "### ODD\n\nObjective + constraints + acceptance, method open.\n"
)


def _start(tmp_path: Path) -> Path:
    api.start_project(
        slug="proj", methodology="odd", workspace_root=tmp_path
    )
    return tmp_path / "projects" / "proj"


def _write_research(proj_root: Path, body: str) -> None:
    (proj_root / "research" / "proj.md").write_text(
        body, encoding="utf-8"
    )


# ----- complete lens-research plan advances -----


def test_AC_PFSE_3_complete_plan_advances(tmp_path: Path) -> None:
    proj_root = _start(tmp_path)
    _write_research(proj_root, _FRONTMATTER + _FOUR_QUESTIONS)
    result = api.advance_stage(slug="proj", workspace_root=tmp_path)
    assert result.from_stage == "research"
    assert result.to_stage == "spec"


# ----- each missing question is rejected (parametrised) -----


@pytest.mark.parametrize(
    "drop_heading",
    [
        "### Claude-leverage\n\nLeans on the Stop hook event.\n\n",
        "### Primary-persona\n\nReduces translation burden by X.\n\n",
        "### Harness\n\nAdds a new guard to the toolkit.\n\n",
        "### ODD\n\nObjective + constraints + acceptance, method open.\n",
    ],
)
def test_AC_PFSE_3_missing_question_refuses(
    tmp_path: Path, drop_heading: str
) -> None:
    proj_root = _start(tmp_path)
    body = _FRONTMATTER + _FOUR_QUESTIONS.replace(drop_heading, "")
    _write_research(proj_root, body)
    with pytest.raises(StageGateFailedError) as exc:
        api.advance_stage(slug="proj", workspace_root=tmp_path)
    assert exc.value.reason == "missing_research_question"


# ----- an EMPTY question section is rejected -----


def test_AC_PFSE_3_empty_question_body_refuses(tmp_path: Path) -> None:
    proj_root = _start(tmp_path)
    # Harness heading present but with an empty body (next line is the
    # ODD heading) -> must refuse.
    body = (
        _FRONTMATTER
        + "## Research questions\n\n"
        + "### Claude-leverage\n\nLeans on a hook.\n\n"
        + "### Primary-persona\n\nReduces burden.\n\n"
        + "### Harness\n\n"
        + "### ODD\n\nMethod open.\n"
    )
    _write_research(proj_root, body)
    with pytest.raises(StageGateFailedError) as exc:
        api.advance_stage(slug="proj", workspace_root=tmp_path)
    assert exc.value.reason == "missing_research_question"


# ----- gate_check (non-advancing production entry) reports the reason -----


def test_AC_PFSE_3_gate_check_reports_missing(tmp_path: Path) -> None:
    proj_root = _start(tmp_path)
    body = _FRONTMATTER + _FOUR_QUESTIONS.replace(
        "### ODD\n\nObjective + constraints + acceptance, method open.\n",
        "",
    )
    _write_research(proj_root, body)
    result = api.gate_check(slug="proj", workspace_root=tmp_path)
    assert result.passed is False
    assert result.reason == "missing_research_question"
    assert "odd" in (result.detail or "").lower()


# ----- generic ODD research (no lens_research flag) is NOT gated -----


def test_AC_PFSE_3_generic_odd_research_not_gated(
    tmp_path: Path,
) -> None:
    """A research plan WITHOUT the lens_research flag is generic ODD —
    objective + AC alone advance it (feedback_odd_cdc_scope). The four-
    question gate does not retroactively break the generic contract."""
    proj_root = _start(tmp_path)
    _write_research(
        proj_root,
        "## Objective\n\nDo a thing.\n\n"
        "## Acceptance Criteria\n\n- one outcome\n",
    )
    result = api.advance_stage(slug="proj", workspace_root=tmp_path)
    assert result.to_stage == "spec"
