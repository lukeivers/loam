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

"""AC.FBMT2.PLBLA.2 — multiplicative BM25 × activation composition.

Per plan-doc ``amendment-135-fbm-tier2-retrieval-mechanics.md`` §4
AC.FBMT2.PLBLA.2:

    The retrieval ranker's final score composes BM25 with activation
    **multiplicatively** in a way that observably re-orders results.
    Concretely: a file with high BM25 + low activation ranks **below**
    a file with moderate BM25 + high activation when the activation
    differential exceeds the BM25 differential.

Verification (per plan-doc): construct two memory files with
controlled BM25 scores; seed the access log so file_A has many recent
accesses and file_B has none; assert file_A ranks above file_B even
when file_B's pre-activation BM25 score is higher.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path

from loam.primary_persona.access_log import append_access_event
from loam.primary_persona.file_memory import FileMemoryStore


def test_AC_FBMT2_PLBLA_2_activation_overrides_bm25_when_differential_dominates(
    tmp_path: Path,
) -> None:
    """File A with moderate BM25 + high activation ranks above file B
    with higher BM25 + zero activation."""
    memory_dir = tmp_path / "mem"
    store = FileMemoryStore(memory_dir=memory_dir)
    now = datetime.now(timezone.utc)

    # File A — moderate lexical match (the query terms appear once).
    store.write_episode(
        name="turn/a-moderate-bm25",
        body="alpha beta and unrelated noise about scheduling",
        source_description="t",
        reference_time=now,
        source="message",
        group_id="ws",
    )
    # File B — STRONG lexical match (query terms repeated many times).
    store.write_episode(
        name="turn/b-strong-bm25",
        body=" ".join(["alpha beta"] * 12) + " extra unrelated content",
        source_description="t",
        reference_time=now,
        source="message",
        group_id="ws",
    )

    # Verify BM25-alone ordering: B wins under pure BM25.
    pre = store.search(query="alpha beta", group_ids=["ws"], num_results=2)
    pre_names = [e["name"] for e in pre["episodes"]]
    assert pre_names[0] == "turn/b-strong-bm25", (
        f"baseline assumption — B should win on pure BM25 before seeding "
        f"activation; got {pre_names}"
    )

    # Now seed many recent access events for file A.
    a_path = next((memory_dir / "episodes" / "ws").rglob("a-moderate-bm25.md"))
    for i in range(20):
        append_access_event(
            memory_dir,
            file=str(a_path),
            ts=now - timedelta(seconds=i * 30),
            op="read",
        )

    # AC.FBMT2.PLBLA.2 — A wins because activation differential dominates.
    post = store.search(query="alpha beta", group_ids=["ws"], num_results=2)
    post_names = [e["name"] for e in post["episodes"]]
    assert post_names[0] == "turn/a-moderate-bm25", (
        f"AC.FBMT2.PLBLA.2 — activation must re-order when its "
        f"differential exceeds the BM25 differential; got {post_names}"
    )


def test_AC_FBMT2_PLBLA_2_activation_neutral_when_log_empty(
    tmp_path: Path,
) -> None:
    """With NO access events for either file, the activation column is
    a neutral multiplier; the pure BM25 ordering survives. Composes
    with AC.FBMT2.PLBLA.4's graceful-on-absent-log surface."""
    memory_dir = tmp_path / "mem"
    store = FileMemoryStore(memory_dir=memory_dir)
    now = datetime.now(timezone.utc)
    store.write_episode(
        name="turn/x", body="alpha beta noise", source_description="t",
        reference_time=now, source="message", group_id="ws",
    )
    store.write_episode(
        name="turn/y",
        body=" ".join(["alpha beta"] * 12),
        source_description="t",
        reference_time=now, source="message", group_id="ws",
    )
    r = store.search(query="alpha beta", group_ids=["ws"], num_results=2)
    names = [e["name"] for e in r["episodes"]]
    # AC.FBMT2.PLBLA.2: with neutral activation, BM25 alone decides;
    # the multiply-by-1 path preserves pure-BM25 ordering.
    assert names[0] == "turn/y", names
