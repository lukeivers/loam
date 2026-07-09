# fleet-collector (WS-A2)

The **fleet collector bridge**: one command emits a single fleet-state JSON describing
every known agent run — live and recent — read from the on-disk records isolated agents
actually produce. The renderer (WS-A3, a cron/launchd static page, out of this
component's scope) consumes that JSON.

Why a bridge and not a view: loam's `observability-aggregator` is fed by an in-process
OTel exporter that isolated dispatched agents never install, so their spans never land
there. The telemetry isolated agents *do* reliably produce is on disk — `handsoff-loop`
run records and (when persisted) `subloam-driver` cost summaries — fragmented across
sinks that do not converge. This collector is the thin bridge over those files.

## Use

```
python -m loam.fleet_collector --root <workspace-or-runs-dir> --out fleet.json
```

`--root` is repeatable and accepts a workspace dir, its `runs/` dir, or a single run
dir. Output defaults to stdout. Library entry point: `collect_fleet(roots)`.

## What it reads (read-only over stable contracts)

| Source | Path | Fields drawn |
|---|---|---|
| handsoff-loop run record | `<run_dir>/run_record.jsonl` | `stage` (last non-heartbeat), `elapsed_s` |
| handsoff-loop run summary | `<run_dir>/run_summary.json` | `objective` (`design.objective`, else `intent.objective`) |
| artifact-probe liveness | the run dir | `alive`, `artifact_age_s` — via the **reused** `probe_liveness()` |
| subloam-driver cost summary | any `<run_dir>/*.json` carrying the full cost key-set | `cost_usd`, `cost_source`, `exit_status` |

The collector **modifies nothing** and imports no producing component's writable surface.

## Emitted shape

```json
{
  "generated_at": 1752000000.0,
  "generated_at_iso": "2026-07-09T00:00:00",
  "run_count": 3,
  "runs": [
    {
      "run_dir": "...", "workspace": "...",
      "objective": "Build a CSV-to-JSON converter." ,
      "stage": "verdict", "elapsed_s": 800.0,
      "alive": false, "artifact_age_s": 4000.0,
      "cost_usd": 0.42, "cost_source": "session-/cost-echo",
      "exit_status": 0
    }
  ]
}
```

Live runs sort first (the live feed reads top-down).

## Honesty rules (Lens 0: expose the substance, never fabricate)

- **Liveness is artifact-probe evidence, never a poller notification.** `alive` is the
  reused `probe_liveness()` judgment (newest-artifact mtime vs the staleness bound);
  `artifact_age_s` carries the concrete evidence so the judgment is auditable.
- **A missing cost is honestly absent.** No driver summary in a run dir →
  `cost_usd: null`, `cost_source: "absent"`, `exit_status: null`. A cost is never
  estimated or fabricated.
- **A live run has no objective yet.** `run_summary.json` is written only when a run
  finishes, so a live run reports `objective: null` rather than an invented one; its
  live value is in workspace/stage/elapsed/alive.

## Known gap (surfaced, not silently worked around)

`subloam-driver` currently writes its per-run summary (with `cost_usd` / `cost_source`
/ `exit_status`) to **stdout only** — no producer persists it into a run dir today. The
collector reads that summary when it *is* co-located in a run dir (full-key-set
detection). Wiring the driver to persist its summary into the run dir is a named
downstream step, outside WS-A2's fence. Until then, cost columns populate only where a
summary has been persisted alongside the run.
