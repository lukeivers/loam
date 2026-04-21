# Component — Safety Layer

**Created:** 2026-04-19 14:13 CDT. **State:** ✅ **COMPLETE — sealed 2026-04-19 17:22 CDT.** Commit `45a15b9` on `pos-v2`; 64/64 safety-layer tests passing; zero sealed-component deltas; all sealed-component regression suites still green (scope-of-work 77, orchestrator 56, primary-persona 101, graceful-degradation 93, observability-aggregator 60, self-upgrade 120); ~35 min wall-clock (top of 25–35 band). First Phase 3 component closed.

---

## Parent objective (from spec v1.0 Foundational layer)

> **Safety and constraint layer.** Kill switches at scope-of-work, session, and system level. Categorical "always ask the user" list — short, explicit, testable. Dangerous-operation gates for irreversible-blast-radius actions.
>
> Acceptance:
> - Each kill switch (scope, session, system) is independently testable and stops work within a bounded time.
> - The "always ask" list exists as a testable artifact and is enforced at the deterministic layer.
> - A sample irreversible-blast-radius action is blocked at the gate in a test run.

## Why this component is first in Phase 3

1. **Safety is foundational** for everything Phase 3 adds on top (reversibility enforcement, cost ceilings, self-correction). Kill switches must exist before any further autonomous capability lands — they're the "big red button" the user needs when anything else goes wrong.
2. **The spec flags safety as first-class**, not an afterthought. The structural pattern (enforced at the deterministic layer, not advisory) matches how clause (g) worked in self-upgrade — schema-level impossibility, not runtime check.
3. **Several sealed components already have partial safety surfaces** — orchestrator has `pause_activation` (session-level halt), scope-of-work has `cancel` (scope-level), graceful-degradation hooks can fire. The safety layer composes these into a coherent user-facing kill-switch surface plus the always-ask-list + blast-radius-gate mechanisms.

## Artifacts

- `research-plan.md` — drafted + approved 2026-04-19 14:24
- `research.md` — produced 2026-04-19 14:35; ruling recorded on 5 questions 16:14
- `proposal.md` — drafted 2026-04-19 16:17; approved 16:35
- `brief.md` — drafted 2026-04-19 16:36; approved 16:56 ("go")
- `brief.md` — not yet drafted
- `outputs/` — empty

## History

- 2026-04-19 14:13 CDT — component created (first Phase 3 component); research plan drafted; awaiting owner's approval before research begins.
- 2026-04-19 14:24 CDT — owner approved research plan ("go for it"). General-purpose Agent dispatched (foreground).
- 2026-04-19 14:27 CDT — session compaction lost the foreground dispatch; re-dispatched as background agent (agentId internal). Awaiting completion notification.
- 2026-04-19 14:35 CDT — research agent returned (~8 min wall-clock). Research doc at `research.md`. Two factual corrections to the research plan owned (halt-cascade is not a public surface — cancel's `_cascade_to_children` is sufficient; SIGTERM is orchestrator lifecycle, not a user-facing safety surface). No sealed-component amendments required. Calibrated build estimate 25–35 AI-min (below plan's band). Five open questions surfaced for ruling recorded before proposal drafting.
- 2026-04-19 16:14 CDT — ruling recorded on all five questions. (1) Money threshold: tunable with floor. (2) System-kill: clean exit. (3) Tier-D close-associate: workspace additions. (4) Ask-list timeout: freeform `Nm|Nh|Nd` string with schema-enforced 15-minute minimum; YAML examples default to hour units. (5) Ask-gate when no `OneOnOneChannel` is reachable: fail-closed. Proposal drafting opens.
- 2026-04-19 16:17 CDT — proposal drafted at `proposal.md`. Encodes rulings as locked inputs, enumerates 19 ODD acceptance criteria (A1–A19), flags 8 primary-persona inferences for the builder to challenge, locks the IPC-wrapping composition pattern as the only non-amending path. Awaiting owner's approval.
- 2026-04-19 16:35 CDT — owner approved proposal ("approve").
- 2026-04-19 16:36 CDT — handoff brief drafted at `brief.md`. Points the builder at the proposal as authoritative; carries the verify-against-code discipline, primary-persona inferences flagged for challenge, halt-at-40-minutes scope-creep trigger, and required return format. Awaiting owner's review before dispatch.
- 2026-04-19 16:56 CDT — owner approved brief ("go"). Background build agent dispatched against the brief with the proposal as binding contract. Awaiting return.
- 2026-04-19 17:12 CDT — Agent returned after ~35 min wall-clock. Commit `45a15b9` on `pos-v2`: 35 files, +3668 lines, entirely within `safety-layer/`. 64/64 tests passing in 0.32s. A20 added per ODD re-extend pattern (safety-beats-degradation promoted from proposal prose to explicit testable objective). primary-persona inference #7 legitimately challenged: `ScopeSpec.structural_hash()` does not exist on `pos-v2` — builder implemented as standalone `safety_layer.events.structural_hash(spec)` helper (SHA-256 over `spec.model_dump_json()`), pure consumer, no amendment. Inferences #3 and #6 retained (CLI name + persona phrases deferred to workspace primary-persona layer). Inferences #1, #2, #4, #5, #8 adopted as written. Zero halt signals. Verified: `git diff --name-only 9e15379 45a15b9 | grep -v "^safety-layer/"` returns zero results; all six sealed-component regression suites pass.
- 2026-04-19 17:22 CDT — owner sealed ("seal"). First Phase 3 component closed. Next up: reversibility primitive.
