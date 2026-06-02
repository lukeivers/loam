# v1.0.1 HARD smoke writeup — the two-minor-fixes PATCH

**Date:** 2026-06-02. **Release:** v1.0.1 — PATCH increment over the published
v1.0.0 (`bump_patch(v1.0.0)`). Owner-authorized: Luke, Telegram 13481.
**Tree:** `/Users/lukeivers/loam` (main). **HEAD at smoke:** `5c1021c9`
(protection-matrix silent-egress seal — the release-window tip).
**Last published (Tier-0, git ref):** `v1.0.0` (tag on `origin/main`).
**Window:** `v1.0.0..HEAD` = `origin/main..HEAD` = 5 commits, clean tree.
**`claude --version`:** `2.1.156 (Claude Code)`. **Subscription mode** — no
`ANTHROPIC_API_KEY`; no `anthropic` SDK (per `feedback_no_anthropic_api_key`).

**Aggregate verdict: GREEN.**

---

## §1 — Probe design (per `feedback_hard_smoke_per_minor_before_publish`)

**HARD bar:** a REAL cold-clone + a REAL editable install with no API key + a
REAL spawn-isolated `claude -p` (per
`feedback_spawned_claude_must_isolate_telegram_plugin` — `--strict-mcp-config`
+ empty `--mcp-config`, `ANTHROPIC_API_KEY` + `TELEGRAM_BOT_TOKEN` scrubbed) +
a real outcome-altitude exercise of the release's user-visible delta + the
touched-component test sweep.

v1.0.1's user-visible delta over v1.0.0 is the two sealed fixes: (1) the
FM.SILENT-EGRESS protection-matrix floor row, surfaced by `loam guards`
(exercised from the cold install at outcome-altitude below), and (2) the FBM
salience-gate fix that drops compaction-summary context-dumps from episode
retrieval (an internal `file_memory.py` behaviour, exercised by its component
suite + the new AC test, §4).

## §2 — F1 — Cold-clone + spawn-isolated `claude -p` subscription probe

**Probe invocation:**
```bash
rm -rf /tmp/v1-0-1-cold-clone
git clone -q /Users/lukeivers/loam /tmp/v1-0-1-cold-clone
cd /tmp/v1-0-1-cold-clone
env -u ANTHROPIC_API_KEY -u TELEGRAM_BOT_TOKEN bash -c \
  'echo "What is 2+2? Answer in one short sentence." | timeout 120 \
   claude -p --strict-mcp-config --mcp-config "{\"mcpServers\":{}}" \
   --output-format text'
```

**Verdict: GREEN.** Clone HEAD = `5c1021c9` (matches canonical HEAD). Output:
`2+2 equals 4.` Exit 0. Single short sentence. Spawn-isolated via
`--strict-mcp-config` + empty `--mcp-config` (no Telegram bot-slot steal — the
live MCP connection was not killed); env scrubbed of both `ANTHROPIC_API_KEY`
and `TELEGRAM_BOT_TOKEN` (subscription-only).

## §3 — F2 — Cold editable install + outcome-altitude `loam guards` exercise

The real cold install — the exact failure the HARD smoke exists to catch (a
fresh clone that doesn't actually install / doesn't produce working verbs).

**Probe:**
```bash
cd /tmp/v1-0-1-cold-clone
python3.13 -m venv .venv
.venv/bin/python -m pip install -q -r install-from-source.txt
.venv/bin/loam guards
```

**Verdict: GREEN.** Install exit 0 (full editable graph from
`install-from-source.txt`).

- **`loam guards` (the FM.SILENT-EGRESS fix's user-visible surface):** produced
  a real protection-pillar coverage report from the cold install with no
  pre-arranged state — **`rows: 19 (17 floor-class)`**. The new
  **`FM.SILENT-EGRESS`** floor row IS present in the live report, shown as
  `no guard / none` — exactly the floor GAP the v1.0.1 fix records (the row's
  purpose is to NAME the unguarded silent-data-egress failure mode, not to
  claim a guard). This is the v1.0.1 delta at outcome-altitude: v1.0.0 shipped
  18 rows (16 floor-class); v1.0.1 adds the silent-egress row → 19 (17
  floor-class). Exit 0.

## §4 — F3 — Touched-component test suites

Run per-component (separate `pytest` invocations to avoid the pre-existing
shared-`conftest.py` `ImportPathMismatchError` when components are collected
together — documented finding from the v1.0.0 smoke).

| Component | Result | Notes |
|---|---|---|
| `framework/protection-matrix/tests/` | **37 passed, 0 failed** | the FM.SILENT-EGRESS fix's component; includes `test_AC_PMROW_3_silent_egress_row.py` (4 passed) + the seal-fence test |
| `framework/primary-persona/tests/` | **895 passed, 1 skipped, 0 failed** | the FBM salience-gate fix's component; includes `test_AC_FBM_SAL_7_compaction_summary_dump_gated.py` (3 passed) + the seal-fence test |

**Verdict: GREEN.** No failures in either touched-component suite. The 1 skip
in primary-persona is pre-existing (environment-gated).

## §5 — F4 — Spawn-isolation + no-API-key invariants

- **Spawn-isolation:** the `claude -p` probe ran with `--strict-mcp-config` +
  empty `mcpServers` (F1). No un-isolated `claude -p` spawn in the window.
- **No-API-key:** `ANTHROPIC_API_KEY` unset throughout; the cold-clone probe
  explicitly scrubbed it (`env -u`). Subscription-only path proven.
- **Boundary:** the cold install wrote only into `/tmp/v1-0-1-cold-clone/.venv`
  (an admitted carve-out); no framework write to user-state outside a home
  (release gate 9 verifies this structurally — GREEN in the dry-run).

**Verdict: GREEN.**

## §6 — Surfaced findings (F2 ruthless feedback — NOT smoke blockers)

1. **`loam --version` reports `0.10.0` (PRE-EXISTING, unchanged from v1.0.0).**
   The meta-package's own version literal is `0.10.0`, decoupled from the
   per-component lockstep anchor (`docs/ACTIVE_MINOR` = `1.0.0`). This is the
   identical pre-existing state observed in the v1.0.0 HARD smoke; v1.0.1 is a
   PATCH and per policy §131 does not touch any version field, so it neither
   introduces nor fixes this. Recommend the meta-package version be folded into
   a future MINOR's lockstep set. Not v1.0.1-blocking.

2. **PATCH carries zero version-field churn (by design — confirming, not a
   defect).** Per `docs/release-versioning-policy.md` §131 (D-NFCLEAN.4 /
   D-SDPD) PATCHes ride the predecessor MINOR's per-component versions.
   `docs/ACTIVE_MINOR` stays `1.0.0`; no pyproject bumped; the lockstep
   regression test stays GREEN with no edit. This is the correct PATCH shape,
   recorded here so a future reader does not mistake the absence of a bump for
   an oversight.
