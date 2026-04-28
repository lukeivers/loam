# Single-framework restructure — research

**Date:** 2026-04-28.
**Author:** dispatched research+plan agent (Opus 4.7, 1M context).
**Working tree audited:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical, HEAD `39cfbb1`).
**Lens:** Lens 1 (Claude-leverage), Lens 2 (harness + primary-persona value), Lens 3 (ODD).
**Companion plan:** `docs/rebuild/plans/single-framework-restructure.builder-plan.md`.

---

## TL;DR — one-page summary

**The doubling problem.** Canonical's repo root carries both top-level docs (`CLAUDE.md`, `CLAUDE.dev.md`, `docs/`, `README.md`) AND a `framework/<comp>/` subdir holding the 16 sealed components. `pos-new-workspace --from <canonical>` clones canonical wholesale into `<workspace>/framework/`, producing `<workspace>/framework/framework/<comp>/` (component paths doubled) and `<workspace>/framework/CLAUDE.md` / `<workspace>/framework/docs/` (top-level docs nested one level deeper than corpus-discovery hooks expect). The pos3 cutover (commit `938b4c8`) workaround is a fan of relative symlinks at the workspace root pointing into `framework/CLAUDE.md`, `framework/docs/...`. Cosmetic patch; the bootstrap still produces the underlying doubling on every fresh workspace.

**Recommendation.** **Alternative 4 — git subtree split + bootstrap clones the framework-only branch.** Canonical maintains a synthetic `framework-only` branch (or a sibling repo) whose tree is the contents of canonical's `framework/` subdir promoted to repo root: `framework-only/<comp>/` rather than `framework/<comp>/`. `pos-new-workspace --from <canonical>` clones that branch (via `git clone --branch framework-only` or via a sibling repo URL), so the workspace gets `<workspace>/framework/<comp>/` at single level. Top-level docs (`CLAUDE.md`, `CLAUDE.dev.md`, `docs/`, `README.md`) live BOTH on the main canonical branch (where humans browse / dev work happens) AND on the `framework-only` branch (where workspace operators read them at `<workspace>/framework/CLAUDE.md`, etc.) — the split mechanism keeps them in sync because they're authored once on `pos-v2` and `git subtree split` (or equivalent) carries them into `framework-only`. Composes with `pos-sync` because the workspace's `framework/` git tree tracks the `framework-only` branch as `origin/<default>`; `git fetch + git merge --ff-only` flow is unchanged.

**Why this alternative.** It is the only candidate that BOTH eliminates the doubling failure class structurally (the workspace's `framework/` directory cannot land at `framework/framework/` because the cloned tree's repo root IS the framework contents) AND keeps the validation property the FUTURE_IDEAS_DRAFT entry names (a stranger can `git clone <canonical>` to inspect the project, `git clone --branch framework-only <canonical>` to bootstrap a workspace; both work without bootstrap scripts). The cost is a one-time canonical-side mechanism setup (subtree split automation) and a single change to `pos-new-workspace` to clone the right branch. Failure class eliminated: "future operator runs `pos-new-workspace` and gets `framework/framework/<comp>/` doubling" — under this alternative, the cloned tree by construction cannot produce that shape.

**Failure-class accounting (ODD §5.1.1 — relocate vs eliminate):**

- **Eliminated:** doubling at `framework/framework/<comp>/`. The shape is unrepresentable because the cloned branch's tree HAS no nested `framework/` subdir — the operator cannot misconfigure their way into the doubled state.
- **Eliminated:** corpus-discovery breakage. `<workspace>/framework/CLAUDE.md` is the post-bootstrap location; `session_start_gate.discover_baseline_corpus` reads `<workspace_root>/CLAUDE.md` — a one-line change in the loader (or an additional symlink scaffolded once at bootstrap) closes the gap. The gap cannot re-open without the loader OR the symlink-scaffolding step being explicitly modified — different from the cosmetic-symlink-patch workaround on pos3, where every future workspace must redo the symlinks by hand.
- **Eliminated (as side effect):** the structural-guard test in `WorkspaceLayout` that refuses `workspace_root` with basename `framework` (workspace_paths.py:62) becomes more meaningful — under doubling the validator would see `<workspace>/framework/framework` if the operator pointed it at the wrong level; under the single-framework shape the `framework` directory's contents are exactly the components, no second-level path could mistakenly route there.
- **Relocated (acceptable):** the discipline of "publish a `framework-only` branch in lockstep with `pos-v2`" lives in canonical-side automation (a CI hook, a `make publish-framework-only` target, or a post-commit subtree-split). If that automation breaks, the `framework-only` branch goes stale; workspace operators get an old framework on their next `pos-sync`. This is a maintenance discipline, not a correctness gap — `pos-sync` still works against whatever the branch holds. Alternatives 1, 2, 3, 5 all relocate the failure class in some way; Alternative 4's relocation is the smallest.

