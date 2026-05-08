# Plan — Research: swarming × extraction composition design exploration

**Authored:** 2026-05-08.
**Status:** plan first per the plan-before-code rule. Research dispatch only; no code committed.

---

## Objective

Design-doc that makes legible **how reverse-ODD extraction composes with Lens 5 swarming** — Luke's 2026-05-08 insight: extracted objectives are natural partitions for swarm dispatch, so reverse-ODD doesn't just produce a contract, it produces a **decomposition** the swarm runtime can dispatch against. The doc explores the design space + names the smallest viable shape that ships this capability.

The output informs v0.4.x or v0.5.x scoping (likely v0.5.x given current roadmap-rerank proposal RR.3 SWE-bench submission lives at v0.4.0/v0.5.0). It is NOT a build dispatch; it's a design exploration that names the integration shape, the open questions, and the minimum work to validate.

## Constraints

- **Lens 5 swarming methodology is canonical.** From `CLAUDE.md` and `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_swarming_recursive_decomposition.md`: PlannerWorkerSwarm cycle, model-rationale field, EVAL_DIMENSIONS named-axis judging, max_planner_depth explicit. The design composes WITH these; doesn't replace them.
- **Reverse-ODD pipeline is canonical.** Extract → backing-map → gap analysis → build-next. The design extends the pipeline — extracted objectives become swarm-task inputs, not just informational artefacts.
- **Software-as-deliverable framing.** The composition's purpose is shipping working code faster on large repos (Luke: "doing it on Web would spend HOURS on a single agent"). Speed-to-software is the deliverable.
- **Subscription-only architecture.** Swarm dispatches use `claude -p` per loam's existing primitives; no API key.
- **No "rebuild" terminology.**

## Acceptance criteria

1. **AC.SX.1 — Composition shape named.** Doc names how extracted objectives get used as swarm-task inputs. Specifically: which extraction-stage output (objectives, backing-map, gap inventory, build-next) feeds the swarm planner; how the planner decomposes; how the worker tasks reference back to the objectives.
2. **AC.SX.2 — Decomposition strategies enumerated.** ≥3 partition strategies the planner could use:
   - Domain-clustered (group objectives by feature domain → one worker per domain)
   - Dependency-ordered (extract objective dependencies → worker phases respect topology)
   - Capability-grouped (objectives sharing a capability → one worker handles them together)
   Each: tradeoffs, when it fits, when it doesn't.
3. **AC.SX.3 — Worker scope question answered.** What does each swarm worker DO? Three candidates: (a) implement code for objective(s); (b) verify code matches objectives; (c) gap-fill (write missing tests / docs / migrations). Doc picks one or more for v1 + names rationale.
4. **AC.SX.4 — Coordinator pattern.** How does the planner reconcile worker outputs? Per Lens 5 the judge is `EVAL_DIMENSIONS` named-axis; doc names how this applies to multi-worker code-gen output (each worker's output gets evaluated against its objective's AC; cross-worker integration via gap-fill cycle).
5. **AC.SX.5 — Drift detection / `needs_fresh_start` semantics.** Lens 5 says drift = restart, not continue. Applied to swarm-extraction: when does the swarm restart vs continue? Concrete trigger conditions.
6. **AC.SX.6 — Smallest viable shape (v1) named.** What's the minimum implementation that demonstrates the composition? E.g., "single-domain partitioning + sequential workers + EVAL_DIMENSIONS judge per objective." Tradeoff: simpler = faster to ship; richer = closer to the full vision.
7. **AC.SX.7 — Open questions explicit.** ≥3 design questions the doc DOESN'T resolve + flags as needing future work. Examples: (a) coordinator state — file-based vs orchestrator-tracked? (b) cost-budget — per-worker vs aggregate? (c) restart-from-scratch granularity — full swarm or just diverged subtree?
8. **AC.SX.8 — Composition with existing v0.4.0 plan.** v0.4.0's outcome is "Loam ships working code from extracted objectives" with single-agent code-gen. The swarm-extraction doc names how it EXTENDS v0.4.0 (likely as v0.5.x — once single-agent code-gen ships + we have calibration data, swarm decomposition is the scale answer for big repos like checkmate Web).
9. **AC.SX.9 — F2 RF tension surfaced.** ≥1 tension. E.g., (a) swarm overhead vs single-agent simplicity — when does swarming pay off, when is it just cost? (b) drift detection sensitivity — too sensitive = restart-thrashing, too lax = diverged-but-shipping.
10. **AC.SX.10 — Word count 2500-4000.** Reference-doc thorough; not exhaustive.

## Out of scope

- **Don't propose specific build cycles.** Doc is the design framework; specific cycles come at v0.4.0 / v0.5.0 plan-author time.
- **Don't survey other swarm frameworks beyond what Lens 5 already references.** The kyegomez/swarms reference at HEAD `e48100a` is the existing canonical; the doc composes on it, doesn't re-survey the field.
- **Don't author swarm runtime code.** Pure design + recommendation.

## Authority chain

- `CLAUDE.md` Lens 5 (swarming primary spec)
- `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_swarming_recursive_decomposition.md` (full text on the Lens 5 patterns)
- `plugins/dev-sdlc/odd-extractor/` (the existing reverse-ODD pipeline)
- `docs/release-roadmap.md` v0.4.0 + v0.5.0 entries (target compositional fits)
- `docs/odd-semver-pinning.md` (each minor as ODD cycle — swarm-extraction would be the v0.5.x cycle's load-bearing capability)
- `<workspace>/.scratch/claude-output/programbench-loam-benchmark-v0.md` (ProgramBench is one of the validation surfaces)

## Output

Write to `docs/plans/research/swarming-extraction-composition.md`. Commit but do NOT push. NEW commit, no --amend.

Reply ≤200 words inline naming path + word count + the smallest-viable-shape (v1) recommendation + any halt-and-surface findings.

## Halt-and-surface

WD mismatch. Authority doc missing. Word count <2300 or >4200 (means scope drift). Push or tag attempt. The agent finds that the swarm × extraction composition fundamentally requires architectural changes the existing pipeline can't accommodate — surface explicitly rather than hide as "open question."
