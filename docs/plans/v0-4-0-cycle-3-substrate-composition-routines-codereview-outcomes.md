# v0.4.0 Cycle 3 — Substrate composition: Routines + Code Review + Outcomes-pattern ADR

**Slug:** `v0-4-0-cycle-3-substrate-composition-routines-codereview-outcomes`
**Date authored:** 2026-05-08.
**Parent master plan:** `docs/plans/v0-4-0-master-plan.md` §3 Cycle 3.
**Predecessor cycles:** C1 sealed at `cc2efbba`; C2 sealed at `f031c89c`.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Component fence:** PRIMARY `plugins/dev-sdlc/skills/plan-docs-author/SKILL.md` (extension); NEW `docs/design/odd-vs-outcomes.md`; NEW memory feedback file `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_routines_runtime_layer.md`; NEW `docs/plans/example-routines-runtime-dispatch.md` + NEW `docs/plans/example-code-review-composition.md`. Universal admissions per `docs/plans/`. Test edit at `plugins/dev-sdlc/odd-extractor/tests/test_AC_V040C2_1_outcome_altitude.py` (folded F2 enhancement; small / cosmetic). Read-only: sealed-component source code; `plugins/dev-sdlc/skills/dispatch-brief-authoring/SKILL.md`.

---

## §1 — Outcome shape (the "why")

C3 closes three small substrate-composition deliverables that share the "compose-on-Claude-substrate" theme. Per the conference research at `<workspace>/.scratch/claude-output/claude-conference-features-2026-05-06.md`, three Claude Code primitives shipped in the past two weeks; loam composes on them rather than reimplements:

1. **Routines** — runtime layer for background-agent dispatches. (See §5 verification finding: actual CLI surface is `claude agents` + `/schedule` SKILL, NOT `claude routine create` as named in the conference research; capability exists; documentation reflects the verified-live surface.)
2. **Code Review / Security Review** — plan-step primitives. (See §5: actual CLI surface is `claude ultrareview` + `/review` / `/security-review` SKILLs, NOT `claude code review` as named in the conference research; capability exists; SKILL guidance + example reflect the verified-live surface.)
3. **Outcomes** (Managed Agents, public beta) — runtime grader analogue to ODD's authoring-time discipline. **API-keyed; loam-on-subscription cannot directly compose**, so this is a documented architectural divergence ADR rather than an integration.

The bundle is intentional per Lens 5 stopping criterion: each individually 15–30 min, three together ~45–90 min; per-AC sub-cycles add coordination overhead with no AC tightening.

The C2 build report's F2 finding #2 ("`pytest -s` did not emit per-stage stdout") folds into this cycle as AC.V040C3.5 — a small cosmetic enhancement adding `len(diff.commits)` print-on-success to the C2 outcome-altitude test so future runs can be classified single-vs-multi from logs without re-running.

## §2 — Lens checks (per CLAUDE.md design lenses)

- **Lens 1 (Claude-leverage-first):** ✓ — C3 is the canonical Lens 1 cycle; every deliverable is "compose on Claude-native primitive, do not reimplement." Verified-live surface: `claude agents` (Routines analogue), `claude ultrareview` (Code Review analogue), `/schedule` + `/review` + `/security-review` SKILLs.
- **Lens 2 (harness + primary-persona value):** ✓ — Routines + Code Review composition reduces translation burden (user no longer hand-codes background-agent or review primitives; they invoke verified-live Claude surface). Outcomes ADR adds clarity about why subscription-only loam diverges from API-only Outcomes — preserves the harness's architectural integrity for the subscription audience.
- **Lens 3 (ODD authoring):** ✓ — every AC observable + testable; method is the builder's call; §4 names six ACs; ≥1 outcome-altitude per the requirement.
- **Lens 4 (scope ↔ confidence):** TIGHT scope — the three deliverables are doc/SKILL/ADR work with high confidence in the outcome shape (cycle stub already named the deliverables explicitly). Method LOOSE — each deliverable's prose / structure is the builder's call. The CLI-name divergence finding (§5) was unknown at plan-author time; the plan-doc tightens after halt-and-surface.
- **Lens 5 (swarming):** Single-agent execution; `max_planner_depth: 1`. The cycle bundles three 15–30 min deliverables that share theme; further decomposition would add only coordination overhead with no AC tightening (per master plan §3 C3 rationale).

## §3 — Component fence (single-component admission list)

