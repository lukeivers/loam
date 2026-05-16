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

"""AC.BRC.6 — the realpb in-loop `check_command: "true"` is replaced
by the behavioural self-check, GENERICALLY.

Outcome under test (not method): the concrete defect — the realpb arm
wiring set the loop's in-loop `check_command` to literally `"true"`
(arms.py:200), so the loop's keep-going condition was satisfied by a
no-op — is fixed by routing the in-loop check through the GENERIC
behavioural self-check construct, NOT a realpb-specific hack and NOT a
hand-authored per-task `"true"`-replacement string and NOT another
no-op / structural-only command.  The same construct serves any task
driven through the loop (the realpb arm is one consumer).
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
PBR_SRC = (
    ROOT / "framework" / "tools" / "programbench-revival" / "src"
)
HANDSOFF_SRC = ROOT / "framework" / "tools" / "handsoff-loop" / "src"
sys.path.insert(0, str(PBR_SRC))
sys.path.insert(0, str(HANDSOFF_SRC))

ARMS = PBR_SRC / "programbench_revival" / "arms.py"


def test_AC_BRC_6_true_literal_removed_from_arms() -> None:
    """The hand-authored `"check_command": "true"` literal is GONE
    from the realpb arm wiring (the concrete bug, removed)."""
    src = ARMS.read_text()
    assert '"check_command": "true"' not in src, (
        "the arms.py:200 `\"true\"` in-loop check_command literal "
        "must be removed — the concrete AC.BRC.6 defect"
    )
    assert "'check_command': 'true'" not in src


def test_AC_BRC_6_arm_does_not_hand_author_a_no_op() -> None:
    """The arm does not substitute ANOTHER no-op / structural-only
    command for the removed `"true"` (no `:`/`echo`/`exit 0`
    in-loop check_command literal)."""
    src = ARMS.read_text()
    for noop in (
        '"check_command": ":"',
        '"check_command": "exit 0"',
        '"check_command": "echo"',
        '"check_command": "false"',
        '"check_command": "/bin/true"',
    ):
        assert noop not in src, (
            f"arms.py substituted a no-op {noop!r} for `\"true\"` — "
            "AC.BRC.6 requires the GENERIC behavioural construct"
        )


def test_AC_BRC_6_arm_routes_through_generic_construct() -> None:
    """The arm opts into the GENERIC behavioural self-check via the
    loop's `--behavioral-done` flag (the construct is the loop's, not
    a realpb-specific hack); the realpb arm is one consumer."""
    src = ARMS.read_text()
    assert "--behavioral-done" in src, (
        "the realpb arm must route the in-loop check through the "
        "GENERIC behavioural self-check (loop CLI --behavioral-done)"
    )
    from programbench_revival.arms import run_loam_arm

    sig = inspect.signature(run_loam_arm)
    # The generic seam is exposed as parameters (default ON for the
    # realpb consumer), proving it is the loop's construct the arm
    # consumes — not a per-task string baked into arms.py.
    assert "behavioral_done" in sig.parameters
    assert sig.parameters["behavioral_done"].default is True
    assert "max_refine_attempts" in sig.parameters


def test_AC_BRC_6_construct_is_generic_not_realpb_specific() -> None:
    """The behavioural self-check construct lives in the handsoff-loop
    package (generic), NOT in programbench-revival, and contains no
    realpb-specific branching."""
    from handsoff_loop import behavioral_selfcheck as bsc

    mod_path = Path(inspect.getfile(bsc))
    assert "handsoff-loop" in str(mod_path), (
        "the construct must be the generic loop construct, not a "
        "realpb-local one"
    )
    body = mod_path.read_text().lower()
    for realpb_token in ("programbench", "realpb", "pbr_", "arms.py"):
        # `arms.py` may appear in a doc cross-reference; the test is
        # for realpb-SPECIFIC LOGIC, so assert no import / branch.
        assert f"import {realpb_token}" not in body
        assert f"if {realpb_token}" not in body


def test_AC_BRC_6_no_op_in_loop_check_is_refused() -> None:
    """Routing a no-op (`true`/`:`/structural-only) as the in-loop
    check is a hard error — the construct refuses it, so a regression
    re-introducing a no-op fails loudly rather than silently shipping
    a hollow `done`."""
    from handsoff_loop.behavioral_selfcheck import (
        NotABehavioralCheck,
        reject_no_op,
    )

    for noop in ("true", ":", "exit 0", "/bin/true", "false", ""):
        with pytest.raises(NotABehavioralCheck):
            reject_no_op(noop)
    # A real behavioural command passes through unchanged.
    assert reject_no_op("sh loam_behavioral_selfcheck.sh").startswith(
        "sh ")
