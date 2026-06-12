---
description: "When the persona is about to dispatch work — a Task tool call, a hook addition, a SKILL authoring, a Bash script, an MCP server call, a scheduled job, a slash command — and more than one Claude / Claude Code primitive could deliver it, apply this rubric to pick the right primitive. Catches mismatches like 'wrote a one-shot prompt when the work needs a recurring SKILL', 'spawned a Task agent for in-session work the persona could handle directly', 'authored a memory rule when the failure mode needs structural enforcement via a hook', or 'wrote a 50-line documented rule when a SKILL bundle would propagate the same content auto-discoverably'. Use whenever the dispatch decision has more than one defensible primitive choice."
---

# tool-selection-rubric

When the persona has work to do and several primitives could deliver
it, walk this seven-decision framework. Each decision has criteria and
a landing primitive. The framework is meant to run **fast** — at the
moment of dispatch, not as a separate planning step.

Capability facts about each primitive (what a hook event does, how the
schedulers compare, what `run_in_background` returns) are NOT restated
here — they live in the capability corpus and the `claude-feature-
awareness` SKILL routes to them. This rubric decides; awareness
indexes. Keeping the facts in one maintained place (the corpus) means
the rubric never goes stale against an upstream release.

## Why this exists

The dispatch decision is otherwise ad-hoc: "I'll just spawn an Agent"
or "I'll add a hook" without weighing alternatives. Three costs of
ad-hoc dispatch:

1. **Under-utilization** — a primitive exists but goes unused because
   nobody checked the corpus.
2. **Over-use** — a heavy primitive gets used when a lighter one fits
   (a background Agent when an inline tool call would do; a hook when a
   documented rule would do).
3. **Sub-agent context-gap** — a sub-agent inherits the dispatcher's
   wrong-primitive choice when the brief is authored from a wrong
   mental model.

The rubric is the explicit alternative-weighing the ad-hoc decision
skips. It is the loam Lens-1 ("Claude-leverage-first") discipline made
into a checklist.

## The seven decision points

### A. Inline vs background

- Work fits the current turn's budget and finishes fast → **inline**
  (direct tool calls).
- Work needs minutes of wall-clock, a long-running tool call, or
  independent context to avoid main-session pollution → **background
  Agent** (`Task` with `run_in_background`). See
  `docs/capability-corpus/claude-code/background-agents.md` for the
  mechanism contract.
- Multi-step but each step short and interactive → **inline with
  task-tracked progress**.

**Anti-pattern:** spawning a background Agent for a two-tool-call
investigation — the setup costs more than the work.

### B. Hook vs documented rule

- The rule is structural (catchable by regex / state-check /
  file-presence) AND a prior memory-rule attempt has failed in
  practice → **hook**.
- The rule needs judgment / context-awareness and fits the
  conversational shape → **documented memory rule**.
- The rule is a HARD invariant that must never be violated → **both**:
  hook as structural enforcement, memory rule as the documentation of
  why.

The hook-event catalogue (which event fires when, what envelope, what
output disposition) is in `docs/capability-corpus/claude-code/hooks.md`
— read it before picking the event.

**Anti-pattern:** authoring a memory rule when the failure mode is
structurally regex-detectable and a memory rule has already failed
once (loam's structural-enforcement-on-recurrence rule: a rule
violated more than once despite being in the corpus wants a hook, not
another memory note).

### C. Which hook event

Pick the event from the corpus catalogue
(`docs/capability-corpus/claude-code/hooks.md`) — it names each event
and its fire moment. Match the fire-moment to the work: before-the-tool
gating, after-the-tool capture, turn-boundary audit, session-start
hydration, pre-compaction checkpoint.

**Anti-pattern:** using a turn-boundary event for what should be a
per-tool event (fires on every turn instead of only when the relevant
tool fired).

### D. Skill vs slash-command vs one-shot prompt

- Recurring + benefits from being invocable by name + the **persona**
  is the consumer → **SKILL**.
