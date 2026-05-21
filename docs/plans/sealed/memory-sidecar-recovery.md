# Plan — memory-sidecar recovery (lifespan-leak + schema-migration)

**Status:** authored 2026-04-29 by builder (task #18 in dispatcher queue).
**Predecessor:** M9 sealed at `2161cb1` (synth-time path substitution + in-place fixture refactor).
**Successor candidates:** M1c-corrective (task #16) ; M11.dry-run (task #19).
**Authority:** dispatcher directive 2026-05-01 ("memory must be fully functional before publish — M11/M12").
**Companion research:** `.scratch/claude-output/memory-sidecar-diagnostic.md` — diagnostic-agent report 2026-04-29 with lsof leak evidence + per-session lifespan stacktrace + `add_episode` schema-mismatch capture. Research-before-plan gate is satisfied by that report; no separate research artefact authored here.

---

## 1. Summary / TLDR

Two coupled defects in `framework/memory-system/src/service.py` + the on-disk Kuzu schema. The diagnostic agent identified both. They MUST land together — fixing one alone re-triggers the other.

1. **Lifespan-leak (fix #1).** `service.lifespan()` is invoked PER MCP session by FastMCP's `StreamableHTTPSessionManager` (not once at process start). Its `finally` block at `service.py:115` sets `_graphiti = None` on every session close, defeating the `_ensure_graphiti()` guard. Each new session rebuilds the Graphiti driver, opening another `kuzu.Database` against the same on-disk file. Kuzu's 8 TiB virtual mmap reservation accumulates per session; mmap eventually fails on macOS VA fragmentation; sidecar enters permanent stuck state returning 503 forever. **Fix:** drop the `_graphiti = None` line from the `finally` block. Driver lives for process lifetime; close runs only at actual process shutdown.

2. **Schema-migration (fix #2).** `add_episode` fails with `Binder exception: Cannot find property reference_time for e.` The on-disk `kuzu_db` was created against an older `graphiti-core` whose `RelatesToNode_` schema lacked `reference_time TIMESTAMP`. Current `graphiti-core` 0.28.x writes that column; `CREATE NODE TABLE IF NOT EXISTS` in the driver's static schema is a no-op when the table already exists, so the column never gets retro-added. **Fix:** idempotent `ALTER TABLE RelatesToNode_ ADD IF NOT EXISTS reference_time TIMESTAMP` on each boot, alongside the existing `ALTER TABLE Episodic ADD IF NOT EXISTS retention_class STRING DEFAULT 'normal'` D10 migration. Kuzu 0.11+ supports `ADD IF NOT EXISTS` (verified empirically — see §2.4).

The fixes interact: any rebuild-from-`episodes.json` path would tear down + reinitialize the driver, re-triggering fix #1's leak. So: ALTER TABLE (not rebuild) is the right shape for #2; #1 must conceptually land first.

Operational restart via `launchctl kickstart -k gui/$UID/com.pos-v2.pos3.memory-graphiti` applies the fixes to the running pos3 sidecar; verify health 200, search OK, **`add_episode` succeeds with a small test write** (the regression that motivates this amendment).

---

## 2. Research findings (inlined)

### 2.1 Diagnostic-agent report

`.scratch/claude-output/memory-sidecar-diagnostic.md` carries the full investigation: lsof showed dozens of open FDs on `kuzu_db` and `kuzu_db.wal` from PID 94504; err.log accumulated 2.66M lines / 226 MB of the same Kuzu mmap stacktrace from 2026-04-28 17:14 onward; root-cause stacktrace at `service.py:107 in lifespan → service.py:90 in _ensure_graphiti → factory.py:255 in make_graphiti → factory.py:176 in make_kuzu_driver → kuzu/database.py:155 in init_database → RuntimeError: Buffer manager exception: Mmap for size 8796093022208 failed.`

### 2.2 Why each session re-enters lifespan (per the diagnostic)

`mcp/server/fastmcp/server.py` (mcp ≥ 1.27) wraps the user lifespan and routes it to `MCPServer.__init__(lifespan=...)`. The Starlette app's lifespan is `lambda app: self.session_manager.run()` — that's `StreamableHTTPSessionManager.run`, which sets up an anyio task group and does NOT call the user lifespan. The user lifespan is entered by `MCPServer.run` per HTTP request that opens an MCP session (`_handle_stateless_request` / `_handle_stateful_request`). So: amendment #34 added `_ensure_graphiti()` as the eager-init path at process start; that path correctly populates `_graphiti` before serve loop entry. The lifespan's `finally` block at line 115 then runs PER SESSION — undoing #34's eager init by nulling `_graphiti` on every session close.

### 2.3 Schema mismatch detail

`graphiti-core/driver/kuzu_driver.py` (installed at `/Users/lukeivers/pos3/.venv/lib/python3.13/site-packages/graphiti_core/driver/kuzu_driver.py`) lines 84-97 declare `RelatesToNode_` with `reference_time TIMESTAMP` at line 95. Kuzu's `CREATE NODE TABLE IF NOT EXISTS` is a no-op when the table exists; existing tables with older schema don't get retro-added columns. Current graphiti-core code (`graphiti_core/utils/maintenance/edge_operations.py` and similar) reads/writes `e.reference_time` — that's the Binder error in `add_episode`'s edge-write path.

### 2.4 ALTER TABLE ADD IF NOT EXISTS — empirical check

```
$ python -c "import kuzu; db = kuzu.Database('/tmp/x'); c = kuzu.Connection(db)
   c.execute('CREATE NODE TABLE IF NOT EXISTS T (uuid STRING PRIMARY KEY, foo STRING)')
   c.execute('ALTER TABLE T ADD IF NOT EXISTS bar TIMESTAMP')   # ok
   c.execute('ALTER TABLE T ADD IF NOT EXISTS bar TIMESTAMP')"  # ok (idempotent)
```

Kuzu 0.11.3 (the version pinned in both canonical and pos3 venvs) supports `ALTER TABLE ADD IF NOT EXISTS` as a true idempotent migration. The same shape is already used at `framework/memory-system/src/retention.py:127`:

```python
ENSURE_RETENTION_COLUMN_CQL = (
    "ALTER TABLE Episodic ADD IF NOT EXISTS "
    "retention_class STRING DEFAULT 'normal'"
)
```

The reference_time migration co-locates with this — same pattern, same module, same boot-time call site (`prepare_graphiti` at `factory.py:265-277`).

### 2.5 Sealed-test impact (ODD §4 in-band retire)

`framework/memory-system/tests/test_service.py:183` asserts `service._graphiti is None` after the lifespan exits (under AC24.1's name). `framework/memory-system/tests/test_AC34_eager_health_after_startup.py:293` carries the same assertion (AC34.2's pointer-to-evidence inline check).

Per `feedback_loose_AC_text_fix_AC_not_implementation`: AC24.1's actual spec text in `docs/plans/amendment-24-memory-system-mcp-migration.md` is "the lifespan context constructs Graphiti exactly once, calls `build_indices_and_constraints()`, yields, and calls `close()` exactly once on exit." The "module global cleared on exit" assertion at line 183 is over-specification beyond the AC — added as a test-side belt-and-braces in the original implementation, not as an AC outcome. AC34.2 inherits from AC24.1 and similarly asserts the same line. The fix #1 implementation matches the AC's actual spec (constructs once, builds indices, yields, closes once); the loose test assertion needs to retire to fit. This is in-band ODD §4 — implementation matches intent, AC is unchanged, only the test text moves.

Both assertions get updated in this amendment to reflect the post-fix-#1 invariant: `service._graphiti is fake` (still populated; close ran but the driver handle stays alive — `KuzuDriver.close()` may or may not unmap, but that's FIDRAFT-tracked, not load-bearing here).

---

## 3. Decisions (recommendations stated)

### D1 — Fix #2 mechanism: ALTER TABLE vs rebuild from episodes.json

**Recommendation: ALTER TABLE.** Idempotent, single-line, no driver teardown. The diagnostic's two options:

- **(a) ALTER TABLE on boot** — runs alongside the existing D10 retention-column migration in `prepare_graphiti`. Empirically idempotent (§2.4). One line. No data motion.
- **(b) Rebuild from `episodes.json`** — re-ingests every episode through the LLM; expensive (the diagnostic's add_episode test took 100s LLM round-trips before hitting the binder error); requires driver teardown + re-init which would re-trigger fix #1's leak; non-deterministic (LLM extraction varies); destructive of any non-`episodes.json`-tracked state.

(a) is structurally cleaner and bounded. Pick it.

### D2 — Where the fix #2 migration call lives

**Recommendation: extend `framework/memory-system/src/retention.py::ensure_retention_column` to a sibling helper `ensure_reference_time_column(driver)` and call both from `factory.py::prepare_graphiti`.** Co-locates with the existing D10 migration; preserves the "all schema migrations live in retention.py" surface (which the docstring at retention.py:99-101 already names as "raw Cypher because graphiti-core doesn't expose per-episode metadata"). Alternative: inline the ALTER into `factory.py::_build_indices_via_graph_ops` (rejected — that function's name is about indices, not schema migration; mixing surfaces).

A cleaner refactor would rename `retention.py` to `schema_migrations.py`, but that's out-of-scope (sealed-component rename, no immediate value, ODD §4 violation).

### D3 — Fix #2 also needs to fire on the eager-init path (`_ensure_graphiti`)

The current code calls `graphiti.build_indices_and_constraints()` inside `_ensure_graphiti` (line 91) but does NOT call `prepare_graphiti` (which is where `ensure_retention_column` lives). That's a pre-existing bug (D10's retention-class column wasn't getting added by the sidecar's startup path either; only by paths that went through `MemoryAPI`). Surface for FIDRAFT: this is a separate silent-swallow-shape ODD §2.5 violation in the sidecar's startup path. **In M-S-FIX scope: replace the `build_indices_and_constraints()` call in `_ensure_graphiti` with a call to `prepare_graphiti(...)`**, so both ensure-column migrations fire on the sidecar's boot path. This adds the reference_time migration AND closes the latent retention-class hole.

**Recommendation: in-scope.** It's one line (replace one call with another) and it's the natural call site for D2. Otherwise the migration helper exists in `retention.py` but only gets called by `MemoryAPI` ingest paths — which is not what the dispatch's "sidecar can be cold-started against existing on-disk kuzu_db without manual schema migration" objective requires.

### D4 — Test shape for fix #1

**Recommendation: in-process mock test.** Build a `FakeGraphiti`, enter `service.lifespan()`, exit it, assert `_graphiti is fake` (still populated) AND `fake.close_calls == 1`. Mirrors the AC24.1 test pattern at `test_service.py:150-183`. Subprocess-based test would require simulating the per-session lifespan invocation pattern, which the existing AC34.1 subprocess test already covers structurally — adding a second subprocess test gains no marginal coverage. The mock test is the minimum that proves the post-fix invariant.

### D5 — Test shape for fix #2

**Recommendation: in-process unit test on `ensure_reference_time_column`.** Build a kuzu in-memory database, create the `RelatesToNode_` table WITHOUT `reference_time` (simulating the older-schema state), call `ensure_reference_time_column(driver)`, assert the column exists. Call again, assert no error (idempotent). Same shape as the existing `test_retention.py` patterns.

### D6 — Sealed-component fence

**Recommendation: memory-system only.** Single sealed component. Both fixes live entirely in `framework/memory-system/src/`. No surface change to hands-off-lifecycle, workspace-bootstrap, or any other component. BASELINE = current HEAD `a31280a` (post-M9 §14 SHA backfill).

---

## 4. Acceptance criteria

AC family **AC.MS-FIX.\*** (per dispatch — doesn't collide with existing AC.M.* family). Each ACs ladders to D1 (memory-system v1.0 spec, "the service auto-starts with the system, restarts on failure, exposes a health check, and is queryable through the MCP interface") → AC.PO.1 + AC.PO.2 (prime objective per `docs/VALUE_PROPOSITION.md`).

| AC ID | Outcome | Verification |
|---|---|---|
| AC.MS-FIX.1 | Lifespan no longer nulls `_graphiti` on session close. After `async with service.lifespan(server):` exits, `service._graphiti` is still populated (the constructed instance) and `close()` was called exactly once. | `framework/memory-system/tests/test_AC_MS_FIX_lifespan_no_null.py::test_AC_MS_FIX_1_lifespan_does_not_null_graphiti_on_exit` — mock-test using FakeGraphiti. |
| AC.MS-FIX.2 | `ensure_reference_time_column` adds the `reference_time TIMESTAMP` column to `RelatesToNode_` idempotently. Call against a kuzu DB whose `RelatesToNode_` lacks `reference_time` → column appears. Call again → no error. | `framework/memory-system/tests/test_AC_MS_FIX_lifespan_no_null.py::test_AC_MS_FIX_2_reference_time_migration_idempotent` — in-process kuzu unit test. |
| AC.MS-FIX.3 | Sidecar's startup path runs both schema migrations. `_ensure_graphiti()` calls `prepare_graphiti(graphiti)` (which fires both `ensure_retention_column` and `ensure_reference_time_column`) before returning. | Source-grep `_ensure_graphiti` body for `prepare_graphiti(`; AC.MS-FIX.1's mock test additionally exercises the call path with a fake `prepare_graphiti` and asserts it fires once per `_ensure_graphiti` call when `_graphiti is None`. |
| AC.MS-FIX.4 | Sealed-test text update: `test_service.py::test_AC24_1_*` line 183 + `test_AC34_eager_health_after_startup.py::test_AC34_2_*` line 293 — the `assert service._graphiti is None` lines retire to `assert service._graphiti is fake` (post-lifespan-exit invariant under fix #1). Text-only edit; AC24.1 + AC34.2's prose ACs unchanged. | Both updated tests pass. |
| AC.MS-FIX.5 | Operational verification: post-restart, the running sidecar at `127.0.0.1:8765` returns `200 OK` from `GET /health`; MCP `mcp__memory-graphiti__health` returns `{status: ok, ...}`; MCP `mcp__memory-graphiti__add_episode` succeeds with a small test write (no Binder exception); MCP `mcp__memory-graphiti__search` returns results. | Manual MCP-tool calls during the build's verification step. Recorded in §14 D-build.MS-FIX.5. |
| AC.MS-FIX.S | `git diff --name-only BASELINE..SEAL_COMMIT` produces only paths under `framework/memory-system/` or universal-paths. | `framework/memory-system/tests/test_no_sealed_amendments.py::test_B20_*` passes against new BASELINE `a31280a`. |

---

## 5. Sealed-component fence

**Components touched (1):**

1. `framework/memory-system/` — receives:
   - `src/service.py` line 115 edit (drop `_graphiti = None`).
   - `src/service.py` line 91 edit (replace `await _graphiti.build_indices_and_constraints()` with `await prepare_graphiti(_graphiti)`; import `prepare_graphiti` from `.factory`).
   - `src/retention.py` extension: new `ensure_reference_time_column(driver)` helper + new `ENSURE_REFERENCE_TIME_COLUMN_CQL` constant.
   - `src/factory.py::prepare_graphiti` — call the new helper after the existing `ensure_retention_column` call.
   - `tests/test_AC_MS_FIX_lifespan_no_null.py` (NEW) — AC.MS-FIX.1 + AC.MS-FIX.2 + AC.MS-FIX.3 tests.
   - `tests/test_service.py` line 183 + `tests/test_AC34_eager_health_after_startup.py` line 293 (text-only edits per AC.MS-FIX.4).

**Universal admissions** (per amendment #22 ruling #3):
- `docs/plans/` — for this sub-plan + manifest.

No cross-component widening required; the seal-test's `allowed_prefixes` already includes `framework/memory-system/` (line 155).

**HC#4 byte-content invariant:** edits land in source + test files; none of these are HC#4 sample paths in the seal-fence config (verified at `framework/memory-system/tests/test_no_sealed_amendments.py` — no HC#4 sample list maintained). NO RETIRE-AND-REBASELINE.

---

## 6. Halt triggers

- HT-1: ALTER TABLE on the live sidecar's on-disk DB fails with an unanticipated error (concurrent connection, file-format incompatibility, etc.) — surface specific case for re-scope.
- HT-2: `prepare_graphiti` injection into `_ensure_graphiti` breaks a sealed test beyond AC.MS-FIX.4's two named lines — surface for ODD §4 expansion vs re-scope decision.
- HT-3: Lifespan teardown without `_graphiti = None` exposes a test that asserts on the null state somewhere OTHER than the two named lines — surface for additional in-band retire.
- HT-4: ODD §2.5 violations in surrounding memory-system source surfaced while applying graceful-fallthrough-with-detection CDC retroactively — note them but DO NOT expand scope to fix; capture for FIDRAFT (per dispatch halt-and-surface trigger #5).
- HT-5: Operational restart applies the fix but post-restart `add_episode` still fails — surface specific cause; the fix may need iteration.
- HT-6: Schema-migration touches surfaces beyond expected (e.g. needs migration framework, not just an ALTER) — re-scope per dispatch HS#3.
- HT-7: HC#4 byte-content invariant breach — escalate.
- HT-8: Wall-clock approaches 90 min — surface for continuation rather than stalling.

---

## 7. Ship shape (commit ladder)

1. **Sub-plan + manifest commit.** This file + `memory-sidecar-recovery.manifest.yaml`. Message: `docs(plans): memory-sidecar-recovery sub-plan + manifest`.
2. **Feature commit.** Both fixes + new tests + sealed-test edits in one commit (the surfaces are coherent — both fix the running sidecar; lift them together). Message: `feat(memory-system): lifespan-leak fix + reference_time schema migration`.
3. **Apply commit.** `loam amend apply --plan-doc /Users/lukeivers/ivers-corp-pos-v2/docs/plans/memory-sidecar-recovery.manifest.yaml` — runs against the plugin-side `loam-amend` package (post-M6b.1). Updates objective-tracker (no objectives declared in manifest; no-op) + applies any apply-step renames (none expected). Message auto-generated: `chore(loam-amend-apply): loam amend apply for memory-sidecar-recovery`.
4. **Seal commit.** `loam amend seal --plan-doc <abs-path>` runs against plugin-side binary. Records SHA in §14 register; seal-test passes against BASELINE `a31280a`. Message auto-generated: `chore(seals): memory-sidecar-recovery — lifespan-leak + reference_time schema migration ...`.
5. **§14 SHA backfill commit.** `docs(plans): record memory-sidecar-recovery commit SHAs in §14 method-decision register`. Per recent amendments' pattern.

No `git commit --amend` per `feedback_no_amend_in_agent_dispatches`. Corrective commits if tests fail post-feature: NEW commits, never amend.

**Operational restart** (between steps 4 and 5):

```bash
launchctl kickstart -k "gui/$UID/com.pos-v2.pos3.memory-graphiti"
```

This replaces the running pos3 sidecar with a fresh one running the post-fix code. The pos3 venv at `/Users/lukeivers/pos3/.venv` imports `src.service` from `/Users/lukeivers/pos3/framework/framework/memory-system/src/service.py` (per the plist `WorkingDirectory`); the canonical edits at `/Users/lukeivers/ivers-corp-pos-v2/framework/memory-system/src/service.py` need to be visible to that pos3 path. Builder: verify the pos3 path is a sync target of the canonical pos-v2 worktree (workspace-sync should propagate framework/ edits into pos3/framework/framework/ — see `workspace/.pos/sync/state.yaml` in pos3); if not, the operational restart applies the fix only after the next sync cycle. Surface accordingly.

---

## 8. Out of scope (per dispatch + named here)

- Per-session lifespan model (FIDRAFT-tracked structural concern; deferred to v0.1.1+ — even with the singleton fix, the per-session enter is wasted work on the construct side and slightly risky on the destruct side).
- Log rotation for `graphiti-service.err.log` (FIDRAFT-tracked; ~226 MB at last check).
- launchd label `com.pos-v2.*` → `com.loam.*` rename (M1c-corrective task #16; separate amendment — the canonical plist at `framework/memory-system/launchd/com.loam.memory-graphiti.plist` is already renamed; only the pos3 workspace's installed plist still carries the old label).
- `KuzuDriver.close()` unmap verification (FIDRAFT-tracked; not blocking memory recovery — even if close is a no-op, the singleton lives forever per-process, which is fine post-fix-#1).
- `_register_custom_routes` ODD §2.5 review (the 503 fall-through when `_graphiti is None` is a legitimate state-check, not a silent swallow — but if any related silent-swallow patterns surface in surrounding source while editing, capture for FIDRAFT per HT-4 / dispatch trigger #5).
- M6c's graceful-fallthrough-with-detection CDC retroactive operationalisation across memory-system (FIDRAFT-tracked; out of scope per dispatch trigger #5).
- D10's retention-class column migration on the sidecar's boot path was previously latent (only `MemoryAPI` ingest paths called `prepare_graphiti`); fix #1's D3 ruling closes this hole AS A SIDE EFFECT of routing `_ensure_graphiti` through `prepare_graphiti`. If retention-class column now gets added to the running pos3 DB, that's a desired secondary outcome — not an objective of this amendment but worth noting.

---

## 9. Backwards-compat verification

- The lifespan's `try/finally` shape preserves; only the inner `_graphiti = None` line drops. `close()` still runs on lifespan exit; fail-closed semantics preserved.
- `_require_graphiti()` raises if `_graphiti is None`; tool implementations preserve their pre-fix surface. Post-fix the null state is unreachable in production (eager init populates it; lifespan exits don't null it; the only null state is pre-startup or post-actual-shutdown, neither of which serves requests).
- `prepare_graphiti(graphiti)` is async + idempotent (per its docstring). Calling it where `build_indices_and_constraints()` was previously called preserves the build-indices behaviour and ADDITIONALLY runs the two schema migrations.
- The new `ensure_reference_time_column` helper is idempotent (Kuzu's `ALTER TABLE ADD IF NOT EXISTS` on 0.11+); safe across cold starts.
- Existing `test_AC34_1_*` subprocess test at `test_AC34_eager_health_after_startup.py:151` exercises the production entry point with a FakeGraphiti seam; it does NOT assert on `_graphiti is None` post-test (the subprocess terminates; assertion is on HTTP 200 within budget). No edit needed.
- AC34.2's pointer-to-evidence test (the inline lifespan exercise at line 282-298) updates per AC.MS-FIX.4. AC34.1's HTTP test stays untouched.
- HC#4 byte-content invariant: NO RETIRE-AND-REBASELINE.

---

## 10. AI-time prediction

Per `feedback_duration_estimation_rubric` calibration table:

- **Predicted (calibrated):** 15-30 min — single-component, two narrow source edits + one new helper + one new test file + two text-only test edits + plan + manifest + seal cycle. Comparable to amendment #34 (eager lifespan; 15-25 min actual) and amendment #21 (S3 silent-excepts; 20-30 min actual).
- **Plan rubric (uncalibrated 1-min-per-tool-call):** 30-60 min.
- **Actual:** populated post-build in §14 D-build.MS-FIX.0.

Calibration row appended to `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_duration_estimation_rubric.md` post-build.

---

## 14. Method-decision register (post-build)

(SHA register populated by `loam amend seal --plan-doc` SHA-backfill; method-decision narratives populated by builder during build.)

### D-build.MS-FIX.0 — AI-time actuals

(Populated post-build.)

### D-build.MS-FIX.1 — Fix #1 implementation actuals

(Populated post-build: did the one-line drop suffice, or did anything additional surface?)

### D-build.MS-FIX.2 — Fix #2 implementation actuals

(Populated post-build: ALTER TABLE confirmed working on the live pos3 kuzu_db; column added; add_episode succeeded post-restart.)

### D-build.MS-FIX.3 — Sealed-test in-band retire actuals

(Populated post-build: were any other sealed tests assert-on-null-state beyond the two named lines? Surface any additional retires.)

### D-build.MS-FIX.4 — Operational restart actuals

(Populated post-build: launchctl kickstart command output; PID transition; post-restart MCP-tool call results.)

### D-build.MS-FIX.5 — FIDRAFT capture from halt-and-surface trigger #5

(Populated post-build: silent-swallow patterns observed in memory-system source while editing; appended to FUTURE_IDEAS_DRAFT.md per discipline.)

### Commit SHAs

- Amendment commit: `f711adddab9b8ee8af6e424d86911b70701fb6a5` —
  `chore(loam-amend-apply): loam amend apply for memory-sidecar-recovery`
- Seal commit: `8ee241b3b7c80e5955d2a303d0713cfda6ecf0ea` —
  `chore(seals): memory-sidecar-recovery — memory-system at f711add`
## 15. Post-build verification checklist

- [ ] `pytest framework/memory-system/tests/` passes (touched-component scope).
- [ ] `loam amend apply --plan-doc <abs-path> --dry-run` returns clean (zero missing admissions, zero skipped reasons).
- [ ] `loam amend seal --plan-doc <abs-path>` produces seal commit; seal-test passes; sidecars + narrative advance.
- [ ] `loam amend apply --plan-doc <abs-path> --dry-run` rerun POST-seal returns clean.
- [ ] launchctl kickstart applied; new PID running; old PID gone.
- [ ] `curl -s http://127.0.0.1:8765/health` returns 200.
- [ ] MCP `health` tool returns `{status: ok, ...}`.
- [ ] MCP `add_episode` with a small test body succeeds (no Binder exception).
- [ ] MCP `search` returns results for a known-empty query.
- [ ] FUTURE_IDEAS_DRAFT.md appended with FIDRAFT entries from any HT-4 surface findings.
- [ ] `feedback_duration_estimation_rubric.md` calibration row appended.

---

## 16. Halt-and-surface findings encountered during plan authoring

- **HSF#1 (informational, in-scope per D3).** `_ensure_graphiti` at `service.py:91` calls `build_indices_and_constraints()` directly, NOT `prepare_graphiti`. Sealed sidecar boot path therefore never adds the D10 `retention_class` column to its on-disk DB unless `MemoryAPI` ingests separately exercise it. The one-line edit (replacing the call) closes this latent hole as a side effect of the schema-migration fix. Documented in D3 as in-scope rationale.

- **HSF#2 (informational, FIDRAFT capture deferred to build-time HT-4).** The retention.py docstring at lines 99-103 describes `ALTER TABLE` schema migrations as "raw Cypher because graphiti-core doesn't expose per-episode metadata" — but the file's name is `retention.py` and the docstring is about retention classes, not schema migrations. Adding `ensure_reference_time_column` here perpetuates a naming mismatch: schema migrations live in retention.py because retention.py was the first to need one. Long-term clean-up: rename to `schema_migrations.py` or extract a sibling module. Out of scope this amendment (sealed-component rename, no immediate value).

- **HSF#3 (informational, out of scope per dispatch trigger #5).** The pre-existing `try/except RuntimeError` at `factory.py:201-206` (FTS index "already exists" suppression) is a graceful-fallthrough-with-detection candidate per M6c's CDC. The catch silently `continue`s without logging — should emit `logger.warning` minimum. Note for FIDRAFT post-build per HT-4.

Plan is authorised to proceed.
