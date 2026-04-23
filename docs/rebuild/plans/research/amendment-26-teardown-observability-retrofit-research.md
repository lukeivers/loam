# Amendment #26 — teardown observability retrofit — research

**Amendment number:** 26
**BASELINE (pre-amendment tip):** `dd11677` (docs: table loam rename idea
— decisions preserved, execution deferred).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored:** 2026-04-22.
**Companion plan:** `../amendment-26-teardown-observability-retrofit.md`.
**Pre-dispatch skills:** research-before-plan CDC, plan-before-code CDC,
scope-only-dispatch CDC, audit-triage-by-severity CDC,
amendment-dispatch-speedups CDC.

## 1. Intent

Tightened CDC 2 at `9559ca7` requires every teardown bucket-(b)
broad-catch to surface exceptions to observability. Bare `pass` is no
longer acceptable inside teardown methods — a `span.add_event(...)`
must fire when a span is in scope, or at minimum
`logger.debug("teardown_*_failed", exc_info=True)` otherwise.
`CancelledError` is expected flow and must be split into its own
bare-pass clause separate from any broad `Exception` catch.

Per the brief, the starting classifier-count is ~44 bucket-(b) sites.
Post re-verification, this research doc catalogs every candidate, keeps
only those inside actual teardown methods with broad catches, and drops
narrow designed-branch catches (bucket-(a) parse-dispatch equivalents)
or non-teardown-enclosed sites (future amendment scope).

## 2. Scanner methodology

Walked every `.py` under:
`scope-of-work/src`, `memory-system/src`, `graceful-degradation/src`,
`cost-governance/src`, `objective-tracker/src`,
`workspace-bootstrap/src`, `self-correction/src`, `self-upgrade/src`,
`observability-aggregator/src`, `telegram-interface/src`,
`primary-persona/src`, `reversibility-primitive/src`,
`safety-layer/src`, `orchestrator/src`, `hands-off-lifecycle/src`
(none), `hands-off-lifecycle/hooks`.

For every `except ...:` clause whose body contains only `pass`,
`continue`, `return`, or `return None` (optionally with comments), I
recorded the nested `def` chain enclosing the clause. Sites whose
enclosing-def chain contains a teardown-semantic name (`close`, `stop`,
`cancel`, `shutdown`, `dispose`, `aclose`, `terminate`, `destroy`,
`teardown`, `cleanup`, `_shutdown`, `finalize`, `stop_*`, `close_*`,
`cancel_*`, `shutdown_*`, `_stop_*`, `_close_*`, `_cancel_*`,
`_shutdown_*`, `dispose_*`, `_dispose_*`, `__a?exit__`, `__del__`) are
classified candidate-teardown and hand-verified below.

**Raw candidate count (teardown-enclosed silent-except):** 28 sites
(some already compliant: workspace-bootstrap/main.py:292 has
`span.add_event`; primary-persona/monitor.py:191 has non-trivial
body). 24 sites entered re-verification.

## 3. Per-site re-verification

### Site 1 — cost-governance/src/store.py:114 — CostStore.close()

**Enclosing:** `CostStore.close(self)` — teardown (unqualified `close`).
**Catch:** `except Exception` — broad. Body: `pass`.
**Span in scope?** No; `close()` only wraps `self._conn.close()` under a
lock. No tracer span open. `cost-governance/src/observability.py`
exposes `trace.get_tracer("pos.cost_governance")`; a new short-lived
teardown span is an option but adds a tracer dependency to the store.
**Fix:** `logger.debug("cost_store_close_failed", exc_info=True)`.
`logging.getLogger(__name__)` at module top.
**Bucket:** (b). Confirmed in-scope.

### Site 2 — self-correction/src/store.py:119 — CorrectionStore.close()

Identical shape to Site 1. `logger.debug("self_correction_store_close_failed", exc_info=True)`.
**Bucket:** (b). Confirmed in-scope.

### Site 3 — observability-aggregator/src/store.py:445 — Store.close()

Identical shape to Site 1 (DuckDB/SQLite Store). Aggregator already has
a module logger convention (`ingest.py:59`:
`log = logging.getLogger("pos.aggregator.ingest")`). Use
`logging.getLogger("pos.aggregator.store")` and emit
`log.debug("aggregator_store_close_failed", exc_info=True)`.
**Bucket:** (b). Confirmed in-scope.

### Site 4 — reversibility-primitive/src/store.py:85 — Store.close()

Identical shape to Site 1. `logger.debug("reversibility_store_close_failed", exc_info=True)`.
**Bucket:** (b). Confirmed in-scope.

