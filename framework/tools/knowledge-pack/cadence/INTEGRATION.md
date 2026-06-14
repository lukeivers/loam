# Pack-render cadence integration — REUSE Slice-1's binding (no second scheduler)

> **D-PUSH.4 / AC.CLP-PUSH-RENDER.6.** The knowledge-pack render is an
> ADDED STEP in Slice-1's existing cadence binding — it owns no scheduler
> of its own. There is no new cloud routine, no new launchd agent, no new
> cron. The pack-render runs in the SAME tick as the capability-refresh,
> right after it, so the pack is always rendered from a freshly-refreshed
> corpus.

## Why no second scheduler

Slice 1 already ships (activation owner-gated) a scheduled binding that
runs `framework/tools/capability-refresh/` ~weekly:
`framework/tools/capability-refresh/cadence/` (the cloud routine spec +
the launchd fallback). A SECOND scheduler for the pack render would be the
duplicate-primitive anti-pattern the program's own doctrine flags (Lens 1
+ `tool-selection-rubric`). The pack render CONSUMES the refresh's output —
they are the same cadence, one after the other.

## The added step

The pack-render step is `scripts/run-cadence-step.sh` in THIS component. It
renders the pack deterministically and emits a PENDING curation-gate
record. It performs NO public action (the pack stages in-repo; publish is
S4c ⛔OWNER) and records NO gate pass (a curator does that before publish).

### Cloud routine (primary) — one added line in the existing prompt

The Slice-1 routine prompt (`capability-refresh-weekly`,
`framework/tools/capability-refresh/cadence/routine-spec.md`) gains one
step after the refresh commit:

```
5. Render the knowledge pack from the freshly-refreshed corpus:
   ./framework/tools/knowledge-pack/scripts/run-cadence-step.sh
   (equivalently: PYTHONPATH=framework/tools/knowledge-pack/src
    python3 -m knowledge_pack render)
   This stages the pack under docs/capability-corpus/.pack with a PENDING
   gate record. Do NOT publish — the public repo + push are owner-gated
   (S4c). Commit any docs/capability-corpus/.pack/ changes locally with
   the refresh commit.
```

No new routine is created; the existing weekly routine triggers the step.

### launchd fallback — same binding, added step

The launchd fallback already invokes
`framework/tools/capability-refresh/scripts/run-cadence.sh`. Operators who
want the pack rendered in the same tick chain the step in their own
activation wrapper (the launchd agent's `ProgramArguments` already point at
a single runner; the pack-render step is appended there). This component
introduces no plist of its own.

## Manual run (always allowed; no activation)

```
cd /Users/lukeivers/loam && ./framework/tools/knowledge-pack/scripts/run-cadence-step.sh
```

or, without staging into the default `.pack` path:

```
PYTHONPATH=framework/tools/knowledge-pack/src python3 -m knowledge_pack \
    render --pack-root /tmp/knowledge-pack-preview
```

## Activation status

Activation of any persistent unattended automation remains OWNER-GATED
(the Slice-1 cadence binding is itself spec-only until the owner switches
it on). This integration adds NO new activation surface — it rides the
Slice-1 binding the owner activates.
