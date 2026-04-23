# Amendment #28 — workspace-identity-routed first-run

**Amendment number:** 28
**BASELINE (pre-amendment tip):** `2a86c27a` (chore(seals):
stale-launchd-readme-cleanup seal — amendment #27).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored:** 2026-04-23.
**Research:** `docs/rebuild/plans/research/amendment-28-workspace-identity-routed-first-run-research.md`
(required by the research-before-plan CDC; read before building).
**Motivating defect report:** `.scratch/claude-output/bootstrap-reconsideration.md`
in the pos3 test clone.

## 1. Objective

First-run completion state is routed per workspace. A SessionStart hook
fired in workspace B never short-circuits to "already done" because
workspace A previously completed. Each workspace's dispatcher reads a
state artefact that names the workspace it belongs to; a state file
belonging to a different workspace is treated as absent. The pos3 /
ivers-corp-pos-v2 false-success mode closes structurally.

Two behaviours; AC-count maps in §4.

## 2. Constraints

- **Budget.** Behavioural amendment only. Scope limited to
  hands-off-lifecycle's `hooks/` package (state, dispatch, helper) plus
  its `tests/`. No new runtime deps. If the implementation would require
  touching any other sealed component's source, halt and signal.
- **Reversibility.** Fully reversible. State-file layout change is
  migration-handled (new layout supersedes old; an old
  `~/.pos/first-run.state` from pre-amendment is interpreted per its
  content — no workspace identity means no match, so it falls through
  to fresh-spawn rather than incorrectly short-circuiting).
- **Dependency fence.** Amends `hands-off-lifecycle/` only. Sealed
  components off-limits: memory-system, orchestrator, workspace-bootstrap,
  safety-layer, reversibility-primitive, cost-governance, self-correction,
  graceful-degradation, scope-of-work, objective-tracker, primary-persona,
  observability-aggregator, self-upgrade, telegram-interface.
- **Authority bound.** Owner approves the ACs in §4 and the seal-plan.
  Builder chooses the state-file layout per the Option A/B/C trade-offs
  in `research.md §5` — the default recommendation is Option C, flagged
  as builder-challengeable.
- **Fail-closed direction.** A state artefact present but unreadable, or
  belonging to a different workspace, is treated as **absent** by the
  dispatcher's Case 2 — the current workspace's first-run proceeds as
  though fresh. No path short-circuits on ambiguous state.
- **Error codes.** Reuse `-32099 hands_off_lifecycle_internal` for new
  failure modes (state-file unreadable, state-file owned by another
  workspace and refused); no new code allocations.
- **Preserve existing failure-class closures.** Per `research.md §7`: the
  hook-timeout SIGKILL remedy, silent-death diagnosis, and atomic-write
  semantics must remain intact. Any builder choice that weakens these is
  a halt trigger.

## 3. Research findings (brief)

Full research at the doc referenced above. The one-paragraph digest
carried here: `~/.pos/first-run.state` is a per-host singleton with no
workspace identity in either its path or its content; `first_run_dispatch.py`
Case 2 short-circuits on `status == "completed"` without comparing the
recorded owner to the current `pos_v2_root`; the original true-first-run
proposal specified per-workspace venv-presence as the marker but the
2026-04-22 session-start-detachment amendment replaced it with the
host-global sentinel to close a separate failure class, dropping the
per-workspace keying.

## 4. Acceptance criteria

Each criterion maps 1:1 to a test function in the build. Criterion IDs
continue the amendment #6 sequence (AC1–AC9 from namespaced-labels-and-bootout);
this amendment adds AC10–AC14.

### AC10 — re-extension of AC6: end-to-end multi-workspace dispatch

Given workspace A at `/tmp/alpha` (slug `alpha`) and workspace B at
`/tmp/beta` (slug `beta`), both sharing the same pos-host dir. Workspace
A has completed first-run (its state artefact says so). A fresh
`dispatch()` is invoked for workspace B. The dispatcher does **not**
return `_msg_completed()` — it enters the fresh-spawn path and spawns a
worker whose `pos_v2_root` argument is B. Test fixture provides both
workspace trees; assert the dispatcher's return string begins with
`"Your pos-v2 workspace is installing."` and asserts `subprocess.Popen`
was called with `--pos-v2-root /tmp/beta`.

### AC11 — state artefact carries workspace identity

A persisted state artefact names the workspace it belongs to. Reading
back a state written by workspace A while the current process claims to
be workspace B yields a dispatcher decision equivalent to "no state
present" — the `_msg_completed()` short-circuit is not reached.
Test: construct a state artefact whose recorded workspace is `/tmp/alpha`
with `status=completed`, invoke `dispatch(pos_v2_root=/tmp/beta, ...)`,
assert the return text is the fresh-start message.

### AC12 — self-workspace recognition preserved

Given a state artefact belonging to workspace A with `status=completed`,
a dispatcher invocation where `pos_v2_root` matches A returns the
completion message (Case 2 still fires for the correct workspace).
Regression test: the fix must not break the normal
session-after-first-run-complete flow.

### AC13 — corrupt / unparseable state is fresh-spawn

A state artefact present but malformed (truncated JSON, missing required
field, garbage bytes) is treated as absent by the dispatcher. Case 2
does not fire; the fresh-spawn path is invoked. Test: write garbage to
the state artefact, invoke `dispatch()`, assert worker is spawned.

### AC14 — silent-death detection is per workspace

Given workspace A has a `running` state with a dead pid and the dispatcher
is invoked for workspace B, the dispatcher does **not** flip A's state
to failed on B's behalf. B's dispatch proceeds as fresh; A's state is
left untouched. (Silent-death diagnosis only fires for the workspace
whose state is being inspected.) Test: stage A's state as `running`
with pid=0 and `updated_at` older than the stale window, invoke
`dispatch()` for B, assert A's state file is unchanged and B's
fresh-start path runs.

### AC:S — seal diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows only paths under
`hands-off-lifecycle/`,
`docs/rebuild/plans/amendment-28-workspace-identity-routed-first-run*`,
`docs/rebuild/plans/research/amendment-28-*`,
`docs/rebuild/FUTURE_IDEAS.md` (Idea 9 catalogue update), and paths
admitted under hands-off-lifecycle's existing allowed-prefix set plus
universal-paths admissions. Anything outside that set is a halt condition.

## 5. Behaviour-count check

| Behaviour | Criteria |
|-----------|----------|
| Dispatcher routes per workspace | AC10 (end-to-end), AC12 (self-workspace recognition) |
| State carries workspace identity | AC11 |
| Ambiguous state is fresh-spawn (fail-closed) | AC13 (corrupt), AC11 (foreign-workspace) |
| Silent-death diagnosis per workspace | AC14 |
| Seal discipline | AC:S |

Four behaviours in §1 objective split across five criteria (AC11 covers
two behaviours). Every behaviour is covered.

## 6. Flagged inferences (builder may challenge)

1. **State-file shape defaults to Option C (workspace-local).** Research
   recommends per-workspace state file under the workspace tree. If the
   builder uncovers a load-bearing need for host-global state (e.g., a
   supervisor that must enumerate every workspace's state), fall back to
   Option A (per-workspace file under `~/.pos/first-run-state/<slug>.state`)
   and explicitly admit the slug-collision hazard — this amendment does
   not close that hazard either way; that remains a future Idea 9 cycle.
2. **Migration of pre-existing `~/.pos/first-run.state`.** The old
   host-global state file is not deleted; it is interpreted by the new
   logic. Because it has no workspace identity, the dispatcher treats
   it as not-this-workspace on every new invocation — which is exactly
   the fresh-spawn behaviour AC11 demands. No migration code ships.
   If the builder discovers a case where leaving the old file causes
   user-visible surprise (e.g., an operator confused by its presence),
   add a one-line docs note; do not delete the file automatically.
3. **`workspace_root` string storage.** Storing the absolute
   path (resolved) is the default; storing a hash would remove the PII
   surface but complicates debugging. Default: absolute path.

## 7. Seal plan

1. Advance `BASELINE` in `hands-off-lifecycle/tests/test_cross_cutting.py`
   per amendment #23 frozen-H19 convention — **do not move**. Sidecar
   narrative stanza + allowed-prefix tuple update only.
2. Advance `BASELINE` in any hands-off-lifecycle seal-diff test that
   uses a floating BASELINE for the `hooks/` surface. (The builder
   inspects which tests apply.)
3. Amendment commit: `fix(hands-off-lifecycle): workspace-identity-routed
   first-run — amendment #28`.
4. Tests committed alongside the fix.
5. Seal commit (separate): `chore(seals): workspace-identity-routed-
   first-run seal — hands-off-lifecycle at <sha>`.
6. Run `pos-amend apply --dry-run` before the amendment commit;
   hard prereq per amendment #22.

## 8. FUTURE_IDEAS catalogue update

As part of this amendment's doc surface, append one paragraph to Idea 9
noting that slug-collision is not the only workspace-identity hazard —
state-file routing was closed by amendment #28, and slug-collision in
launchd labels remains an open future concern for its own cycle.

## 9. Halt triggers

1. Any test requires amending a sealed component outside
   `hands-off-lifecycle/` — halt.
2. The proposed Option C path placement conflicts with a workspace-tree
   convention (e.g. lands in a path a sealed test treats as
   forbidden) — halt and signal for an Option A fallback.
3. Pre-existing state-file migration surfaces a user-visible data
   concern the research did not anticipate — halt.
4. `pos-amend apply --dry-run` fails — halt, flag.
5. An AC test cannot be written deterministically (requires model
   inference or human judgment) — halt.

## 10. Tests

### 10.1 Pre-amendment

- `hands-off-lifecycle` full suite at BASELINE `2a86c27a` — green.
- Seal-diff tests across all 10 components — green (amendment-dispatch
  CDC: narrow test scope; untouched components get seal-diff only).

### 10.2 Post-amendment (pre-seal)

- `hands-off-lifecycle` full suite — green, including the five new
  AC10–AC14 test functions.
- Seal-diff tests across all 10 components — green.

### 10.3 Post-seal

- Seal-diff tests only across all 10 components — green (per
  amendment-dispatch CDC: skip pre-seal full rerun; sidecar-only edits
  in seal commit cannot break code).

## 11. ODD compliance

- §2.5 (no non-objective code): every new code path in `hooks/` maps to
  AC10–AC14. Builder audits the diff in both directions before seal.
- §4 (re-extension): AC10 is explicitly a re-extension of amendment
  #6's AC6 — the objective-level behaviour the original AC did not
  reach end-to-end. Commit message cites AC10 and names the extension.
- §5.1 (structural over advisory): Option C's path-based routing is the
  structural remedy; advisory-"remember to check workspace" inside the
  dispatcher is the anti-pattern this amendment refuses.
- §8.2.9 (no non-objective code in the diff): every file/branch in the
  diff maps back to an AC or is a universal-admissions entry (plan,
  manifest, CLAUDE.md-adjacent docs). Builder verifies at seal.
