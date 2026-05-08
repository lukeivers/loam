# Self-Upgrade Framework — Proposal

**Component:** Self-Upgrade Framework (final Phase 2 foundational component)

**Status:** DRAFT — awaiting owner's review and approval before a handoff brief is drafted
**Against:** objectives spec v1.0 + v1.1 + v1.2 addenda
**Informed by:** `research-plan.md`, `research.md` (returned 2026-04-19 11:37 CDT). the owner's rulings on the three halt signals 2026-04-19 11:52 CDT.

---

## Summary

Build the self-upgrade framework as an external CLI that coordinates all seven sealed components' existing upgrade-fidelity surfaces into a single atomic operation enforcing the seven-clause acceptance (a–g) from the owner's v1.1 R1 refinement. Upgrades land as a release tag plus a YAML manifest; execution is fetch → pre-snapshot → pre-probe → orchestrator-pause → bounded drain → SIGTERM → symlink-swap → launchctl restart → post-probe → sha-verify. Rollback is whole-upgrade atomic; partial acceptance is rejected on first-principles. Clause (g) — no silent skip — is enforced **structurally** through a manifest-diff + conflict-report schema where `skipped` is not a permitted resolution value. The framework owns the observability-aggregator probe set internally (the owner-approved); no sealed-component amendment. Failed-rollback path validated by manual destructive testing at integration time (prototype-only; CI harness deferred).

## Direction

### Upgrade unit — release tag + YAML manifest

- **Upgrade unit:** a release tag `pos-v2-vX.Y.Z` backed by a commit sha, plus a per-release manifest file `pos-release.yml` that declares:
    - Every framework file with expected sha256 pre- and post-upgrade.
    - Per-component schema versions (pre and post).
    - Declared breaking changes (named migration path per change).
    - Ordered migration steps (schema or data migrations, executed in order).
- **Framework semver** is single and monotonic across components. Component-level schema versions are embedded in the manifest, not exposed as separate versioning surfaces to the user.

### Execution sequence

```
1. Fetch target release + manifest
2. Validate manifest signature / integrity
3. Pre-upgrade snapshot (all seven sealed components)
4. Pre-upgrade probe run (each component's probe set)
5. orchestrator.pause_activation("upgrade:<tag>")
6. Bounded drain window (default 30 s)
7. SIGTERM to orchestrator; wait for pid exit
8. Write framework files to staging; run manifest migrations
9. Atomic symlink swap (staging → live path)
10. launchctl kickstart orchestrator on new path
11. IPC reconnect + no-op RPC (clause a)
12. Post-upgrade probe run (each component's probe set)
13. sha-verify every file in the manifest (clause g)
14. Clause-by-clause verification pass (a–g)
15. Accept or rollback
```

### Clause-by-clause enforcement

| Clause | Enforcement |
|---|---|
| (a) active session continues | IPC socket rebind + no-op RPC; session health confirmation post-restart |
| (b) personas load unchanged | Call `build_survival_payload` on every persona; all five `SURVIVAL_LIST` fields must populate |
| (c) memory semantic round-trip | Memory's existing `upgrade.compare()` — `DriftReport.passed` is the gate |
| (d) in-flight tasks preserved | Scope-of-work + objective-tracker `assert_no_drift(..., threshold=0)` |
| (e) breaking changes surfaced | Manifest `breaking_changes` list + pre/post schema version diff; unsurfaced schema bumps halt |
| (f) upgrade reversible | File-copy snapshots of all substrates + preserved prior release tree + atomic symlink revert |
| (g) no silent skip | Manifest sha-diff pre-install + conflict-report YAML (schema has no `skipped` value) + sha-verify post-install |

### Rollback — whole-upgrade atomic

On any clause failing post-upgrade: revert symlink to prior release tree, restore all substrate snapshots, launchctl kickstart old orchestrator, emit `upgrade_rolled_back` event with failing-clause context.

