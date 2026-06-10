# v1.5.0 HARD smoke writeup — frame-kernel patches + KEEL adoption Phase 1

**Date:** 2026-06-10. **Release:** v1.5.0 — MINOR increment over published
v1.4.0 (`next_MINOR(v1.4.0) = v1.5.0`). Owner-authorized publish: Luke,
Discord 1514378120, 2026-06-10 16:17 CDT.
**Reconcile:** the 35-commit amendment stack (origin/main..HEAD, four
sealed amendments) is a clean FAST-FORWARD onto the published v1.4.0
baseline — no squash / no merge / no amend.
**Release HEAD at smoke:** `82063cd7` (the HEAD at smoke time; the
lockstep version bump lands as a release commit after smoke GREEN, before
tag + push — this is the same pattern as v1.4.0).
**Last published (Tier-0, git ref):** `v1.4.0` annotated tag (`7dc1e38`) →
commit (reachable from HEAD as ancestor).
**Secret scan (pre-push, public repo):** `origin/main..HEAD` diff scanned
for API-key / GitHub-token / AWS-key / Slack-token / private-key /
Telegram-bot-token patterns — **0 matches**; no secret-bearing filenames
in the window.
**Subscription mode** — no `ANTHROPIC_API_KEY`; no `anthropic` SDK (per
`feedback_no_anthropic_api_key`). **python:** 3.13 venv for the cold
install and every probe.

**Aggregate verdict: GREEN.**

---

## §1 — Probe design (per `feedback_hard_smoke_per_minor_before_publish`)

HARD bar: a REAL cold-clone of the release HEAD + a REAL editable install
with no API key + a REAL spawn-isolated `claude -p` (per
`feedback_spawned_claude_must_isolate_telegram_plugin`) + the touched-
component regression ride-alongs swept from the cold install. The outcome-
altitude user-visible delta for v1.5.0 is the KEEL P1 doc-honesty sweep
(AC.KDOC.S) — verified as part of the cold-install suite run (it is a
grep-class automated sweep, the strongest mechanical outcome check available
for a docs-only amendment; no interactive BFI run needed for this release
window because the BFI path was the v1.4.0 outcome-altitude AC and the
frame-kernel patches are correctives to that same path, not new user-visible
outcome shape).

## §2 — Cold clone

A fresh `git clone` of the canonical loam tree into
`.scratch/smokes/v1-4-1-smoke` + checkout `82063cd7`. Clone HEAD verified
== `82063cd73c7a55133d6ecc9dd4648451cef35b74`. No shared venv or state.
(Cloned from the local canonical tree so the cold clone carries the
unpushed v1.5.0 commits — they are not yet on `origin`.)

## §3 — Editable install from the manifest

`python3.13 -m venv .venv` + `pip install -r install-from-source.txt` in
the cold clone. Install exit 0. **`loam --version` from the cold install →
`loam 1.4.0`** — the lockstep bump (advancing to 1.5.0) has not yet landed
as a release commit; this is the pre-bump cold-clone state, identical to
the v1.4.0 smoke pattern (the bump is the final bookkeeping commit, landing
after smoke GREEN). GREEN (install works, binary resolves, same behavior as
v1.4.0 cold install).

## §4 — Spawn-isolated `claude -p` (the bot-slot protection)

```
echo 'Reply with exactly the two words: SMOKE OK' | \
  env -u ANTHROPIC_API_KEY -u TELEGRAM_BOT_TOKEN CLAUDE_PERSONA=loam-smoke-v150 \
  claude -p --strict-mcp-config --mcp-config .scratch/smokes/empty-mcp-v141.json
→ SMOKE OK   (exit 0)
```

A genuine model response, subscription-mode, with the telegram plugin NOT
loaded (`CLAUDE_PERSONA` set + `--strict-mcp-config` + an empty
`{"mcpServers":{}}` config file). GREEN.

## §5 — Outcome-altitude: KEEL doc-honesty sweep at production entry points (cold)

The headline v1.5.0 doc-honesty delta is the KEEL P1 docs amendment. The
AC.KDOC.S outcome-altitude AC is a grep-class honesty sweep against the
live repo — run via the sealed dev-sdlc test suite (which is the production
entry point for doc-integrity checks, run from the cold install). This is
the strongest mechanical outcome check available for a docs-only amendment:
a scripted sweep against real files, no pre-arranged state, identical
command to the sealed AC tests.

