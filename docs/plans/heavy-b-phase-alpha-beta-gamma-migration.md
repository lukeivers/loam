# Heavy-B Phase α / β / γ data migration — plan

Dev-discipline data work. **NOT** a sealed-component amendment. No `pos-amend` manifest, no SEAL_COMMIT bump, no seal commit. The migration is the body of work that populates the workspace's tracker DB with the value-prop-rooted tree (root + spec phases + sealed components + amendment ACs + test bindings) per the Heavy-B research's three-phase recommendation. Companion to amendments #38 (`objective-tracker` schema widening) + #39 (`workspace-bootstrap` tracker seed) + #40 (primary-persona tracker-context contributor) and the pos-amend-tracker-integration plan.

**Reframed 2026-04-25 mid-session:** the migration is no longer scoped as a "canonical-only one-shot" body of work. It is **lazy-projected**: triggered by `dev_intent=yes` on a workspace's PersonaContract (per sub-plan A in the two-modes-and-multi-workspace programme), executes once per workspace when the signal first flips on, and runs in any dev-intent workspace — not just canonical. End users in DEV MODE get the dev objective tree projected automatically when they signal dev intent; no manual canonical-side step. Continuous registration via `pos-amend` (Phase γ's persistent shape) remains unchanged once the initial projection has happened. The existing ACs (AC.D-mig.1–AC.D-mig.6) describe post-phase outcomes that hold regardless of trigger — the reframe changes the trigger, not the outcomes; no AC additions or modifications.

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Companion research:** `docs/plans/research/value-prop-as-root-heavy-b-migration-research.md` — the Heavy-B master research artefact; this plan is the data-migration body of work surfaced at research §B.2 ruled D-5 + D-6.
**Prior dev-discipline plan precedent:** `docs/plans/pos-amend-install-instructions-fix.md` (commit `045f6db`) + `pos-amend-tracker-integration.md` (sibling plan in this programme).

**Sibling work in the Heavy-B programme.** This plan depends on **all four amendments + the pos-amend integration + sub-plan A landing first**.

- **#38:** `objective-tracker` schema widening + query API. **Hard prerequisite.**
- **#39:** `workspace-bootstrap` first-run tracker seed (value-prop root + spec descendants). **Hard prerequisite — overlaps with Phase α scope.**
- **#40:** `primary-persona` tracker-context contributor. **Hard prerequisite — the contributor is the consumer that makes the migrated content useful.**
- **`pos-amend-tracker-integration.md`:** manifest `objectives` block + `apply` registration + `seal` `source_commit` write. **Hard prerequisite — Phase γ "continuous registration" uses pos-amend's surface.**
- **Sub-plan A (`docs/plans/two-modes-and-multi-workspace/A-onboarding-dev-intent.md`):** `dev_intent` field on PersonaContract. **Hard prerequisite for the lazy-projection trigger — phase migration consults this signal to know whether to run.** Without A's storage location settled, the lazy trigger has no signal to read; the migration cannot self-activate. (Pre-A: the migration could still run as a manually-invoked script in canonical, but the reframed shape relies on A.)
- **This plan:** the α / β / γ phasing (Phase α: root + spec + components; Phase β: component ACs; Phase γ: amendment ACs + test bindings + continuous registration going forward) **plus the lazy-projection trigger that consults A's `dev_intent` signal**.

---

## 1. Summary / TLDR

The Heavy-B migration populates a dev-intent workspace's tracker DB in three phases, per research §B.2 + owner ruling D-6. **Lazy-projection trigger (reframed 2026-04-25):** the phases run automatically on the first session where the workspace's PersonaContract carries `dev_intent="yes"` (per sub-plan A in the two-modes-and-multi-workspace programme) AND the dev tree has not already been projected. Re-runs are no-ops by `lifted_from` idempotency (per §6 constraint 6). The trigger applies in any dev-intent workspace — not just canonical; an end-user in DEV MODE gets the dev objective tree projected automatically when they signal dev intent. No manual canonical-side step.

