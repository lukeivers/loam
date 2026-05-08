# Principle derivation map — F4 (scope ↔ confidence) compositional reference

**Status:** Foundation reference doc. F4 compose-with/independent/partial table for the operating-principle corpus; doubles as M5 principle-conflict-resolution lookup.

**Doubles as:** primary M5 artefact — the compose-with/independent/partial table M5 references for routine principle-compatibility lookups.

## Purpose

Two purposes, in priority order:

1. **Show, for each principle in the corpus, whether F4 (scope ↔ confidence) informs it (compose-with), is unrelated to it (independent), or partially overlaps (partial).** This is *not* a strict derivation hierarchy — F4 is most-broadly-applicable but NOT a first axiom from which all other principles derive.
2. **Serve as M5's reference table.** When two principles conflict in a specific situation, the M5 four-step process (name conflict / name signals / make call / surface if non-obvious) uses this table to identify which principles share dominant signals (compose-with) vs which weight different signals (independent).

This table is **organisational reference, not an override list.** A "compose-with-F4" label does NOT mean "F4 wins when this principle conflicts." Conflict resolution is per M5, not per this table.

## Reading the columns

| Column | Meaning |
|---|---|
| **Principle** | The principle name + memory-file basename (or framework-doc location for non-memory principles). |
| **F4 relationship** | One of: `compose-with` / `independent` / `partial` / `IS F4` / `IS M5`. |
| **One-line justification** | Why the relationship label fits. Short (≤ 25 words). |

## Existing principles

