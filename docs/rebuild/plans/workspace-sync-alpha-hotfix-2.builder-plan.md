# workspace-sync α-hotfix-2 — builder-plan

**Authored:** 2026-04-26 by primary persona (α-hotfix-2 sealed-component amendment dispatch).
**Companion plan:** `docs/rebuild/plans/workspace-sync-alpha-hotfix-2.md` (§1-§5 + AC.α-hotfix-2.1–.4 + AC.α-hotfix-2.S).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Pre-amendment baseline (BASELINE candidate):** `8083a029034a0d69aafa7f512df7de2b667c2369` — current HEAD at amendment-commit-stage time. Prior amendment was **#59** (α-hotfix, sealed `f1abded`); next free amendment number = **#60**.

This builder-plan captures (a) the **method choices** (D-build.x) within each AC's outcome bound, (b) the **§2.5 reverse-direction trace** (one row per code path / branch → AC), and (c) the **build sequence** the agent will execute.

α-hotfix-2 closes 4 correctness bugs of the same shape as α-hotfix #59: verdict-set-without-content-staged. #59 fixed the NN-resolver branch only (HC#1 named-scope binding). The remaining 3 were surfaced as HALT-FOUND #1, #2, #3 in the #59 plan-doc §13. Bug D (state.yaml hygiene) was caught by primary persona during the post-#59 verification.

---

## Section A — Method choices (D-build.x)

### D-build.A — Centralize the staging contract for ALL accept-canonical-flavored verdicts (Bug A + Bug B)

