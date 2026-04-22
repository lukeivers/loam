# pOS v2 — Future Ideas

Captured 2026-04-21. Ideas recorded for future work — not scoped, not committed to a timeline, not attached to a component. Each lives here until it either becomes a concrete component cycle or is explicitly retired. These are broader strategic directions than the operational items in `BACKLOG.md`.

---

## Core Development Principles — three research lenses

Three principles must become part of the research of every future feature — not one-time exercises, but always-on lenses. A feature proposal that does not answer all three is incomplete.

### Lens 1 — Claude-leverage-first

> **pOS v2 is exclusively attached to Claude.** Every feature built on pOS v2 must actively consider what Claude Code / Claude SDK / Claude capabilities (slash commands, hook events, MCP, skills, plugins, background tasks, session primitives) can be leveraged to simplify, extend, or improve the feature — including capabilities the end user does not yet have configured but could adopt easily. If a Claude-native primitive already provides part of the feature, the design should compose on top of it rather than re-implement.

*Example:* Claude's skill ecosystem may already expose a legal-research skill a user does not have enabled. A hypothetical legal plugin for pOS v2 that composes with that skill is a different (and likely better) shape than one that re-implements legal-research primitives inside the plugin.

The required research question: **"What Claude capability does this lean on or extend?"**

### Lens 2 — Harness + primary-persona value

> **The primary persona is a translation layer between the user's natural-language intent and AI-effective execution; the harness is the toolkit the primary persona draws from.** Every feature must reduce translation burden for the user and add to the toolkit the primary persona can invoke. Full detail in `VALUE_PROPOSITION.md`.

The two required research questions:

- **Primary-persona test:** does this reduce the translation burden between the user's natural-language intent and AI-effective execution?
- **Harness test:** does this add to the toolkit the primary persona can draw from?

A feature that fails either test needs redesign. A feature that fails the harness test is almost always wrong.

### Lens 3 — ODD authoring

> **Work in pOS v2 is defined by its observable outcome, not by a sequence of steps.** ODD methodology governs how features are authored once research concludes they should exist — objectives + constraints + acceptance criteria; method is the builder's call. Full detail in `odd-methodology.md` and `odd-in-pos.md`.

ODD applies after the Lens 1 and Lens 2 research questions have been answered; it shapes the mechanical form of the feature's authoring, not whether the feature should exist.

### Timing note on enforcement

These three lenses are captured as design principles now; the execution programme to *mechanically enforce* them in future research plans (see Idea 1 below) does not start until the new pOS v2 copy is being tested in a live evaluation workspace. Until enforcement lands, feature authors apply the lenses by discipline; once enforcement lands, a research plan missing an answer to any lens fails its gate.

---

## Core Development Convention — step-by-step when the system cannot act

> **When the system cannot do a step on the user's behalf, it produces exact step-by-step instructions for that step — not advice, not encouragement to figure it out, not a link to documentation.**

Rationale. The fourth lens's aspiration is zero manual steps. Physical reality sometimes prevents it — a third-party service whose API key belongs to the user is literally impossible for the system to obtain for them. The pragmatic rule is a three-tier gradient, not a binary:

1. **Silent** when possible. The system does it.
2. **Step-by-step instructions** when impossible. Numbered, unambiguous, with expected time ("this takes about two minutes"). No narrative, no "and then you'll want to...," no implicit steps that presume the user understands the system's architecture. The instructions are a concrete, testable product — if a reader follows them verbatim, the step gets done.
3. **Loud failure** when even instructions aren't enough. Named diagnostic, contact surface.

Step-by-step instructions carry the same discipline as code: they are authored with specific target users in mind, they are tested (can a non-technical reader follow them without asking for clarification?), and they are updated when their environment changes. "See the documentation" is not instructions; it is a non-answer.

Applied to every future feature that interacts with user-owned external surfaces (Telegram bot tokens, OAuth flows, API keys for paid services, service-account creation on cloud providers, etc.).

---

## Core Development Convention — plan before code, always

