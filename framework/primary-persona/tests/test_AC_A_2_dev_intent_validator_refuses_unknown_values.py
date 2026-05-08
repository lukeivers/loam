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

"""AC.A.2 — `PersonaContract` carries a `dev_intent` field with structural validation.

Sub-plan A (two-modes-and-multi-workspace) lands a new
``dev_intent`` field on ``PersonaContract`` whose admissible values
are the literals ``"unanswered"`` (default), ``"yes"``, and ``"no"``.
Pydantic's ``Literal`` typing structurally rejects any other string
at validation time; the persona cannot end up in an undefined dev-mode
state (AC.PO.1). The contract field is the canonical signal sub-plans
E / B / F compose on (AC.PO.2).

Plan: docs/plans/two-modes-and-multi-workspace/A-onboarding-dev-intent.md
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from loam.primary_persona.contract import PersonaContract


def _base_contract_dict() -> dict:
    return {
        "handle": "iris",
        "given_name": "Iris",
        "contract_version": "1.0.0",
        "responsibilities": {
            "single_point_of_contact": "Coordinator for the user's domain.",
            "context_holder": "Carries ongoing context.",
            "escalation_judge": "Decides when to surface.",
        },
        "authority_boundary": {
            "tier_a": "defer",
            "tier_b": "defer",
            "tier_c": "execute",
            "tier_d": "execute",
        },
        "escalation_taxonomy": {"categories": ["x"]},
        "severity_vocabulary": {"labels": ["a", "b"]},
    }


def test_AC_A_2_dev_intent_yes_validates():
    """``dev_intent='yes'`` is an admissible literal value."""
    payload = _base_contract_dict() | {"dev_intent": "yes"}
    contract = PersonaContract.model_validate(payload)
    assert contract.dev_intent == "yes"


def test_AC_A_2_dev_intent_no_validates():
    """``dev_intent='no'`` is an admissible literal value."""
    payload = _base_contract_dict() | {"dev_intent": "no"}
    contract = PersonaContract.model_validate(payload)
    assert contract.dev_intent == "no"


def test_AC_A_2_dev_intent_unanswered_validates():
    """``dev_intent='unanswered'`` is the documented sentinel."""
    payload = _base_contract_dict() | {"dev_intent": "unanswered"}
    contract = PersonaContract.model_validate(payload)
    assert contract.dev_intent == "unanswered"


def test_AC_A_2_dev_intent_default_is_unanswered():
    """Constructing without specifying the field defaults to the
    documented unanswered sentinel."""
    contract = PersonaContract.model_validate(_base_contract_dict())
    assert contract.dev_intent == "unanswered"


def test_AC_A_2_dev_intent_validator_refuses_unknown_values():
    """Any other string raises Pydantic ValidationError. Structural
    refusal at the schema layer (AC.PO.1)."""
    payload = _base_contract_dict() | {"dev_intent": "maybe"}
    with pytest.raises(ValidationError):
        PersonaContract.model_validate(payload)


def test_AC_A_2_dev_intent_validator_refuses_empty_string():
    """The empty string is not the unanswered sentinel — the contract
    documents a specific literal."""
    payload = _base_contract_dict() | {"dev_intent": ""}
    with pytest.raises(ValidationError):
        PersonaContract.model_validate(payload)


def test_AC_A_2_dev_intent_validator_refuses_non_string():
    """Non-string values (bool, int) are also rejected by the
    Literal typing."""
    payload = _base_contract_dict() | {"dev_intent": True}
    with pytest.raises(ValidationError):
        PersonaContract.model_validate(payload)
