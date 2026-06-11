# release-flow-partial-publish-repair — apply ladder

Publish-gate dependency PATCH. Plan:
`docs/plans/release-flow-partial-publish-repair.md`.

Closes the v1.5.0 live incident's root cause (FIDRAFT
F-RELEASE-FLOW-PARTIAL-PUBLISH-NOT-REPAIRABLE): the release
runner's already-on-origin branch returned "nothing to do" with
the GitHub Release missing, so a partial publish (tag pushed,
Release never created) was unrepairable by re-run and recovery
was a manual cross-package kludge. Sibling: the notes
generator's plan-doc lookup missed the
release-integration-v<X-Y-Z>.md naming (notes degraded to
"(unavailable)" — visible on the published v1.4.0 Release), and
the explicit --plan-doc flag never reached notes generation.

Fix shape (plan §10): Release-existence detection + repair in
the already-on-origin branch behind the existing --release
opt-in; release-side naming resolution (shared loam_amend
locator untouched, D-RFPR.1); plan-doc threaded into
generate_notes (D-RFPR.2); dry-run honored across the reworked
branch including the pre-existing backfill-mutates-on-dry-run
latent bug (D-RFPR.4); both-halves completeness reporting scoped
to --release runs (D-RFPR.5). Adjacent manifest-sweep-before-
release-prep-stubs item ruled OUT of fence with disposition
recorded (D-RFPR.3).

AC family AC.RFPR.1-4 (plan §4); AC.RFPR.3 is outcome-altitude
(production entry-point on a deliberately tag-only fixture, no
pre-arranged repair state, ends with the Release existing).
Idempotency on fully-published versions is AC.RFPR.4, not a hope.

Ladders to roadmap §4 Candidate 7 -> the publish flow's "SHIPPED
PUBLIC means user-visibly shipped" promise -> AC.PO.2
(protection: feedback_published_state_only_from_git_refs — the
tag ref was green while the user-visible Releases page was stale
for a day).