### Site 5 — safety-layer/src/store.py:78 — SafetyStore.close()

Identical shape to Site 1. `logger.debug("safety_store_close_failed", exc_info=True)`.
**Bucket:** (b). Confirmed in-scope.

### Site 6 — telegram-interface/src/availability.py:212 — stop_background()

**Enclosing:** `TelegramAvailability.stop_background(self)` — teardown.
**Catch:** `except (asyncio.CancelledError, Exception)` — broad + expected-
flow mixed. Body: `pass`.
**Tightened CDC 2 demand:** split. Keep bare-pass for CancelledError;
add emission for broad Exception.
**Span in scope?** No live span. Use logger:
`logger.debug("availability_stop_background_failed", exc_info=True)`.
**Bucket:** (b). Confirmed in-scope.

### Site 7 — orchestrator/src/supervisor.py:268 — MemorySupervisor.stop()

**Catch:** `except (asyncio.CancelledError, Exception)`. Body: `pass`.
**Split:** `except asyncio.CancelledError: pass` + broad Exception with
`logger.debug("supervisor_stop_probe_task_failed", exc_info=True)`.
**Bucket:** (b). Confirmed in-scope.

### Site 8 — orchestrator/src/ipc.py:116 — IPCServer.stop() writer close

**Enclosing:** `IPCServer.stop(self)` — teardown.
**Catch:** `except Exception` inside a per-client writer-close loop.
Body: `pass`.
**Span in scope?** No. Use
`logger.debug("ipc_server_stop_writer_close_failed", exc_info=True)`.
**Bucket:** (b). Confirmed in-scope.

### Site 9 — orchestrator/src/ipc.py:122 — IPCServer.stop() socket unlink

**Catch:** `except FileNotFoundError` — NARROW designed-branch (socket
file already absent).
**Bucket:** (a) — exception-to-result-conversion. The narrow catch IS
the observable surface: "file gone" is the designed success condition.
**Outcome:** DROP from scope. Not bucket-(b). (Tightened CDC 2
specifically names "broad catch" — narrow catches are designed-branch
signals.)

### Site 10 — orchestrator/src/ipc.py:248 — IPCClient.close() writer close

**Catch:** `except Exception`. Body: `pass`.
`logger.debug("ipc_client_close_writer_failed", exc_info=True)`.
**Bucket:** (b). Confirmed in-scope.

### Site 11 — orchestrator/src/orchestrator.py:224 — _shutdown heartbeat await

**Catch:** `except (asyncio.CancelledError, Exception)`. Body: `pass`.
**Span in scope?** YES — `self._process_span` is live until line 257.
`obs.emit_event(self._process_span, "pos.orchestrator.heartbeat_stop_exception", {"exception_class": type(e).__name__})`.
Split CancelledError into a separate bare-pass clause.
**Bucket:** (b). Confirmed in-scope.

### Site 12 — orchestrator/src/orchestrator.py:233 — _shutdown monitor.stop wait

**Catch:** `except (asyncio.TimeoutError, Exception)`. Body: `pass`.
**Split:** TimeoutError is NOT CancelledError-semantic — it indicates
the monitor did not stop within `sigterm_grace_seconds`, which is a
distinct operational signal. Per tightened CDC 2, the broad-Exception
branch must emit; the TimeoutError branch should ALSO emit (it's not
expected-flow — it's the configured-grace timeout expiring, worth
surfacing). Split into two emission branches both on
`self._process_span`.
**Bucket:** (b). Confirmed in-scope.

### Site 13 — orchestrator/src/orchestrator.py:239 — _shutdown ipc_server.stop

**Catch:** `except Exception`. Body: `pass`.
`obs.emit_event(self._process_span, "pos.orchestrator.ipc_server_stop_exception", {...})`.
**Bucket:** (b). Confirmed in-scope.

### Site 14 — orchestrator/src/orchestrator.py:246 — _shutdown scope_runtime.close

`obs.emit_event(self._process_span, "pos.orchestrator.scope_runtime_close_exception", {...})`.
**Bucket:** (b). Confirmed in-scope.

### Site 15 — orchestrator/src/orchestrator.py:287 — Orchestrator.close() local_state close

**Catch:** `except Exception`. Body: `pass`.
**Span in scope?** No — `_process_span` is already ended by the time
`close()` is called. Use logger:
`logger.debug("orchestrator_close_local_state_failed", exc_info=True)`.
**Bucket:** (b). Confirmed in-scope.

### Sites 16-17 — workspace-bootstrap/adapters/observability_aggregator.py:60,64 — _shutdown processor/exporter

