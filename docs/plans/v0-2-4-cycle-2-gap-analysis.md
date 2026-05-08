# v0.2.4 Cycle 2 — Gap analysis (two-category GapInventory over augmented objectives + backing-map + adapter evidence-rows)

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-04 (Sonnet, plan-author dispatch).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.
**Predecessor:** v0.2.4 Cycle 1 (completeness interview) sealed at `d42ace9`.
**Parent plan:** `docs/plans/v0-2-4-master-plan.md` §3 Cycle 2 + §9.
**Always-load grounding:** `docs/odd-llm-grounding.lean.md`; auto-loaded structurally per v0.2.2 AC.OGP.1/AC.OGP.2. The §self-checks were applied to every "objective" / "AC" / "constraint" / "capability" named here; §11 records the audit pass.
**BASELINE (pre-build tip):** to be set by build agent to the source-edit commit when source lands.

**Quality bar (Luke directive 2026-05-04, carried verbatim):**

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

Cycle 2 IS the gap-surface layer of v0.2.4. Two-category inventory fully implemented (objectives_without_verified_backing + implementation_orphans; not stubbed). Confidence rule (STRONG vs WEAK) honored on both categories. Negative-alignment carved to v0.2.6+ but Pydantic carries the forward-compat field at v0.2.4 (null-default). Audit-log per analysis run (Decision P SOC-2 floor). CLI subcommand idempotent on re-run. **No partial features.** Self-checks pass on every example named per §11.

---

## §1 — Outcome shape

Cycle 2 ships the **gap analysis** that consumes Cycle 1's `augmented-objectives.yaml` + v0.2.3's `backing-map.yaml` + adapter evidence-rows and produces a `GapInventory` persisted at `<workspace>/.loam/extractions/<repo-id>/gap-inventory.yaml`. Two categories: (a) objectives whose backing-map entry is empty OR all evidence-rows are WEAK OR the objective is HYPOTHESISED with no rows; (b) implementation evidence-rows that no objective claims (orphans).

**Pin (outcome 1):** A user invoking `loam odd-extract gaps <workspace>` after Cycle 1 produces an augmented set sees a two-category gap inventory persisted at the canonical path + a stdout summary listing per-category counts + STRONG/WEAK split. Verified by `test_AC_GAPAN_9_integration.py` against the `mixed/` fixture.

**Pin (outcome 2):** Each `Gap` carries a STRONG/WEAK confidence band orthogonal to v0.2.3 objective banding, computed by AC.GAPAN.4 (V/P + empty-backing OR non-test orphan → STRONG; HYPOTHESISED OR test/config-only → WEAK). Verified by `test_AC_GAPAN_4_confidence_rule.py`.

**Pin (outcome 3):** Re-running on unchanged inputs produces a byte-identical inventory (idempotent) plus a 3-event audit-log triple (`gap_analysis_start` / `gap_inventory_persisted` / `gap_analysis_end`). Verified by `test_AC_GAPAN_5_persistence.py` + `test_AC_GAPAN_6_audit_log.py`.

**Pin (outcome 4):** `Gap.negative_alignment_evidence: list[EvidenceRowRef] | None` defaults `None` at v0.2.4 — forward-compat seam for v0.2.6+ negative-alignment without requiring a v0.2.4 schema-version bump. Verified by `test_AC_GAPAN_8_forward_compat.py`.

**Pin (Eric-relevance):** On Eric's rd-automation fixture (interview-added `O.security.audit_trail` PLAUSIBLE; backing-map shows 0 STRONG rows + 3 WEAK rows in `authMiddleware.js`; orphan: `process-disputes` route in `disputeroutes.js` claimed by no objective), the inventory surfaces both — category-a STRONG gap on `O.security.audit_trail` and category-b WEAK orphan on `process-disputes`. Verified structurally by the `eric-shape/` fixture in AC.GAPAN.9.

---

## §2 — Lens checks (per CLAUDE.md design lenses; abbreviated)

