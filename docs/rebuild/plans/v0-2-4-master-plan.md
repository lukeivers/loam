# v0.2.4 master plan — Completeness interview + gap analysis + "what should I build next?" output

**Status:** master plan-doc, plan-before-code per `feedback_plan_before_code`. Authored 2026-05-04 (Sonnet, plan-author dispatch).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.
**Parent plan:** `docs/rebuild/plans/odd-rebuild-master-plan-2026-05-05.md` §3 v0.2.4 — AUTHORITATIVE.
**Always-load grounding:** `docs/odd-llm-grounding.lean.md` (committed `d37c623`; auto-loaded structurally per v0.2.2 AC.OGP.1/AC.OGP.2). The §self-checks 1-5 in §8 of that doc were applied to every "objective" / "AC" / "constraint" / "capability" named in this plan-doc; §11 below records the self-check pass.

**Predecessor commits:**
- v0.2.3 SHIPPED rollup `50b5385` (combined v0.2.2 + v0.2.3; v0.2.5/v0.2.6 split recorded). Cycle 3 seal `f78bb36`. Apply `e277c27`.
- v0.2.3 Cycle 1 (multi-source synthesis) seal `9b9f87c`; Cycle 2 (backing-map + ratification reframe) seal `857749c`; Cycle 3 (PR-safety + watch reframe + SOFT smoke) seal `f78bb36`. Aggregate ~93 min wall-clock per the AI-time rubric.
- v0.2.2 SHIPPED — apply `ada74e1`, seal `5eda09d`, post-seal SHA backfill `ebca7dc`.
- v0.2.1 SHIPPED rollup `6d66a2e`. Eric ship paused per Luke 2026-05-05.
- ODD grounding lean doc `d37c623`; verbose derivation `ffd9c95`.
- ODD-rebuild master plan `5974103` (v0.2.2 → v0.2.6+ sequence; v0.2.5/v0.2.6 split per Luke 2026-05-05).
- v0.1.7 PM batch API: `framework/per-project-pm/` Cycle 4 seal `122a7c8`. `PMRuntime.enqueue_decision` / `surface_next_questions_batch` / `record_response` are the load-bearing entry-points for Cycle 1's interview surface (verified at `runtime.py:118 / :240 / :313 / :405`).
- v0.2.3 substrate that v0.2.4 layers above:
  - `plugins/dev-sdlc/odd-extractor/spec.py` — `Objective` / `Constraint` / `Capability` Pydantic models (AC.OBJX.{1,2,3} sealed at Cycle 1).
  - `plugins/dev-sdlc/odd-extractor/synthesis.py` — multi-source LLM-pass synthesis pipeline (AC.OBJX.{4,5,8} sealed).
  - `plugins/dev-sdlc/odd-extractor/backing_map.py` — objective→evidence-row map (AC.BACKMAP.* sealed at Cycle 2).
  - `plugins/dev-sdlc/odd-extractor/ratify.py` + `ratification_state.py` — objective-altitude ratification flow (AC.OBJRAT.* sealed at Cycle 2).

**Quality bar (Luke directive 2026-05-04, carried forward):**

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

v0.2.4 IS the layer that turns the v0.2.3 contract into a forward-pointing artefact: the user can ask "what should I build next?" and get back a usable, banded, gap-derived answer. Every objective named answers `outcome-or-fact` on the §self-checks side of "outcome." Every gap surfaced is a gap RELATIVE to user-stated priorities. **No partial features.**

---

## Principles applied this turn

- **CHANNEL** — replies route to dispatcher (not Telegram).
- **AUTONOMY** — settle planning decisions; only escalate genuinely-critical / public-action / financial.
- **F2 RUTHLESS FEEDBACK** — §7 honest doubts surface real tensions in this decomposition (interview-question-bombing; gap-analysis precision-recall; ranking-vs-prescription line; LLM-as-judge cost band).
- **LOCKED-DESIGN-NOT-LICENSE** — ODD-rebuild master plan §3 v0.2.4 + the v0.2.5/v0.2.6 split are the locked design at this depth. Re-tested at §3; held.
- **PROMISES > IN-MOMENT JUDGMENT** — quality bar non-negotiable.
- **ODD §2.5** — every named AC family below ladders to the §2 source-of-truth + the v0.2.6+ end-state objective ("user can ask: what should I build next?"); per-cycle plan-docs tighten + bind to tests at build time.
- **WD-IN-DISPATCHES** — confirmed at start; propagated to every cycle dispatch brief in §4.
- **PARTITION RULE** — pre-resolved at §3:
  - Completeness interview core → `plugins/dev-sdlc/odd-extractor/` (PRIMARY; new `completeness.py` + `interview.py` modules).
  - Gap analysis → `plugins/dev-sdlc/odd-extractor/` (PRIMARY; new `gap_analysis.py`).
  - Build-next recommendation → `plugins/dev-sdlc/odd-extractor/` (PRIMARY; new `build_next.py`).
  - Persona-conversation surface → `framework/persona-extensions/` shape (read-only; conversation-pull surface) + odd-extractor CLI exposure.
