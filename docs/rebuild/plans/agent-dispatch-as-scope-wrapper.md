# Plan — A8 agent-dispatch-as-scope wrapper

**Status:** plan (post-R1-revision, pre-dispatch). 2026-04-26.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored against HEAD:** `de5fe11` (post amendment #47 SHA-record commit).
**Revised against HEAD:** `5ad5f68` (post amendment #51 HALT-prefix commit;
fence widened to orchestrator/ per the R1 ruling locked by Luke
2026-04-26 in response to the §8.1.1/§8.6 halt-and-surface report at
`.scratch/claude-output/A8-halt-surface-2026-04-26.md`).
**Pre-amendment tip:** placeholder — captured at brief-dispatch
(`baseline: <sha>` in the manifest, BASELINE-as-HEAD~1 pattern per
amendments #29 / #34-#51).
**Amendment number:** unassigned at authoring; assigned #52 at dispatch.
Plan filename slug: `agent-dispatch-as-scope-wrapper`.
**Research (governs):**
`docs/rebuild/plans/research/harness-usage-audit-2026-04-26.md`
(audit headline: A8 is the highest-leverage move; cost-governance
gate is starved by structural omission, not design). Audit §11
locks the surface.
**Composes on (sealed):** `scope-of-work` (Phase 1 — `ScopeSpec`,
`Budget`, `ReversibilityClass`, `SuccessCriterion`),
`session-resilient orchestrator` (Phase 2 — `IPCClient`,
`activate_scope` IPC), `cost-governance` (Phase 3 —
`register_cost_governance_ipc`'s innermost wrap, `cost.status`
IPC), `safety-layer` (Phase 3 — wrap), `reversibility-primitive`
(Phase 3 — wrap), `objective-tracker` (Phase 1 — `bind_scope`
already runs inside `activate_scope`), `primary-persona` (sealed,
amendments #32/#33/#35–#37/#40/#46/#48 — wrapper lives here,
mirrors the live MCP client pattern from amendment #48).
**Owner directive (locked 2026-04-26 under confidence-delegation):**
A8 wraps Agent tool dispatches in a `ScopeSpec` so the four-gate
chain (safety / reversibility / cost / orchestrator) fires on
every dispatch. Audit D1 ruled in favour of A8 over a separate
token-accounting layer. Most decisions in §6 are mechanical
follow-throughs; this plan-doc surfaces only genuine uncertainty.

---

## 1. Summary / TLDR

Today exactly one production code path constructs a `ScopeSpec`
(`self-correction/src/spec_builder.py`). Every Agent dispatch the
primary persona issues runs *outside* `activate_scope` and
therefore *outside* the four-gate chain. Effect: cost-governance
ledger is empty; 80%-throttling cannot fire; `cost.status` IPC
has zero callers; safety / reversibility wraps observe nothing on
the dominant traffic shape. Amendment A8 closes the gap by
adding a **dispatch wrapper** that:

1. Takes the persona's natural-language Agent dispatch
   (objective, constraints, halt conditions, expected duration).
2. Constructs a `ScopeSpec` with `Budget(time_seconds, tokens,
   money_cents)` inferred from the duration-estimation rubric
   (memory bullet `feedback_duration_estimation_rubric`).
3. Calls `activate_scope` over the orchestrator's `IPCClient`.
4. On approval (gate chain green), invokes the actual Agent tool.
5. Emits `BudgetDebited` / `BudgetRefunded` against the scope's
   id during and after the dispatch.
6. On dispatch close, transitions the scope to
   `completed | failed | cancelled`; reservations reconcile.

After A8 lands, every persona-issued Agent dispatch exercises the
four-gate chain. Cost ledger fills with real reservations; the
80% ceiling-warning pathway fires for the first time on
non-correction work; `cost.status` becomes a meaningful surface
the persona can query for its awareness block.

Sealed-component fence: `primary-persona/` + `orchestrator/`
(R1-revised — see ODD §4 re-extension note below). The existing
`activate_scope` IPC takes only `(scope_id, objective_id)` and has
no path to register a `ScopeSpec` for the wrap chain to read. The
production `spec_resolver` defaults to `None` for any scope not
constructed in-process by the orchestrator runtime, so the cost-gov
wrap silently passes without reserving (verified empirically — see
the halt-surface report). The R1 fix: orchestrator/ exposes a new
IPC method `activate_scope_with_spec(scope_id, objective_id,
spec_payload)` that calls `scope_runtime.create(spec, scope_id=...)`
in-process before activating, so the in-memory `CostLedger`
subscriber fires and the wrap chain has a non-None spec to gate on.
The persona-side wrapper calls the new IPC method instead of the
existing `activate_scope`. Existing `activate_scope` IPC stays
registered for backwards-compat with self-correction's same-process
path.

This is sibling-shaped to amendment #48 (primary-persona +
hands-off-lifecycle) and amendment #50 (primary-persona +
workspace-bootstrap) — two-component amendments where the persona
gains a primitive that requires a small partner-component edit to
unblock production wiring.

Per CLAUDE.md output convention, owner reads from §6 (decisions
for owner) — every other section supports it.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Named spec objectives this amendment satisfies:**

- **v1.1 R12 — Cost governance refined.** R12 codifies that
  token + cost tracking aggregates by prompt-type AND per-scope.
  Today no Agent dispatch produces a per-scope reservation; the
  per-scope-aggregation surface is empty. A8 makes per-scope
  aggregation truthful for the dominant traffic shape. (R12's
  acceptance addition — "per-prompt-type aggregation is queryable
  and a test workload with varied prompt types confirms
  attribution" — is *not* this amendment's surface; A8 makes the
  per-scope axis live, prompt-type axis is downstream.)
- **v1.0 Cost governance — aggregate ceilings.** Session +
  rolling ceilings configured in `~/.pos/cost/ceilings.yaml`
  cannot debit because nothing reserves. A8 makes the ceiling
  pathway exercisable on every persona-issued dispatch.
- **v1.0 Scope-of-work primitive — seven-field declaration.**
  The audit's central finding: `ScopeSpec` is built,
  Pydantic-validated, IPC-routed, and produced by exactly one
  caller. A8 makes the persona a first-class producer of
  `ScopeSpec` instances per dispatch.
- **VALUE_PROPOSITION's two tests (the prime objective ACs).**
  - *Primary-persona test (AC.PO.1):* persona's Agent dispatches
    carry declared budgets; the persona answers from the cost
    surface ("we're at 60% of today's tokens; let me batch the
    next two reads") without the user managing tokens. Token
    discipline is a translation-layer concern per
    VALUE_PROPOSITION §"the primary persona is a translation
    layer" (paragraph 4).
  - *Harness test (AC.PO.2):* the dispatch wrapper is a reusable
    primitive every future persona-side dispatcher (scheduled
    routines, background monitors, retry loops) composes against.

**Sealed-component amendment classification.** Two sealed
components touched (R1-revised):

- `primary-persona`: new `dispatch_wrapper.py` module + a single
  persona-callable public surface. Pure-additive (existing
  `session_start_emitter`, `stop_emitter`, `mcp_memory_client`
  unchanged). Tests added.
- `orchestrator`: new `activate_scope_with_spec` Python surface +
  IPC handler. Pure-additive (existing `activate_scope` Python
  surface + IPC handler unchanged — backwards-compat preserved per
  AC.A8.A2). Tests added.

Sibling shape to amendments #48 (primary-persona +
hands-off-lifecycle) and #50 (primary-persona +
workspace-bootstrap).

