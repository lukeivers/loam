# Research — swarming × extraction composition design exploration

**Authored:** 2026-05-08.
**Status:** design exploration; informs v0.4.0 / v0.5.x scoping. Pure
design + recommendation. No build dispatch, no runtime code.
**Authority chain:** `CLAUDE.md` Lens 5 (swarming primary spec) ·
`~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_swarming_recursive_decomposition.md`
(full text on the three reference patterns) · `plugins/dev-sdlc/odd-extractor/`
(canonical reverse-ODD pipeline) · `docs/release-roadmap.md`
(v0.4.0 + v0.5.0 entries) · `docs/odd-semver-pinning.md` (each
minor as ODD cycle).

---

## §1 The composition framing

Luke's 2026-05-08 insight, restated: when reverse-ODD runs over a
foreign codebase, the artefacts it emits — `objectives.yaml`,
`backing-map.yaml`, `gap-inventory.yaml`, `build-next.yaml` —
already carry a *partition* of the work. Each objective names a
distinct outcome with its own ACs. Each gap names a missing
capability with its own scope. The same structure that makes the
extracted contract legible to humans also makes it directly
addressable by the Lens 5 PlannerWorkerSwarm runtime: the partition
is already done at extraction time, so the swarm planner doesn't
re-decompose — it dispatches.

The headline consequence — every reverse-ODD pass is implicitly a
work-decomposition pass. v0.4.0 ships single-agent code-gen against
the extracted contract. v0.5.x is the version where that single
agent becomes a swarm: workers claim objectives from the typed
queue, each one running `claude -p` against its named subset of
ACs, the judge reconciles outputs against the same contract that
seeded the dispatch. A 200-objective Web codebase — Luke's
"HOURS on a single agent" example — becomes a wave of bounded
parallel workers with a known stopping criterion (judge says
`is_complete` against the gap inventory) and a known restart
condition (`needs_fresh_start` when accumulated worker output
diverges from the extracted contract).

The doc that follows enumerates how the composition should be
shaped, what the v1 minimum is, and what stays as future work.

---

## §2 Which extraction-stage outputs feed the swarm

Reverse-ODD has four named stages with persisted artefacts (per
`plugins/dev-sdlc/odd-extractor/README.md`): `init` →
`analyze` → `generate` → `verify`. Post-verify the pipeline emits
`objectives.yaml`, `backing-map.yaml`, `gap-inventory.yaml`, and
`build-next.yaml`. Three of those four are candidate inputs for
the swarm planner; one is not.

- **`objectives.yaml` — primary input.** Each objective is a typed
  outcome with its own AC set. It is the natural unit of swarm
  partition: one worker per objective, one judge axis per objective.
  This is the artefact the swarm planner reads first.
- **`backing-map.yaml` — context input.** Maps each objective to
  the source artefacts that backed its extraction (file paths,
  symbol names, evidence rows). Workers receive their objective's
  backing-map slice as part of the dispatch brief; the planner
  does not partition on backing-map — it indexes into it.
- **`gap-inventory.yaml` — primary input.** Each gap names a
  missing capability with a reference to the objective it should
  serve. For build-software runs, gaps are the work. The planner
  partitions over `gap-inventory.yaml` when the swarm's purpose
  is gap-fill (write missing tests, docs, migrations); over
  `objectives.yaml` when the purpose is implement-from-scratch.
- **`build-next.yaml` — sequencing input, not partition input.**
  Build-next is loam's existing recommendation surface — it picks
  ONE candidate gap to address next, with a confidence band and a
  rationale. The swarm composition relaxes the one-candidate
  constraint; build-next becomes a *priority signal* on the swarm
  task queue rather than a single-item filter. High-priority
  build-next candidates claim worker capacity first; low-priority
  candidates run only if budget remains.

The composition's first design choice is therefore: **partition
on `objectives.yaml` for implement-from-scratch swarms, on
`gap-inventory.yaml` for gap-fill swarms; index `backing-map.yaml`
per worker; consume `build-next.yaml` as priority signal on the
queue.** Worker tasks reference back to the objective they serve
via the `objective_id` field that already exists in the extraction
schema.

---

## §3 Decomposition strategies

