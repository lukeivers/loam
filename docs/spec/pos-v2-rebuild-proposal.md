# pOS — Gap Analysis and Forward Plan

**Date:** 2026-04-17. **Status:** APPROVED 2026-04-17 15:44 CDT — all five decisions answered.

## Rulings recorded (2026-04-17 15:44 CDT)

1. **Rebuild parallel — confirmed.**
2. **New branch on existing repo, not a new repo.** Burn everything down in that branch and start from scratch on it. Preserves revert-ability via the untouched main branch.
3. **Current pOS in maintenance mode — confirmed.** Bug fixes only, no new features.
4. **Timelines are fiction.** Work proceeds when attention allows; phases have acceptance gates, not calendar dates. The 16-week shape in the original plan is struck from the record.
5. **No personas in the new pOS core at all.** The objectives don't require built-in personas; pOS provides the *primary-persona primitive* (the interface and contract), workspaces supply their own implementations. All workspace personas are workspace content and live in the workspace, never in pOS.

Decision 5 reshapes the phase plan — see the revision below. Phases are now gate-based, not week-based.

## Rulings recorded (2026-04-17 15:51 CDT)

6. **Migration approach changed.** Once the new pOS baseline exists, the owner starts with a fresh greenfield workspace rather than migrating the existing workspace into new pOS. Individual artifacts (personas, memory entries, workflows) from the existing workspace get pulled in one at a time, only as a concrete need arises. This replaces the "migrate at cutover" plan. The goal is the authentic, fresh pOS experience.
7. **Memory system is the non-negotiable.** Flagged with uncommon emphasis — four "really"s. The memory system must be exceptionally well-implemented, above everything else. It warrants its own dedicated phase with extra research and proposal rigour.
8. **Dogfood the new pOS principles whilst building the new pOS.** Plan-before-execute, proportional planning, objective-based work, tiered determinism — all apply to the build process itself. The build is the first real test of the principles.
9. **Every major component requires a full research-and-proposal session, approved by the owner, before work starts.** No component is worked on that isn't aligned with an approved proposal.
10. **Every task/workflow handoff brief is reviewed by the owner before dispatch.** The primary persona has a tendency to be overspecific; the owner's review is the correction. No handoff to any specialist without the owner's review of the brief first.

**The governing rule, owner's words:** *"NOTHING is worked unless I have seen what it is being worked against before work starts."*

## Ruling recorded (2026-04-18 09:18 CDT)

