# v1.4.0 HARD smoke writeup — the memory + build-from-intent MINOR

**Date:** 2026-06-10. **Release:** v1.4.0 — MINOR increment over published
v1.3.0 (`next_MINOR(v1.3.0) = v1.4.0`). Owner-authorized publish: Luke,
Discord 1514274994857709700.
**Reconcile:** the 61-commit amendment stack (`b16b49f2..a3f58a21`, six
sealed amendments) is a clean FAST-FORWARD onto the published v1.3.0
baseline (`git merge-base origin/main main` == `origin/main` at `22df8683`)
— no squash / no merge / no amend.
**Release HEAD at smoke:** `f3501210` (the lockstep-bump tip; the D.1
hash-pin rebaseline `2c38e77f` was pulled into the same cold clone and the
affected suite re-swept — see §6).
**Last published (Tier-0, git ref):** `v1.3.0` annotated tag (`10ef8f2a`) →
commit `7ebbe45a`; `origin/main` at `22df8683`.
**Secret scan (pre-push, public repo):** the full `origin/main..main` diff
(23,103 lines) scanned for API-key / GitHub-token / AWS-key / Slack-token /
private-key / Telegram-bot-token patterns — **0 matches**; no secret-bearing
filenames in the window.
**Subscription mode** — no `ANTHROPIC_API_KEY`; no `anthropic` SDK (per
`feedback_no_anthropic_api_key`). **python:** 3.13 venv for the cold install
and every probe.

**Aggregate verdict: GREEN.**

---

## §1 — Probe design (per `feedback_hard_smoke_per_minor_before_publish`)

HARD bar: a REAL cold-clone of the release HEAD + a REAL editable install
with no API key + a REAL spawn-isolated `claude -p` (per
`feedback_spawned_claude_must_isolate_telegram_plugin`) + an
outcome-altitude exercise of the release's user-visible delta (the general
build-from-intent path run end-to-end on the documented App-1 command from
the cold clone) + the touched-component regression ride-alongs swept from
the cold install.

## §2 — Cold clone

A fresh `git clone` of the canonical loam tree into `/tmp/loam-v140-smoke` +
`checkout f3501210`. Clone HEAD verified == `f3501210`. No shared venv or
state. (Cloned from the local canonical tree so the cold clone carries the
unpushed v1.4.0 commits — they are not yet on `origin`.)

## §3 — Editable install from the manifest

`python3.13 -m venv .venv` + `pip install -r install-from-source.txt` in the
cold clone. Install exit 0. **`loam --version` from the cold install →
`loam 1.4.0`** — the lockstep bump (32 in-scope pyprojects +
`docs/ACTIVE_MINOR` + the meta-package literal, commit `f3501210`) is live
at the production entry point; the v1.3.0 release-metadata anomaly (§7 of
the v1.3.0 writeup — code self-reporting the prior version at smoke time)
does not recur. No NEW top-level component ships in v1.4.0, so the manifest
needs no change. GREEN.

## §4 — Spawn-isolated `claude -p` (the bot-slot protection)

```
echo 'Reply with exactly the two words: SMOKE OK' | \
  env -u ANTHROPIC_API_KEY -u TELEGRAM_BOT_TOKEN CLAUDE_PERSONA=loam-smoke-v140 \
  claude -p --strict-mcp-config --mcp-config /tmp/empty-mcp-v140.json
→ SMOKE OK   (exit 0)
```

A genuine model response, subscription-mode, with the telegram plugin NOT
loaded (`CLAUDE_PERSONA` set + `--strict-mcp-config` + an empty
`{"mcpServers":{}}` config file). GREEN.

## §5 — Outcome-altitude: general build-from-intent at the production entry point (cold)

The headline v1.4.0 user-visible delta is the general build-from-intent
path. The probe runs the RUN_LOG's documented App-1 reconciliation command
(the harness's "reproduce this run" contract — the IDENTICAL underlying
command, no per-archetype branching) from the cold clone with NO
pre-arranged state, a fresh workspace each run. Per the honest-log
contract, EVERY run is reported, fails included:

- **Run 1** (workspace `/tmp/bfi-smoke-v140-app1`, run dir
  `runs/20260610-094622`, wall 818.9s): terminal **`generation-failed`** —
  "sub-task 'csv-io-and-cli' brief leaks the gate — refusing". This is the
  loop's DESIGNED gate-holdout protection firing on stochastic LLM content
  (the generated sub-task brief leaked acceptance-gate text; the loop
  refused to build on a broken plan rather than corrupt the independent
  check). An honest refusal at a designed guard, not a crash and not a code
  regression: the identical command at effectively identical code went
  `done` 4/4 in the committed RUN_LOG over the preceding 24h (entries at
  `cc394548`/`06e7aa4e`/`00f7e044`/`e87b1a4f` + the off-vertical entry at
  `a3f58a21`), and the v1.4.0 delta since those runs touches no
  handsoff-loop source (the lockstep bump excludes the tool's deliberate
  `0.0.0` pyproject). Per the empirical-recheck discipline the leg was
  re-run once.
- **Run 2** (workspace `/tmp/bfi-smoke-v140-app1-run2`, run dir
  `runs/20260610-100155`, wall 712.6s): terminal **`done`**. Intent
  extracted + confirmed (2 meaningful questions, both genuinely
  build-shaping); grounding `grounded=True` (live-verified citations, 0
  dropped); generative middle produced objective + tool + acceptance gate
  in-run; convergence `reached_done=True`, `stop_reason=done`, first pass
  (`refine_attempts=0`), gated on the independent verify (primary exit 0 +
  held-out exit 0); final check "PASS: all gate criteria satisfied";
  progress audit: 18 user-visible updates, max gap 120.0s on the monotonic
  clock, within the heartbeat bound, **0 unverifiable claims**; 3
  expert-gate flags honestly surfaced (fuzzy threshold, batch payments,
  rounding tolerance — practitioner decisions, exactly the designed human
  gate).

The documented command reproduces end-to-end from the cold clone at the
production CLI entry point. GREEN (run 1 honest designed-guard refusal +
run 2 `done`; both reported per the fails-included contract).

## §6 — Touched component suites (cold install)

| Suite | Result |
|---|---|
| `framework/frame-kernel/tests/` | **62 passed** |
| `framework/workspace-sync/tests/` | **126 passed** |
| `framework/primary-persona/tests/` | **1190 passed, 1 skipped, 1 failed** — the failure (`test_AC_MSC_3_canonical_claude_dev_md_carries_named_surface`: empty dev-mode session-start payload) is Tier-0-verified PRE-EXISTING-ENVIRONMENTAL: it fails IDENTICALLY at the published v1.3.0 tip `22df8683` in the same cold clone, and PASSES in the canonical tree — a cold-clone environment-shape sensitivity in the emitter probe, NOT a v1.4.0 regression |
| `framework/hands-off-lifecycle/tests/` | **772 passed, 7 skipped** (after the D.1 hash-pin retire-and-rebaseline `2c38e77f` pulled into the clone; the 2 pre-rebaseline failures were the KNOWN lockstep-bump↔byte-pin coupling — SIXTH consecutive recurrence, root-cause fix still owed, F2-surfaced) |
| `framework/tools/loam/tests/` | **179 passed** |
| `framework/workspace-bootstrap/tests/` | **674 passed, 16 skipped** |
| `framework/tools/handsoff-loop/tests/` (non-live) | **89 passed, 7 skipped** (the live OA proof is the §5 end-to-end run itself) |
| `plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py` (canonical) | **5 passed** at the 1.4.0 lockstep state |

## §7 — Findings

**No blocker findings.** Two non-blocking findings recorded:

1. **D.1 byte-pin recurrence (SIXTH).** The lockstep bump mechanically
   invalidated the two pinned pyproject SHAs again; closed in-band by the
   established retire-and-rebaseline (`2c38e77f`). The owed root-cause fix
   (exclude pyproject.toml from the byte-content sample — pyprojects MUST
   mutate every MINOR by design) remains scheduled; re-surfaced as a hard
   F2 finding in the v1.4.0 release report.
2. **`test_AC_MSC_3` cold-clone environmental failure.** Pre-existing on
   the published tip (§6); worth a follow-up so the emitter probe is
   environment-independent, but not a release gate.

## §8 — Verdict

**GREEN on all smoke dimensions** (cold-clone install + `loam --version` →
1.4.0 + spawn-isolated `claude -p` + the build-from-intent App-1 documented
command reproduced end-to-end at outcome altitude + 7 suites swept from the
cold install with every failure Tier-0-attributed). The public tag + push +
GitHub Release proceed under the owner authorization.
