# Release roadmap — dependency map

**Created:** 2026-05-09. **Last refresh:** 2026-05-09. **Effective with:** `docs/release-roadmap.md` v0.5.0+ entries. **Composes with:** `feedback_soft_halt_vs_hard_halt.md` (memory rule), `feedback_serialize_amendment_builds.md` (worktree-level build serialization), `docs/release-versioning-policy.md` (SemVer commitments).

## Why this artefact exists

The release roadmap (`docs/release-roadmap.md` §4) lists per-version dependencies, but the dependency type — HARD (technical prerequisite) vs SOFT (sequencing preference) — isn't named. Read literally, the roadmap implies a strictly serial build chain v0.5 → v0.6 → ... → v1.0 with no parallel work possible.

Re-examination shows that read overstates the actual constraint: roughly half the stated dependencies are SOFT — sequencing preferences that can yield to parallel work when fence-discipline holds. This document codifies the HARD-vs-SOFT classification per edge so the parallel-work surface is explicit and so soft-halt declarations have a canonical reference.

## Dependency-type taxonomy

**HARD** — the dependent version's outcome cannot be produced without the antecedent version's outcome being shipped (sealed locally is sufficient; public-publish is not the gate). Code, data, or capability literally consumed by the dependent.

**SOFT** — the dependent version's outcome could be produced without the antecedent's outcome. The stated dependency reflects sequencing preference (e.g., "we'd rather ship A before B because B's UX assumes A is in users' hands") OR a calibration dependency on production data the antecedent generates. Soft deps yield to parallel work when worktree fences are non-overlapping.

**MIXED** — the version has multiple ACs; some have HARD deps, some have SOFT deps. Sub-AC granularity matters; the version overall is gated by the HARD subset only.

## Per-version dependency edges

The current chain from `release-roadmap.md` §4 with type classification:

| Edge | Stated dep | Type | Evidence / notes |
|---|---|---|---|
| **v0.5.0** ← v0.4.0 | code-gen wired; ProgramBench docs-only baseline | **HARD** | Binary-usage observation harness produces evidence rows that feed the code-gen pipeline shipped in v0.4.0. AC.V050.2 (binary-feeder mode for odd-extractor) literally extends the v0.4.0 evidence-row contract. |
| **v0.6.0** ← v0.5.0 | working-software output is precondition for non-tech user reaching working-software output | **MIXED** | AC.V060.5 (real session-transcript demo) HARD-depends on v0.5.0 (the demo IS a v0.5.0-shaped end-to-end trace). AC.V060.1 (light-touch education), AC.V060.2 (channel config slot), AC.V060.3 (corpus override pattern), AC.V060.4 (memory-doc skeleton template) are SOFT — could be authored in parallel with v0.5.0. AC.V060.6 (outcome-altitude AC) HARD-depends on v0.5.0. |
| **v0.7.0** ← v0.6.0 | UX surface stable enough to add structural enforcement on top | **SOFT** | v0.7.0 is META-FRAMEWORK class — structural-enforcement substrate. The substrate work (hook surface widening, principle-foundation files) is orthogonal to END-USER UX. The dep reflects "we'd rather not change the substrate while UX is unstable" — sequencing preference, not technical prereq. |
| **v0.8.0** ← v0.7.0 | structural enforcement substrate provides hook surface | **HARD** | v0.8.0 contract-validation literally consumes v0.7.0's hook surface (the structural checks fire on the same hook events). |
| **v0.9.0** ← v0.8.0 | memory FBE.7 stable + production usage long enough for interaction volume | **MIXED** | v0.9.0 deep-personalization features can be CODED without v0.8.0 in production; only the calibration/empirical-tuning work needs production volume. Code-side SOFT; data-side HARD. |
| **v0.10.0+** ← v0.9.0 | richer user model for plugin composition | **SOFT** | Plugin suite items can ship against v0.7-substrate; v0.9 personalization is enrichment, not gate. |

## Realistic parallel-work surface (post-v0.4.3)

Once v0.4.3 (memory retrieval BM25 fix) ships locally, the HARD-only constraint chain is:

```
v0.4.3 [in flight] → v0.5.0 (HARD)
                                  ↓
                  v0.6.0 outcome-altitude ACs (HARD on V050)
```

The SOFT-classified work that can run in parallel:

| Stream | Fence | Parallelizable with | Stage |
|---|---|---|---|
| v0.5.0 main (binary harness) | new component `framework/binary-observation-harness/` + adapter in `framework/scope-of-work/` | v0.7.0 substrate (no fence overlap) | build |
| v0.7.0 META-FRAMEWORK substrate | hook surface widening (`framework/orchestrator/`, `framework/safety-layer/`) + principle-foundation docs | v0.5.0 main, v0.6.0 sub-features | build |
| v0.6.0 sub-features (V060.1, V060.2, V060.3, V060.4) | various per AC | v0.5.0 main | build |
| BallotPath Stage 6 (counties) | entirely separate workspace `/Users/lukeivers/ballotpath/` | everything in canonical | build |
| Subagent-personas amendment | `.claude/agents/<name>.md` in canonical | most things; small fence | build |
| Rebrand-residue sweep | cross-cutting in canonical | nothing else in canonical (race) | build |

## Worktree-level constraints (build-time only)

`feedback_serialize_amendment_builds` rules: BUILD agents in the same worktree race on `git index.lock` / `pos-amend` / tests. Therefore:

- **Plan-author + research agents** — parallel-safe across any number, even in the same worktree.
- **Build agents** — serialize per worktree. Different worktrees (e.g., canonical vs BallotPath) parallelize freely.

For canonical, this means at most ONE build agent runs at a time. The 3 streams above (v0.5.0 / v0.7.0 / v0.6.0 sub-features) can have plans authored in parallel but builds serialized.

For different worktrees (canonical + BallotPath), TWO build agents run simultaneously without race.

## Soft-halt application

Each version's stated SOFT dependencies enable soft-halt declarations like:

> Soft-halted on v0.4.3 publish (HARD HALT class — public action). Continuing on v0.5.0 plan-doc authoring (fence-clear, parallel-safe per this map). Exit: owner ratifies v0.4.3 publish.

> Soft-halted on v0.6.0 sub-feature build (waiting for v0.5.0 main to complete, MIXED dep). Continuing on v0.7.0 META-FRAMEWORK substrate plan (SOFT dep on v0.6.0 per this map; substrate fence orthogonal to v0.5.0 binary-harness fence). Exit: v0.5.0 main lands.

The 4-element soft-halt template (item / dep graph / non-blocked work / exit condition) maps directly onto rows from this table.

## Maintenance

This artefact is a SHIPPED-state document, not a forward-looking plan. It updates when:

1. New version added to `release-roadmap.md` §4 — add row + classify deps.
2. A SOFT dep proves operationally HARD (e.g., parallel-build attempt hits unforeseen coupling) — reclassify with note + commit.
3. A HARD dep gets refactored away (e.g., new abstraction breaks the consumption point) — reclassify with note + commit.

No version-line ownership; this lives at the roadmap-level alongside `release-roadmap.md` itself.

## Authority chain

- `docs/release-roadmap.md` §4 — version objectives + stated deps.
- `feedback_soft_halt_vs_hard_halt.md` — memory rule defining the halt classes.
- `feedback_serialize_amendment_builds.md` — worktree-level build serialization rule.
- `feedback_build_forward_on_publish_pending.md` — instance pattern (publish gates are SOFT halt class).
- Soft-halt analysis at `<workspace>/.scratch/claude-output/soft-halt-version-deps-orchestration-analysis-2026-05-09.md` — origin of the HARD-vs-SOFT re-examination.
