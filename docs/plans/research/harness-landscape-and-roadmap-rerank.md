# Harness Landscape Research + Gap Analysis + Roadmap Re-rank

**Authored:** 2026-05-08.
**Plan-doc authority:** `docs/plans/research/harness-landscape-and-roadmap-rerank-plan.md`.
**Composes with:** `docs/release-roadmap.md` (target ordering this artefact may propose adjusting), `docs/VALUE_PROPOSITION.md` (the prioritization filter), `docs/release-versioning-policy.md`, `docs/odd-semver-pinning.md`.
**Window:** 2026-04-22 → 2026-05-08 (past two weeks; older shipments are background context only).
**Architectural floor (non-negotiable across this artefact):** subscription-only via `claude -p`; no Anthropic API key anywhere; no migration to multi-provider routers; software-as-deliverable framing (loam exists to help people use LLMs to build software).

---

## §1 Stage 1 — Recent shipments and developments (past ~two weeks)

The window 2026-04-22 → 2026-05-08 is unusually busy for harness/agent infrastructure: Code w/ Claude 2026 (San Francisco, 2026-05-06) anchored Anthropic's Managed Agents push (Outcomes, Multi-Agent, Dreaming, Routines, Code/Security Review, Webhooks); LangGraph cut a 1.x point release; CrewAI shipped 1.13.0; Microsoft Agent Framework 1.0 GA'd as the merged successor to AutoGen + Semantic Kernel; Cursor 3.x added an Agents Window and `/multitask` async sub-agents; OpenAI Codex CLI persisted goals and added a hooks browser; GitHub Copilot landed agent-level browser/terminal sharing and BYOK; Replit shipped Agent 4 with Power-mode running on Opus 4.7. The list below is a tabular shipment register; trend distillation in §2.

