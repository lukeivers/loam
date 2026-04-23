# Amendment #26 — teardown observability retrofit

**Amendment number:** 26
**BASELINE (pre-amendment tip):** `dd11677` (docs: table loam rename idea
— decisions preserved, execution deferred).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored:** 2026-04-22.
**Research doc:** `research/amendment-26-teardown-observability-retrofit-research.md`.

## 1. Intent

Retrofit 23 bucket-(b) teardown broad-catch sites across eight
components to surface exceptions to observability per tightened CDC 2
at `9559ca7`. Each site keeps its no-raise contract (shutdown must not
cascade) but replaces bare `pass` with either
`span.add_event("<name>", {"exception": type(exc).__name__})` when a
span is in scope, or
`logger.debug("teardown_<context>_failed", exc_info=True)` otherwise.
`CancelledError` is split into its own bare-pass clause wherever it
shares a broad-Exception catch today.

## 2. Files edited per site

Per the research doc's catalogue (23 sites):

| # | File:line | Method | Fix |
|---|-----------|--------|-----|
| 1 | cost-governance/src/store.py:114 | CostStore.close | logger.debug |
| 2 | self-correction/src/store.py:119 | CorrectionStore.close | logger.debug |
| 3 | observability-aggregator/src/store.py:445 | Store.close | logger.debug |
| 4 | reversibility-primitive/src/store.py:85 | Store.close | logger.debug |
| 5 | safety-layer/src/store.py:78 | SafetyStore.close | logger.debug |
| 6 | telegram-interface/src/availability.py:212 | stop_background | split CancelledError + logger.debug |
| 7 | orchestrator/src/supervisor.py:268 | MemorySupervisor.stop | split CancelledError + logger.debug |
| 8 | orchestrator/src/ipc.py:116 | IPCServer.stop writer loop | logger.debug |
| 9 | orchestrator/src/ipc.py:248 | IPCClient.close | logger.debug |
| 10 | orchestrator/src/orchestrator.py:224 | _shutdown heartbeat await | split CancelledError + span.add_event |
| 11 | orchestrator/src/orchestrator.py:233 | _shutdown monitor.stop | split TimeoutError + span.add_event for both |
| 12 | orchestrator/src/orchestrator.py:239 | _shutdown ipc_server.stop | span.add_event |
| 13 | orchestrator/src/orchestrator.py:246 | _shutdown scope_runtime.close | span.add_event |
| 14 | orchestrator/src/orchestrator.py:287 | Orchestrator.close local_state | logger.debug |
| 15 | workspace-bootstrap adapters/observability_aggregator.py:60 | nested _shutdown processor | logger.debug |
| 16 | workspace-bootstrap adapters/observability_aggregator.py:64 | nested _shutdown exporter | logger.debug |
| 17 | workspace-bootstrap adapters/safety_layer.py:92 | nested _shutdown | logger.debug |
| 18 | workspace-bootstrap adapters/cost_governance.py:84 | nested _shutdown | logger.debug |
| 19 | workspace-bootstrap adapters/self_correction.py:70 | nested _shutdown | logger.debug |
| 20 | workspace-bootstrap adapters/memory_system.py:95 | nested _shutdown terminate | logger.debug |
| 21 | workspace-bootstrap adapters/memory_system.py:98 | nested _shutdown kill | logger.debug |
| 22 | workspace-bootstrap adapters/primary_persona.py:87 | nested _shutdown | logger.debug |
| 23 | workspace-bootstrap adapters/reversibility_primitive.py:77 | nested _shutdown | logger.debug |

## 3. Dropped per re-verification (deferred to follow-up)

- `orchestrator/src/ipc.py:122` (narrow `FileNotFoundError` — bucket a).
- `hands-off-lifecycle/hooks/first_run_progress.py:159` (narrow `OSError`
  — bucket a).
- `workspace-bootstrap/adapters/memory_system.py:109-117` (startup
  cleanup — enclosing method is `contribute()`, not a teardown).

These are captured in the research doc §5 and in the narrative stanza
for follow-up-amendment visibility.

## 4. Fix patterns (by shape)

### 4.1 Store.close() sites (1-5, 14)

Add module-top logger and emit before pass:

```python
import logging
_LOGGER = logging.getLogger(__name__)

def close(self) -> None:
    with self._lock:
        try:
            self._conn.close()
        except Exception:
            _LOGGER.debug(
                "<component>_store_close_failed", exc_info=True
            )
```

### 4.2 Split-CancelledError sites (6, 7)

```python
try:
    await self._task
except asyncio.CancelledError:
    pass  # expected on cancel
except Exception:
    _LOGGER.debug("<context>_failed", exc_info=True)
```

### 4.3 span.add_event sites (10-13)

`_process_span` is live during `_shutdown`. Use `obs.emit_event`:

```python
try:
    await self._heartbeat_task
except asyncio.CancelledError:
    pass
except Exception as e:
    obs.emit_event(
        self._process_span,
        "pos.orchestrator.heartbeat_stop_exception",
        {"exception_class": type(e).__name__},
    )
```

