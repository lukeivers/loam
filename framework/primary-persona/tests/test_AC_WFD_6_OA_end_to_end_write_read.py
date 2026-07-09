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

"""AC.WFD.6 (OUTCOME-ALTITUDE) — the discipline operates end-to-end through
the real write + recall path, no pre-arranged state.

Through the PRODUCTION fact-write entry-point (``write_episode``) and the
PRODUCTION recall entry-point (``retrieve``) invoked with no pre-arranged
retrieval state: an event/state/finding body is written fact-typed and
recalls UNMARKED; an opinion-shaped body is written non-fact-typed and
recalls MARKED not-a-verified-fact; BOTH are written to disk (neither is
suppressed). The store builds its own index; the shared query token
matches both bodies so an exclusion would be the discipline, never a BM25
miss.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import (
    EPISTEMIC_NON_FACT_ANNOTATION,
    FileMemoryStore,
)
from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve


SHARED = "quizzlefarn"


def _capture(store: FileMemoryStore, *, name: str, body: str, now: datetime) -> Path:
    res = store.write_episode(
        name=f"turn/{name}",
        body=body,
        source_description="session capture",
        reference_time=now,
        source="message",
        group_id="pos3",
    )
    return Path(res["path"])


def test_AC_WFD_6_OA_end_to_end_typed_marked_both_persist(tmp_path: Path) -> None:
    memory_dir = tmp_path / "memory"
    store = FileMemoryStore(memory_dir=memory_dir)
    now = datetime.now(timezone.utc)

    # Lowercase distinctive markers — an ALL-CAPS marker would itself read
    # as a named-constant durable-fact signal and mis-veto the opinion to
    # fact, so the markers stay lower-case (they are only line locators).
    fact_marker = "factmarkerzz"
    opinion_marker = "opinmarkerzz"

    # A verified finding (fact) ...
    fact_path = _capture(
        store,
        name="finding",
        body=(
            f"[user]\nwhat is the {SHARED} ranker cap\n\n[assistant]\n"
            f"the {SHARED} ranked-pool cap is DEFAULT_TOP_N set to 5 "
            f"{fact_marker}\n"
        ),
        now=now,
    )
    # ... and a bare opinion (non-fact) sharing the query token.
    opinion_path = _capture(
        store,
        name="opinion",
        body=(
            f"[user]\nwhat do you make of the {SHARED} ranker\n\n[assistant]\n"
            f"the {SHARED} ranker design is elegant and gorgeous "
            f"{opinion_marker}\n"
        ),
        now=now,
    )

    # BOTH persisted to disk — neither suppressed (liberal ingest).
    assert fact_path.exists()
    assert opinion_path.exists()

    # The production recall entry-point, no pre-arranged state.
    config = RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=tmp_path / "empty-corpus",
        claude_homes=(),
        objectives_home=tmp_path / "no-obj",
        episode_memory_dir=memory_dir,
        episode_group_ids=("pos3",),
    )
    block = retrieve(prompt=f"the {SHARED} ranker", config=config)

    # Both records recalled (neither withheld) — located by their source
    # path filename, which rides each rendered pointer line.
    lines = block.splitlines()
    opinion_lines = [ln for ln in lines if opinion_path.name in ln]
    fact_lines = [ln for ln in lines if fact_path.name in ln]
    assert opinion_lines, f"the opinion must recall (not withheld): {block!r}"
    assert fact_lines, f"the fact must recall: {block!r}"

    # The non-fact annotation rides the OPINION pointer, never the fact one.
    assert EPISTEMIC_NON_FACT_ANNOTATION in opinion_lines[0], (
        f"the opinion pointer must be marked not-a-verified-fact: {opinion_lines[0]!r}"
    )
    assert EPISTEMIC_NON_FACT_ANNOTATION not in fact_lines[0], (
        f"the fact pointer must NOT be marked: {fact_lines[0]!r}"
    )
