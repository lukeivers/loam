# Bootstrap-Registration Guide

The aggregator is wired into a pOS workspace via the orchestrator's `~/.loam/bootstrap.py` workspace-hook convention.

## Minimal bootstrap

Create `~/.loam/bootstrap.py`:

```python
from pos_observability_aggregator import AggregatorConfig
from pos_observability_aggregator.ingest import install_for_workspace

# Module-level so the pipeline keeps running for the orchestrator's lifetime.
_pipeline = None

def register(orchestrator):
    global _pipeline
    cfg = AggregatorConfig()    # defaults to ~/.loam/observability.duckdb
    _pipeline, _provider = install_for_workspace(cfg, start_pipeline=True)
    # _pipeline.stop() on shutdown is optional — daemon threads exit
    # with the process.
```

The orchestrator calls `register(self)` once at startup. From that point on:
- The global TracerProvider routes every component's spans through our exporter.
- The spool drainer + memory tailers run as daemon threads.
- `QueryAPI`, `NLPath`, and `pos obs` all have data to query.

## What `install_for_workspace` does

1. Creates `~/.loam/` if missing.
2. Opens (or creates) `~/.loam/observability.duckdb` with the canonical schema.
3. Installs a `TracerProvider` whose `BatchSpanProcessor` feeds the `AggregatorSpanExporter` (which writes to `~/.loam/spool.jsonl`).
4. Starts the spool drainer and the three memory tailers as daemon threads.
5. Returns `(pipeline, provider)` so the caller can stop them on shutdown if desired.

## Late-binding contract

Python OTel's `trace.get_tracer(name)` returns a `ProxyTracer` when no provider is installed. The proxy delegates to whatever provider is set on first span emission. This means:

- A sealed component can call `_TRACER = trace.get_tracer("pos.scope_of_work")` at module import time (before our bootstrap runs).
- Our bootstrap can call `set_tracer_provider(...)` later.
- The first span emitted from `_TRACER` after our `set_tracer_provider` call will route through our exporter.

The `test_pre_existing_proxy_tracer_picks_up_provider` test verifies this end-to-end. If a future component breaks late-binding (by binding a concrete tracer at the SDK level before our bootstrap runs), that test fails with a clear halt-and-signal diagnostic.

**Halt condition:** if you observe spans emitted from a sealed component NOT landing in the spool, check:
1. Was `install_for_workspace` called before any component's first span?
2. Has another piece of workspace code already called `set_tracer_provider`? OTel's `set_tracer_provider` Once-guards by default; the first call wins. Our bootstrap should be among the first.

## Configuration

```python
from pos_observability_aggregator import AggregatorConfig
from pos_observability_aggregator.config import RetentionConfig, IngestConfig

cfg = AggregatorConfig(
    base_dir="~/.loam",
    substrate="duckdb",                       # or "sqlite"
    db_path="~/.loam/observability.duckdb",    # optional override
    retention=RetentionConfig(
        full_fidelity_days=7,                 # 0-7d full
        daily_rollup_end_days=30,             # 7-30d daily + top-N raw
        monthly_rollup_end_days=365,          # 30-365d monthly
        audit_cutoff_days=None,               # None: keep yearly forever
        top_n_raw_per_day=20,                 # spans kept raw in 7-30d window
    ),
    ingest=IngestConfig(
        memory_sink_dir="./data/observability",
        spool_path=None,                      # default ~/.loam/obs_spool.jsonl
        batch_size=256,
        batch_interval_seconds=2.0,
        self_namespace_prefix="pos.aggregator",
    ),
)
```

Or load from YAML:

```python
cfg = AggregatorConfig.from_yaml("~/.loam/observability.yaml")
```

YAML format:
```yaml
observability:
  base_dir: "~/.loam"
  substrate: duckdb
  db_path: "~/.loam/observability.duckdb"
  retention:
    full_fidelity_days: 7
    daily_rollup_end_days: 30
    monthly_rollup_end_days: 365
    top_n_raw_per_day: 20
  ingest:
    memory_sink_dir: "./data/observability"
    batch_size: 256
    batch_interval_seconds: 2.0
```

## Shutdown

```python
def shutdown_workspace():
    if _pipeline is not None:
        _pipeline.stop()    # joins daemon threads with timeout
```

The OTel TracerProvider has its own lifecycle; calling `provider.shutdown()` flushes pending spans through the BatchSpanProcessor before the process exits. This is good practice but not strictly required — the spool will buffer anything in flight; the next start drains it.

## Verifying installation

After `register()` runs, dispatch one span and confirm it lands:

```python
from opentelemetry import trace
from pos_observability_aggregator import open_store
from pos_observability_aggregator.api import QueryAPI, SpanFilter

tracer = trace.get_tracer("pos.scope_of_work")
with tracer.start_as_current_span("install_smoke_test"):
    pass

# Wait for the BatchSpanProcessor to flush (default 2 seconds).
import time
time.sleep(3)

store = open_store(AggregatorConfig())
api = QueryAPI(store)
spans = api.find_spans(SpanFilter(name_exact="install_smoke_test"))
assert spans, "Bootstrap did not land smoke-test span — check timing"
```