- Recurring + invocable by name + the **user** is the consumer →
  **slash-command** (a SKILL with user-facing invocation).
- One-time → **one-shot prompt** inline.

**Anti-pattern:** authoring a slash-command for a one-time
investigation — the discovery surface costs more than the work saved.

### E. Recurring-execution primitives (schedule vs loop vs durable)

- Cross-session, cron-shaped, runs while the machine is off →
  `/schedule` (see `docs/capability-corpus/claude-code/schedule.md`).
- In-session, self-paced or fixed-cadence iteration with a stop
  condition → `/loop` (see
  `docs/capability-corpus/claude-code/loop.md`).
- Watching a long-running local process for completion or an event
  stream → the Monitor mechanism (covered in
  `docs/capability-corpus/claude-code/background-agents.md`).
- Durable cross-session scheduling on the local machine → a launchd
  plist (named in the scheduling comparison; the corpus
  `schedule.md` / `loop.md` entries draw the session-bound vs
  cross-session line).

**Anti-pattern:** using a session-bound primitive for work that must
survive session boundaries. Read the corpus entry's session-lifetime
note before choosing.

Where loam already ships a bespoke mechanism that overlaps a native
primitive (for example an in-session keep-going mechanism vs the
native `/goal`), this rubric names BOTH as candidates and leaves the
bespoke-vs-native ruling to its own decision cycle — the rubric
surfaces the choice; it does not pre-rule it.

### F. MCP vs Bash vs HTTP-hook

- Calling an authenticated third-party service that has an MCP →
  **MCP**; otherwise Bash + token.
- Local file / git / system operation → **Bash**.
- Webhook out to an external service → **HTTP via curl in Bash**.

**Anti-pattern:** writing custom Bash + token handling when an MCP
server already provides the auth.

### G. Plugin vs in-repo SKILL

- Capability should ship to users of loam → **plugin** (under
  `plugins/<name>/`).
- Capability is workspace-specific or not yet validated → **in-repo
  SKILL** at the workspace skills dir.
- In development, graduate-when-ready → start in-repo, promote after
  dogfood validates.

**Anti-pattern:** promoting a SKILL to a canonical loam plugin before
dogfood validates it at the workspace layer — the plugin surface is
harder to revert.

## How to apply at dispatch time

1. **Name the work in one sentence.**
2. **Walk the seven decisions in order**, picking a primitive at each
   (most are obvious; surface the ones that aren't).
3. **If the chosen primitive is non-default**, add a
   `primitive-rationale: <primitive> — <one-sentence reason>` line to
   the dispatch reasoning (the `primitive-rationale-check` SKILL owns
   this discipline; it mirrors the `model-rationale:` line for
   non-Sonnet model selection).
4. **Proceed with the chosen primitive.**

## Composition

- **`claude-feature-awareness`** — the catalogue this rubric reads
  from. Awareness indexes the corpus; the rubric decides.
- **`primitive-rationale-check`** — records the choice after the rubric
  makes it.
- **`scope-decompose`** — when decision A surfaces a task big enough to
  partition, the decomposition discipline takes over (loam's F3
  swarming).

## Graceful degradation

Without loam installed — a stranger running raw Claude Code who enables
this plugin alone — the seven decisions still apply; only the corpus
pointers degrade. Where a decision references a
`docs/capability-corpus/claude-code/<entry>.md` path, the raw-Claude-Code
fallback is the upstream documentation the corpus projects from:
Claude Code's own hooks reference for decision C, its commands /
routines reference for decision E, its sub-agents reference for
decisions A and E. The decision criteria themselves carry no loam
dependency — they are primitive-selection judgment that holds for any
Claude Code user. The corpus simply makes the facts local and
refresh-kept; absent it, read the upstream docs the entries cite in
their `Source` blocks.

## Out of scope

- Restating capability facts — those stay in the corpus.
- Ruling on any specific bespoke-vs-native overlap — the rubric names
  both candidates; the ruling is its own decision.