- **PLAN-BEFORE-CODE** — this dispatch IS the plan-before-code at master altitude. Per-cycle sub-plan-docs author next.
- **SCOPE-ONLY** — method specifications (LLM judge prompt shape, missing-objective heuristic, ranking-rationale prose template, exact module-name carving) are cycle plan-doc responsibility.
- **NEW-SCHEMA OPPORTUNITY** — manifest YAMLs schema v3 (`plan_doc_ref:`, no `amendment.number`). Seal commits short-form per the schema-v3 convention.
- **SWARMING (Lens 5)** — three cycles each strictly tighter than v0.2.4 parent; further decomposition adds only coordination overhead. Stops at three. `max_planner_depth: 1`.
- **PRINCIPLE-APPLICATION DISCIPLINE** — propagated to every cycle's dispatch brief.
- **TIGHT-VS-LOOSE SCOPE (F4)** — primary work areas + cycle count + negative-alignment-out-of-scope are TIGHT; specific cycle plan-doc method choices (LLM-as-judge vs heuristic for missing-objective detection; ranking algorithm specifics; rationale-prose template) are LOOSE.
- **TIME-CLAIMS-DISCIPLINE** — every AI-time band cited at AI-altitude per the rubric (`wall_clock_minutes ≈ tool_calls × 0.1-0.15`); human-developer-hour bands carried only as parent-master-plan provenance.
- **TEST-AGAINST-OPERATIONAL-OBJECTIVE-BEFORE-ESCALATING** — operational objective is shipping the "what should I build next?" output Eric (or any user) can act on; every decision below tested against that.

---

## §1 — Executive summary

v0.2.4 layers three pieces above v0.2.3's objective-first extractor contract: (1) a **completeness interview** — persona presents extracted objectives + flags missing-but-expected ones, user confirms/adjusts/adds via v0.1.7 PM batch API one-at-a-time per Decision Q; (2) a **gap analysis** producing two-category inventory (`objectives_without_verified_backing` + `implementation_orphans`, per ODD §2.5 strict mapping); (3) a **"what should I build next?" output** ranking gap candidates against user-stated priorities (informative, NOT prescriptive).

**Theme.** Forward-pointing. v0.2.3's contract is the substrate; v0.2.4 turns it into something the user can act on.

**Negative-alignment is OUT OF SCOPE** per Luke 2026-05-05 ruling — carved out to v0.2.6+ as standalone release post-Eric / post-calibration-data. v0.2.4's two-category gap analysis covers Eric's case via the indirect path (he flags missing security objective in interview → gap analysis surfaces WEAK backing → build-next ranks high). See ODD-rebuild master plan §3 v0.2.6+ for the carve-out rationale.

**Cycle count: three cycles**, serialized per `feedback_serialize_amendment_builds`:

1. **Cycle 1 — Completeness interview.** PRIMARY `plugins/dev-sdlc/odd-extractor/`. Missing-objective detection (heuristic + LLM-as-judge); PM batch API interview surface; augmented set persisted.
2. **Cycle 2 — Gap analysis.** PRIMARY `plugins/dev-sdlc/odd-extractor/`. New `gap_analysis.py`; `GapInventory` with two categories; persisted; CLI surface.
3. **Cycle 3 — Build-next + persona surface + SOFT smoke.** PRIMARY `plugins/dev-sdlc/odd-extractor/`. New `build_next.py`; ranking by gap-confidence × priority-match × estimated-impact; informative output (denylist enforces); CLI subcommand for persona pull. Release-level SOFT integration smoke on canonical jsts-playwright-app.

**AI-time band (per rubric `wall_clock_minutes ≈ tool_calls × 0.1-0.15`).** Parent §3 v0.2.4: 6-12 h human-developer → ~36-72 min AI wall-clock. Per-cycle: Cycle 1 ~12-20 min (~80-130 calls); Cycle 2 ~7-12 min (~50-80 calls); Cycle 3 ~12-18 min (~80-120 calls). Aggregate ~31-50 min; midpoint ~40 min, lower edge of parent band given v0.2.3 substrate is more complete than projections assumed.

**Dependencies.** v0.2.3 sealed (objectives + backing-map + ratification); v0.1.7 PM batch API; v0.1.6 cost-governance; v0.2.2 grounding-doc auto-load.

**What closes the release.** Three cycles sealed + SOFT smoke green on canonical jsts-playwright-app fixture: extraction → interview adds 1-2 missing objectives → gap analysis produces inventory with both categories populated → build-next produces ranked candidate list with rationale. HARD smoke against rd-automation deferred to v0.2.5. If any cycle ships partial, halt and surface.

---

## §2 — Scope source-of-truth

Pulled from parent §3 v0.2.4 + composed with v0.2.3 substrate + v0.1.7 PM batch API surface.

### From ODD-rebuild master plan §3 v0.2.4

