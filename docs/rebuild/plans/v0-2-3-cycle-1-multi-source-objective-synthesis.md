# v0.2.3 Cycle 1 — Multi-source objective synthesis (extraction-core rebuild)

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-04 (Sonnet, plan-author dispatch).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Predecessor:** v0.2.3 master plan committed at `35155fd` (parent §3 Cycle 1 + §4 + §6.1/§6.3 + §9 method-decision register).

**BASELINE (pre-build tip):** to be set to the source-edit commit when the build commit lands.

**Parent plan:** `docs/rebuild/plans/v0-2-3-master-plan.md` §3 Cycle 1 + §4 Cycle 1 dispatch brief + §6 open items + §9 method-decision register.

**Always-load grounding:** `docs/odd-llm-grounding.lean.md` (committed `d37c623`; auto-loaded structurally per v0.2.2 AC.OGP.1/AC.OGP.2). The §self-checks (§8 of that doc) were applied to every "objective" / "AC" / "constraint" / "capability" named in this plan-doc; §11 below records the self-check pass.

**Quality bar (Luke directive 2026-05-04, carried verbatim from master plan):**

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

Cycle 1 IS the altitude rebuild. Multi-source synthesis fully implemented (not stub). Banding rule explicit (V/P/H criteria documented in extension to `plugins/dev-sdlc/docs/odd-methodology.md`). §self-checks 1-5 enforced programmatically + LLM-as-judge for borderline. Cost surfacing honest (no hidden LLM-pass spend). Adapter outputs reshaped to evidence rows, not ACs. Per-band rule documented. **No partial features.** Self-checks pass on every example AC named in this plan-doc per §11.

---

## §1 — Outcome shape

Cycle 1 ships the **multi-source objective synthesis pipeline** that replaces v0.1.8's tree-walk extraction with an LLM-pass synthesis layer producing objectives at outcome altitude. The four-stage workflow (init → analyze → generate → verify) shape survives unchanged. The **generate** stage rewires: instead of dispatching adapters that emit symbol-altitude `BandedAC` rows to `acs:`, generate now (a) collects multi-source inputs (README + design docs + tests + user-survey + adapter-emitted code-pattern signals), (b) invokes a single LLM-pass synthesis call emitting banded `Objective` + `Constraint` + `Capability` rows, (c) writes the pre-existing adapter symbol-tree output to renamed `evidence-rows.yaml` for Cycle 2 backing-map population.

**Fence reality.** `plugins/dev-sdlc/odd-extractor/` already exists. Cycle 1 extends `spec.py` (new `Objective` / `Constraint` / `Capability` models alongside existing `RawACs`), rewires `generate.py` (multi-source inputs + LLM-pass + evidence-rows routing), extends `verify.py` (objective-altitude rendering + §self-check audit), and adds new modules (`synthesis.py`, `multi_source.py`, `altitude_validator.py`). Adapter `extract()` signatures unchanged; routing layer in generate.py redirects their output.

**Release-note promise.** `loam odd-extract <repo>` against a canonical fixture produces `contract-draft.md` containing a banded objectives table + constraints + capabilities at outcome altitude (surviving the implementation-swap test); sidecar `contract-draft.yaml` carrying typed lists; `evidence-rows.yaml` for Cycle 2; `audit-log/<NNNN>.yaml` per stage including new `synthesis_complete` event-kind. On README-rich fixtures the README purpose statement maps to a banded objective; test names asserting the same outcome lift band to VERIFIED. §self-checks 1-5 run on every emitted row; rows failing checks are restated, downgraded to HYPOTHESISED, or dropped per decision tree (AC.OBJX.8).

**Discipline.** v0.1.6 cost-governance budget envelope wraps the synthesis LLM-pass per AC.OBJX.6: dry-run estimate pre-call; live-mode enforces envelope per existing `BudgetExceededError`; default ceiling $1.00/extraction per master plan §6.1; halt-and-surface if calibrated cost outside $0.10–$5.00.

---

## §2 — Lens checks (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage-first

Composes on existing primitives + leans on Anthropic SDK:

- **Anthropic Messages API + prompt caching.** Synthesis prompt is large (lean grounding doc §altitudes/§drift-modes/§self-checks injected verbatim per AC.OGP propagation). Prompt caching cuts D2 re-extraction cost. `claude-api` SKILL is the reach-for default.
- **`framework/cost-governance/`'s `BudgetEnvelope` + `enforce_budget` + `BudgetExceededError`.** v0.1.6 primitive; Cycle 1 wires synthesis-pass through it without surface change.
- **`bands.py` `ConfidenceBand` + `Evidence` + per-band model_validators.** New `Objective` / `Constraint` / `Capability` models reuse the same enum + per-band invariant pattern (Pydantic ValidationError on construction).
- **Four-stage workflow + `cli.py` dispatch.** Generate + verify rewired in-place; CLI surface unchanged.
- **`observability.py` audit-log.** Existing `write_audit_entry` extends with new event_kinds (`synthesis_complete`, `altitude_check_complete`).
- **AC.OBJX.9 user-survey.** Reads survey file per AC.ONBOARD.15 shape; reuses `framework/workspace-bootstrap/`'s `survey_parser.py` via lazy-import.
- **Lens 5 `EVAL_DIMENSIONS`.** §self-checks 1-5 evaluated as 5 named axes via concurrent LLM-as-judge for borderline rows; programmatic heuristics gate cost.

Answer: every load-bearing primitive composes on existing v0.1.6 → v0.2.2 surfaces; Anthropic SDK is the new dependency wired through `claude-api` SKILL conventions.

### Lens 2 — Harness + primary-persona value

- **Primary-persona test:** translation burden drops from "131 symbol-altitude rows" to "~10–30 outcome-altitude rows mirroring user's own framing." Pass.
- **Harness test:** synthesis layer + altitude validator + multi-source collector are reusable harness primitives (v0.2.4 completeness interview composes on the `Objective` model). Pass.

### Lens 3 — ODD authoring

