# v0.2.5 corrective C6 — fixture-PM + extraction-dir resolution + error-message fix — plan

Dev-discipline work; touches one sealed component (`dev-sdlc` / odd-extractor) plus pos-v2 universal `.gitignore`. Single `loam amend` cycle.

**Status:** plan + manifest ready for apply + seal. 2026-05-05.
**Working directory:** /Users/lukeivers/ivers-corp-pos-v2/
**Companions:**
**Ancestor record:** v0.2.5 corrective C5 — `f69fb1f` STATE entry; `4eee938` §14 backfill; `6d2052d` seal; `290ed00` apply; `cf8a338` BASELINE.
**Research:** v0.2.5 HARD smoke 3rd-run report at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-2-5-hard-smoke-3rd-run-report.md` (F-DESIGN-1/2/3).

---

## 1. Summary / TLDR

The 3rd HARD smoke run (post-C4-pivot + C5) closed the F1+F2+F5+F8 history (synthesis pipeline runs end-to-end via `claude -p`). Three new design-shape findings now block GREEN:

- **F-DESIGN-1** — smoke fails stages 2/3/4 because no PM is authored in the `rd-automation` fixture; `--interview` requires a PM and the dependency chain forces clean-exit-2 through stages 2/3/4.
- **F-DESIGN-2** — Stage 2's error message says `Run \`loam project init\``, but `loam project` is NOT a registered subcommand. Bad guidance.
- **F-DESIGN-3** — `loam odd-extract <repo>` resolves the extraction-dir relative to CWD, not relative to `<repo>`. Running from inside pos-v2 against `<rd-automation>` lands artefacts inside the loam tree (`<pos-v2>/.loam/`), not under the target repo.

This corrective lands FIVE ACs that fix all three findings:

- AC.V025-C6.1 — Outcome-altitude smoke-fixture-with-PM test exercises the full 4-stage CLI pipeline end-to-end via subprocess; stages 1-4 all exit 0; produces `objectives.yaml` + `backing-map.yaml` + `gap-inventory.yaml` + `build-next.yaml`.
- AC.V025-C6.2 — `interview.resolve_pm_handle` error message references actionable guidance that names a real CLI surface (or the workspace path + `--pm-handle`); no reference to the nonexistent `loam project init` subcommand.
- AC.V025-C6.3 — Default `--workspace-root` resolves to the target `<repo>` (positional arg), not to `Path.cwd()`. Help text reflects the new default.
- AC.V025-C6.4 — `.loam/` added to pos-v2's `.gitignore` (prevents self-pollution of the loam tree by extraction runs invoked from inside pos-v2).
- AC.V025-C6.5 — Full odd-extractor + dev-sdlc test suites green; no regressions.

Ratifying decisions:
- **D-1 (canonical PM-authoring surface):** there IS no canonical CLI command for authoring a PM in the v0.2.5 codebase. Authoring is a tiny YAML write per the per-project-pm conftest pattern. The smoke fixture writes the YAML directly via the new outcome-altitude test; not a halt-and-surface for a missing `loam project init` because no design ruling is required — the absent CLI is the absence of a surface, not a bug.
- **D-2 (workspace-root default):** change to `<repo>` (positional arg). Existing tests pass `--workspace-root` explicitly; no regressions. New default matches the operational expectation that artefacts live alongside the target.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)

Per CLAUDE.md §2.5 (every line of code/branch/test maps to a named AC), this corrective lands FIVE ACs that together fence: outcome-altitude smoke (AC.V025-C6.1), error-message correctness (AC.V025-C6.2), extraction-dir default semantics + help-text (AC.V025-C6.3), pos-v2 self-pollution prevention (AC.V025-C6.4), and no-regression guarantee on full suite (AC.V025-C6.5).

This corrective claims its own V025-C6.* prefix scoped to the C6 corrective itself, mirroring the C4-pivot + C5 precedents (V025-C4P.*, V025-C5.*).

---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude leverage

The fixture-PM smoke test is plain Python; the workspace-root resolution change is plain argparse. No Claude-specific primitive applies. The error-message fix points users at the actual CLI surface (`--pm-handle` + workspace path) rather than a phantom subcommand.

### Lens 2 — Harness + primary-persona value

