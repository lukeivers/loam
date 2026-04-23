# Amendment #16 — D12 chaos-durability split pytest plan

**Status:** plan (written before any test edit, per plan-before-code CDC).
**Branch:** `pos-v2` at HEAD `1b144f6` (pyyaml-reachability seal — amendment #5 follow-up's seal commit).
**Amends:** `memory-system/tests/` — adds pytest surface for D12 (Kuzu chaos-durability). Test-only. Zero `memory-system/src/` edits. Zero `memory-system/scripts/chaos_durability.py` edits.
**Motivation:** D12 is a named acceptance criterion in `docs/rebuild/components/memory-system/brief-full-build.md` (lines ~110–119). The runner (`memory-system/scripts/chaos_durability.py`) ships; the 2026-04-18 report (`memory-system/docs/chaos-durability-report.md`) + three `data/runs/chaos_durability_*.json` artifacts show all three scenarios passing. But no pytest test asserts D12 under the `test_D12_*` naming contract. Under ODD §8.2 rule 9, a standalone runner script is not a regression surface — the test suite must be able to re-prove the AC. Amendment #16 closes the coverage gap.

D12's AC covers three sub-behaviours: kill-mid-ingest produces clean-rollback or recoverable-WAL (never corrupted); kill-mid-query produces no state change (reads idempotent); WAL-recovery replays committed state on restart. The runner already encodes all three as async `scenario_*` functions and produces a JSON report at `data/runs/chaos_durability_<ts>.json`. This amendment adds pytest wrappers that invoke the runner and assert the outcome — plus a fast bucket that protects the durability-adjacent config defaults.

---

## 1. Objective

Add `memory-system/tests/test_D12_chaos_durability.py` mapping D12 to two test surfaces per prior Luke ruling ("option c — split"):

1. **Fast bucket (default-on):** in-process assertions that the `make_kuzu_driver` factory produces a driver with the durability-posture defaults D12 depends on. These protect the config surface against silent regression in day-to-day dev. Every `pytest memory-system/` run executes them.
2. **Slow bucket (marked-slow, default-off):** one pytest test that invokes `chaos_durability.main()` end-to-end and asserts `overall_passed == True` plus per-scenario verdicts by parsing the runner's JSON report. Skipped by default; runs under `pytest -m slow`.

## 2. Scope

**Primary surface:** `memory-system/tests/test_D12_chaos_durability.py` (new file).

**Marker registration:** memory-system has no `pyproject.toml`, no `pytest.ini`, no `conftest.py`, no existing marker registration. `grep @pytest.mark` across `memory-system/tests/` returns only `@pytest.mark.asyncio`. There is no prior `slow` or `durability` marker to reuse. Amendment adds `memory-system/tests/conftest.py` (new file) registering the `slow` marker via the `pytest_configure` hook. Chosen over `pyproject.toml` creation because a one-line `conftest.py` is narrower scope, and no other pytest config needs to land. Marker name: `slow` (generic, widely recognised, matches the common pytest convention described in pytest docs).

**Secondary surfaces (bookkeeping):**
- `memory-system/tests/test_no_sealed_amendments.py` — advance `BASELINE` from `fd7c6cf` to `1b144f6`; extend the BASELINE-history comment block with this amendment's narrative. No `allowed_prefixes` change (the existing tuple already admits `memory-system/` + `docs/rebuild/plans/` + `data/`).
- `memory-system/tests/SEAL_COMMIT` — sidecar bump to the amendment commit SHA (seal-commit step).
- `hands-off-lifecycle/tests/test_cross_cutting.py` — `BASELINE` advance from `fd7c6cf` to `1b144f6`; extend the BASELINE-history comment block. No `allowed` top-level set change (`memory-system` already admitted).
- `hands-off-lifecycle/tests/SEAL_COMMIT` — sidecar bump mirroring memory-system.
- `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run` — append an amendment-cycle narrative note.
- `docs/rebuild/plans/d12-chaos-durability-split-pytest.md` — this plan.

**Not touched:**
- `memory-system/src/*` — zero implementation edits.
- `memory-system/scripts/chaos_durability.py` — zero edits. The runner ships; this amendment adds test surface only.
- `memory-system/docs/chaos-durability-report.md` — left as narrative proof of the 2026-04-18 baseline run.
- Any other sealed component's src or tests.

## 3. Test names + assertion shapes

All names start with `test_D12_` so grepping by D12 finds them all.

### 3.1 Fast bucket — `test_D12_*` (default-on)

D12's three sub-behaviours all depend on specific Kuzu durability-posture defaults surfaced by `make_kuzu_driver`. The fast tests assert these defaults without subprocess or SIGKILL.

#### 3.1.1 `test_D12_kuzu_driver_factory_initialises_database_attribute`

Ties to: all three D12 sub-behaviours (the `_database` attribute is the workaround that prevents `add_episode` from cloning the driver per-group_id, which would break write-serialisation and thus the WAL-recovery and kill-mid-ingest guarantees — clones point at different Kuzu DB handles, invalidating the single-writer invariant the durability posture rests on).

Assertion shape:
- `make_kuzu_driver(db_path=":memory:")` returns a driver.
- `driver._database == ""` (matches `get_default_group_id(KUZU)`).
- No AttributeError on `driver._database` access.

#### 3.1.2 `test_D12_kuzu_driver_factory_wires_build_indices_override`

Ties to: durability-adjacent regression guard. The `build_indices_and_constraints` override is the FTS-index wiring D12's scenarios depend on (the seed+query worker scenarios run real search queries; without FTS the query worker fails before the SIGKILL, invalidating the kill-mid-query assertion). Also the override is idempotent (swallows "already exists") — a reopen after WAL-replay retriggers index-build, and a non-idempotent wiring would fail the second open.

Assertion shape:
- `make_kuzu_driver(db_path=":memory:").build_indices_and_constraints` is callable and is NOT the graphiti-core 0.28.2 `pass` no-op (verified by checking the method's module attribution or its closure).
- Two sequential `await driver.build_indices_and_constraints()` calls on the same driver both succeed (idempotency proof). Uses `pytest.mark.asyncio`.

#### 3.1.3 `test_D12_prepare_graphiti_wires_retention_column_hook`

Ties to: D12's kill-mid-ingest scenario specifically. The retention-column hook (`ensure_retention_column`) runs at `prepare_graphiti()`; if it were missing, an ingest-mid-kill on a fresh DB could leave the Episodic table without the `retention_class` column, and a reopen's `MATCH (e:Episodic) RETURN ...` would fail. The hook being wired is the necessary-and-sufficient precondition for D12's reopen-counts-episodes verification.

Assertion shape:
- `prepare_graphiti` source references `ensure_retention_column` (imported inside the function body per the live source; verify by reading the function's `__code__.co_names` or by `inspect.getsource`).
- Running `prepare_graphiti(g)` on a fresh `:memory:` graphiti instance does not raise, and a subsequent `ALTER TABLE Episodic ADD IF NOT EXISTS retention_class STRING DEFAULT 'normal'` via the same driver is a no-op (column already present post-`prepare_graphiti`). Uses `pytest.mark.asyncio`.

### 3.2 Slow bucket — `test_D12_chaos_durability_runner_reports_all_scenarios_pass` (marked `slow`)

Ties to: D12's full AC. Invokes the runner's `main()` via `asyncio.run(chaos_durability.main())`, then parses the most recent `data/runs/chaos_durability_*.json` report (sorted by filename — the runner uses `int(time.time())` as the suffix so lexical sort = temporal sort at second-granularity; ties broken by mtime).

Decorator: `@pytest.mark.slow`. Module-level.

Assertion shape:
- `await chaos_durability.main()` returns `0` (runner's own exit code convention for pass).
- Locate the newest report: `sorted(RUNS_DIR.glob("chaos_durability_*.json"), key=lambda p: p.stat().st_mtime)[-1]`.
- Parse JSON. Assert `payload["overall_passed"] is True`.
- Assert `{s["name"] for s in payload["scenarios"]} == {"kill_mid_ingest", "kill_mid_query", "wal_recovery"}` (exactly these three, no more no less — named-AC-sub-behaviours only).
- Assert every scenario has `passed is True`.
- Imports `scripts/chaos_durability.py` (per the cached sys.path bootstrap the runner itself does at module load — same path manipulation; no subprocess invocation). Verified: `import chaos_durability` from a `sys.path.insert(0, str(MEMORY_SYSTEM / "scripts"))` context succeeds with no side effects beyond the module's own `sys.path.insert` + factory imports.

Runtime budget: ~65s (2026-04-18 report shows ~56s across three scenarios; pytest overhead negligible). Not fit for default CI; hence `-m slow`.

**Runner precondition (environment, not AC):** the runner's worker subprocesses call `make_graphiti` which constructs a `ClaudePrintLLMClient` and probes OAuth state at construction time (`ClaudeUnauthenticatedError` otherwise). This is a runner-precondition, not a D12 sub-behaviour. The slow test gates on `_claude_oauth_available()` and `pytest.skip`s with a clear message if auth is absent — so unauthenticated environments (agent sessions, fresh clones without `claude /login` run) produce a skip rather than a false failure. On Luke's authenticated workstation the probe passes and the full runner executes. D12's AC covers Kuzu durability (clean-rollback, recoverable-WAL, idempotent reads on kill-mid-query), not LLM subprocess auth; the precondition skip keeps the failure mode honest.

### 3.3 Test function names summary

Fast bucket (3 tests):
- `test_D12_kuzu_driver_factory_initialises_database_attribute`
- `test_D12_kuzu_driver_factory_wires_build_indices_override`
- `test_D12_prepare_graphiti_wires_retention_column_hook`

Slow bucket (1 test):
- `test_D12_chaos_durability_runner_reports_all_scenarios_pass`

## 4. Test-count delta

- `memory-system/` default run (excludes `-m slow`): 67 → 70 (+3 fast tests).
- `memory-system/` with `-m slow`: 67 → 71 (+3 fast +1 slow).
- `hands-off-lifecycle/`: 66 → 66 (unchanged — BASELINE + narrative edits only).
- All other sealed components: unchanged.

## 5. BASELINE advances

- `memory-system/tests/test_no_sealed_amendments.py`: `fd7c6cf` → `1b144f6` (the pre-amendment tip — pyyaml-reachability amendment #5 follow-up's seal commit immediately before this amendment's code commit).
- `hands-off-lifecycle/tests/test_cross_cutting.py`: `fd7c6cf` → `1b144f6` (same pre-amendment tip).

No other BASELINE advances.

## 6. Marker cadence (critical — F3 concern)

A mark-slow test with no documented run cadence is dead weight. The `test_D12_chaos_durability_runner_reports_all_scenarios_pass` test runs:

1. **Manually before any pos-v2 release cut.** Release-cut discipline is human; this is the first checkpoint.
2. **On any PR whose diff touches** `memory-system/src/factory.py`, `memory-system/src/retention.py`, or any kuzu-adjacent surface in `memory-system/src/` (retention.py's `ensure_retention_column`, factory.py's `make_kuzu_driver` / `make_graphiti` / `prepare_graphiti`, memory.py's ingest path, drain.py's retention-class application). No CI automation promised — this is a human-discipline checkpoint recorded rather than implicit.

### 6.1 Runbook

```bash
cd memory-system
.venv/bin/pytest -m slow tests/test_D12_chaos_durability.py -v
```

Expected runtime ~65s. Expected output: 1 passed. On failure, investigate the runner's stdout — scenario verdicts print inline, and the JSON report under `data/runs/chaos_durability_<ts>.json` captures per-scenario observations. A failure indicates a real durability regression; do not mark as flake without root-cause analysis.

## 7. Halt triggers

- [ ] `scripts/chaos_durability.py` is not importable from pytest (module-level side effects at import).
- [ ] The marked-slow test fails (indicates a real durability regression or flakiness — investigate before deciding if it's this amendment's bug or an upstream issue).
- [ ] Scope cascades beyond `memory-system/tests/` + plan doc + hands-off-lifecycle BASELINE/seal.
- [ ] `make_kuzu_driver`'s current config doesn't satisfy D12's durability preconditions (indicates a structural defect, not a test-coverage gap — halt and flag).

Halt-check status recorded at plan-writing time:
- chaos_durability importability: VERIFIED (`.venv/bin/python -c "import chaos_durability"` succeeds from `scripts/`; `dir()` exposes `main`, `scenario_*`, `CHAOS_EPISODES` with no side effects beyond the module's intentional `sys.path.insert` + factory imports).
- fast-bucket preconditions: VERIFIED by reading `memory-system/src/factory.py` lines 103–164 + `memory-system/src/retention.py` lines 132–145. `_database = ""` initialised at line 132; `build_indices_and_constraints` override at line 141 with idempotent "already exists" swallow; `prepare_graphiti` imports `ensure_retention_column` at runtime (line 218) and awaits it at line 221.
- scope whitelist: verified against the plan's "Not touched" section.

## 8. Commit structure

Two commits (no amends):

1. **Amendment commit** — `fix(memory-system, hands-off-lifecycle): D12 chaos-durability split pytest (amendment #16)` — includes the new test file, new `memory-system/tests/conftest.py` registering the `slow` marker, BASELINE bumps in both sealed-component seal tests, BASELINE-history comment blocks, this plan doc. All test suites green before commit:
   - memory-system default run: 67 → 70 passing + 1 skipped (the slow test is auto-skipped when no marker expression is in play — see `tests/conftest.py` `pytest_collection_modifyitems`).
   - memory-system `-m slow`: 1 test selected (passes on Luke's auth'd workstation; skips with a precondition message when run in an un-authed environment — auth is runner-precondition, not D12 AC).
   - hands-off-lifecycle: 66 passing.
   - All other sealed components' `test_no_sealed_amendments.py`: green (their SEAL_COMMIT sidecars unchanged).

2. **Seal commit** — `chore(seals): d12-chaos-durability-split-pytest seal — memory-system + hands-off-lifecycle at <amendment-sha>` — bumps `memory-system/tests/SEAL_COMMIT` and `hands-off-lifecycle/tests/SEAL_COMMIT` to the amendment commit's SHA; appends the amendment-cycle narrative to `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run`. Tests green again against the bumped sidecars.
