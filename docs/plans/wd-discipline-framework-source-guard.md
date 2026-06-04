# WD-discipline framework-source guard — sub-plan

> Refuse `Write`/`Edit` against framework-SOURCE code when the working
> location is a DERIVED workspace (a vendored framework copy), while
> ALLOWing the same edit under canonical loam. Structural enforcement
> of the working-directory discipline that was violated twice (task
> #89): framework code edited directly inside `pos3/framework/` instead
> of canonical `~/loam`, where it diverged and was nearly clobbered by
> an upgrade.

## §1 Objective

A `PreToolUse(Write|Edit|MultiEdit)` hook, shipped with
`framework/safety-layer/`, that **BLOCKS** an edit whose target is
framework-source code AND whose enclosing git repository is **not**
canonical loam (i.e. a derived/vendored workspace), redirecting the
edit to canonical `/Users/lukeivers/loam`; and **ALLOWS** that same
edit under canonical loam (or any canonical worktree) and ALLOWS all
workspace-local content edits everywhere.

## §2 Predecessors / context

- Composes against canonical main `32f36291` (v1.2.0 published tip).
- Reference shape: `framework/safety-layer/hooks/config_write_guard.py`
  (the existing `PreToolUse` path-protection guard — same envelope
  parse, same `permissionDecision: deny` JSON contract, same
  fail-open + toggle-env + `.loam/safety-hooks.log` conventions).
- Sibling reference (cross-repo, not canonical): the interactive
  session's `in_thread_work_budget_guard.py` — the override-hatch
  pattern (env var + sentinel file) named in the dispatch.
- Task #89 (the twice-seen WD-discipline violation this guard
  structurally enforces). Born alongside task #88 (the v1.2.0 upgrade
  that nearly clobbered the divergent vendored edits).

