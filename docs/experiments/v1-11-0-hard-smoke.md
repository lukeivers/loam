# v1.11.0 HARD smoke writeup — memory substrate + model-lineup honesty

**Date:** 2026-07-08. **Release:** v1.11.0 — MIXED MINOR increment over published v1.10.0 (`next_MINOR(v1.10.0) = v1.11.0`). Objective: harden loam's per-user memory substrate (recall bounded only by relevance + attention; write path curbs confidently-wrong facts) and keep the automated model-lineup tracking honest against upstream formatting drift.

**Staging topology:** built DIRECTLY on `main` in the canonical tree (`/Users/lukeivers/loam`, single-writer this cycle). Because the release is on `main`, gate-5 (`branch-main`) is satisfiable at dry-run (unlike a worktree stage).

**Release content tip at smoke:** `badd2d6f` — HEAD after the four component seals + lockstep bump + bookkeeping (this smoke-writeup + §status backfill commits land on top).
**Four-fence seal windows (Tier-0, each window = own delta):**
- capability-refresh model-extractor (AC.CLP-MDLR.1-5): source `927639ac` · apply `4cd0b821` · seal `f2d88060`.
- memory write-side facts-discipline (AC.WFD.1-9): plan+source `6d0e20a5` · apply `fb0cf1f2` · seal `c9c94f0d`.
- recall volume-limits reshape (AC.RVL.1-9): source `ec9dd982` · apply `c17fb90` · seal `2cd8b714`.
- dev-sdlc KDOC line-budget raise (AC.MSLB.1): tests `4094467b` · apply `20700c2` · seal `badd2d6f`.

**Reconciliation:** the first three cycles based at merge-base `a1166b8`, which `main` had advanced 7 commits past (PR #3, a separate capability-refresh seal #194); none was fast-forwardable and the model-extractor branch conflicted on the capability-refresh `SEAL_COMMIT` sidecar. Reconciled by re-apply/re-seal against current main baseline (S1a precedent); source sha256-identical to the branch work; original branches preserved as source-of-record.

**Last published (Tier-0, git ref):** `v1.10.0` tag `fbf9d5a` (ancestor of HEAD).
**Secret scan:** no secrets introduced. All four cycles are stdlib-only source/test/doc edits; no `.env`, credential, or token file added.
**Subscription mode** — no `ANTHROPIC_API_KEY`; no `anthropic` SDK. The real `claude -p` spawn (§4) used the subscription credential via the sealed `loam_spawn_isolation` surface.

**Aggregate verdict: GREEN.**

---

## §1 — Probe design

Full per-MINOR HARD smoke per `feedback_hard_smoke_per_minor_before_publish`: a real cold-clone of the release content tip, a real editable install into a fresh venv, the system binary exercised, a real spawn-isolated `claude -p` leg end-to-end, an outcome-altitude fixture exercising the new recall behavior at the production entry-point, and the touched-component + ride-along regression suites — all against the cold-installed tree.

- Cold clone: `git clone --no-local /Users/lukeivers/loam` → fresh tree, then advanced to the final content tip `badd2d6f`.
- Fresh venv (pyenv Python 3.13.2) + `pip install -r install-from-source.txt`.
- Interpreter/keys: subscription mode, no API key.

## §2 — Cold-install evidence

`pip install -r install-from-source.txt` into the fresh venv: **exit 0**, no errors. Every in-scope component installed at **1.11.0** (`loam-cli 1.11.0`, `loam-primary-persona 1.11.0`, `loam-plugin-dev-sdlc 1.11.0`, `loam-amend 1.11.0`, `loam-mode 1.11.0`, `loam-odd-extractor 1.11.0`, `loam-pr-safety 1.11.0`, … the full in-scope cohort — the "not-at-1.11.0" check returns empty, excluding the deliberate 0.x/0.0.0 out-of-scope harnesses).

**System binary operational (release-process gate 7):**

- `loam --version` → `loam 1.11.0` (Tier-0, from the cold-install venv AND the maintainer system binary `/opt/homebrew/bin/loam`).
- `loam --help` → exit 0; lists the documented subcommands: `init`, `amend`, `release`, `odd-extract`, `onboard`, `pr-safety`, `project` (plus `migrate`, `guards`, `report`, `recover`, `audit`, `flow`, `init-intake`, `workspace`).

## §3 — Capability + regression suites (cold-install venv, final content tip)

| Suite | Result |
|---|---|
| `framework/tools/capability-refresh/tests/` (touched — model-extractor) | **46 passed** |
| `framework/primary-persona/tests/` (touched — write-side + recall) | **full suite green (exit 0, no failures; ≈1410 passed / 1 skipped per the recall seal, re-run green)** |
| `plugins/dev-sdlc/tests/` (touched — KDOC line-budget raise + ride-along release/lockstep/amend) | **399 passed, 7 skipped** |
| all four `test_no_sealed_amendments.py` seal fences | **pass** (each window = own delta only) |

**Cross-component collision caught and resolved by this smoke.** The initial cold-tree run flagged one failure: `plugins/dev-sdlc/tests/test_AC_KDOC_1::test_spec_at_most_360_lines` — the recall cycle's required AC.RVL.8 cap-bias checklist (§7.6 + reviewer item 15 in `odd-methodology.md`) grew that doc 360 → 373 lines, past dev-sdlc's ≤360 leanness guard. Two sealed constraints collided. Resolved (dispatcher-ruled) by a proper 4th dev-sdlc fence (AC.MSLB.1) raising the guard 360 → 380 per `feedback_loose_AC_text_fix_AC_not_implementation` — the guard's intent (no return of the dropped 8-lens sprawl) is preserved; a 13-line legitimately-required feature checklist is not that bloat. Post-fix the dev-sdlc suite is 399 passed / 7 skipped; `test_AC_RVL_8` (the checklist's own contract) stays green.