> **Every build — every scope of work, every amendment, every fix —
> requires a written build plan on disk BEFORE code writing begins. On
> completion, verify the plan exists and the outcome matches it. ODD
> compliance check runs against every completed scope before moving on.**

Rationale. The 2026-04-22 audit surfaced three RED components
(workspace-bootstrap, hands-off-lifecycle, session-resilient-orchestrator)
with ODD violations that traced back to work proceeding without a
scoped plan against the acceptance criteria. Amendments extended
pre-existing violations (non-objective Linux code, method-in-acceptance)
because the extending author did not pause to verify the existing
surface was itself AC-backed before adding to it. A written plan closes
that gap: it forces the author to name which ACs the work satisfies,
what files are touched, and what validation proves the plan's outcome
before any code is produced.

Mechanics:

- Plans live at `docs/rebuild/plans/<work-item-name>.md`.
- Plan structure: objective, ACs-satisfied (cite by ID), files changed,
  validation strategy, halt triggers. Mirrors the proposal format at a
  smaller scale for work that doesn't warrant a full five-gate cycle.
- Plan writes-to-disk happen before any source edit.
- Plan commits with (or just before) the code it describes.
- Completion check: verify plan file exists AND the outcome matches
  what the plan declared.

Subagent flow:

- Every subagent dispatched for build work is instructed to write the
  plan file first, then execute against it.
- The agent's final report cites the plan path.
- The main session verifies at return.

ODD compliance check on every completed scope:

- Acceptance criteria are outcome-shaped, deterministic, one-test-per-criterion.
- No method-in-acceptance.
- No silent exception branches for cases no AC names.
- No code supporting cases the objectives do not declare (§2.5).
- Tests assert outcome, not method.

Violations surface immediately, not in a future audit.

Question-asking discipline (companion rule):

- Before asking the owner any question, evaluate it against the
  design corpus: objectives spec v1.0+v1.1+v1.2, odd-methodology.md,
  odd-in-pos.md, VALUE_PROPOSITION.md, STATE.md, FUTURE_IDEAS.md.
- Only surface questions that are NOT answered by those sources.
- Do not present "options to rule on" when the methodology already
  rules — method-level choices are the builder's call per ODD.

Applied immediately to all work from 2026-04-22 forward.

## Core Development Convention — setup scripts self-retire on success

> **Work that happens once should leave no code behind that runs every session.** First-run setup completes its job, verifies the outcome, then removes itself — from the filesystem where the script lives, and from the hook registration that invoked it. Subsequent sessions never run first-run code because first-run code is not present to run. Future update-triggered setup ships its own self-removing script; setup logic is not reused session-after-session as check-and-skip scaffolding.

Rationale. Check-and-skip surfaces are an anti-pattern: they accumulate over time (each new setup concern adds another conditional), they add ongoing session-start cost for zero payoff once the one-time job is done, and they turn "is setup complete?" into a live-at-every-session state-machine query that the fourth lens was explicitly trying to retire. Self-retiring setup makes "setup is done" structural — the absence of the script is the proof, not a state flag the script consults.

Applied immediately to true-first-run (Phase 5 second component): the first-run shell script's last act before exit is to (a) write `.claude/settings.json` with the SessionStart hook pointing at the sealed supervisor path, (b) delete itself from the filesystem. Subsequent SessionStart fires invoke the supervisor directly; no first-run surface remains.

Design principle for future components: any setup code should answer the question *"how do I remove myself on success?"* as part of its scope, not as a maintenance afterthought.

---

## Idea 1 — Three-lens enforcement programme

The concrete plan for operationalising the three Core Development Principles above. Four sequential steps; the review (Step 2) and enforcement (Step 3) steps are multi-lens rather than Claude-only, because enforcing a subset of the lenses does not yield a well-designed feature.

### Step 1 — Research what Claude offers and document it

Produce a durable map of the Claude capability surface for pOS v2's consumption: slash commands, hook event types, settings schema, SDK methods and primitives, MCP tool patterns, the plugin system, skills available on marketplace, session mechanics, the agent tool, background-task primitives, subagent patterns.

