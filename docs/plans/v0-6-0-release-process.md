# v0.6.0 minor — concrete release process

**Status:** plan-only at authoring time. Plan-before-code per `feedback_plan_before_code` (hard rule). Owner ratifies before any cycle dispatches.
**Slug:** `v0-6-0-release-process`
**Date authored:** 2026-05-09. **Revised** 2026-05-09 — class re-derived MINOR (originally v0.4.5 PATCH); branch `pos-v2` → `main` (split-worktrees move retired the pos-v2 branch); remote `loam` → `origin` (fresh clone uses `origin`); slug `v0-4-5-release-process` → `v0-6-0-release-process`; AC IDs `V045.{1-7,S}` → `V060.{1-7,S}`.
**Class:** MINOR (new outcome shape: structural release ritual + post-ship-review step). Per Q2 ratification (Telegram 10570; class is suggestive on roadmap; plan-author rules at build-time).
**Predecessor:** v0.5.1 (split-worktrees + Phase 1 cleanse) — published.
**Working directory:** `/Users/lukeivers/loam/`.
**Owner authorization:** Telegram 10547 ("having a concrete release process is much safer; let's add that to the roadmap sooner rather than later so later work can use it").

---

## §1 — Outcome shape (the "why")

Today's v0.4.3 publish (2026-05-09) was figured-out-as-I-went after the dispatcher discovered `pos-publish-framework-only` was archived (commit `ea8c4bbd`, OSS-architecture migration). Investigation steps required: read canonical state, verify remote tag inventory via `git ls-remote --tags origin` (and notice the `head -10` truncation that misled the first calibration), identify the architecture-migration shape (direct-push to `origin/main` rather than synthesis branch), then execute manually.

That workflow recurs on every future publish. It's the exact failure shape that bites at the wrong moment — when the publish is time-pressured (e.g., a hotfix), or when the dispatcher is a different session/persona that doesn't have today's investigation context. Codifying both a runbook (rule-shape; for the human gate) and a CLI verb (structural; for the mechanical execution) closes the gap.

The structural shape per `Structural enforcement default` Lens: a CLI verb beats a runbook because the CLI gates publish on verifiable preconditions (HARD smoke GREEN, all ACs verified, etc) while a runbook relies on the dispatcher remembering to check.

## §2 — Prime objective ladder

VALUE_PROPOSITION.md prime objective (loam helps people use LLMs to **build software**) → reliable release process is part of the harness toolkit the primary persona draws from → without it, every publish has dispatcher-recall risk + investigation tax → v0.6.0 ACs (V060.{1-7} + S) implement the CLI + runbook + dogfood.

## §3 — Component fence

**PRIMARY:** `framework/tools/loam/` — extends the existing `loam` top-level CLI (currently has `amend` and `project` subcommands per `loam --help`). Adds `release` subcommand.

**Secondary:** `docs/release-process.md` — new runbook doc (top-level under `docs/`, sibling to `release-roadmap.md`).

