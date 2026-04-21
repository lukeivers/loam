# Research — Self-Upgrade Framework

**Component:** Self-Upgrade Framework — the coordinator that wraps each sealed component's per-component R1 harness in a system-wide upgrade operation and enforces the seven-clause acceptance (v1.1 R1 clauses a–g).
**Status:** DRAFT — research only. Produces no code, no proposal.
**Authored by:** research agent (dispatched by the primary persona). **Date:** 2026-04-19.
**Inputs read:** research-plan.md, objectives spec v1.0 + v1.1 + v1.2 addenda, the eight sealed components on `pos-v2`, STATE.md, `bin/upgrade-pos` (anti-pattern only).

---

## 0. Pre-work halt signals raised

Two items surfaced during the read-through that must be decided by the owner before the proposal is authored. Neither blocks research; both shape the proposal's scope.

1. **Observability-aggregator has no `snapshot_probe()` surface in `src/`.** The research plan claims it has "its own R1 round-trip test"; a search of `observability-aggregator/src/` and `tests/` shows no `snapshot` or `probe` or `round_trip` function. The aggregator's querable surface (`QueryAPI.find_spans`, `cost_by_prompt`, `audit_search`, `get_trace`, `get_span`) is sufficient to *build* a probe set externally, but the framework then owns the probe-set definition for this component — every other sealed component owns its own. This is a non-amendment route (aggregator's surfaces are not extended), but it does place a per-aggregator probe set inside the framework repo. Flagged for decision recorded: accept the asymmetry, or ask for a small `snapshot_probe()` addition to the aggregator (would require unsealing).

2. **Plan claims "eight sealed components" but STATE.md names seven sealed plus four Phase 1 primitives.** Counting from STATE.md: memory-system, scope-of-work, primary-persona, objective-tracker, orchestrator, graceful-degradation, observability-aggregator = 7 sealed. The plan's "eight" most likely counts the three primary-persona sub-deliverables (loader, monitor, autonomous authoring) or treats the Phase 1 primitives as a single bundle. No functional consequence — the framework consumes each component's surfaces regardless of numerology — but flagged so the proposal count is unambiguous.

Neither is blocking. Both are surfaced now so the subsequent proposal authoring has clean ground to stand on.

---

## 1. Survey of existing patterns

This survey is for design precedent only. Several patterns are explicitly rejected below as misfits for pOS's shape (single-user, file-plus-schema, Python-native, self-referential-orchestrator constraint). The survey is useful because clause (g) — "no silent skip" — is widely violated in this class of tool; seeing how each incumbent fails the clause is informative.

### 1.1 Django migrations

- **Upgrade unit:** a migration file per app, numbered, referenced by dependency graph. Forward `operations` + a `reverse_code` or `reverse_sql` per operation.
- **Atomicity:** each migration runs in a transaction on backends that support DDL-transactional (PostgreSQL yes, MySQL no). A *group* of migrations across apps is not atomic — a partial failure leaves a half-migrated database.
- **Rollback:** `migrate app_name 0001` moves to that revision if every intervening migration has valid reverse logic. Data migrations require manual `reverse_code`. DROP operations are effectively irreversible on most backends.
- **Relevant to pOS:** the "dependency graph across apps + per-migration atomicity" shape is roughly what pOS wants per-component, but Django's cross-app non-atomicity is exactly the failure mode clause (f) rejects. *Do not carry over the cross-migration gap.*

### 1.2 Alembic

- **Upgrade unit:** a revision file per change, linear or branching history, `upgrade()` + `downgrade()` functions.
- **Version bookkeeping:** `alembic_version` table in the target database — the version is stored on the substrate being migrated, not alongside the migration files. Offline mode (`--sql`) emits SQL without touching the DB.
- **Rollback:** `downgrade -1` if `downgrade()` is implemented. No built-in rollback for failures during `upgrade()` — the maintainer's issue tracker has an open proposal for it.
- **Relevant to pOS:** the "version lives on the substrate" principle matters. pOS-v2 components already implement `_SCHEMA_VERSION` per SQLite store; the framework should require a matching version alongside its manifest. *Carry over: schema version lives with the data, not with the code.*

### 1.3 Flyway

- **Upgrade unit:** versioned migration files with a name + version + checksum, plus "repeatable" migrations applied whenever their checksum changes.
- **Checksum verification is the key discipline:** Flyway hashes every applied migration and stores the hash in `flyway_schema_history`. If an already-applied migration file is edited post-hoc, checksum mismatch halts execution. This is the *anti-silent-skip* mechanism of the class. The database's record of "what was applied" is compared against what the file now says; disagreement is a hard failure, not a skip.
- **Baseline:** for brownfield databases, `baseline` marks a point below which Flyway will not attempt to run migrations.
- **Relevant to pOS:** the checksum-store-and-compare pattern is directly applicable to clause (g). The framework records, per file, what was expected; post-upgrade it diffs expectation vs reality; any mismatch is surfaced, never swallowed. *Carry over: manifest-checksum-post-diff is the operational shape of clause-g enforcement.*

### 1.4 Homebrew self-upgrade

- **Upgrade unit:** git fetch + merge against the Homebrew repo plus the user's taps.
- **User modifications:** `brew update` attempts to merge the user's changes into the upstream — but if the user has edited a core formula, `HOMEBREW_NO_INSTALL_FROM_API=1` is required or the user's edits are silently ignored. `brew update-reset` exists explicitly because users regularly end up in a state where their tree is stuck.
- **Relevant to pOS:** the Homebrew failure mode — user-edits-silently-dropped — is *precisely the clause (g) anti-pattern* named in the spec. Homebrew papers over it with `update-reset` (blow away user edits) and docs. pOS rejects both responses: user edits are either respected explicitly (conflict surfaced), or replaced explicitly (user chose), never dropped. *Do not carry over: Homebrew's laissez-faire merge behaviour.*

### 1.5 Ollama upgrade

