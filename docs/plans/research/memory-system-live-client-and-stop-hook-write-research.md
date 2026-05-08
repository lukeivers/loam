# Research — memory-system live client + Stop-hook turn-close write

**Authored:** 2026-04-26 (background-agent dispatch).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored against HEAD:** `de5fe11`.
**Driver:** amendments #46 (sealed `2f44bbb`) and #47 (sealed
`1498c86`) closed the SessionStart-emitter and `.mcp.json`-writer
gaps. Two production-wiring gaps remain that prevent the memory
system from being live:

1. `primary_persona.session_start_emitter._default_memory_client_factory`
   returns `None`. Even with `.mcp.json` present (so Claude Code can
   discover the MCP server), the **Python persona-layer process** that
   runs at SessionStart / UserPromptSubmit has no client of its own —
   `register_memory_retrieval` is skipped, and the per-turn retrieval
   block never lands in `additionalContext`.
2. `primary_persona.memory_consumer.TurnAggregator.close_turn` has no
   production caller. Episodes are never written.

**Owner directive (locked, do not re-rule):** the turn-close write
**must be triggered by Claude Code's `Stop` hook**, not by prepending
the prior turn's aggregate to the next `UserPromptSubmit` payload.
Luke ruled this 2026-04-26. Research below treats it as a hard
constraint and designs around it.

---

## 1. Question set

Five blocks of questions, in the order the plan needs them answered:

**Q-A. Stop-hook contract.** What payload does Claude Code pass on
stdin? What's the exit-code semantics? What's the timeout? Does
stdout reach `additionalContext` or only the debug log?

**Q-B. Recoverability of user_message + persona_reply at Stop time.**
Does `transcript_path` give us both? What is the JSONL shape? Are
there other hook events better-suited?

**Q-C. Streamable-HTTP MCP client construction in Python.** What
imports? What handshake? How does a synchronous contributor
(`build_memory_retrieval_contributor`) drive an async MCP session?
Does the `mcp` package even ship in the persona venv?

**Q-D. Idempotency / firing semantics.** Does Stop fire more than
once per turn? On `/compact`? On ESC interrupt? On sub-agent
completion? How do we avoid double-writing the same episode?

**Q-E. Failure modes + cost / latency.** Memory service down,
transcript unreadable, MCP-client init failure, Stop-hook timeout.
The empirical 113s episode-extraction cost from amendment #33: how
does that interact with Stop's exit-0-allows-Claude-to-stop
contract?

---

## 2. Q-A — Stop-hook contract (verified against Claude Code docs)

Source: <https://code.claude.com/docs/en/hooks> fetched 2026-04-26.

### 2.1 When it fires

> `Stop` | When Claude finishes responding

— per-event table. **One Stop per turn.** Distinct event from
`SubagentStop` (which fires when a Claude Code subagent completes,
not the main loop).

### 2.2 Input JSON envelope (stdin)

The docs do **not** publish a Stop-specific schema; they document
*common* fields that every hook receives:

| Field             | Description |
|-------------------|-------------|
| `session_id`      | Current session identifier |
| `transcript_path` | Path to conversation JSON (JSONL) |
| `cwd`             | Current working directory when the hook is invoked |
| `permission_mode` | `"default"` / `"plan"` / `"acceptEdits"` / `"auto"` / `"dontAsk"` / `"bypassPermissions"` |
| `hook_event_name` | Name of the event that fired (`"Stop"`) |

There is **no documented `prompt` field** on Stop (as there is on
UserPromptSubmit) — the user message must be recovered from
`transcript_path`. See §3.

The docs mention that some Anthropic SDKs / tooling include a
`stop_hook_active` flag in the input on recursive Stop firings —
the docs page consulted does not name that field, but the
public Claude Code documentation in adjacent pages and the
github cookbook discussion thread reference it. **This is an
unknown the builder must verify empirically** — see §10 Q1.

