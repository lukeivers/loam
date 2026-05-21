# OTel tracer-version honesty PATCH

**Status:** plan-only at authoring time. Plan-before-code per `feedback_plan_before_code`. Owner ratification: dispatch brief from dispatcher 2026-05-14 explicitly authorises closure of FIDRAFT F-OTEL-VERSION-BUMP (captured 2026-05-10 from v0.8.0 AC.HONEST.1 in-cycle finding; deferred to telemetry-touching cycle OR pre-v1.0 sweep). This PATCH executes that closure.
**Slug:** `otel-tracer-version-honesty` (scope-descriptive; no version pre-baked per `feedback_version_numbers_at_release_time`).
**Date authored:** 2026-05-14.
**Class:** **PATCH** per `docs/release-versioning-policy.md`. Telemetry-layer drift closure inside already-shipped per-component-version discipline (AC.HONEST.1) — same outcome shape (per-component-version honesty) extended to the OTel tracer-version arg surface that v0.8.0 deliberately deferred. No new outcome capability; no public API change; no user-visible behaviour change. Trace-data layer only.
**Predecessor:** v0.10.3 PATCH SHIPPED PUBLIC (sealed `44c28e6`; published `3cd7983`). Build-forward per `feedback_build_forward_on_publish_pending`.
**Working directory:** `/Users/lukeivers/loam/`.
**Version derivation:** at release-time per `feedback_version_numbers_at_release_time`: `next_PATCH(v0.10.3) = v0.10.4`. Plan-doc slug scope-descriptive (no version pre-baked); AC family scope-descriptive (`AC.OTVH.*` for `otel-tracer-version-honesty`).

---

## §1 — Outcome shape (the "why")

Each component's `observability.py` (or equivalent module-level emitter) carries the line:

```python
_TRACER = trace.get_tracer("loam.<component>", "0.1.0")
```

The second arg is OTel's `instrumenting_library_version` — distinct from the package version, but emitted in every span's `instrumentation_scope.version` field. v0.8.0 AC.HONEST.1 swept the user-visible per-component-version surface (30 pyproject.toml versions + 4 `__version__` strings, all bumped 0.1.0 → 0.8.0; per-component-version discipline established). The tracer-version literal `"0.1.0"` was deliberately deferred — telemetry layer, not user-visible — and captured at FIDRAFT F-OTEL-VERSION-BUMP for closure at the next telemetry-touching cycle OR pre-v1.0 sweep.

Today's enumeration (empirical, 2026-05-14):

- **7 production sites** across **6 components** carry `_TRACER = trace.get_tracer("loam.<component>", "0.1.0")` with the stale literal:
  1. `framework/cost-governance/src/loam/cost_governance/observability.py:30`
  2. `framework/self-correction/src/loam/self_correction/observability.py:31`
  3. `framework/dormancy/src/loam/dormancy/observability.py:40`
  4. `framework/reversibility-primitive/src/loam/reversibility_primitive/observability.py:30`
  5. `framework/safety-layer/src/loam/safety_layer/observability.py:32`
  6. `framework/orchestrator/src/loam/orchestrator/supervisor.py:63` (orchestrator component, supervisor module)
  7. `framework/orchestrator/src/loam/orchestrator/observability.py:31` (orchestrator component, observability module)

