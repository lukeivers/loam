# v1.6.0 HARD smoke writeup — capability-refresh + knowledge-pack + Claude-leverage defaults + principle-foundation structural enforcement

**Date:** 2026-06-18. **Release:** v1.6.0 — MINOR increment over published
v1.5.0 (`next_MINOR(v1.5.0) = v1.6.0`). Objective: loam continuously
refreshes its own capability knowledge, pushes a knowledge corpus to the
marketplace, prefers Claude-native primitives by default, and structurally
enforces its principle foundation.
**Reconcile:** the amendment stack (origin/main..HEAD) is a clean
FAST-FORWARD onto the published v1.5.0 baseline — no squash / no merge / no
amend. The window measured at smoke time is **149 commits**
(`git rev-list --count origin/main..HEAD = 149`; the dispatch brief's
"148-commit" figure was the pre-bump count — the final lockstep version-bump
commit `95b13fc4` makes it 149).
**Release HEAD at smoke:** `95b13fc4` — the lockstep version bump
(`1.5.0 -> 1.6.0`). Unlike the v1.5.0 smoke (bump-after-GREEN pattern), the
v1.6.0 lockstep bump is already the HEAD commit in the smoke window, so the
cold-install `loam --version` reports `1.6.0` directly.
**Last published (Tier-0, git ref):** `v1.5.0` annotated tag → commit
`31ac1d7071406228578bf19a213cff019b2435c3` (reachable from HEAD as ancestor).
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
component regression ride-alongs swept from the cold install. The v1.6.0
amendment window introduces two NEW components (capability-refresh,
knowledge-pack) plus principle-foundation structural enforcement across
dev-sdlc (Slices A/B + GUARD-SWEEP FLOOR + ProgramBench retirement-sweep
AC.PBRET.5 + lockstep AC.PCVR), primary-persona (Slice C Stop-hook
contributors), and workspace-bootstrap (Slice D slug-collision +
knowledge-pack marketplace wiring). The mechanical outcome check for this
window is the swept pytest suites of all touched components, run from the
cold install — the strongest automated outcome check available across a
multi-component structural-enforcement window.

## §2 — Cold clone

A fresh `git clone` of the canonical loam tree into
`.scratch/smokes/v1-6-0-smoke` + checkout `95b13fc4`. Clone HEAD verified
== `95b13fc412b8f657f74ce7327f002e1e2d336a90`. No shared venv or state.
(Cloned from the local canonical tree so the cold clone carries the
unpushed v1.6.0 commits — they are not yet on `origin`.)

## §3 — Editable install from the manifest

`python3.13 -m venv .venv` + `pip install -r install-from-source.txt` in
the cold clone. Install exit 0. **`loam --version` from the cold install →
`loam 1.6.0`** — the lockstep bump (advancing to 1.6.0) is the HEAD commit
in the smoke window (`95b13fc4`), so the cold clone reports the post-bump
version directly. This differs from the v1.5.0 smoke (where the bump landed
after smoke GREEN and the cold clone reported the pre-bump version). GREEN
(install works, binary resolves, version reflects the lockstep bump).

## §4 — Spawn-isolated `claude -p` (the bot-slot protection)

```
echo 'Reply with exactly the two words: SMOKE OK' | \
  env -u ANTHROPIC_API_KEY -u TELEGRAM_BOT_TOKEN CLAUDE_PERSONA=loam-smoke-v160 \
  claude -p --strict-mcp-config --mcp-config .scratch/smokes/empty-mcp-v141.json
→ SMOKE OK   (exit 0)
```

A genuine model response, subscription-mode, with the telegram plugin NOT
loaded (`CLAUDE_PERSONA` set + `--strict-mcp-config` + an empty
`{"mcpServers":{}}` config file). The local bash-guard
`claude_spawn_isolation_guard.py` is satisfied by the `--strict-mcp-config`
+ empty `--mcp-config` shape. GREEN.

## §5 — Outcome-altitude: lockstep version + new-component sweeps at production entry points (cold)

The headline v1.6.0 user-visible deltas are (a) the two new tools
(capability-refresh, knowledge-pack) becoming live components and (b) the
lockstep version advancing to 1.6.0 across all in-scope pyprojects. The
production-entry-point outcome check is the cold-install pytest sweep of the
new components plus the lockstep AC test (AC.PCVR), run from the cold
`.venv` against real files with no pre-arranged state:

```
cd .scratch/smokes/v1-6-0-smoke
.venv/bin/python -m pytest framework/tools/capability-refresh/tests/ -q
→ 24 passed
.venv/bin/python -m pytest framework/tools/knowledge-pack/tests/ -q
→ 22 passed
.venv/bin/python -m pytest plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py -q
→ 5 passed   (lockstep verified at the 1.6.0 state — the bump is in the window)
```