## §4 — Real spawn-isolated `claude -p` SMOKE

Ran a real subscription-mode isolated `claude -p` on the cold-installed tree via the mandated sealed surface `loam_spawn_isolation.spawn_isolated_claude` (empty-strict-MCP isolation injected, env token/API-key-scrubbed, isolation asserted before spawn):

```
import OK; spawn_isolated_claude present: True
returncode: 0
CONTAINS_SMOKE_OK_V1110: True
output: SMOKE_OK_V1110
```

A real isolated review leg returned its exact token — no hang, no Telegram-kill vector (isolation flags present, `--strict-mcp-config`), subscription credential resolved on the cold tree.

## §5 — Outcome-altitude fixtures (production entry-points, no pre-set state)

Cold-tree, hitting production entry-points with no pre-arranged release state:

- **AC.RVL.7** `test_AC_RVL_7_OA_production_retrieve_floor_over_count.py` (the new recall behavior — production `retrieve()`, floor over count): **passed** (3 cases). The count cap no longer truncates a relevant-memory set below the relevance floor.
- **AC.WFD.6** `test_AC_WFD_6_OA_end_to_end_write_read.py` (production write→read): **passed**.
- **AC.CLP-MDLR** `test_AC_CLP_MDLR_1_5_format_robust.py` + capability-refresh fence: **9 passed** (backtick-agnostic detection of the reformatted model-lineup).

## §6 — F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN ride-alongs

Window-scoped to the reconciled cycles' source diffs (`927639ac` cap-refresh, `6d0e20a5` write-side, `ec9dd982` recall; the dev-sdlc 4th fence is test-only):

- **F-LEAK (MCP-config / settings.json write-surface):** **GREEN.** Added-line scan for a `~/.claude` / `settings.json` / `expanduser` write path: the only hit is a design-doc line explicitly stating `settings.json` is NOT touched (a reference, not a write). No new path writes MCP/settings config beyond the workspace boundary.
- **F-TIMEOUT (claude-print client / subprocess timeout):** **GREEN by construction.** None of the three cycles touches `claude_print_client` / the synthesis client or its timeout config.
- **F-VERIFY-ORPHAN (un-isolated `claude` binary spawn):** **GREEN.** No new `subprocess`/`Popen` invocation of the `claude` binary in any added line; the only real spawn path used is the sealed `spawn_isolated_claude` surface (§4).

## §7 — Seal evidence (four fences)

- Four component seals, all HEAD-reachable: `f2d88060` (capability-refresh), `c9c94f0d` (primary-persona write-side), `2cd8b714` (primary-persona recall), `badd2d6f` (dev-sdlc KDOC raise).
- Each fence `test_no_sealed_amendments.py` passes with `BASELINE..SEAL_COMMIT` containing only that amendment's own delta.
- Post-seal `loam amend apply --dry-run` clean for each (verified by the seal step).
- Sidecars (Tier-0): capability-refresh `SEAL_COMMIT` = `4cd0b821`; primary-persona `SEAL_COMMIT` = `c17fb90` (recall apply, the latest primary-persona seal); dev-sdlc `SEAL_COMMIT` = `20700c2`.

## §8 — Versioning + lockstep

- `test_AC_PCVR_pyproject_version_lockstep` GREEN (5 passed): `docs/ACTIVE_MINOR` 1.11.0; the 31 in-scope pyprojects at 1.11.0; no out-of-graph component in the in-scope set.
- `loam --version` reports `1.11.0` from the cold-install venv AND the maintainer system binary (the meta `__version__` literal advanced in lockstep).
- Migration declared `no-op` (`docs/state-migrations/v1-11-0-memory-substrate-and-model-extractor.migration.yaml`): additive read-back-safe `epistemic:` frontmatter, query-only recall change, unchanged model-lineup artifact shape.

## §9 — Release-gate note

Release staged on `main` in the canonical tree, so gate-5 (`branch-main`) is satisfiable at dry-run. The `loam release v1.11.0 --dry-run` structural gates (hard-smoke GREEN token — this writeup; acs-verified — plan-doc §13 §status; state-shipped; branch-main; seal-reachable; migration-declared; substrate-audit; boundary-respected) are all satisfied. The clean-tree gate REDs ONLY on two pre-existing untracked `docs/plans/per-session-resume-handoff.*` files (NOT part of this cut; dispatcher-handled) — every other gate GREEN is the success bar. The public tag + `git push` + GitHub Release proceed ONLY under the owner's explicit command; they were NOT run.

## §10 — Verdict

**GREEN on all smoke dimensions.** Cold clone + real editable install at 1.11.0; system binary operational; the touched-component suites pass on the cold-installed tree (the one cross-component collision surfaced by this smoke was resolved as a proper 4th sealed fence); a real subscription-mode spawn-isolated `claude -p` leg returned its token; outcome-altitude recall + write fixtures pass at the production entry-point; F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN clean; four seals clean and HEAD-reachable; lockstep + migration honest.

The release is SEALED-LOCAL on this evidence. The public tag push + `git push origin main` + the GitHub Release proceed ONLY under the owner's explicit command — they were NOT run.
