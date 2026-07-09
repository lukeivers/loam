# WS-A2 — Fleet collector bridge (builder plan)

**Status:** in-build. **Working directory:** `/Users/lukeivers/loam`.
**Source:** `workspace/strategy/ai-shop-backplane/BACKPLANE-PLAN.md` §5 Track A (WS-A2)
+ `workspace/strategy/ai-shop-backplane/02-dashboard.md` §4b/§6.
**Class:** NEW standalone component under `framework/fleet-collector/`. NOT a sealed-component
amendment → plan + tests (no `loam amend` cycle).

---

## 1. Objective

One command emits a single fleet-state JSON describing every known agent run (live and
recent) read from the on-disk records isolated agents actually produce. The artifact is
what WS-A3 (a cron-rendered static page, out of this fence) consumes. Read-only over
stable contracts; a bridge over sinks that do not converge, not a pure view.

## 2. Fence (scope)

IN: a new component `framework/fleet-collector/` (`loam.fleet_collector`). It READS
`handsoff-loop` run dirs (`run_record.jsonl`, `run_summary.json`) and reuses
`probe_liveness()` from `handsoff_loop/convergence.py` for liveness. It emits a fleet JSON.

OUT (halt-and-surface if the work would touch these):
- Any modification to `handsoff-loop`, `subloam-driver`, or any sealed component.
- `.claude/settings.json` (Track F single-writer; WS-A2 registers no hook).
- The renderer / cron job (WS-A3), the cap alert (WS-A1), any other workstream.

## 3. Data sources — verified against ground truth this session

- **handsoff-loop run dir** = `<workspace>/runs/<YYYYMMDD-HHMMSS>/` containing
  `run_record.jsonl` (append-only JSONL; each line `{"ts","ts_mono","stage","message",...}`;
  `stage` ∈ understanding/asking/researching/planning/building/checking/verdict/heartbeat)
  and, ONLY once the run finishes (`_finish`), `run_summary.json`
  (`BuildFromIntentResult.as_evidence()` → `design.objective`, `intent.objective`, `terminal`).
- **liveness** = `probe_liveness(run_dir)` (newest-artifact mtime vs `stale_after_s`).
  Reused via a `__file__`-relative `sys.path` insert (loam cross-package convention),
  copied byte-for-byte from `framework/file-lease-registry/src/loam/file_lease_registry/_liveness.py`.
- **cost / exit_status** = a `subloam-driver` per-run summary carrying
  `cost_usd` + `cost_source` + `exit_status`. **Verified F2 gap:** `subloam-driver`
  writes this summary to STDOUT only (`cli.py`); `driver.py` persists NO cost file to
  disk. The collector reads a driver summary co-located in a run dir WHEN one is present
  (detected by the full key-set, so `run_summary.json` cannot false-match); absent → the
  fields degrade to `cost_usd: null`, `cost_source: "absent"`, `exit_status: null`.

## 4. Named decisions (recommendation = decision; F2 gaps surfaced)

- **D-A2-1 objective for live runs → `null` (honest).** `run_summary.json` is written
  only at `_finish`; `_frozen` carries the acceptance gate, not the objective. No stable
  on-disk objective field exists for a live run. objective is read from `run_summary.json`
  when present, else `null`. The live view earns its keep on workspace/stage/elapsed/alive
  (the "is it stuck / runaway / done?" signal); objective enriches rows with real evidence.
  No fake objective field is injected into fixtures.
- **D-A2-2 cost read-shape is a forward contract (F2).** No producer persists the driver
  summary to a run dir today. The collector defines the read (full-key-set detection);
  wiring the driver to persist its summary into the run dir is a named downstream step,
  OUT of this fence. Surfaced, not built.
- **D-A2-3 stage = last NON-heartbeat event's stage** (heartbeat is a liveness pseudo-stage,
  not pipeline progress); fall back to last stage if every event is a heartbeat.
- **D-A2-4 workspace = `run_dir.parent.parent`** when the dir sits under `runs/`
  (`<workspace>/runs/<ts>`), else `run_dir.parent`.
- **D-A2-5 `~/.claude/projects` (session-transcript / session-report read) is EXCLUDED
  from WS-A2 — surfaced, not silently dropped (F2).** The dispatch prose named three
  sources (handsoff run-records, subloam `/cost`, and `~/.claude/projects`). The binding
  WS-A2 ACs (§5) name only the first two, and BACKPLANE-PLAN §4 build-table lines 285–286
  assign the session-transcript HISTORICAL read to Build 3 (WS-A3, the page's historical
  strip: `observability-aggregator` + `per-project-pm` + session data), not Build 2. It is
  also per-session-keyed, not per-handsoff-run-keyed, so it does not fold into this
  collector's per-run rows. **Call: build to the two AC-named per-run sources; exclude the
  session-transcript leg as A3's historical surface.** If the dispatcher intended the
  broader prose to override the plan table, adding it is a bounded second leg globbing
  `~/.claude/projects` appended to the same JSON — surfaced for the dispatcher's ruling.

## 5. Acceptance criteria (from BACKPLANE-PLAN §5 WS-A2; outcome-shape)

- **AC.FLEET.1 (outcome-altitude).** Against a fixture directory with ≥3 run records
  (one live-with-recent-heartbeat, one dead-stale, one completed-with-cost), the production
  entry point emits JSON where each run carries
  `{workspace, objective, stage, elapsed, alive, cost_usd|null, exit_status}` (+ the
  constraint-mandated `cost_source`), and the alive/dead judgment matches the artifact
  evidence. Liveness is the reused `probe_liveness()` — a test asserts the collector's
  `alive` equals `probe_liveness(run_dir)["alive"]` (proves reuse, not a re-roll).
- **AC.FLEET.2.** A run record with a partial (mid-write) last line does not crash the
  collector; the run appears with its last complete state.
- **AC.FLEET.3.** Runtime under 5 seconds against 100 fixture runs.

Every field/branch maps to an AC above (ODD §2.5). No non-objective/defensive code.

## 6. Build steps

1. `framework/fleet-collector/` scaffold: `pyproject.toml`, `pytest.ini`, `README.md`.
2. `src/loam/fleet_collector/_liveness.py` — copy the sibling's shared-probe import
   (`parents[4]/tools/handsoff-loop/src`).
3. `src/loam/fleet_collector/collector.py` — `collect_fleet(roots)` + `FleetRun`:
   discover run dirs, tolerant JSONL read (AC.FLEET.2), stage/elapsed/objective/cost
   derivation, `alive` via reused probe.
4. `src/loam/fleet_collector/__main__.py` + `__init__.py` — CLI production entry
   (`python -m loam.fleet_collector --root ... --out ...`).
5. `tests/` — `conftest.py` + `test_AC_FLEET_1_*`, `test_AC_FLEET_2_*`, `test_AC_FLEET_3_*`.
   Every AC test drives the real entry point (`collect_fleet`/`main`) against fixtures;
   dead/completed fixtures aged via `os.utime` so alive/dead is genuinely exercised.
6. `pip install -e`, import from `/tmp`, `pytest`, pyright, commit on
   `feat/ws-a2-fleet-collector`.

## 7. Halt triggers

- Any edit that would touch a sealed component, `handsoff-loop`/`subloam-driver` source,
  or `.claude/settings.json`.
- An AC that would ship partial — name the gap, do not weaken the AC.
- A surrounding-code ODD violation surfaced during the build.
