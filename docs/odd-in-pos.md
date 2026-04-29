# Objective-Driven Design in pOS — Implementation Companion

**Audience:** human developers using pOS or contributing components to it
who have read (or are about to read) `odd-methodology.md` and want to see
how the framework actually practices what that document specifies.

**Status:** illustrative, not normative. When this document and
`odd-methodology.md` disagree, the methodology doc governs. This
document's job is to show the methodology in action, using sealed
components of pOS-v2 as worked examples.

---

## 1. Orientation

Objective-Driven Design (ODD) is the methodology pOS uses to structure
every unit of delegated work. An objective names what must be true when the
work is done; constraints bound the method; acceptance criteria are
deterministic checks that verify the objective. The builder chooses the
method. For the full specification, see `odd-methodology.md`.

pOS uses ODD because every unit of work in the framework is a delegation:
primary-persona to specialist, specialist to background agent, human to
agent, proposal to build. In each case the author of the work and the
author of the method are different entities. The objective is the contract
that crosses that boundary. Whatever machinery the builder uses to satisfy
the objective — library choice, file layout, algorithm — is the builder's
internal concern and not the delegator's business.

This document shows how that contract is authored and enforced in practice
by walking through four of the thirteen sealed components of pOS-v2:

- **safety-layer A1–A20** — the canonical re-extension example.
- **self-upgrade clause (g)** — the canonical structural-enforcement example.
- **cost-governance C14** — a timing-inclusive acceptance criterion.
- **workspace-bootstrap B18** — an objective authored to verify the
  extension protocol itself.

Then: how to add an ODD-compliant component, how to review ODD work, and
the mistakes pOS's own rebuild actually made (which are probably the
mistakes you will also make, given the chance).

---

## 2. The pOS five-gate chain is ODD-shaped

Every sealed component in pOS-v2 passed through the same five gates:

```
research-plan  →  research  →  proposal  →  brief  →  build
```

Each gate produces an artifact; each artifact feeds the next. The
methodology maps onto the chain cleanly:

| Gate | Primary author | What the artifact contains (ODD mapping) |
|------|----------------|------------------------------------------|
| Research plan | Eve | The question set the research will answer. Not objectives yet — the inputs needed to author them. |
| Research | Eve (or delegate) | Evidence. The "is this solvable and how" assessment. Surfaces design options and trade-offs — still not objectives, but the material from which they are distilled. |
| Proposal | Eve | **ODD objectives live here.** Scope, constraints, acceptance criteria. This is the contract Luke approves. |
| Brief | Eve | Operational restatement of the proposal for a background agent (or sub-agent). Contains the same objectives with dispatch detail added (tools, budget, halt triggers). Objectives do not change between proposal and brief. |
| Build | The specialist (usually a background agent) | Code that satisfies the objectives + tests that assert them. Plus a seal commit pinning the component against further change. |

The important structural fact: **acceptance criteria in the proposal are
the objectives**. They are not a checklist a builder runs through as a
courtesy. They are the work definition. A proposal with weak acceptance
criteria is a weak contract, and the build will expose every gap in the
contract as a defect during review.

The seal ritual at the end of the build tests the objectives
deterministically. If `test_A7_*.py` fails, A7 was not delivered regardless
of what the commit message claims. This is why acceptance criteria in pOS
proposals are authored as individual test-shaped statements — they map
1:1 to test functions and cannot hide behind prose.

---

## 3. Worked example: safety-layer A1–A20 (re-extension)

The safety-layer is the foundational component responsible for kill
switches (scope, session, system), the always-ask list, and the
dangerous-operation gate. Its proposal lives at
`docs/rebuild/components/safety-layer/proposal.md` and declares
twenty acceptance criteria grouped by spec clause.

### 3.1 How the criteria group

