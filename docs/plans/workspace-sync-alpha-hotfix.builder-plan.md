# workspace-sync α-hotfix — builder-plan

**Authored:** 2026-04-27 by primary persona (α-hotfix sealed-component amendment dispatch).
**Companion plan:** `docs/plans/workspace-sync-alpha-hotfix.md` (§1-§5 + AC.α-hotfix.1 + AC.α-hotfix.S).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Pre-amendment baseline (BASELINE candidate):** `44d470d1a15bab73ffa714197bf7a798d2f0704d` — current HEAD at amendment-commit-stage time. Prior amendment was **#58** (Bundle β.1 ergonomics, sealed `6860e4d`); next free amendment number = **#59**.

This builder-plan captures (a) the **method choices** (D-build.x) within AC.α-hotfix.1's outcome bound, (b) the **§2.5 reverse-direction trace** (one row per code path / branch → AC), and (c) the **build sequence** the agent will execute.

---

## Section A — Method choices (D-build.x)

### D-build.0 — Where to read canonical's HEAD content

**Choice.** Add a small helper at module top of `merge_helper.py`:

```python
def _read_canonical_blob_at_ref(
    canonical_path: Path, ref: str, rel_path: str
) -> bytes | None:
    """Resolve <ref>:<rel_path> on the canonical repo to its blob bytes.

    Returns the blob's raw bytes on success, None on failure (path
    missing at ref, submodule, symlink, ref unresolvable). The caller
    treats None as "cannot stage; skip" — the resolver path that
    falls through will surface the missing content as a deferred
    conflict via the existing legacy resolver path.
    """
    try:
        completed = subprocess.run(  # noqa: S603 — argv constructed
            ["git", "-C", str(canonical_path), "show", f"{ref}:{rel_path}"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout
```

**Why a helper and not inline?** Two NN branches (cache-hit at 438-447, cache-miss at 495-504) both need the same call shape. DRY + a single audit point for the shellout.

**Why bytes and not text?** The existing `stage_canonical_clean_writes` in `staging.py` writes bytes via `target.write_bytes(completed.stdout)`. The existing `_write_merged_to_staging` in `cli.py` calls `stage_resolved_content` which uses `target.write_text(content)` — a text-only sink. The merge_helper's existing `write_merged: Callable[[str, str], str]` signature is `(path, str_content) -> str_path`. We need to pass text (decoded UTF-8) to match the callable's signature.

**Method.** Read bytes first; decode UTF-8 with `errors="strict"`; on `UnicodeDecodeError`, treat as binary and fall through to `None` (which the caller handles as "cannot stage; let the legacy resolver path raise/defer"). Symmetric with `_read_text_or_none` already in this module (line 113).

