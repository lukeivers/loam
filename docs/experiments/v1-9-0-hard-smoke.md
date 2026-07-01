# v1.9.0 HARD smoke writeup — dev→build→deploy spine P1 LOCAL tier + refinements

**Date:** 2026-07-01. **Release:** v1.9.0 — MINOR increment over published
v1.8.0 (`next_MINOR(v1.8.0) = v1.9.0`). Objective: loam ships the first deploy
tier on the sealed deploy-safety floor — a non-technical owner can build and
verify their project against a LOCAL environment (floor idle, proof in the
shared build→deploy shape); rolled up with a model-lineup capability-refresh, a
memory-volatility read disposition that stops a stale operational-status claim
being recalled as current (its durable decision preserved), and a
work-visibility hook-output fix.

**Staging topology:** prep + smoke ran DIRECTLY on `main` in the canonical tree
`/Users/lukeivers/loam` — no concurrent session owns the canonical tree this
cut, so no isolated worktree was needed. The `branch-main` gate therefore
resolves GREEN.

**Release HEAD at smoke:** `1bc5328b` — `main` tip after the lockstep
version-bump + release bookkeeping commit. The cold clone reports `loam 1.9.0`
directly (the bump is in the smoke window).
**Reconcile (Tier-0):** `git rev-list --left-right --count origin/main...HEAD` at
the pre-bookkeeping tip = `0 0` — a clean linear state, zero divergence, zero
merge commits. The release-window content tip `5e96f08f` (capability-refresh
model-lineup seal) is reachable from HEAD (Tier-0: `git merge-base --is-ancestor
5e96f08f HEAD` → yes).
**Last published (Tier-0, git ref):** `v1.8.0` annotated tag `b6df7e4` → content
tip `3225eeee` (reachable from HEAD as ancestor).
**Secret scan (pre-push, public repo):** `v1.8.0..HEAD` diff scanned for
API-key / GitHub-token / AWS-key / Slack-token / private-key / Telegram-bot-token
patterns — **0 real secret-bearing matches** (the only hits are documentation
prose in the v1.8.0 smoke writeup naming `ANTHROPIC_API_KEY` /
`TELEGRAM_BOT_TOKEN` as words in the isolation recipe, not credential values);
no `.env`/`.pem`/credentials filenames added in the window.
**Subscription mode** — no `ANTHROPIC_API_KEY`; no `anthropic` SDK (per
`feedback_no_anthropic_api_key`). **python:** 3.13.2 venv for the cold install
and every probe.

**Aggregate verdict: GREEN.** (One classified pre-existing-environmental
cold-clone failure — `test_AC_MSC_3`, the same cold-clone sensitivity the v1.7.0
smoke documented — proven to PASS in the canonical dev-mode tree; untouched by
any v1.9.0 cycle; not a v1.9.0 regression. See §6 + §10.)

---

## §1 — Probe design (per `feedback_hard_smoke_per_minor_before_publish`)

HARD bar: a REAL cold-clone of the release HEAD + a REAL editable install with
no API key + a REAL spawn-isolated `claude -p` (per
`feedback_spawned_claude_must_isolate_telegram_plugin`) + the v1.9.0 capabilities
reproduced at outcome altitude from the cold tree + the touched-component
regression ride-alongs swept from the cold tree. The v1.9.0 window introduces
ONE NEW top-level component (`local-deploy-tier`, 0.1.0 out-of-graph),
ADDITIVELY extends sealed `primary-persona` (memory-volatility read disposition +
the work-visibility hook fix), extends the sealed `deploy-safety-floor` (the
fail-policy adoption de-dup), and extends `capability-refresh` (model-lineup
tracking).

## §2 — Cold clone

A fresh `git clone --no-local file://.../.git` of the release HEAD into
`.scratch/smokes/v1-9-0-smoke`. Clone HEAD verified ==
`1bc5328ba6eb05062aac296359c71fa321b96bfc` (the `main` tip). Cold clone reports
`docs/ACTIVE_MINOR` = `1.9.0`. No shared venv or state.

## §3 — Editable install from the manifest

