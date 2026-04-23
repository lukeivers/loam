# pOS v2 — Future Ideas

Captured 2026-04-21. Ideas recorded for future work — not scoped, not committed to a timeline, not attached to a component. Each lives here until it either becomes a concrete component cycle or is explicitly retired. These are broader strategic directions than the operational items in `BACKLOG.md`.

---

## Core Development Principles — three research lenses

Design lenses now live in `/CLAUDE.md` at the repo root.

---

## Core Development Conventions — temporary parking

> These CDCs are dev-specific machinery that governs how *we* build pOS v2. They don't belong in core pOS v2 docs, but until the Dev/SDLC plugin (Idea 3 below) exists, this file is their temporary home. When the plugin lands, they migrate there.

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

## Core Development Convention — Run all execution work through background agents / subagents

> **All build, commit, edit, test, and probe work in pos-v2 runs through background agents or subagents. The main conversational session is an interactive channel reserved for conversation, reading files for direct answers, memory writes, plan writes, and tool calls that directly answer an owner question. Everything else goes to background. There is no "short work is fine in foreground" carve-out.**

Rationale. The main session between the owner and the primary-persona-layer assistant is an interactive channel. Every tool call issued in the main session blocks that channel until it returns — the owner cannot redirect, interject, or halt the work mid-flight without waiting for the call to complete. Background agents (and subagents dispatched from the main session) do not block the channel: while they run, the owner retains full interactive control and the main session can continue listening, replying, and re-routing. That property is unconditional — it holds for one-second calls and one-hour calls alike — which is why the rule does not admit a "short work is fine" exception. A softening along those lines surfaced and slipped within the same session that established the "plan before code, always" CDC, which is why this companion rule is being codified explicitly rather than left as a preference.

Rule:

- Execution work — building, editing source, running tests, running scripted probes, committing, anything that produces a side-effect on the repo or its environment — dispatches to a background agent or subagent.
- Main session operations that remain in-channel: conversation with the owner, reading files (for direct answers or context assembly), writing memory / preference files, writing plan files, and tool calls whose output is the direct answer the owner just asked for.
- Everything outside that list goes to background. No length-based carve-out; a three-second edit blocks the channel for three seconds that the owner might have needed to redirect.

Relationship to the "plan before code, always" CDC: that CDC's Subagent flow subsection is now the default path, not one option among several. Plans are written in the main session (plan writes are on the main-session allowlist above); execution against those plans happens in background.

Applied immediately to all work from 2026-04-22 forward.

## Core Development Convention — scope-only dispatch to delegated agents

> **A handoff from a session or persona to a delegated agent — subagent, background agent, scheduled worker, another persona — carries only scope material. Scope material is the objective (what must be true at the end), the scope boundaries (what surface the work covers), the constraints (budget, dependency fence, authority bound, reversibility class, forbidden surfaces), the halt triggers, and the shape the acceptance check will take. Method — the files to edit, the symbols to name, the acceptance-criteria prose, the ordered steps of the work, the wording of the commit message — belongs in the receiving agent's plan, not in the dispatching prompt.**

Rationale. This is ODD's delegator/builder split (`docs/odd-methodology.md` §1.1: the delegator authors objective + constraints + acceptance criterion; the builder authors method) applied to the specific surface of session-to-agent handoffs. When a dispatching prompt enumerates files, symbols, acceptance-criteria text, or step structure, the receiving agent's plan collapses into paperwork that documents decisions the dispatch already made — the delegator has silently crossed into the builder's territory, and the plan-before-code discipline produces a plan that verifies nothing that was not already decided elsewhere. The scope-only shape preserves what plan-before-code was set up to deliver: a durable artefact in which the builder commits, in writing, to a method that satisfies the scope *before* any of that method is executed. If scope is well-authored, the builder's plan is the first place method exists; the dispatching prompt never contains it.

The rule is surface-agnostic. It applies to research dispatches, scope-of-work assignments, background monitoring runs, persona handoffs, code builds, doc authoring — every shape of delegated work. The input/output asymmetry is the same in all of them: the sender authors outcome and bound, the receiver authors method.

Authoring the rule scope-only itself. What belongs in a dispatching prompt: objective, scope, constraints, halt triggers, and the shape (not the exact text) of the acceptance check the dispatcher will run. What does not: file paths beyond scope boundaries, symbol names, acceptance-criterion prose, numbered step lists, commit-message wording. This rule deliberately does not prescribe a layout or section ordering for a dispatch prompt — that would be method, and prescribing it would make the rule violate the rule it states.

