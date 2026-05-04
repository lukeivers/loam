# Sub-plan — workspace-bootstrap: framework-only → main

Authored 2026-05-04 by plan author (Sonnet, dispatcher: Luke).
Working directory: `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2).

Companion files:

- Builder-plan: `docs/rebuild/plans/workspace-bootstrap-framework-only-to-main.builder-plan.md`
- Manifest: `docs/rebuild/plans/workspace-bootstrap-framework-only-to-main.manifest.yaml`
- Status: `<pos3>/workspace/.scratch/claude-output/workspace-bootstrap-framework-only-to-main-status-2026-05-04.md`

---

## §1 — Objective

Single sealed-component amendment on `framework/workspace-bootstrap/`
that switches the bootstrap's clone-target branch from
`framework-only` (the now-deprecated synthesis output) to `main` (the
canonical default branch on `lukeivers/loam`). Post-seal, a stranger
clones `lukeivers/loam`, runs `loam init <workspace>` (no `--from`
required given FBE.9 cwd-default-when-git-tree), and lands a working
canonical-shape workspace whose `framework/` subdir is checked out on
`main`. The retained `loam:framework-only` legacy ref on the remote
gets deleted in the post-seal cleanup step (§6); after that,
`loam:main` is the only ref Eric (or any stranger) needs.

---

## §2 — Provenance

**Surfaced from:** `docs/rebuild/plans/oss-dev-architecture-survey-and-migration-2026-05-04.md`
§8.8 — the migration agent's halt-and-surface during phase 4 of the
dev-architecture migration (sealed at `ea8c4bb`, 2026-05-04). The
migration agent identified that `FRAMEWORK_ONLY_BRANCH = "framework-only"`
is wired into 3 production callsites + the test conftest depends on
the now-archived synthesis tool to fabricate fixtures + multiple AC
tests are explicitly named for the framework-only branch. Switching to
`main` requires a sealed-component amendment, not an inline change.

**Why deferring was safe:** `loam:main` carries the full canonical
history (HEAD `c7e5dd7` post-migration). The remote retains the legacy
`loam/framework-only` ref (stale at `1bea0f8` pre-migration synthesis
output) for any in-flight stranger clone that started before
2026-05-04. Existing bootstrap flows continue to work against
`framework-only` until that ref is deleted (post-seal, §6).

**Quality bar (Luke directive 2026-05-04):**

> "I want this to WOW him. It can't be half-assed. What ships needs to
> deliver what we promise. No excuses."

Every release-note promise corresponds to tested + reliable behavior.
All 6 smoke dimensions exercised. If any AC ships partial → halt.

---

## §3 — Scope

### In scope

1. Replace the module-level constant `FRAMEWORK_ONLY_BRANCH = "framework-only"`
   in `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py`
   with a `main`-targeting constant. Naming is the builder's call;
   recommended `CANONICAL_BRANCH = "main"` to match the survey doc's
   §4.1 one-line summary ("default branch: `main`").
2. Update the 3 production callsites:
   - `_materialise_framework_only_branch(...)` — re-points
     `refs/heads/<branch>` at `refs/remotes/origin/<branch>` on the
     cache. Helper renames + targets `main`.
   - `_clone_canonical(...)` — clones canonical and checks out
     `<branch>`. Default keyword arg flips to `main`.
   - `bootstrap_new_workspace(...)` local-path branch — calls the
     materialise helper before cloning. Mirrors the URL-form flow.
3. Update the test conftest (`framework/workspace-bootstrap/tests/conftest.py`)
   `make_fixture_canonical` factory:
   - Remove dependency on `loam.publish_framework_only.synth.synthesise_framework_only`
     (the synthesis tool is archived at
     `docs/rebuild/archive/synthesis-tool-2026-05-04/`; can't be
     imported from active source).
   - Replace the synthesis step with a direct git fixture: the fixture
     canonical is a single git working tree on `main` (initialised
     with `--initial-branch=main`), carrying `framework/<comp>/...` +
     top-level docs. No second branch synthesis needed; the bootstrap
     clones `main` and lands the same `<workspace>/framework/<comp>/`
     shape via the existing doubled-component contract (FBE.2c.5
     binding, see §3.2 below for whether to preserve or simplify).
   - Drop the `_FIXTURE_MANIFEST_REL` + `_FIXTURE_MANIFEST_YAML` block
     (publish-mode-manifest no longer needed; was synthesis-tool
     input).
4. Update the AC tests that name `framework-only` literally:
   - `test_AC_FBE_10_1_local_path_clone_of_canonical.py` — rename
     and rewrite to assert `main` post-bootstrap (or replace with a
     successor AC; see §4 acceptance criteria).
   - `test_AC_SFR_5_stranger_clones_canonical.py` — second test
     `test_AC_SFR_5_framework_only_reachable_via_explicit_branch` is
     obsolete (no second branch); delete or rewrite to assert that a
     no-flag clone produces the working tree on `main`.
   - `test_pos_new_workspace.py` — `test_AC_D_4_1_local_canonical_creates_working_workspace`
     contains the assertion `framework_branch == "framework-only"`;
     flip to `"main"`. The `test_AC_D_4_1_url_form_routes_through_cache_clone`
     test reads `framework/README.md` content via the cache clone;
     flip the branch tracking assertion.
   - `test_AC_SFR_1_single_framework_directory.py` — multiple
     assertions on `framework-only` as the cloned branch + the
     "canonical does not publish framework-only" failure-mode test
     (uses `publish_framework_only=False`). With `main` as the
     default branch on canonical, the failure mode "canonical does
     not publish `main`" cannot happen for any real clone — git
     refuses to clone a repo with no default branch. The
     failure-mode test (`test_AC_SFR_1_*_failure_mode_*` or whatever
     it's named) should be DELETED — there is no equivalent failure
     mode post-migration (`main` is always the default; the kwarg
     that gates fixture-canonical fabrication of a non-default
     branch goes away with the synthesis tool).
   - `test_AC_SFR_4_pos_sync_composition.py` — **structural
     dependency** on `from loam.publish_framework_only.synth import
     synthesise_framework_only`. The test exercises the
     bootstrap-then-sync ff-graph composition by (a) bootstrapping
     against a fixture canonical, (b) advancing the synthesis-only
     branch via `synthesise_framework_only`, (c) re-syncing, and
     (d) verifying byte-equality post-sync. Post-migration the
     ff-graph advancement happens on canonical's `main` branch
     directly (no synthesis layer); the test rewrites to advance
     canonical's `main` HEAD via a direct `git commit` on the
     fixture canonical, then re-syncing. Conceptually simpler;
     drops the `synthesise_framework_only` import entirely.
   - Other tests with framework-only literals in docstrings or
     comments — update text only; no assertion changes if not present.

   **Halt-and-surface finding (post-plan-authoring):** the dispatch's
   halt-trigger language ("Refactor surfaces a structural assumption
   beyond the 3 callsites + tests → halt + surface") was checked
   pre-plan-authoring. Two additional structural dependencies
   surfaced (the AC.SFR.1 failure-mode kwarg + the AC.SFR.4
   synthesise_framework_only import); both fall WITHIN the
   workspace-bootstrap fence + scope-only the test layer (no
   additional production-callsite surface). The plan absorbs them
   as a single AC family extension (AC.WBM2M.5 covers all test-
   layer rewrites). If the builder finds a THIRD structural
   surface beyond these two, halt + surface to dispatcher.

### In scope (post-seal cleanup)

5. Delete the `loam:framework-only` ref on the remote
   (`git push lukeivers/loam :framework-only`). Sealed amendment
   itself does NOT need this; Luke's discretion; recommended within
   24 h of seal so the public surface settles. See §6.
6. Backfill seal SHA into:
   - `docs/rebuild/STATE.md` Change log
   - `docs/rebuild/plans/eric-final-delivery-plan-2026-05-04.md`
     §2 (in the v0.1.7 / migration row, as a follow-up amendment
     entry)
   - `docs/rebuild/plans/v0-1-x-roadmap.md` §8 method-decision
     register (post-build SHA row)

### Out of scope

- Renaming the test files themselves (low-value churn; rename inside
  the file-content is sufficient if the AC label changes).
- The `framework/tools/loam/tests/test_no_sealed_amendments.py`
  `allowed_prefixes` dead-text reference to
  `"framework/tools/pos-publish-framework-only/"` — surfaced in the
  migration agent's halt as flagged for cleanup in "the next sealed-
  component amendment that touches them"; that touches `loam`
  component, not `workspace-bootstrap`. **DEFERRED to a separate
  follow-up amendment** — outside this fence.
- The `framework/tools/loam-memory-inspect/README.md` similar dead-
  text reference — same reason; outside fence.
- v0.1.8 work (extractor heavy, Ruby first-class, 6 SKILLs).
- Cost-audit recommendations (manifest narrative collapse, commit
  merge, etc.) — separate amendment per dispatcher direction.

### §3.2 — Doubled-component shape (FBE.2c) — keep or simplify?

The current bootstrap produces `<new-ws>/framework/framework/<comp>/`
because the framework-only branch carried `framework/<comp>/` paths
(post-FBE.2b prefix-preserving synth). When we clone `main` instead,
canonical's `pos-v2` HEAD also has `framework/<comp>/` paths — the
same shape — so the doubled-component contract holds without change.
The clone-into `<new-ws>/framework/` produces
`<new-ws>/framework/framework/<comp>/` regardless of which branch
we clone (synthesised `framework-only` or canonical `main`).

**Decision: KEEP the doubled-component contract.** This minimises
behavior regression for fresh-clone bootstrap (the dispatch's
explicit goal: "Existing test contracts preserved byte-identically
where possible"). FBE.2c.5 + FBE.2c.6 assertions stand verbatim;
only the branch name changes. The corpus-discovery readers' fall-
through to `<workspace>/framework/` (AC.SFR.3) continues to work
because both top-level docs (`CLAUDE.md`, `docs/...`) live at
single-level `<new-ws>/framework/<doc>` on `main` exactly as they
did on `framework-only` (canonical `pos-v2` carries them at root,
clone produces them one level under `framework/`).

If the reader thinks the doubling itself is a bug worth fixing now
that we control the clone target — that is a separate amendment
(structural shape change to the workspace tree); halt-and-surface to
Luke before doing it.

---

## §4 — Acceptance criteria

### AC family naming

`AC.WBM2M.{1..6}` ("workspace-bootstrap main migration"). Six
criteria covering the constant rename, three callsites, conftest
fixture rewrite, AC test updates, and seal-diff hygiene.

### AC.WBM2M.1 — Constant + callsite flip to `main`

`framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py`
contains exactly one module-level branch-name constant (recommended
`CANONICAL_BRANCH = "main"`). The substring `"framework-only"` does
NOT appear anywhere in the file (`grep` returns zero hits) except in
the file's authorial-history comments if any, which should also be
updated to read coherently against the new shape. The three call
sites (`_materialise_framework_only_branch` — renamed to e.g.
`_materialise_canonical_branch`, `_clone_canonical`, and the local-
path branch of `bootstrap_new_workspace`) all reference the new
constant.

**Test:** `test_AC_WBM2M_1_constant_and_callsites_flip_to_main.py` —
parses the source file, asserts (a) `FRAMEWORK_ONLY_BRANCH` is not
present as a name, (b) the new constant is present with value
`"main"`, (c) the substring `"framework-only"` does not appear in
any source string literal, (d) the three callsites reference the
new constant.

### AC.WBM2M.2 — Stranger-clone of canonical produces a working workspace

A stranger clones a fixture canonical (built fresh per the rewritten
conftest factory; single git working tree on `main`), runs
`bootstrap_new_workspace(...)`, and lands a working workspace whose
`framework/` subdir is checked out on `main`. End-to-end equivalent
of the dispatch's smoke D1 cold-state at the AC level.

**Test:** `test_AC_WBM2M_2_stranger_clone_lands_working_workspace.py`
— mirrors `test_AC_FBE_10_1_local_path_clone_of_canonical.py` shape
but asserts `framework_branch == "main"` and uses the rewritten
conftest factory (no synthesis tool).

### AC.WBM2M.3 — Local-path branch materialises `main` from remote-tracking ref

When a stranger clones canonical and runs `bootstrap_new_workspace`
against the local clone (the post-FBE.9 cwd-default-when-git-tree
pattern), `main` exists only as `refs/remotes/origin/main` on the
stranger-clone (because `git clone` propagates only LOCAL refs from
the source — and the source's `main` IS the local default, so the
stranger-clone's `main` IS local; pre-condition differs from the
framework-only case, see below).

**Subtle but important:** unlike `framework-only` (which was a
non-default branch on canonical), `main` IS the default branch on
canonical post-migration. Therefore on a stranger-clone of
canonical, `main` is automatically a LOCAL branch (the default
branch of the source IS the only local branch propagated by
`git clone`). The materialise helper's logic (re-point local
ref at remote-tracking ref) becomes a NO-OP for the typical
stranger-clone case — `refs/heads/main` already exists.

**Decision per ODD §1.1 (builder's call):**

- **Option (a):** keep the materialise helper, accepting it's a no-
  op on the typical case but defensive against any future scenario
  where `main` IS NOT the default. Simplest diff against current
  code.
- **Option (b):** remove the materialise helper entirely. Cleaner
  code; fewer paths.

**Recommendation: (a) keep + simplify.** The helper now has a
single useful case (cache clone where the cache might track multiple
remotes), and its no-op behavior on the typical case is harmless +
self-documenting. If the helper is removed entirely (option b), the
URL-form flow's cache-clone step would lose its defensive
materialisation; net risk > net cleanup.

**Test:** `test_AC_WBM2M_3_local_path_materialises_main.py` —
verifies the materialise helper runs without error on a stranger-
clone where `main` already exists as a LOCAL branch (idempotent;
`git update-ref` is a no-op when the ref already points at the
target SHA).

### AC.WBM2M.4 — Conftest fixture builds a `main`-shape canonical without synthesis

The `make_fixture_canonical` factory in
`framework/workspace-bootstrap/tests/conftest.py` produces a fixture
canonical that:

- Uses `git init --initial-branch=main` (was `--initial-branch=pos-v2`).
- Carries `framework/<comp>/...` paths + top-level docs verbatim
  (no synthesis step; canonical pos-v2 HEAD already has this shape
  post-D-cutover).
- Does NOT import `loam.publish_framework_only.synth` (the module
  is in `docs/rebuild/archive/synthesis-tool-2026-05-04/`, no
  longer importable from active source).
- Does NOT write `publish-mode-manifest.yaml` (deprecated input
  to the synthesis tool).
- Returns the same `Path` shape callers expect.

**Test:** `test_AC_WBM2M_4_conftest_fixture_main_shape.py` — calls
`make_fixture_canonical`, asserts (a) the resulting tree's HEAD is
on `main`, (b) `framework/<comp>/...` paths exist, (c) the
synthesis-tool import isn't reachable from the conftest's import
graph.

### AC.WBM2M.5 — Existing AC tests updated, not deleted (where contracts persist)

For every existing AC test that asserted `framework_branch == "framework-only"`:

- The assertion flips to `"main"` (one-character semantic change at
  the AC level).
- Test names referring to `framework-only` in the file body are
  updated; test FILE names are NOT renamed (low-value churn) unless
  the AC label changes (which it does for AC.FBE.10 → AC.WBM2M.2 and
  the obsolete second AC.SFR.5 test).
- The obsolete `test_AC_SFR_5_framework_only_reachable_via_explicit_branch`
  test (asserts a second branch is reachable) is DELETED — there is
  no second branch on canonical `main` post-migration. The first
  AC.SFR.5 test (`test_AC_SFR_5_stranger_clone_byte_identical_to_pos_v2`)
  is RE-NAMED in body to assert byte-identity to `main` instead of
  `pos-v2` — actually, drop the `pos_v2` name; rename the test
  function to assert byte-identity of stranger-clone tree to
  canonical's HEAD on `main`.

**Test:** verified by the existing test files passing post-edit
(no new test file required — the existing tests ARE the AC). The
`test_no_sealed_amendments.py` seal-diff test catches any drift.

### AC.WBM2M.6 — Seal-diff hygiene (single-component fence)

Only `framework/workspace-bootstrap/` + universal admissions
(`docs/rebuild/plans/`, `CLAUDE.md`, `docs/odd-in-pos.md`,
`docs/odd-methodology.md`, `docs/rebuild/FUTURE_IDEAS.md`,
`docs/rebuild/STATE.md`, `docs/rebuild/FUTURE_IDEAS_DRAFT.md`)
appear in the seal-diff. Verified by:

- `framework/workspace-bootstrap/tests/test_no_sealed_amendments.py`
  at the manifest BASELINE.
- Every other sealed component's `test_no_sealed_amendments.py`
  sweep (zero changes outside their fence).

---

## §5 — Smoke (REALISTIC CONDITION — all 6 dimensions)

Per dispatch: HARD gate. If any dimension fails, halt.

- **D1 — cold-state:** fresh stranger clones `lukeivers/loam`
  (private; `git clone https://github.com/lukeivers/loam.git` into a
  fresh tmpdir, OR a local-equivalent: `git clone <canonical>` into
  a tmpdir away from any pos-v2 install). Run `loam init <workspace>`
  (or `pos-new-workspace <workspace>` directly) without `--from`
  (cwd-default-when-git-tree). Workspace appears with `framework/`,
  `workspace/`, `.claude/`. Anthropic-discovery + persona + skills +
  PM all wire correctly per the workspace's `<workspace>/.claude/`
  contents.
