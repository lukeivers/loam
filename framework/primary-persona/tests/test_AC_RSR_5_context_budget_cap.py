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

"""AC.RSR.5 (context-budget-bound) + AC.RVL.5 (recall volume-limits reshape).

The situational-rules block is bounded by its BYTE sub-budget
(``SITUATIONAL_RULE_CHAR_CAP``), not by a count. ``SITUATIONAL_RULE_CAP`` is
now a NO-OP overflow backstop (raised well above any byte-budget-fit set), so
a matched behavioral directive is NEVER dropped by count — only the byte
sub-budget bounds the block, dropping a rule WHOLE (never half-emitted) on
overflow. The count backstop remains a named, tunable lever: lowering it to a
value below the byte-fit set re-imposes a count cut (the AC.RSR.5
reversibility path), and excess is dropped by a DETERMINISTIC priority
(strength / recency / path).
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona import rules_store as rs
from loam.primary_persona.keep_pace import retrieval as R
from loam.primary_persona.keep_pace.retrieval import (
    RetrievalConfig,
    retrieve,
)

_SITUATION = "dispatching-subagent"
_TRIGGER_PROMPT = "dispatch a background agent for this build"


def _cfg(tmp_path: Path, store: Path) -> RetrievalConfig:
    return RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=None,
        claude_homes=(),
        objectives_home=tmp_path / "no-obj",
        rules_memory_dir=store,
    )


def _seed_many(store: Path, n: int) -> None:
    # Distinct strengths so the deterministic drop order is observable.
    for i in range(n):
        rs.write_rule(
            store,
            directive=f"Directive number {i} with strength {i}.",
            situation=[_SITUATION],
            provenance=[f"feedback_{i}.md"],
            strength=i,
        )


def test_AC_RSR_5_block_bounded_by_byte_budget_not_count(
    tmp_path: Path, monkeypatch
) -> None:
    # AC.RVL.5 — SITUATIONAL_RULE_CAP is now a NO-OP overflow backstop, not the
    # set-determiner. Seed MORE matched rules than fit the byte sub-budget but
    # FEWER than the backstop: the BYTE budget (not the count) bounds the block,
    # and no matched rule is dropped by count.
    store = tmp_path / "store"
    store.mkdir()
    n = R.SITUATIONAL_RULE_CAP - 5  # < backstop, > byte-budget-fit
    _seed_many(store, n=n)
    matched = rs.rules_for_situation(store, [_SITUATION])
    assert len(matched) == n
    block = retrieve(prompt=_TRIGGER_PROMPT, config=_cfg(tmp_path, store))
    n_lines = block.count("\n  - ")
    # The count backstop is a NO-OP here (n < backstop); the BYTE sub-budget is
    # what bounds the block — strictly fewer than the matched set, and the block
    # respects its byte sub-budget (drop-whole on overflow).
    assert 0 < n_lines < n
    assert n_lines < R.SITUATIONAL_RULE_CAP, "count backstop must not have cut"
    assert len(block) <= R.SITUATIONAL_RULE_CHAR_CAP


def test_AC_RSR_5_cap_drops_lowest_priority_deterministically(
    tmp_path: Path,
) -> None:
    """The highest-strength rules survive the cap; the lowest-strength
    excess is dropped — a deterministic priority, not a random slice."""
    store = tmp_path / "store"
    store.mkdir()
    _seed_many(store, n=R.SITUATIONAL_RULE_CAP + 2)
    block = retrieve(prompt=_TRIGGER_PROMPT, config=_cfg(tmp_path, store))
    # Highest strengths kept; the two lowest (0, 1) dropped.
    top = R.SITUATIONAL_RULE_CAP + 1  # highest strength index
    assert f"Directive number {top} " in block
    assert "Directive number 0 " not in block
    assert "Directive number 1 " not in block


def test_AC_RSR_5_cap_is_a_tunable_lever(tmp_path: Path, monkeypatch) -> None:
    """Lowering the cap admits fewer; raising it admits more — the lever
    reorders the outcome."""
    store = tmp_path / "store"
    store.mkdir()
    _seed_many(store, n=5)

    monkeypatch.setattr(R, "SITUATIONAL_RULE_CAP", 1)
    one = retrieve(prompt=_TRIGGER_PROMPT, config=_cfg(tmp_path, store))
    assert one.count("\n  - ") == 1

    monkeypatch.setattr(R, "SITUATIONAL_RULE_CAP", 4)
    four = retrieve(prompt=_TRIGGER_PROMPT, config=_cfg(tmp_path, store))
    assert four.count("\n  - ") == 4


def test_AC_RSR_5_byte_sub_budget_drops_whole_never_half(
    tmp_path: Path, monkeypatch
) -> None:
    """With a tiny byte sub-budget, a rule that would overflow is dropped
    WHOLE — the block never contains a truncated directive."""
    store = tmp_path / "store"
    store.mkdir()
    long_directive = "X" * 400 + " end-of-directive-marker."
    rs.write_rule(
        store,
        directive=long_directive,
        situation=[_SITUATION],
        provenance=["feedback_long.md"],
        strength=10,
    )
    rs.write_rule(
        store,
        directive="short one",
        situation=[_SITUATION],
        provenance=["feedback_short.md"],
        strength=1,
    )
    # Sub-budget only fits the header — the long high-strength rule is
    # dropped whole rather than truncated (break-on-overflow).
    monkeypatch.setattr(R, "SITUATIONAL_RULE_CHAR_CAP", 90)
    block = retrieve(prompt=_TRIGGER_PROMPT, config=_cfg(tmp_path, store))
    assert "end-of-directive-marker" not in block
    # No partial directive: any emitted line is a complete "  - ..." line.
    assert "X" * 400 not in block
