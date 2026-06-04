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

"""AC.WMS4.LIVE.1 (OUTCOME-ALTITUDE, ``outcome-altitude:true``) — a REAL
store with a REAL dependency chain → the prioritization surfaces the
RIGHT unblocked-next item + a transparent reason, no pre-arranged state.

Plan §6 AC.WMS4.LIVE.1. Through the production entry points against a
REAL work-item store carrying a REAL dependency chain (A independent +
stale, B blocks C, C waits_on B) created via the store's OWN API with NO
pre-arranged surfacing/ranking state: the prioritization surfaces the
RIGHT unblocked-next item (B — the one whose landing unblocks C, ahead of
the independent stale A) AND a TRANSPARENT plain-language reason ("next
because C is waiting on it" — i.e. naming the dependency), through the
live derivation + relational-lens render + the EXISTING ``unblocked_next``
query. No fixtures of pre-computed rankings, no hand-set priority
strings, no pre-arranged reason text.
"""

from __future__ import annotations

from loam.primary_persona.keep_pace.relational import (
    render_relational_block,
    reset_cache,
)

from _wms4_store import EDGE, fresh_factory, live_store, make_open


async def test_AC_WMS4_LIVE_1_real_chain_surfaces_right_next_and_reason(tmp_path) -> None:
    reset_cache()
    db = tmp_path / "objectives.db"

    # Build a REAL store with a REAL dependency chain through the store's
    # OWN API. NO pre-arranged priority strings, rankings, or reason text.
    setup = live_store(db)
    try:
        # A — independent (no edges). It exists; it is genuinely open.
        a = await make_open(setup, "tidy the independent backlog item")
        # B — the unblocker: B blocks C (and C waits on B).
        b = await make_open(setup, "build the shared foundation")
        # C — the blocked downstream item.
        c = await make_open(setup, "ship the feature on the foundation")
        # The REAL dependency chain: C waits_on B, B blocks C.
        await setup.record_edge(
            c.objective_id, edge_kind=EDGE.waits_on, to_id=b.objective_id
        )
        await setup.record_edge(
            b.objective_id, edge_kind=EDGE.blocks, to_id=c.objective_id
        )
    finally:
        setup.close()

    # Through the LIVE production entry point — the relational lens render
    # resolving a fresh tracker, calling the EXISTING unblocked_next query
    # + the live derivation. No pre-arranged state.
    block = render_relational_block(
        tracker_factory=fresh_factory(db), objectives_text=""
    )
    assert block, "the live render must produce a block over the real store"

    # 1. The RIGHT unblocked-next item is B (the unblocker), surfaced as
    #    "next" — ahead of the independent A and not the blocked C.
    next_line = next(
        (ln for ln in block.splitlines() if ln.strip().startswith("next:")),
        "",
    )
    assert "build the shared foundation" in next_line, (
        f"the right unblocked-next item (B, the unblocker) must be surfaced "
        f"as 'next'; next line={next_line!r}\nfull block={block!r}"
    )
    # C is blocked (waiting on B) — it must NOT be the next thing.
    assert "ship the feature on the foundation" not in next_line, (
        "the blocked downstream item must not be surfaced as next"
    )

    # 2. A TRANSPARENT plain-language reason accompanies it — naming the
    #    dependency (C is waiting on B), not a numeric score.
    assert "waiting on it" in next_line.lower(), (
        f"the next item must carry a transparent dependency reason; "
        f"next line={next_line!r}"
    )
    # No black-box score / internal id leaks to the user.
    import re

    assert not re.search(r"\b\d+\.\d+\b", next_line), (
        f"no raw numeric score may surface in the reason; line={next_line!r}"
    )
    assert "obj-" not in next_line, "no internal id may leak in the reason"

    # 3. The blocked downstream item surfaces as blocked-on-what (the
    #    real graph answer), naming B in plain language.
    assert "blocked: ship the feature on the foundation" in block
    assert "waiting on build the shared foundation" in block
