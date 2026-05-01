---
name: memory:archive
description: Archive episodes older than a named date under <workspace>/workspace/.loam/memory/archived/. Moves episode files (preserves history); idempotent. Use when the user wants to reduce the live-memory footprint, or when retrieval starts surfacing low-value old episodes.
---

# /memory:archive — file-based memory archival

This skill is the user-facing entry-point for archiving older
episodes from loam's file-based memory store.

## What this skill does

1. Asks the user for a cutoff date (e.g. `2026-01-01`).
2. Walks `<workspace>/workspace/.loam/memory/episodes/<group>/<date>/`
   directory tree.
3. Moves every episode whose date-dir is strictly before the cutoff
   under `<workspace>/workspace/.loam/memory/archived/<group>/<date>/`.
4. Reports the count of moved episodes.

## Usage

The user invokes:

    /memory:archive 2026-01-01

→

    [memory-archive] moved 47 episodes older than 2026-01-01.
      archived/<slug>/2025-12-30/  (12 episodes)
      archived/<slug>/2025-12-29/  (8 episodes)
      …

## Underlying mechanics

- Move-not-delete (preserves history; reversible by moving the
  archived dir back).
- Idempotent: re-invocation with the same cutoff is a no-op once no
  episodes remain before the cutoff.
- Directory-level move (`os.replace`) when the target dir doesn't
  exist; episode-by-episode merge when it does.

## Composition

This skill assumes:

- The workspace's memory dir exists.
- The user has authority to archive (no per-user gating at v0.1.0;
  the workspace owner makes the call).

## Out of scope

- Compression of archived episodes (future; FUTURE_IDEAS).
- Auto-archive on schedule (out of v0.1.0 scope; user-driven only).
- Cross-workspace archive operations.
- Restoring archived episodes (manual `mv` is the recovery path;
  CLI verb is FUTURE_IDEAS).
