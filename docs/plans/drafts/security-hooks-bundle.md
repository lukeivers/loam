# Security hooks bundle — per-work-item plan-doc (Wave 1 of ECC absorption)

**Status:** per-work-item plan-doc, plan-before-code, DRAFT — pending owner ratification of this plan. Authored 2026-05-24 by `loam-plan-author` subagent.
**Working directory:** `/Users/lukeivers/loam/` (canonical loam tree).
**Parent plan:** `docs/plans/drafts/everything-claude-code-absorption-master-plan.md` (Wave 1, WI-2).
**Predecessors:**
- D-SEC.HOOKS ratified core-loam-always-on placement per Telegram 12249 + 12301.
- Master absorption plan §4 D-SEC.HOOKS + §5 WI-2 sketch (the AC family seed + objective name).
- Existing `framework/safety-layer/` component (architecture per `framework/safety-layer/docs/architecture.md`) — composes with, does not replace.
- Existing `plugins/dev-sdlc/hooks/bash_guard.py` — load-bearing overlap; see §10 F2 doubt #1 + §3 fence treatment.

**BASELINE (pre-build tip, to be refreshed at apply time):** current `pos-v2` HEAD per `git -C /Users/lukeivers/loam log -1 --format=%H`.
**Status-file target:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/security-hooks-bundle-status-2026-05-24.md` (created at build time).
**Quality bar:** decision-doc + per-work-item plan; owner ratifies §5 AC family + §3 fence + §8 open question Q1 (B2/B5 overlap-deletion-vs-divert) before any build dispatch. No source touched in this dispatch.

---

## §0 — Executive summary

### TL;DR (5 bullets)

1. **Install three PreToolUse hooks in `framework/safety-layer/hooks/`** — secret-pattern detection (sk-/ghp_/AKIA + ~11 more), dangerous-flag blocking (`--no-verify` on git push / commit; `--force` against protected branches), config-file write-protection (`.eslintrc`, `biome.json`, `.pre-commit-config.yaml`, `.git/config`). Wired into every loam workspace's `<workspace>/.claude/settings.json` via the existing `first_run_settings.merge_pre_tool_use` registration helper. Always-on per D-SEC.HOOKS; toggle-off via `LOAM_SAFETY_HOOKS=off` env var.
2. **Load-bearing overlap with existing `plugins/dev-sdlc/hooks/bash_guard.py`** must be resolved before build. `bash_guard.py` already covers (a) secret-FILE commit detection (`.env`, `*.pem`, `id_rsa`) and (b) blast-radius destructive commands. The new safety-layer secret-PATTERN hook covers different surface (secret-CONTENT in pasted strings); dangerous-flag hook overlaps `bash_guard`'s B5 surface partially. Decision needed (Q1 §8): divert (new hooks cover net-new patterns only; dev-sdlc keeps its surface) OR partial absorption (move B2/B5 universal-fires out of dev-sdlc into safety-layer; dev-sdlc retains dev-only B1/B3/B4). Recommendation: **divert** (smaller blast radius; bash_guard is already sealed).
3. **Hooks fail-open by default** — any exception (regex error, runtime fault, missing dependency) → allow the operation, log the failure to `<workspace>/.loam/safety-hooks.log`. Per D-SEC.HOOKS rationale: real security is structural-defense-in-depth; loam's hooks are belt to suspenders the user already has. Failing closed on a hook fault would create a worse failure mode than the one being defended against.
4. **Three ACs are outcome-altitude (AC.SECHK.S1 / S2 / S3)** — one per hook. Each invokes the production hook dispatch path with no pre-arranged state: synthetic Claude Code PreToolUse envelope arriving at the hook script via stdin, blocked diagnostic emitted to stdout, exit-0 (per loam hook convention). Per `feedback_test_outcome_altitude_required.md` — STUB-class tests on parsed input do NOT satisfy the outcome-altitude AC.
5. **Two sealed-component cycles serialized** per `feedback_serialize_amendment_builds.md` — Cycle 1 ships the three hooks + registration + tests in a single multi-component fence (`framework/safety-layer/` + `framework/hands-off-lifecycle/` for the settings-merge wiring); Cycle 2 ships the workspace-bootstrap template seed (so fresh workspaces get the hooks at first-run). Two manifests, two `loam amend apply` runs, two seals. Decision noted: if scope-discipline check at Cycle-1-plan-time finds Cycle 2 has no fence overlap with Cycle 1 (likely), they MAY be merged into a single multi-component cycle. Default = serialized.

### Named decisions with recommendations (maintainer-facing summary table)

| ID | Decision | Recommendation | Rationale (short) | Reversibility | Blast radius |
|---|---|---|---|---|---|
| **D-SECHK.OVERLAP** (Q1) | How to resolve overlap with existing `plugins/dev-sdlc/hooks/bash_guard.py`? Divert (new hooks ≠ existing surface), partial absorption (move B2/B5 universal-fires to safety-layer), or full absorption (move all bash_guard logic). | **Divert.** Safety-layer hooks cover net-new patterns (secret-CONTENT, dangerous-FLAG, config-FILE-write); bash_guard.py keeps its existing dev-mode surface (B1 amend-in-subagent, B3 amend-dry-run-fail, B4 wrong-tree-write) PLUS its universal surfaces (B2 secret-FILE-commit, B5 blast-radius). Two hooks in the PreToolUse stanza is supported (matcher independence). | High (revisit at v0.2+ once we observe whether the divert produces user-visible "two hooks fired" noise) | Low (no sealed-component change to bash_guard) |
| **D-SECHK.FAIL-OPEN** | Hooks fail-open (allow + log) or fail-closed (deny + diagnostic) on internal hook fault? | **Fail-open + structured log.** | Per D-SEC.HOOKS rationale; real security is defense-in-depth. Failing closed on a regex-engine fault would block legitimate work for a self-inflicted reason. | High (toggle to fail-closed via env var if log shows zero-faults over a steady-state window) | Low (faults log to dedicated file; never silently dropped) |
| **D-SECHK.PATTERN-SET** | Which secret patterns ship in v1? ECC's 14-pattern set verbatim, a loam-curated subset, or a superset? | **ECC's 14-pattern set verbatim as the v1 floor; allow workspace-additions via `<workspace>/.loam/secret-patterns.yaml` (additive only — cannot remove framework floor).** | ECC's set is empirically tested; loam matches the floor + allows workspace extension. The additive-only constraint matches the existing safety-layer `always_ask` floor pattern. | High (patterns are data; add/remove without code change) | Low |
| **D-SECHK.TOGGLE-GRANULARITY** | Toggle off via one env var (`LOAM_SAFETY_HOOKS=off`) or per-hook env vars (`LOAM_SAFETY_HOOKS_SECRET=off`, `_DANGEROUS_FLAG=off`, `_CONFIG_WRITE=off`)? | **Both.** Single var disables all three; per-hook vars disable individually. | Per-hook granularity matters when one hook is noisy (e.g., config-write fires on legitimate `.git/config` edits during workspace setup); single var matters for "loam is broken; let me turn off the whole guard" emergencies. Cheap to provide both. | High | Low |
| **D-SECHK.DIAGNOSTIC-SHAPE** | Blocked-operation diagnostic surface: structured JSON (machine-readable for the persona) or plain text (human-readable for the user)? | **Structured JSON per Claude Code's `hookSpecificOutput.permissionDecisionReason` shape (matches existing `bash_guard.py` convention). The persona translates the JSON to user-readable text per `feedback_translate_outbound_too.md` discipline.** | Consistency with existing hooks; persona is the translation layer. | High | Low |
| **D-SECHK.CYCLE-SHAPE** | Two cycles (hooks + registration; then bootstrap-seed) or one multi-component cycle? | **Default to two serialized; build phase MAY merge if Cycle-2 plan finds no fence overlap with Cycle-1.** | Serialization is the safe default per `feedback_serialize_amendment_builds`; merge is an optimization that depends on Cycle-1-plan finding zero risk. Defer the merge call to plan time. | High | Low |

---

## §1 — Plan objective + scope

### Objective

Author the per-work-item plan-doc for WI-2 (`safety-layer-input-hooks`) such that, on maintainer ratification, the build-dispatch agent can execute Cycle 1 + Cycle 2 with method-time decisions covered by §6 build steps and method-of-build covered only by the AC ladders + halt triggers (per AGENT-PROMPTS-SCOPE-ONLY + ODD §2.5).

Outcome: three production PreToolUse hooks installed in `framework/safety-layer/hooks/`, registered via `first_run_settings.merge_pre_tool_use` into every loam workspace's `<workspace>/.claude/settings.json` at first-run, fail-open with structured diagnostics, toggle-off via env vars, covering secret-pattern leaks + dangerous-flag invocations + config-file writes.

### In-scope

- Three new PreToolUse hook scripts at `framework/safety-layer/hooks/`:
  - `secret_pattern_guard.py` — content-pattern detection in Bash command args + Edit/Write content
  - `dangerous_flag_guard.py` — flag-pattern detection in Bash command args (git push --no-verify, git commit --no-verify, git push --force against protected branches)
  - `config_write_guard.py` — path-target detection in Edit/Write/MultiEdit tool inputs (.eslintrc / biome.json / .pre-commit-config.yaml / .git/config)
- Shared helper module `framework/safety-layer/hooks/_secret_patterns.py` carrying the 14-pattern floor + workspace-additions loader.
- Registration changes in `framework/hands-off-lifecycle/hooks/first_run_settings.py` — three new entries in the `POS_V2_PRETOOLUSE_HOOK_MARKERS` set; `merge_pre_tool_use` composes the three new hook entries alongside existing pos-v2 hooks.
- Workspace-bootstrap template update — `framework/workspace-bootstrap/` first-run scaffold writes the new hooks into the settings.json template (via the existing merge mechanism; no template rewrite).
- Tests:
  - Unit tests per hook (pattern match / non-match / fail-open behavior / toggle-off behavior / structured diagnostic shape).
  - Integration tests via the `merge_pre_tool_use` helper that the three hooks land in settings.json correctly.
  - Three outcome-altitude tests invoking the production hook dispatch path with no pre-arranged state.
- Documentation:
  - Update `framework/safety-layer/docs/architecture.md` with the new hooks subdir + composition with refusal-chain.
  - Append to `docs/getting-started.md` the LOAM_SAFETY_HOOKS env var documentation.

### Out-of-scope

- **Content-deep secret scanning** (e.g., entropy-based detection, AI-call to verify) — this is pattern-class only.
- **PostToolUse cleanup hooks** — defense-in-depth for what hooks let through; deferred to a separate work-item.
- **Refusal-chain extensions** — the new hooks compose with the existing `safety-layer` `SafetyController`; they do NOT replace or modify the refusal-chain dispatcher.
- **Migration of `bash_guard.py` content** — per D-SECHK.OVERLAP recommendation; bash_guard keeps its surface; the new hooks cover net-new patterns. (Reversal of this decision = follow-on work-item, NOT in this fence.)
- **Persona-side translation of structured diagnostics** — persona behavior (how it surfaces "the safety-layer blocked X" to non-tech users) is per `feedback_translate_outbound_too.md` already in corpus; no new persona code in this work-item.
- **Hooks for non-Claude-Code surfaces** (e.g., bash invocations outside Claude Code) — out of scope per L1 (loam is Claude-attached).
- **Workspace allowlist mechanism for false-positive whitelisting** (e.g., "this regex pattern is OK for this workspace") — captured to FIDRAFT for v0.2+; v1 is fail-open + log, which makes whitelisting unnecessary at the start.
- **Per-pattern severity tiers** (warn / block / require-confirm) — v1 ships block-only with toggle-off; severity tiers deferred.

---

## §2 — Acceptance criteria

All ACs scope-descriptive per `feedback_scope_descriptive_ac_ids.md` (slug `SECHK`). Outcome-altitude ACs marked per `feedback_test_outcome_altitude_required.md`. AC ladder ladders up to AC.PO.1 + AC.PO.2 (VALUE_PROPOSITION prime objective) via "primary persona absorbs the safety check on user's behalf" + "harness toolkit gains structural defense surface."

### AC.SECHK.* — input-layer security hooks

- **AC.SECHK.1 — Secret-pattern hook fires on Bash command args + Edit/Write content; blocks the 14-pattern floor; emits structured `permissionDecisionReason`.** Test cases: each of the 14 patterns (sk-..., ghp_..., AKIA..., etc.) embedded in (a) a Bash command argument (`echo sk-abc123`), (b) an Edit/Write tool input (file content). Tests assert hook stdout contains `permissionDecision: "deny"` + the pattern name in the reason. Non-match cases (random strings, English prose) pass through (default-allow). Pattern set loaded from `framework/safety-layer/hooks/_secret_patterns.py` (the floor) PLUS optional `<workspace>/.loam/secret-patterns.yaml` (additive).
- **AC.SECHK.2 — Dangerous-flag hook blocks `git push --no-verify`, `git commit --no-verify`, `git push --force` against protected branches.** Test cases: each named flag-shape in a Bash command arg. Protected-branch list defaults to `{main, master, pos-v2, production}` and loads optional `<workspace>/.loam/protected-branches.yaml`. Non-`git` commands pass through. `git push --force` against a non-protected branch passes through.
- **AC.SECHK.3 — Config-write hook blocks writes to `.eslintrc{,.json,.js}`, `biome.json`, `.pre-commit-config.yaml`, `.git/config`, `.gitignore` via Edit/Write/MultiEdit tool inputs.** Test cases: each named path-shape (absolute + relative-to-cwd) in tool input's `file_path` field. Non-config paths pass through.
- **AC.SECHK.4 — All three hooks fail-open on internal exception.** Test cases: each hook receives a malformed input envelope (missing `tool_input`, non-JSON stdin, unicode-decode-error). Hook returns exit-0 with empty stdout (default-allow) AND appends a structured NDJSON line to `<workspace>/.loam/safety-hooks.log` naming the fault. No exception propagates.
- **AC.SECHK.5 — Toggle-off env vars disable hooks at the granularity declared.** Test cases: `LOAM_SAFETY_HOOKS=off` → all three hooks no-op (return exit-0 immediately, do not pattern-match). `LOAM_SAFETY_HOOKS_SECRET=off` → only secret-pattern hook no-ops; other two still fire. (And symmetric for the other two per-hook env vars.) When toggled-off, hook records the no-op in NDJSON log so a later audit can confirm it was actually disabled, not silently broken.
- **AC.SECHK.6 — Three new hook entries land in `<workspace>/.claude/settings.json` at first-run scaffold AND on re-merge.** Test cases: run `first_run_settings.merge_pre_tool_use` against a tmpfs workspace with no prior settings.json → settings.json has `hooks.PreToolUse[0].hooks` containing entries for the three new hook scripts (matcher pattern correct per the hook's target tool: `Bash` for secret/dangerous-flag; `Edit|Write|MultiEdit` for config-write — the matcher independence preserved per the existing convention). Re-running the merge over a settings.json that already has the pos-v2 hooks is idempotent (no duplicates). A user-authored PreToolUse stanza is preserved alongside (per existing test_AC_OBG_settings_merge convention).
- **AC.SECHK.7 — Existing `plugins/dev-sdlc/hooks/bash_guard.py` continues firing unchanged (no regression).** Test cases: every AC.BAG.1 through AC.BAG.7 (in `framework/hands-off-lifecycle/tests/test_AC_BAG_*.py`) still passes. The two hooks coexist in the PreToolUse stanza (Claude Code dispatches both per matcher; either can `deny`). New hook scripts MUST NOT modify bash_guard.py or its registered marker entries.
- **AC.SECHK.S1 (outcome-altitude) — synthetic session: secret-pattern hook blocks a pasted `sk-...` content via the production dispatch path.** Test: spawn a subprocess invocation of `framework/safety-layer/hooks/secret_pattern_guard.py` with a Claude Code PreToolUse envelope on stdin (`{"tool_name":"Bash","tool_input":{"command":"echo sk-test-abc123"},...}`). Assert stdout contains `permissionDecision: "deny"` + pattern name. No pre-arranged state in the test (no fakes, no module-level patches, no stubs on the regex engine).
- **AC.SECHK.S2 (outcome-altitude) — synthetic session: dangerous-flag hook blocks `git push --no-verify` via the production dispatch path.** Same shape as S1; subprocess invocation; stdin envelope; stdout deny.
- **AC.SECHK.S3 (outcome-altitude) — synthetic session: config-write hook blocks an Edit to `.eslintrc.json` via the production dispatch path.** Same shape; tool envelope carries `Edit` + `file_path: <abs>/.eslintrc.json`; stdout deny.
- **AC.SECHK.S4 (outcome-altitude) — fresh-workspace smoke: settings.json scaffold lands the three hooks; a `claude` session in the scaffolded workspace observes hook-block on a synthetic blocked operation.** Status-file-recorded (not a unit test; ride-along smoke). Per parent absorption plan §6 — this is the cross-cycle smoke that confirms the workspace-bootstrap seed wires the hooks correctly end-to-end.

### Fence (sealed-component scope)

- **Cycle 1 fence:** `framework/safety-layer/` (the three new hooks + helper + tests + docs update); `framework/hands-off-lifecycle/` (the merge_pre_tool_use marker-set extension + tests). Plus `docs/plans/` for plan-doc + manifest, plus `docs/getting-started.md` for env-var docs (universal-admit prefix). NO touch to `plugins/dev-sdlc/hooks/bash_guard.py` (sealed; D-SECHK.OVERLAP recommended divert).
- **Cycle 2 fence:** `framework/workspace-bootstrap/` (template seed update — the fresh-workspace scaffold path triggers the merge). Plus `docs/plans/` for cycle-2 manifest.
- **If cycles merge per D-SECHK.CYCLE-SHAPE:** single fence is the union of Cycle 1 + Cycle 2 fences.

---

## §3 — Fence (in/out, sealed-component-aware)

### In-fence

| Path | Cycle | Reason |
|---|---|---|
| `framework/safety-layer/hooks/secret_pattern_guard.py` | 1 | New hook script. |
| `framework/safety-layer/hooks/dangerous_flag_guard.py` | 1 | New hook script. |
| `framework/safety-layer/hooks/config_write_guard.py` | 1 | New hook script. |
| `framework/safety-layer/hooks/_secret_patterns.py` | 1 | Shared pattern data + workspace-additions loader. |
| `framework/safety-layer/hooks/__init__.py` | 1 | New subpackage init. |
| `framework/safety-layer/tests/test_AC_SECHK_*.py` | 1 | One test file per AC. |
| `framework/safety-layer/docs/architecture.md` | 1 | Append hooks subdir + composition notes. |
| `framework/hands-off-lifecycle/hooks/first_run_settings.py` | 1 | Extend `POS_V2_PRETOOLUSE_HOOK_MARKERS` + add the three new hook entry shapes. |
| `framework/hands-off-lifecycle/tests/test_AC_SECHK_6_settings_merge.py` | 1 | Settings-merge integration test for the three new hooks. |
| `docs/getting-started.md` | 1 | LOAM_SAFETY_HOOKS env var docs (small section). |
| `docs/plans/security-hooks-bundle.md` (this file → final non-draft location) | 1 + 2 | Plan-doc; lives in `docs/plans/` per convention §1. |
| `docs/plans/security-hooks-bundle.manifest.yaml` | 1 | Cycle-1 manifest. |
| `docs/plans/security-hooks-bundle-cycle2.manifest.yaml` | 2 | Cycle-2 manifest. (If cycles merge: single manifest.) |
| `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py` | 2 | Bootstrap-seed wires hooks at fresh-workspace scaffold. (Verify path during Cycle-2 plan.) |
| `framework/workspace-bootstrap/tests/test_AC_SECHK_S4_*.py` | 2 | Cross-cycle smoke. |

### Out-of-fence (explicit non-touches)

| Path | Reason |
|---|---|
| `plugins/dev-sdlc/hooks/bash_guard.py` | Sealed; D-SECHK.OVERLAP recommended divert (NOT migration). Halt-and-surface if Cycle-1 finds it impossible to ship the new hooks without touching bash_guard. |
| `plugins/dev-sdlc/hooks/tdd_guard.py` | Unrelated. |
| `plugins/dev-sdlc/hooks/agent_guard.py` | Unrelated. |
| `framework/safety-layer/src/loam/safety_layer/controller.py` (existing SafetyController) | New hooks compose alongside; do NOT modify the refusal-chain runtime. |
| `framework/safety-layer/src/loam/safety_layer/dangerous_op.py` (existing DangerousOpGate) | New hooks fire BEFORE the orchestrator dispatch; DangerousOpGate fires DURING dispatch. Separate surfaces; no merge. |
| `framework/hands-off-lifecycle/canonical-dev/settings.dev-template.json` | Currently SessionStart-only. The new hooks merge into the runtime settings.json (not the dev-template) per the workspace-side scaffolding pattern. If extension needed for canonical-dev parity — separate decision, captured to §11 FIDRAFT. |

### Fence-rationale

The three new hooks are net-new files in a new subdirectory of an existing sealed component (`safety-layer`); per partition rules and the existing safety-layer architecture (`framework/safety-layer/docs/architecture.md`), the component owns its own hooks surface and the new files don't touch existing sealed code. The `hands-off-lifecycle` touch is a single function (`merge_pre_tool_use`) that's already designed to compose multi-hook stanzas — extending the marker set + adding three entries is the existing extension shape. The workspace-bootstrap touch (Cycle 2) is the template-seed equivalent.

---

## §4 — Work decomposition (cycle-level method outline)

Method is the builder's call per ODD §1.1; what follows is the cycle decomposition + ordering, not method-in-AC. Per AGENT-PROMPTS-SCOPE-ONLY: the eventual build dispatch carries scope only; the cycle decomposition here informs the dispatcher's scope-authoring, not the builder's implementation.

### Cycle 1 — three hooks + registration + tests (multi-component fence)

1. Plan-doc lands (this file ratified by owner; moves from `docs/plans/drafts/` to `docs/plans/`).
2. Cycle-1 manifest authored (`docs/plans/security-hooks-bundle.manifest.yaml`) — multi-component fence on `framework/safety-layer/` + `framework/hands-off-lifecycle/`, plus universal paths for `docs/plans/` + `docs/getting-started.md`.
3. Source edits (order is builder's call; suggested order surfaced for review only):
   - `framework/safety-layer/hooks/__init__.py` (empty subpackage)
   - `framework/safety-layer/hooks/_secret_patterns.py` (pattern data + loader)
   - `framework/safety-layer/hooks/secret_pattern_guard.py`
   - `framework/safety-layer/hooks/dangerous_flag_guard.py`
   - `framework/safety-layer/hooks/config_write_guard.py`
   - `framework/safety-layer/tests/test_AC_SECHK_*.py` (per AC)
   - `framework/safety-layer/docs/architecture.md` (append hooks subdir + composition)
   - `framework/hands-off-lifecycle/hooks/first_run_settings.py` (marker set extension + entry shape)
   - `framework/hands-off-lifecycle/tests/test_AC_SECHK_6_settings_merge.py` (integration test)
   - `docs/getting-started.md` (env-var docs)
4. Touched-tests run (only the new tests + existing `framework/safety-layer/tests/` + `framework/hands-off-lifecycle/tests/` regression band per `feedback_amendment_dispatch_speedups`).
5. `loam amend apply` (per `feedback_dispatch_explicit_loam_amend_apply` — NOT `git commit --amend`).
6. `loam amend seal` (deterministic seal commit).
7. Smoke (D1 cold-state): unit-test-level outcome-altitude smokes S1 + S2 + S3 pass.

### Cycle 2 — workspace-bootstrap template seed (single-component fence)

1. Cycle-2 manifest authored (`docs/plans/security-hooks-bundle-cycle2.manifest.yaml`).
2. Source edits:
   - `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py` — verify path; the scaffold may already call `first_run_settings.merge_pre_tool_use` (in which case extending the marker set in Cycle 1 is sufficient). If a separate seed-path is needed, add it here.
   - `framework/workspace-bootstrap/tests/test_AC_SECHK_S4_fresh_workspace_hooks_present.py` (cross-cycle smoke).
3. Touched-tests run (`framework/workspace-bootstrap/tests/`).
4. `loam amend apply`.
5. `loam amend seal`.
6. Smoke (S4): fresh workspace scaffold → three hooks present in settings.json → synthetic Claude session → hook-block observable.

### Cycle-merge condition

If the Cycle-2 plan (authored separately at build-time) finds that the workspace-bootstrap scaffold ALREADY composes `merge_pre_tool_use` (likely, per the existing `test_AC_TDG_settings_merge.py` precedent), then Cycle 1 + Cycle 2 collapse into a single multi-component cycle whose fence is the union of the two fences above. Decision deferred to Cycle-1-plan-time per D-SECHK.CYCLE-SHAPE.

---

## §5 — Risk surfaces

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| **Hook-noise from legitimate operations.** False-positive secret-pattern fires on a legitimate ECC-prefix-like string in user input (e.g., a project named `sk-something`). | MEDIUM | MEDIUM | (a) ECC's 14-pattern set is empirically tested; false-positive rate has not been measured for loam's user base. (b) Workspace-additions mechanism allows adding patterns; no in-product mechanism for REMOVING floor patterns. (c) Halt trigger per §7: more than 1 false-positive per session during build-time smoke = halt + tighten patterns. (d) Toggle-off env var per AC.SECHK.5 is the user-facing escape hatch. |
| **Hook-noise from `.git/config` legitimate edits during workspace setup.** Config-write hook fires on `git config --local user.email` style commands during workspace init. | MEDIUM | HIGH | The config-write hook matches Edit/Write/MultiEdit tool inputs on `file_path`; Bash `git config` invocations don't match (matcher is `Edit|Write|MultiEdit` per AC.SECHK.6). So `git config` Bash commands pass through. Halt-and-surface if Cycle 1 testing finds Bash `git config` somehow tripping the hook. |
| **bash_guard.py + new hooks both fire on same Bash command.** Two hooks deny with different reasons; persona may surface both. | LOW | MEDIUM | Per Claude Code semantics: if EITHER hook denies, the operation is blocked. The user sees the first-emitted reason; persona translation per `feedback_translate_outbound_too.md` consolidates. No technical breakage; possible UX confusion. Mitigated by D-SECHK.OVERLAP divert (no surface overlap on the AC level — bash_guard.py covers files, new hooks cover content). |
| **Fail-open lets a real attack through.** A regex-engine fault on a real secret-pattern fires the fail-open path; the operation proceeds; the secret leaks. | MEDIUM | LOW | This is the accepted risk per D-SECHK.FAIL-OPEN. Mitigation: NDJSON log of every fault; persona surfaces faults in audit-block; halt-trigger on >1 fault in steady-state. Real defense lives at the surface above (user's existing git-hook protections, GitHub's secret-scanning, etc.) — loam's hooks are belt-not-suspenders. |
| **Settings.json merge breaks user-authored hooks.** A user has authored their own PreToolUse hook; merge overwrites it. | HIGH | LOW | The existing `merge_pre_tool_use` helper preserves user-authored PreToolUse stanzas (per `test_AC_OBG_settings_merge.py` line 110: "existing user PreToolUse hooks are preserved"). AC.SECHK.6 inherits this guarantee. |
| **`bash_guard.py` is moved or renamed in a parallel amendment** between this plan's authoring and build. | LOW | LOW | Plan-doc cites the current path + a SHA snapshot; build-dispatch re-verifies. Halt-and-surface if path changed. |

---

## §6 — Dependencies

This work-item is **Wave 1 leaf** — no dependencies on other ECC-absorption work-items. Composes with:

- **Existing `framework/safety-layer/` component** — the new hooks live inside its directory; the component's existing architecture (SafetyController + DangerousOpGate + refusal-chain) composes alongside (hooks fire pre-dispatch; existing safety fires during/post).
- **Existing `framework/hands-off-lifecycle/hooks/first_run_settings.py`** — extend marker set + entry shape; the merge helper itself is unchanged.
- **Existing `plugins/dev-sdlc/hooks/bash_guard.py`** — coexist; no modification (per D-SECHK.OVERLAP divert).
- **Existing test infrastructure at `framework/hands-off-lifecycle/tests/test_AC_BAG_*.py` + `test_AC_OBG_settings_merge.py`** — pattern reference for the new tests' shape.

Forward dependencies (downstream work-items that compose with this):

- **WI-3 token-defaults SKILL** — independent; can dispatch in parallel.
- **WI-5 observer-loop guard** (Wave 2) — composes via the same `merge_pre_tool_use` mechanism; this work-item lays the multi-hook composition pattern WI-5 reuses.
- **Future workspace allowlist mechanism** (FIDRAFT) — extends `_secret_patterns.py` loader to read workspace whitelists; this work-item lays the loader shape.

---

## §7 — Cost estimate + go-order

### Per-cycle cost (AI-time per `feedback_duration_estimation_rubric.md`)

| Cycle | Tool-calls (estimated) | Wall-clock band (midpoint) | Components touched |
|---|---|---|---|
| **Cycle 1** | 80–140 (3 hooks + helper + 7 tests + 1 docs + 1 integration test) | 12–24 min (18 min midpoint) | 2 sealed |
| **Cycle 2** | 30–60 (workspace-bootstrap path verification + 1 test + manifest) | 6–10 min (8 min midpoint) | 1 sealed |
| **Total (serialized)** | 110–200 | **18–34 min (26 min midpoint)** | 3 sealed |
| **Total (merged cycle)** | 100–180 | 15–28 min (22 min midpoint) | 3 sealed |

Owner gate-review time (separate from AI-time): ratification of this plan-doc estimated 5–10 minutes; mid-build halt-and-surface estimated 0–5 minutes per surface (most surfaces autonomous).

### Go-order

1. **Maintainer ratifies this plan-doc** (per `feedback_record_owner_ratification_before_dispatch.md` — ratification recorded in plan-doc status field; build dispatched off the resulting commit).
2. **Cycle 1 build dispatched** in background (per `feedback_background_agents`; the build is long-generation enough to warrant background per `feedback_background_default_for_authoring`).
3. **Cycle 1 seals + smokes pass** → Cycle 2 dispatched (per `feedback_serialize_amendment_builds`). If Cycle-1-plan-time finds zero risk in merging, single-cycle path is taken.
4. **Cycle 2 seals + smokes pass** → STATE.md + parent absorption plan §6 backfilled with apply + seal SHAs (per `feedback_dispatch_explicit_loam_amend_apply`).
5. **Cross-workspace smoke** (manual; owner-time): fresh canonical loam clone → run a session → verify the three hooks are observable + block their target operations.

---

## §8 — Open questions for maintainer (one-question-at-a-time, ranked)

### Q1 (CRITICAL — blocks build) — D-SECHK.OVERLAP: divert, partial absorption, or full absorption of `bash_guard.py` content?

**Question:** The existing `plugins/dev-sdlc/hooks/bash_guard.py` already covers (B2) secret-FILE commit detection (`.env`, `*.pem`, `id_rsa`) and (B5) blast-radius destructive Bash commands (force-push, `rm -rf` outside scratch, `chmod -R 777`, `curl | bash`, etc.). The new safety-layer hooks cover net-new pattern classes (secret-CONTENT in pasted strings, dangerous git FLAGS, config FILE writes). There is partial conceptual overlap on the "block dangerous Bash" axis. How should we resolve?

**Options:**
- (a) **Divert.** New safety-layer hooks cover net-new patterns only. bash_guard.py keeps its existing surface (B1 dev-mode + B2/B5 universal). Two hooks coexist in the PreToolUse stanza. No sealed-component change to bash_guard.
- (b) **Partial absorption.** Move B2 (secret-FILE-commit) and B5 (blast-radius) — bash_guard's universal-fire surfaces — into the new safety-layer hooks. bash_guard.py retains only dev-mode surfaces (B1 amend-in-subagent, B3 amend-dry-run-fail, B4 wrong-tree-write). Requires sealed-component amendment to dev-sdlc.
- (c) **Full absorption.** Migrate ALL bash_guard content into safety-layer. dev-sdlc no longer ships its own bash_guard. Largest sealed-component change; biggest blast radius.

**Recommendation:** **(a) Divert.** Smallest blast radius (no sealed-component touch to dev-sdlc), preserves the existing dev-mode B1/B3/B4 specialization (which is dev-CDC-scope-correct per `feedback_odd_cdc_scope.md`), and the partial conceptual overlap is acceptable at the hook layer (matcher independence handles it cleanly).

**Rationale:** bash_guard.py's universal surfaces (B2/B5) work; partial absorption would generate identical functionality in two places and require ongoing sync. The conceptual purity argument for absorption is real but doesn't justify the sealed-component churn at v1. If post-ship audit shows the two hooks creating user-visible noise (e.g., persona surfaces both fires on the same operation in a confusing way), revisit per `feedback_locked_design_not_license_for_bad_outcomes.md`.

**Blast radius:** Low (option a) / Medium (option b) / High (option c).

**Reversibility:** High for (a) — can absorb later if signal emerges. Medium for (b)/(c) — sealed-component-touch is harder to reverse.

### Q2 (IMPORTANT) — D-SECHK.PATTERN-SET: ECC's 14-pattern set verbatim, loam-curated, or superset?

**Question:** Which secret-pattern set ships in v1?

**Options:**
- (a) ECC's 14-pattern set verbatim as the floor; workspace-additions via `<workspace>/.loam/secret-patterns.yaml` (additive only).
- (b) Loam-curated subset (drop ECC patterns whose value-axis doesn't apply to non-tech workspaces).
- (c) Superset (ECC's 14 + loam-additions for patterns ECC missed).

**Recommendation:** **(a)** verbatim + additive workspace mechanism.

**Rationale:** ECC's set is empirically tested (loam has zero pattern-fire data; ECC has months); curating now is speculation. The additive workspace mechanism is the structured-extension path; cheap to provide; satisfies the same value-axis as (c) without committing to specific loam-additions before data.

**Blast radius:** Low (data + loader; no logic).

**Reversibility:** High (patterns are data; add/remove without code change).

### Q3 (IMPORTANT) — D-SECHK.CYCLE-SHAPE: confirm two-cycle default vs single-cycle option?

**Question:** Confirm the default two-cycle serialization vs the conditional single-cycle merge (per D-SECHK.CYCLE-SHAPE recommendation).

**Recommendation:** Default to two cycles serialized; build phase may merge to single cycle IF Cycle-1-plan finds no fence overlap with Cycle 2. (i.e., delegate the merge call to the build-dispatch agent's plan-time discretion.)

**Rationale:** Serialization is the safe default (`feedback_serialize_amendment_builds`); merge is an optimization with non-zero coordination risk. Letting plan-time discretion call it preserves the safe default while not forcing waste when the merge is empirically safe.

**Blast radius:** Low either way.

**Reversibility:** High.

### Q4 (NORMAL) — Confirm D-SECHK.FAIL-OPEN + D-SECHK.TOGGLE-GRANULARITY + D-SECHK.DIAGNOSTIC-SHAPE recommendations?

These three are lowest-controversy in the set; recommendations stand unless maintainer objects. Implicit-yes if Q1/Q2/Q3 ratified without comment on these.

---

## §9 — Halt triggers (in-flight)

If any of these fire during build, halt and surface to dispatcher per `feedback_subagent_odd_violation_halt.md`:

1. **WD drifts** off canonical loam (`/Users/lukeivers/loam/`) — halt + surface (per `feedback_dispatch_cd_literal_first_action.md`).
2. **`bash_guard.py` touched** when D-SECHK.OVERLAP recommendation is divert — halt + surface; do not absorb without rerouted ratification.
3. **Pattern-set false-positive rate exceeds ~1/session** during build-time smoke testing — halt + tighten patterns; do not ship a noisy hook (per parent plan §9 halt trigger #1).
4. **Outcome-altitude AC test cannot invoke production hook dispatch path with no pre-arranged state** (test ends up pre-arranged or mock-laden) — halt per `feedback_test_outcome_altitude_required.md`.
5. **Fail-open path fires more than 0 times during build-time smoke** (any internal fault in the new hooks during synthetic load) — halt + diagnose; fail-open is for production faults, not for shipping known faults.
6. **Existing AC.BAG.* tests regress** — halt + diagnose; the divert decision requires bash_guard surface integrity.
7. **More than 5 in-build decisions require maintainer escalation** — halt + summarize per `feedback_summarize_and_surface_decisions.md`; do not silently accumulate.
8. **Cycle 1 seal fails** — halt; do NOT start Cycle 2.
9. **`merge_pre_tool_use` extension breaks existing settings.json merge tests** — halt; the merge surface is load-bearing for the whole hook ecosystem.
10. **Any AC ships partial** — halt + reframe (per `feedback_subagent_odd_violation_halt.md` ODD §2.5).

---

## §10 — F2 Ruthless Feedback (honest doubts)

1. **The "divert" recommendation in Q1 risks silent overlap-rot.** Recommending divert (option a) preserves the existing bash_guard surface, but two hooks covering related axes is a maintenance surface that compounds. The follow-on cost (ongoing sync of pattern lists, dual-fire UX confusion, future re-absorption work) is real. If maintainer time is the bottleneck (per parent plan §10 doubt #4), the right answer might be (b) partial absorption upfront. Calling divert anyway because the parent plan ruled D-SEC.HOOKS at hook-layer not amend-layer; the absorption decision is a separable downstream call. Honest: I'd rate this 60/40 divert vs partial; surfaced as a Q1 with options + recommendation rather than locking.

2. **The "14-pattern set verbatim" recommendation in Q2 is operationally untested for loam's user base.** ECC has months of pattern-fire data; loam has zero. Recommending verbatim defers the calibration work; this is acceptable for v1 IF the workspace-additions mechanism actually gets exercised and IF the fail-open + log lets us observe false-positive rates. The risk: ship the bundle, never look at the logs, accumulate user friction silently. Mitigation captured to §11 FIDRAFT: review-cadence for the safety-hooks log.

3. **The outcome-altitude ACs (S1/S2/S3) invoke the hooks via subprocess, not via Claude Code's actual PreToolUse dispatch.** This satisfies the letter of `feedback_test_outcome_altitude_required.md` (no pre-arranged state; production entry-point) but does NOT exercise Claude Code's actual hook-firing behavior. The full-fidelity test is S4 (fresh workspace + live `claude` session); that's status-file-recorded smoke, not unit-test. F2: if maintainer wants higher confidence than "subprocess invocation works" pre-ship, dispatch the live-Claude smoke as a build-time owner-gated checkpoint.

4. **Fail-open is the accepted policy but is genuinely a "leak the secret silently if the regex engine faults" path.** The mitigation chain (NDJSON log + audit-block surface + halt-on-fault) is real but operationally depends on the persona surfacing the audit-block AND someone reading it. For a non-tech-user audience this chain may not close. The right belt-not-suspenders framing requires that the user has OTHER defenses (GitHub secret-scanning, git pre-commit hooks). Maintainer should confirm: is this true for loam's target users? If the maintainer's mental model is "loam IS the user's only defense," fail-open is the wrong policy. Recommendation stands as fail-open ONLY if the belt-not-suspenders framing holds; surfaced for explicit confirmation.

5. **The "always-on, toggle via env var" shape doesn't surface to the persona that hooks are disabled.** If a user toggles `LOAM_SAFETY_HOOKS=off`, the persona has no way to know the safety layer is off (env vars don't propagate into the persona's context). The persona may continue to refer to "the safety-layer blocked that" when it actually didn't. AC.SECHK.5's NDJSON log mitigates (audit can find the disabled-record) but doesn't close the loop in real time. F2: consider a session-start surface that reports active hook status to the persona. Captured to §11 FIDRAFT.

6. **The parent absorption plan §10 doubt #4 ("Wave 1 work risks being TOO obvious; why hasn't loam built it already?") applies here.** WI-2 is the highest-value Wave 1 item; the fact loam doesn't already have content-pattern hooks (only file-pattern via bash_guard) suggests prioritization gaps the absorption frame is correcting. F2: this work is valuable and overdue; the only risk is shipping it in a shape that creates more noise than value (mitigated by §5 risk table + §9 halt triggers + fail-open default).

7. **AC.SECHK.S4 is status-file-recorded smoke (not unit-test).** Per `feedback_test_outcome_altitude_required.md` an outcome-altitude AC is satisfied by a test invoking the production entry-point with no pre-arranged state; status-file-recorded smokes satisfy the spirit but are NOT enforceable in CI. The three unit-test outcome-altitude ACs (S1/S2/S3 via subprocess) satisfy the letter for CI; S4 is the cross-cycle confidence-builder. Maintainer should know: if "outcome-altitude in CI" is the requirement, S4 is a complement, not a substitute.

8. **F4 calibration for this plan-doc itself.** §2 ACs are TIGHT (outcome-shaped, deterministic, one-test-per); §4 work decomposition is LOOSE on order/method (per AGENT-PROMPTS-SCOPE-ONLY); §3 fence is TIGHT (exact paths named); §5 risks are MEDIUM (each row carries severity + likelihood + mitigation but the likelihood numbers are estimates, not data). Per F4: the tight/loose mix matches confidence-shape — high on AC outcomes, lower on method, lower on operational data.

---

## §11 — FIDRAFT capture (for maintainer to graduate or discard)

- **F-SAFETY-HOOKS-LOG-REVIEW-CADENCE** — §10 doubt #2: ship the bundle, observe false-positive rate over a steady-state window (~2 weeks?), tighten patterns if needed. Could be a scheduled SKILL on /loop OR a manual quarterly review. Per `feedback_durable_capture_for_planned_work` — captured here; graduate post-Wave-1-ship if maintainer wants the cadence enforced.
- **F-PERSONA-AWARE-HOOK-STATUS** — §10 doubt #5: the persona doesn't know when hooks are toggled off. Session-start context contributor that exports hook status into the persona's runtime context would close the loop. Composes with `framework/primary-persona/` context-contributor surface. Lower-priority than the bundle itself; graduate if/when the gap becomes user-visible.
- **F-LIVE-CLAUDE-OUTCOME-ALTITUDE-SMOKE** — §10 doubt #3: AC.SECHK.S4 is status-file-recorded; a CI-enforceable live-Claude smoke (driving `claude -p` against a fixture, verifying hook-block in stdout) would close the smoke-vs-CI gap. Significant infrastructure work; not in this fence; graduate post-Wave-3 if hooks become higher-stakes.
- **F-HOOK-BUNDLE-AS-INSTINCT-CAPTURE-SEED** — Wave 2 instinct-capture (WI-8) shares the SessionEnd/PreToolUse infrastructure; this work-item's hook scaffolding can inform that one's surface. Cross-reference captured for parent plan §6 sequencing.
- **F-CANONICAL-DEV-SETTINGS-TEMPLATE-HOOK-PARITY** — §3 out-of-fence notes that `framework/hands-off-lifecycle/canonical-dev/settings.dev-template.json` is currently SessionStart-only. Whether canonical-dev should mirror the runtime PreToolUse hooks (so the maintainer's interactive canonical sessions get the same defense as user workspaces) is a separate decision. Captured for separate owner ruling.

---

## §12 — Provenance trail

All citations verified Tier-0 (file-read or git-log on 2026-05-24).

**Maintainer directives:**
- Telegram 12249 (D-SEC.HOOKS ratification — core loam, always-on)
- Telegram 12301 (Wave 1 plan-author dispatch approval, "B" — proceed with recommended bundle)
- Telegram 12242 (non-tech user is the audience — applies to D-SEC.HOOKS rationale)

**Parent plan-doc:**
- `docs/plans/drafts/everything-claude-code-absorption-master-plan.md` — §4 D-SEC.HOOKS (lines 425–444); §5 WI-2 sketch (lines 615–628); §6 Wave 1 sequencing (lines 678–686); §9 halt triggers (line 843); §10 doubts (lines 851–867); §12 provenance.

**Research artifact:**
- `/Users/lukeivers/pos3/workspace/.scratch/claude-output/everything-claude-code-research-2026-05-24.md` (loam-researcher dispatch 2026-05-24) — ECC hooks subsystem section.

**ECC sources (cited in parent plan, verified there):**
- `https://github.com/affaan-m/everything-claude-code/tree/main/hooks` — 14 secret patterns + dangerous flag list + config-file path list. (Cited but not re-fetched in this dispatch; verification deferred to build-time when patterns are transcribed.)

