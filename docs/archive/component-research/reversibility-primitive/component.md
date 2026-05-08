# Component — Reversibility Primitive

**Created:** 2026-04-19 17:23 CDT. **State:** ✅ **COMPLETE — sealed 2026-04-20 08:19 CDT.** Commit `f657f8c` on `pos-v2`; 43/43 reversibility tests passing; zero sealed-component deltas; all nine sealed-component regression suites still green (scope-of-work 77, orchestrator 56, primary-persona 101, graceful-degradation 93, observability-aggregator 60, self-upgrade 120, safety-layer 64); ~30 min wall-clock (low end of 30–40 band). Second Phase 3 component closed.

---

## Parent objective (from spec v1.0 Foundational layer)

> **Reversibility-first execution.** Every scope declares its `reversibility_class` (`fully_reversible` | `compensatable` | `irreversible`). `irreversible` scopes cannot execute without a declared compensation path, or they fall under the safety layer's dangerous-operation gate and require explicit user approval. The system prefers reversible paths over irreversible ones when both achieve the same objective.
>
> Acceptance:
> - A scope declared `irreversible` without a declared compensation path or matching dangerous-op approval cannot activate (deterministic refusal).
> - A scope with a compensation path records the path and can invoke it on rollback.
> - When the system has a choice between a reversible and irreversible path to the same declared outcome, telemetry records which was chosen and why.

## Why this component is next in Phase 3

1. **Safety layer just sealed** and reads `reversibility_class` as a gate signal. The reversibility primitive promotes the class from a passive field to an **active declaration with a compensation contract** — the gate becomes "does a compensation path exist?" not "is the class set to irreversible?"
2. **Cost governance depends on this.** Cost ceilings are a reversibility concern — exceeding a ceiling without a compensation path to refund/unwind is a class of irreversible action. Reversibility ships before cost.
3. **Self-correction loop depends on this.** A system that detects its own error and wants to correct it needs to know which actions are reversible (try a new path) versus irreversible (compensate or escalate). Reversibility ships before self-correction.
4. **The scope-of-work `ReversibilityClass` enum already exists.** This component consumes and extends; it does not amend.

## Artifacts

- `research-plan.md` — drafted + revised + approved 2026-04-19 17:32
- `research.md` — produced 2026-04-19 17:40; ruling recorded on 4 questions 17:47
- `proposal.md` — drafted 2026-04-19 17:48; approved 17:56 ("approve")
- `brief.md` — drafted 2026-04-19 17:57; approved 18:23 ("approve")
- `brief.md` — not yet drafted
- `outputs/` — empty

## History

- 2026-04-19 17:23 CDT — component created (second Phase 3 component, follows sealed safety layer); research plan drafted; awaiting owner's approval before research begins.
- 2026-04-19 17:25 CDT — the owner pushed back on Q25's "might require amendment" framing; noted the objective-tracker sidecar + safety-layer structural-hash-helper precedent that handled similar structural-enforcement questions without amending scope-of-work. Plan revised: sidecar/activation-wrap is now the *default assumption* throughout §5, §7, §11, and the execution note. Amendment is last resort with named failure mode, not a first question.
- 2026-04-19 17:32 CDT — owner approved revised plan ("approve"). Background research agent dispatched with explicit references to both precedents (`ScopeObjectiveBinding`, `safety_layer.events.structural_hash`, safety IPC-handler wrap) as the templates to emulate.
- 2026-04-19 17:40 CDT — research agent returned after ~7.5 min wall-clock. Research doc at `research.md`. Sidecar/wrap pattern held throughout; one subtlety in §8.3 (reversibility wrap peeks into safety's store for the irreversible+no-binding+approval case — one-way read dep, not a cycle). Zero halt signals. Factual claims verified: `ReversibilityClass` enum confirmed at `scope-of-work/src/spec.py:50-53`; `ReversibilityTrigger` discriminated-union member already present at `spec.py:243-253`; safety reads `reversibility_class` at `safety-layer/src/dangerous_op.py:76-77`. Build estimate 35 min wall-clock, red-line 45. Four proposal-stage rulings surfaced.
- 2026-04-19 17:47 CDT — ruling recorded on all four questions ("approve all 4"). (1) Wrap registration order: reversibility first → safety second → orig_activate. (2) Rollback during active dangerous-op gate: refuse with `-32052 REVERSIBILITY_NOT_ACTIVATED`. (3) Default `budget_seconds`: `None`; per-workspace opt-in. (4) Reuse safety's `structural_hash` by import (single source of truth).
- 2026-04-19 17:48 CDT — proposal drafted at `proposal.md`. Encodes rulings as locked inputs, enumerates 26 ODD acceptance criteria (R1–R26), flags 8 primary-persona inferences for the builder to challenge, locks reversibility-first wrap order and `-32050..-32059` error-code range. Awaiting owner's approval.
- 2026-04-19 17:56 CDT — owner approved proposal ("approve").
- 2026-04-19 17:57 CDT — handoff brief drafted at `brief.md`. Points the builder at the proposal as authoritative; carries the verify-against-code discipline (four surfaces named), halt-at-45-minutes scope-creep trigger, wrap-ordering load-bearing rule, circular-import watch on safety's `structural_hash` import, and required return format. Awaiting owner's review before dispatch.
- 2026-04-19 18:23 CDT — owner approved brief ("approve"). Background build agent dispatched against the brief with the proposal as binding contract.
- 2026-04-19 18:37 CDT — Agent returned after ~30 min wall-clock. Commit `f657f8c` on `pos-v2`: single cohesive commit, 30 files, all within `reversibility-primitive/`. 43/43 tests passing in 1.27s. primary-persona inference #4 legitimately challenged and deviated: `rank_alternatives` suppresses `path_chosen` span on single-element lists (one-element "ranking" carries no reversibility signal worth recording). Inference #2 resolved against code: public projection accessor is `ScopeRuntime.get(scope_id)`; `ScopeProjection.parent_close_policy` confirmed on the public projection. Other inferences retained. Zero halt signals. Safety's `structural_hash` import was clean, no circular dependency. Verified: diff clean against `45a15b9`; all nine sealed-component regression suites still green.
- 2026-04-20 08:19 CDT — owner sealed ("seal"). Second Phase 3 component closed. Next up: cost governance.
