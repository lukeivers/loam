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

"""AC.KP1.5 — fresh read each turn: a corpus change between turns is
reflected on the next turn without a session restart."""

from __future__ import annotations

import time
from pathlib import Path

from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve

from _helpers_keep_pace import write_corpus


def test_AC_KP1_5_mid_session_write_seen_next_turn(tmp_path: Path) -> None:
    memory_dir = tmp_path / "memory"
    write_corpus(memory_dir)
    cfg = RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=memory_dir,
        claude_homes=(),
        objectives_home=tmp_path / "empty-home",
    )
    # Turn 1: no corpus doc mentions "obsidianforge", so the pointer is
    # absent from the (objective-anchored) results.
    turn1 = retrieve(prompt="tell me about obsidianforge tooling", config=cfg)
    assert "obsidianforge" not in turn1.lower()

    # A new corpus entry lands mid-"session" (same config object, no
    # restart — the index re-syncs on the next search).
    time.sleep(0.01)
    (memory_dir / "feedback_obsidianforge.md").write_text(
        "# Obsidianforge tooling protocol\n\n"
        "The obsidianforge tooling protocol builds obsidianforge artefacts "
        "via the obsidianforge pipeline.\n",
        encoding="utf-8",
    )

    # Turn 2 (same config): the new entry is now seen WITHOUT a restart —
    # this is the fresh-read-each-turn contract.
    turn2 = retrieve(prompt="tell me about obsidianforge tooling", config=cfg)
    assert "obsidianforge" in turn2.lower(), (
        "a corpus write between turns must be reflected on the next turn "
        "without a session restart (AC.KP1.5)"
    )
