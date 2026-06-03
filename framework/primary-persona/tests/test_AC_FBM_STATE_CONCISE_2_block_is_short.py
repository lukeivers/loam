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

"""AC-FBM-STATE-CONCISE-2 (Slice D — conciseness guard) — the STATE block is
SHORT and high-signal: one line per project, modules grouped by liveness class,
under the hard cap, NOT a per-module evidence dump.

The whole point of the overhaul is LESS junk + MORE accuracy in the turn-start
context. This AC pins the conciseness contract so the removed junk is not traded
for a new wall of status text: a project with many modules renders ONE line, the
module names liveness-grouped, the per-module EVIDENCE strings absent from the
surfaced block.
"""

from __future__ import annotations

from loam_cli.audit.probe import Liveness
from loam_cli.audit.record import ComponentState, StateOfLoam

from loam.primary_persona.keep_pace.project_state import (
    _STATE_BLOCK_CHAR_CAP,
    render_project_state_block,
)


def _record_with_evidence() -> StateOfLoam:
    """A many-module record whose rows carry LONG distinctive evidence
    strings (so we can assert the evidence does NOT leak into the block)."""
    mods = ["verify", "ledger", "execute", "pilot", "cause"]
    rows = tuple(
        ComponentState(
            name=m,
            liveness=Liveness.MERGED,
            kind="component",
            evidence=(
                f"DISTINCTIVE_EVIDENCE_{m}_xyzzy present (7 impl files); "
                f"introducing commit deadbeef is an ancestor of HEAD"
            ),
        )
        for m in mods
    )
    return StateOfLoam(head_sha="0123456789ab", components=rows)


def test_block_is_one_line_per_project_under_cap() -> None:
    """The rendered block is one line per project (plus the header), grouped
    by liveness, under the hard char cap."""
    rec = _record_with_evidence()
    block = render_project_state_block(
        names=("cairn",), derive=lambda _n: rec
    )
    assert block, "the block must render for a populated record"
    assert len(block) <= _STATE_BLOCK_CHAR_CAP, (
        f"the block must stay under the {_STATE_BLOCK_CHAR_CAP}-char cap; "
        f"got {len(block)} chars:\n{block}"
    )
    # Exactly one project LINE (a '  - ' bullet) — modules are grouped onto it,
    # NOT one line per module.
    project_lines = [ln for ln in block.splitlines() if ln.strip().startswith("- ")]
    assert len(project_lines) == 1, (
        f"one project must render as exactly one line; got {project_lines}"
    )
    # All five modules appear on that single line (liveness-grouped).
    line = project_lines[0]
    for m in ("verify", "ledger", "execute", "pilot", "cause"):
        assert m in line, f"module {m} must appear on the single project line"


def test_per_module_evidence_does_not_leak() -> None:
    """The per-module EVIDENCE strings are NOT dumped into the surfaced block
    — it is glanceable status, not a verbose evidence dump."""
    rec = _record_with_evidence()
    block = render_project_state_block(
        names=("cairn",), derive=lambda _n: rec
    )
    assert "DISTINCTIVE_EVIDENCE" not in block, (
        "the concise block must NOT dump per-module evidence strings; "
        f"got:\n{block}"
    )
    assert "impl files" not in block and "ancestor of HEAD" not in block, (
        f"evidence prose leaked into the concise block:\n{block}"
    )
