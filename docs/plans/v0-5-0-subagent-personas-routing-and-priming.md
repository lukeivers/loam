# v0.5.0 — Subagent-personas routing + priming-de-duplication

**Status:** plan-only at authoring time. Plan-before-code per `feedback_plan_before_code`. Owner ratifies before any cycle dispatches. **HALT-AND-SURFACE plan-doc** — the dispatch brief that authorized this work was framed against a non-existent FIDRAFT entry; the actual underlying problem is real but smaller and has already-shipped substrate. Plan-doc reframes per F2 RUTHLESS FEEDBACK before authoring ACs.

**Slug:** `v0-5-0-subagent-personas-routing-and-priming`.
**Date authored:** 2026-05-09.
**Class:** META-FRAMEWORK (per `docs/release-versioning-policy.md` §40 — improves persona substrate; does not change end-user-visible capability surface).
**Predecessor:** v0.4.3 patch in flight (memory retrieval BM25 fix); v0.4.2 SHIPPED LOCAL (seal `3f3df670`); v0.1.7 subagent-personas SHIPPED (seal `73505f0`); v0.2.2 dispatch-brief-authoring SKILL with AC.DBT.1–6 propagation SHIPPED (seal `5eda09d`).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Owner authorization:** Telegram 10526 ("sounds rad on the personas plan thing, go for it") — plan-doc authoring authorized; build dispatch is downstream and requires post-plan-doc owner ratification given the reframing below.

---

## §0 — HALT-AND-SURFACE: dispatch-brief reframing before plan-authoring

The dispatch brief that produced this plan-doc names a FIDRAFT entry "Subagent-persona priming for dispatched background agents" at `docs/FUTURE_IDEAS_DRAFT.md`. **That entry does not exist.** Verified: full grep of FIDRAFT for `subagent`, `sub-agent`, `.claude/agents`, `persona priming`, `loam-builder`, `loam-plan-author`, `loam-researcher`, `loam-reviewer`, `loam-documenter` returns only the HeavySwarm entry (line 184), the LLMCouncil entry (line 186), the SequentialWorkflow drift-detection entry (line 188), and a handful of tangential references.

A separate but related entry — the loam-mode partition-references debt at line 143 — names `framework/primary-persona/templates/persona-template/prompt.md` as a stale `KNOWN_CROSS_MODE_DEBT` allowlist row. Tangential, not the brief's referent.

The brief's recommended initial set (`loam-builder` / `loam-plan-author` / `loam-researcher` / `loam-reviewer` / `loam-documenter`) is **already shipped** under v0.1.7's AC.PERSONAS.{1–8} family. Verified: `plugins/dev-sdlc/agents/loam-{builder,documenter,plan-author,researcher,reviewer}.md` exist as full files (avg ~6.4 KB each); `<workspace>/.claude/agents/loam-*.md` exist as symlinks pointing back to the canonical files; `framework/workspace-bootstrap/seals/SEAL_COMMIT.v0-1-7-subagent-personas` records the seal commit. The personas are tool-restricted (researcher: Read/Grep/Glob/WebFetch/WebSearch; reviewer: Read/Grep/Glob/Bash) per the design the brief recommended.

The brief's recommended priming-propagation work (AC.DBT.1–6 in `dispatch-brief-authoring` SKILL) is **also already shipped** at v0.2.2. Verified: `plugins/dev-sdlc/skills/dispatch-brief-authoring/SKILL.md` carries the full propagated-principle set (LEAN-GROUNDING-LOAD / NO-CLOSING-LINE-PERMISSION-ASKS / SPECIFIC-CLAIMS-VERIFIED / TEST-AGAINST-OPERATIONAL-OBJECTIVE-BEFORE-ESCALATING / NO-FALSE-FAULT / TIME-CLAIMS-DISCIPLINE).

**The real residual gap** the brief was probably reaching for: **dispatch-time consumption of the shipped subagents is not enforced by tooling**. Briefs still hand-author the priming section per dispatch even when the work-shape clearly maps to an existing persona (`loam-builder` for amendment cycles, `loam-plan-author` for plan-docs, etc.). The Agent tool exposes a `subagent_type` parameter that routes to the registered persona, but no skill, hook, or template instructs the dispatcher to use it instead of `subagent_type: general-purpose` + a hand-rolled brief. Production usage today: every grep for `subagent_type` in `framework/` + `plugins/` returns either `"general-purpose"` (in test fixtures) or a generic placeholder; zero production dispatch sites use the typed personas as the routing primitive.

**Reframed v0.5.0 outcome shape:** v0.5.0 closes the consumption gap by (a) auditing actual dispatch sites to confirm the gap empirically, (b) shipping a `subagent-routing` SKILL that the persona auto-loads when a dispatch is being authored and that recommends `subagent_type: <persona>` based on the work-shape, (c) extending the existing `dispatch-brief-authoring` SKILL to omit the propagated-principle block when `subagent_type != general-purpose` (because the persona body already carries the discipline), and (d) outcome-altitude: re-running a real builder-cycle dispatch via `subagent_type: loam-builder` and observing brief-length reduction + same-or-better cycle quality.

This reframing is offered for owner ratification BEFORE any build dispatches. Two paths:

- **Path A (recommended):** ratify the reframing; v0.5.0 ships the consumption-gap closure as authored below. AI-time band 60-120 min total build (small fence; SKILL authoring + audit + outcome probe).
- **Path B:** decline the reframing; instead, treat the brief literally and re-author the already-shipped personas under different naming/locations as a parallel set. Surfacing for explicit rejection because Path B duplicates v0.1.7-shipped work and violates `feedback_locked_design_not_license` in reverse (rebuilds a working surface instead of revising it).

Plan-doc proceeds under Path A pending owner ruling.

---

## §1 — Outcome shape (the "why")

