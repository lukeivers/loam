---
description: "When the persona needs durable cross-session scheduling on macOS — work that must fire on a schedule and survive Claude session restarts, machine reboots, and `/clear` — author a launchd plist under `~/Library/LaunchAgents/`. launchd is the right primitive for genuinely persistent recurring work: weekly audits, daily snapshots, cross-session reminders, anything where session-scoped CronCreate (despite its `durable: true` flag) does NOT persist. Use when: a weekly job must survive any number of Claude sessions, a daily snapshot fires regardless of whether Claude is open, periodic maintenance unaffected by session boundaries. Composes with `cron-create` (session-bound vs cross-session) and `schedule-wakeup` (one-shot vs recurring durable)."
---

# launchd-plist

Durable cross-session recurring scheduling on macOS via a plist
under `~/Library/LaunchAgents/`.

## When to load me

- Persona needs work to fire on a schedule across Claude session
  restarts, machine reboots, and `/clear`.
- Persona is about to use CronCreate's `durable: true` flag for
  genuinely durable work — that flag does NOT achieve cross-
  session persistence (empirical finding pos3 task #77,
  2026-05-14). launchd is the right primitive.
- Persona is on macOS and the work is recurring (weekly audit,
  daily snapshot, hourly health check).
- Persona needs the schedule to survive `--bare` calls,
  permission resets, plugin reloads.

## What the primitive does

A launchd plist registered under `~/Library/LaunchAgents/` is a
user-level scheduled job managed by macOS itself. `launchctl
load` registers it; `launchctl unload` removes it. On machine
reboot, user login, or schedule trigger, launchd fires the
specified program (typically `claude -p <prompt>` or a shell
script that ends in a claude call).

Compared to CronCreate: launchd is OS-managed and persistent;
CronCreate is harness-managed and session-scoped. Compared to
ScheduleWakeup: launchd is recurring across sessions;
ScheduleWakeup is one-shot within a session. launchd is the only
primitive on this list that survives Claude session boundaries.

Reference plist shape (from pos3/Library/LaunchAgents/):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.loam.weekly-audit</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/local/bin/claude</string>
    <string>-p</string>
    <string>Run the weekly audit and write the report.</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key><integer>1</integer>
    <key>Hour</key><integer>9</integer>
    <key>Minute</key><integer>0</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>/tmp/com.loam.weekly-audit.out</string>
  <key>StandardErrorPath</key>
  <string>/tmp/com.loam.weekly-audit.err</string>
</dict>
</plist>
```

## Composition

- **`cron-create`** (sibling SKILL) — CronCreate is session-
  bound; launchd is durable cross-session. Pick by lifetime
  requirement. CronCreate's `durable: true` flag does not deliver
  what its name suggests.
- **`schedule-wakeup`** (sibling SKILL) — ScheduleWakeup is one-
  shot in-session; launchd is recurring across sessions.
- **`claude-feature-awareness`** SKILL — scheduling-comparison
  table covers all four primitives (Routines / desktop tasks /
  `/loop`+CronCreate / launchd). launchd is the only one of those
  with min-interval = 1s AND no requirement for an open session.
- **Reference plist:**
  `pos3/Library/LaunchAgents/com.loam.pos3.places-audit.plist`
  — canonical example of a durable cross-session loam job.

## Anti-patterns

- Using launchd for session-bounded work — CronCreate is lighter
  and doesn't require shell-level setup.
- Using launchd without checking `claude -p` licensing on the
  target machine — the program-args must invoke `claude` correctly
  for the local install.
- Forgetting `StandardOutPath` / `StandardErrorPath` — without
  them, debug is hard; launchd is silent about runtime failures
  otherwise.
- Hardcoding paths the user might move — use `$HOME` indirection
  or a stable canonical path.
- Forgetting `launchctl load ~/Library/LaunchAgents/<file>` —
  authoring the plist isn't enough; it must be loaded.

## Example invocation

```bash
# Author the plist:
cat > ~/Library/LaunchAgents/com.loam.weekly-audit.plist <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
... (full plist as above) ...
PLIST

# Load it:
launchctl load ~/Library/LaunchAgents/com.loam.weekly-audit.plist

# Verify:
launchctl list | grep com.loam.weekly-audit

# Unload (to remove):
launchctl unload ~/Library/LaunchAgents/com.loam.weekly-audit.plist
```

For loam-internal cross-session work, name the label with the
`com.loam.<job>` convention to keep `launchctl list` greppable.
