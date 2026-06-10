# GENERAL BUILD-FROM-INTENT — the corrected #86 capability (readiness program W1+W2 core)

**Status:** sub-plan-doc, **OWNER-RATIFIED 2026-06-09 (G2 approved, Discord msg 1514112412, 22:42 CDT). D5 ruled: dispatcher authors the off-vertical proof prompt, SEALED PRE-BUILD (written 22:45 CDT, SHA-256 ec34f279fc59244b0821466392d1bc354207574fcbc71a94c6bc4ddb9a77cb42, path withheld from builders) — Luke's sharpening: pre-commitment so the prompt cannot be tuned to the implementation. Build authorized.** The build queues behind the memory-recall cycle seal (`memory-decision-ledger-surfacing-dispatch-packs`, in-build in this tree 2026-06-09; one tree, builds serialize per `feedback_serialize_amendment_builds`). · **Date:** 2026-06-09
**WD:** `/Users/lukeivers/loam` (canonical loam)
**Parent / motivating artefacts:** the owner's verbatim spec (Discord msg 1514064080, 2026-06-09): *"It needs to be able to take their input, ask meaningful questions if it has any, do any research that's valuable to align expectations with industry standards, plan, build, keep the user in the loop during the process so they can feel comfortable that things are moving along."* Constraints from the same ruling: **NO faking, NO hardcoded objectives, NO pre-built tools posing as generated, NO pre-gaming. Must run on a FRESH loam workspace in front of strangers** (Alan/Aaron type the ask, live). Program context: `pos3/workspace/strategy/revenue/tilth-loam-readiness-program.md` (W1+W2); corrected-target history: tasks #86 + #109; binding doctrine: `feedback_honest_capability_demo_no_overfit.md` including the June-8 recurrence — **this plan builds the CORRECTED target that demo should have been.**

---

## OWNER SUMMARY (rule from this — full detail below)

1. **What this is:** the build plan for the real thing — a stranger types a vague ask into a fresh loam workspace, and loam understands it, asks questions only when it genuinely has them, researches how practitioners actually do that work, then **generates the tool, the data shape, and the pass/fail test itself**, builds to convergence, and keeps the person informed in plain language the whole way. Your five-clause spec, one slice per clause, plus a proof slice.
2. **Nothing is pre-built or pre-gamed.** The June-8 demo's shortcut (pre-built tool, hardcoded objective, no research) is retired by name. Every claim in this plan is gate-backed: the tool, gate, and objective must verifiably come into existence DURING the run, on a fresh workspace, from wording the builders never saw.
3. **Six slices:** (S1) any vague build ask triggers live intent-understanding + meaningful questions only when real ambiguity exists; (S2) an in-loop web-research step producing a practitioner-grounding doc that shapes the generated acceptance test and flags where a human expert is needed; (S3) the generative middle — loam derives the objective and generates tool + data shape + gate, zero vertical-specific code; (S4) build-to-convergence becomes canonical loam default with the proven timeout discipline; (S5) the in-loop progress surface — honest plain-language stage updates and heartbeats, no silent stretches; (S6) the proof runs — Alan's back-office trio (Apps 1/3/2: reconciliation, customer-list dedupe, books migration) generated honestly on fresh workspaces, PLUS at least one off-vertical run as the standing anti-rigging probe.
4. **The two bars:** Lubbock-demo-ready = S1–S5 working + the S6 runs logged, honestly scored, reproducible on demand. Production-customer-ready = the named follow-ons on top (smoke cadence as a release regression, research/rulings flowing into dispatch memory packs, expert-gate flags routing to a named human).
5. **One call I need from you (D5):** who authors the off-vertical proof prompt. Recommended: you (or Eric) write it, the builders never see it before the run — the strongest honest answer to "how do we know it isn't rigged."
6. **Cost:** roughly 17–34 agent-hours (midpoint ~25h, ≈2–4 days of background work), matching the program's independent estimate. Each slice carries a pass/fail measured prediction.
7. **Honest risk, named:** the generative middle (S3) is the genuinely hard step and carries the widest estimate; full generation will make live runs longer than the old pre-built-tool runs (~15–45 min estimated vs 6–15 min observed), which likely makes the same-morning-real-run demo rung (F2) the realistic meeting shape — that's the program's W4 call, not this plan's.
8. **Status:** DRAFT. Your ratification is program gate G2 and dispatches the build, queued behind the memory-recall seal.

---

## Header detail

**Predecessors (load-bearing prior seals + seams, Tier-0 verified on disk/git in `/Users/lukeivers/loam`, 2026-06-09):**

