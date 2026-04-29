"""Adapter — self-correction (consumer, not a new wrap).

Phase: after_orchestrator_ready.
Role: construct the SelfCorrectionController and subscribe to
ScopeRuntime.emitter.on('*') for scope-failure triggers. Also
registers the three IPC methods (record_part, report_review_verdict,
user_reported). Does NOT install an activate_scope wrap — per
self-correction's brief, it is a consumer of the three-gate chain.
"""

from __future__ import annotations

import logging
from typing import ClassVar

from ..spec import BaseContribution, ContributionMetadata, Phase


_LOGGER = logging.getLogger(__name__)


class SelfCorrectionContribution(BaseContribution):
    metadata: ClassVar[ContributionMetadata] = ContributionMetadata(
        name="self_correction",
        phase=Phase.after_orchestrator_ready,
        after=("safety_layer",),  # ensures the gate chain is in place.
    )

    def contribute(self, host) -> None:
        from loam.self_correction import (
            CorrectionChannel,
            CorrectionNotifier,
            CorrectionStore,
            ScopeFailurePyeeSubscriber,
            SelfCorrectionController,
            default_config,
            register_self_correction_ipc,
        )

        from ._channels import resolve_channel
        from ..workspace_paths import data_subdir

        server = host.require("ipc_server")
        scope_runtime = host.require("scope_runtime")

        store_path = (
            data_subdir(host.workspace_root) / "self_correction" / "correction.sqlite"
        )
        store_path.parent.mkdir(parents=True, exist_ok=True)
        store = CorrectionStore(store_path)
        config = default_config()

        channel = resolve_channel(host, "self_correction", CorrectionChannel)
        notifier = CorrectionNotifier(channels=[channel])

        controller = SelfCorrectionController(
            store=store,
            config=config,
            notifier=notifier,
        )
        register_self_correction_ipc(server=server, controller=controller)

        # Subscribe to scope failure events.
        async def _handler(trigger):
            await controller.intake(trigger)

        subscriber = ScopeFailurePyeeSubscriber(handler=_handler)
        subscriber.subscribe(scope_runtime)

        host.self_correction_controller = controller

        def _shutdown() -> None:
            try:
                store.close()
            except Exception:
                # Amendment #26 — teardown CDC 2: surface exception via
                # logger.debug (no span in scope at adapter shutdown).
                _LOGGER.debug(
                    "self_correction_adapter_shutdown_failed",
                    exc_info=True,
                )

        host.register_shutdown("self_correction", _shutdown)
