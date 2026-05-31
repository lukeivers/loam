# v0.14.0 HARD smoke writeup — keep-pace MVP + FBM Cycle-1 + first-run message accuracy MINOR

**Date:** 2026-05-29. **Build cycle:** v0.14.0 MINOR — keep-pace-with-user MVP (#149-152) + FBM Cycle-1 fix-write-path/unify (#154) + first-run-message retired-deps accuracy sweep (#155).
**Worktree:** `/Users/lukeivers/loam-release-v0-14-0` branch `release/v0-14-0`.
**Worktree HEAD at smoke:** `b291bdb` (post-#155-seal + §14 SHA-record follow-up).
**Last published (Tier-0, git ref):** `v0.13.0`. **Window:** `v0.13.0..HEAD`.
**`claude --version`:** `2.1.156 (Claude Code)`. **Subscription mode** — no `ANTHROPIC_API_KEY` set; no `anthropic` SDK (per `feedback_no_anthropic_api_key`).

---

## §1 — Probe design (per `feedback_hard_smoke_per_minor_before_publish`)

**HARD bar:** cold-clone install with no API key + real **spawn-isolated** `claude -p` (per `feedback_spawned_claude_must_isolate_telegram_plugin` — `--strict-mcp-config` + empty `--mcp-config`) + a real fixture exercising the MINOR's user-visible delta at outcome-altitude + F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN regression ride-alongs.

The v0.14.0 user-visible/runtime delta over v0.13.0 (window `v0.13.0..HEAD`):
1. **#155 first-run message accuracy** — the fresh-start first-run message no longer claims the install pulls graphiti-core/neo4j/kuzu (retired at v0.1.0); it now names file-based memory. This is the one *user-visible string* delta. Exercised by F2 below.
2. **keep-pace MVP (#149-152)** — UserPromptSubmit/PreToolUse hook chain wiring (fail-open, per-turn latency budget), work-anchored retrieval, abstraction-voice + constraint draft gate, SessionStart objective surface. Contributors wired in-tree; `settings.fragment.json` STAGED (live `~/.claude/settings.json` activation is the owner-gated step, not part of this publish). Exercised by F3 + F-LEAK.
3. **FBM Cycle-1 (#154)** — primary-persona write-path fix + unified retrieval surface. Exercised by F3 (primary-persona 793 passed).
4. **#155 in-fence D.1 re-baseline** — cli.py frozen-hash re-baseline driven by #154's legitimate edit (surfaced stale-RED at the #155 seal sweep). Exercised by the D.1 byte-content test inside F3 hands-off-lifecycle.

---

## §2 — F1 — Cold-clone + spawn-isolated `claude -p` subscription probe

**Probe invocation:**
```bash
cd /tmp && rm -rf v0-14-0-cold-clone
git clone -q --branch release/v0-14-0 /Users/lukeivers/loam-release-v0-14-0 v0-14-0-cold-clone
cd /tmp/v0-14-0-cold-clone
echo "What is 2+2? Answer in one short sentence." \
  | timeout 90 claude -p --strict-mcp-config --mcp-config '{"mcpServers":{}}' --output-format text
```

**Expected:** cold tree clones at `b291bdb`; spawn-isolated `claude` subscription works (no Telegram-plugin steal — empty MCP servers); meaningful response within 90s.

**Verdict:** **GREEN.** Clone HEAD = `b291bdb`. Output: `4.` Exit 0. Single short sentence. Spawn-isolated via `--strict-mcp-config` + empty `--mcp-config` (no Telegram bot-slot steal — the live MCP connection was not killed).

---

## §3 — F2 — #155 first-run message accuracy (outcome-altitude, cold tree)

The MINOR's only user-visible *string* delta. Probe invokes the production message-builder `_msg_fresh_start(log, helper_version)` from the **cold-clone tree** with no pre-arranged state (the path a fresh user hits on first run).

**Probe:** load `framework/hands-off-lifecycle/hooks/first_run_dispatch.py` as a module from the cold clone, call `_msg_fresh_start(log=<nonexistent>, helper_version='v0.14.0-smoke')`, assert (a) no `graphiti`/`neo4j`/`kuzu` (case-insensitive) and (b) names file-based memory.

**Actual fresh-user message returned:**
> Your pos-v2 workspace is installing.
>
> This takes about 5 minutes on a fresh clone (component dependencies are being installed into a shared virtualenv; memory is file-based — no external memory store or heavy memory database is pulled).
>
> Live progress: <log-path>
>
> Close this claude session, wait a few minutes, then reopen. First-run will finish in the background and the next launch will be instant. ...

**Verdict:** **GREEN.** Retired-dep names present: NONE. Names file-based memory: True. AC.FRMSG.1 + AC.FRMSG.2 + AC.FRMSG.S all satisfied at outcome-altitude from a cold clone.

**F2 surfaced finding (Lens 7, NOT a smoke blocker):** the message still opens with "Your **pos-v2** workspace". The `pos-v2` product-name residue is explicitly OUT of #155's scope (plan §7 — task-#19 proper, a separate rename cycle) and is NOT the user-visible *false-dependency* blocker this MINOR closed. Surfaced, not halted.

---

## §4 — F3 — Touched-component test suites (sealed worktree state)

Touched components in the `v0.13.0..HEAD` window: hands-off-lifecycle (keep-pace wiring + #155 + D.1 re-baseline), primary-persona (FBM Cycle-1 + keep-pace KP1/KP5), orchestrator (keep-pace KP7).

| Component | Result | Notes |
|---|---|---|
| `framework/hands-off-lifecycle/tests/` | **717 passed, 7 skipped, 0 failed** | Includes the now-GREEN D.1 byte-content test (16/16) + AC.FRMSG (5/5) + the cross-cutting seal-test |
| `framework/primary-persona/tests/` | **793 passed, 1 skipped, 0 failed** | FBM Cycle-1 write-path + unified retrieval surface |
| `framework/orchestrator/tests/` | **115 passed, 0 failed** | keep-pace KP7 SessionStart objective surface |

**Aggregate:** **1625 passed, 8 skipped, 0 failed** across the 3 touched components.

**Conftest-collision note (pre-existing topology, not a regression):** components are tested in separate `pytest` invocations to avoid the shared-`conftest.py` `ImportPathMismatchError`.

---

## §5 — F4 — Regression ride-alongs

### F-LEAK — MCP-config / settings.json surface leakage
**Window scope:** only KP0 (#149, `407b54d`) touched a settings-named path. Its own commit message confirms `settings.fragment.json is STAGED, not a live ~/.claude/settings.json edit`. Added-line scan for any `~/.claude` / `expanduser` / `/Users/.../.claude/settings` **write** path: none (the matches are a docstring naming the owner-gated activation, empty `claude_homes=()` test fixtures, and the abstraction-voice path-detector regex — not writes).
**Verdict:** **GREEN.** No new path to write MCP/settings config beyond the workspace boundary; live activation stays owner-gated.

### F-TIMEOUT — claude-print client / subprocess timeout
**Window scope:** `git log v0.13.0..HEAD -- framework/memory-system/** framework/**/claude_print_client.py` is empty — the synthesis client + its timeout config are untouched.
**Verdict:** **GREEN by construction.**

### F-VERIFY-ORPHAN — un-isolated claude-binary spawn paths
**Window scope:** added-line scan for a new `claude` binary subprocess invocation: the only matches are docstring/comment references (KP10 post-MVP future judge; a topic-token keyword list). KP0's new `subprocess.run` paths drive the latency-budget CLI hook + security-hook tests — they do NOT spawn the `claude` binary. No new un-isolated `claude -p` orphan-risk path introduced.
**Verdict:** **GREEN.**

---

## §6 — Aggregate verdict

**GREEN.** All probes pass:
- §2 cold-clone + spawn-isolated `claude -p` subscription: GREEN (`4.`, exit 0, isolated).
- §3 #155 first-run message accuracy outcome-altitude (cold tree): GREEN.
- §4 touched-component suites: 1625 passed, 8 skipped, 0 failed.
- §5 F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN: GREEN (1 by construction, 2 by structural verification).

**The HARD-smoke gate is CLEAR for the v0.14.0 publish.** Surfaced (non-blocking): the `pos-v2` product-name residue in first-run messages — out of #155's fence, scheduled to task-#19.

---

## §7 — Provenance trail (load-bearing Tier-0 sources)

- Worktree HEAD: `b291bdb`. #155 seal commit: `e0ff5bd`. D.1 re-baseline corrective: `2a019c3`. §14 SHA-record follow-up: `b291bdb`.
- BASELINE (hands-off-lifecycle sidecar post-seal): `2a019c3515cc55edf7b0339729c12454a919b08f`.
- Last published tag (Tier-0): `v0.13.0`. `docs/ACTIVE_MINOR` currently `0.13.0` (bumped to `0.14.0` at release-prep).
- `claude --version`: `2.1.156 (Claude Code)`.
- Cold-clone: `release/v0-14-0` → `/tmp/v0-14-0-cold-clone` (transient; deleted post-smoke).
- Touched-component test counts from this turn's `pytest` invocations against the worktree.
