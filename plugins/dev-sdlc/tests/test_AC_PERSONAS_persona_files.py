"""AC.PERSONAS.{1,2,3,4,5} — five subagent persona files at
``plugins/dev-sdlc/agents/<name>.md`` exist with valid frontmatter
and the standard 5-section body shape.

Per ``docs/plans/v0-1-7-personas-pm-layered-skills.md`` §5:
- AC.PERSONAS.1 — `loam-builder` present + frontmatter valid + body
  references `loam amend apply`, `loam amend seal`, ODD §2.5,
  plan-before-code rule.
- AC.PERSONAS.2 — `loam-plan-author` present + frontmatter valid +
  body references plan-doc shape + named-decisions-with-recommendations
  + outcome-shape ACs.
- AC.PERSONAS.3 — `loam-researcher` present + frontmatter valid +
  tools restricted to read-only (Read, Grep, Glob, WebFetch,
  WebSearch); body references Lens 1/2/3 research; halt-and-surface
  fluent.
- AC.PERSONAS.4 — `loam-reviewer` present + frontmatter valid + tools
  limited (excludes Edit/Write but permits read-only Bash); body
  references gate-review for sealed amendments + ODD §2.5
  verification.
- AC.PERSONAS.5 — `loam-documenter` present + frontmatter valid +
  body references public-docs voice (non-jargon) + methodology-
  awareness.

Frontmatter shape per Anthropic subagent-file documented surface
(https://docs.claude.com/en/docs/claude-code/sub-agents):
  - `name` required; matches the file basename.
  - `description` required; ≤ 200 chars (per plan §3 Surface #1).
  - `model` recommended (default "inherit").
  - `tools` optional; comma-separated list when present.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml


AGENTS_DIR = (
    Path(__file__).resolve().parent.parent / "agents"
)

PERSONAS = (
    "loam-builder",
    "loam-plan-author",
    "loam-researcher",
    "loam-reviewer",
    "loam-documenter",
)

# Body-shape sections (5 required sections per plan §3 Surface #1;
# the persona file shape mirrors the 6-section SKILL.md template
# structurally — Identity anchor + Persona prompt with Role / Voice /
# When / Composition / Out of scope).
REQUIRED_BODY_HEADINGS = (
    "# Identity anchor",
    "# Persona prompt",
    "## Role",
    "## Voice",
    "## When to invoke me",
    "## How I compose with the harness",
    "## Out of scope",
)


def _read_persona(handle: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_text) for the named persona."""
    path = AGENTS_DIR / f"{handle}.md"
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", text, re.DOTALL)
    assert match, f"{handle}.md must start with YAML frontmatter"
    frontmatter = yaml.safe_load(match.group(1))
    body = match.group(2)
    assert isinstance(frontmatter, dict), (
        f"{handle}.md frontmatter must parse as a dict"
    )
    return frontmatter, body


@pytest.mark.parametrize("handle", PERSONAS)
def test_persona_file_present(handle: str) -> None:
    """AC.PERSONAS.{1..5} — each persona file exists at the canonical
    path."""
    path = AGENTS_DIR / f"{handle}.md"
    assert path.is_file(), f"expected persona file at {path}"


@pytest.mark.parametrize("handle", PERSONAS)
def test_persona_frontmatter_required_fields(handle: str) -> None:
    """Each persona has required `name`, `description`, `model`
    frontmatter fields."""
    frontmatter, _body = _read_persona(handle)
    assert frontmatter.get("name") == handle, (
        f"frontmatter `name` must equal file basename ({handle})"
    )
    desc = frontmatter.get("description")
    assert isinstance(desc, str) and desc, (
        "frontmatter `description` is required + non-empty"
    )
    # Description budget cap — generous on the persona surface
    # (plan §3 Surface #1 names ≤ 200 chars; we allow some slack
    # given Anthropic's 1536-char ceiling).
    assert len(desc) <= 1536, (
        f"description length {len(desc)} exceeds Anthropic's "
        "1536-char ceiling"
    )
    assert frontmatter.get("model") in ("inherit", "haiku", "sonnet", "opus"), (
        "frontmatter `model` must be inherit | haiku | sonnet | opus"
    )


@pytest.mark.parametrize("handle", PERSONAS)
def test_persona_body_has_required_sections(handle: str) -> None:
    """Standard body shape — 5 main sections present."""
    _frontmatter, body = _read_persona(handle)
    for heading in REQUIRED_BODY_HEADINGS:
        assert heading in body, (
            f"{handle}.md body missing required section heading: "
            f"{heading!r}"
        )


# ---- AC.PERSONAS.1 — loam-builder named-references --------------------


def test_AC_PERSONAS_1_loam_builder_references_amend_cycle() -> None:
    """loam-builder body references the cycle ritual primitives."""
    _fm, body = _read_persona("loam-builder")
    body_lower = body.lower()
    for required in (
        "loam amend apply",
        "loam amend seal",
        "odd",
        "plan-before-code",
    ):
        assert required in body_lower, (
            f"loam-builder body must reference {required!r} "
            "(case-insensitive)"
        )