| Group | Criteria | What they test |
|-------|----------|----------------|
| Kill-switch acceptance (spec clause a) | A1–A5 | Each kill level transitions state within a bounded time budget, writes a row to `kill_events`, emits the right OTel span. A5 covers the pathological case of a wedged scope (slow LLM adapter) and documents the "bounded-time-to-initiate" semantics. |
| Always-ask list acceptance (spec clause b) | A6–A10 | The Pydantic-validated load-time refusal, the gate-check on `commit_external_funds`, the approval-then-activate path, the duration-format floor (`15m` minimum, ruling #4), and the fail-closed behaviour when `OneOnOneChannel` is unreachable. |
| Dangerous-op gate acceptance (spec clause c) | A11–A14 | Stricter gate on top of the ask gate, with threshold-tunable behaviour and approval-binds-to-structural-hash semantics. |
| Integration acceptance (cross-cutting) | A15–A18 | The IPC-wrapping composition must not mutate the orchestrator. OTel must flow through the aggregator's registered provider. `OneOnOneChannel` must refuse `is_group=True` at construction. Zero imports from legacy Ruby machinery. |
| Structural-impossibility acceptance | A19 | Defence-in-depth: monkey-patching the `FrameworkFloorCategory` enum at runtime does not change gate behaviour because the gate reads the validated model, not the enum directly. |

Each one is test-shaped. A1 reads:

> **A1.** Scope kill issued against an active scope transitions the scope
> and its TERMINATE-policy children to `cancelled` within 500ms p95.
> Emits `pos.safety.scope_kill` span with level + reason + source. Writes a
> `kill_events` row.

The test writes itself: fire a scope kill, assert state transition, assert
child cancellation, assert span attributes, assert row, assert timing.
Every clause in the criterion maps to one assertion. No ambiguity, no
judgment call.

### 3.2 A20 — the re-extension

During the build, the builder noticed that the proposal's §5 constraints
section contained the sentence *"Safety always wins on collision with
graceful-degradation. Graceful-degradation records 'superseded by safety'
on its own episode."* That was a promise about behaviour.

But A1–A19 did not include a test for that promise. The collision between
safety and graceful-degradation — what happens if a system-kill is issued
while graceful-degradation has paused the workspace? — was declared as a
constraint, not as a verifiable objective.

The builder had two options:

1. **Bury it.** Write the safety-wins code path, merge, trust the author's
   promise.
2. **Re-extend.** Promote the promise to a named acceptance criterion
   (A20) and write a test against it.

ODD requires option 2. The safety-layer build shipped with:

```
tests/test_safety_beats_degradation.py
```

containing `test_A20_system_kill_supersedes_degradation_pause` and
`test_A20_session_kill_supersedes_degradation_pause`. The commit naming
A20 explicitly cited "the proposal promises it and failure here would be a
contract violation." The foundation-audit flagged this as
"YELLOW (but exemplary)" — the exact ODD pattern working as intended, a
negative case re-extended up the chain as a new positive objective.

### 3.3 Why this matters

Buried as an exception branch, A20 would have had no name in the criteria
audit, would have been invisible to anyone modifying graceful-degradation
six months from now, and would have hidden inside whatever test happened
to cover the kill path. Re-extension produced a file named for the
behaviour, a pair of tests named for the scenarios, and an acceptance
criterion in the seal audit trail. The component can now be reasoned
about from the proposal alone.

**Rule of thumb:** if you are about to write `if x or y` inside existing
code to handle a case you did not originally scope, stop. Ask whether
the case deserves its own acceptance criterion. Usually the answer is
yes.

---

## 4. Worked example: self-upgrade clause (g) (structural enforcement)

Clause (g) of the self-upgrade spec is one sentence:

> Every pOS change included in the upgrade is actually installed — none
> are silently skipped.

This is the canonical case where ODD's structural-over-advisory preference
produces a measurably better design. A weaker framework would ship this as
a rules-file entry — "the upgrade runner must not skip files" — and hope
the runner's author reads it. ODD refuses that. The objective "no change
is silently skipped" becomes a schema-level impossibility.

### 4.1 Walking the transformation

The one-sentence objective produced four concrete structural artifacts in
`self-upgrade/src/self_upgrade/`:

**1. A manifest schema that cannot represent a skipped change.**

`manifest.py` defines a `FileEntry` Pydantic model with a `ChangeKind`
enum (`NEW`, `MODIFIED`, `DELETED`, `UNCHANGED`). Notice what is missing
from that enum: `SKIPPED`. The schema has no way to name a change that was
supposed to happen but didn't. A release author who wanted to skip a file
would have to add the enum value, add schema validation for it, add the
clause-(g) verifier logic to skip it, and get all of that through review.
Four changes to make the forbidden case expressible. The refusal lives in
the type system.

The `@model_validator(mode="after")` on `FileEntry` goes further: a file
declared `change_kind=modified` with matching pre/post SHAs is refused at
load — that configuration is logically incoherent, and the schema will
not permit it to exist as a validated object.

**2. A verifier function that iterates every manifest entry.**

`clause_checks.py::check_clause_g(manifest, live_root)` walks every
`FileEntry` in the manifest. For each entry it computes the actual SHA of
the live file and compares against `expected_post_sha`. Any mismatch goes
into the `mismatches` list; any missing file goes into the `missing` list.
If either list is non-empty, the function returns `ClauseResult(clause="g",
passed=False, ...)` with the deltas attached.

Notice again what is missing: there is no code path that says "skip this
file because the author marked it optional." The verifier does not accept
an exemption list. A file in the manifest must verify or clause (g) fails.

**3. A clause bundle wiring the verifier into the upgrade sequence.**

`run_all_clauses` runs clause (g) alongside clauses (a) through (f). The
bundle returns a `ClauseBundle` whose `all_passed` property is `True` only
if every clause passed. Rollback triggers when any clause fails. The
caller in `upgrade.py` cannot finish an upgrade without the bundle
passing; there is no back-channel path that skips the check.

**4. Tests that assert the impossibility.**

`tests/test_clause_checks.py` and `tests/test_manifest.py` cover:
the manifest refuses a malformed `change_kind=modified` entry at load, the
verifier reports mismatches on tampered files, the verifier reports
missing files, the bundle rolls back on any clause failure. Together
these tests *prove* the one-sentence objective — not that the code looks
like it satisfies it, but that code attempting to satisfy it any other way
would fail.

### 4.2 What this buys

A rules-file version of clause (g) depends on three readers (release
author, runner author, future modifier) each reading, believing, and
remembering the rule. Three chances to forget.

The structural version depends on one thing: the type system. The enum
has no `SKIPPED`. There is no path to a skipped file that does not
require refactoring the schema, the verifier, and the bundle. The refusal
is in the data, not in the reader's memory.

**Rule of thumb:** if you find yourself writing "the caller must not do
X" in a docstring, ask whether you can make X unrepresentable instead.
`@model_validator` is your friend; a missing enum value is your friend;
a constructor that raises on invalid inputs is your friend.

---

## 5. Worked example: cost-governance C14 (timing-inclusive criterion)

Most acceptance criteria describe a state: "after X, Y is true." Some
criteria also need to describe *when* that state must become true — or,
more subtly, the shape of the state over time. C14 from cost-governance is
one of those.

The objective: when a scope's prospective reservation would push aggregate
spend past 80% of any ceiling, the user should be warned — exactly once,
not repeatedly per debit.

The criterion as written:

> **C14.** When a prospective reservation would push aggregate spend ≥ 80%
> of any ceiling (session or rolling), the ledger emits
> `pos.cost.ceiling_warning` and dispatches a single notification via the
> `OneOnOneChannel` (group-channel refusal inherited). The warning fires
> **before the reservation is written** — so a scope that activates at 85%
> of cap triggers the warning once, not repeatedly per debit.

Three behaviours are packed into one criterion here, and the timing matters
as much as the behaviours themselves:

1. **The trigger is the prospective-reservation math**, not the actual
   debit. This means the warning fires at activation, not mid-scope.
2. **The emission precedes the ledger write.** A test has to check both
   "the warning was emitted" and "the warning happened before the row
   appeared in `reservations`" — a sequencing assertion.
3. **Once, not per-debit.** The fire-once semantics matter because the
   obvious buggy implementation is to re-check the threshold on every
   `BudgetDebited` event, which would spam the user across a scope that
   sits at 85%.

All three are testable. `tests/test_throttle_warning.py` (named in the
proposal's §6) has to assert the 80% trigger, the pre-write ordering, and
the fire-once behaviour across multiple debits on a single scope.

### 5.1 Why this shape is worth copying

A naive version ("the system warns the user when approaching the
ceiling") fails every ODD test: who decides "approaching" (method-
dependent judgment), before or after the write (unspecified), once or
repeatedly (unspecified), what channel (unspecified — opens the door to
group-chat leaks).

C14 pins all four: "≥ 80%" is deterministic (and C15 pins configuration
and refuses out-of-range values at load); "before the reservation is
written" is explicit sequencing; "once, not repeatedly per debit" names
the failure mode inside the criterion; "via the `OneOnOneChannel`"
inherits the safety layer's security boundary rather than re-declaring
it.

**Rule of thumb:** if a behaviour has a "this must happen at time T" or
"this must happen N times" character, the timing and count are part of
the criterion, not separate concerns. The test will assert them anyway;
the criterion should declare them so the reader does not have to guess.

---

## 6. Worked example: workspace-bootstrap B18 (verifying the protocol)

The workspace-bootstrap component is the framework that composes the ten
sealed foundational components into a running orchestrator, plus the
published extension protocol through which Phase 4+ components register
without amending bootstrap. The tricky ODD question here: *how do you test
that a protocol is actually extensible?*

You could write a criterion like "bootstrap supports adding new
contributions without code changes." That is not an ODD criterion — it is
a wish. "Supports" is unverifiable. "Without code changes" is not even a
state; it is a negative historical claim about a diff that has not been
taken yet.

B18 solves this by making the extension act itself into a test fixture:

> **B18.** Synthetic Phase 4 contribution: a mock `onboarding_adapter`
> module defines a `Contribution` subclass with metadata
> `{name: "onboarding", phase: "after_orchestrator_ready",
> after: ("self_correction",)}`. Adding one line to the test workspace's
> `bootstrap.yaml` enables it; the framework discovers, validates, orders,
> and invokes `contribute(host)`. **Zero change to bootstrap's code.**

What makes this a well-formed ODD criterion:

1. **The extension is a real, runnable module** — not a mock that returns
   a fake value, but a module that actually implements the `Contribution`
   protocol. If the protocol is wrong, the module fails to import or run.
2. **The enablement is a real config change** — one line to
   `bootstrap.yaml`. If the manifest parser is wrong, the line fails to
   parse.
3. **The framework's response is observable** — discover, validate, order,
   invoke. Each of these has a measurable outcome: did the name appear
   in the DAG, did the ordering call place it after `self_correction`, did
   `contribute(host)` run.
4. **The "zero change to bootstrap's code" clause is a diff assertion.**
   The builder runs `git diff` against the bootstrap source tree and
   asserts empty. B20 reinforces this at the seal level:
   `git diff --stat ac48a7b..<bootstrap-seal>` shows only
   `workspace-bootstrap/` changes.

B19 is the negative-case partner: the same synthetic contribution with an
intentional cycle (`after: ("self_correction",),
before: ("observability_aggregator",)`) trips `-32084
BOOTSTRAP_ORDERING_CYCLE`. The protocol must fail loudly and nameably on
the contract violation, not silently tolerate it.

### 6.1 The pattern B18 teaches

When an objective is "the thing is extensible," the ODD move is: write a
synthetic extension, add it through the public protocol, assert the
framework behaved as promised, then assert the diff is empty. A criterion
that just says "the protocol is extensible" is untestable; B18 is
test-shaped because the test is the extension act itself.

This shape generalises. Any time a component declares "X is configurable,"
"Y is pluggable," or "Z extensibility," the question is: can a test
*exercise* that configurability with a synthetic contribution and assert
the outcome? If yes, write the criterion that way. If no, the feature is
probably not actually configurable — it is just presumed to be.

B25 (added in amendment #17) is the framework-internal complement to B18:
it names the `Phase` enum values as the framework-internal phase set that
bootstrap's own adapters register under, distinguishing a bootstrap
amendment (which may add a phase-enum value, as Amendment #4's
`first_run_scaffold` did) from a Phase 4+ contribution (which registers
against the existing enum values via the external-extension protocol).
B18's "zero change to bootstrap's code" scopes to external-contribution
registration; B25 covers the framework-internal phase surface.

---

## 7. Adding an ODD-compliant component to pOS

If you are contributing a new component — a Phase 4+ extension or a
foundational amendment (rare, gated) — the rhythm is the five-gate chain
from §2 above. The following is the human-targeted version.

### 7.1 Research plan

State the questions your research needs to answer. You are not writing
objectives yet. Typical questions: what integration points does this
component have with sealed components, what constraints does the spec
impose, what trade-offs exist between candidate designs, what does
"done" look like for the minimum viable version.

Submit to Eve. Eve either approves or redirects with clarifying questions.

### 7.2 Research

Answer the questions. Produce evidence. Surface unknowns and design
options. Where a decision requires Luke's judgment, isolate it as a
numbered ruling question — do not assume.

The output is a research document that gives a proposal author enough
material to author objectives confidently. You are still not writing
objectives.

### 7.3 Proposal — where ODD becomes load-bearing

Now you write objectives. Author in this order (do not permute — the order
is in `odd-methodology.md` §7.1):

1. **Objective first.** State the outcome in one sentence per acceptance
   criterion. "X must be true."
2. **Constraints second.** Budget, reversibility class, dependency fence,
   authority bound, fail-closed direction. Specifically: what sealed
   components may you consume (never amend), what error-code range do you
   reserve, what's the time budget for the build.
3. **Acceptance third.** One deterministic criterion per declared behaviour.
   Timing and count belong *in* the criterion, not separately. Negative
   cases worth preventing are their own criteria (A19, B19, the
   structural-impossibility family).
4. **Method last — and only as suggestion.** Mark it "suggested" or "the
   builder's call." Never in an acceptance criterion.

File layout, class names, algorithm choices — keep them in a "suggested
approach" section or delete them. If a structural constraint is
load-bearing (e.g. "must use the IPC-wrapping pattern, not orchestrator
amendment"), that is a *constraint*, not a method. It bounds the method
without prescribing it.

At the end of the proposal, flag your inferences explicitly. Anywhere you
inferred a detail Luke did not explicitly rule on (a threshold, a naming
choice, a category count), list it under "flagged for the builder to
challenge." This is the signal that says "I made a judgment call here —
challenge it if the data argues otherwise." Safety-layer §8 has eight
such inferences listed; the builder used one of them to halt and
re-verify a scope-of-work surface before assuming it existed.

### 7.4 Brief

Eve (or the proposal author) drafts the brief at dispatch time: the
proposal restated for a background agent, with dispatch detail added
(tools, halt triggers, budget). Objectives do not change between
proposal and brief. If they do, the proposal was wrong and should be
corrected first. The brief is a dispatch-time artifact — produced when a
builder is dispatched, consumed by that builder, not retained as a
committed canonical artifact. The canonical artifact set that lives in
the repo is proposal + plan + shipped code + seal. (This matches the
`scope-only-dispatch` CDC — the dispatch carries objective, scope,
constraints, halt triggers, and ODD-check; the builder's own plan under
`docs/rebuild/plans/` is the paper trail the repo keeps.)

### 7.5 Build

The background agent writes code that satisfies the objectives and tests
that assert them. The test-to-criterion mapping should be 1:1 — one test
function per criterion, named after the criterion (`test_A7_*`,
`test_C14_*`). Anyone reviewing the build should be able to grep the test
tree by criterion ID and find the proof.

During build: if you discover a gap (a scenario not covered, a collision
not anticipated, a negative case that passes the letter but violates the
spirit of the criteria), re-extend. Promote the gap to a new acceptance
criterion, write a test, cite the rationale in the commit. Do not bury as
an exception branch. A20 is the canonical case.

If the gap is too large to re-extend inside the current scope — the
original author needs to re-scope — halt and signal. Do not push through.

### 7.6 Seal

The final commit pins the component's `SEAL_COMMIT` into a sidecar file
(`.seal-commit` or equivalent). The seal test
(`tests/test_no_sealed_amendments.py`) diffs `BASELINE..SEAL_COMMIT` at
audit time — if any sealed component was touched outside your own
package, the audit fires red. The seal ritual is the deterministic gate
that says "this component's objectives are locked, and the foundation it
was built on is unchanged."

---

## 8. Reviewing ODD-compliant work

You may be reviewing a proposal before dispatch, or a completed build
before seal. The questions are different.

### 8.1 Reviewing a proposal

Before the work leaves Eve, walk the acceptance criteria with these checks:

- **Method-in-acceptance.** Scan every criterion for verbs that describe
  how rather than what. "Uses pytest." "Implements visitor pattern." "Via
  Pydantic validator." Every hit is a violation. Rewrite as outcome.
  (This is the single most common ODD defect in pOS's own history — see §9.)
- **Behaviour-count mismatch.** Count the declared behaviours in each
  objective (words "and," "also," bulleted lists). Count the acceptance
  criteria. If criteria < behaviours, the objective is under-tested.
- **Missing halt trigger.** The proposal should say what happens when the
  work exceeds its ceiling (time, scope, dependency). Absence of a halt
  trigger lets the builder treat "almost done" as a reason to exceed scope.
- **Missing constraints.** Every proposal needs a budget, a reversibility
  class, a dependency fence, an authority bound. Absence of any of these
  is unbounded scope.
- **Advisory where structural would work.** A criterion that says "callers
  should not do Y" but the code will permit Y. If Y can be prevented
  structurally (type system, schema, constructor), the advisory is a
  defect — promote to structural. Clause (g) is the reference pattern.

### 8.2 Reviewing a build

The code and tests are in front of you. The diff is ready.

- **Every criterion has a test.** Grep the test tree for each criterion
  ID (A1, C14, B18, etc.). Missing tests = missing verification
  regardless of what other tests pass.
- **Tests assert outcome, not method.** A test that asserts "the function
  returns an `AskGateResult` with `state == BLOCK`" is testing the
  criterion. A test that asserts "the function calls
  `model_validator` twice" is testing the method. The second shape is a
  brittle test and an ODD defect.
- **No silent exception branches.** Look for code paths that handle cases
  not named in the acceptance criteria. If the case is worth handling, it
  is worth naming — re-extend as a new criterion with a test, or remove
  the branch.
- **Structural enforcement where applicable.** Pydantic schemas, enum
  constraints, constructor raises. Advisory docstrings where structural
  would work are defects.
- **Seal integrity.** `git diff --stat BASELINE..SEAL_COMMIT` should show
  only changes under the component's own package path. Any delta to a
  sealed component fails the audit.

### 8.3 What the audit trail looks like

For a sealed component, the audit trail consists of:

1. The proposal document with numbered acceptance criteria.
2. The brief (usually closely matching the proposal).
3. The commit history from baseline to seal, with commit messages citing
   criterion IDs for each acceptance.
4. The test tree with files named for behaviours and test functions
   named for criterion IDs.
5. The seal-test file pinning `SEAL_COMMIT` for future-amendment
   detection.
6. The foundation-audit entry rating the component GREEN / YELLOW / RED
   against enumerated acceptance criteria.

The foundation-audit for pOS-v2's first thirteen components landed at
`93.6% : 6% : 0.5%` (GREEN : YELLOW : RED). The methodology does not
guarantee GREEN dominance — the audit discipline does. But the
methodology makes the discipline possible: when criteria are test-shaped
and map 1:1 to tests, an auditor can verify correctness without reading
every line of code.

---

## 9. Common mistakes observed during pOS's rebuild

These are failures Luke caught (or the foundation audit flagged as YELLOW)
during the thirteen-component build. If you are authoring proposals or
reviewing them, watch for these.

### 9.1 HOW-prescriptions in proposals

Eve's drafts occasionally leaked method into acceptance criteria —
a specific Pydantic validator named in a criterion, a file name buried
in an objective, a "the component will use X" where X is a library choice.
Luke caught several of these by reading the proposal with the ODD checks
in mind and pushing back.

**The fix in every case:** rewrite the criterion as the observable outcome
and move the library / validator / file name to a "suggested approach"
section (or delete it entirely if the builder does not need the hint).

**Why this is tempting:** the author has often already thought through the
method while writing the research document. Carrying the method forward
into the criterion feels like finishing the thought. In ODD terms it is
over-specification: the criterion now tests the method rather than the
outcome, which couples the test to the implementation and prevents the
builder from making the call they were delegated to make.

### 9.2 "Suggested file layout" over-specification

The workspace-bootstrap proposal originally leaned into a detailed
suggested file layout — class names, submodule boundaries, the shape of
the framework's internals. Luke flagged that the layout was over-specified
for an acceptance contract: the proposal was telling the builder *how* the
framework should be structured rather than *what state* it should produce.

The corrected version confined the file layout to a "suggested" block
marked as the builder's call to refine. The authoritative surface is the
acceptance criteria; the layout is advisory. If the builder chooses a
different internal structure that satisfies all criteria, that is the
builder's right.

**The rule:** file structure is almost always method. It belongs in the
"builder's judgement to adjust" section unless it is load-bearing for a
cross-cutting constraint (e.g. "tests must live under `tests/`").

### 9.3 Proposal-doc-stale-against-code drift

Foundation-audit item #12: workspace-bootstrap proposal §3.2 listed
`after=safety_layer` on `cost_governance`, but the actual adapter used
`after=("observability_aggregator",)` because the integration test
required the inverse. The code and test were correct; the proposal
document was stale.

This is a small, common drift. Method-level details the proposal tried
to pin (ordering of adapter declarations in an integration) turned out to
need builder adjustment during the build. The right corrective move is
to update the proposal when the ruling changes, or — better — leave
method-level details out of the proposal entirely so the drift can never
occur.

**The rule:** if a detail in a proposal is at risk of changing during the
build, it is probably method and should not be in the proposal's
authoritative surface at all.

### 9.4 Inferences carried as assertions

An author who has thought deeply about a component sometimes carries
their inferences as assertions in the proposal — stating a
threshold as if Luke had ruled on it, naming a category as if it were
settled, assuming a sealed surface exists without verification.

The discipline for this: **flag inferences explicitly**. Safety-layer §8
lists eight of them — the floor threshold of 1 cent, the 15-minute ask
timeout minimum, the seven framework-floor categories, the
`ScopeSpec.structural_hash()` surface (which was flagged as "verify
against code before assuming"), and so on. Any of these could have been
the author's error; naming them in a flagged block invites the builder to
halt and confirm rather than silently inherit.

The failure mode without flagged inferences: the builder inherits the
author's judgment silently, the ruling later turns out to be different
from Luke's actual preference, and the build has to be unwound. Flagged
inferences are the cheap fix — seconds to write, hours saved if they
catch a misreading.

### 9.5 "Verify against code" rather than parroting the spec

Several YELLOW findings trace to proposals that assumed a sealed-component
surface existed without verifying. The scope-of-work's
`structural_hash()` method, the orchestrator's `request_stop()`, the
`OneOnOneChannel` constructor's `is_group=True` refusal — each was
referenced in downstream proposals, and each needed to be verified against
the actual code before the proposal could be confident in the reference.

The discipline: if a proposal references a surface on a sealed component,
the author should have read the code, not the prior proposal. "I assume
this surface exists because the earlier proposal promised it" is the
exact failure mode ODD's verification-discipline rule (from
`odd-methodology.md`) guards against.

### 9.6 Timing omitted from criteria that need it

An early cost-governance draft had a throttle criterion that read "a
warning is emitted when spend approaches the ceiling." It did not say
*when* (before or after the ledger write), *how often* (once or
per-debit), or *at what threshold* (the 80% came in later). Each of those
omissions would have produced a working-but-wrong implementation.

The C14 that shipped is the corrected shape: threshold, ordering,
fire-once, channel all in the criterion text. The test that verifies C14
can assert all four; the author did not have to choose which of the four
the test covered.

### 9.7 Code for cases no objective names

(`odd-methodology.md` §2.5 is the governing rule; this subsection
documents the first pOS-v2 incident that surfaced the need to state it
explicitly.)

During the 2026-04-22 build session an unrelated review surfaced that
pos-v2 shipped Linux/systemd/systemctl code paths across twelve Python
files — service-manager templates, platform-branched installers,
rollback helpers. No objective in spec v1.0, v1.1, or v1.2 names Linux
as a supported platform. The code was added incidentally because
"POSIX-ish shells make it easy" — a reason, but not a contract.

Worse: amendment #6 (namespaced-labels-and-bootout) landed WITH new
Linux acceptance criteria (AC3 systemd naming, AC4's Linux stop/
reload/start) to verify behaviour in code that shouldn't have existed
in the first place. The amendment's author saw the Linux branch in the
pre-existing code and wrote ACs around it without checking whether
Linux was a named objective at the spec level. The amendment
perpetuated a §2.5 violation by formalising it with acceptance tests.

The sequence of ODD failures:

1. Original build added Linux branches without a Linux objective.
   (§2.5 violation — invisible to review because no one ran the
   "reverse direction" of the behaviour-count check: every branch
   back to a criterion.)
2. An amendment review scanned the diff for method-in-acceptance
   (§8.1.1) and silent exception branches (§8.2.8) and found the
   amendment complied with those rules as worded.
3. But the review DID NOT ask "does the code this amendment extends
   have a backing objective?" Because §2.5 was not a named rule yet.
4. The amendment shipped, its Linux tests now lock in Linux-handling
   as de-facto "supported" — harder to remove later than if the
   original leak had never been formalised.

What the corrected process would have looked like:

- At original build: the behaviour-count check runs in both
  directions. The builder's diff has `_SYSTEMD_TEMPLATES` and a
  `plat == "linux"` branch. The reviewer asks: "which acceptance
  criterion does this satisfy?" None. The branch is deleted or the
  objective is added.
- At amendment time: the amendment author reads the code being
  extended and notices Linux has no objective backing. The amendment
  halts-and-signals back to the owner: "the code I'm extending
  contains §2.5 violations; should this amendment's scope expand to
  remove them first, or should it remove Linux from the amendment's
  surface?" Owner rules; work proceeds against the ruling.

**Rule of thumb:** for every line of code in a diff, point at the
acceptance criterion it satisfies. When extending existing code, audit
the code being extended by the same rule — do not propagate
violations. "It was already there" is not a backing criterion; the
amendment's author carries responsibility for what lands at HEAD, not
only what the amendment added to whatever came before.

### 9.8 Byte-content verification on state-mutating amendments

(`odd-methodology.md` §8.2.14 is the governing rule; this subsection
documents the first pos-v2 incident that surfaced the need to state
it explicitly.)

Workspace-sync amendment #57 (Bundle α — resolver cost overhaul)
shipped with 101 passing tests verifying verdict shape — the resolver
produced the right `entry_status: "ancestor_match"` enum, the audit
row was emitted, the apply step output `[workspace-sync] applied:
<ref>`. Live-tested against pos3, the apply step ran clean: the
verdict was right, the audit was right, the message printed. The
files on disk were unchanged.

The bug: `resolved_content_path: null` in the NN ancestor-detection
path let `apply` silently no-op. Tests asserted the verdict
structure; no test read a post-apply file from disk and compared
bytes against canonical's expected blob.

Amendment #59 (α-hotfix) closed AC.α-hotfix.1: NN-resolved entries
actually overwrite workspace files. Amendment #60 (α-hotfix-2)
closed four further correctness bugs of the verdict-without-stage
class, identified once the byte-content discipline was applied.

The lesson: for any amendment whose effect is to mutate workspace
files (sync, upgrade, scaffold, install), verdict-shape tests are
necessary but not sufficient. At least one test must read the
post-mutation file from disk and byte-compare against the expected
blob. The verdict describes the intent; only on-disk content
describes the effect.

### 9.9 Relocate vs eliminate — the workspace-sync D-decision

(`odd-methodology.md` §5.1.1 is the governing rule.)

The 2026-04-27 first-principles review of workspace-sync produced
two structurally-sound alternatives:

- **D′** — keep the current flat layout; rely on the existing
  `.gitignore` to keep workspace state out of canonical's git
  tree; reduce `pos-sync` to `git fetch + git merge --ff-only`
  against a tracking branch.
- **D** — directory-split the workspace into `framework/`
  (git-tracked, pulled from canonical) and `workspace/`
  (workspace state, never pulled).

Both are nominally structural — neither relies on a runtime rule
the operator must remember. But the relocate-vs-eliminate test
distinguishes them:

- D′ relocates the failure class. A future maintainer who
  introduces a new state-file pattern must remember to add it to
  the gitignore. Forgotten gitignore entries silently track
  workspace state into canonical, exactly the failure mode the
  mechanism was supposed to prevent. The mechanism shifts the
  burden from "remember the sync rule" to "remember the gitignore
  rule"; the failure class is preserved.
- D eliminates the failure class. State files written under
  `workspace/` cannot be tracked by canonical's pull because
  canonical's pull operates against `framework/`. The wrong-
  directory mistake is structurally unreachable; no future
  maintainer can recreate the failure class without refactoring
  the directory split itself.

Luke ruled D over D′. The decision rationale: even though D′
captures ~80% of D's benefit at ~20% of the migration cost, the
~20% D adds *is* the elimination guarantee, and that guarantee
is the property the sync mechanism's robustness depends on.

The lesson: among structural options, prefer the one that makes
the failed state unrepresentable. "Structural mechanism in place"
is necessary; "failure class no longer reachable" is the goal.

### 9.10 Bug-pattern-driven architectural review

(`odd-methodology.md` §4.5 is the governing rule.)

Workspace-sync's α stage shipped at #57. Live-test against pos3
surfaced the byte-content bug (§9.8 above); amendment #59 closed
the NN-resolved-overwrite gap as α-hotfix-1. Once the byte-content
discipline was applied to the rest of the resolver, four sibling
correctness bugs of the same class surfaced — each a `verdict-
without-stage` failure where the resolver emitted the right
verdict but never produced the staged file. Amendment #60 closed
all four as α-hotfix-2.

At that point the pattern itself was the signal: two hotfix
amendments against the same code area within hours, with the
sibling failures sharing a single root cause. The signal said
"the gap is at the architecture level, not the AC level." Per
§4.5, the response is to pause hotfix iteration and first-
principles the design.

The first-principles review (2026-04-27) commissioned a research
dispatch evaluating four design alternatives (A′, B, C, D) plus
the status-quo continuation. The output: D′ (gitignore-based)
and D (directory-split) emerged as the structurally-sound
alternatives. The relocate-vs-eliminate test (§9.9 above) ruled
D over D′. D commitment closed the architecture-level gap; no
further hotfix in the α chain landed.

The lesson: 2 hotfixes in the same area is the structural signal
that the architecture is wrong-shaped. The hotfix loop is a
patch — necessary in the short term, evidence of an architectural
gap in the medium term. First-principles review at the 2-hotfix
threshold is the sanctioned response; pushing through to a 3rd
hotfix without review is the failure mode.

---

## 10. Frozen-vs-floating BASELINE convention (per-invariant BASELINE)

Seal-diff tests pin a `BASELINE` SHA that scopes the window a test
diffs against. Historically every `BASELINE` in pos-v2 *floated* — it
advanced to the pre-amendment tip on every amendment, so the test's
diff window was "what changed across the current amendment." That
pattern works for per-component contamination checks but causes two
problems when applied uniformly:

1. **Coordination serialisation.** hands-off-lifecycle's H19 test uses
   a whole-repo diff. Under a floating BASELINE, every amendment of
   any component has to advance H19's BASELINE even when hands-off-
   lifecycle itself is untouched. This serialises all amendment
   development behind one edit.
2. **Invariant-proof erosion.** A structural check authored in
   amendment *N* that asserts "amendment N's fidelity held" stays
   valid only as long as its BASELINE window hasn't moved. Advancing
   BASELINE on subsequent amendments re-scopes the check to a later
   window and silently weakens the proof.

Amendment #23 (frozen-H19 BASELINE + per-invariant-BASELINE convention)
codifies the two patterns that resolve both.

### 10.1 Frozen BASELINE — for cumulative-admissibility checks

A **frozen** BASELINE is pinned at a project-wide anchor (typically
project-start) and never advances for the lifetime of the component's
test file. The test's diff window expands monotonically. The check
proves a cumulative invariant: "across all project history to date,
no unadmitted surface ever appeared." New admissions land via an
explicit edit to the `allowed` set; existing admissions stay.

**When to use.**

- The test's fidelity target is cumulative, not per-amendment (e.g.
  surface-introduction checks, never-retracted rule lists,
  accumulated-ledger assertions).
- The test's diff window is cross-component (whole-repo) — floating
  BASELINE creates coordination friction between amendments that
  don't semantically interact.

**Canonical example: hands-off-lifecycle's H19.**
`hands-off-lifecycle/tests/test_cross_cutting.py`'s `BASELINE` is
pinned at `3780603` (pre-amendment-#1 tip). The `allowed` set is the
cumulative list of top-level dirs + top-level files ever admitted.
Any new amendment that introduces a new bucket adds one entry to
`allowed`; no amendment ever moves BASELINE.

### 10.2 Floating BASELINE — for per-component contamination checks

A **floating** BASELINE advances to the pre-amendment tip every time
the component's own source is touched by an amendment. The test's
diff window stays narrow — only the current amendment's changes are
visible. The check proves a per-amendment invariant: "during this
amendment's window, only the declared surfaces were edited."

**When to use.**

- The test's fidelity target is per-amendment contamination (e.g.
  `tests/test_no_sealed_amendments.py` on every sealed component).
- The test's diff window is scoped to the component's own directory
  plus declared cross-component admissions.

**Canonical example: any sealed component's `test_no_sealed_amendments.py`.**
Each advances its BASELINE only when the component is itself in
scope for the current amendment. A component that sits out several
amendments keeps its BASELINE pinned to its last-touch tip, and its
test stays trivially green.

### 10.3 Per-invariant BASELINE (frozen-both-endpoints) — for point-in-time invariant proofs

A **per-invariant** BASELINE is a pair of function-scoped SHA
constants (`BASELINE` + `SEAL`) that pin a specific assertion to the
exact window it was authored to prove. **Both endpoints are frozen**
in code — neither floats with subsequent amendments. The test's
module-top BASELINE (floating or frozen) is untouched. Once
authored, the pair never moves unless the invariant itself is being
restated.

The "frozen-both-endpoints" wording is load-bearing. Pinning only
the BASELINE while leaving the SEAL endpoint resolved through a
floating sidecar (e.g. via a `_seal_commit()` helper) re-introduces
the widening-pressure failure class: every amendment that legitimately
advances the component's SEAL_COMMIT sidecar drags the per-invariant
test's upper bound forward, and any path admitted by sibling
amendments enters the per-invariant test's window. Amendment #69
(`docs/rebuild/plans/ac-m-s-structural-redesign.md`) documents the
six-amendment widening tax this defect produced on AC.M.S before
conversion to frozen-both-endpoints.

**When to use.**

- The invariant is point-in-time: "during amendment *N*'s window,
  property *P* held."
- Subsequent amendments may legitimately break the property outside
  amendment *N*'s window (e.g. an AC that forbade edits to a
  directory is later amended to allow them) — pinning keeps the
  original proof intact while letting the directory evolve.

**Pattern (code template — frozen-both-endpoints):**

```python
# Both endpoints are constants. Neither is read from a floating
# sidecar or computed at test-run time. The pair pins amendment N's
# window for the project's lifetime; subsequent amendments cannot
# re-scope this assertion.
_AMENDMENT_9_BASELINE = "b9e1f96"
_AMENDMENT_9_SEAL = "4f8b933"


def test_AC7_no_telegram_interface_src_edits() -> None:
    """AC7 (amendment #9): no edits to telegram-interface/src/
    landed in amendment #9. Pinned to amendment #9's exact window.
    """
    out = subprocess.check_output(
        ["git", "diff", "--name-only",
         f"{_AMENDMENT_9_BASELINE}..{_AMENDMENT_9_SEAL}",
         "--", "telegram-interface/src/"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]
    assert changed == [], (
        "amendment #9 edited telegram-interface/src/ — AC7 halt-signal. "
        f"Changed paths: {changed}"
    )
```

The convention default for new per-invariant assertions is
**frozen-both-endpoints**. A test that resolves either endpoint
through a sidecar / live-resolver / `HEAD` fallback is not a
well-formed per-invariant test — it's a hybrid of the per-invariant
shape and the §10.2 floating-window shape, and the two protect
different invariants. See AC.M.S → AC.MS-fix migration in amendment
#69 for the worked example of converting a hybrid to the canonical
frozen-both-endpoints shape.

**Canonical example: AC7 on telegram-interface.**
`telegram-interface/tests/test_no_sealed_amendments.py::test_AC7_no_telegram_interface_src_edits`
(introduced at `7d27f00` as amendment #21's corrective). The
amendment-#9 AC7 invariant is pinned to `b9e1f96..4f8b933` for the
project's lifetime. Amendment #21's legitimate edits to
`telegram-interface/src/` under AC:S3 don't re-violate AC7 because
the pinned window closes before amendment #21 begins.

**Sub-pattern: placeholder-sentinel for tests authored alongside
their own amendment.** When a per-invariant test must include the
amendment's *own* seal-diff window, the author faces a chicken-and-egg
problem: the test's frozen SEAL endpoint is the seal commit, but the
seal commit references the test that locks the SEAL endpoint. The
canonical resolution is a placeholder-sentinel constant
(`__POST_SEAL_CORRECTIVE__`) paired with a sentinel-branch early-return
in the test body; the corrective commit landed immediately after seal
fills the constant with the actual SHA. The test stays well-formed
(both endpoints are constants once filled) and the seal-window
self-reference is broken without re-introducing the floating-SEAL
defect §10.3 above forbids.

```python
_AMENDMENT_N_BASELINE = "abc1234"  # filled at plan-author time
_AMENDMENT_N_SEAL = "__POST_SEAL_CORRECTIVE__"  # filled by post-seal corrective commit


def test_AC_X_invariant_pinned_to_amendment_N() -> None:
    if _AMENDMENT_N_SEAL == "__POST_SEAL_CORRECTIVE__":
        # Pre-corrective state: SHA not yet known. Test is authored
        # but inert until the corrective commit fills the sentinel.
        return
    # ... normal frozen-both-endpoints body using both constants ...
```

Canonical example: AC.MS-fix.S (amendment #69) — see
`docs/rebuild/plans/ac-m-s-structural-redesign.md` §14 for the
worked corrective-commit mechanics.

### 10.4 Migration guidance

- **New invariants** use §10.3 by default. If the invariant's fidelity
  is cumulative, use a §10.1-frozen module-top BASELINE instead.
- **Existing invariants** are not retrofitted wholesale. When an
  amendment touches a sealed-component test file for other reasons
  (tuple widening, a new AC), the author is free to pin any existing
  point-in-time invariant at that time. No audit sweep; conversion
  is opportunistic.
- The `pos-amend` tool's manifest accepts a per-component
  `frozen_baseline: bool` field (introduced amendment #23). When
  `true`, `apply` skips the module-top BASELINE literal bump for
  that component while still advancing sidecars and tuples. Use
  this on every amendment that affects hands-off-lifecycle (or any
  other future frozen-BASELINE component).

### 10.5 Parallel-development note

Frozen H19 + per-invariant BASELINE together unlock disjoint-component
parallel amendment development: two amendments touching non-overlapping
sealed components no longer race on the hands-off-lifecycle BASELINE
literal, and no in-flight point-in-time invariant-proof re-scopes
when the other amendment lands. See
`.scratch/claude-output/pos-v2-parallel-dev-research.md` §3 for the
full classification (Class A — parallel under current rules; Class B —
parallel post-amendment #23; Class C — structurally serial).

---

## 11. Where to go next

- `odd-methodology.md` — the operational specification. When this doc and
  it disagree, it wins. Read it for definitions, the authoring order
  (§7.1), the catching-violations checklist (§8), and the
  quick-reference card (§9).
- *Companion doc: the methodological argument.* If published, it covers
  why ODD fits delegated AI-assisted work — the case against TDD and BDD
  for this use case, the relationship to first-principles thinking, and
  why structural-over-advisory matters more in LLM-executed work than in
  human-executed work.
- The sealed components themselves. Read their proposals and compare
  against their test trees. The 1:1 mapping between criteria and tests
  is the best evidence that the methodology works in practice.

---

## 12. Closing

ODD is not a new idea — outcome-based delegation is older than software.
What pOS contributes is concrete operational discipline: the five-gate
chain, the criterion-to-test 1:1 mapping, the re-extension rule, the
structural-over-advisory preference, the seal audit. Each piece is
small. Together they produce a codebase where every behaviour has a
name, every name has a test, and every test asserts the behaviour
rather than the method.

Write objectives as outcomes, not procedures. Count behaviours, count
criteria, make them match. When you discover a gap during build,
re-extend. Prefer structural refusals over advisory rules. Test the
outcome; let the builder choose the method.
