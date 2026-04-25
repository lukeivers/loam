# Sub-plan C — Multi-workspace state-file partition

**Status:** authored 2026-04-25; revised 2026-04-25 to reflect
D-MASTER.2's revision (commit `217477e`) — pos-v2 mirrors Claude
Code's `~/.claude/` (global) + `<workspace>/.claude/` (workspace
override) pattern. Multi-component sealed-component amendment(s).
Spec objective: re-extension under FUTURE_IDEAS Idea 9 (workspace-
identity hazards) — same pattern amendment #28 used for first-run
state.

**Master plan:** `MASTER.md`.

---

## 1. Summary / TLDR

Introduce a workspace-state vs operator-preference partition for
on-disk pos-v2 state, mirroring Claude Code's `~/.claude/` (global) +
`<workspace>/.claude/` (workspace override) pattern (D-MASTER.2 owner
ruling, 2026-04-25).

**Two file classes, two resolution rules:**

| Class | Lives where | Override? |
|-------|-------------|-----------|
| **Workspace state** (objective-tracker DB, orchestrator SQLite, scope-of-work SQLite, first-run.state, first-run.log, persona contract under `<workspace>/personas/`) | `<workspace>/.pos/` only | No global form makes sense; existing `~/.pos/` content for these classes is *ignored* by the new resolver. |
| **Operator preferences** (`memory.yaml`, `cost/`, `safety/`, `degradation-config.yaml`, `reversibility.yaml`, `self-correction.yaml`, `telegram.yaml`, `bootstrap.yaml`, `observability.yaml`, `orchestrator.yaml`, `self-upgrade.yaml`, `workspace_bootstrap_py.yaml`) | `~/.pos/` global default | `<workspace>/.pos/<filename>` overrides if present. |

**Resolution logic:**

- **State files:** always workspace-local; no fallback, no read from
  `~/.pos/`. Remnants in `~/.pos/` from the pre-C era are silently
  ignored by the resolver — no halt, no diagnostic, no operator
  action required.
- **Preference files:** the resolver reads
  `<workspace>/.pos/<filename>` first; if absent, falls back to
  `~/.pos/<filename>`; if absent there too, uses the scaffold's
  bundled default.

**The work decomposes into:**

1. **Resolver introduction** — workspace-bootstrap exposes a
   path-resolver seam that classifies a request as state vs
   preference and applies the correct rule. Adapters that read
   `host.config_dir / <filename>.yaml` route through the resolver.
2. **State-write routing** — the scaffold and the components that
   own runtime state (objective-tracker, orchestrator, scope-of-work,
   memory-staging, hands-off-lifecycle log) write workspace-local
   only. Where today's defaults are `Path.home() / ".pos"`, they
   rotate to the resolver's state-class output (workspace-local).
3. **Preference-write routing** — the scaffold continues to write
   bundled-default preference files at `<workspace>/.pos/<filename>`
   *as workspace overrides*. Existing `~/.pos/<filename>` content is
   read by the resolver as the global default until/unless a
   workspace override is written.
4. **Path-mismatch fix** — `tracker_db_path_for(pos_root)` →
   `tracker_db_path_for(workspace_root)` per FUTURE_IDEAS_DRAFT entry
   "Path-mismatch (#39 ↔ #40) fix direction". Independent of the
   partition but in the same neighbourhood; lands here.
5. **Launchd plist `EnvironmentVariables`** carry workspace-local
   state paths so spawned services see workspace-local locations.

**Migration burden:** zero. Existing `~/.pos/` content for the
canonical install (or any pre-C user) keeps working as global
preference defaults via the new resolver. State-class remnants in
`~/.pos/` are silently ignored — fresh state writes to
`<workspace>/.pos/` going forward; if state was ever read from
`~/.pos/` (e.g., a pre-C tracker DB), it stops being read. Under
amendment #28's `partial_recovery` pattern, missing state files at
`<workspace>/.pos/` are written from scratch on next scaffold.

