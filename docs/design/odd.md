# Objective-Driven Design (ODD) in loam

**Audience:** contributors reading or authoring work inside a loam
workspace. This is the short form. It tells you what ODD is, why
loam practices it natively, and how to read or author an acceptance
criterion when you contribute.

If you are looking at a brief, an issue, or a pull-request description
and trying to decide whether it is well-formed, this document is
where to start.

---

## What ODD is

Objective-Driven Design defines every unit of work by its **observable
outcome**, not by a sequence of steps. Work is assigned as:

- an **objective** — a statement about the state of the world that
  must be true when the work is done,
- a set of **constraints** — bounds the method must respect (budget,
  reversibility, allowed dependencies, authority, fail-closed
  direction),
- one or more **acceptance criteria** — deterministic checks that
  confirm the objective is met,
- and **method is the builder's call.** The author of the objective
  does not prescribe the implementation.

The one-sentence test:

> An objective is a state of the world you want true; an acceptance
> criterion is a deterministic check that the objective is met.

If a work description does not fit that shape, rewrite it until it
does.

---

## Why loam practices ODD

Two reasons.

**First, loam is a Claude-attached harness, and the natural shape of
its work is *delegation*.** A primary persona dispatches a specialist;
a user requests a long-running task; a background agent picks up a
scope. In every case, the author of the objective and the author of
the method are different people (or the same person at different times,
which amounts to the same thing). ODD is the methodology designed for
exactly that gap: the objective is the contract that crosses the
delegation boundary; the method is the builder's internal concern.

**Second, ODD plays well with structural enforcement, which loam
relies on.** An objective stated as observable outcome is testable.
A test is mechanical. Structural mechanisms (Pydantic schemas, type
constructors, refusal at construction time) make invalid states
unrepresentable rather than relying on humans or LLMs to remember
rules. The chain — objective → acceptance criterion → test →
structural check — is what keeps loam's autonomy trustworthy.

ODD is not the same as TDD or BDD. TDD is about *how you build* a
unit (red/green cadence on behaviour-level tests). BDD is about *what
you build* at the scenario level with stakeholder-readable specs.
ODD is about *what you delegate* — the contract between a delegator
and a builder is the objective, not the procedure. The three are
adjacent, not interchangeable.

ODD is not a novel discipline, and loam does not claim it is. It
descends from named ancestors — goal-oriented requirements
engineering (KAOS), Outcome-Driven Innovation (Ulwick),
Specification by Example (Adzic), and Design by Contract (Meyer) —
combined as: ATDD + goal-reverse-engineering + a strict
reverse-coverage rule + evidence banding, tuned for work delegated
to an LLM builder.

One scope split to hold onto: **ODD is how criteria are written;
KEEL is how they are enforced.** ODD is the authoring grammar inside
the KEEL contract lifecycle (Capture → Translate → Ratify → Bind →
Build → Verify → Deliver, Amend user-only); the root contract every
criterion ladders to is Charter entry #0 in
[`../charter.md`](../charter.md), whose first derived criteria are
`AC.PO.1` / `AC.PO.2` in
[`../VALUE_PROPOSITION.md`](../VALUE_PROPOSITION.md).

---

## How to read an acceptance criterion

An acceptance criterion (AC) in loam looks something like:

> **A1.** Scope kill issued against an active scope transitions the
> scope and its TERMINATE-policy children to `cancelled` within 500ms
> p95. Emits `loam.safety.scope_kill` span with level + reason +
> source. Writes a `kill_events` row.

What to notice:

1. **Outcome, not procedure.** The criterion says what must be true,
   not how to achieve it. The implementation could use locks, queues,
   pubsub, or a database trigger — the AC does not care.
2. **Deterministic.** Someone else can run the check and get a
   pass/fail answer without consulting the author's intent.
3. **One AC per declared behaviour.** This AC declares three things
   (state transition, span emission, audit-row write), and each is
   independently testable. If you see an objective declaring four
   behaviours and supplying one AC, the other three are unverified.
4. **Timing in the AC.** Performance, latency, and concurrency
   bounds belong in the criterion. "Within 500ms p95" is part of the
   contract, not a separate concern.
5. **Negative criteria are valid.** "X does not happen" is an AC when
   the objective is preventing something.

ACs in loam are typically prefixed (`AC.OSS.1`, `AC.PO.1`, `A1`,
`A19`) so they can be referenced in commit messages, plan documents,
test names, and seal narratives. When you author a test, the test
function name usually includes the AC reference.

---

## How to author work for loam

If you are submitting a feature proposal, a plan, or a substantial
issue, follow this order. Do not permute.

1. **Objective first.** State the outcome in one sentence: "X must
   be true when this scope is done."
2. **Constraints second.** State the budget (time, tokens, money),
   reversibility class (fully reversible / compensatable /
   irreversible), dependency fence (what may be touched, what may
   not), authority bound (what the builder may decide unilaterally),
   and fail-closed direction (what happens when the objective
   cannot be satisfied).
3. **Acceptance third.** Write one deterministic AC per declared
   behaviour. Count behaviours; count criteria; verify they match.
4. **Method last — only as suggestion, never as instruction.** If
   you list method, mark it advisory; never embed it inside an AC.

If method feels necessary before acceptance, the objective is
underspecified. Tighten the objective until method is obvious.

---

## Plan before code

