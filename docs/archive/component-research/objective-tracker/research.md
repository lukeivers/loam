# Research — Objective Tracker

**Component:** Objective Tracker (third and final Phase 1 primitive).
**Status:** DRAFT — research output per the owner-approved plan.
**Author:** research agent. **Date:** 2026-04-18.

---

## 0. Executive summary

The objective tracker is an event-sourced, SQLite-backed, Pydantic-modelled
primitive that registers user-authored root objectives, lets them decompose
into child objectives as a tree (DAG rejected; see §2), records acceptance-
criterion evaluations as typed events, and exposes a resolution API
(`resolve(objective_id) -> ObjectiveProjection | None`, `trace_to_root`,
`list_by_parent`, `list_by_root`, etc.) that lets enforcement happen
**outside** the tracker — by whatever layer authors a scope-of-work.

**The tracker does not, and cannot, mutate the sealed scope-of-work
primitive.** That primitive has no `parent_objective_id` field today
(§1.1 below); adding one is an amendment and a halt signal per the
brief. Rather than amend, the research recommends a sidecar
`ScopeObjectiveBinding` table maintained by the tracker itself,
populated either by an explicit helper the caller invokes
(`tracker.bind_scope(scope_id, objective_id)`) **after** calling
`runtime.create(spec, ...)`, or by a pyee subscriber the tracker
registers against the scope runtime's `scope_created` event — with
one critical constraint: the subscriber **rejects the binding and
records a `binding_rejected` event** if the referenced objective is
unknown or unreachable from a user-authored root. This gives
deterministic enforcement at scope creation without requiring any
change inside scope-of-work.

A lighter alternative — passing the objective id through a scope's
`observers` field or embedded in its `goal` string — is rejected as
string-based and non-enforceable. Both are discussed in §3.

The tracker ships as a Python package with a thin async API mirroring
scope-of-work's posture (`ObjectiveRuntime` over an `EventStore`),
reuses pyee for emission, reuses OpenTelemetry for spans, and adds no
runtime dependency beyond the brief's permitted list.

Complexity estimate: **340–420 AI-minutes**, squarely in the plan's
predicted 300–450 range. It is the simplest of the three Phase 1
primitives: a single tree with one kind of acceptance-criterion event
and one kind of enforcement query, no authoring pipeline, no LLM-inside,
no compaction-survival machinery.

**Halt signals surfaced:**
1. **Scope-of-work lacks `parent_objective_id`** (research-plan §Starting
   position claims the field exists; it does not — see §1.1). The
   tracker proceeds under the sidecar-binding model and does not amend
   scope-of-work. This is surfaced for owner's awareness — not because
   the tracker requires an amendment, but because the plan's wording
   anticipated a field that is not there, and the owner should see the
   discrepancy before approving the proposal.
2. **The term "user-authored root" is undefined in the spec.** The
   research proposes a concrete definition (§2.3) but flags that the owner
   must confirm the definition before the proposal locks it in. This
   is a low-risk halt — the definition is small and clean — but it is
   surfaced because it is load-bearing on enforcement.

Everything else in the research plan can be satisfied under the stated
constraints.

---

## 1. Starting position — what the sealed components actually expose

### 1.1 Scope-of-work — the critical discovery

The research-plan starting position says:

> Scope-of-work carries parent-objective references in its seven-field
> `ScopeSpec` — the field exists, but no runtime enforces that the
> reference resolves to a real objective. Today's behaviour: the string
> is stored, unverified.

**This is incorrect.** Inspection of
`pos-v2/scope-of-work/src/spec.py` (full
read, 313 lines) shows the seven declared fields are: `goal`,
`constraints`, `budget`, `reversibility_class`, `success_criteria`,
`observers`, `escalation_triggers`. Plus metadata (`owner_persona`,
`parent_close_policy`, `expected_duration_seconds`) and the
hierarchical `parent_scope_id` passed at `create()` time. **There is
no `parent_objective_id` field, no objective reference of any kind.**
`grep -r objective` across `pos-v2/` returns
docstrings and a single line in
`scope-of-work/docs/relationship-map.md` describing the objective
tracker as "bidirectional — reads success_criteria; writes
`evaluate_success_criterion(...)` events." It does not say the scope
spec carries an objective id.

**Implication:** The research plan's enforcement goal ("scope-of-
work's `parent_objective_id` reference must become enforceable after
the tracker lands") has to be re-framed. There are three shapes for
the enforcement mechanism, detailed in §3 below. All three keep
scope-of-work untouched.

### 1.2 Memory system

Reviewed `pos-v2/memory-system/docs/
prose-explanation.md` and `memory-system/src/scope.py`. Memory attributes
every entry to a scope (`group_id` = `scope_id`), consumes a
`ScopeSource` protocol, and does not know about objectives. Memory
is a pure downstream consumer of scope identity; no change is
required for the tracker to land.

### 1.3 Primary-persona layer

Reviewed `primary-persona/docs/prose-explanation.md`,
`primary-persona/docs/relationship-map.md`, `primary-persona/src/
contract.py`, and the relevant portion of `src/authoring.py`. The
layer's `PersonaContract` does not reference objectives directly;
authoring runs inside a caller-supplied `authoring_scope_id` (a
scope, not an objective). The hard dependency the tracker introduces
is one-directional: objectives may later be referenced by persona
authority boundaries or escalation categories, but the persona
contract as sealed does not need to know about objectives on day one.

**v1.2 R14 — autonomous authoring:** the authoring pipeline is
budgeted by a scope-of-work that has (today) no parent objective.
§7 below recommends a convention for what that scope's objective
should be — a recommendation, not a requirement of the tracker.

### 1.4 Summary of sealed-component constraints

| Sealed component | Does it know about objectives? | Amendment needed? |
|---|---|---|
| scope-of-work `ScopeSpec` | No | **No** — tracker owns the binding sidecar |
| scope-of-work runtime | No | **No** — tracker subscribes via pyee |
| memory `ScopeSource` | No | **No** — memory remains scope-only |
| `PersonaContract` | No | **No** — referencing is workspace-level |
| Authoring pipeline | Runs under an `authoring_scope_id` | **No** — scope can be bound to an objective by the caller |

**No sealed-component amendments are required** for the tracker to land
and deliver every v1.0 / v1.1 / v1.2 acceptance criterion that names
objectives. This is the most important conclusion of the research.

---

## 2. Question group 1 — objective primitive: schema and fields

### 2.1 Options considered

Three shapes for the objective primitive were evaluated:

**Option A — Minimal primitive (four spec-declared fields only).** Keep
the primitive exactly what the spec declares: `goal`, `parent` (or
root marker), `testable_criterion`, `time_bound_or_evergreen`. Status
derived from events, owner derived from the parent's owner, everything
else implicit.

**Option B — Enriched primitive (spec fields plus status, owner,
timestamps, provenance).** Spec-declared fields plus: `status`
(draft / active / achieved / abandoned), `created_at`, `provenance`
(user_authored | system_authored, which persona/scope authored it),
and operational metadata (priority, measurement cadence).

**Option C — Event-sourced primitive (spec fields as `ObjectiveCreated`
event payload; state projected from events).** Same declared surface
as Option B at the `ObjectiveProjection` level, but the source of
truth is the event log. Mirror scope-of-work's architecture exactly.

### 2.2 Recommendation — Option C, event-sourced, mirroring scope-of-work

Rationale:

1. **Architectural coherence with scope-of-work.** Scope-of-work is
   event-sourced; the upgrade-fidelity probe (v1.1 R1) depends on
   replayability. Making the tracker event-sourced means replay works
   across objectives too, and the upgrade harness can treat both
   primitives uniformly. An alternative persistence model for
   objectives would create a second upgrade-fidelity story.
2. **Status mutation is a first-class concern.** Status changes
   (`draft` → `active` → `achieved` / `abandoned`, and the implicit
   `re-opened` case when a negative case re-extends back up the
   chain) need audit — *when* did this objective get marked achieved,
   under what evidence, by what actor? Event sourcing makes this
   deterministic and replayable.