| Item | Placement |
|---|---|
| Completeness interview (persona presents + flags missing-but-expected) | `plugins/dev-sdlc/odd-extractor/completeness.py` (NEW) — Cycle 1 |
| One-question-at-a-time via PM batch API per Decision Q | `plugins/dev-sdlc/odd-extractor/interview.py` (NEW) — Cycle 1 |
| Augmented set persisted | `<workspace>/.loam/extractions/<repo-id>/augmented-objectives.yaml` (NEW) — Cycle 1 |
| Gap analysis: objectives-without-VERIFIED-backing + implementation-orphans | `plugins/dev-sdlc/odd-extractor/gap_analysis.py` (NEW) — Cycle 2 |
| Negative-alignment cases | OUT OF SCOPE — carved to v0.2.6+ per Luke 2026-05-05 |
| "What should I build next?" output | `plugins/dev-sdlc/odd-extractor/build_next.py` (NEW) — Cycle 3 |
| Persona-conversation surface | CLI subcommand — Cycle 3 |

### v0.2.3 substrate consumed (read-only)

| Substrate | Location | v0.2.4 disposition |
|---|---|---|
| `Objective` / `Constraint` / `Capability` | `spec.py` | Read-only; additive `source` field at Cycle 1 |
| Multi-source synthesis pipeline | `synthesis.py` | Unchanged consumer |
| `BackingMap` + `EvidenceRow` | `backing_map.py` | Read-only at Cycle 2 |
| Ratification flow | `ratify.py` + `ratification_state.py` | Unchanged surface; interview-added objectives ratify via existing path |
| Audit-log floor | `observability.py` | Extended additively with new event_kinds |
| Adapter outputs | `registry.py` + `lang/*/` | Read-only at Cycle 2 (orphan detection) |

### v0.1.7 PM batch API consumed (read-only)

`PMRuntime.enqueue_decision` (`runtime.py:240`); `surface_next_questions_batch(n=1)` (`:313`); `record_response` (`:405`). Zero PM-side edits.

### NOT in scope at v0.2.4

- Negative-alignment detection → v0.2.6+ (Luke 2026-05-05; speculative + calibration-data-dependent).
- HARD smoke gate against rd-automation → v0.2.5.
- Eric re-ship → v0.2.5.
- Auto-promotion of interview-added objectives → never (PLAUSIBLE entry; v0.2.3 ratify flow).
- Prescriptive build-next output → never (informative only per parent line 86).
- Watch / PR-safety surfacing of build-next → post-v0.2.5.
- SKILL.md for "what to build next?" pattern → composes via v0.2.0 auto-skill-capture if recurs.

### Connection to v0.2.5/v0.2.6+

v0.2.4 enables: augmented objective set + two-category gap inventory + ranked build-next output. v0.2.5 ships this against rd-automation as Eric's HARD-gate ship. v0.2.6+ adds the third gap category (negative-alignment) post-calibration-data.

---

## §3 — Cycle decomposition

Three cycles. Each: theme, scope-tightening relative to v0.2.4 parent, fence, AC family seed, smoke dimensions, dependencies, out-of-scope, AI-time, Eric-relevance, quality-bar audit.

### Cycle 1 — Completeness interview

**Theme.** Persona presents extracted objectives + flags missing-but-expected ones (heuristic pre-pass + LLM-as-judge). PM batch API runs one-question-at-a-time interview. User confirms / adjusts / adds. Augmented set persists.

**Scope-tightening.** Parent v0.2.4 AC = "interview + gap-analysis + build-next + persona surface." Cycle 1 AC = "augmented objective set persisted via interview; one-at-a-time enforcement honored; missing-objective detection runs." Strictly tighter — no gap analysis / build-next / persona pull-point (Cycles 2-3).

**Fence.** PRIMARY `plugins/dev-sdlc/odd-extractor/`. Read-only compose-points: `framework/per-project-pm/` (v0.1.7 PM batch API); `framework/cost-governance/` (LLM-judge budget).

**AC family seed.** `AC.COMPINT.*` — augmented-set Pydantic shape (additive `Objective.source` enum; `AugmentedObjectiveSet` container), hybrid missing-objective detection (heuristic pre-pass + LLM-judge cap 5; §self-checks 1-5 applied prompt-side), PM batch API interview surface (one-question-at-a-time per AC.QSURF.1; three question shapes — confirm/flag-missing/free-form-add), interview-added objectives default PLAUSIBLE, persistence at `<workspace>/.loam/extractions/<repo-id>/augmented-objectives.yaml`, audit-log event_kinds for every interview action, cost band $0.20 default ($0.05–$0.50 halt), resumability mirroring v0.2.1 D3, component tests on 3+ synthetic fixtures. Full enumeration in cycle sub-plan-doc §4.

**Smoke dimensions.** D1 cold-state ✓; D5 cross-session ✓; D6 telemetry-floor ✓; D2/D3/D4 inherited.

**Dependencies.** v0.2.3 (Objective shape); v0.1.7 PM batch API; v0.1.6 cost-governance; v0.2.2 grounding-doc auto-load.

**Out-of-scope.** Gap analysis (Cycle 2); build-next (Cycle 3); negative-alignment (v0.2.6+); auto-promotion (never).

