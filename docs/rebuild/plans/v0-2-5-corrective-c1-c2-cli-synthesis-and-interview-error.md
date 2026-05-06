# v0.2.5 Corrective C1+C2 — CLI synthesis wire-through + `_cmd_interview` ValueError leak

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-05 (Sonnet, single-agent plan-author + builder).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Predecessor:** v0.2.4 SHIPPED `4f54649` (Cycle 3 seal `064cc2e`). v0.2.5 HARD smoke against rd-automation completed RED with two named blockers (smoke evidence at `<pos3>/workspace/.scratch/claude-output/v0-2-5-hard-smoke-report.md`).

**Authority:** v0.2.5 dispatch brief explicitly authorized "land both correctives so the v0.2.5 HARD smoke can re-run GREEN" using the v0.2.1 corrective amendment precedent (`loam amend apply` + `loam amend seal`).

**BASELINE (pre-build tip):** to be set to the source-edit feat commit when the build commit lands.

---

## §1 — Outcome shape (the "why")

The v0.2.5 HARD smoke against rd-automation surfaced two BLOCKERs:

1. **F1 — CLI synthesis wire-through gap.** `loam odd-extract <repo> --live` produces `objectives: []` end-to-end via the CLI. Root cause: `cli._cmd_extract` calls `generate_raw_acs(config=config, plan=plan)` — never threading an Anthropic client. Inside `generate_raw_acs`, `synthesis_required` defaults to `False`, so the synthesis pass falls into `_empty_synthesis_result` (`generate.py:206-208`). Backing-map population is gated on non-empty objectives (`generate.py:229`), so it's also skipped. `synthesis.build_default_anthropic_client()` exists but is unused by the CLI. The SOFT release smoke (`test_AC_PERSONA_PULL_4_release_smoke.py`) didn't catch this because it bypasses the CLI — it writes canned `objectives.yaml` + `backing-map.yaml` directly via `_relsmoke_helpers.write_canned_objectives_and_map`.

2. **F2 — `_cmd_interview` ValueError leak.** `interview.resolve_pm_handle` raises Python builtin `ValueError` on zero-PMs / multiple-PMs (interview.py:295, 301). The CLI's `_cmd_interview` only catches `OddExtractorError` (cli.py:452), so a Python traceback escapes to the user instead of an actionable error message + exit 2.

The fixes are surgical and orthogonal:
- **C1:** `_cmd_extract` constructs `synthesis.build_default_anthropic_client()` when `args.live` is set; passes it through to `generate_raw_acs(..., anthropic_client=client, synthesis_required=args.live)`. The client flows transitively into backing-map population via `generate.py:238`. Lazy-import failure (anthropic SDK missing) raises `StageError → OddExtractorError`, caught by the existing `except OddExtractorError` block and emitted as actionable stderr + exit 2 (NOT a Python traceback).
- **C2:** `interview.resolve_pm_handle` raises `OddExtractorError` instead of `ValueError` so the existing CLI catch produces clean exit 2 + actionable message. Aligns with the existing exception hierarchy (`errors.py:OddExtractorError` is the base; `_cmd_interview` already catches it).

**Why both correctives ship as one amendment.** Both are v0.2.5 HARD-smoke RED BLOCKERs. The two changes touch different files (cli.py + interview.py) but both fix the same release-gating evidence document. v0.2.1 corrective F1 / F2 shipped as separate amendments because they touched different components (odd-extractor vs workspace-bootstrap); C1 + C2 both touch only odd-extractor, so a single combined corrective amendment is structurally simpler and matches v0.2.1 corrective F1's single-amendment-multi-AC precedent.

---

## §2 — ACs — `AC.V025-C1` + `AC.V025-C2` + `AC.V025-C3` (locked, 3 ACs)

ODD §2.5: every line of code, every branch, every test maps to a named AC.

