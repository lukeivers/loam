# Verify the dispatch is the right action before sending it

## Pattern

Before sending a tighten / remove / rename / sealed-component
dispatch to a background agent, the dispatcher reads the
relevant code or surface in the main session and confirms
the dispatch is the right action. The main-session check
is the dispatcher-side mirror of the agent's halt-and-surface
discipline: if the dispatch is wrong, the agent can halt
with full context — but if the dispatcher is wrong, the
agent will faithfully execute the wrong thing.

This pattern applies most strongly to dispatches that
*remove* or *change* existing surface, less strongly to
purely additive dispatches. The asymmetry: a wrong additive
dispatch ships extra surface (recoverable); a wrong removal
dispatch ships missing surface (recoverable but with
narrative regret).

## Conditions

This pattern applies when:

- The dispatch will tighten an existing AC, remove an
  existing function, rename an existing surface, or modify
  a sealed component's source.
- The dispatcher can use grep + Read in the main session
  to check the on-disk reality before authoring the
  dispatch prompt.
- The dispatch carries an irreversibility implication
  (post-seal, the surface is locked; getting it wrong
  needs a follow-up amendment).

This pattern does **not** apply when:

- The dispatch is purely additive (new files, new
  components) — there's nothing to verify against.
- The dispatcher is the agent itself running a sub-task
  (recursive verification budget).

## Failure modes

This pattern guards against:

- **Faithful execution of wrong removal.** A dispatcher
  who hasn't checked the surface tells the agent to remove
  something that isn't there, or remove something
  load-bearing the dispatcher misremembers.
- **Rename targeting a stale name.** Renaming `foo_bar`
  to `foo_baz` when the surface was already renamed
  `foo_quux` in a prior amendment.
- **Sealed-component scope creep.** Believing a fence
  admits an edit that it doesn't, leading to a
  halt-and-surface from the agent that costs a round-trip
  and partially-built surface.

## Cross-references

- [primitive: claude-code:background-agents]
- [primitive: harness:scope-of-work]

## Trust marker

```
sources_count: 1
validation_count: 3
supersession_chain: ""
owner_acked: true
```

The owner directive is captured in
`~/.claude/projects/-Users-lukeivers-pos3/memory/MEMORY.md`
as `feedback_verify_dispatch_before_sending`. Validation
count reflects three amendments where the dispatcher's
pre-send check caught a surface-shape mistake before
dispatch.
