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

"""AC.SR-RECOVER.1 + AC.SR-RECOVER.2 — the recovery surface is
plain-language + actionable and carries ZERO internal vocabulary.

AC.SR-RECOVER.1 — the surface a non-technical user receives is
plain-English, gives a concrete next action, and is satisfiable by a
non-technical user (no logs, no dev commands, no internal concepts).

AC.SR-RECOVER.2 — the user-facing recovery text contains no stack traces,
AC-IDs, commit SHAs, file paths, agent-IDs, or ODD/methodology vocabulary.
"""

from __future__ import annotations

import pytest

from loam.self_correction import (
    RecoverySituation,
    RecoverySurfaceLeak,
    contains_internal_vocabulary,
    find_internal_vocabulary,
    render_recovery,
)


_ALL_SITUATIONS = (
    RecoverySituation.channel_down,
    RecoverySituation.work_stuck,
    RecoverySituation.claimed_not_done,
    RecoverySituation.reset_offered,
    RecoverySituation.all_clear,
)


# ---- AC.SR-RECOVER.1 — plain-language + actionable --------------------


@pytest.mark.parametrize("situation", _ALL_SITUATIONS)
def test_AC_SR_RECOVER_1_every_surface_is_actionable(situation: str) -> None:
    """Every rendered surface gives a concrete next action a non-technical
    user can take (a headline + a next-action block)."""
    msg = render_recovery(situation)
    assert msg.headline.strip()
    assert msg.next_action.strip()
    # The full text reads as plain prose: it has both blocks.
    assert msg.headline in msg.text
    assert msg.next_action in msg.text


@pytest.mark.parametrize("situation", _ALL_SITUATIONS)
def test_AC_SR_RECOVER_1_no_dev_instructions(situation: str) -> None:
    """The surface never tells the user to read logs / run dev commands /
    know an internal concept."""
    text = render_recovery(situation).text.lower()
    for forbidden in (
        "stack trace",
        "log file",
        "run the command",
        "pytest",
        "git ",
        "traceback",
        "exception",
        "config file",
    ):
        assert forbidden not in text, f"{situation}: leaked dev instruction {forbidden!r}"


# ---- AC.SR-RECOVER.2 — zero internal vocabulary -----------------------


@pytest.mark.parametrize("situation", _ALL_SITUATIONS)
def test_AC_SR_RECOVER_2_rendered_surface_is_clean(situation: str) -> None:
    """The rendered surface carries ZERO internal vocabulary."""
    text = render_recovery(situation).text
    hits = find_internal_vocabulary(text)
    assert hits == (), f"{situation}: internal vocab leaked: {[h.matched for h in hits]}"
    assert contains_internal_vocabulary(text) is False


def test_AC_SR_RECOVER_2_probe_catches_each_forbidden_shape() -> None:
    """The probe (the verifier the AC relies on) actually flags each
    forbidden internal shape — so a real leak would be caught."""
    samples = {
        "ac-id": "see AC.SR-RECOVER.2 for details",
        "commit-sha": "fixed in 634030fe now",
        "file-path": "open framework/self-correction/cli.py",
        "module-path": "import loam.self_correction.safe_reset",
        "traceback": "Traceback (most recent call last): boom",
        "methodology-vocab": "this violates the ODD acceptance criteria",
    }
    for label, text in samples.items():
        assert contains_internal_vocabulary(text), f"probe missed {label}: {text!r}"


def test_AC_SR_RECOVER_2_leak_raises_rather_than_ships() -> None:
    """If a render WOULD leak (hard invariant, plan §8), it raises rather
    than shipping the leak to the user. We prove the self-check is wired by
    forcing a leaky situation block."""
    from loam.self_correction import recovery_surface as rs

    leaky = "self-recovery-internal"
    orig = dict(rs._SITUATION_BLOCKS)
    rs._SITUATION_BLOCKS[leaky] = (
        "Here is your error",
        "Run pytest framework/self-correction/tests/foo.py to see AC.SR-S.1",
    )
    try:
        with pytest.raises(RecoverySurfaceLeak):
            render_recovery(leaky)
    finally:
        rs._SITUATION_BLOCKS.clear()
        rs._SITUATION_BLOCKS.update(orig)


def test_AC_SR_RECOVER_2_unknown_situation_rejected() -> None:
    with pytest.raises(ValueError):
        render_recovery("not-a-real-situation")
