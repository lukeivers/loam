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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.DLG.3 — decision records participate in unified retrieval: a
topic query matching a record's entity vocabulary returns the record
positioned for whole-record injection (per AC.SRF.3); records with
``status: open`` on an active workstream surface without an explicit
query; a record can mark a corpus rule superseded via the sealed
supersession mechanism and the existing honor applies.

Memory recall cycle, Slice 3.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.decision_ledger import write_decision
from loam.primary_persona.keep_pace.retrieval import (
    RetrievalConfig,
    retrieve,
)

from _helpers_keep_pace import write_corpus


def _config(tmp_path: Path) -> RetrievalConfig:
    memory_dir = tmp_path / "memory"
    write_corpus(memory_dir)
    return RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=memory_dir,
        claude_homes=(),
        objectives_home=tmp_path / "empty-home",
        episode_memory_dir=tmp_path / "ws-memory",
    )


def _write_tilth(mem: Path, **overrides) -> dict:
    kwargs = dict(
        question="How large is the Tilth raise ask?",
        ruling="$750,000 at $4M post-money valuation",
        reasoning="AI-era raises differ; comp-heavy is fine founder-led.",
        entities=("Tilth", "Alan", "raise", "valuation"),
        aliases=("the raise", "newco"),
        source="telegram message 14053, 2026-06-07",
        workstream="tilth",
    )
    kwargs.update(overrides)
    return write_decision(mem, **kwargs)


def test_AC_DLG_3_entity_query_injects_record_whole(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    _write_tilth(cfg.episode_memory_dir)
    block = retrieve(prompt="draft the Tilth raise plan", config=cfg)
    # Whole-record injection (AC.SRF.3 contract): question + ruling +
    # reasoning + source all present, never a one-line pointer.
    assert "How large is the Tilth raise ask?" in block
    assert "$750,000" in block
    assert "AI-era raises differ" in block
    assert "telegram message 14053" in block
    # Positioned for whole-record injection: the record block precedes
    # ordinary pointer lines.
    assert block.index("=== record:") < len(block)


def test_AC_DLG_3_open_record_surfaces_without_query(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    _write_tilth(
        cfg.episode_memory_dir,
        question="Who is Aaron in the deal?",
        ruling="(open)",
        status="open",
        entities=("Aaron", "deal"),
        aliases=(),
    )
    # A work-anchored prompt that shares NO vocabulary with the record.
    block = retrieve(prompt="git safety protocol secrets", config=cfg)
    assert "Who is Aaron in the deal?" in block, (
        "AC.DLG.3: an open record surfaces without an explicit query"
    )


def test_AC_DLG_3_superseded_record_never_surfaces(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    old = _write_tilth(cfg.episode_memory_dir)
    new = _write_tilth(
        cfg.episode_memory_dir, ruling="$900,000 (revised ask)"
    )
    from loam.primary_persona.decision_ledger import supersede_decision

    supersede_decision(old["path"], new["path"])
    block = retrieve(prompt="draft the Tilth raise plan", config=cfg)
    assert "$900,000" in block
    assert "$750,000" not in block, (
        "the superseded ruling must not surface (existing honor applies)"
    )


def test_AC_DLG_3_no_ledger_leaves_output_unchanged(tmp_path: Path) -> None:
    # The no-regression envelope: an absent ledger contributes nothing.
    shared_corpus = tmp_path / "shared-memory"
    write_corpus(shared_corpus)
    cfg_a = RetrievalConfig(
        workspace_root=tmp_path / "a",
        memory_dir=shared_corpus,
        claude_homes=(),
        objectives_home=tmp_path / "empty-home",
    )
    cfg_b = RetrievalConfig(
        workspace_root=tmp_path / "b",
        memory_dir=shared_corpus,
        claude_homes=(),
        objectives_home=tmp_path / "empty-home",
        episode_memory_dir=tmp_path / "empty-ws-memory",
    )
    a = retrieve(prompt="git safety protocol secrets", config=cfg_a)
    b = retrieve(prompt="git safety protocol secrets", config=cfg_b)
    assert a == b
