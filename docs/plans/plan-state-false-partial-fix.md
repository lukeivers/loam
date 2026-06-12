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

- Plan+manifest commit: d17da709
- Source/test commits: 7a76fb4e (fix + AC.PSTATE.1-3 tests), 51114e69
  (AC.PSTATE.4-5 OA re-grounding)
- Apply commit: b7fc83d3
- Seal commit: **8671fd89** (2026-06-12, third invoke GREEN; clean
  tree, sidecars at 0989fc27). First halt (§16b finding 3, AC.α.8
  breach) RESOLVED per dispatcher ruling (a): corrective commit
  b5df9cbf (currency-cycle guard-list completion; primary-persona
  sweep GREEN, 1191 passed / 1 skipped / 0 failed). Second halt
  (§16b finding 4, hands-off-lifecycle AC.DCG.OA live-premise rot)
  RESOLVED per dispatcher ruling (a-durable): corrective plan
  7adb7e93 + corrective commit 0989fc27 (see finding 4 below).
- D-PSTATE.1: implemented as `_latest_evidence_is_seal()` checking
  `seal_evidence[0]`'s subject for the `chore(seals): ` prefix
  (evidence is newest-first by git-log order; HEAD-reachability by
  construction of the `git log` probe).
- All 5 ACs verified green at build time: 11 passed (loam-cli
  PSTATE+PSI suites), 2 passed (AC.PSI.OA re-grounded), 2 passed
  (AC.CLG.OA re-grounded), 34 passed (fixture-consumer sweep:
  PSI_2/3, WVS_MR_1, CLG_1-4).

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

## §16b Halt-and-surface findings (build/seal time)

