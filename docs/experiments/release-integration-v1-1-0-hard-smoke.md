# v1.1.0 HARD smoke writeup — the FBM-retrieval + never-leak MINOR

**Date:** 2026-06-03. **Release:** v1.1.0 — MINOR increment over published
v1.0.1 (`next_MINOR(v1.0.1)`). Owner-authorized: Luke, Telegram 13626.
**Worktree:** `/Users/lukeivers/loam-release-v1.1.0-wt` (isolated; branch
`release/v1.1.0`).
**Release HEAD at smoke:** `4c8e29e9` (install-manifest fix on top of the
`d71f450e` lockstep version bump, on top of fbm-80 tip `a3f2bfc6`).
**Last published (Tier-0, git ref):** `v1.0.1` annotated tag → commit
`deb85f6a` (tag object `5c1021c9`).
**Window:** `v1.0.1..release/v1.1.0` — the 55-commit linear stack + 2 release
commits (version bump + install-manifest fix).
**`claude --version`:** `2.1.156 (Claude Code)`. **Subscription mode** — no
`ANTHROPIC_API_KEY`; no `anthropic` SDK (per `feedback_no_anthropic_api_key`).
**python:** 3.13.12 (host default `python3` is 3.9 — below the >=3.11 floor;
the pre-existing 3.9 entry-point failures are NOT chased, per brief).

**Aggregate verdict: GREEN.** (One pre-existing, shipped-in-v1.0.1 test
failure surfaced as a non-blocker finding — §6.)

---

## §1 — Probe design (per `feedback_hard_smoke_per_minor_before_publish`)

HARD bar: a REAL cold-clone + a REAL editable install with no API key + a REAL
spawn-isolated `claude -p` (per `feedback_spawned_claude_must_isolate_telegram_plugin`
— `--strict-mcp-config` + empty `--mcp-config`, `ANTHROPIC_API_KEY` +
`TELEGRAM_BOT_TOKEN` scrubbed) + outcome-altitude exercise of the release's
user-visible deltas + the touched/new-component test sweep.