**AI-time band.** ~12-20 min wall-clock (~80-130 tool calls × 0.1-0.15). Variability: LLM-judge prompt design + interview-surface composition.

**Eric-relevance.** Cycle 1 flags Eric's auth-bypass concern as missing security objective. Production-stake (Q4=Yes) + survey §5 auth-middleware findings + no security-shape objective in extracted set = high-confidence flag. Eric adds → set augmented → Cycle 2 surfaces backing gap.

---

### Cycle 2 — Gap analysis

**Theme.** Augmented objective set + v0.2.3 backing-map + adapter evidence-rows → `GapInventory` with two categories: (a) `objectives_without_verified_backing` (objective exists; backing-map entry empty OR all rows WEAK; OR HYPOTHESISED with no rows); (b) `implementation_orphans` (evidence-rows not mapped to any objective). Negative-alignment OUT OF SCOPE → v0.2.6+.

**Scope-tightening.** Cycle 2 AC = "gap inventory with two categories produced from augmented set + backing-map; persisted; CLI-observable." Strictly tighter — no ranking (Cycle 3), no persona pull-point (Cycle 3), no negative-alignment (v0.2.6+).

**Fence.** PRIMARY `plugins/dev-sdlc/odd-extractor/`. New `gap_analysis.py`. Read-only compose: `backing_map.py` + `spec.py` + adapter evidence-rows.

**AC family seed.** `AC.GAPAN.*` — `Gap` + `GapInventory` Pydantic shapes (two-category Literal, STRONG/WEAK confidence orthogonal to objective banding), `analyze_gaps()` over (augmented_objectives, backing_map, evidence_rows) with orphan-cluster collapse, confidence rule (STRONG = V/P + empty-backing OR non-test orphan; WEAK = HYPOTHESISED OR test/config orphan), persistence at `<workspace>/.loam/extractions/<repo-id>/gap-inventory.yaml`, audit-log event_kinds, CLI `loam odd-extract gaps <workspace>`, forward-compat `Gap.negative_alignment_evidence` field (null at v0.2.4), component tests on 4 synthetic fixtures (clean / category-a-only / category-b-only / mixed). Full enumeration in cycle sub-plan-doc §4.

**Smoke dimensions.** D1 cold-state ✓; D5 ✓; D6 ✓; D2/D3/D4 inherited.

**Dependencies.** Cycle 1 sealed; v0.2.3 substrate (backing-map + evidence-rows + spec.py).

**Out-of-scope.** Build-next (Cycle 3); persona pull-point (Cycle 3); negative-alignment (v0.2.6+); auto-mitigation (never).

**AI-time band.** ~7-12 min wall-clock (~50-80 tool calls × 0.1-0.15). Variability: confidence-rule tuning + orphan-grouping.

**Eric-relevance.** Cycle 2 turns Eric's interview-added security objective into "O.security.audit_trail (PLAUSIBLE) has 0 STRONG backing rows; 3 WEAK rows in authMiddleware.js." Plus orphans like "process-disputes route in disputeroutes.js has no objective ladder." Eric reads, sees his Q5 concern surfaced.

---

### Cycle 3 — Build-next recommendation + persona surface + SOFT smoke

**Theme.** Gap inventory → ranked candidate list with rationale. Each candidate = gap × priority-match × estimated-impact. Informative (here are gaps matching your stated priorities), NOT prescriptive. Persona invokes via CLI subcommand. Release-level SOFT integration smoke on canonical jsts-playwright-app.

**Scope-tightening.** Cycle 3 AC = "ranked-candidate list with rationale + CLI subcommand + persona pull-point + SOFT smoke green." Strictly tighter — no producer-side change; no negative-alignment (v0.2.6+).

**Fence.** PRIMARY `plugins/dev-sdlc/odd-extractor/`. New `build_next.py` + CLI subcommand. Read-only compose: `gap_analysis.py` output + survey-context at v0.2.1 AC.ONBOARD.15 path. Persona surface IS the CLI invocation at user-question-trigger.

**AC family seeds.**

- `AC.BLDNXT.*` — `BuildNextCandidate` Pydantic, composite ranking (gap-confidence × priority-match × estimated-impact; tie-break by category with objectives-without-backing > orphans), priority-match via survey-context (Q11/Q12) + keyword overlap + LLM-judge for borderline, output cap top-10 (`--limit` configurable), stdout markdown + YAML + human-readable Markdown outputs, **informative-not-prescriptive denylist** at output-emit, cost band $0.10 default ($0.02–$0.30 halt), audit-log event_kinds, component tests on 3+ fixtures (high-priority-match / no-survey-context / orphan-only).
- `AC.PERSONA-PULL.*` — CLI subcommand `loam odd-extract build-next <workspace>` (idempotent ± LLM variance), persona invokes CLI on user-question-trigger (no new SKILL.md at v0.2.4), composition with v0.2.3 ratification (un-ratified flagged in rationale, not blocked), integration test on canonical jsts-playwright-app fixture.

Full enumeration in cycle sub-plan-doc §4.

