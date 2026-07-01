# v1.9.1 — MSC3 cold-clone test fixture fix

**Class:** PATCH — backwards-compatible test-correctness fix; no production
code change; no new capability.

## §1 Objective

Close the long-standing cold-clone failure of
`test_AC_MSC_3_canonical_claude_dev_md_carries_named_surface` in
`framework/primary-persona/tests/test_AC_MSC_3_named_thread_surface_in_corpus.py`.

**Root-cause (Tier-0 verified):** the test fixture uses `reader` injection to
simulate dev-mode without creating the on-disk directory structure that
`_read_dev_intent_inner` requires. Specifically, `_read_dev_intent_inner`
checks `personas_dir.is_dir()` before iterating; if the directory does not
exist on disk the function returns `"absent"` and `emit_session_start_context`
returns `""` without ever consulting the `reader` callable. In the dev-tree
`workspace/personas/primary/` exists (real user state, untracked by git), so
the check passes. In a cold clone, this directory is absent, so the check
fails.

**Classification: TEST-CORRECTNESS issue, not a behavior bug.** The behavior
is correct — `_read_dev_intent_inner` should not iterate a non-existent
directory. The test was designed with an incomplete fixture: `reader` injection
alone is insufficient; the personas directory must exist on disk for the reader
to be reached.

**Fix:** add `tmp_path: Path` parameter to the formerly-parameterless test
function; create a minimal `workspace/personas/loam/contract.yaml` on disk at
`tmp_path` (empty file — `reader` supplies the content); change the
`emit_session_start_context` call to use `tmp_path` as `workspace_root`.
This passes in both the dev-tree (where the test no longer relies on the
real `workspace/personas/`) and a cold clone (where the directory never
existed).

## §2 Scope / fence

Single-component fence: `primary-persona`.

**In fence:**
- `framework/primary-persona/tests/test_AC_MSC_3_named_thread_surface_in_corpus.py`
  (test fixture only; no production-code change)

**Out of fence (do NOT touch):**
- `framework/primary-persona/src/loam/primary_persona/session_start_gate.py`
- `plugins/dev-sdlc/tools/loam-mode/src/loam_mode/session_start.py`
- Any other component

## §3 Halt-before-build checks

- WD: `/Users/lukeivers/loam` — must match
- Plan-doc authored before any source edit (this file)
- No out-of-fence dependencies on the fix path
- Verified cold-clone failure reproduced Tier-0 against
  `.scratch/smokes/v1-9-0-smoke/` (the cold clone smoke from v1.9.0 — see
  that smoke writeup §10)

Halt triggers during build:
- Any source edit outside the fence
- A seal-test failure unrelated to this amendment's edits
- An ODD violation in adjacent code (surface, do not silently fix)
- Post-fix: if ANY of the 3 previously-passing MSC_3 tests regress

## §4 — Acceptance criteria

### AC.MSCCF.1

`test_AC_MSC_3_canonical_claude_dev_md_carries_named_surface` passes when
`workspace/personas/` is absent from the test's `workspace_root` (cold-clone
equivalent). The test creates a minimal `workspace/personas/loam/contract.yaml`
on disk at `tmp_path`, routes the `emit_session_start_context` call through
`tmp_path`, and the assertion `"docs/FUTURE_IDEAS_DRAFT.md" in payload` holds.

### AC.MSCCF.2

No regression in the other 3 MSC_3 tests
(`test_AC_MSC_3_named_surface_in_discovered_corpus`,
`test_AC_MSC_3_present_surface_reflected_in_session_fields`,
`test_AC_MSC_3_absent_surface_graceful_missing`), which remain parameterless
and do not rely on `workspace/personas/`.

### AC.MSCCF.S ★ (outcome-altitude)

All 4 `test_AC_MSC_3*` tests pass in BOTH the dev-tree AND a cold-clone
equivalent environment (a `pytest --rootdir` run against the primary-persona
component with no pre-seeded `workspace/personas/` directory at the test's
discovered workspace_root — i.e., a cold clone of HEAD).

