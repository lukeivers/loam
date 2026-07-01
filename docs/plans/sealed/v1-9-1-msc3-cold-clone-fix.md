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
