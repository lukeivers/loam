# Session-Resilient Orchestrator — Documentation Bundle

This directory is the bundled-documentation deliverable per v1.1 R4
plus the D10 measurement addendum.

Contents:

| File | What it covers |
|------|----------------|
| `architecture.md` | Process model, IPC, monitor-hosting, dispatch-layer, restart semantics. Architecture + component diagrams. |
| `sequences.md` | Sequence diagrams: `bind_scope` activation flow, compaction-restore flow. |
| `relationships.md` | What this component consumes (all four Phase 1 primitives) and what consumes it (session, graceful-degradation, observability aggregator). |
| `api-reference.md` | One-page IPC surface: every JSON-RPC method with params, result, and errors. |
| `operations.md` | How to install, measure, and uninstall the launchd user agent (per Luke's build-time ruling). |
| `measurement-launchd.md` | Results of the D2 measurement addendum (launchd auto-restart latency under SIGKILL / SIGSEGV / OOM-approx / rapid-crash). |
| `measurement-ipc-latency.md` | Results of the D4 measurement addendum (Unix-socket IPC p95 latency under representative workload). |

## Purpose

The orchestrator is pOS's one long-lived process. Before this
component, Phase 1 primitives (memory, scope-of-work, primary-persona
layer, objective tracker) existed as libraries. The orchestrator is
the surface that composes them into a running system:

- It hosts the primary-persona layer's background-work monitor
  coroutine.
- It enforces `bind_scope` at the dispatch layer (Luke's decision).
- It owns a small local SQLite for its own process-lifecycle state.
- It exposes a Unix-domain-socket JSON-RPC API so an interactive
  Claude session can attach as a peer process.
- It restarts cleanly via launchd on macOS and survives SIGKILL,
  reboots, API outages, and compaction events with no loss of
  authoritative state.

## Permitted runtime dependencies

Python stdlib + `pydantic` + `pyee` + `opentelemetry-api/sdk` + `PyYAML`.
Anything else is halt-and-signal per the dispatch brief.

## File-length disclaimer

Per STATE.md rule #9, the 200-line file rule is suspended for new pOS
until new-pOS standards are authored. `src/orchestrator.py` is the
single composition point; keeping the lifecycle, dispatch, IPC, and
compaction wiring co-located reads more cleanly than splitting them
into shard files whose only purpose is to satisfy an old Ruby rule.
