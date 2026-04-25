# pOS v2 — personal OS, Claude-native

pos-v2 is a Claude-only personal operating system: a long-running
background process (the orchestrator) plus a semantic memory store,
a three-gate safety chain, a primary persona that translates your
natural-language intent into AI-effective execution, and a supervisor
that keeps the whole system healthy without you doing anything
beyond opening a Claude Code session.

## Status

Foundation-complete: twelve sealed components plus the
hands-off-lifecycle amendments. The full component status table lives
in the dev-mode tracker docs (DEV MODE only).

## What running a session looks like

1. Open a Claude Code session in this workspace.
2. First run: a single sentence reports what was scaffolded. Proceed.
3. Normal runs: your primary persona greets you with what needs
   attention — no "open the terminal and start the sidecar."
4. Close the session. Background work continues. The supervisor
   keeps services healthy; the loud-escalation channel tells you
   when something needs founder attention.

## Layout

```
docs/rebuild/         — research, proposals, briefs per sealed component
memory-system/        — semantic memory sidecar (FastAPI + Graphiti + Kuzu)
orchestrator/         — long-lived asyncio process, Unix-socket JSON-RPC
workspace-bootstrap/  — composition engine; twelve-adapter bundle
safety-layer/
reversibility-primitive/
cost-governance/
self-correction/      — the three-gate chain + self-correction loop
graceful-degradation/
objective-tracker/
scope-of-work/
primary-persona/      — runtime policy + primitives
observability-aggregator/
self-upgrade/         — infrastructure
hands-off-lifecycle/  — Amendment bundle: supervisor, staging/drain,
                        first-run scaffold, Claude Code SessionStart hook
```

## Hands-off lifecycle

Opening a Claude Code session in a fresh workspace scaffolds
`~/.pos/`, installs the memory-sidecar and orchestrator service
files, asks the service manager to bring them up, and emits one
confirmation sentence. Nothing else. Ongoing lifecycle concerns
(sidecar health, drain on recovery, config drift) are the
supervisor's problem, not yours — self-heal silently when possible,
escalate loudly via your primary-persona channel when not. Degraded
mode that silently stays degraded is a bug, not a satisfaction.

See `hands-off-lifecycle/README.md` for the amendment bundle's
full layout.

## Implementation

Python 3.13. Language/test/file conventions live in the DEV MODE
tracker docs.

## License and contributions

Personal-use software in heavy development. Not currently accepting
external contributions; rebuild rules live in the DEV MODE tracker
docs.
