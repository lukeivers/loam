"""Adapter — cost governance (innermost wrap at dispatch).

Phase: wrap_activate_scope.
Registration order (per sealed integration test
`cost-governance/tests/test_ipc_wrap_composition.py`):

    cost FIRST → reversibility SECOND → safety THIRD → orig_activate

Because each wrap captures the prior handler as `orig_activate`,
registering cost first means at dispatch time cost runs innermost —
right before the orchestrator's original `activate_scope`.

Note: proposal §3.2 listed `after=safety_layer` on cost. Verifying
against the sealed integration test shows the inverse is required
(cost registers FIRST). Implemented per the sealed code.
"""

from __future__ import annotations

from typing import Any, ClassVar

from ..spec import BaseContribution, ContributionMetadata, Phase


class CostGovernanceContribution(BaseContribution):
    metadata: ClassVar[ContributionMetadata] = ContributionMetadata(
        name="cost_governance",
        phase=Phase.wrap_activate_scope,
        # After observability so all gate spans land in the aggregator.
        after=("observability_aggregator",),
    )

    def contribute(self, host) -> None:
        from cost_governance import (
            CostLedger,
            CostNotifier,
            CostStore,
            default_config,
            register_cost_governance_ipc,
        )
        from cost_governance.controller import CostController
        from cost_governance.notification import CostChannel

        from ._channels import resolve_channel

        server = host.require("ipc_server")
        scope_runtime = host.require("scope_runtime")

        store_path = host.workspace_root / "data" / "cost" / "cost.sqlite"
        store_path.parent.mkdir(parents=True, exist_ok=True)
        store = CostStore(store_path)
        config = default_config()

        channel = resolve_channel(host, "cost", CostChannel)
        notifier = CostNotifier(channels=[channel])

        def _spec_resolver(scope_id: str):
            # The scope-of-work runtime stores ScopeSpec in the
            # pending-extension directory. The resolver looks up the
            # in-memory projection for an active scope; tests wire a
            # custom resolver via host.
            resolver = host.channel_registry.get("spec_resolver")
            if resolver is not None:
                return resolver(scope_id)
            proj = scope_runtime.get(scope_id)
            return getattr(proj, "spec", None) if proj is not None else None

        controller = CostController.build(
            store=store,
            config=config,
            scope_runtime=scope_runtime,
            notifier=notifier,
        )
        register_cost_governance_ipc(
            server=server,
            ledger=controller.ledger,
            spec_resolver=_spec_resolver,
        )
        host.cost_controller = controller

        def _shutdown() -> None:
            try:
                store.close()
            except Exception:
                pass

        host.register_shutdown("cost_governance", _shutdown)
