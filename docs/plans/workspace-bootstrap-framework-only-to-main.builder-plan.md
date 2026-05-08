# Builder-plan — workspace-bootstrap: framework-only → main

Authored 2026-05-04 by plan author (Sonnet, dispatcher: Luke).
Companion to `docs/plans/workspace-bootstrap-framework-only-to-main.md`.
Files + symbols this build will touch.

Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## Pre-edit gate (verify BEFORE any source edit)

1. `git rev-parse HEAD` — confirm canonical `pos-v2` tip
   (`ad1e6bb` at plan-doc authoring time; may advance via
   plan-doc + manifest commits before BASELINE freezes).
2. `grep -rn "FRAMEWORK_ONLY_BRANCH\|_materialise_framework_only_branch" framework/workspace-bootstrap/src/`
   MUST return exactly the 3 production callsites named below + 1
   helper definition + 1 constant definition. If 4+ callsites exist,
   **HALT** and surface to dispatcher.
3. `grep -rn "_materialise_framework_only_branch" framework/ plugins/ docs/`
   MUST return zero hits outside `framework/workspace-bootstrap/src/`
   (i.e. helper is module-private; no external callers). If external
   callers exist, **HALT**.
4. `grep -rn "from loam.publish_framework_only" framework/ plugins/`
   MUST return zero hits in active source (the synthesis tool is
   archived). If active-source hits exist, **HALT** — they should
   have been migrated by the dev-architecture migration.
5. Verify canonical `main` (= canonical `pos-v2` HEAD) carries the
   `framework/<comp>/` shape:
   `git ls-tree -r --name-only HEAD | grep -E '^framework/' | head`
   MUST return entries.
