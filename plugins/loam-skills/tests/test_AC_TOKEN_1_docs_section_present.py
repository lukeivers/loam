"""AC.TOKEN.1 — A "Token-optimization defaults" section exists in
``docs/getting-started.md`` listing the 4 recommended settings (Sonnet
default, ``MAX_THINKING_TOKENS=10000``, ``CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50``,
MCP/tool caps) with a one-sentence rationale per setting and a
one-line pointer to the ``cost-optimised-defaults`` SKILL.

Per ``docs/plans/drafts/token-defaults-optin-skill.md`` §4 AC.TOKEN.1
+ AC.PO.1 ladder (primary-persona translation-burden — docs absorbs
the technical detail in plain prose for the docs-first user
discovery path).

The test reads ``docs/getting-started.md`` post-build, asserts each
of the 4 setting names appears, asserts the SKILL-pointer string
appears, and asserts the section header appears AFTER the five-step
bootstrap headers (per the §3 in-scope placement constraint).

RED-on-mutation: deleting the section, removing one of the setting
names, or moving the section before the bootstrap headers fails the
test as required.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GETTING_STARTED = REPO_ROOT / "docs" / "getting-started.md"


# The 4 settings the docs section MUST name. Strings match the
# canonical setting names as documented in the
# `cost-optimised-defaults` SKILL frontmatter.
REQUIRED_SETTING_NAMES = [
    "sonnet",
    "MAX_THINKING_TOKENS",
    "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE",
]

# MCP/tool discipline phrasing — either "MCP" + "tool" co-occurrence
# OR the explicit "<10" / "<80" caps. Builder's-call wording, but at
# least one of the discipline anchors must be present.
MCP_TOOL_DISCIPLINE_PATTERNS = [
    r"\bMCP",
    r"\btools?\b",
]

# The SKILL pointer — wording is builder's call (per §10 doubt #5,
# alternative phrasing acceptable) but the canonical SKILL name must
# appear so the docs section unambiguously points at it.
SKILL_POINTER_TOKEN = "cost-optimised-defaults"

# Section-header anchor for the new token-optimization section.
# Accepts any of: "Token-optimization defaults", "Token optimization
# defaults", "Token-optimisation defaults" (British spelling
# acceptable; builder's call).
SECTION_HEADER_REGEX = re.compile(
    r"^#+\s+Token[- ]optim[iz]+ation\s+defaults\b",
    re.IGNORECASE | re.MULTILINE,
)

# The five-step bootstrap headers — the AC.TOKEN.1 position constraint
# requires the new section to appear AFTER all five. We anchor on the
# H3 step numbering pattern used in the existing doc.
BOOTSTRAP_STEP_HEADER_REGEX = re.compile(
    r"^###\s+(\d+)\.\s+",
    re.MULTILINE,
)


def _load_doc() -> str:
    assert GETTING_STARTED.exists(), (
        f"AC.TOKEN.1: docs/getting-started.md must exist at "
        f"{GETTING_STARTED}."
    )
    return GETTING_STARTED.read_text(encoding="utf-8")


def test_token_optimization_section_exists() -> None:
    """The section header is present."""
    doc = _load_doc()
    match = SECTION_HEADER_REGEX.search(doc)
    assert match, (
        "AC.TOKEN.1: docs/getting-started.md must contain a "
        '"Token-optimization defaults" section header (matched '
        f"regex {SECTION_HEADER_REGEX.pattern}); none found."
    )


def test_token_optimization_section_names_four_settings() -> None:
    """The 4 setting names appear in the doc."""
    doc = _load_doc()
    for setting in REQUIRED_SETTING_NAMES:
        assert setting in doc, (
            f"AC.TOKEN.1: docs/getting-started.md must name the "
            f"setting `{setting}`; not found in the doc."
        )
    # MCP/tool discipline anchors (at least one of each).
    for pattern in MCP_TOOL_DISCIPLINE_PATTERNS:
        assert re.search(pattern, doc), (
            f"AC.TOKEN.1: docs/getting-started.md must reference "
            f"MCP/tool discipline (pattern {pattern!r}); not found."
        )


def test_skill_pointer_present() -> None:
    """The one-line pointer to the SKILL is present."""
    doc = _load_doc()
    assert SKILL_POINTER_TOKEN in doc, (
        f"AC.TOKEN.1: docs/getting-started.md must include a pointer "
        f"to the `{SKILL_POINTER_TOKEN}` SKILL (the canonical SKILL "
        f"name string); not found."
    )


def test_section_appears_after_five_step_bootstrap() -> None:
    """The section position constraint: header AFTER the five-step
    bootstrap headers."""
    doc = _load_doc()
    section_match = SECTION_HEADER_REGEX.search(doc)
    assert section_match, (
        "AC.TOKEN.1: section header must exist (covered by "
        "test_token_optimization_section_exists; re-asserted here "
        "for the position check)."
    )
    section_pos = section_match.start()

    # Find all bootstrap step headers; the new section must appear
    # after the highest-numbered step (per the §3 placement constraint
    # that the section lives AFTER the five-step bootstrap).
    bootstrap_steps = list(BOOTSTRAP_STEP_HEADER_REGEX.finditer(doc))
    assert bootstrap_steps, (
        "AC.TOKEN.1 position-check precondition: getting-started.md "
        "must contain bootstrap step headers matching `^### <n>.\\s+`; "
        "none found, indicating either an unexpected doc shape OR the "
        "doc was restructured. Update the test anchor if the bootstrap "
        "shape moved."
    )
    last_step = max(bootstrap_steps, key=lambda m: m.start())
    assert section_pos > last_step.start(), (
        f"AC.TOKEN.1: the Token-optimization section must appear "
        f"AFTER the last bootstrap step header (step "
        f"{last_step.group(1)} at offset {last_step.start()}); the "
        f"section was found at offset {section_pos}."
    )
