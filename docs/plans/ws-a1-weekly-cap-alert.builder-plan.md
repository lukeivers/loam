# WS-A1 — Weekly-cap alert (builder plan)

**Status:** in-build. **Working directory:** `/Users/lukeivers/loam`.
**Source:** `workspace/strategy/ai-shop-backplane/BACKPLANE-PLAN.md` §5 Track A (WS-A1).
**Class:** NEW standalone component under `framework/weekly-cap-alert/`. NOT a sealed-component
amendment → plan + tests (no `loam amend` cycle). Composes the SEALED `usage-window-guard`
by import only (never modifies it).
**Branch:** `feat/ws-a1-weekly-cap-alert` (off `main` = `c53458da`).

---

## 1. Objective

When the Claude **weekly** (`seven_day`) cap utilization crosses the owner-set threshold,
a Discord message reaches Luke; below it, silence. When the utilization cannot be read
(`UsageUnavailable`), the alert fires the categorical failure reason and never a number.
Runs as a periodic launchd job that survives a session ending.

## 2. Fence (scope)

IN: a new component `framework/weekly-cap-alert/` (`loam.weekly_cap_alert`). It IMPORTS
`loam.usage_window_guard.read` (sealed; editable-installed in the venv) as the reading,
evaluates the `seven_day` window against a config threshold, and surfaces via an injected
channel seam. It ships a launchd plist template + a renderer/installer.

OUT (halt-and-surface if the work would touch these):
- Any modification to `usage-window-guard` or any sealed component (import-only compose).
- `.claude/settings.json` (Track F single-writer; WS-A1 registers NO settings.json hook —
  it uses its own launchd plist file, which does not collide, per §5 of the plan).
- WS-A4's cap-into-cost-governance wiring, WS-A5's roll-up, the fleet page. Different fences.
- The pos3 workspace channel module (`channel_notify.py`) — loam source NEVER imports it
  (the H-3 fence proven by handsoff-loop AC.HB.4). The channel surface enters by injection.

## 3. Ground truth verified this session