- **Upgrade unit:** downloaded binary + model updates via `ollama pull`.
- **Mechanism:** on macOS/Windows, auto-download-to-local then "Restart to update" applies the new binary. Models are separate — `ollama pull <model>` diffs the local blob vs registry and fetches deltas.
- **Relevant to pOS:** the clean "binary download + explicit restart to apply" shape is applicable to the *self-referential orchestrator-upgrade* case specifically — stage new files, then restart. Not a general model for pOS because Ollama doesn't deal with user-modified framework files or semantic-state preservation across upgrade. *Carry over: stage-then-restart for the orchestrator.*

### 1.6 Cargo / rustup self-update

- **Mechanism:** `rustup self update` replaces the rustup binary itself; `auto-self-update = enable` makes it implicit.
- **Rollback:** no built-in rollback of `cargo update`; workaround is "keep `Cargo.lock` in VCS and revert." This is the pattern of "version control is the rollback" and it is robust because git is the substrate.
- **Relevant to pOS:** the "git is the rollback substrate" pattern is applicable. The framework's upgrade-unit should be a git commit (or tag); rollback is `git checkout` to the prior commit of the *framework tree*. What git cannot roll back is the component *databases* — SQLite and DuckDB files — which is why each sealed component also exposes a file snapshot as well as a semantic probe. *Carry over: git for code, file snapshots for data.*

### 1.7 Git-based atomic-symlink deploys

- **Upgrade unit:** a full release checkout in `releases/TIMESTAMP/`; a `current` symlink pointing at the live release.
- **Atomicity:** the symlink swap is a single filesystem operation (`rename(2)` via `ln -sfn`), which is atomic on POSIX. Everything runs against `current/`; the swap is the go/no-go moment.
- **Rollback:** re-point the symlink at the previous `releases/TIMESTAMP/`. Old releases are retained (typically N=5).
- **Relevant to pOS:** this is the *strongest* precedent for pOS's shape. The framework tree can live in `~/.pos/framework/current` as a symlink to `~/.pos/framework/releases/<commit-sha>/`. The pre-upgrade snapshot preserves the *data* stores; the *code* side is handled by keeping the prior release on disk and re-pointing the symlink. This gives byte-for-byte code rollback with no git operation in the rollback path. *Carry over as the structural shape.*

### 1.8 Kubernetes rolling update + rollback

- **Upgrade unit:** a new `Deployment` revision; replicas are replaced incrementally; `kubectl rollout undo` reverts to the previous revision.
- **Rollback:** versioned revisions are retained; `--to-revision=N` is explicit.
- **Pre-upgrade hooks:** not first-class in stock Kubernetes — Helm has `pre-upgrade` / `post-upgrade` hooks as chart annotations.
- **Relevant to pOS:** the *revision as a first-class versioned object* and *explicit rollout-undo* discipline transfers. pOS is single-process, not replicated, so the rolling-replacement aspect does not. *Carry over: explicit revision identity and named rollback command.*

### 1.9 Summary of what transfers

| Pattern | Carry over to pOS | Reject |
|---------|-------------------|--------|
| Django | per-unit atomicity (yes) | cross-unit non-atomicity (no) |
| Alembic | version-lives-on-substrate (yes) | in-process downgrade-only (no) |
| Flyway | manifest-checksum-post-diff (yes) | shared-DB-write-quorum (n/a) |
| Homebrew | — | silent-merge-on-user-edit (no — this is the anti-pattern) |
| Ollama | stage-then-restart for orchestrator (yes) | blind-binary-replace (no) |
| Cargo / rustup | git as rollback substrate (yes) | no-rollback acceptance (no) |
| Atomic-symlink deploys | symlink-swap release directory (yes — structural shape) | — |
| Kubernetes / Helm | named revisions + explicit `rollout undo` (yes); pre- and post-upgrade hook points (yes) | rolling-replica model (n/a) |

**Distinguishing thesis.** pOS is a single-user local-first harness with self-referential constraints (the orchestrator can be the subject of its own upgrade). No incumbent solves this exactly. The closest operational shape is atomic-symlink deploy + Flyway-style checksum verification + Kubernetes-style named revisions + component-level semantic round-trip probes. These combine into the design shape below.

---

## 2. Recommended design shape

Eight question groups from the plan. For each: options considered, recommendation, rationale.

### 2.1 What counts as a "framework upgrade"

**Options:**
- (a) A git commit on `pos-v2` — precise, but git commits on the same repo include code churn unrelated to a pOS release (test-only changes, doc updates). No natural stopping point.
- (b) A release tag — `pos-v2-vX.Y.Z` — named, countable, attached to a tree state, manifest-friendly.
- (c) A manifest listing files-to-update + migrations — declarative, portable, but duplicates state that git already carries.

**Recommended: (b) release tag, backed by a git commit sha, with a per-release *manifest* generated from the tagged tree.**

The manifest is derived — not hand-authored — from a `pos-release.yml` file checked into the repo root at tag time. Content:

- `release_version` — semver (`0.5.0`, `1.0.0-rc.1`)
- `commit_sha` — the tagged commit
- `components` — per-component:
  - `name`, `schema_version` (if any), `entry_path`, `file_manifest` (relative paths + sha256)
  - `breaking_changes: []` — explicit; empty list means "no breaking changes declared"
  - `migrations: []` — ordered list of migration scripts to run (see §2.3)
- `framework_files` — files outside any component (e.g. `bin/pos`, `~/.pos/bootstrap.py.example`, CLI entrypoints) with sha256
- `generated_at` — UTC ISO-8601

**Rationale.**
- Tags are the natural naming unit for a release and survive git-archive / tarball download. The manifest makes the clause-g post-diff possible without re-running git.
- Per-file sha256 in the manifest is the clause-g substrate: "is this file installed as expected?" becomes `sha256(installed_file) == manifest.expected_sha256`. Any deviation is a conflict (or a bug), never a skip.
- Version numbering is single-framework-semver with per-component schema-versions embedded. Rationale: the user sees one number ("pOS v1.2.3"); internally, each component's SQLite `_SCHEMA_VERSION` still governs its own migrations.

