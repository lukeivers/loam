# v0.2.3 master plan — Objective-first extractor (replaces v0.1.8 extraction logic)

**Status:** master plan-doc, plan-before-code per `feedback_plan_before_code`. Authored 2026-05-05 (Opus, plan-author dispatch).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.
**Parent plan:** `docs/rebuild/plans/odd-rebuild-master-plan-2026-05-05.md` §3 v0.2.3 — AUTHORITATIVE.
**Always-load grounding:** `docs/odd-llm-grounding.lean.md` (committed `d37c623`; auto-loaded structurally per v0.2.2 AC.OGP.1/AC.OGP.2). The §self-checks in §8 of that doc were applied to every "objective" / "AC" / "constraint" / "capability" named in this plan-doc; §11 below records the self-check pass.

**Predecessor commits:**
- v0.2.2 SHIPPED — apply `ada74e1`, seal `5eda09d`, post-seal SHA backfill `ebca7dc` (dev-sdlc at `da58ad8`). Lean grounding doc auto-loads in DEV MODE corpus + dispatch-brief-authoring SKILL extended with 5 propagated principles.
- v0.2.1 SHIPPED rollup `6d66a2e`. Eric ship paused per Luke 2026-05-05.
- ODD grounding lean doc `d37c623`; verbose derivation `ffd9c95`.
- ODD-rebuild master plan `5974103` (v0.2.2 → v0.2.5 sequence).
- v0.1.8 substrate sealed (Cycles 1+2 the load-bearing pieces for repurpose): Cycle 1 scaffolding `c1abda1`; Cycle 2 bands+ratification `4865028`; Cycle 3 Ruby adapter `6711dd7`; Cycle 4a JS/TS adapter `67dd302`; Cycle 4b `c648cf9`; Cycle 5 `e4512b9`. Local rollup `9b64cd4`.
- v0.1.9 PR-safety sealed: Cycle 1 gate engine `790807d`; Cycle 2 hooks+templates `0dc557e`; Cycle 3 SKILLs+cleanup `3284087`. Local rollup `9022df1`.
- v0.2.0 watch+skill-capture sealed: Cycle 1 watch `6fef2f1`; Cycle 2 skill-capture `549fe88`; rollup `bbc93a7`.

**Quality bar (Luke directive 2026-05-04, carried forward):**

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

v0.2.3 IS the rebuild. The substrate is reused; the extraction altitude is what changes. Every objective named in the output answers `outcome-or-fact` on the §self-checks side of "outcome." Every PR-safety gate decision after this release fires on objective-altitude evidence — not symbol-altitude evidence. No partial features.

---

## Principles applied this turn

- **CHANNEL** — replies route to dispatcher (not Telegram).
- **AUTONOMY** — settle planning decisions; only escalate genuinely-critical / public-action / financial.
- **F2 RUTHLESS FEEDBACK** — §7 honest doubts surface real tensions in this decomposition (multi-source synthesis cost; adapter-repurpose-vs-rewrite; PR-safety surface coupling; watch incremental-mode altitude).
- **LOCKED-DESIGN-NOT-LICENSE** — ODD-rebuild master plan §3 v0.2.3 is the locked design at this depth; revisit if cycle decomposition reveals an obviously-better path. Re-tested at §3; held.
- **PROMISES > IN-MOMENT JUDGMENT** — quality bar non-negotiable.
- **ODD §2.5** — every named AC family below ladders to the §2 source-of-truth + the v0.2.5 end-state objective ("user can ask: what should I build next?"); per-cycle plan-docs tighten + bind to tests at build time.
- **WD-IN-DISPATCHES** — confirmed at start; propagated to every cycle dispatch brief in §4.
- **PARTITION RULE** — pre-resolved at §3:
  - Multi-source extraction core → `plugins/dev-sdlc/odd-extractor/` (PRIMARY; substrate already lives here).
  - PR-safety reframe → `plugins/dev-sdlc/pr-safety/` (PRIMARY for Cycle 3).
  - Watch reframe → `plugins/dev-sdlc/odd-extractor/incremental*.py` (PRIMARY for Cycle 3).
  - Ratification reframe → `plugins/dev-sdlc/odd-extractor/ratify.py` + `ratification_state.py` (Cycle 2).
  - Backing-implementation map → `plugins/dev-sdlc/odd-extractor/` (Cycle 2; new module).
- **PLAN-BEFORE-CODE** — this dispatch IS the plan-before-code at master altitude. Per-cycle sub-plan-docs author next.
- **SCOPE-ONLY** — method specifications (LLM provider choice, prompt shape, exact module-name carving, adapter-output schema migration strategy) are cycle plan-doc responsibility.
- **NEW-SCHEMA OPPORTUNITY** — manifest YAMLs schema v3 (`plan_doc_ref:`, no `amendment.number`). Seal commits short-form per the schema-v3 convention.
- **SWARMING (Lens 5)** — three cycles each strictly tighter than v0.2.3 parent; further decomposition adds only coordination overhead. Stops at three. `max_planner_depth: 1`.
- **PRINCIPLE-APPLICATION DISCIPLINE** — propagated to every cycle's dispatch brief.
- **TIGHT-VS-LOOSE SCOPE (F4)** — primary work areas + cycle count are TIGHT; cycle plan-doc method choices are LOOSE per `feedback_agent_prompts_scope_only`.
- **TEST-AGAINST-OPERATIONAL-OBJECTIVE-BEFORE-ESCALATING** — operational objective is shipping the objective-first extractor; every decision below tested against that before any escalation surfaced.

---

## §1 — Executive summary

v0.2.3 is the **rebuild release** of the ODD-rebuild path. v0.1.8 produced the structural-fact extractor that mistakes implementation for ACs (the failure mode the lean grounding doc names structurally); v0.2.3 replaces that extraction logic with an objective-first synthesis pipeline that produces banded objectives + constraints + capabilities + a backing-implementation map (the v0.1.8 structural extraction becomes derivative evidence rows here, not the primary output), and reframes the v0.1.9 PR-safety gate + v0.2.0 continuous-watch to consume this objective-altitude contract. The v0.1.8 substrate (banding shape, audit-log, four-stage workflow, ratification flow plumbing) is preserved; the extraction logic itself is rebuilt.

**Theme.** Right altitude, multi-source. The substrate is correct; the extraction is wrong. Rebuild the extraction; preserve the substrate.

**Cycle count: three cycles**, serialized per `feedback_serialize_amendment_builds`:

1. **Cycle 1 — Multi-source objective synthesis.** PRIMARY `plugins/dev-sdlc/odd-extractor/`. Multi-source pipeline (README + design docs + tests + user-survey + code patterns); LLM-pass synthesis layer; objective + constraint + capability schema; banding (V/P/H) applied to objectives. Adapters become evidence-row producers, not AC producers.
2. **Cycle 2 — Backing-implementation map + ratification reframe.** PRIMARY `plugins/dev-sdlc/odd-extractor/`. New `backing_map.py` (objective_id → code paths). Ratification flow (`ratify.py`, `ratification_state.py`) reframed to objective altitude (P→V on the OBJECTIVE; promotion gate requires backing-implementation evidence).
3. **Cycle 3 — PR-safety + continuous-watch reframe.** Two-component fence: `plugins/dev-sdlc/pr-safety/` (PRIMARY) + `plugins/dev-sdlc/odd-extractor/incremental*.py` (secondary). Gate consumes objectives + backing-map; triggers on diffs touching backing of VERIFIED objectives. Watch flags coverage changes at objective altitude.

