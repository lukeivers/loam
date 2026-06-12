# Cadence activation — OWNER-GATED (one command per mechanism)

> **Nothing is live.** No cloud routine has been created and no launchd
> agent is loaded. Persistent unattended automation is switched on only
> by the owner's explicit word (dispatcher gate 2026-06-11; precedent:
> the refusal-watchdog persistence ruling). Everything below is a single
> documented step.

## Primary — cloud routines (recommended; D-CUR.2)

From an interactive Claude Code session in this repo (one per cadence
class):

```
/schedule create the capability-refresh-daily routine exactly as specified in framework/tools/capability-refresh/cadence/routine-spec.md
/schedule create the capability-refresh-weekly routine exactly as specified in framework/tools/capability-refresh/cadence/routine-spec.md
```

Runs on Anthropic's cloud on the subscription (no machine awake, no API
key); commits arrive on a `claude/`-prefixed branch via the owner's
GitHub connection (reviewable — keep the default branch permissions).

## Fallback — launchd (machine must be awake at fire time)

```
launchctl bootstrap gui/$(id -u) /Users/lukeivers/loam/framework/tools/capability-refresh/cadence/launchd/com.loam.capability-refresh-daily.plist
launchctl bootstrap gui/$(id -u) /Users/lukeivers/loam/framework/tools/capability-refresh/cadence/launchd/com.loam.capability-refresh-weekly.plist
```

Deactivate with `launchctl bootout gui/$(id -u)/<label>`. Commits stay
LOCAL (the runner never pushes).

## Manual run (no activation; always allowed)

```
cd /Users/lukeivers/loam && ./framework/tools/capability-refresh/scripts/run-cadence.sh high-velocity
```

or, without committing:

```
PYTHONPATH=framework/tools/capability-refresh/src python3 -m capability_refresh --cadence-class all --dry-run
```
