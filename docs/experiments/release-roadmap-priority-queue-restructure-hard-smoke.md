# HARD smoke — release-roadmap priority-queue restructure

**Build slug:** `release-roadmap-priority-queue-restructure`.
**Build class:** MINOR (META-FRAMEWORK).
**Version derived at build:** `v0.10.0` (per `next_MINOR(v0.9.0) = v0.10.0`).
**Date:** 2026-05-13.
**State:** SEALED LOCAL — awaiting dispatcher dogfood publish per ASK-FIRST.

---

## Stage 1 — Repository invariants

Verified at sealed state:

- `docs/release-roadmap.md` §4 is restructured: top-level header reads "Priority-ordered candidate queue (next-release pipeline)"; 6 candidate sections present (`binary-usage-observation-harness`, `principle-foundation-structural-enforcement`, `negative-alignment-detection`, `deep-personalization`, `plugin-suite-expansion`, `v1.0.0-stability-gate`); each candidate carries the 8 named fields (slug, objective, class, AC family, constraints, source items, AI-time, dependencies).
- `docs/release-roadmap.md` §4-prelude reclassification-audit table is present with two sections (historical-shipped read-only + forward-looking rescope-applied). 13 historical rows; 6 forward-looking rows.
- `docs/release-versioning-policy.md` has new "Number derivation at build-commence time" section between "When 1.0.0 ships" and "Pre-release tags" — recipe block + 5 narrative paragraphs (where the recipe applies; what `current_version` means; hot-patch case; edge case for in-flight PATCH; implementation choice).
- `docs/release-roadmap-dependency-map.md` per-candidate dependency table is keyed by candidate-slug for forward edges + version-numbers for shipped antecedents.
- AC IDs use scope-descriptive family abbreviations: `AC.BUOH.*` (binary-usage), `AC.PFSE.*` (principle-foundation), `AC.NAD.*` (negative-alignment), `AC.DP.*` (deep-personalization). `AC.V100.*` retained for the v1.0.0 stability gate (structurally pinned by policy).
- Plan-doc + manifest + source-edit + apply + seal commits all land under the named fence.

## Stage 2 — Outcome-altitude probe (AC.RR.4)

Real production entry-point invoked from `/Users/lukeivers/loam/` at sealed state. The probe verifies that the post-restructure artefacts pass `loam release` gates against the live restructured state — exercising the v0.8.2 `--plan-doc` flag + v0.8.3 REMOVED-verdict-parser (this PATCH chain shipped specifically to make scope-descriptive plan-docs publish-able).

**Command:**

```
loam release v0.10.0 \
    --plan-doc docs/plans/release-roadmap-priority-queue-restructure.md \
    --dry-run
```

**Pre-source-edit baseline (run from current state at b269d8e plan-doc):** N/A — the plan-doc was always uncommitted-source-edit until this build; nothing to baseline against.

**Post-seal verbatim output (executed 2026-05-13 at HEAD post-§status-backfill + §13 rename):**

```
== Pre-publish gates ==
  [GREEN] hard-smoke: HARD smoke GREEN at docs/experiments/release-roadmap-priority-queue-restructure-hard-smoke.md
  [GREEN] acs-verified: all 5 AC(s) verified (GREEN or REMOVED) in docs/plans/release-roadmap-priority-queue-restructure.md §status
  [GREEN] state-shipped: v0.10.0 marked SHIPPED in docs/STATE.md
  [GREEN] clean-tree: working tree clean
  [GREEN] branch-main: on branch main
  [GREEN] seal-reachable: seal c71b2fa reachable from HEAD

DRY-RUN: would create annotated tag v0.10.0 at c71b2fa with message: 'v0.10.0 — release-roadmap priority-queue restructure MINOR — ...'
DRY-RUN: would push origin main + tag v0.10.0
DRY-RUN: would apply post-publish backfill — 4 edit(s)
```

ALL 6 GATES GREEN closes AC.RR.4 outcome-altitude. The dogfood probe IS the verification of the v0.6.0 release-CLI substrate against the new scope-descriptive plan-doc convention — composes with the v0.7.2 + v0.8.2 + v0.8.3 PATCH chain that prepared the gates for exactly this shape. The v0.10.0 release-roadmap-priority-queue-restructure is the first end-to-end exercise of that chain.

**One in-cycle parser conformance fixup surfaced + closed:** the plan-doc originally placed §status at §12 (per the v0.2.x-era convention); the v0.6.0 release-CLI `check_acs_verified` parser at `gates.py:357-361` recognises only `§13` or `§status` (no number) per a long-standing regex. Renamed §12 → §13 (and the existing §13 "Build-time decision deviations" → §14) for parser conformance. Plan-doc commit `6f2231f`. Captured as a candidate FIDRAFT entry for follow-on parser-flexibility PATCH if more plan-docs adopt the §12-§status convention — for now, one-off rename was cheaper than widening the parser.

