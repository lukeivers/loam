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

"""AC.DBT.6 — No-false-fault-admission reference in
``dispatch-brief-authoring`` SKILL.md.

Per v0.2.2 sub-plan-doc §3 AC.DBT.6 (PROMOTE): the skill names the
no-false-fault rule for sub-agent audit blocks (no manufactured ✗
when no real miss occurred) and references
``feedback_no_false_fault_admission``.
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


def test_AC_DBT_6_feedback_memory_referenced() -> None:
    """SKILL.md references ``feedback_no_false_fault_admission``."""
    text = _load_skill_text()
    assert "feedback_no_false_fault_admission" in text, (
        "AC.DBT.6: SKILL.md must reference "
        "feedback_no_false_fault_admission as the source rule."
    )


def test_AC_DBT_6_four_test_named() -> None:
    """SKILL.md names the four-test before writing audit ✗."""
    text = _load_skill_text().lower()
    assert "four-test" in text, (
        "AC.DBT.6: SKILL.md must name the 'four-test' that gates audit "
        "✗ output."
    )


def test_AC_DBT_6_four_test_dimensions_named() -> None:
    """SKILL.md enumerates at least three of the four-test dimensions
    so the rule's surface shape is unambiguous."""
    text = _load_skill_text().lower()
    dimensions = (
        "upstream input",
        "over-anticipation",
        "prior signals",
        "third-party",
    )
    matched = sum(1 for term in dimensions if term in text)
    assert matched >= 3, (
        "AC.DBT.6: SKILL.md must enumerate at least three of the "
        "four-test dimensions (upstream input clarity / "
        "over-anticipation / ignored prior signals / "
        "third-party-reviewer attribution)."
    )


def test_AC_DBT_6_no_manufactured_x_phrase_named() -> None:
    """SKILL.md names the 'no manufactured ✗' (or equivalent) shape."""
    text = _load_skill_text().lower()
    # Accept either 'manufactured' or 'manufacture' to allow either
    # noun or verb wording.
    assert "manufacture" in text, (
        "AC.DBT.6: SKILL.md must name the 'no manufactured ✗' shape "
        "(or equivalent verb form)."
    )
