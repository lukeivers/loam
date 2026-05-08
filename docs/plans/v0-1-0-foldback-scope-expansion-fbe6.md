# FBE.6 sub-plan — re-synth + sweep + extended smoke + reviewer re-run + staging push

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-03.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/plans/v0-1-0-foldback-scope-expansion.md` (FBE.6 row to be backfilled in §8 register; placeholder at lines 614-617 is `<TBD>`).
**Programme master:** `docs/plans/oss-v0-1-0-publish.md`.
**Predecessors:** FBE.{1,2,2b,2c,3,4,5,5b,7} all sealed (`21b9480`, `8d2b770`, `47ccb3a`, `1d6ff13`, `becf183`, `99c03a6`, `bc56f0d`, `48bb7e2`, `a102bde`).
**BASELINE (pre-build tip):** `48bb7e2` — current canonical pos-v2 HEAD (the FBE.5b seal commit).

---

## 1. Summary / TLDR

FBE.6 is the close-the-cycle step for the v0.1.0 publish foldback. All source-side fixes from FBE.{1,2,2b,2c,3,4,5,5b,7} are now sealed at canonical HEAD `48bb7e2`. FBE.6 re-synthesises the `framework-only` branch from canonical HEAD, re-runs the M11a-3 sweep AC checks (no-regression verification), runs an EXTENDED smoke that exercises the documented install path end-to-end (post-FBE.2c clone-flow shape: no `framework/` arg in `git clone`), pushes the synth to staging (`lukeivers/loam-staging`), and re-dispatches the stranger-perspective reviewer agent. Reviewer's verdict either GOes (foldback closes; M12 publish-flip is the next dispatch) or surfaces a new BLOCKER (foldback re-opens; halt + surface to dispatcher).

**Negative AC:** zero source/doc edits during FBE.6. If the reviewer surfaces a new BLOCKER, do NOT silently fix in FBE.6 — surface to dispatcher.

**Sealed-component fence:** NONE (narrative seal only at `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe6`; mirrors M11a precedent and the parent plan §4 FBE.6.S clause).

**Note on §8 register backfill:** the parent foldback plan-doc names FBE.6 explicitly at §8 line 614-617 with placeholder SHAs (`<TBD>`). Full §8 register entry will be backfilled at completion via the universal-paths admission (post-seal commit, mirroring FBE.2b/FBE.2c/FBE.5b precedent).

---

## 2. Halt-and-surface BEFORE build

### Surface #1 (no halt — recorded; smoke updated for post-FBE.2c clone flow)

The parent plan §4 FBE.6.3 step-list still carries the pre-FBE.2c clone shape (`git clone --branch framework-only --single-branch /Users/lukeivers/ivers-corp-pos-v2 loam-fbe6-test/framework`). FBE.2c shipped (sealed `1d6ff13`) and dropped the `framework/` arg from the documented install flow per Decision D's Path α — README + getting-started.md now show `git clone <repo>` → `cd <name>`. The dispatcher's brief explicitly names the corrected clone shape (no `framework/` arg; result lands at `loam-fbe6-test/framework/...` because the synth tree carries `framework/` prefix per FBE.2b). Smoke per the dispatcher's brief is the source of truth; parent plan §4 FBE.6.3 is stale and will be updated post-seal.

### Surface #2 (no halt — recorded; install-from-source.txt is the install entry point post-FBE.4)

FBE.4 ratified bare-name inter-component deps in pyprojects + introduced `install-from-source.txt` at the canonical root carrying ordered `-e ./<path>` lines. The smoke MUST use `pip install -r install-from-source.txt` (single-line install of all 17 components in the right order), not piecewise `pip install -e <component>` repeats. The dispatcher's brief names this explicitly. Verification: `git ls-tree framework-only` should carry `install-from-source.txt` at root (per FBE.4's `dev_and_public` admission `cfc9ed4`).

### Surface #3 (no halt — recorded; reviewer agent dispatch is the new-instance pattern)

The reviewer agent (AC.FBE.6.5) is dispatched via Task tool with a fresh-context prompt. The brief mirrors the original `loam-user-review-2026-05-03.md` framing: stranger-perspective + Ruthless Feedback principle + walk-through-the-install-path. The reviewer reads the staging tree (or the local synth tree if staging push is delayed). The reviewer's verdict — GO or NEW BLOCKER — is the close-or-reopen signal for the foldback.

### Surface #4 (no halt — recorded; staging remote not currently configured)

`git remote -v` shows only `origin → https://github.com/lukeivers/ivers-corp.git`; no `staging` remote. The M11a-3 dispatch pushed to `lukeivers/loam-staging` via direct URL (`git push https://github.com/lukeivers/loam-staging.git framework-only:main`). FBE.6 follows the same pattern (URL-direct push); no remote config required. If the push fails on auth → halt-and-surface per parent plan §4 FBE.6 halt trigger #4.