**Choice.** Promote the `_stage_canonical_for_nn_match` helper in `merge_helper.py` (added by #59) into a more general `_stage_canonical_at_ref` primitive and call it from BOTH:

1. The cli.py post-resolve loop for `INFERRED_ACCEPT_CANONICAL` (closes Bug A).
2. The cli.py post-resolve loop for `ACCEPT_UPSTREAM` (closes Bug B).

The existing `_stage_canonical_for_nn_match` already does exactly the work: read canonical bytes via `git show <ref>:<path>`, decode UTF-8, write to staging via `write_merged` callable, set `entry.resolved_content_path`. Bug A is covered structurally by reusing the same helper for the cli.py:271-274 branch. Bug B is covered by the same helper, called for `ACCEPT_UPSTREAM`.

**Why NOT touch the resolver Protocol.** The dispatch's halt-and-surface trigger asks: "does centralization require touching the resolver Protocol?" Reading the merge_helper's exit invariant (a `MergeVerdict` is returned + entry mutated; resolver call is internal), staging is purely downstream of the verdict. **No resolver Protocol changes needed.** The `MergeResolver` ABC's contract ends at "return a verdict"; staging is the helper's responsibility, not the resolver's.

**Implementation surface.**

- **`merge_helper.py`:** Rename `_stage_canonical_for_nn_match` → `_stage_canonical_at_ref` (semantic broadening; same signature). Or add a thin wrapper if the rename creates churn — simpler: keep the existing function, expose it publicly (move underscore prefix off → `stage_canonical_at_ref`, or just re-export). **Decision:** keep `_stage_canonical_for_nn_match` private to merge_helper; add a NEW public-shaped helper `stage_canonical_at_ref` (no leading underscore) in merge_helper.py that takes the same args and returns a bool. cli.py imports it. The original `_stage_canonical_for_nn_match` becomes a thin `return stage_canonical_at_ref(...)` wrapper to preserve the existing two call sites' signature.

  Actually simpler: just rename the existing private helper to `stage_canonical_at_ref` (drop leading underscore), update the two NN call sites in merge_helper.py, and import it from cli.py. Single rename + two cli.py call sites added. No wrapper.

- **`cli.py`:** In the post-resolve loop (lines 269-278):
  - For `INFERRED_ACCEPT_CANONICAL` entries with `resolved_content_path is None` (the NN-resolved entries already have it set), call `stage_canonical_at_ref(...)`. If it fails, raise — the verdict is already sealed; we cannot leave the file unstaged or the bug ships.
  - For `ACCEPT_UPSTREAM` entries (Class-B), call `stage_canonical_at_ref(...)` unconditionally. If it fails, raise (Class-B can't fall back to "leave PENDING" — the resolution is sealed at envelope time).

**Why raise on failure for cli.py path (vs leave PENDING in the merge_helper NN branches).** The NN branches in merge_helper get to leave PENDING because they run BEFORE the verdict is sealed; the legacy resolver path picks it up. The cli.py post-resolve loop runs AFTER the resolver helper finished — there is no fallback path. If the canonical content can't be read at this stage, we have a real problem (e.g., canonical ref vanished mid-run). Failing closed (raise → discard staging → exit 2) is the correct response.

**Concrete change in cli.py.** Replace lines 268-278 with:

```python
# Stage resolved content for accept-canonical-flavored verdicts.
# AC.α-hotfix-2.1 + AC.α-hotfix-2.2: the merge_helper NN branches
# stage their own content (α-hotfix #59), but the LLM-resolver
# INFERRED_ACCEPT_CANONICAL path and the Class-B ACCEPT_UPSTREAM
# path don't — close them here.
if halt_exception is None:
    for entry in report.conflicts:
        if (
            entry.resolution is Resolution.INFERRED_ACCEPT_CANONICAL
            and entry.resolved_content_path is None
        ):
            # LLM-resolver returned accept-canonical (not via NN
            # fast-path) — stage canonical's HEAD content now.
            staged = stage_canonical_at_ref(
                entry=entry,
                canonical_root=canonical_root,
                canonical_ref=resolved_ref,
                workspace_root=workspace_root,
                sync_ref=resolved_ref,
                write_merged=lambda p, c: _write_merged_to_staging(
                    staging_path, p, c
                ),
            )
            if not staged:
                discard_staging(staging_path)
                print(
                    f"[workspace-sync] failed to stage canonical "
                    f"content for {entry.path} (binary or "
                    f"unreadable); halting.",
                    file=sys.stderr,
                )
                return 2
        elif entry.resolution is Resolution.ACCEPT_UPSTREAM:
            # Class-B operator-prefers-canonical branch. Stage
            # canonical content explicitly — the post-stage
            # clean_writes.append in α-hotfix-1 was a no-op.
            staged = stage_canonical_at_ref(
                entry=entry,
                canonical_root=canonical_root,
                canonical_ref=resolved_ref,
                workspace_root=workspace_root,
                sync_ref=resolved_ref,
                write_merged=lambda p, c: _write_merged_to_staging(
                    staging_path, p, c
                ),
            )
            if not staged:
                discard_staging(staging_path)
                print(
                    f"[workspace-sync] failed to stage canonical "
                    f"content for Class-B path {entry.path}; halting.",
                    file=sys.stderr,
                )
                return 2
```

The buggy `clean_writes.append(entry.path)` is removed entirely (it was a no-op).

### D-build.B — Tighten ConflictEntry validator (Bug C)

**Choice.** Extend the existing `_resolution_requires` model_validator in `conflict_report.py` to require non-null `resolved_content_path` for `INFERRED_ACCEPT_CANONICAL` and `ACCEPT_UPSTREAM`. Mirrors the existing rule for `INFERRED_MERGED` and `THREE_WAY_MERGE`.

**Why these and not also `INFERRED_ACCEPT_WORKSPACE`.** `INFERRED_ACCEPT_WORKSPACE` means "preserve the workspace's content" — staging is unnecessary because the workspace already has the content. The dispatch's note confirms this: "`INFERRED_ACCEPT_WORKSPACE` does NOT require it (the workspace already has the content; staging is unnecessary)." Same for `KEEP_LOCAL`.

**Why also `ACCEPT_UPSTREAM`.** Class-B operator-prefers-canonical: same shape as `INFERRED_ACCEPT_CANONICAL` — canonical's content needs to be staged for apply to work. Tightening the validator catches Bug B structurally.

**Where to place.** Inside `_resolution_requires` (existing model_validator at line 159), add:

```python
if r in (Resolution.INFERRED_ACCEPT_CANONICAL, Resolution.ACCEPT_UPSTREAM):
    if not self.resolved_content_path:
        raise ValueError(
            f"{self.path}: resolution={r.value} requires "
            "resolved_content_path"
        )
```

**Backwards-compat impact.** This validator runs at every `ConflictEntry` construction time (Pydantic `mode="after"`). The existing audit YAMLs in pos3 and the test fixtures with `resolution: inferred-accept-canonical` and `resolved_content_path: null` will FAIL TO LOAD post-change. Two affected surfaces:

1. **Test fixtures.** `tests/test_conflict_report_b_shape.py` and `tests/test_merge_helper.py` likely have synthetic `ConflictEntry` constructions that need updating. Need to grep for affected tests and add `resolved_content_path="..."` to any test that constructs an `INFERRED_ACCEPT_CANONICAL` or `ACCEPT_UPSTREAM` entry.

2. **Pre-existing audit YAMLs on disk.** Workspaces (e.g., pos3) with old audit YAMLs containing the bug shape will fail to load via `load_conflict_report`. This is desirable — it surfaces the bug class structurally — but the load-failure path needs to be graceful. Looking at `load_conflict_report` (line 294): a malformed YAML raises `pydantic.ValidationError`, which propagates. The CLI's `_ref_already_applied` calls `load_state` (state.yaml, not audit.yaml) — the audit isn't loaded in the idempotency path. Audit re-load happens only via direct user inspection or future re-resolve flows. Acceptable.

**Test for Bug C.** New test in `tests/test_conflict_report_b_shape.py`:

```python
def test_alpha_hotfix_2_inferred_accept_canonical_requires_resolved_content_path():
    """AC.α-hotfix-2.3: ConflictEntry rejects INFERRED_ACCEPT_CANONICAL
    with null resolved_content_path. Structural enforcement of the
    same bug class as Bug A — without resolved_content_path the
    apply silently no-ops."""
    with pytest.raises(ValueError, match="resolved_content_path"):
        ConflictEntry(
            path="framework/x.py",
            prior_release_sha256=None,
            installed_sha256="abc",
            new_release_sha256="def",
            change_kind=ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
            resolution=Resolution.INFERRED_ACCEPT_CANONICAL,
            rationale="test",
            confidence=1.0,
            resolved_content_path=None,  # the bug shape
        )

def test_alpha_hotfix_2_accept_upstream_requires_resolved_content_path():
    """AC.α-hotfix-2.3: same enforcement for Class-B ACCEPT_UPSTREAM."""
    with pytest.raises(ValueError, match="resolved_content_path"):
        ConflictEntry(
            path="framework/x.py",
            prior_release_sha256=None,
            installed_sha256="abc",
            new_release_sha256="def",
            change_kind=ConflictChangeKind.LOCAL_MODIFIED_EQUALS_UPSTREAM,
            resolution=Resolution.ACCEPT_UPSTREAM,
            resolved_content_path=None,  # the bug shape
        )
```

### D-build.C — state.yaml hygiene (Bug D)

**Choice.** Per dispatch's option (a) — simpler. The merge_helper currently writes a state.yaml in its `finally` block (lines 770-808 of merge_helper.py) with status SUCCESS/PARTIAL/FAILURE. Specifically when `halt_reason is None and not has_pending() and deferred_count == 0`, it writes `SUCCESS`. Then cli.py re-stamps SUCCESS at line 337-353 after `apply_staging_atomically` succeeds.

Bug D fires when:
1. resolve_inferred_conflicts completes cleanly → merge_helper writes `status=SUCCESS` (line 786).
2. CLI confirm gate refuses (auto-accept floor not met) → discard_staging → no apply.
3. cli.py's success-restamp doesn't run (it's inside the `if confirmed_by_operator:` branch).
4. **state.yaml is left at SUCCESS** with `sync_ref` set — but no apply happened.
5. Next run hits the `_ref_already_applied` idempotency check → no-op false-success.

**Fix shape.** Change merge_helper's terminal status from `SUCCESS` to a new `NEEDS_APPLY` (or repurpose `PARTIAL`). The cli.py post-apply path is the ONLY writer of `SUCCESS`. The idempotency check at `_ref_already_applied` already requires `status is SyncStatus.SUCCESS` — so any `NEEDS_APPLY` won't match.

**Why a new status (`NEEDS_APPLY`) vs. reusing `PARTIAL`.** `PARTIAL` semantically means "some conflicts pending"; reusing it for "resolved cleanly but apply not yet run" muddies the meaning and might confuse audit consumers. A new `NEEDS_APPLY` enum value is clean.

**Concrete change.**

- **`state.py`:** Add `SyncStatus.NEEDS_APPLY = "needs-apply"`.
- **`merge_helper.py` line 786:** Change `else: status = SyncStatus.SUCCESS` to `else: status = SyncStatus.NEEDS_APPLY`. The merge_helper NEVER writes SUCCESS now — it writes `FAILURE` (halt), `PARTIAL` (pending/deferred), or `NEEDS_APPLY` (resolved-cleanly-await-apply).
- **`cli.py`:** No change needed — the apply path already calls `make_state_record(..., status=SyncStatus.SUCCESS)` and saves it AFTER `apply_staging_atomically`. The discard-path correctly leaves the merge_helper's `NEEDS_APPLY` state in place (no rewrite needed; the next run will re-resolve and the idempotency check will not match).

**Test for Bug D.** New test in `tests/test_cli_b_shape.py`:

```python
def test_alpha_hotfix_2_discard_path_does_not_advance_state_to_success(...):
    """AC.α-hotfix-2.4: when --auto-accept's confidence floor is not
    met and CLI discards staging, state.yaml status MUST NOT be
    SUCCESS — otherwise next run no-ops via idempotency fast-path
    and ships false-success."""
    # Build canonical with one path that resolves below the floor.
    # Set --confidence-floor to a value above what α.1 produces (1.0)
    # — actually α.1 produces 1.0 confidence; need a Class-C path
    # that goes through LLM and produces low confidence. Use a stub
    # resolver that returns confidence=0.5 with --confidence-floor=0.85.
    # ...
    # rc = main(...)
    # assert rc == 0  # discard is a successful exit
    # state = load_state(workspace)
    # assert state.status is not SyncStatus.SUCCESS
    # # And confirm next-run does NOT short-circuit on idempotency:
    # rc2 = main(...)  # same args
    # # If the bug is unfixed, rc2 path was "already applied"; post-fix
    # # it re-resolves.
```

Actually a simpler test shape: post-discard, verify the state.yaml status field is NOT `success`. That's the binding assertion. Making the next-run no-op assertion is a bonus.

### D-build.D — Test infrastructure for Bug D + Bug A

For Bug A, we need to force the LLM-resolver to return `inferred-accept-canonical` (not via NN fast-path). The cleanest way: stub the resolver factory to return a `MergeResolver` whose `.resolve()` returns a `MergeVerdict(resolution="inferred-accept-canonical", ...)`. AND ensure α.1 NN doesn't engage by making the workspace content NOT match any canonical-history blob (use random content, not the ancestor's).

For Bug B, we need a Class-B path with workspace_sha == prior_sha (so the helper picks ACCEPT_UPSTREAM). The conflict_detection won't surface such a path naturally (it filters identical content). Construct the test by directly invoking `resolve_inferred_conflicts` with a hand-built `ConflictReport` containing a Class-B path with `change_kind=LOCAL_MODIFIED_EQUALS_UPSTREAM`.

But wait — the apply path is `cli.py`, not `resolve_inferred_conflicts` directly. To test the cli.py:275-278 fix, we need the FULL CLI flow. Approach:

**Bug B test approach.** Make the conflict_detection produce a Class-B entry with workspace_sha != canonical_sha but where `merge_helper` resolves to `ACCEPT_UPSTREAM`. The merge_helper's Class-B branch picks `ACCEPT_UPSTREAM` only when `change_kind` is NOT in `(LOCAL_MODIFIED_ONLY, UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED)`. But conflict_detection produces only those two kinds when canonical != workspace — UNLESS `prior_sha != None` and `canonical_sha != prior_sha` and `workspace_sha == prior_sha` (line 121-124, returns None — clean update, no entry). Or convergent `LOCAL_MODIFIED_EQUALS_UPSTREAM` (filtered).

So the Class-B `ACCEPT_UPSTREAM` branch in merge_helper is currently UNREACHABLE from real CLI flow. **However, the dispatch explicitly names it as a bug** because it's reachable if a future change adds `prior_sha` plumbing or the change_kind classifier produces a different kind.

**Pragmatic test approach for Bug B.** Mock or monkey-patch the conflict_detection to produce a Class-B entry with `change_kind=LOCAL_MODIFIED_EQUALS_UPSTREAM` (or alternative: directly invoke the helper with a constructed report). Then run cli.py's `_execute_sync` flow (skip CLI argv parsing). Assert workspace file post-apply matches canonical's HEAD blob.

**Cleaner approach.** Patch `detect_b_shape_conflicts` with a stub that returns a hand-built report with one Class-B entry resolved to `ACCEPT_UPSTREAM` already (wait — but then the merge_helper's `if entry.resolution is not Resolution.PENDING: continue` skips it; but cli.py's post-resolve loop hits it). Even simpler — construct the entry with `resolution=Resolution.ACCEPT_UPSTREAM` directly via mock of detect.

Actually simpler still: the merge_helper's Class-B path sets `ACCEPT_UPSTREAM` ONLY when `change_kind not in (LOCAL_MODIFIED_ONLY, UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED)`. We can construct a synthetic test that bypasses conflict_detection by directly providing `ConflictReport` with a Class-B entry having `change_kind=LOCAL_MODIFIED_EQUALS_UPSTREAM` — but that triggers the AUTO_ACCEPT validator. Let me look at the validator constraints again.

Looking at `_resolution_requires` (line 167-174): `AUTO_ACCEPT_LOCAL_MATCHES_UPSTREAM only valid when change_kind=local_modified_equals_upstream`. The reverse is not asserted: `LOCAL_MODIFIED_EQUALS_UPSTREAM` does NOT require resolution=AUTO_ACCEPT. So we can construct a `ConflictEntry(change_kind=LOCAL_MODIFIED_EQUALS_UPSTREAM, resolution=PENDING)` — then merge_helper's Class-B classification fires `ACCEPT_UPSTREAM`. 

**Most pragmatic test for Bug B.** Use `monkeypatch` to replace `detect_b_shape_conflicts` with a stub returning a hand-built `ConflictReport` with a single PENDING Class-B entry having `change_kind=LOCAL_MODIFIED_EQUALS_UPSTREAM`. Real canonical + real workspace at different content for the path. Run cli.main. Assert workspace file post-apply matches canonical HEAD blob.

Or simplest of all: Class-B `LOCAL_MODIFIED_EQUALS_UPSTREAM` is tricky precisely because it's structurally unreachable — let's accept that and TEST via `resolve_inferred_conflicts` directly, then a SECOND test that invokes `_execute_sync` with a stubbed detector. That second test is the binding HC#3 file-content assertion.

**Bug A test approach.** Stub the resolver to return `MergeVerdict(resolution="inferred-accept-canonical", ...)`. Build canonical with two paths: one (`framework/normal.py`) won't match any ancestor → falls through to LLM resolver → resolver returns accept-canonical → cli.py:271 branch fires.  Assert workspace file post-apply matches canonical's HEAD content.

**Bug D test approach.** Real two-commit canonical. Real workspace differing. Resolver stub returns `inferred-merged` with confidence=0.5. CLI invoked with `--auto-accept --confidence-floor 0.85`. The all_floor_met check (line 320-324) fails → confirm gate returns False → discard_staging runs. Assert state.yaml post-discard has status != SUCCESS. Bonus: invoke main() a second time, assert it does NOT print "already applied" (i.e., it does re-resolve).

### D-build.E — Commit prose

Single amendment commit. Per speedup (c), inline methodology snippets:

```
feat(workspace-sync): α-hotfix-2 — close 4 correctness bugs of the verdict-without-stage class (amendment #60, AC.α-hotfix-2.1–.4 + AC.α-hotfix-2.S)

α-hotfix #59 fixed the NN-resolver branch only (HC#1 named-scope
binding). Three remaining bugs of the same class were surfaced as
HALT-FOUND #1, #2, #3 in #59's plan-doc §13. Bug D was caught by
primary persona during post-#59 verification.

Bug A — cli.py:271-274 LLM-resolver INFERRED_ACCEPT_CANONICAL was
unstaged (the "do nothing extra" comment was wrong; clean_writes
contains only no-conflict paths). Fix: when the post-resolve loop
sees an INFERRED_ACCEPT_CANONICAL entry without resolved_content_path
(NN entries already have it), call the centralized staging primitive.

Bug B — cli.py:275-278 ACCEPT_UPSTREAM did clean_writes.append AFTER
stage_canonical_clean_writes had already run; the append was a no-op.
Fix: replace with a direct call to stage_canonical_at_ref.

Bug C — conflict_report.py validator did not require
resolved_content_path for INFERRED_ACCEPT_CANONICAL or ACCEPT_UPSTREAM.
Fix: extend _resolution_requires to enforce the contract structurally
so future regressions cannot ship.

Bug D — state.yaml advanced to SUCCESS even when staging was
discarded (e.g., auto-accept floor not met → no apply). Subsequent
runs hit the convergent-idempotency fast-path. Fix: merge_helper
writes status=NEEDS_APPLY (new SyncStatus value) on resolve-clean;
only cli.py post-apply writes SUCCESS.

Three regression tests asserting file-content-byte-match (HC#3
binding) plus three validator/state tests.

Surface added: ~150 LOC under workspace-sync/.
- src/workspace_sync/merge_helper.py: rename
  _stage_canonical_for_nn_match → stage_canonical_at_ref (public
  re-export); change SUCCESS → NEEDS_APPLY in finally state-write.
- src/workspace_sync/cli.py: replace lines 268-278 with explicit
  staging calls per accept-canonical-flavored verdict.
- src/workspace_sync/conflict_report.py: extend validator.
- src/workspace_sync/state.py: add SyncStatus.NEEDS_APPLY.
- tests/test_cli_b_shape.py: 3 new tests (Bug A, Bug B, Bug D).
- tests/test_conflict_report_b_shape.py: 2 new tests (Bug C).

Backwards-compat (HC#2 binding): all 140 existing workspace-sync
tests pass. Some existing tests construct ConflictEntry with
resolution=INFERRED_ACCEPT_CANONICAL or ACCEPT_UPSTREAM and
resolved_content_path=None — those test fixtures are updated to
include the now-required field. Such updates are mechanical and
preserve test intent (the intent was to verify verdict-shape, not
to assert a null content path).

No new third-party deps (HC#4). No edits outside workspace-sync/.

Plan-doc: docs/rebuild/plans/workspace-sync-alpha-hotfix-2.md
Builder-plan: docs/rebuild/plans/workspace-sync-alpha-hotfix-2.builder-plan.md
Manifest: docs/rebuild/plans/workspace-sync-alpha-hotfix-2.manifest.yaml
```

---

## Section B — Reverse-direction trace (every code path → AC)

| Surface | Path / function | AC |
|---|---|---|
| `merge_helper.py` rename | `_stage_canonical_for_nn_match` → `stage_canonical_at_ref` (public) | AC.α-hotfix-2.1 + AC.α-hotfix-2.2 |
| `merge_helper.py` finally state-write | line 786 SUCCESS → NEEDS_APPLY | AC.α-hotfix-2.4 |
| `state.py` enum | new `SyncStatus.NEEDS_APPLY` value | AC.α-hotfix-2.4 |
| `cli.py` post-resolve loop | lines 268-278 replaced with explicit per-resolution staging | AC.α-hotfix-2.1 + AC.α-hotfix-2.2 |
| `conflict_report.py` validator | extended `_resolution_requires` to gate INFERRED_ACCEPT_CANONICAL + ACCEPT_UPSTREAM | AC.α-hotfix-2.3 |
| `tests/test_cli_b_shape.py` Bug A test | LLM-resolver INFERRED_ACCEPT_CANONICAL → file-content-byte-match | AC.α-hotfix-2.1 |
| `tests/test_cli_b_shape.py` Bug B test | Class-B ACCEPT_UPSTREAM → file-content-byte-match | AC.α-hotfix-2.2 |
| `tests/test_cli_b_shape.py` Bug D test | discard path does not advance state to SUCCESS | AC.α-hotfix-2.4 |
| `tests/test_conflict_report_b_shape.py` Bug C test (×2) | validator rejects null resolved_content_path for INFERRED_ACCEPT_CANONICAL + ACCEPT_UPSTREAM | AC.α-hotfix-2.3 |
| Pre-existing test fixtures | mechanical updates for tightened validator | (no new AC; HC#2 backwards-compat) |
| `tests/SEAL_COMMIT` | sidecar bumped via `pos-amend apply` | AC.α-hotfix-2.S |
| `tests/test_no_sealed_amendments.py` BASELINE | bumped to amendment-#60 HEAD~1 via `pos-amend apply` | AC.α-hotfix-2.S |
| `seals/SEAL_COMMIT.alpha-hotfix-2` | narrative target written by `pos-amend seal` | AC.α-hotfix-2.S |

Every line of new/modified code lives in a row above. ODD-clean.

---

## Section C — Build sequence

1. **Run `pos-amend apply` on the manifest** to bump BASELINE + sidecar + widen bindings.
2. **Edit `state.py`:** add `SyncStatus.NEEDS_APPLY` enum value.
3. **Edit `merge_helper.py`:**
   - Rename `_stage_canonical_for_nn_match` → `stage_canonical_at_ref` (drop leading underscore so cli.py can import). Update both NN call sites.
   - Change line 786: `else: status = SyncStatus.SUCCESS` → `else: status = SyncStatus.NEEDS_APPLY`.
4. **Edit `cli.py`:** replace lines 268-278 with the explicit per-resolution staging block. Import `stage_canonical_at_ref` from `merge_helper`.
5. **Edit `conflict_report.py`:** extend `_resolution_requires` to require `resolved_content_path` for `INFERRED_ACCEPT_CANONICAL` + `ACCEPT_UPSTREAM`.
6. **Run smoke tests** (speedup b):
   ```
   /Users/lukeivers/ivers-corp-pos-v2/.venv/bin/python -m pytest \
     workspace-sync/tests/ -q
   ```
   Some tests will FAIL on the validator tightening (existing fixtures with null resolved_content_path on the now-gated resolutions). Fix each by adding `resolved_content_path="..."` mechanically; re-run until green. (Speedup b allows skipping pre-seal full-suite if workspace-sync smoke passes.)
7. **Add new tests:**
   - `tests/test_cli_b_shape.py`: Bug A, Bug B, Bug D tests (3).
   - `tests/test_conflict_report_b_shape.py`: Bug C tests (2).
8. **Re-run smoke pass** until all green.
9. **Stage + commit** the amendment with the prose from D-build.E.
10. **Run `pos-amend seal --plan-doc <abs-path> --scoped-sweep <manifest>`** (speedup a).
11. **Verify post-seal:** git log shows amendment + seal + plan-§14-backfill commits; `tests/SEAL_COMMIT` matches; `tests/test_no_sealed_amendments.py` BASELINE matches HEAD~1.
12. **Backfill plan §14 + §15.**

---

## Section D — Risk surface + halt-trigger review

Per dispatch's halt-and-surface triggers:

- **Centralization touches resolver Protocol.** Re-checked: `MergeResolver` ABC's contract is `.resolve(path, canonical_text, workspace_text, prior_text) -> MergeVerdict`. The verdict is structural; staging is downstream of the verdict. **Trigger does NOT fire.** No Protocol changes needed.
- **Bug D fix collides with merge_helper PARTIAL/SUCCESS state-write convention.** The cli.py:335 comment notes the helper writes state during resolve. After this fix, the helper writes `NEEDS_APPLY` (not SUCCESS) on clean resolve; cli.py overwrites with SUCCESS only on apply. The convention is preserved — cli.py is still the authoritative SUCCESS writer. **Trigger does NOT fire.**
- **Wall-time exceeds 3-4h projection.** Estimated: ~2-3h (4 fixes, 5 tests, 1 enum addition, 1 validator extension, fixture mechanical updates). Halt if exceeded.

Halt-trigger review post-build: backfill in §14.
