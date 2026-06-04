# WMS Increment 5 — the GOALS, ON-MY-PLATE, and WAITING-ON lenses

**Status:** sub-plan-doc (PLAN ONLY — no build) · **Date:** 2026-06-03
**WD (build):** `/Users/lukeivers/loam` (the loam repo; canonical pos-v2 tree — confirm `pwd` as the literal first build action)
**Parent plan:** `docs/design/work-management-system-architecture.md` (the WMS architecture; roadmap §7 item 5 + the lens set §3 + the FBM boundary §5)
**Predecessors (load-bearing, verified on the branches 2026-06-03):**
- `build/wms-increment-2` — the unified L1 work-item model + the **projects lens** (`keep_pace/projects.py`) — the EXISTING lens pattern this increment mirrors.
- `build/wms-increment-4` — `keep_pace/relational.py` (waiting-on-me-vs-others + unblocked-next ALREADY surfaced) + `keep_pace/prioritize.py` (the five-signal derived ordering). Tip `ea1dcc37` (a docs-backfill child of seal `1fb84d9c`).
**BASELINE candidate:** `build/wms-increment-4` tip @ build time — the plan-doc commit's parent on THAT branch (the work-item store, the edge graph, `prioritize.py`, `relational.py`, the `OBJECTIVES.md` ladder loader all live there + on its inc-2 ancestor, NOT on main — building on main finds no graph to lens, §8 halt #1).
**Status-file target:** `docs/STATE.md` + roadmap §8 register + architecture §7 row-5 backfill on seal.
**Quality bar:** ODD §2.5 (every line maps to a named AC); zero-internal-vocab HARD invariant on every render; ≥1 outcome-altitude AC; single-component on the SEALED `primary-persona` (consume the store read-only — no store mutation).
**Branch:** stacks on `build/wms-increment-4` (do NOT branch from main).

---

## §1 Summary / TL;DR

Three lenses — **goals**, **on-my-plate**, **waiting-on** — each a VIEW (filter + grouping + sort + render) over the ONE inc-2 work-item graph, each mirroring the sealed `projects.py` lens shape and composing on inc-4's `prioritize.py` ordering + the Slice-D renderer discipline. No new store, no store mutation, no new lifecycle.

- **goals lens** — work laddered over the user's stated objectives (`OBJECTIVES.md`): per active objective, the work that advances it + a goals-with-no-work surface ("nothing is moving this goal") + plain-language progress. **The ladder is DERIVED via the SAME alignment mechanism `prioritize.py` already uses** (`aligned_terms_from_objectives` + goal-text-mentions-subgoal) — there is NO stored `objective-slug` field on the work item (confirmed absent on the projection, §11), so the goals lens computes the ladder, it does not read a binding.
- **on-my-plate lens** — a flat, priority-sorted filter of what's actively on the user NOW: open + ready + not-blocked + not-waiting-on-others, ordered by inc-4's `prioritize` (reusing its ranking + transparent reason wholesale). The "what should I actually be doing" view.
- **waiting-on lens** — on-me (`owner_pending` / internal waits) vs on-others (external-party `waits_on`), **formalized as a named lens by EXTRACTING + WRAPPING inc-4's existing `_waiting_rows` logic into a reusable shared helper that BOTH `relational.py` and the new waiting-on lens call** — NOT a re-implementation (the central reconciliation, §3 D-WMS5.3 / §10 RF #1).

