"""Adapter — reversibility primitive (middle wrap at dispatch).

Phase: wrap_activate_scope. Registers AFTER cost so at dispatch time
reversibility runs between safety (outermost) and cost (innermost).
"""

from __future__ import annotations

import logging
from typing import Any, ClassVar

from ..spec import BaseContribution, ContributionMetadata, Phase


_LOGGER = logging.getLogger(__name__)


class ReversibilityPrimitiveContribution(BaseContribution):
    metadata: ClassVar[ContributionMetadata] = ContributionMetadata(
        name="reversibility_primitive",
        phase=Phase.wrap_activate_scope,
        after=("cost_governance",),
    )

    def contribute(self, host) -> None:
        from reversibility_primitive import (
            ReversibilityController,
            ReversibilityStore,
            RollbackNotifier,
            register_reversibility_ipc,
        )
        from reversibility_primitive.notification import ReversibilityChannel

        from ._channels import resolve_channel
        from ..workspace_paths import data_subdir

        server = host.require("ipc_server")
        scope_runtime = host.require("scope_runtime")

        store_path = data_subdir(host.workspace_root) / "reversibility" / "rev.sqlite"
        store_path.parent.mkdir(parents=True, exist_ok=True)
        store = ReversibilityStore(store_path)

        channel = resolve_channel(host, "reversibility", ReversibilityChannel)
        notifier = RollbackNotifier(channels=[channel])

        # Optional — wire safety approval resolver if safety has
        # registered one on the host. Safety registers AFTER
        # reversibility, so in practice this is None at wire time and
        # the ActivationGate permits the class-dispatch refusal check
        # to fall through. Workspaces that want cross-gate linkage
        # override via host.channel_registry.
        safety_approval_resolver = host.channel_registry.get(
            "safety_approval_resolver"
        )

        def _spec_resolver(scope_id: str):
            resolver = host.channel_registry.get("spec_resolver")
            if resolver is not None:
                return resolver(scope_id)
            proj = scope_runtime.get(scope_id)
            return getattr(proj, "spec", None) if proj is not None else None

        controller = ReversibilityController(
            store=store,
            scope_runtime=scope_runtime,
            notifier=notifier,
            safety_approval_resolver=safety_approval_resolver,
        )
        register_reversibility_ipc(
            server=server,
            store=controller.store,
            gate=controller.gate,
            rollback_runtime=controller.rollback_runtime,
            spec_resolver=_spec_resolver,
        )
        host.reversibility_controller = controller

        def _shutdown() -> None:
            try:
                store.close()
            except Exception:
                # Amendment #26 — teardown CDC 2: surface exception via
                # logger.debug (no span in scope at adapter shutdown).
                _LOGGER.debug(
                    "reversibility_primitive_adapter_shutdown_failed",
                    exc_info=True,
                )

        host.register_shutdown("reversibility_primitive", _shutdown)
