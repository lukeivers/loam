# Rebrand Phase 1 — branch rename + first-impression cleanse

**Status:** plan-only at authoring time. Plan-before-code per `feedback_plan_before_code` (hard rule). Owner ratifies before any cycle dispatches; uncommitted at land time.
**Slug:** `rebrand-phase-1-branch-and-first-impression`.
**Date authored:** 2026-05-09.
**Class:** META-FRAMEWORK + REBRAND-EXECUTION (branch-rename ops + Tier-1 documentary rebrand; no end-user runtime capability change).
**Predecessor:** Q7 ratification 2026-05-09 (Telegram 10594) — phased shape; no commit-history rewrite; Tier 3 = move-to-archive-with-header (separate phases later); Tier 4 = SKIP. The decisions doc `docs/plans/loam-rename-decisions.md` (approved 2026-04-23) is the standing authority for the rebrand naming choices. Phase 1 documentary rebrand was previously activated as part of v0.1.0 publish (per FUTURE_IDEAS Idea 12 status line); this plan-doc executes the **completion** of that Phase 1 against the current canonical state plus closes out the long-deferred branch rename.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Dependency on v0.5.0 publish:** SOFT — see §8.

---

## §1 — Outcome shape (the "why")

External readers (senior eng / OSS reviewer / potential acquirer) hit the loam GitHub repo. Their first 60 seconds: clone or browse `lukeivers/loam` → see the default branch name → read `README.md` → glance at `CLAUDE.md` (if curious about how the project ships agent context). Today, three first-impression failures degrade that 60-second read:

1. **Default branch is `main`, but maintainer pushes from `pos-v2`.** External readers cloning from `loam:main` get the canonical content (because the push refspec maps `pos-v2 → main`), so the public surface looks correct. But anyone who clones the maintainer's working tree, or reads any of the dev-mode docs that name `pos-v2` as the active branch, sees a branch name that contradicts the project's identity. The branch name is the highest-frequency identity signal in any git workflow — visible in every `git status`, `git branch`, every IDE branch indicator, every CI badge, every PR diff URL.
2. **`CLAUDE.dev.md` opens with "pOS v2 — CLAUDE.dev.md" + 5 more `pos-v2` references in the body.** Any external reader who opens `CLAUDE.dev.md` (the dev-extension companion to the always-loaded `CLAUDE.md`) sees the old project name in the title and throughout the file. The always-loaded `CLAUDE.md` is clean (verified zero refs) — but the moment a reader follows the docs into the dev surface, the brand inconsistency surfaces.
3. **Top-level docs tier (verified clean for README/LICENSE/CONTRIBUTING/SECURITY/CODE_OF_CONDUCT/install-from-source.txt — see §3 audit) carries zero pos-v2 refs today.** This is the strongest first-impression layer and is already correct; Phase 1 preserves that property and extends it.

Phase 1 ships the highest-leverage external-presentability win at lowest cost: rename the active development branch to `main` (closing the awkward push-refspec mapping), scrub `CLAUDE.dev.md` of all `pos-v2` references, and verify the rest of the Tier-1 first-impression surface stays clean. The external-reader's 60-second read sees zero `pos-v2` references in any first-impression file plus a default branch named `main` that matches their workflow expectations.

Composes with: `docs/plans/loam-rename-decisions.md` (the rename naming authority — pos-v2/pOS v2 → loam, ~/.pos → ~/.loam, etc.). Composes with: FUTURE_IDEAS Idea 13 status — the rebrand is in-flight per the decisions doc; Phase 1 is the documentary slice.

---

## §2 — Prime objective ladder

`docs/VALUE_PROPOSITION.md` prime objective (loam helps people use LLMs to build software) → loam adoption by external readers compounds Goal 2 (consulting tool credibility — the rebranded surface is what prospective consulting clients see when evaluating loam) and Goal 1 (external-reviewer first-impression signal). Branch name + Tier-1 doc surface are the two highest-frequency external-touch points; both must read as `loam` (not `pos-v2` historical residue) for the adoption signal to compound rather than degrade.

Composes with: Lens 4 (scope-confidence) — Phase 1 has HIGH confidence on the outcome shape (rename + clean Tier-1 docs; the hard call was already made in `loam-rename-decisions.md`), so scope tight per the AC family below. Composes with: Lens 5 (swarming) — Phase 2 (current-state docs) and Phase 3 (historical archive) are separate plan-docs at this same altitude; this plan-doc is one subtask in the broader rebrand-completion swarm. Composes with: F2 RUTHLESS FEEDBACK — the discovery during plan-authoring that local `main` is a separate-history orphan branch from `lukeivers/ivers-corp.git` (NOT a stale loam main) is surfaced at §9 Q1 as a hard halt-and-surface finding affecting the rename mechanism choice.

---

## §3 — Component fence

**PRIMARY (git-ops):**

