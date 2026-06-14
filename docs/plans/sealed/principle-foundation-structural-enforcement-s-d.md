# principle-foundation-structural-enforcement — Slice D — SLUG-COLLISION + ARBITER SKILL — apply ladder

Fourth and FINAL slice under the candidate plan
`docs/plans/principle-foundation-structural-enforcement.md`. Baselines on
Slice C's seal (fafd2898). Closes the candidate (roadmap §4 Candidate 1).

This amendment:
  1. AC.PFSE.6 — workspace-slug collision detection. A new
     workspace-bootstrap adapter (slug_collision.py): detect_slug_collision
     derives the slug + scans ~/Library/LaunchAgents/com.loam.<slug>.*.plist
     for a plist whose embedded WorkingDirectory points at a DIFFERENT
     workspace (a same-workspace re-bootstrap is NOT a collision);
     disambiguate_slug appends <slug>-N until free; taken_slugs_in reads
     the live host state. Deterministic; fail-soft. Catches the silent
     launchd-label clobber two same-slug workspaces cause.
  2. AC.PFSE.8 — the meta-decision-haiku arbiter SKILL. Packages the
     SKILL.md the sealed lsk1 ruling held open as planned-not-yet-packaged
     (PFSE plan §2 — this AC is the authority that fills the slot). The
     impartial borderline-rule arbiter invokes Haiku via the subscription
     print-client path (NO API key) on a BOUNDED trigger list — a
     tiebreaker OFF the per-action hot path, the operational arbiter for
     M5. Carries the model-rationale line for the Haiku selection.
  3. The lsk1 planned-not-yet-packaged state is SUPERSEDED: README count
     25->26, the planned note removed, the CLP-DOC.6 test flipped to
     assert packaged, the SKTRI trigger table gains the entry.

With Slice D sealed, the candidate is complete: the three Lenses +
derivation-map are NAMED PRIMITIVES (the principle-manifest, Slice A),
structurally enforced for the machine-checkable subset (the four-question
gate + context-load gate, Slice B; the permission-ask + terminology-drift
Stop contributors, Slice C; slug-collision + the arbiter SKILL, Slice D).
M5 ships ADVISORY per the D-PFSE.1 partition (named primitive + arbiter
SKILL + recorded-conflict template; behavioural enforcement explicitly
out — interior cognition, no observable artefact).

NO public-action steps; NO Anthropic API key anywhere (the arbiter routes
through the subscription print-client path). BASELINE = Slice C seal
(confirmed at apply); counter 191 next free; builder confirms both at
apply time. LOCAL only.
