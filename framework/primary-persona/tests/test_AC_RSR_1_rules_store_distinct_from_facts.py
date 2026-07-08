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

"""AC.RSR.1 — the rules store exists and is distinct from facts.

A behavioral rule persists as a structured record carrying a directive, a
situation representation, a provenance set, and a status; it lands in a
store DISTINCT from the decision ledger + the corpus, human-readable and
prunable on disk; reading it back returns the authored rule.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona import rules_store as rs
from loam.primary_persona.decision_ledger import (
    DECISIONS_SUBDIR,
    write_decision,
)


def test_AC_RSR_1_write_readback_fields(tmp_path: Path) -> None:
    res = rs.write_rule(
        tmp_path,
        directive="Dispatch briefs carry scope only.",
        situation=["dispatching-subagent", "planning"],
        provenance=["feedback_agent_prompts_scope_only.md"],
        strength=4,
        floor_promote=True,
        trigger="key-idea",
    )
    rec = rs.read_rule(res["path"])
    assert rec is not None
    assert rec.directive == "Dispatch briefs carry scope only."
    assert rec.situation == ("dispatching-subagent", "planning")
    assert rec.provenance == ("feedback_agent_prompts_scope_only.md",)
    assert rec.strength == 4
    assert rec.floor_promote is True
    assert rec.trigger == "key-idea"
    assert rec.status == "active"


def test_AC_RSR_1_store_is_distinct_dir_from_decisions(tmp_path: Path) -> None:
    """Rules land under ``rules/`` — the ledger's ``decisions/`` sibling —
    so the two stores are physically distinct directories."""
    rule = rs.write_rule(
        tmp_path,
        directive="A directive.",
        situation=["s"],
        provenance=["feedback_x.md"],
    )
    dec = write_decision(
        tmp_path,
        question="q?",
        ruling="r",
        reasoning="because",
        entities=("e",),
        source="src",
    )
    assert rs.RULES_SUBDIR != DECISIONS_SUBDIR
    assert (tmp_path / rs.RULES_SUBDIR) in Path(rule["path"]).parents
    assert (tmp_path / DECISIONS_SUBDIR) in Path(dec["path"]).parents
    # The rules dir contains only the rule; the decisions dir only the
    # decision — no cross-contamination.
    assert [p.name for p in (tmp_path / rs.RULES_SUBDIR).glob("*.md")] == [
        Path(rule["path"]).name
    ]


def test_AC_RSR_1_human_readable_and_prunable(tmp_path: Path) -> None:
    """The on-disk record is plain frontmatter'd markdown (glanceable +
    prunable by deleting the file)."""
    res = rs.write_rule(
        tmp_path,
        directive="Keep the human's voice.",
        situation=["authoring-outbound-text"],
        provenance=["feedback_de_ai_external_text.md"],
    )
    text = Path(res["path"]).read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "record: rule" in text
    assert "Keep the human's voice." in text
    # Prune it: deleting the file removes the rule; the store degrades
    # fail-soft to empty.
    Path(res["path"]).unlink()
    assert rs.iter_rules(tmp_path) == []


def test_AC_RSR_1_iter_returns_only_rule_records(tmp_path: Path) -> None:
    """A non-rule markdown file in the rules dir is ignored (record-type
    guard), so the store never mis-reads a stray file as a rule."""
    rs.write_rule(
        tmp_path,
        directive="d",
        situation=["s"],
        provenance=["p.md"],
    )
    stray = tmp_path / rs.RULES_SUBDIR / "not-a-rule.md"
    stray.write_text("---\nrecord: decision\n---\nnope\n", encoding="utf-8")
    recs = rs.iter_rules(tmp_path)
    assert len(recs) == 1
    assert recs[0].directive == "d"
