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

"""AC.INTK.DETECT.1 — work-vs-not discrimination over a turn.

A turn carrying a clear forward-looking piece of work is recognised as
work-intent and produces a candidate (a plain title + optional candidate
stream/project + optional waiting-on party); a turn carrying no work-intent
produces no candidate. Method (which extractor, what prompt) is the builder's
call — here exercised via the injected extractor seam."""

from __future__ import annotations

from _helpers_intake import FakeWorkIntentExtractor, fresh_tracker

from loam.primary_persona.keep_pace.intake import WorkIntent, intake_turn


async def test_AC_INTK_DETECT_1_work_turn_yields_candidate(tmp_path) -> None:
    work = WorkIntent(
        is_work=True,
        title="rental paperwork",
        candidate_stream="house",
        waits_on="",
        strength="clear",
    )
    ext = FakeWorkIntentExtractor({"I need to get the rental paperwork going": work})
    tracker = fresh_tracker(tmp_path)
    try:
        proposal = await intake_turn(
            "I need to get the rental paperwork going",
            tracker,
            extractor=ext,
            claude_home=tmp_path / "home",  # no matrix -> light default
        )
        assert proposal is not None, "a clear work turn produced no candidate"
        assert proposal.title == "rental paperwork"
        assert proposal.candidate_stream == "house"
    finally:
        tracker.close()


async def test_AC_INTK_DETECT_1_chatter_turn_yields_no_candidate(tmp_path) -> None:
    # The extractor reads pure chatter as non-work (is_work=False).
    ext = FakeWorkIntentExtractor(
        {"what time is it in Tokyo right now?": WorkIntent(is_work=False)}
    )
    tracker = fresh_tracker(tmp_path)
    try:
        proposal = await intake_turn(
            "what time is it in Tokyo right now?",
            tracker,
            extractor=ext,
            claude_home=tmp_path / "home",
        )
        assert proposal is None, "a chatter turn produced a candidate"
        # No item was created.
        assert list(tracker.query_projection_view()) == []
    finally:
        tracker.close()


async def test_AC_INTK_DETECT_1_waits_on_party_captured(tmp_path) -> None:
    work = WorkIntent(
        is_work=True,
        title="launch review",
        waits_on="Eric",
        strength="clear",
    )
    ext = FakeWorkIntentExtractor({"the launch waits on Eric's review": work})
    tracker = fresh_tracker(tmp_path)
    try:
        proposal = await intake_turn(
            "the launch waits on Eric's review",
            tracker,
            extractor=ext,
            claude_home=tmp_path / "home",
        )
        assert proposal is not None
        # The waiting-on party surfaces in the plain-language line.
        assert "Eric" in proposal.line
    finally:
        tracker.close()
