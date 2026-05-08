# orphan-plist-cleanup

Detects and reversibly remediates pre-amendment-#6 archaeological
orphan launchd plists in `~/Library/LaunchAgents/` on a macOS host.

Plan: `docs/plans/orphan-plist-cleanup-tool.md`.

## Background

Amendment #6 (`namespaced-labels-and-bootout`) moved loam launchd
labels from a global single-segment shape (e.g. `com.pos-v2.memory-
graphiti`, `com.pos.orchestrator` — the historical pre-#6 archaeological
shapes) to a workspace-slug-namespaced shape (post-M1c rename:
`com.loam.<slug>.<kind>`; pre-M1c the prefix was `com.pos-v2.` —
that pre-M1c-live-shape transition is owned by the M1c migration
helper at `framework/tools/loam-migrate-launchd-labels/`, not this
tool). Hosts with an install from before #6 may carry orphan plists
with the old single-segment shape — they survive across upgrades
because the workspace's bootout-before-bootstrap loop only touches
its own labels. The 2026-04-23 pos3 first-run session hit this: an
orphan `com.pos-v2.memory-graphiti` daemon was loaded and bound
port 8765, which falsely satisfied the new workspace's health probe.

This tool detects those pre-#6 archaeological orphans and remediates
them reversibly. Post-M1c stale `com.pos-v2.<slug>.<kind>` plists are
NOT this tool's mission — see the M1c migration helper for that
transition.

## Run

This is a one-shot remediation tool. You do not need to install it.
The recommended path runs the source directly using the Python that
loam already requires (`python3.13`, present on any host that
completed loam first-run).

**Prerequisites:** macOS, plus `python3.13` available at
`/opt/homebrew/bin/python3.13` (Homebrew's `python@3.13` formula —
already installed if loam first-run has run on this host). To
confirm:

```
/opt/homebrew/bin/python3.13 --version
```

You should see `Python 3.13.<something>`. If that command errors,
install Homebrew Python 3.13 with `brew install python@3.13` first
(roughly two minutes on a warm cache).

### Dry-run (read-only — list orphans, do not change anything)

From the pos-v2 workspace root, run this single line. Estimated
wall-clock: under one second.

```
PYTHONPATH=tools/orphan-plist-cleanup/src /opt/homebrew/bin/python3.13 -m orphan_plist_cleanup --dry-run
```

You will see one absolute path per detected orphan (or no output if
no orphans exist). Exit code 0 either way.

### Apply (mutating — bootout each orphan and rename it aside)

When you have reviewed the dry-run output and want to remediate:

```
PYTHONPATH=tools/orphan-plist-cleanup/src /opt/homebrew/bin/python3.13 -m orphan_plist_cleanup --apply
```

Each orphan is booted out and renamed to `*.orphan-disabled.bak` next
to the original. The plist file is never deleted; recovery is
documented under "What apply mode does" below.

### Optional — install as a PATH-resolvable command

If you would rather type `orphan-plist-cleanup` than the
`PYTHONPATH=… python3.13 -m …` line, install it editable into a
Python 3.13 environment. The simplest no-side-effects path uses a
throwaway venv:

```
/opt/homebrew/bin/python3.13 -m venv /tmp/opc-venv
/tmp/opc-venv/bin/pip install -e tools/orphan-plist-cleanup/
/tmp/opc-venv/bin/orphan-plist-cleanup --dry-run
```

Estimated wall-clock: under thirty seconds. To remove afterwards:
`rm -rf /tmp/opc-venv`. Do not run a bare `pip install -e
tools/orphan-plist-cleanup/` — on most macOS shells the default
`pip` resolves to a Python below 3.11 and the install fails with
`Package 'orphan-plist-cleanup' requires a different Python`.

## Subcommand surface

```
--dry-run    # list detected orphans; default mode
--apply      # bootout + rename-aside each detected orphan
```

`--dry-run` is the default; running with no flags is equivalent.
`--apply` is the only mutating mode and must be passed explicitly.

## What counts as an orphan

A plist file in `~/Library/LaunchAgents/` whose filename matches one
of these pre-amendment-#6 archaeological shapes:

- `com.pos-v2.<single-segment>.plist` — single segment after the
  `com.pos-v2.` prefix, no embedded dots in that segment.
- `com.pos.<single-segment>.plist` — pre-pos-v2 v1-era shape.

A plist file whose filename matches `com.loam.<slug>.<kind>.plist`
(workspace-slug-namespaced post-M1c live shape, two segments after
`com.loam.`) is **never** classified as an orphan — those belong to
live workspaces. Pre-M1c stale 4-segment plists `com.pos-v2.<slug>.<kind>.plist`
are also not this tool's mission — see the M1c migration helper at
`framework/tools/loam-migrate-launchd-labels/` for that transition.

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
