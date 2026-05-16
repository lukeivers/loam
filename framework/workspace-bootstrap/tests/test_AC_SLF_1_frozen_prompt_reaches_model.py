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

"""AC.SLF.1 — the frozen prompt verifiably reaches the model
regardless of how many bracketed-paste fragments it is split into.

Plan: docs/plans/subloam-driver-fix.md  (§3 AC.SLF.1)

Root cause (verified, programbench-step0-rootcause-and-contamination
-2026-05-15.md §A): the OLD submission path wrote the multi-KB frozen
prompt in one os.write, slept a FIXED 0.5 s, then sent ``\\n``
unconditionally. The real TUI fragments a large write into multiple
bracketed-paste segments (ESC[200~ … ESC[201~); a ``\\n`` that arrives
while a fragment is still in flight lands as literal text inside the
open paste, not as the submit key — the turn was never submitted and
the run died on the idle-timeout.

The fix replaces fixed-sleep submission with a paste-settle gate
(:func:`_paste_has_settled`): the submit ``\\n`` is sent ONLY after
the bracketed-paste echo has gone quiet for ``paste_settle_s``. This
test pins the OUTCOME — the submit decision is never made while a
fragment is still arriving — across 1, 3, and many fragments. It is
deterministic (a simulated fragment-arrival timeline, no real claude;
the real frozen-prompt end-test is AC.SLF.4/.5).
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

from subloam_driver.driver import _paste_has_settled  # noqa: E402

SETTLE = 2.5


def _submit_time_for_fragments(
    *,
    write_at: float,
    fragment_echo_times: list[float],
    settle_s: float = SETTLE,
    tick: float = 0.25,
    horizon: float = 120.0,
) -> float | None:
    """Replay the driver's submit-gate against a simulated timeline.

    ``fragment_echo_times`` are absolute times at which bracketed-
    paste echo bytes for each fragment arrive (the driver advances
    ``last_paste_echo_at`` on each). Returns the time the submit
    gate first fires (the ``\\n`` would be sent), or None within the
    horizon. Mirrors the loop's ~``tick``-second select cadence.
    """
    now = write_at
    while now <= write_at + horizon:
        last_echo = write_at
        for t in fragment_echo_times:
            if t <= now:
                last_echo = max(last_echo, t)
        if _paste_has_settled(
            now=now,
            prompt_written_at=write_at,
            last_paste_echo_at=last_echo,
            paste_settle_s=settle_s,
        ):
            return now
        now += tick
    return None


def test_AC_SLF_1_single_fragment_submits_after_settle() -> None:
    """A short prompt that arrives as ONE echo fragment: the submit
    gate fires only after the settle window past that fragment."""
    submit = _submit_time_for_fragments(
        write_at=100.0,
        fragment_echo_times=[100.1],
    )
    assert submit is not None
    # Never before the last fragment's echo + the settle window.
    assert submit >= 100.1 + SETTLE
    # And not absurdly late (bounded by tick granularity).
    assert submit <= 100.1 + SETTLE + 0.5


def test_AC_SLF_1_three_fragments_submit_only_after_last_settles() -> None:
    """The verified failing scenario: the frozen yj prompt arrived as
    THREE bracketed-paste chunks. The submit gate must NOT fire until
    the THIRD fragment has settled — never between fragments (that is
    exactly the ``\\n``-inside-an-open-paste root cause)."""
    frag1, frag2, frag3 = 100.4, 102.0, 104.5
    submit = _submit_time_for_fragments(
        write_at=100.0,
        fragment_echo_times=[frag1, frag2, frag3],
    )
    assert submit is not None
    # The submit decision is made strictly AFTER the last fragment +
    # the settle window — i.e. never while fragment 2 or 3 is still
    # in flight.
    assert submit >= frag3 + SETTLE
    # Crucial negative: the gate did NOT fire in the gap between
    # fragment 1 and fragment 2 (where the OLD fixed-0.5s sleep would
    # have sent the ``\n`` into an open paste).
    assert submit > frag2
    assert submit > frag1


def test_AC_SLF_1_many_fragments_regardless_of_count() -> None:
    """Outcome is delivery-path agnostic: for an arbitrarily
    fragmented prompt (here 12 fragments dribbling in) the submit
    gate still only fires after the FINAL fragment settles — the AC's
    'regardless of how many fragments' clause."""
    write_at = 50.0
    echoes = [write_at + 0.3 + i * 0.9 for i in range(12)]
    submit = _submit_time_for_fragments(
        write_at=write_at,
        fragment_echo_times=echoes,
    )
    assert submit is not None
    assert submit >= echoes[-1] + SETTLE
    # Did not fire during the 12-fragment arrival window.
    assert submit > echoes[-1]


def test_AC_SLF_1_floor_when_no_echo_ever_arrives() -> None:
    """Degenerate case: the TUI emits NO echo at all. The gate must
    still eventually fire on the write-time floor (so a run never
    hangs forever un-submitted), but never before the settle floor."""
    submit = _submit_time_for_fragments(
        write_at=10.0,
        fragment_echo_times=[],
    )
    assert submit is not None
    assert submit >= 10.0 + SETTLE


def test_AC_SLF_1_predicate_false_while_fragment_in_flight() -> None:
    """Direct predicate assertion: while a fragment echo is still
    arriving (last echo within the settle window of now) the gate is
    False — the submit ``\\n`` is withheld."""
    # Fragment echoed 0.5 s ago, settle window 2.5 s -> NOT settled.
    assert (
        _paste_has_settled(
            now=200.0,
            prompt_written_at=190.0,
            last_paste_echo_at=199.5,
            paste_settle_s=SETTLE,
        )
        is False
    )
    # Echo quiet for 3.0 s and 10 s since write -> settled.
    assert (
        _paste_has_settled(
            now=200.0,
            prompt_written_at=190.0,
            last_paste_echo_at=197.0,
            paste_settle_s=SETTLE,
        )
        is True
    )