The plan-doc names three candidate partition strategies. Below each
gets a fuller treatment — what fits, when, and what it costs.

### §3.1 Domain-clustered

Group objectives by feature domain (auth, payments, search) → one
worker per domain. The Ruby/JsTs adapters already implement this
shape at *extraction* time (`slicer.py` Surface #2 partitions the
repo by Rails-idiom domain when the budget envelope is exceeded);
mirroring the strategy at *build* time has the property that
extraction-domain ↔ build-domain alignment is preserved by design.

- **When it fits.** Codebases with strong domain boundaries — auth
  doesn't talk to payments, search doesn't talk to either. Workers
  can be parallelised maximally; cross-worker integration risk is
  low because domains barely touch.
- **When it doesn't.** Cross-cutting concerns — logging,
  observability, RBAC — touch every domain. A domain-clustered
  swarm produces N copies of slightly-different RBAC scaffolding,
  which the aggregator then has to reconcile. The Ruby slicer's
  >50% duplicate-ratio `SliceDriftError` already detects this
  failure mode at extraction time; the build-time analog detects
  it at integration time, when reconciliation is more expensive.
- **Cost.** Low planner cost (domains are usually obvious from
  the backing-map). Moderate aggregator cost (de-duplication of
  cross-cutting code). Worker cost scales linearly with domain
  count.

### §3.2 Dependency-ordered

Extract objective dependencies — "objective X provides capability
that objective Y consumes" — into a DAG; worker phases respect the
topology. The PlannerWorkerSwarm reference already has this primitive:
`PlannerTask.depends_on_titles` resolves to a dependency graph that
the worker queue's `claim()` honours. The composition reuses it.

- **When it fits.** Layered codebases where some objectives are
  load-bearing for others — a database-migration objective must
  finish before a CRUD-handler objective that uses the new schema.
  Dependency-ordered respects the layer; downstream workers find
  the upstream artefact already in place.
- **When it doesn't.** Codebases where dependencies are circular
  or implicit — most ad-hoc business code. Extracting a clean DAG
  from `backing-map.yaml` is itself an LLM-judgment-shaped task.
  Get the dependency wrong and downstream workers fail because
  upstream contracts didn't ship in the order the topology
  promised.
- **Cost.** High planner cost (DAG construction is non-trivial).
  Low aggregator cost (topology constrains worker output to be
  order-consistent). Worker latency scales with critical-path
  length, not worker count — adding parallelism past the critical
  path doesn't help.

### §3.3 Capability-grouped

Group objectives sharing a capability — "all objectives that need
the new auth middleware" → one worker handles them together. This
is the inverse of domain-clustered: domain-clustered groups by
*feature*, capability-grouped groups by *primitive used*.

- **When it fits.** Codebases where the same low-level primitive
  is reused across many features — every form-handler needs the
  same validation library, every API endpoint needs the same
  request-logging middleware. A capability-grouped worker writes
  the primitive once and applies it to every consumer.
- **When it doesn't.** Codebases where capabilities are highly
  diverse — every objective uses a different primitive, so the
  capability-group degenerates to one worker per objective and
  the strategy adds overhead without benefit.
- **Cost.** Moderate planner cost (capability-extraction from
  backing-map is heuristic-shaped). Low aggregator cost (workers
  produce non-overlapping artefacts by construction). Worker cost
  is unbalanced — the worker that owns "the validation library"
  carries far more state than the worker that owns "the rarely-
  used XML serialiser."

### §3.4 Strategy-selection rule of thumb

The three strategies aren't mutually exclusive. The empirically-
observed pattern from the Ruby/JsTs adapters' slice-and-swarm:
domain-clustered partitioning at the outer level, capability-grouped
gap-fill at the inner level, dependency-ordered execution within
each cluster. v1 (per AC.SX.6 below) picks domain-clustered alone;
later versions stack the strategies once empirical data shows
which combinations actually pay off.

---

## §4 Worker scope — what does each worker DO?

Three candidates per the plan-doc. The recommendation here picks
two of three for v1 and defers the third.

- **(a) Implement code for objective(s).** The worker takes the
  objective text + backing-map slice + AC list, dispatches `claude
  -p` with a code-gen prompt, returns a unified diff or a branch.
  This is the primary worker scope. It maps directly to v0.4.0
  AC.V040.1 — "produces working source code that maps every line
  to a named AC."
