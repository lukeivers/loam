# ODD — LLM context prime (lean)

**Load before ODD-shaped tasks.** Verbose derivation: `docs/odd-llm-grounding-derivation.md`. **Glossary** of the recurring ODD-cluster vocabulary (objective, capability, contract, banded AC, ratification): `docs/glossary.md`.

## Failure mode this prevents

Mistaking implementation facts for objectives. v0.1.8 odd-extractor shipped this: 131 outputs labeled "AC" were symbol-level structural facts ("Express route GET /all-orders at file:line"), not objectives. ODD requires outcome-altitude.

## Four altitudes

| Layer | Definition | Test |
|---|---|---|
| Objective | Outcome system delivers; observable from outside; survives implementation rewrite | Rewrite in different language + libs — does statement still describe the system? Yes → objective |
| Constraint | Bound on solution space; not itself an outcome | Restricts HOW outcomes are delivered without being one? Yes → constraint |
| Capability | Feature/function serving objectives; one of many possible HOWs | Could different system deliver the same objectives without this exact thing? Yes → capability |
| Implementation | Specific symbol/file/line/library | Names a specific symbol/file/line/library? Yes → implementation |

## What's specifically new in ODD (vs BDD/TDD/ATDD/DbC/user-stories/DDD/RE)

- **§2.5 strict mapping** — every line of code/branch/test maps to named AC; no orphan code. Stricter than any adjacent methodology.
- **Banding** — V/P/H confidence-graded, not binary. Novel.
- **Method-loose** — objective + constraints + ACs pin WHAT; HOW is builder's call. Tight scope, loose method.
- **ODD-RE** — reverse-engineer from existing code as first-class workflow.
- **LLM-as-builder** — natural-language-statable, observable, banding-honest-on-uncertainty.
- **Three-altitude layering** — Objective → Capability → Implementation; maps between.

## 7 drift modes (recognize → correct)

1. **Symbol-as-AC.** "Route X exists at file:line" labeled AC. Wrong altitude: implementation. Correct: state outcome route serves.
2. **Function-name-as-AC.** "Function foo() exists" labeled AC. Wrong: implementation. Correct: outcome function serves.
3. **Feature-as-objective.** "App has CSV upload" labeled objective. Wrong: capability. Correct: outcome CSV upload serves.
4. **Test-name-as-implementation.** Test asserts call / DOM / specific invocation. Wrong: implementation-shaped test. Correct: tests asserting OUTCOMES are AC-shaped; tests asserting calls are implementation.
5. **Gap-as-objective.** "Missing test coverage" labeled objective. Wrong: gap is finding. Correct: gap analysis is separate layer AFTER objective extraction.
6. **Constraint-as-objective.** "System must be SOC-2-compliant" labeled objective. Wrong: SOC-2 is constraint. Correct: objective is user-facing OUTCOME ("audit trail identifies who did what"); SOC-2 is bound.
7. **Implementation-detail-as-constraint.** "Uses RSA-OAEP" labeled constraint. Wrong: implementation. Correct: lift to constraint ("tokens confidential under transport").

## 5 self-checks before producing ODD output

1. Outcome-or-fact? Outcome → objective candidate; fact → not objective.
2. Implementation-swap. Survives rewrite? → objective.
3. Builder-method. Could different builder produce different shape meeting it? Yes → loose enough.
4. Observable-from-outside. Verifiable without reading code? → objective.
5. User-purpose. Names purpose / value-to-someone? → objective candidate.

Any check fails → wrong altitude → restate.

## Brownfield ODD-RE inputs (signal, reliability-ranked)

1. README + design docs — plain-English purpose statements.
2. User-supplied context — maintainer's own framing.
3. Test names + assertions — when names assert outcomes, closest-to-objective in code.
4. Code-pattern + LLM inference — route shapes / middleware / page-objects → domain inference.
5. Commit messages — chronological intent evolution.
6. Comments + docstrings — sometimes intent.

Single source insufficient. Banding reflects multi-source confidence gradient.

## Worked example (rd-automation)

- **v0.1.8 produced (wrong altitude):** `AC.JSTS.express.get.all_orders.src_routes_exportroutes_js` — labeled AC, but is implementation.
- **ODD-shaped (right altitude):**
  - Objective O1: "Operators file refund disputes against DoorDash + Uber Eats merchant portals at scale, replacing manual portal clickwork."
  - Capability C1 (→ O1): "CSV upload + validation pipeline."
  - Implementation: "Express route GET /all-orders at src/routes/exportRoutes.js:66" — backing-implementation evidence row for C1, NOT primary output.

## Outcome-altitude AC requirement

Every AC set MUST include ≥1 AC explicitly marked at outcome-altitude. Without one, the set can pass §2.5 mapping while collectively missing the user-facing outcome (three failures observed: v0.2.1 F1, v0.2.1 F2, v0.2.5 F1).

An outcome-altitude AC is verified by a test that:

- Invokes the production code path (CLI / API / dispatch surface) the user actually uses.
- Does NOT pre-arrange state that the production code would normally produce (pre-arrangement bypasses upstream — STUB-class, can satisfy implementation-altitude ACs only).
- Produces a real outcome artefact (file written, response returned, side-effect observed).

AC schema marks each AC `outcome-altitude: true|false` so plan-authors and reviewers spot-check at a glance. Risk-band classifier + pre-arrangement detection rubric live in the `odd-test-altitude-discipline` SKILL.

## Use sequence

1. Read this prime.
2. Hold altitudes + drift-modes + self-checks in working memory.
3. For any declared AC / objective / constraint / capability, run self-checks.
4. Any check fails → restate.
5. For depth, load `docs/odd-llm-grounding-derivation.md`.