### 2.3 Exit-code semantics

> `Stop` | Can block? **Yes** | What happens on exit 2: **Prevents
> Claude from stopping, continues the conversation**

- **Exit 0:** Claude continues (i.e., stops as normal).
- **Exit 2:** Blocking error. Claude is forced to continue the
  conversation.
- **Other non-zero:** non-blocking error. Stderr surfaces in the
  debug transcript; Claude still stops.

For the persona-layer's turn-close write, we want the **Claude-stops-
as-normal** semantics. Exit 0 unconditionally is the right contract,
even on internal failure (mirrors `cli_session_start` /
`cli_user_prompt_submit` from #46 — non-zero would block Claude's
flow and surface "internal hook errored" to the user, which violates
the persona's translation-layer role).

### 2.4 Decision JSON

The docs document a `decision: "block"` JSON output that has the
same effect as exit 2. We do **not** want to use this — the
persona's turn-close write is purely side-effectual (memory
persistence). Skipping the decision field + exiting 0 is the
correct shape.

### 2.5 Stdout disposition

> "For most events, stdout is written to the debug log but not shown
> in the transcript. The exceptions are `UserPromptSubmit`,
> `UserPromptExpansion`, and `SessionStart`, where stdout is added
> as context that Claude can see and act on."

**Stop is not in the exception list.** Stop-hook stdout goes to
the debug log only. This is fine — the persona-layer's turn-close
write doesn't need to feed text back to the model; it just needs to
persist the aggregated episode.

### 2.6 Timeout

Documented defaults: 600s for command hooks, 30s for prompt hooks,
60s for agent hooks. Stop is a command hook — **default 600s**.
Per-hook override: `"timeout": <seconds>` field in the inner-hook
envelope.

The hook subprocess returns to Claude Code when its own command
exits. The asyncio-create_task non-blocking pattern from amendment
#33 means our Stop hook can return in milliseconds: the subprocess
schedules a background asyncio task and exits 0. **The 113s
extraction happens inside the spawned task, not inside the hook
subprocess.**

But wait — the hook subprocess is short-lived. A `create_task` in a
short-lived process **dies with the process**. See §6.2 for the
reach-for resolution: spawn a detached subprocess (the
`hands-off-lifecycle/hooks/first-run.sh` detachment pattern is the
shipped precedent in this codebase).

---

## 3. Q-B — Recovering user_message + persona_reply at Stop time

### 3.1 transcript_path is the only documented source

The Stop hook input carries `transcript_path` — every other
recovery surface (the persona's prior `UserPromptSubmit` invocation,
in-process state, a sidecar file the SessionStart emitter writes)
would either require a new persistent surface or piggy-back on
process state that doesn't survive between hook invocations (each
hook is a fresh subprocess).

**The transcript IS the canonical surface.** Read it; pull the last
user message + last assistant reply; aggregate; persist.

### 3.2 JSONL format — undocumented on the hooks page

The docs page does not publish a per-line schema. From the
amendment #46 builder plan §3 D-build.3 confirmation flow + the
publicly-visible Claude Code JSONL examples in the wider
documentation set:

- The transcript is line-delimited JSON. Each line is one event.
- Events include user messages, assistant replies, tool calls,
  tool results, hook results, system events, and meta events
  like compaction.

**Builder must verify the schema empirically before relying on it.**
The shape is stable enough to power public tools (e.g. `claude-trace`
parses these), but it is not contractually documented. Tools that
read JSONL in pos-v2 already exist (`orchestrator/`'s session
recovery walks the transcript); the builder should compose against
that existing surface where possible — see §6 and §10 Q2.

### 3.3 The shape we need

For the turn-close write we need:

- The most recent user message (text content)
- The most recent assistant reply (text content)
- A turn identifier — `session_id` plus a turn-counter is the
  cheapest stable shape (the transcript itself doesn't number
  turns, but the count of user-message-shaped lines up to the
  current Stop event is a stable monotonic id)

