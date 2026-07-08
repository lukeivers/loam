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

"""AC.RSR.6 (reversibility) — a named master lever reverts (c) to a no-op.

With the master lever OFF (or ``SITUATIONAL_RULE_CAP = 0``) the recall
output is BYTE-IDENTICAL to pre-S4 (no rules block emitted); flipping it
on re-admits rules with NOTHING deleted on disk.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona import rules_store as rs
from loam.primary_persona.keep_pace import retrieval as R
from loam.primary_persona.keep_pace.retrieval import (
    RetrievalConfig,
    retrieve,
)

from _helpers_keep_pace import write_corpus

_PROMPT = "dispatch a background agent to run the litrpg canon production pipeline"


def _cfg(tmp_path: Path, corpus: Path, store) -> RetrievalConfig:
    return RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=corpus,
        claude_homes=(),
        objectives_home=tmp_path / "no-obj",
        rules_memory_dir=store,
    )


def _pre_s4_baseline(tmp_path: Path, corpus: Path) -> str:
    """The pre-S4 recall: the rules channel simply does not exist (no
    ``rules_memory_dir`` configured)."""
    return retrieve(prompt=_PROMPT, config=_cfg(tmp_path, corpus, None))


def test_AC_RSR_6_master_off_is_byte_identical_to_pre_s4(
    tmp_path: Path, monkeypatch
) -> None:
    corpus = tmp_path / "memory"
    write_corpus(corpus)
    store = tmp_path / "store"
    store.mkdir()
    rs.seed_starter_rules(store)

    baseline = _pre_s4_baseline(tmp_path, corpus)
    # Sanity: with the lever ON the rules block IS present, so the
    # byte-identical claim below is non-trivial.
    on = retrieve(prompt=_PROMPT, config=_cfg(tmp_path, corpus, store))
    assert "[behavioral-rules]" in on

    # Master lever OFF: the configured store is IGNORED; output reverts.
    monkeypatch.setattr(R, "SITUATIONAL_RULES_ENABLED", False)
    off = retrieve(prompt=_PROMPT, config=_cfg(tmp_path, corpus, store))
    assert off == baseline, "master-off recall is not byte-identical to pre-S4"
    assert "[behavioral-rules]" not in off


def test_AC_RSR_6_cap_zero_is_byte_identical_to_pre_s4(
    tmp_path: Path, monkeypatch
) -> None:
    corpus = tmp_path / "memory"
    write_corpus(corpus)
    store = tmp_path / "store"
    store.mkdir()
    rs.seed_starter_rules(store)

    baseline = _pre_s4_baseline(tmp_path, corpus)
    monkeypatch.setattr(R, "SITUATIONAL_RULE_CAP", 0)
    capped = retrieve(prompt=_PROMPT, config=_cfg(tmp_path, corpus, store))
    assert capped == baseline
    assert "[behavioral-rules]" not in capped


def test_AC_RSR_6_flip_on_readmits_with_store_untouched(
    tmp_path: Path, monkeypatch
) -> None:
    """Flipping the lever off then on re-admits the SAME rules — the flip
    never deletes a file."""
    corpus = tmp_path / "memory"
    write_corpus(corpus)
    store = tmp_path / "store"
    store.mkdir()
    rs.seed_starter_rules(store)
    files_before = sorted(p.name for p in (store / "rules").glob("*.md"))

    monkeypatch.setattr(R, "SITUATIONAL_RULES_ENABLED", False)
    retrieve(prompt=_PROMPT, config=_cfg(tmp_path, corpus, store))
    monkeypatch.setattr(R, "SITUATIONAL_RULES_ENABLED", True)
    on = retrieve(prompt=_PROMPT, config=_cfg(tmp_path, corpus, store))

    files_after = sorted(p.name for p in (store / "rules").glob("*.md"))
    assert files_before == files_after, "the lever flip mutated the store"
    assert "[behavioral-rules]" in on