**AI-time band.** **12–22 h** per parent §3 v0.2.3, midpoint ~17 h. Cycle 1 is the highest-risk single cycle (multi-source synthesis + LLM-pass cost calibration + adapter-output reshape): **5–10 h**. Cycle 2 (backing-map + ratification reframe; substrate-aware): **3–6 h**. Cycle 3 (consumer-side reframe; gate-logic + watch-classifier reshape): **4–6 h**. 20% quality-bar absorption baked in. Wall-clock ≈ tool_calls × 0.1–0.15.

**Dependencies.** v0.2.2 (lean grounding doc auto-loads — load-bearing for every cycle's plan-author + build agent); v0.1.8 substrate (banding + four-stage workflow + audit-log); v0.1.9 PR-safety (Cycle 3 reframes the gate); v0.2.0 watch (Cycle 3 reframes incremental-mode); v0.1.7 PM batch API (ratification surface, unchanged); v0.1.6 cost-governance (LLM-pass budget envelope; load-bearing for Cycle 1).

**What closes the release.** Cycle 1 + 2 + 3 sealed. Extraction against rd-automation produces objectives at outcome-altitude (Eric's app purpose statement maps to a named objective; the SOC-2-CC6 audit-trail concern maps to a named objective; CSV-upload becomes a capability laddering to an objective, not an objective itself). Backing-implementation map populated. Ratification flow promotes objectives, not symbols. PR-safety gate fires on objective-altitude diff classifications. Watch flags coverage gaps, not symbol diffs. All §self-checks pass on the contract output. If any cycle ships partial, halt and surface; do not proceed to next cycle until that cycle is complete.

The HARD smoke gate against rd-automation end-to-end is **deferred to v0.2.5** per parent master plan §3 v0.2.5; v0.2.3 ships when its three cycles seal green and a SOFT integration smoke (Cycle 3 §3) demonstrates the reframed gate + watch consume the new shape on the canonical-fixture banded contract.

---

## §2 — Scope source-of-truth

Pulled verbatim from parent §3 v0.2.3 + composed with v0.1.8 substrate map + v0.1.9 PR-safety surface + v0.2.0 watch surface.

### From ODD-rebuild master plan §3 v0.2.3

| Item | Source | Placement |
|---|---|---|
| Multi-source extraction pipeline (README + design docs + tests + user-survey + code patterns) | parent §3 v0.2.3 line 59 | `plugins/dev-sdlc/odd-extractor/` (PRIMARY) — Cycle 1 |
| Output: objectives (V/P/H banded), constraints, capabilities | parent §3 v0.2.3 line 60 | `plugins/dev-sdlc/odd-extractor/` schema — Cycle 1 |
| Backing-implementation map (objectives → code paths; v0.1.8 structural extraction becomes evidence rows) | parent §3 v0.2.3 line 61 | `plugins/dev-sdlc/odd-extractor/backing_map.py` (NEW module) — Cycle 2 |
| Surface rename: ACs are objectives (no `AC.JSTS.express.get.<route>` labels for primary output) | parent §3 v0.2.3 line 62 | Cycle 1 schema; Cycle 2 backing-map naming |
| Ratification flow operates at objective altitude (PLAUSIBLE → VERIFIED on OBJECTIVE) | parent §3 v0.2.3 line 63 | `plugins/dev-sdlc/odd-extractor/ratify.py` + `ratification_state.py` — Cycle 2 |
| PR-safety reframe: gate triggers on changes touching code backing a VERIFIED OBJECTIVE | parent §3 v0.2.3 line 64 + master plan §6.6 | `plugins/dev-sdlc/pr-safety/` — Cycle 3 |
| Continuous-watch reframe: operate at objective altitude post-reframe | parent §6 v0.2.3 work area 6 | `plugins/dev-sdlc/odd-extractor/incremental*.py` — Cycle 3 |

### Substrate preserved (NOT rewritten)

| Substrate | v0.1.8/9/0 location | v0.2.3 disposition |
|---|---|---|
| Confidence-band shape (`ConfidenceBand` + `Evidence` + `BandedAC`) | `bands.py` | Preserved type-signature; `text` now holds objective prose; `ac_id` is `O.<domain>.<n>` |
| Four-stage workflow (init/analyze/generate/verify) | `cli.py` + 4 stage modules | Preserved shape; **generate** rewires adapter-pure → multi-source-LLM-pass |
| Audit-log floor | `observability.py` | Preserved; gains objective-promotion entries (structured-payload already supports) |
| Ratification CLI surface | `ratify.py` | Command surface preserved; operates on objectives (Cycle 2) |
| Adapter registry + adapters | `registry.py`, `lang/jsts/`, `lang/ruby/` | **Repurposed to evidence-row producers** for backing-map (Cycle 2). Tree-walk + symbol-extraction unchanged; output flows into evidence rows, NOT primary `acs:` list |
| Budget envelope + dry-run | `budget.py` | Preserved; recalibrated for LLM-pass cost (Cycle 1 plan-doc) |
| PM batch API (one-question-at-a-time) | `framework/per-project-pm/` | Unchanged |
| PR-safety stage shape (read → parse-diff → classify → decide → act) | `pr-safety/{contract,diff,classifier,gate}.py` | Stage shape preserved; classifier + gate reshape (Cycle 3) |
| PR-safety override flow | `pr-safety/override.py` | Operates on objective overlays |
| PR-safety hooks + CI + PR templates | `pr-safety/installers/`, `templates/` | Templates preserved; auto-population reshapes to objective altitude |
| Watch incremental engine shape | `incremental.py` + `incremental_ratify.py` + `proposals.py` + `diff_classifier.py` | Engine shape preserved; classifier + proposal-set reshape (Cycle 3) |

### Surfaces NOT in scope at v0.2.3

| Surface | Disposition | Rationale |
|---|---|---|
| Completeness interview (persona + user augment objectives) | v0.2.4 | Layer above; depends on v0.2.3 producing objectives |
| Gap analysis (objectives without VERIFIED backing; orphans; negative-alignment) | v0.2.4 + v0.2.5 | Layer above; v0.2.5 ships negative-alignment specifically |
| Negative-alignment detection (objective says X, code does ¬X) | v0.2.5 | Hardest layer; deferred per master plan §3 v0.2.5 |
| Auto-skill-capture (v0.2.0 Cycle 2) | unchanged | SKILL-ratification independent of extraction altitude |
| Onboarding ritual (v0.2.1 Cycle 1) | unchanged | Install-time UX, not codebase-analysis |
| Promotion rubric (v0.2.1 Cycle 2) | unchanged | SKILL promotion independent |
| Eric re-ship | v0.2.5 | Eric paused per Luke 2026-05-05 |
| HARD release-level smoke gate against rd-automation end-to-end | v0.2.5 | Negative-alignment detection lives there; HARD-gate at release ship |
| Multi-source schema migration of pre-existing v0.1.8 contract drafts | not on roadmap | New contracts only; existing drafts re-extract |

### Connection to v0.2.5 end-state objective

What v0.2.3 enables: a loam user installed on their codebase has a contract draft populated with objectives at outcome-altitude + a backing-implementation map. The PR-safety gate at this point fires on objective-altitude semantics, and the watch flags coverage-relevant changes. The "what should I build next?" affordance (v0.2.5) and the completeness-interview / gap-analysis (v0.2.4) ride on top of this contract shape.

---

## §3 — Cycle decomposition

Three cycles. Each: theme, scope-tightening relative to v0.2.3 parent, fence, AC family seed, smoke dimensions, dependencies, out-of-scope, AI-time, Eric-relevance, quality-bar audit.

### Cycle 1 — Multi-source objective synthesis (extraction-core rebuild)

**Theme.** The pipeline that produces objectives at outcome altitude from multi-source inputs. The LLM-pass synthesis layer that takes README + design docs + test names + user-survey context + code-pattern signals and emits banded objectives + constraints + capabilities. Adapter outputs become evidence-row inputs to the synthesis, not direct AC producers.

**Scope-tightening.** Parent v0.2.3 AC = "objective-altitude extractor + backing-map + reframed ratification + reframed PR-safety + reframed watch." Cycle 1 AC = "extraction produces objectives + constraints + capabilities at outcome altitude from multi-source inputs; adapter outputs are evidence-row inputs only." Strictly tighter — no backing-map module yet (Cycle 2), no ratification reframe (Cycle 2), no PR-safety reframe (Cycle 3), no watch reframe (Cycle 3).

**Fence.** PRIMARY single-component on `plugins/dev-sdlc/odd-extractor/`. Compose-points (read-only — halt-and-surface if non-trivial extension needed): `framework/cost-governance/` (LLM-pass budget envelope; v0.1.6 primitive); `framework/per-project-pm/` (ratification surface unchanged at this cycle).

**AC family seed: AC.OBJX.\* (Objective-altitude extraction).**

- **AC.OBJX.1** — New extraction-output schema: `Objective` Pydantic model with fields `objective_id` (`O.<domain>.<n>` shape), `text` (outcome-altitude prose), `confidence: VERIFIED | PLAUSIBLE | HYPOTHESISED`, `evidence` (multi-source citation block: README excerpts + design-doc refs + test-name list + user-survey-line refs + code-pattern signals), `domain` (e.g., `dispute-flow`, `auth`, `audit`, `data-export`).
- **AC.OBJX.2** — `Constraint` Pydantic model with fields `constraint_id` (`K.<domain>.<n>`), `text`, `bounds_kind: compliance | infra | language | security | domain`, `evidence`.
- **AC.OBJX.3** — `Capability` Pydantic model with fields `capability_id` (`C.<domain>.<n>`), `text`, `serves: list[objective_id]` (links back to objectives), `evidence`.
- **AC.OBJX.4** — Multi-source input pipeline: extractor reads README (any `README*` at repo root), design docs (any `docs/**/*.md`), test names + assertions (existing adapter tree-walk extended to dump test names + first assertion line), user-survey context (if `~/loam-onboarding-survey.md` or `<repo>/.loam/onboarding-survey.md` exists per AC.ONBOARD.15-style), code patterns (existing adapter tree-walk output, treated as inference signal not authority).
- **AC.OBJX.5** — LLM-pass synthesis emits banded objectives + constraints + capabilities. Banding rule: V if test-name asserts outcome AND README states it (two-source verification); P if README states it without test confirmation (single-source); H if pattern-derived inference only. §self-checks 1-5 run prompt-side as final filter; outputs failing any check are restated, downgraded to H, or dropped.
- **AC.OBJX.6** — Dry-run cost-band estimate BEFORE any LLM call (token-count per repo size). Live extraction enforces foreign-codebase budget envelope per `BudgetExceededError`. Cycle 1 plan-doc commits to a default ceiling (~$1.00/extraction); halt-and-surface if calibrated band wider than $0.10–$5.00.
- **AC.OBJX.7** — Adapter-output reshape: JS/TS + Ruby adapters keep tree-walk + symbol-extraction; output flagged `kind: evidence-rows`, consumed by synthesis (Cycle 1) and backing-map (Cycle 2). Legacy `acs: list[BandedAC]` output preserved in `raw-acs.yaml` (or renamed `evidence-rows.yaml`; Cycle 1 plan-doc decides) — does NOT flow to primary `contract-draft.yaml acs:`.
- **AC.OBJX.8** — Verify stage runs §self-checks 1-5 over each emitted objective/constraint/capability programmatically (text-shape heuristics + LLM-as-judge for borderline per `EVAL_DIMENSIONS` Lens 5). Drift-detection: >30% self-check fail rate → halt + surface (kyegomez/swarms `needs_fresh_start` shape).
- **AC.OBJX.9** — User-survey context: read `<repo>/.loam/onboarding-survey.md` or `~/loam-onboarding-survey.md` if exists; if absent, extraction proceeds without it and survey-shape concerns (production-stake, compliance) cap at PLAUSIBLE (user ratifies to V via Cycle 2 flow).
- **AC.OBJX.10** — Surface migration: contract-draft.md/.yaml shape changes structurally. Cycle 1 plan-doc decides legacy-key transition vs drop (loose); halt-and-surface if the structural break is unworkable mid-cycle.
- **AC.OBJX.11** — Component tests against 3+ synthetic multi-source fixtures (README-rich; README-thin + tests-rich; code-pattern-only). Each exercises synthesis + self-check filter + banding rule.
- **AC.OBJX.12** — Audit-log per synthesis LLM call: source-list + token-count + cost-actual + objective-count by band. Composes with v0.1.6 SOC-2 floor + v0.1.8 audit primitive.

**Smoke dimensions exercised.**
- D1 cold-state ✓ — fresh canonical workspace runs `loam odd-extract <fixture>` producing banded objectives + constraints + capabilities.
- D5 cross-session ✓ — extraction artefacts at `<workspace>/.loam/extractions/<repo-id>/` survive `/clear`; resume works.
- D6 telemetry-floor ✓ — per-extraction-run audit log entry (start/end/cost-actual/synthesis-call-count/objectives-by-band/self-check-pass-rate).
- D2 / D3 / D4 inherited from component-shape per v0.1.8 Cycle 1 precedent (extractor invoked-on-demand, not a daemon).

**Dependencies.** v0.2.2 (lean grounding doc auto-loads — load-bearing for the synthesis prompt); v0.1.8 substrate (bands.py + spec.py + audit-log + four-stage workflow); v0.1.6 cost-governance (LLM-pass budget envelope).

**Out-of-scope.**
- Backing-implementation map module → Cycle 2.
- Ratification reframe (objective-altitude PLAUSIBLE → VERIFIED) → Cycle 2.
- PR-safety reframe → Cycle 3.
- Watch reframe → Cycle 3.
- Completeness interview → v0.2.4.
- Gap analysis → v0.2.4.
- Negative-alignment detection → v0.2.5.

**AI-time band.** **5–10 h**. Wall-clock ~25–60 min. Synthesis-prompt design + multi-source input pipeline + adapter-output reshape + cost calibration are the variability drivers.

**Eric-relevance.** Cycle 1 IS the altitude rebuild. Eric's rd-automation README + survey response + Playwright-spec test names should produce objectives like "operators file refund disputes against DoorDash + Uber Eats merchant portals at scale" (banded V if test names assert the dispute flow; P if only README states it). Without Cycle 1, Eric continues to see `AC.JSTS.express.get.all_orders.src_routes_exportroutes_js` — the failure mode the rebuild exists to fix.

**Quality-bar audit.** Multi-source synthesis fully implemented (not stub). Banding rule explicit (V/P/H criteria documented in extension to `plugins/dev-sdlc/docs/odd-methodology.md`). §self-checks 1-5 enforced programmatically + LLM-as-judge for borderline. Cost surfacing honest (no hidden LLM-pass spend). Adapter outputs reshaped (evidence rows, not ACs). Per-band rule documented. **No partial features.** Self-checks pass on every example AC named in this plan-doc per §11 below. ✓

---

### Cycle 2 — Backing-implementation map + ratification reframe

**Theme.** The backing-implementation map links objectives to code paths; the ratification flow operates at objective altitude. The v0.1.8 structural extraction (adapter symbol-tree output) becomes the population mechanism for the backing-map; ratification PLAUSIBLE → VERIFIED on an objective requires backing-implementation evidence (the objective is observable from outside the system, anchored to code that delivers it).

**Scope-tightening.** Cycle 1 AC = "objectives + constraints + capabilities at outcome altitude." Cycle 2 AC = "objectives are linked to backing-implementation evidence + ratification operates on objectives, not symbols." Strictly tighter — no PR-safety surface change yet (Cycle 3), no watch surface change yet (Cycle 3).

**Fence.** PRIMARY single-component on `plugins/dev-sdlc/odd-extractor/`. New module `backing_map.py`; edits to `ratify.py` + `ratification_state.py`. Compose-points: `framework/per-project-pm/` (ratification surface; PM batch API unchanged); v0.2.0 `proposals.py` (proposal shape; read-only at this cycle).

**AC family seed: AC.BACKMAP.\* + AC.OBJRAT.\*.**

#### AC.BACKMAP.* — Backing-implementation map

- **AC.BACKMAP.1** — `BackingMap` Pydantic model: `objective_id`, `evidence_rows: list[EvidenceRow]`. `EvidenceRow`: `kind: route | callback | model | test | pattern`, `path`, `line_range`, `symbol_name`, `language`, `confidence: STRONG | WEAK` (signal strength; orthogonal to objective banding).
- **AC.BACKMAP.2** — Population: `populate_backing_map(objectives, evidence_rows)` per-objective; LLM-pass classifier matches objectives to evidence (e.g., dispute-flow-objective matches `POST /process-disputes` + `dd_dispute.spec.ts` + `DisputeManager`). Cycle 2 plan-doc decides heuristic-vs-hybrid split (loose; cost-band $0.05–$2.00 halt-trigger).
- **AC.BACKMAP.3** — Persistence at `<workspace>/.loam/extractions/<repo-id>/backing-map.yaml`. Round-trips through Pydantic; D5-survives.
- **AC.BACKMAP.4** — Coverage report: every objective has a backing-map entry (empty `evidence_rows` allowed for HYPOTHESISED). `contract-draft.md` extension shows per-objective backing-row counts.
- **AC.BACKMAP.5** — Forward-compat for v0.2.4/v0.2.5: shape supports `implementation_orphans:` (code paths matching no objective). v0.2.4 gap-analysis + v0.2.5 negative-alignment consume this.
- **AC.BACKMAP.6** — Component tests against 2+ synthetic shapes (tight 1-to-1; loose multi-row; no-evidence HYPOTHESISED).
- **AC.BACKMAP.7** — Audit-log per population: objective-count + evidence-row-count + LLM-pass-token-count + matches-found + matches-uncertain.

#### AC.OBJRAT.* — Objective-altitude ratification

- **AC.OBJRAT.1** — `loam odd-extract ratify` operates on objectives. Interactive batch presents banded objectives one-at-a-time per Decision Q (PM batch API). Each: promote (P→V), demote (P→H or V→P), edit (text refinement), reject (drop).
- **AC.OBJRAT.2** — P→V on objective requires (a) explicit owner Y per Decision I default-no AND (b) at least one strong-confidence backing-map row OR passing test pinned to SHA. Refuses silent promotion AND promotion without backing.
- **AC.OBJRAT.3** — V→P demotion: single explicit action; no backing-evidence requirement.
- **AC.OBJRAT.4** — Audit-log per action: objective_id + band-before/after + actor + timestamp + reason + backing-map-evidence-cited (if promotion).
- **AC.OBJRAT.5** — Constraint + capability ratification: same shape; constraints have no backing-map (bound solution-space, not delivery); capabilities validate `serves:` linkage (cannot ratify if empty or references unknown objectives).
- **AC.OBJRAT.6** — Substrate preservation: extend `ratification_state.py` (do NOT replace). New `RatificationStateV2` schema-versioned; adapter migrates v1 (symbol-AC) → v2 (objective) state if v1 exists. Cycle 2 plan-doc decides migration strategy (loose); halt-and-surface if non-trivial across PM-side queue state.
- **AC.OBJRAT.7** — PM-side `decision-queue.yaml` shape preserved; Cycle 2 plan-doc decides whether entries carry `altitude: objective` field or stay altitude-agnostic.
- **AC.OBJRAT.8** — Component tests against 3+ synthetic banded-objective sets (all-P; mixed-bands; edge-V-without-backing-blocked).

**Smoke dimensions exercised.**
- D1 cold-state ✓ — synthetic banded contract + backing-map → ratify objective → audit log entries observable.
- D5 cross-session ✓ — partial ratification batch resumable across `/clear`; backing-map round-trips.
- D6 telemetry-floor ✓ — audit log entries per ratification + backing-map population.
- D2 / D3 / D4 inherited.

**Dependencies.** Cycle 1 (objective output schema is load-bearing); v0.1.7 Cycle 4 PM batch API; v0.1.8 Cycle 2 ratification substrate.

**Out-of-scope.**
- PR-safety reframe → Cycle 3.
- Watch reframe → Cycle 3.
- Completeness interview → v0.2.4.
- Auto-promotion (no owner ratification) → never on roadmap.

**AI-time band.** **3–6 h**. Wall-clock ~15–35 min. Backing-map shape + LLM-pass classifier prompt design + ratification-flow Pydantic-extension are variability drivers.

**Eric-relevance.** Cycle 2 makes the rebuilt extraction useful: Eric ratifies his app's objectives (production-stake YES → real-money flow OBJECTIVE; SOC-2 audit-trail concern → CONSTRAINT; CSV-upload pipeline → CAPABILITY ladders to objective). Without Cycle 2, Cycle 1's output is read-only — no forward path to acted-on contract.

**Quality-bar audit.** Backing-map fully implemented (not stub). Ratification flow fully reframed at objective altitude (not partial). PLAUSIBLE → VERIFIED rule explicit (backing-evidence required + owner explicit-Y). Substrate preservation (Pydantic extension, not replacement) honored. Migration path explicit. **No partial features.** ✓

---

### Cycle 3 — PR-safety + continuous-watch reframe

**Theme.** The consumers of the contract reframe to objective altitude. PR-safety gate triggers on diffs touching code backing a VERIFIED objective (via backing-map). Continuous-watch flags changes that might affect objective coverage (via backing-map + classifier reshape), not just symbol-level diffs.

**Scope-tightening.** Cycle 1 + Cycle 2 ship the new contract shape. Cycle 3 AC = "PR-safety gate + continuous-watch operate on objective-altitude contract via backing-map." Strictly tighter — no producer-side change at this cycle (Cycles 1 + 2 own that); no negative-alignment detection (v0.2.5).

**Fence.** Two-component fence (serialized per `feedback_serialize_amendment_builds`): PRIMARY edits to `plugins/dev-sdlc/pr-safety/` (gate + classifier + override-flow + audit-log) + secondary edits to `plugins/dev-sdlc/odd-extractor/` (incremental.py + diff_classifier.py + proposals.py reframe — same parent component as Cycles 1 + 2 so single seal). The two components seal as one fence per the substrate convention; manifest names both. Compose-points: `framework/per-project-pm/` (override surface unchanged); `framework/cost-governance/` (production-stake profile unchanged).

**AC family seed: AC.PRSGOBJ.\* + AC.WATCHOBJ.\*.**

#### AC.PRSGOBJ.* — PR-safety reframed at objective altitude

- **AC.PRSGOBJ.1** — `BandedContract` in `pr-safety/spec.py` consumes objectives + backing-map (legacy `acs` drop default per §6.2; Cycle 3 plan-doc revisits if Cycle 1 actuals reveal blocker).
- **AC.PRSGOBJ.2** — Diff classifier consumes backing-map: produces `TouchedObjective` (via backing rows) + `NovelDiff` (lines not mapped).
- **AC.PRSGOBJ.3** — Gate decision matrix at objective altitude: V touched → HARD_BLOCK; P touched → SURFACE_DECISION; H touched → DOCS_ONLY; novel-diff → DOCS_ONLY + implementation-orphan annotation. Pre-emption order HARD_BLOCK > SURFACE_DECISION > DOCS_ONLY > PASS preserved.
- **AC.PRSGOBJ.4** — `OverrideRequest` carries `original_objectives` + `proposed_objectives`. `contract-update:` commit shape preserved; structured-trail YAML carries objective-id + text + before/after band + rationale.
- **AC.PRSGOBJ.5** — PR description template renders objective-altitude content (touched objectives + per-objective band + backing-map rows overlapped + provenance trail with ratification SHAs). Templates at `pr-safety/templates/pr/` updated structurally; CI YAML templates unchanged (invoke same gate CLI).
- **AC.PRSGOBJ.6** — Hooks (`pre-commit`, `pre-push`) install-shape unchanged; gate they invoke operates on objective contract.
- **AC.PRSGOBJ.7** — Audit-log per gate decision: objective-ids touched + bands + backing-rows-overlapped + decision-action + ratification-required + safety-profile.
- **AC.PRSGOBJ.8** — Component tests: V-objective-blocks; P-objective-surfaces; novel-diff-orphan-annotates; production-stake-honour preserved per AC.PRSG.8 v0.1.9 precedent.

#### AC.WATCHOBJ.* — Continuous-watch reframed at objective altitude

- **AC.WATCHOBJ.1** — `diff_classifier.py` reframes: consults backing-map to identify which objectives' backing rows are stale (file moved, symbol removed, line-range shifted). Output: `still_current` / `out_of_date` / `orphaned` at objective altitude (was symbol altitude in v0.2.0).
- **AC.WATCHOBJ.2** — `IncrementalProposalSet` carries objective-altitude proposals ("objective O.<id> may need re-extraction; backing shifted"). Domain-batching in `domain_batching.py` groups by objective domain.
- **AC.WATCHOBJ.3** — PM queue entries: same call-propagation as AC.OBJRAT.7 (consistent altitude-tagging decision across cycles).
- **AC.WATCHOBJ.4** — `--incremental` mode: production-stake refusal shape unchanged (`IncrementalRefusedError`); contract-not-found messaging at objective altitude.
- **AC.WATCHOBJ.5** — Audit-log per incremental run: still_current / out_of_date / orphaned counts + backing-map-staleness-detected.
- **AC.WATCHOBJ.6** — Component tests: backing-row-shifted-detects; objective-orphaned-on-file-deletion; objective-still-current-on-unrelated-diff.

**Smoke dimensions exercised (release-level SOFT integration smoke).**
- D1 cold-state ✓ — fresh canonical-fixture (jsts-playwright-app from v0.1.8 Cycle 4) + objective-altitude contract (extracted via Cycles 1 + 2) + synthetic PR-diff touching VERIFIED-objective backing-row → HARD_BLOCK observed; synthetic PR-diff touching PLAUSIBLE objective → SURFACE_DECISION observed; synthetic external commit modifying backing → watch flags coverage shift.
- D2 steady-state ✓ — re-run extract / gate / watch on unchanged → idempotent.
- D3 restart ✓ — mid-extraction `kill -TERM` → re-invoke clean.
- D5 cross-session ✓ — Session A extracts + ratifies; Session B gate fires on objective-altitude contract.
- D6 telemetry-floor ✓ — audit-log per gate decision + watch run + ratification.
- D4 reboot — n/a structurally for gate/watch components per v0.1.9 + v0.2.0 precedent.

**Dependencies.** Cycles 1 + 2 sealed (objective contract + backing-map are the input); v0.1.9 PR-safety substrate; v0.2.0 watch substrate; v0.1.6 production-safety profile.

**Out-of-scope.**
- HARD release-level smoke gate against rd-automation end-to-end → v0.2.5.
- Negative-alignment detection in PR-safety → v0.2.5 (consumes backing-map + LLM-as-judge).
- Completeness-interview surfacing in watch → v0.2.4.

**AI-time band.** **4–6 h**. Wall-clock ~20–35 min. Two-component fence + classifier + gate-logic + watch-classifier reshape are variability drivers.

**Eric-relevance.** Cycle 3 closes the loop: extraction produces objectives, ratification promotes them to VERIFIED, PR-safety enforces them, watch keeps them synchronised. Without Cycle 3, the new contract shape is producer-only — Eric's gate fires on stale symbol-altitude semantics.

**Quality-bar audit.** Two-component fence + serialised. Gate decision matrix fully reframed (not partial). Override flow reframed (objectives, not ACs). PR-description template reframed. Watch incremental engine reframed. Pre-emption order preserved per v0.1.9. Audit-log preserved per v0.1.6 SOC-2 floor. **No partial features.** ✓

---

### Decomposition stopping-criterion check (per Lens 5)

- Three cycles each strictly tighter than v0.2.3 parent (Cycle 1: extraction-core; Cycle 2: backing-map + ratification reframe; Cycle 3: PR-safety + watch reframe).
- Considered + rejected splits:
  - **Cycle 2 split into backing-map + ratification:** thin dependency between them, but ratification's PLAUSIBLE → VERIFIED rule REQUIRES backing-map evidence (AC.OBJRAT.2). Splitting introduces a deferred-coupling that ratification can't honor at AC.OBJRAT seal time. Net negative.
  - **Cycle 3 split into PR-safety + watch:** both consume backing-map + objective-altitude contract; both reshape diff-classifier logic with overlapping module-level concerns. Splitting forces double-pass on the classifier surface. Net negative.
  - **Combined Cycle 1 + 2:** breaks the strict-tighter rule (Cycle 2's AC subsumes Cycle 1's). Also blows the AI-time band (8–16 h single cycle is the tail of the v0.1.8 precedent — a single agent stalls).
- Cycle count: 3 ∈ [3, 4] (master-plan halt-trigger range, lower edge); halt-trigger (>5 sub-cycles) NOT triggered.
- `max_planner_depth: 1` set explicitly per Lens 5 / `feedback_swarming_recursive_decomposition`.

---

## §4 — Per-cycle dispatch briefs (light)

Three dispatch briefs ready at v0.2.3 cycle-plan-author time. Source-of-truth fields (fence, ACs, smoke, AI-time, out-of-scope) live at §3 — briefs reference §3 + add operational fields. Sub-plan-authors expand at cycle-plan-author time per per-cycle convention.

All three briefs share common shape; only cycle-specific fields differ. Common: WD `/Users/lukeivers/ivers-corp-pos-v2/`; LOAD `docs/odd-llm-grounding.lean.md` FIRST; principles per "Principles applied this turn" above; manifest schema v3; pos-amend apply (NOT --amend); single semantic commit; short-form seal; §14 backfill separate; master plan §9 row backfill on each cycle seal.

### Cycle 1 — Multi-source objective synthesis

Output: `docs/rebuild/plans/v0-2-3-cycle-1-multi-source-objective-synthesis.md` + `.manifest.yaml`.

Quality bar: multi-source synthesis fully implemented (not stub); banding rule explicit; §self-checks 1-5 enforced programmatic + LLM-as-judge; cost surfacing honest; adapter outputs reshaped to evidence-rows.

Source pointers: master plan §3 Cycle 1; ODD-rebuild master plan §3 v0.2.3; `docs/odd-llm-grounding.lean.md`; v0.1.8 substrate; v0.1.6 cost-governance; v0.2.2 grounding propagation `ada74e1`.

Halt triggers: WD drifts; plan-doc not before code; per-extraction cost band wider than $0.10–$5.00; v0.1.9 PR-safety or v0.2.0 watch consumer break non-trivial mid-cycle (master plan revision); >30% self-check fail rate on fixtures; LLM-pass cannot reach outcome-altitude on any 3 synthetic fixtures; ODD violations in surrounding code; >3 escalations.

Model rationale: Sonnet default. Opus permitted for synthesis-prompt design with mandatory `model-rationale:` line per Lens 5.

### Cycle 2 — Backing-implementation map + ratification reframe

Output: `docs/rebuild/plans/v0-2-3-cycle-2-backing-map-and-ratification-reframe.md` + `.manifest.yaml`.

Quality bar: backing-map fully implemented; ratification flow fully reframed at objective altitude; P→V rule explicit (backing + explicit-Y); substrate preservation via Pydantic extension; migration path explicit.

Source pointers: master plan §3 Cycle 2; Cycle 1 SHA backfilled post-seal; v0.1.7 Cycle 4 PM batch API `122a7c8`; v0.1.8 Cycle 2 ratification substrate `4865028`; v0.2.0 Cycle 1 watch `6fef2f1`.

Halt triggers: WD drifts; plan-doc not before code; Cycle 1 not sealed; backing-map population cost-band absent or wider than $0.05–$2.00; ratification-state v1→v2 migration non-trivial in PM-side queue state; >3 escalations.

Model rationale: Sonnet default.

### Cycle 3 — PR-safety + continuous-watch reframe

Output: `docs/rebuild/plans/v0-2-3-cycle-3-pr-safety-and-watch-reframe.md` + `.manifest.yaml`. Single semantic commit covers both pr-safety + odd-extractor edits under shared dev-sdlc parent.

Quality bar: two-component fence serialised; gate decision matrix fully reframed; override flow reframed (objectives, not ACs); PR description template reframed; watch incremental engine reframed; pre-emption order preserved per v0.1.9; audit-log preserved per v0.1.6 SOC-2 floor.

Source pointers: master plan §3 Cycle 3 + §5; Cycles 1 + 2 SHAs backfilled post-seal; v0.1.9 PR-safety (`790807d`, `0dc557e`); v0.2.0 watch `6fef2f1`; v0.1.6 production-safety; v0.1.8 jsts-playwright canonical fixture.

Halt triggers: WD drifts; plan-doc not before code; Cycle 1 OR Cycle 2 not sealed; gate-logic full rewrite needed (vs consumer-swap); legacy-AC backward-compat inconsistency unresolvable; SOFT integration smoke fails on jsts-playwright canonical fixture; >3 escalations. v0.2.3 SHIPPED rollup follows.

Model rationale: Sonnet default.

---

## §5 — Release-level smoke gate (SOFT at v0.2.3; HARD deferred to v0.2.5)

SOFT gate per parent master plan §3 v0.2.3 + Decision R precedent (HARD at v0.1.6 / v0.1.8 / v0.2.1 / v0.2.5; SOFT elsewhere). Quality-bar absolutely binding regardless of HARD/SOFT classification. Cycle 3's smoke (§3 above) IS the SOFT gate — release closes when its dimensions exercise green on the canonical jsts-playwright-app fixture (NOT rd-automation; that's v0.2.5's HARD gate target).

After Cycle 1 + Cycle 2 + Cycle 3 seal, release-rollup verifies:

1. **D1 cold-state on canonical jsts-playwright-app fixture.** `loam odd-extract <fixture>` produces objective-altitude contract + backing-map; ratification CLI promotes one objective P→V with backing evidence; PR-safety gate fires on synthetic VERIFIED-objective-touching diff; watch flags synthetic backing-row-shifting commit.
2. **D2 steady-state.** Re-run extract / gate / watch on unchanged → idempotent.
3. **D3 restart.** Mid-extraction + mid-ratification `kill -TERM` → re-invoke clean.
4. **D5 cross-session.** Session A extracts + ratifies + observes contract shape; Session B persona reads contract + gate fires + watch flags correctly.
5. **D6 telemetry-floor.** Audit-log per extraction + ratification + gate decision + watch run.
6. **§self-checks pass-rate.** Programmatic + LLM-as-judge over the released contract output: ≥90% of objectives + constraints + capabilities pass §self-checks 1-5. Rate <90% → halt + surface (drift signal per Cycle 1 AC.OBJX.8 stopping criterion).

**Gate to v0.2.3 release tag (deferred to v0.2.5 ship).** Per parent master plan: v0.2.3 ships the rebuild but Eric install is gated at v0.2.5. SOFT smoke green + dispatcher creates v0.2.3 SHIPPED rollup commit. Tag is set on the rollup commit but NOT pushed until v0.2.5's HARD-gate ship sequence per parent §3 v0.2.5.

---

## §6 — Open items for dispatcher (max 3)

Three architectural / context calls. All others resolved at master-plan altitude per AUTONOMY.

**§6.1 — Multi-source synthesis cost-band default ceiling.** Cycle 1 plan-doc commits to a per-extraction LLM-pass cost ceiling (e.g., $1.00). The sane band is $0.10–$5.00. Default value within that band is a calibration call that depends on which LLM provider Cycle 1 plan-author selects (Sonnet vs Opus vs Haiku, batch vs streaming, prompt caching vs not). Recommendation: $1.00 per extraction default; halt-and-surface in Cycle 1 plan-doc if calibrated cost lands outside that band. Dispatcher rules at Cycle 1 plan-doc time, not now.

**§6.2 — Legacy-AC backward-compat at PR-safety reframe.** Cycle 3 plan-doc decides whether the v0.1.9 `acs:` shape is supported during a transition window (existing rd-automation extraction at `/Users/lukeivers/pos3/workspace/rd-automation/.loam/extractions/rd-automation-5f656bad/` is on the v0.1.8 shape and would re-extract under v0.2.3). The tight scope says drop legacy support — the rd-automation extraction is a development artefact, not a load-bearing user contract; drop simplifies the gate. The loose scope says preserve for one release. Recommendation: drop. Dispatcher rules at Cycle 3 plan-doc time if Cycle 1 actuals reveal a re-extraction blocker.

**§6.3 — Adapter-output naming (`raw-acs.yaml` vs `evidence-rows.yaml`).** Cycle 1 AC.OBJX.7 leaves this loose. The rename is structural-cleanup-good (the file is no longer "ACs" — it's evidence rows for the synthesis layer); the keep-as-is is migration-friction-low (no consumer breaks). Recommendation: rename to `evidence-rows.yaml` for clarity; legacy filename stays in v0.1.9 PR-safety transition path if §6.2 decides to keep legacy support. Dispatcher rules at Cycle 1 plan-doc time.

(No other escalations — all 5 primary work areas + cycle decomposition + AI-time bands + Eric-relevance + scope source-of-truth + composition-with-existing-surfaces + halt-and-surface triggers settled at this altitude.)

---

## §7 — Honest doubts (F2 RF on this decomposition)

The places this decomposition is least confident.

**7.1 — LLM-pass synthesis may not reach outcome-altitude reliably.** Even with §self-checks 1-5 enforced, LLM outputs can drift to capability/implementation altitude on code-pattern-heavy README-thin inputs. *Mitigation:* AC.OBJX.8 drift detection (>30% halt); §self-checks programmatic + LLM-as-judge double-pass per `EVAL_DIMENSIONS`; HYPOTHESISED banding for pattern-only. Residual: 25% drift still ships objectives that LOOK outcome-shaped but are capability-altitude on close reading. Cycle 1 plan-doc may add adversarial implementation-swap LLM-as-judge.

**7.2 — Multi-source signal inconsistency may produce hallucinated reconciliation.** README/tests/survey/commits may conflict. *Mitigation:* V/P/H banding is the structural defence (P = consistent with multiple sources but not directly verified; H = pattern-only). Adversarial fixture with deliberate cross-source contradiction → synthesis must flag conflict, not silently pick.

**7.3 — Backing-map population cost may exceed $0.05–$2.00 band.** N objectives × M evidence rows naive = expensive on rd-automation's 81 files. *Mitigation:* Cycle 2 commits to hybrid (heuristic pre-filter on adapter symbol-tree + LLM-pass classification on narrowed candidates). Halt if naive cost >$2.00.

**7.4 — Gate-logic rewrite vs consumer-swap depth at PR-safety.** Master plan §6.6 risk: "v0.2.3 reframes break v0.1.9 in transit." Cycle 3 assumes consumer-swap; if `BandedAC`-coupled state spans `gate.py + classifier.py + audit.py + templates/pr/`, cycle-count grows or splits. *Mitigation:* Cycle 3 halt-trigger names this; surfaces in cycle plan-doc §6 if rewrite needed.

**7.5 — Watch reframe may need richer backing-map than Cycle 2 ships.** Watch needs fast "diff at file:line touched objective O.<id>" lookup. Cycle 2's `EvidenceRow` shape intends to cover; tests don't exercise watch consumption. *Mitigation:* Cycle 3 surfaces if shape insufficient; halt + propose Cycle 2 corrective before Cycle 3 proceeds.

**7.6 — Substrate preservation is semantically partial.** `BandedAC.text` now carries outcome-altitude prose — same type signature, behavioural change. Cycle 1's structural reuse hides a semantic break. *Mitigation:* AC.OBJX.10 surfaces; existing `test_AC_BANDS_*` tests may need updating beyond docstring-level.

**7.7 — Survey-absent path caps survey-shape claims at PLAUSIBLE.** Eric's first experience may be many P-band entries he has to ratify. *Mitigation:* v0.2.4 completeness interview promotes; v0.2.3 producing "honest P pending user input" IS the correct shape.

**7.8 — Per-objective backing-map evidence is N→1 lossy at rename.** v0.1.8's 131 symbol-altitude ACs collapse to ~10–30 objectives. *Mitigation:* `evidence_rows` is a list — Cycle 2 preserves all 131 v0.1.8 outputs as evidence rows; rename at primary `acs:` level only. v0.2.3 carries strictly more info than v0.1.8, organised differently.

**7.9 — Cycle 1 AI-time band (5–10 h) may be optimistic.** Heaviest single-cycle ask in path; v0.1.8 Cycle 4a precedent shipped at upper edge. *Mitigation:* >3 escalations halt; log actuals for forward calibration.

**7.10 — Decomposition may split if rd-automation re-extraction surfaces altitude-mismatch edges.** Cycle 3 SOFT smoke runs on canonical jsts-playwright-app fixture, not rd-automation. v0.2.5 HARD gate is the real-codebase test. *Mitigation:* intentional path — corrective-amendment-not-ship-with-caveats per v0.2.1 precedent.

---

## §8 — Provenance trail

- **Master plan source authority:** `docs/rebuild/plans/odd-rebuild-master-plan-2026-05-05.md` §3 v0.2.3 + §5 + §6 + §7.
- **Lean grounding doc (auto-loaded):** `docs/odd-llm-grounding.lean.md` at `d37c623`. §self-checks 1-5 + §drift-modes + §altitudes held in working memory throughout this plan-doc authoring.
- **Verbose grounding doc:** `docs/odd-llm-grounding-derivation.md` at `ffd9c95`.
- **v0.2.2 grounding propagation:** apply `ada74e1`, seal `5eda09d`, post-seal §14 backfill `ebca7dc` (dev-sdlc at `da58ad8`).
- **v0.2.1 SHIPPED rollup:** `6d66a2e`. Eric ship paused per Luke 2026-05-05.
- **v0.2.1 master plan (shape precedent):** `docs/rebuild/plans/v0-2-1-master-plan.md`.
- **v0.2.0 master plan + Cycle 1 watch substrate:** `docs/rebuild/plans/v0-2-0-master-plan.md` + Cycle 1 `6fef2f1`.
- **v0.1.9 master plan + PR-safety substrate:** `docs/rebuild/plans/v0-1-9-master-plan.md` + Cycle 1 `790807d` + Cycle 2 `0dc557e`.
- **v0.1.8 master plan + extractor substrate:** `docs/rebuild/plans/v0-1-8-master-plan.md` + Cycle 1 `c1abda1` + Cycle 2 `4865028`.
- **rd-automation extraction artefacts (concrete v0.1.8 wrong-altitude grounding):** `/Users/lukeivers/pos3/workspace/rd-automation/.loam/extractions/rd-automation-5f656bad/contract-draft.md` (131 symbol-altitude PLAUSIBLE entries — the failure mode the rebuild fixes).
- **Eric's survey response (multi-source synthesis input precedent):** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/eric-onboarding-response-2026-05-05.md`.
- **v0.1.7 PM batch API (ratification surface):** Cycle 4 `122a7c8`.
- **v0.1.6 production-safety + cost-governance:** `3f1d237` / `88674cb`.
- **Schema v3 + seal-narrative compression:** `019cfca` / `df3f50f`.
- **Lens 5 swarming:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_swarming_recursive_decomposition.md` + `framework/CLAUDE.md`.
- **AI-time rubric:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_duration_estimation_rubric.md`.
- **Quality bar (Luke directive 2026-05-04):** parent v0.1.8 §1 verbatim + carried forward through v0.2.x master plans.

---

## §9 — Method-decision register

Master-plan-level method decisions. Per-cycle plan-docs author own §14.

| Decision | Choice | Rationale |
|---|---|---|
| Cycle count | 3 | Lens 5: each strictly tighter than parent; halt-trigger range [3, 4] at lower edge; further split is coordination overhead. |
| Substrate disposition | Repurpose v0.1.8 (banding / four-stage workflow / audit-log / ratification flow); replace extraction logic | Substrate is correct shape; extraction was wrong altitude (parent §7 Decision row). |
| Adapter disposition | Reshape to evidence-row producers (NOT remove); legacy `acs:` output preserved in `raw-acs.yaml`/`evidence-rows.yaml` for backing-map population | v0.1.8 tree-walk + symbol-extraction is correct as evidence; only the AC labelling was wrong. |
| Multi-source inputs | README + design docs + tests + user-survey + code patterns (5 sources) | Parent §3 v0.2.3 line 59 verbatim. |
| LLM-pass synthesis | Yes for objective extraction; cost-banded; §self-checks programmatic + LLM-as-judge double-pass | Heuristic-only cannot reach outcome-altitude on real codebases (parent §6.3). |
| Banding rule (V/P/H) | V = test-asserts-outcome AND README-states-outcome (two-source); P = README-states-outcome only (single-source); H = pattern-only inference | Multi-source banding shape is the honesty-on-uncertainty mechanism (parent §6.2). |
| Backing-implementation map placement | New module `plugins/dev-sdlc/odd-extractor/backing_map.py`; persisted at `<workspace>/.loam/extractions/<repo-id>/backing-map.yaml` | Same parent component; clean module-level seam from Cycle 2; survives `/clear` per D5 expectation. |
| Backing-map population approach | Cycle 2 plan-author chooses heuristic-vs-hybrid (loose method); cost band $0.05–$2.00 per extraction halt-trigger | Cycle 2 plan-doc decides; halt-and-surface if outside band. |
| Ratification altitude shift | PLAUSIBLE → VERIFIED on objective requires backing-map evidence + owner explicit-Y | Backing-map is the structural defence against silent V-promotion of unverified objectives. |
| Substrate Pydantic preservation | Extend (not replace) `BandedAC`, `RatificationState`; new types tagged with schema version | Substrate-preservation framing requires structural extension over rewrite. |
| PR-safety reframe approach | Consumer swap (replace `BandedAC` consumer with `Objective + BackingMap` consumer); legacy-AC drop default | Master plan §6.6 named risk; tight scope says drop; halt-and-surface if rewrite needed (§7.4 + Cycle 3 halt-trigger). |
| Watch reframe approach | Reshape `IncrementalProposalSet` + diff_classifier output to objective altitude; preserve engine shape | Substrate-preservation; classifier is the touch-point. |
| Cycle 3 fence | Two-component (pr-safety + odd-extractor under shared dev-sdlc parent); single seal | Same parent component + serialised builds per `feedback_serialize_amendment_builds`. |
| Smoke gate at v0.2.3 | SOFT (per parent Decision R); HARD deferred to v0.2.5 | Parent master plan §3 v0.2.3 + §3 v0.2.5; Eric ship gates at v0.2.5. |
| SOFT-gate fixture | jsts-playwright-app canonical (NOT rd-automation) | rd-automation is v0.2.5's HARD-gate target; v0.2.3 SOFT covers canonical-fixture sanity. |
| Release-tag policy | Tag on SHIPPED rollup; do NOT push until v0.2.5 ship gate | Eric paused per Luke 2026-05-05; tag accumulates in canonical pos-v2 only. |
| Dispatch model tier | Sonnet for all 3 cycle plan-authors; Opus only for Cycle 1 if multi-source synthesis-prompt design lands above Sonnet's depth (model-rationale required) | Per existing precedent + cost; Opus rationale-line discipline per Lens 5. |
| Plan-doc shape per cycle | Mirror v0.2.1 master-plan / sub-plan-doc convention | Verified working through Eric path. |
| Quality-bar absorption | 20% (baked into 12–22 h band) | Mirrors v0.1.8 + v0.1.9 + v0.2.0 + v0.2.1; recalibrate post-Cycle-1. |
| Cost-band ceilings | Cycle 1 default $1.00 per extraction (band $0.10–$5.00); Cycle 2 default $0.50 per backing-map population (band $0.05–$2.00) | §6.1 + §7.3 + AC.OBJX.6 + AC.BACKMAP.2; halt-and-surface if outside band. |

### Per-cycle SHA backfill table

| Cycle | Theme | Apply SHA | Seal SHA |
|---|---|---|---|
| Cycle 1 | Multi-source objective synthesis | 1e20037 | 9b9f87c |
| Cycle 2 | Backing-implementation map + ratification reframe | TBD | TBD |
| Cycle 3 | PR-safety + continuous-watch reframe (release SOFT smoke) | TBD | TBD |

Backfilled per cycle as cycles seal. Final v0.2.3 SHIPPED rollup updates STATE.md + roadmap + ODD-rebuild master plan §3 v0.2.3 row + this register's per-cycle SHAs after Cycle 3 + SOFT smoke green.

---

## §11 — §self-checks audit (per AC.OGP discipline)

Every "objective" / "AC" / "constraint" / "capability" named or exemplified in this plan-doc was tested against §self-checks 1-5 from `docs/odd-llm-grounding.lean.md`. Compressed audit rows:

| Element | Classified-as | Self-checks 1-5 | Pass |
|---|---|---|---|
| "operators file refund disputes against DoorDash + Uber Eats merchant portals at scale" (§1, §2 worked example from parent master plan) | objective | outcome ✓ / survives rewrite ✓ / builder-method-loose ✓ / observable-from-outside ✓ / user-purpose (replace manual clickwork) ✓ | ✓ |
| "audit trail identifies who initiated each action" (§1, Eric's response §5 narrative) | objective | outcome ✓ / survives rewrite (different audit substrate delivers same) ✓ / builder-method-loose ✓ / observable-from-outside (auditor verifies trail) ✓ / user-purpose (SOC-2 CC6) ✓ | ✓ |
| "CSV upload + validation pipeline" (lean grounding worked example; §2) | capability | NOT outcome — feature serving the dispute-flow objective; correctly classified | ✓ |
| "tokens confidential under transport" (lean grounding §drift-modes) | constraint | NOT outcome — bounds solution-space; correctly classified | ✓ |
| "AC.JSTS.express.get.all_orders.src_routes_exportroutes_js" (rd-automation v0.1.8 output; failure-mode reference in §1) | implementation | NOT objective — file/lib-named, fails implementation-swap test; correctly named as failure-mode the rebuild fixes | ✓ |
| "Multi-source extraction pipeline" / "Backing-implementation map" / "PR-safety gate triggers on diffs touching VERIFIED-objective backing" (Cycles 1, 2, 3 themes) | capabilities of the loam tool itself | tool-internal capabilities serving the user-objective "what should I build next?" at v0.2.5; correctly classified at the tool-altitude | ✓ |
| "Right altitude, multi-source" (§1 theme) | design-intent prose | NOT objective — correctly used as descriptive prose, not labelled as objective | ✓ |

**Drift-mode check** (each recognised + avoided in this plan-doc):

- **Symbol-as-AC** ✓ avoided (rd-automation example named explicitly as the failure mode; Cycle 1 AC.OBJX.7 reshapes adapters away from symbol-AC output).
- **Function-name-as-AC** ✓ avoided (no function-name labels labelled as ACs).
- **Feature-as-objective** ✓ avoided (CSV upload pipeline named as capability throughout).
- **Test-name-as-implementation** ✓ avoided (AC.OBJX.5 banding rule treats test-names asserting outcomes as VERIFIED-class evidence; tests asserting calls remain implementation).
- **Gap-as-objective** ✓ avoided ("missing audit-trail coverage" surfaces as v0.2.4 gap-analysis output, not as objective).
- **Constraint-as-objective** ✓ avoided (SOC-2 + production-stake as constraints; the audit-trail-identifies-who narrative is the objective).
- **Implementation-detail-as-constraint** ✓ avoided (no RSA-OAEP-shape details labelled as constraints).

§self-checks pass on every "objective" / "AC" / "constraint" / "capability" named in this plan-doc. ✓

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Master-plan method-level decisions recorded at §9 above. The `## 14.` heading exists per AC.D-sa.7 lint requirement; content lives at §9 to avoid duplication. Per-cycle plan-docs author own §14 with cycle-specific decisions.