**ODD §2.5 reverse direction.** Every code path, branch,
dependency, and test in this amendment must trace back to a
named AC under §5. No silent branches; no defensive `if`s without
backing AC.

---

## 3. Three-lens analysis

### Lens 1 — Claude leverage

**What Claude capability does this lean on or extend?** Two:

1. **Claude Code's `Agent` tool.** Claude-native dispatch
   primitive (the persona uses it on most non-trivial turns).
   The wrapper is invoked *before* `Agent` runs and *after* it
   returns; the actual dispatch shape is unchanged. No
   re-implementation of agent dispatch; A8 composes around the
   Claude-native primitive.
2. **MCP / IPC orchestration.** The orchestrator's existing
   Unix-socket JSON-RPC IPC (`IPCClient` in
   `orchestrator/src/ipc.py:240`) is the same one cost / safety
   / reversibility wraps already use. The wrapper opens an
   `IPCClient`, calls the new `activate_scope_with_spec` method,
   lets the wrap chain fire (the new method invokes the same
   `wrapped_activate_scope` chain as `activate_scope` after
   registering the spec in-process), then proceeds.
   Composition + a single small extension (new IPC method
   added to `orchestrator/`) — see §3 fence note for why the
   extension is necessary.

This is textbook Lens 1 with one minimal extension: the existing
primitives drive 95% of the surface; the new IPC method is the
load-bearing 5% that closes the structural gap audited in
`harness-usage-audit-2026-04-26.md` §11.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation
burden?* YES — load-bearing. Today the persona has no
relationship to cost; the user pays the translation cost (counts
tokens themselves, watches context rot themselves, asks
"how much did that cost?" and gets no structural answer).
VALUE_PROPOSITION §"the primary persona is a translation layer"
paragraph 4 names this *exact* failure mode: *"if the user is
thinking about tokens, the translation layer has failed."* A8
moves token discipline into the harness; the persona answers
from `cost.status` instead of inferring.

**Harness test.** *Does this add to the toolkit the primary
persona can draw from?* YES. The wrapper is the missing primary
producer of `ScopeSpec` — once it lands, every other harness
surface starved of input becomes alive:

- Cost ledger debits per dispatch.
- Safety wrap inspects every dispatch's reversibility class.
- Reversibility wrap binds compensations on every
  compensatable / irreversible dispatch.
- Observability aggregator's span chain captures every dispatch.
- Self-correction's scope-failure detector fires on Agent
  failures.
- 80% ceiling warning becomes reachable (currently zero
  production fires).

This is the audit's "wired but starved" pattern's structural
fix — one move, five harness surfaces become productive.

### Lens 3 — ODD authoring

ACs are outcome-shaped. No method in any AC. Behaviour-count
forward direction in §5.x. Reverse direction is the builder's
audit; the plan is structured so reverse-trace is mechanical
(every behaviour maps to one AC; every code path the eventual
builder produces traces back to one AC).

---

## 4. Objective

The primary persona's Agent-tool dispatches participate in the
session-resilient orchestrator's four-gate chain as first-class
scopes of work. Every Agent dispatch the persona issues opens a
`ScopeSpec` (with declared budget, reversibility class, success
criteria) via `activate_scope` over the orchestrator IPC, awaits
the chain's verdict (safety + reversibility + cost), and only on
approval invokes the underlying `Agent` tool. The dispatch
emits `BudgetDebited` / `BudgetRefunded` against the scope's id
during and at completion, and transitions the scope to a
terminal state (`completed | failed | cancelled`) when the
agent returns or halts. The wrapper is fail-soft against a
detached / unavailable orchestrator (the dispatch proceeds
through a documented fallback path), but the *expected* path is
gate-then-dispatch; the wrapper is the structural primitive that
makes cost-governance, safety-layer, reversibility-primitive,
observability-aggregator, and self-correction productive on the
dominant traffic shape (persona Agent dispatches).

---

## 5. Acceptance criteria

Each AC is outcome-shaped. Forward behaviour-count check in
§5.x. The §2.5 reverse direction is the builder's pre-seal audit
(restated as halt-and-signal trigger in §8).

### AC.A8.1 — Wrapper constructs a valid `ScopeSpec` from a dispatch shape

Given a dispatch shape carrying `objective: str`,
`constraints: tuple[str, ...]`, `halt_conditions: tuple[str,
...]`, `expected_duration_seconds: float`,
`reversibility_class: ReversibilityClass`, and at least one
budget axis, calling the wrapper's spec-construction surface
returns a `ScopeSpec` whose Pydantic validation passes. The
returned `ScopeSpec` carries: `goal` populated from `objective`;
`constraints` carrying the inputs verbatim; `budget` declared on
at least one axis; `reversibility_class` matching the input;
`success_criteria` containing at least one `SuccessCriterion`
derived from the halt-conditions tuple; `expected_duration_seconds`
populated.

### AC.A8.2 — Budget inference from the duration-estimation rubric

Given a dispatch shape carrying only an `expected_duration_seconds`
hint and a task-shape category label drawn from the rubric's
six-row table (memory bullet
`feedback_duration_estimation_rubric`), the wrapper's
budget-inference surface returns a `Budget` whose `time_seconds`
and `tokens` axes are non-None and whose values fall within the
rubric's documented bounds for that category. (Money axis is
optional per the rubric's "tokens map to money via per-axis
config" downstream; A8 declares time + tokens as the minimum
inferred axes.)

### AC.A8.3 — Wrapper calls `activate_scope_with_spec` and respects the gate verdict

Given a constructed `ScopeSpec` and a reachable orchestrator
IPC, the wrapper's dispatch surface opens an `IPCClient`,
calls `activate_scope_with_spec(scope_id, objective_id,
spec_payload)` (the new IPC method per AC.A8.A1), and:

- On gate-chain approval (no exception): invokes the underlying
  Agent tool with the original dispatch payload.
- On gate-chain refusal (`ApplicationError` with code `-32060`,
  `-32061`, `-32062` from cost; `-32070..-32079` from safety;
  `-32080..-32089` from reversibility — error-code ranges
  inherited from the sealed components): the underlying Agent
  tool is **not** invoked; the wrapper surfaces a structured
  refusal object with the gate code, the rejecting gate's name,
  and the reason text.

### AC.A8.4 — `BudgetDebited` / `BudgetRefunded` emission

For an approved dispatch that runs to completion, the wrapper
emits `BudgetDebited` events against the scope id during the
dispatch (at minimum: one `BudgetDebited` recording the
agent-reported `total_tokens` post-dispatch). On dispatch
failure or cancellation before reservation is fully consumed,
a `BudgetRefunded` event is emitted reconciling the unconsumed
remainder. After dispatch close,
`CostStore.get_reservation(scope_id)` returns a row whose
`debited_tokens` field equals the agent-reported tokens (or
zero when the dispatch refused without running).

### AC.A8.5 — Scope state transitions to a terminal state on dispatch close

