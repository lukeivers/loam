# ODD — LLM grounding derivation

> **RETRACTION + ARCHIVE NOTE (2026-06-10).** This document is archived,
> not live doctrine. Its §1 claim that "ODD is genuinely new" / "not in my
> training data" is **retracted** per the owner-ratified
> methodology-synthesis verdict (2026-06-10, Discord 1514360242): ODD
> descends from named ancestors — KAOS goal-oriented requirements
> engineering, Ulwick's Outcome-Driven Innovation, Adzic's Specification by
> Example, Meyer's Design by Contract — and is honestly repositioned as
> ATDD + goal-reverse-engineering + a strict reverse-coverage rule +
> evidence banding, tuned for LLM delegation. The load-bearing material
> here (the §6 altitude tests, §7 drift modes, §8 self-checks) was promoted
> into the live spec at `plugins/dev-sdlc/docs/odd-methodology.md` §9; the
> load-first form lives in `docs/odd-llm-grounding.lean.md`. The §5
> derivation chain is retired with the novelty claim. Kept verbatim below
> for the audit trail.

**Authored:** 2026-05-05 by main session, per Luke directive.
**Audience:** the LLM agent (or future agent) about to do ODD work.
**Status:** load deliberately into context BEFORE ODD-shaped tasks (extraction, ratification, gap-analysis, plan-authoring, AC-tightening). Read this whole file first; then proceed to the task with the altitude tests at §7 active in working memory.
**Primary failure mode this prevents:** mistaking implementation facts for objectives. The v0.1.8 odd-extractor shipped this exact failure mode — the document at the end (§9) is the case study.

---

## §1 — Why this doc exists

Luke (the human) and I (the agent) have been building loam, a Claude-attached harness whose authoring methodology is **ODD — Objective-Driven Design**. ODD is genuinely new. It was not in my training data. There is no Wikipedia page, no Bertrand Meyer book, no Hacker News thread that named "Objective-Driven Design" as a discipline before this project named it.

Because ODD is new, my default reasoning about ODD-shaped tasks reaches for the closest things in training data — BDD, TDD, ATDD, DDD, design-by-contract, user stories, requirements engineering — and produces output at the altitude those adjacent concepts operate at. That altitude is wrong for ODD often enough that it has caused a shipped-feature defect: the v0.1.8 odd-extractor labels its outputs "AC" but extracts implementation facts (Express route exists at file:line), not objectives (operators can file refund disputes against merchant portals).

This document exists so the agent can deliberately bridge from training-data-built-in concepts to ODD-as-defined-by-this-project before doing ODD work. Once the bridge is loaded, the altitude tests (§7) become reflexive.

---

## §2 — The diagnosis (what goes wrong without this grounding)

Without this grounding, the agent's failure mode on ODD-shaped tasks looks like this:

