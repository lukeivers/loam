# Relationships

## Consumed (hard dependencies — all Phase 1)

| Component | Public API the orchestrator uses | Why |
|-----------|----------------------------------|-----|
| `scope_of_work.ScopeRuntime` | `create`, `start`, `get`, `list`, `subscribe_all`, `emitter`, `poll_external_events` | Authoritative scope state; the monitor's upstream emitter; the `scope_runtime.start` half of activation |
| `objective_tracker.ObjectiveTracker` | `create`, `bind_scope`, `subscribe_scope_emitter` | Dispatch-layer `bind_scope` enforcement; auto-evaluation of ScopeSuccessCriterion from scope events |
| `primary_persona.BackgroundWorkMonitor` | `start`, `stop`, `on_user_prompt` | Awareness block for every UserPromptSubmit; hosted in-process (Luke's decision) |
| `primary_persona.LoadedPersona` + `compaction.build_survival_payload` | `consume_compaction` restoration | Five-item canonical survival list from authoritative sources |

No amendments are made to any Phase 1 component. Every integration
goes through documented public APIs. Phase 1 test counts remain
unchanged:

- scope-of-work: 77 passed, 1 skipped
- objective-tracker: 86 passed
- primary-persona: 101 passed

## Consumed by (soft dependencies — future)

| Component | How it consumes the orchestrator | Status |
|-----------|----------------------------------|--------|
| Interactive Claude session (peer process) | Unix-socket JSON-RPC: `ping`, `status`, `awareness`, `activate_scope`, `mark_precompact`, `consume_compaction` | Integration contract shipped in D3/D4/D5/D8; session-side hook implementation is workspace code |
| Graceful-degradation component (next Phase 2) | `pause_activation(reason)` / `resume_activation()` hooks | Hooks exposed in D5/D7; the component that calls them is a separate build |
| Observability aggregator (later Phase 2) | OTel spans/events emitted by orchestrator operations | Emissions shipped in D9 (A1 correction: succeeds with no consumer) |
| Self-upgrade framework (later Phase 2) | orchestrator's local SQLite participates in pOS-wide upgrade-fidelity story | v1.1 R1 probe shipped in D6 |

## Workspace contract

`~/.loam/bootstrap.py` — workspace-authored file exposing:

```python
def register(orchestrator) -> None:
    """Wire callbacks, set the loaded persona, register the recent-
    corrections provider, add scope observers. The orchestrator is
    the single argument; accept it and use its public methods."""
```

pOS core defines the contract. The workspace authors the file.

On missing or erroring bootstrap the orchestrator refuses to start
(exit code 2 / 3). Luke's ruling — fail-closed matches the primary-
persona loader.
