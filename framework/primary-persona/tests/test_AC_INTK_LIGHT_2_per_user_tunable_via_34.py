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

"""AC.INTK.LIGHT.2 — aggressiveness read from #34, light default.

The intake aggressiveness is read from the per-user interaction-model
(``work-tracking`` / ``intake-aggressiveness``), defaulting light when no cell
is set; setting the cell to ``off`` produces no proposals on any turn, and
setting it to a more-eager value lowers the threshold at which a turn produces a
proposal — changing the cell changes the capture behavior without editing intake.
Mirrors the WMS-D4 per-user dial."""

from __future__ import annotations

from _helpers_intake import (
    FakeWorkIntentExtractor,
    fresh_tracker,
    write_aggressiveness_matrix,
)

from loam.primary_persona.keep_pace.intake import (
    DEFAULT_AGGRESSIVENESS,
    AGGR_LIGHT,
    WorkIntent,
    intake_turn,
    resolve_aggressiveness,
)


def test_AC_INTK_LIGHT_2_missing_cell_defaults_light(tmp_path) -> None:
    # No matrix file at all -> light default.
    assert resolve_aggressiveness(tmp_path / "empty-home") == AGGR_LIGHT
    assert DEFAULT_AGGRESSIVENESS == AGGR_LIGHT


async def test_AC_INTK_LIGHT_2_off_produces_no_proposal(tmp_path) -> None:
    home = write_aggressiveness_matrix(tmp_path / "home", "off")
    # Even a CLEAR work turn produces nothing at `off`.
    work = WorkIntent(is_work=True, title="renew the registration", strength="clear")
    ext = FakeWorkIntentExtractor({"I need to renew the registration": work})
    tracker = fresh_tracker(tmp_path)
    try:
        p = await intake_turn(
            "I need to renew the registration", tracker,
            extractor=ext, claude_home=home,
        )
        assert p is None, "`off` aggressiveness still proposed"
        assert list(tracker.query_projection_view()) == []
    finally:
        tracker.close()


async def test_AC_INTK_LIGHT_2_eager_lowers_threshold(tmp_path) -> None:
    # A SOFT/aside signal: light does NOT propose it; eager DOES — changing the
    # cell changes the behavior without editing intake.
    soft = WorkIntent(is_work=True, title="look into solar panels", strength="soft")
    turn = "might look into solar panels eventually"

    light_home = write_aggressiveness_matrix(tmp_path / "light", "light")
    eager_home = write_aggressiveness_matrix(tmp_path / "eager", "eager")

    ext = FakeWorkIntentExtractor({turn: soft})
    tracker_light = fresh_tracker(tmp_path / "dbl")
    try:
        p_light = await intake_turn(
            turn, tracker_light, extractor=ext, claude_home=light_home
        )
        assert p_light is None, "light captured a soft signal"
    finally:
        tracker_light.close()

    ext2 = FakeWorkIntentExtractor({turn: soft})
    tracker_eager = fresh_tracker(tmp_path / "dbe")
    try:
        p_eager = await intake_turn(
            turn, tracker_eager, extractor=ext2, claude_home=eager_home
        )
        assert p_eager is not None, "eager did not capture a soft signal"
        assert p_eager.title == "look into solar panels"
    finally:
        tracker_eager.close()
