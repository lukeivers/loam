# v0.2.0 master plan — Continuous codebase-watch + persona-driven skill capture

**Status:** master plan-doc, plan-before-code. Authored 2026-05-04 (Sonnet, plan-author REDISPATCH).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.
**Parent plan:** `docs/rebuild/plans/eric-final-delivery-plan-2026-05-04.md` (§2 v0.2.0 row — AUTHORITATIVE).
**Companion research:**

- `docs/rebuild/plans/layered-skill-story-research-2026-05-04.md` (§3 — auto-creation; §3.6 universal-tier).
- `docs/rebuild/plans/v0-1-9-master-plan.md` (precedent for cycle-decomposition + dispatch-brief shape; sealed `b01d3eb`).
- `docs/rebuild/plans/v0-1-8-master-plan.md` (extractor full mode at v0.1.8 Cycles 3+4 — incremental mode here is the increment).
- `plugins/dev-sdlc/docs/smoke-test-discipline.md` (six-dimension smoke; SOFT gate at v0.2.0).

**Predecessor commits:**

- v0.1.9 sealed (local) at `9022df1` — Cycle 1 `790807d` PR-safety gate engine; Cycle 2 `0dc557e` hooks + 3 CI templates + PR description; Cycle 3 `3284087` 6 dev-sdlc SKILLs + audit-allowlist cleanup. Release-level SOFT smoke green; tag deferred.
- v0.1.8 sealed at `9b64cd4` — banded contract + extractor full mode (Cycle 3 `6711dd7`; Cycle 4a `67dd302`; Cycle 4b `c648cf9`).
- v0.1.7 PM batch API + layered-skill discovery: Cycle 3 `bcf699a`; Cycle 4 `122a7c8`.
- v0.1.6 production-safety + cost-governance: `3f1d237` / `88674cb`.
- M-FBM operational health: `1a1f830`.

**Quality bar (Luke directive 2026-05-04):**

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

v0.2.0 is the **contract-stays-alive + Eric-patterns-captured release**. v0.1.8 produced the contract; v0.1.9 enforced it at PR-time; v0.2.0 keeps the contract synchronised as Eric's app evolves AND captures Eric-specific patterns into workspace-local skills. MVP scope intentional (3 triggers, not 6, per parent §2) — every named feature ships complete. All 6 smoke dimensions exercised at release-level (SOFT gate; quality-bar-non-negotiable applies). No partial features.

---

## Principles applied this turn

