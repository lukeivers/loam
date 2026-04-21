# Component — Objective Tracker

**Created:** 2026-04-18 18:45 CDT. **State:** ✅ **COMPLETE — sealed 2026-04-18 19:56 CDT.** All D1–D9 landed; 86 tests green; scope-of-work's 77 tests still pass; zero regressions; single commit `f96fb4c`. **Phase 1 closed** — four primitives (memory, scope-of-work, primary-persona layer, objective tracker) all complete.

---

## Parent objective (from spec v1.0)

> *Objective:* a declared, testable outcome with a parent, a time horizon, and an acceptance criterion. Every objective nests under another objective until it reaches a top-level one the user has authored. Nothing in pOS operates against a vague wish; it operates against something measurable.

Acceptance (from spec):
- Every objective names its parent (or is marked root).
- Every objective carries a testable criterion and a time-bound/evergreen mark.
- No workflow, task, or scope exists without an objective trace to a top-level objective (v1.1 R3, objective-based at every level).

Relevant cross-cutting rules:
- **ODD** (Objective-Driven Design) — decisions 11–12 on the rebuild proposal. Tests are authored against objectives; negative cases are re-extended up the chain as new positive objectives.
- **Proportional planning** — v1.0 Architectural layer. Planning proportional to scope size.

## Why this component is next

1. **Completes Phase 1.** Memory, scope-of-work, and primary-persona-layer are complete. Objective tracker is the third and final Phase 1 primitive.
2. **Unenforced parent-references.** Scope-of-work carries "parent objective" references in its field set, but those references don't resolve anywhere — they're strings pointing at nothing. The tracker makes them resolvable and enforces the hierarchy.
3. **ODD is a load-bearing test methodology** that needs a real objective-tracking runtime to operate against. Every component sealed so far assumes objectives exist; now they actually do.

## Artifacts

- `research-plan.md` — drafted 2026-04-18; awaiting owner's approval
- `research.md` — not yet produced
- `proposal.md` — not yet produced
- `brief.md` — not yet produced
- `outputs/` — empty

## History

- 2026-04-18 18:45 CDT — component created; research plan drafted; awaiting owner's approval before research begins.
- 2026-04-18 19:01 CDT — owner approved research plan ("approve, move forward"). General-purpose Agent dispatched.
- 2026-04-18 ~19:09 CDT — Agent returned after ~8 minutes. Research doc at `research.md` (17 sections). Recommended design: Pydantic `ObjectiveSpec` with four-variant `CriterionType` discriminated union; strict forest-of-trees (DAG rejected for traceability ambiguity); separate SQLite file from scope-of-work, event-sourced for v1.1 R1 upgrade-fidelity coherence; **sidecar `ScopeObjectiveBinding` table** as the enforcement mechanism — no amendment to scope-of-work required. `parent_close_policy` defaults to `notify` (not TERMINATE — "parent objective abandoned" differs from "parent scope cancelled"). Two halt signals surfaced: (1) the research plan's claim that `ScopeSpec` had a `parent_objective_id` field was the primary persona's factual error — the field does not exist, but the sidecar binding approach makes this moot (no amendment needed); (2) "user-authored root" is undefined in the spec — agent proposes `authored_by: "user"|"system"` field on `ObjectiveSpec`, awaiting confirmation. Complexity: 340–420 AI-minutes (within the 300–450 plan range).
- 2026-04-18 19:15 CDT — ruling recorded on both halt signals: sidecar confirmed; `authored_by` refined to carry arbitrary provenance (either `"user"` or a persona handle) so sub-objectives authored by personas are traceable. Richer design than the agent's original binary proposal; enables debugging chains where a persona authored a wrong sub-objective.
- 2026-04-18 19:20 CDT — Proposal drafted at `proposal.md`. Nine deliverables (D1 primitive + D2 hierarchy + D3 criteria + D4 sidecar enforcement + D5 authored_by provenance + D6 ODD integration + D7 OTel + D8 upgrade-fidelity + D9 bundled docs). No sealed-component amendments required. Three minor open questions with the primary persona leans (time_bound default, scope_success auto-evaluation, re_open rationale mandatory). Awaiting ruling recorded.
- 2026-04-18 19:28 CDT — owner approved ("lets go with your choices and move forward") — time_bound mandatory at creation, scope_success auto-evaluates on scope events, re_open rationale mandatory.
- 2026-04-18 19:31 CDT — Handoff brief drafted at `brief.md`. Covers D1–D9; hard constraints name the owner's six baked-in decisions (sidecar enforcement, authored_by as provenance, notify default parent-close, mandatory time_bound, scope_success auto-eval, mandatory re_open rationale, plus the overarching "no amendments to sealed components"). Two the primary persona inferences flagged (dispatch-layer integration as mock in the build's integration test; scope_success pyee subscription at tracker startup). Awaiting owner's review before dispatch.
- 2026-04-18 19:33 CDT — owner approved brief ("approve to dispatch"). General-purpose Agent dispatched for D1–D9 full build.
- 2026-04-18 ~19:45 CDT — Agent returned after ~12 minutes (dramatically under the 340–420-minute estimate — scope-of-work's pattern library translated directly, no novel design problems). All D1–D9 complete; 86 tests green (D1:18, D2:10, D2b:5, D3:14, D4:9, D5:7, D6:9, D7:8, D8:6); scope-of-work's 77 tests still pass (no sealed-component amendment); single commit `f96fb4c` (32 files, 4,433 lines). Three minor deviations surfaced honestly: (1) baseline count was 78 not 77 (1 pre-existing skipped test dependent on live memory-system infra, unchanged); (2) added a D2b test file (5 tests) covering the owner's `notify` default parent-close which wasn't called out as a named D-letter; (3) `runtime.py` ~460 lines, STATE.md rule #9 exempts new-pOS from 200-line rule, cohesion-first. Recommended next action: declare tracker complete, close Phase 1.
