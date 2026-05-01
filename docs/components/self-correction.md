# self-correction

## What it does

`self-correction` is the four-part loop that fires after the
safety, cost, or reversibility gates refuse a tool call. Rather
than absorbing the refusal as "Claude failed," the loop walks
the persona through naming what was attempted, why the gate
fired, what the corrected approach is, and whether the
correction landed within the scope's remaining budget.

The four parts, in order:

1. **Acknowledge.** The refusal is recorded as a structured
   event, not paraphrased away.
2. **Diagnose.** The gate that fired is identified and its
   reason surfaced — a kill switch, an always-ask hold, a
   ceiling breach, an irreversibility classification.
3. **Correct.** The persona proposes a corrected approach
   that respects the gate's reason. If no corrected approach
   exists within scope, the loop halts and surfaces the
   block.
4. **Verify.** The corrected approach is checked against the
   same gate chain before re-attempting; a second refusal
   exits the loop and surfaces the obstacle for ruling.

The loop is structurally enforced — every refusal goes through
it — so refusals cannot accumulate silently as "tool failed,
moved on."

## How to invoke

The loop is invoked automatically by the dispatch wrapper when
any of the safety / cost / reversibility gates refuses. There
is no user-facing CLI verb; if you want to inspect the loop's
state directly, the component's audit log is the surface.

Operator inspection of the loop's history:

```bash
loam-correction ls              # list recent self-correction loops
loam-correction show <id>       # full transcript of one loop
```

## Observable surface

What you can `tail` / `cat` / `grep` to see the component working:

- **OTel spans.** `loam.self_correction.*` namespace. Each loop
  emits one `loop` span with child spans for `acknowledge`,
  `diagnose`, `correct`, `verify`.
- **Audit ledger.** Per-loop entries in a local SQLite store;
  the CLI's `show` verb reads it.
- **Halt surface.** When a loop halts (no corrected approach
  in scope, or second refusal during verify), the persona
  surfaces the halt to the user with the loop's transcript;
  the loop's halt event is written to the audit ledger and
  emitted as an OTel span the observability aggregator
  captures.

## Stable surfaces (for plugin authors)

Plugin authors writing new specialists do not need to do
anything special — the loop wraps every dispatch automatically.
If a plugin's specialist requires a custom diagnose or correct
step (e.g. a domain-specific reason class), it can contribute a
diagnoser or corrector to the loop's contribution registry.

For internal implementation detail see the component source under
`framework/self-correction/`.