### 2.2 Framework vs workspace scope

**Recommendation: a strict three-tier classification in the manifest.**

| Tier | Owner | Example paths | Upgrade behaviour |
|------|-------|---------------|-------------------|
| **Framework** | pOS release | `framework/memory_system/`, `framework/orchestrator/`, `bin/pos` | Replaced on upgrade; subject to clause-g checksum verification |
| **Workspace-local config** | Workspace | `~/.pos/bootstrap.py`, `~/.pos/stack.yml`, `~/.pos/personas/` | Never touched by the framework upgrade. Read by components at runtime |
| **Component data** | Component at runtime | `~/.pos/scope_of_work.sqlite`, `~/.pos/memory/*.kuzu`, `~/.pos/orchestrator.sqlite`, `~/.pos/aggregator.duckdb`, `~/.pos/degradation.sqlite` | Never touched directly by upgrade. Snapshotted pre-upgrade; migrated via the component's own migration scripts; restored from snapshot on rollback |

Boundary rule: any path under `~/.pos/` that is *not* workspace-local config and *not* component data is a bug. The framework never writes to `~/.pos/` at upgrade time; the framework writes to `~/.pos/framework/` and toggles a symlink.

**Clause (b–d) mapping:** personas (tier 2) and memory entries (tier 3) are untouched by the code side of the upgrade. Clause (b) becomes "the new loader loads the unchanged tier-2 persona content and passes compaction-survival"; clause (c) becomes "the new memory module reads the unchanged tier-3 Kuzu DB and the semantic round-trip passes"; clause (d) becomes "the new scope-of-work projects the unchanged tier-3 event log and the capture/replay drift is within threshold."

### 2.3 Upgrade execution

**Options:**
- (a) Shell out to `git checkout` at a named commit + run migrations. Simple; requires git at runtime; commingles code delivery with data migration.
- (b) Explicit migration-file-based system, Alembic/Django-style. Heavy; pOS components already each own their schema-version logic; duplicating it centrally is redundant.
- (c) Declarative manifest + atomic symlink swap + per-component migration dispatch. Keeps git out of the runtime path; makes the clause-g post-diff trivial; matches the sealed components' existing shape.

**Recommended: (c).**

Execution sequence (sketch; the proposal will tighten):

1. **Fetch.** Download the release tarball for the target tag to `~/.pos/framework/staging/<tag>/`. Compare tarball sha256 against manifest-declared sha. Halt if mismatch.
2. **Pre-upgrade snapshots.** Each component's `snapshot_probe()` captures a semantic snapshot (dict); each component's substrate file is byte-copied to `~/.pos/framework/snapshots/<tag>/<component>/`. The snapshot directory is the rollback boundary.
3. **Pre-upgrade probe.** Each component's R1 harness captures its probe set against the current (pre-upgrade) module. Results stored to `~/.pos/framework/snapshots/<tag>/probes/<component>.json`.
4. **Activation pause.** Framework calls `orchestrator.pause_activation("upgrade:<tag>")`. Graceful-degradation is informed via a dedicated upgrade-tag attribute (so it does not treat the pause as a Claude-outage degradation episode — see §6.3).
5. **Migrations.** For each component declaring migrations in the manifest, run them in declared order. Each migration is a python callable `migrate(pre_db, post_db) -> None` with a declared `from_schema_version` → `to_schema_version`. Per-component-atomic: a migration that raises rolls back its component's substrate from the snapshot before proceeding to the halt path (§2.5).
6. **Symlink swap.** `~/.pos/framework/current` → `~/.pos/framework/staging/<tag>/` via `os.replace` for atomicity. This is the go-point.
7. **Orchestrator restart.** See §2.5 for the self-referential sequence.
8. **Post-upgrade probe.** Each component's R1 harness replays against the now-upgraded module. The framework collects the drift report from each component and composes a system-wide `UpgradeReport` (see §5).
9. **Clause-by-clause enforcement.** See §3 for the per-clause map.
10. **Accept or rollback.** If every clause passes, the snapshot directory is retained (default N=5 releases) and the report is written to `~/.pos/framework/history/<tag>.json`. If any clause fails, trigger rollback (§4).

**Per-component migration handling.** Each component that has a `_SCHEMA_VERSION` declares its migrations under `framework/<component>/migrations/<from_v>_to_<to_v>.py`. The framework runs them — it does not write them. This keeps migration authorship with the component's domain expertise (scope-of-work knows its own event log best).

### 2.4 Schema migrations

- SQLite stores (`orchestrator.sqlite`, `scope_of_work.sqlite`, `objective_tracker.sqlite`, `degradation.sqlite`): framework invokes `python -m <component>.migrations.apply --from N --to M` which uses the component's registered migrators. Each migrator opens the SQLite file, runs DDL + data moves inside a single transaction, and exits 0 on success.
- DuckDB store (`aggregator.duckdb`): same pattern; DuckDB supports transactional DDL for its core SQL.
- Kuzu store (memory): Kuzu's schema changes are less transactional; the pre-upgrade substrate snapshot *is* the rollback mechanism. If a Kuzu migration fails partway, the substrate is restored from the file-copy snapshot. The semantic probe then runs against the restored (pre-upgrade) module to confirm recovery.

No framework-wide migration system is introduced; the framework orchestrates per-component migrations.

### 2.5 Orchestrator self-referential upgrade

This is the hardest question in the brief. Recommendation below; subject to a prototype validation per §10.

**Constraint.** The orchestrator is a long-lived asyncio process supervised by launchd (macOS) or systemd (Linux). It cannot upgrade itself in-place (Python import caches, event-loop state, open file handles to `~/.pos/orchestrator.sqlite`). An external supervisor — or a standalone upgrade CLI — must be the agent of the replacement.

**Recommended sequence (orchestrator-upgrade case):**

