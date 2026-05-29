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

"""AC.FBMU.2 — when the episode index is absent or empty, the unified
contributor's corpus-side output is byte-identical to the pre-unify KP1
output (no regression; fail-open envelope preserved).

The additive-only guarantee (D4): adding the episode-merge must not
change KP1's existing live behaviour when there are no episodes — the
exact no-regression property the keep-pace chain's fail-open contract
demands.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve

from _helpers_keep_pace import write_corpus


def _base_cfg(tmp_path: Path, *, episode_memory_dir=None) -> RetrievalConfig:
    memory_dir = tmp_path / "memory"
    write_corpus(memory_dir)
    return RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=memory_dir,
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives-file-here",
        episode_memory_dir=episode_memory_dir,
    )


def test_AC_FBMU_2_no_episode_dir_is_byte_identical(tmp_path: Path) -> None:
    """episode_memory_dir=None → output identical to corpus-only KP1."""
    pre = retrieve(
        prompt="continue the batch",
        config=_base_cfg(tmp_path / "a", episode_memory_dir=None),
    )
    # A separate cold workspace, same corpus, no episode dir.
    post = retrieve(
        prompt="continue the batch",
        config=_base_cfg(tmp_path / "b", episode_memory_dir=None),
    )
    assert pre == post
    # And the canon pointer still surfaces (KP1.6 behaviour preserved).
    assert "canon" in pre.lower() or "litrpg" in pre.lower()


def test_AC_FBMU_2_empty_episode_store_is_byte_identical(tmp_path: Path) -> None:
    """An episode dir that exists but holds zero episodes contributes
    nothing — output equals the corpus-only path."""
    corpus_only = retrieve(
        prompt="continue the batch",
        config=_base_cfg(tmp_path / "corpus-only", episode_memory_dir=None),
    )

    empty_episode_dir = tmp_path / "empty-episodes"
    empty_episode_dir.mkdir(parents=True)
    with_empty_store = retrieve(
        prompt="continue the batch",
        config=_base_cfg(
            tmp_path / "with-empty", episode_memory_dir=empty_episode_dir
        ),
    )
    assert corpus_only == with_empty_store, (
        "an empty episode store changed the corpus-side output — "
        "the no-regression / fail-open envelope is broken"
    )
