# Background-agent dispatch — Task tool, run_in_background, Monitor

## Surface

Background-agent dispatch is the parallelism primitive that
runs work asynchronously while the main session stays
interactive. Three composable mechanisms:

1. **Task tool / Agent dispatch.** The persona dispatches a
   subagent via the `Task` tool (also surfaced as the
   general-purpose agent / `/agents` slash command). The
   subagent runs a scope-only prompt, has its own tool
   surface, and reports back when done. Sub-agents can spawn
   their own sub-agents — nesting up to 5 levels deep — since
   Claude Code 2.1.172 (changelog-verified live 2026-06-11;
   supersedes the earlier no-recursion limit. The sub-agents
   docs page still carried the older no-recursion statement
   on 2026-06-11 — docs lag; the changelog is the
   release-truth source for shipped behaviour).
2. **`run_in_background` Bash.** The Bash tool's
   `run_in_background: true` parameter starts a long-running
   shell command that streams output for later retrieval —
   useful for builds, test suites, file watchers.
3. **Monitor.** Streams events from a background process
   (each stdout line is a notification). For "wait until
   done" semantics, Bash with `run_in_background` is the
   one-shot path; for "stream events as they arrive",
   Monitor is the right reach.

The persona's default is to push long-running or
multi-artefact work to background, keeping the main session
free for owner conversation.

## Inputs/outputs

**Task tool.** Inputs: a `description` (short; for the
caller's view), a `prompt` (the agent's full instructions —
scope-only per the dispatch CDC), a `subagent_type`
(general-purpose / specialised). Outputs: the agent's final
report, returned synchronously when the agent halts. Token
usage and cost are scoped to the agent's own context;
relays back as a final assistant message.

**`run_in_background` Bash.** Inputs: the bash command, a
`run_in_background: true` flag, an optional timeout.
Outputs: a background task handle the caller polls or
monitors via the Read or Monitor tools.

**Monitor.** Inputs: a process / log path. Outputs: an
event stream that yields per-line notifications until the
process exits or the caller halts the watch.

## Composition notes

Background-agent dispatch composes with virtually every
other primitive:

- With `/schedule`: the scheduled routine dispatches a
  background agent for the per-run work.
- With `/loop`: each loop iteration may dispatch a
  background agent, keeping the main loop's polling fast.
- With Telegram-interface: long-running background work
  surfaces final outputs to the user's Telegram channel
  rather than waiting for them to return to Claude Code.
- With memory-system: background agents can write episodes
  through the memory-system's MCP tools; the main session
  reads them back when it resumes.

**Critical composition gotcha.** Per the harness's
serialize-amendment-builds rule, two background-agent
*build* dispatches in the same git working tree race on
`index.lock`, `loam amend`, and tests. Builds serialize at
the working-tree level even when they target distinct
sealed components. Research and plan-author agents are
safe in parallel (read-only or doc-authoring); only build
agents need serialisation in a single tree.

## [user-intent phrasings]

- "research X in the background"
- "go figure out Y while I do Z"
- "kick off a long task"
- "do this in parallel"
- "fire-and-forget"
- "run this without blocking"
- "keep working on this while I switch contexts"
- "summarise this big doc, I'll be back"

## Source

```
source_url: https://code.claude.com/docs/en/sub-agents
source_fetch_ts: 2026-08-24T13:33:08Z
source_status: current
```
