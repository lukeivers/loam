# Builder-plan — Amendment #39: workspace-bootstrap tracker-seed

Authored 2026-04-25 by build agent (Heavy-B amendment 2 of 4).
Companion to `docs/rebuild/plans/amendment-39-workspace-bootstrap-
tracker-seed.md`. Files + symbols this build will touch.

---

## Pre-edit gate verified

- `git log --oneline -3` shows seal `92bead1` for amendment #38 +
  plan-SHA backfill `fa15127` already landed.
- `objective_tracker.LiftedFrom`, `objective_tracker.ObjectiveFilter`,
  `objective_tracker.ObjectiveTracker.query_projection_view` all
  importable (verified in pre-build smoke check).
- BASELINE for this amendment: `fa15127` (HEAD~1 at amendment commit
  time, mirroring #34/#35/#36/#37/#38 BASELINE-as-HEAD~1 pattern).

## D-build choices (refining plan §11)

- **D-build.1 — pos-v2-dev classifier.** Candidate (a): detect by
  presence of `docs/rebuild/VALUE_PROPOSITION.md` at the workspace
  root. Pure-function `_classify_workspace(workspace_root) -> str`
  returning `"pos-v2-dev" | "user"`. Zero new metadata surface; the
  artefact is sufficient (and is what the seed will read as
  template source if classified pos-v2-dev).
- **D-build.2 — Spec-tier descendant shape.** Candidate (a): one
  objective per spec phase (v1.0, v1.1, v1.2). Three descendants;
  each `authored_by="user"`, each with `lifted_from.source_doc =
  "docs/rebuild/spec/pos-v2-objectives-spec.md"` and
  `source_ac = "v1.0" | "v1.1" | "v1.2"`. Compact tree (~4 records);
  matches research §B.2 Phase α subset.
- **D-build.3 — Non-dev workspace UX.** Candidate (b): templated
  path `<workspace>/value-prop.md` the workspace user pre-creates.
  If absent at first-run-time, the scaffold emits a structured
  diagnostic in the result (`ScaffoldResult.tracker_seed_skipped`)
  + skips tracker seeding for that run; idempotent on re-run once
  the user supplies the file. Non-interactive, durable, parallels
  amendment #36's persona template-from-disk shape.
- **D-build.4 — Seed transaction boundary.** Candidate (b): seed
  root first; commit; then seed descendants individually. Matches
  the partial-recovery contract — interrupted seed (root present,
  descendants missing) recovers cleanly via #38's
  `query_projection_view` filter on `lifted_from.source_doc` to
  detect already-seeded records.

## Files this build will touch

### New source

- `workspace-bootstrap/src/workspace_bootstrap/adapters/tracker_seed.py`
  — the seed mechanism module. Exports:
  - `_classify_workspace(workspace_root: Path) -> str`
  - `_load_value_prop_source(workspace_root: Path, classification: str)
    -> tuple[str, str]` returning `(source_doc_path, source_text)` —
    source_doc is the relative-to-workspace path stored in
    `lifted_from.source_doc`; source_text is the raw markdown.
  - `_extract_value_prop_record_data(source_text: str) -> dict` — pure
    function returning `{"goal": ..., "ac_po_1_prose": ...,
    "ac_po_2_prose": ...}` parsed from the framework template via
    section markers (the canonical VALUE_PROPOSITION.md structure).
    On non-dev workspaces the parser is permissive: missing AC
    sections fall back to fixed AC.PO.1/AC.PO.2 prose templates so
    the user-supplied root is well-formed even when the user
    omits the criteria sections.
  - `seed_tracker(*, workspace_root, tracker_db_path, classification,
    value_prop_source_path, value_prop_text) -> TrackerSeedResult`
    — async coroutine that opens an `ObjectiveTracker`, queries via
    `query_projection_view` for already-seeded records, and creates
    only the missing root + descendants in a fixed-id-deterministic
    fashion (uses `objective_id="value-prop-root"` for the root
    and `objective_id=f"spec-{phase}"` for descendants so re-runs
    are observably idempotent without relying on UUID equality).
  - `TrackerSeedResult` dataclass: `seeded: bool`, `reason: str`
    (`"fresh_seed" | "already_seeded" | "completed_partial" |
    "skipped_no_value_prop"`), `root_id: str | None`,
    `descendants_seeded: tuple[str, ...]`, `value_prop_source: str |
    None`.

### Modified source

- `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py`:
  - Import `tracker_seed` module + invoke it inside
    `run_first_run_scaffold(...)` after the persona-directory
    install. Tracker DB path: `pos_root / "objective_tracker.sqlite"`
    (matches `OrchestratorConfig.objective_tracker_db` default).
  - Add `tracker_seed_runner: TrackerSeedRunner | None = None` kwarg
    so tests inject a synchronous runner; default impl runs
    `asyncio.run(seed_tracker(...))`.
  - Add `value_prop_path_override: Path | None = None` kwarg for
    test-fixturing the source path on non-dev workspaces (parallels
    `persona_template_override`).
  - Extend `ScaffoldResult` with `tracker_seeded: bool`,
    `tracker_seed_reason: str | None`, `tracker_root_id: str | None`,
    `tracker_descendants_seeded: tuple[str, ...]` — observable AC
    surface.

### New tests

- `workspace-bootstrap/tests/test_AC39_1_fresh_clone_seeds_root_and_descendants.py`
- `workspace-bootstrap/tests/test_AC39_2_authored_by_user_invariant.py`
- `workspace-bootstrap/tests/test_AC39_3_re_run_is_noop.py`
- `workspace-bootstrap/tests/test_AC39_4_partial_recovery_resumes.py`
- `workspace-bootstrap/tests/test_AC39_5_non_dev_workspace_user_supplied.py`
- `workspace-bootstrap/tests/test_AC39_6_no_tracker_payload_in_source.py`

### Modified tests

- `workspace-bootstrap/tests/test_no_sealed_amendments.py` — BASELINE
  literal advances from `057afdb` to `fa15127`; new comment block
  documenting amendment #39's window.
- `workspace-bootstrap/tests/SEAL_COMMIT` — sidecar advances via
  `pos-amend apply` to amendment commit, then via `pos-amend seal`
  to seal commit.

### New/modified non-source

- `docs/rebuild/plans/amendment-39-workspace-bootstrap-tracker-seed.manifest.yaml`
  — pos-amend manifest.
- `docs/rebuild/plans/amendment-39-workspace-bootstrap-tracker-seed.md`
  — append §14 method-decision record + commit SHAs post-seal.
- `workspace-bootstrap/seals/SEAL_COMMIT.tracker-seed` — narrative
  authored by `pos-amend seal`.

## Zero-content-tension resolution

The chosen method satisfies STATE.md rule #4 ("pOS core ships zero
personas/content") AND the single-tree ruling AND owner D-4
ruling (b):

- pos-v2 core source code (`workspace-bootstrap/src/`) ships ZERO
  literal value-prop prose. AC39.6 is enforced via a sentinel-scan
  test against the canonical VALUE_PROPOSITION.md primary statement.
- The "template source" for pos-v2 dev workspaces is the
  canonical doc `docs/rebuild/VALUE_PROPOSITION.md` itself, READ at
  first-run-time. The doc is core-framework documentation, not
  bootstrap-seed payload — it lives in `docs/`, not in
  `workspace-bootstrap/`. Reading from disk at first-run time is
  identical in shape to amendment #36's persona-template-from-disk
  pattern.
- On non-dev workspaces the seed reads `<workspace>/value-prop.md`
  the user supplied; if absent, the seed skips and emits a
  structured diagnostic (no fallback to Luke's content). This is
  the ONLY path under which a non-dev workspace's tracker root
  could carry value-prop content, and the content always comes
  from a workspace-user-authored file.
- Single tree: there is exactly ONE `docs/rebuild/VALUE_PROPOSITION.md`
  in the framework. Pos-v2 dev workspaces (the framework workspace
  itself) seed from it directly; clones of the framework that
  classify as pos-v2-dev (because the classifier looks for that
  file) inherit the same content — which is the explicit template-
  from-Luke shape D-4 ruling (b) sanctions. A workspace-user who
  forks pos-v2 to build their own thing replaces
  `docs/rebuild/VALUE_PROPOSITION.md` with their own content; the
  classifier still routes to the dev path; the seed reads the
  user's now-replaced file. Authority is preserved.

## Idempotency contract (mirroring amendment #36)

- Re-run on a workspace whose tracker already carries the
  value-prop root: scaffold completes; `query_projection_view(
  ObjectiveFilter(lifted_from_source_doc=...))` returns the existing
  records; no `tracker.create()` calls; no `objective_created` event
  emission; result.tracker_seed_reason = "already_seeded".
- Re-run on a workspace where root exists but some descendants are
  missing (partial-recovery case): the re-run creates ONLY the
  missing descendants; result.tracker_seed_reason = "completed_partial".
- Re-run on a workspace classified non-dev with NO `value-prop.md`:
  result.tracker_seed_reason = "skipped_no_value_prop"; non-fatal;
  re-run after the user supplies the file completes the seed.
- Idempotency enforced by stable objective IDs (`value-prop-root`,
  `spec-v1.0`, `spec-v1.1`, `spec-v1.2`). The tracker's
  `tracker.create(spec, objective_id=...)` accepts caller-supplied
  IDs, so the re-run query-then-skip is a tight check.

## Test scope

- **workspace-bootstrap full suite** — required green; 133 baseline
  + ~16 new AC39 tests.
- **Cross-component seal-diff sweep** — every other sealed
  component's `test_no_sealed_amendments.py` (or
  `test_cross_cutting.py` for hands-off-lifecycle) green at its
  pinned SEAL_COMMIT.
- **Skip pre-seal full-suite rerun** per
  `feedback_amendment_dispatch_speedups`.
- `pos-amend apply --dry-run` green prereq.

## Halt triggers reaffirmed

Per plan §9 + brief halt list. Specifically: any cross-component
source edit halts; any required relaxation of the user-authored-root
invariant halts; any path that requires shipping value-prop prose
into source halts; any deviation from amendment #36's idempotency
model halts.