Partial acceptance is rejected as a design principle — components are coupled (memory's knowledge graph contains scope ids; scope events reference objective ids; observability stores all of the above), and a half-upgraded system is an undefined state. Whole or nothing.

### Self-referential orchestrator upgrade

The framework is an **external CLI** invoked from a staging directory (never from inside the running orchestrator's path). The sequence above (steps 5–10) handles the self-referential case cleanly: the CLI process is the one doing the SIGTERM + symlink-swap + kickstart; the running orchestrator never has to upgrade itself in-flight. Orchestrator does **not** need to be unsealed — existing SIGTERM + graceful shutdown + local-state replay is sufficient.

### Conflict report (clause g enforcement)

`~/.pos/framework/history/<tag>-conflicts.yaml` — human-readable, schema-validated, one entry per changed file. Each entry carries:
- `path`
- `change_kind` (one of: `new`, `modified`, `deleted`, `unchanged`, `conflict`)
- `expected_pre_sha`, `actual_pre_sha`, `expected_post_sha`
- `resolution` (one of: `pending`, `auto-accept-local-matches-upstream`, `accept-upstream`, `keep-local`, `three-way-merge`, `abort`)

The value `skipped` is **not in the enum**. A change cannot be silently dropped; it must be resolved to one of the permitted values before upgrade proceeds. This is the structural enforcement of the owner's clause (g) — not a runtime check but a schema-level impossibility.

### Framework-owns-aggregator-probe-set (the owner ruling)

The observability aggregator does not expose a named `snapshot_probe()` method. Rather than unseal the aggregator, the framework defines its own probe set against the aggregator's DuckDB schema — a small collection of deterministic queries whose results round-trip across an upgrade. Added to the framework's probe-collection step at line 4 of the sequence.

### Failed-rollback test discipline (the owner ruling)

Prototype-only. The framework's acceptance tests cover the success path + clean-rollback path (non-destructive failures — a clause check returning False triggers rollback, rollback completes cleanly). The **failed-rollback case** (where the rollback itself fails mid-way through restoring snapshots) is validated by manual destructive testing at integration time, not a CI harness. Rationale: failed-rollback is catastrophic-tier; it needs a human-in-the-loop story (call the user, halt all autonomous work, surface recovery instructions) rather than an automated test. A CI harness that deliberately corrupts snapshots to test the failed-rollback path is overengineering for pOS's scale.

---

## Deliverables

Ten deliverables D1–D10.

### D1. Release-tag + manifest format

**Objective:** the framework defines and validates the `pos-release.yml` manifest format.
**Acceptance:** Pydantic-validated schema; malformed manifests reject with clear errors; roundtrip YAML ↔ Python model; manifest includes all fields named in the Direction section.

### D2. External CLI scaffold

**Objective:** `pos upgrade <tag>` command exists; runs as an external process (not from inside the orchestrator); invokable from a staging directory.
**Acceptance:** CLI parses args; loads manifest; prints the planned steps without executing (dry-run); `--execute` flag runs the full sequence.

### D3. Pre-upgrade snapshot

**Objective:** every sealed component's durable state is snapshotted atomically before upgrade begins.
**Acceptance:** file-copy snapshots produced for memory's Kuzu DB, scope-of-work's SQLite, objective-tracker's SQLite, orchestrator's SQLite, graceful-degradation's SQLite, observability-aggregator's DuckDB. All snapshots captured in a single coordinated pass (no drift between components). Snapshots stored under `~/.pos/framework/history/<tag>-pre/`.

### D4. Pre-upgrade probe run (framework probe set)

**Objective:** the framework collects each component's existing probe surface + runs its own probe set against the observability aggregator, producing a `pre-probe.json`.
**Acceptance:**
- Calls memory's probe, scope-of-work's `capture_pre_upgrade`, objective-tracker's `capture_pre_upgrade`, orchestrator's `snapshot_probe`, graceful-degradation's `snapshot_probe`, primary-persona's `build_survival_payload`.
- Framework's own aggregator-probe set runs a deterministic DuckDB query collection and captures results.
- All probe results serialised to `pre-probe.json` under the history directory.

### D5. Upgrade execution + orchestrator restart

**Objective:** steps 5–10 of the sequence run correctly; orchestrator gracefully stops, files update, orchestrator restarts.
**Acceptance:**
- `pause_activation("upgrade:<tag>")` halts new scope activations within the bounded drain window (default 30 s, tunable).
- SIGTERM delivered; pid exits within a bounded timeout.
- Symlink swap is atomic (no half-swapped state observable by any reader).
- `launchctl kickstart` starts the new orchestrator; IPC socket rebinds.
- A no-op RPC over the new socket succeeds (clause a check).

### D6. Post-upgrade probe run + clause verification

**Objective:** each clause (a)–(g) has a concrete check that runs post-upgrade; any failing check triggers rollback.
**Acceptance:**
- Each of the seven clauses has a named check function returning `Passed | Failed(reason)`.
- All checks run; results aggregated into `post-probe.json`.
- A failing check triggers rollback (D8); a passing suite triggers accept (D9).
- Clause (g) runs a manifest sha-verify — every expected post-upgrade file has the expected sha256; mismatches are reported with file path + expected vs actual.

### D7. Conflict report + structural clause-(g) enforcement

**Objective:** the conflict-report YAML schema exists; `skipped` is not a permitted `resolution` value; upgrade blocks on any `pending` resolution.
**Acceptance:**
- Pydantic schema for the conflict-report YAML; schema-level rejection of `skipped` as a resolution.
- Running an upgrade against files with divergent local shas produces a conflict report; the upgrade blocks until the user resolves each conflict to a permitted value via edit-the-YAML + retry.
- `abort` as a resolution cleanly cancels the upgrade without any state change to sealed components.

### D8. Rollback path (success path + clean-failure path)

**Objective:** rollback restores all snapshots, reverts symlink, restarts orchestrator on the prior release tree.
**Acceptance:**
- Success-path test: upgrade, then user invokes `pos rollback`; all snapshots restored, post-rollback probe round-trips the pre-upgrade probe results.
- Clean-failure-path test: an upgrade with a failing clause check auto-rolls-back; post-rollback probe matches pre-upgrade.
- Failed-rollback path (rollback itself fails mid-way) is **not** tested in CI; documented as prototype-only manual destructive test per ruling recorded.

### D9. Accept path + emission

**Objective:** a successful upgrade writes an `accepted.json` under the history directory, emits an `upgrade_accepted` OTel span, and clears the upgrade pause.
**Acceptance:**
- `accepted.json` contains the release tag, clause-by-clause verdicts, total duration, file counts.
- OTel span `loam.upgrade.accepted` emitted with attributes for release, duration, clause verdicts.
- `orchestrator.resume_activation()` called; scopes resume per orchestrator's normal resume path.

### D10. Bundled documentation + manual destructive-test script

**Objective:** v1.1 R4 documentation plus an explicit manual destructive-test script the builder and the owner can run at integration time.
**Acceptance:**
- Prose, architecture diagram (CLI + snapshots + orchestrator + clause checks), sequence diagrams (upgrade happy path, rollback path), conflict-report reference, manifest-authoring reference.
- A manual destructive-test script that a human can run against a test release: corrupts a snapshot mid-rollback, verifies the framework halts safely, surfaces a recovery-instructions report (rather than crashing silently). Not a CI test; a runbook.
- Relationship map: depends on all seven sealed components; consumed by nothing yet (upgrade is a root operation).
- One-page CLI reference.

---

## Spec coverage

| Criterion | Delivered by |
|---|---|
| v1.0 Self-upgrade — framework upgrades without disrupting running configuration | D5 + D8 + D9 |
| v1.1 R1 clause (a) — active session continues | D6 clause-a check |
| v1.1 R1 clause (b) — personas load unchanged | D6 clause-b check (calls primary-persona's `build_survival_payload`) |
| v1.1 R1 clause (c) — semantic round-trip memory | D6 clause-c check (calls memory's `upgrade.compare()`) |
| v1.1 R1 clause (d) — in-flight tasks preserved | D6 clause-d check (scope-of-work + objective-tracker no-drift) |
| v1.1 R1 clause (e) — breaking changes surface explicitly | D6 clause-e check + manifest schema |
| v1.1 R1 clause (f) — upgrade reversible | D3 snapshots + D8 rollback |
| v1.1 R1 clause (g) — no silent skip | D7 conflict-report + sha-verify + structural schema enforcement |
| v1.1 R4 — bundled documentation | D10 |
| v1.1 R11 — OTel observability | D9 `loam.upgrade.*` span emission + aggregator ingests it |

---

## Dependencies

### Hard dependencies (no amendments)

- All seven sealed components via their existing probe / snapshot / compare surfaces.
- launchctl (macOS) / systemd-user (Linux) already present from orchestrator build — used for the stop/start sequence.

### Soft dependencies

- None. The framework is a root operation; nothing else consumes it.

### Permitted runtime dependencies

- stdlib, pydantic, pyee, opentelemetry-api/sdk, PyYAML, duckdb (from prior components).
- No new dependencies anticipated. Anything else halt-and-signal.

---

## Assumptions (inference recorded — flagged so the builder can challenge)

1. **IPC client reconnect behaviour.** Clause (a) assumes IPC clients reconnect on socket error — that's a property of the client implementation, which lives outside the framework's sealed-component surfaces. The framework verifies the server-side rebind and a no-op RPC succeeds; it can't guarantee every client library reconnects gracefully. If the builder finds a client in the codebase that doesn't reconnect, halt and flag.
2. **30-second drain window default.** Matches orchestrator's launchd throttle interval. If the builder finds a representative drain takes longer than 30 s, halt and flag with measurement.
3. **Single atomic symlink swap** as the file-swap primitive. POSIX-standard; works on APFS + ext4. If the builder finds a cross-platform concern, halt and flag.

---

## Open questions for the owner (resolved 2026-04-19 11:57)

1. **User notification: YES.** Primary persona notifies the user via the one-on-one channel before an upgrade starts and again on success/rollback. Matches graceful-degradation's notification pattern and the v1.1 R13 + v1.2 R15 one-on-one restriction.
2. **Automatic vs user-initiated: CONFIGURABLE per workspace, captured at first-run orientation.** Two modes:
    - `require_confirmation` — framework detects an available upgrade, asks the user through the primary persona, waits for explicit yes before proceeding.
    - `notify_and_apply` — framework notifies the user, then proceeds automatically after a brief grace window (default 60 s; user can type "cancel" within the window to abort).
   - **Default for v1** (before orientation captures preference): `require_confirmation` (safest — matches the rebuild's fail-closed posture).
   - **Config key:** `auto_update_mode` in `~/.pos/upgrade-config.yaml`.
   - **Orientation integration:** when the first-run orientation component is built (future, primary-persona-layer territory), it asks the user which mode they prefer and writes the chosen value. This integration is tracked on the backlog.

---

## Complexity honesty

Research quoted 450–650 AI-minutes. Calibrated wall-clock expectation: **~45–65 minutes** — with a physical floor on the `launchctl kickstart` round-trip and Kuzu snapshot duration that doesn't compress. This is similar to the orchestrator build's size — comparable integration-layer cross-cutting concerns.

---

## What happens on approval

1. I draft the handoff brief. rulings recorded baked in: framework owns aggregator probe set (no amendment); failed-rollback prototype-only; corrected sealed-component count to 7. Plus the two the primary persona leans above on approval.
2. On brief review, a general-purpose agent is dispatched.
3. Halt-on-deviation applies.
