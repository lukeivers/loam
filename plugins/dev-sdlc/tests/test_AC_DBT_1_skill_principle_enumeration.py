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

"""AC.DBT.1 — ``dispatch-brief-authoring`` SKILL.md enumerates the
propagated principle set.

Per v0.2.2 sub-plan-doc §3 AC.DBT.1: the skill's "Principles to apply
at turn-start" section is extended with a "Propagated principles for
sub-agents" sub-section enumerating each promoted principle by name
(AC.DBT.2 → AC.DBT.6).

Test home — ``plugins/dev-sdlc/tests/`` per the sibling
``test_AC_SKILLS_DSDLC1_2_*.py`` precedent (skill-related tests live
at the plugin level, not co-located with the skill).
"""

from __future__ import annotations

import re
from pathlib import Path


SKILL_PATH = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "dispatch-brief-authoring"
    / "SKILL.md"
)


def _load_skill_body() -> str:
    text = SKILL_PATH.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", text, re.DOTALL)
    assert match, f"SKILL.md must start with YAML frontmatter at {SKILL_PATH}"
    return match.group(2)


def test_AC_DBT_1_propagated_principles_subsection_present() -> None:
    """The skill body contains a "Propagated principles for sub-agents"
    sub-section (AC.DBT.1)."""
    body = _load_skill_body()
    assert "Propagated principles for sub-agents" in body, (
        "AC.DBT.1: SKILL.md must contain a "
        "'Propagated principles for sub-agents' sub-section."
    )


def test_AC_DBT_1_each_promoted_ac_named() -> None:
    """Each AC.DBT.2–6 ID appears in the SKILL.md body so the link
    between the skill and the locking AC is structural."""
    body = _load_skill_body()
    for ac_id in ("AC.DBT.2", "AC.DBT.3", "AC.DBT.4", "AC.DBT.5", "AC.DBT.6"):
        assert ac_id in body, (
            f"AC.DBT.1: SKILL.md must reference {ac_id} in the "
            "propagated-principles sub-section."
        )
