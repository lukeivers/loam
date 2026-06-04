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

"""AC.INTK.CONFIRM.1 — confirm→active, dismiss→abandoned, ignore→no-renag.

A plain-language confirmation of a live proposal promotes the proposed item to
``active``; a dismissal abandons it; an unacted proposal does not re-surface /
re-nag on subsequent turns. All over the store's existing transitions."""

from __future__ import annotations

from _helpers_intake import FakeWorkIntentExtractor, fresh_tracker

from loam.objective_tracker.spec import ObjectiveStatus
from loam.primary_persona.keep_pace.intake import (
    WorkIntent,
    confirm_proposal,
    dismiss_proposal,
    intake_turn,
)


async def test_AC_INTK_CONFIRM_1_confirm_promotes_to_active(tmp_path) -> None:
    work = WorkIntent(is_work=True, title="file the permit", strength="clear")
    ext = FakeWorkIntentExtractor({"I need to file the permit": work})
    tracker = fresh_tracker(tmp_path)
    try:
        proposal = await intake_turn(
            "I need to file the permit", tracker,
            extractor=ext, claude_home=tmp_path / "home",
        )
        assert proposal is not None
        promoted = await confirm_proposal(tracker, proposal.objective_id)
        assert promoted.status == ObjectiveStatus.active
        # It is now a real tracked item the lenses render.
        item = tracker.get(proposal.objective_id)
        assert item.status == ObjectiveStatus.active
    finally:
        tracker.close()


async def test_AC_INTK_CONFIRM_1_dismiss_abandons(tmp_path) -> None:
    work = WorkIntent(is_work=True, title="repaint the fence", strength="clear")
    ext = FakeWorkIntentExtractor({"maybe repaint the fence sometime": work})
    tracker = fresh_tracker(tmp_path)
    try:
        proposal = await intake_turn(
            "maybe repaint the fence sometime", tracker,
            extractor=ext, claude_home=tmp_path / "home",
        )
        assert proposal is not None
        abandoned = await dismiss_proposal(tracker, proposal.objective_id)
        assert abandoned.status == ObjectiveStatus.abandoned
        item = tracker.get(proposal.objective_id)
        assert item.status == ObjectiveStatus.abandoned
    finally:
        tracker.close()


async def test_AC_INTK_CONFIRM_1_ignored_proposal_does_not_renag(tmp_path) -> None:
    # A proposal is made and IGNORED (no confirm, no dismiss). A subsequent
    # IDENTICAL re-mention does NOT produce a second proposal — the still-open
    # `proposed` item dedups it (no re-nag, no pile-up).
    work = WorkIntent(is_work=True, title="rental paperwork", strength="clear")
    ext = FakeWorkIntentExtractor(
        {"I need to do the rental paperwork": work}
    )
    tracker = fresh_tracker(tmp_path)
    try:
        first = await intake_turn(
            "I need to do the rental paperwork", tracker,
            extractor=ext, claude_home=tmp_path / "home",
        )
        assert first is not None  # proposed, then ignored.
        # Same turn again on a later turn — no second proposal.
        second = await intake_turn(
            "I need to do the rental paperwork", tracker,
            extractor=ext, claude_home=tmp_path / "home",
        )
        assert second is None, "an ignored proposal re-nagged on re-mention"
        # Still exactly ONE item, still proposed (no pile).
        items = list(tracker.query_projection_view())
        assert len(items) == 1
        assert items[0].status == ObjectiveStatus.proposed
    finally:
        tracker.close()
