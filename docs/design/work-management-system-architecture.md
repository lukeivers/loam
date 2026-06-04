# loam — WORK MANAGEMENT SYSTEM architecture

**Date:** 2026-06-03 · **Status:** READ-ONLY ARCHITECTURE (nothing built here; every increment below is an owner-gated future build-plan) · **Owner:** Luke Ivers (owner-elevated to MAJOR sub-component, Telegram 13656) · **Author:** dispatched design agent (Opus)

**Scope-tightness (Lens 4):** the *data-model shape* (work-as-first-class-entity, lenses-as-views) is HIGH-confidence and tightly scoped — it is the foundation everything else binds to, so it is pinned. The *function internals* (intake parser, prioritization weighting, analytics surfaces) and *increment-2+ method* are LOW-confidence and deliberately left loose: named as decisions, not locked. This doc gives outcome-shape to the increment plans; method stays the builder's call (Lens 3).

**This is a VISION + DATA MODEL + LENS SET + FUNCTION MAP + FBM BOUNDARY + INCREMENT ROADMAP + NAMED DECISIONS.** It is NOT a build and NOT a single-feature plan. The work-streams plan (`docs/plans/work-streams-fbm-derived-tracks.md`) is INCREMENT 1 and derives from this; §8 names the one adjustment it needs to fit the unified model.

---

## Tier-0 reads this composes on (verified on disk 2026-06-03; do NOT re-derive)

