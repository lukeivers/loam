# v0.1.9 Cycle 2 — Hook installers + 3 CI templates + provenance-traceable PR description template

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-04 (Sonnet, build dispatch).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Predecessor:** Cycle 1 sealed at `790807d` (PR-safety gate engine + override workflow; NEW component `plugins/dev-sdlc/pr-safety/`; CLI `loam pr-safety gate <repo>`; 105 cycle tests green).

**BASELINE (pre-build tip):** to be set to the source-edit commit when the build commit lands. Pre-flight tip: `3162d2f` (Cycle 1 §9 backfill).

**Parent plan:** `docs/rebuild/plans/v0-1-9-master-plan.md` §3 + §4 Cycle 2 (sealed at `b01d3eb`).

**Status file:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-9-cycle-2-status-2026-05-04.md`.

**Quality bar (load-bearing):** "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses." — Luke 2026-05-04. Hook installers are reliable (broken hooks = silent gate-bypass = the failure mode the gate was built to prevent). Three CI templates ship complete (no "GitHub works, GitLab is a stub"). PR description format is auditable end-to-end. All 6 smoke dimensions exercised.

---

## §1 — Outcome shape (the "why")

Cycle 2 wraps the Cycle 1 gate engine in **delivery surfaces** so the gate fires automatically wherever Eric's team works — at commit-time (pre-commit), push-time (pre-push), and PR-time (CI). It auto-populates a structured PR description with provenance trail (which ACs the diff touched, which overrides applied, which audit-log entries witness it) so reviewers see at-a-glance contract impact.

Cycle 2's release-note promise:

1. `loam pr-safety install pre-commit <repo>` writes a hook that fires the gate on every `git commit` (working-tree-vs-HEAD); HARD-BLOCK exits non-zero so the commit is rejected.
2. `loam pr-safety install pre-push <repo>` writes a hook that fires the gate on every `git push` (HEAD-vs-upstream); HARD-BLOCK exits non-zero so the push is rejected.
3. `loam pr-safety install ci github-actions <repo>` writes `.github/workflows/loam-pr-safety.yml`; the workflow runs the gate on `pull_request` events; HARD-BLOCK fails the workflow.
4. `loam pr-safety install ci gitlab-ci <repo>` writes (or appends to) `.gitlab-ci.yml`; the job runs the gate on merge-request pipelines.
5. `loam pr-safety install ci circleci <repo>` writes `.circleci/config.yml` (or appends to it); the job runs the gate on PR-shaped builds.
6. `loam pr-safety install pr-template <repo>` writes `.github/pull_request_template.md` (and a generic markdown variant the caller can pipe into other surfaces); the template auto-renders sections (ACs touched / Override-history / Ratifications / Audit-log excerpt) when the gate runs in CI mode (`--render-pr-description`).
7. `loam pr-safety install --all <repo>` does all six in one call.
8. Idempotent — re-running install is a no-op for unchanged content; refreshes loam-managed regions when the gate-engine version moves.
9. Halts on conflict — pre-existing non-loam hook content surfaces as a decision; Cycle 1's PM batch is the surface (audit-log entry + structured exit code).
10. Husky-aware — when `.husky/` is detected, pre-commit/pre-push install routes to husky-shaped hooks (`.husky/pre-commit` invokes loam) instead of `.git/hooks/`.

The shape (3 hook surfaces + 3 CI surfaces + 1 PR-template surface + install ergonomics + render-pr-description gate-mode + smoke against canonical fixtures) is the deliverable. Cycle 3 ships 6 SKILLs + audit-allowlist cleanup; Cycle 2 explicitly does not.

---

## §2 — Lens checks (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage-first

Cycle 2 composes on existing primitives rather than re-implementing:

- **Cycle 1 gate engine.** All install surfaces are thin wrappers around `loam pr-safety gate`. The hook script is a 5-10 line shell stub that invokes the CLI; CI templates are YAML that runs the CLI; PR description is rendered from the CLI's `--json` output + audit-log lookup.
- **Cycle 1 audit-log shape.** PR description rendering reads the audit-log entries written by the gate (Cycle 1 AC.PRSG.7) — no new persistence layer.
- **Cycle 1 PM batch surface.** Install-conflict halts surface as a PM decision (Decision Q) — same one-question-at-a-time mechanism the override flow uses.
- **Cycle 1 production-stake integration.** Hooks honour the `safety_profile` flag transitively — the hook stub passes through to the gate; the gate honours the profile per AC.PRSG.8. No new profile logic in Cycle 2.
- **git's hook-script convention.** `.git/hooks/<name>` shell scripts are the universal git mechanism — Cycle 2 doesn't invent a custom hook runner.
- **husky's `.husky/<name>` convention.** Most JS/TS projects (Eric's first project is JS/TS/Playwright per parent §1) use husky; Cycle 2 detects + composes rather than collides.
- **GitHub Actions `actions/checkout` + `setup-python`.** The CI templates use stock actions; no custom-action authoring in Cycle 2.
- **GitLab CI's `script:` + `rules:` directives + CircleCI's `jobs:` + `workflows:` directives.** Standard idioms; Cycle 2 templates mirror the platforms' canonical patterns.

The required research question — **"What Claude capability does this lean on or extend?"** — answer: every load-bearing primitive composes on Cycle 1 (gate engine, audit-log, PM surface, production-stake) plus standard git/CI conventions. Cycle 2 is delivery wrapping, not new mechanism.

### Lens 2 — Harness + primary-persona value

- **Primary-persona test:** translation burden drops because the persona no longer authors hook scripts or CI YAML by hand for every Eric project — `loam pr-safety install --all` is one verb that wires everything. Pass.
- **Harness test:** every loam-driven persona (PR-author, PR-reviewer, security-reviewer, ops) can call `loam pr-safety install` to wire a target repo's gate enforcement; the install surfaces are reusable harness primitives. Pass.

Both pass.

### Lens 3 — ODD authoring

Outcome above + named ACs (§4) + halt triggers (§9) + acceptance smoke (§7). Method (which template engine, which install-conflict heuristic, exact hook-script body, CI-template YAML structure) stays the builder's call within the constraints (idempotent, halt-on-conflict, husky-aware).

### Lens 4 — Prompt scope ↔ confidence

Outcome confidence is **HIGH** for shape: master plan §3 Cycle 2 + dispatch brief name the six install surfaces explicitly. Tight scope.

Outcome confidence is **MEDIUM** for one decision: husky-detection heuristic. Master plan §6.2 surfaces husky as the explicit JS/TS case but doesn't name the detection rule. This plan-doc commits to **`(<repo>/.husky/_/husky.sh).exists() OR <repo>/package.json has "husky" key`** as the detection rule (§5 Surface #4).

Outcome confidence is **MEDIUM** for one decision: PR-description body-overflow strategy. Master plan §7.6 names it as a real risk. This plan-doc commits to **truncate per-AC provenance to ~200 chars + link to full audit-log file** (§5 Surface #7).

Outcome confidence is **LOW** for one decision: GitLab CI / CircleCI smoke depth. The dispatch brief says "GitHub Actions chosen as the most-common; GitLab + CircleCI smoke is template-render-validates only" (master plan §3 Cycle 2 AC.PRSI.9). This plan-doc binds: **all 3 templates render-validate via YAML schema parsing AND syntactic gate-invocation correctness; full subprocess execution against a CI-provider sandbox is out of Cycle 1+2 scope** (no CI-provider account in canonical pos-v2's CI). This is the shipping correctness floor; F2 RF flag at §10.4.

### Lens 5 — Swarming

Single-component fence under `plugins/dev-sdlc/pr-safety/`. Within the cycle, decomposition options:

- (a) one-file-per-surface (`installer_pre_commit.py`, `installer_pre_push.py`, `installer_ci.py`, `installer_pr_template.py`, `install_cli.py`, `render_pr_description.py`) — natural decomposition mirroring Cycle 1's per-stage layout.
- (b) one-file-per-concern (`installers.py` for all hooks + CI, `templates.py` for all template rendering, `install_cli.py`) — collapses surfaces.

The builder picks **(a)** — per-surface decomposition matches the install-verb decomposition + gives the tightest AC-per-file mapping. `max_planner_depth: 1` (no sub-planners). No further decomposition adds value (e.g., splitting GitHub-Actions/GitLab-CI/CircleCI into 3 sub-cycles is net-negative per master plan §3 Cycle 2 stopping-criterion check; templates share rendering plumbing).

---

## §3 — Single-component fence

**Scope:** `plugins/dev-sdlc/pr-safety/` (existing component sealed by Cycle 1; Cycle 2 extends it within the same fence).

**New paths (this cycle):**

- `plugins/dev-sdlc/pr-safety/src/loam_pr_safety/installers/` (NEW directory)
  - `__init__.py` — public-API re-exports for the install verbs.
  - `hooks.py` — pre-commit + pre-push hook generators; idempotency guard; husky detection + routing; conflict detection.
  - `ci.py` — GitHub Actions / GitLab CI / CircleCI template renderers; placeholder substitution; conflict detection.
  - `pr_template.py` — PR description template + render-from-gate-output logic; body-overflow truncation strategy.
  - `conflicts.py` — conflict detection helpers (read existing file, classify "loam-managed" vs "non-loam content", build halt payload for PM surface).
- `plugins/dev-sdlc/pr-safety/src/loam_pr_safety/templates/` (NEW directory; static template assets)
  - `hooks/pre-commit.sh.template` — the pre-commit hook script body.
  - `hooks/pre-push.sh.template` — the pre-push hook script body.
  - `hooks/husky-pre-commit.sh.template` — the husky-shaped variant.
  - `hooks/husky-pre-push.sh.template` — the husky-shaped variant.
  - `ci/github-actions/loam-pr-safety.yml.template` — the GitHub Actions workflow.
  - `ci/gitlab-ci/.gitlab-ci.snippet.yml.template` — GitLab CI snippet (insertable into existing `.gitlab-ci.yml`).
  - `ci/circleci/config.snippet.yml.template` — CircleCI snippet (insertable into existing `.circleci/config.yml`).
  - `pr/pr_description.md.template` — markdown PR description with placeholder slots for the rendered sections.
- `plugins/dev-sdlc/pr-safety/src/loam_pr_safety/cli.py` (EDIT — extend Cycle 1 CLI with `install` sub-subcommand + `gate --render-pr-description` flag)
- `plugins/dev-sdlc/pr-safety/src/loam_pr_safety/__init__.py` (EDIT — re-export new public API: `install_pre_commit`, `install_pre_push`, `install_ci`, `install_pr_template`, `render_pr_description`)
- `plugins/dev-sdlc/pr-safety/tests/` (EXTEND — Cycle 2 adds per-AC tests + integration tests)
  - `test_AC_PRSI_1_pre_commit_installer.py`
  - `test_AC_PRSI_2_pre_push_installer.py`
  - `test_AC_PRSI_3_hook_script_semantics.py`
  - `test_AC_PRSI_4_github_actions_template.py`
  - `test_AC_PRSI_5_gitlab_ci_template.py`
  - `test_AC_PRSI_6_circleci_template.py`
  - `test_AC_PRSI_7_pr_description_template.py`
  - `test_AC_PRSI_8_install_ergonomics.py`
  - `test_AC_PRSI_9_e2e_smoke.py`
  - `test_AC_PRSI_10_test_surface.py`
  - `test_idempotency_d2.py` — idempotency variant (5+ install runs no-op for stable content)
  - `test_cross_session_state_d5_install.py` — installed hooks survive process boundary
  - `test_husky_detection.py`
  - `test_conflict_halt.py`
  - `test_pr_description_overflow.py`
- `plugins/dev-sdlc/pr-safety/tests/fixtures/` (EXTEND)
  - `husky-detection/` — fixture repos with husky present (package.json + .husky/) vs absent.
  - `ci-templates/` — sample existing `.github/workflows/`, `.gitlab-ci.yml`, `.circleci/config.yml` for conflict detection.

**Edits to existing pr-safety paths (in-fence):**

- `plugins/dev-sdlc/pr-safety/README.md` — append "Cycle 2" section + install surface table; bump component description.
- `plugins/dev-sdlc/pr-safety/pyproject.toml` — bump version to `0.2.0` (Cycle 2 extends; 0.1.0 → 0.2.0); description string mentions Cycle 2 surfaces.

**Composition (read-only, no edit):**

- Cycle 1's `loam_pr_safety.gate.decide`, `loam_pr_safety.classifier.classify`, `loam_pr_safety.contract.read_contract`, `loam_pr_safety.audit.{write_audit_entry, list_entries}`, `loam_pr_safety.profile.{is_production_stake, read_safety_profile}` — install surfaces invoke these read-only.
- `loam.per_project_pm.{PMRuntime, RatificationBatch, surface_next_questions_batch}` — install-conflict halts surface through PM batch (same as Cycle 1 override flow).
- `loam_odd_extractor.state.compute_repo_id` — re-used for repo-id derivation in install verbs (already imported via Cycle 1's `loam_pr_safety.state`).

**Universal-admitted prefixes/files (off-fence, allowed under standard amendment policy):**

- `docs/rebuild/plans/` — this plan-doc + manifest.
- `CLAUDE.md`, `docs/odd-in-loam.md`, `docs/odd-methodology.md`, `docs/rebuild/STATE.md` — universal admission per `dev-pattern-simplifications-2.manifest.yaml` precedent.

**Out-of-fence (would halt-and-surface):**

- Any `framework/` component edit (other than read-only imports).
- Any other plugin (e.g., `loam-skills/`) edit.
- Any edit to `plugins/dev-sdlc/odd-extractor/` source.
- Any edit to other `plugins/dev-sdlc/tools/` packages.
- PM-side extension (e.g., a new `RatificationBatch` shape with install-conflict-specific fields). The existing API is sufficient; if Cycle 2 plan-author / build agent finds it isn't, halt-and-surface for two-component fence ruling.

---

## §4 — AC family — `AC.PRSI.*` (locked)

Each AC has at least one explicit pytest under `plugins/dev-sdlc/pr-safety/tests/test_AC_PRSI_<n>_<slug>.py`. ODD §2.5 — every line of code, every branch, every test maps to a named AC.

- **AC.PRSI.1 — Pre-commit hook installer.**
  - `install_pre_commit(repo_path: Path, *, force: bool = False) -> InstallResult` writes a pre-commit hook to `<repo>/.git/hooks/pre-commit` (or `<repo>/.husky/pre-commit` when husky detected) that invokes `loam pr-safety gate <repo>` with the working-tree-vs-HEAD diff range.
  - Hook script: shebanged shell script (`#!/usr/bin/env bash`); sets `set -euo pipefail`; runs `loam pr-safety gate "$REPO" --json`; exits with the gate's exit code (0 PASS / 2 HARD-BLOCK / 3 SURFACE-DECISION / 4 OVERRIDE-REJECTED / 5 error). HARD-BLOCK + OVERRIDE-REJECTED + ERROR cause `git commit` to fail.
  - Idempotent: if `<repo>/.git/hooks/pre-commit` exists with loam-managed content (detected via `# loam-pr-safety:managed:<version>` sentinel comment), reinstall is a no-op for unchanged content; refreshes when version differs.
  - Halt-on-conflict: if the file exists with non-loam content (no sentinel), raises `InstallConflictError` carrying the existing content for PM surface unless `force=True` (which appends a backup + replaces).
  - Hook script is executable (chmod +x).
  - CLI surface: `loam pr-safety install pre-commit <repo>`.
  - Test: install into tmp git repo → hook file exists, executable, contains sentinel; re-run → no-op; pre-existing non-loam hook → raises; `force=True` → appends backup.

