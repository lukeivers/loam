# Component — Observability Aggregator

**Created:** 2026-04-19 10:04 CDT. **State:** ✅ **COMPLETE — sealed 2026-04-19 11:24 CDT.** All D1–D9 landed across 8 atomic commits on `pos-v2`; 60 tests green; zero sealed-component regressions; 100% NL translate accuracy; self-observability and privacy verified byte-level. Third Phase 2 component sealed.

---

## Parent objective (from spec v1.0 Foundational layer + v1.1 R11)

> **Observability, introspection, replay.** Every autonomous action produces an auditable record. The user can replay a session's decisions after the fact. The system can answer "why did you do X at time T" by citing the objective, constraint, or knowledge that caused the decision.
>
> Acceptance:
> - Every action writes a record containing actor, timestamp, operation, inputs, outputs, and tool calls; completeness verified by a sampled test reconstructing an action from its record alone.
> - Replay of a past session reproduces the decision chain end-to-end.
> - "Show me why" queries return a cited answer pointing at the specific objective, constraint, or knowledge.

Plus **v1.1 R11 OpenTelemetry as internal trace format** (already satisfied by each component's per-operation span emission), **v1.1 R12 per-prompt-type cost attribution** (already emitted by memory + scope-of-work + primary-persona + orchestrator + graceful-degradation).

## Why this component is next

1. **Every sealed component already emits OTel spans and events** per v1.1 R11. What's missing is the consumer — the aggregator that stores, indexes, and serves those emissions. Every primitive has been built A1-safe: emission succeeds with no consumer. Now we build the consumer.
2. **Lighter weight than self-upgrade** and a natural fit before it — self-upgrade's framework-level migration story benefits from observability being in place (upgrade events are themselves observable).
3. **Completes the "everything is observable" story** and delivers the spec's "why did you do X at time T" query capability.

## Artifacts

- `research-plan.md` — drafted 2026-04-19; awaiting owner's approval
- `research.md` — not yet produced
- `proposal.md` — not yet produced
- `brief.md` — not yet produced
- `outputs/` — empty

## History

- 2026-04-19 10:04 CDT — component created; research plan drafted; awaiting owner's approval before research begins.
- 2026-04-19 10:25 CDT — owner approved research plan ("everything has been good so far, just going to trust you on this one. approve."). General-purpose Agent dispatched.
- 2026-04-19 ~10:36 CDT — Research returned with 3 halt signals (Reading A vs B for replay; DuckDB as new dep; ephemeral stub vs drop). ruling recorded all three 2026-04-19 10:45 CDT.
- 2026-04-19 10:50 CDT — Proposal drafted.
- 2026-04-19 10:51 CDT — Ruling recorded on the two proposal open questions — decaying retention adopted per the example provided pattern; derived-only payloads dropped immediately.
- 2026-04-19 10:55 CDT — Handoff brief drafted.
- 2026-04-19 10:54 CDT — owner approved brief ("approved"). General-purpose Agent dispatched in background.
- 2026-04-19 ~11:20 CDT — Agent returned. All D1–D9 complete across 8 atomic commits: `6980550` (scaffold), `988a467` (D1+D2), `84d5ab0` (D4+D6), `6a6226f` (D7), `167bb9e` (D5), `8e9beff` (D8), `b597491` (tests), `a0906c1` (D9 docs). 60 tests passing. All sealed components still at baseline. NL-path: 100% translate accuracy (25/25) on the corpus, well clear of the 80% threshold. Self-observability: aggregator's own `pos.aggregator.*` spans filtered at the exporter and the spool drainer; no infinite-loop on repeated NL queries. Privacy: byte-level absence of payload for `derived-only` and `ephemeral` records. Complexity: ~30–35 min wall-clock, upper end of the calibrated band (the owner's 5–10× rule holds).
- 2026-04-19 ~10:36 CDT — Agent returned after ~10 minutes / 48 tool calls. Research doc written. Ingestion: in-process custom SpanProcessor + SpanExporter registered via orchestrator's `bootstrap.py` (workspace hook, not sealed-component amendment); memory's hand-rolled JSONL sinks handled via a tailer. A1 correction held rigorously — no sealed component modified. Storage: DuckDB recommended, SQLite fallback. Query: structured Pydantic API + NL-via-Claude for "show me why" + `pos obs` CLI. **Three halt signals:** (1) HARD — replay semantics spec-ambiguous (Reading A read-only playback vs Reading B deterministic re-execution; agent's lean is Reading A which satisfies spec without amendments, Reading B would require amending every LLM-calling component); (2) SOFT — DuckDB is a net-new dependency (not on the permitted list), soft-halt flagged explicitly; (3) SOFT — v1.1 R10 ephemeral episodes: minimal stub ("time T, ephemeral op happened") vs drop entirely. Complexity estimate ~505 AI-minutes, slightly above the 350–500 plan ceiling; dropping NL surface lands back in range.
