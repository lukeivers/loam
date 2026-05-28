# loam Memory Architecture

**Date:** 2026-05-28
**Status:** design (read + design only; no implementation in this pass)
**Owner:** Luke Ivers
**Author:** strategy synthesis over the L5 context-memory research wave + the live loam memory implementation
**Strategic frame (owner, TG 12831):** *"Memory is such a core part of loam's pitch. We HAVE to get that right. Getting memory right is the KEY to making this work transparently to non-tech users."* Memory is treated here as a **first-class capability**, not a hygiene fix. The live MEMORY.md truncation is a *symptom* of an architecture that does not yet scale — this doc is the architecture; the fixes fall out of it as instances.

---

## 0. The spine in five sentences

loam's memory is **three physically distinct stores serving one promise** — that the persona remembers the user's context across sessions so the user never re-explains themselves. The promise breaks at the **load boundary**: any store with an unwatched byte/line budget silently drops its tail past the cap (the live MEMORY.md is 28.7KB against a Claude-native 25KB cap — the last third of the corpus index is functionally absent right now, and the *same silent-budget-truncation class* hits skill-description loading per the L2 research). The fix is not manual trimming but a **structural index-vs-detail discipline with an automatic guard**: a thin, budget-bounded, machine-checked *index* surface that always loads, pointing at unbounded *detail* files retrieved just-in-time when relevant. The tiering (hot index / warm topic-files / cold graph) maps each kind of memory to the store whose load-behaviour matches its access pattern, and a small set of Claude-native hooks (an InstructionsLoaded budget-audit, a PreCompact pointer-injector, a UserPromptSubmit re-injector) makes the whole thing observable and compaction-surviving without re-implementing any retrieval engine. The non-tech-user payoff is the three properties this architecture exists to guarantee: **transparent continuity** (context carries forward), **trust** (the user can see their context is held and nothing silently vanished), and **graceful scaling** (the corpus grows for years without a load-day where it quietly stops working).

---

## 1. Current state (Tier-0, verified)

loam's memory promise is served today by **three physically distinct stores**, often conflated under one word. The conflation is the root of the architecture gap.

| # | Store | What it holds | Who writes it | Where it lives | Load behaviour |
|---|---|---|---|---|---|
| **S1** | **CLAUDE.md hierarchy** | Static rules, design lenses, output conventions | the user (hand-authored) | `~/.claude/CLAUDE.md`, `<repo>/CLAUDE.md`, nested | Loaded every session; root file **re-read after `/compact`** (survives) |
| **S2** | **Claude-native auto-memory (FBM corpus)** | Accumulated learnings — the `feedback_*.md` discipline rules + the `MEMORY.md` index | Claude Code autonomously + user-prompted ("remember that…") | `~/.claude/projects/<project>/memory/` | **MEMORY.md: first 200 lines OR 25KB, whichever first.** Topic files: read on demand by the model |
| **S3** | **loam `memory-system`** (graphiti) — **DESIGN-ASPIRATIONAL, NOT CURRENTLY LIVE** (see note below) | Per-turn episodic facts + an entity/relationship knowledge graph | _(designed: the primary-persona consumer, per turn via `memory_consumer.py` — currently a Protocol shim with no live backend)_ | _(designed: `<workspace>/workspace/data/memory-system/kuzu_db` + MCP — **no `kuzu_db` exists on disk**)_ | _(designed: retrieved per-turn via `search(group_ids=[slug])`, not auto-loaded — **the search path is not wired today**)_ |

> **S3 is design-aspirational, not currently live (Tier-0 verified 2026-05-28).** `python3 -c "import graphiti_core"` → `ModuleNotFoundError`; no `kuzu_db` directory exists anywhere on disk; `memory_consumer.py` is a Protocol shim whose own docstring states it "never imports memory-system source; the Protocol is sufficient" — there is no live graph backend behind it. **loam's operative memory reality today is file-based only: S1 (CLAUDE.md hierarchy) + S2 (`feedback_*.md` corpus + MEMORY.md index).** The S3 rows/claims in this doc (this table, §3.5, the §6 Lens-1 "already exists and is sealed" note) describe the *designed* shape, not the *running* shape. The keep-pace-with-user MVP's KP1 retrieval therefore runs over the **markdown corpus** (BM25/FTS5), not the graph. (RF-1 correction per `docs/plans/keep-pace-with-user-mvp.md` §10.)

