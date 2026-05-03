# FBE.6d sub-plan — re-run FBE.6c close-cycle against post-FBE.11 canonical HEAD (dual-ref staging path)

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-03.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` (FBE.6d row to be backfilled in §8 register at completion; FBE.11 row at lines 853-892 records the dual-ref push closure of BLOCKER-FBE6c.1; FBE.6d is the re-verification cycle post-FBE.11).
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md`.
**Predecessors:** FBE.{1,2,2b,2c,3,4,5,5b,7,8,6b,9,10,6c,11} all sealed (`21b9480`, `8d2b770`, `47ccb3a`, `1d6ff13`, `becf183`, `99c03a6`, `bc56f0d`, `48bb7e2`, `a102bde`, `cc66b08`, `08589ce`, `308d7b4`, `428deeb`, `6fd3812`, `771e649`); FBE.6 apply at `364c37d` (apply-only; seal intentionally pending — FBE.6 stays the FOLDBACK record).
**BASELINE (pre-build tip):** `e834a98` — current canonical pos-v2 HEAD (the FBE.11 §8 register backfill commit).

---

## 1. Summary / TLDR

FBE.6d is the **fourth re-run** of the close-the-cycle step against post-FBE.11 canonical HEAD. The cycle so far:

- **FBE.6** → FOLDBACK (BLOCKER-FBE6.1 install-flow doc + BLOCKER-FBE6.2 loam-cli dev-vocabulary)
- **FBE.8** → closed both BLOCKERs + seal-debt
- **FBE.6b** → FOLDBACK (NEW BLOCKER-FBE6b.1 README/getting-started.md `loam init .` doesn't match CLI's required `--from`)
- **FBE.9** → closed BLOCKER-FBE6b.1 (Path B: `--from` optional + cwd-default-when-git-tree); SURFACED BLOCKER-FBE9.1
- **FBE.10** → closed BLOCKER-FBE9.1 (extracted `_materialise_framework_only_branch` helper + call from local-path branch)
- **FBE.6c** → FOLDBACK (NEW BLOCKER-FBE6c.1 publish pushes `framework-only:main` only; stranger clones can't find `origin/framework-only`)
- **FBE.11** → closed BLOCKER-FBE6c.1 via Path B (publish-side dual-ref push: `framework-only:main framework-only:framework-only`); operator-instruction doc edits at `oss-v0-1-0-publish-dry-run.md` AC.M11a.7 + parent §4 AC.FBE.6.4

FBE.6d mirrors FBE.6c's structure but executes against the post-FBE.11 tree AND uses the new dual-ref staging path (per dispatcher's brief):