- **AC.V025-C1 — CLI synthesis wire-through.**
  - Surface: `cli._cmd_extract` constructs `synthesis.build_default_anthropic_client()` when `args.live` and the generate stage is active; passes the client into `generate_raw_acs` along with `synthesis_required=args.live`. Lazy-import failure raises `StageError → OddExtractorError`; existing CLI catch emits actionable error + exit 2.
  - Test: `test_AC_V025_C1_C2_cli_synthesis_and_interview_error.py::test_AC_V025_C1_cli_live_produces_real_objectives_via_synthesis` — runs `cli.main([<repo>, "--live", "--budget-cents", "100", "--budget-override", "--workspace-root", <ws>])` against the canonical `jsts-playwright-app` fixture; monkeypatches `synthesis.build_default_anthropic_client` to return a 2-shot stub (synthesis JSON + backing-map verdicts); asserts `objectives.yaml` carries ≥1 objective, `backing-map.yaml` exists, `synthesis.yaml.model_id != "(none)"`, and the stub was invoked at least once.
  - Pre-fix verification: the test FAILS on current `_cmd_extract` (objectives empty post-run; reproduces the smoke finding F1).

- **AC.V025-C2 — `_cmd_interview` ValueError leak fixed.**
  - Surface: `interview.resolve_pm_handle` raises `OddExtractorError` instead of `ValueError` on zero-PMs / multiple-PMs. Existing `_cmd_interview` catch (cli.py:452) traps it and emits actionable error + exit 2.
  - Test: `test_AC_V025_C1_C2_cli_synthesis_and_interview_error.py::test_AC_V025_C2_interview_no_pm_emits_clean_error_no_traceback` — pre-authors an extraction-dir with empty `objectives.yaml`, then invokes `loam odd-extract <repo> --interview` against a workspace with no PM authored; asserts (a) exit code is non-zero, (b) stderr contains "no pm authored" / "loam project init" / "--pm-handle", (c) NO `Traceback (most recent call last)` substring in stderr/stdout.
  - Pre-fix verification: the test FAILS on current `_cmd_interview` (uncaught `ValueError`; reproduces smoke finding F2).

- **AC.V025-C3 — All existing tests still pass.**
  - Surface: structural — fix MUST NOT regress any sealed AC.
  - Test: meta-AC honored by running full odd-extractor test suite (`pytest plugins/dev-sdlc/odd-extractor/tests/`) at seal-time and verifying zero new failures vs the v0.2.4 baseline (813 passed, 1 skipped). Post-fix expectation: 815 passed, 1 skipped (813 + 2 new C1/C2 tests). One test (`test_AC_OREK_6_budget_envelope.py::test_live_with_override_proceeds`) is updated to monkeypatch `build_default_anthropic_client` since it previously depended on the F1 bug (silent synthesis no-op); the AC.OREK.6 invariant under test (budget-override audit-log entry) is preserved.

---

## §3 — Build dispatch brief (folded into this run)

This corrective amendment is single-agent: plan-author + builder are the same Sonnet run per dispatch. Build sequence:

1. **Plan-doc + manifest commit** (this commit).
2. **Source-edit feat commit (BASELINE).** Edit `cli.py` (~16 lines added in `_cmd_extract`); edit `interview.py` (replace 2 `ValueError` → `OddExtractorError`; add import); edit `test_AC_OREK_6_budget_envelope.py::test_live_with_override_proceeds` to monkeypatch `build_default_anthropic_client`; add new test file `test_AC_V025_C1_C2_cli_synthesis_and_interview_error.py`. Single commit subject: `fix(odd-extractor): wire CLI synthesis client + convert resolve_pm_handle ValueError to OddExtractorError (v0.2.5 corrective C1+C2)`.
3. **Manifest+apply commit.** `loam amend apply <this manifest>` produces a single merged commit per AC.DPS1.6 schema-v3.
4. **Seal commit.** `loam amend seal --plan-doc <abs path> <this manifest>` produces deterministic short-form seal commit per AC.DPS2 schema-v3 + a §14 backfill follow-up commit per AC.D-sa.7.

**No `git --amend`. No push. Single semantic commit per stage.**

---

## §4 — Halt triggers + bookkeeping

