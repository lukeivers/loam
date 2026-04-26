# Amendment plan — bootstrap-progress visualization in Claude Code's terminal status line

**Amendment number:** unassigned at authoring. Assigned at build-dispatch per owner ruling 2026-04-24.

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

**Authored:** 2026-04-26. **Status:** plan (pre-dispatch). No code, no manifest, no bookkeeping mutations.

**Research:** `docs/rebuild/plans/research/bootstrap-progress-statusline-research.md` (governs this plan).

**Owner directive:** locked 2026-04-26 — terminal status line via project-scoped `.claude/settings.json` `statusLine`; refresh = file-polled at 1 s; active during bootstrap only; non-tech audience; workspace-scoped.

---

## 1. Summary for the owner

A small renderer script reads the per-workspace first-run state file the worker already maintains and prints a one-line plain-English progress string. Claude Code re-runs the script every 1 s while the workspace's `.claude/settings.json` declares a `statusLine` entry pointing at it. While the detached worker installs (30 s–8 min on a cold-cache fresh clone), the user sees a live progress line at the bottom of their terminal — no log-tailing, no wait-and-hope, no guessing. After completion the line briefly displays a steady-state "ready" message then clears.

**Spec-objective binding:** §"Non-tech users" v1.0 acceptance bullet *"every interactive session starts with the primary persona present by default"* presupposes the user reaches the persona-driven session at all — a 5-minute silent terminal violates that presupposition because non-tech users abort before the persona arrives. This amendment is a re-extension of the same low-friction-onboarding objective: the user should know the system is working without the system having to be asked. Lens 2 directly: a feature that translates the user's natural-language need (*"is this stuck?"*) into AI-effective ambient feedback. Method-level decisions are recorded in §6 and live entirely on the builder's side per the scope-only-dispatch CDC.

**Component fence:** `hands-off-lifecycle/` only. `workspace-bootstrap/` is **not** touched. No new sealed-component primitive.

**Decisions surfaced:** six. See §10.

---

## 2. Objective

Make first-run bootstrap progress automatically visible in the Claude Code terminal so a non-technical user knows what is happening (and roughly how much longer it will take) without asking, opening logs, or running diagnostics. Specifically:

1. While the detached first-run worker is in flight, the terminal status line continuously displays a plain-English line naming the current phase, time elapsed, and rough remaining estimate.
2. When first-run completes successfully, the status line briefly shows a "ready" steady-state then clears on subsequent sessions.
3. When first-run fails, the status line shows a glanceable summary of the failure; the full remediation reaches the user via the existing SessionStart `additionalContext` channel.
4. The behaviour is workspace-scoped — pos-v2's status-line presence is confined to `.claude/settings.json` inside the workspace, not the user's global settings.

The objective is satisfied by composition on Claude Code's `statusLine` primitive plus a renderer that reads the existing `<workspace>/.pos/first-run.state` file. No new state surface is introduced; the only new artefacts are the renderer script and a settings-merge function.

---

## 3. Three-lens analysis

### Lens 1 — Claude-leverage-first

The work composes on Claude Code's `statusLine` setting, a Claude-native primitive that runs an arbitrary script every 1 s (or event-driven) and renders its stdout at the terminal bottom. The amendment writes ~ 0 lines of "render to terminal" code; Claude Code does that. The amendment writes ~ 50–100 lines of "read the state file and produce one line of plain English." Re-implementation cost: zero.

The same primitive is also leveraged for graceful failure (non-zero exit → blank status line) and per-project precedence (workspace-scoped settings.json overrides user-global) — both the owner directive and Lens 1 align on those.

### Lens 2 — Harness + primary-persona value

**Primary-persona test (translation burden):** the user's intent is *"tell me whether this is working."* Today they cannot translate a "see ~/.pos/first-run.log" instruction into useful action without leaving the Claude Code session. The status line removes that translation burden entirely — the answer arrives without the user requesting it. **Pass.**

**Harness test (toolkit the persona draws from):** the renderer reads `FirstRunState` — an existing harness primitive — and writes to a Claude-native channel. The persona's session-start `additionalContext` continues to compose against the same state file (the dispatcher's `_msg_still_running` and `_msg_completed` paths read it today). The toolkit grows: any future persona contributor can read the same state file to mirror progress in chat. **Pass.**

### Lens 3 — ODD authoring

ACs are outcome-shaped (state-of-the-world after worker advances + script renders + user sees expected line). Method-level decisions live in §6, not in ACs. §2.5 reverse direction: every code path traces to a named AC; called out explicitly in §11.