- **(b) Verify code matches objectives.** The worker takes
  generated code (from a previous worker's output, or from
  pre-existing source) and runs the AC's outcome-altitude test
  against it, returning a pass/fail + evidence. This is the natural
  judge-shape for the swarm — the EVAL_DIMENSIONS named-axis
  judging primitive applied per-objective. Recommended FOR v1
  as the *judge* role, not as an independent worker role; one
  judge instance evaluates all worker outputs against their named
  ACs concurrently rather than each worker self-verifying.
- **(c) Gap-fill — write missing tests / docs / migrations.** The
  worker takes a gap-inventory entry and fills it. Defer for v1.
  Gap-fill is the natural follow-up cycle once implement-then-
  verify produces a generated codebase — the gap inventory of the
  *generated* codebase becomes the input for the next swarm pass.

**v1 recommendation:** workers run scope (a) implement-code;
the judge runs scope (b) verify-code per EVAL_DIMENSIONS; gap-fill
(c) is deferred to v0.5.x or v0.6.x once the implement-then-verify
loop is calibrated.

---

## §5 Coordinator pattern — how the planner reconciles worker outputs

Per Lens 5: the judge is `EVAL_DIMENSIONS` named-axis. Per
§4 above: the judge runs verify-code (scope b). The composition
shape:

1. **One judge instance per cycle, one evaluation per
   objective.** Each objective's AC list is a named axis. The
   judge dispatches one `claude -p` per objective concurrently
   (rate-limited per the workspace's existing budget envelope),
   collects per-axis verdicts, and aggregates.
2. **Aggregate verdict shape.** Mirrors the swarms reference's
   `CycleVerdict`: `is_complete: bool` (all axes pass);
   `overall_quality: int 0-10` (weighted axis score); `gaps:
   List[str]` (named axes that failed plus reason); `needs_fresh_
   start: bool` (drift detector — see §6).
3. **Cross-worker integration via gap-fill cycle.** Workers may
   write code that compiles individually but conflicts when
   integrated — two workers both creating an `auth` middleware
   with different signatures, or two workers patching the same
   schema with incompatible migrations. Integration failures
   surface as gaps in the judge's verdict (axes whose AC was
   "objective X integrates with the existing codebase without
   regression"); gap-fill becomes the next cycle's worker input.
4. **Aggregator output.** Per the Ruby slicer's existing primitive
   — sort by `objective_id` lexicographically, dedupe, write the
   union to a worktree. Existing `SliceDriftError` semantics
   (>50% duplicate-ratio across slices) extend cleanly to the
   build-time aggregator: the same threshold detects the same
   failure mode (cross-cutting concern produced N times) at the
   integration step.

The aggregator is a candidate for software-as-deliverable reuse:
the existing Ruby/JsTs slicer aggregator (Surface #9, #2) ships
production-ready dedup-and-merge logic. The build-time aggregator
extends it with a code-merge step (git-style merge over per-worker
worktrees) but the duplicate-detection contract is identical.

---

## §6 Drift detection — `needs_fresh_start` semantics

Lens 5: drift = restart, not continue. Applied to the swarm-
extraction composition, two distinct drift conditions exist, each
with its own trigger.

- **Extraction-time drift (existing).** Per the Ruby/JsTs
  adapters: `SliceDriftError` raises when >50% of generated ACs
  are duplicates across slices. This stays as-is; it's a
  property of the extraction phase.
- **Build-time drift (new).** The judge's `needs_fresh_start`
  flag fires when one or more of:
  1. **Cross-worker integration failures exceed threshold.**
     ≥30% of objectives have at least one AC failing because
     another worker's output broke its preconditions. (Threshold
     is a v0.5.x calibration question.)
  2. **Worker outputs collectively contradict the contract.**
     Generated code as a whole satisfies <50% of named ACs.
     The contract was wrong, the partition was wrong, or both;
     in either case, restart-from-scratch is cheaper than
     patch-and-continue.
  3. **A worker's `claude -p` output reveals an objective the
     extraction pipeline missed.** The worker says "to satisfy
     AC.X, I also need capability Y, which is not in the
     contract." If multiple workers surface the same out-of-
     contract capability, the contract itself needs re-extension
     and the swarm needs to restart against the updated contract.

Restart-from-scratch granularity is itself a v1 design choice.
Per AC.SX.7 (open question 3): full-swarm restart vs diverged-
subtree restart. Recommendation: v1 ships full-swarm restart
only — simpler, matches the swarms reference exactly. v0.5.x
or later can introduce subtree restart once empirical data
shows full-swarm restart is too expensive in practice.

---

## §7 Smallest viable shape (v1)

The minimum implementation that demonstrates the composition end-
to-end. Tradeoff: simpler = faster to ship; richer = closer to
the full vision. The recommendation here picks simpler
deliberately — once the loop runs, calibration data tells us
where to invest next.

- **Partition strategy.** Domain-clustered (§3.1) only. One
  domain → one worker. Domain extraction reuses the existing
  Ruby/JsTs slicer's domain-partitioning logic (the slicer
  already classifies extraction artefacts by domain;
  build-time uses the same classification as input).
