# FBE.11 sub-plan — close BLOCKER-FBE6c.1 (publish-side dual-ref push)

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-03.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/plans/v0-1-0-foldback-scope-expansion.md` (FBE.11 row to be backfilled in §8 register at completion; FBE.6c row at lines 820-855 is the FOLDBACK record that named BLOCKER-FBE6c.1).
**Programme master:** `docs/plans/oss-v0-1-0-publish.md`.
**Predecessors:** FBE.{1,2,2b,2c,3,4,5,5b,7,8,6b,9,10,6c} all sealed (`21b9480`, `8d2b770`, `47ccb3a`, `1d6ff13`, `becf183`, `99c03a6`, `bc56f0d`, `48bb7e2`, `a102bde`, `cc66b08`, `08589ce`, `308d7b4`, `428deeb`, `6fd3812`); FBE.6 apply at `364c37d` (apply-only; seal intentionally pending — FBE.6 stays the FOLDBACK record).
**BASELINE (pre-build tip):** `03ef8da` — current canonical pos-v2 HEAD (the FBE.6c §8 register backfill commit).

---

## 1. Summary / TLDR

FBE.11 closes **BLOCKER-FBE6c.1** by changing the documented operator push command from a single-ref push (`framework-only:main`) to a **dual-ref push** (`framework-only:main` + `framework-only:framework-only`). Path B per dispatcher's locked path: preserve `main` as the friendly browse default, AND also publish a `framework-only` ref so stranger clones get `origin/framework-only` and the bootstrap's `_clone_canonical` step succeeds.

The publish path is **manual operator commands documented in plan-docs** — there is no push-driving script in `framework/tools/pos-publish-framework-only/` (that tool only synthesises the local `framework-only` branch; the push-to-staging / push-to-public step is operator-typed per the documented push command in the M11 dry-run plan). Therefore FBE.11 is a doc-only amendment that updates the documented push command at the live operator-instruction surfaces:

1. `docs/plans/oss-v0-1-0-publish-dry-run.md` AC.M11a.7 (the canonical operator instruction for the staging push).
2. `docs/plans/v0-1-0-foldback-scope-expansion.md` §4 AC.FBE.6.4 row (the forward-AC text that future FBE.6d will follow).

Sealed-amendment FBE.6/FBE.6b/FBE.6c sub-plans are historical records of past dispatches — they are **not** retroactively edited (the dispatches happened with the old push command; their narratives stay accurate to the as-dispatched step). FBE.6d will use the new dual-ref push per the (updated) AC.FBE.6.4 text.

The fix verifies via a **local-tmp-ref push smoke**: push to a fresh local bare repo (or `/tmp/loam-staging-fbe11-smoke.git`) with the dual-ref command, then `git ls-remote` confirms BOTH `refs/heads/main` AND `refs/heads/framework-only` land at the same SHA. A subsequent `git clone` of the local bare confirms the stranger then has `origin/framework-only` available.

**Negative AC:** zero edits to source under `framework/<comp>/src/` or `framework/<comp>/tests/`. FBE.11 is doc-only at the operator-instruction surfaces.

**Sealed-component fence:** hands-off-lifecycle only (HOL no-op narrative anchor pattern; `frozen_baseline: true` per amendment #23 + FBE.6/FBE.6b/FBE.6c manifest precedent). Narrative seal at `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe11` (sibling to FBE.6/FBE.6b/FBE.6c narratives).

**No premature push to actual staging or public** — that's M12's job. FBE.11 just lands the FIX in canonical and verifies via local-tmp-ref smoke.

---

## 2. Halt-and-surface BEFORE build

### Surface #1 (no halt — recorded; publish path is operator-manual)

The dispatcher noted "Find the publish/push code (likely in `framework/tools/pos-publish-framework-only/` or one of its scripts; the M12 publish-flip path likely lives in `docs/plans/oss-v0-1-0-publish.md` M12 row + may invoke a script)." Verified at sub-plan time: the synth tool at `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/` (`cli.py`, `synth.py`, `partition.py`, `substitution.py`, `__init__.py`) advances the local `framework-only` ref only — `git grep -n "push\|remote\|loam-staging" framework/tools/pos-publish-framework-only/src/` returns zero hits. The push command is operator-manual, documented in `oss-v0-1-0-publish-dry-run.md` AC.M11a.7 + line 32 + line 430 (D-build.M11a.10 dispatch-3 mechanism note) + line 174 (gh repo create). Per dispatcher's brief: "If the publish path is a manual operator command (no script), update the operator doc to instruct the dual-ref push." That's what FBE.11 does.

### Surface #2 (no halt — recorded; sealed-amendment plan-docs not retroactively edited)

The FBE.6/FBE.6b/FBE.6c sub-plan-docs (`v0-1-0-foldback-scope-expansion-fbe6.md`, `-fbe6b.md`, `-fbe6c.md`) all carry the old `framework-only:main` single-ref push in their AC tables (AC.FBE.6.4 / AC.FBE.6b.4 / AC.FBE.6c.4). These are **sealed-amendment historical records** — they describe the dispatch as it actually happened. Editing them retroactively would be revisionist and breaks the audit trail. FBE.11 leaves them untouched. FBE.6d's sub-plan-doc (when authored post-FBE.11 seal) will use the new dual-ref push command per the updated parent plan §4 AC.FBE.6.4 + the updated M11 dry-run plan AC.M11a.7.

### Surface #3 (no halt — recorded; smoke is local-only)

The dispatch explicitly forbids premature push to actual staging or public ("that's M12's job. FBE.11 just lands the FIX in canonical"). The smoke uses a local bare repo at `/tmp/loam-staging-fbe11-smoke.git` (deleted post-smoke). This proves the dual-ref push command syntax works AND that a stranger cloning the resulting remote sees BOTH refs. No GitHub state written.

### Surface #4 (no halt — recorded; HOL no-op narrative anchor pattern recurs)

Per FBE.6/FBE.6b/FBE.8/FBE.9/FBE.10/FBE.6c precedent, doc-only amendments use the HOL narrative anchor pattern: the structural surface IS the seal narrative file at `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe11`; HOL `frozen_baseline: true`; sealed-component fence is HOL only.

### Surface #5 (no halt — anticipated `loam amend` ergonomic recurrences)

Per FBE.{6b,9,10,6c} precedent: (a) `loam amend apply` may not auto-commit (4 consecutive recurrences in FBE.6b/FBE.9/FBE.10/FBE.6c — pattern STRONG) — manually commit if needed via `chore(amend): FBE.11 apply`; (b) `loam amend seal` requires clean working tree — pre-existing untracked + dirty paths in canonical require `git stash push --include-untracked` to unblock then `git stash pop` post-seal. FBE.11 expects both to recur and applies the same workarounds.

---

## 3. Spec-objective placement

**Binds to:**
- **AC.PO.1 + AC.PO.2** (prime objective per `docs/VALUE_PROPOSITION.md`) — closing the v0.1.0 foldback cycle so the publish-flip can happen.
- **Parent plan §4 AC.FBE.6.4** (the canonical push-command AC) — FBE.11 updates this row's text to the dual-ref push.
- **Parent plan §5 cycle gate #3** ("Reviewer's verdict surfaces a NEW BLOCKER → halt + surface; foldback re-opens") — FBE.11 closes the cycle FBE.6c re-opened via halt-trigger.
- **AC.FBE.11.* (this sub-plan)** — the new ACs for FBE.11.

**Ladders to:** AC.FBE.11.* → FBE.6d (re-verification) → M12 publish-flip → AC.PO.1 + AC.PO.2.

---

## 4. Acceptance criteria (FBE.11.*)

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.FBE.11.1** | `docs/plans/oss-v0-1-0-publish-dry-run.md` AC.M11a.7 (lines 170-178) updated to instruct the dual-ref push: `git push <staging-url> framework-only:main framework-only:framework-only --force`. Verification text updated to assert BOTH refs land at the same SHA. | `grep -n "framework-only:framework-only" docs/plans/oss-v0-1-0-publish-dry-run.md` returns ≥1 hit; the AC.M11a.7 §body names both refs in the push command + verifies both via `git ls-remote`. |
| **AC.FBE.11.2** | `docs/plans/oss-v0-1-0-publish-dry-run.md` line 32 (M11a summary) + line 430 (D-build.M11a.10 mechanism note) updated to dual-ref push. | `git grep -n "framework-only:framework-only" docs/plans/oss-v0-1-0-publish-dry-run.md` shows the summary + mechanism-note lines among the hits. |
| **AC.FBE.11.3** | `docs/plans/v0-1-0-foldback-scope-expansion.md` §4 AC.FBE.6.4 row (line 366) updated to the dual-ref push command, so future FBE.6d (which mirrors AC.FBE.6.4 verbatim per FBE.6/FBE.6b/FBE.6c precedent) inherits the fix. | `grep -n "framework-only:framework-only" docs/plans/v0-1-0-foldback-scope-expansion.md` returns ≥1 hit at line 366 (AC.FBE.6.4 row). |
| **AC.FBE.11.4** | Local-tmp-ref smoke: dual-ref push to `/tmp/loam-staging-fbe11-smoke.git` (fresh local bare) with the new push command lands BOTH `refs/heads/main` AND `refs/heads/framework-only` at the same SHA. A subsequent `git clone /tmp/loam-staging-fbe11-smoke.git /tmp/loam-stranger-fbe11/` produces a clone with `refs/remotes/origin/framework-only` available. | Shell sequence: create bare repo → push framework-only:main framework-only:framework-only → ls-remote shows both refs at canonical's framework-only SHA → clone bare into stranger path → `git -C /tmp/loam-stranger-fbe11 for-each-ref` shows `refs/remotes/origin/framework-only`. |
| **AC.FBE.11.5** | Status file authored at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe11-status-2026-05-03.md` with per-AC pass/fail + SHAs ladder + halt-and-surface findings (if any). | File exists post-build; carries per-AC PASS/FAIL table + smoke transcript + commit ladder + one-paragraph close summary for the dispatcher. |
| **AC.FBE.11.6** | Negative AC: zero edits to source under `framework/<comp>/src/` or `framework/<comp>/tests/`. | `git diff 03ef8da..SEAL_COMMIT --name-only` produces only paths under: (a) `docs/plans/` (sub-plan + manifest + parent §8 backfill + AC.FBE.6.4 row update + dry-run plan-doc updates), (b) `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe11` (NEW narrative file), (c) `framework/hands-off-lifecycle/tests/SEAL_COMMIT` (apply step's frozen-baseline-aware sidecar bump). No edits under `framework/<comp>/src/` or `framework/<comp>/tests/`. |
| **AC.FBE.11.S** | Sealed-component fence: hands-off-lifecycle (frozen_baseline: true; HOL no-op narrative anchor pattern). Anchor at `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe11` per FBE.6/FBE.6b/FBE.8/FBE.9/FBE.10/FBE.6c manifest precedent. | The narrative file is created and committed; HOL sidecar bump via `loam amend apply`; seal commit lands cleanly via `loam amend seal`. |

---

## 5. Three-lens analysis

### Lens 1 — Claude-leverage-first
N/A for this amendment shape (operator-instruction doc-only). The publish step itself is operator-typed; no Claude-native primitive in scope.

### Lens 2 — Harness + primary-persona value
- **Primary-persona test:** PASS. Closes BLOCKER-FBE6c.1 — the README's literal `git clone https://github.com/lukeivers/loam` flow currently fails at `loam init`; FBE.11's fix means the documented (M12-equivalent) push path will produce a remote where stranger clones get the `origin/framework-only` ref the bootstrap requires.
- **Harness test:** PASS. The harness's external-publish surface (the documented operator push command) becomes correct; it adds robustness to the toolkit's bootstrap-from-published-default-branch path.

### Lens 3 — ODD authoring
Outcome ACs only (§4); method (which exact tmp path, which exact `git ls-remote` verification format) is the builder's call but constrained by the AC verification mechanisms.

### Lens 4 — Prompt scope ↔ confidence
**Tight scope, high confidence.** Dispatcher named: Path B (dual-ref), the exact push command shape (`framework-only:main` + `framework-only:framework-only`), the smoke approach (local-tmp-ref push, no GitHub state), the sealed-component fence (likely HOL-only), the negative AC (no source-side edits). The single open uncertainty is which exact files carry the operator instruction (resolved at sub-plan time: `oss-v0-1-0-publish-dry-run.md` + parent plan §4 AC.FBE.6.4). Tight scope is appropriate.

### Lens 5 — Swarming
FBE.11 is a single-shot doc edit + smoke + seal. No decomposition opportunity tighter than the parent's AC set. Stopping criterion satisfied at this granularity. Model = Sonnet (default; no rationale needed per F3).

---

## 6. File-by-file map

### Doc edits (operator-instruction surfaces — universal-paths admission):
- `docs/plans/oss-v0-1-0-publish-dry-run.md` — update AC.M11a.7 §body (lines ~170-178), summary (line 32), D-build.M11a.10 mechanism note (line 430) for dual-ref push. **Doc-only edit; no source delta.**
- `docs/plans/v0-1-0-foldback-scope-expansion.md` — update §4 AC.FBE.6.4 row (line 366) for dual-ref push command (the forward-AC text future FBE.6d inherits). **Doc-only edit; no source delta.**

### Plan-doc paper trail (universal-paths admission):
- `docs/plans/v0-1-0-foldback-scope-expansion-fbe11.md` — this sub-plan (NEW).
- `docs/plans/v0-1-0-foldback-scope-expansion-fbe11.manifest.yaml` — amendment manifest (NEW).
- `docs/plans/v0-1-0-foldback-scope-expansion.md` §8 FBE.11 register backfill at completion.

### Narrative seal anchor:
- `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe11` — narrative anchor file (NEW; sibling to FBE.6/FBE.6b/FBE.8/FBE.9/FBE.10/FBE.6c narratives).

### Status file:
- `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe11-status-2026-05-03.md` — per-AC outcome + SHAs + halt-and-surface (NEW).

### NOT TOUCHED (negative AC.FBE.11.6):
- `framework/<comp>/src/**` — zero edits.
- `framework/<comp>/tests/**` — zero edits (apart from the HOL sidecar bump driven by `loam amend apply`, which is the standard seal-cycle mechanic, not a test edit).
- `docs/plans/v0-1-0-foldback-scope-expansion-fbe6.md` / `-fbe6b.md` / `-fbe6c.md` — sealed-amendment historical records, not retroactively edited.

---

## 7. Method (builder's call, recorded for reproducibility)

### 7.1 Doc edits (AC.FBE.11.1, AC.FBE.11.2, AC.FBE.11.3)

**`oss-v0-1-0-publish-dry-run.md` AC.M11a.7 (lines 170-178):**

Update the §body to instruct the dual-ref push. Replace the single-ref push with the dual-ref form. Update the verification §body to assert BOTH refs land at the same SHA via `git ls-remote`. Add a note explaining the dual-ref rationale (browse-friendly `main` + bootstrap-required `framework-only`).

**`oss-v0-1-0-publish-dry-run.md` line 32 (M11a summary):**

Update "push to private `lukeivers/loam-staging:main`" → "push BOTH `framework-only:main` AND `framework-only:framework-only` to private `lukeivers/loam-staging`".

**`oss-v0-1-0-publish-dry-run.md` line 430 (D-build.M11a.10 dispatch-3 mechanism note):**

Update the historical record's reference to the now-corrected mechanism. Add a parenthetical: "(superseded post-FBE.11: dual-ref push to `framework-only:main framework-only:framework-only`; see updated AC.M11a.7)". This preserves the as-dispatched record while annotating the supersede.

**`v0-1-0-foldback-scope-expansion.md` §4 AC.FBE.6.4 row (line 366):**

Update from `git push staging framework-only:main` to `git push <staging-url> framework-only:main framework-only:framework-only`. Update the verification language to name BOTH refs.

### 7.2 Smoke (AC.FBE.11.4)

Local bare repo + dual-ref push + clone:

```
TMP=/tmp/loam-staging-fbe11-smoke.git
STRANGER=/tmp/loam-stranger-fbe11
rm -rf "$TMP" "$STRANGER"

# Set up a bare repo to act as the staging remote
git init --bare "$TMP"

# Push BOTH refs from canonical pos-v2's framework-only branch
git -C /Users/lukeivers/ivers-corp-pos-v2 push "$TMP" \
  framework-only:main framework-only:framework-only --force

# Verify both refs land
git ls-remote "$TMP"
# Expect: <SHA> refs/heads/framework-only
#         <SHA> refs/heads/main
# (same SHA on both)

# Clone the bare; verify stranger sees both
git clone "$TMP" "$STRANGER"
git -C "$STRANGER" for-each-ref --format='%(refname) %(objectname:short)'
# Expect:
#   refs/heads/main <SHA>
#   refs/remotes/origin/HEAD <SHA>
#   refs/remotes/origin/framework-only <SHA>
#   refs/remotes/origin/main <SHA>
```

The presence of `refs/remotes/origin/framework-only` in the stranger clone is the dispositive proof — it's what the bootstrap's `_clone_canonical` step needs.

Capture exit codes + outputs into the status file. Clean up tmp dirs post-smoke.

### 7.3 Manifest + apply + seal

- Manifest YAML mirrors FBE.6c's HOL no-op narrative anchor (`frozen_baseline: true`). Sealed-component fence: hands-off-lifecycle only.
- `loam amend apply` — admits the universal-paths plan/seal/dry-run scope.
  - `docs/plans/oss-v0-1-0-publish-dry-run.md` and `docs/plans/v0-1-0-foldback-scope-expansion.md` both ride the `docs/plans/` universal-paths prefix admission.
  - Be alert for the no-auto-commit pattern (4 consecutive recurrences); manually commit if needed via `chore(amend): FBE.11 apply ...`.
- `loam amend seal` — produces the seal commit attaching the narrative. Expect clean-tree requirement (Surface #5); `git stash push --include-untracked` to unblock then pop post-seal.

### 7.4 Touched-only test scope

Per `feedback_amendment_dispatch_speedups`: skip full repo-wide pytest pre-seal. Touched-component pytest = HOL only (the sole component in the fence; doc-only amendment otherwise). The seal command's built-in HOL touched-test pass is sufficient verification.

### 7.5 Status file + parent plan backfill

- Status file at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe11-status-2026-05-03.md`: SHAs ladder, per-AC outcomes, smoke transcript, one-paragraph summary for the dispatcher.
- Parent plan §8 backfill: edit `docs/plans/v0-1-0-foldback-scope-expansion.md` §8 — add new FBE.11 row (after FBE.6c row at lines 820-855), record sub-plan/manifest/seal SHAs.

---

## 8. Out of scope (NOT in FBE.11)

- Source/test edits under `framework/<comp>/` (negative AC.FBE.11.6) — the fix is doc-only at the operator-instruction surface.
- Push to actual staging or public (`lukeivers/loam-staging` or `lukeivers/loam`) — that's M12's job. Smoke uses local-tmp bare repo only; no GitHub state written.
- Re-edit of FBE.6 / FBE.6b / FBE.6c sealed sub-plan-docs — sealed-amendment historical records; not retroactively edited.
- FBE.6d re-verification cycle — separate dispatch post-FBE.11 seal (per dispatcher's brief).
- M12 publish-flip — separate dispatch gated on FBE.6d GO.
- Regression test for the dual-ref push behaviour (e.g., `test_AC_FBE_11_X_stranger_clone_from_dual_ref_published_remote.py` in workspace-bootstrap) — explicitly deferred to v0.1.x per dispatcher's brief.
- `pos-publish-framework-only` pyproject `pyyaml` dep fix (FBE.6c Surface #2) — out of scope; FUTURE_IDEAS_DRAFT candidate.
- HIGH-FBE6b.1 (339 `Amendment #N` source-comment references) — explicit dispatcher-deferral; document as known limitation in v0.1.0 release notes.

---

## 9. Halt triggers

Per dispatcher's brief:

1. WD drifts to pos3 → halt immediately.
2. Publish path is more complex than expected (e.g., requires github API calls, requires repo settings change beyond what the dispatcher specified) → halt + surface.
3. Sealed-component fence breach beyond plan-named → halt + surface.
4. Build cycle exceeds 50 min wall-clock → halt with partial findings.
5. Local-tmp-ref smoke fails (dual-ref push command syntax unexpected behaviour) → halt + surface; investigate before doc-edit lands.
6. `loam amend apply` partner-prefix derivation breaks beyond known FBE.{4,5,6b,6c} corrective pattern → halt + surface.
7. ODD violation discovered in surrounding code/docs → halt + surface; do not silently extend.

---

## 10. Risks

- **Risk: dual-ref push command syntax error.** Mitigation: smoke against local bare BEFORE editing the doc; if syntax fails, halt-trigger #5 fires.
- **Risk: doc edit at line 430 (historical record annotation) violates "don't retroactively edit history" principle.** Mitigation: edit is a parenthetical supersede note attached to the historical record, not a rewrite — preserves the as-dispatched fact and adds the post-FBE.11 supersede annotation. Same shape as FBE.6c's annotation of FBE.6/FBE.6b precedent in §4 / §8.
- **Risk: `loam amend apply` doesn't auto-commit.** 4 consecutive recurrences (FBE.6b/FBE.9/FBE.10/FBE.6c). Mitigation: manually commit per `chore(amend): FBE.11 apply` pattern; NEW commit, never `--amend`.
- **Risk: clean-tree requirement at seal.** Mitigation: `git stash push --include-untracked` pre-seal, pop post-seal (per FBE.6c Surface #6).
- **Risk: github default-branch settings drift.** Out of scope per Path B (we keep `main` as default; no `gh repo edit --default-branch` call required). FBE.11 makes no GitHub state changes at all.

---

## 11. AI-time band

- Predicted: **15–30 min, midpoint 22 min**; dispatch hard cap 50 min.
- Justification: Smaller scope than FBE.6c (no full M11a sweep, no full smoke install, no reviewer probe). Steps: sub-plan + manifest + 4 doc edits (small, targeted) + local-tmp-ref smoke (fast) + apply (with anticipated manual-commit recurrence) + seal + parent §8 backfill + status file. Dispatcher's brief estimated 10-20 min wall-clock for the fix; sub-plan + manifest + seal mechanics add ~10 min on top.

---

## 12. Method-decision register (post-build)

(Populated as commits land.)

- Plan-doc commit: `<TBD>`.
- Doc-edit commit (operator-instruction surfaces): `<TBD>`.
- HOL narrative anchor commit: `<TBD>`.
- Manifest commit: `<TBD>`.
- Apply commit: `<TBD>` (manual per anticipated `loam amend apply` no-auto-commit recurrence).
- Seal commit: `<TBD>`.
- Parent plan-doc §8 backfill commit: `<TBD>`.

---

*End of FBE.11 sub-plan-doc. BASELINE `03ef8da`. Next: doc edits → local-tmp-ref smoke → manifest + apply + seal → §8 backfill → status file.*
