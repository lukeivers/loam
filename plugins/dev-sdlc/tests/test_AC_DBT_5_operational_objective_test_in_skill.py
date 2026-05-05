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

"""AC.DBT.5 — Test-against-operational-objective-before-escalating
reference in ``dispatch-brief-authoring`` SKILL.md.

Per v0.2.2 sub-plan-doc §3 AC.DBT.5 (PROMOTE): the skill names the
operational-objective test for sub-agent escalation/non-escalation
calls and references
``feedback_test_against_operational_objective_before_escalating``.
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


def test_AC_DBT_5_feedback_memory_referenced() -> None:
    """SKILL.md references
    ``feedback_test_against_operational_objective_before_escalating``."""
    text = _load_skill_text()
    assert (
        "feedback_test_against_operational_objective_before_escalating"
        in text
    ), (
        "AC.DBT.5: SKILL.md must reference "
        "feedback_test_against_operational_objective_before_escalating "
        "as the source rule."
    )


def test_AC_DBT_5_operational_objective_phrase_named() -> None:
    """SKILL.md names the 'operational objective' phrase."""
    text = _load_skill_text().lower()
    assert "operational objective" in text, (
        "AC.DBT.5: SKILL.md must name the 'operational objective' "
        "phrase that anchors the test."
    )


def test_AC_DBT_5_escalation_floor_named() -> None:
    """SKILL.md names the escalation floor — critical-call /
    public-action / financial decisions are the only escalation
    triggers."""
    text = _load_skill_text().lower()
    floor_terms = ("critical-call", "public-action", "financial")
    matched = sum(1 for term in floor_terms if term in text)
    assert matched >= 2, (
        "AC.DBT.5: SKILL.md must name at least two of the escalation-"
        "floor categories (critical-call / public-action / financial)."
    )