1. The user (or a scheduled task) runs `pos upgrade <tag>` from a terminal session — outside the orchestrator process.
2. The CLI does steps 1–5 of §2.3 while the orchestrator is still running. `pause_activation` is the handshake: the orchestrator now refuses new `activate_scope` calls and emits a `pause_activation` local event with `reason="upgrade:<tag>"`.
3. The CLI waits for in-flight scopes to settle — a bounded drain window (default 30s; configurable). If scopes do not settle, the framework halts with `upgrade:drain_timeout` and rolls back (§4). No force-kill of in-flight work at this layer.
4. The CLI calls `orchestrator.prepare_for_replacement()` — *this method does not exist today and is the candidate addition that, per constraint 2, requires halt-and-surface.* See the halt signal in §0 extension below.
   - **Alternative** that avoids extending the orchestrator surface: the CLI sends SIGTERM directly. The existing orchestrator already implements graceful shutdown on SIGTERM (see `orchestrator.py` signal handling). The CLI waits for the pid to exit.
5. Once the orchestrator has exited, the CLI performs the symlink swap (step 6 of §2.3).
6. The CLI re-loads the launchd/systemd unit — or, on macOS, issues `launchctl kickstart` — and waits for the orchestrator to come up against the new tree. Wait timeout: 60s; beyond, upgrade halts and rolls back.
7. Once the orchestrator is up, the CLI connects to the new Unix-domain socket and runs the post-upgrade probe (step 8 of §2.3).
8. The orchestrator's own `upgrade_probe` local event — which already exists in `local_state.py` — is appended pre and post; the framework reads both to include the probe in the drift report.

**Halt signal (from §0).** Step 4 above can use either a new method (`prepare_for_replacement`) or SIGTERM + graceful shutdown. Recommendation: prefer SIGTERM (no surface change); the orchestrator already supports it. Method-add is not needed. *Keeps the orchestrator sealed.*

**Self-referential subtlety.** The CLI is itself shipped from the framework tree. On an orchestrator-upgrade, should the CLI be the new version or the old? Recommendation: *the CLI invoked by the user is the new version* (it has been unpacked into the staging directory). This is consistent with atomic-symlink-deploy practice: new code runs the switch; old code does nothing during the switch. The user invokes `pos upgrade <tag>` from their shell — which path `pos` resolves to is the detail. Options:
- (a) `pos` is a shim that always delegates to `~/.pos/framework/staging/<tag>/bin/pos` if present.
- (b) `pos upgrade` is explicitly "download, verify, then re-invoke `~/.pos/framework/staging/<tag>/bin/pos --stage-2 <tag>` which continues from step 4."

(b) is the safer pattern. The shell command fetches + verifies; the re-invoke runs the swap. If the fetch fails, no change has occurred.

### 2.6 Pre-upgrade readiness and probe set

The "declared probe set" is per-component. The framework collects them:

| Component | Probe surface | File |
|-----------|---------------|------|
| memory-system | `run_probe_set(memory, probe_set)` → drift report | `memory-system/src/upgrade.py` |
| scope-of-work | `capture_pre_upgrade(store)` / `replay_post_upgrade(store, captured)` → drift report | `scope-of-work/src/upgrade.py` |
| objective-tracker | `capture_pre_upgrade(store)` / `replay_post_upgrade(store, captured)` → drift report | `objective-tracker/src/upgrade.py` |
| orchestrator | `local_state.snapshot_probe()` → dict; pre/post compared | `orchestrator/src/local_state.py` |
| graceful-degradation | `state.snapshot_probe()` → dict; pre/post compared | `graceful-degradation/src/state.py` |
| primary-persona | `build_survival_payload` → five-item survival list | `primary-persona/src/compaction.py` |
| observability-aggregator | **probe set defined by framework** (see §0 halt signal 1) | framework/ |

The framework's orchestrator of probes is a thin wrapper: it calls each surface, serialises results, and composes a system-wide `UpgradeReport`. No amendments to any sealed component surface are required *except* the aggregator — see §0. Recommendation in §0: framework carries the aggregator probe; no amendment.

### 2.7 User-facing experience

**Channel.** Primary persona notifies via the user's one-on-one channel (inherits v1.1 R13 + v1.2 R15 one-on-one restriction). Not group chats. The framework itself is persona-less (per rule 7); notification goes through the persona layer's notification surface, which is persona content, which is workspace. The framework emits OTel spans; the workspace-configured persona subscribes and speaks to the user.

**CLI surface.** `pos upgrade <tag>` is the entry. The CLI streams a progress line per stage (fetch → snapshot → pre-probe → pause → migrate → swap → restart → post-probe → verify). The final output is either "upgrade accepted, vX.Y.Z" or "upgrade rejected, reverted to vA.B.C" with the drift report path.

**Estimated duration.** Informed estimate from the sealed components' shapes:
- fetch: 2–10s (tarball size est. <5 MB)
- snapshots: 1–3s (SQLite files are small; Kuzu snapshot dominant — ~1 GB at realistic volume projects to 5–20s on SSD)
- pre-probe: dominated by memory's probe set; existing harness runs in seconds at realistic probe counts
- pause + drain: up to 30s
- migrations: 0–60s depending on the release; typically seconds
- swap: <1s
- restart: 5–15s (orchestrator boot)
- post-probe: same as pre-probe
- verify: <5s

Total estimate: 45–150s for a no-migration release; 2–5 minutes with Kuzu-scale snapshot + migrations. These are projections; the prototype priority in §10 is measuring them.

**Worst-case failure experience.** If rollback succeeds, the user sees "upgrade rejected; previous version restored; drift report at <path>". If rollback itself fails (substrate write errors, disk full, symlink cannot revert), the framework surfaces a **Tier 1 restore-failure notification** through the persona's one-on-one channel, logs full state to `~/.pos/framework/history/<tag>-restore-failed.json`, and leaves the CLI in an explicit failed state. There is no auto-retry of rollback. The user is told what to do: either re-run `pos upgrade --resume-rollback <tag>` (framework operation), or contact support (manual). The goal: never claim success when rollback did not complete.