1. Asked to "extract objectives from a codebase."
2. Reaches for closest-relative concepts — TDD acceptance criteria, BDD Gherkin scenarios, design-by-contract preconditions/postconditions, user stories.
3. None of those concepts have a clean shape for "extract from existing code that wasn't authored under that methodology" — they're greenfield-authoring concepts.
4. Defaults to the nearest tractable thing the agent CAN do: walk the codebase via tree-sitter, enumerate symbols, label each symbol an "AC."
5. Produces output that's symbol-level structural inventory, mis-labeled as ACs.
6. Does NOT notice the altitude error because "AC" isn't a load-bearing term in the agent's training (it's frequently used loosely).

The v0.1.8 odd-extractor's 131 outputs on rd-automation are exhibit A. "Express route GET /all-orders" is correctly extracted as a fact — the code DOES contain that route. But that's an implementation fact, not an objective. The OBJECTIVE the route serves is something like "operators can list refunded orders by period for review and prioritization" — that's the outcome; the route is one way to deliver it.

The agent shipped 131 of these mis-altitude facts and labeled them "ACs" because nothing in training data flagged the altitude error. That's the failure mode this doc prevents.

---

## §3 — Concepts in training data — what's adjacent

For each adjacent concept, what's similar to ODD + what's different.

### BDD — Behavior-Driven Development

**What's similar:** outcome-orientation. Gherkin scenarios (Given / When / Then) are written from the perspective of "what happens when the user does X" — that's objective-shaped. The scenario text is closer to an objective than most code-level constructs are.

**What's different:** BDD scenarios are typically authored before implementation, as test specs. They're greenfield. ODD assumes both greenfield AND brownfield (existing code with implicit objectives). ODD also has banding (V/P/H) — BDD scenarios are binary pass/fail. ODD requires §2.5 strict mapping; BDD scenarios can leave swaths of code uncovered by design (e.g., infrastructure bootstrap).

**Transferable insight:** test names in BDD-style codebases are often closer to objectives than the surrounding code. When extracting from a real codebase, prioritize test names + assertions over symbol inventory.

### TDD — Test-Driven Development

**What's similar:** write the test first (the spec); make it pass. Test-as-spec is closer to objective than implementation.

**What's different:** TDD is fine-grained — a test typically asserts one branch / one return value / one exception. Objectives are coarser-grained — they describe outcomes the system delivers, often spanning many tests. TDD has no banding.

**Transferable insight:** unit tests in TDD codebases are mostly implementation-detail-shaped (asserting specific function behavior); integration / acceptance tests are closer to objectives. Prefer the latter for objective extraction.

### ATDD — Acceptance Test-Driven Development

**What's similar:** named acceptance criteria authored before implementation; implementation must satisfy. The "AC" terminology comes from here. Closest single ancestor of ODD's AC concept.

**What's different:** ATDD is greenfield-only in practice. ATDD ACs are usually binary. ATDD doesn't have the strict §2.5 mapping (orphan code is allowed). ATDD doesn't address the LLM-as-builder context.

**Transferable insight:** ATDD's AC vocabulary is the closest term-of-art match to ODD's. When the doc says "AC," map it to ATDD's notion + tighten with ODD's banding + strict mapping.

### Design by Contract — Bertrand Meyer

**What's similar:** preconditions / postconditions / invariants are constraint-shaped statements about what the system guarantees. Constraint extraction is part of ODD.

**What's different:** DbC operates at function/method level (what does THIS function guarantee). Objectives operate at system level (what does the system as a whole deliver). Different altitudes.

**Transferable insight:** for constraint extraction, DbC vocabulary is useful — "the system guarantees X under condition Y" is constraint-shaped.

### User stories — Cohn / Agile shape

**What's similar:** "As X, I want Y, so that Z." That's objective-shaped — names the actor, the desired outcome, the value rationale.

**What's different:** user stories are typically backlog items (work to do), not extracted facts about an existing system. They're authored, not derived.

**Transferable insight:** the user-story TEMPLATE is a useful objective shape. When stating an objective from extracted code, the "as X, I want Y, so that Z" frame produces well-shaped statements.

### Domain-Driven Design — Evans

**What's similar:** ubiquitous language, bounded contexts. DDD distinguishes domain language (what the business does) from technical language (how the code works). That's the objective-vs-implementation altitude distinction.

**What's different:** DDD is architectural. Objectives are coarser still — they're outcomes, not domain entities or contexts.

**Transferable insight:** when extracting objectives, look for the codebase's domain language (model class names, route path segments, README terminology). Domain language carries objective-shape signal.

### Requirements engineering — IEEE 830 / waterfall heritage

**What's similar:** formal specifications; functional vs non-functional requirements; the spec is the contract.

**What's different:** RE is heavyweight, document-first, often divorced from code. ODD is code-adjacent — every objective ladders to backing code paths. RE doesn't have banding.

**Transferable insight:** functional vs non-functional distinction maps usefully to ODD's objective vs constraint distinction.

### Feature-Driven Development / feature-toggle-driven

**What's similar:** features as units of value. A feature is closer to a capability than an objective.

**What's different:** features are NOT objectives. A feature is a thing the system has; an objective is an outcome the system delivers. Many features can serve one objective; one feature can serve many objectives. The mapping is many-to-many, not 1:1.

**Transferable insight:** when extracting, feature inventories produce capability-shaped output, not objective-shaped. The next step up (what outcome do these features serve?) is the objective.

---

## §4 — What's specifically new in ODD

These are the load-bearing distinctions that make ODD different from the adjacent concepts.

### 4.1 — §2.5 strict mapping (no orphan code)

Every line of code, every branch, every test maps to a NAMED acceptance criterion that ladders to a named objective. No defensive code for unnamed cases. No "in case we need this later" branches. No orphan utility functions.

This is stricter than any adjacent methodology. BDD allows uncovered code. TDD doesn't enforce coverage at the line level. ATDD is silent on orphan code. Only ODD says: if there's no named AC, the code shouldn't exist.

The reverse-direction implication for extraction: if the codebase has orphan code (which most real codebases do), the extractor must surface that as a finding (orphan inventory) — not invent objectives to retroactively cover it.

### 4.2 — Banding (V / P / H — confidence-graded, not binary)

Acceptance criteria carry a confidence band:

- **VERIFIED** — there's direct evidence the system delivers this outcome. Usually means a test asserts it, or the AC text is in the codebase verbatim (a spec doc, a code comment, etc.).
- **PLAUSIBLE** — there's structural evidence consistent with this outcome (a route exists; a function with an indicative name; a class structured the right way). Could be true; not directly verified.
- **HYPOTHESISED** — pattern-based inference. The code shape + nearby code suggest the outcome, but there's no direct evidence.

Banding is novel. No adjacent methodology has it. The point: ODD acknowledges that extraction from existing code produces a confidence gradient, not a yes/no answer. The user (or persona) ratifies P → V or H → P / V via review.

### 4.3 — Method-is-builder's-call

ODD names the WHAT (objective + constraints + acceptance criteria). The HOW (specific implementation, file layout, library choice, test fixture shape) stays loose — the builder's call within constraints. ODD authoring discipline is "tight scope, loose method": objectives + ACs pin the outcome; method is inferable from constraints, not stated.

This distinguishes ODD from RE-shape methodologies that prescribe HOW (specific tooling, specific file layouts). It also distinguishes ODD from DDD (which prescribes architectural shape).

### 4.4 — Reverse-engineering as a first-class case (ODD-RE)

Most adjacent methodologies are greenfield-authoring-only. ODD names "extract an ODD from an existing codebase" as a first-class workflow. That's what the v0.1.8 extractor was supposed to do (and got the altitude wrong on).

ODD-RE has its own discipline: the extractor must produce objective-shaped output, not implementation-shaped. Banding allows the extractor to surface uncertainty rather than fabricate. The user ratifies. Backing-code maps make objectives traceable to implementation.

### 4.5 — LLM-as-builder context

ODD was designed knowing the builder is often an LLM agent. That means:

- Objectives must be statable in natural language (the LLM reads them; renders against them).
- ACs must be observable (the LLM can verify them by reading code or running tests).
- Method-is-builder's-call honors the LLM's strengths (synthesis, pattern-matching, code generation) without locking it into a specific approach.
- Banding gives the LLM a way to honestly report uncertainty rather than confabulate.

No adjacent methodology was designed for LLM-as-builder. Most assume human builders.

### 4.6 — Layered structure: Objective → Capability → Implementation

ODD distinguishes three altitudes:

- **Objective:** outcome the system delivers (e.g., "operators can file refund disputes against merchant portals at scale").
- **Capability:** a feature or function that contributes to delivering an objective (e.g., "Playwright-driven dispute filing pipeline"). Multiple capabilities can serve one objective; one capability can serve multiple objectives.
- **Implementation:** how a capability is built (e.g., "Express route POST /process-disputes spawns child processes per dispute via testRunner.js").

These are not synonyms. The v0.1.8 extractor confused them by labeling implementations "ACs."

A complete ODD has all three layers AND the maps between them. The PR-safety gate (v0.1.9) needs the implementation-to-capability-to-objective map to gate correctly: a change that touches code backing a VERIFIED objective is a different blast-radius class than a change touching orphan code.

---

## §5 — Derivation chain (premises → ODD's distinct shape)

Step-by-step reasoning from agreed-upon premises about software to ODD's distinctive properties.

### Premise A
Every system has a purpose. A system without purpose either doesn't exist or is broken.

### Premise B
The purpose can be stated as one or more outcomes the system delivers (observable results from outside the system).

### Premise C
Implementation serves purpose. If implementation doesn't serve purpose, it's defective code (dead code, anti-feature, vestigial).

### Premise D
Implementation can be replaced (refactored, rewritten in a different language, swapped to a different library) while preserving purpose. This is the load-bearing distinction: outcomes are stable across implementation changes.

### Premise E
For an existing codebase, the purpose is implicit (in code shape, tests, docs, comments, user-context) even when it's not explicitly stated as a named objective list.

### Step 1
From A + B: a system can be characterized by its outcomes. Naming the outcomes IS naming the system's purpose.

### Step 2
From C + D: the same outcomes can be delivered by different implementations. Therefore the outcome description is independent of implementation.

### Step 3
From step 2: an authoring discipline that operates at outcome-altitude (not implementation-altitude) produces specs that survive implementation churn. ODD operates at outcome-altitude.

### Step 4
From E: extracting outcomes from existing code requires inferring from multiple signal sources (docs, tests, code patterns, user context). No single source is sufficient. Banding reflects the multi-source confidence gradient.

### Step 5
From step 1 + step 3: the §2.5 strict mapping rule (every code line ladders to a named AC) follows because if all code serves outcomes, every code line should be traceable to an outcome. Code that doesn't trace is orphan code (dead, anti-feature, or unstated objective surfaced by the extraction).

### Step 6
From step 3 + step 4: ODD-RE (reverse-engineering an ODD from existing code) is a coherent operation. It operates by: (a) reading multiple signal sources, (b) inferring outcomes, (c) banding by signal strength, (d) mapping outcomes to backing code, (e) surfacing orphans.

### Step 7
From step 6: the extractor's output altitude is OUTCOMES (objectives), not symbols. An extractor that produces symbol inventory is at the wrong altitude — it's doing implementation-extraction, not objective-extraction. (This is the v0.1.8 failure mode.)

### Conclusion

ODD's distinct shape — outcome-altitude, banded, strictly-mapped, method-loose, reverse-engineerable, LLM-builder-aware — falls out of the premises about software's relationship to its purpose. The shape is not arbitrary; it's derivable.

---

## §6 — The altitude question (objective / constraint / capability / implementation)

The four altitudes, with tests to distinguish.

### Objective

**Definition:** an outcome the system delivers. Observable from outside. Stable across implementation changes.

**Test:** "If the implementation were rewritten in a different language with different libraries, would this statement still describe what the system does?" If yes, it's objective-altitude.

**rd-automation example:** "Operators can file refund disputes against DoorDash and Uber Eats merchant portals at scale (hundreds-to-thousands per period across many merchants)."

**Anti-example (NOT objective-altitude):** "Express route GET /all-orders returns refunded order data" — this is the HOW, not the WHAT. If we rewrote in Rails, the route shape would change.

### Constraint

**Definition:** a bound on the solution space. Not an outcome; a property the solution must have.

**Test:** "Does this restrict HOW the system can deliver outcomes, without itself being an outcome?" If yes, constraint.

**rd-automation example:** "SOC-2 compliance binds the org. Every dispute-filing action emits an audit-log entry attributing the action to a user."

**Anti-example (NOT constraint):** "The audit log is stored in S3" — this is implementation. The constraint is that there IS an audit log; the storage choice is implementation.

### Capability

**Definition:** a feature or function the system provides that contributes to delivering objectives. Capability is one of potentially-many ways to serve an objective.

**Test:** "Could a different system deliver the same objectives without this exact capability?" If yes, capability (not objective). "Does this name a feature with a clear purpose?" If yes, capability (not implementation detail).

**rd-automation example:** "CSV upload + validation + S3 storage" — a capability that contributes to the objective "operators provide refund data for batch processing."

**Anti-example (NOT capability):** "the parseCSV function returns an array" — that's implementation; the capability is "CSV parsing," and the function is one way to build it.

### Implementation

**Definition:** specific code, classes, routes, file layout, library choices that build capabilities.

**Test:** "Does this name a specific symbol, file, line, or library?" If yes, implementation.

**rd-automation example:** "Express route GET /all-orders at src/routes/exportRoutes.js:66."

This is what v0.1.8 extracts and mis-labels "AC."

---

## §7 — Drift modes (patterns that look ODD-shaped but aren't)

These are concrete patterns the agent must recognize as drift.

### Drift mode 1 — symbol-as-AC

**Pattern:** "Express route GET /all-orders at file:line" labeled as AC.

**Why it's wrong:** the route is implementation. The AC is the outcome the route serves.

**Correction:** restate as objective: "Operators can list refunded orders for a given period." Map the route as one of N backing implementations.

### Drift mode 2 — function-name-as-AC

**Pattern:** "Function processDispute() exists" labeled as AC.

**Why it's wrong:** function existence is implementation. The AC is the outcome the function serves.

**Correction:** "Dispute-filing pipeline accepts a refunded-order record + produces a filed-dispute outcome on the merchant portal."

### Drift mode 3 — feature-as-objective

**Pattern:** "App has CSV upload" labeled as objective.

**Why it's wrong:** "CSV upload" is a capability. The objective is the OUTCOME the capability serves.

**Correction:** "Operators provide batch refund data without manual data entry." (CSV upload is one of N ways to deliver this; alternatives include API integration, manual entry, scheduled fetch, etc.)

### Drift mode 4 — test-name-as-implementation

**Pattern:** test name `test('processDispute calls portal.login() with credentials')` extracted as if it were the AC.

**Why it's wrong:** the test asserts implementation behavior (the call). The AC the test contributes to is the outcome.

**Correction:** test names that assert OUTCOMES (`test('Process disputes')`) are AC-shaped; test names that assert calls / DOM queries / specific function invocations are implementation-shaped. Distinguish at extraction time.

### Drift mode 5 — gap-as-objective

**Pattern:** "Missing test coverage on auth middleware" surfaced as an objective.

**Why it's wrong:** the absence of coverage is a finding, not an objective. The objective is what the system SHOULD deliver; gap analysis compares delivered objectives against expected.

**Correction:** keep gaps in a separate gap-analysis layer (a successor pass, after objective extraction).

### Drift mode 6 — constraint-as-objective

**Pattern:** "System must be SOC-2-compliant" labeled as objective.

**Why it's wrong:** SOC-2 compliance is a constraint (a property the solution must have), not an outcome the system delivers to users.

**Correction:** treat as constraint. The outcome-shaped objective behind it is something like "audit trail identifies who performed each privileged action" — that IS an outcome.

### Drift mode 7 — implementation-detail-as-constraint

**Pattern:** "System uses RSA-OAEP for token decryption" labeled as constraint.

**Why it's wrong:** the algorithm choice is implementation. The constraint is "tokens are confidential under transport" or similar.

**Correction:** lift to constraint altitude.

---

## §8 — Self-checks before producing ODD output

Five questions the agent runs over its own output before declaring an "AC" or "objective."

1. **Outcome-or-fact?** Is this an OUTCOME the system delivers OR a FACT about how it's built? If "fact about how it's built," it's not an objective. Restate as the outcome the fact-pattern serves.

2. **Implementation-swap test.** If the implementation were rewritten in a different language with different libraries, would this statement still describe what the system does? If no, it's implementation-altitude. Lift up.

3. **Builder-method test.** Could a different builder produce a different shape that meets this same statement? If no, the statement is too prescriptive about method. Loosen to objective + constraint.

4. **Observable-from-outside test.** Could someone outside the system verify this from observable behavior, without reading the code? If no, it's implementation-internal — not objective.

5. **User-purpose test.** Does this statement name a purpose / outcome / value-to-someone? If no, it doesn't have objective-shape. (Capabilities and constraints can also pass this test in modified form: capability names a function-with-clear-purpose; constraint names a property-the-solution-must-have.)

If any check fails, the output is at the wrong altitude. Restate before producing.

---

## §9 — rd-automation worked example

Concrete grounding. rd-automation is Eric's actual app, ~17.7k LOC TS/Playwright/Express, SOC-2-bound, production-stake, at `/Users/lukeivers/pos3/workspace/rd-automation/`.

### What v0.1.8 currently produces (wrong altitude)

131 outputs labeled "AC," all of the shape:

- `AC.JSTS.express.get.all_orders.src_routes_exportroutes_js` — "Express route GET /all-orders" (PLAUSIBLE, source citation `src/routes/exportRoutes.js:66`)
- `AC.JSTS.express.use.batches.src_routes_exportroutes_js` — "Express middleware mount USE /batches" (PLAUSIBLE)
- `AC.JSTS.playwright_page.orderspage` — "Playwright page object: OrdersPage" (PLAUSIBLE)
- `AC.JSTS.test.playwright.process_disputes` — "Playwright test: 'Process disputes'" (VERIFIED)

These pass §6 implementation altitude tests, NOT §6 objective tests. They're symbols-with-locations. The "Process disputes" test is the closest-to-objective signal in the set (test names that assert outcomes), but even it was extracted as an implementation fact (the test exists), not an objective (operators can file disputes).

### What ODD-shaped output would look like (correct altitude)

Drawn from rd-automation's actual purpose (per Eric's survey response):