| Principle | F4 relationship | One-line justification |
|---|---|---|
| **F4 — prompt scope ↔ confidence** (`feedback_prompt_scope_confidence.md`) | IS F4 | Self-reference; the principle this map is keyed on. |
| **M5 — principle conflict resolution multi-signal** (`feedback_principle_conflict_resolution_multi_signal.md`) | IS M5 | Self-reference; the conflict-resolution process this map serves. F4 is one of M5's named signals. |
| Background agents by default (`feedback_background_agents.md`) | independent | Channel/dispatch-shape rule grounded in main-session interactivity, not in scope-confidence. F4 doesn't decide what runs in background. |
| Trust operational reality over research citations (`feedback_trust_operational_reality.md`) | independent | Information-credibility rule (whose evidence wins) — orthogonal to scope-tightness. |
| ODD — no non-objective code (§2.5) (`feedback_odd_no_non_objective_code.md`) | compose-with | The implementation-stage application of F4: once AC list reaches high confidence, scope tightens to "build only what ACs require." |
| Plan before code — hard rule (`feedback_plan_before_code.md`) | compose-with | Code-time confidence requires plan-time confidence first; the rule mechanises the F4 sequencing for build work. |
| Agent prompts — scope only, no method prescription (`feedback_agent_prompts_scope_only.md`) | compose-with | The method-confidence-low → loose-scope application of F4 to dispatch authoring. |
| Always specify WD in agent dispatches (`feedback_always_specify_wd_in_dispatches.md`) | independent | Routing/working-directory correctness rule; orthogonal to scope-tightness. |
| No --amend in agent dispatches (`feedback_no_amend_in_agent_dispatches.md`) | independent | Audit-trail integrity rule; F4 has no bearing on commit shape. |
| Amendment dispatch speedups (`feedback_amendment_dispatch_speedups.md`) | partial | Three speedups; one (narrow test scope) is F4-shaped (tight-scope when confidence in test surface is high), two are independent process tweaks. |
| Summarize and surface decisions (`feedback_summarize_and_surface_decisions.md`) | compose-with | Owner-audience confidence-in-attention is bounded; tighten output to summary-form so owner can rule from it. F4 applied to authoring-for-owner. |
| Task-tracking discipline (`feedback_task_tracking_discipline.md`) | independent | State-persistence rule; F4 doesn't decide whether items go to a task list. |
| Duration estimation rubric (`feedback_duration_estimation_rubric.md`) | independent | Estimation-calibration rule; orthogonal to scope-tightness. |
| Session-start discipline (`feedback_session_start_discipline.md`) | independent | Context-load rule; F4 doesn't decide what to read at session start. |
| ODD/CDC scope — pos-v2 dev only (`feedback_odd_cdc_scope.md`) | independent | Applicability-boundary rule for ODD; meta-level (where does ODD apply), not within-ODD. |
| Default to background agents for multi-artefact authoring (`feedback_background_default_for_authoring.md`) | independent | Channel-shape rule; orthogonal to scope-tightness. |
| Serialize amendment builds in same working tree (`feedback_serialize_amendment_builds.md`) | independent | Concurrency-safety rule; F4 doesn't decide build serialization. |
| Verify post-amendment state from code (`feedback_verify_post_amendment_state.md`) | compose-with | Confidence-in-prior-agent-reports is intrinsically bounded; loosen scope of "trust" by reading code directly. F4 applied to evidence-source choice. |
| VALUE_PROPOSITION as prime objective (`feedback_value_proposition_as_prime_objective.md`) | independent | Outcome-orientation prime; ODD-itself class. F4 is about *how to scope* an objective, not *what the prime objective is*. |
| Subagents must halt on ODD violations (`feedback_subagent_odd_violation_halt.md`) | partial | Halt-and-surface IS the F4 loose-scope-at-low-confidence escape hatch when applied to in-flight discoveries — but the rule is also independently grounded in audit-trail integrity. |
| Loose AC text → fix the AC, not implementation (`feedback_loose_AC_text_fix_AC_not_implementation.md`) | compose-with | Direct F4 corollary at AC-stage: tighten the AC text post-build (raise confidence) rather than re-shaping implementation. |
| Strict autonomy — don't pause on authorized work (`feedback_strict_autonomy_no_pause_for_authorized_work.md`) | independent | Channel/control rule about already-authorized work; F4 doesn't arbitrate authorization-state-vs-pause. |
| Sealed-component dispatches must explicitly name pos-amend apply (`feedback_dispatch_explicit_pos_amend_apply.md`) | compose-with | Confidence-in-agent-inferring-mechanism is low; tighten scope by naming the mechanism explicitly. F4 applied to dispatch-prompt method-naming. |
| Verify the dispatch is the right action before sending (`feedback_verify_dispatch_before_sending.md`) | compose-with | Confidence-in-dispatch-shape must be raised before the dispatch lands. F4 applied to the dispatcher side of the workflow. |
| Critical thinking on deviations (`feedback_critical_thinking_on_deviations.md`) | compose-with | Enumeration is the loosening response when confidence in first-viable resolution is low. Direct F4-shaped procedure. |
| Asymmetric problem solving (`feedback_asymmetric_problem_solving.md`) | partial | Surfaces high-leverage points (independent of F4); but spotting "unjustified ceremony" is often confidence-in-current-shape that turns out to be unjustified — F4-shaped. |
| FUTURE_IDEAS_DRAFT.md no-overhead capture (`feedback_future_ideas_draft_workflow.md`) | independent | Capture-channel rule; F4 doesn't decide where ideas land. |
| Specific claims must be verified or marked as guesses (`feedback_specific_claims_verified_or_marked_guess.md`) | partial | Direct calibration rule (independent of F4); but "marking as guess" is *exactly* the F4 loosening response when confidence in a specific number is low. AMBIGUOUS — could equally be labeled compose-with. |

## F3 + F2 — operating-tier extensions

| Principle | F4 relationship | One-line justification |
|---|---|---|
| **F3 — Swarming (recursive decomposition)** (`feedback_swarming_recursive_decomposition.md`) | compose-with | F3's stopping criterion uses scope-confidence (F4) as its primary signal — decompose when subtask scope is tighter; stop when it isn't. Model-selection audit (`model-rationale` line) also operationalises confidence-tracking. F3 + F4 are the strongest compose-with pair in the corpus. |
| **F2 — Ruthless Feedback** (`feedback_ruthless_feedback.md`) | independent | Communication-honesty principle; the obligation to surface problems does not derive from scope-tightness. Core is independent; composes with F4 only at evidence-quality level (when confidence in a gap is mixed, the "name the evidence" requirement acts as a calibration check on the feedback itself). |

**Top three compose-with-F4 compositions in F3:**

1. **Stopping criterion composition.** F3's rule "decompose until each subtask's acceptance criterion is strictly tighter than the parent's; stop when the split adds only coordination overhead" is the direct application of F4 at the decomposition-decision level. The question "is the next subtask's scope tighter?" is a scope-confidence measurement.

2. **`needs_fresh_start` as F4 escape hatch.** When the judge fires `needs_fresh_start`, the correct response (discard-and-restart) maps directly to F4's "when confidence in current shape is low, loosen scope and re-enumerate." Completing a diverged subtask chain is the over-tight-at-low-confidence failure mode applied to swarm execution.

