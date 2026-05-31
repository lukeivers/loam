# STATE-OF-LOAM operative-reality record + substrate-audit gate (N2) — apply ladder

2026-05-31. Roadmap N2 (R-1 + R-3) per
`docs/plans/state-of-loam-record-and-substrate-audit-gate-slice-plan.md`.
Builds the standing mechanism that would have caught today's
built-≠-live drift automatically: a single record DERIVED FRESH from
ground truth (git ref graph + per-component seal sidecars + live
runtime config + a cheap REAL probe for backend-class components) and
a comparator that surfaces any claim diverging from it.

Four forks ruled (built to, not re-opened):
  D1 = generate-fresh on every read (no persisted record — a cached
       record reintroduces the exact drift surface this slice kills).
  D2 = build the `loam audit` verb first (the testable real entry-
       point) + wire the release-gate arm this slice; the always-on
       plan-author hook is a fast-follow, out of fence.
  D3 = surface-only authoring arm (deferred); HARD-BLOCK release-gate
       arm; auto-heal deferred entirely (a false-positive auto-rewrite
       corrupts a canonical doc).
  D4 = structured status-fields only (bounded, low-false-positive);
       NL "rides existing X" prose-scanning is a separate later slice.

The load-bearing F2 carried: NOT every liveness fact is ref-derivable.
Static config alone mis-classifies a backend as live (the graphiti
case: MCP-wired + async queue present, but the consumer was a Protocol
shim that never ran → config said "wired", reality was dark). So a
backend-class probe does a cheap REAL probe (an import/call) and
classifies DARK on probe failure, even when config says wired.

What landed (all under framework/tools/loam/ — the loam-cli fence):
  - `loam_cli/audit/probe.py` — the ground-truth classifiers:
    `classify_build_status` (built/sealed/merged from `merge-base
    --is-ancestor` against a seal sidecar SHA), `classify_hook_wired`
    (wired/dark from live settings.json), `classify_backend_liveness`
    (wired/dark from config AND a real probe — the F2).
  - `loam_cli/audit/record.py` — the generate-fresh record (D1):
    `generate_record` derives every row from ground truth on each
    call; `render_record` produces the terse always-loadable summary.
  - `loam_cli/audit/comparator.py` — the R-3 comparator:
    `compare_claim`/`compare_claims` (LIVE/DARK-side divergence on the
    Liveness partition; fail-safe on UNKNOWN / uncovered / unparseable)
    + `extract_claims_from_doc` (the bounded structured-status surface).
  - `loam_cli/audit/reconcile.py` — the FBM second entry point:
    `reconcile_stored_claim` routes a checkable stored claim through
    the SAME comparator; the finding is dated + scoped, never eternal.
  - `loam_cli/audit/loam_state.py` — the default canonical-repo probe
    registry (FBM hook marker, primary-persona + loam-cli seal
    sidecars, the loam-cli-runtime real backend probe).
  - `loam_cli/audit/cli.py` + the `audit` entry-point in pyproject —
    the `loam audit` verb (the real entry-point AC.SOL-PLANTED.1
    drives).
  - `loam_cli/release/gates.py` — the 8th gate `check_substrate_audit`
    appended to ALL_GATES + threaded through run_all (HARD-BLOCK; fail-
    safe: degrades to pass-with-caveat on its own failure, never a
    false RED that blocks a legit publish).

Proven: AC.SOL-RECORD.{1,2,3} (derived-not-authored, reflects-real-
change, terse), AC.SOL-PROBE.{1,2,3} (refs/config/real-probe + the
backend-config-says-wired-but-dark F2 case + FBM-reads-live on the live
repo), AC.SOL-GATE.{1,2,3} (divergence caught, agreement clean, composes
on ALL_GATES, release-gate HARD-BLOCK on a planted divergence),
AC.SOL-RECONCILE.{1,2} (the FBM second caller, dated+scoped finding),
and ★ AC.SOL-PLANTED.1 (outcome-altitude: the REAL `loam audit` verb
catches a planted dark-for-live divergence — NOT a unit test of the
inner status function). loam-cli component suite: 126 passed.