For site 11 (monitor.stop — TimeoutError+Exception), split TimeoutError
into its own `span.add_event` (distinct signal, not expected-flow).

### 4.4 workspace-bootstrap adapters (15-23)

Each adapter module gets a module-top logger and the nested `_shutdown`
closures emit via that logger. Workspace-bootstrap has no per-module
span state at adapter-close time — logger is the only channel.

## 5. Test additions

+7 new test files (one per component with source edits),
parameterized where possible:

- cost-governance/tests/test_s4_teardown_observability.py
- self-correction/tests/test_s4_teardown_observability.py
- observability-aggregator/tests/test_s4_teardown_observability.py
- reversibility-primitive/tests/test_s4_teardown_observability.py
- safety-layer/tests/test_s4_teardown_observability.py
- telegram-interface/tests/test_s4_teardown_observability.py
- orchestrator/tests/test_s4_teardown_observability.py
- workspace-bootstrap/tests/test_s4_teardown_observability.py

Each test monkey-patches the teardown target to raise and asserts
the expected logger record or span.add_event fires. Parameterization
over sites in the same component is preferred (one function,
multiple pytest.param entries).

## 6. BASELINE + SEAL + H19 bookkeeping

### 6.1 Manifest components

Per the research doc §6, eight manifest entries:

- cost-governance — floating BASELINE → `dd11677`.
- self-correction — floating → `dd11677`.
- observability-aggregator — floating → `dd11677`.
- reversibility-primitive — floating → `dd11677`.
- telegram-interface — floating → `dd11677`.
- orchestrator — floating → `dd11677`.
- workspace-bootstrap — floating → `dd11677`.
- hands-off-lifecycle — `frozen_baseline: true` (per amendment #23);
  sidecar + narrative only.

### 6.2 Allowed-prefix widenings (via `extra_allowed_prefixes`)

safety-layer gets source edits but has no seal-diff test. Its edits
are admitted into the other components' diff windows via
`safety-layer/` prefix. Six of the seven sealed-with-test components
do NOT currently admit `safety-layer/`:

- cost-governance: ADD `safety-layer/`.
- self-correction: ADD `safety-layer/`.
- observability-aggregator: ADD `safety-layer/`.
- reversibility-primitive: ADD `safety-layer/`.
- telegram-interface: ADD `safety-layer/`.
- workspace-bootstrap: ADD `safety-layer/`.

Orchestrator already admits `safety-layer/` (from amendment #19).

### 6.3 H19 cross-cutting

All 8 touched top-level surfaces are already in H19's `allowed` set
(amendments #18, #19, #20, #21 contributed these admissions). No new
H19 entry needed.

### 6.4 SEAL_COMMIT sidecars

Each manifest component's `tests/SEAL_COMMIT` gets the amendment SHA
in the seal commit (via `pos-amend seal`).

### 6.5 true-first-run narrative

Append amendment #26 stanza to
`hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run` — via pos-amend
`narrative:` block in the manifest.

## 7. Commit cadence

**Commit 1 (amendment):** human-authored via pos-amend `apply`.

Long-title amendment commit (brief explicitly allows):
```
fix(cost-governance, self-correction, observability-aggregator, reversibility-primitive, safety-layer, telegram-interface, orchestrator, workspace-bootstrap): teardown observability retrofit — surface 23 bucket-(b) sites per tightened CDC 2 (amendment #26)

23 broad-catch teardown sites across 8 components retrofitted to emit
observability per the tightened CDC 2 (`9559ca7`). Every `except
Exception: pass` inside a close() / stop() / _shutdown / __aexit__ /
cancel() / dispose() method now logs at DEBUG (with exc_info) or fires
span.add_event when a component-owned span is live at the catch site.
CancelledError is split into its own bare-pass clause wherever it was
previously co-caught with broad Exception.

[... per-site bullets ...]
```

**Commit 2 (seal):** via `pos-amend seal`.
```
chore(seals): teardown-observability-retrofit seal — cost-governance + self-correction + observability-aggregator + reversibility-primitive + telegram-interface + orchestrator + workspace-bootstrap + hands-off-lifecycle at <amendment-sha>
```

## 8. Halt triggers (re-checked at amendment-code time)

- Re-verification dropped scope to zero → NO (23 sites remain).
- Public-API change required → NO.
- Touched a non-admitted sealed component → NO (safety-layer covered
  by prefix in others' tuples after widening).
- pos-amend dry-run fails → WILL re-verify on build.
- A test-count drop in any component's existing suite → halt.

## 9. ODD compliance

Every added branch / test / import maps to the tightened-CDC-2 rule
in `docs/rebuild/FUTURE_IDEAS.md` (codified at `9559ca7`). The rule
IS an ODD-legit substitute for per-component AC backing (per the
core-development-convention framing). Each new test's assertion
shape — "raising inside teardown emits an observability record" —
discharges the CDC's observable-surface requirement.
