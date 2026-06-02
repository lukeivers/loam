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

"""AC-FBM-SAL-6 (SPREAD-PATH JUNK GATED — load-bearing, outcome-altitude) — B3.

The gap the 813-test suite missed and the live-store activation smoke caught:
a junk episode reachable ONLY via co-citation SPREAD (NOT a direct BM25 match)
arrived at the salience gate with no ``_salience`` slot, defaulted to full
salience (the never-drop floor), and BYPASSED the gate — leaking one junk
pointer per query into the rendered recall block.

This test reproduces the exact failure condition: a ``<task-notification>``
junk episode that does NOT lexically match the query but IS pulled in by a
strong co-citation edge from a substantive lexically-matched episode. After
the fix (``_salience`` tagged on the spread-neighbor ``n_row`` exactly as the
FTS/grep candidate pools tag it), the junk neighbor is salience-gated out of
the surfaced set.

Proven end-to-end through the production write -> search -> spread -> merge ->
``retrieve()`` path with no pre-arranged retrieval state (outcome-altitude):
the spread is driven by a real access log, the gate fires inside the real
``retrieve()`` entry-point.

Mirrors AC-FBM-SAL-1 (junk-filtered direct-match) and AC.FBMT2.COCG.2
(one-hop-spread-observable); this is the SAL family x COCG family
intersection that neither parent test exercised.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from loam.primary_persona.access_log import append_access_event
from loam.primary_persona.file_memory import FileMemoryStore
from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve


# A distinctive token carried ONLY by the junk neighbor's body. The query
# never contains it, so the neighbor cannot be a direct BM25 hit — it can only
# arrive via co-citation spread. If it appears in the rendered block, the junk
# leaked through the gate via the spread path (the bug).
JUNK_NEIGHBOR_TOKEN = "quibberflange"

# The lexically-matched substantive episode the query DOES hit. The junk
# neighbor co-occurs with it in the access log, so the spread step pulls the
# junk neighbor in off this anchor.
ANCHOR_BODY = (
    "[user]\n"
    "Walk me through the altitude cold-walk retrieval design and the merge.\n"
    "\n"
    "[assistant]\n"
    "The altitude cold-walk retrieval design merges corpus and episode hits.\n"
)

# A task-notification body (pure scaffolding user half => SALIENCE_JUNK) that
# carries the distinctive neighbor token in its content so we can detect a
# leak in the rendered block.
JUNK_NEIGHBOR_BODY = (
    "[user]\n"
    "<task-notification>\n"
    "<task-id>b58636f21a3d43459</task-id>\n"
    "<tool-use-id>toolu_01JYci2nPBHvvpNeguMS7UTV</tool-use-id>\n"
    "<status>completed</status>\n"
    f"<summary>Agent finished the {JUNK_NEIGHBOR_TOKEN} cleanup task</summary>\n"
    f"<result>Done with the {JUNK_NEIGHBOR_TOKEN} cleanup.</result>\n"
    "</task-notification>\n"
    "\n"
    "[assistant]\n"
    f"Owned and corrected the {JUNK_NEIGHBOR_TOKEN} work.\n"
)


def _seed_store(tmp_path: Path) -> tuple[FileMemoryStore, Path, Path]:
    """Write the anchor + junk-neighbor episodes and seed a strong
    anchor<->junk co-citation edge in the access log. Returns the store
    plus the two on-disk episode paths."""
    memory_dir = tmp_path / "mem"
    store = FileMemoryStore(memory_dir=memory_dir)
    now = datetime.now(timezone.utc)

    store.write_episode(
        name="turn/anchor-lexically-matched",
        body=ANCHOR_BODY,
        source_description="t",
        reference_time=now,
        source="message",
        group_id="pos3",
    )
    # Seed the junk neighbor DIRECTLY into the HOT episodes tier + FTS index,
    # simulating a junk episode already stored in the hot store (e.g. a
    # pre-fbm-write-time-salience-gate-cold-tier episode written before the
    # write gate existed, or any hot-tier junk the owner-gated purge has not yet
    # moved). The write gate (Slice A) would now divert such junk to the cold
    # tier at ingest, so it could never be a hot-tier spread neighbour for a
    # fresh write — but the READ-side spread gate this AC protects must still
    # catch junk already in the hot index. ``store.write_episode`` would route
    # this body to the cold tier, so we bypass it to reproduce the hot-tier
    # condition the read gate defends.
    junk_dir = memory_dir / "episodes" / "pos3" / now.strftime("%Y-%m-%d")
    junk_dir.mkdir(parents=True, exist_ok=True)
    junk_path = junk_dir / "junk-task-notif-neighbor.md"
    junk_front = (
        "---\n"
        "name: turn/junk-task-notif-neighbor\n"
        "source: message\n"
        "source_description: t\n"
        f"reference_time: {now.isoformat()}\n"
        "group_id: pos3\n"
        "salience: 0.0\n"
        "---\n"
    )
    junk_path.write_text(junk_front + JUNK_NEIGHBOR_BODY, encoding="utf-8")
    store._index_episode(
        path=junk_path,
        name="turn/junk-task-notif-neighbor",
        body=JUNK_NEIGHBOR_BODY,
        group_id="pos3",
        reference_time=now,
    )

    anchor_path = next(
        (memory_dir / "episodes" / "pos3").rglob("anchor-lexically-matched.md")
    )

    # Drive a strong anchor<->junk co-citation edge: many co-occurring access
    # events inside the COOCCUR_WINDOW_SECONDS window (default 1800s).
    for i in range(15):
        ts_anchor = now - timedelta(seconds=i * 60)
        ts_junk = now - timedelta(seconds=i * 60 + 5)
        append_access_event(memory_dir, file=str(anchor_path), ts=ts_anchor, op="read")
        append_access_event(memory_dir, file=str(junk_path), ts=ts_junk, op="read")

    return store, anchor_path, junk_path


def test_spread_path_pulls_junk_neighbor_into_raw_search(tmp_path: Path) -> None:
    """Precondition guard: confirm the junk neighbor IS reachable via spread
    in the raw (un-gated) ``store.search`` so the SAL-6 gate test is actually
    exercising the spread path and not a no-op.

    This asserts the spread machinery delivers the junk neighbor into the raw
    episode set (where the gate has not yet fired). The leak-prevention is the
    job of the gated ``retrieve()`` test below.
    """
    store, _anchor, _junk = _seed_store(tmp_path)
    # Query lexically matches ONLY the anchor (never the junk token).
    result = store.search(
        query="altitude cold-walk retrieval design merge",
        group_ids=["pos3"],
        num_results=5,
    )
    names = [e["name"] for e in result["episodes"]]
    assert "turn/junk-task-notif-neighbor" in names, (
        "precondition: the junk neighbor must be reachable via co-citation "
        f"spread in the raw search for SAL-6 to be meaningful; got {names}"
    )
    # And confirm the raw spread row now carries a JUNK salience slot (the fix):
    # on OLD code this slot is ABSENT, which is exactly what let it bypass the
    # gate. We assert it is present and junk so the gate has something to act on.
    junk_row = next(
        e for e in result["episodes"] if e["name"] == "turn/junk-task-notif-neighbor"
    )
    assert junk_row.get("_salience") == pytest.approx(0.0), (
        "the spread-neighbor row must carry _salience=0.0 (junk) so the "
        f"downstream gate can drop it; got {junk_row.get('_salience')!r}"
    )


def test_AC_FBM_SAL_6_spread_junk_neighbor_gated_from_recall(tmp_path: Path) -> None:
    """A junk episode reachable ONLY via co-citation spread does NOT surface
    in the production ``retrieve()`` block (outcome-altitude).

    FAILS on old code: the spread ``n_row`` had no ``_salience`` slot, so the
    gate defaulted it to full salience and the junk neighbor leaked into the
    rendered recall block. PASSES on fixed code: the neighbor is tagged
    SALIENCE_JUNK from its body and gated out before rendering.
    """
    store, _anchor, _junk = _seed_store(tmp_path)

    cfg = RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=None,  # no corpus — isolate the episode spread+gate path
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives",
        episode_memory_dir=store.memory_dir,
        episode_group_ids=("pos3",),
        top_n=5,
    )
    # Query lexically matches ONLY the substantive anchor; the junk neighbor's
    # distinctive token never appears in the query, so it can reach the block
    # ONLY via co-citation spread.
    block = retrieve(
        prompt="altitude cold-walk retrieval design merge", config=cfg
    )

    assert JUNK_NEIGHBOR_TOKEN not in block, (
        "the task-notification junk neighbor reached the recall block ONLY via "
        "co-citation spread and BYPASSED the salience gate (the live-store "
        f"leak); block={block!r}"
    )
    # The task-notification boilerplate must not leak either.
    assert "task-id" not in block and "tool-use-id" not in block, (
        f"task-notification scaffolding leaked via the spread path; block={block!r}"
    )
