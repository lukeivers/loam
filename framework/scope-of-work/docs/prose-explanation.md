# Scope-of-work primitive — what it is, why it exists

**For:** anyone (technical or not) who needs to understand what this
component does and how it fits into the rest of pOS.

## What

A "scope of work" is the unit pOS uses to bound any piece of
autonomous work. Every time the system commits to doing something —
researching a question, drafting a document, sending an email,
ingesting a memory — it does so inside a scope. The scope answers
seven questions before the work begins:

1. **What is the goal?** (the outcome the work is trying to produce)
2. **What are the constraints?** (things the work must not do)
3. **What is the budget?** (caps on time, tokens, and money)
4. **How reversible is the action?** (fully reversible / compensatable
   / irreversible)
5. **What does success look like?** (named criteria, evaluable at the
   end)
6. **Who is observing?** (subscribers who get notified of events)
7. **What can escalate this?** (declarative triggers that pause or
   halt the work if a condition is met)

If any of those seven questions is unanswered, the scope cannot be
created. That single gate is what makes the rest of the system
trustworthy: nothing autonomous runs without bounds.

## Why

The pOS objectives spec calls for a system that can be left to do
work, with the user trusting it to fail safely and predictably. That
trust depends on three properties this primitive provides:

- **Cost is bounded.** A budget is declared up front; if the work
  exceeds it, the scope pauses (the default) and asks for an
  extension. It does not silently keep spending.
- **Every action is auditable.** Every state change, every LLM call,
  every observer mutation is a typed event in an append-only log. You
  can replay any scope's history and reconstruct exactly what it did
  and why.
- **Failure is structural, not silent.** Triggers fire on declared
  conditions (budget thresholds, time elapsed, irreversible
  activation, success criterion not met) and escalate the scope —
  surfacing the failure rather than burying it.

Together these are the foundation pOS builds the rest of the safety
layer, cost governance, observability, and self-correction loop on.

## Lifecycle

A scope moves through a small set of states:

```
proposed → active → {paused ↔ active}* → {completed | failed | cancelled | escalated}
```

- **proposed** — created, not yet running.
- **active** — work is underway; budget time accumulates.
- **paused** — work is suspended (manual pause, throttle policy, or
  pending an extension request).
- **completed** — work finished; success criteria evaluated.
- **failed** — work stopped due to error; reason recorded.
- **cancelled** — work halted by user or by a parent scope.
- **escalated** — a trigger fired or a `halt_and_signal` budget
  policy hit its cap; the scope is awaiting human resolution.

Transitions are validated; an illegal transition (e.g. completed →
active) raises rather than silently misbehaving.

## Three decisions Luke made

These are baked into the defaults; per-scope override is available.

1. **Budget exhaustion default: request extension.** When any axis
   (time, tokens, money) runs out, the scope pauses, writes a
   pending-extension file and an event, and waits indefinitely for
   `extend()` or `reject()`. It does not silently halt or keep
   spending.
2. **Parent-close default: TERMINATE.** Cancelling a parent scope
   immediately cancels active children. (Children may declare
   ABANDON or REQUEST_CANCEL instead.)
3. **No separate prototyping round.** Cross-process cascade latency,
   trigger evaluation cost, and refund semantics are folded into the
   full build with halt-on-deviation as the safety valve.

## What this primitive does NOT do

- It does **not** dispatch LLM calls itself. The caller dispatches; the
  scope debits the resulting token usage via the `debit()` API.
- It does **not** decide whether an action should be reversible. The
  scope declares a class; the safety layer (future component)
  enforces preferences.
- It does **not** carry persona content. pOS core ships zero personas;
  scopes have an `owner_persona` string that points at workspace-
  supplied persona content.
- It does **not** know about specific consumers. Memory, observability,
  cost governance, primary persona loader — all subscribe via the
  pyee emitter and OTel emission. None are assumed to exist when this
  primitive ships.

## Where to start reading the code

- `src/spec.py` — the seven-field `ScopeSpec` and supporting types.
- `src/runtime.py` — the orchestrator (`ScopeRuntime`); start here
  for the public API.
- `src/store.py` — SQLite WAL event log + projection cache.
- `src/projection.py` — the deterministic event → state projector
  (the foundation for upgrade-fidelity replay).
- `src/triggers.py` — evaluation logic for declarative triggers.
- `src/observability.py` — OTel span/event emission.
- `src/adapter.py` — the 10-line `RealScopeSourceAdapter` that
  retires memory's `MockScopeSource`.
- `src/upgrade.py` — D7 upgrade-fidelity probe harness.

## When to use what

- **Need to bound a piece of autonomous work?** Create a scope with
  `await runtime.create(spec, parent_scope_id=...)` and call
  `await runtime.start(scope_id)`.
- **Made an LLM call?** Tell the scope: `await runtime.debit(...)`.
- **The call failed?** Refund: `await runtime.refund(call_id, ...)`.
- **Want to know what's running?** `runtime.list(states=[ScopeState.active])`
  — see the relationship map for how the future background-work
  monitor will use this.
- **Want to receive events?** `runtime.subscribe(scope_id, callback)`.
