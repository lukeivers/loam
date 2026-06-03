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

"""AC.RQ80.3 (#80 cap-not-delete / norm-not-zero guard) — the two levers BOUND
their targets, they do not DELETE them:

  * the anchor is CAPPED, not deleted — >= 1 anchor token survives whenever the
    anchor has tokens, and the AC.KP1.6 vague-"continue" objective-rescue still
    surfaces a hit;
  * an omnibus doc is length-NORMALIZED, not ZEROED — its penalized relevance
    stays STRICTLY POSITIVE (floored at LENGTH_NORM_FLOOR), so it remains
    retrievable rather than being filtered out entirely.

Plan: docs/plans/fbm-retrieval-quality-anchor-cap-omnibus-norm.md §AC.RQ80.3.
"""

from __future__ import annotations

from pathlib import Path

import sys

from loam.primary_persona.keep_pace.corpus_index import (
    LENGTH_NORM_FLOOR,
    _length_penalty,
)
from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve
from loam.primary_persona.keep_pace.work_anchor import (
    MIN_ANCHOR_FLOOR,
    WorkAnchor,
    tokenize,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _helpers_keep_pace import write_corpus  # noqa: E402


_LONG_OBJECTIVE = (
    "Build durable robust financial independence weighted toward passive income "
    "target active consulting bootstrap engine convert into assets investing "
    "real estate ip catalog ai operated bought businesses until work optional"
)


def test_AC_RQ80_3_anchor_capped_not_deleted() -> None:
    """The anchor is CAPPED, not DELETED — >= 1 anchor token survives even a
    rich prompt, so the standing objective context is still present."""
    prompt = "can we use the Anthropic API key for an LLM call"
    anchor = WorkAnchor(prompt=prompt, objective_texts=[_LONG_OBJECTIVE])
    tokens = anchor.query_tokens()
    prompt_tokens = set(tokenize(prompt))
    anchor_contributed = [t for t in tokens if t not in prompt_tokens]
    assert len(anchor_contributed) >= 1, (
        "the anchor must NOT be deleted — at least one anchor token survives "
        f"the cap; query={tokens!r}"
    )
    # The floor guarantees at least MIN_ANCHOR_FLOOR when the anchor has that
    # many distinct tokens (it does here).
    assert len(anchor_contributed) >= MIN_ANCHOR_FLOOR


def test_AC_RQ80_3_vague_continue_rescue_still_fires(tmp_path: Path) -> None:
    """AC.KP1.6 behaviour preserved: a vague "continue" still surfaces the
    litrpg canon pointer via the (capped-but-present) objective anchor."""
    memory_dir = tmp_path / "memory"
    write_corpus(memory_dir)
    cfg = RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=memory_dir,
        claude_homes=(tmp_path,),
        objectives_home=tmp_path / "no-objectives-file-here",
    )
    block = retrieve(prompt="continue the batch", config=cfg)
    assert block, "the capped anchor must still produce an injection"
    assert "canon" in block.lower() or "litrpg" in block.lower(), (
        f"the objective-anchor rescue must still surface the canon pointer "
        f"despite the cap; got {block!r}"
    )


def test_AC_RQ80_3_omnibus_penalty_strictly_positive() -> None:
    """The length penalty is BOUNDED below — an omnibus doc is nudged down, NOT
    zeroed, so it stays retrievable (penalty in [LENGTH_NORM_FLOOR, 1.0])."""
    # An absurdly long doc still gets a penalty >= the floor, never 0.
    for doclen in (2_000, 10_000, 100_000, 10_000_000):
        pen = _length_penalty(doclen)
        assert pen >= LENGTH_NORM_FLOOR > 0.0, (
            f"omnibus length penalty must stay >= {LENGTH_NORM_FLOOR} (never "
            f"zeroed); got {pen} for doclen={doclen}"
        )
        assert pen < 1.0, "a doc past the pivot must be penalized (< 1.0)"
    # A short doc is a no-op (penalty exactly 1.0).
    assert _length_penalty(10) == 1.0