**Objectives (outcomes the system delivers):**

- O1: Operators can file refund disputes against DoorDash and Uber Eats merchant portals at scale (hundreds-to-thousands per period across many merchants), replacing manual portal clickwork.
- O2: Each dispute-filing action is attributable to a specific user via the audit trail.
- O3: Operators can review run results (per-dispute outcome, screenshots, errors) after a batch completes.
- O4: The system recovers from in-flight failures (process restarts, portal-side errors) without losing or double-filing disputes.
- O5: The system avoids interfering with other Checkmate operations (CORS scoping, deploy gates, lifecycle hardening).

**Capabilities (features that contribute to objectives):**

- C1 (→ O1, O3): CSV-upload + validation pipeline (operator UI → backend validation → S3 storage)
- C2 (→ O1): Playwright-driven dispute-filing pipeline (per-dispute child process, per-merchant logic)
- C3 (→ O1, O4): Job orchestration (dispute job tracker, retry semantics, status streaming)
- C4 (→ O2): Identity-tagged audit trail (Winston backend + UberLogger Playwright; user email threaded through reports)
- C5 (→ O3): Run reporting (real-time logs, downloadable HTML reports, S3-stored artefacts)
- C6 (→ O4): Server-lifecycle hardening (randomized restarts, 503 health probe, drain-in-flight)
- C7 (→ O2): Authentication & authorization (RSA-OAEP token, CORS-restricted, Referer-checked)

