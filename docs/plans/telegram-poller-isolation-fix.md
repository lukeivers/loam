# Telegram-poller-isolation fix — wire the three handsoff-loop launch sites

**Class:** ODD-shaped build plan + §14 SHA register.
**Binding contract:** `pos3/workspace/.scratch/claude-output/telegram-isolation-fix-plan-2026-05-16.md`
(authored 2026-05-16, owner-greenlit, dispatcher-verified sound). This
in-repo doc is the ODD-faithful build-spine of that contract; the
contract is authoritative for objective/fence/ACs and is not re-derived
here.

**Reuses the proven mechanism (do NOT re-implement):**
`framework/tools/subloam-driver/src/subloam_driver/driver.py` —
`build_isolated_claude_argv` / `build_isolated_env` /
`write_empty_mcp_config` / `IsolationConfig`. Sealed under AC.LIPW.5/.6;
empirically verified necessary-and-sufficient operator-protection (the
telegram-plugin/empty-MCP/env-scrub exclusion). This build composes ON
that result and adds NO new isolation machinery.

**Prime objective it ladders to:** `framework/docs/VALUE_PROPOSITION.md`
(the harness must not break the operator's only user-visible channel
while doing background work — a harness that kills the channel fails the
harness test).

---

## §1 — Objective

Every internal `claude`-launch site in loam is telegram-plugin-isolated
such that spawning any internal `claude` cannot disconnect a
concurrently-running operator session's Telegram poller — by extending
the proven subloam-driver isolation to the handsoff-loop sites (the only
unisolated family, contract §1b), reusing the existing mechanism
(contract §2), introducing no new isolation machinery.

## §2 — Fence (sealed-component)

Seal anchor: **`workspace-bootstrap`**
(`framework/workspace-bootstrap/tests/test_no_sealed_amendments.py`,
BASELINE bumped at apply to the pre-apply branch tip). Its LIVE
seal-test admits every surface this build touches: `framework/tools/`
(the three §1b handsoff-loop launch sites + the new isolation helper +
the AC test files), `docs/plans/` + `docs/STATE.md` (plan + manifest +
backfill).

Anchor rationale (autonomously resolved per operational-objective test,
recorded for the register): the §1b sites live under
`framework/tools/handsoff-loop/`, inside the `workspace-bootstrap`
seal-test's admitted `framework/tools/` prefix. Mirrors the
`subloam-driver-fix` + `handsoff-loop-real-build` precedents that sealed
cleanly against `workspace-bootstrap` on this exact branch tip.

**IN fence** (contract §3.2):
- Wiring the three §1b handsoff-loop launch sites
  (`intake.py:_claude_json`, `goal_drive.py:build_goal_drive_argv`,
  `orchestrator.py:_dispatch_subagent`) so each spawned `claude` carries
  the same telegram-plugin-unreachable argv + token/API-key-scrubbed env
  the subloam-driver mechanism produces.
- The empty-MCP-config file lifecycle those sites need (mirroring
  `write_empty_mcp_config`).
- The acceptance suite extending the contract §2 three-part pattern to
  the §1b sites.

**OUT of fence (explicit)** (contract §3.2):
- Any change to the bot token, `~/.claude/channels/telegram/.env`,
  `access.json`, `.mcp.json` (workspace or plugin), or any
  channel/onboarding config. The fix is sub-process-reach narrowing
  only. (Contract §5 verifies this is necessary-and-sufficient; if it
  were not, that flips it to owner-gated — contract §6 Halt-2.)
- The upstream plugin-cache hardening
  (`~/.claude/plugins/.../telegram/.../server.ts`) — owner-gated,
  separate, not planned here.
- The §1a already-isolated sites (subloam-driver / resolvers /
  synthesis / upgrade-merge) — already correct; re-wiring forbidden.
- The §1c non-`claude` subprocess sites — not kill-vector sites;
  untouched.

## §3 — Halt-and-surface BEFORE build

Read the contract §6 halt log. The three contract-resolved halts
(Halt-1 structural-can't-reuse NOT triggered; Halt-2 would-need-config
NOT triggered; Halt-3 ODD-violation-in-read-surface NONE found) are
ratified here. The builder re-checks them empirically during the cycle;
if any fires at build time it halts and surfaces, it does not paper.

## §4 — Lens analysis

### Lens 1 — Claude leverage

