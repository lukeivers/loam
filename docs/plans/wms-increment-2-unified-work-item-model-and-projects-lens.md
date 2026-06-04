# WMS Increment 2 — the unified WORK-ITEM model (L1) + the PROJECTS lens

**Status:** sub-plan-doc (PLAN ONLY — no build) · **Date:** 2026-06-03 · **Owner:** Luke (greenlit "build it all the way through", Telegram 13704)
**WD:** `/Users/lukeivers/loam` (canonical loam checkout)
**Parent plan / architecture:** `docs/design/work-management-system-architecture.md` — the work-items-first model + the 7-increment roadmap + decisions WMS-D1..D7. **This is roadmap item 2.**
**Predecessors (load-bearing prior seals + artefacts, Tier-0 read on disk 2026-06-03):**
- **objective_tracker** (the L1 seed — extend, do NOT replace) — `framework/objective-tracker/src/loam/objective_tracker/` : `spec.py` (`ObjectiveSpec` 7-field primitive, `ObjectiveStatus` 5-state lifecycle `proposed/active/owner_pending/achieved/abandoned`, `ParentClosePolicy`, `LiftedFrom` provenance, the criterion discriminated-union), `events.py` (append-only typed event log; `ObjectiveCreated`/`StatusTransitioned`/`CriterionEvaluated`/`ScopeBound`/`ParentClosed`; `event_from_row` replay), `runtime.py` (`ObjectiveTracker`: `query_projection_view`/`list`/`list_by_root`/`trace_to_root`/`get`/`snapshot`/`register_source_binding`), `projection_view.py` (`ObjectiveProjection` public immutable read-model), `filter.py` (`ObjectiveFilter` — `authored_by` + `lifted_from_source_doc`, AND-narrowed). **Event-sourced; the projection cache rebuilds from events alone (the D8 round-trip).**
- **tracker_context** (the existing state + priority vocabulary) — `framework/primary-persona/src/loam/primary_persona/tracker_context.py` : `IN_FLIGHT_STATUSES = {proposed, active}`, `OWNER_PENDING_STATUS`, `OPEN_LOOP_STATUSES`, `_OPEN_LOOP_PRIORITY_RANK`, the narrow read-only `TrackerClient` Protocol. **The priority-key the WMS-D5 derived priority composes ON, never replaces.**
- **FBM Slice C** (project STATE engine) — `framework/tools/loam/src/loam_cli/audit/registry.py` : `derive_project_state(name)` (fresh-from-ground-truth, `None` for unregistered), `PROJECT_REGISTRY` (registers exactly `loam` + `cairn` today), `registered_project_names`, `ProjectStateSpec`. **FBM OWNS project STATE; the projects lens CONSUMES it, never re-derives.**
- **FBM Slice D** (per-turn surfacer discipline) — `framework/primary-persona/src/loam/primary_persona/keep_pace/project_state.py` : `render_project_state_block`, `register_project_state_contributor`, `_STATE_BLOCK_CHAR_CAP = 600`, `_STATE_TTL_SECONDS = 60`. **The TTL-cache + char-cap + fail-soft renderer the projects lens REUSES (Lens-1).**
- **Increment 1** (the work-streams lens) — plan-doc `docs/plans/work-streams-fbm-derived-tracks.md`; the WMS-D7 pre-L1 SHIM + the re-pointability AC. **⚠ NOT YET BUILT — see §10 RF #1; this materially affects the re-point scope.**
- **Slice E** (aggregation + plain-render precedent) — `framework/primary-persona/src/loam/primary_persona/work_visibility.py` : read-only multi-source snapshot, zero-internal-vocab HARD invariant.
- **Composer** — `framework/primary-persona/src/loam/primary_persona/context_composer.py` : `TriggerKind.turn`, `register`, the 10k-char structural cap. The registration seam.
**BASELINE candidate:** current branch tip at build time (the plan-doc commit's parent). Components in §2 + D-WMS2.1 — recommendation: **two-component amendment on `objective-tracker` (the L1 extension) + `primary-persona` (the projects lens + the streams re-point).**
**Status-file target:** `docs/STATE.md` + roadmap §8 + parent architecture §7 row-2 backfill (see §9).
**Quality bar:** ODD §2.5 — every AC outcome-shape, no method-in-AC; ≥1 outcome-altitude AC exercising the production entry points through a real turn with no pre-arranged state. Normal careful loam discipline (sealed cycle + tests) — this is bounded-to-the-individual (the user's own work-tracking), NOT the high-risk confidence-gate bar.

---

## §1 Summary / TL;DR

**What ships (increment 2 only):** the **unified WORK-ITEM model (L1)** — a single first-class work item/effort as the source of truth — built by **extending the sealed `objective_tracker`** (Lens-1; WMS-D1) with the relational graph (`blocks` / `waits-on` / `relates-to` edges + `belongs-to-project` + `tagged-streams[]`), a derived `priority` signal, a `blocked` lifecycle distinction, and intake/project-binding provenance — then the **PROJECTS lens** as a VIEW over that graph (bounded efforts; STATE derived live from FBM Slice C, same renderer discipline as the streams lens), and a **re-point of increment-1's work-streams shim** onto the real work-item graph (satisfying WMS-D7's re-pointability AC so the streams become true tag-views, not a parallel store).

**AC families:**
- `AC.WI.*` — the work-item entity: the extended schema (edges, priority, project-binding, stream-tags, provenance), event-sourced, round-trips through events alone, parent/child + the new non-tree edges resolve.
- `AC.WI.EDGE.*` — the relational graph: `blocks`/`waits-on`/`relates-to` edges memory has no concept of; an unblocked-next query; no-edge-fabrication.
- `AC.PROJ.*` — the projects lens: filter (`belongs-to-project`) + group + sort + render over the graph; STATE derived live from FBM for bound projects; the no-ground-truth-bound honest mark for unbound ones.
- `AC.REPOINT.*` — increment-1's streams shim re-points at the work-item graph: a stream's project-bindings/backlog resolve to work-items tagged with the stream, NOT a register-local list; the WMS-D7 re-pointability AC is satisfied.
- `AC.WMS2.LIVE.*` — **outcome-altitude**: one real turn surfaces work through BOTH the projects lens AND the re-pointed streams lens, ALL over ONE work-item store, STATE derived live — no parallel drift.

**Key decisions baked (full list + recommendations in §3):**
1. **WMS-D1 confirmed — EXTEND objective_tracker, do NOT build a new store** (§3 D-WMS2.1, with the fence justification §2 + §5). The tracker already IS an event-sourced work-item store with lifecycle + parent/child + projection + provenance; the increment is additive edges + fields.
2. **Edge representation: a typed `WorkEdge` event in the existing append-only log** (a new event kind alongside `ObjectiveCreated`/`StatusTransitioned`), NOT a side table — keeps the single-source-of-truth + the event-replay round-trip (§3 D-WMS2.2).
3. **WMS-D2 confirmed — computed lenses with a per-turn TTL cache** (Slice D discipline); no materialized lens-index this cycle (§3 D-WMS2.3).
4. **The streams re-point is the streams lens reading work-item tags** — the `WORK-STREAMS.md` register stays the lens-presentation config (attention/nest), its project-bindings/backlog resolve THROUGH the graph (§3 D-WMS2.4).

**F2 RF on scope realism (full treatment in §10):** the load-bearing realism caveat is that **increment 1 is NOT yet built** (the READ-FIRST framed it as sealed; the filesystem says `work_streams.py` does not exist). The re-point (scope item 3) cannot re-point a store that does not exist. Resolution + the two viable orderings are in §10 RF #1 and named as halt-trigger §8 #1 — this is the single thing Luke should weigh before the build dispatches.

---

## §2 Placement decisions

| Item | Placement | Rationale |
|------|-----------|-----------|
| The work-item schema extension (edges, priority, project-binding, stream-tags, `blocked` state, intake provenance) | **`objective-tracker`** component (`spec.py` additive fields + a new `WorkEdge` event in `events.py` + projection surfacing in `projection.py`/`projection_view.py`) | WMS-D1 + Lens-1: the tracker IS the event-sourced work-item store; the extension is ADDITIVE (the amendment-#38 `LiftedFrom` + the R2 `owner_pending` widening are the exact additive precedent). A new store would abandon a sealed primitive + re-create the five-surface drift (architecture §2b). |
| The projects lens (filter+group+sort+render over the graph; STATE derived live) | **`primary-persona`** keep-pace (`.../keep_pace/projects.py`, sibling to `project_state.py` + the incr-1 `work_streams.py`) | The lens IS a keep-pace `TriggerKind.turn` view; it composes Slice D's `render_project_state_block` + `derive_project_state` (Lens-1), reading the graph via the narrow `TrackerClient` Protocol. |
| Live project STATE for a bound project | **reused verbatim** from `derive_project_state` (Slice C) | Lens-1 — FBM owns STATE; the lens is a pure consumer. |
| The streams re-point (streams' bindings/backlog resolve to tagged work-items) | **`primary-persona`** keep-pace (the incr-1 `work_streams.py` surfacer gains a graph-backed resolution path) | WMS-D7: the streams lens reads work-item `tagged-streams[]` instead of a register-local list; the register keeps only the lens-presentation config (attention/nest). |
| The `belongs-to-project` ↔ FBM-registry binding | a field on the work item resolved at render time against `PROJECT_REGISTRY` | A bound item's STATE derives live; an unbound item is honestly marked (architecture §5 gap, AC.PROJ.3). |

**Out of placement (NOT this increment):** intake (incr-3), derived-priority *weighting* + graph self-heal (incr-4), goals/plate/waiting-on lenses (incr-5), per-user lens-choice wiring (incr-6), analytics (incr-7). This increment lands the L1 *fields/edges* + the projects lens + the re-point — the `priority` field EXISTS and is populated by the existing `tracker_context` key, but the multi-signal *weighting* (WMS-D5) is incr-4.

---

## §3 Named decisions (with recommendations) — surface to Luke

Every decision carries a recommendation. ★ flags a genuine **owner product-shape call**; the rest are **autonomous method-calls** (the builder takes method from here).

### D-WMS2.1 — Extend objective_tracker vs a new work-item store. **RECOMMEND (confirms architecture WMS-D1): EXTEND `objective_tracker`. Method-call, NOT an owner product-shape fork — the architecture already ruled it + the code confirms the fit.**
- **The fence justification (verified on disk):** the tracker already carries 6 of the 7 §2a field-groups — identity (`id`/`goal`/`authored_by`), state (the 5-state lifecycle + `owner_pending`), parent/child (`parent_id`, one-parent forest + `trace_to_root`), criteria, provenance (`LiftedFrom`), and an event-sourced replay store. **What is genuinely missing and this increment ADDS:** (a) non-tree edges (`blocks`/`waits-on`/`relates-to` — the tracker has only the single-parent tree); (b) `belongs-to-project` + `tagged-streams[]`; (c) a `blocked` state distinction; (d) a `priority` surfacing field. Every add is ADDITIVE — the same shape as amendment-#38's `LiftedFrom` widening and the R2 `owner_pending` widening, both of which preserved the D8 round-trip (pre-widening records deserialise unchanged).
- **Cost honestly (F2):** this elevates `objective_tracker` from "the persona's objective tracker" to "the work-management L1 backbone" — a role-expansion of a SEALED component. It is touched with a manifest entry; if the extension would require changing an EXISTING read-contract (`ObjectiveProjection`'s current fields, `ObjectiveFilter`'s current keys, the existing event kinds) rather than ADDING to them, the builder HALTS (§8 #2). Additive-only is the fence.
- **Alternative rejected:** a new `work_item` store. Rejected — re-creates the five-surface drift the whole architecture exists to kill (§2b), abandons a sealed working primitive, and forces FBM-binding duplication.

### D-WMS2.2 — Edge representation. ★ **RECOMMEND: a typed `WorkEdge` event in the EXISTING append-only event log** (a new event-kind alongside `ObjectiveCreated`, projected into the read-model), NOT a separate edge table and NOT an in-spec field list. **This is a genuine schema-shape call worth Luke's eyeball — it is the one decision that boxes-in or frees increments 4–5.**
- **Why an event, not a field:** edges are mutable relationships (a `waits-on` clears when the blocker ships; the incr-4 self-heal MUTATES edges against FBM ground truth). The tracker's whole design is "mutation is via events" (`StatusTransitioned` is the precedent). An edge as an append-only `WorkEdge`/`WorkEdgeCleared` event pair keeps the single-source-of-truth + the replay round-trip + gives incr-4's self-heal a clean append-only mutation path. A field-list on the spec would be a mutable-frozen-model contradiction (the spec is `frozen=True`).
- **Why not a side table:** a parallel edge table outside the event log breaks the "projection rebuilds from events alone" invariant (the D8 round-trip) — the exact single-source property the architecture is built on.
- **Edge shape recommended:** `WorkEdge{from_id, to_id, kind: blocks|waits-on|relates-to, party?: external-party-name}` — `waits-on` with an external `party` is the "waiting on Eric" case (architecture §4c); `blocks` is the inverse the unblocked-next query reads; `relates-to` is the soft non-blocking link.
- **The owner call:** confirm the edge-as-event shape (vs a field-list) — it is load-bearing for incr-4/5 and worth a deliberate yes. Recommendation is event-as-edge.

### D-WMS2.3 — Computed lens vs materialized index. **RECOMMEND (confirms WMS-D2): computed — the projects lens is a live query+filter+sort over the graph, with the per-turn Slice-D TTL cache for the surfaced block. NO materialized lens-index this cycle. Method-call.**
- Why: single-user-scale work set; the graph query is cheap; Slice D's 60s TTL already bounds per-turn cost. A materialized index is a cache, never a source of truth, and only justified if lens-render latency proves a real problem — that is named as halt-trigger §8 #3 (mirrors the incr-1 plan §8 #4), not built speculatively.

### D-WMS2.4 — How the streams re-point. ★ **RECOMMEND: the streams lens resolves its membership from work-item `tagged-streams[]` (the graph), and the `WORK-STREAMS.md` register keeps ONLY the lens-presentation config (attention: active/deep-dive/paused; nest-under). A stream's `projects:` binding and backlog resolve THROUGH tagged work-items, not a register-local list.** Worth Luke's eyeball because it changes what increment-1 ships.
- Why: this IS the WMS-D7 re-pointability outcome — the streams stop being a parallel store and become a true tag-view, dissolving the OBJECTIVES-vs-WORK-STREAMS duplication the incr-1 plan §10 #4 flagged.
- **The ordering call (the real fork — see §10 RF #1):** because incr-1 is NOT yet built, the re-point is either (a) **fold-forward** — build incr-1's streams lens directly graph-backed in THIS increment (no shim ever ships), or (b) **build incr-1 first** with the pre-L1 shim, then re-point here. RECOMMEND **(a) fold-forward** — it is strictly less total work (the shim is never built then re-pointed) and the architecture's only reason for the shim was "incr-1 ships before L1 exists for the cheapest proof." If Luke wants the cheapest-possible incr-1 proof shipped first regardless, (b) is valid. This is the one ordering decision Luke should rule.

### D-WMS2.5 — The `priority` field this cycle. **RECOMMEND: add the `priority` field + populate it from the EXISTING `tracker_context` open-loop priority-key (`_OPEN_LOOP_PRIORITY_RANK`); the multi-signal WMS-D5 weighting (goal-alignment + dependency-position + staleness) is incr-4, NOT here. Method-call.**
- Why: the field must EXIST for the projects-lens sort to be real, but the derived *weighting* is a later increment's scope (architecture §7 row 4). This cycle wires the field to the priority vocabulary that already ships; incr-4 enriches the signal. Keeps this increment's scope honest (Lens-4: don't build incr-4's weighting under incr-2's confidence).

---

## §4 Spec-objective placement

- **Binds to:** the work-management-system prime capability (architecture §1 + §10 Lens-2) — "where is all my work / what's next / what's waiting on me" reduced to zero translation burden. The projects lens + the unified model are roadmap item 2, the L1 FOUNDATION every later lens binds to.
- **Ladders up to:** **VALUE_PROPOSITION prime objective** (per `feedback_value_proposition_as_prime_objective`) — Lens-2 primary-persona test: a single accurate multi-lensed work model the persona surfaces + reasons over every turn IS the translation-burden win; the projects lens is the second view proving the model holds.
- **Prime directive tie (Lens-0):** per-user-tuned translation applied to work — the user brings WHAT work exists; loam owns HOW it is modelled, related, and surfaced. The unified L1 model is what makes the lenses coherent (the multi-lens-over-one-model insight, architecture §1 ★).

---

## §5 Sealed-component fence

**Two components touched; both with manifest entries.**

1. **`objective-tracker`** (SEALED) — the L1 extension. **Fence: ADDITIVE-ONLY.** Permitted: new `WorkEdge`/`WorkEdgeCleared` event kinds added to the discriminated union + `_EVENT_CLASSES`; new ADDITIVE optional fields on `ObjectiveSpec`/`ObjectiveCreated` (`belongs_to_project`, `tagged_streams`, `priority`, edge-derived projection fields) with defaults that preserve the D8 round-trip; new projection-surfacing of edges on `ObjectiveProjection` (additive fields); a `blocked` value added to `ObjectiveStatus` (additive enum member, the R2 `owner_pending` precedent). **Forbidden without a halt:** changing an EXISTING field's type/meaning, removing/renaming an event kind, narrowing `ObjectiveFilter`'s existing keys, or any change that makes a pre-widening record fail to deserialise (the D8 round-trip is the hard invariant — §8 #2).
2. **`primary-persona`** (SEALED, has a live sidecar) — the projects lens + the streams re-point. **Fence:** new keep-pace modules (`keep_pace/projects.py`) + the incr-1 `work_streams.py` gains a graph-backed resolution path; the surfacer registers as a `TriggerKind.turn` contributor. **Forbidden without a halt:** modifying the `OBJECTIVES.md` read-contract KP1/N4 bind to (incr-1 plan §8 #2 precedent), or widening the narrow read-only `TrackerClient` Protocol into a write surface (the lens is read-only over the graph; writes go through the tracker's own API).

Both components seal via `loam amend apply` + `loam amend seal` — **name `loam amend apply` explicitly in the build dispatch** (per `feedback_dispatch_explicit_loam_amend_apply`); serialize the two-component build in one tree (per `feedback_serialize_amendment_builds` — do NOT run two build agents in this tree concurrently).

---

## §6 Acceptance criteria (outcome-shape; method-in-AC test passed on each)

Each AC states an *outcome* satisfiable by methods other than the one in mind; each maps to a named test at build time. AC IDs are scope-descriptive (per `feedback_scope_descriptive_ac_ids`).

**AC.WI.1** — A work item carries, in addition to the existing identity/lifecycle/parent-child/criteria/provenance, a `belongs-to-project` binding, a `tagged-streams` set, and a `priority` value; a work item constructed without any of these is still well-formed (every pre-existing record deserialises unchanged). *(Outcome: the schema is extended additively + round-trips; method — field vs sub-model — is the builder's call. The D8 round-trip is the hard property.)*

**AC.WI.2** — A work item's full state, including its edges and new fields, reconstructs from the event log alone after a cold projection rebuild — no out-of-log side state is load-bearing. *(Outcome: single-source-of-truth preserved; method is the builder's call.)*

**AC.WI.EDGE.1** — A `blocks` / `waits-on` / `relates-to` edge can be recorded between two work items (and a `waits-on` may name an external party); the edge surfaces on the projection of both endpoints; a recorded edge can be cleared, and after clearing it no longer surfaces. *(Outcome: the relational graph memory has no concept of exists + is mutable; method — event-pair vs table — is the builder's call.)*

**AC.WI.EDGE.2** — Given a set of work items with `waits-on`/`blocks` edges, a query returns the items that are NOT waiting on any unresolved blocker (the "next unblocked thing" question); an item waiting on an external party is reported as waiting-on-other, not as next. *(Outcome: the graph answers the question memory cannot; method is the builder's call.)*

**AC.WI.EDGE.3** — No edge is fabricated where none was recorded: querying a work item with no recorded edges returns no edges, and a project binding to an unregistered FBM project does not synthesize a `blocks`/`waits-on` relationship. *(Outcome: no edge-fabrication — the honest-graph invariant; method is the builder's call.)*

**AC.PROJ.1** — The projects lens loads work items filtered to those with a `belongs-to-project` binding, groups them by project, sorts within a project by `priority`, and renders one concise block within a hard character cap — composing the Slice-D renderer discipline, NOT a second wall of text. *(Outcome: a projects view exists, filtered+grouped+sorted+capped; method is the builder's call.)*

**AC.PROJ.2** — For a project bound to a registered FBM project, the lens's surfaced STATE is composed from a FRESH `derive_project_state` call (the Slice-C production entry point), never a stored/stale status string; changing the underlying repo ground truth and re-reading the lens reflects the change without editing any register. *(Outcome: derived-not-stored, verifiable by changing ground truth; method is the builder's call. Mirrors incr-1 AC.WS.DERIVE.1.)*

**AC.PROJ.3** — A project bound to NO registered FBM project (e.g. a Money/LitRPG/Personal-Home project) surfaces a next-action from its work-items' staleness/cadence AND is explicitly marked "no ground-truth project bound" — it never fabricates a derived build-STATE. *(Outcome: the architecture §5 honest gap as an AC; method is the builder's call.)*

**AC.REPOINT.1** — The work-streams lens resolves a stream's membership from work-items carrying that stream in `tagged-streams`, NOT from a register-local backlog list; a work item tagged with a stream AND bound to a project appears in BOTH the streams lens and the projects lens without being stored twice. *(Outcome: the WMS-D7 re-pointability AC satisfied — streams are a tag-view over the one graph; the appears-in-both-without-duplication is the architecture's whole point. Method is the builder's call.)*

**AC.REPOINT.2** — The `WORK-STREAMS.md` register, after the re-point, carries ONLY lens-presentation config (a stream's `attention` state and `nest-under`); a stream's project-binding and backlog are no longer a register-owned parallel list. Re-pointing required no rewrite of the register's attention/nest config. *(Outcome: the shim is dissolved, not duplicated; the register stays the lens-definition surface. Method is the builder's call.)*

**AC.WMS2.LIVE.1 (OUTCOME-ALTITUDE, `outcome-altitude:true`)** — Through ONE real keep-pace turn against the LIVE loam + cairn repos with NO pre-arranged state: the surface presents work through BOTH the projects lens AND the re-pointed streams lens; a work item that belongs to a project AND is tagged with a stream appears in both views; the project's STATE is DERIVED live from `derive_project_state` (e.g. the `loam` project → loam's real built/sealed STATE); and both lenses read from the SAME work-item store (no parallel store, no stored-stale status). Invokes the production entry points (tracker query + projects-lens render + streams-lens render + `derive_project_state`), no fixtures, no pre-arranged state. *(This is the literal "both lenses over ONE work-item store, derived live, no parallel drift" the objective names. Method is the builder's call.)*

---

## §7 Build steps (method-level guidance only — builder's call per ODD §1.1)

Two-component amendment (`objective-tracker` + `primary-persona`); serialized in one tree. Per-cycle shape:
1. Manifest at `docs/plans/wms-increment-2-unified-work-item-model-and-projects-lens.manifest.yaml` (paired, below); two `components:` entries.
2. **`objective-tracker` extension (AC.WI.* + AC.WI.EDGE.*):** add the `WorkEdge`/`WorkEdgeCleared` event kinds (events.py union + `_EVENT_CLASSES` + replay); add the additive `belongs_to_project`/`tagged_streams`/`priority` fields (spec.py + ObjectiveCreated, default-preserving); add a `blocked` `ObjectiveStatus` member; surface edges + new fields on `ObjectiveProjection`; the unblocked-next query as a runtime method. Hold the D8 round-trip (every test of a pre-widening record stays green).
3. **`primary-persona` projects lens (AC.PROJ.*):** add `keep_pace/projects.py` (filter `belongs-to-project` → group → sort by priority → render via Slice-D discipline + per-project `derive_project_state`); register as a `TriggerKind.turn` contributor; the no-ground-truth-bound honest mark.
4. **The streams re-point (AC.REPOINT.*):** per D-WMS2.4's ordering ruling (§3 / §10 RF #1) — either fold-forward (build the streams lens graph-backed here) or re-point an already-built incr-1 shim. The streams lens resolves membership from `tagged-streams`; the register keeps attention/nest only.
5. Tests authored per AC (each AC → a named test; `AC.WMS2.LIVE.1` is the outcome-altitude live-repo test through both lenses).
6. `loam amend apply` (name it explicitly in the dispatch) → seal → smoke (a real turn renders both lens blocks over the one store).

---

## §8 Halt triggers (abort the in-flight build + surface)

1. **Increment 1 is not built AND the ordering ruling (D-WMS2.4 fold-forward vs build-incr-1-first) is not yet given.** Halt — this is the load-bearing scope fork (§10 RF #1); the builder cannot re-point a streams store that does not exist, and must not silently pick the ordering. Surface for the ruling.
2. **The objective-tracker extension would require changing an EXISTING field/event/filter-key rather than ADDING** (i.e. a pre-widening record would fail to deserialise, or `ObjectiveProjection`/`ObjectiveFilter`'s existing contract narrows). Halt — that breaks the D8 round-trip + a sealed read-contract; surface rather than silently widen (the additive-only fence, §5).
3. **The computed projects lens is too slow per-turn even with Slice D's TTL cache** when fanned across projects + edge-resolution. Halt — surface a caching/materialized-index ruling (WMS-D2's named escape hatch) rather than introduce a per-turn latency regression.
4. **Extending the streams re-point would require modifying the `OBJECTIVES.md` read-contract** KP1/N4 bind to. Halt — touches a predecessor contract without a manifest entry (incr-1 plan §8 #2 precedent); surface.
5. **An AC drifts to method-in-AC during build** (a test can only pass one specific way). Halt + fix the AC (doc-only) per `feedback_loose_AC_text_fix_AC_not_implementation`, never the implementation.
6. **Scope creep into increments 3–7** — if a "next unblocked thing" or "derived priority" task starts pulling in intake parsing (incr-3), multi-signal priority weighting (incr-4), the goals/plate/waiting-on lenses (incr-5), lens-choice wiring (incr-6), or analytics (incr-7). Halt — those are later in the chain (§2 out-of-placement); surface rather than widen.

---

## §9 Bookkeeping (backfill on seal)

- **`docs/STATE.md`** — add the L1 work-item model (objective-tracker extended to the WMS backbone) + the projects lens under primary-persona/keep-pace.
- **Roadmap §8 / parent architecture §7** — mark increment-2 row as built (the unified L1 model + projects lens + streams re-point landed).
- **`docs/design/work-management-system-architecture.md`** — backfill WMS-D1 confirmed-extend, WMS-D2 confirmed-computed, WMS-D7 re-pointability satisfied (or fold-forward if D-WMS2.4(a) ruled).
- **Increment-1 plan** (`docs/plans/work-streams-fbm-derived-tracks.md`) — if fold-forward (D-WMS2.4(a)) ruled, note the shim was never built; the streams lens shipped graph-backed in increment 2.
- **Task #84** (the MAJOR sub-component) → progress note: increment 2 sealed. **Task #70** (work-streams) → reconciled with the actual build state (see §10 RF #1; #70's "completed" marked the PLAN, not the build).
- **`feedback_*` memory** — none new required; this cycle consumes existing principles. (If the edge-as-event-vs-table question recurs across components, capture then.)

---

## §10 F2 Ruthless Feedback (honest doubts + named design risks)

1. **★ INCREMENT 1 IS NOT BUILT — the re-point has nothing to re-point yet (the load-bearing finding).** *Disagreement:* the dispatch's READ-FIRST states increment 1 is "already SEALED" and scope item 3 is "RE-POINT increment-1's work-streams shim." Both assume incr-1 shipped. *Evidence (Tier-0, this session):* `framework/primary-persona/src/loam/primary_persona/keep_pace/work_streams.py` DOES NOT EXIST; the incr-1 plan-doc is explicitly `Status: sub-plan-doc (PLAN ONLY — no build)`. Task #70 shows `[completed]` in the task list, but per `feedback_published_state_only_from_git_refs` + `feedback_notes_and_users_are_pointers_evidence_resolves`, the filesystem ground truth wins over the task-status note — #70's "completed" marks the PLAN sealed, not the build. *Alternative (the resolution, two viable orderings — Luke rules per D-WMS2.4):* **(a) fold-forward (RECOMMEND)** — build incr-1's streams lens directly graph-backed inside this increment; the pre-L1 shim is never built, so there is nothing to re-point and AC.REPOINT.* are satisfied by construction. Strictly less total work. **(b) build incr-1 first** (its plan is ready) with the WMS-D7 shim, then re-point here — valid only if Luke wants the cheapest-possible incr-1 proof shipped + sealed before L1. This is the one fork that changes the build dispatch's shape; it is halt-trigger §8 #1.

2. **objective_tracker role-expansion is real and touches a sealed component.** *Disagreement:* "just extend the tracker" understates that this promotes a sealed primitive from "the persona's objective tracker" to "the WMS L1 backbone." *Evidence:* `spec.py`'s `ObjectiveSpec` is `frozen=True` + `extra="forbid"` — adding mutable edges to a frozen-spec model is a contradiction if done as in-spec fields. *Alternative:* edges as append-only `WorkEdge` EVENTS (D-WMS2.2), not spec fields — this respects the frozen-spec + the event-sourced design + gives incr-4's self-heal a clean mutation path. The additive-only fence (§5) + halt-trigger §8 #2 keep the role-expansion from silently breaking the D8 round-trip.

3. **Half the projects have no ground-truth STATE — same gap as incr-1.** *Disagreement:* "projects with STATE derived live from FBM" is literally true only for `loam` + `cairn` (the two registered FBM projects). *Evidence:* `registry.py` `_default_registry()` registers exactly `loam` + `cairn`. *Alternative:* AC.PROJ.3 makes the unbound case explicit (staleness/cadence next-action + a "no ground-truth project bound" mark), never faking STATE; registering litrpg-writer + a money surface as FBM projects stays the named follow-on (incr-1 §7, out of scope here). Honest framing for Luke: this cycle delivers true live derivation for loam + Cairn projects now, clean staleness for the rest.

4. **The `priority` field ships but the WMS-D5 weighting does not (deliberate scope cut).** *Disagreement:* a projects lens that "sorts by priority" could imply the full derived-priority engine, which is incr-4. *Evidence:* architecture §7 row 4 places derived priority + the relational self-heal in increment 4. *Alternative:* D-WMS2.5 — the field exists + is populated from the EXISTING `tracker_context` priority-key this cycle; the multi-signal weighting is incr-4. Named so the scope line is conscious, not silent (Lens-4: don't build incr-4 under incr-2's confidence).

5. **Scope-confidence (F4) note.** The data-model SHAPE is HIGH-confidence (the architecture pinned it; the code confirms the fit) and tightly scoped. The two genuinely-open forks left as ★ owner-calls are the edge representation (D-WMS2.2) and the re-point ordering (D-WMS2.4 / RF #1) — both surfaced with recommendations, method left to the builder, no method locked in ACs. The lens-render details, the unblocked-next query internals, and the projection-surfacing mechanics are method-calls left loose. The ACs are outcome-shape; the forks are surfaced.

---

## §11 Provenance trail (load-bearing sources, verified on disk 2026-06-03)

- Architecture (parent) — `docs/design/work-management-system-architecture.md` (§2a work-item fields, §2b work-items-first F2, §2c WMS-D1, §3 lens-set + the projects-lens row, §5 FBM boundary + the ground-truth gap, §7 increment roadmap row 2, §8 the WMS-D7 incr-1 adjustment, §9 WMS-D1/D2/D7 recommendations).
- objective_tracker spec — `framework/objective-tracker/src/loam/objective_tracker/spec.py` (`ObjectiveStatus` lifecycle L58–96, `ObjectiveSpec` frozen 7-field L298–343, `LiftedFrom` additive-precedent L256–292, `extra="forbid"`+`frozen=True` L321).
- objective_tracker events — `framework/objective-tracker/src/loam/objective_tracker/events.py` (the discriminated union + `_EVENT_CLASSES` L152–170, `event_from_row` replay L173–178, the append-only-log + D8-round-trip docstring L15–25, `StatusTransitioned` mutation precedent L85–91).
- objective_tracker runtime API — `framework/objective-tracker/src/loam/objective_tracker/runtime.py` (`query_projection_view` L636, `list`/`list_by_root` L570/L595, `trace_to_root` L668, `register_source_binding` L703).
- projection read-model — `framework/objective-tracker/src/loam/objective_tracker/projection_view.py` (`ObjectiveProjection` frozen public view L49–90, `public_projection` builder L103–126).
- tracker_context (priority + read-only Protocol) — `framework/primary-persona/src/loam/primary_persona/tracker_context.py` (`IN_FLIGHT_STATUSES` L131, `OWNER_PENDING_STATUS` L140, `_OPEN_LOOP_PRIORITY_RANK` L160–164, the narrow `TrackerClient` Protocol L180–203).
- FBM Slice C STATE engine — `framework/tools/loam/src/loam_cli/audit/registry.py` (`derive_project_state` L117–139, `PROJECT_REGISTRY` registers loam+cairn L73–89, `registered_project_names` L108).
- FBM Slice D surfacer discipline — `framework/primary-persona/src/loam/primary_persona/keep_pace/project_state.py` (`render_project_state_block` L168, `_STATE_BLOCK_CHAR_CAP=600` L66, `_STATE_TTL_SECONDS=60` L62, `register_project_state_contributor` L250).
- Increment 1 (streams) — `docs/plans/work-streams-fbm-derived-tracks.md` (PLAN ONLY status L3; the WMS-D7 shim + re-pointability intent §8/§10 #4; AC.WS.DERIVE.1 the derived-not-stored precedent L110). **`work_streams.py` confirmed absent on disk — RF #1.**
- Composer registration seam — `framework/primary-persona/src/loam/primary_persona/context_composer.py` (`TriggerKind.turn`, `register`, the 10k cap).
- Owner mandate — Telegram 13704 ("build it all the way through"); 13656 (WMS elevated to MAJOR sub-component); 13511 (multi-lens-over-one-model; span-AND-nest; derived-not-stored).
