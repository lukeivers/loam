# N4 — MVP user-model + config (the adaptive interaction-model's first real brick)

**Status:** sub-plan-doc, PLAN-ONLY (plan-before-code). **Research-grade** —
this is the FLAGSHIP pillar-1 engine's first slice (the per-user-tuned-translation
engine). The genuinely-owner-call shapes are surfaced as **forks-with-recommendations**;
the dispatcher is in FULL-AUTONOMY and rules them fast — this plan does NOT
design for an owner round-trip, but every fork carries a stated recommendation
so the ruling is a yes/no on a default, not an open question.
Authored 2026-05-31.
**Working directory:** `/Users/lukeivers/loam/`.

**Parent plans:**
- `docs/plans/loam-roadmap.md` §4 row **N4** ("MVP user-model + config (v-next P1.5) — FLAGSHIP pillar 1, first slice"; critical path `N1 → N3 → N4 → Phase 3`). N4 is the next unblocked kernel slice — N3 (onboarding/init) seeds the state N4 adapts.
- `docs/plans/loam-vnext-build-plan.md` Phase-1 **P1.5** (the user-model slice).
- `docs/design/adaptive-interaction-model.md` — **THE flagship design.** N4 builds its **MVP cut** (design §8 "MVP" table: AIM-0 already done by N3; AIM-1 read-path, AIM-2 enforce-path, AIM-3 explicit-statement + inspect). The design's **Backlog** (AIM-4..8) is the explicit LATER remainder — OUT of N4's fence (§7).

**Predecessors (load-bearing prior seals + artefacts, Tier-0 on disk 2026-05-31):**
- `f1f6116` — **`main` HEAD**: carries the full kernel + onboarding (N3 sealed at `74e6103`/`96aae8a` — the seed-writer that writes `~/.claude/INTERACTION-MODEL.md` at `confidence: prior`). **This is the BASELINE N4 evolves in place on.**
- **N3 seed-writer** (`framework/workspace-bootstrap/src/loam/workspace_bootstrap/seed_writer.py`, live on `main`): `render_interaction_model()` writes the exact AIM matrix N4 reads — markdown `## <area>` headers over `AIM_AREAS = (harness-mechanics, code-and-builds, their-domain-work, ops-and-money, decisions-and-tradeoffs, default)`, each area carrying four `axis: { value: <v>, confidence: prior, evidence: [] }` lines for axes `(technical-exposure, autonomy, tone, learning-appetite)`. The openness-biased defaults are `_OPEN_DEFAULTS` with the `_CAUTIOUS_AUTONOMY_AREAS = (ops-and-money, decisions-and-tradeoffs)` autonomy floor at `surface`. **N4 reads this file; it does NOT re-seed or re-shape it.** The matrix file format IS the read contract — N4's parser binds to it.
- **The live keep-pace UserPromptSubmit hook** (`framework/hands-off-lifecycle/hooks/keep_pace/user_prompt_submit.py`): the `contributors()` list of `Contributor(name, fn(envelope) -> Optional[str])` callables, run fail-open through `run_chain`, emitting merged `additionalContext`. **This is the live seam N4's read-path composes on** — N4 adds ONE new contributor to this list; it does NOT add a new hook (Lens 1).
- **The KP1 work-anchor** (`framework/primary-persona/src/loam/primary_persona/keep_pace/work_anchor.py` + `retrieval.py`): `WorkAnchor{prompt, objective_texts, subgoals, last_topic}` already computed every turn inside KP1. **N4's area-classifier maps this already-built anchor → an area slug** — it does NOT recompute the anchor.
- **The live KP9 draft-gate** (`framework/hands-off-lifecycle/hooks/keep_pace/draft_gate.py`): the PreToolUse register/jargon lint (Layer-1 jargon-leak + Layer-2 register judge). **N4's enforce-path parameterizes its threshold by the active area's `technical-exposure` cell** (design §4a step 3) — see fork D-N4.2.
- **The FBM rule-weighting slice** (`docs/plans/fbm-rule-weighting-slice-plan.md`, B1): added `weight: <int 1–100>` + `pinned: true` optional corpus-doc frontmatter (`BASELINE_WEIGHT = 50` no-op default), read in `read_corpus_docs` → boosts retrieval relevance. **N4 is the home for AUTO-weighting** — inferring a sensible weight + surfacing it for confirm (rather than the user hand-editing frontmatter). The mechanism (the `weight` field) is built; N4 adds the *infer + surface-for-confirm* layer (the prior "B2 fold").
- `docs/design/adaptive-interaction-model.md` §6.1 — the **G5 pre-ruled** openness-default revision of `feedback_abstraction_first_default.md` (substance always exposed; only vocabulary adapts). **PRE-RULED in this dispatch — not re-opened** (§3.G5).

**BASELINE (pre-build tip):** `f1f6116` (current `main` HEAD).
**Status-file target:** `<workspace>/.scratch/claude-output/n4-user-model-status.md` (builder writes build progress here).
**Quality bar:** the **REAL live `user-prompt-submit` hook**, given a seeded `INTERACTION-MODEL.md` and a turn whose work-anchor points at a known area, **actually injects that area's exposure/autonomy cell** into the turn's `additionalContext` — verified at the live entry-point (a real envelope through `main()` / the registered contributor), not a unit test of an inner classifier function. Fail-open is preserved: a missing/garbled matrix returns the openness prior and the turn proceeds exactly as today (no regression to the keep-pace chain).

