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

"""AC.RVL.4 — DEFAULT_TOP_N / the post-merge count survive only as a NAMED
backstop with an explicit, telemetry-measurable retirement trigger, and the
backstop is a NO-OP on all normal-volume turns.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.keep_pace import retrieval as R
from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve


def _write_corpus(memory_dir: Path, n: int) -> None:
    memory_dir.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        (memory_dir / f"feedback_rule_{i}.md").write_text(
            f"# widgetronic{i} directive\n\nThe widgetronic{i} directive governs {i}.\n",
            encoding="utf-8",
        )


def _config(tmp_path: Path, memory_dir: Path) -> RetrievalConfig:
    return RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=memory_dir,
        claude_homes=(),
        objectives_home=tmp_path / "no-obj",
    )


def test_AC_RVL_4_backstop_names_a_retirement_trigger_in_source() -> None:
    src = Path(R.__file__).read_text(encoding="utf-8")
    # The DEFAULT_TOP_N declaration carries an explicit, telemetry-measurable
    # retirement trigger (not a bare integer).
    assert "DEFAULT_TOP_N = " in src
    assert "RETIREMENT TRIGGER" in src
    assert "telemetry" in src.lower()
    assert "p99 floor-clearing-set-size" in src, (
        "the retirement criterion must be explicit + telemetry-measurable"
    )


def test_AC_RVL_4_backstop_is_a_no_op_on_normal_volume_turns(tmp_path: Path) -> None:
    # A normal-volume turn (fewer floor-clearing records than the backstop).
    memory_dir = tmp_path / "corpus"
    _write_corpus(memory_dir, 3)
    cfg = _config(tmp_path, memory_dir)
    prompt = "widgetronic directives widgetronic0 widgetronic1 widgetronic2"

    # Output with the backstop at its shipped value vs at a huge no-op value
    # must be IDENTICAL — the backstop does not bite on a normal turn.
    at_backstop = retrieve(prompt=prompt, config=cfg)
    R_backstop = R.DEFAULT_TOP_N
    try:
        R.DEFAULT_TOP_N = 100_000  # a no-op ceiling
        # Rebuild config default too (top_n defaults to DEFAULT_TOP_N at
        # dataclass-definition time, so pass it explicitly for the no-op run).
        cfg_noop = RetrievalConfig(
            workspace_root=tmp_path,
            memory_dir=memory_dir,
            claude_homes=(),
            objectives_home=tmp_path / "no-obj",
            top_n=100_000,
        )
        at_noop = retrieve(prompt=prompt, config=cfg_noop)
    finally:
        R.DEFAULT_TOP_N = R_backstop

    assert at_backstop == at_noop, (
        "a normal-volume turn must render identically at the backstop vs at its "
        "no-op value — the count backstop is not a set-determiner"
    )
    assert at_backstop, "sanity: the normal turn produced a non-empty injection"


def test_AC_RVL_4_restoring_five_reproduces_legacy_count_cut() -> None:
    """Reversibility (§15): the post-merge count backstop is the named lever —
    restoring it to the legacy 5 re-imposes the count cut on the merge (the
    episode-inclusive path where ``combined[:top_n]`` operates); the raised
    backstop leaves the whole set. (The corpus-only path is now floor + byte
    only — the corpus search truncation was STRUCTURALLY removed per RF-1, so it
    is not governed by this lever.)"""
    from loam.primary_persona.keep_pace.retrieval import _merge_by_score

    corpus = [
        {"path": f"/x/c{i}.md", "title": f"c{i}", "pointer": f"c{i}", "score": 50.0 - i}
        for i in range(6)
    ]
    episodes = [
        {"pointer": f"e{i}", "score": 40.0 - i, "_episode": True} for i in range(6)
    ]
    at_legacy = _merge_by_score(corpus, episodes, top_n=5)
    assert len(at_legacy) == 5, "restoring top_n=5 must re-impose the merge count cut"
    at_backstop = _merge_by_score(corpus, episodes, top_n=50)
    assert len(at_backstop) == 12, "the raised backstop leaves the whole merged set"
