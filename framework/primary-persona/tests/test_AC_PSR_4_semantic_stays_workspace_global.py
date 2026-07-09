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

"""AC.PSR.4 — semantic retrieval stays workspace-global.

Outcome (plan §4 AC.PSR.4, D2): a session in persona P still sees
another workstream's decision/ruling record. The decision-ledger
catch-up sweep AND the per-turn decision branch are NOT session-scoped
— only the episode branch is. This is the load-bearing D2 split: the
episodic thread is private per session; semantic knowledge is shared.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.decision_ledger import run_catch_up_sweep, write_decision
from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve

from _helpers_keep_pace import write_corpus


def test_AC_PSR_4_per_turn_decision_branch_is_global(tmp_path: Path) -> None:
    """In P's session (episode_session_key set), a ruling recorded under
    a DIFFERENT workstream still surfaces in the per-turn block."""
    corpus = tmp_path / "memory"
    write_corpus(corpus)
    ep = tmp_path / "ws-memory"
    write_decision(
        ep,
        question="How large is the Tilth raise ask?",
        ruling="$750,000 at $4M post-money",
        reasoning="AI-era raises differ.",
        entities=("Tilth", "raise"),
        aliases=("the raise",),
        source="telegram message 14053",
        workstream="tilth",
    )
    cfg = RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=corpus,
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives",
        episode_memory_dir=ep,
        episode_group_ids=("pos3",),
        episode_session_key="master-control",
    )
    block = retrieve(prompt="draft the Tilth raise plan", config=cfg)
    assert "$750,000" in block, (
        "a ruling from another workstream must surface even with the "
        "episode branch session-scoped (D2 — semantic is global)"
    )


def test_AC_PSR_4_session_start_catch_up_is_global(tmp_path: Path) -> None:
    """The session-start decision-ledger catch-up sweeps a ruling-shaped
    episode even when it is tagged with ANOTHER persona's session_key —
    the sweep reads all episodes, not a session-filtered subset."""
    ep_dir = tmp_path / "episodes" / "pos3" / "2026-06-09"
    ep_dir.mkdir(parents=True)
    # A ruling-shaped, owner-authored episode tagged for persona loam-dev.
    (ep_dir / "ruled-turn.md").write_text(
        "---\nname: turn/x\nsource: message\ngroup_id: pos3\n"
        "session_key: loam-dev\n---\n"
        "[user]\nApproved. Go with the narrow fence for the cycle.\n"
        "[assistant]\nProceeding with the narrow fence.\n",
        encoding="utf-8",
    )
    block = run_catch_up_sweep(tmp_path)
    assert "narrow fence" in block, (
        "the catch-up sweep must surface a ruling from ANY session — it "
        "is not session-scoped (D2 semantic-global)"
    )
