# KEEL adoption program — unified objective-contract primitive, grafted onto the proven spine

**Status:** program plan + Phase-1 build plan (sub-plan skeletons for Cycles A–F inline; each cycle expands to its own sub-plan at dispatch time per `plugins/dev-sdlc/docs/conventions/plan-docs.md` §2).
**WD:** `/Users/lukeivers/loam` (canonical).
**Ratified verdict (governs this plan):** `/Users/lukeivers/pos3/workspace/strategy/methodology-synthesis-recommendation-2026-06-10.md` — RATIFIED by owner 2026-06-10 15:06 CDT (Discord 1514360242, "Make it so"), including the corrected AI-time estimates in its RATIFICATION RECORD.
**Predecessors / inputs:** the clean-room KEEL design (`cleanroom-objective-enforcement-design-2026-06-10.md`), the implementation-fidelity audit + adversarial critique (same dir), the three 2026-06-10 ledger records (problem statement / founding intent / root objective, `/Users/lukeivers/pos3/workspace/.loam/memory/decisions/`), the sealed `general-build-from-intent` plan, the queued `ws-handsoff-promise-delivery-contract` (pos3 `workstream-queue.yaml` line 220).
**Plan-authored at:** HEAD `c232ab3e37eebba5557ff74a592ffa2f8a3e4411`, 2026-06-10 15:13 CDT.
**Manifest (Phase 1):** `docs/plans/keel-adoption-program.manifest.yaml` (schema v3, slug-identified).
**Quality bar:** every estimate below is AI-time per the ratification record's calibration anchors (kernel build 35 min vs 6.5 h human-framed estimate; corrective amendments 5–10 min plan-to-seal; v1.4.0 release w/ HARD smoke 75 min). Calendar spread comes only from owner gate-reviews and deliberate watch-points, never from work time.

---

## §1 Summary

The ratified verdict keeps the proven spine untouched (pre-build ratified plan → precise checkable ACs at declared altitude → one production-entry-point `.S` smoke → seal-time executed suites → seal-diff fence → recorded live probes) and grafts KEEL's five missing organs onto it: verbatim Charter capture, the conversation-blind judge, done-bound-to-Charter-hash, propose-never-enact amendment asymmetry, and the proportionality dial — then unifies dev work, build-from-intent, the promise-delivery fix, and owner conversations onto one contract primitive. ODD survives as the authoring grammar inside KEEL's Translate step; no sealed plan, test, or tool is renamed.

**Program shape:** Phase 1 (doc + wiring + genesis, one amendment, ≈1–3 agent-hours) followed by six amendment cycles (≈30–90 min each), total ≈4–8 agent-hours of work. Governing rule (verdict §5): **grafts before cuts; every cut staged separately and reversible; cuts NEVER bundled with grafts;** nothing touching `seal.py` or `verify.py` lands except through a sealed amendment with the fence active.

**Phase table:**

| Phase | Name | Grafts/cuts delivered | AI-time (band, mid) | Fence | Depends on | Parallel-safe with |
|---|---|---|---|---|---|---|
| **P1** | Doctrine rewrite + Charter genesis | Charter #0, AC.PO.1/2 real, spec 1,264→~300, novelty retraction, dormant-gates archive note, VERIFIED rename (doctrine) | 1–3 h (mid 2 h) | docs only: `dev-sdlc` docs subtree + `docs/` universal paths | — (first) | — |
| **A** | Charter capture machinery | Verbatim capture + append-only enforcement (live hook) + dispatch contract-carriage | 45–90 min (mid 60) | `dev-sdlc` (hooks + charter tooling) + `.claude/settings.json` + `docs/charter.md` | P1 | D, F-docs |
| **B** | Gate binding (Charter-hash) | done-bound-to-Charter-hash in seal manifests + `seal.py` comparison + `verify.py` hash field (additive) | 60–90 min (mid 75) | `dev-sdlc` (loam-amend) + `handsoff-loop` (additive field only) | A | F-docs |
| **C** | Conversation-blind judge leg | Stateless judge at seal time for judged-kind criteria | 45–90 min (mid 60) | `dev-sdlc` (loam-amend seal + judge module) | B | D, F-docs |
| **D** | Promise-delivery contract | Letter+spirit verdict layer in BFI's judge (folds `ws-handsoff-promise-delivery-contract`) | 45–90 min (mid 60) | `handsoff-loop` only | P1 | A, B, C, F-docs |
| **E** | Proportionality dial + size-S path | Ledger→charter-append wiring, one-sentence ratification, capture threshold, propose-never-enact conversational surface | 60–90 min (mid 75) | `primary-persona` + charter tooling reuse | A | F-docs |
| **F** | Convergence + scheduling + ladder hygiene | BFI↔KEEL formalization, sealed-AC liveness convention, component-tier honesty, regeneration-test scheduling | 30–60 min (mid 45) | docs + `docs/release-process.md` + `docs/components/` | P1 (docs); AC.REGEN.S rides next minor | A–E (docs-only) |

"Parallel-safe" = logically independent; builds still serialize in one working tree per `feedback_serialize_amendment_builds` (or use worktree isolation).

