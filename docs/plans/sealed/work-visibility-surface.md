# work-visibility surface — an always-current, self-maintaining view of loam's work + status the user can SEE without asking — plan

**Status:** sub-plan-doc (PLAN-ONLY; no code, no manifest application, no bookkeeping mutations by this drive).
**Working directory:** `/Users/lukeivers/loam` (canonical loam tree). Authored on `main` @ the BASELINE below; the build agent that picks this up works the canonical tree per the manifest fence.
**Parent doctrine:** `docs/VALUE_PROPOSITION.md` — prime objective ("per-user-tuned translation": *"The user only ever has to know what they need; loam owns how"*) + the protection side (*"having no real memory"* / *"working from missing context"*). The status-anxiety stressor IS a translation failure: today the user has to do translation work (open Telegram, compose "what's happening", wait for a render) to learn the state of *his own system*. This surface closes that — the answer becomes always-available and self-maintaining.
**Owner directive:** Telegram 13231 (2026-05-31), task #37. The named root problem is **the status-anxiety stressor** — *not knowing what is happening is itself the harm*; the surface is the fix. Greenlit: this drive designs HOW, not WHETHER.
**Predecessors (load-bearing, Tier-0 read at plan-time @ `067e3435`):**
- `framework/primary-persona/src/loam/primary_persona/tracker_context.py` @ `067e3435` — the objective-tracker context contributor. Already distinguishes **in-flight** (`_is_in_flight`), **open-loop** (`_is_open_loop`), and **owner-pending** (`_is_owner_pending`) projections, traces each chain to the value-prop root, and renders a projection block (`_render_projection_block`, AC40.* family). This is the live work-state backbone — the surface READS it, does not re-derive it.
- `framework/tools/loam/src/loam_cli/flows/cursor.py` @ `067e3435` — the position-cursor (`{flow, step, branch_state, updated_at}`; `read_cursor` / `resolve_cursor`). Supplies "which process are we in + where" with the UNRESOLVED-over-wrong-confident posture (AC.CURSOR.*). The surface reads the resolved cursor; a STALE/UNRESOLVED cursor is rendered as "between steps", never as a false position.
- `framework/orchestrator/scripts/session_surface.py` @ `067e3435` — KP7 SessionStart objective + last-state surface ("Picking up where you left off: …"; plain-language likely-next-action; AC.KP7.*). The fail-open/fail-soft lazy-import discipline (`_LEAD_IN`, best-effort cross-component reads) is the precedent the visibility surface's aggregation reuse follows verbatim.
- `framework/self-correction/src/loam/self_correction/recovery_surface.py` @ `067e3435` — the **zero-internal-vocabulary renderer** + `contains_internal_vocabulary` probe (AC.SR-RECOVER.2). The visibility surface's plain-language render composes on this probe so the rendered status carries no SHAs / AC-IDs / paths / agent-IDs / ODD vocab.
- `framework/self-correction/src/loam/self_correction/watchdog.py` @ `067e3435` — the stuck/silent-agent + dead-channel detection (AC.SR-WATCH.*). Supplies the **health signal** the surface renders ("a job looks stuck" vs "everything healthy") so the surface is not merely a passive list but answers *"is it stuck?"* — the actual anxiety question.
- `docs/plans/bootstrap-progress-statusline.md` (sealed; `hands-off-lifecycle` fence) — the DIRECT shape precedent: a renderer over a state file + Claude Code `statusLine` (`.claude/settings.json`) producing a one-line plain-English progress string refreshed at the platform's polling cadence, *"so a non-technical user knows what is happening without asking, opening logs, or running diagnostics."* The visibility surface is the steady-state generalization of the bootstrap-only statusline.
- `framework/tools/loam/src/loam_cli/flows/reinject.py` @ `067e3435` — the always-in-context re-injection carrier (SessionStart / PreCompact / UserPromptSubmit / PreToolUse → `additionalContext`; AC.REINJECT.1). The mechanism by which a status block can be made *persona-owned + always-current in-context* without the user pulling it.
**BASELINE candidate:** current `main` @ `067e3435` (`chore(seals): protection-matrix-catalogue-track-and-rows`). The builder re-baselines to the actual source-edit BASELINE at build time.
**Status-file target:** `docs/STATE.md` rollup + `docs/release-roadmap.md` + `docs/plans/loam-roadmap.md` line 103 ("Owner work-visibility window") — backfilled at seal (see §9).
**Quality bar:** dev-mode ODD/CDC; every AC outcome-shape; ≥1 outcome-altitude AC verified at a real entry-point with NO pre-arranged state.

