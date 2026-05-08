# v0.3.0 Cycle 1 — `docs/rebuild/` collapse + reference scrub (STUB)

**Status:** stub sub-plan-doc; finalizes at cycle-dispatch time per `plan-docs-author` SKILL master-vs-sub-plan trim discipline.
**Slug:** `v0-3-0-cycle-1-rebuild-collapse-and-reference-scrub`
**Date authored:** 2026-05-08.
**Parent master plan:** `docs/plans/v0-3-0-master-plan.md` §3 Cycle 1.
**Predecessor cycles:** N/A (first cycle of v0.3.0).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## §1 — Outcome shape (the "why")

"Rebuild" is a finished phase of loam's history; the directory's name names a stage that's no longer current. v0.3.0 collapses the `docs/rebuild/` subtree so the canonical doc-tree has one root. A stranger cloning loam at v0.3.0 sees one `docs/` root; doesn't navigate "wait, why is there a `docs/rebuild/`?" cognitive bump.

The scope is bulk-edit-shaped: directory-subtree migration into `docs/spec/` / `docs/components/` / `docs/design/` / `docs/plans/` / `docs/archive/` per content; cross-reference rewrite (~5300 references across `framework/`, `plugins/`, root docs); redirect / archive-pointer mechanism preserves link integrity for 6 months.

## §3 — Component fence

PRIMARY: `docs/rebuild/` directory subtree.

Universal admissions (cross-reference rewrites): `framework/` + `plugins/` + `CLAUDE.md` + `README.md` + root `docs/*.md`.

Read-only: sealed-component source code (no source edits in this cycle).

## §4 — AC family seed — `AC.RBC.*`

Load-bearing concerns to be tightened at dispatch time:

- Directory-subtree migration into target paths per content classification (spec / components / design / plans / archive).
- Cross-reference rewrite — every reference to `docs/rebuild/<path>` resolves to the new canonical path post-collapse.
- Redirect / archive-pointer mechanism — link integrity preserved for 6 months minimum.
- STATE.md still grep-discoverable post-collapse (likely at `docs/STATE.md`).
- FUTURE_IDEAS.md still grep-discoverable (likely at `docs/FUTURE_IDEAS.md`).
- No broken-link regressions across the codebase.
- An outcome-altitude AC — the audit-deliverable cross-reference resolution test.

## §5 — Build dispatch brief

Build dispatch brief authored inline by dispatcher at dispatch time per `dispatch-brief-authoring` SKILL.

## §7 — Out of scope

- No `docs/` reorganization beyond rebuild-subtree absorption.
- No content edits beyond reference rewrites + path updates.
- No new `docs/` files beyond what migration creates.

## §10 — F2 RF gaps to surface at dispatch

- 5300-ref count includes possible indirect references via templates / generators — surface to dispatch for inventory.
- Per-content placement decision (which artefact goes to spec vs components vs design vs plans vs archive) — load-bearing classification choice.
- Redirect mechanism — symlink vs archive-pointer-prose vs Git-history-only — author chooses at dispatch.

## §11 — Provenance trail

Master plan §3 Cycle 1; release-roadmap §3 v0.3.0 AC.V030.8.

## §14 — Method-decision record (backfilled at dispatch + seal)

To be filled at cycle-dispatch authoring + post-seal backfill.