---

## 4. Acceptance criteria (outcome-shaped)

Cited as `AC.SL.x` in this plan; final IDs are assigned by `pos-amend` at apply-time per the existing convention.

| AC | Outcome | Test shape |
|----|---------|------------|
| AC.SL.1 | When the first-run worker is in flight (state-file `status` ∈ {`starting`, `running`}) for a workspace whose `.claude/settings.json` declares the pos-v2 `statusLine` entry, an invocation of the renderer script with a stdin envelope naming that workspace produces stdout containing the workspace's current phase translated to a plain-English label, an elapsed-seconds figure derived from `started_at`, and (when known) a remaining-time estimate. Output ≤ 200 chars; exit 0. | One unit test per state-file fixture (one per phase the worker writes); each asserts the rendered line contains the phase's plain-English label, an `Xm Ys` token, and an estimate token, all within 200 chars. |
| AC.SL.2 | When the worker has just completed (state `completed`, `updated_at` within the last 60 s) the renderer produces a "ready"-shaped steady-state line ≤ 200 chars, exit 0. When the worker completed more than 60 s ago, the renderer produces empty stdout, exit 0. | Two unit tests over completed-state fixtures with synthesised `updated_at` (now-30s and now-3600s). |
| AC.SL.3 | When the state-file `status` is `failed`, the renderer produces a glanceable failure line containing a plain-English summary derived from the file's `detail` field (no traceback, no JSON keys, ≤ 200 chars) and exits 0. | One unit test over a failed-state fixture; asserts presence of plain-English failure phrasing and absence of `error_code` numeric prefix. |
| AC.SL.4 | When the state-file is absent OR contains a `workspace_root` that does not match the stdin envelope's workspace path, the renderer produces empty stdout, exit 0. | Two unit tests: (a) absent file, (b) foreign-workspace fixture. |
| AC.SL.5 | When the state-file's `status` is `running` or `starting` and the recorded pid is not alive AND the most-recent `updated_at` is older than the dispatcher's `is_stale_live_state` grace window, the renderer produces a one-line stalled-summary instructing the user to reopen Claude (≤ 200 chars), exit 0. | One unit test over a stale-live-state fixture (pid=1 — kernel pid, never alive in our process tree; or a non-existent pid). |
| AC.SL.6 | After the first-run worker completes its self-retire on a fresh-clone bootstrap, the workspace's `.claude/settings.json` contains a top-level `statusLine` entry whose `command` field references the renderer script's absolute path, whose `type` is `command`, and whose `refreshInterval` is 1. | Integration test: simulate a worker self-retire (existing fixture in `hands-off-lifecycle/tests/`), assert post-state of settings.json. |
| AC.SL.7 | A workspace whose `.claude/settings.json` already carries a user-authored `statusLine` entry has that entry preserved by writing the entire prior settings.json to a timestamped backup before the merge replaces it; the new pos-v2 entry is in place after the merge. | One unit test on `merge_status_line` with a fixture user-authored `statusLine` value; assert backup file written and pos-v2 entry installed. |
| AC.SL.8 | A workspace that has already completed first-run before this amendment landed (its state-file says `status=completed`, no `statusLine` entry in its `.claude/settings.json`) gains the `statusLine` entry on its next supervisor-path session-start, without re-running first-run. | Integration test: fixture workspace with completed-state and settings.json without `statusLine`; invoke the supervisor path; assert post-state contains the entry. |
| AC.SL.9 | The renderer script's runtime dependencies are limited to the Python standard library (no `pip install` required to run it). | Static check / import audit run from a no-deps Python interpreter. |
| AC.SL.S | The amendment's seal-diff is confined to `hands-off-lifecycle/` and `docs/rebuild/plans/`. No edits to `workspace-bootstrap/`, `primary-persona/`, or any other sealed component. | Existing seal-diff harness (`test_no_sealed_amendments.py` per touched component, plus `hands-off-lifecycle/tests/test_cross_cutting.py`'s H19). |

Behaviour count: AC.SL.1 declares three behaviours (label, elapsed, estimate) — verified by a multi-clause test. AC.SL.2 declares two behaviours (steady-state inside 60 s, blank outside) — verified by two tests. All other ACs are single-behaviour. Counts match.

---

## 5. Hard constraints