ODD reverse trace target: every line of `_read_canonical_blob_at_ref` ladders to AC.α-hotfix.1 (it is the staging primitive's input).

### D-build.1 — Where exactly to call `write_merged` in NN branches

**Choice.** In both NN branches, immediately after setting `entry.confidence = 1.0` and `entry.ancestor_match_sha = ...`, before the `ancestor_match_count += 1` / `resolved_count += 1` / `continue` triple, insert:

```python
# Stage canonical's HEAD content so apply_staging_atomically
# actually overwrites the workspace file. Without this, the
# verdict says "accept canonical" but no staging file exists,
# so os.replace skips the path silently. (α-hotfix #59: the
# named bug — verdict-without-stage was the cause of false-
# success on every NN-resolved path.)
canonical_bytes = _read_canonical_blob_at_ref(
    canonical_root, canonical_ref, entry.path
)
if canonical_bytes is not None:
    try:
        canonical_text = canonical_bytes.decode("utf-8")
    except UnicodeDecodeError:
        # Binary file — let the legacy resolver path defer.
        # We DO NOT mark resolved here; fall through.
        canonical_text = None
    if canonical_text is not None and write_merged is not None:
        entry.resolved_content_path = write_merged(
            entry.path, canonical_text
        )
```

**Why preserve `write_merged is not None` guard?** The callable is optional (line 265 of merge_helper.py: `write_merged: Callable[[str, str], str] | None = None`). When omitted, the helper's else-branch at line 578-589 writes to `workspace_root/.pos/sync/<ref>/merged/<path>` — **but that path is NOT under the staging tree**. Staging lives at `workspace_root/.pos/sync/staging/<ref>/<path>`. The else-branch was already part of the bug (it would write to a non-staging location). For NN, when `write_merged is None`, we fall back to the same else-branch shape used for INFERRED_MERGED at line 578-589 — except even that doesn't get applied. **Plan-author observation: when `write_merged is None`, no caller of `resolve_inferred_conflicts` actually applies via `apply_staging_atomically`.** Today the only caller is `cli.py` which always provides `write_merged`. The else-branch is reachable only from tests that instantiate `resolve_inferred_conflicts` directly. Safe to mirror the existing else-branch logic for NN. The new test will provide `write_merged`.

**Why decode UTF-8 and not pass bytes?** The existing `write_merged` callable signature is `Callable[[str, str], str]` (text in, path out). Changing the signature would break HC#1 (no edits outside the NN branches). We decode here. Binary files in the framework surface are rare; if one shows up, it'll fail UTF-8 decode and fall through to the legacy path (which raises a `_FallthroughToGenerator` or defers — observable + investigable, not silently broken).

**What if `_read_canonical_blob_at_ref` returns None?** The verdict has already been set (`entry.resolution = Resolution.INFERRED_ACCEPT_CANONICAL`). If we leave that verdict intact without staging, we ship the original bug. **Decision:** if reading fails, we MUST NOT keep the INFERRED_ACCEPT_CANONICAL verdict — that would re-introduce the false-success. Instead, we leave `entry.resolution = Resolution.PENDING` (don't set the verdict) and `continue` so the legacy resolver path picks it up later. This requires moving the verdict-set lines below the read-and-stage block, OR setting the verdict only after the staging succeeds.

**Refined method.** Restructure both NN branches:

```python
# (cache-hit branch)
if cached.ancestor_sha is not None:
    # Read canonical's HEAD content first; if we can't, leave
    # the entry PENDING so the legacy resolver path handles it.
    canonical_bytes = _read_canonical_blob_at_ref(
        canonical_root, canonical_ref, entry.path
    )
    canonical_text: str | None = None
    if canonical_bytes is not None:
        try:
            canonical_text = canonical_bytes.decode("utf-8")
        except UnicodeDecodeError:
            canonical_text = None
    if canonical_text is None:
        # Cannot stage; fall through to the legacy resolver path.
        # Span emitted via the no-match path below.
        with otel_span(...): pass
    else:
        # Stage and seal the verdict.
        with otel_span(...) as span: ...
        entry.resolution = Resolution.INFERRED_ACCEPT_CANONICAL
        entry.rationale = ...
        entry.confidence = 1.0
        entry.ancestor_match_sha = cached.ancestor_sha
        if write_merged is not None:
            entry.resolved_content_path = write_merged(entry.path, canonical_text)
        else:
            # Mirror INFERRED_MERGED's else-branch (lines 578-589).
            merged_dir = workspace_root / ".pos" / "sync" / report.sync_ref / "merged"
            target = merged_dir / entry.path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(canonical_text)
            entry.resolved_content_path = str(target)
        ancestor_match_count += 1
        resolved_count += 1
        continue
```

Same shape for the cache-miss branch.

**Why this restructure is preferable to the inline insert from D-build.0's first form.** It preserves the invariant "verdict set ⇔ content staged". The original buggy code violated that invariant; the fix has to honour it.

### D-build.2 — Regression test design

**Choice.** New test in **`workspace-sync/tests/test_cli_b_shape.py`** (extends the CLI integration test family that already builds synthetic canonicals + workspaces). Function name: `test_alpha_hotfix_NN_resolved_paths_actually_overwrite_workspace_file`.

**Test fixture shape.**

1. **Build a canonical repo** with two commits:
   - Commit 1 (ancestor): writes `framework/payload.txt` containing string `"v1-content"`.
   - Commit 2 (HEAD): edits `framework/payload.txt` to `"v2-canonical-head"`.
2. **Build a workspace** that has `framework/payload.txt` at content `"v1-content"` (matches the ancestor blob from commit 1).
3. **Mark `framework/payload.txt` as Class C** in the workspace's `sync_protected.yaml` (so it routes through the resolver).
4. **Run `pos-sync --canonical <canonical> --workspace <workspace> --auto-accept --confidence-floor 0.85`** (or import + invoke `cli.main` directly with the equivalent argv).
5. **Assert the verdict shape** (existing pattern):
   - The audit YAML reports `resolution: inferred-accept-canonical` for `framework/payload.txt`.
   - `state.yaml` advances to `success`.
6. **Assert file-content-byte-match (HC#4 binding):**
   ```python
   workspace_payload = (workspace_root / "framework" / "payload.txt").read_bytes()
   canonical_head_payload = subprocess.check_output(
       ["git", "-C", str(canonical_root), "show", "HEAD:framework/payload.txt"]
   )
   assert workspace_payload == canonical_head_payload, (
       f"workspace file content does not match canonical HEAD blob "
       f"(workspace={workspace_payload!r}, canonical={canonical_head_payload!r})"
   )
   ```

**Why `test_cli_b_shape.py` and not a new file?** That test file already has the synthetic-canonical + synthetic-workspace + `cli.main` invocation pattern. Reusing the existing helpers minimises new fixture surface; the test is one new function inside an existing module.

**Why a real two-commit canonical and not a mock?** The bug is at the `git show <ref>:<path>` boundary. Mocking the git-shellout would be uninstrumented (the test would pass even if the shellout argv shape was wrong). A real canonical with a real ancestor-match exercises the full path, including the new `_read_canonical_blob_at_ref` helper.

**Speedup (b) compatibility.** The new test runs in <1s (small canonical, single conflict). It composes with the existing test suite's pytest discovery; no new conftest entries needed.

### D-build.3 — Commit prose

**Choice.** Single amendment commit. Per speedup (c), inline methodology snippets in the commit message body.

```
feat(workspace-sync): α-hotfix — NN-resolved entries actually overwrite workspace files (amendment #59, AC.α-hotfix.1 + AC.α-hotfix.S)

Bug: Bundle α (#57) introduced the NN ancestor-detection accept-
canonical fast-path in merge_helper.py (lines 438-447 cache-hit;
495-504 cache-miss). Both branches set the verdict
(Resolution.INFERRED_ACCEPT_CANONICAL + rationale + confidence +
ancestor_match_sha) but did NOT stage canonical's HEAD content.
The downstream apply_staging_atomically walks the staging tree,
finds no file for the NN-resolved path, and silently no-ops.
state.yaml advances to "applied"; workspace files stay at pre-
apply state. False-success ships.

Repro (verified 2026-04-27 by primary persona): pos-sync against
pos3 with --auto-accept reports applied:<ref>; audit confirms
46 NN-resolved entries with resolved_content_path: null;
workspace files do not match canonical's HEAD blob byte-for-byte.

Fix: read canonical's HEAD content via
git show <canonical_ref>:<entry.path> in a new helper
_read_canonical_blob_at_ref, decode UTF-8, and call the
existing write_merged callable to drop the content into staging.
Set entry.resolved_content_path on success. On read failure
(missing path, binary, ref unresolvable), do NOT set the verdict
— leave the entry PENDING so the legacy resolver path picks it
up. This preserves the invariant "verdict set ⇔ content staged"
that the buggy code violated.

Regression test: test_cli_b_shape.py adds
test_alpha_hotfix_NN_resolved_paths_actually_overwrite_workspace_file
which builds a real two-commit canonical (ancestor + HEAD), seeds
a workspace with the ancestor's content, runs cli.main with
--auto-accept, and asserts post-apply that the workspace file's
bytes equal canonical's HEAD blob byte-for-byte. Without this
test, Bundle α's existing 139 tests let the bug ship despite
all "verdict shape correct" assertions passing.

Surface: workspace-sync/src/workspace_sync/merge_helper.py
(+~30 / -2 LOC; both NN branches restructured); a new helper
_read_canonical_blob_at_ref at module top (~15 LOC);
workspace-sync/tests/test_cli_b_shape.py (+1 test, ~80 LOC).

Halt-found in §13 of the plan-doc: cli.py:271-274 (LLM-resolver
INFERRED_ACCEPT_CANONICAL also unstaged); cli.py:275-278
(Class-B ACCEPT_UPSTREAM post-stage clean_writes append never
restages); conflict_report.py validator does not require
resolved_content_path for INFERRED_ACCEPT_CANONICAL. All three
deferred to follow-on amendment #60 per HC#1's named-scope
binding.

Backwards-compat (HC#2 + HC#3 binding): all 139 existing
workspace-sync tests pass. Post-hotfix total = 140
(+1 regression test). No edits to self-upgrade/ or
workspace-bootstrap/. No new third-party deps (HC#5).

Plan-doc: docs/plans/workspace-sync-alpha-hotfix.md
Builder-plan: docs/plans/workspace-sync-alpha-hotfix.builder-plan.md
Manifest: docs/plans/workspace-sync-alpha-hotfix.manifest.yaml
```

---

## Section B — Reverse-direction trace (every code path → AC)

| Surface | Path / function | AC |
|---|---|---|
| `merge_helper.py` new helper | `_read_canonical_blob_at_ref(canonical_path, ref, rel_path) -> bytes \| None` | AC.α-hotfix.1 |
| `merge_helper.py` cache-hit NN branch (438-447 → restructured) | reads canonical, decodes, calls write_merged, sets resolved_content_path | AC.α-hotfix.1 |
| `merge_helper.py` cache-miss NN branch (495-504 → restructured) | same shape | AC.α-hotfix.1 |
| `tests/test_cli_b_shape.py` new test | `test_alpha_hotfix_NN_resolved_paths_actually_overwrite_workspace_file` | AC.α-hotfix.1 |
| `tests/SEAL_COMMIT` | sidecar bumped via `pos-amend apply` | AC.α-hotfix.S |
| `tests/test_no_sealed_amendments.py` BASELINE | bumped to amendment-#59 HEAD~1 via `pos-amend apply` | AC.α-hotfix.S |
| `seals/SEAL_COMMIT.alpha-hotfix` | narrative target written by `pos-amend seal` | AC.α-hotfix.S |

Every line of new/modified code lives in a row above. ODD-clean.

---

## Section C — Build sequence

1. **Run `pos-amend apply` on the manifest** to bump BASELINE + sidecar + widen bindings. (Performed by primary persona in this session.)
2. **Edit `merge_helper.py`:**
   - Add `_read_canonical_blob_at_ref` helper at module top (after `_resolve_canonical_head_sha`, line ~110).
   - Restructure cache-hit NN branch (438-447) per D-build.1's refined method.
   - Restructure cache-miss NN branch (495-504) per D-build.1's refined method.
3. **Add the regression test in `tests/test_cli_b_shape.py`** per D-build.2.
4. **Run smoke tests (speedup b):**
   ```
   /Users/lukeivers/ivers-corp-pos-v2/.venv/bin/python -m pytest \
     workspace-sync/tests/test_merge_helper.py \
     workspace-sync/tests/test_cli_b_shape.py \
     workspace-sync/tests/test_ancestor_detection.py \
     -q
   ```
   On pass, proceed; on fail, debug + iterate without re-running the full suite.
5. **Stage + commit** the amendment with the prose from D-build.3.
6. **Run `pos-amend seal --plan-doc <abs-path> --scoped-sweep <manifest>`** (speedup a — restricts cross-component sweep to workspace-sync only).
7. **Verify post-seal:** `git log` shows the amendment commit + seal commit + plan-§14-backfill commit; `tests/SEAL_COMMIT` matches the amendment commit; `tests/test_no_sealed_amendments.py` BASELINE matches HEAD~1 of the amendment commit.
8. **Report on completion** with the post-build §14 + §15 backfill content and the file-content-byte-match test name.
