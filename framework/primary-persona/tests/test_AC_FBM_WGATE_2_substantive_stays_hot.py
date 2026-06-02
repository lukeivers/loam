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

"""AC-FBM-WGATE-2 (write-gate precision — substantive turns stay hot).

A substantive Luke turn (real instruction, >8 chars, no junk signature) IS
written under ``EPISODES_SUBDIR`` AND FTS-indexed at full salience —
byte-identical to pre-amendment behaviour; the cold tier stays empty for it.
Write-gate precision matches read-gate precision: no new false positives vs. the
sealed ``compute_salience``. This is the protect-real-messages property on the
WRITE path.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import (
    COLD_SUBDIR,
    EPISODES_SUBDIR,
    FileMemoryStore,
)


_REAL_BODY = (
    "[user]\n"
    "Refactor the salience gate so junk diverts at write time, then run "
    "the touched tests and report the seal SHA.\n"
    "\n"
    "[assistant]\n"
    "On it — moving the gate onto write_episode now.\n"
)


def _write_real(store: FileMemoryStore) -> dict:
    return store.write_episode(
        name="turn/wgate-real-1",
        body=_REAL_BODY,
        source_description="test seed",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="pos3",
    )


def test_AC_FBM_WGATE_2_substantive_written_to_hot_tier(tmp_path: Path) -> None:
    """A substantive turn lands under EPISODES_SUBDIR, not the cold tier."""
    store = FileMemoryStore(memory_dir=tmp_path / "mem")
    result = _write_real(store)
    path = Path(result["path"])
    assert EPISODES_SUBDIR in path.parts, (
        f"a substantive turn must land in the hot episodes dir; path={path}"
    )
    assert COLD_SUBDIR not in path.parts
    # The cold tier carries nothing for a substantive-only ingest.
    cold_root = tmp_path / "mem" / COLD_SUBDIR
    cold_files = list(cold_root.rglob("*.md")) if cold_root.exists() else []
    assert cold_files == [], (
        f"cold tier must be empty after a substantive-only ingest; {cold_files}"
    )


def test_AC_FBM_WGATE_2_substantive_surfaces_in_search(tmp_path: Path) -> None:
    """The substantive turn IS FTS-indexed and surfaces on a keyword query —
    no false positive; the write gate did not divert a real turn."""
    store = FileMemoryStore(memory_dir=tmp_path / "mem")
    _write_real(store)
    out = store.search(query="refactor salience gate", group_ids=["pos3"], num_results=5)
    names = [e.get("name", "") for e in out["episodes"]]
    assert any("wgate-real-1" in n for n in names), (
        f"the substantive turn must surface in search; got {names!r}"
    )


def test_AC_FBM_WGATE_2_salience_field_emitted_full(tmp_path: Path) -> None:
    """The hot-tier episode still carries the salience frontmatter (full) so
    the read-side gate stays correct (defence in depth)."""
    store = FileMemoryStore(memory_dir=tmp_path / "mem")
    result = _write_real(store)
    raw = Path(result["path"]).read_text(encoding="utf-8")
    assert "salience: 1.0" in raw
