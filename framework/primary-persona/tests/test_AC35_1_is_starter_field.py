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

"""AC35.1 — `is_starter` field exists on the persona contract and validates.

The ``PersonaContract`` Pydantic model exposes a Boolean ``is_starter``
field with default ``False``. A YAML containing ``is_starter: true``
round-trips through ``model_validate`` → ``to_yaml()`` →
``model_validate`` and produces an equivalent contract. A YAML
omitting the field validates with ``is_starter: False``. A YAML
containing a non-Boolean value rejects with a clear validation error.
No existing v1.0 / v1.1 / v1.2 contract field is renamed or removed.

Plan: docs/rebuild/plans/amendment-35-primary-persona-renderer-and-onboarding.md
"""

from __future__ import annotations

import pytest
import yaml
from pydantic import ValidationError

from loam.primary_persona.contract import PersonaContract


def _base_contract_dict() -> dict:
    """Minimum-valid contract payload (mirrors VALID_CONTRACT_YAML)."""
    return {
        "handle": "eve",
        "given_name": "Eve",
        "contract_version": "1.0.0",
        "responsibilities": {
            "single_point_of_contact": "Sole coordinator for personal-life operations.",
            "context_holder": "Carries ongoing context across sessions.",
            "escalation_judge": "Decides when to surface matters to Luke.",
        },
        "authority_boundary": {
            "tier_a": "defer",
            "tier_b": "defer",
            "tier_c": "execute",
            "tier_d": "execute",
        },
        "escalation_taxonomy": {
            "categories": ["external-funds-commitment", "strategy-pivot"],
        },
        "severity_vocabulary": {
            "labels": ["crisis", "urgent", "material", "advisory"],
        },
    }


def test_AC35_1_is_starter_default_is_false():
    """A YAML omitting `is_starter` validates with `is_starter: False`."""
    contract = PersonaContract.model_validate(_base_contract_dict())
    assert contract.is_starter is False


def test_AC35_1_is_starter_true_round_trip():
    """`is_starter: true` round-trips through model_validate → to_yaml → model_validate."""
    payload = _base_contract_dict()
    payload["is_starter"] = True
    contract = PersonaContract.model_validate(payload)
    assert contract.is_starter is True

    yaml_text = contract.to_yaml()
    reloaded = PersonaContract.model_validate(yaml.safe_load(yaml_text))
    assert reloaded.is_starter is True
    # Equivalent contract beyond is_starter — every field round-trips.
    assert reloaded.handle == contract.handle
    assert reloaded.given_name == contract.given_name
    assert (
        reloaded.responsibilities.single_point_of_contact
        == contract.responsibilities.single_point_of_contact
    )


def test_AC35_1_is_starter_false_round_trip():
    """`is_starter: false` round-trips identically."""
    payload = _base_contract_dict()
    payload["is_starter"] = False
    contract = PersonaContract.model_validate(payload)
    assert contract.is_starter is False
    yaml_text = contract.to_yaml()
    reloaded = PersonaContract.model_validate(yaml.safe_load(yaml_text))
    assert reloaded.is_starter is False


def test_AC35_1_is_starter_non_boolean_rejected():
    """A non-Boolean value rejects with a clear validation error
    naming the field."""
    payload = _base_contract_dict()
    payload["is_starter"] = "yes"  # str, not bool
    with pytest.raises(ValidationError) as exc:
        PersonaContract.model_validate(payload)
    err_text = str(exc.value)
    assert "is_starter" in err_text


def test_AC35_1_existing_d1_fields_preserved():
    """No existing v1.0/v1.1/v1.2 contract field is renamed or removed.

    Spot-check the canonical mandatory and optional fields are still
    present on the model and validate as before.
    """
    contract = PersonaContract.model_validate(_base_contract_dict())
    # Mandatory v1.0 surface.
    assert contract.handle == "eve"
    assert contract.given_name == "Eve"
    assert contract.contract_version == "1.0.0"
    assert contract.responsibilities is not None
    assert contract.authority_boundary is not None
    assert contract.escalation_taxonomy is not None
    assert contract.severity_vocabulary is not None
    # Optional state flags landed pre-#35.
    assert contract.pending_introduction is False
    assert contract.is_addressable is True
    # Default for the new field.
    assert contract.is_starter is False