- **Probe API** (`framework/usage-window-guard/src/loam/usage_window_guard/probe.py`):
  `read()` returns a sum type — `UsageWindows(five_hour, seven_day)` where each `Window`
  has `.utilization` (float in `[0,100]`, Anthropic's own accounting) and `.resets_at`,
  OR `UsageUnavailable(reason: UnavailableReason, detail: str)` which by construction
  carries **NO** numeric utilization. This is why a fabricated number is structurally
  impossible on the failure path. `read()` is import-only; I do not touch the component.
- **`seven_day` is the correct window** (constraint): the weekly bucket is the only Claude
  limit that costs anything; the 5-hour window is a throttle (standing owner rule).
- **Channel delivery** is workspace-owned (`pos3/.claude/hooks/channel_notify.py`,
  `post_to_active_channel`, default DISCORD). loam source must not import it (H-3). The
  seam is an injected `notify_fn`; the launchd job bridges to the workspace poster via a
  `--notify-cmd` filled at install time. See D-A1-3.
- **launchd** convention: `framework/orchestrator/ops/launchd/*.plist.tmpl` +
  `string.Template` render, verified by a `plistlib.loads` structural test. WS-A1 differs:
  it is **periodic** (`StartInterval` + `RunAtLoad`, NO `KeepAlive` — A1 is a cron tick,
  not a persistent daemon).

## 4. Named decisions (recommendation = decision; F2 gaps surfaced)

- **D-A1-1 `UsageUnavailable` FIRES the alert with the categorical reason (no number).**
  Not silent-to-stdout. Two constraints force this: (a) the WS-A1 constraint says "the
  alert **reports** the categorical failure reason" — reports to Luke, not to a swallowed
  log line; (b) BACKPLANE-PLAN §5 WS-A4 (line 439) fails OPEN on `UsageUnavailable`
  *explicitly because* "the alert in WS-A1 covers the blind window." If A1 were silent on
  unavailable, nothing would cover the window: WS-A4 proceeds blind AND Luke never learns
  his cap reader went dark. So unavailable → `notify=True`, message = the categorical
  `reason.value` + a plain phrase, and **no utilization number** anywhere on that path
  (`detail` is NOT interpolated onto the alert message — it can carry "HTTP 401" which is
  a digit but not a fabricated %).
- **D-A1-2 transient-blip de-duplication is OUT of the WS-A1 AC fence (surfaced, not
  built, F2).** `auth_rejected` is transient (a rotated token the next probe refreshes);
  a naive periodic job would re-ping every tick while it persists. Suppressing the alert
  to solve this would under-build D-A1-1. The honest resolution is a dedup/backoff slice
  (remember the last surfaced state; ping on transition, not on every tick) — a bounded
  follow-on, named here, not silently folded in. WS-A1 builds the honest surface; the
  dedup is a downstream enhancement.
- **D-A1-3 delivery seam = `--notify-cmd` (H-3 boundary).** loam ships channel-agnostic:
  the default `notify_fn` writes the message to stdout (self-contained, launchd-runnable,
  captured in the job's `StandardOutPath`). A `--notify-cmd CMD` argument shells `CMD`
  with the message on **stdin** — the launchd plist is rendered with `notify-cmd` pointed
  at a workspace poster so the real Discord ping happens without loam importing the pos3
  channel module. **F2 surface:** `pos3/.claude/hooks/channel_notify.py` exposes
  `post_to_active_channel` as a Python *module function*, not a stdin CLI. Making real
  delivery live therefore needs a thin one-file workspace wrapper (read stdin →
  `post_to_active_channel(None, body, prefix="")`) that the plist's `notify-cmd` targets.
  That wrapper is a **workspace artifact, OUT of loam's fence** — I name it as the single
  owner/workspace wiring step; loam's side (the `--notify-cmd` seam + stdout default) is
  complete and provable in-fence.
- **D-A1-4 threshold lives in config, not code (constraint).** `config.py` carries
  `DEFAULT_THRESHOLD_PCT = 60.0` — **owner-ratified (D5)**, not a placeholder — and a
  `load_threshold()` that reads an optional JSON config (`LOAM_WEEKLY_CAP_ALERT_CONFIG`
  env override, else `~/.claude/weekly-cap-alert.json`), key `threshold_pct`, failing back
  to the ratified 60.0 on any absence/malformation (fail-open to the ratified default,
  never a wedge). A `--threshold-pct` CLI flag overrides for a one-off run.

## 5. Acceptance criteria (from BACKPLANE-PLAN §5 WS-A1; outcome-shape)

- **AC.CAP.1 (outcome-altitude).** With a stubbed probe returning `seven_day` utilization
  **above** threshold, invoking the production entry point (`run_alert`) produces a sent
  notification (an injected capturing `notify_fn` receives a message carrying the
  utilization); **below** threshold, `notify_fn` is never called (silence). The entry
  point is driven end-to-end; only the probe + channel boundaries are injected.
- **AC.CAP.2.** With the probe returning `UsageUnavailable(reason)`, the production entry
  point fires the alert (D-A1-1): `notify_fn` receives a message containing the categorical
  `reason.value` and **no utilization percentage**. (Asserted against a percentage shape,
  not "no digit anywhere.")
- **AC.CAP.3.** The job is registered to run on a schedule and survives a session ending:
  the install renderer writes a valid launchd plist that (a) parses via `plistlib.loads`,
  (b) carries a `StartInterval` (periodic schedule) + `RunAtLoad` and NO `KeepAlive`,
  (c) invokes `python -m loam.weekly_cap_alert`. Verified from the installed artifact, not
  `.claude/settings.json`.

Every field/branch/test maps to an AC above (ODD §2.5). No non-objective/defensive code.

## 6. Build steps

1. `framework/weekly-cap-alert/` scaffold: `pyproject.toml` (dep: `loam-usage-window-guard`),
   `pytest.ini`, `README.md`.
2. `src/loam/weekly_cap_alert/config.py` — ratified default + `load_threshold()`.
3. `src/loam/weekly_cap_alert/notify.py` — `stdout_notify` default + `command_notify(cmd)`
   stdin-shelling factory (the H-3-clean delivery seam).
4. `src/loam/weekly_cap_alert/alert.py` — `AlertDecision` + `evaluate(result, threshold)`
   (the three outcomes: above→notify+number, below→silence, unavailable→notify+reason) +
   `run_alert(*, probe, threshold, notify_fn)` production entry.
5. `src/loam/weekly_cap_alert/install.py` — plist render/write from the `.plist.tmpl`.
6. `ops/launchd/com.loam.weekly-cap-alert.plist.tmpl` — periodic (StartInterval+RunAtLoad).
7. `src/loam/weekly_cap_alert/__main__.py` + `__init__.py` — CLI production entry.
8. `tests/` — `conftest.py` + `test_AC_CAP_1_*`, `test_AC_CAP_2_*`, `test_AC_CAP_3_*`.
   Each drives the real entry point, injecting only probe + notify (+ tmp plist path).
9. `pip install -e`, import from `/tmp`, `pytest`, pyright, commit on the WS-A1 branch.

## 7. Halt triggers

- Any edit that would touch a sealed component, `usage-window-guard` source, or
  `.claude/settings.json`.
- An AC that would ship partial — name the gap, do not weaken the AC.
- A surrounding-code ODD violation surfaced during the build.