### Surface #5 (no halt — recorded; cycle gate at AC.FBE.6.5)

The reviewer's verdict is the gate. If GO, AC.FBE.6.* all close, sweep report records GO, status file authored, FBE.6 seals via narrative anchor. If reviewer surfaces a NEW BLOCKER not covered by FBE.{1..5,5b,2b,2c,7}, halt + surface to dispatcher (do NOT silently fix; foldback re-opens). HIGH-severity findings (per parent plan §4 FBE.6 halt trigger #5) get triaged: may or may not block v0.1.0 GO depending on shape.

---

## 3. Spec-objective placement

**Binds to:**
- **AC.PO.1 + AC.PO.2** (prime objective per `docs/VALUE_PROPOSITION.md`) — closing the v0.1.0 foldback cycle so the publish-flip can happen.
- **Parent plan §5 cycle gate #2** ("FBE.6 closes GO — sweep PASS, extended smoke PASS, reviewer agent verdict GO (or non-blocking HIGH only)").
- **AC.FBE.6.* (parent plan §4 FBE.6)** — every AC ladders to the same parent.

**Ladders to:** AC.FBE.6.* → M12 publish-flip → AC.PO.1 + AC.PO.2.

---

## 4. Acceptance criteria (FBE.6.*)

AC family `AC.FBE.6.*` — defined in parent plan §4 FBE.6; reproduced here with verification mechanism for each.

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.FBE.6.1** | `pos-publish-framework-only` re-runs from canonical HEAD `48bb7e2`; produces a fresh `framework-only` branch SHA. Synth exit code 0. | Build a venv with `pos-publish-framework-only` editable-installed; run `pos-publish-framework-only --repo /Users/lukeivers/ivers-corp-pos-v2 --source HEAD`; assert exit 0; record new branch SHA. |
| **AC.FBE.6.2** | All 8 AC.M11a.* sweeps from the M11a-3 sweep report re-run and PASS (no regression). | Per-sweep `git grep` invocations against the new `framework-only` SHA: 8 banned literals (AC.M11a.2), 4 source-side substitution tokens (AC.M11a.3), per-component production-caller count (AC.M11a.4), 6 memory-system deps × 14 pyprojects (AC.M11a.5). All counts match M11a-3 baseline (zero hits where expected; ≥1 caller where expected). |
| **AC.FBE.6.3** | EXTENDED smoke (post-FBE.2c clone flow) exercises the full documented install path end-to-end. | Shell sequence per dispatcher brief: `cd /tmp && rm -rf loam-fbe6-test loam-fbe6-test-ws && git clone --branch framework-only --single-branch /Users/lukeivers/ivers-corp-pos-v2 loam-fbe6-test && cd loam-fbe6-test && python3.13 -m venv .venv && .venv/bin/pip install -r install-from-source.txt && .venv/bin/loam --version && .venv/bin/loam init /tmp/loam-fbe6-test-ws --from /tmp/loam-fbe6-test && ls /tmp/loam-fbe6-test-ws/{framework,workspace,.claude} && ls ~/.loam/`. Every step exits 0; final `loam init` produces a runnable workspace; `.claude/settings.json` exists. |
| **AC.FBE.6.4** | Push synth to staging (`git push https://github.com/lukeivers/loam-staging.git framework-only:main` — URL-direct per M11a-3 precedent). Confirm remote SHA matches local. | `git push` exits 0; `git ls-remote https://github.com/lukeivers/loam-staging.git refs/heads/main` shows new SHA matching the FBE.6.1 synth SHA. |
| **AC.FBE.6.5** | Re-dispatch the stranger-perspective reviewer agent (new instance, no prior context) against the new staging tree. Reviewer's verdict = GO or surfaces a NEW BLOCKER not covered by FBE.{1..5,5b,2b,2c,7}. | Task-tool dispatch with stranger-perspective + Ruthless Feedback brief mirroring `loam-user-review-2026-05-03.md`; reviewer's report attached to FBE.6 sweep report. |
| **AC.FBE.6.6** | Sweep report authored at `<workspace>/.scratch/claude-output/v0-1-0-foldback-fbe6-sweep-report.md`. | File exists post-build; carries per-AC PASS/FAIL table + reviewer verdict + halt-and-surface findings (if any). |
| **AC.FBE.6.7** | Negative AC: zero source/doc edits during FBE.6. | `git diff 48bb7e2..SEAL_COMMIT --name-only` produces only paths under: (a) `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe6` (NEW narrative file), (b) `docs/plans/` (sub-plan + manifest + parent backfill via universal admission). No source or doc edits outside the plans/seals scope. |
| **AC.FBE.6.S** | Sealed-component fence: NONE — narrative seal only. Anchor at `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe6` per parent plan §4 FBE.6.S clause and M11a precedent (e.g. `SEAL_COMMIT.oss-v0-1-0-publish-scrub`). | The narrative file is created and committed; no sealed-component sidecar updates required (no source-side delta means no fence to enforce). |