Outcome + named ACs (§3) + halt triggers (§5 + §6) + acceptance smoke (§4). Method-loose per builder's call within constraints: 5 source kinds; V/P/H banding rule; §self-checks 1-5 enforced programmatic + LLM-judge for borderline; cost-band $0.10–$5.00; >30% self-check fail-rate halts; adapter outputs to `evidence-rows.yaml`.

### Lens 4 — Prompt scope ↔ confidence

**HIGH** confidence for shape: master plan §3 Cycle 1 names all 12 ACs verbatim; v0.1.8 substrate verified-working; cost-governance + adapter Protocol verified. Tight scope: extension to existing component, additive Pydantic models in `spec.py`, rewired `generate.py`, new modules, AC-shaped tests.

**MEDIUM** for synthesis-prompt design (master plan §7.1 names this risk). Commitments: (1) system prompt with lean grounding doc §6 + §7 + §8 verbatim; user prompt with multi-source bundle in priority order; response format = structured JSON matching the typed-model shape; (2) prompt caching on lean grounding + structural shape; (3) ≥70% §self-check pass-rate sanity floor; >30% fail-rate triggers AC.OBJX.8 `needs_fresh_start` halt.

**MEDIUM** for altitude-validator heuristic/LLM-judge split. Commitments: (1) programmatic heuristics (`outcome_or_fact` keyword-and-regex; `implementation_swap_test_proxy` symbol/file/line markers); (2) LLM-judge only for `borderline` rows; concurrent eval over 5 axes per `EVAL_DIMENSIONS`; cost-cap ~10% of synthesis budget; (3) decision tree on failure: §1 fail → drop; §2 fail → restate-as-capability or drop; §3/4 fail → downgrade band; §5 fail → drop unless VERIFIED evidence supports HYPOTHESISED retention.

**MEDIUM-LOW** for cost calibration. Commitments: (1) default model Sonnet; (2) default ceiling $1.00/extraction; (3) dry-run cost via SDK's `messages.count_tokens` if available, else 4-chars-per-token approximation; (4) halt-and-surface from build agent if calibrated cost on canonical fixture lands outside $0.10–$5.00 (band is contract; ceiling within band is build agent's adjustable choice with documented rationale).

**HIGH** for substrate preservation (four-stage workflow + adapter Protocol + audit-log). v0.1.8 is verified-working; Cycle 1 extends, doesn't replace.

### Lens 5 — Swarming

Single-component fence under `plugins/dev-sdlc/odd-extractor/`. Per-concern module decomposition (synthesis.py + multi_source.py + altitude_validator.py + spec.py extension) matches master plan's named-mechanism naming + gives tightest AC-per-module mapping. `max_planner_depth: 1` — sub-planning the synthesis prompt is coordination overhead with no tighter AC. Model rationale: Sonnet default; Opus permitted for synthesis-prompt design specifically with mandatory `model-rationale:` line if depth exceeds Sonnet's reach.

---

## §3 — AC enumeration — `AC.OBJX.*` (locked, 12 ACs)

Each AC has at least one explicit pytest. ODD §2.5 — every line of code, branch, test maps to a named AC. AC.OBJX.1 → AC.OBJX.12 inherited from master plan §3 Cycle 1 with method tightening per §7. §self-checks 1-5 ran on every example outcome / capability / constraint named in this plan-doc; §11 records the audit.

- **AC.OBJX.1 — `Objective` Pydantic model.**
  - Fields: `objective_id` (regex `^O\.[a-z][a-z0-9-]*\.\d+$`); `text` (min 20 chars); `confidence: ConfidenceBand` (V/P/H reused from `bands.py`); `evidence: ObjectiveEvidence` (multi-source citation block); `domain: str` (e.g., `dispute-flow`, `auth`, `audit`).
  - `ObjectiveEvidence` carries: `readme_excerpts: list[str]` (≤500 chars each); `design_doc_refs: list[str]` (path + section heading); `test_name_refs: list[str]` (test path + assertion name); `survey_line_refs: list[str]`; `code_pattern_refs: list[str]` (file:line); `repo_sha: str | None`; `rationale: str | None`.
  - `model_validator` enforces per-band invariants: VERIFIED requires non-empty `test_name_refs` AND (`readme_excerpts` OR `design_doc_refs`) AND non-null `repo_sha`; PLAUSIBLE requires ≥1 of `readme_excerpts`/`design_doc_refs`/`survey_line_refs`; HYPOTHESISED requires non-empty `rationale`.
  - Fence: `spec.py` extension. Test: `test_AC_OBJX_1_objective_model.py` — construction success per band; ValidationError on band/evidence mismatch; round-trip; ID regex enforcement.

- **AC.OBJX.2 — `Constraint` Pydantic model.**
  - Fields: `constraint_id` (regex `^K\.[a-z][a-z0-9-]*\.\d+$`); `text`; `bounds_kind: Literal["compliance","infra","language","security","domain"]`; `evidence: ConstraintEvidence` (same shape as ObjectiveEvidence minus `test_name_refs` — tests assert outcomes, not bounds).
  - `model_validator` enforces ≥1 ref kind populated.
  - Fence: `spec.py`. Test: `test_AC_OBJX_2_constraint_model.py` — construction per `bounds_kind`; ValidationError on empty evidence; round-trip.

- **AC.OBJX.3 — `Capability` Pydantic model.**
  - Fields: `capability_id` (regex `^C\.[a-z][a-z0-9-]*\.\d+$`); `text`; `serves: list[str]` (non-empty; each matches `O.<...>` regex); `evidence: CapabilityEvidence` (same shape as ObjectiveEvidence).
  - `model_validator` enforces `serves` non-empty + objective_id regex compliance; referential integrity (target objective exists) deferred to AC.OBJX.10 verify-stage cross-validation.
  - Fence: `spec.py`. Test: `test_AC_OBJX_3_capability_model.py` — construction; ValidationError on empty `serves` / malformed reference; round-trip.