A "last user message + last assistant reply" walk from the tail of
the JSONL until both are found is the simplest extraction. The
walk skips tool-use / tool-result / system events.

### 3.4 Edge cases for transcript reads

- **First Stop after SessionStart** — the transcript exists but
  contains only one user message and one reply. Standard case.
- **Stop after `/compact`** — see §5 §Q-D. The transcript may have
  been rewritten / truncated; the "last user message" semantics
  still hold but the prior turn boundary may be inside compaction
  output. We treat this as a degraded case; if the extraction
  produces an empty or compacted-block-shaped reply, we skip the
  write (no episode is better than a malformed one).
- **Stop after ESC interrupt** — see §Q-D. The reply may be
  truncated mid-stream. The transcript line should still contain
  the partial assistant text up to the interrupt. We persist what's
  there; this is data the user actually saw.
- **Stop while a sub-agent's `SubagentStop` fires concurrently** —
  these are distinct events on distinct hooks. `Stop` is what we
  register against. `SubagentStop` only fires from a subagent's
  Stop; the docs explicitly state subagent Stop hooks "are
  automatically converted to SubagentStop." We do NOT register on
  SubagentStop in this amendment.

---

## 4. Q-C — Streamable-HTTP MCP client construction in Python

### 4.1 Package + import path

Confirmed from the in-tree memory-system venv at
`memory-system/.venv/lib/python3.13/site-packages/mcp/`:

- `mcp` package ships the client surface.
- `mcp.client.streamable_http` exposes the streamable-HTTP transport.
- Function: `streamable_http_client(url, *, http_client=None,
  terminate_on_close=True)` — `@asynccontextmanager`. Yields
  `(read_stream, write_stream, get_session_id)`.
- A deprecated `streamablehttp_client` (no underscore) exists as a
  legacy alias — **do not use**; the canonical name is
  `streamable_http_client`.
- Session: `mcp.ClientSession(read_stream, write_stream)` — also
  an async context manager. `await session.initialize()` performs
  the MCP handshake. `await session.call_tool(name, arguments=dict)`
  invokes a tool; returns `CallToolResult` with `content` (list of
  `TextContent` etc.) + `structuredContent` + `_meta`.

### 4.2 The persona venv currently does NOT have `mcp`

The persona's `pyproject.toml` declares no `mcp` runtime dep; the
package is shipped only in the `memory-system/.venv` (because the
service is the MCP server, not a client). **The plan must add
`mcp` to the persona venv** — `mcp` is already in the host's wider
dependency graph (used by FastMCP service); adding it to the
persona's runtime declared deps is a Python-package change, well
inside the `primary-persona/` fence.

This is a **runtime dep addition**. Per pos-v2 STATE.md rule #8,
the persona's brief permits the persona's declared runtime deps;
adding one is a method-level decision but the AC for it is
"persona-layer can construct a live MCP client and call its
tools" — outcome. Builder's call which Python package surfaces it
(stick with the canonical `mcp` from PyPI; alternatives like
`fastmcp` ship a higher-level client too — research lean below).

### 4.3 Sync ↔ async bridge

The composer's contributor callables are synchronous (D8 / #32).
`memory_consumer.build_memory_retrieval_contributor` already bridges
sync→async via `_run_async` (memory_consumer.py:267) — it wraps
asyncio in a temp loop or thread pool. The same bridge handles
`session.initialize()` + `session.call_tool(...)` with no new code.

The `MemoryClient` Protocol (memory_consumer.py:63) declares an
`async def add_episode(...)` and `async def search(...)`. A live
adapter that calls `await session.call_tool("add_episode", ...)`
inside those methods conforms to the Protocol. The Protocol is
already correctly typed for a streamable-HTTP MCP client.

### 4.4 Adapter shape

The adapter has two concerns:

