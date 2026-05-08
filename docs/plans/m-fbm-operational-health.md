# M-FBM operational-health amendment — `AC.MFBM-OPS.*`

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-04.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Trigger:** Diagnosis at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/m-fbm-operational-failure-diagnosis-2026-05-04.md` — Luke's M-FBM worker died on 2026-05-01, never restarted, accumulated 175-item queue backlog over 3 days. Test suite passed throughout (structural ACs only — `plist file shape`, `drain code paths in isolation`); no operational-health ACs (queue stability, worker liveness, recent-episode floor, plist-Label namespacing, worker heartbeat).
**Programme master:** `docs/plans/v0-1-x-roadmap.md` §8 v0.1.x sealed-amendment register (this amendment to be backfilled at completion).

---

## 1. Summary / TL;DR

Sealed-component amendment that adds operational-health AC coverage to the M-FBM substrate so the silent-worker-death failure mode (the queue still drains structurally, the writer still enqueues, the tests still pass — but no episode files reach disk) is caught by tests, not by Luke noticing stale retrieval surfaces three days later.

Five ACs in a new family `AC.MFBM-OPS.*`:

1. **AC.MFBM-OPS.1** — queue stability under sustained load (post-drain queue depth < threshold after N enqueues).
2. **AC.MFBM-OPS.2** — worker-liveness check (post-bootstrap, the workspace-slug-namespaced launchd Label appears in `launchctl list`).
3. **AC.MFBM-OPS.3** — recent-episode floor (within K minutes of session activity, an episode file exists for the most-recent turn-id).
4. **AC.MFBM-OPS.5** — workspace-slug-namespaced plist Label (test asserts the generated Label matches `com.loam.<slug>.memory-write-worker`, never the generic `com.loam.ws.memory-write-worker`).
5. **AC.MFBM-OPS.6** — worker-heartbeat instrumentation (worker emits `kind: "worker-heartbeat"` log entries every N seconds; test asserts ≥1 heartbeat in a short-window fixture).

**Why a sealed amendment:** the M-FBM substrate is sealed (FBE.7 narrative anchor; `AC.MFBM.*` family lives in `framework/primary-persona/`). Adding new ACs to that family is the canonical sealed-component-extension shape (cf. amendments #34, #45, #67 — same component, new test, new AC, manifest-driven seal).

**Sealed-component fence (verified at sub-plan time):**
- `framework/primary-persona/` — M-FBM worker source + new tests for AC.MFBM-OPS.{1,2,3,6}. Fence component owns the worker code (`memory_write_worker.py`) the AC-family targets.
- `framework/workspace-bootstrap/` — new test for AC.MFBM-OPS.5 (plist-Label namespacing). Fence component already owns the plist generator (`first_run_scaffold.py` `service_label("memory-write-worker", slug)`); test only.

Every edit maps to a named AC. ODD §2.5 negative AC: nothing else.

---

## 2. Halt-and-surface BEFORE build

### Surface #1 (HALT — dispatch-relative scope correction)

The dispatch said the fence is `framework/framework/memory-system/`. The actual code involved lives in two components:
- `framework/primary-persona/` — owns `memory_write_worker.py` + the existing `AC.MFBM.*` test family (`tests/test_AC_MFBM_*.py`).
- `framework/workspace-bootstrap/` — owns `first_run_scaffold.py` + the plist generator + the existing `test_AC_J_5_memory_write_worker_plist.py` plist-Label test.

`framework/memory-system/` is the graphiti-side service component (sealed at `a5469f2e8e24...`); it does NOT own the worker source or plist generator. Editing its `tests/` directory would not exercise the worker the dispatch's diagnosis identifies as the failure surface.

**Resolution (autonomous, builder's call per ODD §1.1, surfaced for transparency):** scope this amendment to `framework/primary-persona/` (4 of 5 ACs) + `framework/workspace-bootstrap/` (AC.MFBM-OPS.5 only). Both are existing sealed components; the AC family lives in primary-persona where the existing `AC.MFBM.*` tests live; OPS.5 lives in workspace-bootstrap because that's where the plist Label is generated.

### Surface #2 (HALT — ground-truth check on the dispatch's plist-collision hypothesis)

The dispatch's diagnosis hypothesised:
> Generic `com.loam.ws.memory-write-worker` Label is hijackable; FBE.10's test plist hijacked the production Label; fix is to namespace the Label by workspace slug.

Empirical findings at sub-plan time (`ls ~/Library/LaunchAgents/`, `launchctl list`, read `~/Library/LaunchAgents/com.loam.pos3.memory-write-worker.plist`):

1. **Workspace-slug Label namespacing already exists in code.** `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py` line 237: `service_label(kind, slug)` returns `f"com.loam.{slug}.{kind}"`. Implemented in amendment #6 (per the comment on line 124).
2. **Production plist on Luke's machine is correctly namespaced** as `com.loam.pos3.memory-write-worker.plist` (slug = `pos3` from the workspace basename `/Users/lukeivers/pos3`).
3. **No file `com.loam.ws.memory-write-worker.plist` exists on disk.** The diagnosis was incorrect about that filename. The actual production plist is correctly namespaced.
4. **The 13 leftover plists in `~/Library/LaunchAgents/`** are amendment-test-fixture plists with names like `com.loam.loam-fbe10-smoke-ws.memory-write-worker`, `com.loam.test-fbe5-ws.memory-write-worker`, etc. — different slugs (test-workspace basenames), no Label collision with production. They are litter, not collisions.
5. **Worker is alive at sub-plan time.** PID 56723 in `launchctl list`; recent `worker-ok` entries in `memory-writes.log` at 2026-05-04T12:33:19. The 175-item backlog has drained (queue depth = 0).

**Implication:** AC.MFBM-OPS.5 as written is still useful — it locks in the existing namespacing as a tested invariant. The Label generator is correct; without an explicit AC, a future amendment could regress it silently. The AC.MFBM-OPS.5 test is **regression-prevention**, not bug-fix-verification. The dispatch's "fix the Label template" code change is **not required** — code already does this.

**FIDRAFT for the actual leftover-plists problem** (separate, non-blocking): the amendment-test-fixture plists are litter, not collisions. A sweeper CLI subcommand that evicts orphan `com.loam.*-test-ws.*` and `com.loam.*-smoke*.memory-write-worker` plists from `~/Library/LaunchAgents/` is a useful follow-on but out of scope for this amendment. Captured as FIDRAFT per the dispatch.

### Surface #3 (no halt — recorded; AC count narrowed from dispatch's 5 to 5)

Dispatch listed AC.MFBM-OPS.{1,2,3,5,6} (skipped 4 and 7 explicitly). This plan keeps exactly that set. AC.MFBM-OPS.4 (retrieval quality / non-probe-episode floor) is a soft objective that's hard to deterministically test; deferred. AC.MFBM-OPS.7 (reboot resilience via bootout+bootstrap cycle) needs full launchctl integration which is fragile in CI; deferred.

### Surface #4 (no halt — recorded; heartbeat instrumentation has no pre-existing pattern)

Reading `memory_write_worker.py`: the diagnostic-log shape uses NDJSON `kind:` discriminators (`worker-start`, `worker-ok`, `worker-retry`, `worker-deadletter`, `worker-skip`, `worker-exit`). The current loop emits `worker-start` once at startup + per-entry events during drain + `worker-exit` at clean shutdown. **There is no periodic liveness emission.** A worker that drains an empty queue forever produces only one log line (`worker-start`); the 5-line / 3-day log Luke saw on 2026-05-01–04 is consistent with this.

The new heartbeat is a clean addition: emit `kind: "worker-heartbeat"` with `pid` + `iteration` + `ts` + `queue_depth` (cheap — `len(list(queue_dir(...).iterdir()))`) every N seconds (default 60). Goes through the existing `_append_diag` helper. No log-rotation conflict (no rotation in the current code; daemon-controlled by launchd's StandardOut/ErrorPath which have no rotation either — that's a separate FIDRAFT-worthy item but not blocking).

### Surface #5 (no halt — recorded; sustained-load fixture stability)

The dispatch's halt trigger calls out flakiness risk on the AC.MFBM-OPS.1 sustained-load fixture. The plan tests the fixture directly: enqueue N=10 turns synthetically, call `drain_once` once with the file-backed memory client (no MCP — local stat + write only), assert queue depth = 0. No timing dependency, no background process, no flaky launchctl interaction. Deterministic.

If the fixture is run as a multi-second background test, it would be flaky; this design avoids that by driving `drain_once` directly. The AC text below pins this — drain-step count, not wall-clock time.

### Surface #6 (no halt — recorded; sealed-component apply mechanics)

Per `feedback_dispatch_explicit_pos_amend_apply` + recent FBE precedents: `loam amend apply` will advance both component sidecars (primary-persona + workspace-bootstrap) + may auto-commit (per FBE.6b/FBE.9 pattern, sometimes manual commit needed). Will `apply` then `seal`. New corrective commits if needed; NEVER `--amend`.

### Surface #7 (no halt — recorded; FIDRAFT entry for plist-collision FIDRAFT)

Per dispatch + the corrective findings in Surface #2 above, the FIDRAFT entry will document:
- The original hypothesised collision (generic Label being hijackable) — and the empirical finding that namespacing was already in place.
- The actual remaining issue (leftover amendment-test plists clutter `~/Library/LaunchAgents/` but don't collide).
- The follow-on item: stale-amendment-plist sweeper CLI subcommand.

This is more accurate than the dispatch's framing and avoids enshrining the collision misdiagnosis in the canonical FIDRAFT.

---

## 3. Spec-objective placement

**Binds to:**
- **AC.PO.1 + AC.PO.2** (prime objective per `docs/VALUE_PROPOSITION.md`) — M-FBM is the v0.1.0 memory-substrate floor; if the worker dies silently and tests pass, the primary-persona's working memory is broken without observable signal. Operational-health ACs ensure tests fail when the substrate is operationally broken.
- **`AC.MFBM.*` family** (existing — `framework/primary-persona/tests/test_AC_MFBM_*.py`) — this amendment extends the family with `AC.MFBM-OPS.*` for the operational-health gap.
- **`feedback_loose_AC_text_fix_AC_not_implementation` / ODD §4 (re-extension after build):** the existing `AC.MFBM.*` ACs are about memory-system shape correctness; the missed dimension is operational health. New AC family, not amendments to existing ACs.

**Ladders to:** `AC.MFBM-OPS.*` → `AC.MFBM.*` → AC.M.* prime-persona memory contract → AC.PO.{1,2}.

---

## 4. Acceptance criteria (`AC.MFBM-OPS.*`)

AC family `AC.MFBM-OPS.*` — collision-safe (verified: `grep -rn "AC.MFBM-OPS\|AC_MFBM_OPS" framework/` returns 0 hits).

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.MFBM-OPS.1** (queue stability under sustained load) | A test enqueues N=10 synthetic turns into the queue, runs `drain_once` once with the file-backed memory client, and asserts the post-drain queue directory is empty. The drain returns `counters["ok"] == 10`; no entries in `retry`, `deadletter`, `skipped-no-client`, `corrupt`. Catches: a worker whose drain loop processes the first entry then bails before completing the queue. | `pytest framework/primary-persona/tests/test_AC_MFBM_OPS_1_queue_stability_under_load.py -x -q` exits 0. The test creates a `tmp_path` workspace, enqueues 10 entries via `memory_write_queue.enqueue_episode`, calls `memory_write_worker.drain_once` with `client_factory=build_file_backed_memory_client`, asserts `counters == {"ok": 10, "retry": 0, "deadletter": 0, "skipped-no-client": 0, "corrupt": 0}` and `len(list(queue_dir(ws).iterdir())) == 0`. Pure file-backed; no network, no launchd, no timing. |
| **AC.MFBM-OPS.2** (worker liveness — slug-namespaced Label) | A test verifies that `service_label("memory-write-worker", slug)` for a non-trivial slug returns the slug-namespaced reverse-DNS Label that launchd uses. Catches: a regression that reverts to a generic Label, breaks slug derivation, or removes the kind from `_SERVICE_KINDS`. **Note:** this AC verifies the function-level contract, NOT a live `launchctl list` call (which is non-hermetic + unavailable in CI). The diagnostic value is "if this regresses, the workspace-slug protection regresses." | `pytest framework/primary-persona/tests/test_AC_MFBM_OPS_2_worker_liveness_label_contract.py -x -q` exits 0. The test imports `loam.workspace_bootstrap.adapters.first_run_scaffold.service_label`, asserts `service_label("memory-write-worker", "pos3") == "com.loam.pos3.memory-write-worker"` and the same for two additional slugs (`alpha-ws`, `prod-canonical`); asserts `service_label("memory-write-worker", "")` raises (empty slug should not produce a generic Label silently). |
| **AC.MFBM-OPS.3** (recent-episode floor) | A test enqueues a single episode at time T, runs `drain_once` with the file-backed client, then asserts an episode file exists in the file-memory store directory with mtime within a short delta of T. Catches: a worker that returns "ok" but doesn't actually write the episode to disk (e.g., a regression in `file_memory.add_episode` that silently no-ops). | `pytest framework/primary-persona/tests/test_AC_MFBM_OPS_3_recent_episode_floor.py -x -q` exits 0. The test (a) records `t_before = time.time()`, (b) enqueues one synthetic turn via `memory_write_queue.enqueue_episode`, (c) calls `memory_write_worker.drain_once` with `client_factory=build_file_backed_memory_client`, (d) inspects the file-memory store directory (resolved via `file_memory._episode_store_dir`), asserts ≥1 file exists whose mtime is ≥`t_before`. |
| **AC.MFBM-OPS.5** (plist Label is workspace-slug-namespaced) | A test (in `framework/workspace-bootstrap/tests/`, where the existing plist tests live) verifies the FIRST-RUN-SCAFFOLD-generated plist's Label content matches the slug-namespaced shape. Specifically: when run with workspace basename `pos3`, the generated plist contains `<key>Label</key><string>com.loam.pos3.memory-write-worker</string>`. Catches: a regression that re-introduces a generic `com.loam.ws.memory-write-worker` Label or the workspace-slug derivation breaks. **Note:** existing test `test_AC_J_5_memory_write_worker_plist.py` exercises this implicitly via `service_label` indirection; new test pins it explicitly with the regression-named AC. | `pytest framework/workspace-bootstrap/tests/test_AC_MFBM_OPS_5_plist_label_workspace_slug.py -x -q` exits 0. The test mirrors `test_AC_J_5_distinct_workspaces_get_distinct_worker_labels` shape — runs `run_first_run_scaffold` on a workspace named `pos3` (basename used for slug derivation), reads the resulting plist, asserts the Label string equals exactly `com.loam.pos3.memory-write-worker`. Negative assertion: `com.loam.ws.memory-write-worker` does NOT appear anywhere in the plist content. |
| **AC.MFBM-OPS.6** (worker-heartbeat instrumentation) | The worker's `run_worker_loop` emits a `kind: "worker-heartbeat"` NDJSON log entry every `heartbeat_interval_iterations` iterations (default `60` — at the default 1.0s `poll_interval_s`, that's ~60s wall-clock). Each heartbeat carries `pid`, `iteration`, `queue_depth`, `ts`. Configurable via `worker-config.yaml` `heartbeat_interval_iterations` key. Test asserts: after `max_iterations=N` (≥ heartbeat interval) drain passes against an empty queue, the log contains ≥1 `worker-heartbeat` entry with the expected fields. Catches: the 5-line-3-day failure mode Luke observed (worker drained an empty queue silently → no log lines → operator can't tell if it's alive). | `pytest framework/primary-persona/tests/test_AC_MFBM_OPS_6_worker_heartbeat_emission.py -x -q` exits 0. The test sets up an empty queue, runs `run_worker_loop` with `max_iterations=3` and `config={"heartbeat_interval_iterations": 1, ...defaults}` so each iteration emits, asserts the diagnostic log file contains ≥3 lines with `kind == "worker-heartbeat"` and each carries `pid`, `iteration`, `queue_depth`, `ts`. |

### Negative AC (ODD §2.5 — nothing else)

This amendment does NOT:
- Re-implement the worker drain-loop or change drain semantics.
- Touch the `AC.J.*` plist-shape tests (they pass; AC.MFBM-OPS.5 is additive, not replacement).
- Add a sweeper CLI subcommand (FIDRAFT-only per Surface #7).
- Add launchctl-bootstrap testing (AC.MFBM-OPS.7-deferred per Surface #3).
- Add retrieval-quality/episode-content tests (AC.MFBM-OPS.4-deferred).
- Touch `framework/memory-system/` (graphiti service; out of fence — that component does not own the failed code paths).

---

## 5. Behaviour count

| # | Declared behaviour | AC |
|---|--------------------|----|
| 1 | Queue empties under sustained N-entry enqueue load (FIFO drain) | AC.MFBM-OPS.1 |
| 2 | `service_label` returns workspace-slug-namespaced Label for valid slugs; raises on empty slug | AC.MFBM-OPS.2 |
| 3 | Single-entry drain produces a written episode file with current mtime | AC.MFBM-OPS.3 |
| 4 | First-run-scaffold-generated plist's Label string is workspace-slug-namespaced (regression-pinned) | AC.MFBM-OPS.5 |
| 5 | `run_worker_loop` emits periodic `worker-heartbeat` NDJSON log entries with pid + iteration + queue_depth + ts | AC.MFBM-OPS.6 |

5 behaviours / 5 ACs. 1:1 mapping.

---

## 6. Hard constraints

1. **No `--amend`.** Corrective new commits only. Per `feedback_no_amend_in_agent_dispatches`.
2. **Scope fence.** Two components: `framework/primary-persona/` + `framework/workspace-bootstrap/`. Per Surface #1 dispatch correction. No edits outside fence except universal-admissions (plan-doc, manifest, FIDRAFT, parent register).
3. **Plan-before-code.** This plan exists; code lands per §7 below.
4. **No new third-party dependency.** Stdlib + existing `yaml` + existing test deps only.
5. **Backward-compat preserved unconditionally.** The new heartbeat is additive (new `kind:` value); existing log readers ignoring unknown kinds continue to work. Default `heartbeat_interval_iterations=60` matches existing 1s poll → ~60s emission cadence; explicit operator config can override.
6. **CDC adherence.** Existing `AC.MFBM.*` + `AC.J.*` tests continue to pass byte-identically. New `AC.MFBM-OPS.*` tests are additive.
7. **AC family collision-safety.** `AC.MFBM-OPS.*` does not collide with `AC.MFBM.*` (verified: `grep -rn "AC.MFBM-OPS\|AC_MFBM_OPS" framework/` returns 0 pre-build).

---

## 7. Implementation order

1. Read this plan + diagnosis at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/m-fbm-operational-failure-diagnosis-2026-05-04.md`.
2. Verify ground-truth findings in Surface #2 (already done at sub-plan time; transcript captured).
3. Author manifest YAML at `docs/plans/m-fbm-operational-health.manifest.yaml`.
4. Land code changes in this order (touched-only test runs after each):
   - 4a. Add `heartbeat_interval_iterations` to `DEFAULT_WORKER_CONFIG` in `memory_write_queue.py`.
   - 4b. Add heartbeat emission to `run_worker_loop` in `memory_write_worker.py` (every `heartbeat_interval_iterations` iterations, emit `_append_diag(workspace_root, {"kind": "worker-heartbeat", ...})`).
   - 4c. Add 4 new tests in `framework/primary-persona/tests/`: `test_AC_MFBM_OPS_1_queue_stability_under_load.py`, `test_AC_MFBM_OPS_2_worker_liveness_label_contract.py`, `test_AC_MFBM_OPS_3_recent_episode_floor.py`, `test_AC_MFBM_OPS_6_worker_heartbeat_emission.py`.
   - 4d. Add 1 new test in `framework/workspace-bootstrap/tests/`: `test_AC_MFBM_OPS_5_plist_label_workspace_slug.py`.