- **AC.OBJX.4 — Multi-source input pipeline.**
  - New module `multi_source.py`. Function `collect_multi_source_inputs(repo_path, workspace_root, *, evidence_rows) -> MultiSourceBundle`.
  - Sources: (a) README — `README*` glob at root; 50KB cap with truncate marker. (b) design docs — `docs/**/*.md`; 20-file × 20KB caps. (c) tests — adapter-derived rows of kind `test`; extract test name + first assertion + file:line. (d) user-survey — read order per AC.OBJX.9. (e) code patterns — adapter-derived `evidence_rows`.
  - Output: `MultiSourceBundle` Pydantic model + `total_token_estimate` (4-chars-per-token approximation).
  - Fence: `multi_source.py`. Test: `test_AC_OBJX_4_multi_source_pipeline.py` — fixtures: README-rich; README-thin; README-absent; survey present/absent variants; cap enforcement on oversized README; assert per-fixture field population.

- **AC.OBJX.5 — LLM-pass synthesis.**
  - New module `synthesis.py`. Function `synthesize_objectives(bundle, *, repo_sha, anthropic_client) -> SynthesisResult`.
  - System prompt: lean grounding doc §6 + §7 + §8 + V/P/H banding rule injected verbatim. User prompt: bundle in priority order (README → design docs → tests → survey → code patterns). Response: structured JSON `{objectives: [...], constraints: [...], capabilities: [...]}`.
  - Banding rule (prompt-side): VERIFIED if test asserts outcome AND README states it (two-source); PLAUSIBLE if README/design-doc/survey single-source; HYPOTHESISED if pattern-only inference. Survey-shape claims cap at PLAUSIBLE per AC.OBJX.9.
  - Prompt caching: lean grounding + banding rule + bundle structural shape cached; per-extraction tail varies (`claude-api` SKILL conventions).
  - Returns `SynthesisResult(objectives, constraints, capabilities, raw_response, token_count, cost_actual_cents)`.
  - Fence: `synthesis.py`. Test: `test_AC_OBJX_5_llm_pass_synthesis.py` — stub Anthropic client with canned responses (no real API calls); assert correct array parsing; ValidationError on malformed LLM rows; prompt structure check; `repo_sha` threading into VERIFIED evidence.

- **AC.OBJX.6 — Dry-run cost estimate + budget envelope.**
  - Pre-synthesis: token-count via SDK `messages.count_tokens` if available, else 4-chars-per-token approximation. Cost band $0.10–$5.00 per extraction at default ceiling $1.00 (master plan §6.1).
  - Live mode: `enforce_budget(estimate, envelope)` raises `BudgetExceededError`. `--budget-cents N` + `--budget-override` mirror v0.1.8 surface.
  - Build-agent halt-and-surface: if calibrated cost on canonical jsts-playwright-app fixture lands outside $0.10–$5.00 band; ceiling within band is build agent's adjustable choice with documentation.
  - Fence: `synthesis.py` + `cli.py`. Test: `test_AC_OBJX_6_cost_estimate_and_envelope.py` — synthetic bundle; estimate within ±10% of computed cost; `BudgetExceededError` raised on overrun; `--budget-override` allows overrun; `budget_override` audit-log entry.

- **AC.OBJX.7 — Adapter-output reshape (evidence-rows routing).**
  - Adapter `extract()` signatures unchanged — JS/TS + Ruby continue producing `RawACs` with `BandedAC` dicts.
  - Routing in `generate.py` redirects: union of adapter outputs → `<workspace>/.loam/extractions/<repo-id>/evidence-rows.yaml` (renamed from `raw-acs.yaml` per master plan §6.3); same data flows into synthesis bundle via `multi_source.py`'s `evidence_rows` parameter.
  - **Legacy compat:** v0.1.9 PR-safety reads `contract-draft.yaml acs:`. Cycle 1 PRESERVES that field; populates with typed `Objective` rows (NOT symbol-altitude evidence rows). Full `acs:` drop is Cycle 3's call per master plan §6.2.
  - `evidence-rows.yaml` shape: `{schema_version: 1, extraction_id: <id>, evidence_rows: [<dict>...], unhandled_paths: [...]}`; round-trips through `RawACs.model_dump`/`model_validate`.
  - Fence: `generate.py` rewire. Test: `test_AC_OBJX_7_evidence_rows_routing.py` — synthetic adapter with 3 BandedAC rows; assert `evidence-rows.yaml` written with all 3; assert these rows NOT in `contract-draft.yaml acs:`; assert `acs:` carries synthesized Objectives.

- **AC.OBJX.8 — Altitude validator (programmatic + LLM-as-judge).**
  - New module `altitude_validator.py`. Function `validate_altitude(rows, *, anthropic_client) -> ValidationReport`.
  - Programmatic heuristics first per Lens 4 commitment: each row gets `pass`/`fail`/`borderline` per §self-check.
  - LLM-as-judge invoked only for `borderline` rows: single concurrent call evaluates all 5 axes per `EVAL_DIMENSIONS`; cost-cap ~10% synthesis budget.
  - Decision tree on failure: §1 fail → drop; §2 fail → restate-as-capability if upstream supports, else drop; §3/4 fail → downgrade band; §5 fail → drop unless VERIFIED evidence supports HYPOTHESISED retention.
  - **Drift detection:** >30% fail rate across all rows → halt-and-surface (`needs_fresh_start` shape from Lens 5). Build agent surfaces; does NOT silently restart.
  - Fence: `altitude_validator.py`. Test: `test_AC_OBJX_8_altitude_validator.py` — fixtures with rows at clear-pass / clear-fail / borderline per axis; assert heuristic classification + LLM-judge invoked only on borderline + decision-tree application + drift-halt at >30%.

