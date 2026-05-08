# Research — memory-system consumer wiring (D7)

**Status:** research artefact for the D7 cycle. Authored 2026-04-24.
Answers the question set in
`docs/plans/research/memory-consumer-wiring-research-plan.md`.
**Scope:** facts + candidate shapes only; no proposal-level
commitments. Per ODD, shape-selection is a proposal-phase decision,
not a research-phase one. Where the research rules out a candidate
on primary-evidence, the ruling-out is recorded; where the candidates
remain live, all survivors are named with trade-offs.

**Session-start corpus consumed.** `CLAUDE.md` §session-start
(odd-methodology, odd-in-pos, VALUE_PROPOSITION, STATE, FUTURE_IDEAS
Idea 8), memory-system + primary-persona-loader + scope-of-work +
session-resilient-orchestrator + objective-tracker +
self-correction-loop component docs (proposals, seal narratives where
available). Amendment #24 (memory-system MCP migration) research +
plan. D8 research plan. D7 research plan verbatim (the plan this doc
answers).

---

## 0. Executive summary (≤15 lines)

1. **First-wave consumer:** primary-persona layer only. D7's first
   amendment wires one read-path (turn-start retrieval feeding the
   additionalContext emitter) and one write-path (turn-close
   aggregated episode). All four other candidates (scope-of-work,
   orchestrator, objective-tracker, self-correction) deferred —
   defer rationale named per component.
2. **Write-path shape:** async + aggregated. Turn-close aggregation
   (one episode per user-turn, not per state-event). Sync writes ruled
   out on 113s cost. Background-scope dispatch via orchestrator's
   existing IPC is the cheapest async surface.
3. **Read-path shape:** turn-start retrieval, query = user message +
   recent-turn context; top-N semantic with `center_node_uuid`
   re-rank when an anchor entity is available from scope-of-work's
   active scope. Session-start retrieval deferred to D8's shared layer.