This guard lives in canonical `framework/safety-layer/` SO THAT it
ships to every derived workspace via the normal framework upgrade
(task #40) — the guard must travel WITH the framework to protect
each derived workspace automatically. A workspace-only hook (like the
interactive session's `in_thread_work_budget_guard.py`) would protect
only the one workspace that happened to install it; the failure mode
is general, so the fix lives in the shipped framework.

## §3 Scope

In scope:

- One new stdlib-only hook script under
  `framework/safety-layer/hooks/` that classifies (path-is-framework-
  source) × (repo-is-canonical) and denies the derived×framework-
  source cell.
- Its AC tests under `framework/safety-layer/tests/`, including a
  real-subprocess outcome-altitude test driven through the production
  hook entry point.
- A `settings`-fragment registration note in the hook's docstring +
  the safety-layer `__init__.py` roster comment, mirroring how the
  three existing safety hooks are described (the first-run installer
  `framework/hands-off-lifecycle/hooks/first_run_settings.py` is the
  mechanism that writes the `PreToolUse` stanza into a workspace's
  `settings.json`; wiring THAT installer is OUT of scope for this
  cycle — see below).

Out of scope:

- Modifying `first_run_settings.py` to auto-install this hook into
  workspaces (a separate cycle; the installer's `PreToolUse` merge is
  its own sealed surface). This cycle ships the guard + its
  registration CONTRACT; activating it in the installer is a
  follow-on. Rationale: keeps this cycle's fence to one component
  (`framework/safety-layer/`) and avoids a cross-component widening
  into `framework/hands-off-lifecycle/` that the structural fix does
  not require to be correct as a unit.
- Any edit to the derived `pos3` workspace itself (that tree gets the
  guard via the later re-sync, per dispatch — LOCAL seal only).
- Blocking Bash-driven edits (`echo > file`, `sed -i`): the existing
  bash_guard family owns Bash; this hook matches content tools only,
  matching `config_write_guard`'s scoping decision.

## §4 Acceptance criteria

| AC ID | Outcome | Verification |
|-------|---------|--------------|
| AC.WDGUARD.1 | A `Write`/`Edit`/`MultiEdit` whose `file_path` is framework-source AND whose enclosing git repo is NOT canonical loam → hook emits `permissionDecision: deny` with a reason naming the WD-discipline rule + redirecting to canonical `/Users/lukeivers/loam`. | `test_AC_WDGUARD_1_*`: synthetic envelope at a simulated derived-workspace framework-source path (repo with non-canonical / empty origin) → assert deny + reason substrings. |
| AC.WDGUARD.2 | The same framework-source edit under CANONICAL loam (origin matches `github.com/.../loam`) → hook ALLOWS (no deny; exit 0, empty stdout decision). | `test_AC_WDGUARD_2_*`: synthetic envelope at a canonical framework-source path → assert NO deny. |
| AC.WDGUARD.3 | Workspace-local content — `.loam/`, `.scratch/`, `products/`, `workspace/`, memory files, `docs/plans/`, `CLAUDE.md`, `.claude/` infra — is ALLOWED everywhere, including inside a derived workspace. | `test_AC_WDGUARD_3_*`: parametrized envelopes for each workspace-local class at a derived-workspace path → assert NO deny for any. |
| AC.WDGUARD.4 | Override hatch: env `LOAM_WD_GUARD=off` (or the all-safety toggle `LOAM_SAFETY_HOOKS=off`), or a `<repo>/.loam/.wd-guard-override` sentinel file, makes the hook no-op (ALLOW) even for the derived×framework-source cell; the bypass is logged. | `test_AC_WDGUARD_4_*`: derived×framework-source envelope WITH each override active → assert NO deny + a `toggled-off`/`override` log line. |
| AC.WDGUARD.5 | Fail-open: malformed / empty / non-content-tool / unparseable-repo input → hook ALLOWS (exit 0, no deny), never wedges the session. | `test_AC_WDGUARD_5_*`: empty stdin, non-Write tool, missing file_path, and an unresolvable path → assert exit 0 + no deny for each. |
| AC.WDGUARD.S | OUTCOME-ALTITUDE: the real hook script, invoked as a `python <script>` subprocess receiving a PreToolUse envelope on stdin (no pre-arranged internal state, no fakes), (a) BLOCKS a framework-source edit at a simulated derived-workspace path, (b) ALLOWS the same-shaped edit under a canonical-identity repo, (c) ALLOWS a workspace-state edit at the derived path, (d) ALLOWS the derived×framework-source edit when the override env is set. | `test_AC_WDGUARD_S_*`: builds two throwaway temp git repos (one with canonical-matching origin, one with non-canonical origin), runs the production script as a subprocess for each of the four sub-cases, asserts the production deny/allow shape on stdout. |

Every line of the hook maps to one of AC.WDGUARD.{1,2,3,4,5}; AC.WDGUARD.S
is the cross-cutting outcome-altitude proof through the production
entry point. No unnamed branch.

## §5 Sealed-component fence

Single-component fence: **`framework/safety-layer/`**.

- seal_test: `framework/safety-layer/tests/test_no_sealed_amendments.py`
- sidecar: `framework/safety-layer/tests/SEAL_COMMIT`
- frozen_baseline: false
- extra_allowed_prefixes: [] (no cross-component widening — out-of-
  scope installer wiring deferred precisely to keep the fence to one
  component).

Universal admissions: `docs/plans/` (this plan-doc + manifest), plus
the standard `CLAUDE.md` / `docs/STATE.md` universal files (unused
this cycle but admitted per convention).

## §6 Halt triggers

The builder STOPS and surfaces (does not silently extend) when:

- **Detection cannot be made robust without false-positiving on
  canonical.** If the canonical-identity signal would ever BLOCK a
  legitimate framework edit under canonical loam or a canonical
  worktree, HALT — a guard that blocks legitimate framework dev is
  worse than no guard. (Empirically pre-verified clean at plan time —
  see §16 — but re-checked during build via AC.WDGUARD.2 + the
  outcome-altitude test.)
- An ODD §2.5 violation surfaces in this work or surrounding
  safety-layer code.
- The seal-test fails for a reason unrelated to this edit (a
  pre-existing fence breach surfaced by the work).
- WD drift from the named worktree.

## §7 Ship shape

Single sealed cycle (not a sub-amendment series). Commit ladder:

1. `docs(plans):` — this plan-doc + manifest (NEW commit, plan-before-code).
2. `feat(safety-layer):` — the hook + tests (BASELINE; source committed BEFORE apply).
3. `loam amend apply` — auto-commit (sidecar + manifest merge).
4. `loam amend seal` — deterministic seal commit (runs seal-tests).
5. `docs(plans):` — §14 SHA backfill.

LOCAL SEAL ONLY — no push, no publish.

## §10 Named decisions

- **D-Q.1 — Detection signal: canonical-identity by git-remote-URL
  match (positive identity), NOT derived-marker presence (negative
  identity).** See §16 for the empirical justification + the
  false-positive analysis. Recommendation: ADOPT.
- **D-build.1 — Hook lives in `framework/safety-layer/` (shipped),
  not in the workspace `.claude/hooks/`.** So the guard travels with
  the framework to every derived workspace. Recommendation: ADOPT.
- **D-build.2 — Framework-source classification by path prefix +
  workspace-local exclusion list.** A path is framework-source iff it
  is under the repo-relative `framework/` or `plugins/` tree AND is
  not in the workspace-local exclusion set (`.loam/`, `.scratch/`,
  `products/`, `workspace/`, `/memory/`, `docs/plans/`, `CLAUDE.md`,
  `.claude/`, `.git/`). Recommendation: ADOPT.
- **D-build.3 — Override hatch mirrors the safety-layer toggle
  idiom (`LOAM_WD_GUARD=off` / `LOAM_SAFETY_HOOKS=off` / `.loam/.wd-
  guard-override` sentinel), not the in-thread-guard's `.scratch/`
  sentinel.** Consistency with the host component. Recommendation:
  ADOPT.

## §14 Method-decision register

Populated at build + seal time.

- D-Q.1 — signal: canonical-identity-by-remote-URL — SHA: `<feat>` / `<seal>`
- D-build.1 — home: framework/safety-layer/ (shipped) — SHA: `<feat>`
- D-build.2 — classification: prefix + workspace-local exclusion — SHA: `<feat>`
- D-build.3 — override idiom: safety-layer toggle — SHA: `<feat>`

Commit ladder SHAs (backfilled post-seal):
- plan+manifest: `<sha>`
- feat (BASELINE): `<sha>`
- apply: `<sha>`
- seal: `<sha>`

## §15 Backwards-compat verification

- Existing `framework/safety-layer/tests/test_no_sealed_amendments.py`
  (A15/A17/A18 invariants) must stay GREEN — the new hook adds no
  import into sealed modules and no monkeypatch.
- Existing `test_AC_SECHK_{1..5,S}` must stay GREEN — the new hook is
  additive; it does not touch the three existing guards.

## §16 Halt-and-surface findings (plan-authoring)

**The detection-robustness question (the dispatch's named halt
trigger) was resolved at plan time by empirical verification against
the REAL canonical tree + the REAL derived `pos3` layout — NOT
assumption.** Findings:

1. **The vendored framework copy is structurally identical to
   canonical** inside the `framework/` subtree (it carries `LICENSE`,
   `plugins/`, `framework/framework/...`, `install-from-source.txt`).
   So presence-of-framework-files is NOT a usable signal — both
   canonical and the vendored copy have them. A naive
   "looks-like-loam" sentinel would mis-allow the derived case.

2. **The robust distinguishing signal is git-repository IDENTITY.**
   Empirically:
   - Canonical `~/loam` and every canonical worktree
     (`loam-*-wt`, `/private/tmp/loam-*-wt`) carry
     `remote.origin.url = https://github.com/lukeivers/loam.git`.
   - The vendored `pos3/framework` is its OWN nested git repo whose
     `origin` is EMPTY (it tracks canonical via a local-path remote
     named `canonical`, and the outer `pos3-workspace` repo
     `.gitignore`s `framework/`).
   - So: a framework-source edit is CANONICAL iff its enclosing git
     repo has a remote URL matching `github.com[:/]…/loam(.git)?`;
     otherwise it is DERIVED.

3. **No false-positive on canonical.** Because the signal is a
   POSITIVE identity check (the repo must PROVE it is canonical loam
   to be allowed), every real canonical checkout AND every canonical
   worktree passes (all share the canonical origin URL, verified
   across four live worktrees). The guard therefore cannot block
   legitimate framework dev under canonical. The only degenerate
   miss — a freshly-`git clone`d canonical checkout BEFORE its origin
   remote is configured — is rare, is a transient bootstrap state,
   and is covered by the override hatch (AC.WDGUARD.4). This residual
   is acceptable and named; it does not block the build.

Conclusion: the detection IS robust on the real layout; NO halt
required. The build proceeds.
