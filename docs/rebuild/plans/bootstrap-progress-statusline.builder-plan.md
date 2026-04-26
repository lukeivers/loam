# Builder plan — bootstrap-progress visualization in Claude Code's terminal status line

**Plan governs:** `docs/rebuild/plans/bootstrap-progress-statusline.md` (D1–D6 LOCKED 2026-04-26).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

**Authored:** 2026-04-26 by build agent. Not amendment-numbered yet — assigned by `pos-amend apply`.

**Pre-amendment tip:** `052b49b docs(plans): record amendment #48 commit SHAs in method-decision register` (= `git rev-parse HEAD` at dispatch). BASELINE pin uses the long SHA written in `52b49b` resolution form: `git rev-parse 052b49b` → `052b49bff...`.

**Pre-amendment narrow-scope test count:** 138 passed (`hands-off-lifecycle/tests/`).

---

## 1. D-decision binding

The plan §10 ruled six decisions. The builder operationalises them verbatim:

| Decision | Locked value | Builder action |
|---|---|---|
| **D1** | (a) — add `progress_pct: int = 0` to `FirstRunState` | Schema field landed in `first_run_state.py`; phase→pct table inside `first_run_helper.py` next to `_advance_state` writes. |
| **D2** | (c) — 60s steady-state then blank | Renderer branch: `status=completed` and `now − updated_at < 60` → "pos-v2 ready" steady-state line; otherwise blank. |
| **D3** | stdin `.workspace.project_dir` | Renderer reads JSON from stdin, looks up `workspace.project_dir`, derives state-file path. |
| **D4** | Python 3.13 stdlib | Renderer is pure stdlib. Settings.json `command` references `<python3.13> <abs-path-to-statusline.py>`. |
| **D5** | retrofit ON | Supervisor (`pos_session_start.py`) gets a fail-soft `merge_status_line` call so existing-workspace retrofit works. |
| **D6** | static phase→duration table | Static dict in `statusline.py`. |

---

## 2. Files touched (named, with role)

### Source — sealed-component fence: `hands-off-lifecycle/`

1. **`hands-off-lifecycle/hooks/first_run_state.py`** (MODIFY)
   - Add `progress_pct: int = 0` field on `FirstRunState` dataclass (after `workspace_root`).
   - No changes to `read_state` / `write_state` signatures — `FirstRunState.__dataclass_fields__` walk already handles new optional fields, and JSON read drops absent fields gracefully (`v is None: continue`).
   - Backwards-compat: an old state-file JSON without `progress_pct` reads as `progress_pct=0`. ✓

2. **`hands-off-lifecycle/hooks/statusline.py`** (NEW)
   - Stdlib-only renderer. Reads stdin JSON envelope; resolves state-file path from `workspace.project_dir`; dispatches by `state.status`; prints one line ≤ 200 chars; exits 0.
   - Symbols: `_PHASE_LABELS` dict, `_PHASE_DURATIONS_S` dict (D6), `_render_active`, `_render_completed`, `_render_failed`, `_render_stalled`, `main()`.
   - Defence in depth: mirrors `_state_belongs_to` from `first_run_dispatch.py` lines 267–289 (strict equality of resolved `workspace_root`).
   - Fail-closed: any exception → empty stdout + exit 0.

3. **`hands-off-lifecycle/hooks/first_run_settings.py`** (MODIFY)
   - Add `_POS_V2_STATUS_LINE_COMMAND_MARKERS` tuple (single marker: `"hands-off-lifecycle/hooks/statusline.py"`).
   - Add `_is_pos_v2_owned_status_line(entry: Any) -> bool` predicate. Note: `statusLine` is a single-mapping object (not a list of stanzas like SessionStart/UserPromptSubmit/Stop), so the predicate inspects `.command` directly.
   - Add `merge_status_line(*, settings_path, new_entry, now_iso=None) -> SettingsMergeResult` — operates on the top-level `statusLine` field (not under `hooks.*`); backs up user-authored value to `<settings>.user-backup-<ts>.json`; atomic `.tmp` + rename; preserves all other top-level keys.

