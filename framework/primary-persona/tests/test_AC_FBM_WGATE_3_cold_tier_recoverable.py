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

"""AC-FBM-WGATE-3 (never-drop — a gated turn is recoverable from the cold tier).

The HARD INVARIANT on the WRITE path: a diverted junk turn is WRITTEN to the cold
tier with its full body verbatim, never deleted. It is recoverable by direct
cold-tier read — the gate diverts from the HOT INDEX, never destroys. A mis-judged
junk turn is therefore re-admittable (read the file back), which is only possible
because nothing was removed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import COLD_SUBDIR, FileMemoryStore


_JUNK_BODY = (
    "[user]\n"
    "<task-notification>\n"
    "<task-id>recoverme</task-id>\n"
    "<status>completed</status>\n"
    "<result>This whole turn is plumbing but must remain on disk verbatim.</result>\n"
    "</task-notification>\n"
    "\n"
    "[assistant]\n"
    "Acknowledged.\n"
)


def test_AC_FBM_WGATE_3_cold_turn_on_disk_verbatim(tmp_path: Path) -> None:
    """The diverted turn exists on disk under the cold tier with its full body."""
    store = FileMemoryStore(memory_dir=tmp_path / "mem")
    result = store.write_episode(
        name="turn/junk-recoverme",
        body=_JUNK_BODY,
        source_description="test seed",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="pos3",
    )
    path = Path(result["path"])
    assert COLD_SUBDIR in path.parts
    assert path.exists(), "the gated turn must still be WRITTEN to disk"
    raw = path.read_text(encoding="utf-8")
    # Full body present verbatim — nothing dropped or compressed.
    assert "recoverme" in raw
    assert "must remain on disk verbatim" in raw
    # Tagged near-zero salience on disk, NOT deleted.
    assert "salience: 0.0" in raw


def test_AC_FBM_WGATE_3_cold_turn_recoverable_by_direct_read(
    tmp_path: Path,
) -> None:
    """The cold tier is walkable on disk — the turn is recoverable by a direct
    cold-tier scan (the re-admit path)."""
    store = FileMemoryStore(memory_dir=tmp_path / "mem")
    store.write_episode(
        name="turn/junk-recoverme",
        body=_JUNK_BODY,
        source_description="test seed",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="pos3",
    )
    cold_root = tmp_path / "mem" / COLD_SUBDIR
    cold_files = list(cold_root.rglob("*.md"))
    assert len(cold_files) == 1, (
        f"exactly one cold-tier episode expected; found {cold_files}"
    )
    assert "recoverme" in cold_files[0].read_text(encoding="utf-8")