- **Worker scope.** Implement-code (§4 (a)) only. No gap-fill
  worker, no verify-as-worker.
- **Judge.** EVAL_DIMENSIONS one-axis-per-objective (§5).
  Each axis runs the AC's outcome-altitude test against the
  worker's generated diff; aggregate verdict per the
  `CycleVerdict` shape.
- **Drift trigger.** Cross-worker integration failure ≥30%
  (§6 condition 1) only. Conditions 2 + 3 deferred — they
  require LLM-judgment-shaped detectors that are themselves
  v0.5.x research.
- **Restart granularity.** Full-swarm restart only.
- **`max_planner_depth: 1`.** No sub-planners; flat partition.
  Per Lens 5, deeper recursion requires explicit opt-in;
  v1 doesn't justify it.
- **Model selection** (per Lens 5 model-rationale rule):
  - Planner phase: Sonnet — partition strategy is mechanical
    once domain classification is fed in; no synthesis-from-
    scratch.
  - Worker phase: Sonnet — code-gen against a tight per-
    objective scope is application of a known template.
  - Judge phase: Opus — cross-cutting synthesis across N
    worker outputs against the contract; rationale: "Opus —
    cross-cutting synthesis across diverse worker outputs;
    Sonnet produces plausible-looking verdicts that miss
    integration regressions."

That's the v1 build. Concretely it's: one new module
(`swarm.py` under `loam_odd_extractor`) wrapping a
PlannerWorkerSwarm-shaped runtime; one CLI subcommand
(`loam build-next --swarm`) that consumes `objectives.yaml` +
`build-next.yaml` and dispatches the swarm; reuse of the
existing aggregator + drift contracts from
`lang/ruby/slicer.py`. Estimated AI-time: 4-8 hours
(~3000-5000 tool calls), comparable to v0.4.0 AC.V040.1's
single-agent code-gen surface — the swarm wrapping adds
~1-2 hours, not 5-10.

---

## §8 Composition with v0.4.0

v0.4.0's outcome (per `docs/release-roadmap.md` §4): "Loam takes
objectives.yaml + gap-inventory.yaml + build-next.yaml as
planning input and produces working source code that maps every
line to a named AC." Single-agent code-gen.

The swarm-extraction composition extends this in two specific
ways without contradicting it:

1. **The single-agent path stays as the v0.4.0 release-gate.**
   v0.4.0 ships, and on small-to-medium codebases (single
   domain, ≤10 objectives, ≤30 minutes of `claude -p` time) the
   single-agent path is the default. Calibration data from
   v0.4.0's first month of use tells us where the single-agent
   path runs out of gas — the codebase size, objective count,
   or wall-clock-budget point at which a serial pass becomes
   wasteful.
2. **v0.5.x adds the swarm path as the scale answer.** The
   swarm composition is the implement-side response to the
   same scale problem the slice-and-swarm extraction adapters
   solved on the extraction side. Concretely: when
   `objectives.yaml` has ≥N objectives (threshold itself a
   v0.5.x calibration), `loam build-next --swarm` activates
   automatically (or by user opt-in). Below the threshold,
   the v0.4.0 single-agent path runs unchanged.

