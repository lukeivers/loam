# scope-of-work — pos-v2 scope/budget/lifecycle primitive

## Surface

The scope-of-work component is pos-v2's bounded-execution
primitive. Every persona-dispatched action that carries
budget, has acceptance criteria, or is owned by an observer
binds to a `ScopeSpec` via the `ScopeRuntime` runtime. The
spec captures: a goal, a set of constraints, a multi-axis
budget (time, tokens, money), reversibility class, success
criteria, observer identity, escalation triggers, and a
parent-close policy.

The scope-of-work primitive is the harness's structural
expression of ODD authoring: every spec carries
*objective + constraints + acceptance criteria* — the same
shape the persona's ODD-shaped-internal-model rule restates
internally.

## Inputs/outputs

**Construction.** `ScopeRuntime(db_path, pending_extension_dir,
cross_process_poll_interval)` — opens the SQLite WAL store
and the human-readable pending-extension surface.

**Spec required fields (seven).** `goal`, `constraints`,
`budget`, `reversibility_class`, `success_criteria`,
`observers`, `owner_persona`. Missing any raises
`pydantic.ValidationError` at construction.

**Lifecycle methods.** `create` (proposed), `start`
(proposed → active), `pause` (active → paused), `resume`
(paused → active), `complete` (active → completed),
`fail` (active → failed), `cancel` (active → cancelled
with cascade).

**Budget methods.** `debit` (records LLM usage; emits OTel
spans), `refund` (reverses a debit), `extend` (grants
additional budget; auto-resumes a paused-pending-extension
scope), `reject` (rejects pending extension; transitions to
completed-if-criterion-met or cancelled).

**Persistence.** SQLite WAL with cross-process polling.
Multiple processes can operate against the same scope DB;
the poll interval governs read-side latency on remote
mutations.

## Composition notes

scope-of-work composes with virtually every other harness
primitive:

- With **objective-tracker**: ScopeSpecs bind to objective
  records via the tracker's `register_objectives` call (per
  `pos-amend apply`'s schema-v2 `objectives` block).
- With **cost-governance**: budgets surface budget-line
  events that cost-governance subscribes to; fire-once
  warnings fire at named percentiles.
- With **session-resilient orchestrator**: the orchestrator
  binds to scopes via `bind_scope` / `activate_scope`; the
  IPC contract delivers progress updates across compaction.
- With **memory-system**: scope lifecycle events flow into
  graphiti via the Stop-hook learning-extraction subscriber.
- With **observability-aggregator**: every `start` /
  `debit` / `complete` emits OTel spans the awareness-block
  contributor surfaces.

The primary-persona binds plans and dispatches to scopes —
when the persona dispatches a background agent, the
dispatch is conceptually a `ScopeSpec` with a goal,
constraints, and acceptance criteria; scope-of-work makes
that binding structural.

## [user-intent phrasings]

- "I want this scoped"
- "give this a budget"
- "set acceptance criteria for..."
- "track this as a piece of work"
- "what's in flight right now?"
- "pause this until..."
- "extend the budget on..."
- "add this as an objective"

## Source

```
source_url: internal:framework/scope-of-work/docs/api-reference.md
source_fetch_ts: 2026-04-28T00:00:00Z
```
