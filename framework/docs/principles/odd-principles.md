# ODD principles — the universal foundation

**Status:** Principles tier (FR.1). Universal, exportable, project-agnostic. Anthropic-publish-grade.

**Companion artefacts:**
- **Machine-read declaration:** [`docs/design/principle-manifest.yaml`](../../../docs/design/principle-manifest.yaml) — the code-side surface a checker enumerates these principles from (the named-primitive registry). This document is the human-readable side; the manifest is the side a hook reads.
- **F4 compose-with / M5 lookup table:** [`docs/design/principle-derivation-map.md`](../../../docs/design/principle-derivation-map.md) — which principles compose with F4, which are independent, which partial.
- **Methodology tier (FR.2):** [`plugins/dev-sdlc/docs/odd-methodology.md`](../../../plugins/dev-sdlc/docs/odd-methodology.md) — how to *do* ODD in practice.
- **Project-bridge tier (FR.3):** [`plugins/dev-sdlc/docs/odd-in-loam.md`](../../../plugins/dev-sdlc/docs/odd-in-loam.md) — how ODD maps onto loam's concrete structures.

This document states *what* the principles are and *why they exist*. It is readable standalone, outside loam, by any project building on a frontier model. It does not duplicate the methodology tier's mechanical rules or the project-bridge tier's loam-specific mappings; it cross-references both.

---

## 0. What ODD is, in one paragraph

**Outcome-Driven Development: work is defined by its observable outcome, not by a sequence of steps.** A unit of work names an objective, the constraints that bound it, and the acceptance criteria that decide whether the outcome was reached. *Method is the builder's call.* This inverts the usual contract: instead of telling the builder how to proceed and hoping the result is right, ODD pins the result and leaves the route open. The payoff is that a result can be *verified* — an acceptance criterion is a checkable claim — where a sequence of steps can only be *audited for compliance*, which is a weaker guarantee.

ODD exists because the failure mode it guards against is endemic to AI-assisted work: an agent that follows instructions faithfully can still produce the wrong outcome, and without a checkable acceptance criterion no one notices until much later. The principles below are the discipline that makes outcome-definition trustworthy.

---

## 1. The named failure modes ODD guards against

Every principle in this corpus exists because a specific failure mode recurs by default. Naming the failure mode is the first half of the principle; the rule is the second half.

| Failure mode | What it looks like | The guarding principle |
|---|---|---|
| **Method-in-acceptance** | The acceptance criterion secretly states *how*, so it can only be met one way — the builder's judgment is foreclosed. | ODD §2.5 (no non-objective code); the method-in-AC test. |
| **Non-objective code** | Code, a branch, or a test that no acceptance criterion requires — scope crept silently. | ODD §2.5: every line maps to a named AC; unnamed cases are violations. |
| **Plan-time / code-time confidence inversion** | Building before the outcome shape is confident — the plan is written after the code, rationalising it. | Plan-before-code; F4 sequencing. |
| **Silent scope extension** | An agent discovers a problem outside its scope and quietly fixes it, erasing the boundary. | Halt-and-surface; F2 + scope discipline (the T1 composition). |
| **Silent principle conflict** | Two principles collide; the agent applies one and ignores the other without naming the conflict — the unmarked resolution becomes the next agent's implicit rule. | M5 (multi-signal conflict resolution). |
| **Over-tight / over-loose scope** | A prompt's scope does not track the author's confidence: narrow scope blocks the correct alternative at low confidence; broad scope burns tokens at high confidence. | F4 (scope ↔ confidence). |
| **Unverified specific claim** | A number, count, SHA, or timestamp asserted from memory rather than checked from ground truth. | Specific-claims-verified-or-marked-guess; information-trust ordering. |
| **Advisory rule that recurs** | A rule violated more than once despite living in the corpus — discipline alone has failed. | Structural enforcement on recurrence (the rule becomes a hook, not another memory). |

The last row is load-bearing for this candidate: **when a rule is violated more than once despite being written down, the fix is structural enforcement (a mechanical check), not a stronger promise.** This principle-foundation work applies exactly that pattern to the principle system itself — the principles become a machine-read manifest plus mechanical checks, not advisory prose alone.

---

## 2. The four foundational principles (extended treatment)

Four cross-cutting principles get extended treatment because they shape *how every other principle is applied*. They are declared as named primitives in the manifest (`F4`, `M5`, `F3`, `F2`); their `enforcement` field there records that they are advisory — they inform judgment rather than gate a single action — with the one carve-out noted under M5.

### 2.1 F4 — Prompt scope ↔ confidence

> **A prompt is a probability mass over agent trajectories; the tightness of the scope tracks the author's confidence that a single specific outcome is correct.**

When confidence in the outcome shape is high, scope tightly: narrow objective, tight constraints, acceptance that pins the outcome — *method stays the builder's call.* When confidence drops, loosen scope so the agent can think broadly. The two failure modes are symmetric: over-tight at low confidence blocks the actually-correct alternative; over-loose at high confidence burns tokens on options the author already knew were wrong.

F4 is the **most-broadly-applicable** shaping principle, but it is **not a first axiom** from which the others derive. Several principles (F2, plan-before-code, ODD itself) stand independent of F4 and compose with it rather than descend from it. The derivation map labels each principle compose-with-F4 / independent / partial.

**The tight-scope-vs-method-in-acceptance test:** tight scope leaves method *inferable from the constraints*; method-in-acceptance states *how* inside the contract. The test — can the acceptance criterion be met by a method other than the one you have in mind? If yes, scope is tight (good). If no, you have stated method (an ODD violation).

### 2.2 M5 — Principle-conflict resolution (multi-signal, four-step)

