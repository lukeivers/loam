# plan-state false-partial fix — sealed verdict from seal-reachability

Per docs/plans/plan-state-false-partial-fix.md. The keep-pace
[plan-state] contributor reported fully-sealed-and-shipped plans as
"partially built" (Tier-0-proven 2026-06-11, four false build-dispatch
premises; live reproduction at plan time found the class is 18 plans):
the derivation granted the `sealed` verdict ONLY on sealed-archive
presence (docs/plans/sealed/<slug>.md), so every plan sealed before the
narrative-target archive convention reported `partially-sealed` forever
— seal commits were collected as evidence but never consulted for the
verdict.

THE FIX (D-PSTATE.1 — latest-evidence-seal-reachability): a plan is
`sealed` when its doc is in the sealed archive OR when its newest
slug-named evidence commit in the HEAD-reachable subject history is a
completed `chore(seals): <slug>` commit. Tag-ancestry was REJECTED as
the predicate (it would false-positive every sealed-local-awaiting-
publish plan; build-state is a seal-commit fact, publish-state is the
tag-ancestry question). "Newest evidence" (not "any seal") keeps
multi-cycle plans honest: a new apply after a prior seal re-enters
`partially-sealed`.

ACs: AC.PSTATE.1 (seal-reachability verdict, fixture), AC.PSTATE.2
(in-flight behavior preserved, fixture), AC.PSTATE.3 ★ outcome-altitude
(production derive_plan_states("loam") against the LIVE repo derives
the four dispatch-named regression fixtures — slice2-swarm,
deep-role-research-provider, egress-consent-core-and-bug-report,
dev-pattern-simplifications-1 — as sealed, independently git-verified),
AC.PSTATE.4 (live surfacing/query never report a seal-reachable plan
as partially built; re-grounded AC.PSI.OA test), AC.PSTATE.5 (the
06-09 claim-guard live replay holds without requiring a live partial
plan; re-grounded AC.CLG.OA test).

Fence: loam-cli (source+tests); primary-persona + hands-off-lifecycle
(tests-only OA re-grounding). Derivation line: INSTANCE of
feedback_published_state_only_from_git_refs applied to the keep-pace
surface itself (FIDRAFT F-PLANSTATE-FALSE-PARTIAL).
