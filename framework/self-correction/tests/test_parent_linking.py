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

"""CR17 — parent_correction_id linking at episode creation."""

from __future__ import annotations

from loam.self_correction import (
    CorrectionEpisode,
    CorrectionStore,
    EpisodeState,
    SelfCorrectionController,
    build_trigger_from_user_report,
)
from loam.self_correction.spec import CorrectionTrigger, TriggerSource


async def test_CR17_parent_correction_id_persists_on_episode(
    controller: SelfCorrectionController,
) -> None:
    # Seed an ancestor episode.
    controller.store.insert_trigger(
        CorrectionTrigger(
            trigger_id="trig-parent", source=TriggerSource.user_reported
        )
    )
    parent_ep = CorrectionEpisode(
        episode_id="ep-parent",
        trigger_id="trig-parent",
        correction_scope_id="scope-parent",
        failure_class="p_class",
        state=EpisodeState.running,
    )
    controller.store.insert_episode(parent_ep)

    # Open a child with parent linkage.
    tr = build_trigger_from_user_report(
        description="child correction",
        related_scope_id=None,
        reporter="eve",
    )
    result = await controller.intake(tr, parent_correction_id="ep-parent")
    assert result is not None

    # Stored episode carries parent linkage.
    child = controller.store.get_episode(result.episode_id)
    assert child is not None
    assert child.parent_correction_id == "ep-parent"


async def test_CR17_no_parent_when_none(
    controller: SelfCorrectionController,
) -> None:
    tr = build_trigger_from_user_report(
        description="top-level", related_scope_id=None, reporter="eve"
    )
    result = await controller.intake(tr)
    assert result is not None
    ep = controller.store.get_episode(result.episode_id)
    assert ep.parent_correction_id is None
