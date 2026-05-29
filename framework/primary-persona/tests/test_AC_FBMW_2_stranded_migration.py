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

"""AC.FBMW.2 — the stranded shadow-dir JSONs are recoverable into the
live queue with no episode lost (count preserved; no overwrite).

The pre-fix bug stranded real episodes in the doubled-``workspace`` dead
shadow (sweep PART B / B2: 17 JSONs, newest 15:07 on 2026-05-29). P2
trust: never silently lose what the user said to keep. The migration
helper moves every stranded ``*.json`` into the live queue so the worker
drains it; a filename collision with an existing live entry is surfaced
(NOT overwritten — plan §8 H5), and the stranded copy is left in place
for operator reconciliation.

Parameterised on N (the actual stranded count is re-counted at migration
time, Tier-0; the test proves the invariant N-stranded → N-accounted-for
regardless of the count).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.primary_persona.memory_write_queue import migrate_stranded_queue


def _seed_shadow(shadow: Path, n: int) -> list[str]:
    shadow.mkdir(parents=True, exist_ok=True)
    names = []
    for i in range(n):
        name = f"sess_{i:03d}.json"
        (shadow / name).write_text(f'{{"turn_id": "sess:{i}"}}\n', encoding="utf-8")
        names.append(name)
    # A non-JSON file must be ignored (only *.json are episodes).
    (shadow / "memory-writes.log").write_text("noise\n", encoding="utf-8")
    return names


@pytest.mark.parametrize("n", [0, 1, 17, 50])
def test_AC_FBMW_2_count_preserved_no_loss(tmp_path: Path, n: int) -> None:
    shadow = tmp_path / "pos3" / "workspace" / "workspace" / ".pos" / "memory-write-queue"
    live = tmp_path / "pos3" / "workspace" / ".pos" / "memory-write-queue"
    seeded = _seed_shadow(shadow, n)

    report = migrate_stranded_queue(shadow_queue_dir=shadow, live_queue_dir=live)

    # Count invariant: every stranded JSON is accounted for.
    assert report["stranded_total"] == n
    assert len(report["migrated"]) + len(report["collisions"]) == n
    # No collisions in a clean live queue → all migrated.
    assert len(report["migrated"]) == n
    assert report["collisions"] == []
    # Each migrated entry is now drainable from the live queue with its
    # body intact; the shadow no longer holds it.
    for name in seeded:
        assert (live / name).is_file()
        assert not (shadow / name).exists()
    # The non-JSON noise file is untouched in the shadow (not migrated).
    assert (shadow / "memory-writes.log").is_file()


def test_AC_FBMW_2_collision_not_overwritten(tmp_path: Path) -> None:
    """H5 — a stranded entry whose filename already exists in the live
    queue is NOT overwritten; it is surfaced as a collision and the
    live + stranded copies both survive (no silent data loss)."""
    shadow = tmp_path / "shadow"
    live = tmp_path / "live"
    shadow.mkdir(parents=True)
    live.mkdir(parents=True)

    (shadow / "dup.json").write_text('{"turn_id": "stranded"}\n', encoding="utf-8")
    (shadow / "fresh.json").write_text('{"turn_id": "fresh"}\n', encoding="utf-8")
    (live / "dup.json").write_text('{"turn_id": "LIVE-original"}\n', encoding="utf-8")

    report = migrate_stranded_queue(shadow_queue_dir=shadow, live_queue_dir=live)

    assert report["stranded_total"] == 2
    assert len(report["migrated"]) == 1
    assert len(report["collisions"]) == 1
    # The live original is preserved byte-for-byte (NOT overwritten).
    assert (live / "dup.json").read_text(encoding="utf-8") == '{"turn_id": "LIVE-original"}\n'
    # The stranded colliding copy is left in place for reconciliation.
    assert (shadow / "dup.json").is_file()
    # The non-colliding stranded entry migrated cleanly.
    assert (live / "fresh.json").is_file()
    assert not (shadow / "fresh.json").exists()


def test_AC_FBMW_2_missing_shadow_is_noop(tmp_path: Path) -> None:
    """An absent shadow dir (already-migrated / fresh machine) yields a
    clean zero report rather than raising."""
    report = migrate_stranded_queue(
        shadow_queue_dir=tmp_path / "nope",
        live_queue_dir=tmp_path / "live",
    )
    assert report == {"migrated": [], "collisions": [], "stranded_total": 0}