**Halt notes.** None of the five halt triggers in the dispatch fired. (1) ODD violations in own work — none. (2) ODD violations in surrounding code — none surfaced (the existing `pos-new-workspace` is clean; its scope-fence holds). (3) Scope creep into canonical-side restructure — surfaced as a candidate alternative and rejected (Alternative 5). (4) Composition break with `pos-sync` — surfaced and verified against each alternative; only Alternative 5 breaks it. (5) Validation gap with stranger-clones-canonical — surfaced and verified; the recommendation preserves the property.

---

## 1. The problem in concrete detail

### 1.1 Canonical's tree shape (HEAD `39cfbb1`)

```
ivers-corp-pos-v2/
  CLAUDE.md          # always-load corpus
  CLAUDE.dev.md      # dev-mode-only fragment (loam-mode reads)
  README.md          # repo entry-point doc
  docs/              # human-readable docs
    odd-methodology.md
    odd-in-pos.md
    rebuild/
      VALUE_PROPOSITION.md
      STATE.md
      FUTURE_IDEAS.md
      FUTURE_IDEAS_DRAFT.md
      plans/         # all amendment plans
        d-migration-*.md
        amendment-*.md
        ...
  framework/         # 16 sealed components + tools
    cost-governance/
    graceful-degradation/
    hands-off-lifecycle/
    memory-system/
    objective-tracker/
    observability-aggregator/
    orchestrator/
    primary-persona/
    reversibility-primitive/
    safety-layer/
    scope-of-work/
    self-correction/
    self-upgrade/
    telegram-interface/
    workspace-bootstrap/
    workspace-sync/
    tools/           # heavy-b-migrate, loam-mode, pos-amend, ...
```

### 1.2 What `pos-new-workspace` produces today (D.4-locked behaviour)

`pos-new-workspace <new-ws> --from <canonical>` runs (per `framework/workspace-bootstrap/src/workspace_bootstrap/new_workspace.py`):

```
git clone <canonical> <new-ws>/framework/
```

Result:
```
<new-ws>/
  framework/             # ← the cloned canonical, framework/.git/ tracking origin
    .git/                # canonical's git history
    CLAUDE.md            # ← landed at framework/CLAUDE.md, NOT <new-ws>/CLAUDE.md
    CLAUDE.dev.md        # ← framework/CLAUDE.dev.md
    README.md
    docs/                # ← framework/docs/
      odd-methodology.md
      rebuild/
        ...
    framework/           # ← DOUBLING: framework/framework/<comp>/
      cost-governance/
      ...
  workspace/             # scaffolded by run_first_run_scaffold (D.2)
    .pos/sync-config.yaml
    personas/<handle>/
    .mcp.json
    objective_tracker.sqlite
  .claude/               # scaffolded (D-Q.A4 lock — Claude Code expects it here)
  .gitignore             # framework/ + .claude/ tracked; everything else workspace-state
```

### 1.3 What the corpus-discovery readers expect

Two framework readers walk the workspace_root for top-level docs:

1. **`framework/primary-persona/src/session_start_gate.py:55`** — `discover_baseline_corpus(workspace_root)` reads `<workspace_root>/CLAUDE.md`'s session-start-discipline section, falls back to a hard-coded list of `docs/odd-methodology.md`, `docs/odd-in-pos.md`, `docs/rebuild/VALUE_PROPOSITION.md`, `docs/rebuild/STATE.md`, `docs/rebuild/FUTURE_IDEAS.md` when CLAUDE.md is missing. With doubling, all these resolve to non-existent paths under `<workspace_root>/`; the symlink-cosmetic on pos3 routes them through.

2. **`framework/primary-persona/src/session_start_gate.py:112`** — `enumerate_amendments_in_flight(workspace_root)` globs `<workspace_root>/docs/rebuild/plans/amendment-*.md`. Same behaviour: with doubling, plans are at `<workspace_root>/framework/docs/rebuild/plans/`; symlink workaround on pos3.

3. **`framework/hands-off-lifecycle/hooks/corpus_load_sentinel.py:186`** — reads `<workspace_root>/docs/rebuild/dev-mode-manifest.yaml`. Same shape.

4. **`framework/tools/loam-mode/src/loam_mode/session_start.py:192`** — `<workspace_root>/CLAUDE.dev.md` for the dev-mode auto-load partition. Same shape.