3. **Acceptance-criterion evaluations are events, not state.** A
   testable criterion can be evaluated many times; each evaluation
   carries its own timestamp, result, scope-of-work that ran the
   check, and note. An event-sourced model expresses this naturally.
4. **Cost.** Scope-of-work's event store is ~700 LOC. The objective
   store will be smaller because there are fewer event kinds. The
   cost of doing this once more is low; the cost of later
   converting a mutable-state primitive to event-sourced is high.

Option A is rejected because status-as-event is required to serve
negative-case re-extension and ODD test-suites. Option B is rejected
because a mutable-state primitive forgoes the architectural coherence
for no material simplification.

### 2.3 Recommended schema (Pydantic sketch, full version in §8)

Two Pydantic types — an immutable `ObjectiveSpec` passed to `create()`,
and a public `ObjectiveProjection` returned from queries. Event types
are a discriminated union analogous to scope-of-work's.

```python
class ObjectiveKind(str, Enum):
    user_authored_root = "user_authored_root"   # top-level; parent_id = None
    child = "child"                              # derived; parent_id required

class CriterionType(str, Enum):
    prose = "prose"                    # free text; evaluation is a caller-supplied check
    scope_success = "scope_success"    # criterion met when a named scope completes
    child_closure = "child_closure"    # criterion met when all children are achieved
    external_predicate = "external_predicate"  # caller-supplied predicate name

class AcceptanceCriterion(BaseModel):
    """Testable criterion — can be evaluated. Evaluation is deferred
    to the caller; the primitive stores what was declared and every
    evaluation event that was run against it."""
    criterion_id: str
    kind: CriterionType
    description: str
    # kind=scope_success → scope_id field names the scope whose
    # completion satisfies this criterion.
    scope_id: str | None = None
    # kind=external_predicate → name the caller resolves at check time.
    predicate_name: str | None = None

class TimeBoundOrEvergreen(BaseModel):
    """Either a deadline (UTC ISO-8601) or evergreen with a review cadence."""
    kind: Literal["time_bound", "evergreen"]
    deadline: str | None = None     # iso-8601, UTC; required when kind=time_bound
    review_cadence_days: int | None = None  # required when kind=evergreen; ≥1

class ObjectiveSpec(BaseModel):
    """The primitive's create-time input. Required fields match the
    v1.0 spec's declaration; optional fields are operational metadata."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    # --- four spec-declared required fields ---
    goal: str = Field(min_length=1)
    kind: ObjectiveKind
    parent_id: str | None = None  # required when kind=child; forbidden otherwise
    acceptance_criteria: tuple[AcceptanceCriterion, ...] = ()  # min_length=1 at create
    time_bound: TimeBoundOrEvergreen
    # --- optional operational metadata ---
    owner_persona: str | None = None
    authored_by: Literal["user", "system"]       # provenance per §2.4
    authored_under_scope_id: str | None = None   # the scope within which this
                                                  # objective was created (for
                                                  # system-authored objectives)
```

### 2.4 Mandatory vs optional at creation

- **Mandatory:** `goal`, `kind`, `acceptance_criteria` (at least one
  criterion), `time_bound`, `authored_by`.
- **Conditionally mandatory:** `parent_id` (required when
  `kind=child`; rejected when `kind=user_authored_root`).
- **Optional:** `owner_persona`, `authored_under_scope_id`.

The primitive rejects creation with a Pydantic `ValidationError` when
any mandatory is missing — mirroring scope-of-work's policy ("missing
any field rejects creation, deterministic, no runtime branch").

### 2.5 Testable criterion representation — the four-variant model

The research recommends a **Pydantic-discriminated-union on
`CriterionType`** with four variants (per the schema above). The
primitive does **not** execute the criterion. It *records* it and
records every `AcceptanceCriterionEvaluated` event the caller
submits. Evaluation remains caller-dispatched — the tracker is a
test registrar, not a test runner.

Rationale:
- `prose` is the base case — every objective needs a natural-language
  description of what "achieved" means. It is never the only variant.
- `scope_success` wires the tracker's tree to scope-of-work's event
  stream directly: "this objective is achieved when scope X completes."
  This is the single most load-bearing variant for ODD — a scope
  completion event fires the criterion's evaluation. The tracker
  subscribes to `scope_of_work.subscribe_all` and emits an
  `AcceptanceCriterionEvaluated(result=met)` event when a bound
  scope reaches `completed`.
- `child_closure` is the cascade predicate: "this objective is
  achieved when all child objectives are achieved." Purely internal
  to the tracker; no external wiring needed.