**Enclosing:** nested `_shutdown()` inside `ObservabilityAggregatorContribution.contribute()`.
**Catch:** `except Exception`. Body: `pass`. Two sequential teardowns
(processor, exporter). Module currently has no logger. Add
`logging.getLogger("pos.workspace_bootstrap.adapters.observability_aggregator")`.
Emit
`logger.debug("aggregator_processor_shutdown_failed", exc_info=True)` /
`logger.debug("aggregator_exporter_shutdown_failed", exc_info=True)`.
**Bucket:** (b). Both confirmed in-scope.

### Site 18 — workspace-bootstrap/adapters/safety_layer.py:92 — _shutdown store.close

`logger.debug("safety_layer_adapter_shutdown_failed", exc_info=True)`.
**Bucket:** (b). Confirmed in-scope.

### Site 19 — workspace-bootstrap/adapters/cost_governance.py:84 — _shutdown store.close

`logger.debug("cost_governance_adapter_shutdown_failed", exc_info=True)`.
**Bucket:** (b). Confirmed in-scope.

### Site 20 — workspace-bootstrap/adapters/self_correction.py:70 — _shutdown store.close

`logger.debug("self_correction_adapter_shutdown_failed", exc_info=True)`.
**Bucket:** (b). Confirmed in-scope.

### Site 21 — workspace-bootstrap/adapters/memory_system.py:98 — _shutdown nested kill()

**Context:** nested `except Exception: pass` inside the TERMINATE-then-
KILL fallback inside the `_shutdown()` closure. The outer catch (line
95) already runs the fallback; the inner catch at line 98 swallows
`kill()` failure.
**Catch:** `except Exception`. Body: `pass`.
**Fix:** split: emit
`logger.debug("memory_system_adapter_kill_failed", exc_info=True)`
before the `pass`.
**Also:** line 95's outer catch wraps `terminate()` + `wait()` with a
fallback body that calls `kill()`. This is NOT silent — it has a
structured fallback path. But the fallback itself is a broad catch
inside a teardown; tightened CDC 2 would still prefer an emission
before the fallback, not bare transition. Research-scope check: that
site is currently captured in the "workspace-bootstrap/adapters/memory_system.py:95"
classifier finding? The scanner found it at line 95 as a catch whose
body is `try: proc.kill() except Exception: pass` — a non-trivial body
(outer catch has real work). Per the tightened CDC the broad catch at
line 95 SHOULD also emit. **Keep in scope as Site 21a.**
**Fix 21a (outer):** emit a logger event before the `proc.kill()`
fallback:
`logger.debug("memory_system_adapter_terminate_failed", exc_info=True)`.
**Fix 21 (inner, nested):** emit
`logger.debug("memory_system_adapter_kill_failed", exc_info=True)`
before the final `pass`.
**Bucket:** (b) for both. Confirmed in-scope.