**Loam sources (verified 2026-05-24 via Read/Bash):**
- `/Users/lukeivers/loam/framework/safety-layer/src/loam/safety_layer/__init__.py` — existing public surface; the new hooks are net-new subpackage; no export changes.
- `/Users/lukeivers/loam/framework/safety-layer/docs/architecture.md` — existing architecture; new hooks compose pre-dispatch alongside the SafetyController.
- `/Users/lukeivers/loam/plugins/dev-sdlc/hooks/bash_guard.py` lines 1–80 — existing B1/B2/B3/B4/B5 surface; the divert recommendation in Q1 is grounded in this content.
- `/Users/lukeivers/loam/framework/hands-off-lifecycle/hooks/first_run_settings.py` lines 168–760 — existing `POS_V2_PRETOOLUSE_HOOK_MARKERS` set + `merge_pre_tool_use` helper; the extension shape for new hooks is established.
- `/Users/lukeivers/loam/framework/hands-off-lifecycle/tests/test_AC_OBG_settings_merge.py` lines 26–227 — settings-merge integration test pattern; AC.SECHK.6 follows this shape.
- `/Users/lukeivers/loam/framework/hands-off-lifecycle/canonical-dev/settings.dev-template.json` — current canonical-dev template (SessionStart-only); informs the §3 out-of-fence note.
- `/Users/lukeivers/loam/docs/plans/v0-1-6-production-safety-and-base-skills.md` lines 1–235 — per-work-item plan-doc shape exemplar.
- `/Users/lukeivers/loam/plugins/dev-sdlc/docs/conventions/plan-docs.md` lines 1–69 — plan-doc + manifest authoring conventions.

