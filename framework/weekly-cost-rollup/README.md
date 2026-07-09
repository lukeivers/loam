# loam weekly cost roll-up (WS-A5)

Once a week, one channel message in three sections:

1. **This machine's weekly Claude cap %** — read from the SEALED
   `usage-window-guard` `seven_day` window (import-only compose). On an unreadable
   cap the section names the categorical reason and carries **no** number.
2. **Top-3 projects by Claude tokens** — a **proxy**, ranked from the local
   `~/.claude/projects` transcripts. It is *not* dollars: a flat subscription has
   no per-project invoice (stream 04 §1c). The label
   `proxy — ranks consumption, not billing-grade` is always present.
3. **Metered-model spend month-to-date** — Vercel AI Gateway. A **named absence**
   until owner decision D1 (gateway signup) lands.

A missing source is a **named** section, never a silently dropped one.

## Why a transcript parser and not `ccusage`

The plan cites adopting `ccusage`. It does run (`npx -y ccusage@latest`), but it
groups usage only by date / month / week / session — its JSON carries a session
UUID and no cwd/project path, so it cannot answer "top-3 **projects** by tokens".
This reads the transcript files ccusage reads (`~/.claude/projects/<encoded-cwd>/
<session>.jsonl`) directly, with the two correctness properties a naive sum
misses: **dedup** on `(message.id, requestId)` (resumed/compacted sessions
re-emit the same message) and a weekly **timestamp window** (this is a weekly
burn signal, not an all-time total). The token source is injectable, so a future
project-aware attribution tool is a config swap.

## Run

```
python -m loam.weekly_cost_rollup                     # deliver to stdout
python -m loam.weekly_cost_rollup --notify-cmd CMD    # pipe the message to CMD's stdin
```

`run_rollup()` called with no arguments exercises the full production path: the
real sealed usage probe, the real transcript parser, the (not-yet-configured)
gateway source, and stdout delivery.

## Schedule

`loam.weekly_cost_rollup.install.install(...)` renders + writes a **weekly**
launchd LaunchAgent (`StartCalendarInterval`, Monday 09:00 by default; `RunAtLoad`;
no `KeepAlive`) that survives a session ending. The operator runs `launchctl load`
to activate it. It writes its own plist file (`com.loam.weekly-cost-rollup.plist`)
and never touches `.claude/settings.json`.

## Channel

Channel-agnostic (H-3): loam never imports the workspace channel module. Delivery
is an injected `notify_fn` (reused from WS-A1); the launchd job bridges to a
workspace poster via `--notify-cmd` (message piped on stdin).
