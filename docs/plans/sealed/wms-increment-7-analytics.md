# WMS Increment 7 — ANALYTICS (the LAST increment)

Per `docs/plans/wms-increment-7-analytics.md` and the parent architecture
`docs/design/work-management-system-architecture.md` (roadmap row 7 — analytics, the
explicitly LAST + LOWEST-confidence increment; §4d the analytics function "read-only
aggregate views over the graph ... queries over the same graph + the tracker's event
history, which already records the state transitions analytics needs"; WMS-D6 §9
"defer to the last increment ... which analytics a non-tech user actually wants is
unverified — don't build speculatively"). WMS is a MAJOR sub-component (owner-elevated
TG 13656). This increment CLOSES the 7-increment WMS roadmap. SINGLE-component
amendment on the SEALED `primary-persona`: ONE new keep-pace module `analytics.py`
(three read-only derivations + an on-demand `render_analytics_block`). Stacks on
`build/wms-increment-6` (the work-item store + event log + projection + the lenses +
the inc-5 on-demand render precedent + the shared lens_render.py + the inc-4 transparent
-reason discipline all live there + on the inc-2..inc-5 ancestors). It composes built
primitives read-only (Lens-1: compose, don't duplicate) — the event log, the projection,
the on-demand render shape, the Slice-D cap, the transparent-reason precedent — and adds
NO new store, field, event kind, query, lifecycle, lens, or per-turn block.

★ THE LOAD-BEARING HONESTY (F2 — the architecture flagged analytics as the lowest-
confidence increment). For a single non-tech person tracking their OWN work, MOST of
what "analytics" connotes — throughput counts, velocity trends, cycle-time charts — is
VANITY: it reports numbers that do not change what the user does next (the Lens-2 test,
the WMS prime-objective AC). This increment is scoped HARD to the few insights that DO
change behaviour, and explicitly CUTS the rest. The conservative THREE: (1) WHERE work
is piling up / stalling — which project/stream/goal has accumulated the most open, non-
advancing work (open items grouped + ranked by count + collective staleness off the
projection), telling the user where to point attention next; (2) CHRONICALLY blocked/
waiting items — items in `blocked` status or carrying an external-party `waits_on` edge
past a staleness threshold (off the projection + edge graph), surfacing the thing the
user forgot was waiting on someone; (3) COMPLETION-vs-INTAKE balance — over a recent
window, how many items were captured vs finished (DERIVED OVER THE EVENT LOG's
ObjectiveCreated vs terminal StatusTransitioned events, NOT a snapshot), one honest plain
sentence of whether the user is accumulating faster than they finish. Each ends in an
action; each is one plain sentence; together they are the honest "here's what you might
be losing track of" surface.

The VANITY metrics are explicitly CUT (D-ANL.2): raw throughput-as-a-number, velocity/
burndown, cycle-time-as-a-headline, per-item bottleneck-edge counts (the relational lens
already surfaces blocking where it's actionable), and any chart/time-series. These are
number-theatre for one person — re-adding one needs evidence a real user wants it, not
speculation. Cycle-time survives ONLY as a supporting phrase inside the pile-up insight
("six things sitting, oldest untouched two weeks"), never a headline statistic (D-ANL.5).

Analytics is ON-DEMAND (D-ANL.3 — the architecture mandate). The `render_analytics_block`
is a production entry point rendered when the analytics question is asked, MIRRORING
inc-5's `render_plate_block` / `render_goals_block` — it registers NO `TriggerKind.turn`
contributor. No new always-on per-turn block exists after this increment; the FBM-don't-
bloat composition holds (the right surface when asked, not a wall of metrics every turn).

Analytics derives over the event log + projection READ-ONLY (D-ANL.4 — Lens-1, the load-
bearing fence fact). The event log ALREADY records every state transition with its
timestamp (`EventStore.all_events()` returns the typed stream; `StatusTransitioned`
carries `from_status`/`to_status`/`created_at`; `ObjectiveCreated` carries `created_at`)
— the complete raw material throughput/cycle-time/intake-vs-completion need, which the
current-state projection (holding only `last_transition_at`) cannot reconstruct. Pile-up
+ staleness + blocked-state read the projection (`list` / `query_projection_view` —
`belongs_to_project` / `tagged_streams` / `status` / `last_transition_at` / edges). The
derivations are computed live, never materialized (mirroring WMS-D2). The staleness +
window thresholds are calibrate-on-use method-defaults (D-ANL.6 — the F4 scope↔confidence
line: the SET of insights is the owner-shape call, the numeric thresholds the builder's
calibratable default), and a too-high threshold simply surfaces fewer insights (fail-
quiet, the safe direction for a low-confidence feature).

The objective-tracker store + event log + the inc-2..inc-6 lenses + prioritize.py are
CONSUMED read-only / reuse-only — NOT modified. The switch from CURRENT-state lenses to
a TEMPORAL/aggregate view is the architecture's own framing of analytics (§4d: "lenses
with a temporal/aggregate grouping"). If the build finds it needs a query the runtime
does not expose, a projection field that does not exist, a new event kind, or any store/
event MUTATION, it HALTS rather than opening a sealed-store amendment (plan §8 #2); if
tempted to register an always-on analytics block it HALTS (§8 #3 — analytics is on-
demand); if tempted to add a CUT vanity metric it HALTS (§8 #4 — that needs an owner
ruling); if the live event log turns out not to support an insight's history read-only,
it HALTS and re-scopes or cuts that insight rather than fabricating it or widening the
store (§8 #6 — the data-isn't-there honesty halt).

The outcome-altitude AC (AC.WMS7.LIVE.1) exercises the live `render_analytics_block`
production entry point against a REAL work-item store (an isolated fixture DB) carrying a
REAL transition history — items created at different times, some advanced to done, some
left stalled, some blocked/waiting past the threshold, intake outpacing completion in the
window — with NO pre-arranged analytics/insight state: a correct pile-up insight naming
the genuinely-most-accumulated group with its plain-language reason; a correct stuck
insight naming the chronically-waiting item(s) with what they wait on; a correct
completion-vs-intake sentence derived over the event-log history in the window — all
plain-language, char-capped, zero internal vocabulary, with NO per-turn registration and
NO mocks at the store/event-log boundary.

★ Owner product-shape calls surfaced (plan §3): D-ANL.1 (WHICH insights ship — the
conservative scope cut: RECOMMEND the three that change what the user does next; the
minimal-viable shape is insight 1 alone if you want it even smaller; deferring the whole
increment until a real user asks an analytics question is a defensible call I'd support)
and D-ANL.2 (the vanity metrics are CUT for good, not parked — RECOMMEND cut). The rest
(D-ANL.3 on-demand-not-per-turn, D-ANL.4 derive-over-event-log-read-only, D-ANL.5
cycle-time-as-supporting-phrase, D-ANL.6 calibrate-on-use-thresholds) are autonomous
method-calls the architecture + the inc-4/5 precedents already rule.

Out of scope (CUT vanity metrics + post-roadmap follow-ons): raw throughput-as-a-number /
velocity / burndown / cycle-time-headline / per-item bottleneck-edge count / any chart or
time-series (D-ANL.2 — vanity for a single person); a new always-on per-turn analytics
block (D-ANL.3 — analytics is on-demand); materialized analytics tables in the store
(computed live, WMS-D2); and the named POST-ROADMAP follow-ons that are NOT analytics —
the #71 edge-mutating relational-graph self-heal; widening the #34 seed taxonomy so
work-tracking is a first-class AIM_AREAS area; registering Money/Personal-Home as FBM
projects to upgrade those lenses from cadence- to STATE-derived; the behavioural auto-
learn of the lens choice. Sealing analytics closes the 7-increment WMS roadmap; these
follow-ons remain open as post-roadmap enhancements, not roadmap increments (plan §10
RF #5). Increment 7 adds NO store, field, event kind, query, lifecycle, lens, or per-turn
block — it is one read-only analytics module with an on-demand render on `primary-persona`.
