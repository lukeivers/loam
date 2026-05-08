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

Five principles must become part of the research of every future
feature — not one-time exercises, but always-on lenses. A feature
proposal that does not answer all five is incomplete.

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
> `docs/rebuild/VALUE_PROPOSITION.md`.

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

### Lens 6 — Principle-conflict resolution (multi-signal four-step process)

> **No principle in this corpus always beats another. When two
> principles conflict in a specific situation, apply the named
> four-step process: (1) name the conflict — both principles, the
> specific tension; (2) name the active signals — open list, at
> minimum scope-confidence (Lens 4), reversibility, blast radius,
> audience, time pressure, information asymmetry; (3) make the call
> given signal weights; (4) surface to user if non-obvious — when
> reasonable people would weigh signals differently, halt-and-surface.**

Silent resolution (apply one principle, ignore the other, never name
the conflict) propagates as silent precedent and is the failure mode
this rule prevents. Lens 4 is one signal feeding the process, never
the sole arbiter.

The companion derivation map at
`docs/design/principle-derivation-map.md` labels each principle in the
corpus compose-with-Lens-4 / independent / partial — that table is the
lookup used in step 2 to identify which principles share dominant
signals (compose-with) vs which weight different signals (independent).

**Procedural rule:** every new feedback memory or principle entry
carries a derivation/relationship line stating how it relates to the
existing corpus. The line is what makes the table maintainable.

The required research question: **"Are two principles giving opposite
advice in this specific situation? If so, have I named the conflict,
the signals, the call, and (if non-obvious) the surface?"**

Full text:
`~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_principle_conflict_resolution_multi_signal.md`.

### Lens 7 — Ruthless Feedback

> **Every quality gap, scope compromise, delivery risk, and design
> disagreement must be named the moment it is observed — regardless
> of who created it, who owns the affected work, or how far into the
> task the discovery occurs.** Silence about a problem is not
> neutrality; it is a compounding error.

**Three required elements of every disagreement:**

1. **Name the disagreement.** State clearly what the observed state
   is vs. what the correct state should be.
2. **Name the evidence.** Give the specific reason — a test failure,
   a violated AC, an architectural constraint, a scope gap, a logical
   inconsistency. "I think this is wrong" without evidence is noise.
3. **Name the alternative.** Bare disagreement without a proposed
   better path is a complaint, not feedback. State what the right
   move is, even if the alternative is "this needs owner ruling
   before proceeding."

This applies symmetrically — to work produced by agents, to plans
authored by dispatchers, and to framing supplied by the owner.
Ruthless Feedback does not have an authority exception.

**Distinguishing ruthless from contrarian:** the principle requires
evidence + alternative precisely to guard against degradation. An
agent that surfaces every problem it observes with named evidence and
a named alternative is applying Ruthless Feedback. An agent that
disagrees with everything, or objects without specifics, is being
contrarian. The distinction is observable: evidence and alternative
are either present or absent.

**T1 resolution — when the discovered problem is out-of-scope:**
scope-discipline and Ruthless Feedback create an apparent tension.
An agent mid-task discovers a defect or gap that is outside its
dispatch scope. Scope-discipline says don't sprawl; Ruthless Feedback
says name every problem. The resolution is **halt-and-surface, then
proceed with original scope unless the owner rules otherwise.** The
agent names the out-of-scope problem (with evidence + alternative
per the three elements), records it as a surface item, and resumes
the in-scope work. Scope-discipline constrains agent *action*;
Ruthless Feedback constrains agent *silence*. The two constraints
are orthogonal once you separate acting from surfacing.

The required research question: **"Have I named every quality gap,
scope compromise, or design tension I observed in this turn — with
evidence and an alternative — even if it falls outside the named
scope?"**

Lens 7 is **independent** of Lens 4: the obligation to surface
problems does not derive from scope-tightness. It composes with
Lens 4 only at the evidence-quality level (when confidence in a
gap is mixed, "name the evidence" acts as a calibration check on
the feedback itself).

Full text:
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
