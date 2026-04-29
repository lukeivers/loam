"""Adapter — primary persona loader + orchestrator bootstrap.

Phase: before_orchestrator_start (runs AFTER observability_aggregator
so the persona-loading spans land in the aggregator).

Role (per Luke's ruling #4): the orchestrator constructs the
BackgroundWorkMonitor inside its own `_startup()`; this adapter
constructs the Orchestrator itself, invokes `_startup()`, and exposes
the constructed attributes on the host.

This adapter is the bridge from "before-phase" to "wrap-phase": by
the time it finishes, `host.orchestrator`, `host.ipc_server`,
`host.scope_runtime`, `host.objective_tracker`, and `host.monitor`
are populated. The wrap-phase adapters (cost → reversibility → safety)
read them off the host.

The persona itself is loaded from `host.config_dir/persona/` when
that directory exists; tests can skip persona loading by omitting it.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, ClassVar

import yaml

from ..spec import BaseContribution, ContributionMetadata, Phase


_LOGGER = logging.getLogger(__name__)


class PrimaryPersonaContribution(BaseContribution):
    metadata: ClassVar[ContributionMetadata] = ContributionMetadata(
        name="primary_persona",
        phase=Phase.before_orchestrator_start,
        after=("observability_aggregator",),
    )

    async def contribute(self, host) -> None:
        from loam.orchestrator import Orchestrator
        from loam.orchestrator.config import OrchestratorConfig, load_config

        from ..workspace_paths import pos_subdir

        # Load orchestrator config. Priority:
        #   1. `orchestrator.yaml` under host.config_dir (if present)
        #   2. OrchestratorConfig with root_dir = pos_subdir(workspace_root)
        #      = ``<workspace>/workspace/.pos`` post-D.2
        #
        # Amendment #7: orchestrator no longer self-loads bootstrap.py,
        # so no ``require_bootstrap=False`` disambiguator is needed
        # (and the field itself was removed from ``OrchestratorConfig``).
        cfg_path = host.config_dir / "orchestrator.yaml"
        if cfg_path.exists():
            config = load_config(cfg_path)
        else:
            config = OrchestratorConfig(
                root_dir=pos_subdir(host.workspace_root),
            )
        config.ensure_dirs()

        orch = Orchestrator(config)
        # Kick off orchestrator startup — this registers the stock
        # `activate_scope` IPC handler that the wrap-phase adapters
        # will compose over.
        await orch._startup()

        host.orchestrator = orch
        host.ipc_server = orch.ipc_server
        host.scope_runtime = orch.scope_runtime
        host.objective_tracker = orch.objective_tracker
        host.monitor = orch.monitor

        # Optional persona load. If a persona directory is present,
        # load it and bind to orch.set_loaded_persona() so compaction
        # restore has access.
        persona_dir = host.config_dir / "persona"
        if persona_dir.exists() and persona_dir.is_dir():
            from loam.primary_persona import PersonaLoader

            loader = PersonaLoader()
            loaded = loader.load(persona_dir)
            host.loaded_persona = loaded
            orch.set_loaded_persona(loaded)

        async def _shutdown() -> None:
            try:
                orch.request_stop()
                await orch._shutdown(clean=False)
                orch.close()
            except Exception:
                # Amendment #26 — teardown CDC 2: surface exception via
                # logger.debug (no span in scope at adapter shutdown).
                _LOGGER.debug(
                    "primary_persona_adapter_shutdown_failed",
                    exc_info=True,
                )

        host.register_shutdown("primary_persona", _shutdown)
