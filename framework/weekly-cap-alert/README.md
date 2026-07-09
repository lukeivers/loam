# weekly-cap-alert (WS-A1)

Fire a channel alert when the Claude **weekly** cap crosses the owner-set
threshold; stay silent below it; on an unreadable cap, fire the categorical
failure reason and never a fabricated number.

Backplane workstream **WS-A1** (`workspace/strategy/ai-shop-backplane/BACKPLANE-PLAN.md`
§5, Track A). Composes the SEALED `usage-window-guard` by **import only**.

## What it does

Each scheduled tick:

1. Reads the REAL `seven_day` (weekly) utilization via
   `loam.usage_window_guard.read()` — the weekly bucket is the only Claude limit
   that costs anything; the 5-hour window is a throttle (standing owner rule).
2. Compares it to the configured threshold (owner-ratified default **60%**,
   backplane decision D5).
3. **Above threshold** → fires a notification carrying the utilization number.
   **Below** → silence. **`UsageUnavailable`** → fires the categorical failure
   `reason` (e.g. `auth_rejected`) with **no** number — because WS-A4's cap guard
   fails open on an unreadable cap *precisely because this alert covers the blind
   window* (a silent unavailable would leave nobody watching a dark cap reader).

## Run it

```
python -m loam.weekly_cap_alert                       # stdout delivery
python -m loam.weekly_cap_alert --notify-cmd "CMD"    # pipe message to CMD's stdin
python -m loam.weekly_cap_alert --threshold-pct 75    # one-off threshold override
```

## Threshold config

Threshold lives in **config, not code**. Set it in
`~/.claude/weekly-cap-alert.json` (or the path in `LOAM_WEEKLY_CAP_ALERT_CONFIG`):

```json
{ "threshold_pct": 60 }
```

Any absence/malformation fails open to the ratified 60% — a bad config never
wedges the alert nor silently moves the threshold.

## Schedule (launchd)

`loam.weekly_cap_alert.install.install(...)` renders the periodic LaunchAgent
plist (`RunAtLoad` + `StartInterval`, **no** `KeepAlive`) into
`~/Library/LaunchAgents/`. As a LaunchAgent it survives any single Claude session
ending. The operator runs `launchctl load` to activate it (a build renders the
artifact; it does not mutate the running launchd).

## The channel seam (H-3)

loam source **never** imports the pos3 workspace channel module — the delivery
surface is an injected `notify_fn` (`stdout_notify` default, `command_notify`
for the launchd bridge). To make real Discord delivery live, the launchd plist's
`--notify-cmd` points at a thin **workspace** wrapper (read stdin →
`post_to_active_channel`); that wrapper is a workspace artifact, outside loam's
fence. loam stays channel-agnostic.