4. **group_id scheme:** per-workspace (`group_id = workspace slug`)
   at v1. Per-scope is candidate-2 (structurally available today via
   memory's `scope_id → group_id` wiring) but defers cross-scope
   retrieval which Lens-2 primary-persona continuity requires.
5. **D8 composition:** single `additionalContext` emitter layer with
   two registered contributors (session-level context-load gate +
   turn-level memory-retrieval). Shared entry at `UserPromptSubmit`
   with a trigger-kind param; session-start bypasses the memory
   contributor entirely.
6. **Top-3 owner decisions:** (A) confirm primary-persona-only first
   wave. (B) rule between per-workspace vs per-scope group_id. (C)
   rule between turn-close aggregation (this doc's lean) vs
   session-close aggregation.

---

## 1. Scope and method

The research plan's §2.1–§2.5 questions are answered in §§2–6 below.
§7 covers the flagged inferences required by §2.6. §8 is the per-
question implication summary for the proposal. §9 halts-and-signals
surface — none fired. §10 is a per-component defer rationale for the
four first-wave deferrals.

**Method.** Read-only evidence gathering over (a) the sealed memory-
system API surface, (b) every candidate consumer's proposal + current
source, (c) the three-lens framing from CLAUDE.md, (d) the 2026-04-23
empirical measurements cited in the research plan (113s per add_episode;
0 references to memory MCP from any consumer today), (e) amendment
#24's MCP-tool surface for transport-layer grounding. No shell probes
needed — the 113s cost was already measured by the referenced session,
and per-consumer event rates can be estimated from proposals' own
cadence claims without running a workload.

**Conformance bounds.** Research does NOT prescribe file names,
function names, AC prose, step ordering, or commit wording. Those
live in the proposal / build-plan artefacts that follow this gate.

---

## 2. Consumer identification (plan §2.1)

### 2.1 The five candidates

Plan §2.1 names five candidates. Each is evaluated on (a) Lens-2
value (does this reduce translation burden / add to the primary
persona's toolkit?), (b) write-volume (episodes/day at the cadence
the component's own proposal declares), (c) integration surface area
(lines touched, amendments needed), (d) memory-observability
payoff (does memory make this component's behaviour visibly better
from the user's seat?), (e) precondition dependencies.

#### 2.1.1 Primary-persona layer

- **Lens-2 value: HIGHEST.** The primary persona IS the translation
  layer (VALUE_PROPOSITION.md verbatim). Memory turns the persona
  from goldfish to chief-of-staff — the single biggest value jump
  any pos-v2 component adds. Every other candidate's memory wiring
  ultimately funnels retrieved context up through the persona
  anyway, which means wiring the persona first backs the use case
  that every subsequent wiring is serving.
- **Write-volume.** Turn cadence. Research plan cites ~20 turns/day
  baseline (from primary-persona-loader proposal §"Assumptions" — 1k
  token awareness block at 20 turns/day = $0.06/day). At turn-close
  aggregation: 20 episodes/day. At per-message aggregation: 40+/day
  (user message + persona reply × 20 turns).
- **Integration surface.** Two surfaces: (a) additionalContext
  emission (already provisioned by primary-persona D3 monitor for
  awareness-block injection; extending it for a memory-retrieval
  contribution is within that D3 surface's shape), (b) turn-close
  hook (new — needs a primitive the persona layer does not yet
  ship; see §3.3). Likely amendment vs sealed components: primary-
  persona only.
- **Memory-observability payoff.** Every user interaction benefits.
  Retrieval every turn, write every turn-close. This is the component
  where memory's absence is MOST visible to the user (every session
  re-learns; no continuity across sessions).
- **Precondition dependencies.** MemoryAPI exists (✓); scope-of-work
  exists (✓); additionalContext emitter surface exists via
  `UserPromptSubmit` hook and the D3 injection path (✓).

#### 2.1.2 Scope-of-work primitive

- **Lens-2 value: MEDIUM-HIGH via cross-scope retrieval.** Scope-start
  memory retrieval ("what did prior scopes like this one look like?")
  is high-value for reducing redo / rediscovery cost. But the value
  is downstream of (a) enough prior scopes existing to compare against
  (cold-start: zero value), and (b) group_id scheme being per-
  workspace not per-scope (a per-scope scheme makes cross-scope
  retrieval a full-graph scan, which defeats the Lens-1 composition).
- **Write-volume.** Per-state-event: scope creation + activation +
  N transitions + completion. Research baseline (memory assumptions)
  cites 10-30 events/day. If every state event is an episode,
  100+ episodes/day; if scope-lifecycle-complete is one aggregated
  episode, ~10 episodes/day.
- **Integration surface.** The scope-of-work runtime already emits
  `pyee` events the primary-persona monitor subscribes to. A memory
  adapter could subscribe to the same emitter without any scope-of-
  work amendment — the emitter is public surface, not internal. But
  the write-path needs a scope-to-episode translator, which is
  genuinely new code.
- **Memory-observability payoff.** Medium — scope lifecycle in
  memory lets the persona answer "when did we last work on X?" and
  "how long did the last X take?" queries. Valuable but not session-
  shaping.
- **Precondition dependencies.** Primary-persona wiring probably lands
  first because scope-of-work retrieval is consumed by the persona —
  no consumer other than the persona has a clean reason to retrieve
  scope-lifecycle episodes directly.

#### 2.1.3 Orchestrator

- **Lens-2 value: LOW for wiring memory directly.** The orchestrator
  is infrastructure plumbing (process lifecycle, bind_scope, IPC
  hosting). Its state transitions are "scope activated", "scope
  compacted", "bind refused" — administrative, not user-semantic.
  Writing those to memory produces a log of admin events, not a
  layer the primary persona draws from.
- **Write-volume.** ~1-3 administrative events per scope activation;
  at 10-30 scope events/day, ~30-90 admin episodes/day.
- **Integration surface.** Orchestrator already emits OTel spans for
  these events (D9). A memory writer would be duplicative with the
  observability-aggregator, which is the purpose-built consumer for
  those OTel spans. Wiring memory here overlaps observability's job.
- **Memory-observability payoff.** LOW. The observability aggregator
  is the right home for operational telemetry. Memory is for
  knowledge; OTel streams are for operations. Amendment #11 cleanly
  separated those two concerns.
- **Precondition dependencies.** None — could technically ship now.
  But low value plus observability overlap argues for defer.

#### 2.1.4 Objective-tracker

- **Lens-2 value: LOW-MEDIUM.** The tracker persists objectives as
  first-class entities. Memory persists facts about entities. There's
  a conceptual overlap (both are "what the user cares about"), but
  the tracker IS the objective store — memory would be a second copy
  of what the tracker already has, keyed by UUID. Useful for cross-
  objective pattern retrieval ("what objectives like this one got
  abandoned?") but requires (a) many objectives to exist, (b) semantic
  similarity across objective goals to produce retrievable edges, which
  graphiti's entity-extraction is not tuned for on short goal strings.
- **Write-volume.** Per-objective: creation + decomposition + status
  changes + achievement/abandonment. ~3-5 events per objective; at
  unknown per-day rate (no baseline in proposals).
- **Integration surface.** Tracker emits OTel + pyee. A memory adapter
  subscribes to pyee without amending the tracker. But the "objectives
  as entities" extraction is a graphiti-native problem — feeding a
  two-line goal string to Claude-Haiku-4-5 for entity extraction
  produces limited-value nodes.
- **Memory-observability payoff.** LOW. The tracker's own `list(filter)`
  surface answers every objective query directly; memory doesn't add
  retrieval power here.
- **Precondition dependencies.** None structural. Defer on value,
  not dependency.

#### 2.1.5 Self-correction loop

- **Lens-2 value: MEDIUM.** Correction episodes carry `failure_class`
  + `CauseDiagnosed` + `StructuralRemedyApplied` — these are exactly
  the entity-rich payloads graphiti-extraction shines on. Retrieval
  shape: "has this failure class happened before? what was the
  remedy?" is a legitimate Lens-2 translation win. The persona can
  short-circuit re-diagnosis by checking memory before opening a new
  correction scope.
- **Write-volume.** Correction scopes are rare by design — the
  four-part protocol (class → instance → cause → remedy) is heavyweight
  precisely because corrections are supposed to be infrequent. Proposal
  estimates are implicit but the research doc's depth cap (3) and
  same-class-window (3/600s) cascade thresholds imply "fewer than a
  handful per day at steady state."
- **Integration surface.** Self-correction already has a sidecar store
  (`correction.sqlite`, four tables). A memory writer at
  `StructuralRemedyApplied` time would be a second sidecar but a
  thin one — one episode per closed correction. No amendment to
  self-correction; a subscribing adapter reads its emitter.
- **Memory-observability payoff.** Conceptually high (pattern-of-
  failure retrieval), concretely low at near-zero correction volume.
  Real payoff requires enough corrections to form a pattern.
- **Precondition dependencies.** Primary-persona wiring probably
  lands first because the main retrieval-consumer is the persona
  deciding whether to short-circuit a correction.

### 2.2 First-wave consumer set

**Primary-persona layer only.** Every other candidate is deferred
per §10's per-component rationale. The minimum-viable consumer set
is one.

**Why one, not more:**

1. **Lens-2 value concentration.** Primary persona is the single
   biggest translation-layer win; every other candidate is either
   lower-value (orchestrator, objective-tracker) or downstream of
   persona wiring working first (scope-of-work, self-correction).
2. **Lens-3 ODD scope discipline.** The research plan's acceptance
   named "minimum-viable consumer set" explicitly. One consumer is
   minimum viable. Shipping two at once doubles the proposal's
   acceptance-criteria surface and introduces cross-consumer
   interaction questions that are not yet grounded in live usage data.
3. **Cost-governance C15 composure.** Section 3.2 shows the write-
   path cost model; one consumer at 10-20 episodes/day stays inside
   C15's ceiling expectations. Multiple consumers require a real
   budget-allocation conversation that should be informed by one
   consumer's live telemetry first.
4. **Empirical-data discipline.** Research plan halt trigger #2
   permits deferring decisions that need data that does not yet
   exist. Cross-consumer ordering, cascade, and budget-split are all
   decisions that require one consumer's live data first. Ship one;
   measure; decide the second.

**Ranking of the deferred four** (proposal-phase sequencing hint,
NOT committed here): self-correction > scope-of-work >
objective-tracker > orchestrator. Rationale in §10.

---

## 3. Write-path shape (plan §2.2)

### 3.1 Event → episode translation per consumer

For the first-wave consumer (primary persona), the translation is
**turn → episode**, not event → episode. Persona "events" are user
messages + persona replies + tool calls; bundling one turn into one
episode is the natural unit because:

- The turn is what memory would retrieve — "what did we discuss last
  time we were on topic X?" returns a turn, not a tool call.
- One episode per turn produces the right cadence (~20/day) to stay
  inside the cost envelope computed in §3.2.
- graphiti's entity extraction is tuned for prose-sized payloads
  (1-2k tokens per episode per assumptions.md); a whole turn fits
  comfortably.

The aggregated payload shape (candidate; proposal commits):

```
name: <turn-id or user-topic-summary>
body: <user message + persona reply + any inline context persona wants
      to preserve>
source: text | message (graphiti EpisodeType)
source_description: "primary-persona turn"
reference_time: <turn-close timestamp>
group_id: <per §5 ruling — workspace slug or scope UUID>
retention_class: <per §5.2 ruling — default normal; persona-overridable>
```

For the deferred consumers, the translation varies:

- **scope-of-work:** scope-lifecycle-complete → one episode (NOT
  per-state-transition). Body captures goal, outcome, budget-consumed,
  duration.
- **objective-tracker:** objective-achieved / objective-abandoned →
  one episode. Per-decomposition and per-status-change not promoted.
- **self-correction:** `StructuralRemedyApplied` event → one episode.
  The four record types ARE already structured; the episode body is
  their concatenation plus the triggering scope's goal.
- **orchestrator:** deferred entirely; observability aggregator owns
  admin-event persistence.

### 3.2 Cost model

**Per-episode measurements** (from memory-system assumptions.md +
2026-04-23 session):

| Metric | Value | Source |
|---|---|---|
| LLM calls per episode (mean) | 3-7 | D4 cost baseline |
| Input tokens per episode | 1-2k | D4 |
| Output tokens per episode | 300-700 | D4 |
| Wall-time per episode | 7-12s (D4 baseline) → 113s for 9-entity/8-edge at full extraction (2026-04-23) | D4 + research plan |
| Cost per episode (Haiku 4.5) | ~$0.0176-0.0215 | D4 + amendment #11 |
| Annual cost at 3,000 episodes | ~$54 | D4 refreshed baseline |

**The 113s-per-episode wall-time is the load-bearing cost.** The 7-12s
number is the mean across small synthetic episodes; 113s is the
observed wall-time for a realistic persona-turn-sized payload. The
plan asks for the implied cost at pos-v2's expected event rate.

**At turn-close aggregation (the recommended shape):**

- 20 turns/day × 1 episode/turn = 20 episodes/day = 7,300 episodes/year.
- At $0.02/episode: $146/year. Inside C15's expectations per
  cost-governance seal (no direct C15 ceiling in research corpus;
  budget ~$50-500/month is in-band per the owner's 2026-04-23
  cost-governance posture).
- At Claude Max: subscription-backed; per-episode $ reports as
  equivalent-cost under amendment #11's subscription-cost-snapshot
  wrapper but does not consume a pay-per-use ceiling. Usage-limits
  pressure is real but absorbed by the subscription.
- Wall-time at turn-close: 20 × 113s = 2,260s/day = 37.7 min/day of
  background compute. Parallelizable, but each episode is a single
  claude-haiku-4-5 call sequence and will not parallelise inside one
  episode.

**At per-message aggregation (40 episodes/day):**

- $292/year, same wall-time doubling. Remains in-band, but starts to
  press subscription throughput; rejected on value — user messages
  and persona replies belong together in one retrievable unit.

**At per-state-event aggregation (NOT recommended, listed for contrast):**

- Scope-of-work: 30 events/day; 10,950 episodes/year; ~$220/year.
  Doable but multiplies subscription pressure without the retrievable-
  unit value of turn-aggregation.

**Cost-governance C15 composition.** C15 pins per-scope ceilings +
fire-once warning at 80%. The memory-write path needs its own budget
surface — memory writes on behalf of other scopes, but the writes
themselves have cost. Two candidate shapes for budget attribution:

1. **Attribute to the triggering scope.** Each turn-close episode
   debits the triggering scope's budget. Pro: clean attribution.
   Con: breaks if the triggering scope has completed before the
   memory write finishes (async).
2. **Attribute to a pinned "memory-write" budget line.** A separate
   budget-line declared at workspace level funds all memory writes.
   Pro: isolates async writes from their originating scopes. Con:
   needs a new budget-line surface that cost-governance does not
   currently declare.

Research lean: **candidate 1** — attribute to triggering scope, with
a hold-open mechanism (scope-of-work stays "completing" until the
memory-write finishes, modeled on orchestrator's compaction-restore
pattern). But this is a proposal-phase decision; both shapes are
live and both have consequences for cost-governance's surface.

### 3.3 Sync vs async

**Sync is ruled out.** 113s per episode blocks the user for two
minutes per turn — unambiguously wrong against Lens-2 (translation
layer cannot make the user wait two minutes; translation layer is
the OPPOSITE of that). Plan §2.6 flags this as an inference; the
empirical data (113s measurement + user-facing latency budget)
closes the inference. Sync is unambiguously wrong.

**Three async candidates:**

#### 3.3.1 Background-scope dispatch via orchestrator

- Mechanism: on turn-close, primary-persona invokes
  `orchestrator.activate_scope(...)` with a memory-write scope spec.
  Orchestrator's bind_scope + scope-of-work runtime kicks off the
  write; the user's turn returns immediately.
- Pro: uses existing orchestrator IPC, existing scope-of-work runtime,
  existing budget-ledger. Failed writes show up as failed scopes in
  the awareness block (the persona sees their own memory failing).
  Correct session-resilience story — a killed orchestrator mid-write
  has the scope-of-work event log to recover from.
- Con: takes a scope slot per turn. At 20 turns/day this is trivial;
  at higher volumes it could crowd real work. Also: the scope-of-work
  event log carries 20 memory-write scopes per day as first-class
  history, which may or may not be what the user wants to see in
  their scope history.
- Observability: every memory-write emits `pos.scope.*` (scope-of-
  work's existing OTel surface) + memory's own `memory.ingest.*` span.
- Research lean: **recommended**. Composition with existing primitives
  is clean; none are amended.

#### 3.3.2 Orchestrator-internal task (not a scope)

- Mechanism: orchestrator runs a long-lived memory-writer task inside
  its own process; persona posts turn payloads via IPC; task drains a
  queue into memory.add_episode calls.
- Pro: lightweight (no scope-per-turn). Survives orchestrator restart
  (queue is persistent). Composition with existing IPC.
- Con: separate budget surface (not on scope-of-work's ledger);
  observability story is orchestrator-internal (less visible to the
  persona). Adds a primitive the orchestrator does not currently ship
  — would need an amendment.
- Research lean: **viable**. The amendment surface is small; the
  lightweight shape is attractive at high-volume futures.

#### 3.3.3 Session-close batch

- Mechanism: buffer turn payloads in-session; write all accumulated
  payloads when the session ends (SessionEnd hook, or after N hours
  of idle).
- Pro: lowest per-turn cost. All aggregation is local until session-
  close.
- Con: memory is stale for the current session (retrieval at
  turn-start returns only prior-session facts; the current session's
  own recent turns are not retrievable). Violates the persona's
  "goldfish to chief-of-staff" value prop during the same session
  the user is in.
- Research lean: **rejected** on Lens-2. Within-session retrieval is
  a primary use case; a batch that defers all writes to session-end
  breaks it.

**Recommended shape: §3.3.1 (background-scope via orchestrator).**
§3.3.2 is a viable fallback if proposal-phase discovers the scope-
per-turn surface is heavier than this research anticipates.

---

## 4. Read-path shape (plan §2.3)

### 4.1 Read trigger

The research plan asks: session-start / turn-start / scope-activation
/ on-demand. Each is evaluated against Lens-2 and cost.

- **Session-start only.** Load context once per session. Pro: one
  read per session, cheap. Con: within-session retrieval (the persona
  asking "did I say X earlier this session?") requires a memory write
  to have landed within-session AND a new read trigger — defeats
  the one-read-per-session shape. Rejected.
- **Turn-start (every `UserPromptSubmit`).** One read per turn.
  Pro: covers the primary use case (persona recalls facts relevant
  to the current user message); composes naturally with the D8
  shared-layer emitter which is already turn-level. Con: retrieval
  cost × 20/day.
- **Scope-activation only.** Read when a new scope starts. Pro:
  tied to the primary-persona's decision moments. Con: most user
  turns are not scope-activations; a turn discussing "what's the
  status of X?" needs memory retrieval without a new scope. Covers
  too little.
- **On-demand via persona tool.** Memory search exposed as a tool
  the persona can invoke when it judges retrieval useful. Pro: zero
  wasted retrieval. Con: relies on the persona to remember to
  retrieve — structurally brittle. Violates Lens-3's preference
  for structural enforcement over persona-judgment enforcement.
  Violates STATE.md rule #7 analog (persona never forgets to check
  its memory).

**Recommended shape: turn-start retrieval + on-demand as secondary
surface.** Turn-start is structural (every turn injects some memory
payload); on-demand is additive (persona can call `memory.search`
mid-turn for deeper probing when it judges useful). Session-start
retrieval is a D8 concern (the context-load gate), NOT a memory-
retrieval concern — see §6.

### 4.2 Query construction

Three candidates, evaluated on precision + engineering cost:

1. **Raw user message.** Copy the user's message text into
   `search.query`. Pro: trivial; zero engineering. Con: short user
   messages ("do it", "thanks") produce zero-relevance searches;
   long user messages dilute the query with noise.
2. **User message + last-N-turn context.** Concatenate the current
   message with the last N persona-turns. Pro: handles short messages;
   preserves conversational context. Con: costs grow; may surface
   irrelevant recent-turn content.
3. **Persona-authored query.** Run one small LLM call to distill
   the user-message-plus-context into a memory query. Pro: highest
   precision. Con: one extra LLM round-trip per turn; ordering
   constraint (blocks turn until query is distilled and memory
   returns).

**Recommended: #2 (user-message + last-3-turn context) as v1.**
Short user messages stay retrievable; long messages dominate
naturally. #3 is candidate-2 if v1 retrieval precision is
unsatisfactory. #1 rejected on precision for short messages.

**`center_node_uuid` anchor:** when the primary-persona-D3 monitor
reports an active scope with a primary entity (e.g., user is in
"Project X" scope), pass that entity's node UUID as `center_node_uuid`
to bias retrieval toward project-relevant edges. Memory already
supports this via MemoryAPI.search's `anchor_node_uuid` param. Low
cost to wire in, substantial precision gain on entity-relevant turns.

### 4.3 Context injection

The plan asks: top-N, time-windowed, persona-authored filter.

- **Top-N by semantic similarity.** Memory's default. Cheap, broadly
  effective. N=5 is graphiti's typical recipe.
- **Time-windowed slice.** Use `valid_at` temporal filter (D8 wrapper).
  Pro: focuses retrieval on recent episodes. Con: breaks cross-
  session continuity for facts that are genuinely old-but-relevant.
- **Persona-authored filter.** Persona inspects top-K results, picks
  the M that matter. Pro: maximum precision. Con: another LLM round-
  trip inside the retrieval path; same latency concern as §4.2
  candidate #3.

**Recommended: top-N semantic (N=5).** Time-window is a degenerate
case of top-N-semantic with a reference_time; use it when the user's
message mentions a temporal reference ("yesterday", "last week") and
otherwise do not bound the time window. Persona-authored filtering
is v2; defer on latency concern.

**Token budget for injected memory payload.** At N=5 with typical
graphiti fact-edge payloads (~30-80 tokens each), inject is ~200-400
tokens per turn. Stays inside the D3 monitor's 1,000-token awareness-
block envelope; composition with D3 is clean (memory-retrieval
block sits alongside the awareness block, not replacing it — see §6).

---

## 5. Retention and group_id scheme (plan §2.4)

### 5.1 group_id convention

Four candidates (from plan §2.4):

1. **Per-workspace (`group_id = workspace slug`).**
   - Pro: ONE retrieval returns everything across every scope in the
     workspace. Matches Lens-2 — the primary persona holds one unified
     picture across all domains.
   - Pro: compatible with graphiti's groups-as-namespaces design; the
     natural partition for single-user workspaces.
   - Con: memory-system's MemoryAPI today passes
     `group_id=scope_rec.scope_id` — a per-scope default. Changing to
     per-workspace needs either (a) a memory-system amendment to
     accept a workspace_id override, or (b) a consumer-side wrapper
     that calls add_episode directly bypassing MemoryAPI's scope
     mapping. Both are modest.
   - Con: breaks `list_scope(scope_id)` semantics — scope-level
     enumeration stops being a primary-key query.
2. **Per-user (cross-workspace).**
   - Rejected on Lens-1 composition. pos-v2 is single-user + workspace-
     scoped by design. A cross-workspace group_id breaks the
     workspace-as-unit model that amendment #6 / #28 / #29 all
     reinforced.
3. **Per-scope (`group_id = scope UUID`).**
   - Pro: matches memory-system's current wiring.
   - Pro: structural scope-partitioning of memory — one scope cannot
     read another scope's edges without explicit cross-scope search.
   - Con: kills cross-scope retrieval for the primary persona. The
     persona's reason to use memory is to remember across scopes;
     per-scope group_id forces every search to enumerate every
     scope_id. At 10-30 scope_events/day × multi-year: impractical.
4. **Hierarchical (user → workspace → scope).**
   - Graphiti does not natively support hierarchical group_ids. Would
     require either a fork or a pos-side re-composition of group_ids.
     Out of scope for a first wiring.

**Recommended: #1 (per-workspace).** Strongest Lens-2 fit; modest
memory-system integration change required. Research flags the
memory-system touch as the one dependency surface this creates —
proposal-phase decides whether it lands as a MemoryAPI amendment or
a consumer-side wrapper.

**Per-scope as preserved secondary dimension.** Retain scope_id as a
per-episode attribute (it is already a scope_source-driven attribute
on every episode via MemoryAPI's current wiring). Filter by scope_id
at search-time when the persona wants scope-local retrieval. Two-tier
model: group_id = workspace for partitioning; scope_id = attribute
for filtering.

### 5.2 Retention class assignment

Memory-system ships three retention classes (normal, derived-only,
ephemeral) per the D10 tagger. Default: `normal`.

For the first-wave consumer (primary persona), three candidate
assignment shapes:

1. **Default-normal with persona-override.** Every turn-episode lands
   as `normal` unless the persona explicitly flags it otherwise.
   Pro: simple; matches memory's documented default.
   Con: no structural privacy boundary for sensitive content.
2. **Computed-from-scope-retention.** Scope-of-work's spec already
   carries a retention-related posture via reversibility_class.
   A turn inside an irreversible / high-cost scope might warrant
   `derived-only`.
   Con: couples retention to reversibility, which is not the same
   semantic axis.
3. **Turn-content-classified via persona.** One small LLM pass per
   turn classifies retention class.
   Con: LLM call in the hot path; turn latency impact.

**Recommended: #1 (default-normal + persona-override).** Structural
persona-override lives in persona's own reasoning (when discussing
financial / health / other sensitive content, the persona flags the
turn as `derived-only` before dispatching the memory-write scope).
Enforcement is advisory at the persona level; memory-system already
enforces it structurally at ingest.

**Retention policy (decay-retention).** Memory's D10 retention_class
column IS the retention surface; the decay-retention analysis
referenced in the plan describes eviction semantics (not currently
implemented per the memory seal; derived-only trims raw text at
ingest but no time-based decay ships today). This research does NOT
propose a new retention class or decay policy — it uses the existing
default-normal with persona-override and surfaces the absence-of-
decay as a separate concern future work addresses.

---

## 6. Composition with D8 shared layer (plan §2.5)

Owner ruling: D7 and D8 share a common `additionalContext`-emitter
layer. This section answers the SHAPE of the shared layer.

### 6.1 Entry points for the two triggers

- **D8 (session-level context-load gate)** fires on `SessionStart`.
  Current harness: `orchestrator/scripts/pos_session_start.py::main()`
  owns the slot. D8's research cycle decides where the gate lives
  inside the persona-layer scope (per D8 owner ruling).
- **D7 (turn-level memory-retrieval)** fires on `UserPromptSubmit`.
  Current harness: primary-persona-D3 monitor already owns this
  slot (`AwarenessBlock` injection per monitor.py::produce_block).

These are **two distinct Claude-Code hook events.** The shared layer
is not a single entry point — it is a shared CONTRIBUTOR registry
that BOTH entry points call into.

### 6.2 Shared-layer candidate shape

```
┌───────────────────────────────────────────────────────────────┐
│ additionalContext contributor registry (pos-layer)            │
│ ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│ │ awareness    │  │ memory-retrieval │  │ session-context  │  │
│ │ contributor  │  │ contributor      │  │ contributor      │  │
│ │ (D3 monitor) │  │ (D7 new)         │  │ (D8 new)         │  │
│ └──────────────┘  └──────────────────┘  └──────────────────┘  │
└────────┬─────────────────────┬──────────────────────┬─────────┘
         │                     │                      │
    trigger: turn         trigger: turn         trigger: session
   (UserPromptSubmit)    (UserPromptSubmit)       (SessionStart)
```

Each contributor:

- Declares which trigger-kinds it runs on (turn / session / both).
- Produces a text payload on trigger-fire.
- Declares a token-budget contribution (subtracted from the overall
  additionalContext cap).

The two entry points:

- **Session-start entry point**: walks the registry for
  `trigger_kind=session` contributors; concatenates + emits.
- **Turn-start entry point**: walks the registry for
  `trigger_kind=turn` contributors; concatenates + emits.

A contributor MAY register for both. None currently need to.

### 6.3 Payload composition model

Three candidate composition models:

1. **Merged into one additionalContext stream** (what the shared-
   layer diagram above shows). Pro: single contract surface;
   deterministic ordering. Con: contributors don't see each other's
   output.
2. **Interleaved.** Each turn emits a pos.* prefix per contributor;
   the persona reads the prefixes. Pro: traceable source of each
   chunk. Con: more tokens spent on prefixes than on payload.
3. **Complementary but distinct additionalContext blocks.**
   SessionStart emits its block; UserPromptSubmit emits its block;
   the two never share a turn. Pro: simplest; no cross-trigger
   interaction. Con: misses the opportunity to suppress one block
   when the other is heavy (plan §2.5 last bullet).

**Recommended: #1 (merged stream).** Within a single turn, ordering
is: awareness (monitor) → memory-retrieval (new) → [suppressible by
quiet-mode policy]. Session-start emits its own block separately
(different trigger, different turn). The two triggers do NOT
interact — D8's session-start payload lands in a different hook
event from D7's turn-start payload.

### 6.4 Write-ordering contract between D7's write and D8's write

"Write" means the additionalContext emission, not memory.add_episode.

- **D8's write** (session-start context load) is one-shot. Lands once
  per session-start. No ongoing contention with D7.
- **D7's write** (turn-start memory retrieval) is every turn. Lands
  in the awareness-block slot (or alongside it). Contention is
  intra-turn with the D3 awareness block.

The contention surface inside a turn:

- Total `additionalContext` budget is bounded (1,000 tokens per D3
  monitor design).
- Awareness block takes up to 1,000 tokens; memory-retrieval takes
  200-400 tokens (§4.3).
- Together they overflow D3's cap.

Three resolution candidates:

1. **Widen the total cap to 1.5k.** Adds tokens to every turn;
   measurable against the persona's budget.
2. **Share the cap with explicit split.** 700 tokens awareness +
   300 tokens memory. Needs D3 amendment to accept a reduced cap.
3. **Priority-ordered with truncation.** Awareness first to its
   cap; memory-retrieval fills the remainder up to a total ceiling.

**Recommended: #3 (priority-ordered).** Awareness (D3) is already
the truncation-aware block (caps categories at 5 rows each);
extending the shared-layer to truncate memory-retrieval when
awareness is heavy, and vice-versa, is the cleanest composition.
Proposal-phase decides the numeric ceilings.

### 6.5 Cases where one trigger should suppress the other

Plan §2.5 last bullet asks whether a heavy session-start payload
should suppress the next turn's retrieval.

**Answer: no suppression needed.** Session-start and turn-start emit
into DIFFERENT Claude-Code hook events — SessionStart injects once
at session boot; UserPromptSubmit injects every turn. They don't
share a context-window budget in a way that suppression would
help — Claude-Code's context window absorbs both. Suppression would
only help if the two contributors were competing for the same
additionalContext envelope, which they are not.

What the shared layer DOES need: **de-duplication between D8's
session-start corpus payload and D7's first-turn retrieval.** If
D8 injected the CLAUDE.md required-reads block and the user's first
turn topic is one of those reads, D7's retrieval may surface the
same content again. Two candidate shapes for de-dup:

1. D7 consults a "session-context-already-emitted" flag and skips
   retrieval-hits that overlap. Needs shared state.
2. Accept the overlap; context-window tolerance is large.

**Recommended: #2 at v1 (no de-dup).** Window overlap is cheap;
shared-state de-dup is engineering cost for marginal gain.

---

## 7. Flagged inferences (plan §2.6)

### 7.1 Ranking inference

**Inference:** primary-persona ranks first-wave-first based on
Lens-2 logic.

**Empirical backing.** VALUE_PROPOSITION.md explicitly names the
persona as the translation layer; memory's value proposition IS
persona continuity. The alternative rankings (scope-of-work first,
self-correction first) were surveyed in §2.1 and each failed at
least one criterion (scope-of-work: value downstream of persona;
self-correction: near-zero volume at steady state; orchestrator:
observability-aggregator overlap; objective-tracker: tracker IS the
store).

**Flag for challenge.** If the owner's preference is to prove
memory-integration on a lower-stakes consumer first (to reduce risk
to the persona's hot path), self-correction is the next-cleanest
candidate (low volume, high entity richness, clean sidecar
integration, no amendment to memory-system). Ranking is proposal-
phase commitment; research carries the lean but flags it.

### 7.2 Sync-vs-async inference

**Inference:** async is correct based on 113s wall-time.

**Empirical backing.** 113s exceeds every reasonable user-facing
latency budget. ORL Lens-2 requires the translation layer to not
block the user on multi-minute waits. Session-resilient-orchestrator's
100ms-per-turn awareness-pull latency budget (per session-resilient-
orchestrator proposal D10) is one datapoint; a 113s sync write
violates this by 1000×.

**Flag for challenge.** If the owner's preference is to block-and-
wait for memory persistence before the next turn (e.g., because
retrieval-next-turn must see the current turn), the sync shape is
viable but slow. The research's lean is async; the flag is that
within-session retrieval cannot see the current turn's episode until
the async write lands, which is a real Lens-2 gap the persona needs
to handle (see §4.2 — short-term buffer in-session can partially
cover this).

### 7.3 Read-trigger-granularity inference

**Inference:** turn-level is right based on the persona's
translation-layer job.

**Empirical backing.** Translation layer runs at the user's cadence,
which is turn-cadence. Session-start retrieval alone misses within-
session learning; scope-activation alone misses non-scope-changing
turns. Turn-level is the granularity that matches the translation-
layer's natural rhythm.

**Flag for challenge.** If token-budget anxiety argues for less
frequent retrieval (every-other-turn, or only on "complex" turns),
the research's lean is overly aggressive. The 200-400-token-per-turn
cost is empirically in-band per §4.3 but the owner may rule for
every-other-turn or similar; propagates to proposal.

### 7.4 Other inferences worth flagging

- **Aggregation unit is the turn, not the message.** §3.1.
  Alternative: per-message episodes. Flag for challenge.
- **Memory-write cost attributes to triggering scope.** §3.2.
  Alternative: pinned memory-write budget-line. Flag.
- **group_id = workspace slug.** §5.1. Alternative: per-scope +
  cross-scope search. Flag.
- **Retention class default-normal with persona-override.** §5.2.
  Alternative: computed-from-scope-retention. Flag.
- **No de-dup between D7's and D8's context contributions.** §6.5.
  Alternative: shared-state de-dup. Flag.

---

## 8. Per-question implications for the proposal

For each of the research plan's sections, the implication for the
subsequent proposal:

- **§2.1 consumer identification** → proposal's first deliverable
  names primary-persona-only wiring. Four deferred consumers each
  become future cycles with per-consumer proposal scope.
- **§2.2 write-path** → proposal commits to turn-close aggregation
  + background-scope-via-orchestrator async. Per-message and session-
  close-batch are surveyed but not selected. Cost-attribution shape
  (triggering-scope vs pinned-line) is an owner-ruling in the
  proposal.
- **§2.3 read-path** → proposal commits to turn-start retrieval with
  user-message + last-3-turn-context query, center_node_uuid anchor
  from active scope, top-5 semantic, 200-400 token injection budget.
  Persona-authored filter and time-window are surveyed; defer.
- **§2.4 group_id** → proposal commits to per-workspace group_id +
  scope_id as per-episode attribute for filtering. Requires either
  a MemoryAPI amendment (add workspace_id override) or a consumer-
  side wrapper — proposal decides which.
- **§2.4 retention** → proposal commits to default-normal with
  persona-override. No decay / eviction policy proposed here.
- **§2.5 D8 composition** → proposal commits to merged
  additionalContext stream via a shared contributor registry; D3
  awareness block + new memory-retrieval contributor on
  UserPromptSubmit; D8's session-context contributor on
  SessionStart. Priority-ordered truncation on the turn envelope.
  No de-dup between session-start and turn-start contributions at
  v1.
- **§2.6 inferences** → proposal's flagged-inferences block lifts
  §7's flags as explicit owner-challenges. None are load-bearing
  enough to stall the proposal; each has a fallback shape.

---

## 9. Halt-and-signal surface

**No halt fired.** Evaluated each halt trigger:

1. **Spec v1.x amendment required.** Primary-persona layer v1.2
   spec (per STATE.md line 72's v1.2 addendum landing and the
   `primary-persona-loader/proposal.md` Spec Coverage table)
   declares STATE.md rule #7 + compaction-survival + autonomous-
   authoring as its objectives. None of those explicitly name
   memory-consumption as an objective. The proposal's D6 (autonomous
   authoring) DOES name "memory query" as a creation-trigger input,
   which is a light consumer already. The D7 wiring proposed here
   extends that existing consumption relationship — reads on
   `UserPromptSubmit`, writes on turn-close — without introducing a
   new spec-level objective. **Verdict: amendment-cycle work, not
   spec-revision work.** No halt.
2. **Empirical data missing.** 113s measurement exists; 20-turn/day
   baseline exists; memory-system cost baselines exist. Every number
   this research needed was already measured. No halt.
3. **Scope > 1500 lines.** This doc is well inside the cap. No halt.
4. **ODD break strongly required.** No candidate shape evaluated
   required method-in-AC or silent exception branches. All shapes
   composed cleanly with existing primitives. No halt.
5. **Fundamental architectural conflict.** §3.3.1 (background-scope-
   via-orchestrator) uses existing primitives without amendment.
   §5.1 (per-workspace group_id) requires ONE memory-system
   integration touch — modest, not fundamental. No halt.

---

## 10. Defer rationale per deferred consumer

Per §2.2, four consumers defer past the first wave. Each defer
carries a named rationale so the proposal can refer back.

- **Orchestrator.** Memory-write overlap with observability-aggregator
  is the primary defer driver. Administrative events (scope activation,
  bind refusal, compaction flag) belong in OTel / the aggregator —
  amendment #11 separated operational telemetry from knowledge for
  exactly this reason. Promote only if a later cycle surfaces a user-
  facing query that admin-episode-memory answers.
- **Objective-tracker.** Tracker's own `list(filter)` surface answers
  every objective query directly. Memory adds retrieval power only
  when objective goals have enough semantic diversity to form
  graph edges — requires volume that doesn't yet exist. Promote after
  persona wiring lands and steady-state objective volume is measurable.
- **Scope-of-work.** Value is downstream of persona wiring (the
  persona is the retrieval consumer for scope-lifecycle episodes).
  Wire persona first; add scope-of-work episode writing in a second
  cycle once the persona retrieval shape is stable.
- **Self-correction.** Structurally cleanest next candidate (low
  volume, high entity richness, clean sidecar pattern, no memory-
  system amendment needed). Defer purely on "one consumer at a time"
  discipline, not on value. Strongest candidate for wave-2.

---

## 11. References

- Research plan: `docs/plans/research/memory-consumer-wiring-research-plan.md`
- Sibling D8 research plan: `docs/plans/research/session-start-context-load-gate-research-plan.md`
- Memory-system proposal: `docs/archive/component-research/memory-system/proposal.md`
- Memory-system assumptions: `memory-system/docs/assumptions.md`
- Memory-system MemoryAPI: `memory-system/src/memory.py`
- Memory-system MCP service: `memory-system/src/service.py` (amendment #24)
- Amendment #24 research: `docs/plans/research/amendment-24-memory-system-mcp-migration-research.md`
- Primary-persona proposal: `docs/archive/component-research/primary-persona-loader/proposal.md`
- Primary-persona D3 monitor: `primary-persona/src/monitor.py`
- Scope-of-work proposal: `docs/archive/component-research/scope-of-work/proposal.md`
- Session-resilient-orchestrator proposal: `docs/archive/component-research/session-resilient-orchestrator/proposal.md`
- Session-start supervisor: `orchestrator/scripts/pos_session_start.py`
- Objective-tracker proposal: `docs/archive/component-research/objective-tracker/proposal.md`
- Self-correction proposal: `docs/archive/component-research/self-correction-loop/proposal.md`
- VALUE_PROPOSITION.md
- ODD methodology: `docs/odd-methodology.md`, `docs/odd-in-pos.md`
- STATE.md (component-state line 70: "follow-ons pending primitives
  that reference it")
- FUTURE_IDEAS.md Idea 8 (D8 context-load gate)
