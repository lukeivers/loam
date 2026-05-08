# D-migration D.1.5 — pos-amend rename-aware seal — builder plan

Builder-plan companion to `docs/plans/d-migration-1-5.md`
(plan-author's locked-decisions plan). Authored before any source
edit per `feedback_plan_before_code`.

**Status:** authored 2026-04-26. Working directory:
`/Users/lukeivers/ivers-corp-pos-v2/`.

---

## 1. Builder method-shape decisions (within locked outcomes)

The plan-author locked outcome bounds in `d-migration-1-5.md` §11
(D-Q.1 through D-Q.5). This builder-plan declares the method-shape
choices the builder will take inside each AC's locked outcome.

### M-1 — Rename-detection helper module + signature

**Method.** New module `framework/tools/pos-amend/src/pos_amend/rename_detection.py`.
Public surface:

```python
def is_rename_only(
    repo_root: Path,
    *,
    baseline: str,
    head: str,
    old_path: str,
    new_path: str,
    bookkeeping_leafnames: tuple[str, ...] = (
        "SEAL_COMMIT",
        "test_no_sealed_amendments.py",
        "test_cross_cutting.py",
    ),
) -> bool:
    """Return True iff every diff entry in the BASELINE..HEAD window for
    the union of *old_path* + *new_path* is either an R100 rename, or an
    A/D pair whose leaf name is in *bookkeeping_leafnames*."""
```

**Why a new module not inline in apply.py.** Single-responsibility +
unit-testable in isolation + matches the existing pos_amend layout
(`baseline.py`, `sidecar.py`, `seal_diff.py` are siblings). Cost: 1
new file. Benefit: clean test surface for AC.D.1.5.1 fixtures.

**Implementation.** Single shellout to
`git diff --find-renames=99% --name-status <baseline>..<head> -- <old> <new>`,
parse the `R<sim>\t<old>\t<new>` / `A\t<path>` / `D\t<path>` /
`M\t<path>` lines. Algorithm:

1. If diff output contains any `M` entry → False (substantive
   modification).
2. If diff contains any `R<sim>` where `sim < 100` → False (content
   edit during rename).
3. For all `A` and `D` entries: check leaf name. If every A/D's leaf
   is in `bookkeeping_leafnames`, treat as bookkeeping. Otherwise →
   False.
4. Each `A` entry should have a paired `D` entry at the equivalent
   `old_path` analog (or vice versa). If not, → False.
5. If everything is `R100` + bookkeeping A/D pairs → True.

**Threshold rationale.** Plan-doc D-Q.1 cited 99% (`--find-renames=99%`)
to catch trivial edits. But strict §1's wording is "every file
`R100`". HC#4 ("false-positive worse than false-negative") favours the
strict reading: R100-only counts as rename, R099 → substantive.
Builder uses **R100-strict** for the verdict (R099 = substantive). The
`--find-renames=99%` flag still controls *git's* matching threshold so
near-renames get detected as R099 (allowing us to classify them as
substantive rather than falsely classifying them as A/D pairs which
the bookkeeping whitelist would erroneously approve).

### M-2 — Apply-side wiring

**Method.** In `framework/tools/pos-amend/src/pos_amend/commands/apply.py`,
wrap the `set_baseline()` + `write_sidecar()` calls in a per-component
guarded branch:

```python
# Before the existing set_baseline() / write_sidecar() block:
old_path = f"{comp.name}/"
new_path = f"framework/{comp.name}/"
head_sha = _git_head(repo_root)  # new helper; rev-parse HEAD
rename_only = is_rename_only(
    repo_root,
    baseline=manifest.baseline,
    head=head_sha,
    old_path=old_path,
    new_path=new_path,
)
if rename_only:
    print(
        f"  - {comp.name}: rename-only — "
        f"BASELINE preserved at {prior_baseline}; "
        f"SEAL_COMMIT preserved at {prior_seal_commit}; "
        f"allowed_prefixes widened."
    )
    # Skip set_baseline() + write_sidecar(). Widening still runs.
else:
    # Existing path — set_baseline + write_sidecar
    ...
```

The widening of `allowed_prefixes` / `allowed_files` runs
unconditionally (rename-only components still need new admissions for
downstream amendments).

### M-3 — Manifest cleanup-directives shape

**Method.** Optional v1-compatible manifest field
`cleanup_directives:`. Each directive declares: `comp_name`,
`pre_baseline`, `pre_seal_commit`, optional `seal_test_path`. Apply
processes the list and writes back the pre-D.1 BASELINE + SEAL_COMMIT
values. This block is OPTIONAL — pre-D.1.5 manifests omit it (default
empty tuple); the rename-only conditional bump path applies to D.1.5+
amendments without needing the cleanup block.

```yaml
cleanup_directives:
  - comp_name: cost-governance
    pre_baseline: dd11677
    pre_seal_commit: 06ea4ef17d7173fafe072c83dcb4ea390b211e9c
    seal_test_path: framework/cost-governance/tests/test_no_sealed_amendments.py
    sidecar_path: framework/cost-governance/tests/SEAL_COMMIT
```

`apply.run` after the existing component loop walks the cleanup
directives and writes back literal BASELINE + SEAL_COMMIT values.

**Schema bump?** No. This is a v1-compatible additive optional field.
Per amendment-#23 / #46 precedent (`frozen_baseline`,
`seal_description`).