---

## 5. Three-lens analysis

### Lens 1 — Claude-leverage-first
The reviewer-agent re-dispatch (AC.FBE.6.5) is itself a Claude-native primitive: spawn a fresh-context sub-agent, give it a stranger-perspective brief, let it walk the staging tree. No Claude capability re-implementation; the close-the-cycle step composes on existing sub-agent dispatch. Lens 1 PASS.

### Lens 2 — Harness + primary-persona value
- **Primary-persona test:** PASS. The verdict is whether a stranger's primary-persona-equivalent first-run experience works end-to-end. Reviewer agent IS the stranger-perspective measurement.
- **Harness test:** PASS. FBE.6 doesn't add to the toolkit, but it is the gate that makes the v0.1.0 toolkit publishable. Closes the cycle that turned the toolkit into a publishable artefact.

### Lens 3 — ODD authoring
Outcome ACs only (§4); method (which exact venv path, which exact `git grep` invocation for each banned literal, how to format the reviewer brief) is the builder's call but constrained by the M11a-3 sweep report's verification mechanism.

### Lens 4 — Prompt scope ↔ confidence
High confidence in outcome shape: dispatcher named the AC set + the smoke-step list + the negative AC. Tight scope. The single uncertainty is the reviewer's verdict (GO vs new BLOCKER) — which is the LOOSEST scope point because the reviewer needs latitude to find things FBE.1..5 missed. The reviewer's brief uses the original loam-user-review's loose framing so they can think broadly.

### Lens 5 — Swarming
FBE.6 has natural decomposition opportunities (sweeps run in parallel; smoke is sequential; reviewer is a sub-agent). Per parent plan §4 FBE.6 AI-time band (60–120 min), the natural critical path is: synth → sweeps → smoke → push → reviewer → report → seal. The reviewer step is the only one requiring sub-agent dispatch (AC.FBE.6.5); other steps run in the build agent's main thread. `max_planner_depth = 1` — reviewer is one level of decomposition; no sub-sub-planners.

---

## 6. File-by-file map

### Source change
**None.** AC.FBE.6.7 is a negative AC. FBE.6 is a sweep + smoke + review amendment.

