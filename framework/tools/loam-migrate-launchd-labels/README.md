# loam-migrate-launchd-labels

One-shot per-host migration helper for the M1c rename: bootouts pre-M1c
`com.pos-v2.<slug>.<kind>` launchd labels and renames the plist files
aside in `~/Library/LaunchAgents/`.

Lands as part of the M1.rename multi-amendment series sub-amendment
M1c. Per series-master `oss-v0-1-0-publish-rename.md` D-RNM.3 (no
compat window) the framework code emits only `com.loam.<slug>.<kind>`
labels post-M1c; this helper retires the existing legacy labels once,
idempotently.

Sibling to `loam-migrate-host-config` (M1b's per-host config dir
helper). Distinct surface; same single-purpose-helper pattern.

## Usage

Explicit invocation only. Run once per host, after upgrading to a
post-M1c release.

```sh
python -m loam_migrate_launchd_labels
# or, if the helper's package is installed editable in a workspace's
# shared venv:
loam-migrate-launchd-labels
```

Optional flag for testing:

```sh
loam-migrate-launchd-labels --launch-agents-dir /tmp/fake-agents
```

## Contract — what the helper does

For each plist filename in `~/Library/LaunchAgents/` whose shape matches
the pre-M1c live form `com.pos-v2.<slug>.<kind>.plist` (4-segment, two
segments after the `com.pos-v2.` prefix):

1. Issues `launchctl bootout gui/<uid>/<label>`. Stderr fragments
   matching the "service not loaded" variant (mirroring amendment #6's
   `ServiceManagerRunner.bootstrap` policy + the orphan-plist-cleanup
   tool's apply mode) are treated as benign — the label may have
   already been booted out by a prior run or manual cleanup.
2. Renames the plist file from `<base>.plist` to
   `<base>.label-rebrand-disabled.bak` (extension replaced wholesale).
   The plist file is never deleted.
3. Reports each remediated path on stdout.

## Outcomes + exit codes

| Outcome | Exit | Meaning |
|---|---|---|
| `NOTHING_TO_MIGRATE` | 0 | Zero matching legacy plists. Clean machine, already-migrated host, or a re-run after a prior MIGRATED. |
| `MIGRATED` | 0 | One or more legacy plists processed cleanly. |
| `PARTIAL_FAILURE` | 1 | At least one legacy plist's bootout failed non-recoverably. Affected file left in place; processing continues for remaining plists. |

## What the helper does NOT do

- **Pre-#6 single-segment orphans** (`com.pos-v2.<single>.plist`,
  `com.pos.<single>.plist`) — those are the orphan-plist-cleanup
  tool's mission. This helper explicitly rejects them via the
  4-segment filter; they are unaffected by an invocation here.
- **Writing new `com.loam.<slug>.<kind>.plist` files** — workspace-
  bootstrap's first-run scaffold owns that path. After running this
  helper, open the workspace in Claude Code and the existing first-run
  flow installs the new-shape plists.
- **Touching the post-M1c live shape** (`com.loam.<slug>.<kind>.plist`)
  — those belong to live workspaces; the helper's filter explicitly
  rejects them.

## Recovery

If a `.label-rebrand-disabled.bak` file needs to be restored (e.g. the
post-M1c first-run scaffold has a problem and the user wants to fall
back to a known-good legacy plist):

```sh
# In ~/Library/LaunchAgents/
mv com.pos-v2.<slug>.<kind>.label-rebrand-disabled.bak \
   com.pos-v2.<slug>.<kind>.plist
launchctl bootstrap gui/$(id -u) com.pos-v2.<slug>.<kind>.plist
```

This is a fallback path only — the structural target of M1c is the
`com.loam.<slug>.<kind>` shape; running this helper followed by
re-running workspace first-run is the supported flow.

## Idempotency

Running the helper twice in succession after a clean MIGRATED produces
NOTHING_TO_MIGRATE the second time — the renamed files no longer carry
the `.plist` suffix the filter matches against.

A run that hits PARTIAL_FAILURE is also re-runnable: the failed
plist's bootout is retried; previously-processed plists no longer
match the filter so they're not re-processed.

## Why explicit invocation (no auto-run)

The migration is per-host (not per-workspace). Auto-running it from
per-workspace first-run would fire it multiple times across multiple
workspaces on the same machine (each firing hitting NOTHING_TO_MIGRATE
after the first). The structural-over-advisory principle says: name
the surface the user uses, don't hide the migration inside an
unrelated lifecycle event. The helper is explicit; the user runs it
once when they upgrade.

## Authority

- Launchd-label rename: `loam-rename-decisions.md` Tier-1 #4 (label
  rebase + version-suffix drop concurrent).
- M1c sub-plan: `docs/plans/oss-v0-1-0-publish-rename-1c.md`
  AC.RNM-1c.3 (idempotency contract) + AC.RNM-1c.5 (orphan-plist-
  cleanup NAMESPACED-arm rebase, distinct mission from this helper).
- Hard-cutover policy: series-master D-RNM.3 (no compat module, no
  symlink shim).
- Sibling helper precedent: `framework/tools/loam-migrate-host-config/`
  (M1b's per-host config dir helper).