5. Run touched-only tests: `pytest framework/primary-persona/tests/ framework/workspace-bootstrap/tests/ -x -q`.
6. Append FIDRAFT entry per §9 (universal admission).
7. Backfill parent §8 v0.1.x register row in `docs/plans/v0-1-x-roadmap.md`.
8. `loam amend apply docs/plans/m-fbm-operational-health.manifest.yaml` (auto-commit).
9. `loam amend seal docs/plans/m-fbm-operational-health.manifest.yaml` (seal commit).
10. Status file at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/m-fbm-operational-health-status-2026-05-04.md`.

---

## 8. Out of scope

- AC.MFBM-OPS.4 (retrieval-quality / non-probe-episode floor) — soft objective; hard to deterministically test. Deferred to v0.1.4+ if still needed post-this-amendment.
- AC.MFBM-OPS.7 (reboot resilience via bootout+bootstrap cycle) — needs full launchctl integration; fragile. Deferred.
- Stale-amendment-plist sweeper CLI subcommand — useful but FIDRAFT-only this cycle.
- Log-rotation for `memory-write-worker.{out,err}.log` and `memory-writes.log` — separate FIDRAFT-worthy item; not blocking the operational-health AC family.
- Changes to the plist Label generator (already correct per Surface #2).
- Changes to `framework/memory-system/` (graphiti service — wrong fence per Surface #1).

---

## 9. Bookkeeping surface (sealed-component amendment)

Manifest at `docs/plans/m-fbm-operational-health.manifest.yaml` carries:

```yaml
schema_version: 1
amendment:
  number: TBD-at-apply  # next available; query `loam amend ...` to confirm
  slug: m-fbm-operational-health
  title: "M-FBM operational-health AC family — AC.MFBM-OPS.* (queue stability, label-contract, episode-floor, plist-label-namespacing, worker-heartbeat)"

