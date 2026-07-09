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

"""AC.PSR.1 — session-start resumes persona P's thread only.

Outcome (plan §4 AC.PSR.1, D1/D2): at session-start in persona P, with
episodes from P AND from other personas in the store, the active-thread
digest reconstructs P's thread and includes NONE of the other personas'
episodes.

The fixture is shaped to FAIL a naive method (plan §2A Finding B): P's
tagged episodes fall OUTSIDE the 32 newest all-persona files
(``recent_episodes`` collects ``limit*4`` path-only before reading
frontmatter). A post-filter-after-``limit`` method AND a naive
frontmatter filter that runs after the ``limit*4`` collection cut both
return an EMPTY (or Q-only) thread. Only a persona-aware bounded walk
that reads frontmatter in-walk and counts P-matches toward the limit
surfaces P's window.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from loam.primary_persona.active_thread import (
    ACTIVE_THREAD_MARKER,
    build_active_thread_contributor,
)
from loam.primary_persona.file_memory import FileMemoryStore

_SLUG = "pos3"


def _store(root: Path) -> FileMemoryStore:
    return FileMemoryStore(memory_dir=root / "workspace" / ".loam" / "memory")


def _seed_interleaved(root: Path) -> None:
    """40 NEWER persona-Q episodes + 8 OLDER persona-P episodes.

    P is quiet-while-Q-was-chatty: P's episodes are NOT among the 32
    newest all-persona files (Finding B — the primary resume-after-idle
    scenario)."""
    store = _store(root)
    now = datetime.now(timezone.utc)
    # 40 newer Q episodes (fill the 32-file horizon and then some).
    for i in range(40):
        store.write_episode(
            name=f"turn/q-{i}",
            body=f"PERSONA-Q unrelated chatter item {i} about widgets",
            source_description="t",
            reference_time=now - timedelta(hours=i + 1),
            source="message",
            group_id=_SLUG,
            session_key="loam-dev",
        )
    # 8 older P episodes on the aurora-migration thread.
    for i in range(8):
        store.write_episode(
            name=f"turn/p-{i}",
            body=f"PERSONA-P aurora migration thread step {i} continues",
            source_description="t",
            reference_time=now - timedelta(days=20 + i),
            source="message",
            group_id=_SLUG,
            session_key="master-control",
        )


def test_AC_PSR_1_session_start_surfaces_only_P(tmp_path: Path) -> None:
    _seed_interleaved(tmp_path)
    fn = build_active_thread_contributor(
        _store(tmp_path),
        workspace_root=tmp_path,
        workspace_slug=_SLUG,
        session_key="master-control",
    )
    block = fn({})
    assert ACTIVE_THREAD_MARKER in block, "expected a non-empty P thread"
    # P's window is present (the bounded walk reached the older P dirs).
    assert "aurora migration" in block, (
        "persona P's thread must surface even though P's episodes fall "
        "outside the 32 newest all-persona files (Finding B)"
    )
    # NONE of persona Q's episodes appear.
    assert "PERSONA-Q" not in block, (
        "no other-persona episode may surface in P's resume"
    )


def test_AC_PSR_1_other_persona_sees_only_its_own(tmp_path: Path) -> None:
    """The symmetric guarantee — persona Q resumes Q's thread, not P's."""
    _seed_interleaved(tmp_path)
    fn = build_active_thread_contributor(
        _store(tmp_path),
        workspace_root=tmp_path,
        workspace_slug=_SLUG,
        session_key="loam-dev",
    )
    block = fn({})
    assert "PERSONA-Q" in block
    assert "PERSONA-P" not in block, (
        "persona Q must not resume persona P's thread"
    )