**Scope-tightness (F4):** TIGHT where the design + N3 already settled it (the matrix shape is fixed by the seed-writer; the read-path rides the live hook; openness-default is pre-ruled G5; the MVP cut is design §8). FORKED-with-recommendation where it is a genuine method/product call the design left open (the area-classifier mechanism; whether enforce-path lands in N4 or defers; how explicit-override locks; the auto-weight inference confidence). Method stays the builder's call; this plan prescribes no files or symbols beyond naming the live seams it composes on.

---

## §1. Summary / TL;DR

N4 ships the **smallest adaptive layer** that makes loam's behaviour respond to
*this* user per area: it **reads the openness-biased matrix N3 seeded** and
**injects the right per-area cell onto the live keep-pace hook every turn**, so
the persona's exposure / autonomy / tone actually adapts to what the matrix
holds — plus the two paths that let the user *drive* the matrix directly
(explicit-override and plain-language inspect), and the home for **FBM rule
auto-weighting** (infer a rule's weight + surface it for confirm).

This is the **per-user-tuned-translation engine's first real brick** (the PRIME
DIRECTIVE / Lens 0): N3 built the front door (seed the prior); N4 makes the
prior *do something* and gives the user the controls. Everything that
auto-LEARNS from behaviour — the signal counters, hysteresis, fast-down-on-distress,
the weekly re-eval + drift judge, the tone + learning-appetite axes — is the
**LATER remainder** (design §8 Backlog AIM-4..8) and is explicitly OUT (§7).

**AC families:**
- **AC.UM.READ.*** — the read+inject path on the live hook (the load-bearing brick + the outcome-altitude AC).
- **AC.UM.AREA.*** — the work-anchor → area classification.
- **AC.UM.OVR.*** — explicit-override (user states a preference → cell hard-set, confidence bumps).
- **AC.UM.INSP.*** — plain-language inspect ("show me how you're set for X").
- **AC.UM.WT.*** — FBM rule auto-weighting (infer a weight + surface for confirm).
- **AC.UM.FENCE.*** — the MVP fence (the LATER engine is provably absent — auto-learn cells move ONLY by explicit statement, never by behavioural signal, in this slice).