**Smoke dimensions (release-level SOFT integration smoke).** D1 ✓; D2 ✓ (LLM-judge variance noted, ranking-shape stable); D3 ✓; D5 ✓; D6 ✓; D4 n/a. **§self-checks gate: ≥90%** of augmented objectives + capabilities + constraints pass §self-checks 1-5 (programmatic + LLM-as-judge double-pass). Rate <90% → halt + surface.

**Dependencies.** Cycles 1+2 sealed; v0.2.3 substrate; v0.1.6 cost-governance.

**Out-of-scope.** HARD smoke against rd-automation (v0.2.5); negative-alignment in build-next (v0.2.6+); watch/PR-safety composition (post-v0.2.5).

**AI-time band.** ~12-18 min wall-clock (~80-120 tool calls × 0.1-0.15). Variability: ranking + denylist + smoke setup.

**Eric-relevance.** Cycle 3 closes the loop. Eric's added security objective + Cycle 2 gap → ranked rank 1 with rationale: "This gap matches your stated SOC-2 CC6 concern; WEAK backing at authMiddleware.js:36-55 reflects the auth-bypass paths you flagged in your survey." Eric reads → can act.

---

### Decomposition stopping-criterion check (per Lens 5)

- Three cycles each strictly tighter than v0.2.4 parent (Cycle 1: completeness interview; Cycle 2: gap analysis; Cycle 3: build-next + persona surface + SOFT smoke).
- Considered + rejected splits:
  - **Cycle 3 split into build-next + persona-surface + SOFT-smoke (3 sub-cycles):** persona-surface is documentation + CLI subcommand registration — collapses to coordination overhead vs the build-next module work; SOFT smoke is the release-rollup gate (not a build cycle in the substrate sense). Net negative.
  - **Cycle 1 split into missing-objective-detection + interview-surface (2 sub-cycles):** interview surface IS the consumer of detection; splitting forces a deferred-coupling that Cycle 1's persistence AC can't honor at seal time. Net negative.
  - **Combined Cycle 2 + 3 (gap + build-next together):** breaks strict-tighter rule (Cycle 3's AC subsumes Cycle 2's). Also blows the per-cycle band into a single 20+ min cycle with two distinct module-level concerns — single agent stalls.
- Cycle count: 3, within parent halt-trigger threshold (>4 sub-cycles → halt + surface; not triggered).
- `max_planner_depth: 1` set explicitly per Lens 5 / `feedback_swarming_recursive_decomposition`.

---

## §4 — Per-cycle dispatch briefs

Per-cycle dispatch briefs are authored inline at dispatch time per the dispatch-brief-authoring SKILL. Source-of-truth for fence + ACs + smoke + AI-time + out-of-scope lives at §3 above + the cycle sub-plan-doc. Common shape: WD `/Users/lukeivers/ivers-corp-pos-v2/`; LOAD `docs/odd-llm-grounding.lean.md` FIRST; principles per dispatch-brief-authoring SKILL; manifest schema v3; loam amend apply (NOT --amend); single semantic commit; short-form seal; §14 backfill separate; master plan §9 backfill on seal.

---

## §5 — Release-level smoke gate (SOFT at v0.2.4; HARD deferred to v0.2.5)

SOFT gate per parent master plan §3 v0.2.4 + Decision R precedent (HARD at v0.1.6 / v0.1.8 / v0.2.1 / v0.2.5; SOFT elsewhere). Quality-bar absolutely binding regardless of HARD/SOFT classification. Cycle 3's smoke (§3 above) IS the SOFT gate — release closes when its dimensions exercise green on the canonical jsts-playwright-app fixture (NOT rd-automation; that's v0.2.5's HARD gate target).

After Cycle 1 + Cycle 2 + Cycle 3 seal, release-rollup verifies:

1. **D1 cold-state on canonical jsts-playwright-app fixture.** `loam odd-extract <fixture>` → completeness interview (auto-answered via PM mock; flagged-missing-objective detection runs; user adds 1 objective) → gap analysis (produces inventory with both categories populated) → build-next (produces ranked list with rationale; informative not prescriptive).
2. **D2 steady-state.** Re-run all 4 stages on unchanged inputs → idempotent (LLM-judge variance noted; ranking-shape stable).
3. **D3 restart.** Mid-interview + mid-gap-analysis + mid-build-next `kill -TERM` → re-invoke clean (interview resumes per AC.COMPINT.10; gap-analysis + build-next re-run from scratch).
4. **D5 cross-session.** Session A runs full path + persists; Session B reads artefacts + persona invokes build-next via CLI.
5. **D6 telemetry-floor.** Audit-log per stage (interview + gap-analysis + build-next).
6. **§self-checks pass-rate.** Programmatic + LLM-as-judge over augmented objective set + capability set + constraint set: ≥90% pass §self-checks 1-5. Rate <90% → halt + surface.

**Gate to v0.2.4 release tag (deferred to v0.2.5 ship).** Per parent master plan: v0.2.4 ships the layer but Eric install is gated at v0.2.5. SOFT smoke green + dispatcher creates v0.2.4 SHIPPED rollup commit. Tag is set on the rollup commit but NOT pushed until v0.2.5's HARD-gate ship sequence per parent §3 v0.2.5.