**Surfacing discipline (load-bearing — §3 D-WMS5.4 / §10 RF #2):** production today already registers FOUR `TriggerKind.turn` contributors (streams, projects, relational, intake). Adding three MORE always-on turn blocks = seven blocks every turn = the per-turn bloat this increment is told not to create. **These three lenses ship as `render_*_block` production entry points that are NOT registered as turn contributors** — they are on-demand / owner-invoked surfaces the persona renders when the question is asked ("what's on my plate?", "how's the launch goal doing?", "what am I waiting on?"), not every-turn walls of text. The per-user always-on lens CHOICE is increment 6 (out of scope).

**AC families:** AC.GOAL.* (ladder + no-work-goal surface + no-fabricated-ladder) · AC.PLATE.* (the right filter + priority-sorted reuse of inc-4 ordering) · AC.WAIT.* (on-me-vs-on-others as a formal lens reusing inc-4's logic, no duplication) · AC.LENS.* (the shared lens shape + the no-bloat surfacing discipline) · AC.WMS5.LIVE.1 (the outcome-altitude — a real store, all three lenses render the right view live, no pre-arranged state, no duplication of inc-4's surfacing).

**Key decisions baked:** lenses are computed not materialized (WMS-D2, inherited); the goals ladder is derived not stored (D-WMS5.2); waiting-on extracts-and-wraps inc-4, never duplicates (D-WMS5.3); the three lenses are on-demand not always-on turn blocks (D-WMS5.4); keep them as sibling modules — do NOT refactor to a lens-protocol this cycle (D-WMS5.5, the Lens-1/F4 call).

**F2 scope realism:** this is a SINGLE-component, derivation-only, three-sibling-module increment on a sealed component with a proven pattern (projects.py) and a proven base (prioritize.py / relational.py) to mirror. The genuine risk is NOT build-size — it is (a) the waiting-on duplication trap if the build re-implements instead of extracts (RF #1), and (b) accidentally registering the lenses as always-on turn blocks and re-bloating the surface (RF #2). Both are named as halt-class so the build cannot drift into them silently.

---

## §2 Placement decisions (per partition rule)

| Item | Placement | Rationale |
|---|---|---|
| goals lens | new `keep_pace/goals.py` on `primary-persona` | mirrors `projects.py` (a sibling lens module); composes the `OBJECTIVES.md` loader + `prioritize`'s alignment |
| on-my-plate lens | new `keep_pace/plate.py` on `primary-persona` | a filter + a straight reuse of `prioritize`; sibling module |
| waiting-on lens | new `keep_pace/waiting_on.py` on `primary-persona` + a SHARED waiting-split helper extracted from `relational.py` | formalizes inc-4's `_waiting_rows` as a lens; the extraction keeps ONE source for the split |
| the shared waiting-split helper | extract from `relational.py` into a shared location BOTH modules import | reconciliation: `relational.py` keeps surfacing it in its combined block; the new lens reuses the SAME logic (no second implementation) |
| the work-item store | CONSUMED read-only (existing `query_projection_view` / `unblocked_next` / `waiting_on_other`) | NOT modified — no store mutation, no new field (D-WMS5.1) |
| per-user lens CHOICE (which lens surfaces by default) | OUT — increment 6 | depends on these three existing first |
| analytics (throughput/aging/plate-load aggregates) | OUT — increment 7 | lowest confidence; needs event history |

---

## §3 Named decisions (with recommendations) — surface to Luke

Every decision carries a recommendation. ★ marks a genuine product-shape call worth Luke's deliberate eyeball; the rest are autonomous method-calls (the architecture + the existing pattern already rule the shape — recorded, not gated).

### D-WMS5.1 — Extend the keep-pace lens layer vs a new component; consume the store read-only. **RECOMMEND (autonomous method-call): EXTEND `primary-persona` keep-pace with three new sibling lens modules — do NOT build a new component, do NOT modify the objective-tracker store, do NOT add a field.** The architecture (§3 lens = filter+group+sort+render over L1) + the sealed `projects.py`/`relational.py` pattern already rule this. The store is consumed through its existing read-only surface only.

### D-WMS5.2 — The goals ladder: DERIVED vs a stored `objective-slug` binding. **RECOMMEND (autonomous method-call): DERIVE the ladder via the SAME alignment mechanism `prioritize.py` already uses** (`aligned_terms_from_objectives` + an item's goal-text mentioning an objective slug/subgoal). The projection carries NO `objective-slug` field (confirmed absent, §11); the architecture §2a names that field "increment add (inverse direction)" and explicitly does not require it here. Deriving reuses a sealed mechanism (Lens-1) and adds no storage. **Cost named (F2):** text-match alignment is fuzzier than a stored binding — a work item whose goal text doesn't surface-mention its objective won't ladder. Mitigation: the goals lens surfaces an "unattributed open work" tail so nothing is silently dropped, and the stored-binding upgrade is a clean later increment if alignment precision proves insufficient (RF #3). The OUTCOME (work ladders to the right goal; goals-with-no-work are named) is the AC; the match mechanism is the method.

### D-WMS5.3 — ★ waiting-on: extract-and-wrap inc-4 vs re-implement. **RECOMMEND: EXTRACT inc-4's `relational._waiting_rows` waiting-on-me-vs-others split into a SHARED helper that BOTH `relational.py` and the new `waiting_on.py` lens call — formalizing the lens WITHOUT a second implementation.** `relational.py` already computes the exact on-me (`owner_pending`) / on-others (external-party `waits_on` via the existing `waiting_on_other` query) split; a standalone waiting-on lens needs the SAME split as its whole body. Re-implementing it would be the five-surface-drift the whole WMS exists to prevent (architecture §2b). This is ★ because it is the brief's named reconciliation and a genuine shape call: the alternative (leave waiting-on AS-IS inside relational, ship no standalone lens) is defensible if Luke decides a standalone waiting-on lens adds nothing over relational's combined block — see RF #1. **My recommendation: ship the standalone lens via extraction**, because increment 6 (per-user lens choice) needs waiting-on as a NAMED selectable lens, and the extraction makes relational + waiting-on share one truth.

### D-WMS5.4 — ★ Surfacing: on-demand entry points vs always-on `TriggerKind.turn` blocks. **RECOMMEND: ship the three lenses as `render_*_block` production entry points that are NOT registered as turn contributors** — the persona renders them on demand when the question is asked, NOT every turn. Production today already registers FOUR always-on turn blocks (streams/projects/relational/intake, §11); three more would be seven-blocks-every-turn bloat. This is ★ because it is a product-surface call: it decides loam does NOT volunteer these three by default and waits to be asked (the per-user always-on CHOICE is increment 6). **My recommendation: on-demand**, because the brief explicitly says these lenses are "mostly on-demand/owner-invoked, not all-at-once-every-turn," and registering them now pre-empts increment 6's per-user choice with a hardcoded always-on default.

### D-WMS5.5 — ★ Refactor to a unified LENS protocol NOW, or keep sibling modules. **RECOMMEND: KEEP them as sibling modules this cycle; do NOT introduce a lens-protocol abstraction yet.** Five lenses now share the filter+group+sort+render shape (streams/projects/goals/plate/waiting-on), which is the threshold where an abstraction starts to pay. But the Lens-1/F4 call: the five lenses do NOT yet share enough BEHAVIOR to factor cleanly — projects derives FBM STATE, goals derives an OBJECTIVES ladder, plate is a pure prioritize-reuse, waiting-on is a state-split, streams is FBM-bound. A premature protocol would force-fit five genuinely-different filter/derive bodies behind one interface and add coordination overhead with no tighter AC (the Lens-5 stopping criterion: stop when the split adds only coordination overhead). The shared discipline they DO have — the Slice-D cap+TTL+fail-soft render + the read-only tracker factory — is already a copy-paste-stable ~30 lines, not a leaky abstraction. **Recommendation: defer the lens-protocol to a dedicated refactor increment AFTER increment 6 (when per-user lens-choice gives a concrete reason to enumerate lenses uniformly), and extract the shared render/factory helper THEN, against five proven concrete lenses.** This is ★ because "refactor now vs later" is a real architectural fork the brief asks me to call; I am calling LATER, with the trigger named (increment 6's lens-choice enumeration).

### D-WMS5.6 — ★ What "on my plate" INCLUDES by default. **RECOMMEND: on-my-plate = open items that are (a) `active` or `proposed-and-ready` (NOT `blocked`), (b) NOT waiting on an external party, (c) NOT explicitly deferred — priority-sorted by inc-4's `prioritize`.** This is ★ because it is the genuine product-shape call the brief flags: it defines what "what should I be doing" MEANS for Luke. The edge cases worth his eyeball: (1) does `owner_pending` (waiting on HIM to rule) belong on the plate, or is that the waiting-on lens's job? **My recommendation: `owner_pending` goes on the plate** — "waiting on you to decide" IS something on the user's plate to action, and excluding it would hide decisions he owes; the waiting-on lens shows the same items under a different framing (the multi-lens-over-one-model point — same item, two lenses, no duplication). (2) Do `proposed` (un-promoted, intake-pending) items appear? **Recommendation: only `active` + `owner_pending` on the plate by default; `proposed` items are not yet committed work** — but this is exactly the kind of default a per-user dial (increment 6) should later tune. Surfaced for Luke's ruling because "what counts as on my plate" is his definition to set.

---

## §4 Spec-objective placement

Binds to **AC.PO.2** of the WMS prime objective (the VALUE_PROPOSITION primary-persona test: "does this reduce the translation burden between the user's natural-language intent and AI-effective execution") via the architecture's Lens-2 statement (§1): the goals/plate/waiting-on lenses reduce the translation burden of "what am I trying to achieve / what should I do now / what am I waiting on" to a plain-language answer the user never has to assemble from machine surfaces. Ladders up through the WMS MAJOR sub-component (#84, owner-elevated TG 13656) to the loam PRIME DIRECTIVE (per-user-tuned translation: the user brings WHAT, loam owns HOW it's surfaced — the lens that fits this person, increment 6). Parent architecture §7 row-5 is the spec anchor; this plan IS that row's build-plan.

---

## §5 Sealed-component fence

| Component | Touch | Mechanism |
|---|---|---|
| `primary-persona` (SEALED) | three new `keep_pace/*.py` lens modules + a shared waiting-split helper extracted from `relational.py` + their tests + the production wiring (the on-demand entry points; NO new `TriggerKind.turn` registration) | `loam amend apply` against the manifest below — advances the existing primary-persona sidecar (follow-on, `new_component: false`) |
| `objective-tracker` (SEALED) | **NONE — consumed read-only** (`query_projection_view` / `unblocked_next` / `waiting_on_other` / `trace_to_root` + the `priority`/`status`/`parent_id` projection fields) | no manifest entry; no edit. If the build finds it needs a store-side change (a query the runtime doesn't expose, a field that doesn't exist), it HALTS (§8 #2) — it does NOT open a sealed-store amendment |
| `relational.py` (sealed within primary-persona, inc-4) | edited ONLY to extract the waiting-split helper to a shared location + import it back (behavior-preserving — relational's rendered block is unchanged) | same primary-persona amendment; the extraction is covered by relational's existing AC.REL.2 test (regression guard) + a new AC.WAIT shared-helper test |

**Fence boundary stated precisely:** every edit lands inside `primary-persona`. The objective-tracker store is read-only. The `relational.py` extraction is behavior-preserving (the existing relational block must render identically — its AC.REL.2 test is the regression fence). No edit widens the narrow read-only `TrackerClient` protocol into a write surface.

---

## §6 Acceptance criteria (outcome-shape; method-in-AC test passed on each)

Each AC states an observable OUTCOME; the method that satisfies it is the builder's call. The method-in-AC test (can the AC be satisfied by a method other than the one I have in mind?) passes on each.

**AC.GOAL — the goals lens**
- **AC.GOAL.1** — Given a real store of work items + a real `OBJECTIVES.md` with active objectives, the goals lens renders, per active objective, the open work that advances it (laddered), in ONE concise capped block. (Outcome: work appears under the right goal. Method — text-alignment vs any future stored binding — is free.)
- **AC.GOAL.2** — An active objective with NO advancing work surfaces explicitly as "nothing is currently moving this goal" — a no-work goal is NAMED, never silently omitted. (The "what goals have no work" architecture requirement.)
- **AC.GOAL.3** — Open work that ladders to NO objective is not silently dropped: it surfaces as an "unattributed open work" tail (honest-coverage — the D-WMS5.2 derivation-cost mitigation). No work item vanishes from the union of (laddered + unattributed).
- **AC.GOAL.4** — The lens fabricates NO ladder: a work item appears under an objective ONLY when a real alignment signal connects them; the lens never asserts a goal→work link that the data does not support (the honest-graph invariant, mirroring AC.REL.4).

**AC.PLATE — the on-my-plate lens**
- **AC.PLATE.1** — Given a real store, the on-my-plate lens renders a flat, priority-sorted view of exactly the items matching the D-WMS5.6 filter (active/owner_pending, not blocked, not waiting-on-others, not deferred) — a blocked item and a waiting-on-others item do NOT appear on the plate. (Outcome: the filter is correct. The filter predicate is named in D-WMS5.6; the implementation is free.)
- **AC.PLATE.2** — The plate's ordering + per-item reason are inc-4's `prioritize` output REUSED (not a second ranking): the top plate item is the top `prioritize` item among the filtered set, carrying the same transparent plain-language reason — no second priority logic exists. (The no-duplication outcome.)
- **AC.PLATE.3** — No numeric score reaches the surface; every plate item carries a plain-language reason (inherited from `prioritize` — AC.PRI.4 invariant holds through the plate lens).

**AC.WAIT — the waiting-on lens (formalized, reconciled)**
- **AC.WAIT.1** — Given a real store, the waiting-on lens renders the on-me (`owner_pending`/internal) vs on-others (external-party) split as a standalone named view, in ONE concise capped block.
- **AC.WAIT.2** — The split is computed by the SAME logic `relational.py` uses — a single shared helper produces both `relational.py`'s waiting rows AND the standalone lens's rows; there is NO second waiting-on implementation. (The reconciliation outcome — verifiable: exactly one function computes the split; both call sites consume it.)
- **AC.WAIT.3** — `relational.py`'s existing rendered block is UNCHANGED by the extraction (behavior-preserving): the inc-4 AC.REL.2 surface renders identically before/after. (The regression fence.)

**AC.LENS — the shared lens shape + surfacing discipline**
- **AC.LENS.1** — Each of the three lenses renders ONE concise block within the Slice-D char cap, fail-soft (any boundary error → empty block, the turn/render proceeds), composing the same cap+TTL+read-only-factory discipline the sealed lenses use — not three new walls of text.
- **AC.LENS.2** — None of the three lenses is registered as a `TriggerKind.turn` contributor: the per-turn surface gains ZERO new always-on blocks (verifiable: the turn-contributor registration set is unchanged; the three lenses expose on-demand `render_*_block` entry points only). (The no-bloat surfacing-discipline outcome — D-WMS5.4.)
- **AC.LENS.3** — Every render carries zero internal vocabulary: no IDs, SHAs, paths, slugs, lifecycle enums, or numeric scores reach the rendered text (the zero-internal-vocab HARD invariant, across all three lenses).

**AC.WMS5.LIVE — the outcome-altitude AC** (`outcome-altitude: true`)
- **AC.WMS5.LIVE.1** — Against a REAL objective-tracker store carrying a REAL set of work items (a dependency chain, items laddering to real objectives, an `owner_pending` item, an external-party wait) with NO pre-arranged lens/ladder/ranking state, invoking each of the three lenses' LIVE production entry points renders the correct view: the goals lens ladders the right work under the right objective AND names a no-work goal; the on-my-plate lens surfaces the right top item with `prioritize`'s reason and EXCLUDES the blocked + waiting-on-others items; the waiting-on lens splits on-me vs on-others — AND the waiting-on result is produced by the SAME shared helper `relational.py` calls (no duplicated surfacing). Exercised through the real entry points, no mocks at the store boundary.

---

## §7 Build steps (method-level guidance only — builder's call per ODD §1.1)

1. **Manifest** at `docs/plans/wms-increment-5-goals-plate-waiting-on-lenses.manifest.yaml` (paired below). BASELINE = `build/wms-increment-4` tip @ build time. Single component: `primary-persona`, `new_component: false`.
2. **Extract the waiting-split helper first** (the reconciliation, D-WMS5.3): pull `relational._waiting_rows`'s on-me/on-others split into a shared helper both modules import; re-point `relational.py` at it; confirm relational's existing AC.REL.2 test still passes (the behavior-preserving regression fence, AC.WAIT.3). Author the shared-helper test (AC.WAIT.2).
3. **Author tests before source** for each lens family (ODD/TDD): AC.GOAL.* against a fixture store + fixture OBJECTIVES.md; AC.PLATE.* against a fixture store with blocked + waiting + deferred items; AC.WAIT.* against the shared helper + a standalone-lens render; AC.LENS.* (cap/fail-soft/no-turn-registration/no-vocab); AC.WMS5.LIVE.1 against a real store via the production entry points.
4. **`goals.py`** — mirror `projects.py`: load work items read-only, derive the ladder via `aligned_terms_from_objectives` + goal-text match, group by objective, surface no-work goals + an unattributed tail, render ONE capped block. On-demand entry point; NO turn registration.
5. **`plate.py`** — mirror the filter+sort shape: load read-only, apply the D-WMS5.6 filter, pass the filtered set straight through `prioritize`, render the priority-sorted block with the inherited reasons. On-demand entry point; NO turn registration.
6. **`waiting_on.py`** — call the shared waiting-split helper, render the standalone on-me-vs-others block. On-demand entry point; NO turn registration.
7. **Wire the on-demand entry points** into the production surface WITHOUT a `TriggerKind.turn` registration (AC.LENS.2) — expose `render_goals_block` / `render_plate_block` / `render_waiting_on_block` as the persona's on-demand callables.
8. **Apply + seal**: `loam amend apply` against the manifest; advance the primary-persona sidecar.
9. **Smoke**: run the three entry points against a real seeded store; confirm AC.WMS5.LIVE.1 renders the right views with no duplication.

---

## §8 Halt triggers (abort the in-flight build + surface)

1. **No graph to lens.** If BASELINE resolves to a tree without the inc-2 work-item store + the inc-4 `prioritize.py`/`relational.py` (e.g. an accidental main-based build), HALT — there is nothing to lens over. (The §11 predecessor check is the pre-build guard.)
2. **A needed store-side change.** If a lens needs a query the runtime doesn't expose, a projection field that doesn't exist (e.g. the build decides it truly needs a stored `objective-slug` binding rather than derivation), or any store MUTATION, HALT and surface — do NOT open a sealed objective-tracker amendment inside this increment (that is a separate, store-touching cycle).
3. **Waiting-on duplication.** If the extraction (D-WMS5.3) proves harder than re-implementing and the build is tempted to write a SECOND waiting-on split, HALT — re-implementation is the explicit anti-goal (AC.WAIT.2). Surface the extraction obstacle for a method ruling rather than duplicating.
4. **`relational.py` regression.** If the extraction changes relational's rendered block (AC.REL.2 fails), HALT — the extraction must be behavior-preserving (AC.WAIT.3).
5. **Turn-surface bloat.** If a lens ends up registered as a `TriggerKind.turn` contributor (AC.LENS.2 violated — the per-turn block count would rise from four to five+), HALT — the on-demand discipline (D-WMS5.4) is load-bearing; surface before shipping an always-on default that pre-empts increment 6.
6. **Surrounding ODD violation.** If the build discovers an ODD violation in the surrounding inc-2/inc-4 code (unnamed-case code, a method-in-AC), surface it — do NOT silently extend it (the subagent-ODD-halt discipline).

---

## §9 Bookkeeping (backfill on seal)

- `docs/STATE.md` — add the wms-increment-5 seal row.
- Roadmap §8 register — record the increment-5 seal (slug + seal SHA; version derives at release time, never pre-assigned).
- Architecture `docs/design/work-management-system-architecture.md` §7 row-5 — flip "future" → BUILT with the seal SHA + the realised decision shapes (D-WMS5.2 derived-ladder, D-WMS5.3 extract-and-wrap, D-WMS5.4 on-demand, D-WMS5.5 sibling-modules-not-protocol, D-WMS5.6 plate-default). Note that the architecture's §7 had on-my-plate + waiting-on in inc-6 and goals in inc-5; this dispatch RE-BUNDLED all three into increment 5 (an owner/dispatcher scope decision) — record that re-bundling so the roadmap row count stays honest, and note increment 6 is now per-user lens-choice ONLY.
- `primary-persona` sidecar — advanced by `loam amend apply`.

---

## §10 F2 Ruthless Feedback (honest doubts + named design risks)

**RF #1 — the waiting-on duplication-vs-reconcile tension (the brief's named tension).**
- *Disagreement/tension:* a standalone waiting-on lens and inc-4's `relational.py` both answer "what's waiting on me vs others." Shipping a standalone lens that re-implements the split would be exactly the five-surface drift the WMS exists to kill (architecture §2b).
- *Evidence:* `relational._waiting_rows` (inc-4, `build/wms-increment-4:.../keep_pace/relational.py`) already computes the on-me (`owner_pending`) / on-others (external-party `waits_on` via `waiting_on_other`) split in full.
- *Alternative:* TWO paths — (a) EXTRACT the split into a shared helper both call (my recommendation, D-WMS5.3); or (b) ship NO standalone lens and let waiting-on remain a sub-block of relational. I recommend (a) because increment 6 (per-user lens choice) needs waiting-on as a NAMED selectable lens. But (b) is genuinely defensible and is Luke's call if he judges a standalone waiting-on lens adds nothing over relational's combined block — surfaced, not silently resolved.

**RF #2 — the always-on-turn-block surfacing trap (the named no-bloat concern).**
- *Disagreement:* the obvious "mirror projects.py" instinct includes mirroring its `register_*_contributor` at `TriggerKind.turn`. Doing that for three lenses takes the per-turn surface from four blocks to seven — re-bloating the exact surface the brief says not to bloat.
- *Evidence:* production wires four turn contributors today (`session_start_emitter.py` registers streams + projects + relational + intake at `TriggerKind.turn`, §11).
- *Alternative:* expose on-demand `render_*_block` entry points and DON'T register them as turn contributors (D-WMS5.4 / AC.LENS.2). Named as a halt trigger (§8 #5) so the build cannot drift into the always-on default silently.

**RF #3 — the derived-ladder precision cost.**
- *Disagreement:* deriving the goals ladder by text-alignment (no stored `objective-slug`) is fuzzier than a real binding — a work item whose goal text doesn't mention its objective won't ladder, so the goals lens can under-attribute.
- *Evidence:* the projection carries NO `objective-slug` field (§11); `prioritize`'s `aligned_terms_from_objectives` is a lowercased slug/subgoal text match.
- *Alternative:* surface an "unattributed open work" tail (AC.GOAL.3) so under-attributed work is never silently dropped, AND name the stored-binding upgrade as a clean later increment if precision proves insufficient. I recommend deriving now (reuses a sealed mechanism, no store touch); the upgrade trigger is "the unattributed tail is consistently large in real use."

**RF #4 — the architecture re-bundling (scope honesty).**
- *Disagreement:* the architecture §7 places on-my-plate + waiting-on in increment 6 and only goals in increment 5; this dispatch bundles all three into increment 5.
- *Evidence:* architecture §7 row 5 = "goals lens"; row 6 = "per-user lens choice" but the lens table (§3) lists on-my-plate + waiting-on as "Increment 6."
- *Alternative:* this is a defensible re-bundling (the three lenses are sibling derivations of equal size and the per-user CHOICE wiring is the real increment-6 substance), but I am NAMING it rather than silently absorbing it — the bookkeeping (§9) records the re-bundling so the roadmap stays honest and increment 6 is re-scoped to per-user-choice-only.

**RF #5 — the lens-protocol deferral (am I under-building?).**
- *Disagreement with my own recommendation:* five lenses sharing filter+group+sort+render is exactly the threshold where an abstraction usually pays; deferring it (D-WMS5.5) risks shipping a sixth copy-paste later.
- *Evidence:* the five lenses share the Slice-D render discipline + the read-only tracker factory (~30 lines) but differ entirely in their derive bodies (FBM STATE vs OBJECTIVES ladder vs pure-prioritize vs state-split).
- *Alternative:* defer the protocol to a post-increment-6 refactor against five PROVEN concrete lenses, extracting only the genuinely-shared render/factory helper THEN (Lens-5 stopping criterion: don't abstract until the split tightens an AC rather than adding coordination overhead). I recommend deferring, with the trigger named — but I flag this as the decision most likely to be re-litigated, and if Luke prefers the long-term-cleaner path (his stated default), extracting the shared render/factory helper THIS cycle (without a full protocol) is the middle option I'd take on his word.

---

## §11 Provenance trail (load-bearing sources, verified on the branches 2026-06-03)

- **Parent architecture:** `docs/design/work-management-system-architecture.md` — §3 lens definition (filter+group+sort+render); §3 lens table (goals/plate/waiting-on rows); §5 FBM boundary; §7 roadmap row 5; §2a the `objective-slug?` field marked "increment add"; WMS-D2 computed-not-materialized.
- **The lens pattern to mirror:** `build/wms-increment-2:framework/primary-persona/src/loam/primary_persona/keep_pace/projects.py` — the canonical filter+group+sort+render lens shape (read-only `_load_work_items` factory, Slice-D `_PROJECTS_BLOCK_CHAR_CAP`/TTL, fail-soft, `render_projects_block` + `register_projects_contributor`).
- **The base to reconcile with (inc-4):**
  - `build/wms-increment-4:.../keep_pace/relational.py` — `_waiting_rows` (the on-me/on-others split TO EXTRACT), `_unblocked_next_rows` (the prioritized-next), the read-only tracker factory, the Slice-D render discipline.
  - `build/wms-increment-4:.../keep_pace/prioritize.py` — `prioritize(items, *, weights, aligned_terms, pinned, deferred, now)` (the ranking to REUSE for plate) + `aligned_terms_from_objectives(text)` (the goal-alignment vocabulary to REUSE for the goals ladder) + `RankedItem(item, reason, score, band)`.
- **The goals substrate:** `build/wms-increment-4:.../keep_pace/objectives.py` — `Objective(slug/status/subgoals/detail_path/is_active)`, `load_objectives(text)`, `user_scope_objectives_path()`.
- **The projection (confirming NO stored ladder field):** `build/wms-increment-4:framework/objective-tracker/src/loam/objective_tracker/projection_view.py` — `ObjectiveProjection` carries `goal`/`status`/`parent_id`/`belongs_to_project`/`tagged_streams`/`priority`/`edges_out`/`edges_in`/`last_transition_at` — and NO `objective_slug`/`ladders_up_to` (grep confirmed NONE). The goals ladder MUST be derived (D-WMS5.2).
- **The surfacing-discipline evidence:** `build/wms-increment-4:.../session_start_emitter.py` — registers streams + projects + relational + intake at `TriggerKind.turn` (four always-on blocks today; the no-bloat basis for D-WMS5.4).
- **The trigger kinds:** `build/wms-increment-4:.../context_composer.py` — `TriggerKind` exposes `session`/`turn` only; there is no "on-demand" trigger, confirming on-demand lenses are render-entry-points NOT registered contributors.
- **The plan-doc shape exemplar:** `build/wms-increment-4:docs/plans/wms-increment-4-prioritization-and-relational-web.md` + its `.manifest.yaml` (schema_version 3; slug-not-number; single-component primary-persona follow-on; the §-structure this doc mirrors).
