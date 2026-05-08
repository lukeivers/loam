# memory

## What it does

Memory is loam's session-bridging substrate. Raw Claude is
goldfish-memoried — every session starts blank. The memory
component lets the primary persona load relevant context when a
session opens and persist salient observations when a session ends,
so the next session is not a cold start.

v0.1.0 ships **file-backed episode memory** (FBE) as the canonical
substrate. Memory entries are plain markdown files on disk, written
by the persona's Stop hook and read at SessionStart and
UserPromptSubmit. You can inspect, edit, version-control, or wipe
the memory store without any database tooling.

The memory component is documented under its own
`docs/components/memory.md` because it is a load-bearing user-facing
contract; the implementation lives inside the
[`primary-persona`](primary-persona.md) component
(`file_memory.py`, `memory_write_queue.py`, `memory_write_worker.py`,
`stop_emitter.py`, `session_start_emitter.py`) because session-
boundary memory load/write is the persona's contract. There is no
separate `framework/memory/` directory.

## How to invoke

You do not invoke memory directly. The primary persona reads it
at SessionStart and UserPromptSubmit and writes it at Stop. The
relevant Claude Code seams are the corresponding lifecycle hooks,
owned by `primary-persona` (read + write).

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

- **The memory store on disk.** Lives at
  `<workspace>/.loam/memory/` — one markdown episode file per
  turn, named with timestamp + scope id. You can `cat` or `grep`
  directly. The path is returned by
  `memory_dir_for_workspace()` in the implementation.
- **The write queue.** Stop-hook writes are queued to disk first
  (so a Stop hook completes quickly) and drained to the episode
  store by a worker. Queue files live alongside the episode store;
  drain progress is observable from the worker's diagnostic log.
- **Diagnostic log.** Memory-primitive errors and write-queue
  state surface at `<workspace>/.pos/memory-writes.log`. The
  memory primitive is failure-soft — first-session errors do not
  block the persona's greeting; they surface here for inspection.
- **OTel spans.** `loam.primary_persona.memory.*` namespace.
  Each read at SessionStart / UserPromptSubmit emits a span
  with the entries returned; each write at Stop emits a span
  with the entries appended.
- **The persona's greeting.** SessionStart loads memory and
  surfaces relevant entries in the greeting; if you see the
  persona reference past context, that came from memory.

## Stable surfaces (for plugin authors)

The memory layer is fronted by a `MemoryProvider` Protocol —
plugin authors writing alternative memory substrates implement
the Protocol and contribute a memory client through the
[`workspace-bootstrap`](workspace-bootstrap.md) extension
protocol. The default file-backed memory client
(`build_file_backed_memory_client` per AC.MFBM.5) is composed
into the persona's hooks unless a plugin replaces it.

A richer graph-of-episodes substrate is **post-v0.1.0 backlog**
on the release roadmap; the file-backed substrate is canonical
for v0.1.0 through at least v0.3.x. Plugin authors who want
semantic recall beyond markdown grep should consult the release
roadmap before implementing.

For internal implementation detail see the component source under
[`framework/primary-persona/`](../../framework/primary-persona/)
(the file-based memory primitive lives inside the primary-persona
component).
