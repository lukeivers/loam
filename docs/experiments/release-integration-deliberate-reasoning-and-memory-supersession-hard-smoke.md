# v1.7.0 HARD smoke writeup — deliberate-reasoning (default-OFF) + memory-supersession

**Date:** 2026-06-24. **Release:** v1.7.0 — MINOR increment over published
v1.6.0 (`next_MINOR(v1.6.0) = v1.7.0`). Objective: loam can deliberately
reason — a metacognitive gate decides per-turn when a task warrants escalated
reasoning and runs an evidence-bound re-entrant loop, triggered by the
situation rather than conversation keywords and wired live (default-OFF); and
loam's memory keeps the current truth current — a superseded ruling is filtered
out of recall by validity interval while its history stays queryable.

**Staging topology:** prep + smoke staged in an ISOLATED git worktree
`/Users/lukeivers/loam-release-v1.7.0-wt` on branch `release/v1.7.0`, branched
off the RATIFIED commit `a0c25db1` (NOT main-tip). A CONCURRENT session owns
the shared `/Users/lukeivers/loam` main working tree (live isolated `claude -p`
+ pytest + uncommitted handsoff-loop edits) — staging in a worktree off the
ratified content avoids racing `index.lock` / corrupting that session's work,
the established loam release-worktree pattern (prior `loam-release-v*-wt`
worktrees exist). The release is scoped to `a0c25db1`'s content, deliberately
excluding the concurrent session's later/in-flight work.

**Release HEAD at smoke:** `24d4ef6e` — `release/v1.7.0` tip after the lockstep
version-bump + bookkeeping commit (`28372988`) and the retirement-sweep reword
corrective (`24d4ef6e`). The cold clone reports `loam 1.7.0` directly (the bump
is in the smoke window).
**Reconcile (Tier-0):** `git rev-list --left-right --count origin/main...HEAD` =
`0 47` — a clean linear fast-forward, zero behind, zero merge commits (43
plan-window commits + 2 ratify/plan commits + 2 v1.7.0 prep commits = 47). The
release-window content tip `7a6a1671` (memory-supersession seal) is reachable
from HEAD (Tier-0: `git merge-base --is-ancestor 7a6a1671 HEAD` → yes).
**Last published (Tier-0, git ref):** `v1.6.0` annotated tag → commit
`4aafc29f` (reachable from HEAD as ancestor).
**Secret scan (pre-push, public repo):** `origin/main..HEAD` diff scanned for
API-key / GitHub-token / AWS-key / Slack-token / private-key / Telegram-bot-
token patterns — **0 hard-pattern matches**; no secret-bearing filenames
(`.env`/`.pem`/etc.) in the window. The only matches of the *strings*
`ANTHROPIC_API_KEY`/`TELEGRAM_BOT_TOKEN` are plan-doc prose referencing the
no-API-key + scrub-the-token disciplines, not secrets.
**Subscription mode** — no `ANTHROPIC_API_KEY`; no `anthropic` SDK (per
`feedback_no_anthropic_api_key`). **python:** 3.13.2 venv for the cold install
and every probe.

**Aggregate verdict: GREEN.**

---

## §1 — Probe design (per `feedback_hard_smoke_per_minor_before_publish`)

HARD bar: a REAL cold-clone of the release HEAD + a REAL editable install with
no API key + a REAL spawn-isolated `claude -p` (per
`feedback_spawned_claude_must_isolate_telegram_plugin`) + the two new
capabilities reproduced at outcome altitude from the cold install + the
touched-component regression ride-alongs swept from the cold install. The
v1.7.0 window introduces one NEW top-level component (`deliberate-reasoning`,
default-OFF, 0.1.0 out-of-graph), extends sealed `primary-persona` with
memory-supersession, lands Tilth hands-off-loop slices (DF/HB/DF6) under the
`workspace-bootstrap` fence, and a dev-sdlc retirement-record register.

