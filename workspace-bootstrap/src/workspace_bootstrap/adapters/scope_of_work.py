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