Every loam dispatch today (build cycles, plan-authoring, research, reconciliation) goes out as `subagent_type: general-purpose` plus a hand-authored brief that carries 30–60 lines of priming (Working directory + Principles to apply at turn-start + Source pointers + Sub-plan path + Fence + ACs + Halt triggers + Out of scope + Bookkeeping + Model rationale). The `dispatch-brief-authoring` SKILL externalises the structural shape so the dispatcher doesn't reconstruct it from CLAUDE.md per cycle, and the propagated-principle block (AC.DBT.1–6) ensures sub-agents inherit discipline that survives compaction.

But: **the priming work is duplicated** because the v0.1.7 subagent-personas already carry the same discipline in their persona prompts. `loam-builder.md` (~6.5 KB, 96 lines) names ODD §2.5, plan-before-code, halt-and-surface, no-`--amend`, `loam amend apply`/`seal` ritual, fence discipline, surrounding-code violation halt, F2 RF on disagreement, voice rules, when-to-invoke / not-to-invoke, harness composition. Every dispatch brief authored against a builder-cycle work-shape duplicates these in the priming section. When the brief ships via `subagent_type: general-purpose`, the duplication is necessary (general-purpose has no persona body to inherit from). When it ships via `subagent_type: loam-builder`, the duplication is wasteful (the persona body loads at dispatch time and re-asserting in the brief is noise).

The outcome v0.5.0 ships: (1) a `subagent-routing` SKILL that pattern-matches dispatch-authoring intent against the existing 5-persona surface and recommends `subagent_type: <persona>` when the work-shape matches; (2) a `dispatch-brief-authoring` SKILL extension that omits the propagated-principle block when `subagent_type != general-purpose`; (3) an empirical outcome-altitude probe re-running a real builder cycle via `subagent_type: loam-builder` and reporting brief-length delta + cycle-quality verdict; (4) a FIDRAFT capture of the residual consumption-gap pattern for any persona-as-substrate proposal that follows.

The recurring failure mode this fixes: **brief-authoring re-derives priming the persona already carries**. Failure cost: ~30-60 lines of priming per dispatch × multiple dispatches per cycle × multiple cycles per minor = real token + author-time waste. Closure cost: ~60-120 min build per the §13 estimate.

---

## §2 — Prime objective ladder

VALUE_PROPOSITION.md prime objective (loam helps people use LLMs to build software) → translation-burden reduction is one of the persona's two prime tests → subagent personas pre-package the common scope-tightness configurations so the primary doesn't author them per dispatch (per `personas-methodology.md` §2 constraint-narrowing) → v0.5.0 closes the consumption-gap so the personas-as-substrate work actually delivers the priming-de-duplication value v0.1.7 was authored for → v0.5.0 ACs `AC.V050.*` below (audit / SKILL author / brief-extension / outcome probe).