- **CHANNEL** — replies route to dispatcher (not Telegram).
- **AUTONOMY** — settle planning decisions; only escalate critical/public/financial.
- **F2 RUTHLESS FEEDBACK** — §7 honest doubts surface real tensions.
- **LOCKED-DESIGN-NOT-LICENSE** — Eric synthesis §2 v0.2.0 + parent dispatch pre-resolved partition placements are authoritative; held at §3.
- **PROMISES > IN-MOMENT JUDGMENT** — quality bar non-negotiable.
- **ODD §2.5** — every named AC family is named here at master-plan level; per-cycle plan-docs tighten + bind to tests.
- **WD-IN-DISPATCHES** — confirmed at start; propagated to every cycle dispatch brief.
- **PARTITION RULE** — pre-resolved by parent dispatch:
  - Watch (incremental): `plugins/dev-sdlc/odd-extractor/` (composes with banded-AC schema; dev-deliverable shape).
  - Auto-creation MVP: `plugins/loam-skills/skills/skill-capture-proposal/` (universal-tier per Luke's 2026-05-04 clarification).
  - Workspace-config flag: `framework/workspace-bootstrap/`.
  - Design note: `docs/design/persona-driven-skill-capture.md`.
- **PLAN-BEFORE-CODE** — this dispatch IS the plan-before-code. Cycle plan-docs separate.
- **SCOPE-ONLY** — method specifications are cycle plan-doc responsibility.
- **NEW-SCHEMA OPPORTUNITY** — manifest YAMLs schema v3. Seal commits short-form.
- **SWARMING (Lens 5)** — two cycles each strictly tighter than v0.2.0 parent; further decomposition is coordination overhead. Stops at two.
- **PRINCIPLE-APPLICATION DISCIPLINE** — propagated to every cycle's dispatch brief.

---

## §1 — Executive summary

v0.2.0 is the **contract-stays-alive + Eric-patterns-captured release**. v0.1.8 produced the banded contract; v0.1.9 enforced it at PR-time; v0.2.0 keeps it synchronised as Eric's Rails-app evolves AND captures Eric-specific recurring patterns into workspace-local skills the persona auto-loads.

**Theme.** Contract evolves automatically; Eric's patterns become invokable skills. The persona detects recurring patterns (3 trigger signals MVP) and proposes them as workspace-local SKILLs the user ratifies via PM. The auto-creation mechanism is universal (dev or non-dev) per Luke's 2026-05-04 clarification; promotion rubric is dev-only and lands at v0.2.1.

**MVP trigger scope (6 → 3 per parent §2 Decision N).** Chosen for highest-precision: explicit-request (near-zero false-positive), repeated-invocation (same multi-step procedure 3+ times — the canonical "auto-creation" use case), ask-and-answer pattern stabilization. Deferred 3 (CLAUDE.md drift, memory-recall hit, hook-trigger) need additional component-side instrumentation OR are dev-mode-only. Quality-bar move: ship 3 complete rather than 6 half-implemented.

**Cycle count: two cycles**, serialized per `feedback_serialize_amendment_builds`:

1. **Cycle 1 — Continuous codebase-watch (incremental extractor) + scheduling + PM ratification-queue + domain-batched AC surfacing.** Primary fence `plugins/dev-sdlc/odd-extractor/`. Compose-points with `framework/scope-of-work/` (scheduling) and `framework/per-project-pm/` (ratification + domain-batching). Reads v0.1.8 baseline contract; detects diffs; classifies which ACs need re-extraction; surfaces proposals through PM batches grouped by domain.

2. **Cycle 2 — Persona-driven skill capture (auto-creation MVP) + workspace-config flag + design note.** Primary fence `plugins/loam-skills/`. Compose-points with `framework/workspace-bootstrap/` (config flag), `framework/per-project-pm/` (ratification surface; mostly read-only), `docs/design/`. The `skill-capture-proposal` SKILL codifies proposal-draft-ratify workflow. `enable_auto_skill_capture` flag defaults false.

No Cycle 3 — the two cycles compose only through PM batch API; release-level smoke (§5) covers integration.

**AI-time band.** **14–24 h** per parent §2, midpoint ~19 h. Cycle 1 is highest-risk (incremental mode + likely two-or-three-component fence): **8–14 h**. Cycle 2: **6–10 h**. Wall-clock ≈ tool_calls × 0.1–0.15. 20% quality-bar absorption baked in.

**Dependencies.** v0.1.8 (full-mode contract baseline); v0.1.9 (gate consumes incremental updates); v0.1.7 Cycles 3+4 (layered-skill discovery + PM batch API); v0.1.6 (production-safety profile); M-FBM (operational health for episode-store reads).

**What closes the release.** Watch runs against both v0.1.8 fixtures with synthetic code-change → proposals surface in PM. PM ratification-queue (ratify / revise / reject) functional. Domain-batched AC surfacing groups ACs per batch. Auto-creation MVP end-to-end: trigger → draft → ratify → SKILL.md materialises → persona auto-loads next turn. `enable_auto_skill_capture` default false. Design note published. All 6 smoke dimensions exercised. If any cycle ships partial, halt + surface.

---

## §2 — Scope source-of-truth

Pulled verbatim from parent §2 v0.2.0 + layered-skills §3.

### From Eric synthesis §2 v0.2.0

| Item | Source | Placement |
|---|---|---|
| Continuous codebase-watch (extractor incremental mode) | Eric G10 | `plugins/dev-sdlc/odd-extractor/` |
| Scheduling integration | Eric G10 | `framework/scope-of-work/` integration |
| PM ratification-queue mechanics | Eric G10 | `framework/per-project-pm/` |
| Domain-batched AC surfacing | Eric G10 | `framework/per-project-pm/` |
| `skill-capture-proposal` SKILL (auto-creation MVP) | layered-skills v0.2.0 | `plugins/loam-skills/skills/skill-capture-proposal/` |
| `enable_auto_skill_capture` workspace-config flag | layered-skills v0.2.0 | `framework/workspace-bootstrap/` |
| Trigger detection (3 signals MVP) | layered-skills v0.2.0 | `plugins/loam-skills/skills/skill-capture-proposal/` |
| Persona-driven-skill-capture design-note | layered-skills v0.2.0 | `docs/design/persona-driven-skill-capture.md` |

### MVP trigger scope (Decision N)

| Trigger | In MVP? | Rationale |
|---|---|---|
| Explicit user request ("remember this") | ✓ | Highest-precision; near-zero false-positive. |
| Repeated invocation (3+ times same procedure) | ✓ | Canonical "auto-creation" use case from Luke's framing. |
| Ask-and-answer pattern stabilization | ✓ | High-precision Q&A; especially valuable for non-dev users. |
| CLAUDE.md drift | ✗ defer | Lower-precision; v0.2.x. |
| Memory-recall hit pattern | ✗ defer | Requires M-FBM-side extension; v0.2.x. |
| Hook-trigger pattern | ✗ defer | Dev-mode only; v0.2.x. |

### Auto-creation as persona-proposed user-ratified skill capture

Per layered-skills §3.1 reframe (load-bearing): "auto-creation" = persona-proposed, user-ratified skill capture. Persona detects pattern, drafts SKILL.md, surfaces one-line decision-question; user's `Y` triggers the file write. Silent skill-creation is a known anti-pattern — user-ratification gate is the structural defence. Workflow per layered-skills §3.3:

1. Detect + draft → `<workspace>/.scratch/claude-output/skill-draft-<name>.md`.
2. Surface decision-question via PM ("I noticed [pattern] N times in M days. Capture as workspace-local skill? Y / N / R(evise).").
3. Ratify: Y → move draft to `<workspace>/.claude/skills/<name>/SKILL.md`. R → iterate. N → cool-down 14 days.
4. Persona auto-loads next relevant turn via Anthropic native discovery.
5. Quarterly review per promotion rubric (v0.2.1 surface).

Workflow gated on `enable_auto_skill_capture: true` (default false). Universal across workflows.

### Eric SaaS-app sequence connection

What v0.2.0 enables for Eric: contract stays in sync with code (watch detects new payment-handling logic + Rails callbacks + accounting rules); Rails-specific patterns ("this concern pairs with a service object") become workspace-local SKILLs; domain-specific ratification batches (payment-handling / accounting / Rails-callback-discipline) surface at sane cadence.

---

## §3 — Cycle decomposition

Two cycles, each: theme, scope-tightening, fence, AC family seed, smoke dimensions, dependencies, out-of-scope, AI-time, Eric-relevance, quality-bar audit.

### Cycle 1 — Continuous codebase-watch + scheduling + PM ratification-queue + domain-batched AC surfacing

**Theme.** Extractor incremental mode. v0.1.8 Cycles 3+4 produced the full-mode contract (one-shot); Cycle 1 here produces the incremental mode (re-extract only what changed; surface proposals through PM). Watch invoked-on-demand (CLI + scheduled trigger), not a long-running daemon.

**Scope-tightening.** v0.2.0 parent's AC is "watch runs + PM queue + auto-creation." Cycle 1's AC is the first two; auto-creation defers to Cycle 2. Strictly tighter.

**Fence.** PRIMARY `plugins/dev-sdlc/odd-extractor/`. Compose-points (likely two-or-three-component fence; halt-and-surface if non-trivial):
- `framework/scope-of-work/` integration (cron scheduling primitive).
- `framework/per-project-pm/` (PM batch-type extension for `contract-update-proposal` + domain-batching — likely a thin extension).

**AC family: AC.WATCH.\***

- **AC.WATCH.1 — Incremental-mode CLI.** `loam extract --incremental <repo>` reads prior contract; classifies each AC's evidence as still-current / out-of-date / orphaned.
- **AC.WATCH.2 — Diff-against-prior-contract logic.** Heuristic: line-range overlap + symbol presence + file existence. Load-bearing risk — under-identification misses contract drift; over-identification re-extracts unchanged ACs.
- **AC.WATCH.3 — Re-extraction proposal generation.** For each out-of-date AC, generate `(ac_id, current_evidence, proposed_new_evidence, confidence_band)` via re-invoking v0.1.8 full-mode extractor scoped to affected files. Includes delta view.
- **AC.WATCH.4 — PM ratification-queue mechanics.** Proposals land as new batch-type in `framework/per-project-pm/`. PM presents delta view; owner ratifies / revises / rejects. Composes with v0.1.7 Cycle 4 PM batch API + Decision Q one-question-at-a-time.
- **AC.WATCH.5 — Domain-batched AC surfacing.** Group out-of-date ACs by domain (tag-based primary, file-path-prefix fallback). PM presents one decision per domain-batch ("12 ACs in payment-handling need re-extraction; review batch?") not per-AC.
- **AC.WATCH.6 — Scheduling integration.** Composes with `framework/scope-of-work/`; MVP supports cron-style schedule. On-merge / on-PR-open triggers deferred to v0.2.x.
- **AC.WATCH.7 — Production-stake honoring.** Under `safety_profile: production-stake`, watch defaults to dry-run (proposals emitted but no auto-update); ratification always required.
- **AC.WATCH.8 — Audit-trail floor.** Every watch run + proposal + ratification/rejection emits audit-log entry per Decision P SOC-2 floor.
- **AC.WATCH.9 — Component-level test surface.** Incremental engine, diff-classifier, proposal-generation, PM ratification, domain-batching, scheduling, production-stake gate-flip, audit-trail.
- **AC.WATCH.10 — End-to-end smoke against canonical fixtures.** Synthetic code-change on jsts-playwright-app + ruby-rails-payment fixtures; watch surfaces proposals through PM; ratification flow tested end-to-end.

**Smoke dimensions.** D1 ✓ (fresh workspace runs `loam extract --incremental`), D2 ✓ (re-run on unchanged → zero proposals; stable proposal set on synthetic change), D5 ✓ (proposals + audit-log survive `/clear`), D6 ✓ (per AC.WATCH.8). D3 / D4 inherited (one-shot invocation; filesystem state).

**Dependencies.** None within v0.2.0. Within parent: v0.1.8 Cycle 3+4 full-mode extractor (load-bearing — incremental reads full-mode baseline); v0.1.9 Cycle 1 PR-safety gate (consumes incremental updates); v0.1.7 Cycle 4 PM batch API; v0.1.6 production-safety; M-FBM operational health.

**Out-of-scope.** Auto-skill-creation → Cycle 2. On-merge / on-PR-open hook triggers → v0.2.x. Automatic VERIFIED→PLAUSIBLE demotion → v0.2.x (Decision I default-no still applies). Multi-fixture watch concurrency → v0.2.x.

**AI-time band.** **8–14 h** (incremental engine + diff-classifier + proposal generation + PM extension + domain-batching + scheduling + production-stake gate + audit log + tests + smoke). Wall-clock ~40–80 min. Two-or-three-component fence is variability driver.

**Eric-relevance.** Cycle 1 IS the contract-stays-alive mechanism. Without it, v0.1.9's gate runs against an increasingly stale contract. Domain-batching is Eric-specific — Eric's team won't ratify 60 individual AC updates; they'll ratify 5–10 domain batches.

**Quality-bar audit.** Diff-classifier accuracy ≥90% on synthetic test set (line-overlap + symbol-overlap + file-existence). Both small-diff and refactor-shaped synthetic diffs exercised. PM ratification end-to-end. Domain-batching uses tag-based + file-path-prefix fallback. Production-stake gate-flip tested. **No partial features.** ✓

---

### Cycle 2 — Persona-driven skill capture (auto-creation MVP) + workspace-config flag + design note

**Theme.** Persona detects recurring patterns (3 triggers MVP) and proposes them as workspace-local SKILLs the user ratifies via PM. Universal-tier (any loam user, dev or non-dev). Defers silent-skill-write — every SKILL gets user-ratified before file-system materialization.

**Scope-tightening.** Cycle 1's AC is "incremental contract maintenance + PM queue." Cycle 2's AC is "3 triggers + draft + ratify + materialise + auto-load." Strictly tighter — auto-creation is a separate surface from contract maintenance.

**Fence.** PRIMARY `plugins/loam-skills/`. Compose-points:
- `framework/workspace-bootstrap/` (config flag — likely thin extension).
- `framework/per-project-pm/` (ratification via existing v0.1.7 Cycle 4 PM API; no PM-side edits expected; halt-and-surface if a new batch-type is needed).
- `docs/design/persona-driven-skill-capture.md` (admitted via `universal_paths`).

**AC family: AC.SKILLCAP.\***

- **AC.SKILLCAP.1 — `skill-capture-proposal` SKILL package.** Directory at `plugins/loam-skills/skills/skill-capture-proposal/` with valid `SKILL.md`. Frontmatter `description` ≤1536 chars; body covers 6-section pattern (What / When / How / Graceful degradation / Composition / Out of scope) + 3 MVP triggers + proposal-draft-ratify workflow.
- **AC.SKILLCAP.2 — Trigger 1: explicit-request detection.** Match phrase-list ("remember this", "make this a thing", "let's codify this", etc.; method-level list deferred to Cycle 2 plan-author). On match → proposal-draft mode immediately.
- **AC.SKILLCAP.3 — Trigger 2: repeated-invocation detection.** Same multi-step procedure 3+ times in N days (N=7 default). Tool-call sequence shape match. Reads M-FBM episode store (read-only). On M-FBM access failure → silent no-op + audit-log entry.
- **AC.SKILLCAP.4 — Trigger 3: ask-and-answer pattern detection.** Same shape of question 3+ times AND answer text stabilizes. Reads M-FBM episode store. Especially for non-dev users.
- **AC.SKILLCAP.5 — Proposal draft generation.** Persona writes draft to `<workspace>/.scratch/claude-output/skill-draft-<slug>.md` using 6-section template. Header notes which trigger fired + evidence (3 instances + timestamps).
- **AC.SKILLCAP.6 — User-ratification via PM.** One-line decision-question via PM batch API: "I noticed [pattern] N times. Capture as workspace-local skill? Y / N / R(evise)." `Y` → file move to `<workspace>/.claude/skills/<slug>/SKILL.md`. `R` → iterate. `N` → audit-log + cool-down.
- **AC.SKILLCAP.7 — `enable_auto_skill_capture` config flag.** Schema in `framework/workspace-bootstrap/`. Default `false`. Read at workspace-init + every persona turn-start. When `false`, all triggers no-op.
- **AC.SKILLCAP.8 — Cool-down semantics.** On rejection, same trigger-pattern suppressed 14 days (per layered-skills §3.5 #1). State at `<workspace>/.loam/skill-capture/cooldowns.yaml`.
- **AC.SKILLCAP.9 — Per-week budget.** ≤3 proposals/week per workspace (per §3.5 #3). Configurable. State at `<workspace>/.loam/skill-capture/budget.yaml`. Exceeded → no-op until rolling 7-day window resets.
- **AC.SKILLCAP.10 — Hard-cap at 20 workspace-local SKILLs.** Per §3.5 #1. Cap reached → no-op + persona surfaces note about promotion via skill-promotion-review at v0.2.1.
- **AC.SKILLCAP.11 — Design note.** `docs/design/persona-driven-skill-capture.md` published. Sections: Architecture (universal-tier); Triggers (3 MVP + 3 deferred); Proposal-draft-ratify workflow; Cool-down + budget + hard-cap; Failure modes; Composition (PM, M-FBM, workspace-bootstrap); Forward path (v0.2.1 promotion rubric; v0.2.x trigger expansion).
- **AC.SKILLCAP.12 — Component-level test surface.** SKILL.md presence + frontmatter + body validation; each trigger tested in isolation against synthetic episode-store fixtures; proposal-draft generation; PM ratification (synthetic batch); cool-down; budget; hard-cap; config-flag default-false + on/off transitions.
- **AC.SKILLCAP.13 — End-to-end smoke against pos3-or-equivalent fixture.** Enable flag → fire synthetic ask-and-answer pattern (most-deterministic for smoke) → draft surfaces → user ratifies (`Y`) → SKILL.md materialises → persona auto-loads in next relevant turn (verified via Anthropic discovery primitive).

**Smoke dimensions.** D1 ✓ (fresh workspace + flag → trigger → draft → ratify → SKILL → auto-load), D2 ✓ (no re-propose after ratification; cool-down stable; budget rolls), D5 ✓ (ratified SKILL survives `/clear` via Anthropic discovery primitive — inherited from v0.1.7 Cycle 3 `bcf699a`), D6 ✓ (audit per trigger-fire + ratification/rejection). D3 / D4 inherited.

**Dependencies.** Cycle 1 (per `feedback_serialize_amendment_builds`). Within parent: v0.1.7 Cycle 3 layered-skill discovery (load-bearing); v0.1.7 Cycle 4 PM batch API (load-bearing); M-FBM (load-bearing for triggers 2+3); v0.1.6 audit-trail floor.

**Out-of-scope.** Promotion rubric → v0.2.1. 3 deferred triggers → v0.2.x. Mode 2 structured-fill-in-blanks UI → v0.2.x (MVP uses Mode 1 per §3.4). Demotion path → v0.2.1. Cross-workspace skill sharing → not on roadmap.

**AI-time band.** **6–10 h** (~3–5 h SKILL package + ~1–2 h config flag + ~2–3 h design note + tests + smoke). Wall-clock ~30–60 min. SKILL authoring well-rehearsed (20 SKILLs sealed at v0.1.9 close); trigger-detection logic (especially M-FBM-reading triggers 2+3) is highest-uncertainty.

**Eric-relevance.** Eric-patterns-captured mechanism. Rails-specific recurring patterns become workspace-local SKILLs persona auto-loads. Universal-tier covers Eric's non-dev teammates.

**Quality-bar audit.** 3 triggers MVP intentional (per parent §2 + Decision N). Each trigger ships complete (not "explicit-request works, ask-and-answer is a stub"). User-ratification gate is structural defence against silent skill-write. Cool-down + budget + hard-cap defend against fatigue + bloat. End-to-end smoke exercises full path. Design note ensures v0.2.1 + v0.2.x have clean reference. **No partial features.** ✓

---

### Decomposition stopping-criterion check

Per Lens 5: decompose until each subtask's AC is strictly tighter than parent; stop when the proposed split introduces only coordination overhead.

- Two cycles each strictly tighter than v0.2.0 parent.
- Considered + rejected: splitting Cycle 1's incremental engine from PM extension (producer + consumer share fence; redundant scaffolding); splitting Cycle 1's domain-batching from rest (part of PM ratification surface); splitting Cycle 2's 3 triggers into 3 sub-cycles (share proposal-draft + ratification + cool-down surface); splitting Cycle 2's design note into separate cycle (note is architectural reference for SKILL — co-shipping ensures alignment); adding a Cycle 3 integration-glue (no deep coupling between 1+2; release-level smoke covers integration).
- Cycle count: 2 ∈ [2, 3] (parent halt-trigger range).

---

## §4 — Per-cycle dispatch briefs

Two dispatch briefs ready at v0.2.0 build time. Source-of-truth fields (fence, ACs, smoke dimensions, AI-time, out-of-scope) live at §3 — briefs reference §3 + add operational fields (sub-plan path, bookkeeping, halt-triggers, model rationale).

### Cycle 1 dispatch brief

```
# v0.2.0 Cycle 1 build dispatch — Continuous codebase-watch + scheduling + PM ratification-queue + domain-batched AC surfacing

Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`. NOT pos3.

Plan-author dispatch (plan-before-code). Output: `docs/rebuild/plans/v0-2-0-cycle-1-continuous-codebase-watch.md` (sub-plan-doc) + `.manifest.yaml`.

Principles to apply at turn-start: CHANNEL / AUTONOMY / F2 RUTHLESS FEEDBACK / LOCKED-DESIGN-NOT-LICENSE / PROMISES > IN-MOMENT JUDGMENT / ODD §2.5 / WD-IN-DISPATCHES / PARTITION RULE / SCOPE-ONLY / v3 manifest schema / short-form seal commits / plan-doc §14 with `## 14.` heading / PRINCIPLE-APPLICATION DISCIPLINE.

Quality bar (Luke directive 2026-05-04): every named AC complete + tested. Diff-classifier ≥90% on synthetic test set. PM ratification end-to-end. Domain-batching tag-based + file-path-prefix fallback. Production-stake gate-flip tested. No partial features.

Source pointers: master plan §3 Cycle 1; Eric synthesis §2 v0.2.0 (lines 244–276); v0.1.8 contract baseline (Cycle 3 `6711dd7`, Cycle 4a `67dd302`, Cycle 4b `c648cf9`); v0.1.9 gate `790807d`; v0.1.7 PM batch API `122a7c8`; smoke discipline `plugins/dev-sdlc/docs/smoke-test-discipline.md`.

Fence + ACs + smoke + AI-time + out-of-scope: per master plan §3 Cycle 1.

Halt triggers: WD drifts; plan-doc not authored before code; diff-classifier <90% on synthetic test set (escalate to tree-sitter AST-aware); PM extension substantial; scope-of-work extension substantial; production-stake gate-flip ambiguous; cycle >6 h wall-clock; ODD violations in surrounding code; >3 escalations needed.

Bookkeeping: pos-amend apply (NOT `git commit --amend`); manifest schema v3; single semantic commit (manifest+apply merged); short-form seal commit; §14 method-decision-register backfill in separate post-seal commit; backfill master plan §9 row for Cycle 1.

Model rationale: (none — Sonnet default).
```

### Cycle 2 dispatch brief

```
# v0.2.0 Cycle 2 build dispatch — Persona-driven skill capture (auto-creation MVP) + workspace-config flag + design note

Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`. NOT pos3.

Plan-author dispatch (plan-before-code). Output: `docs/rebuild/plans/v0-2-0-cycle-2-persona-driven-skill-capture.md` + `.manifest.yaml`.

Principles to apply at turn-start: same set as Cycle 1.

Quality bar (Luke directive 2026-05-04): 3 triggers MVP intentional; every trigger complete (not "explicit-request works, ask-and-answer is a stub"). User-ratification gate is structural defence against silent skill-write. Cool-down + budget + hard-cap defend against fatigue + bloat. Design note documents architecture for v0.2.1 + v0.2.x. End-to-end smoke against fixture workspace. No partial features.

Source pointers: master plan §3 Cycle 2; Eric synthesis §2 v0.2.0 (lines 244–276); layered-skills §3 (lines 184–258); §3.6 universal-tier (lines 243–258); v0.1.7 layered-skill discovery `bcf699a`; v0.1.7 PM batch API `122a7c8`; v0.2.0 Cycle 1 SHA backfilled post-seal; smoke discipline `plugins/dev-sdlc/docs/smoke-test-discipline.md`.

Fence + ACs + smoke + AI-time + out-of-scope: per master plan §3 Cycle 2.

Halt triggers: WD drifts; plan-doc not authored before code; Cycle 1 not sealed (serial dependency); trigger detection requires M-FBM-side edits (cross-component ruling); PM extension needed (three-component-fence ruling); SKILL.md frontmatter invalid; SKILL body is a stub; end-to-end smoke fails (proposal doesn't materialise OR materialised SKILL doesn't auto-load); cycle >5 h wall-clock; ODD violations in surrounding code; >3 escalations needed.

Bookkeeping: pos-amend apply (NOT `git commit --amend`); manifest schema v3; single semantic commit; short-form seal commit; §14 method-decision-register backfill in separate post-seal commit; backfill master plan §9 row for Cycle 2; backfill v0.2.0 release-level rows (STATE.md + roadmap §8 + eric-final-delivery §2) with both cycle SHAs + SHIPPED status — only AFTER release-level smoke green.

Model rationale: (none — Sonnet default).
```

---

## §5 — Release-level SOFT smoke gate

SOFT smoke gate at v0.2.0 (per Decision R cadence — HARD at v0.1.6 / v0.1.8 / v0.2.1; SOFT at v0.1.7 / v0.1.9 / v0.2.0). Quality-bar-non-negotiable still applies; all 6 dimensions exercised.

After Cycle 2 seals, dispatcher runs release-level smoke against canonical pos-v2:

1. **D1 cold-state.** Fresh workspace clone. `loam init`. Run:
   - `loam extract --incremental <jsts-playwright-app>` → zero proposals on unchanged code.
   - Synthetic JS code-change (new method on user-creation Express handler) → watch surfaces proposal in PM ("user-creation domain: 1 AC re-extraction proposed"); owner ratifies → contract updates; audit-log entry recorded.
   - Same against ruby-rails-payment fixture (synthetic Rails-callback addition); grouped by Rails-callback-discipline domain.
   - Domain-batching: synthetic 8-AC change across payment-handling + accounting → PM presents 2 batches not 8 individual questions.
   - Production-stake profile: rerun under `safety_profile: production-stake` → dry-run default; proposals emitted, not auto-updated; ratification required.
   - Auto-skill-capture: enable `enable_auto_skill_capture: true` in fixture workspace; fire synthetic ask-and-answer pattern (3 instances); draft surfaces; user ratifies (`Y`); SKILL.md materialises at `<workspace>/.claude/skills/<name>/SKILL.md`; persona auto-loads next turn.
   - `/` menu still shows 20 SKILLs from v0.1.9 close (8 base loam-skills + 12 dev-sdlc).

2. **D2 steady-state.** Re-run watch on unchanged code (zero proposals; idempotent); re-run trigger after ratification (no re-propose); cool-down + budget stable.

3. **D3 restart.** Mid-extraction `kill -TERM` → re-invoke clean; no corrupt cache.

4. **D4 reboot.** macOS reboot. Post-reboot: workspace state survives (extraction cache; cool-down; ratified skills); audit-log survives.

5. **D5 cross-session (most-load-bearing).** Session A: fire skill-capture trigger → ratify → SKILL materialises → end. Session B: persona auto-loads new SKILL via Anthropic discovery (verified via `/` menu). Same for watch: Session A produces proposal → ratifies → contract updates; Session B re-runs watch → recognises updated contract.

6. **D6 telemetry-floor.** Audit log entries per watch run + proposal + ratification/rejection + skill-capture trigger-fire + skill ratification/rejection. Absence detectable.

**Eric-path smoke.** Path 1 (JS/TS/Playwright): contract from v0.1.8 + gate from v0.1.9 + (NEW v0.2.0) synthetic JS code-change → watch surfaces proposal grouped by payment-handling domain → ratify → contract updates → v0.1.9 gate reads updated contract; persona observes recurring pattern across 3+ commits → fires repeated-invocation trigger → drafts `payment-handling-audit-log` workspace-local SKILL → ratify → auto-loads next turn. Path 2 (Rails): analogous with Rails-callback addition + `rails-concern-with-service-object` SKILL. Both paths: v0.1.9 surfaces still functional; new workspace-local skills auto-discovered alongside existing 20.

**Gate to v0.2.1.** v0.2.0 smoke green on all 6 → `git tag v0.2.0` (DO NOT push until Luke gates). v0.2.1 plan-author can begin in parallel after Cycle 2 seals; release-tag push waits on Luke.

---

## §6 — Open items for Luke

Two items. Architectural calls only. Per AUTONOMY directive, all other planning decisions are settled.

1. **Cycle 1 PM-extension scope (preemptive surface).** Cycle 1's PM ratification-queue + domain-batched surfacing extends `framework/per-project-pm/`. v0.1.7 Cycle 4 PM batch API already handles arbitrary question-payloads; open question is whether Cycle 1 needs (a) just a new batch-type registration (`contract-update-proposal`) — thin extension — or (b) a new domain-tag schema in PM-side batch model — substantial extension. *Criticality:* low. *Recommendation:* defer to Cycle 1 plan-author halt-trigger; halt-and-surface if substantial.

2. **Cycle 1 scheduling-integration scope (preemptive surface).** Cycle 1 composes with `framework/scope-of-work/` for cron-style scheduling. Existing scope-of-work primitive supports task scheduling but watch invocation may need a "watch" task-shape. *Criticality:* low. *Recommendation:* defer to Cycle 1 plan-author halt-trigger; halt-and-surface if scope-of-work extension non-trivial.

(No other escalations needed — Decisions N / Q / R all RESOLVED at parent §3.)

---

## §7 — Honest doubts (F2 RF on this decomposition)

The places this decomposition is least confident.

**7.1 — Cycle 1 diff-classifier load-bearing risk.** Mirrors v0.1.9 Cycle 1's classifier risk. Under-identification misses contract drift; over-identification re-extracts unchanged ACs. *Mitigation:* Cycle 1 plan-doc names heuristic explicitly (line-overlap + symbol-overlap + file-existence likely all needed); smoke exercises both small-diff and refactor-shaped diffs; <90% accuracy → halt-and-surface for tree-sitter AST-aware heuristic.

**7.2 — Trigger 2 (repeated-invocation) precision hard to bound.** Exact match too strict, fuzzy too loose. *Mitigation:* Cycle 2 plan-doc names matching heuristic (tool-call sequence + arg-shape similarity, ≥70% overlap); both exact-match and near-match cases exercised in smoke.

**7.3 — Trigger 3 (ask-and-answer) requires M-FBM episode-store reads.** Read-only, but M-FBM API for "find episodes similar to <text>" may not exist in needed shape. *Mitigation:* Cycle 2 plan-doc surfaces this; if M-FBM API insufficient → halt-and-surface for cross-component ruling. Worst case: trigger 3 behind feature-flag, lands fully at v0.2.x post-M-FBM extension.

**7.4 — Auto-skill-capture per-week budget (3) may be wrong.** *Mitigation:* configurable via `skill_capture_weekly_budget`; Eric-feedback at v0.2.1 fresh-user-smoke drives recalibration.

**7.5 — Domain inference may not match Eric's codebase.** Tag-based + file-path-prefix fallback may produce noisy domains on non-conventional folder structures. *Mitigation:* Cycle 1 plan-doc names algorithm explicitly + smoke exercises both well-tagged and poorly-tagged synthetic contracts; v0.2.1 Eric-deliverable smoke surfaces real-world fit.

**7.6 — Serial-build constraint.** Both cycles touch potentially-overlapping framework components. *Mitigation:* serialize per `feedback_serialize_amendment_builds`; plan-author parallel-safe, builds are not. Cycle 2 dispatches after Cycle 1 seals.

**7.7 — Two-cycle decomposition assumes 1+2 don't need integration-glue.** *Mitigation:* if release-level smoke reveals integration friction (e.g., proposal batch and skill-capture batch collide on display ordering or ID namespace), surface as corrective amendment post-seal — don't add Cycle 3 pre-emptively.

**7.8 — MVP trigger scope (3 of 6) may underwhelm Eric.** *Mitigation:* Cycle 2 plan-doc + design note name deferred 3 explicitly + v0.2.x roadmap; Eric sees forward path.

**7.9 — Quality-bar absorption (20%) may be too low for Cycle 1.** Highest-risk single cycle (incremental mode + likely two-or-three-component fence). *Mitigation:* log actuals after Cycle 1 per `feedback_duration_estimation_rubric`; recalibrate before Cycle 2. Cycle 1 halt-trigger at ~6 h wall-clock forces early split.

---

## §8 — Provenance trail

- **Master plan source authority:** `docs/rebuild/plans/eric-final-delivery-plan-2026-05-04.md` §2 v0.2.0 + Decisions I / N / P / Q / R (SOFT at v0.2.0).
- **Layered-skills auto-creation reference:** `docs/rebuild/plans/layered-skill-story-research-2026-05-04.md` §3 + §3.6 universal-tier.
- **v0.1.9 master plan precedent:** `docs/rebuild/plans/v0-1-9-master-plan.md` (sealed `b01d3eb`).
- **v0.1.9 sealed cycles (immediate predecessors):** Cycle 1 `790807d` / Cycle 2 `0dc557e` / Cycle 3 `3284087`. Local release `9022df1`.
- **v0.1.8 sealed (banded contract baseline + extractor full mode):** `9b64cd4`; Cycle 3 `6711dd7`; Cycle 4a `67dd302`; Cycle 4b `c648cf9`; Cycle 5 `e4512b9`.
- **v0.1.7 sealed cycles (PM API + layered-skill discovery):** `3aa20dd` / `73505f0` / `bcf699a` / `122a7c8`.
- **v0.1.6 sealed cycles (production-safety + cost-governance + base-skills):** `3f1d237` / `88674cb`.
- **M-FBM operational health:** `1a1f830`.
- **Smoke-test discipline:** `plugins/dev-sdlc/docs/smoke-test-discipline.md`.
- **Schema v3 + seal-narrative compression:** dev-pattern-simplifications-1 `019cfca`; dev-pattern-simplifications-2 `df3f50f`.
- **Lens 5 swarming reference:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_swarming_recursive_decomposition.md` + framework/CLAUDE.md.
- **Universal-tier framing (Luke 2026-05-04):** layered-skills §3.6 + parent dispatch pre-resolved-tension.
- **AI-time rubric:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_duration_estimation_rubric.md`.
- **Quality bar (Luke directive 2026-05-04):** parent §1 verbatim + Decision R framing.
- **Eric stack context (Rails, JS/TS/Playwright, SOC 2):** parent §1 + parent §3 Decisions P + Q.

---

## §9 — Method-decision register

Master-plan-level method decisions. Per-cycle plan-docs author their own §14 with cycle-specific decisions.

| Decision | Choice | Rationale |
|---|---|---|
| Cycle count | 2 (no Cycle 3 integration-glue) | Lens 5: Cycle 3 would be coordination overhead without tighter AC; cycles compose only via PM batch API; release smoke covers integration. |
| MVP trigger scope (Cycle 2) | 3 of 6 | Per parent §2 + Decision N. Highest-precision subset; deferred 3 require additional component instrumentation OR are dev-mode-only. |
| Watch invocation model | Invoked-on-demand (CLI + cron via scope-of-work) | Mirrors v0.1.9 PR-safety gate shape; simpler operational footprint; D3+D4 smoke trivial. Daemon adds disproportionate complexity. |
| Domain inference | Tag-based primary + file-path-prefix fallback | Composes with v0.1.8 contract author tag annotations; fallback handles untagged ACs without halting. |
| Auto-creation default | Mode 1 (persona drafts + user reviews) | Per layered-skills §3.4 Decision D. Lower friction; user reviews anyway. Mode 2 deferred to v0.2.x. |
| User-ratification surface | PM batch (one-question-at-a-time per Decision Q) | Composes with v0.1.7 Cycle 4 PM batch API. |
| Cool-down period | 14 days post-rejection | Per layered-skills §3.5 #1. Configurable. |
| Per-week budget | 3 proposals/week | Per §3.5 #3. Configurable. Eric-feedback at v0.2.1 drives recalibration. |
| Hard-cap | 20 workspace-local SKILLs | Per §3.5 #1. Above cap → suggest promotion via v0.2.1 skill-promotion-review. |
| `enable_auto_skill_capture` default | `false` (opt-in) | Per layered-skills §3.6 Decision E. Fresh workspace shouldn't immediately propose. |
| Universal-tier placement (Cycle 2) | `plugins/loam-skills/skills/skill-capture-proposal/` | Per parent dispatch pre-resolved-tension + Luke's 2026-05-04 universal-scope clarification. |
| Watch placement (Cycle 1) | `plugins/dev-sdlc/odd-extractor/` | Per parent dispatch pre-resolved-tension + Eric synthesis §2. Watch IS the extractor's incremental mode. |
| SKILL frontmatter shape | `description`-only (no `name` field) | Mirrors all 20 sealed SKILLs at v0.1.9 close. |
| SKILL body section ordering | What captures / When / How / Graceful degradation / Composition / Out of scope | Verified-working pattern across 20 sealed SKILLs. |
| Test file granularity | One test file per AC (~10 per cycle) | Mirrors dev-sdlc convention. |
| Dispatch model tier | Sonnet (default) | No model-rationale line required per swarming-discipline. |
| Quality-bar absorption | 20% (baked into 14–24 h band) | Mirrors v0.1.9 framing. |
| Skip release-level smoke? | NO — SOFT gate per Decision R | Quality-bar-non-negotiable applies. SHIPPED rollup only AFTER smoke green. |

### Per-cycle SHA backfill table

| Cycle | Theme | Apply SHA | Seal SHA |
|---|---|---|---|
| Cycle 1 | Continuous codebase-watch + scheduling + PM ratification-queue + domain-batched AC surfacing | TBD | TBD |
| Cycle 2 | Persona-driven skill capture (auto-creation MVP) + workspace-config flag + design note | TBD | TBD |
| Release-level smoke | Six-dimension smoke + Eric-path smoke (Path 1 + Path 2) | TBD | n/a |

Backfilled per cycle as cycles seal. Final v0.2.0 SHIPPED rollup updates STATE.md + v0-1-x-roadmap.md §8 + eric-final-delivery-plan-2026-05-04 §2 v0.2.0 row only AFTER release-level smoke green.

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Master-plan method-level decisions recorded at §9 above. The `## 14.` heading exists per AC.D-sa.7 lint requirement; content lives at §9 to avoid duplication. Per-cycle plan-docs author their own §14 with cycle-specific decisions.
