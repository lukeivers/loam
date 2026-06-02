# Plan-doc — migrate loam's `claude -p` fan-out to in-session subagents

**Slug (scope-descriptive):** `claude-p-to-insession-subagent-fanout`
**Class:** MINOR (new spawn-primitive path + a user-facing notice; no breaking
surface). Version derives at release time — NOT pre-assigned.
**Working directory:** `/Users/lukeivers/loam/`.
**Authored:** 2026-06-02.
**Owner greenlight:** Luke (TG 13481) — build Slice 1, the lowest-risk first
slice; sets up the live billing test.

**BASELINE (build time):** `aa759aa8` — the v1.0.1 post-publish backfill tip
(the tree is clean + released free for this minor). Slice-1 manifest pins this.

**Predecessors / load-bearing context:**
- Authored ODD plan (the full three-slice map this operationalizes):
  `/Users/lukeivers/pos3/workspace/.scratch/claude-output/loam-insession-subagent-migration-plan.md`
  (2026-06-02). VERIFIED against the territory this session — see §11.
- Feasibility study:
  `/Users/lukeivers/pos3/workspace/.scratch/claude-output/loam-swarm-to-insession-subagents-feasibility.md`.
- Prior pricing/threat research:
  `/Users/lukeivers/pos3/workspace/.scratch/claude-output/loam-anthropic-individual-use-line-research.md`
  (meter-not-ban; spend-cap is the bridge).

**Quality bar:** every converted workload keeps the budget + the graceful-
degradation fallback intact; no sealed honesty-control is weakened by the
spawn-primitive swap. Subscription-pool billing empirically confirmed before the
high-volume slice ships.

---

## §1. Summary / TL;DR

This minor migrates loam's autonomous parallel fan-out from spawning detached
`claude -p` subprocesses to fanning out **in-session subagents** (the Task
primitive — the same one a live Claude Code session uses to dispatch background
agents). The motive is economic: post-June-15-2026, `claude -p` / Agent-SDK
usage draws from a separate metered Agent SDK credit, while in-session subagents
are accounted **against the subscription plan limits**. The swap keeps full
parallelism — it changes the *spawn primitive*, not the swarm shape.

**Three convertible exposure sites**, shipped as **three serialized slices**:

1. **Slice 1 — deep-research provider** (`deep_role_research_provider.py`).
   Lowest risk: single call site, single bounded subagent. **Doubles as the
   empirical billing test** (a post-June-15 `/usage` read on this workload).
   **THIS DOC scopes + builds Slice 1.**
2. **Slice 2 — handsoff-loop swarm core** (`orchestrator._dispatch_subagent` +
   `goal_drive.py`). Builds after Slice 1 seals. (Out of this doc's build scope;
   its AC family AC.SWARM.* is enumerated in the parent plan §5.)
