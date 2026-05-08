# Component — Graceful Degradation

**Created:** 2026-04-19 08:41 CDT. **State:** ✅ **COMPLETE — sealed 2026-04-19 10:02 CDT.** All D1–D10 landed; 93 tests green; zero sealed-component regressions; 0% garbage FPR; all 8 one-hour-outage invariants passed. Memory-system detection blind spot accepted with documented pyee-fallback mitigation; enhancement logged to post-Phase-2 backlog.

---

## Parent objective (from spec v1.0 Foundational layer)

> **Graceful degradation.** Defined behaviour when the upstream Claude API is down, rate-limited, or returning garbage; includes a "safe mode" that degrades or pauses autonomous scope rather than hallucinating forward.
>
> Acceptance:
> - Simulated one-hour Claude outage does not corrupt in-flight scope state.
> - Sessions resume cleanly once the upstream returns.
> - User is informed before blast radius exceeds a declared threshold.

## Why this component is next

1. **The orchestrator already exposes `pause_activation(reason) / resume_activation()` hooks.** Graceful degradation is their first natural consumer; doing it next closes the "handle Claude outage" story end-to-end.
2. **Decision from orchestrator research (accepted by the owner):** graceful degradation is a separate component, not a sub-module of the orchestrator — it owns LLM-judged policy (safe-mode narrative, user notification, threshold calls), whereas the orchestrator is deterministic plumbing.
3. **First Phase 2 consumer layer.** Orchestrator is plumbing; this is the first component that encodes pOS policy on top of that plumbing.

## Artifacts

- `research-plan.md` — drafted 2026-04-19; awaiting owner's approval
- `research.md` — not yet produced
- `proposal.md` — not yet produced
- `brief.md` — not yet produced
- `outputs/` — empty

## History

- 2026-04-19 08:41 CDT — component created; research plan drafted; awaiting owner's approval before research begins.
- 2026-04-19 08:49 CDT — owner approved research plan ("do it"). General-purpose Agent dispatched.
- 2026-04-19 ~08:59 CDT — Agent returned after ~10 minutes / 28 tool calls. Research doc written. Key recommendations: passive detection via `ClaudeClient` wrapper with active probing only during half-open FSM state; six failure modes tracked (Down, Overloaded 529, Rate-limited 429, Garbage, Auth-broken 401, Latency-sustained); four enumerated response policies (P1 pause-all, P2 pause-LLM-only, P3 fall-through, P4 request-user) with per-mode defaults; compound OR notification threshold (5min wall-clock, 3+ paused scopes, user-relevant escalation trigger, or auth-broken); automatic resume for transient modes, gated for auth-broken and >30min dwells (tunable); own SQLite at `~/.pos/degradation.sqlite` with three tables; deterministic fallback template for when the Claude-authored safe-mode narrative can't be produced because Claude itself is the failure source. No halts. No amendments to sealed components required. Complexity estimate 320–410 AI-minutes.
- 2026-04-19 09:04 CDT — owner approved research recommendations ("approved, let's go").
- 2026-04-19 09:08 CDT — Proposal drafted at `proposal.md`. Ten deliverables (D1 ClaudeClient adapter + D2 per-mode FSMs + D3 detection rubrics + D4 response-policy dispatch + D5 notification threshold + D6 safe-mode narrative + fallback + D7 resume mechanism + D8 state preservation + restart reconciliation + D9 OTel emission + D10 bundled docs + 1-hr outage verification). Three the primary persona leans (Tier-2-default with Tier-1-for-auth-broken; Haiku 4.5 as default narrative model, workspace-tunable; `~/.pos/degradation-config.yaml` for per-workspace tunability). Three the primary persona inferences flagged. Awaiting ruling recorded.
- 2026-04-19 09:16 CDT — owner approved all three the primary persona leans ("your lean is fine on all 3, let's go").
- 2026-04-19 09:20 CDT — Handoff brief drafted at `brief.md`. Covers D1–D10; rulings recorded baked in (six failure modes with defaults, four response policies with per-mode defaults, compound-OR notification threshold, Tier-2-default + Tier-1-for-auth-broken, Haiku-4.5 default narrative model, 30-min resume-gate threshold, own SQLite at ~/.pos/, YAML config for workspace tunability). Three the primary persona inferences flagged (ClaudeClient adapter everywhere, detection threshold calibration from research conventions, single-template vs per-mode fallback). Awaiting owner's review before dispatch.
- 2026-04-19 09:30 CDT — owner approved brief ("approved"). General-purpose Agent dispatched for D1–D10 full build.
- 2026-04-19 ~09:56 CDT — Agent returned after ~25 minutes / 107 tool calls. All D1–D10 complete across three commits on `pos-v2`: `141ff6d` (D1–D8 scaffold), `7c4ff11` (tests), `d522070` (D10 sim + FPR + docs). Graceful-degradation: 93 tests passing. All five sealed components still at baseline. Garbage-detector false-positive rate: **0/20 = 0.00%** on synthetic known-good corpus (well below the research's 15% ceiling). One-hour-outage simulation: **all eight invariants PASS** (I1–I8: pause/resume balanced; started/resolved balanced; 3 LLM scopes paused→resumed; 0 deterministic scopes paused; 0 orphan spans out of 47). Complexity: well under the 320–410-minute estimate. One documented non-deviation: **memory-system detection blind spot** — Graphiti owns its AnthropicClient internally so memory's extraction calls cannot route through the ClaudeClient adapter without amending memory/Graphiti (forbidden by the no-amendment rule). Mitigation: pyee subscription on `ScopeRuntime.subscribe_all()` + `record_scope_fail()` heuristic signal-mapping catches memory-triggered failures indirectly via the scope that triggered them. Documented in `docs/architecture.md` under "Memory-system detection blind spot" — flagged for the primary persona/the owner review at seal time, not silent.
