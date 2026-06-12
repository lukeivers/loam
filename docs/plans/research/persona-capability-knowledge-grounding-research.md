# Research — grounding the primary persona in Claude Code + harness capability knowledge

**Authored:** 2026-04-26.
**Extended:** 2026-04-26 (two-class corpus + currency mechanism — see §2.6, §7bis, and amendment δ/ε in §7).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Driver:** owner directive 2026-04-26 — the persona's prime expression of the translation-layer value prop is its ability to leverage Claude Code + the harness intelligently. When the persona plans how to take action on almost anything, it should actively stop and think about how to best leverage both. The strawman: seed graphiti with capability knowledge so it gets retrieved when contextually relevant. This research evaluates that strawman and competing/complementary designs.
**Subsequent owner lock 2026-04-26:** capability knowledge is **two distinct content classes** (Anthropic-canonical reference + community-accumulated best-practices wisdom) and **both must stay current** — Anthropic ships features faster than training cuts; best-practices evolve continuously. The hybrid design must address both content classes and a currency mechanism for each. §2.6, §7bis, and the program-shape update in §7 carry the extension.
**Spec ladder:** Idea 1 / Step 1 of `FUTURE_IDEAS.md` (the durable Claude-capability map) — pre-existing on the future-work register; this research recommends sequencing it ahead of Idea 1's Steps 2–4 because step 1's deliverable is now the active blocker on the persona's day-1 effectiveness. v1.0 spec ladder: "non-tech users" objective — every interactive session starts with the primary persona present *and effective*; effectiveness collapses if the persona doesn't know what's in the toolkit. The currency mechanism (§7bis) ladders directly to Knowledge-accrual (R3 process-of-arrival capture, R5 4-dimensional temporal model, R6 supersession) — both classes accrue and supersede; the spec already names the underlying primitives.

---

## TL;DR — one-page summary for owner ruling

**Recommended design (one-line headline):** **Hybrid-with-prompt-as-spine, two-class corpus, dual-channel currency.** The persona's prompt.md carries a tight "leverage rule + capability index" spine (always-on, ~1.5 k chars); a new MCP knowledge-server exposes the full capability corpus — partitioned into **Class A (Anthropic-canonical reference)** and **Class B (community-accumulated best-practices wisdom)** — as on-demand resources Claude fetches when the spine names them; **Class A stays current via a scheduled deterministic-projection refresh**; **Class B accrues continuously via a hybrid of community-survey scope + internal Stop-hook learning-extraction + user-supplied capture**; graphiti seeding is **rejected for capability docs** as wrong-shape and continues to do interaction memory; **Class B's user-and-internal accrual writes through graphiti's same Stop-hook learning-extraction primitive** (Stream A) but with a `source_description="capability-best-practice"` tag so it lands in a separate retrieval bucket — no parallel-memory chaos.

**Four named decisions for owner ruling** (D-1, D-2, D-3 carried from the original research; D-4 is new):

