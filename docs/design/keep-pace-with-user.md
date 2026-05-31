# loam — Keeping Pace With the User

**Date:** 2026-05-28
**Status:** FINAL design + build plan (folds the adversarial critique; MVP-first, infra-corrected)
**Owner:** Luke Ivers
**Author:** strategy synthesis over the five keep-pace research streams + the storage foundation, reconciled against verified machine state (2026-05-28)
**Strategic frame (owner, verbatim intent):** memory should work like a human's at its best — effectively perfect recall, where the *only* real problem is "ensuring the right things surface at the right times." Tonight's failure was the assistant forgetting / failing-to-surface relevant on-file things *while actively working on a related topic.* That must stop. Beyond surfacing: multiple live sessions must cross-load; the system must learn what the user frequently needs and preload it; it must recover when a request misses the loaded context; it must continuously track the user's *current* objectives (which have gone stale — ZERO on file for the fiction pipeline and the revenue push) without erasing old work; and it must talk to the user as an **abstraction over hard concepts by default** — never making a non-technical user hold file names or mechanism in their head.

**Reads on disk this composes (do NOT re-derive):**
- Storage layer — `memory-architecture.md` (index-vs-detail, the hot cap, M1 compression + M2 budget-guard, hot/warm/cold tiering). STORAGE is solved there.
- The keep-pace streams — `keep-pace-research-{surfacing,cross-session,objectives,abstraction-voice}.md`.
- Context-memory foundation — `l5-context-memory-{scout,deep-1,deep-2,deep-3}.md`.
- **This critique** — `keep-pace-critique.md` (every fix below is folded in; the verified-machine-state corrections are load-bearing).

---

## 0. Verified machine state (Tier-0, 2026-05-28) — read this before trusting any "rides existing infra" claim

The previous draft asserted the design "rides loam's existing hook chain (≥5 live `UserPromptSubmit` hooks incl. `queue_status_inject.py`)." **That was false.** Re-verified directly:

| Claim in prior draft | Verified reality | Consequence |
|---|---|---|
| ≥5 live `UserPromptSubmit` hooks | Global `settings.json` `hooks` = `{}`. Project + local settings: no hooks key. No plugin `hooks.json` anywhere. | **Zero wired hooks except SessionStart.** Hook-wiring is real, first work — see KP0. |
| `queue_status_inject.py` re-reads queue every turn | **Does not exist** anywhere in the tree or `~/.claude`. | The "same proven re-read channel" existence-proof is gone. KP3's cross-session read needs its own n=1 proof. |
| `translation_jargon_check.py` is a live `PreToolUse` hook to extend | Does not exist as a hook. The jargon logic lives in the **`translation-discipline` SKILL** + a deterministic jargon-guard ODD component (`hands-off-lifecycle`). | KP9 = wire a NEW `PreToolUse` hook that reuses that existing jargon logic, not "extend a running hook." |
| `claude_print_client.py` at `framework/memory-system/src/` | Wrong path. Real wrapper: `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/claude_print_synthesis_client.py`. | KP-judge points at the real wrapper (or a thin shared extraction of it). |
| `pos_session_start.py` is a real SessionStart hook | **TRUE.** `framework/orchestrator/scripts/pos_session_start.py`, header confirms SessionStart. Its current job is service-health probing, not context surfacing. | KP7 is a real NEW feature on a real hook — not an extension of existing surfacing. |
| `/goal` could "grow into a persistent objective register" | `/goal` is the `goal-command` SKILL — an autonomous-loop *driver* (halt-on-success). It is NOT a register. | The register is KP5's `OBJECTIVES.md`; `/goal` stays the driver. KP6 = a thin lifecycle SKILL over the register, not a mutation of `/goal`. |
| `OBJECTIVES.md` | Does not exist. | The literal stale-ODD gap. KP5 creates + seeds it. |

**Net:** every per-prompt / draft-gate / journal mechanism is NEW wiring. The primitives all exist (hooks, `claude -p`, FTS5, markdown), so it is all buildable — but the work is **wire + smoke + calibrate**, not "augment a running chain." Confidence ratings below are re-graded against this. The "$0 / 45ms" figures are **claude-mem's measured numbers, not loam's** — loam's are TBD on first build.

