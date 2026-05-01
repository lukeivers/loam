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

"""Adapter — scope-of-work (declaration-only).

Phase: before_orchestrator_start.
Role: register the name `scope_of_work` in the ordering DAG so Phase
4+ contributions can declare `after=("scope_of_work",)`. The
ScopeRuntime itself is constructed inside `Orchestrator._startup()`
(Luke's ruling #4); this adapter does NOT re-construct it. The host's
`scope_runtime` attribute is populated by the primary_persona adapter
from the started orchestrator.

Declaration-only means `contribute()` is a no-op.
"""

from __future__ import annotations

from typing import ClassVar

from ..spec import BaseContribution, ContributionMetadata, Phase


class ScopeOfWorkContribution(BaseContribution):
    metadata: ClassVar[ContributionMetadata] = ContributionMetadata(
        name="scope_of_work",
        phase=Phase.before_orchestrator_start,
    )

    def contribute(self, host) -> None:
        # Declaration-only — the orchestrator constructs ScopeRuntime
        # inside its _startup(). This adapter exists so the name is a
        # valid ordering-DAG participant.
        return None
