# v0.1.8 master plan — ODD reverse-engineering (heavy) + Ruby/Rails first-class extractor + dev-sdlc skill-ification pass 1

**Status:** master plan-doc, plan-before-code. Authored 2026-05-04 (Sonnet, plan-author dispatch).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.
**Parent plan:** `docs/rebuild/plans/eric-final-delivery-plan-2026-05-04.md` (§2 v0.1.8 row).
**Companion research (load-bearing):**
- `docs/rebuild/plans/eric-saas-app-use-case-version-sequence-2026-05-04.md` (Eric path)
- `docs/rebuild/plans/layered-skill-story-research-2026-05-04.md` (skills path; §5 = candidate dev-sdlc SKILLs)
- `<workspace>/.scratch/claude-output/odd-reverse-engineering-skill-research.md` (907 lines, eight D-Q.RE.* sub-decisions)
- `plugins/dev-sdlc/docs/smoke-test-discipline.md` (six-dimension smoke spec; release-level HARD gate per Decision R)

**Predecessor commits:**
- v0.1.6 sealed at `3f1d237` (Cycle 1) + `88674cb` (Cycle 2) — production-safety + base-skills.
- v0.1.7 sealed at `3aa20dd` / `73505f0` / `bcf699a` / `122a7c8` — subagents + per-project PM + layered-skill discovery + one-question-at-a-time.
- workspace-bootstrap framework-only → main sealed at `a1e231c`.
- Dev-pattern simplifications (schema v3 + seal-narrative compression) sealed at `019cfca` / `df3f50f`.

**Quality bar (load-bearing — Luke directive 2026-05-04):**

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

v0.1.8 is the **headline release** of the Eric path. Every release-note promise corresponds to tested + reliable behavior. All 6 smoke dimensions exercised at release-level (HARD gate per Decision R). No partial features. The extractor is COMPLETE — first-class Ruby/Rails, not a thin grep fallback.

---

## Principles applied this turn

- **CHANNEL** — replies route to dispatcher (not Telegram).
- **AUTONOMY** — settle planning decisions; only escalate genuinely-critical / public-action / financial.
- **F2 RUTHLESS FEEDBACK** — §7 honest doubts surface where this decomposition could be wrong; surfaced in §6 if a cycle reveals a deeper architectural question.
- **LOCKED-DESIGN-NOT-LICENSE** — Eric synthesis is the locked design for v0.1.8 scope; revisit if cycle decomposition reveals an obvious better path. Re-tested at §3; held.
- **PROMISES > IN-MOMENT JUDGMENT** — quality bar is non-negotiable. Every promised feature delivered fully.
- **ODD §2.5** — every named AC family is named here at master-plan level; per-cycle plan-docs tighten + bind to tests at build time.
- **WD-IN-DISPATCHES** — confirmed at start; propagated to every cycle dispatch brief in §4.
- **PARTITION RULE** — odd-extractor and dev-sdlc-skills placement decisions made at §3.
- **PLAN-BEFORE-CODE** — this dispatch IS the plan-before-code. Build cycles dispatch separately, each with its own sub-plan-doc per cycle.
- **SCOPE-ONLY** — this is a plan; method specifications are for the build cycles to author per their cycle plan-docs.
- **NEW-SCHEMA OPPORTUNITY** — manifest YAMLs authored per cycle use schema v3 (`plan_doc_ref:`, no `amendment.number`). Seal commits short-form per the new convention.
- **PRINCIPLE-APPLICATION DISCIPLINE** — propagated to every cycle's dispatch brief.

---

## §1 — Executive summary

v0.1.8 is the headline release of the Eric path. It is where loam stops being "a methodology + ritual library" and starts being "a tool that reads your codebase and produces a contract you can ratify and gate against." Eric's Rails SaaS gets parsed by a Ruby/Rails-aware extractor; the output is a confidence-banded acceptance-criteria draft (VERIFIED / PLAUSIBLE / HYPOTHESISED) Eric can ratify. Six high-leverage dev-sdlc SKILLs ship alongside, making the loam dev-rituals self-evident as Eric and other dev users learn the surface.

**Theme.** Loam reads Eric's Rails codebase and produces a Ruby-AST-aware contract draft. Confidence bands surface ambiguity for ratification rather than fabricating ACs. Test-first means existing Rails specs become the contract anchor. Six SKILLs make rituals discoverable.

**Cycle count.** **Five cycles**, serialized per `feedback_serialize_amendment_builds`:

1. **Cycle 1 — odd-extractor scaffolding** (NEW component `plugins/dev-sdlc/odd-extractor/`). Language-agnostic skeleton + four-stage workflow shape (init / analyze / generate / verify). No language-specific extractors yet.
2. **Cycle 2 — Confidence bands + ratification workflow.** Schema for VERIFIED / PLAUSIBLE / HYPOTHESISED + AC-promotion workflow (low → medium → high → verified). Eric-ratification workflow composes with `framework/per-project-pm/` (sealed v0.1.7).
3. **Cycle 3 — Ruby/Rails first-class adapter.** Language-specific extractor that understands ActiveRecord migrations, callbacks, concerns, polymorphic associations, ActiveJob/Sidekiq. Test-first extraction priority. Slice-and-swarm (Cartographer-style) for SaaS-app scale.
4. **Cycle 4 — Python first-class adapter + smoke fixtures.** Mirror Ruby coverage for Python-Flask path; ship both fixtures (Python-Flask-payment + Ruby-Rails-payment) for end-to-end smoke. Python is the language-agnostic-skeleton's reference implementation.
5. **Cycle 5 — dev-sdlc skill-ification first pass (6 SKILLs).** Six high-leverage SKILLs: `loam-amend-cycle`, `dispatch-brief-authoring`, `plan-before-code-author`, `fidraft-capture`, `front-load-principle-walk`, `audit-finding-triage`. Single sealed-component amendment cycle on `plugins/dev-sdlc/`.

**AI-time band.** **42–66 hours** at parent §2 estimate, midpoint ~54 h. Cycles 1+2 ship the scaffolding + bands (~12–18 h). Cycle 3 is the highest-risk single cycle (Ruby/Rails first-class, slice-and-swarm; 14–22 h). Cycle 4 mirrors Ruby with Python (~6–10 h, faster because skeleton and bands are already shipped). Cycle 5 ships 6 SKILLs (~8–12 h, ~1–2 h per SKILL plus tests). Plus 20% quality-bar absorption already baked into bands.

