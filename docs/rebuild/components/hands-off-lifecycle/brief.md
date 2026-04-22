# Handoff Brief — Hands-Off Lifecycle

**For:** the general-purpose Agent dispatched to build the hands-off-lifecycle component.
**From:** Eve, 2026-04-21 18:44 CDT.
**Status:** awaiting owner's G3 review; not yet dispatched.

---

## 1. What you are building

The hands-off-lifecycle component for pos-v2. When an owner opens a Claude Code session in a fresh pos-v2 workspace, a running healthy system materialises on its own: memory sidecar launched and supervised, orchestrator running, per-component YAML defaults scaffolded, one confirmation sentence emitted. Ongoing lifecycle concerns (sidecar health, drain on recovery, loud escalation when self-heal fails) are the harness's problem, not the user's.

This component lands four sealed-component amendments as sub-cycles inside its own build — memory-system, orchestrator, graceful-degradation, workspace-bootstrap. Each amendment is individually sealed as its sub-cycle completes; the overall component's seal depends on all four landing cleanly.

## 2. Authoritative documents (read in this order)

1. **This brief.**
2. **`components/hands-off-lifecycle/proposal.md`** — the binding contract. Halt and signal rather than deviate.
3. **`components/hands-off-lifecycle/research.md`** — the design detail. Reference only; the proposal governs where they conflict.
4. **`context/handoffs/2026-04-17-eve-ruthless-review-pos-objectives.md`** — the pos-v2 spec.
5. **`context/pos-rebuild/STATE.md`** — governing rules for the rebuild.
6. **`docs/rebuild/FUTURE_IDEAS.md`** and **`docs/rebuild/VALUE_PROPOSITION.md`** in pos-v2 — the four-lens research discipline this component's design was evaluated against.

## 3. The objective in one sentence

Deliver the four approved sealed-component amendments plus the new hands-off-lifecycle component so that opening a Claude Code session in a fresh pos-v2 workspace produces a running healthy system without the owner doing anything they cannot do, and so that ongoing service-lifecycle concerns are owned by a supervisor that self-heals silently and escalates loudly only when it cannot.

## 4. Hard constraints (non-negotiable)

