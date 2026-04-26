# Research — bootstrap-progress visualization in Claude Code's terminal status line

**Authored:** 2026-04-26.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Governs plan:** `docs/rebuild/plans/bootstrap-progress-statusline.md`.
**Owner directive:** locked 2026-04-26 — surface = Claude Code terminal status line via project-scoped `.claude/settings.json` `statusLine`; refresh = file-polled at 1 s; active during bootstrap only; non-tech audience; workspace-scoped.

This document is the research-before-plan artefact required by the FUTURE_IDEAS "research before plan for non-trivial new work" CDC. The work is a net-new cross-component visibility surface composed onto a Claude Code primitive nobody in pos-v2 has used yet, so the CDC's "non-trivial new work" branch applies. Sized proportionately: behavioural questions on the status-line primitive are already answered in `/Users/lukeivers/pos3/.scratch/claude-output/claude-code-statusline-research.md` (cited here, not duplicated); this doc covers the pos-v2-side decisions the existing status-line research left open.

---

## 1. Summary

A small status-line script (≈ 30–60 lines) reads a JSON state file the existing detached first-run worker already updates at every phase boundary (via `first_run_state.write_state`) and renders a one-line plain-English progress string. Claude Code re-runs the script every 1 s while the status-line config sets `refreshInterval: 1`, so the user sees live progress in the terminal during the 30 s–8 min cold-cache first-run window without tailing logs or re-opening sessions. After bootstrap completes, the same script renders a brief steady-state line OR clears, per a flagged decision below.