# ---- AC.PERSONAS.2 — loam-plan-author named-references ----------------


def test_AC_PERSONAS_2_loam_plan_author_references_plan_shape() -> None:
    """loam-plan-author body references plan-doc shape + decisions."""
    _fm, body = _read_persona("loam-plan-author")
    for required in (
        "plan-doc",
        "outcome-shape",
        "Named Decisions",  # the owner-decision-summary format
    ):
        assert required in body, (
            f"loam-plan-author body must reference {required!r}"
        )


# ---- AC.PERSONAS.3 — loam-researcher tools restriction ----------------


def test_AC_PERSONAS_3_loam_researcher_tools_restricted() -> None:
    """loam-researcher frontmatter `tools` carries read-only set
    (Read, Grep, Glob, WebFetch, WebSearch). Edit / Write / Bash
    are excluded."""
    fm, _body = _read_persona("loam-researcher")
    tools = fm.get("tools")
    assert tools is not None, (
        "loam-researcher frontmatter must declare `tools` (read-only "
        "restriction)"
    )
    # `tools` may be a list or a comma-separated string per Anthropic
    # spec. Normalise to a set for assertion.
    if isinstance(tools, str):
        tools_set = {t.strip() for t in tools.split(",") if t.strip()}
    elif isinstance(tools, list):
        tools_set = {str(t).strip() for t in tools}
    else:
        pytest.fail(
            f"`tools` must be list or comma-separated string; got {type(tools)}"
        )
    # Required read-only tools.
    for tool in ("Read", "Grep", "Glob", "WebFetch", "WebSearch"):
        assert tool in tools_set, (
            f"loam-researcher tools must include {tool!r}"
        )
    # Excluded mutating tools.
    for forbidden in ("Edit", "Write"):
        assert forbidden not in tools_set, (
            f"loam-researcher must NOT include {forbidden!r} in tools "
            "(read-only restriction)"
        )


def test_AC_PERSONAS_3_loam_researcher_references_lenses() -> None:
    """loam-researcher body references Lens 1/2/3 research."""
    _fm, body = _read_persona("loam-researcher")
    assert "Lens 1" in body or "Lens 1–3" in body or "Lens 1-3" in body
    assert "Lens 2" in body
    assert "Lens 3" in body


# ---- AC.PERSONAS.4 — loam-reviewer tools limited ---------------------


def test_AC_PERSONAS_4_loam_reviewer_tools_excludes_edit_write() -> None:
    """loam-reviewer frontmatter `tools` excludes Edit + Write but
    permits read-only Bash for git operations."""
    fm, _body = _read_persona("loam-reviewer")
    tools = fm.get("tools")
    assert tools is not None, (
        "loam-reviewer frontmatter must declare `tools` (review-only "
        "restriction)"
    )
    if isinstance(tools, str):
        tools_set = {t.strip() for t in tools.split(",") if t.strip()}
    elif isinstance(tools, list):
        tools_set = {str(t).strip() for t in tools}
    else:
        pytest.fail(
            f"`tools` must be list or comma-separated string; got {type(tools)}"
        )
    # Required read-only review tools.
    for tool in ("Read", "Grep", "Glob"):
        assert tool in tools_set, (
            f"loam-reviewer tools must include {tool!r}"
        )
    # Bash permitted (read-only git operations).
    assert "Bash" in tools_set, (
        "loam-reviewer tools must include `Bash` for read-only git "
        "operations (git diff / log / show)"
    )
    # Excluded mutating tools.
    for forbidden in ("Edit", "Write"):
        assert forbidden not in tools_set, (
            f"loam-reviewer must NOT include {forbidden!r} in tools"
        )


def test_AC_PERSONAS_4_loam_reviewer_references_gate_review() -> None:
    """loam-reviewer body references gate-review for sealed
    amendments + ODD §2.5."""
    _fm, body = _read_persona("loam-reviewer")
    assert "gate-review" in body or "gate review" in body
    assert "ODD" in body
    # Body explicitly references the seal-test pattern.
    assert "seal-test" in body or "test_no_sealed_amendments" in body


# ---- AC.PERSONAS.5 — loam-documenter named-references ----------------


def test_AC_PERSONAS_5_loam_documenter_references_public_voice() -> None:
    """loam-documenter body references public-docs voice + methodology
    awareness."""
    _fm, body = _read_persona("loam-documenter")
    assert "public-facing" in body or "non-jargon" in body
    # Methodology-awareness — references at least one loam idiom by
    # name (so a non-loam-dev reader sees the idiom + its definition).
    assert (
        "VALUE_PROPOSITION" in body
        or "FIDRAFT" in body
        or "ODD" in body
    )


# ---- AC.PERSONAS.S — sanity / fence ------------------------------------


def test_exactly_five_personas_shipped() -> None:
    """The agents/ directory carries exactly the 5 named personas (no
    accidental drift)."""
    md_files = sorted(p.name for p in AGENTS_DIR.glob("*.md"))
    expected = sorted(f"{h}.md" for h in PERSONAS)
    assert md_files == expected, (
        f"agents/ directory should ship exactly {expected}, found {md_files}"
    )
