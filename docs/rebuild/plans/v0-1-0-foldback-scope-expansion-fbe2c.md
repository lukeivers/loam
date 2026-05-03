# FBE.2c sub-plan — README + getting-started clone-line + 4 broken fixture tests

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-03.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` (FBE.2c row to be backfilled in §8 register; closing "Remaining sequence:" line currently lists FBE.5b only — re-shape post-seal).
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md`.
**Predecessors:** FBE.{1,2,2b,3,4,5,5b,7} all sealed (`21b9480`, `8d2b770`, `47ccb3a`, `becf183`, `99c03a6`, `bc56f0d`, `ea6fad1` (FBE.5b apply; seal pending FBE.2c), `a102bde`).
**BASELINE (pre-build tip):** `ea6fad1` — current canonical pos-v2 HEAD (the FBE.5b apply commit; FBE.5b's seal is gated on FBE.2c per FBE.5b's halt-and-surface).

---

## 1. Summary / TLDR

FBE.5b halted at `loam amend seal` because FBE.2b's prefix-preserving synth change introduced a doc-vs-runtime collision that surfaces both as 4 failing fixture tests AND as a real production install-flow defect.

**The defect.** Pre-FBE.2b: synth's `framework-only` branch carried bare-component paths at root (`workspace-sync/...`, `tools/loam/...`, `CLAUDE.md`, `docs/...`). The documented `git clone https://github.com/lukeivers/loam framework/` call cloned that branch INTO a `framework/` subdir, producing single-level workspace shape `<workspace>/framework/<comp>/...`. Post-FBE.2b: synth retains `framework/` prefix on shipped paths (`framework/workspace-sync/...`, `framework/tools/loam/...`), so cloning the same branch INTO `framework/` produces DOUBLED shape `<workspace>/framework/framework/<comp>/...`. Verified empirically (this turn): a fresh `bootstrap_new_workspace` against a fixture canonical produces `/.../new-ws/framework/framework/workspace-sync/src/workspace_sync/__init__.py`.

**Path α (dispatcher-locked).** Keep FBE.2b's synth shape (semantically richer; matches the docs that reference `framework/<comp>/`); drop the `framework/` arg from `git clone` in `README.md` + `docs/getting-started.md` so the documented flow becomes `git clone <repo>` → `cd loam`. The post-clone working directory is then the loam framework root, so cross-references to `framework/<comp>/` paths in the rest of the docs (e.g. `pip install -e framework/tools/loam`) STAY correct relative to the new working directory. The 4 failing tests assert the OLD single-level shape; update them to assert the NEW doubled shape (the source-side contract for `bootstrap_new_workspace` is unchanged — it still clones canonical INTO `<new-ws>/framework/`; the doubling is a deliberate consequence of FBE.2b + the existing bootstrap clone target).

**The 4 failing tests** (verified failing this turn against `ea6fad1`):

1. `framework/workspace-bootstrap/tests/test_pos_new_workspace.py::test_AC_D_4_1_local_canonical_creates_working_workspace` — `fixture_pairs` workspace-side paths point at single-level locations that no longer exist (`framework/workspace-sync/src/...`); also asserts `not (new_ws / "framework" / "framework").exists()` which post-FBE.2b is the wrong contract for components.
2. `framework/workspace-bootstrap/tests/test_pos_new_workspace.py::test_AC_D_4_1_url_form_routes_through_cache_clone` — reads `(new_ws / "framework" / "README.md")` which post-FBE.2b lives at `(new_ws / "framework" / "framework" / "README.md")`.
3. `framework/workspace-bootstrap/tests/test_AC_SFR_1_single_framework_directory.py::test_AC_SFR_1_single_level_framework_directory` — asserts `(framework / "workspace-sync").is_dir()` which is now `(framework / "framework" / "workspace-sync").is_dir()`; also asserts no doubling.
4. `framework/workspace-bootstrap/tests/test_AC_SFR_5_stranger_clones_canonical.py::test_AC_SFR_5_framework_only_reachable_via_explicit_branch` — asserts `all(not p.startswith("framework/") for p in paths)` against the framework-only branch tree, which is the inverse of FBE.2b's actual contract.

**Empirical evidence (this turn, fresh probe).** Against current HEAD `ea6fad1` with fixture canonical built via `_make_fixture_canonical`:

- `git ls-tree -r --name-only framework-only` → `CLAUDE.md`, `docs/odd-methodology.md`, `framework/README.md`, `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`, `framework/workspace-bootstrap/src/workspace_bootstrap/__init__.py`, `framework/workspace-sync/src/workspace_sync/__init__.py`. Top-level docs (`CLAUDE.md`, `docs/`) are at synth-tree root because they were never under `framework/` in pos-v2; component leaves keep their `framework/` prefix.
- `bootstrap_new_workspace` produces:
  - `<new-ws>/framework/CLAUDE.md` (single-level; top-level doc)
  - `<new-ws>/framework/docs/odd-methodology.md` (single-level; top-level doc)
  - `<new-ws>/framework/framework/README.md` (DOUBLED; the original `framework/README.md` from pos-v2)
  - `<new-ws>/framework/framework/workspace-sync/src/workspace_sync/__init__.py` (DOUBLED; component leaf)
  - `<new-ws>/framework/framework/workspace-bootstrap/src/workspace_bootstrap/__init__.py` (DOUBLED; component leaf)
  - `<new-ws>/framework/framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` (DOUBLED; component leaf)

The doubling is structural for component leaves; top-level docs stay single-level.

