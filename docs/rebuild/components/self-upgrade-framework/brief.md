# Handoff Brief — Self-Upgrade Framework

**Component:** Self-Upgrade Framework (final Phase 2 foundational component)
**For:** general-purpose Agent (builder)
**Authored by:** the primary persona
**Status:** DRAFT — awaiting owner's review before dispatch
**Against:** `proposal.md` (approved 2026-04-19 11:57 CDT, both open questions resolved)
**Spec:** objectives spec v1.0 + v1.1 + v1.2 addenda

---

## Objective

Deliver a production-ready self-upgrade framework as an external CLI that coordinates every sealed component's existing upgrade-fidelity surfaces into a single atomic operation, enforces all seven clauses (a)–(g) of the owner's v1.1 R1 refinement, and rolls back cleanly on any clause failure. The framework owns the observability-aggregator probe set internally (no sealed-component amendment). Clause (g) — no silent skip — is enforced structurally through a YAML-schema conflict report in which `skipped` is not a permitted resolution value. On landing and sealing, Phase 2 closes.

---

## Hard constraints

1. **Implementation language:** Python 3.13 dev target, `pos-v2` branch. Work lives under `pos-v2/self-upgrade/` (mirror prior component layouts).
2. **No amendments to any of the seven sealed components.** Memory, scope-of-work, primary-persona layer, objective tracker, orchestrator, graceful-degradation, observability-aggregator all stay as they are. The framework consumes their existing probe / snapshot / compare surfaces; the framework owns its own probe set for the observability aggregator (the owner-approved, no amendment).
3. **Zero carryover from current pOS.** `bin/upgrade-pos` (Ruby) is the anti-pattern that inspired clause (g); not a reference implementation.
4. **Permitted runtime dependencies:** stdlib, `pydantic`, `pyee`, `opentelemetry-api`, `opentelemetry-sdk`, `PyYAML`, `duckdb`. Test-only (pytest, pytest-asyncio) permitted. Anything else requires halt-and-signal.
5. **Max-first.** LLM inference is unexpected; if used for conflict-resolution wording or upgrade-narrative authoring, uses Claude via Max.
6. **No personas in pOS core.**
7. **No assumed downstream consumer (A1 correction).** Framework emits OTel; aggregator subscribes automatically.
8. **Halt-on-deviation.** Silent deviation forbidden.
9. **Bundled documentation per v1.1 R4.**

## rulings recorded baked into this brief

- **Upgrade unit:** release tag `pos-v2-vX.Y.Z` + per-release `pos-release.yml` manifest with sha256 per file, per-component schema versions, declared breaking changes, ordered migrations.
- **External CLI pattern:** `pos upgrade <tag>` runs from a staging directory; never from inside the running orchestrator's path.
- **Rollback atomicity: whole-upgrade atomic.** Partial acceptance rejected on first-principles; components are coupled.
- **Self-referential case:** orchestrator is NOT unsealed; existing SIGTERM + graceful shutdown + `launchctl kickstart` on new path is the whole sequence.
- **Conflict-report schema structurally forbids `skipped`.** No silent-skip path can exist at the schema level, not merely at runtime.
- **Framework owns the observability-aggregator probe set** internally — it runs deterministic DuckDB queries whose results round-trip across the upgrade.
- **Failed-rollback test discipline: prototype-only.** Manual destructive-test runbook, not a CI harness.
- **User notification: YES.** Primary persona notifies via one-on-one channel before upgrade starts and again on success/rollback.
- **Auto vs confirmation: workspace-configurable.** `auto_update_mode` key in `~/.pos/upgrade-config.yaml`; values `require_confirmation` (default for v1) or `notify_and_apply` (with 60 s cancel window). Orientation integration tracked on BACKLOG.

---

## Deliverables

Ten deliverables D1–D10 as named in the proposal. Objective-level acceptance; no prescribed module names, class hierarchies, file layout, or function signatures beyond the API surface sketched in the proposal.

### D1. Release-tag + manifest format

**Objective:** the framework defines and validates `pos-release.yml`.
**Acceptance:** Pydantic-validated schema; malformed manifests reject with clear errors; roundtrip YAML ↔ Python model; manifest fields include `release_tag`, `commit_sha`, `files` (each with `path`, `expected_pre_sha`, `expected_post_sha`, `change_kind`), `component_schemas` (per-component pre/post versions), `breaking_changes` (list with migration path per change), `migrations` (ordered).

### D2. External CLI scaffold

**Objective:** `pos upgrade <tag>` command runs as an external process from a staging directory; supports dry-run + execute.
**Acceptance:**
- CLI parses args; loads manifest; dry-run prints the planned steps without side effects.
- `--execute` flag runs the full sequence.
- CLI reads `~/.pos/upgrade-config.yaml` for `auto_update_mode`; honours it (see D10 for notification-and-decision flow).
- CLI emits a clear error if invoked from inside the live framework path.