outcome-altitude:true: AC.MSCCF.S

## §5 Named decisions

**D-MSCCF.1** — Why not fix `_read_dev_intent_inner` to call reader when
the directory is absent?

The behavior is correct: you should not iterate a non-existent directory.
Making the reader override the directory check would require either (a)
calling the reader on a `Path` that doesn't exist (breaks the reader's
contract as a file-content substitute), or (b) adding a `is_dir_fn` seam
(over-engineering for a test-fixture issue). The test fixture is the
right place to fix this.

**D-MSCCF.2** — Why use `tmp_path` as workspace_root instead of creating
the directory at `repo_root/workspace/personas/loam`?

`repo_root` (`/Users/lukeivers/loam`) is the canonical dev-tree with real
user state; creating files there in a test is unacceptable (it would
pollute the working tree and could interfere with other tests or processes).
`tmp_path` is pytest's per-test isolated temporary directory.

**D-MSCCF.3** — Does the `reader` intercept the `contract.yaml` content
when the file exists on disk as empty?

Yes. `_read_dev_intent_inner` calls `reader(candidate)` instead of
`candidate.read_text()` whenever `reader is not None`. The reader returns
`"is_primary: true\ndev_intent: yes\n"` for any `.yaml` or `contract`
path, which parses to `{"is_primary": True, "dev_intent": "yes"}` via
`yaml.safe_load`. `dev_intent: yes` is YAML 1.1 bool `True`; the code
handles this via the `if answer is True: return "yes"` branch.

## §6 Build steps

1. Author this plan-doc.
2. Author the manifest (`v1-9-1-msc3-cold-clone-fix.manifest.yaml`).
3. Commit plan + manifest.
4. Edit `test_AC_MSC_3_named_thread_surface_in_corpus.py`:
   - Add `tmp_path: Path` parameter to
     `test_AC_MSC_3_canonical_claude_dev_md_carries_named_surface`.
   - Before the `emit_session_start_context` call, create:
     `tmp_path / "workspace" / "personas" / "loam" / "contract.yaml"`
     (empty file, reader supplies content).
   - Change `emit_session_start_context(repo_root, reader=_reader)` to
     `emit_session_start_context(tmp_path, reader=_reader)`.
5. Run all 4 MSC_3 tests: confirm 4 passed.
6. Commit source edit (`fix(primary-persona): AC.MSCCF.1 MSC_3 cold-clone
   fixture adds minimal personas dir`).
7. `loam amend validate` — schema passes.
8. `loam amend apply` — apply commit lands.
9. `loam amend seal` — seal commit lands.
10. Author `docs/experiments/v1-9-1-hard-smoke.md`.
11. Author `docs/state-migrations/v1-9-1-msc3-cold-clone-fix.migration.yaml`.
12. Backfill §13 of this plan-doc with AC verdicts.
13. Backfill `docs/STATE.md` with v1.9.1 SHIPPED LOCAL entry.
14. Backfill `docs/release-roadmap.md` §2 with v1.9.1 row (seal SHA).
15. Commit release bookkeeping.
16. `loam release v1.9.1 --dry-run` → verify all GREEN.

## §7 Out of scope

- Any production-source change in `session_start_gate.py`,
  `session_start_emitter.py`, or `loam_mode/session_start.py`
- Any new AC not listed in §4
- Changes to other test files
- Any non-primary-persona component

## §8 Method-decision register

| Decision | Recommendation | Rationale |
|---|---|---|
| D-MSCCF.1 | Fix the test fixture, not `_read_dev_intent_inner` | Behavior is correct; reader is insufficient for directory-check override |
| D-MSCCF.2 | Use `tmp_path` as workspace_root | Protects dev-tree from test-created state |
| D-MSCCF.3 | Empty on-disk file, reader supplies content | File must exist for `is_file()` check; reader intercepts content |

## §13 §status

| AC | Verdict |
|---|---|
| AC.MSCCF.1 | GREEN |
| AC.MSCCF.2 | GREEN |
| AC.MSCCF.S | GREEN |
