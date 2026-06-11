# Release roadmap — dependency map

**Created:** 2026-05-09. **Last refresh:** 2026-05-13. **Effective with:** `docs/release-roadmap.md` §4 priority-ordered candidate queue (post `release-roadmap-priority-queue-restructure` MINOR). **Composes with:** `feedback_soft_halt_vs_hard_halt.md` (memory rule), `feedback_serialize_amendment_builds.md` (worktree-level build serialization), `docs/release-versioning-policy.md` (SemVer commitments + number-derivation recipe).

## Why this artefact exists

The release roadmap (`docs/release-roadmap.md` §4) lists per-candidate dependencies, but the dependency type — HARD (technical prerequisite) vs SOFT (sequencing preference) — isn't named. Read literally, the queue's stated deps could imply a strictly serial build chain with no parallel work possible.

Re-examination shows that read overstates the actual constraint: roughly half the stated dependencies are SOFT — sequencing preferences that can yield to parallel work when fence-discipline holds. This document codifies the HARD-vs-SOFT classification per edge so the parallel-work surface is explicit and so soft-halt declarations have a canonical reference.

**Re-key 2026-05-13 (priority-queue restructure).** Dependency rows are now keyed by **candidate slug** for forward-looking entries (matches `docs/release-roadmap.md` §4 shape). Already-shipped antecedents continue to be keyed by version-number (the published tags are the stable reference). The dep-graph itself is unchanged; only the row labels.

## Dependency-type taxonomy

**HARD** — the dependent version's outcome cannot be produced without the antecedent version's outcome being shipped (sealed locally is sufficient; public-publish is not the gate). Code, data, or capability literally consumed by the dependent.

**SOFT** — the dependent version's outcome could be produced without the antecedent's outcome. The stated dependency reflects sequencing preference (e.g., "we'd rather ship A before B because B's UX assumes A is in users' hands") OR a calibration dependency on production data the antecedent generates. Soft deps yield to parallel work when worktree fences are non-overlapping.

**MIXED** — the version has multiple ACs; some have HARD deps, some have SOFT deps. Sub-AC granularity matters; the version overall is gated by the HARD subset only.

## Per-candidate dependency edges

The current §4 priority queue with type classification. Edges from forward-looking candidate slugs to either other candidate slugs OR already-shipped version-numbers. Slug labels match the §4 queue entry name; version-numbers refer to published tags on `origin`.

| Edge | Stated dep | Type | Evidence / notes |
|---|---|---|---|
| **`principle-foundation-structural-enforcement`** ← v0.7.0 | UX surface stable enough to add structural enforcement on top | **SOFT** | This candidate is META-FRAMEWORK class — structural-enforcement substrate. The substrate work (hook surface widening, principle-foundation files) is orthogonal to END-USER UX. The dep reflects "we'd rather not change the substrate while UX is unstable" — sequencing preference, not technical prereq. |
| **`negative-alignment-detection`** ← `principle-foundation-structural-enforcement` | structural enforcement substrate provides hook surface | **HARD** | Negative-alignment detection consumes the principle-foundation hook surface (the structural checks fire on the same hook events). HARD when principle-foundation has shipped first; if dep order inverts (negative-alignment ships first), the alignment detection ships with a placeholder hook layer + retrofits later — SOFT under that ordering. |
| **`deep-personalization`** ← v0.8.0 + memory FBE.7 production volume | memory FBE.7 stable + production usage long enough for interaction volume | **MIXED** | Deep-personalization features can be CODED without v0.8.0 in production; only the calibration/empirical-tuning work needs production volume. Code-side SOFT; data-side HARD. v0.8.0 honesty cleanup MINOR shipped (the dep is on the established cleanup baseline + per-component-version discipline; the original v0.8.0 negative-alignment shape never landed and is now folded into the `negative-alignment-detection` candidate). |
| **`plugin-suite-expansion`** ← `deep-personalization` | richer user model for plugin composition | **SOFT** | Plugin suite items can ship against the existing principle-foundation substrate; deep-personalization is enrichment, not gate. Each plugin gets its own MINOR with its own objective sentence + ACs. |
| **`v1.0.0-stability-gate`** ← multiple antecedents | All documented features work + 1 real-user shipping event + 6-month backwards-compat commitment + plugin contract stable | **MIXED** | Per `docs/release-versioning-policy.md` §"When 1.0.0 ships." Quality-bar event, not a calendar event. The "1 real user has shipped real software with loam" criterion is an external dependency (user adoption); the others are internal-roadmap gates. |

