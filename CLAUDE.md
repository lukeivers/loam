# loam — CLAUDE.md

loam is a general-purpose harness for Claude-attached workflows. It
is explicitly *not* targeted at development as a primary use case —
dev-specific machinery (the methodology, conventions, and tooling that
govern how *we* build loam itself) lives behind a dev-mode auto-load
partition. DEV MODE workspaces additionally auto-load a dev-extension
fragment of these instructions; NORMAL USE workspaces never see it.

This file carries the always-on design lenses + output conventions
that shape every feature, proposal, and decision inside the loam
codebase.

---

## Design lenses for every feature

A prime lens (Lens 0) and seven supporting principles must become
part of the research of every future feature — not one-time exercises,
but always-on lenses. A feature proposal that does not answer all
eight is incomplete.

### Lens 0 — the prime lens: per-user-tuned translation

> **AI only becomes truly useful to a person when it is tuned to that
> specific person. loam's job is to continuously learn the specific
> user and translate what they want — customised to them — down into
> the underlying machinery (the frontier model, Claude Code, whatever
> sits beneath), so the user only ever has to know *what* they need,
> never *how.* The seven lenses below all serve this one.**

This is the lens the other seven serve. Where they shape *how* a
feature is researched and built, this one states *what* loam is for,
and every feature answers it first.

The translation must be **learned and customised per person,
continuously** — the same request does not translate the same way for
two people. loam runs this through a four-step loop, which is what it
adds on top of a raw model: (1) infer the action-oriented end-intent
behind the literal ask; (2) design a healthy way to enable it — should
it recur, need a framework, be deterministic?; (3) surface it back to
the user to verify; (4) learn from the answer, then repeat. The
inferred intent is always a hypothesis surfaced for checking, never an
assumption silently built on; verification both corrects the
hypothesis and teaches the per-user model. Guard the loop's own
failure mode: do not meet every "do this once" with "make it an
automated framework" — scale proposed structure to what this person
has shown they want.

Translation is only one side. The other is **protection**: what loam
delivers toward the user's intent must avoid the known ways AI betrays
its users by default (inventing things, missing context, breaking the
surrounding work or the original goal, having no real memory). A floor
of protection — the failures that betray *any* user — is always on for
everyone and not tunable; above the floor, rigor flexes with user and
stakes, and every guard is sized in proportion to the damage its
failure would do.

Two standing commitments fall out of this lens and bind every feature
and every reply:

- **Expose the substance; adapt only the vocabulary.** Always expose
  the actions, consequences, and decisions — what is actually
  happening — and never hide the substance. What adapts is the
  *words*: describe that substance in the vocabulary the user knows.
  loam's own coined terms count, even for a technical user; any
  coined or narrow term the user has not shown they know gets
  translated by default.
- **Follow the defined workflow; if you lose your place, pause.**
  Real multi-step processes are defined as structured flows that stay
  in context during the work. Follow the flow — and if you are unsure
  where in it you are, pause all other work until you re-establish
  your position, the way a pilot re-establishes location before
  touching anything.

The required research question: **"How does this serve learning the
user and translating for them specifically — and what known AI failure
mode does its delivery need guarding against?"**

Full statement of the doctrine this lens heads: `docs/design/loam-doctrine.md`.

### Lens 1 — Claude-leverage-first

> **loam is exclusively attached to Claude.** Every feature built
> on loam must actively consider what Claude Code / Claude SDK /
> Claude capabilities (slash commands, hook events, MCP, skills,
> plugins, background tasks, session primitives) can be leveraged to
> simplify, extend, or improve the feature — including capabilities
> the end user does not yet have configured but could adopt easily.
> If a Claude-native primitive already provides part of the feature,
> the design should compose on top of it rather than re-implement.

*Example:* Claude's skill ecosystem may already expose a legal-research
skill a user does not have enabled. A hypothetical legal plugin for
loam that composes with that skill is a different (and likely better)
shape than one that re-implements legal-research primitives inside the
plugin.

