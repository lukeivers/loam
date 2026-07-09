# v1.13.0 HARD smoke writeup — Tilth operational-backplane integration

**Version:** v1.13.0 (MINOR over published v1.12.0). **Class:** MINOR.
**Release content tip (cold-clone target):** `c578a231` (integration branch `integration/backplane` HEAD: four stack merges + main sync + substrate + lockstep bump `ebbfec9e` + release-prep docs). **Tag target (dominating seal):** `1e42e028`.
**Per-minor HARD smoke gate** per `feedback_hard_smoke_per_minor_before_publish`: a real cold clone of the release content tip, a real editable install into a fresh Python 3.13 venv, the system binary exercised, clean-cwd import of all eight backplane packages, the seven touched-component suites on the cold tree, a real spawn-isolated `claude -p` leg end-to-end, the outcome-altitude cross-package fleet-page render at the production entry-point over REAL data, and the F-LEAK / F-VERIFY-ORPHAN ride-alongs.

**Aggregate verdict: GREEN.**

---

## §1 — Probe design

Cold clone of the release content tip into a temp dir → fresh Python 3.13 venv → `pip install -r install-from-source.txt` → exercise `loam --version` + the system binary → clean-cwd import of all eight packages → the seven touched-component suites on the cold tree → a real subscription-mode spawn-isolated `claude -p` via the sealed `loam_spawn_isolation.spawn_isolated_claude` surface → the outcome-altitude fleet-page render over a REAL fleet-collector run → the leak / orphan-spawn ride-alongs. No pre-set release state.

## §2 — Cold-install evidence

- `git clone <local> && git checkout c578a231` → cold tree at `c578a231`.
- `pip install -r install-from-source.txt` into the fresh Python 3.13 venv: **exit 0**, no errors. (First attempt on a stray Python 3.9 shim failed the `requires-python >=3.11` guard — re-run under `python3.13`; a correct floor-enforcement signal, not a defect.)
- `loam --version` → **`loam 1.13.0`** (Tier-0, from the cold-install venv `.../venv/bin/loam`); maintainer system binary `which loam` → `/opt/homebrew/bin/loam`.

## §3 — Clean-cwd import (coexistence, from a cwd OUTSIDE the repo)

All eight resolve from `/tmp` against the cold-install venv — the coexistence "done":

```
OK  loam.file_lease_registry     OK  loam.weekly_cost_rollup
OK  loam.fleet_collector         OK  loam.cost_governance
OK  loam.fleet_page              OK  adversarial_review
OK  loam.weekly_cap_alert        OK  loam.usage_window_guard
```

The install is driven PURELY by `install-from-source.txt` (the six backplane `-e ./framework/<pkg>` lines added this cut) — no ad-hoc `-e` for the eight.

## §4 — Capability + regression suites (cold-install venv, content tip `c578a231`)

Seven touched-component suites, run per-component on the cold tree (per-component isolation is loam's own convention; a single multi-dir invocation trips pytest's duplicate-basename collision, not a code defect):

| Component | Result |
|---|---|
| file-lease-registry | 9 passed |
| fleet-collector | 10 passed |
| fleet-page | 14 passed |
| weekly-cap-alert | 16 passed |
| weekly-cost-rollup | 11 passed |
| cost-governance | 81 passed |
| adversarial-review | 77 passed, 2 skipped |

**Total: 218 passed, 2 skipped.** The two adversarial-review skips are the real-Codex-CLI smoke legs (no Codex binary on the smoke host) — environmental, not a defect.

## §5 — Seal integrity (the two sealed fences)

Both sealed seal-tests GREEN on the merge-topology history (the disjoint A-stacks did not widen either fence; NO re-seal needed) — verified on the integration tree and re-confirmed post-lockstep-bump:

