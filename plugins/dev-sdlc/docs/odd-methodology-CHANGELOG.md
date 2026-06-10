# odd-methodology.md — CHANGELOG

Changelog-class record for the operational ODD specification at
`plugins/dev-sdlc/docs/odd-methodology.md`. Version-pinned rule additions
that are reference material rather than doctrine live here (relocated per
KEEL adoption program Phase 1, AC.KDOC.5).

## 2026-06-10 — KEEL Phase-1 rewrite

The spec was rewritten 1,264 → ≤360 lines per the ratified
methodology-synthesis verdict: spine-as-system leading; banding restated as
evidence grades (VERIFIED = ran green at a known SHA; assumed-green =
ASSERTED) under mechanical/judged/attested check-kinds; altitude tests +
drift modes promoted in from the derivation doc (now archived); per-criterion
altitude declaration canonized; novelty claim retracted; ancestry named;
adapter conventions relocated to
`plugins/dev-sdlc/odd-extractor/docs/adapter-conventions.md`; the v0.2.3 §14
multi-source banding rule relocated below. Full pre-rewrite text:
`docs/archive/odd-methodology-2026-06-10-pre-keel.md`.

## 2026-05 (v0.2.3 Cycle 1) — multi-source banding rule, relocated verbatim

> Pre-rewrite §14, preserved verbatim. Read its band names through the
> doctrine §6 mapping: the extractor-side `VERIFIED` band = ASSERTED
> evidence grade until the enum rename lands.

## 14 — v0.2.3 Cycle 1: multi-source banding rule (objective altitude)

Per v0.2.3 master plan §3 Cycle 1 + sub-plan-doc §3 AC.OBJX.5 — the
v0.2.3 multi-source synthesis pipeline introduces banded
`Objective` / `Constraint` / `Capability` rows alongside the
existing symbol-altitude `BandedAC` evidence rows. The banding rule
for objectives (and the analogous evidence-shape rules for
constraints/capabilities) is multi-source verified, NOT
single-citation:

### 14.1 — V/P/H banding criteria for objectives

| Band | Criteria (programmatic Pydantic invariants) |
|------|---------------------------------------------|
| **VERIFIED** | `evidence.test_name_refs` non-empty AND (`evidence.readme_excerpts` OR `evidence.design_doc_refs`) non-empty AND `evidence.repo_sha` non-null. The two-source rule: an outcome-asserting test plus a maintainer purpose statement (README or design doc). |
| **PLAUSIBLE** | At least one of `evidence.readme_excerpts` / `evidence.design_doc_refs` / `evidence.survey_line_refs` non-empty. Single-source minimum. **Survey-only evidence caps at PLAUSIBLE** — never promote a survey-only claim to VERIFIED (sub-plan-doc §7 + master plan §7.7). |
| **HYPOTHESISED** | `evidence.rationale` non-empty (LLM-derived inference chain explanation). Pattern-only inference; no maintainer purpose statement and no test. |

Pydantic `model_validator` enforces these structurally — Objective
construction with mismatched band/evidence raises
`pydantic.ValidationError` (no instance can hold a malformed pair).

### 14.2 — Evidence shape (multi-source citation block)

`ObjectiveEvidence` carries six lists in priority order (lean
grounding doc §brownfield ODD-RE inputs):

1. `readme_excerpts: list[str]` — plain-English maintainer purpose.
2. `design_doc_refs: list[str]` — `path#heading` design-doc
   pointers.
3. `test_name_refs: list[str]` — outcome-asserting test names.
4. `survey_line_refs: list[str]` — operator-supplied context.
5. `code_pattern_refs: list[str]` — adapter-derived `file:line`
   pointers (HYPOTHESISED-band fuel).

Plus `repo_sha: str | None` (pin for VERIFIED) and
`rationale: str | None` (required for HYPOTHESISED).

`ConstraintEvidence` is the same shape minus `test_name_refs`
(tests assert outcomes, not bounds — drift-mode #4).

`CapabilityEvidence` is the same shape as ObjectiveEvidence
(capabilities can be test-asserted as features-serving-outcomes).

### 14.3 — §self-checks 1-5 enforcement

The altitude validator (`altitude_validator.validate_altitude`)
runs §self-checks 1-5 from `docs/odd-llm-grounding.lean.md` on
every emitted row. Programmatic heuristics first; LLM-as-judge
extension point for borderline rows (Cycle 1 ships programmatic-
only — Lens 4 cost-bounded). Decision tree on failure:

- §1 fail (fact-as-objective) → drop.
- §2 fail (implementation-swap) → restate-as-capability or drop.
- §3 fail (method-prescription) → downgrade band.
- §4 fail (non-observable) → downgrade band.
- §5 fail (no purpose) → drop unless VERIFIED evidence supports
  HYPOTHESISED retention.

Drift detection: >30% fail rate across all rows triggers
`drift_halt_triggered` on the `ValidationReport` (the
`needs_fresh_start` shape from Lens 5). Build agents surface the
halt; do NOT silently restart.

### 14.4 — Adapter-output reshape

Adapter `extract()` signatures unchanged. Adapter outputs (Ruby +
JS/TS `BandedAC` rows at symbol altitude) flow into
`<workspace>/.loam/extractions/<repo-id>/evidence-rows.yaml`
(renamed from `raw-acs.yaml` per master plan §6.3; the legacy name
is preserved as a transitional alias so v0.1.9 PR-safety + v0.1.8
test substrates keep reading the same content). Cycle 3 retires the
legacy alias.

The `contract-draft.yaml acs:` field is preserved for v0.1.9 PR-
safety transitional compat — populated with typed `Objective` rows
(NOT symbol-altitude evidence rows). Full schema retirement is
Cycle 3 per master plan §6.2.
