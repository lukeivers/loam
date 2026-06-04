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

"""AC.INTK.DETECT.2 — fail-soft to silence on extractor decline.

When the intent-extraction seam declines (unavailable / times out / no usable
read), intake surfaces NO proposal for that turn and the turn proceeds normally
— the failure never propagates and never produces a low-quality over-capture.
The default extractor DECLINES, so the path is off until a real one is
registered; that decline is the same fail-soft-to-silence path."""

from __future__ import annotations

from _helpers_intake import FakeWorkIntentExtractor, fresh_tracker

from loam.primary_persona.keep_pace.intake import (
    DisabledWorkIntentExtractor,
    build_intake_contributor,
    default_work_intent_extractor,
    intake_turn,
)


async def test_AC_INTK_DETECT_2_decline_yields_no_proposal(tmp_path) -> None:
    ext = FakeWorkIntentExtractor(decline=True)
    tracker = fresh_tracker(tmp_path)
    try:
        proposal = await intake_turn(
            "I really need to finish the budget this week",
            tracker,
            extractor=ext,
            claude_home=tmp_path / "home",
        )
        assert proposal is None, "extractor decline produced a proposal"
        assert list(tracker.query_projection_view()) == [], "decline created an item"
    finally:
        tracker.close()


async def test_AC_INTK_DETECT_2_default_extractor_declines(tmp_path) -> None:
    # The default extractor is the disabled one (opt-in / off until registered).
    assert isinstance(default_work_intent_extractor(), DisabledWorkIntentExtractor)
    tracker = fresh_tracker(tmp_path)
    try:
        # With no extractor passed, intake resolves the default (declines).
        proposal = await intake_turn(
            "I need to renew the registration",
            tracker,
            claude_home=tmp_path / "home",
        )
        assert proposal is None
        assert list(tracker.query_projection_view()) == []
    finally:
        tracker.close()


def test_AC_INTK_DETECT_2_contributor_never_raises_on_decline(tmp_path) -> None:
    # The turn contributor returns "" (no block) on decline — the turn proceeds.
    ext = FakeWorkIntentExtractor(decline=True)
    db_tracker = fresh_tracker(tmp_path)
    try:
        fn = build_intake_contributor(
            tracker_factory=lambda: fresh_tracker(tmp_path),
            extractor=ext,
            claude_home=tmp_path / "home",
        )
        out = fn({"prompt": "I need to schedule the inspection"})
        assert out == "", "decline did not yield an empty contributor output"
    finally:
        db_tracker.close()
