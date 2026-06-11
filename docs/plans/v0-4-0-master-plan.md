> **RETIRED-SCOPE BANNER 2026-06-11.** This master plan is a completed
> historical record. The ProgramBench-related work referenced herein was
> retired 2026-06-11 by owner ruling (Discord 1514747695972094165; plan
> `docs/plans/programbench-full-retirement.md`); nothing PB-related in this
> document is current or future work. Content below is preserved verbatim.

# v0.4.0 master plan — Loam ships working code from extracted objectives

**Status:** master plan-doc; plan-before-code per `feedback_plan_before_code`. Authored 2026-05-08 (Sonnet, master-plan-author dispatch). **Plan-only — owner ratification gate before any cycle dispatch.**
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.
**Parent authority:** `docs/release-roadmap.md` §3 v0.4.0 — AUTHORITATIVE for objective + ACs + constraints + estimated AI-time.
**Always-load grounding:** `docs/odd-llm-grounding.lean.md`. Self-checks 1–5 applied to every "objective" / "AC" / "constraint" / "capability" named here; §10 records the self-check pass.

**Predecessor commit:**
- v0.3.0 SHIPPED — Cycles 1–7 + C6.1 sealed at `3c6fdd5` (final seal). META-FRAMEWORK foundation in place: `docs/rebuild/` collapsed, graphiti rip-out, FBE.7 file-backed memory canonical, glossary published, lint-clean, feature-honesty audit 100% match, `claude -p --strict-mcp-config` invariant verified, foundation-docs gap-fill landed.
- `docs/release-roadmap.md` §3 v0.4.0 — six ACs (V040.1–V040.6) named.
- `docs/release-versioning-policy.md`, `docs/odd-semver-pinning.md`, `docs/leverage-discipline.md` — sibling methodology + policy docs.
- `<workspace>/.scratch/claude-output/claude-conference-features-2026-05-06.md` §4 — Routines + Code Review composition surface; Outcomes-pattern divergence note.
- `<workspace>/.scratch/claude-output/programbench-loam-benchmark-v0.md` — Variant A docs-only baseline shape.
- `docs/plans/research/harness-landscape-and-roadmap-rerank.md` — confirms v0.4.0 positioning (T2 rubric-driven grading correctly mapped at v0.4.0; no re-rank needed for this minor).
- `docs/plans/amendment-38-objective-tracker-schema-widening.md` — `lifted_from = {source_doc, source_ac, source_commit}` schema; reused as the per-commit `objectives:` block carrier.

**Quality bar (END-USER class):** v0.4.0 ships new user-visible capability. The class gate per `docs/release-versioning-policy.md` §Quality-gate is met by the named translation-burden delta — *the user can now request "build feature X from my extracted objectives" and receive working source code with every commit traced to a named AC, not just a contract document.* This is the version where loam stops being a contract-extractor and starts being a software-builder; the Dev/SDLC plugin's prime function activates here.

---

## Principles applied this turn

CHANNEL (terminal); AUTONOMY (hard halt before owner ratification gate per dispatch directive Telegram 10365, not discretionary); F2 RF (§10 surfaces seven honest doubts); LOCKED-DESIGN-NOT-LICENSE (release-roadmap §3 v0.4.0 is locked baseline; surface re-extension if dispatch reveals scope can't fit); ODD §2.5 (every cycle ladders to §2; ≥1 outcome-altitude AC per cycle); WD-IN-DISPATCHES (confirmed `pwd` returned `/Users/lukeivers/ivers-corp-pos-v2`); PLAN-BEFORE-CODE (5 cycle stubs land same commit); SCOPE-ONLY (method specs are cycle plan-doc responsibility); SWARMING Lens 5 (`max_planner_depth: 1`; 5 cycles each tighter than parent); F4 (cycle count + ordering + AC.V040.1 split + substrate bundling + ProgramBench scope are TIGHT; per-cycle method LOOSE); TIME-CLAIMS-DISCIPLINE (rubric `wall_clock_minutes ≈ tool_calls × 0.1–0.15`; aggregate matches parent ~8hr midpoint); NO ANTHROPIC API KEY (subscription-only via `claude -p`; Outcomes ADR documents divergence, doesn't work around it); OUTCOME-ALTITUDE AC REQUIREMENT (AC.V040.6 verifies against `jsts-playwright-app` no monkeypatch); ASK-FIRST ON PUBLIC ACTIONS (no push, no tag, no GitHub Release in any cycle).

---

## §1 — Outcome shape

v0.4.0 is the **END-USER class transition minor**. Loam stops scaffolding and starts shipping code. Objective sentence (verbatim from `docs/release-roadmap.md` §3 v0.4.0):

