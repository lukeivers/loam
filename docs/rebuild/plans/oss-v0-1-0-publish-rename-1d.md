# OSS v0.1.0 publish — M1d — OTel `pos.*` → `loam.*` roots — sub-plan

**Status:** plan-doc (pre-build, plan-before-code). 2026-04-29.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Series master:** `docs/rebuild/plans/oss-v0-1-0-publish-rename.md` (committed `ebe0a57`, 2026-04-29).
**Prior sub-amendments:**
- M1a — docs/prose-only brand rebrand (sealed `143d465`, 2026-04-29; SHA-register in `oss-v0-1-0-publish-rename-1a.md` §12).
- M1b — env-vars + per-host config dir + migration helper (sealed `d97c8c1`, 2026-04-29; SHA-register in `oss-v0-1-0-publish-rename-1b.md` §14).
- M1c — launchd labels + plist filename cascade + sibling migration helper (sealed `1e99d0b`, 2026-04-29; SHA-register in `oss-v0-1-0-publish-rename-1c.md` §14).
**Programme position:** Fourth sub-amendment of the M1.rename multi-amendment series. Independent of M1a / M1b / M1c in scope; lands fourth per series-master ladder ordering.
**Authority documents:**
- `docs/rebuild/plans/loam-rename-decisions.md` Tier-1 item 5 (OTel root rebrand; attribute names below the second segment unchanged).
- `.scratch/claude-output/loam-rename-migration-plan.md` §3.5 (OTel surface mechanics + breaking-change flag).
- `docs/rebuild/plans/oss-v0-1-0-publish-rename.md` §2 (sub-amendment ladder), §5 (series-wide hard constraints), §7 (series-wide halt triggers).
- `docs/rebuild/plans/oss-v0-1-0-publish.md` §5 (programme master plan; M1d row in the M1a..M1g ladder per M1b's precursor commit `7be713b`).

---

## 1. Summary / TLDR

**M1d lands the OTel `pos.*` → `loam.*` root rebrand:**

1. **Span / event names rebase.** Every span name, event name, and tracer-emitted name where the FIRST segment is `pos` rebases the first segment to `loam`. Second-and-below segments unchanged (e.g. `pos.cost.budget_breach.amount` → `loam.cost.budget_breach.amount`; the `.amount` and its sibling attribute keys stay verbatim).
2. **Attribute keys rebase.** OTel span attributes prefixed with `pos.<comp>.<key>` (e.g. `pos.session.id`, `pos.scope.id`, `pos.objective.id`, `pos.objective.status`, `pos.retention.class`, `pos.prompt.type`) rebase the first segment to `loam.`. The `.id`, `.status`, etc. tail segments are unchanged. Memory-system records' bare `retention_class` field (no namespace prefix) is unchanged — it lives outside the OTel namespace and is not in M1d's scope.
3. **Tracer / logger / meter names rebase.** Every `trace.get_tracer("pos.X...")`, `logging.getLogger("pos.X...")`, `get_meter("pos.X...")` callsite rebases. Tracer-name conventions in this codebase: `pos.<component_package>` (e.g. `pos.cost_governance`, `pos.safety_layer`, `pos.self_correction`, `pos.telegram_interface`, `pos.reversibility_primitive`, `pos.scope_of_work`, `pos.bootstrap`, `pos.aggregator`, `pos.aggregator.nl`, `pos.aggregator.store`, `pos.aggregator.ingest`, `pos.degradation`, `pos.orchestrator`, `pos.hands_off_lifecycle`).
4. **Aggregator namespace defaults rebase.** `framework/observability-aggregator/src/config.py::self_namespace_prefix: str = "pos.aggregator"` and the three function-default mirrors in `ingest.py` rebase to `"loam.aggregator"`. The aggregator's `service.name` Resource attribute rebases. The aggregator's `TRACER_TO_COMPONENT` lookup map (`schema.py`) keys rebase.
5. **Tests and fixtures rebase.** Every test that asserts a literal `pos.X` span/event/attribute/tracer name updates its assertion to `loam.X`. Test fixtures emitting under `pos.*` for inspection rebase emission strings.
6. **Live component docs rebase.** `framework/<comp>/docs/*.md` files that name OTel roots in worked examples / architecture diagrams rebrand.
7. **Component proposal docs rebase.** `docs/rebuild/components/<comp>/proposal.md` files that name OTel roots in design contracts rebrand. (`research.md`, `research-plan.md`, `brief.md`, `component.md` historical-record files preserved per M1a/b/c convention — they are frozen at design / handoff time.)
8. **`docs/odd-in-pos.md` worked examples rebase.** Two callsites (lines ~100, ~255) cite `pos.safety.scope_kill` and `pos.cost.ceiling_warning` as worked-example span/event names; rebrand.

**Hard cutover** per series-master §1 D-RNM.3. No dual-emit shim that publishes spans under both `pos.*` and `loam.*`. No aggregator query-layer compat that reads both prefixes. Existing retention-DB rows under `pos.*` stay queryable as historical data (rows are not modified — only emit-side and query-time-filter literals change). Pre-public release; zero existing external consumers; the cutover boundary is a single seal.

**Documented-roots count:** the migration plan §3.5 catalogue lists 23 roots. Empirical inventory at plan-authoring time enumerates **25** roots in the live tree (the catalogue + two roots that appear in the live tree but are not in the §3.5 enumeration: `pos.sync` (workspace-sync, post-research addition) and `pos.memory` (used by the aggregator's mapper for memory-system records — workspace-sync was added after the research; memory-system was implicit in §3.5's "memory's hand-rolled sinks" comment). All 25 roots rebase per the locked Tier-1 #5 ruling. **Halt-and-surface (non-blocking).** See §11 finding #1 for the surface-inventory disclosure; the per-doc catalogue mismatch is non-blocking — the ruling text "all 23 roots" is a count, not an enumeration ceiling, and the post-build `loam.*` count + the absence-of-`pos.*` grep both bind the post-rename invariant.

**`pos.degradation`** rebases to `loam.degradation` in M1d (mechanical first-segment substitution). The Tier-2 graceful-degradation → dormancy rename at M1f (per series-master ladder) cascades `loam.degradation` → `loam.dormancy` as part of its component-rename scope. Splitting prevents a two-step rename inside one amendment and keeps M1d's contract purely first-segment substitution.

**What does NOT land in M1d** (deferred per series-master §2 ladder):
- Workspace-side `<workspace>/.pos/` sentinel directory — distinct surface; M1b discipline carried forward.
- Internal Python identifiers carrying `POS_V2_` / `pos_v2` / `pos-v2` decoration (`_POS_V2_*`, `CANONICAL_POS_V2_PATH`, `pos_v2_root`, `--pos-v2-root` shell flag) — namespace work; M1e.
- launchd labels — M1c (sealed).
- Per-host config dir + env-vars — M1b (sealed).
- `pos-amend` CLI rename → `loam amend` — M1e per dispatch §Scope.
- Code imports `from pos_<comp>` → `from loam.<comp>` and package directory restructure — M1e/M1f per dispatch §Scope.
- `graceful-degradation` → `dormancy` — M1f per dispatch §Scope (pulls the second-segment rename `loam.degradation` → `loam.dormancy` into scope).
- `pos.bootstrap.contributions` Python entry-point group name in `framework/workspace-bootstrap/` — Python packaging identifier, NOT an OTel root. Per dispatch §Scope out-of-scope ("Any non-OTel `pos.*` reference"). Renames at M1e (the namespace pivot subsumes the entry-point group rename).
- `pos_v2.primary_persona` legacy entry in `framework/observability-aggregator/src/schema.py::TRACER_TO_COMPONENT` — pre-existing tech-debt entry (matches `pos_v2.*` not `pos.*`); preserved per M1d's "first-segment-`pos`-only" scope. **Halt-and-surface (non-blocking) §11 finding #2.** A future cleanup amendment removes the dead lookup key.
- Path strings of form `/Users/lukeivers/ivers-corp-pos-v2/...` — M9-deferred per `oss-v0-1-0-publish.md` §6.
- `pos.*` references inside historical seal narratives (`framework/<comp>/seals/SEAL_COMMIT.*`) — preserved per `loam-rename-decisions.md` Q2 (history keeps contemporary terminology).
- `pos.*` references inside historical plan-docs at `docs/rebuild/plans/*.md` — historical method-record; preserved (consistent with M1a + M1b + M1c).
- `pos.*` references inside frozen-record component docs (`docs/rebuild/components/<comp>/research.md`, `research-plan.md`, `brief.md`, `component.md`) — historical-record; preserved per M1a/b/c convention. Only the LIVE design contract (`proposal.md` files that name OTel roots) is in scope.
- STATE.md, BACKLOG.md, FUTURE_IDEAS.md, FUTURE_IDEAS_DRAFT.md — historical-narrative-heavy live docs; M1a + M1b + M1c deferred; M1d continues to defer.
- Spec docs at `docs/rebuild/spec/pos-v2-*.md` — M1e (filename + content).
- The `tracer_to_component`'s pre-existing `"pos_v2.primary_persona"` legacy entry — see above; M1d preserves verbatim.
- `pos.bootstrap.contributions` references in `framework/workspace-bootstrap/{src,docs,README}.md` — see above; M1e.

**Sealed-component fence (post-build):** **thirteen sealed components** carry OTel `pos.*` callsites in src / tests / docs:
- `cost-governance` — observability.py + tests/test_observability_routing.py + cost-budget breach attrs.
- `graceful-degradation` — detection.py + observability.py + 3 tests (D9, amendment-20, D10) (rebases to `loam.degradation` only; the `degradation` second-segment stays — M1f cascades to `loam.dormancy`).
- `objective-tracker` — observability.py + runtime.py + tests/test_d7_otel_emission.py + others.
- `observability-aggregator` — config.py (default), ingest.py (4 callsites + service.name), nl_path.py (tracer + 2 spans + 2 attrs), replay.py (5 attr lookups), api.py (1 attr lookup), schema.py (TRACER_TO_COMPONENT keys + 2 attr literals), store.py (logger name) + 9 test files.
- `orchestrator` — supervisor.py (tracer name), observability.py (tracer name) + tests.
- `primary-persona` — 7 files (observability.py, persona events + onboarding, tests).
- `reversibility-primitive` — observability.py (tracer name).
- `self-correction` — observability.py + triggers.py + tests/test_observability_routing.py + tests/test_amendment_20_silent_excepts.py + tests/test_detection_otel_anomaly.py.
- `self-upgrade` — observability.py + rollback.py + clause_checks.py + upgrade.py.
- `telegram-interface` — observability.py + 2 tests.
- `workspace-bootstrap` — host.py (tracer name `pos.bootstrap`), discovery.py (entry-point group OUT OF SCOPE — see above), main.py (any tracer/emit) + tests/test_observability_routing.py + docs/extension_protocol.md.
- `workspace-sync` — observability.py + cli.py + tests.
- `hands-off-lifecycle` — narrative anchor + H19 owner. **No source/test edits expected** (HOL emits via orchestrator's tracer; HOL-internal source contains zero `pos.*` literals at plan-authoring time per surface inventory). HOL is in the fence as the conventional narrative anchor and so its H19 byte-content invariant covers the in-band rebaseline (see §5 + §11 finding #3).

Plus **scope-of-work + safety-layer (no SEAL_COMMIT sidecar)** — touched in src/tests but not entered as fence components per the M1a-locked precedent (`scope-of-work + safety-layer (no SEAL_COMMIT sidecar pre-D.1) are moved by git mv but not entered here — their seal-discipline is handled by hands-off-lifecycle's H19 cross-cutting test`). H19's allowed-set covers their admission.

Plus `docs/odd-in-pos.md` (universal admission), the `docs/rebuild/components/<comp>/proposal.md` files (universal `docs/rebuild/` prefix), and the M1d plan-doc + manifest YAML (`docs/rebuild/plans/`).

**Estimate:** 180–300 min AI-time per the duration rubric (multi-component mechanical-substitution category; thirteen-component fence — widest of the M1 series so far; ~681 `pos.*` literal occurrences across ~70 files; medium-volume mechanical surface; **HC#4 retire-and-rebaseline EXPECTED at M1d** for `framework/workspace-bootstrap/src/workspace_bootstrap/host.py` (line 82 carries `trace.get_tracer("pos.bootstrap")`; rebrand changes the file's SHA — pre-build verification per dispatch §Constraints HOL byte-content-match enumeration confirmed). The other 14 sample files contain no M1d-touched OTel callsites. M1c calibration was 75 min for a five-component fence with ~50 callsites; M1d's surface is roughly 3× that — so 225 min midpoint with 2× variance bound is a reasonable rubric prediction.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Named spec objectives this sub-amendment satisfies:**

- **AC.OSS.5** (`oss-v0-1-0-publish.md` §3) — *"Documentary rebrand complete in public artefacts"* — partial; M1d closes the OTel-root slice. M1e/M1f/M1g close namespace + dormancy + CLI portions.
- **AC.OSS.3** — *"No dev-discipline machinery visible in public synthesis output"* — M1d stabilises the `loam.*` OTel root that any downstream observability consumer (the aggregator itself, future tooling) reads. Future plugin-emitted spans claim `loam.<plugin>.*` sub-namespaces.
- **AC.PO.1** (VALUE_PROPOSITION primary-persona test) — single-syllable identity (`loam`) reduces the user's translation-burden vocabulary in span-name reading (when debugging via `loam obs query` or aggregator NL path).
- **AC.PO.2** (VALUE_PROPOSITION harness test) — the `loam.*` OTel root becomes the harness's namespaced ID-root that future plugin services / extensions claim sub-namespaces under (e.g. `loam.<plugin>.<event>`).

**Sealed-component fence (preliminary — see §4 ACs + §11 surface inventory):** thirteen sealed components touched in src/tests/docs, plus scope-of-work + safety-layer admitted via H19 cross-cutting, plus `docs/odd-in-pos.md` + `docs/rebuild/components/<comp>/proposal.md` files via universal admissions. The amendment manifest YAML lists the thirteen sealed components.

**ODD §2.5 reverse-direction commitment.** Every line of code/test/doc-prose changed in M1d's diff traces back to AC.RNM-1d.1 .. AC.RNM-1d.S below. Mechanical first-segment substitution (`pos.` → `loam.`); no behaviour changes; no defensive-`if` admissions; no cross-mode-debt cascade beyond the named surface.

---

## 3. Three-lens analysis (abbreviated; series-master §4 covers cross-cutting)

- **Lens 1.** Pass. Preserves every existing Claude-native composition. The Claude Code session emits no OTel spans into the framework's tracer providers; Claude-Code-shape unaffected. Future Claude-shape extensions (M6's Dev/SDLC plugin) read uniform `loam.*` paths post-M1d.
- **Lens 2.** Primary-persona pass. The user reading `loam obs query session=...` sees `loam.<comp>.<event>` span names — single brand-vocabulary surface in the user's debug surface. Harness pass — `loam.*` becomes the canonical OTel root that plugins claim sub-namespaces under.
- **Lens 3.** Pure mechanical first-segment substitution work. Outcome-shaped ACs (post-rename grep counts — exactly zero `pos.*` first-segment OTel callsites in non-historical surfaces; specific 25-root inventory verifying every documented root rebases). Method-shape (sed, Edit, surgical edits where archaeology overlaps live code) is the builder's call inside the AC outcome bound.

---

## 4. Acceptance criteria — AC.RNM-1d.*

Outcome-shaped. Behaviour-count check at end of section.

### AC.RNM-1d.1 — All `pos.X.Y...` first-segment OTel callsites rebase to `loam.X.Y...`

Every framework callsite (src + tests + live docs + component-proposal docs) where a `pos.<root>.<rest>` literal appears as ANY of:
- A span name (`start_as_current_span("pos.X")`, `name="pos.X"`, etc.).
- An event name (similar invocations on `add_event`).
- A tracer / logger / meter name (`trace.get_tracer("pos.X")`, `logging.getLogger("pos.X")`).
- An attribute key (`set_attribute("pos.X.Y", ...)`, `attrs.get("pos.X.Y")`).
- A `service.name` Resource attribute (`Resource.create({"service.name": "pos.aggregator"})`).
- A namespace prefix configuration default (`self_namespace_prefix: str = "pos.aggregator"`).
- A `TRACER_TO_COMPONENT` lookup-map key (in `observability-aggregator/src/schema.py`).
- A test assertion / fixture / parametrize value referencing any of the above.
- A worked-example or architecture-diagram citation in a live component doc or `docs/odd-in-pos.md` or component `proposal.md`.

post-amendment carries `loam.X.Y...` (first segment substituted; second-and-below segments unchanged).

**Outcome (positive):** `grep -rE 'loam\.(aggregator|bootstrap|call|correction|cost|degradation|hands_off_lifecycle|http|notification|objective|orchestrator|other|persona|prompt|retention|reversibility|safety|scope|scope_of_work|session|sync|telegram|test|upgrade|memory|cost_governance|safety_layer|self_correction|telegram_interface|reversibility_primitive|primary_persona|objective_tracker)\b' framework/ docs/odd-in-pos.md docs/rebuild/components/*/proposal.md --include="*.py" --include="*.md" --include="*.yaml" --include="*.json" --include="*.fragment"` returns **at least 681 matches** (the pre-rename total `pos.*` count in the in-scope surface). The 25-root catalogue in §1 plus the tracer-component variants (`cost_governance`, `safety_layer`, `self_correction`, `telegram_interface`, `reversibility_primitive`, `primary_persona`, `objective_tracker`) all appear with `loam.` prefix in the post-rename surface.

**Outcome (negative):** `grep -rE '"pos\.[a-z_]+' framework/ docs/odd-in-pos.md docs/rebuild/components/*/proposal.md --include="*.py" --include="*.md" --include="*.yaml" --include="*.json" --include="*.fragment"` returns **0 matches** in the live (non-historical) surface. Permitted residuals (NOT counted as breaches):
- `framework/<comp>/seals/SEAL_COMMIT.*` historical seal narratives.
- `docs/rebuild/plans/*.md` historical method-record (preserved consistent with M1a + M1b + M1c).
- `docs/rebuild/components/<comp>/research.md`, `research-plan.md`, `brief.md`, `component.md` (historical records preserved per M1a/b/c convention).
- `pos.bootstrap.contributions` entry-point-group references in `framework/workspace-bootstrap/{pyproject.toml, src/, docs/extension_protocol.md, README.md}` (Python packaging identifier; not OTel; out of scope per §1; M1e closes this surface).
- `pos_v2.primary_persona` legacy entry in `framework/observability-aggregator/src/schema.py::TRACER_TO_COMPONENT` (pre-existing tech-debt entry; preserved per scope §1).
- `tmp_path / ".pos"`, `_POS_SUBDIR = ".pos"`, `<workspace>/.pos/` workspace-sentinel-dir references (not OTel).
- Workspace `pos.*` references in `STATE.md`, `BACKLOG.md`, `FUTURE_IDEAS.md`, `FUTURE_IDEAS_DRAFT.md` (historical-narrative-heavy live docs; deferred).

### AC.RNM-1d.2 — All 25 documented OTel root namespaces appear in the post-rename surface as `loam.*`

The post-amendment in-scope surface contains the following 25 first-segment-`loam.` roots (matching the pre-amendment first-segment-`pos.` roots verbatim except for the first-segment substitution):

```
loam.aggregator     loam.bootstrap      loam.call          loam.correction
loam.cost           loam.degradation    loam.hands_off_lifecycle  loam.http
loam.memory         loam.notification   loam.objective     loam.orchestrator
loam.other          loam.persona        loam.prompt        loam.retention
loam.reversibility  loam.safety         loam.scope         loam.scope_of_work
loam.session        loam.sync           loam.telegram      loam.test
loam.upgrade
```

Plus the tracer-component variants (these are package-name-mirroring tracer names emitted via `trace.get_tracer(...)`, distinct from the span-name roots above):

```
loam.cost_governance        loam.safety_layer
loam.self_correction        loam.telegram_interface
loam.reversibility_primitive   loam.primary_persona
loam.objective_tracker
```

**Outcome:** `grep -rEho '"loam\.[a-z_]+' framework/ --include="*.py" 2>/dev/null | sort -u` enumerates ALL of the 25 first-segment-`loam.` roots above plus the seven tracer-component variants. The pre-rename inventory recorded in §1 of this plan-doc (and re-confirmed at build time as the BASELINE..feature-commit transition) maps exactly into this post-rename inventory, modulo the first-segment substitution.

### AC.RNM-1d.3 — Aggregator namespace defaults rebase

The observability-aggregator's namespace-related defaults rebase:

- `framework/observability-aggregator/src/config.py`: `self_namespace_prefix: str = "pos.aggregator"` → `"loam.aggregator"`.
- `framework/observability-aggregator/src/ingest.py`: three `self_namespace_prefix: str = "pos.aggregator"` function-default mirrors → `"loam.aggregator"`.
- `framework/observability-aggregator/src/ingest.py:191`: `Resource.create(resource_attrs or {"service.name": "pos.aggregator"})` → `{"service.name": "loam.aggregator"}`.
- `framework/observability-aggregator/src/schema.py::TRACER_TO_COMPONENT`: every `"pos.<X>"` key rebases to `"loam.<X>"`. The pre-existing `"pos_v2.primary_persona"` legacy entry is PRESERVED (out-of-scope per §1; halt-and-surface §11 finding #2 records it for future cleanup amendment).

**Outcome:** `pytest framework/observability-aggregator/tests/test_d1_otel_ingestion.py framework/observability-aggregator/tests/test_d3_storage.py framework/observability-aggregator/tests/test_d4_query_api.py framework/observability-aggregator/tests/test_d5_nl_path.py framework/observability-aggregator/tests/test_d6_replay.py framework/observability-aggregator/tests/test_d7_retention.py framework/observability-aggregator/tests/test_d9_self_obs_and_privacy.py framework/observability-aggregator/tests/test_s4_teardown_observability.py framework/observability-aggregator/tests/test_amendment_20_silent_excepts.py framework/observability-aggregator/tests/test_d2_memory_jsonl_tailer.py` PASSES.

### AC.RNM-1d.4 — Aggregator's namespace validation accepts `loam.*` (tautology under config-default rebrand)

The aggregator's two `tracer_name.startswith(self._self_prefix)` callsites in `framework/observability-aggregator/src/ingest.py` (lines 155 + 477) validate against the configurable `self_namespace_prefix` field. Post-AC.RNM-1d.3 the default is `"loam.aggregator"`. There is no hardcoded `pos.` prefix check in the production code — the production code reads the configurable field, so the default-update IS the contract update. **Halt-trigger #7 of the dispatch is structurally moot** (no hardcoded `pos.` validator existed; the configurable field IS the contract).

**Outcome:** the aggregator's existing self-obs filter (which prevents the aggregator's own NL spans from being re-ingested) continues to work post-rename — the filter matches `loam.aggregator.*` against the now-`loam.aggregator` configured prefix. `pytest framework/observability-aggregator/tests/test_d9_self_obs_and_privacy.py` PASSES.

### AC.RNM-1d.5 — Live component docs + component proposals + odd-in-pos rebrand

Every `framework/<comp>/docs/*.md` file plus `docs/rebuild/components/<comp>/proposal.md` files plus `docs/odd-in-pos.md` lines that cite OTel `pos.*` root literals in worked-examples / architecture diagrams / contract descriptions rebrand to `loam.*`.

**Outcome:** `grep -rE '"?pos\.(aggregator|bootstrap|call|correction|cost|degradation|hands_off_lifecycle|http|memory|notification|objective|orchestrator|persona|prompt|retention|reversibility|safety|scope|scope_of_work|session|sync|telegram|test|upgrade|cost_governance|safety_layer|self_correction|telegram_interface|reversibility_primitive|primary_persona|objective_tracker)\b' framework/*/docs/ docs/odd-in-pos.md docs/rebuild/components/*/proposal.md` returns 0 matches.

### AC.RNM-1d.S — Sealed-component fence narrows to OTel-emit-and-assert-and-doc surface only

Thirteen-component sealed amendment commit lands per `pos-amend apply` + `pos-amend seal` convention (using the still-`pos-amend` CLI; M1d is one sub-amendment before M1e's CLI rename). The amendment manifest YAML lists thirteen sealed components. The `seal_diff` `allowed_prefixes` admit `framework/<comp>/` for each touched component plus the universal paths.

**Per-component touched-test scope:** narrow to touched files. Per `feedback_amendment_dispatch_speedups`, M1d skips pre-seal full-suite rerun. Each sealed component's `tests/test_no_sealed_amendments.py` runs as part of `pos-amend apply` verification. The seal-diff fence test for AC.RNM-1d.S is the primary check (verifies the fence isn't reaching beyond OTel surfaces).

**Outcome:** `git log --oneline | head -3` shows feature-commit + apply-commit + seal-commit triple per repo convention; thirteen per-component sidecars all advance; `pytest framework/<comp>/tests/test_no_sealed_amendments.py` per touched component PASSES.

### AC.RNM-1d.6 — No work outside the named surfaces (negative AC)

Negative AC. The amendment's git-diff includes ZERO touches outside:

- The thirteen named sealed components' src/tests/docs paths.
- `framework/scope-of-work/`, `framework/safety-layer/` (admitted via H19 cross-cutting allowed-set per the M1a-locked precedent).
- `docs/odd-in-pos.md` (universal admission).
- `docs/rebuild/components/<comp>/proposal.md` (universal `docs/rebuild/` prefix).
- The plan-doc + manifest YAML under `docs/rebuild/plans/`.
- Any necessary admission-extension to `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py` (HC#4 retire-and-rebaseline for `framework/workspace-bootstrap/src/workspace_bootstrap/host.py` per dispatch §Constraints + §11 finding #3 — this IS in-band methodology-aligned ODD §4 work).

**Permitted ZERO surfaces (no edits expected):**

- No env-var or per-host-config-dir changes — M1b closed those.
- No launchd-label changes — M1c closed those.
- No internal Python identifiers carrying `POS_V2_` / `pos_v2` decoration — M1e.
- No `--pos-v2-root` CLI flag rename — M1e.
- No `from pos_<comp>` imports — M1f.
- No `pos-amend` CLI references in code — M1e.
- No path-string `/Users/lukeivers/ivers-corp-pos-v2/...` rewrites — M9.
- No `framework/<comp>/seals/SEAL_COMMIT.*` historical-narrative edits.
- No `docs/rebuild/plans/*.md` historical method-record edits beyond this plan-doc + this manifest YAML.
- No `docs/rebuild/components/<comp>/research.md`, `research-plan.md`, `brief.md`, `component.md` edits (historical records preserved).
- No `pos.bootstrap.contributions` entry-point-group changes — M1e.
- No `pos_v2.primary_persona` legacy entry change in `TRACER_TO_COMPONENT` — out of scope (§1 finding #2).
- No `graceful-degradation` → `dormancy` rename (only the first-segment of `pos.degradation` changes; `degradation` second-segment stays).

**Outcome:** `git diff <baseline>..<feature-commit-tip> --stat` shows changes only in the named surfaces above.

### Behaviour-count check (ODD §3.3 forward)

Six outcome-named behaviours (first-segment OTel rebrand, 25-root post-rename inventory, aggregator namespace defaults, aggregator validation tautology, live docs + proposals + odd-in-pos rebrand, fence-narrowing seal) → six ACs (AC.RNM-1d.1 .. AC.RNM-1d.5 + AC.RNM-1d.S). Plus one negative AC (AC.RNM-1d.6) enforcing the OTel-surface-only fence. Match.

ODD §2.5 reverse direction (every diff line traces to a named AC) is the builder's pre-seal audit; surfaced explicitly as halt trigger §8.5 below.

---

## 5. Hard constraints (M1d-specific; series-wide constraints from master §5 inherit)

- **OTel-only diff with hard cutover.** AC.RNM-1d.6 is the structural fence — span/event/tracer/logger/attr/Resource literals + aggregator namespace defaults + live component docs + component proposals + `docs/odd-in-pos.md` worked examples + plan-doc only. No other surfaces.
- **Hard cutover.** Per series-master §1 D-RNM.3: no dual-emit shim publishing under both `pos.*` and `loam.*`; no aggregator query-time fallback that reads either prefix; no compat module that registers both tracers. The retention-DB rows are not modified — only emit-side and query-time-filter literals change.
- **First-segment-only substitution.** Only the `pos.` prefix becomes `loam.`. Second-and-below segments stay verbatim. `pos.cost.budget_breach.amount` → `loam.cost.budget_breach.amount`; the `.cost.budget_breach.amount` tail is unchanged.
- **Attribute keys + tracer/logger names + span names + event names ALL in scope.** All four convey the OTel namespace identity; all four rebase.
- **Memory-system records' `retention_class` field stays.** Memory's hand-rolled records carry a bare `retention_class` field (no namespace prefix) — that's NOT OTel and stays.
- **`pos.degradation` rebases to `loam.degradation`.** The Tier-2 dormancy rename at M1f cascades to `loam.dormancy`; M1d's contract is first-segment-only.
- **`pos.bootstrap.contributions` entry-point-group is OUT OF SCOPE.** It is a Python packaging identifier, not an OTel root. M1e closes it concurrently with the namespace pivot.
- **`pos_v2.primary_persona` legacy `TRACER_TO_COMPONENT` entry is PRESERVED.** Pre-existing tech-debt entry; not in M1d's first-segment-`pos`-only scope. §11 finding #2 records the recommendation to remove it in a future cleanup amendment.
- **`pos-amend apply` runs BEFORE the seal commit** (`feedback_dispatch_explicit_pos_amend_apply`).
- **No `git commit --amend`** (`feedback_no_amend_in_agent_dispatches`). Corrective commits are NEW commits.
- **HC#4 byte-content sample retire-and-rebaseline EXPECTED at M1d.** Per dispatch §Constraints HOL byte-content-match check: the fifteen sample files in `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py` were enumerated for ANY OTel `pos.*` callsite at plan-authoring time. Result: `framework/workspace-bootstrap/src/workspace_bootstrap/host.py` (line 82) carries `self.tracer = trace.get_tracer("pos.bootstrap")` — an OTel-tracer-name callsite that M1d rebrands to `"loam.bootstrap"`. This SHA-changes the file. ODD §4 in-band retire-and-rebaseline is named in M1d's scope per the lesson-#9 convention from M1c: the HC#4 SHA pin for `host.py` updates to the post-M1d hash with a comment naming M1d amendment + the cause; the docstring/tracer-name rebrand IS the AC-named work (AC.RNM-1d.1). The other 14 sample files contain ZERO M1d-touched OTel callsites (verified at plan-authoring time per §11 finding #3). HC#4 stays GREEN with the single SHA bump.
  - One additional sample file does carry a `pos.*` literal (`workspace_bootstrap/discovery.py:30: _ENTRYPOINT_GROUP = "pos.bootstrap.contributions"`) but that callsite is a Python packaging identifier (entry-point-group name), NOT an OTel root — M1e (the namespace pivot) handles it. M1d does NOT touch `discovery.py`; HC#4's pin for `discovery.py` is unaffected.
- **Test scope is narrow.** Per `feedback_amendment_dispatch_speedups`, M1d skips pre-seal full-suite rerun. Touched-test rerun + per-component `test_no_sealed_amendments.py` is the methodology-aligned narrow verification.
- **Historical preservations.** `docs/rebuild/plans/*.md`, `framework/<comp>/seals/SEAL_COMMIT.*`, and `docs/rebuild/components/<comp>/{research.md,research-plan.md,brief.md,component.md}` files preserved verbatim (per M1a/b/c convention; they are method/design records moments-in-time).
- **Historical retention-DB data.** Existing rows in the aggregator's retention DB stored under `pos.*` span names stay verbatim. Post-M1d, queries that wish to retrieve historical rows can query the row's `name` field for the literal `pos.*` value; the aggregator's query layer doesn't introduce a `pos.*`/`loam.*` translation. Pre-public release; zero historical-data-consumers; the data-as-archaeology lifetime is unbounded but pure read-only.

---

## 6. Out of scope (named explicitly per ODD §2.5)

(See §1 for the full list. Re-named here for ODD §2.5 compliance.)

- All work deferred to M1e..M1g + M9 (CLI, namespace pivot, dormancy rename, dir rename, spec-file renames).
- **Workspace-side `<workspace>/.pos/` sentinel directory** — distinct surface; M1b discipline carried forward.
- **Internal Python identifiers** carrying `POS_V2_` / `pos_v2` / `pos-v2` decoration — namespace work; M1e.
- **`--pos-v2-root` CLI flag** — namespace shape; M1e.
- **Historical seal narratives** at `framework/<comp>/seals/SEAL_COMMIT.*` — preserved.
- **Historical plan-docs** at `docs/rebuild/plans/*.md` (other than this plan-doc + this manifest YAML) — preserved.
- **Historical component-record docs** at `docs/rebuild/components/<comp>/{research.md,research-plan.md,brief.md,component.md}` — preserved.
- **STATE.md, BACKLOG.md, FUTURE_IDEAS.md, FUTURE_IDEAS_DRAFT.md** — historical-narrative-heavy live docs; M1a + M1b + M1c deferred; M1d continues to defer.
- **Spec docs** at `docs/rebuild/spec/pos-v2-*.md` — M1e (filename + content).
- **`pos.bootstrap.contributions`** Python entry-point group identifier — Python packaging, not OTel; M1e.
- **`pos_v2.primary_persona`** legacy entry in `framework/observability-aggregator/src/schema.py::TRACER_TO_COMPONENT` — pre-existing tech-debt entry; preserved per M1d's first-segment-`pos`-only scope. **Halt-and-surface (non-blocking) §11 finding #2.**
- **graceful-degradation → dormancy directory + package + config-files** rename — M1f. M1d only rebrands the OTel first segment; `loam.degradation` second-segment stays until M1f cascades.
- **Memory-system records' `retention_class` bare field** — not OTel-namespaced; stays.
- **Aggregator's retention-DB rows already stored under `pos.*` names** — pre-public release; zero data-consumers; rows are not modified — only emit-side and query-time-filter literals change.

---

## 7. Implementation order (suggested — builder's call to refine)

1. **Pre-flight verification.** `pwd` returns `/Users/lukeivers/ivers-corp-pos-v2`; `git rev-parse --abbrev-ref HEAD` returns `pos-v2`; `git status --short` shows working tree clean (only the pre-existing `personas/` untracked item remains). Halt-and-surface if any check fires.
2. **BASELINE pin.** Pin to M1c's seal commit `1e99d0b`.
3. **M1d sub-plan + manifest commit.** This plan-doc + a manifest YAML at `docs/rebuild/plans/oss-v0-1-0-publish-rename-1d.manifest.yaml` per the established M1a/M1b/M1c precedent shape.
4. **Phase A — first-segment substitution across framework src.** Mechanical rename across the thirteen sealed components plus scope-of-work + safety-layer. Per-file Edit / sed for the simple cases; surgical Edit per callsite where archaeology overlaps live code (the aggregator's `TRACER_TO_COMPONENT` map preserves `pos_v2.primary_persona`; the workspace-bootstrap entry-point-group `pos.bootstrap.contributions` is preserved). Touched files include (non-exhaustive — builder enumerates from grep at build time):
   - `framework/cost-governance/src/observability.py` (tracer name + spans + attrs).
   - `framework/graceful-degradation/src/observability.py` (tracer + spans + attrs); `framework/graceful-degradation/src/detection.py`.
   - `framework/objective-tracker/src/observability.py`; `framework/objective-tracker/src/runtime.py`.
   - `framework/observability-aggregator/src/{config.py, ingest.py, nl_path.py, replay.py, api.py, schema.py, store.py}` (config default + 4 ingest defaults + Resource service.name + nl_path tracer + 2 spans + 2 attrs + replay's 5 attr lookups + api's 1 attr lookup + schema's TRACER_TO_COMPONENT keys + 2 attr literals + store's logger name).
   - `framework/orchestrator/src/{supervisor.py, observability.py}`.
   - `framework/primary-persona/src/{observability.py, persona events, onboarding}` (callsite enumeration at build time).
   - `framework/reversibility-primitive/src/observability.py`.
   - `framework/self-correction/src/{observability.py, triggers.py}`.
   - `framework/self-upgrade/src/self_upgrade/{observability.py, rollback.py, clause_checks.py, upgrade.py}`.
   - `framework/telegram-interface/src/observability.py`.
   - `framework/workspace-bootstrap/src/workspace_bootstrap/{host.py (line 82 tracer name), main.py}`. **NOT** `discovery.py` (entry-point group out of scope).
   - `framework/workspace-sync/src/workspace_sync/{observability.py, cli.py}`.
   - `framework/scope-of-work/src/{runtime.py, observability.py}` (admitted via H19, not a fence-component).
   - `framework/safety-layer/src/observability.py` and similar (admitted via H19, not a fence-component).

   Builder runs grep at start of Phase A for the authoritative file list; the names above are inventory at plan time and may shift slightly as builder enumerates.

   Post-edit grep verifies AC.RNM-1d.1 outcome (0 framework `"pos\.<root>"` matches in the live src surface; only the documented permitted residuals remain).

5. **Phase B — first-segment substitution across framework tests.** Mechanical rename across every test file that asserts a literal `pos.X` span/event/attribute/tracer name. Touched files include (non-exhaustive — builder enumerates from grep):
   - `framework/cost-governance/tests/test_observability_routing.py`.
   - `framework/graceful-degradation/tests/{test_d9_observability.py, test_amendment_20_silent_excepts.py, test_d10_one_hour_outage.py}`.
   - `framework/objective-tracker/tests/test_d7_otel_emission.py`.
   - `framework/observability-aggregator/tests/{test_d1_otel_ingestion.py, test_d2_memory_jsonl_tailer.py, test_d3_storage.py, test_d4_query_api.py, test_d5_nl_path.py, test_d6_replay.py, test_d7_retention.py, test_d9_self_obs_and_privacy.py, test_amendment_20_silent_excepts.py, test_s4_teardown_observability.py}`.
   - `framework/orchestrator/tests/...` (callsite enumeration at build time).
   - `framework/primary-persona/tests/test_AC35_7_observability.py` and others.
   - `framework/safety-layer/tests/test_observability_routing.py`.
   - `framework/scope-of-work/tests/{test_d5_otel_emission.py, test_s3_silent_excepts.py}`.
   - `framework/self-correction/tests/{test_observability_routing.py, test_amendment_20_silent_excepts.py, test_detection_otel_anomaly.py}`.
   - `framework/telegram-interface/tests/test_structural.py` and others.
   - `framework/workspace-bootstrap/tests/test_observability_routing.py`.
   - `framework/workspace-sync/tests/...`.

   Post-edit grep verifies tests pass under the new prefix.

6. **Phase C — live component docs + component proposals + `docs/odd-in-pos.md`.** Mechanical rename across:
   - `framework/<comp>/docs/*.md` files that reference OTel roots (architecture diagrams, relationship maps, api-references, prose-explanations, nl-references).
   - `docs/rebuild/components/<comp>/proposal.md` files that reference OTel roots in design contracts.
   - `docs/odd-in-pos.md` lines ~100 + ~255 (worked examples).

   Post-edit grep verifies AC.RNM-1d.5 outcome.

7. **Phase D — HC#4 retire-and-rebaseline for `host.py`.** Update the SHA pin in `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py` for `framework/workspace-bootstrap/src/workspace_bootstrap/host.py` to the post-M1d hash. Add a comment naming M1d amendment + the cause (matching M1c's lesson-#9 convention).

8. **Phase E — feature commit.** Single feature commit carrying the OTel rebrand diff + the HC#4 SHA bump + the live-docs / proposals / odd-in-pos rebrand. Commit message names the M1d slug, the AC family (AC.RNM-1d.1–AC.RNM-1d.S), and the series-master pointer.

9. **Phase F — pos-amend apply.** Run `pos-amend apply` against the manifest. Verify clean apply. **`pos-amend apply` BEFORE the seal commit per FIDRAFT note from amendment #41.**

10. **Phase G — apply commit.** The apply commit (sidecars + seal-narrative scaffold) per `pos-amend apply` convention.

11. **Phase H — seal-diff fence verification.** AC.RNM-1d.S + AC.RNM-1d.6 — verify `git diff <baseline>..HEAD --stat` shows ONLY the named surfaces. Verify each component's `pytest framework/<comp>/tests/test_no_sealed_amendments.py` passes.

12. **Phase I — touched-test rerun.** Run the explicit test scope: every test file in the OTel-callsite list (Phase B), the aggregator's tests (heaviest-touched), HC#4 cross-cutting (post-rebaseline), each touched sealed component's `test_no_sealed_amendments.py`. Per `feedback_amendment_dispatch_speedups`, the full-suite rerun is skipped pre-seal — the touched-test-only sweep is the methodology-aligned narrow verification.

13. **Phase J — `pos-amend seal --plan-doc <abs-path>`.** Backfills §14 SHA register (this plan's §14 below). The seal commit narrative cites the AC family, the 25-root catalogue, the HC#4 retire-and-rebaseline, the preserved-archaeology pre-existing entries (`pos.bootstrap.contributions` + `pos_v2.primary_persona`), and the live-docs/proposals scope.

Phases A–C are mechanical-substitution. Phase D is one Edit + one comment-line. Phases 8–13 are commit + seal mechanics.

---

## 8. Halt triggers (M1d-specific; series-wide triggers from master §7 inherit)

The build agent MUST halt and surface when:

1. **An OTel emit site outside the framework surfaces.** Inventory pre-build expects callsites in framework/<13 sealed components> + scope-of-work + safety-layer + the live docs + odd-in-pos + component proposals. Any callsite in `tools/` (other than `pos-amend` which is M1g surface; no OTel callsite expected there), `scripts/`, root-level files, plugins/, etc. surfaces as a fence-creep signal. Halt; surface for re-scope.
2. **An attribute-level name is malformed.** Per dispatch halt-trigger #2: an attribute key whose name structurally has the `pos.` prefix in a different way than the documented `pos.<root>.<key>` pattern (e.g. `.pos.X` with a leading dot, or `pos..X` with a doubled dot, or `pos.X..Y` with embedded double-dot, or any shape that isn't first-segment-`pos`) is malformed and surfaces. Halt; flag for owner ruling on whether to repair in-band or surface as a separate cleanup.
3. **HC#4 byte-content-match invariant breach BEYOND `host.py`.** Per dispatch §Constraints + §11 finding #3, ONE sample file (`host.py`) is expected to need ODD §4 retire-and-rebaseline; the in-band SHA bump IS in M1d's scope. ANY OTHER sample file's SHA changing (i.e. M1d's diff touches a sample file beyond `host.py`) is a frozen-baseline breach beyond the planned single bump. Halt; surface for owner ruling on whether to expand the in-band rebaseline or split scope.
4. **`pos-amend` automation hits a gap on the OTel surface.** Regex narrowness (e.g. fails on attribute-key regex with embedded special chars), abs-path requirement, manifest-validation false-positive on the thirteen-component fence, manifest-validation false-positive on the universal `docs/rebuild/components/` admission. Record in `FUTURE_IDEAS_DRAFT.md` and surface; do not push through.
5. **ODD §2.5 violations encountered in surrounding code.** Halt; do NOT silently extend. Surface for owner ruling on whether to fix in-band, defer, or reshape M1d's scope.
6. **Cross-mode debt** (loam-mode F-register, hands-off-lifecycle allowed_prefixes, dispatch-template path refs) that prevents OTel rebrand from landing cleanly. Record + address in scope or surface for follow-on.
7. **Aggregator namespace validation refuses `loam.*` because it had hardcoded `pos.`.** Per dispatch halt-trigger #7: this would be an in-band fix in M1d's scope (the validation IS the contract for the rename). **Pre-build verification at plan-authoring time confirms NO hardcoded `pos.` validator exists** — the production code reads `self_namespace_prefix` (configurable; default rebrands to `"loam.aggregator"` in AC.RNM-1d.3). The halt-trigger is structurally moot per AC.RNM-1d.4. If build-time discovery contradicts this (a hardcoded `startswith("pos.")` in some path not yet read), halt and surface.
8. **AC.RNM-1d.6 fence is breached.** The diff reaches outside OTel-surface + live-docs + proposals + odd-in-pos + plan-doc. Halt; do not "fix" by widening the AC; the over-reach IS the failure signal.
9. **A `loam` identifier already in use** in any of the named surfaces (e.g. an existing `loam.X` literal in some pre-rename fixture). Halt; surface for rename-the-conflicting-use first.
10. **Wall-clock exceeds 6 h** (M1d is rubric-priced 180–300 min midpoint 225 min; 6 h is roughly 1.6× upper-bound). Halt with current-state report; dispatcher triages continue / split-further / pause.
11. **Pre-existing test fails post-rename.** Halt; the rename has hit a non-mechanical change. Surface failing test + diagnosis.
12. **A `pos.*` reference is found in `framework/<comp>/seals/SEAL_COMMIT.*`** during touched-test verification — historical narratives are preserved per `loam-rename-decisions.md` Q2; if a sealed-narrative cross-reference assertion ties a marker phrase to a `pos.*` literal AND the marker is brand-keyed (vs intent-keyed), apply `feedback_loose_AC_text_fix_AC_not_implementation` per M1a's #9 precedent.
13. **A literal `pos.<root>` callsite resists rebrand because of test-fixture / mock-data shape that asserts pre-rename literal directly.** This is the same pattern as M1c's "selective grep-rename" pattern. Builder uses surgical Edit per callsite; does NOT use global sed across the file if the file mixes archaeological + live shapes. Halt if the pattern looks unsafe; surface for ruling.

---

## 9. Risks (M1d-specific)

1. **Wide test-fixture surface in observability-aggregator and the OTel-emitting sealed components.** ~52 callsites in observability-aggregator/tests/ + ~14 in observability-aggregator/src/. A naive `s/"pos\./"loam./g` is correct for span-name / tracer-name / attr-key callsites because every callsite rebases. The failure mode is missing one or accidentally rebasing the preserved `pos_v2.primary_persona` legacy entry or the `pos.bootstrap.contributions` entry-point group. Mitigation: post-edit grep verifies AC.RNM-1d.1 outcome (0 framework `"pos\.<root>"` matches in live surface; the two named exceptions stay verbatim).
2. **The aggregator's `TRACER_TO_COMPONENT` map mixes a `pos_v2.*` legacy entry with `pos.*` live entries.** A naive global `s/"pos\.<X>"/"loam.<X>"/g` over the schema.py file would NOT touch `pos_v2.primary_persona` (different prefix), but a careless regex `s/pos\./loam./g` on a single line could miss the careful case. Mitigation: surgical Edit per line in `schema.py`.
3. **The retention-DB rows stored under `pos.*` names stay in the DB post-M1d.** Future queries that wish to retrieve historical rows can ask for the literal `pos.*` value; the aggregator's query layer doesn't introduce a translation. Pre-public release; zero historical-data-consumers; this is acceptable. Risk: a future feature wants to bridge the two (probably never — pre-public release means historical rows are diagnostic noise that washes out).
4. **HC#4 byte-content sample retire-and-rebaseline.** One file (`host.py`) requires SHA bump. Risk: build-time grep finds a SECOND sample file with an OTel callsite that wasn't flagged at plan time. Mitigation: §11 finding #3 enumerates the explicit pre-build verification; halt-trigger §3 fires on any second SHA bump.
5. **Mixed-archaeological tests.** The orphan-plist-cleanup tool's tests carry both archaeological and live literals — but those are launchd-label tests, not OTel. The OTel test surface does NOT have analogous archaeological mixing (the `pos_v2.primary_persona` entry is in src/schema.py, not tests). Risk low.
6. **The aggregator's NL path filter (`tracer_name.startswith(self._self_prefix)`) at lines 155 + 477 of ingest.py.** Reads the configurable `self_namespace_prefix` (default rebrands in AC.RNM-1d.3). Risk: a test passes a literal `"pos.aggregator"` as the prefix override and expects the filter to match the legacy emission, but the production code now emits `"loam.aggregator"`. Mitigation: `pytest framework/observability-aggregator/tests/test_d9_self_obs_and_privacy.py` PASSES post-rename; if a test passes a literal `"pos.aggregator"` it's a pre-rename test and rebases concurrently in Phase B.
7. **Component proposal docs vs research / brief / research-plan docs.** The dispatch §Scope says "component proposals" — the singular `proposal.md` per component. Builder distinguishes: `proposal.md` = live design contract (in-scope); `research.md`, `research-plan.md`, `brief.md`, `component.md` = historical record (preserved). Risk: mis-classification rebrands a frozen-record file. Mitigation: per-file allowlist ((proposal.md only); explicit AC.RNM-1d.5 grep is the post-rename outcome check.
8. **Wall-clock blow-out.** 13-component fence plus ~681 occurrences plus 14 test-files plus live docs is large mechanical work. Risk: surrounding-debt tax adds significantly. Mitigation: halt-trigger #10 fires at 6 h.

---

## 10. Decisions remaining for owner ruling

**None** at the dispatcher level. Per series master §1, all three D-RNM rulings (split, namespace shape, no compat window) closed at owner-ruling time. The dispatch's authority text + the locked rulings cover M1d's scope cleanly.

**Builder's calls within ACs (NOT requiring owner ruling):**

- D-build.M1d.1 — sed-vs-Edit per file. Builder's call within AC.RNM-1d.1: simple-mechanical files use sed-style replace_all; mixed-archaeological files (schema.py with `pos_v2.primary_persona` legacy + `pos.X` live; or any file mixing entry-point group `pos.bootstrap.contributions` + OTel `pos.bootstrap` tracer) use surgical Edit per line. Recommendation: sed-style for ~85% of files; surgical Edit for the aggregator's schema.py and the workspace-bootstrap host.py + discovery.py pair (where `host.py` has live OTel and `discovery.py` has only entry-point group, both of which mix in same component).
- D-build.M1d.2 — order of Phase A vs Phase B. Builder's call: Phase A (src) then Phase B (tests) is conventional; tests-after-src means the touched-test rerun in Phase I has the post-rename src to validate against. Alternative: per-component (src + tests in lockstep). Recommendation: Phase A then Phase B (the conventional order).
- D-build.M1d.3 — HC#4 SHA pin update timing. Builder's call within AC.RNM-1d.6's HC#4 in-band fix: update the SHA pin in Phase D (after Phase A's `host.py` edit so the post-rename hash is computable). Phase E's feature commit captures both the rebrand and the SHA pin update in a single commit, mirroring M1c lesson #9 / D-build.M1c.7's convention.

---

## 11. Halt-and-surface findings encountered during plan authoring

Per the dispatch's halt-and-surface clause: surface any audit-recommendation conflict with sealed-component invariants, methodology breaches, or surrounding-code/-doc ODD violations.

**Findings during plan authoring:**

1. **(Catalogue-vs-empirical disclosure — non-blocking.) Migration plan §3.5 documents 23 OTel root namespaces; empirical inventory at plan-authoring time enumerates 25 in the live tree.** The two delta roots: `pos.sync` (workspace-sync — added after the research; the research enumerated state at 2026-04-23 and workspace-sync's OTel surface landed during a subsequent amendment) and `pos.memory` (used by the aggregator's mapper for memory-system records — the research's "memory's hand-rolled sinks" comment implicit-named this; explicit in the live tree as `tracer_name="pos.memory"` in `framework/observability-aggregator/src/ingest.py:329`). The locked Tier-1 #5 ruling text "all 23 roots rebase" is a count-prose statement, not an enumeration ceiling — the binding ruling is "every span/event/attribute root with first-segment `pos` rebases to `loam`." All 25 roots rebase per AC.RNM-1d.1. The catalogue mismatch is a research-vs-build snapshot drift; non-blocking. The plan-doc records the explicit 25-root enumeration in AC.RNM-1d.2 so the post-build invariant matches the actual surface.

2. **(Pre-existing tech-debt observation; non-blocking; preserved per scope.) `framework/observability-aggregator/src/schema.py::TRACER_TO_COMPONENT` carries a legacy entry `"pos_v2.primary_persona": "primary_persona"` alongside the canonical `"pos.primary_persona": "primary_persona"`.** The legacy entry matches a `pos_v2.*` first-segment, NOT `pos.*`. M1d's first-segment-`pos`-only scope does not touch this entry. Origin: pre-amendment-#67 snapshot; the live emission code for primary-persona has used `pos.primary_persona` (single segment) since at least amendment #66's persona-emission scaffold landing — the `pos_v2.primary_persona` entry would only fire if some past code path emitted under that prefix, which the live `framework/primary-persona/src/` does not. **Recommendation for future cleanup amendment:** remove the dead lookup key. Recorded for FIDRAFT-or-future-cleanup. Non-blocking — preserving a dead lookup key is harmless.

3. **(Pre-build HC#4 byte-content sample re-check — finding fires; in-band ODD §4 retire-and-rebaseline declared in M1d's scope.) Per dispatch §Constraints HOL byte-content-match check + M1c lesson #9: enumerate ALL renamed surfaces and grep each HC#4 sample file.** Result of full enumeration of the fifteen sample files in `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py`:
   - `framework/primary-persona/src/cli.py` — no `pos.*` OTel callsite (M1c rebranded the single launchd-label callsite already; SHA-pinned post-M1c).
   - `framework/primary-persona/src/{__init__.py, onboarding.py, session_start_emitter.py, pyproject.toml}` — no callsites.
   - `framework/workspace-bootstrap/src/workspace_bootstrap/{__init__.py, spec.py, errors.py}` — no callsites.
   - `framework/workspace-bootstrap/src/workspace_bootstrap/host.py` (line 82) — **carries `self.tracer = trace.get_tracer("pos.bootstrap")`** — an OTel tracer-name callsite that M1d rebrands to `"loam.bootstrap"`. THIS triggers HC#4 retire-and-rebaseline (in-band per ODD §4; AC.RNM-1d.6's named carve-out).
   - `framework/workspace-bootstrap/src/workspace_bootstrap/discovery.py` (line 30) — `_ENTRYPOINT_GROUP = "pos.bootstrap.contributions"` — Python entry-point group identifier; NOT OTel; NOT touched by M1d. Discovery.py SHA stays.
   - `framework/scope-of-work/src/{spec.py, events.py, projection.py, triggers.py, pyproject.toml}` — no callsites.
   The verification confirms exactly one HC#4 sample file (`host.py`) needs SHA bump in M1d's scope; the in-band retire-and-rebaseline is methodology-aligned per the dispatch's named ODD §4 carve-out.

4. **(Live docs vs historical records distinction — non-blocking ruling.) Component proposal docs (`docs/rebuild/components/<comp>/proposal.md`) are LIVE design contracts that name OTel roots; they rebrand.** Historical records (`research.md`, `research-plan.md`, `brief.md`, `component.md`) are frozen-at-design-time artefacts and stay verbatim per the M1a/b/c convention. The dispatch §Scope's "component proposals" wording is the binding inclusion. Per-file allowlist in Phase C; AC.RNM-1d.5 grep is the post-rename outcome check.

5. **(FUTURE_IDEAS_DRAFT — pre-emptive.) Plan-time observation: the M1.rename series convention "first-segment-only substitution preserves second-and-below semantics" is now established across M1c (launchd-label first-segment-only swap) and M1d (OTel first-segment-only swap).** A reusable "loam-rename-helper" tool (M1a §11.5 + M1b §11.5 + M1c §11.5) would benefit from this convention as an explicit invariant — the helper distinguishes archaeology-preservation cases from live-rebrand cases. Captured for FIDRAFT-worthy convention update; do NOT extend M1d scope to add it.

6. **(No ODD §2.5 violation found in surrounding code/docs at plan-authoring time.)** The mechanical rename is the rename itself; no defensive `if`s without backing AC; no behaviour changes beyond the rename. The thirteen-component fence is wider than M1c (five) but each component's rename-touched lines all trace back to AC.RNM-1d.1 / .2 / .3 / .4 / .5.

7. **(No methodology breach in plan structure.)** ACs are outcome-shape, deterministic, behaviour-count-checked. AC.RNM-1d.6 (negative AC enforcing the OTel-surface fence) is the explicit ODD §2.5 reverse-direction protection. The wider-than-prior-amendments fence is disclosed (finding #1 + the §1 thirteen-component fence statement) so the dispatcher sees the surface in the plan-doc commit before the feature commit.

---

## 12. Method-decision register (placeholder)

The method-decision content for M1d lives in §14 below per the
`pos-amend seal --plan-doc` convention (which expects §14 as the
SHA-backfill anchor). Content moved to §14 to avoid duplication.

§14 anchored from authoring per M1c's locked precedent (avoid post-seal restructure).

---

## 13. Test breakdown (post-build)

Per AC, the touched test files plus the cross-cutting HC#4 verification.
- AC.RNM-1d.1: every Phase B test file (heaviest-touched: observability-aggregator's 10 D-test files; others enumerated at build time).
- AC.RNM-1d.2: post-rename `grep -rEho '"loam\.[a-z_]+'` enumerates the 25 + 7 root inventory.
- AC.RNM-1d.3: observability-aggregator's full D-test suite + the rebrand of `TRACER_TO_COMPONENT` keys.
- AC.RNM-1d.4: `pytest framework/observability-aggregator/tests/test_d9_self_obs_and_privacy.py` (the self-obs filter test).
- AC.RNM-1d.5: post-rename grep on `framework/*/docs/`, `docs/odd-in-pos.md`, `docs/rebuild/components/*/proposal.md` for `pos.<root>` ; expect 0 hits.
- AC.RNM-1d.S: each sealed component's `test_no_sealed_amendments.py` + HOL `test_cross_cutting.py` + HOL `test_d1_byte_content_match.py` (post-rebaseline).

### Backwards-compat verification

N/A — hard cutover per series-master D-RNM.3.

### HC#4 byte-content sample status

POST-REBASELINE (single SHA bump on `host.py`). The fourteen other sample files in `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py` are unchanged by M1d (verified pre-build per §11 finding #3). HC#4 stays GREEN with the M1d in-band retire-and-rebaseline.

### Dependents cleared to dispatch

- **M1e** (largest remaining sub-amendment) cleared to dispatch. Per series-master ladder + dispatch §Output: M1e is `pos-amend` CLI rename + `loam.*` namespace pivot (the latter pulls in the entry-point group `pos.bootstrap.contributions` and the internal `_POS_V2_*` / `pos_v2_root` decorations and the `--pos-v2-root` shell flag). Largest mechanical surface of the series; owner-review gate recommended pre-dispatch given fence width.
- M1e..M1g remain serial in the shared tree per `feedback_serialize_amendment_builds`.

---

## 14. Method-decision register (post-build)

### D-build.M1d.1 — sed-vs-Edit per file

(Populated post-build with the actual mix per file.)

### D-build.M1d.2 — order of Phase A vs Phase B

(Populated post-build with the actual order applied.)

### D-build.M1d.3 — HC#4 SHA pin update timing

(Populated post-build with the actual SHA + commit position.)

### Commit SHAs

- Amendment commit: `fb45384669428dd741cf208b5e1ea39aa90cf13f` —
  `chore(rename-1d-apply): pos-amend apply for amendment #79 (M1d OTel pos.* → loam.* root rebrand)`
- Seal commit: `74ae5d304928dbc70fc0e68c074be1b8617d6155` —
  `chore(seals): M1d OTel root rebrand — every span/event/attribute/tracer/logger/Resource literal with first segment `pos` rebases to `loam` across every framework callsite (25 documented roots + 7 tracer-component variants per locked plan §1 inventory) + observability-aggregator namespace defaults (config.self_namespace_prefix, ingest function-defaults x3, Resource service.name, schema.TRACER_TO_COMPONENT keys) + live component docs (framework/<comp>/docs/) + component proposals (docs/rebuild/components/<comp>/proposal.md) + docs/odd-in-pos.md worked examples + HC#4 in-band retire-and-rebaseline for framework/workspace-bootstrap/src/workspace_bootstrap/host.py (line 82 tracer-name rebrand triggers SHA bump per ODD §4 in-band methodology-aligned). Hard cutover per series-master D-RNM.3 — no dual-emit shim. — hands-off-lifecycle+cost-governance+graceful-degradation+objective-tracker+observability-aggregator+orchestrator+primary-persona+reversibility-primitive+self-correction+self-upgrade+telegram-interface+workspace-bootstrap+workspace-sync at fb45384`
## 15. References

- **Series master:** `docs/rebuild/plans/oss-v0-1-0-publish-rename.md` (committed `ebe0a57`).
- **Prior sub-amendments:**
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1a.md` (sealed `143d465`).
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1b.md` (sealed `d97c8c1`).
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1c.md` (sealed `1e99d0b`).
- **Authority documents (inherited from series master):**
  - `docs/rebuild/plans/loam-rename-decisions.md` Tier-1 item 5.
  - `.scratch/claude-output/loam-rename-migration-plan.md` §3.5.
- **Programme master plan:** `docs/rebuild/plans/oss-v0-1-0-publish.md` (M1d row in §5 per M1b precursor commit `7be713b`).
- **STATE.md** — governing rules.
- **ODD methodology + ODD-in-loam:** `docs/odd-methodology.md`, `docs/odd-in-pos.md`.
- **VALUE_PROPOSITION:** `docs/rebuild/VALUE_PROPOSITION.md`.
- **CLAUDE.md** + `~/.claude/CLAUDE.md` + `~/.claude/projects/-Users-lukeivers-pos3/memory/MEMORY.md`.
- **Memory bullets carried forward:**
  - `feedback_no_amend_in_agent_dispatches`.
  - `feedback_dispatch_explicit_pos_amend_apply`.
  - `feedback_subagent_odd_violation_halt`.
  - `feedback_amendment_dispatch_speedups`.
  - `feedback_summarize_and_surface_decisions`.
  - `feedback_serialize_amendment_builds`.
  - `feedback_always_specify_wd_in_dispatches`.
  - `feedback_verify_post_amendment_state`.
  - `feedback_duration_estimation_rubric`.
  - `feedback_loose_AC_text_fix_AC_not_implementation`.
  - `feedback_critical_thinking_on_deviations`.
  - `feedback_strict_autonomy_no_pause_for_authorized_work`.
- **Precedent multi-component sealed-amendment manifests:**
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1c.manifest.yaml` (M1c sibling — five-component fence).
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1b.manifest.yaml` (M1b sibling — eleven-component fence).
  - `docs/rebuild/plans/oss-v0-1-0-publish-rename-1a.manifest.yaml` (M1a sibling — four-component docs-only fence).
- **`pos-amend` tool:** `framework/tools/pos-amend/` (M1d is built using this CLI; rename to `loam amend` is M1e per dispatch §Scope).
