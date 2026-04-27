# D-migration — strict directory-split workspace architecture (framework/ vs workspace/) — plan

Multi-amendment **migration plan** that retargets pos-v2's
single-flat-tree workspace shape to a **strict two-directory split**
(framework code under `framework/`; workspace state under
`workspace/`). Captures the full sequence (D.1 → D.5), the sealed-
component fence per amendment, the hard constraints, the named
decisions for owner ruling, and the halt-and-surface findings the
codebase read produced. Plan-before-code per the dev CDC.

**Status:** plan (pre-dispatch). 2026-04-27.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`
**Companions:**
- **Research note (D-D1 ruling on merits):**
  `docs/rebuild/plans/research/workspace-architecture-directory-split-2026-04-27.md`
  — six-question research; recommended D′; Luke ruled D over D′
  on merits 2026-04-27 (structural elimination > pattern relocation).
  This plan supersedes the research's "13-17 day" framing — that's
  a wall-clock estimate for human dev work; AI-builder time for
  the same surface is 1-2h delta D vs D′, negligible.
- **First-principles analysis (the "why"):**
  `/Users/lukeivers/pos3/.scratch/claude-output/workspace-sync-first-principles-2026-04-27.md`
  — bug-class analysis that triggered the architectural review.
- **Architecture being migrated FROM:**
  - `docs/rebuild/plans/workspace-sync.md` (#56 — keystone B-mode)
  - `docs/rebuild/plans/workspace-sync-resolver-cost-overhaul.md` (#57 — α NN fast-path)
  - `docs/rebuild/plans/workspace-sync-alpha-hotfix.md` (#59 — α-hotfix #1)
  - `docs/rebuild/plans/workspace-sync-alpha-hotfix-2.md` (#60 — α-hotfix #2)
- **Spec anchors:** `docs/rebuild/VALUE_PROPOSITION.md` (AC.PO.1 +
  AC.PO.2 — the prime objective). `docs/odd-methodology.md` §2.5
  + §5.3 (structural enforcement).
- **Amendment precedents:** #46 (multi-component plan-shape with
  §14 method-decision register; multi-component sealed-component
  amendment is the shape D.1 + D.2 use). #47 (single-sealed-
  component manifest + plan-doc shape; D.3 / D.4 baseline). #54
  (heavy-b-migrate sealed-floor-rebase precedent — relevant if
  D.1 ends up needing it).
- **Vars-file (rendered companion):**
  `docs/rebuild/plans/d-migration.vars.yaml` — top-level
  variables for any future template render of this plan or
  per-amendment dispatches.

**Ancestor record:**
- **Owner ruling 2026-04-27 (locked):** D-D1 = strict D over D′ on
  merits. D-D2 = flat→directory-split target structure (framework/
  + workspace/). D-D3 = `pos-sync` becomes `git fetch + merge --ff-
  only` against `framework/`; LLM-resolver retained as rare-conflict
  fallback. D-D4 = β.2 absorbs into D's migration sequence as
  `pos-new-workspace --from <repo>`. D-D5 = β.3 (global install)
  unchanged, independent amendment.
- **Bug pattern 2026-04-26 / 2026-04-27:** four α-hotfix
  amendments in two weeks (#56→#57→#59→#60), every bug the same
  fault-class — verdict-set-without-content-staged. The
  research (companion above) traced it to architectural
  fragility, not local code defects.
- **Recent precedent for multi-component sealed-component
  amendments:** amendment #46 (primary-persona +
  hands-off-lifecycle co-amended for SessionStart/UserPromptSubmit
  emitter wiring). The pattern fits D.1 + D.2.
- **Recent precedent for cross-component file moves under
  amendment cycles:** amendment #54's heavy-b-migrate run
  (sealed-floor-rebase machinery exists; if needed for D.1, it's
  battle-tested). D.1's atomic move probably *doesn't* need it
  per this plan's analysis (§5 Q3 trade-off — atomic-with-feature-
  flag is feasible without `heavy-b-migrate` because the moves
  are deterministic + tooling-discoverable), but it's a fallback
  if mid-amendment surprises emerge.

**Research:** Two research artefacts ladder up to this plan:
1. `docs/rebuild/plans/research/workspace-architecture-directory-split-2026-04-27.md`
   — Q1-Q6 trade-off analysis, recommended D′. The recommendation
   was overruled by Luke 2026-04-27 on merits (D's structural
   elimination compounds; D′'s pattern relocation does not). The
   research's structural findings carry forward; only the
   D-vs-D′ rec is overridden.
2. `/Users/lukeivers/pos3/.scratch/claude-output/workspace-sync-first-principles-2026-04-27.md`
   — bug-class first-principles. Carries forward in full — D's
   architectural shape is the realisation of the
   first-principles proposal.

---

## 1. Summary / TLDR

**The shape that's coming.** Five amendments (D.1–D.5) migrate pos-v2
from a flat-tree workspace where framework code and workspace state
intermingle at the workspace root, to a strict two-directory split:

```
~/pos3/                          # (and analogous structure for canonical pos-v2)
  framework/                     # git-tracked, pulled from canonical
    primary-persona/
    orchestrator/
    workspace-sync/
    self-upgrade/
    workspace-bootstrap/
    memory-system/
    objective-tracker/
    hands-off-lifecycle/
    tools/
    docs/
    scope-of-work/
    safety-layer/
    reversibility-primitive/
    cost-governance/
    self-correction/
    graceful-degradation/
    observability-aggregator/
    telegram-interface/
    first-run-inventory.yaml
    .gitignore
    pyproject + lock files
    CLAUDE.md (canonical's project CLAUDE.md)
    ...
  workspace/                     # workspace-local state, NEVER pulled, gitignored at framework's level
    .pos/
    personas/
    .mcp.json
    .scratch/
    memory.yaml
    objective_tracker.sqlite
    orchestrator.{out,err}.log
    memory-write-worker.{out,err}.log
    .venv/                       # shared workspace venv (per-workspace; never canonical's)
    data/
  .claude/                       # workspace root — Claude Code expects here (D-Q.A4)
    settings.json
    agents/
```

**Why D over D′ (Luke 2026-04-27, on merits).** D′'s `.gitignore`-
based protection is *pattern-maintenance* — every new workspace-state
file requires a developer to add a gitignore entry, and forgetting
one is silently dangerous. D's directory split is *structural
construction* — workspace state can't accidentally land in
`framework/` because the directory boundary is the contract; a
developer trying to write workspace state into `framework/` writes
to a git-tracked tree and is caught at the next sync. D collapses
the entire bug class by structure; D′ relocates it to a different
maintenance discipline. Architectural cleanliness compounds.

**The five amendments.**

| # | Amendment | Shape | Sealed-component scope | Wall-time est. (AI-builder) |
|---|-----------|-------|------------------------|------------------------------|
| D.1 | Directory restructure on canonical pos-v2 | **multi-component sealed amendment** (every component touched: `framework/<name>/` move + canonical-side dev tooling path updates) | every component has a moved seal-test sidecar — handle via `heavy-b-migrate` if surprises emerge, else atomic with config-flag (see §10 D-1 build-shape) | 4-6h |
| D.2 | Workspace-state directory established (`<workspace>/workspace/`) + workspace-bootstrap scaffolds there + plist EnvironmentVariables updated | **multi-component sealed amendment** (workspace-bootstrap + hands-off-lifecycle + workspace-sync; `.claude/` placement decision in D-Q.A4) | 3-4h |
| D.3 | `pos-sync` becomes `git fetch + git merge --ff-only` against `framework/`; LLM-resolver kept as rare-conflict fallback | **single-sealed-component amendment** (workspace-sync only; massive LOC drop ~2400 LOC retired, ~110 tests retired) | 3-4h |
| D.4 | `pos-new-workspace --from <repo>` console-script (β.2 absorbed); subsumes new-workspace bootstrap | **single-sealed-component amendment** (workspace-bootstrap only; new console_script; new `pos init` shape) | 2-3h |
| D.5 | Cleanup of dead code from old workspace-sync mechanism (optional; plan-author classifies needed/not-needed at end of D.3 build) | **single-sealed-component amendment** (workspace-sync only) | 1-2h |

**Total wall-time estimate (AI-builder, sequential):** **13-19h**
across 5 amendments. (Per Luke's duration-estimation rubric:
each amendment is "moderate-surface multi-file edit + tests";
calibration multiplier ~1.3× over raw tool-call count given the
cross-component coupling.)

**The structural promise (HC#6).** Post-migration, it must be
**impossible** to accidentally write workspace-state into `framework/`
or framework code into `workspace/`. The directory boundary is the
structural contract enforced by:

1. `framework/.gitignore` does NOT include `.pos/`, `personas/`,
   `memory.yaml`, etc. — those names simply do not exist inside
   `framework/`. A bug that wrote `.pos/` inside `framework/` would
   be caught by the next `git status` (untracked-file surface).
2. `<workspace>/.gitignore` (the parent gitignore at workspace root)
   declares `framework/` as the ONLY git-tracked subdirectory. Any
   workspace-state file lands in `workspace/` (or workspace root
   for `.claude/`) and is structurally outside the
   git-tracked-subtree. Sync simply doesn't see it.
3. Components that historically read `<workspace>/<file>` for
   workspace state now read `<workspace>/workspace/<file>` (or for
   `.claude/`, `<workspace>/.claude/<file>`). The lookup path
   itself enforces the class.

**Decision-shape tightness.** The dispatch surfaces D-D1..D-D5 as
LOCKED. This plan exposes only **outcome-shape** decisions for owner
ruling (per dispatch instruction: "Surface only outcome-shape
choices"); method-shape (which exact files, which test functions,
which exact AC numbering) is the builder's call inside each
amendment's locked outcome bound. Owner-ruling decisions in §11.

**Bundle splitting / ordering.** D.1 → D.2 → D.3 → D.4 → D.5,
sequential. Same-tree-serialize per
`feedback_serialize_amendment_builds`. Each amendment lands its
own commit + seal commit pair. Methods may use `pos-amend apply`
+ `pos-amend seal --plan-doc` per the amendment-#46/#47 precedent.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)

This migration binds to **VALUE_PROPOSITION's AC.PO.1
(translation-burden absorption) + AC.PO.2 (toolkit-primitive
growth)** as the prime spec hooks. Per
`feedback_value_proposition_as_prime_objective` (CLAUDE.md §2.5),
AC.PO.1 / AC.PO.2 are the prime objective's ACs and every
component/feature/amendment ladders up.

**Reverse trace per CLAUDE.md §2.5.** Every AC across D.1–D.5
traces back to the spec lines above + maps forward to AC.PO.1
and/or AC.PO.2:

- **AC.PO.1 (translation-burden):**
  - **D.1–D.2**: the operator's workspace tree is now legible at
    `ls`. A new contributor (or future-Luke) sees `framework/` +
    `workspace/` and immediately knows which is which without
    reading `.gitignore` or `sync-protected.yaml`. The persona
    no longer has to translate "is this workspace state or
    framework code?" because the directory tells them.
  - **D.3**: `pos-sync` becomes a thin wrapper around git, which
    is universally understood. The operator who says "pull the
    latest" gets git's merge mechanics underneath; on conflict,
    they can use `git status` / `git log` directly. Translation
    burden drops to "git knowledge" which most developers have.
  - **D.4**: `pos-new-workspace --from <repo>` is one verb that
    composes with the two-directory structure. Current β.2
    plan's bootstrap UX simplifies because the structure does
    half the work.

- **AC.PO.2 (toolkit-primitive growth):**
  - **D.1–D.2**: adds the **two-directory contract** as a new
    primitive. Future plug-ins, future workspace-shaped tooling,
    future multi-framework workspaces all compose against the
    same contract.
  - **D.3**: surfaces **git** as the framework-pull primitive.
    Future amendments compose on git's mature surface (branches,
    rebases, tags, reflog, `git bisect`, `git blame`, hooks)
    instead of re-implementing slices of it.
  - **D.4**: `pos-new-workspace` is a new toolkit primitive the
    primary persona invokes when the user asks for a new
    workspace. Composes with D.5's eventual `pos-amend
    template` family + B.3's global `pos` binary.

**No new top-level objective is required.** This is method-shape
realignment of the existing self-upgrade + workspace-sync
objectives, not a new outcome axis. The bug-class collapse the
research named is a *means* to AC.PO.1 + AC.PO.2's ends.

**Halt note.** Plan author considered whether D's architectural
re-shape constitutes a new top-level objective. It doesn't —
the *outcome* (workspaces stay in sync with canonical without
losing state) is unchanged from #56's keystone objective. D
re-implements that objective on a different mechanism (git +
directory split) instead of the bespoke resolve→stage→apply
pipeline. **Halt trigger 1 does not fire** — flagged in §13 with
reasoning so owner can override if they read it differently.

---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude leverage

Composes on Claude-native primitives without inventing new ones,
and shifts pos-v2 onto a more-leveraged underlying primitive (git):

1. **Git as the substrate.** Most syncs are fast-forwards;
   git's merge mechanics handle Class-B (operator-prefers-X) via
   `.gitattributes` `merge=ours`; Class-C (operator-edited
   framework code) genuinely-conflicting hunks are the only case
   the LLM-resolver fires. This shifts ~80% of workspace-sync's
   work onto git, which is mature, well-audited, well-understood
   by every developer, and well-understood by Claude (Claude
   reads + writes git via the standard tools). The net Claude-
   leverage gain is significant: the LLM-resolver budget shrinks
   to "rare conflicts only," freeing the resolver-budget envelope
   for other Claude-mediated work.
2. **Claude Code's git-aware tooling.** Claude has native git
   awareness (the user prompt + system reminders carry git status
   today). The two-directory split makes Claude's git-status
   reasoning more accurate — `git status` inside `framework/`
   is the framework-tracking view; `git status` inside
   `<workspace>/` (root) is the workspace-state view. The two
   views are no longer entangled in one tree's noisy `git status`.
3. **Workspace-bootstrap's existing scaffold pattern.** D.4's
   `pos-new-workspace --from <repo>` composes on workspace-
   bootstrap's existing scaffold logic (already battle-tested
   per amendments #28, #36, #39, #47). The new shape is "git
   clone <repo> <new-ws>/framework/ && pos init <new-ws>" — the
   `pos init` invokes the existing scaffold against the now-
   established `<new-ws>/workspace/` location.
4. **Claude SDK structured-output (preserved as fallback).** The
   workspace-sync LLM-resolver (clause-(h) machinery + α-hotfix-2's
   centralized staging) is preserved as the rare-conflict
   fallback. When git produces unresolvable Class-C hunks, the
   resolver receives the conflicted-hunk content (via `git
   diff`-shaped input), produces structured output (via the
   existing `MergeVerdict` Pydantic shape), and applies via
   `git add` + `git commit -m '<resolver-summary>'`. Same Claude
   SDK surface; just invoked rarely.

**No new top-level Claude SDK surface.** No new MCP server. No new
hook event. The leverage gain is *more* of git, *less* of bespoke
mechanism.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** Reduces translation burden across multiple
axes:

- **"Is this workspace state or framework code?"** — Pre-D, the
  persona had to consult `sync-protected.yaml`'s framework_floor
  to answer. Post-D, the persona answers from the path itself:
  `framework/<...>` = code; `workspace/<...>` (or `.claude/`) =
  state. **Pass.**
- **"How do I sync this workspace?"** — Pre-D, the persona ran
  `pos-sync` and translated the bespoke audit. Post-D, the
  persona runs `pos-sync` (which internally is `cd framework &&
  git fetch + git merge --ff-only`); on the rare conflict, the
  persona surfaces `git status` directly to the user (or invokes
  the LLM-resolver fallback). The translation simplifies because
  git is universally understood. **Pass.**
- **"How do I create a new workspace from this repo?"** — Pre-D,
  the persona ran `pos new-workspace` (β.2-shaped, not yet
  implemented). Post-D, the persona runs `pos-new-workspace
  --from <repo>` which is `git clone <repo> <new-ws>/framework/
  && pos init <new-ws>`. **Pass.**

**Harness test.** Adds three primitives to the toolkit:

1. **Two-directory contract** as the structural workspace shape.
   Future tooling (workspace-export, workspace-clone, plan-doc
   semantic-compare, plugin-install, etc.) compose against the
   same contract.
2. **Git-as-framework-pull-primitive.** Future amendments to
   workspace-sync compose against git's mature surface (which
   has decades of audit behind it). Future tools that want
   "atomic apply with reversibility" can lean on `git stash` /
   `git reset --hard` instead of re-implementing the staging
   tree.
3. **`pos-new-workspace` console-script.** A new toolkit verb
   the persona invokes for the "create a new workspace" intent.
   Composes with D.5's eventual `pos-amend template` family +
   the planned β.3 global `pos` binary.

**Pass on both tests.**

### Lens 3 — ODD authoring

Each of D.1–D.5 has outcome-shaped acceptance criteria (§4); each
AC names a state of the world the amendment must make true, with
deterministic test shape. **Method-shape choices** (e.g. exact
file moves, exact `git mv` invocation order, which feature-flag
mechanism for the discovery-code transition, exact `git
fetch`/`merge --ff-only` shellout vs `pygit2` Python binding)
are the builder's call inside each AC's outcome bound — captured
in each amendment's builder-plan and §14 method-decision
register.

Behaviour-count check applied per amendment in §5.

ODD §2.5 reverse trace is the builder's pre-seal check captured
in each amendment's builder-plan (one row per code path → AC).

Halt-and-surface triggers per §10; explicit per
`feedback_subagent_odd_violation_halt`.

---

## 4. Acceptance criteria (per amendment)

Outcome-shape only. Method-shape decisions are the builder's
call inside each amendment's locked outcome bound. Each AC
includes the deterministic test shape; method (exact test name,
exact assertion mechanism) is the builder's call.

### Amendment D.1 — Directory restructure on canonical pos-v2

**Objective.** Move all framework component directories under a
new top-level `framework/` directory in canonical pos-v2's tree.
Update component pyproject paths, plist templates, scaffold
templates, and editable-install discovery code so the workspace
operates correctly from the new location. This amendment lands
in canonical first; downstream workspaces (pos3) absorb via
later amendments after D.3.

**AC.D.1.1 — Directory move complete.** All 17 framework
components (`primary-persona`, `orchestrator`, `workspace-sync`,
`self-upgrade`, `workspace-bootstrap`, `memory-system`,
`objective-tracker`, `hands-off-lifecycle`, `tools`,
`scope-of-work`, `safety-layer`, `reversibility-primitive`,
`cost-governance`, `self-correction`, `graceful-degradation`,
`observability-aggregator`, `telegram-interface`) plus
`first-run-inventory.yaml`, `docs/`, and the canonical-side
configuration files are present at `<canonical-root>/framework/<name>/`.
The pre-existing top-level paths no longer exist (verified via
`ls`-equivalent).

**Verification.** A test in `tools/heavy-b-migrate/tests/` (or
the per-amendment seal-diff test, builder's call) asserts (a)
`framework/<name>/pyproject.toml` exists for every component,
(b) `<name>/pyproject.toml` does not exist at canonical root,
(c) `git ls-files framework/` returns the expected file count
within ±2 of pre-migration `git ls-files | grep -v ^framework/
| wc -l`.

**AC.D.1.2 — Editable-install topology preserved post-move.**
After the move, `hands-off-lifecycle/hooks/first_run_helper.py`'s
`_discover_components(pos_v2_root)` walks
`<pos_v2_root>/framework/` (not `<pos_v2_root>/`) and returns
the same 12 shared-venv components + 1 dedicated-venv component
(`memory-system`) the pre-migration code returned. The
topological sort produces the same DAG ordering. Editable
installs still resolve `import scope_of_work`, `import
primary_persona`, etc., in the shared `.venv`.

**Verification.** A test in
`hands-off-lifecycle/tests/test_first_run_helper.py` constructs
a fixture pos-v2 tree with the new `framework/` layout, invokes
`_discover_components` + `_topological_order`, and asserts the
returned component list + ordering matches pre-migration
expectations. A second test (HC#5 binding — empirical) runs a
full first-run scaffold against a fresh-clone fixture and
asserts every editable install lands; `import scope_of_work`
+ all sibling-component imports succeed.

**AC.D.1.3 — Plist templates + .claude/settings.json point at the
new framework paths.** All plist templates in
`workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py`'s
`_LAUNCHD_TEMPLATES` reference `{workspace}/framework/<...>` for
framework-code paths (e.g. `{workspace}/framework/memory-system/.venv/bin/python`,
`{workspace}/.venv/bin/python` stays as-is for the shared workspace
venv since it's a workspace artefact). The orchestrator-script
hook in `.claude/settings.json` references
`/<workspace-root>/framework/orchestrator/scripts/pos_session_start.py`
post-D.1 (test exercises this against a fixture).

**Verification.** A test in
`workspace-bootstrap/tests/test_first_run_scaffold.py` invokes
`_LAUNCHD_TEMPLATES["memory-graphiti"].format(...)` against a
fixture workspace, parses the result, and asserts the
`<string>{workspace}/framework/memory-system/.venv/bin/python</string>`
literal appears (after substitution, it's
`<string><fixture-ws>/framework/memory-system/.venv/bin/python</string>`).
Same shape for orchestrator + memory-write-worker plists.

**AC.D.1.4 — Canonical-side dev workflow continues to function.**
The canonical pos-v2 maintainer (Luke) can run `pytest`, run
`pos-amend apply`, run `pos-amend seal`, run `loam-mode`, and run
all dev tooling against `<canonical-root>/framework/` paths. The
canonical-side `.claude/settings.json` SessionStart hook references
`<canonical-root>/framework/hands-off-lifecycle/hooks/first-run.sh`
post-migration (or — per D-Q.A4 ruling — the canonical's
`.claude/` may stay at canonical root with paths updated).

**Verification.** A test in `tools/heavy-b-migrate/tests/`
asserts that a fresh-clone of canonical pos-v2 + first-run +
`pytest` (smoke subset across each component) produces a green
result post-D.1. Also: an end-to-end test (or operator-confirmed
manual check captured in the seal narrative) that running
`pos-amend apply --dry-run` against an in-flight amendment
manifest works on the new tree.

**AC.D.1.5 — `git diff` content-match for representative
component files post-move.** For three representative components
(scope-of-work — leaf; primary-persona — mid-graph;
workspace-bootstrap — high-fan-in), a diff of every Python
source file's content between `<framework/<component>/src/...>`
post-move and `<component>/src/...>` pre-move is empty.
**HC#4 binding — byte-content-match.**

**Verification.** A test runs `git show
<pre-migration-sha>:<component>/<file>` and `cmp` against
`<framework/<component>/<file>`'s content for ≥3 components ×
≥5 files each. Empty diff = test passes.

**AC.D.1.S — Seal-diff invariant.** Diff between BASELINE and
SEAL_COMMIT is confined to (a) the `framework/<component>/` move
(all 17 components), (b) updates to `first_run_helper.py`
discovery code, (c) updates to `_LAUNCHD_TEMPLATES` and any
analogous canonical-side plist templates, (d) `.claude/settings.json`
path updates (canonical's, if D-Q.A4 lands `.claude/` at
canonical root post-D.1), (e) seal-test BASELINE bumps + SEAL_COMMIT
sidecar updates for every touched sealed component, (f)
amendment-universal admissions (`docs/rebuild/plans/`).

**Verification.** Seal-diff test exercises `BASELINE..SEAL_COMMIT`
for the multi-component window. **Note:** because EVERY sealed
component is touched by D.1 (its sidecar + seal-test moves to
`framework/<component>/tests/`), this is a **multi-component
sealed amendment** at scale. The `pos-amend seal --scoped-sweep`
mechanism scales (verified via amendment #46 multi-component
precedent).

### Amendment D.2 — Workspace-state directory established (`<workspace>/workspace/`)

**Objective.** Establish `<workspace>/workspace/` as the canonical
location for `.pos/`, `personas/`, `memory.yaml`,
`objective_tracker.sqlite`, `orchestrator.{out,err}.log`,
`memory-write-worker.{out,err}.log`, `data/`, `.scratch/`, and
the shared `.venv/`. Update workspace-bootstrap's scaffold to seed
there. Update `.claude/settings.json` template paths in
workspace-bootstrap. Update plist EnvironmentVariables to use the
new paths. Decide `.claude/` placement (D-Q.A4 — likely at
workspace root, since Claude Code expects it there).

**AC.D.2.1 — workspace-bootstrap scaffolds workspace state at
`<workspace>/workspace/`.** A fresh-clone first-run produces
`<workspace>/workspace/.pos/`, `<workspace>/workspace/personas/`,
`<workspace>/workspace/memory.yaml`,
`<workspace>/workspace/.scratch/`, etc. The pre-D.2 paths
(`<workspace>/.pos/`, `<workspace>/personas/`, etc.) are no longer
created.

**Verification.** A test in
`workspace-bootstrap/tests/test_first_run_scaffold.py` runs the
scaffold against a fixture fresh-clone workspace and asserts the
workspace-state files land at `<fixture-ws>/workspace/<...>`.
Pre-D.2 pathnames are not created (verified via `not
(<fixture-ws> / <pre-D2-name>).exists()`).

**AC.D.2.2 — `<workspace>/.claude/` location preserved at workspace
root (D-Q.A4 — pending owner ruling).** Per Claude Code's
expectation, `.claude/settings.json` lives at `<workspace>/.claude/`,
NOT at `<workspace>/workspace/.claude/`. workspace-bootstrap
scaffolds `.claude/settings.json` and `.claude/agents/` at
workspace root.

**Verification.** A test in
`workspace-bootstrap/tests/test_first_run_scaffold.py` asserts
the scaffold writes `<fixture-ws>/.claude/settings.json` and
`<fixture-ws>/.claude/agents/` (not under `workspace/`).

**AC.D.2.3 — Plist EnvironmentVariables reference new paths.**
The orchestrator + memory-graphiti + memory-write-worker plists'
`EnvironmentVariables` sections reference
`<workspace>/workspace/<...>` for workspace-state paths
(StandardOutPath, StandardErrorPath, WorkingDirectory for orchestrator,
POS_V2_WORKSPACE_ROOT — though the latter retains semantics: it's
the workspace ROOT, not `<workspace>/workspace/`).

**Verification.** A test in
`workspace-bootstrap/tests/test_first_run_scaffold.py`
substitutes the templates and asserts plist content has
`<workspace>/workspace/orchestrator.out.log` (not
`<workspace>/orchestrator.out.log`) for the orchestrator's
StandardOutPath.

**AC.D.2.4 — Workspace-state migration script for in-place
upgrades.** A migration script (lands inside `self-upgrade/` or
`workspace-bootstrap/` per builder's call) detects an existing
flat-tree workspace at upgrade time and moves
`.pos/` → `workspace/.pos/`, etc. The script is idempotent
(running it twice produces no further moves) and atomic (an
interrupted move resumes correctly via the atomic-rename
+ pre-condition-check pattern).

**Verification.** A test exercises the migration script against
a fixture flat-tree workspace and asserts (a) all workspace-state
files land at the new paths, (b) zero pre-D.2 paths remain, (c)
all file content is byte-identical pre/post (HC#4 binding —
byte-content-match).

**AC.D.2.5 — `pos3` real-apply verification.** After D.1 + D.2
land, primary persona runs the migration against pos3. Assertion:
zero workspace-state file content changes (every file's content
matches pre-migration byte-for-byte); zero workspace-state file
losses; first-run after migration produces a green session.
**HC#5 binding — empirical end-to-end.**

**Verification.** Recorded in the D.2 amendment's seal narrative
as the operator-confirmed empirical run. The migration script's
test in AC.D.2.4 exercises the same machinery on a fixture; the
pos3 run is the live verification.

**AC.D.2.S — Seal-diff invariant.** Diff between BASELINE and
SEAL_COMMIT is confined to (a) `workspace-bootstrap/`,
(b) `hands-off-lifecycle/`, (c) `workspace-sync/sync_protected.py`
+ `framework_floor` patterns updates, (d) `self-upgrade/` (if
the migration script lives there), (e) seal-test BASELINE bumps
+ SEAL_COMMIT sidecar updates for every touched sealed
component, (f) universal-paths admissions.

### Amendment D.3 — `pos-sync` becomes git-merge

**Objective.** Replace workspace-sync's bespoke resolve→stage→apply
pipeline with `git fetch + git merge --ff-only` against
`framework/`. Keep workspace-sync's LLM-resolver as the
rare-conflict fallback path only. Audit log derives from `git
log` + LLM-resolver-output. Drop the entire staging
infrastructure (`staging.py`'s `stage_canonical_clean_writes`,
`stage_resolved_content`, `apply_staging_atomically`,
`discard_staging`); drop the bespoke conflict-detection (NN
ancestor-detection in `ancestor_detection.py`); drop most of
`merge_helper.py` (~700 LOC); drop the bulk of
`conflict_detection.py` (~600 LOC).

**AC.D.3.1 — `pos-sync` invokes `git fetch` against the canonical
remote configured per `<workspace>/.pos/sync-config.yaml`'s
`canonical_source:`.** When the resolved canonical source is a
URL, the existing `~/.pos/canonical-cache/<repo-id>/` mechanism
fetches there (ensuring the cache clone is fresh); the workspace's
`framework/` git-remote is configured to track that cache clone
(or the URL directly, builder's call). When the resolved source
is an absolute POSIX path, the workspace's `framework/` git-remote
points there directly.

**Verification.** A test in
`workspace-sync/tests/test_cli_d_shape.py` (new file; method
shape per builder) constructs a fixture workspace + canonical-as-
local-clone, runs `cli.main` (the new CLI), and asserts the
workspace's `framework/.git/refs/remotes/canonical/HEAD`
advances post-fetch.

**AC.D.3.2 — `pos-sync` runs `git merge --ff-only
<remote>/<branch>` and exits 0 on success.** When the workspace's
`framework/` is strictly behind the canonical remote (most syncs
are this shape), the merge is a fast-forward; the workspace's
`framework/HEAD` advances; no merge commit is created;
`pos-sync` exits 0 with a structured summary.

**Verification.** A test in `workspace-sync/tests/test_cli_d_shape.py`
runs the fast-forward case end-to-end and asserts (a)
`framework/HEAD` advances, (b) the CLI exits 0, (c) the audit
output (per AC.D.3.5) carries the expected fast-forward summary.

**AC.D.3.3 — On non-fast-forward, `pos-sync` runs `git merge` with
the merge driver; on remaining unresolved conflicts, hands off to
the LLM-resolver fallback.** When the workspace has its own
commits on `framework/<branch>` (e.g. operator edited
`primary-persona/cli.py` locally), `git merge --ff-only` fails;
the CLI falls back to `git merge` (which uses
`framework/.gitattributes`'s `merge=ours` driver for Class-B
paths). Remaining conflicts (Class-C: both sides changed)
get handed to the existing `MergeResolver` (LLM-mediated); the
resolver produces resolved content; the CLI applies via `git
add` + `git commit -m '<resolver-summary>'`.

**Verification.** A test in `workspace-sync/tests/test_cli_d_shape.py`
constructs a fixture with conflicting Class-C content (operator-
edited file + canonical edit), stubs the resolver, runs the CLI,
and asserts the conflict resolves via the resolver and the
resulting `git log` shows a merge commit with the resolver's
summary.

**AC.D.3.4 — Class-A protection is structural.** The fixture
test (and operator-confirmed pos3 run, HC#5) confirms that
files under `<workspace>/workspace/` (`.pos/`, `personas/`,
etc.) are never modified by `pos-sync` regardless of canonical
state. **The directory boundary is the contract — `pos-sync`
operates exclusively inside `framework/`.**

**Verification.** A test seeds `<fixture-ws>/workspace/`
with custom content; runs `pos-sync` (which produces a fast-
forward inside `framework/`); asserts every file under
`<fixture-ws>/workspace/` is byte-identical pre/post (HC#4
binding — byte-content-match assertion).

**AC.D.3.5 — Audit log derives from `git log`.** The audit
output of `pos-sync` (replacing the pre-D.3 YAML-shaped audit
at `<workspace>/.pos/sync/<ref>/audit.yaml`) is constructed
from `git log <prev-ref>..<new-ref> --merges --no-merges`-
shaped queries plus, when the LLM-resolver fired, the
resolver's structured output appended as a separate per-
conflict log under `<workspace>/workspace/.pos/sync/resolver-runs/`.

**Verification.** A test runs `pos-sync` end-to-end and asserts
the operator-facing summary contains both the git-log-derived
summary AND (when the resolver fired) the resolver's structured
output. Method shape (one summary file vs structured stream
output) is the builder's call.

**AC.D.3.6 — pre-D.3 workspace-sync code retired.** ~2400 LOC
across `staging.py`, `ancestor_detection.py`, most of
`merge_helper.py`, most of `conflict_detection.py`, the
`canonical_cache.py` clean-write enumeration, and ~110 tests
are removed. The retained surface is: `cli.py` (rewritten),
`merge_resolver.py` (LLM resolver), `_resolver_client.py`,
`canonical.py` (resolution), `sync_config.py`, `state.py`
(now `git log`-derived; minimal), `sync_protected.py` (now
just declares `framework_floor` for documentation; structural
enforcement comes from the directory split). Test count
post-D.3: ~30 tests (90 retired).

**Verification.** A test asserts the post-D.3 file count
+ test count match the expected retained set. (Method: the
seal-diff test catches this naturally; an explicit counter is
optional.)

**AC.D.3.S — Seal-diff invariant.** Single-component
amendment (workspace-sync only). Diff between BASELINE and
SEAL_COMMIT is confined to `framework/workspace-sync/` (post-D.1)
+ universal admissions.

### Amendment D.4 — `pos-new-workspace` console-script (β.2 absorption)

**Objective.** New `pos-new-workspace --from <repo>`
console-script (entry point in `workspace-bootstrap`'s
`pyproject.toml`) that creates a new workspace at
`<new-ws>/` by:

1. `git clone <repo> <new-ws>/framework/`
2. `pos init <new-ws>` — invokes the existing scaffold against
   `<new-ws>/workspace/` (and `<new-ws>/.claude/`).

Subsumes the previously-planned β.2 LL bootstrap (which
assumed flat-tree). The β.2 plan (`workspace-sync-ergonomics.md`
β.2 chain) absorbs into D.4's amendment cycle.

**AC.D.4.1 — `pos-new-workspace --from <repo> <new-ws-path>`
creates a working workspace.** Running the command against a
URL (or a local canonical path) produces a `<new-ws>/` with
(a) `<new-ws>/framework/` cloned from `<repo>`, (b)
`<new-ws>/workspace/` scaffolded, (c) `<new-ws>/.claude/`
scaffolded with `settings.json` + `agents/`. The workspace is
ready for first-run on `cd <new-ws> && claude`.

**Verification.** A test in
`workspace-bootstrap/tests/test_pos_new_workspace.py` runs the
command against a fixture canonical clone and asserts the
expected directory tree post-invocation. A second test exercises
the `pos init <existing-ws>` shape against a workspace whose
`framework/` was cloned by the operator outside the
`pos-new-workspace` flow (back-compat).

**AC.D.4.2 — `pos init` is idempotent.** Re-running `pos init
<existing-ws>` produces no further changes (no mtime churn,
no file overwrites). Same idempotency contract as
amendment #36/#37/#47's scaffold operations.

**Verification.** A test runs `pos init <fixture-ws>` twice
and asserts the second run reports zero changes
(structured-result equivalence).

**AC.D.4.3 — `pos-new-workspace` documented in
`workspace-bootstrap/README.md` + the operator-facing
`docs/rebuild/STATE.md` entry.** The verb is discoverable
without reading source.

**Verification.** A test asserts `pos-new-workspace --help`
output references the `--from` flag + the `<new-ws-path>`
positional + describes the resulting directory shape.

**AC.D.4.S — Seal-diff invariant.** Single-component amendment
(workspace-bootstrap only). Diff confined to
`framework/workspace-bootstrap/` (post-D.1) + universal
admissions.

### Amendment D.5 — Optional cleanup of dead workspace-sync code

**Objective.** Builder's call at end of D.3: any code that
remained for transition purposes during D.3 (e.g. the old
`staging.py` shim that for transitional reasons was kept as a
no-op surface, the pre-D `.pos/sync-protected.yaml` writer
that's now redundant with the directory boundary) gets
deleted in a final cleanup amendment.

**AC.D.5.1 — Audited cleanup.** Builder lists every
remaining-but-dead file/symbol in the D.3 builder-plan's
post-build audit. Each item gets either (a) deleted with a
deletion-rationale, (b) kept with a justification (some surface
may be needed for the in-place migration script in D.2's
deferred-removal-window), (c) re-extended with a new AC
backing it.

**Verification.** A test asserts the cleanup is complete: no
unreferenced symbols in `framework/workspace-sync/src/`
(static-analysis catches dead exports). Method shape is the
builder's call.

**AC.D.5.S — Seal-diff invariant.** Single-component amendment
(workspace-sync only).

**Plan-author note.** D.5 is **optional** — if D.3's build
captures the cleanup inline (no transition surface left
behind), D.5 collapses to a no-op + this plan's tracking entry
gets closed. Plan-author classifies need at end of D.3 build.

---

## 5. Behaviour-count check (ODD §3.3 forward; per amendment)

Forward direction per amendment:

| Amendment | Declared behaviours | ACs | Match |
|-----------|---------------------|-----|-------|
| D.1 | (1) move complete; (2) editable-install topology preserved; (3) plist + .claude paths updated; (4) canonical dev workflow; (5) byte-content-match for representative files; (S) seal-diff | AC.D.1.1, .2, .3, .4, .5, .S | ✓ |
| D.2 | (1) workspace-state at workspace/; (2) .claude at root; (3) plist EnvironmentVariables; (4) migration script; (5) pos3 real-apply; (S) seal-diff | AC.D.2.1, .2, .3, .4, .5, .S | ✓ |
| D.3 | (1) git fetch invocation; (2) ff merge happy path; (3) non-ff fallback to LLM resolver; (4) Class-A structural protection; (5) audit derived from git log; (6) dead code retired; (S) seal-diff | AC.D.3.1, .2, .3, .4, .5, .6, .S | ✓ |
| D.4 | (1) pos-new-workspace creates working ws; (2) pos init idempotent; (3) help-text discoverable; (S) seal-diff | AC.D.4.1, .2, .3, .S | ✓ |
| D.5 | (1) audited cleanup; (S) seal-diff | AC.D.5.1, .S | ✓ |

Forward check passes.

Reverse direction (every code path / branch / dependency / test
in each amendment's diff → backing AC) is the builder's
pre-seal check, captured in each amendment's builder-plan §5
(per amendment-#46/#47/#48 precedent).

---

## 6. Hard constraints (binding from dispatch)

**HC#1.** Each amendment fences cleanly. **D.1 spans every
component** (directory move) — amendment-shaped per amendment-#46
multi-component precedent. D.2 spans workspace-bootstrap +
hands-off-lifecycle + workspace-sync (sync_protected) + possibly
self-upgrade (migration script). D.3 fences to workspace-sync.
D.4 fences to workspace-bootstrap. D.5 fences to workspace-sync.

**HC#2.** No regression of any landed amendment's tests. Every
component's existing tests continue to pass post-migration.
Tests targeting old workspace-sync code paths can be
removed/replaced when the underlying behavior moves to git-merge
(during D.3's specific window, ~110 tests retire — that's not a
"regression," that's a planned removal of test surface backing
removed code).

**HC#3.** No new third-party deps. Use existing git-shellout
machinery + Pydantic + stdlib. (D.3 specifically: shells out to
`git fetch`, `git merge --ff-only`, `git status --porcelain`,
`git log`, `git show`. No `pygit2` / `dulwich` / etc.)

**HC#4 (CRITICAL — bug-class-elimination).** Each amendment's
tests MUST include byte-content-match assertions for sample
workspace files post-apply. The resolve-stage-apply bug class
that triggered this whole architectural review was test-shape-
only verification; D's tests close that gap structurally.
Specifically:

- D.1 includes byte-content-match for component source files
  pre/post move (AC.D.1.5).
- D.2 includes byte-content-match for migrated workspace-state
  files (AC.D.2.4 + AC.D.2.5).
- D.3 includes byte-content-match for files post-`git merge --ff-only`
  (workspace files match canonical's HEAD blob byte-for-byte) and
  byte-equality for Class-A files pre/post sync (AC.D.3.4).
- D.4 includes byte-content-match for files in
  `<new-ws>/framework/` after `git clone` (matches canonical)
  and for `<new-ws>/workspace/` after `pos init` (matches
  scaffold-default values).

**HC#5.** Workspace-state preservation must be empirically
verified end-to-end against pos3 (real apply, real `cmp`
against canonical's HEAD blobs in `framework/`, real
workspace-state retention check in `workspace/`). This is the
"believe Luke's machine, not just the test fixture" check
mandated by `feedback_trust_operational_reality`. The
verification lands in D.2's seal narrative (the migration
amendment) and again in D.3's seal narrative (the first
post-migration sync run).

**HC#6 (D's structural promise).** Post-migration, it must be
**impossible** to accidentally write workspace-state into
`framework/` or framework code into `workspace/`. The directory
boundary is the structural contract enforced by:

1. `framework/.gitignore` does NOT include `.pos/`, `personas/`,
   `memory.yaml`, etc. — those names simply do not exist
   inside `framework/`.
2. `<workspace>/.gitignore` (the parent gitignore at workspace
   root) declares `framework/` as the ONLY git-tracked
   subdirectory (everything else gitignored).
3. Components that read workspace state read
   `<workspace>/workspace/<file>` (or `<workspace>/.claude/<file>`).
   The lookup path itself enforces the class.

Plan-author explicitly notes the place where the boundary is
*currently fuzzy* + how D's migration sharpens it (per dispatch
instruction): pre-D, `<workspace>/personas/contract.yaml` was
Class-A by `sync-protected.yaml`'s framework_floor pattern, but
nothing structurally prevented a sync-bug from overwriting it
(α-hotfix-2's exact bug class). Post-D, `<workspace>/workspace/personas/`
is *structurally outside* `framework/`'s tree; `pos-sync`
operating exclusively inside `framework/` cannot touch it.
**Fuzziness eliminated.** Same shape for `.pos/`, `.mcp.json`,
`memory.yaml`, every other Class-A path.

**HC#7 (CDC adherence).** scope-only-dispatch CDC (each
amendment's dispatch carries objective + scope + halt + ODD-check;
the builder authors method in the builder-plan). Standard
pos-amend manifest discipline. `pos-amend seal --plan-doc
<abs-path>` backfills §14.

**HC#8 (No `--amend`).** Corrective new commits only per
`feedback_no_amend_in_agent_dispatches`.

**HC#9 (Plan-before-code).** This plan exists; each amendment's
builder authors a builder-plan at
`docs/rebuild/plans/d-migration-D.x.builder-plan.md` (or per
the sub-plan-doc precedent — naming is the dispatcher's call
at dispatch time) before editing any source.

---

## 7. Out of scope (explicit)

Per ODD §2.5 and the locked dispatch:

- **Workspace tooling beyond pos-v2's own.** Adopting uv
  workspaces / hatch workspaces (the research's Q2 option (c))
  is **out of scope** for D-migration. If maintainability of
  multiple editable installs becomes a pain post-D, a future
  amendment can add monorepo tooling — independent of D.
- **Multi-framework workspaces** (a hypothetical workspace
  that pulls from two canonical sources). Out of scope; the
  directory-split makes this *easier* to add later (just put
  `framework-a/` + `framework-b/` side-by-side) but D ships
  one framework.
- **Plugin layout structural change.** Plugins (per
  FUTURE_IDEAS Idea 3, workspace-bootstrap's extension protocol)
  continue to ship as in-tree components (under
  `framework/<plugin-name>/`) or as external editable installs.
  Plugins-from-external-source landing under
  `framework/plugins/<name>/` is a future amendment.
- **`.gitattributes` `merge=ours` driver authoring.** D.3's
  rare-conflict fallback uses `git merge`; the merge driver
  config lives in `framework/.gitattributes` (D-Q.B5 surfaces
  the question "do we ship a default `.gitattributes` with
  `memory.yaml merge=ours`?"). Plan-author surfaces; if owner
  rules YES, it lands inside D.3's amendment; if NO, it's a
  future-amendment for an operator-tunable workspace-rules layer.
- **`pos` global binary** (β.3 MM). Independent amendment per
  D-D5 LOCKED. Not in this migration plan.
- **Removal of `~/.pos/canonical-cache/`** (the cache clone
  used pre-D for fetch freshness). Post-D it can be retired
  if `framework/`'s git-remote points directly at the canonical
  URL; whether to retire is the builder's call inside D.3 (the
  cache clone has minor freshness benefits — multi-workspace
  shared cache vs per-workspace fetch). Builder's call.
- **Slash-command primitive `/sync` in Claude Code.** Future
  amendment composes `/sync` on top of the new `pos-sync`
  shape. Out of scope.
- **The persona's "what changed in canonical?" briefing.** The
  audit-log shape (AC.D.3.5) supports it; but the persona-side
  consumer is a future amendment.

---

## 8. Implementation order

Suggested order — each amendment's builder refines in their
builder-plan. **Sequential** (per `feedback_serialize_amendment_builds`
— same git tree, no parallel builds):

1. **D.1 builds first.** Restructures canonical's tree. After
   D.1 seals, every dev tool (loam-mode, pos-amend,
   heavy-b-migrate) operates against `framework/<...>` paths.
2. **D.2 builds second.** Establishes `<workspace>/workspace/`
   path; ships migration script. The pos3 in-place migration
   runs at end of D.2 build (HC#5 — empirical verification).
3. **D.3 builds third.** Replaces `pos-sync`'s pipeline with
   git-merge. Heavy LOC drop. After D.3 seals, the bug-class
   collapse is structural.
4. **D.4 builds fourth.** Adds `pos-new-workspace` console-script.
   β.2 absorbed.
5. **D.5 builds optionally.** Cleanup pass; or no-op.

**Per-amendment internal order** is each builder's call
inside the AC outcome bound. Suggested high-level shape:

- Read session-start corpus + this plan + the relevant prior
  amendments' plan-docs.
- Author builder-plan at
  `docs/rebuild/plans/d-migration-D.x.builder-plan.md` before
  any source edit.
- Land structure-shape changes first (file moves; new
  scaffold paths); then code-shape changes (discovery, plist,
  config); then test changes (existing test fixtures + new
  byte-content-match assertions).
- Run touched-component suite; then `pos-amend apply --dry-run`;
  if clean, run amendment commit; then `pos-amend seal
  --plan-doc <abs-path>`.
- For D.2: also run the empirical pos3 migration as the seal-
  narrative artefact (HC#5).

**Speedups applied** per `feedback_amendment_dispatch_speedups`:

- (a) Scoped-sweep seal: each amendment's `pos-amend seal
  --scoped-sweep` runs only the touched component(s)' seal-
  diff tests. (D.1 is the exception — multi-component scope
  means the sweep is wide.)
- (b) Pre-seal smoke: touched-component tests pass before
  commit; full repo-wide pytest skipped pre-seal.
- (c) Inline methodology snippets in commit prose.

---

## 9. Bookkeeping surface (per-AC plan-doc convention)

Per amendment, sealed-component shape:

### D.1 manifest sketch (multi-component)

```yaml
schema_version: 1
amendment:
  number: <N+0>  # next free amendment number at dispatch time; D.1 is the first of 5
  slug: d-migration-D.1-directory-restructure
  title: "D-migration D.1 — framework/ directory restructure on canonical pos-v2"

baseline: <HEAD~1 SHA>

plan: docs/rebuild/plans/d-migration.md

# Multi-component sealed amendment. Every framework component's
# seal-test sidecar moves to framework/<component>/tests/SEAL_COMMIT.
components:
  - name: scope-of-work
    seal_test: framework/scope-of-work/tests/test_no_sealed_amendments.py
    sidecar: framework/scope-of-work/tests/SEAL_COMMIT
    frozen_baseline: false
    extra_allowed_prefixes: []
  - name: objective-tracker
    seal_test: framework/objective-tracker/tests/test_no_sealed_amendments.py
    sidecar: framework/objective-tracker/tests/SEAL_COMMIT
    frozen_baseline: false
    extra_allowed_prefixes: []
  - name: primary-persona
    seal_test: framework/primary-persona/tests/test_no_sealed_amendments.py
    sidecar: framework/primary-persona/tests/SEAL_COMMIT
    frozen_baseline: false
    extra_allowed_prefixes: []
  # ... 14 more components ...
  - name: hands-off-lifecycle
    seal_test: framework/hands-off-lifecycle/tests/test_no_sealed_amendments.py
    sidecar: framework/hands-off-lifecycle/tests/SEAL_COMMIT
    frozen_baseline: true   # H19 frozen baseline component (per amendment #23)
    extra_allowed_prefixes: []

universal_paths:
  prefixes:
    - docs/rebuild/plans/
  files:
    - CLAUDE.md
    - docs/odd-in-pos.md
    - docs/odd-methodology.md
    - docs/rebuild/FUTURE_IDEAS.md

narrative:
  target: framework/<TBD>/seals/SEAL_COMMIT.d-migration-D.1
  body: |
    # Amendment #<N> — D-migration D.1 — framework/ directory restructure
    <builder finalises body — see narrative shape in
    amendment-46 manifest for multi-component precedent>
```

### D.2 manifest sketch (multi-component)

```yaml
components:
  - name: workspace-bootstrap
    seal_test: framework/workspace-bootstrap/tests/test_no_sealed_amendments.py
    sidecar: framework/workspace-bootstrap/tests/SEAL_COMMIT
  - name: hands-off-lifecycle
    seal_test: framework/hands-off-lifecycle/tests/test_no_sealed_amendments.py
    sidecar: framework/hands-off-lifecycle/tests/SEAL_COMMIT
    frozen_baseline: true
  - name: workspace-sync
    seal_test: framework/workspace-sync/tests/test_no_sealed_amendments.py
    sidecar: framework/workspace-sync/tests/SEAL_COMMIT
  - name: self-upgrade  # if migration script lives here; else drop
    seal_test: framework/self-upgrade/tests/test_no_sealed_amendments.py
    sidecar: framework/self-upgrade/tests/SEAL_COMMIT
```

### D.3 manifest sketch (single-component)

```yaml
components:
  - name: workspace-sync
    seal_test: framework/workspace-sync/tests/test_no_sealed_amendments.py
    sidecar: framework/workspace-sync/tests/SEAL_COMMIT
```

### D.4 manifest sketch (single-component)

```yaml
components:
  - name: workspace-bootstrap
    seal_test: framework/workspace-bootstrap/tests/test_no_sealed_amendments.py
    sidecar: framework/workspace-bootstrap/tests/SEAL_COMMIT
```

### D.5 manifest sketch (single-component, optional)

```yaml
components:
  - name: workspace-sync
    seal_test: framework/workspace-sync/tests/test_no_sealed_amendments.py
    sidecar: framework/workspace-sync/tests/SEAL_COMMIT
```

**Dependents cleared at seal:** D.2 unblocks once D.1 seals;
D.3 unblocks once D.2 seals; D.4 unblocks once D.3 seals; D.5
optional, post-D.3.

**Universal admissions** match amendment #46/#47 pattern.

**Frozen-baseline:** `true` for `hands-off-lifecycle` (per
amendment #23 H19 frozen-baseline rule); `false` for
others.

**Test scope** per `feedback_amendment_dispatch_speedups`:
narrow per-amendment; D.1 is the exception (broad scope) but
runs touched-component sweep (every component) which is the
intended behaviour for the multi-component restructure.

**Commits:**
- D.x amendment commit: `feat(<components>): D-migration D.x —
  <one-line summary> (amendment #<N>, AC.D.x.1–AC.D.x.S)`.
- D.x seal commit: `chore(seals): d-migration-D.x — <components>
  at <amendment-sha>`.

No `--amend`. `pos-amend apply --dry-run` green is the prereq
to amendment commit; `pos-amend seal --plan-doc <abs-path>`
finalises.

---

## 10. Halt triggers (builder halts + signals owner)

Each amendment's builder halts and signals owner if any of the
following fire. Each carries a specific surface check; the
builder does NOT silently extend a violation per
`feedback_subagent_odd_violation_halt`.

1. **A required new top-level spec objective surfaces.** This
   plan binds to AC.PO.1 + AC.PO.2. If during D.x build the work
   cannot fit under existing VALUE_PROPOSITION ACs, halt-and-
   surface to owner.
2. **ODD violation observed in surrounding code/docs.** Per
   `feedback_subagent_odd_violation_halt`, halt and surface;
   do NOT extend a violating surface.
3. **An AC cannot be authored outcome-shaped.** If a behaviour
   the build needs to satisfy can only be tested by asserting
   a method choice, halt — the AC-author (owner via this plan
   author) must rewrite as outcome.
4. **Required source-edit OUTSIDE the named amendment fence.**
   Halt and surface. The plan's per-amendment fence is binding;
   cross-fence work re-extends the amendment scope or splits
   into a separate amendment.
5. **Pre-existing test fails post-restructure (D.1).** During
   D.1, if a pre-existing component test fails after the move
   (other than mechanical-fixture-update fails for the path
   shift itself), halt — that's a topology-discovery code bug
   that needs surfacing before we proceed to D.2.
6. **D.2 migration script breaks pos3 mid-flight.** During D.2's
   pos3 empirical run (HC#5), if the migration script produces
   any non-byte-identical workspace-state file post-migration,
   halt immediately. Recovery: revert pos3 to pre-D.2 state via
   git reset on framework/'s remote; investigate; halt-and-surface.
7. **D.3's git-merge mechanics produce a workspace-file change
   inside `<workspace>/workspace/`.** Per HC#6 — the directory
   boundary is the structural contract. If `pos-sync` ever
   modifies any path outside `framework/`, halt — that's an
   architectural bug; the sync should never have touched it.
8. **Wall-time exceeds projected per-amendment estimate by
   >50%.** Halt with current-state report; owner triages
   whether to continue, split, or pause.
9. **D.4's `pos-new-workspace` cannot land without touching
   sealed components outside workspace-bootstrap.** Halt;
   owner rules whether to extend D.4's fence or split into
   sub-amendments.
10. **HC#5 empirical pos3 verification fails.** Workspace-state
    file lost or modified during D.1 / D.2 / D.3. Stop
    immediately; this is the bug-class-elimination promise's
    structural guarantee — failure here means the migration
    didn't actually deliver the promise.

---

## 11. Decisions remaining for the owner to rule on

**All five decisions LOCKED 2026-04-27 by primary persona under confidence-delegation** (Luke 2026-04-27 broad-autonomy directive). Detail preserved below for audit trail.

- **D-Q.A1 LOCKED:** AC breakdown per §4 accepted as-authored. High confidence.
- **D-Q.A2 LOCKED:** Build sequence D.1 → D.2 → D.3 → D.4 → D.5 accepted. Alternatives fail prerequisites. High confidence.
- **D-Q.A3 LOCKED:** All 5 amendments are sealed-component-shaped. High confidence.
- **D-Q.A4 LOCKED:** `.claude/` at workspace root, NOT under `workspace/`. Honours Claude Code expectation; structural-promise preserved (D's directory split keeps workspace state separation; `.claude/` is a Claude Code surface, not pos-v2 workspace state per se). High confidence.
- **D-Q.A5 LOCKED:** Drop Class-B as a category under D. Directory split makes formerly-Class-B paths Class-A by relocation (they live in `workspace/` and never get pulled). The `.gitattributes merge=ours` driver becomes vestigial. Medium confidence: alternative (preserve Class-B) has unclear use cases under directory-split — leaving framework simpler wins; if a real Class-B use case emerges post-migration, easy to re-introduce as follow-on.

**Decisions detail follows below for audit-trail purposes.**

Five outcome-shape decisions remained at plan-author time. Method-shape (which file, which test, which exact `git mv` order) is the builder's call inside each AC bound.

### D-Q.A1 — Per-amendment AC breakdown (deviation from §4 outline?)

**Question.** §4 enumerates 5–7 ACs per amendment. The
dispatch authorised plan-author to refine the AC breakdown if
deviation from the 5-amendment outline is needed. Plan-author
**did not deviate** — the 5-amendment outline holds. Per-
amendment ACs follow §4.

**Recommendation.** **Accept the §4 AC breakdown.** No new
amendments needed; no merging of D.4 + D.5 (D.5 is optional
and may be a no-op).

**Why this matters.** If owner has a different mental model
of the AC granularity (e.g. wants D.1 split into D.1a
"directory move" + D.1b "discovery code update"), surface now
before dispatch.

### D-Q.A2 — Build sequence ordering (deviation from D.1 → D.5?)

**Question.** §8 enumerates D.1 → D.5 sequentially. Plan-
author considered alternatives:

- **(a) D.1 → D.2 → D.3 → D.4 → D.5** (recommended; locked at
  dispatch).
- **(b) D.3 first, then D.1 + D.2.** Fails: D.3's `git fetch +
  git merge --ff-only` against `framework/` requires
  `framework/` to exist as a directory. Cannot precede D.1.
- **(c) D.2 before D.1.** Fails: D.2's plist EnvironmentVariables
  reference `<workspace>/framework/<...>` paths which don't
  exist before D.1.

**Recommendation.** **Accept (a).** No deviation from the
dispatch's locked ordering.

### D-Q.A3 — Sealed-component vs dev-discipline shape per amendment

Per dispatch: "Whether each amendment is sealed-component or
dev-discipline shape (plan-author classifies)."

**Plan-author classification:**

| Amendment | Shape | Reasoning |
|-----------|-------|-----------|
| D.1 | sealed-component (multi-component) | Source moves; tests update; sealed-component fences trigger. **Confirmed sealed.** |
| D.2 | sealed-component (multi-component) | Source edits (workspace-bootstrap scaffold; hands-off-lifecycle helper paths; workspace-sync sync_protected). **Confirmed sealed.** |
| D.3 | sealed-component (single-component) | Big LOC drop in workspace-sync src + tests. **Confirmed sealed.** |
| D.4 | sealed-component (single-component) | New console-script entry point; new source module. **Confirmed sealed.** |
| D.5 | sealed-component (single-component) | Cleanup edits inside workspace-sync src. **Confirmed sealed** (or no-op if D.3 captures inline). |

**Recommendation.** **All five are sealed-component**. None
is dev-discipline shape.

### D-Q.A4 — Path layout for `<workspace>/workspace/` — `.claude/` placement

Per dispatch: "Specific path layout decisions for
`<workspace>/workspace/` (e.g., does `.claude/` live at
`<workspace>/.claude/` or `<workspace>/workspace/.claude/`? —
Claude Code expects `.claude/` at workspace root)."

**Question.** Should `.claude/` (containing `settings.json` +
`agents/`) live at `<workspace>/.claude/` (workspace root) or
under `<workspace>/workspace/.claude/`?

**Constraints:**

- Claude Code reads `.claude/settings.json` from the workspace
  root by default. Moving it to `<workspace>/workspace/.claude/`
  requires Claude Code to be invoked as `cd workspace/ && claude`
  — operator chore.
- `.claude/settings.json` IS workspace state (operator-edited
  hooks, agent registrations). It belongs in the
  workspace-state class.
- The structural-promise (HC#6) requires that workspace state
  not be inside `framework/`. `.claude/` at workspace root
  satisfies this — it's outside `framework/` (which is the
  git-tracked subdirectory).

**Plan-author analysis.** Three options:

- **(a) `.claude/` at workspace root** (current pos3 location;
  Claude Code finds it natively). `framework/.gitignore`
  excludes nothing (no `.claude/` inside `framework/`).
  `<workspace>/.gitignore` declares `framework/` as the only
  tracked subdirectory; `.claude/` is gitignored at workspace
  root.
- **(b) `.claude/` at `<workspace>/workspace/.claude/`**
  (operator runs `cd workspace/ && claude`). Violates Claude
  Code's expectation; significant operator chore.
- **(c) Symlink `<workspace>/.claude/` → `<workspace>/workspace/.claude/`**
  (best of both worlds for Claude Code; structural-promise
  satisfied because the data lives under `workspace/`).
  Adds a symlink layer; symlinks-in-pos3 historically caused
  trouble per workspace-sync HC#12 ("no symlink resolution").
  Deferred; not preferred.

**Recommendation.** **(a) `.claude/` at workspace root.** The
structural-promise is preserved (it's outside `framework/`);
Claude Code's expectation is honoured; no operator chore.
Plan-author proposes locking this for D.2.

### D-Q.A5 — `.gitattributes` `merge=ours` driver for Class-B paths (D.3-window)

**Question.** D.3's rare-conflict fallback uses `git merge`
when `git merge --ff-only` fails. Pre-D's Class-B paths
(`memory.yaml` is the only documented one in
`sync_protected.py`'s `FRAMEWORK_FLOOR`) prefer-canonical-on-
no-local-edit semantics. Under D.3:

- (a) Ship `framework/.gitattributes` with `memory.yaml
  merge=ours` so git auto-resolves the merge in workspace's
  favour. (Plan-author note: `merge=ours` keeps the LOCAL
  side; for "prefer-canonical-on-no-local-edit," the actual
  git driver is more nuanced — may need a custom merge driver
  shellout.)
- (b) Drop Class-B as a category. Under D, `memory.yaml` lives
  under `<workspace>/workspace/memory.yaml` (workspace-state),
  outside `framework/`'s tree. There's nothing for canonical to
  conflict against because canonical doesn't ship a
  `<workspace>/workspace/memory.yaml` — it ships
  `<framework>/<some-other-shape>/memory.yaml` if at all.
  **Class-B becomes Class-A by structural relocation.**
- (c) Leave Class-B as a documentation surface only; D.3's
  resolver handles the rare case where canonical happens to
  ship a same-named file.

**Recommendation.** **(b) Drop Class-B as a category.** Under
D's directory split, `memory.yaml` is workspace-state and lives
under `<workspace>/workspace/memory.yaml`. The structural
boundary makes it Class-A by construction. No `merge=ours`
driver needed; no `.gitattributes` needed beyond the
default. **Surface to owner; recommended ruling.**

If owner prefers (a) or (c) for back-compat (e.g. some
in-flight workspace has `memory.yaml` at workspace root pre-
migration), the migration script (D.2 AC.D.2.4) handles the
move; Class-B reduces to "transition-window only" and gets
retired in D.5.

---

## 12. Summary of named decisions (owner-readable)

| Decision | Recommendation | Why it matters |
|---|---|---|
| D-Q.A1 — AC breakdown deviates from §4? | **Accept §4 outline as-is** | 5 amendments hold; no merging, no splitting |
| D-Q.A2 — Build ordering deviates from D.1→D.5? | **Accept D.1 → D.5** | (b) and (c) fail structural prerequisites |
| D-Q.A3 — Sealed-component vs dev-discipline shape | **All 5 sealed-component** | Source edits + tests in every amendment trigger sealed-component shape |
| D-Q.A4 — `.claude/` at workspace root or under `workspace/`? | **(a) At workspace root** | Honours Claude Code's expectation; structural-promise preserved (outside `framework/`); no operator chore |
| D-Q.A5 — Class-B handling under D.3 | **(b) Drop Class-B as a category** | Directory split makes `memory.yaml` Class-A by structural relocation; no merge driver needed |

All five surface for owner ruling. D-Q.A1 / A2 / A3 / A4 are
high-confidence recommendations (likely accepted). D-Q.A5 has
two close-second alternatives (a) and (c) that owner may prefer
on back-compat grounds.

---

## 13. Halt-and-surface findings encountered during plan authoring

Per `feedback_subagent_odd_violation_halt`: halt and surface any
ODD violation observed in surrounding code/docs, plus any
constraint the dispatch missed.

Plan-authoring scope (read-only audit of canonical pos-v2's tree
+ the workspace-sync component + pos3's actual layout):

### Finding 1 — `.claude/settings.json` is BOTH framework-tracked AND workspace-scaffolded (today)

**The asymmetry.** Canonical pos-v2's `.claude/settings.json`
is tracked in canonical's git (verified — canonical has the
SessionStart hook config wiring `first-run.sh`). Workspace-
bootstrap, on first-run, **overwrites** pos3's `.claude/settings.json`
with a different content (verified — pos3's settings.json
references `/Users/lukeivers/pos3/.venv/bin/python ...
orchestrator/scripts/pos_session_start.py` which is
workspace-bootstrap-scaffolded, not canonical-tracked content).

This is exactly the bug-class the research's D-Q.A1 question
named: a file that is tracked in canonical AND workspace-
scaffolded creates an N-branches "did sync remember to skip
overwriting it?" code path. Today's mechanism: workspace-bootstrap
overwrites on first-run, and `pos-sync` treats it as Class-A
(per `sync_protected.py`'s `framework_floor` `.mcp.json`-style
admission that any `.claude/` path is workspace state). But
the canonical-side `.claude/settings.json` is tracked content;
when canonical updates it, downstream pos3 doesn't pick up the
change because the workspace-bootstrap scaffold has already
overwritten it with a workspace-tailored variant.

**Under D, the asymmetry resolves cleanly:**

- Canonical's dev-mode hooks live at `<canonical-root>/.claude/settings.json`
  (canonical's workspace root). After D.1 + D.2, canonical's
  workspace-state location is `<canonical-root>/.claude/`
  (workspace root, per D-Q.A4 recommendation). Canonical's
  `.claude/settings.json` is gitignored (NOT tracked under
  `framework/`).
- An optional `framework/.claude/settings.dev-template.json`
  ships in canonical's tracked tree as a *template* the
  canonical maintainer's first-run can copy to
  `<canonical-root>/.claude/settings.json` on a fresh canonical
  clone. This is the dev-mode bootstrap.
- Workspace-bootstrap continues to scaffold pos3-style
  `<workspace>/.claude/settings.json` from
  `framework/workspace-bootstrap/<scaffold-template>` — its
  current behaviour. **Unchanged.**
- The split eliminates the "did sync remember to skip"
  question structurally: `.claude/settings.json` is
  unambiguously workspace state (D-Q.A4); canonical never
  ships one inside `framework/`; sync can never overwrite it.

**Plan-author surfacing.** D.1's amendment fence MUST include
the canonical-side `.claude/settings.json` rename to
`framework/<...>/settings.dev-template.json` (or analogous;
builder's call inside D.1 outcome bound). Surfaced as a
specific item the D.1 builder must include.

### Finding 2 — `memory-system/.venv/` is workspace-state, not framework code

The dedicated venv at `<workspace>/memory-system/.venv/` is
workspace-state (per the existing `.gitignore` pattern
`.venv/`). Under D, it lands at
`<workspace>/workspace/memory-system-venv/` or
`<workspace>/framework/memory-system/.venv/` (gitignored
inside `framework/`).

**Plan-author analysis.** The cleanest shape is a single
`<workspace>/.venv/` (the shared venv) plus a single
`<workspace>/.venv-memory-system/` (the dedicated heavy
venv). Both at workspace root. Both gitignored at the
parent `<workspace>/.gitignore` level. Inside `framework/`,
NO `.venv/` directories exist — those are workspace state.
This requires updating `first-run-inventory.yaml`'s
`dedicated_venvs[0].venv_path` from
`memory-system/.venv` to `.venv-memory-system/` (or similar)
and updating `first_run_helper.py`'s install logic. Builder's
call inside D.1 / D.2 outcome bound; surfaced for owner
awareness.

**Surface.** D.1 + D.2's combined fence MUST address the
venv path question. Plan-author flags but does not lock —
builder picks shape inside outcome bound.

### Finding 3 — `data/` directories are component-relative + gitignored via `*/data/`

`.gitignore`'s `*/data/` pattern catches per-component data
dirs (`memory-system/data/`, `scope-of-work/data/`, etc.).
Under D's framework move, those become
`framework/<component>/data/`. The pattern still works
(`*/data/` matches `framework/<component>/data/` because
`*` matches `framework` but does NOT match `framework/<component>` —
wait, `*/data/` only matches one path-segment-deep). **This
needs verification by the D.1 builder.** A safer approach:
add explicit `framework/*/data/` to `framework/.gitignore`,
or relocate per-component data to
`<workspace>/workspace/data/<component>/` (workspace-state
class, structural).

**Recommendation (surfaced for owner):** relocate
per-component data to `<workspace>/workspace/data/<component>/`.
Per-component data is workspace-state (databases, caches,
runtime artefacts), not framework code. Belongs under
`workspace/`. **Surface for owner ruling under D-Q.A4
extension.** Plan-author leans toward this shape; flagged
for D.2 builder confirmation.

### Finding 4 — `first-run-inventory.yaml` IS framework configuration (lives under `framework/`)

`first-run-inventory.yaml` declares the framework's component
list + venv config. It's framework configuration, not
workspace state. Under D, it lands at
`framework/first-run-inventory.yaml`. Test:
`first_run_helper.py`'s `_install_editable_components` reads
from `<pos_v2_root>/framework/first-run-inventory.yaml` post-
D.1.

**No halt — flagged as a confirmation for D.1 builder.**

### Finding 5 — `tools/` contains canonical-side dev tooling (loam-mode, pos-amend, heavy-b-migrate)

Pre-D, `tools/` is at canonical root. Post-D, `tools/`
moves under `framework/tools/`. Verified that `tools/pos-amend/`
+ `tools/heavy-b-migrate/` use relative-path resolution
internally (verified via grep — `pos-amend`'s entry-point
references are relative). The move should be clean. Verify
during D.1.

**No halt — flagged as a confirmation for D.1 builder.**

### Finding 6 — Cross-machine plist-template path embedding

The plist templates in `_LAUNCHD_TEMPLATES` use `{workspace}`
placeholders that become absolute paths at install-time
(`/Users/lukeivers/pos3/...`). Under D, those become
`/Users/lukeivers/pos3/framework/...` for framework-code
references and `/Users/lukeivers/pos3/workspace/...` for
workspace-state references (or `/Users/lukeivers/pos3/...`
for the shared venv at workspace root, per D-Q.A4
recommendation).

**Cross-machine gotcha:** if Luke (or any future user) has
a workspace at a non-`/Users/lukeivers/pos3/` path, the
plist templates substitute correctly because they use
`{workspace}` — already cross-machine-safe by construction.
**No halt — confirmation that D's template machinery is
cross-machine-clean.**

### Finding 7 — workspace-sync `sync-protected.yaml`'s `FRAMEWORK_FLOOR` becomes vestigial under D

Pre-D, `FRAMEWORK_FLOOR` patterns (`personas/**/contract.yaml`,
`.pos/**`, `.scratch/**`, `.mcp.json`, `memory.yaml`) declare
which paths are Class-A. Under D, every one of these lives
under `<workspace>/workspace/<...>` or `<workspace>/.claude/<...>` —
i.e. STRUCTURALLY OUTSIDE `framework/`. The
`FRAMEWORK_FLOOR` pattern-matching is no longer the structural
contract; the directory boundary is.

**Plan-author judgment.** Drop `sync_protected.py`'s
runtime classification entirely under D.3. Keep the file
as documentation surface (a comment or readme), or retire
the file entirely. **Surface to owner via D-Q.A5 + D.5
cleanup audit.** Builder's call inside D.3 / D.5 outcome
bound.

### Finding 8 — `~/.pos/canonical-cache/` retain-or-retire

Pre-D, the cache clone at `~/.pos/canonical-cache/<repo-id>/`
is the bare clone workspace-sync fetches against. Post-D, the
workspace's `framework/.git/` has its own remote pointing
at canonical (URL or path). The cache clone becomes
optional — it's still useful for multi-workspace freshness
sharing (one fetch, N workspaces consume), but not
structurally required.

**Builder's call** (inside D.3 outcome bound): retire the
cache clone, or retain. Plan-author leans retain-with-
optional (cache clone serves multiple workspaces; retiring
is a small LOC drop but loses freshness-sharing). Surfaced
for awareness.

### Halt summary

**No critical halts.** Findings 1–8 are surface-confirmations
the per-amendment builders pick up, plus minor decision-shape
items surfaced under D-Q.A4/A5 + the per-amendment fence
clarifications.

**Wall-time projection:** plan-authoring took ~45 minutes —
under the 1.5h ceiling. **Halt trigger 8 does not fire.**

---

## 14. Method-decision record (builder, post-build)

To be filled by the D-migration builders post-build (per
amendment-#46/#47/#54 precedent). Each amendment's record
is its own §14 sub-section here (D-build.D.x.A through
D-build.D.x.Z).

### D.1 — D-build.D.1.x

(post-build)

### D.2 — D-build.D.2.x

(post-build)

### D.3 — D-build.D.3.x

(post-build)

### D.4 — D-build.D.4.x

(post-build)

### D.5 — D-build.D.5.x

(post-build, if D.5 is non-no-op)

### Commit SHAs

- Amendment commit: `8acdff591cac810140210c85f1144af35d6b5d30` —
  `chore(workspace-bootstrap): advance BASELINE + SEAL_COMMIT for D-migration D.4 window`
- Seal commit: `8dbbb7abd5a774be099188eed1dc92736aaad464` —
  `chore(seals): D-migration D.4 — pos-new-workspace --from <repo> console-script (β.2 absorbed) — workspace-bootstrap at 8acdff5`
## 15. Backwards-compat verification (per amendment, post-build)

To be filled by builders post-build. Each amendment's record
documents:

- All pre-existing tests pass post-amendment.
- Any test fixtures requiring mechanical updates documented
  with intent preservation.
- HC#1 (per-amendment fence) verified via seal-diff test.
- HC#2 (no regression) verified via full touched-component
  pytest pass.
- HC#3 (no new third-party deps) verified via uv.lock diff.
- HC#4 (byte-content-match assertions) verified via per-AC
  test assertions.
- HC#5 (pos3 empirical) verified via operator-confirmed
  end-to-end run, captured in seal narrative.
- HC#6 (structural-promise) verified via end-to-end fixture
  exercise.
- Speedups applied per `feedback_amendment_dispatch_speedups`.

---

## 16. References

- CLAUDE.md (project + global)
- `docs/odd-methodology.md`, `docs/odd-in-pos.md`
- `docs/rebuild/VALUE_PROPOSITION.md`, `docs/rebuild/STATE.md`,
  `docs/rebuild/FUTURE_IDEAS.md`,
  `docs/rebuild/FUTURE_IDEAS_DRAFT.md`
- `docs/rebuild/plans/research/workspace-architecture-directory-split-2026-04-27.md`
  (research note — companion gating doc)
- `/Users/lukeivers/pos3/.scratch/claude-output/workspace-sync-first-principles-2026-04-27.md`
  (first-principles analysis)
- `docs/rebuild/plans/workspace-sync.md` (#56 — keystone B-mode)
- `docs/rebuild/plans/workspace-sync-resolver-cost-overhaul.md` (#57 — α NN fast-path)
- `docs/rebuild/plans/workspace-sync-alpha-hotfix.md` (#59 — α-hotfix #1)
- `docs/rebuild/plans/workspace-sync-alpha-hotfix-2.md` (#60 — α-hotfix #2)
- `workspace-sync/src/workspace_sync/sync_protected.py` (FRAMEWORK_FLOOR — vestigial post-D)
- `workspace-sync/src/workspace_sync/cli.py` (the CLI being rewritten in D.3)
- `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py`
  (`_LAUNCHD_TEMPLATES` updated in D.1; scaffold paths updated in D.2)
- `hands-off-lifecycle/hooks/first_run_helper.py`
  (`_discover_components` + `_topological_order` updated in D.1)
- `hands-off-lifecycle/hooks/first-run.sh` (canonical-side
  hook; path updated in D.1)
- `first-run-inventory.yaml` (moves to `framework/first-run-inventory.yaml`
  in D.1)
- `.gitignore` (updated in D.2 for the `framework/` + `workspace/`
  split)
- `.claude/settings.json` (canonical's tracked dev-mode hook;
  renamed under D.1 finding-1 surfacing)
- `pos3/.claude/settings.json` (workspace-bootstrap-scaffolded
  hook; unchanged in shape; absolute paths shift per D.2)
- `~/.pos/canonical-cache/` (cache clone retain/retire decision
  inside D.3)
- Amendment commit SHAs: `<TBD>` per amendment
- Amendment precedents: #46 (multi-component shape), #47
  (single-component shape + workspace-local config writer), #54
  (heavy-b-migrate sealed-floor-rebase fallback for D.1)