Once the objective + constraints + acceptance criteria are
written, the next step for any non-trivial build is to **write a
plan document before touching source.** A plan in loam is a short
markdown file naming the build's outcome, its scope boundaries,
the named decisions the builder will make method-shape, and the
halt-and-surface conditions that will cause the builder to stop
and ask. The plan is not a method prescription; it is the
builder's working confrontation with the objective at full
dimension before the diff exists. Skipping the plan means
discovering the objective mid-build — the failure mode the
methodology is designed to prevent.

---

## Halt and surface

When a builder hits a condition where continuing would extend an
ODD violation, exceed the named scope, or breach a constraint,
the sanctioned action is **halt and surface** — stop, name the
condition, return to the delegator for ruling. "Almost done" is
never a reason to continue past a halt condition.

Every brief should name halt-and-surface conditions explicitly.
When a builder discovers a condition the brief did not anticipate
but that has the same shape, the rule applies anyway. Halt-and-
surface is what makes scope discipline operational; without it, a
builder treats discovered work as in-scope and the objective
drifts.

---

## The two rules that catch most violations

**Rule 1 — No method in acceptance.** ACs that say "the test will use
pytest", "the component will implement a visitor pattern", "the
refusal will be a Pydantic model_validator" are violations. The
acceptance contract names the outcome; the implementation is the
builder's call. Rewrite as "what must be true."

**Rule 2 — No code for cases the objectives do not name.** Every line
of code, every branch, every test, every dependency in a deliverable
maps to a named AC. A platform branch for an OS no objective covers,
a configuration field no AC exercises, a defensive `if/except` for a
case the contract says cannot arise — these are method-in-code
leakage. They get re-extended up the objective chain (promoted to a
named AC with a test) or deleted. "Might be useful later" is not a
backing.

The check has two directions:

- **Forward (authoring):** every declared behaviour in every objective
  has an AC.
- **Reverse (review):** every code path, branch, test, and dependency
  in the diff has an AC it maps back to.

A diff where forward and reverse both pass is scope-clean.

---

## Handling defects and gaps

When a builder discovers a scenario the current objectives do not
cover, the correct action is **not** to quietly add an `if` branch.
The correct action is to promote the gap to a named AC and extend
the objective list — a re-extension, sometimes called the A20
pattern after loam's safety-layer AC that originated the rule.

A failure mode buried as an exception branch is invisible to the AC
audit, invisible to anyone reviewing the objective list, untestable
independently, and accumulates silently. A failure mode re-extended
as a positive AC appears in the audit, has its own test, survives in
the audit trail, and can be reasoned about when the component is
modified.

When a builder cannot re-extend (the gap is too large for the current
scope), the sanctioned action is **halt and signal**, not quiet
handling. Halt-and-signal is part of every brief; its absence lets a
builder treat "almost done" as a reason to exceed scope.

When 2+ hotfixes hit the same code area in close succession, the gap
is at the architecture level, not the AC level. Pause hotfix
iteration; commission a first-principles review of the design choice
underneath the hotfix surface. AC-level re-extension cannot fix a
structural problem.

---

## Structural over advisory

ODD applied to code produces structural enforcement, not advisory
rules. The distinction is mechanical.

An **advisory rule** lives in prose — a docstring, a comment, a
prompt. It describes what the code should do but does not prevent
the code from doing otherwise.

A **structural check** lives in the type system, the schema, or the
constructor. It prevents the forbidden state from being representable.
The code cannot violate it without refactoring the structural check
itself.

loam prefers structural over advisory every time. Advisory is the
fallback for things structure cannot reach (persona voice,
documentation clarity, whether a chosen abstraction is the right
one). Anything that *can* be expressed structurally *must* be.

When choosing between two structural options, prefer the one that
*eliminates* the failure class over the one that merely *relocates*
it. A `.gitignore` pattern that must be updated when new state files
are introduced has relocated the failure mode from "developer forgot
the rule" to "developer forgot to update the mechanism." A directory
split that prevents accidental modification because the wrong
directory cannot be reached without explicit traversal has
*eliminated* the failure class.

The test: *"Can a future code change re-introduce the same failure
class without active discipline?"* If yes, the option is rule-shaped
despite using a structural mechanism, and a stronger option should be
sought.

---

## Quick reference

**Authoring:** outcome as "X must be true"; budget +
reversibility + dependencies + authority + fail-closed direction;
one deterministic AC per declared behaviour; halt trigger named.

**Building:** plan before code; gap during build → new AC + test
+ rationale in the commit, or halt-and-signal if the gap exceeds
scope.

**Reviewing a brief:** scan for method-in-acceptance; count
behaviours vs criteria; check for missing halt trigger / budget
/ authority bound; check for advisory-where-structural-would-work.

**Reviewing built work:** every AC has a test; no silent exception
branches; every code path / branch / test / dependency in the
diff maps to a backing AC; tests assert outcome, not method.

---

## Where to go next

- **Contributing workflow:** [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md).
- **Positioning:** [`../positioning.md`](../positioning.md) — what
  loam is and who it is for.
- **Architecture:** [`../architecture.md`](../architecture.md) — how
  the components compose.

ODD is loam's operational methodology; this document is the
contributor-facing summary. The longer authoring corpus loam itself
practices internally is not shipped as part of v0.1.0 — the principles
on this page are what an external contributor needs.
