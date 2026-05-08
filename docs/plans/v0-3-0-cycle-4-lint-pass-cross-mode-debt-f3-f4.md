# v0.3.0 Cycle 4 — Lint pass + cross-mode-debt shrinkage + F3/F4 closures (STUB)

**Status:** stub sub-plan-doc; finalizes at cycle-dispatch time per `plan-docs-author` SKILL master-vs-sub-plan trim discipline.
**Slug:** `v0-3-0-cycle-4-lint-pass-cross-mode-debt-f3-f4`
**Date authored:** 2026-05-08.
**Parent master plan:** `docs/plans/v0-3-0-master-plan.md` §3 Cycle 4.
**Predecessor cycles:** Cycle 1 (lint sweep clean post-collapse).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## §1 — Outcome shape (the "why")

Close out language-tooling debt + named-FIDRAFT items so the lint discipline runs clean every push. New code in v0.4.0+ inherits a clean lint baseline; `KNOWN_CROSS_MODE_DEBT` shrinkage is observable proof of the shrink-not-grow discipline.

Three semi-orthogonal items bundled into one cycle because each individually is small (~15–30 min); per-item decomposition would add 3 micro-cycles with no AC tightening.

## §3 — Component fence

PRIMARY: `framework/` + `plugins/` (lint-fix sweep).

Secondary: `plugins/dev-sdlc/odd-extractor/` for F3 (extending `_SKIP_DIR_NAMES`).

Tertiary: `plugins/dev-sdlc/methodology/`-or-equivalent for F4 v0.2.1 corrective F1 seal-text doc-drift fix.

Universal admissions: `KNOWN_CROSS_MODE_DEBT` allowlist file (location to be confirmed at dispatch).

## §4 — AC family seed — `AC.LDC.*`

Load-bearing concerns to be tightened at dispatch time:

- `ruff check framework/ plugins/` exits 0.
- `mypy --strict` (or named profile) exits 0 across `framework/` + `plugins/`.
- `KNOWN_CROSS_MODE_DEBT` allowlist count strictly decreases vs v0.2.5.1 baseline; target zero.
- F3 closure — odd-extractor `analyze` step adds `framework/` to `_SKIP_DIR_NAMES`; test asserts the skip behavior on a fresh framework/-containing fixture.
- F4 v0.2.1 corrective F1 seal-text doc-drift resolved per FIDRAFT.
- An outcome-altitude AC — full repo-wide `ruff` + `mypy` + `pytest` green sweep on canonical fixture.

## §5 — Build dispatch brief

Build dispatch brief authored inline by dispatcher at dispatch time per `dispatch-brief-authoring` SKILL.

## §7 — Out of scope

- Type-system migration beyond `mypy` named profile.
- Test-suite restructuring beyond F3/F4 closure tests.
- New ruff / mypy rule additions beyond default profile.
- Lint-pass on `docs/` (doc-only edits).

## §10 — F2 RF gaps to surface at dispatch

- Existing ruff / mypy violation count unknown until dispatch — if it's >100, lint-fix iteration may exceed 60-min budget; halt-trigger §8.4 catches.
- `KNOWN_CROSS_MODE_DEBT` allowlist location and current count — surface to dispatch for inventory.
- F3 closure may interact with future v0.4.0 extractor work — if the skip is too coarse, false-negatives at extraction time. Surface for owner ruling at dispatch.

## §11 — Provenance trail

Master plan §3 Cycle 4; release-roadmap §3 v0.3.0 AC.V030.6 + AC.V030.9 + AC.V030.10; FIDRAFT entries for F3 (odd-extractor analyze framework/ skip) + F4 (v0.2.1 corrective F1 seal-text doc-drift).

## §14 — Method-decision record (backfilled at dispatch + seal)

To be filled at cycle-dispatch authoring + post-seal backfill.
