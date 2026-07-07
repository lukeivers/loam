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

"""AC.RTEL.6 — standing / append + daily rotation. Two turns append two
records to the SAME day's file (append-only, never overwrite); the file
lives at the daily-rotated ``retrieval-telemetry-<UTC-date>.jsonl`` path
under the workspace ``.loam`` telemetry dir.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve
from loam.primary_persona.keep_pace.retrieval_telemetry import (
    telemetry_dir_for_workspace,
)

from _helpers_keep_pace import write_corpus


def test_AC_RTEL_6_two_turns_append_to_one_day_file(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "memory"
    write_corpus(corpus_dir)
    telemetry_dir = tmp_path / "tel"

    cfg = RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=corpus_dir,
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives",
        telemetry_dir=telemetry_dir,
    )
    retrieve(prompt="continue the batch", config=cfg)
    retrieve(prompt="keep going on the pipeline", config=cfg)

    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    day_file = telemetry_dir / f"retrieval-telemetry-{day}.jsonl"
    assert day_file.exists(), f"expected the day file {day_file}"

    lines = [ln for ln in day_file.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 2, (
        f"append-only rotation failed; expected 2 lines, got {len(lines)}"
    )
    # Only the one day file exists (no per-turn file explosion).
    assert sorted(p.name for p in telemetry_dir.glob("*.jsonl")) == [
        f"retrieval-telemetry-{day}.jsonl"
    ]


def test_AC_RTEL_6_telemetry_dir_is_gitignored_loam_sibling(tmp_path: Path) -> None:
    """The resolved standing path lives under ``<ws>/workspace/.loam/`` —
    the gitignored state dir, beside the episode store."""
    resolved = telemetry_dir_for_workspace(tmp_path)
    assert resolved == tmp_path / "workspace" / ".loam" / "retrieval-telemetry"
