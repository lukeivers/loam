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

"""AC.FBMT2.S — outcome-altitude smoke for FBM retrieval mechanics.

Marked ``outcome-altitude: true`` per
``feedback_test_outcome_altitude_required``. Invokes the production
:func:`build_file_memory_retrieval_contributor` with no pre-arranged
state beyond a synthetic memory corpus + a synthetic access-log seed.

Memory recall cycle Slice 1 (AC.EVX.1 / AC.EVX.2) — updated to the
June-7 eval verdict's FLOOR configuration:

  - the one-hop co-citation spread is DELETED (measured net-harmful:
    worse on every metric, 2x latency, 0-of-88 rescues on its own
    target subset). A lexically-mismatched file must NOT surface —
    the old T2.2 spread observable is now asserted ABSENT.
  - power-law activation is DEFAULT-OFF behind the named
    ``LOAM_FBM_ACTIVATION`` switch; the default-path smoke asserts
    pure BM25 x supersession ordering, and the flag-on path is
    covered by AC.FBMT2.PLBLA.2.

The test still patches NO internal helpers — the production
contributor is invoked exactly as the persona's composer invokes it
on every UserPromptSubmit (V025-C1 risk-band HIGH lesson).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from loam.primary_persona.access_log import append_access_event
from loam.primary_persona.file_memory import (
    FileMemoryRetrievalConfig,
    FileMemoryStore,
    build_file_memory_retrieval_contributor,
)


def test_AC_FBMT2_S_end_to_end_via_production_contributor(
    tmp_path: Path,
) -> None:
    """Floor-configuration smoke through the production contributor
    factory (AC.EVX.1): BM25 ranks; seeded access events change
    NOTHING by default; the lexically-mismatched file does NOT
    surface (spread deleted)."""
    memory_dir = tmp_path / "mem"
    store = FileMemoryStore(memory_dir=memory_dir)
    now = datetime.now(timezone.utc)

    # (a) Seed memory corpus of 3 files with controlled lexical overlap.
    # File A: matches the query terms.
    store.write_episode(
        name="turn/a",
        body="alpha beta gamma query terms about the topic",
        source_description="t",
        reference_time=now,
        source="message",
        group_id="ws",
    )
    # File B: weaker lexical match than A.
    store.write_episode(
        name="turn/b",
        body="alpha beta noise here different scheduling matter",
        source_description="t",
        reference_time=now,
        source="message",
        group_id="ws",
    )
    # File C: lexically MISMATCHED with the query. Pre-verdict it
    # surfaced via the one-hop co-citation spread; post-deletion it
    # must NOT appear for this query (AC.EVX.1).
    store.write_episode(
        name="turn/c",
        body="entirely separate vocabulary xenon yttrium zinc",
        source_description="t",
        reference_time=now,
        source="message",
        group_id="ws",
    )

    a_path = next((memory_dir / "episodes" / "ws").rglob("a.md"))
    c_path = next((memory_dir / "episodes" / "ws").rglob("c.md"))

    # (b) Access-log seed that would (pre-verdict) have boosted A and
    # co-cited C alongside it. With activation default-off and spread
    # deleted, these events must contribute NOTHING to the ranking.
    for i in range(12):
        ts = now - timedelta(seconds=i * 60)
        append_access_event(memory_dir, file=str(a_path), ts=ts, op="read")
        append_access_event(
            memory_dir, file=str(c_path), ts=ts + timedelta(seconds=2), op="read"
        )

    # (d) Build the PRODUCTION contributor via the factory — no patching
    # of internal helpers.
    config = FileMemoryRetrievalConfig(
        store=store,
        workspace_slug="ws",
        num_results=5,
    )
    contributor = build_file_memory_retrieval_contributor(config)

    rendered = contributor({"prompt": "alpha beta gamma query terms topic"})
    assert "turn/a" in rendered, (
        f"AC.EVX.1: A must surface as the top BM25 result; "
        f"rendering={rendered!r}"
    )
    assert "turn/c" not in rendered, (
        f"AC.EVX.1: C is lexically mismatched and the co-citation "
        f"spread is deleted — it must NOT surface; rendering={rendered!r}"
    )


def test_AC_FBMT2_S_smoke_returns_non_empty_block_with_seeded_corpus(
    tmp_path: Path,
) -> None:
    """A sanity-floor companion: a single memory episode + one query
    returns a non-empty rendering through the production contributor.
    Guards against the contributor short-circuiting on empty-prompt or
    fail-closed surrounding contracts when state IS seeded."""
    memory_dir = tmp_path / "mem"
    store = FileMemoryStore(memory_dir=memory_dir)
    now = datetime.now(timezone.utc)
    store.write_episode(
        name="turn/lonely",
        body="solitary content with the keyword sphinx",
        source_description="t",
        reference_time=now,
        source="message",
        group_id="ws",
    )
    config = FileMemoryRetrievalConfig(
        store=store, workspace_slug="ws", num_results=5
    )
    contributor = build_file_memory_retrieval_contributor(config)
    rendered = contributor({"prompt": "sphinx"})
    assert rendered, "production contributor must return non-empty block"
    assert "turn/lonely" in rendered
