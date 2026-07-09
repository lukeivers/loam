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

"""AC.RVL.6 — every byte budget in the recall path names, in-source, the
resource constraint it derives from; a byte budget with no named resource is
absent.

Per the owner's §3 ruling (hybrid): both byte budgets derive as named
fractions of ADDITIONAL_CONTEXT_CAP — the one limit backed by a real enforced
resource boundary (context construction refuses above it).
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.context_composer import ADDITIONAL_CONTEXT_CAP
from loam.primary_persona.keep_pace import retrieval as R


def test_AC_RVL_6_injection_char_cap_derived_from_the_enforced_resource() -> None:
    assert R.INJECTION_CHAR_CAP == round(
        R.FACT_BLOCK_BUDGET_FRACTION * ADDITIONAL_CONTEXT_CAP
    ), "INJECTION_CHAR_CAP must derive from the enforced ADDITIONAL_CONTEXT_CAP"
    # No-regression: the derivation preserves the sealed AC.SRF.3 value exactly.
    assert R.INJECTION_CHAR_CAP == 5000


def test_AC_RVL_6_rules_char_cap_derived_from_the_enforced_resource() -> None:
    assert R.SITUATIONAL_RULE_CHAR_CAP == round(
        R.SITUATIONAL_RULE_BUDGET_FRACTION * ADDITIONAL_CONTEXT_CAP
    ), "SITUATIONAL_RULE_CHAR_CAP must derive from the enforced ADDITIONAL_CONTEXT_CAP"
    # No-regression: the derivation preserves the sealed AC.RSR.5 value exactly.
    assert R.SITUATIONAL_RULE_CHAR_CAP == 1200


def test_AC_RVL_6_each_budget_names_its_resource_in_source() -> None:
    src = Path(R.__file__).read_text(encoding="utf-8")
    # Both budgets carry an in-source comment naming ADDITIONAL_CONTEXT_CAP as
    # the resource each derives from (not a bare integer).
    assert "ADDITIONAL_CONTEXT_CAP" in src
    assert "FACT_BLOCK_BUDGET_FRACTION" in src
    assert "SITUATIONAL_RULE_BUDGET_FRACTION" in src
    # The derivation is computed, not hard-coded, for each budget.
    assert "INJECTION_CHAR_CAP = round(" in src
    assert "SITUATIONAL_RULE_CHAR_CAP = round(" in src