---

## §6 — Open items for dispatcher (max 3)

Three architectural / context calls. All others resolved at master-plan altitude per AUTONOMY.

**§6.1 — Missing-objective LLM-judge approach: heuristic-pre-pass-only vs hybrid (heuristic + LLM-judge).** AC.COMPINT.2 + AC.COMPINT.3 commit to hybrid — heuristic pre-pass produces priors for the LLM-judge to filter or augment. The tight scope says hybrid — heuristic-only catches the obvious cases (production-stake without security objective; survey-mentions-compliance without compliance objective) but misses domain-specific gaps that LLM synthesis catches. The loose scope says heuristic-only — saves cost (~$0.20 per run), keeps the surface simple. Recommendation: hybrid, with cost ceiling AC.COMPINT.9 ($0.20 default; halt outside $0.05-$0.50). Dispatcher rules at Cycle 1 plan-doc time if calibrated cost lands above ceiling, OR if heuristic-pre-pass-alone covers ≥85% of cases on synthetic fixtures.

**§6.2 — Build-next ranking weights: explicit-formula vs LLM-judge.** AC.BLDNXT.2 commits to explicit composite-score formula (gap-confidence × priority-match × estimated-impact) with deterministic tie-break. The tight scope says explicit-formula — predictable, debuggable, no per-call LLM cost beyond AC.BLDNXT.3 (priority-match LLM-judge for borderline only). The loose scope says LLM-as-judge ranks the whole list — captures nuance the formula misses but introduces LLM-variance into ranking-shape. Recommendation: explicit-formula default; LLM-as-judge gates only the priority-match-borderline subset. Dispatcher rules at Cycle 3 plan-doc time if tie-break ambiguity surfaces on synthetic fixtures consistently.

**§6.3 — Persona-conversation pull-point shape: SKILL.md vs documentation-only.** AC.PERSONA-PULL.2 commits to documentation-only at v0.2.4 (no new SKILL.md ships). The tight scope says documentation-only — SKILL extraction is v0.2.0 auto-skill-capture's domain; if "what should I build next?" recurs in user sessions, that mechanism handles it independently. The loose scope says ship a starter SKILL.md alongside v0.2.4 release. Recommendation: documentation-only at v0.2.4. v0.2.0 auto-skill-capture composes structurally if the question recurs. Dispatcher rules at Cycle 3 plan-doc time only if v0.2.0 composition turns out to require explicit SKILL seed (currently it does not).

(No other escalations — primary work areas + cycle decomposition + AI-time bands + Eric-relevance + scope source-of-truth + composition-with-existing-surfaces + halt-and-surface triggers + negative-alignment-out-of-scope settled at this altitude.)

---

## §7 — Honest doubts (F2 RF on this decomposition)

**7.1 — Missing-objective LLM-judge may over-flag or under-flag.** Hybrid heuristic + LLM may produce 0 on clean codebases or 5+ on complex (user bombardment). *Mitigation:* AC.COMPINT.2 cap of 5; cycle plan-doc tightens; halt if synthetic fixtures consistently produce 0 or 5+ on shapes that should differ. Residual ~20% drift acceptable: user skips via question-shape (b)(2); all interview-added objectives enter PLAUSIBLE (no irreversible consequence).

**7.2 — Gap-confidence STRONG/WEAK rule may miscalibrate.** A HYPOTHESISED objective with empty backing might be a real gap; current rule says WEAK. *Mitigation:* cycle plan-doc tunes on synthetic fixtures; AC.GAPAN.9 tests cover edge cases; halt if 100%-STRONG or 100%-WEAK on mixed fixtures.

**7.3 — Informative-not-prescriptive denylist insufficient.** LLM-generated prose can be prescriptive without denylist words. *Mitigation:* cycle plan-doc may add LLM-as-judge pass at output-emit; AC.BLDNXT.9 fixture covers "you should..." case. Residual ~15% slips past on novel phrasings — acceptable given Eric's autonomy authority bound (Q6).

**7.4 — Priority-match degenerates without survey-context.** Survey-absent → output collapses to "priority_match: NONE" everywhere; ranking falls back to gap-confidence × estimated-impact. *Mitigation:* this IS the correct degenerate behavior; stdout summary explicitly flags "no survey-context — ranking by gap-confidence + impact only" (cycle plan-doc adds).

**7.5 — Negative-alignment carve-out may surface user-confusion at v0.2.5.** v0.2.4 ships "what to build next" without auth-bypass-shape detection that catches Eric's specific finding directly. *Mitigation:* indirect path covers Eric's case (interview-flag-missing → gap-analysis-WEAK-backing → build-next-rank-high). Carve-out per Luke 2026-05-05 deliberate trade: ship verified capability now, defer judgment-class until calibration data exists. See ODD-rebuild master plan §3 v0.2.6+.