### M-4 — `--dry-run` reporting

**Method.** `dry_run.analyse` already returns per-component
`ComponentReport`. Add `rename_only_verdict: bool | None` field.
`format_reports` prints `rename-only: True/False` per component.

### M-5 — Tests

**Method.** New tests in `framework/tools/pos-amend/tests/`:

- `test_rename_detection.py` — AC.D.1.5.1 (helper unit tests with
  fixture git repos).
- `test_AC_D_1_5_2_apply_rename_only_skip.py` — AC.D.1.5.2 (apply
  fixture + assertion that rename-only component skips bumps).
- `test_AC_D_1_5_3_dry_run_reports.py` — AC.D.1.5.3 (`--dry-run`
  output check).
- `test_AC_D_1_5_4_backwards_compat.py` — AC.D.1.5.4 (substantive
  fixture path-identical to pre-D.1.5 behaviour).
- `test_AC_D_1_5_5_cleanup_directives.py` — AC.D.1.5.5 (cleanup
  directive applies expected reverts).

Existing `test_seal.py` + `test_apply.py` + `test_dry_run.py` etc.
remain untouched (HC#1).

### M-6 — Hands-off the optional override (AC.D.1.5.6)

**Method.** Skip per D-Q.5 lock. No `rename_only:` override field.

### M-7 — Apply chore commit SHAPE (apply step's own commit)

The existing `pos-amend apply` is a non-committing in-tree mutation.
After D.1.5's apply edits the cleanup target paths, the operator
manually stages + commits the apply chore (matches D.1's pattern —
`97a4459`). For D.1.5 this is a single chore commit covering
pos-amend's own edits + the cleanup edits + universal-paths admissions.

---

## 2. Test breakdown (per AC)

Outcome-shape ACs from `d-migration-1-5.md` §4. Method-shape test
declarations:

| AC | Test file | Test cases |
|----|-----------|-----------|
| AC.D.1.5.1 | `tests/test_rename_detection.py` | `test_pure_rename_only_returns_true`, `test_modify_returns_false`, `test_partial_rename_R099_returns_false`, `test_unwhitelisted_AD_returns_false`, `test_bookkeeping_AD_pairs_admitted`, `test_unpaired_A_returns_false` |
| AC.D.1.5.2 | `tests/test_AC_D_1_5_2_apply_rename_only_skip.py` | `test_rename_only_skips_baseline_bump`, `test_rename_only_skips_sidecar_bump`, `test_rename_only_still_widens_prefixes`, `test_substantive_advances_baseline_and_sidecar` |
| AC.D.1.5.3 | `tests/test_AC_D_1_5_3_dry_run_reports.py` | `test_dry_run_reports_rename_only_verdict_true`, `test_dry_run_reports_rename_only_verdict_false` |
| AC.D.1.5.4 | `tests/test_AC_D_1_5_4_backwards_compat.py` | `test_existing_substantive_apply_unchanged`, `test_v1_manifest_without_cleanup_directives_parses` |
| AC.D.1.5.5 | `tests/test_AC_D_1_5_5_cleanup_directives.py` | `test_cleanup_directive_writes_pre_baseline_back`, `test_cleanup_directive_writes_pre_sidecar_back`, `test_cleanup_directive_idempotent` |
| AC.D.1.5.S | (existing seal-diff invariant via universal-paths admission) | (verified by D.1.5's own seal step) |

Speedup (a) per dispatch: pre-seal scoped to pos-amend's tests.
Speedup (b): skip pre-seal repo-wide pytest. Speedup (c): inline
methodology snippets in commit prose.

---

## 3. Component classification (rename-only verdict per D.1's window)

Builder-side authoritative classification using strict R100 + standard
bookkeeping whitelist (`SEAL_COMMIT`, `test_no_sealed_amendments.py`,
`test_cross_cutting.py`). Window: `57d735f..0d599bb`.

### Rename-only (8 components — SEAL_COMMIT + BASELINE will be reverted)

| Component | Pre-D.1 SEAL_COMMIT | Pre-D.1 BASELINE |
|-----------|---------------------|------------------|
| cost-governance | 06ea4ef17d7173fafe072c83dcb4ea390b211e9c | dd11677 |
| graceful-degradation | 5d92d710c04bf86073b5a43810a652a319f6ecaa | 9559ca7 |
| memory-system | 135398d372bb6398d2d78eec0e14406cc031d18e | 045f6db |
| observability-aggregator | 06ea4ef17d7173fafe072c83dcb4ea390b211e9c | dd11677 |
| reversibility-primitive | 06ea4ef17d7173fafe072c83dcb4ea390b211e9c | dd11677 |
| self-correction | 06ea4ef17d7173fafe072c83dcb4ea390b211e9c | dd11677 |
| self-upgrade | 4da967edcb3926e5cbb7dfb776fc54aa9609e253 | 90246dc4dafa953c1f5ad5d97819e24d97a761a7 |
| telegram-interface | 06ea4ef17d7173fafe072c83dcb4ea390b211e9c | dd11677 |

### Substantive (3 — bumps preserved per HC#4)

| Component | Reason |
|-----------|--------|
| objective-tracker | substantive A/D edits to `test_AC_SE_S_seal_diff_window.py`, `test_d4_scope_binding.py` (REPO_ROOT depth + brittle-test relaxation per c7fb441 history) |
| orchestrator | substantive A/D edit to `scripts/pos_session_start.py` (parents[3] + framework/ hooks dir path) |
| primary-persona | substantive A/D edits to 5 test files (REPO_ROOT depth + path additions) |

### Other amendments' substantive components (already correctly bumped)

| Component | Notes |
|-----------|-------|
| hands-off-lifecycle | R<100 + 88 A/D entries — substantive (first_run_helper.py, first-run.sh, .claude template) |
| workspace-bootstrap | R099 in first_run_scaffold.py (LAUNCHD_TEMPLATES) — substantive |
| workspace-sync | duplicated (not git-mv'd) — all-A entries, no D — substantive verdict (HC#4 false-negative tolerated) |

### No-op for cleanup (no pre-D.1 sidecar)

| Component | Notes |
|-----------|-------|
| safety-layer | unsealed pre-D.1 (no SEAL_COMMIT sidecar) |
| scope-of-work | unsealed pre-D.1 (no SEAL_COMMIT sidecar) |

---

## 4. Halt-and-surface watchpoints (builder)

Per dispatch + plan §10. Builder halts and surfaces if:

1. **Substantive component cascade unwind fails post-cleanup.**
   Specifically: per the empirical sweep (HC#5), if any of the 7
   representative AC.X.S tests fails post-D.1.5 — particularly tests
   inside the *substantive* set (primary-persona's
   `test_AC_M_S_seal_diff_window.py`, objective-tracker's
   `test_AC_SE_S_seal_diff_window.py`) — surface; the strict-R100 +
   whitelist algorithm classified them as substantive (correct under
   HC#4) but the cascade does not unwind for them. This is the
   anticipated halt-trigger surface.
2. **Rename-detection edge case in fixture.** If a fixture surfaces an
   unexpected verdict (e.g. R099 file should be rename per operator
   intent), surface to Luke for D-Q.5 override-build authorization.
3. **Cleanup directive writes fail.** If `set_baseline` reports
   `BaselineAmbiguous` or the seal-test file shape doesn't match the
   regex, surface immediately.
4. **pos-amend test regression.** Any pre-existing pos-amend test
   failing post-edit halts (HC#1 binding).

---

## 5. Pre-seal verification plan

Per dispatch speedup (a/b):

1. Run pos-amend's full test suite: `pytest framework/tools/pos-amend/tests/`.
2. Skip repo-wide pytest pre-seal.
3. Empirical AC.X.S sweep is **post-seal** verification (HC#5).

---

## 6. Implementation sequence

1. Author this builder-plan + manifest. **(complete)**
2. Implement `rename_detection.py` + tests for AC.D.1.5.1.
3. Wire `apply.py` for AC.D.1.5.2 + tests.
4. Wire `dry_run.py` for AC.D.1.5.3 + tests.
5. Add manifest `cleanup_directives:` parsing for AC.D.1.5.5 + tests.
6. Verify AC.D.1.5.4 backwards-compat: full pos-amend test suite green.
7. Stage feat commit. (`feat(framework/tools/pos-amend): D-migration D.1.5 — rename-aware seal + D.1 cleanup (amendment #62, AC.D.1.5.1–AC.D.1.5.S)`)
8. Run `pos-amend apply --dry-run --plan d-migration-1-5.manifest.yaml`; iterate.
9. Run `pos-amend apply --plan d-migration-1-5.manifest.yaml`; commit apply chore.
10. Run `pos-amend seal --plan-doc <abs> --scoped-sweep <manifest>`.
11. Empirical post-seal AC.X.S sweep (HC#5).
12. §14 backfill via the seal step's `--plan-doc` flow.

---

## 7. Backwards-compat verification (HC#1 / HC#2)

- AC.D.1.5.4 test fixture exercises an all-substantive component
  (no rename-only paths) — apply behaviour byte-identical to pre-D.1.5.
- Existing pos-amend test suite runs unchanged — `test_seal.py`,
  `test_apply.py`, `test_dry_run.py`, etc.
- v1 manifests without `cleanup_directives:` parse (default empty
  tuple) and apply unchanged.

---

## 8. Method-decision register (post-build; backfilled via seal)

To be populated by `pos-amend seal --plan-doc` mechanism + manual
backfill notes. Builder records method choices, test breakdown
deviations, commit SHAs, post-seal HC#5 verification results.