**Halt-and-surface triggers (per dispatch brief):**
- `pwd` ≠ `/Users/lukeivers/ivers-corp-pos-v2` — handled at start.
- Pre-fix integration test (the C1 verification test) does NOT actually fail before the fix — addressed: both tests verified failing pre-fix, passing post-fix.
- Any v0.2.1 / v0.2.2 / v0.2.3 / v0.2.4 test regresses post-fix — addressed: full odd-extractor suite green; updated `test_AC_OREK_6_*::test_live_with_override_proceeds` test was previously coupled to the F1 bug (silent synthesis no-op) — its AC.OREK.6 invariant (budget-override audit-log entry) is preserved.
- `loam amend apply` or `loam amend seal` errors out — TBD at apply/seal time.
- Any push attempt (you should not push; if you did, halt and surface) — n/a; no push.
- Any tag attempt — n/a; no tag.
- A third BLOCKER surfaces during the build that's not C1, C2, or C3 — none surfaced.

**ODD §2.5 surrounding-code observations (per principle 2 — halt-and-surface on adjacent ODD violations):**
- F3 (analyze framework/-skip) and F4 (v0.2.1 F1-corrective seal-text doc-drift) are explicitly out-of-scope per the dispatch brief; pushed to FIDRAFT.

**Bookkeeping:**
- `loam amend apply` (= `pos-amend apply`). NOT `git --amend`. NOT manual `git commit`.
- Manifest schema v3.
- Single semantic commit on apply. Subject: `fix(odd-extractor): wire CLI synthesis client + convert resolve_pm_handle ValueError to OddExtractorError (v0.2.5 corrective C1+C2)`.
- Short-form seal commit per AC.DPS2 schema-v3.
- §14 backfill via `loam amend seal --plan-doc` flag (separate post-seal commit per AC.D-sa.7).
- NO push; NO tag; v0.2.5 release-tag remains gated on Luke's ship ruling.

---

## §5 — Smoke (REALISTIC CONDITION — applicable dimensions)

**D1 cold-state.** Fresh tmp workspace via `tmp_path`; fresh extraction via `cli.main([<repo>, "--live", ...])`; assert objectives.yaml carries ≥1 objective, backing-map.yaml exists. Verified by AC.V025-C1.

**D2 steady-state.** Re-running `loam odd-extract` on byte-identical inputs produces byte-identical artefacts (synthesis is idempotent on idempotent inputs; backing-map skip-fired via `is_idempotent_skip` on objective-count match). Inherited from v0.2.3 idempotence verification (AC.BACKMAP.D2 + AC.OBJX.D2); not re-verified per fix-scope.

**D3 restart.** N/a structurally — `_cmd_extract` is stateless on entry; restart equivalent is re-run with same workspace.

**D4 reboot.** N/a — one-shot CLI; D4 collapses to D5 for one-shot CLIs per `plugins/dev-sdlc/docs/smoke-test-discipline.md`.

**D5 cross-session.** Extractor in process A writes objectives.yaml; the augmented-objectives + gap-analysis stages in fresh process B parse them cleanly. Inherited from v0.2.4 cross-session verification (AC.COMPINT + AC.GAPAN); not re-verified per fix-scope.

**D6 telemetry-floor.** `_cmd_extract` continues to write the same audit-log entries (`extraction_start`, `stage_complete:init/analyze/generate/verify`, `extraction_end`); when synthesis runs, `synthesis_complete` and `backing_map_populated` entries are emitted (per existing generate.py / backing_map.py audit-log primitives). Verified structurally — audit-log writes are unchanged by this fix.

**PLUS: full-suite green sweep** — pre-corrective odd-extractor tests at HEAD all pass post-corrective; halt + surface on any regression. Verified by AC.V025-C3 (815 passed, 1 skipped — same shape as the v0.2.4 baseline + 2 new tests).

---

## §6 — FIDRAFT entries authored for F3 + F4

Per dispatch brief out-of-scope guidance, append F3 + F4 captures to `docs/rebuild/FUTURE_IDEAS_DRAFT.md` under a new "v0.2.5 yellow findings" subsection. F3 = odd-extractor analyze step has no `framework/` skip (latent gap; not load-bearing in current smoke). F4 = v0.2.1 F1-corrective seal text references retired contract-draft fields (post-v0.2.3 Cycle 3 doc drift; no functional bug). Both surfaced by the v0.2.5 HARD smoke; both deferred per dispatch.

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Corrective amendment scope is tight (CLI client wire-through + ValueError → OddExtractorError conversion).

**Method decisions:**

