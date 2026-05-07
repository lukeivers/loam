# Objective-Driven Design: Outcome-Altitude Acceptance for LLM-Authored Software

## Abstract

Test-driven and behaviour-driven methodologies assume the test author
and implementation author share context. LLM-authored software breaks
that assumption: the agent rarely shares the human author's mental
model, and standard methodologies produce specifications at the wrong
altitude — implementation facts mislabelled as objectives, methods
baked into acceptance criteria, code paths shipped without a contract
naming them. This paper describes Objective-Driven Design (ODD): four
altitudes (objective, constraint, capability, implementation); a
strict mapping rule requiring every line of code and every test to
ladder back to a named criterion; and an outcome-altitude acceptance
requirement that forces at least one verification per criterion set
to invoke the production code path on realistic inputs. We describe
the reverse-walk pipeline that extracts outcome-altitude objectives
from existing codebases, present a case study against a real-world
Playwright TypeScript project, and discuss how ODD composes with
primitives an LLM-attached harness already provides.

---

## 1. Introduction

Methodologies that govern human-authored code — TDD, BDD, ATDD,
design-by-contract, user stories — were designed for builders who
share the original author's intent. The author writes a test; the
builder reads it; both operate against a common mental model. Drift
between specification and code is bounded by the small distance
between two minds in the same room.

LLM-authored software stretches that distance to the limit. The agent
has only what the brief, the surrounding code, and its training data
tell it. When the brief is tight, the agent produces well-shaped
output. When the brief is loose or carries the wrong altitude of
detail — a function name where an outcome should appear; a library
choice where a criterion should appear — the agent extends the wrong
shape faithfully and ships defects that pass every local test.

Three failure patterns motivate this work:

1. **Specification at the wrong altitude.** A spec naming "Express
   route GET /all-orders returns refunded order data" names an
   implementation, not an outcome. The objective the route serves —
   "operators can list refunded orders for review" — is the outcome.
   Implementation-altitude specs prescribe method, lock the agent into
   a single shape, and produce tests that assert calls rather than
   user-observable behaviour.
2. **Acceptance criteria with method baked in.** "The component will
   reject malformed input via a Pydantic validator" prescribes the
   validator. The objective is "the component refuses malformed
   input"; how is the agent's call. Method-in-acceptance couples the
   test to the implementation and prevents refactor.
3. **Code paths without a contract.** A platform branch no criterion
   names; a configuration field exercised by no test; a defensive
   `if/except` for a case the contract says cannot arise. These
   accumulate silently, lock in behaviours future agents reason
   against, and propagate violations across iterations.

Objective-Driven Design (ODD) closes these gaps. It distinguishes four
altitudes, requires every code path to ladder to a named criterion at
the right altitude, and requires every criterion set to include at
least one test that verifies the production code path end-to-end on
realistic inputs.

---

## 2. ODD Methodology

### 2.1 The four altitudes

| Altitude | Definition | Test |
|---|---|---|
| **Objective** | An outcome the system delivers; observable from outside; survives implementation rewrite | If rewritten in a different language with different libraries, would this still describe what the system does? |
| **Constraint** | A bound on the solution space; restricts how outcomes are delivered without itself being an outcome | Does this restrict how outcomes are delivered, without itself being an outcome? |
| **Capability** | A feature serving objectives; one of many possible methods | Could a different system deliver the same objectives without this exact feature? |
| **Implementation** | A specific symbol, file, line, or library | Does this name a specific symbol, file, line, or library? |

The altitudes are not synonyms. An objective is the outermost statement:
what the user gets. A constraint is the perimeter of the solution
space. A capability is one means by which objectives are delivered. An
implementation is the specific code.

A worked example. For a system that automates refund disputes against
external merchant portals, "operators can file refund disputes at scale,
replacing manual portal clickwork" is an objective — it survives any
reasonable rewrite. "Every dispute-filing action emits an audit-log
entry attributing it to a user" is a constraint. "CSV upload and
validation pipeline" is a capability. "Express route POST
/process-disputes at src/routes/disputeRoutes.js:120" is an
implementation.

### 2.2 The strict mapping rule

Every line of code, every branch, every test, and every dependency in
a deliverable must map to a named acceptance criterion that ladders to
a named objective. Code handling a case, platform, configuration, or
concern the objectives do not declare is a violation regardless of how
well-written it is.

The rule runs in both directions:

- **Forward (authoring).** Every declared behaviour in every objective
  has at least one criterion. If the objective contains "and", count
  the conjuncts and verify each has its own criterion.
- **Reverse (review).** Every code path, test, branch, and dependency
  in the diff has a criterion it maps back to. If you cannot point at
  one, the code should not exist.

The reverse direction is load-bearing. Forward checks catch
under-tested objectives; reverse checks catch the silent accumulation
of method that crept in without a contract authorising it. "Might be
useful later" is never a backing.

When a builder discovers a gap during work, the sanctioned response is
to promote the gap to a new criterion with a test, not to bury it
behind an exception branch. This *re-extension* pattern distinguishes
ODD's defect handling from approaches where defensive code accumulates
as silent precedent.

### 2.3 Drift modes

LLM-authored work drifts predictably. Seven patterns recur:

1. **Symbol-as-criterion.** "Express route GET /all-orders at file:line"
   labelled a criterion. Route is implementation; the criterion is the
   outcome the route serves.
2. **Function-name-as-criterion.** "Function processDispute() exists"
   labelled a criterion. Function existence is implementation.
3. **Feature-as-objective.** "App has CSV upload" labelled an
   objective. CSV upload is a capability.
4. **Test-name-as-implementation.** A test asserting one function
   called another with specific arguments is implementation-shaped, not
   outcome-shaped.
5. **Gap-as-objective.** "Missing test coverage on auth middleware"
   labelled an objective. The absence is a finding.
6. **Constraint-as-objective.** "System must be SOC-2-compliant"
   labelled an objective. SOC-2 is a constraint.
7. **Implementation-detail-as-constraint.** "Uses RSA-OAEP" labelled a
   constraint. The constraint is "tokens are confidential under
   transport"; the algorithm is implementation.

Recognising these at authoring time is cheapest. By review time the
drift has often locked in via tests that codify the wrong altitude.

### 2.4 Self-checks

Before declaring an objective, constraint, capability, or criterion,
an agent runs five questions over its own output:

1. **Outcome-or-fact?** Outcome the system delivers, or fact about how
   it is built?
2. **Implementation-swap.** If rewritten in a different language with
   different libraries, would this still describe what the system does?
3. **Builder-method.** Could a different builder produce a different
   shape meeting it?
4. **Observable-from-outside.** Verifiable from observable behaviour,
   without reading code?
5. **User-purpose.** Names a purpose, outcome, or value to someone?

Any failure indicates the wrong altitude. The fix is to restate, not
label loosely.

### 2.5 Positive framing

Acceptance criteria are stated in the positive: what the system does,
not what it must not do. "The component does not crash on malformed
input" tests for the bug. "The component refuses malformed input with
an actionable error" names the outcome — the rejection is observable,
and the error message is the artefact the test asserts on.

This converts regressions into objectives. When a defect surfaces,
the question is not "what test catches this bug" but "what objective
was missing that allowed this code to ship?" The answer becomes a
positively-stated criterion. Positive criteria concentrate on the
contract the system delivers; the agent authors against contracts,
not against past failure modes.

### 2.6 Why this is novel

Adjacent methodologies operate at outcome-altitude in their greenfield
framing — Gherkin scenarios, user-story templates, acceptance-test
names. They diverge from ODD in four ways. First, none enforce strict
mapping in both directions; orphan code is allowed by default. Second,
none distinguish four altitudes explicitly; objectives, features, and
implementations are routinely conflated. Third, none require positive
framing — negative-tested invariants are routine in BDD and
design-by-contract, where they accumulate as regression scaffolding
rather than as criteria the agent authors against. Fourth, none were
designed for the LLM-as-builder context — where the spec must be
statable in natural language, the criteria observable without reading
code, and method left to the agent's optimisation room. ODD is the
operational shape that falls out when those four constraints are
taken seriously together.

---

## 3. Reverse-Walk Pipeline

A second contribution: extracting outcome-altitude objectives from
existing codebases.