1. **Phase α — Root + spec + components (~30 records, manual seed).** The value-prop root + spec v1.0 / v1.1 / v1.2 phase objectives + the 13 sealed component root objectives. Most of this is delivered by amendment #39's first-run seed (which seeds root + spec descendants); Phase α extends that on a dev-intent workspace by adding the 13 sealed-component objective records. **Lazy trigger:** executes when `dev_intent` flips on, if not already projected (idempotency by `lifted_from.source_doc`).
2. **Phase β — Component ACs (~130–200 records, automated extractor + manual review).** Each sealed component's proposal-declared ACs (e.g., safety-layer A1–A20, memory D1–D9, scope-of-work, reversibility B18–B25, etc.) lift into ObjectiveSpec records under their component objective. Authored as a one-time extractor script with manual placeholder seeding for ambiguous cases per owner ruling D-5. **Lazy trigger:** executes when `dev_intent` flips on, after Phase α completes, if not already projected.
3. **Phase γ — Amendment ACs + test bindings + continuous registration (~500 records, automated extractor + pos-amend hook).** Every amendment plan from #1 onward (best-effort per owner ruling D-5) lifts its declared ACs into ObjectiveSpec records under the relevant component objective, with `lifted_from.source_doc` pointing at the plan file and `lifted_from.source_commit` populated from the amendment's commit SHA. Test functions backing the ACs bind via a scripted second pass. **Lazy trigger:** executes when `dev_intent` flips on, after Phase β completes, if not already projected. After Phase γ lands, every new amendment registers its records via the pos-amend integration's `objectives` manifest block (continuous registration, no extractor needed) — continuous registration is unchanged by the lazy-projection reframe and runs every time `pos-amend apply` runs in a dev-intent workspace.

The migration is data, not code. **Nothing in this plan touches sealed-component source.** The work composes against amendment #38's schema + query API, amendment #39's seeded root, amendment #40's consumer, sub-plan A's `dev_intent` field, and pos-amend's `objectives` block. All extractor logic lives in `tools/pos-amend/` (or a sibling `tools/heavy-b-migrate/` — exact home is method) as dev-discipline tooling.

The migration is split into three phases per ODD §2.5 ("build only what the objectives require") + research §B.2: a single big-bang of 700 records would author records the migration's ACs do not require to test in one commit. Phasing lets each phase's ACs verify exactly what that phase landed. The lazy-projection trigger preserves the phase ordering (AC.D-mig.6) — α before β before γ — and the per-phase idempotency rule.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)

§2.5 reads: "Before scoping anything as a sealed-component amendment, name the specific spec objective (v1.0/v1.1/v1.2) the code will satisfy. If I can't name one, the work is dev-discipline (CLAUDE.md, docs, CDCs, tools/), not a sealed-component cycle."

**No single spec objective names "the workspace's tracker DB is populated with extracted records from the existing dev corpus."** The clauses adjacent to this work — v1.0 Architectural "Objective-based" + v1.1 R1 (semantic round-trip) + V1.2 R16 (framework-not-content) — are satisfied by amendments #38/#39/#40 + the pos-amend integration. The migration's contribution is operational: it backfills the data substrate that the substrate-creating amendments enabled. That is dev-discipline territory by every property §2.5 names:

