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

"""AC.FBM1.S — OUTCOME-ALTITUDE (``outcome-altitude: true``).

A FRESH session (no pre-arranged in-memory state) writes an episode that
LANDS in the single-``workspace`` live store AND is RETRIEVABLE through
the unified surface in a subsequent retrieval call — proving write-path
(AC.FBMW.*) + activation-readiness + unify (AC.FBMU.*) compose
end-to-end.

Outcome-altitude discipline (``feedback_test_outcome_altitude_required``):
this drives the PRODUCTION code chain with NO pre-seeded episodes —
  1. the production caller resolves the repo root from the live cwd
     shape (operator workspace ``<repo>/workspace/``), with no explicit
     --workspace and no env override (the fresh-session condition);
  2. the production enqueue writes a turn record to the live queue;
  3. the production worker drain (default file-backed client factory →
     ``FileMemoryStore.write_episode``) lands the episode at the
     single-``workspace`` live store;
  4. the production unified retrieval entry-point (``retrieve`` with the
     episode store wired) returns the just-written episode.
No layer is stubbed; the only thing NOT exercised here is Luke's live
``~/.claude/settings.json`` hook firing (the owner-gated D3 step + the
runtime AC.FBMA.1 verification) — that is verified post-flip, not in the
seal (plan §10 risk 3).
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona import cli
from loam.primary_persona.memory_write_queue import enqueue
from loam.primary_persona.memory_write_worker import drain_once
from loam.primary_persona.file_memory import memory_dir_for_workspace
from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve


def test_AC_FBM1_S_fresh_write_lands_single_workspace_and_retrieves(
    monkeypatch, tmp_path
):
    # --- FRESH SESSION: no pre-arranged state, no env override -------
    repo_root = tmp_path / "pos3"
    operator_ws = repo_root / "workspace"
    operator_ws.mkdir(parents=True)
    monkeypatch.delenv("LOAM_WORKSPACE_ROOT", raising=False)
    monkeypatch.chdir(operator_ws)  # the live Claude Code project cwd

    # No episodes exist yet — the live store dir is not even created.
    live_store = memory_dir_for_workspace(repo_root)
    assert not (live_store / "episodes").exists()

    # --- (1)+(2) production caller resolution + enqueue --------------
    workspace_root = cli._resolve_workspace(None)
    assert workspace_root == repo_root  # repo root, not operator ws
    enqueue(
        workspace_root=workspace_root,
        turn_id="freshsess:turn01",
        session_id="freshsess",
        user_message="How should we handle the canary rollout?",
        assistant_reply=(
            "We agreed the canary rollout gates on the error-budget "
            "burn rate before promoting to the full fleet."
        ),
    )

    # --- (3) production worker drain → episode store write -----------
    counters = drain_once(workspace_root=workspace_root)
    assert counters["ok"] == 1, f"worker did not land the episode: {counters}"

    # The episode LANDED at the SINGLE-``workspace`` live store.
    assert (live_store / "episodes").exists()
    assert sum(1 for _ in (live_store / "episodes").rglob("*.md")) == 1
    assert "workspace/workspace" not in str(live_store)

    # --- (4) RETRIEVABLE through the unified surface -----------------
    # An empty markdown corpus (this is the fresh-session episode path,
    # not the KP1 corpus path) — the episode must surface on its own.
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    slug_group = _resolve_slug(workspace_root)
    cfg = RetrievalConfig(
        workspace_root=repo_root,
        memory_dir=corpus_dir,
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives",
        episode_memory_dir=live_store,
        episode_group_ids=(slug_group,),
    )
    block = retrieve(prompt="what did we decide about the canary rollout", config=cfg)

    assert block, "the just-written episode was NOT retrievable end-to-end"
    assert "from an earlier turn" in block.lower(), (
        f"episode did not surface through the unified surface; got: {block!r}"
    )
    assert "canary" in block.lower()


def _resolve_slug(workspace_root: Path) -> str:
    from loam.primary_persona.memory_consumer import resolve_workspace_slug

    return resolve_workspace_slug(workspace_root)
