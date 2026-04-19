# CLI reference

One-page summary of the `pos` CLI. Full flag docs via `pos upgrade --help`.

## Commands

```
pos status
    Show current framework version and the last few accepted releases.

pos upgrade <tag> --manifest <path> --staging-dir <path> [--prior-tag <tag>]
    Execute a release upgrade. Requires the release's pos-release.yml
    and an unpacked staging directory. Invokes the full sequence:
    pre-snapshot → pre-probe → pause → drain → SIGTERM → swap →
    launchctl kickstart → post-probe → clause verify → accept|rollback.

pos upgrade <tag> --dry-run [--manifest <path> --staging-dir <path>]
    Print the planned steps; make no state changes. Warns on silent
    schema bumps detected in the manifest (clause e pre-check).

pos upgrade <tag> --conflicts-from <path> ...
    Resume an upgrade from a user-edited conflicts YAML.

pos rollback <tag> [--prior-tag <tag>]
    Invoke explicit rollback. Restores substrate snapshots, reverts
    the symlink, and restarts the orchestrator on the prior tree.
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Upgrade accepted, or rollback succeeded. |
| 1 | Upgrade rejected and rolled back cleanly. |
| 2 | Argument error, invoked from live path, missing adapters. |
| 3 | Pending conflicts — edit `<tag>-conflicts.yaml` and retry. |
| 4 | Rollback itself failed — manual recovery required. |

## Invocation constraint

The CLI refuses to run if `sys.executable` resolves inside
`~/.pos/framework/current/`. This prevents the running orchestrator
from trying to replace the Python process that owns it. Invoke from a
staging venv or from the workspace's own venv — never from the live
pOS tree.

## Production adapters

The CLI is framework-only; there are no personas in pOS core. The
workspace wires live adapters via `--adapters-module <pkg.mod>`:

```python
# workspace-local: e.g. products/pos_harness/adapters.py
def build_adapters():
    return MyAdapters(
        pid_file=Path("~/.pos/orchestrator.pid").expanduser(),
        ipc_socket=Path("~/.pos/orchestrator.sock").expanduser(),
        launchd_label="com.pos.orchestrator",
        ...
    )
```

The adapters must implement the ``LiveAdapters`` protocol (see
``upgrade.py`` for the full list of required methods).

## Configuration

```yaml
# ~/.pos/upgrade-config.yaml
auto_update_mode: require_confirmation  # or notify_and_apply
drain_timeout_seconds: 30
sigterm_timeout_seconds: 30
orchestrator_boot_timeout_seconds: 60
cancel_window_seconds: 60               # notify_and_apply only
confirmation_timeout_hours: 24          # require_confirmation only
launchd_label: com.pos.orchestrator
```
