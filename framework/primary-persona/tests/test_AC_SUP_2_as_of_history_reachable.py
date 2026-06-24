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

"""AC.SUP.2 — History-reachable = 1.0.

An explicit historical query (``as_of τ``, t1 < τ < t2) returns A for
EVERY triple. Proves filtering ≠ deletion: the stale record is removed
from the default view but stays reachable on demand.

Driven by the FROZEN probe set
``framework/primary-persona/eval/probes/sup_contradiction_triples.json``.
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

from loam.primary_persona.file_memory import FileMemoryStore

_PROBES = (
    Path(__file__).resolve().parent.parent
    / "eval"
    / "probes"
    / "sup_contradiction_triples.json"
)


def _load_triples() -> list[dict]:
    return json.loads(_PROBES.read_text(encoding="utf-8"))["triples"]


def _seed_triple(store: FileMemoryStore, memory_dir: Path, triple: dict) -> None:
    group = "supgroup"
    a = triple["stale"]
    a_prime = triple["current"]
    a_from = datetime.fromisoformat(a["valid_from"])
    a_to = datetime.fromisoformat(a["valid_to"])
    ap_from = datetime.fromisoformat(a_prime["valid_from"])
    store.write_episode(
        name=f"turn/{triple['id']}-current",
        body=a_prime["body"],
        source_description="probe",
        reference_time=ap_from,
        source="message",
        group_id=group,
    )
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
    assert stale_files
    text = stale_files[0].read_text(encoding="utf-8")
    stale_files[0].write_text(
        text.replace(
            f"group_id: {group}\n",
            f"group_id: {group}\n"
            f"superseded-by: ./{triple['id']}-current.md\n"
            f"superseded-date: {a_to.isoformat()}\n",
        ),
        encoding="utf-8",
    )


def test_AC_SUP_2_history_reachable_is_one():
    triples = _load_triples()
    assert triples
    failures: list[str] = []
    for triple in triples:
        with tempfile.TemporaryDirectory() as td:
            memory_dir = Path(td) / "memory"
            store = FileMemoryStore(memory_dir=memory_dir)
            _seed_triple(store, memory_dir, triple)
            as_of = datetime.fromisoformat(triple["as_of"])
            result = store.search(
                query=triple["query"],
                group_ids=["supgroup"],
                num_results=5,
                as_of=as_of,
            )
            paths = [ep["path"] for ep in result["episodes"]]
            if not any(f"{triple['id']}-stale.md" in p for p in paths):
                failures.append(
                    f"{triple['id']}: as_of={triple['as_of']} did NOT "
                    f"return the stale record; paths={paths}"
                )
    assert not failures, (
        "History-reachable < 1.0 — an as_of query failed to return the "
        f"historically-valid record (AC.SUP.2):\n" + "\n".join(failures)
    )