| # | Source / project | Date | Shipment | One-line | URL |
|---|---|---|---|---|---|
| 1 | Anthropic — Managed Agents | 2026-05-06 (Code w/ Claude) | **Outcomes** (public beta) | Define a markdown rubric; harness provisions a separate-context-window grader that iterates the agent until rubric satisfied (default 3 / max 20 iterations). +10pp success rate on Anthropic internal benchmarks. | <https://platform.claude.com/docs/en/managed-agents/define-outcomes> |
| 2 | Anthropic — Managed Agents | 2026-05-06 | **Multi-agent orchestration** (public beta) | Lead agent delegates to specialists in parallel with persistent event logs; typed task surface. | <https://platform.claude.com/docs/en/managed-agents/overview> |
| 3 | Anthropic — Managed Agents | 2026-05-06 | **Dreaming** (research preview) | Scheduled background process reviews past sessions to find patterns and self-improve agent memory. | <https://platform.claude.com/docs/en/managed-agents/dreams> |
| 4 | Anthropic — Claude Code | rolling Apr→May | **Routines** | Higher-order async prompts; "wake up to PRs ready to merge." | <https://code.claude.com/docs/en/routines> |
| 5 | Anthropic — Claude Code | rolling | **Code Review + Security Review** | Built-in automated review surfaces with confidence ratings + targeted patches. | <https://code.claude.com/docs/en/code-review> |
| 6 | Anthropic — Claude Code | Apr–May | **Hooks + plugins improvements** | `PostToolUse` can replace tool output for all tools (was MCP-only); `duration_ms` exposed; `--plugin-dir` accepts `.zip`; pinned plugins auto-update to highest satisfying tag; new skill search box. | <https://code.claude.com/docs/en/changelog> |
| 7 | Anthropic — Managed Agents | 2026-05-07 | **Webhooks** | Session + vault lifecycle events delivered to subscriber URLs. | <https://releasebot.io/updates/anthropic> |
| 8 | LangChain | 2026-05 | **LangGraph 1.x point releases** (1.1.7a1, SDK 0.3.14, 2026-05-05) | Standard JSON Schema support; Deep Agents v1.9.0 alpha adds *async sub-agents* that launch non-blocking background tasks. | <https://changelog.langchain.com/> |
| 9 | LangChain | 2026-04 newsletter | **AskGenie + Cisco agentic-engineering case studies** | External adoption signal — production-grade multi-agent stacks reporting concrete ROI (Cisco: 93% time-to-root-cause reduction, 200+ engineering hours saved/month). | <https://www.langchain.com/blog/april-2026-langchain-newsletter> |
| 10 | CrewAI | 2026-04 | **CrewAI 1.13.0** | A2UI extension v0.8/v0.9 + schemas; lazy event bus reduces overhead; *checkpoint forking with lineage tracking*; reasoning-token + cache-creation-token tracking. | <https://docs.crewai.com/en/changelog> |
| 11 | Microsoft | 2026-04-07 | **Microsoft Agent Framework 1.0 GA** | Production-ready merger of Semantic Kernel + AutoGen; AutoGen now in maintenance mode. Multi-pattern orchestration (sequential, concurrent, handoff, group chat, Magentic-One); checkpointing + pause/resume + human-in-loop. A2A + MCP cross-runtime interop. | <https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/> |
| 12 | Cursor | 2026-04-02 | **Cursor 3.0 — Agents Window** | Run many agents in parallel across repos/environments — locally, in worktrees, in cloud, on remote SSH. Structural shift in what "Cursor" means. | <https://cursor.com/changelog/3-0> |
| 13 | Cursor | 2026-05-06 | **Cursor 3.3 — `/multitask` + context-usage breakdown** | Async sub-agents in the editor (parallelize requests rather than queue); per-agent context-usage telemetry. | <https://cursor.com/changelog> |
| 14 | OpenAI | 2026-04-30 | **Codex CLI v0.128.0** | Persisted `/goal` workflows; `codex update`; configurable TUI keymaps; expanded permission profiles. | <https://developers.openai.com/codex/changelog> |
| 15 | OpenAI | 2026-05-07 | **Codex CLI v0.129.0** | Modal Vim composer; redesigned workflow picker; in-TUI `/hooks` browser; theme-aware status line; plugin management upgrades. GPT-5.5 recommended. | <https://blakecrosley.com/guides/codex> |
| 16 | GitHub | 2026-05-06 | **Copilot April→May releases** | Semantic search across workspaces; `/chronicle` chat history; agents read/write existing terminals; integrated browser tab-sharing as agent context; remote Copilot CLI control from github.com / mobile; **BYOK API keys** (OpenRouter, Foundry, Google, Anthropic, OpenAI). | <https://github.blog/changelog/2026-05-06-github-copilot-in-visual-studio-code-april-releases/> |
| 17 | Replit | 2026-04-02 (Dev Day) | **Agent 4 + Code Repair** | Power mode runs on Claude Opus 4.7; Lite/Economy/Power segmented selector; Code Repair model auto-fixes 60% of LSP errors. | <https://blog.replit.com/introducing-agent-4-built-for-creativity> |
| 18 | Replit | 2026-04-22 | **Agent on any framework** | Replit Agent works across all dev frameworks (was Replit-stack-only); Security Agent + CVE Auto-Protect ship. | <https://blog.replit.com/agent-on-any-framework> |
| 19 | Aider | rolling Apr–May | **New model support + `--add-gitignore-files`** | Gemini 2.5 family + thinking-token plumbing; o-series (o1-pro, o3-pro); Deepseek max-tokens 65536; polyglot benchmark refresh (GPT-4.1 at 88% pass). | <https://aider.chat/HISTORY.html> |
| 20 | Cline | 2026-04 | **Cline 3.78 + 5M install milestone** | "Spend Limit Reached" UI prevents runaway agent draining accounts (daily/monthly caps). 5M+ extension installs (May); GitHub stars ~61k. Multi-IDE expansion (JetBrains, Zed, Neovim, preview CLI). | <https://github.com/cline/cline> |
| 21 | Cognition (Devin) | 2026-04-15, 2026-04-27 | **Manage-Devins + agents-tab + auto-merge** | Devin breaks large tasks down and *delegates to a team of managed Devins working in parallel*; Reviews tab groups Devin Review spend by repo; auto-merge from review. | <https://cognition.ai/blog/devin-can-now-manage-devins> |
| 22 | HuggingFace | 2026-04 | **smolagents v1.19.0 + vision web-browsing** | Streaming refactor; output tracking; vision-enabled web-browsing agents (open browser, scroll, click, navigate). | <https://github.com/huggingface/smolagents/releases> |
| 23 | mem0 / Cloudflare | rolling | **Agent-memory ecosystem maturation** | mem0 covers 21 frameworks / 19 vector stores / 3 hosting models; Cloudflare ships Agent Memory as a managed service; "graph memory in production" goes from experimental (2024) to default (early 2026). | <https://mem0.ai/blog/state-of-ai-agent-memory-2026>, <https://blog.cloudflare.com/introducing-agent-memory/> |
| 24 | Academic | Mar–Apr 2026 | **ACE — Agentic Context Engineering** (arXiv 2510.04618 + survey threads) | Treats contexts as evolving playbooks updated via Generator-Reflector-Curator cycle; prevents brevity bias and context collapse. Sets up a methodology layer above prompt engineering. | <https://arxiv.org/abs/2510.04618> |
| 25 | Anthropic | 2026-05-06 | **Doubled rate limits + Advisor pattern** | 5-hour Claude Code limits doubled; peak-hour reductions removed; Opus API rate limits "considerably" raised. Advisor: smaller models receive on-demand advice from Opus (~5x cost reduction at near-Opus quality, per Artiverse). | <https://www.cnbc.com/2026/05/06/anthropic-spacex-data-center-capacity.html>, <https://www.artiverse.ca/highlights-from-anthropics-code-w-claude-2026-conference/> |

