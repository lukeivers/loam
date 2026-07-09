# WS-A5 — Weekly cost roll-up (builder plan)

**Status:** in-build. **Working directory:** `/Users/lukeivers/loam`.
**Source:** `workspace/strategy/ai-shop-backplane/BACKPLANE-PLAN.md` §5 Track A (WS-A5).
**Class:** NEW standalone component under `framework/weekly-cost-rollup/`. NOT a
sealed-component amendment → plan + tests (no `loam amend` cycle). Composes the SEALED
`usage-window-guard` (import-only probe path) and REUSES WS-A1's channel-notify seam
(`loam.weekly_cap_alert.notify`) — never modifies either.
**Branch:** `feat/ws-a5-weekly-cost-rollup` (off `feat/ws-a1-weekly-cap-alert` =
`483615d1`, because WS-A5 depends on WS-A1's probe path + notify seam, and WS-A1 is not
yet merged to `main`; see D-A5-6).

---

## 0. Scope-discrepancy note (F2 — surfaced, not silently resolved)

The dispatch prose described WS-A5 as "the roll-up that composes the fleet page (WS-A3) +
the cost ceiling/alert into the single operator surface … Depends on WS-A3 + WS-A4". That
does NOT match BACKPLANE-PLAN §5 WS-A5, which is the **Weekly cost roll-up**: a weekly
Discord message in three sections (per-machine cap %, top-3 projects by Claude tokens
labeled a proxy, metered-model $ MTD), depending on **WS-A1** (probe path) + **D1**
(gateway). The instruction is explicit: "Read §5 for WS-A5 and build EXACTLY that to its
acceptance criteria." The plan is authoritative; I build the §5 Weekly cost roll-up. The
prose mismatch is flagged for the dispatcher, not silently reconciled.

## 1. Objective

Once a week, one Discord message carrying three sections: (1) weekly Claude cap % for this
machine, (2) top-3 projects by Claude tokens (explicitly labeled a proxy, never dollars),
(3) metered-model spend month-to-date (Vercel AI Gateway). Missing sources are **named**,
never silently omitted. Runs as a weekly launchd job that survives a session ending.

## 2. Fence (scope)

IN: a new component `framework/weekly-cost-rollup/` (`loam.weekly_cost_rollup`). It reads
the SEALED `usage-window-guard` `seven_day` cap (import-only), parses per-project Claude
token totals from the local transcript store (`~/.claude/projects/*/*.jsonl`), takes an
injectable gateway-spend source, assembles the three-section message, and delivers via the
WS-A1 channel seam. It ships its own weekly launchd plist template + renderer/installer.

OUT (halt-and-surface if the work would touch these):
- Any modification to `usage-window-guard`, `weekly-cap-alert`, or any sealed component
  (import-only compose / reuse).
- `.claude/settings.json` (Track F single-writer). WS-A5 registers NO settings.json hook —
  it writes its OWN separate launchd plist file (`com.loam.weekly-cost-rollup`), which per
  §5 does not collide with WS-A1's plist. If a settings.json hook were ever needed → HALT.
- WS-A3 fleet page, WS-A4 cost-governance wiring — different fences.
- The pos3 workspace channel module (`channel_notify.py`) — loam source NEVER imports it
  (H-3 fence). The channel surface enters by injection (reused WS-A1 `--notify-cmd` seam).

## 3. Ground truth verified this session