- **Branch:** `pos-v2`. **Language:** Python 3.13.
- **Permitted deps as established.** No new runtime deps without surfacing.
- **Exactly four sealed-component amendments approved in scope.** memory-system, orchestrator, graceful-degradation, workspace-bootstrap. If a fifth amendment is required, halt and signal. Do not improvise a fifth.
- **Memory is mandatory.** The Graphiti-backed memory system is the base layer. No design path that makes it removable or optional is acceptable.
- **Silent-stay-degraded is forbidden.** Degraded mode is urgent-recovery territory. Bounded retries, then loud escalation. A design that silently continues indefinitely in degraded mode fails the fourth lens.
- **Zero manual lifecycle management.** The fourth lens, load-bearing. Every ongoing-operation concern the owner would otherwise have to manage is the supervisor's problem.
- **Claude Code v2.1.87 `SessionStart` + FD-inheritance bug (issue #43123) mitigation is mandatory.** The session-start hook must not launch child processes directly; it must delegate to `launchctl bootstrap` / `systemctl --user start`. If in the future this mitigation proves insufficient, halt and signal rather than work around.
- **Halt triggers:** past 180 minutes without a sealed sub-amendment landed — halt and report partial progress. Any fifth amendment case discovered — halt and surface. Any regression on an unamended sealed-component test — halt.
- **Error-code range `-32090..-32099`** reserved to this component. No overlap with the five prior ranges (`-32040s` safety, `-32050s` reversibility, `-32060s` cost, `-32070s` self-correction, `-32080s` workspace-bootstrap).
- **A1 correction held.** OTel via `trace.get_tracer(...)` only; no `TracerProvider` construction.
- **Seal-test pattern mandatory per amendment.** Each amended sealed component gets its own `SEAL_COMMIT` sidecar update as its sub-cycle completes; the new hands-off-lifecycle component also carries a `SEAL_COMMIT` sidecar at overall seal.
- **Owner rulings from the proposal are locked.** The seven question rulings in §2.2 of the proposal are inputs, not options.
- **Halt on deviation.**

## 5. Acceptance (ODD — 21 criteria in proposal §5)

H1–H5: first-run scaffold (platform-unsupported halt, partial-scaffold halt, confirmation-sentence wording, one-shot emission, service-manager state).
H6–H10: supervisor state machine (state transitions, config-driven cadence, OTel spans, crash recovery, unit testability).
H11–H15: staging + drain (FIFO preservation, idempotent drain, overflow-to-caller, drain failure escalation, read-during-degraded).
H16–H18: loud escalation (per-class dedup, class-change re-notify + recovery close, Tier-1 cap exceedance discipline).
H19–H21: cross-cutting (diff scope exactly the four amendments + new component; all sealed-component regressions pass; fresh README lands).

Each criterion is a deterministic observable outcome. Tests target the criterion directly.

## 6. Verify-against-code discipline

Before amending any sealed component, open the relevant files and confirm the amendment surface exists as the proposal describes. Four priority verifications:

- **memory-system MemoryAPI surface** — the current ingest and search methods on which the degraded-mode branches attach. Confirm signatures before amending.
- **orchestrator `_startup()` + heartbeat loop** — the supervisor module integrates into the existing startup; confirm the integration point matches the research's recommendation.
- **graceful-degradation `fsm.py` + `detection.py`** — the new `memory_sidecar` failure mode adds to the FSM and the supervisor-signal subscription adds to the detection layer; confirm both files accept the amendment cleanly.
- **workspace-bootstrap phase model** — the new `first_run_scaffold` phase inserts before `before_orchestrator_start`; confirm the existing phase-enum and ordering engine accept the addition.

If any of these does not match the proposal's claim, halt and signal with the named file and symbol.

## 7. Eve's inferences (proposal §9) — challenge any that feel wrong

Eight items are Eve's extrapolation rather than owner rulings:

1. Per-amendment `SEAL_COMMIT` sidecar vs composite.
2. Error-code range `-32090..-32099`.
3. Amendment dependency ordering (bootstrap → memory → orchestrator → graceful-degradation).
4. `first_run_scaffold` phase placement before `before_orchestrator_start`.
5. `~/.pos/attention.md` as the durable unresolved-state surface.
6. Platform-halt diagnostic wording.
7. OTel span namespace `pos.hands_off_lifecycle.*`.
8. First-run detection heuristic (absence of `~/.pos/` and `~/.pos/bootstrap.yaml`).

Challenge any with a halt signal and an alternative. Inferences are not load-bearing unless the owner confirms; the substantive rulings are in §2 of the proposal.

## 8. Estimate

**155–250 AI-minutes wall-clock; red line at 180 unless progressing clearly.**

If the build exceeds 180 minutes, the named failure classes to investigate are: amendment 4's phase-placement complexity (the most architecturally delicate), memory-system's drain-correctness under recovery races, or a fifth unnamed amendment surfacing. Do not extend past 180 silently; halt and report partial progress.

## 9. What I need back

On completion:

1. **Paths to commits on `pos-v2`** — one per sub-amendment seal plus the hands-off-lifecycle component seal. Commit granularity is your call within that pattern.
2. **Test results** — every H-criterion (H1–H21, plus any H22+ you added with rationale) mapped to a passing test. Every amended sealed-component regression suite passing at its amended state. Every unamended sealed-component regression suite passing unchanged.
3. **Sealed-component diff check** — the final `git diff --name-only` should cover exactly: `memory-system/`, `orchestrator/`, `graceful-degradation/`, `workspace-bootstrap/`, new `hands-off-lifecycle/` (or equivalent surface). Anything else is a halt-signal.
4. **SEAL_COMMIT sidecars present** for all four amended components and the new component.
5. **Eve-inferences you challenged** and the alternative you chose (or halted on).
6. **Any halt signals** — named component + surface + what you tried first.
7. **Actual wall-clock vs the 155–250 min estimate.** Honest calendar minutes.

Return summary: under 600 words given the scope. Code and tests carry the detail.

## 10. Failure modes I am watching for

- "Improving" the scope mid-build. Don't — stay within the four approved amendments.
- Monkey-patching a sealed component instead of amending it cleanly. Halt.
- Regression on an unamended sealed component's test suite. Halt.
- Silent degradation paths — any code path that leaves the system indefinitely in degraded mode without escalation is a failure of the lens. Halt and redesign.
- Child-process spawning inside the `SessionStart` hook handler — hits the v2.1.87 FD bug. Must delegate to launchctl/systemctl.
- A fifth amendment case discovered. Halt and surface — the owner approved exactly four.
- Silent drop of a staged memory write on drain failure. Halt; this violates the mandatory-memory constraint.

---

**End of brief.** Owner reviews at G3; on their green light, dispatch follows.
