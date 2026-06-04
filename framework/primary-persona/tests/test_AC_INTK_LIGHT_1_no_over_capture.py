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

"""AC.INTK.LIGHT.1 — no over-capture at the light default.

Under the default (light) aggressiveness: ordinary chatter and a trivial one-off
("can you reformat this paragraph") do NOT produce a proposal or a tracked item;
only a clear forward-looking piece of work does. The number of proposals over a
sequence of mixed turns matches the count of genuine work-intent turns, not the
turn count."""

from __future__ import annotations

from _helpers_intake import FakeWorkIntentExtractor, fresh_tracker

from loam.primary_persona.keep_pace.intake import WorkIntent, intake_turn


async def test_AC_INTK_LIGHT_1_mixed_sequence_proposal_count(tmp_path) -> None:
    # A mixed sequence: 2 clear work turns, 1 soft/aside, 2 chatter/one-off.
    turns = {
        "I need to renew the registration": WorkIntent(
            is_work=True, title="renew the registration", strength="clear"
        ),
        "remind me to book the dentist": WorkIntent(
            is_work=True, title="book the dentist", strength="clear"
        ),
        "might look into solar panels eventually": WorkIntent(
            is_work=True, title="look into solar panels", strength="soft"
        ),
        "what's the capital of Peru?": WorkIntent(is_work=False),
        "can you reformat this paragraph for me": WorkIntent(is_work=False),
    }
    ext = FakeWorkIntentExtractor(turns)
    tracker = fresh_tracker(tmp_path)
    try:
        proposals = []
        for text in turns:
            p = await intake_turn(
                text, tracker, extractor=ext, claude_home=tmp_path / "home"
            )
            if p is not None:
                proposals.append(p)
        # Only the 2 CLEAR work turns produce proposals at the light default —
        # the soft/aside is NOT captured; the chatter/one-off are NOT captured.
        assert len(proposals) == 2, f"over/under-capture: {[p.title for p in proposals]}"
        titles = {p.title for p in proposals}
        assert titles == {"renew the registration", "book the dentist"}
        # Exactly 2 items in the store (not 5).
        assert len(list(tracker.query_projection_view())) == 2
    finally:
        tracker.close()


async def test_AC_INTK_LIGHT_1_trivial_one_off_not_captured(tmp_path) -> None:
    ext = FakeWorkIntentExtractor(
        {"reformat this paragraph": WorkIntent(is_work=False)}
    )
    tracker = fresh_tracker(tmp_path)
    try:
        p = await intake_turn(
            "reformat this paragraph", tracker,
            extractor=ext, claude_home=tmp_path / "home",
        )
        assert p is None
        assert list(tracker.query_projection_view()) == []
    finally:
        tracker.close()