- **Probe API** (`loam.usage_window_guard.read`): sum type — `UsageWindows(five_hour,
  seven_day)` where each `Window` has `.utilization` (float, Anthropic's own accounting),
  OR `UsageUnavailable(reason, detail)` carrying **NO** number. `seven_day` is the weekly
  bucket (the only Claude limit that costs anything). Import-only; component untouched.
- **Transcript schema** (verified against a live `~/.claude/projects/*/*.jsonl`): each
  project directory is the encoded cwd; assistant lines carry `message.usage` with
  `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`.
  Total tokens for the proxy ranking = sum of those four across all assistant usage blocks
  in a project's session files. This is exactly what `ccusage` reads.
- **ccusage runs via `npx -y ccusage@latest` (exit 0) but has NO project dimension**
  (groups by date/month/week/session only; `session --json` rows carry a session-UUID +
  `lastActivity`, no cwd; the `--instances` flag is gone). See D-A5-1: unusable for a
  per-project ranking, so the default token source parses the transcript files directly,
  with dedup on `(message.id, requestId)` + a weekly `timestamp` window (D-A5-1b).
- **Channel seam** (`loam.weekly_cap_alert.notify`): `stdout_notify` (default, launchd-log
  capture), `command_notify(cmd)` (stdin-shell bridge to a workspace poster via
  `--notify-cmd`), `NotifyFn` type. Reused verbatim (no re-roll, per dispatch constraint).
- **launchd** convention (WS-A1 `install.py`): `string.Template` render of a `.plist.tmpl`,
  verified by `plistlib.loads`. WS-A5 is **weekly**: `StartCalendarInterval` (Monday 09:00)
  + `RunAtLoad`, NO `KeepAlive` (a probe-and-exit tick, not a daemon).

## 4. Named decisions (recommendation = decision; F2 gaps surfaced)

- **D-A5-1 default token source parses transcripts directly — an empirically-grounded
  adopt→build deviation the dispatcher should note (F2).** The plan directs ADOPT ccusage
  (`ccusage --instances`, row 22 / §5). I ran the real adopt path (`npx -y ccusage@latest`,
  exit 0 — ccusage runs without a global install), and it is **structurally unusable for
  this objective**: (a) the `--instances` flag no longer exists; (b) ccusage groups only by
  date / month / week / **session**, never by project; (c) its `session --json` row carries
  a session-UUID `period` + `lastActivity` and **no cwd/project path** — the project
  dimension the objective ranks on is exactly what ccusage discards. So "top-3 **projects**
  by tokens" cannot come from ccusage's output. The transcript files (verified schema above)
  DO carry the project (the encoded-cwd directory name), so the default source parses them
  directly. This is the adopt→build swap surfaced as a deviation, not made silently: adopt
  was tried, empirically ruled out for the project dimension, build justified. Source stays
  **injectable** so a future project-aware attribution tool is a config swap.
- **D-A5-1b the parser owes dedup + weekly windowing, or the proxy misleads.** A weekly
  burn signal summed naively over every `*.jsonl` line is wrong twice: (a) resumed/compacted
  sessions re-emit the same assistant message, so summing double-counts (ccusage dedupes on
  `message.id` + `requestId`; the parser does the same — a usage block is counted once per
  `(message.id, requestId)`); (b) an all-time sum never moves week to week and misranks
  toward whatever was resumed most — so the parser **windows** to the last `window_days`
  (default 7) by each line's top-level `timestamp`. Both are required for AC.RUP.1's
  "correct top-3 ranking" (a double-counted / all-time ranking is not correct), so every
  line maps to that AC — not gold-plating. This directly answers the plan's own
  "attribution over-trust" risk row.
- **D-A5-2 the gateway section defaults to a NAMED absence (D1 not yet signed up).** The
  Vercel AI Gateway signup is owner decision D1, not yet done. The gateway source is an
  injectable seam whose default returns `GatewayUnavailable(reason="not_configured")`, so
  the section renders "source unavailable — Vercel AI Gateway not configured yet (D1
  pending)". This is the plan's "degrades … plus a named absence", not a silent two-section
  message. When D1 lands, a real provider is configured at the seam.
- **D-A5-3 the roll-up ALWAYS delivers (unlike the WS-A1 alert, which is conditional).**
  It is a scheduled weekly digest; `run_rollup` always hands the assembled message to
  `notify_fn`. There is no "silence" branch.
- **D-A5-4 the proxy label is mandatory and non-negotiable (stream 04 §1c).** The token
  section always carries "proxy — ranks consumption, not billing-grade". Asserted by AC.
