# v1.3.0 HARD smoke writeup — the WD-discipline framework-source guard MINOR

**Date:** 2026-06-05. **Release:** v1.3.0 — MINOR increment over published
v1.2.0 (`next_MINOR(v1.2.0) = v1.3.0`). Owner-authorized publish: Luke,
Telegram 13904.
**Reconcile:** the 9-commit WD-guard cycle (`32f36291..fa422412`) is a clean
FAST-FORWARD onto the published v1.2.0 baseline — no squash / no merge / no
amend.
**Release HEAD at smoke:** `fa422412` (the §14-backfill + dev-sdlc preload +
CLAUDE.md doctrine tip on top of the WD-guard seal `7ebbe45a`).
**Last published (Tier-0, git ref):** `v1.2.0` annotated tag (`e08430f3`) →
commit `fde2b170`; `origin/main` at `32f36291`.
**Window:** `origin/main..HEAD` = the 9 commits ahead — the WD-guard build
cycle (plan, feat, baseline-pin, schema-bump, apply, seal, §14-backfill) + the
dev-sdlc `skills: preload` frontmatter feat + the CLAUDE.md operating-discipline
doctrine doc.
**`claude --version`:** `2.1.156 (Claude Code)`. **Subscription mode** — no
`ANTHROPIC_API_KEY`; no `anthropic` SDK (per `feedback_no_anthropic_api_key`).
**python:** 3.13.12 (the cold install + every probe runs the 3.13 venv).

**Aggregate verdict: GREEN.**

---

## §1 — Probe design (per `feedback_hard_smoke_per_minor_before_publish`)

HARD bar: a REAL cold-clone of the release HEAD + a REAL editable install
with no API key + a REAL spawn-isolated `claude -p` (per
`feedback_spawned_claude_must_isolate_telegram_plugin` — `CLAUDE_PERSONA` set +
`--strict-mcp-config` + an empty `--mcp-config` file, `ANTHROPIC_API_KEY` +
`TELEGRAM_BOT_TOKEN` scrubbed) + an outcome-altitude exercise of the release's
user-visible delta (the WD-guard production hook, proven via the sealed
`test_AC_WDGUARD_S` subprocess test from the cold install) + the touched
component test sweep.

## §2 — Cold clone

A fresh `git clone` of the canonical loam tree into `/tmp/loam-v130-smoke` +
`checkout fa422412`. Clone HEAD verified == `fa422412` (the release HEAD). No
shared venv/state. (Cloned from the local canonical tree so the cold clone
carries the 9 unpushed WD-guard commits — they are not yet on `origin`.)

## §3 — Editable install from the manifest

`python3.13 -m venv .venv` + `pip install -r install-from-source.txt` in the
cold clone. Install exit 0. No NEW top-level component ships in v1.3.0 (the
WD-guard is a hook added inside the already-listed `framework/safety-layer/`
component), so the manifest needs no v1.3.0 change.

## §4 — Spawn-isolated `claude -p` (the bot-slot protection)

```
echo 'Reply with exactly the two words: SMOKE OK' | \
  env -u ANTHROPIC_API_KEY -u TELEGRAM_BOT_TOKEN CLAUDE_PERSONA=loam-smoke-v130 \
  claude -p --strict-mcp-config --mcp-config /tmp/empty-mcp-v130.json
→ SMOKE OK   (exit 0)
```

A genuine model response, subscription-mode, with the telegram plugin NOT
loaded (`CLAUDE_PERSONA` set + `--strict-mcp-config` + an empty MCP config
file) — the parent Telegram bot slot is protected (per
`feedback_spawned_claude_must_isolate_telegram_plugin`; the live
`~/.claude/hooks/claude_spawn_isolation_guard.py` PreToolUse guard was present
+ wired as the structural backstop). GREEN.

## §5 — Outcome-altitude: the WD-guard at the production entry point (cold)

The v1.3.0 user-visible delta is the WD-guard hook. The authoritative
outcome-altitude exercise is the sealed `test_AC_WDGUARD_S_outcome_altitude`
test, which — with NO pre-arranged state, NO mocks at the git boundary —
builds two throwaway temp git repos (one with a canonical-matching
`github.com/.../loam` origin, one with a non-canonical origin), runs the
PRODUCTION `wd_discipline_guard.py` script as a `python <script>` subprocess
for each of the four sub-cases, and asserts the production deny/allow shape on
stdout:

- (a) DERIVED × framework-source → `permissionDecision: deny` (+ canonical
  redirect reason).
- (b) CANONICAL × framework-source → ALLOW (no deny).
- (c) DERIVED × workspace-state → ALLOW.
- (d) DERIVED × framework-source WITH the override env → ALLOW.

Run from the cold install: **`test_AC_WDGUARD_S_outcome_altitude` → 1 passed**
(177 deselected). GREEN — the guard's deny/allow contract proven at outcome
altitude through the production entry point from the cold clone.

## §6 — Touched component suite (cold install)

| Suite | Result |
|---|---|
| `framework/safety-layer/tests/` | **178 passed** (incl. the 28 new WDGUARD tests + `test_AC_WDGUARD_S_outcome_altitude` + the pre-existing SECHK + A15/A17/A18 seal-invariant tests) |

The six WDGUARD AC families (AC.WDGUARD.1, .2, .3, .4, .5, .S) are within the
pass set; `test_AC_WDGUARD_S` is the outcome-altitude production-subprocess
proof.

## §7 — Findings

**No blocker findings in the smoke itself.** One release-process anomaly
surfaced OUTSIDE the smoke (recorded here for completeness, owner-gated before
the public tag-push):

- **The MINOR lockstep version bump was NOT performed by the build cycle.**
  `docs/ACTIVE_MINOR` + all in-scope `pyproject.toml` versions + the
  meta-package `--version` literal remain at `1.2.0`. So `loam --version` from
  the cold install reports **`loam 1.2.0`**, NOT 1.3.0. Every prior MINOR
  (v1.1.0, v1.2.0) bumped the lockstep as pre-publish bookkeeping; the `loam
  release` tool does NOT perform the bump (it tags at the seal commit + pushes
  + creates the GitHub Release). The `pyproject-version-lockstep` regression
  test (`plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py`)
  passes 5/5 at the consistent-1.2.0 state — but it pins pyprojects to
  `docs/ACTIVE_MINOR`, so bumping ACTIVE_MINOR to 1.3.0 without bumping the
  pyprojects would turn it RED (a coupled ~31-file bump). This is NOT a smoke
  failure — the WD-guard, the touched suite, and the isolation are all GREEN —
  but publishing a v1.3.0 tag at `7ebbe45a` whose code self-reports 1.2.0 is a
  release-metadata inconsistency. HELD for the owner's ruling on whether to
  bump the lockstep (the +31-file MINOR-discipline bump, scope beyond the 5
  paperwork gates) before the public tag-push.

## §8 — Verdict

**GREEN on the smoke dimensions** (cold-clone install + spawn-isolated
`claude -p` + outcome-altitude WD-guard production proof + 178/178 touched
suite). The lockstep-version-bump anomaly (§7) is a release-process gate the
build cycle skipped alongside the 5 paperwork gates, surfaced to the owner; it
does not change the smoke verdict but gates the irreversible public tag-push.
