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

"""AC.DLG.OA (outcome-altitude: true) — THE $750k REPLAY. With the
backfilled June-7 Tilth ruling record on disk and NO other pre-arranged
state, the production ask-time path for a "draft the Tilth workstream
plan"-class prompt injects the ruling WHOLE — value, reasoning, and
source pointer all present in the rendered context — before any
drafting surface is reached.

This is the literal 2026-06-09 failure, replayed against production
machinery: the deciding turn contained neither "Tilth" nor "750" (pure
deixis), the 1,200-char path-less injection couldn't carry it, and the
planning agent never saw it. The record's encode-time entity
vocabulary is what bridges the ask to the ruling.

Runs against the LIVE workspace ledger (the backfilled Tilth seed
record); skips (does not fail) when the live ledger is absent (CI /
fresh machine). Rides along on every future memory-touching seal.

Memory recall cycle, Slice 3.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.primary_persona.keep_pace.retrieval import (
    RetrievalConfig,
    retrieve,
)


LIVE_MEMORY_DIR = Path.home() / "pos3" / "workspace" / ".loam" / "memory"
LIVE_CORPUS_DIR = (
    Path.home() / ".claude" / "projects" / "-Users-lukeivers-pos3" / "memory"
)


def _live_tilth_record_present() -> bool:
    d = LIVE_MEMORY_DIR / "decisions"
    if not d.is_dir():
        return False
    return any("tilth" in p.name.lower() for p in d.glob("*.md"))


@pytest.mark.skipif(
    not _live_tilth_record_present(),
    reason="live ledger / Tilth seed record absent (CI / fresh machine)",
)
def test_AC_DLG_OA_tilth_ruling_loads_whole_at_ask_time(
    tmp_path: Path,
) -> None:
    config = RetrievalConfig(
        workspace_root=tmp_path,  # index scratch only; store is live
        memory_dir=LIVE_CORPUS_DIR if LIVE_CORPUS_DIR.is_dir() else None,
        claude_homes=(Path.home() / ".claude",),
        objectives_home=Path.home() / ".claude",
        episode_memory_dir=LIVE_MEMORY_DIR,
    )
    block = retrieve(
        prompt="draft the Tilth workstream plan for the raise",
        config=config,
    )
    assert block, "the ask-time path must inject context for this prompt"
    # The ruling arrives WHOLE: value + reasoning + source pointer.
    assert "750" in block, f"ruling value missing: {block!r}"
    assert "AI-era raises differ" in block or "AI era" in block, (
        f"ruling reasoning missing: {block!r}"
    )
    assert "14053" in block, f"source message pointer missing: {block!r}"
    # And it arrives as a record block, not a truncated pointer line.
    assert "=== record:" in block