## Stage 3 — Ride-along orthogonality (rd-automation pathway)

This restructure is doc-only — no framework code touched (the optional Python helper per D-RR.5.4 was declined in favor of the documented manual rule). The rd-automation synthesis pathway / memory retrieval / subagent-personas routing / amendment-dispatch tooling are all untouched.

**Verdict:** PASS by inspection — no source file under `framework/` modified; no plugin pyproject version bumped; no test added or removed. The doc-only fence preserves the rd-automation surface verbatim.

## Stage 4 — AC verdict matrix mapping (backfilled at §status time)

The plan-doc's §12 §status table backfills post-build per the v0.8.3 precedent. Each AC.RR.* gets a verdict cell + evidence citing source-edit commit SHA + this smoke writeup.

| AC | Expected verdict | Evidence anchor |
|---|---|---|
| AC.RR.1 — §4 restructured to priority-ordered queue of unnumbered candidates | GREEN | §4 restructured shape verified at Stage 1 above; source-edit commit (TBD-AT-COMMIT); 6 candidates with 8 fields each + no pre-assigned version-numbers + header note present. |
| AC.RR.2 — Reclassification audit deliverable | GREEN (rescoped) | Audit table at §4-prelude; historical section (13 rows, read-only) + forward-looking section (6 rows, rescope-applied per build-time directive). Surfaces 2 historical mis-classifications (v0.4.1 borderline, v0.4.4 caught + renamed before publish); no retroactive rename per HARD HALT. Source-edit commit (TBD-AT-COMMIT). |
| AC.RR.3 — Number-derivation rule documented | GREEN | New section in `docs/release-versioning-policy.md` between "When 1.0.0 ships" and "Pre-release tags". Recipe block present + 5 narrative paragraphs. Source-edit commit (TBD-AT-COMMIT). |
| AC.RR.4 — Outcome-altitude probe (dogfood) | GREEN (probed post-seal) | `loam release v0.10.0 --plan-doc docs/plans/release-roadmap-priority-queue-restructure.md --dry-run` returns ALL 6 GATES GREEN against the live restructured artefacts. Probe writeup at this file (Stage 2 above). |
| AC.RR.S — Seal-diff discipline | GREEN | `git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under named fence: `docs/release-roadmap.md` + `docs/release-versioning-policy.md` + `docs/release-roadmap-dependency-map.md` + universal-admission docs (STATE.md row + this smoke writeup + plan-doc §status backfill) + auto-managed seal sidecar. No source-code changes outside the fence. |

## Stage 5 — Findings + halt-and-surface

**No build-time halt-and-surface findings.** The rescope directive in the dispatch brief was honored: historical-section is read-only (no retroactive renames proposed for already-shipped versions); forward-looking-section walks remaining §4 entries.

**Two historical mis-classifications surfaced + recorded (audit-as-lessons-learned, not retroactive renames):**

1. **v0.4.1 — borderline-MINOR shipped as PATCH.** The from-scratch prompt mode is arguably a new outcome shape. Published with `v0.4.1` tag; no rename per HARD HALT (would break OSS consumers). Lesson-learned applied going forward: borderline cases default to MINOR.
2. **v0.4.4 — MINOR shipped as PATCH (misnamed in queue).** Caught + renamed to v0.5.0 before public publish per Q1 2026-05-09 ratification. The priority-queue restructure structurally prevents this class of drift: class is determined at build-commence-time, not at queue-authoring-time.

**Class-drift rate before restructure:** 2/27 shipped versions = ~7%. After restructure: tracked at build-commence-time per the number-derivation recipe; queue stays class-agnostic until promotion.

---

**Smoke verdict:** GREEN (Stages 1-3 verified at sealed state; Stage 4 backfills post-§status; Stage 5 surfaces 2 historical findings, no halt).

Composes-with-context:

- v0.8.2 `--plan-doc` flag (the gates read the right paths for scope-descriptive plan-docs).
- v0.8.3 REMOVED-verdict-parser (the gates accept REMOVED in §status).
- v0.7.2 §4-scoping (the gates ignore cross-references in §6/§8/§11/§13).
- `feedback_version_numbers_at_release_time` (the discipline this MINOR structurally encodes).
- `feedback_scope_descriptive_ac_ids` (the convention applied to candidate slugs + AC family abbreviations).
- `feedback_locked_design_not_license_for_bad_outcomes` (the audit surfaces historical mis-classifications without proposing retroactive renames).
