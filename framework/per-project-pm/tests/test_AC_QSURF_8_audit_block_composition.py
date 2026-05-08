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

"""AC.QSURF.8 — Composition with `audit-block-on-telegram` SKILL.

Per cycle-4 plan §4 + §5 Surface #5 + §5 Surface #7 + AC.QSURF.8:

  - SurfacedQuestion + RecordedResponse expose
    is_audit_block_trigger=True.
  - framework/per-project-pm/docs/design.md §12 references the SKILL
    by exact path + names the "decision was made" trigger condition.
  - The SKILL.md file at the referenced path actually exists and
    contains the named trigger condition string.
"""

from __future__ import annotations

from pathlib import Path

from loam.per_project_pm.runtime import PMRuntime
from loam.per_project_pm.state import RecordedResponse, SurfacedQuestion


_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_DESIGN_NOTE = (
    _REPO_ROOT
    / "framework"
    / "per-project-pm"
    / "docs"
    / "design.md"
)
_SKILL_PATH = (
    _REPO_ROOT
    / "plugins"
    / "loam-skills"
    / "skills"
    / "audit-block-on-telegram"
    / "SKILL.md"
)


def test_SurfacedQuestion_exposes_is_audit_block_trigger() -> None:
    """The class itself exposes the property (introspection without
    instantiation)."""
    assert hasattr(SurfacedQuestion, "is_audit_block_trigger")


def test_SurfacedQuestion_is_audit_block_trigger_returns_True(
    authored_pm: tuple[Path, str],
) -> None:
    workspace_root, pm_name = authored_pm
    runtime = PMRuntime.from_workspace(workspace_root, pm_name)
    runtime.enqueue_decision("Q1")
    surfaced = runtime.surface_next_question()
    assert surfaced is not None
    assert surfaced.is_audit_block_trigger is True


def test_RecordedResponse_exposes_is_audit_block_trigger() -> None:
    """The class itself exposes the property."""
    assert hasattr(RecordedResponse, "is_audit_block_trigger")


def test_RecordedResponse_is_audit_block_trigger_returns_True(
    authored_pm: tuple[Path, str],
) -> None:
    workspace_root, pm_name = authored_pm
    runtime = PMRuntime.from_workspace(workspace_root, pm_name)
    runtime.enqueue_decision("Q1")
    surfaced = runtime.surface_next_question()
    assert surfaced is not None
    response = runtime.record_response(surfaced.audit_path, "A1")
    assert response.is_audit_block_trigger is True


def test_design_note_references_audit_block_skill_by_exact_path() -> None:
    """docs/design.md must reference the SKILL by exact path so the
    cross-reference is unambiguous."""
    text = _DESIGN_NOTE.read_text(encoding="utf-8")
    assert (
        "plugins/loam-skills/skills/audit-block-on-telegram/" in text
    ), "design.md missing exact path to audit-block-on-telegram SKILL"


def test_design_note_names_decision_was_made_trigger() -> None:
    """The design-note must name the SKILL's 'decision was made'
    trigger condition string explicitly — that's the linkage the
    composition contract is built on."""
    text = _DESIGN_NOTE.read_text(encoding="utf-8")
    assert "decision was made" in text, (
        "design.md missing the named SKILL trigger condition string"
    )


def test_skill_md_file_exists_at_referenced_path() -> None:
    """The cross-reference would be a lie if the SKILL.md doesn't
    exist at the named path. Fail-loud on missing skill."""
    assert _SKILL_PATH.exists(), (
        f"audit-block-on-telegram SKILL.md missing at {_SKILL_PATH}"
    )


def test_skill_md_contains_decision_was_made_trigger() -> None:
    """The SKILL itself must contain the 'decision was made' trigger
    condition string the composition contract names. If the SKILL
    drifts away from that wording in a future v0.1.6+ amendment, this
    test surfaces the drift so the composition is repaired before
    landing.
    """
    text = _SKILL_PATH.read_text(encoding="utf-8")
    assert "decision was made" in text.lower(), (
        "audit-block-on-telegram SKILL.md missing 'decision was made' "
        "trigger condition string"
    )


def test_property_docstring_references_audit_block_skill() -> None:
    """The property's docstring must name the SKILL — composition is
    discoverable from `help(SurfacedQuestion.is_audit_block_trigger)`."""
    sq_doc = SurfacedQuestion.is_audit_block_trigger.fget.__doc__ or ""
    rr_doc = RecordedResponse.is_audit_block_trigger.fget.__doc__ or ""
    for doc in (sq_doc, rr_doc):
        assert "audit-block-on-telegram" in doc
        assert "decision was made" in doc
