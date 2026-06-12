# plan-state false-partial fix — sealed verdict from seal-reachability, not archive presence

Working directory: /Users/lukeivers/loam (canonical loam, branch main).

## §1 Objective

A plan whose newest slug-named build-evidence commit reachable from HEAD
is a completed `chore(seals): <slug>` commit derives `sealed` — never
`partially-sealed` ("partially built" at the contributor surface) — while
genuinely mid-cycle plans (apply landed, seal not yet) keep deriving
`partially-sealed`.

## §2 Predecessors / context

- The plan-state derivation shipped in the FBM correctness cycle, Slice 1
  (AC.PSI.1, `framework/tools/loam/src/loam_cli/audit/plan_state.py`);
  the contributor surface (AC.PSI.2/3) in
  `framework/primary-persona/src/loam/primary_persona/keep_pace/plans_state.py`;
  the claim guard (AC.CLG.*) consumes the query surface.
- THE DEFECT (Tier-0-reproduced 2026-06-12 via the production entry point
  `derive_plan_states("loam")` against the live repo): the `sealed` verdict
  is granted ONLY on sealed-archive presence (`docs/plans/sealed/<slug>.md`).
  Seal commits are collected as *evidence* but never consulted for the
  verdict — so every plan sealed before the `narrative.target →
  docs/plans/sealed/` convention (amendment #142 Scope A) reports
  `partially-sealed` forever. Live reproduction found **18** such false
  positives, every one with a `chore(seals): <slug>` commit as its newest
  evidence, including the four dispatch-named fixtures:
  - claude-p-to-insession-subagent-fanout-slice2-swarm (seal a315ed0b, in v1.1.0)
  - deep-role-research-provider (seal 44d85830)
  - egress-consent-core-and-bug-report (seal ffb99af2)
  - dev-pattern-simplifications-1 (seal 019cfca7)
- FIDRAFT capture: F-PLANSTATE-FALSE-PARTIAL (pos3
  docs/FUTURE_IDEAS_DRAFT.md, commit b739d0f8). Its "commit-count
  heuristic" cause-guess is corrected here: the count is rendering only;
  the verdict miss is archive-presence-only classification. Derivation
  line: INSTANCE of feedback_published_state_only_from_git_refs applied to
  the keep-pace surface itself.

## §3 Scope

In scope:

1. The verdict predicate in `loam_cli.audit.plan_state.derive_plan_states`
   (loam-cli component) + its AC tests.
2. Re-grounding the two live-repo outcome-altitude tests whose premise
   ("the live repo must carry a partially-sealed plan") is falsified by
   the fix flipping all 18 false partials to sealed:
   - `framework/primary-persona/tests/test_AC_PSI_OA_outcome_altitude_live_repo.py`
   - `framework/hands-off-lifecycle/tests/test_AC_CLG_OA_live_repo_replay.py`
   Both keep their filenames + original AC identity (AC.PSI.OA /
   AC.CLG.OA still verified at outcome altitude); the re-grounding edits
   map to AC.PSTATE.4 / AC.PSTATE.5.

Out of scope:

- The persona renderer / query / claim-guard logic (pure consumers of the
  verdict; no change needed — verified by consumer sweep at plan time:
  only `plan_state.py`, `plans_state.py`, `claim_guard.py` touch the
  verdict in production, and the latter two branch identically on
  sealed-or-partial).
- The FIDRAFT's `<backfill>`-placeholder idea: the derivation never reads
  plan prose (that is its design), so there is no placeholder path to fix.
- Archiving the 18 plan-docs into `docs/plans/sealed/` (a doc-hygiene
  backlog item, NOT the fix — the derivation must be correct for
  legacy-narrative plans regardless).
- pos3's synced framework copy (picks the fix up at next pos-sync).

## §4 Acceptance criteria

AC family: **AC.PSTATE.*** (scope-descriptive per convention).

| AC | Outcome | Verification |
|----|---------|--------------|
| AC.PSTATE.1 | A plan-doc in `docs/plans/` (NOT in the sealed archive) whose newest slug-named evidence commit is `chore(seals): <slug> …` derives `sealed`, purely from the git ref graph, with its evidence carried. | `framework/tools/loam/tests/test_AC_PSTATE_1_seal_reachability_verdict.py` (fixture repo) |
| AC.PSTATE.2 | Genuinely-in-flight behavior preserved: (a) apply-only evidence → `partially-sealed`; (b) a NEW apply commit after a prior seal (next cycle mid-flight) → `partially-sealed`; (c) no evidence → `no-build-evidence`; (d) sealed-archive presence → `sealed` regardless of evidence order. | `framework/tools/loam/tests/test_AC_PSTATE_2_inflight_preserved.py` (fixture repo) |
| AC.PSTATE.3 ★ outcome-altitude | Production entry point `derive_plan_states("loam")` (production registry, live repo, no pre-arranged state) derives `sealed` for all four regression fixtures named in §2; INDEPENDENT git verification (the test's own `git log` probe, never the module under test) confirms each fixture's newest slug evidence is a `chore(seals):` subject AND its doc is absent from the sealed archive — proving the new predicate (not archive presence) produced the verdict. | `framework/tools/loam/tests/test_AC_PSTATE_3_outcome_altitude_regression_fixtures.py` |
| AC.PSTATE.4 | The production surfacing entry points (`render_plans_block()`, `query_plan_state()`) against the live repo never report a seal-reachable plan as "partially built": no §2 fixture identity appears in a "partially built" line; the slice2 fixture queries as `sealed` with evidence; every reported-partial plan (if any) independently verifies as genuinely mid-cycle. | re-grounded `framework/primary-persona/tests/test_AC_PSI_OA_outcome_altitude_live_repo.py` |
| AC.PSTATE.5 | The 2026-06-09 claim-guard live replay holds WITHOUT requiring the live repo to carry a partial plan: a false-denial draft about a real evidence-backed plan draws a CG steer citing that plan + its REAL build-state; a true claim about a sealed plan passes un-steered. | re-grounded `framework/hands-off-lifecycle/tests/test_AC_CLG_OA_live_repo_replay.py` |

Ladder-up: AC.PSTATE.* → AC.PSI.1's derived-not-stored contract → the
protection floor of Lens 0 (never feed the user/persona invented state) →
AC.PO.1/AC.PO.2.

## §5 Sealed-component fence

- **loam-cli** (`framework/tools/loam/`) — source + tests.
- **primary-persona** (`framework/primary-persona/`) — tests only
  (AC.PSTATE.4 re-grounding).
- **hands-off-lifecycle** (`framework/hands-off-lifecycle/`) — tests only
  (AC.PSTATE.5 re-grounding).

Universal admissions: `docs/plans/` prefix; `CLAUDE.md`, `docs/STATE.md`.

## §6 Halt triggers

- Foreign commits land on main mid-cycle.
- A seal-test failure NOT caused by this cycle's edits.
- The consumer sweep in §3 turns out incomplete (a fourth production
  consumer of the verdict surfaces during edits).
- Weekly token-limit stall (expected-possible per dispatch; halt and
  resume, never swap).

## §7 Ship shape

Single amendment, one cycle. Commit ladder: plan+manifest (`docs(plans)`)
→ source+tests (`fix(loam-cli)` / `test(...)` commits, small) →
`loam amend apply` → `loam amend seal` → §14 backfill (`docs(plans)`).
LOCAL only — never pushed.

## §10 Named decisions

- **D-PSTATE.1 — the sealed-verdict predicate.** DECIDED:
  **latest-evidence-seal-reachability** — a plan is `sealed` when its doc
  is in the sealed archive, OR when its newest slug-named evidence commit
  in the HEAD-reachable subject history is a completed `chore(seals):
  <slug>` commit. (HEAD-reachability is by construction: the evidence
  probe is `git log` from HEAD.) REJECTED: tag-ancestry
  (`git tag --contains <seal>`) as the predicate — it reproduces the
  false-positive class for every sealed-local-awaiting-publish plan (the
  standard LOCAL-only window; e.g., THIS cycle's own seal until the next
  publish), and "build complete" is a seal-commit fact, not a publish
  fact. Tag-ancestry remains the right predicate for *published* claims
  (feedback_published_state_only_from_git_refs), which is a different
  question from build-state. "Newest evidence" (not "any seal exists")
  keeps multi-cycle plans honest: a new apply after a prior seal re-enters
  `partially-sealed`.

## §14 Method-decision register

Populated at build/seal time:

- Plan+manifest commit: 4e2447ab
- Source/test commits: 0bb0791e (fix + AC tests), 5151ed5a (OA re-grounding)
- Apply commit: ee46a5d6
- Seal commit: 718337ff
- D-PSTATE.1: implemented as `_EVIDENCE_SEAL_PREFIX` check on
  `seal_evidence[0]` (evidence is newest-first by git-log order).

## §15 Backwards-compat verification

- All existing `test_AC_PSI_1_*` tests pass unchanged (their fixtures
  end cycles with archive+seal or apply-only — both verdicts preserved).
- Fixture-injected consumer tests (`test_AC_PSI_2/3`, `test_AC_CLG_1/3`,
  `test_AC_WVS_MR_1`) pass unchanged (they fabricate states above the
  derivation seam).
- Component seal-tests (`test_no_sealed_amendments.py` /
  `test_cross_cutting.py`) green at seal.

## §16 Halt-and-surface findings (plan-authoring)

- The false-positive class is 18 plans, not 4 (Tier-0 live derivation at
  plan time) — fix shape unchanged; the four stay the named regression
  fixtures.
- The FIDRAFT cause-guess ("commit-count heuristic + stale `<backfill>`
  placeholders") was wrong in mechanism; corrected in §2. No scope
  change.
