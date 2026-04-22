# Proposal — namespaced-labels-and-bootout amendment (#6)

**Status:** DRAFT — approved by owner in-session 2026-04-22.
**Authored by:** assistant (this session).
**Target components (multi-component amendment):**
`workspace-bootstrap` + `hands-off-lifecycle`.
**Precedent:** session-start-detachment amendment (multi-component seal
at `d962ffd`), pyyaml-reachability amendment (single-component seal at
`9b4bcd3`).

---

## 1. Objective

Every service the first-run scaffold installs uses a label that embeds
the workspace's identity, and every bootstrap call replaces any prior
launchd/systemd-user configuration loaded under that label. Two
workspaces on one host coexist without collision; a re-run of the
scaffold from a relocated or renamed workspace overrides whatever stale
configuration the service manager cached from an earlier run.

Three behaviours in one objective — #4 below counts criteria against it.

## 2. Constraints

- **Budget.** Behavioural amendment only. No new runtime deps. If
  implementation would require restructuring `ServiceManagerRunner`
  beyond a slug helper + bootout wrapper + template parameterisation,
  halt and signal — scope creep.
- **Reversibility.** Fully reversible. Any label this amendment
  bootstraps can be `launchctl bootout`'d. No on-disk state written
  outside plist/unit files and the in-repo amendment docs.
- **Dependency fence.** Amends `workspace-bootstrap/` and
  `hands-off-lifecycle/` only. No other sealed component may be touched
  — orchestrator, memory-system, safety-layer, reversibility-primitive,
  cost-governance, self-correction, graceful-degradation, scope-of-work,
  objective-tracker, primary-persona, observability-aggregator,
  self-upgrade, telegram-interface are all off-limits.
- **Authority bound.** Owner approves acceptance criteria (this doc) +
  the seal-plan SHA bump. Builder chooses helper naming, module layout,
  whether the slug utility is a free function or a small class.
- **Fail-closed direction.** Slug-derivation failure halts the scaffold
  before any file write. Bootout failure for reasons other than "service
  not loaded" halts before attempting bootstrap — an ambiguous service-
  manager state must not be pushed through.
- **Error codes.** Reuse `-32099 hands_off_lifecycle_internal` for new
  failure modes (within the reserved `-32090..-32099` range). No new
  codes introduced.
- **Legacy labels.** Out of scope. Already-loaded unscoped labels
  (`com.pos.orchestrator`, `com.pos-v2.memory-graphiti`) that predate
  this amendment remain loaded after the amendment lands. Owner handles
  cleanup manually after first clean install verifies. Rationale: owner
  ruling in-session 2026-04-22.

## 3. Acceptance criteria

Each criterion maps 1:1 to a test function in the build.

### AC1 — slug derivation is deterministic

A function `workspace_slug(workspace_root: Path) -> str` returns a
string matching `^[a-z0-9][a-z0-9-]*$`: `basename(workspace_root)`
lowercased, non-matching characters replaced with `-`, runs of `-`
collapsed, leading/trailing `-` trimmed. Test asserts the slug for
fixture paths covering uppercase, underscores, dots, mixed punctuation,
and mixed-case Unicode.

### AC2 — plist labels embed the workspace slug (macOS)

After `run_first_run_scaffold(workspace_root=/tmp/alpha, ...)` on
macOS, the file
`<override_dir>/com.pos-v2.alpha.orchestrator.plist` exists and
`<override_dir>/com.pos-v2.alpha.memory-graphiti.plist` exists. Neither
unscoped filename (`com.pos.orchestrator.plist`,
`com.pos-v2.memory-graphiti.plist`) is written under any condition.

### AC3 — systemd unit names embed the workspace slug (Linux)

Symmetric to AC2 on Linux: units land as
`com.pos-v2.<slug>.orchestrator.service` and
`com.pos-v2.<slug>.memory-graphiti.service` under the override dir. No
unscoped unit filenames written.

### AC4 — bootout-before-bootstrap, idempotent (macOS)

`ServiceManagerRunner.bootstrap(label=L, service_file=F)` on macOS
executes `launchctl bootout gui/<uid>/<L>` (non-fatal on
"service not loaded") before `launchctl bootstrap gui/<uid> <F>`.
Running the same call twice produces identical final state from the
caller's perspective — the second call is a no-op observable.

### AC5 — stale-path replacement (the pos3 regression)

Given label L already loaded from plist `/old/plist` (program path
`/old/venv/bin/python`), a call
`bootstrap(label=L, service_file=/new/plist)` where `/new/plist` points
at `/new/venv/bin/python` results in `launchctl print
gui/<uid>/<L>` reporting `program = /new/venv/bin/python`. This is the
exact failure class that blocked pos3's first-run on 2026-04-22.

