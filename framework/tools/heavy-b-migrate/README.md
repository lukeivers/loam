# heavy-b-migrate

Heavy-B Phase α / β / γ data-migration tooling. Dev-discipline.

**Plan:** `docs/rebuild/plans/heavy-b-phase-alpha-beta-gamma-migration.md`.
**Builder plan:** `docs/rebuild/plans/heavy-b-phase-alpha-beta-gamma-migration.builder-plan.md`.

## What it does

Populates a dev-intent workspace's tracker DB with ObjectiveSpec
records lifted from the workspace's docs corpus, in three phases:

1. **Phase α** — one ObjectiveSpec per sealed-component proposal.md
   under `docs/rebuild/components/<slug>/proposal.md`. Parented at
   `spec-v1.0` (the value-prop-rooted spec phase).
2. **Phase β** — one ObjectiveSpec per parseable AC anchor inside each
   component proposal. Parented at the component objective from α.
   Unparseable proposals get a single placeholder record.
3. **Phase γ** — one ObjectiveSpec per parseable AC anchor inside each
   amendment plan under `docs/rebuild/plans/amendment-*.md` (excluding
   `.builder-plan.md` companions). Parented at `spec-v1.0`.
   Unparseable plans get a placeholder.

Every record carries `lifted_from(source_doc, source_ac)` provenance.
Idempotency is by `(source_doc, source_ac)` — re-runs are no-ops.

## Lazy-projection trigger

The phase migration runs automatically on the first session where the
workspace's PersonaContract carries `dev_intent="yes"` (per sub-plan A).
The trigger is wired into loam-mode's session-start emitter and is:

- **Read-only** of the dev-intent signal (per plan §6 constraint 13).
- **Idempotent** by `lifted_from` (per plan §6 constraint 14).
- **Fail-soft** — every exception is swallowed; the SessionStart hook
  proceeds normally regardless.

## CLI

```
heavy-b-migrate run                     # run all three phases
heavy-b-migrate run --phases alpha beta # run α + β only (γ skipped)
heavy-b-migrate run --workspace /path   # against a non-cwd workspace
heavy-b-migrate verify-continuous       # AC.D-mig.4 verifier
```

The phase runner enforces ordering structurally: requesting `beta` only
or `alpha gamma` (skipping β) raises `PhaseOrderingError` and exits
non-zero.

## Tests

```
.venv/bin/python -m pytest tools/heavy-b-migrate/tests/
```

One test file per AC (`test_ac_d_mig_<n>_<name>.py`).

## What this composes against (does NOT touch)

- **#38** — `objective-tracker` schema widening (`lifted_from`,
  `query_projection_view`).
- **#39** — `workspace-bootstrap` first-run tracker seed (value-prop
  root + spec descendants).
- **#40** — `primary-persona` tracker-context contributor (the
  consumer that surfaces migrated content).
- **#16** — `loam amend` tracker integration (manifest `objectives`
  block + apply registration + seal source_commit).
- **Sub-plan A** — `dev_intent` field on PersonaContract.
- **#45** — multi-contributor SessionStart (loam-mode contributes the
  hook; heavy-b-migrate's trigger rides loam-mode's session-start
  surface).

The tool composes against these; it does not modify any of them. If
a change to one of them is required, halt and signal — that's a
sealed-component amendment, not part of this dev-discipline plan.