- `framework/cost-governance/tests/test_no_sealed_amendments.py` — 1 passed.
- `framework/adversarial-review/tests/test_no_sealed_amendments.py` — 1 passed.
- `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` — 2 passed (the lockstep bump's IN_SCOPE fold-in edit is outside the fence window).

## §6 — Real spawn-isolated `claude -p` SMOKE

Ran a real subscription-mode isolated `claude -p` on the cold-installed tree via the mandated sealed surface `loam_spawn_isolation.spawn_isolated_claude` (empty-strict-MCP isolation injected, env token/API-key-scrubbed, `CLAUDE_PERSONA` set, isolation asserted before spawn):

```
rc: 0
CONTAINS_SMOKE_OK_V1130: True
output: SMOKE_OK_V1130
```

A real isolated leg returned its exact token — no hang, no Telegram/Discord-kill vector (empty-strict-MCP isolation), subscription credential resolved on the cold tree.

## §7 — Outcome-altitude cross-package render (production entry-point, no pre-set state)

The `fleet-page` production entry-point `generate_page(out_path, *, fleet_source, cost_source, decisions_source)` wrote real HTML over a REAL cross-package path, from a clean cwd against the cold venv:

- **fleet_source** = `sources.read_fleet` bound to `framework/tools/handsoff-loop/smoke` → a REAL `fleet-collector` run over 2 genuine on-disk handsoff-loop run records (`run_record.jsonl` + `run_summary.json`) — the page renders their real objectives (a round-robin scheduler build).
- **cost_source** = `sources.read_cost_rows` → the REAL observability-aggregator `QueryAPI.cost_by_prompt`.
- **decisions_source** = `sources.read_decisions` over `discover_pm_dirs("/Users/lukeivers/pos3")` → 4 REAL per-project-pm decision dirs.

Result: a 3915-byte HTML with all four panels (`Live agents`, `Recent outcomes`, `This week's cost`, `Needs a human`), overflow-guarded (`max-width:1100px` centered container + `.scroll{overflow-x:auto}` on wide tables — no horizontal body overflow), both themes via `prefers-color-scheme`. The cross-package path (fleet-page → fleet-collector + observability-aggregator + per-project-pm) resolved LIVE over real records with no pre-set state — the feature sub-plan's AC.BPI.5 outcome-altitude criterion.

## §8 — F-LEAK / F-VERIFY-ORPHAN ride-alongs

- **F-LEAK (settings.json / MCP write-surface): GREEN.** The fleet-page RENDER path (`generate_page` → `render.py`) does NOT touch `.claude/settings.json` / MCP config (verified — it writes only the caller-specified `out_path` HTML). The `.claude/settings.json` references in `fleet_page/schedule.py` are the EXPLICIT launchd scheduler-install verb (`install_launchd_job`, a user-invoked install action), not the render/collect path. `weekly-cap-alert` reads/writes its OWN config file (`~/.claude/weekly-cap-alert.json`); `weekly-cost-rollup` READS `~/.claude/projects` transcripts (read-only, the token proxy). None writes `settings.json` / MCP config on the render/collect path.
- **F-VERIFY-ORPHAN (un-isolated `claude` binary spawn): GREEN.** The only new-component `subprocess.run` is `weekly-cap-alert/notify.py`, which spawns a USER-PROVIDED `--notify-cmd` (loam stays channel-agnostic; the workspace names whatever command reaches the owner). It does NOT spawn the `claude` binary. The five new components spawn no `claude` process; the sole real claude-spawn path in the smoke is the sealed `spawn_isolated_claude` surface (§6).

## §9 — Versioning + lockstep

- `test_AC_PCVR_pyproject_version_lockstep` GREEN (5 passed): `docs/ACTIVE_MINOR` 1.13.0; the 31 existing in-scope pyprojects + the six FOLDED-IN backplane components (five new + adversarial-review) all at 1.13.0 (IN_SCOPE now 37); the two excluded 0.0.0 measurement harnesses unchanged.
- `loam --version` reports `1.13.0` from the cold-install venv (the meta `__version__` literal advanced in lockstep, commit `ebbfec9e`).

## §10 — Verdict

**GREEN on all smoke dimensions.** Cold clone + real editable install at 1.13.0; system binary operational; all eight packages import from a clean cwd via `install-from-source.txt` alone; the seven touched-component suites pass on the cold tree (218 passed / 2 skipped, the two skips environmental); both sealed fences intact (no re-seal); a real subscription-mode spawn-isolated `claude -p` leg returned its exact token; the outcome-altitude fleet-page render resolved the live cross-package path over REAL run records at the production entry-point; F-LEAK / F-VERIFY-ORPHAN clean; lockstep + migration honest.
