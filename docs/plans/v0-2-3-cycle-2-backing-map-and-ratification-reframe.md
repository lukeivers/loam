# v0.2.3 Cycle 2 — Backing-implementation map + ratification reframe

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-04 (Sonnet, plan-author dispatch).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Predecessor:** v0.2.3 Cycle 1 SHIPPED — apply `1e20037`, seal `9b9f87c`, §14 backfill `66de327`, master plan §9 backfill `914809d`. Master plan committed at `35155fd`. Lean grounding doc `d37c623`.

**BASELINE (pre-build tip):** to be set to the source-edit commit when the build commit lands.

**Parent plan:** `docs/plans/v0-2-3-master-plan.md` §3 Cycle 2 + §4 Cycle 2 dispatch brief + §6 + §9 method-decision register.

**Always-load grounding:** `docs/odd-llm-grounding.lean.md` (auto-loaded structurally per v0.2.2 AC.OGP.1/AC.OGP.2). The §self-checks (§8 of that doc) were applied to every "objective" / "AC" / "constraint" / "capability" named in this plan-doc; §11 below records the audit.

**Quality bar (Luke directive 2026-05-04, carried verbatim from master plan):**

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

Cycle 2 makes Cycle 1's output actionable. Backing-implementation map fully implemented (not stub). Ratification flow fully reframed at objective altitude (not partial). PLAUSIBLE → VERIFIED rule explicit (backing-evidence required + owner explicit-Y). Substrate preservation honored via Pydantic extension, not replacement. Migration path explicit. **No partial features.** Self-checks pass on every example AC named in this plan-doc per §11.

---

## §1 — Outcome shape

Cycle 2 ships two tightly-coupled mechanisms above Cycle 1's substrate:

1. **Backing-implementation map.** Bidirectional structure linking each `Objective` to `evidence-rows.yaml` rows that back it (path + symbol + line + signal-strength). Populated post-synthesis via heuristic pre-filter + LLM-pass classifier on narrowed candidates. Persisted at `<workspace>/.loam/extractions/<repo-id>/backing-map.yaml`. Surfaces orphan evidence rows — forward-compat carrier for v0.2.4 gap-analysis + v0.2.5 negative-alignment.

2. **Ratification flow reframed at objective altitude.** v0.1.8's `ratify.py` operated on `BandedAC` (symbol-altitude). Cycle 2 extends the substrate to operate on `Objective` (and `Constraint` + `Capability`) rows: PLAUSIBLE → VERIFIED requires (a) explicit owner Y per Decision I AND (b) at least one STRONG-confidence backing-map row OR test-asserts-outcome evidence-row pinned to `repo_sha`. `RatificationAction` + `RatificationState` extend (do NOT replace); new `RatificationStateV2` carries altitude-tagged records alongside v1 shape for a one-release migration window.

**Fence reality.** `plugins/dev-sdlc/odd-extractor/` exists. Cycle 2 adds `backing_map.py`, extends `spec.py` (new models), extends `ratify.py` (parallel factories + apply path; v1 preserved), extends `ratification_state.py` (schema_version=2; migrating loader), extends `generate.py` (post-synthesis populate call), extends `verify.py` (per-objective backing counts + orphan section), extends `cli.py` (objective-altitude ratify routing).

**Release-note promise.** After Cycle 1's synthesis produces banded `Objective` rows, Cycle 2's `populate_backing_map(...)` enriches the contract with code-path evidence. User runs `loam odd-extract ratify <repo-id>` and sees objective-altitude prompts one-at-a-time via PM batch API. P→V requires STRONG backing OR test-asserts-outcome row pinned to repo_sha; absent either, returns `RatificationRefusedError` naming missing evidence. Audit-log captures every action with backing-map evidence cited inline.

**Discipline.** v0.1.6 cost-governance wraps the backing-map LLM-pass per AC.BACKMAP.7: dry-run estimate pre-call; default ceiling $0.50 (band $0.05–$2.00 per master plan §6.1 + §9); halt-and-surface if outside band. Heuristic pre-filter narrows candidates so LLM-pass operates on a small fraction of the cross-product.

---

## §2 — Lens checks (per CLAUDE.md design lenses)

**Lens 1 — Claude-leverage-first.** Reuses Cycle 1's Anthropic SDK integration (prompt caching + cost envelope); Cycle 1's `Objective`/`Constraint`/`Capability` Pydantic models (referential integrity via `model_validator`); v0.1.8's `ratify.py` factory + `apply_ratification_action` shape (parallel paths added; v1 preserved); `ratification_state.py` schema-versioned loader (v1→v2 auto-migration on read); `framework/per-project-pm/`'s `PMRuntime` (zero PM-side schema edits — provenance string carries altitude tag); `observability.py` audit-log; Lens 5 `EVAL_DIMENSIONS` per backing-map classifier (file-path-relevance / symbol-name-relevance / domain-match / outcome-shape-match scored concurrently). Cycle 2 introduces zero new dependencies beyond what Cycle 1 wired.

