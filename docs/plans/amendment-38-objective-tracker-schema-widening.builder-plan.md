# Builder-plan — Amendment #38: objective-tracker schema widening

Companion to `docs/plans/amendment-38-objective-tracker-schema-widening.md`.
Records D-build.x method choices and the concrete file/symbol surface
this amendment touches.

**BASELINE:** `5ad573d` (HEAD at brief dispatch; the immediate-prior
commit `docs(plans): record amendment #37 commit SHAs in method-decision
register`). Mirrors the BASELINE-as-HEAD~1 pattern that amendments
#29 / #34 / #35 / #36 / #37 used.

**Pre-existing seal infrastructure on objective-tracker:** none. Per
amendment #18's seal commit narrative (`f1ff28b`), objective-tracker
historically shipped without a `tests/SEAL_COMMIT` sidecar or a
`tests/test_no_sealed_amendments.py` seal-diff test. This amendment
introduces both, mirroring the precedent set in amendment #32 for
primary-persona (introduced its sidecar surface alongside the first
behaviour change). The manifest's `seal_test` /`sidecar` paths
become real files inside this amendment.

## D-build.x method choices

- **D-build.1 — `lifted_from` Pydantic shape: nested `BaseModel`
  with `extra="forbid"` and `frozen=True`.** Master-research
  recommendation (a). Preserves the recursive strict-shape pattern
  ObjectiveSpec uses (`TimeBound` is the existing precedent — same
  config). Keys: `source_doc: str (min_length=1)`,
  `source_ac: str (min_length=1)`, `source_commit: str | None = None`
  (default None; min_length=1 when set).

- **D-build.2 — `query_projection_view` filter signature: Pydantic
  `ObjectiveFilter` model.** Master-research recommendation (b).
  Self-documenting in a Pydantic-first codebase; future filter
  extension lands as new `ObjectiveFilter` fields (additive).
  Initial fields: `authored_by: str | None = None`,
  `lifted_from_source_doc: str | None = None`. AC38.3 names exactly
  these two keys; further filter expressiveness is out of scope
  (plan §7).

- **D-build.3 — Storage representation: JSON-serialised text in a
  single new `lifted_from_json` column on `objective_state`.**
  Master-research recommendation (a). Matches the existing
  convention (`criteria_json`, `time_bound_json`,
  `criteria_latest_json`). Existing rows take the `DEFAULT '{}'`
  sentinel and decode to `lifted_from is None`. The
  `ObjectiveCreated` event payload already serialises every spec
  field via `event.model_dump(mode="json")`, so `lifted_from`
  flows through events with no event-schema migration. The query
  reads the projection cache row's `lifted_from_json` column for
  filter matching (no full-replay scan needed).

- **D-build.4 — D8 probe-fixture extension: extend the existing
  probe set with `lifted_from`-shaped probes.** Master-research
  recommendation (a). Single probe set, single drift threshold,
  one `_seed` function in `test_d8_upgrade_fidelity.py`.

## File surface

- `objective-tracker/src/spec.py` — add `LiftedFrom` Pydantic model;
  extend `ObjectiveSpec` with `lifted_from: LiftedFrom | None = None`.
- `objective-tracker/src/events.py` — add `lifted_from: LiftedFrom |
  None = None` to `ObjectiveCreated` (additive optional field; old
  events deserialise with `None`).
- `objective-tracker/src/projection.py` — fold `lifted_from` from
  `ObjectiveCreated` into `ObjectiveProjectionData`; emit it in
  `projection_to_state_row`.
- `objective-tracker/src/projection_view.py` — surface `lifted_from`
  on the public `ObjectiveProjection`.
- `objective-tracker/src/store.py` — add `lifted_from_json` column
  to `objective_state` schema (additive `ALTER TABLE` gated on
  column-existence check for in-place upgrades).
- `objective-tracker/src/runtime.py` — add
  `query_projection_view(filter: ObjectiveFilter) -> tuple[
  ObjectiveProjection, ...]`; thread `spec.lifted_from` into
  `ObjectiveCreated` on `create()`.
- `objective-tracker/src/filter.py` (new) — `ObjectiveFilter`
  Pydantic model.
- `objective-tracker/tests/test_AC38_1_lifted_from_field.py` — AC38.1.
- `objective-tracker/tests/test_AC38_2_round_trip_preservation.py` — AC38.2.
- `objective-tracker/tests/test_AC38_3_query_projection_view.py` — AC38.3.
- `objective-tracker/tests/test_AC38_4_d8_lifted_from_probes.py` — AC38.4.
- `objective-tracker/tests/test_AC38_5_existing_suite_unchanged.py` —
  meta-test asserting baseline test files unmodified.
- `objective-tracker/tests/test_no_sealed_amendments.py` (new) —
  AC38.S seal-diff invariant. Mirrors primary-persona's pattern:
  `BASELINE = "5ad573d"`, sidecar at
  `objective-tracker/tests/SEAL_COMMIT`, fallback to HEAD when sidecar
  is the placeholder.
- `objective-tracker/tests/SEAL_COMMIT` (new) — placeholder until
  `pos-amend apply` writes the BASELINE; `pos-amend seal` advances
  to the seal commit SHA.
- `objective-tracker/seals/SEAL_COMMIT.schema-widening` (new) —
  amendment-cycle narrative target.
- `docs/plans/amendment-38-objective-tracker-schema-widening.manifest.yaml`
  (new) — pos-amend manifest.

## Implementation order

1. Author `LiftedFrom` + `ObjectiveFilter` Pydantic models.
2. Wire `lifted_from` through spec → events → projection → store →
   runtime; add `query_projection_view`.
3. Author AC38.1 / AC38.2 / AC38.3 / AC38.4 tests.
4. Author seal-test + sidecar + AC38.5 meta-test.
5. Author manifest.
6. Run objective-tracker test suite; confirm 86 baseline + 5 AC files
   green.
7. Run `pos-amend apply --dry-run` against the manifest; confirm exit 0.
8. `pos-amend apply` to bump BASELINE + sidecar + widen bindings.
9. Amendment commit (single coherent commit covering source + tests +
   manifest + sidecar).
10. `pos-amend seal` to advance the sidecar to the amendment SHA and
    write the narrative file.
11. Seal commit.
12. Cross-component seal-diff sweep.
