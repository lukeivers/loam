# pOS Rebuild — BACKLOG

**Last updated:** 2026-04-21 (foundation-audit disposition pass; "Option A" scope ruling).
**Purpose:** items surfaced during Phase 1–4 builds that are deferred — some await external triggers, some are held for post-first-release work, some are retired.

The foundation-audit (`components/foundation-audit/research.md`) subsumed the prior BACKLOG on 2026-04-20; this file is the post-audit residual. Item organisation below is by disposition rather than source component.

---

## Held for post-first-release

Ruling recorded 2026-04-21: pursue Option-A now (fix-smalls + BACKLOG grooming + foundation-audit seal); keep Options B and C around for after first release. The items below are the B/C scope preserved for that work.

### Decay-retention patches (six items, per `decay-retention-analysis.md`)

Each amends a sealed component's source; each needs its own research → proposal → build → seal cycle.

1. **Orchestrator heartbeat rollup** — `orchestrator/src/local_state.py`, `heartbeat` event rollup to daily summaries. Easy, big win, no event-sourcing complexity. ⭐⭐⭐
2. **Memory JSONL rotation** — `memory-system/src/observability.py`, `spans.jsonl` + `tokens.jsonl` daily rotation with bounded retention (aggregator has already ingested them). ⭐⭐⭐
3. **Graceful-degradation detection_events rollup** — `graceful-degradation/src/state.py`, per-mode daily aggregates. ⭐⭐⭐
4. **Scope-of-work terminal-scope `BudgetDebited` rollup** — `scope-of-work/src/events.py`, snapshot-and-truncate when scopes reach terminal state. Larger engineering effort. ⭐⭐
5. **Orchestrator `bind_refused` / `scope_activated` rollup** — daily counts. ⭐⭐
6. **Scope-of-work state-defining events for aged terminal scopes** — snapshot-and-truncate pattern. ⭐

Cross-cutting possibility: if three or more of these land, a shared `rollup-framework` library may be extracted.

### Cost-governance budget-extension diagnostic span

**`pos.cost.ceiling_post_hoc_overrun` diagnostic emission** — one-line addition when a scope's `BudgetExtended` event pushes aggregate spend past a rolling-window ceiling already. Build agent deferred as purely diagnostic (no acceptance coverage). Trigger: if observability ever surfaces unexplained post-hoc overruns.

---

## Awaiting external trigger (genuine deferrals)

Items that can't be blown through in a single session because they depend on work that doesn't exist yet.

- **Wire real dispatch primitive** — retire the mock producer in memory's D11 process-of-arrival capture. Trigger: dispatch primitive is designed (no component for it yet; may fold into orchestrator or primary-persona-layer's authoring pipeline).
- **Launchd plist re-activation** — for when pOS is actually run (not just built). `orchestrator/docs/operations.md` documents the exact install command. Trigger: first "running pOS" handoff.
- **250k-edge chaos stress test** — before long-term-volume durability claims. Trigger: long-term-volume durability claims are wanted.
- **Memory-system detection blind spot enhancement** — Graphiti owns its `AnthropicClient` internally; memory's Claude calls therefore do not route through the `ClaudeClient` adapter and do not generate direct degradation-detection signals. Current mitigation: pyee subscription on `ScopeRuntime.subscribe_all()` + `record_scope_fail()` heuristic catches memory-triggered failures indirectly via the scope that failed. **Future enhancement:** a Graphiti-level hook (or a LiteLLM-style client replacement at Graphiti init time) would give direct detection signals. Trigger: next time memory is touched for any reason, or when tightening detection is explicitly valuable.
- **First-run-orientation integration for `auto_update_mode`** — the self-upgrade framework ships with a config key `auto_update_mode: require_confirmation | notify_and_apply` defaulting to `require_confirmation`. The first-run orientation flow (onboarding component, explicitly deferred per 2026-04-20 15:28 ruling) should capture the user's preference and write it to `~/.pos/upgrade-config.yaml`. Trigger: onboarding-component design work.

---

## Documentation-only (no action required)

- **Defensive gate-refusal exclusion regex in self-correction** — self-correction's build verified that gate refusals raise `ApplicationError` before `orig_activate` runs, so `StateTransitioned(failed)` is never naturally emitted for a gate refusal. The exclusion regex in `triggers.py` is belt-and-braces for any manual `runtime.fail(reason="gate-ish-string")` path. Documented inline; no action unless pattern becomes noise.
- **Memory-system runs in its own `.venv` by design** (Graphiti + Neo4j driver deps are segregated). Running the full regression across all components requires per-component venv awareness; the shared `pos-v2/.venv` does not have `graphiti_core` installed. The `memory-system/tests/test_temporal.py` module imports `graphiti_core` at module scope, so collection in the shared venv fails. This is deliberate dep segregation, not a defect. If a future cross-component test-runner wants to unify, the memory-system venv is canonical for its tests. Audit-surfaced 2026-04-20.

---

## Retired as done

Items the audit (and this session) confirmed are complete or have been superseded.

- **Wire real scope-of-work primitive** (from memory-system build) — done via `RealScopeSourceAdapter` during primary-persona-layer build.
- **Build observability aggregator** — sealed 2026-04-19 11:24.
- **Build self-upgrade framework** — sealed 2026-04-19 14:12.
- **Seal-test template pattern** (cost-governance follow-on) — structural remedy committed `f94d602` 2026-04-20; retrofit to sidecar pattern for reversibility + cost completed on commit `af99046` 2026-04-21.
- **Retrofit SEAL_COMMIT sidecar-file pattern to reversibility + cost-governance** (from self-correction build) — completed on commit `af99046` 2026-04-21.
- **Fix workspace-bootstrap proposal §3.2 ordering claim** (audit finding F1) — completed on commit `55ab3e1` 2026-04-21.
- **Live pytest re-run for full-tree verification** (audit finding RED-16) — run completed 2026-04-20 post-audit: 794 tests in the shared venv + 30 in memory-system's own venv = 824 tests passing.

---

## Reference

- Decay-retention analysis: `docs/rebuild/decay-retention-analysis.md`
- Foundation audit (the source of this BACKLOG's re-grounding): `docs/rebuild/components/foundation-audit/research.md`
