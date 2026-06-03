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

"""AC.WVS-MR.3 ★ (outcome-altitude:true, Slice E) — the PRODUCTION
work-visibility snapshot, built with NO pre-arranged state against the
LIVE registry (loam + /Users/lukeivers/cairn), reflects BOTH repos' real
ground-truth build state — Cairn's engine modules counted as BUILT — and
the rendered surface carries zero internal vocabulary.

A STUB-class test (hand-fed summaries, mocked derivation, a pre-built
snapshot) does NOT satisfy this. This test drives the real
``derive_project_state`` against the live Cairn repo via the production
``render_work_visibility`` / ``build_snapshot`` entry points with no
injected project_state_reader — reproducing from ground truth the fact
the persona got WRONG (claiming Cairn's verify/ledger/execute "remain to
be built" when those modules exist on disk + landed via merged PRs).

Skips cleanly if the live Cairn repo is absent (CI without the repo) —
the outcome-altitude guarantee is about the LIVE path, not a fixture.

Plan: docs/plans/fbm-multi-repo-work-visibility.md §5.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.primary_persona.work_visibility import (
    build_snapshot,
    render_work_visibility,
)
from loam.self_correction.recovery_surface import contains_internal_vocabulary

_CAIRN_ROOT = Path("/Users/lukeivers/cairn")


def _live_cairn_available() -> bool:
    return (_CAIRN_ROOT / ".git").exists()


@pytest.mark.skipif(
    not _live_cairn_available(),
    reason="live Cairn repo absent — outcome-altitude needs the real repo",
)
def test_AC_WVS_MR_3_live_snapshot_includes_cairn_built(tmp_path: Path) -> None:
    """Outcome-altitude: the production snapshot against the live registry
    carries BOTH loam and cairn buckets, Cairn's engine counted built,
    with NO pre-arranged state."""
    # No project_state_reader → the production registry read runs against
    # the LIVE PROJECT_REGISTRY (loam + cairn), deriving each fresh from
    # ground truth. No tracker DB on this fresh tmp workspace (work-state
    # marks unknown) — that is irrelevant to the multi-repo assertion.
    snapshot = build_snapshot(tmp_path)

    by_name = {p.name: p for p in snapshot.project_states}
    assert "loam" in by_name, "live loam bucket missing from snapshot"
    assert "cairn" in by_name, "live cairn bucket missing from snapshot"

    cairn = by_name["cairn"]
    # Cairn's engine modules (verify/ledger/execute/pilot/cause) are on
    # disk + landed via merged PRs → classified BUILT. The persona's WRONG
    # claim ("remain to be built") is contradicted: built > 0 and every
    # classified Cairn module is built.
    assert cairn.total > 0, "cairn derived zero modules — derivation broke"
    assert cairn.built == cairn.total, (
        f"cairn shows un-built modules ({cairn.built}/{cairn.total}); the "
        "live engine modules should all classify built"
    )
    assert cairn.unknown is False


@pytest.mark.skipif(
    not _live_cairn_available(),
    reason="live Cairn repo absent — outcome-altitude needs the real repo",
)
def test_AC_WVS_MR_3_live_surface_names_both_zero_vocab(tmp_path: Path) -> None:
    """Outcome-altitude: the production rendered surface names both repos'
    build state in plain language with ZERO internal vocabulary, end-to-end
    from the live registry."""
    surface = render_work_visibility(tmp_path)
    lower = surface.lower()
    assert "project loam" in lower
    assert "project cairn" in lower
    assert "pieces built" in lower
    # The zero-internal-vocab HARD invariant holds for the multi-repo
    # surface (counts + plain display names only — no module names / SHAs).
    assert not contains_internal_vocabulary(surface), (
        f"AC.WVS-MR.3 — live multi-repo surface leaked internal vocab: "
        f"{surface!r}"
    )
