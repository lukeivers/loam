# Five-gate chain — research → spec → plan → build → seal

> **Non-trivial pos-v2 work flows through five gates: research, spec, plan, build, seal. Each gate produces a durable artefact + advances the work to the next stage. The chain is what the Dev/SDLC plugin OPERATIONALISES at v0.1.0 — `loam project new` scaffolds the stage tree, `loam project advance` enforces the gate's structural check, `loam project status` shows the current stage. The methodology mirrors the chain: the user advances through the gates with structural enforcement (objective + AC presence required before stage advance).**

This document is the concise codification of the five-gate chain convention. The exhaustive narrative — including per-stage rationale + methodology variants (ODD vs TDD vs BDD vs adhoc) — lives in `../odd-in-loam.md` + `../odd-methodology.md`. The plugin's stage-engine implementation lives at `../../src/loam/plugins/dev_sdlc/stages.py`.

## 1. The five gates

| Gate | Output artefact | Structural check |
|------|-----------------|------------------|
| Research | `<project>/research/<slug>.md` (research findings, primary-source catalogue, surveyed-component map) | objective declared; method NOT prescribed |
| Spec | `<project>/spec/<slug>.md` (objective + acceptance criteria + constraints + scope boundaries) | objective + ACs declared; method NOT prescribed |
| Plan | `<project>/plan/<slug>.md` (method + ordered work + per-AC verification) | method declared; ACs cited; halt triggers named |
| Build | feature commits + corrective commits + apply commit | source code per the plan; tests pass; ODD §2.5 compliance |
| Seal | seal commit + SEAL_COMMIT sidecars + per-amendment seal narrative | seal-test passes; baseline advanced; §14 register populated |

Each gate's output is the input to the next. The structural check at each gate is the property the user must satisfy to advance.

## 2. Gate enforcement

The plugin's `loam project advance` invocation checks the current stage's structural property + advances if the property holds, else raises `StageGateFailedError` with a structured `reason` field. The persona's exception-handling translates the reason to natural-language guidance for the user.

ODD (default): structural check inspects the artefact for `objective:` + `acceptance_criteria:` Markdown frontmatter. TDD: structural check looks for test files in the stage's test directory. BDD: structural check inspects for scenario blocks. Adhoc: structural check is "artefact exists + non-empty + a methodology-specific minimal sentinel."

## 3. Optional research-skip path

The research gate is required for non-trivial new work + skipped for trivial work (rename, single-line edit, modification of existing solution). Per the `research-before-plan` CDC, the dispatcher's judgement determines whether research is required; when uncertain, run research.

## 4. Cross-references

- Long-form gate methodology: `../odd-methodology.md` §1.
- Plugin's stage-engine implementation: `../../src/loam/plugins/dev_sdlc/stages.py`.
- Plugin's templates per stage: `../../src/loam/plugins/dev_sdlc/templates/` (odd-research.md, odd-spec.md, odd-plan.md, odd-build.md, odd-review.md).
- CDC: `../cdcs/research-before-plan.md` + `../cdcs/plan-before-code.md`.

## 5. Applied-immediately footer

The five-gate chain is the structural shape pos-v2 dev work follows from project-start forward. Pre-M6b.0 the convention lived in `docs/odd-methodology.md` + `docs/odd-in-loam.md`; M6b.0 codifies the chain as a named convention + the plugin operationalises it as the v0.1.0 workflow shape.
