# v0.3.0 Cycle 2 — Graphiti rip-out + FBE.7 memory pivot (STUB)

**Status:** stub sub-plan-doc; finalizes at cycle-dispatch time per `plan-docs-author` SKILL master-vs-sub-plan trim discipline.
**Slug:** `v0-3-0-cycle-2-graphiti-ripout-and-fbe7`
**Date authored:** 2026-05-08.
**Parent master plan:** `docs/plans/v0-3-0-master-plan.md` §3 Cycle 2.
**Predecessor cycles:** Cycle 1 (parallelizable in principle but serialized per `feedback_serialize_amendment_builds`).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## §1 — Outcome shape (the "why")

Graphiti-the-component is removed. The FBE.7 file-backed approach (Stop hook persists; UserPromptSubmit retrieves) replaces it. Re-implementation is backlog per Luke 2026-05-08 ruling. A stranger cloning loam at v0.3.0 has memory that survives `/clear`; doesn't see segregated graphiti venv install ceremony or kuzu_db / graphiti-service residue in workspace state.

## §3 — Component fence

PRIMARY: `framework/memory-system/` (subtree edit + venv removal).

Secondary: `install-from-source.txt`; cross-references in `framework/`, `plugins/`, root `docs/`.

Universal admissions: hook-related code paths in `framework/primary-persona/` if they invoke memory-system surfaces.

## §4 — AC family seed — `AC.GRX.*`

Load-bearing concerns to be tightened at dispatch time:

- Directory pruning — graphiti-service launchd plist; graphiti-core `.venv`; graphiti-data files.
- `install-from-source.txt` — graphiti line removed.
- Cross-reference scrub — ~60+ references to graphiti / kuzu in `framework/`, `plugins/`, root `docs/` resolved.
- FBE.7 file-backed implementation — Stop hook persists session contributions to a workspace file; UserPromptSubmit retrieval reads file content into the next session's surface.
- Workspace state cleanup — `kuzu_db.wal` / `graphiti-service.{log,err.log}` no longer surface on stranger-clone install.
- Memory-system tests green on FBE.7 path (existing test suite migrates; new tests for FBE.7 surface).
- An outcome-altitude AC — full memory-write-then-retrieve flow against fresh workspace.

D5 (cross-session) verification deferred to Cycle 6 stranger-clone outcome AC.

## §5 — Build dispatch brief

Build dispatch brief authored inline by dispatcher at dispatch time per `dispatch-brief-authoring` SKILL.

## §7 — Out of scope

- Graphiti re-implementation — backlog per Luke 2026-05-08 (trigger: if FBE.7 proves operationally inadequate).
- Memory system feature additions beyond FBE.7 — deferred to v0.9.0 (deep personalization).
- M-GMP plugin-shaped graphiti — backlog with broader graphiti category.

## §10 — F2 RF gaps to surface at dispatch

- FBE.7 implementation details (file format; serialization; retrieval-prompt-shape) — load-bearing method choice; surface to dispatch.
- Workspace-state cleanup mechanism — does a fresh-install setup script handle the cleanup, or does the build agent leave the path dormant for natural-decay?
- Memory-test migration strategy — port existing graphiti-targeted tests to FBE.7 (lots of prior assertions) or rewrite (cleaner but loses regression coverage)?

## §11 — Provenance trail

Master plan §3 Cycle 2; release-roadmap §3 v0.3.0 AC.V030.2 + AC.V030.3.

## §14 — Method-decision record (backfilled at dispatch + seal)

To be filled at cycle-dispatch authoring + post-seal backfill.
