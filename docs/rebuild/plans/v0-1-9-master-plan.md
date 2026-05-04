# v0.1.9 master plan — PR-safety gate + provenance-traceable PR template + dev-sdlc skill-ification pass 2 + audit-allowlist cleanup

**Status:** master plan-doc, plan-before-code. Authored 2026-05-04 (Sonnet, plan-author dispatch).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.
**Parent plan:** `docs/rebuild/plans/eric-final-delivery-plan-2026-05-04.md` (§2 v0.1.9 row).
**Companion research (load-bearing):**

- `docs/rebuild/plans/eric-saas-app-use-case-version-sequence-2026-05-04.md` (Eric path; §3 G2 PR safety gate + G6 confidence-banded contract + G8 provenance-traceable PR template).
- `docs/rebuild/plans/layered-skill-story-research-2026-05-04.md` (skills path; §5 — 12 candidate SKILLs; v0.1.9 second-pass list named at §5 first-paragraph list at lines 506–511).
- `docs/rebuild/plans/v0-1-8-master-plan.md` (precedent for cycle-decomposition pattern + per-cycle dispatch-brief shape).
- `plugins/dev-sdlc/docs/smoke-test-discipline.md` (six-dimension smoke spec; SOFT gate at v0.1.9 per Decision R but quality-bar-non-negotiable still applies).
- `docs/rebuild/FUTURE_IDEAS_DRAFT.md` (line 143 — `KNOWN_CROSS_MODE_DEBT` allowlist drift FIDRAFT entry; graduates here).

**Predecessor commits:**

- v0.1.8 sealed (local) at `9b64cd4` — five cycles: Cycle 1 (`c1abda1`), Cycle 2 (`4865028`), Cycle 3 (`6711dd7`), Cycle 4a (`67dd302`), Cycle 4b (`c648cf9`), Cycle 5 (`e4512b9`); release-level HARD smoke gate green on canonical pos-v2; tag deferred.
- v0.1.7 sealed at `3aa20dd` / `73505f0` / `bcf699a` / `122a7c8` — subagents + per-project PM + layered-skill discovery + one-question-at-a-time. Cycle 4 PM batch API + audit-log primitive load-bearing for v0.1.9 Cycle 1's per-band gating audit log + Cycle 2's PR description template ratification surface.
- v0.1.6 sealed at `3f1d237` / `88674cb` — production-safety + base-skills. Production-stake mode load-bearing for Cycle 1's gate behaviour (no auto-merge under production-stake).
- M-FBM operational-health amendment `1a1f830` — load-bearing for cross-session per-codebase state continuity (D5 smoke).

**Quality bar (load-bearing — Luke directive 2026-05-04):**

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

v0.1.9 is the **contract-enforcement release** — v0.1.8 produced the banded contract, v0.1.9 enforces it at PR-time. Every release-note promise corresponds to tested + reliable behavior. All 6 smoke dimensions exercised at release-level (SOFT gate per Decision R; HARD-gate-equivalent quality bar applies). No partial features. The gate is COMPLETE — pre-commit + pre-push + 3 CI templates + override workflow + provenance trail all ship together.

---

## Principles applied this turn

