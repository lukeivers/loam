# API reference — scope-of-work

One page covering the complete public surface. All async methods take
keyword arguments where shown.

## Construction

```python
from scope_of_work import ScopeRuntime

rt = ScopeRuntime(
    db_path="./data/scope.db",                # SQLite WAL file
    pending_extension_dir="./data/pending",   # human-readable surface
    cross_process_poll_interval=0.25,         # seconds, for poll loops
)
# rt.close() on shutdown.
```

## Building a spec

```python
from scope_of_work import (
    ScopeSpec, Budget, BudgetAxis, BudgetExhaustionPolicy,
    Observer, ReversibilityClass, SuccessCriterion,
    BudgetThreshold, TimeElapsed, EventTypeTrigger,
    SuccessCriterionTrigger, ReversibilityTrigger,
    ParentClosePolicy,
)

spec = ScopeSpec(
    goal="research who introduced Aldermere clients to Nordic partners",
    constraints=("synthetic data only", "no email"),
    budget=Budget(
        time_seconds=900,
        tokens=10_000,
        money_cents=200,
        # All three default to request_extension; override per axis:
        tokens_policy=BudgetExhaustionPolicy.request_extension,
    ),
    reversibility_class=ReversibilityClass.fully_reversible,
    success_criteria=(
        SuccessCriterion(criterion_id="answers_question",
                         description="primary research question answered"),
    ),
    observers=(Observer(observer_id="eve"),),
    escalation_triggers=(
        BudgetThreshold(trigger_id="warn-tokens",
                        axis=BudgetAxis.tokens, threshold=2_000),
        TimeElapsed(trigger_id="t-cap", seconds=600),
    ),
    owner_persona="eve",
    parent_close_policy=ParentClosePolicy.TERMINATE,  # default
)
```

Missing any of the seven required fields raises `pydantic.ValidationError`
at construction.

## Lifecycle methods

| Method | Returns | Notes |
|---|---|---|
| `await rt.create(spec, *, scope_id=None, parent_scope_id=None)` | `ScopeProjection` | Creates in `proposed`. Auto-generates `scope_id` if omitted. |
| `await rt.start(scope_id)` | `ScopeProjection` | proposed → active; opens OTel `invoke_scope` span. |
| `await rt.pause(scope_id, reason=None)` | `ScopeProjection` | active → paused. |
| `await rt.resume(scope_id)` | `ScopeProjection` | paused → active. |
| `await rt.complete(scope_id, *, evaluations=None)` | `ScopeProjection` | active → completed. `evaluations` is `[(criterion_id, "met"|"not_met", note)]`. |
| `await rt.fail(scope_id, reason)` | `ScopeProjection` | active → failed. |
| `await rt.cancel(scope_id, reason=None)` | `ScopeProjection` | active → cancelled; cascades to children per their `parent_close_policy`. |

Illegal transitions raise `RuntimeError`.

## Budget methods

| Method | Returns | Notes |
|---|---|---|
| `await rt.debit(scope_id, *, input_tokens=0, output_tokens=0, money_cents=0, prompt_name=None, model=None, call_id=None)` | `ScopeProjection` | Records LLM usage. Auto-generates `call_id` if omitted. Emits a child OTel `chat {model}` span when model is given. |
| `await rt.refund(scope_id, call_id, *, input_tokens=None, output_tokens=None, money_cents=None, reason=None)` | `ScopeProjection` | Reverses a debit. Defaults to full refund. |
| `await rt.extend(scope_id, axis, amount)` | `ScopeProjection` | Grants additional budget on an axis. Auto-resumes a scope that was paused with a matching pending-extension request. |
| `await rt.reject(scope_id)` | `ScopeProjection` | Rejects a pending extension. Transitions to `completed` if any success criterion was met, else `cancelled`. |

## Observers and triggers

| Method | Returns | Notes |
|---|---|---|
| `await rt.add_observer(scope_id, observer)` | `ScopeProjection` | Auto-wires `Observer.callback_handle` if registered. |
| `await rt.remove_observer(scope_id, observer_id)` | `ScopeProjection` | Both add/remove are auditable events. |
| `await rt.evaluate_success_criterion(scope_id, *, criterion_id, result, note=None)` | `ScopeProjection` | Records an evaluation; may fire a `SuccessCriterionTrigger`. |
| `rt.subscribe(scope_id, callback)` | `None` | pyee subscription; callback receives the typed event. |
| `rt.subscribe_all(callback)` | `None` | Subscribe to every scope's events. |
| `rt.register_callback(handle, async_fn)` | `None` | Register a string-to-async-fn map for `Observer.callback_handle`. |

## Queries

| Method | Returns | Notes |
|---|---|---|
| `rt.get(scope_id)` | `ScopeProjection \| None` | Sync; reads cached projection. |
| `rt.list(*, states=None, parent_scope_id=None, owner_persona=None, include_pending_extension=None)` | `list[ScopeProjection]` | Sync filter; the data surface a future background-work monitor polls. |
| `rt.per_prompt_costs()` | `list[dict]` | v1.1 R12 — per-prompt name/model totals (with refunds applied). |

## Snapshots and upgrades

| Method | Returns | Notes |
|---|---|---|
| `rt.snapshot(target_path)` | `Path` | `VACUUM INTO` — consistent file copy of the SQLite DB. |
| `await rt.poll_external_events(last_event_id=0)` | `int` | Cross-process catch-up; fans events into pyee. |

For the upgrade-fidelity harness:

```python
from scope_of_work.upgrade import (
    capture_pre_upgrade, replay_post_upgrade, assert_no_drift,
)

probes = capture_pre_upgrade(rt.store, snapshot_to="./data/pre.db")
# ... apply upgrade ...
report = replay_post_upgrade(rt.store, probes)
assert_no_drift(report, threshold=0)
```

## Memory adapter

```python
from scope_of_work.adapter import RealScopeSourceAdapter

adapter = RealScopeSourceAdapter(rt)
# Inject into memory:
api = MemoryAPI(memory_store, scope_source=adapter)
```

The adapter satisfies memory's `ScopeSource` protocol; unknown scope
ids raise `KeyError` (the production behaviour memory has been
prepared for since the mock).

## ScopeProjection (read model)

The dataclass returned by every API call. Public fields:

```
scope_id, state, goal, constraints, reversibility_class,
owner_persona, parent_scope_id, parent_close_policy,
last_event_id, last_transition_at, pause_reason,
pending_extension_axis, children,
budget_tokens_remaining, budget_money_cents_remaining, budget_time_seconds_remaining,
budget_tokens_consumed,  budget_money_cents_consumed,  budget_time_seconds_elapsed,
success_criteria_met, success_criteria_not_met,
fired_trigger_ids,
```
