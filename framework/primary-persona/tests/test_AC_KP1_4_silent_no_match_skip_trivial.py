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

"""AC.KP1.4 — silent on no-match (no noise); trivial prompts (greetings,
acks) are skipped."""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve
from loam.primary_persona.keep_pace.work_anchor import is_trivial_prompt

from _helpers_keep_pace import write_corpus


def _config(tmp_path: Path) -> RetrievalConfig:
    memory_dir = tmp_path / "memory"
    write_corpus(memory_dir)
    return RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=memory_dir,
        claude_homes=(),
        objectives_home=tmp_path / "empty-home",
    )


@pytest.mark.parametrize(
    "trivial",
    ["hi", "hey", "thanks", "thank you!", "ok", "okay.", "got it", "yes", "lol", "gn"],
)
def test_AC_KP1_4_trivial_prompts_detected(trivial: str) -> None:
    assert is_trivial_prompt(trivial) is True


@pytest.mark.parametrize(
    "working",
    ["continue", "keep going", "continue the batch", "what next on the canon"],
)
def test_AC_KP1_4_working_prompts_not_trivial(working: str) -> None:
    # A vague-but-working prompt is NOT trivial — the objective anchor
    # rescues it (the AC.KP1.6 case).
    assert is_trivial_prompt(working) is False


def test_AC_KP1_4_trivial_prompt_injects_nothing(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    assert retrieve(prompt="thanks!", config=cfg) == ""


def test_AC_KP1_4_no_match_is_silent(tmp_path: Path) -> None:
    # No-match = the work-anchored key (prompt + objective + subgoal)
    # matches NOTHING in the corpus. Use a corpus with no docs relevant
    # to the prompt OR the seed objectives → empty injection (silent).
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    (memory_dir / "feedback_unrelated.md").write_text(
        "# Quokka husbandry\n\nNotes on quokka feeding schedules.\n",
        encoding="utf-8",
    )
    cfg = RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=memory_dir,
        claude_homes=(),
        objectives_home=tmp_path / "empty-home",
    )
    block = retrieve(prompt="semaphore xylophone obscure terms", config=cfg)
    assert block == ""