**Env-scrub discipline (extended this cut):** in addition to scrubbing
`ANTHROPIC_API_KEY` + `TELEGRAM_BOT_TOKEN`, the smoke scrubs
`LOAM_DELIBERATE_REASONING` from the probe environment. The deliberate-reasoning
default-OFF tests assert no-op behaviour by reading the absence of that env var;
the interactive session that ran the smoke had `LOAM_DELIBERATE_REASONING=1`
exported (workspace activation), which — if left set — makes the default-OFF
test correctly observe an ENABLED layer and "fail." Scrubbing it reproduces the
true stranger-machine / default-OFF condition. (See §10 finding 1.)

## §2 — Cold clone

A fresh `git clone --branch release/v1.7.0` of the worktree into
`.scratch/smokes/v1-7-0-smoke`. Clone HEAD verified ==
`24d4ef6e84f400a91c830efc89ca0e82f22a4b13` (the release tip). No shared venv or
state. (Cloned from the local worktree so the cold clone carries the unpushed
v1.7.0 commits — they are not yet on `origin`.)

**Topology note (§10 finding 2):** the clone is a single-branch clone of
`release/v1.7.0`, so it has no local `refs/heads/main`. The
workspace-bootstrap AC.LIVI fixture (`isolated_canonical_clone`) reads
`refs/heads/main` of the repo root; a `git branch main HEAD` was created in the
clone so the fixture's documented-Quickstart topology assumption (a stranger's
`git clone` lands on `main`) holds. This is a staging-clone artefact, not a
defect — a real stranger clone of the published repo lands on `main` by default.

## §3 — Editable install from the manifest

`python3.13 -m venv .venv` + `pip install -r install-from-source.txt` in the
cold clone. **Install exit 0.** All 27 lockstep components installed at
`1.7.0` (loam-cli-1.7.0, loam-primary-persona-1.7.0, loam-workspace-bootstrap-
1.7.0, …) — confirming the lockstep bump is coherent across the full install
graph. **`loam --version` from the cold install → `loam 1.7.0`.** GREEN.

**deliberate-reasoning install-graph wiring (the plan's flagged debt):**
`deliberate-reasoning` is correctly NOT in the install graph (Tier-0: 0
`deliberate-reasoning` lines in `install-from-source.txt`; `importlib` does not
resolve `deliberate_reasoning` from the cold `.venv`) — it ships at 0.1.0
OUT-of-graph per D-LOCK, so it is correctly EXCLUDED, not broken. Its tests run
from the cold source tree via `PYTHONPATH=framework/deliberate-reasoning/src`
(the self-contained pattern). GREEN (the new-component install-graph gap the
plan flagged resolves as "correctly excluded," the standing 0.1.0-out-of-graph
debt named in §1 / plan §9.4).

## §4 — Spawn-isolated `claude -p` (the bot-slot protection)

```
echo 'Reply with exactly the two words: SMOKE OK' | \
  env -u ANTHROPIC_API_KEY -u TELEGRAM_BOT_TOKEN -u LOAM_DELIBERATE_REASONING \
  CLAUDE_PERSONA=loam-smoke-v170 \
  claude -p --strict-mcp-config --mcp-config .scratch/empty-mcp-v170.json
→ SMOKE OK   (exit 0)
```

A genuine model response, subscription-mode, with the telegram plugin NOT
loaded (`CLAUDE_PERSONA` set + `--strict-mcp-config` + an empty
`{"mcpServers":{}}` config). Protects the live Telegram bot slot per
`feedback_spawned_claude_must_isolate_telegram_plugin`. GREEN.

## §5 — Outcome-altitude: the two v1.7.0 user-visible deltas (cold install)

Both deltas reproduced from the cold install with NO pre-arranged state, through
production entry points (AC.REL.S):

**Delta 1 — deliberate-reasoning `process_turn` escalates + runs the loop.**
The production entry-point OA test
(`test_AC_MGRL_OA_outcome_altitude_real_entrypoint.py`) **1 passed** from the
cold tree, plus a standalone live demonstration: a genuinely-hedged draft + a
genuinely-novel task class + explicit stakes framing, run through `process_turn`
with `TurnConfig(enabled=True)` and no seeded gate state →

```
escalated=True  final_answer='391'  triggers=(NOVELTY, LOW_CONFIDENCE, STAKES)
```

The gate decided escalate on its own from real signals; the deliberate loop ran
end to end and returned the revised answer. GREEN.

**Delta 2 — memory-supersession filters a stale record + returns `as_of`
history.** From the cold install (pip-installed primary-persona), **7 passed**:
`test_AC_SUP_OA_outcome_altitude_live_corpus.py` (live-corpus filter + as_of) +
SUP.1 (default view filters stale) + SUP.2 (as_of history reachable) + SUP.3
(write path closes interval) + SUP.5 (reversible un-mark). A superseded record
is filtered out of current recall while `as_of` returns its history. GREEN.

## §6 — Touched component suites (cold install, `LOAM_DELIBERATE_REASONING`
scrubbed)