- **Budget:** ≤ 1 day wall-clock for the build agent. Renderer + merge function + tests is a small surface.
- **Reversibility class:** fully reversible. Removing the `statusLine` entry from settings.json restores the prior UX; deleting the renderer script makes Claude Code blank the line; no migrations, no schema breakage (the additive `progress_pct` field, if landed, is defaulted).
- **Dependency fence:** consumes `hands-off-lifecycle/hooks/first_run_state.py` (read-only — no public surface change to `FirstRunState` unless decision D1 lands as (a), in which case the schema gains one defaulted optional field). May not amend any sealed component except `hands-off-lifecycle/`. Renderer script stdlib-only.
- **Authority bound:** the builder may make all method-level choices (script layout, label table, estimate-table calibration values) without escalation. The six surfaced decisions in §10 are owner-ruling-required before dispatch.
- **Fail-closed direction:** any failure in the renderer (state file unreadable, JSON parse error, unexpected schema) produces empty stdout + exit 0 → blank status line. Never raises, never blocks, never spams the terminal.
- **Side effects:** the renderer is a pure stdin→stdout function. The merge function is a single atomic settings.json write via `.tmp` + rename. No other filesystem mutation.

---

## 6. Method-level decisions (D-build.x — builder authority)

These are not ACs. They record the intended method so the build agent's plan composes directly on this document.

- **D-build.1 — Renderer language and interpreter resolution.** Python 3.13 stdlib-only. The settings.json `statusLine.command` is `<resolved-python> <renderer-path>`. The script picks `<resolved-python>` at install time — same detection chain as `first-run.sh` (line 87–129): `POS_V2_PYTHON` env → `python3.13` → Homebrew → `python3` (verified ≥ 3.13). Post-completion the supervisor's settings-touch optionally rewrites the command to use `<workspace>/.venv/bin/python` for cold-start latency reduction; this is method, not AC.
- **D-build.2 — Renderer location.** `hands-off-lifecycle/hooks/statusline.py`. Reuses `first_run_state.read_state`, `first_run_state.is_stale_live_state` and a small phase→label / phase→duration table local to the script.
- **D-build.3 — Settings.json merge function.** New `merge_status_line(*, settings_path, new_entry, now_iso=None)` in `first_run_settings.py`. Mirrors `merge_session_start` and `merge_user_prompt_submit`: backs up user-authored entry to `<settings>.user-backup-<ts>.json`, replaces with pos-v2 entry, atomic `.tmp` + rename. Operates on the top-level `statusLine` field, not under `hooks`.
- **D-build.4 — Settings fragment update.** `hands-off-lifecycle/hooks/settings.json.fragment` adds the canonical `statusLine` shape alongside the existing `hooks.SessionStart` reference. Sealed-fragment role unchanged: it documents the post-self-retire reference shape, not a hand-merge recipe.
- **D-build.5 — Worker integration.** `first_run_helper.py`'s Phase 6 self-retire path calls `merge_status_line` once, alongside the existing `merge_session_start` call. The supervisor's settings-touch path (`pos_session_start.py`) gains the same call so existing-workspace retrofit works (per decision D5).
- **D-build.6 — Phase→label table.** Static dict in the renderer. Phase keys are the existing strings the worker writes (`phase-2-venv-creation`, `phase-3a-inventory`, `phase-3b-shared-deps`, `phase-3c-dedicated-venvs`, `phase-3e-editable-installs`, `phase-4a-scaffold`, `phase-4b-health-poll`, `phase-4c-agent-file-authorship`, `phase-5-confirmation`, `phase-6-self-retire`, `complete`). Labels in plain English (e.g., "creating Python environment", "installing shared dependencies", "writing config files", "starting background services", "finishing up"). Builder calibrates labels for non-tech readability.
- **D-build.7 — Phase→duration estimate table.** Static dict, seeded from the helper's own already-advertised "~5 minutes total" figure plus the worker's own per-phase wall-clocks. Calibration is method-level — the builder may adjust the table without owner escalation. Future iteration via dynamic last-N-runs averaging is out of scope per §9.
- **D-build.8 — `progress_pct` field, if D1 lands as (a).** Additive `int = 0` field on `FirstRunState`. Worker writes a static-mapped percentage at each `_advance_state` call. Renderer uses it for a `▓░` bar glyph; renderer falls back to no-bar when the field is absent or zero.
- **D-build.9 — Inactivity defence in depth.** Renderer mirrors the dispatcher's `_state_belongs_to(state, project_dir)` check (lines 267–289 of `first_run_dispatch.py`). Foreign or empty-`workspace_root` state → empty render.