Companion to the plan-before-code CDC (which established that a plan must exist before code) and the all-work-through-background-agents CDC (which established that execution runs in a delegated agent). The three compose as a chain: plan-before-code says a plan must exist, background-agent-default says execution goes to a delegated agent, scope-only dispatch governs what the handoff to that delegated agent contains. Together they give the primary persona a structural boundary between delegator work (authored in scope) and builder work (authored in the receiving agent's plan).

Applied immediately to all work from 2026-04-22 forward.

## Core Development Convention — setup scripts self-retire on success

> **Work that happens once should leave no code behind that runs every session.** First-run setup completes its job, verifies the outcome, then removes itself — from the filesystem where the script lives, and from the hook registration that invoked it. Subsequent sessions never run first-run code because first-run code is not present to run. Future update-triggered setup ships its own self-removing script; setup logic is not reused session-after-session as check-and-skip scaffolding.

Rationale. Check-and-skip surfaces are an anti-pattern: they accumulate over time (each new setup concern adds another conditional), they add ongoing session-start cost for zero payoff once the one-time job is done, and they turn "is setup complete?" into a live-at-every-session state-machine query that the fourth lens was explicitly trying to retire. Self-retiring setup makes "setup is done" structural — the absence of the script is the proof, not a state flag the script consults.

Applied immediately to true-first-run (Phase 5 second component): the first-run shell script's last act before exit is to (a) write `.claude/settings.json` with the SessionStart hook pointing at the sealed supervisor path, (b) delete itself from the filesystem. Subsequent SessionStart fires invoke the supervisor directly; no first-run surface remains.

Design principle for future components: any setup code should answer the question *"how do I remove myself on success?"* as part of its scope, not as a maintenance afterthought.

## Core Development Convention — research before plan for non-trivial new work

> **When building a new solution (including a bug fix that produces a net-new solution rather than modifying an existing one), if the work is more complex than a very simple task, a research step is required before the plan step.**

Rationale. The existing plan-before-code CDC prevents "dive straight into editing." But for new solutions, the plan itself benefits from prior research — exploring adjacent components, reading authoritative docs, confirming constraints, surveying existing primitives — so the plan doesn't propose something that turns out to be infeasible, redundant with an existing surface, or structurally wrong. Research is not required for: (a) modifying an already-present solution, (b) tasks that are very simple (e.g. a rename, a single-line edit, a trivial deletion of orphaned code). Research IS required for: building a new component, adding a new cross-component surface, implementing a non-trivial feature inside an existing component, writing a non-trivial test harness, refactoring that crosses component boundaries. "Very simple" is a judgement call by the dispatcher; when uncertain, run research. The research step is bounded — produce a research document sized proportionately to the work, not an exhaustive survey.

How to apply. Before drafting the plan document for non-trivial new work, produce a research artifact (a short research doc, a set of findings, a primary-source catalogue) at `docs/rebuild/plans/research/<name>.md` or inline in the plan's §"Research findings" section. The plan then builds on the research rather than inferring from first principles.

Applied immediately to all new-solution work from 2026-04-22 forward.

## Core Development Convention — shutdown-path broad-catch exception

> *A broad catch inside a teardown method (`close()`, `stop()`, `cancel()`, `shutdown()`, `__aexit__`, or semantically-equivalent cleanup) is ODD-legit without per-component acceptance-criterion backing — but the caught exception must be surfaced to observability. When an observability span is in scope at the catch site, use `span.add_event(name, {"exception": type(exc).__name__, ...})`. Otherwise, log at least `logger.debug("teardown_exception", exc_info=True)`. Bare `pass` is insufficient. The teardown must not raise; the exception information must not disappear.*

Rationale. Observability is a first-class primitive in pos-v2 (sealed `observability-aggregator` component; every other sealed component emits span events and OTel signals by design). A teardown that silently discards exception information undermines that primitive — the aggregator has nothing to aggregate, the forensic trail dies at the try-except boundary, and shutdown-path debugging devolves into guesswork. The original CDC 2 (bare `pass` tolerated) was consistent with "shutdown shouldn't cascade" but weaker than pos-v2's observability posture warrants. The tightened form preserves the no-cascade guarantee (broad catch still swallows) while restoring the forensic trail (emission preserves what happened, even if the caller doesn't need to act on it).

