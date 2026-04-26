# Builder-plan — Amendment #53 — self-upgrade seal-bookkeeping retrofit

**Status:** builder-plan (pre-build).
**Author:** retrofit-build agent (this session).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**HEAD at authoring:** `edf6429` (post amendment #52 SHA-record commit).
**Plan (governs):** `docs/rebuild/plans/self-upgrade-seal-bookkeeping-retrofit.md`.
**Manifest:** `docs/rebuild/plans/self-upgrade-seal-bookkeeping-retrofit.manifest.yaml`.

This builder-plan records the implementation method this builder
intends to use to satisfy the ACs. It is not part of the contract
(per ODD §1, method is the builder's call); it exists for
transparency + post-amendment audit.

---

## 1. Files to create

### `self-upgrade/tests/test_no_sealed_amendments.py` — NEW

Mirror memory-system's pattern exactly. Module-level constants:

- `REPO_ROOT = Path(__file__).resolve().parent.parent.parent`
- `BASELINE = "edf64290c7c6f76d1d1c32e8808900fce76278b2"` — written
  at the full 40-char SHA so `pos-amend apply`'s regex
  `[0-9a-fA-F]{7,40}` matches and rewrites cleanly.
- `SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"`

Helper:

- `_seal_commit() -> str` — reads sidecar; returns sidecar contents
  if non-empty and not the literal `"HEAD"`; else returns `"HEAD"`.
  Identical to memory-system's helper.

Tests (two, exactly mirroring memory-system):

1. `test_B23_seal_commit_pinning_pattern` — reads its own source,
   asserts `"BASELINE = "` substring, `"SEAL_COMMIT_PATH"`
   substring, and `"{BASELINE}..{seal}"` substring (the diff form
   that routes through `_seal_commit()`). Guards against the
   `f94d602` HEAD-hardcoding defect re-introduction.
2. `test_B20_only_self_upgrade_surfaces_changed` — runs
   `git diff --name-only BASELINE..SEAL_COMMIT` and asserts every
   listed path matches an entry in `allowed_prefixes` or
   `allowed_files`.

`allowed_prefixes` — minimal initial set:

```python
allowed_prefixes = (
    "self-upgrade/",
    "data/",
    "docs/rebuild/plans/",
    "docs/rebuild/components/self-upgrade/",
)
```

`allowed_files` — universal admissions (per amendment #22 ruling #3):

```python
allowed_files: set[str] = {
    "CLAUDE.md",
    "docs/odd-in-pos.md",
    "docs/odd-methodology.md",
    "docs/rebuild/FUTURE_IDEAS.md",
}
```

The `pos-amend apply` step adds `docs/rebuild/plans/` to prefixes
and the four files via `universal_paths`. Manifest already declares
both; the test file's initial set must include them so
`apply --dry-run` reports green.

Module docstring summarises the retrofit context (parallel to
memory-system's docstring) — three paragraphs:

1. What this is (retrofit; 2026-04-26; mirrors memory-system #8 /
   gd+oa `7d462e3`).
2. Pattern note (B23 — BASELINE..SEAL_COMMIT, NOT ..HEAD; the
   `f94d602` defect must not recur).
3. BASELINE pin rationale + initial value `edf6429`.

### `self-upgrade/tests/SEAL_COMMIT` — NEW

Single line, no trailing newline beyond the SHA's own:

```
edf64290c7c6f76d1d1c32e8808900fce76278b2
```

`pos-amend seal` advances this to the seal commit SHA at seal
time.

### `self-upgrade/seals/.gitkeep` — NEW

Empty file. Creates the directory under git tracking so future
`pos-amend seal` runs can write `SEAL_COMMIT.<slug>` narrative
files. Same pattern peer components use (no `.gitkeep` actually
exists in their seals/, but those dirs got their first narrative
files immediately at first sealed amendment; for self-upgrade the
first narrative file lands in this same amendment via the
manifest's `narrative.target`, so the `.gitkeep` is technically
optional once the seal commit lands).

**Method choice:** ship the `.gitkeep` placeholder anyway, even
though the manifest's `narrative.target` writes
`self-upgrade/seals/SEAL_COMMIT.seal-bookkeeping-retrofit` at
seal time. Two reasons:

1. AC.SU-sb.3 is "directory exists ready to receive narratives" —
   shipping it as part of the amendment commit (not deferring to
   the seal commit) satisfies the AC at amendment-commit time.
2. The amendment-commit + seal-commit two-step is the standard
   ritual; if the directory does not exist before
   `narrative.target` is written, the seal step's mkdir-parents
   handles it, but tracking the directory in the amendment commit
   makes the surface visible at git-blame time.

If `.gitkeep` becomes redundant after the seal lands the narrative
file, that's tolerable — peer components carry no `.gitkeep` in
their populated seals/ dirs, and a follow-up cleanup is harmless.
Decision: ship the `.gitkeep`, leave it in place; small enough not
to matter.

## 2. Files to NOT touch

- `self-upgrade/src/**/*` — strict prohibition per plan §6.2.
- `self-upgrade/scripts/`, `self-upgrade/docs/`, `self-upgrade/
  pyproject.toml` — out of scope.
- The existing 14 self-upgrade test files — out of scope; only
  the new test file lands.
- Previous-BB clause-h artefacts (`docs/rebuild/plans/self-
  upgrade-clause-h-llm-merge.{md,builder-plan.md,vars.yaml}`) —
  left untracked per dispatcher directive.

## 3. Sequence

1. Verify pre-amendment narrow-scope test count
   (`cd self-upgrade && ../.venv/bin/pytest tests/ -q`) — expect
   120 passed.
2. Author the three new files (test, sidecar, .gitkeep).
3. Run the new tests in isolation
   (`cd self-upgrade && ../.venv/bin/pytest tests/test_no_sealed_amendments.py -v`)
   — expect 2 passed (empty diff against `BASELINE..HEAD` post
   creation, all paths under `self-upgrade/` prefix).
4. Run full self-upgrade suite — expect 122 passed.
5. `git status` sanity check — only the three new files staged
   plus the plan + manifest + builder-plan + vars.
6. `pos-amend apply --dry-run docs/rebuild/plans/self-upgrade-seal-bookkeeping-retrofit.manifest.yaml`
   — expect green; allowed_prefixes already include
   `docs/rebuild/plans/` so the universal admission is a no-op.
7. Stage + amendment commit (no `--amend`):

   ```
   feat(self-upgrade): seal-bookkeeping retrofit (amendment #53,
   AC.SU-sb.1–AC.SU-sb.S)
   ```

   Body: short paragraph naming the three artefacts + the parity
   rationale + reference to the precedent commits.
8. Post-amendment narrow-scope tests — confirm 122 passed.
9. `pos-amend seal --plan-doc docs/rebuild/plans/self-upgrade-seal-bookkeeping-retrofit.md docs/rebuild/plans/self-upgrade-seal-bookkeeping-retrofit.manifest.yaml`
   — runs touched-component tests + cross-component sweep,
   advances sidecar to seal SHA, writes
   `self-upgrade/seals/SEAL_COMMIT.seal-bookkeeping-retrofit` with
   the manifest narrative body, creates the deterministic seal
   commit, verifies post-seal `apply --dry-run` green, appends
   Commit-SHAs subsection to plan §14.
10. Cross-component seal-diff sweep across all 14 sealed components
    (now including self-upgrade) — expect green.

## 4. Test method

The two new tests are pure pattern + diff-scope tests; no new
fixtures. The existing `self-upgrade/tests/conftest.py` is not
relevant to the new file (it provides `tmp_history`,
`sample_manifest_dict`, `write_file_sha` — all unrelated to
seal-diff). The new test imports only `subprocess` + `pathlib`,
matching the memory-system precedent.

## 5. Risk-points + halt mitigations

- **Risk: BASELINE..HEAD diff at apply time includes unexpected
  files** (e.g. unstaged modifications outside the fence). Halt
  trigger #1 + #3 from plan §10. Mitigation: `git status`
  inspection before commit; only the four planned files (plan,
  manifest, builder-plan, vars) plus the three retrofit artefacts
  should appear staged.
- **Risk: an existing self-upgrade test fails because
  conftest.py side-effects collide with the new test file's
  module-level path manipulation** — none expected (the new file
  does not call `sys.path.insert`); halt trigger #4. Mitigation:
  pre-amendment full-suite run as the baseline.
- **Risk: cross-component sweep RED on a peer sealed component
  this amendment did not touch** — would indicate pre-existing
  drift surfaced by the sweep, not regression caused by this
  amendment. Halt trigger #5; surface for owner ruling.
- **Risk: previous-BB clause-h artefacts get accidentally
  staged** — halt trigger #8. Mitigation: explicit `git status`
  read before each commit; the three untracked clause-h files
  stay untracked throughout.

## 6. Backwards-compat verification

This amendment adds three NEW files; it does not modify or remove
any existing file. Backwards-compat is satisfied trivially —
nothing pre-existing changes shape.

## 7. ODD-compliance check (to run on completion)

- New tests assert observable outcomes (file source contains
  required constants; runtime diff scope confined to allowed
  prefixes). Yes.
- Silent exception branches? `_seal_commit()` falls back to
  `"HEAD"` when sidecar absent / equals literal `"HEAD"` —
  sanctioned pattern per B23, mirrors all peer retrofitted
  components. Yes.
- Non-objective code? No — every line maps to AC.SU-sb.1 or
  AC.SU-sb.2 or AC.SU-sb.3 or AC.SU-sb.S.
- Tests 1:1 to ACs? Two tests for AC.SU-sb.1 (pattern pinning +
  diff scope) — matches the existing retrofitted-component
  shape. AC.SU-sb.2 + AC.SU-sb.3 are file-existence-shaped and
  verified by `git status` + `pos-amend apply --dry-run`. Yes.

## 8. Commit shape

Amendment commit (plain `feat`, mirrors agent-dispatch-as-scope
naming):

```
feat(self-upgrade): seal-bookkeeping retrofit (amendment #53, AC.SU-sb.1–AC.SU-sb.S)
```

Seal commit message is generated by `pos-amend seal` from
`seal_description` in the manifest:

```
chore(seals): self-upgrade seal-bookkeeping retrofit — self-upgrade at <amendment-sha>
```

Plan-SHA-record commit is generated by `pos-amend seal --plan-doc`:

```
docs(plans): record amendment #53 commit SHAs in method-decision register
```

No `--amend` at any step.
