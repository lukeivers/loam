# Single-framework restructure — `pos-new-workspace` + corpus-discovery readers

**Builder-plan.** Authored 2026-04-28 against canonical pos-v2 HEAD `39cfbb1`. Amendment number TBD (next free; currently #67 at the time of authoring, may drift if other amendments land first).

This plan addresses the path-doubling failure observed during pos3's D-cutover (commit `938b4c8`): `pos-new-workspace --from <canonical>` clones canonical wholesale into `<workspace>/framework/`, producing `<workspace>/framework/framework/<comp>/` (component paths doubled) and `<workspace>/framework/CLAUDE.md` (top-level docs nested one level deeper than the four corpus-discovery readers expect). The pos3 cutover patched it with relative symlinks at the workspace root; that patch is workspace-specific and does not survive into future fresh workspaces produced by the bootstrap.

The recommended structural fix per the companion research (`docs/rebuild/plans/research/single-framework-restructure-research.md`) is **Alternative 4 — subtree-split synthetic branch on canonical** plus **sub-option 4a — corpus-discovery readers fall through to `<workspace>/framework/`** when the workspace-root copy of the doc is absent.

**Status:** ready for owner ruling on D1–D7 (research §6) before dispatch to a build agent.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Companion research:** `docs/rebuild/plans/research/single-framework-restructure-research.md`.

---

## §0. Summary + named decisions

**Outcome.** After this amendment seals:

1. Canonical maintains a synthetic `framework-only` branch whose tree is canonical's `framework/` subdir promoted to repo root, plus the top-level docs (`CLAUDE.md`, `CLAUDE.dev.md`, `README.md`, `docs/`) carried verbatim into the synthetic-branch root. The synthesis is automated by a script invoked from a pre-push hook on canonical's `pos-v2` branch (or by hand via a Makefile target) such that every `pos-v2` commit produces a corresponding `framework-only` commit in lockstep.

2. `pos-new-workspace --from <canonical>` clones the `framework-only` branch (not canonical's default branch). Workspaces produced by the bootstrap have shape `<new-ws>/framework/<comp>/` (single level) plus `<new-ws>/framework/CLAUDE.md` etc.

3. The four corpus-discovery readers (`primary-persona/session_start_gate.py`, `hands-off-lifecycle/hooks/corpus_load_sentinel.py`, `tools/loam-mode/session_start.py`, plus the loam-mode-CLI / context_composer wiring as needed) probe `<workspace_root>/CLAUDE.md` first and fall through to `<workspace_root>/framework/CLAUDE.md` when the workspace-root copy is absent. Same pattern for `docs/odd-methodology.md`, `docs/rebuild/VALUE_PROPOSITION.md`, `docs/rebuild/STATE.md`, `docs/rebuild/FUTURE_IDEAS.md`, `docs/rebuild/dev-mode-manifest.yaml`, `CLAUDE.dev.md`, and the `docs/rebuild/plans/amendment-*.md` glob.

4. `pos-sync` is unchanged. The workspace's `<workspace>/framework/.git/` tracks `framework-only` as origin; `git fetch + git merge --ff-only` runs against `framework-only`'s HEAD. D.3's invariant holds.

5. pos3's existing root-level symlinks (`<pos3>/CLAUDE.md → framework/CLAUDE.md`, etc.) continue to work (the readers prefer the workspace-root path when present); pos3 may opt to delete them post-amendment as cosmetic cleanup.

**Named decisions (research §6 — pre-attached recommendations; each is the owner's call):**

1. **D1 — Adopt Alternative 4 (subtree-split synthetic `framework-only` branch)?** Recommendation: Yes.
2. **D2 — Alternative 5 (canonical-side restructure of `framework/<comp>/` to `<comp>/`) instead?** Recommendation: No.
3. **D3 — Reader fall-through (4a) vs bootstrap-time symlinks (4b)?** Recommendation: 4a.
4. **D4 — Synthesis pipeline implementation (subtree-split vs custom commit-tree script vs Makefile-only)?** Recommendation: Custom commit-tree script (~50–100 LOC python) invoked by pre-push hook + Makefile target.
5. **D5 — Reader fall-through preference (workspace-root vs framework-root)?** Recommendation: probe-and-prefer-workspace-root (handles future workspaces with workspace-specific overrides at workspace root).
6. **D6 — Apply on pos3 immediately, or only on future workspaces?** Recommendation: Both. Reader change unblocks pos3 simultaneously without touching its symlinks.
7. **D7 — Branch name for synthetic surface?** Recommendation: `framework-only`.

---

## §1. Acceptance criteria

The AC prefix for this amendment is `AC.SFR` (single-framework-restructure). All ACs are outcome-shaped per ODD §2; method (which file, which library, which test framework) is the builder's call. The behaviour-count check is in §2.

- **AC.SFR.1 — `pos-new-workspace --from <canonical>` produces a single-level framework directory.** When the operator runs `pos-new-workspace <new-ws> --from <canonical>` against a canonical repo that publishes a `framework-only` branch, the resulting workspace has shape `<new-ws>/framework/<comp>/` for every sealed component (no `<new-ws>/framework/framework/<comp>/` doubling). The workspace's `<new-ws>/framework/CLAUDE.md` is byte-identical to canonical's `framework-only`-branch `CLAUDE.md`. The workspace's `<new-ws>/framework/.git/` tracks `framework-only` as origin (so subsequent `pos-sync` operates against the synthetic branch).

- **AC.SFR.2 — Canonical publishes a `framework-only` branch in lockstep with the primary `pos-v2` branch.** A `framework-only` ref exists on canonical and points at a commit whose tree contains: (a) every entry under canonical's `framework/` subdir promoted to the synthetic-branch root (e.g. `framework/cost-governance/` → `cost-governance/`); (b) canonical's top-level docs (`CLAUDE.md`, `CLAUDE.dev.md`, `README.md`, `docs/...`) at the synthetic-branch root verbatim. After every advance of canonical's `pos-v2` branch, the `framework-only` branch advances to a corresponding new commit reflecting the changes.

- **AC.SFR.3 — Corpus-discovery readers find docs under `<workspace>/framework/` when absent at workspace root.** Each of the four readers (named in §3) probes the workspace-root path first (preserving today's behaviour for workspaces that have workspace-root docs); when absent, falls through to the corresponding `<workspace>/framework/<path>` location. The fall-through applies to: `CLAUDE.md`, `CLAUDE.dev.md`, `docs/odd-methodology.md`, `docs/odd-in-pos.md`, `docs/rebuild/VALUE_PROPOSITION.md`, `docs/rebuild/STATE.md`, `docs/rebuild/FUTURE_IDEAS.md`, `docs/rebuild/dev-mode-manifest.yaml`, and the `docs/rebuild/plans/amendment-*.md` glob.

- **AC.SFR.4 — `pos-sync` composition with the synthetic branch is unchanged from D.3's invariant.** A workspace produced by the post-restructure `pos-new-workspace` runs `pos-sync` (no args) and the operation completes via `git fetch + git merge --ff-only` against `framework-only`'s HEAD when the workspace's `framework/` tracks it. After `pos-sync`, every file under `<workspace>/framework/<rel>` is byte-identical to `framework-only`'s HEAD `<rel>`. Files under `<workspace>/workspace/` are byte-identical pre/post sync (D.3's HC#6 structural promise carried forward).

- **AC.SFR.5 — Stranger-clones-canonical property preserved.** `git clone <canonical-url>` (no `--branch` flag, no `--recurse-submodules`) produces a working tree byte-identical to canonical's primary `pos-v2` branch. No bootstrap script is required to make canonical browseable / clone-able. The `framework-only` branch is reachable via `git fetch origin framework-only` or `git clone --branch framework-only <canonical-url>` but is not required for canonical-side inspection.

- **AC.SFR.S — Seal-diff invariant.** The amendment's diff is confined to: (a) the named sealed components in §3 (workspace-bootstrap, primary-persona, hands-off-lifecycle, tools/loam-mode); (b) `framework/tools/<new-tool-or-existing-tool>/` for the synthesis pipeline (builder's call where it lands; tools fence is not sealed-component-shape); (c) `docs/rebuild/plans/single-framework-restructure*` artefacts; (d) universal admissions (manifests, baselines, plan docs). No edits to other sealed components.

---

## §2. Behaviour-count check (ODD §3.3 forward)

| AC | Behaviour |
|----|-----------|
| AC.SFR.1 | Bootstrap produces single-level `framework/<comp>/` shape from canonical's `framework-only` branch |
| AC.SFR.2 | Canonical maintains a `framework-only` branch in lockstep with `pos-v2` |
| AC.SFR.3 | Corpus-discovery readers fall through to `<workspace>/framework/` when workspace-root copy absent |
| AC.SFR.4 | `pos-sync` continues to operate via `git fetch + git merge --ff-only` against the synthetic branch |
| AC.SFR.5 | Strangers can `git clone <canonical-url>` without bootstrap script (the `pos-v2` branch is unchanged) |
| AC.SFR.S | Seal-diff fence honoured |

Six declared behaviours, six ACs. Forward check passes. Reverse check (every code edit / branch / test → backing AC) is the builder's responsibility at build time per ODD §2.5.

---

## §3. Component fence (multi-component sealed-amendment)

This amendment touches multiple sealed components plus a non-sealed tools-side surface. Sealed-component fence per HC#1; the manifest declares each component explicitly.

**Sealed components in scope (each gets a SEAL_COMMIT bump, manifest entry, allowed_prefixes admission):**

1. **`framework/workspace-bootstrap/`** — `new_workspace.py` change to clone the `framework-only` branch (added `--branch framework-only` to the `git clone` call; the URL/local-path discriminator is unchanged). Test additions exercise the post-restructure shape.

2. **`framework/primary-persona/`** — `session_start_gate.py` reader fall-through (`discover_baseline_corpus`, `enumerate_amendments_in_flight`). Test additions exercise both workspace-root-present and workspace-root-absent paths.

3. **`framework/hands-off-lifecycle/`** — `corpus_load_sentinel.py` reader fall-through (`compute_corpus_paths_required` reads `dev-mode-manifest.yaml`). Test additions.

4. **`framework/tools/loam-mode/`** — `session_start.py` reader fall-through (`emit_session_start_context` reads `CLAUDE.dev.md`). Test additions.

**Non-sealed (tools-side) in scope:**

5. **Synthesis pipeline location.** Builder's call. Three viable homes:
   - `framework/tools/pos-publish-framework-only/` (new tool; cleanest separation; ~100 LOC).
   - `framework/tools/pos-amend/` (extension; pos-amend already mediates canonical-side seal automation; reasonable home).
   - `framework/Makefile` or canonical-root `Makefile` (lightest weight; least structural).
   
   Recommendation surfaced for builder: NEW tool at `framework/tools/pos-publish-framework-only/` per the cleanest-separation principle, BUT explicitly the builder's call within the AC outcome bound. The synthesis tool's function is bounded (input: canonical repo + commit; output: synthesised commit on `framework-only`); it composes well with a pre-push hook.

6. **Pre-push hook** at `.git/hooks/pre-push` on canonical (NOT versioned by default; canonical-side install via a `make install-hooks` target). Canonical-side maintainer discipline.

**Out of scope (must NOT be edited):**
- Other sealed components (cost-governance, graceful-degradation, memory-system, objective-tracker, observability-aggregator, orchestrator, reversibility-primitive, safety-layer, scope-of-work, self-correction, self-upgrade, telegram-interface, workspace-sync).
- Existing canonical structure (`framework/<comp>/` layout on the `pos-v2` branch is unchanged — Alternative 5 was rejected per D2).
- pos3-side cleanup (the symlinks on pos3 are NOT touched; they continue to work; a separate cosmetic pos3 amendment may remove them later).

---

## §4. Hard constraints

- **HC#1 (fence).** Multi-component sealed-amendment fence; manifest names workspace-bootstrap, primary-persona, hands-off-lifecycle, loam-mode. Tools-side synthesis pipeline lands inside `framework/tools/`. No edits to other sealed components.
- **HC#2 (no regression).** Pre-amendment workspace-bootstrap, primary-persona, hands-off-lifecycle, loam-mode test suites pass post-amendment. New tests added for AC.SFR.1, AC.SFR.3, AC.SFR.4, AC.SFR.5.
- **HC#3 (no new third-party deps).** Synthesis pipeline + reader changes use stdlib only (`pathlib`, `subprocess`, `git` CLI calls). No new pyproject entries.
- **HC#4 (byte-content match).** Tests for AC.SFR.1 + AC.SFR.4 assert byte-identity between fixture-canonical's `framework-only`-branch contents and the cloned-workspace's `<workspace>/framework/<rel>` contents.
- **HC#5 (composition with pos-sync).** Tests for AC.SFR.4 exercise the full `pos-sync` flow against a fixture canonical that publishes a `framework-only` branch; verify `git fetch + git merge --ff-only` fast-forwards the workspace's `framework/` to the synthetic-branch HEAD.
- **HC#6 (structural promise carried forward).** D.2's `<workspace>/workspace/` structural-guard test is re-asserted: every workspace-state file lives under `<new-ws>/workspace/` exclusively (apart from `.claude/` per D-Q.A4). The post-restructure shape MUST NOT regress this.
- **HC#7 (CDC).** Scope-only-dispatch authored in this builder-plan. `pos-amend seal --plan-doc <abs-path>` backfills §14.
- **HC#8 (no `--amend`).** Corrective new commits only.
- **HC#9 (plan-before-code).** This plan exists; the manifest is committed alongside.
- **HC#10 (stranger-clones-canonical preserved).** Tests for AC.SFR.5 verify that a fresh clone of canonical's primary branch (the `pos-v2` branch) is byte-identical to today's tree shape; no bootstrap script needed.

---

## §5. Out of scope (explicit)

- Restructuring canonical's `framework/<comp>/` to `<comp>/` at canonical root (Alternative 5; rejected per D2).
- Migrating pos3's existing symlinks to a different shape; pos3 is unaffected by this amendment beyond the reader fall-through, which is additive.
- Adding a new corpus-discovery primitive (e.g. an `<workspace>/.pos/corpus.yaml` overrides file). The reader changes are minimal: workspace-root-first, framework-root-fall-through. No new config surface.
- Submodule-based packaging of canonical (Alternative 7; fails AC.SFR.5).
- Sparse-checkout-based bootstrap (Alternative 2; fails to eliminate the doubling).
- Two-clone composition (Alternative 1; breaks `pos-sync` doc-staleness).
- post-clone working-tree mutation (Alternative 3; breaks `pos-sync`).

---

## §6. Suggested implementation order (builder's call to refine)

This is advisory only per ODD §7.1 step 4. The builder may reorder, batch, or split steps as method-decision provided the ACs land.

1. Author the synthesis script (the one piece with no upstream dependencies). Land it at the chosen location (D4 recommendation: NEW `framework/tools/pos-publish-framework-only/`). Smoke-test against a fixture canonical: input = canonical repo + commit, output = synthetic commit on `framework-only` reachable via `git rev-parse framework-only`. Verify the synthetic tree contains the promoted framework contents + top-level docs.

2. Run the synthesis script against the actual canonical's current HEAD (`39cfbb1`) once, as a one-shot manual operation: produce the initial `framework-only` ref. Verify by `git ls-tree framework-only` (should show component dirs at root + CLAUDE.md + docs/ etc.).

3. Land the canonical-side pre-push hook (or Makefile target) that re-runs the synthesis on every `pos-v2` commit. Verify by making a no-op commit on canonical's `pos-v2`; verify `framework-only` advances correspondingly.

4. Update `pos-new-workspace` (`framework/workspace-bootstrap/src/workspace_bootstrap/new_workspace.py`) to pass `--branch framework-only` to the `git clone` call. Add the AC.SFR.1 test against a fixture canonical that publishes both a `pos-v2` branch and a `framework-only` branch.

5. Update the four corpus-discovery readers with workspace-root-first / framework-root-fall-through resolution. Order doesn't matter; each component is independent. Add per-reader tests exercising both paths.

6. Run the cross-component test sweep. Verify AC.SFR.1, AC.SFR.3, AC.SFR.4, AC.SFR.5, AC.SFR.S all pass.

7. `pos-amend apply` (after the amendment commit, before seal); `pos-amend seal --plan-doc <abs-path>` to land the seal commit + §14 backfill.

---

## §7. Halt-and-surface checklist (per dispatch)

The builder MUST halt and surface, not push through, when any of these fire:

1. **The synthesis script's commit-graph is unsound.** If the synthetic `framework-only` branch's parents/grafts produce a graph git refuses to `git merge --ff-only` against from the workspace side (e.g. unrelated histories), halt — the synthesis design needs revision before AC.SFR.4 can land.

2. **Reader fall-through breaks an existing test.** If updating any of the four readers causes a regression in the existing component test suite (e.g. a test that asserted `<workspace>/CLAUDE.md`-only behaviour), halt and surface — the existing AC may need re-extension per ODD §4.

3. **Sealed-component fence violation discovered during build.** If implementing the reader changes turns out to require touching another sealed component (e.g. `framework/orchestrator/` or `framework/tools/pos-amend/` because a hook calls into them), halt — the amendment's scope grew beyond what was authorised.

4. **Synthesis pipeline cannot run pre-push without authorisation that doesn't exist.** If the pre-push hook requires permissions or daemons not available on a stock developer machine (e.g. requires running a service, requires admin rights), halt and surface — the synthesis discipline must be invokable on the canonical-maintainer's local machine without ceremony.

5. **§2.5 violation observed in surrounding code.** If the existing reader code in any of the four target components contains code paths that satisfy no AC (per ODD §2.5), halt and surface — should this amendment's scope expand to scrub them, or should the plan author around them?

6. **Composition break with `pos-sync`.** If during AC.SFR.4 testing it turns out `git fetch + git merge --ff-only` against `framework-only` produces unexpected behaviour (non-fast-forward, conflicts on the synthetic-branch HEAD), halt — D.3's invariant is load-bearing; do not land an amendment that breaks it.

7. **Stranger-clones-canonical regression.** If the synthesis pipeline accidentally edits canonical's `pos-v2` branch (e.g. adds a `framework-only` synthesis-state file at canonical root), halt — AC.SFR.5 prohibits canonical-side regressions.

---

## §8. Empirical verification plan

**Pre-implementation:**
1. Read `framework/workspace-bootstrap/src/workspace_bootstrap/new_workspace.py` and the existing `test_pos_new_workspace.py` test fixture pattern (`make_fixture_canonical` in `conftest.py`).
2. Read each of the four reader modules end-to-end; identify the existing test files and the path-resolution call sites.

**Implementation tests (per builder, in addition to the §6 sequencing):**

- **AC.SFR.1 test (workspace-bootstrap):** extend `test_pos_new_workspace.py` with `test_AC_SFR_1_clone_framework_only_produces_single_level_framework`. Construct a fixture canonical with both `pos-v2` and `framework-only` branches; run `cli_main(["--from", str(fixture_canonical), str(fixture_new_ws)])`; assert `<fixture-new-ws>/framework/cost-governance/` exists; assert `<fixture-new-ws>/framework/framework/` does NOT exist.

- **AC.SFR.2 test (synthesis pipeline):** the synthesis tool's tests (location TBD per D4) exercise: input = canonical with N `pos-v2` commits; output = `framework-only` with N corresponding commits. Each `framework-only` commit's tree promotes `framework/<comp>/` to root + carries top-level docs.

- **AC.SFR.3 tests (per reader):** four parameterised tests exercising both branches of the fall-through (workspace-root present → uses workspace-root path; workspace-root absent → uses framework-root path). Each reader-component gets its own test file or test cases.

- **AC.SFR.4 test (workspace-sync composition):** a fixture canonical publishes both branches; the workspace is bootstrapped from `framework-only`; canonical advances `pos-v2` (synthesis re-runs and advances `framework-only`); `pos-sync` runs from the workspace; assert `git fetch + git merge --ff-only` succeeds; assert workspace's `framework/<rel>` byte-identical to `framework-only` HEAD.

- **AC.SFR.5 test (stranger-clones-canonical):** `git clone <canonical-as-fixture>` with no `--branch` and no `--recurse-submodules`; assert tree byte-identical to canonical's `pos-v2` branch (no synthesis-state files at canonical root).

**Pre-seal commit:**
- `pos-amend apply --dry-run docs/rebuild/plans/single-framework-restructure.manifest.yaml`. Expect green (no missing admissions).

**Amendment commit:**
- Single feat commit covering all §3 named components + the synthesis pipeline. Commit message names AC.SFR.1 through AC.SFR.5 + AC.SFR.S.

**`pos-amend apply` (real, after amendment commit, before seal):**
- Advances BASELINE + widens allowed_prefixes/allowed_files for the amendment commit's diff.

**Seal commit:**
- `pos-amend seal --plan-doc <abs-path-to-this-plan>` runs the cross-component sweep, advances each named component's SEAL_COMMIT sidecar, creates the seal commit, backfills §14.

---

## §9. Method-decision register (post-build)

The plan §0 left D-build.x method choices to the builder within the ACs' outcome bounds. This section is populated post-build per the seal-automation extension.

### D-build.x — (placeholder for the build agent's method choices)

(populated by builder)

### Test breakdown

(populated by builder)

### Backwards-compat verification

(populated by builder)

### Notable mid-build deviations

(populated by builder)

### Commit SHAs

(populated by `pos-amend seal --plan-doc <ABSOLUTE PATH-to-this-file>` after build, per the seal-automation extension. Pass an ABSOLUTE path to avoid the `Path.relative_to` crash documented at commit `75c4d73`. The amendment commit + apply chore + seal commit + plan-SHA backfill commit each appear here on completion.)

### Dependents cleared to dispatch

(populated by builder)

---

## §10. Halt-and-surface findings encountered during plan authoring

**1. Halt-trigger #3 (scope creep into canonical-side restructure) — surfaced explicitly.** The research considered Alternative 5 (rearrange canonical's own `framework/<comp>/` to `<comp>/` at canonical root). Alternative 5 produces the same workspace-side outcome as Alternative 4 but at a much higher one-time cost (touches every plan doc, manifest, fence configuration in the D-architecture's three months of work). Surfaced as decision D2 with recommendation: stay with Alternative 4. Halting is honoured by surfacing the choice rather than picking silently.

**2. The dispatch's path reference `framework/docs/rebuild/FUTURE_IDEAS_DRAFT.md` does not match canonical's tree shape.** Canonical's docs are at `docs/rebuild/FUTURE_IDEAS_DRAFT.md` (no `framework/` prefix). Additionally, the three D-cutover follow-on entries the dispatch references are NOT yet present in canonical's draft; they appear to have been captured pos3-side and not yet propagated. The research and plan proceed because the problem is self-evident from the canonical tree shape + pos3 commit `938b4c8`'s diff. **Surfaced for the dispatcher's awareness** but not blocking the plan: the dispatch's framing of the problem is precise enough to author against.

**3. The recommended reader change touches THREE sealed components plus one tools-side component.** The amendment's fence is multi-component, not single-component. This is supported by precedent (e.g. amendment #45 multi-contributor session-start was multi-component, amendment #66 D.5.5 was single-component but referenced multiple subsystems). The manifest must list all four explicitly. Surfaced as a structural note for the build agent.

**4. The synthesis pipeline runs on canonical-side.** It is operator-triggered (pre-push hook) or maintainer-triggered (`make publish-framework-only`). It does NOT run from a workspace; the workspace is read-only with respect to canonical-side state. The dispatch's working-directory constraint (canonical pos-v2 only) is honoured because the synthesis tool ITSELF lives in canonical (under `framework/tools/`); strangers cloning canonical can run it manually if they want to publish their own derivative `framework-only` branch (e.g. for a forked workspace bootstrap source).

**5. The amendment's blast radius for current workspaces is bounded.** pos3 (currently the only D-shape workspace) continues to function: its symlinks resolve to the framework copy; the new readers prefer the workspace-root path when present (which IS where the symlinks point); fall-through is invoked only on workspaces without the symlinks. This means the amendment can land + the change becomes effective for pos3 immediately + future fresh workspaces from `pos-new-workspace` get the structural fix natively.

---

## §14. Method-decision register (placeholder)

### Commit SHAs

(populated by `pos-amend seal --plan-doc <ABSOLUTE PATH>` after build per the seal-automation extension)

---

## §15. References

- CLAUDE.md (project + global) — design lenses + output conventions.
- `docs/odd-methodology.md`, `docs/odd-in-pos.md` — ODD methodology + in-pos examples (§5.1.1 relocate-vs-eliminate is the load-bearing rule for the recommendation).
- `docs/rebuild/VALUE_PROPOSITION.md`, `docs/rebuild/STATE.md`, `docs/rebuild/FUTURE_IDEAS.md`.
- `docs/rebuild/plans/research/single-framework-restructure-research.md` — companion research; the seven decisions D1–D7 originate there.
- `docs/rebuild/plans/d-migration-3.builder-plan.md` — D.3's `pos-sync = git fetch + git merge --ff-only` invariant (load-bearing for AC.SFR.4).
- `docs/rebuild/plans/d-migration-4.builder-plan.md` — D.4's `pos-new-workspace --from` definition (the primitive being modified).
- `docs/rebuild/plans/d-migration-1-5.builder-plan.md` — multi-component sealed-amendment manifest precedent.
- pos3 commit `938b4c8` — D-shape cutover; the symlink workaround being replaced by structural fix.
- `framework/workspace-bootstrap/src/workspace_bootstrap/new_workspace.py` — `pos-new-workspace` implementation (the bootstrap call site for AC.SFR.1).
- `framework/primary-persona/src/session_start_gate.py` — `discover_baseline_corpus` + `enumerate_amendments_in_flight` (AC.SFR.3 reader call sites).
- `framework/hands-off-lifecycle/hooks/corpus_load_sentinel.py` — `compute_corpus_paths_required` (AC.SFR.3 reader call site).
- `framework/tools/loam-mode/src/loam_mode/session_start.py` — `emit_session_start_context` (AC.SFR.3 reader call site).
- `framework/workspace-bootstrap/src/workspace_bootstrap/workspace_paths.py` — `WorkspaceLayout` structural-guard validator (HC#6 binding).