3. **Model-selection rationale as scope-tightness annotation.** The `model-rationale` line in the dispatch brief is the F4 scope-tightness annotation (`intended scope-tightness: loose, because high-uncertainty synthesis → Opus`) applied to model selection specifically. Each tier of a swarm (planner / worker / judge) has a different confidence level → different scope → different model tier.

## Counts

- Total principles in corpus: 30 (26 base + F4 + M5 + F3 + F2).
- Compose-with-F4: 10 — `odd_no_non_objective_code`, `plan_before_code`, `agent_prompts_scope_only`, `summarize_and_surface_decisions`, `verify_post_amendment_state`, `loose_AC_text_fix_AC_not_implementation`, `dispatch_explicit_pos_amend_apply`, `verify_dispatch_before_sending`, `critical_thinking_on_deviations`, `swarming_recursive_decomposition` (F3).
- Partial: 4 — `amendment_dispatch_speedups`, `subagent_odd_violation_halt`, `asymmetric_problem_solving`, `specific_claims_verified_or_marked_guess`.
- Independent: 14 — `background_agents`, `trust_operational_reality`, `always_specify_wd_in_dispatches`, `no_amend_in_agent_dispatches`, `task_tracking_discipline`, `duration_estimation_rubric`, `session_start_discipline`, `odd_cdc_scope`, `background_default_for_authoring`, `serialize_amendment_builds`, `value_proposition_as_prime_objective`, `strict_autonomy_no_pause_for_authorized_work`, `future_ideas_draft_workflow`, `ruthless_feedback` (F2).
- Self-reference: 2 (F4 + M5).

**Cross-check on counts:** 10 compose-with + 4 partial + 14 independent + 2 self-reference = 30. Matches total.

## Calibration notes (per Ruthless Feedback applied to this table)

Two of the classifications are flagged AMBIGUOUS — surfaced for owner ruling rather than auto-classified:

1. **`specific_claims_verified_or_marked_guess`** — labeled `partial` in the table above, but the rule "marking as guess when confidence is low" is *exactly* F4 applied to numeric claims. Could equally be labeled `compose-with`. The `partial` choice reflects that the calibration-trait grounding is independently strong (it would exist even without F4). **Owner ruling needed:** is the F4 framing dominant enough to relabel as compose-with?

2. **`subagent_odd_violation_halt`** — labeled `partial` in the table above. The halt-and-surface mechanism IS F4-shaped (loose scope when discovery confidence is low), but it's also independently grounded in ODD's §4 re-extension pattern, which predates F4 codification. The `partial` label may underweight the ODD-§4 lineage. **Owner ruling needed:** is this better labeled `independent` (ODD-§4 inheritance dominant) or `partial` (both lineages active)?

The remaining 26 classifications are stated with reasonable confidence; the justifications above are the basis. If owner reads the table and disagrees on any specific label, the disagreement itself is M5 input — name the conflict, the signals weighted differently, and re-rule.

## How M5 uses this table

When two principles conflict in a specific situation:

1. **Look up both principles in the table.** If both are labeled compose-with-F4, scope-confidence is likely a dominant signal — apply F4 directly as part of the M5 four-step process.
2. **If one is compose-with and one is independent,** the conflict likely turns on a signal *other* than scope-confidence. The M5 process names that other signal (reversibility, blast radius, audience, time pressure, information asymmetry, ...).
3. **If both are independent,** the conflict is squarely in the open-signal-list territory; F4 plays no role. M5 process applies as normal.
4. **Partial labels** are warning flags — the relationship to F4 is conditional on the specific situation. Examine whether F4 applies in *this* instance before weighing it.

The table is a lookup, not an oracle. Don't substitute table-checking for the four-step process — the process is what produces the resolution; the table just inputs to step 2.

## Maintenance

- **Every new feedback memory** added to the corpus must include a derivation/relationship line in its body or front-matter (per M5's procedural rule). When such a line is added, add the principle to this table with the matching label.
- **Reclassifications** (an existing principle's relationship to F4 changes as understanding sharpens) are valid and expected. Update the row + add a one-line note in this section.
- **The signal list in M5** is explicitly open — adding a new signal to M5 does NOT require re-doing this table; this table only maps F4 specifically.
