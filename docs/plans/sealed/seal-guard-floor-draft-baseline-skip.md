# seal-guard-floor-draft-baseline-skip (PATCH) — the GUARD-SWEEP FLOOR's class-5 manifest-conformance sweep (AC.DPS1.13) wrongly couples every seal to every in-flight DRAFT plan's manifest validity: two sibling drafts (claude-leverage-program-s4b-wire baseline PENDING-S4A-SEAL; principle-foundation-structural-enforcement baseline PLAN_DOC_COMMIT) carry legitimate placeholder baselines that fail load_manifest's hex-SHA check, blocking unrelated seals. FIX (D-GFLOOR2.1): the sweep SKIPS any manifest whose baseline is not a resolvable commit-ish (non-hex placeholder OR hex-shaped-but-unresolvable draft marker); REAL resolvable-baseline manifests stay FULLY validated (a malformed applied/sealed manifest still blocks — that protection is the floor's point). locked-design-not-license on the floor sealed f7c1cc29. ★ outcome-altitude AC.GFLOOR2.3: the production seal entry-point against a real repo carrying a placeholder-baseline draft does NOT halt on it via the manifest-conformance sweep, AND a malformed real-baseline manifest still fails the sweep.

slug: seal-guard-floor-draft-baseline-skip
components: dev-sdlc
baseline: b14e279d
amendment-commit: cb3fd8d4da139cab71b07ac5355ead7c6fb1c844
plan-doc: docs/plans/sealed/seal-guard-floor-draft-baseline-skip.md
acs-satisfied: 3

Narrative body collapsed per cost-audit 2026-05-04 Recommendations A + B (manifest narrative collapse + seal-narrative compression) — see the plan-doc above for full rationale, AC family, and smoke results.