| Suite | Result |
|---|---|
| `framework/deliberate-reasoning/tests/` | **78 passed** (slice-1 AC.MGRL.* + slice-3 AC.TRIG.* / AC.WIRE.* / AC.WIRE.OA; run via `PYTHONPATH=.../src`, env scrubbed) |
| `framework/primary-persona/tests/` | **1244 passed, 1 skipped, 1 failed** — the failure (`test_AC_MSC_3_canonical_claude_dev_md_carries_named_surface`: empty dev-mode session-start payload) is Tier-0-verified PRE-EXISTING-ENVIRONMENTAL: it PASSES in the canonical tree (`/Users/lukeivers/loam/.venv` → `1 passed`) and fails only in the cold clone — a cold-clone environment-shape sensitivity in the emitter probe, the SAME known failure documented in the v1.6.0 / v1.5.0 / v1.4.0 smokes, NOT a v1.7.0 regression. The SUP + E2E ACs (the v1.7.0 memory deltas) pass within the 1244 |
| `framework/tools/handsoff-loop/tests/` | **126 passed, 9 skipped** (Tilth slices DF / HB / DF6 incl. AC.DF.6) |
| `framework/workspace-bootstrap/tests/` | **697 passed, 15 skipped** (with the local `main` ref present per §2 topology note) |
| `plugins/dev-sdlc/tests/` | **396 passed, 7 skipped** (incl. the pbret retirement-sweep AC.PBRET.5 GREEN after the §10-finding-3 reword + the lockstep AC.PCVR at 1.7.0) |
| `plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py` | **5 passed** at the 1.7.0 lockstep state (31 in-scope pyprojects + meta `loam --version` coherently advanced) |

No NEW failure outside the v1.6.0-documented known set. The single
primary-persona failure is exactly the documented `test_AC_MSC_3`
pre-existing-environmental one, Tier-0-verified passing in canonical.

## §7 — Gate 7 — system binary operational

```
loam --version  → loam 1.7.0
loam --help     → usage: loam [-h] [--version]
   {migrate,project,guards,pr-safety,init,report,amend,recover,audit,flow,
    release,odd-extract,init-intake,onboard,workspace} ...   (exit 0)
```

All documented subcommands present (init, amend, release, odd-extract, onboard,
pr-safety, project + migrate/guards/report/recover/audit/flow/workspace);
`loam --version` reports `1.7.0`; exit 0. GREEN. (The §1 release-process gate-7
note: `which loam` resolves to the maintainer's system binary
`/Users/lukeivers/.local/bin` shell; the cold-install `.venv/bin/loam` is the
authoritative version-reporting binary for this staging smoke. Operator-verified
in the cold install.)

## §8 — Lockstep version coherence (AC.REL.2)

