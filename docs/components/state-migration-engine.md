# state-migration-engine

## What it does

`state-migration-engine` is the component that carries a user's
`.loam/` state forward across loam upgrades. When the framework
ships a release that changes the shape of a user's stored state, the
engine replays the declared migrations — in release-version order,
never jumping — so an existing workspace ends up at the new shape
without the user touching anything.

Three pieces make up the engine:

- **Declared-migration schema + validator** — each release declares
  what it changes to a user's state in a
  `docs/state-migrations/<slug>.migration.yaml` file. A code-only
  release declares `operation: no-op` (a valid, ~30-second
  declaration). The release-gate (`loam release`) HARD-BLOCKS a
  publish that declares no migration at all.
- **Ordered cumulative replay** — the engine reads the per-workspace
  applied-migration cursor, enumerates the migrations not yet applied,
  and replays them in release-version order through every
  intermediate version (never skipping ahead).
- **Reversibility safety envelope** — the whole replay runs inside the
  reversibility primitive's snapshot/restore envelope. A migration that
  fails rolls the workspace back to its pre-replay state; the cursor
  then reflects the pre-replay version, so a failed upgrade never
  leaves a workspace half-migrated.

## How to invoke

The user-facing CLI verb:

```bash
loam migrate                          # replay every pending migration in order
loam migrate --dry-run                # report the pending set + order, apply nothing
loam migrate --workspace <root>       # migrate a workspace other than the cwd
loam migrate --target-version <v>     # replay only up to a named version
loam migrate --migrations-dir <dir>   # override the declared-migration contract home
```

`loam migrate` is the real production upgrade entry-point — the
auto-upgrade slice invokes this verb when a workspace's cursor is
behind the framework's shipped version.

## Observable surface

What you can `cat` / `grep` to see the component working:

- **Applied cursor.** The authoritative per-workspace record of which
  migrations have run lives at
  `<workspace>/.loam/migrations/.cursor` (user-state; gitignored). A
  fresh workspace with no `.cursor` reads as the empty cursor.
- **Declared-migration contract.** The tracked, version-controlled set
  of declared migrations lives at `docs/state-migrations/*.migration.yaml`
  (see `docs/state-migrations/README.md`). This is the source of truth
  the engine replays against.
- **Reversibility snapshots.** Each replay run takes a snapshot through
  the reversibility primitive before applying; a rollback restores from
  it. The snapshot root is configurable (`--snapshot-root`).

## Stable surfaces (for plugin authors)

A plugin that ships its own user-state and wants it carried forward
declares a migration in `docs/state-migrations/` the same way the
framework does; the engine replays plugin and framework migrations
through the same ordered cursor. Pinning against a specific loam minor
also pins the migration set that version shipped.

For internal implementation detail see the component source at
[`framework/state-migration-engine/`](../../framework/state-migration-engine/).
