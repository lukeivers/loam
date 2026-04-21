# Ruthless Review — pOS Objectives (2026-04-17)

**STATUS: v1.0 LOCKED 2026-04-17 16:31 CDT; v1.1 ADDENDUM LANDED 2026-04-18 08:58 CDT; v1.2 ADDENDUM LANDED 2026-04-18 18:44 CDT.** v1.0 text below is preserved unchanged per the lock rule. v1.1 and v1.2 revisions are appended at the bottom. For the effective contract: apply v1.1 and v1.2 deltas to v1.0 as overrides and additions (later addenda supersede earlier ones where they overlap).

**Context:** a rewritten set of pOS objectives was posted with a request for first-principles critique — at least 5 additions and 5 refinements — discarding existing context about what pOS is today. No work to be done yet; this is examination input for the reframe.

**Feedback only — not an implementation plan.**

---

## Overall read

The brief is recognisably ambitious — a harness that compensates for LLM weaknesses whilst remaining approachable to non-technical users, which is a worthy goal and rather a harder one than the document admits. The list is coherent in spirit but uneven in resolution: some objectives (session-resilience, knowledge management) are specified at architect level, whilst others (primary persona, anti-deskilling, communicator) are specified at product-pitch level. That unevenness is the first thing to fix — a spec where some items constrain implementation and others gesture at it produces arbitrary coupling between layers.

## Internal consistency — five tensions worth naming

1. **Non-tech approachable vs strict planning at all levels.** Mandatory planning is well-established friction for non-technical users. The spec currently treats "strict planning" as universal; it should be proportional to scope size.

2. **Anti-deskilling vs auto-creation of skills/workflows.** Auto-creation without exposure is itself a deskilling pattern — the user gets the outcome without understanding it. These two goals need an explicit reconciling principle (auto-create plus auto-explain; never auto-create silently).

3. **"Save everything except extremely ephemeral" vs "recall the right knowledge at the right time."** These are the two hardest halves of knowledge management; lumping them into a single bullet understates the engineering reality. Accrual's failure mode is bloat, privacy leakage, context-window waste. Retrieval's failure mode is wrong-thing-at-wrong-time. They need separate specs with separate acceptance criteria.

4. **Primary persona handles all interactive sessions vs modular plugin system with suggestions.** If the persona suggests plugins, who arbitrates which plugins are appropriate? If plugins can intercept the persona's routing, the boundary gets leaky fast. Requires explicit layering: persona above plugins, or plugins extending persona — one or the other, not both ambiguously.

5. **Deterministic where it makes sense vs modular plugin system.** Plugins imported from elsewhere undermine the determinism guarantee. Either plugins operate within the determinism layer (constraint: expressible as hooks/scripts/rubrics) or they don't (and the harness promises weaker determinism in plugin-augmented contexts). The spec takes no position.

## Structural gaps

The objectives are a flat list, but they belong to three layers that want different treatment: *foundational* (session-resilience, knowledge, determinism, self-correction), *user-facing* (non-tech optimisation, primary persona, anti-deskilling, communicator), and *architectural* (modularity/plugins, objective-based, planning). Mixing them obscures which properties are load-bearing. Reorganise into those three tiers and explicitly name dependencies — non-tech usability *depends on* session-resilience and good communication, which in turn *depend on* knowledge recall and observability. Right now the reader has to reconstruct the dependency graph from prose.

