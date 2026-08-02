# `/schedule` — recurring scheduled remote agents

## Surface

The `/schedule` skill creates, updates, lists, and runs
scheduled remote agents (routines) that execute on a cron
schedule. It is the persona's first reach for any user
request shaped as "recurring task" or "do X every Y" — the
schedule is owner-managed cron-shape, not session-bound.

The skill also supports one-time scheduled runs ("run this
once at 3 pm", "remind me to check X tomorrow"), which the
skill internally implements as a degenerate single-fire
schedule.

## Inputs/outputs

**Trigger.** The skill is invoked when the user wants to
schedule a recurring remote agent, set up automated tasks,
create a cron job for Claude Code, or manage their scheduled
agents/routines. The persona invokes the skill via the
`Skill` tool with `skill="schedule"`.

**Inputs.** The user supplies (interactively, through the
skill's conversation): the cadence (cron-shaped, e.g. "every
weekday at 7 am"), the dispatch target (the prompt or scope
the scheduled agent runs), and any one-off vs recurring
selector. The skill manages the scheduling backend (claude.ai
hosted routine surface).

**Outputs.** A registered routine on the user's claude.ai
account. The routine fires per the cadence and produces a
remote-agent run. Outputs are visible via the skill's `list`
operation; per-run outputs flow through the routine's
configured channel (Telegram, in-app, etc.).

## Composition notes

`/schedule` composes naturally with **background-agent
dispatch** — a scheduled routine typically dispatches a
background agent for the actual work (research, summarise,
report). The persona's prompt-to-action shape for "daily
briefing" is: `/schedule` (the cadence) + background-agent
dispatch (the per-run scope) + Telegram or in-app delivery
(the channel).

`/schedule` does **not** compose with `/loop` — `/loop`
self-paces inside a session; `/schedule` runs cron-shaped
across sessions. They are siblings, not nestable. The
persona picks one based on whether the user wants
session-bound polling (`/loop`) or owner-managed cron
(`/schedule`).

`/schedule` runs against the user's cloud subscription, not
the local machine — it works while Claude Code is closed.

## [user-intent phrasings]

- "set me up to get a daily briefing"
- "remind me every weekday at 7 am to..."
- "send me a digest each morning"
- "do this thing every 12 hours"
- "make this a recurring task"
- "run this once at 3 pm"
- "schedule a check-in for tomorrow morning"
- "every Monday, summarise..."

## Source

```
source_url: https://code.claude.com/docs/en/routines
source_fetch_ts: 2026-08-02T12:59:20Z
source_status: current
```
