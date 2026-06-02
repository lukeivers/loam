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

"""AC-FBM-WGATE-1 (write-time salience gate — junk diverted to cold tier).

A ``<task-notification>``-opening turn written through the production
``write_episode`` path is NOT written under ``EPISODES_SUBDIR`` and is NOT in the
FTS index; a search for its boilerplate tokens returns it absent from the
surfaced set. It IS written under ``COLD_SUBDIR``. This is the structural fix:
the gate now diverts junk AT WRITE so it never enters the hot retrieval index.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import (
    COLD_SUBDIR,
    EPISODES_SUBDIR,
    FileMemoryStore,
)


_JUNK_BODY = (
    "[user]\n"
    "<task-notification>\n"
    "<task-id>wgate-junk-1</task-id>\n"
    "<status>completed</status>\n"
    "<result>uniquetoken_notindexed agent finished the build.</result>\n"
    "</task-notification>\n"
    "\n"
    "[assistant]\n"
    "Acknowledged.\n"
)


def _write_junk(store: FileMemoryStore) -> dict:
    return store.write_episode(
        name="turn/wgate-junk-1",
        body=_JUNK_BODY,
        source_description="test seed",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="pos3",
    )


def test_AC_FBM_WGATE_1_junk_not_under_hot_episodes_dir(tmp_path: Path) -> None:
    """The junk turn is NOT written under EPISODES_SUBDIR (the hot tier)."""
    store = FileMemoryStore(memory_dir=tmp_path / "mem")
    result = _write_junk(store)
    path = Path(result["path"])
    assert EPISODES_SUBDIR not in path.parts, (
        f"junk must not land in the hot episodes dir; path={path}"
    )
    # The hot tier carries nothing for this turn.
    hot_root = tmp_path / "mem" / EPISODES_SUBDIR
    hot_files = list(hot_root.rglob("*.md")) if hot_root.exists() else []
    assert hot_files == [], (
        f"hot tier must be empty after a junk-only ingest; found {hot_files}"
    )


def test_AC_FBM_WGATE_1_junk_written_under_cold_tier(tmp_path: Path) -> None:
    """The junk turn IS written under COLD_SUBDIR."""
    store = FileMemoryStore(memory_dir=tmp_path / "mem")
    result = _write_junk(store)
    path = Path(result["path"])
    assert COLD_SUBDIR in path.parts, (
        f"junk must be diverted to the cold tier; path={path}"
    )
    assert path.exists()


def test_AC_FBM_WGATE_1_junk_absent_from_surfaced_search(tmp_path: Path) -> None:
    """A search for the junk's unique boilerplate token surfaces nothing —
    the junk never entered the hot retrieval index (FTS not built for it; the
    grep fallback scans EPISODES_SUBDIR only)."""
    store = FileMemoryStore(memory_dir=tmp_path / "mem")
    _write_junk(store)
    out = store.search(
        query="uniquetoken_notindexed",
        group_ids=["pos3"],
        num_results=5,
    )
    assert out["episodes"] == [], (
        "the cold-tier junk turn must not appear in the surfaced search set; "
        f"got {out['episodes']!r}"
    )