- **Combined vs split corrective.** Both C1 + C2 ship as one amendment, not two. Rationale: both fixes are v0.2.5 HARD-smoke RED BLOCKERs against the same release; both touch only odd-extractor (vs v0.2.1 correctives F1/F2 which crossed component boundaries). Combined matches v0.2.1 corrective F1 single-amendment-multi-AC precedent.

- **C2 implementation: `OddExtractorError` vs catch-and-convert in CLI.** Picked option (a) — convert `resolve_pm_handle`'s `ValueError` raises to `OddExtractorError`. Rationale: (1) the existing exception hierarchy (`errors.py`) already centralizes user-facing CLI errors under `OddExtractorError`; the resolution function is the natural place to raise the typed error. (2) The existing `_cmd_interview` catch (`except OddExtractorError`) already does the right thing (emits actionable stderr + exit 2); no CLI-side change needed. (3) No tests asserted `pytest.raises(ValueError)` on `resolve_pm_handle` — verified via grep of the full test surface — so the swap is semantically safe.

- **AC.V025-C1 fixture choice.** Used `jsts-playwright-app` per dispatch suggestion. Rationale: it's the canonical existing fixture used by `test_AC_PERSONA_PULL_4_release_smoke`; mirroring that test's `_setup_jsts_repo` helper keeps the shape consistent. The test exercises the synthesis + backing-map pass via a 2-shot stub (synthesis JSON for the first messages.create call; verdict array for subsequent calls).

- **`test_live_with_override_proceeds` test-update.** Pre-fix the test passed because `--live` silently no-op'd the synthesis pass. Post-fix `--live` actually constructs a client; the test must monkeypatch `build_default_anthropic_client` to inject a stub. The AC.OREK.6 invariant (budget-override audit-log entry) is preserved. This is a bug-coupling fix, not a regression.

### Commit SHAs

**Bookkeeping note (2026-05-05):** the v0.2.5 corrective C1+C2 source edits (`cli.py`, `interview.py`, `test_AC_OREK_6_*.py`, new `test_AC_V025_C1_C2_*.py`) landed inside the parallel `odd-test-altitude-procedural-fix` amendment cycle's apply commit `16d6e50` rather than under their own separately-named `loam amend apply` commit. The v0.2.5 corrective plan-doc + manifest are at `c098b3b`. The parallel `odd-test-altitude-procedural-fix` amendment cycle was authored / dispatched / applied / sealed by the dispatcher concurrently with this build; its apply step swept my unstaged source edits into its merged-manifest+apply commit. This is anomalous for the v0.2.1 corrective F1 precedent (which used a dedicated source-edit feat commit + dedicated apply + seal); the functional outcome is the same (fixes shipped, tests green) but the audit trail bundles the v0.2.5 corrective into the odd-test-altitude cycle's seal. The v0.2.5 corrective manifest at `c098b3b` did NOT receive its own separate apply/seal commits.

- Plan-doc + manifest commit (v0.2.5 corrective C1+C2): `c098b3b` (jointly with `odd-test-altitude-procedural-fix` plan-doc; same author commit)
- Source-edit feat commit (BASELINE) — functionally absorbed: `16d6e50` (titled `chore(amend): odd-test-altitude-procedural-fix manifest+apply` but containing the v0.2.5 corrective source edits)
- Manifest baseline-pin commit (v0.2.5 corrective): N/A — separate apply was not run
- Amendment apply commit (v0.2.5 corrective): N/A — fixes apply-pinned via `16d6e50`
- Seal commit: `a9bc524` (titled `chore(seals): odd-test-altitude-procedural-fix — dev-sdlc at 16d6e50`; the v0.2.5 corrective source edits ride along)
- §14 backfill commit: `876bf66` (titled `docs(plans): record odd-test-altitude-procedural-fix commit SHAs in method-decision register`; v0.2.5 corrective §14 backfill — THIS doc — lands as a separate post-seal commit)
- v0.2.5 corrective §14 backfill (this doc-update + STATE.md + FIDRAFT F3/F4): `e699958`

**Verification at HEAD `876bf66`:** full odd-extractor test suite is 815 passed / 1 skipped (vs v0.2.4 baseline 813 / 1; the +2 tests are AC.V025-C1 + AC.V025-C2). No regressions. The fixes are functionally complete; v0.2.5 HARD smoke can re-run GREEN.