The pos3 workaround (commit `938b4c8`) creates symlinks at the workspace root (`<workspace>/CLAUDE.md → framework/CLAUDE.md`, `<workspace>/docs/odd-methodology.md → ../framework/docs/odd-methodology.md`, `<workspace>/docs/rebuild/STATE.md → ../../framework/docs/rebuild/STATE.md`, etc.). Three problems with the symlink workaround:

- It is hand-authored on pos3 only. Every future fresh workspace from `pos-new-workspace` would have to recreate all of them — and the tool doesn't.
- It is opaque: a Claude Code session running in `<new-ws>` sees broken corpus-discovery until the operator manually scaffolds the symlinks. The workspace looks scaffolded but doesn't function.
- It is fragile. The symlink targets relative paths into `framework/`; if pos-sync ever rearranges canonical's top-level files (e.g. canonical itself moves CLAUDE.md), every workspace's symlinks need re-authoring. Distance from "what humans browse on canonical" to "what readers find at workspace root" grows over time.

### 1.4 The fresh-checkout-of-canonical-from-GitHub validation requirement

The FUTURE_IDEAS_DRAFT entry the dispatch references names a property: a stranger should be able to `git clone <canonical-url>` from GitHub and have it "just work" — no bootstrap script required to make canonical browseable / inspectable / clone-able. The property exists because canonical IS the published thing; if cloning canonical requires `./bootstrap.sh` first, canonical's discoverability is gated on knowing about the script. The single-framework restructure must preserve this property: any candidate that requires running a setup script to make canonical itself usable is disqualified.

This rules out alternatives that would require, e.g., post-clone tree manipulation by the operator before the workspace is ready, or that would package canonical differently from its current shape (single git repo, browseable on GitHub).

---

## 2. Alternatives enumerated

### Alternative 1 — Two-clone composition (clone canonical for docs, clone `framework/` subdir for framework code)

**How it works.** `pos-new-workspace` runs two separate operations:

1. `git clone --depth 1 --filter=tree:0 --no-checkout <canonical> <new-ws>/.canonical-docs/` then `git -C .canonical-docs checkout HEAD -- CLAUDE.md CLAUDE.dev.md README.md docs/` (sparse checkout of just the top-level files).
2. `git clone <canonical> <new-ws>/framework/` (the existing flow).
3. Move the docs files OUT of `<new-ws>/.canonical-docs/` to the workspace root: `<new-ws>/CLAUDE.md`, `<new-ws>/docs/`, etc.

**Corpus-discovery behaviour.** Top-level docs land at `<workspace>/CLAUDE.md`, `<workspace>/docs/...`, `<workspace>/CLAUDE.dev.md` — exactly where the readers look. No reader changes.

**`pos-sync` story.** `pos-sync` runs `git fetch + git merge --ff-only` inside `<workspace>/framework/`. The workspace-root docs (`<workspace>/CLAUDE.md`, etc.) are NOT touched by `pos-sync` — they're a separate, independent copy of canonical's docs. **This is a regression:** when canonical's CLAUDE.md changes, `pos-sync` updates `<workspace>/framework/CLAUDE.md` (still doubled inside framework's clone) but NOT `<workspace>/CLAUDE.md`. The workspace-root copy goes stale. To fix, `pos-sync` would need a second sub-flow that re-syncs the docs — breaking the `git fetch + git merge --ff-only` invariant (now there are two sync mechanisms).

**Failure-class accounting.** RELOCATES the failure: doubling is gone but staleness is introduced. A future operator (or pos-sync itself) must remember to re-sync docs separately. Per ODD §5.1.1's elimination-over-relocation default, this is a worse structural shape than Alternative 4.

**Cost.** Medium. Two-clone bootstrap is ~30 lines added to `pos-new-workspace`. The pos-sync second-flow change is bigger (~150 LOC in `workspace-sync/cli.py`); it would also need its own AC and tests; AND the AC fixes a structural problem the alternative caused.

**Verdict.** Rejected — relocates the failure class.

### Alternative 2 — Sparse-checkout (single clone, restrict working-tree paths)

**How it works.** `pos-new-workspace` runs:

```
git clone --no-checkout <canonical> <new-ws>/framework/
git -C <new-ws>/framework sparse-checkout init --cone
git -C <new-ws>/framework sparse-checkout set framework/  # only check out framework/<comp>/
git -C <new-ws>/framework checkout HEAD
```

