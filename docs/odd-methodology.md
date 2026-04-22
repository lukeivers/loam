# Objective-Driven Design (ODD) — Operational Specification

**Audience:** AI assistants authoring, reviewing, or executing work inside a pOS
workspace — primary personas, specialist personas, and background agents. This
document is the canonical reference for what "doing ODD properly" requires at
the mechanical level. It is not persuasive (see the companion doc for why ODD
is chosen) and not illustrative of pOS specifically (see the implementation
doc for pOS examples). It is the specification you consult when structuring
work.

**Status:** normative. When this document and a persona's own instincts
disagree, this document wins.

---

## 1. What ODD is

Objective-Driven Design defines every unit of work by its **observable outcome**,
not by a sequence of steps. Work is assigned as an *objective* — a statement
about the state of the world that must be true when the work is done — plus
*constraints* that bound the method, plus *acceptance criteria* that are
deterministic checks confirming the objective is met.

The receiving agent chooses the method. Method is not part of the work
definition.

### 1.1 The three terms

| Term | Definition | Authored by |
|------|------------|-------------|
| **Objective** | A state of the world the work is required to make true. Stated as outcome, not as procedure. | The delegator |
| **Constraint** | A bound the method must respect (budget, dependency, reversibility class, forbidden imports, etc.). Not a step — a guardrail. | The delegator |
| **Acceptance criterion** | A deterministic, test-shaped check that confirms the objective is met. One criterion per declared behaviour inside the objective. | The delegator, with builder challenge permitted |
| **Method** | How the objective is satisfied. File structure, algorithm, library choice, sequencing. | The builder |

If an instruction tells the builder *what steps to take* rather than *what must
be true at the end*, it is not an objective — it is a procedure. Procedures
and objectives can coexist in a brief, but only the objectives bind. Procedures
are advisory.

### 1.2 The one-sentence test

> An objective is a state of the world you want true; an acceptance criterion is a
> deterministic check that the objective is met.

If your work description does not fit that shape, rewrite it until it does.

---

## 2. Authoring an objective

An ODD objective has three required components and one forbidden one.

### 2.1 Required: scope

Name what this objective is about. The scope must be small enough that a
single acceptance criterion can test it, or large enough that it decomposes
cleanly into sub-objectives each with its own criterion. A scope that needs
seven criteria to test is probably three objectives.

### 2.2 Required: constraints

State what the method may not do. Constraints come in five common shapes:

1. **Budget** — time, tokens, money. Exceeding the budget fails the scope
   regardless of objective satisfaction.
2. **Reversibility class** — fully reversible / compensatable / irreversible.
3. **Dependency fence** — what this scope may import, call, or depend on. What
   it must not touch (e.g., "no amendments to sealed components").
4. **Authority bound** — what decisions the builder may make unilaterally and
   what must be escalated.
5. **Fail-closed direction** — when the objective cannot be satisfied, what
   the failure state must look like (refuse, halt, queue, etc.).

Constraints bound the method without prescribing it. "No LLM calls inside the
gate" is a constraint. "Use a Pydantic validator for the gate" is method.

### 2.3 Required: acceptance criterion

A deterministic check. Someone else (human or machine) can run it and get a
pass/fail answer without consulting the author's intent.

The rule that governs acceptance criteria is the criteria-audit rule:

> Every declared behaviour within an objective must carry its own testable
> acceptance criterion. An objective that declares three behaviours and
> supplies one criterion has tested one-third of its content.

If your objective statement contains the words "and" or "also," count the
declared behaviours and verify each has a criterion.

### 2.4 Forbidden: method

Do not prescribe the method. Prescribing method in an acceptance criterion is
the single most common ODD violation.

Method-in-acceptance anti-patterns:

- "The test will use pytest." (How the check runs is not what the check tests.)
- "The component will implement a visitor pattern." (Pattern is method.)
- "The refusal will be a Pydantic model_validator." (Structure is method — the
  objective is "the refusal happens"; whether it happens via Pydantic or an if
  statement is the builder's call.)
- "The function will return an `ErrorResult` dataclass." (The *return shape* is
  sometimes a contract, but stating it inside an objective is usually
  over-specification — if the contract matters, lift it out as a separate
  interface objective.)
- "The builder will first write the schemas, then the store, then the gates."
  (Ordering is method.)

Objective restatements of the above:

- "A test suite exists that verifies every A-criterion and exits non-zero on
  any failure."
- "A component exists that accepts input of shape X and produces output of shape Y."
- "A component that receives malformed input refuses it and produces a
  structured error the caller can route."
- "The component's public API rejects invalid inputs at construction." (If the
  rejection mechanism matters, name it as an interface objective, not buried
  in an acceptance bullet.)
- (No restatement — ordering was never an objective. Delete.)

### 2.5 Forbidden: code for cases the objectives do not name

The positive-space corollary of §2.4: **build only what the objectives
require.** Every line of code, every branch, every test, every dependency
in a deliverable must map to a named acceptance criterion backing a named
objective. Code that handles a case, platform, configuration, or concern
the objectives do not declare is an ODD violation regardless of how
well-written it is — it is method that crept into the deliverable without
a contract authorising it.

§2.4 names method-in-acceptance — prescribing HOW inside the contract.
§2.5 names method-in-code — executing HOW outside any contract at all.
Both are the same class of error: over-specifying method beyond what the
objectives require. The first is visible at authoring time; the second
is visible at review time inside the diff.

Anti-patterns:

- A platform branch for an OS no objective names. ("pos-v2 supports
  Linux" is not a stated objective — yet Linux branches exist in
  service-manager code, test fixtures, and installer helpers. Added
  incidentally because "POSIX-ish shells make it easy," not because a
  contract required it. Luke's 2026-04-22 ruling formalised this rule.)
- A configuration field/option/flag no acceptance criterion exercises.
  The field is method-leakage; if the knob matters, it needs a criterion
  that verifies its effect. If no criterion reaches for it, delete it.
- A defensive `if/except` branch for a case the contract says cannot
  arise (raises on an unknown enum value; wraps a call that can't fail;
  handles a None where None is impossible). These are silent exception
  branches from the §8.2.8 rule, rendered from the proposal side.
- A dependency imported for a feature no objective requires. "We might
  want X later" is not a current-objective backing.
- A test that exercises a path no criterion declares. Tests without
  backing criteria inflate the test surface without inflating the
  covered contract; they also lock in non-objective code against
  refactor, making the violation harder to remove later.

The test: for every code block, every branch, every dependency, every
test, point at the acceptance criterion it satisfies. If you cannot, the
code should not exist. Two ways forward:

1. **Re-extend up the objective chain** (per §4). Promote the case to a
   named acceptance criterion with its own test. The code now has a
   contract. This is the same mechanism §4 names for negative cases
   discovered during build; §2.5 extends it to positive cases a builder
   is tempted to include "because it's easy."
2. **Delete the code.** If the case isn't worth an objective, it isn't
   worth implementing either.

"Might be useful later" is never a justification for current inclusion.
If it's useful later, it gets a future objective and a future amendment.
Current code matches current objectives only.

The structural check is the same one §3.3's behaviour-count enforces,
run in both directions:

- **Forward (authoring):** every declared behaviour in every objective
  has an acceptance criterion.
- **Reverse (review):** every code path, test, branch, and dependency
  in the diff has an acceptance criterion it maps back to.

A diff where forward+reverse both pass is scope-clean by §2.5's rule.
A diff that fails reverse has method-in-code leakage that must be
corrected before landing — by re-extension or deletion.

---

## 3. Acceptance criteria in detail

An acceptance criterion is the load-bearing component of an ODD objective.
Everything else is scaffolding.

### 3.1 Deterministic check

"Deterministic" means the criterion yields the same verdict for the same
state, every run, without reliance on model inference or human judgment.

- **Good:** "Loading a `always_ask.yaml` that omits any framework-floor
  category raises a Pydantic validation error at load time."
- **Bad:** "The loader should reject malformed configs." (Who decides
  "malformed"? What exception? What timing?)

A criterion you cannot execute is not a criterion — it is a wish.

### 3.2 Test-shaped

Write the criterion as something a test would assert. The test function
usually writes itself from a well-formed criterion:

> **A1.** Scope kill issued against an active scope transitions the scope and
> its TERMINATE-policy children to `cancelled` within 500ms p95. Emits
> `pos.safety.scope_kill` span with level + reason + source. Writes a
> `kill_events` row.

The test: fire a scope kill; assert state transition; assert child cancellation;
assert span attributes; assert row; assert timing. Every clause in the criterion
maps to one assertion in the test.

### 3.3 One criterion per declared behaviour

Count behaviours, count criteria. If the objective says *"the system accepts
X, rejects Y, and logs Z"*, that is three behaviours, which requires three
criteria (or one multi-clause criterion with three independently testable
clauses).

This rule prevents the failure mode where an objective declares four
behaviours, supplies one criterion for the easiest one, and ships with the
other three unverified. It happens reliably when acceptance criteria are
written after the objective rather than as the mechanical completion of it.

### 3.4 Timing and budget belong in the criterion

Performance, latency, cost, and concurrency constraints are part of the
acceptance criterion, not a separate concern. "Within 500ms p95" is part of
A1 above because a kill that works in 60s is not the objective pOS wants.

### 3.5 Negative criteria are criteria too

"X does not happen" is a valid criterion when the objective is about
preventing something:

> **A19.** A hand-crafted `always_ask.yaml` with `framework_floor: []` is
> refused at load. A workspace that attempts to monkey-patch
> `FrameworkFloorCategory` at runtime does not change the gate's behaviour
> because the gate reads the validated model, not the enum directly.

This is testable: hand-craft the file, try to load it, assert the load fails.
Monkey-patch the enum, fire the gate, assert behaviour unchanged.

---

## 4. Handling defects and negative cases

ODD's distinctive rule for defects: **a failure mode discovered during work is
re-extended up the objective chain as a new positive objective, not buried as
an exception branch in existing code.**

### 4.1 The re-extension pattern

When the builder (or reviewer) discovers:

- a scenario the current objectives do not cover,
- a collision between two objectives that was not anticipated,
- a negative case that passes the letter of the acceptance criteria but
  violates the spirit,

the correct action is **not** to quietly add an `if` branch to handle it.
The correct action is to promote the failure mode to a named acceptance
criterion and extend the objective list.

### 4.2 Canonical example — safety-layer's A20

The safety-layer component's proposal in pOS declared A1–A19. During build,
the builder noticed that the proposal §5 contained the sentence *"Safety
always wins on collision with graceful-degradation"* as a constraint — but
nothing in A1–A19 tested that collision.

Two options were available:

1. **Bury it** — write the safety-wins code, merge, assume the behaviour holds
   because the author promised it.
2. **Re-extend** — promote the promise to a named acceptance criterion (A20)
   and author a test against it.

ODD requires option 2. The safety-layer build shipped with:

```
tests/test_safety_beats_degradation.py  # A20 (added per brief §5)
```

containing `test_A20_system_kill_supersedes_degradation_pause` and
`test_A20_session_kill_supersedes_degradation_pause`. The commit message
named A20 as the re-extended criterion and cited the rationale: "the proposal
promises it and failure here would be a contract violation."

### 4.3 Why this rule exists

A failure mode buried as an exception branch in existing code:

- is invisible to the acceptance-criteria audit (the criteria list still says
  A1–A19 are the work, so the audit passes),
- is invisible to anyone reviewing the objective list (they see A1–A19 and
  reason about those),
- cannot be tested independently (its test hides inside whatever test
  happened to catch the branch first),
- accumulates silently — a component with twelve buried exception branches
  has twelve untracked behaviours that future changes can break without
  detection.

A failure mode re-extended as a positive objective:

- appears in the acceptance-criteria list,
- has its own test,
- survives in the audit trail,
- can be reasoned about when the component is modified.

### 4.4 Re-extension is never a violation; silent handling is

A builder who extends A1–A19 with an A20 has not exceeded their scope.
Re-extension is the sanctioned response to a discovered gap. What is forbidden
is *handling the gap silently* — producing code that addresses the case
without naming it as an objective.

When a builder cannot re-extend (e.g., the gap is so large it requires the
original author to re-scope), the sanctioned action is **halt and signal**,
not quiet handling.

---

## 5. Enforcement at runtime — structural checks, not advisory rules

ODD applied to code produces structural enforcement, not advisory rules.
The distinction is mechanical.

### 5.1 Structural vs advisory

An **advisory rule** lives in prose — a docstring, a comment, a rules file, a
prompt. It describes what the code should do but does not prevent the code
from doing otherwise. Advisory rules depend on the reader (human or LLM)
following them.

A **structural check** lives in the type system, the schema, or the
constructor. It prevents the forbidden state from being representable. The
code cannot violate it without refactoring the structural check itself.

ODD prefers structural over advisory every time. Advisory is the fallback for
things structure cannot reach (e.g., persona voice, documentation clarity).
Anything that *can* be expressed structurally *must* be.

### 5.2 The clause-(g) pattern

The canonical ODD-as-code pattern in pOS is the clause-(g) structural check
from the self-upgrade framework. Clause (g) of the self-upgrade spec is
"every pOS change included in the upgrade is actually installed — none are
silently skipped." The objective is one sentence; the enforcement is this:

1. The upgrade unit (release tag) ships with a manifest listing every file
   that should change and its expected post-upgrade SHA.
2. Post-upgrade, the framework runs `check_clause_g(manifest, live_root)`
   which iterates every manifest entry and verifies the on-disk file's SHA
   matches the expected SHA.
3. Any mismatch returns a `ClauseResult(clause="g", passed=False, ...)` with
   the list of mismatches attached.
4. A failed clause-(g) check triggers rollback in the caller — the upgrade
   did not silently skip anything because the verification that it didn't is
   itself part of the upgrade pipeline.

The rule "never silently skip a change" was originally an advisory rule.
Under ODD, it became:

- a **manifest** (structural — the expected state is a data structure),
- a **verifier** (structural — the check is a function),
- a **clause bundle** wiring the verifier into the upgrade sequence
  (structural — failure short-circuits to rollback).

The refusal to silently skip is in the schema and the code path, not in a
human's or LLM's memory.

### 5.3 Pydantic + model_validators is the reach-for default

When a refusal must be structural, Pydantic schemas with `@model_validator`
decorators are the reach-for default in pOS. They:

- fail at construction, not at use — invalid state is unrepresentable once
  the validator passes,
- produce structured errors the caller can route,
- are test-shaped (constructing a bad instance in a test asserts failure),
- compose (validators can reference other fields on the same model and raise
  with named reasons).

The safety-layer's `always_ask.yaml` loader uses this pattern: the loader
raises a Pydantic validation error at load time when any framework-floor
category is missing. The refusal is in the schema, not in the gate's runtime
logic. The gate reads the validated model; it cannot be bypassed by
monkey-patching the enum because the model has already been frozen by the
validator.

### 5.4 When structural enforcement is not available

Some things resist structural checks. Examples:

- persona voice and tone,
- documentation clarity,
- whether a user-facing message is helpful,
- whether a chosen abstraction is the right one.

For these, ODD falls back to the objective + acceptance pattern with a
test-based or review-based check, and accepts that the check is not
structurally guaranteed. The rule is: structural where possible, advisory
only where structure cannot reach.

---

## 6. ODD vs TDD vs BDD (brief)

These three methodologies are adjacent but not interchangeable. Short form:

### 6.1 TDD — Test-Driven Development

- **Level:** behaviour of a unit of code.
- **Loop:** red → green → refactor.
- **Authoring:** write a failing test, write the minimum code to pass it,
  refactor.
- **Outputs:** a test suite and the code that satisfies it.
- **Scope of judgment:** the test author decides what "done" looks like per
  behaviour.
- **Negative cases:** added as new failing tests; the code is extended to
  pass them.

TDD is about *how you build* a unit — red/green cadence on behaviour-level
tests.

### 6.2 BDD — Behaviour-Driven Development

- **Level:** scenario, in stakeholder language.
- **Form:** given/when/then.
- **Authoring:** scenarios describe behaviour from the stakeholder's
  perspective; each scenario becomes an executable spec.
- **Outputs:** a scenario suite readable by non-engineers plus the code that
  satisfies it.
- **Scope of judgment:** the scenario author collaborates with stakeholders
  on what matters.
- **Negative cases:** added as new scenarios — "given X, when Y, then the
  system refuses."

BDD is about *what you build* at the scenario level, with stakeholder-readable
specs.

### 6.3 ODD — Objective-Driven Design

- **Level:** objective (state of the world to make true).
- **Form:** scope + constraints + acceptance criterion.
- **Authoring:** state the outcome, bound the method, write a deterministic
  acceptance check; the builder chooses the method.
- **Outputs:** a set of objectives with acceptance criteria; the code that
  satisfies them; the tests that verify them.
- **Scope of judgment:** the delegator decides what must be true; the
  builder decides how to make it true.
- **Negative cases:** re-extended up as new positive objectives (not
  buried as exception branches).

ODD is about *what you delegate* — the contract between a delegator and a
builder is the objective, not the procedure.

### 6.4 Why ODD fits delegated work

TDD and BDD assume the test/scenario author is the code author (or in the
same room). ODD is designed for the case where the author of the objective
and the author of the method are different — which is every delegation from a
primary persona to a specialist, every background dispatch, every user
request assigned to an AI agent.

The objective is the contract that crosses the delegation boundary. The
method is the builder's internal concern. This matches how personas in pOS
actually work.

---

## 7. How AI assistants apply ODD when authoring work

This section is the operational checklist for an AI assistant (especially a
primary persona) structuring a unit of work for delegation.

### 7.1 Order of composition

Author in this order. Do not permute:

1. **Objective first.** State the outcome in one sentence: "X must be true
   when this scope is done."
2. **Constraints second.** State the budget, reversibility class, dependency
   fence, authority bound, and fail-closed direction.
3. **Acceptance third.** Write one deterministic criterion per declared
   behaviour inside the objective. Count behaviours; count criteria; verify
   they match.
4. **Method last — and only if the builder needs hints, not instructions.**
   Marked as "suggested" or "the builder's call to refine." Never in the
   acceptance criteria.

If step 4 feels necessary before step 3, the objective is underspecified.
Go back to step 1 and tighten until the method is obvious from the
objective.

### 7.2 The "how vs what" smell test

Read every line of the work description. For each line, ask: *is this
describing what must be true at the end, or how to get there?*

- "What must be true at the end" → objective or acceptance criterion.
- "How to get there" → method.

Method lines in the objective or acceptance sections are defects. Move them
to a "suggested approach" section marked advisory, or delete them.

### 7.3 The behaviour-count check

Before handing the work to the builder, run:

1. Re-read each objective.
2. Count the declared behaviours (words "and", "also", lists).
3. Count the acceptance criteria.
4. If behaviours > criteria, add criteria until counts match.

This catches the failure mode where one-third of an objective ships
unverified.

### 7.4 Flagged inferences

When the author of the objective has made inferences that the builder should
challenge (budget thresholds, naming choices, category lists), list them
explicitly as "flagged for the builder to challenge." This is not scope
expansion — it is making the author's ungrounded judgments visible so the
builder can call them out rather than silently inheriting them.

Example from the safety-layer proposal:

> **Floor threshold of 1 cent on ruling #1.** Luke said "tunable with floor."
> I inferred a minimum floor of 1 cent to prevent a workspace dialing the
> threshold to zero. If the intent was "tunable without floor," challenge
> and halt.

### 7.5 Halt-and-signal as a first-class option

An objective brief includes explicit halt triggers. If the builder discovers
that the objective cannot be met within the constraints, or that the work
exceeds a declared ceiling (time, scope, dependency), the sanctioned action
is halt-and-signal. Never push-through.

The halt trigger is part of the brief because its absence lets the builder
treat "almost done" as a reason to exceed scope.

---

## 8. Catching ODD violations

This section is for reviewers — human, or another AI reviewing a peer's
delegation brief or completed work. Each item is a deterministic check a
reviewer can run against a brief or an acceptance-criteria list.

### 8.1 Authoring-time violations

The brief is in front of you. It has not been dispatched yet.

1. **Method in acceptance.** Scan every acceptance criterion for verbs that
   describe how rather than what ("uses pytest", "implements visitor
   pattern", "via Pydantic validator"). Every hit is a violation. Rewrite
   as "what must be true."
2. **Behaviour-count mismatch.** Count declared behaviours; count criteria.
   If they don't match, the objective is under-tested.
3. **Missing acceptance.** An objective with no acceptance is not an
   objective — it is a wish. Reject the brief.
4. **Acceptance that relies on judgment.** "The code should be readable."
   "The output should be helpful." These are advisory prose, not acceptance
   criteria. Either replace with a deterministic check or acknowledge it is
   a soft goal outside the acceptance contract.
5. **Procedure in the objective.** The objective says "first X, then Y." The
   objective is the end state; ordering is method. Delete or move to a
   suggested-approach section.
6. **Unbounded scope.** The objective lacks at least one of: budget,
   reversibility class, authority bound. The builder cannot know when to
   halt.
7. **Missing halt trigger.** The brief does not say what to do when the
   work exceeds its ceiling. Add the halt trigger explicitly.

### 8.2 Review-time violations

The work has been built. You are reviewing the diff.

8. **Silent exception branches.** Code paths that handle cases not named in
   the acceptance criteria. If the case is worth handling, it is worth
   naming — re-extend as a new criterion with a test, or remove the branch.
9. **Code for cases no objective names** (positive-case equivalent of #8,
   see §2.5). Platform branches, configuration fields, dependencies, or
   tests that do not map back to any acceptance criterion. Every orphan
   code path is a §2.5 violation. Either re-extend up with a named
   objective or delete the code — "might be useful later" is not a
   backing. For every code block in the diff, point at the criterion it
   satisfies; no criterion = no code.
10. **Acceptance tests that test method.** A test asserting a specific
    implementation detail (class name, internal structure) rather than the
    objective-level behaviour. Acceptance tests should test the observable
    outcome; implementation tests (if any) belong elsewhere.
11. **Acceptance criteria without tests.** A criterion was declared in the
    brief but no test verifies it. Missing tests are missing verification —
    the component has not met the spec regardless of what other tests pass.
12. **Tests that re-assert the method.** A test that says "the function
    returns X" where X is the internal method's return, not the
    outcome-level state, has tested method, not objective.
13. **Advisory rules where structural checks would work.** A docstring says
    "callers should not do Y" but the code permits Y. If Y can be prevented
    structurally (type system, schema, constructor), the advisory is a
    defect — promote to structural.

### 8.3 The two quick refusal rules

If you see only these two, you can catch most ODD violations:

- **"stating 'the test will use pytest' is a violation"** — this is the
  method-in-acceptance smell in its purest form.
- **"stating 'the component will refuse malformed input' is an objective"** —
  this is a well-formed outcome statement with no method prescribed.

Hold these two shapes in mind when reviewing. Most violations look like the
first; most well-formed objectives look like the second.

---

## 9. Quick reference card

For AI agents who have loaded this document once and need a checklist the
next time.

**Authoring a scope:**
1. State outcome as "X must be true."
2. Bound method with budget, reversibility, dependencies, authority,
   fail-closed direction.
3. Write one deterministic acceptance criterion per declared behaviour.
4. Do not prescribe method in the objective or acceptance.
5. Flag inferences explicitly for builder challenge.
6. Include halt trigger.

**Discovering a gap during build:**
1. Do not bury in an exception branch.
2. Promote to a new acceptance criterion (A20-style).
3. Author a test against it.
4. Name the rationale in the commit message.
5. If the gap exceeds the scope's remit, halt and signal.

**Building only what the objectives require (§2.5):**
1. For every branch, dependency, and test you're adding, point at the
   acceptance criterion it satisfies. If you cannot, do not add it.
2. "Might be useful later" is not a backing. Later objectives get
   later amendments.
3. When extending an existing component, audit whether the code you're
   extending was itself objective-backed. Adding tests to a non-backed
   branch propagates the violation.

**Enforcing at runtime:**
1. Prefer structural (Pydantic, schema, constructor) over advisory (prose,
   docstring).
2. The refusal lives in the type system, not in the reader's memory.
3. Where structural is impossible, use acceptance-test-based verification
   and acknowledge the check is not structurally guaranteed.

**Reviewing a brief:**
1. Scan for method-in-acceptance.
2. Count behaviours vs criteria.
3. Check for missing halt trigger, budget, authority bound.
4. Check for advisory-where-structural-would-work.

**Reviewing built work:**
1. Check acceptance criteria all have tests.
2. Check for silent exception branches.
3. Check for code/branches/tests with no backing acceptance criterion
   (§2.5 — the reverse direction of the behaviour-count check).
4. Check tests assert outcome, not method.

---

## 10. Where this fits

ODD is the framework pOS uses for structuring all delegated work — from
primary-persona-to-specialist dispatches, through component builds in the
pOS-v2 rebuild, through user-facing scope-of-work objectives created at a
terminal. It is the operational methodology; the philosophical case is in
the companion document, and worked pOS examples are in the implementation
document.

When the three documents disagree, this one governs the mechanics. The
others are context.
