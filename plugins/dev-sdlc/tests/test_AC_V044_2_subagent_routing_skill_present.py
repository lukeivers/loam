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

"""AC.V044.2 — ``subagent-routing`` SKILL.md present and content-correct.

Per ``docs/plans/v0-4-4-subagent-personas-routing-and-priming.md``
§4 AC.V044.2: a new SKILL at
``plugins/dev-sdlc/skills/subagent-routing/SKILL.md`` is
discoverable AND its body carries the full routing rubric.

Required substring/structural assertions per the AC:
- A description triggering when the persona is dispatching a
  Task/Agent and the work-shape may match a registered persona.
- A rubric mapping work-shapes → personas: amendment-cycle/build →
  ``loam-builder``; plan-doc authoring → ``loam-plan-author``;
  research/investigation → ``loam-researcher``; sealed-amendment
  review → ``loam-reviewer``; public-facing docs → ``loam-documenter``;
  everything else → ``general-purpose``.
- A note on when to fall back to ``general-purpose`` even when a
  persona-shape matches.
- A reference to ``docs/personas-methodology.md`` for the rubric
  authority.
- A reference to the ``dispatch-brief-authoring`` SKILL for the
  brief-shape extension.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml


SKILL_PATH = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "subagent-routing"
    / "SKILL.md"
)

DESCRIPTION_MAX_CHARS = 1536


def _load_skill() -> tuple[dict, str]:
    assert SKILL_PATH.is_file(), (
        f"AC.V044.2: expected SKILL.md at {SKILL_PATH}; SKILL must "
        "exist at the canonical path."
    )
    text = SKILL_PATH.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", text, re.DOTALL)
    assert match, (
        f"{SKILL_PATH}: SKILL.md must start with YAML frontmatter."
    )
    frontmatter = yaml.safe_load(match.group(1))
    body = match.group(2)
    return frontmatter, body


def test_AC_V044_2_skill_file_exists() -> None:
    assert SKILL_PATH.is_file(), (
        f"AC.V044.2: expected subagent-routing SKILL.md at "
        f"{SKILL_PATH}"
    )


def test_AC_V044_2_skill_frontmatter_valid() -> None:
    frontmatter, _body = _load_skill()
    assert isinstance(frontmatter, dict)
    description = frontmatter.get("description")
    assert isinstance(description, str)
    assert description.strip()
    assert len(description) <= DESCRIPTION_MAX_CHARS, (
        f"subagent-routing: description is {len(description)} chars; "
        f"cap is {DESCRIPTION_MAX_CHARS}."
    )


def test_AC_V044_2_description_triggers_on_dispatch_authoring() -> None:
    """Description names the dispatch-authoring trigger so Claude's
    SKILL discovery loads it at the right time."""
    frontmatter, _body = _load_skill()
    description_lower = frontmatter["description"].lower()
    # The description must name the dispatch-authoring trigger
    # (Task / Agent / dispatch).
    assert "dispatch" in description_lower, (
        "AC.V044.2: description must name 'dispatch' so SKILL "
        "discovery triggers at brief-authoring time."
    )
    # And must reference subagent_type / persona / typed routing.
    assert (
        "subagent_type" in description_lower
        or "persona" in description_lower
    ), (
        "AC.V044.2: description must reference subagent_type or "
        "persona routing."
    )


def test_AC_V044_2_rubric_maps_all_five_personas() -> None:
    """Body carries the work-shape → persona rubric covering all 5
    v0.1.7 personas + the general-purpose fall-back."""
    _frontmatter, body = _load_skill()
    for persona in (
        "loam-builder",
        "loam-plan-author",
        "loam-researcher",
        "loam-reviewer",
        "loam-documenter",
    ):
        assert persona in body, (
            f"AC.V044.2: rubric must map a work-shape to {persona!r}."
        )
    # The general-purpose fall-back is named explicitly.
    assert "general-purpose" in body, (
        "AC.V044.2: body must name 'general-purpose' as the "
        "fall-back routing target."
    )


def test_AC_V044_2_fall_back_clause_present() -> None:
    """Body carries an explicit fall-back-to-general-purpose
    section/clause."""
    _frontmatter, body = _load_skill()
    body_lower = body.lower()
    # The clause is named in a heading or paragraph; we accept either
    # phrasing as long as 'fall' + 'general-purpose' co-occur.
    assert "fall back" in body_lower or "fall-back" in body_lower, (
        "AC.V044.2: body must carry an explicit fall-back-to-"
        "general-purpose clause."
    )


def test_AC_V044_2_references_personas_methodology() -> None:
    """Body cites ``docs/personas-methodology.md`` as the rubric
    authority."""
    _frontmatter, body = _load_skill()
    assert "personas-methodology.md" in body, (
        "AC.V044.2: body must reference docs/personas-methodology.md "
        "as the rubric authority."
    )


def test_AC_V044_2_references_dispatch_brief_authoring_skill() -> None:
    """Body cites the ``dispatch-brief-authoring`` SKILL for the
    brief-shape extension."""
    _frontmatter, body = _load_skill()
    assert "dispatch-brief-authoring" in body, (
        "AC.V044.2: body must reference the dispatch-brief-authoring "
        "SKILL for the brief-shape extension."
    )
