# Safety layer — architecture

**Status:** Built 2026-04-19.

This is the structural summary for future readers.

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

safety-layer/hooks/  — PreToolUse safety hooks (Wave 1 ECC absorption)
├── _secret_patterns.py     — 14-pattern ECC floor + B2 FILE patterns (migrated from bash_guard) + workspace-additions loader
├── secret_pattern_guard.py — AC.SECHK.1 + AC.SECHK.B2-MIGRATION (Bash/Edit/Write/MultiEdit content + Bash file-staging)
├── dangerous_flag_guard.py — AC.SECHK.2 (git push|commit --no-verify; git push --force protected-branch)
└── config_write_guard.py   — AC.SECHK.3 (.eslintrc / biome.json / .pre-commit-config.yaml / .git/config / root .gitignore)
```

## Hooks subsystem (Wave 1 ECC absorption, 2026-05-24)

Three PreToolUse hooks ship as part of the safety-layer component
(per D-SEC.HOOKS — security primitives are core-loam, always-on).
The hooks compose alongside (do NOT replace or modify) the
SafetyController + DangerousOpGate; they fire BEFORE the
orchestrator's `activate_scope` dispatch via Claude Code's
PreToolUse hook event.

| Hook                       | Matcher                          | What it blocks                                                                   |
|----------------------------|----------------------------------|----------------------------------------------------------------------------------|
| `secret_pattern_guard.py`  | `Bash\|Edit\|Write\|MultiEdit`   | 14-pattern ECC content floor (sk-..., ghp_..., AKIA..., etc.) + secret-FILE commits (B2 migration from bash_guard) |
| `dangerous_flag_guard.py`  | `Bash`                           | `git push --no-verify`, `git commit --no-verify`, `git push --force <protected-branch>` |
| `config_write_guard.py`    | `Edit\|Write\|MultiEdit`         | Writes to `.eslintrc{,.json,.js,.yaml,.cjs}`, `biome.json`, `.pre-commit-config.yaml`, `.git/config`, root `.gitignore` |

### Fail-open policy (D-SECHK.FAIL-OPEN)

Per the always-on rationale: real security is defense-in-depth and
loam's hooks are belt-not-suspenders. Failing closed on an internal
hook fault (regex engine error, malformed envelope) creates a worse
failure mode than the one being defended against (legitimate work
blocked for a self-inflicted reason). Each hook:

- Catches every internal exception at the top-level `try/except`
- Returns exit-0 + empty stdout (default-allow)
- Appends a structured NDJSON failure-log line to
  `<workspace>/.loam/safety-hooks.log`

### Toggle-off mechanism (D-SECHK.TOGGLE-GRANULARITY)

Two granularities:

- `LOAM_SAFETY_HOOKS=off` — disables all three hooks
- `LOAM_SAFETY_HOOKS_SECRET=off` — disables `secret_pattern_guard`
- `LOAM_SAFETY_HOOKS_DANGEROUS_FLAG=off` — disables `dangerous_flag_guard`
- `LOAM_SAFETY_HOOKS_CONFIG_WRITE=off` — disables `config_write_guard`

A toggled-off hook records the no-op in the NDJSON log so a later
audit can confirm it was actually disabled, not silently broken.

### Workspace-additions (D-SECHK.PATTERN-SET)

The secret-pattern hook's CONTENT pattern set is the ECC 14-pattern
floor + an additive workspace override at
`<workspace>/.loam/secret-patterns.yaml`. Schema:

```yaml
patterns:
  - name: workspace-internal-token
    regex: "internal-key-[A-Z0-9]{16}"
```

Additive only — the loader cannot remove framework-floor patterns.
Invalid regexes silently drop (fail-open at the loader); the floor
plus any valid additions ship as the effective pattern set.

The dangerous-flag hook's protected-branch set is the
`{main, master, pos-v2, production}` floor + an additive workspace
override at `<workspace>/.loam/protected-branches.yaml`. Schema:

```yaml
branches:
  - release-train
```

### Registration into workspace settings.json

The three hooks register into `<workspace>/.claude/settings.json`
via the existing `framework/hands-off-lifecycle/hooks/first_run_settings.py`
multi-contributor `merge_pre_tool_use` helper:

- `build_secret_pattern_guard_stanza(loam_root)` →
  `Bash|Edit|Write|MultiEdit` matcher
- `build_dangerous_flag_guard_stanza(loam_root)` → `Bash` matcher
- `build_config_write_guard_stanza(loam_root)` →
  `Edit|Write|MultiEdit` matcher
- `build_safety_layer_stanzas(loam_root)` → convenience helper
  returning all three in registration order

The three hooks compose alongside the existing pos-v2 PreToolUse
contributors (A2 objective-binding gate, A3 TDD-guard, A4
bash_guard / agent_guard) via matcher independence — Claude Code
only invokes hooks whose matcher matches the active tool name.

### Overlap with `plugins/dev-sdlc/hooks/bash_guard.py` (D-SECHK.OVERLAP)

Per the owner ruling on D-SECHK.OVERLAP (option B — partial absorb,
ratified 2026-05-24 via Telegrams 12310/12311): the B2 secret-FILE
detection MIGRATED from `bash_guard.py` to
`secret_pattern_guard.py`. `bash_guard.py` retains B1 (amend-in-
subagent, DEV-MODE), B3 (loam-amend-dry-run-failure, DEV-MODE), B4
(wrong-tree-write, DEV-MODE), B5 (blast-radius, UNIVERSAL). The
canonical secret-detection layer is now the safety-layer; the
universally-available B2 surface continues firing via the
safety-layer hook in ALL workspaces (was UNIVERSAL pre-migration).

Verified by AC.SECHK.B2-MIGRATION-{1,2,3}:

- MIGRATION-1: behavior parity (the same inputs that fired
  bash_guard's B2 now fire safety-layer's secret_pattern_guard)
- MIGRATION-2: no double-fire (bash_guard.evaluate() returns
  allow/no-op on the migrated inputs)
- MIGRATION-3: B1/B3/B4/B5 surfaces preserved (regression coverage
  via existing AC.BAG.2-7 tests)

## Non-amendment discipline

The safety layer does not touch sealed components. It consumes:

| Sealed component     | Surfaces used                                           |
|----------------------|---------------------------------------------------------|
| scope-of-work        | `ScopeRuntime.cancel`, `ScopeRuntime.list`, `ScopeSpec` |
| orchestrator         | `pause_activation`, `resume_activation`, `request_stop`, `IPCServer.register` |
| primary-persona      | `OneOnOneChannel`, `ChannelKind`                        |
| observability-agg    | `trace.get_tracer("loam.safety_layer")` — no provider construction |

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