Every dispatch issued through the wrapper transitions its scope
to exactly one of `completed | failed | cancelled` before the
wrapper returns control to the persona. No scope opened by the
wrapper is left in `active` after wrapper return.
(`StateTransitioned` events for the close transition appear in
the scope-of-work emitter's event log.)

### AC.A8.6 — Orchestrator unreachable: documented fallback path

Given the orchestrator IPC socket is unreachable (path missing,
connection refused, timeout), the wrapper emits a structured
diagnostic to a workspace-local log
(`<workspace>/.pos/dispatch-wrapper.log`, NDJSON, mirroring
amendment #48 D8) AND proceeds with the underlying Agent tool
unwrapped. The wrapper does not block the user's dispatch on a
detached harness. (Outcome: the persona's Agent calls do not
hard-fail when the orchestrator daemon is not running; the
fallback path is observable via the diagnostic log so the
operator can detect the harness is absent.)

### AC.A8.7 — Refusal surfacing to the persona

When the gate chain refuses a dispatch, the wrapper's structured
refusal object carries:
`gate_code: int`,
`rejecting_gate: Literal["safety", "reversibility", "cost"]`,
`reason: str`,
`scope_id: str`,
and is returned to the persona caller as a non-exception value
(not raised) so the persona can route the refusal to user
narration without exception-handling boilerplate. The persona's
own narration of the refusal is downstream of A8 (out of scope —
§9); A8 owns the structured surface only.

### AC.A8.8 — Idempotent re-dispatch on persona retry

Given a dispatch the persona retries verbatim within the same
session (same objective text, same constraints, same persona
session id), the wrapper opens a *new* scope id for each
attempt (each retry is a distinct scope). Reservations from
prior attempts are *not* re-charged; each scope's budget is
reserved independently. (Behaviour: the audit trail preserves
each attempt as its own scope; the cost ledger does not silently
double-count retries.)

### AC.A8.9 — Wrapper public surface is callable from the persona

The wrapper exposes a single public callable
(`primary_persona.dispatch_wrapper.dispatch_with_scope` — name
is method, but **the AC is "the persona has one entry point
that takes a dispatch shape and returns the dispatch result or
a structured refusal"**). A persona-callable test fixture
constructs a dispatch shape, calls the wrapper, and observes
the dispatch ran (or refused) without further IPC plumbing in
the caller.

### AC.A8.10 — Backwards-compat: existing #46 / #47 / #48 / #50 / #51 behaviours unchanged

Existing tests in `primary-persona/tests/`,
`hands-off-lifecycle/tests/`, `workspace-bootstrap/tests/`,
`cost-governance/tests/`, `safety-layer/tests/`,
`reversibility-primitive/tests/`,
`scope-of-work/tests/`, and `orchestrator/tests/` (notably the
`test_no_sealed_amendments.py` family for every sealed
component) stay green after this amendment lands.

### AC.A8.A1 — Orchestrator exposes `activate_scope_with_spec` IPC

The orchestrator IPC server registers a new method
`activate_scope_with_spec` whose params payload carries
`scope_id: str`, `objective_id: str`, and a `spec` payload
(JSON-encoded `ScopeSpec`). On call, the orchestrator:

1. Decodes the spec payload into a `ScopeSpec` (Pydantic
   validation; malformed payloads raise `ApplicationError(-32602)`).
2. Calls `scope_runtime.create(spec, scope_id=<param>)` to
   register the spec with the in-process runtime — so the
   in-memory `CostLedger` subscriber sees the `ScopeCreated`
   event AND the cost-gov wrap's `spec_resolver(scope_id)` call
   path (Path B in the halt-surface report:
   `scope_runtime.get(scope_id).spec` — but here we expose the
   spec via the channel-registry resolver, not via projection).
3. Invokes the existing `wrapped_activate_scope` IPC chain
   (cost / reversibility / safety / orig — installed by the
   workspace-bootstrap adapters in the production wiring) with
   `{scope_id, objective_id}` so the gate chain fires identically
   to a direct `activate_scope` call.

The error-shape on each gate's refusal mirrors the existing
`activate_scope` IPC's surface (same `ApplicationError` codes;
same `ScopeNotPending` / `BindRefused` wraps). On success the
return value carries the `activate_scope` result plus the
`scope_id` echoed back.

### AC.A8.A2 — Existing `activate_scope` IPC stays registered and unchanged

The existing `activate_scope` IPC method remains registered on
the orchestrator with its existing signature (`scope_id`,
`objective_id`) and existing behaviour. Tests that call
`activate_scope` directly (notably `test_d5_bind_scope.py`) pass
unchanged. Self-correction's same-process path
(`controller.create_scope_fn` -> `scope_runtime.create` ->
`activate_scope`) is unaffected.

### AC.A8.A3 — Orchestrator exposes `record_dispatch_close` IPC

The orchestrator IPC server registers a method
`record_dispatch_close` whose params payload carries
`scope_id: str`, `terminal_state` ∈ `{"completed", "failed",
"cancelled"}`, and `debited_tokens: int = 0`. On call, the
orchestrator:

1. If `debited_tokens > 0`, calls `scope_runtime.debit(scope_id,
   output_tokens=...)` so a `BudgetDebited` event lands in the
   in-process scope-of-work event store and the in-memory
   CostLedger subscriber fires.
2. Transitions the scope to `terminal_state` via the
   corresponding `scope_runtime.complete | fail | cancel`
   call.

This is the close-emission surface paired with
`activate_scope_with_spec`. AC.A8.4 (BudgetDebited /
BudgetRefunded emission) and AC.A8.5 (scope reaches terminal
state) become reachable via this IPC method.

**§4 re-extension note:** AC.A8.A3 is added during builder-plan
authoring (2026-04-26) — the original plan's §5 named
AC.A8.4 + AC.A8.5 as outcome-shaped behaviours but did not
expose a load-bearing IPC method through which the persona's
out-of-process wrapper could drive them. AC.A8.A3 names that
method explicitly so the contract → code mapping is traceable
(ODD §2.5 forward + reverse). This is the second §4
re-extension in this amendment cycle (the first being the R1
fence widening, recorded in §14).

### AC.A8.11 — Cost-status reachable for persona awareness

After at least one dispatch closes through the wrapper,
`cost.status` IPC returns a non-empty `active_reservations` list
during the dispatch's lifetime AND a non-empty `session_rollup`
after dispatch close. (Audit-target: the first production
caller of `cost.status` other than the CLI exists; the
awareness-block contributor that *uses* `cost.status` is a
downstream amendment per §9.)

### AC.A8.12 — ODD §2.5 reverse direction

Every code path, branch, dependency, and test in the amendment
diff traces back to AC.A8.1 – AC.A8.11. The builder audits both
directions before seal. (Halt-and-signal if any code path lacks
backing.)

### AC.A8.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows only paths
under: `primary-persona/src/`, `primary-persona/tests/`,
`primary-persona/pyproject.toml`,
`orchestrator/src/`, `orchestrator/tests/`,
`orchestrator/pyproject.toml`, and the universal-paths
admissions
(`docs/rebuild/plans/`, `CLAUDE.md`, `docs/odd-in-pos.md`,
`docs/odd-methodology.md`, `docs/rebuild/FUTURE_IDEAS.md`).
Anything outside this set is a halt condition.

Both per-component seal-diff tests
(`primary-persona/tests/test_no_sealed_amendments.py` and
`orchestrator/tests/test_no_sealed_amendments.py`) require
mutual cross-admission of the partner component's prefix in
their `allowed_prefixes` tuple — `pos-amend apply` performs
this widening from the manifest's component list, mirroring
amendment #48's pattern across primary-persona +
hands-off-lifecycle.

### 5.x — Behaviour-count check (forward)

| # | Declared behaviour | AC |
|---|--------------------|-----|
| 1 | Wrapper constructs valid `ScopeSpec` from dispatch shape | AC.A8.1 |
| 2 | Budget inferred from duration-estimation rubric | AC.A8.2 |
| 3 | Wrapper calls `activate_scope_with_spec`; respects gate verdict | AC.A8.3 |
| 4 | `BudgetDebited` / `BudgetRefunded` emission | AC.A8.4 |
| 5 | Scope reaches terminal state on dispatch close | AC.A8.5 |
| 6 | Orchestrator unreachable → documented fallback | AC.A8.6 |
| 7 | Refusal surfaced as structured value (not raised) | AC.A8.7 |
| 8 | Retry produces distinct scope; no double-charge | AC.A8.8 |
| 9 | Single persona-callable public surface | AC.A8.9 |
| 10 | Backwards-compat with sealed-component test suites | AC.A8.10 |
| 11 | `cost.status` returns non-empty surface after dispatch | AC.A8.11 |
| 12 | ODD §2.5 reverse direction | AC.A8.12 |
| 13 | Orchestrator exposes `activate_scope_with_spec` IPC | AC.A8.A1 |
| 14 | Existing `activate_scope` IPC stays registered, unchanged | AC.A8.A2 |
| 15 | Orchestrator exposes `record_dispatch_close` IPC | AC.A8.A3 |
| cross-cutting | Seal-diff window respected | AC.A8.S |

15 behaviours, 16 ACs (one cross-cutting). No method-in-AC.

---

## 6. Decisions for owner (read this first)

The owner directive locks the bulk of the design. The plan-author
surfaces only genuine uncertainty below. **All other decisions
default to the audit's locked recommendation** and are listed in
§6.x as "method, builder's call to refine."

### D1 — Failure semantics when the orchestrator is unreachable

- **Recommendation:** **fallback through; emit diagnostic.** When
  the orchestrator IPC is unreachable, the wrapper logs an NDJSON
  diagnostic to `<workspace>/.pos/dispatch-wrapper.log` and
  invokes the underlying Agent tool unwrapped. The dispatch
  proceeds; the cost / safety / reversibility chain does not
  fire; the operator sees a log entry per orphaned dispatch.
- **Why:** the harness is not a hard-runtime dependency of the
  persona's main session (the persona has work to do even if
  `pos bootstrap` hasn't started or has crashed). Hard-blocking
  on harness reachability would regress the persona's
  general-purpose interactivity.
- **Alternative (a):** **fail-closed.** Refuse the dispatch when
  the harness is unreachable. Cleaner cost-discipline story, but
  introduces a hard runtime dependency that breaks the
  general-purpose-Claude-Code use case (workspaces that haven't
  installed pos-v2 fully).
- **Alternative (b):** **fail-closed in DEV MODE only.** Hybrid.
  Adds CLAUDE.dev.md-vs-CLAUDE.md branching to the wrapper, which
  is method-leakage at the wrapper level.
- **Caveat:** if the owner picks fail-closed, AC.A8.6 changes
  shape (refusal instead of fallback); the rest of the AC set
  is unchanged. The fallback log is preserved either way.

### D2 — Reversibility-class default for dispatches that don't declare one

- **Recommendation:** **`compensatable`**. A dispatch the persona
  issues without an explicit class declaration is treated as
  compensatable by default; the persona may upgrade to
  `irreversible` (which routes through the safety layer's
  approval gate per Phase 3 wiring) or downgrade to
  `fully_reversible` for read-only dispatches.
- **Why:** matches `self-correction/spec_builder.py`'s
  precedent (correction scopes are forced compensatable).
  Conservative on safety, consistent across persona-issued and
  self-correction-issued scopes.
- **Alternative:** `fully_reversible`. Lower friction (no
  compensation registration overhead per dispatch); but a
  dispatch that mutates state without a registered
  compensation later defeats the reversibility primitive's
  point.
- **Caveat:** the wrapper does NOT register a compensation by
  default — the dispatch itself is responsible for declaring
  what compensation looks like. AC.A8.3's `compensatable`
  refusal path catches the "compensatable without binding"
  case structurally (this is an existing reversibility-primitive
  contract per amendment #14's gate).

### D3 — Module placement inside `primary-persona/src/`

- **Recommendation:** new module
  `primary-persona/src/dispatch_wrapper.py` exposing
  `dispatch_with_scope(...)` and helper builders
  (`_build_scope_spec`, `_infer_budget_from_duration`).
- **Why:** mirrors amendment #48's separation
  (`mcp_memory_client.py`, `stop_emitter.py` — one file per
  responsibility surface). Keeps IPC-client concerns local;
  testable surface.
- **Alternative:** add to an existing module
  (`session_start_emitter.py` or a new `harness_client.py`
  catch-all). Rejected — each amendment-#48 file has a single
  responsibility; A8's wrapper is its own.

### D4 — Where the duration-rubric lookup table is encoded

- **Recommendation:** **inline constant** at the top of
  `dispatch_wrapper.py` (Python dataclass / dict literal),
  matching the six-row category table in the memory bullet
  verbatim. Updated when the bullet's calibration table tightens
  (low-overhead — one constant edit per refresh).
- **Why:** the rubric is calibration data, not configuration the
  user tunes. Keeping it inline keeps the wrapper
  self-contained; no YAML loader / no config schema; method is
  the dataclass shape.
- **Alternative (a):** YAML at `<workspace>/.pos/duration-rubric.yaml`.
  Rejected — the rubric is a project-wide calibration, not a
  per-workspace tunable.
- **Alternative (b):** read the markdown in the memory bullet
  at runtime. Rejected — fragile (memory file lives outside the
  repo; not version-pinned).

### D5 — Objective-id resolution for the `bind_scope` step inside `activate_scope`

- **Recommendation:** the wrapper accepts an
  `objective_id: str` parameter on its public surface; the
  persona supplies it. **Default value when the persona omits:**
  the workspace's "ambient" objective id (a tracker entry seeded
  by workspace-bootstrap per amendment #39). The wrapper does
  NOT auto-create objectives.
- **Why:** ODD §1: every scope must bind to an objective. The
  ambient-objective fallback keeps the wrapper usable when the
  persona has not yet authored a specific objective; auto-create
  would silently grow the tracker without persona intent.
- **Alternative:** require `objective_id` always; refuse the
  dispatch otherwise. Cleaner, but high friction — most
  persona dispatches don't have a named objective today; A8
  shouldn't be the moment that retroactively requires one.
- **Caveat:** the ambient-objective seed is amendment #39's
  surface; a workspace that hasn't run amendment #39 yet won't
  have one. AC.A8.6's fallback covers that case (no ambient
  objective → log and pass through unwrapped).

### D6 — Money-axis budget: omit by default or compute from tokens?

- **Recommendation:** **omit by default**. The wrapper declares
  `time_seconds` + `tokens`; `money_cents` stays None unless the
  caller supplies it.
- **Why:** money-from-tokens conversion requires a per-model
  rate table that is not yet a sealed surface of pos-v2.
  Cost-governance accepts a None money axis (per `Budget.cap_for`
  semantics — None means "no cap on this axis"). Money-axis
  inference is a future amendment.
- **Alternative:** ship a default rate table inline. Rejected —
  same fragility argument as D4 alt(a); rates change.

### D7 — Test scope for the build-dispatch CDC speedup

- **Recommendation:** narrow pre-amendment test scope to
  `primary-persona/tests/`, `cost-governance/tests/`,
  `scope-of-work/tests/`, and `orchestrator/tests/` (the four
  components the wrapper directly composes against per §1's
  "composes on" list). Skip pre-seal full-suite rerun
  (sidecar-only edits between amendment and seal). Inline
  odd-methodology snippets into the dispatch brief. (Per
  `feedback_amendment_dispatch_speedups`.)
- **Why:** the wrapper is in-component to primary-persona and
  exercises four sealed components' public surfaces. Other
  components' tests are not at risk; widening the rerun is
  unnecessary cost.

### D8 — Single amendment vs split into wrapper + persona-prompt-edit

- **Recommendation:** **single amendment**, scoped to
  `primary-persona/` only. The persona-prompt amendment
  ("§Harness surfaces I draw from" block) is a *separate*
  follow-up — content authoring for a persona's prompt is
  **out of scope** per amendment #48's umbrella plan §4c
  (deferred Q1) AND per the audit's framing of A8 as the
  "structural" amendment vs the "awareness" amendment.
- **Why:** A8 is the structural primitive; the prompt edit that
  *uses* the primitive is content authoring (Lens 2 toolkit
  vs persona-content). Bundling them risks a
  build-then-refactor loop if the prompt-edit shape changes
  during initial use.

### D10 — Fence widening to orchestrator/ (R1 ruling, locked 2026-04-26)

- **Locked:** R1 from the halt-surface report
  (`.scratch/claude-output/A8-halt-surface-2026-04-26.md`).
  Owner ruled at 2026-04-26 — same pattern as the X D5
  ruling (carried from confidence-delegation 2026-04-26).
- **Why R1 over R2/R3:** R1 is the single change that makes
  A8's structural promise true. R2 (workspace-bootstrap
  spec_resolver channel) introduces cross-process spec
  serialisation + race-condition surface + still requires
  `poll_external_events` wiring (third change). R3 (defer
  the cost ACs) ships the wrapper without delivering the
  value-prop move it exists to deliver — `BudgetDebited` event
  emission with no consumer is itself a §2.5 violation.
- **What R1 mandates:** new IPC method
  `activate_scope_with_spec(scope_id, objective_id,
  spec_payload)` that decodes the spec, calls
  `scope_runtime.create(spec, scope_id=...)` in-process, then
  invokes the existing `wrapped_activate_scope` chain. Existing
  `activate_scope` IPC stays for backwards-compat (see AC.A8.A2).
- **§4 re-extension shape:** the original plan was authored
  with a §3 fence pinned to `primary-persona/` only. The R1
  ruling re-extends scope to `orchestrator/` per the audit's
  empirical findings. This re-extension is recorded in §14's
  method-decision register at seal time.

### D9 — `IPCClient` lifecycle inside the wrapper

- **Recommendation:** **per-dispatch open-and-close**. Each
  wrapper call opens a fresh `IPCClient`, calls
  `activate_scope_with_spec`, awaits the verdict, closes. No
  connection pooling.
- **Why:** Unix-socket connect is microseconds-scale on
  loopback; pooling adds complexity (connection-reuse races,
  reconnection-on-detach, lifetime management) that isn't worth
  it for the dispatch frequency (single-digit per minute on
  active turns). Mirror amendment #48's per-hook MCP client
  shape (out of scope §9 — D-build.equivalent there).
- **Alternative:** module-level singleton client. Adds
  complexity; pos-amend dependency-injection story for tests
  becomes harder.

### 6.x — Method, builder's call to refine (not surfaced for owner ruling)

These are flagged inferences per ODD §7.4 — the builder may
challenge any of them at build time and halt-and-signal back to
the dispatcher; the owner does not need to rule on them upfront.

- Diagnostic-log format: NDJSON (mirrors amendment #48 D8).
- Test fixtures' orchestrator stub: monkeypatch the `IPCClient`
  call site (mirrors amendment #48 D3 test approach).
- Error-code ranges for refusal handling: read from the sealed
  components' public error-code tables; do not fork the
  numbering.
- Wrapper's input schema validation: Pydantic (mirrors every
  other public surface in pos-v2).

---

## 7. Hard constraints

1. **No `--amend`.** Corrective commits only.
2. **Scope fence (R1-revised).** In-scope source:
   `primary-persona/src/`, `primary-persona/tests/`,
   `primary-persona/pyproject.toml`,
   `orchestrator/src/`, `orchestrator/tests/`,
   `orchestrator/pyproject.toml`.
   Any edit elsewhere (other than the universal-paths
   admissions in §10) is a halt trigger (§8).
3. **Reversibility.** Fully reversible. The wrapper is additive
   (existing dispatch paths are unaffected; only persona
   callers that opt-in to the wrapper exercise it). The
   fallback path (D1) preserves dispatch-without-harness
   behaviour for callers that don't go through the wrapper.
4. **No edits to sealed components outside primary-persona +
   orchestrator (R1-revised).** The cost-governance wrap, the
   safety-layer wrap, the reversibility-primitive wrap, the
   workspace-bootstrap cost_governance adapter, scope-of-work,
   and objective-tracker are **untouched**. The orchestrator's
   existing `activate_scope` IPC is preserved unchanged
   (AC.A8.A2); the new `activate_scope_with_spec` IPC is the
   sole orchestrator-side surface added. If the builder
   discovers any other missing IPC or inadequate signature on
   any other sealed component, halt per §8.3.
5. **No new top-level objective.** The wrapper composes on
   already-named v1.0 / v1.1 objectives (R12, scope-of-work,
   cost governance). If during build a new top-level objective
   surfaces, halt per §8.4.
6. **No Agent-tool re-implementation.** The wrapper invokes
   Claude Code's existing `Agent` tool; it does not re-implement
   dispatch.
7. **Dependency fence.** No new runtime dep needed (the
   wrapper imports `scope_of_work`, `pos_orchestrator.ipc`,
   already in the persona venv). Test-only deps per STATE.md
   rule #8.
8. **Fail-soft on harness unreachability.** Per D1; AC.A8.6
   measures observable behaviour. Do not introduce a
   hard-block path.
9. **Refusal as value, not exception.** Per AC.A8.7. The
   persona caller receives a structured refusal object; the
   wrapper does NOT raise on gate-chain refusal. Internal
   exceptions inside the wrapper still raise (e.g. invalid
   `ScopeSpec` construction is a programmer error and surfaces
   as `ValidationError`); gate-chain refusals are domain
   outcomes and surface as values.
10. **CDC adherence.** Plan-before-code (this plan), background-
    agent default for the build, scope-only dispatch, research-
    before-plan (audit doc landed at `de5fe11`'s parent).
11. **`pos-amend apply --dry-run` green is a hard prereq** per
    amendment #22.
12. **Sealed-component preservation.** AC.A8.10 is the
    structural assertion: every prior amendment's seal-diff
    invariant stays green.
13. **No edits to `personas/`.** Persona content authoring
    (the §"Harness surfaces I draw from" prompt block) is
    out of scope per D8 / §9.
14. **No edits to `cost-governance/` IPCs.** The
    `cost.status` / `cost.scope` / `cost.adjust_ceiling`
    surfaces are sealed. The wrapper consumes them; it does
    not extend them. The new orchestrator IPC method
    (`activate_scope_with_spec` per AC.A8.A1) invokes the
    existing `wrapped_activate_scope` chain via the standard
    handler-lookup pattern — it does not bypass or modify any
    cost-governance surface.
15. **No connection pooling.** Per D9; one `IPCClient` per
    dispatch.
16. **Composes with V/Y context.** A future Y-amendment will
    consume the `ScopeSpec` context A8 produces (path-choice
    ranking via reversibility's `rank_alternatives`). A8 must
    not preempt Y's design; the `ScopeSpec` shape A8
    produces is the existing seven-field primitive — Y
    composes on top.

---

## 8. Halt triggers (R1-revised)

Any of the following → halt and signal back to the dispatcher;
do NOT silently work around:

1. **Cross-component scope expansion beyond R1 fence.** Any
   required source edit to a sealed component **outside**
   `primary-persona/` + `orchestrator/` — halt. Specifically:
   1. **Cost-governance / safety-layer / reversibility-primitive
      edit.** If any sealed wrap requires a signature change
      to support the wrapper's call shape — halt. (R1 design
      explicitly avoids these by registering the new IPC method
      such that the existing wrap chain composes onto it
      identically. If the wrap chain does NOT compose, the
      design assumption is wrong and the builder halts.)
   2. **Workspace-bootstrap edit.** The cost-governance adapter
      that registers `wrapped_activate_scope` needs no change —
      the new `activate_scope_with_spec` IPC self-installs the
      same wrap composition by calling
      `server._handlers.get("activate_scope")` after the
      bootstrap chain has run. If the builder finds the bootstrap
      adapter must be touched, halt.
   3. **Scope-of-work or objective-tracker edit.** Both surfaces
      are public-API stable; the new IPC method consumes
      `scope_runtime.create(spec, scope_id=...)` and
      `objective_tracker.bind_scope(...)` exactly as the existing
      `activate_scope` does. If either requires a signature
      change, halt.
2. **AC cannot be expressed outcome-shaped.** If during build
   an AC requires method to express, halt; the AC needs
   re-authoring at the dispatcher's level.
3. **`pos-amend apply --dry-run` red** at any point — halt.
4. **A required new top-level objective surfaces.** Per Luke's
   hard requirement (memory bullet
   `feedback_subagent_odd_violation_halt`). If the builder
   discovers the wrapper requires a v1.0 / v1.1 / v1.2 spec
   surface that isn't yet declared — halt.
5. **§2.5 violation in surrounding code.** If during build
   the builder discovers any branch in `primary-persona/src/`
   or `orchestrator/src/` modules touched by the amendment
   that has no backing AC — halt. Do NOT extend a violating
   surface.
6. **`activate_scope_with_spec` shape is incompatible with
   existing scope-runtime semantics.** If empirical
   verification reveals `scope_runtime.create(spec,
   scope_id=...)` cannot accept a caller-supplied `scope_id`
   (or that doing so introduces a duplicate-event hazard the
   existing tests would catch) — halt. (The R1 design depends
   on the `create(scope_id=...)` parameter being supported per
   `scope-of-work/src/runtime.py:152` — verified in the
   research read; halt-trigger fires only if a build-time
   regression is found.)
7. **Backwards-compat with existing `activate_scope` callers
   can't be preserved.** Per AC.A8.A2. If the new IPC method's
   registration order or wrap-composition path forces a change
   to the existing `activate_scope` IPC handler's behaviour,
   halt.
8. **Budget inference is too lossy.** If the duration-rubric
   table cannot produce defensible token estimates for the
   six categories without a per-category overhaul, halt;
   D4's "encode the rubric inline" assumption is wrong.
9. **A test for any AC.A8.x or AC.A8.Ax cannot be written
   deterministically.** Halt.
10. **Composition test reveals wrap-order regression.** If
    adding the new IPC method changes the observed wrap-call
    order (`safety → reversibility → cost → orig_activate`) on
    the composition test — halt. (The new method is registered
    BEFORE the workspace-bootstrap wrap chain installs at
    startup; `wrapped_activate_scope` does NOT wrap
    `activate_scope_with_spec` directly. Instead, the new IPC
    method invokes `wrapped_activate_scope` internally — see
    AC.A8.A1 step 3.)
11. **§4 re-extension surfaces a new fence-widening request.**
    If the build discovers a third sealed component must be
    touched (beyond primary-persona + orchestrator), halt.
    The R1 ruling is locked at exactly two components.

---

## 9. Out of scope (named explicitly per ODD §2.5)

- **Persona-prompt content authoring.** The §"Harness surfaces I
  draw from" block in `personas/primary/prompt.md` (audit's "fix
  in 60 lines") is a follow-up amendment, not A8.
- **Money-axis budget inference.** D6 — money axis is None by
  default; per-model rate-table is a future amendment.
- **Awareness-block contributor for `cost.status`.** Surfacing
  cost into the persona's session-start payload (AC.A8.11
  reachable; consumer is downstream) — future amendment.
- **Self-correction wiring of dispatch failures.** A9 from the
  audit; A8 makes scope failures *visible* to self-correction's
  trigger queue (existing wiring), but the persona-side
  invocation of `correction.user_reported` is a separate
  amendment.
- **Path-choice ranking** (`reversibility-primitive`'s
  `rank_alternatives` consumer). Audit A7; future amendment;
  composes on top of A8's `ScopeSpec` output.
- **`ClaudeClient` adapter routing for graceful degradation.**
  Audit A4; A8 produces the `ScopeSpec`; routing the inferred
  LLM call shape through `ClaudeClient` for 429/529 observation
  is downstream.
- **Memory-system / MCP triage.** Audit A1; orthogonal to A8.
- **Creation-trigger live-detection adapter.** Audit A3; orthogonal.
- **Persona "why did I" surface.** Audit A5; orthogonal.
- **Persona-owned safety surface (kill phrases + ask-list
  awareness).** Audit A6; orthogonal.
- **Self-upgrade availability surface.** Audit §8 sequence;
  orthogonal.
- **Background-task / scheduled-routine wrapping.** A8 wraps the
  Agent tool dispatch surface only. Scheduled routines are a
  future amendment that composes the wrapper into a
  cron-equivalent harness primitive.
- **Multi-orchestrator / multi-socket support.** One
  orchestrator IPC socket per workspace; pos-amend's existing
  socket-discovery surface is sufficient.
- **Cost-status awareness narration in the persona prompt.**
  Future amendment; A8 makes the surface reachable.

If any of these surface as hard prerequisites during the build,
halt-and-signal; do not silently expand scope.

---

## 10. Bookkeeping surface (`pos-amend` manifest sketch)

Per amendment #22's `pos-amend` convention. Manifest YAML at
build-dispatch, schema:

```yaml
schema_version: 1
amendment:
  number: 52   # assigned post-amendment-#51 HALT-prefix commit (5ad5f68)
  slug: agent-dispatch-as-scope-wrapper
  title: "primary-persona Agent-dispatch-as-scope wrapper (A8) + orchestrator activate_scope_with_spec IPC"

baseline: <pre-amendment-tip-sha>   # HEAD~1 of amendment commit

plan: docs/rebuild/plans/agent-dispatch-as-scope-wrapper.md

seal_description: "primary-persona dispatch wrapper + orchestrator activate_scope_with_spec IPC (A8 R1-revised)"

# Two sealed components touched per R1-revised plan §3 fence:
#   - primary-persona: new dispatch_wrapper.py + persona-callable
#     surface + tests.
#   - orchestrator: new activate_scope_with_spec Python surface +
#     IPC handler registration + tests. Existing activate_scope
#     IPC stays registered + unchanged (AC.A8.A2).
components:
  - name: primary-persona
    seal_test: primary-persona/tests/test_no_sealed_amendments.py
    sidecar: primary-persona/tests/SEAL_COMMIT
    frozen_baseline: false
  - name: orchestrator
    seal_test: orchestrator/tests/test_no_sealed_amendments.py
    sidecar: orchestrator/tests/SEAL_COMMIT
    frozen_baseline: false

universal_paths:
  prefixes:
    - docs/rebuild/plans/
  files:
    - CLAUDE.md
    - docs/odd-in-pos.md
    - docs/odd-methodology.md
    - docs/rebuild/FUTURE_IDEAS.md

narrative:
  target: hands-off-lifecycle/seals/SEAL_COMMIT.agent-dispatch-as-scope-wrapper
  body: |
    # Amendment #52 — primary-persona Agent-dispatch-as-scope
    #                  wrapper (A8) + orchestrator
    #                  activate_scope_with_spec IPC
    (body authored by builder at seal time; references
     AC.A8.1 – AC.A8.S + AC.A8.A1 / AC.A8.A2, the audit doc, the
     halt-surface report, and the R1 ruling.)
```

**Universal admissions** per amendment #22 ruling #3 cover
`docs/rebuild/plans/`, `CLAUDE.md`, `docs/odd-*.md`, and
`docs/rebuild/FUTURE_IDEAS.md`. No other paths admitted.

**Test scope per amendment-dispatch CDC speedups (Luke
2026-04-23) + D7 lock (R1-confirmed):** narrow pre-amendment test
scope to `primary-persona/tests/` + `orchestrator/tests/` +
`cost-governance/tests/` + `scope-of-work/tests/` (the four
components in the wrap chain). Skip pre-seal full-suite rerun
(sidecar-only edits between amendment and seal). Inline
odd-methodology snippets into the dispatch brief.

**Commits:**
- Amendment commit: `feat(primary-persona, orchestrator): wire
  Agent-dispatch-as-scope wrapper + activate_scope_with_spec IPC
  (amendment #52, AC.A8.1–AC.A8.S + AC.A8.A1–AC.A8.A2)`.
- Seal commit: `chore(seals): A8 dispatch wrapper +
  activate_scope_with_spec IPC — primary-persona+orchestrator at
  <amendment-sha>`.

No `--amend`. `pos-amend apply --dry-run` green is the prereq
to amendment commit; `pos-amend seal --plan-doc <abs-path>`
finalises.

---

## 11. Risks + mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Orchestrator IPC `activate_scope` signature insufficient | low-medium | scope expansion to orchestrator/ | empirical verification of the IPC's accepted shape during plan-author + halt-trigger #6 |
| Duration rubric produces unrealistic token estimates per category | medium | wrapper over/under-reserves; cost-governance refuses dispatches that should pass | start with rubric's documented bounds; halt-trigger #7 if bounds are too lossy; tighten via the rubric's calibration loop |
| Wrapper adds dispatch latency the user notices | low | persona perception degraded | per-dispatch IPC handshake is microseconds on loopback; AC.A8.5 is observable, not latency-budgeted, but plan-author target is <50ms wrapper overhead per dispatch |
| Persona retries flood the cost ledger | low | rollups inflated by retry attempts | AC.A8.8 measures distinct scopes per retry — not double-counting; the *count* of retries is data the persona uses, not a bug |
| Sealed wrap-order regresses | very low | safety-before-cost-before-orig violated | the wrapper is a *client* of `activate_scope`, not a wrap; halt-trigger #9 catches if the composition test changes |
| Fallback path (D1) becomes the dominant path in practice | low-medium | A8 lands but produces no cost data because the harness isn't running | operational concern, not a build risk; the diagnostic log surfaces it; downstream awareness-block contributor (out of scope) flags chronic fallbacks |
| Money axis missing causes cost-governance to treat dispatches as money-uncapped | low | session money ceiling cannot enforce on persona dispatches | D6 documents the trade-off; future amendment closes; AC.A8.4 measures the time/tokens axes only |
| `BudgetDebited` event volume saturates pyee emitter | very low | emitter back-pressure on rapid dispatches | persona dispatch rate is single-digit per minute; emitter is sized for hundreds of events per minute on Phase 1 design |
| Wrapper's structured refusal not caught by persona | low | refusal silently dropped | persona-side handling of the refusal is downstream; A8 ships the structured surface; AC.A8.7 measures the surface's existence + shape, not the persona's response |

---

## 12. Three-lens AC trace

| AC | Lens 1 (Claude) | Lens 2 (Translation / Toolkit) | Lens 3 (ODD) |
|----|------------------|---------------------------------|--------------|
| AC.A8.1 | composes on existing `ScopeSpec` Pydantic surface | toolkit primitive — every future dispatch contributor builds against same shape | outcome-shaped |
| AC.A8.2 | leverages duration-estimation calibration data | translation: persona declares budget without user math | outcome-shaped |
| AC.A8.3 | composes on `IPCClient` (Phase 2) + activate_scope (Phase 2) + wrap chain (Phase 3) | translation: gate verdict absorbed at framework | outcome-shaped |
| AC.A8.4 | composes on scope-of-work emitter (Phase 1) | translation: cost ledger fills without persona accounting | outcome-shaped, count-bound |
| AC.A8.5 | composes on scope-of-work state machine | toolkit: closes the audit-trail loop per dispatch | outcome-shaped |
| AC.A8.6 | composes on Unix-socket connection-error semantics | translation: harness absence absorbed at boundary | outcome-shaped |
| AC.A8.7 | n/a | translation: refusal narration is downstream of the structured surface | outcome-shaped |
| AC.A8.8 | composes on scope-id generation in scope-of-work | toolkit: retries audit cleanly | outcome-shaped, count-bound |
| AC.A8.9 | composes on Claude Code's `Agent` tool | toolkit primitive — single entry point | outcome-shaped |
| AC.A8.10 | preserves all earlier sealed surfaces | toolkit backwards-compat | structural |
| AC.A8.11 | composes on `cost.status` IPC | translation: cost surface reachable for awareness | outcome-shaped |
| AC.A8.12 | n/a | n/a | review-time audit |
| AC.A8.A1 | extends orchestrator IPC by one method (composes the existing wrap chain) | toolkit primitive — every harness producer of `ScopeSpec` over IPC composes against | outcome-shaped |
| AC.A8.A2 | preserves existing `activate_scope` IPC | toolkit backwards-compat | structural |
| AC.A8.A3 | extends orchestrator IPC for close-emission lifecycle | toolkit primitive — every harness emitter of dispatch-close over IPC composes against | outcome-shaped |
| AC.A8.S | n/a | n/a | structural |

---

## 13. Ladder to AC.PO.1 / AC.PO.2 (VALUE_PROPOSITION as prime objective)

- **AC.A8.1, AC.A8.2, AC.A8.4, AC.A8.11 → AC.PO.1.** Persona
  declares a budget per dispatch; cost ledger fills; persona
  answers from structured cost state. Translation burden
  absorbed (token discipline lives in the harness, not the
  user's mental load). VALUE_PROPOSITION §"the primary persona
  is a translation layer" paragraph 4 is the explicit anchor.
- **AC.A8.3, AC.A8.5, AC.A8.7 → AC.PO.1.** Gate-chain verdict
  surfaces as structured value the persona can route; user
  doesn't see exception traces or low-level IPC errors;
  translation absorbed at the framework boundary.
- **AC.A8.6 → AC.PO.1.** Harness absence absorbed; user's
  general-purpose Claude Code experience preserved when pos-v2
  isn't fully bootstrapped.
- **AC.A8.1, AC.A8.9 → AC.PO.2.** New toolkit primitive: a
  single persona-callable surface that turns any Agent
  dispatch into a four-gate-governed scope. Future
  contributors (scheduled routines, background monitors,
  retry loops) compose against this surface.
- **AC.A8.4 → AC.PO.2.** Cost ledger is now a productive
  surface; future toolkit features (awareness-block cost
  contributor, throttle-based dispatch back-off, per-prompt
  attribution) compose against an alive cost surface, not an
  empty one.
- **AC.A8.10 → AC.PO.2.** Backwards-compat preserves every
  prior sealed surface as a productive part of the toolkit.

---

## 14. Execution sequencing (suggested; builder's call to refine) — R1-revised

**§4 re-extension register (recorded 2026-04-26):** the original
plan was authored with the §3 fence pinned to `primary-persona/`
only, on the audit's "wrapper alone closes the cost gap" model.
Empirical verification by the prior V-build agent showed that
model was structurally incomplete (see
`.scratch/claude-output/A8-halt-surface-2026-04-26.md`):
`activate_scope`'s IPC takes only ids, the production
`spec_resolver` defaults to None for any scope not constructed
in-process by the orchestrator runtime, and `CostLedger` is
in-process so cross-process events do not reach the ledger
without `poll_external_events` wiring (zero production callers).
The R1 ruling (locked by Luke 2026-04-26 — same pattern as the X
D5 ruling) re-extends scope to add `orchestrator/` to the fence,
adding a new IPC method `activate_scope_with_spec` that decodes
the spec, calls `scope_runtime.create(spec, scope_id=...)` in-
process, then invokes the existing `wrapped_activate_scope` chain.
The §4 entry per ODD §4 protocol: original-plan-fence → empirical
discovery → owner ruling → re-extension → builder-plan + manifest
update → continued build cycle.

1. **Now — Luke rules on §6 D1, D2, D5, D7 (genuine
   uncertainty).** D3, D4, D6, D8, D9 are method-level and
   default to the recommendation unless Luke flags otherwise.
   D10 (R1 fence-widening) is locked.
2. **Empirical verification (during plan-author or
   build-dispatch prep).** Confirm `activate_scope` IPC's
   accepted payload shape (read the orchestrator's IPC handler
   end-to-end); confirm scope registration sequencing
   (register-then-activate vs activate-with-spec) — the audit
   assumes register-then-activate; halt-trigger #6 covers the
   alternative. Confirm `cost.status`, `cost.scope`,
   `cost.session` return the documented shapes against a live
   bootstrapped harness in pos3.
3. **Build dispatch** (background agent, working dir
   `/Users/lukeivers/ivers-corp-pos-v2/`, brief carries scope
   only — AC.A8.1–AC.A8.S + halt triggers + ODD-check + the
   `pos-amend apply --dry-run` then commit then `pos-amend
   seal --plan-doc <abs-path>` flow).
4. **Verify in pos3:** restart Claude Code; persona issues an
   Agent dispatch through the wrapper; confirm `cost.status`
   returns a non-empty active reservation during the
   dispatch's lifetime; confirm the reservation reconciles
   after the dispatch returns; confirm a `BudgetDebited`
   event lands on the scope-of-work emitter; confirm the
   refusal path produces a structured value (not a raise) by
   crafting a dispatch that exceeds the session ceiling.
5. **Append findings** to `FUTURE_IDEAS_DRAFT.md` per the
   no-overhead capture pattern. Specifically: any
   wrapper-overhead-latency observations (target <50ms), any
   rubric-bound corrections, any fallback-path firings (the
   harness was unreachable in pos3 at sample time? — that's
   data).
6. **Update `STATE.md`** if this lands during a Phase
   milestone (likely not — A8 is a Phase 4+ amendment, no
   Phase boundary).

Per `feedback_amendment_dispatch_speedups`: the dispatch scopes
test rerun to `primary-persona/tests/` + `orchestrator/tests/` +
`cost-governance/tests/` + `scope-of-work/tests/` only.
Per `feedback_subagent_odd_violation_halt`: the dispatch carries
the explicit halt-and-surface-ODD-violations-in-surrounding-code
clause.
Per `feedback_dispatch_explicit_pos_amend_apply`: the dispatch
names `pos-amend apply --dry-run` + `pos-amend apply` +
`pos-amend seal --plan-doc <abs-path>` explicitly as the
bookkeeping mechanism.
Per `feedback_no_amend_in_agent_dispatches`: corrective commits
only; no `git commit --amend`.
Per `feedback_always_specify_wd_in_dispatches`: the dispatch
specifies WD `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## 15. References

- Locked research (governs):
  `docs/rebuild/plans/research/harness-usage-audit-2026-04-26.md`
  (A8 named at lines 207–216; cost-governance §11 acute gap at
  lines 181–216; one-page summary at lines 19–37; D1 ruling
  surface at line 51).
- Sealed-component proposals A8 composes on:
  - `docs/rebuild/components/scope-of-work/proposal.md`
  - `docs/rebuild/components/orchestrator/proposal.md`
  - `docs/rebuild/components/cost-governance/proposal.md`
  - `docs/rebuild/components/safety-layer/proposal.md`
  - `docs/rebuild/components/reversibility-primitive/proposal.md`
- Sibling plan-docs for shape:
  - `docs/rebuild/plans/memory-system-live-client-and-stop-hook-write.md`
    (amendment #48 — adjacent persona-side wiring amendment).
  - `docs/rebuild/plans/amendment-46-persona-session-start-turn-start-emitters.builder-plan.md`
    (sibling pattern for hook-CLI authoring inside
    primary-persona).
  - `docs/rebuild/plans/amendment-33-memory-consumer-wiring-primary-persona.md`
    (sibling pattern for persona-as-consumer wiring).
- Where the wrapper lives:
  `primary-persona/src/dispatch_wrapper.py` (new — D3).
- Existing surfaces the wrapper composes on:
  - `scope-of-work/src/spec.py` — `ScopeSpec`, `Budget`,
    `ReversibilityClass`, `SuccessCriterion`.
  - `orchestrator/src/orchestrator.py:366` — `activate_scope`
    Python surface.
  - `orchestrator/src/orchestrator.py:658` — `activate_scope`
    IPC handler.
  - `orchestrator/src/ipc.py:240` — `IPCClient` async client.
  - `cost-governance/src/ipc_wiring.py:141` — innermost
    `wrapped_activate_scope`.
  - `self-correction/src/spec_builder.py` — the only existing
    production `ScopeSpec` constructor (precedent shape).
- Duration-estimation rubric (encoded inline per D4):
  memory bullet `feedback_duration_estimation_rubric` (six-row
  table at §"Step 1 — Categorize by task shape").
- ODD methodology + ODD-in-pos:
  `docs/odd-methodology.md`, `docs/odd-in-pos.md`.
- VALUE_PROPOSITION:
  `docs/rebuild/VALUE_PROPOSITION.md` (translation-layer §;
  paragraph 4 is the token-discipline anchor for AC.PO.1).
- STATE / FUTURE_IDEAS:
  `docs/rebuild/STATE.md`, `docs/rebuild/FUTURE_IDEAS.md`.
- v1.1 R12 spec text:
  `docs/rebuild/spec/pos-v2-objectives-spec.md` line 300–306.
- Amendment-dispatch bookkeeping:
  `tools/pos-amend/`.