Primary-persona test: F-DESIGN-3 directly hurts Eric's onboarding — running `loam odd-extract <his-repo>` from anywhere lands artefacts in CWD, surprising the user. F-DESIGN-2 sends the user chasing a nonexistent command. Both reduce friction.

Harness test: the new outcome-altitude smoke fixture becomes a durable "the CLI works end-to-end against a fixture with a PM authored" probe — extends the toolkit; future stages can reuse the pattern.

### Lens 3 — ODD authoring

Five outcome-shaped ACs. None state HOW (no "use Path.cwd() / use args.repo_path" in the AC body); each pins WHAT the observable surface is. The method (argparse default lambda; YAML-write in fixture; gitignore line) lives in §14 and in the implementation.

### Lens 4 — Prompt scope ↔ confidence

High confidence: the three findings are crisply diagnosed in the smoke report; the fix shapes are obvious (rewrite error string; change one default; add one gitignore line; new test mirroring existing ratification + persona-pull test patterns). Tight scope appropriate.

### Lens 5 — Swarming

Single corrective with two cross-cutting concerns (CLI semantics + smoke test). Decomposing further (one agent per AC) adds coordination overhead with no tighter AC. Single agent.

---

## 4. Acceptance criteria (V025-C6 — dev-discipline plan)

### AC.V025-C6.1 — Outcome-altitude smoke fixture authors PM and exercises full 4-stage pipeline

A new outcome-altitude test in `plugins/dev-sdlc/odd-extractor/tests/` exercises the full `loam odd-extract` 4-stage pipeline (stages 1-4) end-to-end against a canonical fixture (`jsts-playwright-app`) — running through extraction → `--interview` → `--gaps` → `--build-next` — with a stub PM authored inline at `<workspace>/workspace/.loam/pms/<handle>/contract.yaml` BEFORE invocation. All four stages MUST exit 0; the test MUST assert all four stage-output artefacts exist (`objectives.yaml`, `augmented-objectives.yaml`, `gap-inventory.yaml`, `build-next.yaml`).

The test is OUTCOME-class per `odd-test-altitude-discipline` SKILL: production CLI surface (`cli.main`) invoked, no monkeypatch / mock of the synthesis client / subprocess / claude binary, asserts on production-produced artefacts. Skips cleanly when `claude` binary is absent from PATH (mirrors C3.3 / C4.3 skip semantics).

**Verification:** the test is named `test_AC_V025_C6_1_*.py`; test runs PASS on the build workstation (`claude` available); test SKIP-passes in environments without `claude`; the four named artefacts exist in the post-run extraction directory.

### AC.V025-C6.2 — Error message references actionable guidance, not nonexistent `loam project init`

`interview.resolve_pm_handle` raises `OddExtractorError` whose message MUST NOT reference `loam project init` (which is not a registered subcommand). The message MUST name (a) the workspace-relative path where a PM contract.yaml is expected (e.g., `<workspace>/workspace/.loam/pms/<handle>/contract.yaml`) AND (b) the `--pm-handle` CLI flag as the explicit-disambiguation path; both are paths a user can act on without an additional CLI surface that does not exist.

**Verification:** `grep -r "loam project init"` across the source tree returns zero hits in implementation paths (test fixtures may still mention the historical phrase if part of an updated assertion-set); a manual `loam odd-extract <repo> --interview` against a workspace with no PM produces an error message containing both `<workspace>/workspace/.loam/pms/` and `--pm-handle`. The pre-existing AC.V025-C2 invariants (clean exit, no Python traceback, OddExtractorError shape) remain satisfied.

### AC.V025-C6.3 — Default `--workspace-root` resolves to the target `<repo>` positional arg

When `--workspace-root` is not passed, `_resolve_workspace_root` returns the resolved `<repo>` positional path (i.e., `args.repo_path.expanduser().resolve()`), NOT `Path.cwd()`. The argparse help text for `--workspace-root` MUST describe the new default ("default: target `<repo>` positional arg"). All existing tests that pass `--workspace-root` explicitly remain unchanged in behaviour.

