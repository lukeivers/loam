# Plan-doc — Slice 2: handsoff-loop swarm core `claude -p` → in-session subagent

**Slug (scope-descriptive):** `claude-p-to-insession-subagent-fanout-slice2-swarm`
**Class:** MINOR — second slice of the in-session-subagent-migration minor (new
spawn-primitive path on the swarm leaf dispatch; no breaking surface). Version
derives at release time — NOT pre-assigned.
**Working directory:** `/Users/lukeivers/loam/`.
**Authored:** 2026-06-02.
**Owner greenlight:** Luke (TG 13512) — build Slice 2, the flagship leaf-dispatch
conversion, after Slice 1 sealed.

**BASELINE (build time):** `34daa5a2` — Slice 1's apply commit (the
workspace-bootstrap SEAL_COMMIT sidecar tip after Slice 1). The handsoff-loop
family seals against the **workspace-bootstrap** component anchor (same as
AC.TPI / AC.BRC — the source lives under `framework/tools/handsoff-loop/`, inside
the workspace-bootstrap seal-test's admitted `framework/tools/` prefix), so the
Slice-2 seal-diff is scoped `34daa5a2..<seal>` to capture only Slice 2's work.

**Predecessors / load-bearing context:**
- Parent ODD plan (the three-slice map; AC.SWARM.* enumerated in its §5):
  `/Users/lukeivers/pos3/workspace/.scratch/claude-output/loam-insession-subagent-migration-plan.md`.
- Slice 1 (SEALED — the dispatcher-seam pattern this slice reuses):
  `docs/plans/sealed/claude-p-to-insession-subagent-fanout.md`; seal commit
  `557a904e`; the seam is `set_in_session_dispatcher` /
  `get_in_session_dispatcher` / `clear_in_session_dispatcher` +
  `InSessionResearchSource` in
  `framework/workspace-bootstrap/src/loam/workspace_bootstrap/deep_role_research_provider.py`.

**Quality bar:** the decompose → dispatch → independent-judge → frozen-verify
spine is byte-behaviour-equivalent across the swap; no sealed honesty control
(frozen-acceptance isolation, the independent-verify gate, the bounded
verification-gated re-drive) is weakened by the spawn-primitive change.

---

## §1. Summary / TL;DR

Slice 2 converts the handsoff-loop swarm core's **leaf dispatch** —
`orchestrator._dispatch_subagent`, which today runs
`subprocess.run(build_goal_drive_argv(spec), env=isolated_env())` to spawn a
detached `/goal`-driven `claude -p` sub-agent per sub-task — to an **in-session
subagent** dispatched through a host-session-registered dispatcher callable (the
same seam shape Slice 1 established). The spine that surrounds the leaf dispatch
(`run_handsoff_loop` / `_run_subtask_pass` / `verify` / `frozen.assert_unseen_by`
/ the bounded re-drive) is **untouched in substance** — only the per-sub-task
spawn primitive changes.

**The win (economic, identical to Slice 1's):** in-session subagents are
accounted against the subscription plan limits, NOT the post-June-15 metered
Agent SDK credit a detached `claude -p` draws from, and they share the parent
session's MCP so they never re-load the Telegram plugin and cannot SIGTERM-steal
the operator's single bot-poller slot.

**Residual `claude -p` path KEPT:** `build_goal_drive_argv` +
`isolated_env` + the `_isolation` helper STAY in the module as the residual /
explicit-opt-in mechanism for the launchd-sessionless path that has no living
parent session to fan an in-session subagent from. The `loam_spawn_isolation` /
subloam-driver isolation apparatus is **NOT deleted** — its scope narrows to
residual-only; the converted in-session path never touches it (no subprocess
argv to isolate).

---

## §2. Placement decisions (Slice 2)

| Item | Placement | Rationale |
|---|---|---|
| In-session dispatch seam (the host→swarm bridge) | `framework/tools/handsoff-loop/src/handsoff_loop/orchestrator.py` — a process-level dispatcher registry (`set_swarm_in_session_dispatcher` / `get_swarm_in_session_dispatcher` / `clear_swarm_in_session_dispatcher`) | Mirrors Slice 1's registry seam. The live host session (the only context with the Task primitive) registers a `(prompt: str, *, timeout: int) -> str` dispatcher; `_dispatch_subagent` resolves it at call time. A registry keeps `run_handsoff_loop` zero-extra-argument so every pre-existing caller/test is byte-behaviour-unchanged. No-dispatcher-registered → the residual `-p` path (graceful, preserves the sealed behaviour). |
| Converted leaf dispatch | `orchestrator._dispatch_subagent` | The ONLY `-p` spawn surface in the swarm core. The decompose/judge/verify spine that calls it is unchanged (AC.FOUND.0 consumed, not re-proved). |
| Residual `-p` leaf dispatch | unchanged — `build_goal_drive_argv` + `isolated_env` STAY, reached when no in-session dispatcher is registered | The launchd-sessionless path still needs it; keeping it preserves the `loam_spawn_isolation` guard's residual-only role (do NOT delete — plan §3 Surface #3 / H-6). |
| `cost_usd` on converted dispatches | honest `None` (measurement-gap) | In-session subagents have no per-call `claude -p --output-format json` envelope to read `total_cost_usd` from. The converted leaf returns `cost_usd=None` rather than a fabricated per-call cost (parent plan §3 Surface #4 — honest-None, NOT a regression). The plan-level cost signal becomes the `/usage` read. |
| Isolation-guard scope-narrowing | narrated in-code at the converted call site | `_isolation` / `loam_spawn_isolation` are NOT deleted — the residual `-p` path still needs them. The converted path simply does not call them (no argv to isolate). Narration in-code so a future reader does not "clean up" a still-load-bearing guard. |

---

## §3. Halt-and-surface BEFORE build (recorded at plan-authoring)

- **Surface #1 (no halt).** The replacement mechanism IS the Claude-native
  in-session subagent / Task primitive (Lens 1: compose on the platform
  primitive). The dispatcher is a callable the live host session injects, exactly
  as Slice 1.
- **Surface #2 (SURFACED — memory-reality mismatch; SAL-class finding; no
  hard-halt).** The parent plan's **AC.SWARM.2 presumes the current swarm-core
  leaf dispatch is parallel** ("full parallelism preserved", "must not silently
  serialize"). **VERIFIED-AGAINST-TERRITORY this session: it is NOT parallel.**
  `_run_subtask_pass` (orchestrator.py L211–241) dispatches sub-tasks in a
  strictly-sequential `for` loop over a blocking `subprocess.run`; there is **no
  concurrency primitive anywhere in `framework/tools/handsoff-loop/src/`**
  (`grep` for `ThreadPool` / `concurrent.futures` / `threading` / `asyncio` /
  `multiprocessing` returns empty). The `/goal` drive iterates turns *within* one
  sub-agent; the N sub-tasks run one-after-another. **Resolution (Lens 6
  four-step, recorded in §10 SAL-2 + §14):** AC.SWARM.2 is re-scoped to its
  truthful form — the conversion must not *change the dispatch-ordering
  semantics* (it stays dispatch-for-dispatch equivalent to the sealed spine; the
  current sequential posture is preserved, NOT regressed). Introducing genuine
  concurrency where none existed would be a **swarm-shape change**, which the
  objective explicitly excludes ("only the leaf-execution mechanism changes") and
  the build constraint names as a HALT trigger ("materially bigger than swap the
  leaf dispatch"). So: convert the primitive, preserve the ordering semantics,
  do NOT add parallelism. Surfaced in the final report, not silently rewritten.
- **Surface #3 (no halt).** In-session subagents share the parent session's MCP
  — they do NOT spawn a competing `claude` that re-loads the Telegram plugin and
  SIGTERM-steals the bot-poller slot. So the kill vector the `_isolation` /
  `loam_spawn_isolation` apparatus defends against does not exist for converted
  dispatches. The guard's **new role is RESIDUAL-ONLY** (launchd-sessionless
  `-p`). It is **NOT deleted** (H-6). The AC.TPI.* family (which seals the
  `_isolation` helper) stays green by construction — `_isolation` is unchanged;
  the residual `-p` path still routes through it.
- **Surface #4 (no halt).** `cost_usd` becomes honest `None` for converted
  dispatches (no `-p` JSON envelope to read). AC.SWARM.4 asserts the honest-None;
  it is NOT a regression (parent plan §3 Surface #4).

---

## §4. Spec-objective placement

**Binds to AC.PO.1 + AC.PO.2** (prime objective, `docs/VALUE_PROPOSITION.md`) —
the migration keeps loam's flagship parallel-work toolkit (the swarm core, the
harness toolkit, Lens 2 harness-test) on subscription economics; the swarm core
is the highest-leverage convertible surface (the buyer story "runs on the Claude
plan you already have; no separate metered agent credit to manage"). **Lens 1** —
the in-session subagent primitive IS the leveraged Claude-native capability.

**Ladders to:** AC.SWARM.* (Slice 2) → this minor → every later release that fans
out swarm work inherits subscription economics → AC.PO.

---

## §5. Acceptance criteria (Slice 2 — AC.SWARM.* family)

> AC IDs are scope-descriptive (`SWARM` = swarm core). All ACs outcome-shape —
> they state the observable outcome, never the in-session-dispatch *method*
> (method is the builder's call; tight scope leaves it inferable from the
> constraints). Each AC is satisfiable by more than one dispatch wiring →
> outcome-shape confirmed.

- **AC.SWARM.1 — the swarm leaf dispatch no longer spawns a detached `claude -p`
  subprocess.** A `run_handsoff_loop` run over ≥2 sub-tasks completes with each
  sub-task dispatched via the in-session path (the registered dispatcher); no
  detached `claude -p` child process is created for the leaf dispatch (the
  `subprocess.run` spawn surface is booby-trapped and never hit). A usable
  per-sub-task transcript + result is produced. *Outcome, not method:* asserts
  the absence of the `-p` subprocess spawn + presence of a usable result; does
  not prescribe which in-session surface produces it.

- **AC.SWARM.2 — the dispatch-ordering semantics are preserved across the swap
  (no silent re-serialization or re-ordering).** *Re-scoped from the parent
  plan's "full parallelism preserved" — SAL-2: the current spine is sequential,
  not parallel (§3 Surface #2).* A multi-sub-task converted run dispatches the
  sub-tasks in the SAME order and with the SAME one-per-sub-task cardinality as
  the sealed spine (the conversion is dispatch-for-dispatch equivalent: N
  sub-tasks → N in-session dispatches, in `sub_tasks` order). The swap does NOT
  silently change the ordering posture in either direction (does not collapse N
  dispatches into one, does not re-order, does not drop a sub-task).

- **AC.SWARM.3 — the independent-judge honesty controls are intact.**
  Frozen-acceptance isolation (`frozen.assert_unseen_by` over every brief) still
  holds across the converted path; "done" is still decided by loam's independent
  tool-executing `verify`, never by a sub-agent self-report; the bounded
  verification-gated re-drive (`refine_log` gated on `independent-verify`) is
  unchanged. The spawn-primitive swap touches the leaf dispatch ONLY — the
  decompose/judge/verify spine is byte-behaviour-equivalent (the sealed AC.A.* /
  AC.BRC.* / AC.TPI.* suites stay green).

- **AC.SWARM.4 — honest cost-None on converted dispatches (outcome-altitude).** A
  converted `run_handsoff_loop` over a real (not stubbed via the deterministic
  spine seam) objective reports `cost_usd` as an honest `None` (measurement-gap)
  for the converted leaf dispatches rather than a fabricated per-call cost, AND
  completes with a definite `final_verify` verdict + `human_loop_driving=False`.
  **Marked `outcome-altitude: true`** — verified by invoking `run_handsoff_loop`
  on a real objective with a real on-disk verify check (no pre-arranged
  transcript state), through the registered in-session dispatcher.

**Slice-2 seal closes on: AC.SWARM.1, AC.SWARM.2, AC.SWARM.3, AC.SWARM.4.** (No
deferred AC in Slice 2 — AC.RES1.4, the calendar-gated billing gate, lives in
Slice 1 / the parent plan §9 and gates Slice 3, not this seal.)

---

## §6. Build steps (method-level guidance — builder's call per ODD §1.1)

1. Manifest: `docs/plans/claude-p-to-insession-subagent-fanout-slice2-swarm.manifest.yaml`;
   single-component anchor = `workspace-bootstrap` (the handsoff-loop family's
   seal anchor); narrative target under `framework/hands-off-lifecycle/seals/`.
   BASELINE pins Slice 1's apply tip `34daa5a2`.
2. Add the swarm in-session dispatcher seam (process-level registry) in
   `orchestrator.py`. Convert `_dispatch_subagent` to: resolve the registered
   dispatcher; if present, build the SAME `/goal`-driven prompt
   (`spec.prompt()`), dispatch it in-session, return
   `(transcript, wall_clock_s, cost_usd=None)`; if absent, fall through to the
   UNCHANGED residual `-p` path. Keep `_run_subtask_pass` / `run_handsoff_loop` /
   the verify spine / the re-drive byte-behaviour-equivalent.
3. Narrate the `_isolation` / `loam_spawn_isolation` guard's residual-only role
   in the converted call site (do NOT delete the guard).
4. Author tests for AC.SWARM.1–.4.
5. `loam amend apply` → tests green → `loam amend seal` → LOCAL only (no push).

---

## §7. Out of scope (Slice 2)

1. Slice 3 (LitRPG path) — its own manifest/seal in pos3, gated behind the
   post-June-15 AC.RES1.4 billing confirmation.
2. The launchd-sessionless residual `-p` path — genuinely cannot convert; stays
   metered; covered by the spend-cap.
3. Deleting `loam_spawn_isolation` / the `_isolation` helper — scope narrows to
   residual-only but stays load-bearing.
4. **Introducing genuine concurrency / parallelism into the swarm core** — the
   current spine is sequential; adding parallelism is a swarm-shape change, NOT a
   spawn-primitive swap (§3 Surface #2 / SAL-2). Out of objective scope; surfaced
   for owner disposition as a possible follow-up.
5. Pushing the minor to origin — owner-gated release later.

---

## §8. Halt triggers (in-flight conditions that abort the build)

- **H-1 — a sealed honesty control would weaken.** If converting the leaf
  dispatch cannot preserve frozen-acceptance isolation, the independent-verify
  gate, or the bounded re-drive without weakening it, HALT.
- **H-2 — the no-API-key invariant is at risk.** If the only viable in-session
  conversion reaches for the `anthropic` SDK / `ANTHROPIC_API_KEY`, HALT.
- **H-3 — the residual-only guard is about to be deleted.** If a build step would
  remove `loam_spawn_isolation` / `_isolation` rather than narrow its scope, HALT.
- **H-4 — the conversion is structurally bigger than a leaf-dispatch swap.** If
  the swarm core's spawn path is entangled with isolation/background semantics
  that do not map cleanly to the in-session seam, HALT and surface rather than
  forcing.

---

## §10. F2 Ruthless Feedback (honest doubts + named risks)

- **SAL-1 — the conversion is genuinely contained to one function.** *Evidence:*
  the only `-p` spawn in the swarm core is `_dispatch_subagent`'s
  `subprocess.run` (orchestrator.py L170); `_run_subtask_pass` and
  `run_handsoff_loop` call it but contain no spawn themselves. The seam swap is a
  single-function change + a process-level registry — the spine is untouched.

- **SAL-2 — AC.SWARM.2's "full parallelism" premise is factually wrong; the spine
  is sequential.** *Disagreement:* the parent plan's AC.SWARM.2 says the
  conversion must "preserve full parallelism" and "must not silently serialize" —
  presuming the current leaf dispatch fans out concurrently. *Evidence (Tier-0,
  this session):* `_run_subtask_pass` (orchestrator.py L211–241) is a
  strictly-sequential `for i, st in enumerate(sub_tasks): ... _dispatch_subagent(
  ...)` over a blocking `subprocess.run`; `grep` for every concurrency primitive
  across `framework/tools/handsoff-loop/src/` returns empty. The sub-tasks run
  one-after-another today. *Alternative:* re-scope AC.SWARM.2 to "dispatch-
  ordering semantics preserved (no silent re-serialization or re-ordering)" — the
  truthful outcome the spawn-primitive swap must hold. Adding genuine parallelism
  is a swarm-shape change (out of objective scope, §7.4); it is surfaced for
  owner disposition, NOT silently introduced and NOT silently asserted-as-already-
  present. This mirrors Slice A's SAL-4 contract-shape correction: the sealed-
  intent contract is corrected where reality contradicts it, with evidence, not
  forced.

- **SAL-3 — `cost_usd` honest-None is a measurement-gap, not a regression.**
  *Evidence:* the per-call cost today is read from the `claude -p
  --output-format json` envelope's `total_cost_usd`; in-session subagents have no
  such envelope. *Alternative:* return `cost_usd=None` (the field already accepts
  `float | None` and `_run_subtask_pass` already folds any `None` to a `None`
  pass-cost — the honest-None path is ALREADY in the code, exercised here, not
  newly built). The plan-level cost signal becomes the `/usage` read.

- **SAL-4 — the residual `-p` path keeps the AC.TPI.* family green by
  construction.** *Evidence:* `_isolation` (the AC.TPI seal surface) is unchanged;
  the residual `-p` dispatch still routes through `build_goal_drive_argv` +
  `isolated_env`. The converted path simply does not reach `_isolation` — there is
  no argv to isolate — so AC.TPI's structural sentinels (which assert the argv/env
  the residual path builds) are unaffected.

---

## §11. Provenance trail (Tier-0, verified against the territory this session)

- `framework/tools/handsoff-loop/src/handsoff_loop/orchestrator.py` — CONFIRMED
  `_dispatch_subagent` (L146–184) runs `subprocess.run(build_goal_drive_argv(
  spec, cost_json=True), env=isolated_env())` per sub-task; cost read from the
  `--output-format json` envelope's `total_cost_usd` (L177–183).
  `_run_subtask_pass` (L187–241) is the strictly-sequential `for` loop;
  `run_handsoff_loop` (L281–491) holds the frozen-isolation guard
  (`frozen.assert_unseen_by`, L371), the independent `verify` (L403, L461), and
  the `refine_log` "gated_on: independent-verify" (L414, L471) honesty spine —
  the AC.SWARM.3 controls.
- `framework/tools/handsoff-loop/src/handsoff_loop/goal_drive.py` — CONFIRMED
  `build_goal_drive_argv` builds `["claude","-p",spec.prompt(),…]` + injects
  isolation (L135–148); `spec.prompt()` (L94–107) is the `/goal`-driven prompt
  the in-session dispatcher reuses verbatim.
- `framework/tools/handsoff-loop/src/handsoff_loop/_isolation.py` — CONFIRMED the
  AC.TPI seal surface (`inject_isolation` / `isolated_env`); unchanged by this
  slice (residual-only role).
- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/deep_role_research_provider.py`
  — CONFIRMED the Slice-1 dispatcher-seam pattern (`set_in_session_dispatcher` /
  registry + `InSessionResearchSource` + graceful-degrade-on-no-dispatcher) this
  slice mirrors.
- `framework/workspace-bootstrap/tests/test_no_sealed_amendments.py` — CONFIRMED
  the workspace-bootstrap seal-test admits `framework/tools/` +
  `framework/hands-off-lifecycle/` + `framework/hands-off-lifecycle/seals/` +
  `docs/plans/` (L279–357) — the handsoff-loop family's seal anchor.
- `docs/plans/sealed/telegram-poller-isolation-fix.manifest.yaml` /
  `docs/plans/sealed/loop-behavioral-refine-cycle.manifest.yaml` — CONFIRMED both
  the AC.TPI and AC.BRC families seal against the **workspace-bootstrap**
  component anchor with the narrative target under
  `framework/hands-off-lifecycle/seals/` — the exact pattern this slice reuses.

**Convention exemplar:** the Slice-1 manifest
`docs/plans/sealed/claude-p-to-insession-subagent-fanout.manifest.yaml` +
`docs/plans/sealed/telegram-poller-isolation-fix.manifest.yaml` (same anchor).

---

## §14. Method-decision record (builder's call, recorded at build/seal time)

- **D-build.1 — swarm dispatcher as an injected callable via a process-level
  registry** (mirrors Slice 1's D-build.1). The live host session registers a
  `(prompt: str, *, timeout: int) -> str` dispatcher via
  `set_swarm_in_session_dispatcher`; `_dispatch_subagent` resolves it at call
  time. A registry (vs threading a dispatcher arg through `run_handsoff_loop` →
  `_run_subtask_pass` → `_dispatch_subagent`) keeps every pre-existing caller/test
  byte-behaviour-unchanged. No-registration → the residual `-p` path (the natural
  degrade, preserving the sealed behaviour for the launchd-sessionless case).

- **D-build.2 — keep the residual `-p` path + `_isolation`.** The
  `build_goal_drive_argv` + `isolated_env` + `_isolation` machinery STAYS so the
  `loam_spawn_isolation` guard stays exercised + load-bearing for the
  launchd-sessionless residual path. Deleting it would re-expose those spawns to
  the proven Telegram kill vector (H-3).

- **D-build.3 — AC.SWARM.2 re-scoped (SAL-2).** The parent plan's "full
  parallelism" premise was factually wrong (the spine is sequential, verified
  this session). AC.SWARM.2 is re-scoped to "dispatch-ordering semantics
  preserved" — the truthful outcome of a spawn-primitive swap. Genuine
  parallelism is a swarm-shape change, out of scope (§7.4), surfaced for owner
  disposition.

- **D-build.4 — `cost_usd=None` on converted dispatches (SAL-3).** Honest
  measurement-gap (no `-p` JSON envelope). The honest-None fold is already in the
  spine (`_run_subtask_pass` collapses any `None` pass-cost to `None`); the
  converted leaf simply returns `None`.

### Commit SHAs

(backfilled 2026-06-11 — Tier-0 re-derived from the git ref graph; the cycle
sealed 2026-06-02 but this section was left at `<backfill>`)

- BASELINE: `34daa5a2` (Slice 1's apply commit — the workspace-bootstrap sidecar
  tip after Slice 1).
- Code commit: `0135cbc3` (2026-06-02 — plan + manifest + `orchestrator.py`
  conversion + dispatcher-seam exports in `__init__.py` +
  `test_AC_SWARM_insession_subagent_swarm.py`).
- Apply (sidecar/BASELINE bump): `8c604897`.
- Seal commit: `a315ed0b` (narrative landed at
  `framework/hands-off-lifecycle/seals/SEAL_COMMIT.claude-p-to-insession-subagent-fanout-slice2-swarm`;
  sidecar advanced to the apply commit `8c604897`).
- Release state (verified from git refs, NOT prose): the seal is an ancestor of
  tag `v1.1.0` — the slice **SHIPPED PUBLIC 2026-06-03 in v1.1.0** under the
  owner-authorized release run (STATE.md v1.1.0 entry names `0135cbc3` in the
  supporting-foundation list). Contained in every tag since (v1.2.0–v1.5.0).

### Verification (Tier-0)

(backfilled 2026-06-11, verified at HEAD `2662245c`-era main)

- `framework/tools/handsoff-loop/tests/test_AC_SWARM_insession_subagent_swarm.py`
  — **7 passed** (AC.SWARM.1–.4 surfaces).
- `framework/workspace-bootstrap/tests/test_no_sealed_amendments.py` — **2
  passed** (fence integrity at HEAD; three later amendments — handsoff-tpi6,
  general-build-from-intent, v1.5.0 prep — have re-sealed over the same anchor
  since, each re-validating the fence).
- Sidecar chain: apply `8c604897` set SEAL_COMMIT to BASELINE `34daa5a2`; seal
  `a315ed0b` advanced it to `8c604897`; later seals have since advanced it
  further (current tip `21422aa4`).
- Ancestry: `git merge-base --is-ancestor a315ed0b v1.1.0` → true;
  `git tag --contains a315ed0b` → v1.1.0, v1.2.0, v1.3.0, v1.4.0, v1.5.0.