**Lens 2 — Harness + primary-persona value.** Primary-persona test ✓ — Eric ratifies ~10–30 objectives one-at-a-time with backing evidence cited inline ("Promote O.dispute-flow.1 to VERIFIED? Backing: src/routes/disputeRoutes.js:42 + tests/dispute-flow.spec.ts asserting 'operator files dispute' at sha 2d9e705"). Harness test ✓ — backing-map + objective-altitude ratification are reusable layers; v0.2.4 completeness interview composes on backing-map orphan list; v0.2.5 negative-alignment uses backing-map + LLM-as-judge.

**Lens 3 — ODD authoring.** Outcome + named ACs (§3) + halt triggers (§5 + §6) + acceptance smoke (§4). Method-loose per builder's call within constraints: bidirectional map shape; heuristic pre-filter then LLM-pass classifier; cost band $0.05–$2.00; orphan-row carrier shape; v1→v2 migration path; backing-evidence requirement at P→V.

**Lens 4 — Prompt scope ↔ confidence.** HIGH confidence for shape (master plan names all 15 ACs; Cycle 1 shipped + verified; v0.1.8 ratify substrate verified-working). MEDIUM for backing-map population approach — commitments: heuristic pre-filter (domain-keyword overlap + `kind=test` weighting + per-language conventions; top-K=8) → LLM-pass classifier → cost-cap $0.50 default → halt at >200 candidate pairs after narrowing. MEDIUM for v1→v2 migration — `RatificationStateV2` structurally backward-compatible; atomic backup at `ratification-state.yaml.v1.bak` before v2 write; PM-side schema preserved (provenance string carries altitude tag). MEDIUM-LOW for "test asserts outcome" heuristic — programmatic regex on assertion-text + verb list ("should"/"expects"/"delivers"/"creates"/"rejects"/"completes") + domain-noun overlap; borderline cases stay PLAUSIBLE with rationale logged; explicit owner Y always required regardless. HIGH for substrate preservation (v1 paths preserved unchanged; Cycle 2 adds parallel paths).

**Lens 5 — Swarming.** Single-component fence under `plugins/dev-sdlc/odd-extractor/`. Per-concern module decomposition (`backing_map.py` + `spec.py` extension + `ratify.py` parallel paths + `ratification_state.py` schema-version extension) matches master plan's named-mechanism naming. `max_planner_depth: 1` — sub-planning is coordination overhead with no tighter AC. Model: Sonnet default; no Opus tier required (LLM-pass is structurally simpler than Cycle 1 — scoring pairs, not generating prose).

---

## §3 — AC enumeration (locked, 15 ACs across two families)

Each AC has at least one explicit pytest. ODD §2.5 — every line of code, branch, test maps to a named AC. AC.BACKMAP.1 → AC.BACKMAP.7 + AC.OBJRAT.1 → AC.OBJRAT.8 inherited from master plan §3 Cycle 2 with method tightening per §7. §self-checks 1-5 ran on every example outcome / capability / constraint named in this plan-doc; §11 records the audit.

### AC.BACKMAP.* — Backing-implementation map (7 ACs)

- **AC.BACKMAP.1 — Pydantic models in `spec.py`.** `EvidenceRowRef`: `evidence_row_id` (composite `kind:path:line` mirroring `BandedAC.ac_id`) + `kind` (Literal route/callback/model/test/pattern/other) + `path` + `line_range: tuple[int,int] | None` + `symbol_name` + `language` (Literal jsts/ruby/python/other) + `confidence: Literal["STRONG","WEAK"]` (signal-strength, orthogonal to objective banding). `BackingMap`: `extraction_id` + `entries: list[BackingMapEntry]` + `orphan_rows: list[OrphanRow]` + `created_at` + `model_id` + `cost_actual_cents` + `total_evidence_rows` + `unmatched_objective_ids`. `BackingMapEntry`: `objective_id` (matches `^O\.[a-z][a-z0-9-]*\.\d+$`) + `evidence_rows: list[EvidenceRowRef]` (may be empty for HYPOTHESISED) + `match_rationale`. `OrphanRow`: same as `EvidenceRowRef` + `reason: Literal["no-objective-match","weak-signal-only","anti-feature-candidate"]` (extensible carrier per AC.BACKMAP.5). `model_validator` enforces id regex + non-empty refs. Test: `test_AC_BACKMAP_1_models.py` — construction; ValidationError on malformed IDs; round-trip.

- **AC.BACKMAP.2 — `populate_backing_map` heuristic pre-filter + LLM-pass classifier.** New module `backing_map.py`. Function `populate_backing_map(objectives, evidence_rows, *, anthropic_client, repo_sha, budget_envelope, extraction_dir, timestamp) -> BackingMap`. Step 1 pre-filter: per objective, score by (a) `objective.domain` substring match vs `path`/`symbol_name`, (b) `kind=test` weighted by assertion-verb regex + domain noun overlap, (c) per-language conventions (Express paths; Ruby controllers; Playwright spec headings). Top-K=8 candidates per objective. Step 2 classifier: single batched LLM call scoring narrowed pairs on STRONG/WEAK/NONE per `EVAL_DIMENSIONS` (4 axes per §2 Lens 1); structured-JSON output. Step 3 orphan: rows with no STRONG match → `no-objective-match`; WEAK-only → `weak-signal-only`. Cost-band $0.05–$2.00; default $0.50; halt outside band. Halt-trigger: >200 pairs after narrowing (pre-filter broken; no LLM fired). Test: `test_AC_BACKMAP_2_population.py` — stub Anthropic with canned scores; assert narrowing + invocation count + STRONG/WEAK/NONE + orphan + cost.