**Verification:** unit test invokes `cli.main([str(repo)])` (no `--workspace-root`) from a CWD different from `repo` and asserts the extraction directory lands at `<repo>/.loam/extractions/<repo-id>/`, not at `<cwd>/.loam/extractions/`. Help-text assertion: `loam odd-extract --help` stdout contains the new default-description string.

### AC.V025-C6.4 — pos-v2 `.gitignore` excludes `.loam/`

Pos-v2's `.gitignore` MUST list `.loam/` so that smoke runs invoked from inside pos-v2 (which historically wrote to `<pos-v2>/.loam/` due to the cwd-default; now mitigated by C6.3 but still possible if a developer explicitly passes `--workspace-root <pos-v2>`) do not leave untracked content under git observation.

**Verification:** `.loam/` appears as a top-level entry in `<pos-v2>/.gitignore`; `git check-ignore .loam/` reports the path is ignored; existing untracked `.loam/extractions/` content is excluded from `git status` reports.

### AC.V025-C6.5 — Full odd-extractor + dev-sdlc test suites pass; no regressions

Sealed AC tests at `plugins/dev-sdlc/odd-extractor/tests/` and `plugins/dev-sdlc/tests/` MUST remain fully green after the change. Pre-C6 baseline (post-C5): 932 + 2 skip; post-C6 expectation: 932+ pass + ≥1 new test (C6.1 is OUTCOME-class so adds 1 test that passes when claude is available, skips otherwise; C6.2 may add 1 unit test; C6.3 may add 1 unit test). The pre-existing `test_AC_V025_C1_C2_cli_synthesis_and_interview_error.py:354-357` assertion (which OR-asserts `loam project init` presence) MUST be updated to remove the nonexistent-command reference and assert against the corrected message.

**Verification:** `pytest plugins/dev-sdlc/odd-extractor/tests/ plugins/dev-sdlc/tests/` pass-count meets or exceeds the post-C5 baseline + new C6 tests; no sealed-AC test fails.

---

## 5. Behaviour-count check (ODD §3.3 forward; applied as dev-discipline check)

| # | Declared behaviour | AC |
|---|--------------------|-----|
| 1 | Outcome-altitude smoke test exercises full 4-stage CLI pipeline against fixture-with-PM and produces all 4 stage artefacts | AC.V025-C6.1 |
| 2 | `resolve_pm_handle` error message references `<workspace>/workspace/.loam/pms/` + `--pm-handle`; no reference to `loam project init` | AC.V025-C6.2 |
| 3 | `_resolve_workspace_root` defaults to target `<repo>` (positional); help-text reflects the new default | AC.V025-C6.3 |
| 4 | Pos-v2 `.gitignore` excludes `.loam/` to prevent self-pollution | AC.V025-C6.4 |
| 5 | Full odd-extractor + dev-sdlc suites green (post-C5 baseline preserved) | AC.V025-C6.5 |

---

## 6. Hard constraints

1. **No `--amend`.** Corrective new commits only. The C4-pivot agent's `--amend` deviation is exactly the failure mode to avoid.
2. **Scope fence.** Edits limited to:
   - `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/interview.py` (error-message text)
   - `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/cli.py` (workspace-root default + help text)
   - new test files under `plugins/dev-sdlc/odd-extractor/tests/`
   - `plugins/dev-sdlc/odd-extractor/tests/test_AC_V025_C1_C2_cli_synthesis_and_interview_error.py` (remove `loam project init` from OR-assertion)
   - `.gitignore` (add `.loam/`)
   - `docs/rebuild/plans/v0-2-5-corrective-c6-fixture-pm-and-extraction-resolution.{md,manifest.yaml}`
   - `docs/rebuild/STATE.md` (post-seal entry)
3. **No edit to per-project-pm component.** Authoring stays inline-YAML in tests (matches existing `_author_pm` pattern across 5+ test files).
4. **No new CLI subcommand.** Do not invent `loam pm new` / `loam project init` or similar; this corrective is bounded to message + default + test.
5. **No new third-party dependency.** Stdlib only.
6. **Backward-compat preserved.** All sealed AC tests green; no API surface change beyond the documented default-shift on `--workspace-root`.
7. **CDC adherence.** No new CDC; this corrective extends the existing dev-sdlc seal pattern.

---

## 7. Out of scope (explicit)