### 2.8 Integration with adjacent components

Per the plan's §8:

- **Orchestrator.** Uses existing `pause_activation("upgrade:<tag>")` + `resume_activation()`. Upgrade framework is the *caller*, not the author of those hooks. Self-referential case handled per §2.5.
- **Graceful-degradation.** The pause reason string carries the `upgrade:<tag>` prefix. Graceful-degradation's detection layer must treat `upgrade:*` reasons as non-Claude-outage; otherwise it would open a false-positive degradation episode. Recommendation: degradation subscribes to OTel emissions from the framework (`pos.upgrade.started`, `pos.upgrade.accepted`, `pos.upgrade.rolled_back`) via the aggregator, and the FSM treats these as an active upgrade window during which detection is suppressed. No amendment to the sealed component; the span attribute is observed.
- **Observability aggregator.** The framework emits OTel spans: `pos.upgrade.started`, `pos.upgrade.pre_probe_complete`, `pos.upgrade.migration.<component>`, `pos.upgrade.swap`, `pos.upgrade.orchestrator_restarted`, `pos.upgrade.post_probe_complete`, `pos.upgrade.accepted` or `pos.upgrade.rolled_back`. Span attributes include `tag`, `commit_sha`, `drift_score` (post-probe).
- **Primary-persona layer.** Post-restart, the primary persona's compaction-survival runs; the framework reads the `build_survival_payload` output and confirms the five-item list is intact. Clause (b) verification.

---

## 3. Clause-by-clause enforcement map (a–g)

Each clause has a named mechanism, substrate, and a test that the proposal will codify.

### Clause (a) — "any active session continues without restart or re-authentication"

- **Mechanism.** An active session is a terminal/Claude-desktop/Telegram attachment to the orchestrator's IPC socket or the primary persona's channel. Two sub-cases:
  1. Orchestrator-only upgrade (orchestrator code replaced): the Unix socket path is preserved; the new orchestrator binds the same path on start; IPC clients reconnect and the caller does not see a re-auth prompt. *Sessions using persistent IPC with reconnect-on-error satisfy this.*
  2. Non-orchestrator upgrade (e.g. memory or degradation code only): no restart required; sessions unaffected.
- **Substrate.** The IPC server's bind-on-existing-path behaviour (documented in the orchestrator's `IPCServer.start`). Credentials are filesystem-permission-bound (owner-only socket), not token-based — there is no "re-authentication" to fail.
- **Enforcement.** Post-upgrade, the framework opens a new IPC client to the socket and calls a no-op RPC. Success = clause (a) passes. For non-orchestrator upgrades, the framework verifies the orchestrator pid is unchanged (it was never restarted).

### Clause (b) — "all personas load unchanged and pass their compaction-survival checks"

- **Mechanism.** Personas are tier-2 (workspace-local content). The framework does not modify them; the primary-persona loader is tier-1 (framework code) and is the subject of the upgrade. Post-upgrade, the new loader is invoked against the unchanged persona directories.
- **Substrate.** `primary-persona/src/loader.py` + `compaction.py`. The framework calls `load_all_personas(workspace_dir)` and, for each loaded persona, invokes `build_survival_payload` with a mocked runtime + memory provider.
- **Enforcement.** Every persona that was addressable pre-upgrade must produce a non-empty `CompactionSurvivor` post-upgrade. All five fields of `SURVIVAL_LIST` must be populated (per `compaction.py`). Any persona that fails to load surfaces as a clause-b failure with the persona handle named.

### Clause (c) — "memory semantic round-trip equivalence; drift below threshold"

- **Mechanism.** Memory's existing R1 harness (`memory-system/src/upgrade.py`): probe set runs pre and post; `compare()` emits a `DriftReport`; `passed` boolean gates the clause.
- **Substrate.** The Kuzu DB is physically snapshotted pre-upgrade; the probe set is declared in `./data/test_set.json` (workspace path, configurable).
- **Enforcement.** `DriftReport.passed` must be `True`. The threshold (`max_drift_fraction` default 0.10, `per_query_recall_tolerance` default 0.15) comes from memory's config. The framework reads the threshold, does not override it.

### Clause (d) — "all in-flight tasks preserved with correct state"

- **Mechanism.** Scope-of-work's existing capture/replay harness (`scope-of-work/src/upgrade.py`): `capture_pre_upgrade(store)` produces a `CapturedProbeSet` of projection states; `replay_post_upgrade(store, captured)` produces a `DriftReport`. Objective-tracker has the identical pattern.
- **Substrate.** SQLite files (scope_of_work.sqlite, objective_tracker.sqlite). Event-sourced — the event log is the source of truth; projection drift is the detection mechanism.
- **Enforcement.** `assert_no_drift(report, threshold=0)` for both scope-of-work and objective-tracker. Zero-drift threshold by default; the framework will not relax it — any divergence in scope projections is a clause-d failure.

### Clause (e) — "breaking contract changes surface explicitly with a named migration path"

- **Mechanism.** Manifest-declared `breaking_changes`. Every element of the list names: the contract that changed, the pre-upgrade version, the post-upgrade version, and the migration path the user must take.
- **Substrate.** `pos-release.yml` in the tagged tree.
- **Enforcement.** The framework compares, per component, `schema_version` before vs after. If the post-version is higher than the pre-version, the manifest must declare a corresponding `breaking_changes` entry. Silent schema-version increment = clause-e failure, upgrade halts at step 5.
- **User surface.** The list is presented at the top of the upgrade CLI output, before the confirmation prompt (when interactive) or logged at the start of the run (when scheduled). A release declaring breaking changes in `breaking_changes` requires an explicit `--i-read-the-breaking-changes` flag when non-interactive, to prevent autopilot acceptance of breaking releases.

### Clause (f) — "upgrade is reversible; previous framework version can be restored from a preserved snapshot"