1. Re-synthesises `framework-only` from canonical HEAD `e834a98` (FBE.11 §8 register backfill).
2. Re-runs all 8 AC.M11a.* sweeps — expecting zero regressions (FBE.11 was doc-only at operator-instruction surfaces; nothing in source was touched).
3. Runs the EXTENDED smoke (UPDATED for dual-ref push per dispatcher's brief): operator-side dual-ref push to a fresh local bare staging → stranger clones the bare → install → `loam init <ws>` end-to-end. This exercises the full README-literal stranger flow with the fix from FBE.11 in place.
4. Pushes synth to staging via the new dual-ref shape (`git push <staging-url> framework-only:main framework-only:framework-only --force`).
5. Re-dispatches the stranger-perspective reviewer agent (fresh-context Task subagent OR in-band per FBE.6/FBE.6b/FBE.6c precedent if Task tool not exposed). The reviewer should test the full public-URL flow (the dual-ref-pushed staging is now stranger-correct).
6. Reviewer's verdict GO → foldback closes; M12 publish-flip is the next dispatch.
   Reviewer's verdict NEW BLOCKER → halt + surface; foldback re-opens.

**Negative AC:** zero source/doc edits during FBE.6d. If reviewer surfaces a new BLOCKER, do NOT silently fix in FBE.6d — surface to dispatcher.

**Sealed-component fence:** hands-off-lifecycle only (HOL no-op narrative anchor pattern; `frozen_baseline: true` per amendment #23 + FBE.6/FBE.6b/FBE.8/FBE.9/FBE.10/FBE.6c/FBE.11 manifest precedent). Narrative seal at `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe6d` (sibling to FBE.6/FBE.6b/FBE.8/FBE.9/FBE.10/FBE.6c/FBE.11 narratives; mirrors precedent).

---

## 2. Halt-and-surface BEFORE build

### Surface #1 (no halt — recorded; smoke flow uses dual-ref staging path per dispatcher's brief)

The dispatcher's brief specifies the EXTENDED smoke uses a FRESH local bare staging + dual-ref push + stranger-clone-from-bare. This is a meaningful change from FBE.6c's smoke (which cloned the canonical pos-v2 directly with `--branch framework-only --single-branch`). The new shape exercises the FULL stranger flow including the publish-side dual-ref behaviour FBE.11 documented:

```
# Step 1: simulate the operator's dual-ref publish push to a tmp staging
cd /tmp && rm -rf loam-fbe6d-staging.git loam-fbe6d-test loam-fbe6d-test-ws
git init --bare loam-fbe6d-staging.git
cd /Users/lukeivers/ivers-corp-pos-v2
git push /tmp/loam-fbe6d-staging.git framework-only:main framework-only:framework-only
# Step 2: simulate stranger clone-and-install from staging
cd /tmp
git clone /tmp/loam-fbe6d-staging.git loam-fbe6d-test
cd loam-fbe6d-test
python3.13 -m venv .venv
.venv/bin/pip install -r install-from-source.txt
.venv/bin/loam --version
.venv/bin/loam init /tmp/loam-fbe6d-test-ws
ls /tmp/loam-fbe6d-test-ws/{framework,workspace,.claude}
ls ~/.loam/  # scaffolded
```

This is the **dispositive** test for BLOCKER-FBE6c.1 closure: the stranger clone of a dual-ref-pushed staging gets `refs/remotes/origin/framework-only`, and `loam init <ws>` then succeeds (rather than failing with `fatal: 'origin/framework-only' is not a commit`).

### Surface #2 (no halt — recorded; staging push uses dual-ref shape now)

Per FBE.11's documentation update at `oss-v0-1-0-publish-dry-run.md` AC.M11a.7 + parent §4 AC.FBE.6.4: the staging push command is now `git push <staging-url> framework-only:main framework-only:framework-only --force` (single invocation; both refspecs in one command). FBE.6d uses this command verbatim per the documented operator instruction. Verify both refs land via `git ls-remote <staging-url>` showing both `refs/heads/main` AND `refs/heads/framework-only` at the same SHA.

### Surface #3 (no halt — recorded; reviewer agent dispatched in-band if Task tool not exposed)

The reviewer agent (AC.FBE.6d.5) is dispatched via Task tool with a fresh-context prompt mirroring the original `loam-user-review-2026-05-03.md` framing: stranger-perspective + Ruthless Feedback principle + walk-through-the-install-path. If Task tool not exposed (per FBE.6/FBE.6b/FBE.6c precedent), reviewer probe is done in-band via fresh-clone + literal-command walk-through from the staging URL. Reviewer's verdict — GO or NEW BLOCKER — is the close-or-reopen signal for the foldback.

### Surface #4 (no halt — recorded; loam-amend ergonomic patterns + clean-tree-requirement workaround)

Per FBE.{8,6b,9,10,6c,11} precedent (5 consecutive recurrences now): (a) `loam amend apply` does NOT auto-commit by design (per dispatcher's brief — apply.py has ZERO git commit calls; only seal.py creates commits). After running apply, MANUALLY commit via `git commit -m "chore(amend): FBE.6d apply ..."`. This is convention, not a regression. Do NOT report this as a regression. (b) `loam amend seal` requires clean working tree — pre-existing untracked + dirty paths in canonical require `git stash push --include-untracked` to unblock. FBE.6d should expect both to recur and apply the same workarounds.

### Surface #5 (no halt — recorded; cycle gate at AC.FBE.6d.5)

The reviewer's verdict is the gate. If GO, AC.FBE.6d.* all close, sweep report records GO, status file authored, FBE.6d seals via narrative anchor, M12 publish-flip dispatches as the next step. If reviewer surfaces a NEW BLOCKER not covered by FBE.{1..10,6b,6c,11}, halt + surface to dispatcher (do NOT silently fix; foldback re-opens). HIGH-severity findings get triaged: HIGH-FBE6b.1 (339 `Amendment #N` source-comment references) is already deferred per FBE.6b/FBE.9/FBE.10/FBE.6c/FBE.11 path-forward; if reviewer re-surfaces it, document as known limitation in v0.1.0 release notes.

### Surface #6 (no halt — recorded; smoke shape is the FULL stranger flow now)

FBE.6c's smoke cloned the LOCAL canonical pos-v2 path directly (which always has `refs/heads/framework-only` AND `refs/remotes/origin/framework-only`); the BLOCKER-FBE6c.1 was exposed only by the SEPARATE reviewer probe that cloned the public staging URL. FBE.6d's smoke uses the dual-ref-pushed staging path that EXACTLY matches what a stranger sees post-FBE.11 publish. This means the smoke and the reviewer probe both exercise the same flow shape; the reviewer probe is the user-facing-language verification, the smoke is the mechanical step-by-step verification.

---

## 3. Spec-objective placement

**Binds to:**
- **AC.PO.1 + AC.PO.2** (prime objective per `docs/rebuild/VALUE_PROPOSITION.md`) — closing the v0.1.0 foldback cycle so the publish-flip can happen.
- **Parent plan §5 cycle gate #2** ("FBE.6 closes GO — sweep PASS, extended smoke PASS, reviewer agent verdict GO (or non-blocking HIGH only)") — FBE.6d is the executor of this gate post-FBE.11.
- **AC.FBE.6.* (parent plan §4 FBE.6)** — the FBE.6d ACs reuse the FBE.6/FBE.6b/FBE.6c AC structure with `.6d.` slug.

**Ladders to:** AC.FBE.6d.* → M12 publish-flip → AC.PO.1 + AC.PO.2.

---

## 4. Acceptance criteria (FBE.6d.*)

AC family `AC.FBE.6d.*` — mirrors FBE.6/FBE.6b/FBE.6c AC structure with same verification mechanisms; the only conceptual differences are (a) BASELINE (post-FBE.11 `e834a98` vs FBE.6c's post-FBE.10 `a87bc87`), (b) smoke flow uses the dual-ref staging path (per dispatcher's brief), (c) staging push uses the dual-ref command (per FBE.11's doc).

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.FBE.6d.1** | `pos-publish-framework-only` re-runs from canonical HEAD `e834a98`; produces a fresh `framework-only` branch SHA (advance from FBE.6c's `19422ed`). Synth exit code 0. | Build a venv with `pos-publish-framework-only` editable-installed (+ `pyyaml` per FBE.6c Surface #2 known issue); run against `--source HEAD`; assert exit 0; record new branch SHA. |
| **AC.FBE.6d.2** | All 8 AC.M11a.* sweeps from the M11a-3 sweep report re-run and PASS — **with zero regressions** (banned literals + dev-vocabulary scrub, substitution tokens, wired-component, MFBM-dep all per-FBE.6c baseline). | Per-sweep `git grep` against the new `framework-only` SHA: 8 banned literals (AC.M11a.2) → all zero hits; 4 source-side substitution tokens (AC.M11a.3) → all zero hits; per-component production-caller count (AC.M11a.4) → ≥1 callers; 6 memory-system deps × N pyprojects (AC.M11a.5) → all zero hits. |
| **AC.FBE.6d.3** | EXTENDED smoke (dispatcher's exact step list: dual-ref push to fresh local bare → stranger clone → install → `loam init <ws>`) exercises the full documented dual-ref publish + stranger-flow install path end-to-end, including `loam init` producing a runnable workspace with `.claude/settings.json`. | Shell sequence per dispatcher brief: `cd /tmp && rm -rf loam-fbe6d-staging.git loam-fbe6d-test loam-fbe6d-test-ws && git init --bare loam-fbe6d-staging.git && cd /Users/lukeivers/ivers-corp-pos-v2 && git push /tmp/loam-fbe6d-staging.git framework-only:main framework-only:framework-only && cd /tmp && git clone /tmp/loam-fbe6d-staging.git loam-fbe6d-test && cd loam-fbe6d-test && python3.13 -m venv .venv && .venv/bin/pip install -r install-from-source.txt && .venv/bin/loam --version && .venv/bin/loam init /tmp/loam-fbe6d-test-ws && ls /tmp/loam-fbe6d-test-ws/{framework,workspace,.claude} && ls ~/.loam/`. Every step exits 0; final `loam init` produces a runnable workspace; `.claude/settings.json` exists. |
| **AC.FBE.6d.4** | Push synth to staging via dual-ref (`git push https://github.com/lukeivers/loam-staging.git framework-only:main framework-only:framework-only --force` per FBE.11 documented operator instruction). Confirm BOTH remote `main` AND remote `framework-only` SHAs match local. | `git push` exits 0; `git ls-remote https://github.com/lukeivers/loam-staging.git` shows both `refs/heads/main` AND `refs/heads/framework-only` at the new SHA matching the FBE.6d.1 synth SHA. |
| **AC.FBE.6d.5** | Re-dispatch the stranger-perspective reviewer agent (new instance, no prior context) against the new staging tree. Reviewer's verdict = GO or surfaces a NEW BLOCKER not covered by FBE.{1..10,6b,6c,11}. The dual-ref-pushed staging is now stranger-correct (per FBE.11 smoke); reviewer probes the full README-literal flow. | Task-tool dispatch with stranger-perspective + Ruthless Feedback brief mirroring `loam-user-review-2026-05-03.md`; reviewer's report attached to FBE.6d sweep report. If Task tool not exposed (per FBE.6/FBE.6b/FBE.6c precedent), in-band fresh-clone walk-through from staging URL. |
| **AC.FBE.6d.6** | Sweep report authored at `<workspace>/.scratch/claude-output/v0-1-0-foldback-fbe6d-sweep-report.md`. | File exists post-build; carries per-AC PASS/FAIL table + reviewer verdict + halt-and-surface findings (if any). |
| **AC.FBE.6d.7** | Negative AC: zero source/doc edits during FBE.6d. | `git diff e834a98..SEAL_COMMIT --name-only` produces only paths under: (a) `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe6d` (NEW narrative file), (b) `docs/rebuild/plans/` (sub-plan + manifest + parent backfill via universal admission), (c) `framework/hands-off-lifecycle/tests/SEAL_COMMIT` (apply step's frozen-baseline-aware sidecar bump). No source or doc edits outside the plans/seals scope. |
| **AC.FBE.6d.S** | Sealed-component fence: hands-off-lifecycle (frozen_baseline: true; HOL no-op narrative anchor pattern). Anchor at `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe6d` per parent plan §4 FBE.6.S clause + FBE.6/FBE.6b/FBE.8/FBE.9/FBE.10/FBE.6c/FBE.11 manifest precedent. | The narrative file is created and committed; HOL sidecar bump via `loam amend apply`; seal commit lands cleanly via `loam amend seal` (FBE.8 closed the pre-existing H19 + HC#4 debt that blocked FBE.6's seal; FBE.{6b,9,10,6c,11} confirmed clean seal pipeline). |

---

## 5. Three-lens analysis

### Lens 1 — Claude-leverage-first
Reviewer-agent re-dispatch (AC.FBE.6d.5) is a Claude-native primitive: spawn a fresh-context sub-agent with stranger-perspective brief; let it walk the staging tree. No re-implementation. Lens 1 PASS.

### Lens 2 — Harness + primary-persona value
- **Primary-persona test:** PASS. The verdict measures whether a stranger's primary-persona-equivalent first-run experience works. Reviewer agent IS the stranger-perspective measurement.
- **Harness test:** PASS. FBE.6d doesn't add to the toolkit; it is the gate making the v0.1.0 toolkit publishable. Closes the cycle (or re-opens it).

### Lens 3 — ODD authoring
Outcome ACs only (§4); method (which exact venv path, which exact `git grep` invocation, how to format the reviewer brief) is the builder's call but constrained by FBE.6/FBE.6b/FBE.6c's verification mechanisms + the M11a-3 sweep report's contract.

### Lens 4 — Prompt scope ↔ confidence
High confidence in outcome shape: dispatcher named the AC set + the smoke-step list (UPDATED for dual-ref) + the negative AC + the seal pattern (mirror FBE.6c). Tight scope. The single uncertainty is the reviewer's verdict (GO vs new BLOCKER) — the LOOSEST scope point because the reviewer needs latitude to find things FBE.{1..11} missed. Reviewer's brief uses the original loam-user-review's loose framing so they can think broadly.

### Lens 5 — Swarming
FBE.6d has natural decomposition opportunities (sweeps run in parallel; smoke is sequential; reviewer is a sub-agent). Per FBE.6c actuals (~40-55 min wall-clock; sweeps + smoke + reviewer + report + manifest + apply + seal + status), critical path: synth → sweeps → smoke → push → reviewer → report → seal. Reviewer is one level of decomposition (`max_planner_depth = 1`); other steps run in main thread. Model = Sonnet (default; no rationale needed per F3).

---

## 6. File-by-file map

### Source change
**None.** AC.FBE.6d.7 is a negative AC. FBE.6d is a sweep + smoke + review amendment.

### Plan-doc paper trail (universal-paths admission):
- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe6d.md` — this sub-plan (NEW).
- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe6d.manifest.yaml` — amendment manifest (NEW).
- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` — parent §8 FBE.6d register backfill at completion.

### Narrative seal anchor:
- `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe6d` — narrative anchor file (NEW; sibling to FBE.6/FBE.6b/FBE.8/FBE.9/FBE.10/FBE.6c/FBE.11 narratives).

### Status file:
- `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe6d-status-2026-05-03.md` — per-AC outcome + SHAs + halt-and-surface (NEW).

### Sweep report:
- `<workspace>/.scratch/claude-output/v0-1-0-foldback-fbe6d-sweep-report.md` — per-AC verification details + reviewer verdict (NEW).

---

## 7. Method (builder's call, recorded for reproducibility)

### 7.1 Re-synth (AC.FBE.6d.1)
- Build venv: `python3.13 -m venv /tmp/fbe6d-synth-venv && /tmp/fbe6d-synth-venv/bin/pip install -e /Users/lukeivers/ivers-corp-pos-v2/framework/tools/pos-publish-framework-only && /tmp/fbe6d-synth-venv/bin/pip install pyyaml` (per FBE.6c Surface #2 known issue).
- Invoke: `/tmp/fbe6d-synth-venv/bin/pos-publish-framework-only --repo /Users/lukeivers/ivers-corp-pos-v2 --source HEAD`.
- Capture exit code + new `framework-only` branch SHA via `git -C /Users/lukeivers/ivers-corp-pos-v2 rev-parse framework-only`.

### 7.2 Sweeps (AC.FBE.6d.2)
Per-sweep `git grep` against the new `framework-only` SHA — same invocations as FBE.6/FBE.6b/FBE.6c §7.2.

**AC.M11a.2 — banned literals (8):** `pos-amend`, `loam-amend`, `loam-mode`, `docs/rebuild/`, `odd-methodology`, `odd-in-loam`, `duration-estimation-rubric`, `pos-publish-framework-only`. For each: `git grep -F -l <literal> framework-only | wc -l` → expect 0.

**AC.M11a.3 — substitution tokens (4):** `/Users/lukeivers/ivers-corp-pos-v2/`, `/Users/lukeivers/ivers-corp-pos-v2`, `lukeivers/pos-v2`, `Luke Ivers`. For each: `git grep -F -l <token> framework-only | wc -l` → expect 0.

**AC.M11a.4 — wired-component sweep:** for each shipping component (15+): `git grep -F -l "loam.<snake_case>" framework-only -- '*.py' | wc -l` → expect ≥1. Verify zero `tests/` files: `git ls-tree -r --name-only framework-only | grep '/tests/' | wc -l` → expect 0.

**AC.M11a.5 — MFBM dep sweep (6 tokens × N pyprojects):** tokens `graphiti`, `kuzu`, `ollama`, `sentence-transformers`, `fastmcp`, `BGE`. For each pyproject + each token: `grep -ic <token>` → sum 0 across all.

### 7.3 Extended smoke (AC.FBE.6d.3)
Per dispatcher brief, exact sequence (dual-ref staging path):
```
cd /tmp && rm -rf loam-fbe6d-staging.git loam-fbe6d-test loam-fbe6d-test-ws
git init --bare loam-fbe6d-staging.git
cd /Users/lukeivers/ivers-corp-pos-v2
git push /tmp/loam-fbe6d-staging.git framework-only:main framework-only:framework-only
cd /tmp
git clone /tmp/loam-fbe6d-staging.git loam-fbe6d-test
cd loam-fbe6d-test
python3.13 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r install-from-source.txt
.venv/bin/loam --version
.venv/bin/loam init /tmp/loam-fbe6d-test-ws
ls /tmp/loam-fbe6d-test-ws/{framework,workspace,.claude}
ls ~/.loam/
```
Capture exit codes + stdout + final `ls` of `.claude/` + `~/.loam/` for the sweep report.

### 7.4 Staging push (AC.FBE.6d.4)
- Verify auth: `gh auth status`.
- Push: `git push https://github.com/lukeivers/loam-staging.git framework-only:main framework-only:framework-only --force` per FBE.11 documented operator instruction (single invocation; both refspecs in one command).
- Verify: `git ls-remote https://github.com/lukeivers/loam-staging.git` shows BOTH `refs/heads/main` AND `refs/heads/framework-only` at the new SHA.

### 7.5 Reviewer agent re-dispatch (AC.FBE.6d.5)
- Try Task tool first; if not exposed (per FBE.6/FBE.6b/FBE.6c precedent), fall back to in-band fresh-clone walk-through from staging URL.
- Brief mirrors `loam-user-review-2026-05-03.md`:
  - Stranger-perspective: assume no prior knowledge of pos-v2, loam, the foldback.
  - Ruthless Feedback: name disagreement, name evidence, name alternative.
  - Walk-through: clone → install → first-run command (`loam init <ws>` no `--from`) → first claude session.
  - Use the staging URL `https://github.com/lukeivers/loam-staging` (post-AC.FBE.6d.4 push).
  - Output: BLOCKER / HIGH / LOW findings + verdict (GO / FOLDBACK).
- Capture reviewer's full report inline in the FBE.6d sweep report.

### 7.6 Sweep report + status file
- Sweep report at `<workspace>/.scratch/claude-output/v0-1-0-foldback-fbe6d-sweep-report.md`: per-AC PASS/FAIL table, sweep details, smoke transcript, reviewer verdict + report excerpt.
- Status file at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe6d-status-2026-05-03.md`: SHAs ladder, per-AC outcomes, halt-and-surface (if any), one-paragraph summary for the dispatcher.

### 7.7 Manifest + apply + seal
- Manifest YAML mirrors FBE.6/FBE.6b/FBE.8/FBE.9/FBE.10/FBE.6c/FBE.11's HOL no-op narrative anchor (frozen_baseline: true). Sealed-component fence: hands-off-lifecycle only.
- `loam amend apply` — admits the universal-paths plan/seal scope. Per dispatcher's brief: apply does NOT auto-commit by design (apply.py has zero git commit calls; only seal.py creates commits). After running apply, MANUALLY commit via `git commit -m "chore(amend): FBE.6d apply ..."`.
- `loam amend seal` — produces the seal commit attaching the narrative. Expect clean-tree requirement (Surface #4); `git stash push --include-untracked` to unblock then pop post-seal.

### 7.8 Parent plan backfill
- Edit `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` §8 — add new FBE.6d row (after FBE.11 row at lines 853-892), record sub-plan/manifest/seal SHAs.

---

## 8. Out of scope (NOT in FBE.6d)

- Source/doc edits (negative AC.FBE.6d.7) — if reviewer surfaces a new BLOCKER, foldback re-opens; do NOT silently fix in FBE.6d.
- M12 publish-flip — FBE.6d closes (or re-opens) the foldback cycle; M12 is the next dispatch (gated on GO).
- §14 master plan backfill in `oss-v0-1-0-publish.md` — at M12-time per parent plan §5 cycle gate #4.
- Re-edit of FBE.6/FBE.6b/FBE.8/FBE.9/FBE.10/FBE.6c/FBE.11 existing seal narratives — FBE.6d authors a sibling narrative.
- HIGH-FBE6b.1 (339 `Amendment #N` source-comment references) — explicit dispatcher-deferral; v0.1.x candidate; document as known limitation in v0.1.0 release notes.
- FBE.6 pending seal — leave as FOLDBACK record per FBE.6b/FBE.9/FBE.10/FBE.6c/FBE.11 path-forward Decision 5.
- `loam amend apply` no-auto-commit pattern — per dispatcher's brief, this is convention not a regression. Do NOT report as regression.
- `pos-publish-framework-only` pyproject `pyyaml` runtime dep (FBE.6c Surface #2) — out of scope for FBE.6d; FUTURE_IDEAS_DRAFT candidate.

---

## 9. Halt triggers

Per dispatcher's brief + parent plan §4 FBE.6 halt-triggers (reproduced):

1. WD drifts to pos3 → halt immediately.
2. Reviewer surfaces a new BLOCKER → halt + surface; do NOT silently fix; foldback re-opens.
3. Extended smoke fails at any step → halt + surface which step + which previous FBE.x amendment regressed.
4. Synth re-run fails → halt; partition manifest invalid.
5. Build cycle exceeds 90 min wall-clock → halt with partial findings.

---

## 10. Risks

- **Risk: synth re-run regresses something subtle.** Mitigation: 8 sweeps catch the known regression shapes; if anything else surfaces, halt-trigger #4 fires.
- **Risk: smoke uncovers ANOTHER latent bug beyond what FBE.{8,9,10,6c,11} closed.** Per dispatcher's halt-trigger #3: halt + surface. The most-likely-next-failure shape would be downstream (e.g., post-`loam init` first-`claude`-session failure), but the dual-ref staging path matches what FBE.11's local-tmp-ref smoke verified works.
- **Risk: reviewer surfaces a NEW BLOCKER.** Per dispatcher's halt-trigger #2 + FBE.6b/FBE.9/FBE.6c negative-AC pattern: halt + surface; do NOT silently fix.
- **Risk: staging push fails.** Per FBE.6/FBE.6b/FBE.6c precedent: dual-ref command per FBE.11 doc; verify both refs land. If auth fails, halt + surface (this gates M12).
- **Risk: dual-ref push to staging accidentally fast-forwards rather than force-overwrites a divergent branch.** Mitigation: use `--force` flag per FBE.11 doc instruction.

---

## 11. AI-time band

- Predicted: **25–40 min, midpoint 32 min**; dispatch hard cap 90 min.
- Justification: FBE.6c actuals were 40–55 min; FBE.6d is the same shape (sub-plan + synth + sweeps + smoke + push + reviewer + sweep report + manifest + apply + seal + parent §8 backfill + status file). FBE.6d may be slightly faster than FBE.6c because (a) sweeps are unlikely to surface new regressions (FBE.11 was doc-only at operator-instruction surfaces, did not touch source), (b) the smoke uses the dual-ref staging shape that FBE.11's local-tmp-ref smoke already verified works, (c) the apply-no-auto-commit pattern is now expected (no investigation time). The reviewer probe is the LOOSEST point — if it surfaces a new BLOCKER, that's the foldback signal; status authoring takes longer.

---

## 12. Method-decision register (post-build)

(Populated as commits land.)

- Plan-doc commit: `<TBD>`.
- HOL narrative anchor commit: `<TBD>`.
- Manifest commit: `<TBD>`.
- Apply commit: `<TBD>`.
- Seal commit: `<TBD>`.
- Parent plan-doc §8 backfill commit: `<TBD>`.

---

*End of FBE.6d sub-plan-doc. BASELINE `e834a98`. Next: re-synth → sweeps → smoke (dual-ref) → push (dual-ref) → reviewer → report → seal → §8 backfill.*