The state surface required to drive the status line **already exists**: `<workspace>/.pos/first-run.state` (amendment #28's workspace-local routing) carries `status`, `phase`, `detail`, `started_at`, `updated_at`, `pid`, `generation`, `error_code`, `remediation`, `workspace_root` — fields the worker writes at every phase transition. No new schema is strictly required; the amendment can compose entirely on top of the existing file. A small additive field (`progress_pct: int` or equivalent) is one of the flagged decisions below; the rest is rendering + settings.json wiring + a new sealed-component fence question (which component owns the script).

---

## 2. Three-lens research questions

### Lens 1 — Claude-leverage-first

**What Claude capability does this lean on or extend?** Claude Code's `statusLine` setting (project-scoped via `.claude/settings.json`), which spawns a shell command with a short JSON envelope on stdin and renders the script's stdout at the bottom of the terminal. The primitive supports event-driven re-run plus configurable polling (`refreshInterval` in seconds, minimum 1). No re-implementation; the amendment composes on top of an existing primitive.

Citation: `/Users/lukeivers/pos3/.scratch/claude-output/claude-code-statusline-research.md` §§1–7. Notably:

- Per-project precedence is supported (§6) — workspace-local `.claude/settings.json` overrides user-global, exactly the boundary the owner directive locks.
- `refreshInterval: 1` is the minimum and behaves as polling even when no message events fire (§3) — necessary because SessionStart's hook fires once and no further events drive re-runs while the worker installs.
- Non-zero exit blanks the status line (§7) — graceful degradation is built-in.
- Workspace-trust gate (§7) — the very first session in a fresh clone may show "statusline skipped · restart to fix" until the user accepts trust. Acceptable: the trust prompt is itself part of the first-session UX and the user is already in a session-start UI moment.

### Lens 2 — Harness + primary-persona value

**Primary-persona test (translation burden):** the user's natural-language intent here is implicit — *"tell me what's happening so I know whether to wait or whether something's stuck."* Today, a non-tech user sees Claude Code open, gets a one-shot SessionStart `additionalContext` paragraph that names the log file, then sees nothing for 30 s–8 min. They cannot translate "log file at this path" into "tail it in another terminal" — and even if they could, that's the very translation work pOS exists to remove. A status-line surface eliminates the translation: the answer is on screen, ambiently, in plain English. **Pass.**

**Harness test (toolkit the persona draws from):** the status line is a primary-persona-invokable surface — the persona doesn't compose against it directly today, but the underlying state file the script reads (`first-run.state`) is already a harness artefact the persona reads via the existing `_msg_still_running` / `_msg_completed` path. The persona's tool kit grows by the new rendering surface (the persona's session-start `additionalContext` payload could later compose with the same state file to mirror the status line in chat when relevant). The harness test is satisfied as long as the script's state-file read is deterministic, schema-versioned, and reusable — which it already is. **Pass.**

### Lens 3 — ODD authoring

ACs are outcome-shaped (state-of-the-world after bootstrap fires + status-line renders + state-file content); no method prescribed in the AC text. Method-level decisions (script language, file path, atomicity strategy, post-completion rendering) live in the plan's "method-level decisions" section, not in ACs. §2.5 reverse direction: every code path the amendment introduces traces to a named AC. Tightened in the plan.

---

## 3. State-file schema design

### 3.1 Existing surface (amendment #28's `FirstRunState`)

The `FirstRunState` dataclass at `hands-off-lifecycle/hooks/first_run_state.py` lines 84–138 already carries:

| Field | Type | Source | Role for status line |
|-------|------|--------|----------------------|
| `status` | str (`starting` / `running` / `completed` / `failed`) | written at every `_advance_state` call | drives the active/inactive branch |
| `phase` | str (e.g. `phase-3b-shared-deps`, `phase-4b-health-poll`, `complete`) | written at every phase boundary | source for the human-readable phase label |
| `detail` | str (free-form, one line) | written at most boundaries | source for trailing detail in the rendered line |
| `started_at` | float (UTC unix seconds) | written at first `write_state` | drives elapsed-seconds display |
| `updated_at` | float | written at every `write_state` | drives staleness detection |
| `pid` | int | written at spawn | drives liveness probe (status line can detect silent death the same way the dispatcher does) |
| `generation` | int | written at every spawn | drives `[gen3]` badge if a respawn happened |
| `error_code` | int | written on failure | drives the failure-line variant |
| `remediation` | str | written on failure | renderable directly to the status line |
| `workspace_root` | str | written on every save | refused by the dispatcher when foreign; status line can apply the same defence-in-depth check |

### 3.2 What the status line needs that the state file already gives

All of the rendering inputs (status, phase, detail, started_at, error_code, remediation) are present today. The phase strings are technical-shaped (e.g. `phase-3b-shared-deps`, `phase-4c-agent-file-authorship`) and need a translation layer at render time — that's the script's job, not a schema change. **Recommendation: do not change the dataclass shape; add a phase→human-readable-label map inside the renderer.**

### 3.3 Optional additive field — `progress_pct`

A `progress_pct: int` (0–100) field is tempting for the rendered "▓▓▓░░░ 45%" bar shape the prior research suggested. Two paths:

- **(a) Add the field to `FirstRunState`** and populate it at each `_advance_state` call site in `first_run_helper.py` based on a static phase→percentage map. **Recommendation: yes, but as a plan-time decision, not a research-time prescription.** It costs ~10 LOC in the worker; it makes the rendered line measurably better for non-tech users (a percent is cognitively cheaper than a phase label); it's an additive schema change (defaulted, backwards compatible) so consumers that don't know about it see the existing fields unchanged.
- **(b) Compute the percentage in the renderer** from a phase→pct table local to the script, using only the existing `phase` field. Cheaper to land, no schema change, but the percentage definition lives in the renderer side. **Acceptable fallback if Owner prefers a strict no-state-file-schema-change posture.**

Recommended: **(a)** — schema change is small, additive, and centralises the canonical per-phase progress definition where the worker can update it as phases change.

### 3.4 Atomicity (worker may crash mid-write)

The existing `write_state` is atomic by construction — `tmp.write_text` then `os.replace(tmp, p)` (lines 209–211 of `first_run_state.py`). POSIX `rename()` within a single filesystem is atomic, so a status-line script reading the file always sees either the prior snapshot or the new one, never a half-written file. **No new atomicity work required.**

A worker that crashes between `tmp.write_text` and the rename leaves a `<file>.tmp` sibling and the prior `<file>` intact; the renderer reads `<file>` and is unaffected. A worker SIGKILL'd between `write_state` calls leaves the *prior* state visible, with a stale `updated_at` — the renderer can detect "stale + status=running" the same way `is_stale_live_state` (line 257 of `first_run_state.py`) does. **Recommendation: the renderer mirrors the dispatcher's `is_stale_live_state` logic; if the worker died silently, render "first-run stalled — reopen Claude to retry" instead of the last-seen phase.**

### 3.5 File location

The state file is **already** at `<workspace>/.pos/first-run.state` per amendment #28 (workspace-local routing). The status-line script needs one of:

- The absolute workspace path resolved from Claude Code's status-line stdin envelope. The envelope carries `workspace.current_dir` and `workspace.project_dir` (per `claude-code-statusline-research.md` §2). **Recommendation: read `.workspace.project_dir` from stdin JSON, append `/.pos/first-run.state`.** This is portable across host and across Claude Code's "open in subdirectory" mode.
- An environment variable — rejected; the status-line process inherits Claude Code's env, which doesn't include `POS_V2_REPO`.
- A symlink at a known path — rejected; introduces a second source of truth.

`HOME-vs-workspace-local` for the state file itself is **not the active question** — amendment #28 settled it (workspace-local). Owner's directive references `~/.pos3-bootstrap-state.json` only as a strawman; the canonical path the worker already writes is `<workspace>/.pos/first-run.state`, and the script reads from there. **Flag for owner ruling: confirm we use the existing workspace-local path rather than introducing a parallel state file.**

---

## 4. Status-line script language

Two viable choices:

### 4.1 Bash + `jq`

The prior research's recommended shape (`claude-code-statusline-research.md` §"Recommended Implementation"). Pros: minimal cold-start cost (~10 ms vs Python's ~50 ms), no venv dependency, every Mac has bash. Cons: requires `jq` (not on every default macOS install — Sonoma+ ships it, but pos-v2 supports macOS broadly), error-handling is verbose, Unicode rendering for any progress-bar glyphs is brittle in pure shell.

### 4.2 Python (stdlib only)

Pros: stdlib `json`, `pathlib`, `time`, `sys` cover everything; matches the rest of pos-v2's hooks (every other `hands-off-lifecycle/hooks/*.py` is Python 3.13 stdlib-only); no `jq` dependency; can reuse `first_run_state.read_state` directly. Cons: ~50 ms cold start, ~50 ms × every 1 s = 5% baseline CPU during bootstrap (negligible).

**Recommendation: Python 3.13 stdlib-only.** Three reasons:

1. **Reuse.** The script can `from first_run_state import read_state, is_stale_live_state` and inherit the existing parsing + stale-detection + workspace-identity-defence-in-depth logic. Re-implementing those in bash duplicates the contract.
2. **Consistency.** Every other hand-off-lifecycle hook is Python; sticking with bash here would require the maintenance overhead of two languages on the same surface.
3. **No new dependency.** `jq` would be a new install-time precondition pos-v2 doesn't currently require. Adding one for status-line cosmetics fails the harness test.

The Python interpreter resolution mirrors `first-run.sh`'s detection (line 87–129 of `first-run.sh`): `POS_V2_PYTHON` env var → `python3.13` on PATH → Homebrew paths → `python3` if 3.13+. The status-line command in `.claude/settings.json` references the script directly; on the first session before the venv exists, the system Python 3.13 runs it; after the venv exists, settings.json could be rewritten to reference `<workspace>/.venv/bin/python` for speed (post-completion rewrite is part of the worker's existing self-retire path, so this composes cleanly).

