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

"""AC.DBT.4 — Specific-claims-verified reference in
``dispatch-brief-authoring`` SKILL.md.

Per v0.2.2 sub-plan-doc §3 AC.DBT.4 (PROMOTE): the skill names the
specific-claims-verified rule for sub-agent post-task reports and
references ``feedback_specific_claims_verified_or_marked_guess``.
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


def test_AC_DBT_4_feedback_memory_referenced() -> None:
    """SKILL.md references
    ``feedback_specific_claims_verified_or_marked_guess``."""
    text = _load_skill_text()
    assert "feedback_specific_claims_verified_or_marked_guess" in text, (
        "AC.DBT.4: SKILL.md must reference "
        "feedback_specific_claims_verified_or_marked_guess as the "
        "source rule."
    )


def test_AC_DBT_4_verified_or_marked_guess_named() -> None:
    """SKILL.md names the binary outcome — verified OR marked guess."""
    text = _load_skill_text().lower()
    assert "verified" in text, (
        "AC.DBT.4: SKILL.md must name 'verified' as the positive case."
    )
    assert "guess" in text, (
        "AC.DBT.4: SKILL.md must name the 'marked guess/estimate/band' "
        "alternative for unverified facts."
    )


def test_AC_DBT_4_fact_categories_named() -> None:
    """SKILL.md enumerates the kinds of facts the rule covers."""
    text = _load_skill_text().lower()
    # A representative subset of the canonical list (line counts /
    # cost estimates / SHAs / durations / tool-call counts) — pinning
    # too many specific terms would over-couple to wording.
    enumerated = sum(
        1
        for term in (
            "line counts",
            "shas",
            "durations",
            "tool-call counts",
            "cost estimates",
        )
        if term in text
    )
    assert enumerated >= 2, (
        "AC.DBT.4: SKILL.md must enumerate at least two specific "
        "fact-category examples (line counts / SHAs / durations / "
        "tool-call counts / cost estimates)."
    )
