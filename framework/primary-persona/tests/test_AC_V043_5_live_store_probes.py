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

"""AC.V043.5 (outcome-altitude) — live-store retrieval probes.

Plan ref: ``docs/plans/v0-4-3-patch-memory-retrieval-bm25-fix.md`` §4
AC.V043.5.

Reruns the 6 probe queries from the investigation report against the
live ``~/lukeivers/pos3/workspace/.loam/memory/`` store + 4 additional
probes targeting curated session-summary memories. Verdict band:
GREEN at ≥7/10 relevant top-3 hits.

Skip-by-default in CI via the ``requires_live_store`` mark; runnable
locally with ``-m requires_live_store --no-header`` or via the build
report harness.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from loam.primary_persona.file_memory import FileMemoryStore


# Live store path — bound to Luke's pos3 workspace per plan-doc §8.
_LIVE_STORE_DIR = Path(
    os.environ.get(
        "LOAM_LIVE_MEMORY_DIR",
        "/Users/lukeivers/pos3/workspace/.loam/memory",
    )
)
_LIVE_GROUP_ID = "pos3"


# Probe set (10 probes). Each entry: (query, [relevance keywords]).
# A top-3 hit "counts" if any of the relevance keywords appears in the
# top-3 episode bodies OR the episode path. Keywords are
# case-insensitive substring matches; per plan-doc §4 the relevance
# judgment is the builder's call — keywords here are the judgment
# rubric so the harness is reproducible.
_PROBES: tuple[tuple[str, tuple[str, ...]], ...] = (
    # Investigation-report probes 1-6.
    ("What was v0.4.2?", ("v0.4.2", "v0-4-2", "f-design-2")),
    ("How does the BallotPath schema work?", ("ballotpath", "schema")),
    ("What did Eric report broken?", ("eric", "rd-automation")),
    ("Stage 7.7 verification corrections", ("stage 7.7", "stage-7-7", "7.7")),
    ("F-DESIGN-1 closure", ("f-design-1", "closure")),
    (
        "How does loam handle subscription-only?",
        ("subscription", "claude max", "anthropic", "no api key"),
    ),
    # Curated session-summary probes 7-10.
    (
        "What is the current BallotPath project status?",
        ("ballotpath", "stage", "ship"),
    ),
    ("What did v0.4.0 ship?", ("v0.4.0", "v0-4-0", "ship", "code-gen")),
    (
        "What memory-rules were captured this session?",
        ("memory", "feedback", "rule", "captured"),
    ),
    (
        "What v0.4.1 and v0.4.2 closures landed?",
        ("v0.4.1", "v0.4.2", "v0-4-1", "v0-4-2", "closure"),
    ),
)


def _probe_one(
    store: FileMemoryStore, query: str, keywords: tuple[str, ...]
) -> tuple[bool, list[dict]]:
    """Run one probe; return (relevant?, top-3-results)."""
    result = store.search(
        query=query, group_ids=[_LIVE_GROUP_ID], num_results=3
    )
    eps = result["episodes"][:3]
    relevant = False
    for ep in eps:
        haystack = (ep.get("content", "") + " " + ep.get("path", "")).lower()
        if any(kw.lower() in haystack for kw in keywords):
            relevant = True
            break
    return relevant, eps


@pytest.mark.requires_live_store
def test_AC_V043_5_live_store_probes_meet_green_band() -> None:
    """≥7 of 10 probes return a relevant top-3 episode."""
    if not _LIVE_STORE_DIR.exists():
        pytest.skip(
            f"live memory dir not present at {_LIVE_STORE_DIR}; "
            f"set LOAM_LIVE_MEMORY_DIR or skip"
        )

    store = FileMemoryStore(memory_dir=_LIVE_STORE_DIR)

    hits = 0
    per_probe: list[tuple[str, bool, list[str]]] = []
    for query, keywords in _PROBES:
        relevant, eps = _probe_one(store, query, keywords)
        per_probe.append(
            (query, relevant, [ep.get("path", "") for ep in eps])
        )
        if relevant:
            hits += 1

    summary = "\n".join(
        f"  [{'OK' if rel else '--'}] {q!r}\n    "
        + "\n    ".join(paths)
        for q, rel, paths in per_probe
    )
    assert hits >= 7, (
        f"AC.V043.5 verdict-band GREEN miss: {hits}/10 probes returned "
        f"a relevant top-3 episode (need ≥7). Per-probe verdicts:\n"
        f"{summary}"
    )