**7.6 — Cycle 1 AI-time band (12-20 min) may be optimistic.** v0.2.3 Cycle 1 actuals (~30 min / 95 calls) suggest 80-130 tool-call estimate may underestimate prompt-iteration. *Mitigation:* halt-trigger at >3 escalations OR cost-band breach; actuals logged for forward calibration.

**7.7 — SOFT smoke fixture may not exercise priority-match path.** Canonical jsts-playwright-app has no survey-context; build-next falls into §7.4 degenerate. *Mitigation:* Cycle 3 plan-doc adds a synthetic survey-context fixture alongside canonical; both paths verified.

**7.8 — Mid-LLM-judge resume re-runs the LLM call.** Heuristic pre-pass output cached; LLM call fresh on resume → ~$0.05 wasted per killed run. *Mitigation:* AC.COMPINT.10 component test covers; cost acceptable.

---

## §8 — Provenance trail

- **Source authority:** `docs/rebuild/plans/odd-rebuild-master-plan-2026-05-05.md` §3 v0.2.4 + §3 v0.2.5/v0.2.6 split per Luke 2026-05-05.
- **Grounding:** lean `docs/odd-llm-grounding.lean.md` (`d37c623`); verbose `docs/odd-llm-grounding-derivation.md` (`ffd9c95`). §self-checks 1-5 + §drift-modes + §altitudes held throughout this plan-doc authoring.
- **v0.2.3 SHIPPED rollup:** `50b5385`. Cycle seals: Cycle 1 `9b9f87c`; Cycle 2 `857749c`; Cycle 3 `f78bb36`.
- **Shape precedents:** `docs/rebuild/plans/v0-2-3-master-plan.md`; `v0-2-3-cycle-1-multi-source-objective-synthesis.md`; `v0-2-1-cycle-1-eric-onboarding-hardening.md` (PM batch API consumption).
- **v0.1.7 PM batch API:** `framework/per-project-pm/src/loam/per_project_pm/runtime.py:118/240/313/405`. Cycle 4 seal `122a7c8`.
- **v0.2.3 substrate:** `plugins/dev-sdlc/odd-extractor/{spec.py, synthesis.py, backing_map.py, ratify.py, ratification_state.py, observability.py}`.
- **Eric survey response (priority-match input):** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/eric-onboarding-response-2026-05-05.md`. Q4=Yes production-stake; Q5 SOC-2 CC6 + auth-bypass finding (authMiddleware.js:36-55); Q11 "Refactor and add new features, maybe add proper testing"; Q12 "Refactoring / coding / feature dev / bug hunt".
- **rd-automation v0.1.8 wrong-altitude reference:** `/Users/lukeivers/pos3/workspace/rd-automation/.loam/extractions/rd-automation-5f656bad/contract-draft.md` (131 symbol-altitude PLAUSIBLE entries — failure mode the rebuild fixes).
- **AI-time rubric:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_duration_estimation_rubric.md`.
- **Lens 5 swarming:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_swarming_recursive_decomposition.md`.
- **Quality bar (Luke 2026-05-04):** carried forward through v0.2.x master plans.
- **v0.2.5/v0.2.6 split decision:** Luke 2026-05-05; negative-alignment carved out post-Eric, post-calibration.

---

## §9 — Method-decision register

Master-plan-level decisions. Per-cycle plan-docs author own §14.

| Decision | Choice | Rationale |
|---|---|---|
| Cycle count | 3 | Lens 5: each strictly tighter than parent; further split is coordination overhead. |
| Negative-alignment scope | OUT (→ v0.2.6+) | Luke 2026-05-05; speculative + needs calibration data; v0.2.4 two-category gap analysis is sufficient against Eric's priorities. |
| Substrate consumption | v0.2.3 Objective/BackingMap/Ratification read-only; additive Pydantic only | Substrate-preservation; no v0.2.3 surface change. |
| `Objective.source` field | additive enum (`extracted`/`added_by_user`/`flagged_by_persona`) | Provenance for gap-analysis + build-next + audit-log. |
| Missing-objective detection | Hybrid: heuristic pre-pass + LLM-judge | §6.1; heuristic-only misses domain gaps; LLM-only over-flags + costly. |
| Detection cap | 5 candidates per run | AC.COMPINT.2; prevents bombardment. |
| Interview surface | v0.1.7 PM `enqueue_decision` + `surface_next_questions_batch(n=1)` + `record_response`; zero PM-side edits | Decision Q + AC.QSURF.1 verified. |
| Interview-added default band | PLAUSIBLE | v0.2.3 ratification flow handles P→V; no new ratification surface. |
| Augmented set persistence | `<workspace>/.loam/extractions/<repo-id>/augmented-objectives.yaml` | Mirrors v0.2.3 backing-map.yaml shape. |
| Gap categories at v0.2.4 | 2 (objectives-without-verified-backing + implementation-orphans) | Luke 2026-05-05 split. |
| Gap-confidence rule | STRONG = V/P+empty-backing OR non-test orphan; WEAK = HYPOTHESISED OR test/config orphan | AC.GAPAN.4; tunable per cycle plan-doc. |
| Forward-compat for v0.2.6+ | `Gap.negative_alignment_evidence` (null at v0.2.4) | AC.GAPAN.8. |
| Build-next ranking | Composite = gap-confidence × priority-match × estimated-impact; tie-break by category | §6.2 + AC.BLDNXT.2; explicit-formula default. |
| Output cap | top-10 default; `--limit` configurable | Informative not exhaustive. |
| Informative-not-prescriptive | Denylist at output-emit | AC.BLDNXT.6; cycle plan-doc may add LLM-judge pass. |
| Priority-match derivation | Read survey-context (v0.2.1 AC.ONBOARD.15 path) + interview priorities; keyword overlap + LLM-judge for borderline | AC.BLDNXT.3; degenerate "NONE" if survey absent. |
| Persona pull-point | CLI subcommand `loam odd-extract build-next`; no new SKILL.md | §6.3; v0.2.0 auto-skill-capture composes if recurs. |
| Smoke gate | SOFT at v0.2.4; HARD deferred to v0.2.5 | Parent §3 v0.2.4. |
| SOFT-gate fixture | canonical jsts-playwright-app + synthetic survey-context augment | rd-automation is v0.2.5's HARD target; both paths covered. |
| §self-checks gate | ≥90% on augmented objectives + capabilities + constraints; programmatic + LLM-as-judge double-pass | Mirrors v0.2.3 Cycle 3; <90% halt. |
| Release-tag policy | Tag on SHIPPED rollup; do NOT push until v0.2.5 ship | Eric paused per Luke 2026-05-05. |
| Dispatch model tier | Sonnet default; Opus only if Cycle 1 LLM-judge prompt design demands (model-rationale required) | Per Lens 5 + cost. |
| Plan-doc shape | Mirror v0.2.3 / v0.2.1 sub-plan-doc convention | Verified working. |
| Quality-bar absorption | 20% (baked in) | Mirrors precedent. |
| Cost-band ceilings | Cycle 1 $0.20 (band $0.05–$0.50); Cycle 3 $0.10 (band $0.02–$0.30) | AC.COMPINT.9 + AC.BLDNXT.7. |

### Per-cycle SHA backfill table

| Cycle | Theme | Apply SHA | Seal SHA |
|---|---|---|---|
| Cycle 1 | Completeness interview | `e1a4239` | `d42ace9` |
| Cycle 2 | Gap analysis | `5636fc3` | `9d15333` |
| Cycle 3 | Build-next + persona surface + SOFT smoke (release SOFT smoke) | TBD | TBD |

Backfilled per cycle as cycles seal. Final v0.2.4 SHIPPED rollup updates STATE.md + roadmap + ODD-rebuild master plan §3 v0.2.4 row + this register's per-cycle SHAs after Cycle 3 + SOFT smoke green.

---

## §11 — §self-checks audit (per AC.OGP discipline)

Every "objective" / "AC" / "constraint" / "capability" named in this plan-doc tested against §self-checks 1-5 from `docs/odd-llm-grounding.lean.md`. Compressed:

| Element | Classified-as | Pass |
|---|---|---|
| "user can ask: what should I build next?" (§1) | objective (user-altitude) | ✓ outcome / survives rewrite / observable / user-purpose |
| "audit trail identifies who initiated each action" (Eric example) | objective | ✓ outcome / survives rewrite (different audit substrate) / observable / user-purpose (SOC-2 CC6) |
| "Completeness interview" / "Gap analysis" / "Build-next" | tool capabilities | ✓ tool-altitude; serve user-objective |
| "missing-but-expected objective" (AC.COMPINT.2) | flagged candidate | ✓ becomes objective on user ratify; §self-checks applied prompt-side |
| "objectives without VERIFIED backing" / "implementation orphans" | gaps (findings, NOT objectives) | ✓ gap-as-objective drift-mode avoided per grounding §drift-modes #5 |
| "informative-not-prescriptive" / "production-stake profile" / "SOC-2 CC6" | constraints | ✓ bound solution-space; NOT outcomes |
| "AC.JSTS.express.get.process_disputes.src_routes_disputeroutes_js" (orphan example) | implementation | ✓ correctly named as orphan, NOT labelled objective |
| "ranked candidate list with rationale" | tool capability output | ✓ derivative artefact, NOT user-altitude objective |

**Drift-modes check (all avoided):** Symbol-as-AC ✓ (orphan named as implementation); Function-name-as-AC ✓; Feature-as-objective ✓ (interview/gap/build-next named as tool-capabilities); Test-name-as-implementation ✓ (tests assert outcomes per AC.\<family\>.\*); Gap-as-objective ✓ (gaps named as findings — v0.2.4's whole point is gap analysis is a separate layer); Constraint-as-objective ✓; Implementation-detail-as-constraint ✓.

§self-checks pass on every element named. ✓

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Master-plan method-level decisions recorded at §9 above. The `## 14.` heading exists per AC.D-sa.7 lint requirement; content lives at §9 to avoid duplication. Per-cycle plan-docs author own §14 with cycle-specific decisions.
