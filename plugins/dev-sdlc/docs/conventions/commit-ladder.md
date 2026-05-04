# Commit-ladder + seal-ritual conventions

> **An amendment's commit history follows a stable ladder: plan + manifest commit → feature commit(s) → corrective commits (if any) → `loam amend apply` commit → seal commit. Each rung carries a stable commit-message prefix; the seal commit is sealed via `loam amend seal` which writes the SEAL_COMMIT sidecars + narrative + applies a deterministic finalisation.**

This document is the concise codification of the commit-ladder + seal-ritual conventions. The exhaustive narrative of why this shape exists lives in `../odd-in-loam.md`; the implementation lives in `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/` (the seal-diff + apply + seal commands).

## 1. The commit ladder

Standard amendment commit ladder, in order:

1. **Plan + manifest commit** — `docs(plans): <slug> sub-plan + manifest`. Lands the plan-doc + manifest YAML before any source change. Per `feedback_plan_before_code`.
2. **Feature commit(s)** — `feat(<component>): <slug>` (or scoped narrower per-commit). The actual scope work; can span multiple commits if the surfaces stay coherent (e.g. M6a's plugin source as one commit, the M2 partition manifest extension as another).
3. **Corrective commits** — `fix(<component>): <correction>`. Used if a feature commit's seal-diff fence misses a path or a test reveals an empirical issue. NEVER `git commit --amend` (per `feedback_no_amend_in_agent_dispatches`); always create new corrective commits.
4. **Apply commit** — `chore(<comp>-apply): loam amend apply for amendment #N (<slug>)`. The `loam amend apply` step writes the propagated allowed_prefixes into each touched seal-test + bumps any per-component bookkeeping. Auto-generated; deterministic.
5. **Seal commit** — `chore(seals): <description> — <comp1>[+<comp2>...] at <sha-short>` (deterministic subject; `<description>` defaults to the manifest's `slug`, optionally overridden by `seal_description`). The `loam amend seal` step advances every touched component's `tests/SEAL_COMMIT` sidecar to the seal commit's SHA, writes the per-amendment seal narrative file, runs the seal-tests, and creates the deterministic seal commit. At schema v3 with `plan_doc_ref` set, the commit message body additionally surfaces a `Plan doc: <ref>` line so `git log` readers see the pointer to the full reasoning without opening the `SEAL_COMMIT.<slug>` file (per cost-audit 2026-05-04 Recommendation B).

Followed by a §14 SHA-register backfill commit (`docs(plans): record amendment #N commit SHAs in method-decision register`) once all SHAs are known.

## 2. Commit-message prefixes

Standard prefixes by ladder rung:

| Rung | Prefix |
|------|--------|
| Plan + manifest | `docs(plans):` |
| Feature | `feat(<component>):` |
| Corrective | `fix(<component>):` |
| Apply | `chore(<component>-apply):` or `chore(loam-apply):` |
| Seal | `chore(seals):` |
| §14 backfill | `docs(plans):` |
| Snapshot / safety | `snapshot:` or `safety:` |

The prefix names the commit's ladder position + which component subtree it touches; the body carries the per-commit narrative.

## 3. Seal-ritual specifics

`loam amend seal` runs:

- Touched-component test scope (per the `feedback_amendment_dispatch_speedups` rule — only components in the manifest's `components:` list run their tests).
- Seal-diff verification against the new BASELINE..HEAD window.
- SEAL_COMMIT sidecar advancement (each component's `tests/SEAL_COMMIT` is rewritten to the new seal commit's SHA).
- Per-amendment seal narrative file written at the manifest's `narrative.target` path. Body source by schema:
  - **Schema v1 / v2 (legacy):** body comes from `narrative.body` verbatim. Historical seal narratives in canonical history average ~160 lines and replicate plan-doc content; readers of `git log` and `framework/<comp>/seals/` see this shape on pre-2026-05-04 amendments.
  - **Schema v3 (collapsed; default going forward):** body is synthesized as a 5-15 line summary covering title + slug + components + baseline + amendment SHA + `plan_doc_ref` pointer + optional `ac_count` + `smoke_outcome`. The full plan-doc content is NOT inlined; readers follow the `plan_doc_ref` pointer for detail. Per cost-audit 2026-05-04 Recommendations A + B; saves ~150 LOC of duplicated narrative authoring per amendment.
- Plan-doc §14 partial backfill (for the SHAs known at seal time).

The seal commit is deterministic given the manifest + the touched component list — re-running `loam amend seal` produces the same commit.

## 4. Cross-references

- Implementation: `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/seal.py` + `commands/apply.py`.
- README: `framework/tools/loam/README.md`.
- Per-component seal narrative target: `<component>/seals/SEAL_COMMIT.<slug>`.
- CDC: `../cdcs/amendment-dispatch-test-scope.md` (touched-component-only test scoping rule).
- Plan-doc convention: `plan-docs.md` (§14 register placeholder shape).

## 5. Applied-immediately footer

This commit-ladder shape is followed by every sealed amendment from project-start forward. Pre-M6b.0 the convention lived in precedent + dispatch templates; M6b.0 names + locates the codification.
