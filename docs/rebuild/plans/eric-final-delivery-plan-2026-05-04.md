# Eric final delivery plan — synthesis (v0.1.6 → Eric-deliverable)

**Status:** synthesis plan-doc, plan-before-code. Authored 2026-05-04 (Sonnet redispatch #3).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/rebuild/plans/v0-1-x-roadmap.md` (extends past v0.1.5 horizon).
**Companion research (load-bearing):**
- `docs/rebuild/plans/eric-saas-app-use-case-version-sequence-2026-05-04.md` (Eric path)
- `docs/rebuild/plans/layered-skill-story-research-2026-05-04.md` (skills path)

**Quality bar (Luke directive 2026-05-04):** *"I'm thinking about getting into business with Eric. I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."* Every release-note promise corresponds to tested + reliable behavior. All 6 smoke-test dimensions exercised, not just cold-state. Onboarding ritual is polished. Bar adds 20–30% to AI-time bands per release for production-polish.

**Eric's stack (load-bearing context):** Ruby on Rails. Compliance: SOC 2 (company-wide; no product-specific compliance). Onboarding default: ONE QUESTION AT A TIME (Eric explicitly hates question-bombing).

---

## Principles applied this turn

- CHANNEL — replies go to dispatcher (not Telegram from this dispatch context).
- AUTONOMY — settle decisions; only escalate genuinely-critical / public-action / financial.
- F2 RUTHLESS FEEDBACK — quality bar applied as F2 against the synthesis itself (§6 doubts).
- LOCKED-DESIGN-NOT-LICENSE — Eric plan + layered-skills plan revisitable; revisited at §2 (interleave; Rails adders; quality-bar absorption).
- PROMISES > IN-MOMENT JUDGMENT — quality bar IS Luke's promise to Eric.
- ODD §2.5 — every line maps to named source (cited inline).
- OUTPUT-TO-DISK — synthesis is this file; reply inline-summarises.
- DURABLE-CAPTURE — synthesis IS the durable surface.
- WD-IN-DISPATCHES — confirmed at start.
- TRANSLATION RULE — §1 readable without loam internals.
- PARTITION RULE — every artefact placed.
- THREE-TIER GATING — auto-creation universal; promotion-to-plugin plugin-dev-only; promotion-to-base loam-dev-only.

---

## §1 — Executive summary

The path to Eric-ready ships in **six interleaved releases (v0.1.6 → v0.2.1)** that combine the Eric-specific safety + extractor + PR-gate work with the layered-skills work into a single coherent cadence. Combined AI-time band: **52–96 hours** (midpoint ~74 hours), with quality-bar absorption (+20–30% for production-polish) and a Rails-aware adder of +8–16 h on the v0.1.8 extractor release. Luke + Eric review time: 6–12 hours across ~15 touchpoints.

**Why interleave (not two parallel sequences).** The Eric research and the layered-skills research both number themselves v0.1.6→v0.2.1. Running them as parallel cadences creates duplicate ceremony, collision on version numbers, and confusion about gates. Interleaving lets each release ship a small Eric-shielding capability + a small skills-shape capability together — the bundles compose (e.g., subagent personas in v0.1.7 directly use the dev-sdlc SKILLs from v0.1.7's mechanism; the auto-creation mechanism in v0.2.0 captures Eric-specific patterns from real use).

**The release-by-release shape:**

1. **v0.1.6** — Production-safety mode + 3 base-skills additions. Defensive shield ships first.
2. **v0.1.7** — Subagent personas + per-project PM + decision-surfacing + layered-skill architecture mechanism. Coordination machinery off the persona's user-visible surface.
3. **v0.1.8** — ODD reverse-engineering (heavy) + confidence bands + Ruby-first-class extractor + dev-sdlc skill-ification first pass (6 SKILLs). The headline release.
4. **v0.1.9** — PR-safety gate + provenance-traceable PR template + dev-sdlc skill-ification second pass (6 SKILLs).
5. **v0.2.0** — Continuous codebase-watch + auto-creation mechanism (universal).
6. **v0.2.1** — Eric-deliverable smoke + onboarding hardening + promotion rubric mechanism. Eric installs.

**Open for Luke (5 escalations — see §3 for detail):** the Rails-first-class extractor scope expansion (Decision O); the SOC-2 audit-trail floor as a hard production-safety constraint (Decision P); the one-question-at-a-time onboarding ritual structural enforcement (Decision Q); the v0.1.6 quality-bar gate (smoke against canonical pos-v2 with full 6-dimension coverage before v0.1.7 builds, Decision R); the Eric-domain pre-call recommendation (Decision S — recommend a 30-min call with Eric BEFORE v0.1.6 builds to lock his Rails app's compliance/domain shape).

**The gate to ship.** v0.2.1 ships when end-to-end smoke passes against an open-source Rails-payment-shape OSS repo, the onboarding ritual is sealed and tested under realistic conditions (full 6 smoke dimensions), and every promised feature is fully delivered with test-coverage at the production-polish bar. No partial features. No "almost there." Eric installs and the experience matches the promise.

---

## §2 — Final combined version sequence

Each release below: theme, concrete bundle (with placement), AI-time band (quality-bar absorbed), dependencies + gate, quality-bar audit, Eric-specific enables.

### v0.1.6 — Production-safety mode + base-skills additions

**Theme.** Defensive shield ships first. Three base-tier SKILLs land alongside.

**Bundle:**

| Item | Source | Placement |
|---|---|---|
| `safety_profile: production-stake \| dev \| research` config | Eric G3 | `framework/workspace-bootstrap/` |
| Default-flipping logic (production-stake activates halt-on-push, etc.) | Eric G3 | `framework/` core + `plugins/dev-sdlc/` dev-defaults |
| Cost-governance recalibration + foreign-codebase budget envelope | Eric G7 | `framework/cost-governance/` |
| Dry-run mode primitive | Eric G7 | `framework/cost-governance/` (general primitive) |
| `translation-discipline` SKILL | layered-skills v0.1.6 | `plugins/loam-skills/skills/translation-discipline/` |
| `audit-block-on-telegram` SKILL | layered-skills v0.1.6 | `plugins/loam-skills/skills/audit-block-on-telegram/` |
| `owner-decision-summary` SKILL | layered-skills v0.1.6 | `plugins/loam-skills/skills/owner-decision-summary/` |
| **BUG FIX:** enroll `plugins/loam-skills/` in `bootstrap.yaml` `contributions:` | layered-skills §1.3 | `framework/workspace-bootstrap/` |
| **BUG FIX:** workspace-bootstrap pre-creates `<workspace>/.claude/skills/.gitkeep` | layered-skills Decision B | `framework/workspace-bootstrap/` |

**AI-time:** **9–15 h** (Eric base 6–10 h + skills base 3–5 h, +20% quality-bar absorption already in band). Two amendment cycles (production-safety on `framework/cost-governance` + `framework/workspace-bootstrap`; skills additions on `plugins/loam-skills/`). Serialise per `feedback_serialize_amendment_builds`.

**Dependencies:** None (independent of all later versions).

**Gate to v0.1.7:**
- Production-stake profile observable in canonical pos-v2 sessions.
- Cost-governance dry-run mode functional.
- All 5 v0.1.3 loam-skills (the f04e925 bundle) AND the 3 new skills auto-discovered in canonical pos-v2 (live `/` menu shows them) — fixes the v0.1.0-shipper-tripping bug.
- 6-dimension smoke of production-safety against canonical: cold-state ✓, steady-state ✓, restart ✓, reboot ✓, cross-session ✓, telemetry-floor ✓.

**Quality-bar audit:** Production-safety profile + dry-run + cost-governance recalibration are all scoped to ship complete. Three SKILLs are full SKILL.md packages with tests. Bug-fix items close known-broken behavior. **No partial features.** ✓

**Enables for Eric SPECIFICALLY:**
- Defensive shield in place BEFORE Eric-shaped capabilities ship; Rails-aware production-stake mode active during all v0.1.7+ canonical testing.
- SOC 2 audit-trail floor satisfied via the cost-governance + dry-run audit (every Eric-pointed dispatch has a budget estimate + post-run actuals recorded).
- The 3 base SKILLs are persona-discipline shaping that benefits Eric's primary-persona on day 1.

### v0.1.7 — Subagent personas + PM persona + layered-skill architecture mechanism

**Theme.** Coordination machinery off the persona's user-visible surface. Layered-skill architecture lands. Per-project PM ships.

**Bundle:**

| Item | Source | Placement |
|---|---|---|
| 5 subagent personas (`loam-builder`, `loam-plan-author`, `loam-researcher`, `loam-reviewer`, `loam-documenter`) | Eric G4 | `plugins/dev-sdlc/agents/` (source) → `<workspace>/.claude/agents/` (symlink at bootstrap) |
| Subagent registration mechanism | Eric G4 | `framework/workspace-bootstrap/` |
| Per-project PM-shape (loader, contract, registry) | Eric G5 | `framework/per-project-pm/` (new component) |
| Decision-surfacing PM discipline (design-note + persona prompt) | Eric G11 | `framework/per-project-pm/` |
| `plugins/loam-skills/` admitted to `dev-mode-manifest.yaml` | layered-skills v0.1.7 | `plugins/dev-sdlc/dev-mode-manifest.yaml` |
| Layered-skill architecture design-note | layered-skills v0.1.7 | `docs/design/layered-skill-architecture.md` |

**AI-time:** **22–34 h** (Eric base 16–24 h + skills mechanism 4–6 h, +20% quality-bar absorption). Three amendment cycles serial: framework/workspace-bootstrap, plugins/dev-sdlc, framework/per-project-pm (new component build). PM-shape is a NEW component-shape addition — research-grade plan-doc required before build per `feedback_research_before_plan`.

**Dependencies:** v0.1.6 (production-safety profile checked by subagents; skills enrollment in bootstrap.yaml).

**Gate to v0.1.8:**
- Subagent personas dispatchable from primary persona; halt-and-surface defaults respect production-stake profile.
- PM persona seedable in a workspace (smoke-test: `loam pm init eric-saas-pm` in canonical works).
- Primary persona's user-facing channel volume returns to translation-shape (per value-prop audit's success criterion).
- Layered-skill architecture: workspace-local skill discoverable end-to-end in canonical pos-v2 (smoke: create `<workspace>/.claude/skills/test-discovery/SKILL.md`, verify it appears in `/` menu without restart).
- 6-dimension smoke on PM persona + subagent dispatch.

**Quality-bar audit:** PM is a NEW component shape — risk surface. Scope explicitly includes design-note before build, smoke under realistic conditions (pos3 workspace), AND a halt-trigger if PM-shape proves wrong before build (split into v0.1.7.a/v0.1.7.b). Subagent personas are 5 persona definitions — each is a complete, tested artefact. **No partial features.** ✓

**Enables for Eric SPECIFICALLY:**
- PM absorbs project state for Eric's Rails app — every ratification decision surfaces through PM, not the primary persona's working memory.
- Subagent-fork lets the extractor (v0.1.8) decompose work without the primary persona's context bloat.
- Decision-surfacing discipline is the SOC-2-compliant audit shape: every Eric-decision is logged via PM's surfacing mechanism, not chat-buried.
- One-question-at-a-time onboarding (Decision Q) is enforced through the PM's surfacing protocol — PM batches questions, then surfaces in single-question form when Eric is in interaction mode.

### v0.1.8 — ODD reverse-engineering (heavy) + dev-sdlc skill-ification pass 1

**Theme.** The headline release. Loam reads Eric's Rails SaaS and produces a confidence-banded contract draft. Six high-leverage dev-sdlc SKILLs ship.

**Bundle:**

| Item | Source | Placement |
|---|---|---|
| `plugins/dev-sdlc/odd-extractor/` Cartographer-style heavy version | Eric G1 | `plugins/dev-sdlc/odd-extractor/` |
| Confidence-banded contract authoring (VERIFIED / PLAUSIBLE / HYPOTHESISED) | Eric G6 | `plugins/dev-sdlc/odd-extractor/` schema + `plugins/dev-sdlc/docs/odd-methodology.md` extension |
| Language-agnostic skeleton + Python first-class | Eric G9 | `plugins/dev-sdlc/odd-extractor/lang/` |
| **Ruby-first-class adapter** (NEW per Decision O) | Eric Rails-adder | `plugins/dev-sdlc/odd-extractor/lang/ruby/` |
| Test-first extraction priority (every test → VERIFIED AC) | Eric G1 | `plugins/dev-sdlc/odd-extractor/` |
| Eric-ratification workflow | Eric G1 | `plugins/dev-sdlc/odd-extractor/ratification/` + `framework/per-project-pm/` |
| `loam-amend-cycle` SKILL | layered-skills v0.1.8 | `plugins/dev-sdlc/skills/loam-amend-cycle/` |
| `dispatch-brief-authoring` SKILL | layered-skills v0.1.8 | `plugins/dev-sdlc/skills/dispatch-brief-authoring/` |
| `plan-before-code-author` SKILL | layered-skills v0.1.8 | `plugins/dev-sdlc/skills/plan-before-code-author/` |
| `fidraft-capture` SKILL | layered-skills v0.1.8 | `plugins/dev-sdlc/skills/fidraft-capture/` |
| `front-load-principle-walk` SKILL | layered-skills v0.1.8 | `plugins/dev-sdlc/skills/front-load-principle-walk/` |
| `audit-finding-triage` SKILL | layered-skills v0.1.8 | `plugins/dev-sdlc/skills/audit-finding-triage/` |
| Smoke fixtures (Python-Flask-payment AND Ruby-Rails-payment) | Eric §6 + Decision O | `plugins/dev-sdlc/odd-extractor/tests/fixtures/` |

**AI-time:** **42–66 h** (Eric base 24–40 h + skills 8–12 h + Rails-first-class adder +8–16 h, +20% quality-bar absorption). Highest-risk release.

**Dependencies:** v0.1.6 (safety + cost-governance), v0.1.7 (subagents + PM coordinate the extraction; M-FBM operational health from amendment #125 is load-bearing for cross-session per-codebase state).

**Gate to v0.1.9:**
- Extractor produces a confidence-banded contract draft against BOTH Python-Flask AND Ruby-Rails fixtures.
- Dry-run cost estimate observable; Eric-ratification workflow runs end-to-end on both fixtures.
- Test-first priority enforced (no PLAUSIBLE→VERIFIED promotion without a passing test pinned).
- 6-dimension smoke on the extractor itself: cold-state ✓, steady-state ✓ (incremental run on fixtures), restart ✓, reboot ✓, cross-session ✓ (resume after `/clear`), telemetry-floor ✓ (per-extraction-run audit log).
- 6 dev-sdlc SKILLs discoverable + invokable in canonical pos-v2 (live `/` menu shows them).

**Quality-bar audit:** Highest-risk release. The extractor must be COMPLETE — not "Python works, Ruby is a thin fallback." Decision O ships Ruby-first-class. The 6 SKILLs are each full SKILL.md packages with tests. Smoke under realistic conditions covers ALL 6 dimensions. **The risk:** if v0.1.8 stretches to 60+ hours (Eric §11.5 doubt), the response is to split into v0.1.8.a (read-only extractor) + v0.1.8.b (full with confidence-bands) — NOT to ship a partial v0.1.8. **No partial features.** ✓

**Enables for Eric SPECIFICALLY:**
- Loam reads his Rails codebase and produces a Ruby-AST-aware contract draft (not a thin grep-fallback).
- Confidence bands surface ambiguity to Eric for ratification rather than fabricating ACs.
- Test-first means existing Rails specs become the contract anchor (high-confidence VERIFIED ACs from the start).
- 6 SKILLs make the loam dev-rituals more self-evident to Eric as he learns the surface.
- SOC 2 audit-trail floor: every PLAUSIBLE→VERIFIED ratification is logged (production-stake mode default-to-no per Decision I).

### v0.1.9 — PR-safety gate + dev-sdlc skill-ification pass 2

**Theme.** Contract enforcement at PR-time. Six more dev-sdlc SKILLs ship.

**Bundle:**

| Item | Source | Placement |
|---|---|---|
| Pre-commit hook installer | Eric G2 | `plugins/dev-sdlc/pr-safety/installers/` |
| Pre-push hook installer | Eric G2 | `plugins/dev-sdlc/pr-safety/installers/` |
| CI status-check templates (GitHub Actions, GitLab CI, CircleCI) | Eric G2 | `plugins/dev-sdlc/pr-safety/templates/ci/` |
| Provenance-traceable PR description template | Eric G8 | `plugins/dev-sdlc/pr-safety/templates/pr/` |
| Override workflow (contract-update commit shape) | Eric G2 | `plugins/dev-sdlc/pr-safety/` |
| Per-band gating (VERIFIED hard-gate; PLAUSIBLE informs; HYPOTHESISED docs-only) | Eric G6 | `plugins/dev-sdlc/pr-safety/` |
| `seal-narrative-writer` SKILL | layered-skills v0.1.9 | `plugins/dev-sdlc/skills/seal-narrative-writer/` |
| `plan-docs-author` SKILL | layered-skills v0.1.9 | `plugins/dev-sdlc/skills/plan-docs-author/` |
| `hook-violation-recovery` SKILL | layered-skills v0.1.9 | `plugins/dev-sdlc/skills/hook-violation-recovery/` |
| `component-scaffold-author` SKILL | layered-skills v0.1.9 | `plugins/dev-sdlc/skills/component-scaffold-author/` |
| `graceful-fallthrough-with-detection` SKILL | layered-skills v0.1.9 | `plugins/dev-sdlc/skills/graceful-fallthrough-with-detection/` |
| `loam-amend-status-quick` SKILL | layered-skills v0.1.9 | `plugins/dev-sdlc/skills/loam-amend-status-quick/` |

**AI-time:** **15–28 h** (Eric base 10–18 h + skills 5–10 h, +20% quality-bar absorption).

**Dependencies:** v0.1.8 (extractor produces the contract surface the gate enforces against).

**Gate to v0.2.0:**
- Gate runs in canonical against fixture repos (Python-Flask + Ruby-Rails).
- Pre-commit hook + pre-push hook + GitHub Actions CI template all functional end-to-end.
- Override workflow tested (Eric-overrides → contract-update commit → CI re-runs).
- PR description template auto-populated from contract + dispatch trail.
- Production-safety profile integration: gate respects production-stake mode (no auto-merge; Eric ratifies).
- 6-dimension smoke on the gate itself.
- 6 SKILLs discoverable + invokable.

**Quality-bar audit:** Three CI templates (GitHub Actions, GitLab CI, CircleCI) is the production-polish move — Eric's company's CI provider is unknown; ship for the three most common. The gate must produce CLEAN structured PR comments — not raw diffs. Override workflow is fully documented and tested. SOC-2 floor: every override is auditable. **No partial features.** ✓

**Enables for Eric SPECIFICALLY:**
- Every Eric-team PR (loam-authored or human-authored) gates against the contract.
- Provenance trail is automatic — Eric's reviewers see "this changes AC.X.Y, ratified Eric 2026-MM-DD."
- Override workflow is the social-acceptance escape hatch (Eric §11.6 risk mitigation).
- SOC-2 audit-trail floor: every gate decision (pass/fail/override) is logged.

### v0.2.0 — Continuous codebase-watch + auto-creation mechanism

**Theme.** Contract stays alive as Eric's Rails app evolves. Loam captures Eric-specific patterns into workspace-local skills.

**Bundle:**

| Item | Source | Placement |
|---|---|---|
| Continuous codebase-watch (extractor incremental mode) | Eric G10 | `plugins/dev-sdlc/odd-extractor/` |
| Scheduling integration (composes with sealed `framework/scope-of-work/`) | Eric G10 | `framework/scope-of-work/` integration |
| PM ratification-queue mechanics | Eric G10 | `framework/per-project-pm/` |
| Domain-batched AC surfacing (payment-handling / accounting / etc.) | Eric G10 | `framework/per-project-pm/` |
| `skill-capture-proposal` SKILL (auto-creation MVP per Decision N) | layered-skills v0.2.0 | `plugins/loam-skills/skills/skill-capture-proposal/` |
| `enable_auto_skill_capture` workspace-config flag | layered-skills v0.2.0 | `framework/workspace-bootstrap/` |
| Trigger detection (3 signals MVP: explicit-request + ask-and-answer + repeat-pattern) | layered-skills v0.2.0 | `plugins/loam-skills/skills/skill-capture-proposal/` |
| Persona-driven-skill-capture design-note | layered-skills v0.2.0 | `docs/design/persona-driven-skill-capture.md` |

**AI-time:** **14–24 h** (Eric base 6–10 h + skills 6–10 h + auto-creation MVP scope reduction net, +20% quality-bar absorption).

**Dependencies:** v0.1.8 (extractor full), v0.1.9 (gate consumes incremental contract updates).

**Gate to v0.2.1:**
- Watch runs in canonical against fixtures; surfaces newly-introduced contract-shape changes.
- PM queue observable; Eric-ratification batch workflow tested.
- Auto-creation MVP: pos3 captures one workspace-local skill end-to-end (proposal → user-edit → SKILL.md materialised at `<workspace>/.claude/skills/`).
- 6-dimension smoke on watch + auto-creation.

**Quality-bar audit:** Auto-creation MVP scope is intentional (3 triggers, not 6). Watch incremental mode is full — not "watches but doesn't re-extract." Domain-batched AC surfacing uses the PM. **No partial features.** ✓

**Enables for Eric SPECIFICALLY:**
- Six-month-out: Eric's Rails-app contract stays in sync with code.
- Eric's Rails-specific patterns (e.g., "this Rails concern always pairs with a service object") become workspace-local SKILLs that loam invokes automatically.
- Eric's domain-specific ratification batches (payment-handling / accounting / Rails-callback-discipline) surface at sane cadence.

### v0.2.1 — Eric-deliverable smoke + onboarding hardening + promotion rubric

**Theme.** The release Eric installs.

**Bundle:**

| Item | Source | Placement |
|---|---|---|
| Onboarding ritual sealed | Eric §6.2 | `framework/workspace-bootstrap/` + `plugins/dev-sdlc/` |
| One-question-at-a-time enforcement (per Decision Q) | Eric §6 | `framework/per-project-pm/` (PM mediates question batching) |
| Eric-facing install docs (general + production-stake) | Eric §6.2 | `docs/getting-started.md` + `docs/dev-mode-getting-started.md` |
| Live OSS smoke pass against Rails-payment-shape repo | Eric §6.2 | `plugins/dev-sdlc/odd-extractor/tests/integration/` |
| Telegram (or Eric-chosen channel) integration | Eric §6.2 | `framework/telegram-interface/` integration |
| `skill-promotion-review` SKILL (3-signal MVP per Decision L) | layered-skills v0.2.1 | `plugins/dev-sdlc/skills/skill-promotion-review/` |
| Quarterly-review trigger | layered-skills v0.2.1 | `framework/scope-of-work/` integration |

**AI-time:** **12–22 h** (Eric base 8–14 h + skills promotion-rubric 4–8 h, +20% quality-bar absorption).

**Dependencies:** All prior versions.

**Gate to Eric installation:**
- End-to-end smoke passes on a real OSS Rails-payment-shape repo.
- Eric's first install replicates the documented onboarding ritual without surprise.
- All 6 smoke dimensions exercised on the full path (install → loam-init → connect-codebase → first-ratification → first-PR-gate → first-watch-cycle).
- One-question-at-a-time onboarding tested with a fresh user (not Luke) before Eric.
- Onboarding ritual feels intentional — first 5–10 minutes are polished.
- Documentation: install, first-pass, daily-usage, override-workflow, audit-trail — all written, all tested.

**Quality-bar audit:** This is the make-or-break release. Quality bar is 100% load-bearing. Live OSS smoke against an actual Rails-payment-shape repo (NOT Eric's real codebase yet — public OSS for shipping verification). Fresh-user test (anyone-but-Luke) before Eric installs. **No partial features.** Eric's first 5–10 minutes feel intentional. ✓

**Enables for Eric SPECIFICALLY:**
- Eric installs. End-of-path.
- Eric's onboarding asks ONE question at a time. He doesn't get question-bombed.
- Audit trail is SOC-2-compliant by default (every action logged; every decision surfaced; every override traceable).

### Summary table

| Release | Theme | AI-time | Quality-bar | Eric-gap closed |
|---|---|---|---|---|
| v0.1.6 | Production-safety + base-skills + 2 bug fixes | 9–15 h | ✓ all 6 dimensions | Defensive shield + skills bug fixed |
| v0.1.7 | Subagents + PM + layered-skill mechanism | 22–34 h | ✓ all 6 dimensions | Coordination off persona's surface |
| v0.1.8 | Extractor heavy + Ruby-first-class + 6 SKILLs | 42–66 h | ✓ all 6 dimensions | Contract derivation possible |
| v0.1.9 | PR-gate + 6 SKILLs | 15–28 h | ✓ all 6 dimensions | Contract enforcement |
| v0.2.0 | Codebase-watch + auto-creation MVP | 14–24 h | ✓ all 6 dimensions | Contract evolves; Eric patterns captured |
| v0.2.1 | Eric-smoke + onboarding + promotion rubric | 12–22 h | ✓ all 6 dimensions; fresh-user | Eric installs |
| **Total** | | **114–189 h** (midpoint ~152 h) | | |

(The total is higher than either source plan because the quality-bar absorption applies to BOTH Eric work AND skills work, the Rails-first-class adder lands at v0.1.8, and skill-ification is interleaved end-to-end.)

---

## §3 — All decisions resolved (24 decisions + audit-rule)

### Eric-research decisions A–I (per Eric §10)

| # | Question | Resolution | AUTONOMOUS / ESCALATED |
|---|---|---|---|
| A | V11.C in `plugins/dev-sdlc/odd-extractor/` (not `framework/`)? | **Confirm.** Extractor is dev-specific. Partition rule applies. | AUTONOMOUS |
| B | Six smaller releases vs three larger? | **Six smaller** (interleaved). Iterate-in-public; smaller blast-radius. | AUTONOMOUS |
| C | Subagents in `plugins/dev-sdlc/agents/` or `.claude/agents/`? | **Both:** source in `plugins/dev-sdlc/agents/`; symlink at workspace-bootstrap to `<workspace>/.claude/agents/`. Lens 1 + partition rule both satisfied. | AUTONOMOUS |
| D | First reverse-engineering pass: dry-run-default or live? | **Dry-run-default** with explicit `--live` flag. Production-stake stakes require opt-in for cost-runaway. | AUTONOMOUS |
| E | v0.2.2 buffer release? | **Pre-allocate** as bandwidth buffer. Prevents iterate-in-public temptation to keep adding to v0.2.1. | AUTONOMOUS |
| F | OSS smoke fixture: which repo? | **Two fixtures:** Python-Flask-payment (`tests/fixtures/python-flask-payment/`) AND Ruby-Rails-payment (`tests/fixtures/ruby-rails-payment/`) shipping at v0.1.8. Specific repo selection at plan-author time. | AUTONOMOUS |
| G | Production-safety mode at v0.1.6 (defensive first) or later? | **v0.1.6 first.** Defensive shield BEFORE sharp tools. | AUTONOMOUS |
| H | Per-project PM at v0.1.7 alongside subagents, or split? | **Bundle at v0.1.7.** Subagents without PM = coordination tokens flooding persona. | AUTONOMOUS |
| I | PLAUSIBLE→VERIFIED ratification: default-yes or default-no? | **Default-no.** Production-stake stakes require explicit ratification. SOC 2 audit-trail compatible. | AUTONOMOUS |

### Layered-skills decisions A–N (per layered-skills §8)

| # | Question | Resolution | AUTONOMOUS / ESCALATED |
|---|---|---|---|
| A | Enroll `plugins/loam-skills/` in `bootstrap.yaml`? | **Yes** at v0.1.6 (bug fix). | AUTONOMOUS |
| B | Pre-create `<workspace>/.claude/skills/.gitkeep`? | **Yes** at v0.1.6. | AUTONOMOUS |
| C | Auto-creation gating: workflow-flag or also dev-mode? | **Workflow-flag only**, default false. Auto-creation universal per Luke. | AUTONOMOUS (Luke pre-ruled) |
| D | Skill drafting: persona drafts full or fill-in-blanks? | **Mode 1** (persona drafts full) with "review carefully" framing. | AUTONOMOUS |
| E | Per-week proposal budget? | **3/week**, tunable. | AUTONOMOUS |
| F | Demotion path: amendment cycle? | **Yes**, explicit amendment cycle. | AUTONOMOUS |
| G | Promotion approval: owner-only? | **Owner-only**, default-to-no. | AUTONOMOUS |
| H | PM as auto-creation driver? | **Primary persona for now**; revisit when PM ships. | AUTONOMOUS |
| I | Workspace-local skill location? | **`<workspace>/.claude/skills/`** (Anthropic-native). | AUTONOMOUS |
| J | Reconcile sequences: renumber or interleave? | **Interleave** (this synthesis). | AUTONOMOUS |
| K | Workspace-local skill auto-prefix convention? | **Convention-suggested first**; structural-enforce only if collisions observed. | AUTONOMOUS |
| L | Promotion rubric: 6-signal or start with 3? | **Start with 3** (Categorization + Quality + Conflict) at v0.2.1. | AUTONOMOUS |
| M | Auto-creation: SKILL or feedback-file or both? | **Both options surfaced**; persona suggests default by pattern shape. | AUTONOMOUS |
| N | Auto-creation v0.2.0 scope: MVP or full? | **MVP** (3 triggers); layer in passive triggers + cool-down + budget at v0.2.x. | AUTONOMOUS |

### Synthesis-introduced decisions (resolved autonomously 2026-05-04)

These five decisions were introduced by the synthesis (quality bar + Rails + SOC 2 + onboarding). Originally escalated; re-tested against the operational objective ("deliver to Eric, high quality, ready to go") on 2026-05-04 by main session and ALL FIVE resolved autonomously per Luke's "answer questions you would have asked me by testing them against the operational objective" directive. Original recommendations preserved as resolutions; full reasoning intact below.

**Decision O — Ruby-first-class extractor at v0.1.8 (vs Ruby-fallback)?** RESOLVED YES.

- **Question.** Eric's app is Rails. Layered-skills/Eric research assumed Ruby fallback via grep+LLM. Quality bar says no half-measures. Ship Ruby first-class (AST-aware, dedicated extractor adapter) at v0.1.8?
- **Recommendation.** **Yes — Ruby first-class.** Adds +8–16 h to v0.1.8. Rails-aware codebase reading needs ActiveRecord migrations, callbacks, concerns, service objects, polymorphic associations, ActiveJob/Sidekiq. A Ruby-grep-fallback produces HYPOTHESISED-band-dominant contracts → thin gate → thin safety. Quality bar fails.
- **Reasoning.** F2 RF on the original Eric §11.3 doubt: a thin Ruby fallback DOES fail the quality bar. The choice is not "thin Ruby fallback" or "Eric waits"; it's "first-class Ruby in v0.1.8" or "Eric ships on a v0.1.8 that under-delivers his contract." Choose first-class.
- **Risk if wrong.** v0.1.8 expands to 50–80 h scope. Mitigation: Ruby-first-class adapter is bounded scope (parse Rails idioms, no orchestration); plan-author dispatch can split into v0.1.8.a (Python first-class + Ruby AST adapter) + v0.1.8.b (full Cartographer + bands) if 50+ hours surfaces.

**Decision P — SOC-2 audit-trail floor as a hard production-safety constraint?** RESOLVED YES (baked into v0.1.6 build dispatch).

- **Question.** Eric's company is SOC 2. The SOC-2 floor (audit trail, change management, no-bypass-of-access-controls) is an external constraint loam doesn't currently model. Should production-safety mode in v0.1.6 explicitly require: every dispatch logged, every decision surfaced via PM, every override auditable, no silent bypasses?
- **Recommendation.** **Yes — bake SOC-2 audit-trail floor into production-stake mode.** Specifically: (a) production-stake mode requires PM-mediated decisions (no chat-buried decisions); (b) override workflow at v0.1.9 produces an auditable commit trail; (c) silent-swallow patterns are halt-and-surface (not warn-and-continue) under production-stake.
- **Reasoning.** SOC 2 is the floor for ANY company-grade SaaS. Modeling it upfront avoids retrofitting. Cost: marginal — most of these are already implied by production-stake mode; making them explicit closes the SOC-2 gap.
- **Risk if wrong.** Eric's specific SOC-2 control set has stricter requirements (e.g., explicit attestation logs). Mitigation: §6 onboarding ritual asks Eric for his SOC-2 control deltas; v0.2.x can extend.

**Decision Q — One-question-at-a-time onboarding structurally enforced?** RESOLVED YES.

- **Question.** Luke confirmed one-question-at-a-time is the default for everyone (Eric especially hates question-bombing). Enforce structurally (PM-mediated, code-level) or convention-only?
- **Recommendation.** **Structurally enforced via PM** at v0.1.7 (PM batches questions, surfaces in single-question form). Onboarding ritual at v0.2.1 has a hard test: "user is asked exactly one question per turn during onboarding."
- **Reasoning.** Convention-only fails under load (the persona will batch questions when it's faster). Structural enforcement is reliability under realistic conditions per the quality bar.
- **Risk if wrong.** PM-mediation adds friction for non-onboarding-mode interactions. Mitigation: scoped to onboarding-mode + ratification batches; normal interaction unaffected.

**Decision R — v0.1.6 quality-bar gate: full 6-dimension smoke before v0.1.7 builds?** RESOLVED YES (HARD gate at v0.1.6 / v0.1.8 / v0.2.1; SOFT elsewhere).

- **Question.** Each release's gate-to-next includes a 6-dimension smoke. Is this a HARD gate (block v0.1.7 builds until v0.1.6 smoke is green) or a SOFT gate (build v0.1.7 in parallel; surface smoke failures)?
- **Recommendation.** **HARD gate** for the production-safety release (v0.1.6) and the headline release (v0.1.8 + v0.2.1). SOFT gate (parallel builds) for v0.1.7, v0.1.9, v0.2.0 where smoke regressions are bounded.
- **Reasoning.** Quality bar IS the hard gate at the load-bearing releases. Soft gate elsewhere keeps the cadence moving.
- **Risk if wrong.** Hard gate at v0.1.6 stretches v0.1.7 launch by ~1 day. Mitigation: smoke is parallelizable (background-agent dispatched per dimension); 1-day delay is the quality-bar cost.

**Decision S — 30-min Eric pre-call before v0.1.6 builds?** RESOLVED YES (recommendation; Luke schedules; not blocking v0.1.6 — recommended before v0.1.7 plan-author work where Eric domain-shape becomes load-bearing).

- **Question.** The Eric path makes assumptions about Rails / SOC 2 / onboarding shape. Recommend a short call with Eric BEFORE v0.1.6 builds to lock his actual context (specific Rails version, specific SOC-2 control set, his channel preference, his domain — Stripe-shape vs accounting vs marketplace).
- **Recommendation.** **Yes — recommend a 30-min Eric call.** Topics: (a) confirm Rails version + Ruby version; (b) confirm SOC-2 control set deltas; (c) confirm channel (Telegram vs Slack vs CLI); (d) confirm domain (payment / accounting / marketplace); (e) confirm onboarding cadence (30-min weekly review or async); (f) confirm authority bounds (read-only vs PR-authoring vs auto-merge ceiling).
- **Reasoning.** Eric §11.7 doubt about domain-shape is real. Front-loading the call de-risks v0.1.8/v0.2.1 by tens of hours.
- **Risk if wrong.** Eric isn't available; v0.1.6 launches on assumptions. Mitigation: ship v0.1.6 anyway (no Eric-specific code at v0.1.6); v0.1.7 PM-shape can absorb late Eric-input.

### Audit-rule refinement (load-bearing per dispatch)

**Resolution:** Per the synthesis brief — surface audit-block contents only when meaningful (✗ violations / decisions taken / commit boundary / Luke explicitly asks). Default-skip when nothing meaningful to surface (every principle ✓ N/A → skip the block; surface a one-line "all clear" if Luke prefers explicit). Captured for `audit-block-on-telegram` SKILL at v0.1.6.

---

## §4 — First-version build brief (v0.1.6)

The dispatch brief that launches the v0.1.6 build.

```
# v0.1.6 build dispatch — production-safety mode + base-skills additions + 2 bug fixes

Working directory: /Users/lukeivers/ivers-corp-pos-v2/ (canonical pos-v2). NOT pos3.

## Principles to apply at turn-start

- CHANNEL — replies route to dispatcher's stop-hook channel (NOT Telegram from this dispatch).
- AUTONOMY — settle decisions yourself; only flag genuinely-critical / public-action / financial.
- F2 RUTHLESS FEEDBACK — name disagreements / scope compromises / quality gaps immediately.
- LOCKED-DESIGN-NOT-LICENSE — synthesis decisions revisitable; surface counter-evidence.
- PROMISES > IN-MOMENT JUDGMENT — quality bar is non-negotiable.
- ODD §2.5 — every line of code/branch/test maps to a named AC.
- WD-IN-DISPATCHES — confirm at start.
- PARTITION RULE — every artefact goes to its placement per the synthesis §2 v0.1.6 table.
- THREE-TIER GATING — base-skills additions are loam-skills tier; auto-creation NOT in this release.
- PLAN-BEFORE-CODE — write `docs/rebuild/plans/v0-1-6-production-safety-and-base-skills.md` BEFORE code.
- POS-AMEND BOOKKEEPING — every component change uses `pos-amend apply` (NOT --amend).
- SCOPE-ONLY — this brief carries scope only; method (which files / which test names / commit prose) is yours.

## QUALITY BAR (load-bearing — Luke directive 2026-05-04)

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

- Every release-note promise corresponds to tested + reliable behavior.
- All 6 smoke-test dimensions exercised, not just cold-state.
- If any AC ships partial, halt and surface BEFORE proceeding.

## Sub-plan path

Author at: `docs/rebuild/plans/v0-1-6-production-safety-and-base-skills.md`
Manifest at: `docs/rebuild/plans/v0-1-6-production-safety-and-base-skills.manifest.yaml`
Status file: `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-6-status-2026-05-04.md`

## Fence

Two amendment cycles, serialized per `feedback_serialize_amendment_builds`:

### Cycle 1 — production-safety + bug fixes
- `framework/workspace-bootstrap/` (safety_profile config, contributions enrollment, .gitkeep pre-create)
- `framework/cost-governance/` (recalibration, dry-run primitive)
- `plugins/dev-sdlc/` (dev-specific safety defaults)

### Cycle 2 — base-skills additions
- `plugins/loam-skills/` (3 new SKILL.md packages)

## Acceptance criteria

Author the AC ladder during plan-doc time. Spec-level ACs to seed (you tighten + name in plan-doc):

**AC.PSAFE.* family (production-safety):**
- safety_profile config field accepted at workspace-bootstrap; valid values production-stake | dev | research
- production-stake profile flips named defaults (you enumerate in plan)
- cost-governance dry-run mode produces estimate before live execution
- foreign-codebase budget envelope schema present
- production-stake profile observable in canonical pos-v2 session

**AC.SKILLS-BASE.* family (3 new SKILLs):**
- translation-discipline SKILL.md authored, frontmatter valid, body covers anti-pattern checklist
- audit-block-on-telegram SKILL.md authored, surface-when-meaningful logic specified per Decision (audit-rule)
- owner-decision-summary SKILL.md authored, body covers summary + named-decisions-with-recommendations format
- All 3 + the existing 5 (f04e925) auto-discoverable in canonical pos-v2 (live `/` menu)

**AC.SKILLS-BUG.* family (bug fixes):**
- plugins/loam-skills/ enrolled in framework/workspace-bootstrap/.../bootstrap.yaml contributions
- Workspace-bootstrap pre-creates `<workspace>/.claude/skills/.gitkeep` at first-run
- Smoke: fresh canonical workspace → all 8 SKILLs visible without restart

## Smoke (REALISTIC CONDITION — all 6 dimensions per smoke-test-discipline.md)

- D1 cold-state: production-safety profile + 8 SKILLs functional from fresh canonical workspace
- D2 steady-state: profile remains active across 5 dispatches; no skill description-budget regression
- D3 restart: profile preserved across pos-v2 process restart; SKILLs remain discoverable
- D4 reboot: profile + SKILLs survive macOS reboot (or simulated equivalent)
- D5 cross-session: profile + SKILLs visible after `/clear` (cross-session continuity is THE ship-test per STATE.md)
- D6 telemetry-floor: cost-governance per-dispatch budget log entries observable

## Halt triggers

- WD drifts → halt + surface
- Plan-doc not authored before code → halt
- Any AC fails the partial-feature test (would ship partial) → halt + reframe
- 6-dimension smoke fails on D5 cross-session → halt (this is the ship-test)
- Any SKILL fails frontmatter validation → halt
- Production-safety profile breaks an existing AC.* test in canonical → halt + RF the conflict
- More than 5 in-build decisions need Luke escalation → halt + describe

## Model rationale

(none — Sonnet is the default for sealed-component amendment build.)

## Out of scope (FUTURE_IDEAS_DRAFT candidates if surfaced)

- Auto-creation mechanism (lands at v0.2.0)
- PM-shape work (lands at v0.1.7)
- Extractor work (lands at v0.1.8)
- 12 dev-sdlc skill-ifications (land at v0.1.8 + v0.1.9)

## Bookkeeping

- pos-amend apply on cycle 1 + cycle 2 (NOT --amend; create NEW commits if a file is missed).
- Single semantic commit message per cycle.
- Backfill `docs/rebuild/plans/v0-1-x-roadmap.md` §8 method-decision register row for v0.1.6.
- Backfill `docs/rebuild/plans/eric-final-delivery-plan-2026-05-04.md` §2 v0.1.6 table with apply + seal SHAs.
- DO NOT push tags until Luke gates the release.
```

---

## §5 — Open items for Luke (escalations)

Five items. Each: question + criticality reason. (See §3 for full reasoning.)

1. **Decision O — Ruby first-class at v0.1.8 (+8–16 h scope)?** *Criticality:* high. The headline release shipping a thin Ruby fallback fails the quality bar. Eric's app is Rails. Need ruling before v0.1.8 plan-author dispatch.
2. **Decision P — SOC-2 audit-trail floor baked into production-stake mode?** *Criticality:* high. Affects v0.1.6 scope. Bake-in early avoids retrofit.
3. **Decision Q — One-question-at-a-time structurally enforced via PM?** *Criticality:* medium. Affects v0.1.7 PM-shape. Convention-only fails the quality bar.
4. **Decision R — Hard 6-dimension smoke gate at v0.1.6 / v0.1.8 / v0.2.1?** *Criticality:* medium. Affects cadence. Hard gate at load-bearing releases is the quality-bar position; soft elsewhere keeps velocity.
5. **Decision S — 30-min Eric pre-call before v0.1.6?** *Criticality:* medium. De-risks v0.1.8/v0.2.1 assumptions. Async fallback if Eric unavailable; v0.1.6 isn't blocked.

---

## §6 — Honest doubts (F2 RF on the synthesis itself)

The places this synthesis is least confident.

**6.1 — The quality bar may still under-deliver on Eric's actual stakes.** Even with 6-dimension smoke + Ruby first-class + SOC-2 floor, the synthesis assumes Eric's company is Stripe-shape (payment-handling). If Eric is in a regulated space (PCI-DSS / HIPAA / specific state-level financial regs), production-stake mode's "audit-trail floor" is necessary-but-not-sufficient. **Mitigation:** Decision S (Eric pre-call) surfaces this; v0.2.1 onboarding asks Eric for his compliance specifics.

**6.2 — v0.1.8 is the load-bearing release and 42–66 h is optimistic at the high end.** §11.5 of the Eric research already named 24–40 h could push to 60+ h. With the Ruby first-class adder, the realistic high band is 70–80 h. The synthesis's 66 h ceiling may be wrong. **Mitigation:** v0.1.8 plan-author dispatch ships with explicit split-trigger: if scope estimate at plan-doc time exceeds 60 h, split into v0.1.8.a + v0.1.8.b.

**6.3 — The 12-SKILL skill-ification interleave (v0.1.8 + v0.1.9) competes for attention with the extractor + gate work in those releases.** Each dev-sdlc SKILL is ~1–2 h of dispatch + tests; the extractor is the expensive scope. Risk: skills get the leftover attention; ship with rough edges. **Mitigation:** skills land in their own amendment cycle within each release (separate from extractor/gate). Plan-author dispatches are independent.

**6.4 — One-question-at-a-time onboarding may slow the ritual to the point of feeling tedious.** Eric hates question-bombing, but he also has stakes; if the onboarding takes 90 minutes because every question is single-shot + sync, friction surfaces differently. **Mitigation:** v0.2.1 onboarding ritual must be tested with a fresh user before Eric (Decision Q's "anyone-but-Luke test"). PM-batched questions surface in a "next question" cadence — not one-at-a-time-with-30s-pauses.

**6.5 — The quality bar adds 20–30% to AI-time bands.** This is a guess. May be 40–50% in practice. The combined total at the high end (189 h) may be wrong. **Mitigation:** log actuals after each release per `feedback_duration_estimation_rubric`; recalibrate the bar's overhead from real data.

**6.6 — PM-persona is still a NEW shape.** v0.1.7's biggest unknown is whether per-project PM works. If it doesn't, v0.1.8 + v0.2.0 (which depend on PM for ratification + queue) bend out of shape. **Mitigation:** v0.1.7 builds with research-grade plan-doc; PM-shape design-note articulates the boundary; v0.1.7.a/v0.1.7.b split available if needed.

**6.7 — Skill-discovery has not been empirically verified at the project-shape `<workspace>/.claude/skills/`.** Only plugin-shape (the f04e925 bundle). v0.1.7 mechanism work depends on this working. **Mitigation:** v0.1.7 includes empirical smoke as the gate; halt-and-surface if discovery fails.

---

## §7 — Roadmap updates needed

The synthesis introduces version numbers + scope deltas that the existing roadmap and STATE doc don't reflect. Three updates needed.

### `docs/rebuild/plans/v0-1-x-roadmap.md` updates

- §1 top-line summary: append a sentence noting the Eric-path extension extends the cadence past v0.1.5 to v0.2.1.
- §2 add per-release detail rows for v0.1.6, v0.1.7, v0.1.8, v0.1.9, v0.2.0, v0.2.1 (one paragraph each, linking to this synthesis as the master).
- §3 deferred items: remove Eric-path items (extractor, PR-gate, etc.) from deferred list — they're now scheduled.
- §4 sequencing diagram: extend with the 6 new releases.
- §5 open owner-decisions: add Decisions O–S (5 new escalations).
- §8 method-decision register: pre-allocate rows for v0.1.6 → v0.2.1 (status `(planned)`).

### `docs/rebuild/STATE.md` updates

- Top-line status: "amendment cycle active (#125+); Eric-deliverable extension activated 2026-05-04; v0.1.6 → v0.2.1 cadence planned at `docs/rebuild/plans/eric-final-delivery-plan-2026-05-04.md`."
- Add a row to the active-programmes table for the Eric-deliverable extension (status `ACTIVE — synthesis sealed; v0.1.6 plan-author next`).

### `docs/rebuild/FUTURE_IDEAS_DRAFT.md` updates

- The "Layered skill story" entry can graduate to ACTIVE (no longer FIDRAFT) since synthesis lands here.
- The "Persona-behavior SKILL packages" entry similarly graduates (3 base + 12 dev-sdlc + 6 ratifications all scheduled).
- The "Two-copies-of-loam friction" entry stays in FIDRAFT (deferred to v0.2.x PyPI publish).
- Add an entry for "Decision O Ruby-first-class adder" cross-reference if Luke rules NO and the original thin-fallback ships.

### Recommendation: defer roadmap commit to v0.1.6 plan-author build agent

The synthesis itself is one commit; the roadmap + STATE updates are downstream of Luke ruling on the 5 escalations. **Defer** roadmap edits to the v0.1.6 plan-author dispatch (or a small follow-on if Luke rules quickly). This keeps the synthesis commit focused on the synthesis itself.

---

## §8 — Provenance trail

- **Quality bar (Luke directive 2026-05-04):** the synthesis brief verbatim quote.
- **`docs/rebuild/plans/eric-saas-app-use-case-version-sequence-2026-05-04.md`** (commit `ab98fb2`) — Eric path; 9 decisions A–I; 5 RF caveats; §7 sequence; §10 decisions.
- **`docs/rebuild/plans/layered-skill-story-research-2026-05-04.md`** (commit `4948e1b` + patch `4c54822`) — layered-skills path; 14 decisions A–N; §7 sequence; §8 decisions; auto-creation universal.
- **`docs/rebuild/VALUE_PROPOSITION.md`** — primary-persona test + harness test.
- **`framework/CLAUDE.md`** (= top-level `CLAUDE.md`) — Lens 1–5; partition rule.
- **`docs/rebuild/STATE.md`** — sealed-component history; M-FBM amendment #125 (commit `1a1f830`).
- **`plugins/dev-sdlc/docs/smoke-test-discipline.md`** — 6-dimension coverage spec.
- **`docs/rebuild/plans/v0-1-x-roadmap.md`** — current 5-release roadmap (v0.1.1–v0.1.5).
- **`docs/rebuild/FUTURE_IDEAS_DRAFT.md`** — layered-skill-story + persona-behavior bundle entries.
- **`plugins/loam-skills/`** (5 SKILLs sealed at `f04e925`, amendment #124) — base-tier surface.
- **Two-layer persona** — synthesis brief thread #3.
- **Three-tier gating** — synthesis brief thread #4 + Luke directives 2026-05-04 messages 9947/9951/9953.
- **Eric-stack context (Rails, SOC 2, one-question-at-a-time)** — synthesis brief threads #11/#12 + Luke directive on onboarding default.

---

## §9 — Method-decision register

(Reserved for post-build amendment SHAs as v0.1.6 → v0.2.1 land. Empty at synthesis authoring.)

| Release | Status | Tag SHA | Notes |
|---|---|---|---|
| v0.1.6 | (planned) | — | Production-safety + base-skills + 2 bug fixes. |
| v0.1.7 | (planned) | — | Subagents + PM + layered-skill mechanism. |
| v0.1.8 | (planned) | — | Extractor heavy + Ruby first-class + 6 SKILLs. |
| v0.1.9 | (planned) | — | PR-gate + 6 SKILLs. |
| v0.2.0 | (planned) | — | Codebase-watch + auto-creation MVP. |
| v0.2.1 | (planned) | — | Eric-deliverable smoke + onboarding + promotion rubric. |

---
