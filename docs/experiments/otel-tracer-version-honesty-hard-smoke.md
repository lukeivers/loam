# otel-tracer-version-honesty — HARD smoke writeup

**Cycle:** v0.10.4 PATCH (slug `otel-tracer-version-honesty`).
**Date:** 2026-05-14.
**Plan-doc:** `docs/plans/otel-tracer-version-honesty.md`.
**Slug-named per** `F-CYCLE-ARTEFACT-SLUG-NAMING` (NOT `v0-10-4-hard-smoke.md`).
**FIDRAFT closed:** F-OTEL-VERSION-BUMP (captured 2026-05-10 from v0.8.0 AC.HONEST.1; deferred to telemetry-touching cycle OR pre-v1.0 sweep — this PATCH dispatched against the second activation gate).

---

## §1 — Outcome shape verified

After this PATCH, every `_TRACER = trace.get_tracer("loam.<component>", "0.10.0")` call site (production observability.py / supervisor.py) emits spans carrying `instrumentation_scope.version == "0.10.0"` — matching the per-component-version discipline established at AC.HONEST.1 and bumped at v0.10.0 (component pyproject versions all at 0.10.0). Closes the documented-vs-actual drift in the telemetry layer that v0.8.0 deliberately deferred.

---

## §2 — Static verification (AC.OTVH.1 + AC.OTVH.2 + AC.OTVH.3)

Pre-source-edit baseline (from plan-doc empirical investigation 2026-05-14):

```
$ grep -rn 'get_tracer("loam\.[a-z_.]*", "0\.1\.0")' framework/ --include="*.py"
framework/cost-governance/src/loam/cost_governance/observability.py:30:_TRACER = trace.get_tracer("loam.cost_governance", "0.1.0")
framework/self-correction/tests/test_amendment_20_silent_excepts.py:56:        provider.get_tracer("loam.self_correction", "0.1.0"),
framework/self-correction/src/loam/self_correction/observability.py:31:_TRACER = trace.get_tracer("loam.self_correction", "0.1.0")
framework/dormancy/tests/test_d9_observability.py:61:    monkeypatch.setattr(gd_obs, "_TRACER", provider.get_tracer("loam.dormancy", "0.1.0"))
framework/dormancy/tests/test_d10_one_hour_outage.py:78:        gd_obs, "_TRACER", provider.get_tracer("loam.dormancy", "0.1.0")
framework/dormancy/tests/test_amendment_20_silent_excepts.py:66:        provider.get_tracer("loam.dormancy", "0.1.0"),
framework/dormancy/src/loam/dormancy/observability.py:40:_TRACER = trace.get_tracer("loam.dormancy", "0.1.0")
framework/observability-aggregator/tests/test_amendment_20_silent_excepts.py:47:        provider.get_tracer("loam.aggregator.nl", "0.1.0"),
framework/reversibility-primitive/src/loam/reversibility_primitive/observability.py:30:_TRACER = trace.get_tracer("loam.reversibility_primitive", "0.1.0")
framework/safety-layer/src/loam/safety_layer/observability.py:32:_TRACER = trace.get_tracer("loam.safety_layer", "0.1.0")
framework/orchestrator/src/loam/orchestrator/supervisor.py:63:_TRACER = trace.get_tracer("loam.hands_off_lifecycle", "0.1.0")
framework/orchestrator/src/loam/orchestrator/observability.py:31:_TRACER = trace.get_tracer("loam.orchestrator", "0.1.0")
```

12 sites: 7 production (`src/`) + 5 test-fixture monkeypatch installers (`tests/`).

