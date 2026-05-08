# v0.2.1 master plan — Eric onboarding hardening + promotion rubric + release-level HARD smoke gate (THE Eric ship)

**Status:** master plan-doc, plan-before-code. Authored 2026-05-04 (Sonnet, plan-author).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.
**Parent plan:** `docs/plans/eric-final-delivery-plan-2026-05-04.md` §2 v0.2.1 — AUTHORITATIVE.
**Companion research:** `docs/plans/layered-skill-story-research-2026-05-04.md` §4 (promotion rubric); `docs/plans/v0-2-0-master-plan.md` (release rollup `bbc93a7`); `plugins/dev-sdlc/docs/smoke-test-discipline.md`.

**Predecessor commits:** v0.2.0 SHIPPED — Cycle 1 `6fef2f1`, Cycle 2 `549fe88`, rollup `bbc93a7`. v0.1.9 SHIPPED — `790807d` / `0dc557e` / `3284087`. v0.1.8 sealed — Cycle 3 Ruby `6711dd7`; Cycle 4a JS/TS `67dd302`; Cycle 4b `c648cf9`; Cycle 5 `e4512b9`. v0.1.7 — `bcf699a` / `122a7c8`. v0.1.6 — `3f1d237` / `88674cb`. M-FBM `1a1f830`.

**Quality bar (Luke directive 2026-05-04):**

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