**Why the README fix matters at runtime, not just the fixture tests.** The `loam init` programmatic path is unchanged — it clones canonical's framework-only branch INTO `<new-ws>/framework/`, yielding the doubled shape. But that's fine for the `loam init` flow because `loam init` is what the user runs AFTER cloning the loam repo for the install — so `loam init` is internal to a workspace whose contents are tooling's choice. The READ.md / getting-started.md text describes what a stranger does to GET the loam tooling installed in the first place: they `git clone`, then `pip install -e framework/tools/loam`. Pre-FBE.2c the README's `git clone <repo> framework/` clones the default branch (`pos-v2`) into a `framework/` subdir of the user's chosen workspace dir → single-level `<ws>/framework/tools/loam/...` → `pip install -e framework/tools/loam` works. Post-FBE.2b we want the same: a `framework/<comp>/...` install path. The simplest doc-only fix: drop the `framework/` arg, let `git clone` create a `loam/` directory by default, the user `cd loam` into it, and `pip install -e framework/tools/loam` resolves against the cloned framework root. (The `loam init` step then bootstraps a workspace whose internal `<ws>/framework/...` shape uses the same DOUBLED-component shape — but that's an internal `loam init` contract the user doesn't see.)

This is **single sealed-component fence** amendment: `framework/workspace-bootstrap/` (the 3 broken fixture-test files) plus universal admissions for `README.md` + `docs/getting-started.md`.

