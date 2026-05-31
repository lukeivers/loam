# FBM state + memory-system roadmap — 2026-05-29

**Date:** 2026-05-29
**Status:** research artefact (READ-ONLY investigation; no code/system touched)
**Owner:** Luke Ivers
**Author:** grounding pass over the loam memory docs + amendment/git history (Tier-0 against canonical loam `/Users/lukeivers/loam` @ `58b6255`)
**Why this exists:** two failures on 2026-05-29 — (1) a stale note trusted over live reality; (2) a "Book 1 done" claim made while pipeline state (Layers 6–7 remain) sat un-surfaced. Owner framing: *"FBM = File-Based Memory. It's supposed to be a COMPREHENSIVE memory storage system — not file-based RULES storage."* This artefact establishes the canonical definition, maps designed-vs-built with git/date evidence, and proposes phased retrieval / consolidation / metamemory builds.

**Trust discipline:** every history claim cites a commit/date/doc; every "currently does Y" cites a file/symbol. Unverifiable items are marked **UNVERIFIED** with how to check.

---

## Q0 — Canonical definition + designed intent of FBM

**FBM = File-Based Memory** (the docs/components contract calls the v0.1.0 substrate **FBE — "file-backed episode memory"**; the amendment stream and queue call it **FBM — "file-based memory."** Same thing, two names — see the naming-drift note below). It is loam's **session-bridging memory substrate**: plain markdown files on disk, written by the persona's Stop hook, read at SessionStart and UserPromptSubmit, so the next session is not a cold start (`docs/components/memory.md:5-15`).

**What FBM was DESIGNED to store/do** — and the answer to the owner's worry directly: **FBM was NOT designed as rules-storage. It was designed as an EPISODE store** — *"one markdown file per turn"* of conversation, retrieved by relevance.

Tier-0 from the implementation, `framework/primary-persona/src/loam/primary_persona/file_memory.py`:
- `:19` — *"file-based primitives: per-turn markdown episode files + a grep/BM25 [retrieval surface]"*
- `:26` — *"Episode shape: one markdown file per turn."*
- `:58-60` — `FileMemoryStore.write_episode` writes one markdown file per turn at `<memory-dir>/episodes/<workspace-slug>/<YYYY-MM-DD>/<turn-id>.md`
- `:146-148` — the store mirrors graphiti's `add_episode` / `search` signatures (*"minimum-viable shape"*) — i.e. FBM is the **file-backed stand-in for the graph-of-episodes memory** (graphiti/S3), not a rules file.

So the canonical store map (`docs/design/memory-architecture.md:21-27`) has **three physically-distinct stores**, and the owner's intuition is about a *conflation* between two of them:

| Store | Holds | Lives at | Status (Tier-0 2026-05-28, per memory-architecture.md §1) |
|---|---|---|---|
| **S1 — CLAUDE.md hierarchy** | static rules, design lenses, prefs-as-rules | `~/.claude/CLAUDE.md`, `<repo>/CLAUDE.md` | live; re-read after `/compact` |
| **S2 — Claude-native auto-memory (the `feedback_*.md` corpus + `MEMORY.md` index)** | **discipline learnings / "remember that…"** | `~/.claude/projects/<project>/memory/` | **live** — this is the RULES corpus |
| **S3 — graphiti memory-system** | per-turn episodic facts + entity/relationship graph | (designed) `kuzu_db` + MCP | **DESIGN-ASPIRATIONAL, NOT LIVE** — no `graphiti_core`, no `kuzu_db` on disk; `memory_consumer.py` is a Protocol shim (`memory_consumer.py:24-26` *"never imports memory-system source; the Protocol is sufficient"*) |

