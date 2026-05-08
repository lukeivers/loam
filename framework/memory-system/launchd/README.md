# launchd hosting for the Graphiti service — HISTORICAL REFERENCE

**This directory is historical reference material only. Do not follow
the instructions from older revisions of this README.**

## Do not manually install the plist in this directory

The file `com.loam.memory-graphiti.plist` in this directory contains
**hardcoded absolute paths** (`<workspace>/loam/...`)
and ships as a historical artifact from before the hands-off-lifecycle
work moved plist generation into the first-run scaffold. It is NOT the
plist used at runtime. Do NOT `cp` it into `~/Library/LaunchAgents/`
and do NOT `launchctl load` it.

Any copy made manually will be silently overwritten at first-run
boot anyway.

## Authoritative plist generator

The plist that actually runs the Graphiti service is generated at
**first-run** by the workspace-bootstrap scaffold:

- Generator: `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py`
- Template: `_LAUNCHD_TEMPLATES["memory-graphiti"]` (the `{workspace}`
  and `{label}` placeholders are substituted at scaffold time with the
  current clone's absolute path and the per-workspace launchd label).
- Output: written directly to `~/Library/LaunchAgents/<label>.plist`
  by the scaffold, then loaded via `launchctl bootstrap`.

The scaffold runs automatically when the workspace is opened in Claude
Code for the first time (see `hands-off-lifecycle/` for the
SessionStart-hook chain). No manual install step is required or
supported.

## What to do instead

1. Clone the repo into the location you want it to live.
2. Open the clone in Claude Code. The SessionStart hook detects the
   first-run condition and dispatches the scaffold.
3. The scaffold substitutes the real paths into the plist template,
   writes the file to `~/Library/LaunchAgents/`, and `launchctl
   bootstrap`s it. The Graphiti service auto-starts at login and
   restarts on crash.

## Why the directory is still here

Two reasons:

1. The plist shape — `RunAtLoad` + `KeepAlive` + `ThrottleInterval: 10`
   + log paths + `PYTHONUNBUFFERED=1` — is useful reading when
   debugging what the scaffold's template produces.
2. Prior research (`docs/archive/component-research/true-first-run/research.md`)
   explicitly ruled that this file could stay in place as reference
   since it is not used at runtime.

A future cleanup amendment may remove the directory outright; for now
it is reference-only.

## Service behaviour (what the scaffold's plist produces)

- Label: `com.loam.memory-graphiti` (or a workspace-scoped variant).
- Auto-start on login (`RunAtLoad`).
- Restart on crash (`KeepAlive` with a 10-second throttle).
- Logs to `<workspace>/memory-system/data/graphiti-service.log` and
  `.err.log`.

Verify the running service:

```bash
launchctl list | grep memory-graphiti
curl -s http://127.0.0.1:9876/health
```

Uninstall (if you really need to — normally the scaffold owns
lifecycle):

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.loam.memory-graphiti.plist
rm ~/Library/LaunchAgents/com.loam.memory-graphiti.plist
```