**Cold-start (pre-venv) caveat.** On the very first session in a fresh clone, `<workspace>/.venv/` does not yet exist, so the status-line command must use the system Python interpreter. The plan must declare which interpreter the settings.json `statusLine` command names: the system `python3.13` (matching `first-run.sh`'s detection chain) until first-run completes, then optionally rewritten to the venv Python after completion. Flagged in the plan.

---

## 5. Failure modes and rendering

### 5.1 State file missing

Two cases distinguishable by surrounding paths:

- **(a) Brand-new workspace, hook hasn't fired yet.** `<workspace>/.pos/` doesn't exist. Render nothing (empty status line). Recommendation: empty stdout, exit 0. Status line goes blank — which is the natural Claude Code behaviour for "no script output" and matches the existing UX (you don't see a progress indicator until the hook actually starts).
- **(b) State file deleted mid-flight.** Should not happen (the worker writes it; nothing else deletes it). If it does, treat as case (a) — empty render.

### 5.2 State file present, status `starting` or `running`, pid alive

Render the active progress line. Recommended shape (flagged for owner refinement):

```
pos-v2 setting up · phase-3b-shared-deps · 1m32s elapsed · ~3 min remaining
```

In plain English, no JSON keys. Phase label translated via the script's phase→label table (step name in plain English, e.g. `phase-3b-shared-deps` → "installing shared dependencies"). Elapsed seconds computed from `started_at`. "Remaining" estimate from the static phase→duration table (calibrated against the helper's own internal duration cap of "~5 minutes total" already advertised in `_msg_fresh_start`).

### 5.3 State file present, status `running`, pid dead (silent death)

Render: `pos-v2 first-run stalled — reopen Claude to retry`. The dispatcher will respawn on the next SessionStart; the renderer's job is to communicate the stall to a user who's mid-session.

### 5.4 State file present, status `failed`

Render: `pos-v2 first-run failed — see status` or similar one-line variant of the dispatcher's `_msg_failed` paragraph. Full remediation reaches the user via the SessionStart `additionalContext` already (path that's unchanged). The status-line variant is a glanceable summary.

