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

"""AC.O.6 — Default contract template is loadable on session 1
with archetype-aligned prose.

The framework template
``primary-persona/templates/persona-template/contract.yaml``
parses through ``load_contract`` to a valid ``PersonaContract``
without modification beyond the scaffold's existing
``handle`` + ``is_starter`` mutations. The loaded contract carries
non-placeholder prose for ``responsibilities.context_holder``,
``responsibilities.escalation_judge``, and
``responsibilities.single_point_of_contact`` — none of the strings
is the literal "Describe, in one sentence, …" prompt text the
prior template carried. ``dev_intent`` is ``"unanswered"``.
``is_primary`` is ``true``. ``tier_d`` is ``defer`` (per the
archetype's chief-of-staff register).

Plan: docs/rebuild/plans/primary-persona-conversational-onboarding-and-default-archetype.md
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam.primary_persona.agent_md import to_agent_md
from loam.primary_persona.contract import PersonaContract, TierAction


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATE_DIR = (
    REPO_ROOT / "framework" / "primary-persona" / "templates" / "persona-template"
)
TEMPLATE_CONTRACT = TEMPLATE_DIR / "contract.yaml"


def _load_template_with_scaffold_mutations() -> PersonaContract:
    """Load the template + apply the scaffold's mutations
    (``handle`` + ``is_starter=True``)."""
    raw = yaml.safe_load(TEMPLATE_CONTRACT.read_text())
    raw["handle"] = "iris"
    raw["is_starter"] = True
    return PersonaContract.model_validate(raw)


def test_AC_O_6_template_parses_after_scaffold_mutation():
    """The template loads to a valid PersonaContract after the
    scaffold's two mutations."""
    contract = _load_template_with_scaffold_mutations()
    assert contract.handle == "iris"
    assert contract.is_starter is True


def test_AC_O_6_responsibilities_are_non_placeholder():
    """All three responsibilities-prose fields are non-empty and
    do not start with the prior template's "Describe, in one
    sentence" placeholder."""
    contract = _load_template_with_scaffold_mutations()
    for field in ("single_point_of_contact", "context_holder", "escalation_judge"):
        prose = getattr(contract.responsibilities, field)
        assert prose.strip()
        assert not prose.lstrip().lower().startswith("describe, in one sentence"), (
            f"{field} still carries placeholder prose: {prose!r}"
        )


def test_AC_O_6_dev_intent_default_unanswered():
    """The template's dev_intent default is 'unanswered'
    (refined during onboarding)."""
    contract = _load_template_with_scaffold_mutations()
    assert contract.dev_intent == "unanswered"


def test_AC_O_6_is_primary_true():
    """The template ships is_primary: true so the scaffold-installed
    persona becomes the workspace's primary."""
    contract = _load_template_with_scaffold_mutations()
    assert contract.is_primary is True


def test_AC_O_6_tier_d_defers():
    """Per the archetype's chief-of-staff register, tier_d is
    'defer' — close-associate communications are surfaced to the
    user rather than handled autonomously by default."""
    contract = _load_template_with_scaffold_mutations()
    assert contract.authority_boundary.tier_d == TierAction.defer


def test_AC_O_6_renders_through_to_agent_md():
    """The loaded contract renders through to_agent_md() without
    raising and produces non-empty output."""
    contract = _load_template_with_scaffold_mutations()
    rendered = to_agent_md(contract)
    assert rendered.strip() != ""
    assert "iris" in rendered  # handle reference
