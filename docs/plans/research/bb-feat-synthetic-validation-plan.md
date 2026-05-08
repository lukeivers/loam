# BB-feat (#54) — synthetic-validation test plan

**Status:** test-plan, post-build validation. 2026-04-26.
**Working directory:** /Users/lukeivers/ivers-corp-pos-v2/
**Scope:** `self-upgrade/tests/` only (validation, no source edits).

## Why this exists

Amendment #54 (commits 0737e7c + 1fd826a + 83d830c) landed clause-(h)
canonical-pull + LLM-merge gate with 53 net-new tests. Before Luke runs
the manual upgrade test on `pos3`, this plan adds synthetic
integration coverage for the six milestone-critical scenarios the
existing tests do NOT exercise end-to-end through the CLI surface:

1. **Class A preservation** — workspace-state survival across an
   actual `pos upgrade --canonical` invocation (existing test covers
   the helper function only; no CLI-level proof).
2. **Class B mixed-customisation** — `memory.yaml`-class semantics
   through `resolve_clause_h_inferred` (existing tests cover the
   `classify()` function; no end-to-end B-resolution test).
3. **Class C framework-only** — covered adequately at unit level; no
   gap to fill.
4. **Audit log written** — real-world expectation: `<workspace>/.pos/...
   audit.yaml` exists after an upgrade; existing tests cover only the
   YAML round-trip + sort, not the disk-write side-effect of a
   complete upgrade.
5. **Idempotency** — re-running converges; existing test checks
   in-memory `Resolution.PENDING` skip but not full re-invocation.
6. **Backward-compat** — `--staging-dir` byte-identical to pre-#54;
   existing tests cover argparse + dry-run only, not full CLI flow.

## Coverage map (existing tests → 6 areas)

| Area | Existing coverage | Gap |
|---|---|---|
| 1. Class A | `test_clause_h_class_a_preserved` (helper-only); `test_classify_class_a_workspace_state` (classify-only) | No CLI-level invocation proving Class A survives an actual `pos upgrade --canonical` halt-on-conflict path |
| 2. Class B | `test_classify_class_b_operator_pref` (classify-only) | No `resolve_clause_h_inferred` test exercising the LOCAL_MODIFIED_ONLY → ACCEPT_UPSTREAM and the modified → KEEP_LOCAL branches with `memory.yaml` |
| 3. Class C | `test_clause_h_class_c_invokes_resolver`; `test_classify_class_c_default` | Adequate |
| 4. Audit log | `test_round_trip_inferred_entry`, `test_sorted_low_confidence_first` | No end-to-end proof that audit YAML is written under workspace path on the resolved-then-blocked-on-pending path through the CLI |
| 5. Idempotency | `test_clause_h_already_resolved_skipped`, `test_write_default_if_absent_idempotent` | No end-to-end re-run test through the CLI |
| 6. Backward-compat | `test_argparse_backward_compat_staging_dir_only`, `test_dry_run_prints_plan` | No full-CLI-flow comparison |

## Test additions — `tests/test_bb_feat_synthetic_validation.py`

One new file. Each test sets up a synthetic workspace + canonical
tmpdir, invokes via the actual `cli.main(["upgrade", ...])` surface,
asserts outcomes against AC.H.* + the dispatch's stated milestone.

1. **`test_class_b_workspace_modified_keeps_local`** — fills the Class B
   `resolve_clause_h_inferred` gap (modified-side workspace wins).
2. **`test_class_b_workspace_unmodified_accepts_canonical`** — fills
   the other Class B branch.
3. **`test_cli_canonical_class_a_preserved_audit_written`** — CLI-level
   integration: workspace has Class-A change vs canonical; canonical
   pull resolves it as KEEP_LOCAL; the conflict report (audit) is
   written and contains the resolution; backward-compat with
   `--staging-dir` is byte-identical at the report level.
4. **`test_cli_canonical_pending_writes_audit_yaml`** — when clause-h
   resolves some but Class-C conflicts remain pending (no resolver
   wired), audit YAML lands at expected path.
5. **`test_cli_canonical_idempotent_rerun_no_resolver_calls`** —
   convergent idempotency on re-run via CLI: feed a prior conflict
   report through `--conflicts-from`; resolver is NOT re-invoked.
6. **`test_cli_staging_dir_backcompat_byte_identical`** — full CLI run
   with `--staging-dir` (no `--canonical`) produces the same conflict
   report as before; clause-h is no-op.

## Halt-and-surface findings (from coverage analysis pre-test-write)

These are surfaced for Luke's ruling — NOT silently fixed in this
validation pass:

- **AC.H.5 vs implementation gap.** AC.H.5 says "Every clause-(h)
  upgrade writes `<workspace>/.pos/upgrade/<tag>/audit.yaml`" but
  `cli.py:cmd_upgrade` only writes the conflict report on
  BudgetExhausted, ResolverFailure, or `report.has_pending()` — a
  successful clause-h pass that resolves all conflicts produces NO
  on-disk audit. Real-world impact: after a clean upgrade, Luke
  cannot read what the resolver decided. The existing tests cover
  the in-memory mutation only.

- **AC.H.8 state.yaml absent.** AC.H.8 says "State is recorded at
  `<workspace>/.pos/upgrade/state.yaml`". No such file is written
  anywhere in `self-upgrade/src/`. Idempotency works only if the
  caller passes `--conflicts-from <prior-yaml>` on re-run; the
  framework does not auto-discover prior state.

- **Audit-log path divergence.** Plan §2 says
  `<workspace>/.pos/upgrade/<tag>/audit.yaml`; implementation writes
  `~/.pos/framework/history/<tag>-conflicts.yaml`. The `~/.pos`
  base is global, not workspace-local. For Luke's "upgrade on
  pos3 doesn't lose workspace-specific content" milestone this is
  the difference between an audit that lives next to the
  workspace's persona/MCP files vs one that lives in a global
  framework directory. **Not a bug per the implementation contract,
  but a divergence from the plan text.**

The new tests assert the AS-BUILT behavior (audit at
`paths.conflicts_yaml(tag)`) so they pass against the current
implementation. The halt-and-surface findings flag the AC vs impl
divergence for owner ruling on whether a follow-on amendment is
needed.

## Out of scope

- Actual LLM call against the live Claude SDK adapter.
- Substrate restart / orchestrator IPC integration.
- A pos3-shaped real fixture (synthetic structure suffices).
