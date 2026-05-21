# Amendment #14 — `skip-launchctl-dead-code-removal` plan

**Status:** plan (written before any source edit, per plan-before-code CDC).
**Branch:** `pos-v2` at HEAD `079258f` (`docs(future-ideas): capture GLiNER2, context-load gate, and slug-collision ideas`).
**Amends:** the pyyaml-reachability amendment (#5, sealed at `9b4bcd3`) and its follow-up (amendment #5 follow-up at `9b4bcd3`) which together introduced and documented the `POS_V2_SKIP_LAUNCHCTL` integration-test opt-out in `hands-off-lifecycle/hooks/first_run_helper.py` plus the source-grep test `test_skip_launchctl_env_var_is_honoured_by_helper_source` in `hands-off-lifecycle/tests/test_pyyaml_reachability.py`.
**Motivation:** prior audit confirmed `POS_V2_SKIP_LAUNCHCTL` has ZERO live setters anywhere in the repo: not in any shell script, not in any test fixture, not in any CI config, not in any shipped doc. Its sole consumer is a read in `first_run_helper.py:1406`, asserted by a source-grep test at `test_pyyaml_reachability.py:384-401`. The source-grep test is method-in-acceptance (ODD §8.2 rule 9 violation); the env-var read itself is §2.5 orphan code (code for cases the objectives do not name — the amendment-#4 validation harness that was supposed to set the flag does not exist in the tree). The clean state is "env var gone, associated test gone, no replacement."

---

## 1. Objective

Delete the `POS_V2_SKIP_LAUNCHCTL` env-var read, its propagation through `_invoke_first_run_scaffold`, the three conditional skip branches in `_run_bootstrap` that fire on it, the justifying comment block, and the source-grep test that pins the wiring in place. No replacement behavioural test — no named AC covers this behaviour; no integration harness in-tree sets the var.

## 2. Scope

**Primary surface:** `hands-off-lifecycle/` (source + test deletions).

**Secondary surfaces:**
- `docs/plans/skip-launchctl-dead-code-removal.md` — this plan.

**Dependency fence:** no other sealed component touched. If the builder finds it needs to touch anything else, HALT and report.

## 3. Files touched

1. `hands-off-lifecycle/hooks/first_run_helper.py`
   - Delete the comment block at lines 1390–1405 (the 15-line stanza beginning "Integration-test opt-out:" and ending "…amendment #5 wires it up.").
   - Delete line 1406 (the `skip_launchctl = bool(os.environ.get("POS_V2_SKIP_LAUNCHCTL"))` read) and the blank line separating it from the comment block.
   - Replace `service_bootstrap=not skip_launchctl` at line 1418 with `service_bootstrap=True` (the kwarg must remain — the scaffold signature accepts it; we are removing the branch, not the arg).
   - Delete the `if skip_launchctl: ... else:` branching at lines 1434–1440 (keep only the else-branch contents, de-indented) so the health poll always runs.
2. `hands-off-lifecycle/tests/test_pyyaml_reachability.py`
   - Delete the function `test_skip_launchctl_env_var_is_honoured_by_helper_source` at lines 384–401 together with the preceding blank line separator (lines 383–401 inclusive).
3. `docs/plans/skip-launchctl-dead-code-removal.md` — this plan (new file).

**Not touched:**
- `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run` — historical narrative; the mention of `POS_V2_SKIP_LAUNCHCTL` there is a record of the pyyaml-reachability amendment's scope, not live code. No change.
- `hands-off-lifecycle/tests/SEAL_COMMIT` — touched only in the **seal commit** (step 2 of the cycle), not the amendment commit.
- `hands-off-lifecycle/tests/test_cross_cutting.py` — `BASELINE` advance happens in the amendment commit (pre-amendment tip = `079258f`, the GLiNER2 docs commit); `SEAL_COMMIT` sidecar + seals/ narrative advance in the seal commit.
- Any other sealed component's source or tests — scope creep.

## 4. Seal-diff allowed-prefix verification

The 5 existing `test_no_sealed_amendments.py` tests (`telegram-interface/`, `orchestrator/`, `memory-system/`, `cost-governance/`, `workspace-bootstrap/`) each gate `BASELINE..SEAL_COMMIT` with their sidecar-pinned SEAL_COMMIT SHAs (all historical, pre-this-amendment). Our new commits land after those pins, so the frozen diff windows do NOT include our amendment — no test needs its allowed_prefixes extended. Spot-check: all 5 already admit `hands-off-lifecycle/` and `docs/plans/` regardless, so even if a future seal re-pin swept these in, the diff would still be clean.

`hands-off-lifecycle/tests/test_cross_cutting.py` H19 admits `hands-off-lifecycle` and `docs` top-level buckets. Our amendment touches exactly those two buckets — H19 stays green.

## 5. BASELINE advances

- `hands-off-lifecycle/tests/test_cross_cutting.py` — **advance** `BASELINE` from `5c49e27` to `079258f` (pre-amendment tip = `docs(future-ideas): capture GLiNER2, context-load gate, and slug-collision ideas`). This narrows the H19 diff window to amendment #14's own surface. Add a BASELINE-history comment block narrating the advance.
- `hands-off-lifecycle/tests/SEAL_COMMIT` — advance from `9e3776b` to the amendment-#14 code-commit SHA in the **seal commit** (step 2).
- `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run` — append an amendment-cycle narrative in the seal commit (step 2).

## 6. Test-count expectations

| component | before | after | delta |
|---|---|---|---|
| hands-off-lifecycle | 67 | 66 | −1 |
| workspace-bootstrap | 86 | 86 | 0 |
| memory-system (ignoring temporal/claude_print_client collection-error modules) | 45 | 45 | 0 |
| orchestrator test_no_sealed_amendments | 2 | 2 | 0 |
| telegram-interface test_no_sealed_amendments | 2 | 2 | 0 |
| memory-system test_no_sealed_amendments | 2 | 2 | 0 |
| cost-governance test_no_sealed_amendments | 1 | 1 | 0 |
| workspace-bootstrap test_no_sealed_amendments | 2 | 2 | 0 |

The −1 in hands-off-lifecycle is the deletion of `test_skip_launchctl_env_var_is_honoured_by_helper_source`. No new tests added — no AC names replacement behaviour.

## 7. Commit cycle

Two commits, no `--amend`.

1. **Amendment commit.** `fix(hands-off-lifecycle): remove POS_V2_SKIP_LAUNCHCTL dead code (amendment #14)`. Contents: source edits in `first_run_helper.py`, test deletion in `test_pyyaml_reachability.py`, BASELINE advance + history comment in `test_cross_cutting.py`, this plan. Tests green before commit.
2. **Seal commit.** `chore(seals): skip-launchctl-dead-code-removal seal — hands-off-lifecycle at <amendment-sha>`. Bumps `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run` (appended narrative) + `hands-off-lifecycle/tests/SEAL_COMMIT` sidecar to the amendment-commit SHA.

## 8. Halt triggers

- Deleting the env-var read causes a passing test to fail → live consumer exists somewhere the audit missed. STOP, restore, report.
- Repo-wide grep for `POS_V2_SKIP_LAUNCHCTL` after the amendment commit finds any non-historical hit (allowed: the narrative in `seals/SEAL_COMMIT.true-first-run`). STOP, report.
- Any test outside `test_pyyaml_reachability.py` references `skip_launchctl` behaviour → scope ballooned. STOP, report.
- Any sealed component's seal-diff test fails after either commit → scope leak or allowed-prefix gap. STOP, investigate.
- Need to touch a sealed component other than `hands-off-lifecycle/` → scope creep. STOP, report.

## 9. Verification steps (post-edit, pre-commit)

1. Repo-wide grep for `POS_V2_SKIP_LAUNCHCTL` and `skip_launchctl` — expect the env-var string to appear only in `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run` (historical); the identifier to appear nowhere.
2. `../.venv/bin/python -m pytest -q` in `hands-off-lifecycle/`, `workspace-bootstrap/`, `memory-system/` (with `--ignore=tests/test_temporal.py --ignore=tests/test_claude_print_client.py --ignore=scripts`).
3. Each of the 5 `test_no_sealed_amendments.py` tests green.
4. After seal commit: re-run (2) + (3) to confirm sidecar advance didn't open a new diff gap.