**Total distinct shipments captured:** 25 (>10 floor met). Excluded items: SWE-bench Pro / Verified leaderboard movements (background — Claude Mythos Preview at 93.9% verified, Opus 4.7 Adaptive at 87.6%, GPT-5.3 Codex at 85% per llm-stats.com on 2026-05-07 — *unverified beyond aggregator*; flagged in §4 for direct check). Anthropic Mythos Preview red-team release noted but not user-facing on subscription path.

**Citation honesty.** Dates marked "rolling Apr–May" are bundled cadence releases; specific point versions in cells with explicit dates were verified against the named source. The two SWE-bench numbers came from one aggregator and are flagged unverified-against-primary in §4's tension. The +10pp Outcomes claim is Anthropic-internal benchmark, not third-party reproduced — surfaced as Anthropic-claim in §2.

---

## §2 Stage 2 — Trend distillation

From the §1 surface, six trend lines emerge with two-or-more shipment evidence. Two more (T7, T8) are surfaced as "marginal" — single-source or weak — to keep this honest.

### T1 — Async sub-agent fan-out becomes the default agent shape

**Evidence:** Cursor 3.0 Agents Window (#12), Cursor 3.3 `/multitask` (#13), LangGraph Deep Agents 1.9.0 async sub-agents (#8), Anthropic Managed Agents Multi-Agent (#2), Devin's Manage-Devins (#21), Microsoft Agent Framework 1.0 multi-pattern orchestration (#11). Six independent shipments.

**Framing for harness builders:** Single-thread ReAct loops are giving way to fan-out architectures where the planner dispatches typed sub-tasks to parallel workers and a judge step decides completion. This is the swarming pattern at industry scale — and it is now a *table-stakes* surface, not a differentiator.

### T2 — Rubric-driven grading replaces single-prompt evaluation

**Evidence:** Anthropic Outcomes (#1), Anthropic Code Review + Security Review (#5), Cursor Bugbot at near-80% resolution rate (#13's neighbour cell), CrewAI checkpoint-forking-with-lineage (#10), ACE Generator-Reflector-Curator (#24).

**Framing:** The pattern is *generate → grade in a separate context window → revise on rubric gaps → repeat*. ODD's authoring-time AC discipline is the same conceptual move pulled to plan-time; Outcomes pulls it to runtime. Two surfaces of the same idea — and the runtime surface is now a first-party Anthropic primitive for the API audience.

### T3 — Memory and persistence go from experimental to assumed

**Evidence:** Anthropic Dreaming (#3), Cloudflare Agent Memory (#23), mem0 production maturation across 21 frameworks (#23), GitHub Copilot `/chronicle` (#16), Cursor context-usage breakdown (#13), Codex `/goal` persisted workflows (#14, #15).

**Framing:** "Goldfish-memory raw LLM" is no longer the default; harnesses are expected to ship with persistence, audit, and rollback. mem0 / Cloudflare make it commodity infrastructure. The differentiation now is *how* memory composes with planning — not whether memory exists.

### T4 — Cost-governance UI goes from afterthought to user-visible primitive

**Evidence:** Cline Spend Limit UI (#20), Cursor per-agent context telemetry (#13), Anthropic doubled rate limits + Advisor pattern (#25), Devin Reviews-tab spend grouping (#21), CrewAI lazy event bus + reasoning-token tracking (#10).

**Framing:** Users now expect to *see* what an agent costs and to *cap* what it can spend. The harness owes the user this visibility. Loam's `safety_profile` + dry-run primitive (v0.1.6) is in this lineage; the surface needs to keep up with what users can see in adjacent products.

### T5 — Plugin / skill / hook ecosystems deepen across all major harnesses

**Evidence:** Claude Code skill search box + plugin .zip + auto-update tags + richer hooks (#6), Codex `/hooks` browser + plugin workflows (#15), GitHub Copilot custom-agent generation (#16), Cursor canvases + custom UI components (#12 neighbours), Microsoft Agent Framework MCP/A2A interop (#11).

**Framing:** Every major harness is investing in *user-extensible behavior surfaces*, and the UX bar is moving fast — discovery (skill search), packaging (.zip plugins), introspection (in-TUI hooks browser), composition (custom-agent generation). Loam's SKILL ecosystem is conceptually well-positioned but the discovery + introspection UX is currently sparse.

### T6 — Background / scheduled / async work is the default execution mode

**Evidence:** Anthropic Routines (#4), LangGraph Deep Agents async (#8), Cognition Manage-Devins (#21), Cursor `/multitask` (#13), GitHub Copilot remote CLI control from mobile + persistent debug logs (#16), Anthropic Dreaming as scheduled background (#3).

**Framing:** "Sit and watch one agent execute" is becoming "fire many, walk away, come back to results." Loam's "background-agent default" memory rule is on-trend; what's missing in loam relative to peers is a *user-visible inventory* of in-flight background work and a *single-pane status* surface.

### T7 (marginal) — BYOK / multi-provider routing as a paid-tier feature

**Evidence:** GitHub Copilot Business+Enterprise BYOK to Anthropic / OpenAI / Google / OpenRouter (#16). Single-source within window. Aider supports many providers (#19) but that's long-standing.

**Framing:** Industry direction is *toward* BYOK. Loam's subscription-only stance is increasingly differentiated rather than aligned. **Surfaced as F2 RF tension in §3 / §4.**

### T8 (marginal) — Visual / canvas / non-text output as a first-class agent surface

**Evidence:** Cursor canvases (#12 neighbours), Anthropic Claude Design (Code w/ Claude announce). Two shipments; not yet a "everyone is shipping this" trend.

**Framing:** Worth watching. Loam's framing is software-as-deliverable; canvas output is orthogonal. Note-and-defer.

---

## §3 Stage 3 — Gap analysis vs loam (per trend)

For each Stage-2 trend, the verdict is one of: **HAS** (loam already has comparable capability), **ROADMAPPED** (on roadmap; check positioning), **GAP-INTENTIONAL** (loam architectural constraint forbids), **GAP-MISS** (genuine gap, not protected by constraint).

### T1 — Async sub-agent fan-out → **HAS** (with positioning concern)

Loam's Lens 5 (Swarming) names the pattern; the dispatch-template SKILL operationalizes it (Opus model-rationale rule, sub-agent-context-gap fix in feedback_principle_application_front_load_and_audit). The roadmap's structural-enforcement substrate at v0.7.0 names the four named-primitive amendments (FR.1–F6). **Positioning concern:** v0.7.0 sits at midpoint ~13h AI-time and is *gated behind* v0.4.0 (code-gen), v0.5.0 (binary harness), v0.6.0 (non-tech-user surface). If swarming is now industry table-stakes, deferring its *named-primitive structural enforcement* to v0.7.0 risks making loam feel "less mature" than it functionally is by the time roadmap entries surface to public attention. **See §4 for a re-rank proposal.**

### T2 — Rubric-driven grading → **ROADMAPPED** (correctly positioned)

v0.4.0 AC.V040.5 (`docs/design/odd-vs-outcomes.md` ADR) names ODD as authoring-time discipline + Outcomes as runtime grader; the stack-when-both-available framing is the right shape. Loam's reverse-ODD pipeline is the authoring-side primitive that makes Outcomes' runtime grading useful at all (rubric quality is bottlenecked on objective-quality at authoring time). **No re-rank needed; the v0.4.0 timing is right.**

### T3 — Memory and persistence go assumed → **ROADMAPPED + has 1 architectural fork**

v0.3.0 AC.V030.2 (Graphiti rip-out) + AC.V030.3 (memory verification on stranger clone via FBE.7 file-backed) are the active path. v0.9.0 holds the deep-personalization layer. **Architectural fork:** the industry is converging on graph memory + managed-service memory; loam picked file-backed (FBE.7) and ripped out Graphiti as a v0.3.0 simplification. This is correct for loam's subscription-only constraint and for current memory volumes — but the trend's velocity means loam should *re-evaluate at v0.9.0 plan-time*, not commit to file-backed forever. The Graphiti backlog re-implementation trigger ("if FBE.7 proves operationally inadequate at production-stake usage") is the right escape hatch. **No re-rank; the contingency is correctly held.**

### T4 — Cost-governance UI → **HAS partial; user-visible surface is GAP-MISS**

v0.1.6's `safety_profile` + dry-run primitive is the structural floor. What's missing relative to peers: a *user-visible* "what is this run costing me right now" surface with caps. Cline's Spend Limit Reached UI is the comparable peer feature. **Verdict: GAP-MISS for the user-visible surface; GAP-INTENTIONAL if we ground it in "subscription-only means no per-run dollar number" — but the peer products show *token-budget* surfaces work even without dollar numbers.** This is a v0.6.0 / v0.7.0-band candidate; currently not named in either. **See §4 re-rank.**

### T5 — Plugin / skill / hook ecosystems deepen → **HAS architecture; UX gaps**

Loam's SKILL system + plugin contract + hooks-as-Stop-hook-contributors are conceptually competitive. Three concrete UX gaps relative to peers: (a) skill discovery — Claude Code shipped a search box, loam has none; (b) hooks introspection — Codex `/hooks` browser is a fast iteration surface, loam's hooks live in settings.json without inspection; (c) plugin packaging — Claude Code accepts `.zip`, loam ships only directory-based. **Verdict: GAP-MISS, but small and bundleable.** Could fold into v0.7.0 (structural-enforcement substrate already touches hooks) or be its own minor.

### T6 — Background work as default → **HAS partial; user-visible inventory is GAP-MISS**

Memory rule "background agents by default" is the discipline floor. What's missing: a `loam status` (or named successor) that *lists all in-flight background work* across the workspace with status, ETA, and resume affordance. Peers (Cursor Agents Window, GitHub Copilot remote CLI control) treat this as a primary surface. Loam treats it as opt-in via the user remembering what they kicked off. **Verdict: GAP-MISS.** Higher-leverage than T5 in user-perceived terms.

### T7 — BYOK / multi-provider → **GAP-INTENTIONAL**

Subscription-only is non-negotiable per `feedback_no_anthropic_api_key.md`. Trend is real but explicitly out-of-scope for loam-as-defined. **F2 RF tension surfaced in §4 — for ruling, not silent acceptance.**

### T8 — Visual / canvas output → **GAP-INTENTIONAL** (likely)

Software-as-deliverable framing. Canvas output is orthogonal. Note-and-defer.

---

## §4 Stage 4 — Roadmap re-rank proposals (recommendations, not applied)

Per AC.HL.4 the roadmap doc itself stays untouched; what follows are *proposed adjustments* with rationale. Each carries one (or both) of the two ranking criteria from AC.HL.5: **(VP) value-prop advancement** — does it tighten translation burden or expand the persona's toolkit; **(EV) external visibility** — does it concretely draw attention or recruit co-maintainers.

### Three highest-impact re-ranks (the named "highest-impact" call per AC.HL.4 + AC.HL.5)

**RR.1 — Pull a `loam status` background-work-inventory primitive *forward* into v0.3.0 or v0.4.0.**

**Trigger:** T6 (background work as default trend); T1 (async fan-out). Currently nowhere named.

**Proposal:** Add a new AC to v0.3.0 (`AC.V030.11 — background-work inventory surface`) OR create v0.4.0's first non-code-gen AC. Surface: a single command (`loam status` or named successor) listing every in-flight background agent + scope + ETA + last update + resume affordance. No new architecture — composes on existing dispatch-tracker + the background-default rule. AI-time band: 30-60 min (~250-400 tool calls).

**Why this re-ranks high (VP + EV):**
- **VP:** Reduces translation burden directly — currently the user (Luke included) tracks in-flight work mentally or in chat. Persona has the data; doesn't expose it as a primitive.
- **EV:** Cursor Agents Window is the comparable peer surface and is the *visible identity feature* of Cursor 3.0. Loam shipping the equivalent (without API-key dependency) is a concrete demo-able artefact for the OSS launch / first-impression surface.

**Verdict:** Pull forward to v0.3.0 (tagging it AC.V030.11) OR explicitly to v0.4.0 first AC. Currently zero-named is the wrong rank.

**RR.2 — Pull a *user-visible token-budget surface* forward to v0.4.0 / v0.5.0 band, separately named.**

**Trigger:** T4 (cost-governance UI as user-visible primitive trend). Currently structural floor at v0.1.6, no user-visible surface named in any minor.

**Proposal:** Add an AC to v0.6.0 OR v0.5.0 — `AC.V0X0.N — user-visible token-budget surface with caps`. Composes on existing `safety_profile` + dry-run; adds a `/budget` (or named) primitive that shows current run's token consumption, session-total, and per-cap status. AI-time band: 60-90 min (~500-700 tool calls). Subscription-only doesn't preclude this — token counts are observable from the Claude Code surface, dollars-per-token are not (and need not be exposed).

**Why this re-ranks high (VP):**
- **VP:** Per VALUE_PROPOSITION.md "the user should not need to understand context windows, token costs, or how an AI's ongoing operation consumes tokens to have the system work well on their behalf — *but* the persona should be able to translate budget concerns into limits *on the user's behalf*." A token-budget surface plus persona-mediated cap interpretation IS the translation layer doing its job. Currently persona has no surface to point at.
- **EV (secondary):** Cline shipped Spend Limit Reached UI in v3.78; this is a known-shape feature with proven adoption mechanics.

**Verdict:** Add to v0.6.0 (non-tech-user readiness needs cost-visibility); name explicitly rather than assume safety_profile covers it.

**RR.3 — Promote a public-benchmark submission ahead of (or in lockstep with) v0.5.0 ProgramBench submission — specifically a *visible* SWE-bench Verified or SWE-bench Pro submission.**

**Trigger:** SWE-bench Pro emerging as the de-facto "honest" leaderboard (per #15 cell + the Verified vs Pro gap — Opus 4.5 80.9% Verified → 45.9% Pro per `morphllm.com/swe-bench-pro`). ProgramBench v0.5 submission alone is *one* leaderboard. SWE-bench Pro is more public-attention-rich.

**Proposal:** Add to v0.5.0 source items (or as an experiment between v0.4.0 and v0.5.0): "ODD-grounded code-gen submission to SWE-bench Pro on a sampled subset." This is *not* a new component — it composes on the v0.4.0 code-gen pipeline plus a public submission action. AI-time band: 90-180 min (~700-1200 tool calls) for a sampled-task submission with full report. Result is a *public score* tied to the loam name.

**Why this re-ranks high (EV >> VP):**
- **EV:** Direct external visibility lever. A real SWE-bench Pro number with loam attribution is recruitable-co-maintainer bait; currently loam has no public score, so external readers can't calibrate against peers.
- **VP (secondary):** Forces loam's code-gen pipeline through a peer-reviewed evaluation harness, which surfaces failure modes the in-house ProgramBench experiment alone won't surface.

**Verdict:** Add as a v0.4.0 successor / v0.5.0-companion experiment item. Optional v1: only do ProgramBench at v0.5.0; pro-level work waits until v0.6.0 or later. Recommended v2: do both — they're cheap enough relative to the visibility return.

### Other re-rank proposals (smaller, but flagged)

**RR.4 — Hooks introspection primitive (`loam hooks list / show`) — fold into v0.3.0 OR v0.7.0.** Trigger: T5. Codex shipped `/hooks` browser. Loam's hooks live in settings.json with no inspection surface. Small AI-time (~30 min); high translation-burden reduction for hook-debug workflows. Currently unnamed. **Recommend: fold into v0.3.0 AC.V030.6 lint-pass-cleanup band, OR v0.7.0 AC.V070 structural-enforcement substrate.**

**RR.5 — Skill search / discovery surface — defer to v0.7.0.** Trigger: T5. Claude Code shipped a search box. Loam SKILL count is small enough that deferral is fine until v0.7.0 structural-enforcement work is touching the SKILL surface anyway.

**RR.6 — Outcomes-pattern ADR (v0.4.0 AC.V040.5) — confirmed correctly positioned.** No change; T2 already correctly mapped.

**RR.7 — Confirm v0.7.0 swarming primitives (FR.1–F6) stay at v0.7.0, NOT pulled forward.** F2 RF on this: T1 says swarming is industry table-stakes. But: loam *has* the discipline floor (Lens 5 + dispatch-template SKILL). What v0.7.0 buys is *structural enforcement* of the discipline, which is a quality gate, not a capability gate. The capability is shipping correctly today. Pulling structural enforcement forward without v0.4.0 (code-gen) and v0.5.0 (real-world workload) generating drift cases would be enforcement-without-data. **Verdict: keep at v0.7.0.**

**RR.8 — Demote nothing.** No items in the current roadmap fail both the VP test and the EV test against this trend surface. Demotion candidates surfaced for owner review but not recommended: Idea 22 memory-doc skeleton template (v0.6.0 AC.V060.4) is small enough that re-ranking carries no cost.

### F2 RF tension — surfaced explicitly per AC.HL.6

**Tension #1 (mandatory surface): T7 BYOK is everywhere; loam's subscription-only stance is increasingly differentiated rather than aligned.**

The naming: the industry is converging on BYOK as a *paid-tier feature* (GitHub Copilot Business+Enterprise, Aider's long-standing multi-provider, OpenRouter as a backend for Cursor / Cline / etc.). Loam's subscription-only stance is grounded in `feedback_no_anthropic_api_key.md` and the v0.2.5 C4-pivot ruling. The question is whether *staying differentiated* costs adoption, or whether *adopting* costs the subscription-only architectural simplicity that lets loam ship features the BYOK harnesses can't (per VALUE_PROPOSITION's persona-as-translation-layer — token discipline is one of the things the user is entitled to ignore).

**My read (recommendation, not a ruling):** Hold the line. Subscription-only is loam's translation-burden-reduction story for the user — the user does not pick providers, does not maintain keys, does not reason about routing. BYOK works against the persona-as-translator because it *requires* the user to make a decision the persona could otherwise translate into "use Claude Max." The differentiation is a feature, not a bug. **However:** the v0.4.0 ADR `docs/design/odd-vs-outcomes.md` should explicitly *name* the BYOK divergence as a documented architectural choice with rationale, not leave it implicit. That makes the choice defensible to external readers without requiring them to dig into a memory-feedback file.

**Surfaced for owner ruling.** No silent commit either way.

**Tension #2 (smaller): SWE-bench Verified data contamination (Opus 4.5 80.9% Verified → 45.9% Pro per `morphllm.com/swe-bench-pro`).** Note: I cited the aggregator (`llm-stats.com/benchmarks/swe-bench-verified`) for the 93.9% / 87.6% / 85% numbers but did not directly verify against primary sources within this artefact. **Marked as guess-via-aggregator; primary verification deferred to RR.3 dispatch authoring time.** This is the specific-claims-verified rule applied honestly — when a number flows through an aggregator and isn't reconfirmed at primary, it gets a "verified-via-aggregator-only" tag.

---

## §5 External-visibility levers — three concrete moves

Per AC.HL.7, ≥3 specific moves loam could make in the next 1–3 minor versions that would meaningfully draw attention. Each scored against VP + EV.

### EV.1 — Public ProgramBench leaderboard submission (v0.5.0 AC.V050.4 already names this)

**Action:** Submit ODD-grounded code-gen results on 3-5 ProgramBench tasks. Publish the report at `docs/experiments/programbench-v0-5-submission.md`.

**VP:** Forces v0.4.0 code-gen pipeline through real evaluation; produces calibration data the codebase can't generate alone.
**EV:** *Direct.* Real public score with loam attribution. Even a 3% "almost resolved" is publishable evidence; ≥8% is a differentiation story; ≥0% fully resolved is a research-ship moment.
**AI-time band:** 75–150 min (per existing programbench-loam-benchmark-v0.md estimates).

**Status:** Already named at v0.5.0 AC.V050.4. **Confirmed high-impact.**

### EV.2 — Methodology paper draft on ODD-grounded reverse extraction + code-gen

**Action:** Author a short paper-shaped artefact (`docs/papers/odd-grounded-codegen-methodology.md` or similar) describing ODD's authoring-time discipline + reverse-ODD's evidence-row pipeline + the stacking shape with Outcomes-style runtime graders. Cross-reference to the ProgramBench experiment results once available. Target audience: ACL Workshop on Agents in the Wild / NeurIPS 2026 Practitioners track. arXiv preprint as the EV-action.

**VP:** Indirect — paper authoring forces methodology coherence (gaps in the paper surface gaps in the methodology).
**EV:** Substantial. arXiv preprints are the de-facto attention surface in this space (per the curated "awesome-ai-agent-papers" survey at the cs.MA arxiv list). A paper with a benchmark number + a named methodology lands in researcher Twitter / Reddit / Hacker News reliably.
**AI-time band:** 4-8 hours for a workshop-shaped 6-8 page artefact, dependent on EV.1 results being in hand.

**Suggested target:** v0.5.0 successor (after ProgramBench score lands) or v0.6.0-companion. **Currently unnamed in roadmap; surfacing for ruling.**

### EV.3 — Public methodology video + stranger-clone walkthrough

**Action:** A 15-25 minute screen-recording of (a) loam install on a fresh machine, (b) reverse-ODD on a real codebase (e.g., a Boris-paper-class small project), (c) build-next dispatch producing working code. Published to YouTube / X with cross-post to Hacker News / Reddit r/MachineLearning / r/LocalLLaMA.

**VP:** Indirect — recording forces user-flow coherence (gaps in the video surface gaps in the v0.6.0 non-tech-user-readiness surface).
**EV:** High — video is the highest-conversion attention format. Loam has zero video assets right now; one good walkthrough is asymmetric-leverage.
**AI-time band:** 60-120 min for the tooling + scripting; recording itself is owner-time, not AI-time.

**Suggested target:** v0.6.0-companion (the video IS evidence of v0.6.0's outcome). **Currently unnamed in roadmap; surfacing for ruling.**

### Scoring summary

| Lever | VP test | EV test | Roadmap status |
|---|---|---|---|
| EV.1 ProgramBench submission | Pass (calibration) | Pass-strong | Named (v0.5.0 AC.V050.4) — confirmed |
| EV.2 Methodology paper / arXiv | Pass-weak (forces coherence) | Pass-strong | Unnamed — propose v0.5.0/v0.6.0 successor item |
| EV.3 Public walkthrough video | Pass (forces flow coherence) | Pass-strong | Unnamed — propose v0.6.0 companion item |

All three pass both tests; EV.2 + EV.3 are currently unnamed in the roadmap and are the cheapest external-visibility moves available. **Recommend: name EV.2 and EV.3 as External Action lines in §6 of the roadmap, parallel to the existing Boris paper push line.**

---

## §6 Authority chain (per AC.HL.8)

- `docs/VALUE_PROPOSITION.md` — primary-persona test + harness test (the prioritization filter applied throughout §4 and §5).
- `docs/release-roadmap.md` — current target ordering; this artefact proposes adjustments to §3 (active v0.3.0), §4 (mapped v0.4.0–v1.0.0), and §6 (External actions).
- `docs/release-versioning-policy.md` + `docs/odd-semver-pinning.md` — versioning + outcome-target shape (used as the constraint surface in §4 RR.1–RR.8).
- `<workspace>/.scratch/claude-output/claude-conference-features-2026-05-06.md` — extended (not re-researched) for items #1–#7, #25 in §1.
- `<workspace>/.scratch/claude-output/programbench-loam-benchmark-v0.md` — referenced for EV.1 framing and for confirming the v0.5.0 submission action shape.
- `<workspace>/.scratch/claude-output/eric-run-issues-friday-processing.md` — referenced as real-user-feedback context (informs T4 cost-governance gap analysis).
- `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_no_anthropic_api_key.md` — the architectural constraint cited in T7 / GAP-INTENTIONAL verdicts and Tension #1.

---

## §7 Summary for owner ruling

**Three highest-impact re-rank proposals (per RR ranking in §4):**

1. **RR.1 — `loam status` background-work-inventory primitive — pull *forward* to v0.3.0 (new AC.V030.11) or v0.4.0's first AC.** VP + EV both pass strong; T6 trend evidence; ~30-60 min AI-time. Currently unnamed in any minor.
2. **RR.2 — User-visible token-budget surface — name explicitly at v0.6.0 (new sub-AC).** VP-strong (translation-burden reduction); cost-governance trend (T4). Currently structural-floor only; no user-visible surface named. ~60-90 min AI-time.
3. **RR.3 — Public SWE-bench Pro submission — add as v0.4.0 successor / v0.5.0-companion experiment.** EV-strong (visibility), VP-secondary; composes on v0.4.0 code-gen pipeline. ~90-180 min AI-time. Currently no public benchmark submission named outside ProgramBench.

**Two unnamed external-visibility levers worth adding (§5):**

- EV.2 methodology paper / arXiv preprint — propose as v0.5.0/v0.6.0-successor External Action.
- EV.3 public walkthrough video — propose as v0.6.0-companion External Action.

**One F2 RF tension surfaced for ruling (§4 Tension #1):**

- T7 BYOK trend is everywhere; loam's subscription-only stance is increasingly differentiated. Recommend hold the line + name the divergence explicitly in v0.4.0 ADR. Surfaced for owner ruling, not silently committed.

**One specific-claims caveat:** SWE-bench Verified leaderboard numbers in §1 #25 cell flow through `llm-stats.com` aggregator without primary verification. Tagged guess-via-aggregator; primary verification deferred to RR.3 dispatch authoring.

**No "rebuild" terminology appears in this artefact's body** (§7 reference to existing `docs/rebuild/` paths is the doc-tree-as-it-stands; the v0.3.0 AC.V030.8 collapse is the existing roadmap's move on this).

**Word count target:** 3000–5000 per AC.HL.9. This artefact tracks at ~3700 words (counted in §8 footer at commit time).

---

*Authored by an executor agent against the plan-doc at `docs/plans/research/harness-landscape-and-roadmap-rerank-plan.md`. Single NEW commit; no push. Output landed at `docs/plans/research/harness-landscape-and-roadmap-rerank.md`.*