**End-user impact:** zero — fresh clones never had `~/.pos/`.
**Canonical install impact:** zero operator action required;
preferences continue to load, state begins fresh under `.pos/` on
next scaffold (or is already there for state amendment #28 already
moved, e.g., first-run.state).

---

## 2. Spec-objective placement

This is **multiple sealed-component amendments**; each one names its
own spec objective. The pattern across all of them:

- **workspace-bootstrap** (multi-amendment scope) — re-extension under
  Idea 9 (workspace-identity hazards), continuing the amendment #28 /
  #29 family. Spec objective: existing workspace-bootstrap spec
  v1.0/v1.1 — first-run scaffold lays workspace state. The change
  is "where state lives": workspace-local, with a resolver seam for
  the preference-class fallback.
- **objective-tracker** — `tracker_seed.tracker_db_path_for` signature
  rotates from `pos_root` to `workspace_root`. One line of the seed-API
  surface; the fix is a re-extension of amendment #39 (the seed wrote
  the path-mismatch in the first place — this is its corrective).
- **scope-of-work / orchestrator** — SQLite path resolution for state-
  class storage. Spec objective: existing orchestrator spec v1.x —
  the orchestrator stores state per-workspace; this amendment makes
  the default reflect that.
- **cost-governance / graceful-degradation / safety-layer / reversibility
  / self-correction / memory-system staging / hands-off-lifecycle log**
  — each component's spec already says "state lives at the configured
  path"; the amendment routes the *default* through the resolver
  without changing the contract. Components owning preference-class
  YAML inherit fallback-to-`~/.pos/` automatically.

§2.5 forward+reverse audit per sub-amendment. Amendment titles are
sequential per `pos-amend` convention (master plan D-MASTER.6
recommendation).

---

## 3. Three-lens analysis

### Lens 1 — Claude-leverage

The partition pattern composes on Claude Code's own `~/.claude/` +
`<workspace>/.claude/` precedent — same mental model the user already
holds for Claude Code config. The pos-v2 resolver re-uses the
pattern; nothing new for the user to learn.

What C enables: every Claude-leveraging contributor (sub-plan A's
contract reader, amendment #33's memory-consumer, amendment #40's
tracker-context, future Idea 4/5 personalisation) automatically sees
workspace-local state without surprise, and operator preferences
travel across workspaces without the operator copying files.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation burden
between the user's natural-language intent and AI-effective execution?*

Yes — by removing a translation layer that should never have existed
and by introducing a partition the operator already understands from
Claude Code. Today the persona has to translate "the user is in
workspace A" into "check workspace-A's first-run state at
`<A>/.pos/first-run.state` AND the tracker DB at
`~/.pos/objective_tracker.sqlite` AND the cost data at
`~/.pos/cost/cost.sqlite` AND…" — the inconsistency is the
translation burden. After C, state lives at `<workspace>/.pos/`,
preferences resolve through the workspace → home chain, and the
persona names one rule.

**Harness test.** *Does this add to the toolkit the primary persona
can draw from?*

Yes — `<workspace>/.pos/` becomes the canonical workspace-local state
location every contributor in the harness composes on. The resolver
itself is a new toolkit primitive: components query it for any
state-or-preference path and get the right answer without re-
implementing the partition rule.

### Lens 3 — ODD authoring

ACs are outcome-shaped per amendment. The amendments serialise behind
each other (per `feedback_serialize_amendment_builds`); each amendment
gets its own `pos-amend` manifest, ACs, and seal commit.

---

## 4. Acceptance criteria (AC.C1–AC.C8, plus per-component ACs in sub-amendments)

### AC.C1 — Path-mismatch (#39 ↔ #40) closes in favour of `workspace_root`