From the cold-install suite run:

```
cd .scratch/smokes/v1-4-1-smoke
.venv/bin/python -m pytest plugins/dev-sdlc/tests/ -q
→ 336 passed, 7 skipped
```

The 336 dev-sdlc tests include `test_AC_KDOC_S_outcome_altitude_honesty_sweep` (the
production-path cold walk). All ACs (AC.CH0.1-2, AC.KDOC.1-5, AC.KDOC.S)
verified green. GREEN.

## §6 — Touched component suites (cold install)

All run from `.scratch/smokes/v1-4-1-smoke` with the cold `.venv`:

| Suite | Result |
|---|---|
| `framework/frame-kernel/tests/` | **92 passed** (up from 62 at v1.4.0 — 30 new tests for the three post-v1.4.0 corrective amendments: cwd-fallback, real-dispatch memory tier, stop-judge transcript objective) |
| `plugins/dev-sdlc/tests/` | **336 passed, 7 skipped** (KEEL P1 ACs: AC.CH0.1-2, AC.KDOC.1-5, AC.KDOC.S all green) |
| `framework/primary-persona/tests/` | **1190 passed, 1 skipped, 1 failed** — the failure (`test_AC_MSC_3_canonical_claude_dev_md_carries_named_surface`: empty dev-mode session-start payload) is Tier-0-verified PRE-EXISTING-ENVIRONMENTAL: it fails IDENTICALLY at the published v1.4.0 tag `f4fd93b0` in the same cold clone (Tier-0-verified: cloned v1.4.0 separately and confirmed identical failure), and PASSES in the canonical tree — a cold-clone environment-shape sensitivity in the emitter probe, NOT a v1.5.0 regression |
| `framework/workspace-sync/tests/` | **126 passed** |
| `framework/tools/loam/tests/` | **179 passed** |
| `plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py` | **5 passed** at the 1.4.0 lockstep state (pre-bump; lockstep test will re-pass at 1.5.0 after the bump commit) |

Note: `framework/workspace-bootstrap/tests/` (674+16skip) and
`framework/tools/handsoff-loop/tests/` (89+7skip) were swept in the
CANONICAL-TREE run (not the cold clone, due to cold-clone install time). Both
pass identically in the canonical venv — consistent with neither component
being in the v1.5.0 amendment window (workspace-bootstrap and handsoff-loop
are not touched by any of the four sealed amendments in this release).

## §7 — Gate 7 — system binary operational

```
which loam
→ /opt/homebrew/bin/loam

loam --version
→ loam 1.4.0

loam --help
→ usage: loam [-h] [--version]
    {init,init-intake,onboard,workspace,amend,release,audit,report,
    odd-extract,migrate,pr-safety,project,guards} ...
  (all documented subcommands present; exit 0)
```

System binary resolves correctly, all documented subcommands listed. GREEN.

## §8 — Findings

**No blocker findings.** Two non-blocking findings recorded:

1. **`test_AC_MSC_3` cold-clone environmental failure.** Pre-existing on
   the published v1.4.0 tip (§6); documented in v1.4.0 smoke §6; not a
   v1.5.0 regression. Root-cause investigation still owed.
2. **`loam --version` reports `1.4.0` in the cold clone.** Expected: the
   lockstep bump (1.4.0 → 1.5.0) lands as the final release bookkeeping
   commit AFTER smoke GREEN, consistent with the established pattern (same
   behavior observed in the v1.4.0 smoke writeup §3). Not a defect.

## §9 — Verdict

**GREEN on all smoke dimensions** (cold-clone install + spawn-isolated
`claude -p` SMOKE OK + frame-kernel 92 passed + dev-sdlc 336/7skip with
AC.KDOC.S outcome-altitude green + primary-persona 1190/1skip/1fail
(pre-existing-environmental, Tier-0-verified at v1.4.0 tip) + workspace-sync
126 + tools-loam 179 + lockstep test 5/pre-bump + system binary operational).
The public tag + push proceed under the owner authorization.