**Note on §8 register backfill:** the parent foldback plan-doc names FBE.2c only implicitly (its closing line lists "FBE.5b ... if dispatched → FBE.6 ..."; FBE.2c is inserted post-FBE.5b's halt). Full §8 register entry will be added at backfill time via the universal-paths admission (post-seal commit, mirroring FBE.2b/FBE.5b precedent).

---

## 2. Halt-and-surface BEFORE build

### Surface #1 (no halt — recorded; the doubled shape is the new contract for the workspace-bootstrap-cloned subtree)

The dispatcher's brief locks "fix the tests, don't fix the source." The source-side contract for `bootstrap_new_workspace` post-FBE.2c is: clone canonical's `framework-only` branch INTO `<new-ws>/framework/`, yielding `<new-ws>/framework/framework/<comp>/...` for component leaves and `<new-ws>/framework/<top-level-doc>` for top-level docs. The 4 failing tests' assertions need to flip on the doubling check and update path literals; nothing in `new_workspace.py` source code needs to change.

This commits to the doubled shape as the post-FBE.2c contract for `loam init`-bootstrapped workspaces. Note that the user-facing flow (per the dispatcher's locked Path α) is `git clone <repo>` → `cd loam` → `pip install -e framework/tools/loam` → `loam init .` — that flow does NOT exhibit the doubling at the user's CWD because `git clone` (no second arg) creates a directory whose name is the repo name (`loam`), and inside that directory `framework/<comp>/...` is single-level (the framework-only branch's content sits directly inside the cloned `loam/` dir). The doubling only appears inside `<workspace>/framework/...` after `loam init` runs — which is an internal layout the user doesn't have to navigate by hand.

### Surface #2 (no halt — recorded; AC.SFR.1's "single level" naming becomes stale post-FBE.2c)

`test_AC_SFR_1_single_framework_directory.py::test_AC_SFR_1_single_level_framework_directory` is named for the OLD contract ("single level"). Post-FBE.2c, the test's body asserts the NEW DOUBLED contract. Renaming the test would expand scope (cross-file rename) and trigger more touched-file diff. **Decision:** keep the file name; tighten the docstring + comments to describe the new contract; add an inline note at the top of the file pointing to FBE.2c's parent plan §8 entry. ODD §2.5 is preserved by binding the body to a NEW AC (`AC.FBE.2c.3`) whose text describes the doubled shape; the old "single level" wording in the file/test name is a documentation artifact that the dispatcher's "no broader doc rewrites" halt trigger forbids fixing in this amendment. (Future amendment can rename if the dispatcher rules.)

### Surface #3 (no halt — recorded; `test_AC_SFR_5_framework_only_reachable_via_explicit_branch` body inverts on the same line FBE.2b's plan called out)

The test asserts `all(not p.startswith("framework/") for p in paths)` for the framework-only branch tree. Pre-FBE.2b that was correct (synth stripped the `framework/` prefix). Post-FBE.2b, FBE.2b's own AC.FBE.2b.5 explicitly describes the negation: "the no doubled framework/ prefix assertion (`assert all(not p.startswith("framework/") for p in paths)`) flipped to its negation (at-least-one-framework-prefixed-leaf for shipping components)". FBE.2b updated this assertion in the synth-pipeline tests inside `framework/tools/pos-publish-framework-only/tests/`, but the workspace-bootstrap test at `framework/workspace-bootstrap/tests/test_AC_SFR_5_stranger_clones_canonical.py:133` was NOT updated in FBE.2b's fence (single-fence: pos-publish-framework-only). FBE.2c updates the workspace-bootstrap mirror.

### Surface #4 (no halt — recorded; README + getting-started edits are the smallest possible doc-prose-only edits to close Path α)

The dispatcher's halt trigger #2 forbids broader doc rewrites. The minimal edit set:

- **README.md** lines 33-44 (§Quickstart code block):
  - Drop the `mkdir my-loam-workspace && cd my-loam-workspace` line (no longer needed; `git clone` will create the directory).
  - Change `git clone https://github.com/lukeivers/loam framework/` → `git clone https://github.com/lukeivers/loam` + new line `cd loam`.
  - Comment line 33 `# 1. Clone loam into a fresh workspace's framework directory.` → `# 1. Clone loam.`
  - Lines 37-44 (`pip install -e framework/tools/loam`, `loam init .`, `claude`) STAY — they're correct relative to the post-`cd loam` CWD.

- **docs/getting-started.md** §1 + §2 (lines 41-67):
  - §1 ("Create a fresh workspace") + §2 ("Clone loam into the workspace's framework directory") collapse into a single §1 ("Clone loam"). The `mkdir -p ~/loam-demo && cd ~/loam-demo` block is dropped; the `git clone` block changes to `git clone https://github.com/lukeivers/loam` + `cd loam`. Step numbers 3-6 renumber to 2-5; §3-§6 headings + bodies stay byte-identical aside from the renumbering. The "What just happened" §'s `Five shell commands` (line 132) updates to match the new step count.
  - The "common first-run problems" reference at line 175 (`pip install -e framework/tools/loam`) STAYS — same install path, just executed from the `loam/` cloned directory's CWD.
  - Line 186's `framework/primary-persona/` path STAYS — relative to workspace root, same path post-FBE.2c.

These are the smallest edits that achieve Path α without drifting into prose-rewrite territory. The narrative shape (workspace = your dir, framework = loam's contribution) implicitly shifts because the cloned `loam/` dir IS now both the framework root AND the workspace root for `loam init .`. The dispatcher's brief authorises this collapsing as adjacent prose; deeper architectural framing (e.g. extracting workspace from framework) is R.x territory.

### Surface #5 (no halt — recorded; smoke verification will exercise the documented flow against the synth tree, not against fixture canonical)

Acceptance #4 specifies: "cloning the synth's framework-only branch WITHOUT a `framework/` arg produces a single-level `<clone>/framework/<comp>/...` shape (no doubling)". The smoke uses the real canonical pos-v2 clone target (or its synth re-run) — the framework-only branch carries `framework/<comp>/...` paths, so a no-`framework/` clone creates `loam/` directory whose contents include `framework/<comp>/...` at single-level relative to `loam/`. The smoke documents this against a fresh `git clone` into `/tmp/`.

### Surface #6 (no halt — recorded; FBE.5b's apply commit `ea6fad1` is on disk; FBE.2c builds on top)

FBE.5b's apply commit landed; seal aborted. FBE.2c's BASELINE is `ea6fad1` (post-FBE.5b apply). After FBE.2c seals, the dispatcher re-runs `loam amend seal` against FBE.5b's manifest — at that point the 4 failing tests pass, and FBE.5b's seal can complete. (FBE.5b's `BASELINE` literal in `framework/workspace-bootstrap/tests/test_no_sealed_amendments.py` was bumped to `49604a9` by `loam amend apply`; FBE.2c's apply will bump it again to FBE.2c's pre-apply tip.)

### Surface #7 (no halt — recorded; partner-prefix derivation gap precedent — single component, canonical shape, low risk)

Per FBE.4/FBE.5/FBE.5b precedent: `loam amend apply` derives partner_prefixes assuming `framework/<name>/` for every fence component. `workspace-bootstrap` lives at `framework/workspace-bootstrap/` (canonical shape) — apply tool should derive cleanly with no corrective needed. Mirror FBE.5b's apply outcome (no corrective). If a corrective is needed at apply, mirror FBE.4's recipe (`0c4d9a0`).

---

## 3. Spec-objective placement

**Binds to:**
- **AC.PO.1 + AC.PO.2** (prime objective per `docs/rebuild/VALUE_PROPOSITION.md`) — the documented install path must produce a working `pip install -e framework/tools/loam` outcome for a stranger reading the README. Pre-FBE.2c: the documented `git clone <repo> framework/` produces `<ws>/framework/<comp>/...` from the default `pos-v2` branch (which carries `framework/<comp>/...`); but the bootstrap's framework-only clone produces doubled `<ws>/framework/framework/<comp>/...`. Post-FBE.2c: `git clone <repo>` produces `loam/` directory with `framework/<comp>/...` at top level; the install command resolves correctly.
- **Reviewer foldback HIGH 1 + Decision D follow-through** — the synth-shape side closed at FBE.2b; the doc-and-test-shape side closes at FBE.2c.
- **AC.FBE.2c.* (this plan §4)** — every AC ladders to the same parent.

**Ladders to:** AC.FBE.2c.* → unblocks FBE.5b seal → AC.FBE.6.{1..N} (extended smoke + reviewer re-run) → AC.OSS-M11a.* (FBE.6 reviewer GO) → M12 publish-flip → AC.PO.1 + AC.PO.2.

---

## 4. Acceptance criteria (FBE.2c.*)

AC family `AC.FBE.2c.*` — collision-safe (verified: no prior amendment uses `AC.FBE.2c.*`).

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.FBE.2c.1** | `README.md`'s Quickstart code block no longer carries `git clone https://github.com/lukeivers/loam framework/`. The new shape: `git clone https://github.com/lukeivers/loam` + `cd loam` (two lines replacing one). The `mkdir my-loam-workspace && cd my-loam-workspace` line is dropped (the `git clone` no-arg form creates the directory). The comment at line 33 changes from "Clone loam into a fresh workspace's framework directory." to "Clone loam.". Lines 37-44 (`pip install -e framework/tools/loam`, `loam init .`, `claude`) byte-unchanged. | `grep -n "git clone https://github.com/lukeivers/loam framework/" README.md` returns 0 hits; `grep -n "git clone https://github.com/lukeivers/loam$" README.md` returns 1 hit; `grep -n "^cd loam$" README.md` returns 1 hit; `grep -n "pip install -e framework/tools/loam" README.md` returns 1 hit (unchanged). |
| **AC.FBE.2c.2** | `docs/getting-started.md`'s steps §1 + §2 collapse into a single §1 ("Clone loam"); the `mkdir -p ~/loam-demo && cd ~/loam-demo` block is dropped; the `git clone https://github.com/lukeivers/loam framework` line becomes `git clone https://github.com/lukeivers/loam` + `cd loam`. Step headings 3-6 renumber to 2-5. The "What just happened" prose updates "Five shell commands" / "five-step bootstrap" → "Five-step bootstrap" / "Five shell commands" stays consistent (verify exact byte at edit time). The references at line 175 (`pip install -e framework/tools/loam`) and line 186 (`framework/primary-persona/`) byte-unchanged. The "Six-step bootstrap" header at line 41 → "Five-step bootstrap". The Step §3 + §4 + §5 + §6 headings renumber to §2 + §3 + §4 + §5. | `grep -n "git clone https://github.com/lukeivers/loam framework$" docs/getting-started.md` returns 0 hits; `grep -n "git clone https://github.com/lukeivers/loam$" docs/getting-started.md` returns 1 hit; `grep -n "^cd loam$" docs/getting-started.md` returns 1 hit; `grep -n "Six-step bootstrap" docs/getting-started.md` returns 0 hits; `grep -n "Five-step bootstrap" docs/getting-started.md` returns 1 hit; `grep -n "pip install -e framework/tools/loam" docs/getting-started.md` returns 2 hits (one in §2 install, one in §"Common first-run problems" — both unchanged in their respective bodies). |
| **AC.FBE.2c.3** | `framework/workspace-bootstrap/tests/test_AC_SFR_1_single_framework_directory.py::test_AC_SFR_1_single_level_framework_directory` passes against current `bootstrap_new_workspace` source (unchanged). The body asserts post-FBE.2b shape: components at `<new-ws>/framework/framework/<comp>/`, doubling presence (NOT absence), top-level docs at `<new-ws>/framework/<doc>`. The function-level docstring + the file-level module docstring updates to describe the new contract; the OLD "no doubling" / "single level" wording inside the assertion comments is replaced with FBE.2c's "post-FBE.2b doubled-component shape" framing. | `pytest framework/workspace-bootstrap/tests/test_AC_SFR_1_single_framework_directory.py::test_AC_SFR_1_single_level_framework_directory` returns PASS. The other 3 tests in the file (`test_AC_SFR_1_byte_content_match_against_pos_v2`, `test_AC_SFR_1_workspace_tracks_framework_only_branch`, `test_AC_SFR_1_failure_when_framework_only_absent`) continue to pass (verified PASS at planning-time — they don't assert the no-doubling claim). |
| **AC.FBE.2c.4** | `framework/workspace-bootstrap/tests/test_AC_SFR_5_stranger_clones_canonical.py::test_AC_SFR_5_framework_only_reachable_via_explicit_branch` passes. The `assert all(not p.startswith("framework/") for p in paths)` assertion flips to assert `any(p.startswith("framework/") for p in paths)` (i.e. at-least-one framework-prefixed leaf in the framework-only tree). The "Top-level docs at root" assertion (`assert "CLAUDE.md" in paths`) stays unchanged (top-level docs remain at synth-tree root post-FBE.2b). | `pytest framework/workspace-bootstrap/tests/test_AC_SFR_5_stranger_clones_canonical.py::test_AC_SFR_5_framework_only_reachable_via_explicit_branch` returns PASS. The other test in the file (`test_AC_SFR_5_stranger_clone_byte_identical_to_pos_v2`) continues to pass (it asserts pos-v2 default-branch content unchanged — orthogonal). |
| **AC.FBE.2c.5** | `framework/workspace-bootstrap/tests/test_pos_new_workspace.py::test_AC_D_4_1_local_canonical_creates_working_workspace` passes. The `fixture_pairs` workspace-side paths update for COMPONENT leaves only: `("framework/workspace-sync/src/workspace_sync/__init__.py", "framework/framework/workspace-sync/src/workspace_sync/__init__.py")`, `("framework/workspace-bootstrap/src/workspace_bootstrap/__init__.py", "framework/framework/workspace-bootstrap/src/workspace_bootstrap/__init__.py")`, `("framework/README.md", "framework/framework/README.md")`. Top-level doc pairs unchanged: `("docs/odd-methodology.md", "framework/docs/odd-methodology.md")`, `("CLAUDE.md", "framework/CLAUDE.md")`. The post-`fixture_pairs` block's no-doubling assertion `assert not (new_ws / "framework" / "framework").exists()` flips to `assert (new_ws / "framework" / "framework").is_dir()` (the doubled directory MUST exist for component leaves to land). | `pytest framework/workspace-bootstrap/tests/test_pos_new_workspace.py::test_AC_D_4_1_local_canonical_creates_working_workspace` returns PASS. The remaining 11 tests in `test_pos_new_workspace.py` continue to pass byte-unchanged. |
| **AC.FBE.2c.6** | `framework/workspace-bootstrap/tests/test_pos_new_workspace.py::test_AC_D_4_1_url_form_routes_through_cache_clone` passes. The `(new_ws / "framework" / "README.md").read_text()` access updates to `(new_ws / "framework" / "framework" / "README.md").read_text()` to find the doubled location of the original `framework/README.md`. | `pytest framework/workspace-bootstrap/tests/test_pos_new_workspace.py::test_AC_D_4_1_url_form_routes_through_cache_clone` returns PASS. |
| **AC.FBE.2c.7** | Smoke verification: a fresh `git clone <local-canonical> /tmp/fbe2c-clone-smoke --branch framework-only` (no `/framework` second arg, no `framework/` arg) produces `/tmp/fbe2c-clone-smoke/framework/<comp>/...` at single-level (no doubling at `<clone>/framework/framework/`). This documents the user-visible flow that Path α targets. Cleanup post-verify. | Manual `git clone --branch framework-only /Users/lukeivers/ivers-corp-pos-v2/ /tmp/fbe2c-clone-smoke` (or against fixture canonical if real-canonical's framework-only is pre-FBE.2b — verify path at smoke time); `find /tmp/fbe2c-clone-smoke -type d -name framework` returns one result `<clone>/framework`; `ls /tmp/fbe2c-clone-smoke/framework/` shows `<comp>/` directories. Result documented in the FBE.2c status file. |
| **AC.FBE.2c.8** | Negative AC — no scope expansion. The fix touches ONLY: README.md (Quickstart §code block + the "Clone loam" comment), docs/getting-started.md (§1 + §2 collapse + step renumber + the "Five-step" prose + the "Six-step bootstrap" heading), the 3 broken fixture-test files (the assertions + literal paths + docstring tightening for AC.FBE.2c.{3,4,5,6}), and the FBE.2c sub-plan + manifest + parent §8 backfill. Specifically NOT touched: `framework/workspace-bootstrap/src/`, any other test file in the workspace-bootstrap fence, any other component, the loam-init CLI, the synth pipeline, any other doc file. | `git diff BASELINE..SEAL_COMMIT --stat` shows changes only in: `README.md`, `docs/getting-started.md`, `framework/workspace-bootstrap/tests/test_pos_new_workspace.py`, `framework/workspace-bootstrap/tests/test_AC_SFR_1_single_framework_directory.py`, `framework/workspace-bootstrap/tests/test_AC_SFR_5_stranger_clones_canonical.py`, `framework/workspace-bootstrap/tests/SEAL_COMMIT`, `framework/workspace-bootstrap/tests/SEAL_COMMIT.notes`, `framework/workspace-bootstrap/tests/test_no_sealed_amendments.py` (BASELINE bump), and the plan-doc + manifest + parent §8 backfill files in `docs/rebuild/plans/`. |
| **AC.FBE.2c.S** | Sealed-component fence: SINGLE component, `framework/workspace-bootstrap/`. Universal admissions for `README.md` + `docs/getting-started.md` (already in workspace-bootstrap's `allowed_files` list — no admission edit needed). | `git diff BASELINE..SEAL_COMMIT --name-only` produces only paths under: (a) `framework/workspace-bootstrap/`, (b) `docs/rebuild/plans/`, plus the two doc files (`README.md` + `docs/getting-started.md`) — all admitted in workspace-bootstrap's fence-test. |

**ACs deliberately out of scope (NOT in FBE.2c):**
- Renaming `test_AC_SFR_1_single_level_framework_directory` (the file name + test function name carry "single_level" but post-FBE.2c the contract is doubled — rename = scope creep per dispatcher halt trigger #2).
- Renaming the AC family `AC.SFR.1` → something else (same reasoning).
- Editing `framework/workspace-bootstrap/src/` source (Path α explicitly forbids; halt trigger #3).
- Editing `framework/loam-init/` or any other component source.
- Editing the synth pipeline or any path-shaping logic.
- Broader README rewrites (e.g. extracting "workspace" vs "framework" framing, or revising the "Why" / "What ships" sections).
- Broader getting-started.md rewrites (e.g. revising the "What just happened" section beyond the step-count number).
- Editing the CLI summary message at `framework/loam-init/src/loam/loam_init/cli.py:128` (`"  framework/  ← clone of ..."`) — same intent: leave runtime prose untouched, the README doc-edit handles the user-facing surface.
- Editing the parent plan §8 register format (only the FBE.2c subsection is added; `Remaining sequence:` line drops FBE.2c).

---

## 5. Three-lens analysis

### Lens 1 — Claude-leverage-first
This is a doc-prose + test-assertion fix; no Claude-native primitive applies directly. The fix preserves the existing Claude-Code-native composition (workspace `.claude/` from FBE.5b, hooks from future amendments) — Path α picks the lower-touch resolution that doesn't disturb Claude composition.

### Lens 2 — Harness + primary-persona value
- **Primary-persona test:** PASS. The user-facing translation burden drops materially: pre-FBE.2c the documented `git clone <repo> framework/` doesn't actually leave the user in a working state for `pip install` because the clone target is buried inside their workspace dir; post-FBE.2c the simpler `git clone <repo>` + `cd loam` puts them directly in a working tree where the documented install command resolves correctly.
- **Harness test:** PASS (preserve). No new toolkit primitive added; the existing toolkit's structural promise (cloned tree carries `framework/<comp>/...` per FBE.2b's synth contract) becomes consistent with the documented install path.

### Lens 3 — ODD authoring
Outcome ACs only (§4); method (which exact line of the README to edit, which exact pytest assertions to flip) is the builder's call but constrained by the existing test bodies + AC text. The "no doubling" → "doubling-required" inversion in two specific assertions is the prime outcome; "use a sed-equivalent rewrite" or "hand-edit" is method, NOT in the AC text.

### Lens 4 — Prompt scope ↔ confidence
High confidence in outcome shape: dispatcher named the failing tests + the README/getting-started change shape + the locked Path α. Tight scope. Method is inferable from constraints (drop one arg from `git clone`, flip one assertion per failing test, update path literals to the new doubled location). The acceptance criteria pin the outcome at the assertion level.

### Lens 5 — Swarming
FBE.2c is a leaf. ACs don't partition further: each AC binds to a single observable surface (one doc-file edit, one test-file pass, one fence-diff). No sub-decomposition; the source change is ~10 line-edits + 4 test-assertion flips + 1 sidecar bump.

---

## 6. File-by-file map

### Doc edits (universal admission via workspace-bootstrap's `allowed_files` for `README.md` + `docs/getting-started.md`):

- **`README.md`** — Quickstart code block (lines 32-45). Replace:
  ```bash
  # 1. Clone loam into a fresh workspace's framework directory.
  mkdir my-loam-workspace && cd my-loam-workspace
  git clone https://github.com/lukeivers/loam framework/
  ```
  with:
  ```bash
  # 1. Clone loam.
  git clone https://github.com/lukeivers/loam
  cd loam
  ```
  Lines 37-44 (`pip install -e framework/tools/loam`, `loam init .`, `claude`) byte-unchanged.

- **`docs/getting-started.md`** — collapse §1 (lines 45-54) + §2 (lines 56-67) into a single §1. Specifically:
  - Replace "## Six-step bootstrap" (line 41) with "## Five-step bootstrap".
  - Replace "The whole walkthrough is six shell commands. Run them in order." (line 43) with "The whole walkthrough is five shell commands. Run them in order."
  - Drop §1 "### 1. Create a fresh workspace" + body (lines 45-54).
  - Replace §2 heading "### 2. Clone loam into the workspace's framework directory" with "### 1. Clone loam".
  - Drop the §2 explanatory paragraph (lines 58-60) — the "loam ships as a Git repository the workspace mounts under `framework/`. The workspace itself is *yours*..." narrative no longer holds (workspace IS the cloned dir).
  - Replace the §2 code block (lines 62-64):
    ```bash
    git clone https://github.com/lukeivers/loam framework
    ```
    with:
    ```bash
    git clone https://github.com/lukeivers/loam
    cd loam
    ```
  - Replace the §2 trailing prose (lines 66-67) "You should see `framework/` populated with the loam component tree (`framework/primary-persona/`, `framework/safety-layer/`, and so on)." with "You should see the cloned `loam/` directory populated with the loam component tree (`framework/primary-persona/`, `framework/safety-layer/`, and so on) — `cd loam` puts you at the framework root for the next step." (Adjacent prose; describes what the user sees post-edit.)
  - Renumber §3 → §2, §4 → §3, §5 → §4, §6 → §5 (the "### N. <name>" headings) and the closing "Six-step" → "Five-step" mention in the "What just happened" section if present (verify at edit time).
  - Update line 132's "Five shell commands" → "Five shell commands" (already says five — verify; the original §3-§6 are 4 commands, plus §2's `git clone` + `cd loam` = effectively 5 commands; matches "five" already; leave unchanged if so).

### Test edits (in-fence; `framework/workspace-bootstrap/`):

- **`framework/workspace-bootstrap/tests/test_pos_new_workspace.py`** — single function `test_AC_D_4_1_local_canonical_creates_working_workspace` (lines 99-243):
  - Update `fixture_pairs` (lines 130-145) workspace-side paths for COMPONENT leaves: prepend `"framework/"` so `framework/workspace-sync/...` → `framework/framework/workspace-sync/...`, `framework/workspace-bootstrap/...` → `framework/framework/workspace-bootstrap/...`, `framework/README.md` → `framework/framework/README.md`. Top-level doc pairs (`docs/odd-methodology.md`, `CLAUDE.md`) unchanged.
  - Tighten the comment block (lines 122-129) to describe the post-FBE.2c contract (cite FBE.2b for the synth-side doubling cause + FBE.2c's parent §8 entry as the workspace-side commitment).
  - Flip the no-doubling assertion (lines 155-161): replace `assert not (new_ws / "framework" / "framework").exists()` (and its f-string) with `assert (new_ws / "framework" / "framework").is_dir()` plus an updated f-string explaining FBE.2c's contract ("post-FBE.2b doubled-component shape required at this path for component leaves to land"). Reference `AC.FBE.2c.5`.

- **`framework/workspace-bootstrap/tests/test_pos_new_workspace.py`** — single function `test_AC_D_4_1_url_form_routes_through_cache_clone` (lines 284-350):
  - Update line 339's `_read_canonical_blob(canonical, "framework/README.md")` left-hand path STAYS (it's a canonical-side `git show HEAD:framework/README.md` — pos-v2 default branch carries `framework/README.md` byte-unchanged).
  - Update line 340-342's `(new_ws / "framework" / "README.md").read_text()` to `(new_ws / "framework" / "framework" / "README.md").read_text()`. Adjacent inline comment (lines 333-337) updates to describe the post-FBE.2b doubled-component contract; cite `AC.FBE.2c.6`.

- **`framework/workspace-bootstrap/tests/test_AC_SFR_1_single_framework_directory.py`** — single function `test_AC_SFR_1_single_level_framework_directory` (lines 77-117):
  - Update component-existence assertions (lines 104-105): `(framework / "workspace-sync").is_dir()` → `(framework / "framework" / "workspace-sync").is_dir()`; same for `workspace-bootstrap`.
  - Flip no-doubling assertion (lines 109-113): replace `assert not (framework / "framework").exists()` + f-string with `assert (framework / "framework").is_dir()` + new f-string.
  - Top-level doc assertions (lines 116-117) STAY unchanged: `(framework / "CLAUDE.md").exists()` + `(framework / "docs" / "odd-methodology.md").exists()` (top-level docs remain single-level post-FBE.2b).
  - Update the test docstring (lines 81-89) + the file-level module docstring (lines 15-40) to describe the post-FBE.2b doubled-component contract; reference `AC.FBE.2c.3`.

- **`framework/workspace-bootstrap/tests/test_AC_SFR_5_stranger_clones_canonical.py`** — single function `test_AC_SFR_5_framework_only_reachable_via_explicit_branch` (lines 106-135):
  - Flip the assertion at line 133: `assert all(not p.startswith("framework/") for p in paths)` → `assert any(p.startswith("framework/") for p in paths)`.
  - Update inline comment (lines 127-128) to describe the post-FBE.2b prefix-preserving synth contract; cite `AC.FBE.2c.4`.
  - Top-level "CLAUDE.md in paths" assertion (line 135) STAYS unchanged (still at synth-tree root).

### Sidecar bumps within sealed-component fence:

- `framework/workspace-bootstrap/tests/SEAL_COMMIT` advances to FBE.2c seal SHA via `loam amend seal`.
- `framework/workspace-bootstrap/tests/test_no_sealed_amendments.py` BASELINE literal bumps via `loam amend apply` (mirrors FBE.5b precedent — apply rewrites `BASELINE = ...` to the pre-apply tip).
- `framework/workspace-bootstrap/tests/SEAL_COMMIT.notes` — narrative file written by `loam amend seal`.

### Plan-doc + manifest (universal_paths.prefixes: `docs/rebuild/plans/`):

- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe2c.md` (this file).
- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe2c.manifest.yaml`.

### Parent plan-doc backfill (post-seal, separate commit):

- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` — §8 method-decision register: ADD a new `### FBE.2c — README + getting-started clone-line + 4 broken fixture tests (Decision D follow-through)` subsection with apply commit SHA + seal commit SHA + verification summary. Update the closing "Remaining sequence:" line: drop FBE.5b (sealed post-FBE.2c) + name FBE.2c as the immediate predecessor.

**TOTAL fence diff:** ~6 line-edits in README.md + ~12 line-edits in docs/getting-started.md (collapse + renumber) + ~8 line-edits across 3 test files (assertion flips + path literal updates + docstring tightens) + 1 sidecar `SEAL_COMMIT` bump + 1 BASELINE literal bump + 1 SEAL_COMMIT.notes narrative + plan-doc + manifest YAML + parent plan §8 backfill.

---

## 7. Smoke verification

**Pre-build smoke (planning-time verification, this turn):**

- `bootstrap_new_workspace` against fixture canonical produces `<new-ws>/framework/framework/workspace-sync/src/...` (DOUBLED) — VERIFIED via fresh probe.
- `git ls-tree -r --name-only framework-only` against fixture canonical shows `framework/<comp>/...` paths preserved — VERIFIED via fresh probe.

**Post-edit smoke (AC.FBE.2c.7) — runs POST-seal so it exercises the seal-bumped tree:**

```
# Smoke proper — documents the user-visible flow
rm -rf /tmp/fbe2c-clone-smoke
git clone --branch framework-only /Users/lukeivers/ivers-corp-pos-v2/ \
    /tmp/fbe2c-clone-smoke 2>&1 | tail
echo "Exit: $?"

# Verify single-level shape (no doubling at <clone>/framework/framework/)
ls /tmp/fbe2c-clone-smoke/
ls /tmp/fbe2c-clone-smoke/framework/

# Cleanup
rm -rf /tmp/fbe2c-clone-smoke
```

Expect:
- `git clone` exits 0 (real canonical's framework-only branch may be pre-FBE.2b shape — in that case the smoke documents that the OLD shape would be `<clone>/<comp>/...` at root WITHOUT a `framework/` parent, which is also single-level relative to clone root; the post-FBE.6-republish shape would be `<clone>/framework/<comp>/...`. Either way, no doubling at `<clone>/framework/framework/` — that's the verification point.).
- Alternative path: smoke against fixture-canonical's framework-only branch via test scaffold reproduces `framework/<comp>/...` at single-level (no doubling), per the planning-time probe.

**Pytest smoke (verifies AC.FBE.2c.{3,4,5,6}):**
- `pytest framework/workspace-bootstrap/tests/test_AC_SFR_1_single_framework_directory.py framework/workspace-bootstrap/tests/test_AC_SFR_5_stranger_clones_canonical.py framework/workspace-bootstrap/tests/test_pos_new_workspace.py` returns 18/18 PASS (was 14 PASS + 4 FAIL pre-FBE.2c).

**Failure modes:**
- Any of the 4 previously-failing tests still fails post-edit → fix is incomplete; halt; surface; iterate.
- Any of the 14 previously-passing tests now fails → unintended scope creep; halt; surface; revert.
- More than 4 tests fail → deeper FBE.2b regression or new surface; halt; surface to dispatcher (matches halt trigger #4).

---

## 8. Hard constraints

- 1 sealed-component sidecar in fence (workspace-bootstrap). 3 test-file edits + 2 doc-file edits.
- No new external runtime deps.
- No `git commit --amend` per `feedback_no_amend_in_agent_dispatches`.
- `loam amend apply` invoked BEFORE seal commit per `feedback_dispatch_explicit_pos_amend_apply`.
- AC-prefix `AC.FBE.2c.*` (collision-safe).
- Auto-memory `MEMORY.md` NOT touched.
- Component-scoped test rerun per `feedback_amendment_dispatch_speedups`: only `framework/workspace-bootstrap/tests/` runs post-seal.
- Per FBE.4/FBE.5/FBE.5b partner-prefix gap precedent: workspace-bootstrap's prefix is the canonical `framework/<name>/` shape — apply tool should derive cleanly. If a corrective is needed, mirror FBE.4's `0c4d9a0` recipe.
- Negative AC.FBE.2c.8: no scope expansion.
- ODD §2.5 — every line of the fix maps to AC.FBE.2c.{1,2,3,4,5,6,7,8}. No defensive code for cases ACs don't name.

---

## 9. Out of scope (per ODD §2.5)

- Renaming `test_AC_SFR_1_single_level_framework_directory` (the file or function name).
- Renaming the AC family `AC.SFR.1` → something else.
- Editing `framework/workspace-bootstrap/src/` source.
- Editing `framework/loam-init/` or any other component source.
- Editing the synth pipeline.
- Broader README rewrites (the §"Why" / §"What ships in v0.1.0" / §"Design lenses" / §"Status" / §"Documentation" / §"Contributing" / §"Security" / §"License" sections are NOT touched).
- Broader getting-started.md rewrites (the §"Audience" / §"Prerequisites" / §"What just happened" / §"Where to go next" / §"Common first-run problems" sections are NOT touched).
- Editing the CLI summary message at `framework/loam-init/src/loam/loam_init/cli.py:128`.
- Editing any other test file in workspace-bootstrap or any other component.

---

## 10. Halt-and-surface (during build)

Per `feedback_subagent_odd_violation_halt`:

- **HT-1:** Edit touches `framework/workspace-bootstrap/src/` (or any non-test source) — wrong fence direction; the dispatcher's brief locks the fix at the test/doc layer. Halt; surface.
- **HT-2:** Edit drifts to other doc files (`docs/architecture.md`, `docs/positioning.md`, `docs/components/<any>.md`, etc.) — out of scope per AC.FBE.2c.8 and dispatcher halt trigger #2. Halt; surface.
- **HT-3:** Edit drifts beyond the single Quickstart code block in README.md (e.g. "Why" or "What ships" or "Documentation" sections). Halt; surface.
- **HT-4:** Edit drifts beyond §1 + §2 collapse + step renumbering in docs/getting-started.md. Halt; surface.
- **HT-5:** More than 4 fixture tests fail at planning-time pytest run — possible deeper FBE.2b regression. Halt; surface (matches dispatcher halt trigger #4).
- **HT-6:** A previously-passing test breaks after the edit — unintended scope creep. Halt; revert; surface.
- **HT-7:** `loam amend apply` rejects the manifest. Halt; surface; manifest shape may need adjustment.
- **HT-8:** `loam amend seal` rejects the seal. Halt; surface; usually a touched-file outside fence + universal admissions; if partner-prefix gap recurs (per FBE.4 precedent `0c4d9a0`), apply hand-corrective.
- **HT-9:** Surrounding-code ODD §2.5 violation discovered in any touched file. Halt; surface; do NOT silently extend or fix in-band.
- **HT-10:** Wall-time exceeds 50 min. Halt with partial findings.
- **HT-11:** WD drifts to pos3. Halt immediately.

---

## 11. Risks

- **Risk: README.md / docs/getting-started.md edits are caught by an additional fence test outside workspace-bootstrap.** Mitigation: most fence tests admit `README.md` + `docs/getting-started.md` in their `allowed_files`; the four that don't (memory-system, dormancy, loam-init, safety-layer) have BASELINEs whose `..SEAL_COMMIT` window does NOT include FBE.2c's commits (their SEAL_COMMIT sidecars don't bump). Verified via grep at planning-time.
- **Risk: `loam amend seal`'s default cross-component sweep includes other components.** Mitigation: pass `--scoped-sweep` if the cross-component sweep surfaces false-positives; if positive findings, halt + surface (HT-8).
- **Risk: Renumbering steps in docs/getting-started.md introduces a numbering inconsistency the test suite catches.** Mitigation: no test asserts step numbering; the only test on getting-started.md is the fence-test admission (path-only, not content). Edit + re-grep at planning-time before commit.
- **Risk: A fresh `git clone <local-path> --branch framework-only` smoke fails because the local canonical's framework-only branch is pre-FBE.2b (still has bare-comp paths).** Mitigation: smoke documents the OLD shape if encountered; the AC.FBE.2c.7 verification point is "no doubling at `<clone>/framework/framework/`", which holds for both old AND new synth shapes (the no-`framework/`-arg clone never double-prefixes regardless of synth). Document the actual observed shape in the FBE.2c status file.
- **Risk: The `feedback_loose_AC_text_fix_AC_not_implementation` precedent argues to fix the AC text when implementation matches intent — but here the implementation is what changed (FBE.2b shifted the synth contract); the AC text was correct for the OLD contract.** Mitigation: AC.SFR.1's "single level" naming is a doc artifact; the test body is the binding contract; FBE.2c rewrites the test body (and adds AC.FBE.2c.* family to bind to) without renaming the file/function/AC-family. Future amendment can rename if dispatcher rules.

---

## 12. Sequencing (commit ladder)

1. **Plan-doc commit** (this file authored alone, NEW commit).
2. **Doc + test edits commit** — single commit covering: README.md Quickstart edit + docs/getting-started.md collapse-and-renumber + 3 fixture-test files' assertion-flips + path-literal updates + docstring tightens.
3. **Manifest commit** — author `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe2c.manifest.yaml` (single component in `components:` block: workspace-bootstrap).
4. **`loam amend apply`** — invoke against the manifest. Produces apply-bookkeeping commit (BASELINE bumps in workspace-bootstrap's `test_no_sealed_amendments.py`; sidecar `SEAL_COMMIT` advances to BASELINE).
5. **`loam amend seal`** — produces deterministic seal commit; sidecar `SEAL_COMMIT` advances to seal SHA; narrative file written at `framework/workspace-bootstrap/tests/SEAL_COMMIT.notes`.
   - **If seal fails on partner-prefix gap (per FBE.4/FBE.5b precedent):** apply corrective hand-admit per FBE.4 recipe (`0c4d9a0`) — single-file edit to the offending fence-test's `allowed_prefixes`; commit; re-run seal.
6. **Smoke verification (AC.FBE.2c.7)** — POST-seal; verify shipped behaviour against the seal-bumped tree.
7. **Parent plan-doc backfill** — `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` §8 add `### FBE.2c` subsection with apply + seal SHAs; update closing "Remaining sequence:" line (separate NEW commit; admitted via `docs/rebuild/plans/` universal prefix).
8. **Status file write** — `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe2c-status-2026-05-03.md` with seal report.

NO `git commit --amend` at any point. NO push to any remote.

---

## 13. References

- **Parent plan:** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` §8 (FBE.2c row to be added at backfill time).
- **FBE.5b status (Surface #1 origin):** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe5b-status-2026-05-03.md` (the 4 failing tests + the bisection diagnosis to FBE.2b).
- **FBE.2b plan + status (the synth-shape change that produced the doubling):** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe2b.md` + `<workspace>/.scratch/claude-output/fbe2b-status-2026-05-03.md`.
- **Source-trace evidence (fresh probe this turn):** `bootstrap_new_workspace` at `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py:545` (clone target = `<new-ws>/framework/`); `_clone_canonical` at line 283 (clone-into target_framework_dir); `synthesise_framework_only` post-FBE.2b preserves `framework/` prefix (verified via `git ls-tree`).
- **Memory bullets honoured:**
  - `feedback_plan_before_code` (this is the plan; no code yet).
  - `feedback_no_amend_in_agent_dispatches` (commit ladder uses NEW commits only).
  - `feedback_dispatch_explicit_pos_amend_apply` (apply step explicit in §12).
  - `feedback_subagent_odd_violation_halt` (HT-1 through HT-11).
  - `feedback_amendment_dispatch_speedups` (test rerun scoped to fence component only).
  - `feedback_summarize_and_surface_decisions` (Surfaces 1-7 explicit).
  - `feedback_specific_claims_verified_or_marked_guess` (every "verified at" claim has a path/line citation; the 4 failing tests are reproduced at planning-time).
  - `feedback_loose_AC_text_fix_AC_not_implementation` — partial inverse: here the implementation changed (FBE.2b synth shift), so the AC text + tests are tightened to match the new implementation; the existing AC family (`AC.SFR.1`) is preserved as a doc artifact and the new contract binds to `AC.FBE.2c.*`.
  - `feedback_critical_thinking_on_deviations` (the 4 failing tests' contract inversion was weighed against alternative resolutions in FBE.5b's status; Path α is the dispatcher's locked resolution).

---

## 14. AI-time band

- Predicted: **20–35 min, midpoint 28 min**; dispatch hard cap 50 min.
- Justification: 2 doc-file edits (~6 + ~12 line-edits) + 3 test-file edits (~8 line-edits + docstring tightens) + 1 manifest YAML + apply (single-fence, canonical-shape — fastest case) + seal + smoke + parent §8 backfill + status file. Per rubric: amendment-build (single-fence, multi-file edits but each small + test-only assertion flips) → 15–30 min midpoint 22; widen for the docs/getting-started.md renumbering verification + the smoke + the parent §8 backfill.

---

## 15. Method-decision register (post-build)

(Populated as commits land.)

- Plan-doc commit: `<TBD>`.
- Doc + test edits commit: `<TBD>`.
- Manifest commit: `<TBD>`.
- Apply commit: `<TBD>`.
- Corrective commit (if needed): `<TBD>`.
- Seal commit: `<TBD>`.
- Parent plan-doc §8 backfill commit: `<TBD>`.

---

*End of FBE.2c sub-plan-doc. Ready to build.*
