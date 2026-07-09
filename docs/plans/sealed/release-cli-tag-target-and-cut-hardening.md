# Release-CLI tag-target + deterministic-cut + mergeability hardening — apply ladder

Cycle 1 of a 3-cycle fix program off the 2026-07-08 release-seal
near-miss audit (`workspace/.scratch/claude-output/release-seal-near-miss-audit-2026-07-08.md`,
pos3). This cycle lands the release-CLI-resident half: Class D (right
tag target), Class A (deterministic cut), and the Class-B cheap partial
(mergeability verb). Classes C (guard-floor registry) and E (brittle-
guard conversion) are separate cycles, out of scope here.

This amendment (single loam-cli fence, NO public action):
  1. (D) Replaces the fragile `seals[-1]` tag-target text-parse with an
     ancestor-DOMINANCE resolver: a version's tag target is the seal in
     its roadmap §2 row that has every other row-seal as an ancestor. If
     no seal dominates → HALT/RED (the row spans divergent history). The
     resolver replaces `seals[-1]` at ALL FOUR tag-target sites
     (runner.py tag creation, gates.py seal-reachable gate, notes.py
     anchor + prior-version range endpoint, post_publish_backfill.py
     marker) — leaving any straggler would be a non-objective
     inconsistency (ODD). A dedicated dominance gate rides gates.run_all
     so it is mandatory at publish (AC.DOM.1-6). Real-row verified: the
     resolver's target == `git rev-list -1 v1.10.0` (99a1be9) and
     v1.11.0 (badd2d6f). Sidecars are NOT in the dominance set
     (D-DOM.SIDECAR — they track each component's latest seal regardless
     of version, so they would false-RED).
  2. (A) Adds a deterministic-cut gate to gates.run_all that recomputes
     class + expected number from repo state (conventional-commit prefix
     scan over `<current-published-tag>..HEAD` + the published-tag read)
     per docs/release-versioning-policy.md, and REDs when the recomputed
     version != the version being cut — the policy's own "halt-and-
     surface, never silent re-number" event made a real chokepoint
     (AC.CUT.1-6). "Content class" mechanized as conventional-commit
     prefixes (D-CUT.CLASS; feat→MINOR, else PATCH); MAJOR stays owner-
     gated, breaking markers surface as a note, never auto-RED
     (D-CUT.MAJOR). Fail-safe: indeterminate published state degrades to
     pass-with-caveat, never a false RED (mirrors gates 8/9).
  3. (B) Adds `loam release preflight <version>` (D-PRE.CLI: a leading
     sub-token on the existing release parser; `loam release <version>`
     is UNCHANGED — no public-CLI break) emitting per-branch
     fast-forward/merge-tree verdicts against main + the computed cut,
     in a stable block recordable into the ratification artefact
     (AC.PRE.1-5). HONESTLY a tool-assisted PARTIAL (relies on being
     run) — NOT the structural pre-dispatch hook, which is a SEPARATE
     scheduled item out of this cycle (D-PRE.PARTIAL).

Outcome-altitude ACs: AC.DOM.4 (non-dominating first-SHA multi-seal row
→ dominating seal, never the early SHA; + real-row rev-list equality),
AC.CUT.4 (MINOR content under a PATCH target, and the inverse → RED
through run_all), AC.PRE.4 (conflicting/non-ff branch → reported
non-clean, end-to-end through the CLI).

STOP at sealed-local. Does NOT run `loam release`, does NOT tag, does
NOT push — the eventual single published cut is the dispatcher's action
AFTER all three cycles seal.

BASELINE 6ca68259 — HEAD of main at plan-authoring (v1.11.0 post-publish
backfill); confirm at apply time. Counter 195 next free; confirm at
apply time. Single-component loam-cli fence; NO other component's
runtime behavior changes.