The lockstep test passing at 1.6.0 confirms every in-scope pyproject + the
meta `loam --version` are coherently advanced. GREEN.

## §6 — Touched component suites (cold install)

All run from `.scratch/smokes/v1-6-0-smoke` with the cold `.venv` unless
noted:

| Suite | Result |
|---|---|
| `framework/tools/capability-refresh/tests/` | **24 passed** (NEW component) |
| `framework/tools/knowledge-pack/tests/` | **22 passed** (NEW component) |
| `plugins/dev-sdlc/tests/` | **396 passed, 7 skipped** (principle-foundation Slices A/B + GUARD-SWEEP FLOOR + ProgramBench retirement-sweep AC.PBRET.5 + lockstep AC.PCVR all green) |
| `framework/primary-persona/tests/` | **1215 passed, 1 skipped, 1 failed** — the failure (`test_AC_MSC_3_canonical_claude_dev_md_carries_named_surface`: empty dev-mode session-start payload) is Tier-0-verified PRE-EXISTING-ENVIRONMENTAL: it fails IDENTICALLY at the published v1.5.0 tag tip `31ac1d7` in a separate fresh cold clone (Tier-0-verified: cloned v1.5.0 separately into `.scratch/smokes/v150-tip-check`, fresh `.venv`, confirmed identical failure), and PASSES in the canonical tree (Tier-0-verified: `1 passed` in `/Users/lukeivers/loam/.venv`) — a cold-clone environment-shape sensitivity in the emitter probe, NOT a v1.6.0 regression. SAME known failure set documented in the v1.5.0 smoke §6 |
| `framework/workspace-bootstrap/tests/` | **697 passed, 15 skipped** (Slice D slug-collision + knowledge-pack marketplace wiring) |
| `plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py` | **5 passed** at the 1.6.0 lockstep state (the bump is the HEAD commit in the window) |

No NEW failures in any suite. The single failure is exactly the one
documented in the v1.5.0 smoke §6, verified pre-existing-environmental at
the v1.5.0 published tip — it is the SAME known set, GREEN-compatible.

## §7 — Gate 7 — system binary operational

```
which loam
→ /opt/homebrew/bin/loam

loam --version
→ loam 1.6.0

loam --help
→ usage: loam [-h] [--version]
    {init,init-intake,onboard,workspace,amend,release,audit,report,
    odd-extract,migrate,pr-safety,project,guards} ...
  (all documented subcommands present; exit 0)
```

System binary resolves correctly, reports `1.6.0`, all documented
subcommands listed. GREEN.

## §8 — Findings

**No blocker findings.** Three non-blocking findings recorded:

1. **`test_AC_MSC_3` cold-clone environmental failure.** Pre-existing on
   the published v1.5.0 tip (§6, Tier-0-verified at tag tip `31ac1d7`);
   documented in v1.5.0 smoke §6 and v1.4.0 smoke before it; not a v1.6.0
   regression. Root-cause investigation still owed.
2. **`loam --version` reports `1.6.0` in the cold clone.** Expected for
   v1.6.0: the lockstep bump (1.5.0 → 1.6.0) is the HEAD commit `95b13fc4`
   in the smoke window, so the cold clone reports the post-bump version
   directly. This differs from the v1.5.0 / v1.4.0 bump-after-smoke pattern;
   it is not a defect — the lockstep AC.PCVR test passing at 1.6.0 confirms
   coherence.
3. **Commit-window count.** The dispatch brief described a "148-commit"
   reconcile; the measured window at smoke time is **149 commits**
   (`git rev-list --count origin/main..HEAD = 149`). The 148 figure was the
   pre-bump count; the final lockstep version-bump commit makes it 149. Not
   a defect — recorded for accuracy.

## §9 — Verdict

**GREEN on all smoke dimensions** (cold-clone install exit 0 + `loam 1.6.0`
+ spawn-isolated `claude -p` SMOKE OK exit 0 + capability-refresh 24 passed +
knowledge-pack 22 passed + dev-sdlc 396/7skip with Slices A/B + GUARD-SWEEP
FLOOR + AC.PBRET.5 + AC.PCVR green + primary-persona 1215/1skip/1fail
(pre-existing-environmental, Tier-0-verified at v1.5.0 tip `31ac1d7` and
passing in canonical) + workspace-bootstrap 697/15skip + lockstep test 5
passed at 1.6.0 + system binary operational at 1.6.0). No NEW failure
outside the v1.5.0-documented known set. The public tag + push proceed under
the owner authorization.
