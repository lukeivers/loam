# Background agents by default

## Pattern

When work is multi-artefact authoring (multiple plan files,
multiple research docs, multiple corpus entries) or any
single long-generation artefact (~30 s+ of model
generation), the persona dispatches it to a background agent
rather than running it inline in the main session. The main
session stays interactive for owner conversation; the
background agent runs in parallel and reports back when
done.

## Conditions

This pattern applies when:

- The work product is multiple artefacts authored in
  parallel (e.g. several plan files for sibling amendments,
  several seed corpus docs).
- A single artefact requires sustained generation (~30 s+) —
  large research docs, multi-section plans, comprehensive
  reviews.
- The user is mid-conversation and reaching for new
  context — running the work inline would block the
  conversation thread.
- The work is not on a critical path that needs immediate
  feedback (no test-run-to-validate within the same turn).

This pattern does **not** apply when:

- The work is a single short artefact (one file, < 30 s
  generation).
- The work is a single-tool call (a single Read, a single
  Edit) — no agent dispatch needed.
- Owner needs to see incremental output during generation
  (sometimes inline streaming is the better shape).

## Failure modes

This pattern guards against:

- **Main-session blocking on long generation.** Without
  background dispatch, owner's turn waits for the model to
  finish; the conversation stalls.
- **Token-budget pressure on the main session.** Long
  inline generation eats the main session's context budget
  irreversibly. Background agents have their own context
  scope.
- **Loss of interactivity during research / authoring
  bursts.** When the persona is reaching for several
  sibling artefacts (e.g. a plan + research + manifest +
  builder-plan), inline serialisation makes the main
  session unresponsive for minutes.

## Cross-references

- [primitive: claude-code:background-agents]

## Trust marker

```
sources_count: 1
validation_count: 8
supersession_chain: ""
owner_acked: true
```

The owner directive is captured in
`~/.claude/projects/-Users-lukeivers-pos3/memory/MEMORY.md`
as `feedback_background_agents` and
`feedback_background_default_for_authoring`. Validation
count reflects multiple amendments in the four-amendment
program plus prior amendments dispatched following this
rule (#67, #66, #65, #50, etc.).
