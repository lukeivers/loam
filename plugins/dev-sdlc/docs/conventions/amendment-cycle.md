# Amendment-cycle convention

> **An amendment is the unit of structural change in pos-v2 — one or more commits per the commit ladder, fenced by sealed-component seal-tests, narrated in a §14 method-decision register, sealed via `loam amend seal`. Amendments compose into sub-amendment series (M1.rename's M1a..M1g, M6's M6a/M6b/M6c/M6b.0/M6b.1) when the structural change is too large for a single sealed cycle.**

This document is the concise codification of the amendment-cycle convention. The exhaustive narrative — including per-cycle rationale + how the cycle composes with the five-gate chain — lives in `../odd-in-loam.md` + STATE.md "Governing rules" rule #1 (the master sequencing rule).

## 1. The cycle

A standard amendment cycle, in order:

1. **Research** (if non-trivial). Produces `docs/rebuild/plans/research/<slug>.md` or inline research section in the plan.
2. **Spec** (if a new component / capability — uses the master plan-doc as the spec).
3. **Plan + manifest**. Produces `docs/rebuild/plans/<slug>.md` + `<slug>.manifest.yaml`. Committed first per `feedback_plan_before_code`.
4. **Build**. Feature commits per the plan. Corrective commits if the plan's seal-diff fence misses a path or a test reveals an empirical issue.
5. **Apply**. `loam amend apply` commit. Auto-generated; deterministic.
6. **Seal**. `loam amend seal` commit. Advances SEAL_COMMIT sidecars; writes the per-amendment seal narrative; runs the seal-tests.
7. **§14 SHA backfill**. `docs(plans):` commit recording all the cycle's SHAs in the plan-doc's §14 register. Runs after the seal commit lands so all SHAs are known.

## 2. Sub-amendment series

When an amendment's surface is too large for a single cycle (rule of thumb: predicted wall-clock > ~360 min OR fence-collision risk across components), the amendment SPLITS into a sub-amendment series. Each sub-amendment:

- Has its own sub-plan + manifest.
- Has its own AC family (extending the master family — e.g. `AC.OSS-M6b0.\*` extends `AC.OSS-M6.\*`).
- Has its own seal cycle.
- Composes against the predecessor sub-amendment's seal commit as its BASELINE.

Series SHIP in dependency order. Each sub-amendment is independently rollback-safe (revert the sub-amendment's seal commit; the prior sub-amendment's state remains intact).

## 3. Halt-and-surface

At any cycle gate, the builder may encounter a condition that exceeds the dispatch's authorised scope (per `feedback_subagent_odd_violation_halt`):

- Surrounding-code ODD violation surfaces while editing.
- Empirical disposition for an inventory item turns out wrong.
- Wall-clock approaches halt-trigger.
- Frozen-baseline / byte-content invariant breach beyond ODD §4 in-band.
- An item's MOVE creates a cycle / cross-tree dependency.

The builder STOPS, surfaces the finding in a halt-and-surface report at `workspace/.scratch/claude-output/<slug>-halt-surface.md`, and returns to the dispatcher. The dispatcher rules on each finding; on resumption, the builder ratifies the rulings in the new sub-plan's §2.

## 4. Rollback granularity

Each amendment is independently revertable (`git revert <seal-sha>`). Sub-amendment series ship rollback granularity matching structural risk: a 5-sub-amendment series exposes 5 rollback points; a single-amendment ship exposes 1.

## 5. Cross-references

- Master sequencing rule: `docs/rebuild/STATE.md` §"Governing rules" rule #1.
- Plan-doc + manifest convention: `plan-docs.md`.
- Commit-ladder convention: `commit-ladder.md`.
- Sealed-component invariants: `sealed-component-invariants.md`.
- CDC: `../cdcs/plan-before-code.md` + `../cdcs/amendment-dispatch-test-scope.md`.

## 6. Applied-immediately footer

The amendment-cycle convention is followed by every structural change in pos-v2 from project-start forward. Pre-M6b.0 the cycle lived in precedent + dispatch templates + `docs/odd-in-loam.md`; M6b.0 names + locates the codification.
