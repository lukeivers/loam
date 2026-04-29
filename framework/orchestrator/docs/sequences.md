# Sequence Diagrams

## `bind_scope` activation flow

```
Session                Orchestrator              ObjectiveTracker       ScopeRuntime
   │                         │                          │                    │
   │ activate_scope          │                          │                    │
   │────────────────────────▶│                          │                    │
   │                         │ get(scope_id)            │                    │
   │                         │─────────────────────────────────────────────▶│
   │                         │◀─── scope (state=?) ────────────────────────│
   │                         │                          │                    │
   │                         │ state != proposed? ──▶ raise ScopeNotPending │
   │                         │ (→ IPC -32020)                                │
   │                         │                          │                    │
   │                         │ bind_scope               │                    │
   │                         │─────────────────────────▶│                    │
   │                         │                          │                    │
   │                         │            trace_to_root + ScopeBound event   │
   │                         │                          │                    │
   │                         │   UnresolvedObjectiveError│                   │
   │                         │  or OrphanRootError    ⟲ │                    │
   │                         │◀─────────────────────────│                    │
   │                         │                          │                    │
   │                         │ append(bind_refused)     │                    │
   │                         │ to local SQLite          │                    │
   │                         │ emit OTel span event     │                    │
   │◀─── 409 + cause_kind ───│                          │                    │
   │                         │                          │                    │
   │  ─── OR on success ───                                                   │
   │                         │ start(scope_id)          │                    │
   │                         │─────────────────────────────────────────────▶│
   │                         │◀─── scope active ────────────────────────────│
   │                         │                          │                    │
   │                         │ append(scope_activated) to local SQLite        │
   │                         │ emit loam.orchestrator.scope_activated span     │
   │◀─── 200 + binding ──────│                          │                    │
```

Test coverage: `test_d5_bind_scope.py` (7 tests).

## Compaction-restore flow

```
Session                        Orchestrator                 primary-persona
  │                                  │                              │
  │  PreCompact hook fires           │                              │
  │─ mark_precompact(session_id) ───▶│                              │
  │                                  │ append(compaction_flag_set)  │
  │                                  │ to local SQLite              │
  │◀─── {pending: true} ─────────────│                              │
  │                                  │                              │
  │   (compaction happens —          │                              │
  │    context is dropped)           │                              │
  │                                  │                              │
  │  next UserPromptSubmit           │                              │
  │─ consume_compaction ────────────▶│                              │
  │                                  │ compaction_flag_pending()?   │
  │                                  │                              │
  │                                  │ yes ─▶ build_survival_payload│
  │                                  │──────────────────────────────▶
  │                                  │   (contract, runtime.list,   │
  │                                  │    recent_corrections)       │
  │                                  │◀──── CompactionSurvivor ─────│
  │                                  │                              │
  │                                  │ append(compaction_restored)  │
  │                                  │ to local SQLite              │
  │                                  │ emit loam.orchestrator.       │
  │                                  │   compaction_restored span   │
  │◀── 5-item survival payload ──────│                              │
  │                                  │                              │
  │  (session re-injects persona     │                              │
  │   identity, authority boundary,  │                              │
  │   current scope context, pending │                              │
  │   decisions, recent corrections) │                              │
```

The flag is SQLite-backed, so if the orchestrator is restarted
between PreCompact and the next UserPromptSubmit (cron, crash,
reboot), the flag survives and restoration still fires. See
`test_d8_compaction_integration.py::test_compaction_flag_survives_restart_and_restores`.

The canonical five-item survival list:

1. `persona_identity`       — from loaded contract.yaml
2. `authority_boundary`     — from loaded contract.yaml
3. `current_scope_context`  — `scope_runtime.list()` active+paused
4. `pending_decisions`      — `scope_runtime.list(include_pending_extension=True)`
5. `recent_corrections`     — wired provider (memory-system)