**Tier-0 measurements (this machine, 2026-05-28):**
- `~/.claude/projects/-Users-lukeivers-pos3/memory/MEMORY.md` = **28,774 bytes / 102 lines**. Because it is 28.7KB it blows the **25KB byte cap** (it is under the 200-line cap — so the *byte* budget is the binding one). The longest index entries are **~1000 chars each** — roughly 5× the ~200-char guideline the file's own warning cites.
- Topic corpus: **113 `feedback_*.md` files, 936KB total.** The index is the only auto-loaded surface; the 936KB of detail is read on demand.
- The system-reminder in the live session states it plainly: *"MEMORY.md is 27.8KB (limit: 24.4KB) — index entries are too long. Only part of it was loaded."* The tail of the index — including recently-captured discipline rules — **never enters context.**

**Where each store's machinery lives (Tier-0):**
- S3 consumer: `framework/primary-persona/src/loam/primary_persona/memory_consumer.py` — **a Protocol shim, NOT a live retrieval path** (Tier-0 2026-05-28: it "never imports memory-system source; the Protocol is sufficient"; no graph backend is wired). The *designed* contract (registers a turn-level retrieval contributor, fire-and-forget per-turn episode writes via `claude -p` extraction, fail-closed, soft cap `MEMORY_RETRIEVAL_CHAR_CAP = 1600`) is aspirational — it does not run today because there is no `kuzu_db`/graphiti backend behind the Protocol.
- S3 extraction client: `ClaudePrintLLMClient` (amendment #8) — subscription-only `claude -p`, never the Anthropic API (`feedback_no_anthropic_api_key`).
- S3 inspector: `framework/tools/loam-memory-inspect/` — read-only kuzu_db size/health probe.
- S1/corpus session-start loader: `framework/hands-off-lifecycle/hooks/corpus_inline_session_start.py` — inlines `CLAUDE.md` + `VALUE_PROPOSITION.md` + `STATE.md` into `additionalContext` at session start (DEV-MODE-gated).
- Prior triage: `docs/plans/research/memory-system-coexistence-triage-research.md` (the S2-vs-S3 coexistence question, already worked).

### 1.1 Failure modes (named + evidenced)

**FM-1 — Silent budget truncation at the load boundary (LIVE, the trigger).**
MEMORY.md exceeds the Claude-native 25KB cap and the last third silently does not load. **The cap is Claude-Code-native (a subagent system-prompt-composition behaviour), NOT a loam-enforced number** — verified: no loam code sets 24.4KB/25KB; it is upstream `code.claude.com/docs/en/memory` behaviour. This matters for the fix: loam cannot raise the cap, only live within it.

**FM-2 — The same truncation class hits skill descriptions (LATENT, same root).**
Per the L2 research, skill descriptions load against a `SLASH_COMMAND_TOOL_CHAR_BUDGET`; past it, descriptions silently drop and the skill stops auto-firing. This is **the same failure class as FM-1** — load-bearing context dropped past an unwatched budget — in a second store. A point-fix on MEMORY.md leaves this one live. The architecture's guard must be store-general.

**FM-3 — Memory rules are context, not enforcement (the binding limit on S1/S2).**
Anthropic's own docs: *"Claude treats them as context, not enforced configuration. To block an action regardless of what Claude decides, use a PreToolUse hook."* GitHub #53900 is the field proof — a self-written memory rule violated within minutes. **A memory rule is a strong nudge, never a guardrail.** Anything that must hold goes to a hook (loam already does this for the behavioural-violation cluster).

**FM-4 — Compaction decay of decision-state.**
Long autonomous runs compact; the five always-lost categories (exact numbers, hard constraints, decision *why*, cross-task deps, implicit preferences) are exactly what loam's discipline rules encode — but they live in files that aren't fed into the *summarizer* at compaction time. loam writes state continuously (a strength), but has no PreCompact hook re-pinning the pointers.

**FM-5 — Index bloat from over-rich entries (the proximate cause of FM-1).**
The index entries are not merely numerous (102), they are *individually fat* — full composes-with chains, provenance, Telegram IDs, AI-time bands inlined into what should be one-line pointers. The detail belongs in the topic file the entry already points at. This is the lever: **the fix is shorter entries, not fewer memories.**

---

## 2. What "getting memory right" means for a non-tech user

Memory is a Lens-2 capability: it is the **continuity substrate of the translation layer.** A non-technical user does not know what a context window, a compaction event, or a 25KB cap is — and must never need to. The promise has three properties, and each maps to an architecture requirement.

**P1 — Transparent continuity.** The persona remembers the user's context across sessions so the user never re-explains themselves. *"You told me last week you're allergic to shellfish"* must survive a session boundary, a compaction, and a year of corpus growth. → Requires: durable stores (have — S1/S2 file-based) + retrieval that surfaces the right memory when relevant (**NOT yet — S3 graphiti is design-aspirational, not live; the keep-pace MVP's KP1 builds this over the markdown corpus**) + a load path that does not silently drop the memory (FM-1: broken).

**P2 — Trust (the user can believe their context is held).** A non-tech user cannot audit a knowledge graph. Trust is built two ways: the persona *demonstrably* recalls (continuity in action), and the system *never silently loses* what the user was told it would keep. **Silent truncation is the single worst trust failure** — the user told the system to remember something, it said it would, and it quietly didn't load it. The user has no way to know. → Requires: a structural guard that makes silent loss *impossible or at least loud* (the InstructionsLoaded budget-audit, §4).

**P3 — Graceful scaling over years.** The corpus only grows. A non-tech user will never run a "memory cleanup." The architecture must degrade gracefully — old memories move to colder tiers, the hot index stays bounded *automatically*, and there is never a "load day" where the system quietly stops working because the corpus crossed a cap. → Requires: tiering + an *automatic* index-budget guard (not manual trimming), §3–4.

> **F2 / Lens-2 framing:** every item in §4 is justified by which of P1/P2/P3 it serves. A memory feature that serves none of these three is not a memory feature for the user — it is plumbing, and should be judged on harness-test terms only.

---

## 3. The architecture

### 3.1 The store map (assign each memory kind to the store whose load-behaviour fits its access pattern)

The architecture does **not** unify the three stores into one. It assigns each *kind* of memory to the store whose physics fit, and makes the boundaries explicit so nothing is duplicated or orphaned.

| Memory kind | Store | Why this store | Access pattern |
|---|---|---|---|
| Static rules / design lenses / preferences-as-rules | **S1 CLAUDE.md** | Survives compaction (re-read from disk); user-authored | Always-on |
| Discipline learnings / corrections / "remember that…" | **S2 FBM index + topic files** | Auto-written, index auto-loads, detail JIT | Index always-on; detail on relevance |
| Per-turn episodic facts + entity/relationship graph | **S3 graphiti** | Rich relational retrieval; per-turn write | Retrieved on prompt-relevance |
| Per-persona craft heuristics (editor catch-classes etc.) | **S4 subagent `memory:`** (proposed) | Native, per-agent, capped, version-controlled | Auto-injected into that persona only |

**S4 is new and deliberately scoped.** Subagent `memory: project` frontmatter (v2.1.33) gives each named persona a private, capped, auto-injected knowledge store. This is for **private per-persona craft heuristics** — NOT shared facts. The shared/authoritative cross-persona fact store stays the canon-store (for the LitRPG product) or S3 (for the workspace). **Do not conflate S4 with the shared stores** (L5-deep-2, F2): subagent memory is siloed per-agent by design. And **do not give the independent judge an S4 store** — persistent memory would let it anchor on prior verdicts and destroy the fresh-eyes property that makes it valuable.

### 3.2 Tiering — hot / warm / cold

The load-boundary problem (FM-1) is fundamentally a tiering problem: **everything was crammed into the one hot tier that auto-loads.** The fix is to keep the hot tier bounded and let warmth fall off.

- **Hot (always-loaded, hard byte-bounded):** the MEMORY.md *index* — one terse pointer line per memory. Plus the S1 CLAUDE.md always-load set. This tier MUST stay under the Claude-native 25KB cap *automatically*. It is the table of contents, not the content.
- **Warm (retrieved just-in-time):** the `feedback_*.md` topic files + S3 graph. Read when a turn's relevance signal points at them. Anthropic's JIT-retrieval strategy: *keep lightweight identifiers, load data at runtime.* The 936KB of detail lives here and costs zero context until needed.
- **Cold (archival):** superseded/absorbed memories. Already partly present — several index entries are marked "STUBBED instance of …" or "absorbed by the frame." Cold memories keep their file (audit trail) but **drop out of the hot index** entirely; they are reachable by explicit search, not by always-load.

The promotion/demotion rule: a memory is hot only while its one-line pointer earns its place in a bounded index. When the index approaches budget, the **lowest-value pointers demote to cold** (the file stays; the index line goes). This is the automatic scaling guard P3 needs.

### 3.3 The index-vs-detail split (the load-bearing structural decision)

This is the spine. **MEMORY.md is an index, not a document.** Each entry is a *pointer*: a stable slug, a one-line "what + when to consult," and the topic-file path. Detail — the full rule, the composes-with chain, the provenance, the worked example — lives in the topic file the pointer names. The model reads the topic file JIT when the index line tells it the rule is relevant.

This is exactly the pattern the Claude-native subagent `memory:` feature *enforces by design* (the doc: "MEMORY.md stays the 200-line index, topic files hold the depth, with instructions to curate if it exceeds the cap"). loam hand-built this pattern for the primary persona but **without the cap-forcing function**, so the index grew rich and overflowed. The architecture adopts the native discipline: index entries are pointers, capped; depth is in the named file.

**The proximate fix for FM-1/FM-5 falls out of this directly:** the current index entries are ~1000 chars because they inlined the detail. Compressing each to a true one-line pointer (<200 chars: slug + trigger + path) brings 102 fat entries well under 25KB *without losing a single memory* — the detail was always in the topic file; the index was just redundantly carrying it.

### 3.4 The automatic budget guard (NOT manual trimming)

P2 (trust) and P3 (scaling) require that the index *cannot silently exceed budget*. Manual trimming is what failed — it depends on someone noticing. The guard is structural and store-general (also covers FM-2, skill descriptions):

- **An `InstructionsLoaded` hook** (a Claude-native event that "logs exactly which instruction files are loaded, when, and why") audits, on every session start, the byte/line size of every budget-bounded load surface — MEMORY.md against 25KB/200-line, the skill-description set against its char budget — and **emits a loud warning into context when any surface is within ~10% of its cap or already over.** This converts FM-1's *silent* truncation into a *visible* one: the persona (and through it the user) learns "your memory index is at 96% — N entries at risk" instead of silently losing the tail. It is the diagnostic that would have caught the current breach automatically.
- The guard does not *enforce* trimming (a hook cannot rewrite the file mid-session safely), but it makes the breach impossible to miss, which is the trust-load-bearing property. Trimming-on-warning becomes a cheap, prompted, owner-or-persona action with full visibility — the opposite of today's silent loss.

> This is the **single highest-leverage structural change** in the doc: it generalises the one-off MEMORY.md fix into a permanent, store-general guard against the entire silent-budget-truncation failure *class* (FM-1 + FM-2 + any future budgeted surface). It is the difference between fixing the symptom and fixing the architecture.

### 3.5 Retrieval — surface the right memory, don't load everything

The hot index is bounded precisely *because* retrieval handles relevance. Two retrieval paths, already present, compose:
- **S2 topic-file JIT:** the index line tells the model "when X, consult `feedback_X.md`"; the model reads it on the X-signal. This is the cheap, deterministic path.
- **S3 graphiti search (DESIGN-ASPIRATIONAL — NOT LIVE):** the *designed* shape is that `memory_consumer.py` fires a per-turn `search(group_ids=[slug])` and renders the top-N facts/episodes under the 1600-char cap, fail-closed — the rich relational path for episodic continuity (P1). **Tier-0 (2026-05-28): this does NOT run today** — `memory_consumer.py` is a Protocol shim with no graph backend (no `graphiti_core`, no `kuzu_db`). The live relevance-retrieval path that the keep-pace MVP builds (KP1) runs over the **markdown corpus** instead.

The two are complements, not competitors (the coexistence triage already established this): S2 holds *discipline rules* (how the persona should behave), S3 holds *episodic facts* (what happened / what the user said). Neither is the load surface that's truncating — the bug is purely in the S2 *index* tier.

### 3.6 Summarization / compaction-into-memory + compaction-survival

FM-4 mitigation, composing on what loam already has:
- **PreCompact hook** injects *pointers* (not bodies — the 10KB cap is tight) into the summarizer: active principle footer names, git branch + last commits, the `workstream-queue.yaml` in-flight roster, active plan-doc paths. Rule-1 "Historical Context at TOP" so compactions compound rather than decay; Rule-7 "Decision/Why/Rejected" mirroring loam's ODD register.
- **UserPromptSubmit re-injection** (NOT SessionStart-compact, which is bugged #15174 — verify on the installed version first) re-pins "compaction occurred; N agents live; re-read X" post-compaction. loam already injects reliably here (`queue_status_inject.py`).
- loam's structural strength: state already lives in plan-docs/FIDRAFT/queue *by methodology*, so PreCompact reads-and-injects rather than needing to make Claude *write* state at compaction time (which #43733 confirms it cannot). The "no SESSION.md before compaction" failure that bites others does not bite loam.

### 3.7 FBM (feedback-memory) integration + cross-session durability

The `feedback_*.md` corpus IS loam's FBM. It is already durable (on disk, survives sessions) and already index+detail-shaped. The architecture changes nothing about *how FBM is written* — it changes how the *index* loads (§3.3) and adds the *guard* (§3.4). The procedural rule already in the corpus ("every new feedback memory carries a derivation/relationship line") is preserved; the architecture just says that line lives in the **topic file**, and the index entry is the terse pointer to it. Cross-session durability is already solved by "files are the only memory"; the gap was never durability, it was the *load boundary*.

---

## 4. Prioritized implementation plan (reward-per-owner-hour)

Each item names the Claude primitive it leans on (Lens 1) and the user-property it serves (Lens 2). Effort is AI-time per the rubric. **This plan re-uses the A1/A3/A5/C3 items already ranked in `PLAN.md` and binds them to the architecture above** — it is not a new backlog, it is the memory slice of the existing one, now with an architectural spine.

| # | Fix | Architecture instance | Primitive | Serves | Effort | Confidence |
|---|---|---|---|---|---|---|
| **M1** | **Compress the MEMORY.md index to one-line pointers** (<200 chars each: slug + trigger + path). No memory deleted — detail already in topic files. Brings 28.7KB under 25KB. | §3.3 index-vs-detail; resolves FM-1/FM-5 | (none — file edit) | P1, P2 | 10–20 min | very high — tight scope |
| **M2** | **`InstructionsLoaded` budget-audit hook** — warn loudly when any budgeted load surface (MEMORY.md, skill descriptions) is ≥~90% of cap or over. | §3.4 automatic guard; resolves FM-1 + FM-2 as a class | InstructionsLoaded hook | P2, P3 | 20–40 min | high — primitive is documented; verify event fires on installed version |
| **M3** | **PreCompact pointer-inject + UserPromptSubmit re-inject** — re-pin principle footer + git + queue roster + plan-doc paths through compaction. | §3.6 compaction-survival; mitigates FM-4 | PreCompact + UserPromptSubmit (route around #15174) | P1 | 30–55 min | high on PreCompact; verify #15174 state first |
| **M4** | **Directive skill descriptions + char-budget audit** — convert passive→imperative; verify total < budget. Pairs with M2's skill-budget audit. | §3.4 (the skill-description half of the guard) | SKILL frontmatter | P3 (FM-2) | trivial–30 min | high |
| **M5** | **Subagent `memory: project` pilot on one craft persona** (copy-editor — git log proves hand-fed catch-classes). NOT the judge. | §3.1 S4 tier | subagent `memory:` frontmatter | (product quality; harness-test) | 20–40 min | medium on quality lift → n=1 probe |

**Sequencing:** M1 first (unblocks the reliability of everything — the live breach). M2 second (makes the class never silently recur — the architectural win). M3/M4 next (compaction + skill budget). M5 is the longest-horizon, lowest-confidence, product-scoped pilot.

**M1 + M2 together are the architecture in miniature:** M1 fixes today's instance; M2 makes the instance-class structurally impossible to suffer silently again. Shipping M1 without M2 fixes the symptom and re-arms the trap.

---

## 5. F2 — open forks, risks, owner-asks

**Surfacing these per Lens 7; each is flagged owner-ask where reasonable people would weigh signals differently.**

1. **OWNER-ASK — Index-compression policy: where does the detail go?** M1 compresses ~1000-char entries to <200-char pointers. The detail (composes-with chains, provenance, AI-time bands) is *already* in the `feedback_*.md` topic files in most cases — but a few index entries carry detail that may NOT be fully duplicated in their topic file (e.g. the full-body "INSTANCE … full body kept" entries). **The fork:** mechanical compression risks dropping detail that lives *only* in the index. The safe path is a per-entry verify (is the detail in the topic file? if not, move it there first, then compress the index line) — slower but lossless. The fast path (compress all, accept that a few full-body entries lose their inline detail) is faster but lossy. *Recommendation: lossless per-entry verify — it's a memory-integrity operation and P2/trust is the whole point. ~20 min vs ~10 min; the 10 min saved is not worth a lost memory.* **Reasonable people could prefer the fast path; surfacing.**

2. **OWNER-ASK — Does M2's `InstructionsLoaded` event fire on the installed Claude Code version, and does it see context?** The event is documented but loam doesn't use it; the L3 research flags it Tier-1-documented but unverified-on-this-version. **The fork:** if the event doesn't fire or can't emit into context on 2.1.x, M2's audit must move to a different surface (SessionStart emission, or a standalone `loam-memory-inspect`-style CLI run at session start). *Recommendation: a 5-line version-probe before building M2 — same probe discipline PLAN.md §5 already mandates for #15174/#37210/#46829. Don't build around an assumed event capability.*

3. **RISK (not a fork) — M2 audits but cannot auto-trim.** A hook can warn but should not rewrite MEMORY.md mid-session (race + the file is Claude-Code-managed). So the guard makes breaches *loud*, not *impossible*. The residual is: the persona/owner must act on the warning. This is acceptable — loud-and-prompted is a categorical improvement over silent — but it is not full automation. A future "trim-on-warning" routine could close it; out of scope here.

4. **RISK — S2 vs S3 boundary drift.** The architecture keeps discipline-rules in S2 and episodic-facts in S3. If the persona starts writing discipline rules into S3 (or facts into S2), the boundary blurs and retrieval quality drops. The coexistence triage already addressed this; the architecture inherits its boundary. No new work, but worth a periodic audit (the `loam-memory-inspect` tool is the natural home).

5. **OWNER-ASK — Should the MEMORY.md cap be treated as 25KB or the 24.4KB the system-reminder cites?** The reminder says 24.4KB; the docs say 25KB; the live file is 28.7KB so both agree it's over. **Minor, but:** the index-compression target should aim well under the lower number (e.g. budget to ~20KB, leaving headroom for years of P3 growth before the next compression). *Recommendation: target ~20KB hot-index budget, ~60% of cap, matching the proactive-compaction discipline (act at 60%, not at the cap). No owner decision strictly needed — flagging the headroom rationale.*

6. **SECURITY GAP (named, unscoped) — instruction-surface integrity.** No loam memory covers memory-poisoning of CLAUDE.md/MEMORY.md/skills (anyone who can write a "trusted" instruction surface can persistently reframe behaviour). This is a genuine gap the research flagged (Cisco persistent-memory-compromise vein). Out of scope for *this* doc (which is about scaling, not security), but it lives on the same surfaces this doc governs, so it belongs in the same future work-stream. **Surfacing, not resolving.**

---

## 6. Lens coverage (completeness check)

- **Lens 1 (Claude-leverage):** the architecture composes on native primitives — the MEMORY.md/topic-file convention (S2), subagent `memory:` (S4), InstructionsLoaded (M2), PreCompact/UserPromptSubmit (M3), skill frontmatter (M4). It re-implements *no* retrieval engine. (Note — corrected per RF-1: the S3 graphiti store is **design-aspirational, not currently live**; there is no `graphiti_core`/`kuzu_db` backend on disk today. The §1 table claim that it "already exists and is sealed" describes the designed shape, not a running store. loam's operative memory is file-based — S1 + S2.)
- **Lens 2 (harness + persona value):** every fix maps to P1/P2/P3 (§2) — the non-tech-user continuity/trust/scaling promise. Memory is framed as the translation-layer's continuity substrate, not plumbing.
- **Lens 3 (ODD):** this is a design doc; ACs are authored at implementation time per item. Each M-item states an observable outcome (index under cap; audit warns at threshold; pointers re-survive compaction) without prescribing method.
- **Lens 4 (scope↔confidence):** M1 is tight (very-high confidence, narrow). M2/M3 carry verify-then-build forks (medium confidence on the primitive's installed-version behaviour → looser scope, probe first). M5 is loosest (no controlled study → n=1 architectural probe).
- **Lens 5 (swarming):** the plan decomposes into 5 independently-shippable items each with a tighter AC than "fix memory." M1/M2/M3/M4 are parallel-safe (different files/hooks); M5 is product-scoped and separate.
- **Lens 6 (conflict resolution):** the F2 forks (§5) are surfaced with signals named (P2-trust vs speed for #1; verify-vs-assume for #2) rather than silently resolved.
- **Lens 7 (ruthless feedback):** failure modes named with evidence (§1.1); forks and risks surfaced (§5); the security gap named even though out of scope.