- **CHANNEL** — replies route to dispatcher (not Telegram).
- **AUTONOMY** — settle planning decisions; only escalate genuinely-critical / public-action / financial.
- **F2 RUTHLESS FEEDBACK** — §7 honest doubts surface where this decomposition could be wrong; this plan-doc names the few real tensions (Cycle 2 surface breadth; CI-template coverage subset).
- **LOCKED-DESIGN-NOT-LICENSE** — Eric synthesis §2 v0.1.9 row + layered-skills §5 second-pass list are the locked design for v0.1.9 scope; revisit only if cycle decomposition reveals an obviously better path. Re-tested at §3; held.
- **PROMISES > IN-MOMENT JUDGMENT** — quality bar non-negotiable. Every promised feature delivered fully.
- **ODD §2.5** — every named AC family is named here at master-plan level; per-cycle plan-docs tighten + bind to tests at build time.
- **WD-IN-DISPATCHES** — confirmed at start; propagated to every cycle dispatch brief in §4.
- **PARTITION RULE** — PR-safety as NEW dev-tier component `plugins/dev-sdlc/pr-safety/`; six SKILLs at `plugins/dev-sdlc/skills/<name>/SKILL.md`; audit-allowlist cleanup is an in-component edit on `plugins/dev-sdlc/tools/loam-mode/tests/` (same dev-sdlc parent as Cycle 3's SKILL surface — same fence).
- **PLAN-BEFORE-CODE** — this dispatch IS the plan-before-code. Build cycles dispatch separately, each with its own sub-plan-doc per cycle.
- **SCOPE-ONLY** — this is a plan; method specifications are for the build cycles to author per their cycle plan-docs. Hook-script content / CI-template YAML structure / SKILL body length are all method-level decisions deferred to the build cycle.
- **NEW-SCHEMA OPPORTUNITY** — manifest YAMLs authored per cycle use schema v3 (`plan_doc_ref:`, no `amendment.number`). Seal commits short-form per the new convention.
- **SWARMING (Lens 5)** — three cycles each with strictly-tighter ACs than v0.1.9 parent; further decomposition adds only coordination overhead (e.g., splitting Cycle 2's three CI templates into three sub-cycles is net negative — they share template-rendering plumbing). Halt-criterion satisfied at three.
- **PRINCIPLE-APPLICATION DISCIPLINE** — propagated to every cycle's dispatch brief.

---

## §1 — Executive summary

v0.1.9 is the **contract-enforcement release** of the Eric path. v0.1.8 produced the confidence-banded contract; v0.1.9 enforces it at PR-time. Eric's team submits a PR; loam's gate reads the contract at the head SHA, classifies the PR's diff against the contract's VERIFIED / PLAUSIBLE / HYPOTHESISED ACs, hard-blocks regressions against VERIFIED ACs, surfaces PLAUSIBLE-AC interactions for owner-ratification, and produces an auditable PR description that names every AC the diff touches with its provenance trail (source citation, ratification SHA, override-history if any).

**Theme.** Contract enforcement at PR-time. Per-band gating: VERIFIED is a hard gate (block); PLAUSIBLE informs the reviewer (surfaces decision); HYPOTHESISED is docs-only (commented). Override workflow exists for when an owner needs to ship a contract-update — produces a structured commit-trail shape (`contract-update:` commit) that re-runs CI and updates the contract's VERIFIED set with the explicit override+rationale recorded. Three CI templates ship (GitHub Actions, GitLab CI, CircleCI) — Eric's company's CI provider is unknown; the production-polish move is to ship for the three most common.

Six high-leverage dev-sdlc SKILLs ship alongside, finishing the 12-SKILL skill-ification programme started at v0.1.8 Cycle 5. The second-pass six are: `seal-narrative-writer`, `plan-docs-author`, `hook-violation-recovery`, `component-scaffold-author`, `graceful-fallthrough-with-detection`, `loam-amend-status-quick`. The audit-allowlist cleanup (FIDRAFT graduate from v0.1.8 Cycle 5 release-smoke) folds into Cycle 3's dev-sdlc fence — a four-line test edit removing entries that have already paid down.

**Cycle count.** **Three cycles**, serialized per `feedback_serialize_amendment_builds`:

1. **Cycle 1 — PR-safety gate scaffold + per-band gating engine + override workflow.** NEW component `plugins/dev-sdlc/pr-safety/`. Reads v0.1.8 banded contract; classifies PR diffs; per-band gating logic; override-commit recognition. Composes with `framework/per-project-pm/` (PM-mediated override-ratification) and `framework/cost-governance/` (production-stake profile blocks auto-merge). No hooks installed yet; no CI templates yet. Strictly tighter than v0.1.9 parent.
2. **Cycle 2 — Hook installers + CI templates + provenance-traceable PR description template.** Pre-commit hook installer + pre-push hook installer (composes with the gate engine from Cycle 1). Three CI templates (GitHub Actions / GitLab CI / CircleCI). PR description template that auto-populates from contract + dispatch trail. Single-component fence on `plugins/dev-sdlc/pr-safety/`.
3. **Cycle 3 — 6 dev-sdlc SKILLs second pass + audit-allowlist cleanup.** Six SKILL.md packages at `plugins/dev-sdlc/skills/<name>/SKILL.md`. Audit-allowlist cleanup: remove the 4 stale entries from `KNOWN_CROSS_MODE_DEBT` in `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_references.py`. Single-component fence on `plugins/dev-sdlc/`.

**AI-time band.** **15–28 hours** per parent §2 estimate, midpoint ~21 h (Eric base 10–18 h + skills 5–10 h + audit-allowlist edit ~0.5 h, +20% quality-bar absorption already baked in). Cycle 1 is the highest-risk single cycle — NEW component scaffold + per-band gating logic + override-commit shape (~6–10 h). Cycle 2 ships hooks + 3 CI templates + PR-description template (~5–10 h; templates share rendering plumbing). Cycle 3 ships 6 SKILLs + the four-line allowlist edit (~4–8 h, ~1–2 h per SKILL plus tests + 0.5 h for the allowlist edit). Wall-clock minutes ≈ tool_calls × 0.1–0.15 per the AI-time rubric — recent cycles ran 25–90 min wall-clock per cycle; v0.1.9 cycles project to similar bands.

**Dependencies on prior versions.**

- **v0.1.8** (banded contract surface) — Cycle 1's gate consumes `<workspace>/.loam/extractions/<repo-id>/contract-draft.md` + sidecar.yaml; the contract IS the gate's input. Without v0.1.8 the gate has nothing to enforce against.
- **v0.1.7** (per-project PM + layered-skill discovery) — override workflow surfaces through PM's decision-queue (one-question-at-a-time per Decision Q); 6 SKILLs auto-discovered via the layered-skill mechanism sealed at `bcf699a`.
- **v0.1.6** (production-safety + cost-governance) — production-stake profile gates auto-merge; SOC-2 audit-trail floor (Decision P) requires every gate decision (pass/fail/override) be logged.
- **M-FBM operational health** (`1a1f830`) — load-bearing for cross-session contract-state continuity.

**What closes the release.** v0.1.9 ships when:

1. The gate runs end-to-end against BOTH canonical fixtures (jsts-playwright-app + ruby-rails-payment): given a synthetic PR-diff that touches a VERIFIED AC, the gate hard-blocks; given a diff that touches a PLAUSIBLE AC, the gate surfaces the decision through PM; given a diff touching only HYPOTHESISED ACs, the gate passes with a docs-only annotation.
2. Override workflow tested end-to-end: owner authors a `contract-update:` commit; gate recognizes the override; CI re-runs; contract's VERIFIED set updates with the override+rationale recorded in the audit log.
3. Pre-commit + pre-push hooks installed in canonical pos-v2 actively gate local commits/pushes against the contract.
4. All 3 CI templates (GitHub Actions / GitLab CI / CircleCI) functional end-to-end against the canonical fixtures.
5. PR description template auto-populated from the contract + dispatch trail.
6. All 6 smoke dimensions exercised on the gate itself (SOFT gate per Decision R; quality-bar-non-negotiable applies).
7. Six dev-sdlc SKILLs second pass discoverable + invokable in canonical pos-v2 (live `/` menu shows them — total 20 SKILLs auto-symlinked: 8 base loam-skills + 12 dev-sdlc).
8. `KNOWN_CROSS_MODE_DEBT` allowlist shrunk to its valid set (1 entry: the memory-system/launchd README → true-first-run reference, the only genuinely-pending debt).

If any cycle ships partial, halt and surface; do not proceed to next cycle until that cycle is complete. Quality bar absorbed in band: 20%; v0.1.9 surface is more bounded than v0.1.8's headline release, so the band is tighter.

---

## §2 — Scope source-of-truth

The full v0.1.9 bundle, pulled verbatim from the parent §2 v0.1.9 row plus layered-skills §5 second-pass list, plus the FIDRAFT-graduated audit-allowlist cleanup.

### From Eric synthesis §2 v0.1.9 (PR-safety gate + provenance-traceable PR template)

| Item | Source | Placement |
|---|---|---|
| Pre-commit hook installer | Eric G2 | `plugins/dev-sdlc/pr-safety/installers/` |
| Pre-push hook installer | Eric G2 | `plugins/dev-sdlc/pr-safety/installers/` |
| CI status-check templates (GitHub Actions, GitLab CI, CircleCI) | Eric G2 | `plugins/dev-sdlc/pr-safety/templates/ci/` |
| Provenance-traceable PR description template | Eric G8 | `plugins/dev-sdlc/pr-safety/templates/pr/` |
| Override workflow (contract-update commit shape) | Eric G2 | `plugins/dev-sdlc/pr-safety/` |
| Per-band gating (VERIFIED hard-gate; PLAUSIBLE informs; HYPOTHESISED docs-only) | Eric G6 | `plugins/dev-sdlc/pr-safety/` |

### From layered-skills §5 second-pass (6 SKILLs per parent §2 + layered-skills §5 lines 506–511)

| SKILL | Why second-pass | Placement |
|---|---|---|
| `seal-narrative-writer` | Composes with `loam-amend-cycle` (Cycle 5 first pass); ritual-anchor for `SEAL_COMMIT.notes` | `plugins/dev-sdlc/skills/seal-narrative-writer/` |
| `plan-docs-author` | Companion to `plan-before-code-author` (first pass); the SHAPE of plan-docs (sections, voice) | `plugins/dev-sdlc/skills/plan-docs-author/` |
| `hook-violation-recovery` | Hook-fire is observed in pos-v2 ops; user-side handler ritual SKILL-shaped | `plugins/dev-sdlc/skills/hook-violation-recovery/` |
| `component-scaffold-author` | Lower fire-rate but high-leverage when fired (NEW components rare; this release ships one — `plugins/dev-sdlc/pr-safety/`) | `plugins/dev-sdlc/skills/component-scaffold-author/` |
| `graceful-fallthrough-with-detection` | CDC-anchor; pairs with `audit-finding-triage` (first pass) | `plugins/dev-sdlc/skills/graceful-fallthrough-with-detection/` |
| `loam-amend-status-quick` | Tools wrapper; pairs with `loam-amend-cycle` (first pass) | `plugins/dev-sdlc/skills/loam-amend-status-quick/` |

### From v0.1.8 Cycle 5 release-smoke FIDRAFT graduate (audit-allowlist cleanup)

| Item | Source | Placement |
|---|---|---|
| `KNOWN_CROSS_MODE_DEBT` 4-entry shrink (remove primary-persona/templates/persona-template/prompt.md → FUTURE_IDEAS_DRAFT.md entry; remove 3 workspace-sync/README.md → docs/rebuild/plans/workspace-sync.* entries) | FIDRAFT line 143 (graduated) | `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_references.py` |

Cross-references for traceability:

- **Eric G2 / G6 / G8** — Eric SaaS-app use-case version-sequence research §3 G2 (gate enforcement) + G6 (confidence-banded contract → per-band gating) + G8 (provenance trail).
- **Decision F** (parent §3) — two fixtures RESOLVED YES; bind §5 release-level smoke fixture coverage (jsts-playwright-app + ruby-rails-payment per v0.1.8 Cycle 4b seals).
- **Decision I** (parent §3) — PLAUSIBLE→VERIFIED default-no RESOLVED YES; bind override workflow (every promotion via override is explicit, audit-logged).
- **Decision P** (parent §3) — SOC-2 audit-trail floor RESOLVED YES; bind every gate-decision (pass/fail/override) audit-logged.
- **Decision Q** (parent §3) — one-question-at-a-time RESOLVED YES; bind override-ratification surface through PM batch (Cycle 1 acceptance ladder).
- **Decision R** (parent §3) — HARD smoke gate at v0.1.6 / v0.1.8 / v0.2.1, SOFT elsewhere; v0.1.9 is SOFT gate but quality bar still applies.
- **Layered-skills v0.1.9 second-pass list** — confirmed by parent §2; binds Cycle 3's six SKILLs.
- **FIDRAFT graduate (v0.1.8 Cycle 5 release-smoke surface)** — `KNOWN_CROSS_MODE_DEBT` 4-entry shrink confirmed empirically: source-file scan of the 4 stale (source, target) pairs returns zero matches; allowlist must shrink to four-fewer entries.

### Empirical verification of the audit-allowlist stale entries

Performed during plan-author pre-flight (2026-05-04). Each of the 4 claimed-stale (source, target) pairs scanned via grep against the source file listed:

- `framework/primary-persona/templates/persona-template/prompt.md` ↛ `docs/rebuild/FUTURE_IDEAS_DRAFT.md` — **0 matches** (stale; the source file no longer references the target).
- `framework/workspace-sync/README.md` ↛ `docs/rebuild/plans/workspace-sync.builder-plan.md` — **0 matches** (stale).
- `framework/workspace-sync/README.md` ↛ `docs/rebuild/plans/workspace-sync.manifest.yaml` — **0 matches** (stale).
- `framework/workspace-sync/README.md` ↛ `docs/rebuild/plans/workspace-sync.md` — **0 matches** (stale; the README references `docs/components/workspace-sync.md` — a different path that's not in the dev-only set).

The fifth entry (`framework/memory-system/launchd/README.md` → `docs/rebuild/components/true-first-run/research.md`) IS still present — confirmed at `framework/memory-system/launchd/README.md:52`. This entry stays in the allowlist; resolution is a future memory-system amendment per the original FIDRAFT entry at line 64 of FUTURE_IDEAS_DRAFT.md. Cycle 3's edit is strictly the four-stale shrink — no fence-opening, no memory-system touch.

---

## §3 — Cycle decomposition

Three cycles, each with: theme, scope-tightening relative to v0.1.9 parent, independent fence, AC family seed, smoke dimensions exercised, dependency on prior cycles, out-of-scope deferrals, AI-time band, Eric-relevance, quality-bar audit.

### Cycle 1 — PR-safety gate scaffold + per-band gating engine + override workflow (NEW component)

**Theme.** Establish the gate. NEW component `plugins/dev-sdlc/pr-safety/` with the four-stage workflow shape (read-contract / classify-diff / gate / record). Per-band gating engine: VERIFIED hard / PLAUSIBLE informs / HYPOTHESISED docs-only. Override-commit recognition: `contract-update:` commits trigger contract-update flow with explicit owner ratification through PM. No hooks installed yet; no CI templates yet — those land in Cycle 2.

**Scope-tightening (relative to v0.1.9 parent).** v0.1.9 parent's AC is "the gate runs end-to-end against both fixtures (Cycles 1+2 combined) + 6 SKILLs ship + audit-allowlist shrunk." Cycle 1's AC is "the gate engine reads a banded contract + a diff + classifies + decides + records via PM, invokable as `loam pr-safety gate <repo>` (CLI surface; hook installers come Cycle 2)." Strictly tighter — engine without delivery wrapping.

**Independent fence.** NEW component `plugins/dev-sdlc/pr-safety/`. No edits to other components. Composes (read-only callouts) with `plugins/dev-sdlc/odd-extractor/` (banded-contract reader API), `framework/per-project-pm/` (override-ratification surface — read-only contract-shape import; no PM-side edits in Cycle 1; if Cycle 1 plan-author finds a PM-extension necessary, halt-and-surface for two-component fence per `feedback_serialize_amendment_builds`), and `framework/cost-governance/` (production-stake profile gate-flip — read-only).

**AC family seed: AC.PRSG.* (PR-Safety Gate engine).**

- AC.PRSG.1 — `plugins/dev-sdlc/pr-safety/` exists with proper component scaffold (component.md, tests/, src/, seals/, SEAL_COMMIT sidecar). Schema v3 manifest.
- AC.PRSG.2 — Banded-contract reader API: `read_contract(repo_path) -> BandedContract` returns the contract surface authored at v0.1.8 Cycle 2 (`BandedAC` + `Evidence` + `ConfidenceBand`). Reads from `<workspace>/.loam/extractions/<repo-id>/contract-draft.md` + sidecar.yaml.
- AC.PRSG.3 — Diff-classifier: given a `git diff` between two SHAs (or working-tree vs HEAD), classifies each touched file/symbol against the contract's ACs. Output: `(touched_acs: list[BandedAC], untouched: bool, novel: list[CandidateAC])`. Novel = lines not mapped to any AC (potential contract drift).
- AC.PRSG.4 — Per-band gating engine:
  - VERIFIED touched + diff-suggests-regression → HARD-BLOCK (exit non-zero, structured failure message).
  - PLAUSIBLE touched → SURFACE-DECISION through PM batch (Decision Q one-question-at-a-time); reviewer ratifies (proceed) or escalates (block).
  - HYPOTHESISED touched → DOCS-ONLY annotation in PR description; never blocks.
  - Novel candidates → SURFACE-DECISION (offer "add as PLAUSIBLE / HYPOTHESISED / skip" via PM batch).
- AC.PRSG.5 — Override-commit recognition: commits matching the prefix `contract-update:` trigger the override flow. Override flow: read the override-rationale block from commit body; require explicit `--override` flag + owner ratification through PM; on approval, update contract VERIFIED set + record override (timestamp, owner, rationale, original-VERIFIED-AC, new-VERIFIED-AC) in audit log. Reject silent overrides (per Decision I default-no).
- AC.PRSG.6 — CLI: `loam pr-safety gate <repo>` (default: HEAD vs origin/main); `--diff <sha1>..<sha2>`; `--override` (opt-in for override flow); `--dry-run` (default under production-stake — Decision D + Decision P composition).
- AC.PRSG.7 — SOC-2 audit-trail floor: every gate decision (pass / hard-block / surface-decision / override-applied / override-rejected) appends to `<workspace>/.loam/pr-safety/audit-log/` per Decision P. Schema includes timestamp, repo SHA, diff range, ACs touched, decision, owner (if PM-mediated).
- AC.PRSG.8 — Production-stake profile integration: under `safety_profile: production-stake` (v0.1.6), the gate refuses auto-merge — output requires explicit owner ratification. Under `safety_profile: dev`, hard-blocks still hard-block but PLAUSIBLE-surface defaults to "proceed-with-warning" (still recorded).
- AC.PRSG.9 — Component-level test surface: contract-reader (against v0.1.8 fixtures); diff-classifier (synthetic diffs against jsts-playwright-app fixture); per-band gating engine (unit-tested decision matrix); override recognition (synthetic `contract-update:` commits); CLI invocation; production-stake integration; audit log shape.

**Smoke dimensions exercised.**

- D1 cold-state ✓ — fresh canonical workspace runs `loam pr-safety gate <fixture-repo>` end-to-end; produces gate decision; audit-log entry observable.
- D5 cross-session ✓ — gate state at `<workspace>/.loam/pr-safety/audit-log/` survives `/clear`; subsequent invocations append correctly.
- D6 telemetry-floor ✓ — per-gate-decision audit-log entry per AC.PRSG.7.
- D2 / D3 / D4 inherited from component-shape: gate is invoked-on-demand (not a long-running daemon); D2 (steady-state) and D3 (restart) are n/a; D4 (reboot) is n/a.

**Dependency on prior cycles.** None within v0.1.9 (this is Cycle 1). Within parent: v0.1.8 Cycle 2 banded contract schema (load-bearing — Cycle 1 reads `BandedAC` + `Evidence` types); v0.1.8 Cycle 4b canonical fixtures (gate is exercised against jsts-playwright-app and ruby-rails-payment); v0.1.7 Cycle 4 PM batch API (override-ratification surfaces through PM batch); v0.1.6 production-safety profile + cost-governance dry-run; M-FBM operational health.

**Out-of-scope deferrals.**

- Pre-commit hook installer → Cycle 2.
- Pre-push hook installer → Cycle 2.
- CI templates (GitHub Actions / GitLab CI / CircleCI) → Cycle 2.
- Provenance-traceable PR description template → Cycle 2.
- 6 SKILLs second pass → Cycle 3.
- Audit-allowlist cleanup → Cycle 3.
- Continuous codebase-watch → v0.2.0.
- Eric's actual codebases (smoke against real OSS) → v0.2.1 fresh-user smoke.

**AI-time band.** **6–10 h** (NEW component scaffold + four-stage workflow + per-band gating engine + override-commit recognition + CLI + audit log + production-stake integration + tests + smoke). Wall-clock band: roughly 30–60 minutes per the AI-time rubric (recent NEW-component cycles ran in this band; tool_calls × 0.1–0.15 ≈ wall-clock minutes).

**Eric-relevance.** Cycle 1 IS the engine that gates Eric's PRs against the contract authored at v0.1.8. Without Cycle 1, the v0.1.8 contract is read-only and ratification-only; with Cycle 1, every Eric-team commit/push/PR runs through the gate. The override workflow (AC.PRSG.5) is the social-acceptance escape hatch named in Eric §11.6 — when contract evolution is needed, the override is auditable, not silent.

**Quality-bar audit.** NEW component shape — risk surface. Scope explicitly includes: (a) read-only contract API (no extractor edits), (b) per-band gating engine fully tested against decision matrix, (c) override workflow end-to-end on synthetic `contract-update:` commits, (d) production-stake integration tested. The decision matrix is small (3 bands × 3 actions = 9 cells) — every cell tested. **No partial features.** ✓

---

### Cycle 2 — Hook installers + CI templates + provenance-traceable PR description template

**Theme.** Wrap the gate in delivery surfaces. Pre-commit hook installer + pre-push hook installer compose with the gate engine from Cycle 1 to gate local development. Three CI templates (GitHub Actions / GitLab CI / CircleCI) compose with the gate to gate PR-time CI. PR description template auto-populates from contract + dispatch trail to give human reviewers an at-a-glance provenance view.

**Scope-tightening.** Cycle 1's AC is "engine without delivery wrapping." Cycle 2's AC is "the engine ships hooks + CI templates + a PR description template that all invoke the engine." Strictly tighter — delivery without contract-shape changes.

**Independent fence.** Single-component fence on `plugins/dev-sdlc/pr-safety/`. No edits to other components.

**AC family seed: AC.PRSI.* (PR-Safety Installers + templates).**

- AC.PRSI.1 — Pre-commit hook installer: `loam pr-safety install pre-commit` writes a hook script to `<repo>/.git/hooks/pre-commit` that invokes the gate engine (working-tree vs HEAD) and exits non-zero on HARD-BLOCK. Idempotent (re-run is a no-op or refresh).
- AC.PRSI.2 — Pre-push hook installer: `loam pr-safety install pre-push` writes a hook script to `<repo>/.git/hooks/pre-push` that invokes the gate engine (HEAD vs upstream) and exits non-zero on HARD-BLOCK. Idempotent.
- AC.PRSI.3 — Hook-script semantics: hooks honour the production-stake profile (under production-stake, no auto-bypass; under dev, an env var or --no-verify analog can bypass with audit-log entry). Hook-script body is a thin wrapper around `loam pr-safety gate` — no business logic in the hook itself.
- AC.PRSI.4 — GitHub Actions CI template: `plugins/dev-sdlc/pr-safety/templates/ci/github-actions/pr-gate.yml` renders to a workflow YAML that runs the gate on PR-open + PR-update; surfaces structured failure as a PR comment / status check. Template uses placeholders (repo identifiers / paths) substituted at install time via `loam pr-safety install ci github-actions`.
- AC.PRSI.5 — GitLab CI template: `plugins/dev-sdlc/pr-safety/templates/ci/gitlab-ci/.gitlab-ci.yml.template` analogous to AC.PRSI.4 for GitLab merge-requests.
- AC.PRSI.6 — CircleCI template: `plugins/dev-sdlc/pr-safety/templates/ci/circleci/config.yml.template` analogous for CircleCI workflows.
- AC.PRSI.7 — Provenance-traceable PR description template: `plugins/dev-sdlc/pr-safety/templates/pr/pr-description.md.template` renders a structured PR body with sections — "ACs touched (with provenance)" / "Override-history (if any)" / "Ratifications (timestamp + owner)" / "Audit-log excerpt." Template auto-populates from gate output + audit-log lookup. Renderable as input to `gh pr create --body` / GitLab API / CircleCI build comments.
- AC.PRSI.8 — Install ergonomics: `loam pr-safety install <surface>` with surfaces in `{pre-commit, pre-push, ci github-actions, ci gitlab-ci, ci circleci, pr-template}`; `--all` for every surface. Halts on conflict (pre-existing hook with non-loam content; pre-existing CI workflow at the target path) — surface-as-decision through PM batch per Decision Q (Cycle 1's PM integration is the surface).
- AC.PRSI.9 — End-to-end smoke against canonical fixtures: pre-commit hook + pre-push hook + at least one CI template (GitHub Actions chosen as the most-common; GitLab + CircleCI smoke is template-render-validates only) + PR description template all exercised in canonical pos-v2 against the jsts-playwright-app and ruby-rails-payment fixtures.
- AC.PRSI.10 — Component-level test surface: hook-script generation + idempotency; CI-template rendering (placeholder substitution); PR-description-template rendering; install conflict halt; e2e smoke harness.

**Smoke dimensions exercised.**

- D1 cold-state ✓ — fresh canonical workspace + `loam pr-safety install --all` against a fixture repo → all surfaces installed; gate exercises end-to-end.
- D2 steady-state ✓ — re-running `install` is idempotent; no churn.
- D5 cross-session ✓ — installed hooks survive `/clear`; PR-description template renders consistently.
- D6 telemetry-floor ✓ — install-action audit-log entries (per AC.PRSG.7 inherited).
- D3 / D4 — n/a (one-shot install + filesystem state).

**Dependency on prior cycles.** Cycle 1 (gate engine + audit log + PM integration). Within parent: v0.1.7 Cycle 4 PM batch API (install conflicts surface through PM); v0.1.6 production-safety (hooks honour production-stake).

**Out-of-scope deferrals.**

- 6 SKILLs second pass → Cycle 3.
- Audit-allowlist cleanup → Cycle 3.
- BitBucket Pipelines / Jenkins / Buildkite CI templates → v0.2.x post-Eric (the three-template scope is the production-polish move per Eric synthesis §2 v0.1.9 "ship for the three most common"; Eric's company's CI provider is unknown — the three covered are the most-likely match).
- PR description rendering for non-GitHub surfaces (GitLab MR descriptions, generic markdown) → in-scope at template level (template is markdown; surface-rendering is left to caller).
- Continuous codebase-watch → v0.2.0.

**AI-time band.** **5–10 h** (hook-script authoring + 3 CI templates + PR description template + install ergonomics + e2e smoke + tests). Wall-clock band: roughly 25–60 minutes. Templates share rendering plumbing (placeholder substitution) — the per-template overhead is small once the rendering shape lands.

**Eric-relevance.** Cycle 2 IS the surface Eric's team interacts with. Pre-commit hook fires on every Eric-team commit; CI workflow fires on every PR; PR description gives reviewers the provenance trail. Per Eric synthesis §2 v0.1.9: "Every Eric-team PR (loam-authored or human-authored) gates against the contract." Without Cycle 2, the gate is invokable only via CLI — Cycle 2 makes it observable at every Eric-team workflow checkpoint.

**Quality-bar audit.** Three CI templates is the production-polish move — Eric's CI provider unknown; ship for the three most common. Each template ships complete (not "GitHub Actions works, GitLab is a stub"). Hook installers are idempotent. PR description template is structured (not raw diffs). Override workflow tested end-to-end on a synthetic `contract-update:` commit (smoke harness). **No partial features.** ✓

---

### Cycle 3 — 6 dev-sdlc SKILLs second pass + audit-allowlist cleanup

**Theme.** Finish the 12-SKILL skill-ification programme started at v0.1.8 Cycle 5. Six high-leverage SKILLs from layered-skills §5 second-pass list: `seal-narrative-writer`, `plan-docs-author`, `hook-violation-recovery`, `component-scaffold-author`, `graceful-fallthrough-with-detection`, `loam-amend-status-quick`. Audit-allowlist cleanup folds in: a four-line edit removing the four stale entries from `KNOWN_CROSS_MODE_DEBT`. Single dev-sdlc fence covers both surfaces — the SKILLs at `plugins/dev-sdlc/skills/<name>/SKILL.md` and the test edit at `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_references.py`.

**Scope-tightening.** v0.1.9 parent's AC (composite) includes "6 SKILLs auto-discovered" + "audit-allowlist shrunk to valid set." Cycle 3's AC is exactly that pair, no other v0.1.9 surface. Strictly tighter than parent.

**Independent fence.** Single-component fence on `plugins/dev-sdlc/`. Two surfaces: (a) `plugins/dev-sdlc/skills/<name>/SKILL.md` × 6 SKILLs; (b) `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_references.py` (4-line shrink of `KNOWN_CROSS_MODE_DEBT` set literal).

**AC family seed: AC.SKILLS-DSDLC2.* (dev-sdlc SKILLs second pass) + AC.AUDIT-CLEANUP.* (audit-allowlist shrink).**

- AC.SKILLS-DSDLC2.1 — `seal-narrative-writer` SKILL.md (frontmatter + body covers SEAL_COMMIT.notes structure: what shipped / what deferred / what surfaced / cycle SHA notes; composes with `loam-amend-cycle` Cycle 5 first-pass).
- AC.SKILLS-DSDLC2.2 — `plan-docs-author` SKILL.md (frontmatter + body covers loam plan-doc shape: objective / scope / principles / executive-summary / cycle-decomposition / per-cycle dispatch briefs / honest doubts / provenance trail / method-decision register; composes with `plan-before-code-author` first-pass).
- AC.SKILLS-DSDLC2.3 — `hook-violation-recovery` SKILL.md (frontmatter + body covers: identify which hook fired / read the message / four-bucket triage / fix or surface / retry; composes with all 5 dev-sdlc hooks + `audit-finding-triage` first-pass).
- AC.SKILLS-DSDLC2.4 — `component-scaffold-author` SKILL.md (frontmatter + body covers `templates/component/` invocation: component.md authoring / src/ + tests/ + seals/ scaffolding / SEAL_COMMIT sidecar / partition-rule placement; composes with `loam-amend-cycle`).
- AC.SKILLS-DSDLC2.5 — `graceful-fallthrough-with-detection` SKILL.md (frontmatter + body covers: when to use try/except + fallback / require detection + audit-log surface / never silent-swallow per `feedback_critical_thinking_on_deviations`; composes with `audit-finding-triage`).
- AC.SKILLS-DSDLC2.6 — `loam-amend-status-quick` SKILL.md (frontmatter + body covers: `loam amend status` output interpretation / next-step recommendation / halt-condition surfaces; composes with `loam-amend-cycle`).
- AC.SKILLS-DSDLC2.7 — All 6 auto-discoverable via the v0.1.7 Cycle 3 layered-skill mechanism. Live `/` menu in canonical pos-v2 shows all 12 dev-sdlc SKILLs (6 first-pass + 6 second-pass) + 8 base loam-skills = 20 total.
- AC.SKILLS-DSDLC2.8 — Regression test per SKILL (frontmatter validation, body-section presence checks).
- AC.AUDIT-CLEANUP.1 — `KNOWN_CROSS_MODE_DEBT` set in `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_references.py` is reduced to exactly the one valid entry: `("framework/memory-system/launchd/README.md", "docs/rebuild/components/true-first-run/research.md")`. The other four (1× primary-persona, 3× workspace-sync) entries removed.
- AC.AUDIT-CLEANUP.2 — `test_AC_F3_always_loaded_no_dev_refs` passes after the shrink. (The test enforces "allowlist must shrink to empty when entries no longer present"; prior to the shrink it was failing the `missing == set()` assertion. Post-shrink the assertion holds.)
- AC.AUDIT-CLEANUP.3 — Source-file scan of the 4 removed (source, target) pairs returns zero matches in their respective source files (i.e., the entries were genuinely stale; pre-flight verified at plan-author time).

**Smoke dimensions exercised.**

- D1 cold-state ✓ — fresh canonical workspace shows all 12 dev-sdlc SKILLs in `/` menu (8 + 12 = 20 total auto-symlinked).
- D5 cross-session ✓ — SKILLs visible after `/clear` (inherited from v0.1.7 Cycle 3 layered-skill discovery).
- D6 telemetry-floor — inherited (no new audit-log shape introduced; allowlist edit is a test-file change with no runtime telemetry).
- D2 / D3 / D4 — inherited (filesystem state; one-shot resolution).

**Dependency on prior cycles.** v0.1.9 Cycles 1+2 (per `feedback_serialize_amendment_builds` — single tree, serial cycles). Within parent: v0.1.7 Cycle 3 layered-skill discovery (load-bearing — SKILL auto-discovery mechanism); v0.1.8 Cycle 5 first-pass SKILLs (six second-pass SKILLs compose with the first-pass surface — `seal-narrative-writer` ⇄ `loam-amend-cycle`, `plan-docs-author` ⇄ `plan-before-code-author`, etc.).

**Out-of-scope deferrals.**

- Auto-creation mechanism → v0.2.0 (per parent §2).
- Promotion rubric → v0.2.1 (per parent §2 + Decision L).
- Memory-system/launchd/README.md cross-mode reference scrub → future memory-system amendment (per FIDRAFT line 64; Cycle 3 only handles the four-stale shrink, never the pending-debt entry).

**AI-time band.** **4–8 h** (~1–2 h per SKILL × 6 + ~0.5 h for the audit-allowlist edit + tests + smoke + manifest). Wall-clock band: roughly 25–50 minutes. Six SKILLs + a four-line test edit is the smallest cycle of the release.

**Eric-relevance.** SKILLs are dev-mode-only — they ship for the loam dev-experience (Luke, future loam-builders, Eric as he learns the surface in dev-mode). Six SKILLs make ritual self-evident. Audit-allowlist cleanup is internal (loam-mode partition discipline); no Eric-facing surface change.

**Quality-bar audit.** Each SKILL body covers the FULL ritual (not a stub). All six auto-discoverable. Each SKILL has a regression test. Audit-allowlist edit verifies the test passes (not just the file change). **No partial features.** ✓

---

### Decomposition stopping-criterion check

Per Lens 5 (swarming): decompose until each subtask's AC is strictly tighter than parent's; stop when the proposed split introduces only coordination overhead.

- Three cycles each have ACs strictly tighter than v0.1.9 parent (Cycle 1: engine without delivery; Cycle 2: delivery without contract-shape changes; Cycle 3: SKILLs + cleanup).
- Further decomposition options considered:
  - **Splitting Cycle 2's three CI templates into three sub-cycles** — net negative; templates share rendering plumbing; per-template overhead is small once shape lands. Coordination overhead exceeds tightness gain.
  - **Splitting Cycle 1's per-band gating from override workflow** — the gating engine's decision matrix and the override flow share the audit-log shape and the PM-batch surface; splitting introduces redundant test scaffolding for two seal commits where one suffices.
  - **Splitting Cycle 3's audit-allowlist cleanup from the 6 SKILLs** — net negative; the four-line edit fits cleanly inside the dev-sdlc fence with the SKILL surface; making it a fourth cycle adds a manifest + seal commit + roadmap §8 row for what is empirically a 0.5 h edit.
- Stopping at three is the cleanest. Cycle count band-check: 3 ∈ [2, 5] (parent halt-trigger range).

---

## §4 — Per-cycle dispatch briefs

Three dispatch briefs, one per cycle, each ready to dispatch at v0.1.9 build time.

### Cycle 1 dispatch brief — PR-safety gate scaffold + per-band gating engine + override workflow

```
# v0.1.9 Cycle 1 build dispatch — PR-safety gate scaffold + per-band gating engine + override workflow

Working directory: /Users/lukeivers/ivers-corp-pos-v2/ (canonical pos-v2). NOT pos3.

## Principles to apply at turn-start

- CHANNEL — replies route to dispatcher (NOT Telegram).
- AUTONOMY — settle decisions; flag only critical / public / financial.
- F2 RUTHLESS FEEDBACK — name disagreements / quality gaps immediately. Especially for:
  (a) per-band gating decision-matrix corner cases (novel candidates outside any AC; symbol-vs-line classification);
  (b) override-commit shape (commit-message convention vs trailer convention);
  (c) PM-extension necessity (if Cycle 1 needs PM-side edits, halt-and-surface for two-component fence).
- LOCKED-DESIGN-NOT-LICENSE — Eric synthesis §2 v0.1.9 row + parent Decisions I/P/Q/R are locked; revisit only if a fixture surfaces a contradiction.
- PROMISES > IN-MOMENT JUDGMENT — quality bar non-negotiable. Per-band gating engine COMPLETE (no "VERIFIED works, PLAUSIBLE is a stub").
- ODD §2.5 — every line maps to a named AC.PRSG.* AC.
- WD-IN-DISPATCHES — confirm at start.
- PARTITION RULE — NEW component at `plugins/dev-sdlc/pr-safety/`. Read-only callouts to odd-extractor + per-project-pm + cost-governance.
- PLAN-BEFORE-CODE — write the cycle plan-doc BEFORE code.
- POS-AMEND BOOKKEEPING — pos-amend apply (NOT --amend); single-component fence per cycle plan-doc.
- SCOPE-ONLY — method (which AST/diff library, hook-script template language, audit-log YAML shape) is yours; surface choices in plan-doc.
- NEW-SCHEMA — manifest v3 (`plan_doc_ref:`, no `amendment.number`).
- SOC-2 FLOOR — every gate decision audit-logged per Decision P.
- ONE-QUESTION-AT-A-TIME — override-ratification surfaces through PM batch per Decision Q.
- SUBAGENT-ODD-VIOLATION-HALT — halt and surface ODD violations in your work OR surrounding code.

## QUALITY BAR

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

- Per-band gating engine COMPLETE — every band-action cell of the 3×3 decision matrix tested.
- Override workflow runs end-to-end on a synthetic `contract-update:` commit.
- Production-stake profile integration tested (no auto-merge under production-stake).
- Audit log SOC-2 compliant (every gate decision logged).
- No silent override (Decision I default-no honoured).

## Source pointers

- Master plan: `docs/rebuild/plans/v0-1-9-master-plan.md` — §3 Cycle 1 scope.
- Eric synthesis: `docs/rebuild/plans/eric-final-delivery-plan-2026-05-04.md` — §2 v0.1.9 row + Decisions I/P/Q/R.
- v0.1.8 Cycle 2 banded contract: `plugins/dev-sdlc/odd-extractor/` (BandedAC + Evidence + ConfidenceBand types; sealed at `4865028`).
- v0.1.8 Cycle 4b canonical fixtures: `plugins/dev-sdlc/odd-extractor/tests/fixtures/jsts-playwright-app/` + `ruby-rails-payment/` (sealed at `c648cf9`).
- v0.1.7 Cycle 4 PM batch API: `framework/per-project-pm/` (`record_response`, `surface_next_questions_batch`, `PendingResponseError`; sealed at `122a7c8`).
- v0.1.6 production-safety: `framework/cost-governance/` + `framework/workspace-bootstrap/` (`safety_profile` config; sealed at `3f1d237`).
- ODD-methodology doc: `plugins/dev-sdlc/docs/odd-methodology.md` (§11 confidence-band semantics — Cycle 1's reader API consumes this schema).
- Smoke-test discipline: `plugins/dev-sdlc/docs/smoke-test-discipline.md`.

## Sub-plan path

Author at: `docs/rebuild/plans/v0-1-9-cycle-1-pr-safety-gate-engine.md`
Manifest at: `docs/rebuild/plans/v0-1-9-cycle-1-pr-safety-gate-engine.manifest.yaml`
Status file: `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-9-cycle-1-status-2026-05-04.md`

## Fence

NEW component `plugins/dev-sdlc/pr-safety/`. No edits to other components in Cycle 1.

If plan-author finds a PM-side extension necessary (e.g., a new PM batch shape for override-ratification), halt-and-surface to dispatcher; that becomes a two-component fence under `feedback_serialize_amendment_builds` and the dispatcher decides whether to extend Cycle 1 or split.

## Acceptance criteria

Author the AC ladder during plan-doc time. Seeds:

- AC.PRSG.1 — `plugins/dev-sdlc/pr-safety/` component scaffold + manifest v3.
- AC.PRSG.2 — Banded-contract reader API (`read_contract`).
- AC.PRSG.3 — Diff-classifier (`(touched_acs, untouched, novel)`).
- AC.PRSG.4 — Per-band gating engine (3×3 decision matrix; novel-candidate handling).
- AC.PRSG.5 — Override-commit recognition (`contract-update:` prefix; PM-mediated ratification).
- AC.PRSG.6 — CLI: `loam pr-safety gate <repo>` with `--diff`, `--override`, `--dry-run`.
- AC.PRSG.7 — SOC-2 audit-trail floor (per-gate-decision audit log).
- AC.PRSG.8 — Production-stake profile integration.
- AC.PRSG.9 — Component-level test surface.

## Smoke (REALISTIC CONDITION — applicable dimensions per smoke-test-discipline.md)

- D1 cold-state: fresh canonical workspace runs `loam pr-safety gate <fixture-repo>` end-to-end; produces gate decision; audit-log entry observable.
- D5 cross-session: gate state at `<workspace>/.loam/pr-safety/audit-log/` survives `/clear`; subsequent invocations append correctly.
- D6 telemetry-floor: per-gate-decision audit-log entry per AC.PRSG.7.
- D2 / D3 / D4: n/a per cycle scope (gate is invoked-on-demand, not a long-running daemon); document n/a in plan-doc.

## Halt triggers

- WD drifts → halt + surface.
- v0.1.8 Cycles 2+4b not sealed (banded contract + canonical fixtures absent) → halt.
- v0.1.7 Cycle 4 PM batch API absent → halt.
- Plan-doc not authored before code → halt.
- Any AC fails the partial-feature test (would ship partial) → halt + reframe.
- Override workflow allows a silent promotion (Decision I violation) → halt + RF.
- 6-dimension smoke fails on D5 cross-session → halt (this is the ship-test for cross-session continuity).
- Cycle exceeds 5 hours wall-clock with no clear progress on the gating engine → halt with partial findings; consider further decomposition (e.g., split engine from override).
- ODD violations discovered in surrounding code → halt + surface; do not silently extend.
- More than 3 escalations needed → halt + describe.
- PM-side extension needed → halt + surface for two-component fence ruling.

## Out of scope

- Pre-commit hook installer → Cycle 2.
- Pre-push hook installer → Cycle 2.
- CI templates → Cycle 2.
- PR description template → Cycle 2.
- 6 SKILLs second pass → Cycle 3.
- Audit-allowlist cleanup → Cycle 3.
- Continuous codebase-watch → v0.2.0.

## Bookkeeping

- pos-amend apply (NOT --amend); create NEW commits if a file is missed.
- Single semantic commit per cycle (manifest+apply merged per schema v3 AC.DPS1.6).
- Backfill `docs/rebuild/plans/v0-1-x-roadmap.md` §8 method-decision register row for v0.1.9 Cycle 1.
- Backfill `docs/rebuild/plans/eric-final-delivery-plan-2026-05-04.md` §2 v0.1.9 progress notes after seal.
- Backfill `docs/rebuild/plans/v0-1-9-master-plan.md` §9 method-decision register row.
- DO NOT push tags until v0.1.9 release-level smoke green AND Luke gates the release.

## Model rationale

(none — Sonnet is the default for sealed-component amendment build.)
```

### Cycle 2 dispatch brief — Hook installers + CI templates + provenance-traceable PR description template

```
# v0.1.9 Cycle 2 build dispatch — Hook installers + CI templates + provenance-traceable PR description template

Working directory: /Users/lukeivers/ivers-corp-pos-v2/ (canonical pos-v2). NOT pos3.

## Principles to apply at turn-start

- CHANNEL — replies route to dispatcher (NOT Telegram).
- AUTONOMY — settle decisions; flag only critical/public/financial.
- F2 RUTHLESS FEEDBACK — name disagreements / quality gaps immediately. Especially for:
  (a) hook-script bypass semantics under dev profile (env-var convention vs --no-verify analog);
  (b) CI-template placeholder-substitution shape (which placeholders are repo-specific vs install-time);
  (c) PR-description template surface (markdown-only vs surface-specific renderings).
- LOCKED-DESIGN-NOT-LICENSE — Cycle 1 gate engine + audit-log shape are locked; revisit only if a fixture surfaces a contradiction.
- PROMISES > IN-MOMENT JUDGMENT — quality bar non-negotiable. Three CI templates ship complete (no "GitHub works, GitLab is a stub").
- ODD §2.5 — every line maps to a named AC.PRSI.* AC.
- WD-IN-DISPATCHES — confirm at start.
- PARTITION RULE — single-component fence on `plugins/dev-sdlc/pr-safety/`. Templates at `plugins/dev-sdlc/pr-safety/templates/{ci,pr}/`; installers at `plugins/dev-sdlc/pr-safety/installers/`.
- PLAN-BEFORE-CODE — write the cycle plan-doc BEFORE code.
- POS-AMEND BOOKKEEPING — pos-amend apply (NOT --amend).
- SCOPE-ONLY — method (template language, placeholder syntax, install-conflict detection) is yours.
- NEW-SCHEMA — manifest v3.
- SOC-2 FLOOR — every install action audit-logged.
- SUBAGENT-ODD-VIOLATION-HALT — halt and surface ODD violations in your work OR surrounding code.

## QUALITY BAR

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

- Three CI templates ship COMPLETE — every one renders + smoke-validates.
- Pre-commit + pre-push hook installers idempotent.
- PR description template auto-populates from contract + dispatch trail (not hand-authored).
- Install conflicts surface through PM (Cycle 1 PM integration); never silent overwrite.
- Override workflow exercised end-to-end via the canonical fixture smoke.

## Source pointers

- Master plan: `docs/rebuild/plans/v0-1-9-master-plan.md` — §3 Cycle 2 scope.
- Cycle 1 plan-doc + seal SHA (predecessor; Cycle 1 ships the gate engine + CLI that hooks/CI invoke).
- v0.1.6 production-safety: hook-script bypass semantics honour `safety_profile`.
- v0.1.7 Cycle 4 PM batch API: install-conflicts surface as PM batch decisions.
- v0.1.8 Cycle 4b canonical fixtures: `jsts-playwright-app/` + `ruby-rails-payment/`.
- Eric synthesis §2 v0.1.9: 3 CI templates production-polish reasoning.

## Sub-plan path

Author at: `docs/rebuild/plans/v0-1-9-cycle-2-installers-templates.md`
Manifest at: `docs/rebuild/plans/v0-1-9-cycle-2-installers-templates.manifest.yaml`
Status file: `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-9-cycle-2-status-2026-05-04.md`

## Fence

Single-component fence on `plugins/dev-sdlc/pr-safety/`. Sub-paths:

- `plugins/dev-sdlc/pr-safety/installers/` (pre-commit + pre-push hook generators).
- `plugins/dev-sdlc/pr-safety/templates/ci/{github-actions,gitlab-ci,circleci}/` (CI templates).
- `plugins/dev-sdlc/pr-safety/templates/pr/` (PR description template).
- `plugins/dev-sdlc/pr-safety/src/` (install ergonomics CLI extension).
- `plugins/dev-sdlc/pr-safety/tests/` (template-render + install-idempotency + e2e-smoke tests).

## Acceptance criteria

Seeds:

- AC.PRSI.1 — Pre-commit hook installer + idempotent re-run.
- AC.PRSI.2 — Pre-push hook installer + idempotent re-run.
- AC.PRSI.3 — Hook-script honours production-stake profile.
- AC.PRSI.4 — GitHub Actions CI template + render-validates.
- AC.PRSI.5 — GitLab CI template + render-validates.
- AC.PRSI.6 — CircleCI template + render-validates.
- AC.PRSI.7 — Provenance-traceable PR description template (auto-populates).
- AC.PRSI.8 — Install ergonomics CLI: `loam pr-safety install <surface>` + `--all` + conflict-halt.
- AC.PRSI.9 — End-to-end smoke (pre-commit + pre-push + GitHub Actions + PR description) against canonical fixtures.
- AC.PRSI.10 — Component-level test surface.

## Smoke

- D1 cold-state: fresh canonical workspace + `loam pr-safety install --all` against a fixture repo → all surfaces installed; gate exercises end-to-end.
- D2 steady-state: re-running `install` is idempotent.
- D5 cross-session: installed hooks survive `/clear`; PR-description template renders consistently.
- D6 telemetry-floor: install-action audit-log entries inherited from Cycle 1 audit-log.
- D3 / D4: n/a (one-shot install + filesystem state).

## Halt triggers

- Cycle 1 not sealed → halt (predecessor required).
- Plan-doc not authored before code → halt.
- Any CI template ships render-only without smoke-validation → halt + RF.
- Hook installer overwrites pre-existing non-loam hook silently → halt + RF.
- PR description template hand-authored (not auto-populated from gate output) → halt + RF.
- Cycle exceeds 5 hours wall-clock → halt with partial findings.
- ODD violations in surrounding code → halt + surface.
- More than 3 escalations needed → halt + describe.

## Out of scope

- 6 SKILLs second pass → Cycle 3.
- Audit-allowlist cleanup → Cycle 3.
- BitBucket / Jenkins / Buildkite CI templates → v0.2.x.
- Continuous codebase-watch → v0.2.0.

## Bookkeeping

- pos-amend apply.
- Backfill v0.1.x-roadmap §8 + eric-final-delivery §2 + v0.1.9 master plan §9.
- DO NOT push tags.

## Model rationale

(none — Sonnet default.)
```

### Cycle 3 dispatch brief — 6 dev-sdlc SKILLs second pass + audit-allowlist cleanup

```
# v0.1.9 Cycle 3 build dispatch — 6 dev-sdlc SKILLs second pass + audit-allowlist cleanup

Working directory: /Users/lukeivers/ivers-corp-pos-v2/ (canonical pos-v2). NOT pos3.

## Principles to apply at turn-start

- CHANNEL — replies route to dispatcher (NOT Telegram).
- AUTONOMY — settle decisions; flag only critical/public/financial.
- F2 RUTHLESS FEEDBACK — name SKILL-shape gaps; SKILL bodies reflect actual ritual, not aspirational shape. Especially:
  (a) compose-with relationships to first-pass SKILLs accurate (not a silent stub);
  (b) audit-allowlist edit verifies test passes (not just file change).
- LOCKED-DESIGN-NOT-LICENSE — six-SKILL list is from layered-skills §5 second-pass; revisit only if a SKILL is clearly redundant after Cycles 1+2 reveal scope.
- PROMISES > IN-MOMENT JUDGMENT — six SKILLs ship; no "five plus a sixth deferred." Audit-allowlist edit closes the FIDRAFT entry; no half-shrink.
- ODD §2.5 — every line maps to AC.SKILLS-DSDLC2.* or AC.AUDIT-CLEANUP.*.
- WD-IN-DISPATCHES — confirm at start.
- PARTITION RULE — single-component fence on `plugins/dev-sdlc/`. Six SKILLs at `plugins/dev-sdlc/skills/<name>/SKILL.md`; allowlist edit at `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_references.py`.
- PLAN-BEFORE-CODE — write the cycle plan-doc BEFORE code.
- POS-AMEND BOOKKEEPING — pos-amend apply (NOT --amend).
- SCOPE-ONLY — method (SKILL body length, examples count, exact test edit form) is yours.
- NEW-SCHEMA — manifest v3.
- SUBAGENT-ODD-VIOLATION-HALT — halt and surface ODD violations in your work OR surrounding code.

## QUALITY BAR

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

- Each SKILL body covers the FULL ritual — not a stub.
- All 12 dev-sdlc SKILLs auto-discoverable in canonical pos-v2 (live `/` menu shows them; total 20 with 8 base loam-skills).
- Each SKILL has a regression test.
- Audit-allowlist shrunk to exactly the one valid entry; test_AC_F3_always_loaded_no_dev_refs passes.

## Source pointers

- Master plan: `docs/rebuild/plans/v0-1-9-master-plan.md` — §3 Cycle 3 scope.
- Layered-skills research §5 (12 candidate SKILLs; second-pass list at lines 506–511).
- v0.1.7 Cycle 3 layered-skill discovery mechanism (`bcf699a`) — load-bearing.
- v0.1.8 Cycle 5 first-pass SKILLs at `plugins/dev-sdlc/skills/` for shape reference + compose-with relationships.
- FIDRAFT line 143 — `KNOWN_CROSS_MODE_DEBT` allowlist drift entry (graduates here).
- Empirical pre-flight (master plan §2) — confirms 4 stale entries genuinely have zero source-file matches.

## Sub-plan path

Author at: `docs/rebuild/plans/v0-1-9-cycle-3-dev-sdlc-skills-pass-2-and-audit-cleanup.md`
Manifest at: `docs/rebuild/plans/v0-1-9-cycle-3-dev-sdlc-skills-pass-2-and-audit-cleanup.manifest.yaml`
Status file: `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-9-cycle-3-status-2026-05-04.md`

## Fence

Single-component fence on `plugins/dev-sdlc/`. Two surfaces inside the fence:

- 6 new SKILL.md packages at `plugins/dev-sdlc/skills/<name>/SKILL.md`:
  - `seal-narrative-writer/`
  - `plan-docs-author/`
  - `hook-violation-recovery/`
  - `component-scaffold-author/`
  - `graceful-fallthrough-with-detection/`
  - `loam-amend-status-quick/`
- 4-line shrink of `KNOWN_CROSS_MODE_DEBT` set literal at `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_references.py`.

## Acceptance criteria

Seeds:

- AC.SKILLS-DSDLC2.1 — `seal-narrative-writer` SKILL.md (composes with `loam-amend-cycle`).
- AC.SKILLS-DSDLC2.2 — `plan-docs-author` SKILL.md (composes with `plan-before-code-author`).
- AC.SKILLS-DSDLC2.3 — `hook-violation-recovery` SKILL.md (composes with `audit-finding-triage`).
- AC.SKILLS-DSDLC2.4 — `component-scaffold-author` SKILL.md (composes with `loam-amend-cycle`).
- AC.SKILLS-DSDLC2.5 — `graceful-fallthrough-with-detection` SKILL.md (composes with `audit-finding-triage`).
- AC.SKILLS-DSDLC2.6 — `loam-amend-status-quick` SKILL.md (composes with `loam-amend-cycle`).
- AC.SKILLS-DSDLC2.7 — All 6 auto-discoverable; `/` menu shows 20 total SKILLs (8 base + 12 dev-sdlc).
- AC.SKILLS-DSDLC2.8 — Regression test per SKILL.
- AC.AUDIT-CLEANUP.1 — `KNOWN_CROSS_MODE_DEBT` shrunk to exactly the one valid entry (memory-system/launchd/README.md → true-first-run/research.md).
- AC.AUDIT-CLEANUP.2 — `test_AC_F3_always_loaded_no_dev_refs` passes after the shrink.
- AC.AUDIT-CLEANUP.3 — Source-file scan of removed (source, target) pairs returns zero matches (verifies entries were genuinely stale).

## Smoke

- D1 cold-state: fresh canonical workspace shows all 12 dev-sdlc SKILLs in `/` menu.
- D5 cross-session: SKILLs visible after `/clear`.
- D6 telemetry-floor: inherited.
- D2 / D3 / D4: inherited.

## Halt triggers

- Cycles 1+2 not sealed → halt.
- v0.1.7 Cycle 3 (layered-skill discovery) not sealed → halt.
- Plan-doc not authored before code → halt.
- Any SKILL frontmatter invalid → halt.
- Any SKILL body is a stub or aspirational placeholder → halt + RF.
- Live `/` menu fails to show any of the 6 → halt (this is the ship-test).
- Audit-allowlist edit removes the still-valid memory-system entry by mistake → halt + RF.
- `test_AC_F3_always_loaded_no_dev_refs` fails post-edit → halt; the test failure says either (a) an entry I removed is still in source, or (b) a new cross-mode reference appeared since pre-flight.
- Cycle exceeds 5 hours wall-clock → halt + describe.
- ODD violations → halt + surface.
- More than 3 escalations needed → halt + describe.

## Out of scope

- Auto-creation mechanism → v0.2.0.
- Promotion rubric → v0.2.1.
- Memory-system/launchd/README.md scrub → future memory-system amendment.

## Bookkeeping

- pos-amend apply.
- Backfill v0.1.x-roadmap §8 + eric-final-delivery §2 + v0.1.9 master plan §9.
- Close FIDRAFT line 143 entry (audit-allowlist drift) on seal — mark as graduated/closed; note Cycle 3 seal SHA.
- DO NOT push tags.

## Model rationale

(none — Sonnet default.)
```

---

## §5 — Release-level smoke

Per Decision R: SOFT smoke gate at v0.1.9 (HARD gate at v0.1.6 / v0.1.8 / v0.2.1). v0.1.9 is a SOFT gate but the quality-bar-non-negotiable position still applies. All 6 dimensions exercised at release-level even though release isn't blocked by smoke regressions.

**End-to-end smoke shape.**

After Cycle 3 seals, the dispatcher runs a release-level smoke pass against canonical pos-v2 covering the full v0.1.9 surface:

1. **D1 cold-state.** Fresh canonical workspace clone. `loam init` + dependencies. Run:
   - `loam pr-safety install --all` against the jsts-playwright-app fixture → all surfaces installed (pre-commit + pre-push + GitHub Actions + GitLab CI + CircleCI + PR description template).
   - Synthetic PR-diff that touches a VERIFIED AC against the jsts-playwright-app fixture's contract → gate HARD-BLOCKS (exit non-zero; structured failure message; audit-log entry).
   - Synthetic PR-diff that touches a PLAUSIBLE AC → gate SURFACES decision through PM batch (one-question-at-a-time per Decision Q); reviewer ratifies (proceed); audit-log entry.
   - Synthetic PR-diff that touches only HYPOTHESISED ACs → gate PASSES with docs-only annotation; audit-log entry.
   - Synthetic `contract-update:` commit with explicit owner ratification → override flow updates contract VERIFIED set; audit-log entry records (timestamp, owner, rationale, original-AC, new-AC).
   - Same workflow against the ruby-rails-payment fixture — both fixtures exercise per-band gating.
   - PR description template auto-populated; sections (ACs touched / Override-history / Ratifications / Audit-log excerpt) all present.
   - `/` menu shows 20 SKILLs (8 base loam-skills + 12 dev-sdlc).

2. **D2 steady-state.** Re-run `install` (idempotent); re-run gate against same diffs (decision stable; no audit-log churn beyond new run).

3. **D3 restart.** Mid-gate `kill -TERM` the gate process; supervisor or operator re-invokes; re-runs cleanly. (Gate is invoked-on-demand, not a long-running daemon — D3 is "process restarts cleanly," not "supervisor recovers from crash.")

4. **D4 reboot.** macOS reboot (or simulated equivalent — `launchctl bootout` + `launchctl bootstrap` for memory-system worker which is the long-running process; gate itself is invoked-on-demand). Post-reboot: installed hooks survive (filesystem state); audit-log at `<workspace>/.loam/pr-safety/audit-log/` survives.

5. **D5 cross-session.** Most-load-bearing dimension. Session A: start gate against a fixture diff → produce decision → end. Session B (fresh `claude`): same gate run against same diff → identical decision (modulo time-stamp drift); audit-log shows two entries.

6. **D6 telemetry-floor.** Audit log entries per gate decision, per install action, per override. Absence detectable.

**End-to-end "the path Eric will walk" smoke.**

Eric's team submits a PR; loam's gate enforces the contract authored at v0.1.8. The release-level e2e smoke exercises the full path against the canonical fixtures (jsts-playwright-app + ruby-rails-payment) — these are the same fixtures v0.1.8 used; v0.1.9 adds the gate on top:

**Path 1 — Eric's first project (JS/TS/Playwright).**

- Step 1 (already done at v0.1.8): contract authored at `<workspace>/.loam/extractions/jsts-playwright-app/contract-draft.md` with 12 VERIFIED + 38 PLAUSIBLE + 10 HYPOTHESISED = 60 ACs (per v0.1.8 Cycle 4a smoke).
- Step 2: `loam pr-safety install --all` in the fixture repo → hooks installed; CI template installed; PR description template installed.
- Step 3: synthetic PR introducing a regression on `AC.JSTS.Express.UserCreate` (a VERIFIED AC anchored to a passing Jest test) → pre-commit hook HARD-BLOCKS; CI workflow HARD-BLOCKS; PR description template flags the regression with provenance trail (source citation, ratification SHA).
- Step 4: owner authors `contract-update:` commit with rationale → override flow surfaces through PM batch → owner ratifies → contract VERIFIED set updates → CI re-runs PASSES → audit-log records the override sequence.

**Path 2 — Eric's second project (Rails).**

- Step 1 (already done at v0.1.8): contract authored at `<workspace>/.loam/extractions/ruby-rails-payment/contract-draft.md` with 15 VERIFIED + 48 PLAUSIBLE + 4 HYPOTHESISED = 67 ACs (per v0.1.8 Cycle 4b smoke).
- Step 2–4: analogous to Path 1, exercising a Rails-specific VERIFIED AC (e.g., a passing RSpec spec on an ActiveRecord callback).

**Both paths.** All 12 dev-sdlc SKILLs auto-discovered; audit-allowlist test passes; test_AC_F3_always_loaded_no_dev_refs green.

**Gate to v0.2.0.**

v0.1.9 release-level smoke green on all 6 dimensions on canonical pos-v2 → `git tag v0.1.9` → DO NOT push tag until Luke gates the release. Per Decision R, this is a SOFT gate — v0.2.0 plan-author can begin in parallel after Cycle 3 seals; release-tag push waits on Luke.

---

## §6 — Open items for Luke

Two items. Architectural calls only.

1. **Cycle 1 PM-extension scope (preemptive surface).** Cycle 1's override workflow surfaces ratification through `framework/per-project-pm/`. Cycle 1 dispatches as single-component fence on `plugins/dev-sdlc/pr-safety/` — read-only PM API call, no PM-side edits. If Cycle 1 plan-author finds the PM batch API needs a new shape (e.g., a override-ratification-specific batch type with rationale-field), the cycle becomes two-component (pr-safety + per-project-pm) per `feedback_serialize_amendment_builds`. *Criticality:* low — the v0.1.7 Cycle 4 batch API already handles arbitrary question-payloads with rationale; Cycle 1 plan-author's first-pass should fit cleanly. *Recommendation:* defer to Cycle 1 plan-author halt-trigger; if PM-extension needed, halt-and-surface for ruling at that point (don't pre-emptively expand fence here).

2. **Cycle 2 install-conflict policy under non-canonical hook content.** AC.PRSI.8 says "halt on conflict" with PM-mediated decision-surface. The conflict surface is "pre-existing non-loam content at the target hook path." Edge case: an existing hook from the `husky` Node convention (common in JS/TS projects — Eric's first project) lives at `.husky/<hook>` rather than `.git/hooks/<hook>`. *Criticality:* medium — JS/TS projects routinely use husky; loam's gate should compose, not collide. *Recommendation:* Cycle 2 plan-author detects husky presence + emits a husky-shaped hook stub (`.husky/<hook>` invokes loam) instead of a `.git/hooks/<hook>` write, when husky is detected. If the husky-detection logic is non-trivial, surface as a Cycle 2 plan-doc decision.

(No Decision R / Decision O / Decision P / Decision Q escalations needed — all already RESOLVED YES at parent §3.)

---

## §7 — Honest doubts (F2 RF on this decomposition)

The places this decomposition is least confident.

**7.1 — Cycle 1 diff-classifier is the load-bearing risk.** AC.PRSG.3 (`(touched_acs, untouched, novel)`) is the linchpin of per-band gating. If the classifier under-identifies touched ACs (false negatives), the gate misses regressions; if it over-identifies (false positives), the gate is noisy and gets ignored. The classifier reads the v0.1.8 contract's `Evidence` block (file paths + line numbers + symbol names) and matches against the diff's touched lines. The matching is line-and-symbol-level — straightforward when the diff is small + localized; harder when the diff is a large refactor that moves code without changing AC-relevant behaviour. *Mitigation:* Cycle 1 plan-doc names the classifier's heuristic explicitly (line-overlap or symbol-overlap or both); Cycle 1 smoke exercises both small-diff and refactor-shaped synthetic diffs. If classifier accuracy is below ~90% on the synthetic test set, halt-and-surface for a stronger heuristic (e.g., AST-aware symbol-graph matching using the existing tree-sitter integration from v0.1.8 Cycle 3+4a).

**7.2 — The 3-band × 3-action decision matrix has corner cases that aren't enumerated yet.** The matrix is "VERIFIED touched → HARD-BLOCK; PLAUSIBLE → SURFACE-DECISION; HYPOTHESISED → DOCS-ONLY; novel → SURFACE-DECISION." But what about a single diff that touches a VERIFIED AC AND introduces a novel candidate? Both surfaces fire; ordering matters. *Mitigation:* Cycle 1 plan-doc enumerates the 3-band × {touched, novel} combinations explicitly (~6 cells) plus the order-of-surface rule (HARD-BLOCK pre-empts SURFACE-DECISION pre-empts DOCS-ONLY). Decision-matrix coverage tests pin every cell.

**7.3 — Override workflow's `contract-update:` commit-prefix convention may collide with other tooling.** Tools like commitizen / conventional-commits use prefixes like `feat:`, `fix:`, `chore:`. `contract-update:` is a custom prefix; if an Eric-team uses commitizen with strict-prefix-validation, the custom prefix may be rejected at commit-time. *Mitigation:* Cycle 1 plan-doc names alternative recognition mechanisms (commit trailer `Loam-Override: <rationale>`; commit-message prefix; `--override` flag at gate-invocation time). Cycle 1 plan-author chooses one + documents the rationale; trailer-based recognition is the most-compatible with conventional-commits.

**7.4 — Three CI templates may not cover Eric's actual CI provider.** GitHub Actions / GitLab CI / CircleCI cover the three most common per Eric synthesis §2 v0.1.9 reasoning. But Eric's company uses what? Possibilities not covered: BitBucket Pipelines, Jenkins, Buildkite, Drone, GitHub Enterprise's older CI surface. *Mitigation:* the templates share rendering plumbing; adding a fourth template post-v0.1.9 is a v0.2.x-shaped follow-on. Decision S (Eric pre-call) would surface this — recommend asking Eric his CI provider as part of v0.1.9-or-v0.2.0 prep. Until then, three is the right scope.

**7.5 — Husky detection (Cycle 2 §6.2 surface) may not cover all hook-management conventions.** husky is the most-common JS/TS hook manager but `pre-commit` (Python tool), `lefthook`, `git-hooks-go` are alternatives. *Mitigation:* Cycle 2 plan-doc surfaces husky as the explicit case (most-likely Eric-relevant); other managers fall through to "halt on conflict" + PM-mediated decision. Edge cases ship to FIDRAFT post-Cycle 2.

**7.6 — PR description template may overflow GitHub's body-character limit on contracts with many touched ACs.** A diff that touches dozens of PLAUSIBLE ACs produces a PR description with provenance for each — the body could exceed GitHub's 65,536-char limit. *Mitigation:* Cycle 2 plan-doc names a body-overflow strategy (truncate per-AC provenance to ~200 chars per entry; link to the full audit-log file in the workspace). The template's render path is parameterized by max-length; the install-time configuration sets the surface-specific limit.

**7.7 — Six SKILLs in Cycle 3 may include lower-leverage entries than first-pass.** Layered-skills §5 ranked by AI-time + dependency, but the first-pass at v0.1.8 took the highest-leverage six (loam-amend-cycle, dispatch-brief-authoring, plan-before-code-author, fidraft-capture, front-load-principle-walk, audit-finding-triage). Some second-pass SKILLs may have lower fire-rate (e.g., `component-scaffold-author` — NEW components are rare; `loam-amend-status-quick` — operators rarely query status interactively). *Mitigation:* Cycle 3 plan-doc explicitly re-evaluates leverage after Cycles 1+2 reveal scope; if a SKILL is clearly redundant or low-value, surface for swap or drop (don't silently swap; never drop without naming the swap). The full-12 commitment per parent §2 means the answer is most-likely "ship as-named, even at varying fire-rates."

**7.8 — Audit-allowlist cleanup is small but verification-heavy.** The four-line edit is trivial; verifying that the four removed entries are genuinely-stale (and that the remaining one is genuinely-pending-debt) is the work. The pre-flight in §2 verified empirically (zero source-file matches for the four; one match for the remaining), but the verification may shift between plan-author time (now) and Cycle 3 build-time. *Mitigation:* Cycle 3 dispatch brief halt-trigger: if `test_AC_F3_always_loaded_no_dev_refs` fails post-edit, halt + RF (the failure says either I removed an entry that's still in source, or a new cross-mode reference appeared since pre-flight).

**7.9 — Quality-bar absorption (20%) may be too low for v0.1.9 Cycle 1.** Cycle 1 is the highest-risk single cycle (NEW component, per-band gating, override workflow, production-stake integration). 20% absorption baked in; if Cycle 1 hits 12+ h actual (above the 6–10 h band's high end), the master plan's 15–28 h band is wrong. *Mitigation:* log actuals after Cycle 1 per `feedback_duration_estimation_rubric`; recalibrate before Cycle 2 commits. Cycle 1's halt-trigger at ~5 h wall-clock forces an early split surface.

---

## §8 — Provenance trail

- **Master plan source authority:** `docs/rebuild/plans/eric-final-delivery-plan-2026-05-04.md` §2 v0.1.9 row + Decisions I (PLAUSIBLE→VERIFIED default-no) + P (SOC-2 floor) + Q (one-question-at-a-time) + R (HARD/SOFT smoke gate cadence).
- **Layered-skills second-pass list:** `docs/rebuild/plans/layered-skill-story-research-2026-05-04.md` §5 (12 candidates; second-pass list at lines 506–511).
- **v0.1.8 master plan precedent (cycle-decomposition pattern + per-cycle dispatch-brief shape):** `docs/rebuild/plans/v0-1-8-master-plan.md` (sealed at `1c2c478`).
- **v0.1.8 sealed cycles (predecessors):** Cycle 1 `c1abda1` / Cycle 2 `4865028` / Cycle 3 `6711dd7` / Cycle 4a `67dd302` / Cycle 4b `c648cf9` / Cycle 5 `e4512b9`. Local release sealed at `9b64cd4`.
- **v0.1.7 sealed cycles (load-bearing PM API + layered-skill mechanism):** Cycle 1 `3aa20dd` / Cycle 2 `73505f0` / Cycle 3 `bcf699a` / Cycle 4 `122a7c8`.
- **v0.1.6 sealed cycles (production-safety + cost-governance + base-skills bug-fixes):** Cycle 1 `3f1d237` / Cycle 2 `88674cb`.
- **M-FBM operational health amendment (cross-session continuity):** `1a1f830`.
- **FIDRAFT graduate (audit-allowlist drift):** `docs/rebuild/FUTURE_IDEAS_DRAFT.md` line 143 (entry captured 2026-05-04 during v0.1.8 Cycle 5 release-level smoke).
- **Empirical verification of allowlist staleness (this dispatch's pre-flight):** grep against the 4 (source, target) pairs returned 0 matches; the 5th pair (memory-system entry) returned a match, confirmed valid pending-debt.
- **Quality bar (Luke directive 2026-05-04):** parent §1 verbatim + parent §3 Decision R framing.
- **Smoke-test discipline:** `plugins/dev-sdlc/docs/smoke-test-discipline.md` (six-dimension spec; SOFT-gate framing per Decision R; quality-bar-non-negotiable still applies).
- **Schema v3 + seal-narrative compression:** dev-pattern-simplifications-1 sealed at `019cfca`; dev-pattern-simplifications-2 sealed at `df3f50f`.
- **Lens 5 (swarming) reference + stopping criterion:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_swarming_recursive_decomposition.md` + framework/CLAUDE.md Lens 5.
- **Eric stack context (Rails, JS/TS/Playwright, SOC 2):** parent §1 + parent §3 Decisions P + Q + cycle 4 reroute (Telegram messages 10009 / 10011 / 10013, 2026-05-04).
- **AI-time rubric:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_duration_estimation_rubric.md` (wall-clock minutes ≈ tool_calls × 0.1–0.15).

---

## §9 — Method-decision register (per-cycle SHA backfill table)

(Reserved; build agents backfill on cycle-seal.)

| Cycle | Status | Apply SHA | Seal SHA | Notes |
|---|---|---|---|---|
| Cycle 1 — PR-safety gate engine + override workflow | SHIPPED | `136adc6` | `790807d` | NEW component `plugins/dev-sdlc/pr-safety/`. Per-band gating engine (3-band × 4-shape × 3-profile decision matrix; 13 cells + 6 mixed-touch pre-emption rules); override-commit recognition (`Loam-Override:` trailer + `contract-update:` prefix + `--override` flag); CLI `loam pr-safety gate`; SOC-2 audit-log; production-stake integration; classifier accuracy 100% on synthetic test set. Plan-doc `3d5f52d`; source-edit `bb592fa`; apply `136adc6`; seal `790807d`; §14 backfill `2f154c8`. AC.PRSG.1..9 satisfied; 105 cycle tests + 392 odd-extractor tests = 497 green; 719 in extended sweep. |
| Cycle 2 — Hook installers + CI templates + PR description template | SHIPPED | `68859d9` | `0dc557e` | Single-component fence on `plugins/dev-sdlc/pr-safety/`. Pre-commit + pre-push installers (idempotent + husky-aware + halt-on-conflict; sentinel-comment detection; LOAM_PR_SAFETY_BYPASS env var honoured under dev/research only); 3 CI templates (GitHub Actions separate file + GitLab CI / CircleCI sentinel-block-delimited); provenance-traceable PR description template (5 sections; 60K-char overflow truncation); `loam pr-safety install <surface>` + `install all`; `loam pr-safety hook-fire` dispatcher; `loam pr-safety gate --render-pr-description` flag. Plan-doc `48a4758`; source-edit `17d02ca`; apply `68859d9`; seal `0dc557e`; §14 backfill `a61d4ff`. AC.PRSI.1..10 satisfied; 78 new Cycle 2 tests + 105 inherited Cycle 1 tests = 183 green; all 6 smoke dimensions exercised. |
| Cycle 3 — 6 dev-sdlc SKILLs second pass + audit-allowlist cleanup | (planned) | — | — | Single-component fence on `plugins/dev-sdlc/`. Six SKILL.md packages (`seal-narrative-writer`, `plan-docs-author`, `hook-violation-recovery`, `component-scaffold-author`, `graceful-fallthrough-with-detection`, `loam-amend-status-quick`); 4-line `KNOWN_CROSS_MODE_DEBT` shrink; FIDRAFT line 143 closes. |
| **v0.1.9 release** | (planned) | — | tag SHA TBD | SOFT smoke gate per Decision R; quality-bar-non-negotiable applies. |

---
