# scope-of-work

## What it does

`scope-of-work` is the named-unit-of-work primitive. Any work the
primary persona dispatches — a single tool call, a multi-turn
research run, a recurring scheduled task, a long-running
background scope — runs inside a named scope. The scope carries
the work's budget envelope, its observers (who needs to know when
it changes state), its escalation triggers (when does the persona
need to surface it to the user), and its event-sourced state
machine.

Two design preferences shape the component:

- **Event-sourced.** State changes are appended; the scope's
  history is replayable, queryable, and survives compaction.
- **FSM-shaped.** Allowed transitions are structural; "scope
  cannot move from cancelled to running without an explicit
  resume verb" is enforced by the FSM, not by prose.

Scope-of-work is the abstraction every other governance
component (cost, safety, reversibility, objective-tracker)
binds against. Without scope, the gates would have nothing to
attach budgets / classifications / objectives to.

## How to invoke

You do not normally invoke scope-of-work directly. Scopes are
created by the primary persona's dispatch path when a new unit
of work begins; they are observed by the persona's reporter
when the user asks "what's running?".

For operator inspection:

```bash
loam-cost ls                     # scopes via cost-governance's view
loam-observability filter --scope <id>   # scope's span series
```

A scope's metadata declares its budget envelope, its observers,
its escalation triggers, and the reversibility class for any
in-scope tool calls; plugin authors writing dispatchable
specialists declare these as part of the scope contribution.

## Observable surface

What you can `tail` / `cat` / `grep` to see the component working:

- **OTel spans.** `loam.scope_of_work.*` namespace. Scope
  creation emits `scope.create`; transitions emit
  `scope.transition` with from/to states; escalations emit
  `scope.escalate` with the trigger that fired.
- **Event store.** Per-workspace event-sourced log under the
  scope-of-work component's data area; replay is loss-free.
- **Active-scope view.** The orchestrator and observability
  aggregator both surface active scopes through their
  respective queries.
- **Greeting integration.** SessionStart greeting includes any
  in-flight scopes from the previous session that need
  attention; this is a scope-of-work consumer.

## Stable surfaces (for plugin authors)

Plugin authors register new scope kinds (a domain-specific
research scope, a recurring schedule scope) by declaring scope
metadata in their plugin contribution. The core scope FSM is
fixed at v0.1.0; new transitions or new states require a core
amendment.

For internal implementation detail see
[`framework/scope-of-work/README.md`](../../framework/scope-of-work/README.md).
