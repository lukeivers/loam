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

"""AC.INTK.PROPOSE.1 — one plain proposal + a real `proposed`-state placed item.

A detected work item is surfaced as exactly ONE concise plain-language proposal
carrying NO internal identifier / lifecycle enum / slug / path, and is backed by
a real work item created in the store's ``proposed`` state with the candidate
stream/project placement. The proposal is NOT a silent commit to ``active``."""

from __future__ import annotations

from _helpers_intake import FakeWorkIntentExtractor, fresh_tracker

from loam.objective_tracker.spec import ObjectiveStatus
from loam.primary_persona.keep_pace.intake import WorkIntent, intake_turn

# Internal-vocab fragments that must NEVER appear in a proposal line.
_FORBIDDEN_VOCAB = ("obj-", "proposed", "active", "objective_id", "tagged_streams",
                    "belongs_to_project", "sqlite", "/", "LiftedFrom")


async def test_AC_INTK_PROPOSE_1_one_plain_line_no_internal_vocab(tmp_path) -> None:
    work = WorkIntent(
        is_work=True, title="Q3 budget review", candidate_project="Money",
        strength="clear",
    )
    ext = FakeWorkIntentExtractor({"don't let me forget the Q3 budget review": work})
    tracker = fresh_tracker(tmp_path)
    try:
        proposal = await intake_turn(
            "don't let me forget the Q3 budget review",
            tracker,
            extractor=ext,
            claude_home=tmp_path / "home",
        )
        assert proposal is not None
        # Exactly one line, plain-language, the title present.
        assert proposal.line.count("\n") == 0
        assert "Q3 budget review" in proposal.line
        # No internal vocabulary leaks into the user-facing line.
        for frag in _FORBIDDEN_VOCAB:
            assert frag not in proposal.line, f"internal vocab leaked: {frag!r}"
    finally:
        tracker.close()


async def test_AC_INTK_PROPOSE_1_backed_by_proposed_item_with_placement(tmp_path) -> None:
    work = WorkIntent(
        is_work=True, title="rental paperwork", candidate_stream="house",
        candidate_project="Home", strength="clear",
    )
    ext = FakeWorkIntentExtractor({"get the rental paperwork going": work})
    tracker = fresh_tracker(tmp_path)
    try:
        proposal = await intake_turn(
            "get the rental paperwork going",
            tracker,
            extractor=ext,
            claude_home=tmp_path / "home",
        )
        assert proposal is not None
        # A REAL item exists, in `proposed` (NOT active — not a silent commit).
        item = tracker.get(proposal.objective_id)
        assert item is not None
        assert item.status == ObjectiveStatus.proposed
        assert item.goal == "rental paperwork"
        # The candidate placement was carried onto the item.
        assert item.belongs_to_project == "Home"
        assert "house" in item.tagged_streams
    finally:
        tracker.close()


async def test_AC_INTK_PROPOSE_1_not_silent_active_commit(tmp_path) -> None:
    work = WorkIntent(is_work=True, title="renew the registration", strength="clear")
    ext = FakeWorkIntentExtractor({"I have to renew the registration": work})
    tracker = fresh_tracker(tmp_path)
    try:
        proposal = await intake_turn(
            "I have to renew the registration",
            tracker,
            extractor=ext,
            claude_home=tmp_path / "home",
        )
        assert proposal is not None
        # The single item is proposed, never auto-active.
        items = list(tracker.query_projection_view())
        assert len(items) == 1
        assert items[0].status == ObjectiveStatus.proposed
    finally:
        tracker.close()