- **Mechanism.** Three substrates are preserved pre-upgrade and rolled back on failure:
  1. Framework tree: the old release directory is kept on disk; the symlink swap is reversible by re-pointing.
  2. Component data: each component's SQLite/DuckDB/Kuzu file is byte-copied to `~/.pos/framework/snapshots/<tag>/<component>/` before migration.
  3. Configuration: tier-2 workspace config is not touched, so there is nothing to restore.
- **Substrate.** Filesystem snapshots in `~/.pos/framework/snapshots/<tag>/`. Retention default N=5 snapshots (atomic-symlink-deploy convention).
- **Enforcement.** The framework has a `pos upgrade --verify-rollback <tag>` mode that runs in CI against a throwaway workspace: apply the upgrade, roll it back, then assert the post-rollback state's semantic round-trip matches the pre-upgrade state. This is test infrastructure, run as part of the release gate; not part of normal upgrade execution.

### Clause (g) — "every pOS change is actually installed; none silently skipped; conflicts surfaced with explicit resolution options"

- **Mechanism — three layers, all deterministic:**
  1. **Pre-install manifest diff.** Before the symlink swap, for every framework file in the manifest, compute `installed_sha256` (if the file already exists at the same relative path under the prior release) and `expected_sha256` (from the manifest). Build the change list. No skip — a file that exists in the new manifest but not in the old is a "create"; one present in the old but absent in the new is a "remove"; one present in both with different sha is an "update".
  2. **Conflict detection against workspace-local overrides.** Tier-1 files are framework-only — the workspace never writes to them. If a user has edited a framework file directly (i.e. modified the `~/.pos/framework/current/` tree, which they should not do but might), the pre-swap check detects `installed_sha != previous_release_sha` — the installed file was hand-edited post-install. This is the *clause-g conflict case*. Response: emit a structured conflict report (§5), halt the upgrade, do not apply any changes. The user chooses per-file: accept the new version (overwrite local edit), keep the local edit (explicitly vendored — moved to a workspace override path), or abort.
  3. **Post-install verification.** After the symlink swap, for every framework file in the manifest, re-compute `sha256(installed_file)` and compare against `expected_sha256`. Any mismatch is a clause-g failure and triggers rollback. This catches write-failures, disk-full-partial-write, and any misconfigured path.
- **Substrate.** The `file_manifest` section of `pos-release.yml`.
- **The no-silent-skip guarantee is structural, not advisory.** Every change is either (i) installed with sha verified, or (ii) reported as a conflict with explicit resolution, or (iii) rolled back. There is no fourth path. The current pOS `bin/upgrade-pos` fails at layer 2 — it prints "SKIP" but drops the change and continues. The new framework *halts* on any conflict; the user must resolve before any change applies.

**Conflict-resolution options the user can pick (per file or as a batch):**
- `accept-upstream` — overwrite the local edit with the new framework version; the local edit is preserved in `~/.pos/framework/overrides/<tag>/<path>` for audit
- `keep-local` — the local edit replaces the framework version in the new release tree; the upgrade is marked as having a workspace override at this path (recorded in the upgrade report so future releases know)
- `three-way-merge` — emit a three-way-diff context (prior release + new release + local) and surface it to the user's primary persona channel; the user resolves and supplies the final file content; the upgrade resumes with the resolved file
- `abort` — cancel the upgrade entirely; no changes applied; no rollback needed

The file-level `keep-local` option is a structural answer to clause-g. Homebrew's silent-merge pattern fails here; pOS requires the user to declare the override, which is then a first-class artifact.

---

## 4. Atomicity and rollback specification

### 4.1 Atomicity boundary

**Whole-upgrade atomic.** The transaction boundary is the full upgrade, not per-clause. If clauses (a)–(f) pass but (g)'s post-install verification fails, the entire upgrade rolls back. Rationale: partial acceptance — e.g. "memory upgraded but orchestrator didn't" — would leave the system in a schema-mismatch state that later clause-c runs might not catch. Atomic-whole is harder to implement but is the only state that is simple to reason about.