- **D2 — steady-state:** `bootstrap_new_workspace` re-run with
  `--init-existing` 5+ times on the same workspace. Idempotent —
  no mtime changes on workspace-state files.
- **D3 — restart:** workspace state survives pos-v2 process restart
  (e.g. kill memory-system service, restart, verify workspace still
  loads). Inherits AC.D.4 idempotency contract; no new behavior.
- **D4 — reboot:** workspace state survives macOS reboot equivalent
  (`launchctl unload` + `launchctl load` + verify). Inherits existing
  contract; verify by simulated reboot test.
- **D5 — cross-session:** the bootstrap-created workspace works
  after `/clear` (the ship-test). Verify by opening the workspace,
  doing a `/clear`, then asking the persona about something memorable
  from the bootstrap session — memory surfaces relevant content
  from the prior session.
- **D6 — telemetry-floor:** bootstrap operations log per the
  audit-trail floor (Decision P / SOC-2). Verify by tailing the
  audit-log dir under `<workspace>/workspace/.pos/audit-log/` after
  bootstrap and confirming entries.

**Smoke commands** (record in status file):

```
# D1 — cold-state stranger clone (uses tmpdir; never touches Luke's actual workspace)
TMPDIR=$(mktemp -d)
git clone /Users/lukeivers/ivers-corp-pos-v2 "$TMPDIR/stranger-clone"
cd "$TMPDIR/stranger-clone" && python -m loam.workspace_bootstrap.new_workspace "$TMPDIR/ws" --from "$TMPDIR/stranger-clone"
# verify framework branch == main:
git -C "$TMPDIR/ws/framework" rev-parse --abbrev-ref HEAD
# expected: main
```

