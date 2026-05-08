# Builder-plan — Amendment #40 (primary-persona tracker-context contributor)

Pre-edit gate verified:
- `objective-tracker/tests/SEAL_COMMIT` = `be7737b…` (#38 amendment commit; seal at 92bead1).
- `workspace-bootstrap/tests/SEAL_COMMIT` = `3f0cd8d…` (#39 amendment commit; seal at 13770df).
- `query_projection_view` callable on `ObjectiveTracker`; `ObjectiveFilter` exposes `authored_by` + `lifted_from_source_doc`; `LiftedFrom` exported.

## Files to add

- `primary-persona/src/tracker_context.py` (new) — owns:
  - `TrackerClient` Protocol — narrow surface (`query_projection_view`, `trace_to_root`, `close`); decoupled from objective_tracker source per the D7/MemoryClient precedent.
  - `TRACKER_DB_FILENAME = "objective_tracker.sqlite"` — private constant; AC40.6 path resolution. Documented as "convention parity with workspace-bootstrap; method-level — AC measures outcome (workspace-identity-derived path resolves correctly), not constant equality."
  - `tracker_db_path_for(workspace_root)` — pure function returning `<workspace_root>/objective_tracker.sqlite`.
  - `TrackerContextConfig` dataclass — `workspace_root`, `value_prop_root_id="value-prop-root"` (stable ID per #39 contract), `objective_id_cap=20`, `char_cap=2000` (sub-cap; composer's structural cap is 10 000, this leaves headroom for other contributors).
  - `_load_in_flight_projections(tracker, root_id)` — pure; uses `query_projection_view()` then `trace_to_root` to filter to descendants of root_id whose status is `proposed | active` (the "in flight" set per AC40.1; tracker uses lifecycle states `proposed→active→{achieved|abandoned}`; "in flight" = pre-terminal). NOTE: plan AC40.1 names "started, decomposed" status set — that's terminology drift; the tracker's actual lifecycle is `proposed | active | achieved | abandoned`. AC40.1 outcome is "non-empty when in-flight objectives exist"; "in flight" maps to `{proposed, active}` in the tracker's actual vocabulary. ODD §2.5: this is method (a vocabulary mapping) not a deviation from the AC outcome.
  - `_render_projection_block(projections, root_id, char_cap, objective_id_cap)` — pure; produces the textual block. Format:
    ```
    [primary-persona/tracker-context]
    workspace value-prop root: <goal>
    in flight (N):
      - <id> [<status>]: <goal>  (<- root)
      - <id> [<status>]: <goal>  (<- parent_goal -> root)
      ...
      [K more in-flight objectives truncated]
    ```
    Identity-anchor-style bracketed marker on first line ⇒ compaction-resilient signal the persona retains.
  - `build_tracker_context_contributor(config, *, tracker_factory)` — factory returning the contributor callable. `tracker_factory` is a callable producing a `TrackerClient`; defaults to `lambda: ObjectiveTracker(tracker_db_path_for(config.workspace_root))` lazily-imported. Allows tests to inject. On any exception during tracker open / query, contributor returns either empty string OR a graceful-degradation marker (`[primary-persona/tracker-context unavailable: <class>]`) and emits `pos.persona.tracker_context.unavailable` event. AC40.3.
  - `register_tracker_context(composer, *, workspace_root, ...)` — convenience wrapper mirroring `register_memory_retrieval` shape.
  - Trigger kind: `TriggerKind.session` (D-build.1).
  - Char cap: contributor's own sub-cap = 2000 chars (AC40.4); proactive trim ahead of the composer's structural 10 000-char refusal.

- `primary-persona/src/observability.py` — append two diagnostic helpers:
  - `tracker_context_composed_event(handle, in_flight_count, truncated_count)`
  - `tracker_context_unavailable_event(handle, failure_class, detail)`

## Files to add (tests)

One test file per AC:

- `primary-persona/tests/_helpers_d40.py` — non-test helpers:
  - `FakeTrackerClient` — Protocol-compatible stub recording calls, returning configured `query_projection_view` results, configurable error injection.
  - `seed_tracker_for_test(tmp_path)` — invokes the actual `objective_tracker.ObjectiveTracker` to seed a small value-prop-rooted tree at `tmp_path / "objective_tracker.sqlite"` (mirrors a fresh-clone first-run minus the workspace-bootstrap dependency).
- `primary-persona/tests/test_AC40_1_in_flight_non_empty.py`
- `primary-persona/tests/test_AC40_2_workspace_root_filter.py`
- `primary-persona/tests/test_AC40_3_graceful_failure.py`
- `primary-persona/tests/test_AC40_4_cap_guard.py`
- `primary-persona/tests/test_AC40_5_empty_when_none_in_flight.py`
- `primary-persona/tests/test_AC40_6_workspace_identity_path.py`
- `primary-persona/tests/test_AC40_7_framework_not_content.py`
- AC40.S — already covered by existing `primary-persona/tests/test_no_sealed_amendments.py`; BASELINE advances via `pos-amend apply`.

## Files to update

- `primary-persona/tests/test_no_sealed_amendments.py` — `BASELINE` literal advances via `pos-amend apply` (do not hand-edit; the manifest names BASELINE).
- `primary-persona/tests/SEAL_COMMIT` — sidecar bumps via `pos-amend seal` after the amendment commit lands.

## Manifest (new)

`docs/plans/amendment-40-primary-persona-tracker-context-contributor.manifest.yaml` — per plan §10 stub. BASELINE = HEAD~1 of the amendment commit (i.e., the immediate-prior commit) per #34–#39 pattern. Captured at amendment-commit time.

## Method-decision register additions to plan §11 (post-build)

D-build.1 → SessionStart only. Rationale: master-research recommended; objective-tree state changes at human cadence; per-turn freshness adds cost without value v1; lighter cold-start budget. AC40.1 measures outcome.

D-build.2 → goals + status + parentage (chain back to root). Rationale: parentage costs ~30 chars/line and substantially improves compaction resilience — persona retains lineage even after compaction. Identity-anchor-style bracketed marker on first line.

D-build.3 → hard-truncation by depth-first walk order; remainder count surfaced as truncation marker. Master-research recommendation. Deterministic, easy to test.

D-build.4 → diagnostic events `pos.persona.tracker_context.composed` and `pos.persona.tracker_context.unavailable`. Matches existing `pos.persona.<event>` naming.

D-build.5 → tracker DB path via private constant `TRACKER_DB_FILENAME = "objective_tracker.sqlite"` mirroring workspace-bootstrap's convention. Documented as "method-level constant; AC40.6 measures outcome (correct path resolution per workspace), not literal equality." No cross-component import surface.

## Halt-and-surface findings (declared up front)

The plan's AC40.1 names statuses `{started, decomposed}`; the actual `ObjectiveStatus` enum uses `{proposed, active, achieved, abandoned}`. "In flight" = `{proposed, active}` (pre-terminal). The plan's terminology is from a hypothetical authoring vocabulary; the build adopts the tracker's actual vocabulary as method (per ODD §2.5: AC bounds outcome). NOT a halt — AC outcome is "non-empty when in-flight objectives exist" and that is verifiable in the tracker's actual vocabulary. Surface to owner in the deliverable.

## Build sequence

1. Author `tracker_context.py` source.
2. Append observability helpers.
3. Author `_helpers_d40.py`.
4. Author seven AC tests.
5. Run primary-persona test suite from primary-persona/.venv (or repo .venv).
6. `pos-amend apply --dry-run` against the new manifest. Expect missing-admission list to confirm scope; iterate.
7. Stage + commit amendment.
8. `pos-amend apply` → bumps BASELINE + SEAL_COMMIT to amendment commit.
9. Sweep seal-diff across every other sealed component.
10. `pos-amend seal` → narrative append + SEAL_COMMIT bump to seal commit.
11. Backfill SHAs into plan §14.