### Plan-doc paper trail (universal-paths admission):
- `docs/plans/v0-1-0-foldback-scope-expansion-fbe6.md` — this sub-plan (NEW).
- `docs/plans/v0-1-0-foldback-scope-expansion-fbe6.manifest.yaml` — amendment manifest (NEW).
- `docs/plans/v0-1-0-foldback-scope-expansion.md` — parent §8 FBE.6 register backfill at completion.

### Narrative seal anchor:
- `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe6` — narrative anchor file (NEW). Format mirrors `SEAL_COMMIT.oss-v0-1-0-publish-scrub` and existing HOL seal narratives.

### Status file:
- `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe6-status-2026-05-03.md` — per-AC outcome + SHAs + halt-and-surface (NEW).

### Sweep report:
- `<workspace>/.scratch/claude-output/v0-1-0-foldback-fbe6-sweep-report.md` — per-AC verification details + reviewer verdict (NEW).

---

## 7. Method (builder's call, recorded for reproducibility)

### 7.1 Re-synth (AC.FBE.6.1)
- Build venv: `python3.13 -m venv /tmp/fbe6-synth-venv && /tmp/fbe6-synth-venv/bin/pip install -e /Users/lukeivers/ivers-corp-pos-v2/framework/tools/pos-publish-framework-only`.
- Invoke: `/tmp/fbe6-synth-venv/bin/pos-publish-framework-only --repo /Users/lukeivers/ivers-corp-pos-v2 --source HEAD`.
- Capture exit code + new `framework-only` branch SHA via `git -C /Users/lukeivers/ivers-corp-pos-v2 rev-parse framework-only`.

### 7.2 Sweeps (AC.FBE.6.2)
Per-sweep `git grep` invocations against `framework-only`:

**AC.M11a.2 — banned literals (8 total):**
- `pos-amend`, `loam-amend`, `loam-mode`, `docs/rebuild/`, `odd-methodology`, `odd-in-loam`, `duration-estimation-rubric`, `pos-publish-framework-only`
- For each: `git -C /Users/lukeivers/ivers-corp-pos-v2 grep -F -l <literal> framework-only | wc -l` → expect 0.

**AC.M11a.3 — source-side substitution tokens (4 total):**
- `/Users/lukeivers/ivers-corp-pos-v2/`, `/Users/lukeivers/ivers-corp-pos-v2`, `lukeivers/pos-v2`, `Luke Ivers`
- For each: `git grep -F -l <token> framework-only | wc -l` → expect 0.

**AC.M11a.4 — wired-component sweep:**
- For each shipping component (15 in M11a-3 baseline): `git grep -F -l "import loam.<snake_case>" framework-only -- '*.py' | wc -l` → expect ≥1.
- Verify zero `tests/` files in synth: `git ls-tree -r --name-only framework-only | grep '/tests/' | wc -l` → expect 0.

**AC.M11a.5 — MFBM dep sweep (6 tokens × 14 pyprojects):**
- Tokens: `graphiti`, `kuzu`, `ollama`, `sentence-transformers`, `fastmcp`, `BGE`.
- For each pyproject + each token: `grep -ic <token>` → sum 0 across all.

### 7.3 Extended smoke (AC.FBE.6.3)
Per dispatcher brief, exact sequence:
```
cd /tmp && rm -rf loam-fbe6-test loam-fbe6-test-ws
git clone --branch framework-only --single-branch \
  /Users/lukeivers/ivers-corp-pos-v2 loam-fbe6-test
cd loam-fbe6-test
python3.13 -m venv .venv
.venv/bin/pip install -r install-from-source.txt
.venv/bin/loam --version
.venv/bin/loam init /tmp/loam-fbe6-test-ws --from /tmp/loam-fbe6-test
ls /tmp/loam-fbe6-test-ws/{framework,workspace,.claude}
ls ~/.loam/
```
Capture exit code + stdout + final `ls` of `.claude/` + `~/.loam/` for the sweep report.