- **AC.OBJX.9 — User-survey context integration.**
  - Read order: `<repo>/.loam/onboarding-survey.md` → `~/loam-onboarding-survey.md` → `$LOAM_ONBOARDING_SURVEY` env-var → none.
  - Parser: H2-section based per AC.ONBOARD.15 shape; reuses `framework/workspace-bootstrap/survey_parser.py` via lazy-import (cross-component isolation pattern). Best-effort; never blocks.
  - Survey-shape claims cap at PLAUSIBLE — synthesis prompt instructed not to promote survey-only evidence to VERIFIED.
  - Survey-absent path: `MultiSourceBundle.user_survey = None`; synthesis proceeds.
  - Fence: `multi_source.py`. Test: `test_AC_OBJX_9_survey_context.py` — fixtures across read-order paths + survey-absent; assert correct precedence; banding cap on survey-only-evidence rows.

- **AC.OBJX.10 — Output schema reshape (verify-stage rendering).**
  - `verify.py` extended: reads `SynthesisResult` from generate-stage state; populates `contract-draft.yaml` with typed `objectives:` + `constraints:` + `capabilities:` lists alongside legacy `acs:` (typed Objectives per AC.OBJX.7).
  - `contract-draft.md`: section per altitude (Objectives table → Constraints table → Capabilities table → Evidence-rows summary → §self-checks audit table from `altitude_validator.py`).
  - Cross-reference validation: every `Capability.serves` ID must resolve to a present objective; raises `StageError` on dangling reference.
  - ODD §2.5 coverage check (extended): every adapter-emitted path appears as evidence row OR `unhandled_paths`; objectives/constraints/capabilities not required to map 1:1 to code paths (Cycle 2 backing-map handles that).
  - Fence: `verify.py` rewire. Test: `test_AC_OBJX_10_verify_stage_rendering.py` — synthetic SynthesisResult; assert all 4 markdown section types; sidecar YAML typed lists; dangling-reference `StageError`; §self-checks audit table rendered.

- **AC.OBJX.11 — Component tests against 3+ multi-source fixtures.**
  - Fixtures under `tests/fixtures/multi-source-synthesis/`: (1) `readme-rich/` — full README purpose statement + 2 design docs + 3 test files + adapter-stub-evidence; (2) `readme-thin-tests-rich/` — 1-line README + 5 test files asserting outcomes + adapter rows; (3) `code-pattern-only/` — no README, no docs/, no tests; only adapter symbol-tree.
  - Each exercises synthesis → altitude validator → verify rendering. Assert objective count > 0; assert banding distribution honors multi-source rule (V on `readme-rich`; mostly P on `readme-thin-tests-rich`; mostly H on `code-pattern-only`).
  - Fence: tests + fixtures. Test: `test_AC_OBJX_11_multi_source_fixtures.py` — 3 sub-tests; stub Anthropic with fixture-tuned canned responses; per-fixture banding distribution within tolerance.

- **AC.OBJX.12 — Audit-log per synthesis call.**
  - New event_kinds: `synthesis_complete` carries `source_list`, `token_count`, `cost_actual_cents`, `objective_count_by_band`, `constraint_count`, `capability_count`. `altitude_check_complete` carries `total_rows`, `pass_count`, `fail_count`, `borderline_count`, `pass_rate`, `dropped_count`, `downgraded_count`.
  - Composed with v0.1.6 SOC-2 floor + v0.1.8 audit-log primitive; payload uses existing `estimate` field for structured dict (no schema-version bump).
  - Fence: `observability.py` extension; `synthesis.py` + `altitude_validator.py` call sites. Test: `test_AC_OBJX_12_audit_log_synthesis.py` — assert both event_kinds present post-run with required fields; structured payload round-trip.

---

## §4 — Component & file layout