This produces a clone where `<new-ws>/framework/.git/` holds the full canonical history, but the working tree contains only `<new-ws>/framework/framework/<comp>/`. Top-level docs are NOT in the working tree (they're in the .git index but not on disk).

Then post-clone, the bootstrap copies the docs out via `git show HEAD:CLAUDE.md > <new-ws>/CLAUDE.md` (etc.).

**Corpus-discovery behaviour.** Top-level docs at `<workspace>/CLAUDE.md`, `<workspace>/docs/...`. Doubled framework path remains: `<workspace>/framework/framework/<comp>/`. So sparse-checkout fixes the docs problem but NOT the doubling.

**Variant 2b.** Sparse-checkout the OTHER way: include only top-level docs, exclude `framework/`. Then check out `framework/` separately at the workspace root. Two checkouts of the same `.git` directory — git supports this via `git worktree add`, but the worktrees share refs and branches, so a `pos-sync` git fetch + merge would have to coordinate two working trees. Loses the "single framework directory tracking origin" mental model that's load-bearing for D.3.

**`pos-sync` story.** Variant 2a: `pos-sync` operates on `<workspace>/framework/`'s sparse-checkout-restricted working tree. `git fetch + git merge --ff-only` should work, but `git merge --ff-only` may unexpectedly try to materialise excluded paths if they change upstream — requires careful sparse-checkout cone discipline. Variant 2b: two worktrees coordinating; pos-sync flow has to pick which.

**Failure-class accounting.** 2a: relocates (doubling persists; sparse-checkout is the operator's discipline). 2b: relocates (two-worktree coordination is its own discipline). Neither eliminates structurally.

**Cost.** Medium-high. Sparse-checkout flag handling is fiddly; cone-mode interaction with `git merge --ff-only` is testing-heavy.

**Verdict.** Rejected — neither variant eliminates the doubling.

### Alternative 3 — Operator-side mv on first sync (clone canonical, mv framework/framework/* to framework/, mv top-level docs to workspace root)

**How it works.** `pos-new-workspace` runs `git clone <canonical> <new-ws>/framework/`, then post-clone mutates the working tree:
- `mv <new-ws>/framework/framework/* <new-ws>/framework/`
- `rmdir <new-ws>/framework/framework`
- `mv <new-ws>/framework/CLAUDE.md <new-ws>/CLAUDE.md`
- (etc.)

Then commits the mv as a single workspace-side commit on `framework/.git`'s HEAD.

**`pos-sync` story.** **Catastrophic.** The next `git fetch + git merge --ff-only` against canonical fails because canonical's HEAD has different paths than the workspace's local HEAD. Recovery requires merge-conflict resolution on every `pos-sync` (every file moved is a divergence). Breaks D.3's locked invariant. Disqualified.

**Verdict.** Rejected — composition break with `pos-sync`.

### Alternative 4 — Subtree-split branch + bootstrap clones the framework-only branch (RECOMMENDED)

**How it works.** Canonical maintains a synthetic git branch (`framework-only`) whose tree IS canonical's `framework/` subdir promoted to repo root, plus the top-level docs (`CLAUDE.md`, `CLAUDE.dev.md`, `README.md`, `docs/`) brought along verbatim. The branch is generated automatically from `pos-v2` (canonical's primary branch) by either:

- `git subtree split --prefix=framework -b framework-only` followed by an explicit second commit that adds the docs files at the synthetic-branch root (subtree-split alone doesn't capture docs at root).
- A `make publish-framework-only` target (or pre-push hook, or CI workflow) that runs the synthesis script after every commit on `pos-v2`.
- A custom synthesis script (~50 LOC bash/python) that uses `git read-tree` + `git commit-tree` + `git update-ref` to construct the synthetic branch's commits without working-tree manipulation. Cleanest implementation.

The synthetic branch's tree:
```
<framework-only>/
  CLAUDE.md           # ← copied from canonical's pos-v2 branch root
  CLAUDE.dev.md
  README.md
  docs/               # ← copied from canonical's pos-v2 branch root
    odd-methodology.md
    rebuild/...
  cost-governance/    # ← was framework/cost-governance/ on pos-v2
  graceful-degradation/
  ...                 # all 16 sealed components + tools/
  workspace-bootstrap/
  workspace-sync/
  tools/
```

`pos-new-workspace --from <canonical>` is updated to clone the `framework-only` branch instead of canonical's default branch:

```
git clone --branch framework-only <canonical> <new-ws>/framework/
```

Workspace shape post-bootstrap:
```
<new-ws>/
  framework/                 # clone of framework-only branch
    .git/                    # tracks <canonical>/framework-only as origin
    CLAUDE.md                # ← single-level
    CLAUDE.dev.md
    README.md
    docs/...
    cost-governance/         # ← single-level: framework/cost-governance/
    graceful-degradation/
    ...
  workspace/                 # scaffolded as today
  .claude/
  .gitignore
```

**Corpus-discovery behaviour.** `<workspace>/CLAUDE.md` is missing — it's at `<workspace>/framework/CLAUDE.md`. Two sub-options for closing this:

- **(4a)** Update the four corpus-discovery readers to also probe `<workspace_root>/framework/CLAUDE.md` (etc.) when the workspace-root copy is missing. Reader changes; small surface (~4 files, each gets a one-line "fall through to framework/" path resolve).
- **(4b)** Have `pos-new-workspace` scaffold the symlinks once at bootstrap time (the same pos3-workaround pattern, but mechanised in the bootstrap so every fresh workspace gets them automatically). Adds ~10 LOC to `new_workspace.py` for the symlink-scaffold step. Readers unchanged.

**Recommendation: 4a.** Per Lens 1 (Claude-leverage) + ODD §5.1 (structural over advisory): an explicit reader-side fall-through is the structural shape; symlinks are operator-discipline (they could be deleted by the operator, by a later sync, etc.). 4a's reader change is the simplest realisation of "the framework documents are inside `framework/`, look there."

**`pos-sync` story.** `pos-sync` operates on `<workspace>/framework/`'s clone, which tracks `framework-only` as its `origin`. `git fetch + git merge --ff-only` runs against `framework-only`. Canonical-side, every commit on `pos-v2` triggers the synthesis pipeline, which advances `framework-only` to a corresponding new commit. The fast-forward invariant holds because the synthesis is deterministic and additive — every `pos-v2` commit produces a `framework-only` commit. Workspace's `pos-sync` is unchanged.

**Failure-class accounting (ODD §5.1.1):**
- **Eliminated:** doubling. The cloned tree's repo root IS the framework contents; there is no nested `framework/` subdir.
- **Eliminated:** corpus-discovery breakage (under 4a). Readers find docs at `<workspace>/framework/CLAUDE.md` because the resolver knows to look there. Adding a new top-level doc (`docs/foo.md`) on canonical's `pos-v2` branch propagates to `framework-only` automatically; readers find it at `<workspace>/framework/docs/foo.md`.
- **Eliminated:** symlink fragility. No symlinks; readers do path resolution explicitly.
- **Relocated (acceptable):** "publish `framework-only` in lockstep with `pos-v2`" — this is canonical-side maintenance discipline. The synthesis pipeline must run on every `pos-v2` commit. If it fails, `framework-only` goes stale; `pos-sync` from a workspace would not see the latest canonical until it's fixed. Mitigations: a pre-push hook or CI gate that refuses to push `pos-v2` if `framework-only` synthesis fails; a `make publish-framework-only` smoke test in canonical's test suite.

**Stranger-clones-canonical validation.** `git clone <canonical-url>` from GitHub still works — strangers see the `pos-v2` branch (default), browse the canonical tree as today. `git clone --branch framework-only <canonical-url>` is what `pos-new-workspace` runs internally; strangers can run it manually too, no bootstrap script required. Property preserved.

**Cost.** Medium. Estimated:
- Synthesis script: ~50–100 LOC (bash or python).
- Pre-push hook or CI gate: ~30 LOC.
- `pos-new-workspace` change: ~5 LOC (add `--branch framework-only` to the `git clone` call; the URL path stays the same; the local-path bootstrap path resolves the `framework-only` branch from the source repo).
- Reader changes (4a): ~4 files × ~5 LOC each = ~20 LOC + tests.
- Documentation: README + d-migration plan section.
- One-time manual setup of the `framework-only` branch on canonical the first time.

**Verdict.** **RECOMMENDED.** Eliminates the doubling failure class structurally; preserves `pos-sync`'s git-merge-ff-only invariant; preserves stranger-clones-canonical; the relocated discipline (synthesis pipeline) is bounded and testable.

### Alternative 5 — Canonical-side restructure (move framework/<comp>/ to <comp>/ at canonical root)

**How it works.** Canonical itself rearranges: `framework/cost-governance/` → `cost-governance/`, `framework/primary-persona/` → `primary-persona/`, etc. Top-level docs stay where they are. `framework/` subdir is deleted. The workspace's clone naturally produces `<workspace>/framework/cost-governance/` (single level) and `<workspace>/framework/CLAUDE.md`.

**Corpus-discovery.** Same as Alternative 4 — `<workspace>/framework/CLAUDE.md` etc. need reader fall-through OR symlinks. Same 4a/4b sub-options.

**`pos-sync` story.** Composes with `git fetch + git merge --ff-only` natively because there's only one canonical branch.

**The dispatch's halt-trigger #3.** "If the research suggests the right fix is a canonical-side restructure (rearranging canonical's own `framework/` subdir layout) rather than a `pos-new-workspace` change, halt and surface; that's a different amendment shape than what was authorized." Alternative 5 is exactly this case. **Halting and surfacing.**

**Comparison vs Alternative 4.** Both produce the same workspace-side shape post-bootstrap. Alternative 5 is structurally cleaner (no synthetic branch; no synthesis pipeline to maintain). Alternative 4 keeps canonical's `framework/<comp>/` structure intact (zero-impact on canonical's own browsing experience; humans browsing canonical on GitHub see the same shape they always have). Alternative 4 also keeps the D-architecture's logical separation: canonical IS the human-readable repo, `framework-only` IS the bootstrap surface.

