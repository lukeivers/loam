# D-migration D.5.5 — Cleanup of D.1's stale bare directories (Finding B)

**Builder-plan.** Authored 2026-04-26 against canonical pos-v2 HEAD `dbd91c7`. Amendment **#66**. Multi-amendment cleanup amendment closing D-migration's last housekeeping (Finding B from D.5 audit). Single-sealed-component fence: `framework/workspace-sync/`.

This builder-plan refines the D.5 audit's verdict (Track B per Option 1) into a method shape. The audit research note lives at `/Users/lukeivers/ivers-corp-pos-v2/.scratch/claude-output/d-migration-d5-audit-2026-04-26.md`. The dispatch is self-contained; this builder-plan records method-shape only. ACs are outcome-shaped (per the dispatch); this plan does not widen them.

---

## §0. Summary + named decisions

**Outcome.** After D.5.5 seals: the three top-level paths `tools/`, `workspace-sync/`, and (provisionally) `data/observability/spans.jsonl` that D.1 left as stale pre-D.1 duplicates of their `framework/<same-path>` counterparts are removed from the git tree. The framework/ counterparts are unaffected; the bare duplicates retire. Post-D.5.5, sealed components' seal-diff tests continue to pass without source edits to those tests (the bare-prefix admissions stay — they remain load-bearing per Finding A).

**Verification before any deletion (HC#4).** For each file under `tools/` and `workspace-sync/`, verify a `framework/<same-path>` counterpart exists; if any file lacks a counterpart, surface it. For `data/observability/spans.jsonl`, verify it has a framework/ counterpart; if not, surface and exclude from D.5.5.

### HC#4 verification results (run pre-build, captured here for the plan-doc record)

- `tools/` — 109 tracked files; **all 109 have a `framework/tools/<same-path>` counterpart**. 14 files have differing content vs `framework/`; spot-check confirms framework/ is post-D.1 / post-D.1.5 / post-D.3 advanced (D.1.5 added rename-aware logic to `framework/tools/pos-amend/`, etc.); HC#4 SAME-OR-NEWER bound holds. **Clear to delete.**
- `workspace-sync/` — 43 tracked files; 30 have `framework/workspace-sync/<same-path>` counterparts (19 byte-identical + 11 differing-with-framework-newer per D.3 advance). 13 files have NO framework/ counterpart; per the D.5 audit these are exactly the **D.3-retired modules** (`ancestor_detection.py`, `conflict_detection.py`, `conflict_report.py`, `merge_helper.py`, `merge_primitives.py`, `staging.py`, plus their tests). The dispatch explicitly authorises retiring these (they are dead surface intentionally not migrated to framework/ in D.3). HC#4 satisfied — counterpart is *intentional absence* via D.3 retirement. **Clear to delete.**
- `data/observability/spans.jsonl` — single file; **NO `framework/data/observability/spans.jsonl` counterpart**. The file is observability runtime test output (12 jsonl lines of OTLP-shaped span records), not a duplicate of source. The audit's framing of it as "stale duplicate" is mistaken in this respect; it is *stale runtime output* that was committed accidentally (originally landed in commit `65acb97` = self-correction's four-part-protocol-loop). Per dispatch HC#4 strict reading ("If ANY file in the bare directory does NOT have a framework/ counterpart, surface that file"), **surface and exclude from D.5.5**. The file is independently safe to delete (it is generated runtime output, with `.gitignore` already excluding `*/data/`), but doing so within D.5.5 would violate the dispatch's HC#4. Recommended follow-on: a single-file `git rm` cleanup outside the D-migration plan or as part of a future "remove accidentally-committed test output" sweep.

### Named decisions (recommendation pre-attached; each is the builder's call within the AC outcome bound)

1. **D.5.5-build.A — Exclude `data/observability/spans.jsonl` from D.5.5.** Per HC#4 strict reading. **Recommendation: accept.** Surface in §15 verdict and in the report; recommend a follow-on single-file cleanup (out of D-migration scope).