Why not per-component atomic? Because components are coupled. Memory references scopes (retention class on a scope's events); scopes reference objectives; objectives reference memory for rationale capture. A half-upgraded system is an undefined state. This is a first-principles decision: either the release is accepted as a whole or rejected as a whole.

### 4.2 Rollback sequence

On any verification failure:

1. **Abort write-in-progress.** If a migration raised, its transaction has already rolled back (SQLite/DuckDB) or its component substrate is restored from file-copy (Kuzu).
2. **Restore framework tree.** Re-point `~/.pos/framework/current` at the prior release directory. Atomic via `os.replace`.
3. **Restore component substrates.** For each component whose substrate was migrated in this upgrade attempt, restore from `~/.pos/framework/snapshots/<tag>/<component>/`. The component-level restore helpers already exist (memory's `restore()`, SQLite file-replace).
4. **Restart orchestrator** if it was restarted during the upgrade. If the upgrade was non-orchestrator and the orchestrator was never stopped, step 4 is a no-op; the `pause_activation` is reversed by a `resume_activation("upgrade:<tag>:rolled_back")`.
5. **Emit roll-back OTel span.** `pos.upgrade.rolled_back` with `tag`, `failed_clause`, `drift_score`, `conflict_report_path`.
6. **Write report.** `~/.pos/framework/history/<tag>-rolled-back.json` with full clause-by-clause status, the conflict report (if clause-g), and the exact state the system is now in.
7. **Notify.** Primary persona via one-on-one channel — "upgrade <tag> rejected; rolled back to <prior-tag>; details at <path>".

### 4.3 Failed rollback

If the rollback itself fails — substrate file cannot be written (disk full, permission change), symlink cannot be re-pointed (inode missing), orchestrator cannot restart against the prior release — the framework is in an undefined state.

- **Detection.** Each rollback step has a success check. First step that fails triggers the failed-rollback path.
- **Response.** Framework writes `~/.pos/framework/history/<tag>-rollback-failed.json` with the exact state: which steps succeeded, which failed, what the current symlink points at, what the current substrate versions are. It then halts. No further automated action.
- **User surface.** Tier 1 notification via primary persona: "UPGRADE FAILED AND ROLLBACK FAILED. SYSTEM IN UNDEFINED STATE. See <path>. Manual recovery required; invoke `pos upgrade --recover --from-snapshot <tag>` with care."
- **Manual recovery.** The `--recover` CLI is a separate entrypoint that does nothing automatically — it prints the state and prompts step-by-step confirmation for each recovery action. Principle: when the automated path has already failed once, the manual path does not pretend to be automatic.

The failed-rollback story is load-bearing because clause (g)'s "no silent skip" plus clause (f)'s "reversible" together imply the framework never claims success it has not verified. Failed rollback does not become "probably OK, restart and hope" — it becomes an explicit halt.

---

## 5. Conflict report format (clause g operationally)

The conflict report is emitted at the pre-swap check when any framework file has diverged from its previous release sha. Format: YAML, human-readable, machine-parseable.

```yaml
# ~/.pos/framework/history/<tag>-conflicts.yaml
upgrade_tag: pos-v2-v1.3.0
prior_tag: pos-v2-v1.2.5
detected_at: 2026-04-19T14:23:11Z
conflicts:
  - path: framework/memory_system/src/upgrade.py
    prior_release_sha256: a1b2c3...
    installed_sha256: d4e5f6...           # different from prior_release — edited locally
    new_release_sha256: 789abc...         # what the new release ships
    change_kind: upstream_modified_and_local_modified
    three_way_diff_path: ~/.pos/framework/snapshots/<tag>/conflicts/framework_memory_system_src_upgrade.py.diff
    resolution: pending
    options:
      - accept-upstream
      - keep-local
      - three-way-merge
      - abort
  - path: framework/orchestrator/src/orchestrator.py
    prior_release_sha256: aaa111...
    installed_sha256: bbb222...            # different from prior — edited locally
    new_release_sha256: bbb222...          # same as local; new release adopted the local edit
    change_kind: local_modified_equals_upstream
    resolution: auto-accept-local-matches-upstream
summary:
  total_framework_files: 412
  unchanged: 398
  will_update_cleanly: 9
  conflicts_requiring_resolution: 1
  auto_resolved: 4
```

**Design principles of the format:**

1. **Every conflict is named.** Silent skips are structurally impossible because the format enumerates every file with `change_kind` and a `resolution`.
2. **`resolution` is never `skipped`.** Every entry is `pending` (awaiting user), `auto-*` (deterministically resolved with a stated rule), `accepted-upstream`, `kept-local`, or `three-way-merged`. The term "skipped" is not a valid `resolution` value. This is enforced by the schema, not a convention.
3. **Auto-resolutions are named.** If the local edit happens to match the new release exactly (the user anticipated the upstream change), `auto-accept-local-matches-upstream` fires and the file is counted as resolved without user intervention. The rule is explicit; the auto-resolution is logged.
4. **Three-way-merge produces a diff file.** When the user picks three-way-merge, the framework writes a unified diff between prior, installed, and new to a resolvable path; the user edits that file to produce the final content; the framework reads it back. This is the only path that involves the user beyond menu-picking a resolution.
5. **Abort is first-class.** `abort` as a resolution cancels the entire upgrade — no changes applied, no rollback needed (the swap hasn't happened yet).

The report is the primary interface between clause (g) and the user. Without it, clause (g) degenerates to a log message; with it, clause (g) is a deterministic gate.

---

## 6. User-experience specification

### 6.1 CLI surface

```
pos upgrade <tag>                   # interactive; prompts on conflicts
pos upgrade <tag> --dry-run         # fetches manifest, shows the plan; no state change
pos upgrade <tag> --auto-resolve    # only runs if no manual resolution required; else halts
pos upgrade <tag> --i-read-the-breaking-changes
                                    # required when the release declares breaking changes
                                    # and the invocation is non-interactive
pos upgrade --status                # current framework version, prior releases, last upgrade log
pos upgrade --rollback <tag>        # restore a preserved snapshot by tag
pos upgrade --verify-rollback <tag> # test-only; applies and rolls back to check integrity
pos upgrade --recover --from-snapshot <tag>
                                    # manual recovery after failed rollback
```

### 6.2 Progress output

Stream per stage. Each stage ends with a one-line verdict: `[ok]` with elapsed ms, or `[halt]` with reason. The output is grep-able by automation; not ANSI-coloured in non-TTY.

```
pos upgrade pos-v2-v1.3.0
  fetch              [ok  184ms]
  manifest verify    [ok   12ms]
  pre-snapshot       [ok  2.4s]
  pre-probe          [ok 11.2s]
  pause-activation   [ok   51ms]
  manifest diff      [ok   92ms]  9 updates, 0 conflicts
  migrations         [ok  0.3s]   2 components
  swap               [ok    2ms]
  orchestrator boot  [ok 12.1s]
  post-probe         [ok 11.8s]
  clause verify      [ok   84ms]  (a)=pass (b)=pass (c)=pass(drift=0.02) (d)=pass (e)=pass (f)=pass (g)=pass
  accept             [ok   34ms]
upgrade accepted: pos-v2-v1.3.0 (total 38.4s)
report: ~/.pos/framework/history/pos-v2-v1.3.0.json
```

### 6.3 Notification via the primary persona

Because the framework ships no personas (rule 7), the framework emits OTel spans; the workspace-configured primary persona subscribes via the observability-aggregator and renders notification to the user. Events rendered:

- `pos.upgrade.started` — persona mentions briefly on the user's one-on-one channel
- `pos.upgrade.accepted` — persona confirms with the new version and the drift summary
- `pos.upgrade.rolled_back` — persona surfaces with the failed clause and the report path
- `pos.upgrade.rollback_failed` — Tier 1, same channel, with the manual-recovery instruction
- `pos.upgrade.conflict_pending` — the conflict report exists; persona surfaces the path and waits for the user to resolve

These events include `pos.upgrade.tag` as a span attribute so the degradation layer can ignore the associated pause (see §2.8).

---

## 7. Dependency map

**Consumed by:** nothing yet. Self-upgrade is a root operation — it has no downstream consumers in the sealed set.

**Depends on (all via existing surfaces; no amendments):**

- memory-system — `upgrade.run_probe_set`, `upgrade.compare`, `upgrade.snapshot`, `upgrade.restore`
- scope-of-work — `upgrade.capture_pre_upgrade`, `upgrade.replay_post_upgrade`, `upgrade.assert_no_drift`
- objective-tracker — `upgrade.capture_pre_upgrade`, `upgrade.replay_post_upgrade`, `upgrade.assert_no_drift`
- orchestrator — `LocalStateStore.snapshot_probe`, `Orchestrator.pause_activation`, `Orchestrator.resume_activation`, IPC socket rebind, SIGTERM graceful shutdown; launchd/systemd install helpers under `orchestrator/scripts/`
- graceful-degradation — `DegradationStore.snapshot_probe`, the FSM's treatment of `upgrade:*` pause reasons as non-outage (verification: the FSM inspects the pause reason attribute; this is an existing read-side surface)
- primary-persona — `loader.load_all_personas`, `compaction.build_survival_payload`, `compaction.SURVIVAL_LIST`
- observability-aggregator — `QueryAPI.find_spans`, `QueryAPI.get_trace`, `QueryAPI.cost_by_prompt`; plus the framework's own span emission is consumed here

**Permitted runtime dependencies:** stdlib, pydantic, pyee, opentelemetry-api/sdk, PyYAML, duckdb. No new runtime dependency is required; the framework is pure stdlib + PyYAML (manifest) + opentelemetry (span emission) + pydantic (manifest parsing).

**Permitted test dependencies:** pytest, pytest-asyncio (per STATE.md rule 8).

---

## 8. Complexity estimate

**Headline AI-minutes: 450–650.**

Breakdown (AI-time per task-orchestration rule 15):

- Manifest schema (pydantic) + release-tag loader + sha256 verifier: 30–45 min
- Snapshot + restore coordination across 5 substrates: 30–45 min
- Conflict report authoring + structured YAML schema: 30–45 min
- Pre-upgrade / post-upgrade probe orchestration (per-component surface wiring): 60–90 min
- Clause (a)–(g) verification module, one per clause with a named failure reason: 60–90 min
- Orchestrator self-referential sequence (fetch → pause → SIGTERM → swap → launchctl kickstart → reconnect → post-probe): 90–120 min — hardest, prototype-informed
- Rollback + failed-rollback paths: 45–60 min
- CLI surface + progress streaming + OTel emission: 30–45 min
- Tests against the seven-clause enforcement, including a verify-rollback CI mode: 60–90 min
- Documentation bundle (per R4): 30–45 min

**Calibration note (critical).** The plan guided 400–600 AI-min; the above lands 450–650. Research AI-minutes compress to ~5–10× calendar wall-clock: a 450-min estimate is roughly 45–90 min of wall-clock research-equivalent *effort*, but the self-referential orchestrator sequence is the cap — the prototype alone may take 60–90 min of AI work before the final production build converges, and that work is not compressible because the feedback loop includes live launchctl cycles.

**Risks to estimate:**
- Conflict-report three-way-merge user interaction is hard to unit-test; integration tests may require a test harness that simulates user resolution input.
- The orchestrator restart cycle has a non-deterministic duration depending on launchctl's schedule; timeouts may need tuning.
- Kuzu substrate snapshot size at realistic data volume is a prototype unknown — could be seconds, could be minutes.

If the actual build exceeds 650 min without a clear reason, halt-and-surface.

---

## 9. Prototyping priorities

Three questions only a prototype can answer:

1. **Self-referential orchestrator restart timing.** Measure end-to-end: SIGTERM sent → pid exits → symlink swapped → launchctl kickstart → orchestrator accepting IPC again. Target: < 20s. If > 30s, the pause-window timeout must be raised, which affects the user experience. The prototype writes this to `measurement-launchd-upgrade.json` in the orchestrator repo's pattern (`measurement-launchd.json` is the existing precedent).
2. **Kuzu substrate snapshot cost at realistic volume.** Synthesise 100 MB, 500 MB, 1 GB, 5 GB Kuzu DBs (memory system's representative sizes); measure `shutil.copytree` time on a representative SSD. If the 1 GB snapshot exceeds 30s, a different strategy (e.g. hard-link + copy-on-write filesystem feature) may be required.
3. **Conflict-report three-way-merge UX.** A prototype run through the conflict path with three synthetic conflicts: one auto-resolvable, one user-picks-accept-upstream, one three-way-merge. Measure the time-to-resolution and confirm every path produces a structured outcome in the report file. Success criterion: no scenario produces a `resolution: skipped` or missing resolution.

These are the open questions. Everything else in this research can be built deterministically from the sealed components' existing surfaces.

---

## 10. Summary of halt signals (for owner's attention before proposal authoring)

1. **Aggregator has no `snapshot_probe()` surface.** Recommendation: the framework owns the aggregator probe set; no unseal required. the owner to confirm.
2. **Plan says "eight sealed components"; STATE.md names seven.** Clarify the count in the proposal.
3. **`prepare_for_replacement()` on the orchestrator is not needed.** SIGTERM + the existing graceful shutdown handler is sufficient. The self-referential case is serviceable without unsealing the orchestrator.
4. **Failed-rollback path is load-bearing but untestable in CI without destructive test infrastructure.** The proposal must either accept this as prototype-only territory (recommended) or design a failure-injection harness to exercise it.

None of these are blocking. All are in scope for the proposal to answer.

---

*End of research document. Next gate: the owner reviews, approves, and authorises the primary persona to write the proposal.*
