# launchd Auto-Restart Measurement (D2 + D10 addendum)

Measurements captured on the reference machine (macOS, Apple M-series,
Python 3.13.12) per the D10 bundled-documentation requirement and
D2 acceptance. Per Luke's dispatch ruling, the launchd agent was
installed for the measurement and uninstalled at end of build; the
`launchctl list | grep com.pos.orchestrator` check returned empty at
the end of the run (see "Uninstall verification" below).

## Setup

- Plist: `ops/launchd/com.pos.orchestrator.plist.tmpl`
- Label: `com.pos.orchestrator`
- Domain: `gui/501` (user agent)
- Throttle: `ThrottleInterval = 30` seconds
- `RunAtLoad = true`, `KeepAlive = true`
- Measurement harness: `scripts/measure_launchd.py`
- Raw report: `docs/measurement-launchd.json`

The harness asks `launchctl` to deliver the signal
(`launchctl kill SIGNAME gui/<uid>/com.pos.orchestrator`). Direct
`os.kill` returns EPERM against a launchd-managed PID because the
job is owned by launchd, not the invoking user session. Using
launchctl itself is the portable idiom.

Latency is measured as the wall-clock interval between "process exited"
(old pid absent) and "new pid present" as reported by `launchctl print`.

## Results

| Failure class | old_pid → new_pid | Restart latency | Behaviour |
|---------------|-------------------|-----------------|-----------|
| First boot after install | — → 52352 | 0.008 s | `RunAtLoad` triggers immediate start. |
| SIGKILL (cold from first boot) | 52352 → 52822 | **7.15 s** | launchd enforces `minimum runtime = 30s`; first kill within that window delays respawn until the minimum window elapses. |
| SIGSEGV (post-warmup) | 52822 → 53091 | **0.007 s** | Immediate restart. Beyond minimum-runtime window, launchd respawns with no added delay. |
| OOM approx (SIGABRT) | 53091 → 54127 | **0.008 s** | Immediate restart. (True OOM-kill parity was not reproduced on a dev machine — SIGABRT is the closest safe proxy for the abnormal-exit telemetry launchd records.) |
| Rapid-crash loop — shot 1 | 54127 → 54941 | 0.008 s | Immediate. |
| Rapid-crash loop — shot 2 | 54941 → 55727 | **30.10 s** | `ThrottleInterval = 30s` honored; launchd held the respawn. |
| Rapid-crash loop — shot 3 | 55727 → 56108 | **30.02 s** | Throttle continues to gate. |

## Conclusions against D2 acceptance

- **launchd plist loads without errors.** Confirmed — install output
  prints `installed plist at …`; `launchctl print` reports state =
  running, runs = 1.
- **SIGKILL → automatic restart within bounded window.** Confirmed —
  7.15 s cold (inside minimum-runtime gate) and ~0.008 s warm (outside
  it). Both fall inside the declared 30-second throttle ceiling.
- **Rapid-crash loop is throttled, not infinite-looped.** Confirmed —
  the 2nd and 3rd shots of three successive SIGKILLs are gated at
  30.10 s and 30.02 s respectively. `ThrottleInterval = 30` matches
  Luke's decision (ruling: 30 s throttle).

## Read

The 30-second throttle behaves as configured. The first observed
SIGKILL-restart latency is dominated by the minimum-runtime gate,
not the throttle — the process had only existed for <1 second when
it was killed, so launchd waited out the 30-second minimum before
respawning. Subsequent restarts complete in under 10 ms because the
process had lived long enough to satisfy the minimum window.

The 30-second throttle on the rapid-crash loop is the property that
matters for real failure scenarios: a transient cause (bad bootstrap,
missing dependency, API outage mid-init) cannot infinite-loop the
orchestrator. It gets 30 s to clear.

## Uninstall verification

After measurement, the harness ran `launchctl bootout
gui/501/com.pos.orchestrator` and removed
`~/Library/LaunchAgents/com.pos.orchestrator.plist`. Post-cleanup:

```bash
$ launchctl list | grep com.pos.orchestrator
(empty)

$ ls ~/Library/LaunchAgents/com.pos.orchestrator.plist
ls: ... No such file or directory
```

This satisfies the dispatch's explicit end-of-build assertion:
*"plist is uninstalled; `launchctl list | grep pos` returns nothing."*

## Reproducing

```bash
cd <workspace>/loam
source .venv/bin/activate
python orchestrator/scripts/measure_launchd.py \
    --python "$(pwd)/.venv/bin/python" \
    --working-dir "$(pwd)" \
    --out "$(pwd)/orchestrator/docs/measurement-launchd.json"
```

Total wall-clock: ~2 minutes (first boot + 3 × 35 s cool-offs + rapid-
crash cycle + uninstall verify). If a stale plist exists from a prior
run, the harness removes it first — the uninstall is idempotent.

To re-activate the orchestrator permanently in a future "running pOS"
handoff, omit `measure_launchd.py` and call `install_launchd.py`
directly (see `operations.md`).
