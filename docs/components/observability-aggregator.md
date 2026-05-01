# observability-aggregator

## What it does

`observability-aggregator` is loam's single-user, local-first
trace store. Every other component emits OpenTelemetry spans
into the workspace's emission surface; the aggregator subscribes,
stores, and serves them. The user-facing value is "I want to know
what just happened" — what the persona did, why a refusal fired,
which scope consumed which budget — answerable with a query
against a local store, not by reading source.

Three query shapes are supported:

- **Structured queries** — typed filters over span attributes
  (scope id, time window, span name, tag).
- **Natural-language queries** — free-text questions against the
  span store; the aggregator routes them to a structured query
  internally.
- **CLI queries** — operator-facing one-line verbs for common
  inspections.

The store is **DuckDB** by default with a SQLite fallback for
hosts where DuckDB cannot run. Both are local, single-file, no
server.

## How to invoke

The aggregator runs as a workspace-supervised background process
launched by `hands-off-lifecycle` at first session. You do not
start it manually. The user-facing surface is the per-component
CLI:

```bash
loam-observability query <text>          # natural-language query
loam-observability filter --scope <id>   # structured query
loam-observability replay <scope-id>     # replay a scope's span
                                         # series (Reading A)
```

Plugin authors can subscribe to specific span classes by
contributing a subscriber to the aggregator; subscribers run
inside the aggregator's process and react to spans as they
arrive (an alert pipeline, a metric emitter, etc.).

## Observable surface

What you can `tail` / `cat` / `grep` to see the component working:

- **The local span store.** DuckDB or SQLite database in the
  workspace's data area. You can attach to it with a standard
  client and query directly if the aggregator's surface is not
  expressive enough.
- **OTel spans.** `loam.observability_aggregator.*` namespace —
  the aggregator emits its own spans about ingestion latency,
  query throughput, and replay state. Visible through its own
  query surface (eat your own dog food).
- **Replay output.** The replay verb writes the scope's span
  series to stdout in chronological order; useful when
  diagnosing a scope after the fact.
- **Retention behaviour.** The aggregator honours per-class
  retention policies (Reading A retention) so high-volume
  ephemeral spans expire while low-volume durable spans
  persist.

## Stable surfaces (for plugin authors)

Plugin authors emit OTel spans under their own
`loam.<plugin>.*` namespaces; the aggregator subscribes
automatically because its bootstrap registration covers the
workspace-wide span pipeline. Plugins that want to *consume*
spans (a metric exporter, an alert engine) register a subscriber
contribution.

For internal implementation detail see the component source under
`framework/observability-aggregator/`.