**Memory rules referenced:**
- `feedback_test_outcome_altitude_required.md` — every AC family carries ≥1 outcome-altitude AC; STUB-class tests don't satisfy them.
- `feedback_scope_descriptive_ac_ids.md` — AC IDs use scope abbreviations (AC.SECHK.*) NOT version-packed.
- `feedback_serialize_amendment_builds.md` — Cycle 1 / Cycle 2 sequencing default.
- `feedback_subagent_odd_violation_halt.md` — halt triggers + §9 source.
- `feedback_dispatch_explicit_loam_amend_apply.md` — `loam amend apply` named in §4 + §7.
- `feedback_record_owner_ratification_before_dispatch.md` — go-order step 1.
- `feedback_summarize_and_surface_decisions.md` — §0 + §8 format.
- `feedback_locked_design_not_license_for_bad_outcomes.md` — D-SECHK.OVERLAP revisit clause.
- `feedback_odd_cdc_scope.md` — dev-CDC scope rationale in Q1 recommendation.
- `feedback_amendment_dispatch_speedups.md` — touched-tests-only band in §4.
- `feedback_duration_estimation_rubric.md` — §7 cost estimate.
- `feedback_durable_capture_for_planned_work.md` — §11 FIDRAFT.
- `feedback_background_agents.md` + `feedback_background_default_for_authoring.md` — §7 go-order step 2.
- `feedback_translate_outbound_too.md` — §0 + §5 + Q4 diagnostic-shape rationale.
- `feedback_dispatch_cd_literal_first_action.md` — §9 halt trigger #1.

