# Plan — multi-LLM orchestration via OpenRouter (DEFERRED — was-v0.1.5)

> **DEFERRED 2026-05-04 by owner directive shortly after authoring.** Owner reversed the v0.1.5 swap; memory-pluggable (D-1/D-2/D-3) restored as v0.1.5. This plan-doc stays committed as durable research/design output for future reactivation; the multi-LLM orchestration work is captured in `docs/FUTURE_IDEAS_DRAFT.md` for re-evaluation when the work is wanted. The §9 "roadmap delta" no longer applies — v0.1.x roadmap is unchanged from its 2026-05-03 reorder. Filename retains `v0-1-5-` only because rename would orphan git history; mental model: "the multi-LLM plan, deferred."

**Status:** plan-doc (pre-build, plan-before-code) — DEFERRED. Authored 2026-05-04 by multi-llm-plan-author dispatch.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Programme master:** `docs/plans/v0-1-x-roadmap.md` (the v0.1.x roadmap; this plan-doc proposes a §2 v0.1.5 reauthoring + §4 sequencing-diagram update).
**Predecessors:** v0.1.0 shipped; v0.1.1 design-note shipped; v0.1.2 in flight (V11.A + V11.E + ack-first + loam-amend ergonomics sealed); v0.1.3 (memory-pluggable D-1/D-2/D-3) and v0.1.4 (SKILL packages + ODD-RE) currently planned but not built.
**Research artefact (governs):** `<pos3>/workspace/.scratch/claude-output/v0-1-5-multi-llm-research-2026-05-04.md` (SWE-bench rankings, OpenRouter API surface analysis, alternatives comparison, recommendation).
**Composes on (sealed):** `primary-persona/` (`dispatch_wrapper.py` — the `agent_runner: Callable` seam from amendment #52 / A8 R1-revised); `cost-governance/` (`Budget.money_cents` + `BudgetDebited` event); `safety-layer/` + `reversibility-primitive/` + `orchestrator/` (the four-gate chain wraps a non-Claude `agent_runner` identically to the existing Claude-Code one); `scope-of-work/` (the `ScopeSpec` shape).
**Owner directive (locked 2026-05-03 by Luke):** swap v0.1.5 from "memory becomes pluggable" (D-1/D-2/D-3) to "multi-LLM orchestration via OpenRouter to farm jobs out to non-Claude agents." Memory-pluggable items move to v0.2.0 alongside M-GMP.

---

## §1. Top-line summary

v0.1.5 ships a **non-Claude `agent_runner` for the existing dispatch wrapper**, plumbed against OpenRouter, with DeepSeek V4 Pro as the first-class target (Luke's named candidate; verified strongest open-weights on SWE-bench Verified at 80.6 %; ~9-34× cheaper than Claude Opus 4.7 depending on promo window).

The architectural seam is **already in place**. `framework/primary-persona/src/loam/primary_persona/dispatch_wrapper.py` (amendment #52, A8) takes an `agent_runner: Callable` parameter. Today that callable invokes Claude Code's Agent tool. v0.1.5 ships a sibling `openrouter_agent_runner` callable; the four-gate chain (safety / reversibility / cost / orchestrator) wraps both transparently with **zero changes to the wrapper itself**.

**Honest scope assessment (F2 RF on the dispatcher's framing):** the dispatcher said "this is bigger than a 3-5 h release — likely 15-30 h+; may need to split." I agree, and propose **splitting across v0.1.5 + v0.1.6**:

- **v0.1.5 — single first-class target (DeepSeek V4 Pro), end-to-end dispatch path, cost-governance integration.** Demonstrates the seam works. ~10-16 h AI-time.
- **v0.1.6 — second target (GPT-5.x), tool-format round-trip verification, model-rationale dispatch brief shape per F3 swarming, simple task-type → model routing.** ~8-16 h AI-time.

If Luke wants a single release that's "good enough to demo," ship v0.1.5 only. If he wants the full multi-LLM-orchestration arc to hold up under iteration, ship the pair.

| Component | Description | AI-time band | Owner-time |
|---|---|---|---|
| C1: `openrouter_agent_runner` callable | New plugin `plugins/multi-llm-router/` with the agent-runner | 3-5 h | 10-15 min |
| C2: cost-governance widening | Accept `money_cents` from per-request OpenRouter cost; route DeepSeek pricing | 2-3 h | 5-10 min |
| C3: API-key plumbing | Workspace-config slot + secret-handling + first-run-inventory entry | 1-2 h | 5-10 min |
| C4: dispatch-brief shape | New `model: str | None` field on `DispatchShape`; routing helper picks model | 2-3 h | 5-10 min |
| C5: end-to-end smoke | A sealed-component smoke test that dispatches a tiny coding task to DeepSeek V4 Pro and verifies the four gates fire | 2-3 h | 5-10 min |
| **v0.1.5 total** | | **10-16 h** | **30-55 min** |
| C6: GPT-5.x target | Second model end-to-end | 2-4 h | 5-10 min |
| C7: tool-format round-trip tests | Verify OpenAI ↔ OpenAI passthrough AND DeepSeek ↔ OpenAI translation preserve tool semantics | 3-5 h | 10-15 min |
| C8: model-rationale dispatch brief shape | F3 swarming `model-rationale: <model> — <reason>` line in dispatch shape; absence-as-violation surface | 1-2 h | 5-10 min |
| C9: simple task-type routing | "Is this a coding task? route to DeepSeek. Plan-author? Claude. Research? Sonnet." Heuristic, not learned. | 2-5 h | 10-15 min |
| **v0.1.6 total** | | **8-16 h** | **30-50 min** |
| **v0.1.5 + v0.1.6 combined** | | **18-32 h, mid ~25 h** | **~1.5-2 h** |

**Dependencies:** v0.1.4 ships first (sequencing — no technical dep). C1 → C2/C3/C4 → C5. C6 → C7. C8 + C9 parallelise after C7.

**Owner gate-review touchpoints:** ~6-8 across the two releases.

---

## §2. Problem framing

### What loam is solving

The primary persona (Claude) frequently dispatches background sub-agents for parallel work. Today every dispatched sub-agent is *also* Claude (via Claude Code's Agent tool). This is an under-utilised constraint:

1. **Cost.** Claude Opus 4.7 output tokens are ~$30-150/M depending on tier. DeepSeek V4 Pro is ~$0.87/M (post-promo $3.48/M). For workloads where SWE-bench Verified is the right proxy (codebase-grade software-engineering tasks), DeepSeek V4 Pro at 80.6 % is within 7 pp of Opus 4.7 at 87.6 % — for 10-30× lower cost.
2. **Specialisation.** Different models excel at different task shapes. GPT-5.5 leads SWE-bench Verified at 88.7 %; Gemini 3.1 Pro has the best long-context handling; Qwen3-Coder is locally runnable. A single-vendor harness leaves leverage on the table.
3. **Resilience.** Vendor-API outages (Anthropic, OpenAI) are not zero-frequency. A multi-LLM dispatch path lets work proceed when one vendor is down.
4. **Iteration speed for Luke.** Luke can experiment with "is DeepSeek good enough for this kind of task?" without rewriting the dispatch path each time.

### What loam is NOT solving

1. **Full LLM-vendor-agnosticism.** The primary persona stays Claude. Lens 1 ("loam is exclusively attached to Claude") still holds. v0.1.5 widens what *dispatched sub-agents* can be, not what loam itself is.
2. **Routing the primary persona to non-Claude.** Possible via `ANTHROPIC_BASE_URL` + LiteLLM — but a different feature shape, deferred. Lens 1 says don't do this.
3. **Self-hosted multi-LLM gateway.** OpenRouter is the hosted-router shape; LiteLLM in proxy mode is the self-hosted shape. v0.1.5 ships only the hosted path; a self-hosted gateway is v0.2+ if/when needed.
4. **Learned routing / model-selection RL.** Heuristic only. F3 swarming requires a `model-rationale` line in dispatch briefs — that's the discipline. No learning loop.

---

## §3. Lens 1 — Claude-leverage-first

The required Lens 1 question: **"What Claude capability does this lean on or extend?"**

This is the most-interesting Lens 1 case loam has shipped. The answer is: **the dispatch wrapper's `agent_runner: Callable` seam is the Claude-leverage** — Claude Code's Agent tool today, but the seam is generic. Plus:

1. **Sub-agent discovery via `.claude/agents/<name>.md`.** Today these files prime Claude-Code-spawned subagents. For non-Claude subagents, a sibling discovery file (`.claude/agents/<name>.openrouter.md` or `.openrouter/agents/<name>.md`) carries the model identifier + system prompt. Claude Code's discovery mechanism still applies for the persona's awareness — the persona sees both kinds of subagents in its mental model — but only Claude-typed ones actually run via the Claude Code Agent tool.
2. **Persona's task-type classification.** The persona is Claude; Claude is what decides "is this task best routed to DeepSeek?" The decision is made by Claude, then the dispatch wrapper actually invokes the chosen model. This composes Claude's planning + classification with cheaper execution — a clean Lens 1 leverage shape.
3. **Cost-governance gate-chain.** Already shipped (amendment #52, A8). Wraps both Claude-Code and OpenRouter `agent_runner` invocations identically. No new Claude-leverage; reuse of the existing one.
4. **MCP server access.** When DeepSeek or GPT-5 is the dispatched sub-agent, MCP servers are NOT available (those are Claude-Code-specific). v0.1.5 documents this restriction; tasks requiring MCP servers remain Claude-typed dispatches.

The required Lens 2 questions:

- **Primary-persona test:** does this reduce the translation burden? **Yes** — the persona can express "this task is suitable for a cheaper model" by setting `DispatchShape.model = "deepseek-v4-pro"`, vs the current "always Claude" implicit choice that wastes budget.
- **Harness test:** does this add to the toolkit? **Yes** — `openrouter_agent_runner` is a new tool the persona can draw from.

The required Lens 4 question:

- **Confidence in outcome shape:** moderate. The seam is clear (the `agent_runner: Callable` parameter); the API choice is clear (OpenRouter). What's NOT yet confidence-high: which model gets routed which task, whether tool-format translation breaks subtle cases, whether DeepSeek's tool-call semantics handle multi-turn well. Per F4 → loosen scope on "which models, which tasks" and tighten scope on "the seam works end-to-end for ONE model."

The required Lens 5 question:

- **Decomposable into tighter-AC subtasks?** Yes, into C1-C5 for v0.1.5 and C6-C9 for v0.1.6. Each component has a strictly tighter AC than the parent objective. Stopping criterion: further decomposition (e.g., splitting C1 into "auth" + "request shape" + "response parsing") adds only coordination overhead — the agent-runner is a single coherent code unit. **Stop at component-level split.**

---

## §4. Architecture sketch

### §4.1 New component placement

**Recommendation: `plugins/multi-llm-router/`.**

Reasoning:
- Matches v0.1.3 D-2 Decision C — "Lens-1 leverage is purest when adapter is a plugin (composes onto loam-the-harness without entanglement)."
- Plugin shape is independently versionable. OpenRouter API breaking changes don't bump loam framework version.
- Plugin shape allows opt-in: workspaces that don't want multi-LLM dispatch don't carry the dependency.
- Mirrors `plugins/dev-sdlc/` precedent (already shipped at v0.1.0).

### §4.2 Data flow

```
                                    ┌─────────────────────────────┐
                                    │ primary-persona             │
                                    │ (Claude)                    │
                                    │                             │
                                    │ persona decides task is     │
                                    │ "coding-grade, not novel"   │
                                    │ → set model = deepseek-v4-  │
                                    │   pro on DispatchShape      │
                                    └──────────────┬──────────────┘
                                                   │
                                                   ▼
                                    ┌─────────────────────────────┐
                                    │ dispatch_wrapper.py         │
                                    │ (existing — amendment #52)  │
                                    │                             │
                                    │ dispatch_with_scope(         │
                                    │   shape=DispatchShape(...,  │
                                    │       model="deepseek-..."),│
                                    │   agent_runner=             │
                                    │     pick_runner(shape))     │
                                    │                             │
                                    │ pick_runner is a NEW        │
                                    │ helper that reads shape.    │
                                    │ model and returns either    │
                                    │ claude_code_agent_runner    │
                                    │ (existing) OR new           │
                                    │ openrouter_agent_runner     │
                                    └──────────────┬──────────────┘
                                                   │
                                ┌──────────────────┴──────────────────┐
                                │                                     │
                                ▼                                     ▼
              ┌─────────────────────────────┐       ┌─────────────────────────────┐
              │ four-gate chain             │       │ four-gate chain             │
              │ (safety / reversibility /   │       │ (safety / reversibility /   │
              │  cost / orchestrator)       │       │  cost / orchestrator)       │
              │                             │       │                             │
              │ Budget reserve                       │ Budget reserve              │
              │ → invoke claude_code_agent  │       │ → invoke openrouter_agent   │
              └──────────────┬──────────────┘       └──────────────┬──────────────┘
                             │                                     │
                             ▼                                     ▼
              ┌─────────────────────────────┐       ┌─────────────────────────────┐
              │ Claude Code Agent tool      │       │ openrouter_agent_runner     │
              │ (existing)                  │       │ (NEW — plugins/multi-llm-   │
              │                             │       │  router/)                   │
              │ Spawns subprocess that uses │       │                             │
              │ Claude Sonnet/Opus per      │       │ HTTP POST to                │
              │ .claude/agents/<name>.md    │       │ openrouter.ai/api/v1/       │
              └─────────────────────────────┘       │ chat/completions            │
                                                    │                             │
                                                    │ Reads .openrouter/agents/   │
                                                    │ <name>.md for system prompt │
                                                    │ + model selection           │
                                                    │                             │
                                                    │ Returns response.usage.cost │
                                                    │ to BudgetDebited            │
                                                    └─────────────────────────────┘
```

### §4.3 Component fences

C1 (`openrouter_agent_runner`): single-component fence on **`plugins/multi-llm-router/`** (new plugin scaffold).

C2 (cost-governance widening): single-component fence on **`framework/cost-governance/`**. Adds price tables for OpenRouter models OR (better) accepts `money_cents` directly from the runner's response. Recommend the latter — keeps cost-governance vendor-agnostic.

C3 (API-key plumbing): two-component fence on **`framework/loam-init/`** + **`framework/workspace-bootstrap/`**. Adds `OPENROUTER_API_KEY` to the env-scrubber whitelist + first-run-inventory env-var probe + workspace-config scaffold.

C4 (dispatch-brief shape): single-component fence on **`framework/primary-persona/`**. Widens `DispatchShape` with `model: str | None` field; adds `pick_runner(shape)` helper. Composes on existing `dispatch_wrapper.py`.

C5 (end-to-end smoke): cross-component verification, lives as a smoke test in `plugins/multi-llm-router/tests/`. NOT a sealed-component fence-extension — verifies behaviour, doesn't add binding code.

### §4.4 What composes naturally

- **Cost-governance.** OpenRouter returns `usage.cost` per request. Plug into existing `BudgetDebited` event. Cost-governance ledger fills with real per-request costs across vendors. The 80 %-throttling pathway fires identically.
- **Safety-layer.** Wraps the runner-invocation transparently. Same `cost.status` IPC.
- **Reversibility-primitive.** Same — wraps transparently.
- **Orchestrator.** Same — `activate_scope_with_spec` IPC works identically; `scope_runtime.create(spec)` doesn't care which LLM the scope ends up calling.
- **Objective-tracker.** Tracker context carries the dispatched scope's binding regardless of LLM. No changes.

### §4.5 What does NOT compose

- **MCP servers.** Claude Code's MCP-server context is not portable to OpenRouter. Tasks requiring MCP-server access remain Claude-typed dispatches. Document this explicitly in `plugins/multi-llm-router/README.md`.
- **`.claude/agents/<name>.md` skill discovery for non-Claude.** The Claude Code skill-discovery mechanism is Claude-Code-specific. Non-Claude sub-agents need their own discovery surface (recommend: `<workspace>/.openrouter/agents/<name>.md`, mirror of the `.claude/agents/` shape, plus a `model:` frontmatter field).

---

## §5. AC table

### v0.1.5 components

| AC | Description | Component | Test shape |
|---|---|---|---|
| AC.MLR.1 | `openrouter_agent_runner(prompt, system, tools, model, ...) -> AgentResult` callable accepts an OpenAI-format request and returns an `AgentResult` containing reply, usage tokens, and `money_cents` from `usage.cost` | `plugins/multi-llm-router/` | unit + smoke against OpenRouter staging |
| AC.MLR.2 | `pick_runner(shape: DispatchShape)` returns `claude_code_agent_runner` when `shape.model` is None or starts with "claude-"; returns `openrouter_agent_runner` otherwise | `framework/primary-persona/` | unit |
| AC.MLR.3 | `DispatchShape.model: str | None` field added; default None; round-trips through serialisation | `framework/primary-persona/` | unit |
| AC.MLR.4 | `BudgetDebited` event accepts `money_cents` directly when supplied by the runner; the existing tokens-based path still works for Claude-Code runners | `framework/cost-governance/` | unit |
| AC.MLR.5 | OpenRouter API key sourced from `$OPENROUTER_API_KEY` env var; if missing, `openrouter_agent_runner` raises a typed `MissingApiKeyError` BEFORE any HTTP call; the four-gate chain catches and returns `DispatchRefusal` | `plugins/multi-llm-router/` | unit |
| AC.MLR.6 | First-run-inventory probes for `$OPENROUTER_API_KEY` and surfaces a YAML row indicating whether multi-LLM dispatch is available | `framework/loam-init/` + `framework/workspace-bootstrap/` | unit + smoke |
| AC.MLR.7 | Env-scrubber whitelist admits `OPENROUTER_API_KEY` (existing precedent for `ANTHROPIC_API_KEY`) | `framework/memory-system/` (the env-scrubber lives here per amendment #30) | unit — verify the whitelist literal |
| AC.MLR.8 | End-to-end smoke: dispatch a tiny coding task to DeepSeek V4 Pro via OpenRouter; the four gates fire (verified via cost-governance ledger having a non-empty row); the response comes back and is captured into the dispatch result | `plugins/multi-llm-router/tests/` | smoke (network-required, marked as such) |
| AC.MLR.9 | When the OpenRouter API returns a non-2xx response or times out, the runner returns a typed `RunnerError` and the four-gate chain handles it as `DispatchRefusal` (cost reservation is refunded) | `plugins/multi-llm-router/` | unit (mocked) |
| AC.MLR.S | Single-component fence on `plugins/multi-llm-router/` for C1; cross-component fences for C2/C3/C4 as named above | sealed-amendment fence | post-seal |

### v0.1.6 components (planned but not built in v0.1.5)

| AC | Description | Component |
|---|---|---|
| AC.MLR.10 | Second model end-to-end: GPT-5.5 (or GPT-5.3-Codex per cost) via OpenRouter | `plugins/multi-llm-router/` |
| AC.MLR.11 | Tool-format round-trip: a request with a tool-use turn round-trips through DeepSeek V4 Pro AND GPT-5.x AND returns identical-shape tool-call results (per OpenRouter's normalisation) | `plugins/multi-llm-router/tests/` |
| AC.MLR.12 | `DispatchShape.model_rationale: str | None` field; if `model` is set to a non-default model AND `model_rationale` is None, dispatch_with_scope logs a structural-violation diagnostic (mirrors F3 swarming `model-rationale` rule) | `framework/primary-persona/` |
| AC.MLR.13 | `pick_default_model_for_task_type(task_type: str) -> str` heuristic helper: "coding" → DeepSeek V4 Pro; "research" → Sonnet (Claude Code default); "plan-authoring" → Opus | `plugins/multi-llm-router/` |
| AC.MLR.14 | Documentation update: how to author a `.openrouter/agents/<name>.md` subagent file | `plugins/multi-llm-router/README.md` |

---

## §6. AI-time estimate

Per `feedback_duration_estimation_rubric`, AI-time only (not owner gate-review).

### v0.1.5

- **C1 (`openrouter_agent_runner`): 3-5 h.** New plugin scaffold + HTTP client + retry/timeout handling + response parsing + `AgentResult` dataclass + 6-10 unit tests + 1-2 mocked-HTTP tests. Full new-component cycle (per rubric: 60-180 min new component + 30-60 min sealed-amendment cycle = 90-240 min midpoint ~3 h; band 3-5 h with debug margin).
- **C2 (cost-governance widening): 2-3 h.** Single-field addition to `BudgetDebited` event + 2-3 new tests + sealed-component cycle (single-component amendment: 10-20 min code + 30-60 min seal = 40-80 min; band widens to 2-3 h because cost-governance has heavier test surface than typical).
- **C3 (API-key plumbing): 1-2 h.** Two-component fence (loam-init + workspace-bootstrap) + env-var addition + first-run-inventory row + 4-6 tests. Per rubric: 20-45 min multi-component amendment + buffer.
- **C4 (dispatch-brief shape): 2-3 h.** Single-component on primary-persona + new field + `pick_runner` helper + 5-8 tests.
- **C5 (end-to-end smoke): 2-3 h.** 1-2 smoke tests (network-required) + cost-governance ledger verification + plumbing for the smoke env to have a cheap test prompt + actually running it against live OpenRouter (Luke's API key).

**v0.1.5 total: 10-16 h, midpoint ~13 h.** This is at the upper edge of typical-sized loam releases (most are 3-7 h); reasonable for the architectural milestone of "multi-LLM dispatch is a thing."

### v0.1.6

- **C6 (GPT-5.x target): 2-4 h.** Mostly config + a price-table entry; the runner code is reused.
- **C7 (tool-format round-trip): 3-5 h.** Test authoring is the bulk; needs careful tool-call payload that exercises >1 round-trip.
- **C8 (`model_rationale` field): 1-2 h.** Single-component amendment on primary-persona.
- **C9 (task-type routing heuristic): 2-5 h.** Heuristic table + 3-5 task-type smoke tests + persona-side wiring.

**v0.1.6 total: 8-16 h, midpoint ~12 h.**

**Combined v0.1.5 + v0.1.6: 18-32 h, midpoint ~25 h.**

---

## §7. Dependencies

### Hard dependencies (block the build)

- **Cost-governance shipped (`framework/cost-governance/`).** Already shipped — amendment #52 / A8.
- **Dispatch wrapper shipped (`framework/primary-persona/dispatch_wrapper.py`).** Already shipped — amendment #52 / A8.
- **Active scope sentinel + four-gate chain working.** Already shipped — amendments #52 / #74.
- **OpenRouter API key from Luke.** Owner-action. Required for AC.MLR.8 smoke and any live testing.

### Soft dependencies (sequencing only)

- v0.1.4 ships first per programme order.
- Memory-pluggable (originally v0.1.5) re-sequences to v0.2.0 (see §10).

### Cross-cutting risk dependencies

- **OpenRouter API stability.** The chat-completions endpoint shape is v1; expected stable. Verify no breaking changes between plan-author and build dispatch.
- **DeepSeek V4 Pro promotional pricing window** ends 2026-05-05. Post-promo prices ($1.74/$3.48 per 1M) still 9× cheaper than Opus 4.7 — recommendation stands either way, but the price-table entries in C2 should reflect post-promo prices for durability.

---

## §8. Owner-decisions

Most decisions land at recommendation; surfaced here so they're explicit.

### Decision A — first-class target: DeepSeek V4 Pro (recommended) vs other?

**Question:** is DeepSeek V4 Pro the right v0.1.5 first-class target?
**Recommendation:** **yes, DeepSeek V4 Pro.** Strongest open-weights SWE-bench Verified (80.6 %), 1M context, 9-34× cheaper than Opus 4.7, matches Luke's named candidate. The runner-up is GPT-5.5 (88.7 % Verified) but it's expensive ($30/M output) and OpenAI-vendor-locked.
**Mirrors:** research artefact §5.1.

### Decision B — split across v0.1.5 + v0.1.6 (recommended) vs single release?

**Question:** ship v0.1.5 as just the seam-works-for-one-model release, with v0.1.6 adding the round-trip tests / second model / model-rationale; OR cram both into v0.1.5?
**Recommendation:** **split.** Single release is 18-32 h AI-time which is 3-5× a typical loam release; reliability-of-delivery argues for split. v0.1.5 demonstrates the seam, v0.1.6 hardens it. v0.1.5's release notes lead with "DeepSeek V4 Pro now dispatch-able"; v0.1.6's lead with "any of N models now selectable."
**Why surfaced:** the dispatcher pre-flagged this; explicit ruling closes it.

### Decision C — OpenRouter (recommended) vs direct provider APIs vs LiteLLM?

**Question:** route via OpenRouter, call DeepSeek's API directly, or run a local LiteLLM proxy?
**Recommendation:** **OpenRouter.** Single OpenAI-compatible endpoint; pass-through token pricing for DeepSeek (5.5 % credit-purchase fee only); per-request cost returned natively for cost-governance integration; tool-format normalisation handled for us. Direct provider APIs are right for v0.2+ when loam wants vendor-native deep features (DeepSeek's `reasoning_effort: xhigh`, etc.). LiteLLM is right for self-hosted scenarios — not v0.1.5.
**Mirrors:** research artefact §5.1 + §4.

### Decision D — API-key plumbing in v0.1.5 (recommended) vs separate amendment?

**Question:** does the API-key plumbing (C3) ship in v0.1.5 or as a separate amendment?
**Recommendation:** **in v0.1.5.** It's small (1-2 h), it's required for AC.MLR.8 smoke to pass, and it's logically inseparable from "multi-LLM dispatch works." Separating buys nothing.

### Decision E — model selection: persona-explicit (recommended for v0.1.5) vs auto-routed?

**Question:** how does "this task should go to DeepSeek" get expressed? Options: (a) persona explicitly sets `DispatchShape.model = "..."`; (b) heuristic auto-routes by task-type; (c) Luke explicitly says "use DeepSeek for this."
**Recommendation:** **(a) explicit-persona for v0.1.5; add (b) heuristic in v0.1.6 (C9).** (a) is the lowest-confidence-required step (persona is Claude; Claude can decide). (b) requires a routing table that's hard to get right without iteration data. (c) is always available as the override.
**Why surfaced:** controls the v0.1.5 scope shape. If Luke wants (b) in v0.1.5, the AI-time band shifts to 13-21 h.

### Decision F — second target for v0.1.6: GPT-5.5 vs GPT-5.3-Codex vs Gemini 3.1 Pro?

**Question:** which model takes the C6 slot?
**Recommendation:** **GPT-5.5 (or GPT-5.3-Codex if GPT-5.5 pricing is too high for verification budget).** Reasons: (1) tool-format is OpenRouter-native (no transformation surface), (2) #1 SWE-bench Verified at 88.7 %, (3) OpenAI is the "if Anthropic is down" fallback vendor most Luke-relevant. Gemini 3.1 Pro deferred to a later release as the third target.
**Why surfaced:** straightforward call but Luke may have preferences (Gemini 3 has a different feature set — 1M context, video, etc.).

### Decision G — `.openrouter/agents/<name>.md` discovery shape: mirror `.claude/agents/` (recommended) vs different shape?

**Question:** how does a workspace describe its non-Claude subagents?
**Recommendation:** **mirror `.claude/agents/<name>.md` shape with a `model:` frontmatter field.** Familiarity for the persona; familiar to humans who've authored Claude subagents; minimal new convention. Path: `<workspace>/.openrouter/agents/<name>.md`.
**Why surfaced:** v0.1.6 (C9) will need this; useful to lock the shape now.

### Decision H — error semantics on OpenRouter outage: refuse-and-surface (recommended) vs fall-back-to-Claude?

**Question:** if OpenRouter is unreachable / API-key invalid / model 404s, does the dispatch fall back to a Claude runner OR refuse and surface?
**Recommendation:** **refuse and surface.** Fall-back-to-Claude silently changes the cost profile under the persona's feet — surprising behaviour. Refuse-and-surface lets Luke (or the persona) make an informed retry. Mirrors the four-gate chain's existing `DispatchRefusal` semantics.
**Why surfaced:** behavioural-shape decision; non-obvious.

---

## §9. Roadmap delta

Proposed update to `docs/plans/v0-1-x-roadmap.md`:

### §9.1 Programme table (replaces §1 table line for v0.1.5)

| Release | One-line theme | AI-time band | Owner-time |
|---|---|---|---|
| v0.1.1 | Articulate the scaffolding choice plainly | 45–90 min | 5–10 min |
| v0.1.2 | Fix what v0.1.0 strangers will hit | 2–4 h | 30–45 min |
| v0.1.3 | Memory becomes pluggable | 3–5 h | 20–30 min (was scheduled here originally — UNCHANGED) |
| v0.1.4 | loam composes with raw Claude Code | 4–7 h | 25–35 min |
| **v0.1.5** | **Multi-LLM dispatch via OpenRouter (DeepSeek V4 Pro target)** | **10–16 h** | **30–55 min** |
| **v0.1.6** | **Multi-LLM hardening (second target + tool-format verification + model-rationale + heuristic routing)** | **8–16 h** | **30–50 min** |
| **Total v0.1.x** | | **~28–48 h** | **~3–4 h** |

**Important context: the existing v0.1.x roadmap document is internally inconsistent on memory-pluggable's slot.** The §1 table at line 19-26 says v0.1.5 = "Memory becomes pluggable" (post the 2026-05-03 reorder), but the §2 per-release detail at lines 109-124 still says v0.1.5 = "harness self-aware about roles" (subagent personas + V11.B + design notes), with v0.1.3 = "Memory becomes pluggable." This plan-doc swaps "Memory becomes pluggable" out of v0.1.5, which means whichever v0.1.5 description is currently authoritative gets replaced — but the v0.1.3 / v0.1.4 contents keep their existing per-release details (subagent personas, design notes, V11.B, SKILL packages, ODD-RE skill, memory-pluggable D-1/D-2/D-3).

**Recommendation as part of this v0.1.5 swap:** the roadmap-author dispatch should also reconcile the §1 table ↔ §2 per-release-detail inconsistency in a SEPARATE small edit at the same time the v0.1.5 swap lands. Do not swap one ambiguity for another.

### §9.2 v0.1.5 contents

Replace the existing v0.1.5 section in `docs/plans/v0-1-x-roadmap.md` §2 (whichever version is currently there post-reconciliation) with:

> ### v0.1.5 — "Multi-LLM dispatch via OpenRouter"
>
> **What this release is about.** loam currently dispatches every sub-agent to Claude (via Claude Code's Agent tool). v0.1.5 widens the dispatch to non-Claude models via OpenRouter. The persona stays Claude (Lens 1); only the dispatched sub-agents become multi-vendor. First-class target: DeepSeek V4 Pro (80.6 % SWE-bench Verified, ~9-34× cheaper than Opus 4.7). The architectural seam is already in place: `dispatch_wrapper.py`'s `agent_runner: Callable` parameter takes a Claude-Code runner today; v0.1.5 ships a sibling `openrouter_agent_runner`.
>
> **Bundle:** see `docs/plans/v0-1-5-multi-llm-orchestration.md` §5 for AC table and component breakdown. Five components C1-C5 (~10-16 h AI-time).
>
> **Dependencies:** v0.1.4 ships first. OpenRouter API key from Luke (one-time setup).
>
> **Gate (closes the release):** an end-to-end smoke dispatching a tiny coding task to DeepSeek V4 Pro via OpenRouter, with the four gates firing and cost-governance ledger filling. Tag `v0.1.5`. Release notes lead with "DeepSeek V4 Pro now dispatch-able from loam."

### §9.3 v0.1.6 contents (NEW)

Add a v0.1.6 section to `docs/plans/v0-1-x-roadmap.md` §2:

> ### v0.1.6 — "Multi-LLM hardening"
>
> **What this release is about.** v0.1.5 demonstrated the seam works for one model. v0.1.6 hardens it. Adds GPT-5.5 (or GPT-5.3-Codex) as second target so tool-format round-trip can be verified across both DeepSeek and OpenAI shapes. Adds the F3 swarming `model-rationale` field to dispatch shape — absence-as-violation observable. Ships a simple task-type → model heuristic so the persona has a default routing table to override.
>
> **Bundle:** see `docs/plans/v0-1-5-multi-llm-orchestration.md` §5 for AC table (AC.MLR.10-14). Four components C6-C9 (~8-16 h AI-time).
>
> **Dependencies:** v0.1.5 ships first.
>
> **Gate (closes the release):** a tool-call round-trips through DeepSeek + GPT-5.x with identical resulting tool-call shape; `model_rationale` absence triggers a structural-violation diagnostic; `pick_default_model_for_task_type` routes 3+ task-types to sensible defaults. Tag `v0.1.6`.

### §9.4 Memory-pluggable's new home

The original v0.1.5 / v0.1.3 contents (memory-pluggable D-1/D-2/D-3) move to **v0.2.0**, alongside M-GMP (graphiti as plugin MemoryProvider). Coherent because:

- Memory-pluggable widens the `MemoryProvider` Protocol surface (D-3); M-GMP is the second non-file-based provider after the Anthropic-tool adapter (D-2). Shipping both in one release lets the Protocol get exercised by 3 providers (file-based + Anthropic-tool + graphiti) at once, which validates the seam.
- v0.2.0 is the natural release-ceremony milestone for "memory backends are first-class."

Update v0.2.0 section in `docs/plans/v0-1-x-roadmap.md` §3 (deferred items) to land memory-pluggable as a v0.2.0 component.

### §9.5 Sequencing diagram update

Update the diagram in §4 of `docs/plans/v0-1-x-roadmap.md` to:

```
v0.1.0 (shipped)
  │
  ▼
v0.1.1 ── design note (why-loam-scaffolds) ✓ SHIPPED
  │
  ▼
v0.1.2 ── orchestrator fix ────────────┐
  │       v0.1.0 hot follow-ons       │
  │       gh-create→push race docs    │
  │       two-copies docs-explain     │
  │       ack-first persona contract  │
  │       loam-amend ergonomics ×3    │
  ▼                                    │
v0.1.3 ── 3-5 SKILL.md packages        │
  │       ODD-RE skill (V11.C)         │
  │       design note: primary-persona │
  ▼                                    │
v0.1.4 ── 5 subagent personas          │
  │       V11.B (#38/#39/#40) ◄────────┘  (orchestrator from v0.1.2)
  │       design notes (file-mem + odd-delegation)
  ▼
v0.1.5 ── C1 openrouter_agent_runner
  │       C2 cost-governance widen
  │       C3 API-key plumbing
  │       C4 dispatch-brief shape
  │       C5 end-to-end smoke (DeepSeek V4 Pro)
  ▼
v0.1.6 ── C6 second target (GPT-5.x)
          C7 tool-format round-trip
          C8 model-rationale dispatch field
          C9 task-type routing heuristic

v0.2.0 (out of scope)
  ├── D-1/D-2/D-3 (memory-pluggable; was v0.1.5/v0.1.3 originally)
  ├── M-GMP (graphiti as first plugin MemoryProvider)
  ├── V2.C swarm-runtime
  ├── PyPI publish gate
  └── ODD-conformance sweep + Foundation revisions + everything in §3
```

---

## §10. Risk register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | OpenRouter API breaking changes between plan-author and build dispatch | Low | Medium | C1 build dispatch should re-verify the API shape at build time; pin SDK version if available |
| R2 | DeepSeek V4 Pro tool-call semantics handle multi-turn poorly | Medium | High | C5 smoke is single-turn first; v0.1.6 C7 explicitly tests multi-turn round-trips — discovers the issue before production use |
| R3 | OpenRouter rate-limits Luke's account during testing | Low | Low | Smoke tests are tiny prompts; rate-limits are unlikely to fire at test scale |
| R4 | Tool-format translation introduces silent semantic drift (a tool call works but its arguments are subtly transformed) | Medium | High | C7 round-trip tests; halt-and-surface protocol on any drift detected |
| R5 | API key handling leaks `OPENROUTER_API_KEY` into logs | Low | High | C3 must follow existing env-scrubber precedent (amendment #30); add explicit redaction tests for the key value in any log emission |
| R6 | Cost surprises (a small bug in cost-governance integration causes runaway spending on DeepSeek) | Low | High | The four-gate chain's 80 % throttle still fires on per-request cost. Plus: the smoke test has a dollar cap; any test running >$0.50 per invocation halts |
| R7 | DeepSeek V4 Pro deprecated / renamed within months | Medium | Medium | Plugin shape isolates the model identifier to one configuration table; swap is a small edit when it happens |
| R8 | License issues with running specific models (DeepSeek's terms permit commercial use; verify before Luke uses for paid work) | Low | Medium | Document each supported model's license + ToS link in `plugins/multi-llm-router/README.md` |
| R9 | The `model: str` field on `DispatchShape` becomes a sprawling enum | Low | Low | Recommendation: keep the model field as a free-string; the runner-picker validates at runtime; don't over-engineer the type system |
| R10 | OpenRouter's 100 % markup on Claude makes "use OpenRouter for everything" a 2× cost vs direct Anthropic for Claude calls | High (this is a fact) | Medium (only an issue if loam mistakenly routes Claude through OpenRouter) | `pick_runner` MUST short-circuit Claude-typed dispatches to the existing Claude-Code runner, never to OpenRouter. AC.MLR.2 enforces |
| R11 | The dispatched non-Claude sub-agent doesn't have access to loam's MCP servers and silently produces lower-quality output for tasks that needed them | Medium | Medium | Document explicitly; add a halt-and-surface in `pick_runner` when `shape.requires_mcp` is True (new field, v0.1.6) |
| R12 | Lens 1 violation creep — over time, loam might gradually route more and more of the persona's work to non-Claude, inverting the original Claude-attached framing | Low (now) / Higher over time | High | The plan-doc explicitly fences this: persona stays Claude; only dispatched sub-agents are multi-vendor. Future amendments need explicit Lens 1 review |

---

## §11. Halt-and-surface BEFORE build

Per `feedback_subagent_odd_violation_halt`. Halt triggers for the v0.1.5 build dispatch:

1. **Dispatch wrapper seam shape changed** since this plan was authored — i.e., `dispatch_wrapper.py`'s `agent_runner: Callable` signature was modified by an amendment between this plan and v0.1.5 build. Halt; surface; re-plan.
2. **OpenRouter API surface changed materially** (e.g., `usage.cost` field renamed, tool-format normalisation removed, OpenAI-compat broken). Halt; re-research.
3. **DeepSeek V4 Pro deprecated / unavailable on OpenRouter** at build time. Halt; surface; offer GPT-5.x or DeepSeek V4 Flash as alternatives.
4. **Cost-governance Budget shape doesn't actually accept money_cents** as the plan assumes. Halt; halt-and-surface; widen scope to include cost-governance schema.
5. **Plan inconsistency:** if this plan-doc and the roadmap (`docs/plans/v0-1-x-roadmap.md`) disagree on what v0.1.5 is at build time. Halt; align before building.

---

## §12. Verification of plan claims

Per `feedback_specific_claims_verified_or_marked_guess`. Specific claims this plan makes and their verification status:

| Claim | Source | Status |
|---|---|---|
| DeepSeek V4 Pro 80.6 % SWE-bench Verified | 4 sources (codersera, framia.pro, nxcode.io, llm-stats) | **Verified.** Multi-source corroboration. |
| DeepSeek V4 Pro promo $0.435/$0.87 through 2026-05-05 | OpenRouter model page | **Verified at research time (2026-05-04); time-sensitive — re-verify at build dispatch.** |
| GPT-5.5 88.7 % SWE-bench Verified | codeant.ai | **Verified single-source; suggest cross-checking before C6 (v0.1.6).** |
| OpenRouter 5.5 % credit-purchase fee, pass-through token rates | costgoat | **Verified.** |
| OpenRouter 100 % markup on Anthropic Claude | costgoat | **Verified single-source — moderate confidence; recommend smoke-verifying at C5 by inspecting `usage.cost` on a Claude call.** |
| `dispatch_wrapper.py` has an `agent_runner: Callable` seam | direct file read at `framework/primary-persona/src/loam/primary_persona/dispatch_wrapper.py:1-90` | **Verified.** |
| v0.1.5 + v0.1.6 combined AI-time 18-32 h | rubric calculation | **Estimate — calibrated against rubric, NOT empirical for this work-shape; treat as a band, not a point.** |
| Lens 1 holds (primary persona stays Claude) | design — this plan-doc enforces it | **Asserted, not measured.** |
| Cost-governance `Budget.money_cents` field exists | NOT directly verified at plan-author time | **GUESS — flagged in §11 halt-trigger 4. Re-verify at build.** |

---

*End of v0.1.5 plan-doc. Companion v0.1.6 contents in §9.3. Research artefact at `<pos3>/workspace/.scratch/claude-output/v0-1-5-multi-llm-research-2026-05-04.md`.*