baseline: <pre-build-tip>  # filled at build time after pre-build commits land

plan: docs/plans/m-fbm-operational-health.md

seal_description: "Adds AC.MFBM-OPS.* family (5 ACs) to the M-FBM substrate's operational-health surface. AC.MFBM-OPS.1 — queue empties under N=10 enqueue load. AC.MFBM-OPS.2 — service_label returns workspace-slug-namespaced reverse-DNS Label, raises on empty slug. AC.MFBM-OPS.3 — single-entry drain produces an episode file on disk. AC.MFBM-OPS.5 — first-run-scaffold-generated plist Label is workspace-slug-namespaced (regression-pinned). AC.MFBM-OPS.6 — run_worker_loop emits periodic worker-heartbeat NDJSON entries with pid + iteration + queue_depth + ts (default every 60 iterations). Worker source change: heartbeat emission added to run_worker_loop; heartbeat_interval_iterations added to DEFAULT_WORKER_CONFIG (default 60). 5 new tests across primary-persona/ + workspace-bootstrap/. Existing AC.MFBM.* + AC.J.* tests pass byte-identically. Diagnosis trigger: Luke's worker died 2026-05-01 + drained empty 3 days; structural ACs passed throughout."

components:
  - name: primary-persona
    seal_test: framework/primary-persona/tests/test_no_sealed_amendments.py
    sidecar: framework/primary-persona/tests/SEAL_COMMIT
    frozen_baseline: false
    extra_allowed_prefixes: []
  - name: workspace-bootstrap
    seal_test: framework/workspace-bootstrap/tests/test_no_sealed_amendments.py
    sidecar: framework/workspace-bootstrap/tests/SEAL_COMMIT
    frozen_baseline: false
    extra_allowed_prefixes: []

