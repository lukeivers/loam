# v1.8.0 HARD smoke writeup — deploy-safety FLOOR

**Date:** 2026-06-28. **Release:** v1.8.0 — MINOR increment over published
v1.7.0 (`next_MINOR(v1.7.0) = v1.8.0`). Objective: loam ships a framework-native
deploy-safety FLOOR — a destructive-action gate keyed off the *resolved
target's* production-ness with an attestation / refuse-all-destructive default,
a per-gate fail-policy primitive that makes the floor's destructive gates fail
CLOSED while advisory guards keep failing open, and a secure-build baseline
(secrets-never-committed at the commit boundary + a dependency-audit gate +
artifact-cleanliness) for the artifact loam PRODUCES.

**Staging topology:** prep + smoke ran DIRECTLY on `main` in the canonical tree
`/Users/lukeivers/loam` — no concurrent session owns the canonical tree this
cut, so no isolated worktree was needed (unlike v1.7.0's
`/Users/lukeivers/loam-release-v1.7.0-wt` staging). The `branch-main` gate
therefore resolves GREEN here rather than the v1.7.0 expected-RED artefact.

**Release HEAD at smoke:** `5c599341` — `main` tip after the lockstep
version-bump + release bookkeeping commit. The cold clone reports `loam 1.8.0`
directly (the bump is in the smoke window).
**Reconcile (Tier-0):** `git rev-list --left-right --count origin/main...main` =
`0 15` — a clean linear fast-forward, zero behind, zero merge commits. The
release-window content tip `3225eeee` (Sub-cycle C secure-build-baseline seal)
is reachable from HEAD (Tier-0: `git merge-base --is-ancestor 3225eeee HEAD` →
yes).
**Last published (Tier-0, git ref):** `v1.7.0` annotated tag → commit `7a6a1671`
(reachable from HEAD as ancestor; `gh release list` → `v1.7.0` Latest).
**Secret scan (pre-push, public repo):** `origin/main..main` diff scanned for
API-key / GitHub-token / AWS-key / Slack-token / private-key / Telegram-bot-token
patterns — the only matches are the secure-build-baseline's OWN test fixtures
(`AWS_KEY = "AKIAIOSFODNN7EXAMPLE"`, AWS's canonical documentation placeholder,
fed to AC.SBB.1 to prove the secret guard BLOCKS it) — **0 real secret-bearing
matches**; no `.env`/`.pem`/credentials filenames in the window;
`ANTHROPIC_API_KEY`/`TELEGRAM_BOT_TOKEN` string occurrences = 0.
**Subscription mode** — no `ANTHROPIC_API_KEY`; no `anthropic` SDK (per
`feedback_no_anthropic_api_key`). **python:** 3.13.2 venv for the cold install
and every probe.

**Aggregate verdict: GREEN.**

---

## §1 — Probe design (per `feedback_hard_smoke_per_minor_before_publish`)

HARD bar: a REAL cold-clone of the release HEAD + a REAL editable install with
no API key + a REAL spawn-isolated `claude -p` (per
`feedback_spawned_claude_must_isolate_telegram_plugin`) + the floor capabilities
reproduced at outcome altitude from the cold tree + the touched-component
regression ride-alongs swept from the cold tree. The v1.8.0 window introduces
TWO NEW top-level components (`deploy-safety-floor`, `secure-build-baseline`,
both 0.1.0 out-of-graph), ADDITIVELY extends sealed `safety-layer` (the per-gate
fail-policy primitive) + `secret_pattern_guard`, and adds `protection-matrix`
catalogue rows.

## §2 — Cold clone

A fresh `git clone` (`--no-local file://.../.git`) of the release HEAD into
`.scratch/smokes/v1-8-0-smoke`. Clone HEAD verified ==
`5c599341073577ee3e211e73a39fa76c9ac11af7` (the `main` tip). Cold clone reports
`docs/ACTIVE_MINOR` = `1.8.0` and the meta `__version__` literal = `1.8.0`. No
shared venv or state.

## §3 — Editable install from the manifest

`python3.13 -m venv .venv` + `pip install -r install-from-source.txt` in the
cold clone. **Install exit 0.** 27 lockstep dists installed at `1.8.0`
(loam-cli-1.8.0, loam-primary-persona-1.8.0, loam-safety-layer-1.8.0,
loam-protection-matrix-1.8.0, …) — the lockstep bump is coherent across the full
install graph. **`loam --version` from the cold install → `loam 1.8.0`.** GREEN.