- `external_predicate` is the escape hatch — caller-supplied check,
  resolved by name at evaluation time. Useful for criteria that
  cannot be expressed as "scope completed" (e.g. "the KPI graph is
  above 0.7 for a week").

Note on test-against-objective: this four-variant model is **exactly
what ODD needs** (§6). A test harness registered against an
`external_predicate` criterion *is* an ODD test, bound to an
objective rather than a behaviour.

### 2.6 Time-bound-or-evergreen

Expressed as the `TimeBoundOrEvergreen` discriminated union above. A
time-bound objective has a UTC ISO-8601 `deadline`; an evergreen
objective has a `review_cadence_days` positive integer. Both are
validated on construction.

This is a modelling choice, not a primitive behaviour: the tracker
does **not** automatically notify on deadline or cadence. Notification
on staleness is future work — a downstream consumer subscribing to the
tracker's pyee stream and running `list_by_cadence_due(at_time)`. The
tracker exposes the query; it does not schedule.

### 2.7 Status modelling

Event-sourced, per Option C:

```
ObjectiveState: draft → active → {paused ↔ active}* → achieved | abandoned
```

Transitions mirror scope-of-work's pattern. Re-opening an achieved
objective (because evidence of failure arrived later) is a legal
transition — `achieved → active` with a `reason` field. This is the
behaviour ODD negative-case handling requires: when a negative case
is surfaced and re-extended as a positive objective, the parent may
need to re-open (its previously-achieved criterion is now disputed).

---

## 3. Question group 2 — hierarchy and traceability

### 3.1 Tree vs DAG vs forest — recommendation: strict tree, forest of roots

Options:

**Strict tree.** Every child has exactly one parent; roots have no
parent. A workspace has a forest (multiple user-authored roots).

**DAG.** A child may have multiple parents (an objective serves two
top-level goals).

**Forest of trees, roots only at the top.** Same as "strict tree" but
with first-class support for multiple roots per workspace.

**Recommendation: strict tree, forest of roots.**

Rationale:

1. **DAG semantics are ambiguous under enforcement.** If an objective
   has two parents and a scope claims to serve it, which root does
   the scope ultimately trace to? "Either" is not an answer in an
   enforcement model — the tracker must produce a deterministic
   trace-to-root, and DAGs do not deterministically produce one
   without tie-breaking rules that introduce their own failure
   modes.
2. **The spec's traceability rule is tree-shaped.** v1.0's bullet is
   "every scope traces to a top-level user-authored objective" — a
   single root path, not a set of paths.
3. **Decomposition is naturally tree-shaped.** Negative-case
   re-extension (ODD's distinguishing feature) produces new sibling
   or parent objectives, not cross-tree edges. The DAG complexity
   buys nothing for the methodology's actual use cases.
4. **Implementation cost.** Tree is O(depth) to trace; DAG needs
   memoised transitive closure or repeated walks. For the cardinality
   pOS targets (hundreds, not millions, of objectives), either works —
   but the tree keeps the invariant local to `parent_id` and avoids
   a second derivation table.

Multiple roots in a single workspace are supported by design — a
workspace may declare "top-level goal: make a living writing" and
"top-level goal: maintain health" as independent roots. `list_roots()`
returns all of them. This is the forest part.

### 3.2 Enforcement — "every scope traces to a top-level user-authored objective"

Three shapes evaluated:

**Shape A — Sidecar binding table (recommended).** The tracker owns a
`ScopeObjectiveBinding(scope_id, objective_id, created_at)` SQLite
table. Bindings are created through `tracker.bind_scope(
scope_id, objective_id)`. The binding call:
1. Verifies the objective exists and is reachable from a
   user-authored root (§2.3 definition) via `trace_to_root`.
2. Emits a `ScopeBound` event on success, or a `BindingRejected`
   event with `reason="unknown_objective" | "orphan_root" |
   "inactive_root"` on failure.
3. Returns the binding record or raises `UnresolvedObjectiveError`.

The caller — whatever layer is creating the scope — uses this call
*before* transitioning the scope to `active`. Callers can enforce at
any point of the creation flow. The contract: **a scope may be
created without a binding (draft), but cannot be `start()`ed without
one** — or, more precisely, an unbinding-before-start scope is the
workspace's problem, not the tracker's. The tracker publishes whether
a scope is bound; enforcement layers (the workspace's dispatch layer,
the primary persona, the safety layer) check the binding.

**Shape B — Tracker subscribes to scope_of_work.subscribe_all.** The
tracker listens for `ScopeCreated` events. Each event's `goal` is
scanned for an `objective:OBJ_ID` prefix (or similar convention). The
tracker emits a `BindingAccepted` or `BindingRejected` event. This
is less clean — it baubles on the goal string — but requires zero
caller effort.

**Shape C — Scope-of-work amendment.** Add `parent_objective_id` to
`ScopeSpec`. Brief-level halt signal; rejected.

**Recommendation: Shape A.** Rationale:

1. **Explicit is better than implicit.** Callers declare the binding
   in one call; the API is discoverable, typed, and tested.
2. **Zero amendment to sealed components.** The tracker is
   purely additive.
3. **The integration test writes itself** (see §5):
   ```python
   # Orphan-objective scope cannot be bound.
   runtime = ObjectiveRuntime(db_path=...)
   await runtime.create(ObjectiveSpec(
       goal="pay bills", kind=ObjectiveKind.user_authored_root,
       acceptance_criteria=(prose("bills paid"),),
       time_bound=evergreen(30),
       authored_by="user"))
   # ...create a scope via scope-of-work...
   with pytest.raises(UnresolvedObjectiveError):
       await tracker.bind_scope(scope_id, "unknown-obj")
   ```
4. **The test for "every scope traces to a top-level user-authored
   objective" becomes a property of the binding API, not of the
   scope_of_work runtime** — consistent with the constraint that
   scope-of-work does not change.

The enforcement surface is *the binding API itself.* What enforces
that "every scope has a binding" is workspace policy — the primary
persona's dispatch protocol — not the tracker. The tracker provides
a deterministic way to ask "is this scope bound to a valid
objective?" (`tracker.is_bound(scope_id)`); the workspace's dispatch
layer refuses to dispatch unbound scopes.

### 3.3 User-authored vs system-authored — the `authored_by` field

The spec's phrase "user-authored" is not formally defined. The
research recommends this definition:

> An objective is **user-authored** when it was created through a
> direct user action: (a) an explicit API call the user made, (b) a
> onboarding step, (c) a command the user invoked (`/add-objective`
> or similar). An objective is **system-authored** when it was
> created by any non-user actor: a persona's autonomous decomposition,
> a negative-case re-extension by the ODD harness, a cascade from
> another objective's child-closure criterion.

Operationally, the distinction is carried by the `authored_by` field
on `ObjectiveSpec` (values: `user` | `system`). A user-authored root
has `kind=user_authored_root, authored_by=user, parent_id=None`. A
system-authored objective (any kind) has `authored_by=system` plus
the `authored_under_scope_id` pointing at the scope that spawned it.

**Important constraint:** the `authored_by` field is **trusted input
from the caller.** The primitive does not authenticate authorship —
that is a workspace-policy concern. But every create event records
the value, so an audit can detect a workspace that is falsely claiming
user-authorship.

**Halt signal #2 reprised:** the owner must confirm this definition in
the proposal phase before the tracker ships. It is the basis of the
tree's root invariant and of the integration test in §5.

### 3.4 Cascade on parent abandonment / achievement

Three options:

- **Cascade** — children inherit the parent's terminal status.
- **Notify** — children get a `parent_closed` event but decide
  their own state.
- **Ignore** — children are unaffected.

**Recommendation: default to "Notify" (middle option), parametrised
by a per-objective `parent_close_policy` field** — copied in spirit
from scope-of-work's parent-close policy. Default: `notify`. Override:
`cascade_achieved`, `cascade_abandoned`, `ignore`. Scope-of-work
already demonstrates this pattern works cleanly; no reason to
diverge.

The `notify` default is the ODD-correct behaviour: when a parent
is abandoned, child objectives are not automatically abandoned —
the user (or the autonomous primary persona in its authorised
autonomy) decides what to do. "Mom said no to the big goal" does
not mean "all the little goals under it are also cancelled."

---

## 4. Question group 3 — persistence and integration with scope-of-work

### 4.1 Shared DB file vs separate

Options:
- **Shared.** One SQLite file with both scope and objective tables.
  Transactions can span both; a single store powers both runtimes.
- **Separate.** Two SQLite files, one per primitive. Cross-
  references are by id.

**Recommendation: separate DB files.** Rationale:

1. **Domain boundary.** Each primitive owns its persistence. Future
   teardown or restoration of one primitive without the other is
   trivial.
2. **Upgrade fidelity.** The scope-of-work upgrade probe is already
   wired to a specific schema; co-location would force the probe to
   account for objective tables, expanding its surface.
3. **Transactional needs are small.** The sidecar binding table (§3.2)
   is the only point that references scope ids. It lives in the
   tracker's DB file and is written by the tracker alone; scope-of-
   work never touches it.
4. **Cross-process read.** When scope-of-work runs in one process
   and the tracker in another (future Phase 3 session-resilience
   work), separate files is the safe default.

### 4.2 Scope-to-objective relationship model

Options:
- **1:1** — every scope has exactly one parent objective.
- **1:many** — a scope may serve multiple objectives.
- **Hierarchical inheritance** — a scope inherits ancestor
  objectives automatically.

**Recommendation: 1:1 binding, hierarchical resolution on demand.**
A scope is bound to exactly one objective via the sidecar table; the
tracker exposes `trace_objectives_for_scope(scope_id) -> tuple[
ObjectiveProjection, ...]` which walks from the bound objective to
the root, returning the full chain.

Rationale:
- 1:1 binding is deterministic and fits the enforcement test cleanly.
- Callers who want the full chain (ODD test harness, primary persona
  briefings, audit reports) get it through the trace query — no
  duplicate bindings needed.
- Many-to-many requires a join table and tie-breaking rules at every
  query; unnecessary for the spec.

### 4.3 Query latency for parent-resolution at scope creation

Prototype question flagged in §9. On expected cardinality (≤10⁴
objectives, ≤10⁵ scopes over a lifetime), a single-process SQLite
`SELECT` on an indexed `objective_id` is sub-millisecond. Across
processes, pyee notification adds <10 ms. The research assumes this
is non-load-bearing at pOS scale and moves on; the prototyping
priority list flags it anyway.

---

## 5. Question group 4 — acceptance-criterion evaluation

### 5.1 On-demand / continuous / scheduled — recommendation: caller-dispatched

The tracker does **not** schedule evaluations. It **records** them.
Three paths for evaluation firing:

1. **`scope_success` criteria are auto-evaluated.** The tracker
   subscribes to scope-of-work's `subscribe_all` emitter. When a
   scope reaches `completed`, the tracker looks up bindings where
   `criterion.scope_id == completed_scope_id` and emits an
   `AcceptanceCriterionEvaluated(result=met)` event automatically.
   If the scope reaches `failed` or `cancelled`, emit
   `AcceptanceCriterionEvaluated(result=not_met, reason=...)`.
2. **`child_closure` criteria are auto-evaluated.** When a child
   objective is marked `achieved`, the tracker re-evaluates the
   parent's `child_closure` criterion (if any). If every child is
   `achieved`, the parent's criterion fires `met`. This is the
   roll-up behaviour ODD depends on.
3. **`prose` and `external_predicate` criteria are caller-dispatched.**
   The caller invokes
   `tracker.evaluate_criterion(objective_id, criterion_id, result,
   evidence_scope_id?, note?)`. The tracker records the event. The
   caller may be the primary persona, a workflow dispatcher, the
   user via a CLI, or the future self-correction loop.

### 5.2 Result storage

Per §2.2, every evaluation is an event. The projection surfaces:
- `last_evaluation_per_criterion` — latest result per criterion.
- `achievement_status` — derived from the last-evaluation pattern
  plus the ObjectiveState transitions.

An objective is achieved when **every** acceptance criterion has a
most-recent `met` evaluation. Caller or subscriber triggers the
`objective → achieved` transition; the tracker does not auto-
transition (this is a design choice: transitions are declarative,
records are passive). Future work may register a default
auto-transition policy; day-one, it's caller-driven.

### 5.3 Interaction with ODD negative-case handling

When a negative case is re-extended up the chain, three concrete
steps happen (in a workspace's ODD harness, not inside the tracker):

1. The negative case is logged as an evaluation event:
   `AcceptanceCriterionEvaluated(result=not_met, reason=<case>)`.
2. A new objective is authored — sibling, parent, or a new tree
   per methodology — with `authored_by=system`, `parent_id=<chosen
   position>`, `acceptance_criteria=(<derived criteria>,)`. The
   authoring may be LLM-assisted (Claude via Max, per constraint 5),
   but the tracker does **not** host the inference. The LLM call
   is made by the workspace's harness; the tracker only records the
   new objective.
3. If the negative case implicates a previously-achieved parent, the
   parent's state transitions `achieved → active` (re-opened) via
   the tracker's API.

**The tracker does not automatically create the new objective.** It
*enables* the workflow by exposing the evaluation event, the
re-extension APIs (`create`, transition APIs), and the traversal
APIs. The decision on *what* the new positive objective should say
is authorial — a Claude-via-Max call the workspace makes.

This keeps the tracker primitive-shaped and keeps inference on the
LLM side of the boundary — matching constraint 5 of the brief.

---

## 6. Question group 5 — ODD-compatibility and test harness integration

### 6.1 Tracker's role: passive registrar, active subscriber

The tracker is:
- **Passive** as a test registrar — tests bind themselves to
  objectives via criterion ids; the tracker does not run tests.
- **Active** as a subscriber — on scope completion events, it
  fires auto-evaluations (§5.1). On objective state transitions,
  it fires pyee events that downstream consumers (the ODD harness,
  the primary persona) subscribe to.

### 6.2 Base query for ODD test runs

The tracker provides `list_by_root(root_id, states=, statuses=,
time_bounds=)` — exactly the query ODD needs. A test run
materialises: "all active, unchecked, non-evergreen objectives under
top-level goal G." The test harness walks the returned list, checks
the criterion kind, and runs the appropriate check.

```python
active_objectives = tracker.list_by_root(
    root_id="goal-writing-income",
    states=[ObjectiveState.active],
    with_unchecked_criteria=True,
    time_bounds=["time_bound"],
)
```

### 6.3 Representing the objective chain for a given scope

Three options:
- **Materialised path.** Store the ancestry as a `/root/.../obj` path
  on each child. Fast reads, updates on parent moves.
- **Runtime walk.** Walk `parent_id` each time. Simple; O(depth).
- **Cached ancestry array.** Periodically materialised in a
  sidecar table.

**Recommendation: runtime walk, cache optionally.** The depth of a
realistic pOS objective tree is <10; walking is cheap and avoids
cache-invalidation complexity. The cache can be added later if
profiling shows it necessary. At pOS scale, it won't.

### 6.4 ODD integration sketch (concrete)

The ODD harness lives outside the tracker — it is workspace code or
a later pOS layer. The sketch:

```python
# An ODD test suite for a root objective.
@odd_suite(root_objective_id="goal-writing-income")
async def test_writing_income_objectives(tracker, scope_runtime):
    objectives = tracker.list_by_root(
        root_id="goal-writing-income",
        states=[ObjectiveState.active],
    )
    for obj in objectives:
        for criterion in obj.acceptance_criteria:
            result = await dispatch_criterion(
                criterion, tracker=tracker, scope_runtime=scope_runtime
            )
            await tracker.evaluate_criterion(
                obj.objective_id, criterion.criterion_id, result.result,
                evidence_scope_id=result.evidence_scope_id,
                note=result.note,
            )
            if result.result == "not_met":
                # negative-case re-extension: the harness proposes a
                # new positive objective (LLM-assisted, outside the
                # tracker), then registers it.
                new_obj_spec = await propose_re_extension(
                    criterion, result, tracker, claude_via_max
                )
                await tracker.create(new_obj_spec)
```

Three things the tracker gives the harness, beyond the bare API:
1. **Stable ids for criteria.** So tests can be bound to criteria by
   id, replayed post-upgrade, and compared.
2. **Evaluation history.** The `AcceptanceCriterionEvaluated` event
   stream is a test-run log. Replay is native.
3. **pyee stream.** An ODD viewer subscribes to
   `tracker.emitter.subscribe_all` and shows which criteria are
   being evaluated in real time.

### 6.5 BDD-vs-ODD framing

The survey (§10) confirms:
- **pytest-bdd / behave** model features → scenarios → steps. Tests
  are authored against behaviours ("when the user clicks, then the
  form submits"). Scenarios are tagged and grouped by feature files.
- **ODD inverts this.** Tests are authored against objectives; the
  "given-when-then" structure is replaced by "evidence that
  criterion K of objective O is met." A negative case is a new
  positive objective, not an exception branch in a scenario.

The objective tracker is the missing primitive that makes ODD
concrete. BDD needs only feature files plus a runner; ODD needs a
runtime store of objectives with criteria — which is exactly the
tracker.

Practical lesson from BDD tooling: **test files need not live in the
same tree as the criteria.** The tracker stores criteria; workspace
test code binds by `criterion_id`. This gives ODD the same flexibility
BDD runners give today.

---

## 7. Question group 6 — API surface and integration

### 7.1 Recommended API (mirrors scope-of-work's posture)

```python
class ObjectiveRuntime:
    def __init__(self, db_path, *, scope_runtime: ScopeRuntime | None = None):
        ...

    # Creation
    async def create(self, spec: ObjectiveSpec, *,
                     objective_id: str | None = None) -> ObjectiveProjection: ...

    # Lifecycle
    async def activate(self, objective_id: str) -> ObjectiveProjection: ...
    async def mark_achieved(self, objective_id: str, *,
                            evidence_scope_id: str | None = None,
                            note: str | None = None) -> ObjectiveProjection: ...
    async def mark_abandoned(self, objective_id: str, *,
                             reason: str) -> ObjectiveProjection: ...
    async def re_open(self, objective_id: str, *,
                      reason: str) -> ObjectiveProjection: ...

    # Decomposition
    async def decompose(self, parent_id: str,
                        child_specs: Sequence[ObjectiveSpec]
                        ) -> tuple[ObjectiveProjection, ...]: ...

    # Acceptance-criterion evaluation
    async def evaluate_criterion(self, objective_id: str, criterion_id: str,
                                  result: Literal["met", "not_met"],
                                  *, evidence_scope_id: str | None = None,
                                  note: str | None = None
                                  ) -> ObjectiveProjection: ...

    # Scope binding (the enforcement surface)
    async def bind_scope(self, scope_id: str, objective_id: str
                         ) -> ScopeObjectiveBinding: ...
    async def unbind_scope(self, scope_id: str) -> None: ...
    def is_bound(self, scope_id: str) -> bool: ...
    def objective_for_scope(self, scope_id: str) -> ObjectiveProjection | None: ...

    # Queries
    def get(self, objective_id: str) -> ObjectiveProjection | None: ...
    def list_roots(self, *, authored_by: Literal["user","system"] | None = None
                   ) -> list[ObjectiveProjection]: ...
    def list_by_parent(self, parent_id: str) -> list[ObjectiveProjection]: ...
    def list_by_root(self, root_id: str, *,
                     states: Sequence[ObjectiveState] | None = None,
                     with_unchecked_criteria: bool | None = None,
                     time_bounds: Sequence[str] | None = None
                     ) -> list[ObjectiveProjection]: ...
    def trace_to_root(self, objective_id: str) -> tuple[ObjectiveProjection, ...]: ...
    def trace_objectives_for_scope(self, scope_id: str
                                    ) -> tuple[ObjectiveProjection, ...]: ...

    # pyee emission
    def subscribe_all(self, callback): ...
    def subscribe(self, objective_id: str, callback): ...

    # OTel + event log
    @property
    def emitter(self): ...
    @property
    def store(self) -> EventStore: ...
```

### 7.2 Emission surface

- **pyee:** every event (objective_created, state_transitioned,
  criterion_evaluated, scope_bound, binding_rejected, child_linked)
  fans out to per-objective and global listeners. Same pattern as
  scope-of-work.
- **OTel:** each `ObjectiveRuntime` operation opens a span. Spans
  carry `pos.objective.id`, `pos.objective.root_id`, `pos.objective
  .state`. The no-op tracer applies by default (A1 correction).

### 7.3 How the primary-persona authoring pipeline interacts with objectives

Authoring a new persona runs under an `authoring_scope_id` (v1.2 R14).
The tracker does not change how the pipeline works; it adds an
optional binding between the `authoring_scope_id` and an objective,
created by the caller of the authoring pipeline. Recommended
convention in §7.4 below. The authoring pipeline itself does not need
to know about objectives.

---

## 8. Question group 7 — primary-persona authoring interaction (v1.2 R14)

### 8.1 Convention for the `authoring_scope_id`'s parent objective

The research recommends a **workspace-level evergreen objective** that
every authoring run is bound to:

```python
ObjectiveSpec(
    goal="Maintain a coherent workspace persona roster that covers active work domains",
    kind=ObjectiveKind.user_authored_root,
    acceptance_criteria=(
        AcceptanceCriterion(
            criterion_id="roster-coverage",
            kind=CriterionType.external_predicate,
            description="No request in the last N days declined for lack of a capable persona.",
            predicate_name="roster_coverage_check",
        ),
        AcceptanceCriterion(
            criterion_id="introduction-gate",
            kind=CriterionType.prose,
            description="Every autonomously-authored persona was introduced to the user before first use.",
        ),
    ),
    time_bound=TimeBoundOrEvergreen(
        kind="evergreen", review_cadence_days=30
    ),
    authored_by="user",
)
```

Rationale:
- The authoring pipeline is *by nature* a workspace-maintenance
  activity; binding it to "maintain coherent roster" is the correct
  framing, not "author persona Y" or "improve domain X."
- Every specific authoring run becomes a scope whose goal names the
  domain gap; the scope traces through this root.
- The objective is evergreen — persona roster coverage is never
  "finished."

### 8.2 Do new personas inherit objectives, get their own, or remain objective-less?

Recommendation: **a newly-authored persona is objective-less at
creation.** An objective is for *work*, a persona is an *actor*. The
first scope dispatched to the new persona carries the first objective
binding. This avoids conflating the "a new actor exists" event
(introduction) with "work has been started" (scope + objective).

Future scopes dispatched to the persona bind to whichever objective
the caller chooses (typically an existing domain objective in the
workspace's tree, or a freshly-authored one in the domain the persona
serves).

---

## 9. Acceptance-criterion coverage — mapping spec → design

The table below maps every v1.0 / v1.1 / v1.2 spec item that names
objectives to the piece of the tracker that delivers it.

| Spec item | Design element |
|---|---|
| v1.0 Core primitives — "objective carries parentage, measurability, time-bound" | `ObjectiveSpec` (§2.3) — required `kind`+`parent_id`, `acceptance_criteria`, `time_bound` fields |
| v1.0 Architectural layer — "three behaviours (required above threshold, hierarchical with parentage, referenced consistently)" | Threshold enforcement is workspace-level; hierarchical parentage is built-in (§3); referenced-consistently is the binding API (§3.2) |
| v1.0 Architectural — "alignment is re-checked at every scope boundary and the check is logged; missing check is a process failure flagged by the self-correction loop" | `scope_success` criterion auto-evaluation on scope completion (§5.1); missing-check detection via `tracker.list_by_root(with_unchecked_criteria=True)` surfaced to the primary persona's monitor |
| v1.0 Objective-based — "every scope traces to a top-level user-authored objective" | `trace_objectives_for_scope()` + binding API (§3.2, §4.2); enforcement via dispatch-time binding check (workspace-level) |
| v1.0 Self-correction — "every failure record contains an immediate-fix field with a linked remediation" | `AcceptanceCriterionEvaluated(result=not_met, note=...)` event carries evidence; downstream self-correction loop consumes these |
| v1.0 Self-correction — "every completed scope runs an outcome-vs-objective check" | `scope_success` criterion auto-evaluation fires on `ScopeCompleted` (§5.1) |
| v1.1 R1 — semantic round-trip on upgrade | The tracker is event-sourced (Option C, §2.2); a probe set of objective queries is replayable pre- and post-upgrade |
| v1.1 R11 — OTel emission | Every runtime operation opens a span with `pos.objective.*` attrs (§7.2); no downstream consumer assumed (A1) |
| v1.2 R14 — authoring pipeline runs inside a scope budgeted under the authoring-roster objective (§8.1) | `ObjectiveSpec` user-authored root per §8.1 |
| v1.2 R15 — mandatory introduction before addressability | Not objective-tracker's concern (persona-layer-enforced); tracker does not block addressability |
| v1.2 R16 — framework-not-content | Tracker ships zero objective content; workspaces author their own roots |

**No spec item is surfaced as unsatisfiable.** All criteria can be
honoured by the recommended design, with no sealed-component
amendments.

---

## 10. Schema sketch — full Pydantic draft

```python
from enum import Enum
from typing import Annotated, Literal, Union
from pydantic import BaseModel, ConfigDict, Field

# ---- enums ------------------------------------------------------------

class ObjectiveState(str, Enum):
    draft = "draft"
    active = "active"
    paused = "paused"
    achieved = "achieved"
    abandoned = "abandoned"

class ObjectiveKind(str, Enum):
    user_authored_root = "user_authored_root"
    child = "child"

class CriterionType(str, Enum):
    prose = "prose"
    scope_success = "scope_success"
    child_closure = "child_closure"
    external_predicate = "external_predicate"

class ObjectiveParentClosePolicy(str, Enum):
    notify = "notify"
    cascade_achieved = "cascade_achieved"
    cascade_abandoned = "cascade_abandoned"
    ignore = "ignore"

# ---- nested shapes ----------------------------------------------------

class AcceptanceCriterion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    criterion_id: str = Field(min_length=1)
    kind: CriterionType
    description: str = Field(min_length=1)
    scope_id: str | None = None
    predicate_name: str | None = None

    def model_post_init(self, __ctx) -> None:
        if self.kind == CriterionType.scope_success and not self.scope_id:
            raise ValueError("scope_success criterion requires scope_id")
        if self.kind == CriterionType.external_predicate and not self.predicate_name:
            raise ValueError("external_predicate criterion requires predicate_name")

class TimeBoundOrEvergreen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["time_bound", "evergreen"]
    deadline: str | None = None
    review_cadence_days: int | None = Field(default=None, ge=1)

    def model_post_init(self, __ctx) -> None:
        if self.kind == "time_bound" and not self.deadline:
            raise ValueError("time_bound requires deadline (ISO-8601 UTC)")
        if self.kind == "evergreen" and self.review_cadence_days is None:
            raise ValueError("evergreen requires review_cadence_days")

# ---- ObjectiveSpec ---------------------------------------------------

class ObjectiveSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    goal: str = Field(min_length=1)
    kind: ObjectiveKind
    parent_id: str | None = None
    acceptance_criteria: tuple[AcceptanceCriterion, ...] = Field(min_length=1)
    time_bound: TimeBoundOrEvergreen
    authored_by: Literal["user", "system"]
    owner_persona: str | None = None
    authored_under_scope_id: str | None = None
    parent_close_policy: ObjectiveParentClosePolicy = ObjectiveParentClosePolicy.notify

    def model_post_init(self, __ctx) -> None:
        if self.kind == ObjectiveKind.user_authored_root and self.parent_id is not None:
            raise ValueError("user_authored_root must not have parent_id")
        if self.kind == ObjectiveKind.child and self.parent_id is None:
            raise ValueError("child objective requires parent_id")

# ---- events -----------------------------------------------------------

class _EventBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    objective_id: str
    event_id: int = 0
    created_at: str
    otel_span_id: str | None = None
    otel_trace_id: str | None = None

class ObjectiveCreated(_EventBase):
    kind: Literal["objective_created"] = "objective_created"
    goal: str
    objective_kind: ObjectiveKind
    parent_id: str | None
    acceptance_criteria: tuple[AcceptanceCriterion, ...]
    time_bound: TimeBoundOrEvergreen
    authored_by: Literal["user", "system"]
    owner_persona: str | None
    authored_under_scope_id: str | None
    parent_close_policy: ObjectiveParentClosePolicy

class StateTransitioned(_EventBase):
    kind: Literal["state_transitioned"] = "state_transitioned"
    from_state: ObjectiveState
    to_state: ObjectiveState
    reason: str | None = None

class AcceptanceCriterionEvaluated(_EventBase):
    kind: Literal["acceptance_criterion_evaluated"] = "acceptance_criterion_evaluated"
    criterion_id: str
    result: Literal["met", "not_met"]
    evidence_scope_id: str | None = None
    note: str | None = None

class ChildLinked(_EventBase):
    kind: Literal["child_linked"] = "child_linked"
    child_objective_id: str

class ParentCloseNotified(_EventBase):
    kind: Literal["parent_close_notified"] = "parent_close_notified"
    parent_objective_id: str
    parent_terminal_state: ObjectiveState

class ScopeBound(_EventBase):
    """Emitted when a scope_id is successfully bound to an objective.
    Lives in the objective's event stream."""
    kind: Literal["scope_bound"] = "scope_bound"
    scope_id: str

class ScopeUnbound(_EventBase):
    kind: Literal["scope_unbound"] = "scope_unbound"
    scope_id: str

class BindingRejected(_EventBase):
    kind: Literal["binding_rejected"] = "binding_rejected"
    scope_id: str
    reason: Literal["unknown_objective", "orphan_root", "inactive_root"]

ObjectiveEvent = Annotated[
    Union[
        ObjectiveCreated, StateTransitioned, AcceptanceCriterionEvaluated,
        ChildLinked, ParentCloseNotified, ScopeBound, ScopeUnbound,
        BindingRejected,
    ],
    Field(discriminator="kind"),
]

# ---- public projection ------------------------------------------------

class ObjectiveProjection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    objective_id: str
    goal: str
    kind: ObjectiveKind
    parent_id: str | None
    state: ObjectiveState
    authored_by: Literal["user", "system"]
    acceptance_criteria: tuple[AcceptanceCriterion, ...]
    time_bound: TimeBoundOrEvergreen
    owner_persona: str | None
    authored_under_scope_id: str | None
    children: tuple[str, ...]
    last_evaluation_per_criterion: dict[str, Literal["met", "not_met", "unchecked"]]
    created_at: str
    last_transition_at: str | None
    parent_close_policy: ObjectiveParentClosePolicy

# ---- sidecar binding --------------------------------------------------

class ScopeObjectiveBinding(BaseModel):
    """The enforcement record — a scope is bound to exactly one
    objective. Maintained exclusively by ObjectiveRuntime.bind_scope()."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    scope_id: str
    objective_id: str
    root_id: str          # cached ancestry root for fast list queries
    created_at: str
```

---

## 11. Enforcement mechanism — sketch of the integration test

The key acceptance signal per the brief: **scope-of-work's
`parent_objective_id` reference must become enforceable after the
tracker lands.** The sketch, sized for a `pytest-asyncio`-powered
integration test on the pos-v2 layout:

```python
# tests/integration/test_enforcement.py
import pytest
from pathlib import Path
from objective_tracker import ObjectiveRuntime, ObjectiveSpec, ObjectiveKind
from objective_tracker import AcceptanceCriterion, CriterionType, TimeBoundOrEvergreen
from objective_tracker.errors import UnresolvedObjectiveError, OrphanRootError
from scope_of_work import ScopeRuntime, ScopeSpec, Budget, ReversibilityClass

@pytest.mark.asyncio
async def test_orphan_scope_cannot_bind_to_unknown_objective(tmp_path):
    tracker = ObjectiveRuntime(db_path=tmp_path / "obj.sqlite")
    scopes = ScopeRuntime(db_path=tmp_path / "scope.sqlite")
    try:
        spec = ScopeSpec(
            goal="run analysis",
            constraints=("no writes",),
            budget=Budget(tokens=1000),
            reversibility_class=ReversibilityClass.fully_reversible,
            success_criteria=(),
            observers=(),
            escalation_triggers=(),
        )
        scope = await scopes.create(spec)

        # Unknown objective — must raise deterministically.
        with pytest.raises(UnresolvedObjectiveError):
            await tracker.bind_scope(scope.scope_id, "obj-nonexistent")

        # Binding was not created; not even a BindingRejected event
        # on an unknown objective — there's no objective to emit on.
        assert not tracker.is_bound(scope.scope_id)
    finally:
        scopes.close(); tracker.close()

@pytest.mark.asyncio
async def test_scope_cannot_bind_to_system_authored_orphan_root(tmp_path):
    """A system-authored root — not user-authored — is an orphan root
    for the purposes of scope binding. This is the enforcement of
    v1.0 'every scope traces to a top-level user-authored objective.'"""
    tracker = ObjectiveRuntime(db_path=tmp_path / "obj.sqlite")
    scopes = ScopeRuntime(db_path=tmp_path / "scope.sqlite")
    try:
        sys_root = await tracker.create(ObjectiveSpec(
            goal="system root",
            kind=ObjectiveKind.user_authored_root,
            acceptance_criteria=(AcceptanceCriterion(
                criterion_id="c1", kind=CriterionType.prose,
                description="orphan"),),
            time_bound=TimeBoundOrEvergreen(kind="evergreen", review_cadence_days=30),
            authored_by="system",  # NOT user
        ))
        scope = await scopes.create(valid_spec())
        with pytest.raises(OrphanRootError):
            await tracker.bind_scope(scope.scope_id, sys_root.objective_id)
    finally:
        scopes.close(); tracker.close()

@pytest.mark.asyncio
async def test_happy_path_scope_traces_to_user_authored_root(tmp_path):
    tracker = ObjectiveRuntime(db_path=tmp_path / "obj.sqlite")
    scopes = ScopeRuntime(db_path=tmp_path / "scope.sqlite")
    try:
        root = await tracker.create(ObjectiveSpec(
            goal="maintain health",
            kind=ObjectiveKind.user_authored_root,
            acceptance_criteria=(AcceptanceCriterion(
                criterion_id="c1", kind=CriterionType.prose,
                description="vitals in normal range"),),
            time_bound=TimeBoundOrEvergreen(kind="evergreen", review_cadence_days=90),
            authored_by="user",
        ))
        child = await tracker.create(ObjectiveSpec(
            goal="exercise 3x/week",
            kind=ObjectiveKind.child, parent_id=root.objective_id,
            acceptance_criteria=(AcceptanceCriterion(
                criterion_id="c1", kind=CriterionType.prose,
                description="3 sessions logged this week"),),
            time_bound=TimeBoundOrEvergreen(kind="time_bound",
                                             deadline="2026-12-31T23:59:59Z"),
            authored_by="user",
        ))
        scope = await scopes.create(valid_spec())
        binding = await tracker.bind_scope(scope.scope_id, child.objective_id)
        assert binding.root_id == root.objective_id
        chain = tracker.trace_objectives_for_scope(scope.scope_id)
        assert len(chain) == 2
        assert chain[0].objective_id == child.objective_id
        assert chain[-1].objective_id == root.objective_id
    finally:
        scopes.close(); tracker.close()

@pytest.mark.asyncio
async def test_scope_completion_fires_criterion_evaluation(tmp_path):
    """The integration hook: scope completion auto-evaluates bound
    scope_success criteria."""
    tracker = ObjectiveRuntime(db_path=tmp_path / "obj.sqlite",
                                scope_runtime=... )  # subscribe to scope events
    ...
    # on scope.complete(), the tracker's subscriber fires
    # AcceptanceCriterionEvaluated(result=met) for any criterion with
    # kind=scope_success and scope_id == completed.scope_id.
```

The critical test is the second one (`test_scope_cannot_bind_to_
system_authored_orphan_root`). It verifies the load-bearing
invariant that ripples through every workspace policy: only
user-authored roots anchor scope binding. Without this, the
"user-authored root" part of the spec is unenforceable.

---

## 12. ODD integration sketch — how tests are authored against objectives

See §6.4 for the harness sketch. The canonical test-authoring pattern:

```python
# Declarative: criterion author registers a criterion on the tracker.
await tracker.create(ObjectiveSpec(
    goal="launch MVP by Q3",
    kind=ObjectiveKind.child, parent_id=root_id,
    acceptance_criteria=(
        AcceptanceCriterion(
            criterion_id="launch-c1",
            kind=CriterionType.external_predicate,
            description="Public landing page returns HTTP 200",
            predicate_name="http_200_on_landing",
        ),
    ),
    time_bound=TimeBoundOrEvergreen(kind="time_bound",
                                     deadline="2026-09-30T23:59:59Z"),
    authored_by="user",
))

# Imperative: the predicate is registered in the ODD harness.
@odd_predicate("http_200_on_landing")
async def _predicate() -> bool:
    async with httpx.AsyncClient() as client:
        r = await client.get("https://example.com/")
        return r.status_code == 200

# The ODD harness runs the predicate and pushes the result through
# the tracker's evaluation API.
```

The shape — criteria-as-data, predicates-as-code, binding-by-id — is
identical to how pytest binds test functions to pytest collection
objects by name. The difference is the unit of work: ODD binds to
criteria that are children of objectives, not scenarios under
features. The tracker is the collection mechanism.

---

## 13. Dependency map

### 13.1 What depends on the tracker (downstream)

| Consumer | How |
|---|---|
| **Every future scope** (workspace dispatch policy) | Bound via `tracker.bind_scope(...)` before dispatch; no binding = no dispatch |
| **ODD test harness** | Reads `list_by_root(...)`, calls `evaluate_criterion(...)`, subscribes to `tracker.emitter` |
| **Primary persona (monitoring)** | Subscribes to evaluation events, includes "objective X moved to achieved" in briefings |
| **Self-correction loop (future phase)** | Subscribes to `result=not_met` events; proposes re-extensions |
| **Observability aggregator (future)** | Consumes OTel spans from `pos.objective.*` |
| **Upgrade harness (v1.1 R1)** | Replays objective event log; drift probe compares pre/post |
| **Primary-persona authoring (v1.2 R14)** | Optional — the workspace convention binds authoring scopes to the roster-maintenance objective (§8.1) |

### 13.2 What the tracker depends on (upstream)

| Dependency | Hardness |
|---|---|
| **scope-of-work runtime** | Soft — the tracker can be used without it (no `scope_success` criteria, no binding API value). With it, the tracker subscribes to `subscribe_all()` for scope completion events |
| **Memory system** | None |
| **Primary-persona layer** | None at the primitive level |
| **stdlib + pydantic + pyee + opentelemetry-api/sdk + PyYAML** | Hard — no other runtime dependency |
| **pytest, pytest-asyncio** | Test-only, per STATE.md rule 8 |

### 13.3 No sealed-component amendments

As laid out in §1.4, every dependency is additive. The tracker does
not require changes to scope-of-work, memory, or the primary-persona
layer.

---

## 14. Complexity estimate

Baseline: the tracker is materially simpler than the primary-persona
layer. No authoring pipeline, no compaction-survival machinery, no
LLM-inside, no introduction protocol.

Comparison with scope-of-work: similar architecture (event-sourced
SQLite, pyee, OTel), fewer event kinds (8 vs 13), no budget axes, no
parent-close cascade complexity (notify-by-default is lighter than
scope-of-work's three-way ABANDON/TERMINATE/REQUEST_CANCEL).

**Estimate: 340–420 AI-minutes**, broken down:

| Work item | AI-minutes |
|---|---|
| Pydantic spec + events (§10) | 30–40 |
| Event store (SQLite WAL; subset of scope-of-work's store) | 40–60 |
| Projection + read model | 40–50 |
| Runtime (`ObjectiveRuntime`) — lifecycle + decomposition APIs | 40–60 |
| Binding API (sidecar table, subscriber to scope events) | 30–50 |
| Acceptance-criterion evaluation (recording + auto-eval for scope_success / child_closure) | 30–40 |
| Queries (`list_*`, `trace_*`, `trace_objectives_for_scope`) | 30–40 |
| pyee fan-out + OTel spans | 15–20 |
| Tests: unit (schema, state machine, criterion evaluation) | 40–50 |
| Tests: integration (the three tests in §11, plus upgrade-fidelity probe) | 40–60 |
| Bundled documentation (prose, data-flow, relationship map — mandatory per v1.1 R4) | 40–60 |

**Range justification:** the low end assumes the store and projection
patterns are lifted from scope-of-work with minor changes; the high
end accounts for the `scope_success` / `child_closure` auto-evaluation
code path, which is new territory.

If proposal-stage clarifications (especially the "user-authored root"
definition) trigger spec revisions, add 30–60 minutes.

---

## 15. Prototyping priorities — questions only a prototype can answer

1. **Cross-process subscriber latency.** If the tracker and scope
   runtime are in different processes (future Phase 3 work), how
   quickly does a scope `completed` event propagate to an
   auto-evaluation on the tracker? Expected: <100 ms via pyee's
   polling pattern plus SQLite event-log tail. Prototype would
   measure.
2. **Binding rejection semantics at high rates.** If a workspace
   policy binds every scope before dispatch and the tracker is
   enforcing orphan rejection, how many rejections per second can
   the tracker handle without starving the dispatcher? Not expected
   to matter at pOS scale (≤10/min) but worth a quick measurement.
3. **ODD test-harness UX.** Is the `@odd_predicate("name")`
   registration + `external_predicate` criterion the right shape? A
   prototype harness running against the synthetic test-world used
   for memory's D2 would answer. If it isn't, variants: decorators
   on criteria themselves (like pytest parametrize), collection
   scanning, plugin entry points (the hypothesis pattern §10
   references).
4. **`scope_success` + `child_closure` interaction.** When an
   objective has one criterion of each kind, the evaluation order
   matters. Prototype verifies that the projection correctly
   computes "all criteria met" even when the order of events is
   child-closure-first vs scope-success-first.
5. **Upgrade-fidelity probe shape for objectives.** The memory
   system's probe is semantic (run the same search, check the
   answer). The scope-of-work probe is event-replay. For
   objectives, should the probe be event-replay, state-query, or
   a hybrid? Prototype would help decide.

None of these block the research → proposal hand-off. All can be
resolved as early build steps.

---

## 16. Survey — existing patterns

### 16.1 BDD test runners (behave, pytest-bdd)

- **Structure:** `features/*.feature` files define a hierarchy of
  `Feature > Scenario > Step`. `Background` applies to every
  scenario in a feature. Tags at feature and scenario levels group
  tests.
- **Relevance to ODD:** tests are bound to behaviours, not
  objectives. The grouping shape ("feature" as a folder, "scenario"
  as a grouped test, tags as a cross-cutting concern) is a useful
  pattern — but the primitive the runtime stores is a scenario, not
  an objective. pytest-bdd does not record *why* a scenario exists,
  which is exactly what an objective does.
- **What carries over:** the idea of **tests as data + predicates as
  code**, bound by stable id; decorators that register predicates
  against ids; a central store that a runner walks.
- **What does not carry over:** the given-when-then shape (ODD is
  "evidence that criterion is met," not "given state, when action,
  then outcome"); the folder-per-feature layout (the tracker is a
  single store, not a filesystem tree).

Sources:
- [pytest-bdd documentation](https://pytest-bdd.readthedocs.io/en/latest/)
- [Behave Feature Testing Setup](https://behave.readthedocs.io/en/latest/gherkin/)
- [pytest-bdd on PyPI](https://pypi.org/project/pytest-bdd/)

### 16.2 OKR tooling (Lattice, Gtmhub/Quantive)

- **Structure:** parent-child links between objectives at company,
  team, and individual levels. Key Results are the measurable
  progress markers. Cascade vs alignment is a modelling question
  each platform answers differently.
- **Relevance to ODD:** OKR hierarchies are *structurally* what ODD
  needs — parent-child trees, measurable criteria, cascade on close.
  Where OKR tooling diverges: they assume human teams and quarterly
  cadences, both of which the pOS tracker does not need.
- **Modelling lesson:** the "Alignment data type" pattern Jeff
  Gothelf and others describe (parent-child as an explicit link,
  not a nested-tree embedding) matches the recommended design
  (`parent_id` on the child, not a nested structure). This keeps
  moves (re-parenting) cheap.
- **Divergence:** OKR tooling does not natively express "testable
  criterion" beyond KPI metrics. ODD needs the four-variant model
  (§2.5) because scope completion and external predicates are not
  KPI values.

Sources:
- [Aligning, Not Cascading, OKRs - Jeff Gothelf](https://jeffgothelf.com/blog/aligning-not-cascading-okrs-with-an-okr-lineage/)
- [Cascading OKRs - What Matters](https://www.whatmatters.com/faqs/cascading-top-down-okr-examples)
- [Understanding views in Viva Goals - Microsoft Learn](https://learn.microsoft.com/en-us/viva/goals/understanding-views)
- [OKR hub – Jira Align](https://help.jiraalign.com/hc/en-us/articles/9537263535252-OKR-hub)

### 16.3 LangGraph goal-state modelling

- **Structure:** state is a shared dict; goals are modelled as
  destinations a supervisor node routes toward; hierarchical agent
  teams compose subgraphs with a top-level supervisor.
- **Relevance to ODD:** LangGraph provides a *runtime graph*, not a
  *persistent objective store*. It is closer to the scope-of-work
  primitive than to the objective tracker. Its hierarchical
  supervisor pattern is useful as a consumer shape — the primary
  persona in pOS plays the supervisor role — but LangGraph's
  goal-state is not persistent across sessions in the way the
  tracker needs to be.
- **What carries over:** supervisor-routes-to-worker as the dispatch
  pattern; state-as-shared-memory within a run. Neither is a
  tracker concern.
- **What does not carry over:** the graph-as-runtime model; the
  stateless-between-runs assumption.

Sources:
- [LangGraph Hierarchical Agent Teams](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/hierarchical_agent_teams/)
- [LangGraph GitHub](https://github.com/langchain-ai/langgraph)
- [Workflows and agents - LangChain Docs](https://docs.langchain.com/oss/python/langgraph/workflows-agents)

### 16.4 Hypothesis (stateful / invariant plugins)

- **Structure:** entry-point-based plugin registration; invariant
  decorators that run after every rule in stateful testing.
- **Relevance to ODD:** the entry-point mechanism is a clean way to
  register external predicates without coupling them to the
  tracker's code. A workspace's ODD harness could register
  `external_predicate` resolvers via entry points; the tracker
  would discover them on startup.
- **What carries over:** the plugin-by-entry-point idiom is idiomatic
  Python and well-documented; if the tracker ever needs external
  predicate discovery, this is the pattern.
- **What does not carry over:** the stateful-testing model's rule /
  state machine shape. That is much closer to scope-of-work's
  state-machine than to the objective tracker.

Sources:
- [Hypothesis Stateful Testing Documentation](https://hypothesis.readthedocs.io/en/latest/stateful.html)
- [Hypothesis Third-Party Extensions](https://hypothesis.readthedocs.io/en/latest/extensions.html)
- [Hypothesis Plugin - Pydantic v1.10](https://docs.pydantic.dev/1.10/hypothesis_plugin/)

### 16.5 Hierarchical Task Network (HTN) planners

- **Structure:** methods decompose abstract tasks into ordered
  subtasks; operators are primitive actions with preconditions and
  effects.
- **Relevance to ODD:** HTN decomposition is structurally what ODD
  negative-case re-extension does — an abstract goal decomposes into
  concrete sub-goals that are testable. GTPyhop is the closest
  Python reference. However, HTN planners consume task
  *declarations*; they do not persist a runtime objective tree that
  evolves across sessions.
- **What carries over:** the decomposition pattern (parent
  objective → ordered children) is the same shape; the language of
  "primitive action" vs "abstract task" maps onto "scope_success
  criterion" vs "child_closure criterion."
- **What does not carry over:** HTN's planning phase (solving a goal
  by searching method combinations) is not something the tracker
  does. ODD does not *plan*; it *registers and evaluates.*

Sources:
- [GTPyhop - A Hierarchical Goal+Task Planner in Python (PDF)](https://www.cs.umd.edu/~nau/papers/nau2021gtpyhop.pdf)
- [Hierarchical Task Network Planning in AI - GeeksforGeeks](https://www.geeksforgeeks.org/artificial-intelligence/hierarchical-task-network-htn-planning-in-ai/)
- [GPT-HTN-Planner GitHub](https://github.com/DaemonIB/GPT-HTN-Planner)

### 16.6 Temporal's parent-close policy

- **Structure:** `ABANDON` / `REQUEST_CANCEL` / `TERMINATE`, with
  `TERMINATE` as default.
- **Relevance:** scope-of-work already uses this pattern. For
  objectives, the research recommended a different default
  (`notify`) because the semantics of "parent objective abandoned"
  are different from "parent workflow cancelled." A cancelled
  workflow stops work; an abandoned objective is a decision to stop
  *caring*. Propagating "stop caring" downward by default is more
  aggressive than the user likely wants; propagating "stop work"
  downward by default is correct for workflows.
- **What carries over:** the three-way-policy shape is clean and
  well-understood; the tracker adopts a four-way variant with
  `notify` as the default.
- **What does not carry over:** the default of `TERMINATE` — wrong
  for objectives.

Sources:
- [Temporal Parent Close Policy Documentation](https://docs.temporal.io/parent-close-policy)
- [Temporal Child Workflows Documentation](https://docs.temporal.io/child-workflows)

### 16.7 Event sourcing libraries (pyeventsourcing, etc.)

- **Structure:** `eventsourcing` (pyeventsourcing) provides an event
  store abstraction, aggregate root pattern, and optional SQLite
  backend with WAL.
- **Relevance:** the library would save implementation time but
  introduces a runtime dependency not on the brief's permitted list
  — halt signal. Scope-of-work took the hand-rolled path for the
  same reason. The tracker follows suit: hand-rolled event store
  mirroring scope-of-work's.
- **What carries over:** the pattern (append-only events, projection
  from events, event_id ordering). Rebuilt, not imported.

Sources:
- [eventsourcing - Python event sourcing library](https://eventsourcing.readthedocs.io/)
- [eventsourcing on PyPI](https://pypi.org/project/eventsourcing/)

---

## 17. Closing — halt signals explicitly restated

Two halt signals this research surfaces for owner's review before
proposal authoring:

**Halt signal #1 — scope-of-work has no `parent_objective_id`.** The
research plan anticipated a field that does not exist in the sealed
code. The research has proceeded under the sidecar-binding model
(§3.2, Shape A) which requires no amendment to scope-of-work. This
is the *recommended* path. If the owner prefers Shape C (amend scope-of-
work to add the field), that is a separate conversation — the
amendment would require reopening the sealed component. The
research's position: **do not reopen.** The sidecar model is clean
and deterministic; reopening a sealed component to add a field that
the sidecar handles is a cost with no matching benefit.

**Halt signal #2 — "user-authored root" is undefined in the spec.**
The research proposes a definition (§3.3) and makes it load-bearing
on the enforcement test (§11). the owner must confirm the definition in
the proposal phase before implementation begins. This is a small
halt — the definition is short, clean, and well-constrained — but
surfacing it now is the correctness-over-momentum path.

Everything else in the research plan's seven question groups can be
satisfied under the stated constraints. No v1.0 / v1.1 / v1.2 spec
criterion is surfaced as unsatisfiable.

**Ready for proposal authoring once the owner has seen these two signals
and either confirmed the recommended paths or redirected.**