**The two are equivalent on workspace-side outcomes.** Differences are on canonical-side maintenance burden:
- A4: synthesis pipeline; canonical's tree shape unchanged.
- A5: canonical's tree shape changes once; no synthesis pipeline; every reader/test/script in canonical that knows about `framework/<comp>/` needs to be updated to `<comp>/` (substantial — `framework/<comp>/` is mentioned in plan docs, manifests, gitignore patterns, hands-off-lifecycle's BASELINE diff windows, pos-amend's seal manifests, pretty much everywhere). One-time but huge.

**Recommendation.** **Surface Alternative 5 to the owner with a recommendation: STAY WITH ALTERNATIVE 4.** Reason: Alternative 5's "one-time" cost is in fact distributed across every existing plan doc, manifest, fence configuration, structural-guard test, etc. The D-architecture's three months of plans + 67 amendments + 16 sealed components all contain `framework/<comp>/` strings. The `pos-amend apply` machinery's regex would need updating; the `WorkspaceLayout` validator's basename refusal would need re-thinking; every sealed component's `tests/SEAL_COMMIT` walk-up would need re-validation. The cost is much higher than Alternative 4's synthesis-pipeline maintenance.

The dispatch's halt-trigger #3 fires explicitly. **Halting + surfacing as decision D2 below.**