**F2 scope realism:** the band totals (P1 2 h + cycles ~6.25 h mid... no — cycle mids sum to 375 min ≈ 6.25 h; with P1 that is ~8.25 h at midpoints, slightly above the ratified "4–8 agent-hours" midband). Honest reading: the ratified whole-program number holds at the optimistic ends; the mid-of-bands sits at its ceiling. Surfaced, not hidden — if cycles run at the calibrated 5–10-min-corrective pace where work is doc-shaped (D, F), actuals land inside the ratified band. Log actuals per cycle for calibration.

---

## §2 Verdict-vs-repo contradictions surfaced at plan-authoring (Tier-0 verified)

1. **The "1,264-line odd.md" is NOT `docs/design/odd.md`.** Tier-0: `docs/design/odd.md` is 280 lines and is the contributor short form the critique rated "keep nearly as-is." The 1,264-line operational spec is **`plugins/dev-sdlc/docs/odd-methodology.md`** (`wc -l` = 1,264). Resolution (no halt needed — the critique itself names the right target): the Phase-1 rewrite target is `odd-methodology.md`; `docs/design/odd.md` receives only the honesty touch-ups (ancestry line, KEEL scope-split sentence, novelty-claim consistency).
2. **Manifest schema reality has moved past the convention doc.** Live manifests (e.g. `self-maintaining-work-loop.manifest.yaml`) are `schema_version: 3`, slug-identified, with NO pre-allocated amendment number (per `feedback_version_numbers_at_release_time`); the convention doc (`plan-docs.md` §3) still documents `schema_version: 1` + `amendment.number`. This program's manifests follow live practice (v3). The convention-doc refresh is a one-paragraph bookkeeping item folded into Cycle F.
3. **Phase-1 contents differ from the verdict's §5 sequencing.** The verdict put the full 1,264→~300 consolidation at item 11 (weeks 1–4) and only quick doctrine edits "tomorrow"; the ratified program dispatch folds the full rewrite into Phase 1. The dispatch is the operative owner instruction and the work fits the 1–3 h band; followed as dispatched, recorded here so the deviation from the verdict's own sequencing is named, not silent.
4. **`AC.PO` is still undefined at HEAD** (`grep -c "AC\.PO" docs/VALUE_PROPOSITION.md` → 0) and **only a Stop hook is live** in canonical `.claude/settings.json` — both confirm the audit's D6/D1 findings are still current at `c232ab3e`. Not contradictions; verified-current preconditions.
5. **`ws-handsoff-promise-delivery-contract` lives in pos3's workstream queue, not the loam repo.** Cycle D absorbs it; the queue entry gets marked absorbed (cross-repo bookkeeping item, §10).
6. **The VERIFIED band is also a code-level enum** in the odd-extractor (`plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/bands.py` et al.). The verdict's rename is a doctrine edit; the code rename is a separate concern — ruled in D4 below.

---

## §3 Named decisions (with recommendations — owner may override; all are autonomous-recorded unless marked owner-gated)

