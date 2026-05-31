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

"""AC-FBM-SAL-3 (NEVER-DELETE — load-bearing, outcome-altitude) — B3.

The HARD INVARIANT: salience gates SURFACING only, NEVER storage. After
ingest, a junk episode is still STORED on disk verbatim and retrievable by
DIRECT lookup (read the file / ``recent_episodes``), even though it is gated
from the surfaced recall set. This is the line that separates a memory system
that protects the user from one that betrays them — a mis-judged junk turn is
re-admittable (AC-FBM-SAL-4), which is only possible because it was never
removed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import FileMemoryStore


_JUNK_BODY = (
    "[user]\n"
    "<task-notification>\n"
    "<task-id>keepme123</task-id>\n"
    "<status>completed</status>\n"
    "<result>This whole turn is plumbing but must remain on disk.</result>\n"
    "</task-notification>\n"
    "\n"
    "[assistant]\n"
    "Acknowledged.\n"
)


def test_AC_FBM_SAL_3_junk_episode_still_written_to_disk(tmp_path: Path) -> None:
    """A junk turn is still WRITTEN to disk with its full body verbatim."""
    episode_dir = tmp_path / "episodes-store"
    store = FileMemoryStore(memory_dir=episode_dir)
    result = store.write_episode(
        name="turn/junk-keepme",
        body=_JUNK_BODY,
        source_description="test seed",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="pos3",
    )
    # The write returned a path; the file exists on disk.
    path = Path(result["path"])
    assert path.exists(), "the junk episode must still be WRITTEN to disk"
    raw = path.read_text(encoding="utf-8")
    # The full body is present verbatim — nothing dropped or compressed.
    assert "keepme123" in raw
    assert "must remain on disk" in raw
    # The salience field is recorded (near-zero) but does NOT remove the body.
    assert "salience: 0.0" in raw, (
        "the junk episode is tagged near-zero salience on disk, not deleted"
    )


def test_AC_FBM_SAL_3_junk_episode_retrievable_by_direct_lookup(
    tmp_path: Path,
) -> None:
    """The junk episode is reachable by DIRECT recency lookup
    (``recent_episodes``), proving storage is untouched — only the keyword
    SURFACING path is gated."""
    episode_dir = tmp_path / "episodes-store"
    store = FileMemoryStore(memory_dir=episode_dir)
    store.write_episode(
        name="turn/junk-keepme",
        body=_JUNK_BODY,
        source_description="test seed",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="pos3",
    )
    recents = store.recent_episodes(group_ids=["pos3"], limit=10)
    names = [r.get("name", "") for r in recents]
    assert any("junk-keepme" in n for n in names), (
        "the junk episode must remain reachable by direct lookup — salience "
        f"gates surfacing, not storage; recents={names!r}"
    )
