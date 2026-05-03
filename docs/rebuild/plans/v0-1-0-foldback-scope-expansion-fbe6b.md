# FBE.6b sub-plan — re-run FBE.6 close-cycle against post-FBE.8 canonical HEAD

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-03.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` (FBE.6b row to be backfilled in §8 register; FBE.6 row at lines 614-652 is the FOLDBACK record; FBE.8 row at lines 654-678 records the source-side fixes that closed FBE.6's blockers; FBE.6b is the re-verification).
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md`.
**Predecessors:** FBE.{1,2,2b,2c,3,4,5,5b,7,8} all sealed (`21b9480`, `8d2b770`, `47ccb3a`, `1d6ff13`, `becf183`, `99c03a6`, `bc56f0d`, `48bb7e2`, `a102bde`, `cc66b08`); FBE.6 apply at `364c37d` (apply-only; seal halted on pre-existing FBE.4+FBE.5 debt that FBE.8 closed).
**BASELINE (pre-build tip):** `f0f9253` — current canonical pos-v2 HEAD (the FBE.8 §8 register backfill commit).

---

## 1. Summary / TLDR

FBE.6b is the **re-run** of FBE.6's close-the-cycle step against post-FBE.8 canonical HEAD. FBE.6 dispatched 2026-05-03 surfaced 2 NEW BLOCKERs (BLOCKER-FBE6.1 install-flow doc + BLOCKER-FBE6.2 loam-cli dev-vocabulary), 2 HIGHs, and pre-existing FBE.4+FBE.5 seal-pipeline debt (Surface FBE.6 #6). FBE.8 (`cc66b08`) closed all four buckets. FBE.6b mirrors FBE.6's structure but executes against the post-FBE.8 tree:

1. Re-synthesises `framework-only` from canonical HEAD `f0f9253`.
2. Re-runs all 8 AC.M11a.* sweeps — expecting zero regressions (banned literals + dev-vocabulary scrubbed by FBE.8; substitution tokens, wired-component, MFBM-dep all per-FBE.6 baseline).
3. Runs the EXTENDED smoke (post-FBE.2c clone flow + post-FBE.4 install-from-source.txt) end-to-end including `loam init`.
4. Pushes synth to `lukeivers/loam-staging` `main`.
5. Re-dispatches the stranger-perspective reviewer agent (fresh-context Task subagent, brief mirrors `loam-user-review-2026-05-03.md`).
6. Reviewer's verdict GO → foldback closes; M12 publish-flip is the next dispatch.
   Reviewer's verdict NEW BLOCKER → halt + surface; foldback re-opens (FBE.9 etc).

**Negative AC:** zero source/doc edits during FBE.6b. If reviewer surfaces a new BLOCKER, do NOT silently fix in FBE.6b — surface to dispatcher.