**Key decisions baked (G5 + the design):** exposure default = OPEN (substance
always exposed, only vocabulary adapts — pre-ruled); compose on the live hook
+ the N3-seeded matrix (don't rebuild either); deterministic lookup, not
model-decides (design §4b); fail-open to the openness prior on any matrix error.

**F2 on scope realism (§10):** the read+inject path is high-confidence and small
(one contributor on a live hook reading a file the seed-writer's format pins).
The **area-classifier is the one real risk** — the design (§7 final flag) calls
signal-classification accuracy "unverified," and the work-anchor→area map is the
N4 incarnation of that risk. The plan keeps it *coarse + fail-open-to-default*
and recommends the deterministic keyword/objective-tag map (D-N4.1) precisely
so the brick lands without resting on an unproven classifier.

---

## §2. Placement decisions (per partition rule)

| Item | Placement | Rationale |
|---|---|---|
| The AIM matrix file (`~/.claude/INTERACTION-MODEL.md`) | **Already placed by N3** — read-only input to N4. | N3's seed-writer owns the WRITE + format. N4 must NOT re-seed or re-shape; it binds a READER to the existing format (predecessor contract). |
| The area-classifier + cell-lookup-and-inject | **New contributor in the live `keep_pace` hook chain** (`framework/hands-off-lifecycle/hooks/keep_pace/`), reading the work-anchor the KP1 component already computes. | Lens 1 — compose on the live `contributors()` seam, not a new hook. The contributor shape (`fn(envelope) -> Optional[str]`, fail-soft) is the established contract. |
| The work-anchor→area map | **Reads the existing `WorkAnchor`** (primary-persona keep_pace); the map itself is N4-new. | The anchor is already built every turn (KP1); N4 adds only the classification layer over it (no anchor recompute). |
| Enforce-path (draft-gate threshold parameterized by cell) | **Live KP9 `draft_gate.py`** — see fork **D-N4.2** (recommend: INCLUDE in N4). | The design (§4a step 3 / AIM-2) places it at the live gate. Fork is whether it lands in N4 or defers; recommendation INCLUDE because it's the seam that makes the model structural not advisory, and it's small (a threshold lookup). |
| Explicit-override + inspect | **Persona behaviour + a matrix WRITE path** (hard-set a named cell; render the matrix in prose). | The user's own statement is the highest-confidence signal (design §5) and needs no classifier — it carries early personalization safely (design §7 flag). The write path reuses the seed-writer's file format. |
| FBM rule auto-weighting (infer + surface) | **Composes on the B1 `weight:` frontmatter mechanism** (already built); N4 adds the infer + surface-for-confirm layer. | B1 built the `weight` field + boost math; N4 owns the *adaptive* half (infer a value, surface for confirm) — the config arm of "user-model + config." |
| Behavioural signal counters / hysteresis / distress fast-down / tone+learning-appetite axes / weekly re-eval + drift judge | **OUT — the LATER remainder** (design §8 AIM-4..8; roadmap §5a "Full adaptive user-model … remainder"). | The MVP fence. Cells move ONLY by explicit statement in N4 (no behavioural auto-learn). |

---

## §3. Halt-and-surface BEFORE build (recorded decisions + the pre-ruled gate)

### G5 — PRE-RULED (do NOT re-open): exposure default = OPEN
The enshrined doctrine settles it — "always expose the substance; adapt only the
vocabulary" + "openness by default, with a floor." N4 builds to **openness-default**:
substance is ALWAYS exposed; only vocabulary/register adapts per the user's
demonstrated competence per area. The N3 seed-writer already encodes this
(`_OPEN_DEFAULTS`: `technical-exposure: open`, `learning-appetite: invite`, with
the `autonomy: surface` floor for consequence-bearing areas). N4's read-path
honours it verbatim and the non-negotiable protection floor (distress / the
protection-floor failures) is always-on regardless of any cell — though the
distress fast-DOWN *trigger* itself is LATER (AIM-5, §7); N4's floor is the
*static* one (a missing/garbled matrix never escalates exposure beyond the
seeded prior; openness applies to TALKING, never to consequence-bearing ACTING —
autonomy stays at the seeded cautious floor).

### Recorded autonomous decisions (named, not gated — F4 tight where settled)
- **D-rec-1:** N4 reads the N3 matrix format AS-IS; the matrix file is a predecessor contract, not an N4 surface. Any format change is a regression against N3 and is OUT.
- **D-rec-2:** The read-path is a NEW contributor on the existing `contributors()` list, fail-soft (matrix error → no injection → openness prior), composing with the chain's fail-open-whole-chain guarantee. No new hook, no change to the chain runner.
- **D-rec-3:** Cells move in N4 ONLY by explicit user statement (override). No behavioural counter writes a cell in this slice (that's AIM-4, OUT). This is the MVP fence made mechanical and is the subject of AC.UM.FENCE.*.

### Forks surfaced WITH recommendations (dispatcher rules fast — see §10 for full reasoning)
- **D-N4.1 — area-classifier mechanism.** *Recommend:* deterministic keyword/objective-tag map (work-anchor objective-tag → area slug), fail-open to `default`. NOT an LLM call on the hot path.
- **D-N4.2 — does the enforce-path (draft-gate threshold) land in N4?** *Recommend:* YES — include it; it's the seam that makes the model structural, and it's small.
- **D-N4.3 — explicit-override lock semantics.** *Recommend:* hard-set to `high` confidence + a `locked` marker; behavioural evidence (LATER) can only *prompt a re-ask*, never silently override.
- **D-N4.4 — auto-weight inference: how aggressive + confirm-gate.** *Recommend:* infer a coarse band (low/normal/high → maps to a `weight` value), ALWAYS surface for confirm, never silent-write.

---

## §4. Spec-objective placement

- **Ladders up to:** the PRIME DIRECTIVE / Lens 0 (per-user-tuned translation) — N4 is its **first functioning brick** (the matrix N3 seeded begins to *steer behaviour*). Binds to `VALUE_PROPOSITION.md` as the prime objective (the persona's translation becomes per-user, not one-size).
- **Binds to parent §:** `loam-roadmap.md` §4 row N4 + §5a "Full adaptive user-model (remainder)" (which N4's fence explicitly defers to).
- **Design binding:** `adaptive-interaction-model.md` §8 MVP table (AIM-1/2/3) + §4 (the deterministic-lookup consumption interface) + §5 (transparency/override).
- **AC.PO binding:** the outcome-altitude AC (AC.UM.READ.4) is the operational proof that the prime-objective brick functions — the real hook adapts behaviour from the seeded per-user state.

---

## §5. Acceptance criteria (outcome-shape; method-in-AC test passed for each)

> Each AC states an observable OUTCOME. Method-in-AC test applied to every one:
> *can it be satisfied by a method other than the one the author has in mind?*
> If yes (it can), the AC is outcome-shape (good). All ACs below pass.

### AC.UM.READ.* — the read+inject path (the load-bearing brick)
- **AC.UM.READ.1 — the cell reaches the turn.** Given a seeded `INTERACTION-MODEL.md` and a turn whose work-anchor resolves to a known area, the keep-pace UserPromptSubmit path emits `additionalContext` that carries that area's `technical-exposure` + `autonomy` cell values as a terse, plain-language directive. *(Method-free: any injection mechanism that lands the cell satisfies it.)*
- **AC.UM.READ.2 — fail-open to prior, no regression.** When the matrix file is missing, unreadable, or malformed, the path emits the openness-prior behaviour (or no injection) and the turn proceeds exactly as the un-personalized keep-pace chain does today — the existing KP1/KP7 contributors are unaffected. *(Observable: a turn with no matrix is byte-indistinguishable in chain outcome from pre-N4.)*
- **AC.UM.READ.3 — the injection is clean + plain.** The injected directive carries NO raw file content, NO mechanism-leak ("I raised your exposure cell"), NO SHAs/paths/axis-jargon in the user-visible register — it is a plain behavioural directive (design §4a "clean, no disclaimer wrapper" + §5 "never narrates its own mechanism").
- **★ AC.UM.READ.4 — OUTCOME-ALTITUDE (`outcome-altitude: true`).** A test invoking the **REAL `user-prompt-submit` hook entry-point** (`main()` / the registered contributor through `run_chain`) with a real envelope and a seeded fixture matrix — **no pre-arranged inner state, no mock of the classifier** — observes the correct per-area cell in the emitted `additionalContext`. A STUB-class test of an inner lookup function does NOT satisfy this AC. *(This is the quality-bar made an AC: the live hook adapts behaviour from seeded per-user state.)*

### AC.UM.AREA.* — work-anchor → area classification
- **AC.UM.AREA.1 — the anchor maps to an area.** Given the `WorkAnchor` the KP1 component already computes (objective text + subgoal + last-topic + prompt), the classifier resolves it to exactly one area slug drawn from the seeded taxonomy (`AIM_AREAS`). *(Method-free: keyword map, tag map, or any deterministic resolver.)*
- **AC.UM.AREA.2 — unknown/low-confidence → `default`.** A turn whose anchor matches no known area (or matches weakly) resolves to the `default` row (the openness prior) — a mis-route is low-harm and self-correcting (design §7 classifier-mis-route mitigation). *(Observable: fail-open routing.)*
- **AC.UM.AREA.3 — the map composes, doesn't recompute.** The classifier reads the EXISTING work-anchor; it does not re-derive the objective/subgoal/last-topic. *(Observable: no second objective-register read introduced on the hot path.)*

### AC.UM.OVR.* — explicit-override
- **AC.UM.OVR.1 — a stated preference sets the cell.** When the user states a preference for an area ("stop explaining the mechanics here" / "I do want the code on builds"), the named area's cell is hard-set to the stated value and persisted to `INTERACTION-MODEL.md` in the seed-writer's format. *(Method-free: any write that lands the value + survives the next read.)*
- **AC.UM.OVR.2 — confidence bumps + locks.** A stated-preference write sets the cell's `confidence` to `high` and marks it locked so that (in the LATER behavioural path) evidence cannot silently override a stated preference — it can only prompt a re-ask (design §5). *(Observable in the file: the cell records high-confidence + the lock marker.)*
- **AC.UM.OVR.3 — the override survives a re-read.** A subsequent turn's read-path injects the overridden value, not the prior default. *(Observable: round-trip through the live read-path.)*

### AC.UM.INSP.* — plain-language inspect
- **AC.UM.INSP.1 — inspect renders in prose, never the raw file.** When the user asks "how are you set for X / how are you treating me," the persona renders the relevant cells as plain-language prose (design §5 — "the system explaining itself is the highest-risk leak surface"), never the raw matrix or axis-jargon. *(Method-free: any prose rendering that conveys the per-area stance.)*
- **AC.UM.INSP.2 — inspect is per-area + truthful to the file.** The rendered description matches what the matrix actually holds for the named area (it reads the live file, not a guess). *(Observable: inspect after an override reflects the override.)*

### AC.UM.WT.* — FBM rule auto-weighting (infer + surface for confirm)
- **AC.UM.WT.1 — a weight is inferred + surfaced, never silent-written.** Given a rule (corpus doc) and a signal of its importance, N4 infers a weight band and SURFACES it for confirmation; it does NOT silently write `weight:` frontmatter. *(Method-free: any inference + any surface-for-confirm mechanism.)*
- **AC.UM.WT.2 — on confirm, the B1 mechanism carries it.** A confirmed weight is written as the B1 `weight:` frontmatter the existing retrieval-boost reads — N4 adds NO new weighting mechanism, only the infer+surface layer. *(Observable: the confirmed value lands as B1-format frontmatter; the B1 boost math applies unchanged.)*
- **AC.UM.WT.3 — no-confirm → no change.** An un-confirmed inferred weight leaves the corpus doc byte-for-byte unchanged (baseline `weight=50` no-op). *(Observable: declining the surface is a no-op.)*

### AC.UM.FENCE.* — the MVP fence (the LATER engine is provably absent)
- **AC.UM.FENCE.1 — cells move ONLY by explicit statement.** No behavioural signal (engagement, bounce, confusion, terseness) writes a cell in this slice — a test drives a sequence of behavioural-signal turns and asserts the matrix is byte-for-byte unchanged; only an explicit override (AC.UM.OVR.*) moves a cell. *(This is the LATER auto-learn path proven ABSENT — the fence made mechanical.)*
- **AC.UM.FENCE.2 — no new hook, no new loop, no consolidation pass.** N4 adds no scheduled job, no `claude -p` consolidation, no distress detector — verified by absence (the read-path is a contributor on the EXISTING hook; no new settings.json hook entry; no new cron/Stop-fold). *(Observable: the settings/hook surface gains no new event registration.)*

---

## §6. Build steps (per-cycle; method-level guidance only — builder's call per ODD §1.1)

> Single-component-cluster amendment (the keep-pace hook chain + a matrix
> reader/writer + the draft-gate threshold). Recommend ONE cycle unless the
> builder's EXAMINE finds the enforce-path (D-N4.2) warrants a split — surface
> if so. Manifest: `docs/plans/n4-mvp-user-model-and-config.manifest.yaml`.

1. **EXAMINE.** Tier-0 confirm on disk: the live matrix format (`render_interaction_model()` output), the `contributors()` seam, the `WorkAnchor` fields, the KP9 draft-gate threshold point, the B1 `weight:` frontmatter reader. Confirm BASELINE = `f1f6116`. Disposition: EXTEND the live keep-pace chain (no new hook) + ADD a matrix reader/writer + (D-N4.2) parameterize the draft-gate threshold.
2. **Read-path (AC.UM.READ.* + AC.UM.AREA.*).** Add the matrix reader (binds to the seed-writer format) + the area-classifier (D-N4.1: deterministic map over the work-anchor) + the inject step, as a NEW fail-soft contributor registered in `contributors()`. Author the outcome-altitude test FIRST (AC.UM.READ.4) — real hook, seeded fixture matrix, real envelope.
3. **Override + inspect (AC.UM.OVR.* + AC.UM.INSP.*).** Add the matrix WRITE path (hard-set + confidence/lock, in the seed-writer's format) + the plain-language inspect renderer (prose, never raw file).
4. **Auto-weight (AC.UM.WT.*).** Add the infer + surface-for-confirm layer over the B1 `weight:` mechanism (no new weighting math).
5. **Enforce-path (D-N4.2, recommended IN).** Parameterize the KP9 draft-gate threshold by the active area's `technical-exposure` cell.
6. **Fence proof (AC.UM.FENCE.*).** Author the tests that prove behavioural signals do NOT move cells and no new hook/loop/consolidation is added.
7. **Apply + seal + smoke.** `loam amend apply` for any sealed-component edits (name `loam amend apply` explicitly — the keep-pace hook chain + draft-gate are sealed components). Local seal. Then the live-hook smoke: a real envelope through the real `user-prompt-submit` entry-point with a seeded fixture matrix shows the correct cell injected (the AC.UM.READ.4 surface, run as a smoke not just a unit test).

---

## §7. Out of scope (the MVP fence — deferred to the LATER remainder)

The FULL adaptive engine is explicitly OUT (design §8 Backlog AIM-4..8;
roadmap §5a "Full adaptive user-model … remainder"):

- **Behavioural signal counters + hysteresis (AIM-4)** — the auto-learn-from-behaviour path. In N4, cells move ONLY by explicit statement (AC.UM.FENCE.1). Deferred until the classifier is dark-launched + calibrated on real traffic (design §7 flag).
- **Fast-down-on-distress trigger (AIM-5)** — the §2.4 asymmetric safety down-update wired to the distress detector. The STATIC protection floor is in N4 (G5); the dynamic fast-down trigger is LATER (needs the distress detector + trusted signal classification).
- **Tone + learning-appetite axes as adaptive (AIM-6)** — N4 reads/injects `technical-exposure` + `autonomy` (the two-axis MVP); tone + learning-appetite are SEEDED (N3) and READABLE but not yet adaptively moved.
- **Weekly re-eval consolidation pass + fresh-evaluator drift judge (AIM-7)** — the periodic consolidation; FBM-T3.1-gated.
- **Capability-auto-adoption + non-tech-recovery as consumers (AIM-8)** — the downstream consumers.
- **Dark-launch signal logging** — even the *logging* of behavioural signals (the AIM-4 precursor) is OUT; N4 ships zero behavioural instrumentation.

**Deferred-until:** AIM-4 starts on a week of dark-launched signal logs; the rest gate on AIM-4 + (for AIM-7) FBM consolidation landing. None of these block the N4 brick — the per-area-adaptive *outcome* ships without them.

---

## §8. Halt triggers (in-flight conditions that abort the build)

- **The matrix format on disk differs from `render_interaction_model()`** — the read contract is broken; HALT (a format change is an N3 regression, out of N4's fence).
- **The area-classifier cannot be made deterministic + fail-open** without an LLM call on the hot path — HALT and surface (the design forbids model-decides-each-turn, §4b; the hot path must not block on `claude -p`).
- **Parameterizing the draft-gate threshold (D-N4.2) requires touching the register-judge's core logic, not just a threshold lookup** — surface; this may push D-N4.2 to its own slice.
- **A behavioural signal would need to write a cell to satisfy any AC** — HALT; that's the AIM-4 fence breach, the AC is mis-framed.
- **Any AC turns out to require the distress detector or a new hook** — HALT; that's LATER-remainder scope leaking into the MVP.

---

## §9. Bookkeeping (on seal)

- **STATE.md** — record N4 sealed (the MVP user-model brick; the read+inject path live on the keep-pace hook; override + inspect + auto-weight; the LATER engine fenced OUT).
- **`docs/plans/loam-roadmap.md`** §4 row N4 — mark built; §5a "Full adaptive user-model (remainder)" now unblocked-by-N4 (its predecessor satisfied).
- **`docs/release-roadmap.md`** — if N4 ships as part of a versioned MINOR, backfill the §2/§3 entry at release time (version derived at release time — do NOT pre-assign).
- **`adaptive-interaction-model.md` §8** — mark AIM-1/AIM-2 (if D-N4.2 IN)/AIM-3 built; AIM-4..8 remain backlog.
- **Manifest sidecar** — advance the seal sidecar for the sealed-component edits (keep-pace chain + draft-gate) per `loam amend apply`.
- **G5 ratification record** — the openness-default revision of `feedback_abstraction_first_default.md` is pre-ruled in this dispatch; record that the memory rule's default is now a lookup (per `feedback_record_owner_ratification_before_dispatch.md`, the pre-ruling IS the record).

---

## §10. F2 Ruthless Feedback (honest doubts + forks-with-recommendations)

### The forks (each: the call, the signals, the recommendation)

**D-N4.1 — the area-classifier mechanism.**
- *The call:* how does a work-anchor become an area slug? Options: (a) deterministic keyword/objective-tag map; (b) an LLM classification call; (c) a learned embedding lookup.
- *Signals:* the design (§4b) FORBIDS model-decides on the hot path (instruction-decay + register self-correction failure); the hook fires EVERY turn (latency-sensitive, must fail-open); the taxonomy is coarse (6 buckets) so mis-routes are low-harm and self-correcting (§7).
- **Recommendation: (a) deterministic keyword/objective-tag map, fail-open to `default`.** Tag the live objectives with an area (litrpg-objective → `their-domain-work`, a loam-dev topic → `harness-mechanics`) and keyword-match the prompt for the rest. It's the design's own §4a recipe, it's hot-path-safe, and the LATER calibrated behavioural path is where accuracy gets earned — not a synchronous LLM call now. **This is the single biggest design risk in N4** (design §7 final flag: signal-classification accuracy is unverified) — keeping it coarse + fail-open-to-default is the mitigation.

**D-N4.2 — does the enforce-path (draft-gate threshold) land in N4?**
- *The call:* the design's AIM-2 (parameterize KP9's jargon/register threshold by the area's `technical-exposure` cell) — in N4, or a follow-on?
- *Signals:* it's the seam that turns the model from ADVISORY (injected directive the persona may ignore — instruction-decay risk) to STRUCTURAL (the gate enforces it); it's small IF it's a threshold lookup; it risks growing IF it touches the register-judge core.
- **Recommendation: INCLUDE in N4, with the §8 halt-trigger as the escape hatch.** A self-injected directive that the gate doesn't back is exactly the instruction-decay failure the design names (§4b) — the read-path without the enforce-path is advisory-only and under-delivers the brick. Include it; if EXAMINE finds it needs register-judge surgery (not a threshold lookup), split it per the §8 halt.

**D-N4.3 — explicit-override lock semantics.**
- *The call:* when the user states a preference, how hard does it lock?
- *Signals:* design §5 ("the user always out-votes the model"; behaviour can only *prompt a re-ask*, never silently override); but the behavioural path that would contend with it is LATER (so the lock has nothing to contend with IN N4 — but the file format must record it for AIM-4).
- **Recommendation: hard-set to `high` confidence + a `locked` marker, recorded in the matrix file now.** Even though nothing contends with it in N4, recording the lock is cheap and makes the file forward-compatible with AIM-4 (which must read it to honour "never silently override"). The override is the highest-confidence, classifier-free path (design §7) — it carries early personalization safely while the behavioural path is dark.

**D-N4.4 — auto-weight inference aggressiveness + confirm-gate.**
- *The call:* how does N4 infer a rule's weight, and is the write gated?
- *Signals:* B1 built the mechanism (`weight: 1–100`, `BASELINE_WEIGHT=50` no-op); a silent weight write is a behavioural-style auto-change (the exact thing the MVP fence defers); the design's whole stance is surface-before-silent-change.
- **Recommendation: infer a COARSE band (low/normal/high → a weight value), ALWAYS surface for confirm, never silent-write (AC.UM.WT.1/.3).** This keeps the auto-weighting inside the MVP fence (no silent behavioural change) while delivering the "infer + surface" outcome. The aggressive auto-tune is LATER with the rest of the behavioural engine.

### Honest doubts (named, not buried)

1. **The classifier is the load-bearing fragility (carried from the design's §7 flag).** The whole brick's *value* scales with routing accuracy, and routing accuracy is unverified. Mitigation: coarse + fail-open-to-default + the override path carrying early personalization. But I want to name plainly that a mis-routing N4 is a *quiet under-delivery* (wrong-but-plausible cell injected) more than a loud failure — the inspect path (AC.UM.INSP) is the user's recourse, so inspect quality matters more than it looks.
2. **Advisory-vs-structural tension (feeds D-N4.2).** If D-N4.2 is deferred, the read-path injects a directive nothing enforces — and the design itself (§4b) says self-injected register instructions decay within ~8 rounds and self-correction fails for register. A read-path-only N4 is a weaker brick than it appears. This is *why* I recommend INCLUDING the enforce-path, and it's the honest risk if it's cut.
3. **The fence is the right cut but it under-sells in a demo.** N4 with no behavioural auto-learn means the only way a cell *moves* is the user explicitly saying so — a cold demo (no overrides) shows the seeded prior, not adaptation. This is CORRECT (Lens 4: ship the high-confidence structure, defer the low-confidence learning) but worth stating: the visible "wow" is the LATER AIM-4, and N4 should be framed as the brick that *makes AIM-4 possible*, not as the adaptive payoff itself.
4. **G5 is pre-ruled but it does edit a memory rule's meaning.** The openness-default reverses `feedback_abstraction_first_default.md`'s `minimal` default. The design (§6.1) justifies it as "a single cell value frozen as a global default" being unfrozen — I agree with the justification — but the *syntactic-leak floor* (no SHAs/paths/IDs in prose) must survive unconditionally regardless of any cell (design §6 row 2), and AC.UM.READ.3 is the guard. Flagging that the floor is separate from the exposure axis and must not be loosened by an `open`/`deep` cell.

---

## §11. Provenance trail (load-bearing sources, with line refs)

- **`docs/design/adaptive-interaction-model.md`** — the flagship design. §8 MVP table (AIM-0/1/2/3 = N4's slice; AIM-4..8 = the LATER remainder, the §7 fence); §4 (deterministic-lookup consumption interface — the read+inject design); §4a (the read-path on the live UserPromptSubmit hook + work-anchor→area map + the clean injection); §4b (why deterministic-lookup not model-decides — instruction-decay + register self-correction failure); §4c (graceful degradation / fail-open — AC.UM.READ.2); §5 (transparency + override + lock + "never narrates its own mechanism" — AC.UM.OVR/INSP/READ.3); §6.1 (the G5 openness-default revision of `abstraction_first_default.md`); §7 (the F2 risk table + the unverified-classifier flag — §10 doubt 1).
- **`framework/workspace-bootstrap/src/loam/workspace_bootstrap/seed_writer.py`** — the matrix format N4 reads: `render_interaction_model()` (lines ~123–152), `AIM_AREAS` (lines ~66–73), `_OPEN_DEFAULTS` + `_CAUTIOUS_AUTONOMY_AREAS` (lines ~79–86), the per-cell `axis: { value, confidence: prior, evidence: [] }` line shape (line ~149). **The read contract.**
- **`framework/hands-off-lifecycle/hooks/keep_pace/user_prompt_submit.py`** — the live `contributors()` seam (lines ~123–132) + the `Contributor(name, fn(envelope) -> Optional[str])` fail-soft contract + `run_chain` fail-open-whole-chain (AC.KP0.4). **The read-path's host seam (AC.UM.READ.*).**
- **`framework/primary-persona/src/loam/primary_persona/keep_pace/work_anchor.py`** — `WorkAnchor{prompt, objective_texts, subgoals, last_topic}` (lines ~127–186). **The classifier's input (AC.UM.AREA.*).**
- **`framework/hands-off-lifecycle/hooks/keep_pace/draft_gate.py`** — the KP9 register/jargon Layer-1/Layer-2 gate. **The enforce-path seam (D-N4.2 / AIM-2).**
- **`docs/plans/fbm-rule-weighting-slice-plan.md`** (B1) — the `weight: <int 1–100>` + `pinned: true` frontmatter mechanism + `BASELINE_WEIGHT=50` no-op + the retrieval-boost math. **The auto-weighting mechanism N4's infer+surface layer composes on (AC.UM.WT.*).**
- **`docs/plans/loam-roadmap.md`** §4 row N4 (the fence + the FBM-auto-weight home) + §5a "Full adaptive user-model (remainder)" (the LATER engine) + the `N1→N3→N4→Phase 3` critical path.
- **`docs/plans/n3-onboarding-init-flow-translate-in-intake.md`** — the predecessor; N3 seeds the prior-confidence matrix N4 reads ("N4 is the engine that moves the cells from evidence").
- **`feedback_abstraction_first_default.md`** — the memory rule G5 revises (the `minimal`→`open` default; the syntactic-leak floor that survives unconditionally — §10 doubt 4).

# N4 — MVP user-model + config (the adaptive interaction-model's first brick) — apply ladder

2026-05-31. Roadmap N4 (critical path N1 -> N3 -> N4 -> Phase 3) per
`docs/plans/n4-mvp-user-model-and-config.md`. The FLAGSHIP pillar-1
engine's FIRST REAL BRICK: N3 built the front door (seed the openness-
biased INTERACTION-MODEL.md matrix at confidence:prior); N4 makes that
prior STEER BEHAVIOUR and gives the user the controls. This is the
per-user-tuned-translation engine (PRIME DIRECTIVE / Lens 0) starting to
function: the persona's exposure/autonomy adapts per area from seeded
per-user state.

The load-bearing design stance: DETERMINISTIC LOOKUP, not model-decides.
The persona reads the matrix CELL from the file every turn via the LIVE
keep-pace UserPromptSubmit hook (a new fail-soft Contributor on the
existing contributors() seam — NO new hook, Lens 1) and injects it as a
plain behavioural directive; the model never has to REMEMBER the
preference because the hook re-states it from the file each turn (the
design's answer to instruction-decay + register self-correction failure).
Determinism lives in the lookup; adaptivity lives in the file contents.

G5 PRE-RULED (not re-opened): exposure default = OPEN — expose the
SUBSTANCE always, adapt only the VOCABULARY. The N3 seed-writer already
encodes this (open exposure + invite learning, with the autonomy floor at
surface for ops-and-money/decisions — openness applies to TALKING, never
to consequence-bearing ACTING). The syntactic-leak floor (no SHAs/paths/
IDs in prose) survives unconditionally regardless of any cell (AC.UM.READ.3).

Composes on (rebuilds none): the LIVE keep_pace contributors() seam
(user_prompt_submit.py), the EXISTING KP1 WorkAnchor (work_anchor.py —
the classifier maps it -> an area slug, no anchor recompute), the N3
seed-writer's matrix FORMAT (render_interaction_model() — the read
contract), the KP9 draft_gate (D-N4.2 enforce-path), and the B1
weight: frontmatter mechanism (auto-weighting composes on it — infer +
surface for confirm, never silent-write).

AC families: AC.UM.READ.* (the cell reaches the turn via the live hook;
fail-open to the openness prior on any matrix error, NO regression; clean
plain injection, no mechanism-leak) incl. the ★ AC.UM.READ.4 OUTCOME-
ALTITUDE (the REAL user-prompt-submit entry-point, a seeded fixture
matrix, a real envelope -> the correct per-area cell in additionalContext;
a STUB of an inner lookup does NOT satisfy it); AC.UM.AREA.* (work-anchor
-> area, unknown -> default fail-open, composes not recomputes); AC.UM.OVR.*
(stated preference -> cell hard-set + confidence high + locked, survives a
re-read); AC.UM.INSP.* (inspect renders in prose never the raw file,
truthful to the file); AC.UM.WT.* (infer a coarse weight band + surface
for confirm; on confirm the B1 mechanism carries it; no-confirm = no-op);
AC.UM.FENCE.* (cells move ONLY by explicit statement — behavioural signals
do NOT move a cell in this slice; NO new hook/loop/consolidation).

MVP FENCE (design AIM-4..8 = the LATER remainder, OUT): behavioural signal
counters + hysteresis (auto-learn-from-behaviour); fast-down-on-distress
trigger (the STATIC floor is in; the dynamic trigger needs the distress
detector + trusted classification); tone + learning-appetite as ADAPTIVE
axes (seeded + readable, not yet moved); weekly re-eval consolidation +
drift judge (FBM-T3.1-gated); capability-auto-adoption + non-tech-recovery
consumers; even dark-launch signal LOGGING is OUT — N4 ships zero
behavioural instrumentation. The per-area-adaptive OUTCOME ships without
them (Lens 4: ship the high-confidence structure, defer the low-confidence
learning top).

Forks (recommendations in plan §10; dispatcher in FULL-AUTONOMY rules fast):
  D-N4.1 = area-classifier mechanism (recommend: DETERMINISTIC keyword/
           objective-tag map, fail-open to default — NOT an LLM call on the
           hot path; the design forbids model-decides-each-turn; this is the
           single biggest N4 risk, mitigated by coarse + fail-open).
  D-N4.2 = does the enforce-path (draft-gate threshold) land in N4
           (recommend: YES include — it's the seam that makes the model
           structural not advisory; split via the §8 halt only if it needs
           register-judge surgery rather than a threshold lookup).
  D-N4.3 = explicit-override lock semantics (recommend: hard-set high
           confidence + a locked marker recorded NOW — forward-compatible
           with AIM-4's "never silently override").
  D-N4.4 = auto-weight inference aggressiveness (recommend: coarse band ->
           weight value, ALWAYS surface for confirm, never silent-write —
           keeps auto-weighting inside the MVP fence).

Unblocks the Phase-2 "Full adaptive user-model (remainder)" (its N4
predecessor satisfied) and is the brick that makes the behavioural
auto-learn engine (AIM-4) possible.

## §14. Method-decision register (build-time rulings)

Build dispatched in FULL-AUTONOMY (owner away); the four forks were ruled
in the dispatch and confirmed at build with no halt:

- **D-N4.1 — area-classifier = DETERMINISTIC keyword/objective-tag map**,
  fail-open to `default`, no LLM on the hot path. Consequence-bearing
  areas (ops-and-money / decisions-and-tradeoffs) win keyword ties so a
  money/decision turn never under-routes to the bolder default. Reads the
  EXISTING WorkAnchor tokens (no recompute). Taxonomy asserted equal to
  the N3 seed-writer's `AIM_AREAS` so a seed-writer drift is caught.
- **D-N4.2 — enforce-path INCLUDED** as a THRESHOLD LOOKUP on the KP9
  draft-gate (`gate(exposure=)` / `layer1_lint(exposure=)`). NOT
  register-judge surgery: Layer C is untouched; the exposure parameter
  only partitions Layer 1's classes into the syntactic-leak FLOOR
  (always enforced, G5) and the exposure-dependent jargon set (`deep`
  relaxes). The §8 split-halt did NOT fire — it was a threshold lookup.
- **D-N4.3 — override hard-sets** the cell value at `confidence: high`
  with a `locked: true` marker, validated against the per-axis
  vocabulary (a bad area/axis/value is rejected, file untouched). The
  lock is recorded in the file now for forward-compat with AIM-4.
- **D-N4.4 — auto-weight = coarse band** (low/normal/high → a B1 weight
  value; normal == BASELINE_WEIGHT, the no-op band), ALWAYS surfaced for
  confirm, NEVER silent-written; on confirm writes the B1 `weight:`
  frontmatter the existing corpus_index boost reads.

**Build-time deviations / surfaces (F2):**

- **D-build.N4.1 — pre-existing D-1 byte-match drift (OUT-OF-FENCE,
  rebaselined in-band).** The hands-off-lifecycle full-suite (run by the
  seal) carried a pre-existing failure: `test_d1_byte_content_match.py`
  for `session_start_emitter.py`. The file is byte-identical to the N4
  BASELINE `f1f6116` (N4 does not touch it); the failure reproduces
  IDENTICALLY on the stashed clean tree. Root cause: the D-1 snapshot
  lagged a legitimate N3-onboarding edit to that file (sealed at
  `f1f6116` without a D-1 rebaseline). Resolved by an ODD §4 in-band
  retire-and-rebaseline of the snapshot hash — the same established
  pattern as the amendment #144 §16 and v0.13.0/v0.14.0 rebaselines in
  that test. The seal-fence could not advance otherwise (the seal runs
  the touched component's full suite). Surfaced per F2.

### Commit SHAs