**PRIMARY scope:** `plugins/dev-sdlc/odd-extractor/` (the existing component's sealed fence; new modules + tests + Pydantic-model extensions land under it).

**TERTIARY admission:** `docs/rebuild/plans/` (universal-paths admission for the plan-doc paper trail) + `plugins/dev-sdlc/docs/odd-methodology.md` (banding rule extension per Cycle 1 quality bar).

### Existing paths (extend in-place; sealed-content unchanged)

- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/spec.py` — extend with new Pydantic models (`Objective`, `Constraint`, `Capability`, `MultiSourceBundle`, `SynthesisResult`, `ValidationReport`); existing `RawACs` / `ContractDraft` / `ExtractionConfig` / `AnalysisPlan` / `Slice` unchanged.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/generate.py` — rewire dispatch: adapter outputs → `evidence-rows.yaml`; multi-source bundle → synthesis → `SynthesisResult` persisted to extraction-dir state; populates `contract-draft.yaml acs:` with typed `Objective` rows for v0.1.9 PR-safety transitional compatibility.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/verify.py` — extend rendering: section per altitude + cross-reference validation + §self-checks audit table.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/observability.py` — extend event_kinds (`synthesis_complete`, `altitude_check_complete`).
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/cli.py` — additive `--budget-cents` integration with synthesis cost band (existing flag, expanded use); additive estimate output fields (synthesis-specific token counts).
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/__init__.py` — additive exports.

### New paths (this cycle)

Source modules (under `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/`):

- `multi_source.py` — multi-source input collector; `collect_multi_source_inputs(repo_path, workspace_root, *, evidence_rows) -> MultiSourceBundle`.
- `synthesis.py` — LLM-pass synthesis layer; `synthesize_objectives(bundle, *, repo_sha, anthropic_client) -> SynthesisResult`. Hosts the synthesis prompt + prompt-caching wiring + per-row Pydantic validation + post-validation audit-log emission.
- `altitude_validator.py` — §self-checks 1-5 enforcement; `validate_altitude(rows, *, anthropic_client) -> ValidationReport`. Programmatic heuristics + LLM-as-judge for borderline + decision tree on failure + drift-detection halt.

Tests (under `plugins/dev-sdlc/odd-extractor/tests/`):

- `test_AC_OBJX_1_objective_model.py`
- `test_AC_OBJX_2_constraint_model.py`
- `test_AC_OBJX_3_capability_model.py`
- `test_AC_OBJX_4_multi_source_pipeline.py`
- `test_AC_OBJX_5_llm_pass_synthesis.py`
- `test_AC_OBJX_6_cost_estimate_and_envelope.py`
- `test_AC_OBJX_7_evidence_rows_routing.py`
- `test_AC_OBJX_8_altitude_validator.py`
- `test_AC_OBJX_9_survey_context.py`
- `test_AC_OBJX_10_verify_stage_rendering.py`
- `test_AC_OBJX_11_multi_source_fixtures.py`
- `test_AC_OBJX_12_audit_log_synthesis.py`
- `test_synthesis_integration.py` — full pipeline end-to-end on `readme-rich` fixture; asserts every AC's exit-state simultaneously (objective count + banding distribution + evidence-rows.yaml present + altitude validator report + audit-log + contract-draft.md sections).

Fixtures (under `plugins/dev-sdlc/odd-extractor/tests/fixtures/multi-source-synthesis/`):

- `readme-rich/` — README.md (3-paragraph purpose statement) + docs/architecture.md + docs/auth-flow.md + tests/test_dispute_flow.spec.ts + tests/test_csv_upload.spec.ts + tests/test_audit_trail.spec.ts + adapter-stub-evidence.yaml.
- `readme-thin-tests-rich/` — README.md (single-line) + tests/* (5 spec files asserting user-facing outcomes) + adapter-stub-evidence.yaml.
- `code-pattern-only/` — empty README + no docs/ + no tests/ + adapter-stub-evidence.yaml only.

Documentation:

- `plugins/dev-sdlc/docs/odd-methodology.md` — extend with V/P/H banding rule for objectives/constraints/capabilities (multi-source verification criteria; verbatim from this plan-doc §3 AC.OBJX.5).

### Smoke dimensions (per master plan §3 Cycle 1)

- **D1 (cold-state)** ✓ — `loam odd-extract <readme-rich-fixture>` against fresh canonical workspace produces banded objectives + constraints + capabilities + evidence-rows.yaml + audit-log entries. Verified by `test_synthesis_integration.py` + per-AC tests.
- **D2 (steady-state)** ✓ — re-run extract on unchanged fixture is idempotent (re-reads existing extraction-dir state; prompt-caching hit-rate increases on second run; no double-write on no-change). Verified by integration test re-invocation variant.
- **D5 (cross-session)** ✓ — extraction artefacts at `<workspace>/.loam/extractions/<repo-id>/` survive `/clear`. `contract-draft.md` + `contract-draft.yaml` + `evidence-rows.yaml` + `audit-log/<NNNN>.yaml` files persist; subsequent session reads them. Verified by manifest-roundtrip test.
- **D6 (telemetry-floor)** ✓ — per AC.OBJX.12. Verified by `test_AC_OBJX_12_audit_log_synthesis.py`.
- **D3 (restart)** inherited from existing `--resume` mode + state.yaml shape; not re-tested at Cycle 1 (no new state to restart through; if synthesis fails mid-call, the LLM-pass is atomic — either the response lands and parses, or it doesn't; partial-state is `synthesis_failed` audit-log entry + retry).
- **D4 (reboot)** n/a structurally — odd-extract is invoked-on-demand, not a daemon; filesystem state survives reboot trivially per existing v0.1.8 precedent.

---

## §5 — Build dispatch brief (READY FOR DISPATCH after this plan-doc seals)

```
# v0.2.3 Cycle 1 BUILD dispatch — Multi-source objective synthesis

Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`. NOT pos3.

LOAD `docs/odd-llm-grounding.lean.md` FIRST. Critical for v0.2.3 — synthesis altitude must NOT drift to implementation-shape.

Authority: build the 12 AC.OBJX.* family per sub-plan-doc §3. Single-component fence on plugins/dev-sdlc/odd-extractor/. Tertiary admissions: docs/rebuild/plans/ + plugins/dev-sdlc/docs/odd-methodology.md (banding rule extension).

Principles to apply at turn-start:
  AUTONOMY / F2 RUTHLESS FEEDBACK / LOCKED-DESIGN-NOT-LICENSE / PROMISES > IN-MOMENT JUDGMENT / ODD §2.5 / OUTPUT-TO-DISK / WD-IN-DISPATCHES / NO --amend / NO push / NO FALSE FAULT / PRINCIPLE-APPLICATION DISCIPLINE / TEST-AGAINST-OPERATIONAL-OBJECTIVE-BEFORE-ESCALATING.

Quality bar (Luke directive 2026-05-04, carried verbatim): every AC ships complete + tested. Multi-source synthesis fully implemented (not stub). Banding rule explicit. §self-checks 1-5 enforced programmatically + LLM-as-judge for borderline. Cost surfacing honest. Adapter outputs reshaped to evidence-rows. No partial features.

Source pointers (READ FIRST):
  - sub-plan-doc (THIS file's predecessor) at docs/rebuild/plans/v0-2-3-cycle-1-multi-source-objective-synthesis.md
  - master plan §3 Cycle 1 + §4 Cycle 1 dispatch brief at docs/rebuild/plans/v0-2-3-master-plan.md (commit 35155fd)
  - Lean grounding doc at docs/odd-llm-grounding.lean.md (commit d37c623)
  - v0.1.8 substrate: bands.py / spec.py / generate.py / verify.py / cli.py / observability.py / registry.py
  - v0.1.6 cost-governance: framework/cost-governance/src/loam/cost_governance/ (BudgetEnvelope + enforce_budget + BudgetExceededError)
  - v0.2.1 Cycle 1 survey-parser shape at framework/workspace-bootstrap/src/loam/workspace_bootstrap/survey_parser.py (lazy-import for AC.OBJX.9 reuse)
  - rd-automation extraction artefact at /Users/lukeivers/pos3/workspace/rd-automation/.loam/extractions/rd-automation-5f656bad/ (concrete v0.1.8 wrong-altitude grounding)
  - Eric's survey response at /Users/lukeivers/pos3/workspace/.scratch/claude-output/eric-onboarding-response-2026-05-05.md (multi-source synthesis input precedent)
  - claude-api SKILL conventions for Anthropic SDK + prompt caching

Fence + ACs + smoke + AI-time + out-of-scope: per sub-plan-doc §3 + §4.

Halt triggers — enumerated at sub-plan-doc §6 + below; halt-and-surface, do NOT silently work around:
  - WD drifts to pos3.
  - Multi-source pipeline design surfaces a source not in master plan list (production logs, runtime telemetry, etc.).
  - LLM-pass cost calibration on canonical jsts-playwright-app fixture lands outside $0.10–$5.00 band.
  - Synthesis prompt design lands above Sonnet's depth (Opus rationale required).
  - Output-schema reshape requires breaking changes to v0.1.9 PR-safety beyond master plan framing.
  - Altitude-validator design requires LLM-as-judge with non-trivial cost (>10% synthesis budget).
  - >30% §self-check fail rate on any 3 synthetic fixtures.
  - LLM-pass cannot reach outcome-altitude on any 3 synthetic fixtures.
  - ODD §2.5 violations in surrounding code OR master plan itself.
  - Cycle wall-clock >10 h with no progress.
  - >3 escalations needed.

Bookkeeping:
  - pos-amend apply (NOT --amend); manifest schema v3.
  - Single semantic commit on apply: feat(odd-extractor): v0.2.3 Cycle 1 — multi-source objective synthesis.
  - Short-form seal commit per AC.DPS2 schema-v3.
  - §14 backfill separate post-seal commit per AC.D-sa.7.
  - Master plan §9 per-cycle SHA backfill row updates with apply + seal SHAs.

Model rationale: Sonnet default. Opus permitted for synthesis-prompt design specifically if depth exceeds Sonnet's reach, with mandatory `model-rationale: <model> — <reason>` line per Lens 5.
```

---

## §6 — Honest doubts (F2 RF on this decomposition)

**6.1 — LLM-pass synthesis may not reliably reach outcome-altitude.** Master plan §7.1 names 25% residual drift risk. *Mitigation:* AC.OBJX.8 drift-detection (>30% halt) + §self-checks programmatic + LLM-as-judge per `EVAL_DIMENSIONS`; HYPOTHESISED banding for pattern-only. Synthesis-prompt design is the highest-leverage variable; build agent has authority to iterate within Sonnet's scope; Opus opt-in with rationale.

**6.2 — Cost calibration may exceed $1.00 ceiling on rich-input fixtures.** README-rich fixture with 5 design docs + 50 test files + 100 adapter rows + survey could push bundle to ~30K tokens; Sonnet input pricing ~$0.10–$0.15; output similar. *Mitigation:* AC.OBJX.6 dry-run estimate + budget envelope + halt-and-surface band $0.10–$5.00. Build agent calibrates default ceiling within band on canonical fixture; documents in dispatch report.

**6.3 — Survey-shape claims cap at PLAUSIBLE — Eric sees many P rows.** Eric's survey response (production-stake YES, SOC-2 narrative, audit-trail-via-userEmail, RSA-OAEP, CORS) is mostly survey-only (rd-automation README is sparse, no test assertions). Master plan §7.7 names this as honest-P-pending-ratification (correct shape). *Mitigation:* synthesis prompt instructs no VERIFIED promotion from survey-only evidence; Cycle 2 ratification flow handles. Build agent surfaces if P-band count >20 on synthetic-rich fixture (cap or batch).

**6.4 — Adapter Protocol preserved but downstream test fixtures may need updates.** Adapter `extract()` signatures unchanged; integration tests asserting end-to-end contract-draft contents need updating (currently expect symbol-altitude rows in `acs:`; Cycle 1 expects typed Objectives). *Mitigation:* build agent runs full suite after rewire; surfaces non-structural test failures; halt-and-surface if updates exceed integration tests.

**6.5 — `evidence-rows.yaml` rename (master plan §6.3).** This plan-doc commits to rename per AC.OBJX.7. v0.1.9 PR-safety reads `contract-draft.yaml`, not `raw-acs.yaml`; rename is structural-cleanup with zero consumer break. Build agent verifies via grep pre-commit.

**6.6 — Substrate-preservation is semantically partial (master plan §7.6 echo).** New Pydantic models are additive; `BandedAC` unchanged at type level; semantic break is WHAT flows into `contract-draft.yaml acs:`. *Mitigation:* AC.OBJX.7 names transitional shape; build agent verifies v0.1.9 PR-safety smoke tests pass on the new shape (or surfaces — Cycle 3 reframes properly). Adapter-output tests pass because evidence-rows path preserves original.

**6.7 — Anthropic SDK is new dependency for odd-extractor.** Existing odd-extractor imports `loam.cost_governance` but no LLM API. *Mitigation:* lazy-import in `synthesis.py`; pyproject.toml `[project.optional-dependencies]` synthesis extra (or required — builder's call); stub Anthropic clients in tests; no real API calls in CI. Build agent surfaces if SDK install path is non-trivial.

**6.8 — Cycle wall-clock band 5–10 h may be optimistic (master plan §7.9 echo).** 12 ACs + 3 modules + 3 fixtures + 12+1 tests + spec/generate/verify/observability rewires + methodology doc + SDK integration is substantive. *Mitigation:* halt at 10h-no-progress; build agent may serialize internally (pass 1: AC.OBJX.1-5 + .7; pass 2: .6 + .8-12); single-commit still required.

**6.9 — Token-count approximation accuracy.** 4-chars-per-token can drift ±15% on code-heavy content. *Mitigation:* halt-band $0.10–$5.00 has 50× headroom; build agent uses SDK's `messages.count_tokens` if available, else approximation; choice documented.

**6.10 — Decision tree on §self-check failures may need iteration.** AC.OBJX.8's first-cut tree (drop on §1; restate-or-drop on §2; downgrade on §3/4; drop on §5 unless VERIFIED) may need finer-grained handling. *Mitigation:* build agent iterates per fixture-driven evidence; documents in module docstring + audit-log; halt-and-surface only if no tree achieves >70% pass rate on any of 3 fixtures.

---

## §7 — Method-decision register (Cycle-1-specific)

| Decision | Choice | Rationale |
|---|---|---|
| Objective ID format | `O.<domain>.<n>` regex `^O\.[a-z][a-z0-9-]*\.\d+$` | Mirrors v0.1.8's `AC.<domain>.<n>` shape; clean structural difference from symbol-altitude IDs. |
| Constraint ID format | `K.<domain>.<n>` | K for "constraint" (avoids C/O collision). |
| Capability ID format | `C.<domain>.<n>` | C for "capability"; structurally cross-references objectives via `serves: list[O.<...>]`. |
| `Objective.text` minimum length | 20 chars | Filter out implementation-shaped one-liners (route names, function names). |
| `ObjectiveEvidence` shape | Multi-source citation block (`readme_excerpts`, `design_doc_refs`, `test_name_refs`, `survey_line_refs`, `code_pattern_refs`, `repo_sha`, `rationale`) | Multi-source banding requires multi-source evidence shape; existing single-`citations` field insufficient for two-source verification check. |
| Per-band invariants | VERIFIED requires test_name_refs + (readme OR design_doc) + repo_sha; PLAUSIBLE requires at least one source ref; HYPOTHESISED requires rationale | Mirrors `bands.py` `BandedAC` per-band pattern; Pydantic structural defence. |
| Multi-source priority order | README → design docs → tests → user-survey → code patterns | Lean grounding doc §brownfield ODD-RE inputs ordering verbatim. |
| README size cap | 50KB per file (truncate marker on overflow) | Bounds bundle size; majority of READMEs fit; truncation is signal-preserving. |
| Design doc cap | 20 files at 20KB each | Bounds bundle; large repos with deep docs/ trees stay under control. |
| LLM provider default | Anthropic Sonnet (claude-api SKILL conventions) | Cost-balance for outcome-altitude reasoning; matches dispatch model rationale. |
| Prompt caching layout | System (lean grounding doc + banding rule) + User (multi-source bundle structural shape) cached; per-extraction tail varies | claude-api SKILL conventions + master plan cost-management framing. |
| Default per-extraction cost ceiling | $1.00 (= 100 cents) within band $0.10–$5.00 | Master plan §6.1 + §9; build agent may adjust within band on canonical-fixture calibration. |
| Token-count approximation | 4 chars ≈ 1 token; SDK's actual counter if available | Documented approximation; 50× headroom on default ceiling. |
| Adapter-output filename | `evidence-rows.yaml` (renamed from `raw-acs.yaml`) | Master plan §6.3 recommendation; structural-cleanup; legacy `raw-acs.yaml` no longer used. |
| Legacy `acs:` field disposition | PRESERVE in `contract-draft.yaml`; populate with typed `Objective` rows | v0.1.9 PR-safety transitional compatibility per AC.OBJX.7; full drop is Cycle 3's call per master plan §6.2. |
| §self-check enforcement | Programmatic heuristics first; LLM-as-judge for borderline; <10% synthesis budget cap | Lens 4 commitment + Lens 5 `EVAL_DIMENSIONS`; cost-bounded. |
| §self-check decision tree | §1 fail → drop; §2 fail → restate-as-capability or drop; §3/4 fail → downgrade band; §5 fail → drop unless VERIFIED-band evidence | Plan-doc §6.10 first-cut; build agent iterates if fixture evidence demands. |
| Drift-detection halt threshold | >30% §self-check fail rate across all rows | Master plan §3 Cycle 1 + Lens 5 `needs_fresh_start` shape. |
| Survey-file read order | `<repo>/.loam/onboarding-survey.md` → `~/loam-onboarding-survey.md` → `$LOAM_ONBOARDING_SURVEY` | Workspace-local first (project context); home next; env-var override for testing. |
| Survey-shape band cap | Survey-only evidence caps at PLAUSIBLE; cannot promote to VERIFIED via prompt instruction | Master plan §7.7 honest-P-pending-ratification framing. |
| Audit-log event_kinds | New `synthesis_complete` + `altitude_check_complete`; existing schema_version=1 preserved | Additive; no schema-version bump per Cycle 1 substrate-preservation framing. |
| Anthropic SDK install path | `[project.optional-dependencies]` extra under odd-extractor pyproject; build agent decides exact extra name | Standard pattern; lazy-import in `synthesis.py` keeps dependency optional for non-synthesis paths. |
| Test stub strategy | Stub Anthropic client returning fixture-tuned canned responses; no real API calls in CI | Standard pattern; deterministic; CI-safe. |
| Synthesis-failure handling | LLM-pass atomic per call; partial-state is `synthesis_failed` audit-log entry + retry; no D3-style mid-call resume | Atomic-call simplification; mid-call partial-state would require streaming + buffering complexity. |
| Output-schema cross-reference validation | Verify-stage raises `StageError` on dangling `Capability.serves` references | ODD §2.5 strict-mapping at the contract layer; data-integrity floor. |
| Banding rule extension to odd-methodology.md | Append section "v0.2.3 — multi-source banding rule" with V/P/H criteria verbatim | Master plan Cycle 1 quality bar; banding-rule documentation is binding. |
| Plan-doc shape | Mirror v0.2.1 Cycle 1 sub-plan-doc convention | Verified working through Eric path. |

---

## §8 — Provenance trail

- **Master plan:** `docs/rebuild/plans/v0-2-3-master-plan.md` §3 Cycle 1 + §4 + §6.1/§6.3 + §7 + §9 (commit `35155fd`).
- **Lean grounding doc (auto-loaded):** `docs/odd-llm-grounding.lean.md` at `d37c623`. §self-checks + §drift-modes + §altitudes held in working memory.
- **Verbose grounding:** `docs/odd-llm-grounding-derivation.md` at `ffd9c95`.
- **v0.2.2 grounding propagation:** apply `ada74e1`, seal `5eda09d`, §14 backfill `ebca7dc` (dev-sdlc at `da58ad8`).
- **Sub-plan-doc shape precedent:** `docs/rebuild/plans/v0-2-1-cycle-1-eric-onboarding-hardening.md` (manifest schema v3; same §1-§7 + §14 structure).
- **v0.1.8 substrate (load-bearing for repurpose):** Cycle 1 `c1abda1`; Cycle 2 `4865028`; Cycle 3 `6711dd7`; Cycle 4a `67dd302`; Cycle 4b `c648cf9`; Cycle 5 `e4512b9`. Rollup `9b64cd4`.
- **v0.1.6 cost-governance (AC.OBJX.6):** `3f1d237` / `88674cb`. `framework/cost-governance/`.
- **v0.2.1 survey-parser (AC.OBJX.9):** `framework/workspace-bootstrap/src/loam/workspace_bootstrap/survey_parser.py` (sealed `55640b1`).
- **rd-automation extraction artefacts (failure-mode grounding):** `/Users/lukeivers/pos3/workspace/rd-automation/.loam/extractions/rd-automation-5f656bad/` (131 symbol-altitude PLAUSIBLE entries).
- **Eric's survey response (multi-source input precedent):** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/eric-onboarding-response-2026-05-05.md`.
- **Lens 5 swarming patterns:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_swarming_recursive_decomposition.md`.
- **AI-time rubric:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_duration_estimation_rubric.md`.
- **Quality bar (Luke directive 2026-05-04):** master plan §1 verbatim.

---

## §11 — §self-checks audit (per AC.OGP discipline + master plan §11 precedent)

Every "objective" / "AC" / "constraint" / "capability" named or exemplified in this plan-doc was tested against §self-checks 1-5 from `docs/odd-llm-grounding.lean.md`. Compressed audit rows:

| Element | Classified-as | Self-checks 1-5 | Pass |
|---|---|---|---|
| "operators file refund disputes against DoorDash + Uber Eats merchant portals at scale, replacing manual portal clickwork" (§1, §6.3) | objective example | outcome ✓ / survives rewrite (different language/library + same statement) ✓ / builder-method-loose ✓ / observable-from-outside (auditor sees disputes filed) ✓ / user-purpose (replace manual clickwork) ✓ | ✓ |
| "audit trail identifies who initiated each dispute" (§6.3 echo) | objective example | outcome ✓ / survives rewrite (different audit substrate, same statement) ✓ / builder-method-loose ✓ / observable-from-outside (auditor verifies) ✓ / user-purpose (SOC-2 CC6) ✓ | ✓ |
| "CSV upload + validation pipeline" (§1) | capability example | NOT outcome — feature serving the dispute-flow objective; correctly classified at capability altitude | ✓ |
| "production-stake claim" / "SOC-2 audit-trail concern" (§6.3) | constraints surfaced via survey | NOT outcomes — bound the solution space; correctly classified at constraint altitude | ✓ |
| "AC.JSTS.express.get.all_orders.src_routes_exportroutes_js" (§1, §6.3 reference to v0.1.8 output) | implementation | NOT objective — file/lib-named, fails implementation-swap test; correctly named as failure-mode the rebuild fixes | ✓ |
| AC.OBJX.1-12 (§3 — the ACs of THIS plan-doc) | implementation contracts of the loam tool | NOT objectives at the user-altitude — these are tool-internal implementation contracts that ladder up to the tool's user-objective ("user reads outcome-altitude rows, not symbol-altitude rows"); correctly classified at the tool-implementation altitude | ✓ |
| "Multi-source objective synthesis" (Cycle 1 theme) | capability of the loam tool itself | tool-internal capability serving the user-objective at v0.2.5 ("what should I build next?"); correctly classified at the tool-altitude | ✓ |
| "Outcome altitude" (used throughout as descriptive prose) | design-intent prose | NOT objective — correctly used as descriptive prose, not labelled as objective | ✓ |
| "objective_id" / "constraint_id" / "capability_id" regexes (§3) | structural format constraints | NOT objectives — bound the implementation; correctly classified as structural defence | ✓ |

**Drift-mode check** (each recognised + avoided in this plan-doc):

- **Symbol-as-AC** ✓ avoided (rd-automation 131-row example named explicitly as failure mode the rebuild fixes; AC.OBJX.7 routes adapter symbol output to evidence-rows.yaml, NOT primary acs:).
- **Function-name-as-AC** ✓ avoided (no function-name labels labelled as objectives).
- **Feature-as-objective** ✓ avoided (CSV upload pipeline named as capability throughout).
- **Test-name-as-implementation** ✓ avoided (AC.OBJX.5 banding rule treats test-names asserting outcomes as VERIFIED-class evidence; tests asserting calls remain implementation-shaped per §self-check 4).
- **Gap-as-objective** ✓ avoided (no gap-analysis output labelled as objective; gap-analysis is v0.2.4 surface).
- **Constraint-as-objective** ✓ avoided (production-stake + SOC-2 explicitly named as constraints in §6.3; the audit-trail-identifies-who narrative is the objective).
- **Implementation-detail-as-constraint** ✓ avoided (no RSA-OAEP-shape details labelled as constraints — only mentioned in §6.3 as Eric's compliance narrative which the synthesis layer must lift to constraint altitude).

§self-checks pass on every "objective" / "AC" / "constraint" / "capability" named in this plan-doc. ✓

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Cycle-1 method decisions at §7. Master-plan method decisions at master plan §9 (`docs/rebuild/plans/v0-2-3-master-plan.md`).

### Commit SHAs

- Amendment commit: `1e2003760a7ab22a22e4cf20deb550dff1e37cc3` —
  `chore(amend): v0-2-3-cycle-1-multi-source-objective-synthesis manifest+apply — dev-sdlc BASELINE+sidecar bump to 404f4d3`
- Seal commit: `9b9f87c8efb0503003ff78e3a8f296cdb1ff8b2a` —
  `chore(seals): v0-2-3-cycle-1-multi-source-objective-synthesis — dev-sdlc at 1e20037`