How to apply. When writing or reviewing teardown broad-catches, pair the catch with one of two observability emissions: a `span.add_event(...)` call when an already-open span is in scope at the catch site, or a `logger.debug("teardown_exception", exc_info=True)` call when no span is in scope. The emission goes *before* the swallow (pass/return). For `CancelledError` specifically, continue to treat it as expected-flow: catch `asyncio.CancelledError` separately with bare `pass`, catch broader `Exception` with the observability emission. Example pattern:

```python
try:
    await task
except asyncio.CancelledError:
    pass  # expected on cancel
except Exception as exc:
    logger.debug("background_task_stop_exception", exc_info=True)
    # or span.add_event("teardown_failed", {"exception": type(exc).__name__})
```

Applied immediately to: amendment #23 (queued) retrofits the ~44 bucket-(b) teardown broad-catches currently using bare `pass` to the tightened pattern. Going forward, new teardown code must follow the tightened CDC from the start.

## Core Development Convention — audit-finding triage by severity

> **Audit findings where no named acceptance criterion backs the code in question (`AC:none`) are triaged by risk severity rather than treated as uniformly mandatory fixes. Outright silent-except violations (no observable surface, no typed-result conversion, no teardown-path exception per the shutdown-path CDC) are fixed. Patterns recognised as legitimate engineering practice are codified as CDC exceptions (like the shutdown-path CDC). Borderline cases (e.g. missing-file fallbacks) graduate by adding AC backing, promoting to violations, or codifying as accepted.**

Rationale. Strict §2.5 read demands every line of production code map to a named AC. Realistically, some patterns are universal engineering invariants (teardown-path cleanup, structured-error return types, optional-config defaults) that don't require per-component AC authorship and would only be ceremony if required. Pragmatism requires a triage scheme. This CDC records the scheme explicitly so future audits don't re-raise already-resolved patterns, and so the boundary between "fix it" and "codify the exception" has a procedure rather than being re-negotiated per audit.

How to apply. When an audit turns up a finding with `AC:none`, ask:

1. Is this a pattern already codified as a CDC exception? If yes, skip.
2. Is the exception observably surfaced to the caller (typed result, log, event emission)? If yes, likely legit — categorise as exception-to-result conversion, skip.
3. Is this a recognised engineering-universal pattern worth codifying as a new CDC? If yes, propose the CDC first, then skip.
4. Is this a genuine silent swallow with no observable surface? Fix it — promote to a violation, amend.

The amendment that fixes (4) findings can batch them by risk profile (safety-critical paths first, user-visible next, internal/observability third).

Applied immediately to all audit triage from 2026-04-22 forward.

## Core Development Convention — amendment-dispatch test & context scope

> **When dispatching a sealed-component amendment build, (a) scope full test-suite runs to components whose source or tests are actually touched; untouched sealed components get only their `test_no_sealed_amendments.py` (seal-diff check). (b) Skip the pre-seal full-suite rerun; sidecar-only edits in the seal commit cannot break real code, so seal-diff-tests-only is the appropriate post-seal verification. (c) Inline the specific methodology/CDC excerpts relevant to the dispatch in the prompt rather than directing the agent to re-read the full source docs.**

Rationale. Non-trivial amendments were running 25-45 min each. Breakdown: agents re-read methodology docs (~2-3 min), ran full test suite across all 10+ sealed components twice (~4-10 min total), and often repeated reference reads across turns. Each of those is compressible without violating any other CDC. Narrower test scope is still correct because the sealed-component convention's purpose is to prove *the diff window* hasn't drifted — running untouched components' full suites doesn't add signal. Skipping pre-seal rerun is safe because seal commits only touch SEAL_COMMIT sidecars + narrative files, which cannot break code paths. Inlining excerpts preserves the authoritative source reference while trimming the agent's cold-start context read. Combined effect: ~25-40% wall-time reduction on non-trivial amendments, which also narrows the window any single dispatch sits exposed to API overload (CDC below).

How to apply. In every dispatch prompt for a sealed-component amendment build, include the three rules above verbatim as constraints. The agent runs full suites only for components it actually touches; other components get seal-diff tests. The pre-seal test step runs only seal-diff tests, not full suites. Methodology snippets are quoted inline, not referenced by section number. The agent retains authority to read full source docs if it judges necessary for a specific question, but the default is to work from inlined excerpts. These speedups do NOT cut the research step (required by the research-before-plan CDC for non-trivial new work), do NOT cut the plan step, and do NOT violate the scope-only-dispatch CDC — they only shrink the re-read + test-scope phases.

