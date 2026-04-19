# Self-Upgrade Framework

External CLI that coordinates every sealed component's existing
upgrade-fidelity surfaces into a single atomic operation enforcing the
seven-clause acceptance (a–g) from v1.1 R1 of the pOS objectives spec.

## At a glance

- **Upgrade unit:** release tag `pos-v2-vX.Y.Z` + per-release
  `pos-release.yml` manifest with sha256 per file, per-component
  schema versions, declared breaking changes, ordered migrations.
- **Execution:** external CLI from a staging directory; never from
  inside the live orchestrator's path.
- **Rollback atomicity:** whole-upgrade atomic. Partial acceptance is
  rejected — components are coupled.
- **Self-referential case:** orchestrator stays sealed; SIGTERM +
  graceful shutdown + `launchctl kickstart` on the new path.
- **No silent skip:** the conflict-report YAML schema structurally
  forbids `resolution: skipped`. The Python enum does not contain that
  value; parsing fails at the schema layer.
- **Framework owns the aggregator probe set** internally — no
  sealed-component amendment.
- **User notification:** primary persona, one-on-one channel only
  (v1.1 R13 + v1.2 R15). `auto_update_mode` toggles
  `require_confirmation` (default) vs `notify_and_apply`.

## Documents in this bundle

- `architecture.md` — the pieces and how they fit
- `sequences.md` — happy path + clean-failure rollback + conflict-
  reporting flow (text sequence diagrams)
- `manifest-reference.md` — `pos-release.yml` schema reference
- `conflict-report-reference.md` — `<tag>-conflicts.yaml` schema
  reference
- `cli-reference.md` — one-page CLI summary
- `notification-flow.md` — both `auto_update_mode` modes end-to-end
- `measurement-timing.md` — measured drain + symlink-swap timing on
  the test machine
- `../scripts/destructive_test_runbook.sh` — manual destructive-test
  runbook (prototype-only per Luke's ruling)

## Relationship map

- **Depends on** (all via existing sealed surfaces; no amendments):
  memory-system, scope-of-work, objective-tracker, orchestrator,
  graceful-degradation, observability-aggregator, primary-persona.
- **Consumed by** nothing — the self-upgrade framework is a root
  operation.
- **Runtime deps:** stdlib, pydantic, pyee, opentelemetry-api/sdk,
  PyYAML, duckdb.
- **Test deps:** pytest, pytest-asyncio.

## Phase 2 sealing

This is the **final Phase 2 foundational component**. On seal, Phase 2
closes and the rebuild transitions to Phase 3.
