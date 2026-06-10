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


def test_AC_KP1_3_pointer_text_plain_with_source_path_suffix(
    tmp_path: Path,
) -> None:
    # AC.SRF.1 (memory recall cycle, Slice 2) UPDATED this pin: the
    # injection block is MODEL-facing context, so every pointer line now
    # carries a followable ``[source: <path>]`` suffix. The pre-cycle
    # "NO file paths anywhere in the block" assertion encoded the KP9
    # user-prose lint mis-applied to model-facing context (the named
    # scope error the cycle reverses; the lint keeps its user-facing
    # scope on outbound drafts). The pointer TEXT itself stays plain
    # language — paths appear only in the source suffix.
    cfg = _config(tmp_path)
    block = retrieve(prompt="git safety protocol secrets", config=cfg)
    bullets = [ln for ln in block.splitlines() if ln.strip().startswith("- ")]
    assert bullets, "expected at least one injected pointer line"
    for ln in bullets:
        assert "[source: " in ln, f"pointer line missing source path: {ln!r}"
        text_part = ln.split("[source: ")[0]
        # The plain-language pointer text itself carries no path.
        assert ".md" not in text_part
        assert "/" not in text_part.replace("- ", "")
