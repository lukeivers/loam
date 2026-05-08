# ADR — ODD vs Outcomes (authoring-time vs runtime grader)

**Status:** Accepted (v0.4.0 Cycle 3).
**Date:** 2026-05-08.
**Closes:** AC.V040.5 per `docs/release-roadmap.md` §3.
**Cycle:** `docs/plans/v0-4-0-cycle-3-substrate-composition-routines-codereview-outcomes.md`.

---

## Summary

Anthropic's **Outcomes** primitive (Managed Agents, public beta as of 2026-05-06) and loam's **ODD** (Objective + constraints + Definition of Done) authoring discipline are **complementary, not competing**, but they operate at different altitudes in the build lifecycle:

- **ODD** is an **authoring-time discipline** — the plan-doc author writes objective + constraints + acceptance criteria BEFORE code; method is the builder's call; ODD §2.5 enforces every line of code maps to a named AC.
- **Outcomes** is a **runtime grader** — the harness provisions a separate-context-window grader Claude that scores the agent's artefact against a markdown rubric per criterion, returning either `satisfied` or per-criterion gaps that feed back into the next iteration.

The two **stack** when both surfaces are available — ODD shapes what gets built; Outcomes verifies it ran correctly. But Outcomes is **API-keyed (Managed Agents beta header `managed-agents-2026-04-01` + Anthropic API key)**, and loam-on-subscription **cannot directly compose on it** without violating the no-API-keys constraint per `feedback_no_anthropic_api_key.md`. The architectural divergence is **deliberate**, not a deficiency — it's the consequence of loam's subscription-only floor, which exists to reduce translation burden for the subscription-audience persona per `docs/VALUE_PROPOSITION.md`.

This ADR documents the divergence, names the stack-when-available shape, and pins loam's subscription-only architecture as the load-bearing reason the divergence exists.

---

## Context

### What ODD is

ODD is loam's plan-time discipline for Claude-attached work. Per `docs/design/odd.md` and `feedback_odd_no_non_objective_code.md`:

- A plan-doc names the **objective** (the outcome the work produces).
- The **constraints** scope what's in/out of bounds (fence + universal admissions + halt triggers).
- The **acceptance criteria** (ACs) are the testable observables that close the cycle. Each line of code, each branch, each test maps to a named AC; unnamed cases are violations.
- **Method is the builder's call** — the plan-doc names objective + constraints + ACs; HOW gets inferred from the constraints, not stated.

ODD is mechanically enforced by the dev-sdlc plugin's `loam amend apply` + `loam amend seal` ladder, the AC.D-sa.7 lint regex on `## 14.` method-decision-record headings, and the `feedback_test_outcome_altitude_required` rule (every AC set ≥1 outcome-altitude AC). It runs at the dev-mode workspace altitude — sealed-component amendment cycles, master plans, individual cycle plan-docs.

### What Outcomes is

Per the conference research at `<workspace>/.scratch/claude-output/claude-conference-features-2026-05-06.md` §2 + Anthropic's Managed Agents docs at `https://platform.claude.com/docs/en/managed-agents/define-outcomes`:

Outcomes is a Managed Agents primitive that lifts an API session "from conversation to work." The developer sends a `user.define_outcome` event with three fields:

- `description` — what the agent should produce.
- `rubric` — markdown either inline or via Files API `file_id`. Names the per-criterion grading axes.
- `max_iterations` — optional, default 3, max 20.

