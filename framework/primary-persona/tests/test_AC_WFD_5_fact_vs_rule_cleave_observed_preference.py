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

"""AC.WFD.5 — the fact-vs-rule cleave at write time; observed-preferences
resolved.

An observed preference lands the OBSERVATION as a fact in store (b)
(always). Only when the behavioral threshold is cleared does a SEPARATE
rule land in store (c) via S4's ``write_rule``, carrying a provenance
pointer back to that fact. The fact store never holds the inferred
generalization as a bare fact; the default when the threshold is NOT
cleared is fact-only (no rule).

The threshold judgment is the persona's (D2) — this stage codes no
significance engine (the S5 boundary). The test drives the two persona
paths and asserts the mechanism composes: (b) always, (c) only when the
persona authors the rule, always provenance-bound.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from loam.primary_persona import rules_store as rs
from loam.primary_persona.file_memory import (
    EPISTEMIC_FACT,
    FileMemoryStore,
    read_epistemic_tag,
)


def _write_observation(store: FileMemoryStore, body: str) -> Path:
    res = store.write_episode(
        name="turn/observed-pref",
        body=body,
        source_description="session capture",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="pos3",
    )
    return Path(res["path"])


# The OBSERVATION recorded as a fact — an event that specifically happened,
# not the inferred generalization.
OBSERVATION = (
    "Luke chose the long-term rebuild over the quick patch on 2026-07-02 "
    "after the patch caused a regression"
)


def test_AC_WFD_5_threshold_cleared_writes_fact_and_provenance_rule(
    tmp_path: Path,
) -> None:
    memory_dir = tmp_path / "memory"
    store = FileMemoryStore(memory_dir=memory_dir)

    # (b): the observation is a fact (an event with an author + time).
    fact_path = _write_observation(store, OBSERVATION)
    assert read_epistemic_tag(fact_path) == EPISTEMIC_FACT

    # (c): the persona judged the threshold cleared (a bad-enough outcome)
    # and authored the behavioral PRIOR as a rule pointing provenance back
    # at the fact — never the generalization as a bare fact in (b).
    res = rs.write_rule(
        memory_dir,
        directive="prefer the long-term rebuild over a quick patch",
        situation=("patch-vs-rebuild-decision",),
        provenance=(str(fact_path),),
        trigger="bad-outcome",
    )
    rule = rs.read_rule(Path(res["path"]))
    assert rule is not None
    assert rule.provenance and str(fact_path) in rule.provenance[0], (
        "the rule must carry provenance back to the store-(b) fact"
    )

    # The fact store holds the OBSERVATION, not the generalization.
    body = fact_path.read_text(encoding="utf-8")
    assert "chose the long-term rebuild" in body
    assert "prefer the long-term rebuild" not in body, (
        "the inferred generalization must NOT live as a bare fact in (b)"
    )


def test_AC_WFD_5_threshold_not_cleared_is_fact_only_no_rule(
    tmp_path: Path,
) -> None:
    memory_dir = tmp_path / "memory"
    store = FileMemoryStore(memory_dir=memory_dir)

    # The default: the persona writes ONLY the observation (threshold not
    # cleared — a routine preference, not significant frustration / a
    # bad-enough outcome / a key idea).
    fact_path = _write_observation(store, OBSERVATION)
    assert read_epistemic_tag(fact_path) == EPISTEMIC_FACT

    # No rule authored => store (c) is empty (LIBERAL fact ingest,
    # CONSERVATIVE high-threshold rule extraction).
    assert rs.iter_rules(memory_dir) == [], (
        "no rule should exist when the behavioral threshold is not cleared"
    )


def test_AC_WFD_5_rule_write_rejects_without_provenance(tmp_path: Path) -> None:
    # The (b)->(c) cleave TERMINATES in S4's provenance contract: a rule
    # with no pointer to a store-(b) fact is rejected (never a floating
    # rule).
    memory_dir = tmp_path / "memory"
    with pytest.raises(rs.RuleValidationError):
        rs.write_rule(
            memory_dir,
            directive="prefer the long-term rebuild",
            situation=("patch-vs-rebuild-decision",),
            provenance=(),
        )
