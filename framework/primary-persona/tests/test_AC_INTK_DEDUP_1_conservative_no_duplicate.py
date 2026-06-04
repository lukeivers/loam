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

"""AC.INTK.DEDUP.1 — re-mentions don't duplicate; new work still lands.

When a turn mentions a piece of work that closely matches an OPEN work item
already in the store (a re-mention), intake does NOT create a second
proposal/item for it; when a turn mentions a genuinely new piece of work that is
not a near-duplicate, it IS proposed. A sequence of re-mentions of one thing
yields one tracked item, not a pile. The match method (string / embedding / LLM)
is the builder's call; the bias is CONSERVATIVE (suppress only on a
high-confidence match — a false-merge silently drops new work, plan §10 RF #3)."""

from __future__ import annotations

from _helpers_intake import FakeWorkIntentExtractor, fresh_tracker

from loam.primary_persona.keep_pace.intake import WorkIntent, intake_turn


async def test_AC_INTK_DEDUP_1_re_mention_yields_one_item(tmp_path) -> None:
    # Three re-mentions of the same work across three turns -> ONE item.
    title = "rental paperwork"
    turns = {
        "I need to do the rental paperwork": WorkIntent(
            is_work=True, title=title, strength="clear"
        ),
        "still have to get the rental paperwork done": WorkIntent(
            is_work=True, title="rental paperwork", strength="clear"
        ),
        "the rental paperwork is still hanging over me": WorkIntent(
            is_work=True, title="rental paperwork", strength="clear"
        ),
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
        # Only the FIRST mention proposes; the re-mentions are deduped.
        assert len(proposals) == 1, f"re-mentions piled up: {len(proposals)}"
        assert len(list(tracker.query_projection_view())) == 1
    finally:
        tracker.close()


async def test_AC_INTK_DEDUP_1_genuinely_new_work_still_lands(tmp_path) -> None:
    # An item exists; a DIFFERENT piece of work is mentioned -> it IS proposed
    # (the conservative bias: only a high-confidence match suppresses).
    turns = {
        "I need to do the rental paperwork": WorkIntent(
            is_work=True, title="rental paperwork", strength="clear"
        ),
        "I also have to schedule the roof inspection": WorkIntent(
            is_work=True, title="schedule the roof inspection", strength="clear"
        ),
    }
    ext = FakeWorkIntentExtractor(turns)
    tracker = fresh_tracker(tmp_path)
    try:
        first = await intake_turn(
            "I need to do the rental paperwork", tracker,
            extractor=ext, claude_home=tmp_path / "home",
        )
        second = await intake_turn(
            "I also have to schedule the roof inspection", tracker,
            extractor=ext, claude_home=tmp_path / "home",
        )
        assert first is not None
        assert second is not None, "a genuinely-new item was falsely merged"
        assert len(list(tracker.query_projection_view())) == 2
    finally:
        tracker.close()


async def test_AC_INTK_DEDUP_1_similar_sounding_new_work_not_falsely_merged(tmp_path) -> None:
    # The false-merge guard: a NEW item that merely SOUNDS adjacent (shares one
    # generic word) is NOT suppressed — a visible item beats a silent drop.
    turns = {
        "I need to review the Q3 budget": WorkIntent(
            is_work=True, title="review the Q3 budget", strength="clear"
        ),
        "I should review the marketing plan too": WorkIntent(
            is_work=True, title="review the marketing plan", strength="clear"
        ),
    }
    ext = FakeWorkIntentExtractor(turns)
    tracker = fresh_tracker(tmp_path)
    try:
        await intake_turn(
            "I need to review the Q3 budget", tracker,
            extractor=ext, claude_home=tmp_path / "home",
        )
        second = await intake_turn(
            "I should review the marketing plan too", tracker,
            extractor=ext, claude_home=tmp_path / "home",
        )
        assert second is not None, "a similar-sounding NEW item was falsely merged"
        assert len(list(tracker.query_projection_view())) == 2
    finally:
        tracker.close()
