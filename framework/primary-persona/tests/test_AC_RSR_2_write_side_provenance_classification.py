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

"""AC.RSR.2 — write-side classification: rules are directives auditable to
evidence; facts stay facts.

A rule write is REJECTED without a provenance pointer to a store-(b)
record (a rule is auditable to the fact(s) that justify it). The
store-(b) facts-only discipline is unchanged (a decision write still
stores a decision, never a directive). Classification is at WRITE time —
a fact + its derived rule land in two DIFFERENT stores.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.primary_persona import rules_store as rs
from loam.primary_persona.decision_ledger import read_decision, write_decision


def test_AC_RSR_2_provenance_less_rule_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(rs.RuleValidationError):
        rs.write_rule(
            tmp_path,
            directive="A floating directive with nothing behind it.",
            situation=["dispatching-subagent"],
            provenance=[],
        )
    # Nothing was persisted — the store stays empty (no floating rule).
    assert rs.iter_rules(tmp_path) == []


def test_AC_RSR_2_whitespace_only_provenance_is_rejected(tmp_path: Path) -> None:
    """A provenance list of only empty/whitespace strings is NO provenance
    — the guard is on real pointers, not list length."""
    with pytest.raises(rs.RuleValidationError):
        rs.write_rule(
            tmp_path,
            directive="d",
            situation=["s"],
            provenance=["   ", ""],
        )


def test_AC_RSR_2_empty_directive_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(rs.RuleValidationError):
        rs.write_rule(
            tmp_path,
            directive="   ",
            situation=["s"],
            provenance=["feedback_x.md"],
        )


def test_AC_RSR_2_rule_with_provenance_is_accepted(tmp_path: Path) -> None:
    res = rs.write_rule(
        tmp_path,
        directive="Run the de-AI scrub on external-bound text.",
        situation=["authoring-outbound-text"],
        provenance=["feedback_de_ai_external_text.md"],
    )
    rec = rs.read_rule(res["path"])
    assert rec is not None
    assert rec.provenance == ("feedback_de_ai_external_text.md",)


def test_AC_RSR_2_fact_and_derived_rule_land_in_two_stores(
    tmp_path: Path,
) -> None:
    """Classification at write time: the fact-half is a decision record in
    ``decisions/``; the rule-half is a directive in ``rules/`` that CITES
    the decision as provenance. They are authored APART, never scored
    together."""
    dec = write_decision(
        tmp_path,
        question="Should agent dispatches enumerate files?",
        ruling="No — scope only, method is the builder's call.",
        reasoning="Over-tight prompts block the correct alternative.",
        entities=("dispatch",),
        source="telegram-1234",
    )
    rule = rs.write_rule(
        tmp_path,
        directive="Dispatch briefs carry scope only.",
        situation=["dispatching-subagent"],
        provenance=[dec["path"]],
    )
    # The decision store still reads a decision (facts-only intact).
    assert read_decision(dec["path"]) is not None
    # The rule store reads a rule whose provenance points at the decision.
    rrec = rs.read_rule(rule["path"])
    assert rrec is not None
    assert rrec.provenance == (dec["path"],)
    # Two physically distinct stores.
    assert Path(dec["path"]).parent != Path(rule["path"]).parent
