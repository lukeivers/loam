# v0.3.0 Cycle 4 — Lint pass + cross-mode-debt shrinkage + F3/F4 closures

**Status:** sub-plan-doc; expanded from stub at cycle-dispatch time per `plan-docs-author` SKILL master-vs-sub-plan trim discipline.
**Slug:** `v0-3-0-cycle-4-lint-pass-cross-mode-debt-f3-f4`
**Date authored:** 2026-05-08 (stub); expanded 2026-05-08 at dispatch.
**Parent master plan:** `docs/plans/v0-3-0-master-plan.md` §3 Cycle 4.
**Predecessor cycles:** Cycle 1 (sealed at `459c7fc`); Cycle 2 (sealed at `013553e`); Cycle 3 (sealed at `be48b34`).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## §1 — Outcome shape (the "why")

Close out language-tooling debt + named-FIDRAFT items so subsequent cycles inherit a clean lint baseline. Three semi-orthogonal threads bundled because each individually is small (~15–30 min) and per-item decomposition would add 3 micro-cycles with no AC tightening (Lens 5 stopping criterion).

A stranger running `ruff check framework/ plugins/` against a fresh canonical clone sees a sharply reduced violation count vs the v0.2.5.1 baseline; the residual surface is enumerated as ratification candidates with explicit out-of-scope-for-C4 framing. The `KNOWN_CROSS_MODE_DEBT` allowlist in `loam-mode/tests/test_partition_references.py` shrinks to the empty set (post-C2 graphiti rip-out made the lone entry's source path non-existent on disk). The odd-extractor `analyze._SKIP_DIR_NAMES` mirrors the v0.2.1 corrective F2 fix in `workspace-bootstrap/.../language_detection.py` — both codepaths now skip `framework/` to prevent loam-internal source leaking into evidence rows. The v0.2.1 corrective F1 plan-doc carries a top-of-file addendum stating its `acs:` / `unhandled_paths:` field-write was retired by v0.2.3 Cycle 3.

## §2 — Prime objective ladder

VALUE_PROPOSITION.md prime objective → v0.3.0 release-roadmap §3 outcome ("documented features work as advertised AND terminology is consistent across forward-looking surface") → AC.V030.6 (lint pass clean) + AC.V030.9 (F3 + F4 close) + AC.V030.10 (KNOWN_CROSS_MODE_DEBT shrinkage) → C4 ACs below.

## §3 — Component fence

PRIMARY (this cycle authors):
- `framework/` + `plugins/` (lint auto-fix sweep — 339 files touched; mostly unused-import + unused-variable removal).
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/analyze.py` (F3 — `_SKIP_DIR_NAMES` extends with `framework`).
- `plugins/dev-sdlc/odd-extractor/tests/test_AC_LDC_F3_framework_skip.py` (NEW — 3 tests asserting the F3 skip behavior).
- `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_references.py` (KNOWN_CROSS_MODE_DEBT shrunk 1 → 0).
- `docs/plans/v0-2-1-corrective-f1-odd-extractor-contract-draft-fields.md` (F4 — top-of-file addendum naming v0.2.3 Cycle 3 supersession).

Secondary (verified post-build):
- 372 dev-sdlc tests + 74 odd-extractor F3-and-related tests green post-fix sweep (no regression).

Excluded from this cycle:
- `mypy --strict` exit-0 across framework/ + plugins/ — surface as ratification candidate (pre-existing structural issues; per-component config authoring needed; halt-and-surface §10 candidate).
- ruff residual 87 errors (F841/E402/E741/E731/F811/F821) — surface as ratification candidates (mostly intentional unused-vars in tests; some are real and need design ruling).
- Lint integration into dev-sdlc PR-safety pipeline — FIDRAFT entry; future minor (v0.3.x or v0.4.x per FIDRAFT line 60-ish).
- Pre-existing tests not touched by lint sweep (sealed-component fences) — read-only.
- Live-API tests under odd-extractor (claude-subprocess-invoking tests) — out of scope for this cycle's verification.

Bookkeeping owner: `dev-sdlc` with `frozen_baseline: true` (mirroring C1 + C2 + C3 pattern; cycle's seal anchor sits with the methodology-surface owner).

## §4 — AC family `AC.LDC.*`

- **AC.LDC.1 — Ruff auto-fix sweep applied across framework/ + plugins/.** Pre-fix baseline: 765 errors (653 F401 unused-import + 68 F841 unused-variable + 15 F541 f-string-missing-placeholder + 8 E402 + 7 E741 + 5 E731 + 5 F811 + 2 E401 + 2 F821). Post-fix: 87 errors remaining (674 fixed). The shrinkage IS the AC; full clean is named as ratification-candidate scope, not C4 scope.

- **AC.LDC.2 — Touched-component test suites green post-auto-fix.** No regression in plugins/dev-sdlc/pr-safety + plugins/dev-sdlc/tools/loam-amend + plugins/dev-sdlc/tools/loam-mode + odd-extractor offline subset. Verification: 372+74+ targeted tests pass.

- **AC.LDC.F3 — odd-extractor `analyze._SKIP_DIR_NAMES` extends with `framework`.** Mirrors v0.2.1 corrective F2 in `workspace-bootstrap/.../language_detection.py`. Per FIDRAFT v0.2.5 yellow finding F3. Test: `test_AC_LDC_F3_framework_skip.py` — 3 tests (skip set membership, skip prevents file leak, extra-skip-dir-names still composes).

- **AC.LDC.F4 — v0.2.1 corrective F1 plan-doc carries supersession addendum.** Top-of-file callout block names v0.2.3 Cycle 3 §6.2 as the retire point for `acs:` + `unhandled_paths:` fields. Doc-only edit; no functional change. Per FIDRAFT v0.2.5 yellow finding F4. No paired test (doc-only).

- **AC.LDC.5 — KNOWN_CROSS_MODE_DEBT allowlist shrinks 1 → 0.** Lone remaining entry (`framework/memory-system/launchd/README.md` → `docs/archive/component-research/true-first-run/research.md`) became stale post-v0.3.0 C2 (graphiti rip-out deleted `framework/memory-system/`). Comment added explaining the shrink + post-v0.3.0 C2 cause. Test `test_AC_F3_always_loaded_no_dev_refs` passes with `KNOWN_CROSS_MODE_DEBT == set()`.

## §5 — Build dispatch brief (folded into this run)

Single-agent Sonnet dispatch per dispatcher 2026-05-08. Build sequence:

1. **Source-edit feat commit (BASELINE).** Apply ruff `--fix` to framework/ + plugins/ (674 auto-fixes). Edit `analyze.py` `_SKIP_DIR_NAMES` (F3). Add `test_AC_LDC_F3_framework_skip.py` (F3 tests). Edit `test_partition_references.py` `KNOWN_CROSS_MODE_DEBT` (shrink to empty). Edit `v0-2-1-corrective-f1-odd-extractor-contract-draft-fields.md` (F4 addendum). Run touched-component tests + targeted odd-extractor tests + partition-references test; assert green. Single commit subject: `chore(v0.3.0): Cycle 4 — lint auto-fix + F3 framework-skip + F4 doc addendum + KNOWN_CROSS_MODE_DEBT shrink`.
2. **Manifest+apply commit.** `loam amend apply <this manifest>` produces a single merged commit per AC.DPS1.6 schema-v3.
3. **Seal commit.** `loam amend seal --plan-doc <abs path> <this manifest>` produces deterministic short-form seal commit per AC.DPS2 schema-v3 + a §14 backfill follow-up commit per AC.D-sa.7.

**No `git --amend`. No push. Single semantic commit per stage.**

## §7 — Out of scope

- mypy `--strict` exit 0 across framework/ + plugins/ (~40 errors in src/ subset alone; structural; halt-and-surface candidate per dispatch §10).
- Ruff residual 87 errors (`F841` / `E402` / `E741` / `E731` / `F811` / `F821`) — most are intentional (unused vars in test scaffolding); some real (forward-ref `F821` in first_run_scaffold; lambda-assignment `E731` in adapters); decompose at v0.3.x or carry to v0.4.x cleanup.
- Type-system migration / repo-wide `mypy.ini` authoring (each component currently relies on its own pyproject.toml; namespace-package collisions need a master config).
- Test-suite restructuring beyond F3 closure tests.
- New ruff / mypy rule additions beyond default profile.
- Lint-pass on `docs/` (doc-only edits stayed within fence: F4 addendum is targeted).
- Lint integration into dev-sdlc PR-safety pipeline — FIDRAFT future-minor item.
- Live-API tests requiring claude subprocess invocations.

## §8 — Halt triggers (in-flight)

Conditions that fire during cycle execution stop the build for surface-and-RF:

1. ruff auto-fix iteration breaks any touched-component test → halt-and-surface; do not silently update sealed-AC tests.
2. F3 `framework` skip causes the workspace-bootstrap-fixture rails-detection test (`test_AC_LD_SKIP_FRAMEWORK_3_bootstrapped_rails_primary_rails.py`) to fail or causes any rd-automation extraction surface to fail → halt-and-surface; revert and reframe.
3. KNOWN_CROSS_MODE_DEBT shrink causes `test_AC_F3_always_loaded_no_dev_refs` to fail with unexpected refs (i.e., other cross-mode debt surfaces post-shrink) → halt-and-surface for triage.
4. mypy clean attempt surfaces structural refactor needs → halt-and-surface (scope expansion beyond C4).
5. Push or `--amend` attempt → immediate halt; corrective NEW commit + RF surface.
6. Cycle scope expands beyond named threads → halt-and-surface.

## §10 — F2 Ruthless Feedback (gaps named this turn)

1. **Ruff residual 87 errors not all benign.** F821 (2) are real forward-reference bugs in `first_run_scaffold.py` (ref `mcp_json_writer` + `tracker_seed` modules without import); E731 (5) lambda-assignment is style preference, not bug; F811 (5) redefined-while-unused are likely real test-fixture redefinitions. Recommended ratification: triage the 87 in a v0.3.x corrective if they materially affect any subsequent cycle's signal-to-noise.

2. **mypy structurally non-clean across the tree.** Per-component pyproject.toml + `loam.<comp>` namespace pattern causes mypy duplicate-package errors when run repo-wide. Even with `--explicit-package-bases`, the tree needs a per-component mypy invocation strategy or a master `mypy.ini` excluding test packages. 40 type-errors observed across `framework/orchestrator` + `plugins/dev-sdlc/odd-extractor` + `pr-safety` src/ subsets alone. Surface as ratification candidate; do NOT block C4 on mypy clean. Per dispatch halt §10 — surface, don't expand.

3. **ruff didn't surface I001 (import-order) by default.** `--select=I` would surface 967 unsorted-import violations; `--select=E,F,W` would surface 552 line-too-long. C4 used the default profile (no `I` / no `E501`). Surface as a forward-ratification question: does v0.3.x want to add isort + line-length enforcement?

4. **Mass auto-fix touches 339 files.** While each individual change is small (unused-import removal), the blast radius is wide. Mitigation: 372 dev-sdlc tests + 74 targeted odd-extractor tests pass post-fix; live-API tests deferred. Risk: a removed import might be re-needed by a downstream component test that the touched-test set didn't exercise. Surface for C7 release-level smoke verification.

5. **F4 doc-only addendum doesn't carry a paired test.** No mechanism enforces the historical-record callout stays in place in the v0.2.1 corrective F1 plan-doc. Acceptable per ODD §2.5 (doc text doesn't map to code branch); future structural enforcement (v0.7.0) could add a fragment-presence assertion if drift becomes a pattern.

## §11 — Provenance trail

- Master plan: `docs/plans/v0-3-0-master-plan.md` §3 Cycle 4.
- Stub origin: same plan-doc inheritance ladder as Cycles 1/2/3.
- FIDRAFT entries: `docs/FUTURE_IDEAS_DRAFT.md` lines 60-ish (lint pass post-Eric ship), 143 (KNOWN_CROSS_MODE_DEBT allowlist drift), 158-162 (v0.2.5 yellow findings F3 + F4).
- Test surfaces: `plugins/dev-sdlc/odd-extractor/tests/test_AC_V025_1_1_off_limits_skip.py` (existing _SKIP_DIR_NAMES test pattern); `framework/workspace-bootstrap/tests/test_AC_LD_SKIP_FRAMEWORK_1_framework_dir_skipped.py` (mirror pattern for v0.2.1 corrective F2).

## §14 — Method-decision record (backfilled at dispatch + seal)

| Decision | Choice | Rationale |
|---|---|---|
| ruff config scope | default profile (no `I`/`E501`) | Per dispatch "ruff (style + import-order + unused-vars + complexity)" — but adding `I` adds 967 violations + adds `E501` adds 552 violations. C4 stays inside the default profile to keep the cycle within its 60-120 min band; surface I001 + E501 as ratification candidate. |
| mypy invocation | per-component src-only sample, NOT repo-wide | Repo-wide mypy hits namespace-package collisions; needs a master config. C4 documents the structural blocker without expanding scope to author the config. |
| Auto-fix scope | apply ruff `--fix` to all 674 auto-fixable | Each individual change is small (unused-import removal); collective blast radius mitigated by 372+74+ touched-component tests passing. |
| Residual 87 errors | surface as ratification candidates, don't fix | Many are intentional (test fixtures); some need design ruling (forward refs). C4 stops at the `--fix` boundary per scope discipline. |
| KNOWN_CROSS_MODE_DEBT shrink mechanism | empty set + comment explaining post-v0.3.0 C2 cause | Test logic preserved (shrink-not-grow discipline still enforced); allowlist authoring becomes explicit-only via NEW commit. |
| F3 fix mirror choice | mirror v0.2.1 corrective F2 wording in code comment | Consistent with corpus precedent; signposts the cross-codepath relationship. |
| F4 addendum location | top-of-file callout block | High-visibility for stranger reading the plan-doc; preserves §1 + §2 framing as historical record. |
| Test scope at AC.LDC.2 | targeted touched-component + offline subset | Live-API tests are hours-long + flaky; out-of-scope for this cycle's verification per dispatch. |

### Commit SHAs

To be filled at cycle-seal + post-seal backfill:

- Plan-doc commit: (pending)
- Source-edit feat commit (BASELINE): (pending)
- Manifest+apply commit: (pending)
- Seal commit: (pending)
- §14 backfill commit: (pending)
