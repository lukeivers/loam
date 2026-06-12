# DCG.OA open-question fixture — derived from the live ledger at test time

Working directory: /Users/lukeivers/loam (canonical loam, branch main).

## §1 Objective

`test_AC_DCG_OA_genuinely_open_question_passes_live` establishes its
"genuinely open question" premise FROM the live ledger AT TEST TIME —
never from a hardcoded question that a later ruling can rot — while
preserving the protective intent exactly: a draft calling a genuinely
open question open draws no decision steer through the production gate
entry point against the REAL live ledger, with no pre-arranged state.

## §2 Predecessors / context

- The test was authored in the decision-claim-guard cycle (aecb8e47,
  2026-06-09) hardcoding the frame-kernel dispatch-pack activation
  timing as its open question. The live pos3 ledger RULED that question
  2026-06-10 10:36 CDT, so the gate now CORRECTLY steers on the fixture
  sentence and the test's premise is rotted — the gate is right, the
  fixture is stale. Tier-0 reproduced 2026-06-12 under the repo venv:
  1 failed / 1 passed in the OA file.
- Surfaced twice independently (PB-retirement §status caveat; the
  plan-state seal halt — plan-state-false-partial-fix §16b finding 4).
  Item 5 of the broken-suite family (pos3 task #11). Dispatcher ruled
  resolution (a-durable): derive the open question from the live
  ledger at test time.
- Derivation line: INSTANCE of the live-OA premise-rot disease
  AC.PSTATE.4-5 cured in two sibling tests (same cycle); same cure
  shape — premise established from live ground truth at run time.

## §3 Scope

In scope: the single test function
`test_AC_DCG_OA_genuinely_open_question_passes_live` (+ its derivation
helpers and the module docstring) in
`framework/hands-off-lifecycle/tests/test_AC_DCG_OA_live_ledger_gate_replay.py`.

Out of scope: the gate / claim-guard production code (the gate is
behaving correctly); the replay leg
`test_AC_DCG_OA_reopened_tilth_ruling_caught_live` (premise is a ruling
— rots only if the ruling is deleted, which the skip-guard covers); the
other broken-suite family items (archived-manifest-path suites,
odd-extractor, FBMT1, loam-mode — task #11); pos3's synced copy.

## §4 Acceptance criteria

AC family: **AC.DCGFIX.*** (scope-descriptive).

| AC | Outcome | Verification |
|----|---------|--------------|
| AC.DCGFIX.1 ★ outcome-altitude | Through the production entry point (`gate()`, hook runtime cwd = live workspace, no pre-arranged state) a draft asserting open a question whose openness is established INDEPENDENTLY of the module under test, from the REAL live ledger at test time, draws no decision steer. Premise derivation: (leg A, preferred) the question of a live record whose `status:` line — read directly from the record file — is not `ruled`; (leg B, when no such record exists, the live-today path) a synthesized question whose subject tokens are nonces + at most one ordinary word, each nonce verified absent from every live record file, so it structurally cannot resolve to any ruling (conservative full-text superset of the guard's declared-vocabulary resolution). Either leg's premise cannot rot: a later ruling changes what is DERIVED, never falsifies what was hardcoded. | the re-grounded test, run live under the repo venv |
| AC.DCGFIX.2 | The replay leg (Tilth ruling steered) and the full hands-off-lifecycle suite are green with the fix; the rotted hardcoded fixture sentence no longer appears in the file. | full component suite run + grep |

Ladder-up: AC.DCGFIX.* → AC.DCG.2's genuinely-open-passes contract →
the protection floor of Lens 0 (the gate must not over-steer truthful
drafts) — the DCG suite's protective objective, unchanged.

## §5 Fence + ship shape

hands-off-lifecycle **tests only** — one file. House precedent
followed (named per dispatch): the plan-state cycle's finding-3
corrective pattern — a fence-internal test-only corrective lands as a
NEW plain commit inside the in-flight plan-state seal window
(attributed as a decision-claim-guard follow-up), and the
`loam amend seal` re-invoke picks it up; no separate amendment cycle.
The plan-state fence (§5 of that plan) already admits
hands-off-lifecycle tests. No `git commit --amend`; LOCAL only; the
in-tree seal-WIP (3 SEAL_COMMIT sidecars + untracked seal narrative)
is never swept into the corrective commit (explicit-path staging only).

## §6 Halt triggers

- A THIRD pre-existing failure at the seal re-invoke (halt + surface
  with the finding discipline; do not fix unruled scope).
- The derivation cannot establish a rot-proof premise (e.g. ledger
  unreadable in a way the skip-guard doesn't cover).

## §14 Method-decision register

- Plan commit: 7adb7e93
- Corrective commit: 0989fc27 (picked up by the plan-state seal
  re-invoke, seal 8671fd89; AC.DCGFIX.2 verified — DCG suite 21
  passed, full component suite 723 passed / 5 skipped / 0 failed,
  rotted fixture grep count 0)
- Leg selection at build time: live ledger holds 29 records, ALL
  `status: ruled` — leg B (synthesized-absent) is the live path today;
  leg A exercises automatically whenever a non-ruled record exists.
