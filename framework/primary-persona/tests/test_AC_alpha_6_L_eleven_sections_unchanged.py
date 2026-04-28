"""AC.α.6 — L's eleven sections in prompt.md remain unchanged in shape.

L (the primary-persona-conversational-onboarding-and-default-archetype
amendment, sealed at SEAL_COMMIT 040e577) authored eleven named
sections in
``framework/primary-persona/templates/persona-template/prompt.md``:

  - five top-value-trait headings: Autonomy, Asymmetric problem
    solving, Parallelism, Test theories before acting on them,
    Self-correction.
  - six operational-rule headings: Lean on the harness, Use the
    right tool, Codify what repeats, Structural enforcement
    default, ODD-shaped internal model, Light-touch narration on
    choices.

Per plan §4 AC.α.6, the post-α prompt.md still carries every one
of L's eleven named sections. α adds the Capability leverage spine
and the seventh operational-rule entry "Lean on the corpus"
additively without removing or renaming any L section.

This test mirrors L's
``test_AC_O_1_named_section_count_is_eleven`` shape applied to the
post-α template content.
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATE_PROMPT_MD = (
    REPO_ROOT
    / "framework" / "primary-persona"
    / "templates"
    / "persona-template"
    / "prompt.md"
)


L_ELEVEN_SECTIONS = (
    # five top-value-trait sections.
    "### Autonomy",
    "### Asymmetric problem solving",
    "### Parallelism",
    "### Test theories before acting on them",
    "### Self-correction",
    # six operational-rule sections.
    "### Lean on the harness",
    "### Use the right tool",
    "### Codify what repeats",
    "### Structural enforcement default",
    "### ODD-shaped internal model",
    "### Light-touch narration on choices",
)


def test_AC_alpha_6_all_eleven_L_sections_present():
    """All eleven L-authored section headings remain present."""
    body = TEMPLATE_PROMPT_MD.read_text()
    missing = [h for h in L_ELEVEN_SECTIONS if h not in body]
    assert missing == [], (
        f"L sections missing from post-α prompt.md: {missing}. "
        "α must add additively, never displace L's eleven sections."
    )


def test_AC_alpha_6_L_top_level_sections_present():
    """L's eight top-level (## ) sections are also still present."""
    body = TEMPLATE_PROMPT_MD.read_text()
    L_TOP_LEVEL = (
        "## Identity / Archetype",
        "## Voice",
        "## Seed questions",
        "## Funnel + OARS + reflections",
        "## Pivot rule",
        "## Proposal moment",
        "## Failure-mode guards",
        "## No-expertise-user variant",
        "## Top-value traits",
        "## Operational rules",
    )
    missing = [h for h in L_TOP_LEVEL if h not in body]
    assert missing == [], (
        f"L top-level sections missing: {missing}"
    )


def test_AC_alpha_6_alpha_additions_present_alongside_L_content():
    """α's Capability leverage spine + Lean on the corpus rule sit
    alongside L's content (additive composition)."""
    body = TEMPLATE_PROMPT_MD.read_text()
    assert "## Capability leverage spine" in body
    assert "### Lean on the corpus" in body
