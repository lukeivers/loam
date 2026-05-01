# reversibility-primitive

## What it does

`reversibility-primitive` classifies every tool call into one of
three reversibility classes and binds compensations where
appropriate, so a failure or rollback decision later in a scope
can undo what was done without bespoke per-tool unwind logic.

The three classes:

- **fully reversible** — the tool's effect is recoverable from
  state available at call time (a file edit captures the
  pre-edit content; a database transaction is in flight; a
  scheduling action can be cancelled).
- **compensatable** — not directly reversible, but a
  compensating action exists (a sent message can be followed by
  a correction; a created resource can be deleted; a changed
  setting can be reverted).
- **irreversible** — the action cannot be undone (an external
  notification has fired, a payment has settled, a public
  artefact has been published). The primitive surfaces these
  before they happen so the persona can confirm.

## How to invoke

You do not invoke the primitive directly. It is wired by the
dispatch wrapper into the **PreToolUse** chain, where each tool
call is classified and (where applicable) bound to its
compensation. The persona's dispatch path always passes through
this gate; ad-hoc tool use inside a Claude Code session also
passes through it because the hook is workspace-level.

The per-component CLI gives operators an interface to the
compensation ledger and rollback path:

```bash
loam-reversibility ls           # list tracked compensations
loam-reversibility show <id>    # inspect a specific compensation
loam-rollback <scope-id>        # rollback every reversible action in a scope
```

The classification table is maintained as part of the component;
plugin authors contributing new specialists declare each tool
call's reversibility class as part of the scope's metadata.

## Observable surface

What you can `tail` / `cat` / `grep` to see the component working:

- **OTel spans.** `loam.reversibility.*` namespace. Each
  classification emits a `classify` span; each compensation
  binding emits a `bind` span; rollback runs emit `rollback`
  spans listing the compensations executed.
- **Compensation ledger.** Per-scope compensations stored in a
  local SQLite table; the CLI's `show` verb reads it.
- **Irreversibility surface.** `loam.reversibility.irreversible.*`
  spans fire when an irreversible class is detected; the
  primary persona consumes these and surfaces the operation
  for explicit ruling before allowing the call.
- **Path-choice telemetry.** Aggregate metrics on which
  reversibility class is chosen for which tool families;
  visible through the observability aggregator's structured
  queries.

## Stable surfaces (for plugin authors)

Plugin authors register tool classifications via a contribution
to the primitive's classification table. Custom compensation
shapes (a tool whose compensation is itself a multi-step scope,
say) can be expressed as a compensation contribution; the
rollback runtime composes them into the scope's rollback plan.

For internal implementation detail see the component source under
`framework/reversibility-primitive/`.