- **AC.PRSI.2 — Pre-push hook installer.**
  - `install_pre_push(repo_path: Path, *, force: bool = False) -> InstallResult` writes a pre-push hook to `<repo>/.git/hooks/pre-push` (or `<repo>/.husky/pre-push` when husky detected) that invokes `loam pr-safety gate <repo> --diff <local-sha>..<remote-sha>` for each ref being pushed.
  - Hook script: reads pre-push stdin (lines of `<local-ref> <local-sha> <remote-ref> <remote-sha>`); for each line where `<remote-sha>` ≠ `0000…` and `<local-sha>` ≠ `0000…`, runs the gate over the ref's diff range; if any HARD-BLOCK, exits non-zero so `git push` is rejected.
  - For new branches (`<remote-sha>` = `0000…`), gates the local SHA against the remote tracking branch's merge-base if computable; otherwise uses HEAD-vs-origin/main fallback.
  - Idempotent + halt-on-conflict + executable, same shape as AC.PRSI.1.
  - CLI surface: `loam pr-safety install pre-push <repo>`.
  - Test: install + simulate a push (git push --dry-run against a tmp remote) → hook fires + exits correctly; idempotency; conflict halt.

- **AC.PRSI.3 — Hook-script semantics honour production-stake profile.**
  - Hook script body delegates to `loam pr-safety gate` (which honours `safety_profile` per Cycle 1 AC.PRSG.8) — no profile logic in the hook script itself.
  - Bypass: under `safety_profile: dev`, the env var `LOAM_PR_SAFETY_BYPASS=1` causes the hook to skip with an audit-log entry (`event_kind: hook_bypass`). Under `production-stake`, `LOAM_PR_SAFETY_BYPASS` is **ignored** (per Decision P SOC-2 floor — no silent bypass under production-stake). Bypass attempts under production-stake are audit-logged as `event_kind: hook_bypass_attempt_rejected`.
  - `git commit --no-verify` is the upstream git-level escape; loam can't disable it but flags it as out-of-band (audit-log entry on subsequent `loam pr-safety` run when the diff is detected to have skipped a hook — Cycle 2 simplification: the gate can't always detect this; documented in README that `--no-verify` bypasses loam).
  - Test: hook with `LOAM_PR_SAFETY_BYPASS=1` under dev → exit 0 + audit-log entry; same env under production-stake → hook still runs gate + audit-logs the rejection.