**New-component install-graph wiring:** `deploy-safety-floor` +
`secure-build-baseline` are correctly NOT in the install graph (Tier-0: 0
matching lines in `install-from-source.txt`; `importlib.find_spec('deploy_
safety_floor')` does not resolve from the cold `.venv`) — they ship at 0.1.0
OUT-of-graph per D-LOCK, so they are correctly EXCLUDED, not broken. Their tests
run from the cold source tree via each component's `conftest.py` (the
self-contained pattern). GREEN.

## §4 — Spawn-isolated `claude -p` (the bot-slot protection)

```
echo 'Reply with exactly the two words: SMOKE OK' | \
  env -u ANTHROPIC_API_KEY -u TELEGRAM_BOT_TOKEN -u DISCORD_BOT_TOKEN \
  CLAUDE_PERSONA=loam-smoke-v180 \
  claude -p --strict-mcp-config --mcp-config .scratch/empty-mcp-v180.json
→ SMOKE OK   (exit 0)
```

A genuine model response, subscription-mode, with the telegram + discord plugins
NOT loaded (`CLAUDE_PERSONA` set + `--strict-mcp-config` + an empty
`{"mcpServers":{}}` config + scrubbed bot tokens). Protects the live bot slot per
`feedback_spawned_claude_must_isolate_telegram_plugin` — an un-isolated
`claude -p` would SIGTERM-steal the one bot slot and drop the owner's live
channel session. GREEN.

## §5 — Outcome-altitude: the v1.8.0 floor at outcome altitude (cold tree)

Both deltas reproduced from the cold tree with NO pre-arranged state, through
production entry points (AC.REL.S):

**Delta 1 — deploy-safety PreToolUse hook denies a fabricated prod destructive
command + stays fail-closed on a raising classifier (AC.DSF.7).** The
outcome-altitude test `framework/deploy-safety-floor/tests/test_AC_DSF_7_outcome
_altitude.py` runs within the **24 passed** deploy-safety-floor suite: the real
PreToolUse hook entry-point, fed raw stdin (a fabricated destructive command in
an `is_production` / no-attestation context) with no pre-arranged fixture,
returns a DENY whose message names the target + destructive sub-action in
non-technical vocabulary; and the same entry-point, fed input that makes its
classifier raise, still returns DENY (fail-closed). GREEN.

**Delta 2 — secure-build secret guard blocks a staged credential at the commit
boundary (AC.SBB.1 / AC.SBB.C OA).** The outcome-altitude test
`framework/secure-build-baseline/tests/test_AC_SBB_C_outcome_altitude.py` runs
within the **31 passed** secure-build-baseline suite: a commit/push whose staged
diff carries a credential pattern (the `AKIAIOSFODNN7EXAMPLE` placeholder) is
blocked at the boundary with no secret value echoed. GREEN.

**Delta 0 — `loam --version` → `loam 1.8.0`** from the cold install (§3). GREEN.

## §6 — Touched component suites (cold tree)

| Suite | Result |
|---|---|
| `framework/deploy-safety-floor/tests/` | **24 passed** (AC.DSF.1-4 / .6 / .7-OA + AC.COV.1; out-of-graph, via conftest) |
| `framework/secure-build-baseline/tests/` | **31 passed** (AC.SBB.1-4 + AC.SBB.C-OA + AC.COV.1; out-of-graph, via conftest) |
| `framework/safety-layer/tests/` | **206 passed** (AC.DSF.5 fail-CLOSED policy primitive + the existing `test_AC_SECHK_4_fail_open` / `test_AC_WDGUARD_5_fail_open` regression suites still green) |
| `framework/protection-matrix/tests/` | **42 passed** (AC.COV.1 catalogue rows; `loam guards` floor coverage) |
| `plugins/dev-sdlc/tests/` | **396 passed, 7 skipped** (incl. the retirement-sweep AC.PBRET.5 clean against the new v1.8.0 release content + the lockstep AC.PCVR at 1.8.0) |
| `plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py` | **5 passed** at the 1.8.0 lockstep state (31 in-scope pyprojects + meta `loam --version` coherently advanced) |