**Sealed-component fence:** hands-off-lifecycle only (HOL no-op narrative anchor pattern; `frozen_baseline: true` per amendment #23 + FBE.6/FBE.8 manifest precedent). Narrative seal at `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe6b` (sibling to FBE.6's existing narrative; mirrors FBE.6 pattern, not a re-edit of it).

---

## 2. Halt-and-surface BEFORE build

### Surface #1 (no halt — recorded; smoke flow is the dispatcher's exact step list)

The dispatcher's brief specifies the smoke step list verbatim (clone with `--branch framework-only --single-branch`, `pip install -r install-from-source.txt`, `loam --version`, `loam init <ws> --from <repo>`, `ls .claude/`, `ls ~/.loam/`). FBE.6 verified this exact sequence works against framework-only `4d105f6`; FBE.6b re-verifies against the post-FBE.8 SHA.

### Surface #2 (no halt — recorded; staging push needs `--force`)

FBE.6 surfaced (Surface FBE.6 #5) that the prior staging remote SHA `c74bc25` was an intermediate synth not tracked by `--force-with-lease` cache; plain `--force` succeeded. FBE.6b can either `git fetch` staging first OR use plain `--force` directly with awareness. Default: try `--force-with-lease` first; fall back to `--force` on stale-info rejection (per FBE.6 precedent).

### Surface #3 (no halt — recorded; reviewer agent dispatched via Task tool)

The reviewer agent (AC.FBE.6b.5) is dispatched via Task tool with a fresh-context prompt mirroring the original `loam-user-review-2026-05-03.md` framing: stranger-perspective + Ruthless Feedback principle + walk-through-the-install-path. Reviewer reads the staging tree (or local synth tree if staging push delayed). Reviewer's verdict — GO or NEW BLOCKER — is the close-or-reopen signal for the foldback.

### Surface #4 (no halt — recorded; partner-prefix bug + clean-tree-requirement workaround)

FBE.8 status Surface #1 + #2 record two recurring `loam amend` ergonomic bugs: (a) `loam amend apply` derives `partner_prefixes` assuming `framework/<name>/` shape — admits bare `loam` for `framework/tools/loam/` (harmless because there's no top-level `loam/`); (b) `loam amend seal` requires clean working tree — pre-existing untracked paths in canonical require `git stash push --include-untracked` to unblock. FBE.6b should expect both to recur and apply the same workarounds (recorded as expected, not surfaced as new findings).

### Surface #5 (no halt — recorded; cycle gate at AC.FBE.6b.5)

The reviewer's verdict is the gate. If GO, AC.FBE.6b.* all close, sweep report records GO, status file authored, FBE.6b seals via narrative anchor. If reviewer surfaces a NEW BLOCKER not covered by FBE.{1..5,5b,2b,2c,7,8}, halt + surface to dispatcher (do NOT silently fix; foldback re-opens). HIGH-severity findings get triaged: may or may not block v0.1.0 GO depending on shape.

---

## 3. Spec-objective placement

**Binds to:**
- **AC.PO.1 + AC.PO.2** (prime objective per `docs/rebuild/VALUE_PROPOSITION.md`) — closing the v0.1.0 foldback cycle so the publish-flip can happen.
- **Parent plan §5 cycle gate #2** ("FBE.6 closes GO — sweep PASS, extended smoke PASS, reviewer agent verdict GO (or non-blocking HIGH only)") — FBE.6b is the executor of this gate post-FBE.8.
- **AC.FBE.6.* (parent plan §4 FBE.6)** — the FBE.6b ACs reuse the FBE.6 AC structure with `.6b.` slug.

**Ladders to:** AC.FBE.6b.* → M12 publish-flip → AC.PO.1 + AC.PO.2.

---

## 4. Acceptance criteria (FBE.6b.*)

AC family `AC.FBE.6b.*` — mirrors FBE.6's AC structure with same verification mechanisms; the only conceptual difference is the BASELINE (post-FBE.8 `f0f9253` vs post-FBE.5b `48bb7e2`).

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.FBE.6b.1** | `pos-publish-framework-only` re-runs from canonical HEAD `f0f9253`; produces a fresh `framework-only` branch SHA (advance from FBE.6's `4d105f6`). Synth exit code 0. | Build a venv with `pos-publish-framework-only` editable-installed; run against `--source HEAD`; assert exit 0; record new branch SHA. |
| **AC.FBE.6b.2** | All 8 AC.M11a.* sweeps from the M11a-3 sweep report re-run and PASS — **with the FBE.6 regressions all closed** (banned literals + dev-vocabulary scrub now zero across the loam-cli + primary-persona surfaces FBE.8 fixed). | Per-sweep `git grep` against the new `framework-only` SHA: 8 banned literals (AC.M11a.2) → all zero hits; 4 source-side substitution tokens (AC.M11a.3) → all zero hits; per-component production-caller count (AC.M11a.4) → ≥1 callers; 6 memory-system deps × 17 pyprojects (AC.M11a.5) → all zero hits (the FBE.6 graphiti pyproject-comment regression closed by FBE.8 Bucket 3 mcp-pin annotation scrub). |
| **AC.FBE.6b.3** | EXTENDED smoke (dispatcher's exact step list) exercises the full documented install path end-to-end, including `loam init` producing a runnable workspace with `.claude/settings.json`. | Shell sequence per dispatcher brief: `cd /tmp && rm -rf loam-fbe6b-test loam-fbe6b-test-ws && git clone --branch framework-only --single-branch /Users/lukeivers/ivers-corp-pos-v2 loam-fbe6b-test && cd loam-fbe6b-test && python3.13 -m venv .venv && .venv/bin/pip install -r install-from-source.txt && .venv/bin/loam --version && .venv/bin/loam init /tmp/loam-fbe6b-test-ws --from /tmp/loam-fbe6b-test && ls /tmp/loam-fbe6b-test-ws/{framework,workspace,.claude} && ls ~/.loam/`. Every step exits 0; final `loam init` produces a runnable workspace; `.claude/settings.json` exists. |
| **AC.FBE.6b.4** | Push synth to staging (`git push https://github.com/lukeivers/loam-staging.git framework-only:main` per FBE.6 URL-direct precedent). Confirm remote SHA matches local. | `git push` exits 0; `git ls-remote https://github.com/lukeivers/loam-staging.git refs/heads/main` shows new SHA matching the FBE.6b.1 synth SHA. |
| **AC.FBE.6b.5** | Re-dispatch the stranger-perspective reviewer agent (new instance, no prior context) against the new staging tree. Reviewer's verdict = GO or surfaces a NEW BLOCKER not covered by FBE.{1..5,5b,2b,2c,7,8}. | Task-tool dispatch with stranger-perspective + Ruthless Feedback brief mirroring `loam-user-review-2026-05-03.md`; reviewer's report attached to FBE.6b sweep report. |
| **AC.FBE.6b.6** | Sweep report authored at `<workspace>/.scratch/claude-output/v0-1-0-foldback-fbe6b-sweep-report.md`. | File exists post-build; carries per-AC PASS/FAIL table + reviewer verdict + halt-and-surface findings (if any). |
| **AC.FBE.6b.7** | Negative AC: zero source/doc edits during FBE.6b. | `git diff f0f9253..SEAL_COMMIT --name-only` produces only paths under: (a) `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe6b` (NEW narrative file), (b) `docs/rebuild/plans/` (sub-plan + manifest + parent backfill via universal admission), (c) `framework/hands-off-lifecycle/tests/SEAL_COMMIT` (apply step's frozen-baseline-aware sidecar bump). No source or doc edits outside the plans/seals scope. |
| **AC.FBE.6b.S** | Sealed-component fence: hands-off-lifecycle (frozen_baseline: true; HOL no-op narrative anchor pattern). Anchor at `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe6b` per parent plan §4 FBE.6.S clause + FBE.6 + FBE.8 manifest precedent. | The narrative file is created and committed; HOL sidecar bump via `loam amend apply`; seal commit lands cleanly via `loam amend seal` (FBE.8 closed the pre-existing H19 + HC#4 debt that blocked FBE.6's seal). |

---

## 5. Three-lens analysis

### Lens 1 — Claude-leverage-first
Reviewer-agent re-dispatch (AC.FBE.6b.5) is a Claude-native primitive: spawn a fresh-context sub-agent with stranger-perspective brief; let it walk the staging tree. No re-implementation. Lens 1 PASS.

### Lens 2 — Harness + primary-persona value
- **Primary-persona test:** PASS. The verdict measures whether a stranger's primary-persona-equivalent first-run experience works. Reviewer agent IS the stranger-perspective measurement.
- **Harness test:** PASS. FBE.6b doesn't add to the toolkit; it is the gate making the v0.1.0 toolkit publishable. Closes the cycle.

### Lens 3 — ODD authoring
Outcome ACs only (§4); method (which exact venv path, which exact `git grep` invocation, how to format the reviewer brief) is the builder's call but constrained by FBE.6's verification mechanism + the M11a-3 sweep report's contract.

### Lens 4 — Prompt scope ↔ confidence
High confidence in outcome shape: dispatcher named the AC set + the smoke-step list + the negative AC + the seal pattern (mirror FBE.6). Tight scope. The single uncertainty is the reviewer's verdict (GO vs new BLOCKER) — the LOOSEST scope point because the reviewer needs latitude to find things FBE.{1..8} missed. Reviewer's brief uses the original loam-user-review's loose framing so they can think broadly.

### Lens 5 — Swarming
FBE.6b has natural decomposition opportunities (sweeps run in parallel; smoke is sequential; reviewer is a sub-agent). Per FBE.6 actuals (~50–60 min wall-clock; sweeps + smoke + reviewer + report + manifest + apply + seal + status), critical path: synth → sweeps → smoke → push → reviewer → report → seal. Reviewer is one level of decomposition (`max_planner_depth = 1`); other steps run in main thread.

---

## 6. File-by-file map

### Source change
**None.** AC.FBE.6b.7 is a negative AC. FBE.6b is a sweep + smoke + review amendment.

### Plan-doc paper trail (universal-paths admission):
- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe6b.md` — this sub-plan (NEW).
- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe6b.manifest.yaml` — amendment manifest (NEW).
- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` — parent §8 FBE.6b register backfill at completion.

### Narrative seal anchor:
- `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe6b` — narrative anchor file (NEW; sibling to FBE.6's existing `SEAL_COMMIT.v0-1-0-foldback-fbe6`).

### Status file:
- `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe6b-status-2026-05-03.md` — per-AC outcome + SHAs + halt-and-surface (NEW).

### Sweep report:
- `<workspace>/.scratch/claude-output/v0-1-0-foldback-fbe6b-sweep-report.md` — per-AC verification details + reviewer verdict (NEW).

---

## 7. Method (builder's call, recorded for reproducibility)

### 7.1 Re-synth (AC.FBE.6b.1)
- Reuse FBE.6's venv if still present, else build: `python3.13 -m venv /tmp/fbe6b-synth-venv && /tmp/fbe6b-synth-venv/bin/pip install -e /Users/lukeivers/ivers-corp-pos-v2/framework/tools/pos-publish-framework-only`.
- Invoke: `/tmp/fbe6b-synth-venv/bin/pos-publish-framework-only --repo /Users/lukeivers/ivers-corp-pos-v2 --source HEAD`.
- Capture exit code + new `framework-only` branch SHA via `git -C /Users/lukeivers/ivers-corp-pos-v2 rev-parse framework-only`.

### 7.2 Sweeps (AC.FBE.6b.2)
Per-sweep `git grep` against the new `framework-only` SHA — same invocations as FBE.6 §7.2.

**AC.M11a.2 — banned literals (8):** `pos-amend`, `loam-amend`, `loam-mode`, `docs/rebuild/`, `odd-methodology`, `odd-in-loam`, `duration-estimation-rubric`, `pos-publish-framework-only`. For each: `git grep -F -l <literal> framework-only | wc -l` → expect 0.

**AC.M11a.3 — substitution tokens (4):** `/Users/lukeivers/ivers-corp-pos-v2/`, `/Users/lukeivers/ivers-corp-pos-v2`, `lukeivers/pos-v2`, `Luke Ivers`. For each: `git grep -F -l <token> framework-only | wc -l` → expect 0.

**AC.M11a.4 — wired-component sweep:** for each shipping component (15+): `git grep -F -l "import loam.<snake_case>" framework-only -- '*.py' | wc -l` → expect ≥1. Verify zero `tests/` files: `git ls-tree -r --name-only framework-only | grep '/tests/' | wc -l` → expect 0.

**AC.M11a.5 — MFBM dep sweep (6 tokens × N pyprojects):** tokens `graphiti`, `kuzu`, `ollama`, `sentence-transformers`, `fastmcp`, `BGE`. For each pyproject + each token: `grep -ic <token>` → sum 0 across all (FBE.8's mcp-pin annotation scrub closes the FBE.6 graphiti regression).

### 7.3 Extended smoke (AC.FBE.6b.3)
Per dispatcher brief, exact sequence:
```
cd /tmp && rm -rf loam-fbe6b-test loam-fbe6b-test-ws
git clone --branch framework-only --single-branch \
  /Users/lukeivers/ivers-corp-pos-v2 loam-fbe6b-test
cd loam-fbe6b-test
python3.13 -m venv .venv
.venv/bin/pip install -r install-from-source.txt
.venv/bin/loam --version
.venv/bin/loam init /tmp/loam-fbe6b-test-ws --from /tmp/loam-fbe6b-test
ls /tmp/loam-fbe6b-test-ws/{framework,workspace,.claude}
ls ~/.loam/
```
Capture exit codes + stdout + final `ls` of `.claude/` + `~/.loam/` for the sweep report.

### 7.4 Staging push (AC.FBE.6b.4)
- Verify auth: `gh auth status`.
- Push: try `--force-with-lease` first; fall back to `--force` per FBE.6 Surface #5.
- Verify: `git ls-remote https://github.com/lukeivers/loam-staging.git refs/heads/main` shows new SHA.

### 7.5 Reviewer agent re-dispatch (AC.FBE.6b.5)
- Task tool, fresh-context, model = Sonnet (default; no rationale needed per F3).
- Brief mirrors `loam-user-review-2026-05-03.md`:
  - Stranger-perspective: assume no prior knowledge of pos-v2, loam, the foldback.
  - Ruthless Feedback: name disagreement, name evidence, name alternative.
  - Walk-through: clone → install → first-run command → first claude session.
  - Use the staging URL `https://github.com/lukeivers/loam-staging` (post-AC.FBE.6b.4 push).
  - Output: BLOCKER / HIGH / LOW findings + verdict (GO / FOLDBACK).
- Capture reviewer's full report inline in the FBE.6b sweep report.

### 7.6 Sweep report + status file
- Sweep report at `<workspace>/.scratch/claude-output/v0-1-0-foldback-fbe6b-sweep-report.md`: per-AC PASS/FAIL table, sweep details, smoke transcript, reviewer verdict + report excerpt.
- Status file at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe6b-status-2026-05-03.md`: SHAs ladder, per-AC outcomes, halt-and-surface (if any), one-paragraph summary for the dispatcher.

### 7.7 Manifest + apply + seal
- Manifest YAML mirrors FBE.6's HOL no-op narrative anchor (frozen_baseline: true). Sealed-component fence: hands-off-lifecycle only.
- `loam amend apply` — admits the universal-paths plan/seal scope. Expect partner-prefix bug (Surface #4) — admit bare `hands-off-lifecycle` if needed; harmless.
- `loam amend seal` — produces the seal commit attaching the narrative. Expect clean-tree requirement (Surface #4); `git stash push --include-untracked` to unblock then pop post-seal.

### 7.8 Parent plan backfill
- Edit `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` §8 — add new FBE.6b row (after FBE.8 row at lines 654-678), record sub-plan/manifest/seal SHAs.

---

## 8. Out of scope (NOT in FBE.6b)

- Source/doc edits (negative AC.FBE.6b.7) — if reviewer surfaces a new BLOCKER, foldback re-opens; do NOT silently fix in FBE.6b.
- M12 publish-flip — FBE.6b closes (or re-opens) the foldback cycle; M12 is the next dispatch.
- §14 master plan backfill in `oss-v0-1-0-publish.md` — at M12-time per parent plan §5 cycle gate #4.
- Re-edit of FBE.6's existing seal narrative — FBE.6b authors a sibling narrative; FBE.6's narrative stays as the FOLDBACK record.

---

## 9. Halt triggers

Per parent plan §4 FBE.6 halt-triggers + dispatcher additions (reproduced):

1. Reviewer agent surfaces a new BLOCKER → halt; re-open foldback; author FBE.9..N.
2. Extended smoke fails at any step → identify which FBE.x amendment regressed; halt and surface for fix.
3. Synthesis re-run fails → halt; partition manifest is in an invalid state.
4. Staging push fails (auth/remote) → halt; surface remote/auth issue.
5. Reviewer agent observes the install path works but raises a new HIGH-severity finding → surface and triage; HIGH-severity findings may or may not block v0.1.0 GO depending on shape.
6. Build cycle exceeds 90 min wall-clock → halt with partial findings.
7. WD drifts to pos3 → halt immediately.

---

*End of FBE.6b sub-plan-doc. BASELINE `f0f9253`. Next: re-synth → sweeps → smoke → push → reviewer → report → seal → §8 backfill.*