**Implementation language: Python, not Ruby.** The original workspace default is Ruby; prior pOS is Ruby. The **new pOS is built in Python**. Reasoning: Python is the native language of the AI ecosystem — most libraries, including Graphiti itself (the memory system's recommended engine), are Python-native. Building in Python removes an entire class of integration pain (Python-to-Ruby async wrappers, language-boundary serialisation) and aligns pOS with the ecosystem it lives in.

This decision supersedes the Ruby default *for the new pOS only.* Prior pOS / the existing workspace continues in Ruby under maintenance mode. Standards files for the new pOS will be Python-first (pyproject.toml, ruff/black/mypy conventions) and authored fresh as part of Phase 0.

## Rulings recorded (2026-04-17 16:15 CDT)

11. **No on-the-fly deviation from approved proposals.** The executor (whoever the brief is handed to) may not make decisions during execution that disagree with the approved proposal. If at any point the executor concludes deviation is required, they halt immediately and emit a clear failure signal (named error state, recorded to event log, surfaced to the primary persona) indicating that execution has stopped and why. The primary persona picks up the signal, reviews with the owner, and the proposal is adjusted. Execution then resumes against the revised proposal. Tight boundaries, absolute — what is wanted, and nothing else.

12. **Testing methodology: Objective-Driven Design (ODD).** A deliberate offshoot of Behaviour-Driven Design. Specs are written against the *objectives* the system must deliver, not against the *behaviours* it exhibits. Objectives decompose hierarchically into child, grandchild, etc., to keep any individual test's scope small — every child objective traces back to a parent objective up to a top-level one. Framing: the concern is not whether the thing behaves a specific way; the concern is whether it delivers a specific objective.

    **Negative-case handling (the ODD principle that distinguishes it from BDD):** negative cases do not live as exception branches inside positive tests. When a negative case is identified, it is *re-extended back up the chain* as a new positive objective — a sibling, parent, or new tree — which is then decomposed and tested on its own terms. The negative concern becomes a positive objective the system must deliver.

**Companion docs:**
- New definition and acceptance criteria: `docs/spec/loam-objectives-spec.md`

---

## TL;DR — recommendation

Build a **new pOS core in parallel** with the existing one. Not an incremental refactor. Not a rip-and-replace. A greenfield rebuild running alongside current pOS, delivered in phases with explicit acceptance tests, and a scheduled cutover once the new core reaches capability parity. Current pOS stays operational for ongoing workspace work throughout.

**Reasoning in one paragraph:** the new definition is different enough from what exists that retrofit costs likely exceed rebuild costs. The accumulated sediment in current pOS — rule layers designed against earlier specs, primitives that don't match the new model, workspace-specific content entangled with framework code — is exactly the class of problem a rebuild solves. Quality was observed to decline after the framework/workspace split; a rebuild in the shape of the new definition resets that sediment cleanly without putting ongoing work at risk.

---

## Gap analysis

Marked by severity: ✓ aligned · ◐ partial · ✗ gap.

### Core primitives
- ✗ **Autonomous scope of work.** Not a defined primitive in current pOS. Tasks, workflows, and jobs exist but carry no budget, no reversibility class, no observer list, no escalation triggers. Retrofit means threading seven new fields through every major code path that touches a task or workflow.
- ◐ **Objective.** Workflows carry objectives; standalone tasks often do not. Hierarchy exists in intent but is not universally enforced. Testable criteria are inconsistent.
- ◐ **Primary persona.** The primary persona exists and coordinates. The "trust and coordination layer" framing is authored in the spec but implemented more as a router — cross-session context is held advisorily, not structurally.

### Foundational layer
- ◐ **Session-resilience.** Orchestrator runs separately; cron/launchd exist; compaction-survival lists are authored. Self-healing when a dispatcher process wedges is advisory — recently-observed wedged stop-guard processes were a case in point.
- ✗ **Graceful degradation.** No defined behaviour for Claude API outage, rate-limiting, or garbage responses. No safe-mode construct.
- ◐ **Self-upgrade.** `bin/upgrade-pos` works. The silent-skip anti-pattern identified is evidence the current implementation can misbehave. Post-upgrade verification of applied changes is absent.
- ◐ **Knowledge accrual.** Memory system exists (daily files, weekly synthesis, entity memory). Time-locking is partial — earlier states are readable via dated entries but not formalised. Supersession markers are not standard. Ephemerality rubric is not defined.
- ◐ **Knowledge retrieval.** Retrieval happens via context injection and search. Precision/recall is not measured. Retrieval cost per query is not bounded.
- ◐ **Tiered determinism.** Hooks and rules exist. The Layer 1/2/3 classification is implicit. No mechanical audit surfaces "rule/prompt where a hook would work" or "arbitrary decision without a rubric."
- ◐ **Self-correction.** Four-part correction is in the prime directive. Enforcement is advisory — corrections frequently stop at "noted for next time," which is the primary failure mode this rebuild aims to close.
- ◐ **Safety.** Tier A–D distinctions exist. Kill switches at scope/session/system level are not uniformly implemented. "Always ask" list is de facto, not a single canonical artifact.
- ✗ **Cost governance.** Not implemented. No per-scope budgets, no ceilings, no throttling, no user-facing spend visibility.
- ◐ **Observability and replay.** Event log exists. Replay is not first-class. "Why did you do X at time T" queries require manual forensics.
- ✗ **Reversibility as primitive.** Not implemented. Actions don't declare a reversibility class; reversible-preferred selection is not structural.

### User-facing layer
- ◐ **Non-tech optimisation.** Current pOS assumes considerable technical comfort — YAML editing, file-system awareness, rule-file authoring. A representative non-technical user would not pass the onboarding acceptance criterion.
- ◐ **Anti-deskilling.** Exists as a rules module. Not yet applied as a design principle at every feature's approval gate.
- ◐ **Communication.** Persona voice specs exist. Tone-drift tests and template enforcement are not present. The "surface blind spots" rule is authored but not mechanically enforced.
- ◐ **Trust and verification.** Second-persona review happens in the SDLC pipeline. Calibration reports with accuracy/success metrics are not surfaced to the user.

### Architectural layer
- ◐ **Objective-based at every level.** Workflows are objective-based. Standalone tasks often are not. Threshold detection is informal.
- ◐ **Proportional planning.** SDLC enforces planning for products. The threshold below which planning is optional or forbidden is not defined.
- ✗ **Plugin trust model.** Skills and modules exist. Signed plugins, sandbox execution, misbehaviour quarantine, determinism-tier declaration — none in place.

### Non-goals alignment
- ✓ **Claude-only.** Already aligned. No vendor-neutral abstractions in the current code.
- ◐ **Domain-agnostic.** Current pOS framework is conceptually domain-agnostic but the workspace conflates framework with workspace-specific personas. The boundary is documented but not mechanically enforced.

### Structural observations
- Rule layer overlap: many rules cross-reference; would itself need a classification audit to promote each rule to the right tier (hook/script, rubric, advisory).
- Framework-vs-workspace boundary: documented in CLAUDE.md but not build-time enforced. A mistaken write to a framework path is caught only by discipline.
- Orchestrator maturity: the current orchestrator is well-tested for its current scope but was built against a different primitive model (tasks/workflows, not scopes-of-work).

**Severity summary:**
- 5 gaps (✗): autonomous scope primitive, graceful degradation, cost governance, reversibility, plugin trust model.
- ~12 partials (◐): most foundational and user-facing items.
- 1 alignment (✓): Claude-only.

This is the shape of "substantially different, not merely incomplete." The case for rebuild follows.

---

## Rebuild vs refactor — the trade-off, honestly

### Arguments for rebuild
1. **The scope-of-work primitive is missing.** Threading it through existing code means touching tasks, workflows, dispatcher, hooks, personas, orchestrator — effectively every major component.
2. **The rule layer needs audit-level rework.** Classifying every rule into the tiered determinism model and either promoting it (to a hook/script) or demoting it (to an advisory) is itself a rebuild of the rule layer.
3. **Sediment from before the workspace split.** Accumulated decisions made against earlier specs.
4. **Conceptual cleanliness.** Every component built against the current spec rather than retrofitted. Fewer "this was designed for X but now it has to do Y" compromises.
5. **Domain-agnostic boundary is easier to enforce in greenfield.** Start with a Claude-only, domain-agnostic core; add workspace extensions on top. Hard to retrofit.

### Arguments against rebuild (for refactor)
1. **Time cost.** Weeks of work. Real risk to ongoing workspace progress if not contained.
2. **Migration complexity.** Existing memory, personas, workflows, tasks need to move across at cutover.
3. **Lost institutional lessons.** Current pOS encodes many hard-won learnings. The spec captures most; some are surely implicit in code.

### Weighting
Rebuild wins *if* it runs in parallel without halting workspace work on the current system. It loses if the rebuild forces day-to-day to pause. The plan below is structured precisely to prevent that.

---

## Proposed approach — parallel rebuild with scheduled cutover

1. **Current pOS stays primary throughout the rebuild.** Workspace work continues on it without interruption. Current pOS enters maintenance mode — bug fixes only, no new features.
2. **New pOS is built greenfield in a separate repository.** Does not modify current pOS code.
3. **Each phase ships a working increment with explicit acceptance tests.** The new pOS gains capabilities phase by phase; each phase is independently validatable.
4. **Capability-parity milestone.** At a defined checkpoint, the new pOS can do everything the current pOS does that is actively used. This is when cutover becomes feasible.
5. **Cutover is scheduled, rehearsed, and reversible.** Migration of memory, personas, workflows is a designed operation. A snapshot of current pOS is preserved so cutover can be rolled back.

---

## Phase plan (revised 2026-04-17 15:51)

Phases are **gate-based**, not time-based. Each phase completes when its acceptance gate passes. No calendar pacing — work proceeds when attention allows. A phase that takes two sessions is fine; one that takes two months is also fine.

**Core principle revised per decision 5:** pOS core ships *no personas at all.* It ships the primary-persona primitive (contract + validation + interface), and the infrastructure to load and verify user-supplied personas. Every phase below assumes zero persona content in pOS itself.

**Per-phase workflow — the approval chain (decisions 8, 9, 10):**

Every phase follows the same five-gate chain. No gate is skipped.

1. **Research plan.** The primary persona authors a research plan for the phase — what must be figured out, what questions must be answered, what options must be evaluated. Sent for approval. Approved before research begins.
2. **Research document.** Research conducted per the approved plan. Findings written up. Sent for awareness (not a gate — this is an intermediate artifact).
3. **Proposal.** The primary persona authors a proposal drawing from the research — what gets built, how it fits the objectives spec, alternatives rejected and why, acceptance criteria for the phase. Sent for approval. **Approved before any build work is briefed.**
4. **Handoff brief.** The primary persona drafts the brief for the builder (whichever role the work calls for). Objective stated, constraints listed (with inferences marked), acceptance criterion co-listed. No prescribed flags, file paths, function names, or step-by-step execution plans. Sent for **review** before dispatch.
5. **Dispatch.** Only after the brief has been reviewed does work start.

The chain is non-negotiable. Execute-then-inform is suspended for this work stream. For the pOS rebuild, the primary persona operates in propose-then-wait mode, not act-then-inform mode.

### Phase 0 — spec lockdown
Before any code. Finalise the objectives spec. Complete the non-goals list. Define the scope-of-work schema formally. Define the objective schema formally. Define the primary-persona contract (what a valid persona must implement, not any specific persona). Write the first acceptance test for each core primitive in a language-agnostic form.
**Gate:** a spec document a developer could implement against without needing to ask clarifying questions for a week.

### Phase 1 — core primitives runtime
Build the scope-of-work runtime (create, validate, persist, lifecycle). Build the objective tracker (parentage, traceability, criterion registration). Build the primary-persona loader — loads a user-supplied persona, validates it against the contract, fails if it doesn't conform. **Build the background-work monitor** — subscribes to scope-of-work's emission and query surface; keeps the primary persona aware of active, stuck, finished, and needs-review background work at all times. Designed alongside the persona loader since the persona is what it feeds. Principle recorded 2026-04-18 13:51: *an interactive session must never lose awareness of active background work and let the system go fallow.*
**Gate:** any scope can be declared; any objective registered with traceability to a parent; a workspace-supplied persona can be loaded and validated; the persona is continuously aware of in-flight background work via the monitor.

### Phase 2 — memory system (elevated per decision 7)
The most emphatic requirement: the memory system must be exceptionally well-implemented. It therefore gets its own phase with the deepest research-and-proposal rigour of the whole build. Separated out from the rest of foundational infrastructure so it is not rushed alongside orchestration and observability.

Scope: knowledge accrual (with time-locking, supersession, ephemerality rubric), knowledge retrieval (with precision/recall and cost bounds), the query interface, the time-travel mechanism for decision archaeology, and integration with the observability layer so replay can reconstruct the knowledge state available at any past moment.
**Gate:** given any decision made at time T, the system reproduces the knowledge state available at T; retrieval hits stated precision/recall targets on a test set; retrieval cost per query stays within a stated budget; superseded entries are excluded from active context unless time-scoped; ephemeral-class data is verified absent from storage.

### Phase 3 — remaining foundational infrastructure
Session-resilient orchestrator (separate process, self-healing, compaction-aware). Event log and observability (every action audited, replay-capable). Graceful degradation (safe mode when Claude is down/rate-limited/garbling). Self-upgrade (with the seven-clause acceptance, including no-silent-skip).
**Gate:** scopes run across session restarts; past sessions are replayable; upstream outage does not corrupt in-flight state; upgrades install verifiably and surface conflicts rather than skipping them.

### Phase 4 — safety, cost, reversibility, self-correction
Safety layer (kill switches at scope/session/system, always-ask list, irreversible gates). Cost governance (budgets, ceilings, throttling, visibility). Reversibility primitive (class declaration, preference enforcement, escalation). Self-correction loop (structural four-part, not advisory).
**Gate:** a scope cannot run without a budget; kill switches stop work in bounded time; irreversible actions escalate; correction events update specs/rules mechanically.

### Phase 5 — tiered determinism
Formalise Layer 1/2/3. Rule-to-hook promotion audit. Rubric-or-lint-failure enforcement. Self-correction loop wired to close classes by updating rules/specs.
**Gate:** every decision class is tiered; rule promotion happens mechanically; arbitrary decisions lint-fail.

### Phase 6 — user-facing layer
Non-technical onboarding flow (the framework of it — not any workspace's specific onboarding). Communication framework (tone-learning contract, drift bounds, structured-output templates, blind-spot enforcement). Trust and verification (independent-review primitive, calibration reports).
**Gate:** the framework supports the non-tech onboarding acceptance test (a representative user can onboard to first scope within target time against a test workspace); drift and template tests pass; calibration reports render.
*Note: the onboarding flow is exercised against a test workspace supplying a test persona. pOS itself still ships no personas.*

### Phase 7 — plugin system
Registry with signing. Sandbox execution. Misbehaviour quarantine. Determinism-tier declaration. Suggestion engine. Persona-above-plugins layering enforcement.
**Gate:** a signed plugin can be browsed, installed, sandboxed, and quarantined on misbehaviour; a plugin attempting to intercept persona routing hard-fails.

### Phase 8 — greenfield-workspace cutover (revised per decision 6)
No migration of existing-workspace content into the new pOS. Instead: when the new pOS reaches the capability-parity gate, a fresh greenfield workspace is opened on top of it — no personas pre-loaded, no memory pre-seeded, no workflows pre-created. The authentic fresh-pOS experience.

Individual artifacts from the current workspace (specific personas, specific memory entries, specific workflows) are pulled across one at a time, only as a concrete need is encountered. Import is a targeted, user-initiated action, not a batch migration.

The existing workspace continues to run on current pOS indefinitely — per-artifact decisions determine whether something needs to exist in the new world or whether it stays where it is.
**Gate:** a fresh workspace is running on new pOS; the targeted-import mechanism works end-to-end on at least one real artifact pulled from the existing workspace; current pOS is not retired until explicitly decommissioned.

---

## Immediate next steps

1. **Finish the objectives spec.** Feedback still being added. Lock when satisfied. This is the contract the new pOS is built against.
2. **Decide the repo structure.** A new repo or a fresh top-level directory. Recommendation: new repo — clean separation is itself part of the rebuild hypothesis.
3. **Brief the builders.** The harness architect owns the design handoff from spec to implementation. Implementation executes. Primary persona coordinates and owns the outcome. Analogous to how products currently get built under SDLC, so the motion is familiar.
4. **Weekly checkpoint.** At the end of each phase, brief review — what shipped, what didn't, what this phase revealed that changes the plan for the next. Keeps sediment from accumulating on the new build.

---

## Decisions needed

These sit at founder-authority — committing time and focus for several weeks, so they warrant a clear yes.

1. **Rebuild vs refactor — confirm.** Recommendation is rebuild parallel. Initial instinct was rebuild. An explicit yes/no is wanted.
2. **New repo vs new directory.** Mild preference for new repo; owner decides.
3. **Current pOS in maintenance mode — accepted?** No new features to current pOS during the rebuild. Bug fixes only. This is a real discipline commitment; if new pOS features are wanted during the build, reshape now.
4. **Timeline sanity check.** The 16-week indicative shape: acceptable, or tighter/looser phasing?
5. **Workspace personas during transition.** All existing clusters continue to run on current pOS until cutover. Confirmed acceptable?

Once these five are answered, Phase 0 is briefed and work begins.
