# Scope-only dispatch — agent prompts carry scope, not method

## Pattern

When the persona dispatches a background agent for a build
or authoring task, the dispatch prompt carries
*objective + scope + constraints + halt-conditions +
ODD-check directive only* — never the method. Naming
specific files, symbols, ACs, layouts, or commit-prose in
the dispatch reduces the agent's plan to paperwork.
Method-prescription in the prompt collapses the
plan-before-code CDC: the plan becomes a transcription of
the dispatch rather than the agent's own design work.

## Conditions

This pattern applies when:

- Dispatching any subagent / background-agent for work that
  has a plan-before-code CDC obligation.
- The work shape admits multiple valid methods (multiple
  file layouts, multiple test conventions, multiple
  authoring orders).
- The dispatcher has confidence the agent can read the
  plan + locked research + corpus and design the method
  itself.

This pattern does **not** apply when:

- The work is a tightly-bounded surgical fix where the
  *outcome* and the *method* are the same thing (e.g. "fix
  this typo in this exact line").
- The dispatcher has tightly-bounded knowledge the agent
  cannot reasonably re-derive (e.g. naming a specific
  amendment number that's already been assigned).

## Failure modes

This pattern guards against:

- **Plan-as-paperwork failure.** When the dispatch
  prescribes the method, the agent's plan ceremoniously
  restates what the dispatch said. The plan-before-code
  CDC is structurally bypassed.
- **Loss of agent's own design judgement.** Method
  prescription overrides the agent's local context, locked
  research, and own ODD self-check. Outcomes that
  prescribed-method dispatchers couldn't see (better
  layouts, better test shapes, better composition) get
  lost.
- **Brittleness to plan refinement.** When the plan
  evolves between dispatch and build, prescribed methods
  fight the refinement; scope-only dispatches absorb plan
  refinements naturally.

## Cross-references

- [primitive: claude-code:background-agents]

## Trust marker

```
sources_count: 1
validation_count: 5
supersession_chain: ""
owner_acked: true
```

The owner directive is captured in
`~/.claude/projects/-Users-lukeivers-pos3/memory/MEMORY.md`
as `feedback_agent_prompts_scope_only`. Validation count
reflects multiple amendments dispatched following this
rule across the four-amendment program.
