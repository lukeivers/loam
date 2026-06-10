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

"""AC.EVX.OA (outcome-altitude: true) — against the LIVE workspace
store with NO pre-arranged state, the production search entry point
returns ranked results whose scores carry no spread/activation
contribution, at single-search latency consistent with the floor arm.

The store is read-only here (search only; the search path's own
access-log bookkeeping is the production behaviour, not test
arrangement). Skips (does not fail) when the live store is absent —
CI / a fresh machine. The full-harness re-run is the slice's measured
prediction, reported at build time; this standing test guards the
structural floor properties on every future run.

Memory recall cycle, Slice 1.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from loam.primary_persona.file_memory import (
    ACTIVATION_FLAG_ENV,
    FileMemoryStore,
    activation_enabled,
)


LIVE_MEMORY_DIR = Path.home() / "pos3" / "workspace" / ".loam" / "memory"

# Generous CI bound for ONE production search against the live store.
# The floor arm measured ~58ms/query on the June-7 harness; the named
# 60ms gate is enforced by the harness re-run (the slice's measured
# prediction), not this standing test — a shared machine under load
# must not flake the seal suite.
SINGLE_SEARCH_LATENCY_CEILING_S = 1.0


@pytest.mark.skipif(
    not (LIVE_MEMORY_DIR / "episodes").is_dir(),
    reason="live workspace store absent (CI / fresh machine)",
)
def test_AC_EVX_OA_live_store_search_is_floor_configuration(
    monkeypatch,
) -> None:
    monkeypatch.delenv(ACTIVATION_FLAG_ENV, raising=False)
    assert activation_enabled() is False, (
        "AC.EVX.OA: production configuration must have activation OFF"
    )

    store = FileMemoryStore(memory_dir=LIVE_MEMORY_DIR)
    t0 = time.monotonic()
    result = store.search(
        query="loam memory retrieval decision",
        group_ids=None,
        num_results=10,
    )
    elapsed = time.monotonic() - t0

    episodes = result.get("episodes", [])
    assert episodes, (
        "AC.EVX.OA: the live store must return ranked results for a "
        "work-anchored query"
    )
    # Zero spread contribution: no row carries spread provenance, and
    # every surfaced row earned its place lexically (a real BM25 score).
    assert not any(e.get("_spread_from") for e in episodes), (
        "AC.EVX.OA: no result may arrive via co-citation spread"
    )
    assert all(
        float(e.get("_bm25_raw", 0.0)) != 0.0 for e in episodes
    ), "AC.EVX.OA: every surfaced row must carry its own BM25 relevance"
    assert elapsed < SINGLE_SEARCH_LATENCY_CEILING_S, (
        f"AC.EVX.OA: single-search latency {elapsed:.3f}s exceeds the "
        f"floor-arm ceiling {SINGLE_SEARCH_LATENCY_CEILING_S}s"
    )