### D3. Pre-upgrade snapshot

**Objective:** every sealed component's durable state is snapshotted atomically before upgrade begins.
**Acceptance:**
- File-copy snapshots produced for Kuzu DB (memory), SQLite files (scope-of-work, objective-tracker, orchestrator, graceful-degradation), DuckDB file (observability-aggregator).
- Snapshots captured in a single coordinated pass; no drift between components (verified by a post-snapshot consistency check: pre-snapshot probe hashes equal post-snapshot-probe hashes).
- Stored under `~/.pos/framework/history/<tag>-pre/`.

### D4. Pre-upgrade probe run

**Objective:** the framework collects each sealed component's existing probe surface + runs its own probe set against the aggregator's DuckDB.
**Acceptance:**
- Calls: memory's probe, scope-of-work's `capture_pre_upgrade`, objective-tracker's `capture_pre_upgrade`, orchestrator's `snapshot_probe`, graceful-degradation's `snapshot_probe`, primary-persona's `build_survival_payload`.
- Framework's own aggregator-probe set: a declared collection of deterministic DuckDB queries whose results round-trip across an upgrade.
- All probe results serialised to `pre-probe.json` under the history directory.

### D5. Upgrade execution + orchestrator restart

**Objective:** steps 5–10 of the sequence run correctly; orchestrator gracefully stops, files update, orchestrator restarts.
**Acceptance:**
- `pause_activation("upgrade:<tag>")` halts new scope activations; bounded drain window (default 30 s, tunable).
- SIGTERM delivered; pid exits within bounded timeout.
- Symlink swap is atomic — no reader observes a half-swapped state.
- `launchctl kickstart` starts the new orchestrator; IPC socket rebinds.
- Post-start no-op RPC over the new socket succeeds (used as clause-(a) verification in D6).

### D6. Post-upgrade probe run + clause verification

**Objective:** each clause (a)–(g) has a concrete check; failing check triggers rollback.
**Acceptance:**
- Seven named check functions returning `Passed | Failed(reason)`.
- Results aggregated into `post-probe.json`.
- Clause (a): IPC socket rebind + no-op RPC success.
- Clause (b): `build_survival_payload` returns a five-field payload with all fields populated for every configured persona.
- Clause (c): memory's `upgrade.compare()` returns `DriftReport.passed`.
- Clause (d): scope-of-work's and objective-tracker's `assert_no_drift(threshold=0)` both pass.
- Clause (e): manifest's `breaking_changes` is non-empty for any schema version bump; silent schema bumps halt.
- Clause (f): pre-upgrade snapshots exist at expected paths; a test rollback-and-restore from the snapshots produces the pre-upgrade state (verified in D8).
- Clause (g): sha-verify every file in manifest; mismatches reported with expected vs actual; no `skipped` possible per D7.

### D7. Conflict report + structural clause-(g) enforcement

**Objective:** conflict-report YAML schema exists; `skipped` is not a permitted `resolution` value; upgrade blocks on any `pending` resolution.
**Acceptance:**
- Pydantic schema for the conflict-report YAML; Python enum for `resolution` enumerates: `pending`, `auto-accept-local-matches-upstream`, `accept-upstream`, `keep-local`, `three-way-merge`, `abort`. `skipped` rejected at schema parse.
- Running an upgrade against files with divergent local shas produces a conflict report at `~/.pos/framework/history/<tag>-conflicts.yaml`.
- Upgrade blocks until the user resolves each `pending` to a permitted value via edit-and-retry.
- `abort` cleanly cancels the upgrade — no state change to sealed components.
- Attempting to set `resolution: skipped` in the YAML fails schema validation.

### D8. Rollback — success path + clean-failure path

**Objective:** rollback restores all snapshots, reverts symlink, restarts orchestrator on the prior release tree.
**Acceptance:**
- Success-path test: upgrade succeeds, then user invokes `pos rollback`; all snapshots restored; post-rollback probe round-trips the pre-upgrade probe results.
- Clean-failure-path test: an upgrade with a failing clause check auto-rolls-back; post-rollback probe matches pre-upgrade.
- Failed-rollback path is **not** tested in CI per ruling recorded — documented as prototype-only manual destructive test (D10 runbook).

### D9. Accept path + OTel emission

**Objective:** a successful upgrade writes `accepted.json`, emits `upgrade_accepted` span, clears the pause.
**Acceptance:**
- `accepted.json` under the history directory contains release tag, clause-by-clause verdicts, total duration, file counts.
- OTel span `pos.upgrade.accepted` emitted with attributes for release, duration, clause verdicts.
- `orchestrator.resume_activation()` called; scopes resume per orchestrator's normal semantics.
- A user notification fires on accept via the primary persona's one-on-one channel.

