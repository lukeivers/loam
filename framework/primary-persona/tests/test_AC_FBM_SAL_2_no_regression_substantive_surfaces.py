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

"""AC-FBM-SAL-2 (NO-REGRESSION — outcome-altitude) — B3.

A substantive episode (full salience) still surfaces normally in
``retrieve()``; the empty-episode early-return in ``_merge_by_score`` stays
byte-identical (the FBMU.2 invariant the gate must not disturb). The
rank-normalize + rule-weighting + FBMU suites staying green is asserted by
those suites themselves; this file proves the salience-gate path does not
regress a real turn and preserves the empty-episode early-return identity.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import FileMemoryStore
from loam.primary_persona.keep_pace.retrieval import (
    RetrievalConfig,
    _merge_by_score,
    retrieve,
)


SUBJECT = "litrpgcanonweaver"


def test_AC_FBM_SAL_2_substantive_episode_still_surfaces(tmp_path: Path) -> None:
    """A real, substantive turn (full salience) surfaces normally."""
    episode_dir = tmp_path / "episodes-store"
    store = FileMemoryStore(memory_dir=episode_dir)
    store.write_episode(
        name="turn/real-decision",
        body=(
            "[user]\n"
            f"We locked the {SUBJECT} pipeline design today — three stages, "
            f"canon store first, then the chapter loop, then the {SUBJECT} "
            "regression check. Capture it.\n"
            "\n"
            "[assistant]\n"
            f"Captured the {SUBJECT} pipeline decision durably.\n"
        ),
        source_description="test seed",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="pos3",
    )
    cfg = RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=None,
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives",
        episode_memory_dir=episode_dir,
        episode_group_ids=("pos3",),
        top_n=5,
    )
    block = retrieve(prompt=f"what did we decide about the {SUBJECT} pipeline", config=cfg)
    assert block, "a substantive full-salience episode must surface"
    assert SUBJECT in block, (
        f"the substantive episode must surface normally; block={block!r}"
    )


def test_AC_FBM_SAL_2_empty_episode_early_return_byte_identical() -> None:
    """With no episode hits, ``_merge_by_score`` returns ``corpus_hits``
    unchanged (same objects, same order) — the salience gate must not run on
    the empty-episode path (the FBMU.2 byte-identical invariant)."""
    corpus_hits = [
        {"pointer": "rule A", "score": 9.0},
        {"pointer": "rule B", "score": 1.0},
    ]
    out = _merge_by_score(corpus_hits, [], top_n=5)
    assert out is corpus_hits, "empty-episode path must return the same list object"


def test_AC_FBM_SAL_2_corpus_hit_never_gated() -> None:
    """A corpus hit (which declares no ``_salience``) rides at full salience
    and is never gated — only episodes carry a sub-full salience."""
    corpus_hits = [{"pointer": "rule A", "score": 5.0}]
    episode_hits = [
        {"pointer": "real episode", "score": 5.0, "_episode": True, "_salience": 1.0},
    ]
    out = _merge_by_score(corpus_hits, episode_hits, top_n=5)
    pointers = [h["pointer"] for h in out]
    assert "rule A" in pointers and "real episode" in pointers
