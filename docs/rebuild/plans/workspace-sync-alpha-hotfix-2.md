# workspace-sync — α-hotfix-2: close 4 correctness bugs of the verdict-without-stage class — plan

Sealed-component amendment extending the existing `workspace-sync/`
component. Closes the 3 follow-on bugs (HALT-FOUND #1, #2, #3) surfaced
during α-hotfix #59 plan authoring + Bug D (state.yaml hygiene)
caught by primary persona during post-#59 verification. All four
share the same fault-class as #59: verdict set without content
staged → silent no-op at apply time → false-success.

**Status:** plan (pre-dispatch). 2026-04-26.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`
**Companions:**
- **#59 plan-doc** (α-hotfix #1 — fixed the NN branch only): `docs/rebuild/plans/workspace-sync-alpha-hotfix.md`
- **#57 plan-doc** (Bundle α — introduced the NN ancestor-detection fast-path that #59 + this hotfix repair): `docs/rebuild/plans/workspace-sync-resolver-cost-overhaul.md`
- **#56 plan-doc** (workspace-sync keystone): `docs/rebuild/plans/workspace-sync.md`
- **`workspace-sync/src/workspace_sync/cli.py`** — Bug A + Bug B sites (lines 271-278); Bug D's missing post-discard guard.
- **`workspace-sync/src/workspace_sync/conflict_report.py`** — Bug C site (validator).
- **`workspace-sync/src/workspace_sync/merge_helper.py`** — Bug D site (state-write SUCCESS in finally block); rename surface for centralization.
- **`workspace-sync/src/workspace_sync/state.py`** — Bug D enum addition.

**Ancestor record:**
- **#56 sealed `0607dc7`** — established stage-then-atomic-apply.
- **#57 sealed `e619b6a`** — added NN fast-path; introduced the verdict-without-stage shape.
- **#59 sealed `f1abded`** — fixed NN branch; surfaced HALT-FOUND #1, #2, #3 in plan-doc §13 for follow-on amendment ruling.
- **Direct empirical reproduction post-#59 (2026-04-27):** primary persona ran `pos-sync --workspace /Users/lukeivers/pos3 --auto-accept --confidence-floor 0.85` against canonical. Pre-#59 NN-resolved paths were unstaged; #59 fixed those. But verification revealed:
  1. state.yaml advanced to SUCCESS even when staging was discarded (Bug D — caught after #59 sealed).
  2. The cli.py:271-274 LLM-resolver path remains unstaged (Bug A — surfaced in #59's §13 HALT-FOUND #1).
  3. The cli.py:275-278 Class-B append-after-stage was a no-op (Bug B — surfaced in #59's §13 HALT-FOUND #2).
  4. The validator gap let null-content-path entries pass shape-check (Bug C — surfaced in #59's §13 HALT-FOUND #3).

**Research:** No new research dispatched — all four bugs are documented + reproducible. Bug A + Bug B fix shape composes on the staging primitive added in #59 (`_stage_canonical_for_nn_match`); Bug C is a validator extension; Bug D is a status-enum addition + a single line change in merge_helper.

---

## 1. Summary / TLDR

Four observables, one fault-class:

| Bug | Site | Observable post-fix |
|---|---|---|
| A | cli.py:271-274 LLM-resolver INFERRED_ACCEPT_CANONICAL | Workspace file matches canonical HEAD blob byte-for-byte |
| B | cli.py:275-278 Class-B ACCEPT_UPSTREAM | Workspace file matches canonical HEAD blob byte-for-byte |
| C | conflict_report.py validator | Constructing entry with null resolved_content_path for INFERRED_ACCEPT_CANONICAL or ACCEPT_UPSTREAM raises ValueError |
| D | state.yaml advances to SUCCESS even on discard | After --auto-accept discard, state.status is NOT SUCCESS; next run re-resolves (no false-idempotent) |

**The fix shape (centralized).** α-hotfix #59 added `_stage_canonical_for_nn_match` in `merge_helper.py` — read canonical's HEAD content via `git show <ref>:<path>`, decode UTF-8, write to staging via the `write_merged` callable, set `entry.resolved_content_path`. This hotfix:

1. Promotes that helper to a public-shaped `stage_canonical_at_ref` (drops leading underscore; same signature). Calls it from cli.py for both `INFERRED_ACCEPT_CANONICAL` (LLM-resolver path) and `ACCEPT_UPSTREAM` (Class-B path).
2. Tightens the `ConflictEntry` validator to require `resolved_content_path` for both resolutions — structural enforcement-default per ODD §5.3.
3. Adds `SyncStatus.NEEDS_APPLY`; merge_helper writes that on clean-resolve; cli.py post-apply remains the only writer of SUCCESS.

**Critical regression tests (HC#3 binding).** Three file-content-byte-match assertions (Bug A, Bug B, Bug D) plus two validator-rejection tests (Bug C). Same discipline as #59 — verdict-shape tests would let bugs of this class re-ship.

**Hard Constraint #1.** No edits outside `workspace-sync/`. Plan-doc + manifest + tests + source — purely additive in `workspace-sync/`.

**Bundle splitting / ordering.** Single amendment (one commit). Lands as **amendment #60** (next free after #59). Same-tree-serialize against any other in-flight amendment work.

**This is sealed-component scope.** workspace-sync/ is the only fence touched; plan + builder-plan + manifest land per the dev CDC.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)

This amendment composes under **VALUE_PROPOSITION's AC.PO.1 (translation-burden absorption)** — the prime objective per CLAUDE.md §2.5. All four bugs break AC.PO.1 in the same way #59 did: when the operator says "pull the latest", the persona translates to `pos-sync`, the CLI reports success (or false-idempotent on re-run), and the workspace files stay stale. Translation broken at substrate. **No new top-level objective.** Halt trigger 1 evaluated: does not fire.

**Reverse trace per CLAUDE.md §2.5.**

- **AC.PO.1 (translation-burden):**
  - Bug A: LLM-resolver path on Class-C conflicts (most common after NN declines) silently fails. Post-fix it succeeds.
  - Bug B: Class-B operator-prefers-canonical path silently fails. Post-fix it succeeds.
  - Bug C: structural-enforcement-default ensures future amendments cannot ship the same fault-class without explicit override.
  - Bug D: re-runs after a discarded staging silently no-op via the idempotency fast-path (the worst form of false-success — the operator believes they're synced and isn't). Post-fix re-run re-resolves correctly.

- **AC.PO.2 (toolkit-primitive growth):**
  - Centralizes the staging primitive (`stage_canonical_at_ref` is the new public shape).
  - Adds `SyncStatus.NEEDS_APPLY` — a new state-machine value in the toolkit.
  - Adds the validator-as-bug-class-trap pattern: future verdict-without-stage shapes can't ship.

---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude leverage

This is a substrate-level correctness fix. No new Claude-native primitives are leaned on or composed against. The α.1 ancestor-detection fast-path itself (Bundle α / #57) IS a Claude-cost-avoidance primitive; this hotfix preserves and completes its sibling code paths. No Claude-side capability surface changes.

### Lens 2 — Harness + primary-persona value

**Primary-persona test (translation burden):** Same shape as #59. Pre-hotfix the persona's translation of "pull the latest" silently fails on the LLM-resolver and Class-B branches. Post-hotfix it succeeds. **Reduces translation burden absolutely** (from "broken on these branches" to "works").

**Harness test (toolkit growth):**
1. Centralizes the staging primitive (single point for all accept-canonical-flavored verdicts to stage canonical content). Composable in all future workspace-sync amendments.
2. Adds `SyncStatus.NEEDS_APPLY` — a state-machine primitive that makes "resolved cleanly but apply not yet run" an observable distinct from "resolved + applied". Future amendments can compose against it (e.g., a "re-confirm staging" command that reads `NEEDS_APPLY` state and offers re-confirm).
3. Tightens the validator to make verdict-without-stage structurally impossible — a structural-enforcement-default primitive that catches the entire bug class.

### Lens 3 — ODD authoring

Four ACs (one per bug) plus AC.S seal-diff invariant. Outcome-shape only. Method-shape (which exact lines, which test functions, which subprocess argv) is the builder's call inside each AC's outcome bound.

---

## 4. Acceptance criteria (AC.α-hotfix-2.x)

### AC.α-hotfix-2.1 — LLM-resolver INFERRED_ACCEPT_CANONICAL paths overwrite workspace files (Bug A)

**Outcome.** When the LLM resolver returns `MergeVerdict(resolution="inferred-accept-canonical", ...)` (i.e., NOT via the α.1 NN fast-path), the post-resolve loop in `cli.py` reads canonical's HEAD content for `entry.path` and writes it to the staging tree. Post-`apply_staging_atomically`, the workspace file's bytes equal `git show <canonical_ref>:<path>` byte-for-byte.

**Verification.** A new regression test `test_alpha_hotfix_2_LLM_accept_canonical_overwrites_workspace_file` in `tests/test_cli_b_shape.py`:
1. Builds a single-commit canonical with a Class-C path (no ancestor history → NN cannot match).
2. Seeds a workspace with different content for the same path.
3. Stubs the resolver factory to return a `MergeVerdict(resolution="inferred-accept-canonical", confidence=1.0, rationale="test")`.
4. Runs `cli.main` with `--auto-accept`.
5. Asserts `Path.read_bytes()` of the workspace file equals `git show HEAD:<path>`.
6. Asserts `state.yaml` advances to SUCCESS (post-apply restamp).

### AC.α-hotfix-2.2 — Class-B ACCEPT_UPSTREAM paths overwrite workspace files (Bug B)

**Outcome.** When the merge_helper's Class-B branch resolves to `Resolution.ACCEPT_UPSTREAM`, `cli.py`'s post-resolve loop reads canonical's HEAD content for `entry.path` and writes it to the staging tree. Post-`apply_staging_atomically`, the workspace file's bytes equal canonical's HEAD blob byte-for-byte.

**Verification.** A new regression test `test_alpha_hotfix_2_class_B_accept_upstream_overwrites_workspace_file` in `tests/test_cli_b_shape.py`. Because the natural conflict_detection flow does not produce a Class-B path with a `change_kind` that triggers `ACCEPT_UPSTREAM` (the kinds the helper checks against route to KEEP_LOCAL), the test uses `monkeypatch` to replace `detect_b_shape_conflicts` with a stub returning a `ConflictReport` containing one Class-B PENDING entry with `change_kind=LOCAL_MODIFIED_EQUALS_UPSTREAM`. The merge_helper's Class-B branch then resolves to `ACCEPT_UPSTREAM`. The CLI's post-resolve loop must stage canonical's content. Assertion: workspace file bytes == canonical HEAD blob.

### AC.α-hotfix-2.3 — ConflictEntry validator gates resolved_content_path on accept-canonical-flavored resolutions (Bug C)

**Outcome.** Constructing or loading a `ConflictEntry` with `resolution=Resolution.INFERRED_ACCEPT_CANONICAL` and `resolved_content_path=None` raises `ValueError` (via Pydantic ValidationError). Same for `Resolution.ACCEPT_UPSTREAM`. The existing rules for `INFERRED_MERGED` and `THREE_WAY_MERGE` continue to hold; `INFERRED_ACCEPT_WORKSPACE` and `KEEP_LOCAL` remain ungated (correctly — workspace already holds the content).

**Verification.** Two new tests in `tests/test_conflict_report_b_shape.py`:
- `test_alpha_hotfix_2_inferred_accept_canonical_requires_resolved_content_path`
- `test_alpha_hotfix_2_accept_upstream_requires_resolved_content_path`

Both construct an entry with the bug shape and assert `pytest.raises(ValueError, match="resolved_content_path")`.

Backwards-compat: any pre-existing test fixture or audit YAML with the bug shape now fails to validate. Mechanical fixture updates apply (set `resolved_content_path="<path>"` to satisfy the contract). Pre-existing on-disk audit YAMLs in operator workspaces with the bug shape will fail to load via `load_conflict_report` — desirable, surfaces the bug class.

### AC.α-hotfix-2.4 — state.yaml does not advance to SUCCESS unless apply completes (Bug D)

**Outcome.** When `resolve_inferred_conflicts` completes cleanly (no halt, no pending) but `apply_staging_atomically` does NOT run (e.g., dry-run, --auto-accept floor not met → CLI discards staging), `state.yaml` shows `status=needs-apply` (a new SyncStatus value), NOT `status=success`. The idempotency fast-path (`_ref_already_applied`) requires `status is SyncStatus.SUCCESS` and so does NOT short-circuit on a `NEEDS_APPLY` state — re-runs against the same ref re-resolve.

**Verification.** A new regression test `test_alpha_hotfix_2_discard_path_does_not_advance_state_to_success` in `tests/test_cli_b_shape.py`:
1. Builds a canonical + workspace with one Class-C path that goes through LLM resolution at low confidence (stubbed resolver returns confidence=0.5).
2. Runs `cli.main` with `--auto-accept --confidence-floor 0.85` → confirm-or-discard returns False → CLI calls `discard_staging`.
3. Reads `state.yaml` and asserts `state.status is SyncStatus.NEEDS_APPLY` (NOT SUCCESS).
4. Bonus assertion: invokes `cli.main` again with the same args → CLI does NOT print "already applied" (i.e., does not short-circuit on idempotency).

### AC.α-hotfix-2.S — Seal-diff invariant

**Outcome.** `git diff --name-only BASELINE..SEAL_COMMIT` produces only paths under the allowed amendment surfaces:
- `workspace-sync/` (the bug-fix sites + new regression tests + sidecar SEAL_COMMIT bump + `seals/SEAL_COMMIT.alpha-hotfix-2` narrative).
- `docs/rebuild/plans/` (plan-doc + builder-plan + manifest, per universal-paths admission).
- `CLAUDE.md` / `docs/odd-*.md` / `docs/rebuild/FUTURE_IDEAS.md` (universal-paths file admission; expected to be untouched but admissible if surfaced).

**Verification.** `tests/test_no_sealed_amendments.py::test_B20_only_workspace_sync_surfaces_changed` passes against `BASELINE = <amendment-#60 commit's HEAD~1>` and `SEAL_COMMIT = <amendment-#60 seal commit>`.

---

## 5. Behaviour-count check (ODD §3.3 forward; applied as dev-discipline check)

Enumeration of branches added/touched against ACs:

| Branch / surface | AC |
|---|---|
| `merge_helper.py` rename `_stage_canonical_for_nn_match` → `stage_canonical_at_ref` (public) | AC.α-hotfix-2.1 + .2 |
| `merge_helper.py` line 786 SUCCESS → NEEDS_APPLY | AC.α-hotfix-2.4 |
| `state.py` new SyncStatus.NEEDS_APPLY enum value | AC.α-hotfix-2.4 |
| `cli.py` post-resolve loop replaced (lines 268-278) — explicit per-resolution staging with halt-on-failure | AC.α-hotfix-2.1 + .2 |
| `conflict_report.py` validator extension (INFERRED_ACCEPT_CANONICAL + ACCEPT_UPSTREAM gate) | AC.α-hotfix-2.3 |
| `tests/test_cli_b_shape.py` 3 new tests (Bug A, B, D) | AC.α-hotfix-2.1, .2, .4 |
| `tests/test_conflict_report_b_shape.py` 2 new tests (Bug C ×2) | AC.α-hotfix-2.3 |
| Pre-existing test fixtures: mechanical updates for tightened validator | (HC#2 backwards-compat; no new AC) |
| `tests/SEAL_COMMIT` sidecar bump | AC.α-hotfix-2.S |
| `tests/test_no_sealed_amendments.py` BASELINE bump | AC.α-hotfix-2.S |

Every branch maps to a named AC. ODD-clean.

---

## 6. Hard constraints

**HC#1.** No edits outside `workspace-sync/`. Plan-doc + manifest + tests + source — purely additive in `workspace-sync/`. (Binding from dispatch.)

**HC#2.** No regression of #56, #57, #58, #59 tests. All 140 existing workspace-sync tests must continue to pass post-hotfix. Some pre-existing fixtures with the bug-shape (null `resolved_content_path` on now-gated resolutions) require mechanical updates to satisfy the tightened validator; intent preserved. (Binding from dispatch.)

**HC#3 (CRITICAL).** Each bug fix has a regression test that asserts file-content-byte-match (or validator-rejection for Bug C) for the relevant code path. Same discipline as α-hotfix #59. (Binding from dispatch.)

**HC#4.** No new third-party deps. Use existing git-shellout machinery + Pydantic + stdlib. (Binding from dispatch.)

---

## 7. Out of scope (explicit)

- **Performance optimisation** of per-entry `git show` shellout. Same out-of-scope as #59.
- **Adding `INFERRED_ACCEPT_WORKSPACE` content-path validation.** The dispatch explicitly notes: "INFERRED_ACCEPT_WORKSPACE does NOT require it (the workspace already has the content; staging is unnecessary)." Same for KEEP_LOCAL. Validator extension covers only the two resolutions that demand staged content.
- **A `pos-sync --re-apply` command** that operates on `NEEDS_APPLY` state. Future amendment if operator UX demands it.
- **Auto-migrating pre-existing audit YAMLs** with the bug shape. Operators with stale audit YAMLs will see a load failure if they re-inspect; that's a desirable surface signal. Migration would be a separate amendment.

---

## 8. Implementation order

1. Author plan-doc + builder-plan + manifest (this amendment cycle's prep).
2. Run `pos-amend apply --plan <manifest>` to bump BASELINE + sidecar + widen bindings.
3. Edit source files in dependency order: state.py (enum) → merge_helper.py (rename + state-write change) → conflict_report.py (validator) → cli.py (post-resolve loop replacement).
4. Run smoke tests; mechanically fix pre-existing fixtures broken by validator tightening.
5. Add new regression tests (5 total).
6. Re-run smoke pass until all green.
7. Commit the amendment with the structured commit prose.
8. `pos-amend seal --plan-doc <plan-doc-abs-path> --scoped-sweep <manifest>`.
9. Backfill plan §14 + §15.

---

## 9. Bookkeeping surface (per-AC plan-doc convention)

- **AC.α-hotfix-2.1** — verified by `test_alpha_hotfix_2_LLM_accept_canonical_overwrites_workspace_file`.
- **AC.α-hotfix-2.2** — verified by `test_alpha_hotfix_2_class_B_accept_upstream_overwrites_workspace_file`.
- **AC.α-hotfix-2.3** — verified by 2 tests in `test_conflict_report_b_shape.py`.
- **AC.α-hotfix-2.4** — verified by `test_alpha_hotfix_2_discard_path_does_not_advance_state_to_success`.
- **AC.α-hotfix-2.S** — verified by `tests/test_no_sealed_amendments.py::test_B20_only_workspace_sync_surfaces_changed`.

---

## 10. Halt triggers (builder halts + signals owner)

Per dispatch:

1. **Centralizing the staging contract requires touching the resolver Protocol.** Pre-build verification: `MergeResolver` ABC's contract is `.resolve(...) -> MergeVerdict`. Staging is downstream of the verdict. **Trigger does NOT fire.** Builder proceeds.
2. **Bug D fix collides with merge_helper PARTIAL/SUCCESS state-write convention** (cli.py:335 comment). Pre-build verification: post-fix, the helper writes `NEEDS_APPLY` (not SUCCESS) on clean resolve; cli.py post-apply remains the authoritative SUCCESS writer. Convention preserved. **Trigger does NOT fire.**
3. **Wall-time exceeds 3-4h projection.** Halt if exceeded. Pre-build estimate: ~2-3h.

---

## 11. Decisions remaining for the owner to rule on

None for the named scope. The fix shapes are bounded by the existing primitives (`git show <ref>:<path>` shellout pattern, `write_merged` callable, `ConflictEntry` Pydantic validator, `SyncStatus` enum).

---

## 12. Summary of named decisions (owner-readable)

1. **Centralize the staging primitive** (`_stage_canonical_for_nn_match` → `stage_canonical_at_ref`). Recommended. Single point for all accept-canonical-flavored verdicts to stage canonical content; closes Bug A + Bug B with one call site each in cli.py.
2. **Halt-on-stage-failure in cli.py post-resolve loop.** Recommended. Unlike the merge_helper's NN branches (which can leave PENDING for the legacy resolver path to handle), cli.py runs AFTER the resolver helper — there's no fallback. Failing closed (discard staging, exit 2) is the correct response.
3. **New SyncStatus.NEEDS_APPLY enum value** (Bug D). Recommended over reusing PARTIAL. Semantic clarity: PARTIAL means "some conflicts pending"; NEEDS_APPLY means "resolved cleanly but apply not run".
4. **Validator gates INFERRED_ACCEPT_CANONICAL + ACCEPT_UPSTREAM only** (Bug C). Recommended. INFERRED_ACCEPT_WORKSPACE and KEEP_LOCAL correctly remain ungated (workspace already has the content; staging is unnecessary). Mirrors the dispatch's explicit guidance.
5. **Single amendment for all 4 bugs.** Recommended. Same fault-class; centralized fix touches 4 files (~150 LOC); 5 regression tests; coherent sealed-component dispatch.

---

## 13. Halt-and-surface findings encountered during plan authoring

None — the dispatch enumerates the four bugs explicitly, the fix shape is bounded by existing primitives, and pre-build verification of the two named halt triggers confirms neither fires. If any halt-trigger fires during build, builder halts and surfaces.

---

## 14. Method-decision record (builder, post-build)

### α-hotfix-2 — Amendment #60 record

#### D-build.x for α-hotfix-2

- **D-build.A — staging primitive centralization.** Renamed
  `_stage_canonical_for_nn_match` (private; added in #59) →
  `stage_canonical_at_ref` (public; same signature). The two NN
  call sites in `merge_helper.py` (cache-hit + cache-miss branches)
  were updated mechanically to use the new name. `cli.py` imports
  the public function and invokes it from the post-resolve loop
  for both `INFERRED_ACCEPT_CANONICAL` (when `resolved_content_path`
  is None — NN entries already have it set) and `ACCEPT_UPSTREAM`
  (Class-B). Halt-on-failure: `cli.py` runs AFTER the resolver
  helper finished — no fallback path — so a False return from
  `stage_canonical_at_ref` triggers `discard_staging` + exit 2.
  Net delta in cli.py: +79 / -10 LOC (replaced the buggy `pass`
  and `clean_writes.append` with explicit per-resolution staging
  blocks, both with structured halt-and-surface diagnostics).

- **D-build.B — validator extension.** Extended the existing
  `_resolution_requires` model_validator in
  `conflict_report.py`. Two new gates, one inside the
  `INFERRED_RESOLUTIONS` branch (for `INFERRED_ACCEPT_CANONICAL`)
  and one outside it (for `ACCEPT_UPSTREAM`, which is not an
  inferred resolution and so does not have rationale/confidence
  requirements). Net delta: +29 LOC (validator gates +
  documentation comments). The `INFERRED_ACCEPT_WORKSPACE` +
  `KEEP_LOCAL` resolutions remain ungated as planned.

- **D-build.C — `SyncStatus.NEEDS_APPLY`.** Added the new enum
  value to `state.py`. Updated `merge_helper.py` line 786 from
  `status = SyncStatus.SUCCESS` → `status = SyncStatus.NEEDS_APPLY`
  on clean-resolve in the finally block. `cli.py` post-apply
  remains the authoritative SUCCESS writer (line 337 unchanged).
  The `_ref_already_applied` idempotency check in `cli.py`
  requires `state.status is SyncStatus.SUCCESS`, so
  `NEEDS_APPLY` correctly does NOT short-circuit re-runs after
  a discarded staging.

- **D-build.D — fixture mechanical updates.** Three pre-existing
  tests broke under the tightened validator:
  1. `test_conflict_report_b_shape.py::test_sorted_low_confidence_first`
     — three `_entry()` calls with `INFERRED_ACCEPT_CANONICAL` and
     null `resolved_content_path`. Updated to supply
     `resolved_content_path="/tmp/staging/<path>"`.
  2. `test_merge_helper.py::test_class_c_invokes_resolver_writes_audit`
     — assertion `state.status is SyncStatus.SUCCESS` updated to
     `state.status is SyncStatus.NEEDS_APPLY` (the test calls
     `resolve_inferred_conflicts` directly with no CLI apply, so
     `NEEDS_APPLY` is now the correct terminal status).
  3. `test_merge_helper.py::test_check_inferred_resolution_invariants_pass`
     — the `_entry()` factory was extended to inject a placeholder
     `resolved_content_path` for resolutions that now require it
     (intent: the factory's job is shape-correctness; null content
     paths are the bug shape the validator now refuses).

  All three updates preserve the original test intent (verdict-shape
  correctness; status-after-resolve correctness).

#### Test breakdown

Six new tests (post-hotfix workspace-sync total: 146; pre-hotfix: 140):

- `tests/test_cli_b_shape.py::test_alpha_hotfix_2_LLM_accept_canonical_overwrites_workspace_file`
  (Bug A; HC#3 file-content-byte-match assertion).
- `tests/test_cli_b_shape.py::test_alpha_hotfix_2_class_B_accept_upstream_overwrites_workspace_file`
  (Bug B; HC#3 file-content-byte-match assertion).
- `tests/test_cli_b_shape.py::test_alpha_hotfix_2_discard_path_does_not_advance_state_to_success`
  (Bug D; state-status assertion + bonus re-run-no-short-circuit
  assertion).
- `tests/test_conflict_report_b_shape.py::test_alpha_hotfix_2_inferred_accept_canonical_requires_resolved_content_path`
  (Bug C; validator-rejection assertion).
- `tests/test_conflict_report_b_shape.py::test_alpha_hotfix_2_accept_upstream_requires_resolved_content_path`
  (Bug C; validator-rejection assertion).
- `tests/test_conflict_report_b_shape.py::test_alpha_hotfix_2_inferred_accept_workspace_remains_ungated`
  (Bug C; explicit out-of-scope check — `INFERRED_ACCEPT_WORKSPACE`
  with null `resolved_content_path` correctly constructs without
  error).

### Commit SHAs

- Amendment commit: `8bae39ab2303bc655387db6ec89f59ea9826e057` —
  `feat(workspace-sync): α-hotfix-2 — close 4 correctness bugs of the verdict-without-stage class (amendment #60, AC.α-hotfix-2.1–.4 + AC.α-hotfix-2.S)`
- Seal commit: `7452b201645895bbd3b746319f24340cf0c9864a` —
  `chore(seals): workspace-sync — α-hotfix-2: close 4 correctness bugs of the verdict-without-stage class — workspace-sync at 8bae39a`
## 15. Backwards-compat verification

- **All 140 pre-existing workspace-sync tests pass post-hotfix.**
  Three pre-existing tests required mechanical fixture updates to
  satisfy the tightened validator (D-build.D); intent preserved.
- **Post-hotfix workspace-sync total: 146 tests** (+6 new).
- **HC#1 (no edits outside workspace-sync/) verified.** Seal-diff
  test `tests/test_no_sealed_amendments.py::test_B20_only_workspace_sync_surfaces_changed`
  passes against `BASELINE = 8083a02` and
  `SEAL_COMMIT = 7452b20`. Only `workspace-sync/` and
  `docs/rebuild/plans/` (universal-paths admission) paths in the
  diff.
- **HC#2 (no #56/57/58/59 regression) verified.** The α.1 NN
  ancestor-detection path (#57 / #59) is unchanged; the
  `INFERRED_MERGED` write_merged path is unchanged; Class-A
  protection is unchanged; β.1 (#58) canonical-source resolution
  is unchanged.
- **HC#3 (regression tests assert byte-match / structural-rejection)
  verified.** Bug A, Bug B tests use `Path.read_bytes()` against
  `git show <ref>:<path>` byte-for-byte. Bug D test asserts
  `state.status is not SyncStatus.SUCCESS` plus a bonus re-run-
  no-short-circuit assertion. Bug C tests use
  `pytest.raises(ValueError, match="resolved_content_path")`.
- **HC#4 (no new third-party deps) verified.** `git diff
  workspace-sync/uv.lock` is empty under this amendment.
- **Speedups applied.**
  - (a) Scoped-sweep seal: `pos-amend seal --scoped-sweep` ran
    only the workspace-sync component's seal-diff test, not all
    sealed components.
  - (b) Pre-seal smoke: workspace-sync tests passed (146/146)
    before commit; full repo-wide pytest skipped pre-seal per
    speedup (b).
  - (c) Inline methodology snippets in commit prose: the
    amendment-commit message above includes structured
    Bug A/B/C/D + D-build.A/B/C/D snippets verbatim from this
    plan-doc rather than referencing them externally.
