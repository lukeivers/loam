# Pre-registration — deliberate-reasoning-layer slice 1

**Status:** PRE-REGISTERED. This document fixes the experiment's metric,
task set, "better" definition, blind-judge protocol, and the
theory-prediction-vs-generic-lift discriminator **before any escalated-mode
run is scored**. Per plan §3.3 / AC.MGRL.4 the commit that lands this file
MUST be an ancestor of the first scored-run commit in the git ref graph
(`feedback_published_state_only_from_git_refs` — the ordering is the
tamper-evidence, not this prose).

**Plan:** `docs/plans/metacognitive-gate-reentrant-loop-slice1.md`
(RATIFIED, commit `c0c584f4`). This document implements the plan's §0
honest-boundary requirement made structural (D-MGRL.3).

**HARD honest-boundary (plan §0, non-negotiable):** a null result, or a
result that is generic-lift-only with the theory-prediction NOT confirmed,
is a VALID and reported outcome. Manufacturing a metric to avoid a null is
the failure this pre-registration exists to prevent (plan §8 trigger 2 /
RF-3). The metric below was chosen because it is objective and
machine-checkable; if it had not been definable non-gameably, the honest
action would have been to HALT (it was definable — see §1).

---

## §1 The task set (FIXED)

The task set is a fixed set of items, each with a **single machine-checkable
canonical answer**. Objective correctness is the only metric — there is no
human-rated quality dimension, so there is nothing to talk past, rationalize,
or game. Each item carries:

- `id` — stable item id.
- `prompt` — the task text.
- `canonical_answer` — the ground-truth answer (string, compared after
  deterministic normalization: trim + lowercase + collapse internal
  whitespace).
- `task_class` — the class label (feeds the gate's NOVELTY signal).
- `trigger_intended` — which gate trigger this item is constructed to carry
  (`low_confidence` | `novelty` | `stakes` | `none`). Items with `none` are
  the **control items the gate is expected to decline** — they are the
  flagged-vs-unflagged discriminator's negative arm.

The task set lives at `framework/deliberate-reasoning/experiment/task_set.json`
and is FROZEN by this pre-registration. Adding/removing items after the first
scored run invalidates the pre-registration.

**Why this task set is non-gameable (plan §8 trigger 2 discharge):** the
outcome is exact-match against a canonical answer under a fixed normalizer.
The judge cannot be persuaded; a wrong answer is wrong regardless of how it
is phrased. The class of tasks (arithmetic / factual-lookup with a unique
answer) was chosen precisely because "better" reduces to "correct", which is
objective. Tasks with subjective quality were deliberately excluded — they
would reintroduce the gameability §8 trigger 2 forbids.

## §2 The metric — what "better" means (FIXED)

For a single arm on a single item: **`correct` ∈ {0, 1}** = the arm's final
answer, normalized, equals the canonical answer, normalized.

- **Per-arm score** = sum of `correct` over the task set (count of items the
  arm got right).
- **Aggregate quality delta (generic lift)** = `escalated_correct_total −
  baseline_correct_total`. A positive value means the escalated arm answered
  more items correctly. **This is generic lift and by itself confirms
  NOTHING about the theory** (any "think harder" intervention can produce
  it — plan §3.3).
- **No-degradation check** = on no item does the escalated arm flip a
  baseline-correct answer to incorrect beyond ZERO tolerance. The
  no-degradation guard (D-MGRL.2) makes the tolerance exactly 0: an
  escalated regression on an already-correct item is a guard failure, not
  an accepted cost.

## §3 The theory-prediction-vs-generic-lift discriminator (FIXED — load-bearing)

The theory predicts the gain is **NOT uniform**: it predicts the correctness
gain **concentrates on the turns the gate flagged (escalated)** and is
**absent on the turns the gate declined to escalate** (the `trigger_intended
== none` control items). Generic lift would raise correctness everywhere or
randomly; the theory's signature is concentration on flagged turns that
tracks the firing trigger.

The discriminator is reported as TWO separately-computed quantities:

- **`gain_on_flagged`** = (escalated correct − baseline correct) summed over
  items the gate ESCALATED.
- **`gain_on_unflagged`** = (escalated correct − baseline correct) summed
  over items the gate DECLINED to escalate. By construction of the
  default-OFF / gated design, the escalated arm equals the baseline arm on
  unflagged items, so **`gain_on_unflagged` MUST be 0** — if it is non-zero
  the default-OFF guarantee (AC.MGRL.2) is broken and the run is INVALID.

**Pre-registered verdict rule (applied without further judgment — AC.MGRL.4):**

- **THEORY-PREDICTION CONFIRMED** iff `gain_on_flagged > 0` AND
  `gain_on_unflagged == 0` AND the no-degradation check holds (zero
  regressions). The gain exists and lands exactly where the theory says it
  should.
- **GENERIC-LIFT-ONLY** iff `gain_on_flagged > 0` but the gain does not meet
  the concentration bar above (e.g. a non-zero `gain_on_unflagged`, which
  also flags a default-OFF breach) — reported as quality-lift NOT
  attributable to the theory's specific prediction.
- **NULL** iff `gain_on_flagged == 0` (escalation produced no measurable
  correctness gain on the flagged turns). A null is INFORMATIVE and reported
  as such (RF-3); it is not buried.

Per AC.MGRL.6 the result artefact reports the aggregate delta AND this
flagged-vs-unflagged breakdown separately; "the theory's prediction held" is
a DISTINCT verdict from "escalation helped on average."

## §4 The blind-judge protocol (FIXED)

The judge that scores each answer is **blind to the hypothesis and to the
arm**: it receives only `(prompt, answer, canonical_answer)` and returns
`correct ∈ {0,1}` via the deterministic normalizer in §2. It does NOT
receive the arm label (baseline vs escalated), the trigger, or any
hypothesis framing. Because the scorer is a deterministic exact-match
checker, blindness is total by construction — there is no channel through
which the hypothesis could leak into the score (plan §3.3, AC.MGRL.5). The
judge implementation is `experiment/judge.py::score_answer`; its signature
structurally excludes the arm label.

## §5 The procedure (FIXED)

1. For each task-set item, the BASELINE arm produces an answer with the
   deliberate layer OFF (the fast-path draft, unperturbed).
2. For each item, the ESCALATED arm runs the same draft through
   `process_turn` with the layer ENABLED; the gate decides; on escalation
   the deliberate loop runs.
3. The blind judge scores every answer from both arms against the canonical
   answer.
4. The result artefact computes: aggregate delta, `gain_on_flagged`,
   `gain_on_unflagged`, the no-degradation check, and the §3 verdict.

The first scored run's commit MUST be a DESCENDANT of this file's commit
(AC.MGRL.4 git-ancestry evidence).

## §6 Degrees-of-freedom disclosures (RF-4)

- The task-set authorship is a degree of freedom (RF-4). It is disclosed
  here and frozen by this commit; the items are constructed so each carries
  a clear intended trigger and the control items carry none.
- The loop's critic in a fully-LLM run is `claude -p` (subscription path,
  `feedback_no_anthropic_api_key`). For a deterministic, reproducible,
  zero-token reference run, a deterministic reference critic that applies
  ONLY evidence-backed canonical corrections is supplied
  (`experiment/runner.py`); this reference run demonstrates the harness and
  the discriminator end-to-end without spending tokens, and its critic is
  evidence-bound by construction (it corrects only against the canonical
  answer key, never free-form). An LLM-critic run is the slice's optional
  follow-on and uses the identical task set + judge + verdict rule.
