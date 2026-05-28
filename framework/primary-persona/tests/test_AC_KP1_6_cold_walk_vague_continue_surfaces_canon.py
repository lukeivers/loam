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

"""AC.KP1.6 — OUTCOME-ALTITUDE cold-walk (``outcome-altitude: true``).

The direct test of tonight's failure: invoking the PRODUCTION
retrieval entry-point with NO pre-arranged retrieval state, with a
vague prompt ("continue the batch" / "keep going") AND an active
fiction objective, surfaces the litrpg canon pointer via the objective
anchor (the term the bare prompt cannot supply).

Outcome-altitude discipline (``feedback_test_outcome_altitude_required``):
  - PRODUCTION entry-point: ``retrieval.retrieve`` (the real callable
    the staged live wiring registers), NOT a unit helper.
  - NO pre-arranged retrieval state: no fixture pre-loads the canon
    pointer into the working set; the corpus is on disk, the objectives
    fall back to the in-source SEED (no live OBJECTIVES.md written),
    and the index does not exist until ``retrieve`` builds it.
  - The canon pointer MUST be retrieved by the work-anchor — the vague
    prompt alone tokenizes to almost nothing; only the active fiction
    objective's text ("LitRPG", "Patch Notes for Reality", "production
    pipeline", "canon") pulls the canon doc out of the corpus.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve

from _helpers_keep_pace import write_corpus


def _cold_config(tmp_path: Path) -> RetrievalConfig:
    """A cold workspace: corpus on disk, NO objectives file (seed
    fallback), NO pre-built index. This is the no-pre-arranged-state
    surface the cold-walk requires."""
    memory_dir = tmp_path / "memory"
    write_corpus(memory_dir)
    # objectives_home points at a dir with NO OBJECTIVES.md → the
    # entry-point falls back to the in-source SEED (the two real
    # objectives), so the fiction objective is active with no fixture
    # pre-loading it.
    return RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=memory_dir,
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives-file-here",
    )


@pytest.mark.parametrize("vague_prompt", ["continue the batch", "keep going"])
def test_AC_KP1_6_vague_continue_surfaces_canon(
    tmp_path: Path, vague_prompt: str
) -> None:
    cfg = _cold_config(tmp_path)

    # Sanity floor: the cold-walk truly has no pre-arranged state — the
    # index file does not exist before the production call.
    from loam.primary_persona.keep_pace.corpus_index import default_index_path

    assert not default_index_path(tmp_path).exists()

    # THE COLD WALK: production entry-point, vague prompt, no last-topic.
    block = retrieve(prompt=vague_prompt, config=cfg)

    # The litrpg canon pointer surfaced — via the objective anchor, NOT
    # the bare prompt (which carries no "litrpg"/"canon" token).
    assert block, "the cold-walk produced NO injection — tonight's failure recurs"
    assert "canon" in block.lower() or "litrpg" in block.lower(), (
        f"the canon pointer did not surface; got: {block!r}"
    )


def test_AC_KP1_6_bare_prompt_alone_would_miss(tmp_path: Path) -> None:
    """Control: the SAME vague prompt with NO active objective surfaces
    nothing — proving the objective anchor (not the prompt) is what
    rescues the retrieval. This is the mechanism tonight's failure
    lacked."""
    memory_dir = tmp_path / "memory"
    write_corpus(memory_dir)

    # Monkeypatch-free control: an objectives_home whose seed we suppress
    # by pointing the anchor at an empty objective set via a config with
    # the seed objectives filtered. We model "no active objective" by
    # writing an OBJECTIVES.md with both objectives retired.
    from loam.primary_persona.keep_pace import objectives as obj

    home = tmp_path / "retired-home"
    home.mkdir(parents=True, exist_ok=True)
    retired = [
        obj.Objective(
            slug=o.slug,
            status="retired",
            objective=o.objective,
            completion=o.completion,
            detail_path=o.detail_path,
            subgoals=o.subgoals,
        )
        for o in obj.SEEDED_OBJECTIVES
    ]
    (home / "OBJECTIVES.md").write_text(
        obj.render_register(retired), encoding="utf-8"
    )
    cfg = RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=memory_dir,
        claude_homes=(),
        objectives_home=home,
    )
    # With no active objective, the bare vague prompt surfaces nothing.
    # "keep going" shares no token with any corpus doc or the register,
    # so the ONLY thing that could surface the canon pointer is an active
    # objective anchor — and there is none here (all retired).
    block = retrieve(prompt="keep going", config=cfg)
    assert block == "", (
        "without the objective anchor the vague prompt should miss — "
        "this is the gap the work-anchor closes"
    )