4. **`hands-off-lifecycle/hooks/first_run_helper.py`** (MODIFY)
   - Import `merge_status_line` from `first_run_settings`.
   - New helper `_status_line_stanza(pos_v2_root: Path) -> dict` — returns the `{"type": "command", "command": "<python> <statusline.py>", "refreshInterval": 1}` shape. Uses `sys.executable` since the worker runs under the resolved Python the dispatch found (matches `first-run.sh`'s detection chain — same approach as `_ensure_shared_venv`).
   - New fail-soft wrapper `_maybe_merge_status_line(*, pos_v2_root, settings_path)` — calls `merge_status_line`; swallows any exception (logs nothing, the status-line install is additive UX).
   - Add `_PHASE_PCT` static dict next to `_advance_state`. Pre-existing phases mapped (per plan §6 D-build.6 / D-build.7 phase-name list): `phase-2-venv-creation`→5, `phase-3a-inventory`→10, `phase-3b-shared-deps`→25, `phase-3e-editable-installs`→55, `phase-3c-dedicated-venvs`→70, `phase-3d` not used (Phase 3d is `_advance_state`-less today; preserved). `phase-4a-scaffold`→80, `phase-4c-agent-file-authorship`→85, `phase-4b-health-poll`→90, `phase-5-confirmation`→95, `phase-6-self-retire`→98, `complete`→100.
   - `_advance_state` extended: when `phase` is provided and matches a `_PHASE_PCT` key, set `state.progress_pct = _PHASE_PCT[phase]`. (Falls back to leaving the prior value untouched on unknown phase — same shape as the existing `if detail: state.detail = detail`.)
   - `_self_retire` (line 1257) gets one new call after the existing `_maybe_merge_stop`: `_maybe_merge_status_line(pos_v2_root=pos_v2_root, settings_path=settings_path)`. The Phase 3d settings.json authorship at line 1700–1720 also gets a parallel `_maybe_merge_status_line` after `_maybe_merge_stop` — symmetrical with the persona session-start / user-prompt-submit / stop hooks.

5. **`hands-off-lifecycle/hooks/settings.json.fragment`** (MODIFY)
   - Extend `_comment` to mention `statusLine` field.
   - Add top-level `"statusLine"` key documenting the post-self-retire reference shape: `{"type": "command", "command": "${POS_V2_REPO}/.venv/bin/python ${POS_V2_REPO}/hands-off-lifecycle/hooks/statusline.py", "refreshInterval": 1}`.
   - Sealed-fragment role unchanged — documents post-self-retire shape, not a hand-merge recipe.

### Source — orchestrator (existing admitted bucket)

6. **`orchestrator/scripts/pos_session_start.py`** (MODIFY — D5 retrofit)
   - Append a fail-soft post-`run_session_start` retrofit call. Derive `pos_v2_root = Path(__file__).resolve().parents[2]` (script lives at `<root>/orchestrator/scripts/pos_session_start.py`).
   - Lazy-import `merge_status_line` from the hooks dir (sys.path append `<root>/hands-off-lifecycle/hooks` first).
   - Build the same `_status_line_stanza` shape used by the worker.
   - Wrap entire retrofit in `try/except Exception: pass` — failure must not block supervisor's main path.
   - Implementation lives inside a small new `_maybe_install_status_line(pos_v2_root)` function called from `main()` after `print(result["additional_context"])` so a partial/ready/error supervisor outcome still gets retrofit attempts.

### Tests — `hands-off-lifecycle/tests/`

One file per AC (mirrors #46 / #48 convention). Test fixtures use the existing `tmp_path` + `FirstRunState` pattern; no real `~/.pos/` writes.

7. `test_AC_SL_1_renderer_active_phases.py` — covers AC.SL.1.
8. `test_AC_SL_2_renderer_completion_steady_state_then_blank.py` — covers AC.SL.2 (two sub-tests: ≤ 60s, > 60s).
9. `test_AC_SL_3_renderer_failed_glanceable_summary.py` — covers AC.SL.3.
10. `test_AC_SL_4_renderer_absent_or_foreign_state.py` — covers AC.SL.4 (two sub-tests).
11. `test_AC_SL_5_renderer_silent_death.py` — covers AC.SL.5.
12. `test_AC_SL_6_settings_json_post_self_retire_carries_status_line.py` — covers AC.SL.6 (uses existing `tmp_path` fresh-workspace fixture pattern from `test_first_run.py`).
13. `test_AC_SL_7_merge_status_line_backs_up_user_authored.py` — covers AC.SL.7.
14. `test_AC_SL_8_supervisor_retrofits_completed_workspace.py` — covers AC.SL.8.
15. `test_AC_SL_9_renderer_stdlib_only.py` — covers AC.SL.9 (import audit: parse renderer source with `ast`; collect imports; assert each top-level module is in stdlib).

AC.SL.S (seal-diff confinement) is covered by the existing `test_no_sealed_amendments.py` per touched component + `test_cross_cutting.py`'s H19. No new test file required.

### Plans / manifest

16. `docs/rebuild/plans/bootstrap-progress-statusline.md` — already on disk; gets committed as part of amendment.
17. `docs/rebuild/plans/bootstrap-progress-statusline.builder-plan.md` — this file; committed.
18. `docs/rebuild/plans/bootstrap-progress-statusline.manifest.yaml` (NEW) — see §3.

---

## 3. Manifest shape

```yaml
schema_version: 1
amendment:
  number: 49
  slug: bootstrap-progress-statusline
  title: "bootstrap-progress visualization in Claude Code's terminal status line"

baseline: 052b49b...   # full SHA at dispatch — pre-amendment HEAD

plan: docs/rebuild/plans/bootstrap-progress-statusline.md

seal_description: "bootstrap-progress visualization in Claude Code statusLine"

components:
  - name: hands-off-lifecycle
    seal_test: hands-off-lifecycle/tests/test_cross_cutting.py
    sidecar: hands-off-lifecycle/tests/SEAL_COMMIT
    frozen_baseline: true   # H19 pinned at project-start per amendment #23

universal_paths:
  prefixes:
    - docs/rebuild/plans/
  files:
    - CLAUDE.md
    - docs/odd-in-pos.md
    - docs/odd-methodology.md
    - docs/rebuild/FUTURE_IDEAS.md

narrative:
  target: hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run
  body: |
    # Amendment #49 — bootstrap-progress visualization in Claude Code's
    #                  terminal status line
    [...]
```

Single sealed component (`hands-off-lifecycle`). `orchestrator/` is admitted via `test_cross_cutting.py`'s H19 allowed-set (already in there). The retrofit edit to `pos_session_start.py` lives under `orchestrator/` — a top-level prefix already admitted at H19.

---

## 4. Order of edits

1. Manifest authored to disk.
2. `pos-amend apply --dry-run` smoke against the empty-diff manifest.
3. Source edits in this order:
   1. `first_run_state.py` — `progress_pct` field.
   2. `statusline.py` — renderer body.
   3. `first_run_settings.py` — `merge_status_line` + predicate + markers.
   4. `first_run_helper.py` — `_status_line_stanza`, `_maybe_merge_status_line`, `_PHASE_PCT`, `_advance_state` extension, two call-site additions (Phase 3d and Phase 6 self-retire).
   5. `settings.json.fragment` — comment + `statusLine` key.
   6. `pos_session_start.py` — supervisor retrofit.
4. Test files in matching order, each run as it lands.
5. Full `hands-off-lifecycle/tests/` suite (narrow-scope per amendment-dispatch CDC).
6. Other 12 sealed components: seal-diff-only.
7. `pos-amend apply --dry-run` — green gate.
8. `pos-amend apply` — apply manifest tuple/sidecar edits.
9. Stage + amendment commit.
10. Post-amendment narrow-scope test run.
11. `pos-amend seal --plan-doc docs/rebuild/plans/bootstrap-progress-statusline.md` — sidecar bumps + narrative + plan-doc SHA section.
12. Seal commit (separate; produced by `pos-amend seal`).
13. Post-seal seal-diff sweep (the `pos-amend seal` step runs this automatically).

---

## 5. Halt-and-surface re-check

Reading the plan §12 halt triggers against present-state:

1. **D-decisions vs ACs.** D1=a → `progress_pct` schema field is referenced by AC.SL.1 (rendered line includes elapsed/estimate; the `progress_pct` is method-level, not AC-text). No contradiction.
2. **Edits outside fence.** The retrofit edit to `pos_session_start.py` is under `orchestrator/` — admitted at H19. The plan §7 lists it under "`orchestrator/scripts/` (read-only check)" and then calls it out as MODIFY iff D5=retrofit on. D5 is locked on. Compliant with named scope.
3. **ODD violation in surrounding code.** `first_run_helper.py` Phase 3d call site already has parallel `_maybe_merge_session_start`/`_maybe_merge_user_prompt_submit`/`_maybe_merge_stop` per amendments #45/#46/#48. Adding `_maybe_merge_status_line` follows the same shape — no §2.5 violation introduced or extended.
4. **Status-line schema.** Plan §13 reference doc unchanged at research time; no halt.
5. **Cross-cutting overlap.** Amendment #48 landed at `74cdf4e` + sealed `452e7d4` + plan-SHAs `052b49b`. No in-flight amendment overlaps the statusLine surface.
6. **Stdlib-only feasibility.** `first_run_state.read_state` uses only stdlib (`json`, `pathlib`, `os`, `time`); `is_stale_live_state` likewise. Renderer can compose without third-party deps. ✓
7. **AC-shape feasibility.** Every AC.SL.x is outcome-shaped (rendered output / settings.json post-state / file presence). No method prescription in AC text.
8. **statusLine surface unsuitability.** Not encountered — research §1 confirmed `refreshInterval=1` polling works.

No halt triggered.

---

## 6. AC → code path map (ODD §2.5 reverse trace)

| AC | Code path |
|---|---|
| AC.SL.1 | `statusline.py::_render_active` (called when `state.status ∈ {starting, running}` and not stalled). |
| AC.SL.2 | `statusline.py::_render_completed` (60s gate inside). |
| AC.SL.3 | `statusline.py::_render_failed`. |
| AC.SL.4 | `statusline.py::main` early-returns: state-file absent → empty; `_state_belongs_to` mismatch → empty. |
| AC.SL.5 | `statusline.py::_render_stalled` (mirrors `is_stale_live_state` semantics). |
| AC.SL.6 | `first_run_helper.py::_self_retire` calls `_maybe_merge_status_line` → settings.json gains `statusLine` entry post-Phase-6. |
| AC.SL.7 | `first_run_settings.py::merge_status_line` backup branch when prior value not pos-v2-owned. |
| AC.SL.8 | `pos_session_start.py::_maybe_install_status_line` retrofit on supervisor path. |
| AC.SL.9 | `statusline.py` imports limited to `json`, `os`, `pathlib`, `sys`, `time`, plus relative `from first_run_state import …`. |
| AC.SL.S | Seal-diff confinement; tested by `test_cross_cutting.py::test_H19_diff_scope_covers_only_approved_surfaces`. |

No introduced code path lacks a backing AC.

---

## 7. Open builder-side considerations (no halt; method)

- **statusLine envelope schema:** Claude Code accepts `{"type": "command", "command": "...", "refreshInterval": 1}` at top-level `statusLine`. Single object, not a list (unlike `hooks.<event>`).
- **Static phase→duration table values:** seeded from the helper's "~5 minutes total" advertised figure + Phase 3b's "1-3 minutes" / Phase 3c's "60-90s heavy deps" / Phase 4b's `timeout_s=60.0`. Builder calibrates plain-language remaining-time strings; precision is method-level.
- **Renderer's elapsed-time format:** "Xm Ys" for ≥ 60s elapsed, "Ys" otherwise. Plain English.
- **Defence-in-depth import path:** the renderer imports `first_run_state` from its sibling directory; the script's own file location resolves the directory at runtime via `Path(__file__).resolve().parent`, the same shape `first_run_helper.py` uses (line 63–65).

---

## 8. Test commands

Pre-amendment:
```
.venv/bin/pytest hands-off-lifecycle/tests/ -q
```
Post-each-edit (incremental):
```
.venv/bin/pytest hands-off-lifecycle/tests/test_AC_SL_*.py -q
```
Pre-seal narrow scope (skip per amendment-dispatch CDC if pre-seal diff is sidecar/narrative-only):
```
.venv/bin/pytest hands-off-lifecycle/tests/ -q
```
Sealed-component sweep:
```
pos-amend seal docs/rebuild/plans/bootstrap-progress-statusline.manifest.yaml --plan-doc docs/rebuild/plans/bootstrap-progress-statusline.md
```
(`pos-amend seal` runs the `test_no_sealed_amendments.py` sweep across all 12 sealed components automatically.)