### 5.5 State file present, status `completed`

Two sub-cases:

- **(a) Recent completion, same session.** Render a brief "pos-v2 ready" line for visual continuity (the user just watched the bar fill; cutting to blank is jarring). Recommendation: render this for ~60 s after `updated_at`, then go blank.
- **(b) Old completion, future session.** Render nothing — the workspace is fully bootstrapped, the status line should not advertise it forever.

This is the **owner-flagged "clear vs steady-state" decision** — a steady-state line ("pos-v2 ready") is one option, blank is another. The recommendation above is a hybrid: brief steady-state for visual continuity then blank. Either pure-blank or pure-steady-state would also be defensible; flagged in the plan.

### 5.6 Foreign workspace state (defence in depth)

The status-line script reads `.workspace.project_dir` from stdin JSON, derives the state-file path from it, and reads. The state file's `workspace_root` field should match the resolved project_dir (per amendment #28 line 267–289). If it doesn't (e.g., a state file that was moved across workspaces), treat as case 5.1 (a) — empty render. Avoids cross-workspace cross-talk, mirrors the dispatcher's `_state_belongs_to` check.

---

## 6. Interaction with hands-off-lifecycle's existing supervisor stanza

Three settings.json stanzas need to coexist:

1. **`hooks.SessionStart`** — already managed by `first_run_settings.py::merge_session_start` (amendment #45 generalised to multi-contributor). The status line is **not** a hook; it's a top-level `statusLine` field. They don't conflict.
2. **`hooks.UserPromptSubmit`** — managed by `merge_user_prompt_submit` (amendment #46). Also doesn't conflict.
3. **`statusLine`** — new top-level key, added by this amendment. Recommendation: new `merge_status_line` function in `first_run_settings.py` that mirrors the merge convention — back up user-authored `statusLine` if present, replace with pos-v2's value, atomic write.

A user who already has a `statusLine` in their workspace `.claude/settings.json` (uncommon but possible — e.g. a forked statusline-cost-tracker script) gets the same treatment as a user-authored SessionStart stanza: their settings.json is backed up, and pos-v2 wins. The confirmation sentence the worker emits names the displacement.

The first-run shell script (`first-run.sh`) already writes `.claude/settings.json` via `first_run_settings.merge_session_start`. The status-line stanza needs to be written at the **same point**: when the framework first establishes the bootstrap-time settings.json (the worker's Phase 6 self-retire is the only path that mutates it post-detachment). Recommendation: write the `statusLine` entry once, at the same write-point as the SessionStart stanza, using the new `merge_status_line` function. Survives post-completion (because the same script keeps rendering — case 5.5).

The settings.json fragment also needs a sealed-fragment counterpart at `hands-off-lifecycle/hooks/settings.json.fragment` that documents the post-self-retire shape including the `statusLine` field, mirroring the existing fragment's role as the authoritative reference for the post-self-retire shape.

---

## 7. Post-completion behaviour — clear vs steady-state

Three options:

- **(a) Clear immediately on `status=completed`.** Cleanest UX surface; no information after the work is done. Drawback: the user who just watched the bar fill sees it disappear instantly, which is mildly disorienting.
- **(b) Steady-state line forever.** "pos-v2 ready" or similar persists across all future sessions. Drawback: the harness owns a non-trivial slice of the user's terminal real estate forever, for a feature that has no remaining function.
- **(c) Brief steady-state (~60 s post-completion), then clear.** Visual continuity for the user mid-session; cleanup for steady-state. The 60-s window is computed from `updated_at` (the timestamp of the `status=completed` write).

**Recommendation: (c).** Owner-flagged for refinement; defensible alternatives are (a) and (b). The recommendation cost is one extra branch in the renderer and a one-line `time() - state.updated_at < 60` check.

After the brief steady-state expires, the status line returns to blank — the script writes nothing to stdout, exit 0. Future sessions read the same `status=completed` state; their elapsed-since-completion is large; they render blank. Self-retiring at the rendering layer.

A second consideration: if the user runs `pos-v2 self-upgrade` later, a future `status=running` could appear in the same state file (the upgrade re-runs first-run-style work). Status-line behaviour automatically resumes — no additional code needed; the state-file-driven design is naturally idempotent for that case. **No special handling required for the self-upgrade case.**

---

## 8. Backwards-compat on existing workspaces

### 8.1 An existing workspace whose state-file emitter pre-dates this amendment

The state-file shape is unchanged (option 3.3 (a) is additive: a new `progress_pct` field defaulted to 0). A workspace whose worker hasn't been re-run since the amendment landed — i.e. its first-run is already complete and its state file says `status=completed` from a prior worker version — has no `progress_pct` field; its renderer reads 0 and treats it as "unknown progress, fall back to phase label only." The completion case (5.5) doesn't need progress_pct at all. **No migration, no breakage.**

### 8.2 An existing workspace whose `.claude/settings.json` does not have the `statusLine` field

That workspace's status line stays exactly as it was — blank, or whatever the user previously had. The amendment's only path to landing the `statusLine` config is via the worker's `merge_status_line` call, which fires only on workers that have the new code. Old workspaces that ship pre-amendment get the new config the next time their first-run worker runs (which for a completed workspace is never). **Recommendation: ship a small one-shot bootstrap-progress retrofit path in the worker — when an existing worker whose first-run already ran detects no `statusLine` field, write it.** Cheap (one extra check at worker startup), composes with the self-retire pattern.

For pos3 specifically (which already has its first-run completed but may not see this amendment's changes until a fresh hook fires): the supervisor path doesn't run the status-line installer today. **Recommendation:** add the `merge_status_line` call to `pos_session_start.py`'s settings-touch path so a workspace that's already past first-run picks up the new statusLine entry on its next session-start. Fail-soft if the merge call raises (don't block the supervisor on a status-line install bug).

### 8.3 An existing workspace with a user-authored `statusLine`

Treated the same as a user-authored SessionStart stanza (per §6) — backed up, pos-v2 wins, displacement surfaced in the confirmation. The user can restore their prior status-line script from the backup if they want.

---

## 9. Component fence — which sealed component owns what

The work touches at minimum two sealed components:

- **`hands-off-lifecycle/`** — the `merge_status_line` settings-merge logic + the settings.json fragment update + (possibly) the supervisor's retrofit-on-existing-workspace path. The settings.json wiring is firmly in this component's territory because amendments #45 and #46 already established that pattern here.
- **`workspace-bootstrap/`** — *iff* the `progress_pct` schema field lands as decision 3.3 (a). The state-file dataclass `FirstRunState` lives at `hands-off-lifecycle/hooks/first_run_state.py`, **not** under workspace-bootstrap, so even the schema change is hands-off-lifecycle-internal. Workspace-bootstrap is touched only if the scaffold-time settings.json templating (the `first_run_settings.py` writer-path) needs to learn the statusLine field. That writer is invoked from workspace-bootstrap's `first_run_scaffold.py` (line 1163-onwards) only via the worker, not directly — so the amendment's actual touch is in hands-off-lifecycle and *not* workspace-bootstrap.

The status-line **renderer script** itself is new code. Three placement options:

- **(a) `hands-off-lifecycle/hooks/statusline.py`** — co-located with the other hook scripts. Reuses `first_run_state.read_state`. **Recommendation.**
- **(b) New sealed primitive `bootstrap-progress/`** — overkill. The renderer is ≤ 100 lines, has no API surface, is consumed only by Claude Code's status-line primitive.
- **(c) Under `workspace-bootstrap/`** — the workspace bootstrap component is the framework that orchestrates first-run; the renderer is downstream of that framework's state. Misplaced.

**Recommended fence: hands-off-lifecycle only.** No new sealed-component primitive, no workspace-bootstrap edits.

If decision 3.3 lands as **(b)** instead of (a) (no schema change, percentage in renderer), the fence is still hands-off-lifecycle only.

---

## 10. Halt-and-surface candidates

The plan author should halt and surface to the owner if research surfaces:

- A Claude Code statusLine schema change since the prior research doc (recheck the doc URL: `https://code.claude.com/docs/en/statusline.md`).
- An existing pos-v2 component already uses statusLine for some other purpose (grep `statusLine` in canonical-pos-v2 — pre-emptive check before plan dispatch).
- The owner-locked "active during bootstrap only" requirement conflicts with a feature the user has come to rely on (e.g., a third-party statusline script the user hasn't surfaced).
- Cross-cutting overlap with the in-flight `memory-system-live-client-and-stop-hook-write` amendment (verified at research time: that amendment touches only `Stop` hook + memory-system internals, not the SessionStart / settings.json surface this work touches; **no conflict identified**).

---

## 11. Decisions surfaced for owner ruling

Listed once here, restated in the plan's Decisions section:

1. **Schema change for `progress_pct`?** Recommendation: **(a)** add the field (additive). Alternative: **(b)** compute percentage in the renderer.
2. **Post-completion rendering — clear vs steady-state?** Recommendation: **(c)** brief steady-state (~60 s) then clear. Alternatives: pure-clear (a), pure-steady-state forever (b).
3. **State-file path source.** Recommendation: read from stdin JSON's `.workspace.project_dir`. Alternative (rejected): env var.
4. **Status-line script language.** Recommendation: Python 3.13 stdlib. Alternative: bash + jq.
5. **Existing-workspace retrofit.** Recommendation: add `merge_status_line` to the supervisor path so a workspace already past first-run picks up the config on its next session. Alternative: no retrofit; only fresh first-run sessions get the config.
6. **Phase→duration estimate calibration.** Recommendation: static table seeded from observed mean durations on a cold-cache fresh clone. Alternative: dynamic (last-N-runs moving average) — defer.

---

## 12. Out of scope

- **A general framework for arbitrary worker progress.** The status-line script is scoped to first-run. Future workers (e.g. self-upgrade) compose against the same state-file shape; no generalised progress framework lives in this amendment.
- **Telegram / Claude-app surfaces.** Only the terminal status-line is in scope. The state file is reusable by other surfaces (the persona's `additionalContext` could mirror it), but those surfaces are out of scope.
- **Phase enrichment for completion-time estimates.** "About 3 minutes remaining" is a static table; per-phase duration calibration is out of scope.
- **Animation / spinner frames.** Status-line refreshes at 1 Hz; spinner-style animation is out of scope.
- **Claude Code SDK / plugin packaging.** This is workspace-scoped settings.json + a script. Not a plugin.

---

## 13. References

- `/Users/lukeivers/pos3/.scratch/claude-output/claude-code-statusline-research.md` — Claude Code status-line behavioural research (read in full; cited throughout this doc).
- `hands-off-lifecycle/hooks/first_run_state.py` — `FirstRunState` dataclass, `read_state`, `write_state`, `is_stale_live_state`, `state_path` per amendment #28.
- `hands-off-lifecycle/hooks/first_run_dispatch.py` — dispatcher's `_msg_*` rendering functions; reference for plain-English style, defence-in-depth `_state_belongs_to` check.
- `hands-off-lifecycle/hooks/first_run_helper.py` — phase boundaries (lines 1382, 1422, 1443, 1505, 1550, 1601, 1657, 1703, 1860, 1890, 1902, 1949) for the phase→label/duration tables.
- `hands-off-lifecycle/hooks/first_run_settings.py` — `merge_session_start`, `merge_user_prompt_submit`, settings.json atomic-write convention (mirror for `merge_status_line`).
- `hands-off-lifecycle/hooks/settings.json.fragment` — authoritative post-self-retire settings.json shape; updated to include the `statusLine` field.
- `docs/rebuild/spec/pos-v2-objectives-spec.md` "Non-tech users" §+v1.0 acceptance — the spec-objective surface this amendment satisfies (low-friction onboarding, persona-in-every-session presupposes the user is *in* the session and not staring at a hung-looking terminal).
- `docs/rebuild/VALUE_PROPOSITION.md` — Lens 2 binding (translation-burden test, harness test).
- `docs/rebuild/plans/amendment-46-persona-session-start-turn-start-emitters.builder-plan.md` — sibling pattern for hook-stanza authoring + ODD shape.
- `docs/rebuild/plans/amendment-28-workspace-identity-routed-first-run.md` — workspace-local `.pos/` state-file routing; the source of truth for the state-file path.
- `docs/rebuild/FUTURE_IDEAS.md` "research before plan for non-trivial new work" CDC — the meta-rule this doc satisfies.
