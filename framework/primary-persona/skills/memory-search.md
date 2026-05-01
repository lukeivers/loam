---
name: memory:search
description: Search the loam file-based memory store for episodes matching a query. Returns the top-N matching episodes with their filename + path, beyond the 1600-char turn-budget block the persona injects per UPS event. Use when the user wants to find prior turns about a specific topic, an entity, or a project; or when the persona needs deeper retrieval than the auto-injected memory-retrieval block.
---

# /memory:search — file-based memory deeper retrieval

This skill is the user-facing entry-point for searching loam's
file-based memory store beyond the per-turn 1600-char retrieval
budget.

## What this skill does

1. Asks the user for a search query (or accepts one inline).
2. Reads the workspace's memory dir at
   `<workspace>/workspace/.loam/memory/episodes/<workspace-slug>/`.
3. Ranks matches by sqlite-FTS5 BM25 when available; falls back to
   a grep-based scan of the most recent ~200 episode files.
4. Returns the top-N episodes with their filename, path, and a
   short content preview.

## Usage

The skill is composed by the persona; the user invokes it with
`/memory:search <query>` in chat. The persona returns a structured
list:

    /memory:search dispatch_with_scope wiring

→

    [memory-search results, query="dispatch_with_scope wiring"]
      1. turn/<id>.md (2026-04-29) — preview of episode body
      2. turn/<id>.md (2026-04-28) — preview of episode body
      …

## Underlying mechanics

- File-based store at `<workspace>/workspace/.loam/memory/episodes/`.
- One markdown file per turn (D-Q.MFBM.1).
- Content + frontmatter authored at Stop-hook write time.
- BM25 ranking via sqlite-FTS5; fallback to grep-based term-count.
- `group_id` filtering: defaults to the persona's workspace slug
  (matches the auto-retrieval contributor's filter).

## Composition

This skill assumes:

- The workspace's primary persona is loaded.
- The workspace's memory dir exists (`workspace-bootstrap`
  ensures this at first-run; the file-based store also lazy-creates
  on first write).

## Out of scope

- Cross-workspace search (each workspace's memory is scoped to its
  own slug per AC.MFBM.5).
- Auto-memory at `~/.claude/projects/<slug>/memory/` (orthogonal
  per D-Q.MFBM.4; Claude-managed; loam never touches it).
- Embedding-based / cross-encoder retrieval (deferred per plan §8;
  M-GMP / future plugin).
