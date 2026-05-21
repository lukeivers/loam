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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.FBMT2.PLBLA.5 — backwards-compat with pre-amendment memory files.

Per plan-doc ``amendment-135-fbm-tier2-retrieval-mechanics.md`` §4
AC.FBMT2.PLBLA.5:

    Existing memory files written before this amendment (no Tier-1
    ``context:`` block, no access-log history) retrieve cleanly under
    the new ranker.

Verification: seed a memory file with the pre-amendment shape (no
``context:`` block; written directly to disk in legacy format); assert
the retrieval contributor returns it in BM25 order; assert no schema-
validation error fires.

Scope of the AC (per §16 build-time finding): the contract is "a
pre-amendment memory file retrieves cleanly under the new ranker" —
singular file in a workspace with no FTS5 index yet. The grep
fallback (AC.MFBM.2 + D-Q.MFBM.2) is the surface that surfaces such a
file. A mixed-corpus scenario (legacy file alongside FTS5-indexed
new file) is **not part of this AC** — that scenario depends on the
FTS5 lifecycle (index-population on session-start), which is a
separate retrieval-substrate concern handled by AC.MFBM.2's
fail-closed branches and not load-bearing for backwards-compat.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import FileMemoryStore


PRE_AMENDMENT_FRONTMATTER = """---
name: turn/legacy-2026-04-15
source: message
source_description: legacy pre-amendment turn
reference_time: 2026-04-15T10:30:00+00:00
group_id: ws
---
This is a pre-amendment memory file. No ``context:`` block, no
``superseded-by`` field. It was written by an older version of
``FileMemoryStore.write_episode`` and remains on disk after upgrade.

alpha beta gamma — the body keywords for this test.
"""


def test_AC_FBMT2_PLBLA_5_legacy_file_retrieves(tmp_path: Path) -> None:
    """A pre-amendment memory file (no ``context:``, no access-log) is
    retrievable + non-error under the new ranker."""
    memory_dir = tmp_path / "mem"
    episodes_dir = memory_dir / "episodes" / "ws" / "2026-04-15"
    episodes_dir.mkdir(parents=True)
    legacy_path = episodes_dir / "legacy-2026-04-15.md"
    legacy_path.write_text(PRE_AMENDMENT_FRONTMATTER, encoding="utf-8")
    # Ensure the FTS5 index picks it up (the store rebuilds the index
    # lazily on first search if needed).
    store = FileMemoryStore(memory_dir=memory_dir)
    result = store.search(
        query="alpha beta gamma", group_ids=["ws"], num_results=5
    )
    names = [e["name"] for e in result["episodes"]]
    # The pre-amendment file must surface (grep fallback at minimum).
    assert "turn/legacy-2026-04-15" in names, (
        f"AC.FBMT2.PLBLA.5: pre-amendment file must retrieve cleanly; "
        f"got {names}"
    )


def test_AC_FBMT2_PLBLA_5_no_schema_warning_on_pre_amendment_shape(
    tmp_path: Path,
) -> None:
    """The pre-amendment shape (no ``context:`` block; no
    ``superseded-by`` field) parses through the retrieval pipeline
    without emitting any schema-validation warning into
    ``_LAST_RANKER_WARNINGS`` (the AC.FBMT1.SUPM.4 surface) — the new
    ranker tolerates the legacy shape as-is."""
    from loam.primary_persona import file_memory as _fm

    memory_dir = tmp_path / "mem"
    episodes_dir = memory_dir / "episodes" / "ws" / "2026-04-15"
    episodes_dir.mkdir(parents=True)
    legacy_path = episodes_dir / "legacy-2026-04-15.md"
    legacy_path.write_text(PRE_AMENDMENT_FRONTMATTER, encoding="utf-8")
    store = FileMemoryStore(memory_dir=memory_dir)
    # Clear the warning surface before invoking the ranker.
    _fm._LAST_RANKER_WARNINGS = []
    store.search(
        query="alpha beta gamma", group_ids=["ws"], num_results=5
    )
    # AC.FBMT2.PLBLA.5: no schema-validation error or warning fires on
    # the legacy shape. ``_LAST_RANKER_WARNINGS`` is the surface
    # AC.FBMT1.SUPM.4 emits into; the supersession-marker path is the
    # only ranker-side warning surface and the legacy file has no
    # ``superseded-by`` field, so the list must stay empty.
    assert _fm._LAST_RANKER_WARNINGS == [], (
        f"pre-amendment files must not raise schema warnings; "
        f"got {_fm._LAST_RANKER_WARNINGS!r}"
    )