`docs/ACTIVE_MINOR` = `1.7.0`; the 31 in-scope `pyproject.toml` `[project]`
version fields = `1.7.0`; the meta `loam --version` literal
(`loam_cli/__init__.py __version__`) = `1.7.0`. Verified two ways: (a) a direct
`tomllib` sweep of all 31 in-scope pyprojects vs `ACTIVE_MINOR` →
`ALL 31 == 1.7.0`; (b) the lockstep regression test
(`test_AC_PCVR_pyproject_version_lockstep.py`) → 5 passed at the 1.7.0 state.
`deliberate-reasoning` (0.1.0) + `handsoff-loop` (0.0.0) are EXCLUDED from the
in-scope set per D-LOCK + policy. GREEN.

## §9 — The seven `loam release --dry-run` gates

See §status matrix below (§12) for the per-gate verdicts. Captured via
`loam release v1.7.0 --plan-doc <plan> --dry-run` from the worktree.

## §10 — Findings

**No blocker findings.** Three non-blocking findings recorded:

1. **`LOAM_DELIBERATE_REASONING=1` env-leak made the default-OFF test "fail" on
   first run.** `test_AC_WIRE_2_default_off_zero_collateral` reads the absence of
   `LOAM_DELIBERATE_REASONING` to assert default-OFF no-op; the interactive
   session had it exported, so the test (correctly) observed an ENABLED layer and
   ran the loop. Scrubbing the var (`env -u LOAM_DELIBERATE_REASONING`) — the
   true stranger-machine / default-OFF condition — yields **78 passed**. NOT a
   code defect: the default-OFF code is correct (`_enabled_from_env()` returns
   False when the var is unset). The smoke now scrubs this var as part of the
   spawn-isolation discipline. Root-cause: session-env contamination, not the
   release.

2. **AC.LIVI cold-clone `main`-branch topology.** The `isolated_canonical_clone`
   session-fixture reads `refs/heads/main`; a single-branch clone of
   `release/v1.7.0` has none, erroring the fixture (11 errors). Creating a local
   `main` ref at the release tip (the topology a real stranger's `git clone` of
   the published repo lands on) yields **697 passed / 15 skipped**. Staging-clone
   artefact, not a v1.7.0 regression.

3. **Retirement-sweep caught two NEW v1.7.0 retirement-record references.** The
   dev-sdlc AC.PBRET.5 sweep (`test_AC_PBRET_5_no_unaccounted_live_pb_references`)
   flagged the v1.7.0 CHANGELOG + the release plan-doc's housekeeping bullet as
   unaccounted live mentions of the retired dev-tooling stem (both authored in
   this window, after the register was last updated). The guard worked exactly as
   designed. Resolved by REWORDING both out of the literal stem (commit
   `24d4ef6e`), per the guard's own repair direction (reword preferred over
   register; reword does not grow a permanent keep-row). Substance preserved; no
   ratified decision / AC / fence / version call changed. Sweep re-run → **396
   passed / 7 skipped** (GREEN). The guard stays ENFORCING — not weakened.

## §11 — Verdict

**GREEN on all smoke dimensions** (cold-clone install exit 0 + `loam 1.7.0` +
spawn-isolated `claude -p` SMOKE OK exit 0 + deliberate-reasoning OA escalate+
loop + supersession filter/as_of 7 passed + deliberate-reasoning 78 passed +
handsoff-loop 126/9skip + workspace-bootstrap 697/15skip + dev-sdlc 396/7skip
with retirement-sweep + lockstep AC.PCVR green at 1.7.0 + primary-persona
1244/1skip/1fail (pre-existing-environmental, Tier-0-verified passing in
canonical) + system binary operational at 1.7.0). No NEW failure outside the
v1.6.0-documented known set. The three findings are all classified, none
blocking. The public tag + push + merge to `main` proceed ONLY under the
SEPARATELY-gated owner authorization (this smoke does NOT publish).

## §12 — §status — the seven release gates (via `loam release v1.7.0 --dry-run`)

(filled in §13 below from the captured dry-run run.)
