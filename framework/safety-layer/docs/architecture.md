# Safety layer — architecture

**Status:** Built 2026-04-19. Binding proposal:
`../../docs/rebuild/components/safety-layer/proposal.md`.

This is the structural summary for future readers. For the decision
record, read the proposal.

## Shape

```
safety-layer/src/
├── action_class.py   — FrameworkFloorCategory enum (7 entries, sealed set)
├── ask_list.py       — AlwaysAskList Pydantic schema + duration parser
├── config.py         — SafetyConfig (money-threshold tunable with floor)
├── dangerous_op.py   — DangerousOpGate decision procedure
├── events.py         — Pydantic records + structural_hash(spec)
├── store.py          — SQLite (ask_decisions, kill_events, system_kill_state)
├── kill.py           — KillEngine: three-level dispatcher
├── notification.py   — SafetyChannel/SafetyNotifier (fail-closed)
├── observability.py  — OTel emission (no TracerProvider construction)
├── controller.py     — SafetyController: composed runtime
├── ipc_wiring.py     — register_safety_ipc: workspace-bootstrap glue
└── cli.py            — `pos kill ...` + `pos safety ...`
```

## Non-amendment discipline

The safety layer does not touch sealed components. It consumes:

| Sealed component     | Surfaces used                                           |
|----------------------|---------------------------------------------------------|
| scope-of-work        | `ScopeRuntime.cancel`, `ScopeRuntime.list`, `ScopeSpec` |
| orchestrator         | `pause_activation`, `resume_activation`, `request_stop`, `IPCServer.register` |
| primary-persona      | `OneOnOneChannel`, `ChannelKind`                        |
| observability-agg    | `trace.get_tracer("pos.safety_layer")` — no provider construction |

## IPC-wrap composition

The workspace bootstrap calls `register_safety_ipc(server, controller)`
AFTER the orchestrator has registered its default handlers. The
`server.register("activate_scope", wrapped)` call overrides the
orchestrator's handler. Inside the wrap: refuse-if-system-killed ->
check_gates -> forward to original handler.

## Gates

Two gates compose. Both are pure functions — no LLM inside the gate.

1. **Always-ask gate** fires on `action_class=<value>` constraint that
   matches the union `framework_floor ∪ workspace_additions`.
2. **Dangerous-op gate** fires on ANY of:
   - `reversibility_class == irreversible`
   - `action_class in dangerous_op_subset`
   - `budget.money_cents >= threshold`

Both gates look up `find_active_approval(structural_hash(spec))`. An
approval binds to the spec's content identity — any mutation invalidates
it (A14).

## structural_hash (builder's challenge of Eve-inference #7)

`ScopeSpec.structural_hash()` does not exist on `pos-v2` (grep
confirmed). The builder chose to implement the hash INSIDE safety-layer
as a standalone helper (`events.structural_hash(spec)`) that SHA-256s
the spec's canonical JSON. This is a pure consumer of the sealed
ScopeSpec; no amendment to scope-of-work.

## Fail-closed (ruling #5)

If no active OneOnOneChannel is reachable at gate-fire time, the
notifier returns False and the gate raises
`IPC_SAFETY_CHANNEL_UNAVAILABLE (-32043)`. No queue-and-fire. The scope
stays `proposed`. `pos safety status` surfaces pending asks.

## Kill switches

| Level   | Two-step?  | Time budget (p95) |
|---------|------------|-------------------|
| Scope   | No         | 500ms             |
| Session | No         | 2s                |
| System  | Yes (nonce)| 5s                |

System-kill is clean-exit (ruling #2): pause + cancel all + record
terminal state + `request_stop`. Next bootstrap's `activate_scope` wrap
refuses until `safety.clear_system_kill` runs.