`python3.13 -m venv .venv` + `pip install -r install-from-source.txt` in the
cold clone. **Install exit 0.** The lockstep dists installed at `1.9.0`
(loam-cli-1.9.0, loam-primary-persona-1.9.0, loam-safety-layer-1.9.0,
loam-deploy-safety-floor's siblings, …) — the lockstep bump is coherent across
the full install graph. **`loam --version` from the cold install → `loam
1.9.0`.** GREEN.

**New-component install-graph wiring:** `local-deploy-tier` is correctly NOT in
the install graph (0.1.0, OUT-of-graph per D-LOCK) — it ships out-of-graph, so
it is correctly EXCLUDED, not broken. Its tests run from the cold source tree
via the component's `conftest.py` (the self-contained pattern). GREEN.

## §4 — Spawn-isolated `claude -p` (the bot-slot protection)

```
echo 'Reply with exactly the two words: SMOKE OK' | \
  env -u ANTHROPIC_API_KEY -u TELEGRAM_BOT_TOKEN -u DISCORD_BOT_TOKEN \
  CLAUDE_PERSONA=loam-smoke-v190 \
  claude -p --strict-mcp-config --mcp-config .scratch-empty-mcp.json
→ SMOKE OK   (exit 0)
```

A genuine model response, subscription-mode, with the telegram + discord plugins
NOT loaded (`CLAUDE_PERSONA` set + `--strict-mcp-config` + an empty
`{"mcpServers":{}}` config + scrubbed bot tokens). Protects the live bot slot per
`feedback_spawned_claude_must_isolate_telegram_plugin` — an un-isolated
`claude -p` would SIGTERM-steal the one bot slot and drop the owner's live
channel session. GREEN.

## §5 — Outcome-altitude: the v1.9.0 deltas at outcome altitude (cold tree)

Reproduced from the cold tree with NO pre-arranged state, through production
entry points (AC.REL.S):

**Delta 1 — the LOCAL deploy tier produces an acceptance record in the shared
proof shape with a command-set carrying no irreversible verb (AC.LOCAL.C).** The
outcome-altitude test
`framework/local-deploy-tier/tests/test_AC_LOCAL_C_outcome_altitude.py` runs
within the **28 passed** local-deploy-tier suite (**4 passed** for the OA test in
isolation): a non-technical owner builds + verifies against a LOCAL environment
and gets an acceptance record in the shared P0 proof shape; the LOCAL command-set
carries no irreversible verb; secrets come from the keychain, never committed.
GREEN.

**Delta 2 — a HARD-volatile operational-status claim is FILTERED from the current
recall view while its history stays queryable (AC.VOL.5).** The outcome-altitude
test `framework/primary-persona/tests/test_AC_VOL_5_outcome_altitude_e2e.py`
passes: a real `write_episode` of a HARD-volatile status claim, then a real
`search`, and the current view no longer surfaces the stale status while the
durable record's history remains queryable. GREEN.

**Delta 0 — `loam --version` → `loam 1.9.0`** from the cold install (§3). GREEN.

## §6 — Touched component suites (cold tree)

| Suite | Result |
|---|---|
| `framework/local-deploy-tier/tests/` | **28 passed** (AC.LOCAL.1-4 + AC.LOCAL.C-OA; out-of-graph, via conftest) |
| `framework/deploy-safety-floor/tests/` | **28 passed** (incl. AC.DSF.8 fail-policy-adoption: **4 passed** for the `-k DSF_8/fail_policy` slice) |
| `framework/tools/capability-refresh/tests/` | **32 passed** (AC.CLP-MDL.1-4 incl. the `claude-sonnet-5` outcome-altitude miss + the pre-existing AC.CLP-CUR suites) |
| `framework/primary-persona/tests/` (VOL + WVS-HOOK-EN slice) | VOL + WVS **43 passed**; WVS-HOOK-EN family **19 passed** (incl. `test_AC_WVS_HOOK_EN_3_outcome_altitude_main`); VOL.5 OA **1 passed** |
| `framework/primary-persona/tests/` (FULL regression sweep) | **1287 passed, 1 skipped, 1 failed** — the single failure is `test_AC_MSC_3_canonical_claude_dev_md_carries_named_surface` (see §10) |
| `plugins/dev-sdlc/tests/` | **396 passed, 7 skipped** (incl. the lockstep AC.PCVR at 1.9.0) |
| `plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py` | **5 passed** at the 1.9.0 lockstep state (31 in-scope pyprojects + meta `loam --version` coherently advanced) |

Every v1.9.0-TOUCHED surface passes clean. The single full-sweep failure is a
documented cold-clone-environmental carry-over, classified in §10.

## §7 — Gate evidence — system binary operational

```
loam --version  → loam 1.9.0
loam --help     → exit 0; subcommands include:
   {report, amend, migrate, project, guards, pr-safety, release, audit,
    flow, init, recover, onboard, workspace, odd-extract, init-intake}
```

All documented subcommands present; `loam --version` reports `1.9.0`; exit 0.
The cold-install `.venv/bin/loam` is the authoritative version-reporting binary
for this staging smoke. GREEN.

## §8 — Lockstep version coherence (AC.REL.2)

`docs/ACTIVE_MINOR` = `1.9.0`; the 31 in-scope `pyproject.toml` `[project]`
version fields = `1.9.0` (Tier-0 sweep: ALL 31 in-scope == 1.9.0, none left at
1.8.0; 0 non-in-scope pyprojects at 1.8.0 or 1.9.0 by accident); the meta `loam
--version` literal (`loam_cli/__init__.py __version__`) = `1.9.0`. The lockstep
regression test `test_AC_PCVR_pyproject_version_lockstep.py` → 5 passed at the
1.9.0 state (both in the canonical tree and from the cold clone). The NEW
`local-deploy-tier` (0.1.0) is EXCLUDED from the in-scope set per D-LOCK (new
component out-of-graph). GREEN.

## §9 — The nine `loam release --dry-run` gates

Captured via `loam release v1.9.0 --dry-run` from the canonical tree (on `main`),
resolving the plan-doc + smoke writeup via the version-slug glob (NO `--plan-doc`
flag). See §11 for the per-gate verdicts.

## §10 — Findings

**No blocker findings.** One non-blocking, classified finding:

**Finding 1 (pre-existing-environmental; NOT a v1.9.0 regression):**
`framework/primary-persona/tests/test_AC_MSC_3_named_thread_surface_in_corpus.py::
test_AC_MSC_3_canonical_claude_dev_md_carries_named_surface` FAILS from the cold
clone (`emit_session_start_context(repo_root, ...)` returns `''` because dev-mode
detection does not resolve in a bare isolated clone). Tier-0 classification:
(a) **untouched by v1.9.0** — `git diff --name-only v1.8.0..HEAD` shows no change
to the MSC_3 test or the `loam_mode.session_start` emitter; the only
primary-persona source touched this window is `file_memory.py` /
`hooks_work_visibility.py` / `keep_pace/retrieval.py`; (b) **proven
environmental** — the SAME test PASSES (4 passed) when run in the canonical
dev-mode tree `/Users/lukeivers/loam`, so the failure is the cold-clone dev-mode
detection sensitivity, not the code; (c) **documented prior** — this is the exact
"single `test_AC_MSC_3` cold-clone sensitivity" the v1.8.0 smoke writeup named
against the v1.7.0 smoke. Same-known-set discipline (AC.REL.4): classified
pre-existing-environmental, does NOT block the release.

## §11 — §status — the release gates (`loam release v1.9.0 --dry-run`)

`loam release v1.9.0 --dry-run` run from the canonical tree on `main`
(post-bookkeeping + post-writeup commit), resolving the plan-doc + smoke writeup
via the `v1-9-0-*` version-slug glob (no `--plan-doc` flag). Captured verdicts:

| Gate | Verdict | Evidence |
|---|---|---|
| 1 hard-smoke | **GREEN** | GREEN aggregate-verdict token at this writeup path (`docs/experiments/v1-9-0-hard-smoke.md`) |
| 2 acs-verified | **GREEN** | all 8 AC.REL.* GREEN in `docs/plans/v1-9-0-release-integration-spine-p1-local.md` §13 §status |
| 3 state-shipped | **GREEN** | v1.9.0 marked SHIPPED LOCAL in `docs/STATE.md` |
| 4 clean-tree | **GREEN** | working tree clean (bookkeeping + writeup committed) |
| 5 branch-main | **GREEN** | on branch `main` (built directly on main, no worktree this cut) |
| 6 seal-reachable | **GREEN** | seal `5e96f08f` reachable from HEAD |
| 7 migration-declared | **GREEN** | `v1-9-0-spine-p1-local.migration.yaml` declares `version: v1.9.0` + `operation: no-op` |
| 8 substrate-audit | **GREEN** | no shipping-status claim diverges from the derived STATE-OF-LOAM record |
| 9 boundary-respected | **GREEN** | no framework-code write lands user-state outside the two declared homes |

**9 GREEN / 0 RED.** (Filled from the actual dry-run run — see §12.)

## §12 — Verdict

**GREEN on all smoke dimensions** (cold-clone install exit 0 + `loam 1.9.0` +
spawn-isolated `claude -p` SMOKE OK exit 0 + LOCAL deploy tier acceptance-record
OA within 28 passed + memory-volatility filtering OA (AC.VOL.5) + DSF.8
fail-policy adoption within 28 passed + capability-refresh model-lineup 32 passed
+ primary-persona 1287 passed with the one classified cold-clone-environmental
carry-over + dev-sdlc 396/7skip + lockstep AC.PCVR 5 passed at 1.9.0 + system
binary operational at 1.9.0). The single `test_AC_MSC_3` failure is
pre-existing-environmental (proven to pass in the canonical tree), not a v1.9.0
regression, and does not block the release. The public tag + push + GitHub
Release proceed ONLY under the owner's explicit command (this smoke does NOT
publish).
