# `/loop` — recurring or self-paced in-session execution

## Surface

The `/loop` skill runs a prompt or slash-command on a
recurring interval inside the current session. It is the
persona's reach for user requests shaped as "keep checking",
"poll every N minutes", or "run this on a cadence until I
stop you" — the cadence is session-bound, not cron-shaped.
Omitting the interval lets the model self-pace (the persona
picks the cadence based on the work shape).

`/loop` is not a scheduled-routine primitive — it stays
alive only while the session is open. For cross-session
recurring work, the persona reaches for `/schedule` instead.

## Inputs/outputs

**Trigger.** Invoked when the user wants to set up a
recurring task, poll for status, or run something repeatedly
on an interval — e.g. "check the deploy every 5 minutes",
"keep running /babysit-prs", "watch this until X
completes". Not for one-off tasks.

**Inputs.** The skill takes (interactively) the prompt or
slash-command to run plus the interval (optional — omit for
self-pacing). Cadence is wall-clock based.

**Outputs.** Per-iteration outputs are emitted into the
current session's chat surface. The user can interrupt the
loop at any time; the skill respects standard cancellation.

## Composition notes

`/loop` composes with **background-agent dispatch** — a
loop iteration may itself dispatch a background agent for
the per-iteration work (avoids blocking the main session
while the iteration runs). For long-iteration loops where
each cycle does substantive work, `/loop` + background-agent
+ stop-condition is the standard pattern.

`/loop` does **not** compose with `/schedule` — see the
schedule.md sibling note. The persona picks one based on
whether session lifetime is the right granularity (`/loop`)
or cron-shape across sessions is needed (`/schedule`).

`/loop` is the cadence sibling of `/goal` (see goal.md):
both keep Claude working across turns, but they halt on
different criteria. `/loop` keeps running until the model
(or the session) stops — the *iteration itself* is the work,
with no single success state to halt on. `/goal` halts the
instant a checkable goal predicate passes — the work is to
*reach a state*. The persona reaches for `/loop` when the
recurring check IS the task ("keep polling the deploy every
5 minutes") and for `/goal` when there is a definite success
predicate to drive toward and halt on ("keep working until
the build is green"). Siblings, not nestable.

`/loop` plus `Monitor` (the event-stream primitive) lets
the persona poll a background process's output stream until
a condition is met, rather than chaining shorter sleeps.

## [user-intent phrasings]

- "check the deploy every 5 minutes"
- "keep running this until X"
- "poll for status"
- "watch this on a cadence"
- "babysit the PR queue"
- "loop on this until done"
- "rerun this every minute and stop when..."

## Source

```
source_url: https://code.claude.com/docs/en/commands
source_fetch_ts: 2026-07-21T13:04:59Z
source_status: current
```
