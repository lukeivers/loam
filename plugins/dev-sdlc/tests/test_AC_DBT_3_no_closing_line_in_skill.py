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

"""AC.DBT.3 — No-closing-line-permission-asks reference in
``dispatch-brief-authoring`` SKILL.md.

Per v0.2.2 sub-plan-doc §3 AC.DBT.3 (PROMOTE): the skill names the
no-closing-line-permission-asks rule for sub-agent post-task reports
and references the underlying memory file
``feedback_no_closing_line_permission_asks``.
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


def test_AC_DBT_3_feedback_memory_referenced() -> None:
    """SKILL.md references ``feedback_no_closing_line_permission_asks``."""
    text = _load_skill_text()
    assert "feedback_no_closing_line_permission_asks" in text, (
        "AC.DBT.3: SKILL.md must reference "
        "feedback_no_closing_line_permission_asks as the source rule."
    )


def test_AC_DBT_3_recommendation_is_the_decision_named() -> None:
    """SKILL.md names the 'Recommendation IS the decision' shape."""
    text = _load_skill_text()
    assert "Recommendation IS the decision" in text, (
        "AC.DBT.3: SKILL.md must name 'Recommendation IS the decision' "
        "as the operative phrasing."
    )


def test_AC_DBT_3_want_me_to_negative_example_named() -> None:
    """SKILL.md names the negative example ('want me to...') so the
    rule's surface shape is unambiguous."""
    text = _load_skill_text().lower()
    assert "want me to" in text, (
        "AC.DBT.3: SKILL.md must name the 'want me to...' negative "
        "example so the rule's surface shape is unambiguous."
    )