- F-DESIGN-4 (pre-existing telegram watchdog stall — predates the smoke window by ~33h; separate operational issue).
- Pushing pos-v2 to remote.
- Tagging.
- Eric outreach.
- Anthropic SDK reintroduction (C4-pivot decision stands).
- Touching `loam_odd_extractor.spec.py` validator.
- Patching the telegram MCP loader.
- Inventing a `loam project init` / `loam pm new` CLI surface.
- Updating sealed-AC `interview.py` body beyond the error-message text (the resolution logic itself is correct; only the actionable phrase is wrong).

---

## 8. Implementation order (suggested — builder's call to refine)

1. Verify pwd is `/Users/lukeivers/ivers-corp-pos-v2`.
2. Read this plan-doc + the C5 plan-doc + the 3rd HARD smoke report + `interview.py` + `cli.py` + the existing `_author_pm` test pattern + the C3.3/C4.3 outcome-altitude test pattern.
3. Edit `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/interview.py`:
   - Replace the `Run \`loam project init\`...` phrase with a workspace-relative-path + `--pm-handle` actionable message.
4. Edit `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/cli.py`:
   - Change `_resolve_workspace_root` body to default to `args.repo_path` when `arg is None`. Signature shift: pass `repo_path` to the helper, OR inline the default at each call site (cleaner; only 4 call sites in `_cmd_extract`/`_cmd_status`/`_cmd_resume`/`_cmd_interview`/`_cmd_gaps`/`_cmd_build_next`/`_cmd_ratify`/`_cmd_incremental` — 8 call sites; helper-with-extra-arg is cleaner).
   - Update `_add_workspace_root_arg` help-text default-description.
5. Edit `plugins/dev-sdlc/odd-extractor/tests/test_AC_V025_C1_C2_cli_synthesis_and_interview_error.py`:
   - Remove the `or "loam project init" in err_lower` clause; assert on `--pm-handle` + path-shape only.
6. Author NEW tests:
   - `test_AC_V025_C6_1_cli_full_pipeline_with_authored_pm.py` — outcome-altitude full-4-stage smoke; authors PM inline; runs `cli.main` for each stage; asserts stage-output artefacts exist.
   - `test_AC_V025_C6_2_interview_error_message.py` — unit test asserts error message contains workspace path + `--pm-handle`; does NOT contain `loam project init`.
   - `test_AC_V025_C6_3_workspace_root_default_is_repo.py` — unit test invokes CLI without `--workspace-root` from a different CWD; asserts extraction lands at `<repo>/.loam/extractions/`.
7. Edit `.gitignore`:
   - Add `.loam/` line (top-level).
8. Run narrow tests: new C6 tests pass.
9. Run full odd-extractor + dev-sdlc test suites.
10. Author manifest at `docs/rebuild/plans/v0-2-5-corrective-c6-fixture-pm-and-extraction-resolution.manifest.yaml`.
11. `git add` files; conventional commit ladder:
    - feat: source + tests (BASELINE)
    - docs: plan-doc + manifest
    - chore(amend): manifest + apply
    - chore(seals): seal commit (via `loam amend seal`)
    - docs(plans): §14 SHA backfill (auto-emitted by `--plan-doc`)
    - docs(state): STATE.md entry (post-seal)
12. Run `loam amend apply <manifest>` then `loam amend seal --plan-doc <plan-doc> <manifest>`.
13. Write build report to `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-2-5-corrective-c6-report.md`.

---

## 9. Bookkeeping surface

Sealed-component touched: `dev-sdlc` (odd-extractor + plugin). One sidecar bump via `loam amend apply`.

