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

"""AC.O.1 — Default archetype prose lives at the framework template.

The framework template
``primary-persona/templates/persona-template/prompt.md`` carries
default archetype prose with the named structural sections
present:

  - Identity / Archetype
  - Voice
  - three seed questions (D1)
  - funnel + OARS + 2-reflections-per-question (D3)
  - 3-of-5 pivot rule with all five conditions (D4)
  - Proposal moment template (D5: reflect-back + 2–3 candidates +
    closing question)
  - Failure-mode guards (D7)
  - No-expertise-user variant (D6)
  - five top-value-trait sections — Autonomy, Asymmetric problem
    solving, Parallelism, Test theories before acting on them,
    Self-correction
  - eight operational-rule sections — Acknowledge first on non-
    trivial requests, Lean on the harness, Use the right tool,
    Codify what repeats, Structural enforcement default, ODD-shaped
    internal model, Light-touch narration on choices, Lean on the
    corpus

The template carries the ``{user_preferred_name}`` and
``{persona_given_name}`` substitution tokens (str.format-compatible)
so AC.O.4's write-back substitution lands user-chosen names without
template editing.

Operational-rule count history:
  - L (sealed at 040e577): 6 operational rules.
  - α (sealed): added "Lean on the corpus" → 7 operational rules.
    Test count was not widened in α (pre-existing AC drift; surfaced
    by v0.1.2 item 5).
  - v0.1.2 item 5 (ack-first persona contract amendment): adds
    "Acknowledge first on non-trivial requests" → 8 operational
    rules; widens the count assertions in lock-step (composes the
    new addition with the α drift fix).

Plan: docs/plans/primary-persona-conversational-onboarding-and-default-archetype.md
v0.1.2 item 5 plan: docs/plans/v0-1-2-ack-first-persona-contract.md
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


def _body() -> str:
    return TEMPLATE_PROMPT_MD.read_text()


def test_AC_O_1_template_prompt_md_exists():
    """The template prompt.md is present at the framework path."""
    assert TEMPLATE_PROMPT_MD.is_file()
    assert _body().strip() != ""


def test_AC_O_1_identity_or_archetype_section_present():
    """An Identity / Archetype section names the eager-new-hire
    chief-of-staff voice."""
    body = _body()
    # Either heading is acceptable; both can be present.
    assert (
        "## Identity" in body
        or "## Archetype" in body
        or "## Identity / Archetype" in body
    )
    # The eager-new-hire chief-of-staff voice is named.
    lower = body.lower()
    assert "eager" in lower or "new-hire" in lower or "new hire" in lower
    assert "chief-of-staff" in lower or "chief of staff" in lower


def test_AC_O_1_voice_section_present():
    body = _body()
    assert "## Voice" in body


def test_AC_O_1_three_seed_questions_present():
    """The template names the three seed questions (D1).

    Detected by distinctive substring markers the builder commits
    to. The phrasing is the builder's call provided each marker
    appears verbatim. The template was authored with exactly these
    three markers; future edits that change them must update both
    the template and this test in lock-step.
    """
    body = _body()
    seed_markers = (
        "Walk me through your day",
        "take pressure off",
        "how you operate",
    )
    for marker in seed_markers:
        assert marker in body, f"seed-question marker {marker!r} missing"


def test_AC_O_1_funnel_oars_two_reflections_section_present():
    """The funnel + OARS + 2-reflections-per-question section is
    present (D3)."""
    body = _body()
    assert "Funnel" in body
    # OARS pattern named explicitly
    assert "OARS" in body
    # The 2-reflections-per-question ratio is named (some
    # spelling form — "two reflections per question" or
    # "2 reflections per question").
    lower = body.lower()
    assert (
        "two reflections per question" in lower
        or "2 reflections per question" in lower
    ), "2-reflections-per-question ratio not named"


def test_AC_O_1_pivot_rule_section_with_five_conditions_present():
    """The 3-of-5 pivot rule with five conditions is present (D4)."""
    body = _body()
    assert "Pivot rule" in body
    # The phrase "3" + "5" near each other (the 3-of-5 framing).
    lower = body.lower()
    assert "three" in lower or "3" in body
    assert "five" in lower or "5" in body
    # Locate the pivot section + count enumerated 1–5 items
    # under it.
    pivot_idx = body.find("Pivot rule")
    assert pivot_idx >= 0
    # Read forward until next ``## `` heading or the next ``##``.
    next_heading_idx = body.find("\n## ", pivot_idx + 10)
    if next_heading_idx < 0:
        next_heading_idx = len(body)
    pivot_section = body[pivot_idx:next_heading_idx]
    # Count distinct enumerated bullets ``1.`` through ``5.``.
    for n in range(1, 6):
        marker = f"\n{n}."
        assert marker in pivot_section, (
            f"pivot rule condition {n} missing from Pivot rule section"
        )


def test_AC_O_1_proposal_moment_section_present():
    """The proposal-moment template (reflect-back + 2–3 candidates +
    closing question, per D5) is present."""
    body = _body()
    assert "Proposal moment" in body
    proposal_idx = body.find("Proposal moment")
    next_heading_idx = body.find("\n## ", proposal_idx + 10)
    if next_heading_idx < 0:
        next_heading_idx = len(body)
    proposal_section = body[proposal_idx:next_heading_idx]
    lower = proposal_section.lower()
    # Reflect-back, 2-3 deliverables, closing question.
    assert "reflect" in lower
    assert "2" in proposal_section or "two" in lower or "three" in lower
    # The closing question or its essence.
    assert "?" in proposal_section


def test_AC_O_1_failure_mode_guards_section_present():
    """The failure-mode guards section (per D7) is present."""
    body = _body()
    assert "Failure-mode guards" in body or "Failure mode guards" in body


def test_AC_O_1_no_expertise_user_variant_section_present():
    """The no-expertise-user variant section (per D6) is present."""
    body = _body()
    assert "No-expertise-user" in body or "no-expertise-user" in body.lower()


def test_AC_O_1_five_top_value_trait_sections_present():
    """All five top-value-trait sections are present."""
    body = _body()
    traits = (
        "### Autonomy",
        "### Asymmetric problem solving",
        "### Parallelism",
        "### Test theories before acting on them",
        "### Self-correction",
    )
    for trait_heading in traits:
        assert trait_heading in body, (
            f"top-value trait section {trait_heading!r} missing from template prompt.md"
        )


def test_AC_O_1_eight_operational_rule_sections_present():
    """All eight operational-rule sections are present.

    Composes L's six (sealed at 040e577), α's "Lean on the corpus"
    addition, and v0.1.2 item 5's "Acknowledge first on non-trivial
    requests" addition (per AC.VPC.5.2). The α addition was not
    reflected in the prior test count (pre-existing AC drift); v0.1.2
    item 5's lock-step widening from 6→8 fixes the drift in-band per
    feedback_loose_AC_text_fix_AC_not_implementation.
    """
    body = _body()
    rules = (
        "### Acknowledge first on non-trivial requests",
        "### Lean on the harness",
        "### Use the right tool",
        "### Codify what repeats",
        "### Structural enforcement default",
        "### ODD-shaped internal model",
        "### Light-touch narration on choices",
        "### Lean on the corpus",
    )
    for rule_heading in rules:
        assert rule_heading in body, (
            f"operational-rule section {rule_heading!r} missing from template prompt.md"
        )


def test_AC_O_1_named_section_count_is_thirteen():
    """Five trait sections + eight rule sections == thirteen named
    sections total.

    History:
      - L (sealed 040e577): 5 traits + 6 rules == 11.
      - α: + "Lean on the corpus" → 5 + 7 == 12 (test count not
        widened — pre-existing drift).
      - v0.1.2 item 5: + "Acknowledge first on non-trivial requests"
        → 5 + 8 == 13. Test count widened in lock-step (AC.VPC.5.2).
    """
    body = _body()
    thirteen = (
        "### Autonomy",
        "### Asymmetric problem solving",
        "### Parallelism",
        "### Test theories before acting on them",
        "### Self-correction",
        "### Acknowledge first on non-trivial requests",
        "### Lean on the harness",
        "### Use the right tool",
        "### Codify what repeats",
        "### Structural enforcement default",
        "### ODD-shaped internal model",
        "### Light-touch narration on choices",
        "### Lean on the corpus",
    )
    present = sum(1 for h in thirteen if h in body)
    assert present == 13, (
        f"expected all 13 named-section headers present; "
        f"found {present}"
    )


def test_AC_O_1_substitution_tokens_present():
    """Both ``{user_preferred_name}`` and ``{persona_given_name}``
    tokens appear at least once."""
    body = _body()
    assert "{user_preferred_name}" in body
    assert "{persona_given_name}" in body


def test_AC_O_1_template_is_str_format_compatible():
    """The template body can pass through ``str.format`` without
    raising — every literal ``{`` / ``}`` outside the two named
    tokens is properly escaped, so the AC.O.4 write-back's
    rendering step works."""
    body = _body()
    rendered = body.format(
        user_preferred_name="Luke",
        persona_given_name="Mara",
    )
    assert "Luke" in rendered
    assert "Mara" in rendered
    assert "{user_preferred_name}" not in rendered
    assert "{persona_given_name}" not in rendered