For each capability: what does it do, how does it compose with pOS v2's foundational layer, what are the known pitfalls, what are practitioners doing with it effectively, how does configuration work for end users.

Deliverable: a `CLAUDE_CAPABILITIES.md` (or similar) document inside pOS v2 docs — the reference an AI agent consults during feature research to know what exists.

**Early observations worth recording** (the capabilities that feel obviously relevant on first glance):

- `/loop` and self-pacing primitives — compose with scope-of-work activation cycles.
- Background tasks + Monitor — compose with the background-work-awareness principle already baked into the primary-persona layer.
- Hook events — the deterministic-enforcement layer complements the structural-refusal patterns ODD prescribes.
- Skills — natural home for workspace-specific canned flows; skill-marketplace skills may replace whole would-be plugins.
- MCP — the external-integration surface most plugins will lean on.
- Subagents — the Agent tool's dispatch pattern is the delegation primitive pOS v2 already leans on heavily during the rebuild.

### Step 2 — Comprehensive multi-lens review of existing pOS v2

Once Step 1 lands, review every existing pOS v2 component and feature against **all three lenses**:

- **Claude-leverage lens** — against the capability map from Step 1. Could this be simplified by leaning on a Claude primitive? Could it be extended or improved by composing with one?
- **Value-proposition lens** — against VALUE_PROPOSITION.md. Does this reduce translation burden for the user? Does this add to the toolkit the primary persona can draw from? Features that force the user to do translation work are suspect.
- **ODD lens** — against odd-methodology.md. Are acceptance criteria well-formed (one per declared behaviour, deterministic, outcome-shaped)? Is structural enforcement preferred over advisory? Are negative cases re-extended as positive objectives rather than buried as exception branches?

Outcome: a disposition pass analogous to the foundation-audit — GREEN (satisfies all three lenses), YELLOW (partial satisfaction on one or more lenses with manageable cost), RED (fails a lens in a way that suggests redesign). YELLOWs and REDs get dispositioned as fix-small / fix-large / defer-with-trigger / accept-with-rationale. The review is a single unified pass rather than three separate ones, since a feature's shape across all three lenses is usually entangled.

### Step 3 — Build the enforcement mechanism

Every feature research plan authored after this lands must include explicit sections answering the required research questions for each lens:

- **Claude-leverage:** what existing Claude capabilities does this feature lean on, extend, or replace?
- **Primary-persona:** does this reduce the translation burden between the user's natural-language intent and AI-effective execution?
- **Harness:** does this add to the toolkit the primary persona can draw from?
- **ODD:** does the proposal state objectives + constraints + acceptance without prescribing method?

The research-plan template / convention is updated to require all four questions. Research plans that do not address any one are incomplete; the gate refuses to advance until they are.

This is structural enforcement of the three Core Principles — not advisory prose in a sidebar, but required artifacts in every research cycle. Matches the ODD preference for structural refusal over runtime nag: the research-plan validator refuses to mark a plan reviewable until each required section is present and non-empty.

### Step 4 — Build the Claude-capability refresh mechanism

Claude ships multiple significant features per week. The `CLAUDE_CAPABILITIES.md` from Step 1 goes stale fast. A scheduled job runs (default: once per day, subject to token-budget guardrails from cost-governance — if an overage is imminent, the refresh waits) and updates the map with newly-announced features, deprecations, and practitioner pattern shifts.

Output: a durable capability map that stays current. Practitioners of pOS v2 (including the primary persona during feature research) always operate against the latest Claude surface, not a stale snapshot.

**Interaction with cost-governance:** the refresh scheduler respects cost ceilings. If refreshing would push a rolling-window spend past its cap, the refresh defers rather than forcing the ceiling up. This is structural composition — the refresh primitive consumes the cost-governance gate like any other scope.

Note: this refresh mechanism is Claude-specific. The value-proposition and ODD principles are stable enough that their principle docs do not need an analogous refresh — they are authored once and iterated only when the principles themselves evolve.

### Sequencing and timing

