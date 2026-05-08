# v0.3.0 Cycle 1 — `docs/rebuild/` collapse + reference scrub

**Status:** sub-plan-doc; expanded from stub at cycle-dispatch time per `plan-docs-author` SKILL master-vs-sub-plan trim discipline.
**Slug:** `v0-3-0-cycle-1-rebuild-collapse-and-reference-scrub`
**Date authored:** 2026-05-08 (stub); expanded 2026-05-08 at dispatch.
**Parent master plan:** `docs/plans/v0-3-0-master-plan.md` §3 Cycle 1.
**Predecessor cycles:** N/A (first cycle of v0.3.0).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## §1 — Outcome shape (the "why")

"Rebuild" is a finished phase of loam's history; the directory's name names a stage that's no longer current. v0.3.0 collapses the `docs/rebuild/` subtree so the canonical doc-tree has one root. A stranger cloning loam at v0.3.0 sees one `docs/` root; doesn't navigate "wait, why is there a `docs/rebuild/`?" cognitive bump.

The scope is bulk-edit-shaped: directory-subtree migration + cross-reference rewrite (~4967 references measured, distributed across `framework/` + `plugins/` + `docs/` + root files).

## §2 — Prime objective ladder

VALUE_PROPOSITION.md prime objective → v0.3.0 release-roadmap §3 outcome ("documented features work as advertised AND terminology is consistent across forward-looking surface") → AC.V030.8 (`docs/rebuild/` collapse) → C1 ACs below.

## §3 — Component fence

PRIMARY: `docs/rebuild/` directory subtree (entire tree migrates).

Universal admissions (cross-reference rewrites): `framework/` + `plugins/` + `docs/` + `CLAUDE.md` + `CLAUDE.dev.md` + `README.md` + `pyproject.toml`.

Read-only: sealed-component source code (no source semantic edits in this cycle; doc-string + comment scrubs of `docs/rebuild/...` path strings DO admit, since they are surface-text not behavior).

Excluded from scrub (historical context preserved):
- `framework/*/tests/test_no_sealed_amendments.py` — historical SHA + amendment narratives.
- `plugins/*/tests/test_no_sealed_amendments.py` — same.
- `framework/*/seals/SEAL_COMMIT.*` — sealed historical narratives (none currently contain `docs/rebuild` refs per pre-build verification).
- `plugins/*/seals/SEAL_COMMIT.*` — same.
- Files moved to `docs/archive/*` — historical artefacts; their internal refs remain.

## §4 — AC family `AC.RBC.*`

- **AC.RBC.1** — Directory subtree migration: every file under `docs/rebuild/` lands at its mapped target path; no file under `docs/rebuild/` post-cycle (i.e. `find docs/rebuild -type f | wc -l` returns 0); `docs/rebuild/` directory itself removed.

- **AC.RBC.2** — Per-content placement per the migration map below.

- **AC.RBC.3** — Cross-reference rewrite: `git grep "docs/rebuild" -- '*.py' '*.yaml' '*.md' '*.toml' '*.json'` returns matches ONLY in excluded historical files (per §3 excluded list). Specifically the 16 historical `test_no_sealed_amendments.py` files are admitted leftover; everywhere else: zero matches.

- **AC.RBC.4** — `docs/STATE.md`, `docs/FUTURE_IDEAS.md`, `docs/FUTURE_IDEAS_DRAFT.md`, `docs/BACKLOG.md`, `docs/VALUE_PROPOSITION.md` exist at their new canonical paths and are grep-discoverable (filename grep + content grep both find them at the new location).

