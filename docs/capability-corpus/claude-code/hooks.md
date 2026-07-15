# Hook events — settings.json hooks/permissions/env

## Surface

Hooks are settings.json-registered handlers that fire on
named lifecycle events inside Claude Code. They are the
persona's primary structural-enforcement reach — a hook
can deterministically refuse, mutate, or augment behaviour
that would otherwise be advisory in a CLAUDE.md or memory
file.

The named hook events:

- **SessionStart** — fires when a new Claude Code session
  opens. Used for additionalContext composition (the
  persona's session-level corpus + tracker contributors
  fire here).
- **UserPromptSubmit** — fires before the model sees the
  user's prompt. Can augment, refuse, or annotate.
- **UserPromptExpansion** — fires during prompt expansion.
- **PreToolUse** — fires before a tool call. Can refuse a
  tool call that violates a structural guard (e.g. block
  Bash commands matching a deny-pattern).
- **PostToolUse** — fires after a tool call. Used for
  observability (log every tool call) or accrual (capture
  observed-effective patterns).
- **Notification** — surfaces an asynchronous event.
- **PreCompact** — fires before context compaction.
- **Stop** — fires when the session halts (the model
  finishes its turn). Used for memory-system episode
  writes, learning-extraction, and session-end housekeeping.
- **SubagentStop** — fires when a dispatched subagent
  halts. Symmetric to Stop but scoped to the subagent.
- **SessionEnd** — fires when the entire Claude Code
  session terminates.

## Inputs/outputs

**Registration.** Hooks register in `.claude/settings.json`
under `hooks.<event-name>`, each as a list of handler
specs. Pos-v2's `merge_session_start` / `merge_user_prompt_submit`
/ `merge_stop` / `merge_status_line` helpers compose
handlers from multiple sources without overwriting.

**Input envelope.** Each handler receives a JSON envelope on
stdin describing the event (session id, prompt content,
tool name, exit context, etc.). Schema varies per event.

**Output disposition.** Handler stdout is appended to the
context (additionalContext channel for SessionStart /
UserPromptSubmit; notification channel for Stop). Exit
codes can refuse the operation (non-zero exit on PreToolUse
blocks the tool call). Timeout is per-handler-configured;
default is short (sub-second to a few seconds).

## Composition notes

Hooks are the structural-enforcement-default reach: when
the persona accepts a critical guard, the first move is
"what hook would catch a violation?" — pre-commit hook
blocking secrets > CLAUDE.md rule; PreToolUse handler
blocking unsafe Bash > advisory feedback file.

Hooks compose with **MCP servers**: a hook can write
through an MCP tool call (memory episode, knowledge-server
mirror). Hooks compose with **scope-of-work**: Stop hooks
typically write learning-extracted episodes scoped to the
turn's active scope.

The persona uses the `update-config` skill for any change
to `.claude/settings.json` — direct edits to settings
files are gated through the skill so the merge logic stays
correct.

## [user-intent phrasings]

- "every time X happens, do Y"
- "from now on when..."
- "before/after X..."
- "automatically capture..."
- "block this kind of action"
- "always log every tool call"
- "make this a hard requirement"
- "structurally enforce..."

## Source

```
source_url: https://code.claude.com/docs/en/hooks
source_fetch_ts: 2026-07-15T13:00:06Z
source_status: current
```