- **D-A5-5 a missing source is a NAMED section, never a dropped one.** Cap-unavailable,
  zero-transcripts, and gateway-unavailable each render a section that names the absence;
  the cap-unavailable path carries the categorical reason and **no** utilization number
  (same discipline as WS-A1 D-A1-1 — a fabricated % is structurally impossible off the
  probe's sum type). This satisfies the constraint "missing sources are named, not
  silently omitted".
- **D-A5-6 branch base is the WS-A1 branch, not `main`.** WS-A5 depends on WS-A1's probe
  path + notify seam; WS-A1 (`framework/weekly-cap-alert`) is not yet on `main`. Basing
  WS-A5 on `main` would make the reused imports unresolvable. Recorded here + in the
  structured result so the dispatcher sequences the eventual merges A1→A5.
- **D-A5-7 message ≤ ~15 lines (constraint — it goes to a chat channel).** Three compact
  sections, top-3 only, one line per project. Blank-line separators keep it under 15 lines.

## 5. Acceptance criteria (from BACKPLANE-PLAN §5 WS-A5; outcome-shape)

- **AC.RUP.1 (outcome-altitude).** Invoking the production entry point (`run_rollup`) with
  **fixture transcript data** (real parser pointed at a fixture `~/.claude/projects`-shaped
  dir) + a stubbed probe returning `UsageWindows` produces the **three-section** message
  with the **correct top-3 ranking** (projects sorted by summed tokens, descending, capped
  at 3) and the **proxy label present**. Driven end-to-end; only the probe + gateway
  boundaries are injected — the token parser and message assembly are the real production
  path. A sibling case asserts a `UsageUnavailable` probe renders the cap section as a
  named absence with the categorical reason and **no** utilization percentage (D-A5-5).
- **AC.RUP.2.** (a) The job is registered to run **weekly** and survives a session ending:
  the install renderer writes a launchd plist that parses via `plistlib.loads`, carries a
  `StartCalendarInterval` (weekly) + `RunAtLoad` and NO `KeepAlive`, and invokes
  `python -m loam.weekly_cost_rollup` (verified from the installed artifact, not
  `.claude/settings.json`). (b) A run with the **gateway unreachable** emits the other two
  sections **plus a named absence** for the gateway section (never a silent drop).

Every field/branch/test maps to an AC above (ODD §2.5). No non-objective/defensive code.

## 6. Build steps

1. `framework/weekly-cost-rollup/` scaffold: `pyproject.toml` (deps:
   `loam-usage-window-guard`, `loam-weekly-cap-alert`), `pytest.ini`, `README.md`.
2. `src/loam/weekly_cost_rollup/tokens.py` — `ProjectTokens`, `TokenUsageUnavailable`,
   `read_project_tokens(root=None)` (glob `<root>/*/*.jsonl`, sum the four usage fields per
   project dir, return ranked list; empty/unreadable root → `TokenUsageUnavailable`). Env
   override `LOAM_CLAUDE_PROJECTS_DIR` for the fixture seam; default `~/.claude/projects`.
3. `src/loam/weekly_cost_rollup/gateway.py` — `GatewaySpend`, `GatewayUnavailable`,
   `read_gateway_spend()` (default → `not_configured` named absence; injectable seam).
4. `src/loam/weekly_cost_rollup/rollup.py` — `build_message(...)` (three sections, top-3,
   proxy label, named absences) + `run_rollup(*, probe, token_source, gateway_source,
   notify_fn, top_n=3)` production entry (always delivers).
5. `src/loam/weekly_cost_rollup/install.py` — weekly plist render/write from the template.
6. `ops/launchd/com.loam.weekly-cost-rollup.plist.tmpl` — `StartCalendarInterval` weekly.
7. `src/loam/weekly_cost_rollup/__main__.py` + `__init__.py` — CLI production entry.
8. `tests/` — `conftest.py` + `test_AC_RUP_1_*` (top-3 + proxy + cap-unavailable) +
   `test_AC_RUP_2_weekly_schedule_artifact.py` + `test_AC_RUP_2_gateway_named_absence.py`.
   Each drives the real entry point, injecting only probe + gateway + notify (+ tmp paths).
9. `pip install -e`, import from `/tmp`, `pytest`, pyright, commit on the WS-A5 branch.

## 7. Halt triggers

- Any edit that would touch a sealed component, `usage-window-guard`/`weekly-cap-alert`
  source, or `.claude/settings.json`.
- An AC that would ship partial — name the gap, do not weaken the AC.
- A surrounding-code ODD violation surfaced during the build.
