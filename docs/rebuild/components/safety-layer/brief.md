# Handoff Brief — Safety Layer

**For:** the general-purpose Agent dispatched to build the safety layer.
**From:** the primary persona, 2026-04-19 16:36 CDT.
**Status:** awaiting owner's review of this brief; not yet dispatched.

---

## 1. What you are building

The safety layer for pOS on the `pos-v2` branch of `the existing workspace root`. It delivers three kill switches (scope, session, system), a deterministic always-ask list enforced at the activation boundary, and a dangerous-operation gate that composes on top of the ask list for irreversible-blast-radius actions.

The work is greenfield Python on `pos-v2`. It consumes sealed components — it does not amend them.

## 2. Authoritative documents (read in this order before you start)

1. **This brief** — gives you the objective, constraints, and acceptance criteria in operational form.
2. **`docs/rebuild/components/safety-layer/proposal.md`** — the contract the owner has approved. Binding. Halt and signal rather than deviate.
3. **`docs/rebuild/components/safety-layer/research.md`** — design detail, integration patterns, structural-enforcement rationale, sequence diagrams. Reference only; the proposal is the contract.
4. **`docs/rebuild/spec/pos-v2-objectives-spec.md`** — spec v1.0 + v1.1 + v1.2 addenda. The safety objective is in v1.0 Foundational layer.
5. **`docs/rebuild/STATE.md`** — governing rules for this rebuild. Rules 1, 2, 3 are the ones you will feel most — five-gate chain, no deviation, ODD methodology.

## 3. The objective (single sentence)

Deliver the safety layer such that each of the three kill switches is independently testable with bounded-time halt, the always-ask list is a Pydantic-validated artifact that structurally cannot be reduced below the framework floor, and a sample irreversible-blast-radius scope is blocked at the gate in a test run — all without amending any sealed component.

## 4. Hard constraints (non-negotiable)

- **Branch:** `pos-v2`. **Language:** Python 3.13.
- **Permitted runtime deps:** stdlib, pydantic, pyee, opentelemetry, PyYAML, duckdb. **Test-only:** pytest, pytest-asyncio.
- **No amendments to sealed components.** scope-of-work, orchestrator, graceful-degradation, primary-persona, objective-tracker, observability-aggregator, self-upgrade, memory-system are all sealed. If you conclude an amendment is required — halt and signal. Do not proceed. Signal format: named component + named surface + alternative you considered.
- **Deterministic-layer enforcement.** The always-ask list and dangerous-op gate are structural checks over validated schemas. No LLM inference inside the gate. The only LLM surface is the primary persona rendering the ask to the user, which is outside the gate.
- **Composition pattern:** the proposal locks IPC-wrapping of `activate_scope` as the non-amending path. If you find a different non-amending path that is cleaner, halt and signal before switching.
- **One-on-one channel only.** Reuse `OneOnOneChannel` from `primary_persona.introduction`; inherit its `is_group=True` rejection. No group-channel escape paths.
- **Fail-closed on channel loss.** If `OneOnOneChannel` is unreachable at gate-fire time, the gate stays BLOCKED; the scope stays `proposed`; no queue-and-fire.
- **Safety always wins on collision** with graceful-degradation. Safety's action proceeds; degradation records "superseded by safety" on its own episode.
- **Zero carryover from current pOS.** No imports from, references to, or patterns copied out of the current-gen Ruby pOS rules-file safety machinery.
- **Max-first.** If you introduce any LLM inference inside the safety layer itself, justify it explicitly in the commit message.
- **Halt on deviation.** Deviating from the proposal without the owner's explicit approval is forbidden.

## 5. Acceptance (ODD — 19 criteria, in proposal §4)

A1–A5: kill switches (scope/session/system) — spec clause (a).
A6–A10: always-ask list — spec clause (b), including ruling #4 (15-min floor) and ruling #5 (fail-closed).
A11–A14: dangerous-op gate — spec clause (c), including ruling #1 (tunable threshold with floor) and ruling #2 (clean system exit).
A15–A18: cross-cutting integration — no sealed-component mutation, aggregator-routed OTel, no group channels, no carryover.
A19: structural-impossibility defence-in-depth.

Each criterion is an objective. Tests are authored against the criterion directly, not against a prescribed behaviour. Negative cases re-extend as positive objectives — if you find one worth naming, add it as A20 and explain its rationale in the commit message.

## 6. Verify-against-code discipline

Before relying on any sealed-component surface, open the file on `pos-v2` and confirm the symbol exists with the shape you expect. Three specific places to check first because they have tripped prior research:

- `ScopeRuntime.cancel` signature and cascade behaviour via `ParentClosePolicy` (the research corrected a plan assertion that `halt-cascade` was a public symbol — it isn't).
- `Orchestrator.pause_activation`, `Orchestrator.resume_activation`, `Orchestrator.request_stop` signatures and semantics.
- `ScopeSpec.structural_hash()` — the proposal §8 flags this as an primary-persona inference; if the method doesn't exist, halt and signal with the alternative you'd use for approval-binding.

If any proposal-level claim about a sealed surface turns out to be wrong, halt and signal — do not improvise around the mismatch.

## 7. inferences recorded (proposal §8) — challenge any that feel wrong

Eight items in the proposal are my extrapolation from conversation rather than the owner's direct words:

1. 1-cent minimum floor on the tunable money threshold.
2. 15-minute minimum on the ask-list timeout.
3. `clear-system-kill` as the gesture name.
4. Seven framework-floor categories ratified as a set, not individually.
5. Session-kill cancels every active scope under the orchestrator instance.
6. The persona-phrase regex sets enumerated in research §4.
7. `ScopeSpec.structural_hash()` exists on `pos-v2`.
8. Two-step IPC nonce for system-kill.

Challenge any of these with a halt signal and a proposed alternative. They are not load-bearing unless the owner confirms — better to halt than accept a wrong inference.

## 8. Estimate

25–35 AI-minutes wall-clock. Anchor components: self-upgrade (~25 min), graceful-degradation (~20 min). The safety layer is structurally simpler than either.

**If the build exceeds 40 minutes, halt and signal.** The failure class to investigate is scope creep, not undersized estimate.

## 9. What I need back

On completion:

1. **Paths to the commits on `pos-v2`.** Atomic commits per phase acceptable; single commit acceptable if cohesion argues for it.
2. **Test results** — every A-criterion mapped to a passing test. If an A-criterion is unsatisfied, name it and explain why.
3. **Sealed-component diff check** — the output of `git diff --stat pos-v2` should show only `safety-layer/` and workspace-bootstrap changes. Any delta to a sealed component is a halt-signal condition.
4. **Any primary-persona inferences you challenged** and the alternative you chose (or halted on).
5. **Any halt signals** — named component + surface + what you tried first.
6. **Actual wall-clock vs the 25–35 min estimate.**

Return summary: under 500 words. The code and tests carry the detail.

## 10. Failure modes I am watching for

- "Improving" the spec while building. Don't. Deliver exactly what the proposal specifies; file enhancement ideas in the commit message for a later component.
- Monkey-patching a sealed component. Halt and signal instead.
- Skipping structural enforcement and replacing it with a runtime nag. The Pydantic validator is the enforcement — the clause-(g) pattern from self-upgrade is the template.
- Building LLM inference into the gate itself. The gate is deterministic; persona rendering of the ask is separate and outside the gate.
- Letting the estimate slip past 40 minutes quietly. Halt at 40 and signal scope creep for triage.

---

**End of brief.** the owner reviews this brief; on the owner's green light, dispatch follows.