The required research question: **"What Claude capability does this
lean on or extend?"**

### Lens 2 — Harness + primary-persona value

> **The primary persona is a translation layer between the user's
> natural-language intent and AI-effective execution; the harness is
> the toolkit the primary persona draws from.** Every feature must
> reduce translation burden for the user and add to the toolkit the
> primary persona can invoke. Full detail in
> `docs/VALUE_PROPOSITION.md`.

The two required research questions:

- **Primary-persona test:** does this reduce the translation burden
  between the user's natural-language intent and AI-effective
  execution?
- **Harness test:** does this add to the toolkit the primary persona
  can draw from?

A feature that fails either test needs redesign. A feature that fails
the harness test is almost always wrong.

### Lens 3 — ODD authoring

> **Work in loam is defined by its observable outcome, not by a
> sequence of steps.** Objective + constraints + acceptance criteria;
> method is the builder's call. ODD applies after the Lens 1 and Lens
> 2 research questions have been answered; it shapes the mechanical
> form of the feature's authoring, not whether the feature should
> exist.

### Lens 4 — Prompt scope ↔ confidence

> **A prompt is a probability mass over agent trajectories; the
> tightness of the scope tracks the author's confidence that a
> single specific outcome is correct.** When confidence in the
> outcome shape is high, scope tightly — narrow objective, tight
> constraints, acceptance that pin the outcome (method stays the
> builder's call). When confidence drops, loosen scope so the agent
> can think broadly. The two failure modes are over-tight at low
> confidence (narrow scope blocks the actually-correct alternative)
> and over-loose at high confidence (broad scope burns tokens on
> options the author already knew were wrong).

This is the **most-broadly-applicable** shaping principle in loam,
but it is **NOT a first axiom** from which all others derive.
Several lenses and principles (Lens 2, ODD itself per Lens 3,
ruthless feedback) stand independent of scope-confidence and
compose with it rather than being derived from it. The
companion derivation map at `docs/design/principle-derivation-map.md`
labels each principle compose-with-F4 / independent / partial.

The required research question: **"What is my confidence that the
outcome shape I have in mind is the right one — and is the scope
I'm authoring tight enough or loose enough to match?"**

Tight-scope vs method-in-acceptance distinction (this is a common
trap): tight scope leaves method *inferable from the constraints*.
Method-in-acceptance states HOW inside the contract. The test —
can the acceptance criterion be satisfied by a method other than
the one you have in mind? If yes, scope is tight (good). If no,
you have stated method (bad — Lens 3 violation).

Conflicts with other lenses or principles are resolved by the
multi-signal conflict-resolution discipline (named four-step
process; see `~/.claude/CLAUDE.md` Universal principles).
Lens 4 is one signal feeding that process, never the sole arbiter.

### Lens 5 — Swarming (recursive task decomposition)

> **When any task can be partitioned into subtasks each with a
> measurably tighter acceptance criterion, decompose and execute in
> parallel or dependency order rather than sequentially in a single
> agent loop.** Apply recursively until further decomposition would
> add only coordination overhead — an aggregator step whose scope is
> no tighter than the parent's — or until the judge declares the
> cycle complete.

**The three reference patterns (from kyegomez/swarms, verified at
HEAD `e48100a`, 2026-05-02):**

1. **PlannerWorkerSwarm cycle.** Planner → typed task queue with
   dependency-aware claiming → judge produces `CycleVerdict`
   (`is_complete`, `gaps`, `needs_fresh_start`). The
   `needs_fresh_start` flag is the drift-detection escape hatch:
   discard all subtasks and re-run the planner with judge feedback.
   Do NOT continue a diverged subtask chain to completion.

2. **`ModelOutput.rationale` field.** Every model-selection decision
   records why in a dedicated field. In loam, this is a required
   `model-rationale: <model> — <reason>` line in every dispatch
   brief that selects a non-default model. Absence on an Opus
   dispatch is a violation.

3. **`EVAL_DIMENSIONS` named-axis judging.** Each AC or quality
   dimension is evaluated by a dedicated concurrent judge rather
   than collapsed into a single yes/no. Applicable to CDC/AC
   verification and LLM-as-judge probes for soft objectives.

**Stopping criterion:** decompose until each subtask's acceptance
criterion is strictly tighter than the parent's. Stop when the
proposed split introduces only coordination overhead. Restart
from scratch (with judge feedback) when drift is detected —
completing a diverged chain is never the correct response.

**`max_planner_depth` must be set explicitly.** Default is `1`
(no sub-planners). Deeper recursion requires an explicit opt-in
line in the dispatch brief.

The required research question: **"Can this task be partitioned
into subtasks each with a tighter acceptance criterion — and if
so, am I selecting the right model tier for each phase
(enumerate / execute / judge)?"**

Composes tightly with Lens 4: the stopping criterion uses
scope-confidence as its primary signal. Full text in
`~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_swarming_recursive_decomposition.md`.

### Lens 6 — Principle-conflict resolution (multi-signal, four-step)

> **No principle always beats another. When two principles conflict
> in a specific situation, run the named four-step process: (1) name
> the conflict — both principles, the specific tension; (2) name the
> active signals — open list, at minimum scope-confidence (Lens 4),
> reversibility, blast radius, audience, time pressure, information
> asymmetry; (3) make the call given signal weights; (4) surface to
> owner if non-obvious — when reasonable people would weigh signals
> differently, halt-and-surface.**

Silent resolution (apply one principle, ignore the other, never
name the conflict) is the failure mode this lens prevents. Silent
precedent compounds: an unmarked resolution becomes the next agent's
implicit rule, which becomes the agent-after-that's load-bearing
assumption, until the corpus has a rule no one ever wrote down.

The signal list is open. Lens 4 (scope ↔ confidence) is one signal,
not the master signal. Adding a new signal to the M5 process does
not require re-doing the principle-derivation map — that map only
covers F4 specifically. New signals enter the signal list as they
surface; the four-step process accommodates them without revision.

Procedural rule: every new feedback memory or principle added to
the corpus carries a derivation/relationship line saying how it
relates to existing principles (compose-with, independent, partial).
This is the M5 input the table at `docs/design/principle-derivation-map.md`
indexes. Without the derivation line, the principle is unindexable
and resolution against it falls back to first-principles each time.

The required research question: **"If this lens conflicts with
another lens or a feedback memory in this specific situation,
what signals weigh which way — and is the resolution obvious enough
that I can rule autonomously, or do I need to halt and surface?"**

Composes-with: every other lens (M5 IS the resolution mechanism for
their conflicts). Independent of: nothing — M5 sits above all other
principles as the meta-process. Full text in
`~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_principle_conflict_resolution_multi_signal.md`.

### Lens 7 — Ruthless Feedback

> **Name the disagreement, name the evidence, name the alternative.
> Surface every quality gap, scope compromise, design disagreement
> immediately — including disagreements with the owner's framing.
> Silent acceptance of a known problem is the failure mode this
> lens prevents.**

Three required elements every time the lens fires:

1. **Name the disagreement.** State the specific claim or framing
   that is wrong, in one sentence. "The plan says X; X is wrong
   because Y."
2. **Name the evidence.** Cite the source — a file path, a
   commit SHA, a test result, an observed runtime behaviour. Bare
   assertion is not evidence; it is restatement.
3. **Name the alternative.** State what should happen instead. A
   feedback note that surfaces a problem without proposing a path
   forward leaves the receiver with a worse decision context than
   silent acceptance would have.

T1 resolution (the scope-discipline / Ruthless-Feedback tension):
scope-discipline constrains *action* — agents do not silently
extend their scope to fix problems they discover outside it.
Ruthless Feedback constrains *silence* — agents halt-and-surface
the out-of-scope discovery, then proceed inside scope unless owner
rules otherwise. The two compose: the surface is mandatory; the
extension is owner-gated.

Independent of Lens 4. Composes with Lens 6 (Ruthless Feedback IS
the surfacing step in M5's four-step process). The required
research question: **"What disagreement, gap, or compromise have
I noticed but not yet named — and what would the receiver of my
output need to know to make a better decision?"**

Full text in
`~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_ruthless_feedback.md`.

---

## Output conventions

> *When any response produced by the primary persona or a dispatched
> agent would exceed roughly 40 lines or 400 words, the content is
> written to a predictable disk path and the path is referenced inline
> instead of inlining the content itself. The user opens the file with
> whatever tool fits the current interface — `open`, `less`, or `bat`
> from a terminal; an attachment through Telegram; the inline viewer
> or `open` from the Claude app.*

Context tokens are finite, expensive, and lost to compaction. Inlining
reports, plans, long analyses, and multi-section syntheses burns
context that could otherwise carry forward useful state, and
compaction discards the content regardless. Writing substantial output
to disk persists the artefact at a stable path and makes it
retrievable on demand without re-transmission. Short replies, direct
answers, status updates, and brief summaries stay inline; the rule
engages only when the content is large enough that a reader would
naturally prefer a dedicated viewer over scrolling chat.

In practice: when an output crosses the ~40-line / ~400-word
threshold, choose a sensible path for the artefact —
`<workspace>/.scratch/claude-output/<subject>.md` for ephemeral
material, a workspace-appropriate canonical path for plans / specs,
or a component-specific path for component-scoped artefacts — write
the file, then inline a brief description plus the path. Format
follows the content (markdown for prose and structure, plain text
for logs). Opening the file is the user's call. Ephemeral files
belong in the workspace's `.scratch/` (gitignored via
`.scratch/.gitignore`, already in place) so they're (a) visible to
the human operator while browsing the repo, (b) survive session
boundaries on disk, and (c) don't disappear on system reboot.

---

## Operating discipline (always-on)

These rules govern how the **primary (interactive) session** spends
its turns. They are durable doctrine; a workspace that has already
seen one of them fail to hold on discipline alone should back it with
structural enforcement (a Claude Code hook on the relevant event)
rather than a second behavioural promise. The doctrine below is
enforcement-agnostic — each workspace wires whatever mechanism its
platform offers; the rule is the same regardless of how it is enforced.

### Heavy generative/mutating work is dispatched

> **The primary session does NOT grind heavy generative or mutating
> work in-thread. Authoring files, multi-step builds, and
> multi-artefact generation are DISPATCHED to a background agent.**
> Read-only investigation, diagnosis, and conversation (reading
> files, searching, running diagnostics, answering questions) are
> EXEMPT and may use many in-thread tool calls — the dividing line is
> work-TYPE (generative/mutating vs read-only/diagnostic), not raw
> tool-call count.

The persona's own legitimate bookkeeping is exempt: scratch space,
memory files, plan-docs, the workspace's own instruction and settings
files, and harness-infrastructure config. Small surgical edits are
always frictionless. A workspace that enforces this structurally
should warn on the first heavy deliverable write to a non-exempt path
and block the runaway pattern, with an explicit escape hatch for the
cases where heavy in-thread authoring genuinely is correct.

### A failed agent is fixed at the agent path, never absorbed in-thread

> **When a background agent FAILS (content-filter block, crash,
> timeout), the correct response is to diagnose-and-fix the agent
> path — re-dispatch with a workaround, split the work, adjust the
> brief — NEVER to fall back to grinding the work out in-thread.**

A failed dispatch is a signal to fix the dispatch, not a license to
absorb the work into the primary session.

### Compaction is a hardened risk point

> **Context compaction can silently thin load-bearing discipline.
> Immediately after any compaction, the core operating discipline and
> the current active-work state are re-injected so the compaction
> cannot quietly drop them.**

Discipline that matters across a compaction lives in enforcement that
survives the compaction event, not only in fragile in-context memory.
A workspace that enforces this structurally should front-load a
preservation block before the summarizer runs and re-inject the full
discipline when a session resumes from a compaction.