The v0.5.x cycle's named outcome under odd-semver-pinning becomes:
"Loam builds working code from extracted objectives at scale,
parallelising bounded workers with judge-mediated reconciliation."
That's a single-sentence outcome (§odd-semver-pinning §2);
its ACs are §7's v1 shape ratified into AC form; its constraints
inherit the composition's framing (subscription-only via
`claude -p`; reuses existing aggregator + drift contracts; no
"rebuild" of the slicer surface).

Important: v0.5.0's existing entry in the roadmap is *binary +
docs feeder* (the cold-start case for ProgramBench). The swarm-
extraction composition is a *separate* v0.5.x line — likely
v0.5.1 or v0.5.2 depending on roadmap-rerank outcome — not a
displacement of v0.5.0's binary-feeder objective. Both ship in
the v0.5.x family because both are scale answers to the v0.4.0
single-agent baseline.

---

## §9 Open questions (deferred to future work)

Per AC.SX.7 — design questions the doc explicitly does NOT
resolve. Calibration data from v0.4.0 + the v1 swarm shape is
required before answering any of them.

1. **Coordinator state — file-based vs orchestrator-tracked?**
   The swarms reference uses an in-memory `TaskQueue`. loam's
   existing extraction state is file-based (`state.yaml` per
   extraction-dir). The swarm runtime needs queue + claim +
   verdict state somewhere. File-based fits the existing pattern
   but introduces lock-file contention; orchestrator-tracked
   fits the runtime shape but adds a new state surface.
   Recommendation deferred — v1 picks file-based by default
   (consistent with extraction state) but the choice is a
   load-bearing v0.5.x design call, not v1.
2. **Cost-budget — per-worker vs aggregate?** The existing
   budget envelope (`enforce_budget`) is per-extraction. Per-
   worker would need N envelopes; aggregate would need one
   shared envelope with worker-claim semantics. v1 should
   ship aggregate-budget — the single-envelope shape matches
   the existing extraction surface. Per-worker budgets become
   relevant when the swarm is deeply parallel and individual
   workers occasionally blow up; that's a v0.6.x or later
   concern.
3. **Restart-from-scratch granularity — full swarm or
   diverged subtree?** §6 above. v1 ships full-swarm only
   (matches reference); subtree restart is a v0.5.2+
   optimisation. Empirical question: how often does drift
   localise to a subtree vs propagate? If localised >70% of
   the time, subtree restart is worth the complexity; if
   propagated, full-swarm restart is the only correct
   semantics anyway.
4. **Worker isolation — git worktrees vs shared
   working-tree?** Per the existing pos-amend serialization
   feedback (`feedback_serialize_amendment_builds.md`), two
   build agents in one tree race on `index.lock`. The swarm's
   parallel workers face the same problem at scale. Worktree
   isolation is the obvious answer, but worktree creation +
   teardown is itself per-worker overhead; the throughput math
   isn't obvious. v1 ships shared-tree with serialised commit
   — slower but proven safe; v0.5.x measures whether worktree
   parallelism actually pays off.
5. **`max_planner_depth` lift conditions.** Lens 5 default is
   `1` (flat). When does opt-in to depth-2 pay off? Likely
   only when a single objective is itself large enough to
   warrant decomposition into sub-objectives — which is itself
   a signal that the *extraction* missed a partition. v1
   forbids depth>1; v0.6.x revisits if calibration shows
   sub-decomposition is regularly justified.

---

## §10 F2 RF tension — when does swarming pay off vs cost?

The headline tension. Lens 5's stopping criterion (decompose only
when each subtask's AC is strictly tighter than the parent's;
stop when split adds only coordination overhead) gives the
correct discipline at the *partition decision*. It does not give
a clean answer to the *runtime decision*: at what codebase scale
does spinning up the swarm runtime cost more than the parallelism
saves?

The case for swarming. Luke's framing: "doing it on Web would
spend HOURS on a single agent." A Web codebase with 200+
objectives serially pressed through `claude -p` accumulates
hours of wall-clock time the user is waiting on. Workers in
parallel collapse the wall-clock to single-objective-time +
coordinator overhead. The aggregator's dedup contract handles
the cross-worker integration risk that single-agent runs avoid
by construction.

