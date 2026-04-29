"""Adapter — safety layer (outermost wrap at dispatch).

Phase: wrap_activate_scope. Registers AFTER reversibility and cost
so at dispatch time safety runs first.
"""

from __future__ import annotations

import logging
from typing import Any, ClassVar

from ..spec import BaseContribution, ContributionMetadata, Phase


_LOGGER = logging.getLogger(__name__)


class SafetyLayerContribution(BaseContribution):
    metadata: ClassVar[ContributionMetadata] = ContributionMetadata(
        name="safety_layer",
        phase=Phase.wrap_activate_scope,
        after=("reversibility_primitive",),
    )

    def contribute(self, host) -> None:
        from loam.safety_layer import (
            AlwaysAskList,
            DEFAULT_DANGEROUS_OP_SUBSET,
            DEFAULT_FRAMEWORK_FLOOR,
            SafetyConfig,
            SafetyController,
            SafetyNotifier,
            SafetyStore,
        )
        from loam.safety_layer.ipc_wiring import register_safety_ipc
        from loam.safety_layer.notification import SafetyChannel

        from ._channels import resolve_channel
        from ..workspace_paths import data_subdir

        server = host.require("ipc_server")
        scope_runtime = host.require("scope_runtime")
        orchestrator = host.require("orchestrator")

        store_path = data_subdir(host.workspace_root) / "safety" / "safety.sqlite"
        store_path.parent.mkdir(parents=True, exist_ok=True)
        store = SafetyStore(store_path)

        channel = resolve_channel(host, "safety", SafetyChannel)
        notifier = SafetyNotifier(channels=[channel])

        ask_list = AlwaysAskList(
            version=1,
            framework_floor=DEFAULT_FRAMEWORK_FLOOR,
            workspace_additions=(),
            dangerous_op_subset=DEFAULT_DANGEROUS_OP_SUBSET,
        )
        config = SafetyConfig()

        def _spec_resolver(scope_id: str):
            resolver = host.channel_registry.get("spec_resolver")
            if resolver is not None:
                return resolver(scope_id)
            proj = scope_runtime.get(scope_id)
            return getattr(proj, "spec", None) if proj is not None else None

        controller = SafetyController(
            scope_runtime=scope_runtime,
            orchestrator=orchestrator,
            store=store,
            ask_list=ask_list,
            config=config,
            notifier=notifier,
        )
        register_safety_ipc(
            server=server,
            controller=controller,
            spec_resolver=_spec_resolver,
        )
        host.safety_controller = controller

        # Expose the safety approval resolver so the reversibility
        # ActivationGate (registered earlier, but stored on its gate
        # object) can cross-reference active safety approvals via the
        # host. Reversibility captures this on its ActivationGate at
        # wire time from host.channel_registry, so the cross-link is
        # workspace-opt-in.
        host.channel_registry["safety_approval_resolver"] = (
            store.find_active_approval_for_spec_hash
            if hasattr(store, "find_active_approval_for_spec_hash")
            else None
        )

        def _shutdown() -> None:
            try:
                store.close()
            except Exception:
                # Amendment #26 — teardown CDC 2: surface exception via
                # logger.debug (no span in scope at adapter shutdown).
                _LOGGER.debug(
                    "safety_layer_adapter_shutdown_failed",
                    exc_info=True,
                )

        host.register_shutdown("safety_layer", _shutdown)
