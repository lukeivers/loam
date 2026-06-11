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

"""AC.BRC.6 — a no-op in-loop `check_command: "true"` is replaced
by the behavioural self-check, GENERICALLY.

Outcome under test (not method): the concrete defect — a consumer
harness wired the loop's in-loop `check_command` to literally
`"true"`, so the loop's keep-going condition was satisfied by a no-op
— is fixed by routing the in-loop check through the GENERIC
behavioural self-check construct, NOT a consumer-specific hack and
NOT a hand-authored per-task `"true"`-replacement string and NOT
another no-op / structural-only command. The same construct serves
any task driven through the loop.

History: the original consumer harness that exposed the defect was
retired 2026-06-11 (its three harness-coupled tests retired with it;
the retirement plan-doc lives in docs/plans/); the two tests below
assert the surviving GENERIC capability.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
HANDSOFF_SRC = ROOT / "framework" / "tools" / "handsoff-loop" / "src"
sys.path.insert(0, str(HANDSOFF_SRC))


def test_AC_BRC_6_construct_is_generic_not_consumer_specific() -> None:
    """The behavioural self-check construct lives in the handsoff-loop
    package (generic — the loop's own construct, serving any consumer),
    NOT in any consumer harness."""
    from handsoff_loop import behavioral_selfcheck as bsc

    mod_path = Path(inspect.getfile(bsc))
    assert "handsoff-loop" in str(mod_path), (
        "the construct must be the generic loop construct, not a "
        "consumer-local one"
    )


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