6. BASELINE for this amendment: `git rev-parse HEAD~1` at the time
   of the source-edit commit (mirrors the per-cycle BASELINE-as-
   HEAD~1 pattern from amendments #34–#39 + v0.1.6/v0.1.7 cycles).

## D-build choices (recommended; builder may diverge)

- **D-build.1 — constant naming.** Recommend `CANONICAL_BRANCH =
  "main"`. Module-level scope; replaces `FRAMEWORK_ONLY_BRANCH`.
- **D-build.2 — helper rename.** Recommend
  `_materialise_canonical_branch(path: Path)` (was
  `_materialise_framework_only_branch`). Body unchanged except for
  the constant reference + docstring rewrite.
- **D-build.3 — conftest fixture.** Recommend single-tree fixture:
  `git init --initial-branch=main` + write files + commit; no
  second branch synthesis. Drop `_FIXTURE_MANIFEST_REL` +
  `_FIXTURE_MANIFEST_YAML` + the `synthesise_framework_only` call.
- **D-build.4 — test file renaming.** Recommend keep file paths,
  rename test fn bodies + docstrings only. AC.FBE.10's file →
  rename body to AC.WBM2M.2; AC.SFR.5's second test → delete.

## Files this build will touch

### Modified source

- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py`
  - Replace `FRAMEWORK_ONLY_BRANCH = "framework-only"` constant
    with `CANONICAL_BRANCH = "main"` (per D-build.1).
  - Rename helper `_materialise_framework_only_branch` →
    `_materialise_canonical_branch` (per D-build.2). Body update:
    references `CANONICAL_BRANCH`. Docstring rewrite: drop synth-
    pipeline narrative; replace with "materialise canonical branch
    as a local ref so subsequent `git clone` propagates it".
  - `_clone_canonical(...)` default kwarg flips: `branch: str = CANONICAL_BRANCH`.
    Docstring rewrite: drop synth-pipeline narrative; replace with
    "clone canonical and check out `main`".
  - `_resolve_url_to_clone_source(...)` — call site flips from
    `_materialise_framework_only_branch(cache_path)` to
    `_materialise_canonical_branch(cache_path)`. Comment block
    rewrite (drops synth-pipeline narrative).
  - `bootstrap_new_workspace(...)` local-path branch — call site
    flips from `_materialise_framework_only_branch(local_path)` to
    `_materialise_canonical_branch(local_path)`. Comment block
    rewrite (drops FBE.10 BLOCKER reference; replace with terse
    "mirror the URL-form materialisation step").
  - Module-level docstring (lines ~15–67) — rewrite occurrences of
    `framework-only` → `main` with coherent prose.
  - The `# Single-framework restructure (amendment #67)` block
    comment (lines ~175–183) — rewrite to reflect the post-OSS-
    migration shape (clones canonical's `main`, no synthesis).

### Modified tests

- `framework/workspace-bootstrap/tests/conftest.py`
  - Drop `_FIXTURE_MANIFEST_REL` + `_FIXTURE_MANIFEST_YAML` constants.
  - Drop `manifest_target.write_text(_FIXTURE_MANIFEST_YAML)` block.
  - Drop the `if publish_framework_only: ... synthesise_framework_only(...)`
    block entirely.
  - `_git(["init", "--initial-branch=pos-v2"], cwd=root)` →
    `_git(["init", "--initial-branch=main"], cwd=root)`.
  - Drop the `publish_framework_only: bool = True` keyword arg
    from `_make_fixture_canonical` (consumers that pass
    `publish_framework_only=False` need to be audited; expected
    none post-cleanup, but verify pre-edit).
  - Update docstrings: drop framework-only / synth-pipeline
    references.

- `framework/workspace-bootstrap/tests/test_AC_FBE_10_1_local_path_clone_of_canonical.py`
  - Rewrite header docstring + test fn name to AC.WBM2M.2.
  - Flip the assertion `framework_branch == "framework-only"` →
    `framework_branch == "main"`.
  - Drop the `local_branches.strip() == ""` pre-condition assertion
    (with `main` as the default, the stranger-clone's `main` IS
    a local branch — see AC.WBM2M.3 discussion).
  - Drop the `origin/framework-only` remote-tracking-ref assertion
    (replace with `origin/main` if useful).
  - Test fn rename: `test_AC_FBE_10_1_local_path_clone_of_canonical_materialises_framework_only`
    → `test_AC_WBM2M_2_local_path_clone_of_canonical_lands_on_main`.

- `framework/workspace-bootstrap/tests/test_AC_SFR_5_stranger_clones_canonical.py`
  - First test (`test_AC_SFR_5_stranger_clone_byte_identical_to_pos_v2`):
    rename to `test_AC_SFR_5_stranger_clone_byte_identical_to_main`;
    flip every `pos-v2` literal in the body to `main`. Assertion
    `stranger_branch == "pos-v2"` → `stranger_branch == "main"`.
  - Second test (`test_AC_SFR_5_framework_only_reachable_via_explicit_branch`):
    DELETE entirely (no second branch on canonical post-migration).

- `framework/workspace-bootstrap/tests/test_pos_new_workspace.py`
  - `test_AC_D_4_1_local_canonical_creates_working_workspace`:
    flip `head_branch == "framework-only"` → `head_branch == "main"`.
    Update the inline narrative comment (lines ~120–138) to
    reflect post-migration shape (no synth pipeline; the doubling
    contract holds because canonical's `main` carries the same
    `framework/<comp>/...` paths). The `fixture_pairs` list shape
    stays the same (paths unchanged).
  - `test_AC_D_4_1_url_form_routes_through_cache_clone`: flip the
    inline narrative similarly. The byte-content assertion on
    `framework/framework/README.md` stays; only the comments need
    to drop synth-pipeline narrative.
  - Other tests in this file that name `framework-only` literally
    in docstrings or comments — text-only updates; no assertion
    changes.

- `framework/workspace-bootstrap/tests/test_AC_SFR_1_single_framework_directory.py`
  - Multiple assertions on `framework-only` as the cloned branch
    (lines ~206, ~223): flip to `main`.
  - The failure-mode test (asserts `CloneFailedError` when canonical
    does not publish `framework-only`, uses
    `publish_framework_only=False` kwarg): **DELETE entirely**. The
    equivalent failure mode does not exist post-migration — `main`
    is canonical's default branch; git refuses to clone a repo
    with no default branch (no equivalent `publish_main=False`
    fixture toggle). The kwarg goes away with the conftest
    rewrite.
  - Update docstrings + comments throughout to drop framework-only
    / synth-pipeline references.

- `framework/workspace-bootstrap/tests/test_AC_SFR_4_pos_sync_composition.py`
  - **Structural dependency rewrite** (halt-and-surface finding,
    sub-plan §3 #4 footnote): the test imports
    `from loam.publish_framework_only.synth import synthesise_framework_only`
    and uses it to advance the canonical-side `framework-only`
    branch between bootstrap and re-sync (testing the ff-graph
    composition contract).
  - Drop the `synthesise_framework_only` import entirely.
  - Replace step 5 ("re-synthesise framework-only") with a direct
    `git commit` on the fixture canonical's `main` branch (e.g.
    write a new file under `framework/<comp>/`, `git add`, `git
    commit -m "fixture advance"`). The bootstrap-then-sync flow
    inherits the ff-graph contract via canonical's HEAD advance,
    not via a separate synthesis tool.
  - Update docstrings + AC narrative to reflect the simpler flow.

- Any other `tests/test_AC_*.py` file with literal `framework-only`
  in docstring or comment — text-only sweep. Builder runs
  `grep -rn "framework-only" framework/workspace-bootstrap/tests/`
  and updates every hit.

### New tests

- `framework/workspace-bootstrap/tests/test_AC_WBM2M_1_constant_and_callsites_flip_to_main.py`
  - Parses `new_workspace.py` source.
  - Asserts `FRAMEWORK_ONLY_BRANCH` is not present as a name.
  - Asserts `CANONICAL_BRANCH = "main"` is present.
  - Asserts `"framework-only"` substring does NOT appear in any
    string literal in the file (allowance for historical
    docstring narrative if the builder chose to retain it for
    audit-trail; if so, narrow the assertion to "no string literal
    referenced as a branch name in `argv`").
  - Asserts the 3 callsites reference `CANONICAL_BRANCH`.

- `framework/workspace-bootstrap/tests/test_AC_WBM2M_3_local_path_materialises_main.py`
  - Builds a fixture canonical via `make_fixture_canonical`.
  - Clones it to a stranger-clone path.
  - Calls `_materialise_canonical_branch(stranger_clone_path)`.
  - Verifies no error raised.
  - Verifies `refs/heads/main` exists post-call (already did
    pre-call; this is the no-op idempotency contract).

- `framework/workspace-bootstrap/tests/test_AC_WBM2M_4_conftest_fixture_main_shape.py`
  - Calls `make_fixture_canonical(tmp_path)`.
  - Asserts the resulting tree's HEAD is on `main`
    (`git -C <root> rev-parse --abbrev-ref HEAD == "main"`).
  - Asserts `framework/<comp>/...` paths exist (e.g.
    `framework/workspace-sync/src/workspace_sync/__init__.py`).
  - Asserts the synthesis-tool import path is NOT in the conftest
    module's globals (e.g. `synthesise_framework_only` not
    callable from the conftest's namespace).

### Manifest

- `docs/plans/workspace-bootstrap-framework-only-to-main.manifest.yaml`
  - Single-component fence on `framework/workspace-bootstrap/`.
  - Universal admissions: `docs/plans/`, `CLAUDE.md`,
    `docs/odd-in-pos.md`, `docs/odd-methodology.md`,
    `docs/FUTURE_IDEAS.md`, `docs/STATE.md`,
    `docs/FUTURE_IDEAS_DRAFT.md`.
  - BASELINE: `<HEAD~1 of source-edit commit>` (filled at
    apply-time; placeholder in initial commit).
  - Narrative target: `framework/workspace-bootstrap/seals/SEAL_COMMIT.workspace-bootstrap-framework-only-to-main`.

### Documentation (universal admissions, post-seal backfill)

These are post-seal updates committed as a follow-on doc-only commit
per `feedback_serialize_amendment_builds` separation rule:

- `docs/STATE.md` — new Change log entry dated 2026-05-04
  with seal SHA + outcome summary.
- `docs/plans/eric-final-delivery-plan-2026-05-04.md` — §2
  table row addition under the v0.1.7 / migration section.
- `docs/plans/v0-1-x-roadmap.md` — §8 method-decision
  register row addition.

## Cycle structure

Single cycle (single-component amendment per dispatch §1).

1. **Plan-doc commit** (this doc + manifest + sub-plan).
2. **Source-edit commit** — single semantic commit covering source
   + tests (the BASELINE is `HEAD~1` at this commit's tip).
3. **`loam amend apply`** lands an auto-commit per cycle bookkeeping
   (advances sidecar to source-edit commit + carries fence diff).
4. **`loam amend seal`** lands the deterministic seal commit.
5. **Doc backfill commit** (post-seal; STATE.md + eric-final + roadmap).
6. **Remote ref deletion** (post-seal; out-of-band; `git push lukeivers/loam :framework-only`).

## Non-method-prescription footer

Per `feedback_agent_prompts_scope_only`: this builder-plan names the
files + symbols + AC contracts. Method choices (exact regex for sed
sweeps, exact test fn names, exact docstring prose) are the builder's
call. The AC tests pin the observable contract; everything else
that satisfies the contract is acceptable.
