"""Adapter — dormancy (declaration-only).

Phase: before_orchestrator_start.

Per Luke's ruling #4, the dormancy component is constructed by the
orchestrator's startup path (or bound to it via another adapter).
This adapter is declaration-only so Phase 4+ contributions can
reference `dormancy` in their `after=` declarations. It does not
itself re-construct the DegradationComponent.
"""

from __future__ import annotations

from typing import ClassVar

from ..spec import BaseContribution, ContributionMetadata, Phase


class DormancyContribution(BaseContribution):
    metadata: ClassVar[ContributionMetadata] = ContributionMetadata(
        name="dormancy",
        phase=Phase.before_orchestrator_start,
    )

    def contribute(self, host) -> None:
        return None
