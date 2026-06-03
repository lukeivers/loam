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

"""AC-FBM-STATE-LIVE-4 (Slice D / D3 — OUTCOME-ALTITUDE) — ``outcome-altitude:true``.

Run the REAL production entry point ``render_project_state_block()`` with NO
pre-arranged state against the LIVE loam + cairn repos. The rendered block must
carry an ACCURATE ground-truth status:

  * BOTH registered projects (loam AND cairn) appear, AND
  * the Cairn line shows ``verify``, ``ledger``, ``execute`` as BUILT — so the
    persona literally cannot, from this turn-start context, claim those modules
    "remain to be built". This reproduces, AT THE LENS SURFACE, the verdict the
    persona got WRONG, now derived from ground truth.

No fixtures, no fixture record injection — the production registry + the live
git/disk probes. Skips (does not fail) only if the live Cairn repo is absent on
this host (the probe target is environment-specific); on the build host it is
present and the assertion runs for real.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.primary_persona.keep_pace.project_state import (
    render_project_state_block,
)

_CAIRN_REPO = Path("/Users/lukeivers/cairn")


@pytest.mark.skipif(
    not _CAIRN_REPO.is_dir(),
    reason="live Cairn repo absent on this host; outcome-altitude target unavailable",
)
def test_live_state_block_shows_cairn_engine_built() -> None:
    """The production entry point, no pre-arranged state, against the live
    repos, surfaces an accurate block: loam + cairn present; Cairn's
    verify/ledger/execute shown BUILT."""
    block = render_project_state_block()  # production registry + live probes
    assert block, "the live STATE block must render (loam + cairn registered)"

    low = block.lower()

    # Both registered projects appear.
    assert "loam" in low, f"the loam project must appear in the block; got:\n{block}"
    assert "cairn" in low, f"the cairn project must appear in the block; got:\n{block}"

    # The Cairn engine modules the persona got WRONG must show as BUILT.
    cairn_line = next(
        (ln for ln in block.splitlines() if "cairn" in ln.lower()), ""
    )
    assert cairn_line, f"a Cairn status line must be present; got:\n{block}"
    cl = cairn_line.lower()
    for module in ("verify", "ledger", "execute"):
        assert module in cl, (
            f"the Cairn line must name {module}; got:\n{cairn_line}"
        )
    # "built" must be the status phrasing on the Cairn line (merged => "built").
    assert "built" in cl, (
        "the Cairn engine modules must show as BUILT in the turn-start context "
        f"(so the persona cannot claim they 'remain to be built'); got:\n{cairn_line}"
    )
    # And the WRONG verdict's phrasing must NOT be derivable from this line:
    # the modules are not 'not built'.
    assert "not built" not in cl, (
        f"the Cairn engine must not be shown as not-built; got:\n{cairn_line}"
    )