- **Intent-extraction seam (#56)** — `framework/workspace-bootstrap/src/loam/workspace_bootstrap/intent_extract.py` (read this session): `IntentExtractor` Protocol, `ClaudeIntentExtractor` (one bounded spawn-isolated `claude -p` call; extracts the literal intent AND a slightly-deeper inferred end-intent), `DisabledIntentExtractor` default, fail-soft regex fallback (AC.INTENT.1–6 tests on disk). **Currently fires at first-run intake only** — S1 makes it per-request.
- **handsoff-loop pipeline (sealed, sidecar `e0b71cbc`)** — `framework/tools/handsoff-loop/`: `intake.py` (elicit-the-minimum bounded questions, single plain-language approval gate, independent faithfulness check, sealed bounded goal-refinement construct), `verify.py` (frozen hash-pinned acceptance authored before any sub-agent runs and seen by none; independent tool-executing judge + anti-overfit held-out check), `orchestrator.py` (**post-migration in-session dispatch verified**: `set_swarm_in_session_dispatcher` routes sub-tasks through the host session's Task primitive, no detached `claude -p`, lines ~32–113 read this session), the sealed behavioral-refine bounded re-drive (`loop-behavioral-refine-cycle`, sealed), honest-negative as first-class outcome. **This is the spine the cycle composes on** (Lens 1/2) — the gap is the generative middle and the research step, not the loop.
- **Build-to-convergence prior art (#111)** — `pos3/.scratch/claude-output/loam-demo-fresh/improve_loop.py`: proven 3× (71.8%→97.4% autonomous), **NOT in canonical loam**; binding lesson carried forward: single generous ~1200s ceiling, NO retry-on-timeout (retry doubles the wait on a slow-but-working agent).
- **The anti-pattern to retire** — `pos3/.scratch/claude-output/loam-demo-fresh/loam_autoroute.py` (header read this session): its own honesty block admits the route is "a deterministic router for the single wired vertical"; the objective sentence is hardcoded, the tool pre-built, the gate reconciliation-specific. **A shortcut to retire, not a foundation** (tasks #86/#109 verbatim). It lives in pos3 scratch, not the loam tree — retirement = nothing in canonical loam references it (verified: zero references in this tree today) + the demo path never invokes it again + a dated retirement note in pos3 (§9).
- **Fence precedent** — three sealed cycles on this exact spine (`handsoff-loop-real-build`, `loop-goal-refinement`, `loop-behavioral-refine-cycle`) all sealed against the **workspace-bootstrap anchor** (seal test `framework/workspace-bootstrap/tests/test_no_sealed_amendments.py`, whose live `allowed_prefixes` admit `framework/tools/`, `framework/hands-off-lifecycle/`, `plugins/loam-skills/`, `framework/workspace-bootstrap/`, `docs/plans/` — verified at lines ~279–343 this session). Same anchor here.
- **Composition seam (NOT a dependency)** — `docs/plans/memory-decision-ledger-surfacing-dispatch-packs.md` S4 (dispatch memory packs) is in-build in this tree now. S2's grounding docs are written as durable, indexable records so the packs can carry them into later builds once that cycle seals + activates — per-customer learning compounding (program W2.5). **No slice in this plan depends on it.**

**BASELINE candidate:** walked at apply-time per the #142 baseline-walk pattern (`baseline: null` in the draft manifest); the build queues behind the memory-recall seal, so the walk starts from whatever commit carries this plan post-seal.
**Components:** one anchor — `workspace-bootstrap` (per the three sealed precedents); all pipeline edits land under its admitted prefixes (`framework/tools/handsoff-loop/`, `framework/workspace-bootstrap/`, `plugins/loam-skills/`, tests under `framework/hands-off-lifecycle/`).
**Status-file target:** `docs/STATE.md` + readiness-program backfill (§9).
**Quality bar:** ODD §2.5 — every AC outcome-shape, method-in-AC test passed on each (each satisfiable by >1 method); ≥1 outcome-altitude AC per family (production entry points, fresh workspace, no pre-arranged state); NO Anthropic SDK/API key (every model call is the real `claude` binary through the sealed spawn-isolation surface); the honest-demo doctrine's three sharpened rules are binding constraints, not aspirations.

---

## §1 Summary / TL;DR

**What ships — the general path, end to end, on a fresh workspace:**

> vague ask → live intent-extraction + plain-language confirm (S1) → meaningful questions ONLY when real ambiguity exists (S1) → bounded web research into practitioner norms → durable grounding doc → informs the generated gate + flags expert-gate points (S2) → loam derives the objective and GENERATES the tool, the data shape, and the acceptance gate — nothing pre-built, nothing hardcoded, zero vertical-specific code (S3) → build-to-convergence with the proven timeout discipline, honest negative preserved (S4) → plain-language progress the whole way, no silent stretches (S5) → proof: Apps 1/3/2 + ≥1 off-vertical run, honestly scored, logged, reproducible (S6).

This maps the owner's five spec clauses one-to-one: *take their input* = S1; *ask meaningful questions if it has any* = S1; *do any research that's valuable to align expectations with industry standards* = S2; *plan, build* = S3+S4; *keep the user in the loop* = S5. S6 is the proof the room can trust.

**What the June-8 demo faked, killed structurally here:** hardcoded objective → AC.REQ.3 + AC.GEN.OA (objective derived from THAT run's ask, evidenced); pre-built tool → AC.GEN.1/OA (tool + gate + data shape born during the run, git/mtime evidence); reconciliation-specific gate → AC.GEN.2 (zero domain-keyed branches in framework source; one code path serves all S6 domains); zero research → AC.DGR.\* (live citations or an explicitly-flagged ungrounded build — never silent fake grounding).

**AC families:** `AC.REQ.*` (per-request intent + questions), `AC.DGR.*` (domain grounding research), `AC.GEN.*` (generative middle), `AC.CVG.*` (convergence as canonical default), `AC.PRG.*` (in-loop progress), `AC.SMK.*` (honest smoke proof) — each with its own outcome-altitude AC.

**Key decisions baked (full list + recommendations in §3):** compose on the handsoff-loop spine, single workspace-bootstrap fence (D1); convergence delivered by extending the sealed re-drive/verify spine with the #111 timeout lesson, not by importing improve_loop wholesale (D2 — method latitude stays with the builder); grounding docs as durable indexable records, packs-compatible but not packs-dependent (D3); one amendment, six slices, pipeline order (D4); off-vertical prompt authored by the owner, unseen by builders (D5 ★ — the one owner call); per-request routing scoped to build-shaped asks this cycle (D6).

**F2 RF on scope realism:** this cycle makes the general path real and proven on four domains. It does NOT make gate-quality computable (a practitioner-credible gate is judged, not computed — §10 #1), does NOT ship the production-bar follow-ons (release-regression cadence, pack carriage verification, expert-gate routing to a named human — §7), and does NOT decide the meeting-day demo rung (the program's W4 owns that; §10 #3 feeds it honestly).

---

## §2 Placement decisions

| Item | Placement | Rationale |
|------|-----------|-----------|
| Per-request intent routing + meaningful questions (S1) | `framework/tools/handsoff-loop/` intake surface + `plugins/loam-skills/skills/handsoff-loop/` (trigger/contract doc) + the sealed `intent_extract` seam consumed from `framework/workspace-bootstrap/` | The SKILL trigger is the Claude-native per-request detection primitive (Lens 1); the intake already owns elicit-the-minimum + the single approval gate; the extractor seam is sealed and importable. Composing these three closes W2.1 without a new component. |
| Domain-research step (S2) | `framework/tools/handsoff-loop/` — a pipeline stage between approved intent and gate-freeze; grounding doc written to a predictable workspace path as a durable frontmatter'd record | Research must be IN the build (doctrine sharpened-rule 3), so it lives in the pipeline, not as a separately-invoked skill; the durable-record form is the packs composition seam (D3). |
| Generative middle (S3) | `framework/tools/handsoff-loop/` — the stage that derives the objective + generates tool design, data shape, and gate text, feeding the EXISTING freeze (`verify.py`) untouched in contract | The freeze/judge spine is the sealed honesty machinery; generation feeds it rather than replacing it — frozen-unseen + independent-judge contracts are preserved by construction. |
| Convergence as canonical default (S4) | `framework/tools/handsoff-loop/` orchestration leg (the sealed bounded re-drive + verify spine, extended with the timeout discipline + own-the-wait) | Lens 1: the sealed re-drive IS convergence machinery already in canonical; #111's improve_loop is prior art whose timeout lesson is binding, not a module to import wholesale (D2). |
| In-loop progress surface (S5) | Pipeline-emitted progress states (run record on disk) + persona narration contract in `plugins/loam-skills/` | The Claude primitives carrying it, named: **in-session subagents (Task primitive)** for the build legs; **dispatcher-side Monitor** for own-the-wait polling (the #99-proven pattern); **SubagentStop hook events** as completion signals; **the persona's plain-language narration** as the user-facing voice (channel `reply`/`edit_message` when a channel is connected; terminal narration on a fresh workspace). Method per leg is the builder's call; the primitives are the named toolkit. |
| Honest smoke proof (S6) | Runs execute in **fresh workspaces OUTSIDE this tree**; a minimal reproducible run command + the run log land under `framework/tools/` | The proof must be stranger-fresh by definition; the loam tree carries only the harness + the log, never run-specific code. |
| Retirement note for `loam_autoroute` | pos3 bookkeeping (§9), not a loam edit | The artifact lives in pos3 scratch; canonical loam already has zero references (verified). |

**Out of placement (NOT this cycle):** anything in `frame-kernel` or the memory-recall surfaces (in-build; a needed edit there is a HALT, §8 #4); W3 production-delivery machinery; the broader any-request four-step loop (D6).

---

## §3 Named decisions (with recommendations) — surface to Luke

★ flags the one genuine owner call; the rest are autonomous method-calls recorded for the trail.

### D1 — Compose on the handsoff-loop spine under the single workspace-bootstrap fence. **Autonomous; recorded.**
- *Why:* the sealed pipeline already owns intake honesty (single approval gate, faithfulness check, bounded goal-refinement), freeze-isolation, independent judging, bounded re-drive, and post-migration in-session dispatch — re-implementing any of it beside itself is the Lens 1 violation, and three sealed precedents establish this exact fence anchor. The gaps this cycle fills (per-request entry, research stage, generative middle, progress surface) are stages and seams ON that spine.
- *Alternative considered:* a new `build-from-intent` component wrapping handsoff-loop. Rejected: it would duplicate the orchestration contract and put the demo path on younger, less-proven machinery.

### D2 — Convergence vehicle: extend the sealed re-drive/verify spine to canonical-default convergence, carrying the #111 timeout lesson as a binding constraint; do NOT import `improve_loop.py` wholesale. **Method-call; builder latitude preserved.**
- *Why:* the sealed `loop-behavioral-refine-cycle` already delivers bounded iterate-on-failure with failure context under the existing cost/wall ceiling — that is convergence machinery in canonical loam. What's missing is the leg-timeout discipline (single generous ~1200s-class ceiling, terminal on timeout, NO retry — the empirically-learned #111 rule) and dispatcher-side own-the-wait. The builder may import specific improve_loop mechanics where they're better; the AC pins outcomes, not lineage.

### D3 — Grounding docs as durable, indexable records (packs-compatible, packs-independent). **Autonomous.**
- *Why:* program W2.5 — research outputs should accrue as per-customer learning. Writing the grounding doc as a frontmatter'd durable record at a predictable workspace path makes it carryable by the dispatch memory packs the moment that cycle activates, with zero coupling now. The cheap verification of actual pack carriage is a named follow-on (§7), not an AC here.

### D4 — One amendment, six slices, pipeline order S1→S2→S3→S4→S5→S6. **Method-call.**
- *Why one amendment:* shared fence, shared review, one seal window; the tree serializes regardless. *Why pipeline order:* S2's grounding-doc contract pins S3's input (building the lowest-confidence slice against a real grounding doc, not a stub); S4 must precede S6 (no end-to-end run converges without it); S5 precedes S6 so the proof runs exercise the progress surface; S6 last because it is the proof of everything before it. Honest cost: a mid-cycle halt stalls the seal of earlier slices — acceptable, the slices are useless to the room individually.

### D5 — ★ Off-vertical proof prompt authorship: **owner-authored (you or Eric), unseen by any build agent until run time** vs builder-chosen second archetype. **RECOMMEND: owner-authored. The one owner call.**
- *Why:* the off-vertical run exists to answer "how do we know it isn't rigged." A builder-chosen archetype is open to the (fair) suspicion of choosing what the path is secretly good at; a prompt the builders literally never saw, from a domain you pick, is the strongest honest answer and costs you one sentence. AC.SMK.OA is written to this shape.
- *The alternative, honestly:* builder-chosen is faster (no owner round-trip) and still off-vertical; it just proves less. If you don't want to author one, say so and AC.SMK.OA degrades to builder-chosen-with-named-caveat.

### D6 — Per-request routing scope: build-shaped asks this cycle; the any-request four-step loop is deferred. **Method-call; scope-guard named.**
- *Why:* the owner spec is about build asks ("take their input… plan, build"); the broader continuously-learning interaction model (loam task #34, the prime-directive engine) is its own workstream. Scoping S1 to build-shaped asks keeps this cycle's fence tight and the demo path short. The SKILL trigger's existing soft-phrasing recognition already covers the non-technical wording space.

---

## §4 Spec-objective placement

- **Binds to:** the owner's verbatim 2026-06-09 spec (header) — five clauses mapped one-to-one to S1/S1/S2/S3+S4/S5 (§1), with the same ruling's four constraints (no faking / no hardcoded objectives / no pre-built-posing-as-generated / no pre-gaming) carried as fence-level hard constraints (§5) and gate-backed ACs, not narrative promises.
- **Ladders up to:** **VALUE_PROPOSITION prime objective / Lens 0** — this IS the prime directive's primary surface: the user brings WHAT (a vague ask in their own words), loam owns HOW (research, plan, generate, build, verify), with the protection floor active (no inventing things: the grounding step + judge; no broken surrounding work: fresh-workspace isolation; honest claims: the honest-negative + claim discipline). Task #86's own text: "This IS the loam prime directive."
- **Program placement:** readiness-program W2.1–W2.4 + W1.2–W1.3; gates Tilth Slice 1 (the Lubbock meeting) per the program's sequencing table; Slice 0.5's redefinition (general path, autoroute retired) is executed by this plan.
- **Binding doctrine:** `feedback_honest_capability_demo_no_overfit` — sharpened rule 1 (middle-is-real) → AC.GEN.OA's born-during-the-run evidence; rule 2 (no special code for the demo vertical) → AC.GEN.2; rule 3 (domain-grounding in the build) → AC.DGR.\*.

---

## §5 Sealed-component fence

**One anchor: `workspace-bootstrap`** (seal test `framework/workspace-bootstrap/tests/test_no_sealed_amendments.py`, sidecar `framework/workspace-bootstrap/tests/SEAL_COMMIT`; live allowed prefixes admit `framework/tools/`, `framework/workspace-bootstrap/`, `framework/hands-off-lifecycle/`, `plugins/loam-skills/`, `docs/plans/` — verified this session). Mirrors the `handsoff-loop-real-build` / `loop-goal-refinement` / `loop-behavioral-refine-cycle` precedents. `extra_allowed_prefixes` EMPTY.

**Fence (binding):**
- Pipeline stages + seams land under `framework/tools/handsoff-loop/` + `plugins/loam-skills/skills/handsoff-loop/`; intent-seam adjustments (if any) under `framework/workspace-bootstrap/`; AC tests under the admitted test prefixes. All additive in contract.
- **Preserved byte-for-byte in outcome:** the frozen-unseen contract (acceptance hash-pinned before any sub-agent, seen by none — a leak is a refusal); the independent-judge contract (sub-agent self-reports never the done signal); the honest-negative terminal (never retried-to-green, never softened); the sealed goal-refinement intake construct (NOT modified — the loop-goal-refinement §8.4 halt stands); AC.FOUND.0 (the decompose→dispatch→judge core is consumed, never re-proved); the sealed spawn-isolation surface on every model call; the in-session dispatcher contract.
- **Forbidden without a halt:** any domain-keyed branch in framework source (the no-vertical-code constraint is owner-hard); any edit to `frame-kernel` or the in-build memory-recall surfaces; any `verify.py` spine redesign; any LLM/API call via the Anthropic SDK/key anywhere; any weakening of an existing `AC.INTENT.*` / `AC.GR.*` / `AC.BRC.*` / `AC.TPI.*` guarantee.

Seal via `loam amend apply` + `loam amend seal` — **name `loam amend apply` explicitly in the build dispatch** (`feedback_dispatch_explicit_loam_amend_apply`); all slices serialize in one tree; NEW commits only, no `--amend`. LOCAL SEAL ONLY — publish is a separate owner-asked action.

---

## §6 Acceptance criteria (outcome-shape; method-in-AC test passed on each)

AC IDs scope-descriptive. Each AC is satisfiable by more than one method; method is the builder's call.

### AC.REQ.\* — per-request intent + meaningful questions (S1)

**AC.REQ.1** — In an established workspace (post-onboarding), a vague build-shaped ask in plain language yields — before any build begins — an inferred end-intent surfaced back in plain language for confirmation, derived live from THAT ask (provably non-canned: materially different asks produce materially different inferences; rewordings of the same ask produce equivalent substance, not identical strings). *(Outcome: the spec's "take their input"; whether via the sealed extractor seam or another live path is the builder's call.)*

**AC.REQ.2** — When the ask leaves a build-shaping question genuinely open, the user gets a bounded number of meaningful plain-language questions before the confirm; an unambiguous ask proceeds with zero questions. Never a spec interview. *(Outcome: "ask meaningful questions IF IT HAS ANY" — both halves binding.)*

**AC.REQ.3** — The stated objective for any run is derived from that run's ask and echoes its specifics; no objective text exists in the pipeline source; two different asks produce two different stated objectives. Canonical loam contains zero references to the retired autoroute artifact. *(Outcome: the hardcoded-objective failure is structurally impossible.)*

**AC.REQ.OA (outcome-altitude: true)** — On a FRESH workspace through the production persona entry point with NO pre-arranged state, a typed vague ask whose wording no build agent has seen produces the plain-language confirm (and questions iff ambiguous), and the confirmed objective carries the ask's specifics. *(The live-demo opening segment, as a standing test.)*

### AC.DGR.\* — domain-grounding research (S2)

**AC.DGR.1** — Between intent confirmation and gate-freeze, the pipeline produces a domain-grounding record — how practitioners actually do this work, the standards and expectations the deliverable should align with — sourced from web research performed DURING the run (citations resolve to real sources fetched that run), written as a durable record at a predictable workspace path. *(Outcome: the spec's "research that's valuable to align expectations with industry standards," in the build, not a follow-up.)*

**AC.DGR.2** — The generated acceptance gate demonstrably reflects the grounding record: at least one gate criterion is traceable to a named practitioner norm; where research cannot settle a judgment standard, the record flags an expert-gate point in plain language instead of inventing a standard. *(Outcome: a gate a practitioner would nod at, or an honest flag where a human is needed.)*

**AC.DGR.3** — Research is bounded (named time/call budget) and honest under failure: research unavailability yields an explicitly-flagged ungrounded build the user is told about — never silent fake grounding, never invented citations. *(Outcome: the claim-or-cite discipline on the research surface.)*

**AC.DGR.OA (outcome-altitude: true)** — On a fresh workspace with NO pre-arranged state, a real archetype ask produces a grounding record whose citations resolve live, and the frozen gate text contains ≥1 criterion traceable to that record. *(The "it's reading how accountants actually do this" moment, gate-backed.)*

### AC.GEN.\* — the generative middle (S3)

**AC.GEN.1** — From the confirmed intent + grounding record, the pipeline derives the objective and GENERATES the deliverable: the tool, its data shape, and its acceptance gate — none of which exists anywhere before the run (the workspace contains no pre-built deliverable; the gate is authored during the run and hash-pinned before any build agent sees work, preserving the frozen-unseen contract). *(Outcome: the real middle — the thing the demo faked.)*

**AC.GEN.2** — Zero vertical-specific code: framework source contains no branch keyed to a business domain, and one identical pipeline code path serves materially different domains — evidenced by the S6 runs sharing that path. *(Outcome: doctrine sharpened-rule 2, structurally checkable.)*

**AC.GEN.3** — The confirm surfaces the form-factor decision (clickable app / CLI / service) in plain language, and the verdict states judge-scope honestly — what the gate did and did not verify about the result, in words a non-technical user understands. *(Outcome: #86's form-factor default + judge-scope-honesty.)*

**AC.GEN.OA (outcome-altitude: true)** — On a FRESH workspace through the production entry point with NO pre-arranged state, an unseen vague ask yields a working generated deliverable that passes its own loam-authored frozen gate — with on-disk evidence (git history / mtimes) that tool, gate, and objective all came into existence during the run — or a definite, evidence-named honest negative. *(The corrected June-8 demo, as a standing test.)*

### AC.CVG.\* — convergence as canonical default (S4)

**AC.CVG.1** — On a fresh workspace, the build leg iterates toward the frozen gate as default behavior: a failed check re-drives bounded refinement carrying the failure context; gate-pass and definite honest negative are the only terminals; no retry-to-green path exists. *(Outcome: convergence is what loam DOES, not a separately-summoned script.)*

**AC.CVG.2** — Long-leg timeout discipline: each agent leg runs under a single generous named ceiling; a timeout is terminal for that leg with the state honestly recorded — never an automatic retry-on-timeout. *(Outcome: the #111 empirical lesson, binding; the ceiling value is a named tunable.)*

**AC.CVG.3** — Own-the-wait: while a build leg is in flight, the dispatching session tracks liveness from run artifacts (artifact-probe class evidence, not poller-cadence inference), and the run record reflects real progress states consumable by S5. *(Outcome: the #99 finding structurally closed for this pipeline.)*

**AC.CVG.OA (outcome-altitude: true)** — Through the production entry point on a fresh workspace with NO pre-arranged state, a generated build whose first gate check fails converges to a pass (or a definite honest negative) within the bounded re-drives, with the full iteration trail on disk. *(The 71.8%→97.4% class of run, on canonical machinery.)*

### AC.PRG.\* — in-loop progress (S5)

**AC.PRG.1** — Throughout a run, the user receives plain-language stage updates (understanding → asking → researching → planning → building → checking → done/negative), each saying what is happening and what comes next; during long legs, no user-visible silence exceeds a named heartbeat interval while work is active. *(Outcome: the spec's "keep the user in the loop… comfortable that things are moving along.")*

**AC.PRG.2** — Every progress claim corresponds to verifiable run-record state — no narrated progress that is not actually occurring; waits are stated honestly with rough time expectations in plain language. *(Outcome: narration-is-not-action, enforced on this surface.)*

**AC.PRG.OA (outcome-altitude: true)** — A fresh-workspace run observed end-to-end: from typed ask to verdict, gaps between user-visible updates stay within the heartbeat bound during active work, and an after-the-fact audit matches every update's claim against the run record with zero unverifiable claims. *(The live-room comfort test, as a standing test.)*

### AC.SMK.\* — honest smoke proof (S6)

**AC.SMK.1** — Three back-office archetype runs — App 1 (intake+reconciliation class), App 3 (one-customer-list / dedupe-and-match class), App 2 (books clean-up/migration-mapping class), per the master proposal's year-one trio — each executed on its own fresh workspace through the one general path, each producing a generated deliverable scored against a loam-authored frozen gate, each logged unfiltered: result, fails included, wall-clock, where human gates fired. *(Outcome: the honest W1 smoke cases — generated, not pre-built.)*

**AC.SMK.2** — At least one OFF-vertical run (a domain outside back-office/accounting entirely) through the identical code path, same logging discipline. A pipeline change that improves the trio but degrades the off-vertical run does not land. *(Outcome: generalization IS the product; the standing anti-overfit probe.)*

**AC.SMK.3** — The run log is a room-ready artifact: every number carries its run-of-origin, every run names its archetype + workspace + commit, and any logged run is reproducible on demand by one documented command. *(Outcome: the program's W1 logged-actuals cadence, seeded.)*

**AC.SMK.OA (outcome-altitude: true)** — A run whose prompt was authored by someone other than any build agent (per D5: owner-authored, unseen until run time), on a fresh workspace with NO pre-arranged state, completes the full path and is scored honestly — pass or fail, reported straight. *(The strongest pre-stranger rehearsal of the live demo.)*

---

## §7 Out of scope (deferred + when)

- **Release-regression smoke cadence (program W1.4 / production bar)** — the S6 log seeds it; graduating it into every-release regression composes with the existing HARD-smoke-per-minor discipline in a follow-on cycle.
- **Dispatch-pack carriage verification (program W2.5)** — grounding docs are written packs-compatible NOW (D3); verifying a later build's dispatch bundle actually carries a prior run's grounding record is a ~1–2h follow-on AFTER the memory-recall cycle seals + its fragment activates.
- **Expert-gate routing to a named human (production bar)** — this cycle flags expert-gate points in plain language (AC.DGR.2); routing them to a named reviewer (Eric) is pilot-phase work (program W2 production bar).
- **W3 production-delivery machinery** (deployment plugin, tenant isolation, security floor, connectors) — gates the pilot, not the meeting; docs/design only pre-meeting per the program.
- **The any-request four-step interaction loop** (D6) — loam task #34's workstream; this cycle covers build-shaped asks.
- **Meeting-day demo rung choice (F1/F2/F3) + narration script + claim audit** — program W4; this plan feeds it the honest timing data (§10 #3) and the S6 artifacts.

---

## §8 Halt triggers (abort the in-flight build + surface)

1. **A credible gate for an archetype can't be generated without vertical-specific code creeping into framework source** — halt; the no-special-code constraint is owner-hard (doctrine rule 2), and the answer is never a domain branch.
2. **The bounded research step cannot produce live-resolving citations in the build environment at all** (e.g., no web access from the pipeline's execution context) — halt + surface the environment ruling; AC.DGR.3's fail-soft covers runtime blips, not a structurally research-blind pipeline.
3. **Satisfying any AC would require modifying the sealed goal-refinement intake construct, the verify spine's freeze/judge contracts, or re-proving AC.FOUND.0** — halt (the loop-goal-refinement §8.4 precedent stands).
4. **Any needed edit lands outside the workspace-bootstrap fence** — especially `frame-kernel` or the in-build memory-recall surfaces — halt; never silently widen the fence.
5. **Any change would weaken the honest-negative terminal, the frozen-unseen contract, or introduce a retry-to-green / retry-on-timeout path** — halt; these are the honesty load-bearers.
6. **A slice only works in pos3 / a dev-configured workspace** — halt; stranger-fresh-workspace operation is the spec's hard constraint, not a nice-to-have.
7. **An AC drifts to method-in-AC during build** — fix the AC text (doc-only) per `feedback_loose_AC_text_fix_AC_not_implementation`, never the implementation.
8. **ODD violation discovered in the work or surrounding code** — halt and surface per `feedback_subagent_odd_violation_halt`; never silently extend.

---

## §9 Bookkeeping (backfill on seal)

- **`docs/STATE.md`** — record the cycle: general build-from-intent (per-request intent, in-pipeline domain research, generative middle, canonical convergence, progress surface) + the four-domain smoke proof.
- **Readiness program doc** (`pos3/workspace/strategy/revenue/tilth-loam-readiness-program.md`) — dated addendum: W2.1–W2.4 + W1.2–W1.3 delivered; logged actuals vs the program's estimates; the two bars' status updated.
- **Tasks** — #86 closed by this seal; #109's W1/W2 legs marked delivered; follow-ons (§7) created as tasks with durable capture.
- **pos3** — dated retirement note on `loam-demo-fresh/loam_autoroute.py` (superseded by the general path, seal SHA named); the S6 run log path recorded in CURRENT-WORK pointers.
- **Workstream plan demo-evidence row** — the program's open decision #5 (corrected framing) lands when room materials regenerate; noted here so the seal summary reminds the dispatcher.

---

## §10 F2 Ruthless Feedback (honest doubts + named design risks)

1. **Gate quality is judged, not computed — S3's real risk.** *Disagreement with an implicit promise:* "loam authors the acceptance gate" does not guarantee the gate is one a practitioner would respect; a generated gate can be checkable-but-shallow. *Evidence:* the intake's faithfulness machinery guards checkable-but-WRONG, not checkable-but-thin; nothing computes practitioner credibility. *Alternative (baked in):* AC.DGR.2 ties the gate to researched norms with traceability; expert-gate flags name what research couldn't settle; the off-vertical probe catches overfit; and the program's Eric-gates review generated gates against REAL practice at pilot time. Residual risk named, not hidden.
2. **S3 carries the widest estimate (6–12h) and the room-date pressure points the wrong way.** The tempting failure under deadline is narrowing the generative middle to "works on the trio" — which is the rigging failure with extra steps. AC.SMK.2's degrade-rule and D5's owner-authored prompt are the structural guards; the builder should treat trio-only success as a FAIL state, not a milestone.
3. **Live-demo wall-clock honestly estimated: full generation will be SLOWER than the faked demo.** Observed convergence on a pre-built tool: 6–15 min. Adding live research + tool generation puts a full run at **~15–45 min [EST]** — likely outside a comfortable live-meeting window. This plan deliberately does NOT promise an F1 (fully-live) demo; it feeds the program's W4 fallback ladder honest numbers from S6's logged actuals. The corrected story remains strong at F2: "this ran this morning; here's the transcript; type a new ask and watch the first segments live."
4. **The research leg is the demo's most environment-fragile moment.** Live web research in front of strangers fails on hotel wifi, rate limits, or source flakiness. AC.DGR.3 keeps the failure honest (flagged-ungrounded, never faked), but an honest degraded run loses the money-shot. W4 rehearsals must include the research leg specifically; named for the rehearsal checklist.
5. **"Generated, not pre-built" evidence has an epistemic floor.** Git/mtime evidence proves the artifacts were created during the run; it cannot prove the model didn't reproduce a memorized solution shape. The honest narration (W4's claim audit) should say exactly what's proven: unseen wording, fresh workspace, artifacts born in-run, same path off-vertical — and not claim more.
6. **Scope-confidence (F4) per slice, for the dispatch brief:** S1 TIGHT (sealed seams compose; outcome pinned). S2 MEDIUM-TIGHT (outcome pinned; research mechanics deliberately loose). S3 MEDIUM — the genuinely-uncertain core; outcome ACs pin honesty properties hard, generation mechanics stay free; its halt triggers are #1–#3. S4 TIGHT (sealed re-drive + one empirical lesson). S5 TIGHT (primitives named, proven patterns). S6 TIGHT (measurement discipline, no new machinery).
7. **One naming honesty note:** the per-request intent loop (S1) overlaps the existing handsoff-loop SKILL trigger; the delta is the live extract-and-confirm leg + ask-when-ambiguous BEFORE intake's approval gate, per-request. If the builder finds the sealed intake's elicit-the-minimum already satisfies AC.REQ.2 as-is, the right move is the thinner integration, not re-building — surface it in the §14 register, don't gold-plate (ODD: no non-objective code).

---

## §11 Provenance trail (Tier-0 verified on disk/git 2026-06-09 in `/Users/lukeivers/loam` unless noted)

- Owner spec — verbatim, Discord msg 1514064080, 2026-06-09 (carried in the dispatch brief; the contract's voice).
- Readiness program — `pos3/workspace/strategy/revenue/tilth-loam-readiness-program.md` (read fully this session): W1/W2 component tables + estimates, the two bars per workstream, sequencing table, risk register.
- Corrected-target history — `~/.claude/tasks/f4841784-…/86.json` + `109.json` (read fully): the faked-middle reckoning, the corrected target, the owner gate (TG 14167) this ratification answers.
- Honest-demo doctrine — `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_honest_capability_demo_no_overfit.md` incl. the 2026-06-08 recurrence + three sharpened rules (read fully).
- Intent seam — `framework/workspace-bootstrap/src/loam/workspace_bootstrap/intent_extract.py` (read this session): Protocol + ClaudeIntentExtractor + DisabledIntentExtractor default + fail-soft contract; AC.INTENT.1–6 test files present.
- handsoff-loop spine — `plugins/loam-skills/skills/handsoff-loop/SKILL.md` (read fully); `framework/tools/handsoff-loop/src/handsoff_loop/orchestrator.py` in-session dispatcher (`set_swarm_in_session_dispatcher`, ~:32–113, read this session); sidecar `framework/tools/handsoff-loop/tests/SEAL_COMMIT` = `e0b71cbc`.
- Fence precedent + admitted prefixes — `framework/workspace-bootstrap/tests/test_no_sealed_amendments.py` `allowed_prefixes` (~:279–343, read this session); sealed manifests `loop-goal-refinement.manifest.yaml` + `loop-behavioral-refine-cycle.manifest.yaml` (anchor rationale read this session).
- Anti-pattern — `pos3/.scratch/claude-output/loam-demo-fresh/loam_autoroute.py` header (skimmed this session): self-declared single-vertical deterministic router; hardcoded objective; pre-built tool. Zero references in canonical loam (grep, this session).
- App trio — `pos3/workspace/strategy/revenue/newco-master-proposal-2026-06-07.md`: App 1 :232 (back-office grunt work, intake+reconciliation pilot), App 2 :252 (books clean-up/migration of absorbed companies), App 3 :470 (one customer list, match/dedupe).
- Composition seam — `docs/plans/memory-decision-ledger-surfacing-dispatch-packs.md` S4 + manifest (read this session; in-build in this tree; not a dependency).
- Convergence prior art + timeout lesson — program W2.4 row + `improve_loop.py` in pos3 scratch (program-verified; lesson carried as AC.CVG.2's binding constraint).

---

## §14 Method-decision register (populated at build time)

Build executed 2026-06-09/10 by the dispatched builder, six slices in plan order, one commit per slice (+ fix/chore commits, NEW commits only).

| # | Decision | How it landed | Commits |
|---|----------|---------------|---------|
| D1 | Compose on the handsoff-loop spine, single workspace-bootstrap fence | All six slices land under `framework/tools/handsoff-loop/` + `plugins/loam-skills/` — five new pipeline modules (`request_intent`, `grounding`, `generative`, `convergence`, `progress`, `build_from_intent`) COMPOSE the sealed intake/`verify`/orchestrator spine; `verify.py` untouched; the sealed goal-refinement construct untouched; model calls reuse `intake._claude_json` (the sealed isolation surface) | `33c018e9`, `6aa33800`, `080e1107`, `5b692343`, `6c5ce02c` |
| D2 | Extend the sealed re-drive to canonical-default convergence; do NOT import improve_loop wholesale | `convergence.run_to_convergence` wraps the sealed `run_handsoff_loop` with refine-bound > 0 by default; the #111 lesson is structural: `DEFAULT_LEG_CEILING_S` (1200s-class named tunable), `subprocess.TimeoutExpired` handler returns terminal-with-state, `timeout_retries` always 0 and recorded; forced-timeout AC test counts exactly one dispatch attempt | `5b692343` |
| D3 | Grounding docs durable + indexable, packs-compatible, packs-independent | YAML-frontmatter markdown at `<workspace>/grounding/<stamp>-grounding.md`; norm ids (N1..) are the gate-traceability keys; zero coupling to the in-build memory-recall surfaces | `6aa33800` |
| D4 | One amendment, six slices, pipeline order | Executed S1→S6 in order, each slice's deterministic ACs green before the next; live probes per slice (results committed under `smoke/`) | all slice commits |
| D5 | ★ Owner-authored off-vertical prompt, sealed pre-build (owner ruled, Discord 1514112412) | The harness serves it: `run_smoke.py --archetype off-vertical --prompt-file <sealed-prompt>` is the documented one-more-case command; AST-verified no per-archetype branching; the dispatcher executes the sealed prompt post-seal | `77b88f5d` |
| D6 | Per-request routing scoped to build-shaped asks | `handsoff-loop understand` + the SKILL contract cover build-shaped asks per-request; the any-request four-step loop stays deferred (task #34) | `33c018e9` |

**Build-time deviations + findings (Ruthless Feedback, §10 mirror):**

1. **S1 probe run 1 scored 5/6** — the third "clear"-labeled ask omitted where files live + duplicate-id semantics, and the model asked exactly those two build-shaping questions: the LABEL was miscalibrated, not the discrimination. Run 1 preserved fails-included (`smoke/s1_probe_results_run1.json`); run 2 with the genuinely-closed wording passed 6/6 + the reword pair. AC.REQ.2's text was not loosened.
2. **AC.DGR.2 / AC.DGR.OA serialization** — their gate-traceability halves consume the S3 generated gate, so they landed with S3 rather than S2 (plan order preserved at the slice level; noted, not silently re-ordered).
3. **Heartbeat coverage hole found by watching the first live OA run** — research + generation legs run minutes-long with zero artifact writes; heartbeats originally wrapped only the build leg, leaving a >bound silence window in `planning`. Fixed in `60d886a5` (heartbeats wrap all three long legs); the pre-fix OA run's PRG audit failure is preserved in the run trail as the bug's evidence.
4. **AC.GEN.2 sweep vocabulary** — "billing" was dropped from the domain-word sweep: the sealed orchestrator's comments use it for Anthropic PLAN accounting (infrastructure vocabulary, not a business vertical). Recorded in the test body.
5. **AC.REQ.OA fresh-workspace assertion** — the spawned `claude` binary scaffolds hidden session dirs (`.scratch`) in its cwd; the test ignores dotfiles (harness scaffolding, not a pipeline write).
6. **Sealed AC.HL.A1 sweep conflict (caught pre-seal, fixed at the implementation)** — the sealed guarantee forbids any interactive surface in `cli.py`; the new entry point's stdin prompts for the single approval gate + meaningful questions (intake-surface, never loop-driving) moved into the pipeline module (`interactive_approve`/`interactive_answer`, commit `493fa2de`); the sealed test was NOT modified.

---

## Build path + effort estimate (AI-time per the duration rubric; ranges with midpoint)

Sequence: S1 → S2 → S3 → S4 → S5 → S6, one amendment, one tree (queued behind the memory-recall seal). Each slice logs a measured prediction; actuals logged post-build for calibration. All figures are agent-hours **[EST]**, consistent with the program's independent W2 estimate (14–27h for the W2 cluster).

| Slice | What | AI-time [EST] | Measured prediction (pass/fail) |
|---|---|---|---|
| **S1 — per-request intent + questions** | live extract-and-confirm on any build-shaped ask; bounded ask-when-ambiguous; autoroute references zero | 2–4 h (mid 3) | On a 6-ask labeled probe (3 seeded-ambiguous / 3 clear): ≥1 meaningful question on 3/3 ambiguous, zero questions on 3/3 clear; two reworded same-asks confirm equivalent substance, non-identical strings |
| **S2 — domain-grounding research** | bounded in-pipeline web research → durable grounding record → gate traceability + expert-gate flags | 2–4 h (mid 3) | A reconciliation-archetype run yields a grounding record with ≥3 live-resolving citations and ≥1 frozen-gate criterion traceable to it |
| **S3 — generative middle** | objective derived from intent; tool + data shape + gate GENERATED; feeds the existing freeze | 6–12 h (mid 9) | One full fresh-workspace run: tool+gate+objective born in-run (git evidence), gate pass or definite honest negative — no pre-existing deliverable anywhere |
| **S4 — convergence canonical** | bounded re-drive as default; single-ceiling timeout (no retry); own-the-wait | 3–5 h (mid 4) | A seeded failing build converges within the bound; a forced-timeout probe terminates that leg with zero retries |
| **S5 — progress surface** | stage updates + heartbeats via Task / Monitor / SubagentStop / persona narration | 2–4 h (mid 3) | One observed run: max inter-update gap ≤ the named heartbeat bound during active work; 100% of update claims verify against the run record |
| **S6 — honest smoke proof** | Apps 1/3/2 + ≥1 owner-authored off-vertical, fresh workspaces, logged unfiltered, reproducible | 2–4 h (mid 3) | 4 runs logged with run-of-origin on every number; App-1 archetype re-run reproduces from the documented command |
| Apply + seal + bookkeeping | amendment mechanics + §9 | 0.5–1 h | — |
| **Total** | | **17.5–34 h, midpoint ≈ 25 h (≈2–4 days background)** | |

Owner gate-review time is a separate line item (owner availability). The S6 logged actuals are also the program's W4 timing inputs (demo-rung decision).