| Primitive | File | What it owns | Role in this system |
|---|---|---|---|
| **objective_tracker** | `framework/objective-tracker/src/loam/objective_tracker/` (`spec.py`, `store.py`, `projection_view.py`, `events.py`) | Event-sourced, DB-backed work-item store: a lifecycle (`proposed → active → … → owner_pending → terminal`), a projection view, trace-to-root parent/child. | **The existing structured work-item store.** This IS the seed of the data model — work items already exist here as first-class, event-sourced records. |
| **tracker_context** | `framework/primary-persona/src/loam/primary_persona/tracker_context.py` | The persona's read over the tracker: `IN_FLIGHT_STATUSES`, `OWNER_PENDING_STATUS`, `OPEN_LOOP_STATUSES`, priority-key, projection filtering. | **The existing state + priority vocabulary** over work items. |
| **FBM `derive_project_state`** (Slice C) | `framework/tools/loam/src/loam_cli/audit/registry.py` | Ground-truth per-PROJECT build/sealed/merged STATE derived from git refs + markers (loam + cairn registered). Never prose. | **FBM owns project STATE.** The work system consumes this; it never re-derives. |
| **project_state surfacer** (Slice D) | `framework/primary-persona/src/loam/primary_persona/keep_pace/project_state.py` | The per-turn keep-pace STATE block: TTL-cached, 600-char-capped, fail-soft, one line per project. | **The surfacing engine.** The work-system's per-turn lens REUSES this renderer discipline + subsumes its block. |
| **work_visibility** (Slice E) | `framework/primary-persona/src/loam/primary_persona/work_visibility.py` | Read-only multi-source snapshot: tracker counts + flow cursor + watchdog health + per-project STATE, plain-language render, zero-internal-vocab HARD invariant. | **The aggregation + plain-render precedent.** The "on-my-plate" / "waiting-on" lenses extend this snapshot. |
| **OBJECTIVES.md register** (KP5) | `framework/primary-persona/src/loam/primary_persona/keep_pace/objectives.py` | User-scope `~/.claude/OBJECTIVES.md`: `Objective` schema (slug/status/cadence/last-touched/subgoals/detail-path), index/detail shape, owner-gated `status`, byte-budget. | **The user-scope register precedent + the "goals" lens substrate.** Objectives ARE the goals lens; work items ladder up to them. |
| **interaction-model** (#34/N4) | `framework/primary-persona/src/loam/primary_persona/keep_pace/interaction_model.py` + `docs/design/adaptive-interaction-model.md` | Per-user `component × axis → {value, confidence, evidence}` matrix; deterministic turn-time lookup; openness-biased; explicit-statement hard-set. | **The lens-CHOICE engine.** Which lens loam surfaces per-user is a per-user preference cell — this is where it lives. |
| **work-streams plan** (Increment 1) | `docs/plans/work-streams-fbm-derived-tracks.md` | Cross-cutting attention tracks, FBM-STATE-derived, per-turn surfaced, deep-dive/pause. | **The first lens.** Derives from this doc; §8 names the adjustment. |

---

## §1 The vision — why a work-management system exists

A non-technical user running on heavy abstraction + closed-loop autonomy has **no good mechanism to track their work or remember what was planned vs done.** They cannot read the task DB, the git refs, the FIDRAFT, or the queue files. They asked loam for an outcome; the work happened behind the abstraction; and now the work-state lives in five disconnected machine surfaces (tracker DB, FBM project STATE, FIDRAFT, the persona task list, the dev queue) that the user can never reconcile. **The status-anxiety that drove task #37 ("is it waiting on ME? what's stuck? where is each track?") is a TRANSLATION FAILURE** — the user cannot translate the system's work-state back into their own picture of "what's on my plate."

**This system is loam doing that FOR them, in a way that meets them where they are.** It ladders directly to the loam PRIME DIRECTIVE (`feedback_loam_prime_directive_user_tuned_translation.md`): the user brings WHAT they want done; loam owns HOW it is tracked, related, prioritized, and surfaced — *customized to that person*, because the same work does not get talked about the same way by every person.

**The Lens-2 statement:** this system reduces the translation burden of "where is all my work and what's next" to zero — the user never has to ask, never has to hand-maintain a `CURRENT-WORK.md`, never has to hold a task-ID. It adds to the persona's toolkit a single, accurate, multi-lensed model of all the user's work that the persona can surface, prioritize against, and reason over every turn.

### ★ The key insight — MULTI-LENS over ONE underlying work model

Work-streams, projects, goals, "what's on my plate," "what's waiting on me/others" are **NOT five different things to track.** They are five different **LENSES onto the SAME underlying work.** A "project" is a bounded slice of the work graph; a "stream" is a cross-cutting slice; a "goal" is the top of a ladder of work; "on my plate" is a filter+sort; "waiting on me" is a state-predicate. **Different non-tech users connect with different lenses** — one person thinks in projects, another in goals, another only ever asks "what's next for me today." The system presents the lens that fits THAT person (the choice is a per-user `interaction-model` preference, #34).

This insight is load-bearing for the data model: **if streams/projects/goals were separate primary entities, the same work would be tracked five times and drift five ways** (exactly the disconnect that exists today across the five machine surfaces). Modeling work once and lenses as views is what makes the system coherent.

### The layered shape (per prime-directive Architectural Model — Luke 13233)

```
  ┌─────────────────────────────────────────────────────────────┐
  │  L4  PER-USER LENS CHOICE        (interaction-model #34)      │  which lens fits THIS person
  ├─────────────────────────────────────────────────────────────┤
  │  L3  LENS / VIEW LAYER  — streams · projects · goals ·        │  views over the work graph
  │      on-my-plate · waiting-on   (each = a view, not a store)  │
  ├─────────────────────────────────────────────────────────────┤
  │  L2  FUNCTION LAYER  — intake · prioritize · relate ·         │  operations over work items
  │      analyze · track/surface                                  │
  ├─────────────────────────────────────────────────────────────┤
  │  L1  WORK MODEL  — work items (efforts) as first-class:       │  the ONE source of truth
  │      state · priority · relations · provenance                │  (objective_tracker, extended)
  ├─────────────────────────────────────────────────────────────┤
  │  L0  STATE / RECALL  — FBM: derive_project_state + recall     │  ground-truth STATE feeds L1
  │      (Slices C/D/E)  — FBM OWNS this; work-system CONSUMES it  │
  └─────────────────────────────────────────────────────────────┘
```

Clean interfaces between layers are the load-bearing property (Ren F2, 13233): a lens can be added or pruned without touching the work model; FBM's STATE engine can change without touching the lenses; the per-user lens choice changes nothing below L4.

---

## §2 The data model (L1) — work as the first-class entity

**RECOMMENDATION: work-items-first.** A single first-class entity — a **work item** (synonym: *effort*) — is the one source of truth. Streams, projects, goals, plate, waiting-on are VIEWS over a graph of work items. This is the foundation; get it right and everything composes; get it wrong and the five-surface drift returns.

### 2a. The work item — fields

A work item is the existing `objective_tracker` record, **extended** (not replaced — Lens 1: the event-sourced store, lifecycle, projection view, and parent/child trace already exist). The conceptual schema:

| Field group | Fields | Source / status |
|---|---|---|
| **identity** | `id`, `slug` (scope-descriptive, never version-packed — `feedback_scope_descriptive_ac_ids`), `title` (plain-language) | tracker (exists) |
| **state** | `lifecycle` (`proposed → active → blocked → owner_pending → done/dropped`), `last-touched`, `cadence`, staleness | tracker `IN_FLIGHT_STATUSES`/`OWNER_PENDING_STATUS` (exists); `blocked` + staleness = increment add |
| **priority** | `priority` (derived, not hand-stored — see §4b), explicit `pin`/`defer` overrides | tracker priority-key (partial); derived priority = increment add |
| **relations** (the contextual/relational web) | `parent`/`child` (decomposition), `blocks`/`waits-on` (dependency), `relates-to`, `belongs-to-project`, `tagged-streams[]` | tracker trace-to-root (parent/child exists); blocks/waits-on/tags = increment add |
| **provenance** | `origin` (intake source: conversation / FIDRAFT-graduated / dev-queue / owner-stated), `created`, `created-from-turn`, `owner-ratified?` | partial in events; provenance enrichment = increment add |
| **STATE binding** (the FBM tie) | `project-binding: <registry-name>?` — when this item is a project bound to an FBM-registered repo, its build-STATE is DERIVED live, never stored | binding = increment add; derivation = **FBM owns** (Slice C) |
| **ladders-up-to** | `objective-slug?` — the user-objective (goal) this work ladders up to | OBJECTIVES.md subgoals (exists, inverse direction) |

**The relational web is the differentiator over memory.** FBM recalls facts; it does not model how work *connects*. Dependencies (`waits-on`), decomposition (`parent`/`child`), and cross-cutting membership (`tagged-streams`) are the relational structure that lets the system answer "what's blocking the launch," "what's waiting on me," "what's the next unblocked thing" — questions memory cannot answer because memory has no edges.

### 2b. Why work-items-first and not lens-first (the central F2)

**Named conflict:** model work-items-first (lenses are views) vs lens-first (streams/projects/goals are each their own primary store). Signals:

- **Single-source-of-truth (decisive).** Lens-first means the same work lives in N stores and drifts N ways — this is *literally the disconnect today* (FIDRAFT, task list, dev queue, tracker, project STATE all separately hold pieces of the same work). Evidence: the work-streams plan §1 + Decision D6 spend their entire import/consolidation effort re-connecting three sources that should never have been separate. Work-items-first makes that disconnect structurally impossible.
- **The multi-lens insight requires it.** "Streams and projects are different lenses onto the same work" (Luke 13511) is only expressible if there IS one underlying work to lens. Lens-first contradicts the owner's own framing.
- **Composition with FBM (Lens 1).** FBM's STATE derivation is per-PROJECT (`derive_project_state(name)`). A work item with a `project-binding` consumes that cleanly. Lens-first would need each lens to separately bind to FBM — N duplications.
- **The existing primitive already IS work-items-first.** `objective_tracker` is an event-sourced *work-item* store with parent/child and a lifecycle. Lens-first would abandon a sealed, working primitive. Work-items-first EXTENDS it.

**Cost, honestly (F2):** work-items-first means the lenses are *computed*, not stored — every lens render is a query+filter+sort over the graph, which is more per-render work than reading a pre-materialized stream file. Mitigation: the same TTL-cache + char-cap discipline Slice D already uses (the lens render is cached per-turn; the graph query is cheap over a single-user-scale work set). This is the right trade: a little compute to guarantee zero drift.

**The alternative kept on the table (not rejected outright):** a *thin* materialized index per lens for performance (a cache, not a source of truth) is a legitimate optimization IF lens-render latency proves a problem (work-streams plan §8 halt #4 already names this as a halt trigger). That is a cache over the work graph, not a return to lens-first — the work graph stays the single source. Named as Decision **WMS-D2**.

### 2c. Where the work model lives

**RECOMMENDATION:** extend `objective_tracker` (the event-sourced store) as the work-item backbone, with the user-scope register files (`OBJECTIVES.md`, the incoming `WORK-STREAMS.md`) as the **lens-definition + index surfaces** that point INTO it. The tracker is the graph; the registers are named views + the user-scope surfaces the persona reads each turn. This keeps the heavy structured store where it already is and the light always-loaded surfaces at user-scope (the KP5 index/detail discipline). Named as Decision **WMS-D1** (it touches a sealed component's role).

---

## §3 The lens set (L3) — views over the work model

A **lens** is defined as: a **filter** (which work items) + a **grouping** (how they cluster) + a **sort** (priority order) + a **render** (how each surfaces) over the L1 work graph. Adding a lens = defining those four functions; it never adds a store.

| Lens | Filter | Grouping | The question it answers | Status |
|---|---|---|---|---|
| **work-streams** | items tagged with a stream | by `stream` (cross-cutting; can span projects + nest) | "how is each parallel track moving + what's next on each" | **Increment 1** (plan exists) |
| **projects** | items with a `belongs-to-project` (bounded effort) | by project; STATE derived live for FBM-bound projects | "where does each bounded project stand + what's its real build-state" | Increment 2 |
| **goals** | items laddering up to a user-objective | by `objective-slug` | "what am I actually trying to achieve + what work serves it" | Increment 5 (OBJECTIVES.md already half-exists) |
| **on-my-plate** | non-paused, non-blocked, active+queued items | flat, priority-sorted | "what should I look at now / today" | Increment 6 |
| **waiting-on** | items in `owner_pending` (waiting on ME) OR `waits-on` an external party (waiting on OTHERS) | by waiting-party | "what is blocked on me vs blocked on someone else" | Increment 6 (work_visibility already renders owner_pending) |

**A stream vs a project (the distinction that matters):** a **project** is a *bounded* effort with a definition of done (and possibly an FBM build-STATE). A **stream** is a *cross-cutting, open-ended track of attention* that can span multiple projects and nest. Same work items underneath; different slice. A work item tagged `loam` (stream) and `belongs-to-project: fbm-overhaul` (project) appears in BOTH lenses without being stored twice — that is the whole point of work-items-first.

**Lens choice is per-user (L4 / #34).** Which lens the persona surfaces by default is a cell in the interaction-model matrix (a new area-slug, e.g. `work-tracking`, with an axis for *preferred-lens*). A projects-thinker gets the projects lens surfaced; a "just tell me what's next" user gets on-my-plate. The openness-biased default (surface the streams lens, the broadest) dials to the user's demonstrated preference. Named as Decision **WMS-D3**.

---

## §4 The functions (L2) — operations over work items

### 4a. Intake — capture new work naturally from conversation

The single most prime-directive-aligned function: **the user states intent in natural language and a work item appears, correctly placed in the graph, without the user touching a tracker.** This is the "translation IN" pillar (prime directive Pillar 1) applied to work.

- **Mechanism (Lens 1):** the LLM intent-extraction seam already chosen for the four-step-loop intake (task #56 — replaces regex distillation) is the same seam. A conversational turn carrying work-intent ("I need to also get the rental paperwork going", "remind me the launch waits on Eric's review") is parsed into a work item: `{title, candidate-stream/project, candidate-relations, provenance: conversation}`.
- **The verify-before-build discipline (prime directive):** the inferred placement is a HYPOTHESIS surfaced, never silently committed — "Sounds like a new thing under Money — want me to track it there?" One plain-language confirm. The confirm doubles as a datum for the user-model (#34). The F2 over-reach guard applies: don't turn every "do X once" into a tracked effort; scale to what the user-model says this person wants.
- **Provenance is captured at intake** so the work item knows where it came from (conversation vs FIDRAFT-graduation vs dev-queue) — load-bearing for the import/consolidation the work-streams plan does manually today.

Named as Decision **WMS-D4** (intake aggressiveness — how readily a turn becomes a tracked item — is a per-user #34 preference, not a fixed threshold).

### 4b. Prioritization — derived, not hand-stored

Priority is **computed** from signals, not a number the user maintains (they can't, and shouldn't have to). Signal inputs: the user-objective the item ladders up to (a goal-aligned item outranks an orphan), dependency position (an item that *unblocks* others outranks a leaf), staleness against cadence, explicit owner pins/defers, and the `tracker_context` open-loop priority-key that already exists. The user can always override with a plain-language pin ("Money is the priority right now" → the Money-lens items float). **This composes with the existing `tracker_context` priority-key — it does not replace it.** Named as Decision **WMS-D5** (the weighting is calibrate-on-use, never an imported magic number — same Lens-4 discipline as #34's thresholds).

### 4c. The relational/contextual web

The function that builds + maintains the edges (§2a relations). Two sub-functions: (1) **capture** relations at intake ("the launch waits on Eric" → a `waits-on` edge to an external party); (2) **derive** relations where ground truth provides them (FBM project STATE already knows which modules are built → a project's child work-items can be auto-marked done when their module merges — the deviation-detection the work-streams plan routes to #71). This is where the work system does MORE than memory: it maintains a *live graph*, and it *self-heals* the graph against ground truth.

### 4d. Analytics

Read-only aggregate views over the graph: throughput (items done per week per stream/goal), aging (items stale past cadence), bottlenecks (items with the most `blocks` edges), plate-load (how much is on the user vs the system vs others). These are *lenses with a temporal/aggregate grouping* — not a new store, queries over the same graph + the tracker's event history (which already records the state transitions analytics needs). Deliberately a LATE increment (low confidence on which analytics a non-tech user actually wants; ship after the lenses prove the model). Named as Decision **WMS-D6**.

### 4e. Tracking / surfacing — planned vs done vs next

The per-turn surface, the heart of the status-anxiety fix. **REUSES Slice D + Slice E wholesale** (Lens 1): the keep-pace turn-contributor that renders the active lens, char-capped, TTL-cached, fail-soft, plain-language (zero-internal-vocab invariant from work_visibility). The surface answers, in plain English, *planned* (queued items), *done* (recently-terminal items — the "what got finished" the user never sees behind the abstraction), and *next* (the top of the on-my-plate sort). This is the literal "remember what was planned / what's done" the owner named as the core gap.

---

## §5 The FBM boundary (L0 ↔ L1) — compose, don't duplicate (Lens 1)

**The boundary, stated precisely:**

| Concern | OWNED BY | The work system does NOT |
|---|---|---|
| Ground-truth project build/sealed/merged STATE | **FBM** (`derive_project_state`, Slice C) | re-derive STATE; it calls the FBM engine |
| Per-turn STATE surfacing discipline (TTL, char-cap, fail-soft renderer) | **FBM/keep-pace** (Slice D) | re-implement a surfacer; its lens render reuses Slice D |
| Fact recall (what was decided, what a thing is) | **FBM** (memory store) | store facts; it stores work items + edges |
| Multi-source read-only snapshot + plain render + vocab invariant | **FBM/keep-pace** (Slice E) | re-implement aggregation; the plate/waiting-on lenses extend the snapshot |
| **Work items as first-class entities (state, priority, relations, provenance)** | **WORK SYSTEM** (L1) | — FBM has no work-item entity, no edges, no priority |
| **Lenses (views over work)** | **WORK SYSTEM** (L3) | — |
| **Intake / prioritization / analytics / the relational graph** | **WORK SYSTEM** (L2) | — |

**The clean statement of the relationship:** *FBM FEEDS the work system accurate project STATE + recall; the work system composes ON it and does MORE — it models the work itself, its relations, its priority, and its lenses.* FBM answers "what is the build-state of project X" and "what was decided about Y." The work system answers "what work exists, how does it connect, what's next, and which lens fits this user." Where they meet: a project-lens work item bound to an FBM-registered repo gets its STATE *from* FBM, live, never stored. That single binding is the entire seam.

**The honest gap (F2 — same as work-streams plan §10 #2):** FBM today registers only `loam` + `cairn`. Money / LitRPG / Personal-Home work items have no ground-truth STATE derivation. The work system handles this by marking those items "no ground-truth project bound" and deriving next-action from cadence/staleness — never faking a build-STATE. Registering litrpg-writer + a money surface as FBM projects is a named FBM follow-on (out of scope here), and is the path that upgrades those lenses from cadence-based to STATE-derived.

---

## §6 The non-tech-user surface — meeting them where they are

Composes the abstraction-first translation layer (`feedback_abstraction_first_default.md`), keep-pace surfacing, and the #34 lens-choice:

1. **Intake is conversation, not a form.** The user never sees a tracker, an ID, a state enum. They say what they want; loam places it and confirms in plain language (§4a). This is the prime-directive operating loop applied to work capture.
2. **The right lens, surfaced per-turn, per-user.** #34 chooses the lens that fits this person; the persona surfaces it as one concise plain-language block (Slice D discipline). A projects-thinker never has to learn "streams"; a goals-thinker sees their objectives and the work under them.
3. **Plain-language tracking — planned vs done vs next (§4e).** The non-tech user finally *sees* what got finished behind the abstraction, what's waiting on them, and what's next — the status-anxiety fix (#37), now over the full work graph instead of just loam's build-state.
4. **The zero-internal-vocab HARD invariant** (work_visibility precedent) carries through every render: no SHAs, IDs, paths, enums ever reach the surface. The outbound-guard hooks (`translation_jargon_check.py`, the internal-ID leak guard #43) enforce it structurally.
5. **Self-recovery composes (#31).** A lost user's distress dials the lens to the simplest (on-my-plate, one thing) and the exposure down — the #34 asymmetric-fast-down rule, applied to work surfacing.

---

## §7 The increment roadmap

Each increment is independently shippable, each is a future build-plan derived from this doc, each has a tighter AC than "work management system" (Lens 5 decomposition). Ordered by dependency + confidence (Lens 4: high-confidence foundation first, low-confidence analytics last).

| # | Increment | Delivers | Depends on | Confidence | Build-plan |
|---|---|---|---|---|---|
| **1** | **work-streams lens** (the stream view + FBM-STATE-derived per-turn surfacing + deep-dive/pause) | The first lens, proving the surfacing path end-to-end on the live FBM STATE. | Slices C/D/E (built) | HIGH | `docs/plans/work-streams-fbm-derived-tracks.md` (exists; needs §8 adjustment) |
| **2** | **the unified work model (L1)** + **projects lens** | Extend objective_tracker to the §2a work-item schema (relations, provenance, project-binding); projects lens over it; streams re-pointed at it. | Increment 1 (validates the surfacing); objective_tracker | HIGH (schema) / MED (migration) | future |
| **3** | **intake** (LLM conversational capture → work item + verify-and-place) | Natural-language work capture; provenance; the verify-before-build confirm. | Increment 2 (a model to intake INTO); task #56 LLM seam | MED | BUILT (sealed-local on `build/wms-increment-3`, seal `d8d10c7`): `docs/plans/wms-increment-3-intake-conversational-work-capture.md` — a `primary-persona` keep-pace `intake.py` turn contributor; LIGHT-default propose-and-confirm (create in `proposed`, promote on confirm), per-user via #34 `work-tracking`/`intake-aggressiveness`; composes the #56 spawn-isolation MECHANISM (work-shaped extractor) + the increment-2 store create/transition API (consumed, not modified); conservative dedup; `origin: conversation` provenance. WMS-D4 confirmed light-default. D-INTK.3 dedup-suppress + D-INTK.4 fail-soft-to-silence are the realised shape. |
| **4** | **prioritization + the relational web** | Derived priority; blocks/waits-on edges; graph self-heal against FBM STATE (deviation → #71). | Increment 2 + #71 | MED | future |
| **5** | **goals lens + on-my-plate + waiting-on lenses** | The remaining lenses; OBJECTIVES.md becomes the goals-lens index over the work graph. | Increment 2; OBJECTIVES.md (exists) | MED | future |
| **6** | **per-user lens choice (L4 wiring)** | #34 chooses + surfaces the per-user-preferred lens; intake aggressiveness per-user. | Increments 1–5; interaction-model (#34 built) | MED | future |
| **7** | **analytics** | Throughput / aging / bottleneck / plate-load views over the graph + event history. | Increment 2 (the graph + events) | LOW (which analytics a non-tech user wants is unverified) | future |

**The dependency spine:** Increment 1 ships the surfacing path on the EXISTING separate stream-register (cheapest proof). Increment 2 builds the unified L1 model and *re-points* the streams lens at it — this is where the foundation lands. Everything 3–7 builds on L1. Analytics is deliberately last (lowest confidence + needs the most data).

---

## §8 Increment-1 (work-streams) — the adjustment it needs to fit the unified model

**The work-streams plan is sound and ships first — but it makes ONE choice that would box the unified model in if shipped unqualified.** F2, named explicitly:

- **The plan stores streams in a NEW user-scope register `~/.claude/WORK-STREAMS.md` (Decision D2) with the stream's project-bindings + attention-state as a `WorkStream` dataclass** — i.e. it makes the *stream* a lightly-first-class thing with its own store, parallel to OBJECTIVES.md. Under the unified model, a stream is a VIEW (a tag) over work items, not a store of bindings.

**The adjustment (small, and the plan already half-anticipates it):** the `WORK-STREAMS.md` register should be authored as a **lens-definition surface** (a named filter+grouping over the work graph: "the streams lens groups items tagged `money`/`litrpg`/`loam`/… and binds each group to these FBM projects"), NOT as a parallel work store. Concretely:
- The stream's `attention` state (active/deep-dive/paused) and `nest-under` are **lens-presentation config** — they legitimately live in the register (they describe the VIEW, not the work). Keep them.
- The stream's `projects: [...]` binding and any per-stream backlog should resolve to **work items tagged with the stream**, not be a separate list the register owns. In Increment 1 (before L1 exists) this is necessarily a register-local list; the adjustment is to **mark it explicitly as the pre-L1 shim** and add an AC that the binding is *re-pointable* at the work graph in Increment 2 without a register rewrite.

**The one-line instruction to the Increment-1 build:** keep the `WORK-STREAMS.md` register as the streams *lens definition + attention config*, but treat its project-bindings and backlog as a **pre-unified-model shim** explicitly marked for re-pointing at the L1 work graph in Increment 2 — so the foundation is not boxed-in. This is a documentation + one-AC adjustment to the existing plan, not a redesign. It composes with the plan's own §8 halt trigger #2 (don't widen a sealed read-contract) and §10 #4 (the OBJECTIVES-vs-WORK-STREAMS duplication risk the plan already flagged) — the unified model is the resolution to that flagged risk: in Increment 2 both registers become lens-definitions over the one graph, and the duplication dissolves.

Everything else in the work-streams plan (FBM-STATE derivation, Slice D surfacing reuse, deep-dive/pause, the subsume-don't-duplicate block discipline, the three-source import, the deviation→#71 seam) is correct under the unified model and ships unchanged.

---

## §9 Named decisions (with recommendations) — surface to Luke

Every decision carries a recommendation; these are the forks Luke should eyeball before the increment builds derive from this architecture.

**WMS-D1 — Where the work model lives. RECOMMEND: extend `objective_tracker` (the sealed event-sourced store) as the L1 work-item backbone; user-scope registers (`OBJECTIVES.md`, `WORK-STREAMS.md`) become lens-definition + always-loaded index surfaces that point into it.** Why: the tracker already IS a work-item store with lifecycle + parent/child + projection view; this reuses a sealed primitive (Lens 1) instead of a new store. Cost: it elevates objective_tracker from "the persona's task tracker" to "the work-management backbone" — a role-expansion of a sealed component (touch with a manifest, halt if it widens a read-contract).

**WMS-D2 — Computed lenses vs materialized lens-index. RECOMMEND: computed (lenses are live queries over the graph), with a per-turn TTL cache (Slice D discipline) for the surfaced lens.** Add a thin materialized index ONLY if lens-render latency proves a real problem (the work-streams plan §8 halt #4 already names this trigger). The cache is never a source of truth.

**WMS-D3 — Lens choice as a per-user preference. RECOMMEND: add a `work-tracking` area to the #34 interaction-model with a preferred-lens axis; openness-default surfaces the streams lens (broadest), dialing to the user's demonstrated lens preference.** Why: "different users connect with different lenses" (Luke 13511) IS a per-user-tuned-translation problem — #34 is its engine.

**WMS-D4 — Intake aggressiveness. RECOMMEND: per-user (a #34 cell), with the prime-directive F2 over-reach guard — don't make every "do X once" a tracked effort; verify-and-place, scale structure to what the user-model says this person wants.** The default leans light (confirm before tracking), not heavy.

**WMS-D5 — Priority is derived, never hand-stored; the weighting is calibrate-on-use, not imported.** RECOMMEND: compose on the existing `tracker_context` priority-key; add goal-alignment + dependency-position + staleness + explicit-pin signals; tune on real use (Lens 4 — no magic number). User pins always override.

**WMS-D6 — Analytics scope + timing. RECOMMEND: defer to the last increment; ship only after the lenses prove the model and there's event-history to analyze. Which analytics a non-tech user actually wants is unverified — don't build speculatively.**

**WMS-D7 — Increment-1 adjustment (the §8 shim-marking).** RECOMMEND: ship work-streams first with its register marked as the pre-L1 lens-shim (one AC for re-pointability), so the foundation isn't boxed-in. This is the only change to the existing, ratified work-streams plan, and it's documentation + one AC.

**The single first thing to build:** Increment 1 (work-streams) **with the WMS-D7 adjustment**, because it ships the surfacing path on the live FBM STATE with the cheapest possible proof, validates the per-turn lens surface end-to-end, and (with the shim-marking) sets up Increment 2's unified model without rework.

---

## §10 Lens coverage

- **Lens 0 (PRIME DIRECTIVE):** this system IS per-user-tuned translation applied to work — the user brings WHAT work they want; loam owns HOW it's tracked/related/prioritized/surfaced, customized per-user via the lens-choice (#34). Intake is the operating-loop's translation-IN; the verify-and-place confirm is the load-bearing verification step.
- **Lens 1 (Claude-leverage + compose-don't-duplicate):** every layer rides a built primitive — objective_tracker (L1), FBM Slices C/D/E (L0 + surfacing), interaction-model #34 (L4), the task #56 LLM seam (intake), the outbound-guard hooks (vocab invariant). No new engine; L1 EXTENDS a sealed store, the surfacer REUSES Slice D, the snapshot EXTENDS Slice E.
- **Lens 2 (harness + primary-persona value):** reduces the translation burden of "where is all my work / what's next / what's waiting on me" to zero (the status-anxiety fix over the full graph); adds to the persona's toolkit one accurate multi-lensed work model it surfaces + reasons over every turn.
- **Lens 3 (ODD):** the data model + lens + function layers state observable outcomes (a work item exists with these relations; a lens renders this filter+sort; intake produces a placed item); method (tracker extension mechanics, the intake parser, the priority weighting) is the builder's call in each increment plan.
- **Lens 4 (scope↔confidence):** the data-model shape is HIGH-confidence and pinned (it's the foundation); the function internals + increment 3–7 method are LOW-confidence and left as named decisions, not locked; analytics (lowest confidence) is last.
- **Lens 5 (swarming):** decomposed into 7 increments, each with a strictly-tighter AC than the parent; the roadmap is dependency-ordered; the FBM-deviation self-heal IS a judge-against-ground-truth cycle (the #71 tie).
- **Lens 6 (conflict resolution):** the two central conflicts — work-items-first-vs-lens-first (§2b) and the FBM-vs-work-system boundary (§5) — are named with signals (single-source-of-truth, drift, composition cost, sealed-primitive reuse) and resolved, with the increment-1 boxing-in risk surfaced (§8) rather than silently shipped.
- **Lens 7 (ruthless feedback):** the work-items-first compute cost (§2b), the FBM ground-truth gap for unregistered projects (§5), the increment-1 register-as-parallel-store boxing-in risk (§8), and the analytics-speculation risk (WMS-D6) are each named with evidence + an alternative.