The four steps are sequential: Step 1's output feeds Step 2's multi-lens review, which feeds Step 3's enforcement mechanism, which (for Claude only) feeds Step 4's refresh automation. Nothing starts until the new pOS v2 copy is being tested in an evaluation workspace — that use is what will surface which lenses pay their keep in practice and where the enforcement mechanism needs to live.

---

## Idea 2 — Non-tech user enablement through light-touch education

One of the primary differences between pOS v1 and pOS v2 is the focus on enablement for non-tech users. Part of that enablement is helping them understand the best way to carry out what they want done — without turning every request into a technical-decision-tree they have to navigate.

A non-tech user will not know when to build a local HTML UI versus use scheduled tasks versus set up a session-resilient orchestration. They will not know when to ask for a new persona or even care that personas exist. They should not have to.

**What the system should do:**

- Carry out what is asked without demanding technical literacy as a precondition.
- Educate the user *very, very lightly* as it goes — expose the choice the system made and the reasoning in a sentence, not a tutorial.
- Over time, the user grows expertise by seeing how the system handles the various shapes of their requests: "I made this a scheduled task because X happens every Tuesday" — next time they understand what scheduled tasks are for.
- Never overwhelm. The education has to be ambient, not interruptive.

**The hard part** is calibrating "light." Too little and the user never grows; too much and every interaction turns into a lesson. The right feeling is closer to a thoughtful assistant narrating a decision than to a tutor.

This is a cross-cutting concern that touches primary-persona layer, scope-of-work, and probably a new "expertise-growth tracker" component that shapes how much meta-explanation the persona surfaces over time.

---

## Idea 3 — Initial plugin suite

The extension protocol proven by workspace-bootstrap is the mechanism. The plugins are the content.

**Must-have at launch:**

- **Dev/SDLC plugin** — replaces the SDLC stuff from pos v1 (the seven-stage pipeline, workflow state-machine, spec/plan/build/review/verify artifacts, contradiction detection, etc.). This is the first and most-needed plugin because building pOS itself uses it. Review pos v1's full SDLC module set for what translates: the workflow engine, artifact registry, stage gates, product lifecycle, roadmap tooling, task orchestration, and related plumbing.
  - **ODD is the default for new projects authored inside pOS v2.** When the user starts a new project using pOS v2, the SDLC plugin defaults its research/spec/plan/build/review/verify stages to ODD's objective-centric shape unless the user explicitly opts out. The default matters because most users will not know to ask for ODD, but the pOS-v2 value proposition is weakened if work inside pOS-v2 fails to leverage the methodology pOS-v2 practices natively.
  - **Opt-out and imported projects keep an internal ODD representation.** For projects where the user chooses a different discipline (continuing TDD, BDD, or ad-hoc conventions), and for existing projects brought into pOS-v2 for review / updates / ongoing maintenance, the SDLC plugin still maintains an internal ODD configuration for that project — abstracted from the combination of the existing tests and the code. This internal representation keeps the system aligned to ODD semantics even when the user's surface representation is not ODD-shaped. The abstracted view informs the primary persona's review and proposal authoring; the user's chosen representation remains untouched in the codebase.

**Review scope from pos v1** — enumerate every module/plugin/configuration-set in current pOS, classify each as (a) translates directly to a pos-v2 plugin, (b) translates with redesign, (c) obsolete under pos-v2's foundational layer (e.g. anything the safety / reversibility / cost / self-correction / bootstrap layers now handle natively), (d) irrelevant.

**Additional plugin candidates the planner names for consideration:**

