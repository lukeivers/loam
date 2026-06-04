# WMS Increment 5 — the GOALS, ON-MY-PLATE, and WAITING-ON lenses

Per `docs/plans/wms-increment-5-goals-plate-waiting-on-lenses.md` and the parent
architecture `docs/design/work-management-system-architecture.md` (roadmap row 5 — the
remaining lenses; §3 lens definition = filter+grouping+sort+render over the L1 work
graph; the lens table's goals / on-my-plate / waiting-on rows; §5 the FBM boundary; §2a
the `objective-slug?` field marked "increment add"). WMS is a MAJOR sub-component
(owner-elevated TG 13656). SINGLE-component amendment on the SEALED `primary-persona`:
three new keep-pace lens modules + one shared waiting-split helper extracted from
`relational.py`. Stacks on `build/wms-increment-4` (the work-item store + the edge graph +
`prioritize.py` + `relational.py` + the `OBJECTIVES.md` substrate live there + on the
inc-2 ancestor). Composes the increment-2 store + queries, inc-4's `prioritize` ordering +
`aligned_terms_from_objectives` alignment, the `objectives.py` register, and the Slice-D
renderer discipline (Lens-1: compose, don't duplicate). It DERIVES three VIEWS over the
existing graph — it adds NO new store, field, edge, or lifecycle.

The GOALS lens ladders open work over the user's stated objectives. Per active objective
in `OBJECTIVES.md` it surfaces the work advancing it, NAMES any objective with no
advancing work ("nothing is currently moving this goal"), and carries an unattributed-
open-work tail so no item is silently dropped. The ladder is DERIVED via the EXISTING
`aligned_terms_from_objectives` text-match (the projection carries no stored
`objective-slug` field, confirmed) — the lens computes the ladder, it does not read a
binding, and it fabricates no goal→work link the data does not support.

The ON-MY-PLATE lens is the "what should I actually be doing now" view: a flat, priority-
sorted filter of what's actively on the user — active / owner_pending items that are NOT
blocked, NOT waiting on an external party, and NOT deferred — ordered by inc-4's
`prioritize` REUSED wholesale, carrying the same transparent plain-language reason. No
second priority logic; no numeric score reaches the surface.

The WAITING-ON lens formalizes on-me (owner_pending / internal waits) vs on-others
(external-party `waits_on`) as a standalone named view. Increment 4's `relational.py`
already computes this exact split; increment 5 EXTRACTS that split into a shared helper
that BOTH `relational.py` and the new lens call — formalizing the lens WITHOUT a second
implementation (the reconciliation; re-implementing it would be the multi-surface drift
the whole WMS exists to prevent). The extraction is behavior-preserving: `relational.py`'s
rendered block is unchanged (its existing AC.REL.2 surface is the regression fence).

All three lenses ship as on-demand `render_*_block` production entry points and are NOT
registered as `TriggerKind.turn` contributors. Production already wires four always-on
turn blocks (streams / projects / relational / intake); three more would be seven-blocks-
every-turn bloat. These lenses are mostly on-demand / owner-invoked — the persona renders
them when the question is asked ("how's the launch goal doing?", "what's on my plate?",
"what am I waiting on?"). The per-user always-on lens CHOICE is increment 6.

The objective-tracker store is CONSUMED via its existing READ API (query_projection_view /
unblocked_next / waiting_on_other / trace_to_root + the priority/status/parent_id
projection fields), NOT modified — increment 5 is single-component on `primary-persona`.
If the build discovers a needed store-side change — a query the runtime does not expose, a
stored `objective-slug` binding it decides it truly needs rather than deriving, OR any
store MUTATION — it HALTS rather than opening a sealed-store amendment (plan §8 #2). The
five lenses now share the filter+group+sort+render shape; the build KEEPS them as sibling
modules and does NOT introduce a lens-protocol abstraction this cycle (the Lens-1/Lens-4/
Lens-5 call — the lenses differ entirely in their derive bodies; a premature protocol adds
coordination overhead with no tighter AC; the protocol is deferred to a post-increment-6
refactor against five proven concrete lenses — plan §3 D-WMS5.5 / §10 RF #5).

The outcome-altitude AC (AC.WMS5.LIVE.1) exercises the live production entry points against
a REAL store carrying a REAL set of work items (a dependency chain, items laddering to real
objectives, an owner_pending item, an external-party wait) with NO pre-arranged lens /
ladder / ranking state: the goals lens ladders the right work under the right objective AND
names a no-work goal; the on-my-plate lens surfaces the right top item with `prioritize`'s
reason and EXCLUDES the blocked + waiting-on-others items; the waiting-on lens splits on-me
vs on-others — AND the waiting-on result is produced by the SAME shared helper
`relational.py` calls (no duplicated surfacing).

★ Owner product-shape calls surfaced (plan §3): the waiting-on extract-and-wrap vs
ship-no-standalone-lens reconciliation (D-WMS5.3); the on-demand-entry-points vs always-on-
turn-blocks surfacing-budget call (D-WMS5.4); keep-sibling-modules vs refactor-to-a-lens-
protocol-now (D-WMS5.5 — RECOMMEND defer); and what "on my plate" includes by default
(D-WMS5.6 — the genuine product-definition call). The rest (extend-not-new-component,
derive-the-ladder) are autonomous method-calls.

Out of scope (later increments): the per-user lens-CHOICE wiring — which lens surfaces by
default for THIS user (increment 6, #34 interaction-model); analytics — throughput / aging
/ bottleneck / plate-load aggregates (increment 7); the edge-MUTATING relational-graph
self-heal against FBM ground truth (#71); a stored `objective-slug` binding + a unified
lens-protocol refactor (clean later increments if the derived ladder's precision or a sixth
lens justifies them). Increment 5 adds NO store, field, edge, or lifecycle — it is three
derived VIEWS + one behavior-preserving extraction on `primary-persona`.
