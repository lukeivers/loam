# workspace-sync — α hotfix: NN-resolved entries actually overwrite workspace files — plan

Sealed-component amendment extending the existing `workspace-sync/`
component. Critical bug-fix on Bundle α (#57) — the NN ancestor-
detection accept-canonical fast-path sets the verdict but never
stages canonical's content, so the downstream apply silently no-ops
on every NN-resolved path. Workspace files stay at pre-apply state
while `state.yaml` advances to "applied" — false-success.

**Status:** plan (pre-dispatch). 2026-04-27.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`
**Companions:**
- **#57 plan-doc** (Bundle α — introduced the NN ancestor-detection fast-path that this hotfix repairs): `docs/plans/workspace-sync-resolver-cost-overhaul.md`
- **#56 plan-doc** (workspace-sync keystone — defines the stage-then-apply envelope this fix preserves): `docs/plans/workspace-sync.md`
- **`workspace-sync/src/workspace_sync/merge_helper.py`** — the buggy module; both NN branches (cached at lines 438-447 and cache-miss at 495-504) set the verdict but skip `write_merged`.
- **`workspace-sync/src/workspace_sync/staging.py`** — the apply-pipeline that walks the staging tree; never observes NN-resolved paths because they are never staged.
- **`workspace-sync/src/workspace_sync/cli.py`** — the orchestrator that wires `_write_merged_to_staging` as the `write_merged` sink for `resolve_inferred_conflicts`; `apply_staging_atomically` walks every file under `staging_path` post-resolution.

**Ancestor record:**
- **#56 (workspace-sync keystone) sealed `0607dc7`** — established the stage-then-atomic-apply envelope. NN-resolved paths did not exist yet; the bug landed when α.1 introduced the ancestor-detection fast-path that bypassed `write_merged`.
- **#57 (Bundle α) sealed `e619b6a`** — added the NN fast-path (lines 438-447 + 495-504 in `merge_helper.py`). 101 tests at seal time covered verdict-shape correctness; none verified file-content-on-disk after `apply_staging_atomically` for an NN-resolved entry. Bundle α's "milestone closed" claim was a calibration miss.
- **#58 (Bundle β.1 ergonomics) sealed `6860e4d`** — landed `pos-sync` no-args + workspace-local `.pos/sync-config.yaml`. β.1 did not edit `merge_helper.py` (HC#1 of #58 explicitly excluded it); the bug carried forward.
- **Direct empirical reproduction (2026-04-27).** `pos-sync --workspace /Users/lukeivers/pos3 --auto-accept --confidence-floor 0.85` against canonical at `44d470d`. Output reports `applied: <ref>`; `state.yaml` advances; audit shows 46 NN-resolved entries with `resolved_content_path: null`. Workspace files (e.g., pos3's `primary-persona/src/__init__.py`) DO NOT match canonical's HEAD blob byte-for-byte. False-success confirmed.

**Research:** No new research dispatched — the bug is fully observed and reproducible against pos3, and the fix shape is bounded by the existing `write_merged` callable already wired through `resolve_inferred_conflicts` (the same sink the LLM-resolver `INFERRED_MERGED` path uses). No method-choice surface remains uncertain.


---

## 1. Summary / TLDR

One observable: NN-resolved paths that match a canonical-history ancestor must, post-apply, contain canonical's HEAD content byte-for-byte. The current implementation sets the verdict (`Resolution.INFERRED_ACCEPT_CANONICAL`) but never populates the staging tree with canonical's HEAD content for those paths. `apply_staging_atomically` walks `staging_path/`, and an NN-resolved path is missing → no `os.replace` runs → workspace file untouched while `state.yaml` advances to "applied".

**The fix.** In both NN branches (cache-hit at line 438-447 and cache-miss at 495-504), after setting `entry.resolution = Resolution.INFERRED_ACCEPT_CANONICAL`, read canonical's HEAD content for the path via `git show <canonical_ref>:<entry.path>` against `canonical_root` and call the `write_merged` callable to drop it into staging. Capture the returned absolute path on `entry.resolved_content_path`. The downstream apply then picks the file up via the existing `staging.py` machinery, untouched.

**Critical regression test.** A new test in `tests/test_cli_b_shape.py` (or a new sibling fixture file) that:
1. Sets up a synthetic workspace whose content matches a canonical-ancestor blob (the empirical case).
2. Runs `pos-sync` against it with `--auto-accept`.
3. **Asserts post-apply that the workspace file's actual byte content matches canonical's HEAD blob byte-for-byte.** Not just verdict-shape; not just `state.yaml`; **actual file content match.**

The test is the binding artefact. Without it, future amendments could re-introduce the same shape of bug while passing every `verdict-shape` assertion.

**Hard Constraint #1 (binding from dispatch).** No edits outside `workspace-sync/`. The fix is purely additive in `merge_helper.py` (NN's branches only) + a new test. Manifest + plan-doc add via universal-paths only.

**Hard Constraint #4 (binding from dispatch).** The regression test MUST verify file-content-on-disk, not just verdict-shape.

**Bundle splitting / ordering.** Single-AC hotfix. Lands as **amendment #59** (next free after #58). Same-tree-serialize against any other in-flight amendment work.

**This is sealed-component scope.** workspace-sync/ is the only fence touched; plan + builder-plan + manifest land per the dev CDC. No new top-level objective.


---

## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)

This amendment composes under **VALUE_PROPOSITION's AC.PO.1 (translation-burden absorption)** — the prime objective per CLAUDE.md §2.5. The bug breaks AC.PO.1: when the operator says "pull the latest", the persona translates to `pos-sync`, the CLI reports success, and the workspace files stay stale. The translation is *broken at the substrate*. **No new top-level objective.** Halt trigger 1 evaluated: does not fire.

**Reverse trace per CLAUDE.md §2.5.**

- **AC.PO.1 (translation-burden):** The NN fast-path's whole purpose is to make "pull the latest" work without LLM cost on the easy cases (workspace content matches a canonical-history blob → just take canonical's HEAD). Today the fast-path *says* "accept canonical" and *does not actually accept canonical*. Post-hotfix, the NN fast-path produces the observable the operator intends.

- **AC.PO.2 (toolkit-primitive growth):** The `write_merged` sink already exists in `cli.py` (`_write_merged_to_staging`); it is the canonical primitive for "drop content into staging at this path". The hotfix wires the NN branches into it. No new primitive; no new export. The fix tightens the implementation to use the existing primitive correctly.


---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude leverage

This is a substrate-level correctness fix; no new Claude-native primitives are leaned on or composed against. The α.1 ancestor-detection fast-path itself is a Claude-cost-avoidance primitive (it sidesteps the LLM resolver when canonical's history already contains the workspace's blob); the hotfix preserves and completes that primitive. No Claude-side capability surface changes.

### Lens 2 — Harness + primary-persona value

**Primary-persona test (translation burden):** The hotfix is a binary correctness gate on the most common sync path. Pre-hotfix the persona's translation of "pull the latest" silently fails on every NN-matched path. Post-hotfix it succeeds. **Reduces translation burden absolutely** (from "broken" to "works").

**Harness test (toolkit growth):** Composes on the existing `write_merged` sink without adding a new primitive. The harness gains *correctness*, not *new primitives*; this is a small but binding gain. The regression test additionally adds a *new test primitive* (file-content-on-disk byte-match assertion against canonical's HEAD blob) that future workspace-sync amendments can compose against to detect the same shape of bug.

### Lens 3 — ODD authoring

Single AC (AC.α-hotfix.1). Outcome-shape only: NN-resolved paths actually overwrite workspace files with canonical's HEAD content; verified by file-content-byte-match test. Plus AC.α-hotfix.S seal-diff invariant. Method-shape (which subprocess argv, which exact line to insert the staging call, which test file the new test lives in) is the builder's call inside the AC's outcome bound.


---

## 4. Acceptance criteria (AC.α-hotfix.x — single-AC hotfix)

### AC.α-hotfix.1 — NN-resolved paths overwrite workspace files with canonical's HEAD content

**Outcome.** When `resolve_inferred_conflicts` resolves an entry to `Resolution.INFERRED_ACCEPT_CANONICAL` via the α.1 NN ancestor-detection fast-path (either cache-hit or cache-miss branch), the staging tree carries canonical's HEAD content for that path before `apply_staging_atomically` runs. Post-apply, the workspace file's bytes equal `git show <canonical_ref>:<path>` byte-for-byte.

**Verification.**

- A new regression test asserts file-content-on-disk byte-match for an NN-resolved entry post-`pos-sync --auto-accept`. The test sets up a synthetic workspace whose content matches a canonical-ancestor blob (using a real two-commit canonical with a known ancestor), runs the CLI, and reads the workspace file post-apply with `Path.read_bytes()` compared to `subprocess.run(["git", "show", f"{ref}:<path>"], cwd=canonical_root).stdout`.
- The `state.yaml` advances to `applied`/`success` only after the staging actually populated; the existing state-write semantics are unchanged.
- All 139 existing workspace-sync tests continue to pass.

**Out of scope (HALT-FOUND surface — not closed by this AC).** The dispatch's named scope is the NN branches in `merge_helper.py`. Two related gaps are surfaced in §13 below for owner ruling on a follow-on amendment; neither is closed by AC.α-hotfix.1.

### AC.α-hotfix.S — Seal-diff invariant

**Outcome.** `git diff --name-only BASELINE..SEAL_COMMIT` produces only paths under the allowed amendment surfaces:
- `workspace-sync/` (the bug-fix site + new regression test + sidecar SEAL_COMMIT bump + `seals/SEAL_COMMIT.alpha-hotfix` narrative).
- `docs/plans/` (plan-doc + builder-plan + manifest, per universal-paths admission).
- `CLAUDE.md` / `docs/odd-*.md` / `docs/FUTURE_IDEAS.md` (universal-paths file admission; expected to be untouched but admissible if surfaced).

**Verification.** `tests/test_no_sealed_amendments.py::test_B20_only_workspace_sync_surfaces_changed` passes against `BASELINE = <amendment-#59 commit's HEAD~1>` and `SEAL_COMMIT = <amendment-#59 seal commit>`.


---

## 5. Behaviour-count check (ODD §3.3 forward; applied as dev-discipline check)

The fix surface is small; an enumeration of branches added/touched against ACs:

| Branch / surface | AC |
|---|---|
| `merge_helper.py` cache-hit NN branch (438-447) — adds a `write_merged` call after setting verdict | AC.α-hotfix.1 |
| `merge_helper.py` cache-miss NN branch (495-504) — same shape | AC.α-hotfix.1 |
| New helper `_read_canonical_blob(canonical_root, ref, path) -> str` (or inline subprocess call) — reads `git show <ref>:<path>` | AC.α-hotfix.1 |
| New regression test in `tests/test_cli_b_shape.py` (or new file) — file-content-byte-match assertion | AC.α-hotfix.1 |
| Sidecar bump `tests/SEAL_COMMIT` → amendment-#59 commit SHA via `pos-amend apply` | AC.α-hotfix.S |
| `tests/test_no_sealed_amendments.py` BASELINE bumped to amendment-#59 HEAD~1 via `pos-amend apply` | AC.α-hotfix.S |

Every branch maps to a named AC. ODD-clean.


---

## 6. Hard constraints

**HC#1.** No edits outside `workspace-sync/`. The fix is purely additive in `merge_helper.py` + a new test. Manifest + plan-doc add via universal-paths only. (Binding from dispatch.)

**HC#2.** No regression of #56 or #57 tests. All 139 existing workspace-sync tests must continue to pass post-hotfix. (Composes from dispatch's HC#2 + HC#3.)

**HC#3.** No regression of β.1's tests; the workspace-sync total post-hotfix grows from 139 to 140-141 (one or two new tests). (Composes from dispatch's HC#3.)

**HC#4 (CRITICAL).** The regression test MUST verify file-content-on-disk via `Path.read_bytes()`, not just verdict-shape, not just `state.yaml`. The fix is incomplete without it. (Binding from dispatch.)

**HC#5.** No new third-party deps. Use existing git-shellout machinery (`subprocess.run(["git", "-C", str(canonical_path), "show", f"{ref}:{path}"])` is already the shape used by `_resolve_canonical_head_sha` in `merge_helper.py` and `_git_show_bytes` in `conflict_detection.py`). (Binding from dispatch.)


---

## 7. Out of scope (explicit)

- **The cli.py:271-274 `pass` branch for `INFERRED_ACCEPT_CANONICAL`.** Surfaced as HALT-FOUND #1 in §13. Not closed by this hotfix.
- **The cli.py:275-278 `clean_writes.append` post-stage append for Class-B `ACCEPT_UPSTREAM`.** Surfaced as HALT-FOUND #2 in §13. Not closed by this hotfix.
- **Tightening the `ConflictEntry` validator to require `resolved_content_path` for `INFERRED_ACCEPT_CANONICAL` (and `THREE_WAY_MERGE` already covered).** Would catch the bug class structurally but lives in `conflict_report.py` (still inside `workspace-sync/`); deferred to follow-on for surface-minimality. Surfaced as HALT-FOUND #3 in §13.
- **Performance optimisation** of the per-NN-entry `git show` shellout. Dispatch acknowledges 46 paths × 1 git show ≈ 200ms is acceptable. Future amendment could batch via `git cat-file --batch` if it becomes a bottleneck.


---

## 8. Implementation order

1. Author plan-doc + builder-plan + manifest (this amendment cycle's prep).
2. Run `pos-amend apply --plan <manifest>` to bump BASELINE + sidecar + widen bindings.
3. Edit `merge_helper.py`: add the staging call to both NN branches (D-build.0 / D-build.1).
4. Add regression test (D-build.2).
5. Run `workspace-sync/tests/` smoke pass via `.venv/bin/python -m pytest workspace-sync/tests/test_merge_helper.py workspace-sync/tests/test_cli_b_shape.py` (speedup b: skip pre-seal full-suite if smoke passes).
6. Commit the amendment with the structured commit prose (D-build.3).
7. `pos-amend seal --plan-doc <plan-doc-abs-path> --scoped-sweep <manifest>` (speedup a: scoped sweep limits cross-component sweep to workspace-sync only).
8. Backfill plan §14 + §15 with method choices, test breakdown, and commit SHAs (per AC.D-sa.7 — `pos-amend seal --plan-doc` automates this).


---

## 9. Bookkeeping surface (per-AC plan-doc convention)

- **AC.α-hotfix.1** — verified by file-content-byte-match regression test (named in §14 D-build.2 post-build).
- **AC.α-hotfix.S** — verified by `tests/test_no_sealed_amendments.py::test_B20_only_workspace_sync_surfaces_changed` against the post-amendment seal SHA.


---

## 10. Halt triggers (builder halts + signals owner)

The dispatch enumerates the halt triggers; restated here for in-plan reference:

1. **The fix exposes another correctness gap I haven't named** (e.g., the verifier-passes path also doesn't stage content; need to check). **FIRED at plan time** — see §13 HALT-FOUND #1, #2, #3. Builder does NOT silently extend; the additional surface is documented in §13 for the owner to rule on a follow-on amendment.
2. Reading canonical's HEAD content via git shellout has performance issues at scale (46 paths × 1 git show each = ~200ms; acceptable). Not fired.
3. The regression test setup is harder than expected (synthetic workspace + canonical with ancestor-match needs a fixture). Halt if can't author cleanly within plan §10 wall-time. Not fired (the existing `tests/conftest.py` has fixture machinery; D-build.2 reuses).
4. Wall-time exceeds 2-3h projection (this is a small bug fix, not a feature). Not fired pre-build.


---

## 11. Decisions remaining for the owner to rule on

None for the named scope (NN branches in `merge_helper.py`). The fix shape is bounded by the existing `write_merged` callable already wired through `resolve_inferred_conflicts`, the existing `subprocess.run(["git", "-C", ...])` shellout pattern in `merge_helper.py`, and the existing test fixture machinery in `tests/conftest.py`.

**For follow-on amendment (HALT-FOUND in §13):** owner ruling needed on whether to land the cli.py:271-274 + cli.py:275-278 fixes as a separate amendment #60 (recommended) or fold them into a wider hotfix that grows this amendment's surface (not recommended — surface drift).


---

## 12. Summary of named decisions (owner-readable)

1. **Single AC, NN-only scope.** Recommended. Matches the dispatch's named scope; minimal seal-diff surface; preserves "small fix, fast turnaround" character of the hotfix.
2. **HALT-FOUND surface in §13** — surfaces three related correctness gaps not closed by this amendment. **Recommendation:** owner rules on follow-on amendment #60 to close HALT-FOUND #1 + #2 (cli.py:271-274 + 275-278); HALT-FOUND #3 (validator tightening) is doc-only / structural and can ride along.


---

## 13. Halt-and-surface findings encountered during plan authoring

### HALT-FOUND #1 (cli.py:271-274) — `INFERRED_ACCEPT_CANONICAL` from the LLM resolver itself is also unstaged.

**Observation.** `cli.py:271-274` reads:

```python
if entry.resolution is Resolution.INFERRED_ACCEPT_CANONICAL:
    # Resolver said "accept canonical" — clean-writes path
    # already staged the canonical; do nothing extra.
    pass
```

The comment is **wrong**. `clean_writes` is the list of paths the conflict-detector classified as canonical-clean writes (no conflict). Any path that became a conflict + was resolved to `INFERRED_ACCEPT_CANONICAL` was *not* in `clean_writes`. The "do nothing extra" path is broken.

**This bug is independent of NN ancestor-detection.** The α.1 NN fast-path is one source of `INFERRED_ACCEPT_CANONICAL` verdicts; the LLM-resolver returning `inferred-accept-canonical` (not `inferred-merged`) is another. Both end up at this `pass` branch.

**Why the named-scope hotfix accidentally fixes this.** The named-scope fix sets `entry.resolved_content_path` in the NN branches via `write_merged`, which writes to `staging_path/<entry.path>`. `apply_staging_atomically` walks the staging tree and applies every file there — it does not consult `entry.resolved_content_path`. So as long as *some* path populates the staging tree, the apply works.

The LLM-resolver path that returns `inferred-accept-canonical` (not `inferred-merged`) does NOT call `write_merged` (the cli.py:271 `pass` is the only branch that handles it post-resolution). So the LLM-resolver `inferred-accept-canonical` path remains broken post-this-hotfix.

**Recommendation.** Land a follow-on amendment #60 that either (a) makes cli.py:271 explicitly stage canonical's content for `INFERRED_ACCEPT_CANONICAL` entries (mirroring what the named-scope fix does in `merge_helper.py` for NN branches), or (b) moves the staging call into the merge_helper for *all* `INFERRED_ACCEPT_CANONICAL` resolutions (including LLM-returned ones). Option (b) centralises the staging contract; option (a) keeps the cli.py orchestration explicit. **Plan-author recommends option (b).**

### HALT-FOUND #2 (cli.py:275-278) — Class-B `ACCEPT_UPSTREAM` path does post-stage `clean_writes.append` that never restages.

**Observation.** `cli.py:275-278` reads:

```python
elif entry.resolution is Resolution.ACCEPT_UPSTREAM:
    # Class-B operator-prefers-canonical branch. Stage
    # canonical content explicitly.
    clean_writes.append(entry.path)
```

This append happens AFTER `stage_canonical_clean_writes` has already run (line 241). Appending to `clean_writes` post-stage does *nothing*; `clean_writes` is a list, not a reactive subscription. Class-B `ACCEPT_UPSTREAM` entries never have their canonical content staged, so `apply_staging_atomically` never overwrites the workspace file.

**Probable empirical visibility.** Less common than NN because Class-B `ACCEPT_UPSTREAM` requires the file to be both in the Class-B set (per `sync_protected.yaml`) AND not workspace-modified. Most Class-B paths in pos3 are Class-B-with-modifications, which take the `KEEP_LOCAL` branch (correctly).

**Recommendation.** Same follow-on amendment #60. Either re-call `stage_canonical_clean_writes` with the appended paths, or call `stage_canonical_clean_writes(..., paths_to_apply=[entry.path])` directly per Class-B `ACCEPT_UPSTREAM` entry.

### HALT-FOUND #3 (`conflict_report.py` validator) — `ConflictEntry` validator does not require `resolved_content_path` for `INFERRED_ACCEPT_CANONICAL`.

**Observation.** Lines 159-200 of `conflict_report.py`: the model_validator requires `resolved_content_path` only for `THREE_WAY_MERGE` and `INFERRED_MERGED`. `INFERRED_ACCEPT_CANONICAL` and `INFERRED_ACCEPT_WORKSPACE` are not gated.

**Why the validator gap allowed the bug.** The NN branches in `merge_helper.py` set the verdict and skip `resolved_content_path`; the validator accepts the entry; the audit YAML records `resolved_content_path: null`; the apply step finds nothing to copy; false-success ships.

**Recommendation.** Tighten the validator in the same follow-on amendment #60: `INFERRED_ACCEPT_CANONICAL` requires `resolved_content_path` (mirroring the contract `INFERRED_MERGED` already has). `INFERRED_ACCEPT_WORKSPACE` does NOT require it (the workspace already has the content; staging is unnecessary; `apply_staging_atomically` correctly does nothing for those entries because they aren't staged).

**Why not in this amendment?** HC#1 binds the surface to `merge_helper.py` + a new test (named scope). The validator change in `conflict_report.py` is inside `workspace-sync/` (so HC#1 doesn't strictly bind it) but expanding the surface beyond the dispatch's named scope is a deviation; the build-time halt is the right surface for that decision, not this plan-doc.

### Halt-trigger surface review (per plan §10)

- **#1 (other correctness gap exposed):** FIRED — three findings above. Not silently extended; surfaced for owner ruling.
- **#2 (performance):** not fired.
- **#3 (test setup harder than expected):** not fired pre-build.
- **#4 (wall-time):** not fired pre-build (~1h projection).


---

## 14. Method-decision record (builder, post-build)

(Backfilled by build agent post-implementation.)

### α-hotfix — Amendment #59 record

#### D-build.x for α-hotfix

(To be filled in post-build with the actual method choices made.)

#### Test breakdown

(To be filled in post-build with the actual test count and names.)

### Commit SHAs

- Amendment commit: `f5190b645f37b871a0fb95fb3b85e90f3672b2f2` —
  `feat(workspace-sync): α-hotfix — NN-resolved entries actually overwrite workspace files (amendment #59, AC.α-hotfix.1 + AC.α-hotfix.S)`
- Seal commit: `f1abded6b0799d840385c9951d8600f92d580516` —
  `chore(seals): workspace-sync — α-hotfix: NN-resolved entries actually overwrite workspace files — workspace-sync at f5190b6`
## 15. Backwards-compat verification

(Backfilled post-build with concrete numbers.)
