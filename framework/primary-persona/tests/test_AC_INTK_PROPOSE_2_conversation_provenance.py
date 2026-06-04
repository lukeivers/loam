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

"""AC.INTK.PROPOSE.2 — conversation provenance captured at creation.

The proposed item carries provenance identifying it as captured from
conversation (an ``origin: conversation`` pointer, distinct from
FIDRAFT-graduated / dev-queue / owner-stated origins) and the turn it was
captured from, so its source is recoverable later."""

from __future__ import annotations

from _helpers_intake import FakeWorkIntentExtractor, fresh_tracker

from loam.primary_persona.keep_pace.intake import (
    CONVERSATION_ORIGIN,
    WorkIntent,
    intake_turn,
)


async def test_AC_INTK_PROPOSE_2_origin_conversation_pointer(tmp_path) -> None:
    work = WorkIntent(is_work=True, title="schedule the inspection", strength="clear")
    ext = FakeWorkIntentExtractor({"I should schedule the inspection": work})
    tracker = fresh_tracker(tmp_path)
    try:
        proposal = await intake_turn(
            "I should schedule the inspection",
            tracker,
            extractor=ext,
            claude_home=tmp_path / "home",
            turn_marker="turn-2026-06-03-A",
        )
        assert proposal is not None
        item = tracker.get(proposal.objective_id)
        assert item is not None
        # Provenance identifies it as captured from conversation.
        assert item.lifted_from is not None
        assert item.lifted_from.source_doc == CONVERSATION_ORIGIN
        # The source turn marker is recoverable.
        assert item.lifted_from.source_ac == "turn-2026-06-03-A"
    finally:
        tracker.close()


async def test_AC_INTK_PROPOSE_2_provenance_distinct_from_other_origins(tmp_path) -> None:
    work = WorkIntent(is_work=True, title="call the contractor", strength="clear")
    ext = FakeWorkIntentExtractor({"need to call the contractor back": work})
    tracker = fresh_tracker(tmp_path)
    try:
        proposal = await intake_turn(
            "need to call the contractor back",
            tracker,
            extractor=ext,
            claude_home=tmp_path / "home",
        )
        assert proposal is not None
        item = tracker.get(proposal.objective_id)
        # The origin marker is specifically "conversation" — not a doc path,
        # not a FIDRAFT / dev-queue marker.
        assert item.lifted_from.source_doc == "conversation"
    finally:
        tracker.close()