**Lens 1 — Claude-leverage-first.** Pure Pydantic + YAML round-trip + filesystem read; zero new Anthropic SDK consumption. Reuses v0.2.3 `BackingMap` + `EvidenceRowRef` + `Objective` + `ConfidenceBand` + Cycle 1 `AugmentedObjectiveSet`. Reuses v0.2.3 `observability.write_audit_entry` (additive event_kinds only). No LLM-judge needed at this altitude — confidence rule is deterministic over typed substrate. Pass.

**Lens 2 — Harness + primary-persona value.** Primary-persona test: translation burden drops from "user manually cross-references objectives.yaml + backing-map.yaml + adapter outputs to spot what's not backed and what's not claimed" to "persona invokes one CLI subcommand; inventory lists both gap categories with confidence bands." Pass. Harness test: `gap_analysis.py` is a reusable harness primitive that Cycle 3 build-next consumes verbatim (gap-inventory.yaml is the input ranking operates over). Pass.

**Lens 3 — ODD authoring.** Outcome + 9 named ACs (§3) + halt triggers (§5 + §6) + smoke (§4) + method-loose. Method-loose holds: orphan-clustering algorithm specifics (per-file vs per-symbol vs per-route grouping) are builder's call; YAML field ordering within the schema constraint is builder's call; stdout summary prose template is builder's call. Constraints pin WHAT (two categories; STRONG/WEAK rule; persistence path; forward-compat field; audit-log floor; idempotence); HOW is the builder's. Pass.

**Lens 4 — Prompt scope ↔ confidence.** **HIGH** for shape: master plan §3 Cycle 2 names 9 load-bearing concerns (Gap Pydantic; GapInventory container; analyze_gaps function signature; confidence rule; persistence; audit-log; CLI; forward-compat field; component tests); Cycle 1 sealed yesterday with the exact substrate shape this consumes. Tight scope: extension to existing `plugins/dev-sdlc/odd-extractor/` component, additive Pydantic models in `spec.py`, one new module (`gap_analysis.py`), AC-shaped tests. **MEDIUM** for confidence-rule wording (master plan §7.2 names this risk); commitments at AC.GAPAN.4 with halt-on-100%-STRONG-or-100%-WEAK escape valve. **MEDIUM** for orphan-grouping algorithm (cluster-collapse vs row-per-orphan); commitments at AC.GAPAN.3 with builder's call inside the AC scope. **HIGH** for substrate preservation. Pass overall.

**Lens 5 — Swarming.** Single-component fence under `plugins/dev-sdlc/odd-extractor/`. Single new module (`gap_analysis.py`) — further decomposition (e.g., `category_a.py` + `category_b.py`) is coordination overhead with no tighter AC. `max_planner_depth: 1` — this is a leaf cycle. Model rationale: Sonnet default; no LLM-judge inside the cycle (see Lens 1). Pass.

---

## §3 — Single-component fence