---

## 7. Files changed (declared scope)

### `hands-off-lifecycle/hooks/`

1. **`statusline.py`** (NEW) — renderer script. Stdlib-only. Reads stdin JSON, derives state-file path from `.workspace.project_dir`, calls `read_state`, dispatches by `status`, prints one line.
2. **`first_run_settings.py`** (MODIFY) — add `merge_status_line` function (top-level field, mirroring `merge_user_prompt_submit`'s shape). Add `_is_pos_v2_owned_status_line` predicate (recognises pos-v2's renderer command marker — substring match on `hands-off-lifecycle/hooks/statusline.py`). Extend marker constants if needed.
3. **`first_run_helper.py`** (MODIFY) — Phase 6 self-retire path adds one call to `merge_status_line(settings_path=..., new_entry=_status_line_stanza(pos_v2_root))`. New helper `_status_line_stanza(pos_v2_root)` returns the canonical entry. Lazy-import + fail-soft: a failure here does not block self-retire (settings-merge for status-line is additive UX).
4. **`first_run_state.py`** (MODIFY, only if D1 = (a)) — add optional `progress_pct: int = 0` field on `FirstRunState`. Update worker call sites in `first_run_helper.py` to pass the field per `_advance_state` call. **Skipped entirely if D1 = (b).**
5. **`settings.json.fragment`** (MODIFY) — `_comment` extended to mention the `statusLine` field; the JSON shape gains a `statusLine` key documenting the post-self-retire reference shape.

### `orchestrator/scripts/` (read-only check)

6. **`pos_session_start.py`** (MODIFY, **iff D5 = retrofit on**) — supervisor path adds a call to `merge_status_line` so existing-workspace retrofit works (AC.SL.8). Fail-soft: any error skips the merge silently.

### `hands-off-lifecycle/tests/`

7. **`test_AC_SL_1_renderer_active_phases.py`** — covers AC.SL.1 across the phase fixture set.
8. **`test_AC_SL_2_renderer_completion_steady_state_then_blank.py`** — covers AC.SL.2.
9. **`test_AC_SL_3_renderer_failed_glanceable_summary.py`** — covers AC.SL.3.
10. **`test_AC_SL_4_renderer_absent_or_foreign_state.py`** — covers AC.SL.4.
11. **`test_AC_SL_5_renderer_silent_death.py`** — covers AC.SL.5.
12. **`test_AC_SL_6_settings_json_post_self_retire_carries_status_line.py`** — covers AC.SL.6.
13. **`test_AC_SL_7_merge_status_line_backs_up_user_authored.py`** — covers AC.SL.7.
14. **`test_AC_SL_8_supervisor_retrofits_completed_workspace.py`** — covers AC.SL.8 (skipped if D5 = no-retrofit).
15. **`test_AC_SL_9_renderer_stdlib_only.py`** — covers AC.SL.9 (import audit).

### `docs/rebuild/plans/`

16. **`bootstrap-progress-statusline.md`** (this file) — committed as part of the amendment.
17. **`bootstrap-progress-statusline.manifest.yaml`** (NEW at build time) — `pos-amend` manifest naming touched components, baseline + seal SHAs, AC tuple expansions.

### `pos3/` and other clones

