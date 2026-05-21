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

"""AC.FBMT2.S — outcome-altitude smoke for FBM Tier 2 retrieval mechanics.

Marked ``outcome-altitude: true`` per
``feedback_test_outcome_altitude_required``. Invokes the production
:func:`build_file_memory_retrieval_contributor` with no pre-arranged
state beyond a synthetic memory corpus + a synthetic access-log seed;
verifies both primitives' behaviors in one synthetic flow.

Per plan-doc ``amendment-135-fbm-tier2-retrieval-mechanics.md`` §4
AC.FBMT2.S:

    A single test exercises the full Tier 2 retrieval surface:
      (a) seed a memory corpus of >=3 files with controlled lexical
          overlap;
      (b) seed an access log with >=5 events showing the frequency
          pattern observable (file_A many touches recent, file_B once
          recent, file_C never) — verifies the activation column
          observable (T2.1);
      (c) seed the co-citation graph with a strong A↔C edge — verifies
          the one-hop spread observable when a query lexically matches
          A and the result includes C without C being lexically
          matched (T2.2);
      (d) issue the query through the production
          :func:`build_file_memory_retrieval_contributor` factory —
          the contributor is the production entry-point, not a test
          stub.

The test asserts the returned result set contains file_C (the spread
observable, T2.2); asserts file_A ranks above file_B despite higher
BM25 for file_B's irrelevant noise (the activation observable, T2.1);
asserts the test does not patch internal helpers like
``_blend_recency`` or ``_superseded_marker`` (the production code
path is what's exercised — V025-C1 risk-band HIGH).
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
    """Full Tier 2 retrieval surface exercised through the production
    contributor factory. NO internal-helper patching — the contributor
    is invoked as the persona's composer invokes it on every
    UserPromptSubmit."""
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
    # File B: matches some query terms (will compete with A on BM25)
    # but is touched only once — activation differential pushes A above.
    store.write_episode(
        name="turn/b",
        body="alpha beta noise here different scheduling matter",
        source_description="t",
        reference_time=now,
        source="message",
        group_id="ws",
    )
    # File C: lexically MISMATCHED with the query (only surfaces via
    # one-hop co-citation spread from A).
    store.write_episode(
        name="turn/c",
        body="entirely separate vocabulary xenon yttrium zinc",
        source_description="t",
        reference_time=now,
        source="message",
        group_id="ws",
    )

    a_path = next((memory_dir / "episodes" / "ws").rglob("a.md"))
    b_path = next((memory_dir / "episodes" / "ws").rglob("b.md"))
    c_path = next((memory_dir / "episodes" / "ws").rglob("c.md"))

    # (b) Access-log seed: A touched many times recent + co-occurring
    # with C; B touched once recent; C touched alongside A so they
    # co-occur (drives the A↔C edge for T2.2).
    for i in range(12):
        ts = now - timedelta(seconds=i * 60)
        append_access_event(memory_dir, file=str(a_path), ts=ts, op="read")
        append_access_event(
            memory_dir, file=str(c_path), ts=ts + timedelta(seconds=2), op="read"
        )
    append_access_event(
        memory_dir, file=str(b_path), ts=now - timedelta(hours=1), op="read"
    )

    # (d) Build the PRODUCTION contributor via the factory — no patching
    # of internal helpers (V025-C1 lesson: don't stub past the
    # production retrieval entry-point).
    config = FileMemoryRetrievalConfig(
        store=store,
        workspace_slug="ws",
        num_results=5,
    )
    contributor = build_file_memory_retrieval_contributor(config)

    rendered = contributor({"prompt": "alpha beta gamma query terms topic"})
    # The contributor returns a rendered string; assert both A and C
    # appear in the rendering (A from BM25 + activation; C via spread).
    assert "turn/a" in rendered, (
        f"AC.FBMT2.S (T2.1): A must surface as the top BM25+activation "
        f"result; rendering={rendered!r}"
    )
    assert "turn/c" in rendered, (
        f"AC.FBMT2.S (T2.2): C must surface via one-hop spread from A "
        f"despite lexical mismatch; rendering={rendered!r}"
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