1. **Connection lifetime.** The async-context-manager pattern
   `async with streamable_http_client(...) as (...): async with
   ClientSession(...) as session: await session.initialize()` is
   per-call expensive: a fresh handshake on every search would
   inflate per-turn latency. Two shapes:
   - (a) Open-connection-per-call (simple, slow).
   - (b) Persistent connection lifecycle managed at adapter
     construction (faster, but the adapter has to own a
     long-running asyncio loop or background thread).
2. **Tool name mapping.** `session.call_tool("add_episode",
   arguments={...})` returns `CallToolResult`; the `MemoryClient`
   Protocol callers expect a `dict[str, Any]`. The adapter
   translates `result.structuredContent` (or parses
   `result.content[0].text` JSON) into the dict shape memory-system's
   `_impl_add_episode` returns.

**Research lean (option (a)):** the persona's hook subprocess is
short-lived (each Stop / SessionStart / UserPromptSubmit runs in
a fresh process). A persistent connection has nowhere to live. The
adapter opens-and-closes per call; the cost is a single TCP
roundtrip on loopback (microseconds) plus the MCP handshake (one
JSON-RPC `initialize` round-trip, also microseconds on loopback).
Total adapter overhead per call: well under 100ms even on a busy
machine. This is well inside the `additionalContext` envelope
research budget. The 113s cost dominates and is server-side.

### 4.5 The empirical 113s figure — what's affected?

- `search` is fast (no LLM call; pure graph traversal); it's the
  retrieval contributor's per-turn cost. ~ms-to-tens-of-ms.
- `add_episode` is the 113s case (LLM-driven entity + edge
  extraction). It's the Stop-hook write cost.

The Stop-hook subprocess **must not block 113s**. See §6 for the
detached-write pattern.

---

## 5. Q-D — Idempotency / firing semantics

### 5.1 Documented Stop firing

> `Stop | When Claude finishes responding`

Per-turn. **Not per-message** — Claude streams a single message
per turn, so one Stop per assistant-reply.

### 5.2 Undocumented edges (must verify empirically)

- **`/compact`** — the docs do not state whether `/compact`
  triggers Stop. Empirical observation in pos3 (the test workspace)
  is needed. **Listed as Q3 in §10.**
- **ESC interrupt** — the docs do not state whether an ESC-
  interrupted turn fires Stop. Empirical observation needed.
  **Listed as Q4 in §10.**
- **`stop_hook_active`** — the docs page consulted does not name
  this field, but cookbook discussion threads in adjacent
  Anthropic documentation reference it on recursive Stops. The
  flag, if present, signals that the Stop hook itself is what
  caused Claude to continue (via exit-2). **Builder must verify
  empirically whether the field arrives — listed as Q1 in §10.**
- **Sub-agent completion** — docs explicitly state SubagentStop is
  the event for subagent-Stop conversions. Stop fires only on the
  main loop. **No special handling needed; we register on Stop only.**

### 5.3 Idempotency mitigations regardless of firing semantics

The aggregator-and-write surface should be idempotent on its own:

- **Turn-id derivation.** The Stop hook can derive a stable turn
  id from `(session_id, transcript_line_count)` or `(session_id,
  hash(last_user_message))`. Two Stops on the same turn produce
  the same id; the writer can skip duplicates with a dedupe
  cache (in-process or filesystem-marker).
- **Filesystem marker as the simplest shape.** Write a tiny
  per-turn marker file before the asyncio task starts:
  `<workspace>/.pos/last-turn-id`. If a re-firing Stop sees the
  same id already on disk, it no-ops. Mirrors the
  `hands-off-lifecycle/hooks/first-run.state` pattern.
- **`stop_hook_active`-aware** (when the field arrives): if
  `stop_hook_active=True`, skip the write entirely (the prior
  Stop already started one).

The exact mechanism is method, not AC. The AC is "exactly one
episode per user↔AI turn (AC-D7.2 inheritance)."

---