**PRIMARY scope:** `plugins/dev-sdlc/odd-extractor/` (the existing component's sealed fence; new module + tests + Pydantic-model extensions land under it).

**TERTIARY admission:** `docs/plans/` (universal-paths admission for plan-doc paper trail).

**Read-only compose-points:** `backing_map.py` (consumes `BackingMap` + `EvidenceRowRef`); `spec.py` (consumes `Objective` + `ConfidenceBand` + Cycle 1's `AugmentedObjectiveSet`); adapter evidence-rows produced by `registry.py` + `lang/*/` adapters (consumes via the same evidence-row schema `backing_map.py` consumes — no adapter-side edits).

**Explicit exclusions:** zero edits to `framework/per-project-pm/`, `framework/cost-governance/`, `framework/loam-amend/`, `plugins/dev-sdlc/seals/`, `plugins/dev-sdlc/SEAL_COMMIT*`. Zero edits to v0.2.3 sealed surfaces (`backing_map.py`, `ratify.py`, `synthesis.py`) — read-only consumption only. Zero edits to Cycle 1 sealed surfaces (`completeness.py`, `interview.py`) — read-only consumption only.

---

## §4 — AC enumeration — `AC.GAPAN.*` (locked, 9 ACs)

Each AC has at least one explicit pytest. ODD §2.5: every line of code, branch, test maps to a named AC. §self-checks 1-5 ran on every example outcome / capability / constraint named in this plan-doc; §11 records the audit.

- **AC.GAPAN.1 — `Gap` Pydantic shape.** New Pydantic `Gap` in `spec.py`: `gap_id: str` (regex `^G\.(BACKING|ORPHAN)\.[a-z0-9_-]+$`); `category: Literal["objective_without_verified_backing","implementation_orphan"]`; `confidence: Literal["STRONG","WEAK"]`; `objective_id: str | None` (set for category-a; None for category-b); `evidence_rows: list[EvidenceRowRef]` (empty for empty-backing category-a; populated otherwise); `rationale: str` (≥20 chars); `negative_alignment_evidence: list[EvidenceRowRef] | None` (per AC.GAPAN.8). `model_validator` enforces category-vs-objective_id invariants. Test: `test_AC_GAPAN_1_gap_model.py` — round-trip; ValidationError on category/objective_id mismatch (both directions); rationale-min-length; gap_id regex.

- **AC.GAPAN.2 — `GapInventory` container Pydantic.** New container `GapInventory` in `spec.py` carrying: `schema_version: int = 1`; `extraction_id: str`; `analyzed_at: datetime`; `audit_path: str`; `gaps: list[Gap]`; `summary: GapSummary` (nested model: `category_a_count`, `category_b_count`, `strong_count`, `weak_count`, `total`). `model_validator` enforces no duplicate `gap_id` + summary fields match `gaps` aggregate counts. Test: `test_AC_GAPAN_2_inventory_model.py` — round-trip; ValidationError on duplicate gap_id; ValidationError on summary-mismatch; nested-model validation.

- **AC.GAPAN.3 — `analyze_gaps` function.** New module `gap_analysis.py`; signature `analyze_gaps(*, augmented_objectives: AugmentedObjectiveSet, backing_map: BackingMap, evidence_rows: list[dict], extraction_id: str) -> GapInventory`. Pure function — no I/O; deterministic; no LLM call. For each objective in augmented_objectives: empty backing-entry OR all-rows-WEAK OR HYPOTHESISED-with-no-rows → category-a Gap (confidence per AC.GAPAN.4). For each evidence-row not referenced by any backing-map entry (orphan): group orphans by source-file (clustering details builder's call within "same-file collapses unless distinct symbols"; group-key recorded in rationale) → category-b Gap (confidence per AC.GAPAN.4). Test: `test_AC_GAPAN_3_analyze_gaps.py` — 4 fixture shapes; category counts; determinism; same-file orphan collapse.

- **AC.GAPAN.4 — Confidence rule (STRONG/WEAK).** Helper `_classify_confidence(...)` in `gap_analysis.py`. **STRONG** = (category-a + objective ∈ {VERIFIED, PLAUSIBLE} + empty backing) OR (category-b + at least one non-test/non-config row). **WEAK** = (category-a + HYPOTHESISED) OR (category-a + WEAK-rows-only no STRONG) OR (category-b + all rows in {test, config}). Mixed orphan groups (test + production) → STRONG (production dominates). Halt-and-surface if `mixed/` fixture produces 100%-STRONG or 100%-WEAK (master plan §7.2 calibration anchor). Test: `test_AC_GAPAN_4_confidence_rule.py` — table-driven across all rule branches; degenerate-fixture halt-detection.

- **AC.GAPAN.5 — Persistence at canonical workspace path.** GapInventory persists at `<workspace>/.loam/extractions/<repo-id>/gap-inventory.yaml` (mirrors v0.2.3 `backing-map.yaml` + Cycle 1 `augmented-objectives.yaml` convention; atomic tmp+rename). Schema: `{schema_version: 1, extraction_id, analyzed_at, audit_path, summary: {...}, gaps: [...]}`. Round-trip via `GapInventory.model_dump` / `model_validate`. Idempotent on no-change (byte-identical re-write when inputs unchanged). Test: `test_AC_GAPAN_5_persistence.py` — file written at expected path; round-trip; tmp cleanup; idempotent (re-run = byte-identical).

- **AC.GAPAN.6 — Audit-log event_kinds.** Additive 3 new kinds in `observability.py`: `gap_analysis_start`, `gap_inventory_persisted`, `gap_analysis_end`. Structured payload via existing `estimate` field (no schema-version bump). Start payload: `{extraction_id, augmented_objective_count, backing_map_objective_count, evidence_row_count}`. Persisted payload: `{extraction_id, gap_count, category_a_count, category_b_count, strong_count, weak_count, gap_inventory_path}`. End payload: `{extraction_id, duration_ms}`. Test: `test_AC_GAPAN_6_audit_log.py` — full run; all 3 kinds present in order; payload round-trip.

- **AC.GAPAN.7 — CLI subcommand `loam odd-extract gaps`.** Additive subcommand in `cli.py`: `loam odd-extract gaps <workspace>` reads augmented-objectives.yaml + backing-map.yaml + cached evidence-rows for the workspace's `extraction_id` → invokes `analyze_gaps` → persists `gap-inventory.yaml` → prints stdout summary (per-category counts, per-confidence counts, top-3 example gap_ids per category). Idempotent on re-run. Halt-and-surface on missing predecessor artefacts (no augmented-objectives.yaml → exit code 2 + actionable message: "run `loam odd-extract interview <workspace>` first"). Test: `test_AC_GAPAN_7_cli.py` — stdout summary format; missing-predecessor halt; idempotent re-run.

- **AC.GAPAN.8 — Forward-compat field for v0.2.6+ negative-alignment.** `Gap.negative_alignment_evidence: list[EvidenceRowRef] | None` field at AC.GAPAN.1 defaults to `None`. At v0.2.4 the field is never populated (`analyze_gaps` produces `None` always). At v0.2.6+ negative-alignment introduces a third category (`negative_alignment`) and populates this field on category-a Gaps where evidence rows actively contradict the objective. Round-trip safety: legacy v0.2.4 inventories deserialise via `model_validate` with field absent / None → no schema-version bump required at v0.2.6+. Test: `test_AC_GAPAN_8_forward_compat.py` — model round-trip with field=None; model round-trip with field populated (synthetic v0.2.6+-shape Gap); field absent in serialised YAML when None (no `negative_alignment_evidence: null` clutter; `model_dump(exclude_none=True)` semantics).

- **AC.GAPAN.9 — Component tests on 4 synthetic fixtures.** Fixtures under `plugins/dev-sdlc/odd-extractor/tests/fixtures/gap-analysis/`:
    1. `clean/` — 3 VERIFIED objectives + full STRONG backing + all rows claimed → empty GapInventory.
    2. `category-a-only/` — 1 PLAUSIBLE + empty backing + 1 HYPOTHESISED + no rows; all rows claimed → 2 category-a Gaps (1 STRONG + 1 WEAK).
    3. `category-b-only/` — 3 VERIFIED objectives fully backed + 5 unclaimed rows (3 production same-file collapse → 1 STRONG orphan; 2 test rows → 1 WEAK orphan) → 2 category-b Gaps.
    4. `mixed/` — Eric-shape (synthetic-of-shape): PLAUSIBLE `O.security.audit_trail` with WEAK rows only → category-a WEAK; production-code orphan → category-b STRONG; HYPOTHESISED no-rows → category-a WEAK; test-only orphan → category-b WEAK. Spans all 4 (category × confidence) cells. Calibration anchor — must produce non-degenerate output (per AC.GAPAN.4 halt).
  Each fixture exercises full path: `analyze_gaps` → persistence → audit-log → stdout. Test: `test_AC_GAPAN_9_integration.py` — four sub-tests; per-fixture gap-count + splits + audit-log + stdout format.

---

## §5 — Build dispatch brief

Build dispatch brief authored inline by dispatcher at dispatch time per `dispatch-brief-authoring` SKILL. Source-of-truth for fence + ACs + smoke + AI-time + out-of-scope lives at §3 above + master plan §3 Cycle 2.

---

## §6 — Honest doubts (F2 RF on this decomposition)

**6.1 — Confidence rule may miscalibrate on real data.** Master plan §7.2 already names this. Synthetic fixtures cover the rule branches but Eric's rd-automation may produce edge cases the synthetic anchor missed. *Mitigation:* AC.GAPAN.4 halt-on-degenerate (100%-STRONG or 100%-WEAK on `mixed/`); v0.2.5 HARD-gate run on rd-automation surfaces real-data calibration; cycle plan-doc rule is tunable.

**6.2 — Orphan-clustering under-specified.** AC.GAPAN.3 says "same source-file collapses unless distinct symbols." *Mitigation:* builder's call within AC scope; group-key in rationale (auditable); Cycle 3 ranking treats each Gap atomic — choice doesn't propagate. Residual ~10% drift acceptable.

**6.3 — Forward-compat field may not survive v0.2.6+.** Negative-alignment shape isn't designed yet (carved out per Luke 2026-05-05); field name may need rename. *Mitigation:* `model_dump(exclude_none=True)` keeps v0.2.4 YAML clean; standard Pydantic migration applies if rename needed; no v0.2.4 user is exposed to the field today.

**6.4 — `evidence-rows.yaml` schema unverified.** AC.GAPAN.7 reads cached evidence-rows for the workspace; build agent verifies exact path + schema match v0.2.3 substrate (`<workspace>/.loam/extractions/<repo-id>/evidence-rows.yaml`) before consuming. *Mitigation:* halt-and-surface if path/schema differs; pre-flight grep in build agent.

**6.5 — Idempotence on `analyzed_at`.** AC.GAPAN.5 requires byte-identical re-write but `analyzed_at` always changes. *Mitigation:* idempotence over `gaps` + `summary` content (`model_dump(exclude={"analyzed_at"})`); skip write entirely on no-change; audit-log still records the no-op run.

**6.6 — Cycle wall-clock band 7-12 min may be optimistic.** Cycle 1 actuals may inform an upward adjustment. *Mitigation:* halt-trigger at >3 escalations OR >25 min with no progress; actuals logged for forward calibration.

**6.7 — Eric-shape fixture data must stay synthetic.** `mixed/` references shapes inspired by Eric's repo but committed fixture data is synthetic-of-the-shape — no real customer repo paths leak. *Mitigation:* build agent verifies; AC.GAPAN.9 explicit on synthetic-only.

---

## §7 — Method-decision register (Cycle-2-specific)

| Decision | Choice | Rationale |
|---|---|---|
| `Gap` shape | Pydantic with category + confidence Literals + objective_id Optional | AC.GAPAN.1; structural symmetry with v0.2.3 BackingMap. |
| `GapInventory` container | Pydantic with schema_version=1 + nested `GapSummary` | AC.GAPAN.2; pre-aggregated counts surface to Cycle 3 build-next + CLI stdout. |
| `analyze_gaps` purity | Pure function; no I/O; deterministic | AC.GAPAN.3; testable + idempotent + cacheable. |
| Confidence rule | Deterministic over typed substrate (no LLM-judge) | Master plan §7.2 + Lens 1; LLM-judge introduces variance into a deterministic pipeline + adds cost without commensurate value at this altitude. |
| Orphan clustering | Same-file collapse; group-key in rationale | AC.GAPAN.3; reduces per-file noise; builder iterates within scope. |
| Persistence path | `<workspace>/.loam/extractions/<repo-id>/gap-inventory.yaml` | Mirrors v0.2.3 `backing-map.yaml` + Cycle 1 `augmented-objectives.yaml`. |
| Idempotence semantics | Content-hash sans `analyzed_at`; skip write on no-change | §6.5 mitigation; preserves byte-identical guarantee where it matters. |
| Audit-log event_kinds | 3 additive (start/persisted/end) | AC.GAPAN.6; mirrors Cycle 1's interview-event-kinds pattern. |
| CLI subcommand | `loam odd-extract gaps <workspace>` | Master plan §3 Cycle 2; symmetric with `loam odd-extract interview`. |
| Missing-predecessor handling | Exit code 2 + actionable message | AC.GAPAN.7; surfaces ordering requirement to the user. |
| Forward-compat field | `Gap.negative_alignment_evidence: list[EvidenceRowRef] \| None` defaulting None | AC.GAPAN.8; `model_dump(exclude_none=True)` keeps v0.2.4 YAML clean. |
| Component test count | 4 fixtures (clean / category-a-only / category-b-only / mixed) | AC.GAPAN.9; covers each cell of the (category × confidence) matrix. |
| `mixed/` fixture data | Synthetic-of-Eric-shape (not real repo paths) | §6.7 mitigation; plugin stays repo-agnostic. |
| Plan-doc shape | Cycle 1 sub-plan precedent + trim discipline (§5 stub) | Luke 2026-05-05; mirrors `v0-2-4-cycle-1-completeness-interview.md`. |

---

## §8 — Provenance trail

- **Master plan:** `docs/plans/v0-2-4-master-plan.md` §3 Cycle 2 + §7.2 + §9 (commit `f230333`).
- **Lean grounding doc (auto-loaded):** `docs/odd-llm-grounding.lean.md`. §self-checks + §drift-modes + §altitudes held in working memory throughout authoring.
- **Cycle 1 sub-plan-doc precedent:** `docs/plans/v0-2-4-cycle-1-completeness-interview.md` (committed `36ca3e2`); seal at `d42ace9`.
- **Trim discipline ratification:** master plan §3 light-entry shape + plan-before-code-author + plan-docs-author SKILLs (Luke 2026-05-05).
- **v0.2.3 substrate (load-bearing read-only):** `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/{spec.py, backing_map.py, observability.py, registry.py}`. v0.2.3 SHIPPED rollup `50b5385`. Cycle 2 seal `857749c` (BackingMap shape).
- **Cycle 1 substrate (load-bearing read-only):** `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/{completeness.py, interview.py}` + `AugmentedObjectiveSet` in `spec.py`. Cycle 1 seal `d42ace9`.
- **Eric survey response (Eric-shape fixture inspiration):** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/eric-onboarding-response-2026-05-05.md`. Q4=Yes; Q5 SOC-2 CC6 + auth-bypass.
- **AI-time rubric:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_duration_estimation_rubric.md`.
- **Lens 5 swarming:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_swarming_recursive_decomposition.md`.

---

## §9 — Bookkeeping

Per `loam-amend-cycle` SKILL + master plan §3 Cycle 2:

- **pos-amend apply** (NOT `--amend`); manifest schema v3 (`plan_doc_ref:` + no `amendment.number`).
- **Single semantic commit on apply:** `feat(odd-extractor): v0.2.4 Cycle 2 — gap analysis`.
- **Short-form seal commit** per AC.DPS2 schema-v3.
- **§14 backfill** as separate post-seal commit per AC.D-sa.7.
- **Master plan §9** per-cycle SHA backfill row updates with apply + seal SHAs (master plan §9 is canonical SHA register; this sub-plan §14 is cycle-local audit trail per trim discipline).
- **Tag policy:** v0.2.4 SHIPPED rollup tags after Cycle 3 seals + SOFT smoke green; tag NOT pushed until v0.2.5 ship per master plan §3.
- **Status file:** master plan §9 per-cycle SHA register row + STATE.md SHIPPED entry summary (per trim discipline).

---

## §10 — Halt triggers (in-flight)

Standard set + Cycle-2-specific:

- WD drifts to pos3 (canonical pos-v2 only).
- Plan-before-code violation (any source-edit before plan-doc commit).
- Fence breach (edits outside `plugins/dev-sdlc/odd-extractor/` + universal admissions).
- Confidence rule produces 100%-STRONG or 100%-WEAK on `mixed/` fixture → halt + surface (AC.GAPAN.4 calibration anchor).
- `evidence-rows.yaml` actual schema/path differs from v0.2.3 substrate assumption (§6.4) → halt + surface.
- Forward-compat field (`negative_alignment_evidence`) surfaces tighter coupling than expected (e.g., requires schema-version bump) → halt + surface.
- Orphan clustering algorithm needs ≥3 attempts to satisfy `mixed/` fixture invariants → halt + surface (master plan amendment may be needed).
- Idempotence test fails on `analyzed_at` field handling → halt + surface (§6.5 design needs revision).
- Cycle wall-clock >25 min (2× upper band) with no progress → halt.
- More than 3 escalations needed → halt.
- ODD §2.5 violations in plan-doc OR surrounding code → halt + surface.

---

## §11 — §self-checks audit (per AC.OGP discipline)

Every "objective" / "AC" / "constraint" / "capability" named in this plan-doc was tested against §self-checks 1-5 from `docs/odd-llm-grounding.lean.md`. Compressed:

| Element | Classified-as | Pass |
|---|---|---|
| "two-category gap inventory persisted" (Pin 1) | tool-altitude capability output | ✓ derivative artefact serving v0.2.5 user-objective |
| "audit trail identifies who initiated each dispute" (Eric example) | objective | ✓ outcome / survives rewrite / observable / user-purpose (SOC-2 CC6) |
| "gap analysis" / "GapInventory" / "two-category surface" | tool capabilities | ✓ tool-altitude; serve user-objective at v0.2.5 |
| "STRONG/WEAK confidence rule" | constraint | ✓ bounds HOW confidence is assigned; NOT outcome |
| "process-disputes route in disputeroutes.js" (Eric orphan example) | implementation evidence | ✓ correctly named as evidence row, NOT objective |
| "idempotent re-run" / "atomic tmp+rename" | constraints on persistence | ✓ bound HOW; NOT outcomes |
| "forward-compat field for v0.2.6+ negative-alignment" | constraint | ✓ bound on schema evolution; NOT outcome |
| AC.GAPAN.1-9 (the ACs of THIS plan-doc) | tool-internal implementation contracts | ✓ ladder up to v0.2.5 user-objective |

**Drift-mode check:** Symbol-as-AC ✓; Function-name-as-AC ✓ (`analyze_gaps` named as capability scope in AC.GAPAN.3, not as the AC itself); Feature-as-objective ✓ (gap-analysis named as capability); Test-name-as-implementation ✓ (tests assert OUTCOMES of inventory shape + counts); Gap-as-objective ✓ (this cycle PRODUCES gaps — gaps are findings, not objectives; Cycle 3 ranks them, never promotes them to objectives without user ratify); Constraint-as-objective ✓; Implementation-detail-as-constraint ✓.

§self-checks pass on every element named. ✓

---

## §12 — Acceptance gate

Plan-doc is gate-ready when:

1. ✓ §1 Outcome shape pinned to verification surfaces.
2. ✓ §2 Lens checks all pass.
3. ✓ §3 Single-component fence + read-only compose-points + explicit exclusions.
4. ✓ §4 AC family enumerated (9 ACs locked; each with pytest path).
5. ✓ §5 stub paragraph (trim discipline applied).
6. ✓ §6 F2 RF gaps named with mitigations.
7. ✓ §7 Method-decision register populated.
8. ✓ §8 Provenance trail cited with SHAs.
9. ✓ §9 Bookkeeping aligned with `loam-amend-cycle` SKILL.
10. ✓ §10 Halt triggers (in-flight) enumerated.
11. ✓ §11 §self-checks audit pass on every named element.
12. ✓ §14 method-decision record heading present (per AC.D-sa.7 lint).
13. ✓ Manifest companion authored at `docs/plans/v0-2-4-cycle-2-gap-analysis.manifest.yaml`.

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Cycle-2 method decisions at §7. Master-plan method decisions at master plan §9 (`docs/plans/v0-2-4-master-plan.md`).

### Commit SHAs

- Amendment commit: `5636fc3d465f7956c37782b444ae5c4be12fb992` —
  `chore(amend): v0-2-4-cycle-2-gap-analysis manifest+apply — dev-sdlc BASELINE+sidecar bump to df67276`
- Seal commit: `9d15333c5a8ba00aaaa74e03a1cee2e3eac234c6` —
  `chore(seals): v0-2-4-cycle-2-gap-analysis — dev-sdlc at 5636fc3`
