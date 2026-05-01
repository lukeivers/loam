# memory

## What it does

Memory is loam's session-bridging substrate. Raw Claude is
goldfish-memoried — every session starts blank. The memory
component lets the primary persona load relevant context when a
session opens and persist salient observations when a session ends,
so the next session is not a cold start.

v0.1.0 ships a **file-based** memory substrate as the default. It
is plain text on disk, written and read by the persona's hooks at
session boundaries; you can inspect it, edit it, version-control
it, or wipe it without any database tooling. A richer
graph-of-episodes substrate (Graphiti) is planned as a v0.1.x
plugin (`graphiti-memory`) for users who want semantic recall
beyond what the file-based form provides.

## How to invoke

You do not invoke memory directly. The primary persona reads it
at SessionStart and UserPromptSubmit and writes it at Stop. The
relevant Claude Code seams are the corresponding lifecycle hooks,
owned by `primary-persona` (read) and `primary-persona` +
plugin contributions (write).

Two opt-in user surfaces:

- **Asking the persona about memory.** "What do you remember
  about project X?" — the persona surfaces what it has stored.
- **Writing intentional memory.** "Remember that I want
  weekly summaries on Mondays." — the persona writes the
  observation explicitly rather than passively.

There is no separate `loam memory` CLI in v0.1.0; the memory
files are plain enough to read by hand if you need to.

## Observable surface

What you can `tail` / `cat` / `grep` to see memory working:

- **The memory store on disk.** File-based; lives under
  `framework/primary-persona/`'s data area. Each entry is a
  plain text record with a timestamp, scope id, and content
  fields. You can `cat` or `grep` directly.
- **OTel spans.** `loam.primary_persona.memory.*` namespace.
  Each read at SessionStart / UserPromptSubmit emits a span
  with the entries returned; each write at Stop emits a span
  with the entries appended.
- **The persona's greeting.** SessionStart loads memory and
  surfaces relevant entries in the greeting; if you see the
  persona reference past context, that came from memory.

## Stable surfaces (for plugin authors)

The memory layer is fronted by a `MemoryProvider` Protocol — the
same interface the v0.1.x `graphiti-memory` plugin will implement
to provide a richer substrate. Plugin authors writing memory
contributions or alternative substrates implement the Protocol;
`workspace-bootstrap` composes the active provider into the
persona's hooks.

For internal implementation detail see the component source under
`framework/primary-persona/` (the file-based memory primitive lives
inside the primary-persona component).