Separately, three load-bearing concepts are named without being defined: **"autonomous scope of work"** (the system's core unit, never specified); **"objective"** (required for larger contexts but not formalised); **"primary persona"** (declared without its boundaries). These definitions should sit at the top of the spec because every other bullet depends on them.

## Significant additions (at least five — offering seven)

1. **Safety and constraint layer as first-class objective.** A harness that enables non-tech users to run autonomous work is a substantial attack and accident surface. Kill switches, spending caps, dangerous-operation gates, and a categorical "these actions always ask the user" list belong in the spec, not as an afterthought.

2. **Cost and resource governance.** Token budgets, compute caps, monthly ceilings per autonomous scope, automatic throttling. Non-tech users are precisely the population most likely to discover cost overruns after the fact. First-class concern, not a minor feature.

3. **Observability, introspection, replay.** "Self-correcting" presupposes observability; you cannot correct what you cannot see. The spec should include: every autonomous action produces an auditable record; the user can replay a session's decisions; the system can answer "why did you do X at time T."

4. **Reversibility as a first-class primitive.** Every action declares its reversibility class (fully reversible, compensatable, irreversible). The system prefers reversible approaches and escalates irreversible ones. Implicit in "self-correction"; should be explicit.

5. **Graceful degradation.** What does pOS do when the underlying model is down, rate-limited, or returning garbage? Session-resilience covers restart; model-layer failure needs its own "safe mode" spec. Non-tech users especially need this — they won't know to pause usage when the upstream is throttling.

6. **Trust and verification.** How does the user come to trust autonomous outcomes? Mechanisms: independent verification by a second persona, test-based acceptance, periodic calibration reports, accuracy metrics surfaced over time. "Self-correcting" is a mechanism; *earned trust* is the outcome.

7. **Explicit non-goals and scope boundaries.** What is pOS deliberately *not* trying to be? Multi-user? Multi-LLM-vendor? A full-featured project manager? Without non-goals, scope expands by accretion and nothing ships.

## Significant refinements (at least five — offering six)

1. **Define "autonomous scope of work" as the system's core object.** Goal, constraints, budget (time/tokens/money), reversibility class, success criteria, observers, escalation triggers. Every other objective references this primitive. Without it, "scopes" means different things in different bullets.

2. **Replace "deterministic where it makes sense" with a tiered determinism model.** Layer 1: hard policy (hooks, scripts) — non-negotiable. Layer 2: deterministic rubrics producing scores the LLM acts on. Layer 3: LLM judgment under layer-1 constraints. Current phrasing treats determinism as preference; treat it as architecture.

3. **Reframe the primary persona from "NL translator" to "trust and coordination layer."** Translation is one function. The persona's real job is being the user's single point of contact, holding ongoing context, judging escalation, and remaining recognisably itself across sessions. Narrowing it to translation misses why non-tech users need it at all.

4. **Replace "strict planning at all levels" with proportional planning.** Mandatory above a threshold, optional below, forbidden for one-offs where overhead exceeds the work. Current phrasing will be ignored in practice; better to specify the threshold honestly.

5. **Anti-deskilling becomes a design principle, not a feature.** Every feature evaluated against "does this reduce the user's capability to understand what was done?" A separate anti-deskilling module patches a gap that should not exist.

6. **Plugin registry becomes plugin trust model.** A registry is the UI; the trust model is the engineering problem. Who signs plugins, what permissions they declare, what sandbox they run in, what happens when a plugin misbehaves. Without this, plugins will be the first serious failure mode.

## One closing thought

The single thing to stress most: the spec talks about *what the system does* far more than *what it measurably produces.* Almost every objective is missing an acceptance criterion. "Optimised for non-tech users" has no measurable test; "accrues knowledge effectively" has none; "excellent communicator" has none. Adding a single testable success criterion to each objective would do more for the brief than any of the additions above, because it forces each bullet to clarify what it actually means.

---

## Addendum — owner feedback (2026-04-17 14:17 CDT)

**On non-goals, pOS as a seed (clarification of earlier "non-goals" addition):**

- pOS itself is explicitly *domain-agnostic.* It is not intended to be aligned with any specific problem domain — not developer-first, not project management, not any other vertical. It is a seed from which users develop their own implementations on top of the core. Domain-specific functionality emerges through user extension, not through pOS itself.
- The "non-goals" proposed should therefore be framed as *"things pOS itself does not commit to,"* not *"things pOS prevents."* pOS enables users to build any of those directions; it just doesn't ship aligned with any of them.
- **Explicit non-goal:** multi-LLM harness. pOS is Claude-only. Any abstraction that anticipates vendor-neutrality is rejected.
- **Explicit non-goal:** alignment with any specific problem domain at the core level (developer-first, PM, ops-first, research-first, etc.). The core is a scaffolding; domain verticals are user implementations built on top.
- This reframes several of the earlier suggestions. "Graceful degradation when the model is down" should assume Claude specifically, not a vendor-neutral fallback. "Trust model for plugins" should consider that plugins may themselves be domain-layer implementations (a dev-first plugin, a PM plugin) rather than horizontal utilities.

**New must-have feature:**

- **Self-upgrade without impacting user configuration.** pOS must be able to upgrade its own framework components (hooks, rules, orchestrator, skills, core tooling) without meaningfully disrupting the user's running configuration — their personas, memory, workflows, projects, plugins, and any workspace-local customisation.
- This is a foundational-layer property sitting alongside session-resilience and graceful degradation. The split of framework vs workspace-specific that exists in the current codebase (pOS-covered vs workspace-specific) is the shape of the solution; this needs to be stated as an objective in the spec, not assumed.
- Acceptance candidates: after an upgrade, the user's active sessions continue without restart; their personas load unchanged; their memory/daily entries are untouched; their workflows and in-flight tasks are preserved; any breaking change to framework contracts is surfaced explicitly with a migration path rather than silently applied.

**Status:** more feedback forthcoming before next document rewrite.

---

## Addendum — acceptance-criteria backfill (2026-04-17 14:19 CDT)

A note flagged that the rewritten list had some bullets without acceptance criteria, and some where the stated criterion was actually about a sub-concern rather than the bullet itself. Three gaps identified and filled below. These will be integrated into the next rewrite.

**Gap 1 — top-level pOS objective had no criterion.**

The statement "an LLM harness designed to work around the core limitations of basic LLMs; optimised for enabling users to define, create, extend, and maintain autonomous scopes of work" was asserted as a goal without a measurable test.

- Acceptance: a newly-onboarded non-technical user can *define*, *create*, and *complete* their first autonomous scope of work within the target onboarding duration without outside help; existing scopes can be *extended* (additional objectives or tasks added) and *maintained* (re-run, revised, re-scoped) without being recreated from scratch. Measured by a representative-user test rather than internal assertion.

**Gap 2 — "Session-resilient" bullet carried a criterion about graceful degradation, not about session-resilience.**

The session-resilience claim itself needs a distinct criterion separate from the graceful-degradation sub-bullet.

- Acceptance for session-resilience proper:
    - Work queued before a session ends completes after session restart without user intervention.
    - Tasks survive system restart (laptop reboot, Claude CLI exit) and resume cleanly.
    - A process killed mid-run either self-heals (restarts) or is marked failed with recoverable state within a bounded window.
    - Compaction events preserve persona identity, active work items, and pending decisions (verified against the compaction-survival list — the list itself is a maintained artifact, not an implicit property).
- Acceptance for graceful degradation (the sub-bullet, unchanged): simulated one-hour Claude outage does not corrupt in-flight scope state; sessions resume cleanly once the upstream returns; user is informed before blast radius exceeds a declared threshold.

**Gap 3 — self-upgrade acceptance was presented as "candidates" plural.**

Firming the list into a single testable statement with each clause independently verifiable:

- Acceptance: after a framework upgrade, *all* of the following hold — (a) any active session continues without restart or re-authentication; (b) all personas load unchanged and pass their compaction-survival checks; (c) memory/daily entries are byte-identical to pre-upgrade; (d) all in-flight tasks are preserved with correct state; (e) any upgrade containing a breaking change to a framework contract surfaces explicitly in the upgrade output with a named migration path, rather than silently applying; (f) the upgrade is itself reversible — the previous framework version can be restored from a preserved snapshot; (g) **every pOS change included in the upgrade is actually installed — none are silently skipped to avoid overwriting user customisations; installation is verifiable post-upgrade via a check that confirms each expected change is in place; when a change cannot be applied due to conflict with user customisation, the conflict is surfaced with explicit resolution options rather than silently dropped.** (Added 2026-04-17 14:29 CDT — prior pOS upgrades had exhibited the "silent skip" anti-pattern, which defeats the point of upgrading.)

**Criteria-audit process (meta) — revised.**

~~Every objective added to the spec must carry exactly one acceptance criterion...~~

The rule as originally stated was wrong. The correct rule: **every *declared behaviour* within an objective must carry its own testable acceptance criterion.** An objective that declares three behaviours and supplies one criterion has tested one-third of its content, not all of it. This is the class surfaced with the knowledge-accrual example; an audit of the full list shows the same pattern in many bullets.

---

## Addendum — behaviour-level acceptance audit (2026-04-17 14:21 CDT)

Auditing each bullet from the rewritten list for behaviour-vs-criterion coverage. Criteria below are *additions* to the existing criteria where coverage was incomplete.

**Core primitives** — three primitives declared but acceptance only tested that each is "defined." Missing: each primitive's internal structure is populated.
- Additional acceptance: scope of work carries all seven declared fields (goal, constraints, budget, reversibility class, success criteria, observers, escalation triggers); objective carries parentage, measurability, time-bound; primary persona carries the three functional responsibilities (single contact, context holder, escalation judge).

**Knowledge accrual** — the original example. Three behaviours (save-non-ephemeral, time-lock, overridable) but only time-lock was tested.
- Additional acceptance: (a) a defined ephemerality rubric decides what is saved vs discarded, and a sampled batch of ephemeral-class data is confirmed absent from storage; (b) superseded knowledge entries carry an explicit supersession marker and a pointer to the superseding entry, and retrieval tests confirm superseded entries are excluded from active context unless explicitly time-scoped.

**Deterministic (tiered)** — three tiers declared plus two negative rules ("never rules where hooks would do"; "never arbitrary where rubric exists"). Acceptance tested only tier declaration.
- Additional acceptance: (a) for any decision currently implemented as a rule/prompt where a deterministic hook/script could produce the same outcome, an audit surfaces it; (b) any arbitrary decision (no rubric cited) surfaces as a lint failure pending rubric definition.

**Self-correcting** — five behaviours (acknowledge, immediate fix, systemic fix, spec update, outcome-vs-objective verification). Acceptance tested systemic-remedy and class-closure only.
- Additional acceptance: (a) every failure record contains an immediate-fix field with a linked remediation; (b) every completed scope runs an outcome-vs-objective check, and check failures are themselves recorded as failures that feed the same correction loop.

**Safety layer** — three behaviours (kill switches, always-ask list, dangerous-operation gates). Acceptance implied but not explicit per behaviour.
- Additional acceptance: (a) kill switches at each declared level (scope, session, system) are independently testable and stop work within a bounded time; (b) the "always ask" list exists as a testable artifact and is enforced at the deterministic layer; (c) a sample irreversible-blast-radius action is blocked at the gate in a test.

**Cost governance** — three behaviours (budgets per scope, ceilings, throttling). Acceptance tested visibility and ceiling enforcement.
- Additional acceptance: (a) every scope declares a budget at creation; missing budget rejects scope creation; (b) throttling activates at a declared threshold below the ceiling and produces a user-facing notification before the ceiling is reached.

**Observability** — three behaviours (auditable record, replay, why-queries). Acceptance tested replay and why-queries.
- Additional acceptance: every autonomous action writes a record containing actor, timestamp, objective cited, inputs, outputs, and tool calls; audit log completeness is verified by a sampled test that reconstructs a given action from its record alone.

**Reversibility** — three behaviours (class declared, reversible preferred, irreversible escalated). Acceptance tested escalation only.
- Additional acceptance: given a choice between two approaches of equivalent outcome where one is reversible and one is not, the system selects the reversible one — verified by a controlled pairwise test case.

**Non-tech users** — four behaviours (low-friction onboarding, persona in every session, auto-create+explain, anti-deskilling principle). Acceptance tested onboarding time and recall.
- Additional acceptance: (a) every interactive session (terminal or desktop) starts with the primary persona present by default — asserted by a session-start test; (b) every auto-created skill/workflow produces an accompanying explanation artifact; silent auto-creation is a lint failure.

**Communicator** — four behaviours (preference learning, bounded adaptation, structure-vs-unstructured judgment, template enforcement). Acceptance tested drift bounds and template compliance.
- Additional acceptance: (a) after N calibration events of a specific preference type, retrieval of a related response reflects the learned preference; (b) structured-vs-unstructured choice is logged per response and reviewable, so judgment quality can be audited.

**Trust and verification** — three behaviours (independent verification, test-based acceptance, calibration reports). Acceptance tested metrics visibility and first-invocation behaviour.
- Additional acceptance: (a) for a defined class of high-stakes outcomes, a second persona produces an independent verification artifact before the outcome is accepted; (b) scopes whose success is test-expressible carry test artifacts that run at completion.

**Objective-based** — three behaviours (required above threshold, hierarchical with parentage, referenced consistently). Acceptance tested parentage/traceability.
- Additional acceptance: alignment is re-checked at every scope boundary and the check is logged; missing check is a process failure flagged by the self-correction loop.

**Plugins** — seven behaviours (registry, suggestions, signing, sandbox, misbehaviour response, determinism declaration, layering). Acceptance tested permissions, quarantine, determinism label.
- Additional acceptance: (a) the registry is browsable and returns signed plugins only; (b) the suggestion engine produces a plugin proposal for a known-solvable request in a test set; (c) the persona-above-plugins layering is enforced — a plugin cannot intercept or override primary-persona routing; violation is a hard failure.

**Pattern noted for the rewrite:** every objective in the next draft will be assembled by (a) listing its declared behaviours explicitly, then (b) writing one acceptance criterion per behaviour. Criteria are co-listed with their behaviour to make the coverage visible rather than inferred.

---

## Addendum — no personas in the pOS core (2026-04-17 15:44 CDT)

Rebuild-proposal decision 5: **pOS core ships zero personas.** The objectives as written do not require built-in personas; therefore they should not be in pOS.

**Restatement of the primary-persona primitive:**

The *primary persona* is defined at the primitive level as a **contract and interface**, not as a specific character or implementation. pOS supplies:
- The contract (what a valid primary persona must implement — the three functional responsibilities: single point of contact, context holder, escalation judge).
- The loader (accepts a workspace-supplied persona, validates it against the contract, fails cleanly if violated).
- The session-integration machinery that binds the loaded persona into every interactive session.

pOS does **not** supply:
- A default primary persona or any other named persona.
- A "fallback" persona for workspaces that don't have one (a workspace without a persona is misconfigured, not serviceable).
- Any persona rosters, prompt content, voice specs, or persona-specific rules.

**Implications across the spec:**

- User-facing layer bullets that say "primary persona present in every interactive session" should be read as "the workspace-supplied primary persona is loaded and present" — pOS enforces the presence and validity, not the content.
- The communication framework (tone-learning, drift bounds, structured templates) is a *capability the framework provides to any persona,* not a quality hard-coded into a specific persona.
- Specialist-persona roster is entirely workspace content. The plugin trust model applies to workspace-authored personas as well as third-party plugins: a workspace persona must declare its contract conformance before being loaded.

**Revised primitive wording for the next rewrite:**

> **Primary persona (primitive):** a contract defining the trust-and-coordination layer that every workspace must supply. A valid primary persona is the single point of contact between user and system, holds ongoing context across sessions, and judges escalation at the authority boundary. pOS supplies the contract, the loader, and the validation; the workspace supplies the persona.
>
> Acceptance (primitive-level):
> - Contract is formally specified; a workspace persona either conforms or is rejected at load time.
> - No pOS-shipped persona content exists in the core repo — enforced by a build-time check that fails on any persona file in pOS paths.
> - A workspace with no primary persona cannot start a session; failure mode is clear and immediate.

---

# v1.1 addendum — memory-system review deltas

**Landed:** 2026-04-18 08:58 CDT.
**Source:** memory-system research v1 + v2 (see `docs/rebuild/components/memory-system/`); all revisions confirmed 2026-04-18.
**Rule:** v1.0 text above is unchanged. The deltas below are the effective contract for the rebuild going forward.

## R1 — U1(c) revised (self-upgrade)

**v1.0 clause (retired):** "(c) memory/daily entries are byte-identical to pre-upgrade."

**v1.1 replacement:** (c) semantic round-trip equivalence — pre-upgrade probe queries produce the same answers when replayed post-upgrade; a drift report measures deviation against a declared threshold for pass/fail. A substrate-level snapshot preserves physical reversibility alongside the semantic test.

## R2 — Accrual behaviour refined (Knowledge accrual)

**v1.1 refinement:** "extremely ephemeral" is a narrow enumerated exclusion set (current-CPU readings, ticking clocks, volatile UI state, and similar transient telemetry), not a general judgment. Everything else is saved — conversations, decisions, research, work, observations. The ephemerality rubric lists what is *excluded*; anything unlisted is accrued.

## R3 — New objective under Knowledge accrual: process-of-arrival capture

* **Process-of-arrival capture**
    * Every background dispatch emits a stream-of-consciousness log during execution.
    * The stream is summarised and ingested into memory alongside the dispatch's output.
    * Memory records the reasoning path, not only the outcome.
    * Acceptance:
        * A representative background dispatch produces a stream log; the log is ingested and summarised into memory; a retrieval query returns both the outcome and the reasoning path when either is queried.
        * A test that submits a known dispatch confirms the full reasoning chain is reconstructible from memory, not only the final output.

## R4 — New cross-cutting objective (Architectural layer): bundled documentation

* **Human-readable documentation bundled alongside every component**
    * Every pOS component ships with human-readable documentation — prose, diagrams, flowcharts, relationship maps.
    * Documentation is bundled with the component, not hosted separately.
    * Documentation covers both how the component works internally and how it relates to adjacent components.
    * Acceptance:
        * No component ships without its bundled documentation; absence is a release-gate failure.
        * A representative non-technical reader can answer "what does this component do and how does it fit with the others" after reading the bundled docs alone.

## R5 — New objective under Knowledge accrual: 4-dimensional temporal model

* **4-dimensional temporal model for knowledge entries**
    * Every knowledge entry carries `valid_at`, `invalid_at`, `created_at`, `updated_at`.
    * Time-lock queries operate on valid-time; audit queries operate on system-time.
    * Acceptance:
        * A query scoped to a valid-time T returns entries whose valid-interval contains T.
        * A query scoped to a system-time T returns entries as the system knew them at T.
        * Both behaviours pass on a controlled test set of entries with staggered valid/system times.

## R6 — Supersession refined (Knowledge accrual)

**v1.1 refinement:** the system infers supersession via LLM-assisted contradiction resolution. Every inferred supersession writes an audit record with the inference rationale and the entries involved. The user can challenge any inferred supersession; challenged supersessions are reversible.

**Acceptance additions:** every supersession event carries an audit record; a user-facing challenge mechanism exists and reversing a supersession restores the superseded entry to active status.

## R7 — New objective under Knowledge retrieval: provenance

* **Provenance of knowledge**
    * Every derived fact points back to the source episode(s) it was derived from.
    * "Why do we believe X?" is a first-class query.
    * Retrieval surfaces sources alongside claims on request.
    * Acceptance:
        * For any derived fact in memory, a provenance query returns the originating source episode(s) without external reconstruction.
        * A fact with missing provenance fails ingestion validation.

## R8 — R1 refined (Knowledge retrieval)

**v1.1 refinement:** retrieval supports multi-hop graph traversal, not only semantic top-k matching. Retrieval walks edges from matched entities to surface related facts.

**Acceptance addition:** a multi-hop test case retrieves a target fact reachable only through graph traversal of two or more edges from the query entity; single-hop-only retrieval fails this test.

## R9 — New objective under Knowledge retrieval: context-aware retrieval

* **Context-aware retrieval**
    * Retrieval can be re-ranked by node-distance from an anchor entity (e.g. the current scope's primary subject).
    * Anchor selection is declared per retrieval call.
    * Anchorless retrieval defaults to query-similarity ranking.
    * Acceptance:
        * With an anchor declared, retrieval prefers entities closer to the anchor over semantically-similar but distant entities; a controlled test with a shared-term ambiguous query returns the anchor-proximate result first.
        * Without an anchor, retrieval ranking degrades gracefully to similarity-only.

## R10 — New objective under Knowledge accrual: per-episode retention class

* **Per-episode retention class**
    * Each ingested episode carries a retention-class tag: `normal`, `derived-only`, or `ephemeral`.
    * `derived-only` persists structured facts extracted from the episode and discards raw text.
    * `ephemeral` allows immediate extraction for context but does not persist.
    * The retention class is set at ingest and is queryable per entry.
    * Acceptance:
        * An episode tagged `derived-only` produces structured facts in memory but no retrievable raw text.
        * An episode tagged `ephemeral` produces no persisted memory beyond its immediate use.
        * A query filtered by retention class returns only entries of that class.

## R11 — Observability primitive refined (Foundational layer — Observability)

**v1.1 refinement:** pOS observability exposes OpenTelemetry as the internal-operation trace format. Components emit OTel spans; downstream consumers (event log, viewer, archive) subscribe to the emission. Framework-wide, not memory-specific.

**Note carried from research annotation A1:** memory emits observability records in OTel format but does not assume a downstream consumer exists. The observability component, when designed, aggregates from component emissions; it is not a prerequisite for any component to ship.

## R12 — Cost governance refined (Foundational layer — Cost and resource governance)

**v1.1 refinement:** token and cost tracking aggregate by prompt-type (prompt name), in addition to per-scope. A user can query "which prompt type costs the most" and tune the top offender.

**Acceptance addition:** per-prompt-type aggregation is queryable; a test workload with varied prompt types confirms attribution is preserved and aggregatable.

## R13 — New objective under User-facing layer: channel-agnostic interaction

* **Channel-agnostic interaction**
    * Primary persona reachable through every Claude-supported channel — terminal, Claude desktop, Telegram, Discord, and any future channel Claude's MCP ecosystem adds.
    * Default channels (terminal, Claude desktop) require no setup.
    * Optional channels are surfaced during onboarding with a walk-through of whatever external setup they need; the user completes setup without leaving onboarding.
    * Primary persona's voice, context-holding, and escalation-judging behaviour are consistent across every enabled channel.
    * Adding a channel that Claude already supports requires no pOS framework change — onboarding surfaces it automatically.
    * Acceptance:
        * Representative non-tech user completes setup of a non-default channel end-to-end through onboarding alone, no external documentation consulted.
        * Channel-consistency test exercises primary persona across at least two channels (terminal plus one external); voice markers and ongoing context are preserved.
        * When Claude introduces a new supported channel, it appears in the onboarding channel list without a pOS framework change — verified by mocking the registry with a novel entry.

---

# v1.2 addendum — primary-persona layer deltas

**Landed:** 2026-04-18 18:44 CDT.
**Source:** primary-persona-layer research + proposal + build (see `docs/rebuild/components/primary-persona-loader/`); all revisions confirmed 2026-04-18 18:43.
**Rule:** v1.0 and v1.1 text above are unchanged. The deltas below are new or overriding clauses under the Primary-persona primitive.

## R14 — Autonomous authoring of specialist personas (new clause under Primary persona)

The primary persona MAY autonomously author new specialist personas when the creation-trigger detector identifies a material gap in the workspace roster. Authoring is gated by: (a) one of five deterministic signals (request declines, domain corrections, cross-domain scopes, low-relevance memory hits, explicit user mentions) crossing a per-workspace-tunable threshold; (b) a judgment LLM call under an explicitly-budgeted scope-of-work returning `yes`; (c) a four-step pipeline (style-harvest, domain-research, contract-synthesis, self-review) that produces a contract passing the primary-persona Pydantic validation by construction, with a ceiling of two self-review retries before the scope terminates with a failure record.

pOS ships the framework; per-signal thresholds, judgment function, and LLM routing are workspace configuration.

**Acceptance:**
- Given synthetic signals crossing threshold, a new persona directory is produced and passes the contract validation;
- Costs are attributed per-prompt via scope-of-work's per-prompt cost view;
- Synthesis failure after two retries records an `authoring_rejected` event and the directory is not persisted.

## R15 — Mandatory introduction before addressability (new clause under Primary persona)

Every autonomously-authored persona is persisted with `pending_introduction: true` and `is_addressable: false`. No message identifying that persona as sender may be delivered until the user has been explicitly introduced — an introduction is a structured message (new persona's name, domain, trigger that caused authoring, retire instructions) dispatched **only** to the user's current one-on-one channel (terminal, Claude desktop, or the user's personal Telegram thread). Group-channel introductions are forbidden at every layer: the channel type rejects `is_group=True`, the dispatcher rejects group channels at construction, and no framework override exists.

If zero one-on-one channels are reachable, the introduction queues and fires when a channel activates. `is_addressable` flips True only on the user's next non-retire message; a retire instruction moves the persona to `_retired/<handle>-<timestamp>/` without ever flipping the flag.

**Acceptance:**
- An integration test verifies no message identifying the new persona as sender can be delivered while `is_addressable` is `false`;
- A construction-time test verifies a group-channel dispatcher cannot be instantiated.

## R16 — Framework-not-content (strengthens the existing no-personas-in-core clause)

pOS core ships the persona contract, loader, validator, background-work monitor, compaction-survival mechanism, creation-trigger detector, authoring pipeline, introduction protocol, and retirement machinery — the **framework** for handling personas. pOS core ships **no** persona content: no `contract.yaml`, no `prompt.md`, no persona directory, no named identity (no default primary persona, no fallback persona).

Enforcement is build-time: the loader's framework-tree scan raises `PersonaInCoreError` on any `contract.yaml` inside a pOS-core path; a workspace without a valid primary persona directory cannot start a session. Template directories in pOS core are permitted only with the reserved placeholder handle `example-persona`.

**Acceptance:**
- A build-time check fails if any non-template persona directory is found inside pOS-core paths;
- A failing-session test when a workspace is missing `personas/` or contains only `_retired/*`.