```yaml
schema_version: 3
amendment:
  slug: v0-2-5-corrective-c6-fixture-pm-and-extraction-resolution
  title: <rendered at manifest authoring time>
baseline: <pinned to source-edit feat commit SHA at manifest commit time>
plan: docs/rebuild/plans/v0-2-5-corrective-c6-fixture-pm-and-extraction-resolution.md
plan_doc_ref: docs/rebuild/plans/v0-2-5-corrective-c6-fixture-pm-and-extraction-resolution.md
ac_count: 5
smoke_outcome: "C6.1 outcome-alt smoke green; C6.2 err-msg actionable; C6.3 ws-root default=<repo>; C6.4 .gitignore .loam/; C6.5 suite green"
components:
  - name: dev-sdlc
    seal_test: plugins/dev-sdlc/tests/test_no_sealed_amendments.py
    sidecar: plugins/dev-sdlc/tests/SEAL_COMMIT
    frozen_baseline: false
    extra_allowed_prefixes: []
universal_paths:
  prefixes:
    - docs/rebuild/plans/
  files:
    - CLAUDE.md
    - docs/odd-in-loam.md
    - docs/odd-methodology.md
    - docs/rebuild/STATE.md
    - docs/rebuild/FUTURE_IDEAS_DRAFT.md
    - .gitignore
narrative:
  target: plugins/dev-sdlc/seals/SEAL_COMMIT.v0-2-5-corrective-c6-fixture-pm-and-extraction-resolution
```

Single combined seal "v0.2.5 corrective C6 — fixture-PM + extraction-dir resolution + error-message fix" per dispatch brief. STATE.md entry mirrors the C5 inline format.

---

## 10. Halt triggers (builder halts + signals owner)

1. `loam amend apply` or `loam amend seal` errors. Halt; investigate.
2. Cross-component scope expansion beyond the named scope fence. Halt.
3. Backward-compat broken (sealed AC test fails). Halt.
4. New third-party dependency required. Halt.
5. ODD violation observed in surrounding code/docs. Halt; do NOT extend.
6. Concurrent agent activity detected (`pos-amend` lock or simultaneous build). Halt.
7. Default workspace-root shift breaks ≥1 sealed-AC test that doesn't pass `--workspace-root`. Halt; surface for ruling.

---

## 11. Decisions remaining for the owner to rule on

(none — D-1 + D-2 closed in §1.)

---

## 12. Summary of named decisions (owner-readable)

| Decision | Recommendation | Why it matters |
|---|---|---|
| D-1 — canonical PM-authoring CLI? | NONE exists; smoke test authors inline YAML per existing `_author_pm` pattern | No design ruling required; the absent CLI is not a bug; tiny YAML write is the pattern across 5+ existing test files |
| D-2 — workspace-root default | Change to target `<repo>` positional arg | Aligns with operational expectation; existing tests pass `--workspace-root` explicitly so no regressions; C6.3 verifies cwd-default no longer pollutes user-CWD |

---

## 13. Halt-and-surface findings encountered during plan authoring

Per `feedback_subagent_odd_violation_halt`: halt and surface any ODD violation observed in surrounding code/docs.

**(none observed during plan authoring.)** The `_resolve_workspace_root` helper, `resolve_pm_handle` function, and the per-project-pm test fixture pattern (`_author_pm`) are all clean, outcome-scoped surfaces. The fix is local to those three.

---

## 14. Method-decision record (builder, post-build)

The plan §11 left D-build.x method choices to the builder within the ACs' outcome bounds. This section is populated post-build.

### D-build.1 — workspace-root default shape

(placeholder — to be filled by builder post-implementation; named candidates were "helper-with-extra-arg" vs "inline-default-at-each-callsite". Helper-with-extra-arg chosen for centralized maintenance.)

### Test breakdown

(placeholder)

### Backwards-compat verification

(placeholder)

### Commit SHAs

(placeholder — auto-emitted by `loam amend seal --plan-doc`.)

---

## 15. References

- v0.2.5 HARD smoke 3rd-run report: `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-2-5-hard-smoke-3rd-run-report.md`
- v0.2.5 corrective C5 plan-doc: `docs/rebuild/plans/v0-2-5-corrective-c5-claude-print-mcp-isolation.md`
- per-project-pm conftest pattern: `framework/per-project-pm/tests/conftest.py` (`_author_pm` / `MIN_VALID_CONTRACT_YAML`)
- C3.3 / C4.3 outcome-altitude precedent: `plugins/dev-sdlc/odd-extractor/tests/test_AC_V025_C4_3_cli_live_outcome_altitude_post_fix.py`
- `odd-test-altitude-discipline` SKILL: `plugins/dev-sdlc/skills/odd-test-altitude-discipline/SKILL.md`
- ODD lean grounding: `docs/odd-llm-grounding.lean.md`
