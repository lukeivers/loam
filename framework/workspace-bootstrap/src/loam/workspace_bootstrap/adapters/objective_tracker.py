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

"""Adapter — objective-tracker (declaration-only).

Phase: before_orchestrator_start. Declaration-only per Luke's ruling
#4. The ObjectiveTracker is constructed inside
`Orchestrator._startup()`; the host surface exposes it after the
orchestrator starts (via the primary_persona adapter).
"""

from __future__ import annotations

from typing import ClassVar

from ..spec import BaseContribution, ContributionMetadata, Phase


class ObjectiveTrackerContribution(BaseContribution):
    metadata: ClassVar[ContributionMetadata] = ContributionMetadata(
        name="objective_tracker",
        phase=Phase.before_orchestrator_start,
    )

    def contribute(self, host) -> None:
        return None
