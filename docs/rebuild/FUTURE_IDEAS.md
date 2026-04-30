# pOS v2 — Future Ideas

Captured 2026-04-21. Ideas recorded for future work — not scoped, not committed to a timeline, not attached to a component. Each lives here until it either becomes a concrete component cycle or is explicitly retired. These are broader strategic directions than the operational items in `BACKLOG.md`.

---

## Core Development Principles — three research lenses

Design lenses now live in `/CLAUDE.md` at the repo root.

---

## Core Development Conventions — moved to the Dev/SDLC plugin

> The CDC corpus migrated to `plugins/dev-sdlc/docs/cdcs/` as part of M6b.0 (2026-04-29). The plugin is now the canonical home for dev-discipline machinery per Idea 13's two-modes design. See `plugins/dev-sdlc/docs/cdcs/README.md` for the index of the 10 CDCs. Each CDC lives at its own file in that directory.

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

**Dev/SDLC plugin sub-feature: objective-extraction skill for existing repos.** Captured 2026-04-26. Most users bring existing code with them — a job repo, a side project, an inherited codebase — and ODD's value-prop drops sharply if those projects can't be brought under the discipline retroactively. The proposed skill runs on a cloned repo and abstracts out what it believes the repo's objectives are: reverse ODD, walking UP the objective tree from concrete artefacts (files, methods, tests, configurations, deployment manifests) to a candidate objective list that the user can confirm, refine, or correct. Output: the objective list the project would have had if authored ODD-shape from the start, the ACs that would have backed each, and a coverage map flagging code that doesn't ladder up to any objective (ODD §2.5 violations the legacy code carries that the user can choose to address or sanction). **Critical implementation constraints, baked in from the start:** (a) handle very large repos via slice-and-swarm — slice the codebase into work units, plan a swarm of background sub-agents that each review a bounded set of files / methods / tests / configs, aggregate findings up; (b) token budget is the user's, not the harness's — instrument cumulative cost and pause / surface / resume rather than silently consuming budget; (c) work must be background-droppable — when the user requests something else, the extraction yields, parks state to disk, and resumes when bandwidth returns; (d) work must be background-pickup-able — the skill can be told "spend 30 minutes on this overnight while I'm not using the system" and make incremental progress without continuous user attention; (e) the slice/swarm/aggregate shape is itself an ODD pattern (each slice is a sub-objective + ACs scoped to its files; the aggregate is the umbrella objective). Composes with: parallelism trait (the swarm IS parallelism applied to a discovery problem); auto-skilling (this is itself a codified pattern, candidate for the skill ecosystem); cost-governance (token-budget-instrumented from day 1); Idea 4 (Deep personalisation — same "abstract structure from data" shape but for code rather than interactions); Idea 20 (LLM-as-classifier+verifier — slice-classify + deterministic-extract + verify shape). High leverage for SDLC plugin adoption — without this, ODD inside pos-v2 helps only greenfield work.

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

## Idea 6 — ODD as the default framing inside pos-v2 conversations

Captured 2026-04-22.

The primary persona should think in objectives by default. ODD is not only the methodology pos-v2 uses to author its own components (see `odd-methodology.md`) — it is also the shape the primary persona's *internal* model of every user request takes, inside every pos-v2 conversation.

Luke's framing:

> "how to get the primary persona to consistently 'think in objectives'. ODD should almost become the default way of framing all thoughts, or at least all requests, within any pos v2 conversation. but it also can't be overly technical and specific or it will make it impossible for nontechnical users to use. but i think enforcing tight bounds like with ODD in a transparent way will actually massively improve outcomes for non-tech users. they just won't know how to talk about it so clearly as a technical person might. so it would have to be carefully translate to and from the internal modeling into the way it discusses with users until they're able to learn more about what ODD is and what it means so they can start using it more impactfully."

What this composes:

- **Internal model is ODD-shaped** — objective + constraints + acceptance. The primary persona treats every request it receives as something to be represented internally in that shape before it acts, whether the request arrived as a one-line ask or as a long unstructured description.
- **User surface is natural language** — no technical vocabulary required. The user never has to say "objective," "constraint," or "acceptance criterion." The user talks the way they already talk.
- **Translation is the primary persona's responsibility.** This is the same translation layer described in `VALUE_PROPOSITION.md` — the persona translates between the user's natural-language intent and AI-effective execution. The new framing here is that the *AI-effective* side of that translation is specifically ODD-shaped, not just "well-structured" in some undefined way.
- **Tight bounds + transparency help non-tech users more than tech users**, even though non-tech users cannot articulate why. A technical user can state objectives and constraints explicitly; a non-tech user cannot, but still benefits from the system behaving as if those bounds were stated — because the behaviour that follows from tight bounds (no drift, no scope creep, deterministic acceptance) is exactly the behaviour non-tech users lack the vocabulary to demand for themselves.

Connection to Idea 2 (light-touch education): as the user engages with the system over time, the persona's ambient narration — "I made this a scheduled task because…," "the acceptance here is that X happens when Y" — gradually teaches the user the shape of ODD thinking without ever naming it. Users move up the sophistication curve on their own, at their own pace, and eventually begin framing requests in ODD-ish language themselves. At that point they can use the methodology more impactfully — they can name the constraints they care about, name the outcomes they want, and get proportionally better results from the system.

Open questions (future work, not for resolution here):

- How transparent should the internal ODD representation be to the user? Always surfaced? Surfaced on request? Surfaced only when ambiguity forces the persona to ask?
- How does the persona signal that a request was ambiguous in a way that ODD framing resolved — without turning that signal into pedagogy the user didn't ask for?
- What is the failure mode when the persona's internal ODD model diverges from what the user actually meant, and how does the user catch it?

These are not scoped here. This idea records the principle, not the implementation.

---

## Idea 7 — GLiNER2 expansion for memory-system entity extraction

Captured 2026-04-22.

Amendment #8 swapped memory-system's LLM backend to `ClaudePrintLLMClient` so entity and relationship extraction runs through the owner's Claude Max subscription rather than a metered API key. That swap solved the cost-surface question for the extraction path memory-system currently exercises, and deliberately left a second, orthogonal question untouched: whether a local zero-shot NER/relationship-extraction model — GLiNER2 is the specific candidate — should also sit on memory-system's extraction surface, either complementing Claude-based extraction for high-volume paths or replacing it for paths where local inference is materially cheaper or faster. The two questions were disentangled at amendment time so the subscription-routed swap could land cleanly; this idea keeps the deferred one on the register rather than quietly losing it.