- **AC.RBC.5** — Tests that hardcoded `docs/rebuild/...` paths are updated; full-suite runs as previously did pre-cycle (any test broken by the path-rewrite is part of this cycle's surface — fix it as part of the scrub).

- **AC.RBC.6** — STATE.md gains a one-row entry naming v0.3.0 Cycle 1 outcome (per §11 backfill ladder; ≤2-line update).

- **AC.RBC.7** — `loam amend apply` + `loam amend seal` ladder lands; manifest schema v3; new commits only (no `--amend`).

## §5 — Migration map

| Old path | New path | Disposition |
|---|---|---|
| `docs/rebuild/STATE.md` | `docs/STATE.md` | git mv |
| `docs/rebuild/VALUE_PROPOSITION.md` | `docs/VALUE_PROPOSITION.md` | git mv |
| `docs/rebuild/FUTURE_IDEAS.md` | `docs/FUTURE_IDEAS.md` | git mv |
| `docs/rebuild/FUTURE_IDEAS_DRAFT.md` | `docs/FUTURE_IDEAS_DRAFT.md` | git mv |
| `docs/rebuild/BACKLOG.md` | `docs/BACKLOG.md` | git mv |
| `docs/rebuild/decay-retention-analysis.md` | `docs/archive/decay-retention-analysis.md` | git mv (historical) |
| `docs/rebuild/plans/` (385 files + research/) | `docs/plans/` (merge) | git mv per file |
| `docs/rebuild/spec/` | `docs/spec/` | git mv (subtree) |
| `docs/rebuild/templates/` | `docs/templates/` | git mv (subtree) |
| `docs/rebuild/capability-corpus/` | `docs/capability-corpus/` | git mv (subtree) |
| `docs/rebuild/components/` | `docs/archive/component-research/` | git mv (archive; historical research) |
| `docs/rebuild/archive/synthesis-tool-2026-05-04/` | `docs/archive/synthesis-tool-2026-05-04/` | git mv (subtree) |

## §6 — Reference scrub strategy

Sed-style replace, more-specific-first (so `docs/rebuild/plans/` substitutes don't get clobbered by a generic `docs/rebuild/` rule firing earlier):

1. `docs/rebuild/STATE.md` → `docs/STATE.md`
2. `docs/rebuild/VALUE_PROPOSITION.md` → `docs/VALUE_PROPOSITION.md`
3. `docs/rebuild/FUTURE_IDEAS_DRAFT.md` → `docs/FUTURE_IDEAS_DRAFT.md`
4. `docs/rebuild/FUTURE_IDEAS.md` → `docs/FUTURE_IDEAS.md`
5. `docs/rebuild/BACKLOG.md` → `docs/BACKLOG.md`
6. `docs/rebuild/decay-retention-analysis.md` → `docs/archive/decay-retention-analysis.md`
7. `docs/rebuild/plans/` → `docs/plans/`
8. `docs/rebuild/spec/` → `docs/spec/`
9. `docs/rebuild/templates/` → `docs/templates/`
10. `docs/rebuild/capability-corpus/` → `docs/capability-corpus/`
11. `docs/rebuild/components/` → `docs/archive/component-research/`
12. `docs/rebuild/archive/synthesis-tool-2026-05-04/` → `docs/archive/synthesis-tool-2026-05-04/`
13. `docs/rebuild/archive/` → `docs/archive/`

Excluded files (excluded from all sed passes):
- `**/test_no_sealed_amendments.py` (historical SHA + narratives)
- `**/seals/SEAL_COMMIT.*` (sealed narratives)
- `docs/archive/**` (historical artefacts; their internal refs stay)

## §7 — Smoke

D2 steady-state — `find docs/rebuild -type f | wc -l` returns 0; `git grep "docs/rebuild" -- '*.py' '*.yaml' '*.md' '*.toml' '*.json'` returns matches ONLY in 16 excluded historical test files; `pytest` exit code matches pre-cycle baseline (no new failures introduced by the scrub).

D5 cross-session — n/a for this cycle.

## §8 — Halt-and-surface (in-flight)

- WD mismatch (cd literal first; halt if pwd ≠ `/Users/lukeivers/ivers-corp-pos-v2`).
- Reference scrub touches a file outside the named scope.
- Tests break in unanticipated ways (i.e. break for reasons OTHER than path-rewrite-staleness).
- Push or tag attempt.
- Any commit touches non-rebuild files unrelated to the scrub.

## §9 — Out of scope

- No `docs/` reorganization beyond rebuild-subtree absorption.
- No content edits beyond reference rewrites + STATE.md cycle-outcome row.
- No new `docs/` files beyond what migration creates.
- Foundation-docs gap-fill (Cycle 3).
- Graphiti rip-out (Cycle 2).

## §10 — F2 RF gaps surfaced at dispatch

1. **Pre-existing dirty working-tree state** — modified + untracked files at `docs/rebuild/plans/...` predating this cycle. They will participate in the move (filesystem-level) but NOT be committed by this cycle (they remain dirty in their new location). Surfaced at report.

2. **5300 estimate vs 4967 actual** — measurement at dispatch returned 4967 references across 779 files. Master plan banded ~5300; actual is within 7% — proceed without re-banding AI-time.

3. **`docs/archive/` will collide** — `docs/archive/` doesn't exist yet (verified). Three sources land there: (a) `decay-retention-analysis.md`; (b) `components/` → `component-research/`; (c) `archive/synthesis-tool-2026-05-04/`. Mapping handles all three; no collision.

4. **Plans/ merge** — `docs/plans/` already exists with 11 plan-docs. `docs/rebuild/plans/` adds 385 files. No name collisions verified at dispatch.

5. **Manifest shape** — multiple top-level dirs touched (`framework/`, `plugins/`, `docs/`, root). Single owning component (`dev-sdlc`) with `frozen_baseline: true` + broad `universal_paths.prefixes` follows the v0-2-5-1 precedent shape.

## §11 — Provenance trail

Master plan §3 Cycle 1; release-roadmap §3 v0.3.0 AC.V030.8.

## §12 — Acceptance gate (pre-cycle conditions)

- [x] Master plan + 7 cycle stubs landed (commit a8838a9).
- [x] WD confirmed at start.
- [x] Reference count verified (4967).
- [x] No name collisions in target dirs verified.
- [x] Migration map covers every file under `docs/rebuild/` (12 mapped paths).
- [x] Excluded-files list covers historical context (16 test files + seals/).

## §14 — Method-decision record

| Decision | Choice | Rationale |
|---|---|---|
| Owning component | `dev-sdlc` (`frozen_baseline: true`) | Doc-only cycle; bookkeeping owner; cycle is methodology-surface. |
| Universal-paths breadth | `docs/`, `framework/`, `plugins/`, root files | Reference scrub crosses all top-level dirs; broad admissions match scope. |
| Sed order | More-specific-first | Avoids `docs/rebuild/plans/` being substituted to `docs/plans/` then re-substituted to wrong target. |
| Components/ → archive | `docs/archive/component-research/` | Historical research per dispatch; not active-design surface. |
| Pre-existing dirty state | Carry through, do NOT commit | Predates cycle; not in scope; surface at report. |
| Path-style construction scrub | Python multi-line script for `/ "rebuild"` patterns | Sed misses multi-line Path constructions; 51 .py files needed Python script handling. |
| Seal-diff window historical retention | Add `docs/rebuild/plans/` back to `_ALLOWED_PREFIXES` of 8 seal-diff window tests | Tests check historical BASELINE..SEAL_COMMIT diff windows where files were at old paths; preserve historical commit-window assertions. |
| In-flight smoke_outcome fix on v0-2-4-master-plan.manifest.yaml | Trim 281 -> 186 chars | Pre-existing data violation surfaced when manifest-validation test moved to scan post-collapse `docs/plans/`; minimal-scope correction to keep cycle whole. |
| Seal `--allow-untracked-globs` usage | 7 patterns covering pre-existing dirty paths | Pre-existing dirty state predates cycle per F2 RF #1; admission-only (no auto-stage) per AC.LAE.2. |
| `--amend` policy | NEW commits only | Per master plan §9 + `feedback_no_amend_in_agent_dispatches.md`. |
| Tag-push policy | NO tag push, NO remote push | Per dispatch + master plan. |

### Commit SHAs

| Commit | SHA | Description |
|---|---|---|
| 1 — plan-doc | `2c2fd75` | `docs(plans): v0.3.0 Cycle 1 — expand stub to sub-plan-doc` |
| 2 — source-edit (BASELINE) | `66bf869` | `docs(v0.3.0): Cycle 1 — collapse docs/rebuild/ + scrub references` |
| 3 — manifest | `fb441a7` | `docs(plans): v0.3.0 Cycle 1 — manifest YAML` |
| 4 — apply auto-commit | `e80437b` | `chore(amend): v0-3-0-cycle-1-rebuild-collapse-and-reference-scrub manifest+apply — dev-sdlc BASELINE+sidecar bump to 66bf869` |
| 5 — seal | `459c7fc` | `chore(seals): v0-3-0-cycle-1-rebuild-collapse-and-reference-scrub — dev-sdlc at e80437b` |