- **Project/task management overlay** — the owner's named example. Customisable view that pulls from corporate sources (Slack, Asana, Jira, Linear, GitHub Projects, etc.) via MCP. One unified pane for "what needs my attention across every tool I'm in."
- **Communications plugin** — email triage + drafting, calendar scheduling, follow-up tracking, light-touch CRM. Gmail + Google Calendar MCPs already exist; this plugin is the workflow layer over them.
- **Knowledge management plugin** — notes + PKM + research synthesis. Obsidian / Logseq / Notion as backends via MCP; the plugin adds scope-of-work-shaped authoring flows (chapter briefs, memo drafts, research lit reviews).
- **Finance / household-ops plugin** — personal finance categorisation, budget tracking, household logistics (bills, subscriptions, recurring decisions). Quicken / YNAB as optional backends; standalone workspace-local store as default.
- **Creative/long-form plugin** — fiction-writing workflows (like pos v1's litrpg-writer expanded into a reusable plugin), editorial pipelines, publication tracking (KDP / Royal Road / Substack).
- **Health/habit tracking** — Apple Health / Oura / similar integrations; habit-formation workflows; medication and appointment tracking.
- **Trading / quant research** — backtesting orchestration, strategy lifecycle, position tracking (like pos v1's betting-engine cluster turned into a generalised plugin).
- **Legal/compliance** — contract review, employment-law workflows, compliance checklists (like pos v1's Jude domain generalised).

For each candidate, the question at planning time is: "does this naturally compose with the foundational layer, does it justify its plugin status over a workspace-local adapter, and what's the delivery shape of its first useful version?"

**Plugin selection discipline:** do not ship all eight. Pick the two or three that maximise early pOS-v2 value and prove the plugin ecosystem; let the community (or later phases) build the rest. The dev/SDLC plugin is the one that is definitely in because pOS itself needs it.

---

## Idea 4 — Deep personalisation through interaction capture

pOS should learn more about the user over time — storing nearly every interaction, perhaps every single interaction — and processing that accumulated record into a durable user profile that makes the system feel increasingly aligned with how the user works, what they care about, and how they prefer to be engaged.

**What "nearly every interaction" means:**

- Session transcripts, or the decision-relevant subset of them.
- Preferences expressed (stated or inferred).
- Patterns observed (time of day / day of week engagement shapes; tool preferences; working styles; task-type affinity).
- Reactions to system outputs — when the user accepted, edited, rejected, or asked for a rework.

**What "processing" means:**

- Not raw-log retrieval; that's memory-system's job.
- A dedicated synthesis layer that periodically (or continuously) updates a structured user-profile artifact.
- The profile feeds back into primary-persona prompting: the persona knows the user well enough to phrase things, anticipate needs, and default-sensibly without asking.

**Privacy and audit:** every interaction captured must be visible to the user on request, with deletion controls. The deep-personalisation value proposition is wholly dependent on the user trusting the capture.

This is a substantial component — larger than any single Phase 4 piece, possibly its own phase.

---

## Idea 5 — Proactive suggestions grounded in the user profile

Bridging off idea 4: once pOS has a decent profile of the user, the system begins to suggest additional things it could accomplish for them that would make it more valuable to them.

**What this looks like in practice:**

- "You've been working on X for three weeks. Have you considered Y as a natural next step? I could do it as a background scope."
- "You keep asking me to do A. I could set up a scheduled task for A. Want me to?"
- "You've expressed interest in topic Z in passing; would you like me to keep a research radar running on it?"
- "I notice you spend Tuesday mornings on household logistics. I could draft the week's household scopes every Monday evening for your approval."

**Critical disciplines for this to work:**

- Suggestions must be rare enough to be signal, not noise.
- The user can turn the feature off entirely or dial its frequency.
- Every suggestion must be easily dismissable without cost (no "are you sure?" loops).
- The profile powering the suggestions is auditable (idea 4's requirement).
- Suggestions compose with the safety / reversibility / cost / self-correction layers — a suggested scope is still a scope.

This is the payoff for idea 4's investment. Without the profile depth, suggestions become generic and annoying; with it, they feel like a colleague who has been paying attention.

---

## Catalogue discipline

This file is the catalogue of future directions for pOS v2. Entries here are not commitments. When an idea is picked up, it becomes a real component cycle (research plan → research → proposal → brief → build → seal) and is retired from this file with a pointer to the component that now owns it. When an idea is deliberately dropped, it is retired with a one-line rationale.

New ideas append to the bottom of the file with a date.

---

*Catalogue maintained alongside STATE.md and BACKLOG.md as the third durable state artifact for the pOS v2 rebuild.*
