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

"""AC.RSR.8 — no regression on the sealed recall surface; fail-open.

S4 adds a channel and never alters the fact/episode/decision pipeline or
the fail-open-whole-chain contract. A broken / absent rules store yields
no rules block and NEVER breaks the turn; a rules-channel error degrades
to the fact block. (The KP1/FBMU/FBM-FILTER/SRF/RDP/RTEL/DLG suites
staying green is the broader guard — run as the full suite at seal.)
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona import rules_store as rs
from loam.primary_persona.keep_pace import retrieval as R
from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve

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


def test_AC_RSR_8_absent_store_no_rules_block_fact_recall_intact(
    tmp_path: Path,
) -> None:
    corpus = tmp_path / "memory"
    write_corpus(corpus)
    # rules_memory_dir points at a dir with NO rules/ subdir.
    empty = tmp_path / "empty-store"
    empty.mkdir()
    block = retrieve(prompt=_PROMPT, config=_cfg(tmp_path, corpus, empty))
    assert "[behavioral-rules]" not in block
    assert "[keep-pace]" in block  # fact recall unchanged


def test_AC_RSR_8_malformed_rule_file_is_skipped(tmp_path: Path) -> None:
    corpus = tmp_path / "memory"
    write_corpus(corpus)
    store = tmp_path / "store"
    (store / "rules").mkdir(parents=True)
    # One valid rule + one garbage file in the same store.
    rs.write_rule(
        store,
        directive="Dispatch briefs carry scope only.",
        situation=["dispatching-subagent"],
        provenance=["feedback_x.md"],
    )
    (store / "rules" / "garbage.md").write_text(
        "not frontmatter at all\n", encoding="utf-8"
    )
    block = retrieve(prompt=_PROMPT, config=_cfg(tmp_path, corpus, store))
    # The valid rule still surfaces; the garbage file broke nothing.
    assert "Dispatch briefs carry scope only" in block
    assert "[keep-pace]" in block


def test_AC_RSR_8_rules_channel_error_degrades_to_fact_block(
    tmp_path: Path, monkeypatch
) -> None:
    """A rules-channel exception (a broken store implementation) NEVER
    reaches ``retrieve``'s caller — the turn degrades to the fact block."""
    corpus = tmp_path / "memory"
    write_corpus(corpus)
    store = tmp_path / "store"
    store.mkdir()
    rs.seed_starter_rules(store)

    def _boom(*a, **k):
        raise RuntimeError("simulated store failure")

    monkeypatch.setattr(
        "loam.primary_persona.rules_store.rules_for_situation", _boom
    )
    block = retrieve(prompt=_PROMPT, config=_cfg(tmp_path, corpus, store))
    assert "[behavioral-rules]" not in block
    assert "[keep-pace]" in block  # fact recall survived the rules error


def test_AC_RSR_8_store_root_is_a_file_fails_soft(tmp_path: Path) -> None:
    """A rules_memory_dir whose ``rules/`` path is unusable (a file, not a
    dir) yields no rules block, no exception."""
    corpus = tmp_path / "memory"
    write_corpus(corpus)
    store = tmp_path / "store"
    store.mkdir()
    # Make rules/ a FILE so glob/is_dir fails soft.
    (store / "rules").write_text("i am a file", encoding="utf-8")
    block = retrieve(prompt=_PROMPT, config=_cfg(tmp_path, corpus, store))
    assert "[behavioral-rules]" not in block
    assert "[keep-pace]" in block