3. **Seal HALTED (2026-06-12) — pre-existing AC.α.8 sweep breach,
   NOT caused by this cycle.** `loam amend seal` ran primary-persona's
   full suite;
   `test_AC_alpha_8_no_capability_content_outside_admitted_paths.py::test_AC_alpha_8_user_intent_phrasings_marker_only_in_admitted_paths`
   fails: the `[user-intent phrasings]` schema marker exists in 8
   non-admitted paths (docs/CLAUDE_CAPABILITIES.md, docs/STATE.md,
   framework/tools/capability-refresh/* — README, src x3, tests x2).
   Tier-0: all 8 carry the marker at this cycle's baseline 12cd606b;
   this cycle's diff (12cd606b..51114e69) is fully disjoint from them.
   Introduced by claude-leverage-program-s1-currency (apply 6c5dc5a2,
   seal c41f9473), whose fence did not run primary-persona's sweep, so
   the breach landed silently and surfaces here. NOT fixed in this
   cycle: extending the test's ADMITTED_PREFIXES maps to no AC.PSTATE.*
   (ODD §2.5) and the admitted-set judgment belongs to the CURRENCY
   plan's scope. Cycle state at halt: apply b7fc83d3 committed; seal
   WIP (3 SEAL_COMMIT sidecars modified + untracked
   docs/plans/sealed/plan-state-false-partial-fix.md) left uncommitted
   in-tree exactly as `loam amend seal` left it for re-invoke.
   Proposed resolutions for dispatcher ruling: (a) one-line
   ADMITTED_PREFIXES extension (capability-refresh tree +
   docs/CLAUDE_CAPABILITIES.md + docs/STATE.md) ratified as a CURRENCY
   follow-up, then re-invoke this seal; or (b) a separate corrective
   cycle on the CURRENCY plan first.

   **RESOLVED 2026-06-12 — dispatcher ruled option (a)** (basis:
   loose-AC/stale-guard analog of
   feedback_loose_AC_text_fix_AC_not_implementation; the currency plan
   sanctioned the surface, so the guard list completes, the content
   doesn't move). All 8 paths Tier-0-verified inside the currency
   plan's sanctioned surface before admitting: 7 of 8 carry the marker
   at currency seal c41f9473 and none at its baseline 266aa93c
   (component fence framework/tools/capability-refresh/ + the demoted
   docs/CLAUDE_CAPABILITIES.md, both in the currency manifest); the
   8th (docs/STATE.md, a currency universal_paths file + its named
   status-file target) gained the marker in the currency §14-backfill
   change-log entry 5e66b9ef describing D-CUR.4. Corrective commit
   b5df9cbf (NEW commit, attributed as currency follow-up).
   Primary-persona sweep GREEN after fix: 1191 passed, 1 skipped, 0
   failed.

4. **Seal HALTED AGAIN (2026-06-12) — second pre-existing sweep
   failure, NOT caused by this cycle: hands-off-lifecycle AC.DCG.OA
   live-premise rot.** The finding-3 re-invoke of `loam amend seal`
   passed loam-cli + primary-persona, then failed in
   hands-off-lifecycle:
   `tests/test_AC_DCG_OA_live_ledger_gate_replay.py::test_AC_DCG_OA_genuinely_open_question_passes_live`
   (1 failed, 722 passed, 5 skipped). The test's "genuinely open
   question" fixture — the frame-kernel dispatch-pack activation
   timing in pos3 — was authored 2026-06-09 21:54 CDT (aecb8e47) when
   that question WAS open; the live pos3 decision ledger RULED it
   2026-06-10 10:36 CDT
   (workspace/.loam/memory/decisions/2026-06-09-when-does-the-frame-kernel-dispatch-pack-hook-activate-live-.md,
   status: ruled), so the decision-claim gate now CORRECTLY steers on
   the fixture sentence and the test's premise is rotted — the gate is
   right, the fixture is stale. Tier-0: this cycle's
   hands-off-lifecycle diff (12cd606b..b5df9cbf) touches only
   test_AC_CLG_OA_live_repo_replay.py + the SEAL_COMMIT sidecar —
   fully disjoint from the DCG test; the first seal attempt (finding
   3) halted at primary-persona before ever reaching this suite, which
   is why it surfaces only now. Same disease this cycle's
   AC.PSTATE.4-5 cured in two OTHER tests (live-OA premise rot), but
   re-grounding the AC.DCG.OA fixture maps to no AC.PSTATE.* (ODD
   §2.5) and the fixture-choice judgment belongs to the decision-claim
   guard cycle's AC surface (aecb8e47). Cycle state at halt: corrective
   b5df9cbf + this backfill committed; seal WIP (3 SEAL_COMMIT
   sidecars modified + untracked
   docs/plans/sealed/plan-state-false-partial-fix.md) left uncommitted
   in-tree exactly as `loam amend seal` left it for re-invoke.
   Proposed resolutions for dispatcher ruling: (a-durable, preferred)
   re-ground the fixture to DERIVE a genuinely-open question from the
   live ledger at test time (premise can't rot again — the same shape
   AC.PSTATE.4-5 used), ratified as a decision-claim-guard follow-up,
   then re-invoke this seal; (a-quick) swap in a question that is open
   in the ledger today (rots again on its ruling); or (b) a separate
   corrective cycle on the decision-claim-guard plan first.

   **RESOLVED 2026-06-12 — dispatcher ruled option (a-durable).**
   Corrective plan docs/plans/dcg-oa-open-question-fixture-derivation.md
   (commit 7adb7e93, AC.DCGFIX.1-2); corrective commit 0989fc27 (NEW
   commit, attributed as decision-claim-guard follow-up, finding-3
   precedent — fence-internal test-only corrective inside this cycle's
   seal window). The test now derives its open question from the live
   ledger at test time: leg A uses a non-ruled record's own question
   (status read from the record file, independent of the module under
   test); leg B (the live path today — all 29 records ruled)
   synthesizes a subject of two absence-verified nonces + one ordinary
   word, structurally below the guard's >=2-token resolution
   threshold. Hands-off-lifecycle suite GREEN after fix: 723 passed,
   5 skipped, 0 failed. Seal re-invoke (third) GREEN: seal 8671fd89.
   This partially closes broken-suite item 5 (pos3 task #11): the
   DCG.OA rot is fixed durably; the other family items
   (archived-manifest-path suites, odd-extractor, FBMT1, loam-mode)
   remain task #11 scope, untouched per dispatch constraint.
