# protection-matrix — re-bind the FM.SILENT-EGRESS row to the now-built egress-consent gate

## Objective

The FM.SILENT-EGRESS row in the failure-mode-guard matrix is STALE. It
states the egress-consent gate is "DESIGNED, not yet built" and carries
the unbuilt-guard shape (`guard_kind: none`, empty `guard_ref`,
`default_on: NONE`). That status is no longer true: `framework/egress-consent/`
is BUILT + SEALED — the fail-closed `EgressReleaseGate.release` choke point,
sealed at `2304dea`. The protection pillar must report the now-real guard
honestly. This amendment re-binds the row to the real sealed symbol using
the FM.COMMS-PATH-DEAD shape (a sealed, resolvable guard whose default-on
wiring is owner-gated, so the row stays a visible floor GAP).

This was explicitly surfaced as the planned follow-on in the prior cycle's
seal narrative (`docs/plans/protection-matrix-dropped-open-loops-row.manifest.yaml`,
MISMATCH #71): "the existing FM.SILENT-EGRESS row is now stale ... Surfaced
for an owner-gated follow-on re-bind."

## Tier-0 ground truth (verified this cycle)

- `EgressReleaseGate` (class) + `release` are defined in
  `framework/egress-consent/src/loam/egress_consent/gate.py` (grep confirmed).
- The component is sealed at `2304dea`
  (`framework/egress-consent/seals/SEAL_COMMIT.egress-consent-core-and-bug-report`;
  `git ls-tree 2304dea` confirms gate.py present at that commit).
- The matrix's runtime resolver (`derive.resolve_guard_ref`) resolves a
  `path:symbol` ref by path-exists + `def`/`class` symbol-defined; it does
  NOT enforce ALL_GATES membership at runtime (only the docstring mentions
  it). `EgressReleaseGate` is a `class`, so it resolves. `release-gate` is a
  valid `guard_kind` enum member (catalogue.py `GUARD_KINDS`).

## Scope

- The FM.SILENT-EGRESS row in `data/failure-mode-guard-matrix.yaml`:
  `guard_kind` → `release-gate`; `guard_ref` →
  `framework/egress-consent/src/loam/egress_consent/gate.py:EgressReleaseGate`;
  `default_on` → `NO-PROGRAMMATIC` (sealed but not yet wired default-on for
  every send — owner-gated, exactly like FM.COMMS-PATH-DEAD); `guard` +
  `verification` text updated to the now-built honest status.
- The FM.DROPPED-OPEN-LOOPS row's `verification` text + its test docstring
  carried a now-stale cross-reference ("the FM.SILENT-EGRESS row holds the
  unbuilt-guard shape"). Re-pointed to a self-describing statement of the
  unbuilt-guard shape (DROPPED-OPEN-LOOPS is now the canonical example of it).
- `test_AC_PMROW_3_silent_egress_row.py` re-greened to assert the now-bound
  shape: a resolvable guard_ref, NOT a divergence, still a floor GAP.
- The generated companion `docs/design/protection-matrix.md` regenerated via
  `loam guards --refresh`.

## Acceptance

- AC.PMROW.3 (re-greened) — the row binds the real sealed EgressReleaseGate
  symbol; the ref resolves against the real tree; the row is NOT a divergence.
- AC.PMROW.4 — the row still surfaces as a visible floor GAP (sealed but not
  yet default-on for every send).
- AC.PMROW.5 (outcome-altitude) — a real `load_catalogue()` +
  `run_coverage_check()` over the shipped catalogue + live tree (no
  pre-arranged state): the row parses, its guard_ref resolves to the real
  EgressReleaseGate symbol, it appears among the live coverage gaps, and adds
  zero new divergence.
- Non-regression: AC.FMG-CAT.1 (schema), AC.FMG-CAT.2 (no invented guards —
  the new ref resolves, zero divergences), AC.FMG-GAP.1 (SILENT-EGRESS stays
  a named gap; EXPECTED_FLOOR_GAPS is a subset assertion), AC.FMG-CHECK.2
  (no new divergence), AC.PMGEN.1 (companion sync), AC.PMROW.4 (dropped-open-
  loops row), AC.PMTRACK.1 all stay green.

## Seal fence

Single-component fence: `framework/protection-matrix/`
(`framework/protection-matrix/tests/test_no_sealed_amendments.py`); advances
the existing sidecar. The row references the egress-consent component's
public symbol but does NOT edit that component — no out-of-fence surface.
The companion + plan/manifest land under the admitted `docs/plans/` /
`docs/design/protection-matrix.md` universal paths.

BASELINE advanced to the current main tip (the documented HEAD~1 advance
pattern) so the single-component window shows only this amendment's
protection-matrix + docs surfaces.

LOCAL SEAL ONLY — not merged, not pushed, not published, not tagged. NEW
commits only; never `--amend`. No version bump (versions derive at release).
