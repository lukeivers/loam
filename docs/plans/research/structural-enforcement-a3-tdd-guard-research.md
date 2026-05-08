# Structural enforcement — A3: TDD-guard test-pinned-to-objective — Research

**Author:** research dispatch (Opus, background)
**Date:** 2026-04-28
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`
**Status:** authored, pending owner ruling on D-decisions §8 below.

**Locked governance (do not re-litigate):**

- Programme research: `docs/plans/research/structural-enforcement-of-critical-requirements-research.md` (locked 2026-04-26).
- A1 plan: `docs/plans/structural-enforcement-a1-substrate.md` (sealed; amendment #51).
- A2 plan: `docs/plans/structural-enforcement-a2-objective-binding-gate.md` (sealed; amendment #70).
- A2 builder plan: `docs/plans/structural-enforcement-a2-objective-binding-gate.builder-plan.md` (records D-build choices).
- A1 substrate code (read-only inputs): `framework/objective-tracker/src/{store.py,runtime.py}`, `framework/hands-off-lifecycle/hooks/{active_scope_sentinel.py,corpus_load_sentinel.py,objective_binding_gate.py}`.

**Programme-level locks (carried forward):** D1 dev-discipline carve-outs; **D2 TDD-guard scoped to re-extension-with-new-AC** (governs A3 directly); D3 manifest extends `objective-tracker`; D4 secret/blast-radius universal, ODD-discipline DEV-MODE-only; D5 KEEP-ADVISORY list of 10. None re-opened in this research.

**Pre-flight staleness result:** A3 has not shipped. `git log --grep="A3\|tdd-guard"` returns only A2's commit (which mentions A3 as the next gate). `ls docs/plans/ | grep -iE "a3|tdd-guard"` is empty.

---

## Summary (read this first)

A3 is the SECOND gate-that-refuses in the structural-enforcement programme, after A2 (objective-binding gate, sealed at amendment #70). A2 refuses Edits whose path doesn't trace to a manifest-registered binding the active-scope sentinel admits. A3 refuses Edits that introduce code satisfying a NEW acceptance criterion without a test pinned to that AC landing in the same diff.

**D2's lock — re-extension-with-new-AC scope.** A3 does NOT enforce "every code edit needs a test." It enforces ODD §4 re-extension semantics: when an amendment introduces a NEW AC (the canonical example: safety-layer's A20 added mid-build per odd-methodology §4.2), the test for that AC must exist on disk before the source edit fires. In-AC modifications and pure refactors of existing-AC code are not gated by A3 — A2's binding-glob already admits them.

The crux of A3's design space is the detection of "new AC in this diff." Three substrates carry the signal — the active-scope sentinel's bindings list (set at dispatch time), the objective-manifest table's row count for `(component, ac_id)` pairs (the build agent's row-registration discipline at AC-author time), and the plan-doc §4 AC list (text). The recommendation: **A3 keys off the manifest table**. A binding `(component, ac_id)` whose row was JUST REGISTERED in the current build's run-loop (i.e. registered after the active-scope sentinel was authored, OR registered with no prior rows for that AC) is "new in this diff." For each such AC, A3 requires a `tests/test_<AC-normalised>_*.py` file present on disk that contains a function whose name starts with `test_<AC-normalised>_`. Source-edit-without-test → deny.

**D2's lock also excludes test-without-implementation refusal from A3.** ODD §3.3 (one criterion per behaviour) implies the inverse direction (a test for an AC must have backing implementation), but the failure class A3 closes is the locked-research's named one — "code authored to non-existent contract, AC drift" (research §2 row #2). Test-without-implementation is a separate failure class; this research surfaces it as a candidate for a future amendment (§4 below) but A3's scope per D2 is implementation-without-test only.

Recommendation across the seven design questions:

- **Q1 firing layer:** `PreToolUse` matcher `Edit|Write|MultiEdit` (precedent A2). Single hook script `framework/hands-off-lifecycle/hooks/tdd_guard.py`. Mode-aware (DEV-MODE only per D4); composes on A1 substrate + A2's helper patterns.
- **Q2 "test pinned to AC" mechanism:** **filename-pattern-pinning** — `tests/test_<AC-normalised>_*.py` containing a function `test_<AC-normalised>_*`. The convention is already established (objective-tracker's `test_AC_SE_6_*`, A2's `test_AC_OBG_1_*`, orchestrator's `test_AC_A8_A_*`). No additional manifest column required; the file-name + function-name pair IS the pinning mechanism.
- **Q3 "new AC in this diff" detection:** key off the objective-manifest table. An AC bound by the active-scope sentinel whose `(component, ac_id)` either (a) has a manifest row whose `created_at` is strictly after the sentinel's `created_at` minus a small wall-clock skew tolerance, OR (b) the manifest table has NO seal-recorded prior row for that AC (this build registered the first row), is "new in this diff." Method per ODD §7.4; builder picks the exact predicate. A simpler shape: "AC is new if its first manifest row's `created_at` is after the sentinel's `created_at`" — handles the canonical case and the re-extension-mid-build case.
- **Q4 carve-outs:** A3 inherits A2's carve-out list (delegated to a shared helper if A3 ships first; otherwise inlined). Test-tree edits (`framework/<comp>/tests/**`) are EXCLUDED from A3's deny logic — the test file IS the satisfaction surface, gating its own creation creates a chicken-and-egg.
- **Q5 mode-aware refusal:** entirely DEV-MODE-only per D4. NORMAL USE workspaces no-op the gate at the mode-bit short circuit (mirrors A2's AC.OBG.6).
- **Q6 composition with A2:** A3 reads the same active-scope sentinel + same workspace-mode bit. A3's evaluator runs AFTER A2's evaluator in the hook chain (A2 admits the path; A3 then checks the test-existence). The shared helper library question (`_gate_helpers.py` per the locked programme research §7.1) RE-OPENS at A3 — A2 inlined helpers (D-build.2 of A2's builder plan rationale: premature extraction). A3 is the second gate; the research recommends extracting helpers NOW for reuse by A4.
- **Q7 audit log shape:** NDJSON at `<workspace>/workspace/.pos/tdd-guard.log`, schema mirrors A2's audit log (one decision per fire). Composes with FIDRAFT-143 dispatch-staleness consumer.

The plan that follows authors A3 with seven outcome-shaped ACs + a seal-diff invariant. Method (decision-tree shape, exact "AC normalisation" rule, helper-library extraction shape) is the builder's call.

---

## 1. What "test-pinned-to-objective" means structurally

### 1.1 The pinning mechanism — three candidates evaluated

| Candidate | Mechanism | Cost | Drift-resistance | Verdict |
|---|---|---|---|---|
| **α — filename + function-name pinning** | `tests/test_<AC>_*.py` containing `def test_<AC>_*(...)` (where `<AC>` is a normalised AC ID — e.g. `AC.OBG.1` → `AC_OBG_1`). Gate scans the test directory for the pattern. | Cheap (one `os.scandir` + name predicate). | High — the convention is already enforced socially in pos-v2; making it structural is a small step. Drift requires renaming a test that's already named correctly (rare). | **Recommended.** |
| β — manifest column `test_path_glob` | Extend A1's `objective_manifest` schema with a parallel `test_path_glob` column (or a `(component, ac_id, kind, path_glob)` row-shape with `kind in {source, test}`). Gate consults the table. | Higher — A1.1 corrective amendment to add the column / row-kind. | Higher — the table IS the authoritative registry; no convention drift. | Considered; **rejected** for A3 — the convention is already established and free; an A1.1 corrective is a substrate change A1's constraint 9 forbids without an explicit amendment. |
| γ — plan-doc §4 row count change | Parse the plan-doc, count the AC table rows, compare to seal-time count. New rows = new ACs. | Cheap (regex parse). | Low — plan-doc text is informal; format drift breaks the parser. | **Rejected** — too brittle; plan-docs ARE source-of-intent, not source-of-truth. |

**Recommendation: α (filename + function-name pinning).** The convention is already universal in pos-v2 (objective-tracker's `test_AC_SE_6_*`, A2's `test_AC_OBG_1_*`, orchestrator's `test_AC_A8_A_*`, workspace-bootstrap's `test_AC_E_1_*`). Making it structural is a small step that doesn't require a substrate change.

### 1.2 The "AC normalisation" rule

The convention writes AC IDs as either `AC.OBG.1` (dotted) or `AC_OBG_1` (underscored) depending on context. The plan-doc §4 uses dotted; tests use underscored. A3 needs a deterministic normalisation to compare.

**Recommendation:** dot → underscore + remove leading `AC.` if present + uppercase. So `AC.OBG.1` → `OBG_1`, `AC.SE.S` → `SE_S`, `AC_A8_A` → `A8_A`. The test-file glob becomes `test_AC_<normalised>_*.py`. Method per ODD §7.4 — the builder confirms the normalisation rule by reading existing test names and recording it in §14.

### 1.3 What "in the same diff" means

ODD §4 re-extension: the test must be authored BEFORE the source edit that satisfies the AC. "In the same diff" structurally means: at the moment the source `Edit` tool call fires, the test file must already exist on disk and contain a matching function.

The gate does NOT require git-log ordering (test commit before source commit). The gate fires per-edit at PreToolUse — by the time the source-`Edit` fires, the file system already reflects the test's authorship if it happened first. Git-log ordering is a stricter check that would require subprocess-ing `git log --follow`, slower, and unnecessary for the failure class — pre-existing-test-file-on-disk is the structural pinning.

### 1.4 The fence statement (A3's analogue to A2 §1.2)

An Edit/Write/MultiEdit on a non-test source path passes A3 when:

1. The workspace is `dev-mode` (else the gate does not apply); AND
2. A2 has already admitted the path (A3 fires AFTER A2; A2's deny short-circuits before A3 evaluates); AND
3. The path is not a test path (`framework/<comp>/tests/**`) — test edits bypass A3 (chicken-and-egg avoidance); AND
4. For every AC the active-scope sentinel binds AND that is "new in this diff" (per Q3 detection rule) AND whose manifest-row glob admits the path: a test file `framework/<comp>/tests/test_<AC-normalised>_*.py` exists AND contains a function `test_<AC-normalised>_*` (any body).

Failing condition 4 → deny with diagnostic naming the missing test path.

### 1.5 What the gate DOES NOT enforce (out of A3 scope per D2)

- **Pure refactor of existing-AC code.** AC bound by the sentinel has manifest rows from prior amendments (i.e. its row's `created_at` is BEFORE the sentinel's `created_at`). Gate is silent — A2's glob admission is the only check.
- **Test edit without backing source.** A test landed without an implementation. Out of A3 per D2 (test-without-impl is a separate failure class; §4.5 below names it as a future amendment candidate).
- **Test that exists but body is empty / passes-trivially.** A3 checks for existence + matching function name. Test correctness is the test-author's discipline; ODD §3.1 (deterministic check) is the test author's responsibility, not A3's.
- **Tests that test method, not behaviour** (ODD §8.2.10). Same — out of A3's surface; review-time concern.

These exclusions are deliberate — A3's leverage comes from closing the canonical "code-without-test" failure class structurally, not from policing test quality. Test quality is review-shaped.

---

## 2. "New AC in this diff" detection — three substrates evaluated

A3 fires only when a NEW AC is being declared in the current diff (D2 lock). The detection question: how does the gate know an AC is "new in this diff" vs "an existing AC the build is amending"?

### 2.1 Candidate A — manifest-table `created_at` comparison (RECOMMENDED)

When the build agent registers a manifest row for `(component, ac_id, source_path_glob)` at build start (per A2's hard constraint 14 — every build registers its rows BEFORE the first source edit), the row's `created_at` is the build-time wall clock. The active-scope sentinel's `created_at` is the dispatch-start wall clock (slightly earlier). When the row's `created_at` is later than the sentinel's, the AC is "new in this build's run-loop."

Implementation: for each binding `(component, ac_id)` in the sentinel, query `tracker.manifest_rows_for_ac(component, ac_id)`; for each returned row, compare `row.created_at >= sentinel.created_at`. If at least one row's `created_at` is after the sentinel — the AC is "new."

**Pros:**

- Substrate is already in place — A1's manifest table has `created_at`; A1's sentinel has `created_at`.
- No new schema field, no plan-doc parsing.
- Mirrors the same data shape A2 already consumes.
- Handles both canonical cases:
  - Amendment introducing a new AC fresh (first row registration in this build → row `created_at` after sentinel).
  - Amendment with multiple new ACs registered mid-build (each row's `created_at` recorded at registration time).

**Cons:**

- Wall-clock dependency. If the build agent's clock drifts from the sentinel-author's clock (extremely rare; same machine), comparison may misclassify by milliseconds. Mitigation: ISO-8601 with second resolution (per A1's `_now_iso` contract) — sub-second drift collapses. Same-machine/same-process — drift is essentially zero.
- Requires the build agent to follow A2's discipline (register rows BEFORE first source edit). If the build agent registers rows AFTER the first edit, A3 misclassifies the AC as "not new" and lets the edit through. Mitigation: A2 already denies the edit (no manifest row → AC.OBG.2 deny) so the order-bug doesn't pose a soundness hole — the build can't get past A2 without registering rows.

### 2.2 Candidate B — manifest-table existence check (any-row-or-no-row)

"AC is new if `manifest_rows_for_ac(c, a)` returned `[]` at sentinel-author time." Requires capturing the sentinel-author time state somehow.

**Rejected.** The "state-at-sentinel-author-time" capture is itself a new substrate (a snapshot mechanism). Substrate creep; A1 doesn't ship it. Equivalent to candidate A's `created_at` comparison but more complex.

### 2.3 Candidate C — plan-doc §4 row count diff vs seal-time

Parse the plan-doc, count §4 AC rows, compare to last-seal-time count. Difference = new ACs.

**Rejected.** Plan-doc parsing is brittle (free-form markdown table); format drift breaks the gate. ODD §3.3 names ACs as objective leaves but doesn't constrain plan-doc format. Out-of-band parsing fails the elimination-over-relocation test (ODD §5.1.1).

### 2.4 Candidate D — sentinel-binding diff vs prior-sentinel

Sentinel binds N (component, ac_id) pairs. If a binding was NOT in the previous sentinel for the same workspace, it's "new."

**Rejected.** The sentinel doesn't track prior state; would need a journal of past sentinels. New substrate; substrate creep.

### 2.5 Recommendation: A (manifest-table `created_at` comparison)

A is the cheapest correct shape. The substrate already exists; the comparison is one line. Method per ODD §7.4 — the exact predicate ("strictly after sentinel.created_at" vs "≥ sentinel.created_at - 1s" tolerance) is the builder's call; record in §14.

**Edge case — re-extension within an already-running scope.** A build agent discovers a §4 re-extension mid-build (canonical safety-layer A20 case). The agent registers a NEW manifest row for the new AC; the row's `created_at` is after the sentinel's. A3 correctly treats it as new and requires the test to exist before the source edit. The methodology's re-extension flow IS the gate's intended behaviour — author the test first, then the source.

---

## 3. Firing layer — five candidates evaluated (parallel to A2 §2)

### 3.1 Candidate A — `PreToolUse` matcher `Edit|Write|MultiEdit` (RECOMMENDED)

Mirrors A2 byte-for-byte. Same matcher, same envelope, same JSON-deny shape. Subagent-inheritance carries the gate to every dispatched build agent. Symmetric with the future A4 (Bash/Agent-context, different matchers).

**Pros:**

- Per-edit granularity (right surface for the failure class — code-without-test is per-edit).
- Composable with A2 in the same `PreToolUse` event chain — Claude Code admits multiple matcher entries.
- Settings-merge surface already authored by A2 (`merge_pre_tool_use` in `first_run_settings.py`); A3 extends it with the `_USER_AUTHORED` back-up convention adapted for multi-contributor.

**Cons:**

- Same per-fire latency budget as A2 (<100ms p95). A3's filesystem-scan (`os.scandir` on `framework/<comp>/tests/`) is the dominant cost — should be sub-10ms for typical-sized test directories.

### 3.2 Candidate B — Commit-time hook (`pos-amend apply --dry-run` extension)

Validate at amendment-commit time that every new AC in the diff has a matching test in the diff.

**Rejected:**

- Catches violations after the fact; recovery cost is high (already authored 50+ files; deny is too late). Same anti-pattern A2 §2.3 rejected.
- Doesn't compose with the build's run-loop.

### 3.3 Candidate C — Post-edit batch check (`Stop` hook)

After each turn ends, scan the diff for source files added/edited and verify each binds to a test.

**Rejected:**

- Misses per-edit granularity. The model edits, then turns, then sees the deny — but the edit already landed in tool-state.
- `Stop` hook can refuse stop, but the model has already committed in-memory edits to its plan; reverting is messy.

### 3.4 Candidate D — Two-phase: `Stop` + `PreCompact` chain

Multi-hook composition that captures source-edits and surfaces missing-tests at session boundary.

**Rejected:**

- Same problem as C plus more complexity. A3's leverage comes from refusing the EDIT, not the COMMIT or the SESSION.

### 3.5 Candidate E — `pos-amend seal --plan-doc` invariant

Add to `pos-amend seal`'s scoped test sweep an invariant "every new AC has a test."

**Rejected:**

- Catches at seal time; `pos-amend seal` runs AFTER the amendment commit. Way too late.

### 3.6 Recommendation: A (PreToolUse)

Mirrors A2 exactly. Same surface, same hook-chain composition, same audit-log pattern. The per-edit shape is correct for the failure class.

---

## 4. The new-test-without-implementation case (D2 lock check)

ODD §3.3 (one criterion per declared behaviour) implies a 1:1 mapping between ACs and tests. Logically this gives both directions:

- **Direction A (A3's surface):** code edit satisfying a new AC must have a backing test. A3 enforces.
- **Direction B (NOT A3's surface):** test for an AC must have backing implementation. A3 does NOT enforce.

### 4.1 Why direction B is out of A3's scope per D2

D2's lock: "TDD-guard scoped to re-extension-with-new-AC scenarios — not all-code-needs-test." The locked-research §2 row #2 names the failure class as "code authored to non-existent contract; AC drift" — direction A only.

Direction B failure looks different: a builder authors a test, then never authors the implementation. The test fails (red); the seal cycle catches it; the build doesn't ship. The failure mode self-corrects at seal time via the test sweep.

### 4.2 Why direction B is the WRONG default for a PreToolUse gate

Direction B fires on a `tests/test_*.py` Edit/Write — but pure test edits are common (test refinement, fixture adjustment, test-only failures discovered post-build). Refusing test edits unless a backing implementation exists would be a high false-positive rate.

Furthermore, ODD §4 re-extension EXPLICITLY admits "test before source" as the canonical sequence. A3 enforcing direction B would refuse the very sequence ODD recommends — the inverse of the methodology's intent.

### 4.3 Surfaced for future amendment (out of A3 scope)

If direction B becomes a real failure mode (tests authored without backing implementation, leaking through seal because the test happens to pass), a future amendment could:

- Land a `Stop`-hook invariant "every test_<AC>_*.py has a backing manifest row whose source_path_glob matches at least one source file under the same component." Single-fire-per-turn.
- OR a `pos-amend apply --dry-run` extension that checks the same invariant.

This is A4-adjacent or post-A4 territory; surfaced here for capture (FIDRAFT candidate).

### 4.4 Conclusion

A3 is direction A only. D2's scope is precise; expanding to direction B would risk false-positives + invert the §4 re-extension flow.

---

## 5. Mode-aware refusal — UNIVERSAL vs DEV-MODE-only

D4 lock: ODD-discipline gates DEV-MODE-only. A3 is ODD-discipline (test-pinned-to-AC enforces ODD §3.3 + §4). **A3 entirely no-ops in NORMAL USE.**

### 5.1 The reasoning chain

Same as A2 §5.1 byte-for-byte. NORMAL USE workspaces have no ACs to bind tests to; the gate has no input to evaluate. Mode-bit short-circuits.

### 5.2 Are there A3 sub-cases that should be UNIVERSAL?

No. Three candidates considered:

- **Edit on `tests/`** that introduces a test for a non-existent AC. This is direction-B (§4); not A3's surface.
- **Edit on source for an AC the test deletes.** Test-deletion is a separate failure class (regression); a future amendment's territory. Not A3.
- **Edit on a sealed-component source path in NORMAL USE.** Out of A3 (the ACs don't exist in NORMAL USE; no binding to enforce).

**Conclusion: A3 entirely DEV-MODE-only.** Identical to A2's conclusion.

---

## 6. Composition with A2 + A1

A3 is the second gate amendment; the architecture-creep watch from the locked programme research §7.1 (and A2's research §9.3) re-opens.

### 6.1 Shared helper library (`_gate_helpers.py`) — recommended for A3

A2's builder plan §D-build.2 inlined helpers in `objective_binding_gate.py` because A2 was the first gate (premature extraction reasoning). A3 is the second gate; helpers that should be shared:

- **Path canonicalisation** (`_workspace_relative` from A2). Identical in A3.
- **Mode-bit short-circuit** (lazy-import + fail-closed-to-permissive). Identical in A3.
- **Sentinel reader** (lazy-import + fail-soft). Identical in A3.
- **Tracker open** (lazy-import + venv path-fix). Identical in A3.
- **Carve-out detection** (`_is_carve_out_path`, `_CARVE_OUT_PREFIXES`, `_CARVE_OUT_FILES`). A3 inherits A2's carve-out list verbatim PLUS adds the test-tree exclusion (`framework/<comp>/tests/**`).
- **Audit-log writer** (`_append_audit_line`). Identical shape; different log filename per gate.

**Recommendation: extract `framework/hands-off-lifecycle/hooks/_gate_helpers.py`** as part of A3's seal-diff window, with A2's `objective_binding_gate.py` REFACTORED to consume the shared helpers (NOT a copy-paste; a refactor moving the shared code out of A2 into the helper module).

The refactor is in A3's seal-diff fence because A2 is sealed and A3 is the amendment that requires the shared surface. A2's seal-diff fence does not gain new admissions — A2's existing tests must continue to pass (regression-protected by `test_no_sealed_amendments.py` and the AC.OBG.S frozen-both-endpoints invariant).

**Risk:** the refactor edits files inside A2's already-sealed surface — `objective_binding_gate.py` is in `framework/hands-off-lifecycle/hooks/`. The fence shape: A3's amendment seal-diff window legitimately re-touches `objective_binding_gate.py` because it is in the same sealed component (`hands-off-lifecycle`); the H19-frozen-baseline pos-amend pattern accommodates this (per A2's manifest already at `frozen_baseline: true`). The AC.OBG.S frozen-both-endpoints test (A2's seal-diff invariant pinned to A2's window) is untouched — its endpoints close before A3 begins.

### 6.2 Hook-chain ordering (A2 then A3)

Both gates are PreToolUse matcher `Edit|Write|MultiEdit`. Claude Code admits multiple matchers; the documented behaviour is sequential evaluation in the order they appear in `settings.json`. A3 runs AFTER A2 — A2's `permissionDecision: deny` short-circuits A3 (Claude Code doesn't invoke later hooks once a deny lands).

This means A3's gate ONLY fires when A2 has already admitted the path. A3 inherits A2's path-binding correctness for free; A3 only verifies the additional test-existence invariant. The hook-script can therefore skip carve-out checks and sentinel-presence checks (A2 already handled them), but defensive duplication is cheap (sub-millisecond) and per-gate isolation is the architecture-creep-watch's recommendation.

**Recommendation:** A3's gate runs the FULL decision chain (mode + carve-out + sentinel-presence + binding-presence + new-AC-detection + test-existence). Defensive in case the hook-chain ordering changes, OR in case A2 is removed in a future amendment, OR in case a carve-out path is shared between the two gates' lists asymmetrically. The duplicated work is bounded.

### 6.3 Audit-log shape

NDJSON at `<workspace>/workspace/.pos/tdd-guard.log`. Fields:

- `ts` (ISO-8601 UTC)
- `tool` (Edit / Write / MultiEdit)
- `path` (raw)
- `rel_path` (workspace-relative, or null)
- `mode` (dev-mode / normal-use)
- `sentinel_state` (present / absent)
- `bound_acs` (list of `{component, ac_id}` dicts)
- `new_acs_in_scope` (list of `{component, ac_id}` dicts — the subset of bound_acs A3 considers "new in this diff")
- `tests_present` (list of `{ac_id, test_path}` dicts for ACs whose test was found)
- `tests_missing` (list of `{ac_id, expected_test_glob}` dicts for ACs whose test was NOT found — empty on allow)
- `decision` (allow / deny / no-op)
- `failure_class` (missing-test-for-new-ac / null)
- `reason` (deny reason text, or null)

Mirrors A2's audit log; consumed by FIDRAFT-143 dispatch-staleness check + future observability surfaces.

### 6.4 Composition with FIDRAFT items

- **FIDRAFT-130 (corpus-inlining):** identical to A2 — A3 reads the corpus-load sentinel for diagnostic purposes only; does not refuse for missing corpus.
- **FIDRAFT-136 (main-session-write-prevention):** orthogonal — different decision data. A3 doesn't preempt this future amendment.
- **FIDRAFT-143 (dispatch-staleness):** A3's audit log is additional substrate for the future staleness check. Same composition shape as A2.

### 6.5 Composition summary

A3 is the second gate; its main composition impact is the helper-library extraction (one-time cost) + hook-chain ordering (zero design cost, settings.json artefact). A4 inherits the helper library and the hook-chain pattern.

---

## 7. Failure-mode taxonomy

### 7.1 New AC bound, no test file exists

- **State:** sentinel binds `(X, Y)`; `manifest_rows_for_ac(X, Y)` has at least one row whose `created_at` is after sentinel's; no file `framework/<X>/tests/test_AC_<Y-normalised>_*.py` exists.
- **Cause:** builder authoring code-first (canonical D2 failure class).
- **Decision:** **deny** with diagnostic naming (a) the AC, (b) the expected test path glob, (c) the repair direction ("author the test first, then retry the source edit").

### 7.2 Test file exists but no matching function

- **State:** `framework/<X>/tests/test_AC_<Y-normalised>_something.py` exists, but no function inside starts with `test_AC_<Y-normalised>_`.
- **Cause:** builder created the file but renamed the function, OR copy-paste from another AC's test left the wrong function name.
- **Decision:** **deny** with diagnostic naming the file + the expected function-name pattern.
- **Implementation note:** the gate scans the file for `def test_AC_<Y-normalised>_` regex; a body-empty function still passes (test correctness is reviewer-shaped per §1.5).

### 7.3 Multiple new ACs, some have tests, some don't

- **State:** sentinel binds two new ACs; one has a test, one doesn't.
- **Decision:** **deny** with a diagnostic listing both new ACs and which is missing.

### 7.4 New AC bound, test exists, gate allows

- **State:** sentinel binds `(X, Y)`; row's `created_at` is after sentinel's; `framework/<X>/tests/test_AC_<Y-normalised>_*.py` exists with matching function.
- **Decision:** **allow.** The path then falls through to A2's binding-glob check (which already admitted, given A3 fires after A2).

### 7.5 Existing-AC edit (not new in this diff)

- **State:** sentinel binds `(X, Y)`; manifest rows for `(X, Y)` all have `created_at` BEFORE sentinel's.
- **Decision:** **allow** (not in A3's scope per D2). The path is gated only by A2's binding-glob check.

### 7.6 Test-tree edit

- **State:** path matches `framework/<comp>/tests/**`.
- **Decision:** **allow** (chicken-and-egg avoidance — the gate must not refuse the test it requires). A3's deny logic is per-source-path; test-paths short-circuit.

### 7.7 Carve-out edit (docs/, plans/, etc.)

- **State:** path matches A2's carve-out list.
- **Decision:** **allow.** Inherited from A2's carve-out treatment; A3 is silent.

### 7.8 Substrate-unreachable

- **State:** tracker can't be opened (venv missing, db absent).
- **Decision:** **allow.** Mirrors A2's fail-closed-to-permissive at the import boundary. Audit log records the failure.

### 7.9 Race conditions

Three race shapes considered:

- **Race A — Test file creation mid-source-edit.** Test author creates the file; gate fires; gate sees the file. Atomic-create-via-write-and-rename guarantees see-or-don't-see. Same property as A1's sentinel reader.
- **Race B — Manifest row registration mid-evaluation.** Builder registers row, then edits, then test-author-time vs source-edit-time. SQLite WAL gives consistent snapshot; comparison is `created_at` against sentinel-`created_at` (both fixed values once read).
- **Race C — Sentinel rewrite mid-evaluation.** Sentinel author writes `.tmp` then renames; gate sees pre or post atomically.

No soundness holes.

---

## 8. Design-decision register (for the plan)

The seven design decisions §1–§7 surface, with recommendations:

| ID | Question | Recommendation | Open / Locked |
|---|---|---|---|
| D-A3.1 | Firing layer | Candidate A — `PreToolUse` matcher `Edit\|Write\|MultiEdit` (§3.6) | Open for owner ruling |
| D-A3.2 | Refusal mechanism | Candidate α — `permissionDecision: deny` + structured `permissionDecisionReason` (mirrors A2) | Open for owner ruling |
| D-A3.3 | Pinning mechanism | Candidate α — filename + function-name pinning (`tests/test_AC_<normalised>_*.py` containing `def test_AC_<normalised>_*`) (§1.1) | Open for owner ruling |
| D-A3.4 | "New AC in this diff" detection | Candidate A — manifest-row `created_at` strictly after sentinel `created_at` (§2.5) | Open for owner ruling |
| D-A3.5 | Direction (impl-without-test only, per D2) | Direction A only — out-of-scope for direction B (test-without-impl) (§4.4) | Locked by programme D2 |
| D-A3.6 | DEV-MODE / UNIVERSAL split | Entirely DEV-MODE-only (§5.2) — programme-D4 lock subsumes | Locked by programme D4 |
| D-A3.7 | Helper-library extraction | Extract `_gate_helpers.py` as part of A3's seal-diff (refactor A2's hook to consume) (§6.1) | Open for owner ruling |
| D-A3.8 | Hook-chain ordering | A3 runs AFTER A2; A3 runs the full decision chain (defensive duplication) (§6.2) | Open for owner ruling |
| D-A3.9 | AC normalisation rule | Dot → underscore + uppercase + drop leading `AC.` if present (`AC.OBG.1` → `OBG_1`) (§1.2) | Open for owner ruling — method-shaped, builder may refine |
| D-A3.10 | Audit log shape | NDJSON at `<workspace>/workspace/.pos/tdd-guard.log` mirroring A2's pattern (§6.3) | Open for owner ruling — method-shaped per ODD §7.4 |

Owner is asked to rule on D-A3.1, D-A3.2, D-A3.3, D-A3.4, D-A3.7, D-A3.8. D-A3.5 is locked by programme D2. D-A3.6 is locked by programme D4. D-A3.9 + D-A3.10 are method per ODD §7.4 (the builder may refine the normalisation rule and log path / format if a sibling amendment standardises a different shape).

### Surfaced for owner ruling: 6 (D-A3.1, D-A3.2, D-A3.3, D-A3.4, D-A3.7, D-A3.8).

---

## 9. Sealed-component fence + halt triggers

### 9.1 Fence

A3 is a hands-off-lifecycle amendment. Same fence as A2. Single sealed component touched: `hands-off-lifecycle/`. `objective-tracker/` is consumer-only (A3 reads `manifest_rows_for_ac`); `loam-mode/` is consumer-only via `corpus_load_sentinel.workspace_mode()`.

A3's seal-diff window ⊆ `framework/hands-off-lifecycle/{hooks,tests,seals}/` plus the universal-paths admissions. A3's hook script (`tdd_guard.py`) is new; the helper library (`_gate_helpers.py`) is new; A2's `objective_binding_gate.py` is REFACTORED in-place to consume the helper library (no behaviour change; existing AC.OBG.x tests must remain green).

### 9.2 Halt triggers

A3 build halts on:

1. **A1 substrate gap.** Any A1-substrate field A3 needs that A1 didn't ship → halt; A1.1 corrective. Specifically: if `manifest_rows_for_ac` doesn't return rows with `created_at`; if the active-scope sentinel doesn't expose `created_at`; if `workspace_mode` doesn't expose the two-string contract A3 expects. Verification at build start: read A1 readers/writers and confirm shapes.
2. **A2 helper incompatibility.** If A2's `objective_binding_gate.py` cannot be refactored to consume `_gate_helpers.py` without breaking AC.OBG.x tests, halt. Specifically: if A2's helpers depend on module-private state that doesn't survive extraction; if the lazy-import pattern creates circular import risks. Verification: dry-run-extract before authoring A3's gate.
3. **A2 manifest API insufficient.** If `manifest_rows_for_ac` returns rows in a shape that doesn't include `created_at` directly readable by A3, halt. Verification: read `objective-tracker/src/store.py::list_manifest_rows_for_ac` at build start and confirm the dict-shape includes `created_at`.
4. **MultiEdit semantics.** Same as A2's halt-trigger 3 — verified empirically by A2 build (Q1 answer in builder plan §5: MultiEdit is single-path, no batch-of-paths). A3 inherits the answer; verification: confirm A2's empirical answer still holds. No new investigation needed.
5. **Existing PreToolUse hook collision.** Settings.json may now have two pos-v2-owned PreToolUse entries (A2's `objective_binding_gate.py` + A3's `tdd_guard.py`) plus user-authored entries. The `merge_pre_tool_use` mechanism A2 shipped is single-contributor; A3 needs multi-contributor. Halt if the existing merge function cannot accept two pos-v2 entries simultaneously without contract change.
6. **Surrounding-code ODD §2.5 violation.** Adjacent modules may surface §2.5 violations during the helper-extraction refactor. Halt-and-surface per the dispatch's explicit ODD-violation clause.
7. **Outcome-resistant AC.** Same as A2 — if any A3 behaviour resists outcome-shaping during plan-doc authoring, halt.
8. **Architecture creep — multi-tenant gate framework.** The helper-extraction question may surface a deeper "should the gates share a single entry-point dispatcher" question. The locked programme research §7.1 + A2's research §9.3 + this research §6.1 all recommend per-amendment hooks with shared helpers. If the builder strongly disagrees, halt — owner-decision.
9. **Substrate-fence breach.** Per constraint 1: any source-edit need outside `framework/hands-off-lifecycle/{hooks,tests,seals}/` halts. Universal-paths admissions are the only exception.
10. **Self-bootstrap fails.** Per A2's hard constraint 14 (mirrored to A3): the build agent's first action is registering manifest rows for AC.TDG.x. The build agent's own first source edit on `tdd_guard.py` must pass A3 itself — meaning the test for AC.TDG.1 must already exist before the source. Bootstrap order: (a) register manifest rows for AC.TDG.1..AC.TDG.S; (b) author test files first; (c) author source files. If the bootstrap order is violated, A3's own gate denies A3's own build.
11. **AC normalisation ambiguity.** If existing pos-v2 test names follow inconsistent conventions (e.g. some `test_AC_OBG_1`, some `test_OBG_1`, some `test_A20_*`), the normalisation rule may not have a deterministic canonical form. Verification at build start: scan `framework/*/tests/test_AC*.py` filenames + sample function names; if conventions diverge, surface to owner.

### 9.3 Architecture-creep watch

The deeper question: **should A3's hook be a separate entry point, or should it be a sub-decision inside A2's `objective_binding_gate.py`?** Combining gates into one script saves a settings.json entry and one process-spawn cost but couples the two failure classes; separating keeps each gate isolated.

The locked programme research §6.2 + A2 research §9.3 recommend separation. This research concurs: A3 is its own script importing shared helpers. The settings.json gains a second PreToolUse entry; the merge mechanism handles multi-pos-v2-contributor.

**Conclusion: per-amendment hooks; shared helper library (extracted in A3); no architecture creep.**

---

## 10. Migration / coexistence with already-active sessions

When A3 lands, sessions in flight that are mid-build face A3's deny on the first source edit for a new AC unless the test already exists. Two sub-cases:

### 10.1 Sessions building amendments where the test was authored first

These sessions already follow ODD §4 re-extension. A3 is a no-op for them. No migration cost.

### 10.2 Sessions building amendments where source landed first (TDD violation)

These sessions face a deny on the next source edit. The deny diagnostic names the missing test path; the operator authors the test, then retries the source edit. Operator pain ~one diagnostic-read per affected session.

### 10.3 Migration shape — hard cutover with diagnostic-named-repair

Same shape as A2 (Shape α from A2's research §7.1). Recommendation: hard cutover. Soft cutover is rule-shaped (relocate-not-eliminate). Operator pain is bounded; the diagnostic names the exact repair.

---

## 11. ODD self-check on the proposed AC set

### 11.1 Acceptance criteria the plan will declare

(Pre-authored here so the §8.1 check is grounded; the plan §4 reproduces them.)

- **AC.TDG.1 — Gate refuses Edit on sealed-component non-test source for a NEW AC with no matching test file (DEV MODE).** Hook fires on `PreToolUse Edit|Write|MultiEdit`; mode = `dev-mode`; A2 has admitted; path is non-test source; sentinel binds AC `(X, Y)`; `(X, Y)`'s manifest-row `created_at` is after sentinel's `created_at`; `framework/<X>/tests/test_AC_<Y-normalised>_*.py` does not exist → returns `permissionDecision: "deny"` with structured reason naming the missing test path + repair direction.
- **AC.TDG.2 — Gate refuses Edit when test file exists but matching function is absent.** Test file exists at the expected path; no `def test_AC_<Y-normalised>_*` inside → deny with reason naming the file + the expected function-name pattern.
- **AC.TDG.3 — Gate allows Edit when path is a test path.** Path matches `framework/<comp>/tests/**` → allow regardless of new-AC state (chicken-and-egg avoidance).
- **AC.TDG.4 — Gate allows Edit when AC is NOT new (existing AC, in-AC modification).** Sentinel binds `(X, Y)`; all manifest rows for `(X, Y)` have `created_at` BEFORE sentinel's → allow (not in A3's scope per D2).
- **AC.TDG.5 — Gate allows Edit when new AC has matching test (file + function).** Sentinel binds `(X, Y)`; `(X, Y)`'s row `created_at` after sentinel's; test file + function present → allow.
- **AC.TDG.6 — Gate is a no-op when workspace-mode is `normal-use`.** Mode = `normal-use` → allow regardless of all other state. Mode-bit-only branch (cheap path).
- **AC.TDG.7 — Gate audit log writes deterministic NDJSON per fire.** Every fire (allow + deny + no-op) appends one line to `<workspace>/workspace/.pos/tdd-guard.log` with a documented schema. Append-only in A3.
- **AC.TDG.S — Seal-diff confined to fence.** A3's seal-diff window contains only edits under `framework/hands-off-lifecycle/{hooks,tests,seals}/` and the universal-paths admissions. Frozen-both-endpoints per `docs/odd-in-pos.md` §10.3.

Optional eighth AC if the helper-library extraction is approved (D-A3.7):

- **AC.TDG.8 — Helper-library extraction preserves A2's behaviour.** Post-extraction, A2's existing AC.OBG.1..AC.OBG.7 tests pass byte-for-byte; AC.OBG.S frozen-both-endpoints invariant unchanged; `objective_binding_gate.py` consumes `_gate_helpers.py` symbols; behaviour-equivalent at the hook-envelope-in/JSON-out boundary.

### 11.2 §8.1 authoring-time violation checks

| Check | Pass / Fail |
|---|---|
| §8.1.1 Method in acceptance | PASS — every AC is outcome-shaped. "Returns permissionDecision: deny" is a Claude Code surface contract, not a method choice. The "matching function" check is a behavioural assertion, not method (the gate's INTERNAL regex/AST shape is method). |
| §8.1.2 Behaviour-count match | 7 AC behaviours + 1 invariant = 8 (or 9 with optional helper-extraction AC). Behaviours declared in §11.1: 7 (deny-no-test, deny-no-function, allow-test-path, allow-existing-AC, allow-test-present, no-op-normal-use, audit-log) + S = 8. PASS — match. |
| §8.1.3 Missing acceptance | PASS — every behaviour has an AC. |
| §8.1.4 Acceptance relies on judgment | PASS — every AC is mechanical. Test-existence is a stat call; matching-function is a regex; new-AC detection is a `created_at` comparison. |
| §8.1.5 Procedure in objective | PASS — no "first X then Y" in any AC. |
| §8.1.6 Unbounded scope | PASS — §9 hard constraints fence the surface. |
| §8.1.7 Missing halt trigger | PASS — §9.2 names halt triggers explicitly. |

### 11.3 §2.5 reverse-direction (forward-only at plan-author time; full reverse is the builder's audit)

Plan-author confirms each declared behaviour (§11.1) maps to exactly one AC. The builder's reverse-direction audit is the run-time check.

### 11.4 Constraint completeness

Per ODD §2.2 the five constraint shapes:

- **Budget:** PreToolUse hook < 100ms p95 (matches A2 envelope; tighter target < 50ms). Filesystem scan via `os.scandir` on `framework/<comp>/tests/` is the dominant cost; sub-10ms for typical-sized directories.
- **Reversibility:** fully reversible. The hook is additive; an existing settings.json without the entry continues to work; removing the entry restores prior behaviour. The helper-library extraction (D-A3.7) is also reversible — A2's gate could be reverted to inlined helpers if needed (though no current plan to do so).
- **Dependency fence:** stdlib-only-plus-A1-substrate. Imports from `objective-tracker.runtime` (public read API), `hands-off-lifecycle.hooks.active_scope_sentinel`, `hands-off-lifecycle.hooks.corpus_load_sentinel.workspace_mode`. New shared helper module `framework/hands-off-lifecycle/hooks/_gate_helpers.py`.
- **Authority bound:** A3 may not amend `objective-tracker` schema, may not amend A1's sentinel JSON shape, may not amend `loam-mode`'s mode-bit interface. Read-only against all three. Single sealed component touched: `hands-off-lifecycle/`.
- **Fail-closed direction:** deny on missing test (DEV MODE, new AC, non-test path). The DENY direction is fail-closed; the NORMAL-USE direction is fail-open (mode short-circuit). Substrate-unreachable falls through to allow (fail-closed-to-permissive at import boundary, mirrors A2).

All five present.

---

## 12. Open questions (research-time)

### Q1 — AC normalisation rule precision

The exact normalisation rule (`AC.OBG.1` → `OBG_1` vs `AC_OBG_1` vs `aobg1`) has multiple candidate forms. Existing test names use `test_AC_OBG_1_*`, `test_AC_SE_6_*`, `test_AC_A8_A_*`, `test_AC36_3_*`, `test_AC39_2_*`. The pattern is `test_AC_<id>_*` where `<id>` is dot-replaced-with-underscore. **Recommendation:** the builder reads existing test names at build start, derives the deterministic rule, records it in §14.

### Q2 — Multi-glob source path admission

A single AC may have multiple manifest rows (e.g. `framework/<comp>/src/**` AND `framework/<comp>/tests/**`). When evaluating "does this path require a new test?", A3 should scope the check per source-glob row, not per binding. **Recommendation:** the builder verifies; A3's "is path a test path" check happens BEFORE the new-AC check (test-tree edits are silent).

### Q3 — Sentinel-binding without manifest-row registration order

The build agent's discipline (per A2 hard constraint 14) is "register manifest rows BEFORE the first source edit." A3 depends on this — if rows are registered AFTER edits, A3's `created_at` comparison misclassifies. **Recommendation:** A3 inherits A2's discipline; A2 already denies edits without rows (AC.OBG.2). If the build agent skips row registration, A2 denies before A3 ever runs.

### Q4 — Test file body validation depth

Should A3 verify the function body is non-trivial (not just `pass` or `assert True`)? **Recommendation: NO.** Test correctness is reviewer territory (ODD §8.2.10). A3 only verifies existence + matching function name; quality is out of scope.

### Q5 — Helper-library extraction shape detail

The shape of `_gate_helpers.py` (a single module vs a small package) is method per ODD §7.4. **Recommendation:** single module for now (A2's helper count is small); package shape opens if A4 adds more helpers.

### Q6 — Direction-B (test-without-impl) future amendment

If direction B becomes a real failure mode post-A3, the right surface is a `Stop` hook or `pos-amend apply --dry-run` extension. **Surfaced for FIDRAFT capture; not blocking for A3.**

---

## 13. Cross-references

- Locked research (governs): `docs/plans/research/structural-enforcement-of-critical-requirements-research.md`
- A1 plan (sealed): `docs/plans/structural-enforcement-a1-substrate.md`
- A2 plan (sealed): `docs/plans/structural-enforcement-a2-objective-binding-gate.md`
- A2 builder plan (records D-build choices A3 inherits / questions): `docs/plans/structural-enforcement-a2-objective-binding-gate.builder-plan.md`
- A1 substrate code (read-only inputs):
  - `framework/objective-tracker/src/store.py` (manifest table CRUD; `objective_manifest` schema with `created_at`)
  - `framework/objective-tracker/src/runtime.py` (public API: `register_source_binding`, `manifest_rows_for_*`)
  - `framework/hands-off-lifecycle/hooks/active_scope_sentinel.py` (reader; `ActiveScopeSentinel.created_at`)
  - `framework/hands-off-lifecycle/hooks/corpus_load_sentinel.py` (workspace-mode bit)
- A2 gate code (helper-extraction source):
  - `framework/hands-off-lifecycle/hooks/objective_binding_gate.py` (the candidate-extraction body)
  - `framework/hands-off-lifecycle/hooks/first_run_settings.py` (`merge_pre_tool_use` — A3 may need multi-contributor extension)
  - `framework/hands-off-lifecycle/hooks/first_run_helper.py` (composition wiring; A3 extends with second `_maybe_merge_pre_tool_use` call site)
- ODD methodology: `docs/odd-methodology.md` (§3.3 one-criterion-per-behaviour; §4 re-extension; §5.1 structural-over-advisory; §5.1.1 relocate-vs-eliminate; §7.4 flagged inferences; §8.1 authoring-time violations)
- ODD-in-pos: `docs/odd-in-pos.md` (§10.3 frozen-both-endpoints baseline pattern — A3's seal-diff invariant test)
- VALUE_PROPOSITION: `docs/VALUE_PROPOSITION.md` (AC.PO.1 + AC.PO.2 — Lens 2 anchor)
- FUTURE_IDEAS: `docs/FUTURE_IDEAS.md` Idea 1 (programme), Idea 8 (structural context-load gate)
- FIDRAFT items: `docs/FUTURE_IDEAS_DRAFT.md` lines 130 (corpus-inlining), 136 (main-session-write-prevention), 143 (dispatch-staleness)
- Test-naming convention examples (existing established convention):
  - `framework/objective-tracker/tests/test_AC_SE_6_objective_manifest_table.py`
  - `framework/hands-off-lifecycle/tests/test_AC_OBG_1_deny_missing_sentinel.py`
  - `framework/orchestrator/tests/test_AC_A8_A_activate_scope_with_spec.py`
  - `framework/workspace-bootstrap/tests/test_AC_E_1_classify_dev_when_dev_intent_yes.py`
- Claude Code hooks docs: https://code.claude.com/docs/en/hooks (PreToolUse decision-control surface; matchers; multiple-matcher-entry support)

---

*End of research artefact. Plan-doc at `docs/plans/structural-enforcement-a3-tdd-guard.md` consumes these findings.*