**Zero failures across every suite** — no NEW failure, and not even a
pre-existing-environmental one this cut (cleaner than the v1.7.0 smoke's single
`test_AC_MSC_3` cold-clone sensitivity). The retirement-sweep did NOT flag the
new v1.8.0 CHANGELOG / STATE / roadmap content (no retired-stem mention), so the
v1.7.0 finding-3 class did not recur.

## §7 — Gate evidence — system binary operational

```
loam --version  → loam 1.8.0
loam --help     → exit 0; subcommands:
   {pr-safety,guards,migrate,project,init-intake,onboard,workspace,
    odd-extract,audit,flow,release,amend,report,init,recover}
```

All documented subcommands present; `loam --version` reports `1.8.0`; exit 0.
The cold-install `.venv/bin/loam` is the authoritative version-reporting binary
for this staging smoke. GREEN.

## §8 — Lockstep version coherence (AC.REL.2)

`docs/ACTIVE_MINOR` = `1.8.0`; the 31 in-scope `pyproject.toml` `[project]`
version fields = `1.8.0` (grep sweep: ALL 31 == 1.8.0, none left at 1.7.0); the
meta `loam --version` literal (`loam_cli/__init__.py __version__`) = `1.8.0`.
The lockstep regression test `test_AC_PCVR_pyproject_version_lockstep.py` → 5
passed at the 1.8.0 state. The two NEW components `deploy-safety-floor` (0.1.0)
+ `secure-build-baseline` (0.1.0) are EXCLUDED from the in-scope set per D-LOCK
(new components out-of-graph); off-version siblings `frame-kernel` (1.5.0) +
`loam-init/meta` (1.1.0) are correctly untouched. GREEN.

## §9 — The nine `loam release --dry-run` gates

Captured via `loam release v1.8.0 --plan-doc docs/plans/release-integration-v1-8-0-deploy-safety-floor.md --dry-run`
from the canonical tree (on `main`). See §11 for the per-gate verdicts.

## §10 — Findings

**No blocker findings. No non-blocking findings either** — every suite passed
clean from the cold tree, the spawn-isolated `claude -p` returned SMOKE OK, the
two new components install-graph-excluded cleanly, and the secret scan's only
hits were the secure-build-baseline's own placeholder fixtures. This is the
cleanest release smoke in the v1.x line to date (no pre-existing-environmental
carry-over to classify).

## §11 — §status — the release gates (`loam release v1.8.0 --dry-run`)

`loam release v1.8.0 --plan-doc docs/plans/release-integration-v1-8-0-deploy-safety-floor.md --dry-run`
run from the canonical tree on `main` (post-bookkeeping-commit). Captured
verdicts:

| Gate | Verdict | Evidence |
|---|---|---|
| 1 hard-smoke | **GREEN** | GREEN aggregate-verdict token at this writeup path |
| 2 acs-verified | **GREEN** | all 8 AC.REL.* GREEN in plan §13 §status |
| 3 state-shipped | **GREEN** | v1.8.0 marked SHIPPED in `docs/STATE.md` |
| 4 clean-tree | **GREEN** | working tree clean (bookkeeping committed) |
| 5 branch-main | **GREEN** | on branch `main` (built directly on main, no worktree this cut) |
| 6 seal-reachable | **GREEN** | seal `3225eeee` reachable from HEAD |
| 7 migration-declared | **GREEN** | `v1-8-0-deploy-safety-floor.migration.yaml` declares `version: v1.8.0` + `operation: no-op` |
| 8 substrate-audit | **GREEN** | no shipping-status claim diverges from the derived STATE-OF-LOAM record |
| 9 boundary-respected | **GREEN** | no framework-code write lands user-state outside the two declared homes |

**9 GREEN / 0 RED.** Unlike v1.7.0 (1 expected-RED `branch-main` from worktree
staging), every gate is GREEN here because the prep ran directly on `main`.

## §12 — Verdict

**GREEN on all smoke dimensions** (cold-clone install exit 0 + `loam 1.8.0` +
spawn-isolated `claude -p` SMOKE OK exit 0 + deploy-safety PreToolUse deny OA
within 24 passed + secure-build secret-block OA within 31 passed + safety-layer
206 passed + protection-matrix 42 passed + dev-sdlc 396/7skip with
retirement-sweep clean + lockstep AC.PCVR 5 passed at 1.8.0 + system binary
operational at 1.8.0). Zero failures. The public tag + push + GitHub Release
proceed ONLY under the owner's explicit command (this smoke does NOT publish).
