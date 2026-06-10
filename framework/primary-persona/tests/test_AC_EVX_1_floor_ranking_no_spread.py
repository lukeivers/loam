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

"""AC.EVX.1 — the June-7 KILL verdict executed: production memory
search ranks with ZERO contribution from co-citation spread, and the
spread machinery no longer executes in any search path. The ranking
for any query equals the harness's floor configuration (BM25 ×
supersession, neutral activation).

Memory recall cycle, Slice 1 (plan
``docs/plans/memory-decision-ledger-surfacing-dispatch-packs.md``).
"""

from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

from loam.primary_persona.access_log import append_access_event
from loam.primary_persona.file_memory import FileMemoryStore


def test_AC_EVX_1_spread_machinery_is_gone() -> None:
    """The co-citation module is deleted from the package and the
    ranker module carries no spread surface — the measured-harmful
    step cannot execute in any search path."""
    assert (
        importlib.util.find_spec("loam.primary_persona.cocitation_graph")
        is None
    ), "AC.EVX.1: cocitation_graph must be deleted (June-7 KILL verdict)"
    import loam.primary_persona.file_memory as fm

    source = Path(fm.__file__).read_text(encoding="utf-8")
    assert "spread_one_hop" not in source and "_cocitation_graph" not in source, (
        "AC.EVX.1: no spread call path may remain in file_memory"
    )


def test_AC_EVX_1_ranking_equals_floor_configuration(tmp_path: Path) -> None:
    """Search ordering is pure BM25 × supersession: seeding access
    events (which previously drove both activation AND the spread
    graph) changes neither membership nor order of the result set,
    and a lexically-unmatched co-accessed file never surfaces."""
    memory_dir = tmp_path / "mem"
    store = FileMemoryStore(memory_dir=memory_dir)
    now = datetime.now(timezone.utc)

    store.write_episode(
        name="turn/strong",
        body=" ".join(["alpha beta"] * 8) + " strong lexical match",
        source_description="t",
        reference_time=now,
        source="message",
        group_id="ws",
    )
    store.write_episode(
        name="turn/moderate",
        body="alpha beta once amid unrelated scheduling noise",
        source_description="t",
        reference_time=now,
        source="message",
        group_id="ws",
    )
    store.write_episode(
        name="turn/unrelated",
        body="entirely separate vocabulary xenon yttrium zinc",
        source_description="t",
        reference_time=now,
        source="message",
        group_id="ws",
    )

    baseline = store.search(query="alpha beta", group_ids=["ws"], num_results=5)
    baseline_names = [e["name"] for e in baseline["episodes"]]
    assert baseline_names[0] == "turn/strong", (
        f"floor arm: pure BM25 must lead with the strong match; "
        f"got {baseline_names}"
    )

    # Seed heavy co-access for moderate + unrelated — the exact signal
    # that previously re-ordered (activation) and spread-in (graph).
    mod_path = next((memory_dir / "episodes" / "ws").rglob("moderate.md"))
    unrel_path = next((memory_dir / "episodes" / "ws").rglob("unrelated.md"))
    for i in range(20):
        ts = now - timedelta(seconds=i * 30)
        append_access_event(memory_dir, file=str(mod_path), ts=ts, op="read")
        append_access_event(
            memory_dir, file=str(unrel_path), ts=ts + timedelta(seconds=1),
            op="read",
        )

    post = store.search(query="alpha beta", group_ids=["ws"], num_results=5)
    post_names = [e["name"] for e in post["episodes"]]
    assert post_names == baseline_names, (
        f"AC.EVX.1: access events must contribute ZERO to ranking by "
        f"default; baseline={baseline_names} post-seed={post_names}"
    )
    assert "turn/unrelated" not in post_names, (
        "AC.EVX.1: a lexically-unmatched co-accessed file must never "
        "spread into the result set"
    )
    assert not any(e.get("_spread_from") for e in post["episodes"]), (
        "AC.EVX.1: no result row may carry a spread provenance marker"
    )
