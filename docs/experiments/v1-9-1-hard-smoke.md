# v1.9.1 HARD smoke writeup — MSC3 cold-clone test fixture fix

**Date:** 2026-07-01. **Release:** v1.9.1 — PATCH increment over published
v1.9.0 (`next_PATCH(v1.9.0) = v1.9.1`). Objective: close the long-standing
cold-clone failure of `test_AC_MSC_3_canonical_claude_dev_md_carries_named_surface`.
Single test-fixture fix; no production-code change.

**Staging topology:** built directly on `main` in the canonical tree
`/Users/lukeivers/loam`. No concurrent session owns the canonical tree this
cut; no isolated worktree needed.

**Release HEAD at smoke:** `8f6e49cd` — `main` tip after the seal commit.
**Reconcile (Tier-0):** `git rev-list --left-right --count origin/main...HEAD`
at smoke = `0 4` (4 commits ahead of remote: plan+manifest commit, fix commit,
apply commit, seal commit — all in the v1.9.1 amendment window, zero divergence).
**Last published (Tier-0, git ref):** `v1.9.0` tag `d8eb3ae3` (reachable from HEAD as ancestor).
**Secret scan:** no new secrets introduced (PATCH is test-fixture only; no
source, config, or credential file touched).
**Subscription mode** — no `ANTHROPIC_API_KEY`; no `anthropic` SDK.

**Aggregate verdict: GREEN.**

---

## §1 — Probe design

PATCH smoke: targeted test-fixture fix with no production-code change. The
full HARD smoke (cold-clone install + `loam --version` + spawn-isolated
`claude -p`) is a per-MINOR gate per `feedback_hard_smoke_per_minor_before_publish`.
For a PATCH: (a) verify the fixed test passes from a cold-clone equivalent
environment; (b) run the primary-persona regression suite; (c) verify the
seal-diff test passes; (d) run the `loam release v1.9.1 --dry-run` gates.

## §2 — Diagnosis (Tier-0)

Root cause verified against the `.scratch/smokes/v1-9-0-smoke/` cold clone
(Tier-0 rerun):

```
FAILED test_AC_MSC_3_canonical_claude_dev_md_carries_named_surface
AssertionError: ...payload head=''
```

Mechanism: `_read_dev_intent_inner` in `loam_mode/session_start.py` checks
`personas_dir.is_dir()` before iterating. In the dev-tree,
`workspace/personas/primary/` exists as real user state (not git-tracked).
In a cold clone, this directory is absent → function returns `"absent"` →
user mode → empty payload → assertion fails.

Classification: **TEST-CORRECTNESS** (not a behavior bug). The behavior is
correct; the test fixture was incomplete: `reader` injection alone cannot
override a directory-existence check.

## §3 — Fix (single test-fixture edit)

`framework/primary-persona/tests/test_AC_MSC_3_named_thread_surface_in_corpus.py`:

- Added `tmp_path: Path` parameter to
  `test_AC_MSC_3_canonical_claude_dev_md_carries_named_surface`.
- Before the emit call: creates `tmp_path/workspace/personas/loam/contract.yaml`
  (empty file; reader supplies content).
- Changed `emit_session_start_context(repo_root, reader=_reader)` to
  `emit_session_start_context(tmp_path, reader=_reader)`.

No production-source change. No other file changed in-fence.

## §4 — Test evidence

**4 MSC_3 tests (dev-tree):** 4 passed.

**4 MSC_3 tests (cold-clone equivalent — `.scratch/smokes/v1-9-0-smoke/`):**
Verified Tier-0 by copying the fixed test into the cold-clone smoke and running
against its venv:

```
4 passed in 0.60s
```

Previously `test_AC_MSC_3_canonical_claude_dev_md_carries_named_surface`
failed with `payload head=''`; now passes.

**Seal test:** `test_no_sealed_amendments.py` — 2 passed.

## §5 — Seal evidence

- Apply commit: `26c6be28`
- Seal commit: `8f6e49cd`
- SEAL_COMMIT sidecar (Tier-0): `26c6be28`
- Seal narrative: `docs/plans/sealed/v1-9-1-msc3-cold-clone-fix.md`

Seal-diff `b9422876..26c6be28` (BASELINE → SEAL_COMMIT): only
`framework/primary-persona/tests/` and `docs/plans/` paths changed —
both within allowed prefix set per the seal test's allowed_prefixes tuple.

## §6 — Gate evidence

Targeted regression only (PATCH, test-fixture-only, no production-source
change, no install-graph change). `loam --version` continues to report
`1.9.0` (pyproject versions do NOT advance on PATCH per D-NFCLEAN.4 +
D-SDPD — PATCHes ride predecessor MINOR). The `loam release v1.9.1 --dry-run`
gates are verified at §7.

## §7 — `loam release v1.9.1 --dry-run` gates

Captured post-bookkeeping (see §8 for final dry-run run):

| Gate | Verdict | Evidence |
|---|---|---|
| 1 hard-smoke | **GREEN** | GREEN aggregate-verdict token at this writeup path |
| 2 acs-verified | **GREEN** | AC.MSCCF.1/2/S all GREEN in plan-doc §13 |
| 3 state-shipped | **GREEN** | v1.9.1 marked SHIPPED LOCAL in `docs/STATE.md` |
| 4 clean-tree | **GREEN** | working tree clean (all bookkeeping committed) |
| 5 branch-main | **GREEN** | on branch `main` |
| 6 seal-reachable | **GREEN** | seal `8f6e49cd` reachable from HEAD |
| 7 migration-declared | **GREEN** | `v1-9-1-msc3-cold-clone-fix.migration.yaml` declares `version: v1.9.1` + `operation: no-op` |
| 8 substrate-audit | **GREEN** | no shipping-status claim diverges from the derived STATE-OF-LOAM record |
| 9 boundary-respected | **GREEN** | no framework-code write lands user-state outside the two declared homes |

**9 GREEN / 0 RED.**

## §8 — Verdict

**GREEN on all smoke dimensions.** Single-test-fixture fix; diagnosis
confirmed Tier-0 against cold-clone smoke; 4 MSC_3 tests green in both
dev-tree and cold-clone equivalent; seal passes; release gates satisfied.
The public tag + push + GitHub Release proceeds ONLY under the owner's
explicit command (`loam release v1.9.1 --release`).
