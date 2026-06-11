# manifest-data-conformance-backfill — apply ladder

Data-conformance fix cycle. Plan:
`docs/plans/manifest-data-conformance-backfill.md`.

Closes the AC.DPS1.13 sweep RED at HEAD a73ff88e: three
context-management manifests carried pre-v3 draft shape
(`schema_version: 1` + `number: null` + `baseline: null` — the
baseline-null failure was masked by first-error-only validation) and
the session-clear-safety master manifest carried a 575-char
`smoke_outcome` over the 200-char cap live since
dev-pattern-simplifications-2 (df3f50f6, 2026-05-04).

Fix shape (plan §10): c1 restored byte-identical to its sealed-branch
record (58c3c401 on build/context-management-c1-see — also dissolves
the latent same-path merge conflict with main's 2662245c stub); c2/c3
re-expressed as slug-identified schema v3 with provisional baseline
pinned to their authoring commit 2662245c; smoke_outcome compressed
preserving all four named outcome facts (full text recoverable at
5e086286).

AC family AC.MCONF.1-4 (plan §4); AC.MCONF.1 is outcome-altitude
(production pytest entry-point, 19/19, no pre-arranged state, empty
diff over the loam-amend tool tree). Sweep test untouchable (hard
halt). Facts-unchanged is an AC, not a hope: per-file fact-diff
narrated in §14.

Ladders to AC.DPS1.13's standing guarantee -> AC.PO.2 (the amend
machinery's data integrity keeps sealed-state claims honest).