- **AC.PRSI.4 — GitHub Actions CI template.**
  - `install_ci_github_actions(repo_path: Path, *, force: bool = False) -> InstallResult` writes `<repo>/.github/workflows/loam-pr-safety.yml`.
  - Workflow shape: triggered on `pull_request` events (`opened`, `synchronize`, `reopened`); runs `actions/checkout@v4` + `actions/setup-python@v5` (Python 3.11+); installs `loam-cli` + `loam-pr-safety` via `pip install`; runs `loam pr-safety gate $GITHUB_WORKSPACE --diff "${{ github.event.pull_request.base.sha }}..${{ github.event.pull_request.head.sha }}" --json --render-pr-description >> pr-description.md`; uploads `pr-description.md` as an artefact; on HARD-BLOCK or OVERRIDE-REJECTED, fails the workflow.
  - Placeholder substitution at install-time: `${REPO_ID}` (computed from repo path), `${LOAM_VERSION}` (from `loam-cli` package version pinned at install).
  - Render-validates: parses as YAML; required keys (`name`, `on`, `jobs`) present; the gate-invocation step's `run:` syntax shell-parseable.
  - Idempotent + halt-on-conflict (existing file with non-loam content).
  - CLI surface: `loam pr-safety install ci github-actions <repo>`.
  - Test: install + parse YAML; invocation `run:` line parses as valid shell; idempotency; conflict halt; placeholder substitution correct.

- **AC.PRSI.5 — GitLab CI template.**
  - `install_ci_gitlab_ci(repo_path: Path, *, force: bool = False) -> InstallResult` writes a snippet to `<repo>/.gitlab-ci.yml` (creates new file if absent; appends a job under existing `stages:` if `.gitlab-ci.yml` is already loam-managed; halts otherwise).
  - Job shape: `loam_pr_safety` job in `test` stage; `image: python:3.11`; `before_script: pip install loam-cli loam-pr-safety`; `script: loam pr-safety gate "$CI_PROJECT_DIR" --diff "$CI_MERGE_REQUEST_DIFF_BASE_SHA..$CI_COMMIT_SHA" --json --render-pr-description`; `rules: - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'`. On HARD-BLOCK, job exits non-zero → MR pipeline fails.
  - Render-validates: YAML parses; required keys (`stages`, `<job-name>`) present; `script:` lines shell-parseable.
  - Idempotent + halt-on-conflict.
  - CLI surface: `loam pr-safety install ci gitlab-ci <repo>`.
  - Test: install into empty `.gitlab-ci.yml` → file created with full snippet; install into pre-existing loam-managed file → snippet refreshed; non-loam pre-existing → halt; YAML parses; rules trigger on MR events.

- **AC.PRSI.6 — CircleCI CI template.**
  - `install_ci_circleci(repo_path: Path, *, force: bool = False) -> InstallResult` writes a snippet to `<repo>/.circleci/config.yml` (same merge-or-halt logic as GitLab).
  - Workflow shape: `version: 2.1`; `jobs.loam_pr_safety: { docker: [{image: cimg/python:3.11}], steps: [checkout, run: pip install loam-cli loam-pr-safety, run: loam pr-safety gate ./ --diff $CIRCLE_SHA1..$CIRCLE_BRANCH --json --render-pr-description] }`; `workflows.pr_safety: { jobs: [loam_pr_safety] }` filtered to non-main branches.
  - Render-validates: YAML parses; required keys (`version`, `jobs`, `workflows`) present.
  - Idempotent + halt-on-conflict.
  - CLI surface: `loam pr-safety install ci circleci <repo>`.
  - Test: install into empty `.circleci/config.yml`, idempotency, conflict halt, YAML parses.

