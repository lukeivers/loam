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

"""AC.MFBM.1 — Stop-hook writes the turn's episode to a file under
the workspace's loam memory dir.

Plan ref: ``oss-v0-1-0-publish-memory-pivot.md`` §5 AC.MFBM.1.

Verification (per plan): after N turns in a fresh workspace, the
count of files under the chosen dir equals N (or N±1 for in-flight
turns); each file's mtime is within 5s of its turn's Stop event;
each file contains the ``[user]`` + ``[persona]`` body bundling the
turn matched a fixture turn-id.

Implementation under test:
:mod:`loam.primary_persona.file_memory.FileMemoryStore`.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import (
    FileMemoryStore,
    memory_dir_for_workspace,
)


def test_AC_MFBM_1_write_episode_creates_one_file_at_canonical_path(
    tmp_path: Path,
) -> None:
    """One write_episode call yields one markdown file under the
    canonical episodes/<group>/<date>/ path."""
    memory_dir = memory_dir_for_workspace(tmp_path)
    store = FileMemoryStore(memory_dir=memory_dir)

    ref = datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = store.write_episode(
        name="turn/session-x:abc123def456",
        body="[user]\nhello\n\n[persona]\nworld\n",
        source_description="primary-persona turn",
        reference_time=ref,
        source="message",
        group_id="alpha",
    )

    assert "path" in result
    p = Path(result["path"])
    assert p.exists()
    assert p.suffix == ".md"
    # Path-shape: episodes/<group>/<date>/<stem>.md
    assert p.parent.name == "2026-05-01"
    assert p.parent.parent.name == "alpha"
    assert p.parent.parent.parent.name == "episodes"


def test_AC_MFBM_1_write_episode_body_carries_user_and_persona_blocks(
    tmp_path: Path,
) -> None:
    """The episode body bundles the user message and persona reply
    under labelled blocks (parity with the existing TurnAggregator
    composition shape)."""
    memory_dir = memory_dir_for_workspace(tmp_path)
    store = FileMemoryStore(memory_dir=memory_dir)
    body = "[user]\nwhat's the workspace?\n\n[persona]\npos-v2 rebuild.\n"
    result = store.write_episode(
        name="turn/x:y",
        body=body,
        source_description="t",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="g",
    )
    content = Path(result["path"]).read_text(encoding="utf-8")
    assert "[user]" in content
    assert "[persona]" in content
    assert "pos-v2 rebuild." in content


def test_AC_MFBM_1_count_after_N_turns_equals_N(
    tmp_path: Path,
) -> None:
    """N writes → N files on disk."""
    memory_dir = memory_dir_for_workspace(tmp_path)
    store = FileMemoryStore(memory_dir=memory_dir)
    for i in range(7):
        store.write_episode(
            name=f"turn/sess:{i:012x}",
            body=f"[user]\nq{i}\n\n[persona]\nr{i}\n",
            source_description="t",
            reference_time=datetime(2026, 5, 1, 12, 0, i, tzinfo=timezone.utc),
            source="message",
            group_id="alpha",
        )
    files = list((memory_dir / "episodes" / "alpha").rglob("*.md"))
    assert len(files) == 7


def test_AC_MFBM_1_mtime_within_5s_of_write(
    tmp_path: Path,
) -> None:
    """Each file's mtime is close to the write moment (verification:
    'within 5s of its turn's Stop event')."""
    memory_dir = memory_dir_for_workspace(tmp_path)
    store = FileMemoryStore(memory_dir=memory_dir)
    before = time.time()
    result = store.write_episode(
        name="turn/x:y",
        body="b",
        source_description="t",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="g",
    )
    after = time.time()
    mtime = Path(result["path"]).stat().st_mtime
    assert before - 1 <= mtime <= after + 1


def test_AC_MFBM_1_atomic_write_no_tmp_file_left(
    tmp_path: Path,
) -> None:
    """The tmp+rename pattern leaves no .tmp residual after a
    successful write."""
    memory_dir = memory_dir_for_workspace(tmp_path)
    store = FileMemoryStore(memory_dir=memory_dir)
    result = store.write_episode(
        name="turn/x:y",
        body="b",
        source_description="t",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="g",
    )
    parent = Path(result["path"]).parent
    tmp_files = list(parent.glob("*.md.tmp"))
    assert tmp_files == []