If D1 fails the bootstrap entirely (clone error, scaffold error),
halt + surface. If D1 lands the workspace but on a wrong branch,
halt + surface — that's an AC failure, not a smoke marginal.

---

## §6 — Bookkeeping

### Per-cycle

- `loam amend apply` per cycle (NOT `git commit --amend`).
- Single semantic commit per cycle.

### Post-seal

1. Backfill seal SHA into:
   - `docs/rebuild/STATE.md` Change log (new dated entry).
   - `docs/rebuild/plans/eric-final-delivery-plan-2026-05-04.md` §2
     (follow-up amendment row under the migration entry).
   - `docs/rebuild/plans/v0-1-x-roadmap.md` §8 method-decision
     register (post-build SHA row, dated 2026-05-04).
2. Delete the legacy `loam:framework-only` ref on the remote
   (Luke's call; recommended within 24 h of seal):
   ```
   git push lukeivers/loam :framework-only
   # OR via gh api:
   gh api -X DELETE repos/lukeivers/loam/git/refs/heads/framework-only
   ```
   After deletion, `loam:main` is the only ref Eric (or any stranger)
   needs to clone.
3. **DO NOT push tags this amendment** (per dispatcher).

---

## §7 — Halt triggers

(Mirrors the dispatch.)

- WD drifts away from `/Users/lukeivers/ivers-corp-pos-v2/` → halt + surface.
- Plan-doc not authored before code → halt.
- Refactor surfaces a structural assumption beyond the 3 callsites +
  tests (e.g. a fourth callsite, a deeper test-conftest dependency,
  an MFBM-shape skill that hard-codes `framework-only`) → halt +
  surface (rescope or proceed depending on Luke's call).
- Smoke fails on D5 cross-session (the ship-test) → halt.
- Stranger-clone test fails (D1) → halt + surface.
- Any AC ships partial → halt + reframe.
- Wall-clock exceeds 5 hours → halt with partial findings + status
  file path.

---

## §8 — Method choices (builder's call per ODD §1.1)

Builder selects from the recommendations below; not load-bearing on
the AC contract. The method-decisions become observable once the
builder commits source edits:

1. **Constant naming.** Recommended `CANONICAL_BRANCH = "main"`.
   Alternative: drop the indirection entirely and inline the literal
   `"main"` at the 3 callsites. Builder's call.
2. **Materialise helper retention.** Recommended (a) keep + simplify
   (defensive, harmless no-op on the typical case). Alternative
   (b) remove entirely. See AC.WBM2M.3 discussion.
3. **Conftest fixture shape.** Recommended `git init --initial-branch=main`
   + write fixture files + commit; no second branch needed.
   Alternative: keep the function-shape but remove only the
   synthesis-tool import + manifest write (single-branch fixture
   on `pos-v2` keyword still valid, just rename to `main`).
4. **Test file renames.** Recommended: rename file BODY (test fn
   names + docstrings) but keep file paths (low-churn). Alternative:
   rename the AC.FBE.10 file to AC.WBM2M.2 file path. Builder's call.

---

## §9 — Risks + mitigations

| Risk | Mitigation |
|---|---|
| The conftest fixture rewrite breaks unrelated tests that rely on `framework-only` being available as a second branch | Audit all conftest-fixture consumers (`grep -r make_fixture_canonical framework/workspace-bootstrap/tests/`) before the rewrite; confirm none assert second-branch existence. If any do, halt + surface. |
| The `_materialise_framework_only_branch` helper rename surfaces a fourth callsite I missed | Pre-edit gate: `grep -rn 'FRAMEWORK_ONLY_BRANCH\|_materialise_framework_only_branch' framework/workspace-bootstrap/src/` MUST return only the 3 callsites named in §3. If 4+, halt + surface. |
| Stranger-clone's `main` is the LOCAL default (not just remote-tracking), so the materialise helper is a no-op — but a different fail mode might surface | AC.WBM2M.3 explicitly covers this; the test verifies the helper is idempotent on the existing-local-ref case. |
| The doubled-component contract (FBE.2c.5) breaks if `main`'s tree shape differs from `framework-only`'s | Pre-edit gate: confirm `framework/<comp>/` paths exist on canonical `main` HEAD (verified — same shape post-D-cutover; ad1e6bb HEAD has them). |
| Smoke D5 (cross-session) fails because bootstrap doesn't seed memory groups correctly under `main` shape | The cross-session contract is owned by memory-system + the workspace's `.pos/sync-config.yaml` — not by the branch name. AC.D.4.1 already verifies sync-config carries `canonical_source` correctly; this amendment doesn't change that. If D5 fails, the bug is upstream of this amendment. |
| Renaming the helper produces a public-API break for any caller importing `_materialise_framework_only_branch` from outside the module | The helper is module-private (leading underscore); no external callers. `grep -rn '_materialise_framework_only_branch' framework/ plugins/ docs/` confirms zero external callers pre-edit. |

---

## §10 — Estimated AI-time

Per the duration-estimation rubric:

- Plan + manifest authoring: 30 min (this doc + builder-plan + manifest).
- Source edit (constant + 3 callsites): 15–25 min.
- Conftest rewrite: 30–45 min (drop synthesis import + replace with
  direct git fixture; verify `make_fixture_canonical` consumers
  unbroken).
- Test updates (AC.FBE.10 → AC.WBM2M.2; AC.SFR.5 deletions; AC.D.4.1
  branch literal flip; etc.): 30–45 min.
- New AC test files (AC.WBM2M.{1,2,3,4} — 4 new tests): 30–45 min.
- Run + iterate test suite to green: 30–60 min (includes per-component
  seal-diff sweeps).
- `loam amend apply` per-cycle bookkeeping + manifest tweaks: 15 min.
- Smoke (D1 + D2 + D5 the load-bearing ones; D3/D4/D6 are existing
  contracts inherited): 30–45 min (D5 the longest).
- Backfill (STATE.md + eric-final + roadmap): 15 min.

**Total band: 3–5 h AI-time** (matches dispatch's 60–120 min build
+ ~30 min plan-doc band, plus contingency). Owner gate-review
separate.

---

## §11 — Closing summary

Single sealed-component amendment. Surface area: 1 source file +
1 conftest + ~5 test files + 4 new AC test files + 1 manifest +
this plan + builder-plan. Single-line semantic change at the
constant level; cascading byte-level changes through callsites,
conftest fixture, and AC tests. Quality bar: all 6 smoke
dimensions pass; no AC ships partial; framework-only literal
appears nowhere in active source post-seal. Post-seal cleanup
deletes the legacy `loam:framework-only` remote ref and backfills
seal SHAs into STATE.md + eric-final §2 + roadmap §8.

When this seals, the OSS dev-architecture migration is fully
complete: `loam:main` is the only ref Eric needs; the workspace-
bootstrap-as-shipped points at it; the `framework-only` branch is
gone from the public surface and from active code.