Applied immediately to every future sealed-component amendment dispatch after 2026-04-23. As of amendment #22 (pos-amend CLI + universal-paths retrofit), these dispatch speedups — and the reactive-widening pattern that produced amendment #18's corrective commit `8bdf194` — are mechanically enforced by `pos-amend apply --dry-run`, which must exit 0 before the amendment commit lands. See `tools/pos-amend/README.md`.

## Core Development Convention — 529 overload recovery

> **HTTP 529 "Site is overloaded" returned by Anthropic's API is a global infrastructure signal, not an account-specific rate limit. When a dispatched background agent fails mid-amendment with a 529, the recovery pattern is: (a) verify the canonical tree's state via `git log` and `git status` to see which commits actually landed; (b) if commits landed but the amendment is incomplete, dispatch a small continuation agent scoped to finish the remaining work (e.g. a seal-completion agent that only bumps sidecars and commits); (c) if nothing landed, wait 5-15 minutes and re-dispatch the full amendment. Never `git commit --amend` to reshape the dead agent's commits; always use new corrective commits.**

Rationale. 529s are service-side overload (distinct from 429 per-account rate-limits, 500 Anthropic bugs, 503 maintenance). The SDK retries 529 with exponential backoff but surfaces the error after a few attempts, which kills the agent. Amendment #18 lost ~22 minutes of wall-time this way (2026-04-23). Because the no-amend CDC means every coherent checkpoint is committed before the agent proceeds, the disk state after a 529 is always recoverable — the work that landed stays landed, and the remaining work can be completed by a follow-up scoped agent. This pattern costs time but never costs committed work. Reducing per-dispatch wall-time (CDC above) narrows the 529-exposure window for each amendment; combined with the commit-at-checkpoints discipline, the practical impact of a 529 is bounded.

How to apply. When a background-agent `task-notification` returns with a 529 summary or an API Error message: (1) run `git log --oneline -5` and `git status --short` in the canonical tree to see what landed; (2) classify the interrupted state — amendment committed but no seal, corrective committed but no seal, nothing committed, etc.; (3) dispatch a continuation agent with a tight scope brief that names exactly the remaining step (e.g. "write the seal commit for the 4c385ed amendment and bump the N affected sidecars"); (4) do NOT attempt to re-run the full amendment dispatch — that re-does work, risks divergent commits, and wastes the agent's prior research. If no commits landed at all, wait for overload to clear (usually 5-15 min, often shorter off-peak), then re-dispatch the original amendment unchanged.

Applied immediately to every dispatched amendment going forward, as the standard recovery playbook for service-side interruptions.

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

Every pos-v2 session so far has rediscovered the same design corpus — `odd-methodology.md`, `odd-in-pos.md`, `FUTURE_IDEAS.md`, the proposal and seal notes for whatever component the current work touches — before it can plan or build correctly. The rediscovery cost is paid session after session because loading the relevant context is a social convention, not a mechanical precondition: the author remembers (or fails to remember) to read the design docs before dispatching work. When the author forgets, the work proceeds on incomplete context and the discrepancy surfaces in review, amendment, or audit instead of in the plan. A structural context-load gate removes the social layer: relevant design docs are *required* to be loaded before coding or planning begins, and the gate refuses to advance until they are.

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

## Idea 10 — Project rename to loam

Captured 2026-04-23.

pOS v2 is being renamed to **`loam`** — substrate-not-plant metaphor
that matches the project's actual identity: the enriched medium the
user cultivates their Claude agent in (user-intent = seed,
Claude = genetic machinery, grown agent = plant). The seed framing
already canonical at `docs/rebuild/spec/pos-v2-objectives-spec.md:73`
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

## Catalogue discipline

This file is the catalogue of future directions for pOS v2. Entries here are not commitments. When an idea is picked up, it becomes a real component cycle (research plan → research → proposal → brief → build → seal) and is retired from this file with a pointer to the component that now owns it. When an idea is deliberately dropped, it is retired with a one-line rationale.

New ideas append to the bottom of the file with a date.

---

*Catalogue maintained alongside STATE.md and BACKLOG.md as the third durable state artifact for the pOS v2 rebuild.*
