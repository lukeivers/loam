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

"""AC.RSR.4 — separate recall channel: rules do not compete with facts.

Rules inject in a distinct, labeled block on a budget separate from the
store-(b) fact pool; the fact recall output for a given turn is
BYTE-IDENTICAL whether or not any rule fires — rules never enter
``_merge_by_score``, never occupy a fact slot, never crowd a topical fact.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona import rules_store as rs
from loam.primary_persona.keep_pace.retrieval import (
    RetrievalConfig,
    rank,
    retrieve,
)

from _helpers_keep_pace import write_corpus

# A prompt that matches BOTH a topical fact (litrpg canon / production
# pipeline) AND a situation (dispatching a sub-agent), so the rules
# channel and the fact channel both have material to surface.
_PROMPT = "dispatch a background agent to run the litrpg canon production pipeline"


def _cfg(tmp_path: Path, corpus: Path, rules_dir) -> RetrievalConfig:
    return RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=corpus,
        claude_homes=(),
        objectives_home=tmp_path / "no-obj",
        rules_memory_dir=rules_dir,
    )


def test_AC_RSR_4_fact_block_byte_identical_rules_empty_vs_populated(
    tmp_path: Path,
) -> None:
    corpus = tmp_path / "memory"
    write_corpus(corpus)
    store = tmp_path / "store"
    store.mkdir()
    rs.seed_starter_rules(store)

    # Rules channel OFF (no store configured) — pure fact block.
    fact_only = retrieve(prompt=_PROMPT, config=_cfg(tmp_path, corpus, None))
    # Rules channel ON — a rule fires (dispatching situation).
    with_rules = retrieve(prompt=_PROMPT, config=_cfg(tmp_path, corpus, store))

    assert "[behavioral-rules]" in with_rules, "the rules channel did not fire"
    assert "[keep-pace]" in fact_only, "no fact block to compare"
    # The fact block is byte-identical — it is the exact suffix of the
    # combined output (rules block precedes it, Fork E ordering).
    assert with_rules.endswith(fact_only), (
        "the fact block was perturbed by the rules channel"
    )
    # The rules block is a distinct, separately-labeled block.
    rules_part = with_rules[: with_rules.index(fact_only)]
    assert rules_part.startswith("[behavioral-rules]")
    assert "[keep-pace]" not in rules_part


def test_AC_RSR_4_ranked_hits_never_include_a_rule(tmp_path: Path) -> None:
    """The ranked hit list (the ``_merge_by_score`` output + P@5 metric
    contract) is identical whether or not a rule fires — a rule is never a
    ranked hit."""
    corpus = tmp_path / "memory"
    write_corpus(corpus)
    store = tmp_path / "store"
    store.mkdir()
    rs.seed_starter_rules(store)

    hits_no_rules = rank(prompt=_PROMPT, config=_cfg(tmp_path, corpus, None))
    hits_with_rules = rank(prompt=_PROMPT, config=_cfg(tmp_path, corpus, store))

    def _identity(hits):
        return [(h.get("pointer"), h.get("path")) for h in hits]

    assert _identity(hits_no_rules) == _identity(hits_with_rules)
    # No ranked hit is a rule directive.
    for h in hits_with_rules:
        assert not str(h.get("pointer", "")).startswith("[behavioral-rules]")