v0.2.1 is **THE Eric ship**. Eric installs this release. Quality bar absolutely binding — no compromise, no partial features. The first 5–10 minutes must feel intentional. HARD smoke gate at release-level per Decision R: every promised v0.1.6 → v0.2.1 capability exercises end-to-end against `rd-automation` (Eric's actual project; single fixture per §6.2).

---

## Principles applied this turn

- **CHANNEL** / **AUTONOMY** / **F2 RUTHLESS FEEDBACK** / **LOCKED-DESIGN-NOT-LICENSE** / **PROMISES > IN-MOMENT JUDGMENT** / **ODD §2.5** / **WD-IN-DISPATCHES** / **PLAN-BEFORE-CODE** / **SCOPE-ONLY** / **PRINCIPLE-APPLICATION DISCIPLINE** — propagated to every cycle's dispatch brief.
- **PARTITION RULE** (pre-resolved by parent dispatch):
  - Onboarding ritual: `framework/workspace-bootstrap/` (harness-general per Lens 2; every loam user gets onboarding).
  - One-question-at-a-time: composes with `framework/per-project-pm/` shipped at v0.1.7 Cycle 4 (`122a7c8`) — no new fence work.
  - Promotion rubric SKILL: `plugins/dev-sdlc/skills/skill-promotion-review/` (dev-scoped per three-tier gating).
  - Telegram: `framework/telegram-interface/` (read-only; channel selection during onboarding).
  - Install docs: `docs/getting-started.md` + `docs/dev-mode-getting-started.md`.
  - Live OSS smoke: `plugins/dev-sdlc/odd-extractor/tests/integration/` (clone-into-CI mode, NOT vendored).
  - Quarterly trigger: `framework/scope-of-work/` integration.
- **NEW-SCHEMA OPPORTUNITY** — manifest YAMLs schema v3; seal commits short-form; plan-doc §14 with `## 14.` heading.
- **SWARMING (Lens 5)** — three cycles each strictly tighter than v0.2.1 parent; further decomposition is coordination overhead.

---

## §1 — Executive summary

v0.2.1 is **THE Eric ship**. Six prior releases (v0.1.6 → v0.2.0) built the capability stack: production-safety + base SKILLs (v0.1.6); subagents + per-project PM + layered-skill discovery + one-question-at-a-time PM flow (v0.1.7); banded ODD extractor + Ruby first-class + 6 dev-sdlc SKILLs (v0.1.8); PR-safety gate + 3 CI templates + provenance PR template + 6 more SKILLs (v0.1.9); continuous codebase-watch + persona-driven skill capture MVP (v0.2.0). v0.2.1 hardens the onboarding ritual that ties this stack together for Eric's first 5–10 minutes, ships the promotion rubric mechanism, and runs the HARD release-level 6-dimension smoke gate against real OSS fixtures.

**Theme.** Polish the surface. Land promotion machinery. Run the gate that proves end-to-end works on someone-else's-codebase. The capability stack is built; v0.2.1 makes it Eric-usable.

**Cycle count: three cycles**, serialized per `feedback_serialize_amendment_builds`:

1. **Cycle 1 — Eric onboarding ritual hardening.** PRIMARY `framework/workspace-bootstrap/`. Auto-detect project language; sequence onboarding via PM batch API one-at-a-time per Decision Q; bootstrap production-stake profile + language adapter + Telegram (or CLI fallback) channel; fresh-user-tested ritual.
2. **Cycle 2 — Promotion rubric mechanism.** PRIMARY `plugins/dev-sdlc/skills/skill-promotion-review/`. 3-signal MVP per Decision L (Categorization + Quality + Conflict primary; Reusability/Tests/Usage secondary). Decision matrix + graduation workflow per layered-skills §4.2/§4.3. Quarterly-trigger via `framework/scope-of-work/`.
3. **Cycle 3 — Release-level HARD smoke gate execution.** No new component code. Execute Decision R HARD gate against Eric's actual project (`rd-automation`, local stale snapshot at `/Users/lukeivers/cowork-openclaw/_tmp-checkmate/rd-automation/`). Output: evidence document gating release tag.

**AI-time band.** **11–21 h** per parent §2 (revised post single-fixture ruling), midpoint ~16 h. Cycle 1: **5–9 h**. Cycle 2: **4–8 h**. Cycle 3: **2–4 h**. 20% quality-bar absorption baked in.

**Dependencies.** Cycle 3 depends on Cycle 1 + Cycle 2 sealed. All prior versions exercised by HARD smoke.

**What closes the release.** All 6 smoke dimensions exercised end-to-end on **Eric's `rd-automation` (single fixture)**. Onboarding fresh-user-tested with anyone-but-Luke. One-question-at-a-time enforced via PM end-to-end. Auto-skill-capture MVP fires on real recurring pattern. Continuous-watch detects synthetic external commit. Promotion rubric SKILL discoverable + invokable. Install docs (general + production-stake) authored + tested. SOC-2 audit-trail floor satisfied. If any feature ships partial, halt + surface BEFORE proceeding.

---

## §2 — Scope source-of-truth

Pulled verbatim from parent §2 v0.2.1 + layered-skills §4.

### From Eric synthesis §2 v0.2.1

| Item | Source | Placement |
|---|---|---|
| Onboarding ritual sealed | Eric §6.2 | `framework/workspace-bootstrap/` + `plugins/dev-sdlc/` |
| One-question-at-a-time enforcement | Eric §6 + Decision Q | `framework/per-project-pm/` (already shipped v0.1.7 Cycle 4) |
| Eric-facing install docs (general + production-stake) | Eric §6.2 | `docs/getting-started.md` + `docs/dev-mode-getting-started.md` |
| Live smoke pass against `rd-automation` (Eric's project; single fixture per §6.2 ruling 2026-05-05) | Eric §6.2 | `plugins/dev-sdlc/odd-extractor/tests/integration/` (read-only against existing local checkout) |
| Telegram (or Eric-chosen channel) integration | Eric §6.2 | `framework/telegram-interface/` integration |
| `skill-promotion-review` SKILL (3-signal MVP per Decision L) | layered-skills §4 | `plugins/dev-sdlc/skills/skill-promotion-review/` |
| Quarterly-review trigger | layered-skills §4.3 | `framework/scope-of-work/` integration |

### From layered-skills §4 (promotion rubric)

**Six signals (§4.1):** Reusability / Quality / Test-coverage / Usage / Conflict / Categorization.

**MVP per Decision L:** 3 signals (Categorization + Quality + Conflict) primary; Reusability + Tests + Usage layered as secondary inputs the SKILL body discusses but does not gate on. 3-signal MVP keeps rubric usable on day-1 (Eric won't have 30 days of usage data); secondary signals layer in once data accumulates.

**Decision matrix (§4.2):** Promote-to-base / Promote-to-plugin / Stay-workspace-local / Author-time-fix / Author-tests / Defer / Deprecate / Promote-with-deprecation-pointer / Fold-into-existing.

**Graduation workflow (§4.3):** quarterly OR on-demand → walk `<workspace>/.claude/skills/` → evaluate each → owner ratifies via PM (default-to-no per Decision G) → author tests for promotions → land in target via amendment cycle → remove workspace-local copy.

### Eric SaaS-app sequence connection

What v0.2.1 enables: Eric installs loam → `loam init` → 6 questions sequenced one-at-a-time → Rails auto-detected → production-stake activated → Telegram or CLI configured → first 5–10 min feel intentional. Post-30-days of accumulated workspace-local SKILLs (from v0.2.0 auto-skill-capture firing on recurring Rails patterns), `/skill-promotion-review` evaluates which graduate. HARD smoke proves all this works on real OSS code (Solidus or jumpstart-pro shape) — not just synthetic Rails fixtures.

---

## §3 — Cycle decomposition

Three cycles, each: theme, fence, AC family seed, smoke dimensions, dependencies, out-of-scope, AI-time, Eric-relevance, quality-bar audit.

### Cycle 1 — Eric onboarding ritual hardening

**Theme.** Polish the first 5–10 minutes. Auto-detect language; sequence onboarding one-at-a-time via PM (composing on v0.1.7 Cycle 4 `122a7c8`); bootstrap production-stake profile + adapter + channel.

**Scope-tightening.** Parent AC = "onboarding + promotion + smoke." Cycle 1 AC = onboarding only. Strictly tighter.

**Fence.** PRIMARY `framework/workspace-bootstrap/`. Compose-points (read-only — halt-and-surface if non-trivial extension needed): `framework/per-project-pm/` (PM batch API for question-mediation); `framework/telegram-interface/` (channel-selection); `plugins/dev-sdlc/odd-extractor/lang/` (adapter detection).

**AC family: AC.ONBOARD.\***

- **AC.ONBOARD.1** — `loam init` triggers ritual on fresh workspace; `LOAM_ONBOARDING_SKIP=1` env-var disables for CI.
- **AC.ONBOARD.2** — Project-language auto-detection (Ruby/Rails / JS/TS+Playwright / mixed / unknown) via depth-bounded tree walk + Gemfile / package.json / config detection. Q1 = confirm-detection ("I detected this is Rails. Continue? Y/N") OR ask-language on unknown.
- **AC.ONBOARD.3** — Question sequencing via PM batch API in single-question form per Decision Q. PM blocks on user response before next question.
- **AC.ONBOARD.4** — Q2: channel preference (1 Telegram / 2 CLI / 3 Skip-for-now). On Telegram → bootstrap calls `framework/telegram-interface/`. ONE channel question (not Telegram + Slack + email tree).
- **AC.ONBOARD.5** — Q3: safety profile (1 production-stake / 2 dev / 3 research). Sets `safety_profile` from v0.1.6. Default-highlight production-stake when language=Rails.
- **AC.ONBOARD.6** — Q4: extractor opt-in (Y now / Defer / Never). On Y → fires v0.1.8 extractor scoped to detected adapter.
- **AC.ONBOARD.7** — Q5: continuous-watch opt-in (Y / Defer-default / N). Defer is default for fresh-user low-context per §7.1.
- **AC.ONBOARD.8** — Q6: auto-skill-capture opt-in (Y / N-default per layered-skills §3.6 Decision E).
- **AC.ONBOARD.9** — Ritual completion summary: capabilities-active list + single next-action + audit-log location.
- **AC.ONBOARD.10** — Production-stake defaults flip on AC.ONBOARD.5: extractor dry-run-default; PR-gate halt-on-push; auto-skill-capture default-false; ratification-required-for-PLAUSIBLE→VERIFIED. Composes with v0.1.6 + Decision P SOC-2 floor.
- **AC.ONBOARD.11** — Audit-trail floor honored: every Q+A + activated capability emits `<workspace>/.loam/audit-log/onboarding-<date>.yaml` per Decision P.
- **AC.ONBOARD.12** — Fresh-user smoke fixture in `framework/workspace-bootstrap/tests/fixtures/fresh-user-onboarding/` exercises full path.
- **AC.ONBOARD.13** — Install docs (`docs/getting-started.md` + `docs/dev-mode-getting-started.md`) updated at quality-bar feel-intentional level: install-from-source; first-run walkthrough; channel selection; production-stake explanation; SOC-2 audit-trail location; troubleshooting.
- **AC.ONBOARD.14** — Component-level tests (per AC) + integration test (full ritual end-to-end against fixture).

**Smoke dimensions.** D1 ✓ (ritual fires + 6 questions sequenced + post-state observable). D2 ✓ (re-run idempotent). D3 ✓ (mid-onboarding `kill -TERM` → restart cleanly). D5 ✓ (post-state survives `/clear`). D6 ✓ (audit per AC.ONBOARD.11). D4 inherited.

**Dependencies.** v0.1.6 (production-safety profile); v0.1.7 Cycle 4 PM batch API (load-bearing); v0.1.8 extractor; v0.2.0 watch + auto-skill-capture.

**Out-of-scope.** Promotion rubric → Cycle 2. Live OSS smoke → Cycle 3. Multi-language polyglot detection beyond simple primary-language pick → v0.2.x.

**AI-time band.** **5–9 h**. Wall-clock ~25–55 min. Single-component fence (read-only compose-points) is the lower-end driver; fresh-user smoke is the upper-end driver.

**Eric-relevance.** Cycle 1 IS the make-or-break first 5–10 minutes. Decision Q's structural enforcement IS the load-bearing test against question-bombing.

**Quality-bar audit.** Each question single-shot per turn (not 3-in-one). All 6 questions exercise different fence components (PM, telegram-interface, language-adapter, profile-config, extractor, watch). Install docs at feel-intentional level. Production-stake default verified via Eric pre-call (open item §6 #3). Fresh-user fixture exercises full path. **No partial features.** ✓

---

### Cycle 2 — Promotion rubric mechanism

**Theme.** Workspace-local SKILLs accumulate; rubric is the disciplined evaluation surface. 3-signal MVP per Decision L → decision matrix → graduation workflow. Quarterly-trigger via `framework/scope-of-work/`. Dev-scoped per three-tier gating.

**Scope-tightening.** Cycle 1 AC = onboarding. Cycle 2 AC = promotion-rubric SKILL + quarterly-trigger. Strictly tighter — independent surface.

**Fence.** PRIMARY `plugins/dev-sdlc/skills/skill-promotion-review/`. Compose-points: `framework/scope-of-work/` (quarterly-trigger; halt-and-surface if non-trivial); `<workspace>/.claude/skills/` (read-only walk); `framework/per-project-pm/` (read-only via existing PM batch API).

**AC family: AC.PROMOTE.\***

- **AC.PROMOTE.1** — `skill-promotion-review` SKILL package with valid SKILL.md (frontmatter ≤1536 char description; 6-section body per dev-sdlc convention from v0.1.8 Cycle 5 + v0.1.9 Cycle 3).
- **AC.PROMOTE.2** — 3-signal MVP body specifies primary gates per Decision L: Categorization (HARNESS-GENERAL / DEV-SPECIFIC / PROJECT-SPECIFIC) + Quality (PASS / FAIL / NEEDS-REVISION) + Conflict (NO-CONFLICT / DUPLICATE / WIDER / NARROWER / ADJACENT). Reusability + Tests + Usage layered as secondary, non-blocking.
- **AC.PROMOTE.3** — Decision matrix encoded in SKILL body covering all 10 row classes from layered-skills §4.2.
- **AC.PROMOTE.4** — Walk-workspace logic: read `<workspace>/.claude/skills/`; per-skill 3-signal evaluation; structured table output with recommendations.
- **AC.PROMOTE.5** — Owner-ratification via PM batch API one-at-a-time per Decision Q. Default-to-no per Decision G; explicit Y to promote.
- **AC.PROMOTE.6** — Author-tests-for-promotions sub-flow per §4.3 step 4: SKILL guides persona to dispatch sub-agent for AC-shaped test authoring.
- **AC.PROMOTE.7** — Land-in-target via amendment cycle (composes with `loam-amend-cycle` SKILL): move SKILL.md → author manifest → `loam amend apply` → `loam amend seal`.
- **AC.PROMOTE.8** — Remove workspace-local copy post-promotion per §4.3 step 6: replace with single-line "moved-to-plugin" pointer.
- **AC.PROMOTE.9** — Demotion path per §4.4: SKILL surfaces "skill X fired N times since promotion; demote/retire?"; corrective amendment cycle.
- **AC.PROMOTE.10** — Quarterly-review trigger via `framework/scope-of-work/` cron-style 90-day cadence + on-demand `/skill-promotion-review`. Halt-and-surface if scope-of-work extension non-trivial; MVP fallback = on-demand only.
- **AC.PROMOTE.11** — Component-level tests against synthetic workspace-local SKILL fixtures (3+ shapes) covering signal-evaluation + decision-matrix + PM ratification flow.
- **AC.PROMOTE.12** — Discoverable in canonical pos-v2: `/skill-promotion-review` invokable; appears in `/` menu via Anthropic native + v0.1.7 Cycle 3 layered-skill mechanism.

**Smoke dimensions.** D1 ✓ (fresh workspace + synthetic skills → walk → recommendations → ratify → graduate). D2 ✓ (re-run on graduated → recognises moved pointer). D5 ✓ (promoted SKILL via Anthropic discovery in next session). D6 ✓ (audit per ratification). D3 / D4 inherited.

**Dependencies.** Cycle 1 (per `feedback_serialize_amendment_builds`); v0.1.7 Cycle 3 layered-skill discovery; v0.1.7 Cycle 4 PM batch API; v0.1.8 Cycle 5 + v0.1.9 Cycle 3 SKILLs precedent; `loam-amend-cycle` SKILL composition.

**Out-of-scope.** 6-signal full evaluation → v0.2.x. Auto-promotion (no owner ratification) → never on roadmap. Demotion-by-disuse-trigger → v0.2.x. Cross-workspace skill sharing → not on roadmap.

**AI-time band.** **4–8 h**. Wall-clock ~20–45 min. SKILL authoring well-rehearsed (20 SKILLs sealed at v0.2.0 close); scope-of-work integration is variability driver.

**Eric-relevance.** Indirect — Eric himself doesn't promote (dev-scoped). But his accumulated workspace-local SKILLs become input to Luke-side review where Eric's Rails patterns graduate to `plugins/dev-sdlc/` for other Rails users to inherit. The mechanism IS what makes Eric's usage compound forward.

**Quality-bar audit.** SKILL body covers FULL ritual (not stub). 3-signal MVP intentional per Decision L (not 6-signal half-implemented). Decision matrix complete. Owner-default-to-no per Decision G. **No partial features.** ✓

---

### Cycle 3 — Release-level HARD smoke gate execution

**Theme.** No new component code. Execute Decision R HARD gate against Eric's actual `rd-automation` codebase (single fixture). Artefact gating release tag.

**Scope-tightening.** Cycle 1 + Cycle 2 ship code. Cycle 3 EXECUTES the gate proving end-to-end works on someone-else's-codebase. Strictly tighter — no code edits, only smoke + evidence document + halt-and-surface.

**Fence.** No primary fence. Read-only across `framework/`, `plugins/`, OSS fixture clones. Output: evidence document at `<pos3>/workspace/.scratch/claude-output/v0-2-1-live-oss-smoke-2026-05-04.md`.

**AC family: AC.HARDSMOKE.\***

- **AC.HARDSMOKE.1** — Fixture is Eric's `rd-automation` at the existing local path `/Users/lukeivers/cowork-openclaw/_tmp-checkmate/rd-automation/` (NOT cloned to pos3 scratch — already on disk; private repo, owner's access revoked). Fixture HEAD SHA captured in evidence document.
- **AC.HARDSMOKE.2** — D1 cold-state on JS/TS fixture: `loam init` → banded contract above floor (≥3 VERIFIED + ≥5 PLAUSIBLE + ≥2 HYPOTHESISED per v0.1.8 floor); JS/TS adapter recognises Express/Playwright/page-objects/TS-types/Zod/class-validator/Jest-Mocha-Vitest idioms.
- **AC.HARDSMOKE.3** — PR-safety gate detects synthetic violations on `rd-automation` (delete a method tied to extracted VERIFIED AC) → hard-block + provenance-traceable PR description per v0.1.9 Cycle 1 + Cycle 2.
- **AC.HARDSMOKE.4** — Auto-skill-creation MVP fires on real recurring pattern (3+ instances) → proposal in PM → ratify → SKILL materialises → auto-loads next turn. End-to-end path.
- **AC.HARDSMOKE.5** — Continuous-watch detects synthetic external commit modifying code tied to extracted AC → PM proposal → ratify → contract updates. Composes with v0.2.0 Cycle 1.
- **AC.HARDSMOKE.6** — Onboarding fresh-user-tested with anyone-but-Luke per Decision Q reasoning + parent §6.4 mitigation. Pass criterion: ≤10 min completion + "feels intentional" verbatim.
- **AC.HARDSMOKE.7** — Promotion rubric SKILL invokable on real workspace post-AC.HARDSMOKE.4: 3-signal evaluation table → recommendations → synthetic Y for one promotion → SKILL graduates (rolled back post-smoke to avoid plugin-tree pollution).
- **AC.HARDSMOKE.8** — D2 steady-state across all surfaces (extract / gate / skill-capture / promotion-review): re-run idempotent.
- **AC.HARDSMOKE.9** — D3 restart: mid-extraction + mid-onboarding `kill -TERM` → re-invoke clean.
- **AC.HARDSMOKE.10** — D4 reboot: macOS reboot equivalent; post-reboot state survives (contract / ratified SKILLs / audit-log / profile config).
- **AC.HARDSMOKE.11** — D5 cross-session (most-load-bearing per STATE.md): Session A onboards + ratifies + extracts; Session B persona auto-loads ratified SKILL + reads contract + gate fires + promotion-review walks correctly.
- **AC.HARDSMOKE.12** — D6 telemetry-floor: audit-log per onboarding question + extraction + gate decision + skill-capture trigger + ratification + promotion-review walk + promotion ratification.
- **AC.HARDSMOKE.13** — Live-OSS-smoke evidence document at `<pos3>/workspace/.scratch/claude-output/v0-2-1-live-oss-smoke-2026-05-04.md` covering: fixture identification (rd-automation local-path + HEAD SHA at smoke time); per-AC.HARDSMOKE evidence (pass/fail + command output excerpts); fresh-user feedback verbatim; halt-and-surface findings; release-tag recommendation. IS the gating artefact.
- **AC.HARDSMOKE.14** — One-question-at-a-time enforced end-to-end across onboarding + extractor ratification + watch ratification + skill-capture ratification + promotion-review ratification. No question-bombing observed.

**Smoke dimensions.** All 6 exercised explicitly per AC.HARDSMOKE.2 (D1) + .8 (D2) + .9 (D3) + .10 (D4) + .11 (D5) + .12 (D6).

**Dependencies.** Cycle 1 + Cycle 2 sealed. ANY prior version broken under real-OSS-fixture conditions surfaces here.

**Out-of-scope.** Eric himself running smoke (post-Eric-go-live). Multi-fixture concurrent smoke. Smoke against Eric's actual codebase (deferred to first install). "Ship anyway with caveats" — corrective amendment instead.

**AI-time band.** **2–4 h**. Wall-clock ~10–25 min if all green; up to ~45 min on findings. Single fixture; no new code.

**Eric-relevance.** Proves to Luke (and Eric, post-hoc) the system works on real code. Without Cycle 3, Eric is the first real-codebase user — too risky for a quality-bar release.

**Quality-bar audit.** HARD gate per Decision R. Single fixture (Eric's `rd-automation`). Fresh-user-tested. End-to-end path exercised. Halt-and-surface on ANY breakage; no "ship anyway." **No partial features.** ✓

---

### Decomposition stopping-criterion check

Per Lens 5: decompose until each subtask's AC strictly tighter than parent; stop when split adds only coordination overhead.

- Three cycles each strictly tighter than v0.2.1 parent.
- Considered + rejected: split Cycle 1 onboarding into 6 sub-cycles (share fence + PM-mediation; redundant scaffolding); split Cycle 2 SKILL from quarterly-trigger (thin dependency; no AC tightening); fold Cycle 3 into Cycle 1+2 tails (release-level smoke is integration-level + has its own AC family per ODD §2.5).
- Cycle count: 3 ∈ [2, 3] (parent halt-trigger range, upper edge); no cleaner 2-cycle option.

---

## §4 — Per-cycle dispatch briefs

Three dispatch briefs ready at v0.2.1 build time. Source-of-truth fields (fence, ACs, smoke, AI-time, out-of-scope) live at §3 — briefs reference §3 + add operational fields.

### Cycle 1 dispatch brief

```
# v0.2.1 Cycle 1 build dispatch — Eric onboarding ritual hardening

Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`. NOT pos3.

Plan-author dispatch (plan-before-code). Output: `docs/plans/v0-2-1-cycle-1-eric-onboarding-hardening.md` (sub-plan-doc) + `.manifest.yaml`.

Principles: CHANNEL / AUTONOMY / F2 RUTHLESS FEEDBACK / LOCKED-DESIGN-NOT-LICENSE / PROMISES > IN-MOMENT JUDGMENT / ODD §2.5 / WD-IN-DISPATCHES / PARTITION RULE / SCOPE-ONLY / v3 manifest schema / short-form seal commits / plan-doc §14 with `## 14.` heading / PRINCIPLE-APPLICATION DISCIPLINE.

Quality bar (Luke directive 2026-05-04): every named AC complete + tested. One-at-a-time questions via PM (no question-bombing). Auto-detection works on Rails + JS/TS (verified against canonical fixtures). Production-stake default for Rails. Install docs feel-intentional. Fresh-user fixture exercises full path. THE Eric ship — no partial features.

Source pointers: master plan §3 Cycle 1; Eric synthesis §2 v0.2.1; Decisions Q + P; v0.1.7 Cycle 4 PM batch API `122a7c8`; v0.1.6 production-safety `3f1d237` / `88674cb`; v0.1.8 adapters `6711dd7` / `67dd302`; v0.2.0 `6fef2f1` / `549fe88`; smoke discipline `plugins/dev-sdlc/docs/smoke-test-discipline.md`.

Fence + ACs + smoke + AI-time + out-of-scope: per master plan §3 Cycle 1.

Halt triggers: WD drifts; plan-doc not before code; PM-side edits needed (escalate); telegram-interface API insufficient (escalate); language-detection misclassifies canonical fixtures (escalate to tree-sitter-aware); production-stake default-flip ambiguous; install-docs ship as stub (halt + reframe); fresh-user fixture cannot exercise full path (escalate); cycle >6 h wall-clock; ODD violations in surrounding code; >3 escalations needed.

Bookkeeping: pos-amend apply (NOT --amend); manifest schema v3; single semantic commit; short-form seal; §14 backfill in separate post-seal commit; backfill master plan §9 row.

Model rationale: (none — Sonnet default).
```

### Cycle 2 dispatch brief

```
# v0.2.1 Cycle 2 build dispatch — Promotion rubric mechanism

Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`. NOT pos3.

Plan-author dispatch. Output: `docs/plans/v0-2-1-cycle-2-promotion-rubric.md` + `.manifest.yaml`.

Principles: same as Cycle 1.

Quality bar: 3-signal MVP intentional per Decision L (not 6-signal half-implemented); SKILL body covers FULL ritual (not stub); decision matrix complete (all 10 row classes); owner-default-to-no per Decision G; quarterly trigger composes cleanly with scope-of-work; tests cover all signal-evaluation paths. THE Eric ship — no partial features.

Source pointers: master plan §3 Cycle 2; Eric synthesis §2 v0.2.1; layered-skills §4 (lines 261–323); Decisions L + G + Q; v0.1.7 Cycle 3 `bcf699a`; v0.1.7 Cycle 4 `122a7c8`; v0.1.8 Cycle 5 + v0.1.9 Cycle 3 SKILLs precedent; `loam-amend-cycle` SKILL; v0.2.1 Cycle 1 SHA backfilled post-seal; smoke discipline.

Fence + ACs + smoke + AI-time + out-of-scope: per master plan §3 Cycle 2.

Halt triggers: WD drifts; plan-doc not before code; Cycle 1 not sealed; scope-of-work extension non-trivial (escalate); PM-side edits needed; SKILL frontmatter invalid; SKILL body stub or missing 6-section; decision matrix incomplete; cycle >5 h wall-clock; ODD violations; >3 escalations needed.

Bookkeeping: pos-amend apply; manifest schema v3; single semantic commit; short-form seal; §14 backfill separate; master plan §9 row backfill.

Model rationale: (none — Sonnet default).
```

### Cycle 3 dispatch brief

```
# v0.2.1 Cycle 3 build dispatch — Release-level HARD smoke gate execution

Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`. NOT pos3.

Smoke-execution dispatch (NO new component code). Output: `<pos3>/workspace/.scratch/claude-output/v0-2-1-live-oss-smoke-2026-05-04.md` (evidence document — IS the gating artefact).

Principles: same as Cycle 1 + Cycle 2 + RUTHLESS-FEEDBACK on every smoke result (no rationalising near-passes as passes).

Quality bar: HARD gate per Decision R. Single fixture: Eric's `rd-automation` (Luke ruled 2026-05-05). All 6 dimensions end-to-end on rd-automation. Fresh-user-tested onboarding. Halt-and-surface on ANY breakage; no "ship anyway with caveats." THE Eric ship — release tag deferred until smoke green.

Source pointers: master plan §3 Cycle 3 + §5; Eric synthesis §2 v0.2.1 (line 289 live OSS smoke); Decision R; v0.1.6 / v0.1.7 / v0.1.8 / v0.1.9 / v0.2.0 SHAs (per master plan §8); v0.2.1 Cycle 1 + Cycle 2 SHAs backfilled post-seal; smoke discipline; STATE.md (D5 cross-session is THE ship-test).

Fence + ACs + smoke + AI-time + out-of-scope: per master plan §3 Cycle 3.

Halt triggers: WD drifts; OSS fixtures (resolved — single fixture: rd-automation); Cycle 1 OR Cycle 2 not sealed; fresh-user not available within reasonable window (escalate — async fallback); ANY AC.HARDSMOKE.* fails (halt + corrective amendment, NOT "ship with caveats"); D5 cross-session fails (THE ship-test — halt); audit-log floor missing on real fixture (Decision P violation — halt); cycle >6 h wall-clock no progress; ODD violations in prior-shipped surface (halt + RF); >3 escalations needed.

Bookkeeping: NO new component commits expected. Evidence document at pos3 scratch (workspace-local; NOT canonical commit). On smoke-green: dispatcher creates v0.2.1 SHIPPED rollup commit on canonical — backfills STATE.md + roadmap §8 + eric-final-delivery §2 v0.2.1 row with Cycle 1 + Cycle 2 SHAs + SHIPPED status. Tag deferred until Luke gates.

Model rationale: (none — Sonnet default; Cycle 3 is execution-and-judging, not heavy synthesis).
```

---

## §5 — Release-level HARD smoke gate

HARD gate per Decision R (HARD at v0.1.6 / v0.1.8 / v0.2.1; SOFT elsewhere). Quality-bar absolutely binding. Cycle 3 IS execution; this section codifies shape.

After Cycle 1 + Cycle 2 seal, Cycle 3 build agent runs:

1. **D1 cold-state on Eric's `rd-automation`** (not synthetic in-tree). The fixture: `loam init` → 6-question onboarding sequenced cleanly → extractor produces banded contract above v0.1.8 floor → audit-log entries observable.
2. **D2 steady-state.** Re-run extract/gate/skill-capture/promotion-review on unchanged → idempotent.
3. **D3 restart.** Mid-extraction + mid-onboarding `kill -TERM` → re-invoke clean.
4. **D4 reboot.** macOS reboot equivalent. Post-reboot: contract / ratified SKILLs / audit-log / profile config survive.
5. **D5 cross-session (most-load-bearing per STATE.md).** Session A onboards + ratifies + extracts. Session B persona auto-loads ratified SKILL + reads contract + gate fires + promotion-review walks correctly.
6. **D6 telemetry-floor.** Audit-log per onboarding Q + extraction + gate decision + skill-capture trigger + ratification + promotion-review walk + promotion ratification.

**End-to-end Eric-path smoke.** (A) `loam init` → 6 questions one-at-a-time → production-stake activated → extractor opt-in → continuous-watch opt-in → auto-skill-capture deferred-default-no → completion summary. (B) Banded contract on real OSS code above floor + audit-log per stage. (C) Synthetic PR breaks VERIFIED AC → gate hard-blocks + provenance PR description. (D) Synthetic recurring pattern → auto-skill-capture trigger → PM proposal → ratify → SKILL materialises → auto-loads. (E) Synthetic external commit → continuous-watch detects → PM proposal → ratify → contract updates. (F) `/skill-promotion-review` walks workspace → 3-signal evaluation → recommendations → synthetic Y for one promotion → SKILL graduates (rolled back post-smoke).

**Fresh-user smoke (AC.HARDSMOKE.6).** Anyone-but-Luke runs onboarding on rd-automation. Pass criterion: ≤10 min without halting + "feels intentional" verbatim.

**Gate to v0.2.1 release tag.** All 6 dimensions green on rd-automation + Eric-survey-response received and reflected in install-config defaults + evidence document authored → dispatcher creates v0.2.1 SHIPPED rollup commit + `git tag v0.2.1` (DO NOT push until Luke gates Eric install).

---

## §6 — Open items for Luke (RESOLVED 2026-05-05)

All three items resolved by owner ruling 2026-05-05. Resolution notes preserved below for traceability.

### §6.1 — OSS fixture (Rails-payment-shape) — RESOLVED: dropped

Eric is JS/TS only for v0.2.1. Rails fixture not needed. Solidus held in FIDRAFT for whenever Rails work re-engages.

### §6.2 — OSS fixture (Playwright JS/TS) — RESOLVED: rd-automation single-fixture

Owner ruled 2026-05-05: smoke against Eric's actual project, `rd-automation`. Local stale snapshot at `/Users/lukeivers/cowork-openclaw/_tmp-checkmate/rd-automation/` (commit dated 2026-03-25; owner's GH access revoked, fetch fails). Single-fixture; the public-OSS landscape research surfaced no real-app-shape candidate, and rd-automation is strictly the more relevant target. Profile: TypeScript 5.7, Playwright 1.50, Express 4.21, AWS SDK (S3/CloudWatch/ECS); 2.7 MB / 81 files / ~17.7k LOC; tests `dd_dispute.spec.ts`, `uber_dispute.spec.ts`, `uber.spec.ts`; README + LOCAL_SETUP_GUIDE.md exist. Public-OSS fixture-research report at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-2-1-playwright-fixture-candidates.md`.

### §6.3 — Eric pre-call (Decision S) — RESOLVED: async Claude-Code-survey

Owner ruled 2026-05-05: live call replaced by async Claude-Code-pasteable onboarding survey. Eric receives prompt → pastes into Claude Code → walks 12 questions one-at-a-time → writes `~/loam-onboarding-eric-<date>.md` → sends file back. Owner is courier. Survey artefact at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/eric-onboarding-prompt-2026-05-05.md`. Companion live-walk-mode question list at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/eric-onboarding-questions-call-mode-2026-05-05.md` (owner reference only). Question set: 8 required (stack versions / Playwright shape / app purpose / production-stake / SOC-2 controls / authority bounds / channel / codebase shape) + 4 optional (existing tooling / off-limits zones / first task / pain points). Eric's responses populate the v0.2.1 install-config defaults.

(No other escalations — Decisions L / G / Q / R RESOLVED at parent §3.)

---

## §7 — Honest doubts (F2 RF on this decomposition)

The places this decomposition is least confident.

**7.1 — AC.ONBOARD.7 + .8 (watch + skill-capture opt-ins) may overload the ritual.** Fresh user without context may answer Q5+Q6 randomly. *Mitigation:* default-defer for Q5+Q6; fresh-user fixture exercises both Y and Defer paths.

**7.2 — Project-language auto-detection may fail on polyglot.** Real codebases often mix Rails+JS+Python. *Mitigation:* Cycle 1 plan-doc names polyglot logic (multi-language → ask primary OR enable both); halt-and-surface if non-trivial extractor-side edits.

**7.3 — Production-stake default for Rails is load-bearing on assumption.** Not all Rails projects are production-stake. *Mitigation:* question shape surfaces all 3 options + highlights production-stake as default-but-overridable; fresh-user verifies non-sticky; Eric pre-call (open item #3) verifies.

**7.4 — Cycle 2 quarterly-trigger may need substantial scope-of-work extension.** *Mitigation:* halt-and-surface; MVP fallback = on-demand only; cron-trigger v0.2.x.

**7.5 — 3-signal MVP may produce too-loose recommendations.** Without Reusability/Tests/Usage as gates, may recommend promotions that lack reuse evidence. *Mitigation:* secondary signals discussed in body (not blocking); owner-default-to-no per Decision G is ultimate gate; v0.2.x layers in.

**7.6 — Cycle 3 OSS fixture clone may pollute canonical-tree state.** Narrowed post single-fixture ruling: rd-automation already on disk at non-canonical path `/Users/lukeivers/cowork-openclaw/_tmp-checkmate/rd-automation/` — no clone, no pollution risk. *Mitigation (now trivial):* evidence document cites local-path + HEAD SHA explicitly.

**7.7 — Fresh-user availability may delay Cycle 3.** Restructured post async-survey ruling: async-survey-via-Eric replaces fresh-user-with-Luke. *Mitigation:* if Eric is slow to return survey, Cycle 3 still runs against rd-automation with default-derived install-config; Eric's responses retrofit defaults post-survey. Halt-trigger only if survey returns evidence Cycle 3 ran on materially-wrong defaults.

**7.8 — HARD smoke may surface real breakage from prior versions.** v0.1.6 → v0.2.0 shipped on synthetic; real-OSS may break paths. Narrowing the fixture set narrows the surface (single fixture vs two), but the failure mode persists. *Mitigation:* corrective amendments per `feedback_audit_finding_triage`; ANY breakage halts + surfaces; SHIPPED rollup waits on amendments green.

**7.9 — Cycle 3 AI-time band (2–4 h) may be optimistic.** Single-fixture cuts the band relative to original 3–5 h estimate. Real-OSS + 6-dim + evidence + halt-and-surface could still push past upper bound on findings. *Mitigation:* log actuals; halt-trigger at >6 h wall-clock.

**7.10 — Decision S Eric pre-call deferral may bite hard.** Replaced post async-survey ruling: pre-call deferral resolved by async Claude-Code-survey (12 questions; §6.3). *Residual risk:* whether 12 written questions surface as much as a 30-min synchronous interaction would. Honestly noted — written-Q-via-courier loses follow-up dynamics, body language, and ad-hoc clarification. *Mitigation:* survey question set is intentionally broad (8 required + 4 optional) to compensate; if Eric's responses surface unanswered deltas, escalate to async follow-up before release-tag push.

---

## §8 — Provenance trail

- **Master plan source authority:** `docs/plans/eric-final-delivery-plan-2026-05-04.md` §2 v0.2.1 + Decisions L / G / Q / P / R / S.
- **Layered-skills promotion rubric:** `docs/plans/layered-skill-story-research-2026-05-04.md` §4 (lines 261–323).
- **v0.2.0 master plan precedent:** `docs/plans/v0-2-0-master-plan.md` (rollup `bbc93a7`).
- **v0.2.0 sealed cycles:** Cycle 1 `6fef2f1`; Cycle 2 `549fe88`; rollup `bbc93a7`.
- **v0.1.9 sealed cycles:** `790807d` / `0dc557e` / `3284087`. Local release `9022df1`.
- **v0.1.8 sealed:** `9b64cd4`; Cycle 3 `6711dd7`; Cycle 4a `67dd302`; Cycle 4b `c648cf9`; Cycle 5 `e4512b9`.
- **v0.1.7 sealed:** `3aa20dd` / `73505f0` / `bcf699a` / `122a7c8`.
- **v0.1.6 sealed:** `3f1d237` / `88674cb`. M-FBM `1a1f830`.
- **Smoke-test discipline:** `plugins/dev-sdlc/docs/smoke-test-discipline.md`.
- **Schema v3 + seal-narrative compression:** `019cfca` / `df3f50f`.
- **Lens 5 swarming:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_swarming_recursive_decomposition.md` + `framework/CLAUDE.md`.
- **AI-time rubric:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_duration_estimation_rubric.md`.
- **Quality bar (Luke directive 2026-05-04):** parent §1 verbatim + Decision R framing.
- **Eric stack context (Rails, JS/TS/Playwright, SOC 2, one-question-at-a-time):** parent §1 + Decisions P + Q + S.

---

## §9 — Method-decision register

Master-plan-level method decisions. Per-cycle plan-docs author own §14.

| Decision | Choice | Rationale |
|---|---|---|
| Cycle count | 3 (Cycle 3 = gate-execution + evidence document) | Lens 5: Cycle 3 has own AC family per ODD §2.5; halt-trigger range [2, 3] at upper edge. |
| Onboarding question count | 6 (language + channel + safety-profile + extractor + watch + skill-capture) | Q5+Q6 default-defer (mitigates 7.1). |
| One-question-at-a-time | PM batch API; no new fence | Decision Q + v0.1.7 Cycle 4 `122a7c8`. |
| Production-stake default for Rails | Highlight as default-but-overridable | Mitigates 7.3; fresh-user + Eric pre-call verify. |
| Project-language detection | Depth-bounded tree walk + Gemfile/package.json; halt-and-surface on polyglot | Mitigates 7.2; polyglot → v0.2.x. |
| Cycle 2 MVP signals | 3 primary (Categorization + Quality + Conflict); 3 secondary discussed not blocking | Decision L. Mitigates 7.5. |
| Cycle 2 owner-ratification | PM batch API; default-to-no | Decision G; mirrors Eric Decision I. |
| Cycle 2 quarterly-trigger | scope-of-work integration; halt-and-surface if non-trivial; on-demand fallback | Mitigates 7.4. |
| Cycle 3 fence | Read-only; no new code | rd-automation already at non-canonical path; no clone needed. Mitigates 7.6. |
| Cycle 3 OSS fixture count | 1 (rd-automation, Eric's actual project) | Owner ruled 2026-05-05; single-fixture; profile per §6.2. |
| Cycle 3 fresh-user test | Anyone-but-Luke; ≤10 min + "feels intentional" verbatim | Decision Q + parent §6.4. Mitigates 7.7. |
| Cycle 3 evidence document | `<pos3>/workspace/.scratch/claude-output/v0-2-1-live-oss-smoke-2026-05-04.md` | Mitigates 7.6. |
| Halt-on-breakage policy | Halt + corrective amendment; NO "ship with caveats" | Decision R + quality bar. Mitigates 7.8. |
| Eric pre-call (Decision S) | RESOLVED — async Claude-Code-survey replaces live call (per Luke 2026-05-05) | §6.3. Mitigates 7.10. |
| v0.2.1 fixture | rd-automation single (private; local stale snapshot 2026-03-25) | Owner ruled 2026-05-05; public-OSS landscape lacks real-app-shape candidate. |
| SKILL frontmatter shape | `description`-only (no `name`) | Mirrors 20+ sealed SKILLs. |
| SKILL body section ordering | What / When / How / Graceful degradation / Composition / Out of scope | Verified across 20+ sealed. |
| Test file granularity | One per AC (~10–15 per cycle) | Mirrors dev-sdlc convention. |
| Dispatch model tier | Sonnet for all 3 cycles | No model-rationale needed; mitigates prior Opus-stall RF. |
| Quality-bar absorption | 20% (baked into 11–21 h band post single-fixture ruling) | Mirrors v0.1.9 + v0.2.0; recalibrate post-Cycle-3. |
| Release-level HARD smoke | YES — Cycle 3 per Decision R | THE Eric ship; quality-bar binding. |
| Release-tag push | Defer until Luke gates Eric install. Loam/main fast-forward push autonomous-authorized per Luke 2026-05-05 (resolves F5 dev-mode for Eric); tag-push remains gated on F5-via-publish + Eric-survey-response. | Standard policy + post-re-smoke YELLOW gating. |

### Per-cycle SHA backfill table

| Cycle | Theme | Apply SHA | Seal SHA |
|---|---|---|---|
| Cycle 1 | Eric onboarding ritual hardening | f6b5047 | 55640b1 |
| Cycle 2 | Promotion rubric mechanism | c48aa68 | 298172e |
| Cycle 3 | Release-level HARD smoke gate execution (smoke-only; original verdict RED) | n/a (no canonical commit) | n/a |
| Corrective F1 | odd-extractor contract-draft.yaml acs+unhandled_paths | apply `0904064` | seal `ad42314` (§14 backfill `5fea94c`) |
| Corrective F2 | workspace-bootstrap language-detection framework/ skip | apply `70987e5` | seal `d82a43b` (§14 backfill `686d65c`) |
| Re-smoke | Post-F1/F2 HARD gate verdict YELLOW (F5 dev-mode persists, resolves via loam push) | evidence at `<pos3>/workspace/.scratch/claude-output/v0-2-1-live-oss-smoke-2026-05-05-rerun.md` | n/a |

Backfilled per cycle as cycles seal. Final v0.2.1 SHIPPED rollup updates STATE.md + v0-1-x-roadmap.md §8 + eric-final-delivery-plan-2026-05-04 §2 v0.2.1 row after Cycle 3 + correctives F1/F2 + re-smoke verdict YELLOW (F5 resolves for Eric via lukeivers/loam:main fast-forward push, authorized 2026-05-05).

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Master-plan method-level decisions recorded at §9 above. The `## 14.` heading exists per AC.D-sa.7 lint requirement; content lives at §9 to avoid duplication. Per-cycle plan-docs author own §14 with cycle-specific decisions.