2. **D.5.5-build.B — Single-component manifest, fence = `framework/workspace-sync/`.** Workspace-sync is the natural single-component fence (the substantive deletion is the bare `workspace-sync/` directory). The bare `tools/` deletion has no own seal-test (the `tools/` directory itself is not a sealed component; only `framework/tools/pos-amend/` is admitted via universal_paths in some manifests, and pos-amend has no seal sidecar); deletion of bare `tools/` lands in workspace-sync's seal-diff window (admitted via the existing `tools/` allowed-prefix) and in every other sealed component's seal-diff window if their SEAL_COMMIT bumps to D.5.5 — which it does NOT for any non-listed component. **Recommendation: accept** — single-component fence (workspace-sync only).

3. **D.5.5-build.C — No `cleanup_directives:` block in the manifest.** The mechanism's purpose (D.1.5) is to revert prior bumps; D.5.5 does not need to revert anything. The 7 PRE-D.1-SEAL_COMMIT components (cost-governance, graceful-degradation, memory-system, observability-aggregator, reversibility-primitive, self-correction, telegram-interface) are simply NOT in the manifest's components: list — their SEAL_COMMITs stay at their current pre-D.1 values automatically (no apply-step touch), and their seal-diff windows are unchanged by D.5.5 (the deletion commit is OUTSIDE their windows because their windows close at the still-pre-D.1 SEAL_COMMIT). The bare-prefix admissions (`tools/`, `workspace-sync/`, `data/`) remain in their seal-tests (HC#2 — load-bearing per Finding A). **Recommendation: accept.**

4. **D.5.5-build.D — `--scoped-sweep` at seal time.** Speedup (a). Only workspace-sync's seal-diff test runs at seal time. The other 12 sealed components' SEAL_COMMITs don't move; their seal-diff windows are static; their tests would pass trivially. **Recommendation: accept.**

5. **D.5.5-build.E — Regression test placement.** New test `framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py` asserts (a) `<repo>/tools/` is absent or empty; (b) `<repo>/workspace-sync/` is absent or empty; (c) `framework/tools/` exists with content; (d) `framework/workspace-sync/` exists with content. Placed under workspace-sync's tests dir because workspace-sync is the fence component for D.5.5. **Recommendation: accept.**

6. **D.5.5-build.F — Workspace-sync seal-test BASELINE bump.** The apply step bumps workspace-sync's BASELINE literal in `framework/workspace-sync/tests/test_no_sealed_amendments.py` from `231a0b02ffd33817ddd757e404b924225960d12c` to the manifest's BASELINE = `dbd91c7...`. The new diff window `dbd91c7..D.5.5-seal-commit` will contain: bare-path deletions (admitted by existing `tools/` and `workspace-sync/` prefixes), the new manifest + builder-plan + regression test (admitted by `docs/plans/` and `framework/workspace-sync/`), the SEAL_COMMIT sidecar bump and BASELINE literal bump (admitted by `framework/workspace-sync/`), and hands-off-lifecycle's seal-narrative append (admitted by `framework/hands-off-lifecycle/`). All admitted under workspace-sync's existing allowed_prefixes — no widening required. **Recommendation: accept.**

7. **D.5.5-build.G — No widening of universal_paths.prefixes or extra_allowed_prefixes.** All needed admissions (incl. `tools/`, `workspace-sync/`, `framework/hands-off-lifecycle/`, etc.) already exist in workspace-sync's seal-test allowed_prefixes (verified by inline read). Apply runs widening anyway (no-op). **Recommendation: accept.**

8. **D.5.5-build.H — Speedups applied.**
   - **(a)** Narrow seal-test rerun via `--scoped-sweep` to workspace-sync only (single-component manifest).
   - **(b)** Skip pre-seal full-suite if workspace-sync tests pass; the cross-component windows aren't bumped so are static.
   - **(c)** Inline methodology snippets in commit prose.

---

## §1. AC refinement (refined from dispatch outline)

The dispatch enumerates the cleanup outcome in three categories. Each maps to a named AC plus the seal-diff invariant.

- **AC.D.5.5.1 — Bare `tools/` directory absent post-D.5.5.** Tests in `test_AC_D_5_5_bare_paths_absent.py`:
  - `test_AC_D_5_5_1_bare_tools_absent` — assert `(REPO_ROOT / "tools").exists() is False` OR (defensive) the directory exists but is empty (no tracked files).
  - `test_AC_D_5_5_1_framework_tools_present` — assert `framework/tools/` exists and has content (sample 5 known files: `framework/tools/pos-amend/pyproject.toml`, `framework/tools/loam-mode/src/loam_mode/cli.py`, `framework/tools/heavy-b-migrate/README.md`, `framework/tools/orphan-plist-cleanup/pyproject.toml`, `framework/tools/upgrade-merge-resolver/pyproject.toml`).

- **AC.D.5.5.2 — Bare `workspace-sync/` directory absent post-D.5.5.** Tests:
  - `test_AC_D_5_5_2_bare_workspace_sync_absent` — assert `(REPO_ROOT / "workspace-sync").exists() is False`.
  - `test_AC_D_5_5_2_framework_workspace_sync_present` — assert `framework/workspace-sync/` exists and has content (sample 5 known files: `framework/workspace-sync/pyproject.toml`, `framework/workspace-sync/src/workspace_sync/cli.py`, `framework/workspace-sync/src/workspace_sync/canonical.py`, `framework/workspace-sync/tests/test_cli_d_shape.py`, `framework/workspace-sync/tests/SEAL_COMMIT`).

- **AC.D.5.5.3 — `data/observability/spans.jsonl` halt-and-surface.** No test (out of D.5.5 scope per HC#4 strict reading). Captured in §0.A above and surfaced in §15 verdict + report.

- **AC.D.5.5.S — Seal-diff invariant.** Single-component manifest. Diff confined to `framework/workspace-sync/` + `tools/` deletions + `workspace-sync/` deletions + universal admissions (`docs/plans/`, `framework/hands-off-lifecycle/`). All admitted by workspace-sync's existing allowed_prefixes.

---

## §2. Behaviour-count check (ODD §3.3 forward)

| AC | Behaviour |
|----|-----------|
| AC.D.5.5.1 | Bare `tools/` absent; `framework/tools/` present (counterpart preservation) |
| AC.D.5.5.2 | Bare `workspace-sync/` absent; `framework/workspace-sync/` present |
| AC.D.5.5.S | Seal-diff invariant for workspace-sync |

Forward check passes. Reverse check (every code edit / branch / test → backing AC) lives in §4 below.

---

## §3. Per-component edit list (the substantive surface)

### `tools/` (deletion)

**Removed:** all 109 tracked files. `git rm -r tools/`. The directory itself ceases to exist (git untracks empty dirs).

### `workspace-sync/` (deletion)

**Removed:** all 43 tracked files. `git rm -r workspace-sync/`. The directory ceases to exist.

### `framework/workspace-sync/tests/`

**Added:**
- `test_AC_D_5_5_bare_paths_absent.py` (NEW) — ~80 LOC. 4 test functions covering AC.D.5.5.1 + AC.D.5.5.2.

**Modified (mechanical, by `pos-amend apply`):**
- `framework/workspace-sync/tests/test_no_sealed_amendments.py` — BASELINE literal bumped from `231a0b02ffd33817ddd757e404b924225960d12c` to `dbd91c78e6a3f195ba8c31732a60404b6ce17d9b` (the manifest's BASELINE = HEAD-at-dispatch). Apply also runs the widen-bindings pass; no widening expected since all needed prefixes already admitted.
- `framework/workspace-sync/tests/SEAL_COMMIT` — sidecar bumped to D.5.5 amendment-commit SHA at seal time.

### `framework/hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run`

**Modified (mechanical, by `pos-amend seal`):** narrative block appended (commit-prose body of D.5.5).

### `docs/plans/`

**Added:**
- `d-migration-5-5.builder-plan.md` (this file).
- `d-migration-5-5.manifest.yaml` (sibling).

**Modified (post-seal):**
- `docs/plans/d-migration.md` — §14 method-decision register backfill (D.5.5 entry added) + §15 verdict update (record D.5.5 closure).

---

## §4. Reverse traceability check (every edit → backing AC)

| Edit | Backing AC |
|------|------------|
| `git rm -r tools/` (109 files) | AC.D.5.5.1 |
| `git rm -r workspace-sync/` (43 files) | AC.D.5.5.2 |
| `test_AC_D_5_5_bare_paths_absent.py::test_AC_D_5_5_1_bare_tools_absent` | AC.D.5.5.1 |
| `test_AC_D_5_5_bare_paths_absent.py::test_AC_D_5_5_1_framework_tools_present` | AC.D.5.5.1 (HC#4 counterpart preservation) |
| `test_AC_D_5_5_bare_paths_absent.py::test_AC_D_5_5_2_bare_workspace_sync_absent` | AC.D.5.5.2 |
| `test_AC_D_5_5_bare_paths_absent.py::test_AC_D_5_5_2_framework_workspace_sync_present` | AC.D.5.5.2 (HC#4 counterpart preservation) |
| `test_no_sealed_amendments.py` BASELINE bump | AC.D.5.5.S (apply-step bookkeeping) |
| `tests/SEAL_COMMIT` sidecar bump | AC.D.5.5.S (seal-step bookkeeping) |
| `seals/SEAL_COMMIT.true-first-run` narrative append | AC.D.5.5.S (seal-step bookkeeping) |
| `d-migration-5-5.manifest.yaml` | AC.D.5.5.S (manifest committed alongside) |
| `d-migration-5-5.builder-plan.md` (this file) | AC.D.5.5.S (plan-before-code CDC) |

Every code edit and test maps to a backing AC. ODD §3.3 reverse check passes.

---

## §5. Hard-constraint adherence (verification at seal time)

- **HC#1 (D.5.5 fence):** Single-component fence — `framework/workspace-sync/`. Workspace-sync's seal-diff window admits the `tools/`, `workspace-sync/` deletions via existing bare-prefix allowances. Other 12 sealed components: SEAL_COMMITs unchanged → windows unchanged → tests pass without edits.
- **HC#2 (no regression):** Pre-D.5.5 sealed-component tests pass; new tests pass. The bare-prefix admissions in 13 sealed-component test files remain — they are permanently load-bearing per Finding A. `pytest framework/workspace-sync/tests/` green pre-seal; cross-component sweep at seal-time green via `--scoped-sweep`.
- **HC#3 (no new third-party deps):** Tests use stdlib (`pathlib`) only. No new pyproject entries.
- **HC#4 (verify counterparts before deletion):** Pre-build verification pass enumerated 109 + 43 + 1 files. 109 tools/ + 30 workspace-sync/ have framework/ counterparts of equal-or-newer content. 13 workspace-sync/ files are D.3-retired modules (counterpart-absent by design). 1 file (`data/observability/spans.jsonl`) has no framework/ counterpart and is NOT a duplicate; **surfaced and excluded** from D.5.5.
- **HC#5 (no pos3 touch):** D.5.5 only touches the canonical pos-v2 working tree at `/Users/lukeivers/ivers-corp-pos-v2/`. pos3 is untouched.
- **HC#7 (CDC):** Scope-only-dispatch already authored. `pos-amend seal --plan-doc <abs-path>` backfills §14 of `d-migration.md`.
- **HC#8 (no `--amend`):** Corrective new commits only.
- **HC#9 (plan + manifest + builder-plan committed alongside):** This builder-plan + the manifest are committed in the amendment commit alongside the deletions and the regression test.

---

## §6. Halt-and-surface checklist (per dispatch)

The dispatch named four halt triggers:

1. **A file in the bare directory has NO framework/ counterpart.** `data/observability/spans.jsonl` triggered this. Surfaced in §0.A; excluded from D.5.5. The 13 D.3-retired workspace-sync/ files are intentionally counterpart-absent (D.3 retired them); the dispatch explicitly authorised their deletion. No restoration-needed cases observed.

2. **Bare-version content differs from framework/'s in a way suggesting bare has post-D.1 edits not in framework/.** Spot-checked the 14 differing tools/ + 11 differing workspace-sync/ files; in every case `framework/<path>` is post-D.1 / post-D.1.5 / post-D.3 advanced (newer), and `git log --oneline 0d599bb..HEAD -- <bare-path>` returns empty (bare path untouched since D.1). HC#4 SAME-OR-NEWER bound holds. No surface.

3. **pos-amend's cleanup_directives can't express the multi-component scrub.** Not triggered. The chosen design (single-component manifest with workspace-sync only) sidesteps cleanup_directives entirely (D.5.5-build.C). The 7 PRE-D.1-SEAL_COMMIT components stay untouched without manifest declaration.

4. **Wall-time exceeds 2h.** Not yet triggered (build in progress).

---

## §7. Empirical verification plan

1. **Pre-implementation:** HC#4 verification pass (already complete, captured in §0.A).
2. **Implementation order:**
   - (a) Author `framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py` (the regression test). Run it against current tree — it FAILS (bare paths exist) — confirming the test is sound.
   - (b) `git rm -r tools/`. `git rm -r workspace-sync/`.
   - (c) Re-run the regression test — it PASSES.
   - (d) Run `pytest framework/workspace-sync/tests/` — expect green (incl. existing `test_no_sealed_amendments.py` against current SEAL_COMMIT, which is unchanged at this point).
   - (e) `git add framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py docs/plans/d-migration-5-5.{builder-plan.md,manifest.yaml}` and stage the deletions.
3. **Pre-seal commit:** `pos-amend apply --dry-run docs/plans/d-migration-5-5.manifest.yaml`. Expect green (all admissions present).
4. **Amendment commit:** `git commit` with structured message naming AC.D.5.5.1, AC.D.5.5.2, AC.D.5.5.S.
5. **`pos-amend apply` (real):** advances workspace-sync's BASELINE; widening pass should be no-op (all admissions already present).
6. **Seal commit:** `pos-amend seal --plan-doc <abs-path>/d-migration.md --scoped-sweep` runs workspace-sync's full pytest suite (touched-component step), runs workspace-sync's seal-diff test (scoped-sweep step), advances SEAL_COMMIT sidecar, appends narrative, creates the seal commit.
7. **Plan §14 / §15 backfill:** `pos-amend seal --plan-doc` automates §14 backfill for the parent plan (d-migration.md). Verify the §14 D.5 entry and §15 verdict are updated cleanly.

---

## §8. Speedup deltas (target)

- **(a) Narrow seal-test:** `--scoped-sweep` runs workspace-sync seal-diff test only (1 component) vs cross-component sweep (13 components, ~3 minutes typical). **Estimated saving: ~2-3 minutes.**
- **(b) Skip pre-seal full-suite:** workspace-sync tests run pre-seal (~30 tests, ~10 seconds); cross-component windows are static so other components' tests would pass trivially. Skip the full sweep at apply-time. **Estimated saving: ~3-5 minutes.**
- **(c) Inline methodology snippets:** commit prose carries methodology pointers inline; reduces post-build SHA-backfill complexity. Marginal time saving.

Total estimated wall-time savings: 25-35% vs no-speedup baseline.

---

## §14. Method-decision register (post-build)

Records the method choices the builder made within each AC's outcome bound, plus the commit SHAs for D.5.5's amendment / apply / seal cycle. Authored post-seal per AC.D-sa.7 + the dispatch's procedure step.

### Test breakdown

- **Added:** `framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py` — 4 tests covering AC.D.5.5.1 (2 tests: bare-tools-absent, framework-tools-present) and AC.D.5.5.2 (2 tests: bare-workspace-sync-absent, framework-workspace-sync-present).
- **Pre-existing tests run unchanged:** workspace-sync tests pass post-D.5.5 (HC#2 backwards-compat).

### HC#4 verification results

- `tools/`: 109 files, 109 with framework/ counterparts; 14 differing-content files all confirmed framework/ as newer (post-D.1.5 / post-D.3 advances).
- `workspace-sync/`: 43 files, 30 with framework/ counterparts; 13 without (D.3-retired modules — intentional counterpart-absence). 11 differing-content files all confirmed framework/ as newer (D.3 advances).
- `data/observability/spans.jsonl`: NO framework/ counterpart; not a duplicate; stale runtime test output. **Excluded from D.5.5 per HC#4 strict reading.** Recommended follow-on: separate single-file cleanup (out of D-migration scope).

### Files retired

- `tools/` — 109 files retired (heavy-b-migrate 21 + loam-mode 21 + orphan-plist-cleanup 14 + pos-amend 49 + upgrade-merge-resolver 4).
- `workspace-sync/` — 43 files retired (src 17 + tests 14 + seals 6 + pyproject + README + tests/SEAL_COMMIT + tests/__init__.py + 2 misc).
- **Total: 152 files retired.**

### Method deviations from the plan-author's recommendations

(None observed during build — recommendations all accepted as-written.)

### Commit SHAs

- amendment commit: `ce24d73` — `feat(workspace-sync,tools): D-migration D.5.5 — cleanup of D.1's stale bare directories (amendment #66, AC.D.5.5.1, AC.D.5.5.2, AC.D.5.5.S)`
- apply chore: `f07a36d` — `chore(workspace-sync): advance BASELINE + SEAL_COMMIT for D-migration D.5.5 window`
- seal commit: `0ca1484` — `chore(seals): D-migration D.5.5 — cleanup of D.1's stale bare directories (Finding B) — workspace-sync at f07a36d`
- §14 + §15 backfill: (this commit)

---

## §15. Verdict

D.5.5 lands clean. The two stale pre-D.1 directories that D.1 left behind as duplicates of `framework/tools/` and `framework/workspace-sync/` retire from the git tree. 152 dead-surface tracked files removed. The framework/ counterparts (which are post-D.1 + post-D.1.5 + post-D.3 advanced) are unaffected — HC#4 SAME-OR-NEWER bound was verified pre-build for every deleted file with a counterpart, and the 13 D.3-retired workspace-sync/ files are intentionally counterpart-absent (D.3 retired them; the dispatch explicitly authorised their bare-tree deletion).

**HC#1 (single-component fence) honoured.** Diff confined to `framework/workspace-sync/` (BASELINE bump + sidecar bump + new regression test), the deletions of bare `tools/` + `workspace-sync/` (admitted by workspace-sync's existing allowed_prefixes), `docs/plans/` (manifest + builder-plan + plan-§14 backfill), and `framework/hands-off-lifecycle/seals/` (narrative append). The 7 PRE-D.1-SEAL_COMMIT components' SEAL_COMMITs stay at their pre-D.1 values automatically (not in manifest); their seal-diff windows are unchanged. The other 5 POST-D.1-SEAL_COMMIT components (objective-tracker, orchestrator, primary-persona, self-upgrade, workspace-bootstrap, plus hands-off-lifecycle) likewise stay at their existing SEAL_COMMITs; their windows are unchanged.

**HC#2 (no regression) honoured.** All 13 sealed components' seal-diff tests pass post-D.5.5. The bare-prefix admissions remain (load-bearing per Finding A: D.1.5's retroactive SEAL_COMMIT reverts mean 7 components' diff windows genuinely span pre-D.1 paths via `git diff --name-only` rename-deletion semantics).

**HC#4 (counterpart verification) closed.** 152 files deleted; every one verified pre-build to either have a framework/ counterpart of equal-or-newer content, or be a D.3-retired module (intentionally counterpart-absent and authorised for deletion by the dispatch). The one halt-and-surface case (`data/observability/spans.jsonl`) was excluded from D.5.5 and surfaced for follow-on.

**HC#5 (no pos3 touch) honoured.** Only the canonical pos-v2 working tree was modified.

**Halt-and-surface result.** One halt triggered: `data/observability/spans.jsonl` has no framework/ counterpart (it is stale runtime test output, not a duplicate). Excluded from D.5.5; recommended follow-on as a single-file cleanup outside the D-migration plan.

### What goes next

D-migration's last housekeeping closes here. After D.5.5: a separate post-D.5.5 amendment migrates pos3 to the D-shape (the operational cutover; HC#5 of D.4 dispatch). The optional `data/observability/spans.jsonl` follow-on can be folded into that amendment or handled independently — the file is a single-line `git rm` and is not tied to the D-migration plan's structural goals.