### Alternative 6 — Reader-side framework-aware path resolution (no bootstrap change; readers walk both `<ws>/CLAUDE.md` and `<ws>/framework/CLAUDE.md`)

**How it works.** Bootstrap unchanged. The four corpus-discovery readers are updated to check `<workspace_root>/CLAUDE.md` first, then fall through to `<workspace_root>/framework/CLAUDE.md` if absent. Doubling at `<workspace>/framework/framework/<comp>/` REMAINS but is invisible to the readers.

**Corpus-discovery.** Closed via reader changes only.

**`pos-sync`.** Unchanged.

**Failure-class accounting.** Doubling is NOT eliminated; it's invisible. A future change anywhere in the codebase that reasons about `framework/<comp>/` paths from the workspace side (a new sealed-component test scaffold, a new launchd plist generator, a new diagnostic tool) is one mistake away from re-introducing doubled paths into observable behaviour. Per ODD §5.1.1: relocates rather than eliminates.

**Cost.** Lowest of all alternatives. ~20 LOC of reader changes. No canonical-side work.

**Verdict.** **NOT RECOMMENDED, but pragmatically tempting.** It's the cheapest patch; it makes the symptom go away. It is the same shape as the pos3 cosmetic-symlink-patch raised one level (instead of symlinks at the workspace root, the readers know about the doubled location). The cosmetic-symlink-patch on pos3 is the existing example of the relocation; Alternative 6 just moves the relocation from operator-discipline (manual symlinks) to framework-code-discipline (reader fall-through). Doubling at the filesystem level remains.

The temptation is real, however, and it's worth surfacing: if Alternative 4's synthesis pipeline turns out to be more expensive than estimated (e.g. hits unforeseen complexity around git refs / Claude Code session caching / GitHub-side branch protection rules), Alternative 6 is a viable Plan B that buys us time to do Alternative 4 later.

**Recommendation.** Surface as a fallback. Default is Alternative 4.

### Alternative 7 — Submodule (canonical's `framework/` becomes a git submodule pointing at a sibling repo)

**How it works.** Canonical's `framework/` subdir becomes a git submodule pointing at a separate `pos-v2-framework` repository. Strangers cloning canonical don't see framework code by default (`git clone`); they need `git clone --recurse-submodules` or `git submodule update --init`. `pos-new-workspace` clones the framework-submodule's repo directly, bypassing the parent canonical.

**Stranger-clones-canonical validation.** **VIOLATED.** A stranger doing `git clone <canonical-url>` from GitHub gets a tree with an empty `framework/` directory; they need to know to add `--recurse-submodules` to get the framework code. The dispatch's halt-trigger #5 fires.

**Verdict.** Rejected — fails the stranger-clones-canonical property.

---

## 3. Comparison matrix

