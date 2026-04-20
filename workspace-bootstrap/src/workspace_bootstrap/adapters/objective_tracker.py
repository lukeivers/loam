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