### AC6 — multi-workspace coexistence

Scaffold on workspace A (slug `alpha`) and on workspace B (slug `beta`)
in sequence. Both `com.pos-v2.alpha.orchestrator` and
`com.pos-v2.beta.orchestrator` are loaded simultaneously; `launchctl
print` for each reports a program path rooted at its own workspace. B's
scaffold does not evict A.

### AC7 — health poll targets computed labels

The first-run worker's Phase 4b health poll reads labels from the
first-run inventory under the workspace-slug rewrite — not hardcoded
strings. Test: invoke Phase 4b in a harness with workspace root pointing
at a fixture path with slug `fixture-x`; assert the poller probes
`com.pos-v2.fixture-x.memory-graphiti` and
`com.pos-v2.fixture-x.orchestrator`.

### AC8 — unrepresentable slug is refused structurally

If `workspace_slug()` would return the empty string (path basename
normalises to empty — `/`, `/...`, all-punctuation names),
`run_first_run_scaffold()` raises a typed exception (new
`WorkspaceSlugUnrepresentableError` subclass of `BootstrapError`, code
`-32099`), **before** any file write. Hand-craft a scaffold call with
such a root; assert no files appear in `pos_root` or the service-
manager dir and the error is typed.

### AC9 — seal diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` after the amendment shows
only paths under `workspace-bootstrap/`, `hands-off-lifecycle/`,
`docs/rebuild/components/namespaced-labels-and-bootout/`, and `data/`.
Any path outside this set is a halt condition for the seal commit.

## 4. Behaviour-count check

Three behaviours in §1 objective × split across nine criteria:

| Behaviour | Criteria |
|-----------|----------|
| Workspace-scoped labels | AC1 (derivation), AC2 (macOS file naming), AC3 (Linux unit naming), AC7 (poll wiring), AC8 (negative case) |
| Bootstrap replaces prior config | AC4 (mechanic), AC5 (stale-path replacement) |
| Coexistence across workspaces | AC6 |
| Seal discipline | AC9 |

Four distinct behaviours → nine criteria → every behaviour is covered
by at least one test.

## 5. Flagged inferences (builder may challenge)

1. **Label prefix `com.pos-v2`.** Normalised across both services
   because `com.pos-v2.memory-graphiti` already uses this form and the
   repo self-identifies as "pos v2." Orchestrator's current
   `com.pos.orchestrator` (unversioned) is bumped to
   `com.pos-v2.<slug>.orchestrator` for consistency.
2. **Slug source = `basename(workspace_root).lower()` sanitised.**
   Alternatives considered: git repo root, user-supplied name in a
   manifest, hash of abspath. Basename is human-readable and requires no
   new config surface. Unstable if the user renames the directory —
   acceptable trade-off for now.
3. **No collision detection.** Two distinct paths producing the same
   slug (e.g. `/a/pos-v2` and `/b/pos-v2`) will collide on the service
   label. Collision detection requires persistent state across
   workspaces and is out of scope; treat as known limitation.
4. **Halt on non-"not loaded" bootout failure.** Error stanza
   `service-manager-bootout-failed:<label>:<stderr-tail>`, code
   `-32099`. Do not push through to bootstrap.

## 6. Seal plan

1. Advance `BASELINE` in
   `workspace-bootstrap/tests/test_no_sealed_amendments.py` from
   `63b7cb8` → `acbde99` (current tip).
2. Advance `BASELINE` in
   `hands-off-lifecycle/tests/test_cross_cutting.py` to `acbde99`
   (current tip).
3. Amendment commit: `fix(workspace-bootstrap, hands-off-lifecycle):
   namespaced-labels-and-bootout amendment (#6)`.
4. Tests committed together with the fix.
5. Seal commit (separate): `chore(seals): namespaced-labels-and-bootout
   seal — workspace-bootstrap + hands-off-lifecycle at <sha>`. Appends
   amendment-cycle note to both `SEAL_COMMIT` sidecar files and updates
   pinned SHA at the bottom of each.

## 7. Halt triggers

- Slug utility requires more than a pure function to implement.
- `ServiceManagerRunner` needs an interface change beyond adding the
  bootout call — e.g. requires a new method signature on the test
  `service_runner` injection hook.
- Any test reveals a need to touch a sealed component outside the two
  amendment targets.
- Any AC test cannot be written deterministically (would require model
  inference or human judgment).

Any of the above: halt, signal to owner, re-scope before continuing.
