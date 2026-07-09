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

"""AC.RVL.5 — a matched situational rule is never dropped by a COUNT; the
rules block is bounded only by its byte sub-budget.

Seeds MORE matched rules than the legacy count cap of 3, all short enough to
fit the byte sub-budget, and asserts every matched rule injects — proving
SITUATIONAL_RULE_CAP is a NO-OP backstop, not a set-determiner.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona import rules_store as rs
from loam.primary_persona.keep_pace import retrieval as R
from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve

_SITUATION = "dispatching-subagent"
_TRIGGER_PROMPT = "dispatch a background agent for this build"
_LEGACY_CAP = 3
_N = 8  # > legacy cap of 3, all fit the byte sub-budget


def _cfg(tmp_path: Path, store: Path) -> RetrievalConfig:
    return RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=None,
        claude_homes=(),
        objectives_home=tmp_path / "no-obj",
        rules_memory_dir=store,
    )


def _seed_short_rules(store: Path, n: int) -> None:
    for i in range(n):
        rs.write_rule(
            store,
            directive=f"Rule {i}.",  # tiny — all n fit the byte sub-budget
            situation=[_SITUATION],
            provenance=[f"feedback_{i}.md"],
            strength=i,
        )


def test_AC_RVL_5_every_matched_rule_that_fits_the_byte_budget_injects(
    tmp_path: Path,
) -> None:
    store = tmp_path / "store"
    store.mkdir()
    _seed_short_rules(store, _N)
    matched = rs.rules_for_situation(store, [_SITUATION])
    assert len(matched) == _N
    block = retrieve(prompt=_TRIGGER_PROMPT, config=_cfg(tmp_path, store))
    n_lines = block.count("\n  - ")
    # All _N matched rules inject — none dropped by count (the count cap is a
    # no-op: _N > the legacy 3, yet every matched rule surfaces).
    assert n_lines == _N, (
        f"every matched rule that fits the byte budget must inject; got "
        f"{n_lines} of {_N} — a count is still dropping matched directives"
    )
    assert _N > _LEGACY_CAP, "the fixture exceeds the legacy count cap of 3"
    assert len(block) <= R.SITUATIONAL_RULE_CHAR_CAP


def test_AC_RVL_5_situational_rule_cap_is_a_no_op_backstop(tmp_path: Path) -> None:
    # SITUATIONAL_RULE_CAP is raised well above any byte-budget-fit set, so it
    # never bites on a normal matched set.
    assert R.SITUATIONAL_RULE_CAP > _N, (
        "SITUATIONAL_RULE_CAP must be a no-op backstop above the byte-fit set"
    )