**Untouched:** All other components. No edits to existing publish-adjacent code (the archived `pos-publish-framework-only` stays archived; the new CLI doesn't resurrect synthesis-branch logic — direct-push is the new architecture).

## §4 — Acceptance criteria

### AC.V060.1 — `loam release` CLI verb

**What:** New `loam release <version>` subcommand. Accepts `--dry-run` (verifies preconditions + reports without acting) and `--release` (creates GitHub Release in addition to tag/push).

**Acceptance:** CLI registers under `framework/tools/loam/` (new subpackage `loam_cli/release/`); `loam release --help` produces usage; integration test verifies subcommand dispatch.

### AC.V060.2 — Structural pre-publish gates

**What:** CLI verifies before pushing:

1. HARD smoke GREEN for the named version (reads `docs/experiments/<version>-hard-smoke.md`; pattern: file exists + contains "GREEN" verdict).
2. All ACs verified per plan-doc §status (reads `docs/plans/<version-slug>.md`; pattern: each AC has GREEN verdict in §verdict-matrix or equivalent).
3. STATE.md updated to mark version SHIPPED (reads `docs/STATE.md`; pattern: §2-shipped row exists for the version).
4. No uncommitted changes in canonical (`git status --porcelain` returns empty).
5. Current branch is `main` (`git branch --show-current` returns `main`).
6. Seal commit exists for the version (`docs/release-roadmap.md` §2 row contains seal SHA; that SHA is reachable from HEAD).

**Acceptance:** Each gate failure surfaces a specific corrective hint (not a generic error). Per-gate test: each precondition has a passing test (precondition met) and a failing test (precondition violated → expected hint surfaces).

**Builder note:** Path A — single CLI module with per-gate functions. Path B — pluggable gate registry with each gate as a separate file. Default A unless complexity warrants B. _Builder rules at build time per D-V060.2._

### AC.V060.3 — Tag + push action

**What:** CLI tags the seal commit with annotated tag (message = version + objective sentence from roadmap), pushes branch + tag to `origin` remote.

**Idempotency:** Re-running on already-published version produces no-op + clear message ("v0.X.Y already on origin remote at <SHA>; nothing to do").

**Acceptance:** Integration test against a local fake remote verifies (a) tag created with correct annotation, (b) `git push` invoked correctly, (c) re-run is no-op.

### AC.V060.4 — Optional GitHub Release with auto-generated notes

**What:** `--release` flag invokes `gh release create <tag>` with notes auto-generated from:

1. Plan-doc §1 outcome shape (the "why").
2. Plan-doc §status (per-AC verdicts).
3. Commit log between previous version's seal SHA and this version's seal SHA (`git log --oneline <prev-seal>..<this-seal>`).

**Acceptance:** Test verifies generated notes contain (a) version objective sentence, (b) AC verdict matrix, (c) commit log section. Integration test (mocked `gh` invocation) verifies command shape.

### AC.V060.5 — Release-process runbook

**What:** New doc at `docs/release-process.md`. Sections:

1. Pre-publish gates (lists what gets checked).
2. The `loam release` invocation (canonical command sequence + flags).
3. Post-publish state (what's now true; what to check next).
4. Manual fallback (if CLI is unavailable: the explicit `git tag` + `git push origin main` + `git push origin <tag>` ritual; matches today's manual ritual for back-compat).

**Acceptance:** Doc exists at canonical path; covers all 4 sections; reviewable in 5 minutes; cross-references the CLI's `--help` output.

### AC.V060.6 — Post-ship review + next-scope decision

**What:** After a successful publish, the CLI fires an autonomous review step (per Q4 ratification Telegram 10577 + the scope-decision discipline per Telegram 10629 + the major-release-shape ratification per Telegram 10633):

1. **Re-evaluate roadmap priorities.** Read `docs/release-roadmap.md` §4 (priority queue), `docs/FUTURE_IDEAS_DRAFT.md` recent captures, recent halt-and-surface findings, and goal-alignment scoring. Re-rank if priorities have shifted.
2. **Decide the next scope.** Pick the next bounded purpose from the queue. Name what's IN that scope (one-sentence objective + named ACs or fence). Name the class (PATCH / MINOR / MAJOR) per the work shape, not by pre-assignment. The decision becomes the next cycle's contract; commits accumulate locally on `main` until that scope completes; next publish ships when that scope's done.
3. **Major-release eval.** Pre-1.0: never cut a major; the answer is always PATCH or MINOR (or the v1.0 quality-bar event itself per `release-versioning-policy.md` §1.0.0). Post-1.0: check whether cumulative state since the last major warrants a major boundary (accumulated breaking changes, significant capability shift, plugin-contract revision per the policy doc); if yes, surface to owner with the trigger evidence.
4. **Surface the decision to owner** in the post-publish output. Owner ratifies the scope (or revises) before the next cycle's first commit.

**Why this AC:** versions are scope-of-work boundaries, not commit-frequency boundaries. Without this step, the post-publish moment risks two anti-patterns: (a) over-versioning (every doc edit gets a tag — version inflation), (b) under-defining (commits accumulate without a named purpose — drift).

**Acceptance:** CLI's post-publish output includes a "Next-scope proposal" block naming objective + class + fence + named ACs. Test: a real publish run produces the block; manual review confirms the scope-decision shape matches the policy.

### AC.V060.7 — Outcome-altitude AC: dogfood v0.6.0 publish

**What:** v0.6.0 itself ships using the new `loam release` CLI (publish + post-ship review). The v0.6.0 publish IS the outcome-altitude test.

**Acceptance:** Build report records the dogfood verdict — CLI succeeded against all gates; tag + push landed; runbook reference matched actual ritual; post-ship review block surfaced + named the next scope. If CLI fails on dogfood, halt-and-surface as F-DESIGN candidate (the design itself didn't survive first-real-use).

`outcome-altitude: true` per `feedback_test_outcome_altitude_required`.

### AC.V060.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under:

- `framework/tools/loam/` (CLI subcommand registration + new `release/` subpackage + tests)
- `docs/release-process.md` (new file)
- `docs/release-roadmap.md` (§2 row added for v0.6.0; §3 active-version updated)
- `docs/STATE.md` (v0.6.0 SHIPPED rollup)
- `docs/plans/v0-6-0-release-process.md` (rename + revision; §status backfill on this file post-seal)

Sidecar advances per sealed-component-cycle ritual.

## §5 — Constraints (load-bearing)

1. **Composes with `loam amend apply` seal flow** — the seal commit IS the publish input. No new seal mechanism.
2. **Composes with `feedback_hard_smoke_per_minor_before_publish`** — HARD smoke gate is a structural pre-publish prereq enforced by AC.V060.2.
3. **Composes with ASK-FIRST on public actions** — the publish action is owner-invoked (the dispatcher runs `loam release <version>` only after explicit owner authorization); the CLI does NOT auto-publish.
4. **Composes with the soft-halt rule** — publish soft-halts the named version's thread on owner ratification per ASK-FIRST class.
5. **No new external service dependencies** — uses `git push` (already required for the workflow) + optional `gh release create` (already installed on maintainer's machine; `--release` flag opt-in only).
6. **No public action during build** — `loam amend apply --dry-run` green is hard prereq + hard post-apply gate. No `git push`, no `git tag` from the build agent itself.
7. **Plan-before-code** — this plan-doc lands BEFORE source edits.
8. **ODD §2.5 + §2.4** — every line of code maps to a named AC. No method-in-AC. No "options to rule on" framing.
9. **Outcome-altitude AC requirement** per `feedback_test_outcome_altitude_required.md` — AC.V060.7 is the outcome-altitude probe (dogfood v0.6.0 publish using the new CLI).
10. **Subscription-only** — no Anthropic API key references.
11. **`claude -p --strict-mcp-config`** — the new CLI does NOT invoke `claude -p` (it's a deterministic git-tag-push + gh-release CLI; no LLM routing). If a future extension adds LLM-routed release-notes auto-summary, that extension carries the strict-mcp-config + empty MCP config tempfile.

## §6 — Out of scope (explicit)

- **Multi-remote publish** — only `origin` remote per the current architecture. Multi-remote (e.g., publishing to a mirror) is FIDRAFT-able if it ever becomes needed.
- **Pre-publish HARD smoke EXECUTION** — the gate VERIFIES that smoke ran GREEN; it doesn't run the smoke itself. Smoke runs as part of the build cycle per existing `feedback_hard_smoke_per_minor_before_publish` rule.
- **Auto-version-bump** — the CLI takes the version as arg; doesn't compute the next version automatically. SemVer policy per `docs/release-versioning-policy.md` is dispatcher-side discipline.
- **Rollback / unpublish** — no `loam release --rollback`. If a published version needs rollback, it's a separate operation (manual `git push --delete` + new fix-up version). FIDRAFT if recurring need.
- **Notification (email / Slack / Telegram on publish)** — not in v0.6.0 scope. Captured for FIDRAFT.

## §7 — HARD HALTs (build-time)

Halt-and-surface to dispatcher (return owner-call) — do NOT proceed past — on any of:

1. AC.V060.7 dogfood publish RED (CLI fails against any pre-publish gate during the v0.6.0 publish itself). Halt; surface as F-DESIGN candidate (the design itself didn't survive first-real-use).
2. ODD §2.5 violation in your work OR surrounding code (per `feedback_subagent_odd_violation_halt`).
3. Wrong-tree-write (any edit lands at a path outside `/Users/lukeivers/loam/`).
4. Any reach for `--amend`. Immediate halt.
5. Any reach for `git push`, `git tag` from the build agent itself (publish is dispatcher-action via the new CLI, not builder-action). Immediate halt.
6. AI-time exceeds upper band (160 min) by >50% → 240 min wall-clock. Halt with current state.
7. Schema/architecture change to existing `loam amend` flow appears necessary. Halt — out-of-scope per §6.

## §8 — Decisions builder rules at build time

- **D-V060.2** (CLI module shape): default Path A (single module with per-gate functions). Switch to Path B (pluggable gate registry) only if complexity demonstrably warrants. Document chosen path + reasoning in build report.
- **D-V060.4** (auto-generated release notes shape): default = plan-doc §1 + §status + commit log. If commit log is too noisy (e.g., includes §14 backfill + manifest-bump churn), filter to feat/fix/docs commits only.
- **D-V060.5** (runbook depth): default = 1-page reference (4 sections). Switch to longer onboarding-tutorial shape only if first reader signals confusion.

## §9 — Dependencies

- **v0.5.1 (split-worktrees + Phase 1 cleanse)** — HARD on commit-graph (v0.6.0 builds on v0.5.1's HEAD).
- v0.5.0 (subagent-personas routing) — published; no direct fence overlap.
- No external service dependencies.

## §10 — Estimated AI-time

| Stage | Band | Midpoint |
|---|---|---|
| Plan-doc authoring (this file) | 15-25 min | 20 min |
| Plan-doc revision (slug + branch + remote) | 5-10 min | 7 min |
| CLI verb + tests | 45-75 min | 60 min |
| Runbook doc | 15-30 min | 22 min |
| HARD smoke + dogfood publish | 15-30 min | 22 min |
| **Total v0.6.0 build** | **95-170 min** | **~131 min** |

Per `feedback_duration_estimation_rubric` — single-component minor + dogfood probe; midpoint ~131 min.

Owner gate-review separate (ratify plan-doc shape before build dispatch + ratify dogfood publish per ASK-FIRST).

## §11 — Open questions for owner ratification

1. **Path A (CLI verb) + Path B (runbook doc) bundle vs split.** Plan-doc bundles both into v0.6.0. Alternative: ship runbook as v0.5.x (immediate; covers today's gap with a reference doc), CLI as v0.6.0 (structural; follows when runbook validates the design). My call: **bundle**, because runbook-only is the rule-shape Luke explicitly rejected as "discipline that won't survive."
2. **AC.V060.4 GitHub Release inclusion** — opt-in via `--release` flag. Alternative: Release creation is mandatory part of every publish. Recommend opt-in (matches current state where v0.1.0 → v0.4.3 don't have Release pages on GitHub; backward-compat).
3. **AC.V060.7 dogfood timing** — v0.6.0 publish IS the test (per AC). Alternative: ship without dogfood, dogfood lands at v0.6.1's publish (one-version delay reduces risk). Recommend dogfood, because the outcome-altitude rule (`feedback_test_outcome_altitude_required`) requires the AC to test the user-visible outcome; non-dogfood would be STUB-class.
4. **CLI subcommand naming** — `loam release` vs `loam publish`. Both are reasonable. Recommend `loam release` because "release" is a noun + matches GitHub Release vocabulary; "publish" reads as a verb-only action. Either is OK; surface for explicit ratification.

## §12 — Authority chain

- Telegram 10547 (owner directive for the work itself).
- Telegram 10570 (Q2 ratification: class is suggestive on roadmap; plan-author rules at build-time).
- Telegram 10629 (scope-decision discipline).
- Telegram 10633 (major-release-shape ratification; pre-1.0 never cuts major).
- Memory rule `feedback_hard_smoke_per_minor_before_publish.md` (HARD smoke gate codification this CLI enforces structurally).

## §13 — §status (post-build backfill)

(Filled in at end of build cycle — per-AC verdict matrix, commit SHAs, dogfood verdict, AI-time actuals.)