**Also-also:** lines 109–117 (at `_deploy` time, NOT a teardown method
— cleanup-after-health-probe-failure). Same pattern (terminate+fallback-
kill). But the enclosing def is `contribute()`, NOT a teardown method —
this is failed-startup cleanup, not a post-success teardown. Per the
brief's teardown-only scope, DROP this one. Future amendment classifies
it (bucket-(b) per tightened CDC? or bucket-(d) because startup-cleanup
isn't technically "teardown"?). Note deferred.

### Site 22 — workspace-bootstrap/adapters/primary_persona.py:87 — _shutdown store.close

`logger.debug("primary_persona_adapter_shutdown_failed", exc_info=True)`.
**Bucket:** (b). Confirmed in-scope.

### Site 23 — workspace-bootstrap/adapters/reversibility_primitive.py:77 — _shutdown store.close

`logger.debug("reversibility_primitive_adapter_shutdown_failed", exc_info=True)`.
**Bucket:** (b). Confirmed in-scope.

### Site 24 — hands-off-lifecycle/hooks/first_run_progress.py:159 — close() target.close

**Catch:** `except OSError` — NARROW designed-branch (stream already
closed). Body: `pass`.
**Bucket:** (a) — exception-to-result-conversion. The narrow catch IS
the observable surface: "stream already unavailable" is the designed
success condition (TTY gone, pipe closed).
**Outcome:** DROP from scope. Not bucket-(b).

## 4. In-scope site summary

| # | File:line | Enclosing | Fix-shape |
|---|-----------|-----------|-----------|
| 1 | cost-governance/src/store.py:114 | CostStore.close | logger.debug |
| 2 | self-correction/src/store.py:119 | CorrectionStore.close | logger.debug |
| 3 | observability-aggregator/src/store.py:445 | Store.close | logger.debug |
| 4 | reversibility-primitive/src/store.py:85 | Store.close | logger.debug |
| 5 | safety-layer/src/store.py:78 | SafetyStore.close | logger.debug |
| 6 | telegram-interface/src/availability.py:212 | stop_background | split CancelledError; logger.debug |
| 7 | orchestrator/src/supervisor.py:268 | MemorySupervisor.stop | split CancelledError; logger.debug |
| 8 | orchestrator/src/ipc.py:116 | IPCServer.stop (writer) | logger.debug |
| 9 | orchestrator/src/ipc.py:248 | IPCClient.close | logger.debug |
| 10 | orchestrator/src/orchestrator.py:224 | _shutdown heartbeat | split CancelledError; span.add_event |
| 11 | orchestrator/src/orchestrator.py:233 | _shutdown monitor.stop | split TimeoutError; span.add_event both |
| 12 | orchestrator/src/orchestrator.py:239 | _shutdown ipc.stop | span.add_event |
| 13 | orchestrator/src/orchestrator.py:246 | _shutdown scope_runtime.close | span.add_event |
| 14 | orchestrator/src/orchestrator.py:287 | Orchestrator.close | logger.debug |
| 15 | workspace-bootstrap/adapters/observability_aggregator.py:60 | nested _shutdown (processor) | logger.debug |
| 16 | workspace-bootstrap/adapters/observability_aggregator.py:64 | nested _shutdown (exporter) | logger.debug |
| 17 | workspace-bootstrap/adapters/safety_layer.py:92 | nested _shutdown | logger.debug |
| 18 | workspace-bootstrap/adapters/cost_governance.py:84 | nested _shutdown | logger.debug |
| 19 | workspace-bootstrap/adapters/self_correction.py:70 | nested _shutdown | logger.debug |
| 20 | workspace-bootstrap/adapters/memory_system.py:95 | nested _shutdown terminate | logger.debug |
| 21 | workspace-bootstrap/adapters/memory_system.py:98 | nested _shutdown kill (inner) | logger.debug |
| 22 | workspace-bootstrap/adapters/primary_persona.py:87 | nested _shutdown | logger.debug |
| 23 | workspace-bootstrap/adapters/reversibility_primitive.py:77 | nested _shutdown | logger.debug |

**Total in-scope: 23 sites.** (Brief's pre-research "~44" estimate
included non-teardown-enclosed sites likely destined for future
amendments, and narrow designed-branch catches that drop to bucket-(a).)

## 5. Dropped / deferred to follow-up amendment

| Dropped site | Reason |
|--------------|--------|
| orchestrator/src/ipc.py:122 | `except FileNotFoundError` — narrow designed-branch (bucket a). |
| hands-off-lifecycle/hooks/first_run_progress.py:159 | `except OSError` — narrow designed-branch (bucket a). |
| workspace-bootstrap/adapters/memory_system.py:109-117 (startup cleanup) | Enclosing `contribute()` is NOT a teardown method; this is failed-startup cleanup. Out-of-scope for #26. |
| orchestrator/src/ipc.py:150-154, 157-161 | `_handle_client` finally-block cleanup. Enclosing method is not teardown-semantic (connection handler). Out-of-scope for #26. |
| orchestrator/src/ipc.py:202-205, 221-224 | `_write_result` / `_write_error` writer.drain swallows. Not teardown. Out-of-scope. |
| All `orchestrator/src/supervisor.py` silent-excepts except line 268 | `_persist_escalation`, `_load_persisted_escalation`, `_write_attention`, `_clear_attention`, `_loop` inner TimeoutError — not teardowns. Out-of-scope. |
| All other `scope-of-work`, `primary-persona`, `memory-system`, `graceful-degradation`, `self-upgrade`, `hands-off-lifecycle/hooks`, etc. silent-excepts | Not inside a teardown method. These are bucket-(a) (exception-to-result), bucket-(d) (outright), or narrow designed-branch. Future amendment (separate ticket). |

## 6. Components touched, seal impact, and manifest shape

| Component | Sites touched | Sealed? | BASELINE |
|-----------|--------------|---------|----------|
| cost-governance | 1 | Yes | advance to dd11677 |
| self-correction | 1 | Yes | advance to dd11677 |
| observability-aggregator | 1 | Yes | advance to dd11677 |
| reversibility-primitive | 1 | Yes | advance to dd11677 |
| safety-layer | 1 | No seal-diff test (monkey-patch import guard only) | no manifest entry |
| telegram-interface | 1 | Yes | advance to dd11677 |
| orchestrator | 7 (supervisor + ipc + orchestrator) | Yes | advance to dd11677 |
| workspace-bootstrap | 9 (7 adapters, plus the memory_system 2-split) | Yes | advance to dd11677 |
| hands-off-lifecycle | 0 source edits | Yes | **frozen_baseline: true** (per amendment #23); sidecar + narrative only |

**Eight manifest components** (cost-governance, self-correction,
observability-aggregator, reversibility-primitive, telegram-interface,
orchestrator, workspace-bootstrap, hands-off-lifecycle).

Safety-layer gets source edits but has no seal-diff test to advance.
No manifest entry; the source edit is admitted via H19's existing
`safety-layer` prefix + the cross-component seal-diff tests'
already-present `safety-layer/` admissions (from amendment #19).

## 7. Allowed-prefix widening check

This amendment touches 8 components plus universal paths. For each
sealed component's seal-diff test, cross-check whether the other seven
are in its `allowed_prefixes` tuple already.

Prior multi-component amendments (#19, #20, #21) already widened tuples
to include cross-component prefixes; subsequent amendments (#22, #23,
#24, #25) also contributed. **I will audit each tuple at plan-execute
time.** Expected widenings (research-predicted):

- cost-governance: may need `workspace-bootstrap/`, `safety-layer/`,
  `observability-aggregator/`, `telegram-interface/`,
  `reversibility-primitive/`, `self-correction/`.
- Similar audit for each other touched sealed component.

Additions use `extra_allowed_prefixes` via pos-amend's manifest.

## 8. New surface in H19

All 8 components are already in H19's allowed top-level set per
amendment #21 (scope-of-work was the last admission). No new H19
admission needed.

## 9. Halt-trigger pre-check

- **Re-verification drops scope to zero:** NO — 23 sites surviving.
- **Fix requires public-API change:** NO — all fixes are internal
  log/emit additions; no method begins raising a new exception, no
  return-contract changes.
- **Scope creep (finding belongs to different amendment class):** The
  `workspace-bootstrap/adapters/memory_system.py:109-117` startup-
  cleanup case flagged and deferred (enclosing method is not a
  teardown). The narrow designed-branch cases (ipc.py:122,
  first_run_progress.py:159) flagged and deferred. No in-scope site
  shifts to a non-teardown fix.
- **pos-amend `apply --dry-run` missing admissions:** Manifest author-
  time adds `extra_allowed_prefixes` for cross-component seal-diff
  tests as needed (§7). Will re-check on green dry-run.

All cleared. Proceeding to plan.

## 10. Test plan (per-component, parameterized where possible)

Ideal shape: one parameterized test per component covering all its
teardown sites, monkey-patching the underlying close to raise and
asserting the emission fired.

- **cost-governance** — `tests/test_s4_teardown_observability.py`
  +1 test (store.close) asserting the logger emission fires.
- **self-correction** — same shape; +1 test.
- **observability-aggregator** — same shape; +1 test.
- **reversibility-primitive** — same shape; +1 test.
- **safety-layer** — same shape; +1 test.
- **telegram-interface** — +1 test in `tests/test_s4_teardown_observability.py`:
  make `stop_background` swallow a broad Exception from the awaited
  task; assert logger emission + split-CancelledError case still
  bare-passes.
- **orchestrator** — +1 test in `tests/test_s4_teardown_observability.py`,
  parameterized across the 3 orchestrator.py shutdown sites that emit
  on `_process_span`. For the supervisor.stop + ipc.stop + ipc_client.close
  logger-based sites, either add a second test or share a caplog-based
  assertion.
- **workspace-bootstrap** — +1 parameterized test in
  `tests/test_s4_teardown_observability.py` across all seven adapters'
  nested `_shutdown()` closures.

**Expected test delta:** +7 new tests (one per component).

## 11. Commit-message shape

**Amendment commit (title long but acceptable; brief explicitly
allows):**
`fix(cost-governance, self-correction, observability-aggregator, reversibility-primitive, safety-layer, telegram-interface, orchestrator, workspace-bootstrap): teardown observability retrofit — surface 23 bucket-(b) sites per tightened CDC 2 (amendment #26)`

**Seal commit:**
`chore(seals): teardown-observability-retrofit seal — cost-governance + self-correction + observability-aggregator + reversibility-primitive + telegram-interface + orchestrator + workspace-bootstrap + hands-off-lifecycle at <amendment-sha>`
