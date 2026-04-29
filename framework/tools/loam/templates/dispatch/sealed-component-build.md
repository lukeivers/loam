---
description: "Sealed-component amendment build dispatch (boilerplate-heavy harness; vars carry the per-amendment specifics)."
required:
  - COMPONENT
  - AMENDMENT_NUMBER
  - AC_PREFIX
  - PLAN_PATH
  - OBJECTIVE
  - SCOPE_FENCE
optional:
  WORKING_DIRECTORY: "/Users/lukeivers/ivers-corp-pos-v2"
  HALT_TRIGGERS_EXTRA: ""
  PARALLEL_AGENTS_NOTE: ""
  ACCEPTANCE_NOTES: ""
  PRIME_OBJECTIVE_FRAMING: "Every AC under the prefix above ladders to AC.PO.1 (translation burden) and AC.PO.2 (toolkit primitive)."
---
Sealed-component amendment build (component: {{COMPONENT}}, amendment #{{AMENDMENT_NUMBER}}). WD: {{WORKING_DIRECTORY}} (verify with `pwd` and `git remote -v`).

# Plan you build against

`{{PLAN_PATH}}`

Read it fully before any code lands. ACs ({{AC_PREFIX}}) are outcome-shaped; method is your call within the AC bounds.

# Objective

{{OBJECTIVE}}

# Scope fence

{{SCOPE_FENCE}}

# Prime-objective framing

{{PRIME_OBJECTIVE_FRAMING}}

# Session-start corpus

- `CLAUDE.md` — three lenses, operational cautions
- `docs/odd-methodology.md` — §2.5, §3, §4
- `docs/rebuild/VALUE_PROPOSITION.md` — prime objective
- `docs/rebuild/FUTURE_IDEAS.md` — three lenses + dev CDCs
- `docs/rebuild/STATE.md`
- The plan referenced above + any in-flight amendment plans
- The component's `docs/rebuild/components/{{COMPONENT}}/` artefacts (proposal, research, seal narrative)

# Constraints (load-bearing)

- WD: {{WORKING_DIRECTORY}}.
- Sealed-component amendment cycle. Use `loam amend apply` and `loam amend seal` for bookkeeping.
- Plan-before-code: plan exists at the path above. Refine D-build.x in §14 method-decision register at the bottom of the plan.
- Scope-only-dispatch: this dispatch carries no method.
- No `--amend`. New corrective commits if you miss a file.
- §2.5: every line of new code/branch/test maps to {{AC_PREFIX}}.
- Backwards-compat: existing tests stay green.
- **Halt and surface ODD violations** in your work or surrounding code.

# Cycle mechanics (session-accumulated lessons)

These bind the amendment cycle's mechanical shape — divergence costs
corrective commits the no-`--amend` rule then prevents collapsing.

- **`loam amend apply` runs BEFORE the amendment commit.** The BASELINE
  bumps + initial SEAL_COMMIT advances + narrative writes are bundled
  INTO the feature commit, not split into a follow-up "manifest-apply"
  commit. Skipping pre-commit `loam amend apply` forces a corrective
  commit + a doubled seal cycle (#41 had to recover from this).
- **§14 method-decision register heading is pre-authored in the plan
  doc.** `loam amend seal --plan-doc` backfills the `### Commit SHAs`
  subsection INSIDE an existing `## 14.` heading; it does NOT create
  the heading. Verify the plan's §14 heading is present before sealing
  (otherwise the seal halts on `plan-doc-missing-section-14`, leaving
  the seal commit in place per #41 recovery).
- **`loam amend seal --plan-doc <ABSOLUTE PATH>`.** Relative paths
  crash `Path.relative_to`. Pass an absolute path.
- **One test file per AC.** Convention from AC35.x / AC40.x / AC.A.x
  onward — `tests/test_<AC_id>_<short_name>.py`, one file per AC,
  multiple test functions inside as needed. Aids ODD §2.5 reverse
  audit (every diff line traces to a named AC).
- **H19 admission debt.** When the amendment introduces a new
  top-level path (new component, new `tools/` subdir, new `docs/`
  subdir, root-level dotfile) AND the seal-diff window crosses
  `hands-off-lifecycle/`, proactively admit the new path in
  `hands-off-lifecycle/tests/test_cross_cutting.py`'s `allowed` set
  per ODD §10 per-invariant-BASELINE convention (the cross-cutting
  test is hands-off-lifecycle's seal-diff bouncer).

# Concurrent agents

{{PARALLEL_AGENTS_NOTE}}

# Halt triggers

- A new dependency would need to be added — halt; that's a re-shape candidate.
- Cross-component scope expansion beyond the scope fence — halt.
- An ODD-violating shape becomes strongly required — halt; owner rules.
- 529 / API overload — standard recovery.
{{HALT_TRIGGERS_EXTRA}}

# Acceptance shape

- Every AC under {{AC_PREFIX}} covered with named tests.
- Pos-amend full suite green.
- Plan doc updated with §14 method-decision record + commit SHAs (via `loam amend seal --plan-doc`).
{{ACCEPTANCE_NOTES}}

# Deliverable

Reply inline (under 300 words):
- Headline: build status (committed | halted).
- Commit SHA(s).
- D-build.x method choices made + one-line rationale each.
- Test green/red breakdown.
- Confirmation: existing loam amend behaviour byte-identical.
- Plan path.
- Asymmetric findings spotted in surrounding code/process — surface to parent.
- ODD-violation findings.
