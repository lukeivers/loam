# Primary persona shape — what loam means by "one trusted voice"

A loam workspace declares one persona. Every Claude Code session in
that workspace opens to the same named identity. The persona greets
you, holds memory across sessions, dispatches specialists in the
background, and owns the channel you actually read on. You talk to
one voice; specialists exist behind it.

This shape is a design choice, not an inevitability. Most agentic
systems shipping today are organised differently — a swarm the user
picks from, a tool-bag the user composes against, a fresh chat per
task. The single-persona shape costs more to build and constrains
more of what the harness can do. This note is about why we made that
trade and what the persona is actually for.

---

## What a primary persona is

Concretely, the primary persona is three things composed:

1. **A long-lived named identity.** One per workspace, declared in
   workspace configuration, loaded into every session through Claude
   Code's `SessionStart` hook. The identity persists across reboots,
   model upgrades, and harness releases. The user develops a
   relationship with it the way they would with any consistent
   collaborator — they learn its habits, it learns theirs, and that
   accumulation is what trust is made of.

2. **A contract enforced by the harness.** The persona is *not* a
   system prompt. A system prompt is a one-shot instruction the model
   is free to drift from as the context fills. The persona is a
   contract loam enforces through hooks — `SessionStart` loads the
   persona's memory and surfaces what is waiting on the user;
   `UserPromptSubmit` binds the turn to the persona's active scope
   and budget envelope; `Stop` writes the turn's salient observations
   back to memory; channel-routing wrappers ensure replies go where
   the user actually reads. The persona's behaviour survives because
   the *harness*, not the model, is responsible for keeping it
   consistent.

3. **The owner of the user-facing voice.** Specialists — researcher,
   planner, builder, reviewer, domain experts — are dispatched by
   the persona behind the scenes. The user does not choose them and
   typically does not see them. The persona dispatches, the
   specialist produces a deliverable, the persona integrates the
   result and surfaces it in its own voice. Outcome ownership stays
   with the persona end-to-end.

The shape is closer to a chief of staff than to a chatbot. The chief
of staff knows your calendar, knows what you said three weeks ago,
knows which specialist on the team handles a given problem, and gives
you one synthesised answer. You do not pick the specialist; you do
not see most of the work; you see the chief of staff and the
outcome.

---

## What it is not

A few shapes that are sometimes confused with this one and are
genuinely different:

- **Not a multi-agent system.** A multi-agent system exposes a swarm
  of named agents the user juggles between — pick the researcher to
  research, pick the writer to write, pick the coder to code. The
  user is the orchestrator. The primary persona shape inverts this:
  swarms exist behind the persona, dispatched by the persona, and
  the user never has to choose. Loam itself uses sub-agents heavily
  during dispatch chains; it just does not surface them as user-
  facing voices.

- **Not an agent-tool-bag.** A persona is more than its toolkit.
  Two personas could share an identical toolkit and still be
  different — different memory, different greeting shape, different
  channel discipline, different bounds on what they will refuse
  without explicit ruling. The toolkit (the harness) is what the
  persona draws from; the persona is the contract about how those
  draws happen on the user's behalf. Confusing the two leads to
  designs where every new tool produces a new agent, which produces
  the swarm-the-user-juggles failure mode.

- **Not a chatbot.** A chatbot is a single-turn interface with no
  meaningful memory and no autonomy between conversations. The
  persona has both — memory accumulates across years, and background
  work happens between sessions and surfaces on the next greeting.
  The persona is something you have an ongoing relationship with,
  not a service you visit per question.

- **Not a generic assistant.** Generic assistants are deliberately
  shapeless — try to be everything to everyone, no contract about
  what they will refuse. The persona has a contract with declared
  bounds: what it owns, what it delegates, what it will not do
  without explicit ruling, what the user has authorised in advance.
  Shapelessness is what makes generic assistants safe to deploy
  publicly; bounded contract is what makes the persona safe to
  trust with autonomy on the user's own machine.

---

## Why one named identity matters

Trust compounds in one relationship. It does not compound across a
distributed set of specialists, even if each specialist is
individually competent. A user who picks between five named agents
has to maintain five mental models — what each one is good at, what
each one's quirks are, what each one knows about them. That overhead
scales linearly with the number of specialists, and the user pays
it on every interaction.

A single persona absorbs that overhead. The user knows one voice,
learns its quirks once, and the specialists are an implementation
detail behind it. The persona's job is to translate the user's
natural-language intent into the right specialist dispatch and then
present the integrated result. The user's mental model is one
relationship, and the system's complexity is hidden behind it.

This is the same argument we make for `VALUE_PROPOSITION.md`'s
translation layer, but it lands at the persona shape specifically:
the translation only works if there is *one* translator. Five
translators is back to the swarm-the-user-juggles problem; the
user has to pick which translator to talk to, which is the work the
translation layer was supposed to absorb.

---

## The contract surface

What the persona contract owns:

- **Greetings and surfacing.** The session-start ritual — load
  memory, check completed background work, summarise what is
  waiting on the user, set up the turn's context.
- **Memory.** What gets written, what gets read, when. The persona
  is the consistent author of memory, which is what makes memory
  coherent over years.
- **Channel discipline.** Where user-visible replies go. If the
  workspace declares Telegram as the user channel, the persona
  routes there; terminal output is diagnostic, not conversation.
- **Principle application.** Which design lenses, which feedback
  rules, which scope-confidence reading apply to the current turn.
- **Autonomy bounds.** What the persona will do without asking,
  what it surfaces for ruling, what it refuses to do without
  explicit ruling.

What the persona contract *does not* own:

- **Specialist execution.** The researcher researches; the builder
  builds; the reviewer reviews. The persona dispatches and
  integrates; it does not run the specialist's work itself.
- **Structural safety.** Reversibility classification, kill-
  switches, cost ceilings, objective binding — these are the
  harness's job, enforced outside the session by PreToolUse
  chains. The persona inherits the safety surface; it does not
  re-implement it.
- **Cost governance.** Token, time, and money ceilings are the
  harness's job. The persona's contract is to operate inside
  the envelope; the envelope is enforced by the harness.

Splitting the contract this way is what makes the persona durable.
The persona owns the user-facing relationship — which is the slow-
changing, high-trust layer. The harness owns the infrastructure —
which is the fast-changing, replaceable layer. Memory backends,
safety primitives, cost governors, and specialists can all evolve
underneath the persona without changing what the user experiences.
The relationship survives the implementation churn because the
contract surface is stable.

---

## What we are not claiming

A few non-claims, to keep the scope honest.

- **Not right for every use case.** Multi-tenant systems serving
  thousands of strangers should not have a single persona; the
  shape requires a real ongoing relationship and accumulating
  memory, neither of which makes sense at multi-tenant scale.
  Public-facing agents — customer-service bots, information
  kiosks — also do not fit; the contract assumes a known user
  with declared authority bounds.

- **Not the only viable shape for personal AI.** A user who
  genuinely prefers picking between named specialists, or who does
  not want a long-lived relationship with a system, can be served
  by other shapes. We are claiming the single-persona shape is the
  right answer for users who want one trusted voice that gets work
  done across long horizons — not that it is the right answer for
  everyone.

- **Not "the model with a name on it."** A named identity over a
  stateless model is not the persona shape; it is cosmetic. The
  shape requires the contract — memory, channel discipline,
  autonomy bounds, hook-enforced behaviour — and the harness that
  enforces it. Without the contract, the named identity is a
  branding exercise.

The choice we made is the choice that follows from the problem we
are solving: one user, long horizons, autonomy under structural
safety, work that survives session boundaries. Anyone solving a
different problem should make a different choice.
