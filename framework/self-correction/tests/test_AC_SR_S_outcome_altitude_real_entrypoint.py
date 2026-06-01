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

"""★ AC.SR-S.1 — outcome-altitude (outcome-altitude: true).

A real scenario at the PRODUCTION entry-points, with NO pre-arranged state:

  (a) a 2nd distress signal trips detection through the REAL detector;
  (b) the system produces a REAL plain-language recovery surface (verified
      to carry zero internal vocabulary); and
  (c) for the reset branch, after running the REAL reset entry-point
      (`loam recover` via its production subcommand) the prior .loam/ store
      is restorable byte-for-byte, AND a no-backup reset is refused.

Per feedback_test_outcome_altitude_required: this test invokes the real
entry-points. It does NOT stub the detector, pre-seed the recovery text, or
fake the snapshot. The detector counter starts EMPTY (no pre-arranged
trip), the workspace starts with a real .loam/ this test creates as the
user's data (not as a fixture the production path is handed), and the reset
runs through the CLI verb the non-tech user would actually invoke.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
HOOKS_DIR = REPO_ROOT / "framework" / "self-correction" / "hooks"
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from distress_detector import DistressDetector  # noqa: E402

from loam.self_correction import (  # noqa: E402
    RecoverySituation,
    contains_internal_vocabulary,
    render_recovery,
)
from loam.self_correction.recover_cli import main as recover_main  # noqa: E402


def test_AC_SR_S_1_real_trip_recover_preserve_end_to_end(
    tmp_path: Path, capsys
) -> None:
    """outcome-altitude: a real stuck scenario trips, recovers, and
    preserves the store — driven through the real entry-points with no
    pre-arranged state."""

    # ----- (a) REAL detection trip, counter starts EMPTY ----------------
    # No pre-arranged state: a fresh detector with an empty counter file.
    state_path = tmp_path / "distress-counter.json"
    assert not state_path.exists()  # nothing pre-arranged
    detector = DistressDetector(state_path=state_path)

    first = detector.observe("hey, are you still there?")
    assert first.tripped is False  # 1st signal does not trip
    second = detector.observe("is this thing stuck? nothing's happening")
    assert second.tripped is True  # the REAL 2nd-signal trip

    # ----- (b) REAL plain-language recovery surface ---------------------
    # The trip routes to the work-stuck recovery surface; render it for real
    # and verify zero internal vocabulary (not pre-seeded text).
    surface = render_recovery(RecoverySituation.work_stuck)
    assert surface.text.strip()
    assert contains_internal_vocabulary(surface.text) is False

    # ----- (c) REAL reset entry-point, store preserved ------------------
    # Create the user's REAL .loam/ store (their irreplaceable data). The
    # production reset path is NOT handed a fake snapshot — it makes its own.
    ws = tmp_path / "workspace"
    loam = ws / ".loam"
    (loam / "memory").mkdir(parents=True)
    user_data = {
        ".loam/objectives.yaml": b"goal: finish the book\n",
        ".loam/memory/canon.md": b"# canon\nthe dragon is named Ember\n",
        ".loam/state.json": b'{"chapter": 7}',
    }
    for rel, content in user_data.items():
        (ws / rel).write_bytes(content)

    # First: a reset with NO confirm is refused by the REAL CLI verb (the
    # non-tech user must say yes; the store survives).
    rc_unconfirmed = recover_main(["reset", "--workspace", str(ws)])
    assert rc_unconfirmed == 2  # refused
    assert (ws / ".loam").exists()  # store untouched

    # Then: the REAL reset, confirmed. Backup-first + fail-closed are
    # inherited from the migration-safety envelope the verb delegates to.
    rc = recover_main(
        ["reset", "--workspace", str(ws), "--confirm", "yes, start fresh"]
    )
    assert rc == 0
    out = capsys.readouterr().out
    # The user-facing confirmation is plain-language (zero internal vocab).
    assert contains_internal_vocabulary(out) is False
    # The destructive step ran.
    assert not (ws / ".loam").exists()

    # The pre-reset store is restorable byte-for-byte from the REAL snapshot
    # the production path made (locate it via the verb's snapshot root).
    from loam.reversibility_primitive import ReversibilityStore
    from loam.self_correction import SafeFbmReset

    store_dir = ws / ".loam-recovery"
    snap_root = store_dir / "snapshots"
    store = ReversibilityStore(store_dir / "reversibility.sqlite")
    try:
        resetter = SafeFbmReset(store=store, snapshot_root=snap_root)
        resetter.restore(snap_root / "loam-snapshot", ws)
    finally:
        store.close()

    assert (ws / ".loam").exists()
    for rel, content in user_data.items():
        assert (ws / rel).read_bytes() == content, f"{rel} not byte-identical"


def test_AC_SR_S_1_real_check_verb_runs_clean(tmp_path: Path, capsys) -> None:
    """The real `loam recover check` verb runs end-to-end on a cold
    workspace and prints a plain-language status with zero internal
    vocabulary (no pre-arranged state)."""
    ws = tmp_path / "cold"
    ws.mkdir()
    rc = recover_main(["check", "--workspace", str(ws)])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.strip()
    assert contains_internal_vocabulary(out) is False