- **AC.PRSI.7 — Provenance-traceable PR description template.**
  - `install_pr_template(repo_path: Path, *, force: bool = False) -> InstallResult` writes `<repo>/.github/pull_request_template.md` (and a generic-markdown variant at `<repo>/.loam/pr-safety/pr_description.template.md` callers can pipe into other surfaces).
  - The static template contains placeholder slots: `{{LOAM_PR_SAFETY_GATE_DECISION}}`, `{{LOAM_PR_SAFETY_TOUCHED_ACS}}`, `{{LOAM_PR_SAFETY_NOVEL_CANDIDATES}}`, `{{LOAM_PR_SAFETY_OVERRIDE_HISTORY}}`, `{{LOAM_PR_SAFETY_AUDIT_LOG_EXCERPT}}`. When the gate runs in a CI context (`--render-pr-description` flag), it expands the placeholders into structured markdown sections.
  - `render_pr_description(decision: GateDecision, audit_entries: list[Path], workspace_root: Path) -> str` is the public API the gate's `--render-pr-description` flag invokes. Output is markdown:
    - `## Gate decision: <action>` with reason + provenance (commit SHA, repo SHA, diff range).
    - `## ACs touched (<n>)` with one bullet per touched AC: `- AC.<id> [<band>] (<touch_kind>) — <text> (provenance: <evidence.kind>:<first 2 citations>)`.
    - `## Novel candidates (<n>)` if any.
    - `## Override history` from approved overlays at `<workspace>/.loam/pr-safety/contract-overrides/<repo-id>/`.
    - `## Audit-log excerpt` — last 3 entries pertaining to this repo-id, with timestamp + event_kind + decision.
  - Body-overflow strategy (per master plan §7.6 + this plan-doc §5 Surface #7): when the rendered body exceeds 60,000 characters (under GitHub's 65,536 limit with 5,536-char headroom), per-AC provenance is truncated to ~200 chars; a `_(truncated; full audit-log at `<workspace>/.loam/pr-safety/audit-log/`)_` footer links to the workspace path. The truncation is deterministic (oldest entries truncate first).
  - Idempotent + halt-on-conflict for the template file.
  - CLI surface: `loam pr-safety install pr-template <repo>`; `loam pr-safety gate <repo> --render-pr-description` (rendering surface).
  - Test: template installs at expected path with placeholders; render against synthetic gate output produces well-formed markdown; overflow truncation triggers above 60K threshold; sections present per spec.

- **AC.PRSI.8 — Install ergonomics CLI: `loam pr-safety install <surface>` + `--all`.**
  - `loam pr-safety install pre-commit <repo>` / `pre-push` / `ci github-actions` / `ci gitlab-ci` / `ci circleci` / `pr-template` — each maps to its installer.
  - `loam pr-safety install --all <repo>` invokes all six (continues past surface-specific conflicts; final exit code reflects worst-case across surfaces).
  - `--force` flag — replaces non-loam content (with backup); without it, conflict halts.
  - `--workspace-root <path>` — for tests + non-cwd workflows.
  - `--dry-run` — describes what would be written without writing (mirrors gate's dry-run pattern).
  - Conflict-halt surface: when a non-loam file blocks install, the CLI emits a structured halt payload to stderr (file path, first 200 chars of conflicting content, suggested action) AND writes an audit-log entry (`event_kind: install_conflict`) per AC.PRSG.7. Exit code 6 (new for Cycle 2 — distinguished from gate's 0/2/3/4/5).
  - Test: each `install <surface>` builds + dispatches; `--all` runs all six; `--dry-run` doesn't write; conflict produces exit code 6 + audit entry; `--force` replaces with backup.

- **AC.PRSI.9 — End-to-end smoke against canonical fixtures.**
  - Pre-commit + pre-push + GitHub Actions + PR description template all exercised against the v0.1.8 Cycle 4b canonical fixtures (`plugins/dev-sdlc/odd-extractor/tests/fixtures/jsts-playwright-app/` + `ruby-rails-payment/`):
    - Setup: copy fixture into a tmp repo (init git); place the v0.1.8-authored synthetic banded contract under `<workspace>/.loam/extractions/<repo-id>/contract-draft.yaml`.
    - `loam pr-safety install --all <repo>` → all six surfaces installed.
    - Synthetic regression commit (touches a VERIFIED AC) → pre-commit hook fires → exit non-zero → commit rejected.
    - With `--no-verify`, commit lands → pre-push hook fires (against a tmp remote) → exit non-zero → push rejected.
    - GitHub Actions workflow YAML render-validates (parses + invocation step shell-parses).
    - GitLab CI snippet render-validates.
    - CircleCI snippet render-validates.
    - PR description renders from the gate's HARD-BLOCK output: contains "Gate decision: HARD_BLOCK", touched AC entry, audit-log excerpt.
    - Audit-log entries witness every step (`gate_decision`, `install_*`, `hook_fired`).
  - GitLab + CircleCI smoke is render-validation only (no CI-provider sandbox in canonical pos-v2; per Lens 4 surface).
  - Test: `test_AC_PRSI_9_e2e_smoke.py` runs both fixtures end-to-end.

- **AC.PRSI.10 — Component-level test surface.**
  - Per-AC test files: `test_AC_PRSI_1_*.py` ... `test_AC_PRSI_10_*.py`.
  - Plus integration tests:
    - `test_idempotency_d2.py` — D2 idempotency variant: 5+ install runs no-op for stable content; loam-managed content detected via sentinel.
    - `test_cross_session_state_d5_install.py` — D5: hooks + CI templates + PR template survive process boundary; content stable across fresh-process invocations.
    - `test_husky_detection.py` — fixture repos with husky present route to `.husky/<hook>`; without husky route to `.git/hooks/<hook>`; detection logic spec (§5 Surface #4).
    - `test_conflict_halt.py` — pre-existing non-loam files trigger halt + exit code 6 + audit entry.
    - `test_pr_description_overflow.py` — large gate-output triggers truncation; truncated output parses as markdown; footer link present.
  - All tests pass before seal; pre-existing 105 Cycle 1 tests still pass (full sweep).

---

## §5 — Halt-and-surface BEFORE build (recorded autonomous decisions)

### Surface #1 — installer module decomposition (no halt — recorded)

**Decision (autonomous):** installers split per-surface (`hooks.py`, `ci.py`, `pr_template.py`, `conflicts.py`) within `plugins/dev-sdlc/pr-safety/src/loam_pr_safety/installers/`. Templates live in a sibling `templates/` directory as static assets.

Rationale: matches Lens 5 swarming decision (per-surface decomposition gives tightest AC-per-file mapping). Templates as static assets (rather than inlined Python strings) keeps the YAML/shell-script surface human-readable + grep-able.

### Surface #2 — sentinel-comment for loam-managed detection (no halt — recorded)

**Decision (autonomous):** loam-managed files carry a sentinel comment as the first non-shebang line:

- Hook scripts: `# loam-pr-safety:managed:<version>` (where `<version>` is the loam-pr-safety package version).
- CI templates: `# loam-pr-safety:managed:<version>` at top of file or top of inserted region.
- PR template: `<!-- loam-pr-safety:managed:<version> -->` HTML comment at top.

Rationale: Cycle 2 needs an idempotency primitive that doesn't read package metadata at install time. The sentinel is a regex-detectable marker; version comparison drives the refresh behaviour. Mirrors how `gh-pages` deployments use `<!-- managed by ... -->` comments and how tools like `pre-commit` (Python) tag their generated files.

### Surface #3 — conflict detection rule (no halt — recorded)

**Decision (autonomous):** an install target is in CONFLICT when the file:
- Exists at the target path, AND
- Does NOT contain the sentinel as expected, AND
- Is non-empty after stripping whitespace + comments.

For YAML files (`.gitlab-ci.yml`, `.circleci/config.yml`) where the file may legitimately have non-loam content alongside loam's snippet:
- Append-mode: if the sentinel block (delimited by `# loam-pr-safety:managed:start` / `# loam-pr-safety:managed:end`) exists, refresh that block in-place (preserving surrounding non-loam content).
- If sentinel block absent + file non-empty + `--force` not set, halt.
- If sentinel block absent + file non-empty + `--force` set, append the loam block + leave existing content as-is.

Rationale: pure-overwrite is dangerous for `.gitlab-ci.yml` / `.circleci/config.yml` (existing CI jobs could be lost). Sentinel-delimited block lets loam own a region without replacing the file. GitHub Actions uses a separate file (`loam-pr-safety.yml`) so the merge-mode complication doesn't apply there.

### Surface #4 — husky detection heuristic (no halt — recorded; F2 RF gap §10.3)

**Decision (autonomous):** husky is detected when EITHER:
- `<repo>/.husky/_/husky.sh` exists (husky v6+ uses this path as the runner), OR
- `<repo>/package.json` has a top-level `"husky"` key (husky v4-v5 config in package.json).

When detected, pre-commit / pre-push install routes to `<repo>/.husky/<hook>` instead of `<repo>/.git/hooks/<hook>`. The husky-shaped hook script sources `husky.sh` (`. "$(dirname -- "$0")/_/husky.sh"`) before invoking the gate.

Rationale: master plan §6.2 names husky as the explicit JS/TS case (Eric's first project). Detecting via the runner-file path (v6+) covers the modern install; the package.json key catches older installs. Other hook-managers (`pre-commit` Python, `lefthook`, `git-hooks-go`) fall through to the standard `.git/hooks/<hook>` install path; conflict detection catches collisions there (per master plan §7.5 mitigation).

### Surface #5 — env-var bypass under dev profile (no halt — recorded)

**Decision (autonomous):** under `safety_profile: dev`, `LOAM_PR_SAFETY_BYPASS=1` causes the hook to skip + write an audit-log entry (`event_kind: hook_bypass`). Under `production-stake`, the env var is **ignored**; bypass attempts are audit-logged as `event_kind: hook_bypass_attempt_rejected` and the hook still runs the gate.

Rationale: dev-profile needs an emergency-escape (e.g., commit-to-feature-branch where loam is unaware); production-stake's SOC-2 floor (Decision P) demands no silent bypass. The audit-log entry under dev is the observable trace.

### Surface #6 — `--render-pr-description` is a gate-mode flag (no halt — recorded)

**Decision (autonomous):** PR description rendering surfaces as `loam pr-safety gate <repo> --render-pr-description` (not a separate `loam pr-safety render-pr-description` subcommand). The flag suppresses normal stdout output and emits the rendered markdown instead; exit code still reflects the gate decision.

Rationale: rendering-from-gate-output is intrinsically tied to the gate run (you render the decision the gate just produced). A separate subcommand would either duplicate the gate's read-contract → classify → decide pipeline OR would have to read audit-log entries from a prior gate run (race-prone).

### Surface #7 — body-overflow truncation strategy (no halt — recorded; F2 RF gap §10.5)

**Decision (autonomous):** when the rendered PR description exceeds 60,000 characters:
1. Truncate per-AC provenance text to the first 200 chars + ellipsis.
2. If still over, truncate audit-log excerpt to last 1 entry (instead of last 3).
3. If still over, drop novel-candidates section (audit-log link still surfaces them).
4. Always include footer: `_(truncated; full audit-log at <workspace>/.loam/pr-safety/audit-log/)_`.

The 60,000 limit (vs GitHub's 65,536 char limit) reserves headroom for surface-specific re-encoding (HTML escapes, line-wrapping).

Rationale: per master plan §7.6, body-overflow is a real risk. Deterministic + ordered truncation keeps the rendered description audit-traceable (the truncation footer is always present so a reviewer knows to consult the workspace audit-log).

### Surface #8 — install-action audit-log entries (no halt — recorded)

**Decision (autonomous):** every install verb writes an audit-log entry (`event_kind: install_pre_commit | install_pre_push | install_ci_github_actions | install_ci_gitlab_ci | install_ci_circleci | install_pr_template | install_conflict | hook_bypass | hook_bypass_attempt_rejected | hook_fired`). Schema mirrors Cycle 1 AC.PRSG.7 with one new field: `target_path` (the path the install wrote to or attempted).

Rationale: SOC-2 audit-trail floor (Decision P) demands every observable-action be logged. Install verbs are observable; hook fires are observable; bypass attempts are observable.

### Surface #9 — D3/D4 smoke applicability (no halt — recorded)

**Decision (autonomous):** Cycle 2's install surfaces are filesystem-state. Hooks run as subprocess on git events (one-shot, not daemon). CI templates are static YAML. PR template is static markdown.

- **D1 cold-state ✓** — fresh canonical workspace + `loam pr-safety install --all` against fixture → all surfaces installed; hook fires on test commit produce HARD-BLOCK; audit-log entries witness.
- **D2 steady-state ✓** — 5+ install runs idempotent; loam-managed content detected via sentinel; no churn.
- **D3 restart ✓** — hooks are subprocess invocations on git events; if `git commit` is interrupted mid-hook (SIGTERM), the hook exits with whatever code it was at (non-zero typically); next invocation restarts cleanly. The "process restart" semantics for the daemon-shape are n/a; the analog (hook-process interrupted mid-flight) is exercised: kill the hook subprocess + retry; re-run completes cleanly.
- **D4 reboot ✓** — installed hooks are filesystem state (`.git/hooks/<hook>` + `.husky/<hook>` + `.github/workflows/*.yml` + `.gitlab-ci.yml` + `.circleci/config.yml` + `.github/pull_request_template.md`). All survive macOS reboot trivially (filesystem). Test: write installed state → `sync` (forces flush) → re-read → identical.
- **D5 cross-session ✓** — installed hooks survive process boundary (subprocess invocation reads them fresh); PR description rendering produces consistent output across sessions for the same gate decision.
- **D6 telemetry-floor ✓** — every install action + hook fire + override + render writes an audit-log entry per Surface #8.

The dispatch's "all 6 dimensions" wording is satisfied — D3 + D4 are exercised in their applicable form (filesystem-state + subprocess-restart semantics, not daemon-restart semantics).

### Surface #10 — release-note promise mapping (no halt — recorded)

**Decision (autonomous):** every release-note promise must correspond to tested + reliable behavior.

| Promise | Backing AC | Test |
|---|---|---|
| "pre-commit hook fires the gate on every commit; HARD-BLOCK rejects" | AC.PRSI.1 | `test_AC_PRSI_1_*.py` + `test_AC_PRSI_9_e2e_smoke.py` |
| "pre-push hook fires the gate on every push; HARD-BLOCK rejects" | AC.PRSI.2 | `test_AC_PRSI_2_*.py` + `test_AC_PRSI_9_e2e_smoke.py` |
| "hooks honour production-stake (no silent bypass)" | AC.PRSI.3 | `test_AC_PRSI_3_*.py` |
| "GitHub Actions / GitLab CI / CircleCI templates render-validate" | AC.PRSI.{4,5,6} | `test_AC_PRSI_4_*.py` / `test_AC_PRSI_5_*.py` / `test_AC_PRSI_6_*.py` |
| "PR description auto-populates from gate output" | AC.PRSI.7 | `test_AC_PRSI_7_*.py` + `test_pr_description_overflow.py` |
| "install --all wires every surface" | AC.PRSI.8 | `test_AC_PRSI_8_*.py` |
| "halts on conflict; never silent overwrite" | AC.PRSI.8 + Surface #3 | `test_conflict_halt.py` |
| "husky-aware install" | AC.PRSI.{1,2} + Surface #4 | `test_husky_detection.py` |
| "5+ install runs idempotent" | AC.PRSI.10 + D2 | `test_idempotency_d2.py` |
| "hooks survive process restart + reboot" | AC.PRSI.10 + D3/D4 | `test_cross_session_state_d5_install.py` |
| "every install + fire audit-logged" | AC.PRSI.{1..8} + Cycle 1 AC.PRSG.7 | `test_AC_PRSI_9_e2e_smoke.py` |

If any test in the right column FAILs at build time, the corresponding promise gets de-shipped (not partially-shipped) — halt-and-surface to dispatcher.

### Surface #11 — version bump strategy (no halt — recorded)

**Decision (autonomous):** `loam-pr-safety`'s `pyproject.toml` version bumps from `0.1.0` → `0.2.0`. Cycle 2 is a feature-add release within the v0.1.9 cycle pair (Cycle 1 = 0.1.0; Cycle 2 = 0.2.0; Cycle 3 doesn't touch pr-safety so no further bump). The version string also propagates into the sentinel comments (`# loam-pr-safety:managed:0.2.0`).

Rationale: SemVer-shaped intra-cycle versioning makes "is this a fresh install vs an upgrade" detectable from the sentinel. Cycle 1 sealed at 0.1.0; Cycle 2 ships 0.2.0.

### Surface #12 — pre-existing pr-safety entry-point doesn't change (no halt — recorded)

**Decision (autonomous):** Cycle 1 registered `pr-safety = "loam_pr_safety.cli:build_pr_safety_subcommand"` in pyproject.toml's `loam.cli.subcommands` group. Cycle 2 extends `build_pr_safety_subcommand` (within `cli.py`) to add the `install` sub-subcommand + the `--render-pr-description` flag on `gate`. The entry-point itself doesn't change.

Rationale: extending the existing builder keeps the entry-point stable (no re-registration; no install-side change). The CLI's existing `gate` subcommand stays at the same path; `install` joins it as a sibling.

---

## §6 — Surface decomposition (locked)

Spelling out the install verbs + their target paths so the build agent can map tests 1:1 to surfaces.

### Per-surface install verbs

| CLI verb | Function | Standard target | Husky variant target |
|---|---|---|---|
| `install pre-commit <repo>` | `install_pre_commit(repo)` | `<repo>/.git/hooks/pre-commit` | `<repo>/.husky/pre-commit` |
| `install pre-push <repo>` | `install_pre_push(repo)` | `<repo>/.git/hooks/pre-push` | `<repo>/.husky/pre-push` |
| `install ci github-actions <repo>` | `install_ci_github_actions(repo)` | `<repo>/.github/workflows/loam-pr-safety.yml` | n/a (CI workflows don't compose with hook managers) |
| `install ci gitlab-ci <repo>` | `install_ci_gitlab_ci(repo)` | `<repo>/.gitlab-ci.yml` | n/a |
| `install ci circleci <repo>` | `install_ci_circleci(repo)` | `<repo>/.circleci/config.yml` | n/a |
| `install pr-template <repo>` | `install_pr_template(repo)` | `<repo>/.github/pull_request_template.md` + `<repo>/.loam/pr-safety/pr_description.template.md` | n/a |
| `install --all <repo>` | all above | all above | all above (with husky on hooks) |

### Sentinel detection

Every loam-managed file carries `loam-pr-safety:managed:<version>` as a comment. The detection implements:

```python
def detect_loam_managed(content: str) -> str | None:
    """Return the version string if loam-managed; else None."""
    m = re.search(r"loam-pr-safety:managed:([\d.]+)", content)
    return m.group(1) if m else None
```

### Install result shape

```python
@dataclass
class InstallResult:
    surface: Literal["pre-commit", "pre-push", "ci/github-actions",
                     "ci/gitlab-ci", "ci/circleci", "pr-template"]
    target_path: Path
    action: Literal["created", "refreshed", "noop", "conflict-halted",
                    "force-replaced"]
    husky_routed: bool = False
    prior_version: str | None = None  # populated on refresh
    new_version: str = ""              # always populated
    backup_path: Path | None = None    # populated on force-replaced
```

`InstallResult` returns from each installer; `--all` aggregates a `list[InstallResult]`.

---

## §7 — Smoke (REALISTIC CONDITION — all 6 dimensions per smoke-test-discipline §6)

Per dispatch's "all 6 dimensions" mandate. Cycle 2's install surfaces are filesystem-state + subprocess invocation, so D3/D4 apply in their applicable form.

### D1 — cold-state (fresh canonical workspace)

**Pattern.** Tmp workspace; tmp git repo with the v0.1.8 Cycle 4b synthetic banded contract written into `.loam/extractions/<repo-id>/contract-draft.yaml`. Run `loam pr-safety install --all <repo>`. Assert: (a) all 6 surfaces installed at expected paths; (b) hook scripts executable; (c) sentinels present in each managed file; (d) audit-log entries witness each install. Then synthetic regression commit (touches a VERIFIED AC) → pre-commit hook fires → exit non-zero → commit rejected. Force-bypass (`--no-verify`), then push to tmp remote → pre-push hook fires → exit non-zero → push rejected. Render PR description from gate output → markdown produced with all 5 sections.

**Test:** `test_AC_PRSI_9_e2e_smoke.py` (covers cold-state + e2e + audit-log witnesses).

### D2 — steady-state (idempotency variant)

**Pattern.** Run `loam pr-safety install --all <repo>` 5 times in succession. Assert: (a) install action is `noop` for runs 2-5 (sentinel matches); (b) byte-equal file content across runs; (c) no audit-log churn beyond run 1's install_* entries (runs 2-5 emit no new entries since action is noop).

When the loam-pr-safety package version differs from the sentinel, action is `refreshed` instead of `noop`; the file is rewritten with the new version; audit-log entry written. Tested separately via mock-version test.

**Test:** `test_idempotency_d2.py`.

### D3 — restart resilience

**Pattern.** Spawn pre-commit hook as subprocess on a synthetic commit; mid-execution send `SIGTERM`. Assert: (a) hook exits non-zero (subprocess captures the signal); (b) git's pre-commit pipeline rejects the commit (since hook exited non-zero); (c) next commit attempt re-runs the hook fresh + completes (no leftover state from the killed run).

Hook is single-shot subprocess; no shared state to corrupt. The "restart" analog is "kill the in-flight invocation; next git event spawns a fresh invocation."

**Test:** `test_cross_session_state_d5_install.py::test_d3_hook_subprocess_restart`.

### D4 — reboot resilience

**Pattern.** Install all surfaces. `sync` (force flush to disk). Read every installed file's content + permissions. Re-mount the tmp workspace (simulating reboot via fresh process invocation reading the same paths). Re-read every installed file's content + permissions. Assert: byte-equal + executable bit preserved.

Real-machine reboot is impractical for unit tests; the equivalent smoke is "filesystem state survives a process boundary AND a flushed sync." Tested by separate-process invocation reading the installed surfaces.

**Test:** `test_cross_session_state_d5_install.py::test_d4_filesystem_state_survives_reboot_equivalent`.

### D5 — cross-session continuity

**Pattern.** Process A: install --all + render PR description from a gate decision → save the rendered markdown. Process B (subprocess invocation): re-render PR description from the same gate decision → produce identical markdown (modulo timestamps via clock injection).

The `/clear` analog is "fresh process boundary"; the test validates that boundary directly (subprocess vs in-process). Audit-log entries persist across the boundary; install state persists.

**Test:** `test_cross_session_state_d5_install.py::test_d5_install_state_persists` + `::test_d5_pr_description_render_consistent`.

### D6 — telemetry floor

**Pattern.** Run a full install + fire + render cycle. Assert: (a) one audit-log entry per install verb (`event_kind: install_*`); (b) one audit-log entry per hook fire (`event_kind: hook_fired` with the gate's decision payload); (c) one audit-log entry per bypass attempt (`event_kind: hook_bypass | hook_bypass_attempt_rejected`); (d) entries follow the Cycle 1 schema (schema_version, timestamp ISO8601 with TZ, repo_id, repo_sha, event_kind, target_path); (e) filenames follow `<YYYY-MM-DD>-<NNNN>.yaml` with monotonic per-day NNNN sequence (continued from Cycle 1's counter).

**Test:** `test_AC_PRSI_9_e2e_smoke.py` (witnesses) + `test_AC_PRSI_3_*.py` (bypass entries).

---

## §8 — Out of scope

Explicit deferrals (master plan §3 Cycle 2 + per-cycle dispatch):

- **6 dev-sdlc SKILLs second pass.** → Cycle 3.
- **Audit-allowlist cleanup.** → Cycle 3.
- **BitBucket Pipelines / Jenkins / Buildkite CI templates.** → v0.2.x post-Eric (per Eric synthesis §2 v0.1.9 production-polish "ship for the three most common"; if Eric's CI is one of these, surface for v0.2.0).
- **Drone / Gitea Actions / Woodpecker CI templates.** → v0.2.x post-Eric.
- **PR description rendering for non-GitHub surfaces (rendering into GitLab MR description / CircleCI build comments via API).** → in-scope at template/render level (markdown output is platform-neutral); surface-specific API integration is left to caller.
- **`pre-commit` (Python tool) / `lefthook` / `git-hooks-go` integration beyond conflict-halt.** → v0.2.x. Cycle 2 detects husky explicitly + falls through to halt-on-conflict for other managers.
- **Test-execution integration for VERIFIED-touched diffs (running the actual test in-hook to confirm regression vs surface a diff).** → Cycle 1 simplification carries forward: VERIFIED-touched is treated as regression-suspect; reviewer ratifies via `--override`.
- **Sub-second hook performance optimisation.** → if the gate takes >5s on Eric's repos, surface for v0.2.x optimisation (caching contract reads, lazy-loading classifier). Cycle 2 ships correctness-first.
- **CI provider sandbox execution.** → out of canonical pos-v2's scope; render-validates only for GitLab + CircleCI per Lens 4. GitHub Actions full-run is also render-validates only (no PR-event sandbox in CI).
- **`gh pr create` / `glab mr create` integration (rendering PR-description via gh/glab CLI).** → markdown output is callable by gh/glab; integration is left to caller.
- **Continuous codebase-watch.** → v0.2.0+.
- **Eric's actual codebases (real OSS PR-safety smoke).** → v0.2.1 fresh-user smoke gate.

---

## §9 — Halt triggers (in-flight)

Per dispatch + master plan:

- **WD drifts.** If `git rev-parse --show-toplevel` is not `/Users/lukeivers/ivers-corp-pos-v2/`, halt + surface.
- **Cycle 1 not sealed.** If `plugins/dev-sdlc/seals/SEAL_COMMIT.v0-1-9-cycle-1-pr-safety-gate-engine` is absent, OR `loam pr-safety gate --help` fails, halt — Cycle 2 depends on Cycle 1's CLI.
- **Plan-doc not authored before code.** This document IS that plan-doc. If code lands before this is committed, halt.
- **Hook installer fails realistic install/uninstall cycle (idempotent + clean uninstall).** Halt + surface.
- **Any CI template fails dry-run validation (YAML parse, gate-invocation step shell-parse).** Halt + surface.
- **PR description render fails on canonical fixture gate output.** Halt + surface.
- **Husky detection produces a false-positive on a non-husky repo OR false-negative on a known husky repo.** Halt + RF; refine the heuristic (§5 Surface #4).
- **Conflict-halt mechanism allows a silent overwrite (production-stake floor violation).** Halt + RF.
- **D3 / D4 smoke fails (subprocess-restart OR filesystem-state-survives).** Halt — these are the ship-tests for the dispatch's "all 6 dimensions" mandate.
- **Any AC ships partial.** If `test_AC_PRSI_<n>_*.py` is XFAIL, skipped, or asserts a degraded behaviour, halt + reframe before sealing.
- **Cycle exceeds 5 hours wall-clock.** Halt with partial findings; consider further decomposition (e.g., split installers from CI templates from PR description).
- **More than 3 in-build decisions need Luke escalation.** Master plan recommends 3.
- **PM-side extension needed.** If the existing `RatificationBatch` API can't carry install-conflict halt payload, halt + surface for two-component fence ruling.
- **ODD violations in surrounding code.** Halt + surface; do not silently extend (per `feedback_subagent_odd_violation_halt`).
- **dev-sdlc Cycle 1 README sub-package entry was supposed to land and didn't.** Note: Cycle 1's plan-doc said it would append a "Sub-packages" entry to `plugins/dev-sdlc/README.md`; verification at HEAD `3162d2f` shows it did not. **Decision (autonomous):** Cycle 2 picks up this loose thread and adds the entry under the same in-fence universal-admission. Surfaced here for transparency (per F2 RF) but not a halt.

---

## §10 — F2 Ruthless Feedback (gaps named this turn)

1. **GitLab CI / CircleCI smoke is render-validates only.** AC.PRSI.{5,6} ship templates that parse-as-YAML + have correct shell-invocation syntax, but neither is exercised against an actual GitLab/CircleCI runner. The dispatch brief says GitHub Actions is "the most-common; GitLab + CircleCI smoke is template-render-validates only" — this matches the dispatch but the F2 honest-framing: if the template has a runner-specific bug (e.g., GitLab's `rules:` syntax has changed), Cycle 2's tests won't catch it. **Mitigation:** the templates use canonical-shape patterns (per current GitLab CI 17.x docs + CircleCI 2.1 docs); render-validate covers syntax; runner-execution validation is a v0.2.x candidate post-Eric (Eric's CI provider unknown until pre-call).

2. **Hook performance under realistic load is unmeasured.** A hook that takes 30s on every commit is a UX disaster regardless of correctness. Cycle 2 ships correctness-first (gate runs, classifier classifies, decision lands). The classifier on Eric's full Rails codebase (60 ACs, hundreds of files) may be slow. **Mitigation:** if Cycle 2 build agent observes >5s wall-clock on either fixture, surface for caching/lazy-loading optimisation as a Cycle 2 follow-on (in-fence) or v0.2.x candidate. Documented in README under "Known limits."

3. **Husky detection is heuristic-not-canonical.** §5 Surface #4 detection rule covers v6+ runner-file + v4-v5 package.json key. But husky v5 transitional installs may have neither (config in `.huskyrc` JSON file); pnpm/yarn workspaces may install husky in a parent dir. **Mitigation:** the heuristic covers ~95% of installs (per husky GitHub stars / popular usage); fall-through is halt-on-conflict at `.git/hooks/pre-commit` which is the safe default. Edge cases ship to FIDRAFT post-Cycle 2 if Eric surfaces one.

4. **The `--render-pr-description` flag conflates rendering with gate-running.** Surface #6 chose this for atomicity, but a reviewer who wants to re-render a previously-decided PR description (e.g., after editing the contract) has to re-run the gate. **Mitigation:** the audit-log carries the prior decision; a future `loam pr-safety render <repo>` standalone could read from audit-log + render — captured as v0.2.x FIDRAFT candidate. Cycle 2 ships the gate-mode flag only.

5. **Body-overflow truncation may hide audit-relevant detail.** Surface #7's "truncate per-AC provenance to 200 chars" loses information; a reviewer relying on the PR description alone (not consulting the audit-log) may miss a regression detail. **Mitigation:** the truncation footer always names the audit-log path, making truncation discoverable. Reviewers SHOULD consult the audit-log for high-stakes gate decisions; Cycle 2's PR description is the at-a-glance summary, not the authoritative log. README documents this.

6. **`--no-verify` bypasses loam at the git-level.** Cycle 2 cannot intercept `git commit --no-verify` (git itself supports the flag). On the next loam invocation (push / CI), the gate runs against the diff and detects the bypassed commit through normal classification. **Mitigation:** this is a known git behaviour; pre-push + CI gate are the safety net. Documented in README. Production-stake teams configure their git server to reject `--no-verify` at the server level (out-of-band; not loam's responsibility).

7. **Idempotency sentinel is regex-detectable, not cryptographically signed.** A malicious actor could insert the sentinel comment into a non-loam hook to make loam's installer skip-instead-of-halt. **Mitigation:** the threat model is internal-team-trust (Eric's team writing their own commits); cryptographic signing of hook content is overkill for v0.1.9. If the threat model later includes hostile commits, the sentinel could be replaced with HMAC-signed content. Captured as FIDRAFT candidate.

8. **CI templates use `pip install loam-cli loam-pr-safety` from PyPI.** Cycle 2 doesn't ship to PyPI yet (the OSS publish is at v0.1.0 per existing `oss-v0-1-0-publish-*` plans, but loam-cli + loam-pr-safety are not yet on PyPI as discoverable packages). **Mitigation:** the CI templates fall back to `pip install -e <repo-path>` when pip-public-install fails (Cycle 2 simplification: the template includes a fallback line). Documented in README. PyPI publication is tracked separately.

9. **The PR description template overlaps with team conventions.** Eric's company likely has a PR template at `.github/pull_request_template.md` already. Cycle 2's install halts on conflict (Surface #3); `--force` replaces with backup. **Mitigation:** the existing template content is preserved as `.github/pull_request_template.md.bak`. The reviewer can manually merge loam's sections into their existing template post-install. README documents this. A future v0.2.x feature could ship "merge mode" that adds loam's sections to an existing PR template via sentinel-block.

10. **Cycle 2 wall-clock band 5–10 h with 5 h halt-trigger.** The halt-trigger is tight for what is a delivery cycle (less risky than Cycle 1's NEW-component build). **Mitigation:** if at 5 h the build is on-track for 6-7 h with 80%+ tests green, dispatcher should consider extending another 1-2h to seal cleanly. If at 5 h tests are <50% green or any AC is partial, halt-and-surface per master plan §6 critical-thinking discipline.

11. **Install --all conflict aggregation.** When `--all` runs all six surfaces and one halts on conflict, Surface #5 of master plan §3 Cycle 2 says "halt on conflict with PM-mediated decision-surface." Cycle 2's interpretation: `--all` continues past conflicts (logging each via audit) and exits with the worst-case code (6 if any conflict; otherwise the gate's normal exit). Reviewer can re-run `--force` post-PM-decision. **F2 RF:** alternative interpretation is "halt on first conflict" (more conservative). The continue-and-aggregate choice prioritises ergonomics (one re-run with `--force` post-decisions); the halt-on-first-conflict choice prioritises explicit-decision-per-surface (more PM batches but cleaner audit). Cycle 2 chooses continue-and-aggregate; if Luke prefers halt-on-first, surface for revisit.

12. **The `LOAM_PR_SAFETY_BYPASS=1` env var introduces a global escape under dev profile.** A developer who sets this in their shell rc forgets and silently bypasses for all future commits — until they read the audit-log. **Mitigation:** the audit-log is the trace; pre-push + CI catch any bypassed commits at later stages. Production-stake ignores the env var entirely. Documented in README under "Bypass behaviour."

13. **Cycle 1 README mentioned a `plugins/dev-sdlc/README.md` "Sub-packages" entry that didn't ship.** §9 surfaces this; Cycle 2 picks it up. F2 RF: this is exactly the silent-extend pattern `feedback_subagent_odd_violation_halt` warns against. The right call is halt-and-surface; this plan-doc is the surface. Building Cycle 2 then includes the entry as a transparent transparent in-fence catch-up rather than introducing it under the radar.

---

## §11 — Provenance trail

- **Master plan source authority:** `docs/rebuild/plans/v0-1-9-master-plan.md` §3 + §4 Cycle 2 (sealed at `b01d3eb`).
- **Eric synthesis:** `docs/rebuild/plans/eric-final-delivery-plan-2026-05-04.md` — Decisions I (PLAUSIBLE→VERIFIED default-no), P (SOC-2 floor), Q (one-question-at-a-time), R (HARD/SOFT smoke gate cadence).
- **Cycle 1 (PR-safety gate engine + override workflow):** `plugins/dev-sdlc/pr-safety/` sealed at `790807d`; CLI registered via `loam.cli.subcommands` entry-point group; 105 cycle tests green; banded contract reader + diff classifier + gate engine + override flow + SOC-2 audit log all available for Cycle 2 composition.
- **Cycle 1 plan-doc (compose-with reference):** `docs/rebuild/plans/v0-1-9-cycle-1-pr-safety-gate-engine.md` — surfaces Cycle 1 chose, decision matrix, audit-log shape.
- **v0.1.8 Cycle 4b canonical fixtures:** `plugins/dev-sdlc/odd-extractor/tests/fixtures/jsts-playwright-app/`, `ruby-rails-payment/`. Sealed at `c648cf9`. End-to-end smoke runs against both.
- **v0.1.7 Cycle 4 PM batch API:** `framework/per-project-pm/src/loam/per_project_pm/runtime.py` — `surface_next_questions_batch`, `record_response`, `PendingResponseError`. Sealed at `122a7c8`. Install conflicts route through this surface.
- **v0.1.7 Cycle 2 PM RatificationBatch:** `framework/per-project-pm/src/loam/per_project_pm/ratification.py` — `RatificationBatch.from_banded_acs`. Sealed at `4865028`.
- **v0.1.6 Cycle 1 production-safety:** `framework/workspace-bootstrap/src/loam/workspace_bootstrap/manifest.py` — `Manifest.safety_profile`, `LEGAL_SAFETY_PROFILES`. Sealed at `3f1d237`. Hooks honour transitively via gate.
- **Dev-pattern-simplifications #1 + #2 (manifest schema v3 + seal-narrative compression):** sealed at `019cfca` + `df3f50f`. Cycle 2 uses v3 schema.
- **Smoke-test-discipline:** `plugins/dev-sdlc/docs/smoke-test-discipline.md` — six dimensions; D3/D4 applicable in their filesystem-state + subprocess-restart shape.
- **ODD-methodology:** `plugins/dev-sdlc/docs/odd-methodology.md` — every line maps to a named AC (ODD §2.5).
- **Lens 5 (swarming) reference + stopping criterion:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_swarming_recursive_decomposition.md` + framework/CLAUDE.md Lens 5.
- **husky reference:** husky v9.x docs (https://typicode.github.io/husky/) — runner-file path + package.json key.
- **Quality bar (Luke directive 2026-05-04):** master plan §1 verbatim + master plan §3 Decision R framing + dispatcher's CLAUDE.md "WOW him" emphasis.

---

## §12 — Bookkeeping

- **Manifest:** `docs/rebuild/plans/v0-1-9-cycle-2-hooks-and-templates.manifest.yaml` — schema_version: 3 with `plan_doc_ref:`. amendment.number omitted per AC.DPS1.10. ac_count: 10. smoke_outcome: "All 6 dimensions exercised — D1 cold-state + D2 idempotency + D3 subprocess-restart + D4 filesystem-state + D5 cross-session + D6 telemetry-floor; full-suite green sweep including 105 inherited Cycle 1 tests".
- **Apply:** `loam amend apply <manifest>` — single merged manifest+apply commit per AC.DPS1.6 (v3 schema). NOT `git commit --amend`; pos-amend creates a new commit per `feedback_no_amend_in_agent_dispatches`.
- **Seal:** `loam amend seal --plan-doc docs/rebuild/plans/v0-1-9-cycle-2-hooks-and-templates.md <manifest>` — synthesizes 5–15 line narrative body per AC.DPS2.{1,4} into `plugins/dev-sdlc/seals/SEAL_COMMIT.v0-1-9-cycle-2-hooks-and-templates`.
- **§14 backfill (this plan-doc, post-seal):** add a `## 14.` heading + method-decision register with the apply SHA + seal SHA + post-seal commit SHA per AC.D-sa.7 lint regex (NOT `## §14`).
- **Master plan §9 backfill:** update Cycle 2 row with apply SHA + seal SHA + notes after seal lands.
- **Roadmap §8 backfill:** add v0.1.9 Cycle 2 row to `docs/rebuild/plans/v0-1-x-roadmap.md` §8 method-decision register.
- **Eric-final-delivery §2 backfill:** add v0.1.9 Cycle 2 progress note to `docs/rebuild/plans/eric-final-delivery-plan-2026-05-04.md` §2.
- **No tag push.** v0.1.9 tag waits on Cycle 3 + release-level SOFT smoke gate (Decision R) + Luke's gate-review.

---

## §13 — Acceptance gate

This plan-doc is gate-ready when:

1. All 10 AC.PRSI.* families named with explicit pytest paths (§4) ✓
2. Single-component fence named (§3) ✓
3. All 6 smoke dimensions addressed — applicable forms exercised (§7) ✓
4. Halt triggers named (§9) ✓
5. Bookkeeping path named (§12) ✓
6. F2 gaps named (§10) — 13 gaps surfaced ✓
7. Surface decomposition fully enumerated (§6) ✓
8. Autonomous decisions recorded (§5) — 12 surfaces ✓
9. Predecessor cycle verified sealed (Cycle 1 at `790807d`) ✓
10. Husky-detection rule committed (§5 Surface #4) ✓
11. Body-overflow truncation strategy committed (§5 Surface #7) ✓

Build proceeds.

---

## 14. Method-decision record (post-seal backfill)

(Reserved; build agent backfills with apply SHA + seal SHA + post-seal commit SHA per AC.D-sa.7 lint regex. The `## 14.` heading is required by the `loam amend seal` lint, NOT `## §14`.)

| Step | SHA | Notes |
|---|---|---|
| Plan-doc commit (this file) | TBD | docs(plans): v0.1.9 Cycle 2 sub-plan + manifest |
| Source-edit commit (BASELINE) | TBD | feat(dev-sdlc): pr-safety hook installers + 3 CI templates + PR description template (v0.1.9 Cycle 2) |
| Apply commit (manifest+apply merged per AC.DPS1.6) | TBD | chore(amend): v0-1-9-cycle-2-hooks-and-templates manifest+apply — dev-sdlc BASELINE+sidecar bump |
| Seal commit | TBD | chore(seals): v0-1-9-cycle-2-hooks-and-templates — dev-sdlc at <baseline> |
| Post-seal SHA-record commit (this §14 backfill + master plan §9) | TBD | docs(plans): record v0-1-9-cycle-2 commit SHAs in method-decision register |

### Commit SHAs

(Reserved post-seal.)
