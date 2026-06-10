# SELF-MAINTAINING WORK LOOP — event-sourced work-state auto-capture + a live census that stays correct on its own

**Status:** sub-plan-doc (PLAN ONLY — no build) · **Date:** 2026-06-05 · **Owner:** Luke (greenlit "build it TODAY", this dispatch)
**WD:** `/Users/lukeivers/loam` (canonical loam checkout — the WD-discipline guard blocks framework-source edits from the pos3 workspace, so this MUST build here)
**Parent plan / architecture:** `docs/design/work-management-system-architecture.md` — the work-items-first model + the 7-increment roadmap. This is the **self-maintenance layer** the architecture assumed but never specified: the WMS shipped the *store + the lenses* (read surfaces); it never shipped the *write-back loop* that keeps the store true without a human reconciling it.
**This is PART 1 of a two-part build.** PART 2 (the hourly autonomous-restart trigger) is the stacked plan `docs/plans/hourly-autonomous-restart-trigger.md` and READS this layer's census to know what is current + what is genuinely done. **Build PART 1 first; PART 2 composes on the census this layer makes trustworthy.**

**Predecessors (load-bearing prior seals + artefacts, Tier-0 read on disk 2026-06-05):**
- **objective_tracker** (the L1 event-sourced work-item store — EXTEND via its existing write API, do NOT replace) — `framework/objective-tracker/src/loam/objective_tracker/` : `runtime.py` (`ObjectiveTracker`: `create`/`start`/transition methods, `query_projection_view`/`list`/`list_by_root`/`trace_to_root`/`snapshot`), `events.py` (append-only typed event log; `ObjectiveCreated`/`StatusTransitioned`/`CriterionEvaluated`; `event_from_row` replay), `spec.py` (`ObjectiveStatus` lifecycle `proposed/active/blocked/owner_pending/achieved/abandoned`, the WMS-inc-2 edges + `belongs_to_project` + `tagged_streams` + `priority`), `store.py` (SQLite WAL event-log store). **Event-sourced; the projection rebuilds from events alone (the D8 round-trip). The store is the single source of truth this layer keeps TRUE.**
- **intake** (the ONLY existing tracker-WRITE path from conversation — the precedent this layer extends) — `framework/primary-persona/src/loam/primary_persona/keep_pace/intake.py` : `create_proposed_item` (async, calls the store's `create`), `gate_admits`, `is_near_duplicate`, `_conversation_provenance` (the `LiftedFrom` `origin: conversation` pointer), the `WorkIntentExtractor` seam. **The write-discipline (propose-and-confirm, conservative dedup, fail-soft, provenance) this layer reuses for the DELTA-capture path.**
- **FBM Slice C** (the ground-truth STATE engine) — `framework/tools/loam/src/loam_cli/audit/registry.py` : `derive_project_state(name)` (fresh-from-git-refs, `None` for unregistered), `PROJECT_REGISTRY` (registers exactly `loam` + `cairn` today), `registered_project_names`. **FBM owns project build/sealed/merged STATE from real git refs. The census DERIVES project truth from here; it never stores a stale status string.**
- **The lenses** (the READ surfaces that consume the store — they are why the store must be true) — `framework/primary-persona/src/loam/primary_persona/keep_pace/` : `work_streams.py` + `work_streams_surface.py` (inc-1, BUILT — the per-turn streams block), `projects.py` (inc-2), `prioritize.py` + `relational.py` (inc-4), `analytics.py` (inc-7). **All read-only over the store; all only as correct as the store's last write. This layer is what makes their reads trustworthy.**
- **stop_emitter** (the Stop-hook turn-close surface — the per-turn trigger seam this layer's capture hangs from) — `framework/primary-persona/src/loam/primary_persona/stop_emitter.py` : `cli_stop` (reads Claude Code's Stop envelope, derives a stable per-turn id, dedups on a workspace marker, enqueues to the disk-backed queue, returns 0 unconditionally). **The existing once-per-turn-close handler. It enqueues FBM memory-episodes today and touches the tracker NOT AT ALL — that absence is the gap this layer closes.**
- **work_visibility** (Slice E — the plain-render multi-source snapshot precedent) — `framework/primary-persona/src/loam/primary_persona/work_visibility.py` : read-only multi-source snapshot, zero-internal-vocab HARD invariant, fail-soft. **The census's render precedent.**
- **Composer** — `framework/primary-persona/src/loam/primary_persona/context_composer.py` : `TriggerKind.turn`, `register`, the 10k-char structural cap. The registration seam for the per-turn census surface.

**BASELINE candidate:** current `main` tip at build time (the plan-doc commit's parent). Components decided in §2 + D1 — recommendation: **two-component amendment on `objective-tracker` (a thin git/task→event capture adapter, additive) + `primary-persona` keep-pace (the turn-close capture contributor + the census surface). NOT a new component.**
**Status-file target:** `docs/STATE.md` + roadmap §8 + parent architecture §7 backfill (see §9).
**Quality bar:** ODD §2.5 — every AC outcome-shape, no method-in-AC; ≥1 outcome-altitude AC exercising the production capture + census through a real turn against the LIVE repos with NO pre-arranged state and NO hand-reconciliation. Normal careful loam discipline (sealed cycle + tests) — this is bounded-to-the-user's-own-work-tracking, NOT the high-risk confidence-gate bar (that bar applies to PART 2).

---

## §1 Summary / TL;DR

**What ships:** the **write-back loop** the WMS never had — a turn-close (Stop-hook) **capture contributor** that records real **work-deltas** into the objective-tracker event log **event-sourced from ground-truth signals** (git refs via FBM Slice C, the persona task list, the workstream-queue completions, decision-register entries), so the work-item store transitions itself (active→achieved when a bound project's STATE shows sealed/merged; new work appears; status moves) **without a human reconciling it** — PLUS a **current-state-of-all-work census** surface that renders the genuinely-current state of every stream/project/loop, **correct because it self-maintained**, derived live (never a stored-stale string), capped + fail-soft like every other keep-pace surface.

**The gap this closes (the thing Luke caught):** the WMS lenses (streams/projects/goals/plate/waiting/analytics) all surface READ-ONLY over the tracker store. The ONLY thing that writes work-state from real activity today is `intake.py` — and it only captures *new* work *on confirm*. **Nothing event-sources work-DELTAS** (a task completing, a release shipping, a status transition) from real git/task signals back into the store. So the census is only as current as the last manual transition — which is exactly how the persona "claimed done when the outcome wasn't delivered." This layer makes the store track reality on its own.

**AC families:**
- `AC.CAP.*` — the capture contributor: on turn-close (and on demand), real work-deltas are recorded into the tracker as events — event-sourced from ground-truth signals, never from LLM recall; idempotent (a delta is captured once); fail-soft (capture failure never blocks the turn).
- `AC.DERIVE.*` — the auto-transition: a work item bound to an FBM-registered project transitions its lifecycle from the project's DERIVED STATE (active→achieved on sealed/merged), never from a hand-typed status; changing ground truth and re-running moves the item with no register edit.
- `AC.CENSUS.*` — the current-state-of-all-work surface: one concise, capped, fail-soft block rendering the genuinely-current state of all streams/projects/open-loops, derived live, subsuming (not duplicating) the existing lens blocks.
- `AC.HONEST.*` — the no-fabrication invariant: an item with NO ground-truth signal (no FBM-registered project, no git/task evidence) is surfaced with its real staleness + an explicit "no ground-truth bound" mark — the census NEVER asserts "done" or a STATE it cannot evidence (the literal Luke-caught failure mode as an AC).
- `AC.SELFMAINT.LIVE.*` — **outcome-altitude**: at an arbitrary moment, against the LIVE loam + cairn repos with NO pre-arranged state and NO hand-reconciliation step, the production census shows the genuinely-current state of all work, correct *because the capture loop maintained it* — verified by changing real ground truth and observing the census reflect it through the production entry points alone.

**Key decisions baked (full list + recommendations in §3):**
1. **Two-component amendment, NOT a new component** (D1) — the capture adapter is additive on `objective-tracker` (it WRITES via the existing event API + READS FBM Slice C); the contributor + census are keep-pace siblings on `primary-persona`.
2. **Event-sourced from ground-truth signals, never LLM recall** (D2 ★) — the capture derives deltas from git refs (FBM Slice C), the task list, the workstream-queue completions, and decision-register entries; it does NOT ask the model "what got done this turn." This is the load-bearing correctness decision.
3. **Capture fires on the Stop-hook (turn-close) + is also on-demand callable** (D3) — composes on the existing `stop_emitter` once-per-turn-close trigger; it enqueues a capture pass the same fail-soft way memory-episodes already enqueue.
4. **The census SUBSUMES the existing lens blocks** (D4) — one current-state block, not a sixth wall of text; inherits the Slice-D char-cap + TTL + fail-soft (no context re-bloat — the FBM load-filter / #80 anti-bloat mandate holds).
5. **Auto-transition is bounded to evidence-backed lifecycle moves; owner-class transitions stay owner-gated** (D5) — the loop auto-moves active→achieved/blocked on hard git-ref evidence; it does NOT auto-close owner_pending items or fabricate transitions without a signal.

**F2 RF on scope realism (full treatment in §10):** the honest constraint is that **ground-truth derivation is only literally true for `loam` + `cairn`** (the two FBM-registered projects). Money / LitRPG / Personal-Home have no registered git derivation — their census line comes from task-list/queue/staleness signals + the explicit "no ground-truth bound" mark (AC.HONEST.1), never a fabricated STATE. The self-maintaining property is FULLY real for the registered projects + the task/queue-tracked items today; registering the other projects is a named follow-on (§7). This is named so the headline "self-maintains without reconciliation" is honest about its current reach.

---

## §2 Placement decisions

| Item | Placement | Rationale |
|------|-----------|-----------|
| The git/task/queue→event capture adapter (derive deltas from ground truth → tracker events) | **`objective-tracker`** component (a new `capture.py` module + the existing event-write API in `runtime.py`/`events.py`) | The store OWNS its write path; the adapter is additive (it consumes FBM Slice C + the task/queue surfaces READ-ONLY and emits `StatusTransitioned`/`ObjectiveCreated` via the existing API). Co-locating keeps the single-source-of-truth + the event-replay round-trip intact (Lens-1). |
| The turn-close capture contributor (fire the capture pass on Stop) | **`primary-persona`** (`stop_emitter` gains a capture-enqueue step, sibling to the memory-episode enqueue; or a keep-pace `keep_pace/work_capture.py` the Stop path invokes) | The Stop-hook is the existing once-per-turn-close trigger; the capture enqueues the same fail-soft, return-0 way memory-writes already do — no new trigger primitive (Lens-1). |
| The current-state-of-all-work census surface | **`primary-persona`** keep-pace (`keep_pace/work_census.py`, sibling to `work_streams_surface.py` + `project_state.py`) | The census IS a keep-pace turn-contributor; it composes the existing lens renderers + `derive_project_state` (Lens-1), capped + TTL'd like Slice D, subsuming the lens blocks. |
| Live project STATE for a bound item | **reused verbatim** from `derive_project_state` (Slice C) | Lens-1 — FBM owns STATE from git refs; the capture + census are pure consumers, never re-derivers. |
| The task-list / workstream-queue completion signals | read-only adapters into the capture pass | These are existing surfaces (the persona task DB + `pos3/.claude/workstream-queue.yaml`'s `completed:` list); the capture reads them as delta-evidence, never owns them. |

**Out of placement (NOT this layer):** the hourly autonomous trigger (PART 2 — its own plan + component); the #71 mismatch side-channel's auto-CORRECT (this layer DETECTS + records deviation as an event; #71 owns the channel + the ground-truth auto-correct); registering Money/LitRPG/Personal-Home as FBM projects (named follow-on, §7).

---

## §3 Named decisions (with recommendations) — surface to Luke

Every decision carries a recommendation. ★ flags a genuine **owner product-shape call**; the rest are **autonomous method-calls** (the builder takes method from here).

### D1 — Two-component extension vs a new component. **RECOMMEND: EXTEND `objective-tracker` (additive capture adapter) + `primary-persona` keep-pace (contributor + census). NOT a new component. Method-call.**
- Why: the store already IS the event-sourced work-item backbone with a write API; the capture adapter is the same shape as `intake.py`'s write path (consume a signal → emit an event), just sourced from ground truth instead of conversation. The census is the same shape as the already-shipped lens surfacers. A new component would duplicate the event API, the FBM-binding, the keep-pace registration, and the TTL/cap discipline.
- Cost honestly (F2): this elevates the capture-from-ground-truth concern into the tracker component (a SEALED component, touched with a manifest entry). The fence (§5) is ADDITIVE-ONLY: a new `capture.py` + new event emissions via the EXISTING API; no change to an existing event kind, field type, or the D8 round-trip. If the capture would require changing an existing contract, the builder HALTS (§8 #2).

### D2 — ★ Capture source: ground-truth signals vs LLM recall. **RECOMMEND: event-source the deltas from GROUND-TRUTH signals ONLY — git refs (FBM Slice C `derive_project_state`), the persona task-list completions, the workstream-queue `completed:` entries, and decision-register entries. The capture NEVER asks the model "what got done this turn." This is the one load-bearing correctness call worth Luke's deliberate yes.**
- Why this is the whole point: Luke caught the persona "claiming done when the outcome wasn't delivered." That is exactly the failure mode of LLM-recall capture — the model narrating progress that isn't on disk. Sourcing capture from git/task/queue ground truth structurally prevents it: an item only transitions to `achieved` when a real git ref / a real task-completion / a real queue-completion evidences it. The capture is a *deterministic reconciliation of the store against reality*, not a model's self-report.
- The owner call: confirm ground-truth-only sourcing (vs a hybrid where the model proposes deltas the ground truth then confirms). RECOMMEND ground-truth-only for the auto-path; the model MAY *propose new work* via the existing intake path (which is already propose-and-confirm), but the *delta/transition auto-capture* is evidence-gated. This keeps the self-maintaining loop honest by construction.

### D3 — Capture trigger. **RECOMMEND: fire the capture pass on the Stop-hook (turn-close), enqueued the same fail-soft / return-0 way `stop_emitter` enqueues memory-episodes; AND expose an on-demand entry point (so PART 2's hourly job + a manual refresh can drive it). Method-call.**
- Why: the Stop-hook is the existing once-per-turn-close trigger (`stop_emitter.cli_stop`); the capture rides it. Per-turn cadence keeps the census fresh without a separate poller. The on-demand entry point is what PART 2's hourly job calls to refresh the census before it decides what to resume (the seam between the two parts).
- Cost honestly: per-turn capture must be cheap (it reads FBM Slice C, already TTL-cached, + the task/queue files). If the fan-out is too slow per-turn even cached, halt (§8 #4) — mirrors the inc-1/inc-2 latency halt.

### D4 — The census surface shape. **RECOMMEND: ONE concise current-state block that SUBSUMES the existing per-lens blocks (streams/projects), within the Slice-D hard char-cap, TTL-cached, fail-soft. NOT a sixth always-on wall of text. Method-call.**
- Why: the FBM load-filter (#80) + Slice D's cap exist precisely to stop context re-bloat. The census is the *unified* current-state view; it replaces-and-subsumes the streams/projects blocks rather than adding a parallel one. If the unified block would exceed the cap, active/changed items render in full and quiet/stable ones collapse to a count (the inc-1 AC.WS.SURFACE.3 precedent). Halt (§8 #1) rather than spill the cap.

### D5 — Auto-transition boundary. **RECOMMEND: the loop auto-moves a work item's lifecycle ONLY on hard evidence (active→achieved on a bound project's sealed/merged git STATE; active→blocked on a recorded blocker that ground truth confirms). It does NOT auto-close `owner_pending` items, does NOT fabricate a transition without a signal, and records every auto-transition as an evented, auditable delta. Method-call, but the owner-class boundary is load-bearing.**
- Why: `owner_pending` means "waiting on Luke" — the loop must never decide that on his behalf. Evidence-gated auto-transitions are safe (a sealed git ref is ground truth); owner-class moves stay owner-gated (the intake/KP5 owner-gated-write precedent). Every auto-move is an event in the append-only log, so the trail is auditable + reversible.

---

## §4 Spec-objective placement

- **Binds to:** the work-management-system prime capability (architecture §1 + §10 Lens-2) — "where is all my work / what's next / what's done" reduced to zero translation burden. The WMS shipped the lenses; this layer is what makes their reads *true on their own*. It also binds to the keep-pace flagship (task #12) — accurate live state surfaced every turn.
- **Ladders up to:** **VALUE_PROPOSITION prime objective** (per `feedback_value_proposition_as_prime_objective`) — Lens-2 primary-persona test: a work-state that maintains itself + surfaces correctly reduces Luke's translation burden to zero AND removes the trust-destroying "claimed done when it wasn't" failure. That correctness IS the value; a lens over a stale store is worse than no lens.
- **Prime directive tie (Lens-0):** per-user-tuned translation of work-state — the user brings WHAT they want done; loam owns HOW it is tracked + kept true; "you always know exactly where things are, without doing the bookkeeping" is the non-tech-user promise this delivers.

---

## §5 Sealed-component fence

**Two components touched; both with manifest entries.**

1. **`objective-tracker`** (SEALED) — the capture adapter. **Fence: ADDITIVE-ONLY.** Permitted: a new `capture.py` module that READS FBM Slice C + the task/queue surfaces and WRITES via the EXISTING `runtime.py` event API (`StatusTransitioned`/`ObjectiveCreated`); a new optional `origin: ground-truth-capture` provenance value (the `LiftedFrom` additive precedent); recording a deviation as an evented delta. **Forbidden without a halt:** changing an EXISTING event kind/field type/meaning, narrowing the projection or filter contract, or any change that makes a pre-widening record fail to deserialise (the D8 round-trip is the hard invariant — §8 #2).
2. **`primary-persona`** (SEALED, has a live sidecar) — the turn-close capture contributor + the census surface. **Fence:** `stop_emitter` gains an additive capture-enqueue step (the memory-episode enqueue is preserved byte-for-byte; capture is a SECOND fail-soft enqueue, return-0 unchanged); a new keep-pace `work_census.py` turn-contributor; the census subsumes (does not delete) the existing lens surfacers' registration. **Forbidden without a halt:** changing `stop_emitter`'s return-0 contract or the memory-write enqueue (AC.M.4/AC.J.2 — the Stop hook MUST stay non-blocking); modifying the `OBJECTIVES.md` read-contract KP1/N4 bind to; widening the narrow read-only `TrackerClient` Protocol into a write surface from the census (the census is READ-ONLY; writes go through the capture adapter's tracker API).

Both seal via `loam amend apply` + `loam amend seal` — **name `loam amend apply` explicitly in the build dispatch** (per `feedback_dispatch_explicit_loam_amend_apply`); serialize the two-component build in one tree (per `feedback_serialize_amendment_builds`).

---

## §6 Acceptance criteria (outcome-shape; method-in-AC test passed on each)

Each AC states an *outcome* satisfiable by methods other than the one in mind; each maps to a named test at build time. AC IDs are scope-descriptive (per `feedback_scope_descriptive_ac_ids`).

**AC.CAP.1** — On turn-close, a capture pass runs and records real work-deltas into the tracker as events: a work item whose bound project's ground-truth STATE has advanced (e.g. a sealed/merged git ref) gets a recorded transition event; the pass derives deltas from ground-truth signals (git refs / task-list / queue completions / decision register), NOT from the model's narration of the turn. *(Outcome: deltas are captured from ground truth into the event log; method — adapter shape, signal set — is the builder's call.)*

**AC.CAP.2** — A given delta is captured at most once: re-running the capture pass over unchanged ground truth records NO duplicate event, and the projection is unchanged. *(Outcome: idempotent capture; method is the builder's call.)*

**AC.CAP.3** — A capture-pass failure (a signal source unreadable, FBM unavailable, the store locked) never blocks the turn: the Stop hook still returns 0 and the turn closes normally; the failure is logged, not raised. *(Outcome: fail-soft, non-blocking — the AC.M.4 Stop-hook contract preserved; method is the builder's call.)*

**AC.DERIVE.1** — A work item bound to an FBM-registered project transitions its lifecycle from the project's DERIVED STATE (a fresh `derive_project_state` call), never from a stored/hand-typed status string: advancing the real repo ground truth (a new sealed/merged ref) and re-running the capture moves the item (active→achieved) with NO edit to any register or hand-set status. *(Outcome: derived-not-stored transition, verifiable by changing ground truth; method is the builder's call.)*

**AC.DERIVE.2** — Every auto-transition is recorded as an evented, auditable delta in the append-only log (reconstructable from events alone after a cold projection rebuild) and carries its evidence (the git ref / task / queue entry that triggered it). *(Outcome: auditable + single-source-of-truth preserved; method is the builder's call.)*

**AC.CENSUS.1** — On a real turn, the keep-pace lens surfaces ONE concise current-state-of-all-work block covering every non-paused stream/project/open-loop, one short line each, within a hard character cap; the block subsumes (does not duplicate) the existing streams/projects lens blocks. *(Outcome: concise, capped, single, subsuming block — no context re-bloat; method is the builder's call.)*

**AC.CENSUS.2** — The census's per-item STATE is composed from a FRESH ground-truth read (a `derive_project_state` call for a bound project; the live task/queue signal otherwise), never a stored/stale status; changing ground truth and re-reading the census reflects the change without editing any register. *(Outcome: live-derived census; method is the builder's call.)*

**AC.HONEST.1** — A work item with NO ground-truth signal (no FBM-registered project, no git/task/queue evidence) is surfaced with its real staleness + an explicit "no ground-truth bound" mark; the census NEVER asserts "done" or a build-STATE it cannot evidence from a ground-truth source. *(Outcome: the no-fabrication invariant — the literal Luke-caught "claimed done when it wasn't" failure forbidden by construction; method is the builder's call.)*

**AC.HONEST.2** — When a work item's expected state (its recorded status) diverges from its derived ground-truth STATE (e.g. an item still `active` whose bound project shows merged), the census flags the divergence AND a structured deviation record `{item, expected, derived, evidence}` is emitted to the memory-reality mismatch side-channel; if that channel's entry point is absent the detection no-ops fail-soft (never crashes the turn). *(Outcome: deviation detected + routed; the #71 wiring is the integration point; method is the builder's call.)*

**AC.SELFMAINT.LIVE.1 (OUTCOME-ALTITUDE, `outcome-altitude:true`)** — At an arbitrary moment, against the LIVE loam + cairn repos with NO pre-arranged state and NO hand-reconciliation step: (1) advance real ground truth (e.g. record a new sealed/merged ref or a task completion that a work item is bound to), (2) drive the production capture pass through its real turn-close / on-demand entry point, (3) render the production census through a real keep-pace turn — and observe the census show the genuinely-current state, with the advanced item's lifecycle MOVED by the capture loop (not by a hand edit), STATE derived live, and no fabricated "done." Invokes the production entry points (capture pass + `derive_project_state` + census render), no fixtures, no pre-arranged state, no manual reconciliation. *(This is the literal "current-state stays live + correct on its own, verified without any hand-reconciliation step" the objective names. Method is the builder's call.)*

---

## §7 Out of scope (deferred + when)

- **The hourly autonomous-restart trigger** — PART 2, its own plan (`docs/plans/hourly-autonomous-restart-trigger.md`) + its own component. This layer ships the census PART 2 reads.
- **Registering Money / LitRPG / Personal-Home as FBM projects** (so they get true git-ref derivation) — a named follow-on (needs a per-project marker spec like Cairn's). Until then those use the task/queue/staleness path + the AC.HONEST.1 "no ground-truth bound" mark.
- **The #71 mismatch side-channel's auto-CORRECT** — this layer DETECTS + records deviation (AC.HONEST.2); #71 owns the channel + the ground-truth auto-correct. Wired fail-soft so order doesn't block.
- **LLM-proposed delta capture** — the auto-path is ground-truth-only (D2); the model proposes only NEW work via the existing propose-and-confirm intake path. A hybrid model-proposes-ground-truth-confirms path is a possible later enrichment, not this layer.

---

## §8 Halt triggers (abort the in-flight build + surface)

1. **The unified census cannot fit all active items within Slice D's char-cap even after the collapse rule.** Halt — the anti-bloat constraint is load-bearing (F2 #1); surface for a cap-vs-content ruling rather than spilling.
2. **The capture adapter would require changing an EXISTING tracker event kind / field type / projection-or-filter contract** (a pre-widening record would fail to deserialise). Halt — that breaks the D8 round-trip + a sealed read-contract; surface rather than silently widen (the additive-only fence, §5).
3. **The capture-enqueue would change `stop_emitter`'s return-0 / non-blocking contract or the existing memory-write enqueue** (AC.M.4 / AC.J.2). Halt — the Stop hook MUST stay non-blocking; surface a seam ruling.
4. **The per-turn capture fan-out is too slow even with the Slice-D TTL cache.** Halt — surface a caching/cadence ruling (capture-every-N-turns, or move capture to PART 2's hourly job only) rather than introduce a per-turn latency regression.
5. **Ground-truth-only sourcing (D2) cannot evidence a class of delta the census needs** (e.g. a "decision made" with no recorded register entry). Halt + surface — do NOT fall back to LLM-recall capture silently; that reintroduces the exact failure mode this layer exists to kill.
6. **An AC drifts to method-in-AC during build** (a test can only pass one specific way). Halt + fix the AC (doc-only) per `feedback_loose_AC_text_fix_AC_not_implementation`, never the implementation.

---

## §9 Bookkeeping (backfill on seal)

- **`docs/STATE.md`** — add the self-maintenance layer (the capture adapter under objective-tracker + the census under primary-persona/keep-pace) — the write-back loop that keeps the WMS store true.
- **Roadmap §8 / parent architecture §7** — record the self-maintenance layer (the loop the architecture assumed but never specified); note the lenses are now backed by a self-maintaining store.
- **`docs/design/work-management-system-architecture.md`** — backfill: the write-back loop closes the "store stays true on its own" gap; the lenses' reads are now trustworthy.
- **Task #69** (FBM quality + accuracy overhaul — its "current-state-of-all-work" slice) → progress note: the census + self-maintenance landed. **Task #84** (the MAJOR WMS sub-component) → note: the self-maintenance loop completes the read-surfaces-only WMS. **Task #71** → integration note (the deviation seam expects its entry point).
- **`feedback_*` memory** — candidate capture: "report against the maintained census, not the model's recall" (the Luke-caught lesson) if it recurs; this layer is the structural fix, the memory is the discipline. Capture on owner confirm.

---

## §10 F2 Ruthless Feedback (honest doubts + named design risks)

1. **★ The self-maintaining property is FULLY real only for the FBM-registered projects (loam + cairn) today.** *Disagreement:* the headline "current-state stays correct on its own without reconciliation" is literally true for items bound to `loam`/`cairn` (git-ref-derived) + items the task-list/queue track; it is NOT yet true for Money/LitRPG/Personal-Home, which have no registered git derivation. *Evidence (Tier-0):* `registry.py` `_default_registry()` registers exactly `loam` + `cairn`; the Money/LitRPG/Personal-Home streams have no FBM project binding. *Alternative (baked in):* AC.HONEST.1 makes the no-ground-truth case explicit (real staleness + a "no ground-truth bound" mark, never a fabricated STATE); registering the other projects is a named follow-on (§7). Honest framing for Luke: this layer delivers TRUE self-maintenance for the loam + cairn build-work + all task/queue-tracked items now, and honest-staleness (not fake-done) for the rest, with the upgrade path named. This is the central scope-realism caveat.

2. **Per-turn capture vs the context-bloat / latency we just fought.** *Disagreement:* a naive "reconcile everything every turn" would re-bloat context (the census) AND add per-turn I/O (the capture). *Evidence:* `project_state.py` `_STATE_BLOCK_CHAR_CAP=600` + `_STATE_TTL_SECONDS=60`; the #80 P@5=0.0 de-flood fix; the FBM-don't-bloat mandate. *Alternative:* the census SUBSUMES the lens blocks (one block, D4) under the same cap; the capture rides the existing TTL-cached FBM read + the cheap task/queue files; if either can't hold, halt (§8 #1 / #4). The resolution is right but the builder must hold both constraints.

3. **Ground-truth-only capture cannot see every kind of delta.** *Disagreement:* "a decision was made this turn" or "a new sub-task emerged in conversation" may have no git/task/queue signal at capture time — so a ground-truth-only auto-path will MISS those until they're recorded somewhere checkable. *Evidence:* the only conversational write path today is intake's propose-and-confirm. *Alternative:* new conversational work flows through the EXISTING intake path (propose-and-confirm — already correct); the auto-capture handles the *transition/completion* deltas that DO have ground-truth evidence. The honest line: this layer makes the store SELF-CORRECT against reality; it does not make it omniscient about un-recorded conversational deltas — those still enter via intake. Surfaced so the boundary is conscious (Lens 6), and named as halt-trigger §8 #5 (never fall back to LLM-recall capture to paper over the gap).

4. **objective-tracker role-expansion (writing from a NEW source) touches a sealed component.** *Disagreement:* "just add a capture adapter" understates that the tracker now accepts auto-writes from git/task ground truth, not only intake. *Evidence:* `spec.py` is `frozen=True`; the event API is the only mutation path. *Alternative:* the adapter emits via the EXISTING event API (the same path intake uses) with a new `origin` provenance value — additive, D8-round-trip-preserving (§5 fence + §8 #2 halt). The role-expansion is real but fenced additive-only.

5. **Scope-confidence (F4) note.** The compositional shape is HIGH-confidence (capture-adapter mirrors intake's write path; census mirrors the lens surfacers; both compose on shipped primitives) and tightly scoped. The genuinely-open fork left as ★ owner-call is D2 (ground-truth-only vs hybrid sourcing) — surfaced with a recommendation, method left to the builder. The capture-pass internals, the census render details, and the signal-set are method-calls left loose. The ACs are outcome-shape; the fork is surfaced.

---

## §11 Provenance trail (load-bearing sources, verified on disk 2026-06-05)

- objective_tracker store + event API — `framework/objective-tracker/src/loam/objective_tracker/` : `store.py` (SQLite WAL event-log L15–33), `runtime.py` (`ObjectiveTracker` create/transition/query API), `events.py` (append-only union + `event_from_row` replay), `spec.py` (`ObjectiveStatus` lifecycle + the inc-2 edges/project-binding/tags/priority, `frozen=True`).
- intake write-path precedent — `framework/primary-persona/src/loam/primary_persona/keep_pace/intake.py` (`create_proposed_item` L546+, `gate_admits` L383, `is_near_duplicate` L441, `_conversation_provenance`/`LiftedFrom` L490, the `WorkIntentExtractor` seam L176–360).
- FBM Slice C STATE engine — `framework/tools/loam/src/loam_cli/audit/registry.py` (`derive_project_state` L138, `PROJECT_REGISTRY` registers loam+cairn L110, `registered_project_names` L129).
- the lenses (read surfaces this layer keeps true) — `framework/primary-persona/src/loam/primary_persona/keep_pace/` : `work_streams.py` + `work_streams_surface.py` (inc-1, BUILT), `projects.py` (inc-2), `prioritize.py`+`relational.py` (inc-4), `analytics.py` (inc-7).
- stop_emitter (the turn-close trigger seam; touches the tracker NOT AT ALL today — the gap) — `framework/primary-persona/src/loam/primary_persona/stop_emitter.py` (`cli_stop` envelope → enqueue → return 0 unconditionally; AC.M.4 non-blocking contract; the memory-write-queue enqueue is its only write — NO tracker write).
- work_visibility (Slice E plain-render precedent) — `framework/primary-persona/src/loam/primary_persona/work_visibility.py` (read-only multi-source snapshot, zero-internal-vocab invariant).
- WMS architecture (parent) — `docs/design/work-management-system-architecture.md` (the work-items-first model §2, the lens set §3, the FBM boundary §5, the increment roadmap §7 — all 7 increments sealed-local read-surfaces; the self-maintenance write-back loop is the unspecified gap this layer fills).
- the Luke-caught failure — the persona reporting a component "done" when the OUTCOME wasn't delivered (this dispatch): the structural cause is a read-only lens over a store nothing event-sources from ground truth; AC.HONEST.1 forbids it by construction.
