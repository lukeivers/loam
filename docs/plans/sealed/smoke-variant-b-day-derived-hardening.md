# Smoke variant-B day-derived hardening — apply ladder

The loam 1.0 acceptance smoke's SECOND re-run
(`docs/experiments/loam-1.0-acceptance-smoke-rerun2.md`) sampled a
PURE-VACUUM opener for variant B ("afternoons just disappear, not sure
where the time goes" — no concrete pain), so B routed to the idea-vacuum
ladder + deep-research and tripped the featherlight gate
(deep-research-correctly-(not)-triggered FAIL). loam routed CORRECTLY for
that input — the defect was the persona script allowing a contentless
opener (harness non-determinism), NOT a loam bug.

This cycle hardens variant B's persona brief (and its human-readable
mirror) so its FIRST stop/start answer reliably describes the day AND names
the concrete pain (the claim-summary write-ups) in the SAME reply — the
day-derived PARTIAL shape the production classifier demotes OFF the research
ladder via the single-derivable-pain demotion. The brief explicitly forbids
the contentless "the time just disappears" opener.

AC.SMOKE.6 asserts (a) the brief instructs a day-with-named-pain opener and
(b) the prescribed opener classifies non-EMPTY via the REAL production
classifier (`_classify_richness`) — coupling the smoke-input fix to the loam
behavior it must exercise. It does NOT loosen AC.SMOKE.3: variant B is still
asserted to reach zero research there; this AC fixes the INPUT so B reliably
presents the day-derived shape, rather than papering over the gate.

Predecessor commits:
  - b474fec6 — #166 close-redesign seal (workspace-bootstrap).
  - ab5762dc — revert of the early smoke edit, replay setup (BASELINE).
  - 3b53fc97 — variant-B persona hardening + AC.SMOKE.6 (replayed, BASELINE+1).

BASELINE ab5762dc. Single-component fence on
`framework/tools/loam-acceptance-smoke/`.

DO NOT push, DO NOT merge — owner-gated.