| Alternative | Eliminates doubling? | Composes with pos-sync? | Stranger-clones-canonical works? | Cost (rough) |
|---|---|---|---|---|
| 1 — Two-clone composition | Yes (mostly) | NO (introduces doc-staleness) | Yes | Medium |
| 2 — Sparse-checkout | NO (relocates) | Risky (cone-mode interactions) | Yes | Medium-high |
| 3 — mv on first sync | Yes | NO (catastrophic) | Yes | Low (but unusable) |
| **4 — Subtree-split branch** | **Yes** | **Yes** | **Yes** | **Medium** |
| 5 — Canonical restructure | Yes | Yes | Yes | Very high (touches every plan/manifest) |
| 6 — Reader fall-through only | NO (relocates) | Yes | Yes | Lowest |
| 7 — Submodule | Yes | Yes (different mechanism) | NO | Medium |

---

## 4. Recommendation

**Adopt Alternative 4 (subtree-split branch).** Sub-option 4a (reader-side fall-through; no bootstrap-time symlinks).

**Rationale.** It is the only candidate that simultaneously:
- Eliminates the doubling failure class structurally (impossible to re-introduce without explicit canonical-side change);
- Composes with `pos-sync`'s `git fetch + git merge --ff-only` invariant (D.3 unchanged);
- Preserves the stranger-clones-canonical property (canonical's `pos-v2` branch is unchanged on GitHub; `framework-only` is a synthetic sibling, also browseable);
- Has a bounded, testable canonical-side cost (one synthesis pipeline + one pre-push gate).

**Decision flow vs Alternative 5.** Alternative 5 produces the same workspace-side outcome with a structurally simpler canonical, but at a one-time cost that touches every plan doc, manifest, fence rule, and structural test in the D-architecture's three-months of work. The dispatch's halt-trigger #3 fires. Surface to the owner as decision D2.

---

## 5. Lens analysis

**Lens 1 — Claude-leverage-first.** Alternative 4 leans on git's native subtree-split + branch primitives — both are in Claude's general knowledge surface. The synthesis pipeline can be a one-shot script the persona invokes, or a hand-authored Makefile target. No new MCP server or skill required. The reader-side fall-through is a stdlib change in primary-persona + loam-mode + hands-off-lifecycle (Python `Path` operations). Claude SDK isn't re-invented; existing Claude Code session-start hooks are unchanged.

**Lens 2 — Harness + primary-persona value.** Translation burden: today, an operator wanting a fresh workspace runs `pos-new-workspace` and gets a half-broken workspace (doubled paths + missing top-level docs the readers can't find). After Alternative 4, the same command produces a fully-functional workspace; the primary persona's session-start corpus discovery JustWorks. Harness toolkit: `pos-new-workspace` continues to be the harness primitive the persona invokes. Tests pass.

**Lens 3 — ODD authoring.** Objective: "fresh workspaces from `pos-new-workspace --from <canonical>` must produce single-level `framework/<comp>/` shape with corpus discovery functional." Three behaviours: clone-shape correct, corpus discovery functional, pos-sync composition unchanged. Three ACs (one per behaviour) plus one S-class structural-guard. ODD §5.1.1's elimination-over-relocation default is the structural-sharpening that picks Alternative 4 over Alternative 6.

---

## 6. Decisions for owner ruling

Per `feedback_summarize_and_surface_decisions`. Each decision has a recommendation; owner rules from this summary.

### D1 — Adopt Alternative 4 (subtree-split branch)?

**Recommendation: Yes.** It's the only alternative that eliminates the doubling structurally while preserving both `pos-sync` composition and stranger-clones-canonical. Cost is bounded (synthesis pipeline + small reader changes). Failure-class accounting: doubling becomes unrepresentable.

### D2 — Alternative 5 (canonical-side restructure) instead?

**Recommendation: No.** Same workspace-side outcome but distributed cost across every plan/manifest/test in the D-architecture's three-month history. The dispatch's halt-trigger #3 fires; surfacing it is an obligation. Recommendation lands at Alternative 4 because the cost is much smaller.

### D3 — Reader fall-through (4a) vs bootstrap-time symlinks (4b)?

**Recommendation: 4a (reader fall-through).** Per ODD §5.1: structural over advisory. A reader's path resolver knowing both `<workspace>/CLAUDE.md` and `<workspace>/framework/CLAUDE.md` is structural; symlinks are operator-discipline (could be deleted, could go stale on `pos-sync` if canonical's docs move). The reader-fall-through change is small (~20 LOC across 4 files); it's encoded once and cannot drift.

### D4 — Synthesis pipeline implementation (subtree-split vs custom commit-tree script vs Makefile target)?

**Recommendation: Custom commit-tree script (~50–100 LOC python).** `git subtree split --prefix=framework` doesn't carry top-level docs into the synthetic branch (subtree-split takes one prefix). A custom script using `git read-tree` + `git commit-tree` + `git update-ref` can construct the synthetic commit deterministically, taking both `framework/*` AND `CLAUDE.md`/`docs/`/`README.md` into the synthetic tree. Cleaner mental model than wrapping `git subtree split` with extra commits.

The script is invoked by a pre-push hook on canonical's `pos-v2` branch (refuses push if synthesis fails) and / or a Makefile target (`make publish-framework-only`) for manual invocation. Pre-push hook is the structural enforcement (the gate that prevents `pos-v2` from advancing without `framework-only` advancing in lockstep).

### D5 — Reader fall-through scope (4a sub-question): probe-and-prefer-workspace-root, or prefer-framework-root?

**Recommendation: probe-and-prefer-workspace-root.** When `<workspace>/CLAUDE.md` exists, use it (handles future workspaces that scaffold their own CLAUDE.md, e.g. dev-mode workspaces with workspace-specific overrides). When absent, fall through to `<workspace>/framework/CLAUDE.md`. Same pattern for `docs/`. This preserves the existing pos3 behaviour (its symlinks resolve to the framework copy; the reader sees the workspace-root path) while unblocking workspaces that don't have the symlinks.

### D6 — Apply this on pos3 immediately, or only on future fresh workspaces?

**Recommendation: Both.** The reader fall-through (4a) unblocks pos3 simultaneously: when the symlinks at `<pos3>/CLAUDE.md` etc. exist, they continue to work. If they were ever removed, the reader fall-through would still find the underlying docs at `<pos3>/framework/CLAUDE.md`. New workspaces from the post-restructure `pos-new-workspace` produce the same shape natively. pos3 can clean up its symlinks at leisure (cosmetic-only after the reader change lands).

### D7 — Branch name for the synthetic surface?

**Recommendation: `framework-only`.** Descriptive; matches the dispatch's "framework-only" framing; not a name conflict with any existing canonical or workspace branch. Alternative names considered: `bootstrap`, `pos-v2-framework`, `dist`. `framework-only` is clearest about its purpose.

---

## 7. Halt findings

None of the dispatch's five halt triggers fired during research, with one explicit surface: halt-trigger #3 (scope creep into canonical-side restructure) fired in alternative enumeration. The research surfaces it as a candidate, weighs it against the recommended alternative, and recommends Alternative 4 over Alternative 5 on cost grounds. The halt is honoured by surfacing the choice as decision D2 rather than by silently picking one or the other.

ODD self-checks (§8 of `docs/odd-methodology.md`):
- Method-in-acceptance: this is a research doc; no ACs authored here. Plan doc gets the ACs.
- Behaviour-count: not applicable (research surface).
- Halt trigger present: surfaced halt-trigger #3 in §2 Alternative 5 + decision D2.
- Constraints: research is read-only by directive; no method, no code edits, no test runs.
- §2.5 reverse direction: research has no code surface; no §2.5 violations possible.

---

## 8. References

- Dispatch directive (in-session, 2026-04-28).
- `docs/odd-methodology.md` (loaded; §5.1.1 relocate-vs-eliminate test was the load-bearing rule).
- `docs/rebuild/VALUE_PROPOSITION.md` (the prime objective the workspace bootstrap must serve).
- `docs/rebuild/FUTURE_IDEAS_DRAFT.md` (the dispatch references three D-cutover follow-on entries; the canonical-side draft does not yet contain them — pos3-side capture).
- `docs/rebuild/plans/d-migration-4.builder-plan.md` (D.4 / amendment #65 — the primitive being modified).
- `docs/rebuild/plans/d-migration-3.builder-plan.md` (D.3's `pos-sync = git fetch + git merge --ff-only` invariant).
- `framework/workspace-bootstrap/src/workspace_bootstrap/new_workspace.py` (the tool being modified).
- `framework/primary-persona/src/session_start_gate.py` (`discover_baseline_corpus`, `enumerate_amendments_in_flight`).
- `framework/hands-off-lifecycle/hooks/corpus_load_sentinel.py` (corpus-load partition reader).
- `framework/tools/loam-mode/src/loam_mode/session_start.py` (dev-extension reader).
- `framework/workspace-bootstrap/src/workspace_bootstrap/workspace_paths.py` (`WorkspaceLayout` structural-guard validator + `WORKSPACE_STATE_SUBDIR`).
- pos3 commit `938b4c8` (the pos3 D-shape cutover; canonical example of the doubling + the symlink workaround).
