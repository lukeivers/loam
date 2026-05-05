"""AC.PROMOTE.4 — Walk-workspace logic specified in SKILL body.

Per v0.2.1 Cycle 2 plan-doc §3 AC.PROMOTE.4: the SKILL body
instructs the persona to read `<workspace>/.claude/skills/`,
treat each subdirectory containing a SKILL.md as a candidate,
handle the empty-workspace case cleanly, render a structured
table to the workspace's `.scratch/claude-output/` path, and
recognise pointer.md replacements (already-graduated; skip).
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


def test_body_mentions_walk_claude_skills_directory() -> None:
    """Body must mention reading `<workspace>/.claude/skills/`."""
    body = _body()
    assert ".claude/skills/" in body, (
        "skill-promotion-review: body must mention reading "
        "`<workspace>/.claude/skills/` to enumerate candidate SKILLs."
    )


def test_body_mentions_empty_workspace_handling() -> None:
    """Body must handle the empty-workspace case: surface a clean
    message and exit, never error."""
    body = _body()
    body_lower = body.lower()
    assert "no workspace-local skills found" in body_lower, (
        "skill-promotion-review: body must surface the literal "
        "'no workspace-local SKILLs found' message when the "
        "workspace's .claude/skills/ is empty."
    )
    # Acceptance: body mentions exit-cleanly behavior (acceptable
    # synonyms: "exit cleanly" / "exit clean" / "exits cleanly").
    assert (
        "exit cleanly" in body_lower
        or "exits cleanly" in body_lower
        or "exit clean" in body_lower
    ), (
        "skill-promotion-review: body must specify clean-exit "
        "(not error) when the workspace is empty."
    )


def test_body_mentions_scratch_output_path() -> None:
    """Body must specify the canonical scratch-output artefact
    path: `<workspace>/.scratch/claude-output/skill-promotion-review-<date>.md`."""
    body = _body()
    assert ".scratch/claude-output/" in body, (
        "skill-promotion-review: body must specify the canonical "
        "scratch-output path `<workspace>/.scratch/claude-output/`."
    )
    assert "skill-promotion-review-" in body, (
        "skill-promotion-review: body must name the artefact "
        "filename pattern `skill-promotion-review-<date>.md`."
    )


def test_body_mentions_pointer_md_skip_already_graduated() -> None:
    """Body must instruct the persona to skip already-graduated
    SKILLs (single-line `pointer.md` markers replacing the
    workspace-local SKILL.md after promotion). Avoids
    double-evaluation in steady-state re-runs."""
    body = _body()
    body_lower = body.lower()
    assert "pointer" in body_lower, (
        "skill-promotion-review: body must mention pointer "
        "(graduation marker) to skip already-graduated SKILLs."
    )
    assert "graduated" in body_lower, (
        "skill-promotion-review: body must mention `graduated` to "
        "frame the pointer.md as a graduation marker."
    )


def test_body_describes_per_candidate_table_output() -> None:
    """Body must specify per-candidate signal-evaluation +
    structured table output."""
    body = _body()
    body_lower = body.lower()
    assert "table" in body_lower, (
        "skill-promotion-review: body must describe rendering a "
        "structured table per-candidate."
    )
    assert "candidate" in body_lower, (
        "skill-promotion-review: body must frame each evaluated "
        "SKILL as a `candidate`."
    )