- **AC.BACKMAP.3 — Persistence at `<workspace>/.loam/extractions/<repo-id>/backing-map.yaml`.** Atomic write tmp+rename (mirrors `ratification_state.py`). Schema: `schema_version: 1` + full `BackingMap.model_dump`. Round-trips Pydantic; D5-survives `/clear`. Generate-stage post-`synthesis.yaml`: calls `populate_backing_map(...)`, writes `backing-map.yaml`, adds `state.artefacts["backing_map"]`. Test: `test_AC_BACKMAP_3_persistence.py` — populate→save→load round-trip; schema_version present; state.yaml artefact key.

- **AC.BACKMAP.4 — Coverage report in `contract-draft.md`.** Verify-stage renders "Backing-implementation map" section: per objective row → `objective_id` + band + STRONG count + WEAK count + total + first-3 path:line preview. Orphan section: count + first-10 paths with `reason` annotation. Empty `evidence_rows: []` allowed for HYPOTHESISED. Test: `test_AC_BACKMAP_4_coverage_report.py` — synthetic backing-map; assert sections + counts + previews + HYPOTHESISED empty-list handling.

- **AC.BACKMAP.5 — Forward-compat for v0.2.4 gap-analysis + v0.2.5 negative-alignment.** `OrphanRow.reason` enum extensible (v0.2.5 may add `negative-alignment-detected`). `BackingMap.unmatched_objective_ids` lists non-HYPOTHESISED objectives with empty backing — v0.2.4 gap-analysis consumes. Test: `test_AC_BACKMAP_5_forward_compat.py` — three enum values accepted; `unmatched_objective_ids` populated for non-HYPOTHESISED + empty path.

- **AC.BACKMAP.6 — Component tests against 3 synthetic fixtures.** `tests/fixtures/backing-map/`: (1) `tight-1-to-1/` — 3 objectives + 5 evidence rows clean per-objective mapping; (2) `loose-multi-row/` — 2 objectives + 12 evidence rows multi-row + 4 orphans; (3) `no-evidence-hypothesised/` — 4 mixed-band + 6 mostly-orphan rows. Each exercises full populate→persist→render. Test: `test_AC_BACKMAP_6_synthetic_shapes.py` — 3 sub-tests; stub Anthropic with fixture-tuned scores; per-fixture distribution within tolerance.

- **AC.BACKMAP.7 — Audit-log per population.** New event_kind `backing_map_populated`: `objective_count` + `evidence_row_count` + `llm_pass_token_count` + `llm_pass_cost_cents` + `strong_match_count` + `weak_match_count` + `orphan_count` + `unmatched_objective_count` + `model_id`. Structured payload via existing `estimate` field (no schema-version bump). Test: `test_AC_BACKMAP_7_audit_log.py` — event_kind present with fields; round-trip.

### AC.OBJRAT.* — Objective-altitude ratification (8 ACs)

- **AC.OBJRAT.1 — Objective-altitude factory functions + apply path.** New factories in `ratify.py`: `promote_objective(target_id, *, from_band, to_band, explicit_yes, backing_evidence_cited) -> ObjectiveRatificationAction`; `demote_objective` / `edit_objective` / `reject_objective`. Parallel set for constraints + capabilities. New typed primitive `ObjectiveRatificationAction` (frozen dataclass mirroring v0.1.8 `RatificationAction`): `kind` + `target_id` + `altitude: Literal["objective","constraint","capability"]` + `from_band` + `to_band` + `edit_text` + `reject_reason` + `explicit_yes` + `backing_evidence_cited: list[str] | None`. New apply path `apply_objective_ratification_action(action, *, draft_rows, backing_map, workspace_root, repo_id, pm_audit_path, timestamp) -> updated_rows`. v0.1.8 `RatificationAction` + `apply_ratification_action` (BandedAC paths) preserved unchanged. Test: `test_AC_OBJRAT_1_factories_and_apply.py` — per-altitude construction; round-trip; refused on missing target_id; v1 path still callable.

- **AC.OBJRAT.2 — PLAUSIBLE → VERIFIED on objective requires backing-evidence + explicit_yes.** `promote_objective(from_band=PLAUSIBLE, to_band=VERIFIED, ...)` factory enforces (a) `explicit_yes=True` (Decision I; mirrors v0.1.8 `promote()`); (b) `backing_evidence_cited` non-empty AND each cited row resolves to a STRONG-confidence backing-map entry OR a `kind="test"` evidence-row pinned to `repo_sha` AND passing programmatic test-as-outcome heuristic. Apply-path defense-in-depth re-checks both invariants against supplied `backing_map`; refuses via `RatificationRefusedError` naming missing/insufficient/stale evidence. Auto-verify hint: persona MAY recommend Y when test-row passes heuristic, but explicit_yes stays user-driven (no auto-flip). Test: `test_AC_OBJRAT_2_promotion_gate.py` — refused without explicit_yes; refused with empty backing; refused with stale-cited row; accepted with STRONG row; accepted with test-row passing heuristic.

