# FBM CORRECTNESS CYCLE — claim-vs-stored-state guard + git-derived plan-state index + supersession correctness

**Status:** sub-plan-doc, **OWNER-RATIFIED 2026-06-09 — build authorized.** D2 ruled **(a) STEER + fail-open** by Luke (Discord msg 1514040998341120081, 2026-06-09 17:58 CDT — answer "a" to the steer-vs-block question delivered at Discord msg 1514039381806022726). All other decisions ratified-as-recommended per the same exchange (summary-level review; recommendation-as-decision per standing practice). · **Date:** 2026-06-09
**WD:** `/Users/lukeivers/loam` (canonical loam — the WD-discipline guard blocks framework-source edits from derived workspaces)
**Parent / motivating artefacts:** `docs/design/fbm-state-and-memory-roadmap-2026-05-29.md` (the FBM roadmap) + `pos3/workspace/.scratch/claude-output/why-memory-was-wrong-rootcause-2026-06-09.md` (the live 2026-06-09 failure + layered fix — the freshest owner-validated framing; see D1 for how it supersedes the roadmap's Cycle-2 text).

---

## OWNER SUMMARY (rule from this — full detail below)

1. **What this fixes:** today (June 9) I confidently told you the subagent migration "wasn't planned" when it was planned, greenlit, and 2/3 built. The behavioral rule that should catch this has now failed 3+ times — this cycle builds the *structural* fix.
2. **Three pieces, one build:** (a) a **plan-state index** — what plans exist and how built they really are, derived live from git, surfaced at session start so I never again have to "remember" what's in flight; (b) a **claim guard** — when I'm about to tell you something is or isn't built/planned, the system checks the real records first and corrects me before the words reach you; (c) **stale-rule retirement** — when an old note's premise has flipped, it gets marked superseded so it stops steering me wrong.
3. **What I deliberately left out:** the roadmap's "consolidation" layer (summarizing old memories) — useful, but not what caused any of the failures. Deferred, not dropped.
4. **One call I need from you (D2):** when the guard catches me about to state something wrong, it *corrects me silently before I speak* (recommended) rather than blocking the message outright. Recommend the correction approach — blocking risks the system wedging on a false alarm.
5. **Cost:** roughly 1–2.5 hours of agent build time across three sequenced slices, plus your review of this plan now and the result after.

---

## Header detail

**Predecessors (load-bearing prior seals, Tier-0 verified on disk + git 2026-06-09):**
- **FBM Slice C — the ground-truth project-STATE engine** — `framework/tools/loam/src/loam_cli/audit/registry.py`: `derive_project_state` (fresh-from-git-refs, `None` for unregistered), `PROJECT_REGISTRY` (registers `loam`, `cairn`, **and `litrpg`** as of today's read — it has grown past the loam+cairn reach the 2026-06-05 plan documented). **The precedent + composition seam for the plan-state index: per-project ground truth derived fresh, never stored prose.**
- **FBM Slice D — lens injection** — `framework/primary-persona/src/loam/primary_persona/keep_pace/project_state.py`: TTL-cached (`_STATE_TTL_SECONDS=60`), char-capped (`_STATE_BLOCK_CHAR_CAP=600`), fail-soft per-project STATE block in the turn-start lens. **The surfacing discipline the plans block inherits.**
- **KP9 draft-gate** — `framework/hands-off-lifecycle/hooks/keep_pace/draft_gate.py`: the gate every user-facing surface routes through; Layer C (`SEEDED_CONSTRAINTS`, a hardcoded tuple at `:431`) checks drafts against seeded canon rules — **the exact seam the roadmap's MM1 names for the claim guard; today it checks a static set, not live stored state.** Fail-open contract (`:621` — never block on internal error). Model-facing-only feedback (AC.KP9.4).
- **KP1 retrieval (LIVE + unified)** — `framework/primary-persona/src/loam/primary_persona/keep_pace/corpus_index.py` + `retrieval.py`: BM25/FTS5 over the markdown rules corpus, **merged with FBM episode hits** (`retrieval.py:160, :239-241` imports `FileMemoryStore` and merges episode results — the roadmap's R1 "unify" is DONE). **Tier-0 verified live:** `~/.claude/settings.json` wires `keep_pace/user_prompt_submit.py` (UserPromptSubmit) + `keep_pace/pre_tool_use.py` (PreToolUse) — the roadmap's Cycle-1 activation is DONE. **Gap this cycle closes: `grep supersed` over `keep_pace/` returns NOTHING — corpus-side retrieval has zero supersession handling.**
- **FBM T1.1 supersession convention** — `framework/primary-persona/src/loam/primary_persona/file_memory.py`: the `superseded-by: <relative-path>` frontmatter convention (`:1216-1221`), `_superseded_marker` (`:1382`), `SUPERSEDED_PENALTY` demotion (`:436-442`, AC.FBMT1.SUPM.\*). **The marker convention exists and is honored on the episode-store side ONLY; Slice 3 extends the honor to the corpus side + adds the marking mechanism.**
- **Self-maintaining work loop (sealed `74fdb418`/`029f82ba`)** — the WMS census + ground-truth capture. **Covers work-ITEM state; it does NOT cover plan-doc build-state (no `docs/plans` reference anywhere in `registry.py` — grep verified) — that absence is Slice 1's gap.**
- **Behavioral rules this cycle structurally replaces** — `feedback_published_state_only_from_git_refs.md` (3 misses in one thread → hard rule → 2 further extensions, 2026-05-29 + 2026-06-09; the doc itself names "the structural fix is the FBM Cycle-2 claim-vs-stored-state guard + a git-derived plan/decision index") and `feedback_notes_and_users_are_pointers_evidence_resolves.md` (the reconciliation protocol + the no-eternal-negatives poison rule MM-pieces 1–3 — this cycle mechanizes its pieces 2-as-guard and the supersession half of staleness; piece 1 claim-metadata + piece 3 lint are §7 deferrals).

**BASELINE candidate:** `main` tip at build time (today: `22df8683`, v1.3.0 post-publish backfill). Walked at apply-time per the #142 baseline-walk pattern (`baseline: null` in the draft manifest).
**Components:** three, all sealed, all additive — `loam-cli` (Slice 1 derivation) + `primary-persona` (Slice 1 surfacing, Slice 3 marking + retrieval respect) + `hands-off-lifecycle` (Slice 2 gate layer). One amendment, three sequenced slices (D3).
**Status-file target:** `docs/STATE.md` + FBM roadmap backfill (§9).
**Quality bar:** ODD §2.5 — every AC outcome-shape, method-in-AC test passed on each; ≥1 outcome-altitude AC per AC family (production entry-point, no pre-arranged state); no API key anywhere (`feedback_no_anthropic_api_key` — all three slices are deterministic, D4).

---

## §1 Summary / TL;DR

**What ships:** the structural replacement for two behavioral rules that have demonstrably failed under repetition — (1) a **git-derived plan-state index**: per-project, the set of plan-docs + their REAL build-state (sealed / partially-sealed / pending), derived fresh from `docs/plans/` + the git ref graph, surfaced concisely at session/turn start and queryable on demand; (2) a **claim-vs-stored-state guard**: a new live layer on the KP9 draft-gate seam that, when an outbound draft asserts work-state — positive ("X is built/sealed/shipped") or **negative** ("X isn't planned / doesn't exist") — verifies the assertion against ground truth (the plan-state index + `derive_project_state` + git refs) and steers the model with the contradicting evidence BEFORE the claim reaches the user; (3) **supersession correctness**: a production mechanism to durably mark a corpus rule superseded-by its successor, plus corpus-retrieval honor of the existing `superseded-by` marker convention so a premise-flipped rule stops outranking or mis-pointing.

**The failure this kills (2026-06-09, live, owner-caught):** asked about the `claude -p`→subagent migration, the persona searched only `memory/`, hit the stale un-marked `no-api-key` rule, found no migration decision *there*, and asserted "not planned" — while the plan, greenlight, and 2/3 of the seals sat in `docs/plans/` + git. Slice 1 makes that state ambient; Slice 2 catches the false assertion at claim-time; Slice 3 retires the mis-pointing rule. Each slice independently blocks one leg of the failure; together they close it.

**AC families:** `AC.PSI.*` (plan-state index), `AC.CLG.*` (claim guard), `AC.SUP.*` (supersession) — each family carries its own outcome-altitude AC.

**Key decisions baked (full list + recommendations in §3):** rootcause framing over the roadmap's literal Cycle-2 text, with the conflict named (D1); steer-not-block, fail-open guard posture (D2 ★); one three-component amendment, slices sequenced 1→2→3 (D3); deterministic detection, no LLM in any hot path (D4); supersession marking + retrieval-honor now, premise-flip AUTO-detection deferred (D5); plan-roots derived per registered project via `PROJECT_REGISTRY` (D6).

**F2 RF on scope realism:** the honest cut is that this cycle makes work-state claims structurally verified and plan-state ambient for the *registered projects' repos*; it does NOT ship claim metadata/volatility (MM2), the no-eternal-negatives storage lint (MM3), consolidation (roadmap Cycle 3), or automatic detection that a rule's premise flipped — those are named deferrals (§7) with the reasoning in §10, not silent drops. Scope-tightness per slice annotated in §10 #5.

---

## §2 Placement decisions

| Item | Placement | Rationale |
|------|-----------|-----------|
| Plan-state derivation (enumerate plan-docs per project + derive each plan's build-state from git refs/seal evidence, fresh, never prose) | **`loam-cli`** (`framework/tools/loam/src/loam_cli/audit/` — sibling/extension of `registry.py`, additive) | Slice C precedent: loam-cli's audit surface OWNS ground-truth STATE derivation from git. Plan-state is the same shape one level up (plans, not modules). Lens-1: extend the engine that exists, don't duplicate. |
| Plan-state surfacing (concise capped block at session/turn start) + on-demand query entry point | **`primary-persona`** keep-pace (sibling of `project_state.py`) | Slice D precedent verbatim: TTL-cached, char-capped, fail-soft turn contributor; the query entry point is what Slice 2's guard calls. |
| Claim-vs-stored-state guard | **`hands-off-lifecycle`** (`hooks/keep_pace/draft_gate.py` gains a live layer alongside Layer C, or a sibling module the gate routes through — builder's call) | The roadmap's MM1 names this exact seam; the gate already routes every user-facing surface (AC.KP9.3) with the fail-open + model-facing-only contracts the guard must inherit. Lens-1: a new check on a built gate, not a new gate. |
| Ground-truth verification the guard performs | **reused** — plan-state query (Slice 1) + `derive_project_state` (Slice C) + git-ref probes | The guard is a CONSUMER of derivation surfaces, never a re-deriver (the Slice D "does NOT re-derive" discipline). |
| Supersession marking mechanism (durably mark a corpus doc superseded-by a successor) | **`primary-persona`** (`file_memory.py` orbit — the component that owns the `superseded-by` convention) | T1.1 owns the marker convention + the episode-side honor; the marking entry point lives with the convention. |
| Corpus-retrieval supersession honor | **`primary-persona`** keep-pace (`corpus_index.py` / `retrieval.py`) | The gap is corpus-side (grep-verified zero supersession handling); the fix lands where the ranking happens, mirroring the episode-side `SUPERSEDED_PENALTY` semantics. |

**Out of placement (NOT this cycle):** consolidation (roadmap C1/C2 — Cycle-3 scope; the work-state-projection half is substantially delivered by the sealed WMS census); MM2 claim metadata + MM3 storage lint; premise-flip auto-detection; indexing of non-git scratch/research artefacts (§7).

---

## §3 Named decisions (with recommendations) — surface to Luke

★ flags the one genuine owner product-shape call; the rest are autonomous method-calls recorded for the trail.

### D1 — Which Cycle-2 framing governs: the roadmap's literal text (R2 + MM1) or the 2026-06-09 rootcause's three layers. **RECOMMEND: the rootcause framing (plan-state index + claim guard + supersession). Conflict named per F2; autonomous (the rootcause doc is the owner-validated fresher artefact), surfaced for the record.**
- *The conflict:* the roadmap (2026-05-29) defines Cycle 2 as **R2** (always-inject guaranteed-surface of load-bearing state) + **MM1** (claim guard). Eleven days later, R2's substance has largely shipped by other routes — Tier-0 evidence: Slice D injects per-project STATE every turn (`project_state.py`, sealed); the WMS census renders all-work state live (`self-maintaining-work-loop`, sealed `029f82ba`); keep-pace is activated in `~/.claude/settings.json`. The *remaining* R2-shaped hole is precisely that **plan-docs + their build-state are in no surfaced or queryable index** — which is the rootcause's Layer B.2. The rootcause additionally adds supersession (Layer C), which the roadmap had parked in Cycle 4+ (MM-adjacent) despite it being one of the two legs of the live failure.
- *The alternative rejected:* building the roadmap's R2 as written would re-deliver shipped surfaces; skipping supersession would leave the stale-rule leg of the 06-09 failure open.

### D2 — ★ Guard posture: steer (model-facing correction, fail-open) vs block (refuse the send). **RECOMMEND: STEER — on a contradicted claim the guard injects a model-facing correction ("draft asserts X; ground truth shows Y — verify before asserting") and the model revises; the guard NEVER blocks a send and fails open on any internal error. The one owner call.**
- *Why:* this is the KP9 gate's existing posture (fail-open `:621`, model-facing-only AC.KP9.4) and the channel-hook's warn-on-slip precedent. A blocking guard with imperfect claim-detection (D4 honest risk) would wedge legitimate sends on false positives — for a comms-critical path, availability beats strictness. The steer carries the *evidence*, which per the reconciliation memory is what actually resolves the conflict.
- *The owner alternative:* block-on-contradiction for the narrow "verified-false work-state claim" class only. Honest cost of the recommendation: a steered model could in principle still send the false claim; the AC (AC.CLG.1) therefore requires the steer to carry the contradicting evidence inline, making the residual failure a visible model-disobedience rather than a silent gap.

### D3 — One three-component amendment vs three single-component amendments. **RECOMMEND: ONE amendment, three slices built in sequence 1→2→3 inside it. Method-call.**
- *Why:* the slices share a fence ruling, a review, and a seal window; builds serialize in one tree regardless (`feedback_serialize_amendment_builds`); Slice 2 depends on Slice 1's query surface, so independent amendments would just re-impose the same ordering with 3× bookkeeping. Lens-5 stopping criterion: a per-slice split adds coordination overhead without tightening any AC beyond what the per-family AC sets already pin.
- *Cost honestly:* a halt in Slice 2 stalls the seal of already-built Slice 1 work. Acceptable — the halt triggers (§8) are narrow, and a halted cycle surfaces with slices 1/3 reviewable.

### D4 — Claim detection mechanism: deterministic (lexical/structural detection of work-state assertions) vs LLM classification. **RECOMMEND: deterministic-only in the hot path. No LLM call, no API key, in any per-turn or per-send path (hard constraint, not preference). Method-call with a named constraint.**
- *Why:* the gate runs on every send; latency + the no-API-key rule + fail-open all point one way. The detection target is NARROW (work-state claims about plans/builds/seals — a small assertion grammar), not general fact-checking, which keeps deterministic precision plausible.
- *Honest risk + escape:* if build-time precision testing shows deterministic detection over-fires on ordinary prose or misses the canonical claim shapes, that is halt trigger §8 #1 — surface for a mechanism ruling (e.g. an in-session-subagent assist OFF the hot path), never a silent LLM call.

### D5 — Supersession: ship marking-mechanism + retrieval-honor now; AUTO-detection of premise-flipped rules deferred. **RECOMMEND: defer auto-detection. Method-call.**
- *Why:* judging that "newer artefact X flips rule Y's premise" is semantic work (LLM-class) with real wrong-mark risk; the correctness-critical part — that a marked rule stops mis-pointing — is deterministic and ships now. The 06-09 instance was hand-marked; the gap was that *nothing honored or systematized the mark*. Auto-detection composes later on C1 consolidation (§7).

### D6 — Plan-index scope: loam's `docs/plans/` only vs per-registered-project plan roots. **RECOMMEND: derive per registered project via `PROJECT_REGISTRY` (each `ProjectStateSpec` repo root's plans dir where one exists), fail-soft when a project has none. Method-call.**
- *Why:* the registry is the existing single source of "which repos do we derive truth from" (now loam + cairn + litrpg); hardcoding loam would re-create the same blind spot one repo over. A project with no plans dir degrades to no block — the Slice C/D fail-soft discipline.

---

## §4 Spec-objective placement

- **Binds to:** the FBM roadmap's Q4 metamemory gap + Q1 drift finding (the built-but-unsurfaced state problem), and the two hard behavioral rules this build structurally replaces (`feedback_published_state_only_from_git_refs`, `feedback_notes_and_users_are_pointers_evidence_resolves` — both of which *name this build as their own fix*).
- **Ladders up to:** **VALUE_PROPOSITION prime objective** — the protection floor of Lens 0: "no real memory → confident stale claims" is a named betray-any-user failure mode; a system that asserts false work-state to its user fails the trust promise (P2: never silently lose what was said/decided) regardless of how good translation is. The 06-09 instance is the prime directive's failure mode demonstrated live (rootcause §4).
- **Prime-directive tie (Lens 0):** the user brings "what's the state of my stuff?"; loam owns knowing — from ground truth, with a warning light when it doesn't. The claim guard IS the warning light the metamemory gap lacked.

---

## §5 Sealed-component fence

**Three components touched; all with manifest entries; all ADDITIVE.**

1. **`loam-cli`** (SEALED) — Slice 1 derivation. **Fence: ADDITIVE-ONLY.** Permitted: a new plan-state derivation module under `audit/` (or additive extension of `registry.py`'s spec surface); read-only git/disk probes. **Forbidden without a halt:** changing `derive_project_state` / `ProjectStateSpec` / `PROJECT_REGISTRY` existing contracts or any existing CLI verb behavior (§8 #2).
2. **`primary-persona`** (SEALED, live sidecar) — Slice 1 surfacing + Slice 3. **Fence:** a new keep-pace plans-block turn contributor (Slice-D cap/TTL/fail-soft discipline; registered additively); a new supersession-marking entry point in the `file_memory` orbit; supersession honor added to corpus ranking as an ADDITIVE ranking factor. **Forbidden without a halt:** breaking any existing `AC.KP1.*` / retrieval-metric (P@5 regression guard) test; changing the episode-side `SUPERSEDED_PENALTY` semantics; any destructive edit of corpus content by the marker (marking annotates, never deletes — AC.SUP.3); changing `stop_emitter` / chain contracts.
3. **`hands-off-lifecycle`** (SEALED, `frozen_baseline` pinned per #23) — Slice 2. **Fence:** the draft-gate gains a new claim-guard layer (or routed sibling module); the gate's fail-open contract, model-facing-only feedback (AC.KP9.4), Layer A/B/C existing behavior, and every existing `AC.KP9.*` test are preserved byte-for-byte in outcome. **Forbidden without a halt:** any path where a guard error blocks a send; any user-facing guard text; cross-component imports that violate the D-KP9.1 self-containment rule (the guard reaches primary-persona/loam-cli surfaces the same lazy fail-soft way `session_surface.py` does).

Seal via `loam amend apply` + `loam amend seal` — **name `loam amend apply` explicitly in the build dispatch** (`feedback_dispatch_explicit_loam_amend_apply`); serialize all slices in one tree (`feedback_serialize_amendment_builds`).

---

## §6 Acceptance criteria (outcome-shape; method-in-AC test passed on each)

AC IDs scope-descriptive (`feedback_scope_descriptive_ac_ids`). Each AC is satisfiable by more than one method; method is the builder's call.

### AC.PSI.\* — plan-state index (Slice 1)

**AC.PSI.1** — For each registered project with a plans dir, a production derivation produces, FRESH from disk + the git ref graph, the set of plan-docs with per-plan identity and build-state (e.g. no-build-evidence / partially-sealed / sealed, with seal evidence) — never from a plan's own prose status line; sealing a slice in the real repo and re-deriving changes the reported state with NO doc edit. *(Outcome: derived-not-stored plan-state; derivation mechanics are the builder's call.)*

**AC.PSI.2** — The session/turn-start surface includes ONE concise plans block — in-flight plans + their real build-state, one short line each — derived live, TTL-cached, within a hard char cap, fail-soft (a derivation failure yields no block, never a wedge or a wrong state). *(Outcome: ambient plan-state without context re-bloat; the cap/TTL values + render shape are the builder's call.)*

**AC.PSI.3** — A production query entry point answers "what stored plan/decision state exists matching this topic?" over the derived index (plan-docs incl. sealed archive + seal-commit evidence), returning matches with their build-state and an explicitly-scoped empty result (what was searched) on no match — never a bare "nothing exists". *(Outcome: the queryable surface the guard consumes + the dated-scoped-negative form from the reconciliation memory; query mechanics are the builder's call.)*

**AC.PSI.OA (outcome-altitude: true)** — Against the LIVE loam repo with NO pre-arranged state: the production derivation + surfacing entry points report a real plan currently in partial build-state, and the reported state matches independent git verification (seal-commit reachability) performed by the test, not by the module under test. *(Production entry points, real repo, no fixtures.)*

### AC.CLG.\* — claim-vs-stored-state guard (Slice 2)

**AC.CLG.1** — When an outbound draft asserts work-state — positive ("X is built/sealed/shipped/published") or negative ("X is not planned / not built / doesn't exist") — about a subject resolvable to stored state, the guard verifies the assertion against ground truth (the plan-state query + project STATE + git evidence) and, on contradiction, the model receives a model-facing steer that names the claim AND the contradicting evidence before the draft is sent; the steer is never rendered as user-facing text. *(Outcome: contradicted claims can't pass silently; detection grammar, verification order, steer wording are the builder's call.)*

**AC.CLG.2** — A negative existence claim whose subject the guard CANNOT resolve against any ground-truth source yields a steer prompting the scoped-honest form ("not found in <searched surfaces>; <unsearched> unchecked") rather than a silent pass — the eternal-negative shape specifically; ordinary unresolvable prose is not steered. *(Outcome: unverified flat negatives get a warning light; scoping mechanics are the builder's call.)*

**AC.CLG.3** — A work-state claim the ground truth CONFIRMS passes with no steer, and non-claim prose passes with no steer — demonstrated against a corpus of true-claim + ordinary-prose drafts. *(Outcome: precision / no alarm fatigue; threshold mechanics are the builder's call.)*

**AC.CLG.4** — Any internal guard error yields a PASS verdict (fail-open), the guard adds no LLM/API call to the send path, and every existing gate behavior (`AC.KP9.*`) is preserved. *(Outcome: the gate's availability + no-API-key contracts hold; method is the builder's call.)*

**AC.CLG.OA (outcome-altitude: true)** — Against the LIVE repo with NO pre-arranged state, through the production gate entry point: (a) a draft asserting that a real, partially-built plan "isn't planned / doesn't exist" produces a steer citing that plan's real evidence; (b) a draft asserting a genuinely-sealed item is sealed produces NO steer. *(The literal 2026-06-09 failure replayed against production machinery and caught.)*

### AC.SUP.\* — supersession correctness (Slice 3)

**AC.SUP.1** — A production entry point durably marks a corpus document superseded-by a named successor using the existing `superseded-by` marker convention; the mark is on-disk, machine-readable, and carries date + successor pointer. *(Outcome: a real marking mechanism instead of a hand-edit; invocation surface is the builder's call.)*

**AC.SUP.2** — Corpus retrieval honors the marker: a superseded document no longer outranks its successor for queries both match, and when a superseded document IS surfaced it carries its supersession annotation (the reader sees "superseded by X", never the bare stale rule). *(Outcome: marked rules stop mis-pointing; ranking mechanics are the builder's call — the episode-side penalty semantics are precedent, not prescription.)*

**AC.SUP.3** — Marking never deletes or rewrites the superseded document's content beyond the marker itself; un-marking restores prior retrieval behavior. *(Outcome: audit trail + reversibility; method is the builder's call.)*

**AC.SUP.OA (outcome-altitude: true)** — Mark a real corpus rule via the production marking entry point, then run a production retrieval on the rule's topic with no pre-arranged index state: the successor ranks ahead of (or the stale rule is surfaced annotated-superseded versus) the marked rule. *(Production entry points, real corpus.)*

---

## §7 Out of scope (deferred + when)

- **Consolidation (roadmap C1 session-end + C3 scheduled)** — Cycle-3 scope; not implicated in any of the named failures (all three failure legs are state-verification, not summarization). Re-enters after this cycle on the roadmap's own sequencing. The C2 work-state-projection half is substantially delivered by the sealed WMS census; the residual is consolidation of *episodic* memory, deferred with it.
- **MM2 claim metadata (volatility / verifiability / last-verified on stored memories)** — the guard verifies against git ground truth directly, which is strictly stronger for the work-state class this cycle covers; metadata becomes load-bearing when guarding softer claim classes. Deferred to the cycle that widens guard coverage.
- **MM3 no-eternal-negatives storage lint** — the storage-side twin of AC.CLG.2 (which handles the assertion side). Small, but write-side linting of the rules corpus touches authoring flows outside this fence. Named follow-on; AC.PSI.3's scoped-empty-result shape pre-builds its vocabulary.
- **Premise-flip AUTO-detection for supersession** (D5) — semantic/LLM-class judgment; composes with C1 later. This cycle ships the mechanism + honor; humans/persona invoke the mark.
- **Indexing scratch/research artefacts** (`.scratch/claude-output/`) into the plan-state index — valuable (the 06-09 artefacts partly lived there) but scratch is by-design ephemeral + ungoverned; indexing it needs its own retention/trust ruling. Named follow-on.
- **Registering further projects / plan roots** — the index inherits whatever `PROJECT_REGISTRY` registers; widening the registry stays its own concern.

---

## §8 Halt triggers (abort the in-flight build + surface)

1. **Deterministic claim detection cannot reach usable precision** — it over-fires on ordinary prose or misses the canonical claim shapes in build-time testing. Halt + surface a mechanism ruling (D4's named escape); do NOT silently add an LLM call to the send path.
2. **Plan-state derivation would require changing an existing Slice-C contract** (`derive_project_state` / `ProjectStateSpec` / registry semantics) or an existing CLI verb. Halt — additive-only fence (§5 #1).
3. **Supersession honor breaks an existing retrieval AC or the P@5 regression guard.** Halt — surface a ranking-semantics ruling rather than weakening a sealed retrieval guarantee.
4. **The plans block + guard checks exceed the keep-pace latency/char discipline** even with Slice-D-style caching. Halt — surface a cadence/caching ruling; never ship a per-turn latency or context-bloat regression (the #80 mandate).
5. **The guard cannot inherit the gate's fail-open + model-facing-only contracts** for any reason. Halt — those contracts are load-bearing (a guard that can block a send or leak gate text to the user is worse than no guard).
6. **An AC drifts to method-in-AC during build** — fix the AC text (doc-only) per `feedback_loose_AC_text_fix_AC_not_implementation`, never the implementation.
7. **ODD violation discovered in the work or surrounding code** — halt and surface per `feedback_subagent_odd_violation_halt`; never silently extend.

---

## §9 Bookkeeping (backfill on seal)

- **`docs/STATE.md`** — record the correctness cycle: plan-state index (loam-cli + primary-persona), claim guard (hands-off-lifecycle), supersession mechanism + corpus honor (primary-persona).
- **`docs/design/fbm-state-and-memory-roadmap-2026-05-29.md`** — backfill a dated addendum: Cycle 1 (activate + unify) DONE; Cycle 2 delivered in the rootcause framing (this plan, D1); R2's substance delivered via Slice D + WMS census; consolidation remains the open Cycle-3 item with its precondition (live warm-up) now long satisfied.
- **pos3 memory corpus (owner-side, post-seal):** `feedback_published_state_only_from_git_refs.md` + `feedback_notes_and_users_are_pointers_evidence_resolves.md` each gain a dated note that their named structural fix is built (rules stay — they're the discipline; the build is the enforcement).
- **Master work queue item #3 (Memory Cycle 2)** → completion note on seal.

---

## §10 F2 Ruthless Feedback (honest doubts + named design risks)

1. **The roadmap's Cycle-2 text is partially stale and I am deliberately not building it as written** (D1). *Disagreement:* dispatching "Cycle 2 per the roadmap" would re-deliver R2 surfaces that shipped 06-05/06-09 via Slice D + the WMS census. *Evidence:* `project_state.py` (sealed, in the live lens), `self-maintaining-work-loop` seal `029f82ba`, live `~/.claude/settings.json` wiring — all Tier-0 read today. *Alternative (taken):* the rootcause's three layers, which include the two legs the roadmap deferred or under-weighted (plan-state; supersession). Named here so the owner ratifies the reframe knowingly.
2. **Claim-detection precision is the genuinely uncertain part of this cycle.** *Disagreement with my own plan:* "deterministic detection of work-state claims" sounds clean; natural prose is messy, and a guard that cries wolf gets ignored (alarm fatigue defeats the purpose as surely as silence). *Evidence:* no existing in-tree precedent for assertion-detection (Layer B detects vocabulary, not propositions). *Alternative (baked in):* AC.CLG.3 makes precision a first-class AC with a no-steer corpus, and §8 #1 makes "can't reach precision" a halt, not a degrade. Scope-confidence honesty: this is the slice where the method could come back different from anyone's current mental model — which is why its ACs pin outcomes hardest and prescribe mechanism least.
3. **A steered model can still disobey (D2 residual).** *Disagreement:* steer-not-block means the guard's catch is advisory at the last hop. *Evidence:* KP9's own design accepts this for jargon (fail-open, model-facing). *Alternative (named for the owner):* the block-posture variant for verified-false claims only — available as a later tightening once false-positive rates are observed; starting at block risks wedging sends on day-one detection errors. The residual failure mode is at least *visible* (evidence injected) rather than silent.
4. **The index covers governed plan-docs, not every place a decision can live.** *Disagreement:* the 06-09 artefacts also lived in `.scratch/` — out of scope here (§7). *Evidence:* rootcause §1 names three locations; this cycle indexes two (plans + git). *Alternative:* AC.PSI.3's explicitly-scoped empty result ("searched X, not Y") keeps the gap honest at answer-time rather than invisible; scratch-indexing is a named follow-on needing its own trust ruling.
5. **Scope-confidence (F4) annotation per slice:** Slice 1 TIGHT (high confidence — Slice C/D precedent is near-isomorphic; constraints pin outcome, method inferable). Slice 3 TIGHT (the marker convention + penalty semantics exist; this is extension of a shipped pattern). Slice 2 MEDIUM — outcome pinned hard (the ACs), method left deliberately loose (detection grammar, verification order, steer shape all builder's-call) because confidence in any single detection design is genuinely low. The dispatch brief should carry these annotations.
6. **No new always-on context cost without an AC guard.** The plans block adds turn-start bytes; AC.PSI.2's hard cap + fail-soft is the same contract that kept Slice D honest. If the cap forces uselessly terse rendering, that surfaces as a §8 #4 halt, not silent spill.

---

## §11 Provenance trail (all Tier-0 verified on disk/git/settings 2026-06-09 unless noted)

- Live failure + layered fix — `pos3/workspace/.scratch/claude-output/why-memory-was-wrong-rootcause-2026-06-09.md` (Layers A/B/C; §3 "the corpus already diagnosed this"; §6 greenlight recommendation).
- FBM roadmap — `docs/design/fbm-state-and-memory-roadmap-2026-05-29.md` (Q1 drift finding; Q4 MM1; recommended cycles §"RECOMMENDED next-cycle plan").
- Keep-pace LIVE — `~/.claude/settings.json` hooks: UserPromptSubmit → `framework/hands-off-lifecycle/hooks/keep_pace/user_prompt_submit.py`; PreToolUse → `keep_pace/pre_tool_use.py` (read this session).
- Retrieval unification DONE — `framework/primary-persona/src/loam/primary_persona/keep_pace/retrieval.py:160` ("merges its episode hits"), `:239-241` (`FileMemoryStore` import + search).
- Corpus-side supersession ABSENT — `grep -rn supersed framework/primary-persona/src/loam/primary_persona/keep_pace/` → no matches (this session).
- Marker convention + episode-side honor — `framework/primary-persona/src/loam/primary_persona/file_memory.py:436-442` (`SUPERSEDED_PENALTY`), `:1216-1221` (frontmatter contract), `:1382` (`_superseded_marker`).
- Gate seam — `framework/hands-off-lifecycle/hooks/keep_pace/draft_gate.py:431` (`SEEDED_CONSTRAINTS`), `:51` (Layer C narrow-set note), `:621` (fail-open).
- Project-STATE engine — `framework/tools/loam/src/loam_cli/audit/registry.py` (`derive_project_state` at `:138`; registry includes `litrpg` per `_default_registry` read this session); **no `docs/plans` reference in the file** (grep, this session).
- Slice D surfacing discipline — `framework/primary-persona/src/loam/primary_persona/keep_pace/project_state.py` (`_STATE_TTL_SECONDS=60`, `_STATE_BLOCK_CHAR_CAP=600`, fail-soft contract in module docstring).
- WMS census + ground-truth capture (work-ITEM state, sealed) — `docs/plans/self-maintaining-work-loop.md` + seal commits `74fdb418` / `029f82ba` (git log, this session).
- Behavioral rules being replaced — `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_published_state_only_from_git_refs.md` (incl. the 2026-05-29 + 2026-06-09 extensions naming this build) + `feedback_notes_and_users_are_pointers_evidence_resolves.md` (the reconciliation protocol + three-piece build proposal).
- Current main tip — `22df8683` (v1.3.0 post-publish backfill; `git log origin/main`, this session).

---

## §14 Method-decision register (populated at build time)

*Placeholder — D1..D6 narratives + commit SHAs backfilled by the builder + `loam amend seal --plan-doc`.*

---

### Commit SHAs

- Amendment commit: `7e6621f999cec080867e256da01a1da6334c101b` —
  `fix(hands-off-lifecycle): H19 admits interim top-level kernel/ prefix at first SEAL_COMMIT crossing`
- Seal commit: `cb0082b6ce27c4050310ee889efd908d97fbf953` —
  `chore(seals): fbm-correctness-claim-guard-plan-index-supersession — loam-cli+primary-persona+hands-off-lifecycle at 7e6621f`
## Effort estimate (duration rubric — AI-time, ranges with midpoint)

| Slice | Category | Estimate |
|---|---|---|
| Slice 1 — plan-state index (loam-cli derivation + persona surfacing) | multi-component amendment slice | 25–50 min (mid 35) |
| Slice 2 — claim guard (gate layer + precision corpus) | single-component slice, elevated test burden | 30–70 min (mid 50) |
| Slice 3 — supersession (marking + corpus honor) | single-component slice on existing pattern | 15–35 min (mid 25) |
| Apply + seal + bookkeeping | amendment mechanics | 10–20 min (mid 15) |
| **Total** | | **80–175 min, midpoint ≈ 125 min** |

Owner gate-review time is a separate line item (owner availability). Log actuals post-build for calibration.

# FBM correctness cycle — plan-state index + claim guard + supersession correctness

Per `docs/plans/fbm-correctness-claim-guard-plan-index-supersession.md`, motivated by the
live 2026-06-09 failure (the persona confidently asserted the claude-p→subagent migration
"wasn't planned" while the plan, greenlight, and 2/3 of its seals sat in docs/plans/ + git)
and the FBM roadmap's Cycle-2 metamemory gap (Q4). The behavioral rule that should have
caught it (feedback_published_state_only_from_git_refs) had already been promoted to hard
+ extended twice and failed anyway — recurrence-despite-corpus is the corpus's own trigger
to build structure. This amendment IS that structure.

Three sequenced slices, one amendment, three sealed components touched ADDITIVELY:

  1. **Plan-state index (Slice 1 — loam-cli + primary-persona).** A derivation in the
     Slice-C audit orbit that enumerates, per registered project (PROJECT_REGISTRY),
     the plan-docs + each plan's REAL build-state — fresh from disk + the git ref graph
     (seal-commit evidence), never from a plan's own prose status line. Surfaced as ONE
     concise capped TTL'd fail-soft plans block in the turn-start lens (the Slice-D
     discipline verbatim) and exposed as a production query entry point ("what stored
     plan/decision state matches this topic?") whose empty result is explicitly scoped
     ("searched X; Y unchecked") — never a bare "nothing exists".

  2. **Claim-vs-stored-state guard (Slice 2 — hands-off-lifecycle).** A new live layer on
     the KP9 draft-gate seam (the exact seam the roadmap's MM1 names; today Layer C checks
     only a hardcoded SEEDED_CONSTRAINTS tuple). When an outbound draft asserts work-state
     — positive ("X is built/sealed/shipped") or NEGATIVE ("X isn't planned / doesn't
     exist") — the guard verifies against ground truth (the plan-state query +
     derive_project_state + git evidence) and on contradiction injects a MODEL-FACING
     steer naming the claim + the contradicting evidence before the send. Steer-not-block
     (owner call D2 ★): fail-open on any internal error, never a blocked send, never
     user-facing guard text, no LLM/API call in the send path (deterministic detection
     only — precision is a first-class AC; can't-reach-precision is a HALT, never a
     silent LLM fallback). True claims and ordinary prose pass un-steered.

  3. **Supersession correctness (Slice 3 — primary-persona).** A production entry point
     that durably marks a corpus document superseded-by a named successor (the existing
     T1.1 superseded-by frontmatter convention — which file_memory honors on the episode
     side but the KP1 corpus retrieval ignored entirely, grep-verified), plus corpus-
     retrieval honor of the marker: a superseded rule no longer outranks its successor,
     and when surfaced carries its supersession annotation. Marking never deletes content;
     un-marking restores prior behavior. Premise-flip AUTO-detection is a named deferral
     (D5) — this ships the mechanism + the honor.

Framing decision (D1, named per F2): the roadmap's literal Cycle-2 text (R2 + MM1) is
partially stale — R2's guaranteed-surface substance shipped 06-05/06-09 via Slice D +
the WMS census, and keep-pace is activated live. This amendment follows the fresher
owner-validated rootcause framing (plan-state index + claim guard + supersession), which
covers the two failure legs the roadmap deferred. Consolidation (roadmap Cycle 3), MM2
claim metadata, MM3 storage lint, and scratch-artefact indexing are named deferrals.

AC families (each with an outcome-altitude AC against production entry points + the LIVE
repo, no pre-arranged state):
  - AC.PSI.1–3 + AC.PSI.OA — derived-not-stored plan-state; ambient capped surfacing;
    scoped-negative queryability; live-repo state matching independent git verification.
  - AC.CLG.1–4 + AC.CLG.OA — contradicted work-state claims (positive AND negative)
    steered with evidence; unresolvable flat negatives prompted to the scoped-honest
    form; true claims + ordinary prose pass clean; fail-open + no-API-key + AC.KP9.*
    preserved; the literal 2026-06-09 failure replayed and caught.
  - AC.SUP.1–3 + AC.SUP.OA — durable machine-readable marking; retrieval honor +
    annotation; reversible/non-destructive; live-corpus mark-then-retrieve.

Fence: all three components ADDITIVE-ONLY. loam-cli: no change to existing Slice-C
contracts (derive_project_state / ProjectStateSpec / registry) — HALT otherwise.
primary-persona: no broken AC.KP1.* / P@5 regression-guard test, no change to episode-side
SUPERSEDED_PENALTY semantics, marker annotates-never-deletes. hands-off-lifecycle: the
gate's fail-open + model-facing-only contracts and every AC.KP9.* behavior preserved;
a guard that can block a send or leak text to the user is a HALT. Latency/char budgets
per the Slice-D / #80 anti-bloat mandate — exceed → HALT.

No ODD violation in surrounding code; every added path traces to a named AC
(AC.PSI.* / AC.CLG.* / AC.SUP.*), no defensive code for unnamed cases.
