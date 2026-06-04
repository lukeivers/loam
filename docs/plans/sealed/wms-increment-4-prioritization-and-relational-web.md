# WMS Increment 4 — PRIORITIZATION (derived, transparent) + the RELATIONAL WEB (surfaced)

Per `docs/plans/wms-increment-4-prioritization-and-relational-web.md` and the parent
architecture `docs/design/work-management-system-architecture.md` (roadmap item 4 —
prioritization + the relational web; §4b prioritization derived-not-hand-stored; §4c the
relational/contextual web; WMS-D5 priority derived, multi-signal, calibrate-on-use).
Owner-greenlit "build it all the way through" (Luke 13704); WMS elevated to MAJOR
sub-component (13656). SINGLE-component amendment on the SEALED `primary-persona` (two
new keep-pace modules: `prioritize.py` + `relational.py`). Stacks on
`build/wms-increment-3` (the work-item store + the WorkEdge edge graph + the
`unblocked_next`/`waiting_on_other` queries live there + on its inc-2 ancestor). Composes
on the increment-2 store + queries, the `tracker_context` priority-key, the Slice-D
renderer discipline, the `OBJECTIVES.md` ladder, and FBM Slice-C STATE (Lens-1: compose,
don't duplicate). It DERIVES priority over + SURFACES the existing graph — it adds NO new
edge or priority STORAGE.

PRIORITIZATION is a derived, TRANSPARENT, calibrate-on-use ordering. A work item's rank
is COMPUTED from five signals — the existing `tracker_context` open-loop priority-key,
blocking-impact (how much downstream work the item unblocks, read off the existing edge
graph), goal-alignment (does it ladder up to a user-objective in OBJECTIVES.md),
recency/staleness (the existing `last_transition_at` past cadence), and explicit owner
pin/defer as a HARD override above the blend. The blend is TRANSPARENT — every ranked
item carries a PLAIN-LANGUAGE reason naming the dominant signal ("next because the launch
is waiting on it" / "stale two weeks and nothing's blocking it"), never a black-box
numeric score (the Lens-2 non-tech trust value) — and the signal WEIGHTING is
calibrate-on-use (a tunable set, no imported magic number, the same Lens-4 discipline as
#34's thresholds). User pins always override.

The RELATIONAL WEB is SURFACED. Increment 2 built the edge graph + the
`unblocked_next`/`waiting_on_other` runtime queries; increment 4 turns them into the
answers that make the graph valuable, rendered in a per-turn lens: what's unblocked +
ready to do next (the PRIORITIZED unblocked_next output + its reason), what's blocked +
on what (the blocks/waits_on chain in plain language), what's waiting on ME vs on OTHERS
(owner_pending/internal vs external-party waits_on), and the decomposition tree (the
parent/child ladder via trace_to_root). ONE concise capped fail-soft block, the Slice-D
char-cap + TTL + fail-soft discipline — no bloat. Prioritization and the relational web
ship together because each is half of "what should I do next, and why" — prioritization
makes "next" mean the RIGHT next thing; the relational web gives prioritization its
dependency/blocking-impact signal.

The objective-tracker store is CONSUMED via its existing READ API (unblocked_next /
waiting_on_other / query_projection_view / trace_to_root + the priority projection field),
NOT modified — increment 4 is single-component on `primary-persona`. If the build
discovers a needed store-side change — a query the runtime does not expose, a pin field
the store does not carry, OR any edge MUTATION against FBM ground truth (that is the
pending #71 self-heal seam, NOT inc-4) — it HALTS rather than opening a sealed-store
amendment (plan §8 #2). The #71 edge-mutation graph self-heal is explicitly DEFERRED
(plan §3 D-PRI.5 / §10 RF #2): inc-4 READS FBM `derive_project_state` as a priority signal
only (where a project is FBM-bound — loam/cairn today; the four always-available signals
carry every other item). The outcome-altitude AC (AC.WMS4.LIVE.1) exercises the live
production entry points against a REAL store carrying a REAL dependency chain with no
pre-arranged ranking/reason state: the prioritization surfaces the RIGHT unblocked-next
item AND a transparent plain-language reason, through the live derivation + relational-lens
render + the existing unblocked_next query.

★ Owner product-shape calls surfaced (plan §3): the priority SIGNAL SET completeness
(D-PRI.2 — is the five-signal set right; the numeric WEIGHTS are an autonomous
calibratable method-default, NOT an owner constant — the F4 scope↔confidence line) + the
unblocked-next surfacing shape (D-PRI.3 — single-top-plus-short-tail vs a flat dump). The
rest are autonomous method-calls.

Out of scope (later increments): the goals/on-my-plate/waiting-on lenses AS named
per-user-choosable lenses (incr-5 — inc-4 surfaces the relational ANSWERS, not the full
lens-choice set); per-user lens-CHOICE wiring (incr-6); analytics — throughput/aging/
bottleneck/plate-load aggregates (incr-7); the edge-MUTATING relational-graph self-heal
against FBM ground truth (#71). Increment 4 adds NO edge/priority STORAGE, no new
lifecycle, no new store.
