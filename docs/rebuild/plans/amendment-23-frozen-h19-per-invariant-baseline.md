# Amendment #23 — frozen-H19 BASELINE + per-invariant-BASELINE convention

Plan for amendment #23. Eliminates the H19 serialization bottleneck by
freezing hands-off-lifecycle's `BASELINE` at project-start and codifies
the per-invariant-pinning pattern (amendment #21's `7d27f00`) into a
reusable convention that future sealed-component invariants adopt.

Rationale lives in the research doc, not here:

- **Research doc:** `/Users/lukeivers/ivers-corp-pos-v2/.scratch/claude-output/pos-v2-parallel-dev-research.md`
  (design-research agent, 2026-04-22). §4.1 = frozen-H19. §4.2 =
  per-invariant BASELINE. Luke accepted all recommendations.
- **Tool-first:** pos-amend CLI (amendment #22, `60dc0c6`) performs the
  mechanical bookkeeping. This amendment is the tool's second real-world
  validation — if the tool fails apply/seal we fix it in a corrective
  commit, not by hand.

## Scope recap (from dispatch brief + research doc)

1. Freeze H19's `BASELINE` at project-start (`3780603`) — the pre-
   amendment-#1 commit. The `allowed` top-level-bucket set becomes
   monotonic (grows only; never shrinks). Diff window is `3780603..SEAL`
   for the entire project lifetime.
2. Codify a per-invariant-BASELINE convention in a new section of
   `docs/odd-in-pos.md`. Document when to use frozen vs floating
   BASELINE, how to declare per-invariant pinned windows, and reference
   amendment #21's AC7 example as the prototype.
3. Extend pos-amend manifest schema iff needed to carry a
   `frozen_baseline: true` marker for components whose module-top
   BASELINE should NOT advance. (This is a minimal, backward-compatible
   extension; `schema_version` stays 1.)
4. Update `tools/pos-amend/README.md` + tool tests to reflect any
   schema/command changes.
5. Add a test fixture (adversarial synthetic diff) in
   `hands-off-lifecycle/tests/test_cross_cutting.py` that proves the
   surface-introduction invariant still catches a new unadmitted
   top-level directory.
6. Follow the sealed-component amendment cycle via pos-amend: validate →
   dry-run → apply → amendment commit → seal → seal commit.

## Current state (verified `git log --oneline --reverse | head`)

- Project-start SHA: `3780603` ("docs(rebuild): extend value-prop to
  cover token management + built-artifact hygiene", 2026-04-21). This
  is the pre-amendment-#1 tip — see the existing comment on
  `test_cross_cutting.py:311–314` and research doc §4.1. Confirmed.
- Current `BASELINE` at `test_cross_cutting.py:274` = `9559ca7`.
- `allowed` set on `test_cross_cutting.py:320–416` contains 17 entries
  (top-level dirs + top-level files).
- Current git tip: `d07af91`.

## §1 — H19 frozen-BASELINE design

### Change to `hands-off-lifecycle/tests/test_cross_cutting.py`

- **BASELINE** literal moves from `"9559ca7"` → `"3780603"`. Permanent.
- Delete the ~240 lines of amendment-history commentary above BASELINE
  (lines 28–273). That history lives canonically in
  `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run`. Replace with a
  short comment citing the frozen-BASELINE convention, naming the
  project-start SHA, and referencing §4.1 of the research doc.
- `allowed` set is preserved byte-for-byte (content). Fidelity is now
  "no new top-level dir has ever appeared in the project that isn't
  admitted", not "no new top-level dir since the last amendment tip."
- `test_H19_diff_scope_covers_only_approved_surfaces` continues to diff
  `BASELINE..SEAL_COMMIT`. With BASELINE pinned at project-start and
  SEAL_COMMIT advancing per-amendment as today, the diff window is
  monotonically expanding — correct: we want cumulative surface
  inspection, not per-amendment inspection.
- Docstring updated to name the invariant: "surface-introduction check
  across project history", not "amendment-scoped diff."

### Convention declared on the test

- A comment block at the top of `test_cross_cutting.py` names H19 as
  **frozen-BASELINE** per the convention doc (see §4 below).
- The `allowed` set's monotonicity is asserted implicitly (new entries
  land via amendment; existing entries are never removed). No explicit
  monotonicity test — the convention is policy, not code.

### Adversarial synthetic test

- `test_H19_frozen_baseline_catches_unadmitted_bucket` — a new test
  that builds a synthetic set of `touched` top-level paths in-memory
  (NOT via git) containing one admitted + one unadmitted bucket, then
  calls the same set-difference the real test does, and asserts the
  unadmitted bucket surfaces. Proves the invariant's fidelity is
  preserved under the frozen-BASELINE design.

### Empty-amendment case

- `test_H19_empty_amendment_yields_empty_hands_off_lifecycle_diff` — a
  meta-test that asserts: for any SEAL within the `allowed` set, the
  diff window `BASELINE..SEAL` contains only admitted prefixes. This
  is the existing H19 assertion; new test is tautological with the
  existing one but frames it as the frozen-BASELINE acceptance (the
  brief §5 item (a)).

### Not in scope

- Per-component `test_no_sealed_amendments.py` BASELINEs stay floating.
  The research doc §2.2 showed those advance correctly (only when the
  component is in-scope for the current amendment). No change here.
- `allowed_prefixes` / `allowed_files` tuples stay floating (grow per-
  amendment). Universal-path admission (amendment #22) already handles
  the cross-amendment friction; no further retrofit.

## §2 — Per-invariant-BASELINE convention

Applies to any invariant-shaped assertion that lives inside a seal-diff
test and whose fidelity is point-in-time (proving an invariant held as
of a specific amendment window) rather than cumulative.

### Pattern (codified)

```python
def test_AC<N>_<name>() -> None:
    """AC<N> invariant description. Pinned to amendment #<M>'s window."""
    AMENDMENT_<M>_BASELINE = "<sha>"
    AMENDMENT_<M>_SEAL = "<sha>"
    # ... diff or assertion using the pinned window ...
```

Constants are function-scoped (NOT module-top). Module-top `BASELINE`
stays for cumulative-admissibility checks only. Once authored, the
pinned constants never move unless the invariant itself is being
restated.

### Prototype (already on disk)

`telegram-interface/tests/test_no_sealed_amendments.py::test_AC7_no_telegram_interface_src_edits`
(introduced at `7d27f00` as amendment #21's corrective). Uses
`amendment_9_baseline = "b9e1f96"` and `amendment_9_seal = "4f8b933"`.
This test becomes the convention's canonical example.

### Second candidate — deferred

The research doc §4.2 names retrofit vs new-only as an open question.
Decision: new-only going forward. Retrofit is mechanical and optional;
future invariants author per-invariant pinning when they need point-in-
time fidelity. No existing test besides AC7 currently needs the
treatment — all other seal-diff tests are cumulative-admissibility
shaped. Flag as a follow-up only if a natural retrofit target surfaces.

### Documented in

`docs/odd-in-pos.md` gains a new section (proposed §10 — "Per-invariant
BASELINE convention"). The content covers:

- When an invariant is point-in-time vs cumulative.
- How to declare the pinned window (code template above).
- Frozen-vs-floating decision framework for whole-test BASELINEs
  (H19's frozen pattern as the counterpoint example).
- Migration guidance: retrofit is optional; new invariants use the
  convention by default.
- Explicit note: this convention unlocks disjoint-component parallel
  development per research doc §3 (Class B amendments).

## §3 — pos-amend tool changes

### Schema extension (backward-compatible, schema_version stays 1)

Add an optional per-component field `frozen_baseline: bool` (default
`false`). Semantics:

- `frozen_baseline: false` (default) — tool bumps the module-top
  `BASELINE = "..."` literal to the manifest baseline. Current
  behaviour.
- `frozen_baseline: true` — tool SKIPS the BASELINE literal bump for
  this component. Everything else (sidecar advance, tuple widening,
  narrative append) is unchanged.

This is the minimum surface needed to express "this component's
BASELINE is frozen; don't touch it." Rationale: preserves the tool's
idempotency guarantee while letting amendment manifests declare a
frozen-BASELINE component without special-casing hands-off-lifecycle in
the tool's code.

### Files changed

- `tools/pos-amend/src/pos_amend/manifest.py` — `ComponentEntry` gains
  an optional `frozen_baseline: bool = False` field. Parser wires it.
- `tools/pos-amend/src/pos_amend/commands/apply.py` — inside the
  per-component loop, if `comp.frozen_baseline` is True, skip the
  `set_baseline(...)` call.
- `tools/pos-amend/README.md` — new paragraph under "Manifest schema
  (v1)" documenting `frozen_baseline`, with the H19 example.
- `tools/pos-amend/tests/test_manifest.py` — new test that a manifest
  with `frozen_baseline: true` parses correctly.
- `tools/pos-amend/tests/test_integration_universal_paths.py` (or new
  test file) — add a test that `apply` with `frozen_baseline: true`
  leaves the BASELINE literal untouched while still advancing the
  sidecar and widening tuples.

### Sealed-at-schema-version invariant

Schema stays at `1`. No migration. Existing manifests parse unchanged
(default `False`). No version bump required.

## §4 — Policy doc

Primary home: `docs/odd-in-pos.md` — new top-level section (§10) as
named above. This keeps the convention co-located with the ODD-in-pos
methodology (the framework rule set that calls out fidelity-preserving
invariants). FUTURE_IDEAS.md is for *temporary parking*; the per-
invariant-BASELINE convention is a committed convention, not an idea.

Section covers:

1. **What the convention is** (per-invariant frozen pin, code
   template, AC7 prototype).
2. **Frozen-vs-floating decision framework** for the whole-test
   BASELINE (H19 frozen; per-component floating; decision rubric
   drawing from research doc §2.1–§2.2).
3. **Migration guidance** — retrofit optional; new invariants use
   the convention by default.
4. **Parallel-development unlock** — one sentence referencing
   research doc §3 (Class A + Class B amendments parallelise once
   H19 is frozen; the convention keeps parallel amendment commits
   from racing on per-invariant pins).

## §5 — Test coverage map

| AC | Test | File |
|---|---|---|
| AC23.1 | H19's frozen BASELINE admits the current tree | `test_H19_diff_scope_covers_only_approved_surfaces` (existing, unchanged behaviour; verifies with new BASELINE value) |
| AC23.2 | Adversarial unadmitted bucket is caught | `test_H19_frozen_baseline_catches_unadmitted_bucket` (new) |
| AC23.3 | pos-amend manifest parser accepts `frozen_baseline` field | `test_manifest.py::test_T15_frozen_baseline_field_accepted` (new) |
| AC23.4 | pos-amend apply skips BASELINE bump when `frozen_baseline: true` | `test_integration_frozen_baseline.py::test_T16_frozen_baseline_preserves_baseline_literal` (new) |

Every AC23.* maps to one named test. Per ODD §2.5, no orphan code.

## §6 — pos-amend manifest for this amendment

`docs/rebuild/plans/amendment-23-frozen-h19-per-invariant-baseline.manifest.yaml`:

- `baseline: d07af91` (current git tip — the amendment-22 research
  preservation commit).
- Single component: `hands-off-lifecycle` with
  `frozen_baseline: true` (as of this amendment — the convention
  applies to this amendment itself). The manifest's effect on
  hands-off-lifecycle becomes: SEAL_COMMIT sidecar advances to
  `d07af91` at apply; seal bumps to HEAD. No BASELINE bump (it's
  being frozen by this same amendment — but after this commit lands
  the literal value is `3780603` which we manually write as part of
  the amendment-code changes, NOT via the tool).
- Narrative target: `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run`
  with a block documenting the amendment.
- No universal-paths changes (amendment #22 already admitted the
  universals everywhere relevant).
- `tools/pos-amend/` component: the tool edits itself — we list a
  second component entry? No — pos-amend doesn't currently have a
  seal-diff test of its own (per `amendment-22` plan, its tests are
  local and don't use BASELINE/allowed_prefixes). Skip.

### Touched paths (for dry-run admission check)

- `hands-off-lifecycle/tests/test_cross_cutting.py` (admitted via
  hands-off-lifecycle top-level bucket — already in H19 `allowed`).
- `hands-off-lifecycle/tests/SEAL_COMMIT` (admitted).
- `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run` (admitted).
- `tools/pos-amend/src/pos_amend/manifest.py` (tools bucket already
  admitted under `allowed`).
- `tools/pos-amend/src/pos_amend/commands/apply.py` (same).
- `tools/pos-amend/tests/test_manifest.py` (same).
- `tools/pos-amend/tests/test_integration_frozen_baseline.py` (new
  file; tools bucket admitted).
- `tools/pos-amend/README.md` (same).
- `docs/odd-in-pos.md` (universal file, admitted post-#22).
- `docs/rebuild/plans/amendment-23-*.md` and `*.manifest.yaml` (plans
  prefix, universal).

## §7 — Commit sequence

1. **Author plan + manifest:** this doc + the `.manifest.yaml`.
2. `pos-amend validate <manifest>` → exit 0.
3. `pos-amend apply --dry-run <manifest>` → exit 0.
4. `pos-amend apply <manifest>` → stages sidecar advance + any other
   mechanical bookkeeping. Note: because `frozen_baseline: true`, no
   BASELINE literal is bumped by the tool.
5. Human edits:
   - Rewrite `test_cross_cutting.py`: change BASELINE from `9559ca7`
     → `3780603`; delete the ~240-line amendment-history comment
     block; add short convention-aware comment; update docstrings.
   - Add adversarial test `test_H19_frozen_baseline_catches_unadmitted_bucket`.
   - Extend pos-amend `ComponentEntry` dataclass + parser.
   - Extend `apply.py` to honour `frozen_baseline`.
   - Write `docs/odd-in-pos.md` §10.
   - Update `tools/pos-amend/README.md`.
   - Add pos-amend tests (`test_T15_*`, `test_T16_*`).
6. Pre-amendment test run:
   - Full suite: `hands-off-lifecycle/`, `tools/pos-amend/`. All
     green.
   - Seal-diff-only for other 9 sealed components (per speedup CDC).
7. **Amendment commit:**
   `fix(hands-off-lifecycle, tools): freeze H19 BASELINE + establish per-invariant-BASELINE convention (amendment #23)`
8. `pos-amend seal <manifest>` → advances sidecar to HEAD + appends
   narrative.
9. **Seal commit:**
   `chore(seals): frozen-h19-per-invariant-baseline seal — hands-off-lifecycle at <amendment-sha>`
10. Post-seal seal-diff-tests-only across all 10 components.

## §8 — Halt triggers (from brief)

- Frozen BASELINE design can't reproduce H19's invariant (adversarial
  fails) → halt.
- Convention requires structural API change beyond research doc →
  halt.
- pos-amend schema-evolution gap needing redesign (not minor bump) →
  halt. (Current design is backward-compatible; schema_version stays
  1; we only extend `ComponentEntry`.)
- Scope cascades beyond hands-off-lifecycle + pos-amend + convention
  doc + `allowed` prefix changes → halt.
- Any test break beyond known safety-layer `primary_persona`
  ModuleNotFoundError → investigate.

## §9 — ODD §2.5 compliance declaration

Every change maps to an AC (AC23.1–AC23.4). No orphan code. The
frozen-BASELINE design preserves H19's named fidelity (surface-
introduction invariant). The per-invariant convention codifies an
existing pattern (amendment #21's `7d27f00`) — no new invariant is
authored.
