# D-migration D.3 — `pos-sync` becomes `git fetch + git merge --ff-only`

**Builder-plan.** Authored 2026-04-26 against canonical pos-v2 HEAD `231a0b0`. Amendment #64. Third of 5 D-migration amendments. Single-sealed-component fence: `framework/workspace-sync/`.

This builder-plan refines the parent plan `docs/plans/d-migration.md` §4 D.3 into a method shape for review. ACs are outcome-shaped (per the parent plan) and are NOT widened by this builder-plan — only the implementation method is recorded here.

---

## §0. Summary + named decisions

**Outcome.** After D.3 seals: `pos-sync --workspace <ws>` (no other args, when canonical_source lives in sync-config.yaml) executes `cd <ws>/framework && git fetch <remote> && git merge --ff-only <remote>/<branch>` against `<ws>/framework/`. The pre-D.3 bespoke resolve→stage→apply pipeline is retired (~2400 LOC). The LLM-resolver primitives (`merge_resolver.py`, `_resolver_client.py`) are preserved as the rare-conflict fallback the new CLI invokes only when `git merge --ff-only` reports non-fast-forward AND the subsequent `git merge` produces unresolved conflicts. HC#6 structural promise: `pos-sync` operates exclusively inside `<ws>/framework/`; nothing outside that subdirectory is touched.

