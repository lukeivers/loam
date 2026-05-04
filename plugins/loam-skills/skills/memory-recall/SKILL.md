---
description: Recall prior-session context from a file-based memory store before answering a question or starting a task. Use when the user references prior work ("what we discussed", "the thing we were doing"), when answering would benefit from continuity across sessions, or when the persona needs to ground a response in earlier decisions. Reads markdown episode files; falls back to filesystem search when no structured store is present.
---

# memory-recall

Cross-session continuity by reading from disk. Loam treats files
as the only memory surface — episodes from prior turns persist as
markdown on the local filesystem, and recall is a directed read
of that store before the persona answers. This skill captures
that pattern so the persona doesn't confabulate prior decisions
or ask the user to repeat themselves.

## What this skill captures

Loam's M-FBM (file-based memory) component writes one markdown
file per turn under `<workspace>/.loam/memory/episodes/<group>/<date>/<turn>.md`.
Frontmatter carries the turn's metadata (group, date, brief,
references); the body carries the persona's reasoning + outputs
worth replaying. A sqlite-FTS5 index at
`<workspace>/.loam/memory/index.sqlite` enables ranked search.

This skill names the recall pattern so the persona can:

1. Recognise turn intents that need prior context (entity names
   the user dropped, project mentions, decisions referenced
   in passing, "the X we were working on").
2. Read targeted episode files BEFORE answering.
3. Cite the recalled material so the user can verify provenance.

## When to use

Trigger phrases the persona should recognise:

- "what we discussed" / "what we decided" / "where we left off"
- "the [entity / project / decision] we were working on"
- "before this session" / "last time" / "earlier today"
- A bare entity name the persona doesn't currently have in context
  but suspects appears in prior episodes.

Also use proactively when answering would benefit from continuity
even when the user didn't explicitly invoke prior context.

## How the persona applies it

1. **Identify the recall query.** Extract the entity / topic /
   decision-name from the user's turn. If the query is fuzzy,
   expand to 2-3 likely keyword combinations.
2. **Search the structured store first.** When the workspace has
   `<workspace>/.loam/memory/index.sqlite`, query the FTS5 index
   with BM25 ranking (top-N matches with file paths + previews).
3. **Read the top matches.** Open the highest-ranked episode
   files. Frontmatter first (cheap shape-check); body if the
   frontmatter passes the relevance filter.
4. **Cite the source path.** When responding, reference the
   episode path so the user can verify ("per episode
   `episodes/<group>/<date>/<turn>.md`, you decided X").
5. **Surface gaps.** If the recall returns nothing relevant,
   say so plainly. Don't invent prior context.

## Graceful degradation

When no `<workspace>/.loam/memory/` directory exists (raw Claude
Code session, no loam workspace):

1. Look for memory artefacts in standard locations: project-local
   `.claude/`, `~/.claude/projects/<slug>/memory/`, scratch
   directories the user mentioned.
2. Use filesystem search (Glob, Grep) over markdown files in the
   working directory + obvious sibling paths.
3. If no memory surface is reachable, ask the user to paste prior
   context rather than guess.

## Composition

- **Loam's primary persona** ships an M-FBM retrieval contributor
  that auto-injects a 1600-char retrieval block per UPS-hook event.
  This skill extends that surface — when the auto-block is
  insufficient, the persona invokes `memory-recall` for deeper
  retrieval.
- **`memory-search` skill** (in
  `framework/primary-persona/skills/`) is the user-invocable verb
  for ad-hoc search. This `memory-recall` skill is the
  pattern-recognition + auto-application companion.
- **v0.1.5 progressive disclosure (D-1)** — when L1/L2/L3 retrieval
  ships, this skill's body will reference the preview-then-expand
  surface. Until then, full episode reads are the default.

## Out of scope

- Cross-workspace recall (each workspace's memory is scoped to its
  own group_id; intentional isolation).
- Auto-archival of old episodes (separate `memory-archive` skill).
- Embedding-based / cross-encoder retrieval (deferred to v0.2+
  M-GMP graphiti plugin or equivalent).
- Writing to memory (this is a read-side skill; writes happen at
  Stop-hook time).
