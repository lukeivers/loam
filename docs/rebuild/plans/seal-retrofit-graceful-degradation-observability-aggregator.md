# Plan — seal-enforcement retrofit for graceful-degradation + observability-aggregator

## Objective

1. **graceful-degradation**: retrofit the existing `tests/SEAL_COMMIT`
   sidecar with a `test_no_sealed_amendments.py` enforcement test so the
   "no sealed-component amendments" constraint moves from advisory to
   executable.
2. **observability-aggregator**: create both the missing
   `tests/SEAL_COMMIT` sidecar and the `test_no_sealed_amendments.py`
   enforcement test, finishing the seal ritual that was incomplete at
   2026-04-19 11:24 seal time.

This is a chore retrofit of the sealed-amendment pattern, not a new
amendment. Precedent: foundation-audit F2 (commit `af99046`) performed
the same retrofit for cost-governance and reversibility-primitive.

## Acceptance criteria (structural)

1. `graceful-degradation/tests/test_no_sealed_amendments.py` exists,
   mirrors the cost-governance / reversibility / self-correction
   pattern, and passes under `../.venv/bin/pytest tests/
   test_no_sealed_amendments.py -v` with zero offending paths.
2. `observability-aggregator/tests/SEAL_COMMIT` exists and carries the
   authoritative observability seal SHA `a0906c1`.
3. `observability-aggregator/tests/test_no_sealed_amendments.py` exists,
   mirrors the same pattern, and passes the same invocation.
4. Both components' full test suites remain green
   (`../.venv/bin/pytest tests/ -q`) — no regression introduced by the
   new files.
5. Each new test file defines two tests: a B23-pattern-pinning test
   (structural check of the file itself — presence of `BASELINE`,
   `SEAL_COMMIT_PATH`, `{BASELINE}..{seal}` diff form) and a B20-diff-
   scope test (runtime git diff confined to allowed prefixes). This
   matches the 2-test shape used by self-correction and orchestrator.

## SHA research

### graceful-degradation

- SEAL_COMMIT sidecar already at `dab49dd` (Amendment 3 landing SHA,
  committed by `d105e1a chore(seals): create graceful-degradation
  SEAL_COMMIT — Amendment 3`). Do not change.
- BASELINE for the new test: `dab49dd` (same as SEAL_COMMIT). Rationale:
  this is a retrofit, not a diff-surfacing exercise. Diffing
  `dab49dd..dab49dd` produces an empty diff — test passes trivially.
  Future amendments bump both BASELINE and SEAL_COMMIT to the new
  amendment's landing SHA (following the existing amendment ritual).
- `allowed_prefixes`: `("graceful-degradation/", "data/")` — same shape
  as cost-governance. `data/` covers runtime test output (OTel JSONL
  etc.) that is not a source change.

### observability-aggregator

- All observability-aggregator commits land in a single 2026-04-19
  sequence culminating at `a0906c1c9f727c879235c7721eaab7c77b8af63d`
  (`docs(observability-aggregator): D9 — bundled documentation per v1.1
  R4`) at 11:20:29 -0500. STATE.md records the seal at 2026-04-19 11:24.
  `a0906c1` is the last commit touching `observability-aggregator/`
  before the next component's work begins (self-upgrade at 12:17:56),
  and it is the final commit in the aggregator build — it is the
  component's seal SHA.
- SEAL_COMMIT sidecar: new file, contents `a0906c1`.
- BASELINE for the new test: `a0906c1` (same as SEAL_COMMIT) — same
  retrofit rationale as graceful-degradation.
- `allowed_prefixes`: `("observability-aggregator/", "data/")`.

## Files to be changed

Created (3 files):

1. `graceful-degradation/tests/test_no_sealed_amendments.py`
2. `observability-aggregator/tests/SEAL_COMMIT`
3. `observability-aggregator/tests/test_no_sealed_amendments.py`

Plus this plan file (1 file, already committed per CDC plan-first rule):

4. `docs/rebuild/plans/seal-retrofit-graceful-degradation-observability-aggregator.md`

No existing files are modified. `graceful-degradation/tests/SEAL_COMMIT`
already carries the correct SHA (`dab49dd`) and is left untouched.

## Validation strategy

1. Run the new tests in isolation:
   - `cd graceful-degradation && ../.venv/bin/pytest tests/test_no_sealed_amendments.py -v` — expect 2 passed.
   - `cd observability-aggregator && ../.venv/bin/pytest tests/test_no_sealed_amendments.py -v` — expect 2 passed.
2. Run the full component suites to confirm no regression:
   - `cd graceful-degradation && ../.venv/bin/pytest tests/ -q`
   - `cd observability-aggregator && ../.venv/bin/pytest tests/ -q`
3. Confirm `git status` shows only the expected unstaged files.

## Halt triggers

- Observability-aggregator SEAL_COMMIT SHA cannot be unambiguously
  identified from `git log observability-aggregator/` → halt, ask owner.
- New test fails on first run (empty `BASELINE..SEAL_COMMIT` diff should
  pass trivially) → halt, inspect git working tree for unexpected
  sealed-component modifications.
- Any existing test in either component starts failing after the file
  additions → halt, diagnose before proceeding.
- Plan file was not written to disk before any source file was created →
  halt; this would itself be a CDC violation.

## ODD-compliance check (to run on completion)

- New tests assert observable outcomes (diff scope confined to allowed
  prefixes; file source contains required constants). Yes.
- Silent exception branches? `_seal_commit()` falls back to `"HEAD"` if
  sidecar absent/placeholder — sanctioned pattern per B23, matches all
  peer retrofitted components.
- Non-objective code? No — seal-enforcement IS the objective.
- Tests 1:1 to structural criteria? Two tests per component (pattern
  pinning + diff scope) — matches existing retrofitted components. Yes.

## Do-not-commit discipline

Per instructions: leave all changes unstaged for owner review. Do not
invoke `git add` or `git commit`.
