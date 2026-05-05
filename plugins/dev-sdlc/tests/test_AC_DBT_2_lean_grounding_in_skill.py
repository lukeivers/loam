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

"""AC.DBT.2 — Lean ODD grounding load reference in
``dispatch-brief-authoring`` SKILL.md.

Per v0.2.2 sub-plan-doc §3 AC.DBT.2 (PROMOTE): the skill names the
load-FIRST directive for ``docs/odd-llm-grounding.lean.md`` on
ODD-shaped sub-agent work, and surfaces the ODD-shaped condition
(extraction / ratification / plan-authoring / AC-tightening /
gap-analysis) so the dispatcher knows when to include the load
directive.
"""

from __future__ import annotations

from pathlib import Path


SKILL_PATH = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "dispatch-brief-authoring"
    / "SKILL.md"
)


def _load_skill_text() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def test_AC_DBT_2_lean_grounding_path_referenced() -> None:
    """SKILL.md references ``docs/odd-llm-grounding.lean.md``."""
    text = _load_skill_text()
    assert "docs/odd-llm-grounding.lean.md" in text, (
        "AC.DBT.2: SKILL.md must reference docs/odd-llm-grounding.lean.md "
        "as the load-FIRST source for ODD-shaped sub-agent work."
    )


def test_AC_DBT_2_load_first_directive_named() -> None:
    """SKILL.md names the load-FIRST directive."""
    text = _load_skill_text()
    assert "FIRST" in text, (
        "AC.DBT.2: SKILL.md must name the 'load FIRST' directive."
    )


def test_AC_DBT_2_self_checks_named() -> None:
    """SKILL.md names the §self-checks discipline that gates ODD outputs."""
    text = _load_skill_text().lower()
    assert "self-checks" in text, (
        "AC.DBT.2: SKILL.md must name the §self-checks discipline run "
        "on every output declared 'objective,' 'AC,' 'constraint,' or "
        "'capability.'"
    )


def test_AC_DBT_2_odd_shaped_condition_named() -> None:
    """SKILL.md names the ODD-shaped condition under which the load
    directive applies (extraction / ratification / plan-authoring /
    AC-tightening / gap-analysis)."""
    text = _load_skill_text().lower()
    # The condition is listed as a comma-or-slash-separated list of
    # ODD-shaped task families. We assert a representative subset to
    # avoid over-coupling to the exact wording while pinning the
    # structural intent.
    for term in ("extraction", "plan-authoring", "gap-analysis"):
        assert term in text, (
            f"AC.DBT.2: SKILL.md must name '{term}' as part of the "
            "ODD-shaped condition that gates the load directive."
        )
