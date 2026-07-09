# WS-A3 — Fleet page (static render) (builder plan)

**Status:** in-build. **Working directory:** `/Users/lukeivers/loam`.
**Source:** `workspace/strategy/ai-shop-backplane/BACKPLANE-PLAN.md` §5 Track A (WS-A3).
**Class:** NEW standalone component under `framework/fleet-page/`. NOT a sealed-component
amendment → plan + tests (no `loam amend` cycle). Depends on WS-A2 (`loam.fleet_collector`,
same branch lineage).

---

## 1. Objective

One static HTML page answering "what are my agents doing right now, are they alive, what
has it cost this week, and what needs a human decision" — regenerated automatically by a
cron/launchd job (NOT a `.claude/settings.json` hook), opened locally, no server. It
consumes WS-A2's fleet JSON (live feed, leading), the `observability-aggregator`
structured API (historical cost strip), and the `per-project-pm` decision queue (the
"needs a human" panel). Degrades gracefully when a source is absent.

## 2. Fence (scope)

IN: a new component `framework/fleet-page/` (`loam.fleet_page`). It READS three sources
(each read-only, via each component's existing public surface — never by re-querying the
underlying store by hand): `collect_fleet()` (WS-A2), `QueryAPI.cost_by_prompt()`
(observability-aggregator), `load_decision_queue()` (per-project-pm). It RENDERS one HTML
file and INSTALLS a launchd/cron regenerator artifact.

OUT (halt-and-surface if the work would touch these):
- `.claude/settings.json` — Track F single-writer; WS-A3 registers NO hook there. The
  regenerator is a cron/launchd job by explicit §5 constraint. (If the design ever
  required a settings.json hook → HALT, per dispatch hard constraint.)
- Any modification to `fleet-collector`, `observability-aggregator`, `per-project-pm`, or
  any sealed component. All three sources are read via their existing public API; if a
  read needs a source-side change → HALT.
- Any other workstream (WS-A1 cap alert, WS-A4/A5, Track B/F).

## 3. Data sources — verified against ground truth this session

- **Live feed (WS-A2).** `loam.fleet_collector.collect_fleet(roots)` →
  `{generated_at, generated_at_iso, run_count, runs:[{run_dir, workspace, objective,
  stage, elapsed_s, alive, artifact_age_s, cost_usd, cost_source, exit_status}]}`. `alive`
  is already the artifact-probe judgment (WS-A2 owns liveness; WS-A3 never re-probes).
- **Historical cost strip.** `QueryAPI(open_store(cfg)).cost_by_prompt(time_range=...)` →
  `dict[str, PromptCost]`, `PromptCost = {prompt_name, input_tokens, output_tokens,
  call_count, estimated_usd}`. Token-count is the durable signal for isolated agents;
  labeled a token PROXY, not billing-grade (stream 04 §1c discipline).
- **Decision queue (per-project-pm).** `load_decision_queue(pm_dir)` →
  `list[{text, provenance, enqueued_at}]`; absent file → `[]` (empty is the normal
  no-decisions state, NOT a missing source).

## 4. Named decisions (recommendation = decision; F2 gaps surfaced)

- **D-A3-1 render is a pure function; the entry point injects sources.** `render_page(...)`
  takes already-read data and returns an HTML string; `generate_page(out, *, fleet_source,
  cost_source, decisions_source)` is the production entry point that calls each source,
  degrades per-source, renders, and writes the file. This makes AC.PAGE.1 (fixture fleet +
  stub queue) and AC.PAGE.3 (one source raising) drive the SAME real entry point with
  different injected sources — no test-only entry point, no method baked into the AC.
- **D-A3-2 three independent sources, per-source degrade.** Each source is called in its
  own `try/except`; a failure marks THAT panel missing (labeled "source unavailable"),
  never blanks the page or invents data (AC.PAGE.3). The fleet source feeds two panels
  (live table + recent-outcomes strip) since both derive from the one JSON; a fleet
  failure marks both missing, cost/decisions still render.
- **D-A3-3 empty ≠ missing.** An empty decision queue, zero live runs, or an empty cost
  map render as explicit "nothing queued / no live agents / no recorded cost" states, NOT
  as a missing-source label. Missing = the source raised or is uninstalled; empty = the
  source answered with nothing. The §5 constraint "must not imply zero activity when the
  collector shows runs" is honored by leading with the live feed and labeling every empty
  vs missing state distinctly.