The fix composes on Claude Code's `--strict-mcp-config --mcp-config`
flag pair (the platform's own MCP-scoping primitive) — the exact
mechanism the official Telegram plugin's single-consumer poller
contention is closed by. No re-implementation of MCP scoping; the
platform flag is the lever.

### Lens 2 — Harness + primary-persona value

A background hands-off-loop run that SIGTERMs the operator's only
user-visible channel fails the harness test outright (the toolkit
becomes net-negative). Closing the §1b kill vector is a direct
harness-test repair: the persona can dispatch the hands-off loop without
severing its own channel to the user.

### Lens 3 — ODD authoring

Objective + fence + outcome-shaped ACs; method (import the proven
functions vs byte-equivalent inline vs wrapper) left to the builder per
contract §2 method-note + §7. Every source line and test maps to a named
AC.TPI.\*; no non-objective code.

## §5 — Acceptance criteria

Verbatim from contract §3.3 (authoritative). One file per AC under
`framework/tools/handsoff-loop/tests/test_AC_TPI_*.py`.

| AC ID | Outcome (not method) |
|---|---|
| **AC.TPI.1** | With a sentinel process holding the single-consumer poller slot, a full handsoff-loop sub-agent dispatch (`orchestrator._dispatch_subagent` via `build_goal_drive_argv`) completes and the sentinel is still alive afterward (`.poll() is None`). Opt-in real-binary. |
| **AC.TPI.2** | Same as AC.TPI.1 for the intake path (`intake._claude_json`, reached via `derive_acceptance_from_intent`): sentinel alive after a real intake `claude -p` call. Opt-in real-binary. |
| **AC.TPI.3** | The argv every §1b site spawns carries the empty-strict-MCP isolation and zero telegram-plugin markers. Fast structural. |
| **AC.TPI.4** | The env every §1b site spawns has `TELEGRAM_BOT_TOKEN` / `CLAUDE_PLUGIN_TELEGRAM_BOT_TOKEN` / `ANTHROPIC_API_KEY` absent. Fast structural. |
| **AC.TPI.5** | A regression that re-introduces a telegram-reachable argv at any §1b site fails loudly (raises / test-red) rather than silently shipping a kill-capable invocation. |
| **AC.TPI.6** | The §1a already-isolated sites and §1c non-`claude` sites are unchanged by the fix. Fence integrity. |

**Honest-negative validity (Lens 3 / contract §3.3):** if AC.TPI.1/.2
cannot be made green because a §1b site **structurally cannot** carry
the isolation, that is a valid terminal outcome → contract §6 Halt-1
(name it, do not paper "contained"). Source read shows no such
dependency; not expected — but a valid AC outcome, not a forced green.

## §6 — Behaviour count

| # | Declared behaviour | AC |
|---|--------------------|-----|
| 1 | Handsoff-loop sub-agent dispatch cannot SIGTERM the operator poller (real-binary) | AC.TPI.1 |
| 2 | Intake `claude -p` call cannot SIGTERM the operator poller (real-binary) | AC.TPI.2 |
| 3 | Every §1b spawned argv carries empty-strict-MCP, zero telegram markers | AC.TPI.3 |
| 4 | Every §1b spawned env scrubs bot-token + API-key spellings | AC.TPI.4 |
| 5 | Telegram-reachable argv regression at a §1b site fails loudly | AC.TPI.5 |
| 6 | §1a / §1c sites untouched by the fix | AC.TPI.6 |

## §7 — Hard constraints

1. **No `--amend`.** New corrective commits only. This is a NEW
   amendment cycle stacked on `amend/loam-init-persona-wiring`; the
   prior `handsoff-loop-real-build` seal is done — never amend it.
2. **Scope fence.** §1b only. §1a/§1c FORBIDDEN to touch (AC.TPI.6).
3. **Plan-before-code.** This plan + manifest land before code.
4. **No new third-party dependency.** Stdlib + the existing
   subloam-driver surface only.
5. **Backward-compat preserved.** The §1b sites' existing argv shape
   (positional `-p` prompt, `--output-format json`, `--permission-mode
   bypassPermissions`) is preserved; only the isolation flags + env
   scrub are added — not a reshape.
6. **LOCAL SEAL ONLY.** NOT merged to main, NOT pushed, NOT published,
   NOT tagged. `origin/main` stays exactly at its current commit.
7. **NO Anthropic API key** — real `claude` binary, default Sonnet
   (`feedback_no_anthropic_api_key`); the env scrub enforces this.

## §8 — Out of scope

- Re-wiring the §1a already-isolated sites (no-op churn).
- The §1c non-`claude` subprocess sites.
- The upstream plugin-cache hardening (owner-gated, separate).
- Any bot-token / channel / `.mcp.json` / onboarding config change.
- Defense-in-depth resilience (reaper, KeepAlive respawn) — orthogonal.

## §9 — Bookkeeping surface

Sealed-component cycle. Single-component fence: `workspace-bootstrap`
(seal-test `framework/workspace-bootstrap/tests/test_no_sealed_amendments.py`,
sidecar `framework/workspace-bootstrap/tests/SEAL_COMMIT`). The §1b
source edits + new isolation helper + AC test files land under the
admitted `framework/tools/` prefix; plan/manifest + STATE/roadmap
backfill under the `docs/plans/` + `docs/STATE.md` universal admissions.
Manifest: `docs/plans/telegram-poller-isolation-fix.manifest.yaml`.
Ritual: source+tests → `loam amend validate` → `loam amend apply` →
`loam amend seal`.

## §10 — Implementation order

1. Read session-start corpus + this plan + the binding contract.
2. Author the isolation helper (`handsoff_loop` reuses subloam-driver's
   proven functions — method: import).
3. Wire `intake._claude_json`, `goal_drive.build_goal_drive_argv`,
   `orchestrator._dispatch_subagent`.
4. Author the six AC.TPI.\* test files.
5. Run touched tests (structural ACs first; then opt-in real-binary
   AC.TPI.1/.2 for real).
6. `loam amend validate` → `loam amend apply` → `loam amend seal`.
7. §14 SHA backfill + STATE/roadmap.

## §11 — Halt triggers

1. A §1b site structurally cannot carry the isolation (contract §6
   Halt-1). HALT, surface with evidence, report straight — NOT
   retry-to-green.
2. The contained mechanism turns out NOT necessary-and-sufficient
   (contract §6 Halt-2 — flips to owner-gated). HALT.
3. ODD violation observed in surrounding code/docs. HALT; do not extend.
4. Out-of-fence drift discovered mid-edit (§1a/§1c). HALT.
5. Wall-clock exceeds the dispatch ceiling. HALT with current state.
6. Canonical `main`/`origin/main` drift post-seal, or a prior commit
   reverted by clean-tree ops. HALT; surface, do not silently re-FF.

## §12 — Decisions

**No genuine owner decision. Ready to build.** (Contract §7.)

The only candidate — "reuse subloam-driver's functions by import vs
re-implement byte-equivalent inline vs wrapper" — is a *method* choice
(Lens 3: the builder's call). Resolved: **import**. Rationale: contract
§2 names "reuse the proven mechanism, introduce no new isolation
machinery" as a hard constraint; import is the highest-fidelity reuse
(zero drift from the sealed source) and the marker-guard (AC.TPI.5
durability) comes for free since `build_isolated_claude_argv` already
raises on telegram markers. The §1b argv shapes are NOT reshaped to the
subloam interactive shape — only the isolation flags + env scrub are
injected into each site's existing argv (necessary-and-sufficient per
contract §5; reshaping would break the §1b sites' `-p`/json function and
breach AC.TPI.6).

## §13 — Halt findings

Per `feedback_subagent_odd_violation_halt`: halt and surface any ODD
violation observed in surrounding code/docs.

**(none observed during plan authoring — contract §6 Halt-3 NONE
ratified; the §1b sites lack isolation but that is the bug being fixed,
not a pre-existing ODD violation to extend.)**

## 14. Method-decision register + commit SHAs

| # | Decision | Resolution | Authority |
|---|----------|-----------|-----------|
| 1 | Reuse-method (import vs inline vs wrapper) | Import subloam-driver's `build_isolated_claude_argv` / `build_isolated_env` / `write_empty_mcp_config` | Builder's call (Lens 3 / contract §2 §7) |
| 2 | §1b argv shape | Inject isolation flags into the existing `-p`/json argv; do NOT reshape to subloam interactive shape | Builder's call; contract §5 necessary-and-sufficient; AC.TPI.6 fence |
| 3 | Seal anchor | `workspace-bootstrap` (admits `framework/tools/`) | Operational-objective test; mirrors `handsoff-loop-real-build` precedent |

### Commit SHAs

Single-component fence: `workspace-bootstrap`. Branch
`amend/loam-init-persona-wiring` (LOCAL SEAL ONLY — NOT merged to
`main`, NOT pushed, NOT published, NOT tagged).

| Stage | SHA |
|---|---|
| BASELINE (amendment-window parent) | `38b8f0f` |
| Plan + manifest commit | `b728ace` |
| Source-edit commit (feature) | `e0b71cb` |
| Apply auto-commit | `969c4bc` |
| Seal commit | `b33c0a8` |

### Per-AC GREEN evidence

| AC | Outcome | Evidence |
|---|---|---|
| AC.TPI.1 | Handsoff-loop sub-agent dispatch cannot SIGTERM the operator poller | Opt-in real-binary (`TPI_REAL_CLAUDE=1`): real `claude` 2.1.143 spawned via `_dispatch_subagent`; sentinel `.poll() is None` afterward — PASSED |
| AC.TPI.2 | Intake `claude -p` call cannot SIGTERM the operator poller | Opt-in real-binary: real `claude` 2.1.143 spawned via `intake._claude_json`; sentinel alive afterward — PASSED |
| AC.TPI.3 | Every §1b argv carries empty-strict-MCP, zero telegram markers | Structural — `build_goal_drive_argv` + intake argv both isolated, `-p`/json shape preserved — PASSED |
| AC.TPI.4 | Every §1b env scrubs bot-token + API-key spellings | Structural — `isolated_env` drops all 3 spellings; `CLAUDE_CONFIG_DIR` unset (subscription auth) — PASSED |
| AC.TPI.5 | Telegram-reachable argv regression fails loudly | Structural — `inject_isolation` raises on telegram markers; clean argv passes — PASSED |
| AC.TPI.6 | §1a / §1c sites untouched | Diff window `38b8f0f..HEAD`: zero §1a/§1c files; only the 4 §1b sources + tests + plan — PASSED |