**Not touched.** This file is authored only against `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## 8. Validation strategy

1. Plan + manifest authored before any code edit (this file + the manifest at build time).
2. `pos-amend apply --dry-run` against the empty-diff manifest (smoke).
3. Author edits in order: (a) `first_run_state.py` schema (if D1=a), (b) `statusline.py` renderer, (c) `first_run_settings.py::merge_status_line`, (d) `first_run_helper.py` Phase 6 wiring + worker call-site `progress_pct` writes (if D1=a), (e) `settings.json.fragment` doc, (f) `pos_session_start.py` retrofit (if D5=retrofit on).
4. Author tests in matching order; run them as each lands (`<workspace>/.venv/bin/pytest hands-off-lifecycle/tests/test_AC_SL_*.py -q`).
5. Run touched-component full suites (`hands-off-lifecycle/tests/`). Other components run only their `test_no_sealed_amendments.py` (per amendment-dispatch CDC).
6. `pos-amend apply --dry-run` against the manifest — expect exit 0.
7. `pos-amend apply` — applies tuple/sidecar edits.
8. Stage + commit (amendment commit). Subject line shape: `feat(hands-off-lifecycle): bootstrap-progress visualization in Claude Code statusLine`.
9. `pos-amend seal --plan-doc <abs-path>` — advance sidecars + run sweep + create seal commit.
10. Verify amendment SHA + seal SHA both present in repo HEAD log.

Per amendment-dispatch CDC: skip pre-seal full-suite rerun (sidecar-only edits). All other sealed components run only their `test_no_sealed_amendments.py`.

---

## 9. Out of scope

- Generalised worker-progress framework. Status-line script is first-run-scoped only; future workers compose on `FirstRunState` separately.
- Telegram, Claude-app, or other status surfaces. Terminal status-line only.
- Dynamic phase-duration calibration (last-N-runs moving average).
- Spinner / animation frames at sub-1s granularity.
- Plugin packaging.
- Renaming or migrating the `<workspace>/.pos/` path.
- Touching `workspace-bootstrap/` or any sealed component other than `hands-off-lifecycle/`.

---

## 10. Decisions surfaced for owner ruling

Six decisions; each with a recommendation and the alternatives. Owner rules; build dispatch consumes the rulings.

1. **D1 — `progress_pct` schema field.** Recommend **(a)** add `progress_pct: int = 0` to `FirstRunState` (additive, defaulted, backwards compatible). Alternative **(b)**: compute percentage in the renderer from a phase→pct table, no schema change.
   - Recommendation rationale: centralises canonical per-phase progress where the worker can update it; worker writes the truth, renderer reads it; small surface.

2. **D2 — Post-completion rendering shape.** Recommend **(c)** brief steady-state ("pos-v2 ready") for ~ 60 s post-completion then blank. Alternatives **(a)** clear immediately on `status=completed`, or **(b)** persistent steady-state forever.
   - Recommendation rationale: visual continuity for the user mid-completion; clean steady state for future sessions.

3. **D3 — State-file path source.** Recommend reading `.workspace.project_dir` from the renderer's stdin JSON envelope. Alternative **(rejected)**: env var.
   - Recommendation rationale: portable, defended by amendment-#28's existing `_state_belongs_to` cross-check; no second source of truth.

4. **D4 — Renderer language.** Recommend **Python 3.13 stdlib**. Alternative: **bash + jq**.
   - Recommendation rationale: reuse `first_run_state` parsing + stale-detection; no `jq` dependency; matches the rest of the hooks directory.

5. **D5 — Existing-workspace retrofit.** Recommend **on** — supervisor path's settings-touch calls `merge_status_line` so a workspace already past first-run picks up the entry on its next session. Alternative: **off** — only fresh first-run sessions install the entry.
   - Recommendation rationale: non-trivial population of pre-amendment workspaces (e.g. pos3, the canonical workspace itself) gain the feature without a forced re-bootstrap; cost is one additional fail-soft call.

6. **D6 — Phase→duration estimate calibration source.** Recommend **static table** seeded from the helper's existing "~5 minutes total" figure + observed cold-cache wall-clocks per phase. Alternative: **dynamic last-N-runs average** (deferred — out of scope).
   - Recommendation rationale: pre-completion estimate is glanceable cosmetic; static table is honest about its precision; dynamic average is over-engineering pre-evidence.

---

## 11. ODD §2.5 reverse-direction trace

Every code path the amendment introduces traces to a named AC:

- `statusline.py` renderer body → AC.SL.1 / AC.SL.2 / AC.SL.3 / AC.SL.4 / AC.SL.5 (each branch maps to one AC, per §6 dispatch logic).
- `merge_status_line` function → AC.SL.6 / AC.SL.7.
- Worker Phase 6 wiring → AC.SL.6.
- Supervisor retrofit path (if D5=on) → AC.SL.8.
- `progress_pct` field (if D1=a) → AC.SL.1 (the worker writes, the renderer reads, the rendered line is what AC.SL.1 verifies).
- Stdlib-only constraint check → AC.SL.9.
- Seal-diff confinement → AC.SL.S.

No introduced code path lacks a backing AC. Build audit re-runs this trace pre-seal.

§2.5 violations in surrounding code: spot-check `first_run_settings.py`, `first_run_helper.py`, `first_run_dispatch.py`, `first_run_state.py`. The build agent halts and surfaces if any branch in those files has no backing AC across the existing amendment chain (#1–#46). If the agent finds none, the trace passes.

---

## 12. Halt triggers (build agent)

The build agent halts and signals to the dispatcher if any of the following surface during build:

1. The owner-ruled decisions in §10 contradict an AC text (e.g. owner picks D1=b but an AC text references `progress_pct`). Halt — request AC text revision.
2. A required edit falls outside the named fence (§7). Halt — request scope revision.
3. An ODD violation in surrounding code that the build agent's edit would extend or formalise (§2.5 reverse trace failure on existing code). Halt — surface the violation; do not silently extend.
4. Claude Code's `statusLine` schema has changed since the prior research doc (§13 reference URL). Halt — verify and update plan.
5. Cross-cutting overlap surfaces with another in-flight amendment (the `memory-system-live-client-and-stop-hook-write` amendment is currently being authored at canonical pos-v2 — research time check found no overlap; the build agent re-checks at dispatch time).
6. The renderer's stdlib-only constraint is unsatisfiable (e.g., the existing `first_run_state` module gained a non-stdlib import the agent cannot avoid). Halt — surface the dependency.
7. The plan author cannot author an AC outcome-shaped (recursion failure on the ODD §3 test). Halt — escalate to owner.
8. The status-line surface turns out to be unsuitable for a reason the existing research missed (e.g. the script is stripped of stdin, refresh interval is silently rejected at 1 s on the user's terminal). Halt — surface and propose alternative.

---

## 13. Risks

- **Stale `progress_pct` table.** If D1=a lands and a future amendment adds a new phase, the table must be updated. Mitigation: phase→pct table is co-located with the worker's `_advance_state` call sites; a phase introduction without a pct update is a §2.5 violation visible in the new code's diff.
- **Cold-start interpreter latency.** Python 3.13 takes ~ 50 ms cold. Refreshing every 1 s means ~ 5% baseline CPU during bootstrap. Negligible on any modern machine; flagged for completeness.
- **`statusLine` precedence collision.** A user with a custom statusLine in workspace-local settings.json is displaced (per AC.SL.7). Mitigated by the timestamped backup; user can restore or relocate to user-global settings if they want both.
- **Foreign-workspace state cross-talk.** Defended by AC.SL.4 + the dispatcher's `_state_belongs_to` mirror. Risk-residual: zero.
- **Status-line surface deprecation by Claude Code.** If Claude Code removes `statusLine` in a future release, the entry becomes inert and the status line goes blank — graceful degradation. Re-implementation of the underlying surface is out of scope.

---

## 14. References

- Research doc: `docs/rebuild/plans/research/bootstrap-progress-statusline-research.md`.
- Spec binding: `docs/rebuild/spec/pos-v2-objectives-spec.md` "Non-tech users" v1.0 acceptance bullet — re-extension of low-friction-onboarding.
- VALUE_PROPOSITION binding: `docs/rebuild/VALUE_PROPOSITION.md` Lens 2 (translation burden + harness toolkit).
- Sibling pattern (settings-merge functions, hook-stanza authoring shape, ODD §2.5 trace): `docs/rebuild/plans/amendment-46-persona-session-start-turn-start-emitters.builder-plan.md`.
- Sibling pattern (workspace-local state-file routing, defence in depth): `docs/rebuild/plans/amendment-28-workspace-identity-routed-first-run.md`.
- State-file primary surface: `hands-off-lifecycle/hooks/first_run_state.py` (`FirstRunState`, `read_state`, `write_state`, `is_stale_live_state`, `state_path`).
- Phase-boundary call sites: `hands-off-lifecycle/hooks/first_run_helper.py` (lines 1382, 1422, 1443, 1505, 1550, 1601, 1657, 1703, 1860, 1890, 1902, 1949).
- Settings-merge convention: `hands-off-lifecycle/hooks/first_run_settings.py` (`merge_session_start`, `merge_user_prompt_submit`).
- Settings fragment authority: `hands-off-lifecycle/hooks/settings.json.fragment`.
- Claude Code status-line behavioural research: `/Users/lukeivers/pos3/.scratch/claude-output/claude-code-statusline-research.md`.
- FUTURE_IDEAS CDCs: `docs/rebuild/FUTURE_IDEAS.md` (research-before-plan, plan-before-code, scope-only-dispatch, amendment-dispatch test-scope).

### Commit SHAs

- Amendment commit: `945b8f53a3ac7202ee3e4f31a75f8b932a38613d` —
  `feat(hands-off-lifecycle): bootstrap-progress visualization in Claude Code statusLine`
- Seal commit: `5f235c7defc0a8e40b5d96b0e2013259b3401282` —
  `chore(seals): bootstrap-progress visualization in Claude Code statusLine — hands-off-lifecycle at 945b8f5`