### D10. Bundled documentation + destructive-test runbook + notification flow

**Objective:** v1.1 R4 docs, a manual destructive-test runbook per the prototype-only ruling, and the user-notification flow for both config modes.
**Acceptance:**
- Prose explanation, architecture diagram (CLI + snapshots + orchestrator + clause checks), sequence diagrams (happy path, clean-failure rollback, conflict-reporting flow), conflict-report schema reference, manifest-authoring reference.
- Destructive-test runbook: a human-executable script that corrupts a snapshot mid-rollback, verifies the framework halts safely with a recovery-instructions report rather than crashing silently. Not a CI test.
- Notification flow implementation:
    - `require_confirmation` mode: primary persona sends a notification "Upgrade <tag> available — reply 'yes' to proceed or 'no' to skip." Framework waits for response via the one-on-one IPC channel; timeout defaults to 24 h, then marks the upgrade as deferred.
    - `notify_and_apply` mode: primary persona sends "Upgrading to <tag> in 60 s — reply 'cancel' to abort." Framework proceeds after the window unless cancelled.
    - On success or rollback: primary persona sends a completion notification with clause verdicts summarised.
- Relationship map: depends on all seven sealed components; consumed by nothing. Self-upgrade is a root operation.
- One-page CLI reference.

---

## Dependencies

### Hard dependencies (no amendments)

- All seven sealed components via their existing probe/snapshot/compare surfaces.
- launchctl (macOS) / systemd-user (Linux) — present from orchestrator build.

### Soft dependencies

- Future first-run orientation component (when built) writes `auto_update_mode` to `~/.pos/upgrade-config.yaml`. Integration tracked on BACKLOG — not blocking.

### Permitted runtime dependencies

As enumerated in hard constraints. No additional libraries anticipated. Anything else halt-and-signal.

---

## Halt conditions

Halt and return with a named failure signal if:

- Any hard constraint cannot be honoured.
- A spec acceptance criterion becomes unsatisfiable under the approved direction.
- Any sealed-component amendment appears genuinely required — do not modify silently.
- An additional runtime dependency appears necessary — surface; do not add.
- IPC-client reconnect behaviour can't be verified from the framework's position (clause a) — surface with diagnosis of which client is at fault.
- Bounded drain window of 30 s is measurably insufficient on realistic workload — surface with measurement.
- Symlink-swap primitive reveals a cross-platform concern on the target filesystem — surface.
- Any ambiguity requiring an invented constraint not in owner's words.

---

## Return format

On completion, return a summary (≤700 words):

1. Which deliverables D1–D10 completed, which halted.
2. Which spec criteria now pass (cite v1.0 behaviour or v1.1 revision, specifically each of (a)–(g)).
3. Confirmation that all seven sealed components' tests still pass at baseline.
4. Framework test counts.
5. Measured bounded-drain timing + symlink-swap timing on the test machine.
6. Complexity outcome (research said 450–650 AI-min; calibrated 45–65 min wall-clock).
7. Commits on `pos-v2`.
8. Any halt signals raised.
9. Confirmation the destructive-test runbook exists + that it has been executed manually once to verify the happy-path of the runbook itself (not the destructive case it verifies).
10. Recommended next action (expected: declare self-upgrade-framework complete; seal closes Phase 2).

---

## What this brief is NOT

- Not a specification of module names, class hierarchies, file layout, or function signatures beyond the API surface the proposal has sketched.
- Not a step-by-step execution plan.
- Not a commitment to designing the first-run orientation component (a future primary-persona-layer concern).
- Not a failed-rollback CI test harness.

---

## inferences recorded in this brief (flagged so the builder can challenge)

Three items come from the primary persona's interpretation rather than the owner's verbatim words:

- *24-hour timeout on `require_confirmation` before marking the upgrade as deferred.* the owner didn't specify; inference recorded from "user might be away a while" — matches the rebuild's ADHD-friendly silence-by-choice posture. Workspace-tunable. If the builder finds a cleaner default, halt and flag.
- *60-second cancel window in `notify_and_apply` mode.* inference recorded for "brief grace period." Short enough that the user doesn't feel interrupted, long enough that a "wait, no, don't" response lands. Tunable. If the builder finds a better default, halt and flag.
- *IPC client reconnect behaviour verified via a no-op RPC post-restart.* feedback recorded clause (a) is "active session continues"; the primary persona's operationalisation is the RPC succeeds. If the builder finds a richer check is needed (e.g. confirming the session's in-flight context is preserved across the reconnect), halt and flag.
