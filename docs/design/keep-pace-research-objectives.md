# Keep Pace — Continuous Objective Tracking (research + design)

**Date:** 2026-05-28
**Status:** research + design (no implementation this pass)
**Owner:** Luke Ivers
**Dimension:** CONTINUOUS OBJECTIVE TRACKING — modeling a user's evolving objectives as first-class, continuously-refined state; objective-drift detection; tying the active memory working-set to current objectives; rotation-by-scope under a hard size cap; retire-but-don't-erase.
**Builds on:** `memory-architecture.md` (storage layer — index/detail split, the 25KB hot-index cap, the M1/M2 budget guard). That doc solved STORAGE. This doc's frontier is the part it explicitly did not cover: keeping the *objective model* current and tying the *loaded working-set* to it.

**The failure this fixes (Luke, verbatim intent #6/#7):** loam's objective-tracking ("its ODD") has gone stale. There are likely ZERO objectives on file for Luke's actual current work (a fiction-writing pipeline; a revenue/consulting push). The system is not continuously understanding objectives, adapting as they shift, or noting new ones. The fix must continuously refine objectives as needs shift WITHOUT erasing old work, and rotate things in/out of the always-loaded index (hard size cap) so loaded memory ties to the CURRENT scope.

---

## 0. Bottom line in five sentences

The frontier problem is not storing objectives — loam already stores everything in files — it is (a) keeping a small, first-class **objective model** continuously synced to what the user is actually working on this week, and (b) using that model to drive **which memories load** into the bounded hot index, so the loaded working-set always matches current scope. The external research converges hard on one architecture: objectives are **durable markdown documents re-read at every major decision boundary**, drift is **detected with two named, measurable signals** (drift-by-commission and drift-by-omission), and the active context is **curated as an explicit action** (add / edit / archive / promote) rather than left to passive accumulation. Two shipped reference points anchor this as buildable, not theoretical: **OpenAI Codex's persistent `/goal` objectives** (thread-level objective state with active/paused/budget-limited status, progress tracked across turn/tool/file boundaries, survives token exhaustion via graceful wrap-up) and the **Memory-as-Action** paper (the agent performs add/edit/delete/promote on its own working set under a size budget, scored by objective-relevance). For loam specifically, all of this composes onto primitives it already owns — a new `OBJECTIVES.md` first-class file, a `/goal`-style slash command, the existing UserPromptSubmit hook (which already injects `workstream-queue.yaml` state) extended to do **intent-match detection + context-miss recovery**, a SessionStart objective-surface, and a periodic (cron/Stop-hook) **objective-drift audit** that proposes rotations against the hard index cap. The non-technical-user payoff is that the assistant always opens already knowing what Luke cares about *this week*, notices out loud when his focus has shifted, and never makes him name a file or a mechanism to get there.

---

## 1. Why objective-tracking is a *distinct* problem from storage

`memory-architecture.md` treats memory as durable facts/rules surfaced on relevance. Objectives are different in three load-bearing ways, and conflating them is why loam's ODD went stale:

1. **Objectives are the relevance signal, not a thing that gets surfaced by relevance.** A fact ("Aaron is at Priya's pod") is retrieved *because* the current turn is about it. An objective ("ship the fiction pipeline to Layer-7 this month") is the thing that *determines* which facts are relevant in the first place. The intent-grounding research (Yang et al., arXiv:2601.10702) makes this its central claim: memory retrieval must be **filtered/ranked by current intent**, not by generic semantic similarity to the query. If the objective model is stale, *every* retrieval is mis-targeted — which is exactly Luke's tonight-failure (forgetting relevant things while actively working on related topics).
2. **Objectives drift continuously and silently.** Facts are added discretely ("remember X"). Objectives shift by erosion — last week's revenue push quietly becomes this week's fiction sprint, and nothing fires an event. The goal-drift research (Zylos, 2026-04) found *every evaluated model* eventually drifts, with degradation correlating to context length. Drift needs **active detection**, not passive storage.
3. **Objectives have a temporal lifecycle (active → dormant → retired) that must not be destructive.** Luke's directive #6/#7: refine WITHOUT erasing old work. A retired objective is not deleted — it is moved out of the active/loaded set but stays recoverable. This is the same hot/warm/cold tiering `memory-architecture.md` §3.2 defined, applied to *objectives* as the tiering key.

**The synthesis:** the objective model is the **rotation key** for the hot-index cap. `memory-architecture.md` left open *what decides* which memories earn a hot-index slot. The answer this doc supplies: **the active objective set decides.** Memories tied to an active objective are hot; memories tied to a dormant/retired objective demote to warm/cold automatically. Rotation-by-scope = rotation-by-active-objective.

---

## 2. External research — mechanisms found (sourced, trust-tiered)

### 2.1 Goal-drift detection: two measurable signals (Tier-2, strongest actionable finding)
Source: [Goal Persistence and Goal Drift in Long-Horizon AI Agents — Zylos Research, 2026-04-03](https://zylos.ai/research/2026-04-03-goal-persistence-drift-long-horizon-ai-agents)

The keystone finding. Drift is decomposed into two named, separately-measurable components:
- **GD_actions (drift by commission):** ratio of goal-aligned investments to total budget, relative to a baseline — *are actions still pointed at the right objective?*
- **GD_inaction (drift by omission):** failure to take a required next action after completing an intermediate phase — *passive abandonment, the goal silently dropped.*

Finding: **all evaluated models eventually drifted**; degradation tracks context length (longer context → more pattern-matching, less goal-fidelity). No fixed numeric threshold given — they recommend monitoring **token usage / context saturation** as the proxy trigger and re-anchoring before fidelity degrades.

**Re-anchoring patterns (directly portable):**
- **Durable goal documents** — objectives + completion criteria as persistent markdown at task inception; re-read **at every major decision point**.
- **Goal re-anchoring at context boundaries** — when context approaches saturation, an explicit step: *state current goal → confirm against the durable doc → record any constraint violations observed.*
- **Subgoal state small enough to stay in every context window**; completed subgoals marked in the durable doc.
- **Semantic consolidation, not replacement** (via Mem0-style extraction of goal statements + decisions + constraints) so prior-session objectives stay retrievable — **cumulative goal evolution, not overwrite.** This is the literature's name for Luke's "refine without erasing."
- **Planner/Executor split + explicit subgoal injection** — a persistent planner owns goal state; on delegation, inject the explicit goal+constraints; on ingest, **filter sub-agent output for goal-relevant content before merging** to prevent inherited drift. (loam already does scope-only dispatch; the new part is the *ingest filter*.)

### 2.2 Intent as first-class state + context-miss detection (Tier-2)
Source: [Grounding Agent Memory in Contextual Intent — Yang et al., arXiv:2601.10702](https://arxiv.org/pdf/2601.10702)

- **Intent is an explicit, persistent, structured component of agent state** — not implicit in query embeddings. It evolves as the conversation progresses; lets the agent distinguish queries belonging to different goals within one session.
- **Retrieval is decoupled from generic semantic match** — memories are filtered/ranked by relevance to the *current intent*, prioritizing what advances the stated objective even when superficially-similar content exists elsewhere.
- **Context-miss detection fires on three conditions:** (1) the current query *contradicts* the loaded intent; (2) information needed for the intent is *absent* from retrieved memories; (3) the conversation shifts to a *fundamentally different* objective. **Recovery = re-evaluate the intent model + refresh the retrieval strategy.** This is the precise mechanism Luke's directive #5 asks for ("when the user asks something NOT aligned with loaded context, run an analysis to load the right things AT THAT MOMENT — don't keep going as if context doesn't exist").
- **Incremental-refine vs radical-switch distinction:** the framework tracks whether the objective is shifting incrementally (a sub-goal refining existing intent) or radically changing (a context switch requiring an intent-model reset). Different responses: refine vs reset.

### 2.3 Memory-as-Action: curation as an explicit operation under budget (Tier-2)
Source: [Memory as Action — arXiv:2510.12635](https://arxiv.org/pdf/2510.12635)

- Treats **memory management itself as an action the agent performs**, not static storage. Four operations: **Add / Edit / Delete / Promote** (promote = elevate an archived item back to active).
- Maintains **active working memory (within a size budget)** vs **archived memory (retrieved when needed)** — same hot/cold split as loam, but with explicit cycle operations.
- Decision strategy: **relevance assessment relative to ongoing objectives + budget constraint + objective alignment + rotation** between active/archived by current utility.

**This is the operational vocabulary for loam's rotation-under-cap.** The hot-index isn't trimmed by a passive heuristic; it's curated by named actions whose key is objective-alignment.

### 2.4 OpenAI Codex `/goal` — a SHIPPED persistent-objective system (Tier-2, the buildable proof)
Source: [OpenAI Codex goal: the new long-horizon mode — howdoiuseai.com, 2026-05-05](https://www.howdoiuseai.com/blog/2026-05-05-openai-codex-goal-the-new-long-horizon-mode-for)

The single best "this is buildable on a CLI agent" reference. Mechanics:
- **Objective state at thread level:** objective text + status (`active` | `paused` | `budget-limited`) + token-usage count + elapsed-time.
- **`goal_id` with stale-update protection** to prevent race conditions on simultaneous updates — *directly relevant to Luke's directive #3 (multiple simultaneous sessions cross-loading).*
- **Survives interruption / token exhaustion:** on budget exhaustion enters budget-limited state and does a **graceful wrap-up** — summarize progress, note what's left, save state to resume.
- **Progress tracked across multiple boundaries:** turn completions, tool calls, file mutations, interrupts, resume events. Detects looping-without-tool-calls and suppresses repeated continuations.
- **CLI surface:** `/goal <objective>` create/replace, `/goal pause`, `/goal resume`, `/goal clear`.

Note: loam **already has a `/goal` skill** (named in the handsoff-loop SKILL description: "/goal driving the keep-going leg"). The Codex model is the design target to grow loam's `/goal` from a keep-going driver into a *persistent objective register*.

### 2.5 PKM relevance-surfacing + periodic review (Tier-3, design vocabulary)
Sources: [InfraNodus — graph-based PKM](https://infranodus.com/docs/personal-knowledge-management); [GAIA — PKM](https://heygaia.io/learn/personal-knowledge-management); [dsebastien — PKM at scale](https://www.dsebastien.net/personal-knowledge-management-at-scale-analyzing-8-000-notes-and-64-000-links/)

- **Node-ranking surfaces influential notes in the current context**; structural-gap analysis flags clusters not yet connected ("those gaps become your next research questions"). → loam analog: rank objectives/memories by edges into the *active* objective; flag objectives with no recent activity (dormancy candidates).
- **Daily/weekly/monthly review cascade** extracts daily notes into denser dedicated notes over time. → loam analog: a periodic objective-drift audit is the "weekly review" mechanized — the natural home for rotation decisions and the frequency-learning Luke wants (directive #4).
- **Frequency-driven preloading** (Luke #4) maps to spaced-repetition's core: frequently/recently accessed items surface more, stale ones surface less ([Spaced repetition — Wikipedia](https://en.wikipedia.org/wiki/Spaced_repetition)). The objective-access log IS the frequency signal.

### 2.6 Forgetting under relevance/efficiency balance (Tier-2, mechanism confirmed, formula not extractable)
Source: [Novel Memory Forgetting Techniques for Autonomous AI Agents — arXiv:2604.02280](https://arxiv.org/pdf/2604.02280)

Confirms the principle (continuous accumulation increases retrieval noise → a principled forgetting mechanism balancing relevance and efficiency is required) but the PDF stream did not yield the specific scoring formula/decay function. **Treat as directional support for "retire-but-don't-erase," not as a citable algorithm.** F2: do not invent a formula and attribute it here.

---

## 3. The design — objective model as first-class state

### 3.1 `OBJECTIVES.md` — the durable objective register (the new first-class file)

A single durable markdown file per workspace (e.g. `<workspace>/OBJECTIVES.md`, or the user-scope `~/.claude/.../OBJECTIVES.md` for cross-project goals). Index-vs-detail shaped exactly like MEMORY.md so it inherits the same budget discipline. Each objective is a terse entry:

```
## OBJ-FICTION-PIPELINE  [active]  last-touched: 2026-05-28  cadence: daily
Ship the LitRPG fiction pipeline through Layer-7. Completion: connection-gate green on a full chapter batch.
Subgoals: [done] L4 chapters exist · [active] L6/6.5/7 build · [pending] audio pass
detail: workspace/products/litrpg-writer/docs/pipeline-objective.md

## OBJ-REVENUE-PUSH  [dormant]  last-touched: 2026-05-20  cadence: weekly
Revenue/consulting push — prioritized portfolio. Completion: first paid engagement booked.
detail: workspace/strategy/revenue/portfolio-plan.md
```

Fields (minimal, Codex-aligned §2.4): **id** (scope-descriptive slug, never version-packed — matches the AC-ID convention), **status** (`active`/`dormant`/`retired`), **last-touched timestamp**, **cadence** (how often this objective is expected to see activity — the frequency-learning anchor, directive #4), **objective text + completion criterion** (the durable-doc re-anchor target, §2.1), **subgoal state** (small enough to stay in every context window, §2.1), **detail path** (warm-tier, JIT). Retired objectives keep their entry but drop out of the hot-load set (move to an `OBJECTIVES-archive.md` or a `[retired]` section below the load cap) — **retire-but-don't-erase** (directive #6).

**Why a file, not the graph (S3):** objectives must be *human-auditable and editable by Luke directly* (P2-trust), survive compaction (root-file re-read), and load deterministically at session start. The S3 graph holds episodic facts *tied to* objectives; the objective register itself is a durable doc. (Composes with `memory-architecture.md` §3.1.)

### 3.2 The active-objective set is the rotation key for the hot index

This is the load-bearing connection to `memory-architecture.md`. The hot MEMORY.md index has a hard cap. **What earns a hot slot = relevance to an `[active]` objective.** Rotation rule:
- A memory/fact whose topic edges into an `[active]` objective → eligible for the hot index.
- When an objective transitions `active → dormant`, its tied memories demote (warm); when `dormant → active` (Luke returns to it), they promote back. This is Memory-as-Action's **promote/archive** (§2.3) keyed on objective status.
- The hot index thus *automatically tracks current scope* — Luke's directive #7 ("rotate things in/out of the always-loaded index so loaded memory ties to current work"). No manual curation; the objective-status transitions drive it.

### 3.3 Continuous drift detection (the always-on lens)

Adapt GD_actions / GD_inaction (§2.1) to loam's file-based, turn-based reality — no token-budget instrumentation needed, use observable proxies:
- **Commission proxy:** does recent activity (git commits, task updates, files touched, dispatch subjects) align with the `[active]` objective set? A run of activity that maps to *no* active objective = commission-drift signal → **propose a new objective** (directive #6: note new ones).
- **Omission proxy:** an `[active]` objective whose `last-touched` is older than its declared `cadence` = omission-drift signal → **propose dormancy** (the objective was silently dropped). This is exactly Luke's stale-ODD failure made detectable.
- **Trigger:** not token-saturation (loam's proxy is weaker there) but (a) **session start** (cheap, always) and (b) a **periodic audit** (Stop-hook or cron). On detection, the system does not silently rewrite — it **surfaces** (F2/Lens-7): "Your activity this week is all fiction-pipeline; the revenue-push objective hasn't moved in 8 days — mark it dormant? And I see a recurring activity (consulting outreach) with no objective on file — add one?" Owner-gated rotation (P2-trust; never silent precedent).

### 3.4 Context-miss recovery at the turn boundary (directive #5)

Extend the existing `UserPromptSubmit` hook (loam already injects `workstream-queue.yaml` here via `queue_status_inject.py` — Tier-0 verified in deep-1 §3). Add an **intent-match check** per Yang et al. (§2.2):
1. On each user prompt, cheaply assess: does this prompt align with any `[active]` objective (or the session's loaded objective)?
2. **Match** → proceed (inject the matched objective's subgoal state as the re-anchor, §2.1).
3. **Miss** (contradicts loaded intent / needed info absent / different objective) → **do NOT proceed as if context doesn't exist** (the explicit failure Luke named). Instead inject a re-orient instruction: "this prompt does not match the loaded objective set; before answering, identify the relevant objective (or that none exists) and load its detail/tied-memories." This is the at-that-moment analysis directive #5 demands.
4. Distinguish **incremental refine** (sub-goal of an active objective → refine, keep context) vs **radical switch** (different objective → reset the loaded working-set to the new objective's tied memories). (§2.2 distinction.)

The cheap implementation of "does this prompt align": the hook can do a lightweight keyword/edge check against objective slugs+text deterministically; the *expensive* semantic version is a `claude -p` sub-call (subscription-only per `feedback_no_anthropic_api_key`) reserved for ambiguous cases — same JIT discipline as the optional PreCompact witness in deep-1 §2.3.

### 3.5 Session-start objective surface (directive #2)

SessionStart hook (loam already runs `pos_session_start.py` + `corpus_inline_session_start.py`) gains an objective-surface: inject the `[active]` objective set + each active objective's *last subgoal touched* + the single most-likely-next-action. This is the "what was being worked last session + its state" Luke wants at start — but framed as objectives, not raw queue items. Necessary-but-not-sufficient (Luke's own words): it seeds the session; drift-detection (§3.3) and context-miss recovery (§3.4) handle the rest.

### 3.6 Cross-session objective sync (directive #3)

Multiple live sessions must cross-load objective updates as they're written. The Codex `goal_id` + stale-update protection (§2.4) is the reference. loam's file-based path:
- `OBJECTIVES.md` is the single source of truth on disk; any session writing an objective update writes the file (with an mtime/`goal_id` version stamp).
- Other live sessions pick it up at their **next UserPromptSubmit** (the hook re-reads `OBJECTIVES.md`, same way `queue_status_inject.py` re-reads the queue YAML every turn — Tier-0 verified). So cross-session propagation is already the proven mechanism; it just needs the objective file added to the re-read set.
- **Race protection:** the stale-update guard = compare on-disk mtime/version before writing; if a peer session advanced it, merge rather than overwrite (append-and-reconcile, never clobber — protects retire-don't-erase across sessions too).

### 3.7 Frequency-learning preload (directive #4)

The `cadence` field + a lightweight access log (which objectives' detail files get opened, which slugs match prompts) is the frequency signal. The periodic audit (§3.3) updates `cadence` from observed access: an objective Luke touches daily gets `cadence: daily` and its tied memories stay hot; one touched monthly relaxes. Spaced-repetition logic (§2.5): recently/frequently-accessed → preload; stale → demote. This is learned, not hand-set — the audit proposes cadence changes alongside dormancy proposals.

### 3.8 Abstraction-voice (directive #8 — load-bearing for the whole value prop)

Everything above is mechanism. The user-facing contract: **the assistant talks about objectives in plain language, never file names or mechanism.** "Last session you were deep in the fiction pipeline — the Layer-6 build. Want to pick that up, or is today the revenue work?" NOT "OBJ-FICTION-PIPELINE is active per OBJECTIVES.md line 3, tied memories rotated into the hot index." The objective register, the drift signals, the rotation — all invisible. This is a Lens-2 requirement and it composes with the existing `feedback_translate_outbound_too` rule (prose-first, no slugs/paths/IDs in outbound). The mechanism is for the assistant; the abstraction is for Luke. Go technical only when asked or on demonstrated-depth topics (Luke wants harness internals; he does not want to hold objective-register schema).

---

## 4. Buildable plan on the Claude-Code harness (Lens-1 — compose, don't re-implement)

Each item names the primitive it leans on and the directive it serves. Effort in AI-time per the rubric. Ranked by reward/owner-hour. **All compose onto primitives loam already runs (verified in deep-1 §3 / deep-3 §3).**

| # | Item | Primitive leaned on | Directive | Effort | Confidence |
|---|---|---|---|---|---|
| **O1** | **`OBJECTIVES.md` register + seed Luke's two real objectives** (fiction-pipeline, revenue-push) — the file that currently has zero entries. Index/detail shaped; `[active]`/`[dormant]`/`[retired]` + cadence + subgoal + detail-path. | file (none) | #6, #7 | 15–30 min | very high — tight scope |
| **O2** | **Grow the existing `/goal` skill into a persistent objective register** — `/goal <text>` create/replace, `/goal pause→dormant`, `/goal done→retired (keep entry)`, `/goal status`. Codex-model (§2.4). | SKILL (existing `/goal`) | #6 | 30–60 min | high — Codex proves the shape |
| **O3** | **SessionStart objective-surface** — extend `pos_session_start.py` to inject active-objective set + last-subgoal + likely-next-action, abstraction-voiced. | SessionStart hook (existing) | #2, #8 | 20–40 min | high |
| **O4** | **UserPromptSubmit intent-match + context-miss recovery** — extend `queue_status_inject.py` (or sibling) to add `OBJECTIVES.md` to the re-read set, do the deterministic match-check, inject re-orient on miss. Cross-session sync falls out (same re-read path). | UserPromptSubmit hook (existing, Tier-0 proven) | #3, #5 | 30–55 min | high on the re-read; medium on the match-quality heuristic |
| **O5** | **Periodic objective-drift audit** — Stop-hook or cron: GD-commission/omission proxies over git+tasks+touched-files; propose new objectives, dormancy, cadence updates; SURFACE (owner-gated), never silent. Drives rotation against the hot-index cap. | Stop hook / Cron + the §3.3 proxies | #4, #6, #7 | 45–90 min | medium — the proxy heuristics need a tuning pass |
| **O6** | **Objective→memory rotation binding** — wire active-objective status as the hot-index promotion key (Memory-as-Action promote/archive, §3.2). Depends on `memory-architecture.md` M1/M2 landing first. | the M2 budget-guard hook | #7 | 30–60 min | medium — sequenced after M2 |

**Sequencing:** O1 first (the file that doesn't exist is the literal "zero objectives on file" gap — highest leverage, near-zero risk). O2+O3 next (the user-facing surfaces — Luke sees value immediately: session opens knowing his objectives, `/goal` captures shifts). O4 (the context-miss fix — directive #5, the tonight-failure). O5 (the always-on keep-pace engine — the hardest, most-tuning, highest-ceiling). O6 last (binds objectives to the storage layer; gated on `memory-architecture.md`'s M2).

**O1+O5 are the architecture in miniature:** O1 gives objectives a home; O5 keeps that home continuously synced to reality. O1 without O5 re-creates the stale-ODD failure in a new file.

---

## 5. Risks + open forks (F2 / Lens-7)

1. **OWNER-ASK — drift-audit autonomy: propose-and-surface vs auto-rotate?** O5 detects dormancy/new-objectives. The safe path (recommended): always *surface* a proposal, owner ratifies before any status change or rotation (P2-trust; silent objective-rewrite is the worst trust failure — the system deciding Luke "doesn't care about revenue anymore" without asking). The fast path: auto-mark-dormant on cadence-miss, surface only retirement. *Recommendation: propose-and-surface for status changes; auto-update only the soft `cadence`/`last-touched` bookkeeping. Reasonable people could want more autonomy here once trust is established — surfacing.*

2. **RISK — intent-match heuristic quality (O4).** A cheap deterministic keyword/edge match will have false-misses (real continuation flagged as context-miss → annoying re-orient) and false-matches (genuine switch proceeds on stale context → the tonight-failure persists). Mitigation: tune the threshold conservatively (prefer a false-miss "let me check which objective this is" over a false-match silent-wrong-context), and escalate ambiguous cases to a `claude -p` semantic check. This is the medium-confidence item; it needs an n≥3 tuning pass on real prompts, not n=1 (this is a *statistical* quality question, not an architectural yes/no — per `feedback_n1_architectural_vs_n3_statistical`).

3. **RISK — objective register bloat (same class as MEMORY.md).** `OBJECTIVES.md` is a budgeted load surface — it inherits FM-1. The M2 `InstructionsLoaded` budget-guard from `memory-architecture.md` must audit it too. Retired objectives must actually leave the hot section (archive file), or the register grows unbounded like MEMORY.md did. Composes directly with M2 — name `OBJECTIVES.md` in M2's audited-surface list.

4. **RISK — cross-session write race (O4/§3.6).** Two live sessions both updating `OBJECTIVES.md`. The Codex `goal_id` stale-guard is the reference but loam is file-based, not a DB. Mitigation: mtime/version-stamp compare-before-write + append-reconcile (never clobber). Lower-probability for a single user across a few sessions, but retire-don't-erase makes clobbering especially costly (a clobbered retire could erase an objective). Worth the guard from day one.

5. **OWNER-ASK — where does `OBJECTIVES.md` live: workspace-scope or user-scope?** Luke's two current objectives span different workspaces (fiction = litrpg-writer; revenue = strategy). A per-workspace file fragments them; a single user-scope file unifies them but loads in every project. *Recommendation: user-scope `~/.claude/.../OBJECTIVES.md` for the top-level life/work objectives (fiction, revenue), with workspace `OBJECTIVES.md` allowed for project-local subgoals that ladder up. Matches the CLAUDE.md hierarchy pattern. Reasonable people could prefer strict per-workspace — surfacing.*

6. **RISK — objective model vs loam's ODD/VALUE_PROPOSITION (named, scoped-out here).** loam's *dev* methodology already has ODD (objective-driven dev) for building loam itself. This `OBJECTIVES.md` is for the *user's* work objectives, a different layer. They must not be conflated: dev-ODD governs how loam is built; user-OBJECTIVES governs what the user is doing. The naming collision ("objective" in both) is a real confusion risk for future agents — flagging so the implementation names them distinctly (e.g. `user-objectives` vs `dev-ODD`). Out of scope to resolve here; surfacing.

---

## 6. How this composes with `memory-architecture.md`

- **Storage doc solved:** index/detail split, the 25KB hot cap, the M1 compression + M2 budget-guard, hot/warm/cold tiering, S1–S4 store map.
- **This doc supplies the missing rotation key:** *what decides hot membership* = active-objective relevance (§3.2). The storage doc left the tiering mechanism without a driver; the objective model is the driver.
- **Shared primitives:** both lean on UserPromptSubmit (re-read + inject), SessionStart (surface), the M2 InstructionsLoaded guard (now audits `OBJECTIVES.md` too).
- **Sequencing across both docs:** storage M1 (compress) → M2 (guard) must land before this doc's O6 (objective→memory binding). O1–O5 are independent of the storage work and can proceed in parallel.

---

## 7. Sources (trust-tiered)

- **Tier-2 (operator/research, plausible, primary mechanism extracted):**
  - [Goal Persistence and Goal Drift in Long-Horizon AI Agents — Zylos, 2026-04-03](https://zylos.ai/research/2026-04-03-goal-persistence-drift-long-horizon-ai-agents) — GD_actions/GD_inaction, durable-doc re-anchoring, semantic-consolidation-not-replacement. **Keystone.**
  - [Grounding Agent Memory in Contextual Intent — Yang et al., arXiv:2601.10702](https://arxiv.org/pdf/2601.10702) — intent as first-class state, retrieval decoupled from semantic match, context-miss detection (3 conditions), incremental-vs-radical distinction.
  - [Memory as Action — arXiv:2510.12635](https://arxiv.org/pdf/2510.12635) — add/edit/delete/promote as agent actions, active-vs-archived under budget, objective-aligned rotation.
  - [OpenAI Codex goal — howdoiuseai.com, 2026-05-05](https://www.howdoiuseai.com/blog/2026-05-05-openai-codex-goal-the-new-long-horizon-mode-for) — shipped persistent-objective model: thread-level state, status, goal_id stale-guard, graceful wrap-up, /goal CLI surface.
  - [Novel Memory Forgetting Techniques for Autonomous AI Agents — arXiv:2604.02280](https://arxiv.org/pdf/2604.02280) — forgetting-for-relevance/efficiency principle (formula not extractable; directional only).
- **Tier-3 (design vocabulary, not adoption):**
  - [InfraNodus PKM](https://infranodus.com/docs/personal-knowledge-management); [GAIA PKM](https://heygaia.io/learn/personal-knowledge-management); [dsebastien — PKM at scale](https://www.dsebastien.net/personal-knowledge-management-at-scale-analyzing-8-000-notes-and-64-000-links/) — node-ranking-by-context, daily/weekly review cascade, frequency surfacing.
  - [Spaced repetition — Wikipedia](https://en.wikipedia.org/wiki/Spaced_repetition) — frequency/recency-driven surfacing basis for cadence-learning.
- **Tier-0 (verified locally, via deep-1/deep-2/deep-3 + this pass):** loam's existing `/goal` skill (handsoff-loop SKILL desc); `queue_status_inject.py` re-reads `workstream-queue.yaml` every UserPromptSubmit; `pos_session_start.py` + `corpus_inline_session_start.py` on SessionStart; no `OBJECTIVES.md` exists; the no-Anthropic-API-key constraint forces `claude -p` for any semantic check.