v1.1.0's user-visible deltas over v1.0.1:
1. **`loam --version` now reports `1.1.0`** (was `0.10.0` — the v1.0.1 §6
   finding #1, folded into this MINOR's lockstep).
2. **protection-matrix** grows to 20 rows / 18 floor-class (was 19/17):
   FM.SILENT-EGRESS now BOUND to a release-gate (was unbound in v1.0.1) +
   the new FM.DROPPED-OPEN-LOOPS floor row.
3. **egress-consent** (NEW component) — fail-closed never-leak privacy gate +
   `loam report` bug-report verb.
4. **usage-window-guard** (NEW component) — OAuth rolling-window usage probe.
5. **FBM retrieval** — write-time salience cold tier, load-time systematic
   filter + dedup, per-project STATE, P@5 metric + guard, #80 anchor-flood cap
   + omnibus length-norm.

## §2 — F1 — Cold-clone + spawn-isolated `claude -p` subscription probe

```bash
git clone -q --branch release/v1.1.0 /Users/lukeivers/loam /Users/lukeivers/loam-v1.1.0-smoke/loam
cd /Users/lukeivers/loam-v1.1.0-smoke/loam
env -u ANTHROPIC_API_KEY -u TELEGRAM_BOT_TOKEN bash -c \
  'echo "What is 2+2? Answer in one short sentence." | timeout 120 \
   claude -p --strict-mcp-config --mcp-config "{\"mcpServers\":{}}" \
   --output-format text'
```

**Verdict: GREEN.** Clone HEAD = `4c8e29e9`. Output: `4.` Exit 0. Spawn-isolated
via `--strict-mcp-config` + empty `mcpServers` (the live Telegram MCP connection
in the parent session was NOT killed — no bot-slot steal). Env scrubbed of both
`ANTHROPIC_API_KEY` and `TELEGRAM_BOT_TOKEN` (subscription-only path proven).

## §3 — F2 — Cold editable install + outcome-altitude verb exercises

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -q -r install-from-source.txt   # exit 0
.venv/bin/loam --version    # -> "loam 1.1.0"
.venv/bin/loam guards       # -> 20 rows (18 floor-class)
```

**Verdict: GREEN.** Install exit 0 (full editable graph from the v1.1.0
install-from-source manifest — see §6 finding for the manifest fix this smoke
caught).

- **`loam --version` → `loam 1.1.0`** (exit 0). The v1.0.1 §6 finding #1 is
  CLOSED: the meta-package `--version` literal now reports the published MINOR.
- **`loam guards` → `rows: 20 (18 floor-class)`** from the cold install, no
  pre-arranged state. v1.0.1 shipped 19 rows (17 floor-class). The two new rows
  are live: **FM.SILENT-EGRESS** (now bound `release-gate`, was unbound) +
  **FM.DROPPED-OPEN-LOOPS** (new floor row). Exit 0. This is the
  protection-matrix delta at outcome-altitude.

## §4 — F3 — Clean re-clone proving the fixed install manifest

A second clean clone (`loam-v1.1.0-smoke2`) installed ONLY from
`install-from-source.txt` (no manual `-e`); both new modules import:

```
.venv/bin/python -c "import loam.usage_window_guard, loam.egress_consent"  # OK
```

**Verdict: GREEN.** Proves a stranger-clone of v1.1.0 gets both headline new
components from the manifest alone.

## §5 — F4 — Touched + new-component test suites (cold install, python 3.13)

| Component | Result |
|---|---|
| `framework/egress-consent/tests/` | **45 passed, 0 failed** |
| `framework/usage-window-guard/tests/` | **23 passed, 0 failed** |
| `framework/protection-matrix/tests/` | **42 passed, 0 failed** |
| `framework/workspace-bootstrap/tests/` | **674 passed, 16 skipped, 0 failed** |
| `framework/primary-persona/tests/` | **944 passed, 1 skipped, 1 failed** (the 1 failure is §6 pre-existing) |
| `plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py` | **5 passed** (lockstep stays GREEN with the bump + new-component fold-in) |

**Verdict: GREEN** for all touched/new components. The single primary-persona
failure is pre-existing (§6), not a release regression.

## §6 — Surfaced findings (F2 ruthless feedback)

1. **[FIXED IN-SMOKE] The two NEW components were missing from
   `install-from-source.txt`.** A cold `pip install -r install-from-source.txt`
   did NOT install `egress-consent` or `usage-window-guard` (the manifest
   predates them) — component suites failed collection with
   `ModuleNotFoundError: No module named 'loam.usage_window_guard'`. This is the
   exact failure the HARD smoke exists to catch (a fresh clone that doesn't
   install the shipped components). FIX: commit `4c8e29e9` adds both as a
   Tier-M block. Re-clone (§4) proves the fix. Without this fix, v1.1.0 would
   have shipped two headline components that a stranger-clone cannot install.

2. **[PRE-EXISTING NON-BLOCKER] `test_AC_MSC_3_canonical_claude_dev_md_carries_named_surface`
   fails in the cold-clone harness.** The dev-mode session-start emitter returns
   an empty payload when run from a bare cold clone (no dev-workspace markers),
   so part (2) of the assertion fails (`payload head=''`). Part (1) passes —
   `CLAUDE.dev.md` DOES carry `docs/FUTURE_IDEAS_DRAFT.md` in its Session-start
   section. **Tier-0 proof this is pre-existing, not a release regression:** the
   test's source commit `91ebdee1` is an ancestor of the published `v1.0.1`
   tag (`git merge-base --is-ancestor 91ebdee1 v1.0.1^{commit}` → YES) — i.e.
   the test shipped in the LAST published release. It fails identically on the
   untouched release base `a3f2bfc6`. The v1.0.1 smoke ran in the canonical tree
   (emitter found its workspace context); this smoke runs in cold-clone
   isolation, where the emitter is environment-gated. NOT a v1.1.0 blocker;
   surfaced for an owner call on whether to make the emitter test
   harness-robust in a follow-up PATCH.

3. **[CONFIRMING] Lockstep version-bump shape.** 32 in-lockstep pyprojects +
   `docs/ACTIVE_MINOR` 1.0.0→1.1.0; the two NEW components folded into the
   `IN_SCOPE_PYPROJECTS` allowlist (mirrors the v1.0.0 fold-in precedent); the
   four 0.0.0 measurement harnesses + two 0.1.0 outliers stay off-lockstep by
   policy. AC.PCVR.{3,4} GREEN.
</content>
</invoke>
