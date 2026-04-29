# Operations — Install, Measure, Uninstall

Per Luke's build-dispatch ruling, the launchd user agent is
authorised for D2 measurement and is uninstalled at end of build.
This document records the commands so a future "running pOS" handoff
can re-activate the orchestrator without re-discovering them.

## Prerequisites

- macOS or Linux user session
- Python 3.13 venv at `pos-v2/.venv` with all four Phase 1 components
  installed editable + `pos_orchestrator` editable
- `~/.loam/bootstrap.py` authored by the workspace (fail-closed if
  missing)

## Install (macOS — launchd user agent)

```bash
cd /Users/lukeivers/ivers-corp-pos-v2
source .venv/bin/activate
python orchestrator/scripts/install_launchd.py \
    --python "$(pwd)/.venv/bin/python" \
    --working-dir "$(pwd)" \
    --throttle-secs 30
```

Verifies:

```bash
launchctl list | grep com.pos.orchestrator
# Expected: <pid>  0  com.pos.orchestrator
```

## Measurement (D2 addendum)

The measurement harness installs (if not already), runs four
failure-class experiments with cool-off gaps so the 30s throttle
only gates the explicit rapid-crash scenario, writes a JSON report,
uninstalls, and asserts the launchctl list is clean.

```bash
python orchestrator/scripts/measure_launchd.py \
    --python "$(pwd)/.venv/bin/python" \
    --working-dir "$(pwd)" \
    --out "$(pwd)/orchestrator/docs/measurement-launchd.json"
```

Total wall-clock: ~2 minutes (first boot + 3 × 35s cool-offs + rapid-
crash cycle + uninstall verify).

## Uninstall (manual)

```bash
python orchestrator/scripts/install_launchd.py --uninstall
launchctl list | grep com.pos.orchestrator   # must return empty
```

## Logs

- stdout: `~/.loam/logs/orchestrator.out`
- stderr: `~/.loam/logs/orchestrator.err`
- structured events: `~/.loam/orchestrator.sqlite` (query with
  `sqlite3 ~/.loam/orchestrator.sqlite "select event_type, count(*)
  from events group by event_type;"`)

## Troubleshooting

- **Orchestrator refuses to start with exit 2**: `~/.loam/bootstrap.py`
  is missing. Author it with a `register(orchestrator)` function.
- **Exit 3**: bootstrap file exists but raised on import or inside
  `register()`. Check `~/.loam/logs/orchestrator.err` for the
  traceback.
- **`launchctl bootstrap` permission denied**: you are in the system
  domain, not `gui/<uid>`. The install script uses `gui/<uid>` by
  default.
- **IPC socket already exists / stale**: the orchestrator removes
  orphaned socket files during `IPCServer.start`. If something else
  is holding the path, check with `lsof ~/.loam/orchestrator.sock`.