universal_paths:
  prefixes:
    - docs/plans/
  files:
    - docs/FUTURE_IDEAS_DRAFT.md

narrative:
  target: framework/primary-persona/seals/SEAL_COMMIT.m-fbm-operational-health
  body: |
    # M-FBM operational-health amendment — apply ladder
    BASELINE <baseline-sha> → seal <seal-sha>. Two fence components:
    primary-persona advances its tests/SEAL_COMMIT sidecar (4 new tests
    + worker source heartbeat addition); workspace-bootstrap advances
    its tests/SEAL_COMMIT sidecar (1 new test pinning plist Label
    namespacing). 5 new ACs in family AC.MFBM-OPS.*. See plan-doc at
    docs/plans/m-fbm-operational-health.md and status file at
    /Users/lukeivers/pos3/workspace/.scratch/claude-output/m-fbm-operational-health-status-2026-05-04.md
    for full narrative.
```

The narrative seal-anchor file path uses primary-persona's seals dir if it exists; if not, drop to workspace-bootstrap's seals dir or a different anchor — verify at build time.

---

## 10. Halt triggers

1. Cross-component scope expansion beyond the two-component fence. Halt.
2. Backward-compat cannot be preserved (heartbeat addition breaks an existing test). Halt; surface for owner ruling.
3. ODD-violating shape becomes strongly required. Halt; owner rules.
4. New third-party dependency becomes required. Halt.
5. Wall-time exceeds 5 hours (per dispatch). Halt with current state.
6. ODD violation observed in surrounding code/docs (per `feedback_subagent_odd_violation_halt`). Halt; do NOT extend a violating surface.
7. Test fixture for AC.MFBM-OPS.1 is unstable / flaky (more than 1 retry needed during touched-only sweep). Halt + surface; recommend reducing N or moving to follow-on.
8. AC.MFBM-OPS.5 plist-Label change requires touching multiple components beyond fence. Halt + surface.
9. Heartbeat instrumentation conflicts with a pre-existing log-rotation pattern. Halt + surface.
10. `index.lock` race conflict from parallel agent C (smoke-test-discipline). Retry once after a brief wait; if still failing, halt + surface.

---

## 11. Decisions

(no genuinely uncertain decisions — listed for transparency)

| Decision | Resolution | Why it matters |
|---|---|---|
| D-1: AC family name | `AC.MFBM-OPS.*` | Collision-checked vs existing; aligns with dispatch's naming. |
| D-2: Test placement (which component) | Primary-persona for OPS.{1,2,3,6}; workspace-bootstrap for OPS.5 | Mirrors source location of the code each AC pins. |
| D-3: Heartbeat configurability | Configurable via `worker-config.yaml`'s `heartbeat_interval_iterations`, default 60 | Operator can disable (set to large int) or accelerate for diagnostics; default approximates the original 60s wall-clock spec. |
| D-4: Heartbeat unit (iterations vs seconds) | Iterations | Composable with the existing `poll_interval_s`-driven loop; keeps test-time fixtures deterministic without faking wall-clock. |
| D-5: AC.MFBM-OPS.5 — function-level vs filesystem-level | Plist filesystem-level (in workspace-bootstrap) AND label-contract function-level (AC.MFBM-OPS.2 in primary-persona) | Two distinct regression surfaces: the function contract (someone could change `service_label` semantics) AND the scaffold output (someone could bypass `service_label` and hardcode a generic Label). Both pinned. |

---

## 12. Decisions summary

| Decision | Recommendation | Why it matters |
|---|---|---|
| AC family name | `AC.MFBM-OPS.*` | matches dispatch + collision-safe |
| Heartbeat unit | iterations (not seconds) | deterministic-test-friendly |
| Plist-Label test placement | workspace-bootstrap | source-of-truth co-location |
| Out-of-scope | OPS.4, OPS.7, sweeper CLI | per Surface #3, dispatch §scope |

---

## 13. Halt findings

Per `feedback_subagent_odd_violation_halt`: halt and surface any ODD violation observed in surrounding code/docs.

**Findings (recorded, not blocking):**
1. Surface #2 above — the dispatch's plist-collision diagnosis was empirically incorrect; namespacing already exists. Does NOT block this amendment (the AC.MFBM-OPS.5 regression-test still has value); does correct the FIDRAFT entry framing in §15.
2. Surface #1 above — dispatch named `framework/framework/memory-system/` as the fence; actual fence is `framework/primary-persona/` + `framework/workspace-bootstrap/`. Resolved autonomously per ODD §1.1; surfaced for transparency.

No ODD violations observed in the surrounding code/docs that block the amendment.

---

## 14. Method-decision register

| ID | Decision | Rationale | Owner of method | Build-time confirmation |
|---|---|---|---|---|
| MD-1 | Heartbeat impl: `_append_diag` reuse | The existing diag-log helper handles atomic append + tolerates OSError; no new infrastructure. | Builder | After §7.4b |
| MD-2 | Heartbeat trigger: every `iteration % heartbeat_interval_iterations == 0` after the drain step | Matches existing `iteration % 60 == 0` cleanup pattern; no new clock concept. | Builder | After §7.4b |
| MD-3 | Test fixtures: `tmp_path` workspace + file-backed memory client | No launchctl, no MCP, no network — deterministic. | Builder | After §7.4c–4d |
| MD-4 | AC.MFBM-OPS.5 file naming | `test_AC_MFBM_OPS_5_plist_label_workspace_slug.py` parallels existing `test_AC_J_5_*.py` convention. | Builder | After §7.4d |

---

## 15. References

- `/Users/lukeivers/pos3/workspace/.scratch/claude-output/m-fbm-operational-failure-diagnosis-2026-05-04.md` — diagnosis trigger
- `framework/primary-persona/src/loam/primary_persona/memory_write_worker.py` — worker source (heartbeat target)
- `framework/primary-persona/src/loam/primary_persona/memory_write_queue.py` — queue + DEFAULT_WORKER_CONFIG (heartbeat interval add)
- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py` — `service_label` source (already correctly namespaced per amendment #6)
- `framework/workspace-bootstrap/tests/test_AC_J_5_memory_write_worker_plist.py` — existing plist-Label test (parallels new AC.MFBM-OPS.5 test)
- `framework/primary-persona/tests/test_AC_MFBM_*.py` — existing M-FBM AC family (siblings to new OPS.* family)
- `docs/plans/v0-1-0-foldback-scope-expansion-fbe7.md` — FBE.7 narrative seal anchor for M-FBM substrate
- `docs/plans/v0-1-x-roadmap.md` — parent register §8 to be backfilled at completion
- `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_loose_AC_text_fix_AC_not_implementation.md` — ODD §4 (post-build re-extension)
- `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_subagent_odd_violation_halt.md` — halt-and-surface discipline