1. **Decision D-1 — Capability knowledge substrate.** Recommend: **MCP knowledge-server + prompt.md spine.** Reject: graphiti seeding as the primary substrate. Alternative: pure-prompt.md (rejected as too small) or pure-additionalContext (rejected as bloat against the 10 k cap).
2. **Decision D-2 — Sequencing.** Recommend: **four amendments — α prompt-spine + corpus seed; β MCP knowledge-server (two-class-aware schema from day one); δ Class A currency (deterministic projection refresh); γ optional dynamic contributor.** Class B accrual rides as features inside β + δ rather than a standalone amendment ε (see §7bis for rationale and the alternative ε if owner prefers the split). Alternative: one combined amendment (rejected — bigger, slower, blocks the cheap win); separate ε for Class B accrual (viable but heavier).
3. **Decision D-3 — "Leverage rule" enforcement shape.** Recommend: **declarative rule in prompt.md** (always-on personality content) **+ a session-start contributor surfacing today's contextually-relevant capability index** (structural). Alternative: pure declarative (rejected — lens 1 violation; the rule without an index doesn't help when the persona's training-cut knowledge is stale).
4. **Decision D-4 (new) — Class B accrual channels.** Recommend: **hybrid of three channels** — (a) periodic community-survey scope dispatched as a background agent (web-search + summarise + propose corpus delta, owner-gate-reviewed before merge), (b) internal Stop-hook learning-extraction with `source_description="capability-best-practice"` so observed-effective patterns from real pos-v2 sessions accrue automatically into the Class B bucket, (c) user-driven capture ("Eve, remember I should always use background agents for research" → ingested as a Class B episode by the same Stop-hook path). Alternative: any single channel alone (rejected — single-source bias; Luke's preference is "structural over advisory"; multiple channels is structural diversity). The owner-gate on (a) is anti-deskilling pairing per Luke's preference.

**Four halt-conditions surfaced for owner attention** (none structurally blocking, all design-level):

- H-α: **The capability corpus is large but bounded** (~30–60 documents at full coverage; <600 k chars for Class A; Class B starts smaller and accrues). It fits inside an MCP server's resources surface comfortably; it does NOT fit inside a single additionalContext payload. Cost-realism for graphiti seeding: 50 docs × ~113 s/episode = 95 min one-shot for a worse retrieval surface. Strawman has a real cost-vs-value problem.
- H-β: **The "leverage rule" landing is partially personality and partially structural** — the structural half (a session-start contributor that names what's relevant given today's `prompt`-shape) is the design lift; the declarative half is one paragraph in prompt.md. Both halves are inside the persona-layer + workspace-bootstrap fence.
- H-γ: **Idea 1 / Step 4 (refresh automation) lands as amendment δ.** The MCP server's resources are a refreshable corpus; the refresh primitive (Step 4) consumes the corpus as input. The currency-mechanism extension makes δ a first-class amendment in the program rather than out-of-scope future work. δ scope is bounded to **Class A** projection (deterministic, structural); Class B accrual is fundamentally different in shape and rides on β + Stop-hook composition (see §7bis).
- H-δ (new): **Class B's internal-accrual channel composes on the *exact same primitive* as Stream A's interaction-memory writes** — `source_description` is the only structural difference. This is favourable (zero new substrate; Luke's "no parallel-memory chaos" preference is honoured) but requires the β knowledge-server to query graphiti for `source_description="capability-best-practice"` episodes when assembling the Class B retrieval surface, OR mirror them into the knowledge-server's sqlite-FTS5 index. Recommendation: **mirror at write time** (β's design admits a Stop-hook subscriber that intercepts capability-best-practice episodes and writes them to the knowledge-server's resource path) — keeps retrieval consistent across both classes, avoids cross-substrate query joins at read time. This is a β method-level decision; the owner does not need to rule on the mirroring approach unless cost analysis flips.

---

## 1. Problem framing

The persona's core function (per `VALUE_PROPOSITION.md`): translate user natural-language intent into AI-effective execution. The translation depends on the persona knowing what execution paths are available — Claude Code primitives, harness primitives, operational patterns. Today the persona's knowledge of those primitives is whatever the model's training distribution carries, plus whatever happens to be in `prompt.md` or in retrieved memory. This is fragile:

- Claude Code ships features faster than model training-cut updates. The persona working from a 6-month-old training cut doesn't know about features like `/loop`, `/schedule`, the new `claude-api` skill, or the new Stop-hook semantics — even though they're documented as of today.
- pos-v2 ships harness primitives weekly during the rebuild. The persona working from a non-current state doesn't know what's been sealed: scope-of-work primitive, orchestrator's pyee subscription surface, cost-governance budget-line API, memory-system's MCP tools. Lens 1 reads ("what Claude capability does this lean on or extend?") fail when the lens's input set is stale.
- Operational patterns ("when to use background agents", "when to use `/loop`") are *between* primitives — they're advice the persona gives on top of the primitives, and they need to be authored once and consulted on every plan.

The owner's framing names this exactly: "*when the persona plans how to take action on almost anything, it should actively stop and think about how to best leverage both Claude Code and the harness.*" That's the prime expression of the translation-layer value prop. Today the persona doesn't have the surface it needs to express it consistently.

---

## 2. Question 1 — Capability corpus inventory

The first thing to establish is the realistic upper bound. The corpus the persona needs to know about partitions into four content surfaces.

### 2.1 Claude Code feature surface (~25–30 docs at full coverage)

From the deferred-tools list visible at session start + the `/help`-discoverable feature surface + the documented hook & MCP & subagent ecosystem:

- **Slash commands.** `/init`, `/loop`, `/schedule`, `/compact`, `/clear`, `/config`, `/permissions`, `/effort`, `/model`, `/feedback`, `/statusline`, `/agents`, `/help`, `/install-github-app`, `/login`, `/logout`, `/release-notes`, plus user-installed skills (which surface as `/<skill-name>` on first reference).
- **Hook events.** `SessionStart`, `UserPromptSubmit`, `UserPromptExpansion`, `PreToolUse`, `PostToolUse`, `Notification`, `PreCompact`, `Stop`, `SubagentStop`, `SessionEnd`. Each has a documented input envelope, exit-code semantics, stdout disposition, timeout. The hooks docs (~1 doc) plus per-event short notes (~10) plus the merge-session-start / merge-stop / settings-merging conventions pos-v2 has authored on top (~2 internal docs) ≈ 13 docs.
- **MCP servers.** Server registration via `.mcp.json` or `~/.claude/mcp.json`; tool surface; resource surface; prompt surface; transport types (stdio, streamable-HTTP, SSE-deprecated). The host-side configuration docs (~1) plus the server-authoring docs (~2) plus pos-v2's own MCP servers (memory-graphiti, telegram-plugin, future knowledge-server) ≈ 6 docs.
- **Subagents / Agent tool / Task dispatch.** The Agent tool's contract (`/agents` + `Task`/general-purpose); the subagent-file format (`.claude/agents/*.md` with frontmatter `name/description/model`); the in-flight `EnterWorktree`/`ExitWorktree` parallel-tree primitive; the `Monitor` event-stream primitive; `TaskStop` cancellation. ≈ 5 docs.
- **Skills.** The skills marketplace; `update-config`, `claude-api`, `loop`, `schedule`, `simplify`, `init`, `review`, `security-review`, `keybindings-help`, `fewer-permission-prompts`, `telegram:configure`, `telegram:access`, plus custom workspace skills. Each carries a one-line trigger description; the persona needs to know which skills exist + when each is the right reach. ≈ 3 aggregated docs (one per category: built-in / marketplace / workspace).
- **Settings.json.** `hooks.*`, `permissions.allow/deny/ask`, `env`, `statusLine`, `model`, `outputStyle`, `theme`, `keybindings`, `disableMessageReceived`, `apiKeyHelper`. ≈ 1 doc.
- **Plugins.** The plugin format; the marketplace-vs-local distinction; the sandboxing model. ≈ 1 doc (low priority — marginal relevance in pos-v2's near-term).
- **Image / file handling.** Read-tool capabilities (PDF, Jupyter, image), Write-tool, Edit-tool. Mostly the model handles this without persona orchestration; ≈ 1 reference doc.
- **Status line.** Doc body covered by `pos3/.scratch/claude-output/claude-code-statusline-research.md`. ≈ 1 internal doc.
- **Background tasks (`run_in_background` + Monitor).** Inline pattern for Bash; the streaming-output pattern for long-running commands. ≈ 1 doc.

**Subtotal: ~30 docs, ~120 k chars at well-edited density.**

### 2.2 Claude API / Anthropic SDK surface (~5–10 docs)

Mostly relevant to *artefacts pos-v2 builds*, not the harness itself, but the persona needs to know what it can choose when it dispatches a build:

- **Prompt caching.** Multi-turn cache, breakpoint placement, expiry semantics, cost mechanics.
- **Thinking mode.** Budget tokens, when extended thinking outperforms baseline.
- **Batch API.** Async batch dispatch; cost halving; latency tradeoff; when batching is the right reach for a build the persona is dispatching.
- **Files API.** Persistent file uploads; cite-via-file pattern; PDF/document-extraction pattern.
- **Citations.** Auto-citation feature; structural citation enforcement.
- **Tool use.** Function calling; structural argument validation; result-shape contracts.
- **Model selection.** Opus / Sonnet / Haiku tradeoffs; subscription routing (`claude -p` vs API key); per-task-shape selection criteria.

**Subtotal: ~7–10 docs, ~30–50 k chars.**

The Anthropic-published `claude-api` skill (visible in the skills list this session) covers most of this content already; the persona's relevant surface is a *thin index* of "when each technique applies", not a duplicate of the skill itself.

### 2.3 pos-v2 harness primitive surface (~15–20 docs)

The sealed-component fence list from `STATE.md`:

- **scope-of-work primitive** — pyee event surface, `list(filter)`, the seven declared fields, lifecycle.
- **objective-tracker** — the SQLite-backed objective registry, how plans bind to it.
- **session-resilient orchestrator** — `activate_scope`, `bind_scope`, IPC contract, compaction-restore.
- **safety-layer** — the structural-refusal patterns, named-failure contracts.
- **cost-governance** — budget lines, fire-once warnings, the C15 ceiling pattern.
- **reversibility-primitive** — the seven reversibility classes; reverse-action authoring.
- **self-correction** — the structural-remedy event surface.
- **observability-aggregator** — the OTel surface, the awareness-block contributor.
- **memory-system** — graphiti add_episode / search; what's a good episode shape; group_id / namespace mechanics.
- **primary-persona-layer** — the contributor surface (`ComposedContextPayload.register`); D7's memory-retrieval contributor; D8's session-start gate; how to compose new contributors.
- **graceful-degradation** — the patterns for partial-failure handling.
- **self-upgrade** — the upgrade-without-impacting-workspace surface.
- **workspace-bootstrap** — the first-run state machine; phases; settings.json merge surface (`merge_session_start`, `merge_user_prompt_submit`, future `merge_stop`, `merge_status_line`).
- **hands-off-lifecycle** — settings.json fragment; first-run-helper; supervisor stanza.
- **telegram-interface** — the inbound/outbound channel; access control; bot-token configuration.

**Subtotal: ~15 component-level docs + per-component "consume me" cheat sheets (~20 docs total), ~80–120 k chars.**

### 2.4 Operational patterns (~10 docs)

These are the "between primitives" advice — what ladders into a Lens 2 read:

- **When to use background agents.** Multi-artefact authoring, ~30 s+ generation, parallel-research dispatches.
- **When to use `/loop`.** Recurring poll without scheduler infra; self-pacing for "tell me when X is true."
- **When to use `/schedule` (cron-shaped).** Daily briefings, weekly digests, monthly closeouts; one-shot reminders ("at 3pm tomorrow").
- **When to fall back to MCP servers.** Decoupled state, third-party API integration, cross-session resource access.
- **When to use a hook vs a script the user runs.** Automated behaviours (per the `update-config` skill's framing) require hooks; one-off transformations don't.
- **When to use a subagent / Agent tool.** Specialist routing, scope-bounded dispatch, parallel research, audit-isolated review.
- **When to use prompt caching.** Long static prefix + variable suffix; multi-turn assistant; structured-output validators.
- **When to use thinking mode.** Hard reasoning that the model gets wrong without it; cost-tolerable single-shot.
- **When to use batch.** Async batched processing; cost-sensitive bulk work; not-time-critical.
- **When to use Telegram-channel reply vs in-session reply.** Sender-context awareness; the persona's translation-layer choice between channels.

**Subtotal: ~10 docs, ~30–40 k chars.**

### 2.5 Realistic upper bound

**~50–70 documents, ~250–350 k chars at well-edited density.** Not 30; not 300. The strawman's question of "30 documents? 300?" lands in the middle.

This is small enough that it fits inside an MCP server's resource list comfortably (Claude Code's MCP resource surface is unbounded by spec). It is too big for a single additionalContext payload (the 10 k cap plus the existing contributors gives the persona ~5 k chars of headroom for capability content; 250 k won't fit). It's too big for the persona prompt.md (which the rendered agent file already extends with the framework's identity-anchor block; bloat in prompt.md hurts every turn's prefill).

### 2.6 Two-class corpus partition (locked by Luke 2026-04-26)

The §2.1–§2.4 inventory above mixes two structurally different content classes. Locking the partition explicitly:

#### Class A — Anthropic-canonical reference

**Definition.** The objective, Anthropic-published feature surface — what each Claude primitive *is*, what its inputs/outputs/contracts are, what its envelope shapes look like. This is the §2.1 (Claude Code feature surface) + §2.2 (Claude API / Anthropic SDK surface) content from above. §2.3 (pos-v2 harness primitives) is the structurally-equivalent **Class A-prime** for the harness — same access pattern, same authoring shape, just sourced from pos-v2's own component docs rather than Anthropic.

**Sources.**
- Anthropic's documented feature surface: `docs.anthropic.com`, `docs.claude.com`, the `/help`-discoverable feature list, the `claude --version` release-notes surface, Anthropic's prompt library.
- Anthropic's first-party skills marketplace (the `claude-api`, `loop`, `schedule`, `update-config` skills are themselves canonical reference for the primitives they wrap).
- For Class A-prime (harness): pos-v2's own `docs/archive/component-research/<name>/` deliverables, sealed-component contracts, and the `STATE.md` ladder.

**Freshness profile.** **As fast as Anthropic ships.** Claude Code releases multiple features per week (per FUTURE_IDEAS.md Idea 1 / Step 4). A new slash command, a new hook event, a new MCP transport — these change the surface the persona must know about within hours of release. Stale Class A entries are silently wrong: the persona will recommend an old-name flag, suggest a deprecated primitive, or miss a new option.

**Authoring shape.** **Deterministic projection from canonical source.** A Class A doc is not authored by judgement — it is *projected* from the upstream documentation by a structural transform (fetch, parse, normalise, emit). A human (or the persona) curates the index entry and the `[user-intent phrasings]` overlay (see §4.1) but the body of each Class A doc is a deterministic rendering of the upstream truth. This makes Class A refreshable (§7bis.1): re-projecting from a newer upstream is mechanical and yields a clean diff.

#### Class B — Best-practices wisdom

**Definition.** Operational patterns *between* primitives — what works in practice, what fails, when to reach for which primitive, prompt shapes that get good results, prompt shapes that get poor results, anti-patterns, real-session experience. This is the §2.4 (Operational patterns) content from above and a great deal more that does not yet exist in any one place.

**Sources.**
- **Community discussion.** Reddit (`r/ClaudeAI`, `r/ClaudeCode`), Discord servers (Anthropic's community Discord and adjacent), X/Twitter (the Claude-Code-builder cluster — patterns shared by users who are using Claude heavily for production workflows), blogs, GitHub issues against `anthropic/claude-code` and adjacent repos.
- **Anthropic's prompt library** (the published examples — these straddle Class A and Class B; the *fact* that the API supports a structured-output pattern is Class A, *which prompt shape works best for it* is Class B).
- **Internal pos-v2-session observations.** When the primary persona dispatches a background agent and the result is high-quality, *that's* a best practice; when a prompt shape fails repeatedly, *that's* an anti-pattern. These accrue from real use and are arguably the most valuable Class B content because they are first-party-validated against Luke's actual workflow.
- **User-supplied capture.** When Luke says "Eve, remember I should always use background agents for research" — that is a Class B entry the user is dictating directly. This is the highest-trust source by definition (the user has lived experience and is asking for it to be persisted).

**Freshness profile.** **Continuous accrual.** Best practices do not arrive in version-bumps; they emerge as users discover them and share them. There is no canonical source to project from. A Class B entry's truth-value is not "Anthropic says X" — it is "this pattern was observed to work N times and fail M times" or "Luke explicitly asked the persona to remember this." The accrual rate is low-volume but constant (a handful of new entries per week if all three channels are wired).

**Authoring shape.** **Synthesis + curation, not deterministic projection.** A Class B doc is authored by a process that:
1. Surveys multiple sources (community discussion, internal observation, user statements).
2. Identifies a recurring pattern across them.
3. Synthesises a single concise entry that names the pattern, the primitives it relates to, the conditions under which it applies, and the failure modes it avoids.
4. Curates against the existing Class B corpus to dedup or supersede entries that have been refined.

The authoring is not deterministic — it requires judgement at every step. This is why the currency mechanism for Class B (§7bis.2) is fundamentally different in shape from Class A's.

#### Cross-relationship — Class A ↔ Class B at retrieval time

A Class A entry ("`/loop` slash command exists, takes optional interval arg, self-pacing when omitted, omitted-interval prompts the model to pace itself") is paired with one or more Class B entries:

- ("when to use `/loop` vs `/schedule`" — `/loop` for poll-and-react with model judgement on cadence; `/schedule` for genuinely cron-shaped fixed-interval work; MCP cron when state must persist across sessions independently of any one Claude session)
- ("`/loop` failure mode: tight loops without exit conditions burn subscription throughput; always pair with a sentinel observation the model can break on")
- ("`/loop` + background-agent pairing: don't `/loop` a background dispatch; the loop is the dispatch's poll surface, not its container")

Both classes are queryable. Both surface to the persona at planning time. The retrieval shape is layered: the Class A entry provides the *contract* (what the primitive is); the Class B entries provide the *judgement* (when and how to use it).

**Implementation:** the β knowledge-server's `resources/list` surface partitions by class — `capability:claude-code:<name>` for Class A, `capability:harness:<name>` for Class A-prime, `capability:best-practice:<topic>` for Class B. The `search(query)` tool fuses across classes and ranks by relevance. The persona's prompt.md spine (§4.4) names a **paired-fetch convention**: when the spine names a Class A primitive that has Class B entries attached, the persona fetches both before planning the action.

#### Why the partition matters

The two classes have different freshness profiles, different authoring shapes, different sources, and different trust-evaluation patterns. Conflating them would cause:

- Class A staleness silently rendered as best practice ("the persona told me to use `--legacy-flag` because the corpus said so" — when the flag was renamed three releases ago and no one updated the entry).
- Class B authoritative-tone applied to community speculation ("the persona told me this pattern works because the corpus said so" — when the source was a single Reddit comment with no validation).
- Currency mechanism mismatch (§7bis): a deterministic-projection refresh that overwrites Class B would destroy hard-won synthesis; a synthesis-and-curation refresh that touches Class A would inject judgement into content that should be mechanically projected.

The partition gives each class its own freshness pipeline and its own trust-marker, while keeping retrieval unified at query time.

---

## 3. Question 2 — Cost realism for graphiti seeding

### 3.1 Empirical baseline (from amendment #33's research)

| Metric | Value | Source |
|---|---|---|
| LLM calls per episode (mean) | 3–7 | amendment #33 §3.2 |
| Wall-time per episode (small synthetic) | 7–12 s | D4 baseline |
| Wall-time per episode (realistic 9-entity / 8-edge payload) | **113 s** | 2026-04-23 measurement |
| Cost per episode (Haiku 4.5) | ~$0.0176–0.0215 | amendment #11 |
| Annual cost at 7,300 episodes/year (turn-aggregation) | ~$146 | research §3.2 |

### 3.2 Strawman cost — one-document-per-episode

**50 docs × 113 s/doc = 95 min one-shot ingest at the realistic-payload extraction rate.** This is wall-time, not cost — at Claude Max it's subscription-absorbed (zero $-cost) but consumes ~1.5 hours of subscription throughput. Pay-per-token: 50 × $0.02 = $1.00 one-shot. Cost is NOT the blocker. Wall-time + the failure-mode profile + the dedup question are the blockers.

### 3.3 Strawman cost — one-doc-per-episode with realistic capability docs

A capability doc is denser than a turn aggregate (more entities, more edges). The 113 s figure was for a 9-entity / 8-edge payload; a typical Claude Code feature doc has ~20 entities (commands, flags, hooks, files, options) and ~30 edges (composition relationships, exclusion relationships, prerequisite relationships). Wall-time scales roughly linearly with extraction work. Estimate: **180–250 s per capability doc**, possibly higher.

**Revised 50-doc estimate: 50 × 200 s = ~167 min wall-time = ~2.8 hours one-shot.** Subscription throughput pressure is real but absorbable.

### 3.4 graphiti's `add_episode_bulk` exists — does it help?

`graphiti_core/graphiti.py:1037` exposes `add_episode_bulk(bulk_episodes: list[RawEpisode], ...)`. Reading the implementation:

- It batches multiple episodes through extraction in parallel where possible.
- **It explicitly does NOT perform edge invalidation or date extraction.** This is documented at line 1097 — "If these operations are required, use the `add_episode` method instead for each individual episode."
- It does not return a temporal-relationship-aware graph; relationships are extracted but invalidation passes are skipped.

For a static reference corpus (capability docs do NOT invalidate each other; they're not temporal), `add_episode_bulk` is **structurally appropriate** and would batch the 50 docs efficiently. Estimate the wall-time at 30–50 % of the sequential figure: **40–80 min one-shot**. The bulk path is real and meaningfully cheaper.

But: this changes the cost story without changing the *retrieval-shape* problem (Question 3). Cheaper bulk-load doesn't mean retrieval works.

### 3.5 Dedup across multiple ingest passes

graphiti's standard `add_episode` does dedup at the entity-and-edge level (uuid_map carries the deduped node identities). `add_episode_bulk` also dedupes within a bulk (`_extract_and_dedupe_nodes_bulk` per line 1156). Re-ingesting the same doc would create a new Episodic node but the entities and edges would dedupe cleanly. Re-ingesting an *updated* doc creates additional nodes/edges; old facts about the prior version of the doc remain in the graph unless invalidated. **graphiti is built around incremental accrual, not refresh-by-replace** — it's the wrong tool for "this doc has been updated, replace its representation."

This is the structural problem. Capability docs *update* — Claude Code ships features weekly, deprecates features, changes flag names. A graphiti seed becomes stale; re-seeding doesn't replace the old facts. Idea 1 / Step 4's refresh primitive lands in a graph that's accumulated 6 months of stale facts. The graph won't tell you "this is the current name"; it will tell you "this and that and a third are all named for this concept; figure out which is current."

### 3.6 graphiti is a user-experience memory, not a static-reference index

This is the crux of the cost-vs-value analysis. graphiti's design optimises for: (a) accruing user-and-assistant interaction signal over time, (b) finding non-obvious connections via multi-hop graph traversal, (c) temporal-validity tracking so superseded facts can be excluded. None of these properties matter for a static capability index:

- (a) capability docs are not user signal; they're authored content with a known schema.
- (b) Capability composition relationships are *explicitly authored* (this hook composes with that primitive); multi-hop discovery doesn't add value when the relationships are already documented as edges in the source corpus.
- (c) Temporal validity matters for capability docs (deprecation), but graphiti's invalidation semantics are interaction-driven, not source-of-truth-driven.

**Verdict: the strawman puts a static-reference need on a memory substrate optimised for user signal. Wrong shape.**

This does NOT mean memory has no role in the leverage problem. It means the memory's role is *capturing what the user has actually used + what worked + what didn't* — exactly what graphiti optimises for. That's a complementary surface, not the substrate for the capability index.

### 3.7 Practical seeding strategy

If the recommendation were the strawman, the practical seeding strategy would be:

- **One-time at workspace-bootstrap** (not at canonical-repo-build): ingest happens after the user's `personas/<handle>/` is in place + the memory MCP server is up. This is the sub-plan G activation + per-workspace-graphiti window. ≈ 40–80 min wall-time.
- **Bulk-load via `add_episode_bulk`** is the right ingest mechanism; not the per-episode `add_episode` path.
- **Refresh via Idea 1 / Step 4** would re-ingest changed docs incrementally; old facts would persist (per §3.5).

But this strategy is *only relevant if the strawman is the recommendation*, which it isn't.

---

## 4. Question 3 — Retrieval-shape design

The retrieval-shape problem is the load-bearing one regardless of substrate. The owner's example is exactly the right test case:

**User says:** *"set me up to get a daily briefing."*

**What the persona needs to know to translate this:**

- `/schedule` skill exists and runs cron-shaped tasks — the slash-command shape is fastest.
- Background agents can be paired with `/schedule` for a "schedule + dispatch" pattern.
- Telegram-interface can deliver the briefing if the user's primary channel is Telegram.
- A briefing's content typically composes proactive-surfacing (Lens 2) + observability-aggregator readouts + memory-retrieval over yesterday's turns.

**Semantic-top-N keyed on the user's literal prompt:**

- Query: "set me up to get a daily briefing."
- Semantic match against capability corpus: the embedding for "daily briefing" matches docs about briefings, daily routines, summaries — but `/schedule` is buried under "cron-shaped tasks" or "scheduled remote agents" and the embedding distance is large. **Likely retrieval miss.**

This is the exact failure mode the strawman has. Three orthogonal mitigations:

### 4.1 Mitigation A — Episode anchoring with synthetic "user-intent phrasings"

Each capability doc gets an explicit synthetic section, e.g.:

```
[user-intent phrasings]
- "set me up to get a daily X"
- "remind me every day to..."
- "send me a digest each morning"
- "do this thing every 12 hours"
- "make this a recurring task"
```

The capability doc's body remains technical; the user-intent phrasings are co-located. Semantic retrieval against the user's prompt finds the phrasings, which point at the capability.

This works **regardless of substrate**:

- In graphiti, the phrasings become part of the episode body — extraction creates entities for each phrasing and edges to the capability concept.
- In an MCP knowledge-server, the phrasings are part of the resource body — full-text search and embedding lookups both surface them.
- In prompt.md, the phrasings are part of the index — keyword-matched directly.

**Recommendation: every capability doc carries a `[user-intent phrasings]` section. This is corpus-authoring discipline, not a substrate choice. Should land in the corpus authoring guide regardless of substrate.**

### 4.2 Mitigation B — Tagged retrieval contributor

Independent of semantic retrieval, the persona should be able to fetch **all "capability:claude-code" episodes** at session start (or on demand when the persona's "is this a Lens 1 moment?" check fires). graphiti supports this via:

- `group_ids=[workspace_slug, "capability-corpus"]` — a separate group for the capability content. The retrieval contributor can then search the capability group regardless of relevance to the immediate prompt.
- `source_description` filtering — graphiti's `_impl_search` doesn't directly support filtering by `source_description`, but the FTS index includes it (`graphiti_core/graph_queries.py:103`). A custom search call could filter by `source_description LIKE 'capability:%'`.

For an MCP knowledge-server, tagging is even simpler: the resource list is the index; "show me all capability:claude-code resources" is one MCP call (`resources/list` with a category filter).

**Recommendation: capabilities are tagged at ingest (whatever the substrate); a retrieval contributor pulls the full capability index on session start as a bounded "menu" the persona can browse without per-turn semantic retrieval.**

### 4.3 Mitigation C — Hybrid retrieval (keyword + semantic)

Pure semantic retrieval misses on the daily-briefing example because "schedule" is the right keyword and "briefing" is the right semantic match. Hybrid retrieval (keyword OR'd with semantic, results fused via reciprocal-rank-fusion) catches both. graphiti's edge search uses RRF internally (`EDGE_HYBRID_SEARCH_RRF` is referenced in `graphiti.py:1531`), but the *episode* surface doesn't expose the same hybrid path.

For the persona's day-1 effectiveness, **hybrid retrieval is more reliably built on top of an MCP knowledge-server's resource surface than on top of graphiti's episode surface.** The MCP server can expose:

- `search(query, ...)` — a tool that does hybrid retrieval over the resource corpus.
- `resources/list` — the static index for "show me everything tagged `capability:*`."
- `resources/read?uri=...` — full doc content on demand.

This is a thin server (~200 LOC); the storage backend can be sqlite-FTS5 + a small embedding index, or a hosted vector DB if more sophistication is wanted. The point is the *retrieval contract* is a separate primitive from the *interaction memory* graphiti is designed for.

### 4.4 Mitigation D — Pre-bake into prompt.md / additionalContext

Some capability content is high-leverage and small: the *index* of capabilities (one line per capability), the leverage rule itself, the "categories of work" routing table. This content is bounded and doesn't go stale at the per-feature level (the *index* is stable; the *details* change). It belongs in prompt.md as the persona's spine.

The shape:

```
[Leverage rule] — On every plan, before any tool call, ask:
1. What Claude Code primitive does this lean on?
2. What harness primitive does this lean on?
3. Have I named both in my plan?
If the answer to (3) is no, stop and consult the capability index.

[Capability index] — When the user asks for...
- recurring work → /schedule (cron-shaped) or /loop (self-pacing)
- async deep-research → background agent (Task tool, run_in_background)
- multi-hop user-history queries → memory-retrieval (composer contributor)
- channel-aware delivery → telegram-interface or in-session
- automated behaviour → settings.json hooks (use update-config skill)
- ... [50 more lines like this]

For full detail on any capability, fetch
mcp__knowledge__read?uri=capability:<name>.
```

This spine fits in ~1.5 k chars in prompt.md. It's always-on. It's the cheapest possible always-on leverage prompt. It points at the MCP server for detail.

### 4.5 Retrieval-shape verdict

**The right shape is a layered stack:**

1. **prompt.md spine** — leverage rule + capability index (1.5 k chars, always-on).
2. **MCP knowledge-server** — full corpus, on-demand fetch via `resources/read` and `search` tools.
3. **graphiti** — user-and-assistant interaction memory, NOT capability docs (the strawman is rejected at this layer; graphiti continues to do what it's designed for).
4. **Optional session-start contributor** — fetches "today's contextually-relevant capability subset" based on the workspace's recent activity (e.g., if the user has an in-flight `/schedule`-bound task, the schedule capability gets surfaced in the session-start additionalContext).

The strawman's intuition was right that capability knowledge needs a retrieval mechanism. The strawman's substrate choice (graphiti) was wrong because graphiti is optimised for the wrong access pattern. The shape that does work uses three substrates layered for different access patterns.

---

## 5. Question 4 — Alternatives to graphiti, weighed

### 5.1 Static additionalContext composer fragment

**Shape:** capability docs (or a summary) loaded as a baseline corpus into every session-start payload. The composer would have a `capability-index` contributor that adds ~1–2 k chars of capability-index content to the SessionPayload.

**Pros:**

- Always-on; persona always has the index in scope.
- Cheap to land (one new contributor in `primary-persona/src/`); composes on D8's existing surface.

**Cons:**

- Bounded by the 10 k additionalContext cap. With existing contributors (memory-retrieval + tracker-context + corpus-gate + future ones), headroom is ~5 k chars; capability content fits as an *index*, not as the corpus itself.
- Any time the index changes, every session-start payload changes — the cap-validator catches overflow at construction time.
- Doesn't solve the "user asks something; persona fetches detail on demand" pattern; index is one-shot at session-start.

**Verdict: yes, but only as the `prompt.md spine` realisation — and prompt.md is the cleaner shape than additionalContext for this content because prompt.md is part of the persona's identity, not a per-session payload.**

### 5.2 MCP knowledge-server (recommended)

**Shape:** a new MCP server exposing capability docs as resources (`resources/list`, `resources/read`) plus a `search(query)` tool. Server runs alongside `memory-graphiti`. Workspace-bootstrap registers it via `.mcp.json`.

**Pros:**

- Clean separation from graphiti — capability docs and interaction memory live on different substrates with different access patterns.
- Hybrid retrieval (keyword + semantic) is straightforward to author with sqlite-FTS5 + a small embedding store.
- On-demand fetch — the persona pulls detail only when the prompt.md spine names a capability the user's prompt invokes.
- Refreshable — Idea 1 / Step 4 can re-author the corpus and reload the server; no graph invalidation problem.
- Tagged retrieval — `resources/list?category=claude-code` is one call.
- Composable on Claude Code's existing MCP fetch surface — no new persona-side machinery needed; the persona uses the same MCP tool-call shape it uses for graphiti.

**Cons:**

- One more MCP server to install + manage. Workspace-bootstrap already handles MCP server registration via the `.mcp.json` writer that landed at amendment #47, so this is incremental.
- ~200 LOC of new server code; ~1–2 weeks of build wall-clock if scoped as a single amendment.
- The corpus authoring is the bigger lift — 50–70 docs to author. This is a separable workstream from the server build; the server can ship with a partial corpus and grow.

**Verdict: yes — the right substrate for the *full* corpus on-demand.**

### 5.3 Persona-prompt content (recommended for the spine)

**Shape:** bake the leverage rule + capability index into `personas/primary/prompt.md` directly. This is workspace content (per the no-personas-in-core rule); the workspace authors the spine.

**Pros:**

- Simplest possible. Always-on. No new infrastructure. No new MCP server. No new contributor.
- Persona's identity carries the leverage rule — the rule is *part of who the persona is*, not a piece of context bolted on.
- Bounded by prompt size, which is large (Claude's context window absorbs prompt.md without strain) but finite.

**Cons:**

- Stale — prompt.md is workspace-authored; refreshing it is a workspace-level operation, not an automatic one.
- Without a refresh primitive (Idea 1 / Step 4), the spine drifts as Claude Code ships features.
- Index-only; full capability docs don't fit.

**Verdict: yes — the right substrate for the *spine*. The full corpus needs another substrate (5.2).**

### 5.4 Hybrid (the recommendation)

**Shape:**

- prompt.md carries the leverage rule + the capability index (always-on, ~1.5 k chars).
- MCP knowledge-server carries the full corpus (on-demand, ~50–70 docs).
- graphiti carries user-and-assistant interaction memory (existing — unchanged).
- Optional D-7-shaped session-start contributor: when the workspace is in DEV MODE, surfaces "today's contextually-relevant capabilities" based on recent scope activity (this is the "structural enforcement" half of D-3).

**Pros:**

- Each substrate does what it's optimised for.
- The spine is tiny and ships fast.
- The server is bigger but ships independently after the spine has demonstrated value.
- graphiti continues doing user-memory; the strawman's overload is avoided.
- Refresh story is clean: Idea 1 / Step 4 re-authors the corpus, server reloads, no graph invalidation.

**Cons:**

- Two-amendment (or three-amendment) program rather than one.
- Corpus authoring is real work; the spine can ship with the index pointing at TODO entries that get filled in over the corpus-authoring phase.

**Verdict: this is the recommendation. It treats the strawman's intuition (capability knowledge needs to be retrievable) as correct while routing the implementation to substrates that actually fit.**

---

## 6. Question 5 — The "always think about leverage" personality rule

The owner's framing names this as both a personality property (the persona's disposition) and a structural property (the harness ensures the persona has the right context to act on it).

### 6.1 Personality half — declarative in prompt.md

The persona's prompt.md gets a load-bearing paragraph:

> **Leverage discipline.** On every plan that involves taking action, stop before the first tool call and ask: *what Claude Code primitive does this lean on? what harness primitive does this lean on?* If you cannot name both, consult the capability index in this prompt or fetch detail via the knowledge MCP server. The user is paying for the translation between their natural-language intent and AI-effective execution; that translation is your prime function. Skipping the leverage check is skipping the function.

This is one paragraph. It's the rule. It's always-on.

### 6.2 Structural half — session-start contributor surfacing "today's contextually-relevant capabilities"

The declarative half by itself doesn't help when the persona's training-cut knowledge is stale. The structural half ensures the persona has *current* capability surface in scope at every session start.

Two shapes:

**Shape A — static capability index in additionalContext.** The composer registers a session-level contributor that emits the same index as prompt.md's spine. Simpler; pure repetition of the spine in additionalContext doesn't add anything beyond reinforcement.

**Shape B — dynamic capability index based on recent activity.** The contributor reads the workspace's recent scope-of-work events (last N days of activity), maps activity types to relevant capabilities, and emits a tighter "given what you've been doing, here are the capabilities most likely relevant" block. This is the smarter shape but it's a real composition: it requires the contributor to know the activity-type→capability mapping, and the mapping has to be authored alongside the corpus.

**Recommendation: shape A first** — the spine in prompt.md is repeated in additionalContext as a hedge against compaction, and the dynamic shape (B) is a follow-on improvement once the corpus is authored and the activity-type vocabulary stabilises.

### 6.3 Lens-1 self-check

Lens 1 ("what Claude capability does this lean on?") is the leverage rule. The persona's session-start contributor is composed against D8's already-shipped contributor surface. The MCP knowledge-server composes on Claude Code's MCP fetch surface. The prompt.md content is composed against the workspace-supplied persona contract surface (amendment #35's projector). **Every layer leans on existing pos-v2 + Claude Code primitives. Lens 1 is satisfied at every layer.**

---

## 7. The recommended program — sequenced amendments

**Four amendments** (was three before the 2026-04-26 currency-mechanism extension), sequenced for compounding value. The research recommends the program but does NOT author plan-docs for each (per dispatch directive — the cost-vs-value cliff in the strawman pushes toward "name and sequence", not "fully plan").

**Program shape with the extension:** α (prompt-spine + corpus seed) → β (MCP knowledge-server, two-class-aware from day one) → δ (Class A currency — the deterministic projection refresh, formerly out-of-scope as Idea 1 / Step 4) → γ (optional dynamic contributor). **Class B accrual** rides as composed features inside β and δ rather than as a standalone amendment ε; see §7bis for the design and the alternative-ε escape hatch if owner prefers the split.

### 7.1 Amendment α — prompt.md spine + corpus authoring guide (1–2 days)

**Scope:**

- Author the leverage discipline paragraph + capability index in `personas/primary/prompt.md` (or whatever workspace's persona-handle directory is canonical at the time the amendment lands).
- Author the **two-class** corpus-authoring guide: "every Class A doc has these sections; here's the `[user-intent phrasings]` discipline; here's the deterministic-projection contract from upstream sources. Every Class B doc has these sections; here's the synthesis-and-curation discipline; here's the trust-marker rubric (sources counted, validation observed, supersession notes)."
- Author 5–10 seed Class A capability docs in `docs/capability-corpus/claude-code/` — start with the highest-leverage ones (`/schedule`, `/loop`, background agents, hooks, MCP, the harness composer surface).
- Author 3–5 seed Class B best-practice entries in `docs/capability-corpus/best-practice/` — start with patterns Luke has already articulated (background agents for research, fire-and-forget for cost, no parallel-memory chaos, anti-deskilling pairing on auto-create — these are already documented in `MEMORY.md` and ladder cleanly to Class B entries).
- The seed docs are static markdown — no MCP server yet. The persona can read them via the Read tool when the spine names them; this proves out the "spine names → persona fetches" flow without server infrastructure. The directory layout under `capability-corpus/` already partitions the two classes, so β inherits a clean schema.

**Lens reads:**

- L1: composes on Claude Code's prompt.md surface + Read tool. No re-implementation.
- L2: primary-persona test passes — the user's leverage-translation burden drops to zero (the persona has the rule and the index). Harness test passes — the corpus is a primitive every future contributor (and human author) draws against.
- ODD: ACs are outcome-shaped — "spine present in prompt.md", "N capability docs authored under canonical path", "each doc has the named sections."

**Sealed-fence:** workspace-supplied persona content (NOT pos-v2 core; the no-personas-in-core rule holds — the spine is *workspace-shipped*, not core-shipped). The corpus is a docs-tree addition; outside any sealed component fence.

**Cost:** small. Mostly authoring time. No code.

### 7.2 Amendment β — MCP knowledge-server, two-class-aware (1–2 weeks)

**Scope:**

- New top-level package `knowledge-server/` (sibling to `memory-system/`, `telegram-interface/`, etc.) — a FastMCP-based streamable-HTTP server exposing:
  - `resources/list` with **two-class** category filtering: `capability:claude-code:<name>` (Class A — Anthropic-canonical), `capability:harness:<name>` (Class A-prime — pos-v2 components), `capability:best-practice:<topic>` (Class B — community + internal + user-supplied). Each resource carries a `class` attribute and a `trust_marker` field (Class A: `source_url + source_fetch_ts`; Class B: `sources_count + validation_count + supersession_chain`).
  - `resources/read?uri=...` returning the full doc body.
  - `search(query, class?)` tool implementing hybrid retrieval (sqlite-FTS5 + small embedding store), partitioned by class so a query for "daily briefing" returns paired Class A entries (`/schedule`, background agents) and Class B entries ("when to use `/schedule` vs `/loop`").
  - **Class B internal-accrual subscriber**: a Stop-hook subscriber (composed on memory-system's existing extraction pipeline) intercepts episodes with `source_description="capability-best-practice"` and mirrors them into the knowledge-server's resource path. This realises the §2.6 internal-observation channel without a parallel-memory substrate. Implementation: amendment β includes a `BestPracticeMirrorContributor` that subscribes to the post-extraction event surface and writes mirrored Class B entries to disk + indexes them.
- Workspace-bootstrap's `.mcp.json` writer (post-amendment-#47 surface) gets a new entry for the knowledge-server.
- The corpus from amendment α moves under the server's resource path; the server reads from disk on startup.
- The persona's prompt.md spine updates: "fetch detail via `mcp__knowledge__resources/read` instead of via Read on the doc path; pair Class A fetches with their attached Class B entries." This makes the corpus location an implementation detail behind the MCP surface.

**Lens reads:**

- L1: composes on Claude Code's MCP server surface + the `.mcp.json` registration mechanism (amendment #47). No re-implementation; the knowledge-server is structurally identical in shape to memory-graphiti, just exposing different content.
- L2: harness test — the knowledge-server is a primitive every future feature draws against (Lens 1 enforcement at research time, the persona's leverage discipline at runtime, future Idea 1 / Step 4 refresh as a downstream consumer).
- ODD: ACs are outcome-shaped — "the knowledge-server registers via `.mcp.json` and Claude Code can list the registered tools at session start", "search returns the right top-N for the daily-briefing test prompt", "resources/read returns the full doc body."

**Sealed-fence:** new top-level component; workspace-bootstrap's `.mcp.json` writer extends to register it. Both are inside existing fences (`knowledge-server/` is new — clean fence; `workspace-bootstrap/` is the home of `.mcp.json` writing).

**Cost:** medium. ~1–2 weeks build wall-clock based on the precedent of memory-system (which is structurally similar — FastMCP server + tools + resources).

### 7.3 Amendment δ — Class A currency (deterministic projection refresh) + Class B community-survey channel (1–2 weeks)

This amendment realises FUTURE_IDEAS.md Idea 1 / Step 4 with the two-class extension. It is the structural answer to the locked-by-Luke 2026-04-26 currency requirement.

**Scope (Class A — deterministic refresh):**

- A scheduled refresh primitive (composed on `/schedule` skill — the cron-shaped scheduler is Claude-native; per Lens 1, lean on it rather than re-implementing) that:
  1. Fetches a manifest of canonical Anthropic sources (the documentation index, the release-notes feed, the skill marketplace listing). Manifest is workspace-authored under `personas/<handle>/capability-sources.yaml`.
  2. For each source, projects the canonical content into the Class A corpus shape via a deterministic transform (parse → normalise → emit markdown body with `[user-intent phrasings]` overlay preserved across refreshes). The transform is structural (per CLAUDE.md "structural over advisory"); it does not consult an LLM.
  3. Diffs each projected doc against the current corpus; produces a structured delta (additions, deprecations, content changes).
  4. **Anti-deskilling pairing on auto-create:** the delta is surfaced to the user (Telegram or in-session) for one-line acknowledgement before merge. Auto-merge is the default for content-changes (low risk); deprecations and additions get the pairing prompt (per Luke's preference for pairing on novelty). The pairing surface is fire-and-forget — the user can ack later; the corpus stays usable in the meantime.
  5. Cost-governance composition: the refresh is a budget-line consumer (per FUTURE_IDEAS Idea 1 / Step 4's existing framing). If the refresh would push a rolling-window spend past its cap, it defers.

- **Cadence:** **daily** for the high-velocity sources (Anthropic release notes, skill marketplace) — Claude Code ships features within hours; daily catches new primitives within a session of their availability. **Weekly** for the slower sources (long-form docs that change less often). Both cadences are workspace-overridable in `capability-sources.yaml`.

- **Trigger surface:** the `/schedule` skill, registered at workspace-bootstrap time. The schedule entries are workspace-authored (per the no-personas-in-core rule); pos-v2 ships the *contract* (manifest schema, projection transform, diff-and-pairing flow) but the schedule binding is workspace.

**Scope (Class B — community-survey channel):**

- A **periodic community-survey scope** dispatched as a **background agent** (per Luke's "default to background agents for multi-artefact authoring" preference) on a slower cadence (weekly or fortnightly):
  1. Web-search across the named Class B sources (Reddit `r/ClaudeAI` + `r/ClaudeCode`, the relevant Discord channels via their public archive surface where available, X/Twitter searches against Claude-Code-builder accounts, GitHub issues with the `pattern` or `best-practice` label).
  2. Summarise observed patterns; cross-reference against the existing Class B corpus.
  3. Propose a corpus delta — new entries + supersession of entries the community has refined.
  4. Owner-gate the delta before merge (anti-deskilling pairing — the survey scope is *generating* judgement-content; the user reviews before that judgement enters the persona's retrieval surface).
  5. Cost-governance composition: bounded per-survey budget; defers on overage.

- **Cadence:** **weekly initially**, with a knob for the user to dial up or down based on survey hit-rate. Faster cadences are wasteful (community wisdom doesn't accrue daily); slower than fortnightly risks staleness.

- **Internal-observation channel** is realised by β's Stop-hook subscriber (already specified in §7.2); δ does not duplicate it.

- **User-driven channel** ("Eve, remember I should always use background agents for research") is realised by the existing graphiti `add_episode` write path — the persona writes the episode with `source_description="capability-best-practice"`, β's mirror subscriber picks it up, the entry appears in the next retrieval cycle.

**Lens reads:**

- L1: composes on `/schedule` (Claude-native scheduler), background-agent dispatch (Claude-native), `cost-governance` budget-line (sealed pos-v2 primitive), `memory-system` Stop-hook surface (sealed). No re-implementation; δ is composition top to bottom.
- L2: primary-persona test — the user gets a self-maintaining capability corpus without managing the maintenance. Translation burden of "is this primitive current?" drops to zero. Harness test — the refresh primitive is itself a toolkit entry the persona can dispatch (e.g., "force a refresh of the schedule capability docs because Anthropic just announced a change") via the same `/schedule run-now` surface.
- ODD: ACs are outcome-shaped — "after δ lands, a fresh Class A entry for a newly-released Anthropic feature appears in the corpus within one cadence-cycle of its release"; "an owner ack on a pending delta merges it within one session"; "a budget-line overage defers the next refresh."

**Sealed-fence:** new code lives inside `knowledge-server/` (added in β; δ extends it) and `personas/<handle>/capability-sources.yaml` (workspace content). The `/schedule` binding is workspace-authored. No source-edit outside the persona-layer + workspace-bootstrap + knowledge-server fence.

**Cost:** medium. ~1–2 weeks build wall-clock. The Class A projection transform is the bulk of the work; the Class B community-survey scope is a thin wrapper around `WebSearch` + `WebFetch` + a summariser prompt.

### 7.4 Amendment γ — dynamic session-start contributor (optional, post-corpus-stabilisation)

**Scope:**

- New contributor in `primary-persona/src/` registered against D8's session-level surface, emitting "given recent scope-of-work activity, the capabilities most likely relevant today are..."
- The contributor reads the activity-type→capability mapping from a workspace-authored `personas/<handle>/capability-routing.yaml` (or similar) — workspace content, not pos-v2 core.
- The mapping authoring is a separable workstream; the contributor ships with a minimal default mapping and grows.

**Lens reads:**

- L1: composes on D8's contributor surface, scope-of-work's pyee event log, the knowledge-server. All existing primitives.
- L2: primary-persona test — translation burden drops further; the user gets contextually-relevant capability surfacing without asking for it.
- ODD: ACs are outcome-shaped — "given a workspace with N recent scope-of-work activations, the contributor emits a non-empty capability-routing block with at most M capabilities named."

**Sealed-fence:** primary-persona/ contributor surface (sealed; an additive contributor registration is inside the fence).

**Cost:** small. ~3–5 days build wall-clock. Contributor is mechanical; the value is in the mapping, which is workspace authoring.

### 7.5 Sequencing rationale

- α first because it's high-leverage and ships in days. Even without the server, the persona acquires the leverage rule + a starter index. This is the cheapest possible win.
- β next because it removes the staleness pressure: docs are now centrally managed, refreshable, retrievable. β is **two-class-aware from day one** — the schema partitions Class A and Class B; the Stop-hook mirror subscriber for internal Class B accrual lands here. Class B retrieval works on β's day-one corpus (the seed entries from α + accruing entries from the mirror subscriber).
- δ third because it requires β's two-class schema as the substrate for the deterministic-projection refresh and the community-survey channel's merge target. δ is the structural answer to the locked-by-Luke 2026-04-26 currency requirement; once δ lands, the corpus is self-maintaining for both classes.
- γ last because it depends on a stable corpus (β + δ) and a stable activity-type vocabulary (which the workspace develops over use).

The four-amendment program is the minimum that addresses all three locked requirements (translate-leverage, two-class corpus, currency). The previous three-amendment program left currency to a future "Idea 1 / Step 4" placeholder; the 2026-04-26 lock promotes that placeholder to a first-class amendment δ.

---

## 7bis. Currency mechanism design (locked by Luke 2026-04-26)

> **Forward-pointer (2026-06-11):** δ's intent realised by
> claude-leverage-program Slice 1 (`framework/tools/capability-refresh/`;
> plan `docs/plans/claude-leverage-program-s1-currency.md`); the stale
> substrate bindings below were re-derived there (cloud routine primary /
> launchd fallback; cadence table unchanged).

Both classes must stay current. The mechanisms are structurally different; this section names each one and the cross-class invariants.

### 7bis.1 Class A currency — deterministic projection refresh

**The mechanism.** A scheduled job, dispatched via the `/schedule` skill, projects each Class A document from its canonical upstream source on a fixed cadence. The projection is deterministic (no LLM call required for the body; LLM judgement enters only at the curated `[user-intent phrasings]` overlay, which persists across refreshes).

**Cadence — recommended (locked, not a decision):**

| Source | Cadence | Rationale |
|---|---|---|
| Anthropic release notes feed | Daily | New features ship within hours; daily catches them within a session of release. |
| Claude Code documentation index | Daily | Same volatility as release notes. |
| Skill marketplace listing | Daily | New skills appear without release-note signal. |
| Long-form Anthropic docs (API reference, prompt-caching guide, etc.) | Weekly | Lower volatility; weekly is sufficient. |
| pos-v2 component docs (Class A-prime) | On-merge | Sealed-component docs change at amendment-merge time; refresh is git-hook-triggered, not cron-triggered. |

Workspace-overridable via `personas/<handle>/capability-sources.yaml`.

**Trigger surface — recommended (locked):** `/schedule` skill. Per Lens 1, the cron-shaped scheduler is Claude-native and should be leaned on, not re-implemented. Workspace-bootstrap registers the schedule entries when the workspace is initialised; the user does not author them by hand. A `/schedule run-now` invocation lets the persona force a refresh on demand (e.g., "Anthropic just announced a new hook event; refresh capability docs").

**Why not a periodic background scope?** A scope-of-work activation is the right shape for stateful long-running work; a refresh is fire-and-forget per cadence-tick. `/schedule` matches the shape; scope-of-work would be an over-reach.

**Why not workspace-bootstrap-time fetch + on-demand re-fetch?** Bootstrap-time fetch is fine for the initial load; "on-demand only" loses the unattended currency that Luke's lock requires. The persona shouldn't have to remember to refresh.

**Diff + merge flow.** Each refresh produces a structured delta. Content changes (an entry's body diff) auto-merge. Additions (a new feature) and deprecations (a removed feature) get an owner-pairing prompt (Telegram or in-session) for one-line ack. Auto-merge with deprecation-skip is the default for fully-headless operation (Telegram-only Luke); the pairing is anti-deskilling, not gating.

**Authoring shape consistency.** The deterministic transform never modifies a Class B entry. Class B's curated content is independent of Class A's projection. A Class A doc's `[user-intent phrasings]` overlay is preserved across refreshes (it's stored alongside the projection target, not inside the projected body).

### 7bis.2 Class B currency — synthesis + curation, three channels

Class B does not project from a canonical source; it accrues from many. Three channels evaluated; **the recommendation is the hybrid (all three):**

#### Channel 1 — Periodic community-survey scope (background-agent dispatch)

**Shape.** A weekly background-agent dispatch runs a community-survey prompt:
1. Web-search across Reddit (`r/ClaudeAI`, `r/ClaudeCode`), X/Twitter (Claude-Code-builder cluster), GitHub issues, blog feeds.
2. Summarise observed patterns in the past N days.
3. Cross-reference against the existing Class B corpus (via the knowledge-server's `search` tool).
4. Propose a delta — new entries, supersession candidates, conflict-with-existing flags.
5. Owner-pair the delta; merge on ack.

**Pros.** Catches the highest-volume folk-knowledge surface. Background-agent dispatch matches Luke's "background-agents-by-default" preference and "fire-and-forget for cost." The owner-pairing on merge is anti-deskilling.

**Cons.** Single-source bias if the survey prompt is poorly authored. Mitigated by including ≥3 source surfaces and requiring cross-source confirmation for high-confidence entries. Cost is non-trivial (weekly background dispatch with web-search + summarisation); cost-governance composition gates this.

**Recommendation: include in δ.**

#### Channel 2 — Internal Stop-hook learning-extraction with `source_description="capability-best-practice"`

**Shape.** When a pos-v2 session executes a pattern that demonstrably worked (the persona observed a successful background-agent dispatch, a `/schedule` binding that hit its target, an MCP composition that returned the right shape), the Stop-hook learning-extractor (already part of memory-system's Stream A per the existing roadmap) emits an episode with `source_description="capability-best-practice"`. β's mirror subscriber (§7.2) picks up these episodes and writes them as Class B entries.

**Pros.** First-party-validated content — the patterns that enter the corpus are ones that actually worked in Luke's workflow. No parallel-memory chaos: the same Stop-hook pipeline writes both interaction memory (Stream A) and capability-best-practice (this channel); only the `source_description` differs. Composes on existing memory-system primitive (Lens 1).

**Cons.** The extraction-prompt has to be tuned to recognise "this was a capability pattern that worked" as a distinct extraction shape from "this was a fact about the user." Authoring effort lands in β's mirror-subscriber design; the prompt-tuning is method-level for β's plan-author, not a research decision.

**Recommendation: include in β + δ. Already specified in β's scope per §7.2.**

#### Channel 3 — User-driven capture

**Shape.** Luke says (in-session or via Telegram): "Eve, remember I should always use background agents for research." The persona recognises this as a Class B authoring intent (distinct from a fact-about-Luke that goes to Stream A) and writes the episode with `source_description="capability-best-practice"`. β's mirror subscriber promotes it to a Class B entry.

**Pros.** Highest-trust source by definition (the user has lived experience and is asking for it to be persisted). Zero infrastructure beyond what β already provides. Matches the Luke-already-uses-this pattern (his `MEMORY.md` is full of these statements).

**Cons.** Requires the persona to disambiguate "remember-X-about-me" (Stream A) from "remember-X-is-the-right-pattern" (Class B). Disambiguation prompt-tuning lives in the persona's prompt.md rather than in β's code (it's a recognition rule, not a parsing rule). This is workspace authoring, not core authoring.

**Recommendation: include in β. The persona's prompt.md spine (α) gets a "when the user articulates a pattern, capture as Class B; when the user articulates a preference about themselves, capture as Stream A" rule.**

#### Hybrid — all three channels (recommendation)

**Why all three:** different freshness profiles + different trust-marker signals + different volume profiles. Channel 1 (community survey) catches breadth; Channel 2 (internal) catches first-party-validated depth; Channel 3 (user-driven) catches owner-articulated truth. A single channel alone has known failure modes (1 alone: community noise; 2 alone: small-sample bias from one user's session history; 3 alone: bottlenecked on owner attention). The three together cover each other's blind spots.

**Trust-marker rubric (Class B entry metadata):**
- `sources_count`: how many sources confirmed the pattern (Channel 1: ≥3 community sources; Channel 2: 1 — the internal observation; Channel 3: 1 — the user statement).
- `validation_count`: how many subsequent observations validated the pattern (incremented by Channel 2 each time the pattern is observed working again).
- `supersession_chain`: pointer to entries this entry refines or replaces.
- `owner_acked`: boolean — was this entry owner-paired before merge? Channel 1: required-true; Channels 2 and 3: implicit-true (owner-action-driven).

The retrieval surface ranks by a fused score (semantic relevance + trust signal). High-`validation_count` entries surface ahead of single-observation entries when relevance ties.

### 7bis.3 Cross-class invariants

- **No cross-class write.** Class A's deterministic refresh never writes to Class B; Class B's accrual channels never write to Class A. Class boundary is enforced at write time by the knowledge-server's resource-path partition.
- **Cross-class read.** The persona's prompt.md spine names the **paired-fetch convention**: when a Class A primitive has Class B entries attached (linked by `[primitive: <name>]` cross-reference), the persona fetches both before planning. β's `search(query)` tool implements the pairing automatically.
- **Cost-governance composition.** Both channels are budget-line consumers (cost-governance sealed primitive). Class A's daily projection is bounded; Class B's weekly survey is bounded; Class B's internal channel is opportunistic (no cost above what Stream A already incurs); Class B's user-driven channel is sub-cent per capture. Total annual cost (under Claude Max): negligible.

### 7bis.4 What is NOT in the currency mechanism

- **A new top-level objective.** The currency mechanism ladders to existing Knowledge-accrual objectives (R3 process-of-arrival, R5 4-dimensional temporal, R6 supersession) and the existing Tiered-determinism architecture (Class A is layer-1 deterministic projection; Class B's owner-gating is layer-2 rubric). No new top-level objective required. Per Luke's hard requirement (he must be involved in defining new top-level objectives), this is the correct outcome — the mechanism realises existing objectives, it does not introduce new ones. **Halt-condition not triggered.**
- **A second MCP server.** Both classes live on β's single knowledge-server. Partition is a schema decision, not a substrate decision.
- **A separate amendment ε for Class B accrual.** The accrual channels compose on β's existing surface (Stop-hook subscriber, prompt.md disambiguation rule) and δ's existing surface (background-agent dispatch via `/schedule`). Splitting Class B accrual into its own amendment ε would duplicate the cost-governance composition and the owner-pairing flow. **Recommendation: keep Class B accrual integrated; do not split into ε.** Alternative ε is viable if owner prefers staged delivery — escape hatch documented in §9.7.

---

## 8. Three-lens read of the recommended program (whole-program)

### 8.1 Lens 1 — Claude leverage

Every layer of the recommendation composes on existing primitives:

- prompt.md spine — composes on Claude Code's persona-prompt + agent-md projector (amendment #35).
- MCP knowledge-server — composes on Claude Code's MCP server registration + tool-call surface + resource surface. Mirrors memory-graphiti's shape.
- Class A currency refresh (δ) — composes on the `/schedule` skill (Claude-native cron-shaped scheduler) + cost-governance budget-line (sealed pos-v2 primitive).
- Class B accrual channels — Channel 1 (community survey) composes on background-agent dispatch + WebSearch + WebFetch (all Claude-native). Channels 2 and 3 compose on memory-system's Stop-hook learning-extraction surface (sealed pos-v2 primitive) with `source_description` partitioning.
- Session-start contributor (γ) — composes on D8's contributor surface + scope-of-work's pyee subscription.

**No re-implementation. No new persona-side primitives that don't exist already. The whole program is composition. The currency-mechanism extension specifically composes on the `/schedule` skill and the existing Stop-hook surface — both Claude-native and sealed-pos-v2 primitives respectively, no new substrate.**

### 8.2 Lens 2 — Harness + primary-persona value

**Primary-persona test:** **PASS, load-bearing.** The leverage rule is the prime expression of the translation-layer value prop per the owner's directive. Without this work, every Lens-1-shaped translation is best-effort against the model's training-cut knowledge. The currency mechanism extends the test: the persona is not just leveraging at session-start, it's leveraging against an *up-to-date* surface — the user's translation burden of "is this primitive current?" drops to zero.

**Harness test:** **PASS.** The knowledge-server is a primitive every future feature draws against — it IS the toolkit the persona invokes when asked "what should I use here?" The two-class partition makes the toolkit richer (canonical + practitioner-validated) without making it harder to use; the paired-fetch convention surfaces both classes when relevant.

### 8.3 Lens 3 — ODD authoring

ACs are outcome-shaped at every amendment level (state-of-the-world after the work lands; method-of-arrival is the builder's call). §2.5 reverse-direction surface is bounded: each amendment touches a known small set of components with no cross-fence reach.

**§2.5 trace for the extension** — every new code path / amendment / mechanism in §2.6 + §7bis maps to a named objective:

- Two-class corpus partition (§2.6) → ladders to v1.0 Knowledge-accrual objective + R3 (process-of-arrival capture, the trust-marker rubric on Class B is the structural realisation) + R5 (4-dimensional temporal model — Class A's `source_fetch_ts` and Class B's `validation_count` are temporal-validity surfaces) + R6 (supersession refined — Class B's `supersession_chain` is the explicit realisation).
- Class A currency refresh (§7bis.1) → ladders to Tiered-determinism layer-1 (deterministic projection is layer-1 by definition) + Knowledge-accrual (refresh keeps the accrued corpus current) + non-tech-users (auto-merge with owner-pairing on novelty matches the "anti-deskilling principle" objective without requiring user technical literacy).
- Class B accrual hybrid (§7bis.2) → ladders to Knowledge-accrual + R3 (process-of-arrival is precisely what Channel 2 captures) + non-tech-users (Channel 3's user-driven capture removes the translation burden of "where do I write down what I learned?").
- Cross-class invariants (§7bis.3) → ladders to Tiered-determinism (no-cross-class-write is a structural enforcement, not advisory) + Knowledge-accrual (paired-fetch is the realisation of "knowledge surfaces when relevant").

**No new top-level objective is introduced.** The extension realises existing objectives more completely; it does not add objectives. (Halt-condition explicitly checked — see §7bis.4 and §9.7.)

---

## 9. Halt-and-surface — surfaces the owner should rule on

### 9.1 H-α — Strawman is rejected; owner intuition is honoured

The strawman (graphiti seed) is rejected as wrong-shape, BUT the owner's underlying intuition (capability knowledge needs to be retrievable contextually) is correct and is what the recommendation builds. The recommendation is responsive to the directive; it just routes the implementation to substrates that fit.

If the owner specifically wants graphiti seeding regardless of the §3 / §4 analysis, the cost-realism is real (~80 min wall-time bulk-load, $1 pay-per-token, ~95 min sequential), and it doesn't structurally break anything — but the retrieval shape will underperform an MCP knowledge-server for the daily-briefing-type prompts. **Owner ruling needed: accept the recommendation, or accept the strawman with eyes open?**

### 9.2 H-β — The "leverage rule" landing is partially personality

The declarative paragraph in prompt.md is workspace content (per the no-personas-in-core rule). pos-v2 core can ship the *template* (a recommended paragraph in the persona-template) but not the active prompt content. **Owner ruling needed: should pos-v2 ship the leverage paragraph as a recommended-template inclusion, or leave it entirely to workspace authors? Recommendation: ship as a recommended template with a comment explaining why.**

### 9.3 H-γ — Idea 1 / Step 4 (refresh automation) is now amendment δ

**Updated 2026-04-26 with the currency-mechanism extension.** The previous version of this halt-condition flagged refresh as out-of-scope future work. The 2026-04-26 lock promotes refresh to a first-class amendment (δ in §7.3) with a designed Class A projection mechanism + Class B accrual hybrid. **Owner ruling needed only if the four-amendment program shape is unacceptable; the recommended shape is documented in §7 + §7bis. No discretionary decision is left to the owner on the mechanism itself — the cadences, channels, and trust-marker rubric are recommended (locked, see §7bis.1 cadence table and §7bis.2 channel hybrid).**

### 9.4 H-δ — Spec-objective ladder check

The work ladders up to:

- v1.0 user-facing layer: "every interactive session starts with the primary persona present" — implicitly requires the persona to be *effective*; effectiveness depends on capability awareness. The spec doesn't name capability-awareness explicitly, which is a gap (see §10).
- VALUE_PROPOSITION's primary-persona test (translation burden) — directly named.
- FUTURE_IDEAS Idea 1 / Step 1 — directly named.
- v1.0 Knowledge-accrual + R3 + R5 + R6 (process-of-arrival, 4-dimensional temporal, supersession refined) — the two-class partition + currency mechanism realise these objectives more completely than the original Idea 1 framing did.
- Tiered-determinism (layer-1 deterministic projection for Class A; layer-2 rubric for Class B trust-marker; layer-3 LLM judgement for community-survey synthesis under owner-gating) — the program is a textbook tiered realisation.
- Non-tech-users (auto-merge default, owner-pairing for novelty, anti-deskilling pairing on auto-create) — the user is never required to understand the projection transform or the Class B trust-marker; the persona handles both behind the curtain.

**The extended work ladders up cleanly to existing v1.0 objectives — Knowledge-accrual + Tiered-determinism + Non-tech-users — with no new top-level objective required. The original gap (capability-awareness not named explicitly in the spec) remains; recommend authoring a docs-only addendum as part of α.**

### 9.5 H-ε — No ODD violations surfaced

No source code is touched outside the persona-layer + workspace-bootstrap + new component fence (`knowledge-server/`). No surrounding-code §2.5 violations spotted. No silent-exception branches introduced. The extension preserves the §2.5 reverse-direction discipline: every new mechanism in §7bis traces to a named v1.0 objective per §8.3.

### 9.6 H-ζ — Idea-N candidate

If the owner wants this research to *land as* an Idea-N entry rather than ride on Idea 1's umbrella, it could become Idea 20 — "persona capability knowledge grounding (prompt.md spine + MCP knowledge-server + two-class corpus + dual-channel currency)" — with explicit cross-references to Idea 1. **Owner ruling needed: graduate to Idea 20, or stay nested under Idea 1?**

### 9.7 H-η — Split Class B accrual into a separate amendment ε? (new)

The recommendation in §7 + §7bis keeps Class B accrual integrated into β + δ. The alternative — a standalone amendment ε that adds Class B accrual after δ ships — is viable but heavier (duplicate cost-governance composition, duplicate owner-pairing flow). **Recommendation: do not split.** Two scenarios where splitting would be the right call:

1. β + δ is too large to ship as two amendments and would exceed amendment-velocity budgets. (Unlikely — β is ~1–2 weeks, δ is ~1–2 weeks; both are within the established amendment-size envelope.)
2. The owner wants to validate Class A currency before committing to Class B accrual infrastructure. (This is the legitimate split scenario — if owner is uncertain whether the Class B channels will accrue useful content at the recommended cadence, deferring them to ε after δ is observed working in practice is conservative and reversible.)

**Owner ruling needed: integrated (β + δ as recommended), or split (ε after δ for staged validation)?**

---

## 10. Out of scope

- **Authoring the corpus.** The recommendation names the corpus shape (two classes, partition schema) and the inventory upper bound; actual doc authoring is part of amendment α + ongoing accrual through δ's channels.
- **MCP knowledge-server detailed design.** Server module layout, sqlite schema, embedding-store choice, `search` tool's exact contract, the `BestPracticeMirrorContributor` implementation details. Method-level decisions for the β plan-author.
- **Class A projection-transform implementation details.** The fetch-parse-normalise-emit pipeline for each canonical source surface (release notes feed format, doc index format, skill marketplace format). Method-level decisions for the δ plan-author.
- **Class B community-survey prompt authoring.** The exact prompt that drives Channel 1's background-agent dispatch — source list, summarisation rubric, cross-reference instructions. Method-level decisions for the δ plan-author with workspace-author input.
- **Activity-type → capability mapping.** The dynamic γ contributor's mapping is workspace authoring, not part of this research.
- **Lens-1-enforcement at research-plan-author time.** Idea 1 / Step 3 (the structural-enforcement gate that refuses research plans without Lens-1 sections) is a separate, complementary workstream; out of scope here.
- **Plan-docs for amendments α, β, δ, γ.** Per dispatch directive — multi-amendment program, name + sequence in research, leave plan-docs for follow-on dispatches. (Was three amendments before the 2026-04-26 currency lock; now four with δ promoted from out-of-scope to in-program.)
- **Spec amendment naming capability-awareness explicitly.** Recommended as a docs-only addendum authored as part of α (per §9.4); the addendum itself is not authored by this research.

---

## 11. References

- `docs/VALUE_PROPOSITION.md` — primary-persona translation-layer test; the prime objective this work serves.
- `CLAUDE.md` — the three lenses (Claude leverage, primary-persona value, ODD authoring).
- `docs/STATE.md` — sealed-component list.
- `docs/FUTURE_IDEAS.md` Idea 1 — the four-step three-lens enforcement programme; Step 1 is the capability map, which this work realises with a substrate decision the original idea didn't make.
- `docs/spec/pos-v2-objectives-spec.md` — v1.0 / v1.1 / v1.2 contracts; the spec ladder.
- `primary-persona/src/context_composer.py` — D8's contributor surface; the structural attach point for the dynamic γ contributor.
- `primary-persona/src/agent_md.py` — amendment #35's projector; how prompt.md becomes the agent file.
- `primary-persona/src/memory_consumer.py` — D7's memory-retrieval contributor; the precedent for any MCP-backed retrieval contributor (the γ contributor would mirror its shape if it does live retrieval rather than static).
- `memory-system/src/service.py` — FastMCP precedent for the β knowledge-server.
- `memory-system/.venv/lib/python3.13/site-packages/graphiti_core/graphiti.py:1037` — `add_episode_bulk`; what makes the strawman 30–50 % cheaper than naive sequential ingest, but doesn't fix the substrate-fit problem.
- `docs/plans/research/amendment-33-memory-consumer-wiring-research.md` §3.2 — empirical 113 s figure for realistic-payload extraction.
- `docs/plans/research/memory-system-live-client-and-stop-hook-write-research.md` — sibling pattern: the persona-side MCP client wiring β would compose on top of.
- `docs/plans/research/bootstrap-progress-statusline-research.md` — sibling pattern: workspace-scoped statusLine, similar shape to a workspace-scoped knowledge-server.
- `docs/FUTURE_IDEAS.md` Idea 13 — two modes (NORMAL USE / DEV MODE); the activity-type vocabulary the γ contributor draws against may differ across modes.
- `docs/odd-methodology.md` §2.5 — the reverse-direction discipline this extension preserves; every new mechanism in §7bis traces to a named v1.0 objective per §8.3.
- `docs/spec/pos-v2-objectives-spec.md` — Knowledge-accrual (R3 process-of-arrival, R5 4-dimensional temporal, R6 supersession refined) and Tiered-determinism objectives the currency-mechanism extension realises more completely than the original Idea 1 framing.
- Anthropic's `/schedule` skill — the Claude-native cron-shaped scheduler δ composes on for Class A daily refresh; per Lens 1, this is leaned on rather than re-implemented.
- Anthropic's `WebSearch` + `WebFetch` tools — the Claude-native surfaces δ's Class B Channel 1 (community-survey background agent) composes on.
- `~/.claude/projects/-Users-lukeivers-pos3/memory/MEMORY.md` — Luke's existing Class B-shaped statements (background agents for research, fire-and-forget for cost, etc.) ladder cleanly to seed Class B entries authored in α.