> *Loam takes objectives.yaml + gap-inventory.yaml + build-next.yaml as planning input and produces working source code that maps every line to a named AC.*

**Theme.** Code-gen-from-objectives. The reverse-ODD pipeline shipped in v0.1.8 → v0.2.5.1 (extract objectives + capabilities + gaps from existing surface) becomes load-bearing because the planning input it produces grounds the code that ships. Every generated commit carries an `objectives:` block (per amendment #38 `lifted_from = {source_doc, source_ac, source_commit}` schema) so a stranger can trace any line of generated code back to the named AC it serves.

**Foundational rationale.** This is the deliverable shape the prime objective (`docs/VALUE_PROPOSITION.md`) names: *loam exists to help people use LLMs to build software*. Pre-v0.4.0, loam helped with planning + extraction + scaffolding — useful but upstream of the deliverable. Post-v0.4.0, loam ships working code attributable to the objectives that motivated it. The translation-burden delta the user gains: instead of "I extracted objectives, now what do I build?" the user runs `loam build-next` (or named successor) and receives a unified diff or branch ready for review with every commit's `objectives:` block populated.

**Composition layer.** Per the conference research at `<workspace>/.scratch/claude-output/claude-conference-features-2026-05-06.md` §4, loam's code-gen pipeline composes on three Claude Code primitives that shipped in the past two weeks:

1. **Routines** (Released) — runtime layer for background-agent dispatches. Loam `claude routine create` invocations replace ad-hoc background-Bash dispatches where async-work-then-resume is the pattern.
2. **Code Review** (`claude code review`, Released) — plan-step primitive. Plan-author SKILL composes on it rather than reimplementing review.
3. **Outcomes** (Managed Agents, public beta) — runtime grader analogue to ODD's authoring-time discipline. **API-keyed; loam-on-subscription cannot directly compose.** Documented as architectural divergence in `docs/design/odd-vs-outcomes.md` (AC.V040.5).

**Class:** END-USER. Per the policy doc §Quality-gate, the named translation-burden delta is "user can now request a feature build and receive working code with provenance, not just a contract." This is concrete and user-visible.

---

## §2 — Scope source-of-truth

Pulled from `docs/release-roadmap.md` §3 v0.4.0.

### Verbatim AC mapping

| AC | Source-of-truth | Cycle |
|---|---|---|
| AC.V040.1 — Code-gen-from-objectives integration | `loam build-next` (or named successor) accepts objectives.yaml + build-next.yaml; dispatches LLM-routed code-gen cycle; produces unified diff or branch with each commit's `objectives:` block populated. | C1 (core dispatch + objectives→diff plumbing) + C2 (outcome-altitude verification against `jsts-playwright-app`) |
| AC.V040.2 — Routines integration | Background loam dispatches can invoke `claude routine create` or equivalent; documented pattern + 1 example plan-doc. | C3 |
| AC.V040.3 — Code-review composition | Plan-author SKILL "compose-on-claude-code-review" guidance; one example plan-doc demonstrates composition. | C3 |
| AC.V040.4 — ProgramBench docs-only baseline (v0) | Variant A run on 3-5 small ProgramBench tasks (jq, ripgrep). Behavioral test pass rate. Report at `docs/experiments/programbench-v0-docs-only.md`. | C4 |
| AC.V040.5 — Outcomes-pattern ADR | `docs/design/odd-vs-outcomes.md` — names ODD as authoring-time discipline + Outcomes as runtime grader; documents stack-when-both-available shape; names API-key-vs-subscription divergence. | C3 |
| AC.V040.6 — Outcome-altitude AC for code-gen | The V040.1 outcome AC exercises the full path against real `claude -p` subprocess on a real fixture, no monkeypatch. | Folded into C2 (outcome-altitude verification cycle) |

### Cycle decomposition rationale

C1+C2 split AC.V040.1 (parent estimate 4-8hr exceeds >5hr halt trigger). C3 bundles V040.2+V040.3+V040.5 (each 15-30min; "compose-on-Claude-substrate" theme; per-AC sub-cycles add coordination overhead with no AC tightening). C4 isolates AC.V040.4 ProgramBench (largest external dependency; highest-leverage EV lever per harness-landscape §5 EV.1). C5 mirrors v0.3.0 Cycle 7 ceremony.

### Connection to v0.5.0+

v0.4.0 enables: v0.5.0 binary-usage observation harness (which feeds the same code-gen pipeline with a third evidence-row source — binary execution traces); v0.6.0 non-tech-user surface (which translates user intent into the planning input the v0.4.0 pipeline consumes); v0.5.0 ProgramBench Variant B leaderboard submission (which composes on v0.4.0's docs-only baseline as the comparison anchor).

### NOT in scope at v0.4.0

- Binary-usage observation harness → v0.5.0.
- mini-SWE-agent compatibility surface → v0.5.0 (v0.4.0 ProgramBench docs-only Variant A is the comparison baseline; binary-feeder Variant B is v0.5.0).
- ProgramBench leaderboard submission → v0.5.0 AC.V050.4 (v0.4.0's report stays at `docs/experiments/programbench-v0-docs-only.md`; submission action is v0.5.0).
- SWE-bench Pro submission → v0.4.0 successor / v0.5.0 companion per harness-landscape RR.3 (surfaced for owner ruling at end of v0.4.0).
- `loam status` background-work-inventory primitive → harness-landscape RR.1 surfaced for owner ruling; not committed to v0.4.0 absent ratification.
- User-visible token-budget surface → v0.6.0 candidate per harness-landscape RR.2.
- Negative-alignment detection (objective-aligned vs objective-contradicting diff classification) → v0.8.0.
- Dreaming / Multi-Agent / Webhooks composition → API-keyed; OUT OF SCOPE per `feedback_no_anthropic_api_key.md`.

---

## §3 — Cycle decomposition (light per-cycle entry per trim discipline)

Each cycle's full AC enumeration lives in its sub-plan-doc stub at `docs/plans/v0-4-0-cycle-N-<slug>.md`. The stubs land in the same commit as this master plan and finalize at cycle-dispatch time per `plan-docs-author` SKILL master-plan-vs-sub-plan trim discipline.

### Cycle 1 — Code-gen-from-objectives core

- **Theme.** The dispatch surface (`loam build-next` or named successor) accepts objectives.yaml + gap-inventory.yaml + build-next.yaml + emits a unified diff or branch where each commit carries an `objectives:` block per amendment #38 `lifted_from` schema.
- **Scope-tightening.** Parent AC.V040.1 covers full code-gen integration end-to-end; C1 narrows to "dispatch surface exists + objectives→diff plumbing works against synthetic fixture; outcome-altitude verification against real-world target deferred to C2."
- **Fence.** PRIMARY likely `plugins/dev-sdlc/code-gen/` (NEW component) or extension of `plugins/dev-sdlc/odd-extractor/build-next/`. Secondary: CLI surface in `plugins/dev-sdlc/cli.py` (or component-equivalent). Read-only: `framework/memory-system/`, sealed `objective-tracker` (consume schema; don't widen).
- **AC family seed.** `AC.CGC.*` — CLI flag + manifest entry; objectives.yaml ingestion + validation; LLM-routed dispatch through `claude -p` (`--strict-mcp-config` + empty MCP config tempfile per the v0.2.5 C5 invariant); diff generation; per-commit `objectives:` block population (schema per amendment #38); SOFT-altitude smoke against synthetic fixture.
- **Smoke.** D2 steady-state — synthetic-fixture run produces non-empty diff with `objectives:` block per commit; D1/D3/D4/D5/D6 deferred-to-C2 or n/a per code-gen-altitude.
- **Dependencies.** None (first cycle). Consumes objective-tracker schema (sealed component — read-only).
- **Out-of-scope.** Outcome-altitude verification against real-world fixture (C2); Routines runtime layer (C3); ProgramBench tasks (C4).
- **AI-time.** ~120–240 min (~1000–2000 tool calls). Largest cycle in v0.4.0.

### Cycle 2 — Code-gen outcome-altitude verification on `jsts-playwright-app`

- **Theme.** Exercise C1's code-gen path end-to-end against the `jsts-playwright-app` canonical fixture; verify outcome-altitude AC requirement per `docs/odd-llm-grounding.lean.md` "Outcome-altitude AC requirement"; tighten AC.V040.1 to closed.
- **Scope-tightening.** Parent AC.V040.1+V040.6 covers integration + outcome-altitude; C2 narrows to "real `claude -p` subprocess + real `jsts-playwright-app` fixture + no monkeypatched stubs + asserts on the produced diff's per-commit `objectives:` block."
- **Fence.** PRIMARY: outcome-altitude test under `plugins/dev-sdlc/code-gen/tests/test_AC_V040_6_outcome_altitude.py` (or component-equivalent path post-C1). Secondary: `jsts-playwright-app` fixture access (read-only). Universal admissions: any prompt-shape adjustments in C1's code-gen surface needed to make the test pass (NEW commit, not `--amend`).
- **AC family seed.** `AC.CGV.*` — outcome-altitude test invokes `loam build-next` (or named successor) with real fixture inputs; produces non-empty diff; per-commit `objectives:` block populates with valid `lifted_from = {source_doc, source_ac, source_commit}` data; behavioral assertion that the diff compiles / lints / passes existing fixture tests; AC.V040.1 marked closed in §11 SHA register; AC.V040.6 marked `outcome-altitude: true` per ODD grounding lean §"Outcome-altitude AC requirement".
- **Smoke.** D1 cold-state — fresh-clone fixture run; D2 steady-state — green; D5 cross-session — n/a (single-run code-gen); D6 telemetry — `objectives:` block grep-discoverable in produced diff.
- **Dependencies.** C1 (code-gen surface exists).
- **Out-of-scope.** Multi-fixture verification (jsts-playwright-app is the named canonical; rd-automation-class real-world targets stay v0.5.0+); behavioral test pass-rate scoring (that's ProgramBench territory in C4).
- **AI-time.** ~60–120 min (~500–1000 tool calls).

### Cycle 3 — Substrate composition: Routines + Code Review + Outcomes-pattern ADR

- **Theme.** Three small substrate-composition deliverables sharing the "compose-on-Claude-substrate" theme. Routines wires loam's background-agent dispatches through `claude routine create`; Code Review composition adds plan-author SKILL guidance + 1 example; Outcomes-pattern ADR documents the API-key-vs-subscription architectural divergence.
- **Scope-tightening.** Parent has three independent ACs (V040.2, V040.3, V040.5); C3 bundles per the Lens 5 stopping criterion (each individually 15-30min; per-AC sub-cycles add coordination overhead with no AC tightening).
- **Fence.** PRIMARY for Routines: a memory feedback file (`feedback_routines_runtime_layer.md` or named) + 1 example plan-doc invoking `claude routine create`. PRIMARY for Code Review: `plugins/dev-sdlc/skills/plan-docs-author/SKILL.md` (compose-on-claude-code-review section) + 1 example plan-doc. PRIMARY for Outcomes: `docs/design/odd-vs-outcomes.md` (NEW). Universal admissions: cross-references in `CLAUDE.md` if Routines becomes a named primitive.
- **AC family seed.** `AC.SUB.*` — Routines pattern documented + 1 example plan-doc invokes `claude routine create` (or equivalent verified live name); Code Review SKILL section added + 1 example plan-doc demonstrates composition; Outcomes-pattern ADR exists at `docs/design/odd-vs-outcomes.md`, names ODD-authoring-time + Outcomes-runtime-grader divergence, names API-key-vs-subscription architectural choice with rationale, documents stack-when-both-available shape; outcome-altitude AC: ADR cross-references resolve from `docs/release-roadmap.md` §3 v0.4.0 line `Compose on `claude code review`...`.
- **Smoke.** D2 steady-state — `grep -n "claude routine create" docs/` returns the example plan-doc + the memory feedback file; `grep -n "compose-on-claude-code-review" plugins/dev-sdlc/skills/plan-docs-author/SKILL.md` returns the new section; `find docs/design -name "odd-vs-outcomes.md"` returns one file. D1/D3/D4/D5/D6 n/a (docs+SKILL).
- **Dependencies.** None (parallelizable with C2 in principle; serialized per `feedback_serialize_amendment_builds`).
- **Out-of-scope.** Multi-Agent / Dreaming / Webhooks substrate composition (API-keyed; OUT OF SCOPE); Routines as a structurally-enforced loam primitive (v0.7.0 structural-enforcement substrate); BYOK divergence beyond Outcomes-pattern surface (T7 tension; harness-landscape RR commentary; F2 RF only).
- **AI-time.** ~45–90 min (~400–750 tool calls; three small docs+SKILL deliverables; midpoint ~67 min). Composes with Routines API verified-live per conference research §1 cell #4 ("Released") — no API-availability risk at this date.

### Cycle 4 — ProgramBench v0 docs-only baseline (Variant A)

- **Theme.** Run docs-only feeder → reverse-ODD → ODD-grounded code-gen on 3-5 small ProgramBench tasks (jq, ripgrep candidates per `programbench-loam-benchmark-v0.md` §"v0 experiment shape"). Score: behavioral test pass rate. Report at `docs/experiments/programbench-v0-docs-only.md`.
- **Scope-tightening.** Parent AC.V040.4 covers Variant A only; C4 narrows to "3-5 small ProgramBench tasks; docs-only feeder (NOT binary-feeder Variant B); pass-rate report; baseline + Variant A side-by-side." Variant B (docs+binary feeder) is v0.5.0 territory.
- **Fence.** PRIMARY `docs/experiments/programbench-v0-docs-only.md` (NEW; `docs/experiments/` is a NEW directory at v0.4.0). Read-only: `plugins/dev-sdlc/odd-extractor/`, `plugins/dev-sdlc/code-gen/` (post-C1+C2), ProgramBench public task definitions. Universal admissions: small task-fixture stubs under `plugins/dev-sdlc/odd-extractor/tests/fixtures/programbench/` if needed for the v0 run (TBD at C4 plan-doc time).
- **AC family seed.** `AC.PBN.*` — task selection rationale (3-5 small tasks; jq, ripgrep candidates; named selection rationale); baseline run (plain code-gen via mini-SWE-agent equivalent or loam-baseline-without-ODD); Variant A run (docs-only feeder → reverse-ODD → ODD-grounded code-gen via C1+C2 surface); behavioral test pass rate captured per task per variant; report doc with comparison table; outcome-altitude AC: report cross-references resolve + the named pass-rate numbers are reproducible by re-running the experiment with stated inputs.
- **Smoke.** D1 cold-state — n/a (synthetic experiment); D2 steady-state — report doc renders; numbers match the run's recorded outputs; D6 telemetry — per-task per-variant raw outputs preserved for audit.
- **Dependencies.** C1 + C2 (code-gen surface exists + outcome-altitude verified).
- **Out-of-scope.** Variant B docs+binary feeder (v0.5.0); ProgramBench leaderboard submission (v0.5.0 AC.V050.4); SWE-bench Pro submission (harness-landscape RR.3; surfaced for owner ruling); >5 task scope.
- **AI-time.** ~75–150 min (~600–1250 tool calls; per programbench doc estimate ~2-4.5hr but Variant B-related cost excluded). Midpoint ~110 min.

### Cycle 5 — Release-level smoke gate + STATE.md SHIPPED rollup

- **Theme.** v0.4.0 SHIPPED sealing event. Master plan §3 entry collapses into `docs/STATE.md` SHIPPED record per release-roadmap §7 protocol; release-roadmap §3 → §2 collapse with seal anchor.
- **Scope-tightening.** Parent has no dedicated AC for release-level smoke gate at master-plan altitude (each cycle handles its own smoke); C5 narrows to "release-roadmap §3 v0.4.0 → §2 with seal SHA + apply SHA per cycle; STATE.md SHIPPED rollup row added; aggregate cycle-count + tests-green count + smoke verdict named." Mirrors v0.3.0 Cycle 7 ceremony shape.
- **Fence.** PRIMARY `docs/release-roadmap.md` (§3 → §2 collapse). Secondary `docs/STATE.md` (SHIPPED narrative-paragraph append per v0.2.5.1 / v0.3.0 precedent). Universal admissions: master plan §11 SHA register backfill.
- **AC family seed.** `AC.SHIP-V040.*` — release-roadmap §3 → §2 collapse; STATE.md SHIPPED row (objective sentence + seal anchor); aggregate cycle count = 5; aggregate tests-green count summarized; aggregate smoke verdict named; outcome-altitude AC: release-roadmap §2 + STATE.md SHIPPED row + master plan §11 SHA register all resolve to the same set of seal SHAs.
- **Smoke.** Inherited from C1–C4.
- **Dependencies.** C1–C4 sealed.
- **Out-of-scope.** Tag push, GitHub Releases marked `--latest`, public-remote push to `lukeivers/loam` (all owner actions per `docs/release-versioning-policy.md` §Tagging).
- **AI-time.** ~20–45 min (~150–375 tool calls).

### Cycle ladder summary table

| Cycle | Slug | AC closure | AI-time band | Dependency |
|---|---|---|---|---|
| 1 | code-gen-from-objectives-core | AC.V040.1 (partial; SOFT) | 120–240 min | none (first) |
| 2 | code-gen-outcome-altitude-verification | AC.V040.1 (close); AC.V040.6 | 60–120 min | C1 |
| 3 | substrate-composition-routines-codereview-outcomes | AC.V040.2 + V040.3 + V040.5 | 45–90 min | none (parallelizable; serialized per discipline) |
| 4 | programbench-v0-docs-only-baseline | AC.V040.4 | 75–150 min | C1 + C2 |
| 5 | release-level-smoke-gate-and-ship | sealing ceremony | 20–45 min | C1–C4 |

**Aggregate band: 320–645 min ≈ 5.3–10.75 hr AI-time. Midpoint ~8 hr.** Within parent §3 estimate (6–11 hr; midpoint ~8 hr). Owner gate-review time separate (~50 min total across 5 cycle ratifications).

---

## §4 — AI-time band aggregate

Per duration-estimation rubric (`wall_clock_minutes ≈ tool_calls × 0.1–0.15`):

- C1: 120–240 min
- C2: 60–120 min
- C3: 45–90 min
- C4: 75–150 min
- C5: 20–45 min

**Aggregate range: 320–645 min ≈ 5.3–10.75 hr.** Midpoint ~8 hr (matches parent §3 estimate ~8 hr midpoint). Owner gate-review time separate.

---

## §5 — Dependencies + cycle ordering

- **C1 first.** Code-gen surface must exist before C2 (verification), C4 (ProgramBench Variant A consumes C1+C2 surface). C3 is parallelizable in principle but serialized per `feedback_serialize_amendment_builds` (single working tree; index.lock + `loam amend` + tests can race across parallel builds without worktree isolation).
- **C2 depends on C1.** Outcome-altitude verification needs the code-gen surface to exist.
- **C3 depends on nothing structurally** (substrate composition is doc/SKILL/ADR work; doesn't read C1/C2 surface). Sequenced after C2 in the serial ladder for working-tree discipline.
- **C4 depends on C1 + C2.** ProgramBench v0 Variant A consumes the verified code-gen surface.
- **C5 depends on C1–C4 sealed.** Release ceremony.

**Suggested execution order:** C1 → C2 → C3 → C4 → C5. Strictly serial.

---

## §6 — Methodology amendments

None proposed at master-plan altitude. v0.4.0's substantive surface is on the deliverable shape (code-gen-from-objectives), not on methodology rules. The two methodology touch-points:

1. **Outcome-altitude AC requirement applies hard** to AC.V040.1's outcome-altitude (AC.V040.6) per `feedback_test_outcome_altitude_required.md`. C2 closes this.
2. **`claude -p --strict-mcp-config` invariant** applies to every C1 LLM-routed dispatch per the v0.2.5 C5 propagation. C1's plan-doc verifies the invariant inline.

If C1's code-gen surface surfaces a methodology gap (e.g., the `objectives:` block schema doesn't compose cleanly with multi-commit diffs), surface for owner ruling at dispatch time and amend the methodology before continuing.

---

## §7 — Risk register

| Risk | Mitigation |
|---|---|
| C1 scope underestimated; 2-4hr band insufficient | Halt-trigger §8.1 fires; re-extend into C1a + C1b at cycle dispatch. |
| AC.V040.6 outcome-altitude test surfaces production-path defects in code-gen | Treated as in-cycle correctives in C2 (NEW commits, not `--amend`); if defects multiply beyond 3, halt for re-extension. |
| ProgramBench task selection wrong (jq/ripgrep too small or wrong shape) | C4 plan-doc names task selection rationale + escapes to alternative tasks if v0 run produces no signal. |
| Routines API behaviour differs from documented shape | Conference research confirmed "Released" status; if `claude routine create` doesn't exist at C3 dispatch time, halt-and-surface; C3 ADR documents the divergence. |
| Outcomes-pattern ADR's API-key-vs-subscription divergence triggers BYOK pressure | Per harness-landscape research §4 Tension #1: hold the line, name the divergence explicitly. F2 RF surface only; not a v0.4.0 blocker. |
| `objectives:` block schema (amendment #38 `lifted_from`) doesn't compose with multi-commit diffs | C1 plan-doc verifies single-commit case first; multi-commit extension is C2's tightening surface or v0.4.1 patch. |
| jsts-playwright-app fixture state at C2 dispatch | C2 plan-doc verifies fixture surface pre-dispatch; if fixture shape changed since v0.1.8, fixture-update is in-cycle. |

---

## §8 — Halt triggers (in-flight)

Conditions that fire during cycle execution stop the build for surface-and-RF (not master-plan-author halts):

1. Any cycle's actual AI-time exceeds upper band by >50% — surface for owner ruling on scope split or carry to v0.4.1.
2. C1 AC family count grows beyond seed (>8 ACs) — ODD §2.5 violation triage; re-extend.
3. C2 outcome-altitude verification fails on real `jsts-playwright-app` fixture — surface for owner ruling on whether this is a code-gen defect (in-cycle corrective, NEW commit) or a deeper methodology gap (escalate).
4. C3 Routines API doesn't exist at the expected name (`claude routine create` or equivalent) — halt-and-surface; verify against current `claude --help` + Anthropic docs; ADR documents whatever the current name is.
5. C4 ProgramBench tasks all produce zero signal (no behavioral tests pass on baseline OR Variant A) — surface for owner ruling on whether to (a) expand task list, (b) ship the negative result as the v0 baseline anyway, or (c) carry to v0.4.1.
6. Push or `--amend` attempt in any cycle — immediate halt; corrective NEW commit + RF surface.
7. C2 surfaces an Anthropic-API-key requirement in the code-gen path (e.g., a `claude -p` flag introduced post-v0.3.0 changes default behaviour) — halt-and-surface; verify the no-API-key invariant; corrective if needed.

---

## §9 — Out-of-scope

- v0.5.0 binary-usage observation harness; mini-SWE-agent compatibility; ProgramBench leaderboard submission Variant B.
- v0.6.0 non-tech-user surface, channel-config slot, memory-doc skeleton template.
- v0.7.0 structural enforcement of swarming + four named primitives (FR.1/FR.2/FR.3/F6 + meta-decision-haiku SKILL).
- v0.8.0 negative-alignment detection.
- v0.9.0 deep personalization through interaction capture.
- Outcomes / Multi-Agent / Dreaming / Webhooks runtime composition (API-keyed; OUT OF SCOPE per `feedback_no_anthropic_api_key.md`; documented divergence in C3's ADR).
- BYOK / multi-provider (subscription-only architectural floor).
- `loam status` background-work-inventory primitive (harness-landscape RR.1; surfaced for owner ruling — not a v0.4.0 commit).
- User-visible token-budget surface (harness-landscape RR.2; v0.6.0 candidate).
- SWE-bench Pro submission (harness-landscape RR.3; surfaced for owner ruling).
- Methodology paper / arXiv preprint (harness-landscape EV.2; v0.5.0/v0.6.0 candidate).
- Public walkthrough video (harness-landscape EV.3; v0.6.0 companion).
- Tag push, GitHub Releases marked `--latest`, public-remote push (owner-action-separate per §Tagging policy).

---

## §10 — F2 Ruthless Feedback (gaps named this turn)

1. **C1's 2-4hr band at upper edge of cycle ceiling.** Parent §3 estimates AC.V040.1 alone at 4-8hr; C1+C2 split brings each within 1-3hr but C1 at 240 min is the upper edge. Halt-trigger §8.1 fires if C1 dispatch can't fit; C1 splits into C1a (CLI + ingestion) + C1b (LLM-dispatch + diff gen). Pushes v0.4.0 to 6 cycles (under 7-ceiling).

2. **AC.V040.4 ProgramBench task selection unspecified at master-plan altitude.** Parent + source artefact mention jq + ripgrep as candidates; final list is C4 plan-doc responsibility. Halt-trigger §8.5 catches zero-signal case.

3. **Routines API name not verified live.** Conference research §1 #4 confirms "Released" but `claude routine create` exact invocation isn't verified against `claude --help` at master-plan-author time. C3 plan-doc verifies + halt-and-surface if divergent.

4. **Outcomes ADR is most-likely BYOK-pressure surface.** Per harness-landscape §4 Tension #1, BYOK trend is industry-wide; ADR tone must name divergence as deliberate architectural choice (translation-burden-reduction story per VALUE_PROPOSITION), NOT a deficiency.

5. **`objectives:` block multi-commit case unverified.** v0.4.0 likely produces multi-commit diffs (AC-per-commit per §2.5 traceability). Whether amendment #38 `lifted_from` round-trips cleanly across multiple commits is unverified. C1 plan-doc verifies single-commit; multi-commit may be in-cycle extension or v0.4.1 patch.

6. **Outcome-altitude AC pre-arrangement risk.** Per `feedback_test_outcome_altitude_required.md`, test must NOT pre-arrange state the production code would produce. For code-gen this means the test can't hand-author objectives.yaml — it must come from a real prior reverse-ODD run. C2 plan-doc names rubric explicitly.

7. **No `loam status` primitive lands in v0.4.0** despite harness-landscape RR.1 surfacing it as a high-leverage forward-pull. Conservative read: scope-lock v0.4.0 to release-roadmap §3 ACs; RR.1 ratification is separate gate. **Surfaced for owner ruling.**

---

## §11 — Authority + provenance trail (canonical SHA register, backfilled as cycles seal)

### Provenance trail

- `docs/release-roadmap.md` §3 v0.4.0 — AUTHORITY for objective, ACs (V040.1–V040.6), constraints, AI-time bands.
- `docs/release-versioning-policy.md` — SemVer commitment + END-USER class + quality gate.
- `docs/odd-semver-pinning.md` — cycle-vs-minor composition rules.
- `docs/odd-llm-grounding.lean.md` — outcome-altitude AC requirement.
- `docs/leverage-discipline.md` — rubric for cycle prioritization.
- `plugins/dev-sdlc/skills/plan-docs-author/SKILL.md` — canonical plan-doc shape.
- `plugins/dev-sdlc/skills/dispatch-brief-authoring/SKILL.md` — cycle dispatch shape.
- `plugins/dev-sdlc/skills/odd-test-altitude-discipline/SKILL.md` — pre-arrangement detection + outcome-altitude rubric.
- `<workspace>/.scratch/claude-output/claude-conference-features-2026-05-06.md` §4 — Routines + Code Review composition; Outcomes-pattern divergence note.
- `<workspace>/.scratch/claude-output/programbench-loam-benchmark-v0.md` — Variant A baseline shape.
- `docs/plans/research/harness-landscape-and-roadmap-rerank.md` — re-rank research; T2 confirms v0.4.0 positioning correct; RR.1/RR.2/RR.3 surfaced separately.
- `docs/plans/amendment-38-objective-tracker-schema-widening.md` — `lifted_from = {source_doc, source_ac, source_commit}` schema, reused as the per-commit `objectives:` block.
- `docs/plans/v0-3-0-master-plan.md` — precedent shape for this master plan.
- `docs/STATE.md` — v0.3.0 SHIPPED state, predecessor.

### Canonical SHA register (backfilled as cycles seal)

| Cycle | Apply SHA | Seal SHA |
|---|---|---|
| 1 — code-gen-from-objectives-core | `a7d1182b` | `cc2efbba` |
| 2 — code-gen-outcome-altitude-verification | `b3586468` | `f031c89c` |
| 3 — substrate-composition-routines-codereview-outcomes | `f9771855` | `2d1e7f01` |
| 4 — programbench-v0-docs-only-baseline | `fdbdc918` | `e5c62463` |
| 5 — release-level-smoke-gate-and-ship | `1733a7df` | `7787a226` |

---

## §12 — Acceptance gate (pre-cycle conditions)

- [x] Master plan + 5 cycle stubs land in one commit.
- [x] 5 cycles in dependency order; each entry: theme + scope-tightening + fence + AC family seed + smoke + deps + OOS + AI-time.
- [x] Word count within 2500–4500 target (count verified at commit time; estimated ~3700 words).
- [x] Each release-roadmap AC.V040.1–V040.6 maps to a named cycle (no orphan ACs).
- [x] No "rebuild" terminology in new prose; no Anthropic API key in any cycle.
- [x] Composes with release-roadmap §3 (references; doesn't duplicate).
- [x] §10 F2 RF surfaces ≥7 honest doubts; §8 halt triggers named.
- [x] Each cycle's AC family seed names ≥1 outcome-altitude AC.
- [x] HARD HALT BEFORE OWNER RATIFICATION — no `loam amend apply` / `loam amend seal` / cycle dispatches in this turn; plan-only.

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

| Decision | Choice | Rationale |
|---|---|---|
| Cycle count | 5 | Each cycle's AC strictly tighter than parent v0.4.0; further decomposition adds only coordination overhead (Lens 5). |
| AC.V040.1 split C1 + C2 | C1 = SOFT-altitude core; C2 = outcome-altitude on `jsts-playwright-app` | Parent estimates AC.V040.1 at 4-8hr; >5hr is halt trigger per dispatch directive. Split keeps each in 1-3hr range. |
| C3 bundle (V040.2+V040.3+V040.5) | Bundled | Each 15-30min per conference research §4; per-AC sub-cycles add coordination overhead with no AC tightening; share "compose-on-Claude-substrate" theme. |
| AC.V040.6 folded into C2 | C2 closes both V040.1 and V040.6 | AC.V040.6 is the outcome-altitude requirement on V040.1; same verification cycle preserves traceability. |
| Cycle ordering | C1 → C2 → C3 → C4 → C5 strictly serial | Per `feedback_serialize_amendment_builds`; C3 parallelizable in principle but serialized for working-tree discipline. |
| ProgramBench scope | 3-5 small tasks; Variant A only | Parent AC.V040.4 explicit; Variant B + leaderboard submission are v0.5.0. |
| `max_planner_depth` | 1 | Per Lens 5. Cycle plan-doc author may decompose at dispatch if scope-confidence drops. |
| Tag-push policy | Owner-action-separate; no tag in any cycle | Per `docs/release-versioning-policy.md` §Tagging. C5 sealing is local-only. |
| `loam status` (RR.1) NOT pulled forward | Out-of-scope at v0.4.0 | Harness-landscape RR.1 surfaced separately; v0.4.0 scope-locked to release-roadmap §3 ACs. F2 RF §10.7 for owner ruling. |
| Outcomes ADR framing | Deliberate architectural choice with rationale, not deficiency | Per harness-landscape §4 Tension #1: hold subscription-only line; name BYOK divergence explicitly. |
| Outcome-altitude pre-arrangement rubric | C2 plan-doc names rubric explicitly | Per `feedback_test_outcome_altitude_required.md`. Code-gen can't hand-author objectives.yaml; must come from real prior reverse-ODD run. |
| `objectives:` block schema | Reuse amendment #38 `lifted_from = {source_doc, source_ac, source_commit}` | Existing sealed schema; reuse rather than re-author. C1 verifies multi-commit case. |
| END-USER class quality gate met | Translation-burden delta: "user can request feature build, receive working code with provenance" | Per `docs/release-versioning-policy.md` §Quality-gate. v0.3.0 was META-FRAMEWORK; v0.4.0 is END-USER (prime-objective deliverable activates). |
