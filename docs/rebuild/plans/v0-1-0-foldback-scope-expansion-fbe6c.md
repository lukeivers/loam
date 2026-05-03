# FBE.6c sub-plan — re-run FBE.6b close-cycle against post-FBE.10 canonical HEAD

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-03.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` (FBE.6c row to be backfilled in §8 register at completion; FBE.6 row at lines 614-652 is the original FOLDBACK record; FBE.8 row at lines 654-678 records the source-side fixes; FBE.6b row at lines 680-709 is the first re-verification (FOLDBACK to FBE.9); FBE.9 row at lines 711-752 closes BLOCKER-FBE6b.1 + surfaces NEW BLOCKER-FBE9.1; FBE.10 row at lines 776-818 closes BLOCKER-FBE9.1; FBE.6c is the re-verification cycle post-FBE.10).
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md`.
**Predecessors:** FBE.{1,2,2b,2c,3,4,5,5b,7,8,6b,9,10} all sealed (`21b9480`, `8d2b770`, `47ccb3a`, `1d6ff13`, `becf183`, `99c03a6`, `bc56f0d`, `48bb7e2`, `a102bde`, `cc66b08`, `08589ce`, `308d7b4`, `428deeb`); FBE.6 apply at `364c37d` (apply-only; seal intentionally pending — FBE.6 stays the FOLDBACK record).
**BASELINE (pre-build tip):** `a87bc87` — current canonical pos-v2 HEAD (the FBE.10 §8 register backfill commit).

---

## 1. Summary / TLDR

FBE.6c is the **re-run** of FBE.6b's close-the-cycle step against post-FBE.10 canonical HEAD. The cycle so far:

- **FBE.6** → FOLDBACK (BLOCKER-FBE6.1 install-flow doc + BLOCKER-FBE6.2 loam-cli dev-vocabulary)
- **FBE.8** → closed both BLOCKERs + seal-debt
- **FBE.6b** → FOLDBACK (NEW BLOCKER-FBE6b.1 README/getting-started.md `loam init .` doesn't match CLI's required `--from`)
- **FBE.9** → closed BLOCKER-FBE6b.1 (Path B: `--from` optional + cwd-default-when-git-tree) + comprehensive doc-vs-CLI sweep; SURFACED BLOCKER-FBE9.1 (workspace-bootstrap local-path branch latent bug)
- **FBE.10** → closed BLOCKER-FBE9.1 (extracted `_materialise_framework_only_branch` helper + call from local-path branch); FBE.10's end-to-end smoke verifies the full stranger-clone install path now works against post-FBE.10 canonical HEAD

FBE.6c mirrors FBE.6b's structure but executes against the post-FBE.10 tree:

1. Re-synthesises `framework-only` from canonical HEAD `a87bc87` (FBE.10 §8 register backfill).
2. Re-runs all 8 AC.M11a.* sweeps — expecting zero regressions (FBE.6b verified all clean post-FBE.8; nothing in FBE.{9,10} would re-introduce dev-vocabulary or banned literals).
3. Runs the EXTENDED smoke (full documented install path including stranger-clone + `loam init <ws>` no `--from` per FBE.10's smoke shape).
4. Pushes synth to `lukeivers/loam-staging` `main`.
5. Re-dispatches the stranger-perspective reviewer agent (fresh-context Task subagent OR in-band per FBE.6b/FBE.9 precedent if Task tool not exposed).
6. Reviewer's verdict GO → foldback closes; M12 publish-flip is the next dispatch.
   Reviewer's verdict NEW BLOCKER → halt + surface; foldback re-opens.

**Negative AC:** zero source/doc edits during FBE.6c. If reviewer surfaces a new BLOCKER, do NOT silently fix in FBE.6c — surface to dispatcher.

**Sealed-component fence:** hands-off-lifecycle only (HOL no-op narrative anchor pattern; `frozen_baseline: true` per amendment #23 + FBE.6/FBE.6b/FBE.8/FBE.9/FBE.10 manifest precedent). Narrative seal at `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe6c` (sibling to FBE.6/FBE.6b/FBE.8/FBE.9/FBE.10 narratives; mirrors precedent).

---

## 2. Halt-and-surface BEFORE build

### Surface #1 (no halt — recorded; smoke flow uses post-FBE.9/FBE.10 shape)

The dispatcher's brief specifies the smoke step list as the full documented install path including stranger-clone + `loam init <ws>` (no `--from`):
```
cd /tmp && rm -rf loam-fbe6c-test loam-fbe6c-test-ws
git clone --branch framework-only --single-branch \
  /Users/lukeivers/ivers-corp-pos-v2 loam-fbe6c-test
cd loam-fbe6c-test
python3.13 -m venv .venv
.venv/bin/pip install -r install-from-source.txt
.venv/bin/loam --version
.venv/bin/loam init /tmp/loam-fbe6c-test-ws
ls /tmp/loam-fbe6c-test-ws/{framework,workspace,.claude}
ls ~/.loam/   # scaffolded
```
This is FBE.10's smoke shape (no `--from` because FBE.9 made it optional + FBE.10 made the local-path-clone work). FBE.10's status already verified this works against canonical HEAD; FBE.6c verifies it works against the freshly-pushed `framework-only` branch SHA.

### Surface #2 (no halt — recorded; staging push needs `--force`)

FBE.6/FBE.6b surfaced (Surface FBE.6 #5 + FBE.6b #1) that `--force-with-lease` cache rejects stale info; plain `--force` succeeds. FBE.6c uses plain `--force` directly per the established pattern (no need to try `--force-with-lease` first).

### Surface #3 (no halt — recorded; reviewer agent dispatched in-band if Task tool not exposed)

The reviewer agent (AC.FBE.6c.5) is dispatched via Task tool with a fresh-context prompt mirroring the original `loam-user-review-2026-05-03.md` framing: stranger-perspective + Ruthless Feedback principle + walk-through-the-install-path. If Task tool not exposed (per FBE.6 + FBE.6b precedent), reviewer probe is done in-band via fresh-clone + literal-command walk-through from the staging URL. Reviewer's verdict — GO or NEW BLOCKER — is the close-or-reopen signal for the foldback.

### Surface #4 (no halt — recorded; partner-prefix bug + clean-tree-requirement workaround)

Per FBE.{8,6b,9,10} precedent: (a) `loam amend apply` may not auto-commit (3 consecutive recurrences in FBE.6b/FBE.9/FBE.10 — pattern strong) — manually commit if needed via `chore(amend): FBE.6c apply`; (b) `loam amend seal` requires clean working tree — pre-existing untracked + dirty paths in canonical require `git stash push --include-untracked` to unblock. FBE.6c should expect both to recur and apply the same workarounds.

### Surface #5 (no halt — recorded; cycle gate at AC.FBE.6c.5)

The reviewer's verdict is the gate. If GO, AC.FBE.6c.* all close, sweep report records GO, status file authored, FBE.6c seals via narrative anchor, M12 publish-flip dispatches as the next step. If reviewer surfaces a NEW BLOCKER not covered by FBE.{1..5,5b,2b,2c,7,8,6b,9,10}, halt + surface to dispatcher (do NOT silently fix; foldback re-opens). HIGH-severity findings get triaged: HIGH-FBE6b.1 (339 `Amendment #N` source-comment references) is already deferred per FBE.6b/FBE.9/FBE.10 path-forward; if reviewer re-surfaces it, document as known limitation in v0.1.0 release notes.

### Surface #6 (no halt — recorded; smoke shape change post-FBE.{9,10})

Pre-FBE.9 smoke required `--from <repo>` (the `loam init` command demanded it). Post-FBE.9 + post-FBE.10, smoke runs `loam init <ws>` from inside the cloned tree with NO `--from` (the dispatcher's brief specifies this shape). This means FBE.6c's smoke exercises the FULL documented post-FBE.{9,10} install path that a stranger would actually follow — the README's literal commands. FBE.6b's smoke (with explicit `--from`) was a workaround for the missing FBE.9 fix; FBE.6c's smoke is the production-equivalent shape.

---

## 3. Spec-objective placement

**Binds to:**
- **AC.PO.1 + AC.PO.2** (prime objective per `docs/rebuild/VALUE_PROPOSITION.md`) — closing the v0.1.0 foldback cycle so the publish-flip can happen.
- **Parent plan §5 cycle gate #2** ("FBE.6 closes GO — sweep PASS, extended smoke PASS, reviewer agent verdict GO (or non-blocking HIGH only)") — FBE.6c is the executor of this gate post-FBE.10.
- **AC.FBE.6.* (parent plan §4 FBE.6)** — the FBE.6c ACs reuse the FBE.6/FBE.6b AC structure with `.6c.` slug.

**Ladders to:** AC.FBE.6c.* → M12 publish-flip → AC.PO.1 + AC.PO.2.

---

## 4. Acceptance criteria (FBE.6c.*)

AC family `AC.FBE.6c.*` — mirrors FBE.6/FBE.6b AC structure with same verification mechanisms; the only conceptual difference is the BASELINE (post-FBE.10 `a87bc87` vs FBE.6b's post-FBE.8 `f0f9253`).

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.FBE.6c.1** | `pos-publish-framework-only` re-runs from canonical HEAD `a87bc87`; produces a fresh `framework-only` branch SHA (advance from FBE.6b's `8f57bde`). Synth exit code 0. | Build a venv with `pos-publish-framework-only` editable-installed; run against `--source HEAD`; assert exit 0; record new branch SHA. |
| **AC.FBE.6c.2** | All 8 AC.M11a.* sweeps from the M11a-3 sweep report re-run and PASS — **with zero regressions** (banned literals + dev-vocabulary scrub, substitution tokens, wired-component, MFBM-dep all per-FBE.6b baseline). | Per-sweep `git grep` against the new `framework-only` SHA: 8 banned literals (AC.M11a.2) → all zero hits; 4 source-side substitution tokens (AC.M11a.3) → all zero hits; per-component production-caller count (AC.M11a.4) → ≥1 callers; 6 memory-system deps × N pyprojects (AC.M11a.5) → all zero hits. |
| **AC.FBE.6c.3** | EXTENDED smoke (dispatcher's exact step list, post-FBE.{9,10} shape with NO `--from`) exercises the full documented install path end-to-end, including `loam init` producing a runnable workspace with `.claude/settings.json`. | Shell sequence per dispatcher brief: `cd /tmp && rm -rf loam-fbe6c-test loam-fbe6c-test-ws && git clone --branch framework-only --single-branch /Users/lukeivers/ivers-corp-pos-v2 loam-fbe6c-test && cd loam-fbe6c-test && python3.13 -m venv .venv && .venv/bin/pip install -r install-from-source.txt && .venv/bin/loam --version && .venv/bin/loam init /tmp/loam-fbe6c-test-ws && ls /tmp/loam-fbe6c-test-ws/{framework,workspace,.claude} && ls ~/.loam/`. Every step exits 0; final `loam init` produces a runnable workspace; `.claude/settings.json` exists. |
| **AC.FBE.6c.4** | Push synth to staging (`git push https://github.com/lukeivers/loam-staging.git framework-only:main` per FBE.6/FBE.6b URL-direct precedent). Confirm remote SHA matches local. | `git push` exits 0; `git ls-remote https://github.com/lukeivers/loam-staging.git refs/heads/main` shows new SHA matching the FBE.6c.1 synth SHA. |
| **AC.FBE.6c.5** | Re-dispatch the stranger-perspective reviewer agent (new instance, no prior context) against the new staging tree. Reviewer's verdict = GO or surfaces a NEW BLOCKER not covered by FBE.{1..5,5b,2b,2c,7,8,6b,9,10}. | Task-tool dispatch with stranger-perspective + Ruthless Feedback brief mirroring `loam-user-review-2026-05-03.md`; reviewer's report attached to FBE.6c sweep report. If Task tool not exposed (per FBE.6 + FBE.6b precedent), in-band fresh-clone walk-through from staging URL. |
| **AC.FBE.6c.6** | Sweep report authored at `<workspace>/.scratch/claude-output/v0-1-0-foldback-fbe6c-sweep-report.md`. | File exists post-build; carries per-AC PASS/FAIL table + reviewer verdict + halt-and-surface findings (if any). |
| **AC.FBE.6c.7** | Negative AC: zero source/doc edits during FBE.6c. | `git diff a87bc87..SEAL_COMMIT --name-only` produces only paths under: (a) `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe6c` (NEW narrative file), (b) `docs/rebuild/plans/` (sub-plan + manifest + parent backfill via universal admission), (c) `framework/hands-off-lifecycle/tests/SEAL_COMMIT` (apply step's frozen-baseline-aware sidecar bump). No source or doc edits outside the plans/seals scope. |
| **AC.FBE.6c.S** | Sealed-component fence: hands-off-lifecycle (frozen_baseline: true; HOL no-op narrative anchor pattern). Anchor at `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe6c` per parent plan §4 FBE.6.S clause + FBE.6/FBE.6b/FBE.8/FBE.9/FBE.10 manifest precedent. | The narrative file is created and committed; HOL sidecar bump via `loam amend apply`; seal commit lands cleanly via `loam amend seal` (FBE.8 closed the pre-existing H19 + HC#4 debt that blocked FBE.6's seal; FBE.{6b,9,10} confirmed clean seal pipeline). |

---

## 5. Three-lens analysis

### Lens 1 — Claude-leverage-first
Reviewer-agent re-dispatch (AC.FBE.6c.5) is a Claude-native primitive: spawn a fresh-context sub-agent with stranger-perspective brief; let it walk the staging tree. No re-implementation. Lens 1 PASS.

### Lens 2 — Harness + primary-persona value
- **Primary-persona test:** PASS. The verdict measures whether a stranger's primary-persona-equivalent first-run experience works. Reviewer agent IS the stranger-perspective measurement.
- **Harness test:** PASS. FBE.6c doesn't add to the toolkit; it is the gate making the v0.1.0 toolkit publishable. Closes the cycle.

### Lens 3 — ODD authoring
Outcome ACs only (§4); method (which exact venv path, which exact `git grep` invocation, how to format the reviewer brief) is the builder's call but constrained by FBE.6/FBE.6b's verification mechanisms + the M11a-3 sweep report's contract.

### Lens 4 — Prompt scope ↔ confidence
High confidence in outcome shape: dispatcher named the AC set + the smoke-step list + the negative AC + the seal pattern (mirror FBE.6b). Tight scope. The single uncertainty is the reviewer's verdict (GO vs new BLOCKER) — the LOOSEST scope point because the reviewer needs latitude to find things FBE.{1..10} missed. Reviewer's brief uses the original loam-user-review's loose framing so they can think broadly.

### Lens 5 — Swarming
FBE.6c has natural decomposition opportunities (sweeps run in parallel; smoke is sequential; reviewer is a sub-agent). Per FBE.6b actuals (~35–45 min wall-clock; sweeps + smoke + reviewer + report + manifest + apply + seal + status), critical path: synth → sweeps → smoke → push → reviewer → report → seal. Reviewer is one level of decomposition (`max_planner_depth = 1`); other steps run in main thread. Model = Sonnet (default; no rationale needed per F3).

---

## 6. File-by-file map

### Source change
**None.** AC.FBE.6c.7 is a negative AC. FBE.6c is a sweep + smoke + review amendment.

### Plan-doc paper trail (universal-paths admission):
- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe6c.md` — this sub-plan (NEW).
- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe6c.manifest.yaml` — amendment manifest (NEW).
- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` — parent §8 FBE.6c register backfill at completion.

### Narrative seal anchor:
- `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe6c` — narrative anchor file (NEW; sibling to FBE.6/FBE.6b/FBE.8/FBE.9/FBE.10 narratives).

### Status file:
- `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe6c-status-2026-05-03.md` — per-AC outcome + SHAs + halt-and-surface (NEW).

### Sweep report:
- `<workspace>/.scratch/claude-output/v0-1-0-foldback-fbe6c-sweep-report.md` — per-AC verification details + reviewer verdict (NEW).

---

## 7. Method (builder's call, recorded for reproducibility)

### 7.1 Re-synth (AC.FBE.6c.1)
- Build venv: `python3.13 -m venv /tmp/fbe6c-synth-venv && /tmp/fbe6c-synth-venv/bin/pip install -e /Users/lukeivers/ivers-corp-pos-v2/framework/tools/pos-publish-framework-only`.
- Invoke: `/tmp/fbe6c-synth-venv/bin/pos-publish-framework-only --repo /Users/lukeivers/ivers-corp-pos-v2 --source HEAD`.
- Capture exit code + new `framework-only` branch SHA via `git -C /Users/lukeivers/ivers-corp-pos-v2 rev-parse framework-only`.

### 7.2 Sweeps (AC.FBE.6c.2)
Per-sweep `git grep` against the new `framework-only` SHA — same invocations as FBE.6/FBE.6b §7.2.

**AC.M11a.2 — banned literals (8):** `pos-amend`, `loam-amend`, `loam-mode`, `docs/rebuild/`, `odd-methodology`, `odd-in-loam`, `duration-estimation-rubric`, `pos-publish-framework-only`. For each: `git grep -F -l <literal> framework-only | wc -l` → expect 0.

**AC.M11a.3 — substitution tokens (4):** `/Users/lukeivers/ivers-corp-pos-v2/`, `/Users/lukeivers/ivers-corp-pos-v2`, `lukeivers/pos-v2`, `Luke Ivers`. For each: `git grep -F -l <token> framework-only | wc -l` → expect 0.

**AC.M11a.4 — wired-component sweep:** for each shipping component (15+): `git grep -F -l "loam.<snake_case>" framework-only -- '*.py' | wc -l` → expect ≥1. Verify zero `tests/` files: `git ls-tree -r --name-only framework-only | grep '/tests/' | wc -l` → expect 0.

**AC.M11a.5 — MFBM dep sweep (6 tokens × N pyprojects):** tokens `graphiti`, `kuzu`, `ollama`, `sentence-transformers`, `fastmcp`, `BGE`. For each pyproject + each token: `grep -ic <token>` → sum 0 across all.

### 7.3 Extended smoke (AC.FBE.6c.3)
Per dispatcher brief, exact sequence (post-FBE.{9,10} shape — NO `--from`):
```
cd /tmp && rm -rf loam-fbe6c-test loam-fbe6c-test-ws
git clone --branch framework-only --single-branch \
  /Users/lukeivers/ivers-corp-pos-v2 loam-fbe6c-test
cd loam-fbe6c-test
python3.13 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r install-from-source.txt
.venv/bin/loam --version
.venv/bin/loam init /tmp/loam-fbe6c-test-ws
ls /tmp/loam-fbe6c-test-ws/{framework,workspace,.claude}
ls ~/.loam/
```
Capture exit codes + stdout + final `ls` of `.claude/` + `~/.loam/` for the sweep report.

### 7.4 Staging push (AC.FBE.6c.4)
- Verify auth: `gh auth status`.
- Push: use plain `--force` directly per FBE.6/FBE.6b precedent (skip `--force-with-lease`).
- Verify: `git ls-remote https://github.com/lukeivers/loam-staging.git refs/heads/main` shows new SHA.

### 7.5 Reviewer agent re-dispatch (AC.FBE.6c.5)
- Try Task tool first; if not exposed (per FBE.6 + FBE.6b precedent), fall back to in-band fresh-clone walk-through from staging URL.
- Brief mirrors `loam-user-review-2026-05-03.md`:
  - Stranger-perspective: assume no prior knowledge of pos-v2, loam, the foldback.
  - Ruthless Feedback: name disagreement, name evidence, name alternative.
  - Walk-through: clone → install → first-run command (`loam init <ws>` no `--from`) → first claude session.
  - Use the staging URL `https://github.com/lukeivers/loam-staging` (post-AC.FBE.6c.4 push).
  - Output: BLOCKER / HIGH / LOW findings + verdict (GO / FOLDBACK).
- Capture reviewer's full report inline in the FBE.6c sweep report.

### 7.6 Sweep report + status file
- Sweep report at `<workspace>/.scratch/claude-output/v0-1-0-foldback-fbe6c-sweep-report.md`: per-AC PASS/FAIL table, sweep details, smoke transcript, reviewer verdict + report excerpt.
- Status file at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe6c-status-2026-05-03.md`: SHAs ladder, per-AC outcomes, halt-and-surface (if any), one-paragraph summary for the dispatcher.

### 7.7 Manifest + apply + seal
- Manifest YAML mirrors FBE.6/FBE.6b/FBE.8/FBE.9/FBE.10's HOL no-op narrative anchor (frozen_baseline: true). Sealed-component fence: hands-off-lifecycle only.
- `loam amend apply` — admits the universal-paths plan/seal scope. Be alert for the no-auto-commit pattern (3 consecutive recurrences in FBE.6b/FBE.9/FBE.10); manually commit if needed.
- `loam amend seal` — produces the seal commit attaching the narrative. Expect clean-tree requirement (Surface #4); `git stash push --include-untracked` to unblock then pop post-seal.

### 7.8 Parent plan backfill
- Edit `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` §8 — add new FBE.6c row (after FBE.10 row at lines 776-818), record sub-plan/manifest/seal SHAs.

---

## 8. Out of scope (NOT in FBE.6c)

- Source/doc edits (negative AC.FBE.6c.7) — if reviewer surfaces a new BLOCKER, foldback re-opens; do NOT silently fix in FBE.6c.
- M12 publish-flip — FBE.6c closes (or re-opens) the foldback cycle; M12 is the next dispatch (gated on GO).
- §14 master plan backfill in `oss-v0-1-0-publish.md` — at M12-time per parent plan §5 cycle gate #4.
- Re-edit of FBE.6/FBE.6b/FBE.8/FBE.9/FBE.10 existing seal narratives — FBE.6c authors a sibling narrative.
- HIGH-FBE6b.1 (339 `Amendment #N` source-comment references) — explicit dispatcher-deferral; v0.1.x candidate; document as known limitation in v0.1.0 release notes.
- FBE.6 pending seal — leave as FOLDBACK record per FBE.6b/FBE.9/FBE.10 path-forward Decision 5.

---

## 9. Halt triggers

Per dispatcher's brief + parent plan §4 FBE.6 halt-triggers (reproduced):

1. WD drifts to pos3 → halt immediately.
2. Reviewer surfaces a new BLOCKER → halt + surface; do NOT silently fix; foldback re-opens.
3. Extended smoke fails at any step → halt + surface which step + which previous FBE.x amendment regressed.
4. Synth re-run fails → halt; partition manifest invalid.
5. Staging push fails → halt + surface; this gates M12.
6. Build cycle exceeds 90 min wall-clock → halt with partial findings.
7. Reviewer agent observes the install path works but raises a new HIGH-severity finding → surface and triage; HIGH-severity findings may or may not block v0.1.0 GO depending on shape.

---

## 10. Risks

- **Risk: synth re-run regresses something subtle.** Mitigation: 8 sweeps catch the known regression shapes; if anything else surfaces, halt-trigger #4 fires.
- **Risk: smoke uncovers ANOTHER latent bug beyond what FBE.{8,9,10} closed.** Per dispatcher's halt-trigger #3: halt + surface. The most-likely-next-failure shape would be downstream (e.g., post-`loam init` first-`claude`-session failure) but FBE.10's smoke verified the workspace shape is correct.
- **Risk: reviewer surfaces a NEW BLOCKER.** Per dispatcher's halt-trigger #2 + FBE.6b/FBE.9 negative-AC pattern: halt + surface; do NOT silently fix.
- **Risk: `loam amend apply` doesn't auto-commit.** 3 consecutive recurrences (FBE.6b/FBE.9/FBE.10). Mitigation: manually commit per `chore(amend): FBE.6c apply` pattern; NEW commit, never `--amend`.
- **Risk: staging push fails.** Per FBE.6/FBE.6b precedent: use plain `--force` directly. If auth fails, halt + surface (this gates M12).

---

## 11. AI-time band

- Predicted: **25–40 min, midpoint 32 min**; dispatch hard cap 90 min.
- Justification: FBE.6b actuals were 35–45 min; FBE.6c is the same shape (sub-plan + synth + sweeps + smoke + push + reviewer + sweep report + manifest + apply + seal + parent §8 backfill + status file). FBE.6c may be slightly faster than FBE.6b because (a) sweeps are unlikely to surface new regressions (FBE.{9,10} closed scoped issues, did not introduce dev-vocabulary), (b) the smoke is the post-FBE.{9,10} shape that FBE.10 already verified works end-to-end. The reviewer probe is the LOOSEST point — if it surfaces a new BLOCKER, that's the foldback signal; status authoring takes longer.

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

*End of FBE.6c sub-plan-doc. BASELINE `a87bc87`. Next: re-synth → sweeps → smoke → push → reviewer → report → seal → §8 backfill.*