- The migration extractor / seeder lives under `tools/`.
- The migration has no spec objective; its load-bearing-ness is operational (the persona-side tracker-context contributor at amendment #40 surfaces meaningful state only once Phase α/β/γ has populated the tree).
- The migration touches no sealed component's source. It writes to the workspace's tracker DB (the data layer), not to the tracker primitive code itself (the schema/API layer landed at #38).

Owner ruling D-5 (best-effort back-extraction with placeholders) + D-6 (three phases, not big-bang) confirmed dev-discipline phasing.

**The chicken-and-egg from research §F.5 is resolved by sequencing.** Phase α can be authored as a script that runs after #38 + #39 seal — its ACs verify post-Phase-α tracker state (the tree contains 13 + n component-tier records), not pre-Phase-α (which would be empty by virtue of the migration not having run). Same for β and γ.

---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage

**What Claude capability does this lean on or extend?**

This plan is bulk data work. The Claude-leverage observation is that the migration **enables** the Lens-1 wins on the consumer side:

- After Phase α/β/γ, primary-persona's tracker-context contributor (amendment #40) surfaces a meaningful tree at session-load — without the migration, the contributor surfaces only the seeded root + spec descendants, which is a thin slice of the workspace's actual objective-state.
- Future `pos-amend project --check` (research §D.1) renders projected plan docs from the tracker — without back-extracted plan-doc records, the projector has nothing to project.

The migration extractor itself does not invoke Claude primitives; it is a Python script that reads markdown files + writes tracker records. That is the right shape — extraction is bookkeeping, not interactive.

**One Claude-leverage opportunity that is explicitly out of scope here but flagged for follow-on:** the manual placeholder seeding for ambiguous pre-#22 plans (per owner ruling D-5) could be driven by an LLM-assisted extraction (an agent reads each ambiguous plan, proposes ObjectiveSpec records, the human reviews). That is a follow-on programme; this plan ships best-effort regex-based extraction + placeholder records for the residual.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation burden between the user's natural-language intent and AI-effective execution?*

Yes — substantially, on the persona-side surface. Without the migration, the persona's tracker-context contributor (amendment #40) surfaces only the seeded root + spec phase objectives — an outline, not a current-state report. After Phase α/β/γ:

- The user asking "what is the workspace working on?" gets an answer that includes in-flight component ACs and amendment ACs, sourced from the tracker, not from the user's memory of which plan files they last read.
- The persona's authoring of new amendments (via the pos-amend integration's `objectives` block) lands records that the contributor surfaces immediately at the next session — translation burden of "which AC am I writing the test against?" is absorbed by the harness.

**AC-trace to AC.PO.1:**

- **AC.D-mig.1 → amendment #39's seed surface (Phase α extension) → v1.0 Architectural "Objective-based" → AC.PO.1.** Phase α adds 13 sealed-component objectives chaining to the value-prop root → persona's tracker-context contributor surfaces "this workspace has 13 sealed components" without the user telling it → translation burden absorbed.
- **AC.D-mig.2 → amendment #38's `lifted_from` field → audit-trail invariant → AC.PO.1.** Every Phase β record carries `lifted_from` pointing at the source proposal + AC ID → re-running the extractor is idempotent → user does not see migration drift over re-runs → translation burden absorbed (no "is this current?" doubt).
- **AC.D-mig.3 → amendment #40's consumer → AC.PO.1.** Phase γ records make in-flight amendment ACs queryable → persona surfaces them → user does not have to remember which amendment is in flight → translation burden absorbed.
- **AC.D-mig.4 → pos-amend integration's `objectives` block → AC.PO.1.** Phase γ continuous-registration ensures tree stays current as new amendments land → user does not see stale tree → translation burden absorbed.

**Harness test.** *Does this add to the toolkit the primary persona can draw from?*

Yes — three new toolkit primitives (data, but data IS the toolkit's content for tracker-consumers):

1. **The fully-populated value-prop-rooted tree** is the substrate for every Heavy-B downstream consumer. Without this data, the primitives at #38/#39/#40 + pos-amend integration are infrastructure with nothing to operate on.
2. **The extractor scripts under `tools/`** are reusable for future dev-corpus extractions (e.g., a future workspace adding its own dev-discipline corpus).
3. **The continuous-registration pattern** post-Phase-γ — every amendment registers its ACs at authoring time — establishes the dev-cycle discipline that keeps the tree current going forward.

**AC-trace to AC.PO.2:**

- **AC.D-mig.1, AC.D-mig.2, AC.D-mig.3 → AC.PO.2.** Each phase adds queryable substrate — toolkit content.
- **AC.D-mig.5 → AC.PO.2.** Phase γ best-effort extractor handles legacy plan docs — toolkit completeness preserved (no orphan ACs).

### Lens 3 — ODD authoring

The plan authors six outcome-shaped acceptance criteria (§4) under §2.5 framing. Each AC names what must be true; method (the extractor's regex / parser shape, the placeholder-record convention, the Phase-β manual-review process, the continuous-registration verification mechanism) is the builder's call.

ODD §2.5 reverse-direction check: every new code path in `tools/` traces back to AC.D-mig.1–AC.D-mig.6. The placeholder branch (AC.D-mig.5) is explicitly criterion-backed; the continuous-registration branch (AC.D-mig.4) is explicitly criterion-backed. No silent branches.

The phasing itself maps cleanly to ODD §4 re-extension: Phase β re-extends Phase α's tree with component ACs; Phase γ re-extends β's tree with amendment ACs; each phase's ACs verify that phase's contribution.

---

## 4. Acceptance criteria (AC.D-mig.x — dev-discipline plan)

Each AC maps to at least one test function in the migration test suite (location method — likely `tools/heavy-b-migrate/tests/` or a sibling under `tools/pos-amend/tests/`).

### AC.D-mig.1 — Phase α — sealed-component objectives chained to value-prop root

After Phase α completes against a workspace whose tracker has been seeded by amendment #39 (root + spec descendants), the tracker contains 13 additional records — one per sealed component (memory-system, scope-of-work, primary-persona, objective-tracker, session-resilient-orchestrator, graceful-degradation, observability-aggregator, self-upgrade-framework, safety-layer, reversibility-primitive, cost-governance, self-correction-loop, workspace-bootstrap, plus hands-off-lifecycle and foundation-audit per STATE.md's component table — exact list method per the workspace's STATE.md). Each component record:

- has `parent_id` pointing at the appropriate spec-phase ancestor (Phase 1 / 2 / 3 / 4 — exact mapping is method),
- has `authored_by == "user"`,
- has `lifted_from.source_doc == "docs/STATE.md"` (or per-component `proposal.md` paths — exact source choice is method),
- chains to the value-prop root via `trace_to_root`.

**Test shape:** run Phase α extractor against the canonical workspace; query the tracker via `query_projection_view(filter={"lifted_from.source_doc": ...})`; assert 13+ records present; assert each chains to the value-prop root.

**Maps to:** v1.0 Architectural "Objective-based" + objective-tracker D2 → AC.PO.1 + AC.PO.2.

### AC.D-mig.2 — Phase β — component ACs registered with `lifted_from` provenance

After Phase β completes, the tracker contains records for every component proposal's declared AC (or a placeholder per AC.D-mig.5 if extraction fails). Each record:

- has `parent_id` pointing at its component objective (from Phase α),
- has `authored_by == "user"`,
- has `lifted_from.source_doc` pointing at the component's `proposal.md`,
- has `lifted_from.source_ac` matching the AC identifier (e.g., `D1`, `A20`, `B25`).

**Test shape:** run Phase β extractor; query the tracker for `lifted_from.source_doc` matching a known component proposal path; assert N records returned where N matches the proposal's declared AC count (verified against a hand-counted reference set for at least 2 components, e.g., memory-system D1–D9 and safety-layer A1–A20).

**Maps to:** amendment #38's `lifted_from` field + objective-tracker D2 → AC.PO.1 + AC.PO.2.

### AC.D-mig.3 — Phase γ — amendment ACs registered with `source_commit` populated

After Phase γ completes, the tracker contains records for every amendment plan's declared AC (or a placeholder per AC.D-mig.5). Each record:

- has `parent_id` pointing at the relevant component objective (or, where the amendment cuts across components, at the relevant ancestor — exact policy is method),
- has `authored_by == "user"` (or `"primary-persona"` per research §A.4 — exact policy is method, but every amendment is `"user"` if Luke authored or approved it, per the research's dominant case),
- has `lifted_from.source_doc` pointing at the amendment's plan file,
- has `lifted_from.source_ac` matching the AC identifier (e.g., `AC29.5`, `AC34.1`),
- has `lifted_from.source_commit` populated to the amendment's seal commit SHA.

**Test shape:** run Phase γ extractor; query the tracker for amendment-29's plan file as `lifted_from.source_doc`; assert 5+ records returned (matching AC29.1–AC29.5); assert `source_commit` matches the actual seal-commit SHA (read from git log).

**Maps to:** amendment #38's `lifted_from` field + audit-trail invariant → AC.PO.1 + AC.PO.2.

### AC.D-mig.4 — Continuous registration verified post-Phase-γ

After Phase γ, every new amendment landed via the pos-amend integration's `objectives` manifest block (per pos-amend-tracker-integration plan AC.D-pa.1) registers its declared ACs in the tracker as part of `pos-amend apply`. A test fixture amendment lands; pos-amend apply runs; the fixture's ACs appear in the tracker; pos-amend seal updates `source_commit`; the contributor at amendment #40 surfaces the new ACs at the next session.

**Test shape:** craft a fixture amendment with an `objectives` block; in a tmpfs workspace simulate the apply → commit → seal cycle; query the tracker; assert the fixture's records are present with correct `source_commit`. Assert amendment #40's contributor surfaces the new records at simulated SessionStart.

**Maps to:** pos-amend integration AC.D-pa.1 + amendment #40 AC40.1 → AC.PO.1.

### AC.D-mig.5 — Best-effort extraction handles legacy plans with placeholders

Per owner ruling D-5, plans whose structure does not parse cleanly (pre-amendment-#22 plans whose AC layout is non-standard, plans with mid-prose AC numbering, plans with no explicit AC headers) get a single placeholder ObjectiveSpec record per plan, with `goal` summarising the plan's title, `lifted_from.source_doc` pointing at the plan file, and a clear `prose` criterion citing the plan path. The extractor logs which plans were placeholder-seeded vs cleanly-parsed; the log is reviewable.

**Test shape:** craft three test-fixture plans — one well-structured (post-#22 shape), one ambiguous (pre-#22 shape with no clear AC layout), one malformed (broken markdown). Run the Phase γ extractor; assert the well-structured plan produces N records (one per AC); assert the ambiguous plan produces 1 placeholder record; assert the malformed plan is logged + produces 1 placeholder record. Assert no exception propagates from any of the three.

**Maps to:** owner ruling D-5 (best-effort) + ODD §2.5 (no orphan ACs in the tree) → AC.PO.2.

### AC.D-mig.6 — Phase order verified — α before β before γ; each phase's ACs verify only that phase's records

The phases are mechanically ordered: Phase β cannot run before Phase α completes (β's `parent_id` pointers reference Phase α's component objectives). Phase γ cannot run before Phase β completes (γ's `parent_id` pointers reference Phase β's component-AC records, where amendment ACs extend a component AC). The extractor's phase-runner enforces ordering — invoking Phase β before α exits non-zero with a structured diagnostic.

**Test shape:** in a fresh tmpfs workspace, attempt to run Phase β before Phase α; assert non-zero exit + diagnostic. Run Phase α; run Phase β; assert success. Repeat for γ.

**Maps to:** ODD §4 re-extension (each phase extends the prior; ordering is structural) → AC.PO.2.

---

## 5. Behaviour-count check (ODD §3.3 forward; applied as dev-discipline check)

| Behaviour (§1) | Criterion/criteria |
|---|---|
| 1. Phase α — 13 sealed-component objectives chained to root | AC.D-mig.1 |
| 2. Phase β — component ACs with lifted_from provenance | AC.D-mig.2 |
| 3. Phase γ — amendment ACs with source_commit populated | AC.D-mig.3 |
| 4. Continuous registration via pos-amend on new amendments | AC.D-mig.4 |
| 5. Best-effort extraction with placeholders | AC.D-mig.5 |
| 6. Phase ordering structurally enforced | AC.D-mig.6 |

Six declared behaviours; six ACs cover them. No method-in-AC. Dev-discipline plans do not carry seal-diff ACs because no sealed component is touched.

---

## 6. Hard constraints

1. **No `--amend`.** Corrective commits only.
2. **Scope fence — `tools/` only** (extractor + tests). Source under `tools/heavy-b-migrate/` (or sibling under `tools/pos-amend/`). Tests under the same root. The migration may also write to `docs/plans/` (manifest fixtures, migration log) per the universal-paths convention. Any source edit outside these paths is a halt.
3. **No edit to amendments #38/#39/#40 or the pos-amend integration.** They are consumed; if they need a change, halt and signal — the change belongs in their respective territories.
4. **Reversibility.** Removing this migration's records returns the tracker to its post-#39-seed state. The data is regenerable from the source corpus by re-running the extractor.
5. **No new third-party deps.** Standard-library Python + the existing PyYAML + the importable `objective-tracker` package suffice.
6. **Idempotency by `lifted_from`.** Re-running any phase against an already-populated workspace is a no-op (records present per `lifted_from.source_doc + source_ac` are skipped). The migration's ACs verify this (AC.D-mig.5 implicitly — re-run the extractor; record count unchanged).
7. **Authored_by discipline.** Per research §A.4: records lifted from `docs/VALUE_PROPOSITION.md`, `docs/spec/pos-v2-objectives-spec.md`, the 13 sealed component proposals, the 26 amendment plans → `"user"` (Luke authored or approved). Any record needing a different `authored_by` requires the builder to surface for owner.
8. **Data quality bound.** The extractor is a regex/parser-based tool; ambiguous extractions get placeholders (AC.D-mig.5), not garbage. The migration log lists every placeholder-seeded plan so the human reviewer can prioritise post-migration cleanup.
9. **Authority bound.** Builder may refine the extractor's parser shape, the placeholder-seeded record convention, the manifest-fixture shape for AC.D-mig.4 verification, the migration-log schema, the phase-runner CLI surface. Builder may NOT relax ordering (AC.D-mig.6), idempotency (per §6 constraint 6), or `authored_by="user"` (§6 constraint 7).
10. **CDC adherence.** Plan-before-code, background-agent default, scope-only dispatch. Multi-phase work runs serially in the same working tree per the serialise-amendment-builds-in-the-same-working-tree memory; phase α background agent + phase β background agent must not race the same tracker DB.
11. **All five upstream deliverables must seal/land before this work begins** — verified at builder's pre-edit gate. The five are: amendments #38 / #39 / #40, the pos-amend-tracker-integration plan, AND sub-plan A (the `dev_intent` field on PersonaContract that the lazy-projection trigger consults).
12. **Dev-discipline framing — no SEAL_COMMIT bump, no manifest, no seal commit.** This work lands as one or more conventional `chore(migrate)` / `feat(tools)` commits per phase.
13. **Lazy-projection trigger — read-only consumer of A's signal.** The trigger reads `dev_intent` from the PersonaContract; it does not write the field, modify A's surface, or extend the contract schema. Any need to extend A's surface is a halt — that's a re-extension of A, not a property of this plan.
14. **Idempotency by `lifted_from` is the lazy-projection guard.** When the trigger fires on a workspace whose dev tree was already projected, every phase is a no-op (records present per `lifted_from.source_doc + source_ac` are skipped per §6 constraint 6). The trigger does not need its own "already projected" sentinel — `lifted_from`-based idempotency covers it.

---

## 7. Out of scope (explicit)

- **Schema widening or query API on `ObjectiveTracker`** — amendment #38.
- **First-run tracker seed** — amendment #39 (Phase α partially overlaps but α extends rather than redoes).
- **Primary-persona tracker-context contributor** — amendment #40.
- **pos-amend `objectives` block / apply registration / seal source_commit** — pos-amend-tracker-integration plan.
- **`pos-amend project` subcommand** — out of scope; lands in a follow-on dev-discipline plan once Phase γ verifies the substrate.
- **`pos-amend audit-coverage` subcommand** — out of scope; lands in a follow-on dev-discipline plan.
- **CDC-as-objective seeding under the harness-toolkit branch** (research §E.2) — out of scope here; deferred to a sibling dev-discipline plan or to a future amendment that lands once the migration substrate is verified.
- **LLM-assisted extraction of ambiguous plans** — out of scope; placeholders per AC.D-mig.5 are the v1 answer.
- **Drift detection between projected plan docs and tracker state** — depends on the `project` subcommand; out of scope here.
- **Rebuilding legacy plan docs from projection** (research §D.2 alternative considered + rejected) — explicitly out of scope; legacy plans stay as historical artefacts.

---

## 8. Implementation order (suggested — builder's call to refine)

1. Read session-start corpus per CLAUDE.md.
2. Read Heavy-B research artefact + amendments #38/#39/#40 plans + pos-amend-tracker-integration plan + sub-plan A + this plan + STATE.md + the 13 component proposal.md files + the 26 amendment plan files.
3. Verify all five upstream deliverables have landed (per §6 constraint 11).
4. Write builder-plan to `docs/plans/heavy-b-phase-alpha-beta-gamma-migration.builder-plan.md` naming specific phase-extractor files + symbols expected to be touched, including the lazy-projection trigger surface.
5. Author the lazy-projection trigger — a small surface that reads `dev_intent` from the PersonaContract on the relevant lifecycle event (e.g., session-start, scaffold completion, or pos-amend invocation — exact attach point is method) and dispatches the phase runner if the workspace is dev-intent and the dev tree is not yet projected. Method-level decision: where the trigger attaches in the lifecycle.
6. Phase α — author the sealed-component objective seeder; trigger runs it against the workspace tracker; verify AC.D-mig.1.
7. Phase β — author the component-proposal AC extractor; trigger runs it after α; verify AC.D-mig.2 + AC.D-mig.5 (placeholder paths exercised on at least one ambiguous case).
8. Phase γ — author the amendment-plan AC extractor + test-binding pass; trigger runs it after β; verify AC.D-mig.3.
9. Verify continuous registration via a fixture amendment cycle; verify AC.D-mig.4.
10. Verify phase ordering enforcement (AC.D-mig.6) AND lazy-trigger idempotency (re-firing the trigger on an already-projected workspace is a no-op via `lifted_from`).
11. Update `tools/pos-amend/README.md` (or `tools/heavy-b-migrate/README.md`) with the migration surface + how to re-run it (idempotently) + the lazy-trigger attach point.
12. Conventional commits land each phase + the docs update (no `--amend`, no SEAL_COMMIT bump, no seal commit). Suggest one commit per phase for clean rollback.

---

## 9. Halt triggers (builder halts + signals owner)

1. **Cross-component scope expansion beyond `tools/`.** Any required source edit to `objective-tracker/`, `workspace-bootstrap/`, `primary-persona/`, `hands-off-lifecycle/`, or any other sealed component → halt. **Note:** the lazy-projection trigger reads `dev_intent` from the PersonaContract; if the trigger's attach point requires extending a sealed component's surface (e.g., a new persona-side hook, a new scaffold-runner branch), halt — that re-extension is a separate sealed-component amendment, not part of this dev-discipline plan.
2. **Any of the five upstream deliverables has not landed before this work begins** (amendments #38 / #39 / #40, pos-amend-tracker-integration, sub-plan A's `dev_intent` field). Halt.
3. **The extractor cannot reach idempotency** because `query_projection_view` does not support filtering by both `source_doc` AND `source_ac` together (the dual-key idempotency check). Halt — coordinate with #38 territory or surface for owner.
4. **The phase ordering cannot be enforced structurally** (e.g., Phase β somehow legitimately needs to seed a record under a Phase α-implied parent that does not yet exist). Halt — that contradicts the research §B.2 phasing model.
5. **The placeholder-seeded record class produces a record that fails ObjectiveSpec validation** (e.g., the cited plan has no parseable goal text). Halt — surface for owner; the placeholder convention may need a new field or a different `time_bound` shape.
6. **An amendment plan needs `authored_by` set to something other than `"user"` or `"primary-persona"`** per research §A.4. Halt; owner rules.
7. **An ODD-violating shape becomes strongly required** (method-in-AC, non-objective code path, silent exception that no AC backs). Halt; owner rules.
8. **A test for AC.D-mig.1–AC.D-mig.6 cannot be written deterministically** — halt.
9. **The dev-discipline framing turns out wrong** (e.g., Phase β unavoidably edits a sealed component's source). Halt — that's a sealed-component amendment, not dev-discipline.
10. **Phase wall-time exceeds 4 hours per phase.** Halt with current state. Owner rules on split vs push-through. (Phases run as background agents per the background-default memory; 4-hour wall-time is the upper bound for a phase before splitting.)

---

## 10. Bookkeeping (n/a — dev-discipline; no `pos-amend` manifest)

This plan is dev-discipline; no manifest, no SEAL_COMMIT bump, no seal commit. Conventional commits land each phase. Suggested commit-message families per phase:

- Lazy-projection trigger: `feat(tools): heavy-b lazy-projection trigger reads dev_intent + dispatches phases`
- Phase α: `chore(migrate): heavy-b phase α — sealed-component objectives seeded`
- Phase β: `chore(migrate): heavy-b phase β — component ACs extracted`
- Phase γ: `chore(migrate): heavy-b phase γ — amendment ACs + test bindings`
- Continuous-registration verification: `chore(migrate): heavy-b continuous-registration verified post-γ`
- Migration log (post-run): `docs(migrate): heavy-b migration log + placeholder-seeded plans summary`

---

## 11. Decisions remaining for the build agent

The following items remain method-level builder choices within this scope. Master-research recommendations are cited but not pinned.

- **D-build.1 — Extractor home.** Two reasonable shapes: (a) sibling tool under `tools/heavy-b-migrate/`; (b) extension to `tools/pos-amend/` as new subcommands. **Master-research recommendation:** (a) for clean separation — heavy-b-migrate is a one-time data-migration tool plus a verification harness, distinct from pos-amend's amendment-cycle bookkeeping role. **Builder's call within scope.** The AC count and structure are the same either way.
- **D-build.2 — Phase β placeholder convention.** Two reasonable shapes: (a) one placeholder ObjectiveSpec per component-proposal section that fails to parse; (b) one placeholder per failed AC plus a "review needed" tag on an existing record. **Master-research recommendation:** (a) — minimal record count; placeholders are visibly distinct. **Builder's call within scope.** AC.D-mig.5 measures outcome.
- **D-build.3 — Phase γ amendment authoring policy.** Two reasonable shapes: (a) every amendment is `authored_by="user"` (per research §A.4 dominant case); (b) authoring is determined per-amendment from git log + plan-doc author conventions. **Master-research recommendation:** (a) for simplicity unless an amendment's plan explicitly names a primary-persona author. **Builder's call within scope.** §6 constraint 7 measures outcome.
- **D-build.4 — Continuous-registration verification mechanism.** Two reasonable shapes: (a) a CI check that compares manifest `objectives` count to tracker record count for the manifest's plan; (b) a one-shot verification pass run after Phase γ that exits 0 if tree matches expected post-Phase-γ state. **Master-research recommendation:** (b) for now — CI integration is a follow-on. **Builder's call within scope.** AC.D-mig.4 measures outcome.
- **D-build.5 — Per-phase test scope.** Phases run independently; per-phase test scope covers that phase + the upstream-prerequisite-verification harness. The builder may unify all six ACs in a single test suite or split per phase; either is acceptable.
- **D-build.6 — Lazy-projection trigger attach point.** Three reasonable shapes for where the trigger consults `dev_intent` and dispatches the phase runner: (a) a session-start hook in primary-persona's contributor surface (cheap to read, fires every session); (b) a one-shot dispatch on first-run scaffold completion when a dev-intent contract is detected; (c) a pre-`pos-amend apply` check that ensures the dev tree is projected before continuous registration writes new records. **Master-research recommendation:** (a) — session-start is the established lifecycle event the contract is already loaded against (per amendment #32's gate); the trigger reads the contract once, dispatches the phases if needed, and the work is idempotent on subsequent sessions. (b) and (c) are method-acceptable but require additional plumbing. **Builder's call within scope.** §6 constraint 13 (read-only consumer) and §6 constraint 14 (idempotency) measure outcome regardless.

These six are surfaced to make the dispatch brief tighter; they are not blockers for plan approval.

---

## 12. Source plan (historical context)

This dev-discipline plan derives from the Heavy-B master research artefact:

- **Master research:** `docs/plans/research/value-prop-as-root-heavy-b-migration-research.md` — covers the full investigation; §B.1 + B.2 specify the hybrid extractor + phasing approach; §B.3 covers idempotency via `lifted_from`; §C.2 specifies the phasing dependency order; §F.5 resolves the chicken-and-egg.

The owner ruled (post-master-research):
- **D-5: best-effort + placeholders** for legacy plan back-extraction.
- **D-6: three phases** (α / β / γ), not big-bang.
- **D-3: pos-amend integration is dev-discipline** (this plan's prerequisite is also dev-discipline).

This plan ships as **dev-discipline** rather than a sealed-component amendment. Plan structure mirrors the prior dev-discipline precedent at `pos-amend-install-instructions-fix.md` (commit `045f6db`) + the sibling `pos-amend-tracker-integration.md` plan.

Master-research decision ↔ this-plan AC mapping (for traceability):

| Master decision | This-plan AC | Note |
|---|---|---|
| D-5 (legacy back-extraction: best-effort or cutoff?) | AC.D-mig.5 | Best-effort + placeholders. |
| D-6 (migration phasing: 3 phases vs big-bang?) | AC.D-mig.1 + AC.D-mig.2 + AC.D-mig.3 + AC.D-mig.6 | Three phases; ordering enforced. |
| Research §B.3 (idempotency via `lifted_from`) | All AC.D-mig.x (idempotency is a hard constraint per §6) | Re-runs are no-ops. |
| Research §F.5 (chicken-and-egg resolution) | AC.D-mig.1 (Phase α runs as a script after #39 seals; α's ACs verify post-α state) | Phase boundary clean. |

---

## 13. Dispatch-time additions (brief-phase material)

When the brief is drafted, it carries these CDC + ODD enforcement requirements verbatim:

- Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`. No cd-out.
- Session-start corpus read mandatory before any code edit.
- **Pre-edit gate:** verify all five upstream deliverables have landed (`objective-tracker/tests/SEAL_COMMIT` past #38 + `lifted_from` field present + `query_projection_view` callable; `workspace-bootstrap/tests/SEAL_COMMIT` past #39 + freshly-scaffolded workspace's tracker carries the value-prop root; `primary-persona/tests/SEAL_COMMIT` past #40 + tracker-context contributor importable; pos-amend's `objectives` manifest block accepted by validate; **sub-plan A landed — `primary-persona/tests/SEAL_COMMIT` post-A + PersonaContract carries `dev_intent` field readable from any consumer**). Halt if any unmet.
- Plan-before-code: builder writes its own builder-plan to disk before touching source (per phase if needed).
- ODD §2.4 + §2.5: no method-in-acceptance, no non-objective-backed code (criteria are AC.D-mig.x because no spec clause anchors this dev-discipline data work; the §2.5 framing in §2 above explains why).
- Strong-ODD-adherence: halt if the builder believes an ODD break is strongly required.
- Scope-only downstream dispatches.
- No `git commit --amend`. Corrective new commits if the builder misses a file.
- No SEAL_COMMIT bump, no `pos-amend` manifest, no seal commit.
- Phases run sequentially in the same working tree (per the serialise-amendment-builds-in-the-same-working-tree memory). Background agents are appropriate per phase per the background-default memory; do not run phases α + β + γ in parallel against the same tracker DB.
- Dispatch-speedups apply: narrow test scope to `tools/heavy-b-migrate/` (or sibling); run upstream-prereq probes only (don't re-run full sealed-component test suites).

---

## 14. Method-decision register (build-time backfill)

Authored before commits per CLAUDE.md plan-before-code; SHAs backfilled
post-build. Companion builder-plan: `heavy-b-phase-alpha-beta-gamma-migration.builder-plan.md`.

- **D-build.1 — Extractor home.** **(a)** New `tools/heavy-b-migrate/` package, sibling to `tools/pos-amend/` and `tools/loam-mode/`. Master-research recommendation; clean separation from pos-amend's amendment-cycle role.
- **D-build.2 — Phase β placeholder convention.** **(a)** One placeholder ObjectiveSpec per component proposal that fails to parse. Visible in `query_projection_view` filtered by `lifted_from.source_doc`.
- **D-build.3 — Phase γ amendment authoring policy.** **(a)** Every amendment is `authored_by="user"` per research §A.4 dominant case.
- **D-build.4 — Continuous-registration verification.** **(b)** One-shot post-Phase-γ verification harness (`heavy-b-migrate verify-continuous` subcommand) running against an isolated tracker DB.
- **D-build.5 — Per-phase test scope.** One test file per AC (`test_ac_d_mig_<n>_<name>.py`).
- **D-build.6 — Lazy-projection trigger attach point.** **(a-prime)** Wired into loam-mode's session-start emitter (`tools/loam-mode/src/loam_mode/session_start.py`), NOT primary-persona's contributor surface as the master-research §11 (a) literally specified. **Deviation rationale:** primary-persona is a sealed component (Phase 1, sealed 2026-04-18). Editing its contributor surface is a sealed-component amendment, not dev-discipline; that contradicts §6 constraint 2 ("scope fence — `tools/` only") and §6 constraint 3 ("no edit to amendments #38/#39/#40"). Loam-mode's session-start emitter (sub-plan B, dev-discipline, in `tools/loam-mode/`) is functionally equivalent — it runs every session via the multi-contributor mechanism #45 generalised, already reads `dev_intent`, and stays inside the scope fence. Per `feedback_critical_thinking_on_deviations`: enumerated; balance picked. The behaviour the plan asks for (session-start lifecycle attach + read `dev_intent` + dispatch the phase runner) is preserved.

Commit SHAs (backfilled):

- Heavy-b-migrate scaffold + extractors: `dc9dccb`
- Loam-mode lazy-projection wire: `df596ab`
- Plan-doc SHA backfill: this commit (chain top after merge).