- **AC.OBJRAT.3 — V → P demotion: single explicit action; no backing-evidence requirement.** `demote_objective(from_band=VERIFIED, to_band=PLAUSIBLE, ...)` accepts demotions without `explicit_yes` and without `backing_evidence_cited`. Asymmetric per Decision I (only promotion to V is gated). Demotion records prior backing-citations in audit-log (informational; v→p signal for v0.2.4 gap-analysis). Test: `test_AC_OBJRAT_3_demotion.py` — V→P / P→H / V→H accepted; same-band + upward refused; backing carried in audit-log.

- **AC.OBJRAT.4 — Audit-log per ratification action.** 12 new event_kinds: `ratification_<altitude>_<action>` for altitude ∈ {objective, constraint, capability} × action ∈ {promote, demote, edit, reject}. Each entry: `target_id` + `altitude` + `band_before` + `band_after` + `actor` + `timestamp` + `reason` + `backing_evidence_cited` (null on edit/reject) + `pm_audit_path` (cross-ref to PM `record_response`). Existing `estimate` field carries structured payload (no schema-version bump). Test: `test_AC_OBJRAT_4_audit_log.py` — full cycle (promote + demote + edit + reject) on each altitude; all 12 kinds present; round-trip.

- **AC.OBJRAT.5 — Constraint + capability ratification (parallel altitudes).** Constraint factories: same shape; NO backing-map required (constraints bound solution-space, don't deliver) — `backing_evidence_cited` not required for promotion; explicit_yes still required at PLAUSIBLE→VERIFIED per Decision I. Capability factories: apply path validates `serves` linkage — refuses via `RatificationRefusedError` if any served objective references unknown objective_id OR is HYPOTHESISED-band (anti-pattern: capability serving unverified outcome cannot itself be verified). Test: `test_AC_OBJRAT_5_constraint_capability.py` — constraint promotion with explicit_yes only; capability blocks on dangling `serves`; capability blocks on H-band served objective.

- **AC.OBJRAT.6 — Substrate preservation: extend, do NOT replace.** `RatificationStateV2` extends `RatificationState` additively: `altitude_index: dict[str, str]` mapping target_id to altitude (`"banded_ac"` for legacy; `"objective"`/`"constraint"`/`"capability"` for new); `pending_targets: list[PendingTarget]` parallel to legacy `pending_acs`. Schema migration on read: `_RATIFICATION_STATE_SCHEMA_VERSION = 2`; loader detects v1 (schema_version=1) and migrates — every `pending_acs` entry gets `altitude="banded_ac"`; `pending_targets` populated; v1 backup written at `ratification-state.yaml.v1.bak`; v2 written atomically. Backward-compat read accessors return v1-shaped data for `altitude="banded_ac"`. Test: `test_AC_OBJRAT_6_state_migration.py` — load v1 → v2 with `altitude_index` populated + backup; fresh-write v2 → no backup; v1 BandedAC apply path still calls load/save cleanly.

- **AC.OBJRAT.7 — PM-side altitude-tagging via provenance string (additive).** `enqueue_ratification_batch` extended to enqueue altitude-tagged questions. Each PM `enqueue_decision` gets `provenance=f"odd-extract:{extraction_id}:{altitude}:{target_id}"` (extends Cycle 1 shape additively). PM-side `decision-queue.yaml` schema UNCHANGED — provenance is free-form from PM's perspective; zero PM-side edits. Persona-side response router parses provenance, identifies altitude, dispatches to correct factory. Test: `test_AC_OBJRAT_7_pm_provenance.py` — assert altitude-tagged provenance enqueued; response router dispatches correctly; PM-side schema unchanged.

- **AC.OBJRAT.8 — Component tests against 3 synthetic ratification fixtures.** `tests/fixtures/objective-ratification/`: (1) `all-plausible/` — 5 P-band + populated backing-map; (2) `mixed-bands/` — 3 V + 4 P + 2 H + mixed backing; (3) `edge-cases/` — P→V-without-backing-blocked + capability-with-H-served-objective. Each exercises full batch (enqueue → surface → parse → apply → audit) with stub PM + stub Anthropic. Test: `test_AC_OBJRAT_8_synthetic_batches.py` — 3 sub-tests; per-fixture state-progression + audit-log assertions.

---

## §4 — Component & file layout

**PRIMARY:** `plugins/dev-sdlc/odd-extractor/`. **TERTIARY:** `docs/plans/` (plan-doc paper trail).

**Existing paths (extend in-place; sealed-content unchanged):**

- `src/loam_odd_extractor/spec.py` — add `BackingMap` + `BackingMapEntry` + `EvidenceRowRef` + `OrphanRow` + `ObjectiveRatificationAction`. Cycle 1 + v0.1.8 models unchanged.
- `src/loam_odd_extractor/ratify.py` — add `promote_objective`/`demote_objective`/`edit_objective`/`reject_objective` (parallel for constraint + capability) + `apply_objective_ratification_action` + altitude-tagged provenance in `enqueue_ratification_batch`. v1 BandedAC paths preserved unchanged.
- `src/loam_odd_extractor/ratification_state.py` — add `RatificationStateV2`; bump `_RATIFICATION_STATE_SCHEMA_VERSION = 2`; auto-migrate on read. v1 dataclass preserved.
- `src/loam_odd_extractor/generate.py` — additive: post-`synthesis.yaml`, call `populate_backing_map(...)`; persist `backing-map.yaml`; `state.artefacts["backing_map"]`.
- `src/loam_odd_extractor/verify.py` — additive: render "Backing-implementation map" + orphan section per AC.BACKMAP.4.
- `src/loam_odd_extractor/observability.py` — 13 new event_kinds.
- `src/loam_odd_extractor/cli.py` — additive: ratify routes to objective/constraint/capability altitude when contract has Cycle 1 typed lists; v1 path remains for legacy contracts.
- `src/loam_odd_extractor/__init__.py` — additive exports.

**New paths (this cycle):**

- Source: `src/loam_odd_extractor/backing_map.py` — `populate_backing_map(...)` orchestrator; LLM-pass system prompt + scoring schema + cost-envelope wiring.
- Tests: `tests/test_AC_BACKMAP_{1..7}_*.py` (7) + `tests/test_AC_OBJRAT_{1..8}_*.py` (8) + `tests/test_objective_ratification_integration.py` (full e2e on `all-plausible` fixture).
- Fixtures: `tests/fixtures/backing-map/{tight-1-to-1,loose-multi-row,no-evidence-hypothesised}/` + `tests/fixtures/objective-ratification/{all-plausible,mixed-bands,edge-cases}/`.

**Smoke dimensions (per master plan §3 Cycle 2):**

- **D1 cold-state** ✓ — synthetic banded contract → populate_backing_map → ratify → audit log observable. Verified by integration test + per-AC tests.
- **D2 steady-state** ✓ — re-ratify idempotent; re-populate skipped when `backing-map.yaml` exists with same `total_evidence_rows` + `objective_count`.
- **D5 cross-session** ✓ — partial ratification resumable; backing-map + state v2 round-trip; v1→v2 migration survives session boundary.
- **D6 telemetry-floor** ✓ — per AC.BACKMAP.7 + AC.OBJRAT.4.
- **D3 restart** inherited from PM batch API + state.yaml; mid-ratification kill -TERM resumes.
- **D4 reboot** n/a structurally (invoked-on-demand, not daemon).

---

## §5 — Build dispatch brief (READY FOR DISPATCH after this plan-doc seals)

```
# v0.2.3 Cycle 2 BUILD dispatch — Backing-implementation map + ratification reframe

Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`. NOT pos3.

LOAD `docs/odd-llm-grounding.lean.md` FIRST. Critical for v0.2.3 — backing-map LLM-pass classifier + ratification gate reasoning must NOT drift to implementation-shape.

Authority: build the 7 AC.BACKMAP.* + 8 AC.OBJRAT.* families (15 ACs) per sub-plan-doc §3. Single-component fence on plugins/dev-sdlc/odd-extractor/. Tertiary admission: docs/plans/.

Principles to apply at turn-start:
  AUTONOMY / F2 RUTHLESS FEEDBACK / LOCKED-DESIGN-NOT-LICENSE / PROMISES > IN-MOMENT JUDGMENT / ODD §2.5 / OUTPUT-TO-DISK / WD-IN-DISPATCHES / NO --amend / NO push / NO FALSE FAULT / PRINCIPLE-APPLICATION DISCIPLINE / TEST-AGAINST-OPERATIONAL-OBJECTIVE-BEFORE-ESCALATING.

Quality bar (Luke directive 2026-05-04, carried verbatim): every AC ships complete + tested. Backing-map fully implemented (not stub). Ratification flow fully reframed at objective altitude (not partial). PLAUSIBLE → VERIFIED rule explicit (backing-evidence required + owner explicit-Y). Substrate preservation honored via Pydantic extension. Migration path explicit. No partial features.

Source pointers (READ FIRST):
  - sub-plan-doc (THIS file) at docs/plans/v0-2-3-cycle-2-backing-map-and-ratification-reframe.md
  - master plan §3 Cycle 2 + §4 + §6 + §9 at docs/plans/v0-2-3-master-plan.md (commit 35155fd)
  - Cycle 1 sub-plan-doc at docs/plans/v0-2-3-cycle-1-multi-source-objective-synthesis.md (sealed 9b9f87c; §14 backfill 66de327)
  - Lean grounding doc at docs/odd-llm-grounding.lean.md (commit d37c623)
  - v0.1.8 ratify substrate: ratify.py + ratification_state.py + tests/test_AC_BANDS_4..7
  - v0.1.7 PM batch API at framework/per-project-pm/src/loam/per_project_pm/runtime.py (122a7c8)
  - v0.1.6 cost-governance at framework/cost-governance/src/loam/cost_governance/
  - rd-automation extraction artefact at /Users/lukeivers/pos3/workspace/rd-automation/.loam/extractions/rd-automation-5f656bad/ (concrete shape of evidence-rows.yaml input)
  - claude-api SKILL conventions for Anthropic SDK + prompt caching

Fence + ACs + smoke + AI-time + out-of-scope: per sub-plan-doc §3 + §4.

Halt triggers — enumerated at sub-plan-doc §6 + below; halt-and-surface, do NOT silently work around:
  - WD drifts to pos3.
  - Backing-map data structure can't be added without breaking v0.1.8 contract-draft.yaml schema.
  - Backing-map LLM-pass cost calibration on canonical jsts-playwright-app fixture lands outside $0.05–$2.00 band.
  - Heuristic pre-filter produces > 200 candidate pairs after narrowing (pre-filter broken).
  - Ratification reframe surfaces tighter coupling than master plan anticipated (e.g., requires PM-side schema extension beyond provenance string).
  - v1 → v2 ratification-state migration produces data loss on any v0.1.8 fixture.
  - Promotion-rule edge case ("test asserts outcome" vs "test asserts implementation") cannot resolve via programmatic heuristic on any 3 synthetic test fixtures.
  - ODD §2.5 violations in surrounding code OR Cycle 1 substrate.
  - Cycle wall-clock >6 h with no progress.
  - >3 escalations needed.

Bookkeeping:
  - pos-amend apply (NOT --amend); manifest schema v3.
  - Single semantic commit on apply: feat(odd-extractor): v0.2.3 Cycle 2 — backing-implementation map + ratification reframe.
  - Short-form seal commit per AC.DPS2 schema-v3.
  - §14 backfill separate post-seal commit per AC.D-sa.7.
  - Master plan §9 per-cycle SHA backfill row updates with apply + seal SHAs.

Model rationale: Sonnet default (no Opus tier required at this depth; LLM-pass design simpler than Cycle 1 — scoring pairs, not generating prose).
```

---

## §6 — Honest doubts (F2 RF on this decomposition)

**6.1 — Backing-map heuristic pre-filter may misclassify domain matches.** rd-automation has domain-keyword overlap across "dispute"/"order"/"all-orders"/"summary" routes not structurally separable by path-component alone. *Mitigation:* top-K=8 (generous); LLM-pass corrects ambiguity; >200-pair halt surfaces broken pre-filter; build agent iterates if rd-automation-shaped fixtures stress-test.

**6.2 — LLM-pass classifier cost.** 131 evidence rows × ~20 objectives = 2620 pre-filter cross-product; narrow to K=8 → ~160 pairs; single batched call ~5K input / ~2K output at Sonnet pricing → ~$0.04. Comfortably under $0.50 default. *Mitigation:* AC.BACKMAP.7 audit-log + AC.BACKMAP.2 band halt; build agent calibrates on canonical jsts-playwright-app.

**6.3 — v1 → v2 ratification-state migration risk.** v0.1.8 fixtures may have edge-case state files (`in_flight_action` mid-flight at migration time). *Mitigation:* atomic `.v1.bak` write before v2; read-tolerant loader; halt on data-loss; build agent verifies migration on every v0.1.8 ratification fixture pre-seal.

**6.4 — "Test asserts outcome" vs "test asserts implementation" heuristic.** `test_route_returns_200` is implementation-shape; `test_operator_files_dispute` is outcome-shape. *Mitigation:* assertion-text + verb-list regex + domain-noun overlap; borderline → PLAUSIBLE with rationale; halt if no heuristic achieves >70% on 3 synthetic test fixtures.

**6.5 — Capability `serves` validator may be over-strict.** Blocking capability promotion when any served objective is HYPOTHESISED may be too tight. *Mitigation:* user can demote→promote-after-objective-verifies; build agent surfaces if fixture evidence shows unworkable.

**6.6 — Cycle wall-clock band 3–6 h may be optimistic.** 15 ACs + new module + 6 module extensions + 6 fixtures + 16 tests + state-migration is substantive. *Mitigation:* halt at 6h-no-progress; build agent may serialize internally (pass 1: AC.BACKMAP.* + spec; pass 2: AC.OBJRAT.* + state-migration); single-commit still required.

**6.7 — Cumulative LLM-pass cost on rd-automation-scale.** Three passes per extraction (Cycle 1 synthesis + altitude-validator + Cycle 2 backing-map). Total cumulative band $1.50–$7.00 still under v0.1.6 production-stake daily budget. *Mitigation:* halt if cumulative outside band on canonical fixture.

**6.8 — Audit-log event_kind explosion (13 new kinds).** Maintenance concern; collapsing to one `ratification_action` with payload-tagged altitude/action would lose grep-ability. *Mitigation:* keep explosion (structurally honest); build agent may revisit if test-maintenance burden surfaces.

**6.9 — Promotion-gate stale-citation edge.** If user re-runs synthesis between backing-map population + ratification, cited row may be stale. *Mitigation:* AC.OBJRAT.2 apply-path defense-in-depth re-resolves against current `backing_map.yaml`; refuses naming the stale row.

---

## §7 — Method-decision register (Cycle-2-specific)

| Decision | Choice | Rationale |
|---|---|---|
| Backing-map placement | New `backing_map.py` module; persisted at `<workspace>/.loam/extractions/<repo-id>/backing-map.yaml` | Master plan §9; clean module seam; D5 survives. |
| `EvidenceRowRef.evidence_row_id` shape | Composite `kind:path:line` (mirrors `BandedAC.ac_id`) | Stable across re-extractions; round-trips cleanly. |
| `EvidenceRowRef.confidence` | Literal["STRONG","WEAK"] (orthogonal to V/P/H) | Signal-strength structurally distinct from objective confidence. |
| Backing-map population | Heuristic pre-filter + LLM-pass classifier hybrid (K=8) | Master plan §9 + §6.1; cost-band halt; LLM corrects ambiguity. |
| Pre-filter signals | (a) domain-keyword substring on path+symbol; (b) kind=test weighted by assertion-verb + domain-noun; (c) per-language conventions | Cheap; structural; fails-soft. |
| Default backing-map cost ceiling | $0.50 within $0.05–$2.00 band | Master plan §6.1 + §9; build agent calibrates on canonical fixture. |
| Halt on pre-filter overflow | >200 candidate pairs after narrowing → halt (no LLM fired) | Pre-filter broken; cost-bound enforcement primary. |
| Orphan-row reason enum | Literal["no-objective-match","weak-signal-only","anti-feature-candidate"] | Forward-compat for v0.2.4/v0.2.5; extensible. |
| `unmatched_objective_ids` semantic | Non-HYPOTHESISED objectives with empty backing | Authoring gap signal for v0.2.4. |
| Ratification factory naming | `promote_objective`/etc. (parallel for constraint + capability) | Mirrors v0.1.8 shape; altitude-suffixed. |
| Apply-path naming | `apply_objective_ratification_action` | Parallel to v0.1.8 `apply_ratification_action`; v1 preserved. |
| `ObjectiveRatificationAction` shape | Frozen dataclass (mirrors v0.1.8); altitude-tagged + backing_evidence_cited | Same pattern as v0.1.8; explicit altitude disambiguates. |
| P→V on objective rule | Requires explicit_yes=True AND backing_evidence_cited non-empty AND each cited row resolves STRONG-or-test-asserting-outcome | Decision I + master plan §3 Cycle 2 + §6.4. |
| Test-asserts-outcome heuristic | Regex on assertion-text + verb list ("should"/"expects"/"delivers"/"creates"/"rejects"/"completes") + domain-noun overlap | First-cut; build iterates; halt if <70% on test fixtures. |
| Auto-verify recommendation vs auto-flip | Persona MAY recommend Y; explicit_yes stays user-driven | Decision I preserved; no silent promotion. |
| V→P demotion | No explicit_yes; no backing required; prior backing carried in audit-log | Asymmetric per Decision I; v→p audit signal for v0.2.4. |
| Capability `serves` validator | Refuses promotion if any served objective is HYPOTHESISED OR references unknown objective_id | Anti-pattern: capability cannot be verified above what it serves. |
| Constraint promotion | explicit_yes gate; no backing required | Constraints bound, don't deliver. |
| `RatificationStateV2` schema | Add altitude_index + pending_targets; preserve v1 fields | Backward-compat read; transparent migration. |
| v1→v2 migration trigger | On read of v1; atomic .v1.bak + v2 write | One-release migration window. |
| PM-side schema | Unchanged — provenance string carries altitude tag verbatim | Zero PM-side edits. |
| Provenance shape | `f"odd-extract:{extraction_id}:{altitude}:{target_id}"` | Additive to Cycle 1 shape. |
| Audit-log event_kind explosion | 13 new kinds (1 backing-map + 12 ratification altitude×action) | Grep-ability over collapsed payload. |
| Idempotent re-population | Skip when `backing-map.yaml` exists with same total_evidence_rows + objective_count | D2 smoke dimension; cost-conscious. |
| Fixture coverage | 3 backing-map + 3 ratification fixtures | Covers all AC paths + edge cases. |
| Test granularity | 1-per-AC (15) + 1 integration | Mirrors Cycle 1 + v0.1.8 + v0.2.0 + v0.2.1 conventions. |

---

## §8 — Provenance trail

- **Master plan:** `docs/plans/v0-2-3-master-plan.md` §3 Cycle 2 + §4 + §6 + §9 (`35155fd`).
- **Cycle 1 sub-plan-doc:** `docs/plans/v0-2-3-cycle-1-multi-source-objective-synthesis.md`. Sealed `9b9f87c`; §14 `66de327`; master §9 `914809d`.
- **Lean grounding (auto-loaded):** `docs/odd-llm-grounding.lean.md` at `d37c623`.
- **v0.1.8 ratify substrate:** `4865028`. `ratify.py` + `ratification_state.py` + `test_AC_BANDS_4..7`.
- **v0.1.7 PM batch API:** Cycle 4 `122a7c8`. `framework/per-project-pm/`.
- **v0.1.6 cost-governance:** `3f1d237` / `88674cb`.
- **rd-automation extraction artefact:** `/Users/lukeivers/pos3/workspace/rd-automation/.loam/extractions/rd-automation-5f656bad/raw-acs.yaml` (131 rows; backing-map fixture reference).
- **Lens 5 swarming + AI-time rubric:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_{swarming_recursive_decomposition,duration_estimation_rubric}.md`.
- **Quality bar:** Luke directive 2026-05-04 (master plan §1 verbatim).

---

## §11 — §self-checks audit (per AC.OGP discipline + master plan §11 precedent)

Every "objective" / "AC" / "constraint" / "capability" named or exemplified in this plan-doc was tested against §self-checks 1-5 from `docs/odd-llm-grounding.lean.md`. Compressed audit rows:

| Element | Classified-as | Self-checks | Pass |
|---|---|---|---|
| "operator files refund dispute" (§1) | objective example | outcome ✓ / rewrite-survives ✓ / method-loose ✓ / observable ✓ / user-purpose ✓ | ✓ |
| "audit trail captures every promotion+demotion+edit+reject" (§1) | objective example (audit outcome the ratification flow delivers) | outcome ✓ / rewrite-survives ✓ / method-loose ✓ / observable ✓ / SOC-2 CC6 user-purpose ✓ | ✓ |
| "src/routes/disputeRoutes.js:42 + tests/dispute-flow.spec.ts" (§1) | implementation citations | NOT objective — file/line specific; correctly classified | ✓ |
| SOC-2 audit-trail floor (§1, §6.7) | constraint | NOT outcome — bounds HOW; correctly classified | ✓ |
| Ratification flow itself (Cycle 2 theme) | tool-internal capability | tool-altitude capability serving v0.2.5 user-objective; correctly classified | ✓ |
| AC.JSTS.express.get.all_orders.... (§8 ref) | implementation | NOT objective — v0.1.8 failure-mode reference; correctly named | ✓ |
| AC.BACKMAP.1-7 + AC.OBJRAT.1-8 (§3) | tool-implementation contracts | NOT user-altitude objectives — ladder up to v0.2.5 user-objective; correctly classified at tool-implementation altitude | ✓ |
| "Backing-implementation map" (Cycle 2 theme) | tool-internal capability | tool-altitude capability; correctly classified | ✓ |
| `objective_id` regex (§3) | structural format constraint | NOT objective — bounds implementation; correctly classified | ✓ |
| "P→V requires explicit_yes + backing-evidence" (§3 AC.OBJRAT.2) | promotion rule constraint | NOT outcome — bounds HOW promotion happens; Decision-I-derived constraint | ✓ |
| "STRONG/WEAK/NONE" signal-strength (§3 AC.BACKMAP.2) | classification labels | NOT objectives — signal-strength orthogonal to objective banding | ✓ |

**Drift-mode check** (each recognised + avoided):

- **Symbol-as-AC** ✓ — evidence rows named as backing-implementation evidence; never labelled as ACs at contract level.
- **Function-name-as-AC** ✓ — `promote_objective`/`populate_backing_map` named as functions; ACs are AC.BACKMAP.*/AC.OBJRAT.* families.
- **Feature-as-objective** ✓ — backing-map + ratification flow named as tool capabilities; user-altitude objectives at v0.2.5.
- **Test-name-as-implementation** ✓ — AC.OBJRAT.2's heuristic explicitly distinguishes outcome-shape from implementation-shape tests.
- **Gap-as-objective** ✓ — `unmatched_objective_ids` carries authoring-gap signal forward; not labelled as objective.
- **Constraint-as-objective** ✓ — Decision I P→V rule named as constraint on promotion; not labelled as objective.
- **Implementation-detail-as-constraint** ✓ — no library/call-shape details labelled as constraints; STRONG/WEAK is orthogonal classification.

§self-checks pass on every "objective" / "AC" / "constraint" / "capability" named in this plan-doc. ✓

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Cycle-2 method decisions at §7. Master-plan method decisions at master plan §9 (`docs/plans/v0-2-3-master-plan.md`). Cycle 1 method decisions at `docs/plans/v0-2-3-cycle-1-multi-source-objective-synthesis.md` §7.

### Commit SHAs

- Amendment commit: `716da0af8444a149568ea3ea90e00f005d2aa907` —
  `chore(amend): v0-2-3-cycle-2-backing-map-and-ratification-reframe manifest+apply — dev-sdlc BASELINE+sidecar bump to 27111ed`
- Seal commit: `857749c4b9a803a49f254f2ed2d6e59c77eee7cf` —
  `chore(seals): v0-2-3-cycle-2-backing-map-and-ratification-reframe — dev-sdlc at 716da0a`
