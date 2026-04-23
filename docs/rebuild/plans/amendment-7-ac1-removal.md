# Amendment #12 — orchestrator-bootstrap-unification AC1 removal plan

**Status:** plan (written before any source edit, per plan-before-code CDC).
**Branch:** `pos-v2` at HEAD `a3bbdcd` (telegram-interface-framework-integration seal).
**Amends:** `docs/rebuild/components/orchestrator-bootstrap-unification/proposal.md` (originally shipped as amendment #7 at `445a6b4`, sealed at `9aeabd4`).
**Motivation:** the 2026-04-22 audit of amendment #7 surfaced that AC1 as written is a *method* assertion (static source-grep that the orchestrator source contains no `load_and_register` reference and no `from .bootstrap` import) rather than an *outcome* assertion. ODD §2.5 / §8.2 rule 9 forbid method-in-acceptance tests. The runtime complement is already covered by AC2's poison-bomb test (`test_AC2_missing_bootstrap_py_is_not_a_fail_closed_condition`), which writes a `raise RuntimeError(...)` into `~/.pos/bootstrap.py` and asserts the orchestrator starts+stops cleanly — structurally, that assertion cannot pass if the orchestrator's `_startup` still loads the workspace `bootstrap.py`.

---

## 1. Objective

Remove AC1 (the method-in-acceptance static-grep) from amendment #7's proposal and the paired test, keeping AC2's runtime poison-bomb as the sole behaviour assertion for "orchestrator no longer self-loads `bootstrap.py`". No other amendment #7 AC is weakened.

## 2. Scope

**Primary surface:** `orchestrator/` (delete one test function + its imports-only supporting module doc line).

**Secondary surfaces:**
- `hands-off-lifecycle/` — BASELINE bump in `tests/test_cross_cutting.py` + SEAL_COMMIT sidecar bump (cross-cutting seal counterpart; every amendment does this).
- `docs/rebuild/components/orchestrator-bootstrap-unification/proposal.md` — AC1 section replaced with a "withdrawn" stub; §4 behaviour-count table row updated.
- `docs/rebuild/plans/amendment-7-ac1-removal.md` — this plan.

**Dependency fence:** no other sealed component touched.

## 3. AC renumbering choice — **withdrawn stub, preserve numbering**

Option A: renumber AC2→AC1, AC3→AC2, …, AC9→AC8.
Option B (chosen): leave AC1's slot as an explicit "AC1 — withdrawn (covered by AC2's runtime complement)" stub; AC2..AC9 keep their original numbers.

**Rationale.** The amendment #7 ACs are cross-referenced from two test files (`orchestrator/tests/test_bootstrap_unification.py` with AC1/AC2/AC7/AC8 and `workspace-bootstrap/tests/test_bootstrap_unification.py` with AC3/AC4/AC5/AC6). Renumbering cascades into `workspace-bootstrap/`, which is a different sealed component whose proposal doesn't own this amendment — that's the §halt-trigger cascade condition. The stub choice keeps the diff contained to `orchestrator/` + `hands-off-lifecycle/` + the proposal + this plan. The stub explicitly names the rationale so future readers see why AC1 was withdrawn rather than why numbering has a gap.

## 4. Files touched

1. `orchestrator/tests/test_bootstrap_unification.py`
   - Delete the function body `test_AC1_startup_no_longer_loads_bootstrap_py` (lines 38–59) and the `_ORCHESTRATOR_SRC` helper at line 35 that only AC1 used.
   - Update the module docstring to remove the AC1 bullet (lines 8–9) and reword the "Covered here" list to `AC2, AC7, AC8` (no AC1).
   - Remove the now-unused `Path` import line only if no other test in the file needs it. (Still needed — AC2 uses `tmp_path: Path` type hint and AC8 uses `from pathlib import Path`. Keep `Path`.)
2. `docs/rebuild/components/orchestrator-bootstrap-unification/proposal.md`
   - Replace §3 AC1 heading+body with a short "withdrawn" stub citing the audit rationale and pointing at AC2.
   - Update the §4 behaviour-count table row ("Framework is the sole loader") to drop AC1 from the criteria list (keep AC4, AC5, AC6).
   - Add a top-of-proposal amendment-history note recording the #12 amendment.
3. `hands-off-lifecycle/tests/test_cross_cutting.py`
   - Advance `BASELINE` from `b9e1f96` (the existing value) to `a3bbdcd` (the pre-amendment tip — the telegram-interface-framework-integration seal commit).
   - Add a BASELINE-history comment block narrating the amendment-#12 advance.
4. `docs/rebuild/plans/amendment-7-ac1-removal.md` — this plan (new file).

**Not touched:**
- `orchestrator/src/` — no source change needed; AC1 was asserting about already-landed source state.
- `workspace-bootstrap/` — no AC renumbering cascade (stub choice preserves AC3–AC6 numbering).
- `orchestrator/tests/test_no_sealed_amendments.py` BASELINE — the existing allowed_prefixes tuple already admits `orchestrator/`, `hands-off-lifecycle/`, and `docs/rebuild/components/orchestrator-bootstrap-unification/`. Confirmed against the `docs/rebuild/plans/` prefix too (already admitted per amendment #10's extension). No BASELINE bump needed; the test remains green because our diff (`BASELINE=7d462e3..SEAL_COMMIT`) already sits fully inside the allowed set.
- Actually, verify above: re-check `orchestrator/tests/test_no_sealed_amendments.py`'s `allowed_prefixes` tuple before commit. If `docs/rebuild/plans/` is absent, **add it** (that's a trivial widen for the existing prefix set; every other seal-diff test already admits `docs/rebuild/plans/`).

