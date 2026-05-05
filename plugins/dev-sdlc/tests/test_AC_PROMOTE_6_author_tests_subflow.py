"""AC.PROMOTE.6 — Author-tests-for-promotions sub-flow.

Per v0.2.1 Cycle 2 plan-doc §3 AC.PROMOTE.6: when an owner-Y
candidate has Tests=NEEDS-TESTS, the SKILL body instructs the
persona to dispatch a sub-agent (per `dispatch-brief-authoring`
shape) to author the AC-shaped structural test under
`plugins/<target>/tests/` mirroring the
`test_AC_SKILLS_DSDLC1_*` template (frontmatter + body +
key-terms checks).
"""

from __future__ import annotations

import re
from pathlib import Path


SKILL_PATH = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "skill-promotion-review"
    / "SKILL.md"
)


def _body() -> str:
    text = SKILL_PATH.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", text, re.DOTALL)
    assert match, f"{SKILL_PATH}: frontmatter parse failed."
    return match.group(2)


def test_body_mentions_sub_agent_dispatch_for_tests() -> None:
    """Body must instruct the persona to dispatch a sub-agent for
    test authoring."""
    body = _body()
    body_lower = body.lower()
    assert "sub-agent" in body_lower or "subagent" in body_lower, (
        "skill-promotion-review: body must mention dispatching a "
        "`sub-agent` for test authoring."
    )
    assert "dispatch" in body_lower, (
        "skill-promotion-review: body must use the word `dispatch` "
        "framing the sub-agent invocation."
    )


def test_body_references_dispatch_brief_authoring() -> None:
    """The sub-agent dispatch follows the `dispatch-brief-authoring`
    SKILL's shape (composition reference)."""
    body = _body()
    assert "dispatch-brief-authoring" in body, (
        "skill-promotion-review: body must reference the "
        "`dispatch-brief-authoring` SKILL as the dispatch-brief "
        "shape source."
    )


def test_body_mentions_structural_test_convention() -> None:
    """Body must mention the structural-test convention from
    test_AC_SKILLS_DSDLC1_* (frontmatter + body + key-terms)."""
    body = _body()
    body_lower = body.lower()
    assert "frontmatter" in body_lower, (
        "skill-promotion-review: body must mention the structural-"
        "test `frontmatter` check."
    )
    assert "body" in body_lower, (
        "skill-promotion-review: body must mention the structural-"
        "test `body` check."
    )
    assert "key-term" in body_lower or "key term" in body_lower, (
        "skill-promotion-review: body must mention the structural-"
        "test `key-term` check."
    )


def test_body_mentions_test_file_path_convention() -> None:
    """Body must mention the test-file path convention under
    `plugins/<target>/tests/test_AC_SKILLS_*_<skill_name>_skill_present.py`
    (mirroring the dev-sdlc precedent)."""
    body = _body()
    assert "tests/" in body, (
        "skill-promotion-review: body must mention the `tests/` "
        "directory placement for the AC-shaped test."
    )
    assert "test_AC_SKILLS" in body, (
        "skill-promotion-review: body must mention the "
        "`test_AC_SKILLS_*` test-file naming convention."
    )