## Realistic parallel-work surface (post v0.9.0 / current state)

The HARD-only constraint chain in the current §4 queue:

```
v0.7.0 [shipped] → principle-foundation-structural-enforcement (SOFT)
                          ↓
                    negative-alignment-detection (HARD)
                          ↓
                    deep-personalization (MIXED — code-side SOFT;
                                                    data-side HARD)
                          ↓
                    plugin-suite-expansion (SOFT)
                          ↓
                    v1.0.0-stability-gate (MIXED — external dep)
```

The SOFT-classified work that can run in parallel:

| Stream | Fence | Parallelizable with | Stage |
|---|---|---|---|
| `principle-foundation-structural-enforcement` | hook surface widening (`framework/orchestrator/`, `framework/safety-layer/`) + principle-foundation docs | other queue candidates (no fence overlap) | build |
| `negative-alignment-detection` (CODE only; calibration deferred) | new detection primitive + `framework/odd-extractor/` extension | other queue candidates (no fence overlap) | build |
| `plugin-suite-expansion` (per-plugin MINOR) | each plugin gets its own `plugins/<name>/` | other candidates (small fence per plugin) | build |
| BallotPath workspace work | entirely separate workspace `/Users/lukeivers/ballotpath/` | everything in canonical | build |
| Rebrand-residue sweep | cross-cutting in canonical | nothing else in canonical (race) | build |

## Worktree-level constraints (build-time only)

`feedback_serialize_amendment_builds` rules: BUILD agents in the same worktree race on `git index.lock` / `loam amend` / tests. Therefore:

- **Plan-author + research agents** — parallel-safe across any number, even in the same worktree.
- **Build agents** — serialize per worktree. Different worktrees (e.g., canonical vs BallotPath) parallelize freely.

For canonical, this means at most ONE build agent runs at a time. The 3 streams above (v0.5.0 / v0.7.0 / v0.6.0 sub-features) can have plans authored in parallel but builds serialized.

For different worktrees (canonical + BallotPath), TWO build agents run simultaneously without race.

## Soft-halt application

Each candidate's stated SOFT dependencies enable soft-halt declarations like:

> Soft-halted on v0.9.0 publish (HARD HALT class — public action). Continuing on `release-roadmap-priority-queue-restructure` build (fence-clear, parallel-safe per this map). Exit: owner ratifies v0.9.0 publish.

> Soft-halted on an owner-gated candidate build (waiting on the gating decision). Continuing on `principle-foundation-structural-enforcement` plan-doc authoring (SOFT dep per this map; orthogonal fence). Exit: the gating decision lands.

The 4-element soft-halt template (item / dep graph / non-blocked work / exit condition) maps directly onto rows from this table.

## Maintenance

This artefact is a SHIPPED-state document, not a forward-looking plan. It updates when:

1. New candidate added to `release-roadmap.md` §4 priority queue — add row + classify deps using candidate-slug labels.
2. A SOFT dep proves operationally HARD (e.g., parallel-build attempt hits unforeseen coupling) — reclassify with note + commit.
3. A HARD dep gets refactored away (e.g., new abstraction breaks the consumption point) — reclassify with note + commit.
4. A candidate ships — its row stays as-is (the candidate-slug label is stable across the queue → ship transition); the row's antecedent column becomes the new published-version reference.

No version-line ownership; this lives at the roadmap-level alongside `release-roadmap.md` itself.

## Authority chain

- `docs/release-roadmap.md` §4 — version objectives + stated deps.
- `feedback_soft_halt_vs_hard_halt.md` — memory rule defining the halt classes.
- `feedback_serialize_amendment_builds.md` — worktree-level build serialization rule.
- `feedback_build_forward_on_publish_pending.md` — instance pattern (publish gates are SOFT halt class).
- Soft-halt analysis at `<workspace>/.scratch/claude-output/soft-halt-version-deps-orchestration-analysis-2026-05-09.md` — origin of the HARD-vs-SOFT re-examination.