## 5. Seal-diff allowed-prefix verification

Per `orchestrator/tests/test_no_sealed_amendments.py`:
```
allowed_prefixes = (
    "orchestrator/",
    "hands-off-lifecycle/",
    "workspace-bootstrap/",
    "self-upgrade/",
    "memory-system/",
    "docs/rebuild/components/orchestrator-bootstrap-unification/",
    "docs/rebuild/components/namespaced-labels-and-bootout/",
    "docs/rebuild/plans/",
    "data/",
)
```
`docs/rebuild/plans/` already present → plan doc lands clean.

Per `hands-off-lifecycle/tests/test_cross_cutting.py` H19: allowed top-level buckets include `docs` → docs paths land clean.

Other sealed components' seal-diff tests (`memory-system/`, `workspace-bootstrap/`, `telegram-interface/`, etc.): their `BASELINE..SEAL_COMMIT` ranges are frozen behind their current sidecar values; our new commits land after those ranges and cannot fall into their diffs.

## 6. BASELINE advances

- `orchestrator/tests/test_no_sealed_amendments.py` — **advance** `7d462e3` → `a3bbdcd` (pre-amendment tip = amendment #9's seal). Intervening amendments #8/#9/#11 did not touch `orchestrator/`, but they landed paths outside this component's `allowed_prefixes`; re-pinning narrows the diff to amendment #12's own surface. The SEAL_COMMIT sidecar in `orchestrator/tests/` advances from `9373444` → amendment-#12 code-commit SHA in the seal commit.
- `hands-off-lifecycle/tests/test_cross_cutting.py` — **advance** `b9e1f96` → `a3bbdcd` (pre-amendment tip = amendment #9's seal). The SEAL_COMMIT sidecar in `hands-off-lifecycle/tests/` advances from `4f8b933` → amendment-#12 code-commit SHA in the seal commit.

## 7. Test-count expectations

| Suite | Before | After | Delta |
|-------|-------:|------:|------:|
| orchestrator | 74 | 73 | −1 (AC1 test deleted) |
| hands-off-lifecycle | 67 | 67 | 0 |
| workspace-bootstrap | 86 | 86 | 0 |

Any other delta on orchestrator = halt trigger (means AC1 was load-bearing).

## 8. Build order

1. Write this plan (done — this file).
2. Edit `orchestrator/tests/test_bootstrap_unification.py` — delete AC1 test + helper + update docstring.
3. Edit `docs/rebuild/components/orchestrator-bootstrap-unification/proposal.md` — withdraw AC1 stub + behaviour-count update + amendment-history note.
4. Advance `hands-off-lifecycle/tests/test_cross_cutting.py` BASELINE.
5. Run all three test suites; confirm counts 73 / 67 / 86 and all pass.
6. Amendment commit: `fix(orchestrator, hands-off-lifecycle): orchestrator-bootstrap-unification AC1 removal (amendment #12)`.
7. Write SEAL_COMMIT sidecars to the amendment-commit SHA.
8. Append amendment-cycle notes to SEAL_COMMIT sidecars if the pattern uses them (orchestrator + hands-off-lifecycle).
9. Seal commit: `chore(seals): orchestrator-bootstrap-unification-ac1-removal seal — orchestrator + hands-off-lifecycle at <sha>`.

## 9. Halt triggers

- Deleting the AC1 test causes any OTHER test to fail. Would indicate AC1 was load-bearing despite being a static grep (e.g. sharing helpers with other tests). Mitigation in plan: the `_ORCHESTRATOR_SRC` helper is scoped to AC1's function only; no other AC uses it.
- AC-renumbering cascades into `workspace-bootstrap/`. Prevented by the stub choice (§3 above).
- More than two sealed components need edits. The only sealed components in scope are `orchestrator/` and `hands-off-lifecycle/`. If the proposal doc edit were to cascade into any other component's docs, halt.
- AC2's poison-bomb does NOT actually fail if the orchestrator re-introduced `load_and_register(cfg.root_dir/"bootstrap.py", self)`. Verification: AC2 writes `raise RuntimeError(...)` into the workspace bootstrap.py; if `_startup` loaded it, Python's import machinery would execute the raise, the startup coroutine would propagate the exception, `orch.run()` would return a non-zero exit code, and both the `exit_code == 0` assertion and the `bootstrap_refused` absence assertion fail. Structurally tight.

## 10. ODD compliance check (run at close)

- AC1's replacement (nothing — just the stub) does not introduce new non-objective code; it removes a method-in-acceptance test.
- AC2 is the sole behaviour complement; it remains a visible-invariant assertion.
- No new silent exception branches introduced.
- Proposal diff is docs-only after AC1 removal; source/tests diff is −1 function + docstring update in `orchestrator/tests/`.
- Seal-diff tests stay green (scope-verified in §5).
