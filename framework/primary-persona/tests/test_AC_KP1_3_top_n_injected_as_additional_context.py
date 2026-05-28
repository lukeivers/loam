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

"""AC.KP1.3 — a prompt mentioning a known on-file topic causes the
correct pointer(s) to be injected as additionalContext, capped N<=5."""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve

from _helpers_keep_pace import write_corpus


def _config(tmp_path: Path) -> RetrievalConfig:
    memory_dir = tmp_path / "memory"
    write_corpus(memory_dir)
    # No OBJECTIVES seed file => seed fallback; objectives_home points
    # at an empty home so the seed objectives are the anchor.
    return RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=memory_dir,
        claude_homes=(),
        objectives_home=tmp_path / "empty-home",
    )


def test_AC_KP1_3_known_topic_injects_pointer(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    # A prompt naming a known on-file topic.
    block = retrieve(prompt="remind me about telegram channel rules", config=cfg)
    assert block
    assert "telegram" in block.lower()


def test_AC_KP1_3_injection_is_additional_context_block(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    block = retrieve(prompt="what is the git safety protocol", config=cfg)
    assert block.startswith("[keep-pace]")


def test_AC_KP1_3_capped_at_top_n(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    cfg.top_n = 5
    # A broad prompt likely matching several docs.
    block = retrieve(
        prompt="canon revenue telegram git duration litrpg passive", config=cfg
    )
    # Count injected bullet lines.
    bullets = [ln for ln in block.splitlines() if ln.strip().startswith("- ")]
    assert 1 <= len(bullets) <= 5


def test_AC_KP1_3_no_file_path_in_injection(tmp_path: Path) -> None:
    # Plain-language pointer: NO file path / .md filename leaks (authored
    # plain-by-construction so it passes KP9's Cycle-3 lint).
    cfg = _config(tmp_path)
    block = retrieve(prompt="git safety protocol secrets", config=cfg)
    assert ".md" not in block
    assert "/" not in block.replace("[keep-pace]", "")