GLiNER2 is an attractive shape on paper: open-weight, small, fast, zero-shot over arbitrary entity and relationship schemas, and free to run locally once loaded. The attraction depends on a structural question that the future cycle has to answer before anything else: does graphiti-core (memory-system's engine) expose a clean entity-extractor seam that a composed GLiNER2 adapter can slot into, or does the extractor live behind an implementation boundary that does not admit a second backend without a fork? If the seam exists, the question becomes one of composition shape — single-backend swap, dual-backend router with quality/cost heuristics, cascade pattern where GLiNER2 handles the cheap path and Claude handles edge cases. If the seam does not exist, the question shifts: is it worth widening the seam upstream, or does memory-system's own extraction surface grow a pre-extraction layer that funnels to the backend of choice.

The second research question is empirical: what fraction of memory's extraction volume is cost-dominated versus quality-dominated under the subscription-routed baseline amendment #8 just landed? If the Claude-via-Max path is effectively free at the volumes pOS v2 actually runs at, the case for GLiNER2 is weaker — the cost argument that motivates it evaporates. If volumes are high enough that the subscription path feels slow, or the quality on specific entity shapes is worse than a purpose-built NER model delivers, the case strengthens. That determination cannot be made from the outside — it needs telemetry from memory-system in a real evaluation workspace, which is why this is not scoped now.

This belongs in FUTURE_IDEAS rather than a near-term component cycle because both questions — the seam question and the volume/quality question — need data that does not yet exist. A research plan authored today would be speculation; a research plan authored after a few weeks of evaluation-workspace memory-system usage is grounded in numbers.

---

## Idea 8 — Structural context-load gate

Captured 2026-04-22.

Every pos-v2 session so far has rediscovered the same design corpus — `odd-methodology.md`, `odd-in-loam.md`, `FUTURE_IDEAS.md`, the proposal and seal notes for whatever component the current work touches — before it can plan or build correctly. The rediscovery cost is paid session after session because loading the relevant context is a social convention, not a mechanical precondition: the author remembers (or fails to remember) to read the design docs before dispatching work. When the author forgets, the work proceeds on incomplete context and the discrepancy surfaces in review, amendment, or audit instead of in the plan. A structural context-load gate removes the social layer: relevant design docs are *required* to be loaded before coding or planning begins, and the gate refuses to advance until they are.

The idea composes naturally with the plan-before-code CDC and the scope-only-dispatch CDC already codified in this file. Plan-before-code says a written plan must exist before any source edit; scope-only dispatch says a dispatch carries only scope. The context-load gate is the upstream companion — it says the primary persona (or the orchestrator layer it runs inside) cannot author the plan, or the scope, or dispatch the builder, until the design context that informs those artefacts has been loaded into the session. The gate is mechanical in the same sense ODD's acceptance-criterion validator is mechanical: not "the author should check this," but "the author cannot proceed until this passes."

The future research cycle has to answer several entangled design questions. Which contexts trigger the gate — build-dispatches only, or every pos-v2 work turn including questions and reviews? How does "relevant design docs" get computed without requiring the user to enumerate them — a static mapping of component to doc set, a dynamic lookup against the component's proposal/seal sidecar, a compose-with-the-Claude-capabilities-map approach, or something else? How does the gate compose with Claude's existing session-start hooks and with the skills ecosystem — is this a skill the primary persona invokes, a hook the harness enforces, or a primary-persona primitive authored at the pos-v2 layer? Is the gate workspace-wide (one gate across all pos-v2 components) or component-scoped (each component declares its own context set, the gate consults that declaration)?

The deeper positioning question: does this idea sit inside the primary-persona layer (the persona gains a "load context before acting" primitive) or inside the bootstrap/framework layer (every pos-v2 session is wrapped in a phase that performs the load)? The answer shapes which existing work the gate composes with and which work it displaces. That determination belongs in a research plan, not here.

This belongs in FUTURE_IDEAS rather than being scoped now because the shape of the gate depends on which Claude primitives end up backing it (Idea 1 Step 1 — the Claude-capabilities map — has not yet produced its deliverable) and on how much of the work is the primary persona's versus the harness's. Neither answer is available today.

---

## Idea 9 — Workspace-slug collision detection

Captured 2026-04-22.

Amendment #6 (`namespaced-labels-and-bootout`) moved hands-off-lifecycle's launchd labels from a single global name to workspace-namespaced names derived from the workspace basename — `com.pos.<slug>.orchestrator` rather than `com.pos.orchestrator`. The slug comes from the workspace directory's basename, which is deterministic and readable but is not a unique identifier: two workspaces with the same basename (two independent checkouts both named `pos-v2`, a `pos-v2` and a `pos-v2-backup/pos-v2`, a clone placed next to its origin without a rename) produce the same slug and therefore the same launchd labels. The bootout-before-bootstrap flow ensures only one of the two workspaces can be loaded at any moment — whichever boots second evicts the first — but the eviction is silent from the user's perspective and the second workspace believes it is running cleanly when it has just displaced a sibling. No current detection, warning, or disambiguation surface exists.

The future research cycle has to decide where detection lives on the install/bootstrap timeline. An install-time check refuses to install hands-off-lifecycle into a workspace whose slug collides with another already-installed workspace — the user is named, the collision is named, a disambiguation knob is offered. A bootstrap-time check detects the collision at first-boot and refuses to boot until the user acknowledges the other workspace. The two options have different failure characteristics: install-time catches the collision before the state machine is live, which is the cleaner shape; bootstrap-time catches collisions that install-time could miss (e.g. a second workspace renamed after install to collide with a third). The cycle may conclude both are needed.

The second open question is which component owns the detection. Hands-off-lifecycle is the component that actually issues the launchd labels, which argues for owning detection at its first-run path. Workspace-bootstrap is the framework layer that orchestrates first-run across components, which argues for owning cross-component concerns like slug uniqueness at its own layer. A cross-workspace registry (the detection has to see other workspaces' slugs, not only this workspace's) probably wants to live at the framework layer regardless, which tilts the answer toward workspace-bootstrap — but the hands-off-lifecycle install flow is where the failure surfaces, so the user-facing message probably surfaces there. The split is not obvious and deserves a real proposal.

The third question is the disambiguation mechanism. Does the fix ship a slug-override knob the user can set to disambiguate (e.g. `POS_V2_WORKSPACE_SLUG=pos-v2-eval`)? Does it auto-suffix on collision and tell the user what it did? Does it refuse to proceed and require the user to rename the directory? Each shape has a different UX character and composes differently with the self-retiring-setup CDC and the step-by-step-when-the-system-cannot-act CDC already recorded above.

This belongs in FUTURE_IDEAS rather than being scoped now because the collision is a latent hazard, not a currently-biting bug — Luke operates one pos-v2 checkout at a time. When a second checkout is spun up for any reason (evaluation workspace, backup directory, parallel development line), the hazard becomes live and the idea graduates to a component cycle.

**Update (2026-04-23, amendment #28).** Slug collision in launchd labels is not the only workspace-identity hazard — first-run *state-file routing* was a sibling defect. Under the session-start-detachment amendment the first-run completion state lived at the host-global `~/.pos/first-run.state` with no workspace identity, so workspace A's completed state short-circuited workspace B's dispatcher into a false-success message. Amendment #28 closes that sibling by routing state workspace-locally (`<workspace>/.pos/first-run.state`) and adding a `workspace_root` field inside the state content as defence in depth. The slug-collision hazard above — two workspaces with the same basename producing the same launchd labels — remains open for its own future cycle. When that cycle runs, it inherits amendment #28's finding that workspace-identity enforcement is cheapest when structural (paths) rather than advisory (remember-to-check).

## Idea 10 — Project rename to loam

**Status:** UN-TABLED 2026-04-29 — prerequisite amendments (#26 teardown retrofit) shipped long ago (current amendment cycle at #75); Phase 1 documentary rebrand activated as part of v0.1.0 publish (Idea 12). Tier-2 dormancy rename also activated — owner ruling 2026-04-29 placed it pre-launch. Decisions recorded in `docs/rebuild/plans/loam-rename-decisions.md`.

Captured 2026-04-23.

pOS v2 is being renamed to **`loam`** — substrate-not-plant metaphor
that matches the project's actual identity: the enriched medium the
user cultivates their Claude agent in (user-intent = seed,
Claude = genetic machinery, grown agent = plant). The seed framing
already canonical at `docs/rebuild/spec/loam-objectives-spec.md:73`
is preserved — `loam` names the substrate; the seed / cultivar /
growth metaphor in existing narrative is unchanged.

Decisions recorded in `docs/rebuild/plans/loam-rename-decisions.md`.
Migration research (inventory, bucketing, phased plan) in
`.scratch/claude-output/loam-rename-migration-plan.md`.

Approved Tier-1 renames (compressed):

- `pos-v2` / `pOS v2` → `loam` (brand, docs, repo directory).
- `~/.pos/` → `~/.loam/`.
- `POS_V2_*` env vars → `LOAM_*`.
- `com.pos-v2.<slug>.*` launchd labels → `com.loam.<slug>.*`
  (drop version bake-in).
- OTel `pos.*` → `loam.*`.
- `pos-amend` CLI → `loam amend` under a unified `loam` top-level CLI.

Tier-2: graceful-degradation → `dormancy`. Package layout: monolithic
`loam.*` namespace. Kept technical (do NOT rename): memory-system,
self-correction, scope-of-work primitive (with `plot` acceptable as
user-facing CLI alias only). Historical record preserved —
commit messages and seal narratives retain "pOS v2"; no retroactive
rewrites.

Execution: multi-amendment migration, kicked off after amendment #23
(frozen-H19 per-invariant baseline, sealed `a27a833`, 2026-04-23).
Phase 1 (documentary rebrand) scoped next.

---

## Idea 11 — Amendment-chain recollapse/reseal convention

Captured 2026-04-22.

As a component accumulates amendments (proposal + amendment #1,
#2, … #N), reading the current state requires walking every
amendment's seal narrative in order — the proposal describes the
original behaviour and each amendment records a delta against the
prior state. A **reseal** operation would let a component periodically
fold that chain into a new baseline: archive prior narratives to
`<comp>/seals/archive/`, reset the seal-diff BASELINE to the reseal
commit, rewrite the proposal so current behaviour is the lede and
amendment history moves to an appendix, and write a fresh v2 narrative.
Source stays byte-identical to the pre-reseal tree; git history is
untouched; every prior amendment remains reachable through the archive
and the commit log.

Detailed design proposal (archive layout, baseline-pointer mechanics,
proposal-rewrite scope, sidecar model) lives at
`.scratch/claude-output/loam-recollapse-reseal-research.md`.

Rulings captured at capture-time:

1. **Hypothetical right now** — no component currently warrants a
   reseal; no tooling is built yet.
2. **Reseal shipping: (a)** — when a reseal does happen, the
   proposal-rewrite and the amendment-appendix move ship together
   in the same reseal amendment, not split across two.
3. **Sidecar backfill: lazy** — per-component narrative sidecars are
   introduced only when that component reseals; no universal
   backfill pass.

Status: **deferred — no concrete trigger yet. Revisit when a
component's amendment chain feels unwieldy.** When activated, the
research doc's §3 proposed model plus the three rulings above govern
the first reseal amendment.

---

## Idea 12 — Open-source launch of loam

Captured 2026-04-22.

**Status:** ACTIVE 2026-04-29. All three open rulings closed (see resolved-rulings block below); prerequisite amendments (#26 teardown retrofit) shipped at #75-current; loam Phase-1 documentary rebrand and Dev/SDLC plugin authoring fold into the v0.1.0 publish work-plan at `docs/rebuild/plans/oss-v0-1-0-publish.md`.

loam launches publicly as an open-source project once the core is
release-ready and the Dev/SDLC plugin (Idea 3) ships. The research
doc covers positioning, release-readiness checklist, repo hygiene,
launch sequencing, engagement, success criteria, and risks.

Top 3 next actions (from the research's executive summary):

1. **Author the Dev/SDLC plugin research plan** — must-ship-at-v1
   per Idea 3; makes loam's ODD pitch visible to the developer
   audience.
2. **Write single-page `docs/positioning.md`** — one-sentence pitch,
   three-paragraph description, target personas, explicit non-goals.
   Downstream artefacts (README, HN title, blog post) all quote from it.
3. **Adopt Apache-2.0 + author LICENSE + CONTRIBUTING.md +
   CODE_OF_CONDUCT.md + SECURITY.md** — signals "this is a real
   project" to first-click reviewers; one-day task; costs the first
   impression if missing.

Biggest risk flagged by research: **maintainer burnout + bus-factor-1.**
loam is a one-person foundation built against a health context
(ADHD, autism, chronic pain, insomnia) that's explicitly design-in-scope
and equally a maintenance-capacity input. Public launch adds 2-4 weeks
of intense response labour (HN, PRs, first bugs). Without pre-launch
recruited co-maintainer circle (or at minimum a shortlist), loam is one
personal-circumstances change from unmaintained-famous-project failure
mode — worse than niche adoption because it comes with stranded users.

Resolved owner rulings (2026-04-29):

1. **Dormancy rename:** **pre-launch** (matches research recommendation). Tier-2 graceful-degradation → dormancy executes inside the v0.1.0 publish sequence, not deferred to v0.2.
2. **v1 plugin count:** **Dev/SDLC only** (matches research recommendation). Audit's deviation to "zero plugins" was rooted in human-time cost framing; AI-time correction undercut that reasoning.
3. **Public repo ownership:** **`lukeivers/loam`** (personal account; deviates from research's product-brand recommendation). Reasoning: honest about bus-factor-1; low ceremony; easy to migrate to an org later if traction warrants.

Full plan at `docs/rebuild/plans/research/loam-open-source-launch-research.md`
for timelines, repo hygiene detail, competitive positioning, content
marketing, engagement, success criteria, and the 13-section full plan.

Status: **planning phase.** Open-source launch is a project-level gate;
loam core + Dev/SDLC plugin both need to be v1-ready before launch.
No immediate execution; rulings on the three open questions unblock
concrete preparation work.

---

## Idea 13 — Two modes (NORMAL USE / DEV MODE) and multi-workspace umbrella

Captured 2026-04-25 (graduated from `FUTURE_IDEAS_DRAFT.md`).

pos-v2 ships as a single GitHub-distributed repository serving both end users and contributors. Two operating modes — **NORMAL USE** (no dev tools auto-load) and **DEV MODE** (dev tools auto-load on intent signal) — live in the same clone. A workspace-local persona-onboarding answer is the authoritative dev-intent signal; the user shouldn't have to manually configure anything heavyweight to switch modes. **Multi-workspace concurrency** (running more than one pos-v2 workspace concurrently on a single host) is captured here as a future direction; it is not part of v1 but the design preserves the migration path.

This idea is the umbrella for the broader two-modes-and-multi-workspace programme. The **active part** is in flight as a master-plan + four sub-plans at `docs/rebuild/plans/two-modes-and-multi-workspace/` (sub-plans A → E → B → F — persona-onboarding dev-intent question, classify_workspace replacement with the path-mismatch fix folded in, two-mode loading mechanism, dev-mode auto-load partition). The **deferred parts** sit under this idea's umbrella for activation when the multi-workspace cycle is picked up:

- **Sub-plan C** (`C-state-file-migration.md`) — multi-workspace state-file migration: every host-global `~/.pos/` SQLite + YAML file gets a workspace-local override path per the `~/.claude/` + `<workspace>/.claude/` pattern owner ruled in D-MASTER.2.
- **Sub-plan D** (`D-memory-port-auto-allocation.md`) — per-workspace memory-graphiti port auto-allocation. Default port 8765 is a multi-workspace collision risk; auto-allocation via `bind(0)` at scaffold time eliminates it.
- **Sub-plan G** (`G-shared-memory-workspace-keying.md`, NEW stub authored 2026-04-25) — shared host-level memory-graphiti instance + workspace-keying via graphiti's `group_id` parameter. A single shared instance serves N workspaces; content is keyed per-workspace by default with an explicit "global" channel for cross-workspace memories (user preferences, identity facts). Sub-plan G captures the design direction; if it activates first at multi-workspace reactivation, it absorbs sub-plan D's outcome (one shared instance, no port collisions).

**Implications already partially addressed by the active programme:**

- `classify_workspace` in amendment #39 is replaced by sub-plan E — `VALUE_PROPOSITION.md` presence is no longer a viable dev-marker since every GitHub-cloned user has it; classification tracks the user's own dev-intent answer instead.
- Host-global `~/.pos/` SQLite files migrate to workspace-local on a per-file basis (extending amendment #28's pattern); the global-vs-workspace partition mirrors Claude Code's own `~/.claude/` + `<workspace>/.claude/` pattern.
- What auto-loads in DEV MODE: `pos-amend`, plan docs, manifest YAMLs, BASELINE conventions, SEAL_COMMITs, sealed-component conventions, dispatch-template, spec docs, component proposals + seal narratives, ODD methodology, dev CDCs from FUTURE_IDEAS.md.
- What stays loaded in NORMAL USE: the runtime harness (memory-system, scope-of-work, primary-persona, objective-tracker, all the Phase 1–4 sealed components), `VALUE_PROPOSITION.md` (still load-bearing for tracker root), basic settings, plus end-user-facing docs/help.

The deferred sub-plans (C, D, G) reactivate when the multi-workspace cycle is picked up. They compose under this idea's umbrella; the master plan's §11.5 explains the deferral rationale. Full reactivation requires a fresh proposal cycle (the sub-plan files on disk are the design seed, not the final shape).

---

## Idea 14 — Path-mismatch (#39 ↔ #40) fix direction (active fix folded into E; comprehensive resolver deferred)

Captured 2026-04-25 (graduated from `FUTURE_IDEAS_DRAFT.md`).

A real latent bug in the post-#39/#40 surface: tracker DB write path (`workspace_bootstrap.adapters.tracker_seed.tracker_db_path_for(pos_root)`) vs read path (`primary_persona.tracker_context.tracker_db_path_for(workspace_root)`). The same helper accepts different roots from different callers — the writer passes `pos_root`, the reader passes `workspace_root`. Bites the moment #40's contributor wires to live persona registration: the persona reads from `workspace_root`'s tracker DB and finds it empty, because #39 seeded into `pos_root`'s.

Owner-leaned fix direction (recorded mid-session 2026-04-25): **B (#39 writes to `workspace_root`)** consistent with amendment #28's workspace-locality and the end-user-shipped principle (the workspace is the unit; pos_root is the install location, not the data location).

**Active fix.** Folded into sub-plan E (the `classify_workspace` replacement, in-flight as the active two-modes programme): a small additive change to `tracker_seed.py` — change the write path argument from `pos_root` to `workspace_root` to match #40's read path. Because E already touches `tracker_seed.py`, the fix folds in without expanding scope (single-component, single amendment). Documented in the master plan's §11.5.

**Comprehensive resolver (deferred under Idea 13's multi-workspace umbrella).** A more thorough fix would extract a workspace-aware path-resolver pattern that all multi-workspace path consumers share (`tracker_seed`, `tracker_context`, `pos_amend.tracker_registration`, the cost / scope-of-work / orchestrator adapters per sub-plan C). The shared resolver enforces consistency: callers can't pass the wrong root because they don't pass a root at all — they pass a workspace handle, and the resolver derives both `pos_root` and `workspace_root` consistently. This deeper fix waits for sub-plan C's reactivation; the active fix in E is sufficient for the single-workspace v1.

**Trigger to activate the comprehensive direction:** when sub-plan C reactivates (multi-workspace cycle), the path-resolver pattern absorbs C's per-component path-rewriting work. Composes with Idea 15 (shared `pos_paths` helper) — the resolver lives in or alongside that helper module.

---

## Idea 15 — Shared `pos_paths` helper for `TRACKER_DB_FILENAME` and sibling path constants

Captured 2026-04-25 (graduated from `FUTURE_IDEAS_DRAFT.md`; surfaced by amendment #16 build agent).

The constant `"objective_tracker.sqlite"` is now duplicated across three consumers: `workspace_bootstrap.adapters.tracker_seed` (writer per #39), `primary_persona.tracker_context` (reader per #40), and `pos_amend.tracker_registration` (registrar per the pos-amend-tracker-integration plan post-#16). Each consumer hard-codes the filename. A fourth consumer would warrant extraction; the third was the trigger flagged at #16 build, but the extraction cost was not worth a dedicated amendment then.

**Direction.** A shared helper module — working name `pos_paths` — that single-sources the workspace-relative path constants every cross-component consumer needs. Tracker DB filename is the first; sibling candidates include the orchestrator SQLite filename, the scope-of-work SQLite filename, the first-run state filename (per amendment #28), the persona-contract directory layout (per amendment #36), and the memory-yaml override path (per amendment #29).

**Composition with Idea 14.** The path-resolver pattern (Idea 14's deferred direction) can live in or alongside `pos_paths`. The resolver answers "which root applies for this consumer" while `pos_paths` answers "what is the workspace-relative path for this state file." Together they replace the duplicated string-constant + path-arithmetic pattern with one source of truth.

**Trigger to activate.** Either: (a) a fourth consumer of `TRACKER_DB_FILENAME` arrives (the Idea-15 trigger from the original draft entry), OR (b) sub-plan C reactivates (multi-workspace cycle) and the resolver pattern needs a home, OR (c) any sealed-component amendment introduces a third hard-coded sibling constant (orchestrator / scope-of-work SQLite filenames are the next candidates).

**Out of scope for activation.** The helper does not introduce new state surfaces; it consolidates existing ones. Its activation should not require any sealed component to expose new path semantics; if it does, the activation is mis-scoped.

---

## Idea 16 — Tracker public API for source-commit rewriting (replace pos-amend's direct SQLite poke)

Captured 2026-04-25 (graduated from `FUTURE_IDEAS_DRAFT.md`; surfaced by amendment #16 build agent).

`pos_amend.tracker_registration.update_source_commits` currently reaches into the tracker's SQLite directly to rewrite the `lifted_from.source_commit` JSON field after seal. Works against amendment #38's stable schema, but a future tracker amendment changing the `lifted_from` JSON shape would silently break pos-amend without an obvious test signal in pos-amend's own test surface — pos-amend doesn't own the schema, so it can't detect schema drift.

**Direction.** A tracker public API — working name `tracker.rewrite_lifted_from_source_commit(objective_id, sha)` (or equivalent) — that owns the SQLite read/write at the tracker layer. pos-amend calls the API; the tracker enforces the schema; schema changes break the API contract (which pos-amend's test suite catches via the API surface), not the storage layout silently.

**Composition.** This is a sealed-component amendment to `objective-tracker` — small surface, narrow API addition, no schema change at first. The amendment's AC count is small (one new public function, one test verifying the function rewrites the SHA, one test verifying the schema-error path).

**Trigger to activate.** Either: (a) a fourth tracker SQLite consumer appears (each new consumer multiplies the schema-drift surface area), OR (b) the next tracker amendment touches `lifted_from`'s shape (which would break pos-amend silently today; the API guard prevents the silent failure). Lightly-coupled to Heavy-B Phase γ — when continuous registration runs at every amendment, pos-amend's poke happens more often, raising the value of the API guard.

**Out of scope.** Migrating other pos-amend ↔ tracker boundaries to API form (e.g. the `objectives` block's apply-time write path) is a separate cycle. This idea names only the post-seal source-commit rewrite.

---

## Idea 17 — Dispatch-template ↔ persona-tracker composition (stretch)

Captured 2026-04-25 (graduated from `FUTURE_IDEAS_DRAFT.md`).

Stretch idea about composing two existing surfaces. The dispatch-template engine (research+plan task #23, building toward a templated agent-dispatch authoring shape) could lean on the persona-tracker context (per amendment #40) to know which sub-agent shape applies for a given workflow — the template's variable defaults could be computed from the workspace's current tracker state rather than hand-supplied per dispatch.

**Why this is a stretch.** The leverage requires both the dispatch-template engine AND the persona-tracker context to be settled in shape. Neither is fully settled today (dispatch-template is in flight; tracker-context is post-#40 but its surface evolves with each amendment). The composition is high-leverage when both stabilise; it is medium-cost speculation today.

**Composition.** Templates declare which tracker-context fields they consume; the dispatch-template engine queries the persona-tracker context at expansion time; the engine fills the template's defaults from the tracker. Example: a "build-agent dispatch" template with a `{{IN_FLIGHT_AMENDMENT}}` placeholder computes its default from the tracker's "what amendment is active in this workspace" query.

**Trigger to activate.** When all three of the following are true: (a) dispatch-template engine has stabilised (post-research-and-plan-#23, post-first-batch of templates landing), (b) persona-tracker context has stabilised (post-Heavy-B-phase-γ continuous registration is steady-state), (c) a concrete dispatch shape benefits from the composition (the abstract benefit is not enough; a specific repeated dispatch pattern needs the auto-fill).

**Inverse-asymmetric concern.** The composition is tempting but can over-couple two surfaces that are independently useful. Surface for review post-initial-phase per the original draft entry; do not pull this in pre-emptively.

---

## Idea 18 — Reusable integration-test harness extraction

Captured 2026-04-25 (graduated from `FUTURE_IDEAS_DRAFT.md`; surfaced by the 2026-04-25 integration-test agent).

The "fresh-clone first-run with sandbox isolation + Monitors" pattern that the 2026-04-25 integration-test agent used is a one-shot today — the agent's prompt + scratch fixtures + post-run analysis carry the harness shape. The pattern could become a reusable harness for any future integration test (post-amendment regression checks, cross-clone sanity checks, multi-workspace fixtures per sub-plan C / Idea 13's deferred parts, etc.).

**Direction.** A `tools/integration-test/` script (or sub-package under `tools/pos-amend/`) that captures the pattern: fresh-clone bootstrap → first-run dispatch under Monitor → controlled-fixture state inspection → structured findings report. The harness is dev-discipline (`tools/`-resident, no sealed-component changes); each integration test is a small recipe that names what to scaffold, what to run, what to inspect. The harness handles sandbox isolation, Monitor wiring, output paths, and findings-report shape.

**Composition.** Future integration tests (sub-plan C's two-workspace fixture per AC.PROG.1, sub-plan G's cross-workspace memory-isolation test, post-amendment regression sweeps) all benefit. The harness is the difference between "spin up a fresh agent prompt with the entire fixture-shape inline" (today) and "write a 30-line recipe that the harness expands" (future).

**Trigger to activate.** Worth considering once a second integration-test pattern surfaces — the second use is what calibrates "is the abstraction right" before extraction. Before then, every recurring fixture pattern feels like the right abstraction; after, the actual shape is empirically validated. The integration-test agent run from 2026-04-25 was the first; the second is yet to happen.

**Out of scope for activation.** Generic test-runner functionality (pytest already covers it). The harness specifically captures the fresh-clone + Monitor + first-run pattern, not generic Python-test execution.

---

## Idea 19 — Scaffold-runner observability: emit ScaffoldResult fields into the worker log

Captured 2026-04-25 (graduated from `FUTURE_IDEAS_DRAFT.md`; surfaced by the 2026-04-25 integration-test agent's Finding-2 investigation).

`workspace_bootstrap`'s `first_run_scaffold_runner.py` discards the `ScaffoldResult` returned by `run_first_run_scaffold` — the fields `tracker_seeded`, `tracker_seed_reason`, `tracker_classification` (added by amendment #39) never reach the worker log. A `skipped_no_value_prop` outcome would be silent: the scaffold completes, the tracker is empty, the user sees "first-run done" with no signal that seeding was skipped. The 2026-04-25 integration-test agent's Finding-2 hypothesis was caused (in part) by exactly this silent-failure shape — the agent had to re-derive the seed outcome from secondary signals because the primary signal was discarded.

**Direction.** A one-line diagnostic emit on the success path of `run_first_run_scaffold`'s caller — log the seed outcome (one structured event with `tracker_seeded`, `tracker_seed_reason`, `tracker_classification`) at the worker-log surface. Future investigations of seed behaviour read the log directly; no re-derivation needed.

**Composition.** This is a sealed-component amendment to `workspace-bootstrap` (the scaffold-runner is in workspace-bootstrap's territory). Small surface — one log emit, one test verifying the log carries the expected fields after a fresh scaffold. Could batch with sub-plan E's amendment if both land in the same `tracker_seed.py` neighbourhood; otherwise its own narrow amendment.

**Trigger to activate.** Either: (a) sub-plan E activates and the amendment can absorb the diagnostic emit (cheapest), OR (b) a second silent-failure investigation surfaces (the integration-test agent's Finding-2 was the first), OR (c) any future amendment to the scaffold-runner surface area where the diagnostic is in the same neighbourhood.

**Out of scope.** A full structured-events programme for first-run observability (telemetry, OTel events, dashboard surfaces). This idea is the one-line emit, not the framework — composable with future telemetry work but not blocked by it.

---

## Idea 20 — LLM-as-classifier + LLM-as-verifier, never LLM-as-generator (meta-pattern)

A generalisable pattern surfaced 2026-04-27 from the workspace-sync milestone live-test. When the LLM acts as **content GENERATOR** (e.g. produces a fully merged file as `merged_content`), it must emit every line of the result — for a 100-line file that's ~5-7k output tokens, ~60-120s+ at typical rates. Asymmetric insight: **small-output LLM calls are cheap; large-output ones are not.**

The pattern collapses generator-shaped problems into two small-output calls bracketing a deterministic primitive:

1. **Classify** (small LLM call, ~50 token output): "Is this {file / case / situation} structurally tractable to {merge / transform / reshape}? If yes, what class?"
2. **Apply** (deterministic primitive, ~0.01s, free, audit-grade reproducible): the matching transformation does the actual work.
3. **Verify** (small LLM call, ~200 token output): "Did the deterministic step preserve {meaning / intent / content}? Any concerns?"
4. **Apply or fall back**: verify passes → accept; verify fails → fall back to the slow LLM-generator path OR halt-and-surface.

**Properties:**

- **Speed:** generator-path → ~60-120s+; classifier+verifier path → ~10-30s. **3-8× faster** in observed cases.
- **Cost:** LLM cost scales with output tokens. Small-output calls are cheap.
- **Auditability:** the deterministic step is reproducible; the verify step is logged. The generator path produces opaque content trusted on faith.
- **Safety:** verify-fail is a high-quality halt-and-surface signal. The generator path has no equivalent.

**Generalises beyond merge resolution to** test generation (deterministic harness + LLM verifies coverage), code review (deterministic linters + LLM verifies semantic correctness), doc summarisation (deterministic outline extraction + LLM verifies fidelity), context compaction (deterministic dedupe + LLM verifies nothing-load-bearing-lost), and any "design + check" task where deterministic primitives can do the design.

**Composes with:**

- Idea 1 (three-lens enforcement): the meta-pattern is itself a candidate enforcement rule — when a feature requires LLM output >X tokens, prefer classifier+verifier shape.
- Idea 4 (Deep personalisation): structured user-profile updates from interactions are deterministic; LLM verifies coherence.
- Idea 6 (ODD as default framing): ODD-shaped tasks are themselves deterministic-primitive-shaped; the persona can verify rather than generate.
- Cost-governance: classifier+verifier shape has known-bounded token budget; generator shape does not.

**Origin and first manifestation:** workspace-sync clause-(h) merge resolver (#56) shipped as LLM-as-generator. Live-test against pos3 timed out on the first inferred-merged verdict (FUTURE_IDEAS_DRAFT.md, ~125 lines × 2 sides + JSON schema = ~5k+ input tokens, full file output forced 120s+ subprocess timeout). Refined design (Bundle α.2 in DRAFT) replaces the generator path. Captures the pattern as a meta-rule for all future LLM-mediated features.

---

## Idea 21 — Persona own-behaviour structural enforcement

Captured 2026-04-27 (graduated from `FUTURE_IDEAS_DRAFT.md` after
4+ documented failure modes in a single session).

The primary persona has a recurring failure mode: asking permission
on uncontroversial in-scope work despite explicit broad-autonomy
directives ("want me to X?", "awaiting your call", "ruling
needed"). Discipline-level reminders have failed empirically — the
pattern is too easy to slip into mid-reply.

Three structural-enforcement candidates:

1. Stop-hook contributor that scans persona's outbound replies
   (Telegram + terminal + Claude desktop) for permission-asking
   patterns and either (a) rewrites them to action announcements
   ("doing X unless you object") or (b) halts with a
   self-correction step before send.
2. Deterministic post-processor at Telegram-send time that converts
   "awaiting your call on X" → "doing X unless you object" for
   in-scope work, evaluated against the autonomy directive at
   send time.
3. Structural pre-send check baked into the reply tool wrapper.

Composes with Idea 1 (three-lens enforcement substrate), Idea 6
(ODD as default framing — own-behaviour is a class of in-scope
work), Idea 20 (LLM-as-classifier+verifier — the rewrite step is
exactly the meta-pattern).

Sibling structural-enforcement candidates from the same review:
default-action-verb rewrite ("I'm doing X" not "want me to X?"),
dossier-canonical-truth deduplication (warn on dossier claims that
disagree with git log / plan-doc §14 / manifest).

Trigger to activate: A1 substrate (existing structural-enforcement
programme) lands and is stable; this is a natural A2 / A3
amendment on top.

---

## Idea 22 — Memory-doc skeleton template (third member of the template family)

Captured 2026-04-29 (graduated from `FUTURE_IDEAS_DRAFT.md`).

The dispatch-template (`framework/tools/pos-amend/templates/dispatch/sealed-component-build.md`) and plan-doc-template (`framework/tools/pos-amend/templates/plan/dev-discipline.md`) shipped during the amendment cycle. Both follow the same shape: frontmatter (description + required + optional vars), then a `{{placeholder}}`-shaped body. Memory-doc authoring (the per-feedback files at `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_*.md`) follows the same per-document structure — frontmatter (name / description / type) + Why + How-to-apply — but is propagated by precedent rather than mechanised.

**Direction.** A third template at `framework/tools/pos-amend/templates/memory/feedback.md` (or similar) standardising the frontmatter fields and ensuring no field drifts over time as the memory ecosystem grows.

**Composition.** Same template engine as the existing two templates; same `description` frontmatter doubles as `pos-amend template list` one-liner (per the DRAFT entry on the introspection-surface pattern). Memory authoring becomes `pos-amend new-memory <slug>` (parallel to the future `pos-amend new-plan <slug>` orchestration).

**Trigger to activate.** Either: (a) a fourth memory file with drifted frontmatter is observed, OR (b) the memory-graphiti integration (Idea 7 GLiNER2) starts consuming memory-doc structure programmatically and benefits from rigid frontmatter.

**Out of scope.** This is the template, not the memory ecosystem itself. Memory content (which feedbacks exist, what they say) remains a per-feedback authoring decision.

---

## Idea 23 — Research dispatches pre-filter recommendations through the scope-fence constraint

Captured 2026-04-29 (graduated from `FUTURE_IDEAS_DRAFT.md`; recurring across #17, #68, A1 builds).

Research dispatches today produce recommendations that the build dispatch then has to deviate from when the recommendation reaches a sealed component the build can't touch. The #17 build's D-build.6 hit exactly this: research recommended attaching the lazy-projection trigger via primary-persona's contributor surface, but primary-persona was sealed and the dispatch was dev-discipline (`tools/` fence). The deviation was forced at build time, not anticipated at research time.

**Direction.** Research-author dispatch prompts grow an explicit "filter recommendations through the scope-fence constraint" instruction: every recommendation cites which surface it reaches and verifies that surface is admitted by the dispatch's scope fence. Recommendations that reach sealed components outside the fence get either (a) rewritten to a dev-discipline-equivalent attach point (loam-mode emitter, hooks dir, `tools/` etc.) OR (b) explicitly flagged as "build-time deviation needed" with the alternative attach point.

**Composition.** Composes with Idea 1's three-lens enforcement (Step 3 enforcement layer can verify research docs cite scope-fence compliance) and amendment #72 A4's `agent_guard.py` (T2 method-enumerated-prompt detection — extending the same surface to detect research recommendations that cross fences). Lens 1 leverage: Claude-Code skills could carry the scope-fence-filter as a research-author skill loadable per dispatch.

**Trigger to activate.** Next non-trivial research-then-build amendment cycle is the right time; the cost is one paragraph in the research-author dispatch boilerplate, the payoff is at least one less build-time deviation per non-trivial amendment.

**Out of scope.** Generic research-author dispatch hardening (factual verification CDC etc.). This idea names only the scope-fence-filter dimension.

---

## Idea 24 — Bash-tool eval-wrapper hazards (glob expansion + stderr capture)

Captured 2026-04-29 (graduated from `FUTURE_IDEAS_DRAFT.md` from two related findings).

The Bash tool wraps commands in an `eval`-style shell that produces non-interactive-shell behaviour distinct from the user's interactive zsh. Two observed hazards:

1. **Glob expansion failure** — `(eval):1: no matches found: <glob>` errors when a glob fails to expand, even when the interactive shell has `setopt nomatch` UNset. The same pattern via `bash -c '...'` or `find -name` works. Caused at least one false-positive "files don't exist" diagnosis during agent dispatches.
2. **Stderr capture drop** — when pos-amend was invoked from a main session via the Bash tool, stderr (where halt diagnostics emit) was filtered/dropped and the tool appeared to silently return rc=0. A fresh agent session running pos-amend saw the halts correctly. Workaround for in-session pos-amend invocations: `2>&1 | tee /tmp/log` or wrap in a script that explicitly captures stderr to a file.

**Direction.** Two structural-enforcement candidates compose:

- A PreToolUse hook (matcher Bash) that warns when an unquoted glob is passed to the tool (zero-result glob would expand surprisingly), suggesting `find -name` or quoted alternatives. Composes with amendment #72 A4's `bash_guard.py` — extends its classifier surface, no new file.
- A pos-amend-side wrapper that always emits structured halt diagnostics to stdout (or a log file), not just stderr, eliminating the stderr-drop failure class regardless of harness behaviour.

**Composition.** Composes with Idea 1's three-lens Claude-leverage lens (PreToolUse is the right Claude primitive here) and Idea 21's persona own-behaviour structural enforcement (similar Stop-hook contributor shape). Lens 1 leverage: PreToolUse hook is a Claude-native primitive that exactly fits the shape.

**Trigger to activate.** Either: (a) a third Bash-tool quirk surfaces (the third instance is what tips one-off-quirk into pattern), OR (b) the structural-enforcement programme adds a fifth A-amendment slot for general Bash-tool-quirk hardening, OR (c) a high-cost diagnosis (>30 minutes wasted on a quirk) recurs.

**Out of scope.** Filing upstream Claude-Code feature requests for the eval-wrapper itself. The right surface is pos-v2-side detection + workaround, not begging the harness to change.

---

## Idea 25 — Workspace-level default-conversation-channel config slot

Captured 2026-04-29 (graduated from `FUTURE_IDEAS_DRAFT.md`; locked behaviour confirmed 2026-04-26 for the pos3 workspace).

Telegram is now the default conversation layer for the pos3 workspace, but the directive lives in the dossier prose — advisory. A persona session that opens against fresh context (no prior turn cached) depends on the persona reading the dossier and remembering to route to Telegram. The recurring miss class: persona replies in-terminal when the user is on Telegram.

**Direction.** A workspace config slot (working name `primary_channel`, location candidates: persona contract field, `<workspace>/.pos/channel.json`, or `<workspace>/CLAUDE.md` frontmatter) that names the workspace's default conversation channel. Persona reads the slot at session-start (composes with #73's corpus-inlining hook) and routes default replies through the named channel's tool — Telegram via `mcp__plugin_telegram_telegram__reply`, terminal output secondary.

**Composition.** Composes with the corpus-inlining hook (#73) — the channel slot becomes another sentinel field A1 substrate populates at session-start, indistinguishable from `workspace_mode` or `corpus_paths_loaded`. Composes with Idea 21 (own-behaviour enforcement) — channel-routing miss is a structural-enforcement candidate (Stop-hook contributor refuses to send to terminal when `primary_channel = telegram` and the message is a user reply). Composes with Idea 1's Claude-leverage lens — MCP reply tools are the Claude-native primitive the slot routes through.

**Trigger to activate.** Either: (a) a second workspace adopts a non-terminal default channel (proves the abstraction is multi-tenant), OR (b) a third documented case of routing-miss-because-persona-forgot, OR (c) the structural-enforcement programme reaches A5+ slot.

**Out of scope.** Multi-channel concurrency (replying to both Telegram and terminal simultaneously). This idea names only the default channel; secondary-channel rules belong in a separate cycle.

---

## Idea 26 — Workspace-specific corpus overrides via reader fall-through

Captured 2026-04-29 (graduated from `FUTURE_IDEAS_DRAFT.md`; surfaced as asymmetric finding by amendment #67 build agent).

The `_resolve_corpus_path` helper that landed in `primary-persona/session_start_gate.py` per amendment #67 (AC.SFR.3, decision D5: probe-and-prefer-workspace-root) elegantly supports a feature that wasn't designed-for: workspaces shipping their own CLAUDE.md / docs/ overrides at the workspace root that take precedence over framework's defaults. No additional code is needed; the resolver already handles it.

**Direction.** Surface this affordance explicitly to: (a) DEV-MODE workspace authors (write a workspace-local `CLAUDE.md` to override framework's three-lens defaults for that workspace), (b) customised personas (a workspace ships its own persona prompt that the loader prefers), (c) plugin-shipped corpus extensions (a plugin installs corpus files at workspace root that compose with framework's defaults).

**Composition.** Composes with amendment #73's corpus-inlining SessionStart hook — workspace overrides flow into `additionalContext` automatically because the inliner reads through the same `_resolve_corpus_path` helper. Composes with Idea 13 (two-modes umbrella) — DEV MODE workspace overrides are a natural shape; NORMAL USE overrides for non-tech-user customisation are a future shape. Composes with Idea 3 (initial plugin suite) — plugins shipping corpus extensions become first-class.

**Trigger to activate.** No activation needed — the affordance exists today; this idea is the *surface* of it. Concrete activation: (a) document the override pattern in onboarding flow when a second workspace adopts an override, (b) author the first reference override (e.g. a domain-specific persona prompt for a derived workspace), (c) when sub-plan G activates and plugins start shipping corpus, the resolver becomes the integration seam.

**Out of scope.** A central registry of "what overrides what" — the current flat-fall-through shape is structurally simpler. If override interactions get complex, that warrants its own cycle.

---

## Catalogue discipline

This file is the catalogue of future directions for pOS v2. Entries here are not commitments. When an idea is picked up, it becomes a real component cycle (research plan → research → proposal → brief → build → seal) and is retired from this file with a pointer to the component that now owns it. When an idea is deliberately dropped, it is retired with a one-line rationale.

New ideas append to the bottom of the file with a date.

---

*Catalogue maintained alongside STATE.md and BACKLOG.md as the third durable state artifact for the pOS v2 rebuild.*
