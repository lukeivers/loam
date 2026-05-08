# v0.3.0 Cycle 5 — Terminology consistency + glossary publication (STUB)

**Status:** stub sub-plan-doc; finalizes at cycle-dispatch time per `plan-docs-author` SKILL master-vs-sub-plan trim discipline.
**Slug:** `v0-3-0-cycle-5-terminology-consistency-and-glossary`
**Date authored:** 2026-05-08.
**Parent master plan:** `docs/plans/v0-3-0-master-plan.md` §3 Cycle 5.
**Predecessor cycles:** Cycle 1 (paths stable post-collapse).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## §1 — Outcome shape (the "why")

Loam-aligned names (substrate / seed / cultivar / amend / seal) used consistently with single canonical definitions. Glossary published. Ad-hoc usages collapse. A stranger cloning loam at v0.3.0 sees consistent terminology; no "is 'amend' the same as 'patch'?" cognitive bump.

## §3 — Component fence

PRIMARY: `docs/glossary.md` (NEW).

Universal admissions: doc-only edits across `docs/`, `framework/docs/`, `plugins/`-docs.

Read-only: source code identifiers (no code-level rename refactors).

## §4 — AC family seed — `AC.TGL.*`

Load-bearing concerns to be tightened at dispatch time:

- `docs/glossary.md` exists with 11 canonical terms: **substrate / seed / cultivar / growth / amend / seal / contract / objective / capability / banded AC / ratification**.
- Each term has single canonical definition + cross-references to where it's used.
- Doc-only sweep replaces ad-hoc usages of these terms across `docs/` + `framework/docs/` + `plugins/`-docs.
- Terms used inline link to glossary entries (or use canonical form consistently).
- No orphaned definitions (every glossary term has at least one cross-reference; every cross-reference resolves).
- An outcome-altitude AC — `grep -c "^## " docs/glossary.md` returns ≥ 11; sweep test asserts zero ad-hoc usages of the 11 terms outside their canonical contexts.

## §5 — Build dispatch brief

Build dispatch brief authored inline by dispatcher at dispatch time per `dispatch-brief-authoring` SKILL.

## §7 — Out of scope

- Code-level rename refactors (terms inside source code identifiers).
- Plugin-specific terminology (per-plugin glossaries land if/when needed).
- New term creation beyond the 11 canonical terms (additions land in future minors).
- Translation / localization (English-only at v0.3.0).

## §10 — F2 RF gaps to surface at dispatch

- 11-term list is master-plan-locked. If the build agent finds the list incomplete (a 12th term is load-bearing across docs), halt-and-surface for owner ruling on additions.
- Canonical definitions — some terms (e.g., "substrate") have multiple plausible definitions; the build agent must pick one + name the alternative in the glossary entry's "see also" / disambiguation note.
- Doc-only sweep boundary — does `framework/docs/design/` count for sweep, or does it inherit from already-canonical-terminology in the principle-derivation-map (Cycle 3)?

## §11 — Provenance trail

Master plan §3 Cycle 5; release-roadmap §3 v0.3.0 AC.V030.7.

## §14 — Method-decision record (backfilled at dispatch + seal)

To be filled at cycle-dispatch authoring + post-seal backfill.