`workspace_bootstrap.adapters.tracker_seed.tracker_db_path_for(workspace_root)`
returns the workspace-local tracker DB path. The function signature
takes `workspace_root`, not `pos_root` (today's name). The two
callers in workspace-bootstrap (the scaffold's `_run_tracker_seed`
call) and in objective-tracker's seed runner are updated to pass
`workspace_root`. The persona-side
`tracker_context.tracker_db_path_for` already takes `workspace_root`
(amendment #40); the two now agree.

**Test shape:** call `tracker_db_path_for(workspace_A)` and
`tracker_db_path_for(workspace_B)`; assert the returned paths are
distinct, both rooted at the supplied workspace. Pre-existing
amendment #39 + #40 tests should not need changes once the signature
is consistent. **HALT TRIGGER:** if amendment #39 or #40 tests need
amendment, surface — re-extension of either needs owner approval.

**Maps to:** AC.PO.1 (translation burden absorbed) + AC.PROG.1 +
AC.PROG.3.

### AC.C2 — workspace-bootstrap scaffold default `config_dir` moves workspace-local

`workspace_bootstrap.manifest.load_manifest`'s `config_dir` default
rotates from `workspace_root / "config"` to `workspace_root / ".pos"`.
Existing manifests that explicitly set `config_dir: ~/.pos/config`
continue to work (`config_dir` is still a manifest-overridable field);
the *default* changes.

**Test shape:** load a manifest with no `config_dir` clause; assert
the resolved path is `<workspace>/.pos`. Load a manifest with
`config_dir: ~/.pos/config`; assert the explicit override is honoured.

**Maps to:** AC.PO.1 + AC.PROG.1.

### AC.C3 — Workspace-state resolver returns workspace-local paths only

A path-resolver seam exposed by workspace-bootstrap, when queried for
a state-class file (objective-tracker DB, orchestrator SQLite, scope-
of-work SQLite, first-run.state, first-run.log, persona contract),
returns a path under `<workspace>/.pos/` (or under `<workspace>/`
where component specs already place state, e.g. `<workspace>/personas/`).
Whatever the host's `~/.pos/` contains for these state classes, the
resolver does NOT read or surface it.

**Test shape:** populate a tmp-fs fake `~/.pos/` (override via
`Path.home`) with a fake `objective_tracker.sqlite`; resolve the
state-class path for the tracker DB on an empty `<workspace>/.pos/`;
assert the resolved path points under `<workspace>/.pos/`, not under
`~/.pos/`. Mirror tests for orchestrator SQLite, scope-of-work SQLite,
first-run.state.

**Maps to:** AC.PO.1 + AC.PROG.1.

### AC.C4 — Preference-class resolver applies workspace → home → bundled fallback

The same resolver, when queried for a preference-class file
(`memory.yaml`, `cost/ceilings.yaml`, `safety/always_ask.yaml`,
`reversibility.yaml`, `self-correction.yaml`, `degradation-config.yaml`,
`telegram.yaml`, `bootstrap.yaml`, `observability.yaml`,
`orchestrator.yaml`, `self-upgrade.yaml`, `workspace_bootstrap_py.yaml`),
returns the first path found in: (1) `<workspace>/.pos/<filename>`,
(2) `~/.pos/<filename>`, (3) the scaffold's bundled default.

**Test shape:** with neither `<workspace>/.pos/memory.yaml` nor
`~/.pos/memory.yaml` present, resolve memory.yaml; assert the
bundled-default path is returned. Place a fake `~/.pos/memory.yaml`;
assert the home path is returned. Place a fake
`<workspace>/.pos/memory.yaml`; assert the workspace path is returned
(workspace wins). Mirror checks for at least one other preference
file (cost ceilings).

**Maps to:** AC.PO.1 + AC.PROG.1 + AC.PO.2.

### AC.C5 — workspace-bootstrap first-run scaffold writes state workspace-local; preference overrides workspace-local

`first_run_scaffold.run_first_run_scaffold(...)` lays state-class files
under `<workspace>/.pos/` only (first-run.state, first-run.log,
persona contract directory in line with existing component conventions).
Preference-class scaffold writes (the YAML files in today's
`_SCAFFOLD_FILES`) land at `<workspace>/.pos/<filename>` as workspace
overrides; the resolver still respects an existing `~/.pos/<filename>`
if the workspace file is absent.

**Test shape:** invoke `run_first_run_scaffold` against a tmp-fs
workspace fixture; assert all preference YAMLs land under
`<workspace>/.pos/`; assert state files (where the scaffold lays
them) also land under `<workspace>/.pos/`. The launchd plist
`EnvironmentVariables` reflect the workspace-local paths.

**Maps to:** AC.PO.1 + AC.PROG.1.

### AC.C6 — Components with `Path.home() / ".pos"` runtime defaults migrate

The five components that hard-code `Path.home() / ".pos"` as a
default (cost-governance/src/cli.py, cost-governance/src/config.py,
graceful-degradation/src/config.py, memory-system/src/staging.py,
hands-off-lifecycle/hooks/first_run_helper.py) rotate to use the
resolver. State-class defaults (e.g., memory-staging SQLite, hands-
off-lifecycle log) become workspace-local. Preference-class defaults
(e.g., cost ceilings) become resolver-routed (workspace → home →
bundled).

**Test shape:** per-component test that constructs the component's
default path with no override; for state-class outputs, assert the
path is workspace-local; for preference-class outputs, assert the
resolver chain is exercised.

(NOTE: each of these is a separate sealed-component amendment with
its own AC tree; this sub-plan names the cross-cutting outcome. The
owner may rule that some defaults stay host-global if the component's
spec-v1.x objective explicitly says so. **HALT TRIGGER:** if any
component's spec contradicts the partition, surface — that's a
spec-amendment question, not C's call.)

**Maps to:** AC.PO.1 + AC.PROG.1.

### AC.C7 — Launchd plist `EnvironmentVariables` carry per-workspace paths

The plist install (amendment #6 + #29 surface) carries env vars
pointing at workspace-resolver outputs (`<workspace>/.pos/...` for
state; for preferences, the resolved path the spawned service should
read). Two workspaces on one host produce two distinct plists with
two distinct env-var sets for state-bearing variables.

**Test shape:** scaffold two fixture workspaces; read both plists;
assert `EnvironmentVariables` differ for any state-path-bearing
variable (extending amendment #29's existing port-only check to the
broader state-path surface).

**Maps to:** AC.PO.1 + AC.PROG.1.

### AC.C8 — Cross-workspace integration test (AC.PROG.1 mirror)

A two-workspace integration test asserts state-isolation: scaffold
two workspaces, run first-run on each, assert no state-class path
written by one is read by the other. Preference-class fallback is
spot-checked (a preference at `~/.pos/memory.yaml` is visible to
both workspaces unless one writes a workspace override).

**Test shape:** new test
`<workspace>/tests/integration/test_two_workspace_state_isolation.py`.
Coverage matrix: every state-class file is checked for path-
distinctness across the two workspaces; one preference-class file is
checked for shared-fallback behaviour.

**Maps to:** AC.PROG.1.

---

## 5. Out of scope

- Renaming `~/.pos/` to `~/.loam/` (Idea 10 — separate migration).
- Cross-workspace data-sharing as a feature (e.g. a "user profile"
  shared across workspaces). The preference-class fallback is the
  shape that exists; richer sharing is Idea 4 territory.
- Migration of memory-graphiti's own data store (not under `~/.pos/`
  — managed by graphiti-core).
- Migration of Telegram credentials (already at `~/.claude/channels/`,
  workspace-agnostic by design).
- Migration of test-fixture host-overrides used by component tests.
  Tests already inject `pos_root` overrides; no change needed.
- An auto-migration runner that copies `~/.pos/` state-class content
  into `<workspace>/.pos/`. D-MASTER.2 makes this unnecessary —
  state-class remnants in `~/.pos/` are silently ignored; fresh
  scaffold writes workspace-local from the start.
- Operator-facing migration documentation. Nothing to document — the
  partition keeps `~/.pos/` working transparently as global preference
  fallback; state remnants are silently superseded.

---

## 6. Halt triggers

1. **A sealed component's spec-v1.x objective explicitly mandates
   host-global *state* (not preference) storage.** Halt and surface;
   the partition touches a contract that requires owner re-ruling.
2. **AC.C1's path-mismatch fix breaks amendment #39 or #40 tests.**
   Halt and surface; re-extension of those amendments needs owner
   approval.
3. **The resolver's workspace → home → bundled chain creates a hazard
   in a component test that already overrides `pos_root`.** Halt and
   surface; an adapter may need an explicit fixture seam.
4. **The amendment touches more than ~6 sealed components in a single
   build.** Halt and split into smaller amendments (per
   `feedback_serialize_amendment_builds`).
5. **A component's preference file is found to carry workspace-state
   semantics in practice (i.e., it should be state-class, not
   preference-class).** Halt and surface; the partition table in §1
   needs revision.

---

## 7. Bookkeeping

C decomposes into multiple `pos-amend` manifests, one per amendment.
The recommended split (subject to D-C.1 below):

- **C.1 — workspace-bootstrap resolver seam + config_dir default**
  (workspace-bootstrap; one component). Introduces the state-vs-
  preference resolver and the manifest default rotation.
- **C.2 — tracker-seed signature fix** (workspace-bootstrap +
  primary-persona; AC.C1).
- **C.3 — runtime defaults for cost-governance + graceful-degradation
  + memory-system staging + hands-off-lifecycle log** (multi-
  component; smaller within if owner prefers). Routes through the
  resolver introduced in C.1.
- **C.4 — Plist env-var widening + cross-workspace integration test**
  (workspace-bootstrap; AC.C7 + AC.C8).

Per amendment: standard manifest shape (`seal_test`, `sidecar`,
`frozen_baseline`).

---

## 8. Dispatch-time additions

When each C-sub-amendment's brief is drafted:

- WD: canonical.
- Plan-before-code per amendment.
- ODD §2.4 + §2.5 audit per amendment.
- The amendments serialise behind each other; recommended order: C.2
  (path-mismatch fix; smallest blast radius) → C.1 (resolver +
  config_dir default) → C.3 (runtime-default migration) → C.4 (plist
  + integration test).
- No `git commit --amend`.

---

## 9. Lens-2 trace blocks

| AC | AC.PO.1 | AC.PO.2 |
|----|---------|---------|
| AC.C1 | Path mismatch closes; persona reads consistent state. | Resolver-API consistency. |
| AC.C2 | One config_dir default, workspace-rooted. | Manifest schema convention extended. |
| AC.C3 | State always workspace-local; the persona names one rule. | Resolver primitive (state class). |
| AC.C4 | Preferences resolve through workspace → home → bundled, matching the user's Claude Code mental model. | Resolver primitive (preference class). |
| AC.C5 | Scaffold lays both classes correctly. | Existing scaffold extends to the partition. |
| AC.C6 | Components stop hard-coding host-global. | Per-component default routes through resolver. |
| AC.C7 | Plist env carries the same locality contract. | Plist-install primitive extended. |
| AC.C8 | Two-workspace coexistence is structurally proven. | Integration-test shape. |

---

## 10. Decision register (sub-plan-local)

| Code | Question | Recommendation |
|------|----------|----------------|
| D-C.1 | Should C be one large amendment or multiple smaller? | Multiple smaller (C.1–C.4 above). Per `feedback_serialize_amendment_builds` the build dispatcher serialises anyway; smaller amendments are easier to review. |
| D-C.2 | `config_dir` default rotation: do we also rename to `state_dir` to reflect content? | No. Under the new partition the directory carries both classes (state files always; preference overrides where present); `config_dir` reads correctly under either reading. A rename is medium cost (manifest schema + every adapter) for cosmetic value. Keep the name. |
| D-C.4 | What about `<workspace>/data/`? Several adapters write there (e.g., safety, observability, cost) — should those migrate to `<workspace>/.pos/data/` for uniformity? | No. `data/` is workspace-local already (adapters today use `host.workspace_root / "data" / ...`); uniformity-for-its-own-sake is medium cost for low leverage. Keep `data/` as-is. |
| D-C.5 | How does the resolver handle a workspace where `<workspace>/.pos/` exists but is partially populated? | Same as amendment #28's `partial_recovery` path — the resolver returns the configured location for missing files; the scaffold writes them on next run, leaving existing files untouched. The partial-recovery path already handles new-resolver path discovery. |

---

## 11. Builder freedom (method-only notes)

Builder chooses: the exact ordering of C.1–C.4 within scope, the
exact API shape of the resolver seam (single function with a class
discriminator vs two functions; method-level), the test fixture's
tmp-fs shape, the env-var key list in AC.C7's plist diff. Builder
chooses how to express the state-vs-preference partition table in
code (constant list, enum, registry).

---

## 12. Test register

Per-amendment test files; the cross-cutting test `AC.C8` lands
alongside the last amendment in the C-series (C.4 recommended).

| AC | Suggested test file | Suggested test function |
|----|---------------------|--------------------------|
| AC.C1 | `workspace-bootstrap/tests/test_tracker_seed_path_mismatch.py` | `test_AC_C1_tracker_db_path_workspace_root` |
| AC.C2 | `workspace-bootstrap/tests/test_manifest_default_config_dir.py` | `test_AC_C2_default_config_dir_workspace_local` |
| AC.C3 | `workspace-bootstrap/tests/test_resolver_state_class.py` | `test_AC_C3_state_class_resolves_workspace_local` |
| AC.C4 | `workspace-bootstrap/tests/test_resolver_preference_class.py` | `test_AC_C4_preference_class_workspace_then_home_then_bundled` |
| AC.C5 | `workspace-bootstrap/tests/test_scaffold_workspace_local.py` | `test_AC_C5_scaffold_writes_under_workspace` |
| AC.C6 | per-component (cost-governance, graceful-degradation, memory-system, hands-off-lifecycle) | `test_AC_C6_<comp>_default_resolves_correctly` |
| AC.C7 | `workspace-bootstrap/tests/test_plist_env_vars_workspace_local.py` | `test_AC_C7_plist_env_distinct_per_workspace` |
| AC.C8 | `<top>/tests/integration/test_two_workspace_state_isolation.py` | `test_AC_C8_two_workspace_state_isolation` |

---

## 13. Asymmetric observations

1. **The `host.config_dir` indirection was already in place (asymmetric
   win).** `manifest.py` defaults `config_dir` to
   `workspace_root / "config"`; adapters all read
   `host.config_dir / ...`. The partition rotates the *default* and
   adds the resolver seam — not every adapter. Effort: low. Leverage:
   high.

2. **The path-mismatch (AC.C1) is one parameter rename.** `pos_root`
   → `workspace_root` in `tracker_seed.tracker_db_path_for`. Two
   callers update; persona-side already takes `workspace_root`.
   Effort: trivial. Leverage: closes a real latent bug.

3. **D-MASTER.2's revision drops the migration runner entirely
   (asymmetric win, taken).** The original C plan carried a halt-and-
   surface diagnostic + an operator-run `mv` + migration docs. All
   three are gone — the partition makes them unnecessary because
   `~/.pos/` keeps working as global preference fallback and state
   remnants are silently superseded. Effort saved: medium (no
   `PartialScaffoldError` extension, no migration doc, no halt
   logic). Leverage gained: zero operator action on canonical install.

4. **Mirroring Claude Code's `~/.claude/` pattern (asymmetric win).**
   Operator already understands the partition from Claude Code; no
   new mental model. The pos-v2 resolver re-uses the user's existing
   knowledge.

5. **Inverse-asymmetric: `<workspace>/data/` cleanup.** Adapters
   already use `workspace_root / "data" / ...`; renaming for
   uniformity is medium cost for low leverage. Dropped per D-C.4.
