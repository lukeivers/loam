# metacognitive-gate-reentrant-loop-slice1 — a gated, evidence-bound deliberate-reasoning layer over the inference engine, pre-registered against baseline

**Status:** RATIFIED — cleared for build. Sub-plan-doc / experiment-plan (first slice of the deliberate-reasoning-layer program). **Class:** MINOR (HARNESS-LAYER + EXPERIMENT) — version derives at release time (`feedback_version_numbers_at_release_time`; do NOT pre-assign).

**OWNER RATIFIED — 2026-06-22 (Luke, Discord msg 1518677639932412088):** "I'm good to go with this plan and these ACs. let's do it." Plan + AC set (`AC.MGRL.{1..7}` + `AC.MGRL.OA`) approved for the slice-1 build as written. **Dispatcher ruling on D-MGRL.4:** all three observable triggers (low-confidence, novelty, stakes) ship in slice 1 — stronger theory-vs-generic discriminator when escalation is attributable to a specific trigger; the surprise/prediction-error trigger is deferred to slice 2.

**Working directory:** `/Users/lukeivers/loam` (canonical loam, `main`).

**Parent / source of truth:** the design proposal `workspace/.scratch/claude-output/consciousness-emulation-harness-design.md` (captured 2026-06-22 from the live Discord design discussion). This plan implements **only** §4 of that proposal ("Smallest viable first experiment") — the metacognitive **gate** + the **evidence-bound re-entrant loop** (the proposal's recommendations 2 + 3), as a turn-level harness layer, default OFF, escalating on a defined trigger set, measured against baseline on a fixed objective-outcome task set with a blind judge. The proposal's §0 "honest boundary" is carried as a HARD requirement (see §3.1).

**Predecessors (load-bearing existing surfaces this plan composes against / cites as precedent — NOT requirements on method):**
- `framework/primary-persona/src/loam/primary_persona/intent_classifier.py` — the proven **deterministic per-turn UserPromptSubmit classifier** (promoted canonical at amendment #144 Scope A). It scores intent with lightweight regex, no LLM call, <5 ms typical, and emits `additionalContext` to shape the model's behaviour BEFORE the persona interprets. This is the closest existing architectural precedent to the gate; the gate is a sibling of this shape, not a new species. Cited as precedent only — the builder owns whether to extend it or build alongside it.
- `framework/self-correction/` — an existing detection→review→verdict→record framework (depth-cap, trigger-dedup, same-class-cascade guards, outcome-altitude real-entrypoint test). The re-entrant loop's "draft → critique → revise → re-check" has a structural cousin here. Cited as precedent; the builder decides reuse-vs-fresh.
- `framework/primary-persona/src/loam/primary_persona/context_composer.py` + `keep_pace/` — the existing turn-level context-assembly surfaces the proposal calls "primitive bones" of the global workspace. Out of THIS slice's scope (the curated working-set is the proposal's rec 5, deferred), but named so the fence is unambiguous.

**BASELINE candidate:** the plan-doc commit (the commit immediately preceding the first source-edits). The builder confirms against the `main` tip at build time per the house pattern.

**Quality bar:** experiment-grade. The pre-registration document (§3.1, §5) is the load-bearing artefact and must be Anthropic-publish-grade in its anti-confirmation-bias rigor: metrics, task set, and the theory-prediction-vs-generic-lift distinction are all fixed and committed BEFORE any escalated-mode run is scored. Any new hook/processing surface meets the house guard-floor bar (p95 well under the per-turn latency budget for the deterministic gate; the deliberate loop is explicitly allowed to be slow because it is gated and OFF by default).

---

## §1 Summary / TL;DR

Build the smallest honest test of the deliberate-reasoning theory: a **gate** that decides per-turn whether the fast inference path answers or a **deliberate, evidence-bound, re-entrant loop** engages — default OFF, escalating only on a defined trigger set — and measure escalated-mode against an identical baseline on a fixed task set with **objective** outcomes, judged **blind to the hypothesis**, against **pre-registered** success criteria.

**What ships in this slice:**
1. A turn-level **gate** that emits an escalate / don't-escalate decision plus the trigger that fired, from observable signals available in the harness.
2. A **deliberate re-entrant loop** that, when the gate escalates, runs draft → adversarial evidence-bound critique → revise → re-check, and either improves the answer or returns the original when critique finds no defensible improvement (the no-degradation guard).
3. A **pre-registered experiment**: a fixed task set with machine-checkable objective outcomes, a baseline-vs-escalated comparison, a **blind judge** that never saw the hypothesis, and a committed-in-advance definition of (a) what "better" means and (b) the behavioral signature that would count as the theory's prediction coming true vs. generic quality lift.

**What does NOT ship in this slice (deferred to slice 2, named in §7):** the persistent, self-authored self-model + goal/valence stack + cross-session continuity (the proposal's recommendation 1, features 6–8). The curated global workspace (rec 5) and the standalone surprise/prediction-error detector beyond what the gate's trigger set needs (rec 4 as its own subsystem) are also deferred.

**AC families:** `AC.MGRL.{1..7}` plus one outcome-altitude AC `AC.MGRL.OA` (escalation fires through the production entry-point with no pre-arranged state).

**Key decisions baked (recommendations = law unless the dispatcher overrules; see §3):**
- **D-MGRL.1** — the gate is a **deterministic signal-scored classifier**, not an LLM-per-turn judge (recommendation + rationale in §3.1).
- **D-MGRL.2** — the deliberate loop's critique is **adversarial and evidence-bound with a no-degradation guard** that can return the original answer; this is the structural answer to the proposal's own §3 "always-on self-critique degrades output" trap (§3.2).
- **D-MGRL.3** — the experiment is **pre-registered before any scored run**, with a **blind judge** and a committed theory-prediction-vs-generic-lift discriminator; this is the §0 honest-boundary requirement made structural (§3.3).
- **D-MGRL.4** — the gate's trigger set for slice 1 is the **subset of the proposal's four triggers that is actually observable in this harness** (low-confidence, novelty, stakes); the predictive-error/surprise trigger ships only to the extent the harness can compute an expectation cheaply, else it is deferred (§3.4).
- **D-MGRL.5** — the layer is **default OFF** and gated, so its cost lands only on escalated turns; the gate is the cost governor (§3.5).

**F2 RF on scope realism (see §10):** the experiment-design half of this slice is the hard part, not the code. The single most likely failure is a metric that *looks* objective but is gameable or measures generic quality lift rather than the theory's specific prediction. §10 RF-1 names this and §3.3 + §5 are the guard. If a genuinely non-gameable pre-registered metric cannot be defined for the chosen task set, the correct action is to HALT and say so (§8 trigger 2), not to ship a soft metric.

---

## §2 Placement decisions

| Item | Placement (recommendation) | Rationale |
|---|---|---|
| The gate (turn-level escalation decision) | A turn-level harness surface in the primary-persona / hook layer, sibling to `intent_classifier.py`'s UserPromptSubmit-classifier shape | The gate is a per-turn pre-interpretation decision; `intent_classifier.py` is the proven precedent for exactly this (deterministic, fast, fires before the persona interprets). **Whether to extend that file or add a sibling is the builder's call** — the placement names the layer, not the file. |
| The deliberate re-entrant loop | A harness component invoked only on escalated turns; reuse `framework/self-correction/`'s detection→review→verdict spine if it fits, else a fresh component | The loop is gated and OFF by default, so it does NOT sit on the per-turn hot path; latency is acceptable here. Reuse-vs-fresh is the builder's call (D-MGRL.2 names the precedent, not the method). |
| The experiment harness (task set + baseline-vs-escalated runner + blind judge) | A self-contained experiment artefact under a dedicated path the builder chooses, with the pre-registration committed as a versioned doc BEFORE any scored run | The pre-registration must be a durable, timestamped, git-committed artefact (the anti-confirmation-bias guard depends on it predating the scored runs). Its exact path is the builder's call; its existence-before-scoring is an AC. |
| The pre-registration document itself | A committed markdown/YAML artefact whose commit predates the first escalated-mode scored run | §0 honest-boundary requirement: "defined before we run the experiment, or we will see what we want to see." The git-ref ordering (pre-reg commit → scored-run commit) is the evidence (`feedback_published_state_only_from_git_refs`). |

---

## §3 Halt-and-surface BEFORE build (recorded + ruled at plan-authoring)

These are autonomous rulings recorded at plan-authoring; the builder respects them as gates, not re-litigations. Each carries a recommendation + rationale per `feedback_summarize_and_surface_decisions`.

### 3.1 — D-MGRL.1 — the gate is a deterministic signal-scored classifier, NOT an LLM-per-turn judge (RULING; recommendation)

**Ruling / recommendation:** the gate decides escalate / don't-escalate from **deterministic, observable signals** scored cheaply per turn — NOT by calling an LLM on every turn to ask "should I think harder about this." **Rationale:** (1) an LLM-per-turn judge collides with the per-turn latency budget and with `feedback_no_anthropic_api_key` cost discipline (every turn would spend a `claude -p` call); (2) `intent_classifier.py` already proves a deterministic per-turn classifier is the right shape for a fire-before-interpretation decision (<5 ms, zero token cost); (3) the proposal's §3 names cost as a real trap and the gate as the cost governor — an LLM-per-turn gate makes the gate itself the cost problem. **Method-in-AC test passed:** "the gate emits an escalation decision + the firing trigger from observable signals" can be satisfied by regex scoring, a small heuristic, a learned threshold on logged confidence signals, or any combination — method stays open. **What the gate is NOT permitted to be (the trap this rules out):** an always-on "think harder" wrapper on every turn — that is the proposal's own §3 degradation trap and is explicitly out (§7).

### 3.2 — D-MGRL.2 — the deliberate loop is adversarial + evidence-bound + has a no-degradation guard (RULING; the load-bearing anti-degradation call)

**Ruling / recommendation:** when the gate escalates, the loop runs draft → **adversarial, evidence-bound** critique ("find the weakest link, name why each step is or is not sound, cite the evidence") → revise → re-check, and is **structurally permitted to return the original draft unchanged** when the critique finds no evidence-backed improvement. **Rationale:** this is the direct structural answer to the proposal's §3 first trap — *always-on self-critique degrades LLM output via rationalization, post-hoc confabulation, and talking past a correct first answer.* Free-form self-narration invites exactly that; evidence-binding ("cite why each step is sound") plus a no-degradation guard (the loop must be able to conclude "the first answer was right, return it") is what makes re-entrance a possible improvement rather than a guaranteed verbosity tax. **Evidence the trap is real:** the proposal §3 names it explicitly and both parties flagged confirmation-bias risk live this session; the LLM-reasoning literature documents self-critique degradation on tasks where the first answer is already correct. **Method-in-AC test passed:** "the escalated answer is never worse than baseline beyond a pre-registered tolerance, measured by the blind judge" is an outcome — the builder owns whether the no-degradation guard is a critique-confidence threshold, a baseline-comparison step, a best-of-N selection, or something else.

### 3.3 — D-MGRL.3 — pre-registration + blind judge + theory-vs-generic discriminator, committed BEFORE any scored run (RULING; the §0 honest-boundary made structural)

**Ruling / recommendation:** the experiment's success criteria, task set, metric definitions, and the **specific behavioral signature that would count as the theory's prediction coming true vs. generic quality lift** are written down and **git-committed before the first escalated-mode scored run**. The judge that scores outcomes is **blind to the hypothesis** — it sees answers to grade against objective criteria, not "this is the consciousness-emulation arm vs. the control arm." **Rationale:** this is the proposal's §0, which the dispatch named a HARD requirement and forbade softening. Without pre-registration the experiment will "see what we want to see" (the proposal's own words; both parties flagged this exact bias live). The git-ref ordering is the tamper-evidence: a pre-registration commit that predates the scored-run commit is checkable from the ref graph, not from prose claims (`feedback_published_state_only_from_git_refs`). **The theory-vs-generic discriminator is the subtle, load-bearing part:** "the escalated arm scores higher" is *generic quality lift* and does NOT by itself confirm the theory — any "think harder" intervention can produce that. The theory predicts a **specific** behavioral signature (e.g. that the gain concentrates on the turns the gate flagged as novel/high-stakes/low-confidence and is absent on turns the gate declined to escalate; that escalation correlates with the trigger signal, not with task difficulty in general). That discriminator is pre-registered. **Method-in-AC test passed:** "a blind judge scores escalated vs. baseline against pre-registered objective criteria" can be a held-out human, a separate hypothesis-blind LLM-judge run via `claude -p`, or a deterministic checker for tasks with machine-checkable answers — method open.

### 3.4 — D-MGRL.4 — slice-1 trigger set is the observable subset of the proposal's four (RULING)

**Ruling / recommendation:** the gate's slice-1 trigger set is the subset of {low self-confidence, detected novelty, high stakes, prediction-error/surprise} that is **actually computable from signals available in this harness at gate-time**. Low-confidence, novelty, and stakes have plausible cheap proxies (e.g. hedging/uncertainty markers in a draft, task-class novelty against recent history, stakes signalled by task class or explicit user framing). The **prediction-error/surprise trigger ships only to the extent the harness can cheaply maintain an expectation and detect its violation**; if maintaining that expectation requires a subsystem larger than this slice, the surprise trigger is **deferred** and named in §7. **Rationale:** the proposal §4 names the trigger set as "low self-confidence, detected novelty, high stakes" for the first experiment — surprise/prediction-error is listed in §1.4 as a fuller mechanism, not a slice-1 requirement. Shipping a half-built surprise detector would be method-in-code for an under-specified case (ODD §2.5 Rule 2). **Method-in-AC test passed:** "the gate fires on at least one defined, observable trigger and records which trigger fired" leaves the specific proxies to the builder. **Open named decision for the dispatcher (§3.4 surface):** which of the three core triggers are in-scope for slice 1 is partly an experiment-design call — recommendation is **all three that are observable**, because the theory-vs-generic discriminator (§3.3) is *stronger* when escalation can be attributed to a specific trigger; a single-trigger gate weakens the discriminator.

### 3.5 — D-MGRL.5 — default OFF, gated; the gate is the cost governor (RULING)

**Ruling / recommendation:** the deliberate layer is **default OFF**. On a turn the gate declines to escalate, the harness behaves exactly as baseline (no extra tokens, no extra latency beyond the deterministic gate's own sub-budget cost). **Rationale:** the proposal §4 ("defaulting off") and §3 (cost trap; "the gate is also the cost governor") both require this. Default-OFF is also what makes the experiment honest: baseline is genuinely unperturbed, so the comparison measures the deliberate layer's effect, not a measurement artefact. **Method-in-AC test passed:** "on a non-escalated turn, output and cost are indistinguishable from baseline" is an outcome verifiable by comparison; method open.

### 3.6 — no-API-key gate (RECORDED)

Any LLM in the loop (the deliberate critique, or a blind LLM-judge if that judge design is chosen) goes through `claude -p` (`framework/memory-system/src/claude_print_client.py` / the subscription path — `feedback_no_anthropic_api_key`). The deterministic gate makes **no** LLM call. This is recorded so the builder does not reach for the Anthropic SDK + API key.

---

## §4 Spec-objective placement

Binds to the design proposal's §4 (smallest-viable-first-experiment) and §0 (honest boundary). Ladders up to **AC.PO.1 (harness test)** + **AC.PO.2 (primary-persona test)** in `docs/VALUE_PROPOSITION.md` (`feedback_value_proposition_as_prime_objective`):

- **Harness test:** the gate + deliberate loop **add to the toolkit the primary persona draws from** — a new, measured, default-off capability to spend more deliberation on the turns that warrant it.
- **Primary-persona test:** if the experiment confirms the prediction, the layer **reduces the translation burden** by improving answer quality on exactly the hard/novel/high-stakes turns where the persona's first-pass translation is least reliable — and does so without taxing the easy turns.

This slice is also a direct instance of Luke's stated north-star for this work (captured 2026-06-22): *"improve the quality of your response as a layered stack on top of the inferencing engine underneath, not relying on them to do the improvements for us."* The gated deliberate layer IS that stack; the pre-registration is what keeps "improvement" honest rather than wished-for.

---

## §5 Acceptance criteria

AC IDs scope-descriptive (`AC.MGRL.*`). Each outcome-shape; method-in-AC test passed (each can be met by ≥1 method other than any I have in mind). Per ODD §2.5 these name WHAT-must-be-true; the builder owns HOW.

| AC | Outcome (NOT method) | Verification surface |
|---|---|---|
| **AC.MGRL.1** | On every turn, the harness produces an escalate / don't-escalate decision **and** records which trigger (or none) fired, from observable signals, without an LLM call on the don't-escalate path. | Given a turn with a defined trigger signal present, the decision is "escalate" and the firing trigger is recorded; given a turn with no trigger signal, the decision is "don't escalate" and no LLM call is made on that path. |
| **AC.MGRL.2** | On a turn the gate declines to escalate, the final output and the cost/latency profile are indistinguishable from baseline (the layer is genuinely default-OFF). | A non-escalated turn produces byte-identical (or within a pre-registered no-op tolerance) output to the same turn with the layer absent; no deliberate-loop tokens are spent. |
| **AC.MGRL.3** | On an escalated turn, the deliberate loop runs a draft → adversarial evidence-bound critique → revise → re-check cycle and yields a final answer that is the revised answer **only when** the critique produced an evidence-backed improvement, else the original draft (the no-degradation guard holds). | On an escalated turn where the first draft is already correct against an objective check, the loop returns an answer no worse than the draft (no introduced regression); on an escalated turn where the draft has a checkable defect the critique can catch, the loop returns the corrected answer. |
| **AC.MGRL.4** | A pre-registration artefact exists and is git-committed **before** the first escalated-mode scored run, fixing: the task set, the metric definitions, what "better" means, and the specific behavioral signature that distinguishes the theory's prediction from generic quality lift. | The pre-registration commit is an ancestor of the first scored-run commit in the git ref graph; the artefact contains all four fixed items, each concrete enough to be applied without further judgment calls. |
| **AC.MGRL.5** | The experiment compares escalated-mode vs. baseline on the fixed task set, scored by a judge **blind to the hypothesis**, against the objective pre-registered criteria. | A run produces per-task baseline + escalated outcomes scored by the blind judge; the judge's inputs demonstrably exclude any hypothesis/arm labelling (the judge cannot tell which arm it is grading). |
| **AC.MGRL.6** | The experiment reports, separately, (a) the aggregate quality delta (generic lift) and (b) the theory-prediction discriminator (whether the gain concentrates on gate-flagged turns and tracks the firing trigger rather than generic task difficulty). | The result artefact reports both the aggregate delta and the per-trigger / flagged-vs-unflagged breakdown the discriminator pre-registered in AC.MGRL.4 requires; "the theory's prediction held" is reported as a distinct verdict from "escalation helped on average." |
| **AC.MGRL.7** | The slice ships default-OFF: enabling the deliberate layer is an explicit, reversible opt-in, and with it off the harness is unchanged. | With the layer disabled, the full existing turn-level test suite passes unchanged; enabling it is a single explicit, reversible switch. |
| **AC.MGRL.OA** *(outcome-altitude:true)* | Escalation fires through the **production entry-point** with **no pre-arranged state**: a real turn carrying a genuine trigger signal, run through the real gate path, produces an escalation decision + a deliberate-loop invocation + a recorded firing trigger. | A real invocation of the production turn-processing entry-point (no seeded gate state, no stubbed trigger) on an input engineered to carry a real low-confidence/novelty/stakes signal yields an observed escalation and a deliberate-loop run end-to-end. (`feedback_test_outcome_altitude_required`.) |

**Behaviour-count vs. criteria-count check (ODD §2.5 forward coverage):** the slice declares seven distinct behaviours (gate decision+trigger record; default-OFF no-op; gated loop with no-degradation guard; pre-registration-before-scoring; blind-judged baseline-vs-escalated comparison; generic-lift-vs-theory-discriminator separation; reversible default-OFF shipping) plus the outcome-altitude fire — eight ACs. They match.

---

## §6 Build steps (method-level guidance only — builder's call per ODD §1.1)

One slice, one logical deliverable; the builder may sub-seal if the gate and the loop and the experiment-harness warrant separate commits (`feedback_serialize_amendment_builds` if more than one build agent is ever used — this slice is single-tree, single-agent). Suggested ordering (advisory, NOT a requirement):

1. **Gate first.** The deterministic escalation decision + trigger-record, sibling to the `intent_classifier.py` shape (extend-or-add is the builder's call). Default-OFF wiring lands here (AC.MGRL.1, AC.MGRL.2, AC.MGRL.7).
2. **Pre-registration second — BEFORE any scored run.** Author + git-commit the pre-registration artefact: task set, metric definitions, "better" definition, theory-vs-generic discriminator. This commit MUST precede the first escalated-mode scored run (AC.MGRL.4). Authoring it before the loop is built is the safest ordering — it forces the success definition to be fixed before any result can bias it.
3. **Deliberate loop third.** The adversarial evidence-bound re-entrant loop with the no-degradation guard, invoked only on escalated turns (AC.MGRL.3). Reuse `framework/self-correction/` spine if it fits.
4. **Experiment harness + blind judge fourth.** The baseline-vs-escalated runner over the fixed task set, the hypothesis-blind judge, and the result artefact that reports generic-lift and the theory-discriminator separately (AC.MGRL.5, AC.MGRL.6).
5. **Outcome-altitude fire.** The real-entrypoint, no-pre-arranged-state escalation test (AC.MGRL.OA).

Tests are authored per-AC (the test name carries the AC ref per house convention). The builder owns file layout, function names, and code structure entirely.

---

## Primitive check (REQUIRED — new mechanism introduced)

Native Claude / Claude Code primitives considered for each new mechanism (per `claude-feature-awareness` + `tool-selection-rubric`):

- **The gate (per-turn escalation decision) → a deterministic classifier at the turn-level hook layer (UserPromptSubmit or the equivalent turn-entry surface), sibling to `intent_classifier.py`.** Native Claude Code hook event; deterministic, no LLM call. Alternatives considered + rejected: an LLM-per-turn judge (rejected — latency + `claude -p` cost on every turn, §3.1); a memory-rule "remember to think harder on hard turns" (rejected — discipline-as-text is the exact failure `feedback_structural_enforcement_on_recurrence` names; the gate must be structural).
- **The deliberate re-entrant loop → a gated harness component, candidate reuse of `framework/self-correction/`'s detection→review→verdict spine; LLM steps via `claude -p`.** Not the Anthropic SDK (`feedback_no_anthropic_api_key`). Default-OFF and gated, so it is off the per-turn hot path — latency is acceptable here by construction (D-MGRL.5).
- **The blind judge → a hypothesis-blind scorer; for machine-checkable tasks a deterministic checker, else a separate `claude -p` judge run with arm/hypothesis labels withheld.** The ONE place an LLM may be in the scoring loop — deliberately blind, off the per-turn path, and only if the task set isn't fully machine-checkable.
- **The pre-registration tamper-evidence → the git ref graph (commit-ancestry ordering), not a prose claim.** Native git; `feedback_published_state_only_from_git_refs` — pre-reg commit must be an ancestor of the first scored-run commit.
- **Default-OFF switch → an explicit reversible opt-in (env var / settings flag / config), not a code-path that's always partially live.** Native settings/env primitive; the failure class to eliminate is "the layer perturbs baseline even when 'off'."

---

## §7 Out of scope (deferred — named, not silently dropped)

- **The persistent, self-authored self-model + goal/valence stack + cross-session continuity (the proposal's recommendation 1, features 6–8) — this is SLICE 2.** Named explicitly per the dispatch. It is the proposal's highest-leverage and most theory-central mechanism, but it is a larger build with its own design surface (authorship of the self-model shifting *to the persona*, durable cross-session persistence, goal weighting). Designing it here would be scope-creep for a first slice and would couple the honest gate/loop experiment to a much larger, harder-to-measure change. Slice 2 gets its own plan-doc once slice 1's experiment pays off (the proposal §4: "If that pays off, graduate to the persistent self-model as the second, larger build").
- **The curated global workspace / deliberate working-set (rec 5, feature 1).** The `context_composer.py` / `keep_pace/` "bones" stay as-is; deliberate working-set curation is deferred.
- **A standalone surprise / prediction-error detector subsystem (rec 4 as its own mechanism), beyond whatever cheap expectation-violation signal the gate's trigger set can compute inline (§3.4).** If the cheap version isn't computable in this slice, the surprise trigger is deferred whole.
- **Endogenous goals + valence weighting and continuity-across-time (features 7–8)** — these travel with slice 2's self-model.
- **Any claim about phenomenal experience / consciousness.** The deliverable is honestly named (proposal §0): "an experiment in functional-consciousness emulation that reliably improves reasoning and tests the theory's behavioral predictions" — NOT "we made Claude conscious." This is a HARD boundary, not a deferral.
- **Publish.** LOCAL/experiment only; the owner gates any external framing of results (`feedback_build_forward_on_publish_pending`).

---

## §8 Halt triggers (in-flight; abort the build + surface)

1. **The gate cannot be made deterministic** — every plausible trigger proxy turns out to need an LLM call to compute → halt; surface the latency/cost collision (D-MGRL.1 is the load-bearing call; an LLM-per-turn gate is the thing this slice is built to avoid).
2. **A genuinely non-gameable, objective pre-registered metric cannot be defined for the chosen task set** → **HALT and say so loudly** (dispatch's explicit halt trigger). A soft metric that "looks objective" but measures generic quality lift or can be gamed is worse than no experiment — it manufactures false confirmation. Do NOT paper over this; re-pick the task set or surface that the experiment as scoped can't be honestly measured.
3. **The no-degradation guard cannot be built** — the deliberate loop cannot be made to reliably return the original answer when critique finds no improvement, so escalation degrades output on already-correct turns → halt; the proposal's §3 trap is then unavoided and the loop design needs revision before it ships.
4. **The default-OFF guarantee cannot hold** — the layer perturbs baseline even when disabled → halt; AC.MGRL.2/AC.MGRL.7 are non-negotiable (a perturbed baseline invalidates the whole experiment).
5. **The pre-registration would have to be written after a scored run** (ordering inversion) → halt; the §0 honest-boundary requires pre-reg to predate scoring, verifiable by git ancestry.
6. **Any ODD violation discovered in the proposal or surrounding loam code** → halt + surface per `feedback_subagent_odd_violation_halt`; do not silently extend it.

---

## §9 Bookkeeping

- `docs/STATE.md` — append a dated entry when the slice seals (the per-minor convention).
- The deliberate-reasoning-layer program needs a parent/program doc or roadmap row the builder updates as slice 1 seals and slice 2 opens — the builder or dispatcher records slice 1 SHIPPED-LOCAL and slice 2 as the named follow-on (mirrors the §7 split).
- This plan's §14 register (below, placeholder) is backfilled at seal via `loam amend seal --plan-doc` if this slice is sealed as an amendment; if it ships as an experiment artefact rather than a sealed-component amendment, the builder records the build decisions in the experiment's own result doc and notes that here.
- The pre-registration commit SHA + the first-scored-run commit SHA are recorded (the git-ancestry evidence for AC.MGRL.4).

---

## §10 F2 Ruthless Feedback (honest doubts; named design risks; Phase-1 review verdict carried in)

**Phase-1 adversarial review of the proposal — verdict per element (carried into the plan, per the dispatch):**

- **(a) Is the metacognitive GATE the right primary mechanism, and is its trigger set detectable here?** **KEEP, with one sharpen.** The gate is the most defensible mechanism in the proposal — it reproduces the actual human two-system shape rather than bolting "think harder" onto everything, and loam already has the exact precedent (`intent_classifier.py`: a deterministic per-turn classifier firing before interpretation). The sharpen: of the four named triggers, three (low-confidence, novelty, stakes) have plausible cheap deterministic proxies; **the fourth (prediction-error/surprise) is NOT cleanly detectable in this harness without maintaining an explicit expectation model**, which is a subsystem larger than this slice. The plan defers surprise unless a cheap version exists (D-MGRL.4, §7). Honest residual risk: "low self-confidence" is itself non-trivial to read off a model that is frequently confidently wrong — the proxy (hedging markers, etc.) is itself an approximation and may correlate poorly with actual correctness. This is named, not hidden; the experiment's per-trigger breakdown (AC.MGRL.6) will partly measure whether the confidence proxy is any good.
- **(b) Is the "evidence-bound re-entrant loop" defensible against the known failure mode that always-on self-critique DEGRADES output?** **KEEP — but only because the proposal itself already names the trap and the structural fix.** This is the single most important review finding. Always-on self-critique is a documented degradation mode (rationalization, post-hoc confabulation, talking past a correct first answer). The proposal's §3 names it and prescribes two structural defenses: the gate (so critique is not always-on) and evidence-binding (so critique cites why each step is sound rather than free-form self-narrating). I add a third, made an AC: **the no-degradation guard** — the loop must be structurally able to return the original answer (D-MGRL.2, AC.MGRL.3). Without that guard, the loop is a coin-flip that can make correct first answers worse. With the gate + evidence-binding + no-degradation guard + a blind-judged baseline comparison, the design is defensible. **This element would be a CUT if any one of those three guards were missing.**
- **(c) Are the pre-registered metrics + blind-judge protocol real and gameable-resistant, or hand-wavy?** **SHARPEN — this is where the proposal is thinnest and the plan does the most work.** The proposal §0/§4 states the *principle* (pre-register, blind judge, objective outcomes) correctly and forcefully, but does NOT specify a concrete metric, task set, or — critically — the **discriminator between the theory's specific prediction and generic quality lift.** That discriminator is the load-bearing gap: "the escalated arm scored higher" confirms *nothing* about the consciousness theory, because any "think harder" intervention produces that. The plan adds the discriminator as a pre-registered, separately-reported result (D-MGRL.3, AC.MGRL.6): the theory predicts the gain **concentrates on gate-flagged turns and tracks the firing trigger**, not that quality rises uniformly. The blind-judge protocol is real and gameable-resistant *if and only if* the task set has objective outcomes (the proposal insists on this) — the §8 trigger-2 halt exists precisely because if a non-gameable metric can't be defined, the honest move is to stop, not soften.
- **(d) What is unbuildable, underspecified, or scope-creep for a FIRST slice?** **CUT from slice 1 (correctly already cut by the proposal §4, reinforced here):** the persistent self-authored self-model + goal/valence stack + cross-session continuity (recs 1, features 6–8) — large, theory-central, but a separate build (→ slice 2, §7). The curated global workspace (rec 5) — deferred. A standalone surprise detector (rec 4 as its own subsystem) — deferred unless cheap (§3.4). **Underspecified in the proposal, now pinned by the plan:** the concrete metric/task-set, the theory-vs-generic discriminator, and the no-degradation guard. **Nothing in the slice-1 scope is unbuildable** as written — the gate, the gated loop, and a pre-registered blind-judged experiment are all buildable with existing loam primitives + `claude -p`.

**Standing design risks (slice-1 specific):**

- **RF-1 (the load-bearing risk). The whole experiment's honesty rests on a non-gameable, objective metric that also carries the theory-vs-generic discriminator — and that metric does not exist yet.** Evidence: the proposal §0/§4 states the principle but specifies no metric; the discriminator is entirely new in this plan. Alternative / mitigation: the metric + discriminator are pre-registered before any scored run (AC.MGRL.4), and §8 trigger-2 makes "can't define an honest metric" a HALT, not a soften. **The dispatcher should expect the experiment-design half to be the hard, slow part — not the code.**
- **RF-2. The "low self-confidence" trigger may be a poor proxy.** A model that is confidently wrong gives the gate no honest low-confidence signal exactly when escalation would help most. Evidence: well-documented LLM miscalibration. Mitigation: the experiment's per-trigger breakdown (AC.MGRL.6) measures whether escalations attributed to the confidence trigger actually correlate with quality gains; if the confidence proxy is worthless, the result will show it rather than hide it. This is a feature of the honest design, not a flaw to fix pre-experiment.
- **RF-3. A null or negative result is a real and likely outcome — and the design must treat it as a success of the method, not a failure to bury.** Evidence: gated deliberate loops can easily produce no measurable lift, or lift that is pure generic-quality (failing the discriminator). The honest design means a null result is *informative* (the theory's functional prediction did not hold on this task set) and must be reported as such. The pre-registration is what makes a null result publishable rather than quietly discarded — this is the entire point of §0. The dispatcher should be told up front: this experiment can honestly come back "no effect" or "generic lift only, theory-prediction not confirmed," and that is a valid, valuable outcome.
- **RF-4. Building the experiment harness and the layer in the same slice risks the experimenter unconsciously tuning the layer to the metric.** Evidence: standard researcher-degrees-of-freedom risk. Mitigation: pre-registration commits the metric before the loop is tuned (build-step ordering in §6 puts pre-registration BEFORE the loop), and the judge is blind. Residual risk named: the builder still chooses the task set, and task-set choice is itself a degree of freedom — the dispatcher may want the task set reviewed before it's locked.

---

## §11 Provenance trail

- `workspace/.scratch/claude-output/consciousness-emulation-harness-design.md` — the source proposal. §0 (honest boundary, HARD requirement), §1.2/§1.3/§1.5 (metacognition / gate / re-entrant loop mechanisms), §3 (the traps: always-on degradation, evaluation confirmation bias, cost), §4 (smallest viable first experiment — the exact scope of this slice), §2 recs 2+3 (gate + evidence-bound loop). Source of truth for scope.
- `framework/primary-persona/src/loam/primary_persona/intent_classifier.py` — the deterministic per-turn UserPromptSubmit classifier (amendment #144 Scope A); the proven precedent for the gate's shape (regex-scored, <5 ms, zero token cost, fires before interpretation). Cited as precedent, not as a method requirement.
- `framework/self-correction/` — the existing detection→review→verdict→record framework (depth-cap, trigger-dedup, same-class-cascade, outcome-altitude real-entrypoint test) — the structural cousin of the deliberate loop. Candidate reuse; builder's call.
- `framework/primary-persona/src/loam/primary_persona/context_composer.py` + `keep_pace/` — the "global workspace bones" the proposal §5 names; explicitly OUT of this slice's scope (rec 5 deferred).
- `docs/design/odd.md` + `plugins/dev-sdlc/docs/odd-methodology.md` §2.4/§2.5 — the no-method-in-acceptance + forward/reverse-coverage rules this plan's ACs are authored against.
- `plugins/dev-sdlc/docs/conventions/plan-docs.md` — the plan-doc shape + the REQUIRED Primitive-check section this plan honours.
- `docs/VALUE_PROPOSITION.md` — AC.PO.1 (harness test) + AC.PO.2 (primary-persona test); the prime objective this slice ladders to (`feedback_value_proposition_as_prime_objective`).
- Luke's north-star statement (captured 2026-06-22, episode turn `c34a916b`): "improve the quality of your response as a layered stack on top of the inferencing engine underneath, not relying on them to do the improvements for us" — the user-intent this slice serves.
- `feedback_test_outcome_altitude_required` — the basis for AC.MGRL.OA (real-entrypoint, no-pre-arranged-state escalation fire).
- `feedback_no_anthropic_api_key` — every LLM step (deliberate critique, optional blind judge) via `claude -p`, never the Anthropic SDK.
- `feedback_published_state_only_from_git_refs` — the pre-registration tamper-evidence is git-ancestry (pre-reg commit ancestor of first scored-run commit), not prose.
- `feedback_version_numbers_at_release_time` — scope-descriptive slug, no pre-allocated version.

---

## §14 Method-decision register (populated at build time)

Placeholder mirroring the D-MGRL.* IDs declared in §3 + any D-build.* the builder narrates. Backfilled with commit SHAs at seal (or in the experiment result-doc if shipped as an experiment artefact rather than a sealed amendment).

- D-MGRL.1 (deterministic gate) — SHA: _pending build_
- D-MGRL.2 (adversarial evidence-bound loop + no-degradation guard) — SHA: _pending build_
- D-MGRL.3 (pre-registration + blind judge + theory-vs-generic discriminator) — SHA: _pending build_
- D-MGRL.4 (slice-1 trigger set) — SHA: _pending build_
- D-MGRL.5 (default-OFF cost governor) — SHA: _pending build_
- D-build.* (builder-narrated method decisions) — _pending build_

## §15 Backwards-compat verification (populated/confirmed at build time)

- With the deliberate layer disabled (default), the full existing turn-level test suite passes unchanged (AC.MGRL.7).
- No existing turn-processing behaviour changes on a non-escalated turn (AC.MGRL.2).

## §16 Halt-and-surface findings (raised + ruled at plan-authoring)

- The prediction-error/surprise trigger is NOT cleanly detectable in this harness without an expectation-model subsystem larger than this slice — ruled deferred unless a cheap version exists (D-MGRL.4; §3.4 surface flagged for dispatcher).
- The proposal specifies no concrete metric/task-set/discriminator — the plan adds the theory-vs-generic discriminator as a pre-registered, separately-reported result; if a non-gameable objective metric cannot be defined, §8 trigger-2 makes it a HALT, not a soften (RF-1).
- Whether all three observable triggers (vs. a single one) are in slice-1 scope is partly an experiment-design call surfaced to the dispatcher (§3.4) — recommendation: all three observable, because the discriminator is stronger when escalation is attributable to a specific trigger.
