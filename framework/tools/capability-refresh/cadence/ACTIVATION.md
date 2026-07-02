# Cadence activation — the RUN binding

> **Primary binding is now a GitHub Actions scheduled workflow** in
> `lukeivers/loam` (`.github/workflows/capability-refresh.yml`). This
> reverses the 2026-06-14 cloud-routine activation per the owner-ratified
> architecture doc
> `workspace/strategy/capability-refresh-delivery-architecture-2026-07-02.md`.
> Both prior bindings failed for the same structural reason — the runner was
> separated from the commit target: the cloud routine had
> compute-but-no-write (403-stranded, zero commits landed in ~18 days); the
> local launchd job had write-but-no-guaranteed-runtime (dead for weeks under
> a fragile Xcode Python 3.9). Actions has native `GITHUB_TOKEN` write,
> guaranteed uptime, pinned deps, and visible failure.

## Primary — GitHub Actions scheduled workflow (ACTIVE)

`.github/workflows/capability-refresh.yml`. Nothing to activate by hand — the
workflow is live once it is on the default branch.

- **Schedule:** daily `37 12 * * *` (high-velocity) + weekly `37 13 * * 0`
  (long-form), UTC (America/Chicago shifts by 1h across DST). Plus
  `workflow_dispatch` for manual runs (the verification path).
- **Runner:** invokes the deterministic `scripts/run-cadence.sh` with
  `LOAM_REFRESH_NO_COMMIT=1`, then OPENS A PULL REQUEST with the corpus
  changes for owner review — it NEVER auto-lands to `main` (ratified
  decision 2).
- **Failure surface:** a failed run goes red and GitHub emails the owner —
  the failure visibility neither prior binding had.

Manual fire: the **Actions** tab → *capability-refresh* → *Run workflow*
(pick the cadence class), or `gh workflow run capability-refresh.yml -f
cadence-class=high-velocity`.

## RETIRED — Anthropic cloud routines

The two cloud routines activated 2026-06-14 (`capability-refresh-daily`
`trig_018DZTYo…`, `capability-refresh-weekly` `trig_01R27t…`) are **RETIRED**.
They burned subscription usage producing commits nobody could reach (proxy /
GitHub-MCP 403). Deleting the routines themselves is an interactive
`/schedule` / web-console action (a repo edit cannot reach the routines API);
the repo-side binding is retired here. `routine-spec.md` is kept as the
historical record, banner-marked RETIRED.

## Fallback — launchd (documented INACTIVE)

The plists in `launchd/` are kept as a documented-**INACTIVE** fallback for a
workspace with no git host. They are booted out (`launchctl bootout
gui/$(id -u)/com.loam.capability-refresh-daily` + `-weekly`) and must NOT be
re-loaded except as a deliberate last resort. **Before any re-activation they
MUST first be hardened:**

- **Use the component venv, NOT bare `python3`.** The daily job died for weeks
  with `ModuleNotFoundError: No module named 'yaml'` under the Xcode-bundled
  Python 3.9 (past end-of-life; the `plists` invoke `python3 -m
  capability_refresh` over the login-shell PATH — the proven-fragile bit). A
  `--user` PyYAML install is a stopgap that pins nothing; an interpreter/macOS
  update re-breaks it. Pin the absolute interpreter to the project `.venv`
  python.
- **Add a failure signal.** launchd gave zero failure signal for weeks — a
  dead job that tells no one is the exact "refresh that never ran" failure the
  currency slice was built to kill.

Re-activate (last resort, only after the hardening above):

```
launchctl bootstrap gui/$(id -u) /Users/lukeivers/loam/framework/tools/capability-refresh/cadence/launchd/com.loam.capability-refresh-daily.plist
launchctl bootstrap gui/$(id -u) /Users/lukeivers/loam/framework/tools/capability-refresh/cadence/launchd/com.loam.capability-refresh-weekly.plist
```

Deactivate with `launchctl bootout gui/$(id -u)/<label>`. Commits stay LOCAL
(the runner never pushes).

## Manual run (no activation; always allowed)

```
cd /Users/lukeivers/loam && ./framework/tools/capability-refresh/scripts/run-cadence.sh high-velocity
```

or, without committing:

```
PYTHONPATH=framework/tools/capability-refresh/src python3 -m capability_refresh --cadence-class all --dry-run
```
