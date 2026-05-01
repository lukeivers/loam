# cost-governance

## What it does

`cost-governance` is loam's per-scope budget primitive. Every
scope-of-work declares an envelope — tokens, wall time, money —
and the cost component activates the envelope at scope start,
tracks consumption as the scope runs, warns at 80% of any
ceiling, and refuses tool calls that would exceed a ceiling.

Two motivating concerns drive the design:

- **Token / time / money discipline.** Long-running AI work
  drifts toward unbounded spend if no structural floor catches
  it. The cost layer is that floor.
- **Drift detection.** A scope that consumes its envelope much
  faster (or slower) than expected is signal: something
  unexpected is happening. The cost layer flags drift so the
  primary persona surfaces it instead of silently absorbing it.

## How to invoke

You do not normally invoke cost-governance directly — it is
activated by the dispatch wrapper every time a scope starts. The
relevant Claude Code seam is **PreToolUse**: every tool call
inside a scope's lifetime checks the scope's remaining budget;
calls that would breach refuse before reaching the tool.

The per-component CLI lets operators inspect and act on cost
state:

```bash
loam-cost ls                    # list active scopes + budget consumption
loam-cost show <scope-id>       # full ledger entries for one scope
loam-cost cap <scope-id> --tokens 100000   # set a hard cap mid-run
```

Scope authors set ceilings declaratively in the scope's
metadata; runtime activation lifts ceilings from declaration to
enforcement.

## Observable surface

What you can `tail` / `cat` / `grep` to see the component working:

- **OTel spans.** `loam.cost_governance.*` namespace. Activation
  emits a `scope.activate` span; each tool consumption emits
  `scope.consume`; refusals emit `scope.refuse` with the breached
  ceiling and the requested vs available cost.
- **Sidecar ledger.** Per-scope ledger entries written to a local
  SQLite store; the per-component CLI's `show` verb queries it.
- **Drift events.** `loam.cost_governance.drift.*` spans fire
  when consumption velocity deviates from the scope's expected
  burn rate; visible alongside the `scope.consume` series so you
  can correlate.
- **80% warning surface.** When any ceiling crosses 80%, the
  layer emits a structured warning the primary persona surfaces
  in the conversation; the warning is also written to the
  workspace's audit ledger for after-the-fact review.

## Stable surfaces (for plugin authors)

Plugin authors implementing a new specialist or background work
declare their scope's envelope in the scope metadata; the cost
layer activates and tracks it without further wiring. Custom cost
classes (e.g. a cloud-API rate ceiling, a hardware-power ceiling)
can be contributed through the component's adapter contract.

For internal implementation detail see the component source under
`framework/cost-governance/`.