- **D-A3-4 launchd over cron on darwin.** Platform is darwin; the regenerator is a launchd
  `.plist` (`StartInterval`) written to a target dir (default `~/Library/LaunchAgents`).
  `install_launchd_job()` writes the plist artifact and returns its path; it invokes
  `python -m loam.fleet_page render`. The artifact references NO `.claude/settings.json`
  (AC.PAGE.2). A `--cron` fallback line generator is provided for non-darwin, but darwin
  is the built-and-tested path.
- **D-A3-5 lazy source imports.** `observability_aggregator` / `per_project_pm` /
  `fleet_collector` are imported INSIDE the default reader functions, never at module top,
  so `import loam.fleet_page` succeeds without those packages installed (clean self-import
  from `/tmp`), and a genuinely-uninstalled source degrades to a missing panel rather than
  an ImportError at module load.
- **D-A3-6 cost = honest read of WS-A2's fields.** The live table's cost column shows
  `cost_usd` when present, else the WS-A2 `cost_source` string (e.g. "absent") — never a
  fabricated `$0.00`. This carries WS-A2's no-fabrication contract through to the view.

## 5. Acceptance criteria (from BACKPLANE-PLAN §5 WS-A3; outcome-shape)

- **AC.PAGE.1 (outcome-altitude).** From fixture collector JSON + a stubbed decision queue
  (and a stub cost map), the production entry point (`generate_page`) writes an HTML file
  showing the live-agent table (columns: status, liveness, elapsed, cost), a
  recent-outcomes strip, and the decision queue; the document carries both-theme CSS
  (`prefers-color-scheme` light + dark) and wraps every wide table in an `overflow-x:auto`
  container so it renders without horizontal overflow in both themes.
- **AC.PAGE.2.** (a) `install_launchd_job()` writes a launchd plist artifact that
  references the `loam.fleet_page` regenerator command and contains NO reference to
  `.claude/settings.json`; the artifact is verifiable on disk. (b) Regeneration overwrites
  a stale page: `generate_page` to an existing path replaces its content on the next call.
- **AC.PAGE.3.** With one source unavailable (its reader raises), `generate_page` still
  writes the page: the remaining panels render and the missing one is labeled
  "source unavailable" — no blank page, no invented data (a missing cost strip shows the
  label, never `$0`).

Every field/branch/panel maps to an AC above (ODD §2.5). No non-objective code.

## 6. Build steps

1. `framework/fleet-page/` scaffold: `pyproject.toml`, `pytest.ini`, `README.md`.
2. `src/loam/fleet_page/render.py` — `render_page(...)` pure HTML builder (4 panels: live
   table, recent-outcomes strip, historical cost strip, decision queue) + theme/overflow
   CSS. HTML-escapes all injected text.
3. `src/loam/fleet_page/sources.py` — default readers (lazy imports): `read_fleet`,
   `read_cost_rows`, `read_decisions`; each raises on genuine unavailability.
4. `src/loam/fleet_page/generate.py` — `generate_page(out, *, fleet_source, cost_source,
   decisions_source, now)` production entry point: per-source degrade → render → write.
5. `src/loam/fleet_page/schedule.py` — `render_plist(...)` + `install_launchd_job(...)`
   (+ `render_cron_line` fallback).
6. `src/loam/fleet_page/__main__.py` + `__init__.py` — CLI (`render` default,
   `install-launchd` subcommand).
7. `tests/` — `conftest.py` + `test_AC_PAGE_1_*`, `test_AC_PAGE_2_*`, `test_AC_PAGE_3_*`.
   Each drives the real entry point against fixtures/stubs.
8. `pip install -e`, import from `/tmp`, `pytest`, pyright, commit on
   `feat/ws-a3-fleet-page`. Install the launchd artifact for real (owner-authorized) and
   report status.

## 7. Halt triggers

- Any edit that would touch `.claude/settings.json`, a source component's code, or any
  sealed component.
- A design that genuinely requires a settings.json hook (dispatch hard constraint → HALT).
- An AC that would ship partial — name the gap, do not weaken the AC.
- A surrounding-code ODD violation surfaced during the build.