**Constraints:**

- K1: SOC-2-bound; every privileged action emits an audit-log entry.
- K2: Production-stake; downtime / data-loss / wrong-action-on-customer-data are unacceptable.
- K3: External-portal-dependency; system must tolerate portal UX changes without crashing.
- K4: Cost-conscious; operations run on ECS Firefox-only Playwright with 1 worker.
- K5: Org-internal; users are Checkmate operators, not customers.

**Backing-implementation map (objectives → implementation):**

- O1 ← C1 (src/routes/inputRoutes.js, src/routes/scheduler*.js) + C2 (tests/dd_dispute.spec.ts, tests/uber_dispute.spec.ts) + C3 (src/services/disputeManager.js, testRunner.js)
- O2 ← C4 (src/utils/winston.js, src/playwright/uberLogger.js, src/services/processDispute.js with userEmail threading) + C7 (src/middleware/authMiddleware.js)
- O3 ← C5 (src/routes/s3reportRoutes.js, src/routes/exportRoutes.js, runs.csv writers)
- O4 ← C6 (src/services/taskManager.js, healthcheck routes) + C3 retry semantics
- O5 ← C7 (CORS scoping) + deploy-gate config (.github/workflows/*.yml)

This map turns the v0.1.8 outputs from primary-output-mis-labeled-as-ACs into BACKING-IMPLEMENTATION evidence-rows. The structural extraction work isn't wasted; it's repurposed as a derivative layer.

**Orphans (code that doesn't trace to a named objective):**

- (To be enumerated in extraction; placeholder section.)

### What gap analysis would surface (separate from extraction)

This is the layer ABOVE objective extraction, separate concern.

- O2 has a known weakness flagged by Eric: authMiddleware.js:36-55 has Referer-based auto-auth + runner_email skip — these weaken the audit trail's reliability for "who initiated this action," which is what O2 / K1 require.
- No automated test coverage on K1's audit-trail emission (no test asserts that processDispute calls log with userEmail).
- Implicit objective candidate: nothing in the extracted set covers "operators can suspend or cancel an in-flight batch" — does the system support that? If yes, it's an undocumented O; if no, it's an implementation gap.

Gap analysis is its own task. It compares (extracted objectives + completeness review) against (delivered implementation + tests + observable behavior).

### What completeness-interview would surface (separate, between extraction and gap-analysis)

Per Luke's proposal: a natural-language interview with the user about extracted objectives. "Here are the objectives I extracted. Here are objectives I think SHOULD be present but aren't (e.g., for a real-money app, no security-shaped objective in the set is suspicious). Confirm / adjust / add."

For rd-automation: an extracted set of 5 objectives that includes nothing security-shaped would prompt: "This system handles SOC-2-bound audit trails, RSA-OAEP token decryption, and customer order data. I extracted no objective stating 'attacker cannot escalate privilege via Referer-spoofing' or 'audit trail is tamper-evident.' Should those be objectives this system aims to deliver?" Eric ratifies / adjusts / adds.

The completeness-interview output augments the extracted-objective set with user-confirmed objectives. THEN gap analysis compares the augmented set against implementation.

---

## §10 — How to use this doc

Before doing any ODD-shaped task (extraction, ratification, completeness-interview, gap analysis, plan-authoring, AC text tightening, smoke verification), the agent does this:

1. **Read this whole file.** Not just the section headings — the derivation chain at §5 and the altitude tests at §6/§7/§8 are load-bearing.
2. **Hold §7 drift modes + §8 self-checks in working memory.** Every output the agent declares an "AC," "objective," "constraint," or "capability" passes §8's five questions.
3. **If reasoning at the wrong altitude, lift up.** §6 / §7 corrections are the lifting tools.
4. **Surface mis-altitude findings honestly.** If extraction produces implementation-shaped outputs (the v0.1.8 failure mode), name them as such; don't relabel.
5. **For greenfield ODD authoring** (new component, new amendment): objectives come first, then ACs, then implementation. The §5 derivation chain is the order.
6. **For brownfield ODD-RE** (extracting from existing code): multiple signal sources (docs, tests, user context, code patterns) → infer objectives at outcome altitude → band by confidence → map to backing implementation. The structural extraction (v0.1.8-shape) is one input, not the output.

---

## §11 — Provenance and revisability

This doc is a derivation written 2026-05-05 to bridge the LLM agent's training-data limitation against ODD-as-this-project-defines-it. Luke directly diagnosed the bridge gap; this document is the response.

If subsequent ODD work surfaces drift modes not covered here, add them to §7. If new adjacent concepts in training data become relevant, add them to §3. The doc evolves with the methodology.

The doc is canonical (lives at `docs/odd-llm-grounding-derivation.md` in pos-v2). It is auto-loaded into context by reference, OR manually loaded at the top of any dispatch brief that touches ODD work. Future enhancement: reference from `framework/CLAUDE.md` or session-start hooks to make auto-loading structural rather than discipline-dependent.
