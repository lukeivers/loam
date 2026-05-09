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

"""AC.NTU.1 — light-touch education / ambient narration.

Per ``docs/plans/v0-7-0-non-tech-user-surface.md`` AC.NTU.1:

    A SKILL or persona-prompt section ships at
    ``framework/primary-persona/skills/light-touch-narration/SKILL.md``
    (or equivalent path; new) that names the decision categories that
    trigger narration (modality, specialist, tier, data-model), the
    one-sentence format, and the calibrated lead-phrase set.

This test verifies the SKILL document carries the AC's required
structure — decision categories, format constraint, lead-phrase
set, and verbosity-tunable contract.

The runtime golden-fixture probes (a) + (b) require live ``claude -p``
invocation; the SKILL document is the load-bearing artefact at
build-time, and these tests verify the SKILL captures every named
contract bit. The runtime probes ride along on AC.NTU.6 (outcome-
altitude stranger-clone end-to-end) where the persona is exercised
end-to-end.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_PATH = (
    REPO_ROOT
    / "framework"
    / "primary-persona"
    / "skills"
    / "light-touch-narration.md"
)


def test_AC_NTU_1_skill_exists_at_canonical_path() -> None:
    """The SKILL ships at the conventional primary-persona/skills/
    location alongside memory-search.md + memory-archive.md.
    """
    assert SKILL_PATH.is_file(), f"SKILL missing at {SKILL_PATH}"


def test_AC_NTU_1_skill_carries_frontmatter_with_name_and_description() -> None:
    """SKILL frontmatter declares name + description (the standard
    shape for primary-persona skills).
    """
    text = SKILL_PATH.read_text(encoding="utf-8")
    # Frontmatter present.
    assert text.startswith("---\n")
    # Required frontmatter fields.
    assert "name: light-touch-narration" in text
    assert "description:" in text


def test_AC_NTU_1_skill_names_all_four_decision_categories() -> None:
    """Per AC.NTU.1 ``what``: the SKILL names modality, specialist,
    tier, and data-model as the decision categories that trigger
    narration.
    """
    text = SKILL_PATH.read_text(encoding="utf-8")
    # Lowercase scan to absorb capitalisation variation.
    body = text.lower()
    assert "modality" in body
    assert "specialist" in body
    # Tier OR implementation-tier
    assert "tier" in body
    assert "data-model" in body or "data model" in body


def test_AC_NTU_1_skill_states_one_sentence_format_constraint() -> None:
    """Per AC.NTU.1 ``what``: format is ``exactly one sentence``."""
    text = SKILL_PATH.read_text(encoding="utf-8")
    # "one sentence" appears as the format constraint.
    assert "one sentence" in text.lower() or "one-sentence" in text.lower()


def test_AC_NTU_1_skill_carries_calibrated_lead_phrases() -> None:
    """Per D-NTU.1 ruling: SKILL ships with named lead-phrases for
    first ship.
    """
    text = SKILL_PATH.read_text(encoding="utf-8")
    # The five canonical lead phrases from D-NTU.1.
    assert "I'm doing this as" in text
    assert "I'll set this up as" in text or "I'm going with" in text


def test_AC_NTU_1_skill_documents_negative_case() -> None:
    """Per AC.NTU.1 (b) negative probe: SKILL names what does NOT
    trigger narration (routine action-takes).
    """
    text = SKILL_PATH.read_text(encoding="utf-8")
    body = text.lower()
    # The SKILL explicitly distinguishes routine action-takes that do
    # NOT trigger narration.
    assert "routine action" in body
    # And names "not interruptive" / "not advisory" / "not present on routine"
    assert "not present on routine" in body or "stays silent" in body or "stay silent" in body


def test_AC_NTU_1_skill_documents_verbosity_contract() -> None:
    """Per AC.NTU.1 (c) verbosity-tunable: SKILL describes the three
    levels (terse / default / richer) and the sentence-budget per level.
    """
    text = SKILL_PATH.read_text(encoding="utf-8")
    body = text.lower()
    assert "education_verbosity" in body
    assert "terse" in body
    assert "default" in body
    assert "richer" in body
    # Default = 1 sentence; terse = 0 sentences when uncontested;
    # richer = up to 3.
    assert "1 sentence" in text or "one sentence" in body
    assert "0 sentence" in text or "zero sentence" in body or "0 sentences when" in text
    assert "3 sentence" in text or "three sentence" in body