- `.git/config` (effective config at `/Users/lukeivers/ivers-corp/.git/config` — this is a worktree-shared git dir; both `ivers-corp` and `ivers-corp-pos-v2` worktrees use the same config). The push refspec is currently a manual `git push loam pos-v2:main` invocation; no `[push]` section exists. The branch rename collapses this to `git push loam main:main` (or just `git push loam main`).
- Local branch refs: `pos-v2` (active) → renamed to `main`. Existing local `main` (orphan from `lukeivers/ivers-corp.git`, NOT shared lineage with `pos-v2` — verified at plan-authoring; `git merge-base main pos-v2` returns empty) needs disposition before the rename — see §9 Q1.
- Local `framework-only` branch (HEAD `1bea0f8e`) — verified obsolete per STATE.md 2026-05-04 entry (workspace-bootstrap migrated off `framework-only` in OSS dev-architecture migration #132).

**SECONDARY (Tier-1 first-impression docs — verified state):**

- `README.md` (7927 bytes; **0 `pos-v2` refs** — verified clean; preserve property via grep gate).
- `CLAUDE.md` (13054 bytes; **0 `pos-v2` refs** — verified clean; preserve property via grep gate).
- `CLAUDE.dev.md` (4827 bytes; **6 `pos-v2` refs** at lines 1, 3, 6, 16, 62, 96 — fence target for scrub).
- `LICENSE` (11357 bytes; **0 refs** — preserve).
- `CONTRIBUTING.md` (6618 bytes; **0 refs** — preserve).
- `SECURITY.md` (5808 bytes; **0 refs** — preserve).
- `CODE_OF_CONDUCT.md` (5731 bytes; **0 refs** — preserve).
- `install-from-source.txt` (4210 bytes; **0 refs** — preserve).

**TERTIARY (sync + workspace-sync follow-on; SOFT update):**

- `framework/workspace-sync/src/loam/workspace_sync/canonical_cache.py:26` — comment string `"pos-v2 is ~15 MB at HEAD"` (cosmetic; preserve technical accuracy by updating to `"main is ~15 MB at HEAD"` at the same time as branch rename to keep the cache-sizing comment current).
- `framework/workspace-sync/src/loam/workspace_sync/sync_config.py:71,194` — docstring + error-message strings reference `"canonical pos-v2 working tree"` and `"pos-v2"` example path (cosmetic; aligns with the rename and prevents reader confusion about the canonical location).

**Untouched (explicit):**

- All historical seal narratives (`framework/*/seals/SEAL_COMMIT.*`) — the published audit trail; references to `pos-v2` branch / pOS v2 brand stay verbatim per `loam-rename-decisions.md` ruling 2 ("Preserve contemporary terminology. Commit messages and seal narratives that cite 'pOS v2' stay untouched").
- All `docs/plans/*.md` plan-docs (historical record + current in-flight). The 408 `pos-v2` refs across `docs/**/*.md` (verified via grep at plan-authoring) are mostly Phase-2 / Phase-3 territory and out of fence here.
- `docs/STATE.md`, `docs/release-roadmap.md`, `docs/FUTURE_IDEAS.md`, `docs/FUTURE_IDEAS_DRAFT.md`, `docs/dev-mode-getting-started.md`, `docs/personas-methodology.md`, `docs/odd-llm-grounding-derivation.md`, `docs/BACKLOG.md` — total 51 `pos-v2` refs across these per grep; these are Tier 2 (current-state docs) and ship in Phase 2.
- `framework/hands-off-lifecycle/hooks/_gate_helpers.py:559` — protected-branch regex hardcodes `pos-v2` in the deny-pattern. This is a **live code surface**, not a doc. It MUST be addressed before the branch rename takes effect (the rename without a hook update would silently de-protect the renamed `main` from force-pushes to it; see §7 HARD HALT). NOT in Phase 1 fence; flagged as **HARD blocker** in §9 Q4 (the hook-update either lands inside Phase 1 as a fence extension OR ships as an immediate prerequisite cycle).
- `framework/hands-off-lifecycle/hooks/first_run_progress.py:91` — comment string `"pos-v2:"` prefix in docstring (cosmetic; preserve in Phase 2 sweep).
- `framework/workspace-sync/tests/test_cli_d_shape.py:88,101,617` — test fixtures naming `pos-v2` as a branch name in mock states. Tests would break if updated without the rename; updated as part of the rename when the rename actually flips canonical's branch name. Phase 2 territory in current scope per Q5.
- All `~256 .py / .yaml / .json live references` (verified count from initial survey) — Phase 2 territory.

**Out of fence:** any framework component runtime, any seal directory write, any test fixture not flagged above, any plugin code, any plan-doc not named in fence. Edits outside fence = halt + rewind.

---

## §4 — AC family `AC.RBPH1.*` (TIGHT)

Each AC carries name + acceptance + outcome-altitude marking per `feedback_test_outcome_altitude_required` and ODD §2.5.

### AC.RBPH1.1 — Local branch `pos-v2` renamed to `main`; orphan local `main` disposed

The local `pos-v2` branch is renamed to `main`. The pre-existing local `main` branch (orphan history from `lukeivers/ivers-corp.git`, NOT loam lineage — verified at plan-authoring time; merge-base with `pos-v2` is empty) is disposed per the §9 Q1 ratified path:

- **Path A (recommended):** delete the orphan local `main` first (`git branch -D main`), then rename `pos-v2` → `main` (`git branch -m pos-v2 main`). Single linear move; final state is clean.
- **Path B:** rename orphan to `ivers-corp-orphan` (preserves history if Luke ever wants the orphan back), then `git branch -m pos-v2 main`.
- **Path C (split):** the orphan `main` belongs to a different repo entirely (`lukeivers/ivers-corp.git`); the cleanest disposition is to remove it from this worktree's git config and let it live in the `ivers-corp` worktree's namespace exclusively. (Requires worktree-config investigation; see §5 D-RBPH1.5.1.)

Post-rename: `git branch` shows `main` (active) + `framework-only` (obsolete; per Q2). `git status` on canonical worktree reports `On branch main`.

**Verdict:** GREEN if `git rev-parse --verify main` resolves to the same SHA that `pos-v2` resolved to before the rename AND `git rev-parse --verify pos-v2` returns error (branch absent) AND any orphan-main disposition path executed cleanly per Q1 ratification. RED if `pos-v2` still exists OR `main` resolves to the orphan SHA OR worktree is in a detached state.

**Test:** `git rev-parse --verify main` returns SHA matching pre-rename `pos-v2` HEAD; `git rev-parse --verify pos-v2 2>&1 | grep -q "unknown revision"`. Outcome verified post-rename in `git status`.

`outcome-altitude: false` (mechanical state change; necessary substrate for AC.RBPH1.5).

### AC.RBPH1.2 — Push refspec updated for new branch name

The current push pattern is a manual `git push loam pos-v2:main` invocation (no persistent `[push]` config block in `.git/config` per inspection). Post-rename, the equivalent is `git push loam main` (or `git push loam main:main` explicit form). Two paths:

- **Path A:** No persistent config update needed; the rename itself eliminates the awkward refspec because `git push loam main` (no colon) just works (push to same-name remote branch). Document the new push command in any place the old `pos-v2:main` form was named.
- **Path B:** Add an explicit `[push]` config block setting `default = upstream` or `default = current` so `git push` (with no args) works against the new `main` branch. Composes with v0.6.0 `loam release` CLI which can shell out to `git push` without arguments.

Post-rename: any documentation that said `git push loam pos-v2:main` (verified at `docs/release-roadmap.md` lines 88, 102 references publish flow) reads `git push loam main` instead. The release-roadmap §6 publish-action references update.

**Verdict:** GREEN if no occurrence of `pos-v2:main` remains in any tracked file AND `git push loam main` is the documented publish command AND any chosen Path A or B is reflected in `.git/config` or absence-of-config matches the documented intent. RED if `pos-v2:main` substring survives in any tracked file OR config-vs-doc disagree.

**Test:** `grep -r "pos-v2:main" docs/ framework/ tools/ workspace-sync/ 2>/dev/null` returns empty. `cat /Users/lukeivers/ivers-corp/.git/config` matches the documented post-rename state.

`outcome-altitude: false` (config + doc consistency; supports AC.RBPH1.5).

### AC.RBPH1.3 — workspace-sync default-branch references updated

Per fence §3 SECONDARY-TERTIARY: `framework/workspace-sync/src/loam/workspace_sync/canonical_cache.py:26` (`"pos-v2 is ~15 MB at HEAD"` comment) and `framework/workspace-sync/src/loam/workspace_sync/sync_config.py:71,194` (docstring + error-message strings) are updated from `pos-v2` to `main`. These are not branch-resolution code — workspace-sync resolves the canonical branch dynamically at runtime per the workspace-bootstrap-framework-only-to-main migration (STATE.md 2026-05-04). The updates are documentation/string consistency, not behavior change.

**Verdict:** GREEN if `grep -n "pos-v2\|pos_v2" framework/workspace-sync/src/` returns empty AND existing workspace-sync tests still pass (no regression introduced by the comment/string updates). YELLOW if comments updated but a test references the old string in a fixture (treat as Phase 2 follow-on per fence §3 Untouched). RED if any source file still contains the old string OR workspace-sync test suite regresses.

**Test:** `grep -rn "pos-v2\|pos_v2" framework/workspace-sync/src/ 2>/dev/null | wc -l` returns 0; `cd framework/workspace-sync && pytest tests/` GREEN at SEAL_COMMIT.

`outcome-altitude: false` (string consistency in non-runtime-critical surface; supports AC.RBPH1.5).

### AC.RBPH1.4 — `CLAUDE.dev.md` scrubbed of `pos-v2` references

`CLAUDE.dev.md` (verified 6 `pos-v2` references at plan-authoring: lines 1, 3, 6, 16, 62, 96) is scrubbed. Replacement strategy:

- Line 1 (`# pOS v2 — CLAUDE.dev.md (dev-extension fragment)`) → `# loam — CLAUDE.dev.md (dev-extension fragment)`.
- Line 3 (`This file is the **dev-extension** of `CLAUDE.md` for the pOS v2 codebase.`) → `This file is the **dev-extension** of `CLAUDE.md` for the loam codebase.`.
- Line 6 (`when the workspace is classified `pos-v2-dev`). NORMAL USE workspaces`) → `when the workspace is classified `loam-dev`). NORMAL USE workspaces`.
- Line 16 (`Before acting on any non-trivial pos-v2 work — planning, proposing,`) → `Before acting on any non-trivial loam work — planning, proposing,`.
- Line 62 (`- `plugins/dev-sdlc/docs/odd-in-loam.md` — ODD applied to pOS v2 specifically, including`) → `- `plugins/dev-sdlc/docs/odd-in-loam.md` — ODD applied to loam specifically, including`.
- Line 96 (`new pOS v2 copy is being tested in a live evaluation workspace. Until`) → `new loam copy is being tested in a live evaluation workspace. Until`.

Plus README.md + CLAUDE.md grep-verified to remain at zero `pos-v2` refs (preserve property; not an edit, a check).

Plus LICENSE / CONTRIBUTING.md / SECURITY.md / CODE_OF_CONDUCT.md / install-from-source.txt grep-verified at zero refs (preserve).

**Verdict:** GREEN if `grep -cEi "pos[ _-]?v?2|posv2" CLAUDE.dev.md` returns 0 AND every other Tier-1 file (README.md, CLAUDE.md, LICENSE, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md, install-from-source.txt) returns 0 AND the rewrites preserve the file's structural meaning (manual review confirms `loam` substitutions read naturally; no broken references introduced). YELLOW if grep clean but one substitution reads awkwardly (e.g., classifier name `loam-dev` clashes with another classifier — research at builder time). RED if any file still has `pos-v2` references.

**Test:** `for f in README.md CLAUDE.md CLAUDE.dev.md LICENSE CONTRIBUTING.md SECURITY.md CODE_OF_CONDUCT.md install-from-source.txt; do count=$(grep -cEi 'pos[ _-]?v?2|posv2' "$f" 2>/dev/null); [ "$count" = "0" ] || echo "FAIL: $f has $count refs"; done` outputs nothing.

`outcome-altitude: false` (file-content state; necessary substrate for AC.RBPH1.5).

### AC.RBPH1.5 (outcome-altitude) — Fresh-clone external-reader 60-second read sees zero pos-v2 references

A fresh `git clone https://github.com/lukeivers/loam.git fresh-loam-clone` (executed against the post-publish remote state) plus a 60-second README + CLAUDE.md + branch-state read by an outsider sees zero `pos-v2` references in the first-impression surface. The probe is exercised end-to-end at SEAL time (not stubbed):

1. **Branch state probe.** In the fresh clone: `git branch` shows `* main` only (no `pos-v2`). `git remote show loam | head -10` reports HEAD branch as `main`. Default checkout lands on `main`.
2. **Top-level surface grep probe.** In the fresh clone: `for f in README.md CLAUDE.md CLAUDE.dev.md LICENSE CONTRIBUTING.md SECURITY.md CODE_OF_CONDUCT.md install-from-source.txt; do grep -cEi 'pos[ _-]?v?2|posv2' "$f" 2>/dev/null; done | paste -sd+ - | bc` returns 0.
3. **Outsider checklist read.** A reader (the build agent steps into the role; or an actual outsider per opportunistic gate) walks: (a) repo landing-page view (GitHub renders README.md by default), (b) cd into clone + `git status`, (c) `cat CLAUDE.md | head -30`, (d) `cat CLAUDE.dev.md | head -10`. The reader confirms in writing (writeup at `<workspace>/.scratch/claude-output/rebrand-phase-1-outcome-probe-2026-05-XX.md`) that no `pos-v2` references appeared in any file read AND the branch was `main`.

**Verdict:** GREEN if all three probes confirm zero refs AND branch reads as `main` AND writeup landed at canonical scratch path naming the three probes' results. YELLOW if grep returns 0 but checklist probe surfaces an awkward reading (e.g., `CLAUDE.dev.md`'s rewritten `loam-dev` workspace classifier doesn't have a corresponding upstream definition — manifests as a broken-reference reader-friction). RED if any probe surfaces a `pos-v2` reference OR the branch isn't `main` OR the writeup is absent.

**Test:** Three probe results captured in the writeup. The probe is run AGAINST THE FRESH CLONE, not the canonical working tree (real-world readiness check; STUB-class would be running against the working tree where state was just edited — that's pre-arrangement).

`outcome-altitude: true` per `feedback_test_outcome_altitude_required` rubric — real fresh clone, real grep, real reader-altitude checklist, real downstream signal (the 60-second first-impression that drives external-reader trust). Production-facing surface (public OSS docs); HARD per-cycle smoke per Luke's risk-band classifier 2026-05-05.

### AC.RBPH1.S — Seal-diff discipline

Sealed-component cycle ritual; sidecar advances; `git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under the named §3 fence: `.git/config` (or its worktree-shared equivalent + push-config if Q3 selects Path B), `CLAUDE.dev.md`, `framework/workspace-sync/src/loam/workspace_sync/canonical_cache.py`, `framework/workspace-sync/src/loam/workspace_sync/sync_config.py`, plan-doc + manifest + seal narrative scaffolding, plus any files surfaced by AC.RBPH1.2 that referenced the old `pos-v2:main` push pattern (e.g., `docs/release-roadmap.md` lines 88+102 — these are Tier-2 territory by general rule but are PUSH-COMMAND-SPECIFIC strings tightly coupled to the rename and may justify in-scope inclusion per §5 D-RBPH1.5.4). Out-of-fence diffs = halt + rewind.

`outcome-altitude: false` (process invariant).

---

## §5 — Decisions builder rules at build time

These decisions are the builder's call at build-time; the plan-doc names the choice points without pre-deciding.

### D-RBPH1.5.1 — Worktree git-config interaction (orphan main disposition mechanics)

The canonical loam tree at `/Users/lukeivers/ivers-corp-pos-v2/` is a **secondary worktree** of `/Users/lukeivers/ivers-corp/` (which is a separate repo: `lukeivers/ivers-corp.git`, the user's "personal stuff" repo). They share `.git/` — meaning the rename of `pos-v2` to `main` happens in the SHARED git directory, but the orphan local `main` is the active branch in the `ivers-corp` worktree.

Two paths:

- **Path A (recommended):** check out a different branch in the `ivers-corp` worktree first (e.g., create `ivers-corp-main` from current `main` SHA, switch to it), then `git branch -D main` (now safe — no worktree has `main` checked out), then `git branch -m pos-v2 main`. The `ivers-corp` worktree gets a renamed branch (`ivers-corp-main` instead of `main`); its remote tracking still works (`branch.ivers-corp-main.remote` points to origin per the renamed-branch convention).
- **Path B:** detach the worktrees (move `ivers-corp` out of the shared git dir; give it its own clone). Cleanest separation; highest cost; out-of-Phase-1-scope for this build. Surfaced for explicit rejection.

_Builder rules at build time per D-RBPH1.5.1._ Path A is the recommended approach; the builder verifies the `ivers-corp` worktree is in a clean state and that the rename of its tracking branch doesn't break Luke's day-to-day workflow on the ivers-corp repo. If `ivers-corp` is dirty or in mid-task at build-time, the builder halts + surfaces.

### D-RBPH1.5.2 — `framework-only` branch handling

Both local `framework-only` (`1bea0f8e`) and remote `loam:framework-only` exist. Per STATE.md 2026-05-04 entry: workspace-bootstrap migrated off `framework-only` (deprecated synthesis output) to canonical `main`. Post-seal cleanup was deferred to Luke's discretion. Three paths:

- **Path A (recommended):** delete both. `git branch -D framework-only` locally; `git push loam :framework-only` remotely. The remote ref deletion is owner-gated per §7 HARD HALT but explicitly authorized in this plan-doc as part of Phase 1's branch-state-cleanup mission.
- **Path B:** delete local; preserve remote as historical artifact. Lower disruption; some external readers might find the `framework-only` ref informative.
- **Path C:** preserve both (status quo). Zero-action; low value (the branch is officially obsolete + no consumer remains).

_Builder rules at build time per D-RBPH1.5.2._ Owner ratification of remote-deletion is required (§7 HARD HALT) before the build executes Path A.

### D-RBPH1.5.3 — Tag for historical anchor

Should a `pos-v2` annotated tag be created at the pre-rename SHA to provide a historical anchor for any future archeology? Two paths:

- **Path A:** create `pos-v2-history-anchor` (or `pre-rename-pos-v2`) annotated tag at the SHA `pos-v2` resolved to immediately before the rename. Free archeological signal; zero-cost preservation.
- **Path B (recommended):** don't create. The git history is preserved through the branch rename (the rename moves the ref, doesn't rewrite history); existing tags `v0.1.0` through `v0.5.0` already anchor the per-version SHAs. A `pos-v2-history-anchor` tag adds a redundant marker.

_Builder rules at build time per D-RBPH1.5.3._

### D-RBPH1.5.4 — Push-command string updates in roadmap docs

`docs/release-roadmap.md` line 88 (`pos-publish-framework-only` was discovered archived) is a historical reference and out-of-fence per "preserve contemporary terminology" rule. But line 102 (AC.V045.2 reference (e) `current branch is pos-v2`) is a forward-looking ACTIVE acceptance criterion that becomes wrong post-rename. Two paths:

- **Path A (recommended):** include the line-102 update in Phase 1 fence as a SECONDARY edit (it's a TODAY-LIVE active-AC string, not historical residue). The rename invalidates the AC text; updating it concurrently keeps the policy doc internally consistent.
- **Path B:** leave for Phase 2; ship Phase 1 with a known AC-text-vs-state inconsistency that v0.6.0 release-process build will catch and update.

_Builder rules at build time per D-RBPH1.5.4._ Path A is recommended; the edit is one line and keeps the AC family in `release-roadmap.md` valid.

### D-RBPH1.5.5 — Hook update sequencing for `framework/hands-off-lifecycle/hooks/_gate_helpers.py:559`

The protected-branch regex hardcodes `pos-v2` in the deny-pattern. The branch rename to `main` means the new branch name is ALREADY in the regex (`main|master|pos-v2|develop|production|prod|release`) — the rename doesn't de-protect anything because `main` is also in the list. But the `pos-v2` element becomes dead-code post-rename (no branch with that name exists). Two paths:

- **Path A (recommended):** leave the regex unchanged in Phase 1 (no behavioral risk; `pos-v2` element is harmless dead-code). Schedule the regex cleanup as part of Phase 2 (current-state code refs cleanup).
- **Path B:** remove `pos-v2` from the regex in Phase 1 as a tiny inline edit. Cosmetic + reduces dead-code; very small diff; could ship in same cycle.

_Builder rules at build time per D-RBPH1.5.5._ Path A is the recommended Phase-1 path (keeps fence narrow; defers code touch to Phase 2). Path B if the builder finds the inline edit obviously safe + composable with the workspace-sync string updates.

---

## §6 — Out of scope (explicit)

The following are EXPLICITLY out of scope for this plan-doc + the build cycle that ships it:

- **Tier 2 cleanse.** `docs/STATE.md`, `docs/release-roadmap.md`, `docs/FUTURE_IDEAS.md`, `docs/FUTURE_IDEAS_DRAFT.md`, `docs/dev-mode-getting-started.md`, etc. — total ~51 `pos-v2` refs across these. Ships as `rebrand-phase-2-current-state-docs` separate plan-doc.
- **Tier 3 cleanse.** Historical-archive plan-docs + seal narratives — total ~408 `pos-v2` refs across `docs/**/*.md`. Per Q7 ratification: move-to-archive-with-header (the historical artifacts move into a dated archive subdirectory with a header noting the pre-rename context). Ships as `rebrand-phase-3-historical-archive` separate plan-doc.
- **Tier 4 (commit-history rewrite).** SKIPPED entirely per Q7 ratification. The git commit-message history retains all pre-rename `pos-v2` / `pOS v2` references verbatim. Anyone running `git log --grep="pos-v2"` continues to find the historical record.
- **Live code surface refs (~256 .py/.yaml/.json refs).** All script filenames (`pos_session_start.py`, `pos_orchestrator`), test fixture branch-names, env var prefixes (`POS_V2_*` per `loam-rename-decisions.md` Tier-1 item 3 — already partially executed), launchd label legacy, etc. Phase 2 territory or later (per `loam-rename-decisions.md` migration phasing).
- **Remote default branch settings on GitHub.** `loam:main` is already the default branch per `git ls-remote`. The rename is local-side; no GitHub repo settings change. (If at any point Luke wants to change the GitHub default branch label or rename the remote ref, that's a separate owner-action.)
- **Publish to remote.** Phase 1 ships LOCAL — branch rename + Tier-1 doc updates land in canonical working tree + sealed via the cycle ritual. The `git push loam main` action is owner-gated per the existing publish gate; Phase 1 build does NOT execute the public push.
- **Anything outside the §3 fence.** Any framework runtime, plugin, persona, hook, test surface, settings file, env var, etc. NOT named in §3. Discovery of additional Tier-1 surface during build = halt + surface for fence extension ratification, not silent inclusion.

---

## §7 — HARD HALTs (build-time)

Builder MUST halt + surface rather than proceed if any of these surface during build:

- **Any reach toward `git push --force` or `git push -f`.** Force-push to ANY branch on the loam remote (or any other remote) is a HARD HALT. The rename is a local op; remote sync (if owner authorizes) uses normal `git push loam main` only.
- **Any deletion of remote branches or tags WITHOUT owner explicit ratification.** D-RBPH1.5.2 Path A (delete `loam:framework-only` remote ref) requires explicit owner ratification before execution; the build does NOT autonomously execute remote-ref-deletion even if Path A was selected at plan-ratification time. Re-ratify at execution.
- **Any rewrite of git commit messages or git history.** Per Q7 explicit ruling. No `git rebase -i`, no `git filter-branch`, no `git commit --amend` on already-pushed commits, nothing that mutates the recorded SHA chain.
- **Any edit outside the §3 fence.** Halt; rewind. Discovery of additional Tier-1 surface (e.g., a top-level file with `pos-v2` refs that wasn't in the verified list) → halt; surface for fence extension; do NOT silently extend.
- **Any commit attempt during the plan-doc landing.** This plan-doc lands UNCOMMITTED. Builder surfaces the ratified plan-doc to owner for review; owner ratification gates the build cycle dispatch (which ships its own commit per the standard amendment-cycle ritual).
- **Discovery that the `ivers-corp` worktree is in a dirty / mid-task state at branch-rename time.** Halt; surface to owner; do NOT execute the rename across a worktree in active use.
- **Any test regression in workspace-sync after AC.RBPH1.3 string updates.** The string updates should be cosmetic-only; if a test fails post-update, surface immediately — there's a fixture or assertion coupled to the old string that needs investigation.
- **Discovery that the protected-branch regex in `_gate_helpers.py:559` doesn't include `main` after the rename.** The current regex DOES include `main` (verified at plan-authoring); halt-trigger included for builder-side defense-in-depth in case the regex is altered concurrently by another in-flight build.

Soft halts (surface but continue if the answer is clear from the ratified plan-doc): finding a Phase-2 or Phase-3 file that's tightly coupled to the rename mechanics (e.g., release-roadmap.md line 102 per D-RBPH1.5.4) — surface; if Path A in D-RBPH1.5.4 is ratified, fence extends to include that line; otherwise leave for Phase 2.

---

## §8 — Dependencies

- **HARD dep on owner ratification of §9 questions.** Q1 (orphan-main disposition path) + Q2 (`framework-only` handling) + Q3 (push-config Path A vs B) + Q4 (`_gate_helpers.py` hook update sequencing) + Q5 (descriptive-vs-suffixed slug for downstream rebrand-phase plan-docs) — all need owner ruling before build dispatches. Persona recommendations supplied; owner overrides as needed.
- **SOFT dep on v0.5.0 publish.** v0.5.0 (subagent-personas-routing) is sealed local + awaiting publish per current STATE.md / release-roadmap. The branch rename can land cleanly EITHER before or after v0.5.0 publish (Path A: rename first, then publish v0.5.0 from `main`; Path B: publish v0.5.0 from `pos-v2:main` per current refspec, then rename). Path A is cleaner (single coherent state at publish time); Path B is lower-disruption (v0.5.0 publish proceeds through the existing flow). Composes with v0.6.0 (release-process plan-doc) — the new `loam release` CLI ships KNOWING the branch is `main`, not `pos-v2`. If Phase 1 lands BEFORE v0.6.0 build, v0.6.0 plan-author writes against the post-rename state; if AFTER, v0.6.0 either hardcodes `main` (assuming the rename is imminent) or stays defensive about both names until the rename lands. Persona recommendation: land Phase 1 BEFORE v0.6.0 build dispatch + AFTER v0.5.0 publish (clean order; v0.5.0 ships through current flow; v0.6.0 builds against final branch state).
- **Composes with `docs/plans/loam-rename-decisions.md`** — the decisions doc is the authority for naming choices. Phase 1 inherits its rulings (preserve historical-context terminology, use `loam` as the rebrand target, etc.).
- **Composes with `docs/plans/release-roadmap-priority-queue-restructure.md`** — Phase 1 is one candidate in the priority-ordered queue (per the priority-queue restructure direction). Slug: `rebrand-phase-1-branch-and-first-impression`. Class: META-FRAMEWORK + REBRAND-EXECUTION (the version digit gets derived at build-commence per the restructure's number-derivation rule; Phase 1 is class PATCH if it ships as a follow-on to v0.5.0 in a single-tier-rebrand-cycle interpretation, OR class MINOR if the branch-rename is treated as a new outcome-shape — branch identity IS a user-visible capability change for anyone interacting with the repo via git tooling).

---

## §9 — Open questions for owner ratification

These need owner ruling BEFORE build dispatches:

### Q1 — Orphan local `main` disposition: delete (Path A), rename-and-keep (Path B), or worktree-split (Path C)?

The local `main` branch is from `lukeivers/ivers-corp.git` (Luke's personal-stuff repo) and has NO common ancestor with `pos-v2` (verified: `git merge-base` returns empty). It's actively checked out in the `ivers-corp` worktree. The rename of `pos-v2` to `main` requires this orphan to be disposed first.

- **Path A:** delete the orphan `main` (`git branch -D main` after first switching `ivers-corp` worktree to a new branch like `ivers-corp-main`). Final state: `ivers-corp` worktree on `ivers-corp-main` tracking origin/main; canonical loam worktree on `main` tracking loam/main (post-rename). Clean; renames a personal-stuff branch as a side-effect.
- **Path B:** rename the orphan to a preservation name (e.g., `ivers-corp-orphan`) before deleting nothing. Same final state as Path A but explicit-rename-then-no-delete (preserves the SHA chain accessible by the new name).
- **Path C:** detach the worktrees — give `ivers-corp` its own independent clone (out-of-shared-git-dir). Cleanest separation but high cost + scope-creep.

**Persona recommendation:** Path A. The orphan tracks `lukeivers/ivers-corp.git/main` from origin; renaming it to `ivers-corp-main` (or letting the deletion happen and accepting the loss-of-local-pointer; remote still has it via `origin/main`) is a one-line tradeoff. The cost of Path C (worktree separation) far exceeds the cost of accepting a renamed personal-stuff branch.

### Q2 — `framework-only` branch handling: delete both (Path A), delete local only (Path B), or preserve (Path C)?

Per STATE.md 2026-05-04, `framework-only` is officially deprecated (workspace-bootstrap migration #132 cut over to canonical `main`). Local + remote refs both exist. Per D-RBPH1.5.2.

**Persona recommendation:** Path A (delete both). The branch is dead; no consumer remains; preservation has zero archeological value (the synthesis-output content is fully reproducible from canonical via the historical workspace-bootstrap script — and the seal narrative at SEAL_COMMIT.workspace-bootstrap-framework-only-to-main records the migration). The remote-deletion is owner-gated per §7 HARD HALT; this Q2 ratification IS the gating answer.

### Q3 — Push-refspec config: leave as manual command (Path A) or add persistent `[push]` config (Path B)?

Currently no `[push]` config; publishes use `git push loam pos-v2:main` literal command. Post-rename, `git push loam main` works without colon. Path A (no config change) is sufficient. Path B (add `[push] default = current` or similar) reduces typing; composes with v0.6.0 `loam release` CLI.

**Persona recommendation:** Path A. The `loam release` CLI (when v0.6.0 builds) will pass explicit args to `git push` regardless of any `[push]` config, so persistent config saves only manual typing. Defer Path B until empirical friction surfaces.

### Q4 — `_gate_helpers.py:559` protected-branch regex: leave dead-code (Path A) or clean inline (Path B)?

The regex hardcodes `pos-v2` as a protected branch name. Post-rename, no `pos-v2` branch exists; the regex element is harmless dead-code. Per D-RBPH1.5.5.

**Persona recommendation:** Path A (leave for Phase 2 sweep). Phase 1 fence stays narrow; the dead-code is harmless. Path B is acceptable as a tiny inline edit if the builder finds it obviously safe and composable.

### Q5 — Phase-2 + Phase-3 plan-doc slug pattern (carry-forward decision)

Phase 2 + Phase 3 plan-docs aren't authored yet but will follow this Phase 1's slug pattern. Should they be `rebrand-phase-2-current-state-docs` + `rebrand-phase-3-historical-archive` (descriptive; consistent with this Phase 1 slug)? Or follow some other naming convention?

**Persona recommendation:** Use the descriptive slug pattern (`rebrand-phase-2-current-state-docs`, `rebrand-phase-3-historical-archive`) — composes with the priority-queue restructure direction (descriptive slugs, not version-number prefixes) and with this Phase 1 slug.

---

## §10 — Estimated AI-time

Per `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_duration_estimation_rubric.md`:

- **Plan-doc authoring** (this dispatch): 25-45 min, midpoint ~35 min. Plan-doc + audit research (verified ref counts, branch-state diagnosis, decisions-doc cross-read). **Actual at land time: TBD** (logged post-hoc per duration-estimation-rubric calibration discipline).

- **Build cycle** (downstream, post-ratification):
  - **Branch-rename ops** (worktree disposition + `git branch -m` + verify state): 10-20 min, midpoint ~15 min. Includes the `ivers-corp` worktree check + orphan-main disposition per Q1 path + `framework-only` deletion per Q2 path (local + remote conditional on owner ratification at execution).
  - **Push-config update** (Path A: zero work; Path B: small `.git/config` edit + verify): 0-10 min, midpoint ~3 min.
  - **`CLAUDE.dev.md` scrub** (6 line edits + structural-meaning preservation review): 5-15 min, midpoint ~10 min.
  - **workspace-sync string updates** (3 edit sites + verify tests still GREEN): 10-20 min, midpoint ~15 min. Test verification dominates.
  - **Push-command-string updates in `release-roadmap.md` per Q4 Path A** (1 line edit at line 102 + grep verify no other `pos-v2:main` strings): 3-8 min, midpoint ~5 min.
  - **Outcome-altitude probe + writeup** (fresh clone + 3-probe execution + writeup at scratch path): 15-30 min, midpoint ~22 min. Includes the actual `git clone` against the post-publish-or-pre-publish remote state per Q5 publish-ordering ratification.
  - **Plan-doc + manifest scaffolding + seal narrative** (sealed-cycle ritual): 20-30 min, midpoint ~25 min.
  - **HARD smoke per `feedback_hard_smoke_per_minor_before_publish` if Phase 1 ships as MINOR-class** (cold install + branch state verify + first-impression checklist re-run against fresh stranger-clone): 20-40 min, midpoint ~30 min. May fold into the AC.RBPH1.5 outcome-altitude probe (clarify at build time).
  - **Total Phase 1 build AI-time:** 83-173 min, midpoint **~125 min** (~2 hours). HARD smoke folds into AC.RBPH1.5 probe partially; if fully separate, total midpoint ~155 min.

Owner ratification time (separate from AI-time): ~10-15 min for plan-doc review + Q1-Q5 rulings (5 questions, mostly persona-recommendation-confirms).

---

## §11 — Authority chain

- `docs/VALUE_PROPOSITION.md` — prime objective.
- `docs/plans/loam-rename-decisions.md` (approved 2026-04-23) — rebrand naming + tier authority.
- `docs/release-roadmap.md` — branch-state references + publish-flow context.
- `docs/release-versioning-policy.md` — class definitions (PATCH vs MINOR for Phase 1).
- `docs/plans/release-roadmap-priority-queue-restructure.md` (in-flight) — slug-style + class-derivation pattern.
- `docs/STATE.md` 2026-05-04 entry — `framework-only` deprecation + post-seal-cleanup-deferred ruling.
- `docs/odd-llm-grounding.lean.md` — methodology authority.
- `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_*.md` — discipline rules cited inline.
- `~/.claude/CLAUDE.md` + `/Users/lukeivers/pos3/CLAUDE.md` — global + project instructions.

This plan-doc inherits the authority of `docs/plans/loam-rename-decisions.md` (which it executes) and Q7 ratification 2026-05-09 (Telegram 10594; phased shape; no commit-history rewrite; Tier 3 = move-to-archive; Tier 4 = SKIP).

---

## §12 — §status (post-build backfill)

To be filled at build seal time. Template:

- AC.RBPH1.1 — Branch rename + orphan-main disposition: VERDICT TBD; evidence: `git branch -a` output snapshot + `git rev-parse main` SHA.
- AC.RBPH1.2 — Push-refspec updated: VERDICT TBD; evidence: `grep -r "pos-v2:main"` returning empty + `cat .git/config` snapshot.
- AC.RBPH1.3 — workspace-sync strings updated: VERDICT TBD; evidence: `grep` empty + `pytest framework/workspace-sync/tests/` GREEN.
- AC.RBPH1.4 — `CLAUDE.dev.md` scrubbed: VERDICT TBD; evidence: per-Tier-1-file grep counts all 0 + manual structural-meaning review notes.
- AC.RBPH1.5 (outcome-altitude) — Fresh-clone outsider 60-second read: VERDICT TBD; evidence: writeup at `<workspace>/.scratch/claude-output/rebrand-phase-1-outcome-probe-2026-05-XX.md` with all three probes documented.
- AC.RBPH1.S — Seal-diff: VERDICT TBD; evidence: `git diff --name-only` between BASELINE + SEAL_COMMIT under fence only.

Q1-Q5 ratifications recorded inline with the build-cycle commits (or as a §"Pre-build ratifications" note in the seal narrative per the standard amendment-cycle ritual).
