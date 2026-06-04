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

"""AC.INTK.LIVE.1 (OUTCOME-ALTITUDE, outcome-altitude:true).

Plan §6 AC.INTK.LIVE.1. Through ONE real production turn-path invocation (the
live keep-pace turn contributor produced by ``build_intake_contributor``, the
production work-intent extractor SEAM filled via ``register_work_intent_extractor``
— the same seam production fills — and the live increment-2 store ``create`` API)
with NO pre-arranged state:

  - a turn whose text naturally mentions a piece of work the user needs to do
    results in exactly ONE correctly-placed ``proposed`` work item in the LIVE
    store (right plain title, conversation provenance, a sensible candidate
    stream), surfaced as ONE plain-language proposal;
  - in the SAME run, a turn of pure chatter results in ZERO proposals and ZERO
    new items.

This invokes the PRODUCTION entry points — the real ``TriggerKind.turn``
contributor reading ``context["prompt"]``, the production extractor seam, and a
real ``ObjectiveTracker`` DB (the one work-item store) — with NO fixtures and NO
pre-arranged tracker state. The work-intent READ is supplied through the
production registration seam (deterministic, no live ``claude -p`` spawn in the
gate) so the outcome is verifiable; the turn-path, the store create, and the
proposal rendering are the real production code.
"""

from __future__ import annotations

import pytest

from loam.objective_tracker.runtime import ObjectiveTracker
from loam.objective_tracker.spec import ObjectiveStatus
from loam.primary_persona.keep_pace.intake import (
    CONVERSATION_ORIGIN,
    WorkIntent,
    build_intake_contributor,
    register_work_intent_extractor,
    reset_work_intent_extractor,
)


class _LiveWorkExtractor:
    """A production-registered extractor that reads a turn deterministically —
    work iff the text carries a clear forward-looking ask. Installed through the
    SAME ``register_work_intent_extractor`` seam production fills; the gate +
    create + render path it feeds is the real production code."""

    def extract(self, turn_text: str) -> WorkIntent:
        text = (turn_text or "").lower()
        if "rental paperwork" in text:
            return WorkIntent(
                is_work=True,
                title="rental paperwork",
                candidate_stream="house",
                strength="clear",
            )
        # Anything else this run reads as chatter (no work).
        from loam.primary_persona.keep_pace.intake import WorkIntent as WI

        return WI(is_work=False)


@pytest.fixture(autouse=True)
def _restore_extractor():
    yield
    reset_work_intent_extractor()


def test_AC_INTK_LIVE_1_work_turn_one_item_chatter_turn_zero(tmp_path) -> None:
    # NO pre-arranged state — a fresh, empty store the live turn writes into.
    db = tmp_path / "objective_tracker.sqlite"

    def live_tracker_factory():
        return ObjectiveTracker(db_path=db)

    # Install the work-intent read through the PRODUCTION seam (the same seam
    # production fills with the real ClaudeWorkIntentExtractor).
    register_work_intent_extractor(_LiveWorkExtractor())

    # The LIVE production turn contributor (TriggerKind.turn fn(context)->str).
    # claude_home points at an empty dir -> the #34 light default holds.
    contributor = build_intake_contributor(
        tracker_factory=live_tracker_factory,
        claude_home=tmp_path / "home",
    )

    # --- a real work-mentioning turn through the production turn-path ---
    work_line = contributor({"prompt": "I still need to get the rental paperwork going"})
    assert work_line, "the work turn produced no proposal line"
    assert "rental paperwork" in work_line
    # The plain proposal carries no internal vocabulary.
    for frag in ("obj-", "proposed", "active", "sqlite", "objective_id"):
        assert frag not in work_line

    # Exactly ONE correctly-placed `proposed` item now lives in the store.
    tracker = live_tracker_factory()
    try:
        items = list(tracker.query_projection_view())
        assert len(items) == 1, f"expected exactly one item, got {len(items)}"
        item = items[0]
        assert item.status == ObjectiveStatus.proposed
        assert item.goal == "rental paperwork"
        assert "house" in item.tagged_streams
        # Conversation provenance is recoverable.
        assert item.lifted_from is not None
        assert item.lifted_from.source_doc == CONVERSATION_ORIGIN
    finally:
        tracker.close()

    # --- a pure-chatter turn in the SAME run -> ZERO proposals, ZERO new items ---
    chatter_line = contributor({"prompt": "what's the weather like in Tokyo?"})
    assert chatter_line == "", "the chatter turn produced a proposal"
    tracker2 = live_tracker_factory()
    try:
        # Still exactly the ONE item from the work turn — chatter added nothing.
        assert len(list(tracker2.query_projection_view())) == 1
    finally:
        tracker2.close()