The harness provisions a **separate-context-window grader** (a second Claude instance with no view into the executor's working memory) that scores the agent's artefact against each rubric criterion **independently**. The grader returns either `satisfied` (all criteria green) or per-criterion gaps; gaps feed back to the executor for the next iteration. Result codes: `satisfied` / `needs_revision` / `max_iterations_reached` / `failed` (rubric-task contradiction) / `interrupted`.

Anthropic reports +10pp task success vs standard prompting, with +8.4% on .docx and +10.1% on .pptx file generation as named benchmarks.

### Surface-area constraints

Outcomes is **API-only**:

- Requires `managed-agents-2026-04-01` beta header.
- Requires an Anthropic API key.
- Exposed via REST (`POST /v1/sessions/:id/events`), official SDKs (Python/TS/Go/Java/Ruby/C#/PHP), and the `ant beta:sessions:events send` CLI.
- Stream surfaces three event types: `span.outcome_evaluation_start` / `_ongoing` / `_end`.
- Deliverables land in `/mnt/session/outputs/` and are fetched via the scoped Files API.
- Grader internal reasoning is opaque (heartbeat only).

Loam-on-subscription accesses Claude **only via the `claude -p` subprocess** (subscription auth), per `feedback_no_anthropic_api_key.md`. The `claude -p` surface does not expose Managed Agents primitives (Routines + Code Review are separate Claude Code substrates, not Managed Agents). Loam therefore **cannot directly compose on Outcomes** without:

1. Adding an Anthropic API key (violates `feedback_no_anthropic_api_key.md`).
2. Adding a `pip install anthropic` dependency (violates the same rule).
3. Wrapping `claude -p` in a hand-rolled grader-loop (re-implements Outcomes; violates Lens 1 "compose, don't reimplement" — but at zero subscription cost; conceivably useful where the user lacks API access).

The first two options are architectural floor-violations and not on the table for v0.4.0. The third is a future-work consideration for v0.6.0+ if the demand surface grows; for v0.4.0, the divergence stands.

---

## Decision

**Loam-on-subscription does not compose on Outcomes at v0.4.0.** The subscription-only architecture (`feedback_no_anthropic_api_key.md`) is the architectural floor. Outcomes is named as a substrate for users who run **both** subscription-loam and a separate Anthropic API project — those users can stack the two surfaces (ODD shapes the build; Outcomes grades the runtime artefact), but the stack lives in user-orchestration territory, not in loam's primary path.

The divergence is **deliberate** for three reasons:

1. **Subscription-only floor reduces translation burden for the primary audience.** Per `docs/VALUE_PROPOSITION.md`, the primary persona is a translation layer between user intent and AI execution. Adding API-key onboarding friction doubles the translation burden — every new loam user would need to configure both subscription auth AND an API key, AND learn when each surface applies. The subscription floor preserves single-credential simplicity.
2. **ODD covers the same ground at a different altitude.** Outcomes' rubric-driven grader iteration ≈ ODD's outcome-altitude AC verification, but ODD operates at **plan-doc authoring time** (the AC family is locked before code commits) while Outcomes operates at **runtime per-iteration**. ODD's mechanical enforcement (lint, sealed-component discipline, `feedback_test_outcome_altitude_required`) provides equivalent or stronger guarantees for the loam audience than Outcomes' opaque-grader loop. For users without API access, ODD is the only path; for users with API access, ODD is upstream of Outcomes.
3. **Loam's value-prop differentiator becomes clearer.** ODD as authoring discipline + Claude-Code-native runtime substrates (Routines + Code Review per the same v0.4.0 cycle) is a coherent harness for the subscription audience. Adding Outcomes-via-API would muddle the architectural story by introducing a second auth surface at the runtime altitude.

---

## Stack-when-both-available shape

For users with both subscription-loam AND an Anthropic API project running Outcomes — a niche audience but real:

1. **Authoring-time:** the plan-doc author runs through the standard ODD ritual (plan-doc + manifest + AC family + halt triggers + smoke). ODD locks the build's contract.
2. **Runtime (loam side):** loam dispatches the build via `claude -p`, produces the source-edit feat commit + manifest + apply + seal. ODD's outcome-altitude AC test verifies the artefact at seal time.
3. **Runtime (Outcomes side):** in a separate API session (the user's own Anthropic project), the user uploads the produced artefact + the plan-doc's AC family as the Outcomes `rubric`, dispatches a runtime-grader pass, and receives `satisfied` / per-criterion-gaps feedback.
4. **Feedback loop:** if Outcomes surfaces gaps, the user authors a corrective amendment cycle (plan-doc + manifest + apply + seal) — the gaps land as new ACs in the next cycle's §4. ODD remains the authoring-time discipline; Outcomes feeds runtime evidence into the next ODD cycle.

The stack is **not bidirectional inside loam** — loam doesn't read Outcomes API responses programmatically. The user is the bridge: they read Outcomes output, author the next ODD cycle, dispatch loam. This matches the harness-plus-primary-persona architecture per `docs/design/primary-persona-shape.md`.

This stack guidance applies only to the niche user. For the primary subscription-only audience, ODD alone is the authoring + verification surface.

---

## Why "deliberate" and not "deficiency"

Per harness-landscape research §4 Tension #1 + `feedback_locked_design_not_license_for_bad_outcomes.md`:

- **The lock is revisitable when outcomes turn bad.** If a future loam user reports that subscription-only + ODD-without-Outcomes is producing measurably worse build outcomes than ODD-plus-Outcomes for users with API access, the lock gets revisited. The architectural floor isn't a terminator on the question; it's the current best answer.
- **Bad-outcome signals to watch.** (a) Outcome-altitude AC pass-rates dropping over time on real fixtures (e.g., `jsts-playwright-app` per v0.4.0 C2). (b) User-reported "the runtime artefact diverged from what the plan-doc named" patterns. (c) Conference + competitor research surfacing rubric-driven runtime grading as table-stakes for the build-software-with-LLMs audience.
- **None of these signals are present at v0.4.0 ship time.** v0.4.0 C2's outcome-altitude verification on `jsts-playwright-app` shipped GREEN at $0.00 cost on subscription auth (per the C2 build report). The lock holds; revisit gate is "if signals materialize at v0.5.0+, re-extend this ADR."

The framing is **not** "loam can't do what Outcomes does" (it can; ODD operates at a different altitude with equivalent guarantees for the subscription audience). The framing is "loam chose subscription-only to reduce translation burden, and that choice is consistent with the build-software-with-LLMs prime objective per `docs/VALUE_PROPOSITION.md`."

---

## Out of scope

- A loam-side hand-rolled grader-loop that re-implements Outcomes via `claude -p` subprocess. Out of scope at v0.4.0; revisit at v0.6.0+ if user demand surfaces. Lens 1 disposition: this is "reimplement," not "compose"; high bar to add.
- Dual-credential support (subscription + API key in the same workspace). Out of scope; violates `feedback_no_anthropic_api_key.md`.
- BYOK (bring-your-own-key) workspace mode. Out of scope at v0.4.0; harness-landscape RR.* surfaced for owner ruling at v0.5.0+ if BYOK pressure mounts.
- Outcomes-style rubric format for ODD acceptance criteria. Already covered — ODD's AC family + `feedback_test_outcome_altitude_required` + outcome-altitude AC mark provides the equivalent rubric structure at authoring altitude.
- Multi-Agent / Dreaming / Webhooks composition. All API-only; same architectural divergence applies; documented separately in conference research §3 Lens-1 alignment table.

---

## Composition with existing rules

- **`feedback_no_anthropic_api_key.md`** — the load-bearing constraint that motivates this divergence. Subscription-only is the floor; Outcomes is API-only; the two don't compose without violating the floor.
- **`feedback_test_outcome_altitude_required.md`** — ODD's runtime-evidence equivalent. Every AC set has ≥1 outcome-altitude AC; outcome-altitude tests invoke the production entry-point on real inputs. This provides the "did the artefact actually meet the contract" check that Outcomes provides at runtime, but at authoring altitude.
- **`feedback_locked_design_not_license_for_bad_outcomes.md`** — drives the "deliberate, not deficiency" framing + the revisit-when-outcomes-turn-bad escape hatch.
- **`feedback_trust_operational_reality.md`** — the source of the v0.4.0 C2 GREEN on `jsts-playwright-app` empirical signal that holds the lock.
- **`docs/design/primary-persona-shape.md`** — the harness-plus-primary-persona architecture that explains why the user (not loam) bridges the stack when both surfaces are available.
- **`docs/VALUE_PROPOSITION.md`** — the prime-objective grounding for the translation-burden-reduction rationale.

---

## Provenance

- `<workspace>/.scratch/claude-output/claude-conference-features-2026-05-06.md` §2 (Outcomes deep-dive) + §3 (Lens-1 alignment "Competing primitive — but architecturally inaccessible to loam") + §4 (Top features for integration).
- `docs/release-roadmap.md` §3 v0.4.0 AC.V040.5 (verbatim source for this ADR's existence + scope).
- `docs/plans/v0-4-0-cycle-3-substrate-composition-routines-codereview-outcomes.md` §5 + §10 — halt-and-surface findings + RF gaps that shaped this ADR.
- `docs/plans/research/harness-landscape-and-roadmap-rerank.md` §4 Tension #1 — BYOK divergence rationale source.
- Anthropic Managed Agents documentation: `https://platform.claude.com/docs/en/managed-agents/define-outcomes` (rubric + iteration semantics) + `https://platform.claude.com/docs/en/managed-agents/overview` (Multi-Agent + Dreaming + Webhooks context).
- `feedback_no_anthropic_api_key.md` — subscription-only architectural floor.
- `docs/VALUE_PROPOSITION.md` — translation-burden-reduction prime objective.

## Cross-references

- `docs/release-roadmap.md` §3 v0.4.0 AC.V040.5 → resolves here.
- `docs/plans/v0-4-0-cycle-3-substrate-composition-routines-codereview-outcomes.md` §4 AC.V040C3.5 + AC.V040C3.6 → ADR existence + cross-reference resolution verified at C5 release-level smoke gate.
- `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_routines_runtime_layer.md` "Out of scope" → Routines + Outcomes stack consideration.
- `docs/plans/example-code-review-composition.md` §7 → Code Review running inside Outcomes-style runtime grader loops.
