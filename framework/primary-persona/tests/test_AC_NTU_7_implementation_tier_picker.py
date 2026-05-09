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

"""AC.NTU.7 — implementation-tier picker conversation pattern.

Per ``docs/plans/v0-7-0-non-tech-user-surface.md`` AC.NTU.7 (CONDITIONAL
on Q3 = FOLD IN — ratified per dispatch brief):

    (a) tier-ladder doc at docs/implementation-tiers.md (sibling to
    release-process.md); (b) SKILL file at
    framework/primary-persona/skills/implementation-tier-picker/SKILL.md
    (or equivalent path) containing the persona-prompt section + the
    five-tier ladder + the tier-5 risk surfacing template; (c) one
    example onboarding-shaped fixture exercising the tier conversation
    against a fixture ask. Test: golden-fixture probe verifies the
    SKILL surfaces the tier conversation when the user's ask is
    ambiguous between tiers.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TIER_DOC_PATH = REPO_ROOT / "docs" / "implementation-tiers.md"
SKILL_PATH = (
    REPO_ROOT
    / "framework"
    / "primary-persona"
    / "skills"
    / "implementation-tier-picker.md"
)


# ---------------------------------------------------------------------------
# (a) Tier-ladder doc


def test_AC_NTU_7_tier_doc_exists_at_canonical_path() -> None:
    """The tier-ladder doc ships at docs/implementation-tiers.md
    (sibling to release-process.md per the AC).
    """
    assert TIER_DOC_PATH.is_file(), f"tier doc missing at {TIER_DOC_PATH}"


def test_AC_NTU_7_tier_doc_names_all_five_tiers() -> None:
    """The doc enumerates the five tiers per the FIDRAFT entry:
    one-time on-thread / reusable script / local file-based /
    local service-based / external service.
    """
    text = TIER_DOC_PATH.read_text(encoding="utf-8")
    assert "one-time on-thread" in text.lower() or "Tier 1" in text
    assert "reusable script" in text.lower() or "Tier 2" in text
    assert "local file-based" in text.lower() or "Tier 3" in text
    assert "local service-based" in text.lower() or "Tier 4" in text
    assert "external service" in text.lower() or "Tier 5" in text
    # All five tier numbers explicitly named.
    assert "Tier 1" in text
    assert "Tier 2" in text
    assert "Tier 3" in text
    assert "Tier 4" in text
    assert "Tier 5" in text


def test_AC_NTU_7_tier_5_doc_carries_risk_surfacing() -> None:
    """Per the AC + FIDRAFT entry: tier-5 selection requires
    EXCEPTIONALLY clear risk surfacing.
    """
    text = TIER_DOC_PATH.read_text(encoding="utf-8")
    body = text.lower()
    # Risk surfacing names data exposure + auth + ongoing liability.
    assert "data" in body and "expose" in body
    assert "auth" in body
    # Tier-5 conversation has 5 named questions (per the FIDRAFT entry
    # + plan-doc AC.NTU.7's risk surfacing template).
    assert "what data" in body or "data flows" in body
    assert "who can reach" in body
    assert "what auth" in body
    assert "who notices" in body
    assert "who pays" in body or "the bill" in body
    # Most non-tech users should never need tier 5.
    assert "never need" in body or "rarely" in body


# ---------------------------------------------------------------------------
# (b) SKILL file


def test_AC_NTU_7_skill_exists_at_canonical_path() -> None:
    """The SKILL ships at framework/primary-persona/skills/
    per D-NTU.7 default ruling (non-tech users are the primary audience).
    """
    assert SKILL_PATH.is_file(), f"SKILL missing at {SKILL_PATH}"


def test_AC_NTU_7_skill_carries_frontmatter_and_persona_prompt_section() -> None:
    """The SKILL has frontmatter + a persona-prompt section telling
    the persona when + how to surface the tier conversation.
    """
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: implementation-tier-picker" in text
    # Persona-prompt section: "When to surface the tier conversation"
    assert "When to surface the tier conversation" in text
    # Conversation shape: name candidates + cost/capability/risk + ask one question
    assert "Conversation shape" in text


def test_AC_NTU_7_skill_carries_tier_5_risk_surfacing_template() -> None:
    """The SKILL carries the tier-5 risk-surfacing conversation
    template with the named questions.
    """
    text = SKILL_PATH.read_text(encoding="utf-8")
    body = text.lower()
    assert "tier 5 risk surfacing" in body or "tier-5 risk surfacing" in body
    # Five questions per the FIDRAFT entry + plan-doc.
    assert "what data flows" in body
    assert "who can reach" in body
    assert "what auth" in body
    assert "who notices" in body
    assert "who pays" in body or "the bill" in body


def test_AC_NTU_7_skill_carries_example_onboarding_flow() -> None:
    """Per AC.NTU.7 (c): one example onboarding-shaped fixture
    exercising the tier conversation against a fixture ask.
    """
    text = SKILL_PATH.read_text(encoding="utf-8")
    # The skill ships an example onboarding flow as part of its body.
    assert "Example onboarding flow" in text
    # The example exercises the tier conversation against an ambiguous ask.
    body = text.lower()
    assert "expense" in body or "track" in body
    # The example shows the persona naming candidate tiers + asking one question.
    assert "tier 2" in body and "tier 3" in body


def test_AC_NTU_7_skill_documents_when_NOT_to_surface() -> None:
    """The SKILL documents the negative case (when the tier conversation
    is NOT surfaced) so the persona doesn't make every reply a tier
    conversation.
    """
    text = SKILL_PATH.read_text(encoding="utf-8")
    # Negative-case section.
    assert "does NOT surface" in text or "does not surface" in text


# ---------------------------------------------------------------------------
# (c) Composition links


def test_AC_NTU_7_composes_with_light_touch_narration() -> None:
    """Per the AC + FIDRAFT composition note: the tier picker composes
    with the light-touch-narration SKILL — once the tier is picked,
    the choice is narrated.
    """
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "light-touch-narration" in text
