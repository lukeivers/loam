"""Adapter — observability aggregator.

Phase: before_orchestrator_start.
Role: register the shared TracerProvider so every later span emitter
(including bootstrap's own `pos.bootstrap.*` spans) lands in the
aggregator spool.

The sealed aggregator exposes `register_otel_provider(spool_path, ...)`
which calls `trace.set_tracer_provider(...)`. Late binding means
already-imported `trace.get_tracer(...)` proxies pick up the new
provider the first time they open a span.

Config: `observability.yaml` under host.config_dir, with keys:
    spool_path: str (default: `<workspace_root>/data/aggregator/spans.jsonl`)
    service_name: str (default: `pos`)
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import yaml

from ..spec import BaseContribution, ContributionMetadata, Phase


class ObservabilityAggregatorContribution(BaseContribution):
    metadata: ClassVar[ContributionMetadata] = ContributionMetadata(
        name="observability_aggregator",
        phase=Phase.before_orchestrator_start,
    )

    def contribute(self, host) -> None:
        from pos_observability_aggregator.ingest import register_otel_provider

        cfg_path = host.config_dir / "observability.yaml"
        cfg: dict = {}
        if cfg_path.exists():
            loaded = yaml.safe_load(cfg_path.read_text()) or {}
            if isinstance(loaded, dict):
                cfg = loaded

        spool_path = Path(
            cfg.get("spool_path")
            or str(host.workspace_root / "data" / "aggregator" / "spans.jsonl")
        ).expanduser()
        spool_path.parent.mkdir(parents=True, exist_ok=True)

        service_name = str(cfg.get("service_name") or "pos")
        provider, processor, exporter = register_otel_provider(
            spool_path,
            resource_attrs={"service.name": service_name},
        )
        host.observability_provider = (provider, processor, exporter)

        def _shutdown() -> None:
            try:
                processor.shutdown()
            except Exception:
                pass
            try:
                exporter.shutdown()
            except Exception:
                pass

        host.register_shutdown("observability_aggregator", _shutdown)
