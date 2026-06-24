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

"""AC.SUP.1 — Currentness@1 = 1.0 (zero tolerance).

On a contradiction triple (A, A', Q) the DEFAULT current view ranks A'
above A OR filters A out entirely — for EVERY triple in the frozen
probe set. Any single A-over-A' is a HARD fail (plan §4 / §8 trigger 2).

Driven by the FROZEN probe set
``framework/primary-persona/eval/probes/sup_contradiction_triples.json``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import FileMemoryStore

_PROBES = (
    Path(__file__).resolve().parent.parent
    / "eval"
    / "probes"
    / "sup_contradiction_triples.json"
)


def _load_triples() -> list[dict]:
    data = json.loads(_PROBES.read_text(encoding="utf-8"))
    return data["triples"]


def _seed_triple(store: FileMemoryStore, memory_dir: Path, triple: dict) -> None:
    """Seed A (stale) then A' (current) into the store with their
    validity intervals expressed as the supersession marker. A's
    interval is closed at A''s valid_from (the write-path interval-close,
    AC.SUP.3 — mirrored here via the marker the production marking entry
    point writes)."""
    group = "supgroup"
    a = triple["stale"]
    a_prime = triple["current"]
    a_from = datetime.fromisoformat(a["valid_from"])
    a_to = datetime.fromisoformat(a["valid_to"])
    ap_from = datetime.fromisoformat(a_prime["valid_from"])

    # Write A' (current) — open interval.
    store.write_episode(
        name=f"turn/{triple['id']}-current",
        body=a_prime["body"],
        source_description="probe",
        reference_time=ap_from,
        source="message",
        group_id=group,
    )
    # Write A (stale) — then close its interval with the marker.
    store.write_episode(
        name=f"turn/{triple['id']}-stale",
        body=a["body"],
        source_description="probe",
        reference_time=a_from,
        source="message",
        group_id=group,
    )
    stale_files = list(
        (memory_dir / "episodes" / group).rglob(f"{triple['id']}-stale.md")
    )
    assert stale_files, f"stale file not written for {triple['id']}"
    text = stale_files[0].read_text(encoding="utf-8")
    annotated = text.replace(
        f"group_id: {group}\n",
        f"group_id: {group}\n"
        f"superseded-by: ./{triple['id']}-current.md\n"
        f"superseded-date: {a_to.isoformat()}\n",
    )
    stale_files[0].write_text(annotated, encoding="utf-8")


def test_AC_SUP_1_currentness_at_1_is_one_zero_tolerance():
    import tempfile

    triples = _load_triples()
    assert triples, "probe set is empty"
    failures: list[str] = []
    for triple in triples:
        with tempfile.TemporaryDirectory() as td:
            memory_dir = Path(td) / "memory"
            store = FileMemoryStore(memory_dir=memory_dir)
            _seed_triple(store, memory_dir, triple)
            result = store.search(
                query=triple["query"],
                group_ids=["supgroup"],
                num_results=5,
            )
            paths = [ep["path"] for ep in result["episodes"]]
            stale_in = any(f"{triple['id']}-stale.md" in p for p in paths)
            current_idx = next(
                (
                    i
                    for i, p in enumerate(paths)
                    if f"{triple['id']}-current.md" in p
                ),
                None,
            )
            stale_idx = next(
                (
                    i
                    for i, p in enumerate(paths)
                    if f"{triple['id']}-stale.md" in p
                ),
                None,
            )
            # PASS condition: stale filtered out entirely, OR current
            # ranks above stale. FAIL: stale present and ranked at/above
            # current.
            ok = (not stale_in) or (
                current_idx is not None
                and stale_idx is not None
                and current_idx < stale_idx
            )
            if not ok:
                failures.append(
                    f"{triple['id']} ({triple['fact_type']}): "
                    f"current_idx={current_idx} stale_idx={stale_idx} "
                    f"paths={paths}"
                )
    assert not failures, (
        "Currentness@1 < 1.0 — the supersession filter is not filtering "
        f"(ZERO TOLERANCE, plan §8 trigger 2):\n" + "\n".join(failures)
    )