### 7.4 Staging push (AC.FBE.6.4)
- Verify auth: `gh auth status` (already authenticated per M11a-3 record).
- Push: `git -C /Users/lukeivers/ivers-corp-pos-v2 push https://github.com/lukeivers/loam-staging.git framework-only:main --force-with-lease` (force-with-lease because staging carries M11a-3's `c4f24bf` tip; FBE.6 advances).
- Verify: `git ls-remote https://github.com/lukeivers/loam-staging.git refs/heads/main` shows new SHA.

### 7.5 Reviewer agent re-dispatch (AC.FBE.6.5)
- Task tool, fresh-context, model = Sonnet (default; no rationale needed per F3).
- Brief mirrors `loam-user-review-2026-05-03.md`:
  - Stranger-perspective: assume no prior knowledge of pos-v2, loam, the foldback.
  - Ruthless Feedback: name disagreement, name evidence, name alternative.
  - Walk-through: clone → install → first-run command → first claude session.
  - Use the staging URL `https://github.com/lukeivers/loam-staging` if push succeeded; fall back to local `framework-only` branch otherwise.
  - Output: BLOCKER / HIGH / LOW findings + verdict (GO / FOLDBACK).
- Capture reviewer's full report inline in the FBE.6 sweep report.

### 7.6 Sweep report + status file
- Sweep report at `<workspace>/.scratch/claude-output/v0-1-0-foldback-fbe6-sweep-report.md`: per-AC PASS/FAIL table, sweep details, smoke transcript, reviewer verdict + report excerpt.
- Status file at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe6-status-2026-05-03.md`: SHAs ladder, per-AC outcomes, halt-and-surface (if any), one-paragraph summary for the dispatcher.

### 7.7 Manifest + apply + seal
- Manifest YAML mirrors prior FBE narrative-only seals (FBE.6 = narrative only, NO sealed-component fence). Reference: this is the M11a/scrub-narrative pattern (no `components:` array per fence; just narrative target = HOL seal narrative file).
- `loam amend apply` — for narrative-only amendments, the apply tool may report "no fence components to admit" or similar; that's the correct shape. The narrative anchor at `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe6` is the seal artefact.
- `loam amend seal` — produces the seal commit attaching the narrative.
- Be alert for partner-prefix bug (precedent: hand-corrective if it recurs).

### 7.8 Parent plan backfill
- Edit `docs/plans/v0-1-0-foldback-scope-expansion.md` §8 FBE.6 register (lines 614-617): replace `<TBD>` with concrete SHAs (sub-plan, manifest, narrative file commit, seal commit).
- Update closing paragraph to reflect FBE.6 seal SHA.

---

## 8. Out of scope (NOT in FBE.6)

- Source/doc edits (negative AC.FBE.6.7) — if the reviewer surfaces a new BLOCKER, foldback re-opens; do NOT silently fix in FBE.6.
- M12 publish-flip — FBE.6 closes the foldback cycle; M12 is the next dispatch (separate amendment).
- §14 master plan backfill in `oss-v0-1-0-publish.md` — happens at M12-time per parent plan §5 cycle gate #4.
- Linux-fidelity smoke (per parent plan Risk 5) — FBE.6's smoke runs on macOS; Linux container smoke deferred to v0.1.x.

---

## 9. Halt triggers

Per parent plan §4 FBE.6 halt-triggers (reproduced):

1. Reviewer agent surfaces a new BLOCKER → halt; re-open foldback; author FBE.8..N.
2. Extended smoke fails at any step → identify which FBE.x amendment regressed; halt and surface for fix.
3. Synthesis re-run fails → halt; partition manifest is in an invalid state.
4. Staging push fails (auth/remote) → halt; surface remote/auth issue.
5. Reviewer agent observes the install path works but raises a new HIGH-severity finding → surface and triage; HIGH-severity findings may or may not block v0.1.0 GO depending on shape.
6. Build cycle exceeds 90 min wall-clock → halt with partial findings.

Plus dispatcher-added trigger:

7. WD drifts to pos3 → halt immediately.

---

*End of FBE.6 sub-plan-doc. BASELINE `48bb7e2`. Next: re-synth → sweeps → smoke → push → reviewer → report → seal → §8 backfill.*