A naive approach feeds the codebase to an LLM and asks for objectives.
The output is reliably at the wrong altitude — the training gradient
pulls the model toward symbol inventory ("Express route X exists at
file:line") and produces structural facts mislabelled as contracts.
An earlier single-pass extractor we built labelled 131 outputs as
acceptance criteria across a 17.7k-line TypeScript application, every
one at implementation-altitude. The codebase contained those facts;
the facts were not the objectives the system delivers.

The reverse-walk pipeline corrects altitude through multi-source
synthesis followed by structural mapping.

### 3.1 Multi-source synthesis

Five signal sources feed extraction, ranked by reliability:

1. **README and design documents** — plain-English purpose statements
   maintainers wrote to explain the system to other humans.
2. **User-supplied context** — the maintainer's own framing.
3. **Test names and assertions** — tests whose names assert outcomes
   are the closest-to-objective signal in code.
4. **Code-pattern inference** — route shapes, middleware names, page
   objects, model class names; domain language carries objective signal.
5. **Commit messages** — chronological intent; weakest signal, useful
   for cross-checking.

Extraction produces confidence-graded output: VERIFIED (test-pinned),
PLAUSIBLE (source-cited), or HYPOTHESISED (LLM-inferred with
rationale). Bands enumerate trust, not importance: a HYPOTHESISED
objective may name a load-bearing outcome; the band states only how
confident the extractor is that it holds.

The synthesis pass invokes an LLM to combine sources into candidate
objectives, with altitude self-checks applied programmatically.
Outputs that fail more than 30% of checks trigger a drift-halt: the
extractor restarts with the failures as input, rather than completing
a diverged chain.

### 3.2 Backing-implementation map

Each extracted objective is mapped bidirectionally to evidence rows in
the codebase — the route, model, test, or function that contributes to
delivering it. Every objective has a non-empty evidence list; every
evidence row is reachable from at least one objective.

Three categories of finding emerge:

- **Verified backing.** At least one VERIFIED-band evidence row.
- **Plausible backing.** Source-citation evidence only; the maintainer
  reads the cited code to confirm.
- **Implementation orphans.** Code paths no extracted objective
  reaches. Either dead code, or the extraction missed an objective the
  orphans serve.

Structural extraction earlier extractors mis-labelled as criteria is
repurposed as the backing-map's evidence rows. The mis-labelling was
the defect; the inventory itself remains useful.

### 3.3 Gap analysis

Two categories sit on top of the backing map:

1. **Objectives without verified backing** — named objectives backed
   only by PLAUSIBLE or HYPOTHESISED evidence. Either tests are needed,
   or the objective is not actually delivered.
2. **Implementation orphans that may indicate missing objectives** —
   code paths the objectives do not reach. Some orphans are dead code;
   some surface undocumented outcomes.

### 3.4 Build-next recommendation

The final stage produces a ranked list of candidate next builds, each
tied to a gap. Candidates are scored on gap severity, backing
confidence, and (when present) operator survey context. Each candidate
carries rationale referencing the gap it addresses, the objective it
strengthens, and the evidence that shaped the recommendation. The
output is informative-not-prescriptive: it ranks options; it does not
select one. The stage connects extracted objectives to forward-looking
work with traceability from candidate through gap and objective back
to the codebase.

---

## 4. The Outcome-Altitude Acceptance Requirement

The strict mapping rule (§2.2) catches code paths without a contract.
It does not catch contracts at the wrong altitude. We observed three
distinct failures sharing a shape: a criterion verified against
pre-arranged fixtures passes in unit and integration tests; the same
criterion verified against the real-world production shape fails at
the release-level integration gate.

The pattern. A criterion states "synthesis stage produces objectives."
A test invokes the synthesis function directly with a stubbed client
and asserts on the output shape. The test passes. In production, the
CLI never calls the synthesis function because the wire-through is
missing; it silently falls into an empty-synthesis path. The criterion
is satisfied at implementation-altitude (the function works when
called); it is not satisfied at outcome-altitude (the user invokes the
CLI and gets nothing).

The strict mapping rule does not catch this. It enforces traceability
but permits all criteria to live at implementation-altitude.

### 4.1 The rule

Every criterion set must include at least one criterion marked at
outcome-altitude, verified by a test that:

1. Invokes the production entry-point the user invokes (CLI, API
   endpoint, dispatch surface) — not a private helper.
2. Does not pre-arrange state that the production code would normally
   produce.
3. Produces a real outcome artefact: a file written, a response
   returned, a side-effect observed.

The first clause prevents the test from asserting on internal helpers
the user never reaches. The second is load-bearing: it forbids
fixtures that bypass upstream stages by writing those stages' outputs
directly.

### 4.2 Pre-arrangement detection

A single question discriminates:

> Does this test write state that the production code under test would
> normally produce?

If yes, the test is stub-class. Stub tests can satisfy
implementation-altitude criteria but never outcome-altitude criteria.

The rule applies regardless of staging — direct file writes into the
working directory before the CLI runs; fixture factories that
pre-populate database tables the production code would have written;
mocks that inject values where production code would compute them;
stub clients that return canned responses standing in for the real
LLM call.

A test is outcome-class when it invokes the production entry-point on
realistic-shape inputs and asserts on the artefacts the production
code produces.

### 4.3 Risk-band classifier

Outcome-altitude verification is not free. Per-iteration outcome tests
against real-world fixtures cost wall-clock time and fixture
maintenance. A risk-band classifier governs when the cost is required.

**Per-iteration verification required** when the iteration touches:
a CLI command or flag; a plugin or extension surface; a user-visible
artefact (file, terminal output, error message); a configuration
schema; a persistence schema crossing session boundaries.

**Release-gate verification acceptable** when the iteration touches
only internal data structures with no observable shape change; pure-
function refactors; test-only edits; or documentation.

The classifier composes with the mapping rule: every code path has a
contract; every contract set has at least one production-path probe;
production-facing surfaces verify per iteration, internal refactors
defer to release.

---

## 5. Case Study

We exercised the methodology against a Playwright TypeScript project
of approximately 19,000 lines: a CSV-driven automation that drives
external merchant portals to file refund disputes at scale, replacing
manual portal clickwork. The system is production-stake, SOC-2-bound,
and handles customer order data.

### 5.1 Four integration runs

The build cycle iterated four end-to-end integration runs against the
production code path. Each invoked the four-stage extractor pipeline
(extraction, completeness interview, gap analysis, build-next
recommendation) against the real codebase with no pre-arrangement.

The progression: failure, failure, failure, pass. Each failure
surfaced a production-path gap synthetic tests had passed without
exercising:

- **Run 1.** The CLI's extraction stage produced empty output. Unit
  tests of the synthesis function passed because they invoked the
  function directly with a stubbed client. The CLI never wired the
  client through; the production path silently fell into an
  empty-synthesis branch.
- **Run 2.** The synthesis subprocess used an SDK-based authentication
  path. The runtime environment did not have the SDK installed. Unit
  tests passed because they monkey-patched the SDK at import time. The
  production path tried to import the real SDK and raised.
- **Run 3.** With the SDK replaced, the live LLM returned outputs that
  violated a banding rule the synthetic fixtures had never produced —
  outputs claiming the highest confidence band without the multi-source
  evidence the band required. The validator raised; the user received
  a stack trace.
- **Run 4.** With upstream stages fixed, the four-stage pipeline ran
  end-to-end. Six outcome-altitude objectives were extracted; §self-
  checks pass rate was approximately 87% (above the 80% threshold);
  all six objectives had backing-map coverage; gap analysis surfaced
  three objectives without verified backing; build-next produced three
  ranked candidates with rationale referencing specific gaps.

### 5.2 The mid-cycle rule shipment

The outcome-altitude acceptance requirement (§4) shipped mid-cycle —
after the second failure. The pattern was too consistent to ignore:
every failure the fixture surfaced had passed every synthetic test.
Criteria were green at implementation-altitude; the user-facing
outcome was broken.

The first test authored under the new rule caught a new
production-path blocker on its first live run. The rule paid for
itself in the cycle that authored it.

### 5.3 Outcome metrics

Final pass: six outcome-altitude objectives extracted; spot-check of
three randomly-selected objectives against the five self-checks scored
5/5, 5/5, and 3/5 (the last contained "parallel workers" phrasing that
hints at implementation, though the outcome it describes — throughput
— survives the rewrite test); aggregate self-check pass 13/15 (~87%);
full backing-map coverage (one verified, five plausible); three gaps
in the inventory; three ranked build-next candidates with prose
rationale referencing specific gap identifiers. No tracebacks. Each
run took approximately five minutes wall-clock, dominated by the
synthesis-stage LLM call.

### 5.4 What the case study teaches

Three observations. First, the mapping rule is necessary but not
sufficient: it caught none of the four real-world failures because
every failing path had a criterion authored against it at the wrong
altitude. Second, synthetic-fixture tests cannot substitute for
production-path probes — each failure involved an upstream stage the
fixtures had pre-populated, bypassing the code the user reaches.
Third, the cost of authoring outcome-altitude probes per iteration is
bounded — once the fixture exists, it is reused across runs — and
savings on release-gate rework are substantial.

---

## 6. Composition with Claude Code

The methodology composes with primitives Claude Code already provides.
Three examples:

### 6.1 Hook-based memory

Claude Code's hook system fires at session lifecycle events
(SessionStart, UserPromptSubmit, Stop). The four altitudes, mapping
rule, drift modes, and outcome-altitude requirement load at
SessionStart via a corpus contributor that surfaces them as
additional context; a Stop hook persists methodology violations and
fixes to disk; a UserPromptSubmit hook retrieves the relevant prior
entries on the next session's first turn. The agent does not
re-derive the methodology from drift each session, and the in-context
budget is paid only for content that scored above a relevance
threshold.

### 6.2 Subprocess-driven LLM calls under subscription auth

The synthesis stage invokes an LLM. When the agent runs under a
developer's Claude Max subscription rather than a keychain-stored
Anthropic API key, the cleanest invocation is <code>claude -p</code> as a
subprocess — Claude Code's print mode — sandboxed via
<code>--strict-mcp-config</code> against an empty MCP configuration so
the spawned process inherits no plugins from the parent session.
The subprocess boundary is the auth boundary; the empty MCP
configuration is the isolation boundary; together they let the
pipeline call the model from automated runs without credential
plumbing or state leakage.

### 6.3 Skill packages for sub-agent propagation

When work is dispatched to a sub-agent, the methodology must travel.
Claude Code's skill-package mechanism — markdown documents under
<code>.claude/skills/</code> the agent loads when their descriptions
match the active task — propagates the methodology's principles to
the sub-agent's session-start corpus. This closes the context gap
that otherwise leaves sub-agents to re-derive the rule from scratch
or worse, ignore it because the parent session's reminders never
crossed the dispatch boundary.

In each case ODD leans on a primitive Claude Code already provides.
The methodology is not a re-implementation; it is a discipline layered
on Claude Code's existing surface.

---

## 7. Limitations and Future Work

### 7.1 Limitations

**Negative-alignment detection is deferred.** The methodology catches
code without a contract, and contracts at the wrong altitude. It does
not catch the case where contract says X and code does not-X — where
intent and implementation are inverted rather than misaligned.
Detection requires richer objective semantics and calibration data
for false-positive control.

**The outcome-altitude probe assumes a callable production
entry-point.** A system whose user-facing surface is a UI without an
automation surface, or a notification stream without a consumer, has
no callable entry-point. The risk-band classifier treats such cases
as production-facing, but verification needs project-specific
harnesses (browser automation, message-queue consumers) the
methodology does not supply.

**Confidence bands rely on test-pass assumptions.** The pipeline
grants the highest band to objectives backed by passing tests but
does not execute tests; pass-state is assumed at the resolved
revision. A codebase whose tests are broken at extraction time will
be over-confident on every test-backed objective. Maintainer
ratification is the human-in-the-loop fix.

**Drift detection at synthesis is heuristic.** The 30% self-check
failure threshold is a calibration choice, not a derived constant.
False-halt and missed-drift rates are open questions.

### 7.2 Future work

**Outcome-altitude probes integrated with cold-start code generation.**
The pipeline currently extracts from existing code. The inverse —
using extracted objectives as a planning input for new code generation
— is a natural next step, letting LLM-authored greenfield code
inherit outcome-altitude discipline rather than learn it through
fix-up cycles.

**Negative-alignment detection.** When calibration data allows,
extending the methodology to catch code contradicting its own contract
would close the third class of failure. This is the least tractable
of the three; we expect it to require new extraction primitives and
judging mechanisms.

**Risk-band classifier formalisation.** The §4.3 classifier is a list
of categories. Formalising it as a structural check (manifest field,
dispatch-brief schema requirement) would replace discipline-on-the-
author with structural enforcement the harness itself runs.

---

## 8. References

The operational specification and LLM-context grounding documents are
public:

- *Objective-Driven Design — Operational Specification.* Mechanics:
  altitudes, mapping rule, re-extension, structural-vs-advisory
  enforcement.
- *ODD — LLM Context Prime (lean).* Compact reference loaded at the
  start of methodology-shaped tasks.
- *ODD — LLM Grounding Derivation.* Long-form derivation walking
  adjacent concepts (TDD, BDD, ATDD, design-by-contract, user stories,
  DDD, requirements engineering) and the premises producing ODD's
  shape.

The §5 reference implementation is a ~19,000-line Playwright
TypeScript application, production-stake and SOC-2-bound; specific
repository details are omitted to honour operator confidentiality.
