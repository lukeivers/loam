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

"""AC.SLF.2 — "a real agentic loop ran" is an honest signal.

Plan: docs/plans/subloam-driver-fix.md  (§3 AC.SLF.2)

Root cause (verified 2026-05-15 in the retired benchmark harness's
step-0 root-cause report §B, archived on the pos3 side): the OLD ``_count_effective_turns`` counted three
TUI-chrome needles (``❯`` / ``─ primary ─`` / ``/effort``) alongside
genuine markers and floored at 1, so ``is_multi_turn`` floated True on
a transcript with ZERO model action — a TUI boot alone satisfied it.

The fix: the loop-ran / multi-turn signal is derived from
``genuine_turns`` (genuine markers ONLY — assistant turn / tool_use /
tool_result / the ``⏺`` assistant bullet). The falsification test is
built into the AC: a synthetic chrome-only transcript MUST classify
not-a-loop / not-multi-turn; a synthetic genuine-loop transcript MUST
classify as a loop. ``effective_turns`` is retained only as a
chrome-inclusive transcript-shape diagnostic and is asserted to be
explicitly NOT the loop signal.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[3]
        / "framework"
        / "tools"
        / "subloam-driver"
        / "src"
    ),
)

from subloam_driver import DriverResult  # noqa: E402
from subloam_driver.driver import (  # noqa: E402
    _count_effective_turns,
    _count_genuine_turns,
)

# A real interactive boot emits exactly this chrome and no model
# action: the bound-persona banner, the empty input affordance, the
# per-turn status line — repeated, ANSI-decorated, but ZERO genuine
# turn marker. This is the step-0 RED transcript shape.
CHROME_ONLY = (
    "\x1b[2J\x1b[H"
    "──────────────── primary ────────────────\n"
    '❯ Try "edit <filepath> to…"\n'
    "  /effort  /help  /cost\n"
    "❯ \n"
    "──────────────── primary ────────────────\n"
    "  /effort\n"
    '❯ Try "..."\n'
)

# A genuine agentic loop: assistant turns + tool use + tool result +
# the ⏺ assistant bullet. This is what a real loop emits.
GENUINE_LOOP = (
    "❯ implement the task\n"
    "⏺ Restating as objective + constraints + acceptance.\n"
    "assistant: decomposing into a build-test loop\n"
    "tool_use: write compile.sh\n"
    "tool_result: ok\n"
    "⏺ tests green; emitting FILE blocks\n"
)


def _result(transcript: str) -> DriverResult:
    """Construct exactly as drive() does (honest genuine count)."""
    return DriverResult(
        transcript=transcript,
        effective_turns=_count_effective_turns(transcript),
        genuine_turns=_count_genuine_turns(transcript),
        file_blocks=(),
        exit_status=0,
        spawn_argv=(),
        spawn_env_config_dir="",
        workspace_root=Path("/tmp/x"),
    )


def test_AC_SLF_2_chrome_only_is_not_a_loop_and_not_multiturn() -> None:
    """The load-bearing falsification: a transcript that is ALL chrome
    and ZERO model action can never be classified loop-ran /
    multi-turn (the exact failure the sealed green floated on)."""
    r = _result(CHROME_ONLY)
    assert _count_genuine_turns(CHROME_ONLY) == 0
    assert r.genuine_turns == 0
    assert r.loop_ran is False
    assert r.is_multi_turn is False


def test_AC_SLF_2_genuine_loop_classifies_as_a_loop() -> None:
    """A transcript with genuine markers IS a loop / multi-turn."""
    r = _result(GENUINE_LOOP)
    assert r.genuine_turns > 1
    assert r.loop_ran is True
    assert r.is_multi_turn is True


def test_AC_SLF_2_chrome_does_not_inflate_genuine_count() -> None:
    """Appending unbounded chrome to a genuine transcript does not
    change the genuine count — the signal is chrome-immune."""
    base = _count_genuine_turns(GENUINE_LOOP)
    polluted = GENUINE_LOOP + CHROME_ONLY * 5
    assert _count_genuine_turns(polluted) == base


def test_AC_SLF_2_effective_turns_is_not_the_loop_signal() -> None:
    """effective_turns stays chrome-inclusive and floors at 1 — which
    is exactly why it must NOT be the signal. The chrome-only
    transcript has effective_turns >= 1 yet is correctly NOT a loop:
    the two are decoupled."""
    eff = _count_effective_turns(CHROME_ONLY)
    assert eff >= 1  # chrome-inclusive diagnostic still counts chrome
    r = _result(CHROME_ONLY)
    # Decoupled: high-ish effective_turns, but loop signal is False.
    assert r.is_multi_turn is False
    assert r.loop_ran is False


def test_AC_SLF_2_single_genuine_turn_is_loop_but_not_multiturn() -> None:
    """A single genuine assistant turn: a loop ran (loop_ran True) but
    it is not multi-turn (genuine_turns == 1). The two signals are
    distinct and both honest."""
    one_turn = "⏺ I produced a single response and stopped.\n"
    r = _result(one_turn)
    assert r.genuine_turns == 1
    assert r.loop_ran is True
    assert r.is_multi_turn is False


def test_AC_SLF_2_gradeable_output_alone_counts_as_loop_ran() -> None:
    """If the model emitted gradeable FILE blocks, a loop ran even if
    the bullet markers were ANSI-mangled out of the transcript —
    loop_ran is the honest OR of genuine markers and gradeable
    output."""
    r = DriverResult(
        transcript="FILE: compile.sh\n#!/bin/bash\n",
        effective_turns=1,
        genuine_turns=0,
        file_blocks=("FILE: compile.sh\n#!/bin/bash\n",),
        exit_status=0,
        spawn_argv=(),
        spawn_env_config_dir="",
        workspace_root=Path("/tmp/x"),
    )
    assert r.loop_ran is True
