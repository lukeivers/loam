# FBE.10 sub-plan — close BLOCKER-FBE9.1 (workspace-bootstrap local-path clones must materialise `framework-only`)

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-03.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/plans/v0-1-0-foldback-scope-expansion.md` (FBE.10 row to be backfilled in §8 register at completion).
**Programme master:** `docs/plans/oss-v0-1-0-publish.md`.
**Predecessors:** FBE.{1,2,2b,2c,3,4,5,5b,7,8,6b,9} all sealed (`21b9480`, `8d2b770`, `47ccb3a`, `1d6ff13`, `becf183`, `99c03a6`, `bc56f0d`, `48bb7e2`, `a102bde`, `cc66b08`, `08589ce`, `308d7b4`); FBE.6 apply at `364c37d` (apply-only; seal intentionally pending — FBE.6 stays the FOLDBACK record). Parent §8 backfilled for FBE.9 at `ec85052` (current canonical HEAD).
**BASELINE (pre-build tip):** `ec85052` — current canonical pos-v2 HEAD (FBE.9 §8 backfill commit).

---

## 1. Summary / TLDR

FBE.10 closes **BLOCKER-FBE9.1** with a minimal one-component source-side fix in `framework/workspace-bootstrap/`: mirror the `framework-only` materialisation step that `_resolve_url_to_clone_source` runs for URL-form canonical sources at the local-path branch in `bootstrap_new_workspace`. Concretely: when the canonical source is a local path, run `git -C <local_path> update-ref refs/heads/framework-only refs/remotes/origin/framework-only` before passing `local_path` to `_clone_canonical`, with the same fail-soft semantics (non-zero exit ignored — the downstream checkout step diagnoses absence precisely).

**Why this is the right fix shape:** the URL-form path already mirrors this exact step at `_resolve_url_to_clone_source` (lines 247–280) for the same root cause — `git clone` propagates only LOCAL refs, so a clone-of-a-clone loses any `framework-only` that exists only as a remote-tracking ref on the intermediate. The local-path branch (lines 569–572 pre-FBE.10) skipped the materialisation step because the original assumption was that `local_path` would be canonical pos-v2 directly (which has `framework-only` as a LOCAL branch). FBE.9's auto-default-to-cwd makes the typical `local_path` a stranger's `git clone <canonical-url>` of canonical, which has `framework-only` ONLY as `refs/remotes/origin/framework-only` — exactly the case this materialisation step handles.

**Sealed-component fence (verified at sub-plan time):**
- `framework/workspace-bootstrap/` — single-component fence carrying the source fix + a new test asserting the local-path-clone-of-canonical case is now handled.
- `framework/hands-off-lifecycle/` — narrative-only seal anchor (HOL `frozen_baseline: true` per amendment #23 + prior FBE precedent).

Every edit maps to a named AC. ODD §2.5 negative AC: nothing else.

---

## 2. Halt-and-surface BEFORE build

### Surface #1 (no halt — recorded; fix-shape interpretation)

The dispatcher's brief specifies: "mirror the `_resolve_url_to_clone_source` materialisation step at the local-path branch, so `framework-only` is locally materialised when the canonical source is a local path (not just a remote URL)." The natural insertion point is after the `local_path = Path(canonical_source).expanduser().resolve()` validation (lines 524–535) and before the `_clone_canonical(clone_source, framework_dir)` call (line 574). Two implementation shapes:

- **Shape A (inline at the local-path branch in `bootstrap_new_workspace`):** add a small `subprocess.run(["git", "-C", str(local_path), "update-ref", ...])` block just before `clone_source = str(local_path)` (line 572).
- **Shape B (extract a helper `_materialise_framework_only_branch(path: Path) -> None` and call it from both `_resolve_url_to_clone_source` AND the local-path branch):** factors out the duplicated logic; cleaner code shape.

**Decision (autonomous, builder's call per ODD §1.1):** Shape B (helper extraction) — the duplicated subprocess.run block is a textbook DRY case + the fail-soft semantics need to be identical across both call sites; one helper enforces that. Helper lives in the same module as a private `_materialise_framework_only_branch` function. ~5 LOC for the helper + 3 LOC for the inline call at the local-path branch + a 3-line replacement at `_resolve_url_to_clone_source` (call the helper instead of inline subprocess.run) = ~15 LOC net. Mode-A semantics preserved (both call sites pass the path that needs materialisation; neither call site changes semantics for any other case).

### Surface #2 (no halt — recorded; test scope)

The existing `test_AC_SFR_5_stranger_clones_canonical.py` covers the URL-form path implicitly (the fixture canonical has `framework-only` as a local branch; `make_fixture_canonical` returns the canonical itself). The bug is at the local-path branch when `local_path` is itself a clone of canonical (a stranger's `git clone <canonical-url>` of the canonical). To exercise the bug + verify the fix, the new test must:
1. Build a fixture canonical (with `framework-only` as a local branch — what `make_fixture_canonical` already produces).
2. Clone the fixture canonical into a second path (the "stranger's clone of canonical" — `framework-only` is now ONLY a remote-tracking ref).
3. Pass that second path as `canonical_source` to `bootstrap_new_workspace` and verify it succeeds (the resulting workspace's `framework/` has the `framework-only` branch checked out).

Pre-FBE.10, this test would have failed with `git checkout -B framework-only origin/framework-only ... failed (exit 128): "fatal: 'origin/framework-only' is not a commit"`. Post-FBE.10, the test passes.

The new test file: `framework/workspace-bootstrap/tests/test_AC_FBE_10_1_local_path_clone_of_canonical.py`. Per ODD §2.5: this test maps directly to AC.FBE.10.2.

### Surface #3 (no halt — recorded; sealed-component fence)

Single-component fence: `framework/workspace-bootstrap/`. Per FBE.4/FBE.5/FBE.5b/FBE.6/FBE.6b/FBE.9 partner-prefix gap precedent: workspace-bootstrap lives at `framework/workspace-bootstrap/` (canonical shape) — apply tool should derive cleanly with no corrective needed. Mirror FBE.9's clean apply outcome. If a corrective is needed at apply, mirror FBE.4's recipe (`0c4d9a0`).

### Surface #4 (no halt — recorded; HOL narrative-only contribution)

Per FBE.6/FBE.6b/FBE.8/FBE.9 precedent: HOL `frozen_baseline: true` in the manifest; HOL contributes only the seal narrative anchor at `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe10`. No HOL source/test edits.

### Surface #5 (no halt — recorded; clean-tree workaround for `loam amend seal`)

Per every prior FBE.x: pre-existing untracked + dirty paths will need `git stash push --include-untracked` to unblock the seal command. Stash popped clean post-seal. Same workaround as FBE.{2,3,4,5,5b,6,7,8,6b,9}.

### Surface #6 (no halt — recorded; `loam amend apply` may not auto-commit — manual commit fallback)

Per FBE.6b Surface #5 + FBE.9 Surface #3: `loam amend apply` may modify sidecars + BASELINE literal but NOT auto-commit. Be alert for the same pattern; manually commit if needed via `chore(amend): FBE.10 apply`. Per memory `feedback_no_amend_in_agent_dispatches`: NEW commit, never `--amend`.

### Surface #7 (no halt — recorded; smoke verification)

The dispatcher's smoke is the FBE.9 BLOCKER-FBE9.1 reproduction:
```
git clone /Users/lukeivers/ivers-corp-pos-v2 /tmp/loam-fbe10-smoke
cd /tmp/loam-fbe10-smoke
python3.13 -m venv .venv && .venv/bin/pip install -r install-from-source.txt
.venv/bin/loam init /tmp/loam-fbe10-smoke-ws  # no --from
```
Pre-FBE.10: fails at `git checkout -B framework-only origin/framework-only` (exit 128). Post-FBE.10: succeeds end-to-end with the workspace shape (`framework/`, `workspace/`, `.claude/settings.json={}`).

### Surface #8 (no halt — recorded; reviewer probe deferred to FBE.6c)

This amendment does NOT run a stranger-perspective reviewer probe. AC.FBE.10.3 below covers the in-band end-to-end smoke (the FBE.9 BLOCKER-FBE9.1 reproduction now succeeds); the full reviewer-probe re-run is FBE.6c's job per dispatcher's brief ("After it seals → FBE.6c re-runs sweep + smoke + reviewer").

---

## 3. Spec-objective placement

**Binds to:**
- **AC.PO.1 + AC.PO.2** (prime objective per `docs/VALUE_PROPOSITION.md`) — the documented install flow must produce a working stranger experience: clone, install, init, claude. Pre-FBE.10, the README's literal commands (post-FBE.9 `loam init <path>` from inside the cloned tree) fail at the very first step.
- **BLOCKER-FBE9.1** (per FBE.9 status §"Surface FBE.9 #1") — `bootstrap_new_workspace` local-path clone branch doesn't materialise `framework-only`. AC.FBE.10.{1,2,3} close this BLOCKER end-to-end.
- **AC.FBE.10.* (this plan §4)** — every AC ladders to the same parent.

**Ladders to:** AC.FBE.10.* → FBE.6c (re-runs sweep + smoke + reviewer post-FBE.10) → M12 publish-flip → AC.PO.1 + AC.PO.2.

---

## 4. Acceptance criteria (FBE.10.*)

AC family `AC.FBE.10.*` — collision-safe (no prior amendment uses `AC.FBE.10.*`).

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.FBE.10.1** (source fix — helper + local-path call site) | `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py` extracts the `git update-ref refs/heads/framework-only refs/remotes/origin/framework-only` block into a private helper `_materialise_framework_only_branch(path: Path) -> None`. The helper preserves the fail-soft semantics (non-zero exit ignored; downstream checkout step diagnoses absence precisely). The helper is called from BOTH `_resolve_url_to_clone_source` (replacing the existing inline block at lines 263–277) AND from `bootstrap_new_workspace`'s local-path branch (after `local_path` validation at lines 524–535, before `clone_source = str(local_path)` at line 572). | (a) `grep -n "_materialise_framework_only_branch" framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py` shows ≥3 hits (1 def + 2 call sites); (b) the local-path branch's call site is positioned before `clone_source = str(local_path)`; (c) URL-form path's behaviour preserved byte-identically (existing tests pass). |
| **AC.FBE.10.2** (new test — local-path-clone-of-canonical case) | `framework/workspace-bootstrap/tests/test_AC_FBE_10_1_local_path_clone_of_canonical.py` (NEW file) builds a fixture canonical, clones it into a second path (so `framework-only` exists ONLY as `refs/remotes/origin/framework-only` on the second path), passes the second path as `canonical_source` to `bootstrap_new_workspace`, and asserts (a) the bootstrap completes without raising; (b) the resulting workspace's `framework/.git` has `framework-only` checked out as the active branch; (c) the resulting workspace shape is correct (`framework/`, `workspace/.pos/sync-config.yaml`, `.claude/settings.json`). | `pytest framework/workspace-bootstrap/tests/test_AC_FBE_10_1_local_path_clone_of_canonical.py -x -q` exits 0. The test is RED pre-FBE.10 source fix (verified by checking out the pre-fix tree, running the test, observing the `CloneFailedError` raise) and GREEN post-fix. |
| **AC.FBE.10.3** (end-to-end smoke — FBE.9 BLOCKER-FBE9.1 reproduction now succeeds) | The FBE.9 BLOCKER-FBE9.1 reproduction smoke runs end-to-end against post-FBE.10 canonical HEAD: `git clone /Users/lukeivers/ivers-corp-pos-v2 /tmp/loam-fbe10-smoke && cd /tmp/loam-fbe10-smoke && python3.13 -m venv .venv && .venv/bin/pip install -r install-from-source.txt && .venv/bin/loam --version && .venv/bin/loam init /tmp/loam-fbe10-smoke-ws` (no `--from`). Every step exits 0; the resulting workspace shape is correct (`framework/`, `workspace/`, `.claude/settings.json={}`). The transcript is captured in the FBE.10 status file. | Shell sequence run against post-FBE.10 canonical HEAD; transcript captured in `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe10-status-2026-05-03.md`. Every step exits 0; `loam --version` reports `loam 0.1.0`; `loam init` produces `framework/`, `workspace/`, and `.claude/settings.json` with `{}` content. |
| **AC.FBE.10.4** (negative AC — scope discipline) | Edits stay strictly within the workspace-bootstrap fence + the manifest + sub-plan + HOL narrative anchor + parent §8 backfill. NO behaviour changes outside the named source fix in `new_workspace.py` and the new test file; NO architecture changes; NO source-comment scrubs (HIGH-FBE6b.1 explicitly deferred); NO changes to URL-form behaviour beyond the helper-extraction refactor (which preserves byte-identical behaviour); NO changes to other components. | `git diff BASELINE..SEAL_COMMIT --name-only` produces ONLY paths under: (a) `framework/workspace-bootstrap/` (source + new test + sidecar + test_no_sealed_amendments.py BASELINE bump); (b) `framework/hands-off-lifecycle/seals/` (HOL narrative anchor; universal admission); (c) `docs/plans/` (sub-plan + manifest + parent §8 backfill via universal prefix admission). |
| **AC.FBE.10.S** (sealed-component fence) | Sealed-component fence: 1 component — `framework/workspace-bootstrap/` (source + new test; carries the BASELINE bump + sidecar advance). Plus universal-paths admissions for `docs/plans/` + `framework/hands-off-lifecycle/seals/` (the HOL narrative-only seal anchor, mirroring FBE.6/FBE.6b/FBE.8/FBE.9 pattern). HOL `frozen_baseline: true` per amendment #23 + prior FBE precedent. | `git diff BASELINE..SEAL_COMMIT --name-only` matches the AC.FBE.10.4 path-set; workspace-bootstrap fence component's `tests/SEAL_COMMIT` advances via `loam amend seal`; workspace-bootstrap's BASELINE literal in `tests/test_no_sealed_amendments.py` bumps via `loam amend apply` (per non-frozen convention). HOL fence-test passes byte-identically (HOL is universal-only seal-narrative carrier; not in fence). |

**ACs deliberately out of scope (NOT in FBE.10):**
- HIGH-FBE6b.1 source-comment scrub (339 `Amendment #N` references) — explicit dispatcher-deferral.
- Mode-B `loam init .` semantics — bigger than FBE.9's "small fix" framing; FUTURE_IDEAS_DRAFT candidate.
- M12 publish-flip — gated behind FBE.6c GO; separate dispatch.
- FBE.6c re-runs (synth + sweeps + reviewer) — separate dispatch post-FBE.10 seal.
- FBE.6 pending seal — leave as FOLDBACK record per FBE.6b's path-forward Decision 5.
- Doc-side updates (none needed — the smoke flow uses the post-FBE.9 `loam init <path>` invocation that's already documented correctly).

---

## 5. Three-lens analysis

### Lens 1 — Claude-leverage-first
The fix is a small subprocess.run refactor in workspace-bootstrap — no Claude-native primitive to lean on, no extension surface. Lens 1 PASS by composition (every prior FBE.x amendment paid the Lens 1 cost; FBE.10 closes their cycle).

### Lens 2 — Harness + primary-persona value
- **Primary-persona test:** PASS. The fix is the difference between "stranger reads README, runs `loam init <path>` from inside cloned loam tree, hits `git checkout -B framework-only origin/framework-only ... failed (exit 128)` within 30s" and "stranger reads README, runs the documented invocation, reaches a working `loam --version` + first-session greeting". Translation burden drops to zero on the install path.
- **Harness test:** PASS by composition. The toolkit gains nothing new structurally, but the bootstrap path becomes truthful — the harness is reachable.

### Lens 3 — ODD authoring
Outcome ACs only (§4); method (helper extraction Shape B vs inline Shape A) is the builder's call but constrained by the fail-soft semantics + DRY composition. Per ODD §2.5: every line of the diff maps to AC.FBE.10.{1,2,3,4}. No defensive code; no other source edits; no preemptive Mode-B implementation.

### Lens 4 — Prompt scope ↔ confidence
High confidence in outcome shape: the dispatcher's brief named the precise file + the precise behaviour ("mirror the `_resolve_url_to_clone_source` materialisation step at the local-path branch"). Tight scope.

### Lens 5 — Swarming
FBE.10 is a single small source-side fix + a single new test + the standard apply/seal ritual. Per F3 stopping criterion: stop when split adds only coordination overhead. A single-agent main-thread sequence completes faster than spawning sub-agents. `max_planner_depth = 0`. Model = Sonnet (default; no rationale needed).

---

## 6. File-by-file map

### 6.1 `framework/workspace-bootstrap/` (sealed-component fence)

**`framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py`:**

- **NEW helper `_materialise_framework_only_branch(path: Path) -> None`** (insert above `_resolve_url_to_clone_source` at ~line 209): runs `git -C <path> update-ref refs/heads/framework-only refs/remotes/origin/framework-only` with the existing fail-soft semantics (non-zero exit ignored; the downstream `_clone_canonical` checkout step surfaces absence precisely). Docstring names the two call sites (URL-form via `_resolve_url_to_clone_source`; local-form via `bootstrap_new_workspace`'s local-path branch) and the root cause (`git clone` propagates only LOCAL refs, so a clone-of-a-clone loses any `framework-only` that exists only as a remote-tracking ref on the intermediate).

- **`_resolve_url_to_clone_source` (lines 247–280):** replace the inline `subprocess.run(["git", "-C", str(cache_path), "update-ref", ...])` block with a single call `_materialise_framework_only_branch(cache_path)`. Preserve the surrounding comment block (the rationale stays accurate; only the implementation moves to the helper).

- **`bootstrap_new_workspace` local-path branch (line 572 area):** insert `_materialise_framework_only_branch(local_path)` just before `clone_source = str(local_path)`. Add a comment block above naming the same root cause + the FBE.10 closure.

**`framework/workspace-bootstrap/tests/test_AC_FBE_10_1_local_path_clone_of_canonical.py`** (NEW file):
- Imports: `subprocess`, `Path` from `pathlib`, `pytest`, the `bootstrap_new_workspace` API, the `make_fixture_canonical` fixture from conftest.
- Single test: `test_AC_FBE_10_1_local_path_clone_of_canonical_materialises_framework_only`. Steps:
  1. Build fixture canonical at `tmp_path / "canonical"` (gets `framework-only` as a local branch).
  2. Clone the fixture canonical into `tmp_path / "stranger-clone"` via `subprocess.run(["git", "clone", str(canonical), str(stranger_clone)])`. Verify pre-call: `git -C stranger-clone branch --list framework-only` returns empty (only `pos-v2` is local; `framework-only` is `refs/remotes/origin/framework-only` only).
  3. Call `bootstrap_new_workspace(new_ws_path=tmp_path / "ws", canonical_source=str(stranger_clone))`. Pre-FBE.10 source fix: this raises `CloneFailedError`. Post-fix: returns `BootstrapResult` cleanly.
  4. Assert the workspace shape: `(ws / "framework").is_dir()`, `(ws / "framework" / ".git").is_dir()`, `(ws / "workspace" / ".pos" / "sync-config.yaml").exists()`, `(ws / ".claude" / "settings.json").exists()`.
  5. Assert the framework checkout is on `framework-only`: `git -C ws/framework rev-parse --abbrev-ref HEAD` returns `framework-only`.

**`framework/workspace-bootstrap/tests/SEAL_COMMIT`** (sidecar): advances to FBE.10 seal SHA via `loam amend seal`.

**`framework/workspace-bootstrap/tests/test_no_sealed_amendments.py`** (line 184 BASELINE literal): bumps via `loam amend apply` (per non-frozen convention). Pre-FBE.10: `BASELINE = "cd2a77e"`. Post-FBE.10: bumps to the post-source-edit pre-apply tip.

### 6.2 HOL narrative-only seal anchor (universal admission)

**`framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe10`** (NEW file): mirrors FBE.6/FBE.6b/FBE.8/FBE.9 pattern. Single seal-narrative anchor file; HOL `frozen_baseline: true` in the manifest (no fence-component edit beyond the anchor file).

### 6.3 Plan-doc + manifest (universal_paths.prefixes: `docs/plans/`)

- `docs/plans/v0-1-0-foldback-scope-expansion-fbe10.md` (this file, NEW commit).
- `docs/plans/v0-1-0-foldback-scope-expansion-fbe10.manifest.yaml` (NEW commit).

### 6.4 Parent plan-doc backfill (post-seal, separate commit)

- `docs/plans/v0-1-0-foldback-scope-expansion.md` §8 — ADD a new `### FBE.10 — close BLOCKER-FBE9.1 (workspace-bootstrap local-path clones must materialise framework-only)` subsection with apply commit SHA + seal commit SHA + AC surface + verification summary; update the closing sequence narrative.

### 6.5 Sidecar bumps within sealed-component fence

- `framework/workspace-bootstrap/tests/SEAL_COMMIT` advances to FBE.10 seal SHA via `loam amend seal`.
- `framework/workspace-bootstrap/tests/test_no_sealed_amendments.py` BASELINE literal bumps via `loam amend apply`.
- `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe10` (NEW narrative anchor file; mirrors FBE.6/FBE.6b/FBE.8/FBE.9 pattern; HOL `frozen_baseline: true`).

**TOTAL fence diff:** ~15 LOC source edits in `new_workspace.py` (1 NEW helper + 1 inline call site + 1 inline call-site replacement) + 1 NEW test file (~50 LOC) + 1 narrative anchor file + plan-doc + manifest YAML + parent plan §8 backfill.

---

## 7. Smoke verification

**Smoke (AC.FBE.10.3):** runs POST-seal so it exercises the seal-bumped tree.

```bash
# Pre-test cleanup
cd /tmp && rm -rf loam-fbe10-smoke loam-fbe10-smoke-ws

# Stranger-clone smoke (the FBE.9 BLOCKER-FBE9.1 reproduction)
git clone /Users/lukeivers/ivers-corp-pos-v2 /tmp/loam-fbe10-smoke
cd /tmp/loam-fbe10-smoke
python3.13 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r install-from-source.txt
.venv/bin/loam --version       # → loam 0.1.0

# AC.FBE.10.3 — no --from from inside a stranger's clone of canonical
.venv/bin/loam init /tmp/loam-fbe10-smoke-ws

# AC.FBE.10.3 — verify workspace shape
ls /tmp/loam-fbe10-smoke-ws/{framework,workspace,.claude}
cat /tmp/loam-fbe10-smoke-ws/.claude/settings.json    # → {}
git -C /tmp/loam-fbe10-smoke-ws/framework rev-parse --abbrev-ref HEAD  # → framework-only

# Cleanup
rm -rf /tmp/loam-fbe10-smoke /tmp/loam-fbe10-smoke-ws
```

**Failure modes:**
- Any step exits non-zero → halt; surface; do not iterate.
- The `git checkout -B framework-only origin/framework-only` failure recurs → the helper extraction or the local-path call-site insertion has a bug.

---

## 8. Hard constraints

- 1 sealed-component fence (`framework/workspace-bootstrap/`) + universal-paths admission for `docs/plans/` + `framework/hands-off-lifecycle/seals/` (HOL narrative anchor).
- HOL narrative-only seal anchor (no fence-component edit; HOL frozen-baseline narrative pattern).
- No new external runtime deps.
- No `git commit --amend` per `feedback_no_amend_in_agent_dispatches`.
- `loam amend apply` invoked BEFORE seal commit per `feedback_dispatch_explicit_pos_amend_apply`.
- AC-prefix `AC.FBE.10.*` (collision-safe).
- Auto-memory `MEMORY.md` NOT touched.
- Component-scoped test rerun per `feedback_amendment_dispatch_speedups`: only the workspace-bootstrap fence component's tests run post-seal.
- Per FBE.4/FBE.5/FBE.5b/FBE.6/FBE.6b/FBE.9 partner-prefix gap precedent: `framework/workspace-bootstrap/` is canonical `framework/<name>/` shape; partner-prefix derivation should run cleanly. Apply hand-corrective if it recurs.
- Negative AC.FBE.10.4: no scope expansion beyond the source fix + new test + manifest + plan + narrative anchor; no source-comment scrubs (HIGH-FBE6b.1 deferred); no changes to other components; no doc edits.
- ODD §2.5 — every line of the diff maps to AC.FBE.10.{1..4}. No defensive code for cases ACs don't name.

---

## 9. Out of scope (per ODD §2.5)

- HIGH-FBE6b.1 source-comment scrub (339 `Amendment #N` references) — explicit dispatcher-deferral; FUTURE_IDEAS_DRAFT candidate for v0.1.x source-comment scrub.
- Mode-B `loam init .` semantics (re-init the cloned tree as workspace) — bigger than "small fix"; FUTURE_IDEAS_DRAFT candidate.
- M12 publish-flip — gated behind FBE.6c GO; separate dispatch.
- FBE.6c re-runs (synth + sweeps + reviewer) — separate dispatch post-FBE.10 seal.
- Backfilling FBE.6's pending seal commit — leave as FOLDBACK record per FBE.6b's path-forward Decision 5.
- Edits to other components' source files beyond workspace-bootstrap.
- Doc-side updates — none needed; the smoke flow uses the post-FBE.9 `loam init <path>` invocation that's already documented correctly.
- Refactor of `_clone_canonical`'s two-step flow (clone → checkout -B) — preserved verbatim; the helper extraction only moves the materialisation step into a shared function.

---

## 10. Halt-and-surface (during build)

Per `feedback_subagent_odd_violation_halt`:

- **HT-1:** WD drifts to pos3 → halt immediately.
- **HT-2:** Fix requires touching components beyond workspace-bootstrap → halt + surface; that widens the fence.
- **HT-3:** Sealed-component fence breach beyond plan-named (workspace-bootstrap + universal admissions + HOL narrative) → halt + surface.
- **HT-4:** Partner-prefix bug recurs → apply hand-corrective per FBE.4/FBE.5 precedent (`0c4d9a0` / `e20445f`).
- **HT-5:** Build cycle exceeds 60 min wall-clock → halt with partial findings (per dispatcher's halt-trigger #6).
- **HT-6:** Post-edit smoke (AC.FBE.10.3) regresses (any step exits non-zero) → halt + surface; uncovers ANOTHER latent bug → foldback re-opens.
- **HT-7:** ODD §2.5 violation discovered in any touched file → halt + surface; do NOT silently extend or fix in-band.
- **HT-8:** Smoke uncovers ANOTHER latent bug beyond BLOCKER-FBE9.1 → halt + surface; foldback re-opens (dispatcher's halt-trigger #3).

---

## 11. Risks

- **Risk: helper extraction breaks URL-form behaviour.** The refactor moves the `subprocess.run(["git", "-C", ..., "update-ref", ...])` block into a helper. If the helper's signature/semantics drift from the inline block, URL-form regresses. Mitigation: helper is a literal extraction (same arguments, same fail-soft semantics, same return); existing URL-form tests must pass byte-identically.
- **Risk: new test fixture doesn't reproduce the bug.** If the cloning step doesn't replicate the "framework-only as remote-tracking ref only" condition, the test passes both pre- and post-fix and doesn't catch the regression. Mitigation: explicit pre-call assertion `git -C stranger-clone branch --list framework-only` returns empty (verifies the bug pre-condition holds); test the pre-fix tree to confirm RED.
- **Risk: smoke uncovers ANOTHER latent bug.** Per dispatcher's halt-trigger #3: halt + surface. The most-likely-next-failure shape would be downstream in `bootstrap_new_workspace` (e.g., scaffold step) or in `pos-sync` first-run; mitigation = halt + surface; do NOT silently extend.
- **Risk: Partner-prefix gap recurs.** Per FBE.4/FBE.5 precedent. Mitigation: apply with watchful eye; hand-correct if needed; document in seal narrative.
- **Risk: `loam amend apply` doesn't auto-commit.** Per FBE.6b Surface #5 + FBE.9 Surface #3. Mitigation: manually commit per `chore(amend): FBE.10 apply` pattern; NEW commit, never `--amend`.

---

## 12. Sequencing (commit ladder)

1. **Plan-doc commit** (this file authored alone, NEW commit).
2. **Source + new test commit** — single commit covering `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py` + the new test file `framework/workspace-bootstrap/tests/test_AC_FBE_10_1_local_path_clone_of_canonical.py`.
3. **HOL seal narrative anchor commit** — `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe10` NEW file (mirrors FBE.6/FBE.6b/FBE.8/FBE.9 pattern).
4. **Manifest commit** — author `docs/plans/v0-1-0-foldback-scope-expansion-fbe10.manifest.yaml` (1 fence component: workspace-bootstrap; HOL narrative-only via universal admission).
5. **`loam amend apply`** — invoke against the manifest. Produces apply-bookkeeping commit (BASELINE bump in workspace-bootstrap; sidecar advances). If it doesn't auto-commit, manually commit per FBE.6b/FBE.9 precedent.
6. **Corrective commit (if partner-prefix gap recurs)** — per FBE.4/FBE.5 precedent.
7. **`loam amend seal`** — produces deterministic seal commit; sidecars advance to seal SHA; narrative appends.
8. **Smoke verification (AC.FBE.10.3)** — POST-seal; verify shipped behaviour against the seal-bumped tree.
9. **Parent plan-doc backfill** — `docs/plans/v0-1-0-foldback-scope-expansion.md` §8 add `### FBE.10` subsection with apply + seal SHAs (separate NEW commit; admitted via `docs/plans/` universal prefix).
10. **Status file write** — `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe10-status-2026-05-03.md` with seal report.

NO `git commit --amend` at any point. NO push to any remote.

---

## 13. References

- **FBE.9 status (BLOCKER-FBE9.1 origin):** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe9-status-2026-05-03.md`.
- **FBE.9 sub-plan:** `docs/plans/v0-1-0-foldback-scope-expansion-fbe9.md`.
- **FBE.6b status (BLOCKER-FBE6b.1 origin):** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe6b-status-2026-05-03.md`.
- **FBE.6b sweep report:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-0-foldback-fbe6b-sweep-report.md`.
- **Parent plan:** `docs/plans/v0-1-0-foldback-scope-expansion.md` §8 register FBE.9 row + closing sequence.
- **bootstrap_new_workspace contract:** `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py:459-632` (BLOCKER-FBE9.1 origin at lines 569-572).
- **`_resolve_url_to_clone_source` materialisation step (the URL-form mirror):** `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py:247-280`.
- **AC.SFR.5 stranger-clones-canonical test (related):** `framework/workspace-bootstrap/tests/test_AC_SFR_5_stranger_clones_canonical.py`.
- **Memory bullets honoured:**
  - `feedback_plan_before_code` (this is the plan; no code yet).
  - `feedback_no_amend_in_agent_dispatches` (commit ladder uses NEW commits only).
  - `feedback_dispatch_explicit_pos_amend_apply` (apply step explicit in §12).
  - `feedback_subagent_odd_violation_halt` (HT-1 through HT-8).
  - `feedback_amendment_dispatch_speedups` (test rerun scoped to workspace-bootstrap component only).
  - `feedback_summarize_and_surface_decisions` (Surfaces 1-8 explicit).
  - `feedback_specific_claims_verified_or_marked_guess` (every "verified at" claim has a path/line citation; SHAs computed empirically not guessed).
  - `feedback_critical_thinking_on_deviations` (Surface #1 weighed Shape A vs Shape B by outcome × cost × risk).
  - `feedback_value_proposition_as_prime_objective` (FBE.10 ladders to AC.PO.1 + AC.PO.2 via FBE.6c → M12).
  - `feedback_principle_conflict_resolution_multi_signal` (Surface #1 Shape A vs Shape B resolved via the multi-signal process: scope-confidence × DRY-composition × fail-soft-semantics-uniformity).

---

## 14. AI-time band

- Predicted: **20–40 min, midpoint 30 min**; dispatch hard cap 60 min.
- Justification: 1 small source-side helper extraction (~15 LOC) + 1 NEW test file (~50 LOC) + manifest YAML + apply (1-fence; partner-prefix watchful eye) + seal + smoke + parent §8 backfill + status file. Per rubric: 1-component amendment with surgical source + test edits is closer to 20-30 min midpoint; widen upper bound for the smoke verification + potential partner-prefix corrective.

---

## 15. Method-decision register (post-build)

(Populated as commits land.)

- Plan-doc commit: `<TBD>`.
- Source + new test commit: `<TBD>`.
- HOL narrative anchor commit: `<TBD>`.
- Manifest commit: `<TBD>`.
- Apply commit: `<TBD>`.
- Corrective commit (if needed): `<TBD>`.
- Seal commit: `<TBD>`.
- Parent plan-doc §8 backfill commit: `<TBD>`.

---

*End of FBE.10 sub-plan-doc. Ready to build.*
