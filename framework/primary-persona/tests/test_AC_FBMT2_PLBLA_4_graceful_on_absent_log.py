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

"""AC.FBMT2.PLBLA.4 — graceful on absent access log.

Per plan-doc ``amendment-135-fbm-tier2-retrieval-mechanics.md`` §4
AC.FBMT2.PLBLA.4:

    A workspace with no access log file present (fresh workspace; cold
    start) returns the **pure-BM25 ranking** without raising. The
    activation column degrades to neutral when no signal exists.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.access_log import access_log_path, read_access_log
from loam.primary_persona.file_memory import FileMemoryStore


def test_AC_FBMT2_PLBLA_4_no_log_returns_bm25_order(tmp_path: Path) -> None:
    """No access log file → retrieval returns pure-BM25 ranking + no raise."""
    memory_dir = tmp_path / "mem"
    store = FileMemoryStore(memory_dir=memory_dir)
    now = datetime.now(timezone.utc)
    # Strong-BM25 episode.
    store.write_episode(
        name="turn/strong",
        body=" ".join(["alpha"] * 20) + " beta",
        source_description="t",
        reference_time=now,
        source="message",
        group_id="ws",
    )
    # Weak-BM25 episode.
    store.write_episode(
        name="turn/weak",
        body="alpha and lots of other content about scheduling",
        source_description="t",
        reference_time=now,
        source="message",
        group_id="ws",
    )
    # AC.FBMT2.PLBLA.4: ensure no log file exists yet (the writes above
    # went through ``write_episode`` directly, not through
    # ``FileBackedMemoryClient.add_episode``, so no write events emitted).
    log_path = access_log_path(memory_dir)
    assert not log_path.exists()

    # Search must not raise and must return BM25 order.
    result = store.search(query="alpha", group_ids=["ws"], num_results=2)
    names = [e["name"] for e in result["episodes"]]
    # Strong-BM25 wins under pure-BM25.
    assert names[0] == "turn/strong", names


def test_AC_FBMT2_PLBLA_4_empty_log_dict(tmp_path: Path) -> None:
    """``read_access_log`` on an absent log returns an empty dict (the
    surface contract downstream callers rely on)."""
    md = tmp_path / "fresh"
    assert read_access_log(md) == {}
    # Even on a partially-initialized memory dir (parent created, no
    # log file) the same contract holds.
    md.mkdir(parents=True)
    assert read_access_log(md) == {}


def test_AC_FBMT2_PLBLA_4_search_on_empty_store_does_not_raise(
    tmp_path: Path,
) -> None:
    """A fresh memory dir with NO episodes returns an empty result
    set without raising. Composes with AC.MFBM.2 fail-closed surface."""
    memory_dir = tmp_path / "mem"
    store = FileMemoryStore(memory_dir=memory_dir)
    result = store.search(query="anything", group_ids=["ws"], num_results=5)
    assert result["episodes"] == []
