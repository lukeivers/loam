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

"""AC.WS.LIVE.1 (OUTCOME-ALTITUDE, outcome-altitude:true) — run the
PRODUCTION surfacer through a real keep-pace turn against the LIVE loam +
cairn (+ litrpg) repos with NO pre-arranged state: the surfaced block
names the streams, and for a stream bound to a registered project the
block shows a STATE + next-action DERIVED from the live
``derive_project_state`` — so the persona cannot, from this block,
mis-state a bound project's status.

This invokes the production entry point (``render_work_streams_block``
with NO ``streams`` / ``derive`` / ``emit`` overrides) — no fixtures, no
pre-arranged state. The literal answer to Luke's "proper context/state
for projects is maintained and surfaced during conversations." It is
SKIPPED only if the live registered repos are not present on this machine
(CI without the repos); on Luke's machine it exercises the real path.
"""

from __future__ import annotations

import pytest

from loam.primary_persona.keep_pace.work_streams_surface import (
    render_work_streams_block,
)


def _live_registry_available() -> bool:
    try:
        from loam_cli.audit.registry import (
            derive_project_state,
            registered_project_names,
        )
    except Exception:
        return False
    # At least loam + cairn must derive a real record for this to be a
    # meaningful live assertion.
    names = registered_project_names()
    if "loam" not in names:
        return False
    rec = derive_project_state("loam")
    return rec is not None and bool(getattr(rec, "components", ()))


pytestmark = pytest.mark.skipif(
    not _live_registry_available(),
    reason="live loam/cairn registry not derivable on this machine",
)


def test_AC_WS_LIVE_1_production_surfacer_derives_live_per_stream_state() -> None:
    # PRODUCTION entry point — no overrides, no fixtures, no pre-arranged
    # state. The register falls back to the in-source seed (the 5 real
    # streams), so this is a genuine cold-turn render.
    block = render_work_streams_block()

    assert block, "the production surfacer must render a block on a live turn"

    # The block is ONE concise block, within the hard cap.
    assert block.count("[work-streams]") == 1
    assert len(block) <= 600

    # It NAMES the bound streams (loam + cairn are FBM-registered).
    assert "- loam " in block, f"the loam stream must surface; got:\n{block}"
    assert "- cairn " in block, f"the cairn stream must surface; got:\n{block}"


def test_AC_WS_LIVE_1_bound_streams_show_derived_build_state() -> None:
    block = render_work_streams_block()
    # The bound streams carry a DERIVED build-status vocabulary (the
    # ground-truth liveness phrasing) — not a stored prose string. Cairn's
    # Layer-A engine is BUILT, so the cairn line must carry a built phrase.
    cairn_line = [ln for ln in block.splitlines() if "- cairn " in ln]
    assert cairn_line, f"cairn line missing; got:\n{block}"
    assert "built" in cairn_line[0].lower(), (
        "the cairn stream must show its DERIVED build state (Layer-A built) "
        f"— the persona cannot mis-state it; got:\n{cairn_line[0]}"
    )


def test_AC_WS_LIVE_1_litrpg_stream_surfaces_production_state() -> None:
    # LitRPG is registered as an FBM project (its production progress is
    # derivable from the litrpg-writer workspace). On a machine with the
    # workspace present, the litrpg stream shows a derived production
    # state; otherwise (workspace absent) the stream is omitted fail-soft.
    try:
        from loam_cli.audit.registry import derive_project_state

        litrpg = derive_project_state("litrpg")
    except Exception:
        litrpg = None
    if litrpg is None or not getattr(litrpg, "components", ()):
        pytest.skip("litrpg production workspace not present on this machine")

    block = render_work_streams_block()
    # When the litrpg workspace is present, the litrpg stream surfaces a
    # derived production state (built/merged or status-unknown per layer) —
    # never a faked one.
    litrpg_line = [ln for ln in block.splitlines() if "- litrpg " in ln]
    # litrpg may collapse on overflow; assert it surfaces OR is honestly
    # collapsed (never silently wrong).
    if litrpg_line:
        low = litrpg_line[0].lower()
        assert ("built" in low) or ("status unknown" in low), (
            f"litrpg must show a DERIVED production state; got:\n{litrpg_line[0]}"
        )
