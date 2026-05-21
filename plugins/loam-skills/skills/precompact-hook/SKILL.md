---
description: "When the persona needs to intervene BEFORE auto-compaction discards context — capture state to a durable surface, block compaction conditionally, or inject additional context into the compacted summary — author a PreCompact hook. PreCompact is the right primitive for cross-session memory protection: it fires before the compaction event and can block via exit-code-2, giving the persona a window to save load-bearing state to disk before tokens are reclaimed. Use when: load-bearing in-flight state must survive compaction, durable capture should fire automatically at compaction time, or compaction should be conditionally blocked when in-flight work makes it unsafe. Composes with the durable-capture memory rule and the structural-enforcement-on-recurrence memory rule (PreCompact is a structural enforcement of 'never lose load-bearing state to compaction')."
---

# precompact-hook

A hook that fires BEFORE auto-compaction discards conversation
state. Can capture, augment, or block.

## When to load me

- Persona has load-bearing in-flight state (pending decisions,
  open dispatches, mid-author artifacts) that would be lost on
  compaction.
- Persona has noticed repeated state-loss-on-compaction failures
  and structural enforcement is needed (memory rules alone have
  not held — see structural-enforcement-on-recurrence).
- Persona wants durable capture to fire automatically at compact
  time, not be remembered by the agent.
- Persona wants compaction conditionally blocked when in-flight
  work makes loss unsafe.

## What the primitive does

The PreCompact hook event fires immediately before Claude Code's
auto-compaction would otherwise reclaim conversation tokens. The
hook's behavior depends on its exit code:

- **Exit 0:** compaction proceeds normally; any output the hook
  printed is delivered alongside (use this to record state +
  let compaction continue).
- **Exit 2:** compaction is BLOCKED; the agent continues with
  full context. Use sparingly — blocking compaction risks
  running into hard limits.
- Other exit codes: standard hook failure handling.

The hook can also output `additionalContext` (per the universal
hook output fields) to inject load-bearing state directly into
the compacted summary the model sees post-compaction.

Loam currently uses `SessionStart`, `UserPromptSubmit`, `PreToolUse`,
`PostToolUse`, `Stop`. **PreCompact is not yet used** — it's the
recommended primitive for cross-session memory protection
identified in the claude-feature-awareness catalog.

## Composition

- **`feedback_durable_capture_for_planned_work.md`** (memory) —
  every TaskCreate for non-immediate work pairs with a durable-
  surface capture. PreCompact is the structural enforcement: at
  compact time, walk the task list + write pending items to
  durable surfaces automatically.
- **`feedback_structural_enforcement_on_recurrence.md`** (memory)
  — a behavioral rule violated more than once despite being in
  the corpus → the fix is a hook, not another memory rule.
  PreCompact is the right hook for "state lost on compaction"
  recurrence.
- **`feedback_compact_clear_decision_heuristic.md`** (memory) —
  token-cost-aware compact/clear rubric. PreCompact composes
  with that rubric: when compaction fires automatically, the
  hook captures load-bearing state regardless of which arm of
  the rubric triggered.
- **`session-handoff`** (sibling SKILL) — session-handoff
  captures pending items at session-close; PreCompact is the
  intra-session analog at compaction-time.
- **`claude-feature-awareness`** SKILL — the 29-event hook
  catalogue includes PreCompact; this SKILL operationalizes one
  specific event.

## Anti-patterns

- Blocking compaction (exit 2) reflexively — that just defers
  the problem until the hard context limit. Block only when the
  current turn is doing something genuinely uninterruptible.
- Authoring a PreCompact hook before the recurrence trigger
  fires — premature structural enforcement is over-tight
  scope. Memory rule first; PreCompact when the rule fails
  twice.
- Doing real work inside the hook — hooks should be fast (the
  default timeout is short). Capture state + exit; defer
  processing to a subsequent turn.
- Writing PreCompact hooks that depend on the model's reasoning
  — hooks are scripts, not LLM calls (except via the `prompt`
  or `agent` handler types, which are bounded but cost tokens).

## Example invocation

`.claude/settings.json` (or per-skill `hooks:` frontmatter):

```json
{
  "hooks": {
    "PreCompact": [
      {
        "type": "command",
        "args": [".claude/hooks/save_state_to_durable.py"],
        "async": false
      }
    ]
  }
}
```

The hook script (`save_state_to_durable.py`) walks the task list,
in-flight dispatch state, and any pending owner-decisions; writes
each to `<workspace>/.scratch/claude-output/precompact-state-<ts>.md`;
exits 0 (let compaction proceed).

For conditional blocking:

```python
# .claude/hooks/conditional_compact_block.py
import sys, json
state = read_in_flight_state()
if state.has_uninterruptible_dispatch():
    print("Compaction blocked — dispatch <id> mid-handshake")
    sys.exit(2)  # block
else:
    save_state_to_durable(state)
    sys.exit(0)  # let compact proceed
```