> **No principle always beats another.** When two principles conflict in a specific situation, run the four-step process: (1) name the conflict — both principles, the specific tension; (2) name the active signals — an open list, at minimum scope-confidence, reversibility, blast radius, audience, time pressure, information asymmetry; (3) make the call given the signal weights; (4) surface to the owner if non-obvious — when reasonable people would weigh the signals differently, halt and surface.

The failure mode M5 prevents is **silent resolution**: applying one principle, ignoring the other, never naming the conflict. Silent precedent compounds — an unmarked resolution becomes the next agent's implicit rule, which becomes the agent-after-that's load-bearing assumption, until the corpus has a rule no one ever wrote down.

**M5 is the one foundational principle with a structural carve-out, and the carve-out is deliberately a *non*-enforcement.** Steps 1–3 are interior cognition with no observable artefact unless the agent chooses to write one; only step 4 (surface) produces an artefact, and that artefact is already covered by the surfacing obligation (F2). A mechanical check on "did the agent run the four-step process" would require an LLM judge on every action, which collides with the hook-latency budget. M5 therefore ships as a **named primitive** (its manifest row), an **impartial borderline arbiter** (a SKILL invoking a small model off the per-action hot path for genuinely borderline rule-application calls), and a **recorded-conflict template** (so that *when* a conflict is written down, it carries the four named steps). The behavioural act of running M5 in-head stays advisory. This is the honest partition: enforce what is mechanically checkable; declare-and-arbitrate what is not.

### 2.3 F3 — Swarming (recursive task decomposition)

> **When a task can be partitioned into subtasks each with a measurably tighter acceptance criterion, decompose and execute in parallel or dependency order rather than sequentially in one agent loop.** Apply recursively until further decomposition adds only coordination overhead, or until a judge declares the cycle complete.

The stopping criterion uses scope-confidence (F4) as its primary signal: decompose until each subtask's acceptance criterion is strictly tighter than the parent's; stop when the split adds only coordination overhead; **restart from scratch (not continue) when a judge detects drift** between the subtasks and the parent objective. Completing a diverged chain is the over-tight-at-low-confidence failure mode applied to swarm execution. Every model-selection decision in a swarm records *why* in a rationale line — the audit trail on the choice.

### 2.4 F2 — Ruthless Feedback

> **Name the disagreement, name the evidence, name the alternative.** Surface every quality gap, scope compromise, and design disagreement immediately — including disagreements with the owner's framing. Silent acceptance of a known problem is the failure mode this principle prevents.

Three elements every time: (1) name the disagreement — the specific claim or framing that is wrong, in one sentence; (2) name the evidence — a file path, a commit, a test result, an observed behaviour (bare assertion is restatement, not evidence); (3) name the alternative — what should happen instead (a problem surfaced without a path forward leaves the receiver worse off than silence would).

F2 composes with M5: ruthless feedback *is* the surfacing step (step 4) of the four-step process. F2 composes with scope discipline via the T1 resolution: scope-discipline constrains *action* (do not silently extend scope to fix an out-of-scope problem); F2 constrains *silence* (halt and surface the discovery). The surface is mandatory; the extension is owner-gated.

---

## 3. The principle corpus (the operating tier)

Beyond the four foundational principles, the corpus carries a body of operating principles — each grounded in a named failure mode, each classified in the derivation map by its relationship to F4. The full enumerated set, with the F4 relationship and one-line justification per principle, lives in [`docs/design/principle-derivation-map.md`](../../../docs/design/principle-derivation-map.md); this document does not duplicate that table. The categories:

- **Information-trust ordering** — every claim carries a trust tier; a higher tier obligates verify-or-demote. Specific numbers / counts / SHAs / timestamps are verified before stating or explicitly marked as guesses.
- **Dispatch + scope discipline** — dispatches carry objective + scope + constraints + halt + ODD-check only; never enumerate the method. Working directory always specified; corrective commits never `--amend`.
- **Outcome-orientation** — the prime objective (for loam, VALUE_PROPOSITION) is the AC of every laddering feature; ODD §2.5 forbids non-objective code at the implementation stage.
- **Channel + autonomy** — heavy generative work is dispatched, not ground in-thread; already-authorized work is not paused for discretionary check-ins; the operational-objective test runs before any escalation.

Each principle carries a **derivation line** in its corpus file stating how it relates to the existing corpus (compose-with / independent / partial). Without that line a principle is unindexable, and conflict resolution against it falls back to first-principles every time. This is M5's procedural rule, and it is the maintenance contract for the corpus.

---

## 4. How this document is enforced

This document is the human-readable *principles tier*. Its machine-read companion is the manifest, and the enforcement is structural:

1. **The manifest declares each principle as a named row** with an `enforcement` field (`enforced` / `advisory` / `partial`). A checker enumerates the frame-rules (FR.1 / FR.2 / FR.3) and M5 from the manifest, not from this prose.
2. **A bidirectional coverage guard** keeps the manifest and the derivation map from drifting: a manifest row that names a corpus file the map does not reference — or a structurally invalid manifest — turns the test suite red.
3. **The `enforced` principles ship a mechanical check on the production path** (a research-question gate, a permission-ask Stop contributor, a context-load gate, slug-collision detection, a terminology-drift contributor, the arbiter SKILL). Drift from an enforced principle is a hook DENY/WARN, not a discipline ask.
4. **The `advisory` principles ship as named primitives** — declared, arbitrable, recorded-when-written — but not behaviourally checked, because the honest partition is that they are interior cognition without an observable artefact.

The partition between enforced and advisory is the load-bearing design decision: enforce what is mechanically checkable without an LLM-per-action judge; declare-and-arbitrate what is not. That partition is recorded in the manifest's `enforcement` field, principle by principle.
