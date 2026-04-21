# Handoff Brief — Objective Tracker

**Component:** Objective Tracker (third and final Phase 1 primitive)
**For:** general-purpose Agent (builder)
**Authored by:** the primary persona
**Status:** DRAFT — awaiting owner's review before dispatch
**Against:** `proposal.md` (approved 2026-04-18 19:28 CDT, all three open questions resolved per the primary persona's leans)
**Spec:** objectives spec v1.0 + v1.1 + v1.2 addenda

---

## Objective

Deliver a production-ready objective-tracker primitive for the new pOS. Build deliverables D1–D9 from the proposal. The tracker ships standalone on the `pos-v2` branch. Every v1.0 Objective acceptance criterion, the ODD methodology's runtime needs, and the relevant v1.1/v1.2 revisions must pass. On landing, scope-of-work's parent-objective traceability becomes enforceable via the sidecar binding table, without any amendment to the sealed scope-of-work component.

---

## Hard constraints

1. **Implementation language:** Python.
2. **Branch discipline:** `pos-v2` on the existing the existing workspace repo repo. Work lives under `pos-v2/objective-tracker/` (mirror the pattern `scope-of-work/`, `memory-system/`, `primary-persona/` use). No modifications to `main`.
3. **No amendments to sealed components.** Scope-of-work, memory-system, and primary-persona-layer all stay as they are. If the build reveals an amendment is genuinely required, halt and signal; do not modify sealed components unilaterally. The sidecar enforcement design exists precisely to avoid this.
4. **Zero carryover from current pOS / the existing workspace.** No reading of the current `GOALS.md` convention, `intake`/`workflow`/`task` hierarchy, or SDLC stage definitions for design inspiration. Clean-slate design.
5. **Permitted runtime dependencies:** Python stdlib (`sqlite3`, `asyncio`, `uuid`, `dataclasses`), `pydantic`, `pyee`, `opentelemetry-api`, `opentelemetry-sdk`, `PyYAML` (carried forward from prior briefs). Any other runtime library requires halt-and-signal. Test-only deps (pytest, pytest-asyncio) permitted per STATE.md rule #8.
6. **Max-first.** LLM inference inside the tracker is unexpected. If a design scenario genuinely needs LLM inference (e.g. automated negative-case re-extension suggestions), that work uses Claude via Max.
7. **No personas shipped in pOS core.** The tracker is framework code.
8. **No assumed downstream consumer (A1 correction).** Tracker emits OTel; no consumer is assumed to exist.
9. **Halt-on-deviation.** Silent deviation is forbidden.
10. **Bundled documentation per v1.1 R4.** Ships at `objective-tracker/docs/`.

## rulings recorded baked into this brief

- **Sidecar `ScopeObjectiveBinding` table is the enforcement mechanism.** No amendment to scope-of-work. Enforcement is dispatch-layer — the workspace dispatch layer calls `tracker.bind_scope(scope_id, objective_id)` before activating any scope, and refuses activation when binding fails.
- **`authored_by` carries arbitrary provenance** — either the literal string `"user"` or a persona handle (e.g. `"mara"`). Not binary `user|system`. The enforcement check for "user-authored root" reads `authored_by == "user"` on the terminal root of a trace.
- **Default parent-close policy: `notify`.** Not TERMINATE. "Parent objective abandoned" is semantically distinct from "parent scope cancelled." Per-objective override to `terminate` or `abandon` available.
- **Default `time_bound`: mandatory at creation.** Omission rejects objective creation. The author must consciously choose a deadline or the `"evergreen"` mark.
- **`scope_success` criterion auto-evaluates** on scope-state-change events. Other criterion variants remain caller-dispatched via `evaluate_criterion()`.
- **`re_open` audit rationale: mandatory.** Non-empty string required. Empty or missing rationale rejects the re-open call.

---

## Deliverables

Nine deliverables D1–D9 as named in the proposal. Objective-level acceptance; no prescribed file layout, class names, or function signatures beyond the API surface sketched in the proposal.

### D1. Objective primitive — schema + persistence

**Objective:** `ObjectiveSpec` exists, Pydantic-validated at construction; event-sourced persistence in a separate SQLite WAL database; state projection rebuildable from events.
**Acceptance:**
- Creating with any missing mandatory field raises at construction.
- Valid objectives persist via event log.
- Replay of the event log reconstructs projection state identically.
- SQLite WAL mode enabled; semantic round-trip upgrade per v1.1 R1 passes (see D8).
- Mandatory fields present: `id`, `goal`, `parent_id`-or-root-marker, `acceptance_criteria`, `time_bound`, `authored_by`, `status`.

### D2. Hierarchy and traceability

**Objective:** forest-of-trees structure; `trace_to_root` returns ordered ancestor chain; orphan detection identifies chains whose terminal root is not `authored_by == "user"`.
**Acceptance:**
- A deliberately-orphaned chain (root `authored_by != "user"`) is detected as orphan by `trace_to_root` + ancestry check.
- A user-authored-root chain validates cleanly.
- DAG attempts (creating an objective with two parents) raise at construction — only one parent permitted.
- `trace_to_root(objective_id)` returns the ordered ancestor list, with the user-authored root last.

### D3. Criterion discriminated union

**Objective:** the four criterion variants (`prose`, `scope_success`, `child_closure`, `external_predicate`) all validate, persist, and support evaluation where applicable.
**Acceptance:**
- Each variant has its own Pydantic validation rules and round-trips through the event log.
- `evaluate_criterion(criterion_id, result, rationale)` stores an evaluation event; later retrievals return the latest result plus full history.
- `child_closure` is computed by querying the current state of referenced children (callers decide when to query).
- `scope_success` auto-evaluates on scope-state-change events (per decision recorded — the tracker subscribes to scope-of-work's pyee emitter for scopes referenced by `scope_success` criteria; on a terminal state event, writes an evaluation event automatically).

### D4. Scope-to-objective enforcement (sidecar)

**Objective:** `bind_scope(scope_id, objective_id)` deterministically resolves and validates; the workspace dispatch layer refuses to activate unbound scopes.
**Acceptance:**
- Successful binding: writes a `ScopeBound` event; subsequent queries return the binding.
- Unknown objective id → raises `UnresolvedObjectiveError` with the offending id in the message.
- Chain-not-terminating-at-user-authored-root → raises `OrphanRootError`.
- An integration test verifies: scope-of-work is **unchanged** (all 77 existing tests still pass — 63 original + 14 D0); an unbound scope cannot be activated; a bound scope activates cleanly. The integration point is the dispatch layer (or a minimal test dispatcher that mimics it) calling `bind_scope` before scope activation.

### D5. `authored_by` provenance

**Objective:** every objective carries `authored_by`; the field accepts either `"user"` or any persona-handle string; `list(authored_by=...)` queries return exactly the set of objectives matching.
**Acceptance:**
- The creation API distinguishes "user-authored" (literal `"user"`) from "persona-authored" (arbitrary string) — the distinction is made by the caller declaring which at creation; the tracker stores whatever is passed without validating handle strings against any registry.
- `list(authored_by="user")` returns only user-authored objectives across all trees.
- `list(authored_by="mara")` returns only objectives with that handle across all trees.
- The orphan-root check (D2) reads this field; a root with `authored_by != "user"` triggers `OrphanRootError` on bind.

### D6. ODD integration surface

**Objective:** the query + evaluation surface ODD harnesses need exists; re-open + re-extension flow is supported.
**Acceptance:**
- `list_by_root(root_id, states=?, with_unchecked_criteria=?)` returns the exact set of objectives matching.
- An external predicate registered by a harness can evaluate against an objective's criterion; the result stores as an event; subsequent queries return it.
- `re_open(objective_id, rationale)` transitions an `achieved` objective back to `active`, writes an audit event including the rationale, and requires a non-empty rationale (empty/missing rationale raises).
- A representative ODD cycle end-to-end in a test: register predicate → list objectives with unchecked criteria → evaluate → record → re-open parent on failure → re-extend with a new objective → verify the new objective is reachable in the tree.

### D7. OTel observability emission

**Objective:** every operation emits OTel spans/events per v1.1 R11.
**Acceptance:**
- `create`, `mark_achieved`, `mark_abandoned`, `re_open`, `bind_scope`, `evaluate_criterion` all produce spans with relevant attributes (objective_id, authored_by, status, outcome).
- State-change events emitted as span events on the parent span.
- Emission succeeds with no consumer present (A1 correction).

### D8. Upgrade-fidelity test harness

**Objective:** the tracker passes v1.1 R1 semantic round-trip test across an upgrade.
**Acceptance:**
- Probe set of objective creations, bindings, evaluations, and queries is captured pre-upgrade.
- Replayed post-upgrade; output-equivalence is asserted; drift above declared threshold fails the upgrade.
- SQLite database snapshot preserves physical reversibility.
- Harness mirrors the pattern scope-of-work's D7 already established (consistent style across components).

### D9. Bundled documentation

**Objective:** v1.1 R4 — human-readable documentation bundled with the component.
**Acceptance:**
- Prose explanation covering what the tracker does and why.
- Architecture diagram (objective event log + projection + sidecar binding table).
- Data-flow diagram (create → decompose into children → bind to scope → evaluate criteria → re-open on failure → re-extend).
- Relationship map (no hard dependencies; consumed by scope-of-work via binding, by future self-correction loop, by ODD harnesses, by primary-persona authoring pipeline's scoped authoring work).
- One-page API reference.
- Non-technical reader can answer "what does the tracker do and how does it fit" from docs alone.

---

## Dependencies

### Hard dependencies

- **None.** The tracker is foundational.

### Soft dependencies (consumers)

- Scope-of-work (via `bind_scope` at the dispatch-layer boundary — no scope-of-work change needed).
- Primary-persona layer (authoring pipeline creates objectives scoped to authoring work; persona handles flow into `authored_by`).
- Future self-correction loop; future observability aggregator; future ODD test-harnesses.

### Permitted runtime dependencies

As enumerated in hard constraints. No additional libraries without halt-and-signal.

---

## Halt conditions

Halt and return with a named failure signal if:

- Any hard constraint cannot be honoured.
- A spec acceptance criterion is discovered unsatisfiable under the approved direction.
- The build genuinely requires an amendment to a sealed component (scope-of-work, memory, primary-persona) — do not amend silently; surface the conflict.
- An additional runtime dependency appears necessary — surface; do not add.
- Any ambiguity requiring an invented constraint not in owner's words.

Halts return control to the primary persona, who reviews with the owner. The proposal is adjusted; execution resumes against the revised version.

---

## Return format

On completion, return with a summary (≤600 words) covering:

1. Which deliverables D1–D9 completed, which halted.
2. Which spec criteria now pass (cite by v1.0 behaviour or v1.1/v1.2 revision number).
3. Confirmation that scope-of-work's 77 existing tests still pass (63 original + 14 D0) — no sealed-component amendment.
4. Test counts and pass rates on the tracker itself.
5. Complexity outcome — AI-time vs the proposal's 340–420-minute estimate.
6. Commits on `pos-v2`.
7. Any halt signals raised.
8. Recommended next action: declare the objective-tracker component complete / flag remaining gaps.

---

## What this brief is NOT

- Not a specification of module names, class hierarchies, file layout, or function signatures beyond the API surface the proposal has sketched.
- Not a step-by-step execution plan.
- Not a commitment to amending scope-of-work or any other sealed component.
- Not a commitment to designing consumers (self-correction loop, observability aggregator) — those have their own components and briefs.

---

## inferences recorded in this brief (flagged so the builder can challenge)

Two items below come from the primary persona's interpretation rather than the owner's verbatim words. Marked so the builder can surface objections:

- *The dispatch-layer integration point for `bind_scope` enforcement is "whatever layer orchestrates scope activation in the workspace."* No such dispatch layer exists yet in the new pOS — the workspace-side harness will call `bind_scope` when its dispatch story is designed. For this build's integration test, the builder may mock a minimal test dispatcher that calls `bind_scope` before scope activation to demonstrate the enforcement works. If the builder finds this unclear or requires a different integration shape, halt and flag.
- *The `scope_success` criterion auto-evaluation subscribes to scope-of-work's pyee emitter at tracker startup.* decision recorded was "auto-evaluate on scope events"; inference recorded is specifically that the tracker's startup subscribes via scope-of-work's existing emitter API. If the builder finds a better integration (e.g. polling, direct state query on a schedule) halt and flag.