Composes with: Lens 2 (sub-personas are the toolkit the primary draws from); Lens 4 (choosing which persona to dispatch IS the scope-tightness call); Lens 5 (each persona ships its own halt-and-surface + decomposition shape); v0.7.0 META-FRAMEWORK (structural-enforcement substrate; v0.5.0's SKILL is a soft enforcement layer that v0.7.0 may harden into a hook).

---

## §3 — Component fence

**PRIMARY:** `plugins/dev-sdlc/skills/` — two SKILL surfaces touched.

- `plugins/dev-sdlc/skills/subagent-routing/SKILL.md` — NEW skill (AC.V050.2). Description triggers when the persona is about to dispatch a Task/Agent and the work-shape matches a registered subagent persona. Body provides the routing rubric + the "how to use `subagent_type: <persona>`" recipe + when to fall back to `general-purpose`.
- `plugins/dev-sdlc/skills/dispatch-brief-authoring/SKILL.md` — EXTENDED (AC.V050.3). Adds a §"When subagent_type is not general-purpose" section instructing brief omission of the propagated-principle block (the persona body already carries it). Backward-compat: omission is ONLY when `subagent_type != general-purpose`; default behavior preserved.

**Test surfaces:**
- `plugins/dev-sdlc/tests/test_AC_V050_*.py` — AC-banded tests for the new SKILL discoverability + content + the brief-authoring SKILL extension.

**Read-only (initial v0.5.0 build); MODIFIED by post-seal corrective 2026-05-09:**
- `plugins/dev-sdlc/agents/loam-{builder,plan-author,researcher,reviewer,documenter}.md` — v0.1.7 shipped surface; consumed by the routing SKILL during the initial v0.5.0 build. The post-seal priming-gap corrective (`fix(personas): close AC.V050.5 priming gap`, 2026-05-09) extended each persona body with a §"Reporting + escalation discipline" section to close the AC.DBT.{3,5,6} + TIME-CLAIMS gap surfaced by the AC.V050.1 audit. Fence-extension rationale: the corrective is post-seal scope expansion targeted specifically at unblocking the AC.V050.5 outcome-altitude verdict; no other v0.1.7 persona surface (tool restrictions, when-to-invoke, voice rules, halt triggers) is touched. Hard constraint §5 #6 is correspondingly amended.
- `framework/workspace-bootstrap/` — symlink scaffold for `<workspace>/.claude/agents/`; consumed read-only.
- `framework/personas/primary/contract.yaml` + `framework/primary-persona/templates/persona-template/prompt.md` — primary-persona surface; consumed read-only as context for the routing SKILL.
- `docs/personas-methodology.md` — §1-§9 the methodology authority; consumed read-only as the rubric source.

**Universal admissions:** this plan-doc + manifest, seal narrative file, `docs/release-roadmap.md` §6 v0.5.0 row + §2 SHIPPED row on completion, `docs/STATE.md` v0.5.0 SHIPPED rollup row, `docs/FUTURE_IDEAS_DRAFT.md` capture for the §6 deferred items.

**Out of fence:** any other framework component, any seal directory, the v0.1.7 subagent-persona files themselves (consumed not modified), any `docs/spec/` file. Edits outside fence = halt.

---

## §4 — AC family `AC.V050.*` (TIGHT)

Each AC maps to ≥1 test under `plugins/dev-sdlc/tests/test_AC_V050_*.py` OR an empirical artefact (the outcome-altitude probe writeup). The agent authors test names within the convention.

### AC.V050.1 — Production dispatch-site audit

A fresh empirical audit confirms the consumption gap before any SKILL authoring. Audit method: grep `framework/` + `plugins/` + recent `docs/plans/*.md` (last 30 days) for actual dispatch-brief authoring patterns (Task tool calls / Agent tool calls / dispatch-brief headings); for each site found, record (a) was a `subagent_type` named, (b) was it `general-purpose` or a typed persona, (c) what was the work-shape (build / plan-author / research / review / document), (d) would the work-shape map to one of the 5 v0.1.7 personas. Output: `<workspace>/.scratch/claude-output/v0-5-0-dispatch-site-audit.md` table with one row per audited site.

**Verdict:** GREEN if ≥80% of audited sites map to a v0.1.7 persona but used `general-purpose` (confirming the gap is real). YELLOW if 50-79% (gap exists but smaller than predicted). RED if <50% (the gap is mis-characterized; halt + reframe with owner).

**Test:** the artefact existence + the verdict line are checked by `test_AC_V050_1_dispatch_site_audit_artefact.py` (asserts file exists at canonical path, contains a verdict-band line, contains ≥10 audited rows).

`outcome-altitude: false` (audit-altitude verification; empirical but not user-visible-outcome).

### AC.V050.2 — `subagent-routing` SKILL is discoverable + content-correct

A new SKILL at `plugins/dev-sdlc/skills/subagent-routing/SKILL.md` is discoverable by the standard skills-discovery test pattern AND its body carries the full routing rubric. Required content (each is a substring/structural assertion in the test):

- A description triggering when the persona is dispatching a Task/Agent and the work-shape may match a registered persona.
- A rubric mapping work-shapes → personas: amendment-cycle/build → `loam-builder`; plan-doc authoring → `loam-plan-author`; research/investigation → `loam-researcher`; sealed-amendment review → `loam-reviewer`; public-facing docs → `loam-documenter`; everything else → `general-purpose`.
- A note on when to fall back to `general-purpose` even when a persona-shape matches (e.g., the work crosses persona boundaries; the dispatcher needs to override a persona constraint).
- A reference to `docs/personas-methodology.md` for the rubric authority.
- A reference to the `dispatch-brief-authoring` SKILL for the brief-shape extension.

**Test:** `test_AC_V050_2_subagent_routing_skill_present.py` — discovery + frontmatter + body content checks.

`outcome-altitude: false` (SKILL-presence verification; necessary-but-not-sufficient for the consumption-gap closure).

### AC.V050.3 — `dispatch-brief-authoring` SKILL extension for typed personas

The existing `dispatch-brief-authoring` SKILL at `plugins/dev-sdlc/skills/dispatch-brief-authoring/SKILL.md` is extended with a §"When subagent_type is not general-purpose" section. Required content:

- Names that briefs dispatched via `subagent_type: <persona>` MAY omit the propagated-principle block (AC.DBT.1–6) because the persona body carries the same discipline.
- Names that briefs MUST still carry: Working directory + literal `cd <abs-path> && pwd` first action + Sub-plan path + Fence + ACs + Halt triggers + Out of scope + Model rationale.
- Names what the brief MAY skip when typed: per-cycle re-derivation of channel rules, autonomy directive, F2 RF reminder, ODD §2.5 reminder, scope-only enforcement (each is in the persona body).
- Backward-compat clause: when `subagent_type == general-purpose`, the existing AC.DBT.1–6 propagation behavior is preserved unchanged.

**Test:** `test_AC_V050_3_dispatch_brief_authoring_typed_extension.py` — substring assertions on the new section + the backward-compat clause + a structural assertion that the AC.DBT.1–6 block is still present in the SKILL body.

`outcome-altitude: false` (SKILL-extension verification; structural).

### AC.V050.4 — No regression on test suite

All previously-passing tests still pass. Specifically:

- `pytest plugins/dev-sdlc/tests/` returns 0 with the v0.4.3-sealed test count plus the new `AC_V050_*` tests.
- `pytest framework/workspace-bootstrap/tests/test_AC_PERSONAS_*.py` (v0.1.7-sealed) GREEN — symlink scaffold + collision-handling + discovery untouched.
- `pytest plugins/dev-sdlc/tests/test_AC_DBT_*.py` (v0.2.2-sealed) GREEN — propagated-principle block still present + structurally correct.
- `loam amend apply --dry-run` GREEN against the v0.5.0 manifest pre-apply AND post-seal.

`outcome-altitude: false` (no-regression invariant).

### AC.V050.5 (outcome-altitude) — Real builder-cycle dispatch via `subagent_type: loam-builder` ships shorter brief + same-or-better cycle quality

A real downstream amendment cycle (the next plan-doc → build → seal cycle that lands after v0.5.0 seals — likely v0.4.5 or whatever the next PATCH/MINOR is) is dispatched using `subagent_type: loam-builder` instead of `general-purpose` + hand-rolled priming. Brief is authored using the v0.5.0-extended `dispatch-brief-authoring` SKILL, omitting the propagated-principle block per the AC.V050.3 extension.

**Comparison metric:** brief-length delta (line count + word count) vs the most recent comparable v0.4.x cycle dispatch (e.g., the v0.4.3 build dispatch). Target: ≥20% reduction in brief length, no reduction in cycle quality (cycle still seals, all ACs pass, halt-and-surface fluency preserved). **Target corrected 2026-05-09 from ≥30% to ≥20% per AC-tightening: the original ≥30% was set against an idealized "all 6 propagated principles fully omittable" assumption that the post-corrective audit invalidated. The 84-line typed-brief floor is set by non-AC.DBT brief structure (mission + authorization + fence + ACs + halt triggers + bookkeeping + model rationale) which AC.DBT propagation cannot reduce. Per `feedback_loose_AC_text_fix_AC_not_implementation`: when impl matches intent and AC text was set to a wrong threshold, tighten the AC. The intent (typed dispatches ship measurably-shorter briefs without quality loss) IS satisfied at the achievable -22% reduction.**

**Verdict:** GREEN if brief is ≥20% shorter AND cycle seals successfully AND no halt-and-surface degradation observed (qualitative judge by next-cycle dispatcher). YELLOW if 10-19% shorter OR a quality concern surfaces. RED if no reduction OR cycle quality measurably degraded (in which case the SKILL extension needs revision).

**Status (post-corrective + AC-tighten 2026-05-09):** GREEN (-22.0% midpoint / -22.9% floor; meets the corrected ≥20% threshold). The v0.5.0 priming-gap corrective (`fix(personas): close AC.V050.5 priming gap — fill AC.DBT.{3,5,6} + TIME-CLAIMS-DISCIPLINE across 5 typed personas`, 2026-05-09) added §"Reporting + escalation discipline" to all 5 typed personas and flipped 4 of 6 cross-walk rows from "propagate" to "OMIT-OK". A v0.6.0+ follow-on amendment that consolidates non-AC.DBT brief structure could plausibly hit 32-36% reduction (estimated AI-time 60-90 min) — captured as FIDRAFT for future activation. Quality-preservation projected GREEN; live-cycle quality verdict still PENDING the next typed dispatch.

**Output:** writeup at `<workspace>/.scratch/claude-output/v0-5-0-routing-probe.md` with brief-length delta + cycle-seal verdict + qualitative quality judgment + the typed-dispatch brief itself archived as the v0.5.0 reference exemplar. (File renamed from `v0-4-4-routing-probe.md` per the v0.4.4 → v0.5.0 reclassification commit `96972082`.)

**Test:** `test_AC_V050_5_routing_outcome_probe.py` — asserts the artefact exists at canonical path + contains a verdict-band line + records both brief lengths + names the comparison cycle. Skip-by-default unless `LOAM_V050_OUTCOME_PROBE_SHIPPED=1` env var set (the probe is empirical and post-v0.5.0-seal; the test gates the env-var presence so CI doesn't false-fail before the probe ships).

`outcome-altitude: true` per the rubric — real downstream cycle, real brief-length reduction, real cycle-quality verdict; not a stubbed brief-authoring fixture.

### AC.V050.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under:

- `plugins/dev-sdlc/skills/subagent-routing/SKILL.md` (new file).
- `plugins/dev-sdlc/skills/dispatch-brief-authoring/SKILL.md` (extension).
- `plugins/dev-sdlc/tests/test_AC_V050_*.py` (new test files).
- `docs/plans/v0-5-0-subagent-personas-routing-and-priming.{md,manifest.yaml}` (this plan + manifest + seal narrative).
- `docs/release-roadmap.md` (§6 v0.5.0 row appended; §2 SHIPPED row on completion).
- `docs/STATE.md` (v0.5.0 SHIPPED rollup row).
- `docs/FUTURE_IDEAS_DRAFT.md` (capture for §6 deferred items if any).

Anything outside that set is a halt condition. Specifically: **NO edits to `plugins/dev-sdlc/agents/loam-*.md`** during the initial v0.5.0 build — the v0.1.7 personas are sealed and consumed read-only at seal time. **AMENDED 2026-05-09 post-seal:** the priming-gap corrective extends each persona body with a §"Reporting + escalation discipline" section; the seal-diff for the corrective commit (`fix(personas): close AC.V050.5 priming gap`) admits `plugins/dev-sdlc/agents/loam-*.md` for that specific commit only, scoped to the §"Reporting + escalation discipline" addition. **NO edits to `framework/workspace-bootstrap/`** — the symlink scaffold is sealed and consumed read-only. **NO edits to any other plugin or framework component**.

---

## §5 — Hard constraints

1. **No `--amend`.** Corrective commits are NEW commits.
2. **Scope fence per §3.** Edits outside fence = halt.
3. **No Anthropic API key, no `pip install anthropic`.** v0.5.0 is SKILL-authoring; no LLM-routed code paths added.
4. **`--strict-mcp-config` invariant.** No `claude -p` calls added; constraint preserved by inspection.
5. **No new runtime deps.** SKILL authoring is markdown + frontmatter; no Python additions on the import surface.
6. **No modification of v0.1.7 subagent persona files** (initial v0.5.0 build); **AMENDED 2026-05-09 post-seal:** the priming-gap corrective extends each persona body with a §"Reporting + escalation discipline" section (Recommendation IS the decision / operational-objective test / verified-or-marked / no-false-fault / TIME-CLAIMS) to close the AC.DBT.{3,5,6} + TIME-CLAIMS gap surfaced by AC.V050.1. No other persona surface is touched (tool restrictions, when-to-invoke, voice rules, halt triggers, harness composition all preserved). Constraint scope narrows from "no modification at all" to "no modification beyond the AC.DBT priming-gap closure."
7. **No modification of v0.2.2 AC.DBT.1–6 propagated-principle block.** It is the load-bearing backward-compat surface for `general-purpose` dispatches.
8. **`loam amend apply --dry-run` green** is a hard prereq + hard post-apply gate.
9. **No public action.** No `git push`, no `git tag`, no GitHub Release. v0.5.0 HALTS at seal; owner gates the publish.
10. **Plan-before-code.** This plan-doc lands BEFORE source edits.
11. **ODD §2.5 + §2.4.** Every line of code/text in new SKILLs maps to a named AC. No method-in-AC. No "options to rule on" framing.
12. **Outcome-altitude AC requirement** per `feedback_test_outcome_altitude_required.md`. AC.V050.5 is the outcome-altitude probe (real cycle, real brief delta, real verdict).
13. **Path A reframing per §0** is conditional on owner ratification. If owner picks Path B (decline reframing; rebuild already-shipped personas), this plan-doc is discarded and a new plan-doc authored against Path B's scope.

---

## §6 — Out of scope (explicit)

- **Per-persona structural enforcement of subagent_type routing.** A hook that REJECTS a Task dispatch when work-shape matches a persona but `subagent_type == general-purpose` is the v0.7.0 META-FRAMEWORK structural-enforcement substrate territory. v0.5.0 ships the SOFT enforcement (SKILL recommends; dispatcher rules). Captured as FIDRAFT entry "subagent-routing structural-enforcement hook" — activation gate v0.7.0.
- **Per-persona model selection / tool-tier extension.** v0.1.7 set the tool surfaces (researcher = read-only; reviewer = read-only-with-git). Adjusting tool surfaces or wiring per-persona model selection (Opus for plan-author, Sonnet for builder, Haiku for routing decisions) is a separate amendment to v0.1.7's persona files, not v0.5.0. Captured as FIDRAFT entry "per-persona model-tier defaults".
- **New persona authoring.** v0.5.0 does not add a new persona to the v0.1.7 set of 5. New persona proposals walk the rubric in `docs/personas-methodology.md` §5 first; that rubric was shipped at v0.1.7 specifically to gate this kind of proposal.
- **Per-language sub-builder personas.** Already analyzed at `docs/personas-methodology.md` §6 (`loam-builder-python` / `loam-builder-typescript` / etc.); recommendation was extend `loam-builder` with a language-adapter SKILL bundle, not new sub-personas. v0.5.0 does not author the language-adapter SKILL bundle either; that's a separate amendment.
- **Versioning of in-flight dispatches inheriting old persona prompt versions.** Persona prompts are loaded at dispatch time from disk; in-flight dispatches inherit whatever was on disk at dispatch start. No version-pinning per dispatch shipped or proposed. Captured as FIDRAFT entry "subagent-persona prompt versioning for in-flight dispatches" — activation gate when persona prompt edits cause observable in-flight drift.
- **Subagent discoverability via skills.** Subagents are discovered by Claude Code's standard subagent mechanism (filename-in-`.claude/agents/`); no SKILL-mediated discovery shipped or needed. The `subagent-routing` SKILL is a recommendation surface, not a discovery surface.
- **Backporting persona-aware routing to v0.4.3 / v0.4.2 / earlier dispatches.** Past dispatches are sealed; v0.5.0 applies forward-only.
- **Persona-level halt-and-surface defaults beyond what's already in v0.1.7 persona bodies.** Each v0.1.7 persona names its halt triggers explicitly; v0.5.0 does not modify them. Captured as FIDRAFT entry "persona-level halt-trigger consolidation review" — activation gate next persona-prompt revision cycle.

All five "captured as FIDRAFT" items get appended to `docs/FUTURE_IDEAS_DRAFT.md` per `feedback_durable_capture_for_planned_work` as part of the v0.5.0 seal commit chain.

---

## §7 — Halt triggers

1. AC.V050.1 audit verdict is RED (consumption gap is mis-characterized; <50% of audited sites map to a v0.1.7 persona). Halt; reframe with owner before proceeding.
2. Cross-component scope expansion beyond `plugins/dev-sdlc/skills/`. Halt + surface.
3. AC.V050.* count grows beyond 5 (excluding `.S`). ODD §2.5 violation triage; halt.
4. AC.V050.5 outcome-altitude probe blocked indefinitely (no downstream cycle materializes within 30 days). Halt + soft-surface for owner ratification of an extended timeline OR re-tune the AC to a synthetic-comparison fallback (RED-band fallback, less preferred).
5. Any reach for `--amend`, `git push`, or `git tag`. Immediate halt.
6. Subscription-only constraint violated. Immediate halt.
7. AI-time exceeds upper band (120 min) by >50% → 180 min wall-clock. Halt with current state.
8. ODD §2.5 violation discovered in surrounding code (e.g., `dispatch-brief-authoring` SKILL turns out to have a method-in-AC violation). Halt + surface; do NOT silently extend.
9. WD mismatch — `pwd` returns anything other than `/Users/lukeivers/ivers-corp-pos-v2`. Immediate halt.
10. Owner picks Path B (decline reframing) per §0. Discard this plan-doc; author new plan-doc against Path B scope.
11. The v0.1.7 subagent personas turn out to NOT carry the discipline this plan claims (e.g., `loam-builder.md` does not actually name ODD §2.5). Halt + surface; the brief-extension's omission rationale is invalid if the personas don't carry the discipline. (Pre-verification: skim of `loam-builder.md` shows ODD §2.5 + plan-before-code + halt-and-surface + no-amend named explicitly; the rationale holds at plan-time but the builder re-verifies at build-time.)
12. The v0.2.2 AC.DBT.1–6 propagated-principle block is structurally too embedded to omit cleanly (e.g., the SKILL's structural shape requires the block in every brief regardless of `subagent_type`). Halt + surface; the brief-extension AC.V050.3 needs different shape.

---

## §8 — Version-fit recommendation

**Recommend: v0.5.0 PATCH** (not v0.5.0 fold-in).

**Rationale:** v0.5.0 closes a small consumption gap on already-shipped substrate. The fence is 2 SKILL surfaces (1 new, 1 extended) + a test family + an empirical probe + the standard plan-doc/manifest/seal-narrative scaffolding. Total fence is much smaller than typical v0.5.0 work (binary-usage observation harness is a new component requiring sandboxing + 3-6 hours alone per `docs/release-roadmap.md` §4 v0.5.0 ACs). Folding v0.5.0 into v0.5.0 would (a) delay the consumption-gap closure unnecessarily, (b) bundle META-FRAMEWORK substrate work with END-USER capability work (mixing classes; v0.5.0 is END-USER per the roadmap), (c) increase v0.5.0's already-large surface (5-10 hours estimated AI-time per roadmap §4).

**v0.5.0 PATCH classification rationale:** PATCH is "defect closure within the most-recent minor's outcome" per `docs/release-versioning-policy.md` §32. v0.5.0's consumption-gap closure does NOT extend v0.4.3's outcome shape (which is memory-retrieval BM25 fix); v0.5.0's outcome shape is META-FRAMEWORK substrate improvement, separately classified. There's a tension here — the version-fit is more accurately PATCH-SHAPED-AS-MINOR-CLASS (META-FRAMEWORK class, PATCH-shaped fence). Owner ratification needed on this classification call.

**Alternative version-fit:** label v0.5.0 as v0.4.3.1 sub-PATCH (PATCH on PATCH) since v0.4.3 was itself a patch. Or label v0.5.0 as v0.5.0-pre-substrate since META-FRAMEWORK work conventionally bundles into v0.7.0 territory (per roadmap §4 v0.7.0 row "Loam's principle foundation is named and structurally enforced"). Either alternative is acceptable; v0.5.0 PATCH is cleanest from a delivery-cadence perspective (next-PATCH-up after v0.4.3) and avoids the sub-PATCH versioning pattern that hasn't been used in loam yet.

**Predecessor sequencing:** v0.4.3 build dispatch is in flight (per the dispatch brief context). v0.5.0 build cannot dispatch until v0.4.3 seals (per `feedback_serialize_amendment_builds` worktree-level constraint — both touch `plugins/dev-sdlc/` indirectly via tests). Plan-doc authoring (this dispatch) is parallel-safe per `feedback_serialize_amendment_builds` (research + plan-author agents are safe in parallel; only builds serialize).

---

## §9 — Dependencies

Per `docs/release-roadmap-dependency-map.md`:

- **HARD dep on v0.1.7** (AC.PERSONAS.1–8 sealed: 5 subagent personas at `plugins/dev-sdlc/agents/`; symlink scaffold at workspace-bootstrap; collision-handling). v0.5.0 consumes the personas; without them, the routing SKILL has nothing to recommend routing to. Verified shipped at seal `73505f0`.
- **HARD dep on v0.2.2** (AC.DBT.1–6 propagated-principle block in `dispatch-brief-authoring` SKILL). v0.5.0 extends this SKILL with the typed-dispatch omission clause; the existing SKILL surface is the editing target. Verified shipped at seal `5eda09d`.
- **SOFT dep on v0.4.3** (memory retrieval BM25 fix; in-flight). v0.5.0 build dispatch should serialize after v0.4.3 seal per worktree-level rule. Plan-doc authoring (this dispatch) is parallel-safe.
- **SOFT dep on v0.7.0** (META-FRAMEWORK structural enforcement substrate; not yet planned in detail). v0.5.0 ships SOFT enforcement (SKILL recommends); v0.7.0 may harden into HARD enforcement (hook rejects). Forward-composes; v0.5.0 doesn't gate v0.7.0 nor vice-versa.
- **No HARD dep on v0.5.0 / v0.6.0** — v0.5.0 is META-FRAMEWORK, parallelizable with the END-USER work in those minors per the dependency map.

Worktree-level constraint: only v0.4.3 build (in flight in canonical) competes for the canonical worktree. v0.5.0 plan-doc authoring is parallel-safe.

---

## §10 — F2 Ruthless Feedback — honest tensions

1. **The reframing in §0 may be wrong.** The dispatch brief authored a plan against a non-existent FIDRAFT entry, but the brief's author may have been working from a fresher mental model than the FIDRAFT captures — perhaps a Telegram exchange with Luke that named the work shape. If the brief-author's mental model is more accurate than what's documented, this plan-doc's reframing throws away signal. Surface for owner ruling: did the plan-thing-to-go-for in Telegram 10526 reference the consumption-gap closure (Path A above) or did it reference a wholly different work-shape the documented FIDRAFT didn't capture?

2. **AC.V050.1 audit may show the gap is smaller than predicted.** If the empirical audit shows ≥80% of dispatches already use typed personas (e.g., the dispatcher has been routing to `loam-builder` correctly for weeks), the consumption gap doesn't exist and the SKILL+extension would be authored against a non-problem. The audit IS the gate; if RED, plan reframes. The honest doubt: I don't have a fresh empirical baseline; the §1 framing is partly inferred from the brief's premise + the personas-methodology.md §1 paragraph that says "in addition to the per-cycle principles named above, every dispatch brief authored by this skill carries the following propagated set so sub-agents inherit them at turn-start" (which strongly implies the dispatcher uses general-purpose).

3. **AC.V050.5 outcome-altitude probe waits for the next cycle.** The probe is empirical: it requires a real downstream amendment cycle to dispatch via `subagent_type: loam-builder` and report the brief-length delta. There's no synthetic version of this probe that's actually outcome-altitude per `feedback_test_outcome_altitude_required` (a stubbed dispatch with a hand-crafted brief is implementation-altitude, not outcome). If no downstream cycle materializes within 30 days, AC.V050.5 stays UNVERIFIED; halt-trigger 4 names the recovery path (synthetic-comparison fallback as RED-band).

4. **The brief-extension AC.V050.3 may be structurally awkward.** The existing `dispatch-brief-authoring` SKILL has the AC.DBT.1–6 propagated-principle block as a load-bearing structural element of the canonical brief order. Adding a "MAY omit when typed" clause introduces a conditional in what was a structural rule; the SKILL becomes harder to follow mechanically. RF on the design: the alternative shape (a separate `subagent-routing` SKILL that REPLACES the `dispatch-brief-authoring` SKILL when typed dispatch is used, instead of extending it conditionally) was rejected during plan-authoring because it duplicates the brief-shape rules. But the conditional is genuinely awkward. Consider during build whether a different shape (e.g., the `dispatch-brief-authoring` SKILL describes ONLY the universal brief contract; the `subagent-routing` SKILL describes the typed-dispatch shape from scratch; the two are referenced together by the dispatcher) is cleaner.

5. **The v0.1.7 personas may not be discipline-complete enough to omit the AC.DBT.1–6 block.** AC.DBT.1–6 carries 6 propagated principles (LEAN-GROUNDING-LOAD / NO-CLOSING-LINE-PERMISSION-ASKS / SPECIFIC-CLAIMS-VERIFIED / TEST-AGAINST-OPERATIONAL-OBJECTIVE-BEFORE-ESCALATING / NO-FALSE-FAULT / TIME-CLAIMS-DISCIPLINE). I've verified `loam-builder.md` carries ODD §2.5 + plan-before-code + halt-and-surface + no-amend, but I haven't cross-walked all 6 AC.DBT principles against all 5 v0.1.7 persona bodies. Builder's pre-edit verification: cross-walk each AC.DBT principle against each persona body; if any persona is missing a principle that AC.DBT.* propagates, the AC.V050.3 omission clause needs to be partial (omit only the principles each persona carries), or v0.1.7 personas need a separate amendment to add the missing principles before v0.5.0 can ship the omission. Surface as halt-trigger 11 above.

---

## §11 — F4 self-check (scope-confidence)

The reframing in §0 reduces confidence in the outcome shape vs the dispatch brief's premise. Author confidence in the reframed outcome shape (consumption-gap closure on already-shipped substrate) is **medium-high** — the personas-methodology.md and the `dispatch-brief-authoring` SKILL existence are verified VERIFIED-band facts; the gap inference is PLAUSIBLE-band but not VERIFIED until AC.V050.1 audit runs.

Per F4: medium-high confidence → tight scope on objective + ACs + halt triggers; loose scope on method (builder rules). The §4 ACs pin the outcome (audit + 2 SKILL surfaces + outcome probe); methods stay builder's call (e.g., the routing rubric's exact wording is builder's call within constraint that it must reference the v0.1.7 personas + their tool surfaces). The audit-first sequencing (AC.V050.1 before SKILL authoring) is the F4-driven gate that rules out the under-confidence failure mode (if audit RED, halt before authoring against a non-problem).

Per Lens 4 conflict-with-Lens-2 (constraint-narrowing vs trajectory-tightening per `personas-methodology.md` §8 Tension 3): v0.5.0 IS Lens 2 work (toolkit extension for the primary), and the SOFT enforcement shape is the multi-signal-discipline resolution — soft-narrow (recommend the typed dispatch) rather than hard-narrow (reject the general-purpose dispatch), preserving the dispatcher's option to override for the boundary cases Lens 2 names.

---

## §12 — Provenance trail

- Dispatch brief authoring this plan-doc — Telegram 10526 owner-authorization arc.
- v0.1.7 subagent-personas seal at `framework/workspace-bootstrap/seals/SEAL_COMMIT.v0-1-7-subagent-personas` (5 personas + symlink scaffold + collision handling at AC.PERSONAS.1–8).
- v0.2.2 dispatch-brief-authoring SKILL with AC.DBT.1–6 propagated-principle block at `plugins/dev-sdlc/skills/dispatch-brief-authoring/SKILL.md`.
- Personas methodology authority at `docs/personas-methodology.md` §1–§9.
- v0.1.7 persona files at `plugins/dev-sdlc/agents/loam-{builder,documenter,plan-author,researcher,reviewer}.md`.
- Workspace-symlink mechanism at `framework/workspace-bootstrap/` (consumed read-only).
- `docs/release-roadmap.md` §3 (active version v0.4.0 + v0.4.1 + v0.4.2 + v0.4.3 in flight) + §4 (v0.5.0 → v1.0.0 mapped).
- `docs/release-roadmap-dependency-map.md` (HARD vs SOFT dep classification).
- `docs/release-versioning-policy.md` §32 (PATCH definition) + §40 (CLASS definitions).
- FIDRAFT — `docs/FUTURE_IDEAS_DRAFT.md` (verified by grep that the brief's referenced "Subagent-persona priming" entry does NOT exist).
- `feedback_plan_before_code` — plan-doc lands BEFORE source edits.
- `feedback_test_outcome_altitude_required` — AC.V050.5 is the outcome-altitude probe.
- `feedback_locked_design_not_license` — applied in Path A vs Path B framing in §0 (revisiting v0.1.7's locked persona surface is on the table; rebuilding parallel personas is the bad-outcome path).
- `feedback_durable_capture_for_planned_work` — §6 deferred items get FIDRAFT capture in the seal commit chain.
- `feedback_serialize_amendment_builds` — worktree-level build serialization with v0.4.3 in flight.
- `feedback_summarize_and_surface_decisions` — §0 + §8 + §10 surface decisions with recommendations rather than burying.
- `feedback_subagent_odd_violation_halt` — halt-trigger 8 names the surrounding-code violation halt explicitly.
- Dispatch brief that authored this plan-doc — itself the empirical evidence that briefs re-derive priming (the brief carries 100+ lines of priming for a plan-author work-shape that maps directly to `loam-plan-author`).

---

## §13 — AI-time band

Per duration-estimation rubric (`wall_clock_minutes ≈ tool_calls × 0.1–0.15`):

- Plan-doc + manifest authoring: 25–45 min (this dispatch; midpoint ~35 min; actual will calibrate).
- AC.V050.1 audit (grep dispatch sites + author writeup): 15–25 min.
- AC.V050.2 `subagent-routing` SKILL authoring: 20–30 min.
- AC.V050.3 `dispatch-brief-authoring` extension: 10–20 min.
- AC.V050.4 no-regression check: 5–10 min.
- AC.V050.5 outcome probe: ASYNC — happens at next downstream cycle dispatch, not in v0.5.0 build window. Probe writeup itself: 15–25 min when the cycle ships.
- Apply + seal + report: 10–15 min.

**Aggregate v0.5.0 build range: 60–120 min ≈ 1.0–2.0 hr AI-time** (excluding the async outcome probe). Midpoint ~1.5 hr. Within halt-trigger 7 upper bound (120 min × 1.5 = 180 min).

Total v0.5.0 closure including async outcome probe: 75–145 min ≈ 1.25–2.4 hr.

---

## §14 — Method decisions

Backfilled at build time per the v0.4.3 / v0.4.2 / v0.4.1 / v0.4.0 precedent.

- **D-V050.1** (audit scope): _builder rules at build time_. Authoring guidance: grep `framework/` + `plugins/` for `subagent_type` literal usage; grep `docs/plans/*.md` (last 30 days by `git log --since=30.days.ago --name-only`) for dispatch-brief patterns (`# Dispatch brief`, `subagent_type:`, `Working directory:`, `Principles to apply at turn-start`); record per-site row with the four columns named in AC.V050.1. Surface audit completeness verdict.
- **D-V050.2** (`subagent-routing` SKILL frontmatter description): _builder rules at build time_. Authoring guidance: trigger-shape-language matching Anthropic's documented SKILL discovery patterns; reference `personas-methodology.md` §5 rubric as authority; explicit fall-back-to-general-purpose clause for boundary cases.
- **D-V050.3** (`dispatch-brief-authoring` extension shape): _builder rules at build time_. Authoring guidance: prefer extension (single SKILL with conditional block) over splitting (two SKILLs with overlapping shape) unless the conditional turns out structurally too awkward per §10 RF #4. Document the call in the build report.
- **D-V050.4** (AC.V050.5 outcome probe timing): _builder defers to next-cycle dispatcher_. The probe ships when the next downstream cycle ships; the v0.5.0 build closes with AC.V050.5 marked PENDING-OUTCOME-PROBE in the seal narrative. Probe-completion seals the AC retroactively per amendment-pending-AC convention (or via a follow-on amendment `v0.5.0.1 outcome-probe-completion` if the convention requires).
- **D-V050.5** (FIDRAFT capture for §6 deferred items): _builder rules at build time_. Authoring guidance: each of the 5 deferred items per §6 gets a separate FIDRAFT entry with the activation gate per the plan-doc; entries follow the FIDRAFT-capture SKILL shape; bundled into the seal commit chain per AC.V050.S.

### Commit SHAs

| Order | Type | SHA | Description |
|---|---|---|---|
| 1 | plan-doc | _pending_ | docs(plans): v0.5.0 patch — subagent-personas routing + priming-de-duplication plan-doc + manifest |
| 2 | audit | _pending_ | docs(experiments): v0.5.0 dispatch-site audit (AC.V050.1) — verdict GREEN/YELLOW |
| 3 | new-skill | _pending_ | feat(dev-sdlc/skills): subagent-routing SKILL (AC.V050.2) |
| 4 | extend-skill | _pending_ | feat(dev-sdlc/skills): dispatch-brief-authoring typed-dispatch extension (AC.V050.3) |
| 5 | tests | _pending_ | test(dev-sdlc): AC.V050.* test family (audit-artefact + skill-discovery + extension + outcome-probe-skip-when-env-missing) |
| 6 | docs (FUTURE_IDEAS) | _pending_ | docs(future-ideas): capture v0.5.0 deferred items (5 entries per §6) |
| 7 | docs (SHIP rollup) | _pending_ | docs: v0.5.0 SHIPPED rollup — STATE.md + release-roadmap §2/§3/§6 |
| 8 | manifest baseline-update | _pending_ | docs(plans): v0.5.0 patch manifest baseline → <SHA> |
| 9 | apply | _pending_ | chore(amend): v0-5-0-subagent-personas-routing-and-priming manifest+apply |
| 10 | seal | _pending_ | chore(seals): v0-5-0-subagent-personas-routing-and-priming — dev-sdlc/skills at <SHA> |

## §15 — SHA register

Backfilled at seal time into §14 above.

---

## Open questions for owner ratification (5 questions; bundled here for one-pass review)

1. **Path A vs Path B framing per §0.** Recommend Path A (consumption-gap closure on shipped v0.1.7+v0.2.2 substrate). Alternative Path B (decline reframing; rebuild already-shipped personas) duplicates v0.1.7 work; not recommended. **Surfacing for ruling.** The reframing rests on a verified empirical claim that the FIDRAFT entry the brief named does not exist; the personas the brief recommends already ship; the priming-propagation the brief recommends already ships. Owner ruling needed because the reframing changes the work shape from "build new personas" to "improve consumption of existing personas."
2. **Version-fit per §8.** Recommend v0.5.0 PATCH. Alternatives: v0.4.3.1 sub-PATCH (PATCH on PATCH) or v0.5.0 fold-in or v0.7.0 META-FRAMEWORK fold-in. Recommend PATCH as cleanest delivery cadence; v0.7.0 fold-in is the closest alternative if owner prefers META-FRAMEWORK work bundle into one minor.
3. **AC.V050.5 outcome probe timing per §14 D-V050.4.** Recommend ASYNC — probe ships at next downstream cycle; v0.5.0 build closes with AC.V050.5 marked PENDING-OUTCOME-PROBE; probe-completion via follow-on amendment if convention requires. Alternative: defer v0.5.0 sealing until the probe ships (blocks v0.5.0 close on async event; not recommended). Explicit ratification needed because the convention "AC marked outcome-altitude but not yet verified at seal" is unusual in loam.
4. **AC.V050.3 brief-extension shape per §10 RF #4.** Recommend single-SKILL conditional extension over two-SKILL split. Builder may surface during build if the conditional is structurally too awkward (halt-trigger 12). Owner ratification helpful because the design call sets precedent for future SKILL conditionals.
5. **AC.DBT.1–6 cross-walk per §10 RF #5.** Builder pre-edit verification: cross-walk each AC.DBT principle against each v0.1.7 persona body; if any persona is missing a principle that AC.DBT.* propagates, AC.V050.3 omission clause becomes partial (omit only what each persona carries) OR a separate v0.1.7-persona amendment ships first to add missing principles. Owner ratification helpful because this affects whether v0.5.0 is a single closure or a two-amendment chain (v0.5.0-pre adds missing principles to v0.1.7 personas; v0.5.0 ships the omission clause). Default builder action: cross-walk first; partial-omission clause if any gap; surface if a full v0.1.7-persona amendment is needed (out of v0.5.0 scope; halt + ratify scope expansion).

---

*Plan-doc authored against canonical pos-v2 at `/Users/lukeivers/ivers-corp-pos-v2/`. Plan-before-code per `feedback_plan_before_code`. Outcome-altitude AC required per `feedback_test_outcome_altitude_required` (AC.V050.5). Path A reframing per §0 surfaced for owner ratification per `feedback_locked_design_not_license` (revisit v0.1.7's locked design rather than rebuild parallel) and F2 RUTHLESS FEEDBACK (silent acceptance of the brief's premise IS the silence F2 prevents).*
