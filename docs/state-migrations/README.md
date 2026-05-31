# `docs/state-migrations/` — declared user-state migrations (framework-side contract)

This directory is the **tracked, framework-side home** for the v-next
user-state migration *contract*. It holds one author-declared migration
file per release/slice describing **what that release changes in a user's
`.loam/` state** (the release-gate input, slice P1.3 / gate G4 — "no-op"
and "structural-only" are valid declared migrations).

## Why these live here and not under `.loam/migrations/`

The framework ↔ user-state boundary (master plan §2 / §3 decision #1)
splits the migration system in two — and they must not be conflated:

| Artefact | Side | Home | Tracked? |
|---|---|---|---|
| **Declared migration files** (`*.migration.yaml`) — the "what a release changes" contract, identical for every user | **Framework** | `docs/state-migrations/` (here) | **yes** |
| **The applied-migration cursor** (`.cursor`) — per-workspace record of which declared migrations *this* workspace has applied | **User-state** | `<workspace>/.loam/migrations/.cursor` | no (gitignored) |

The declared contract ships with loam and is versioned with loam, so it is
committed here. The applied-state cursor is unique per user, so it lives on
the gitignored user-state side.

## F2 corrective — why P1.1's migration moved here

The P1.1 (FBM-LIVE) slice authored its migration under
`.loam/migrations/fbm-live-slice.migration.yaml`, but `.loam/` is
gitignored (it is user-state), so that file was never committed (commit
`8ae3d7b` held only the slice plan-doc). Slice P1.2 (this layout-contract
slice) is exactly where the durable home for the declared-migration
*contract* is decided; the P1.1 migration content was relocated here as a
corrective so the release-gate has a tracked contract to read.

## File naming

`<scope-descriptive-slug>.migration.yaml`. Versions are NOT pre-assigned
(they derive at release time — `feedback_version_numbers_at_release_time`);
the slug is scope-descriptive.