---

## §1 — Summary / TL;DR

**What ships:** a **single always-current view of loam's work + status** — what is running now, what is queued, what is waiting on the owner, where each active process sits, and whether anything looks stuck — that the user can SEE *without asking and without waiting for a render*. The persona OWNS keeping it current; the user never pulls status.

This is an **AGGREGATION + WIRING cycle, not a new tracking system** (Lens 1 — the load-bearing design choice; §10 F2 #1). Every signal the surface shows already exists in a sealed primitive. The cycle builds (a) a deterministic **aggregator** that reads those primitives into one work-state snapshot, (b) a **plain-language renderer** composing on the existing zero-internal-vocabulary probe, and (c) the **wiring** that makes the snapshot self-maintaining and always-available across the surfaces the owner actually looks at.

Four AC families:
1. **AC.WVS-AGG.\*** — the aggregator reads the live primitives (objective-tracker in-flight/open-loop/owner-pending projections + position-cursor + watchdog health) into ONE snapshot, fail-soft per source.
2. **AC.WVS-RENDER.\*** — the snapshot renders to a plain-language status the user reads at a glance, carrying ZERO internal vocabulary, and explicitly answering the three anxiety questions: *what's happening now / what's next / is anything stuck*.
3. **AC.WVS-FRESH.\*** — the surface is **self-maintaining**: it reflects the current work-state without the user asking, refreshed on the events that change work-state (persona-owned, not user-pulled).
4. **AC.WVS-S.1 ★** — outcome-altitude: a real workspace with genuine live work-state (no pre-arranged snapshot) produces the real plain-language surface at the production entry-point.

**Key decisions baked:** this composes on the five named primitives (no re-derivation of work-state); the surface is persona-owned + self-maintaining (Lens 2); the rendered text is plain-language zero-internal-vocab (the non-tech 1.0 contract). **One central fork is OPEN and surfaced for owner ruling (§3 / §16): what the surface physically IS** — a generated file the user opens, a `/status` on-demand render, a hook-driven live in-context block, or a combination. A recommendation is given; method below the fork stays the builder's call.

**F2 on scope realism (§10):** the build is small *because* the hard part (tracking + state-distinction + plain-language probe) is already sealed. The realism risk is the opposite of under-scoping — it is over-building a "dashboard" when the correct shape is a thin aggregator over existing state. The plan fences against that explicitly (§7).

---

## §2 — Placement decisions

Per the partition rule (which sealed component owns each piece):

1. **The aggregator + renderer + surface entry-point → `primary-persona` component.** Rationale: the aggregated work-state is *the persona's own situational awareness rendered outward* — the tracker-context contributor (the in-flight/open-loop/owner-pending backbone) already lives there, and Lens 2 names this as a persona-owned toolkit capability ("a tool the persona keeps current", not a thing the user operates). The surface is the outward-facing twin of the inward `tracker_context` contributor. Placing it here keeps the read-side of work-state in one component and advances that component's existing sidecar.
2. **The watchdog health signal → READ from `self-correction` across the fence (no edit).** Rationale: `watchdog.py` is sealed; the aggregator CALLS its public health surface (the same cross-component best-effort lazy-import discipline `session_surface.py` uses). Editing `self-correction` is OUT of fence (§8 halt).
3. **The position-cursor read → READ from `loam_cli.flows.cursor` across the fence (no edit).** Rationale: `read_cursor` / `resolve_cursor` are the public surface; the aggregator consumes a resolved cursor. No edit to the flows component.
4. **The plain-language vocabulary probe → READ/REUSE `self_correction.recovery_surface.contains_internal_vocabulary` (no edit).** Rationale: the zero-internal-vocab guarantee is already a sealed, tested probe; the renderer composes on it rather than re-implementing the scan.
5. **The surface wiring (hook registration and/or `statusLine` and/or a `/status` SKILL) → settings + universal paths.** Rationale: which carrier(s) the surface rides is the central fork (§3); whichever the builder lands, the registration is a settings/`.claude/` edit admitted via universal paths, mirroring the statusline precedent and the reinject hook registration.

**No new sealed component is created.** This is an existing-component (`primary-persona`) extension that composes on four sealed primitives across their fences.

---

## §3 — Halt-and-surface BEFORE build (the central design fork)

One fork is genuinely open and is surfaced to the owner/dispatcher for ruling. The remaining method is the builder's call.

### ★ FORK F-1 (OPEN — owner/dispatcher rules): what is the surface, PHYSICALLY?

The surface SHAPE is the one genuinely low-confidence decision (Lens 4 — loosen here). Options, weighed against: how non-technical the eventual user is (this is also a 1.0 feature for non-tech users, not just Luke), token cost, and whether it self-maintains vs needs persona attention.

- **(a) Always-current generated status file the user opens** (e.g. a `STATUS.md` / `.loam/status.md` regenerated by a hook on the events that change work-state). *Pros:* zero in-context token cost; survives across sessions; the user opens it any time on any surface (terminal, Telegram attachment, the Claude app, a future Tailscale/iOS view per the roadmap row); self-maintaining via the hook. *Cons:* the user must remember it exists and open it; not pushed.
- **(b) On-demand `/status` render** (a SKILL the persona/user invokes that renders the snapshot fresh). *Pros:* always fresh at read-time; discoverable; cheap. *Cons:* it is a PULL — the user still has to ask, which is the exact translation-work the prime objective says to remove. Fails the "without asking" test on its own.
- **(c) Hook-driven live in-context block** (the snapshot re-injected as `additionalContext` on the reinject carrier's events, so the persona always *has* current work-state and renders it conversationally without being asked). *Pros:* truly persona-owned + zero user action; the persona can proactively say "still running X, Y is next" because it always holds current state. *Cons:* per-turn in-context token cost; in-context only (no out-of-band surface for when the user is away from the session).
- **(d) Combination.** A generated file (a) as the durable always-openable artifact + the hook-driven in-context block (c) as the persona's live awareness, sharing ONE aggregator. The `/status` render (b) falls out for free as a thin command over the same snapshot.

**RECOMMENDATION — (d), with (a)+(c) as the load-bearing pair and (b) as a free thin wrapper.** Reasoning, signal-weighted:
- **Prime-objective test (decisive):** the surface must answer *without the user asking*. (b) alone fails this (it is a pull). (a) is openable-without-asking but not pushed. (c) is the only option where the persona *proactively* keeps the user current. The combination gives both the durable openable artifact AND the proactive in-context awareness.
- **Non-tech-user signal:** a non-technical user away from a terminal needs a *thing they can open* (a file an attachment can carry) more than an in-context block they only see mid-session. (a) is the surface that scales to the roadmap's "beyond Telegram (Tailscale/iOS)" line. So (a) is non-optional for the 1.0 audience.
- **Token-cost signal:** (a) is free in-context; (c) costs per-turn. Keeping (c) thin (a few lines, not a dashboard) and reusing the existing reinject carrier bounds the cost. The aggregator is shared, so the combination is NOT three separate builds — it is one snapshot with three thin presenters.
- **Self-maintenance signal:** both (a) and (c) self-maintain via hooks; neither needs the user to operate it. This is the Lens-2 requirement.

The builder MAY ship (a)+(c) first and defer (b) if scope realism demands, but the **aggregator must be a single shared snapshot** regardless of how many presenters ride it (this is the anti-fragmentation invariant — §7 / §8). **Owner/dispatcher: rule on whether (d) is the target, or narrow to a single presenter.** If unruled, the builder defaults to (d)'s shared-aggregator core with (a)+(c) as the first presenters.

### Surfaces I record + name autonomously (no owner ruling needed)
- The aggregator is deterministic, no-LLM (`feedback_no_anthropic_api_key`): the snapshot is a pure read over on-disk state, not a model call.
- Cross-component reads are best-effort lazy-imported + fail-soft (the `session_surface.py` precedent): a broken/missing source degrades to "that part unknown", never breaks the surface or the host hook.
- The rendered surface routes through the existing `contains_internal_vocabulary` probe before it is ever shown (the non-tech contract is a HARD invariant, not best-effort).

---

## §4 — Spec-objective placement

- **Binds to:** AC.PO.1 + AC.PO.2 (the two VALUE_PROPOSITION tests — the prime objective per `feedback_value_proposition_as_prime_objective`). Specifically the **translation side**: the user does zero translation work to learn the state of his own system (today he composes + sends + waits; the surface removes all three). And the **protection side**: it guards the *"working from missing context"* + *"no real memory"* failure modes by making current work-state always visible rather than reconstructed-on-ask.
- **Ladders up via:** the `primary-persona` component's existing AC40.* objective-surfacing family (the inward contributor) → this is its outward-facing twin → AC.PO.1.
- **Roadmap row:** `docs/plans/loam-roadmap.md` line 103 ("Owner work-visibility window — Live view of current/queued/in-flight work beyond Telegram… reading live kernel state. Early QoL win — its only hard dep is 'live state exists,' which the kernel produces"). The hard dep is satisfied: the tracker, cursor, and watchdog all produce live state @ `067e3435`.

---

## §5 — Acceptance criteria

AC IDs are scope-descriptive (`feedback_scope_descriptive_ac_ids`). Each AC is outcome-shape; the method-in-AC test (can it be satisfied by a method other than the one I have in mind?) passes for every row.

| AC ID | Outcome (what must be observably true) | Verification shape (builder's method) |
|---|---|---|
| **AC.WVS-AGG.1** | A single aggregator reads the live work-state into ONE snapshot whose contents distinguish, at minimum: work running NOW, work QUEUED, work WAITING ON THE OWNER, and (where a flow is active) WHERE that process sits. The state-distinctions derive from the existing tracker projections (in-flight / open-loop / owner-pending) + the resolved position-cursor — the aggregator does not re-derive them. | A test drives the aggregator against a workspace whose tracker carries projections in ≥2 distinct states + an active cursor; the snapshot reflects each state in its correct bucket. |
| **AC.WVS-AGG.2** | Every source read is fail-soft: a missing / broken / unresolved source (e.g. an UNRESOLVED cursor, an absent tracker DB, a watchdog that errors) degrades that part of the snapshot to "unknown" and NEVER breaks the snapshot or the host hook. | A test removes/corrupts each source in turn; the aggregator still returns a snapshot, with the broken part marked unknown, exit 0. |
| **AC.WVS-AGG.3** | The snapshot carries a health signal sourced from the watchdog: when a job is stuck/silent or a channel is dead, the snapshot reflects "something looks stuck" (vs "healthy"); the surface thereby answers *"is it stuck?"*, not merely *"what is there?"*. | A test with a watchdog reporting a stuck condition produces a snapshot whose health field is non-healthy; a clean watchdog produces healthy. |
| **AC.WVS-RENDER.1** | The snapshot renders to a plain-language status a non-technical reader understands at a glance, explicitly answering the three anxiety questions — *what's happening now / what's next / is anything stuck* — in plain English. | A test asserts the rendered text contains a now / next / health statement in plain prose against a populated snapshot. |
| **AC.WVS-RENDER.2** | The rendered surface carries ZERO internal vocabulary (no stack traces, AC-IDs, commit SHAs, file paths, agent-IDs, slugs, or ODD/methodology vocabulary), verified by the existing `contains_internal_vocabulary` probe. A render that cannot avoid leaking an internal token is a halt condition, not best-effort. | A test renders against a snapshot whose underlying state contains internal tokens (a SHA-named flow, a path) and asserts the probe finds NO internal vocabulary in the output. |
| **AC.WVS-FRESH.1** | The surface is self-maintaining: it reflects the CURRENT work-state without the user asking. After a work-state change (an objective starts / completes / moves to owner-pending, or the cursor advances), the surface reflects the new state on the next refresh event — no user pull required. | A test mutates work-state, fires the refresh entry-point, and asserts the surface content changed to match. |
| **AC.WVS-FRESH.2** | The surface is persona-owned, not user-operated: the refresh is driven by the events that change work-state (the persona's own lifecycle), not by a command the user must run. (Whether the carrier is a file-regen hook, an in-context re-inject, or both is FORK F-1; this AC fixes the *self-maintaining* outcome, not the carrier.) | A test verifies the refresh entry-point is invoked by a work-state-change / lifecycle event path, with no user-issued command in the trigger path. |
| **AC.WVS-S.1 ★** *(outcome-altitude:true)* | A REAL workspace carrying genuine live work-state (no pre-arranged snapshot, no hand-fed status string) produces the real plain-language surface at the production entry-point: it names the current work + what's next + whether anything looks stuck, in plain English, with zero internal vocabulary, sourced end-to-end from the live tracker + cursor + watchdog. A STUB-class test (pre-built snapshot, hand-fed status text, mocked sources) does NOT satisfy this. | A test stands up a workspace with real tracker projections + a real cursor + a real watchdog reading, invokes the production surface entry-point with NO pre-arranged in-memory state, and asserts the live-sourced plain-language surface. |

**Ladder-up:** every AC ladders to the `primary-persona` AC40.* objective-surface family → AC.PO.1 + AC.PO.2 (§4). **Outcome-altitude:** AC.WVS-S.1 is the required `outcome-altitude:true` AC (`feedback_test_outcome_altitude_required`), driving the real entry-point with no pre-arranged state.

---

## §6 — Build steps (method-level guidance; builder's call per ODD §1.1)

The dispatch carries scope; this section is guidance the builder may adapt. The exact module layout, function names, and presenter wiring are the builder's call.

1. **Manifest:** `docs/plans/work-visibility-surface.manifest.yaml` (paired; §below). Component fence: `primary-persona` (existing — advance sidecar). Cross-fence READS on `self-correction` (watchdog + recovery_surface probe), `loam_cli.flows.cursor`, and `orchestrator` (the session_surface precedent is reference-only, not edited).
2. **Aggregator (AC.WVS-AGG.\*):** a deterministic, no-LLM reader producing one work-state snapshot from the tracker projections + resolved cursor + watchdog health. Best-effort lazy-import each source (the `session_surface.py` fail-soft discipline). Tests authored per AC family BEFORE wiring (plan-before-code; TDD).
3. **Renderer (AC.WVS-RENDER.\*):** a pure function snapshot → plain-language now/next/health text, routed through `contains_internal_vocabulary` before return. Tests assert the three anxiety-question answers + zero-internal-vocab.
4. **Presenter wiring (AC.WVS-FRESH.\* + FORK F-1):** per the owner's F-1 ruling — the generated-file regen hook (a) and/or the reinject-carried in-context block (c) and/or the `/status` thin wrapper (b). Registration via settings / `.claude/` (universal paths) mirroring the statusline + reinject precedents. The SHARED-AGGREGATOR invariant holds regardless of presenter count.
5. **Outcome-altitude smoke (AC.WVS-S.1):** one real run in a cold workspace with genuine tracker/cursor/watchdog state → the live plain-language surface, no pre-arranged state.
6. **Apply / seal / smoke:** `loam amend apply` then `loam amend seal` per the manifest (`feedback_dispatch_explicit_loam_amend_apply`); HARD smoke only if this lands as a minor's last cycle (`feedback_hard_smoke_per_minor_before_publish`) — otherwise local seal.

---

## §7 — Out of scope (deferred)

- **A net-new tracking system / state store.** The surface READS existing state; it never becomes a second source of truth. (Anti-fragmentation invariant; §10 F2 #1.)
- **A graphical dashboard / web UI / Tailscale/iOS app.** The roadmap names beyond-Telegram surfaces (Tailscale/iOS) as the *eventual* consumers; this cycle ships the always-current *artifact + in-context surface* those future views will read. Building the iOS/Tailscale view is a later cycle.
- **Editing any sealed primitive** (watchdog, recovery_surface, cursor, session_surface). The cycle CALLS their public surfaces; modifying them is out of fence (§8).
- **The adaptive user-model's exposure/tone modulation** (task #34) — the surface renders plain-language by default; per-user verbosity tuning rides the user-model separately.
- **Whichever F-1 presenter the owner defers** (e.g. the `/status` wrapper) — deferrable to a follow-on without re-opening the aggregator.

---

## §8 — Halt triggers (abort the build + surface)

1. **A source-read would require EDITING a sealed primitive** (watchdog / recovery_surface / cursor / session_surface) rather than calling its public surface → halt; that is out of fence.
2. **The renderer cannot satisfy zero-internal-vocab** for some real snapshot (the probe finds a token it cannot abstract) → halt and surface; the non-tech contract is a HARD invariant, not best-effort (mirrors AC.SR-RECOVER.2's halt posture).
3. **The aggregator would need to re-derive work-state** the tracker already owns (i.e. the existing projections are insufficient and a NEW state-distinction is required) → halt; that is a tracker-schema question (a different component's fence), not a visibility-surface decision.
4. **The shared-aggregator invariant would be violated** (a presenter wants its own divergent state read) → halt; one snapshot, many thin presenters.
5. **FORK F-1 is unruled AND the builder's default (d / shared-core + a+c) is materially more expensive than a single presenter would be** → halt and surface the cost before building all three.

---

## §9 — Bookkeeping (backfilled at seal)

- `docs/STATE.md` — rollup line for the work-visibility surface cycle.
- `docs/release-roadmap.md` — note the cycle in the active-minor lineage.
- `docs/plans/loam-roadmap.md` line 103 — mark the "Owner work-visibility window" row built.
- Parent §14 method-decision register (in this plan) — populated by the builder at build time with D-F1.\* (the F-1 presenter ruling) + D-build.\* decisions; SHAs backfilled at seal via `loam amend seal --plan-doc`.

---

## §10 — F2 Ruthless Feedback (honest doubts + named risks)

1. **The load-bearing design call — this is a WIRING cycle, and the risk is over-building (named + fenced).** *Disagreement with the implicit "window/dashboard" framing:* the word "window" (Telegram 13231) suggests a built thing-to-look-at. *Evidence:* every signal the surface needs already exists sealed — `tracker_context.py` distinguishes in-flight/open-loop/owner-pending and chains to root; `cursor.py` gives position; `watchdog.py` gives health; `recovery_surface.py` gives the plain-language probe; `bootstrap-progress-statusline` already proved the renderer-over-state-file + `statusLine` shape for the exact same "is it stuck?" anxiety. *Alternative:* frame + build this as a thin AGGREGATOR + renderer over existing state, NOT a dashboard. The plan is fenced to that (§7 out-of-scope #1/#2; §8 halt #3/#4). Building a parallel tracker would be the failure mode.
2. **Is the owner-pending bucket the real anxiety reducer?** A large slice of status-anxiety is *"is it waiting on ME and I don't know?"* The tracker already has `_is_owner_pending`; the surface MUST render that bucket prominently (AC.WVS-AGG.1 names it), or it will reduce "what's running" anxiety while leaving "am I blocking it" anxiety intact. Named so the builder weights the owner-pending bucket in the render, not just in the snapshot.
3. **The "is it stuck?" answer is only as good as the watchdog.** AC.WVS-AGG.3 routes the health signal through the watchdog — but if the watchdog is conservative (few false-positives, some false-negatives), the surface will sometimes say "healthy" while a job is wedged. This is acceptable for v1 (a false "healthy" is no worse than today's no-signal), but it means the surface must NOT over-claim certainty — render "no problems detected" rather than "everything is fine". Named for the renderer's wording.
4. **In-context token cost of presenter (c) is a real recurring cost.** If F-1 lands (c), every turn pays for the in-context block. Mitigation is to keep it thin (now/next/health, ~3 lines) and ride the existing reinject carrier. If the owner is cost-sensitive, narrowing to (a)-only (generated file) is the cheaper ruling — surfaced in F-1.
5. **1.0 acceptance-smoke dependency (SURFACED, not buried).** Task #48 is the loam 1.0 non-tech-user end-to-end acceptance smoke (3 variants). A self-maintaining work-visibility surface is plausibly a variable the 1.0 smoke should assert — a non-tech user mid-build should be able to SEE what's happening as part of the end-to-end gate. *This cycle does NOT make that an AC* (the 1.0 smoke is its own cycle and owns its variables), but the dependency is named here so the 1.0-smoke author wires this surface in rather than re-discovering it. Flagged per the dispatch's explicit instruction.

---

## §11 — Provenance trail

- Owner directive + root problem (status-anxiety stressor): Telegram 13231 (2026-05-31); task #37.
- Prime objective + the two tests this binds to: `docs/VALUE_PROPOSITION.md` (translation side + protection side).
- Live work-state backbone (in-flight/open-loop/owner-pending + chain-to-root + render block): `framework/primary-persona/src/loam/primary_persona/tracker_context.py` @ `067e3435` (`_is_in_flight` / `_is_open_loop` / `_is_owner_pending` / `_render_projection_block`; AC40.* family; `test_AC40_1_in_flight_non_empty.py`).
- Position ("which process + where", UNRESOLVED-over-confident posture): `framework/tools/loam/src/loam_cli/flows/cursor.py` @ `067e3435` (`read_cursor` / `resolve_cursor`; AC.CURSOR.*).
- Plain-language renderer + zero-internal-vocab probe: `framework/self-correction/src/loam/self_correction/recovery_surface.py` @ `067e3435` (`contains_internal_vocabulary`; AC.SR-RECOVER.2).
- Stuck/dead-channel health signal: `framework/self-correction/src/loam/self_correction/watchdog.py` @ `067e3435` (AC.SR-WATCH.*).
- Aggregation fail-soft + plain-language-next-action precedent: `framework/orchestrator/scripts/session_surface.py` @ `067e3435` (KP7; AC.KP7.*).
- Always-in-context carrier: `framework/tools/loam/src/loam_cli/flows/reinject.py` @ `067e3435` (AC.REINJECT.1).
- Direct shape precedent (renderer-over-state-file + `statusLine`, same "is it stuck?" anxiety, non-tech audience): `docs/plans/bootstrap-progress-statusline.md` (sealed; `hands-off-lifecycle` fence).
- Roadmap row + the "live state exists" hard-dep satisfaction: `docs/plans/loam-roadmap.md` line 103.
- BASELINE: `067e3435` (`chore(seals): protection-matrix-catalogue-track-and-rows`).

---

## §14 — Method-decision register (populated at build time; SHAs backfilled at seal)

- **D-F1.1** — the FORK F-1 presenter ruling actually built (a / b / c / d, or owner-narrowed). *Pending owner ruling + builder record.*
- **D-build.1** — aggregator module layout + the snapshot dataclass shape. *Builder's call.*
- **D-build.2** — exact cross-component public surfaces called on watchdog + cursor + tracker. *Builder's call.*
- **D-build.3** — presenter registration mechanism(s) per the F-1 ruling. *Builder's call.*

---

### Commit SHAs

- Amendment commit: `39d0e98a8ff9f340825083400cfcc1e2817531a7` —
  `chore(amend): work-visibility-surface manifest+apply — primary-persona BASELINE+sidecar bump to 1b400bb`
- Seal commit: `3951f2ee38ce30a00325ba5d6a9cc720b17bde0f` —
  `chore(seals): work-visibility-surface — primary-persona at 39d0e98`
## §15 — Backwards-compat verification

- The existing `primary-persona` AC40.* tracker-context contributor and its tests stay GREEN (the outward surface ADDS a reader; it does not change the inward contributor).
- The existing `pos_session_start.py` / `session_surface.py` behaviour is PRESERVED (referenced as a precedent; not edited).
- No sealed primitive is modified; all four cross-component dependencies stay at their sealed surfaces.

---

## §16 — Halt-and-surface findings (raised at plan-authoring)

- **★ FORK F-1 (OPEN — owner/dispatcher rules):** what the surface physically IS — generated file (a) / on-demand `/status` (b) / hook-driven in-context block (c) / combination (d). **Recommendation: (d)** with (a)+(c) load-bearing and (b) a free thin wrapper, on a SHARED aggregator. Full reasoning + signal-weighting in §3. If unruled, builder defaults to (d)'s shared-core with (a)+(c) first.
- **Surfaced dependency (not a fork):** the loam 1.0 acceptance smoke (#48) plausibly wants this surface as a variable; named in §10 #5 so the 1.0-smoke author wires it in. Not made an AC of this cycle.
- **No locked-decision contradiction, no method-in-AC I could not reframe, no sealed-component edit required** — the three other halt-and-surface triggers did not fire.

# work-visibility surface — an always-current, self-maintaining view of
loam's work + status the user SEES without asking — apply ladder

Per `docs/plans/work-visibility-surface.md` and the prime objective
`docs/VALUE_PROPOSITION.md` (the translation side — the user does ZERO
translation work to learn the state of his own system — and the
protection side — guarding "working from missing context" / "no real
memory" by making current work-state always visible rather than
reconstructed-on-ask). Owner directive Telegram 13231, task #37: the
named root problem is the STATUS-ANXIETY STRESSOR — not knowing what is
happening is itself the harm; the surface is the fix.

Plan: `docs/plans/work-visibility-surface.md`.

Scope (per plan §2 + §7): an AGGREGATION + WIRING cycle (NOT a new
tracking system — plan §10 F2 #1). EXTEND the `primary-persona`
component (the outward-facing twin of its inward tracker-context
contributor) and COMPOSE on four sealed surfaces, READ-ONLY:

  1. Aggregator. A deterministic, no-LLM reader
     (feedback_no_anthropic_api_key) that reads the EXISTING tracker
     projections (in-flight / open-loop / owner-pending, chained to the
     value-prop root — AC40.*) + the resolved position-cursor
     (read_cursor / resolve_cursor — which process + where, with the
     UNRESOLVED-over-confident posture) + the watchdog health signal
     (stuck/silent-agent + dead-channel — the "is it stuck?" answer)
     into ONE snapshot. Every source is best-effort lazy-imported +
     fail-soft (the session_surface.py precedent): a broken/missing/
     UNRESOLVED source degrades to "unknown", never breaks the snapshot
     or the host hook.
  2. Plain-language renderer. The snapshot renders to a status a
     non-technical reader understands at a glance, explicitly answering
     the three anxiety questions — what's happening now / what's next /
     is anything stuck — and carrying ZERO internal vocabulary, routed
     through the EXISTING contains_internal_vocabulary probe. A render
     that cannot avoid leaking an internal token is a HALT, not
     best-effort (mirrors AC.SR-RECOVER.2's halt posture).
  3. Self-maintaining presenter wiring (FORK F-1 — owner-ruled). The
     surface is persona-owned, not user-pulled: it reflects current
     work-state without the user asking, refreshed on the events that
     change work-state. FORK F-1 (RECOMMENDATION (d)): a generated
     status file the user opens (durable, beyond-Telegram-ready) + a
     hook-driven in-context block (proactive persona awareness) on a
     SHARED aggregator, with an on-demand render falling out as a thin
     wrapper. One snapshot, many thin presenters (the anti-fragmentation
     invariant).

AC families:

  - AC.WVS-AGG.1 — ONE aggregator snapshot distinguishes running-now /
    queued / owner-pending / position, sourced from the existing tracker
    projections + resolved cursor (NOT re-derived).
  - AC.WVS-AGG.2 — every source read is fail-soft: missing/broken/
    UNRESOLVED degrades to "unknown", never breaks the snapshot/host hook.
  - AC.WVS-AGG.3 — the snapshot carries a watchdog-sourced health signal
    so the surface answers "is it stuck?", not just "what's there?".
  - AC.WVS-RENDER.1 — renders plain-language now/next/health a
    non-technical reader understands at a glance.
  - AC.WVS-RENDER.2 — ZERO internal vocabulary (verified by the existing
    contains_internal_vocabulary probe); a leak is a HALT.
  - AC.WVS-FRESH.1 — self-maintaining: reflects current work-state
    without the user asking; a change shows on the next refresh event.
  - AC.WVS-FRESH.2 — persona-owned: refresh driven by work-state-change /
    lifecycle events, not a user command (carrier = FORK F-1).
  - AC.WVS-S.1 ★ (outcome-altitude) — a REAL workspace with genuine live
    work-state (no pre-arranged snapshot / hand-fed status / mocked
    sources) produces the real plain-language surface at the production
    entry-point, sourced end-to-end from the live tracker + cursor +
    watchdog. STUB-class does NOT satisfy it
    (feedback_test_outcome_altitude_required).

Method-level choices are the builder's call per ODD §1.1; the plan fixes
the aggregation-not-tracking scope, the composition on the four named
sealed surfaces, the AC set, and the SHARED-aggregator invariant — not
the implementation.

The LOAD-BEARING design (plan §10 F2 #1): this is a WIRING cycle, and the
risk is OVER-building a dashboard when the correct shape is a thin
aggregator over existing state. Every signal already exists sealed; the
bootstrap-progress-statusline cycle already proved the
renderer-over-state-file + statusLine shape for the exact same "is it
stuck?" anxiety. Building a parallel tracker is the failure mode — fenced
out (plan §7 / §8 halt #3/#4). Named secondary risks: the owner-pending
bucket must render prominently (a large slice of the anxiety is "is it
waiting on ME?"); the health render must say "no problems detected" not
"everything is fine" (the watchdog is conservative); presenter (c)'s
per-turn in-context cost is bounded by keeping it thin.

Surfaced dependency (plan §10 #5): the loam 1.0 acceptance smoke (#48)
plausibly wants this surface as a variable; named so the 1.0-smoke author
wires it in. NOT made an AC of this cycle.

Predecessor:
  - 067e3435 — main tip @ plan-authoring
    (protection-matrix-catalogue-track-and-rows seal).

BASELINE 067e3435 (re-baselined by the builder to the actual source-edit
commit). EXISTING-component fence on `framework/primary-persona/` (+ the
hooks/ and scripts/ prefixes); the sidecar is ADVANCED at this seal
(prior seal exists). Cross-component READS on self-correction (watchdog +
recovery_surface probe), loam_cli.flows.cursor, and the orchestrator
precedent — none edited.