| ID | Decision | Recommendation | Why |
|---|---|---|---|
| D1 | Rewrite target | Rewrite `plugins/dev-sdlc/docs/odd-methodology.md` → ~300–350 lines; `docs/design/odd.md` gets touch-ups only | §2.1; critique (d): the short form is already the quality bar |
| D2 | Charter path | **`docs/charter.md`** | Peer of `VALUE_PROPOSITION.md`, whose two tests become Charter #0's first derived criteria (AC.PO.1/2); versioned, human-findable, not hidden in a dot-dir; KEEL's `.keel/` layout is the *generic-project* shape — loam's own repo keeps its docs-rooted convention. Halt if any existing tooling expects a different path. |
| D3 | Phase-1 absorbs the full doc consolidation | Yes, per dispatch | §2.3 |
| D4 | Extractor band-enum code rename (VERIFIED→ASSERTED in `bands.py` etc.) | **Defer** to the next extractor-touching amendment; Phase 1's doctrine carries an explicit mapping note ("the extractor's `VERIFIED` band = ASSERTED evidence grade until renamed") | Cuts/renames never bundled with grafts (verdict §7.1 staging rule); the doctrine rename delivers the honesty fix; the code rename is mechanical follow-through with sealed-fence cost |
| D5 | Disposition of `docs/odd-llm-grounding-derivation.md` (436 lines; carries the novelty claim at :12; carries the altitude tests §6–§8) | Promote §6/§7/§8 (altitude tests, drift-mode catalogue, self-checks) INTO the rewritten spec; archive the derivation doc to `docs/archive/` with a dated retraction note + redirect stub | Critique: "crown jewel buried in a derivation doc"; the §5 derivation chain is a named cut; archiving (not editing in place) keeps the retraction auditable |
| D6 | Cycle count | 6 cycles (verdict's 4–6 upper bound) | Staged-and-reversible: each graft separately attributable beats fewer/fatter cycles; risk-register #1 demands attributability |
| D7 | Charter hash | One canonical hash implementation consumed by BOTH gates (seal.py and verify.py) — outcome: both gates compute identical hashes for identical charter state | Two divergent hash functions = the stale-verdict guarantee silently broken; method (module placement, algorithm) is the builder's call |
| D8 | `docs/design/odd-vs-outcomes.md` overclaim ("equivalent or stronger guarantees") | Fix in Phase 1 alongside the novelty retraction: honest restatement = "different altitude, weaker runtime guarantee, chosen for the no-API-key constraint" | Same honesty-debt class (critique flaw #7); one-line edit; bundling-with-grafts rule not violated (Phase 1 is the honesty-debt phase) |
| D9 | Judge-leg model + invocation | `claude -p` via the existing no-API-key client path; default Sonnet | `feedback_no_anthropic_api_key`; composition over invention (reuse BFI judge machinery, verdict §5.6) |
| D10 | New-hook dormancy prevention | Every hook this program ships carries an AC asserting LIVE registration in canonical `.claude/settings.json` and a production-path firing observation | "Built+sealed+dormant is the worst state" (audit rec #2) — the program that archives the dormant gates must not mint new ones |

---

## §4 Spec-objective placement

- Binds to **Charter entry #0** (the founding intent, verbatim per ledger record `2026-06-10-loam-founding-intent-statement-root-contract.md`) and its first derived criteria **AC.PO.1 / AC.PO.2** (the two VALUE_PROPOSITION tests — defined for real by Phase 1, making the 62 citing plans retroactively well-founded without editing any sealed plan).
- Ladders to the original problem statement (ledger record `…-odd-original-problem-statement-canonical.md`): the user's statements become structural guarantees the build cannot violate by definition; pos3 is just another loam user.
- The program IS the spec-objective for the methodology-evolution workstream; each cycle's AC family ladders to the phase objective → program objective → Charter #0.

---

## §5 PHASE 1 — Doctrine rewrite + Charter genesis (full build plan)

**Objective:** loam's doctrine honestly documents the system that actually produces the works-as-expected record, framed as ODD-the-grammar inside KEEL-the-primitive; loam's root contract exists on disk as Charter entry #0 with real AC.PO.1/AC.PO.2 derived from it.

**Scope (in):**
1. `docs/charter.md` — genesis: entry #0 = the founding intent statement **verbatim** ("Make a harness which can run entirely off of the Claude Max subscription whose purpose is to make a tool for people to more effectively be hands-off while an AI does the development for them."), timestamped, source-tagged (Discord 1514355792709685389, 2026-06-10 14:49 CDT), hashed; the bootstrap exception documented as the genesis record (KEEL b.8.1 — hand-written and owner-ratified before the binding exists, named, not silently exempted).
2. `docs/VALUE_PROPOSITION.md` — the two tests labeled `AC.PO.1` / `AC.PO.2` verbatim, recorded as the first derived criteria tracing to Charter #0.
3. `plugins/dev-sdlc/docs/odd-methodology.md` rewritten to ~300–350 honest lines: the spine documented as the system (audit rec #1); §2.5 forward/reverse coverage leading; altitude tests + drift-mode catalogue promoted in (from derivation doc §6–§8); banding restated as evidence grades (V/P/H) under check-kinds (mechanical/judged/attested), criteria binary; VERIFIED = "ran green at a known SHA", assumed-green = ASSERTED (+ extractor mapping note per D4); halt-and-surface; per-criterion altitude declaration canonized (mechanism-pinning legitimate when the mechanism is the deliverable, declared + traced to an outcome-altitude parent); change-management unbundled ("ODD is how criteria are written; KEEL is how they are enforced; the amendment cycle is loam's change-management, not the methodology"); honest ancestry (KAOS, Ulwick ODI, Adzic SbE, Meyer DbC); KEEL primitive frame (Capture→Translate→Ratify→Bind→Build→Verify→Deliver, Amend user-only) with the unification table; recent-era plan shape promoted to the documented standard (lean plan, per-AC outcome-shape annotation, chain uplinks, one `.S` smoke; mandatory per-plan 8-lens sections dropped — lenses stay at feature-proposal altitude).
4. Novelty-claim retraction: derivation doc archived per D5 with dated note; no live doc claims ODD is "genuinely new"; §12/§13 adapter tables → extractor package docs; §14 → CHANGELOG-class file.
5. Dormant-gates archive note (dated): `objective_binding_gate.py` + `tdd_guard.py` archived-by-decision with the verdict's three reasons (completion-time vs write-time; record produced with them off; built+sealed+dormant is the worst state); the salvaged component named: **dispatch contract-carriage via extension of the existing `dispatch_setup_hook.py`** (built in Cycle A).
6. `docs/design/odd.md` + `docs/design/odd-vs-outcomes.md` touch-ups (D1, D8).

**Scope (out):** any framework/plugin *code* change; hook registration; extractor enum rename (D4); the grafts (Cycles A–F).

**AC ladder (all outcome-shape; altitude declared per criterion):**

| AC | Outcome | Altitude |
|---|---|---|
| AC.CH0.1 | `docs/charter.md` exists; entry #0 carries the founding intent byte-faithful to the ledger record's verbatim statement, with timestamp + source tag + content hash; the genesis/bootstrap exception is documented in-file | doc-outcome |
| AC.CH0.2 | `grep -c "AC\.PO\.[12]" docs/VALUE_PROPOSITION.md` ≥ 2; each label sits on its corresponding test verbatim and names Charter #0 as its source | doc-outcome (closes audit D6) |
| AC.KDOC.1 | Rewritten `odd-methodology.md` ≤ 360 lines and carries every §5-scope-item-3 element (checkable per-element list in the build's sub-§) | doc-outcome |
| AC.KDOC.2 | No file in the live docs tree (docs/ + plugins/*/docs/, excluding `docs/archive/` + `docs/plans/sealed/`) asserts ODD novelty/"not in training data"/unprecedented; the archived derivation doc carries the dated retraction note; ancestry named in the rewritten spec | doc-outcome |
| AC.KDOC.3 | Doctrine defines VERIFIED = ran green at a known SHA; ASSERTED = assumed-green; extractor mapping note present | doc-outcome |
| AC.KDOC.4 | Dated dormant-gates archive note exists naming both gates + the three reasons + the salvaged dispatch contract-carriage component; no live doc implies write-time structural enforcement is active (closes audit D1's doctrine half) | doc-outcome |
| AC.KDOC.5 | Adapter-table content lives under the extractor's package docs, not the methodology spec; §14 content lives in a changelog-class file | doc-outcome |
| AC.KDOC.S | **Outcome-altitude cold walk:** against the live repo with no pre-arranged state, a scripted honesty sweep (grep-class, production paths) finds zero live-doc claims of: ODD novelty, active write-time gating, VERIFIED-without-run, Outcomes-equivalence — and finds Charter #0 + AC.PO.1/2 resolvable from `docs/charter.md` and `docs/VALUE_PROPOSITION.md` alone | outcome-altitude |

**Build steps (method-level guidance only; method is the builder's call):** manifest `docs/plans/keel-adoption-program.manifest.yaml` → charter genesis + VALUE_PROPOSITION labels → spec rewrite → archive moves + retraction notes → touch-ups → tests (doc-sweep assertions under `plugins/dev-sdlc/tests/`) → `loam amend apply` → `loam amend seal` → smoke.

**Fence:** `dev-sdlc` component (docs subtree + tests only — a diff touching `plugins/dev-sdlc/hooks/` or `tools/` source is a fence breach) + universal `docs/` paths. Owner ratification of this plan recorded per `feedback_record_owner_ratification_before_dispatch` before the build dispatches.

**Halt triggers:** (1) the verbatim founding-intent wording in the ledger record conflicts with any other ratified record → halt, owner rules wording; (2) the ~300-line target forces dropping an element the audit found load-bearing → halt (never sacrifice spine documentation to a line count); (3) any rewrite step would alter the MEANING of a sealed plan's cited rule (vs reframing the doctrine) → halt; (4) tooling found depending on `odd-llm-grounding-derivation.md`'s live path → halt.

**Estimate:** 1–3 h AI-time, mid 2 h. **Measurable prediction:** wall-clock 60–180 min; formula-implied ~480–1,440 tool calls at 0.1–0.15 min/call; single agent, no parallelism on the critical path. Log actuals.

---

## §6 CYCLES A–F — sub-plan skeletons

Each skeleton below expands to a full sub-plan (`docs/plans/keel-adoption-<cycle-slug>.md` + manifest) at dispatch time. Versions are NOT pre-assigned (release-time derivation).

### Cycle A — Charter capture machinery + append-only enforcement + dispatch contract-carriage

- **Objective:** ratified owner rulings append to `docs/charter.md` as hash-chained entries through a production append path; non-append mutation through the hooked tool path is refused; sub-agent dispatches carrying a contract block must carry (charter path, criteria path, content hash) or do not launch.
- **Scope:** charter append tooling; append-only PreToolUse enforcement (LIVE-registered, per D10); `dispatch_setup_hook.py` extension (the salvaged component — composes with its existing `<AC-MANIFEST>` contract); supersession marking (append-only supersession, never deletion — risk-register #9).
- **Named decisions:** hook registration surface (canonical settings vs plugin hook config) — builder proposes, recorded in §14; tamper-EVIDENCE wording in all user-facing text (never tamper-proof — risk #7).
- **AC ladder:** AC.CHCAP.1 append → verifiable hash chain from file alone; AC.CHCAP.2 non-append edit via hooked path refused, refusal names the Amendment path, hook LIVE in canonical settings; AC.CHCAP.3 out-of-band mutation detected by chain verification (tamper-evident); AC.CHCAP.4 contract-carrying dispatch without the triple refused / with it launches; AC.CHCAP.S (outcome-altitude) cold walk on the live repo exercising all three behaviors through production entry points, no pre-arranged state.
- **Fence:** `dev-sdlc` + `.claude/settings.json` + `docs/charter.md`.
- **Halt triggers:** hook cannot be made fail-open-safe (internal error must never lock the owner out of his own charter file edit-by-ratification path); any design forcing charter writes through an LLM-judgment step (capture is mechanical, judgment stays at the threshold per risk #4).
- **Estimate:** 45–90 min (mid 60). Prediction: 360–720 tool calls.

### Cycle B — Gate binding: done-bound-to-Charter-hash

- **Objective:** stale-agreement delivery becomes structurally impossible: seal manifests and BFI verdicts carry the hash of the Charter state they satisfied; an Amendment changes the hash; stale verdicts don't count.
- **Scope:** charter-hash field in seal manifests + comparison in `seal.py` (ADDITIVE: a field + a comparison, not a rewrite — risk #2); the same hash recorded in `verify.py` verdicts (additive field only); one canonical hash implementation for both gates (D7).
- **AC ladder:** AC.GBIND.1 a seal records the charter hash it verified against; AC.GBIND.2 seal attempted against a since-amended charter refuses with a named error; AC.GBIND.3 BFI verdicts carry the hash; a stale verdict does not satisfy the gate; AC.GBIND.4 (regression floor) full existing seal suite + fence behavior byte-identical for charter-unaware historical manifests (back-compat: absence of the field = pre-KEEL manifest, allowed, logged); AC.GBIND.S (outcome-altitude) a real `loam amend seal` run binds + refuses correctly with no pre-arranged state.
- **Fence:** `dev-sdlc` (loam-amend) + `handsoff-loop` (verdict-record field only).
- **Halt triggers:** ANY change to `verify.py`'s spine contracts (frozen-unseen / independent-judge / honest-negative — sealed; redesign is a named halt per verdict §5 never-changes list); seal-diff fence behavior change; back-compat break on historical manifests.
- **Estimate:** 60–90 min (mid 75) — Tier-0-organ surgery, top of band. Prediction: 480–900 tool calls.

### Cycle C — Conversation-blind judge leg at seal time

- **Objective:** judged-kind criteria in a dev amendment are verified at seal by a fresh, conversation-free judge that receives only (Charter, criteria, deliverable) and returns per-criterion verdicts with quoted evidence; verdict without evidence = FAIL.
- **Scope:** judged-kind criterion declaration in plan/manifest; seal-time judge leg (reuse BFI judge machinery — composition, not invention; D9: `claude -p`, no API key); mechanical criteria stay pytest-only.
- **AC ladder:** AC.JUDGE.1 seal of an amendment declaring judged-kind criteria produces per-criterion verdicts with quoted evidence from a context that contained no conversation; AC.JUDGE.2 evidence-free verdict → FAIL → seal refuses; AC.JUDGE.3 no judged-kind criteria → leg does not fire (cost containment, risk #5); AC.JUDGE.4 mechanical criteria are never routed to the judge; AC.JUDGE.S (outcome-altitude) a live seal with one judged criterion end-to-end, no pre-arranged state.
- **Fence:** `dev-sdlc` (loam-amend + judge module).
- **Halt triggers:** judge leg requires an API key path (forbidden); seal wall-clock blowup beyond a stated budget → surface with measurements; any temptation to route mechanical checks through the judge (the stateless property of pytest is already the guarantee).
- **Estimate:** 45–90 min (mid 60). Prediction: 360–720 tool calls.

### Cycle D — Promise-delivery contract (letter + spirit in BFI's judge)

- **Objective:** whatever the approval-gate text promises the user becomes a checked criterion; the independent judge scores the deliverable against the criteria (letter) AND the verbatim promise (spirit); a promised-surface divergence (web page promised, CLI delivered — the soccer act-2 finding, Discord 1514324401) is an honest FAIL naming the broken promise. Folds `ws-handsoff-promise-delivery-contract`.
- **Scope:** promise extraction from gate text into checked criteria (or promise text derived FROM the build plan, never free-written — the queue entry's two admissible shapes; builder proposes which, records in §14); letter+spirit dual verdict in the existing judge; divergence between letter-pass and spirit-fail flagged as a translation bug (re-translate, not deliver — verdict §2.2 Tier-2 row).
- **AC ladder:** AC.PDC.1 every promise in approved gate text is a checked criterion at verify time; AC.PDC.2 a deliverable diverging from a promised surface FAILs with the divergence named in the user's words; AC.PDC.3 (regression floor) frozen-unseen, honest-negative, no-retry-to-green, independent-judge contracts unchanged — existing BFI suite green; AC.PDC.S (outcome-altitude) a real handsoff run against a fixture ask with an intentionally divergent build → honest negative naming the broken promise, production entry point, no pre-arranged state.
- **Fence:** `handsoff-loop` only.
- **Halt triggers:** any change shape that refactors `verify.py`'s spine rather than composing on it (risk #3 — "verify.py is already KEEL" must not license a redesign); promise extraction requiring the judge to see the conversation (breaks conversation-blindness).
- **Estimate:** 45–90 min (mid 60). Prediction: 360–720 tool calls. **Bookkeeping:** mark `ws-handsoff-promise-delivery-contract` absorbed in the pos3 workstream queue at seal; note the pairing with `ws-handsoff-degraded-step-policy` (NOT absorbed — out of this program's scope).

### Cycle E — Proportionality dial + size-S path (pos3 as just another user)

- **Objective:** an owner-conversation ask crossing the capture threshold becomes a staged charter entry (decisions ledger = capture staging), ratified by ONE plain-language confirmation sentence, appended via Cycle A's path; the never-waived floor holds at size S (verbatim capture + ≥1 criterion + 1 independent verification + append-only history); AI-originated objective changes exist only as inert proposal artifacts until ratified.
- **Scope:** ledger→charter-append wiring; one-sentence ratification surface; capture threshold (a recorded judgment call — KEEL residue #6; batchable confirmations; "don't make a big production of this" honored per risk #4); amendment-proposal staging surface (propose-never-enact's conversational half — its structural half shipped in Cycle A).
- **AC ladder:** AC.DIAL.1 threshold-crossing ask → staged candidate + one-sentence ratification → ratified entry appears in the charter hash chain; AC.DIAL.2 size-S floor enforced before "here you go" (all four floor elements observable); AC.DIAL.3 below-threshold utterances produce zero ceremony; AC.DIAL.4 an AI-originated objective-change proposal cannot reach the charter without ratification (no tool path); AC.DIAL.S (outcome-altitude) a cold conversational run end-to-end through production persona surfaces, no pre-arranged state.
- **Fence:** `primary-persona` (+ intake surface) + charter tooling consumption (no `dev-sdlc` source change).
- **Halt triggers:** ceremony rebound — if the dial's smallest setting still degrades conversational flow in the cold run, halt and surface (the worst outcome is an enforcement system the owner routes around, risk #4); any design storing the floor's "independent verification" as a self-report.
- **Estimate:** 60–90 min (mid 75). Prediction: 480–900 tool calls.

### Cycle F — BFI↔KEEL convergence formalization + regeneration scheduling + ladder hygiene

- **Objective:** the unification is a documented, falsifiable artifact: the BFI↔KEEL correspondence formalized as the primitive's canonical statement; the sealed-AC liveness convention installed; the component tier honest; the regeneration test scheduled as the top-level drift check.
- **Scope:** convergence design doc (the verdict §3 table + machinery→concept map as canon; the scope-split sentence in both docs — risk #6); sealed-AC liveness sweep convention (deletion/reframe amendments enumerate retired/superseded sealed ACs — audit rec #6, closes D5); component-tier honesty (name `docs/components/*.md` as the component-objective tier, author the ~6 missing docs, retire the `objectives.yaml` obligation in the conformance allowlist with a dated note — closes D2); regeneration-test scheduling (per minor, piggybacking HARD-smoke-per-minor in `docs/release-process.md`: feed Charter #0 to BFI, judge the sketch vs actual loam at architecture altitude with a rubric; verdict is surface-to-owner ONLY, never auto-action — risk #10); plan-docs convention-doc refresh to schema v3 reality (§2.2).
- **AC ladder:** AC.CONV.1 canonical convergence doc exists; both methodology docs carry the one-sentence scope split; AC.CONV.2 liveness-sweep convention installed and checkable on the next deletion-class amendment; AC.CONV.3 component tier honest: missing component docs authored; allowlist amended with dated note; zero live obligation to phantom `objectives.yaml`; AC.REGEN.1 release process names the regeneration step with its rubric + surface-to-owner-only contract; AC.REGEN.S (outcome-altitude) the FIRST regeneration run executes against live loam at the next minor's HARD smoke and its judged sketch-vs-actual verdict reaches the owner (rides the release; sealed with this cycle as a scheduled obligation, executed at the minor).
- **Fence:** docs + `docs/release-process.md` + `docs/components/` + conventions (docs-only; `dev-sdlc` docs subtree).
- **Halt triggers:** regeneration-test design drifting toward auto-action on divergence; convergence doc tempted to respecify BFI internals (compose, never refactor).
- **Estimate:** 30–60 min (mid 45) + the regeneration run itself rides the next minor's release window. Prediction: 240–480 tool calls.

---

## §7 Out of scope (program-wide)

1. Anything on the verdict's never-changes list: plan-before-code; owner ratification before dispatch; seal-time executed suites; the seal-diff fence; one production-entry-point smoke; halt-and-surface; §2.5 reverse coverage; the amendment cycle's steps; BFI's frozen-unseen / independent-judge / honest-negative contracts; the no-API-key posture.
2. Mass renaming of sealed plans, AC-named tests, or tooling (verdict §6 — scope split, not rebrand).
3. The extractor band-enum code rename (D4 — deferred, mapped).
4. `ws-handsoff-degraded-step-policy` (paired queue entry; separate amendment).
5. Wiring the archived write-time gates (ruled anti-KEEL; archive is the decision, not a deferral).
6. Editing `docs/spec/` (outside any cycle's fence).
7. Re-running the regeneration test more often than per-minor (cost discipline).

## §8 Program-wide halt triggers

1. Any cycle's diff would touch `seal.py`/`verify.py` outside its declared additive surface → halt.
2. A cut found bundled into a graft cycle's diff → halt (staging rule is load-bearing for risk-#1 attributability).
3. Charter content conflicting with a previously ratified ledger record → halt, owner rules.
4. Any new hook landing unregistered (D10) → halt before seal.
5. Post-cycle regression in the works-as-expected record (an owner-flagged surprise on sealed work) → pause the program, attribute against the staged cuts/grafts before the next cycle dispatches.

## §9 Bookkeeping

- `docs/STATE.md` change-log entry per phase seal; sealed narratives at `docs/plans/sealed/<slug>.md` per convention.
- pos3 workstream queue: mark `ws-handsoff-promise-delivery-contract` absorbed at Cycle D seal.
- Duration actuals logged per phase against the §1 predictions (calibration discipline).
- Owner gate-review points: after P1 (the doctrine is the contract everything else builds on), after B (Tier-0 organ touched), and at program close. Owner time is a separate line item from AI-time.

## §10 F2 Ruthless Feedback — honest doubts

1. **The estimate-band ceiling (§1):** mid-of-band program total (~8.25 h) sits at the top of the ratified 4–8 h. Evidence: the per-cycle bands above vs the ratification record. Alternative if it matters: merge F into E's dispatch (saves coordination overhead, costs attributability). Recommendation: keep 6 cycles, accept the ceiling; the staging rule outranks the estimate aesthetics.
2. **AC.KDOC.S is a grep-class smoke.** A doc-honesty sweep is the strongest *mechanical* outcome check available for a docs-only amendment, but it cannot judge whether the rewritten spec is GOOD — that is judged-kind. Honest shape: P1's quality is owner-gate-reviewed (§9); Cycle C ironically ships the machinery that would have judged it. Named, not hidden.
3. **Cycle E is the highest-uncertainty cycle.** The capture threshold is a judgment call by design (KEEL residue #6) and risk #4 (ceremony rebound) is the program's most likely real-world failure. The AC.DIAL.S cold run is the canary; the halt trigger is armed. If E's cold run feels bad, the right move is dial tuning, not graft removal.
4. **The §1 phase table claims "parallel-safe" knowing builds serialize in-tree.** The honest value of the column is dispatch-ordering freedom (D can run before or between A–C), not wall-clock parallelism, unless worktree isolation is used.
5. **AC.REGEN.S's seal-vs-execution gap:** Cycle F seals the *scheduled obligation*; the run itself happens at the next minor. A sealed AC whose verification rides a future release is exactly the D5 staleness class the liveness sweep exists for — the obligation is therefore written into `release-process.md` (a release can't complete without it), not left as a plan-doc promise.

## §11 Provenance trail

- Ratified verdict + RATIFICATION RECORD: `/Users/lukeivers/pos3/workspace/strategy/methodology-synthesis-recommendation-2026-06-10.md` (§2 element verdicts; §3 unification table; §4 root contract; §5 migration path + never-changes list; §6 naming; §7 risk register; ratification 2026-06-10 15:06 CDT, Discord 1514360242).
- Clean-room design: `cleanroom-objective-enforcement-design-2026-06-10.md` (b.2 artifacts; b.3 lifecycle; b.4 tiers; b.5 anti-Goodhart; b.7 dial; b.8 dogfooding; §e residue).
- Audit: `odd-implementation-fidelity-audit-2026-06-10.md` (D1–D8 register; §d de-facto system; recs 1–7). Critique: `odd-methodology-critique-2026-06-10.md` (flaws 1–12; §g five changes).
- Ledger records (verbatim sources for Charter #0 + problem statement + root objective): `/Users/lukeivers/pos3/workspace/.loam/memory/decisions/2026-06-10-{odd-original-problem-statement-canonical, loam-founding-intent-statement-root-contract, loam-root-objective-restated-substrate-knowledge}.md`.
- Repo reality (Tier-0, this authoring, HEAD `c232ab3e`): `wc -l plugins/dev-sdlc/docs/odd-methodology.md` = 1,264; `wc -l docs/design/odd.md` = 280; `grep -c "AC\.PO" docs/VALUE_PROPOSITION.md` = 0; live hooks in canonical `.claude/settings.json` = Stop only; `dispatch_setup_hook.py` `<AC-MANIFEST>` contract present; dormant gates present at `plugins/dev-sdlc/hooks/`; seal sidecars: `plugins/dev-sdlc/tests/SEAL_COMMIT` (extractor inside the dev-sdlc fence); manifest schema v3 slug-identified (`self-maintaining-work-loop.manifest.yaml`); BFI gate at `framework/tools/handsoff-loop/src/handsoff_loop/verify.py`; queue entry at pos3 `workstream-queue.yaml:220`.

## §14 Method-decision register

Populated per-cycle at build time; SHAs backfilled by `loam amend seal --plan-doc`.

### Phase 1 (built 2026-06-10)

| ID | Decision (method-level, builder's call) | Why |
|---|---|---|
| P1-M1 | Rewritten spec preserves the pre-KEEL section numbers for the heavily-cited rules (§1.1, §2.4, §2.5, §3.3, §3.4, §4.x, §5.1.1, §5.3, §7.4, §8.2, §10) and carries an old→new section map at §11; full pre-rewrite text archived at `docs/archive/odd-methodology-2026-06-10-pre-keel.md` | Halt trigger 3 (sealed plans cite "ODD §N" 900+ times for §2.5 alone — Tier-0 grep count; renumbering would alter cited meanings) |
| P1-M2 | Landed at exactly 360 lines (the AC ceiling) — element-complete; the deeper ~300 target was not reachable without cutting spine documentation, which halt trigger 2 forbids | "~300-line target is an outcome of honest cutting, not a quota" (dispatch principle 5) |
| P1-M3 | AC.KDOC.4/.S write-time-gating sweep scoped to DOCTRINE surfaces (docs root + docs/design + plugins/*/docs), not docs/plans/ | The AC's own "doctrine half" clause; historical plan/research records legitimately document the gates' build and are work records, not doctrine |
| P1-M4 | Charter hash discipline: `content-sha256` = SHA-256 of the verbatim statement's UTF-8 bytes; chain rule `chain(N) = SHA-256(chain(N-1) + "\n" + statement(N))`; entry #0 chain = its content hash (genesis) | Verifiable from the file alone (Cycle A's AC.CHCAP.1 builds on this); simplest scheme that is byte-checkable |
| P1-M5 | Adapter tables → `plugins/dev-sdlc/odd-extractor/docs/adapter-conventions.md` (new package-docs dir, old §11.2–§13 verbatim + ASSERTED mapping header); old §14 → `plugins/dev-sdlc/docs/odd-methodology-CHANGELOG.md` (new changelog-class file — repo had none) | AC.KDOC.5; both paths inside the dev-sdlc fence |
| P1-M6 | Derivation doc archived via `git mv` + dated retraction note prepended + redirect stub at the old path | D5; the stub keeps the five on-demand pointer references (CLAUDE.dev.md, corpus hook comment, dev-mode-manifest comment, SKILL.md, leverage-discipline.md) resolvable with zero out-of-fence edits — no tooling loads the path programmatically (Tier-0 verified), so halt trigger 4 did not fire |
| P1-M7 | In-scope honesty ride-alongs: `docs/odd-llm-grounding.lean.md` ("What's specifically new…Novel." → distinctive-vs-ancestors + V/P/H-as-evidence-grades restatement; derivation pointers → archive path) and `docs/glossary.md` (banded-AC entry gains the D4 ASSERTED mapping note; authority pointer §11 → §6) | AC.KDOC.2/.3's sweep surfaces include these live docs; leaving them would fail the very sweeps Phase 1 installs |

### Commit SHAs

- Amendment commit: `bd95f081607ca1e38ce7aaba4cfe2f78fe09e311` —
  `chore(amend): KEEL adoption Phase 1 — docs-only amendment. Honesty debts paid (novelty retraction, VERIFIED rename in doctrine, dormant-gates archive note, Outcomes-equivalence overclaim fixed) + the root contract installed (Charter #0 verbatim, AC.PO.1/2 derived from it, the 62 citing plans retroactively well-founded without editing a sealed plan). Grafts (Cycles A–F) follow separately per the staged-and-reversible rule: cuts never bundled with grafts. ACs: AC.CH0.1-2, AC.KDOC.1-5, AC.KDOC.S (outcome-altitude doc-honesty cold sweep).  manifest+apply — dev-sdlc BASELINE+sidecar bump to c232ab3`
- Seal commit: `31ac1d7071406228578bf19a213cff019b2435c3` —
  `chore(seals): KEEL adoption Phase 1 — docs-only amendment. Honesty debts paid (novelty retraction, VERIFIED rename in doctrine, dormant-gates archive note, Outcomes-equivalence overclaim fixed) + the root contract installed (Charter #0 verbatim, AC.PO.1/2 derived from it, the 62 citing plans retroactively well-founded without editing a sealed plan). Grafts (Cycles A–F) follow separately per the staged-and-reversible rule: cuts never bundled with grafts. ACs: AC.CH0.1-2, AC.KDOC.1-5, AC.KDOC.S (outcome-altitude doc-honesty cold sweep).  — dev-sdlc at bd95f08`
## §16 Halt-and-surface findings at plan-authoring

The six §2 items. None required a hard halt: items 1–3 are resolvable from the inputs themselves and are recorded as named decisions (D1, D3) or bookkeeping; items 4–6 are verified-current preconditions. Ratification of THIS plan (the program plan) is the one owner gate before Phase 1 dispatches.

# KEEL adoption program — Phase 1: doctrine rewrite + Charter genesis

Per `docs/plans/keel-adoption-program.md` and the ratified methodology-synthesis
verdict (`methodology-synthesis-recommendation-2026-06-10.md`, owner-ratified
2026-06-10 15:06 CDT, Discord 1514360242). The proven spine (ratified plan →
precise ACs at declared altitude → one `.S` smoke → seal-time executed suites →
seal-diff fence → recorded live probes) is untouched — this phase documents it
AS the system and installs the root contract everything ladders to.

What it ships:
  - **`docs/charter.md` genesis** — the founding intent statement verbatim as
    entry #0 ("Make a harness which can run entirely off of the Claude Max
    subscription whose purpose is to make a tool for people to more effectively
    be hands-off while an AI does the development for them."), timestamped,
    source-tagged (Discord 1514355792709685389), hash-chained; the bootstrap
    exception documented as the genesis record, not silently exempted.
  - **AC.PO.1 / AC.PO.2 defined for real** in `docs/VALUE_PROPOSITION.md` as
    the first criteria derived from Charter #0 — closing the audit's
    phantom-anchor finding (D6) at the root.
  - **`plugins/dev-sdlc/docs/odd-methodology.md` rewritten 1,264 → ~300 honest
    lines**: spine-as-system; §2.5 reverse coverage + the altitude tests /
    drift-mode catalogue promoted in; banding restated as evidence grades under
    mechanical/judged/attested check-kinds with criteria binary; VERIFIED =
    ran green at a known SHA (assumed-green = ASSERTED, extractor mapping note
    pending the deferred code rename); per-criterion altitude declaration
    canonized; change-management unbundled ("ODD is how criteria are written;
    KEEL is how they are enforced"); honest ancestry (KAOS, Ulwick, Adzic,
    Meyer); the KEEL lifecycle frame.
  - **Honesty debts paid:** novelty claim retracted (derivation doc archived
    with a dated note; altitude tests salvaged into the spec); adapter tables →
    extractor package docs; §14 → changelog; `odd-vs-outcomes.md` equivalence
    overclaim restated honestly; dormant write-time gates
    (objective_binding_gate.py, tdd_guard.py) archived with a dated note naming
    dispatch contract-carriage (the dispatch_setup_hook.py extension, built in
    Cycle A) as the salvaged component.

Fence: docs-only — dev-sdlc docs subtree + tests; any diff touching
plugins/dev-sdlc/hooks/ or tools/ source is a fence breach. Cuts staged
separately from grafts per the verdict's risk register; Cycles A–F (charter
capture, gate binding, conversation-blind judge, promise-delivery contract,
proportionality dial, convergence + regeneration scheduling) follow as their
own amendments.

No ODD violation in surrounding work; every edit traces to a named AC
(AC.CH0.1-2, AC.KDOC.1-5, AC.KDOC.S); no changes for unnamed cases.