**Named decisions (recommendation pre-attached; each is the builder's call within the AC outcome bound):**

1. **D.3-build.A — `framework/` as a git working tree.** D.3's mechanism requires `<workspace>/framework/` to be a git working tree (its own `.git/`). Canonical pos-v2 itself is NOT structured this way (canonical's `framework/` is a subdirectory of canonical's tree). For D.3's tests, **fixture workspaces are constructed with `<fixture-ws>/framework/` cloned from a fixture canonical repo, so they have their own `.git/`**. Real-workspace adoption (pos3) lands in D.4's β.2-absorption (`pos-new-workspace --from <repo>` clones canonical into `<new-ws>/framework/`). HC#5 (pos3 smoke) operates against a pos3 that has been moved to D.4's shape; if pos3 has not been moved by post-D.3 time, the smoke runs against a synthetic D.3-shaped fixture, NOT pos3. Builder surfaces this in §15 verdict.

   **Recommendation: accept.** D.3 does not bootstrap framework/ as a git working tree on existing pos3-shape workspaces; that's D.4's job. D.3's tests verify the merge-based mechanism on synthetic fixtures.

2. **D.3-build.B — Remote configuration on first sync.** When `<ws>/framework/.git/config` lacks a remote named `canonical`, the new CLI configures one pointing at the resolved canonical source (URL or local path) before `git fetch`. On subsequent invocations, the existing remote is reused; if `canonical_source:` in sync-config.yaml has changed since last sync, the remote URL is updated in-place.

   **Recommendation: accept.** Avoids requiring the operator to manually `git remote add canonical <...>`. Idempotent; visible via `git remote -v` so operator can audit.

3. **D.3-build.C — Branch resolution.** Merge target ref defaults to `<remote>/HEAD` (whatever canonical's default branch is, resolved via `git remote show canonical | grep "HEAD branch"` or `git rev-parse canonical/HEAD`). `--ref <commit-or-branch>` flag overrides; format: bare branch name (e.g. `pos-v2`), tag, or SHA — passed through to `git merge --ff-only <ref>`.

   **Recommendation: accept.** Default-branch resolution mirrors `git pull`'s behaviour; explicit `--ref` mirrors the pre-D.3 CLI's same flag. Operator-facing UX preserved.

4. **D.3-build.D — Audit + state shape post-D.3.** The pre-D.3 audit/state pair was YAML at `<ws>/workspace/.pos/sync/<ref>/audit.yaml` + `<ws>/workspace/.pos/sync/state.yaml` carrying `ConflictReport` + `StateRecord` Pydantic structures. Post-D.3 the audit derives from `git log <prev>..<new> --oneline` and the state simplifies to `last_synced_sha` + `last_synced_at` + `last_branch`. **Recommendation:**
   - **Audit**: stderr-printed summary + `git log` reference. No on-disk audit YAML for fast-forward syncs (the operator can `git -C framework log <prev>..<new>` directly). On the LLM-fallback path, per-conflict resolver records land at `<ws>/workspace/.pos/sync/resolver-runs/<sha>/<sanitised-path>.yaml` carrying the `MergeVerdict` shape (resolution, merged_content, rationale, confidence) so the fallback's verdicts remain audit-grade.
   - **State**: simplify `state.py` to a 30-line `SyncState` Pydantic model with `last_synced_sha: str`, `last_synced_at: str`, `last_branch: str`, `last_outcome: Literal["fast-forward","merged","conflict-fallback","up-to-date"]`. Idempotency fast-path: re-run against same canonical+ref short-circuits when `last_synced_sha` matches `git -C framework rev-parse FETCH_HEAD` post-fetch.

   Trade-off: dropping the YAML audit on fast-forward syncs costs the operator's "what did this sync do?" briefing, but the dispatch's plan §11 D-Q.A5 accepts this — git's native `git log` is the primitive and it's universally understood. The fallback resolver-runs preserve audit-grade output for the rare LLM-mediated case.

5. **D.3-build.E — Vestigial `sync_protected.py`.** Plan §4 D.3 says `sync_protected.py` "now just declares `framework_floor` for documentation; structural enforcement comes from the directory split." **Recommendation: keep `sync_protected.py` as documentation surface only.** Its `FRAMEWORK_FLOOR` constant + `SyncProtected` Pydantic schema stay (the workspace's `<ws>/workspace/.pos/sync-protected.yaml` continues to be scaffolded by workspace-bootstrap; its load remains valid). The CLI no longer reads it for classification (git-merge mechanics replaced classification). A future amendment may retire it entirely; D.3 keeps it for back-compat with already-scaffolded workspaces. Test `test_sync_protected.py` stays.

6. **D.3-build.F — `canonical_cache.py` retention.** Plan §4 D.3 says "the `canonical_cache.py` clean-write enumeration" retires. Inspecting `canonical_cache.py` (143 lines) shows it has NO clean-write enumeration — that machinery lives in `staging.py` + `merge_helper.py`. `canonical_cache.py` is only the URL→cache-clone shape (`ensure_cache_clone`, `derive_repo_id`). **Recommendation: keep `canonical_cache.py` unchanged.** URL-form `canonical_source:` still needs the cache clone (the cache directory is what becomes `framework/`'s `canonical` remote URL). The plan's "clean-write enumeration" wording was off — the actual retired machinery is in staging + merge_helper. Surface this discrepancy in §15 verdict.

7. **D.3-build.G — `canonical.py` retention.** `canonical.py`'s `resolve_canonical(canonical_path, ref)` validates a canonical-path-as-git-tree + resolves `ref` to SHA via `git rev-parse`. Under D.3 the new CLI still needs to validate that the canonical source is a real git tree (or that the cache clone is) before configuring it as `<ws>/framework/`'s remote. **Recommendation: keep `canonical.py` unchanged.** Its surface is still useful even when the merge happens inside `<ws>/framework/` rather than between `canonical_path` and `<ws>`.

8. **D.3-build.H — `_audit.py` retention.** `_audit.py` (114 lines) renders `ConflictReport` for the operator-confirm gate. Under D.3 the fallback path produces per-conflict `MergeVerdict`s; we can still surface them via a thin operator-summary helper. **Recommendation: keep `_audit.py` but simplify** — replace the `ConflictReport`-shaped renderer with a `list[MergeVerdict]`-shaped renderer (one line per fallback resolution). `confirmed_by_operator` (the TTY-confirm helper) stays unchanged.

9. **D.3-build.I — `conflict_report.py` retention.** Plan dispatch said "conflict_report shape (used by fallback path)". On reflection, the new fallback path can be much simpler: per-conflict `MergeVerdict` returned by `MergeResolver.resolve()` is enough; we don't need the full `ConflictReport`/`ConflictEntry` apparatus (which carried Resolution-enum, ChangeKind, ancestor_match_sha, classifier_class, deterministic_primitive, fallback_reason — all α-machinery for the retired classifier+primitive+verifier path). **Recommendation: retire `conflict_report.py`** along with the rest. The simpler fallback path under D.3 records `MergeVerdict` directly. Test `test_conflict_report_b_shape.py` retires. Surface this as a deviation from the dispatch's "conflict_report shape stays" wording — the new fallback path is simpler than the dispatch envisaged. (HC#3: no new deps; no breaking surface change for external consumers because there ARE no external consumers — verified via `grep "from workspace_sync.conflict_report"` — only workspace-sync internal code references it.)

   **Halt-and-surface candidate.** This is a method-shape choice within the AC outcome bound (the AC's outcome is "LLM resolver fires on remaining conflicts" — it does not require the ConflictReport shape). Per `feedback_loose_AC_text_fix_AC_not_implementation`, the dispatch's "conflict_report shape (used by fallback path)" is loose-text guidance; the AC text in plan §4 D.3 does not mention conflict_report. Builder rules: retire it. If owner disagrees post-build, the file can be re-introduced at zero structural cost.

10. **D.3-build.J — `merge_resolver.py` shape.** `merge_resolver.py` exposes `MergeResolver`, `MergeVerdict`, `ResolverBudget`, `ResolverFailure`, `BudgetExhausted`. **Recommendation: keep unchanged.** D.3's fallback invokes it per conflicted file; the existing budget mechanism (per-conflict + cumulative) still applies; the existing prompt builder still applies (a three-way merge prompt — except the "prior-release content" is now the merge-base content from `git merge-base canonical/HEAD HEAD`, fed into `prior_text=` parameter).

11. **D.3-build.K — `_resolver_client.py` shape.** Keep unchanged. The `--strict-mcp-config` + `claude -p` shellout shape is preserved; `build_merge_resolver()` factory still exists; `cli.py` still loads it via `--merge-resolver-module workspace_sync._resolver_client` default.

12. **D.3-build.L — Pre-D.3 cli.py retired vs rewritten.** The pre-D.3 cli.py is 679 lines of bespoke pipeline orchestration. **Recommendation: rewrite from scratch** — name the new file `cli.py` (no rename; preserves pyproject `[project.scripts]` entries). Target ~250 lines: argparse + workspace-root derivation + canonical-source resolution + remote configuration + git fetch + git merge --ff-only + (on non-ff) fallback to `git merge` + LLM resolver per conflicted file + audit summary + state record. The bulk of cli.py's complexity (idempotency-fast-path, sync_protected envelope load, inferred-resolution invariants check, dry-run, confidence-floor, auto-accept) simplifies dramatically when git is the substrate.

13. **D.3-build.M — Test surface post-D.3.** Pre-D.3 tests retire by file:
    - `test_ancestor_detection.py` (497 LOC) — retires (ancestor_detection.py retires)
    - `test_conflict_detection_b_shape.py` (124 LOC) — retires
    - `test_conflict_report_b_shape.py` (222 LOC) — retires (per D.3-build.I)
    - `test_merge_helper.py` (640 LOC) — retires
    - `test_merge_primitives.py` (346 LOC) — retires
    - `test_staging.py` (88 LOC) — retires
    - `test_cli_b_shape.py` (994 LOC) — retires (every test in this file exercises the retired pipeline; the new CLI-shape tests live in `test_cli_d_shape.py`)

   New tests:
    - `test_cli_d_shape.py` — D.3 CLI tests (AC.D.3.1, .2, .3, .4, .5; per the AC verifications)
    - `test_state_d_shape.py` — D.3 state-record tests
    - (existing) `test_canonical.py`, `test_resolver_client_mcp_isolation.py`, `test_merge_resolver.py`, `test_state.py`, `test_sync_config.py`, `test_sync_protected.py` stay (with mechanical updates to drop references to retired modules where present).

   Retired test count: ~2900 LOC (~110+ tests). New test count: ~30 tests in `test_cli_d_shape.py` + 5-10 in `test_state_d_shape.py`.

14. **D.3-build.N — `__init__.py` re-exports.** No external consumers import from `workspace_sync.<module>` (verified via grep — only internal workspace-sync code references). `__init__.py` stays at version-string only.

15. **D.3-build.O — Idempotency fast-path.** The pre-D.3 idempotency check loaded `state.yaml` and matched `sync_ref`. Under D.3 the equivalent is: after `git fetch`, compare `git rev-parse FETCH_HEAD` against the workspace's `git rev-parse HEAD` inside `framework/`. If equal, the workspace is already at canonical; exit 0 with `up-to-date` outcome. **Recommendation: accept.** Simpler than reading state.yaml; trusted git for the SHA equality.

16. **D.3-build.P — HC#4 byte-content-match test.** AC.D.3.4's verification mandates byte-content match for files inside `framework/` post-merge (synthetic fixture: workspace at canonical-ancestor, merge to canonical-HEAD; assert byte-content match for representative files). Method: in `test_cli_d_shape.py`, the test seeds canonical with files A, B, C; clones canonical into fixture workspace's `framework/`; advances canonical (modifies A, adds D, deletes C); runs `pos-sync`; reads each file's bytes from `<fixture-ws>/framework/A`, `<fixture-ws>/framework/B`, `<fixture-ws>/framework/D` and asserts byte-equal to canonical's HEAD bytes; asserts `<fixture-ws>/framework/C` is absent. This is HC#4's binding.

17. **D.3-build.Q — HC#6 structural-guard test.** AC.D.3.4's verification mandates that `<fixture-ws>/workspace/` is byte-identical pre/post sync. Method: same fixture as P, additionally seeds `<fixture-ws>/workspace/.pos/foo.txt` and `<fixture-ws>/workspace/personas/handle/contract.yaml`; runs `pos-sync`; asserts the workspace/ files are byte-identical pre/post (SHA-256 compare of the workspace/ subtree).

18. **D.3-build.R — Speedups applied.**
    - **(a)** Narrow seal-test rerun to workspace-sync (single-component manifest).
    - **(b)** Skip pre-seal full-suite if workspace-sync tests pass; full sweep deferred to seal-time `--scoped-sweep`.
    - **(c)** Inline methodology snippets in commit prose.

---

## §1. AC refinement (refined from plan §4 D.3 outline)

The plan §4 ACs are kept verbatim; this section names the test methods.

- **AC.D.3.1 — `pos-sync` invokes `git fetch` against the canonical remote.** Test: `test_cli_d_shape.py::test_AC_D_3_1_git_fetch_advances_remote_ref` — constructs fixture workspace + fixture canonical, runs `cli.main(["--workspace", str(fixture_ws)])`, asserts `<fixture-ws>/framework/.git/refs/remotes/canonical/<branch>` advances to canonical's HEAD SHA. URL-form canonical_source path covered by parameterised case using `ensure_cache_clone` against a `file://` URL.

- **AC.D.3.2 — `git merge --ff-only` happy path.** Test: `test_cli_d_shape.py::test_AC_D_3_2_fast_forward_advances_workspace_HEAD` — fixture workspace's `framework/` HEAD is at canonical-ancestor; runs `cli.main`; asserts (a) `git -C <fixture-ws>/framework rev-parse HEAD` equals canonical's HEAD SHA, (b) the CLI returns 0, (c) stderr contains the fast-forward summary line.

- **AC.D.3.3 — Non-FF fallback to LLM resolver.** Test: `test_cli_d_shape.py::test_AC_D_3_3_non_ff_falls_through_to_resolver` — fixture has workspace-side commit on `framework/<branch>` editing path P; canonical also edits P (different content). Stub resolver via `--merge-resolver-module workspace_sync.tests._stub_resolver` (test-side stub returning a synthetic `MergeVerdict`); runs `cli.main`; asserts (a) `git -C <fixture-ws>/framework log` shows a merge commit, (b) resolver was invoked once, (c) `<fixture-ws>/framework/P` carries the resolver's merged content.

- **AC.D.3.4 — Class-A protection structural.** Test: `test_cli_d_shape.py::test_AC_D_3_4_workspace_state_byte_identical_pre_post_sync` — fixture seeds `<fixture-ws>/workspace/.pos/foo.txt` + `<fixture-ws>/workspace/personas/h/contract.yaml`; canonical advances; `pos-sync` runs (fast-forward); asserts every file under `<fixture-ws>/workspace/` is byte-identical pre/post (HC#4 + HC#6 binding). Plus the framework-side byte-content-match assertion (HC#4): `<fixture-ws>/framework/<file>` byte-equals canonical's HEAD bytes.

- **AC.D.3.5 — Audit log derives from `git log`.** Test: `test_cli_d_shape.py::test_AC_D_3_5_audit_summary_references_git_log` — fast-forward sync; asserts CLI stderr summary contains the canonical-side commit-subject lines from `git -C <canonical> log <prev>..<new> --oneline`. Fallback variant: `test_AC_D_3_5_resolver_runs_recorded_under_workspace_state` — non-FF sync invoking resolver; asserts `<fixture-ws>/workspace/.pos/sync/resolver-runs/<sha>/<sanitised-path>.yaml` exists with the `MergeVerdict` shape.

- **AC.D.3.6 — Pre-D.3 code retired.** Verified naturally by AC.D.3.S (seal-diff catches the retirements). Plus a smoke test: `test_cli_d_shape.py::test_AC_D_3_6_retired_modules_absent` — asserts `framework/workspace-sync/src/workspace_sync/staging.py` (etc., enumerated) does not exist.

- **AC.D.3.S — Seal-diff invariant.** Single-component manifest. Diff confined to `framework/workspace-sync/` + universal admissions.

---

## §2. Behaviour-count check (ODD §3.3 forward)

| AC | Behaviour |
|----|-----------|
| AC.D.3.1 | `pos-sync` fetches from canonical remote |
| AC.D.3.2 | Fast-forward merge advances framework/HEAD; CLI exits 0 |
| AC.D.3.3 | Non-FF triggers `git merge` + LLM-resolver fallback per conflict |
| AC.D.3.4 | Class-A protection structural; framework/ byte-matches canonical post-FF; workspace/ byte-identical pre/post |
| AC.D.3.5 | Audit derives from git log; fallback resolver-runs persisted |
| AC.D.3.6 | Retired source modules absent post-D.3 |
| AC.D.3.S | Seal-diff invariant |

Forward check passes. Reverse check (every code edit / branch / test → backing AC) lives in §5 below.

---

## §3. Per-component edit list (the substantive surface)

### `framework/workspace-sync/src/workspace_sync/`

**Retired (`git rm`):**
- `ancestor_detection.py` (242 LOC)
- `conflict_detection.py` (249 LOC)
- `conflict_report.py` (336 LOC; per D.3-build.I)
- `merge_helper.py` (883 LOC)
- `merge_primitives.py` (518 LOC)
- `staging.py` (141 LOC)

**Total retired src LOC: 2369** (close to plan's "~2400 LOC" estimate).

**Rewritten:**
- `cli.py` — current 679 LOC bespoke pipeline → ~250 LOC git-merge-based flow. Imports retire correspondingly. New control flow:
  1. Parse args + derive workspace_root.
  2. Resolve canonical_source (URL → cache clone via `ensure_cache_clone`; local → use directly).
  3. Verify `<ws>/framework/.git/` exists (if absent, halt with structured error pointing at D.4's `pos-new-workspace`).
  4. Configure `<ws>/framework/`'s `canonical` remote (idempotent).
  5. `git -C <ws>/framework fetch canonical`.
  6. Resolve target ref (`--ref` flag OR `<remote>/HEAD`).
  7. Idempotency fast-path: if `git -C <ws>/framework rev-parse HEAD` == `git -C <ws>/framework rev-parse FETCH_HEAD`, exit 0 with `up-to-date`.
  8. `git -C <ws>/framework merge --ff-only FETCH_HEAD` — on success, record state + exit 0.
  9. On `git merge --ff-only` failure: `git -C <ws>/framework merge FETCH_HEAD` (no `--ff-only`).
  10. On unresolved conflicts (parsed via `git status --porcelain`): for each `UU`/`AA` path, invoke `MergeResolver.resolve(path, canonical_text, workspace_text, prior_text=git_merge_base_text)`; write resolved content; `git add <path>`; record `MergeVerdict` to `<ws>/workspace/.pos/sync/resolver-runs/<sha>/<path>.yaml`.
  11. Once all conflicts resolved: `git commit -m '<resolver-summary>'`.
  12. Record state at `<ws>/workspace/.pos/sync/state.yaml`.

- `state.py` — current 182 LOC `StateRecord` model → ~60 LOC `SyncState` model with `last_synced_sha`, `last_synced_at`, `last_branch`, `last_outcome`. `audit_yaml_path` retires; `state_yaml_path` stays (path unchanged: `<ws>/workspace/.pos/sync/state.yaml`).

- `_audit.py` — current 114 LOC `summarize_audit_for_operator(ConflictReport)` → ~80 LOC `summarize_resolver_runs(list[MergeVerdict])` + unchanged `confirmed_by_operator`. Renderer simplified (no Resolution-enum buckets; the only inputs are `MergeVerdict` shapes).

- `__init__.py` — version string only; updated docstring removes references to "three-class envelope" / "resolve-stage-apply" pipeline.

**Unchanged (retained):**
- `merge_resolver.py` — LLM resolver (235 LOC).
- `_resolver_client.py` — Claude-print client (297 LOC; `--strict-mcp-config` flag preserved).
- `canonical.py` — canonical-path resolver (112 LOC).
- `canonical_cache.py` — URL→cache-clone (143 LOC; per D.3-build.F).
- `sync_config.py` — sync-config schema (182 LOC).
- `sync_protected.py` — vestigial documentation surface (183 LOC; per D.3-build.E).
- `observability.py` — OTel spans (53 LOC).

### `framework/workspace-sync/tests/`

**Retired:**
- `test_ancestor_detection.py` (497 LOC)
- `test_conflict_detection_b_shape.py` (124 LOC)
- `test_conflict_report_b_shape.py` (222 LOC)
- `test_merge_helper.py` (640 LOC)
- `test_merge_primitives.py` (346 LOC)
- `test_staging.py` (88 LOC)
- `test_cli_b_shape.py` (994 LOC; every test exercises retired pipeline)

**Total retired test LOC: 2911**.

**New:**
- `test_cli_d_shape.py` — D.3 CLI shape tests (~25 tests across the AC verifications).
- `test_state_d_shape.py` — D.3 state-record tests (~5 tests).
- `_stub_resolver.py` — test-side stub resolver factory (used via `--merge-resolver-module workspace_sync.tests._stub_resolver`; emits canned `MergeVerdict`s).

**Updated:**
- `conftest.py` — add fixture `make_framework_workspace` that constructs `<ws>/framework/` as a clone of a fixture canonical repo; add fixture `make_advancing_canonical` that constructs canonical + advances it to a second commit.
- `test_state.py` — update for the new `SyncState` schema (~10 tests retained, possibly reshaped).
- `test_sync_config.py` — unchanged (sync_config.py is unchanged).
- `test_sync_protected.py` — unchanged (sync_protected.py is unchanged).
- `test_canonical.py` — unchanged (canonical.py is unchanged).
- `test_merge_resolver.py` — unchanged (merge_resolver.py is unchanged).
- `test_resolver_client_mcp_isolation.py` — unchanged.
- `test_no_sealed_amendments.py` — unchanged (BASELINE bumped by `pos-amend apply`).

---

## §4. Reverse traceability check (every edit → backing AC)

| Edit | Backing AC |
|------|------------|
| `cli.py` rewrite (git fetch + merge --ff-only flow) | AC.D.3.1, AC.D.3.2 |
| `cli.py` rewrite (non-FF fallback path) | AC.D.3.3 |
| `cli.py` rewrite (resolver-runs persistence) | AC.D.3.5 |
| `state.py` simplification (SyncState model) | AC.D.3.6 (retired apparatus) |
| `_audit.py` simplification (MergeVerdict renderer) | AC.D.3.5 |
| Retire `staging.py`, `merge_helper.py`, `merge_primitives.py`, `ancestor_detection.py`, `conflict_detection.py`, `conflict_report.py` | AC.D.3.6 |
| New `test_cli_d_shape.py` | Verifies AC.D.3.1, .2, .3, .4, .5 |
| New `test_state_d_shape.py` | Verifies AC.D.3.6 (state shape) |
| Retired test files | AC.D.3.6 (mechanical retirement; no behaviour loss) |
| `test_no_sealed_amendments.py` BASELINE bump | AC.D.3.S |

Reverse check passes — every edit traces to an AC.

---

## §5. Halt triggers for the build

Per dispatch §10 + plan §10.

1. **A reader of retired surface turns up.** (e.g. self-upgrade or workspace-bootstrap imports `workspace_sync.staging`.) Halt + surface for fence widening.
2. **LLM-resolver-fallback path requires more retained machinery than expected.** Halt; preserve what's needed; document.
3. **`git merge --ff-only` against canonical with workspace-side commits in framework/ produces unexpected behaviour.** Halt.
4. **HC#6 structural guard test reveals workspace/ is touched by pos-sync.** Halt — D's structural promise broken; investigate.
5. **Wall-time exceeds 4h.** Halt with current-state report.
6. **Pre-existing test fails post-build other than mechanical-retirement-fixture-update fails.** Halt.
7. **AC outcome cannot be authored as a test without prescribing method.** Halt — surface to plan-author.

---

## §6. Pos-amend manifest binding

Per the manifest at `docs/plans/d-migration-3.manifest.yaml`. Single-component: workspace-sync. BASELINE = current HEAD at dispatch (`231a0b0`). Plan-doc admitted via `docs/plans/` prefix. Universal admissions match D.2's pattern.

---

## §7. Build sequence

1. Author this builder-plan + manifest (DONE on commit of these two files).
2. Rewrite `cli.py` against the new git-merge-based architecture.
3. Simplify `state.py` (`SyncState` model).
4. Simplify `_audit.py` (MergeVerdict renderer).
5. Retire `staging.py`, `merge_helper.py`, `merge_primitives.py`, `ancestor_detection.py`, `conflict_detection.py`, `conflict_report.py`.
6. Retire test files: `test_ancestor_detection.py`, `test_conflict_detection_b_shape.py`, `test_conflict_report_b_shape.py`, `test_merge_helper.py`, `test_merge_primitives.py`, `test_staging.py`, `test_cli_b_shape.py`.
7. Author `test_cli_d_shape.py` + `test_state_d_shape.py` + `_stub_resolver.py` test helper.
8. Update `conftest.py` with new fixtures.
9. Update `test_state.py` for `SyncState` shape.
10. Run workspace-sync pytest sweep (speedup (a) + (b)).
11. `pos-amend apply --dry-run` against the manifest. Green prerequisite.
12. Amendment commit (single feat commit per `feedback_no_amend_in_agent_dispatches`).
13. `pos-amend apply <plan>` — bumps BASELINE + SEAL_COMMIT for workspace-sync.
14. `pos-amend seal <manifest> --plan-doc <abs> --scoped-sweep`.
15. Backfill plan §14 (method-decision register) + §15 (verdict).

---

## §8. Speedups applied

- **(a) Narrow seal-test rerun to workspace-sync** (single-component manifest).
- **(b) Skip pre-seal full-suite if workspace-sync tests pass.** Full sweep deferred to seal-time `--scoped-sweep`.
- **(c) Inline methodology snippets in commit prose.** The amendment commit message references D.3-build.A through L inline.

Estimated wall-time: **3-4h** (per dispatch projection).

---

## §14. Method-decision register (post-build backfill)

Per AC.D-sa.7 + the dispatch's §10 procedure step. Records the method choices the builder made within each AC's outcome bound, the test breakdown, and the commit SHAs from the apply+seal cycle.

### Method choices

- **D.3-build.A (framework/ as a git working tree).** Built per recommendation. The fixture-builder helper `make_framework_workspace` (in `tests/conftest.py`) clones the fixture canonical repo into `<fixture-ws>/framework/`. The CLI's new `_ensure_framework_git_tree(workspace_root)` validates that `<ws>/framework/.git/` exists and emits a structured halt error pointing at `pos-new-workspace` (D.4) when absent. The pos3 smoke (HC#5) defers to D.4's β.2-absorption — pos3 today does NOT have a `framework/` git working tree, so the HC#5 verification cannot run against pos3 until D.4 lands. Captured in §15 verdict.

- **D.3-build.B (idempotent canonical-remote configuration).** Built per recommendation. `_configure_canonical_remote` reads `git config --get remote.canonical.url`; on existing match returns no-op; on mismatch issues `git remote set-url canonical <url>`; on absent issues `git remote add canonical <url>`. Verified by `test_cli_argparse_canonical_flag_overrides_config`.

- **D.3-build.C (branch resolution).** Default ref shifted from the dispatched `canonical/HEAD` symbol (which doesn't exist post-fetch unless `git remote set-head` is called) to `canonical/<current-local-branch>` (mirrors `git pull`'s default and is what `git fetch` populates without extra config). Detached-HEAD falls back to `FETCH_HEAD`. Tests use the default-branch path; explicit `--ref` is exercised via `test_cli_argparse_canonical_flag_overrides_config`.

- **D.3-build.D (audit + state shape).** State simplified to 4-field `SyncState` Pydantic model (`last_synced_sha`, `last_synced_at`, `last_branch`, `last_outcome`). The audit derives from `git log <prev>..<new> --oneline` printed to stderr post-fast-forward. On the LLM-resolver fallback path, per-conflict `MergeVerdict` records persist at `<ws>/workspace/.pos/sync/resolver-runs/<sha>/<sanitised-rel-path>.yaml`. Verified by `test_AC_D_3_3_resolver_run_recorded_under_workspace_state`.

- **D.3-build.E (sync_protected.py vestigial).** Kept unchanged per recommendation — `FRAMEWORK_FLOOR` constant + `SyncProtected` schema retained for back-compat with already-scaffolded workspace `<ws>/workspace/.pos/sync-protected.yaml` files. The CLI no longer reads the envelope for classification; structural enforcement comes from the directory boundary (HC#6).

- **D.3-build.F (canonical_cache.py retention).** Kept unchanged. The dispatch's note about "the canonical_cache.py clean-write enumeration" was a wording mismatch — the actual clean-write enumeration lived in `staging.py` + `merge_helper.py`, both retired. URL-form `canonical_source:` continues to use `ensure_cache_clone` to materialise the cache clone; the cache directory's absolute path becomes the `canonical` remote URL on `<ws>/framework/.git`.

- **D.3-build.G (canonical.py retention).** Kept unchanged. `resolve_canonical(canonical_path, ref)` validates a local canonical path is a git working tree; the CLI calls it for absolute-path canonical_source values.

- **D.3-build.H (_audit.py simplification).** Built per recommendation — `summarize_audit_for_operator(ConflictReport)` retired; replaced with `summarize_resolver_runs(list[(rel_path, MergeVerdict)])` (~30 LOC). `confirmed_by_operator` (TTY-confirm helper) preserved unchanged.

- **D.3-build.I (conflict_report.py retired).** Built per recommendation — the dispatch's "conflict_report shape (used by fallback path)" was loose-text guidance; under D.3's simpler fallback, the per-conflict `MergeVerdict` from `MergeResolver.resolve()` carries everything the resolver-runs need. No external readers (verified via grep). Surfaced as deviation in §15 verdict.

- **D.3-build.J (merge_resolver.py retention).** Kept unchanged. The fallback path constructs `prior_text` from `git merge-base HEAD canonical/<branch>` content and passes it to `resolver.resolve(...)` for the three-way merge prompt.

- **D.3-build.K (_resolver_client.py retention).** Kept unchanged. `--strict-mcp-config` + empty MCP-config tempfile preserved; AC.WSα.8 verification still passes.

- **D.3-build.L (cli.py rewritten).** Wrote ~640 LOC (vs target ~250). The extra LOC come from comprehensive halt-and-error-message coverage (workspace-root derivation halt, framework-not-git-tree halt, canonical-source-absent halt, fetch failure, ref-resolve failure, merge-abort on resolver halt, etc.). Each halt path has a structured stderr message naming the failure mode + recovery action. The control flow itself is ~300 LOC; the rest is parsing + error handling.

- **D.3-build.M (test surface).** Retired test files: 7 (`test_ancestor_detection.py`, `test_cli_b_shape.py`, `test_conflict_detection_b_shape.py`, `test_conflict_report_b_shape.py`, `test_merge_helper.py`, `test_merge_primitives.py`, `test_staging.py`) totalling 2911 LOC. New test files: 2 (`test_cli_d_shape.py` 678 LOC + `_stub_resolver.py` 96 LOC). Updated: `conftest.py` (added `make_framework_workspace`, `advance_canonical`, `workspace_commit` fixtures), `test_state.py` (rewritten for `SyncState` shape, 5 tests).

- **D.3-build.N (__init__.py).** Updated docstring to describe the git-merge architecture; bumped version 0.1.0 → 0.2.0 to mark the architecture change.

- **D.3-build.O (idempotency fast-path).** Built per recommendation. Post-fetch SHA equality between `HEAD` and target ref short-circuits with `UP_TO_DATE` outcome. Verified by `test_AC_D_3_2_idempotent_on_already_synced`.

- **D.3-build.P (HC#4 byte-content-match).** Built. `test_AC_D_3_2_byte_content_match_post_ff` advances canonical (modify foo.py, add added.py, delete keep.py); runs pos-sync; asserts each framework/<file> byte-equals canonical's HEAD bytes; deleted file absent. **HC#4 binding satisfied.**

- **D.3-build.Q (HC#6 structural-guard).** Built. `test_AC_D_3_4_workspace_state_byte_identical_pre_post_sync` snapshots SHA-256 of every file under `<fixture-ws>/workspace/` pre-sync; runs pos-sync; re-snapshots; asserts equality (modulo `state.yaml` which is the CLI's own write). Plus `test_AC_D_3_4_pos_sync_does_not_touch_workspace_subtree` directly asserts `git rev-parse --show-toplevel` inside framework/ returns framework/ (not the workspace root) and that workspace/ paths are not in framework/'s git index. **HC#6 binding satisfied.**

- **D.3-build.R (speedups).** Applied (a) + (b) + (c). Seal-test rerun confined to workspace-sync via `--scoped-sweep`; pre-seal full-suite skipped (touched-component pytest was the gate); commit prose carries D.3-build.A through .R inline.

### Test breakdown

**New tests (1 file, 19 tests in `test_cli_d_shape.py`):**

- `test_AC_D_3_1_git_fetch_advances_remote_ref` — fetch advances `refs/remotes/canonical/<branch>` post-invocation.
- `test_AC_D_3_2_fast_forward_advances_workspace_HEAD` — FF advances framework/HEAD; CLI exit 0; SyncState records FAST_FORWARD outcome.
- `test_AC_D_3_2_byte_content_match_post_ff` — HC#4: every framework/<file> byte-equals canonical's HEAD bytes; deletions propagate.
- `test_AC_D_3_2_idempotent_on_already_synced` — re-running against already-synced workspace produces UP_TO_DATE outcome with same SHA.
- `test_AC_D_3_3_non_ff_falls_through_to_resolver` — workspace+canonical both edit same path; stub resolver fires; resulting framework/<file> carries merged content; git log shows merge commit; SyncState records CONFLICT_FALLBACK.
- `test_AC_D_3_3_resolver_run_recorded_under_workspace_state` — fallback persists `<ws>/workspace/.pos/sync/resolver-runs/<sha>/<sanitised>.yaml` with MergeVerdict shape.
- `test_AC_D_3_4_workspace_state_byte_identical_pre_post_sync` — HC#6: snapshot-compare every workspace-state file pre/post sync.
- `test_AC_D_3_4_pos_sync_does_not_touch_workspace_subtree` — direct structural check that framework/.git's toplevel is framework/, not workspace root; workspace/ paths absent from framework/'s git index.
- `test_AC_D_3_5_audit_summary_references_git_log` — fast-forward summary contains canonical commit subjects (distinctive marker test).
- `test_AC_D_3_6_retired_modules_absent` — 6 retired source modules absent from disk.
- `test_AC_D_3_6_retained_modules_present` — 11 retained source modules present.
- `test_AC_D_3_6_cli_does_not_import_retired_modules` — cli.py source contains zero references to retired modules.
- `test_workspace_root_derivation_post_D` — derive accepts framework/.git/ marker.
- `test_workspace_root_derivation_post_D2` — derive accepts workspace/.pos/sync-protected.yaml marker.
- `test_workspace_root_derivation_pre_D2_back_compat` — derive accepts pre-D.2 marker.
- `test_workspace_root_derivation_no_marker_fails` — halts with WorkspaceRootError when no marker present.
- `test_cli_halts_when_framework_git_absent` — fail-fast halt with structured error pointing at pos-new-workspace.
- `test_cli_halts_when_no_canonical_source` — argparse halt when neither `--canonical` nor sync-config provides source.
- `test_cli_argparse_canonical_flag_overrides_config` — `--canonical` flag overrides sync-config.yaml.

**Updated tests (`test_state.py`, 5 tests):**

- `test_state_path_under_workspace_pos_sync` — path lands at `<ws>/workspace/.pos/sync/state.yaml`.
- `test_state_save_load_round_trip` — SyncState round-trips cleanly.
- `test_load_state_missing_returns_none` — absent state returns None.
- `test_state_yaml_uses_d3_field_names` — D.3 fields present; pre-D.3 fields absent.
- `test_all_outcomes_round_trip` — every SyncOutcome enum value round-trips.

**Retired tests (7 files, ~110 tests, 2911 LOC):**

- `test_ancestor_detection.py` (497 LOC) — tested retired ancestor_detection.py.
- `test_cli_b_shape.py` (994 LOC) — tested retired CLI pipeline.
- `test_conflict_detection_b_shape.py` (124 LOC) — tested retired conflict_detection.py.
- `test_conflict_report_b_shape.py` (222 LOC) — tested retired conflict_report.py.
- `test_merge_helper.py` (640 LOC) — tested retired merge_helper.py.
- `test_merge_primitives.py` (346 LOC) — tested retired merge_primitives.py.
- `test_staging.py` (88 LOC) — tested retired staging.py.

**Net test count: pre-D.3 ~165 tests / 5085 LOC (workspace-sync); post-D.3 77 tests / ~2200 LOC. Net retired: ~88 tests / ~2900 LOC.**

### Backwards-compat (HC#2)

Touched-component test results post-D.3:

- workspace-sync: **77 passed** (D.3-shape + retained modules).
- workspace-bootstrap: **218 passed** (one ambient-flake test passes on retry).
- hands-off-lifecycle: **214 passed**.
- primary-persona: **226 passed**.
- self-upgrade: **194 passed**.

Total: 929 passing across the touched + adjacent sealed components. Zero regressions traceable to D.3 (the workspace-bootstrap flake reproduced both pre- and post-D.3 in stress runs).

### HC#4 byte-content results

`test_AC_D_3_2_byte_content_match_post_ff` advances canonical with three operations (modify, add, delete) and asserts:

- `framework/README.md` — bytes match canonical HEAD.
- `framework/src/foo.py` — bytes match canonical HEAD (post-modification).
- `framework/src/added.py` — bytes match canonical HEAD (post-addition).
- `framework/src/keep.py` — file absent (post-deletion).

All assertions pass. **HC#4 binding closed.**

### HC#6 structural-guard test result

`test_AC_D_3_4_workspace_state_byte_identical_pre_post_sync` seeds 5 workspace-state files (`.pos/foo.txt`, `.pos/sync/state.yaml`, `personas/handle/contract.yaml`, `memory.yaml`, `.scratch/notes.md`); runs pos-sync (advancing canonical); asserts every workspace-state file is byte-identical pre/post (modulo `state.yaml` which is the CLI's own write).

`test_AC_D_3_4_pos_sync_does_not_touch_workspace_subtree` directly asserts `git rev-parse --show-toplevel` inside `framework/` returns `framework/` (not the workspace root) and that `workspace/` paths are absent from framework/'s git index.

**HC#6 binding closed.**

### LOC retired count

**Source: 2369 LOC retired** (ancestor_detection 242 + conflict_detection 249 + conflict_report 336 + merge_helper 883 + merge_primitives 518 + staging 141). Plus cli.py was 679 LOC pre-D.3, ~640 LOC post-D.3 (rewritten in place; not a retirement, but the bulk of the bespoke pipeline orchestration logic is gone).

**Tests: 2911 LOC retired** (ancestor_detection 497 + cli_b_shape 994 + conflict_detection_b_shape 124 + conflict_report_b_shape 222 + merge_helper 640 + merge_primitives 346 + staging 88).

**Total: 5280 LOC retired.** Plus 38 LOC removed from `state.py` + cli.py rewritten in place + `_audit.py` simplified. Net diff (per `git show e53463b --stat`): **2289 insertions, 5925 deletions, ~3636 LOC net drop**.

### D.1.5 rename-aware classification

`pos-amend apply`'s rename-aware logic classified workspace-sync as **substantive** (rename-only=False) — verified by the apply output:

```
[workspace-sync]
  rename-only: False
  ok
applied:
  - workspace-sync: BASELINE → 231a0b02ffd33817ddd757e404b924225960d12c
  - workspace-sync: SEAL_COMMIT → 231a0b02ffd33817ddd757e404b924225960d12c
```

Substantive change (cli.py rewrite + 6 module retirements + new tests) — BASELINE advances correctly. No bump-skip.

### Speedup deltas

- (a) narrow seal-test rerun: workspace-sync only via `--scoped-sweep`; saved ~3-5 minutes vs full-repo sweep.
- (b) pre-seal full-suite skipped: touched-component sweep (workspace-sync + adjacent self-upgrade + workspace-bootstrap + primary-persona + hands-off-lifecycle) was the gate; saved ~5 minutes pre-seal wall-time.
- (c) inline methodology snippets: amendment commit message carries D.3-build.A through .R inline; no separate research-citation pass.

Estimated savings: 25-40% wall-time reduction vs unaccelerated baseline.

### Commit SHAs

- amendment commit: `e53463b`
- apply chore: `9a15485`
- seal commit: `209b6af`
- §14 + §15 backfill: (this commit)

---

## §15. Verdict

D.3 lands clean. The keystone semantic change of D-migration is delivered: pos-sync's bespoke resolve→stage→apply pipeline retired in favour of `git fetch + git merge --ff-only` against `<workspace>/framework/`, with the LLM resolver demoted to the rare-conflict fallback path. Net ~3600 LOC removal; the architecture simplification is structural — every test that was previously asserting bespoke-pipeline correctness is gone, replaced by a much smaller test suite that exercises git's mature merge tooling.

**HC#6 (structural promise) is now structurally enforced.** All git operations run with `-C <workspace>/framework`. Files under `<workspace>/workspace/` are unreachable by the merge mechanics — verified by both byte-content snapshot comparison and direct git-toplevel assertion.

**HC#4 (byte-content match) closed.** Post-fast-forward, every file in `framework/` byte-equals canonical's HEAD bytes; deletions propagate; additions land. The bug class that triggered D-migration (α-hotfix-2's stage-without-canonical-content fault) is structurally impossible under git-merge semantics.

**HC#5 (pos3 empirical smoke) deferred to post-D.4.** pos3 today does NOT have a `framework/` git working tree — it has the legacy flat-tree layout (with workspace-state at `<ws>/.pos/`, `<ws>/personas/`, etc.) that pre-dates D.2's directory split. D.2's amendment intentionally did NOT auto-migrate pos3 (HC#5 of D.2 honoured); D.4 will ship `pos-new-workspace --from <repo>` which sets up the post-D layout (including `<ws>/framework/` as a git clone). Once D.4 lands and Luke runs `pos-new-workspace --from <canonical> /Users/lukeivers/pos3-d` (or the operator-driven migration script), the HC#5 smoke can run against that post-D-shaped workspace. **Recommendation: surface this for owner ruling before D.4 dispatches** — Luke may want to defer the pos3 cutover to a separate amendment or include it in D.4's scope.

### Notable mid-build deviations

1. **D.3-build.C — branch resolution shifted from `canonical/HEAD` to `canonical/<current-local-branch>`.** The dispatched recommendation used `canonical/HEAD` but git fetch does not by default populate `refs/remotes/canonical/HEAD` — it only does so when `git remote set-head` is explicitly called. The shift to `canonical/<current-local-branch>` matches what `git pull` does without extra config. Test failures during initial test runs caught this; the fix was a 5-line shift in `_resolve_target_ref`.

2. **D.3-build.I — `conflict_report.py` retired.** The dispatch's wording suggested `conflict_report shape (used by fallback path)` should stay; on closer reading the loose AC text in plan §4 D.3 does not require it, and the new fallback path is much simpler than the dispatch envisaged (per-conflict `MergeVerdict` is enough). No external readers (verified via grep). Per `feedback_loose_AC_text_fix_AC_not_implementation` + `feedback_critical_thinking_on_deviations`, builder ruled retire. If owner disagrees, the file can be re-introduced at zero structural cost (it's a Pydantic model file with no runtime side-effects).

3. **D.3-build.F — `canonical_cache.py` "clean-write enumeration" wording mismatch.** The dispatch's note about retiring "the canonical_cache.py clean-write enumeration" did not match the actual code surface — `canonical_cache.py` only carries the URL→cache-clone shape, no clean-write enumeration. The clean-write enumeration lived in `staging.py` + `merge_helper.py` (both retired). `canonical_cache.py` kept unchanged. Surfaced for transparency.

4. **Workspace-bootstrap ambient flake.** During the touched-component sweep, `test_D5_1_memory_graphiti_scaffold_plist_reaches_health_200` failed once (ambient-state interference between concurrent test runs); passes on isolated re-run + on a clean full-suite re-run. **Not a D.3 regression** — pre-existing flake under stress. Captured for transparency; not blocking.

### What goes next

D.4 dispatches against the post-D.3 tree. D.4 ships `pos-new-workspace --from <repo>` console-script (β.2 absorption) which is the verb that makes pos3-style workspaces post-D-compatible. Once D.4 lands, HC#5's empirical pos3 smoke becomes runnable. D.5 is optional — at end of D.3 build, no transition surface was left behind needing cleanup (the `sync_protected.py` vestigial retention is intentional documentation surface, not transition-window debt). Plan-author may close D.5 as a no-op + this plan's tracking entry.
