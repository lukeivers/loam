"""CostController composes ledger + store + notifier + rollup.

Single construction site for cost governance. The workspace bootstrap
builds a `CostController`, then calls `register_cost_governance_ipc`
with it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from scope_of_work import ScopeRuntime

from .config import CostConfig
from .ledger import CostLedger, DispatchFn, SessionResolver
from .notification import CostNotifier
from .rollup import RollupTask
from .store import CostStore


@dataclass
class CostController:
    """Top-level cost-governance runtime.

    Constructed by the workspace bootstrap; passed to
    `register_cost_governance_ipc` to install the innermost wrap.
    """

    store: CostStore
    config: CostConfig
    ledger: CostLedger
    rollup_task: RollupTask
    notifier: CostNotifier | None

    @classmethod
    def build(
        cls,
        *,
        store: CostStore,
        config: CostConfig,
        scope_runtime: ScopeRuntime,
        notifier: CostNotifier | None = None,
        session_resolver: SessionResolver | None = None,
        dispatch_fn: DispatchFn | None = None,
        reservation_retention_days: int = 30,
        session_retention_days: int = 365,
    ) -> "CostController":
        ledger = CostLedger(
            store=store,
            config=config,
            notifier=notifier,
            session_resolver=session_resolver,
            dispatch_fn=dispatch_fn,
        )
        ledger.subscribe(scope_runtime)
        rollup_task = RollupTask(
            store=store,
            config=config,
            reservation_retention_days=reservation_retention_days,
            session_retention_days=session_retention_days,
        )
        return cls(
            store=store,
            config=config,
            ledger=ledger,
            rollup_task=rollup_task,
            notifier=notifier,
        )
