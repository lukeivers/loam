# self-upgrade

## What it does

`self-upgrade` is the framework that coordinates every
component's upgrade-fidelity surfaces into a single atomic
operation. When you upgrade loam — the framework, a plugin, a
component — there is a seven-clause acceptance contract every
component must satisfy: the upgrade either lands cleanly across
the workspace or rolls back, never partially applied.

The seven clauses (paraphrased):

- a — framework state migrated to the new version's expected shape,
- b — workspace config re-rendered against the new shape,
- c — running supervisor processes restarted under the new code,
- d — per-host launchd / systemd labels re-installed,
- e — fixtures and per-host config migrated where the version
  changed schema,
- f — observability emission surface registered against the new
  version's namespace,
- g — rollback path exercised so the upgrade can be reverted if
  needed.

The component composes the per-component upgrade hooks
(workspace-bootstrap's adapter contributions, dormancy's config
migration, observability-aggregator's namespace registration,
etc.) into one atomic action.

## How to invoke

User-facing entry point:

```bash
loam upgrade                     # upgrade the framework to the
                                 # latest canonical HEAD
loam upgrade --rollback          # revert the most recent upgrade
```

The upgrade verb itself is implemented as a coordinator that
calls into each component's upgrade contract; per-component
upgrade behaviour cannot be invoked alone (the seven-clause
contract is atomic).

## Observable surface

What you can `tail` / `cat` / `grep` to see the component working:

- **OTel spans.** `loam.self_upgrade.*` namespace. Each upgrade
  run emits a `run` span with child spans for each clause
  (`clause.a`, `clause.b`, etc.); rollbacks emit `rollback`
  spans listing what was reverted.
- **Upgrade log.** Per-host upgrade history at
  `~/.loam/upgrades.log`; survives the framework's data area
  being wiped.
- **Manifest stash.** The pre-upgrade state is stashed before
  each run so the rollback path has a snapshot to restore from;
  visible at `~/.loam/upgrades/<run-id>/`.
- **Greeting integration.** If a previous upgrade is still
  in-flight (an interrupted run), the SessionStart greeting
  surfaces it for resumption.

## Stable surfaces (for plugin authors)

Plugin authors register their plugin's upgrade contract through
a plugin upgrade contribution; the seven-clause requirement
applies to plugins identically. Most plugins satisfy clauses by
declaring their state shape and config schema; the framework
supplies the rest.

For internal implementation detail see the component source under
`framework/self-upgrade/`.