**FBM is the file-backed stand-in for S3** — the episodic store — built so loam has real episodic memory without the unshipped graph. Its designed job (the architecture's three user-promises, `memory-architecture.md:62-68`): **P1 transparent continuity** (carry context across sessions), **P2 trust** (never silently lose what the user said to keep), **P3 graceful scaling** (corpus grows for years without a load-day where it quietly stops). The store map (`memory-architecture.md:80-87`) explicitly assigns: **discipline-rules → S2; per-turn episodic facts → S3/FBM.** They are *complements, not competitors* (`memory-architecture.md:122`).

**The naming drift (worth a one-line fix):** `docs/components/memory.md:11` calls it **FBE** ("file-backed episode memory"); `docs/public-surface-manifest.md:82,135` calls it **FBE.7**; the amendment stream (#134/#135) and `memory-architecture.md` call it **FBM**. Same substrate. The dispatcher started this investigation with the name wrong — because the corpus itself carries both names. **Recommend: pick one (FBM) and sweep the other.**

---

## Q1 — Designed vs built + when the scope narrowed

### Designed-vs-built table (Tier-0)

| Layer / item | Designed (source) | Built? | Evidence |
|---|---|---|---|
| **FBM Tier 0 — episode store + BM25** (`M-FBM` baseline) | episode-per-turn markdown + grep/BM25 retrieval | **BUILT** | `file_memory.py` present; seal `1a1f830` (`SEAL_COMMIT.m-fbm-operational-health`), cited in amendment-134 §2 |
| **FBM Tier 1 — write-side + supersession** (T1.1 superseded-by marker, T1.2 encoding-context capture, T1.3 FIDRAFT cleanup-on-seal, T1.4 plan archive-on-seal) | `fbm-end-to-end-rethink-v2-synthesized-2026-05-21.md` §"Tier 1" | **BUILT** | amendment **#134**, sealed `0347760` (apply `ed8d3bf`), authored 2026-05-21; `file_memory.py:262 SUPERSEDED_PENALTY`, `:984 ENCODING_CONTEXT_FIELDS` |
| **FBM Tier 2 — retrieval mechanics** (T2.1 power-law base-level activation; T2.2 co-citation graph + 1-hop spreading activation) | v2 rethink §"Tier 2" | **BUILT** | amendment **#135**, sealed `32608d2` (apply `b41b52b`); `file_memory.py:1294-1313`, `access_log.py`, `cocitation_graph.py` present |
| **FBM T2.3 — pinned working set** (≤7 files, eviction-on-task-close) | v2 rethink §"Tier 2" / E.1 | **DEFERRED** | owner ruling TG 11810 (2026-05-21); queue `ws-fbm-tier-2-3-working-set` `deferred_at: 2026-05-21 16:17:34Z` (`pos3/.claude/workstream-queue.yaml:131`) |
| **FBM Tier 3 — orchestration** (T3.1 session-end consolidation; T3.2 scheduled consolidation) | v2 rethink §"Tier 3" | **DEFERRED** | queue `ws-tier3-orchestration` `deferred_at: 2026-05-21 19:00:00Z` (`pos3/.claude/workstream-queue.yaml:125`), reason *"depends on Tier 1 + Tier 2 having warm-up time. Re-evaluate after ~1 week."* |
| **S3 graphiti graph backend** | `memory-architecture.md:25` | **NOT LIVE** | no `kuzu_db`; `memory_consumer.py` Protocol shim only (Tier-0 2026-05-28, `memory-architecture.md:27`) |
| **memory-architecture M1** — compress MEMORY.md index to one-line pointers | `memory-architecture.md:143` | **UNVERIFIED** — MEMORY.md was 28.7KB/over-cap on 2026-05-28 | check: `wc -c ~/.claude/projects/-Users-lukeivers-pos3/memory/MEMORY.md` vs 25KB |
| **memory-architecture M2** — `InstructionsLoaded` budget-audit hook | `memory-architecture.md:144` | **NOT BUILT** (no evidence of a wired InstructionsLoaded hook) | check: grep `settings.json` + plugin `hooks.json` for `InstructionsLoaded` |
| **Keep-pace KP0** — wire UserPromptSubmit+PreToolUse chain, latency budget, fail-open | `keep-pace-with-user.md` KP0 | **BUILT in-tree** | amendment **#149**, sealed `ccfdc22`; `framework/hands-off-lifecycle/hooks/keep_pace/user_prompt_submit.py` |
| **Keep-pace KP1** — work-anchored per-prompt retrieval (BM25/FTS5 over the **markdown corpus**) | KP1 | **BUILT in-tree** | amendment **#150**, sealed `aadf2b7`; `test_AC_KP1_*` in `framework/primary-persona/tests/`; AC.KP1.6 cold-walk GREEN against live 114-file corpus |
| **Keep-pace KP5** — `OBJECTIVES.md` register, seeded with the two real objectives | KP5 | **BUILT in-tree** (file seed STAGED) | amendment #150; `test_AC_KP5_*`; the live `~/.claude/OBJECTIVES.md` seed is part of the gated activation step |
| **Keep-pace KP9** — abstraction-voice lint + Layer-C constraint draft-gate | KP9 | **BUILT in-tree** | amendment **#151**, sealed `6b37490`; `framework/hands-off-lifecycle/hooks/keep_pace/draft_gate.py` |
| **Keep-pace KP7** — SessionStart objective + last-state surface | KP7 | **BUILT in-tree** | amendment **#152**, sealed `07d3b59`; `framework/orchestrator/scripts/session_surface.py` |
| **Keep-pace KP2/KP3/KP4/KP6/KP8/KP10** — miss-gate, cross-session journal, ARC rotation, objective-lifecycle SKILL, drift audit, register judge | `keep-pace-with-user.md` §"Backlog" | **NOT BUILT** | backlog, gated on observed need / a week of score-logging (KP2) |
| **Live activation** of the whole keep-pace chain (`~/.claude/settings.json` + OBJECTIVES.md seed) | — | **NOT DONE — owner-gated** | `STATE.md` (#152): *"ONLY the single owner-gated live `~/.claude/settings.json` activation step remains"* |

### The drift finding (F2 — named, with evidence)

**The owner's hypothesis is HALF right, and the correction matters.** FBM did **not** narrow into rules-only storage — FBM *is* and always was the episode store, and Tiers 1+2 of it shipped (#134 `0347760`, #135 `32608d2`, both 2026-05-21). The real drift is **three-fold and more precise:**

1. **The comprehensive episode store is built but NOT WIRED LIVE.** FBM Tier 0/1/2 exist in `framework/primary-persona/` with passing tests, but the persona's per-turn read/write path that would make episodes actually flow is gated behind the **same un-flipped `~/.claude/settings.json` activation switch** as keep-pace. So at runtime, the operative memory is *de facto* S1 (CLAUDE.md) + S2 (the `feedback_*.md` rules corpus) — exactly what the owner observed — **not because FBM narrowed to rules, but because the episode store's live wiring was never turned on.** This is the load-bearing drift: **built ≠ live.** (Evidence: `STATE.md` #152 "live activation still STAGED-not-done"; `memory_consumer.py` is still a Protocol shim with no live backend per `memory-architecture.md:27`, 2026-05-28.)

2. **The COMPREHENSIVE layer was deferred and never came back.** The two pieces that make memory a *project/work-state model* rather than turn-logging-plus-rules are **Tier 3 consolidation** (episodic → semantic/state) and **T2.3 working set** — and BOTH were deferred on **2026-05-21** (queue entries above). The deferral reason was sound ("needs ~1 week warm-up; re-evaluate") — but **8 days later (2026-05-29) it was never re-evaluated.** The "re-evaluate after ~1 week" trigger fired with nobody listening. **This is when + how the scope narrowed: 2026-05-21 the comprehensive top (consolidation + working-set) was deferred for warm-up; the warm-up window closed and the re-eval never happened.** This is exactly a `feedback_workaround_masks_rootcause_urgency` shape — the deferral was a reasonable pause that silently became permanent.

3. **Two parallel memory tracks were built without a unifying retrieval surface.** FBM (episode store, primary-persona, #134/#135, BM25 + activation + co-citation) and keep-pace KP1 (a *separate* BM25/FTS5 index over the **markdown discipline corpus** — `feedback_*.md` + CLAUDE.md + OBJECTIVES.md, per STATE.md #150) are **two different indexes over two different corpora**, built three weeks apart, neither aware of the other at retrieval time. There is no single retrieval call that sees both episodes AND rules AND objectives. (Evidence: KP1's index is described in STATE.md #150 as "a NEW BM25/FTS5 index over the markdown corpus — feedback_*.md + CLAUDE.md hierarchy + OBJECTIVES.md" — it does **not** include the FBM episode store.)

**Net drift statement (with evidence):** FBM the episode store was fully designed (v2 rethink, 2026-05-21) and Tiers 0–2 built (#134 `0347760` / #135 `32608d2`), but (a) its live per-turn wiring sits behind an un-flipped activation switch, (b) the comprehensive consolidation/working-set tier was deferred 2026-05-21 and the "~1 week" re-eval trigger silently lapsed, and (c) a second retrieval track (keep-pace KP1) was built over the rules corpus without unifying with the episode store. The runtime result the owner sees — "memory is just rules" — is the *symptom* of (a)+(b), not a design narrowing.

---

## Q2 — Retrieval precision (today's mechanism + concrete improvements)

**How retrieval works today (Tier-0):**
- **FBM episode retrieval** (`file_memory.py`): BM25/FTS5 over per-turn episode markdown, then **× power-law base-level activation** (T2.1, `ln(Σ (now−t)^−0.5)`, Anderson & Schooler 1991) **× supersession penalty** (T1.1, `0.1×`), then **one-hop co-citation spread** (T2.2). Score = `BM25 × activation × supersession`, then spread. Mature ranking — *if it were running live.*
- **Keep-pace KP1 retrieval** (`framework/primary-persona/`, behind the activation switch): a separate BM25/FTS5 index over the *discipline corpus*, keyed on **prompt + active-objective + active-subgoal + last-turn topic** (the "work-anchor" — `keep-pace-with-user.md` §1 fix #1), top-N≤5 injected as plain-language `additionalContext`, silent on no-match via a zero-IDF floor.
- **No `memory-search` skill** found in the available-skills list; retrieval is hook-driven, not a user-invoked skill.

**Why load-bearing facts failed to surface (the two 2026-05-29 failures):**
- The **stale-note** failure: retrieval *did* surface the note; the failure was **trusting the note over live ground truth** — a metamemory/reconciliation gap, not a ranking gap. (See Q4.)
- The **"Book 1 done"** failure: the pipeline-state fact (Layers 6–7 remain) lived in files but was **never indexed into a retrievable, queryable work-state model** — there is no consolidation layer (Q3). KP1 might have surfaced a pointer *if* it were live AND *if* "is Book 1 done" lexically hit the right file; but a status claim isn't a retrieval query — it's an assertion that needs a **guard** (Q4), not better ranking.

**Concrete improvements (phased):**
- **R1 (highest leverage, do first): flip the activation switch + UNIFY the two indexes.** Make one retrieval call see FBM episodes + the rules corpus + OBJECTIVES.md. Today they're two BM25 indexes that don't know about each other. Either point KP1's indexer at the FBM episode dir too, or have the UserPromptSubmit contributor query both and merge by score. **This is mostly wiring of already-built parts** — very high confidence, tight scope.
- **R2: guaranteed-surface for load-bearing state.** A small "always-inject" set (active objectives, current pipeline/work-state, any `pinned: true` memory) that bypasses relevance ranking and is injected every turn under a hard byte budget — so load-bearing facts can't lose a ranking competition to chatter. This is **T2.3 working-set** (deferred) re-scoped as "guaranteed surface," and the missing half of the two failures.
- **R3: query expansion via the existing co-citation graph.** T2.2's graph is built; use it for *query* expansion (expand the work-anchor key through one hop before scoring), not only post-BM25 candidate spreading. Cheap, reuses shipped machinery, directly attacks F-PHRASING for the "vague continue" case.
- **R4 (defer): KP2 miss-gate** — dark-launch (log scores a week, calibrate threshold) per the keep-pace plan. Already designed; gated on a week of live data — which only starts accruing after R1.
- **R5 (defer indefinitely): dense/semantic hybrid** — only on observed keyword-miss; the no-API-key constraint (`feedback_no_anthropic_api_key`) + the technical-corpus regime keep sparse the right default (`keep-pace-with-user.md` §6.2).

---

## Q3 — Consolidation (episodic → semantic / queryable work-state)

**The gap:** there is no layer that turns a stream of per-turn episodes into an **evolving, queryable PROJECT/WORK-STATE model.** The "Book 1 done" failure is exactly this — episodes record what happened turn-by-turn, but nothing rolls them up into "pipeline status: Layers 1–5 complete, 6–7 remaining" that a status-claim can be checked against. **This is FBM Tier 3, designed and deferred** (`ws-tier3-orchestration`, deferred 2026-05-21, "re-evaluate after ~1 week" — never done).

**Where it fits (it already has a home in the architecture):**
- **C1 — session-end consolidation hook (FBM T3.1, designed):** at Stop, a Sonnet `claude -p` call (via `claude_print_synthesis_client.py`, the real subscription-routed wrapper, NOT the Anthropic SDK per `feedback_no_anthropic_api_key`) over the N episodes touched this session + their co-citation neighbors → detect contradictions / state-changes, write a consolidation candidate to a review queue. **Build this next after R1** — it is the designed mechanism for the "Book 1 done" class.
- **C2 — work-state projection (NEW, the comprehensive piece the owner is asking for):** a durable, append-not-overwrite **work-state document per active objective** (e.g. `pipeline-state` under each `OBJECTIVES.md` entry's detail-path) that consolidation maintains — current phase, completed steps, remaining steps. This is the *queryable model* a status claim checks against. It composes with KP5's OBJECTIVES.md (objectives already have a `detail-path`; work-state is what lives there). Append-not-overwrite = the "refine without erasing" the owner already specified (`keep-pace-with-user.md` §2 Dimension B).
- **C3 (defer): T3.2 scheduled consolidation** — daily broad-window pass to morning Telegram. Depends on C1 mature.

**Sequencing:** C1 (session-end consolidation) is the keystone; it produces the records C2 (work-state projection) maintains. Both are owner-gated to *surface, not silently rewrite* (the v2 rethink + drift-audit discipline). C1's "~1 week warm-up needs Tier 1+2 live" precondition is **satisfied the moment R1 flips the switch** — the warm-up data starts flowing.

---

## Q4 — Metamemory (claim-vs-stored-state guard)

**The gap:** nothing checks, before the persona asserts something, whether the assertion **contradicts known stored state.** Both 2026-05-29 failures are this class: "no auto-router exists" (contradicted a stored hook) and "Book 1 done" (contradicted stored pipeline state). KP9's draft-gate has a **Layer-C constraint-check** (`draft_gate.py`, seeded with canon rules + sealed rulings) — this is the *exact right seam* but it currently checks against a small hardcoded `SEEDED_CONSTRAINTS` set, not against live stored state.

**This composes directly with the already-captured reconciliation protocol** in `feedback_notes_and_users_are_pointers_evidence_resolves.md` (2026-05-29, TG 12906), which specifies: a stored note and a user statement are **both pointers to truth**; on conflict, **go check the cheapest ground truth** and let it override both; **never store eternal negatives.** The metamemory guard is the *structural enforcement* of that memory rule (the rule itself notes a "memory-system build proposal" with three pieces — this IS that build).

**Concrete build (phased, composes with KP9 + the reconciliation memory):**
- **MM1 — extend KP9 Layer-C into a live claim-vs-state guard.** On the draft-to-send gate, when the draft makes a **checkable assertion** (status claim "X is done", existential "no X exists", state claim), query the unified retrieval surface (R1) for contradicting stored state; on a hit, **inject a "your draft says X; stored state says Y — check ground truth before asserting" steer** (model-facing, never user-facing per KP9's leak discipline). This is the procedure step 1 of the reconciliation memory, mechanized. **High leverage — it sits on a built gate.**
- **MM2 — claim metadata on stored memories** (the reconciliation memory's piece 1): claim-type (observation/inference/decision/preference), verifiability (cheap-checkable / expensive / none), **volatility-by-domain** (system-state = high/short-half-life → re-check on conflict; ethics/goals/ratified-decisions = low → confirm-don't-override). Volatility tells MM1 whether a conflict means "note went stale" (re-check, truth wins) or "user changed their mind" (confirm).
- **MM3 — no-eternal-negatives lint** (the reconciliation memory's piece 3): a stored negative-existential / "impossible" / universal claim is auto-flagged and rewritten to the dated+scoped form (*"search S on DATE over [dirs] did not find X"*). This directly prevents the recurrence of the 2026-05-29 stale-negative failure. A Stop-hook write-side lint.
- **MM4 — calibrated "I should check" signal:** MM1 fires the check; the *calibration* is the volatility table (MM2) + a confidence floor. Surface the reconciliation **visibly** to a non-technical user before acting on a contradicted stored claim ("my notes say X but you're seeing Y — checking") — the reconciliation memory's "non-technical-user safety valve."

---

## RECOMMENDED next-cycle plan (most leverage first)

The single highest-leverage move is **not** building new tiers — it is **turning on what's already built and unifying it.** Most of the comprehensive system exists in-tree, dark.

1. **CYCLE 1 — Activate + unify (R1).** Flip the owner-gated `~/.claude/settings.json` activation (the keep-pace chain + OBJECTIVES.md seed are already bundled into this one step per STATE.md #152) AND wire FBM episode retrieval + the KP1 corpus index into one retrieval surface. **Owner-gated (the activation switch is owner-class), then mostly wiring.** Highest leverage: makes the built comprehensive store actually run, gives every later piece live data, and starts KP2's score-logging clock. *Effort: 30–60 min AI-time once the owner flips the switch; the unify is the larger half.*
2. **CYCLE 2 — Guaranteed-surface + claim guard (R2 + MM1).** Always-inject load-bearing state (active objectives + work-state) bypassing ranking, AND extend KP9 Layer-C into a live claim-vs-stored-state guard. **These two together fix BOTH 2026-05-29 failures** — R2 surfaces the load-bearing fact, MM1 catches the contradicting assertion. *Effort: 60–120 min; both sit on built seams.*
3. **CYCLE 3 — Consolidation keystone (C1 + C2).** Session-end consolidation (FBM T3.1, the deferred tier) + the work-state projection per objective. This is the "comprehensive memory" the owner is asking for — episodic → queryable work-state. Its warm-up precondition is satisfied by Cycle 1. *Effort: multi-component, 2–4 hr.*
4. **CYCLE 4+ — backlog on observed need:** MM2/MM3 (claim metadata + no-eternal-negatives lint), KP2 miss-gate (after a week of logs), the FBM naming sweep (FBE→FBM), memory-architecture M1/M2 (verify MEMORY.md cap state first), T3.2 scheduled consolidation.

**The one-sentence recommendation:** the comprehensive memory system is ~80% built and sitting dark behind an un-flipped switch and a lapsed re-eval — **activate + unify first (Cycle 1), then add the guaranteed-surface + claim-guard that the two failures specifically demand (Cycle 2), then build the deferred consolidation tier (Cycle 3)** — rather than designing anything new from scratch.

---

## F2 — open items + verification owed

1. **UNVERIFIED — MEMORY.md current size.** memory-architecture.md measured 28.7KB/over-cap on 2026-05-28; M1 compression status unknown. Verify: `wc -c ~/.claude/projects/-Users-lukeivers-pos3/memory/MEMORY.md`.
2. **UNVERIFIED — exact current `~/.claude/settings.json` hooks state.** keep-pace-critique.md found it empty 2026-05-28; whether any keep-pace activation has since happened is the load-bearing fact for Cycle 1's scope. Verify: read `~/.claude/settings.json` + plugin `hooks.json`.
3. **Naming drift (FBE vs FBM)** is a real corpus inconsistency (`memory.md`/`public-surface-manifest.md` say FBE; amendments + queue say FBM). Low-severity but it caused this very investigation to start with the name wrong. Recommend a doc-only sweep to FBM.
4. **The "~1 week re-evaluate" trigger on Tier 3 / T2.3 lapsed silently** (deferred 2026-05-21, never re-evaluated by 2026-05-29). This is a `feedback_workaround_masks_rootcause_urgency` instance — recommend the re-eval be a durable task, not a queue comment.

**Derivation line (M5):** this artefact composes with `feedback_notes_and_users_are_pointers_evidence_resolves.md` (Q4 mechanizes its reconciliation protocol), `feedback_information_trust_ordering.md` (the trust-tier frame Q4 enforces), and `feedback_workaround_masks_rootcause_urgency.md` (the lapsed-deferral finding in Q1). Independent of Lens 4.