3. **Slice 3 — LitRPG `ClaudePrintClient`** (pos3 product workspace). Ships
   last, after slices 1–2 prove the billing premise. (Out of this doc's scope.)

**Two surfaces are ALREADY SAFE and convert to NOTHING** (named so no one
re-touches them): **keep-pace** (a `UserPromptSubmit` hook — zero spawn) and
**subloam-driver** (an interactive PTY, explicitly NOT `-p`; the bench-validity
clean room — converting it would contaminate the measurement).

**Honest residual (does NOT convert):** truly-sessionless launchd
auto-restart-after-crash generation (`framework/orchestrator`) stays on
`claude -p` and stays metered — an in-session subagent requires a living parent
session to fan out from, and there is none at a 3am crash-restart. Covered by
the `/usage-credits` spend-cap, NOT by this migration.

**Named deliverable shipped with Slice 1:** the **"keep loam open in the
background to finish while you're away; close it and it pauses"** USER NOTICE —
plain-language guidance that converted long-running work runs as long as the
session stays open. This is the operational behaviour-change the in-session
model introduces, surfaced instead of silently assumed.

---

## §2. Placement decisions (Slice 1)

| Item | Placement | Rationale |
|---|---|---|
| In-session research source (the replacement mechanism) | `framework/workspace-bootstrap/src/loam/workspace_bootstrap/deep_role_research_provider.py` | The provider owns its `ResearchSource`; the conversion adds a NEW production source + swaps the default. The injectable `ResearchSource` Protocol is unchanged (the deterministic AC.DRR.* tests stay green by construction). |
| In-session dispatch seam (the host→provider bridge) | same module — a process-level dispatcher registry (`set_in_session_dispatcher` / `get_in_session_dispatcher`) | The standalone Python provider is not itself a Claude session; the live host session that runs onboarding registers its Task-primitive dispatcher. No-dispatcher-registered → graceful fallback (AC.RES1.3). Seam shape is reusable by Slice 2. |
| USER NOTICE deliverable | a user-facing doc surface shipped with Slice 1 (`docs/insession-subagent-keep-open-notice.md`) reachable through the normal user-facing path | The notice is harness-general guidance, not slice-specific; ships once with the first converted long-running workload. |
| Isolation-guard scope-narrowing | documented in `deep_role_research_provider.py` (the converted call site) | `loam_spawn_isolation` is NOT deleted — the residual `-p` path still needs it. The converted path simply does not touch it (no subprocess argv to isolate). Narration in-code so a future reader does not "clean up" a still-load-bearing guard. |
| Residual `-p` source | unchanged — `ClaudeSubagentResearchSource` STAYS in the module | It is no longer the production default but remains the residual/explicit-opt-in mechanism + keeps the spawn-isolation consumer alive for that path. NOT deleted. |

---

## §3. Halt-and-surface BEFORE build (recorded at plan-authoring)

- **Surface #1 (no halt).** The replacement mechanism IS the Claude-native
  in-session subagent / Task primitive (Lens 1: compose on the platform
  primitive — loam does not build a new fan-out framework). The dispatcher is a
  callable the live host session injects.
- **Surface #2 (no halt).** The billing premise is high-confidence-not-certain
  (assembled from two Anthropic doc lines). Slice 1 doubles as the empirical
  settle: a post-June-15 `/usage` read. **AC.RES1.4 stays open until that read;
  it does NOT block this seal** (it is a MINOR-level deferred empirical gate
  that gates the later high-volume Slice 3, not a Slice-1 code AC — see §5).
- **Surface #3 (no halt).** In-session subagents share the parent session's MCP
  — they do NOT spawn a competing `claude` process that re-loads the Telegram
  plugin and SIGTERM-steals the bot-poller slot. So `loam_spawn_isolation`'s
  kill vector does not exist for converted workloads. The guard's **new role is
  RESIDUAL-ONLY** (launchd-sessionless `-p` + bench-PTY). It is **NOT deleted.**
  Accuracy correction (verified this session): there is **no PreToolUse hook**
  in canonical loam's `.claude/hooks` for this — the enforcement is the in-code
  `assert_loam_spawn_isolated` function in the `loam_spawn_isolation` package.
- **Surface #4 (no halt).** The USER NOTICE ships WITH Slice 1, as AC.RES1.5
  (outcome-altitude), not a follow-up.

---

## §4. Spec-objective placement

**Binds to AC.PO.1 + AC.PO.2** (prime objective, `docs/VALUE_PROPOSITION.md`) —
the migration keeps loam's parallel-work toolkit on subscription economics,
which keeps the per-user buyer story clean ("runs on the Claude plan you already
have; no separate metered agent credit to manage") and reduces the operator's
translation burden of managing a second billing meter (Lens 2 primary-persona +
harness tests). **Lens 1** — the in-session subagent primitive IS the leveraged
Claude-native capability; loam composes on it.

**Ladders to:** AC.RES1.* (Slice 1) → this minor → every later release that fans
out work inherits subscription economics → AC.PO.

---

## §5. Acceptance criteria (Slice 1)

> AC IDs are scope-descriptive (`RES1` = research-slice-1). All ACs
> outcome-shape — they state the observable outcome, never the in-session-
> dispatch *method* (method is the builder's call; tight scope leaves it
> inferable from the constraints). Each AC below is satisfiable by more than one
> dispatch wiring → outcome-shape confirmed.

- **AC.RES1.1 — the production role-research path no longer spawns a detached
  `claude -p` subprocess.** A test exercising the production `ResearchSource`
  (the default, non-injected one) observes that producing a `RawRoleResearch`
  for a role does NOT create a detached `claude -p` child process, AND yields a
  usable three-axis result when an in-session dispatcher is wired. *Outcome, not
  method:* asserts the absence of the `-p` subprocess spawn + presence of a
  usable result; does not prescribe which in-session surface produces it.

- **AC.RES1.2 — the bounded research budget is still enforced.** For any role,
  the produced `RawRoleResearch.total_roundtrips ≤ MAX_RESEARCH_ROUNDTRIPS`; an
  overshoot folds to the marked fallback (the sealed AC.DRR.2 over-reach-guard
  behaviour is preserved through the conversion).

- **AC.RES1.3 — graceful degradation preserved.** When the in-session research
  capability is unavailable (no dispatcher registered, dispatcher raises, or the
  result is unparseable), `research_role` returns the clearly-marked
  `is_stub=True` fallback (never raises, never hangs) — the sealed AC.DRRGRACE.1
  contract holds unchanged across the primitive swap.

- **AC.RES1.4 — subscription-pool billing empirically confirmed (the
  calendar-gated settle).** *DEFERRED MINOR-LEVEL EMPIRICAL GATE — NOT a Slice-1
  code AC and does NOT block this seal.* After June-15-2026, one day of running
  the converted research workload, a `/usage` read shows the workload's tokens
  attributed under the **plan-limits** breakdown and the Agent SDK credit
  **undrawn** by it. Status-file-recorded; closes only post-June-15; gates the
  high-volume Slice 3. **Tracked separately as a minor-level gate — see §9.**

- **AC.RES1.5 — USER NOTICE shipped (outcome-altitude).** The "keep loam open in
  the background to finish while you're away; close it and it pauses" guidance is
  present as a user-facing surface, reachable through the normal user-facing path
  (not buried in code comments). A reader who has never seen the migration learns,
  in plain language, that converted long-running work runs while the session
  stays open and pauses when it closes. **Marked `outcome-altitude: true`** —
  verified by walking the user-facing surface cold, with no pre-arranged state,
  and finding the notice.

**Slice-1 seal closes on: AC.RES1.1, AC.RES1.2, AC.RES1.3, AC.RES1.5.**
AC.RES1.4 is the deferred calendar gate (§9) and explicitly does NOT block.

---

## §6. Build steps (method-level guidance — builder's call per ODD §1.1)

1. Manifest: `docs/plans/claude-p-to-insession-subagent-fanout.manifest.yaml`;
   single-component fence = `framework/workspace-bootstrap/`. BASELINE pins the
   v1.0.1 tip `aa759aa8`.
2. Add the in-session dispatcher seam (process-level registry) + a NEW
   production `ResearchSource` that fulfills research through the registered
   in-session dispatcher; keep the `ResearchSource` Protocol + the budget + the
   parse + the fallback unchanged. Swap `make_default_research_provider` to the
   in-session source. KEEP `ClaudeSubagentResearchSource` (residual mechanism).
3. Narrate the spawn-isolation guard's residual-only role in the converted call
   site (do NOT delete the guard).
4. Ship the USER NOTICE surface (AC.RES1.5).
5. Author tests for AC.RES1.1–.3, .5.
6. `loam amend apply` → tests green → `loam amend seal` → LOCAL only (no push).
   Hold AC.RES1.4 open as the §9 deferred minor-level gate.

---

## §7. Out of scope (Slice 1)

1. Slices 2 + 3 (handsoff-loop swarm core; LitRPG path) — their own
   manifests/seals, serialized after this seal (one git tree; builds race).
2. The launchd-sessionless residual `-p` path — genuinely cannot convert; stays
   metered; covered by the spend-cap.
3. The bench-validity PTY path (`subloam-driver`) — deliberately stays isolated.
4. Deleting `loam_spawn_isolation` — its scope narrows to residual-only but it
   stays load-bearing.
5. The `/usage-credits` spend-cap setup — the contingency bridge, a separate
   ~zero-effort owner action.
6. Pushing the minor to origin — owner-gated release later.

---

## §8. Halt triggers (in-flight conditions that abort the build)

- **H-1 — a sealed honesty control would weaken.** If converting cannot preserve
  the budget / the graceful-degradation fallback without weakening it, HALT.
- **H-2 — the no-API-key invariant is at risk.** If the only viable in-session
  conversion reaches for the `anthropic` SDK / `ANTHROPIC_API_KEY`, HALT.
- **H-3 — the residual-only guard is about to be deleted.** If a build step would
  remove `loam_spawn_isolation` rather than narrow its scope, HALT.
- **H-4 — AC.RES1.4 would block the seal.** If the AC structure forces the
  calendar-gated billing AC to block the Slice-1 seal, HALT and surface the
  ODD-structure issue rather than forcing/faking it.

---

## §9. Deferred minor-level gate (AC.RES1.4) — tracked separately

AC.RES1.4 (post-June-15 `/usage` billing confirmation) is a MINOR-LEVEL deferred
empirical gate, NOT a Slice-1 acceptance criterion. It:
- physically cannot be verified before June-15-2026 (calendar-gated);
- does NOT block the Slice-1 seal;
- is NOT faked to green, NOT stubbed to green;
- gates the later high-volume Slice 3 (H-4 in the parent plan): Slice 3 does not
  build until AC.RES1.4 closes post-June-15.

Recorded in the status file
(`<workspace>/.scratch/claude-output/insession-subagent-migration-status.md`) +
the §14 method-decision register at build time.

---

## §10. F2 Ruthless Feedback (honest doubts + named risks)

- **RF-1 — the feasibility doc names a hook that does not exist as a hook.** The
  feasibility doc calls the isolation guard a "`claude_spawn_isolation_guard.py`
  PreToolUse hook." VERIFIED this session: there is no such hook in
  `/Users/lukeivers/loam/.claude/`; the enforcement is the in-code
  `assert_loam_spawn_isolated` function in
  `framework/tools/loam-spawn-isolation/src/loam_spawn_isolation/__init__.py`.
  The plan names the verified surface (the in-code function) as the thing whose
  scope narrows.

- **RF-2 — the standalone provider is not itself a Claude session.** The
  `claude -p` shell-out exists precisely because plain Python cannot import the
  Task tool. The in-session conversion therefore needs the live host session to
  inject its dispatcher — there is no way for the provider to "become"
  in-session by itself. The seam (a registered dispatcher callable) is the
  honest shape of that: when no live session wired one, the provider degrades to
  the fallback (AC.RES1.3), exactly as it does today when `claude` is absent.

- **RF-3 — the residual is real; the migration does NOT cover 100%.** The
  launchd auto-restart path has no interactive parent at restart time. Named as
  the honest residual; covered by the spend-cap; framed as "the convertible
  majority," not "all of it."

- **RF-4 — the economic premise is high-confidence-not-certain until one
  calendar-gated read.** Gate the high-volume Slice 3 behind AC.RES1.4; build
  Slice 1 (low blast radius) ahead of the gate but do not close the billing AC.

- **RF-5 — "keep a session open overnight" is a behavioural change.** Converted
  long-running work runs only while the parent session lives. Ship the USER
  NOTICE (AC.RES1.5) as a first-class deliverable.

---

## §11. Provenance trail (Tier-0, verified against the territory this session)

- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/deep_role_research_provider.py`
  — CONFIRMED `ClaudeSubagentResearchSource.research` spawns
  `spawn_isolated_claude(["claude","-p",…])` (L259–311); injectable
  `ResearchSource` Protocol + `MAX_RESEARCH_ROUNDTRIPS=3` budget +
  `_fallback_result(is_stub=True)` graceful-degrade all present. Slice-1
  conversion target confirmed.
- `framework/workspace-bootstrap/tests/test_AC_DRR_deep_role_research_provider.py`
  — CONFIRMED the deterministic-source seam pattern (`DeterministicSource`,
  `UnavailableSource`, `OverBudgetSource`) that drives the real provider
  end-to-end without a network call; the AC.DRR.* / AC.DRRSEAM.* / AC.DRRGRACE.*
  / AC.DRROUT.* families stay green by construction across the swap.
- `framework/tools/loam-spawn-isolation/src/loam_spawn_isolation/__init__.py` —
  CONFIRMED the chokepoint + the in-code `assert_loam_spawn_isolated` guard
  (L211–254). No PreToolUse hook exists for this (RF-1).
- loam HEAD at authoring: `aa759aa8` (v1.0.1 post-publish backfill tip) — the
  clean released tip this minor builds on.

**Convention exemplar:** `plugins/dev-sdlc/docs/conventions/plan-docs.md`
(plan-doc shape, scope-descriptive AC IDs, manifest fields). Shape exemplar:
recent single-component manifests under `docs/plans/`.