---

## 1. The spine — one loop, four views (unchanged direction, the correct synthesis)

The reflexive reading is "four problems → four subsystems." That is wrong, and naming why is the load-bearing move. **All four dimensions read from / write to the same two artefacts:**

| Shared artefact | What it is | Which dimensions touch it |
|---|---|---|
| **The hot index** (bounded, always-loaded, hard cap — `memory-architecture.md` §3.2) | One terse pointer line per hot memory + the active-objective set | surfacing (what's loaded), cross-session (frequency rotates it), objectives (active set IS its rotation key), voice (never leaks to the user) |
| **The per-prompt hook** (`UserPromptSubmit`) + **the draft-to-send gate** (`PreToolUse`) | The read-path (recompute relevance vs the live work) and the write-path guard (catch leaks + contradictions before they reach the user) | ALL FOUR |

**The one-sentence version:** the per-prompt hook surfaces the right memory against the live *work* (not just the typed prompt); the draft gate catches what the model is about to send before it sends it; the journal makes memory cross-session-live; the active-objective set decides what stays hot; the voice gate keeps all of it invisible. Remove any one stage and the rest still function — graceful degradation by design.

**The one critique fix that reshapes the spine (HIGH):** the prior draft keyed retrieval to *the user's typed prompt*. Tonight's failure is the model drifting from on-file context *during its own multi-step work*, where the prompt is a vague "keep going." BM25 on "keep going" surfaces nothing, and the miss-gate stays silent (vague ≠ low-score anomaly). **Two corrections, both folded in below:**
1. **Work-anchored retrieval key.** The hook scores against `prompt + active-objective text + active-subgoal + last-turn topic` — so "continue the batch" inherits "litrpg Ch2 canon" as retrieval terms and the canon rule surfaces. (Same `active_objective_match` signal the draft used only in the *rotation* score — now also on the *read* path.)
2. **The draft-to-send gate is the only place that sees the generated text.** A `UserPromptSubmit` hook fundamentally cannot catch a mid-draft contradiction. So the gate built for *voice* (KP9) is extended to also check the draft against active high-salience constraint-memories (canon rules, sealed rulings). This is where the actual tonight-failure catch lives.

**Honest residual (F2):** KP1+KP2 raise the *probability* the right memory is in context; injecting a pointer ≠ the model attending to it (lost-in-the-middle applies to the pointer too). The draft gate closes more of the gap by checking the text. Neither *guarantees* zero drift. The build improves the failure substantially; it does not claim to eliminate it.

```
 session start →  SessionStart (pos_session_start.py + NEW surface step):
                  last-subgoal + active objectives + likely-next-action, abstraction-voiced
                        │
 user prompt   →  UserPromptSubmit hook (THE read-path core):
                   1. build WORK-ANCHORED key = prompt + active objective + subgoal + last topic   ← fix #1, surfacing #1
                   2. BM25/FTS5 score key vs hot index + cold pointers; inject top-N (≤5) relevant
                   3. MISS-GATE: top score low band → recover-now steer (don't proceed blind)        ← context-miss #5
                   4. (later) read journal partitions fresh, fold by timestamp                        ← cross-session #3
                   5. re-inject abstraction-voice directive keyed to topic depth                      ← voice #8
                   6. (later) bump usage counters for what matched                                    ← frequency #4
                        │
 persona drafts reply
                        │
 draft → send  →  PreToolUse gate (EVERY user-facing surface — Telegram reply, drift proposal,
                  session-start summary):
                   Layer 1: deterministic jargon lint (block on file-name/path/ID/ALLCAPS leak)      ← voice #8 syntactic
                   Layer 2 (later): claude -p register judge — surgical rewrite, conditional, fail-open
                   Layer C: check draft vs active constraint-memories (canon/sealed rulings)          ← TONIGHT-FAILURE catch
                        │
 turn end      →  Stop / SessionEnd: append turn's distilled memory to THIS session's journal
                  partition (O_APPEND, one writer); observe depth signal                              ← cross-session #3, voice learn
                        │
 periodic      →  Compactor + drift audit (SessionStart-fold):
                   - fold journals → durable index + topic files (atomic rename)
                   - rotate hot index by recency × frequency × active-objective-match
                   - drift proxies → SURFACE new/dormant objective proposals (owner-gated)            ← objectives #6,#7
```

---

## 2. Architecture by dimension (condensed — full rationale in the research streams)

**Dimension A — Human-like recall (#1, #5).** Per-prompt retrieval on a **work-anchored key** (the fix above), BM25/FTS5 over the markdown corpus, inject top-N ≤5, silent on no-match, skip trivial prompts, read store fresh each turn, hard-timeout. The **miss-gate** uses the *score gap* (CAG's mechanism ports; its cosine thresholds don't): top score in the low band → emit a high-salience recover-now steer ("this request misses the loaded working set — sweep the topic corpus / objectives / plan-docs for [terms] before answering"). Two granularities: memory-miss (steer) and objective-miss (incremental-refine vs radical-switch reset). The mid-draft contradiction the prompt can't catch is caught by **Layer C of the draft gate.**

**Substrate: BM25/FTS5, NOT embeddings.** Load-bearing and verified: (a) no Anthropic API key (`feedback_no_anthropic_api_key`); (b) corpus regime — 113 highly-technical files (slugs, AC-IDs, exact mechanism names) is exactly where sparse beats dense; (c) claude-mem proves the whole loop on FTS5 (its $0/45ms — not yet loam's); (d) an inverted index updates in single-digit ms on write. Reserve dense/MCP-vector as an optional later hybrid *only on observed keyword-miss* — and KP2's gate is the instrument that tells you if it's ever needed.

**Dimension B — Cross-session live + frequency preload (#3, #4, #7).** One **append-only journal partition per session** (`<workspace>/.scratch/memory-journal/<session_id>.jsonl`); each session is sole writer to its own partition → locks unnecessary by construction. Reading is the merge: a session's hook reads ALL partitions, sorts by timestamp, folds (order-independent because records are immutable — the CRDT property). State evolution = new superseding records, never overwrites — structurally = Luke's "refine without erasing." Liveness is **turn-granular** (session B sees A's writes after A's Stop hook), not instant — named so it is not a surprise. Frequency preload = **ARC (recency × frequency)**: a `usage-counters.json` the hook increments; the compactor keeps the top-N that fit the hot budget, demotes the rest to cold (file stays, index line goes). New memories get a recency-boost so they enter hot immediately. A repeated *miss* JIT-loads + promotes — the system learns shifting scope by demand-paging.

**Dimension C — Continuous objective-tracking (#6, #7) — the rotation key.** `OBJECTIVES.md`, index-vs-detail shaped exactly like MEMORY.md (so it inherits the budget discipline and **must be in M2's audited-surface list**). Each entry: scope-descriptive slug, status (`active`/`dormant`/`retired`), last-touched, cadence, objective text + completion criterion, subgoal state, detail-path. **Named distinct from loam's dev-ODD** (`user-objectives` vs `dev-ODD`) to prevent agent confusion. **The active-objective set IS the hot-index rotation key** (the `w_s` term): a memory tied to an `[active]` objective is hot; `active→dormant` demotes its memories; `dormant→active` promotes back. Retired objectives keep their entry, drop out of hot-load — retire-but-don't-erase. **Drift audit** (observable proxies, no token instrumentation): commission drift (recent activity mapping to no active objective → propose new) and omission drift (active objective past its cadence → propose dormancy). On detection it **surfaces, never silently rewrites** (owner-gated).

**The architecture's own fragility, named (critique §4, folded):** "if the objective model is stale, every retrieval is mis-targeted" applies *to this architecture itself* — the correctness pivot (objectives→rotation) rests on KP8, the weakest, last-built, uncalibrated component. **Mitigation:** start `w_s` (the objective term) **low**; let recency+frequency carry rotation until objectives are proven current and KP8 is calibrated and trusted. Keep all objective status changes fully owner-gated until then.

**Dimension D — Abstraction-voice as structural default (#8).** Advisory reminders fail by *measured* mechanism: instruction influence decays within ~8 rounds (Li et al. COLM 2024), drift is always toward the technical pole, and **self-correction fails for register** — so the check must be *independent* of the generating context, never "remember to talk simply" in the persona's own prompt. Layers: **L1** deterministic jargon lint (file-names/paths/IDs/un-introduced ALLCAPS — block on hit, immune to attention decay); **L2** independent `claude -p` register judge (4-axis: mechanism-leak / unrequested-depth / assumed-context / register; surgical rewrite of the offending span; **fail-OPEN**; conditional on the topic's depth setting); **L3** per-turn re-injection of a terse clean voice directive (a cheap nudge, partially effective — composes, doesn't substitute); **L4** per-topic depth model learned from behavioural signal, debounced ("demonstrably + consistently").

**Two critique fixes folded (MEDIUM):**
1. **ALL user-facing surfaces pass the gate** — not just persona free-text. Drift proposals, the SessionStart summary, any surfaced miss-recovery are *also* Telegram replies and route through L1/L2. The gate is drawn around every outbound surface in the loop diagram.
2. **The system describes its own behaviour in plain language.** Explicit rule: when reporting on its own memory ("I've been keeping your fiction work close at hand"), never internal terms ("ARC-promoted 3 memories," "w_s," "GD-commission"). The system explaining itself is the highest-risk leak surface; this closes it.
3. The gate's own feedback stays model-facing only (stderr/hook-reason) — a "your reply was blocked by the register judge" message is itself a mechanism-leak (the cure becoming the disease).

---

## 3. The build plan — MVP first, then backlog (reward-per-owner-hour ordered)

Re-cut per the critique: **a 5-item MVP that ships the outcome, then a 6-item backlog gated on observed need.** Each item names the Claude primitive (Lens 1), the dimension + Luke-directive, AI-build-time AND time-to-value as distinct lines (duration rubric), and confidence re-graded against the verified infra state.

### MVP — ship these now (the outcome lives here)

| # | Item | Primitive | Dim / # | Build time | Time-to-value | Confidence | Done test |
|---|---|---|---|---|---|---|---|
| **KP0** | **Wire the hook chain into settings + ordering/timeout smoke.** UserPromptSubmit + PreToolUse + a per-turn total-latency budget + fail-open-whole-chain. | `settings.json` / plugin `hooks.json` | infra | 30–50 min | immediate | HIGH (mechanical, but **the FD-inheritance + #15174 risk surface lives here — was invisible in the prior draft**) | A no-op test hook fires on UserPromptSubmit + PreToolUse; chain time-out fails open (turn proceeds); smoke logs per-hook latency. |
| **KP1** | **Work-anchored per-prompt retrieval** — BM25/FTS5 over corpus + hot index; key = prompt + active objective + subgoal + last topic; inject top-N ≤5; silent on no-match; skip trivial; fresh read each turn. | `UserPromptSubmit` (NEW) | A / #1,#3 | 45–75 min | days (logs scores week 1; **KP2 dark-launched until calibrated**) | HIGH (claude-mem proves the pattern; the work-anchor key is the novel part, low-risk) | Prompt mentioning a known on-file topic → correct pointer injected as additionalContext; vague "continue" on litrpg work → canon pointer surfaces via the objective anchor. |
| **KP5** | **`OBJECTIVES.md` register + seed the two real objectives** (fiction pipeline, revenue push) — index/detail; status/cadence/subgoal/detail-path; named distinct from dev-ODD; added to M2's audited set. | file (none) | C / #6,#7 | 15–30 min | immediate | VERY HIGH (tight scope) | File exists, two objectives seeded `active`, both load within the hot budget; KP1's anchor reads it. |
| **KP9** | **Abstraction-voice Layer 1 lint + Layer C constraint-check** — NEW `PreToolUse` hook reusing the `translation-discipline` jargon logic (file-names/paths/IDs/ALLCAPS) AND checking the draft vs active constraint-memories; **routes EVERY user-facing surface.** | `PreToolUse` (NEW, reuses existing jargon module) | D + A / #8,#1 | 30–50 min | immediate | HIGH (deterministic; reuses proven logic — but it's NEW wiring, not "extend a running hook") | A draft containing `/Users/...` or a `.md` filename is blocked; a litrpg draft contradicting a seeded canon rule is flagged before send. |
| **KP7** | **SessionStart objective + last-state surface** — active objectives + last subgoal + likely-next-action, abstraction-voiced, **routed through KP9's gate**; mitigation for #15174 (re-assert via first UserPromptSubmit so a compaction can't evaporate it). | `SessionStart` (`pos_session_start.py`, NEW step) | C+D / #2,#8 | 25–45 min | immediate | HIGH (real hook exists; surfacing is a new job on it) | Session opens with a plain-language "last session you were on X; next likely Y"; survives one compaction via UserPromptSubmit re-assert. |

**MVP total: ~2.5–4.5 build-hours of AI-time + one week of score-logging before KP2 steers.**

### Backlog — ship on observed need (optimizations of a loop that must exist first)

| # | Item | Primitive | Dim / # | Build time | Confidence | Gate to start |
|---|---|---|---|---|---|---|
| **KP2** | **Context-miss gate** (dark-launched in KP1 week 1: log only; steer after threshold calibrated from the observed distribution). | same UserPromptSubmit hook | A / #5,#6 | +20 min | HIGH mechanism / threshold needs in-corpus calibration | KP1 has logged a week of scores. |
| **KP3** | **Session journal + cross-session fold** — append-only partition per session; hook reads all partitions fresh, folds by timestamp; atomic-rename on index rewrite. | Stop/SessionEnd append + UserPromptSubmit read | B / #3 | 40–70 min | HIGH model (git's) / **needs its own n=1 two-session proof** (the cited precedent doesn't exist) | MVP loop observed working single-session. |
| **KP4** | **ARC hotness rotation** — `usage-counters.json`; compactor scores `w_f·freq + w_r·recency + w_s·objective-match` with **`w_s` capped low initially**; demote lowest to cold at cap. | compactor (SessionStart-fold) + per-prompt increment | B+C / #4,#7 | 40–70 min | MEDIUM-HIGH theory / weights need weeks of traffic | `memory-architecture.md` M1+M2 landed; frequency data accruing. |
| **KP6** | **Objective-lifecycle SKILL over the register** — create/replace, pause→dormant, done→retired(keep entry), status. NOT a `/goal` mutation; `/goal` stays the driver. | NEW thin SKILL | C / #6 | 25–45 min | HIGH (Codex `/goal`-register proves the shape) | KP5 exists. |
| **KP10** | **Layer 2 register judge** — independent `claude -p` (real wrapper path), 4-axis rubric, surgical rewrite, conditional, fail-open. | `claude -p` via `claude_print_synthesis_client.py` (Sonnet) | D / #8 | 40–70 min | MEDIUM (judge ~80–90% on style; adds latency to flagged replies) | KP9 + re-injection observed insufficient on semantic leaks. |
| **KP8** | **Objective-drift audit** — commission/omission proxies over git+tasks+touched-files; SURFACE proposals (heavy owner-gating); learn cadence. | SessionStart-fold / cron + proxies | C / #4,#6,#7 | 45–90 min | MEDIUM (proxy heuristics need a tuning pass; **annoyance risk highest — ship last, behind owner-gate**) | Objectives manually curated for a while; `w_s` proven safe. |

### Sequencing rationale (reward-per-owner-hour)
1. **KP0 first** — nothing else runs without it; it's also where the FD/compact bugs bite, so smoke it explicitly.
2. **KP1 + KP5 + KP9 + KP7 = the MVP** — fixes tonight's failure (work-anchored retrieval + the draft-gate constraint-check), closes the zero-objectives gap, protects the user-facing promise day one, and surfaces last-state at session open. All four ride KP0.
3. **KP2** activates once KP1 has logged a week of real scores — the one un-buildable-blind step.
4. **KP3 → KP6 → KP4 → KP10 → KP8** in that order: cross-session liveness, the objective-lifecycle SKILL, frequency rotation (gated on storage M1/M2), the semantic judge, and the drift engine last (loosest, highest annoyance risk).

---

## 4. The single first thing to build

**KP0 + KP1 + KP5, as one MVP slice — and within it, KP1 (work-anchored per-prompt retrieval) is the load-bearing piece.** KP0 is the unavoidable prerequisite (no hooks are wired); KP5 is 15–30 min and gives KP1 its work-anchor to read. KP1 is what actually fixes tonight's failure: it surfaces the right memory against the live *work*, not just the typed prompt. It is also the read-path every later dimension plugs into (cross-session pull-in, objective re-anchor, voice re-injection, frequency bumps all ride this one hook), and it is proven cheap on FTS5 with no embedding API. The draft-gate constraint-check (KP9 Layer C) is its necessary partner for the mid-draft case the prompt-hook structurally can't see — so KP9 ships in the same MVP slice.

---

## 5. How this changes Luke's day-to-day (plain language)

Right now, the assistant can store everything but keeps losing track of the right thing at the right moment — it forgot rules it had already written down while it was working on the exact thing those rules covered. Here is what changes:

- **It stops forgetting mid-task.** Every time you send a message, the assistant quietly re-checks its own notes against what you're actually working on — not just the words you typed, but the project and the step you're in. So if you say "keep going" while it's deep in your fiction chapters, it still pulls up the canon rules for that book. And right before it sends you anything, it double-checks the reply against those rules, so it catches itself about to break one *before* you see it.
- **It admits when it's lost instead of bluffing.** If you ask about something that isn't in what it has loaded, it stops and goes looking first, rather than answering as if it never knew.
- **It knows what you're working on, and keeps up as that shifts.** Your real goals — the fiction pipeline, the revenue push — get written down as living objectives (right now there are none on file, which is half the problem). As your focus moves week to week, it keeps the relevant material close at hand and quietly files the rest where it's safe and findable. Nothing ever gets deleted; old work just steps back until you return to it. If it notices your focus has clearly shifted, it asks you ("your revenue goal hasn't moved in a while — park it for now?") rather than deciding for you.
- **When you open a new session, it tells you where you left off** — in plain English, not file names.
- **It talks to you like a person, by default.** You should never have to hold a filename, a code, or a mechanism in your head. It speaks in plain language unless you've clearly and repeatedly shown you want the technical depth on a given topic — and even when it describes *itself*, it uses plain words, never its own internal jargon.

The honest limit: this makes the assistant far more likely to have the right thing in mind and to catch its own slips — it is a large improvement, not a guarantee of perfection.

---

## 6. Owner-asks (genuine forks only — collapsed from five to two per the critique)

The prior draft front-loaded five forks, three of which are decisions about backlog items four steps deep (compactor cadence, drift autonomy, judge gating) — premature, and a one-question-at-a-time violation. Those are **deferred to their build item**, not asked now. Two genuine forks remain, and they're sequenced one-at-a-time by what the MVP needs first.

1. **(needed for KP5, the MVP) `OBJECTIVES.md` scope — user-level or per-workspace?** Your two objectives span workspaces (fiction lives in the litrpg workspace; revenue is cross-cutting). Recommendation: a **user-level** `~/.claude/.../OBJECTIVES.md` for top-level life/work objectives, with per-workspace files allowed for project subgoals that ladder up (mirrors the CLAUDE.md hierarchy). *Signals: cross-workspace unification (favours user-level) vs per-project load cost (favours workspace). Reasonable people could prefer strict per-workspace — surfacing.*

2. **(needed before KP10, post-MVP) substrate confirmation — stay sparse, or plan a dense hybrid?** Recommendation: **sparse-first (BM25/FTS5), defer dense indefinitely.** Constraint (no API key), corpus regime (113 technical files), and cheap reversibility all align, and KP2's miss-gate is the instrument that will tell you if dense is ever warranted. This is barely a fork — the call is already made; flagging only because the substrate is load-bearing and you may want to confirm. *Signals: constraint (hard), corpus-regime (strong-for-sparse), reversibility (cheap to add later). Decide only if you disagree with sparse-first.*

**Not forks — decisions deferred to their build item (named so they're not lost):** compactor cadence (KP3 — lean SessionStart-fold), drift-audit autonomy (KP8 — propose-and-surface, owner-ratifies every status change), Layer-2 judge gating policy (KP10 — pre-filter-then-judge, fail-open, log to tune). **Verify-first RISKS (not forks):** a 5-line version-probe for `InstructionsLoaded` + the #15174 SessionStart-compact behaviour, and the n=1 two-session journal test before trusting KP3 — all live inside KP0's smoke or their own build item.

---

## 7. Lens coverage

- **Lens 1:** every mechanism rides native primitives (`UserPromptSubmit`, `PreToolUse`, `Stop`/`SessionEnd`, `SessionStart`, the existing `pos_session_start.py`, the `translation-discipline` jargon module, the `goal-command` SKILL, `claude_print_synthesis_client.py` for the judge). No retrieval engine re-implemented — BM25/FTS5 is a library, the journal is git's model, ARC is textbook. **Corrected:** these are NEW wirings of existing primitives, not extensions of a running chain.
- **Lens 2:** the loop reduces the user's translation burden (right context surfaces; objectives stay current; never holds a file name) and adds to the persona's toolkit (work-anchored recall, the draft-gate catch, cross-session liveness, objective-tracking, the voice gate). Maps to `memory-architecture.md` P1/P2/P3.
- **Lens 3:** every item states an observable outcome with a done-test; ACs authored at build time, method the builder's call.
- **Lens 4:** KP5/KP9/KP1 high-confidence → tight; KP0/KP3 high-but-verify → tight-with-a-probe; KP2/KP4/KP10 medium (thresholds/weights/judge) → calibrate-then-tighten; KP8 loosest → owner-gated, last.
- **Lens 5:** eleven independently-shippable items, MVP/backlog partitioned; KP8 IS the `needs_fresh_start` drift-signal applied to objectives; KP10 uses `EVAL_DIMENSIONS` named-axis scoring.
- **Lens 6:** §6 surfaces two genuine forks with signals named; three premature forks demoted to their build item — the multi-signal resolution applied to the scope question itself.
- **Lens 7:** the over-claimed tonight-failure fix corrected and the residual named; the false-infrastructure claims corrected at Tier-0; the architecture's own objectives→rotation fragility flagged with the `w_s`-capped-low mitigation; every imported tuning constant marked calibrate-don't-import.

## 8. Source trust-tier summary

Inherits the per-stream bibliographies. Load-bearing primaries: CAG (arXiv 2411.16133), claude-mem FTS5 (operator, code-backed — its $0/45ms is **claude-mem's, not loam's**), Lost-in-the-Middle (2307.03172); POSIX `O_APPEND` + git-as-CRDT + ARC via PostgreSQL/ZFS; Zylos goal-drift, Yang et al. intent-grounding (2601.10702), OpenAI Codex `/goal`; Li et al. COLM 2024 (2402.10962 — drift within 8 rounds), CEFR drift (2505.08351 — self-correction fails for register), PONTE (2603.06485), LLM-Rubric (2501.00274). **Tier-0 verified locally (2026-05-28):** global+project `settings.json` hooks empty; `queue_status_inject.py` and `translation_jargon_check.py` do not exist; `pos_session_start.py` and `claude_print_synthesis_client.py` real (latter at the corrected path); `OBJECTIVES.md` absent; `/goal` is a driver SKILL not a register; `memory-architecture.md` present. **Do not import a tuning number** — KP2 threshold, KP4 weights, KP8 proxies, KP4 `w_s` cap all calibrate on loam's own corpus and real prompts.
