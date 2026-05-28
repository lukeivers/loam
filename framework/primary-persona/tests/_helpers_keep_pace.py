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

"""Shared fixtures for the keep-pace KP1/KP5 tests.

Builds a tmp markdown corpus (the file-based reality KP1 retrieves
over) including a litrpg-canon doc, so the cold-walk (AC.KP1.6) and the
inject/silent/fresh tests run against a real on-disk corpus without
touching the live machine.
"""

from __future__ import annotations

from pathlib import Path


def write_corpus(memory_dir: Path) -> dict[str, Path]:
    """Write a small markdown corpus into ``memory_dir``.

    Returns a dict of named doc paths. The litrpg-canon doc is the one
    the AC.KP1.6 cold-walk must surface via the objective anchor; the
    other docs are distractors so the retrieval is doing real ranking,
    not returning the only file.
    """
    memory_dir.mkdir(parents=True, exist_ok=True)
    docs: dict[str, str] = {
        # NOTE: this canon doc deliberately shares NO token with the
        # vague cold-walk prompts ("continue the batch" / "keep going")
        # so AC.KP1.6 proves the OBJECTIVE ANCHOR (litrpg/canon/patch/
        # production/pipeline) is the sole retrieval path, not a prompt-
        # word collision.
        "feedback_litrpg_canon_consistency.md": (
            "# LitRPG canon consistency for Patch Notes for Reality\n\n"
            "The series canon store tracks character stats, skill trees, "
            "and world rules across all seven novels. Check the canon store "
            "so a chapter does not contradict an earlier established fact. "
            "The litrpg canon is the source of truth for the autonomous "
            "production pipeline.\n"
        ),
        "feedback_revenue_plan.md": (
            "# Revenue independence plan\n\n"
            "Build passive income toward financial independence; convert "
            "active consulting into durable owned assets.\n"
        ),
        "feedback_telegram_channel.md": (
            "# Telegram is the only user channel\n\n"
            "Every reply to the user routes through Telegram; the terminal "
            "is diagnostics only.\n"
        ),
        "feedback_git_safety.md": (
            "# Git safety protocol\n\n"
            "Never commit secrets; create new corrective commits, never "
            "amend a published commit.\n"
        ),
        "feedback_duration_estimation.md": (
            "# Duration estimation in AI-time\n\n"
            "Estimate background-agent work in AI-time, not human-developer "
            "time; use the calibrated rubric.\n"
        ),
    }
    out: dict[str, Path] = {}
    for name, body in docs.items():
        p = memory_dir / name
        p.write_text(body, encoding="utf-8")
        out[name] = p
    return out