The case against. Three failure modes the v1 shape needs to
surface honestly:

- **Coordinator overhead at small scale.** A 5-objective
  codebase incurs the same planner + judge dispatch cost as a
  50-objective codebase, but the wall-clock saving is small.
  The swarm becomes a cost ceiling instead of a floor. v1's
  threshold (N objectives → swarm activates) is a calibration
  question — without it, the swarm runs on tasks where
  single-agent would ship faster.
- **Drift-restart thrashing.** A judge whose drift detector
  is too sensitive triggers `needs_fresh_start` repeatedly;
  the swarm restarts, drifts again, restarts again. Wall-clock
  to completion can exceed single-agent because each restart
  pays the full coordinator cost over again. The 30% threshold
  in §6 is an educated guess; if it's wrong, the swarm
  performs worse than the baseline it's meant to replace.
- **Integration risk hidden by per-axis judging.** EVAL_
  DIMENSIONS evaluates each AC independently. Two workers
  both produce code that passes its own ACs but conflict with
  each other's invariants — the per-axis judge sees green,
  the integration test sees red, and the swarm ships a
  diverged contract that nobody audited. The mitigation
  (cross-cutting integration AC per objective) is in §7 but
  is itself a calibration-shaped question.

The tension the doc surfaces explicitly: **swarm-as-default
on every codebase is wrong; single-agent-as-default forever is
also wrong; the threshold between them is empirical and unknown
until v0.4.0 + v1 swarm both ship and we have calibration
data.** That data only exists post-shipping; pre-shipping
estimates are guesses. Treat v1's threshold as a placeholder,
log actuals, recalibrate at v0.5.2 / v0.5.3.

---

## §11 Summary + named decisions

The composition is real and operationalisable. Reverse-ODD's
artefacts are the partition; Lens 5's runtime is the dispatcher;
the slice-and-swarm contracts already proven in the Ruby/JsTs
adapters extend cleanly to the build-time aggregator. v1 picks
domain-clustered partition + implement-code workers + EVAL_
DIMENSIONS judge + full-swarm restart + flat planner depth, and
defers strategy stacking, gap-fill workers, subtree restart, and
worktree isolation to v0.5.2 or later. The version that ships
this is v0.5.x — likely v0.5.1 or v0.5.2 depending on
roadmap-rerank outcome — running alongside the existing v0.5.0
binary-feeder objective, not displacing it.

**Named decisions surfaced for owner ruling.** Each is a v1-
gating call that the owner should rule on before the v0.5.x
plan-doc gets authored. Recommendations included.

1. **D1 — Partition primary input.** Recommendation:
   `objectives.yaml` for implement-from-scratch; `gap-inventory.
   yaml` for gap-fill (deferred to v0.5.2+). v1 ships
   implement-from-scratch only. Owner ruling needed if a
   different artefact should be the partition input.
2. **D2 — v1 partition strategy.** Recommendation:
   domain-clustered alone. Strategies stack at v0.5.2+ once
   calibration data shows benefit. Owner ruling needed if a
   different starting strategy fits better.
3. **D3 — Drift threshold.** Recommendation: 30% cross-worker
   integration failure → `needs_fresh_start`. Calibration-
   shaped; placeholder until empirical data. Owner ruling
   needed only if a different default is preferred.
4. **D4 — Restart granularity.** Recommendation: full-swarm
   only at v1; subtree restart is v0.5.2+. Owner ruling
   needed if subtree restart should ship at v1.
5. **D5 — Coordinator state location.** Recommendation:
   file-based under `<workspace>/.loam/swarms/<run-id>/`
   matching the existing extraction-state pattern. Owner
   ruling needed if orchestrator-tracked state is preferred.
6. **D6 — Roadmap slot.** Recommendation: v0.5.1 or v0.5.2
   (sequence depends on roadmap-rerank). Owner ruling needed
   on the exact slot once the rerank lands.

The doc closes with the standing F2 RF tension named in §10:
the threshold between single-agent-default and swarm-default
is empirical and post-shipping. Treat v1's threshold as a
placeholder, log actuals, recalibrate.

---

**End of doc.**
