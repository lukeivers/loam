# v1.9.1 — MSC3 cold-clone test fixture fix

Per docs/plans/v1-9-1-msc3-cold-clone-fix.md.
`test_AC_MSC_3_canonical_claude_dev_md_carries_named_surface` failed in
cold-clone environments because the test's `reader` injection was
insufficient: `_read_dev_intent_inner` checks `personas_dir.is_dir()`
before iterating, and the reader is never consulted when the directory
is absent. In the dev-tree `workspace/personas/` exists as real user
state; in a cold clone it does not.

THE FIX: add `tmp_path: Path` parameter to the test; create a minimal
`workspace/personas/loam/contract.yaml` (empty) at `tmp_path`; route
`emit_session_start_context` through `tmp_path`. The reader still
supplies all file content (dev_intent=yes YAML for the contract;
CLAUDE.dev.md text for the dev-extension path). Passes in both
dev-tree and cold-clone. Classification: TEST-CORRECTNESS (not a
behavior bug — the behavior is correct).

ACs: AC.MSCCF.1 (passes without workspace/personas/ at workspace_root),
AC.MSCCF.2 (other 3 MSC_3 tests unaffected), AC.MSCCF.S ★ (all 4
MSC_3 tests pass in dev-tree and cold-clone equivalent).

Fence: primary-persona/tests only. No production-source change.

Predecessor: b9422876 (docs(release): v1.9.0 post-publish backfill).

## §4 — Acceptance criteria

### AC.MSCCF.1

`test_AC_MSC_3_canonical_claude_dev_md_carries_named_surface` passes when
`workspace/personas/` is absent from the test's `workspace_root`
(cold-clone equivalent). The test creates a minimal
`workspace/personas/loam/contract.yaml` on disk at `tmp_path`, routes
the `emit_session_start_context` call through `tmp_path`, and the
assertion `"docs/FUTURE_IDEAS_DRAFT.md" in payload` holds.

### AC.MSCCF.2

No regression in the other 3 MSC_3 tests
(`test_AC_MSC_3_named_surface_in_discovered_corpus`,
`test_AC_MSC_3_present_surface_reflected_in_session_fields`,
`test_AC_MSC_3_absent_surface_graceful_missing`), which remain parameterless
and do not rely on `workspace/personas/`.

### AC.MSCCF.S

All 4 `test_AC_MSC_3*` tests pass in BOTH the dev-tree AND a cold-clone
equivalent environment (Tier-0 verified against `.scratch/smokes/v1-9-0-smoke/`).

outcome-altitude:true: AC.MSCCF.S

## §13 §status

| AC | Verdict |
|---|---|
| AC.MSCCF.1 | GREEN |
| AC.MSCCF.2 | GREEN |
| AC.MSCCF.S | GREEN |