PRIMARY edit surfaces:
- `plugins/dev-sdlc/skills/plan-docs-author/SKILL.md` — gain a "compose-on-claude-code-review" section (~30–60 lines).
- `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_routines_runtime_layer.md` — NEW memory feedback file (pos3-local convention; see §10 RF #3 for canonicalization tradeoff).
- `docs/design/odd-vs-outcomes.md` — NEW Outcomes-pattern ADR.
- `docs/plans/example-routines-runtime-dispatch.md` — NEW example plan-doc invoking the verified-live Routines surface (`claude agents` / `/schedule`).
- `docs/plans/example-code-review-composition.md` — NEW example plan-doc invoking the verified-live Code Review surface (`claude ultrareview` / `/review` / `/security-review`).
- `plugins/dev-sdlc/odd-extractor/tests/test_AC_V040C2_1_outcome_altitude.py` — small F2-from-C2 enhancement: print `len(diff.commits)` on success so future runs are classifiable single-vs-multi from logs (AC.V040C3.5).

Universal admissions: `docs/plans/` (plan-doc + manifest + examples); test edit is a single-line print-on-success addition under the C2 sealed component (no behaviour change; AC-aligned to AC.V040C3.5).

Read-only: sealed-component code; `dispatch-brief-authoring` SKILL; `claude --help` invocation surface (verification only).

## §4 — AC family — `AC.V040C3.*`

- **AC.V040C3.1 — Routines pattern memory feedback file exists + names verified-live invocation shape.** `feedback_routines_runtime_layer.md` exists at `~/.claude/projects/-Users-lukeivers-pos3/memory/`; names the verified-live surface (`claude agents` + `/schedule`); names the Routines-vs-`claude routine create` divergence from the conference research §1 #4; explains when to compose Routines (async-work-then-resume background dispatches) and when not (sync foreground dispatches). `outcome-altitude: false` (memory file is documentation, not user-invokable surface).
- **AC.V040C3.2 — 1 example plan-doc invokes the verified-live Routines surface.** `docs/plans/example-routines-runtime-dispatch.md` exists; demonstrates a plan-doc that dispatches background work via `claude agents` (or `/schedule` SKILL when cron-scheduled); cross-reference resolves from the memory feedback file. `outcome-altitude: true` — the example must invoke a verified-live surface (not a hypothetical CLI verb).
- **AC.V040C3.3 — Plan-author SKILL gains "compose-on-claude-code-review" section.** `plugins/dev-sdlc/skills/plan-docs-author/SKILL.md` gains a section titled "Compose on Claude Code review primitives" or equivalent; section names the verified-live invocation shape (`claude ultrareview` + `/review` + `/security-review`); names the Code-Review-vs-`claude code review` divergence; names when-to-compose conditions (review-as-plan-step vs review-as-cycle vs hand-author review prose). `outcome-altitude: false` (SKILL guidance is documentation).
- **AC.V040C3.4 — 1 example plan-doc demonstrates Code Review composition.** `docs/plans/example-code-review-composition.md` exists; demonstrates a plan-doc with a `claude ultrareview` (or `/review` / `/security-review`) plan-step; cross-reference from the SKILL section resolves. `outcome-altitude: true` — the example must invoke a verified-live surface.
- **AC.V040C3.5 — Outcomes ADR exists at `docs/design/odd-vs-outcomes.md`.** ADR names ODD as authoring-time discipline (objective + constraints + AC at plan time) + Outcomes as runtime grader (rubric scoring at execute time); documents stack-when-both-available shape; names BYOK-vs-subscription divergence as **deliberate architectural choice with rationale per `feedback_no_anthropic_api_key.md`** (NOT a deficiency); cross-references `release-roadmap.md` §3 v0.4.0 AC.V040.5 + the `feedback_no_anthropic_api_key` memory file. `outcome-altitude: false` for the doc-existence AC; `outcome-altitude: true` for AC.V040C3.6 below which verifies the cross-reference resolution.
- **AC.V040C3.6 — All previously-passing tests still pass + F2 enhancement validated.** All 26 C1+C2 ACs still pass; `len(diff.commits)` print-on-success added at the end of the C2 outcome-altitude test (per C2 build report F2 finding #2); ADR cross-references resolve from `docs/release-roadmap.md` §3 v0.4.0 entry (verified at seal time). `outcome-altitude: true` — the cross-reference resolution is the documented-deliverable-surface AC the master plan §3 named.

**Outcome-altitude ACs:** AC.V040C3.2, AC.V040C3.4, AC.V040C3.6 are marked `outcome-altitude: true`. The cycle is doc/SKILL/ADR work; outcome-altitude is "the cross-reference resolves from the canonical entry-point" + "the example invokes a verified-live surface (not a hypothetical CLI verb)." Per `odd-test-altitude-discipline` SKILL: this is a release-gate-HARD risk band (pure documentation surface; no production-facing CLI / config / persistence change), so per-cycle HARD verification is not required — the C5 release-level smoke gate verifies cross-reference resolution as part of the §3 → §2 collapse.

## §5 — Halt-and-surface BEFORE build (recorded autonomous decisions)

1. **WD verified.** `pwd` returned `/Users/lukeivers/ivers-corp-pos-v2/` per dispatch directive's literal `cd` first action. No mismatch.
2. **Predecessor seals verified.** `git log --oneline -3` confirms `f031c89c` (C2 seal) at HEAD; `cc2efbba` (C1 seal) at HEAD~3.
3. **`claude --help` verification at C3 dispatch time (per master plan §10.3 RF gap).** Verified against `claude --version` `2.1.128 (Claude Code)` at dispatch time. **HALT-AND-SURFACE FINDING:** the conference research at §1 #4 named the Routines CLI as `claude routine create`; actual `claude --help` at HEAD shows NO `routine` subcommand. The Routines capability is exposed via:
   - `claude agents` subcommand ("Manage background and configured agents") — for ad-hoc background agents.
   - `/schedule` SKILL ("Create, update, list, or run scheduled remote agents (routines) that execute on a cron schedule") — for cron-scheduled Routines per the docs site.
   Conference research §1 #5 named the Code Review CLI as `claude code review` and `claude code security review`; actual `claude --help` at HEAD shows NO `code` subcommand. The Code Review capability is exposed via:
   - `claude ultrareview` subcommand ("Run a cloud-hosted multi-agent code review of the current branch (or a PR number / base branch) and print the findings") — for cloud-hosted multi-agent review.
   - `/review` SKILL ("Review a pull request") — for in-session PR review.
   - `/security-review` SKILL ("Complete a security review of the pending changes on the current branch") — for security-specific review.
   - `/ultrareview` SKILL — surface-level wrapper around the CLI subcommand.
   **Resolution (autonomous per dispatch's "halt-and-surface for owner ratification on doc-vs-reality fix"):** the conference research described the documentation site at `code.claude.com/docs/en/routines` and `code.claude.com/docs/en/code-review`; the docs may use one naming convention, the shipped CLI another. C3's deliverables compose on the **verified-live surface** (`claude agents`, `claude ultrareview`, `/schedule`, `/review`, `/security-review`) and document the divergence honestly per F2 RF. Future research updates may resolve which name is canonical at the docs altitude; for v0.4.0 ship, verified-live wins. This is consistent with `feedback_trust_operational_reality` (prefer machine-empirical evidence over secondary-source citations) and `feedback_specific_claims_verified_or_marked_guess` (every CLI claim verified against `claude --help`).
4. **Memory feedback file path canonicalization (per master plan §10.3 RF #3).** Authored at `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_routines_runtime_layer.md` per pos3-local convention (matches the existing 30+ feedback files at that path). Loam-canonical path may differ post-v0.5.0 once cross-workspace memory rules ship; for v0.4.0, pos3-local is the verified-live surface.
5. **Outcomes ADR tone confirmed deliberate** (per master plan §10.3 RF #4 + harness-landscape research §4 Tension #1): the BYOK-vs-subscription divergence is named as a deliberate architectural choice rooted in `feedback_no_anthropic_api_key.md`, NOT a deficiency. Translation-burden-reduction story per VALUE_PROPOSITION: subscription-only architecture means loam works for the subscription audience without API-key onboarding friction.
6. **AC.V040C3.5 (folded F2-from-C2) confirmed in scope.** Adds a single print line at end of `test_AC_V040C2_1_outcome_altitude.py`; AC-aligned; small / cosmetic; falls within the C2 component sub-fence per universal admissions discipline (test edit AC-aligned to a named AC, no production-code change).

## §6 — Smoke (REALISTIC CONDITION — applicable dimensions per smoke-test-discipline)

- **D1 cold-state.** N/A structurally — C3 is doc/SKILL/ADR work; no fresh-clone state to verify (no new CLI / no new config / no new persistence).
- **D2 steady-state.** Verified by greps at seal time:
  - `grep -n "claude agents\|/schedule" docs/plans/example-routines-runtime-dispatch.md` returns ≥1 hit (verifies AC.V040C3.2).
  - `grep -n "claude ultrareview\|/review" docs/plans/example-code-review-composition.md` returns ≥1 hit (verifies AC.V040C3.4).
  - `grep -n "Compose on Claude Code review" plugins/dev-sdlc/skills/plan-docs-author/SKILL.md` returns the new section heading (verifies AC.V040C3.3).
  - `find docs/design -name "odd-vs-outcomes.md"` returns one file (verifies AC.V040C3.5).
  - `ls ~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_routines_runtime_layer.md` returns the new file (verifies AC.V040C3.1).
  - C1+C2 ACs still pass: `pytest plugins/dev-sdlc/odd-extractor/tests/test_AC_V040C1_*.py` returns `25 passed` (verifies AC.V040C3.6 no-regression).
  - The C2 outcome-altitude test stays runnable (its `len(diff.commits)` print is the only delta; not re-run at C3 seal time per `feedback_amendment_dispatch_speedups` "skip pre-seal full rerun for outcome-altitude class" — the addition is a print-on-success at end of test body that cannot regress the existing assertions).
- **D3 process-restart.** N/A — no daemon / long-running process.
- **D4 reboot.** N/A — no cross-reboot persistence change.
- **D5 cross-session.** N/A — no session-state mechanism touched.
- **D6 telemetry-floor.** Verified — every new file is grep-discoverable by its named markers (verified-live CLI verbs); plan-doc cross-references resolve.

Full-suite green sweep clause: `pytest plugins/dev-sdlc/` returns all-pass at seal time. Per `feedback_amendment_dispatch_speedups` "narrow test scope" speedup: pre-seal rerun limited to C1+C2 AC tests (the only suite touched by AC.V040C3.5's print enhancement); component sweep tests run via `loam amend seal` per the standard ladder.

## §7 — Out of scope

- Multi-Agent / Dreaming / Webhooks substrate composition (API-keyed; OUT OF SCOPE per `feedback_no_anthropic_api_key.md`).
- Routines as a structurally-enforced loam primitive (v0.7.0 structural-enforcement substrate per master plan §9).
- Code Review composition beyond the named SKILL guidance + 1 example (additional examples may land as separate cycles or via FIDRAFT).
- BYOK divergence beyond the Outcomes-pattern ADR (T7 tension surfaced in harness-landscape research §4; F2 RF only at v0.4.0).
- Conference-research naming reconciliation (whether docs-site or shipped-CLI is canonical) — out of scope; documented as divergence; future research may revisit.
- Memory feedback file canonicalization across workspaces — pos3-local for v0.4.0; cross-workspace memory rules deferred to v0.5.0+.

## §8 — Halt triggers (in-flight)

- C3 actual AI-time exceeds 90 min upper band by >50% (>135 min) — surface for owner ruling on scope split or carry to v0.4.1.
- AC family count grows beyond seed (>8 ACs) — ODD §2.5 violation triage; re-extend.
- `loam amend seal` fails on dirty working tree (per C2 F2 finding #1) — apply the C2 resolution (`git stash push --include-untracked`, run seal, `git stash pop`); not an in-cycle blocker.
- Push or `--amend` attempt — immediate halt; corrective NEW commit + RF surface per `feedback_no_amend_in_agent_dispatches`.
- Subscription-only invariant violated (any deliverable references `ANTHROPIC_API_KEY` or `pip install anthropic` as load-bearing) — immediate halt.

## §9 — Bookkeeping

- pos-amend usage: `loam amend apply --plan-doc <abs-path>` then `loam amend seal --plan-doc <abs-path>` per `loam-amend-cycle` SKILL.
- Manifest schema v3 per `loam amend validate`.
- Commit ladder shape (per the standard 5-commit ritual minus optional §14-backfill in-cycle):
  1. `docs(plans): v0.4.0 Cycle 3 — substrate composition (plan-doc finalized + manifest + deliverables)` (single semantic commit per AC.DPS1.6; carries plan-doc + manifest + the four NEW files + the test print enhancement + the SKILL section).
  2. `chore(amend): v0-4-0-cycle-3-... manifest+apply` (from `loam amend apply`).
  3. `chore(seals): v0-4-0-cycle-3-... — dev-sdlc at <SHA>` (from `loam amend seal`).
- §14 backfill: deferred to v0.4.0 ship per C1+C2 precedent (single batch commit at C5 covers all 5 cycles).
- Master-plan §11 SHA register row update: deferred to C5 backfill.
- Tag-push policy: NO push, NO tag, NO Release. v0.4.0 ships as a unit at C5 per dispatch directive.

## §10 — F2 Ruthless Feedback (gaps named this turn)

1. **Conference research naming divergence is a wider F2 surface than C3 covers.** Conference research §1 #4 + #5 named CLI verbs that don't exist at HEAD; resolved here by composing on the verified-live surface. **But the conference research itself is now stale at the named-verb altitude.** Mitigation: this plan-doc names the divergence inline; deliverables document it; future research updates may revisit which naming is canonical. C3 doesn't fix the research artefact; that's separate work.
2. **The `feedback_routines_runtime_layer.md` file is loaded only when pos3-local memory rules apply.** Other workspaces (e.g., a stranger running `claude` in a fresh loam dev-mode workspace) won't see the file. Mitigation: cross-reference from `CLAUDE.md` is OUT OF SCOPE per the master plan §3 C3 universal-admissions list; future v0.5.0+ cross-workspace memory rules may surface a shared path. Surfaced for owner awareness; not blocking C3.
3. **Example plan-docs are illustrative, not consumed by sealed components.** Their cross-reference resolution (AC.V040C3.2 + AC.V040C3.4 outcome-altitude) verifies against grep, not against `loam` execution. This matches the master plan §3 C3 D2 smoke shape — but the user-facing translation-burden-reduction is "the example shows how to invoke the surface," not "the example actually runs." Authentic outcome-altitude verification of Routines + Code Review composition would require running `claude agents` / `claude ultrareview` against a real fixture; that's deferred to v0.5.0+ if the substrate composition becomes load-bearing for a downstream cycle. Surfaced for owner awareness.
4. **AC.V040C3.5 print-on-success is a single line; it can't regress** but the seal-time `loam amend seal --scoped-sweep` does run the C2 test as part of `dev-sdlc` component sweep — wall-clock cost ~7 min if the outcome-altitude test is in-scope for the sweep. Mitigation: the seal sweep targets the dev-sdlc seal_test (`tests/test_no_sealed_amendments.py`), NOT the per-AC tests directly; the print-on-success addition does not affect the seal-test outcome. Surfaced for awareness; `loam amend seal` invocation is the empirical check.
5. **The Outcomes ADR's stack-when-both-available story may oversell the integration path.** Subscription-only loam users CAN'T stack Outcomes (it's API-only). The "stack when both surfaces available" guidance is for the small intersection of users who run both subscription-loam AND a separate API-key Anthropic project. Mitigation: ADR explicitly names this audience scope in the "stack" section — it's a niche guidance, not a primary recommendation.

## §11 — Provenance trail

- Master plan §3 Cycle 3 entry — locked source-of-truth for AC.V040.2/.3/.5 mapping.
- `docs/release-roadmap.md` §3 v0.4.0 lines 86, 93, 94, 96 — verbatim AC text for V040.2, V040.3, V040.5.
- `<workspace>/.scratch/claude-output/claude-conference-features-2026-05-06.md` §1 cells #1, #4, #5 + §3 Lens-1 alignment table + §4 AI-time bands — the reference artefact whose CLI-verb names diverged from `claude --help` at HEAD; documented in §5 resolution + each deliverable.
- `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-4-0-cycle-2-build-report.md` §F2 RF #2 — source of AC.V040C3.5 (folded F2-from-C2 print-on-success enhancement).
- `feedback_no_anthropic_api_key.md` — source of subscription-only architectural commitment that motivates the Outcomes ADR's BYOK-divergence-as-deliberate-choice framing.
- `feedback_specific_claims_verified_or_marked_guess.md` — drives the `claude --help` verification step at §5.
- `feedback_trust_operational_reality.md` — drives "verified-live wins over secondary citation" resolution at §5.
- `plugins/dev-sdlc/skills/plan-docs-author/SKILL.md` (existing pre-C3) — skill being extended in AC.V040C3.3.
- `plugins/dev-sdlc/skills/odd-test-altitude-discipline/SKILL.md` — outcome-altitude AC discipline applied to §4.
- `plugins/dev-sdlc/odd-extractor/tests/test_AC_V040C2_1_outcome_altitude.py` (sealed at f031c89c) — site of AC.V040C3.5 print-on-success enhancement.

## §12 — Acceptance gate (pre-cycle conditions)

- [x] WD verified `/Users/lukeivers/ivers-corp-pos-v2/`.
- [x] Predecessor seals verified (`cc2efbba` C1, `f031c89c` C2 at HEAD).
- [x] Plan-doc finalized (this commit lands plan-doc + manifest + deliverables).
- [x] AC family locked (6 ACs; ≥3 outcome-altitude per `odd-test-altitude-discipline`).
- [x] Smoke dimensions covered (D2 verified + D6 verified; D1/D3/D4/D5 N/A with rationale).
- [x] Bookkeeping discipline named (loam-amend-cycle ladder; NO `--amend`; NO push/tag/Release).
- [x] §10 F2 RF surfaces ≥3 honest doubts.
- [x] §8 halt triggers named.
- [x] `claude --help` verified at dispatch time (§5 finding documented).
- [x] HARD HALT BEFORE PUBLIC ACTIONS — local-only seal; no push, no tag, no Release.

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

| Decision | Choice | Rationale |
|---|---|---|
| Compose on verified-live CLI surface (not conference-research-named verbs) | `claude agents` + `/schedule` for Routines; `claude ultrareview` + `/review` + `/security-review` for Code Review | `feedback_trust_operational_reality` + `feedback_specific_claims_verified_or_marked_guess` — empirical machine evidence wins over secondary citation. |
| Single semantic commit for plan-doc + deliverables | One `docs(plans):` commit covering plan-doc finalization + manifest + 5 NEW files + 1 print-on-success edit | Per `loam-amend-cycle` step 4 + AC.DPS1.6 (apply collapses to one semantic commit); plan-doc + deliverables cohere as a single cycle's authoring discipline. The C2 source-edit feat commit pattern doesn't apply here because no production code changes (only docs + SKILL prose + 1-line test print). |
| Memory feedback file location | pos3-local at `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_routines_runtime_layer.md` | Convention matches 30+ existing feedback files. Cross-workspace memory rules deferred to v0.5.0+. |
| Bundle 3 deliverables into 1 cycle (vs 3 sub-cycles) | Bundled per master plan §3 C3 rationale (Lens 5 stopping criterion) | Each individually 15–30 min; per-AC sub-cycles add coordination overhead with no AC tightening. Ratified at master-plan altitude. |
| Outcomes ADR framing | Deliberate architectural choice with rationale, NOT deficiency | Per harness-landscape §4 Tension #1 + `feedback_no_anthropic_api_key`; subscription-only is the architectural floor. |
| AC count = 6 (vs 5 in dispatch + 5 in stub seed) | Adopt 6: split AC.V040C3.6 from AC.V040C3.5 in the dispatch | Dispatch's AC.V040C3.5 conflated "tests still pass" + "F2 print-on-success added" + "ADR cross-references resolve" into one AC; splitting cleanly separates regression-check (no-regression) from cosmetic enhancement from outcome-altitude cross-reference resolution. The dispatch's stub seed in the plan also had 6 ACs; alignment preserved. |
| Outcome-altitude AC count = 3 (AC.V040C3.{2,4,6}) | Plan-author authored | Per `odd-test-altitude-discipline` SKILL — pure-documentation surface is release-gate-HARD risk band; per-cycle HARD not required; ≥1 outcome-altitude AC required per `feedback_test_outcome_altitude_required`; 3 named for cross-reference resolution clarity. |
| `--scoped-sweep` for `loam amend seal` | Default scoped to dev-sdlc component | Per `feedback_amendment_dispatch_speedups` "narrow test scope"; AC.V040C3.5 print enhancement is single-line + AC-aligned + cannot regress existing assertions. |
| Skip pre-seal full repo rerun | Adopt | Per `feedback_amendment_dispatch_speedups` second speedup; touched test surface is exclusively C2 outcome-altitude test (cosmetic print only); no production code changed. |
| Test edit (C2 component) admitted under universal-paths | Admit per AC-alignment rule | The C2 test is in the dev-sdlc component fence; the print-on-success edit is AC-aligned to AC.V040C3.5 (folded F2-from-C2); per amendment #22 universal-admissions discipline this is permissible. |

### Post-seal SHA register

| Commit | SHA |
|---|---|
| Plan-doc + deliverables commit | (pending) |
| Apply commit | (pending) |
| Seal commit | (pending) |
| §14 backfill commit | (deferred to v0.4.0 ship) |