Post-source-edit (verified at cycle's source-edit commit):

```
$ grep -rn 'get_tracer.*"0\.1\.0"' framework/ --include="*.py"
(zero matches — AC.OTVH.3 idempotence GREEN)

$ grep -rn 'get_tracer("loam\.[a-z_.]*", "0\.10\.0")' framework/ --include="*.py"
framework/cost-governance/src/loam/cost_governance/observability.py:30:_TRACER = trace.get_tracer("loam.cost_governance", "0.10.0")
framework/self-correction/tests/test_amendment_20_silent_excepts.py:56:        provider.get_tracer("loam.self_correction", "0.10.0"),
framework/self-correction/src/loam/self_correction/observability.py:31:_TRACER = trace.get_tracer("loam.self_correction", "0.10.0")
framework/dormancy/tests/test_d9_observability.py:61:    monkeypatch.setattr(gd_obs, "_TRACER", provider.get_tracer("loam.dormancy", "0.10.0"))
framework/dormancy/tests/test_d10_one_hour_outage.py:78:        gd_obs, "_TRACER", provider.get_tracer("loam.dormancy", "0.10.0")
framework/dormancy/tests/test_amendment_20_silent_excepts.py:66:        provider.get_tracer("loam.dormancy", "0.10.0"),
framework/dormancy/src/loam/dormancy/observability.py:40:_TRACER = trace.get_tracer("loam.dormancy", "0.10.0")
framework/observability-aggregator/tests/test_amendment_20_silent_excepts.py:47:        provider.get_tracer("loam.aggregator.nl", "0.10.0"),
framework/reversibility-primitive/src/loam/reversibility_primitive/observability.py:30:_TRACER = trace.get_tracer("loam.reversibility_primitive", "0.10.0")
framework/safety-layer/src/loam/safety_layer/observability.py:32:_TRACER = trace.get_tracer("loam.safety_layer", "0.10.0")
framework/orchestrator/src/loam/orchestrator/supervisor.py:63:_TRACER = trace.get_tracer("loam.hands_off_lifecycle", "0.10.0")
framework/orchestrator/src/loam/orchestrator/observability.py:31:_TRACER = trace.get_tracer("loam.orchestrator", "0.10.0")
```

Same 12 sites, all literal `"0.1.0"` → `"0.10.0"` (AC.OTVH.1 + AC.OTVH.2 GREEN). Production count: 7 (cost-governance + self-correction + dormancy + reversibility-primitive + safety-layer + orchestrator/observability + orchestrator/supervisor). Test count: 5 (self-correction + dormancy ×3 + observability-aggregator).

---

## §3 — Outcome-altitude dogfood probe (AC.OTVH.4) — runtime instrumentation_scope.version

Live runtime probe. Spawn a fresh `TracerProvider`, install an in-memory exporter, import a production component module (its module-level `_TRACER = trace.get_tracer(...)` call resolves against the just-installed provider), invoke a span-emitting function, capture the span, read the `instrumentation_scope.version` attribute.

### §3.1 — Single-component verification (cost-governance)

```
$ python3 -c "
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry import trace as ot_trace

provider = TracerProvider()
exporter = InMemorySpanExporter()
provider.add_span_processor(SimpleSpanProcessor(exporter))
ot_trace.set_tracer_provider(provider)

from loam.cost_governance import observability as cg_obs
print('cost-governance _TRACER name:', cg_obs._TRACER._instrumentation_scope.name)
print('cost-governance _TRACER version:', cg_obs._TRACER._instrumentation_scope.version)

cg_obs.reservation_created(scope_id='probe-scope', session_id='probe-session', reserved_time=10, reserved_tokens=100, reserved_money_cents=5)
spans = exporter.get_finished_spans()
print('captured spans:', len(spans))
for s in spans:
    print('  span name:', s.name)
    print('  instrumentation_scope.name:', s.instrumentation_scope.name)
    print('  instrumentation_scope.version:', s.instrumentation_scope.version)
"
```

Verbatim output (captured 2026-05-14):

```
cost-governance _TRACER name: loam.cost_governance
cost-governance _TRACER version: 0.10.0
captured spans: 1
  span name: loam.cost.reservation_created
  instrumentation_scope.name: loam.cost_governance
  instrumentation_scope.version: 0.10.0
```

`instrumentation_scope.version == "0.10.0"` confirmed at runtime — the source-edit propagates through OTel's `get_tracer(name, version)` contract to the wire. AC.OTVH.4 GREEN.

### §3.2 — All 7 production tracers cross-verified

For completeness, probe every production `_TRACER` to confirm the literal change propagates uniformly:

```
$ python3 -c "
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry import trace as ot_trace

provider = TracerProvider()
exporter = InMemorySpanExporter()
provider.add_span_processor(SimpleSpanProcessor(exporter))
ot_trace.set_tracer_provider(provider)

from loam.cost_governance import observability as cg_obs
from loam.self_correction import observability as sc_obs
from loam.dormancy import observability as dm_obs
from loam.reversibility_primitive import observability as rp_obs
from loam.safety_layer import observability as sl_obs
from loam.orchestrator import observability as or_obs
from loam.orchestrator import supervisor as sup_obs

for label, mod in [
    ('cost_governance', cg_obs),
    ('self_correction', sc_obs),
    ('dormancy', dm_obs),
    ('reversibility_primitive', rp_obs),
    ('safety_layer', sl_obs),
    ('orchestrator (observability.py)', or_obs),
    ('orchestrator (supervisor.py)', sup_obs),
]:
    s = mod._TRACER._instrumentation_scope
    print(f'{label:42s} name={s.name:32s} version={s.version}')
"
```

Verbatim output (captured 2026-05-14):

```
cost_governance                            name=loam.cost_governance             version=0.10.0
self_correction                            name=loam.self_correction             version=0.10.0
dormancy                                   name=loam.dormancy                    version=0.10.0
reversibility_primitive                    name=loam.reversibility_primitive     version=0.10.0
safety_layer                               name=loam.safety_layer                version=0.10.0
orchestrator (observability.py)            name=loam.orchestrator                version=0.10.0
orchestrator (supervisor.py)               name=loam.hands_off_lifecycle         version=0.10.0
```

All 7 production tracers verified at runtime carrying `version=0.10.0`. Component-name first arg preserved verbatim across the sweep (no name-arg corruption). AC.OTVH.4 GREEN — outcome-altitude verification complete.

---

## §4 — Test suite verdict (modified files)

19 tests across 5 modified test files all PASS post-edit:

| File | Tests | Verdict |
|---|---|---|
| `framework/dormancy/tests/test_d9_observability.py` | 7 | 7 passed |
| `framework/dormancy/tests/test_amendment_20_silent_excepts.py` | 3 | 3 passed |
| `framework/observability-aggregator/tests/test_amendment_20_silent_excepts.py` | 2 | 2 passed |
| `framework/self-correction/tests/test_amendment_20_silent_excepts.py` | 5 | 5 passed |
| `framework/dormancy/tests/test_d10_one_hour_outage.py` | 2 | 2 passed |

Full per-component test suites (post-source-edit):

| Component | Verdict |
|---|---|
| `framework/cost-governance/` | 71 passed |
| `framework/self-correction/` | 84 passed |
| `framework/dormancy/` | 104 passed |
| `framework/reversibility-primitive/` | 46 passed |
| `framework/safety-layer/` | 72 passed |
| `framework/orchestrator/` | 104 passed + 2 pre-existing failures (`test_pos_session_start.py::test_ready_path_when_both_services_up` + `test_AC_V11_E_1_memory_skipped_when_plist_absent` — rebrand-residue string-comparison test failures, NOT caused by tracer-version edit; verified via git stash baseline) |
| `framework/observability-aggregator/` | 65 passed |

6 of 7 affected components 100% GREEN. Orchestrator's 2 failures are documented-pre-existing per F-TF-* class (rebrand-residue from the v0.5.1 split-worktrees migration; expected `'pos v2 ready'` vs actual `'loam ready'` — separate cleanup concern, NOT in F-OTEL-VERSION-BUMP scope).

Release-CLI tests (`framework/tools/loam/`): 98/98 GREEN.

---

## §5 — Slug-naming compliance (F-CYCLE-ARTEFACT-SLUG-NAMING)

This file lives at `docs/experiments/otel-tracer-version-honesty-hard-smoke.md` (slug-named matching the plan-doc's slug `otel-tracer-version-honesty`). Does NOT live at `docs/experiments/v0-10-4-hard-smoke.md` (version-named — would violate `F-CYCLE-ARTEFACT-SLUG-NAMING` and trip the v0.8.2 `--plan-doc` flag's stem-derived path resolution).

The release-CLI gate `check_hard_smoke` reads `docs/experiments/<plan-doc-stem>-hard-smoke.md` when `--plan-doc <path>` is set, where `<plan-doc-stem>` = `Path(plan_doc).stem` = `otel-tracer-version-honesty`. This file's path matches that stem-derived expectation.

---

## §6 — Halt-and-surface findings

**No HARD HALTs fired in-cycle.**

**Pre-existing-test-failure clarification:** Orchestrator's 2 failures (rebrand-residue) are pre-existing on main (verified via `git stash` baseline at plan-doc commit `5d0ca57`); they are NOT caused by the tracer-version edit. Captured under the F-TF-* class for separate cleanup; out of scope for F-OTEL-VERSION-BUMP closure.

**Empirical-recheck-before-halt discipline:** never fired (each of the 12 substitutions had an unambiguous fix-target).

**One AC text tightening at plan-time** (per `feedback_loose_AC_text_fix_AC_not_implementation`): AC.OTVH.2 originally framed by FIDRAFT capture as "tests if any assert on tracer version" — empirically NO production assertions exist; tests install via `provider.get_tracer(...)` monkeypatch with the literal as a fixture-controlled value. AC text tightened doc-only at plan-authoring-time to name the actual scope (fixture installations) rather than the assertion scope the capture suggested. Doc-only; no source-text divergence from intent.

**One FIDRAFT entry flipped to RESOLVED:** F-OTEL-VERSION-BUMP at `docs/FUTURE_IDEAS_DRAFT.md:260`; entry preserved with RESOLVED block citing this PATCH cycle's plan-doc + smoke writeup paths.

**One new FIDRAFT entry captured:** F-OTEL-VERSION-DYNAMIC-IMPORT — proposes the `__version__`-import shape as a follow-on cycle gated on either: (a) a future cycle that's already touching the 6 components' `__init__.py` for other reasons, or (b) structural drift signal. See plan-doc §15.

**F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH discipline:** verified empirically — `grep -rn "F-OTEL-VERSION-BUMP" docs/` returned 1 reference at `docs/FUTURE_IDEAS_DRAFT.md:260` (the entry itself) plus 1 unrelated count-table reference at `docs/plans/v0-8-0-honesty-cleanup.md:425`. No other FIDRAFT entries reference F-OTEL-VERSION-BUMP as a blocker / dep / unblocker; no flip-on-unblock action needed.