## 6. Q-E — Failure modes + cost / latency

### 6.1 Failure modes the design must handle

| Mode | Required behaviour | Where in the design |
|------|--------------------|---------------------|
| Memory service down | Persona stops as normal; no episode persisted; no error to user | Stop-hook subprocess exits 0 unconditionally; the spawned async task catches `Exception` from the MCP client and logs to stderr only |
| Transcript unreadable | Persona stops as normal; no episode | Read-fail in the Stop CLI returns "" payload, exit 0 |
| MCP-client init failure | Persona stops as normal; no episode | Adapter raises; aggregator catches; exit 0 |
| Stop hook timing out | Persona stops as normal (Claude's view); the user is unblocked; the unfinished write logs as a warning | The hook subprocess returns in <100ms regardless of the asyncio task fate (see §6.2) |
| Double-fire (recursive Stop / `/compact` / sub-agent leak) | Single episode persisted | Turn-id idempotency (§5.3) |

### 6.2 Why the asyncio-create_task pattern alone is wrong here

`memory_consumer.TurnAggregator.close_turn` schedules an
`asyncio.create_task` on the caller's running loop. This works in
unit-test fixtures (the test loop stays alive). It **does not
work** when the caller is a short-lived hook subprocess: as soon as
`cli_stop()` returns and the process exits, the task is cancelled
mid-execution, and the 113s extraction is killed.

**Two reach-for resolutions:**

- **(a) Drive the write synchronously in the Stop subprocess.** Wait
  for `add_episode` to complete before returning exit 0. Bad: 113s
  blocks the subprocess; default timeout 600s lets it complete, but
  any fan-out to other Stop hooks queues behind us; the user sees no
  problem (Claude has already stopped to them as far as they know,
  but the next prompt may stall on the still-running hook). Worse:
  if `pos-v2`'s Stop subprocess is the only Stop registration and a
  user types fast, the second turn is held until the first turn's
  episode finishes extracting.
- **(b) Spawn a detached background subprocess.** The Stop hook
  CLI fork-exec's a fully-detached child process that does the
  MCP write; the parent (Stop hook) returns immediately with exit 0.
  Mirrors `hands-off-lifecycle/hooks/first-run.sh`'s detachment
  pattern (which spawns the worker via a similar fork/disown).

**Research lean (option (b)):** the detachment pattern is already
shipped in this codebase, the precedent is canonical, and it
preserves the "Claude stops as normal" semantic without holding
Claude's hook fan-out for 113s. Method-level: builder confirms the
detachment shape against the first-run.sh script's flow.

### 6.3 Cost / latency budget

**Per-turn cost (steady state):**

- `search` (UserPromptSubmit retrieval contributor): ms-scale.
- `add_episode` (Stop background subprocess): 113s server-side
  (LLM-driven extraction). Free at Claude Max subscription; ~$0.02
  pay-per-token. Annual at 20 turns/day: ~$146/year (per
  amendment #33 research §3.2).

**Per-turn user-visible latency:**

- UserPromptSubmit retrieval: bounded by hook timeout (5s, per
  amendment #46) + per-call envelope (sub-second on loopback).
- Stop hook subprocess return: bounded by detachment time
  (milliseconds — the parent does fork+exec+exit, no wait on the
  child).

**Subscription throughput pressure:** 20 turns/day × 113s sequential
extractions = 37.7 minutes/day of background graphiti / Haiku 4.5
work. The subscription absorbs this; live human user is not
blocked. Aligned with amendment #33's existing analysis.

---

## 7. Options analysis (ruled directions)

### 7.1 Where the live MCP client lives

Three places it could live:

1. **Inside the persona's session_start_emitter.** The
   `_default_memory_client_factory` becomes a real factory that
   returns a `LiveMCPMemoryClient(...)` — straightforward
   replacement of the current `return None`. **Recommended.**
2. **Inside a new dedicated module under primary-persona** (e.g.
   `primary_persona/mcp_client.py`). Cleaner separation; the
   factory function in `session_start_emitter.py` imports it.
   Equivalent outcome; method-level shape.
3. **Outside primary-persona** (e.g. a new top-level package).
   No reason to do this — the persona is the only consumer and
   the dep fence is well-defined.

### 7.2 Where the Stop hook handler lives

Three places the Stop hook subprocess could live:

1. **A new CLI subcommand on `primary_persona.cli`.**
   `python -m primary_persona.cli stop`. Mirrors the
   session-start / user-prompt-submit pattern from #46. The
   subcommand reads stdin JSON, calls into a new
   `stop_emitter.handle_stop(workspace_root, envelope)` function,
   exits 0. **Recommended.**
2. **A new CLI subcommand on `hands-off-lifecycle`.** Wrong
   layer — hands-off-lifecycle owns hook *registration* (the
   merge-into-settings.json plumbing); the persona owns hook
   *handlers*. Recommendation: continue the existing split.
3. **A dedicated executable / shell script.** Worse for testing;
   the Python subcommand pattern is the established precedent.

### 7.3 Where the Stop hook is registered in settings.json

The `hands-off-lifecycle/hooks/first_run_settings.py` already
exposes `merge_session_start` (#37) + `merge_user_prompt_submit`
(#46). The Stop hook needs an analogous **`merge_stop`**
function, plus a `_persona_stop_stanza` helper, plus three call-
site invocations in `first_run_helper.py` (Phase 3d, Phase 4c,
Phase 6) mirroring the UserPromptSubmit helpers.

This is mechanically isomorphic to amendment #46's
`merge_user_prompt_submit` work. The plan can lean heavily on
the precedent.

### 7.4 Where TurnAggregator's close_turn is invoked from

The Stop CLI subcommand is the call site. It:

1. Reads stdin JSON envelope.
2. Loads transcript at `transcript_path`; extracts the last
   user_message + last assistant_reply by walking the JSONL
   tail.
3. Constructs a turn_id.
4. Idempotency check (skip if already-seen turn).
5. Spawns a detached background process (per §6.2) that:
   - Constructs the live MCP client.
   - Constructs a `TurnAggregator`.
   - Calls `close_turn(turn_id=..., user_message=...,
     persona_reply=...)`.
   - Awaits the returned task to completion.
   - Logs success / failure to a sidecar file (so a future
     awareness-block contributor can surface failed writes per
     amendment #33's note about D9 OTel).
6. The parent (Stop CLI) exits 0 immediately.

---

## 8. Bringing the design down to ACs (handed to the plan-doc)

The plan-doc covers ACs in detail; this section sketches the shape
the research suggests so the plan can audit forward+reverse.

**Two amendment-level closures:**

1. **Live MCP memory client in the persona venv.** The
   `_default_memory_client_factory` returns a real client; the
   persona venv declares the `mcp` package as a runtime dep; the
   live adapter conforms to the existing `MemoryClient` Protocol.
   Both `register_memory_retrieval` (UserPromptSubmit) AND the
   Stop-hook write path use this same client.

2. **Stop-hook turn-close write.** A new `stop` CLI subcommand on
   `primary_persona.cli` reads the Stop envelope, recovers
   user_message + persona_reply from `transcript_path`,
   detaches a background process that drives `TurnAggregator.
   close_turn(...)` to completion. A new `merge_stop` in
   `hands-off-lifecycle/hooks/first_run_settings.py` registers
   the Stop hook in `.claude/settings.json`. Three call sites in
   `first_run_helper.py` invoke it (Phase 3d, Phase 4c, Phase 6).

These two pieces are tightly coupled (both require the live
client) and should ride on a single amendment cycle. The
sealed-component fence is clean: `primary-persona/` +
`hands-off-lifecycle/`. No other sealed component is touched.

---

## 9. Three-lens read

**Lens 1 — Claude leverage.** The Stop hook is Claude-native; no
custom polling, no orchestrator-side daemon, no recurring scope.
The MCP `streamable_http` client surface is part of Claude's
broader MCP ecosystem; the persona consumes it the same way every
other MCP-aware Python tool does. **Composing on Claude primitives,
not re-implementing them.**

**Lens 2 — Harness + primary-persona value.**

- *Primary-persona test:* YES, load-bearing. Without this, every
  user turn is a new conversation in memory's eyes. Long-arc
  memory ("yesterday Luke said X") simply does not exist. The
  translation layer can't translate intent that depends on
  history because there is no history.
- *Harness test:* YES. The live MCP client is a primitive every
  future persona-side memory consumer (and there will be more —
  the awareness block, the proactive surfacing, the corpus
  retrieval extension) draws against. The Stop-hook handler is a
  primitive future hook handlers (e.g., a workflow-end emitter)
  compose alongside.

**Lens 3 — ODD authoring.** ACs are outcome-shaped; behaviour
count maps cleanly; the §2.5 reverse-direction surface is
constrained (single sealed-component fence, well-known precedents
for each new file/symbol). No method prescription needed in any
AC.

---

## 10. Surfaced unknowns / open questions for owner ruling

The plan author should treat each of these as a flagged inference
in the plan's "decisions for owner" block; they are method-level
or empirical-verification questions that don't require Luke's
judgement at research time but will require it at plan-review time
or build time.

**Q1 — `stop_hook_active` field empirical verification.** The
docs page consulted does not document the field. Adjacent
documentation references it. Empirical verification (one Stop
hook firing in pos3 with `cat > /tmp/stop_input.json` ahead of
the build) closes this. **Recommendation:** verify before build;
if absent, the turn-id idempotency pattern (§5.3) is sufficient
on its own.

**Q2 — Transcript JSONL schema empirical verification.** Builder
must read 2-3 real transcripts in pos3 before relying on the
`type: "user" | "assistant"` walk. **Recommendation:** verify;
the orchestrator's existing transcript-reading code is a
candidate composition surface (composing on it would compose
on a sealed-component surface, which is a halt-trigger; the
plan should NOT compose on orchestrator surfaces).

**Q3 — Does Stop fire on `/compact`?** Empirical, fire one
`/compact` in pos3 with the new Stop hook tee'd. **Recommendation:**
verify; design treats compaction-Stops as graceful-no-op (the
last user message in a compacted transcript is the compaction
prompt, not a real user turn).

**Q4 — Does Stop fire on ESC interrupt?** Empirical. **Recommendation:**
verify; design treats ESC-Stops as best-effort (persist what's in
the transcript; if the assistant reply is empty, skip).

**Q5 — Detachment shape — fork-exec or new-subprocess.** Method
level. The first-run.sh detachment pattern uses a shell-script
disown; the Python subprocess detachment uses
`subprocess.Popen(..., start_new_session=True,
stdin/stdout/stderr=DEVNULL)`. Either works; the Python pattern is
preferred for testability. **Recommendation:** Python `Popen`
with detached session; mirrors how `hands-off-lifecycle` already
spawns its detached worker from Python.

**Q6 — Where the persona's runtime sidecar lives.** The Stop
detached process needs a place to log success/failure (so a
future awareness-block contributor can surface failed writes).
Two candidates:
- `<workspace>/.pos/memory-writes.log` (workspace-local; simple).
- The orchestrator's existing scope-of-work event log (richer;
  but composes onto a sealed-component surface — disallowed by
  amendment #33's existing fence).
**Recommendation:** workspace-local sidecar log file. Plan-level
decision.

**Q7 — `mcp` package version pin.** The persona venv currently has
no `mcp` dep. Pinning a specific version vs floating-with-bound is
method. **Recommendation:** pin to the version present in
`memory-system/.venv` to ensure persona client matches server's
protocol.

**Q8 — Does Claude Code's Stop hook stdin envelope carry a way to
distinguish "stopped because Claude finished" from "stopped because
of a tool refusal" or "stopped because of /compact"?** The
documented common fields don't surface this. **Recommendation:**
treat all Stop firings the same; the transcript walk produces an
empty reply on weird firings (compact, refusal); we skip those.

---

## 11. Halt conditions / ODD violations surfaced

None during research. The amendment scope as designed is clean:

- `primary-persona/src/` — extend with `mcp_client.py` (or
  emit-module-internal) + `stop_emitter.py` + `cli.py` `stop`
  subcommand. **Inside fence.**
- `primary-persona/pyproject.toml` — add `mcp` runtime dep.
  **Inside fence.**
- `hands-off-lifecycle/hooks/first_run_settings.py` — add
  `merge_stop` + `_is_pos_v2_owned_stop` + marker set. **Inside
  fence.**
- `hands-off-lifecycle/hooks/first_run_helper.py` — add
  `_persona_stop_stanza` + `_maybe_merge_stop` + three call-site
  invocations. **Inside fence.**
- Test files in both components. **Inside fence.**
- Universal-paths admissions (`docs/plans/`, etc.).
  **Inside fence.**

No surrounding-code §2.5 violations spotted. The
`memory_consumer.py`, `session_start_emitter.py`, and
`first_run_settings.py` surfaces are AC-backed (AC-D7.x, AC46.x,
AC.45.x respectively). No silent exception branches in the new
code paths the plan introduces.

---

## 12. Cost summary (for plan-doc inclusion)

- Build budget: medium — 8-12 hours of agent wall-clock based on
  amendment #46's actual cost (mechanically isomorphic work,
  similar surface area).
- Runtime budget per turn: bounded.
- Annual memory cost: ~$146/year at 20 turns/day pay-per-token,
  or subscription-absorbed at Claude Max. Same as amendment #33's
  baseline; nothing new.

---

## 13. References

- Claude Code hooks docs:
  <https://code.claude.com/docs/en/hooks> (fetched 2026-04-26)
- Claude Code MCP docs:
  <https://code.claude.com/docs/en/mcp> (consumed at amendment
  #47 dispatch; same source the plan-doc references)
- `mcp.client.streamable_http`:
  `memory-system/.venv/lib/python3.13/site-packages/mcp/client/streamable_http.py`
- D7 research:
  `docs/plans/research/amendment-33-memory-consumer-wiring-research.md`
- D7 plan:
  `docs/plans/amendment-33-memory-consumer-wiring-primary-persona.md`
- Umbrella plan:
  `docs/plans/memory-into-context-integration.md`
- #46 builder plan (sibling pattern for hook-CLI authoring):
  `docs/plans/amendment-46-persona-session-start-turn-start-emitters.builder-plan.md`
- #47 builder plan (sibling pattern for `.mcp.json` writer + the
  half of the pair we are NOT re-doing here):
  `docs/plans/amendment-47-workspace-local-mcp-json-writer.builder-plan.md`
- Memory consumer substrate:
  `primary-persona/src/memory_consumer.py`
- Session-start emitter (where `_default_memory_client_factory`
  lives): `primary-persona/src/session_start_emitter.py:74`
- Persona CLI (where the new `stop` subcommand goes):
  `primary-persona/src/cli.py`
- Settings.json merge surface (where `merge_stop` goes):
  `hands-off-lifecycle/hooks/first_run_settings.py`
- First-run helper (where `_maybe_merge_stop` calls land):
  `hands-off-lifecycle/hooks/first_run_helper.py`
- ODD methodology + ODD-in-pos: `docs/odd-methodology.md`,
  `docs/odd-in-pos.md`
- `docs/VALUE_PROPOSITION.md`,
  `docs/STATE.md`,
  `docs/FUTURE_IDEAS.md`
