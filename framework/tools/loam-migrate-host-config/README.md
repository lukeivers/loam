# loam-migrate-host-config

One-shot per-host migration helper for the M1b rename: relocates the
operator's existing `~/.pos/` per-host config directory to `~/.loam/`.

Lands as part of the M1.rename multi-amendment series sub-amendment
M1b. Per series-master `oss-v0-1-0-publish-rename.md` D-RNM.3 (no
compat window) the framework code reads only `~/.loam/` post-M1b;
this helper migrates an existing `~/.pos/` directory once, idempotently.

## Usage

Explicit invocation only. Run once per host, after upgrading to a
post-M1b release.

```sh
python -m loam_migrate_host_config
# or, if the helper's package is installed editable in a workspace's
# shared venv:
loam-migrate-host-config
```

Optional flag for testing:

```sh
loam-migrate-host-config --home /tmp/fake-home
```

## Idempotency contract — four cases

1. **`~/.pos/` exists, `~/.loam/` does not.** Renames `~/.pos/` to
   `~/.loam/`. Prints a one-line summary + the post-rename path.
   Exit 0.
2. **`~/.pos/` does not exist, `~/.loam/` exists.** Already migrated.
   Prints "already migrated"; exit 0.
3. **Neither exists.** Fresh machine. Prints "no per-host state
   present; nothing to migrate"; exit 0.
4. **Both `~/.pos/` and `~/.loam/` exist.** HALT. Prints both paths
   + an explicit refusal-to-merge message. Exit non-zero (`2`).
   The user resolves manually (review, back up, or delete one) and
   re-runs.

The helper never merges, copies, or modifies file contents — case 1
is a single `os.rename()`. Cases 2/3 read filesystem state only and
exit cleanly.

## Why explicit invocation (no auto-run)

The migration is per-host (not per-workspace). Auto-running it from
per-workspace first-run (which is the natural place to add a
"migration step" hook) would fire it multiple times across multiple
workspaces on the same machine, with the second-onwards firing
hitting case 2 (no-op) or case 4 (halt). The structural-over-advisory
principle says: name the surface the user uses, don't hide the
migration inside an unrelated lifecycle event. The helper is
explicit; the user runs it once when they upgrade.

If the user opens a fresh-clone workspace post-M1b without having
run the helper, framework code reading `~/.loam/` finds the dir
absent and (per existing fail-closed behaviour for missing config
dirs) raises a clear "config dir not present" error — not a silent
fallback to `~/.pos/`. That error message names this helper as the
remediation.

## Authority

- Per-host path rename: `loam-rename-decisions.md` Tier-1 #2.
- M1b sub-plan: `docs/rebuild/plans/oss-v0-1-0-publish-rename-1b.md`
  AC.RNM-1b.3 (idempotency contract) + AC.RNM-1b.5 (this README).
- Hard-cutover policy: series-master D-RNM.3 (no compat module, no
  symlink shim).
