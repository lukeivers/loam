# loam-memory-inspect

One-shot pre-discard inspection script for the kuzu_db state under
`<workspace>/workspace/data/memory-system/kuzu_db`. Authored at M-FBM
(memory-substrate pivot, 2026-05-01) per plan
`oss-v0-1-0-publish-memory-pivot.md` decision **D-Q.MFBM.6** (kuzu_db
state migration: discard, with one-shot inspection script that surfaces
findings BEFORE discard).

## What it reports

- File size of `kuzu_db` and `kuzu_db.wal` (when present).
- Existence of sibling artefacts (`graphiti-service.log` /
  `graphiti-service.err.log`).
- A best-effort byte-scan for `episode_uuid` strings in the kuzu_db
  binary (proxy for episode count when no kuzu binary is on PATH).
- The `episodes.json` file's record count when present (the test-
  fixture surface; not the live runtime data).

## Why it exists

Plan §11 D-Q.MFBM.6 + §9.8 halt trigger: if the kuzu_db state
contradicts research §5's "1 episode after weeks" evidence (e.g.
the file actually carries hundreds of retrievable episodes), the
M-FBM build halts and the owner re-rules the discard decision. This
script is the empirical check at amendment time.

## Usage

    loam-memory-inspect <workspace-root>

Or from canonical:

    .venv/bin/loam-memory-inspect /path/to/workspace

The script reads only; it never deletes, moves, or modifies any
file. The discard step (if D-Q.MFBM.6 stays) is a separate
operator-driven action.

## Out of scope

- Episode body extraction (would require kuzu's binary client +
  embeddings; out of M-FBM scope per ODD §2.5).
- Migration of episodes into the file-based store. Decision per
  D-Q.MFBM.6 is **discard**.
- Graphiti service control (start/stop/health). Owner can manually
  `launchctl bootout` post-M-FBM if desired; the amendment does NOT
  bootout the service.

Lives at `framework/tools/loam-memory-inspect/`. Classified
`dev_only` in `framework/tools/pos-publish-framework-only/
publish-mode-manifest.yaml`.
