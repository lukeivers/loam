# orphan-plist-cleanup

Detects and reversibly remediates pre-amendment-#6 orphan pos-v2
launchd plists in `~/Library/LaunchAgents/` on a macOS host.

Plan: `docs/rebuild/plans/orphan-plist-cleanup-tool.md`.

## Background

Amendment #6 (`namespaced-labels-and-bootout`) moved pos-v2 launchd
labels from a global single-segment shape (e.g. `com.pos-v2.memory-
graphiti`, `com.pos.orchestrator`) to a workspace-slug-namespaced
shape (`com.pos-v2.<slug>.<kind>`). Hosts with a pos-v2 install from
before #6 may carry orphan plists with the old shape — they survive
across upgrades because the workspace's bootout-before-bootstrap loop
only touches its own labels. The 2026-04-23 pos3 first-run session
hit this: an orphan `com.pos-v2.memory-graphiti` daemon was loaded
and bound port 8765, which falsely satisfied the new workspace's
health probe.

This tool detects those orphans and remediates them reversibly.

## Install

```
pip install -e tools/orphan-plist-cleanup/
```

Registers the `orphan-plist-cleanup` console script. Requires
Python 3.11+. macOS only.

## Subcommand surface

```
orphan-plist-cleanup --dry-run    # list detected orphans; default mode
orphan-plist-cleanup --apply      # bootout + rename-aside each detected orphan
```

`--dry-run` is the default; running with no flags is equivalent.
`--apply` is the only mutating mode and must be passed explicitly.

## What counts as an orphan

A plist file in `~/Library/LaunchAgents/` whose filename matches one
of these pre-amendment-#6 shapes:

- `com.pos-v2.<single-segment>.plist` — single segment after the
  `com.pos-v2.` prefix, no embedded dots in that segment.
- `com.pos.<single-segment>.plist` — pre-pos-v2 v1-era shape.

A plist file whose filename matches `com.pos-v2.<slug>.<kind>.plist`
(workspace-slug-namespaced, two segments after `com.pos-v2.`) is
**never** classified as an orphan — those belong to live workspaces.

## What apply mode does

For each detected orphan:

1. `launchctl bootout gui/<uid>/<label>` is invoked. Stderr matching
   the "service not loaded" variant is treated as success (consistent
   with amendment #6's `ServiceManagerRunner.bootstrap` policy).
2. The orphan plist file is renamed to a sibling with extension
   `.orphan-disabled.bak`. The original `.plist` extension is
   replaced wholesale.
3. The action is reported on stdout.

The plist file is never deleted. Recovery is `mv foo.orphan-
disabled.bak foo.plist` followed by `launchctl bootstrap gui/<uid>
foo.plist`.

## Idempotency

Running `--apply` twice produces no double-action: after the first
run, the orphan files have suffix `.orphan-disabled.bak` and no
longer match the detection pattern.

## Exit codes

```
0   ok (dry-run completed, or apply succeeded with all orphans
    remediated, or no orphans found)
1   apply mode encountered a non-recoverable launchctl error on at
    least one orphan; the affected file was left in place
2   wrong platform (not macOS)
```

## Tests

```
cd tools/orphan-plist-cleanup && pytest -q
```

Tests mock the launchctl + filesystem boundary; no real `launchctl`
invocation occurs in the suite.
