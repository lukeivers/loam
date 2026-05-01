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

"""CR16 — same-class cascade: 3 in 600s trips escalation regardless of depth."""

from __future__ import annotations

import time

from loam.self_correction import (
    CorrectionConfig,
    CorrectionEpisode,
    CorrectionStore,
    EpisodeState,
    SelfCorrectionController,
    build_trigger_from_user_report,
)
from loam.self_correction.bounds import same_class_cascade_check
from loam.self_correction.spec import CorrectionTrigger, TriggerSource, iso_now


def _seed_same_class(
    store: CorrectionStore, *, count: int, failure_class: str
) -> None:
    for i in range(count):
        trig_id = f"trig-sc-{failure_class}-{i}"
        store.insert_trigger(
            CorrectionTrigger(
                trigger_id=trig_id,
                source=TriggerSource.scope_failure,
            )
        )
        store.insert_episode(
            CorrectionEpisode(
                episode_id=f"ep-sc-{failure_class}-{i}",
                trigger_id=trig_id,
                correction_scope_id=f"scope-sc-{failure_class}-{i}",
                failure_class=failure_class,
                state=EpisodeState.running,
                opened_at=iso_now(),
            )
        )


def test_CR16_one_existing_does_not_trip(store: CorrectionStore) -> None:
    # Threshold=3: refuse when opening this would make it the 3rd.
    # One existing → this would be the 2nd → no trip.
    cfg = CorrectionConfig(cascade_window_seconds=600, cascade_threshold=3)
    _seed_same_class(store, count=1, failure_class="bad_route")
    trip = same_class_cascade_check(
        failure_class="bad_route", store=store, config=cfg
    )
    assert trip is None


def test_CR16_at_threshold_trips(store: CorrectionStore) -> None:
    cfg = CorrectionConfig(cascade_window_seconds=600, cascade_threshold=3)
    # Two existing → this would be the 3rd, meeting threshold → trip.
    # This is the conservative interpretation: we refuse the correction
    # that would reach the threshold, rather than letting it open and
    # triggering on the 4th. The cascade signal fires early.
    _seed_same_class(store, count=2, failure_class="bad_route")
    trip = same_class_cascade_check(
        failure_class="bad_route", store=store, config=cfg
    )
    assert trip is not None
    assert trip.failure_class == "bad_route"
    assert trip.window_count == 3


async def test_CR16_intake_refuses_on_cascade_and_notifies(
    controller: SelfCorrectionController, channel_and_inbox
) -> None:
    _, inbox = channel_and_inbox
    # Seed 2 existing episodes of the same class. The incoming would
    # be the 3rd, which trips threshold=3.
    _seed_same_class(controller.store, count=2, failure_class="user_reported")

    tr = build_trigger_from_user_report(
        description="distinct text to avoid dedup",
        related_scope_id="scope-new",
        reporter="eve",
    )
    # failure_class_hint is "user_reported" → matches the seeded class.
    result = await controller.intake(tr)
    assert result is not None
    assert result.state == EpisodeState.escalated
    assert result.refusal_reason == "same_class_cascade"
    assert len(inbox) == 1


def test_CR16_old_episodes_fall_out_of_window(store: CorrectionStore) -> None:
    cfg = CorrectionConfig(cascade_window_seconds=1, cascade_threshold=3)
    _seed_same_class(store, count=5, failure_class="oldclass")
    # Sleep past the 1s window so seeded episodes fall out.
    time.sleep(1.1)
    trip = same_class_cascade_check(
        failure_class="oldclass", store=store, config=cfg
    )
    assert trip is None