**Lens references:**
- L1 Claude-leverage-first — hooks compose with Claude Code's PreToolUse primitive.
- L2 Harness + primary-persona value — non-tech-user-frame strongly favors structural defense.
- L3 ODD authoring — every section maps to named objective; AC outcome-shape verified.
- L4 Prompt scope ↔ confidence — §10 doubt #8 calibration applied.
- L5 Swarming — Cycle 1 / Cycle 2 decomposition has tighter ACs per cycle.
- L6 Principle-conflict resolution — D-SECHK.OVERLAP is a real conflict (divert vs absorb); options + signals named.
- L7 Ruthless Feedback — §10 surfaces 8 honest doubts.

---

## §13 — Authoring trail

Authored 2026-05-24 by `loam-plan-author` subagent, one of 4 parallel Wave 1 plan-author dispatches (others: strategic-compact SKILL graduation, token-defaults opt-in SKILL, README restructure) per dispatcher message Telegram 12301.

Plan-doc ratification: pending. Build dispatches conditional on:
1. Maintainer rules Q1 (D-SECHK.OVERLAP) — divert recommended; alternative options open.
2. Maintainer rules Q2 (D-SECHK.PATTERN-SET) — ECC verbatim + additive recommended.
3. Maintainer rules Q3 (D-SECHK.CYCLE-SHAPE) — confirm two-cycle default.
4. Maintainer implicit-confirms Q4 (fail-open + toggle-granularity + diagnostic-shape) unless objection.

On ratification: this file moves from `docs/plans/drafts/` to `docs/plans/` (per the master plan's draft → ratified convention) + the status field at the top updates to "ratified; build pending"; the ratifying commit becomes the BASELINE for the Cycle 1 manifest.