**Dependencies on prior versions.**
- v0.1.6 (production-safety + cost-governance) — extractor uses dry-run mode by default per Decision D; foreign-codebase budget envelope governs scope.
- v0.1.7 (per-project PM + layered-skill discovery) — Eric-ratification workflow composes with PM's decision-surfacing protocol; six SKILLs auto-discovered via the layered-skill mechanism sealed at `bcf699a`.
- M-FBM operational health (amendment #125 sealed at `1a1f830`) — load-bearing for cross-session per-codebase state continuity (D5 smoke).

**What closes the release.** v0.1.8 ships when:
1. The extractor produces a confidence-banded contract draft against BOTH Python-Flask AND Ruby-Rails fixtures, with VERIFIED ACs anchored to passing tests.
2. Dry-run cost estimate observable; Eric-ratification workflow runs end-to-end on both fixtures.
3. Test-first priority enforced (no PLAUSIBLE→VERIFIED promotion without a passing test pinned; per Decision I default-to-no).
4. All 6 smoke dimensions exercised on the extractor itself — cold-state ✓, steady-state ✓ (incremental run on fixtures), restart ✓, reboot ✓, cross-session ✓ (resume after `/clear`), telemetry-floor ✓ (per-extraction-run audit log). HARD gate per Decision R.
5. Six dev-sdlc SKILLs discoverable + invokable in canonical pos-v2 (live `/` menu shows them).

If any cycle ships partial, halt and surface; do not proceed to next cycle until that cycle is complete. The risk per Eric §11.5: if v0.1.8 stretches to 60+ hours actual, the response is to split into v0.1.8.a (read-only extractor + bands) + v0.1.8.b (full Cartographer + ratification + skills) — NOT to ship a partial v0.1.8.

---

## §2 — Scope source-of-truth

The full v0.1.8 bundle, pulled verbatim from the parent §2 v0.1.8 row plus layered-skills §5 first-pass (6 SKILLs):

### From Eric synthesis §2 v0.1.8 (extractor + Rails-first-class)

| Item | Source | Placement |
|---|---|---|
| `plugins/dev-sdlc/odd-extractor/` Cartographer-style heavy version | Eric G1 | `plugins/dev-sdlc/odd-extractor/` (NEW component) |
| Confidence-banded contract authoring (VERIFIED / PLAUSIBLE / HYPOTHESISED) | Eric G6 | `plugins/dev-sdlc/odd-extractor/` schema + `plugins/dev-sdlc/docs/odd-methodology.md` extension |
| Language-agnostic skeleton + Python first-class | Eric G9 | `plugins/dev-sdlc/odd-extractor/lang/` |
| Ruby-first-class adapter (NEW per Decision O) | Eric Rails-adder | `plugins/dev-sdlc/odd-extractor/lang/ruby/` |
| Test-first extraction priority (every test → VERIFIED AC) | Eric G1 | `plugins/dev-sdlc/odd-extractor/` |
| Eric-ratification workflow | Eric G1 | `plugins/dev-sdlc/odd-extractor/ratification/` + composes with `framework/per-project-pm/` |
| Smoke fixtures (Python-Flask-payment AND Ruby-Rails-payment) | Eric §6 + Decision O | `plugins/dev-sdlc/odd-extractor/tests/fixtures/` |

### From layered-skills §5 first-pass (6 SKILLs per parent §2)

| SKILL | Why first-pass | Placement |
|---|---|---|
| `loam-amend-cycle` | highest leverage; ritual-dense | `plugins/dev-sdlc/skills/loam-amend-cycle/` |
| `dispatch-brief-authoring` | highest fire-rate; replaces every dispatch-prompt's scaffold | `plugins/dev-sdlc/skills/dispatch-brief-authoring/` |
| `plan-before-code-author` | high CDC-anchor | `plugins/dev-sdlc/skills/plan-before-code-author/` |
| `fidraft-capture` | frequent use | `plugins/dev-sdlc/skills/fidraft-capture/` |
| `front-load-principle-walk` | turn-start | `plugins/dev-sdlc/skills/front-load-principle-walk/` |
| `audit-finding-triage` | medium fire-rate | `plugins/dev-sdlc/skills/audit-finding-triage/` |

Cross-references for traceability:
- **Eric G1 / G6 / G9** — Eric SaaS-app use-case version-sequence research §11 sub-decisions D-Q.RE.{1..8} carry forward as method-level choices for cycles 1–4.
- **Decision O** (parent §3) — Ruby first-class extractor RESOLVED YES; binds Cycle 3 scope.
- **Decision D** (parent §3) — dry-run-default RESOLVED YES; binds Cycle 1's invocation contract.
- **Decision I** (parent §3) — PLAUSIBLE→VERIFIED default-no RESOLVED YES; binds Cycle 2's ratification workflow.
- **Decision F** (parent §3) — two fixtures (Python-Flask + Ruby-Rails) RESOLVED YES; binds Cycle 4 fixture work.
- **Decision R** (parent §3) — HARD smoke gate at v0.1.8 RESOLVED YES; binds release-level smoke (§5).
- **Layered-skills v0.1.8 first-pass list** — confirmed by parent §2; binds Cycle 5.

---

## §3 — Cycle decomposition

Five cycles, each with: theme, scope-tightening relative to v0.1.8 parent, independent fence, AC family seed, smoke dimensions exercised, dependency on prior cycles, out-of-scope deferrals, AI-time band.

### Cycle 1 — odd-extractor scaffolding (NEW component)

**Theme.** Establish the four-stage workflow shape (init / analyze / generate / verify) as a language-agnostic skeleton. No actual language extraction yet — the skeleton lands; concrete extractors land in Cycles 3+4.

**Scope-tightening (relative to v0.1.8).** This cycle's AC is "the extractor scaffolds: a `loam odd-extract <repo>` invocation runs init → analyze → generate → verify in dry-run mode and produces an empty (but well-shaped) contract draft." The parent v0.1.8's AC is "extractor produces a confidence-banded contract against both fixtures." Cycle 1 is strictly tighter: shape without content.

**Independent fence.** NEW component `plugins/dev-sdlc/odd-extractor/`. No edits to other components. Composes with `framework/cost-governance/` for dry-run cost estimate (read-only callout; no edits).

**AC family seed: AC.OREK.* (Odd Reverse Engineering Kit).**
- AC.OREK.1 — `plugins/dev-sdlc/odd-extractor/` exists with proper component scaffold (component.md, tests/, src/, seals/, SEAL_COMMIT sidecar).
- AC.OREK.2 — CLI entry point: `loam odd-extract <repo-path>` invocable; dry-run by default per Decision D; `--live` flag opt-in.
- AC.OREK.3 — Four-stage workflow shape: init (configure repo + budget), analyze (walk repo, plan extractions), generate (run extractions per language), verify (post-process + ODD §2.5 check). Each stage produces a structured artefact (init→config.yaml, analyze→plan.yaml, generate→raw-acs.yaml, verify→contract-draft.md + sidecar.yaml).
- AC.OREK.4 — Language-adapter registry: `plugins/dev-sdlc/odd-extractor/lang/` walks subdirectories per-language; each adapter exports a `supports(repo)` + `extract(repo, plan)` contract. Skeleton ships zero adapters; binding test verifies registry loads cleanly.
- AC.OREK.5 — Dry-run cost estimate: every invocation produces a budget estimate (token count band) BEFORE any LLM calls; surfaces via the cost-governance dry-run primitive sealed in v0.1.6.
- AC.OREK.6 — Foreign-codebase budget envelope: extractor refuses to run live on a repo above a configurable token-band ceiling without explicit `--budget-override` flag.
- AC.OREK.7 — Component-level test surface (no language-specific tests yet): scaffold + workflow shape + registry + dry-run + budget envelope all unit-tested.

**Smoke dimensions exercised.**
- D1 cold-state ✓ — fresh canonical workspace runs `loam odd-extract <fixture-stub>` end-to-end; produces empty contract draft.
- D5 cross-session ✓ — extraction artefacts at `<workspace>/.loam/extractions/<repo-id>/` survive `/clear`; resume works.
- D6 telemetry-floor ✓ — per-extraction-run audit log entry (start/end/cost-actual).
- D2 / D3 / D4 inherited from component-shape: extractor is invoked-on-demand, not a long-running daemon → D2 (steady-state) and D3 (restart) are n/a; D4 (reboot) is n/a.

**Dependency on prior cycles.** None within v0.1.8 (this is Cycle 1). Depends on v0.1.6 cost-governance dry-run primitive + foreign-codebase budget envelope; v0.1.7 layered-skill discovery (the extractor is a plugin component but its outputs may be consumed by SKILLs in Cycle 5).

**Out-of-scope deferrals.**
- Confidence bands → Cycle 2.
- Python adapter → Cycle 4.
- Ruby/Rails adapter → Cycle 3.
- Ratification workflow → Cycle 2.
- 6 SKILLs → Cycle 5.
- Continuous codebase-watch → v0.2.0.

**AI-time band.** **8–14 h** (component scaffold + four-stage workflow shape + tests + smoke).

---

### Cycle 2 — Confidence bands + ratification workflow

**Theme.** Schema for VERIFIED / PLAUSIBLE / HYPOTHESISED + the AC-promotion workflow (HYPOTHESISED → PLAUSIBLE → VERIFIED). Ratification composes with `framework/per-project-pm/` from v0.1.7.

**Scope-tightening.** Cycle 1's AC is "shape without content." Cycle 2's AC is "shape carries banded ACs and the ratification workflow can promote them." Still no actual extraction yet — bands populate from a stubbed test source. Strictly tighter than parent.

**Independent fence.** Two-component fence (serialized): primary edits to `plugins/dev-sdlc/odd-extractor/` (schema + ratification subpackage); secondary edits to `framework/per-project-pm/` (PM-side ratification batch + queue integration). Per `feedback_serialize_amendment_builds`, the two components seal as one fence after the source-edit; the manifest names both.

**AC family seed: AC.BANDS.* (Confidence bands).**
- AC.BANDS.1 — Each AC in the contract draft carries a `confidence: HYPOTHESISED | PLAUSIBLE | VERIFIED` field with a `evidence:` block listing source-citations (file paths + line numbers + test names if VERIFIED).
- AC.BANDS.2 — VERIFIED requires a passing test pinned (test name + repo SHA at extraction time). PLAUSIBLE requires source-code citation. HYPOTHESISED requires an LLM-derived inference rationale.
- AC.BANDS.3 — Schema documented in `plugins/dev-sdlc/docs/odd-methodology.md` extension (universal-admitted doc edit).
- AC.BANDS.4 — Ratification workflow: `loam odd-extract ratify <contract-draft>` opens an interactive batch (or PM-mediated batch per v0.1.7 Decision Q one-question-at-a-time); each AC's band can be promoted/demoted/edited/rejected.
- AC.BANDS.5 — PLAUSIBLE→VERIFIED promotion requires owner explicit yes per Decision I (default-no). Workflow refuses silent promotion.
- AC.BANDS.6 — Audit log: every ratification action (promote / demote / edit / reject) appends to `<workspace>/.loam/extractions/<repo-id>/audit-log/` per the SOC-2 floor (Decision P).
- AC.BANDS.7 — PM integration: ratification batches surface through `<workspace>/.loam/pms/<pm-name>/decision-queue.yaml`; one-question-at-a-time per Decision Q.

**Smoke dimensions exercised.**
- D1 cold-state ✓ — synthetic banded contract → ratify → audit log entries observable.
- D5 cross-session ✓ — partial ratification batch resumable across `/clear`.
- D6 telemetry-floor ✓ — audit log entries per ratification.
- D2 / D3 / D4 inherited from Cycle 1.

**Dependency on prior cycles.** Cycle 1 (extractor scaffold). Within parent: v0.1.7 Cycle 2 + Cycle 4 (per-project PM + one-question-at-a-time).

**Out-of-scope deferrals.**
- Actual language extraction → Cycles 3+4.
- Test-first extraction priority → Cycle 3+4 (the extraction phase that derives VERIFIED from passing tests).
- 6 SKILLs → Cycle 5.

**AI-time band.** **6–10 h** (schema + workflow + PM integration + tests + smoke).

---

### Cycle 3 — Ruby/Rails first-class adapter

**Theme.** Language-specific extractor that understands Rails idioms. THE highest-risk cycle: Decision O resolved yes, so Eric ships on a first-class Ruby/Rails adapter, not a thin grep fallback. Slice-and-swarm (Cartographer-style) for SaaS-app scale.

**Scope-tightening.** Cycle 2's AC is "schema carries banded ACs." Cycle 3's AC is "the Ruby/Rails adapter populates the banded contract from a real Rails codebase, with VERIFIED ACs anchored to passing RSpec/Minitest tests, PLAUSIBLE ACs anchored to ActiveRecord/concerns/polymorphic associations/Sidekiq jobs, HYPOTHESISED ACs anchored to LLM-inferred behaviour." Strictly tighter — language matters.

**Independent fence.** Single-component fence on `plugins/dev-sdlc/odd-extractor/`. No edits to `framework/`.

**AC family seed: AC.RAILS.* (Ruby/Rails first-class extraction).**
- AC.RAILS.1 — Ruby AST adapter at `plugins/dev-sdlc/odd-extractor/lang/ruby/` parses Ruby source via a deterministic AST library (e.g., parser gem or equivalent; method-level choice for Cycle 3 plan-doc).
- AC.RAILS.2 — Rails-idiom recognisers: ActiveRecord migrations (db/migrate/); callbacks (before_save, after_create, etc.); concerns (app/models/concerns/, app/controllers/concerns/); polymorphic associations (`belongs_to :owner, polymorphic: true`); ActiveJob/Sidekiq (app/jobs/, queue_as :*); routes (config/routes.rb).
- AC.RAILS.3 — Test-first extraction priority per Decision G1: every passing RSpec/Minitest test → candidate VERIFIED AC. Test name + file path + repo SHA captured as evidence.
- AC.RAILS.4 — Slice-and-swarm: codebase exceeding token-budget ceiling is sliced (per-component / per-domain / per-route) and swarmed (parallel sub-extractions per slice; aggregator merges). Per Lens 5 (swarming).
- AC.RAILS.5 — Eric-ratification workflow runs end-to-end on the Ruby-Rails-payment fixture (smoke fixture lands in Cycle 4; this AC pins the extraction shape against that fixture once it lands).
- AC.RAILS.6 — Confidence band rules per Rails idiom: ActiveRecord schema → PLAUSIBLE (schema is real but behaviour requires verification); passing test asserting that schema → VERIFIED; LLM-inferred domain rule → HYPOTHESISED.
- AC.RAILS.7 — Cost-governance dry-run: dry-run produces per-slice token-band estimate; live run respects budget envelope.
- AC.RAILS.8 — Adapter unit tests against synthetic Rails snippets (no full fixture yet — that's Cycle 4).

**Smoke dimensions exercised.**
- D1 cold-state ✓ — adapter runs against a small synthetic Rails snippet; produces banded ACs.
- D2 steady-state ✓ — incremental re-run against same snippet produces stable output (idempotent extraction).
- D5 cross-session ✓ — extraction state survives `/clear`; resume mid-slice.
- D6 telemetry-floor ✓ — per-slice audit log entries.
- D3 / D4 inherited.

**Dependency on prior cycles.** Cycle 1 (scaffold) + Cycle 2 (bands + ratification). Composes with v0.1.6 cost-governance.

**Out-of-scope deferrals.**
- Python adapter → Cycle 4.
- Full Ruby-Rails-payment fixture + end-to-end smoke → Cycle 4 (fixtures land there).
- 6 SKILLs → Cycle 5.
- Continuous codebase-watch → v0.2.0.

**AI-time band.** **14–22 h** (highest-risk single cycle: Ruby AST integration + Rails-idiom recognisers + slice-and-swarm + test-first + tests + smoke).

**Halt-trigger specific to Cycle 3.** If Ruby AST library integration proves infeasible within ~5 h of plan-author + first-pass implementation → halt and surface; recommend split into Cycle 3.a (Ruby AST + 3 Rails idioms — ActiveRecord, callbacks, routes) + Cycle 3.b (concerns, polymorphic, Sidekiq, slice-and-swarm). Per parent §6.2 risk mitigation.

---

### Cycle 4 — Python first-class adapter + smoke fixtures

**Theme.** Mirror Ruby coverage for Python (the language-agnostic-skeleton's reference implementation per Eric G9). Ship both fixtures so end-to-end smoke runs at release-level.

**Scope-tightening.** Cycle 3's AC is "Ruby/Rails adapter populates the banded contract from a real Rails codebase." Cycle 4's AC is "Python/Flask adapter does the same; both fixtures ship; end-to-end smoke runs against both." Strictly tighter — releases the gate to v0.1.9.

**Independent fence.** Single-component fence on `plugins/dev-sdlc/odd-extractor/`. The Python adapter lands in `plugins/dev-sdlc/odd-extractor/lang/python/`; fixtures land in `plugins/dev-sdlc/odd-extractor/tests/fixtures/python-flask-payment/` and `plugins/dev-sdlc/odd-extractor/tests/fixtures/ruby-rails-payment/`.

**AC family seed: AC.PYTHON.* + AC.FIXTURES.* (Python adapter + smoke fixtures).**
- AC.PYTHON.1 — Python AST adapter at `plugins/dev-sdlc/odd-extractor/lang/python/` uses Python's stdlib `ast` module (no external dep needed for AST).
- AC.PYTHON.2 — Python-idiom recognisers: Flask route declarations, SQLAlchemy / Django models, Pydantic schemas, pytest test functions, Celery tasks.
- AC.PYTHON.3 — Test-first extraction: pytest functions → candidate VERIFIED ACs.
- AC.PYTHON.4 — Slice-and-swarm: same shape as Ruby (Cycle 3); shared aggregator code where possible (DRY across adapters).
- AC.PYTHON.5 — Confidence band rules per Python idiom: model schema → PLAUSIBLE; passing test → VERIFIED; LLM-inferred → HYPOTHESISED.
- AC.FIXTURES.1 — `tests/fixtures/python-flask-payment/` is a small but realistic Flask payment app (5–10 routes, SQLAlchemy models, ≥10 pytest tests, README).
- AC.FIXTURES.2 — `tests/fixtures/ruby-rails-payment/` is a small but realistic Rails payment app (5–10 routes, ActiveRecord models with callbacks + concerns, polymorphic association, Sidekiq job, ≥10 RSpec tests, README).
- AC.FIXTURES.3 — End-to-end smoke: `loam odd-extract tests/fixtures/python-flask-payment` and `loam odd-extract tests/fixtures/ruby-rails-payment` both produce confidence-banded contract drafts; ≥3 VERIFIED, ≥5 PLAUSIBLE, ≥2 HYPOTHESISED per fixture (band distribution sanity-checks the schema).
- AC.FIXTURES.4 — Eric-ratification workflow runs end-to-end on Ruby-Rails fixture (the canonical Eric path).
- AC.FIXTURES.5 — Both fixtures are committed real repos (not git submodules); LICENSE permissive.

**Smoke dimensions exercised.**
- D1 cold-state ✓ — fresh extraction against both fixtures.
- D2 steady-state ✓ — incremental re-run against both fixtures stable.
- D5 cross-session ✓ — partial extraction state survives `/clear`.
- D6 telemetry-floor ✓ — per-fixture audit log entries.
- D3 / D4 inherited.

**Dependency on prior cycles.** Cycles 1+2+3 (scaffold + bands + Ruby adapter; the Ruby fixture exists for Cycle 3 to test against, but the canonical fixture lands in Cycle 4 — Cycle 3 uses synthetic Ruby snippets internally).

**Out-of-scope deferrals.**
- Continuous codebase-watch → v0.2.0.
- Eric's actual Rails codebase → v0.2.1 (fresh-user smoke).

**AI-time band.** **6–10 h** (Python adapter mirrors Ruby skeleton, faster; fixture authoring is the bulk; end-to-end smoke).

---

### Cycle 5 — dev-sdlc skill-ification first pass (6 SKILLs)

**Theme.** Six high-leverage dev-sdlc SKILLs ship. Per layered-skills §5: chosen by AI-time + dependency on existing CDCs/conventions.

**Scope-tightening.** Cycles 1–4 ship the extractor. Cycle 5's AC is "six dev-sdlc SKILLs are auto-discovered + invokable in canonical pos-v2." Independent of extractor work; could land in parallel at plan-author stage but serializes at build-time per `feedback_serialize_amendment_builds`.

**Independent fence.** Single-component fence on `plugins/dev-sdlc/`. No edits to `framework/`.

**AC family seed: AC.SKILLS-DSDLC1.* (dev-sdlc skills first pass).**
- AC.SKILLS-DSDLC1.1 — `loam-amend-cycle` SKILL.md authored at `plugins/dev-sdlc/skills/loam-amend-cycle/`; frontmatter valid (name, description ≤ 1024 chars, model: inherit, tools: inherit); body covers the full amendment cycle ritual (plan → manifest → apply → seal → backfill).
- AC.SKILLS-DSDLC1.2 — `dispatch-brief-authoring` SKILL.md authored; body covers the dispatch-brief sections + the principle-application footer + halt triggers.
- AC.SKILLS-DSDLC1.3 — `plan-before-code-author` SKILL.md authored; body covers the ODD-shaped plan-doc skeleton (objectives + ACs + halt triggers + smoke + bookkeeping).
- AC.SKILLS-DSDLC1.4 — `fidraft-capture` SKILL.md authored; body covers the FUTURE_IDEAS_DRAFT.md capture format (entry shape, provenance, composes-with line).
- AC.SKILLS-DSDLC1.5 — `front-load-principle-walk` SKILL.md authored; body covers the turn-start principle re-citation ritual.
- AC.SKILLS-DSDLC1.6 — `audit-finding-triage` SKILL.md authored; body covers the audit-block surface-when-meaningful logic + finding-categorisation taxonomy.
- AC.SKILLS-DSDLC1.7 — All 6 SKILLs auto-discoverable in canonical pos-v2 via the layered-skill discovery mechanism (sealed v0.1.7 Cycle 3 at `bcf699a`); live `/` menu shows them.
- AC.SKILLS-DSDLC1.8 — Each SKILL has a regression test (existence + frontmatter validation + content-marker grep).

**Smoke dimensions exercised.**
- D1 cold-state ✓ — fresh canonical workspace shows all 6 SKILLs in `/` menu.
- D5 cross-session ✓ — SKILLs visible after `/clear`.
- D2 / D3 / D4 / D6 inherited from layered-skill discovery (sealed v0.1.7).

**Dependency on prior cycles.** None within v0.1.8 (parallelizable at plan-author; serializes at build per `feedback_serialize_amendment_builds`). Depends on v0.1.7 Cycle 3 (layered-skill discovery mechanism).

**Out-of-scope deferrals.**
- Six second-pass SKILLs → v0.1.9 (per layered-skills §5).

**AI-time band.** **8–12 h** (~1–2 h per SKILL plus tests; 6 SKILLs).

---

### Cycle dependency diagram

```
Cycle 1 (extractor scaffold) ──┐
                               │
Cycle 2 (bands + ratification) ◄┘
   │
   ▼
Cycle 3 (Ruby/Rails adapter) ──┐
                               │
Cycle 4 (Python adapter +     ◄┘
         fixtures + e2e smoke)
   │
   ▼
[v0.1.8 release-level smoke; HARD gate per Decision R]
   │
   ▼
v0.1.9 (PR-safety gate)


Cycle 5 (6 SKILLs) — independent at plan-author; serializes at build-time.
                     Can land any time after Cycle 1's component scaffold lands
                     (since it's a different component; no fence collision).
```

**Recommended build order.** Cycle 1 → Cycle 2 → Cycle 3 → Cycle 4 → Cycle 5. Cycle 5 could land between any two extractor cycles if dispatcher prefers to interleave for variety, but the skills land last by default to respect "extractor is the headline; skills are the supporting cast."

---

## §4 — Per-cycle dispatch briefs

Each brief below is the dispatcher's verbatim-or-near-verbatim hand-off to the build agent. Embed a complete brief; sections match the existing build-dispatch shape.

### Cycle 1 dispatch brief — odd-extractor scaffolding

```
# v0.1.8 Cycle 1 build dispatch — odd-extractor scaffolding (NEW component)

Working directory: /Users/lukeivers/ivers-corp-pos-v2/ (canonical pos-v2). NOT pos3.

## Principles to apply at turn-start

- CHANNEL — replies route to dispatcher's stop-hook channel (NOT Telegram from this dispatch).
- AUTONOMY — settle decisions yourself; only flag genuinely-critical / public-action / financial.
- F2 RUTHLESS FEEDBACK — name disagreements / scope compromises / quality gaps immediately.
- LOCKED-DESIGN-NOT-LICENSE — master plan + Eric synthesis revisitable; surface counter-evidence.
- PROMISES > IN-MOMENT JUDGMENT — quality bar is non-negotiable. Extractor is COMPLETE, not partial.
- ODD §2.5 — every line of code/branch/test maps to a named AC.OREK.* AC.
- WD-IN-DISPATCHES — confirm at start.
- PARTITION RULE — odd-extractor lives at `plugins/dev-sdlc/odd-extractor/` per Decision A.
- PLAN-BEFORE-CODE — write the cycle plan-doc BEFORE code.
- POS-AMEND BOOKKEEPING — every component change uses `pos-amend apply` (NOT --amend).
- SCOPE-ONLY — this brief carries scope only; method (which AST library, which test names, commit prose) is yours.
- NEW-SCHEMA — manifest YAML uses schema v3 (`plan_doc_ref:`, no `amendment.number`); seal commit short-form.

## QUALITY BAR

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

- Every release-note promise corresponds to tested + reliable behavior.
- The extractor scaffold ships COMPLETE — four-stage workflow, registry, dry-run, budget envelope all work.
- If any AC ships partial, halt and surface BEFORE proceeding.

## Source pointers

- Master plan: `docs/rebuild/plans/v0-1-8-master-plan.md` — §3 Cycle 1 scope.
- Eric synthesis: `docs/rebuild/plans/eric-final-delivery-plan-2026-05-04.md` §2 v0.1.8 row.
- ODD-RE research: `<pos3-workspace>/.scratch/claude-output/odd-reverse-engineering-skill-research.md` (D-Q.RE.{1..8} sub-decisions; method-level guidance for AST/budget/output-shape).
- Smoke discipline: `plugins/dev-sdlc/docs/smoke-test-discipline.md` — six dimensions.

## Sub-plan path

Author at: `docs/rebuild/plans/v0-1-8-cycle-1-odd-extractor-scaffolding.md`
Manifest at: `docs/rebuild/plans/v0-1-8-cycle-1-odd-extractor-scaffolding.manifest.yaml` (schema v3; plan_doc_ref pointing at the plan-doc)
Status file: `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-8-cycle-1-status-2026-05-04.md`

## Fence

Single-component fence — NEW component:

- `plugins/dev-sdlc/odd-extractor/` (NEW)

Composes (read-only) with `framework/cost-governance/` for dry-run primitive callout. No edits to other components.

## Acceptance criteria

Author the AC ladder during plan-doc time. Spec-level seeds (you tighten + name in plan-doc):

- AC.OREK.1 — component scaffold present (component.md, tests/, src/, seals/, SEAL_COMMIT sidecar).
- AC.OREK.2 — `loam odd-extract <repo-path>` CLI; dry-run default per Decision D; `--live` opt-in.
- AC.OREK.3 — Four-stage workflow (init / analyze / generate / verify) with structured artefacts per stage.
- AC.OREK.4 — Language-adapter registry; ships zero adapters; binding test verifies registry loads.
- AC.OREK.5 — Dry-run cost estimate via cost-governance primitive.
- AC.OREK.6 — Foreign-codebase budget envelope with `--budget-override` opt-in.
- AC.OREK.7 — Component-level test surface.

## Smoke (REALISTIC CONDITION — applicable dimensions per smoke-test-discipline.md)

- D1 cold-state: fresh canonical workspace runs `loam odd-extract <fixture-stub>` end-to-end; produces empty contract draft.
- D5 cross-session: extraction artefacts at `<workspace>/.loam/extractions/<repo-id>/` survive `/clear`; resume works.
- D6 telemetry-floor: per-extraction-run audit log entry.
- D2 / D3 / D4: n/a per cycle scope (extractor is invoked-on-demand, not a long-running daemon); document n/a in plan-doc.

## Halt triggers

- WD drifts → halt + surface.
- Plan-doc not authored before code → halt.
- Any AC fails the partial-feature test (would ship partial) → halt + reframe.
- 6-dimension smoke fails on D5 cross-session → halt (this is the ship-test for cross-session continuity).
- Cycle exceeds 5 hours wall-clock → halt with partial findings; consider further decomposition (e.g., split CLI from registry).
- ODD violations discovered in surrounding code → halt + surface; do not silently extend.
- More than 5 in-build decisions need Luke escalation → halt + describe.

## Out of scope

- Confidence bands → Cycle 2.
- Ruby/Rails adapter → Cycle 3.
- Python adapter → Cycle 4.
- 6 SKILLs → Cycle 5.
- Continuous codebase-watch → v0.2.0.

## Bookkeeping

- pos-amend apply (NOT --amend); create NEW commits if a file is missed.
- Single semantic commit per cycle (manifest+apply merged per schema v3 AC.DPS1.6).
- Backfill `docs/rebuild/plans/v0-1-x-roadmap.md` §8 method-decision register row for v0.1.8 Cycle 1.
- Backfill `docs/rebuild/plans/eric-final-delivery-plan-2026-05-04.md` §2 v0.1.8 progress notes after seal.
- DO NOT push tags until v0.1.8 release-level smoke green AND Luke gates the release.

## Model rationale

(none — Sonnet is the default for sealed-component amendment build.)
```

### Cycle 2 dispatch brief — Confidence bands + ratification workflow

```
# v0.1.8 Cycle 2 build dispatch — Confidence bands + ratification workflow

Working directory: /Users/lukeivers/ivers-corp-pos-v2/ (canonical pos-v2). NOT pos3.

## Principles to apply at turn-start

- CHANNEL — replies route to dispatcher (NOT Telegram).
- AUTONOMY — settle decisions; flag only critical/public/financial.
- F2 RUTHLESS FEEDBACK — name gaps + design tensions immediately.
- LOCKED-DESIGN-NOT-LICENSE — band schema revisitable; surface a better shape if discovered.
- PROMISES > IN-MOMENT JUDGMENT — quality bar non-negotiable.
- ODD §2.5 — every line maps to a named AC.BANDS.* AC.
- WD-IN-DISPATCHES — confirm at start.
- PARTITION RULE — extractor schema in odd-extractor; PM integration in `framework/per-project-pm/`.
- PLAN-BEFORE-CODE — write the cycle plan-doc BEFORE code.
- POS-AMEND BOOKKEEPING — pos-amend apply (NOT --amend); two-component manifest per fence.
- SCOPE-ONLY — method (schema YAML shape, ratification CLI prose) is yours.
- NEW-SCHEMA — manifest v3.
- SOC-2 FLOOR — every ratification action audit-logged per Decision P.
- ONE-QUESTION-AT-A-TIME — ratification batch surfaces through PM per Decision Q.

## QUALITY BAR

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

- Every band promise tested.
- Ratification workflow runs end-to-end (no half-ratification).
- Audit log is SOC-2 compliant.

## Source pointers

- Master plan: `docs/rebuild/plans/v0-1-8-master-plan.md` — §3 Cycle 2 scope.
- Eric synthesis Decision I (PLAUSIBLE→VERIFIED default-no), Decision P (SOC-2 floor), Decision Q (one-question-at-a-time).
- Cycle 1's plan-doc + seal SHA (predecessor).
- v0.1.7 Cycle 4 PM integration: `framework/per-project-pm/` (decision-queue.yaml shape).
- ODD-methodology doc: `plugins/dev-sdlc/docs/odd-methodology.md` (target for the band-schema extension).

## Sub-plan path

Author at: `docs/rebuild/plans/v0-1-8-cycle-2-bands-and-ratification.md`
Manifest at: `docs/rebuild/plans/v0-1-8-cycle-2-bands-and-ratification.manifest.yaml`
Status file: `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-8-cycle-2-status-2026-05-04.md`

## Fence

Two-component fence (manifest names both):

- `plugins/dev-sdlc/odd-extractor/` (band schema + ratification subpackage)
- `framework/per-project-pm/` (PM-side ratification batch + decision-queue integration)

## Acceptance criteria

Author the AC ladder during plan-doc time. Seeds:

- AC.BANDS.1 — Each AC carries `confidence:` + `evidence:` block.
- AC.BANDS.2 — VERIFIED requires passing test pinned; PLAUSIBLE requires source citation; HYPOTHESISED requires LLM rationale.
- AC.BANDS.3 — Schema documented in `plugins/dev-sdlc/docs/odd-methodology.md` extension.
- AC.BANDS.4 — Ratification CLI: `loam odd-extract ratify <contract-draft>`; PM-mediated batch.
- AC.BANDS.5 — PLAUSIBLE→VERIFIED requires owner explicit yes per Decision I.
- AC.BANDS.6 — Audit log per ratification action (SOC-2 floor).
- AC.BANDS.7 — PM integration: ratification batches → decision-queue.yaml; one-question-at-a-time.

## Smoke

- D1 cold-state: synthetic banded contract → ratify → audit log entries observable.
- D5 cross-session: partial ratification batch resumable across `/clear`.
- D6 telemetry-floor: audit log per ratification action.
- D2 / D3 / D4: inherited from Cycle 1.

## Halt triggers

- Cycle 1 not sealed → halt (predecessor required).
- Plan-doc not authored before code → halt.
- Two-component fence breaks `feedback_serialize_amendment_builds` (e.g., concurrent build agent on either component) → halt.
- Cycle exceeds 5 hours wall-clock → halt with partial findings.
- ODD violations in surrounding code → halt + surface.
- Audit log shape conflicts with M-FBM convention → halt + RF the conflict.
- More than 5 escalations needed → halt + describe.

## Out of scope

- Actual language extraction → Cycles 3+4.
- Test-first extraction → Cycles 3+4.
- 6 SKILLs → Cycle 5.

## Bookkeeping

- pos-amend apply with two-component manifest.
- Backfill v0.1.x-roadmap §8 + eric-final-delivery §2 progress notes.
- DO NOT push tags until release-level smoke green.

## Model rationale

(none — Sonnet default.)
```

### Cycle 3 dispatch brief — Ruby/Rails first-class adapter

```
# v0.1.8 Cycle 3 build dispatch — Ruby/Rails first-class adapter

Working directory: /Users/lukeivers/ivers-corp-pos-v2/ (canonical pos-v2). NOT pos3.

## Principles to apply at turn-start

- CHANNEL — replies route to dispatcher (NOT Telegram).
- AUTONOMY — settle decisions; flag only critical/public/financial.
- F2 RUTHLESS FEEDBACK — name disagreements / quality gaps immediately. Especially for AST library choice.
- LOCKED-DESIGN-NOT-LICENSE — Decision O (Ruby first-class) is the locked design; revisit only if Ruby AST integration proves infeasible (halt-trigger below).
- PROMISES > IN-MOMENT JUDGMENT — quality bar non-negotiable. Ruby/Rails is COMPLETE — no thin grep fallback.
- ODD §2.5 — every line maps to a named AC.RAILS.* AC.
- WD-IN-DISPATCHES — confirm at start.
- PARTITION RULE — Ruby adapter at `plugins/dev-sdlc/odd-extractor/lang/ruby/`.
- PLAN-BEFORE-CODE — write the cycle plan-doc BEFORE code.
- POS-AMEND BOOKKEEPING — pos-amend apply (NOT --amend).
- SCOPE-ONLY — method (which AST library, which Rails version targets) is yours; surface choice in plan-doc.
- NEW-SCHEMA — manifest v3.
- SWARMING (Lens 5) — slice-and-swarm for SaaS-app scale; named in AC.RAILS.4.
- TEST-FIRST EXTRACTION — passing tests → VERIFIED ACs per Eric G1.

## QUALITY BAR

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

- Ruby AST integration is real (deterministic AST lib; not regex or grep).
- Rails idioms (ActiveRecord, callbacks, concerns, polymorphic, Sidekiq) ALL recognised — no "later".
- Test-first works: existing RSpec tests → VERIFIED ACs.
- Slice-and-swarm scales to SaaS-app codebases.

## Source pointers

- Master plan: `docs/rebuild/plans/v0-1-8-master-plan.md` — §3 Cycle 3 scope.
- Eric synthesis Decision O (Ruby first-class +8–16 h adder).
- Eric SaaS-app research §11.3 (the original "thin Ruby fallback" doubt that Decision O addresses).
- Cycle 1+2 plan-docs + seal SHAs.
- ODD-RE research D-Q.RE.{1..8} (method-level guidance: AST library choice; output-shape; budget; coverage-gap surface).
- Lens 5 (swarming): `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_swarming_recursive_decomposition.md`.

## Sub-plan path

Author at: `docs/rebuild/plans/v0-1-8-cycle-3-ruby-rails-adapter.md`
Manifest at: `docs/rebuild/plans/v0-1-8-cycle-3-ruby-rails-adapter.manifest.yaml`
Status file: `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-8-cycle-3-status-2026-05-04.md`

## Fence

Single-component fence on `plugins/dev-sdlc/odd-extractor/`. The Ruby adapter lands in `plugins/dev-sdlc/odd-extractor/lang/ruby/`.

## Acceptance criteria

Seeds:

- AC.RAILS.1 — Ruby AST adapter parses Ruby via deterministic AST lib (you choose; surface in plan-doc).
- AC.RAILS.2 — Rails-idiom recognisers: ActiveRecord migrations + callbacks + concerns + polymorphic associations + ActiveJob/Sidekiq + routes.
- AC.RAILS.3 — Test-first extraction: every passing RSpec/Minitest → candidate VERIFIED AC.
- AC.RAILS.4 — Slice-and-swarm: codebase exceeding budget ceiling sliced + swarmed; aggregator merges.
- AC.RAILS.5 — End-to-end Eric-ratification on Ruby-Rails fixture (fixture lands in Cycle 4; this AC pins the contract for that smoke).
- AC.RAILS.6 — Confidence band rules per idiom (schema → PLAUSIBLE; passing test → VERIFIED; LLM-inferred → HYPOTHESISED).
- AC.RAILS.7 — Cost-governance dry-run; budget envelope respected.
- AC.RAILS.8 — Adapter unit tests against synthetic Rails snippets.

## Smoke

- D1 cold-state: adapter against synthetic Rails snippet → banded ACs.
- D2 steady-state: incremental re-run idempotent.
- D5 cross-session: extraction state survives `/clear`; resume mid-slice.
- D6 telemetry-floor: per-slice audit log entries.
- D3 / D4: inherited.

## Halt triggers

- Cycle 1 + 2 not sealed → halt.
- Ruby AST library integration infeasible within ~5 h plan-author + first-pass implementation → halt + surface; recommend split into Cycle 3.a (AST + 3 idioms) + Cycle 3.b (concerns + polymorphic + Sidekiq + slice-and-swarm).
- Slice-and-swarm aggregator produces inconsistent banded output across slices → halt.
- Cycle exceeds 8 hours wall-clock with no clear progress on Rails idioms → halt + RF.
- ODD violations in surrounding code → halt + surface.
- More than 5 escalations needed → halt + describe.

## Out of scope

- Python adapter → Cycle 4.
- Full Ruby-Rails-payment fixture + e2e smoke → Cycle 4.
- 6 SKILLs → Cycle 5.
- Continuous codebase-watch → v0.2.0.

## Bookkeeping

- pos-amend apply.
- Backfill v0.1.x-roadmap §8 + eric-final-delivery §2.
- DO NOT push tags.

## Model rationale

(none — Sonnet default for sealed-component amendment build.)
```

### Cycle 4 dispatch brief — Python first-class adapter + smoke fixtures

```
# v0.1.8 Cycle 4 build dispatch — Python first-class adapter + smoke fixtures

Working directory: /Users/lukeivers/ivers-corp-pos-v2/ (canonical pos-v2). NOT pos3.

## Principles to apply at turn-start

- CHANNEL — replies route to dispatcher (NOT Telegram).
- AUTONOMY — settle decisions; flag only critical/public/financial.
- F2 RUTHLESS FEEDBACK — name DRY opportunities across Python/Ruby adapters; surface where shared aggregator code emerges.
- LOCKED-DESIGN-NOT-LICENSE — band schema + slice-and-swarm shape established in Cycles 2+3 are locked; revisit only if a fixture surfaces a contradiction.
- PROMISES > IN-MOMENT JUDGMENT — both fixtures must run e2e; no "Python works, Ruby fixture is a stub."
- ODD §2.5 — every line maps to AC.PYTHON.* or AC.FIXTURES.*.
- WD-IN-DISPATCHES — confirm at start.
- PARTITION RULE — Python adapter at `plugins/dev-sdlc/odd-extractor/lang/python/`; fixtures at `plugins/dev-sdlc/odd-extractor/tests/fixtures/`.
- PLAN-BEFORE-CODE — write the cycle plan-doc BEFORE code.
- POS-AMEND BOOKKEEPING — pos-amend apply (NOT --amend).
- SCOPE-ONLY — method (Python AST module choice; fixture content shapes) is yours.
- NEW-SCHEMA — manifest v3.
- TEST-FIRST EXTRACTION — pytest tests → VERIFIED ACs.

## QUALITY BAR

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

- Python adapter ships first-class (not a thin port of Ruby).
- Both fixtures real, runnable, tested.
- End-to-end smoke against both fixtures: extractor → bands → ratification → audit log.

## Source pointers

- Master plan: `docs/rebuild/plans/v0-1-8-master-plan.md` — §3 Cycle 4 scope.
- Eric synthesis Decision F (two fixtures).
- Eric synthesis G9 (language-agnostic skeleton + Python first-class).
- Cycle 1+2+3 plan-docs + seal SHAs.

## Sub-plan path

Author at: `docs/rebuild/plans/v0-1-8-cycle-4-python-adapter-and-fixtures.md`
Manifest at: `docs/rebuild/plans/v0-1-8-cycle-4-python-adapter-and-fixtures.manifest.yaml`
Status file: `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-8-cycle-4-status-2026-05-04.md`

## Fence

Single-component fence on `plugins/dev-sdlc/odd-extractor/`. Python adapter at `lang/python/`; fixtures at `tests/fixtures/python-flask-payment/` + `tests/fixtures/ruby-rails-payment/`.

## Acceptance criteria

Seeds:

- AC.PYTHON.1 — Python AST adapter using stdlib `ast` module.
- AC.PYTHON.2 — Python-idiom recognisers: Flask routes, SQLAlchemy/Django models, Pydantic schemas, pytest tests, Celery tasks.
- AC.PYTHON.3 — Test-first extraction.
- AC.PYTHON.4 — Slice-and-swarm (shared aggregator with Ruby).
- AC.PYTHON.5 — Confidence band rules per idiom.
- AC.FIXTURES.1 — `tests/fixtures/python-flask-payment/` realistic Flask payment app.
- AC.FIXTURES.2 — `tests/fixtures/ruby-rails-payment/` realistic Rails payment app.
- AC.FIXTURES.3 — End-to-end smoke: both fixtures produce banded contract drafts; band distribution sanity-checks (≥3 VERIFIED, ≥5 PLAUSIBLE, ≥2 HYPOTHESISED per fixture).
- AC.FIXTURES.4 — Eric-ratification e2e on Ruby-Rails fixture.
- AC.FIXTURES.5 — Both fixtures committed real repos (LICENSE permissive).

## Smoke

- D1 cold-state: fresh extraction against both fixtures.
- D2 steady-state: incremental re-run stable.
- D5 cross-session: partial extraction state survives `/clear`.
- D6 telemetry-floor: per-fixture audit log entries.
- D3 / D4: inherited.

## Halt triggers

- Cycles 1+2+3 not sealed → halt.
- Either fixture fails the band-distribution sanity check (≥3 VERIFIED etc.) → halt + RF the schema.
- DRY opportunity ignored (Python and Ruby adapters duplicate aggregator code) → halt + refactor + surface.
- Cycle exceeds 5 hours wall-clock → halt with partial findings.
- ODD violations → halt + surface.
- More than 5 escalations → halt.

## Out of scope

- Continuous codebase-watch → v0.2.0.
- Eric's actual Rails codebase → v0.2.1 fresh-user smoke.

## Bookkeeping

- pos-amend apply.
- Backfill v0.1.x-roadmap §8 + eric-final-delivery §2.
- DO NOT push tags.

## Model rationale

(none — Sonnet default.)
```

### Cycle 5 dispatch brief — dev-sdlc skill-ification first pass (6 SKILLs)

```
# v0.1.8 Cycle 5 build dispatch — dev-sdlc skill-ification first pass (6 SKILLs)

Working directory: /Users/lukeivers/ivers-corp-pos-v2/ (canonical pos-v2). NOT pos3.

## Principles to apply at turn-start

- CHANNEL — replies route to dispatcher (NOT Telegram).
- AUTONOMY — settle decisions; flag only critical/public/financial.
- F2 RUTHLESS FEEDBACK — name SKILL-shape gaps; SKILL bodies reflect actual ritual, not aspirational shape.
- LOCKED-DESIGN-NOT-LICENSE — six-SKILL list is from layered-skills §5; revisit only if one is clearly redundant after Cycles 1–4 reveal scope.
- PROMISES > IN-MOMENT JUDGMENT — six SKILLs ship; no "five plus a sixth in v0.1.9."
- ODD §2.5 — every line maps to AC.SKILLS-DSDLC1.* AC.
- WD-IN-DISPATCHES — confirm at start.
- PARTITION RULE — six SKILLs at `plugins/dev-sdlc/skills/<name>/SKILL.md`.
- PLAN-BEFORE-CODE — write the cycle plan-doc BEFORE code.
- POS-AMEND BOOKKEEPING — pos-amend apply (NOT --amend).
- SCOPE-ONLY — method (SKILL body length, examples count) is yours.
- NEW-SCHEMA — manifest v3.

## QUALITY BAR

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

- Each SKILL body covers the FULL ritual — not a stub.
- All 6 auto-discovered in canonical pos-v2 (live `/` menu shows them).
- Each SKILL has a regression test.

## Source pointers

- Master plan: `docs/rebuild/plans/v0-1-8-master-plan.md` — §3 Cycle 5 scope.
- Layered-skills research §5 (12 candidate SKILLs; first 6 here).
- v0.1.7 Cycle 3 layered-skill discovery mechanism (`bcf699a`).
- Existing SKILLs in `plugins/loam-skills/skills/` for shape reference.

## Sub-plan path

Author at: `docs/rebuild/plans/v0-1-8-cycle-5-dev-sdlc-skills-pass-1.md`
Manifest at: `docs/rebuild/plans/v0-1-8-cycle-5-dev-sdlc-skills-pass-1.manifest.yaml`
Status file: `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-8-cycle-5-status-2026-05-04.md`

## Fence

Single-component fence on `plugins/dev-sdlc/`. Six new SKILL.md packages at `plugins/dev-sdlc/skills/<name>/SKILL.md`.

## Acceptance criteria

Seeds:

- AC.SKILLS-DSDLC1.1 — `loam-amend-cycle` SKILL.md (frontmatter + body covers plan→manifest→apply→seal→backfill).
- AC.SKILLS-DSDLC1.2 — `dispatch-brief-authoring` SKILL.md (sections + principle footer + halt triggers).
- AC.SKILLS-DSDLC1.3 — `plan-before-code-author` SKILL.md (ODD-shaped plan skeleton).
- AC.SKILLS-DSDLC1.4 — `fidraft-capture` SKILL.md (entry shape + provenance + composes-with).
- AC.SKILLS-DSDLC1.5 — `front-load-principle-walk` SKILL.md (turn-start ritual).
- AC.SKILLS-DSDLC1.6 — `audit-finding-triage` SKILL.md (surface-when-meaningful + categorisation).
- AC.SKILLS-DSDLC1.7 — All 6 auto-discoverable via layered-skill mechanism.
- AC.SKILLS-DSDLC1.8 — Regression test per SKILL.

## Smoke

- D1 cold-state: fresh canonical workspace shows all 6 SKILLs in `/` menu.
- D5 cross-session: SKILLs visible after `/clear`.
- D2 / D3 / D4 / D6: inherited from layered-skill discovery.

## Halt triggers

- v0.1.7 Cycle 3 (layered-skill discovery) not sealed → halt.
- Plan-doc not authored before code → halt.
- Any SKILL frontmatter invalid → halt.
- Any SKILL body is a stub or aspirational placeholder → halt + RF.
- Live `/` menu fails to show any of the 6 → halt (this is the ship-test).
- Cycle exceeds 6 hours wall-clock → halt + describe.

## Out of scope

- Six second-pass SKILLs → v0.1.9.
- Auto-creation mechanism → v0.2.0.
- Promotion rubric → v0.2.1.

## Bookkeeping

- pos-amend apply.
- Backfill v0.1.x-roadmap §8 + eric-final-delivery §2.
- DO NOT push tags.

## Model rationale

(none — Sonnet default.)
```

---

## §5 — Release-level smoke

Per Decision R: HARD smoke gate at v0.1.8 (load-bearing release). All 6 dimensions exercised at release-level, not just per-cycle.

**End-to-end smoke shape.**

After Cycle 5 seals, the dispatcher runs a release-level smoke pass against canonical pos-v2 covering the full v0.1.8 surface:

1. **D1 cold-state.** Fresh canonical workspace clone. `loam init` + dependencies. Run:
   - `loam odd-extract plugins/dev-sdlc/odd-extractor/tests/fixtures/python-flask-payment` → produces banded contract draft; ≥3 VERIFIED.
   - `loam odd-extract plugins/dev-sdlc/odd-extractor/tests/fixtures/ruby-rails-payment` → produces banded contract draft; ≥3 VERIFIED.
   - `loam odd-extract ratify <ruby-rails-contract>` → PM-mediated ratification batch; promote ≥1 PLAUSIBLE → VERIFIED with explicit yes.
   - `/` menu shows all 6 dev-sdlc SKILLs.

2. **D2 steady-state.** Re-run extraction against the same fixtures incrementally; output stable; no queue/log growth.

3. **D3 restart.** Mid-extraction `kill -TERM` the extraction process; supervisor restarts (or operator re-invokes); resume from last checkpoint.

4. **D4 reboot.** macOS reboot (or simulated equivalent — `launchctl bootout` + `launchctl bootstrap` for memory-system worker which is the long-running process; extractor itself is invoked-on-demand). Post-reboot: extraction artefacts at `<workspace>/.loam/extractions/` survive; resume works.

5. **D5 cross-session.** Most-load-bearing dimension. Session A: start extraction → produce partial contract → end. Session B (fresh `claude`): resume same extraction → completes; banded output identical (modulo time-stamp drift).

6. **D6 telemetry-floor.** Audit log entries per extraction-run, per ratification action, per slice in slice-and-swarm. Absence detectable.

**End-to-end "the path Eric will walk" smoke.**

Point the extractor at a real Rails project (NOT Eric's actual codebase yet — public OSS Rails-payment-shape repo, e.g. solidus/spree/jumpstart-pro-clone — to be selected at v0.1.8 release-time):

- Step 1: `loam odd-extract <repo>` → confidence-banded contract draft produced.
- Step 2: `loam odd-extract ratify <draft>` → PM-mediated ratification batch surfaces one question at a time.
- Step 3: ≥3 VERIFIED ACs anchored to passing RSpec tests; ≥5 PLAUSIBLE ACs anchored to ActiveRecord/concerns/etc.; ≥2 HYPOTHESISED ACs anchored to LLM-inferred behaviour.
- Step 4: Audit log reflects every action.
- Step 5: All 6 dev-sdlc SKILLs auto-discovered.

**Gate to v0.1.9.**

v0.1.8 release-level smoke green on all 6 dimensions on canonical pos-v2 → `git tag v0.1.8` → DO NOT push tag until Luke gates the release.

---

## §6 — Open items for Luke

Three items. Architectural calls only.

1. **Real OSS Rails-payment-shape fixture for §5 release-level e2e smoke.** Cycle 4 ships the synthetic `tests/fixtures/ruby-rails-payment/` fixture. The §5 release-level e2e additionally points the extractor at a REAL public OSS Rails-payment-shape repo. Candidates Luke should rule on (or delegate to plan-author dispatch at release-time): solidus (Rails commerce framework), spree (Rails commerce framework), jumpstart-pro-clone (SaaS starter), or other. *Criticality:* medium — affects release-level smoke scope, not cycle scope. *Recommendation:* defer to v0.1.8 release-gate dispatch; choose by recency of last commit + permissive license + size that fits within budget envelope.

2. **Cycle 5 ordering relative to extractor cycles.** Recommended order: 1 → 2 → 3 → 4 → 5. Alternative: 1 → 5 → 2 → 3 → 4 (skills land early so they're available during extractor cycles for use by build agents themselves, e.g., `loam-amend-cycle` SKILL guides Cycles 2–4 builders). *Criticality:* low — cycle scopes are independent. *Recommendation:* default 1→2→3→4→5 to keep extractor as the headline focus; switch to 1→5→2→3→4 if dispatcher prefers tooling-first.

3. **Cycle 3 split-trigger threshold.** Cycle 3's halt-trigger names ~5 h wall-clock as the split-trigger for "Ruby AST integration infeasible." The parent §6.2 doubt names "60+ hours total" as the v0.1.8.a/v0.1.8.b split-trigger at the release level. The cycle-level threshold is more aggressive. *Criticality:* low — both thresholds are bands, not hard lines. *Recommendation:* keep cycle-level at ~5 h to preserve early halt; release-level at 60+ h covers the slow-creep failure mode. Both halt-triggers cite parent §6.2.

(No Decision R / Decision O / Decision Q escalations needed — all three already RESOLVED YES at parent §3.)

---

## §7 — Honest doubts (F2 RF on this decomposition)

The places this decomposition is least confident.

**7.1 — Cycle 3 (Ruby/Rails first-class) is the load-bearing risk.** 14–22 h is optimistic at the high end. Eric synthesis §6.2 already named v0.1.8 high-band as 70–80 h actual; if Cycle 3 alone hits 25–30 h, the master plan's 42–66 h band is wrong. *Mitigation:* Cycle 3 halt-trigger at ~5 h plan-author + first-pass implementation forces an early split (Cycle 3.a + Cycle 3.b) before sunk-cost dynamics dominate. The release-level v0.1.8.a / v0.1.8.b split-trigger remains available at 60+ h.

**7.2 — Slice-and-swarm aggregator is unproven.** Cycle 3's AC.RAILS.4 and Cycle 4's AC.PYTHON.4 share a slice-and-swarm aggregator. The aggregator must merge banded outputs from parallel slices without producing inconsistent confidence (e.g., one slice reports VERIFIED, another reports HYPOTHESISED for the same logical AC). *Mitigation:* Cycle 3's plan-doc must specify the aggregator's conflict-resolution rule (highest-band wins? evidence-richest wins? halt-on-conflict?). If the rule isn't obvious at plan-author time, surface as a decision in Cycle 3's plan-doc.

**7.3 — Cycle 2's PM integration may collide with v0.1.7's PM contract.** Cycle 2 extends `framework/per-project-pm/` with a ratification-batch shape. v0.1.7 Cycle 4 (`122a7c8`) sealed the one-question-at-a-time decision-queue. If the ratification-batch shape contradicts the decision-queue's existing shape, halt-and-surface per Cycle 2 dispatch. *Mitigation:* Cycle 2's plan-doc reads the v0.1.7 Cycle 4 sealed shape FIRST and explicitly extends rather than overrides.

**7.4 — Six SKILLs in Cycle 5 may be the wrong six.** Layered-skills §5 lists 12 candidates; the first-pass selection (loam-amend-cycle / dispatch-brief-authoring / plan-before-code-author / fidraft-capture / front-load-principle-walk / audit-finding-triage) was made before extractor cycles. After Cycles 1–4, one of the second-pass candidates (e.g., `seal-narrative-writer`, `hook-violation-recovery`) may turn out higher-leverage than one of the first-pass SKILLs. *Mitigation:* Cycle 5's plan-doc explicitly re-evaluates the first-six list against actual Cycles 1–4 ritual usage; if a swap is warranted, surface as a Cycle 5 decision (don't silently swap).

**7.5 — The "real OSS Rails repo" §5 release-level smoke fixture is not pre-selected.** §6 item 1 names the question; deferring it to release-time leaves a small gap where the e2e smoke fixture may not be available. *Mitigation:* if no real OSS Rails fixture is ruled by release-time, the synthetic Ruby-Rails-payment fixture from Cycle 4 covers the AC; the real-OSS smoke is the additional production-polish layer per Decision R quality bar. The release isn't blocked.

**7.6 — Confidence-band schema may evolve after Cycle 2 lands.** Cycle 2 ships the schema; Cycle 3+4 populate it; Cycle 5 references it via SKILLs. If Cycle 3 reveals a band the schema doesn't admit (e.g., "VERIFIED-by-property-test" needs a sub-distinction from "VERIFIED-by-spec"), schema churn surfaces late. *Mitigation:* Cycle 2's plan-doc explicitly future-proofs by allowing band-extension (additive enum + opt-in `confidence_subtype:` field) without schema-version bump.

**7.7 — `loam odd-extract` CLI vs persona-invocation semantics.** Cycle 1's AC.OREK.2 names a CLI entry point. The Eric path's actual user surface may not be the CLI — Eric may invoke extraction through the primary persona ("hey loam, extract our contract"). The CLI exists for scripting / CI integration; the persona-mediated invocation is the natural Eric surface. *Mitigation:* Cycle 1's plan-doc names BOTH surfaces (CLI for scripting; persona-tool for natural-language invocation). The persona-tool wraps the CLI.

**7.8 — Quality-bar absorption (20%) may be too low for v0.1.8.** Eric synthesis §6.2 named the same risk for the synthesis as a whole. v0.1.8 is the headline release with the most quality-sensitive surface (Eric reads the contract; Eric ratifies; Eric trusts the bands). 20% may underestimate; 40–50% may be the truth. *Mitigation:* log actuals after each cycle per `feedback_duration_estimation_rubric`; recalibrate after Cycle 1 + 2 (the lower-risk cycles) before Cycle 3 commits.

---

## §8 — Provenance trail

- **Master plan source authority:** `docs/rebuild/plans/eric-final-delivery-plan-2026-05-04.md` §2 v0.1.8 row + Decision O + Decision F.
- **Layered-skills first-pass list:** `docs/rebuild/plans/layered-skill-story-research-2026-05-04.md` §5 + parent §2 v0.1.8 row.
- **ODD-RE research:** `<pos3>/workspace/.scratch/claude-output/odd-reverse-engineering-skill-research.md` (907 lines; D-Q.RE.{1..8} method-level guidance).
- **FIDRAFT V11.C entry:** `docs/rebuild/FUTURE_IDEAS_DRAFT.md` (search "ODD-reverse-engineering"; defers heavy V11.C to v0.1.4+ — now realised at v0.1.8).
- **Smoke-test discipline:** `plugins/dev-sdlc/docs/smoke-test-discipline.md` (six-dimension spec; HARD-gate framing per Decision R).
- **Quality bar (Luke directive 2026-05-04):** parent §1 verbatim + parent §3 Decision R.
- **Eric stack context (Rails, SOC 2, one-question-at-a-time):** parent §1 + parent §3 Decisions P + Q.
- **v0.1.6 + v0.1.7 sealed predecessors:** parent §2 v0.1.6 / v0.1.7 rows + commit SHAs (3f1d237 / 88674cb / 3aa20dd / 73505f0 / bcf699a / 122a7c8).
- **Schema v3 + seal-narrative compression:** dev-pattern-simplifications-1 sealed at `019cfca`; dev-pattern-simplifications-2 sealed at `df3f50f`.
- **Lens 5 (swarming) reference:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_swarming_recursive_decomposition.md` + framework/CLAUDE.md Lens 5.
- **Decision R HARD-gate framing:** parent §3 + smoke-test-discipline.md §2.

---

## §9 — Method-decision register (per-cycle SHA backfill table)

(Reserved; build agents backfill on cycle-seal.)

| Cycle | Status | Apply SHA | Seal SHA | Notes |
|---|---|---|---|---|
| Cycle 1 — odd-extractor scaffolding | sealed | `9637b58` | `c1abda1` | NEW sub-package `plugins/dev-sdlc/odd-extractor/`. Plan-doc `e3a20b3`; source-edit BASELINE `b33a0dc`. AC.OREK.{1..7} all green; 56 tests pass. D1+D2-idempotency+D5+D6 smoke exercised; D3/D4 n/a (one-shot CLI). |
| Cycle 2 — bands + ratification | sealed | `96bacfe` | `4865028` | Two-component fence (dev-sdlc + per-project-pm). Plan-doc `8f97d64`; source-edit BASELINE `08256cf`; §14 SHA backfill `cbde592`. AC.BANDS.{1..7} all green; 54 new tests on dev-sdlc side (124 total) + 10 new tests on per-project-pm side (124 total) all pass. D1+D2-idempotency+D5+D6 smoke exercised; D3/D4 n/a (one-shot CLI). odd-methodology.md §11 confidence-band semantics added; cross-component allowed-prefixes auto-extended via apply step. |
| Cycle 3 — Ruby/Rails adapter | (planned) | — | — | Highest-risk; halt-trigger at ~5 h. |
| Cycle 4 — Python adapter + fixtures | (planned) | — | — | DRY aggregator with Ruby. |
| Cycle 5 — 6 SKILLs first pass | (planned) | — | — | Independent at plan-author; serializes at build. |
| **v0.1.8 release** | (planned) | — | tag SHA TBD | HARD smoke gate per Decision R. |

---
