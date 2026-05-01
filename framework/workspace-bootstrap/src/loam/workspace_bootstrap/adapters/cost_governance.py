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

import logging
from typing import Any, ClassVar

from ..spec import BaseContribution, ContributionMetadata, Phase


_LOGGER = logging.getLogger(__name__)


class CostGovernanceContribution(BaseContribution):
    metadata: ClassVar[ContributionMetadata] = ContributionMetadata(
        name="cost_governance",
        phase=Phase.wrap_activate_scope,
        # After observability so all gate spans land in the aggregator.
        after=("observability_aggregator",),
    )

    def contribute(self, host) -> None:
        from loam.cost_governance import (
            CostLedger,
            CostNotifier,
            CostStore,
            default_config,
            register_cost_governance_ipc,
        )
        from loam.cost_governance.controller import CostController
        from loam.cost_governance.notification import CostChannel

        from ._channels import resolve_channel
        from ..workspace_paths import data_subdir

        server = host.require("ipc_server")
        scope_runtime = host.require("scope_runtime")

        store_path = data_subdir(host.workspace_root) / "cost" / "cost.sqlite"
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
                # Amendment #26 — teardown CDC 2: surface exception via
                # logger.debug (no span in scope at adapter shutdown).
                _LOGGER.debug(
                    "cost_governance_adapter_shutdown_failed",
                    exc_info=True,
                )

        host.register_shutdown("cost_governance", _shutdown)