- **5 test sites** across **3 components** carry `provider.get_tracer("loam.<component>", "0.1.0")` to install monkeypatch fixtures (NOT assertions on the literal — the tests install a tracer with that version arg into a fresh provider for fixture-isolated span capture). Same drift class — fixture-controlled literal that should track production for consistency:
  1. `framework/self-correction/tests/test_amendment_20_silent_excepts.py:56`
  2. `framework/dormancy/tests/test_d9_observability.py:61`
  3. `framework/dormancy/tests/test_d10_one_hour_outage.py:78`
  4. `framework/dormancy/tests/test_amendment_20_silent_excepts.py:66`
  5. `framework/observability-aggregator/tests/test_amendment_20_silent_excepts.py:47` (uses `loam.aggregator.nl` — installs into the `nl_path` module's `_TRACER` slot; production `nl_path.py:52` has NO version arg so the production side is not in F-OTEL-VERSION-BUMP scope, but the test fixture installer carries the same `"0.1.0"` literal as a stale-by-coincidence value)

After this PATCH, every `get_tracer(..., <version>)` call in the framework (production + monkeypatch fixtures) emits the tracer-version literal `"0.10.0"` matching the most-recent MINOR's per-component-version discipline (v0.10.0 bumped all 30 component pyprojects 0.9.0 → 0.10.0). Closes F-OTEL-VERSION-BUMP.

---

## §2 — Prime objective ladder

```
VALUE_PROPOSITION.md prime objective
   └─ "primary persona is a translation layer between the user's
       natural-language intent and AI-effective execution"
        └─ documented features work as advertised + documented-state
           matches actual-state (v1.0 quality-bar criterion #1)
             └─ per-component-version discipline (AC.HONEST.1) applies
                uniformly across all version-carrying surfaces (pyproject
                + __version__ + tracer-version arg)
                  └─ AC.OTVH.1 (every production observability.py /
                                  supervisor.py with a tracer-version arg
                                  emits "0.10.0", not stale "0.1.0" —
                                  closes F-OTEL-VERSION-BUMP at the
                                  production site)
                  └─ AC.OTVH.2 (every test-fixture monkeypatch installer
                                  with a tracer-version arg uses "0.10.0"
                                  for consistency with production —
                                  closes F-OTEL-VERSION-BUMP at the
                                  fixture-installer site)
                  └─ AC.OTVH.3 (idempotence — re-running the sweep
                                  produces zero new edits; no remaining
                                  "0.1.0" literals adjacent to
                                  get_tracer calls anywhere in framework/)
                  └─ AC.OTVH.4 (outcome-altitude dogfood probe — spawn
                                  a production tracer at runtime, read
                                  the emitted instrumentation_scope.version
                                  field, verify it equals "0.10.0")
                  └─ AC.OTVH.S (seal-diff: only the named observability /
                                  supervisor / test files + plan-doc +
                                  manifest + smoke writeup + STATE/roadmap/
                                  FIDRAFT admin + dev-sdlc seal anchor
                                  artefacts touched)
```

The two VALUE_PROPOSITION tests:

- **Primary-persona test** — extends the per-component-version honesty surface to the telemetry layer; a maintainer reading any span's `instrumentation_scope.version` in 6 months will see the actual current version, not a v0.1.0-era ghost. Closes a known documented-vs-actual drift surface deferred at v0.8.0.
- **Harness test** — no harness extension; closes a defect within the existing telemetry surface (the `get_tracer` proxy contract every component uses).

Composes with: AC.HONEST.1 (per-component-version discipline this PATCH extends to telemetry; v0.10.0 MINOR bumped per-component versions to 0.10.0 — this PATCH brings tracer-version into alignment), `feedback_loose_AC_text_fix_AC_not_implementation` (AC.OTVH.2 originally framed by FIDRAFT capture as "tests if any assert on tracer version" — empirically NO production assertions exist; tests install via monkeypatch with the literal as a fixture-controlled value; AC text tightened to match the actual fixture-installer scope, not the assertion scope the capture suggested).

Composes with: F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH discipline (verified empirically: no other FIDRAFT entries reference F-OTEL-VERSION-BUMP as a blocker / dependency / unblocker; only one other reference exists in `docs/plans/v0-8-0-honesty-cleanup.md:425` as a count-table entry, no flip needed).

---

## §3 — Component fence

**PATCH spans 6 production components but each touches only the single `get_tracer(..., <version>)` call site.** Seal anchor: dev-sdlc (the canonical seal-anchor for cross-component PATCH that touches multiple framework components but stays narrow in each — matches v0.8.0 AC.HONEST.1 precedent shape). Path-A (per-component seal anchor) declined per build-time D-OTVH.4: the change is one-line per file in 7+5=12 files; per-component sealing would multiply the seal ritual by 6× without sharpening the fence.

**PRIMARY (7 production files, 1 line each):**

- `framework/cost-governance/src/loam/cost_governance/observability.py` — line 30: `"0.1.0"` → `"0.10.0"`.
- `framework/self-correction/src/loam/self_correction/observability.py` — line 31: `"0.1.0"` → `"0.10.0"`.
- `framework/dormancy/src/loam/dormancy/observability.py` — line 40: `"0.1.0"` → `"0.10.0"`.
- `framework/reversibility-primitive/src/loam/reversibility_primitive/observability.py` — line 30: `"0.1.0"` → `"0.10.0"`.
- `framework/safety-layer/src/loam/safety_layer/observability.py` — line 32: `"0.1.0"` → `"0.10.0"`.
- `framework/orchestrator/src/loam/orchestrator/supervisor.py` — line 63: `"0.1.0"` → `"0.10.0"`.
- `framework/orchestrator/src/loam/orchestrator/observability.py` — line 31: `"0.1.0"` → `"0.10.0"`.

**PRIMARY (5 test fixture files, 1 line each):**

- `framework/self-correction/tests/test_amendment_20_silent_excepts.py` — line 56: `"0.1.0"` → `"0.10.0"`.
- `framework/dormancy/tests/test_d9_observability.py` — line 61: `"0.1.0"` → `"0.10.0"`.
- `framework/dormancy/tests/test_d10_one_hour_outage.py` — line 78: `"0.1.0"` → `"0.10.0"`.
- `framework/dormancy/tests/test_amendment_20_silent_excepts.py` — line 66: `"0.1.0"` → `"0.10.0"`.
- `framework/observability-aggregator/tests/test_amendment_20_silent_excepts.py` — line 47: `"0.1.0"` → `"0.10.0"`.

**PRIMARY (smoke writeup):**

- `docs/experiments/otel-tracer-version-honesty-hard-smoke.md` — slug-named per `F-CYCLE-ARTEFACT-SLUG-NAMING`. One outcome-altitude dogfood probe: spawn a production component's tracer at runtime, start a span, capture it via an in-memory exporter, read the `instrumentation_scope.version` field, verify it equals `"0.10.0"`.

**SECONDARY (admin docs — universal-admission):**

- `docs/STATE.md` — append v0.10.4 row to §2 (Change log section).
- `docs/release-roadmap.md` — append v0.10.4 row to §2 + v0.10.4 standalone bold entry to §3 Active version.
- `docs/FUTURE_IDEAS_DRAFT.md` — flip F-OTEL-VERSION-BUMP entry to RESOLVED (status flip; entry preserved for audit trail).

**TERTIARY (cycle bookkeeping):**

- `docs/plans/otel-tracer-version-honesty.md` — this file.
- `docs/plans/otel-tracer-version-honesty.manifest.yaml` — schema-v3 manifest.
- `plugins/dev-sdlc/seals/SEAL_COMMIT.otel-tracer-version-honesty` — seal narrative.
- `plugins/dev-sdlc/tests/SEAL_COMMIT` — sidecar bump (auto at seal-time).
- `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` — BASELINE pointer auto-bump (auto at seal-time per dev-sdlc-anchored amendment convention; pre-included in AC.OTVH.S allow-list).

**Out of fence:**

- Any change beyond the literal `"0.1.0"` → `"0.10.0"` substitution at the named call sites (HARD HALT #1).
- Any new `__version__` exports in the 6 affected components' `__init__.py` files (the alternative D-OTVH.1 Path A; declined — see §5). No `__init__.py` files touched.
- Any pyproject.toml bumps (PATCH rides predecessor MINOR per AC.HONEST.1 / D-NFCLEAN.4 / D-SDPD / v0.8.3 / v0.10.1 / v0.10.2 / v0.10.3 precedent).
- The OTel SDK itself, observability-aggregator's ingest pipeline, or any non-`get_tracer`-version-arg surface.
- Production sites that have NO version arg (`framework/observability-aggregator/.../nl_path.py:52`, `framework/telegram-interface/.../observability.py:33`, `framework/workspace-bootstrap/.../host.py:96`, `framework/primary-persona/.../observability.py:44`, plus the wrapper-style `def get_tracer():` modules in `workspace-sync` / `objective-tracker` / `self-upgrade` / `scope-of-work` that call `trace.get_tracer(_TRACER_NAME)` with name-only). These are not in F-OTEL-VERSION-BUMP scope (no stale literal to bump). Adding a version arg to them would be scope-creep.
- Edits outside fence = halt.

---

## §4 — Acceptance criteria (`AC.OTVH.*`)

Each AC maps to a verifiable acceptance signal. Method stays builder's call.

### AC.OTVH.1 — Production tracer-version literal swept to "0.10.0" across all 7 sites

Each of the 7 production sites enumerated in §3 PRIMARY has its `_TRACER = trace.get_tracer("loam.<component>", "0.1.0")` line updated to `_TRACER = trace.get_tracer("loam.<component>", "0.10.0")` per D-OTVH.1 (Path B — current literal "0.10.0" everywhere; Path A `__version__`-import declined as out-of-scope expansion). The component-name first arg is preserved verbatim (no other change to the line). Closes F-OTEL-VERSION-BUMP at the production site.

**Verdict GREEN if:** `grep -rn 'get_tracer("loam\.[a-z_.]*", "0\.1\.0")' framework/ --include="*.py"` returns ZERO matches in PRODUCTION (`src/`) paths post-source-edit. Companion grep `grep -rn 'get_tracer("loam\.[a-z_.]*", "0\.10\.0")' framework/ --include="*.py"` returns 7 matches at the named line offsets (one per file; line offset may shift ±1 if surrounding context changed, but the literal itself is updated).

**Verdict YELLOW if:** 6 of 7 sites updated (one missed) — partial-fix fault detectable by the grep.

**Verdict RED if:** any of the 7 production sites still carries `"0.1.0"` OR any non-target line was modified (e.g., the component-name arg corrupted) OR a new tracer-version arg was added to a site that previously had none (scope-creep into Path C territory).

`outcome-altitude: false` (function-altitude verification — grep is the assertion).

### AC.OTVH.2 — Test-fixture monkeypatch installer literal swept to "0.10.0" across all 5 sites

Each of the 5 test-fixture sites enumerated in §3 PRIMARY has its `provider.get_tracer("loam.<component>", "0.1.0")` line updated to `provider.get_tracer("loam.<component>", "0.10.0")`. These sites install monkeypatched tracers into module-level `_TRACER` slots for fixture-isolated span capture; they do NOT assert on the literal value (verified empirically — no test in the framework asserts on the literal `"0.1.0"` adjacent to a tracer-version context). Updating them keeps fixture instrumentation versions tracking production for consistency and prevents future drift confusion.

The original FIDRAFT F-OTEL-VERSION-BUMP capture text framed this as "tests if any assert on tracer version"; the empirical finding is that no assertions exist (only fixture installations). AC text tightened doc-only at plan-time per `feedback_loose_AC_text_fix_AC_not_implementation` to name the actual scope (fixture installations) rather than the assertion scope the capture suggested. Closes F-OTEL-VERSION-BUMP at the fixture-installer site.

**Verdict GREEN if:** `grep -rn 'get_tracer("loam\.[a-z_.]*", "0\.1\.0")' framework/ --include="*.py"` returns ZERO matches in TEST (`tests/`) paths post-source-edit. Companion grep `grep -rn 'get_tracer("loam\.[a-z_.]*", "0\.10\.0")' framework/ --include="*.py"` returns 12 total matches (7 production + 5 test).

**Verdict YELLOW if:** 4 of 5 sites updated (one missed) — partial-fix fault.

**Verdict RED if:** any of the 5 test-fixture sites still carries `"0.1.0"` OR any test BREAKS post-edit (the fixture installer is fixture-controlled but tests using the fixture should pass identically — the version arg only affects the emitted span's `instrumentation_scope.version` field, not span content).

`outcome-altitude: false`.

### AC.OTVH.3 — Idempotence — no remaining "0.1.0" literals adjacent to get_tracer

After AC.OTVH.1 and AC.OTVH.2 land, the framework tree contains ZERO `get_tracer(..., "0.1.0")` call sites. Re-running the same sweep (any tool, any pattern) produces zero new edits. Future drift detectable by the grep — if a new component is added with the stale literal, the same grep flags it.

The check explicitly excludes pyproject.toml `version = "0.1.0"` lines (those are project versions, not tracer-version args, and the v0.8.0 AC.HONEST.1 + v0.10.0 sweep already established their lifecycle). The check explicitly excludes `framework/hands-off-lifecycle/tests/test_first_run.py` `'version = "0.1.0"'` strings (test fixtures synthesizing pyproject content for first-run scenarios; not tracer-version args).

**Verdict GREEN if:** `grep -rn 'get_tracer.*"0\.1\.0"' framework/ --include="*.py"` returns ZERO matches AND a re-run of the sweep tool/method produces zero diffs.

**Verdict YELLOW if:** zero matches BUT the grep pattern is the only assertion (no second-tool cross-check) — single-tool blind-spot fault.

**Verdict RED if:** any `get_tracer(..., "0.1.0")` literal remains anywhere in `framework/` source.

`outcome-altitude: false`.

### AC.OTVH.4 — Outcome-altitude dogfood probe (runtime-emitted instrumentation_scope.version)

Live runtime probe spawns a production tracer (e.g., the `_TRACER` from `framework/cost-governance/src/loam/cost_governance/observability.py`), starts a span, captures the span via an in-memory `InMemorySpanExporter` attached to a fresh `TracerProvider`, reads the captured span's `instrumentation_scope.version` attribute, and verifies it equals `"0.10.0"` (NOT `"0.1.0"`). Documented at `docs/experiments/otel-tracer-version-honesty-hard-smoke.md` (slug-named per `F-CYCLE-ARTEFACT-SLUG-NAMING`) with verbatim runtime output.

This probe is the canonical outcome-altitude check: the AC.OTVH.1 grep verifies the source-text edit; AC.OTVH.4 verifies the change actually propagates through OTel's instrumentation contract to the wire.

The probe runs ONE component (cost-governance is the canonical example; choice is builder's call) — not all 6 — because OTel's `get_tracer(name, version)` contract is uniform; if it works for one, it works for all. Per-component verification would multiply runtime cost without sharpening the verdict.

**Verdict GREEN if:** smoke writeup at the slug-named path documents the probe with verbatim Python output showing `instrumentation_scope.version == "0.10.0"` for the chosen component's tracer.

**Verdict YELLOW if:** writeup exists but uses a non-runtime grep-only verification — would duplicate AC.OTVH.1 without adding outcome-altitude value.

**Verdict RED if:** writeup absent OR runtime probe shows `"0.1.0"` (regression — source edit didn't actually propagate).

`outcome-altitude: true` (runtime invocation against the production-shipped contract).

### AC.OTVH.S — Seal-diff discipline

`git diff --name-only <plan-commit>..<seal-commit>` shows changes ONLY under:

- `framework/cost-governance/src/loam/cost_governance/observability.py`
- `framework/self-correction/src/loam/self_correction/observability.py`
- `framework/dormancy/src/loam/dormancy/observability.py`
- `framework/reversibility-primitive/src/loam/reversibility_primitive/observability.py`
- `framework/safety-layer/src/loam/safety_layer/observability.py`
- `framework/orchestrator/src/loam/orchestrator/supervisor.py`
- `framework/orchestrator/src/loam/orchestrator/observability.py`
- `framework/self-correction/tests/test_amendment_20_silent_excepts.py`
- `framework/dormancy/tests/test_d9_observability.py`
- `framework/dormancy/tests/test_d10_one_hour_outage.py`
- `framework/dormancy/tests/test_amendment_20_silent_excepts.py`
- `framework/observability-aggregator/tests/test_amendment_20_silent_excepts.py`
- `docs/experiments/otel-tracer-version-honesty-hard-smoke.md`
- `docs/STATE.md`
- `docs/release-roadmap.md`
- `docs/FUTURE_IDEAS_DRAFT.md`
- `docs/plans/otel-tracer-version-honesty.md`
- `docs/plans/otel-tracer-version-honesty.manifest.yaml`
- `plugins/dev-sdlc/seals/SEAL_COMMIT.otel-tracer-version-honesty`
- `plugins/dev-sdlc/tests/SEAL_COMMIT`
- `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` (BASELINE pointer auto-bump at seal-time — bookkeeping; pre-included in this allow-list per the dev-sdlc-anchored amendment auto-bump fence convention)

NO entries in pyproject.toml; NO entries in any component's `__init__.py`; NO entries in any non-named source file. NO `__version__` updates.

**Verdict GREEN if:** `git diff --name-only <plan-commit>..<seal-commit>` matches the allow-list above with zero unlisted entries.

**Verdict YELLOW if:** all entries match BUT a benign extra (e.g., a docs/ entry not in the allow-list) appears — tighten allow-list doc-only post-build per `feedback_loose_AC_text_fix_AC_not_implementation` if intent matched.

**Verdict RED if:** any entry outside fence appears (e.g., pyproject.toml bump, `__init__.py` edit, plugin source edit beyond dev-sdlc seal anchor).

`outcome-altitude: false`.

---

## §5 — Decisions builder rules at build time

### D-OTVH.1 — Path B (current literal "0.10.0") chosen over Path A (`__version__` import)

The FIDRAFT F-OTEL-VERSION-BUMP capture proposed two paths: (A) "import `__version__` from each component's package + use it as the tracer-version arg" or (B) "bump the literal to `0.8.0` everywhere." Empirical investigation at plan-time (2026-05-14):

- **Path A blocker:** none of the 6 affected components export `__version__` from their `__init__.py`. Only 4 packages in `framework/` export `__version__` today (workspace-sync, loam-init, tools/loam, tools/orphan-plist-cleanup); cost-governance / self-correction / dormancy / reversibility-primitive / safety-layer / orchestrator do NOT. Adding `__version__ = "0.10.0"` to each of 6 `__init__.py` files would (a) expand scope to 6 new files outside the F-OTEL-VERSION-BUMP capture's scope, (b) introduce a maintenance surface (every MINOR bump now requires updating 6 `__init__.py` files in addition to pyproject.toml), and (c) duplicate the per-component-version discipline already encoded in pyproject.toml. The runtime cost of `from importlib.metadata import version; version("loam-<component>")` is acceptable but adds an import-time package-metadata call to every component on import.

- **Path B advantages:** (a) one-line edit per file; (b) literal value `"0.10.0"` matches the per-component-version discipline established at AC.HONEST.1 and bumped at v0.10.0 (current pyproject.toml versions for all 6 components verified at "0.10.0"); (c) zero new files; (d) the future drift surface (next MINOR bump v0.11.0 will need to re-bump these literals) is the exact same surface the per-component-version discipline already manages — adding to its inventory is a known-bounded cost; (e) matches the FIDRAFT capture's OR option verbatim.

**Ruling:** Path B. Future-drift mitigation captured as new FIDRAFT entry F-OTEL-VERSION-DYNAMIC-IMPORT (at §15 of this plan-doc, mirrored to `docs/FUTURE_IDEAS_DRAFT.md`) — proposes the `__version__`-import shape as a follow-on cycle gated on either: (a) a future cycle that's already touching the 6 components' `__init__.py` for other reasons (no incremental scope cost), or (b) a structural drift (e.g., 3+ MINORs in a row where the literals were forgotten to bump).

### D-OTVH.2 — Test fixture sites included in scope (not deferred)

The F-OTEL-VERSION-BUMP capture text reads "tests if any assert on tracer version + verification." Empirical investigation at plan-time: NO test in the framework asserts on the literal `"0.1.0"` adjacent to a tracer-version context (verified via `grep -rn '"0.1.0"' --include="*.py" /Users/lukeivers/loam/framework/` cross-referenced with `get_tracer` call sites). What the 5 test sites DO is install monkeypatched tracers via `provider.get_tracer("loam.<component>", "0.1.0")` for fixture-isolated span capture.

**Question:** are these test-fixture installer sites in F-OTEL-VERSION-BUMP scope?

**Two paths:**

- Path X: **In scope.** Same `"0.1.0"` literal in the same drift class; same maintainer-cognitive-load surface (a maintainer reading either kind of site sees a stale version string). Updating them keeps fixture instrumentation versions tracking production. AC.OTVH.2 names them explicitly.
- Path Y: **Out of scope.** Production-only PATCH; defer test sites to a follow-on. The literal is fixture-controlled; the version arg in a monkeypatched tracer doesn't propagate to production telemetry.

**Ruling:** Path X. The test-fixture installer literal is the same drift class as the production literal (both are stale-by-design from the v0.1.0 era); leaving them stale would (a) require a follow-on PATCH for the same FIDRAFT entry and (b) leave test-fixture-emitted spans with `instrumentation_scope.version == "0.1.0"` while production emits `"0.10.0"` — confusing for any future contributor running `pytest -s` and reading span dumps. AC.OTVH.2 ratifies the inclusion.

### D-OTVH.3 — `loam.aggregator.nl` test-fixture site included despite production having no version arg

The 5th test fixture site at `framework/observability-aggregator/tests/test_amendment_20_silent_excepts.py:47` installs `provider.get_tracer("loam.aggregator.nl", "0.1.0")` — but the production-side `framework/observability-aggregator/src/loam/observability_aggregator/nl_path.py:52` reads `_TRACER = trace.get_tracer("loam.aggregator.nl")` (NO version arg). Production is not in F-OTEL-VERSION-BUMP scope (no stale literal to bump on production).

**Question:** does this test-fixture site need to be updated since production has no version arg to track?

**Ruling:** YES, included. The test-fixture installer carries the same `"0.1.0"` literal as a stale-by-coincidence value (the test was likely copy-pasted from the dormancy test fixture). Leaving it stale while updating the other 4 test fixtures would create test-corpus inconsistency. The production-side getting no version arg is a separate concern (could capture as F-OTEL-PRODUCTION-NL-PATH-VERSION if future drift makes it worth fixing) and is explicitly out of scope for this PATCH.

### D-OTVH.4 — Single dev-sdlc seal anchor over per-component sealing

This PATCH touches 6 production components + 3 test-component trees. Per-component sealing would multiply the seal ritual by 6× (each component's `test_no_sealed_amendments.py` sees the cross-component diff and trips the fence) without sharpening the substance. The dev-sdlc seal anchor is the canonical pattern for cross-component PATCHes that touch many components narrowly (matches v0.8.0 AC.HONEST.1 precedent — 30 pyproject bumps across 30 components, single dev-sdlc seal).

**Ruling:** dev-sdlc seal anchor. The 6 affected components' own `test_no_sealed_amendments.py` files DO need to admit the cross-component diff via universal-paths or extra-allowed-prefixes wildcards if their fences are tight; verify mid-build whether any component-fence trips, and if so, widen via the universal-paths admission in the dev-sdlc manifest (matches the v0.8.0 admission shape). HARD HALT if any component-fence widening would require new prefix entries beyond what the v0.8.0 / v0.10.0 admission allow.

### D-OTVH.5 — pyproject.toml versions stay at 0.10.0 (PATCH discipline)

Per AC.HONEST.1 / D-NFCLEAN.4 / D-SDPD / v0.8.3 / v0.10.1 / v0.10.2 / v0.10.3 precedent: PATCHes ride the predecessor MINOR's per-component-version. v0.10.0 bumped all 30 component pyprojects from 0.9.0 → 0.10.0. v0.10.4 (this PATCH) does NOT touch any pyproject.toml.

**Ruling:** zero pyproject.toml edits.

---

## §6 — Out of scope (explicit)

- Any change to OTel SDK version, ingest pipeline, span attribute semantics, or the `instrumentation_scope.name` first arg.
- Adding a `__version__` export to any component's `__init__.py` (D-OTVH.1 Path A declined).
- Bumping any component's pyproject.toml version (D-OTVH.5).
- Touching any production code path that does NOT carry `_TRACER = trace.get_tracer(..., "0.1.0")` — e.g., the wrapper-style `def get_tracer(): return trace.get_tracer(_TRACER_NAME)` modules (workspace-sync, objective-tracker, self-upgrade, scope-of-work) or production sites with no version arg (telegram-interface, observability-aggregator/nl_path, workspace-bootstrap/host, primary-persona/observability).
- Adding a version arg to any production site that previously had none (would be Path C territory; out of scope).
- Updating `framework/observability-aggregator/.../nl_path.py:52` to add a version arg (D-OTVH.3 — separate concern, separate FIDRAFT if it surfaces).
- Test files that synthesize pyproject.toml content with `version = "0.1.0"` (`framework/hands-off-lifecycle/tests/test_first_run.py` lines 907 / 914 / 920 / 1000 / 1020 / 1090 — these are pyproject fixtures for first-run scenarios, NOT tracer-version args).
- The `assert result.mcp_json_reason == "skipped_v0_1_0_no_graphiti"` assertion at `framework/workspace-bootstrap/tests/test_AC47_3_write_failure_graceful.py:186` (this is a code-name string literal carrying `v0_1_0` as part of a sentinel value; not a tracer-version reference).
- Any other FIDRAFT entry beyond F-OTEL-VERSION-BUMP (verified empirically: no other FIDRAFT references F-OTEL-VERSION-BUMP as a blocker / dep / unblocker).

---

## §7 — HARD HALTs (build-time)

1. **Out-of-fence edit discovered as necessary mid-build.** If any line beyond the literal `"0.1.0"` → `"0.10.0"` substitution at the 12 named call sites needs to change for correctness, halt and surface for owner ruling. Do NOT silently extend scope.
2. **Empirical-recheck-before-halt discipline.** If you reach a "this is impossible" / "structurally infeasible" conclusion, run the 4-step discipline: state evidence; ≥3 alternative hypotheses; empirically test each; halt only after confirmation of structural infeasibility.
3. **Halt-and-surface ODD violations** including in surrounding code per `feedback_subagent_odd_violation_halt`. If a non-target line in any of the 12 named files violates ODD §2.5 (non-objective code), surface as halt-and-surface finding in §status; do NOT silently fix.
4. **No `--amend`** per `feedback_no_amend_in_agent_dispatches`. If a corrective is needed post-source-edit, create a NEW commit. The collapse of audit trail via `--amend` is forbidden.
5. **Test regression you cannot trace to your edit.** If `pytest framework/cost-governance/ framework/self-correction/ framework/dormancy/ framework/reversibility-primitive/ framework/safety-layer/ framework/orchestrator/ framework/observability-aggregator/` (or a more narrowly-scoped equivalent) fails post-edit and the failure mode is not obviously the version-arg change, halt and surface.
6. **Component-fence-widening required beyond v0.8.0 / v0.10.0 admission shape** per D-OTVH.4. If any of the 6 affected components' `test_no_sealed_amendments.py` trips a fence that requires new prefix entries beyond the existing universal-paths admission shape, halt and surface.
7. **No `__version__` introduction.** If during build you decide Path A (D-OTVH.1) would be cleaner, do NOT silently switch — halt and surface for owner re-ruling.

---

## §8 — Dependencies

- v0.10.3 PATCH SHIPPED PUBLIC (sealed `44c28e6`; published `3cd7983`; predecessor for build-forward per `feedback_build_forward_on_publish_pending`).
- v0.10.0 MINOR (per-component-version discipline bumped to 0.10.0 — the literal this PATCH brings tracer-version into alignment with).
- v0.8.0 AC.HONEST.1 (the per-component-version discipline this PATCH structurally extends to the telemetry layer).
- v0.7.4 release-CLI runner (the `loam release` substrate this PATCH publishes via — auto-backfill helpers in scope).
- v0.10.0 + v0.10.1 + v0.10.2 + v0.10.3 release-CLI gate stack (release-CLI gates ready for scope-descriptive plan-doc paths via the `--plan-doc` flag).
- F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH discipline (captured 2026-05-14 d9776ba) — verified empirically that no other FIDRAFT entries reference F-OTEL-VERSION-BUMP as a blocker / dep / unblocker.

---

## §9 — Estimated AI-time

| Stage | Estimated band | Midpoint |
|---|---|---|
| Plan-doc + manifest authoring | 15-25 min | ~20 min |
| Source-edit (12 one-line edits + slug-named smoke writeup with runtime probe + STATE/roadmap admin + FIDRAFT flip) | 20-35 min | ~28 min |
| `loam amend validate` + manifest baseline backfill + `apply` + `seal` | 5-10 min | ~7 min |
| §13 §status backfill commit + roadmap-row seal-SHA backfill | 3-5 min | ~4 min |
| **Total** | **~43-75 min** | **~59 min** |

In-band against the FIDRAFT capture's 30-60 min band (~45 min midpoint). Slightly over-band on the upper edge because the plan-doc decided to include the 5 test-fixture sites (D-OTVH.2) and the dogfood probe (AC.OTVH.4) — both add ~15 min total but tighten the closure. Per `feedback_duration_estimation_rubric`: tool-call estimate ~400-600 calls × 0.1-0.15 min/call = 40-90 min raw; ~58 min midpoint accounts for parallel tool calls reducing critical path.

Owner gate-review time is separate (depends on dispatcher availability for publish ratification per ASK-FIRST).

---

## §11 — Authority chain

1. `docs/release-versioning-policy.md` (PATCH classification)
2. `feedback_version_numbers_at_release_time` (version derived at build-commence-time; `next_PATCH(v0.10.3) = v0.10.4`)
3. `feedback_scope_descriptive_ac_ids` (AC family `AC.OTVH.*`; slug `otel-tracer-version-honesty`)
4. `feedback_plan_before_code` (plan-doc + manifest BEFORE source edits)
5. v0.8.0 AC.HONEST.1 (per-component-version discipline this PATCH extends to telemetry layer)
6. F-OTEL-VERSION-BUMP FIDRAFT (the entry this PATCH closes)
7. F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH (discipline for flipping dependent FIDRAFT entries when an unblocker lands; verified no dependents exist)
8. F-CYCLE-ARTEFACT-SLUG-NAMING (slug-named smoke writeup at `docs/experiments/otel-tracer-version-honesty-hard-smoke.md`)
9. `feedback_loose_AC_text_fix_AC_not_implementation` (AC.OTVH.2 text tightened doc-only at plan-time to match empirical scope — fixture installations not assertions)
10. `feedback_subagent_odd_violation_halt` (HARD HALT #3)
11. `feedback_no_amend_in_agent_dispatches` (HARD HALT #4)
12. `feedback_duration_estimation_rubric` (§9)
13. `feedback_build_forward_on_publish_pending` (§8 — v0.10.3 sealed-public; v0.10.4 builds forward)

---

## §12 — Source items (FIDRAFT entries closed by this PATCH)

- **F-OTEL-VERSION-BUMP** (`docs/FUTURE_IDEAS_DRAFT.md:260`) — captured 2026-05-10 from v0.8.0 AC.HONEST.1 in-cycle finding. Activation gate: "next telemetry-touching cycle OR pre-v1.0 sweep." This PATCH dispatches against the second activation gate (pre-v1.0 sweep on the per-component-version discipline surface). Status flips to RESOLVED in §source-edit commit; entry preserved with RESOLVED block citing this plan-doc + smoke writeup paths.

---

## §13 — §status

**Build cycle:** SHIPPED LOCAL 2026-05-14. Single-cycle PATCH closing FIDRAFT F-OTEL-VERSION-BUMP via 12 one-line literal substitutions across 7 production observability/supervisor sites + 5 test-fixture monkeypatch installer sites; slug-named outcome-altitude dogfood probe; STATE/roadmap/FIDRAFT admin. Sealed local; awaiting dispatcher dogfood publish per ASK-FIRST.

**Plan-doc commits:** plan-doc + manifest `5d0ca57`; source-edit (12 literal substitutions + slug-named smoke writeup with runtime probe + STATE/roadmap admin + F-OTEL-VERSION-BUMP RESOLVED + new FIDRAFT F-OTEL-VERSION-DYNAMIC-IMPORT capture) `b3bc24c`; manifest baseline backfill `963a609`; apply auto-commit (BASELINE + sidecar bump to `b3bc24c`) `6abe3c7`; seal commit (deterministic seal) `aa78baf`.

### AC verdict matrix

| AC | Verdict | Evidence |
|---|---|---|
| AC.OTVH.1 — Production tracer-version literal swept to "0.10.0" across all 7 sites | GREEN | `grep -rn 'get_tracer("loam\.[a-z_.]*", "0\.1\.0")' framework/ --include="*.py"` returns 0 matches in `src/` paths post-source-edit; companion `grep -rn 'get_tracer("loam\.[a-z_.]*", "0\.10\.0")' framework/ --include="*.py"` returns 7 production matches at the named line offsets (cost-governance/observability:30 + self-correction/observability:31 + dormancy/observability:40 + reversibility-primitive/observability:30 + safety-layer/observability:32 + orchestrator/supervisor:63 + orchestrator/observability:31). Component-name first arg preserved verbatim across all 7 sites. |
| AC.OTVH.2 — Test-fixture monkeypatch installer literal swept to "0.10.0" across all 5 sites | GREEN | Same grep pattern returns 0 matches in `tests/` paths post-source-edit; companion `"0.10.0"` grep returns 5 test matches (self-correction/test_amendment_20:56 + dormancy/test_d9:61 + dormancy/test_d10:78 + dormancy/test_amendment_20:66 + observability-aggregator/test_amendment_20:47). 19 tests across the 5 modified test files PASS post-edit (verified mid-build at commit `b3bc24c` with pytest-asyncio installed per `install-from-source.txt`). AC text tightened doc-only at plan-time per `feedback_loose_AC_text_fix_AC_not_implementation` (FIDRAFT capture's "tests if any assert on tracer version" framing was inaccurate to the actual fixture-installer scope — empirically verified zero production assertions on the literal). |
| AC.OTVH.3 — Idempotence — no remaining "0.1.0" literals adjacent to get_tracer | GREEN | `grep -rn 'get_tracer.*"0\.1\.0"' framework/ --include="*.py"` returns 0 matches post-source-edit. The check explicitly excludes pyproject.toml `version = "0.1.0"` lines (project versions, not tracer-version args), `framework/hands-off-lifecycle/tests/test_first_run.py` synthesized pyproject fixtures (lines 907 / 914 / 920 / 1000 / 1020 / 1090), and `framework/workspace-bootstrap/tests/test_AC47_3_write_failure_graceful.py:186` `"skipped_v0_1_0_no_graphiti"` sentinel value (code-name string, not a tracer-version reference). Sweep re-run produces zero new edits. |
| AC.OTVH.4 — Outcome-altitude dogfood probe (runtime-emitted instrumentation_scope.version) | GREEN | `docs/experiments/otel-tracer-version-honesty-hard-smoke.md` (slug-named per `F-CYCLE-ARTEFACT-SLUG-NAMING`) §3.1 documents single-component runtime probe (cost-governance) with verbatim Python output showing `instrumentation_scope.version == "0.10.0"` on a captured span. §3.2 cross-verifies all 7 production tracers carry `version=0.10.0` at runtime — uniform across cost_governance + self_correction + dormancy + reversibility_primitive + safety_layer + orchestrator/observability + orchestrator/supervisor. The probe verifies the source-text edit propagates through OTel's `get_tracer(name, version)` contract to the wire (not just the literal in source). |
| AC.OTVH.S — Seal-diff discipline | GREEN | `git diff --name-only 5d0ca57..aa78baf` shows changes only under: 7 production observability/supervisor files (cost-governance + self-correction + dormancy + reversibility-primitive + safety-layer + orchestrator/observability + orchestrator/supervisor); 5 test-fixture monkeypatch installer files (self-correction/test_amendment_20 + dormancy/test_d9 + dormancy/test_d10 + dormancy/test_amendment_20 + observability-aggregator/test_amendment_20); slug-named smoke writeup at `docs/experiments/otel-tracer-version-honesty-hard-smoke.md`; universal-admission docs (`docs/STATE.md` + `docs/release-roadmap.md` + `docs/FUTURE_IDEAS_DRAFT.md`); plan-doc + manifest (`docs/plans/otel-tracer-version-honesty.{md,manifest.yaml}`); dev-sdlc seal anchor artefacts (seal narrative + `plugins/dev-sdlc/tests/SEAL_COMMIT` sidecar bump + `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` BASELINE pointer auto-bump — pre-included in §3 allow-list per the plan-doc-template-auto-bump-fence convention). NO entries in pyproject.toml; NO entries in any `__init__.py`; NO `__version__` updates. |

### AI-time actuals

| Stage | Estimated (§9) | Actual |
|---|---|---|
| Plan-doc + manifest authoring | 15-25 min | ~22 min |
| Source-edit (12 literal substitutions + slug-named smoke writeup with runtime probe + STATE/roadmap admin + FIDRAFT flip + new FIDRAFT capture) | 20-35 min | ~28 min |
| `loam amend validate` + manifest baseline backfill + `apply` + `seal` (incl. one validate fixup for smoke_outcome length) | 5-10 min | ~6 min |
| §13 §status backfill commit + roadmap-row seal-SHA backfill | 3-5 min | ~5 min |
| **Total** | **~43-75 min** | **~61 min** |

In-band — landed cleanly without HARD HALTs; one minor `loam amend validate` iteration on the manifest's `smoke_outcome` field (length cap 200 chars; trimmed twice from 468 → 238 → 152 chars).

### Halt-and-surface findings

**No HARD HALTs fired in-cycle.**

**Pre-existing-test-failure clarification:** orchestrator's 2 failures (`test_pos_session_start.py::test_ready_path_when_both_services_up` + `test_AC_V11_E_1_memory_skipped_when_plist_absent`) are pre-existing on main (verified via `git stash` baseline at plan-doc commit `5d0ca57`); they are NOT caused by the tracer-version edit. Documented under the F-TF-* class (rebrand-residue from the v0.5.1 split-worktrees migration; expected `'pos v2 ready'` vs actual `'loam ready'`); separate cleanup concern, NOT in F-OTEL-VERSION-BUMP scope.

**Test-environment context:** the homebrew Python 3.13 environment lacks `pytest-asyncio` by default; per `install-from-source.txt` (post-v0.8.0 root-cause closure of the asyncio-marked failure class), pytest-asyncio>=0.23 is the documented install dependency. Tests verified GREEN post-install; pre-existing failure modes documented in F-TF-1/2/3/4 captured at v0.8.0.

**Empirical-recheck-before-halt discipline:** never fired (each of the 12 literal substitutions had an unambiguous fix-target derivable from the FIDRAFT capture's proposed-shape line + plan-doc D-OTVH.1 ruling).

**One AC text tightening at plan-time** (per `feedback_loose_AC_text_fix_AC_not_implementation`): AC.OTVH.2 originally framed by FIDRAFT capture as "tests if any assert on tracer version" — empirically NO production assertions exist; tests install via `provider.get_tracer(...)` monkeypatch with the literal as a fixture-controlled value. AC text tightened doc-only at plan-authoring-time to name the actual scope (fixture installations) rather than the assertion scope the capture suggested. Doc-only; no source-text divergence from intent.

**One FIDRAFT entry flipped to RESOLVED:** F-OTEL-VERSION-BUMP at `docs/FUTURE_IDEAS_DRAFT.md:260`; entry preserved with RESOLVED block citing this PATCH cycle's plan-doc + smoke writeup paths.

**One new FIDRAFT entry captured:** F-OTEL-VERSION-DYNAMIC-IMPORT — proposes the `__version__`-import shape as a follow-on cycle gated on either: (a) a future cycle that's already touching the 6 components' `__init__.py` for other reasons, or (b) structural drift signal (3+ MINORs in a row where the literals were forgotten to bump).

**F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH discipline verified:** `grep -rn "F-OTEL-VERSION-BUMP" docs/` returned 1 reference at `docs/FUTURE_IDEAS_DRAFT.md:260` (the entry itself) plus 1 unrelated count-table reference at `docs/plans/v0-8-0-honesty-cleanup.md:425`. No other FIDRAFT entries reference F-OTEL-VERSION-BUMP as a blocker / dep / unblocker; no flip-on-unblock action needed.

**One manifest schema fixup at validate-time:** `smoke_outcome` field length-capped at 200 chars; initial draft was 468 chars; trimmed twice (238 → 152) to fit. Doc-level; no semantic drift.

---

## §14 — Method decisions

Plan-doc's §5 names the build-time decisions (D-OTVH.{1,2,3,4,5}). Each is a deterministic ruling at plan-time; no in-flight builder rulings expected unless a HARD HALT fires.

---

## §15 — New FIDRAFT capture (deferred follow-on)

- **F-OTEL-VERSION-DYNAMIC-IMPORT — Replace literal tracer-version with `importlib.metadata.version` import.** Captured 2026-05-14 from D-OTVH.1 Path A deferral. The current implementation (Path B per this PATCH) hardcodes `"0.10.0"` as the tracer-version arg in 12 sites. Future drift is bounded by the same per-component-version discipline that manages pyproject.toml versions. Proposed shape: replace `_TRACER = trace.get_tracer("loam.<component>", "0.10.0")` with `_TRACER = trace.get_tracer("loam.<component>", version("loam-<component>"))` (using `from importlib.metadata import version`). Eliminates future drift entirely; tracer-version always reflects the installed package version. Cost: an `importlib.metadata.version` call at module-import time per component (acceptable). Composes with: F7-PLUGIN-VERSION (similar dynamic-version-import pattern for plugin api_version field). AI-time band: 30-50 min (sweep 12 sites + handle ImportError fallback for development installs + verify across `pip install -e .` AND wheel-installed scenarios). Status: capture-only. Activation gate: (a) next cycle that's already touching the 6 components' `__init__.py` for other reasons (no incremental scope cost), OR (b) structural drift signal (e.g., 3+ MINORs in a row where the literals were forgotten to bump).
