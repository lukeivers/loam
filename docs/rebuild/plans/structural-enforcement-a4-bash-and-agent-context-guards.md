# Structural enforcement — A4: Bash/Agent-context guards (PreToolUse Bash + Task refusal-on-{secret,blast-radius,wrong-tree-write,amend-in-subagent-context,pos-amend-dry-run-failure,wrong-WD-dispatch,method-enumerated-prompt,stale-dispatch})

**Status:** authored 2026-04-28 (plan-doc only; no code, no commits, no manifest yet).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Programme:** A4 of the four-amendment structural-enforcement programme — the FINAL gate amendment that closes the programme. A1 substrate sealed at amendment #51; A2 objective-binding gate sealed at amendment #70; A3 TDD-guard sealed at amendment #71; A4 Bash/Agent-context guards is this plan.
**Locked programme research:** `docs/rebuild/plans/research/structural-enforcement-of-critical-requirements-research.md` (2026-04-26).
**A4 research:** `docs/rebuild/plans/research/structural-enforcement-a4-bash-and-agent-context-guards-research.md` (sibling artefact authored alongside this plan).
**Programme-level locks (carried forward, not re-litigated):** D1 dev-discipline carve-outs for `docs/`, `tools/`, `.scratch/`, `CLAUDE*.md`, `personas/`; D2 TDD-guard scoped to re-extension-with-new-AC (out of A4 scope); D3 manifest extends `objective-tracker`; **D4 secret/blast-radius gates UNIVERSAL, ODD-discipline gates DEV-MODE-only** (governs A4 directly — partition table in §6 D-A4.5); D5 KEEP-ADVISORY list of 10.
**Pre-flight verification (mandatory; per `feedback_verify_dispatch_before_sending`):** pre-A4-build dispatch verifies `git log --grep="A4|bash.guard|agent.guard|bash-and-agent"` returns no A4 amendment commit AND `ls docs/rebuild/plans/ | grep -iE "a4|bash.guard|agent.guard"` returns nothing matching `structural-enforcement-a4-*` other than this plan-doc + its sibling research. Halt-and-surface if either does.

---

## 1. Summary / TLDR

A4 is the FINAL structural-enforcement gate. After A2 (Edit/Write/MultiEdit binding) and A3 (Edit/Write/MultiEdit test-pinning), A4 extends the gate pattern to **two new tool surfaces** — `Bash` (every shell command) and `Task` (every Agent dispatch). Both use the same `PreToolUse` hook event A2/A3 use; both deny via the same `permissionDecision: "deny"` shape; both compose against A3's extracted `_gate_helpers.py` library.

A4 is structurally distinct from A2/A3 in three ways:

1. **Two NEW matchers (Bash + Task), not the existing one.** A4 lands two new stanzas in `hooks.PreToolUse`, alongside A2's + A3's stanzas. Each matcher has its own `tool_input` shape and its own decision logic.
2. **Mode-aware partition is non-trivial (programme D4).** Some gate classes are UNIVERSAL (fire in NORMAL USE workspaces too — secret/blast-radius); others are DEV-MODE-only (ODD-discipline). The partition is enforced PER GATE CLASS within each script.
3. **More acceptance criteria.** Bash + Task each cover multiple distinct failure classes; ODD §3.3 (one criterion per behaviour) requires separate ACs for each — 13 ACs total (12 behaviours + seal-diff invariant).

A4 ships:

1. **Bash gate** — `framework/hands-off-lifecycle/hooks/bash_guard.py`. Fires on `PreToolUse` matcher `Bash`. Five failure classes (B1 through B5). Two universal (B2 secret-commit, B5 blast-radius); three DEV-MODE-only (B1 amend-in-subagent, B3 pos-amend-dry-run, B4 wrong-tree-write).
2. **Agent gate** — `framework/hands-off-lifecycle/hooks/agent_guard.py`. Fires on `PreToolUse` matcher `Task`. Three failure classes (T1 wrong-WD dispatch, T2 method-enumerated prompt, T3 stale dispatch). All DEV-MODE-only.
3. **`_gate_helpers.py` extension.** Two new functions for universal-applicable classifiers: `is_secret_commit_command`, `is_blast_radius_command`. Reuse-only of every other helper A3 extracted.
4. **`merge_pre_tool_use` consumer extension.** First-run-helper composes a four-element `[A2, A3, A4_bash, A4_task]` outer list. The marker tuple `_POS_V2_PRE_TOOL_USE_COMMAND_MARKERS` adds two more entries.
5. **Two new audit logs.** `<workspace>/workspace/.pos/bash-guard.log` + `<workspace>/workspace/.pos/agent-guard.log`. NDJSON, atomic-append, append-only in A4 (rotation deferred per FIDRAFT-147).

After A4 lands, every Bash command and every Agent dispatch in pos-v2 (DEV MODE workspaces — and the universal subset in NORMAL USE workspaces too) is structurally checked against the named failure classes. The "no `--amend` in agent context", "no secret commits", "no `rm -rf` outside scratch", "WD must match canonical for pos-v2 dispatches", "no stale re-dispatch of sealed amendments" rules become mechanically enforced — the failure class moves from "review/feedback bullet catches it after the fact" to "the tool call cannot fire without satisfying the gate."

A4 closes the four-amendment programme. The structural-enforcement programme's full shape (substrate + 3 gate matchers covering Edit, Write, MultiEdit, Bash, Task) is observable end-to-end after A4 seals.

Per CLAUDE.md output convention, owner reads from §9 (decisions for owner) — every other section supports it.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Named spec objective this plan satisfies:**

- **`docs/rebuild/spec/pos-v2-objectives-spec.md` line 134–135 — Deterministic (tiered).** Same binding A1+A2+A3 satisfied. A4's gate decisions extend the audit-log surface that line 135-(a) names ("for any decision currently implemented as a rule/prompt where a deterministic hook/script could produce the same outcome, an audit surfaces it"); after A4 lands, the rule inventory's PROMOTE rows (locked programme research §2) are all closed by structural enforcement.
- **VALUE_PROPOSITION's two tests (the prime objective ACs).**
  - *Primary-persona test:* the persona's translation toolkit no longer has to remember "no `--amend` in agent context", "no secret commits", "WD-canonical for pos-v2 dispatches", "verify dispatch isn't stale", "no `cd <ws>/framework && ...`". The substrate refuses these tool calls; the persona doesn't carry the rules. Reduces translation burden directly across 5+ named feedback bullets.
  - *Harness test:* the gate is a reusable harness primitive composed against `_gate_helpers.py`. Two new helper functions (secret-classifier, blast-radius-classifier) become reusable for any future amendment that needs to inspect a Bash command. The gate-decision pattern is now established for two more matcher surfaces (Bash, Task), opening the door for future amendments to extend (e.g., a SubagentStop-hook auditor reusing the same helpers).

**Sealed-component fence (D3 governs):**

- `hands-off-lifecycle` — single sealed component. Two new PreToolUse hook scripts (`bash_guard.py`, `agent_guard.py`); `_gate_helpers.py` extended with two functions; settings-merge marker tuple extended; first-run-helper composition extended; tests for AC.BAG.x + AC.AG.x + AC.A4.S.
- `objective-tracker` — consumer-only. A4's Agent gate calls A1's public read API (`manifest_rows_for_ac`); no schema or runtime change.
- `loam-mode` — consumer-only via the workspace-mode bit (already a `corpus_load_sentinel.workspace_mode()` thin wrapper from A1).

**Single sealed component touched: `hands-off-lifecycle`.** Symmetric with A2's + A3's shape.

**ODD §2.5 reverse direction.** Every code path, branch, dependency, and test in A4's diff traces back to a named AC under §4. No silent branches; no defensive `if`s without backing AC. The two new helper-library functions trace to AC.BAG.1 (secret) + AC.BAG.2 (blast-radius) directly.

---

## 3. Three-lens analysis

### Lens 1 — Claude leverage

*Required research question: what Claude capability does this lean on or extend?*

A4 leans on the same three Claude Code primitives A2 + A3 lean on, plus a fourth:

- **`PreToolUse` hook event.** Claude-native; documented; subagent-inheriting. A4 is the THIRD + FOURTH entries under the same event in the merged settings.json (after A2's Edit|Write|MultiEdit + A3's Edit|Write|MultiEdit). Claude Code admits multiple matcher entries; A4's stanzas are independent (Bash + Task matchers don't overlap with A2/A3's matcher).
- **`Bash` tool matcher.** Claude-native primitive. The `tool_input.command` field carries the literal shell string — A4 inspects via regex.
- **`Task` tool matcher.** Claude-native primitive. The `tool_input.prompt` field carries the dispatch prompt; the envelope's top-level `cwd` carries the parent's working directory (the subagent inherits this).
- **`hookSpecificOutput.permissionDecision: "deny"` + `permissionDecisionReason`.** Native deny mechanism; same as A2/A3.

The substrate (manifest table for stale-dispatch checks, sentinel for subagent-context detection, mode-bit for partition) extends Claude-adjacent infrastructure A1+A2+A3 shipped. A4 is a pure consumer of that substrate at the Claude hook layer, plus the locked-programme-§7.1 finding applied recursively: *"Claude Code's hook surface IS the structural-enforcement surface."* A4 is the third + fourth concrete gate matchers; the same hook surface carries the entire programme.

### Lens 2 — Harness + primary-persona value

*Primary-persona test: does this reduce the translation burden between the user's natural-language intent and AI-effective execution?*

**Yes — direct, load-bearing reduction across multiple feedback bullets.** The persona's translation toolkit currently includes:

- "Never `git commit --amend` in agent context (`feedback_no_amend_in_agent_dispatches`)" — closed by AC.BAG.3.
- "Never commit secrets" — closed by AC.BAG.1 (universally).
- "Never `rm -rf` outside scratch / never `git push --force` to protected branches" — closed by AC.BAG.2 (universally).
- "Always specify WD on agent dispatches (`feedback_always_specify_wd_in_dispatches`)" — closed by AC.AG.1.
- "`pos-amend apply --dry-run` exit-0 BEFORE amendment commit (`feedback_dispatch_explicit_pos_amend_apply`)" — closed by AC.BAG.4.
- "Verify dispatch isn't stale before sending (`feedback_verify_dispatch_before_sending`)" — closed by AC.AG.3.
- "Don't write to `<ws>/framework/` from main session (FIDRAFT-136)" — closed by AC.BAG.5.

Seven distinct rules collapse into structural enforcement. The persona's mental model narrows from "remember N rules and apply per-tool-call" to "the gates enforce the rules at the tool-call boundary." The methodology is preserved for AUTHORING (writing AC text, choosing partition); enforcement is no longer the persona's concern.

*Harness test: does this add to the toolkit the primary persona can draw from?*

**Yes — four new toolkit primitives.**

1. **The Bash-gate-script pattern.** First of its shape; `bash_guard.py` becomes the precedent for any future amendment that needs to inspect Bash commands.
2. **The Task-gate-script pattern.** First of its shape; `agent_guard.py` becomes the precedent for any future amendment that needs to inspect Agent dispatches.
3. **`is_secret_commit_command` + `is_blast_radius_command` helpers.** Universal-applicable classifiers in `_gate_helpers.py`; reusable by any future amendment that audits Bash history (e.g., a SubagentStop hook).
4. **The mode-aware partition pattern within a single gate script.** A4's bash_guard demonstrates how to mix UNIVERSAL + DEV-MODE-only checks in one decision-tree. Future amendments may need the same partition — A4 establishes the shape.

Both Lens 2 tests pass. **→ AC.PO.1 + AC.PO.2.**

### Lens 3 — ODD authoring

A4 is structurally shaped, not advisory. Each gate is deterministic — same Bash command + same workspace-mode = same decision, every fire. The refusal is structured (`permissionDecision: "deny"`), the diagnostic is named (the `permissionDecisionReason` enumerates the failure class + the repair), the audit is captured (two NDJSON logs).

Every AC below is outcome-shaped (no "the implementation will use X" language). Method (regex patterns for secret/blast-radius detection, decision-tree shape, exact carve-out interaction, env-var override name, prompt-pattern detection regex for T3) is the builder's call and lives in the builder plan.

ODD §5.1.1 (relocate-vs-eliminate test): A4 ELIMINATES the named failure classes. A future code change cannot re-introduce the failures without active discipline (i.e., without amending or removing A4 itself). The gate's refusal shape is structural, not an `if/else` a maintainer can forget to update.

ODD §3.3 (one criterion per behaviour): each Bash failure class (B1, B2, B3, B4, B5) and each Task failure class (T1, T2, T3) gets its own AC. Bundling B1+B2+B5 into "AC.BAG.bash-deny" is forbidden — different decision data, different mode partition, different reason text.

---

## 4. Acceptance criteria

A4's outcome is the gates' observable behaviour at every PreToolUse Bash + Task fire. Twelve behaviours + seal-diff invariant = **13 ACs**.

Per programme D4 + the partition recommendation in D-A4.5, ACs are tagged UNIVERSAL or DEV-MODE-only.

### Bash gate (5 failure classes)

- **AC.BAG.1 — Bash gate denies secret-file commit (UNIVERSAL).** Given a `Bash` tool call whose `tool_input.command` matches a secret-commit pattern (the command invokes `git add`, `git commit`, or `git stash` in a way that includes a path matching the secret-file regex family — `\.env(?:\..+)?$` excluding `\.env[.-]example$`, `credentials\.json$`, `\.aws/credentials$`, `.*\.pem$`, `.*\.key$`, `id_rsa$`, `id_ed25519$`, plus a curated extensible list): hook returns `hookSpecificOutput.permissionDecision: "deny"` with a `permissionDecisionReason` that names (a) the matched paths, (b) the secret-class detected, (c) at least one repair direction (rename to `.env-example`, add to `.gitignore`, halt and surface). Fires regardless of workspace mode. The env-var override `POS_BASH_GUARD_ALLOW=1` does NOT bypass this gate.

- **AC.BAG.2 — Bash gate denies blast-radius destructive command (UNIVERSAL).** Given a `Bash` tool call whose `tool_input.command` matches a blast-radius pattern from a curated deny-list — at minimum: `git push --force` (or `--force-with-lease`) to `pos-v2`/`main`/`master`; `rm -rf <path>` where the resolved path is OUTSIDE `<workspace>/.scratch/` AND OUTSIDE `/tmp/`; `chmod -R (777|0)` against `~` or workspace root; `dd if=.* of=/dev/.*`; `curl <url> | (bash|sh)` / `wget <url> | (bash|sh)`: hook returns `permissionDecision: "deny"` with reason naming the matched class + the matched substring + at least one repair direction (use `.scratch/` for ephemeral deletes, use `git push` without force, save the curl output to a file and inspect first). Fires regardless of workspace mode. The env-var override `POS_BASH_GUARD_ALLOW=1` does NOT bypass this gate.

- **AC.BAG.3 — Bash gate denies `git commit --amend` in subagent context (DEV-MODE-only).** Given workspace-mode = `dev-mode`, given an active-scope sentinel is present (proxy for "this is a subagent build context"), given the `tool_input.command` matches `git commit\s+(.*\s+)?--amend` (anywhere in the command, including pipes/heredocs): hook returns `permissionDecision: "deny"` with reason naming the rule (`feedback_no_amend_in_agent_dispatches`), the sentinel state, and at least one repair direction (author a new corrective commit instead; if main-session intentional amend, remove the sentinel or use `POS_BASH_GUARD_ALLOW=1`). NORMAL USE workspaces no-op this check.

- **AC.BAG.4 — Bash gate denies amendment-shape commit when `pos-amend apply --dry-run` would fail (DEV-MODE-only).** Given workspace-mode = `dev-mode`, given the `tool_input.command` matches a sealed-amendment commit pattern (`git commit\s+-m\s+["'](feat|fix|chore|seal)\([\w-]+\)`): the hook invokes `pos-amend apply --dry-run <manifest>` against the canonical manifest set; on exit ≠ 0, hook returns `permissionDecision: "deny"` with reason that includes the dry-run's stderr/stdout output + at least one repair direction (fix the manifest, run `pos-amend apply` to advance BASELINE, retry). Method per ODD §7.4: the manifest discovery (which `<plan>.manifest.yaml` to dry-run against) is the builder's call — candidate strategies include reading the active-scope sentinel's `plan_path` + deriving the manifest path, OR walking `docs/rebuild/plans/*.manifest.yaml` and filtering by current-branch state. NORMAL USE workspaces no-op this check.

- **AC.BAG.5 — Bash gate denies wrong-tree-write via `cd <ws>/framework && <write>` (DEV-MODE-only).** Given workspace-mode = `dev-mode`, given the `tool_input.command` contains a `cd` clause whose target resolves to `<workspace>/framework/` OR `<workspace>/framework/<subdir>` AND the command's subsequent action is a write (`git commit`, `git apply`, `git restore`, `>` redirect, `tee`, `sed -i`, etc.) AND the target path is NOT in the dev-discipline carve-out (per `_gate_helpers.is_carve_out_path`): hook returns `permissionDecision: "deny"` with reason naming the failure (FIDRAFT-136 main-session-write-prevention) + the canonical pos-v2 path as the right target + at least one repair direction (redirect the command to operate inside canonical pos-v2; if the workspace IS canonical, the gate doesn't fire — this case fires only against mirror trees). NORMAL USE workspaces no-op this check. The env-var override `POS_BASH_GUARD_ALLOW=1` bypasses this gate (operator-trusted triage).

### Bash gate envelope

- **AC.BAG.6 — Bash gate is no-op for non-targeted commands (UNIVERSAL behavior — applies to non-matching commands in any mode).** Given a `Bash` tool call whose `tool_input.command` matches none of the AC.BAG.1..AC.BAG.5 patterns: hook returns no `permissionDecision` (default-allow). Cheap path: the hook's wall-clock cost is bounded by the regex sweep (sub-millisecond p95 for typical commands; bounded by the regex deny-list size).

- **AC.BAG.7 — Every Bash gate fire is observable through a deterministic audit surface.** Each PreToolUse Bash fire (allow + deny + no-op + error) is recorded in a workspace-local audit surface that a downstream consumer can read deterministically. The recorded data is sufficient to reconstruct: when the fire happened, the matched command (or "no-match"), workspace mode, sentinel state (when DEV-MODE-only check fires), the gate's decision, and (on deny) the same reason text the model received + the failure class + the matched pattern. The surface is append-only; concurrent fires across processes do not corrupt each other (atomicity guarantee). Path, format, and exact field names are method per ODD §7.4 — the builder confirms the shape composes with A2's + A3's audit-log shape (sibling format from `_gate_helpers.append_audit_line`).

### Agent gate (3 failure classes)

- **AC.AG.1 — Agent gate denies wrong-WD dispatch (DEV-MODE-only).** Given workspace-mode = `dev-mode`, given a `Task` tool call whose `tool_input.prompt` mentions pos-v2 surfaces (the prompt contains at least one of: `docs/rebuild/`, `framework/<comp>/src/` or `framework/<comp>/tests/` patterns, the literal `pos-amend`, the literal "seal commit", the literal canonical path `/Users/lukeivers/ivers-corp-pos-v2/`, OR an amendment-shape pattern `amendment #\d+`), given the envelope's top-level `cwd` does NOT match the canonical pos-v2 path: hook returns `permissionDecision: "deny"` with reason naming (a) the detected pos-v2 surface mentions, (b) the wrong cwd, (c) the canonical path the dispatch should target, (d) at least one repair direction (re-dispatch with `cwd` set to canonical, or strip the pos-v2 surface mentions if dispatch is intentionally for a derived workspace). NORMAL USE workspaces no-op this check.

- **AC.AG.2 — Agent gate denies method-enumerated prompt above length threshold (DEV-MODE-only).** Given workspace-mode = `dev-mode`, given a `Task` tool call whose `tool_input.prompt` length exceeds **2500 characters**: hook returns `permissionDecision: "deny"` with reason naming the rule (`feedback_agent_prompts_scope_only` — scope-only-dispatch CDC), the prompt length, and at least one repair direction (extract method-enumerated content into the plan-doc; the dispatch's job is scope+constraints+halt+ODD-check, not file/symbol/AC enumeration). The length threshold (2500) is named in this AC (not method per ODD §7.4 — auditable threshold). NORMAL USE workspaces no-op this check.

- **AC.AG.3 — Agent gate denies stale dispatch re-targeting an already-sealed amendment (DEV-MODE-only).** Given workspace-mode = `dev-mode`, given a `Task` tool call whose `tool_input.prompt` mentions an amendment number (matches `amendment #(\d+)`) OR an AC ID (matches `AC\.\w+\.\w+`), given the manifest table OR git history shows the named amendment/AC has already sealed (manifest row present for the AC AND/OR a seal commit grepable by `chore(seals).*amendment #N` exists): hook returns `permissionDecision: "deny"` with reason naming (a) the detected stale reference, (b) the seal commit SHA when known, (c) at least one repair direction (re-target a different amendment, surface the staleness to the dispatcher). Fail-closed-to-permissive at the manifest-import boundary: tracker unreachable → fall through to allow (mirror A2's R7). NORMAL USE workspaces no-op this check.

### Agent gate envelope

- **AC.AG.4 — Agent gate is no-op for non-targeted dispatches (UNIVERSAL behaviour — applies regardless of mode for unmatched dispatches).** Given a `Task` tool call whose prompt matches no AC.AG.1..AC.AG.3 pattern (or workspace-mode is `normal-use` for DEV-MODE-only checks): hook returns no `permissionDecision`. Cheap path: bounded by the regex sweep + mode-bit read.

- **AC.AG.5 — Every Agent gate fire is observable through a deterministic audit surface.** Each PreToolUse Task fire (allow + deny + no-op + error) is recorded in a workspace-local audit surface (separate from AC.BAG.7's Bash-gate log). Mirrors AC.BAG.7's contract (sufficient to reconstruct fire, decision, failure class on deny, audit-log path is method per ODD §7.4).

### Settings + Seal

- **AC.A4.settings_merge — Multi-contributor merge admits A2+A3+A4_bash+A4_task.** Given A2's stanza + A3's stanza + A4_bash's stanza + A4_task's stanza: `merge_pre_tool_use(new_entries=[a2, a3, a4_bash, a4_task])` writes the four-element outer list under `hooks.PreToolUse`. Re-merge over a pos-v2-owned four-element outer list (every inner-hook command matches a recognised pos-v2 marker — `objective_binding_gate.py`, `tdd_guard.py`, `bash_guard.py`, `agent_guard.py`) does not back up. User-authored stanzas continue to be preserved via the `_USER_AUTHORED` backup convention (regression contract for A2's existing settings-merge tests + A3's multi-contributor extension).

- **AC.A4.S — Seal-diff confined to fence.** A4's seal-diff window contains only edits under `framework/hands-off-lifecycle/{hooks,tests,seals}/` and the universal-paths admissions (`docs/rebuild/plans/`, `CLAUDE.md`, `docs/odd-methodology.md`, `docs/odd-in-pos.md`, `docs/rebuild/FUTURE_IDEAS.md`, `docs/rebuild/FUTURE_IDEAS_DRAFT.md`). Per-invariant frozen-both-endpoints BASELINE pattern (per `docs/odd-in-pos.md` §10.3) for the A4 invariant test.

### Behaviour-count check (forward)

| # | Declared behaviour in §1 / §4 | AC | Mode |
|---|---|---|---|
| 1 | Bash gate denies secret-file commit | AC.BAG.1 | UNIVERSAL |
| 2 | Bash gate denies blast-radius destructive command | AC.BAG.2 | UNIVERSAL |
| 3 | Bash gate denies `--amend` in subagent context | AC.BAG.3 | DEV-MODE-only |
| 4 | Bash gate denies amendment-shape commit when dry-run fails | AC.BAG.4 | DEV-MODE-only |
| 5 | Bash gate denies wrong-tree-write via `cd <ws>/framework && ...` | AC.BAG.5 | DEV-MODE-only |
| 6 | Bash gate is no-op for non-matching commands | AC.BAG.6 | — |
| 7 | Bash gate audit log per fire | AC.BAG.7 | — |
| 8 | Agent gate denies wrong-WD dispatch | AC.AG.1 | DEV-MODE-only |
| 9 | Agent gate denies method-enumerated prompt above 2500-char threshold | AC.AG.2 | DEV-MODE-only |
| 10 | Agent gate denies stale dispatch re-targeting sealed amendment | AC.AG.3 | DEV-MODE-only |
| 11 | Agent gate is no-op for non-matching dispatches | AC.AG.4 | — |
| 12 | Agent gate audit log per fire | AC.AG.5 | — |
| 13 | Multi-contributor settings merge | AC.A4.settings_merge | — |
| 14 | Seal-diff confinement | AC.A4.S | — |

**Behaviours = 14, ACs = 14.** Match. (12 substantive behaviours + 2 invariants = 14 ACs; ODD §3.3 satisfied.)

### Behaviour-count check (reverse)

The reverse direction (every code path / branch / dep / test in the diff traces back to AC.BAG.x / AC.AG.x / AC.A4.x) is exercised in the builder plan's §2.5 reverse-direction audit at build time. This plan asserts the audit will run; the builder records its outcome.

---

## 5. Hard constraints

1. **Dependency fence.** Source-edit scope: `framework/hands-off-lifecycle/{hooks,tests,seals}/`. Any edit to other sealed components is a halt trigger. Non-fence consumer reads (`objective-tracker.runtime.ObjectiveTracker.manifest_rows_for_ac`, `loam-mode` via `corpus_load_sentinel.workspace_mode()`) are READ-ONLY; if a write or schema extension surfaces necessary, that's an A4.1 corrective on A1's substrate (forbidden — see constraint 12).
2. **A2/A3 contracts are sealed.** A4 may not propose edits to A2's `objective_binding_gate.py` evaluate function signature, A2's audit-log shape, A3's `tdd_guard.py` evaluate function signature, A3's audit-log shape, or any of A1's read APIs. The `_gate_helpers.py` library is EXTENDED in-place by adding two new functions; no existing helper symbol is renamed, removed, or signature-changed.
3. **Reversibility.** Fully reversible. The new gates are additive: two new hook scripts, two new settings.json entries, two new audit log files. Removing the entries restores prior behaviour (A2 + A3 still fire as today).
4. **Budget.** Bash gate < 50ms p95 (target < 10ms — fires per shell command; latency compounds across a build's command-burst). NORMAL USE branch < 5ms (regex + mode-bit). Universal-only matches (B2 + B5 fire even in NORMAL USE) < 2ms (regex sweep only). Task gate < 100ms p95 (target < 50ms — fires per dispatch, including manifest query for T3). NORMAL USE branch < 5ms. Cumulative A2 + A3 + A4 hook-chain budget for Edit/Write/MultiEdit unchanged (~200ms p95). Bash chain runs only A4_bash; Task chain runs only A4_task.
5. **Fail-closed direction (DEV MODE).** All DEV-MODE-only checks deny on positive match; the env-var override `POS_BASH_GUARD_ALLOW=1` admits B1, B3, B4 only — NOT B2 or B5 (universal blast-radius/secret).
6. **Fail-open direction at substrate-import boundary.** Tracker unreachable → AC.AG.3 falls through to allow (mirrors A2's R7 + A3's constraint 7). Mode-bit unreadable → fail-closed-to-permissive (`normal-use`), which means DEV-MODE-only checks short-circuit; UNIVERSAL checks fire regardless. **This direction is correct:** universal checks are user-protective; the failure mode is "unreadable substrate falls back to most-permissive for ODD-discipline + most-protective for blast-radius/secret."
7. **No `--amend`.** Corrective commits only (per `feedback_no_amend_in_agent_dispatches`).
8. **ODD §2.5.** Every code path, branch, dependency, and test in A4's diff traces back to AC.BAG.1–AC.BAG.7 + AC.AG.1–AC.AG.5 + AC.A4.settings_merge + AC.A4.S. The builder runs the §2.5 reverse-direction audit before seal — including the `_gate_helpers.py` extension (the two new functions trace to AC.BAG.1 + AC.BAG.2 directly).
9. **No new top-level objective.** A1+A2+A3 already satisfied spec line 134–135; A4's audit logs feed the same lint surface. No spec amendment.
10. **No method prescription.** This plan-doc names outcomes; the builder plan picks: hook script structure, decision-tree shape, exact secret-file regex list, exact blast-radius regex list, env-var override naming, dry-run manifest-discovery strategy (AC.BAG.4), prompt-pattern detection regex for T3, stale-amendment query strategy (manifest-only vs git-log-fallback), JSON keys for the deny reason and audit log, multi-contributor merge marker tuple ordering. The 2500-char threshold for AC.AG.2 IS named (not method per ODD §7.4 — auditable).
11. **A1 + A2 + A3 substrate is sealed.** A4 may not propose edits to A1's manifest schema, sentinel JSON shape, mode-bit interface, A1's reader/writer contracts, A2's evaluate function, A2's audit-log shape, A3's evaluate function, A3's audit-log shape, or `_gate_helpers.py`'s existing function signatures. The library is EXTENDED only (two new functions added at module-level; existing symbols untouched).
12. **Backwards-compat.** Existing PreToolUse hooks (A2's gate + A3's gate + user-authored entries) must be preserved. The multi-contributor merge surface generalises naturally; A2's existing `test_AC_OBG_settings_merge.py` + A3's `test_AC_TDG_settings_merge.py` continue to pass byte-for-byte (regression contract).
13. **No agent-side discipline-as-code.** A4 must not require build agents or the persona to "remember to call the gate" — the gates ARE the discipline. The dispatcher / build-agent learns from the deny diagnostic.
14. **Sealed-component dispatch must explicitly name `pos-amend apply`** as the bookkeeping mechanism for the seal-diff window per `feedback_dispatch_explicit_pos_amend_apply`.
15. **Build-time AC-row registration is a hard prereq (inherited from A2/A3).** The build agent's first action (before the first source edit) is registering manifest rows for AC.BAG.1–AC.BAG.7 + AC.AG.1–AC.AG.5 + AC.A4.S via `tracker.register_source_binding(component="hands-off-lifecycle", ac_id="AC.BAG.x" / "AC.AG.x" / "AC.A4.x", source_path_glob="framework/hands-off-lifecycle/...")`. Without this, A2's gate denies the first source edit (chicken-and-egg). Bootstrap order: (a) register manifest rows; (b) author A4's tests first (A3's gate admits new ACs only when test exists); (c) THEN author A4's source files (`bash_guard.py`, `agent_guard.py`, `_gate_helpers.py` extensions, settings + first-run-helper extensions).
16. **Audit-log paths follow D-migration D.2 convention.** `<workspace>/workspace/.pos/bash-guard.log` + `<workspace>/workspace/.pos/agent-guard.log` (NOT `<workspace>/.pos/`). Builder confirms by inspecting `framework/workspace-bootstrap/src/workspace_bootstrap/workspace_paths.py` at build time — the canonical `WORKSPACE_STATE_SUBDIR` = `"workspace"`.
17. **Mode-aware partition is enforced PER GATE CHECK, not per script.** Each gate script's first action is the mode-bit read; UNIVERSAL checks (B2, B5) fire BEFORE the partition gate; DEV-MODE-only checks fire AFTER the partition. This is the partition pattern; A4 establishes it for future amendments.
18. **Env-var override `POS_BASH_GUARD_ALLOW=1` admits ONLY B1, B3, B4.** AC.BAG.1 + AC.BAG.2 explicitly enumerate the no-override property; the implementation must verify this in tests.

---

## 6. D-decisions for this plan (record + rationale)

The five programme-level D-decisions are LOCKED 2026-04-26 (see header). This section records the A4-level design choices that follow from the research artefact + the programme locks. **Owner is asked to rule on D-A4.1 through D-A4.8 below; D-A4.9 + D-A4.10 are method per ODD §7.4.** Decisions for owner are summarised in §9 (read this first).

### D-A4.1 — Firing layer

**Recommendation: Candidate A — `PreToolUse` matchers `Bash` + `Task` (two stanzas).** Mirrors A2/A3 architecturally; native Claude primitive; subagent-inheriting. Rejected: B (single multi-tool stanza — conflates four decision-logics; ODD §5.1 violation), C (PostToolUse for B3 — relocate-not-eliminate per ODD §5.1.1), D (`.git/hooks/pre-commit` for B3 — outside the canonical structural-enforcement surface per locked programme research §7.1).

### D-A4.2 — Refusal mechanism

**Recommendation: Candidate α — `permissionDecision: "deny"` + structured `permissionDecisionReason`.** Mirrors A2/A3. No deviation.

### D-A4.3 — Bash hook script layout

**Recommendation: single `bash_guard.py` script handling all five Bash failure classes (B1–B5).** Internal mode-bit branch + UNIVERSAL-vs-DEV-MODE partition is cheap (~microseconds); splitting forces two settings.json entries + two audit logs + two deny-message styles. Bundling is structural here (one gate, one decision-tree, one matcher); Bash + Task ARE structurally different (different `tool_input` shape — different gates).

### D-A4.4 — Task hook script layout

**Recommendation: single `agent_guard.py` for T1+T2+T3.** Same rationale as D-A4.3.

### D-A4.5 — Universal-vs-DEV-MODE partition table (HIGH-STAKES)

**Recommendation:**

| Class | Description | Mode | Rationale |
|---|---|---|---|
| B1 | `git commit --amend` | DEV-MODE-only + sentinel-present | Main-session amend is legitimate; DEV-MODE-only avoids false-deny |
| B2 | Secret-file commit | UNIVERSAL | Irreversible blast radius |
| B3 | `pos-amend apply --dry-run` commit gate | DEV-MODE-only | pos-v2-bookkeeping rule |
| B4 | Wrong-tree-write `cd <ws>/framework` | DEV-MODE-only | Workspace-mode-specific |
| B5 | Blast-radius destructive | UNIVERSAL | Mass-destructive class |
| T1 | Wrong-WD dispatch | DEV-MODE-only | pos-v2-dev-specific |
| T2 | Method-enumerated prompt (length) | DEV-MODE-only | pos-v2-dev CDC |
| T3 | Dispatch-staleness | DEV-MODE-only | Manifest substrate is pos-v2-only |

**Caveat:** if owner reclassifies any class (e.g., "block --amend universally"), the corresponding AC reshapes.

### D-A4.6 — Override mechanism for DEV-MODE-only Bash gates

**Recommendation: env var `POS_BASH_GUARD_ALLOW=1`.** Cheapest correct shape; per-session; no persistent state. Admits ONLY DEV-MODE-only checks (B1, B3, B4); UNIVERSAL checks (B2, B5) are NOT bypassable. Hard constraint 18 enforces the property.

**Alternatives:** sentinel file (more state to manage); no override (operator can't triage). Env var is the locked programme research's named pattern for B1.

### D-A4.7 — Length threshold for T2 (method-enumerated prompt)

**Recommendation: 2500 characters.** Locked programme research §2 row 5 named threshold. Most well-formed scope-only-dispatch prompts are 1000–2200 chars; the threshold catches 3000+ method-enumerated outliers. **The threshold is NAMED in AC.AG.2** (auditable, not method per ODD §7.4).

### D-A4.8 — T3 detection method

**Recommendation: union of (a) amendment-number regex + manifest table query AND (b) AC-id regex + manifest table query AND (d) git-log-fallback when manifest doesn't return the named row.** The two regex patterns catch different writing styles; the git-log fallback admits stale-dispatch detection even when the manifest is mid-bootstrap on a fresh workspace. Rejected: (c) "AC-id only" — misses dispatches that name an amendment but no AC; (d-only without manifest) — reintroduces the brittleness D3 chose to avoid.

### D-A4.9 — Audit-log shape (method per ODD §7.4)

**Default:** NDJSON at `<workspace>/workspace/.pos/bash-guard.log` + `<workspace>/workspace/.pos/agent-guard.log` mirroring A2's + A3's `objective-binding-gate.log` + `tdd-guard.log` pattern. Atomic-append via POSIX `O_APPEND`. Append-only in A4; rotation deferred to a future amendment (FIDRAFT-147).

### D-A4.10 — Secret + blast-radius regex deny-list (method per ODD §7.4)

**Default:** built-in regex deny-list curated by the builder. AC.BAG.1 + AC.BAG.2 name the failure class but not the exact regex; the builder plan records the exact patterns + carve-outs (e.g., `\.env[.-]example` admitted; `<workspace>/.scratch/**` admitted under `rm -rf`). The deny-list is extensible by future amendments; A4 ships the curated minimal set named in this plan + research §1.1, §4.

---

## 7. Out of scope (explicit per ODD §2.5)

A4 is the FINAL gate amendment in the programme. Items below are explicitly NOT in A4's surface.

- **PostToolUse hooks for any of the failure classes.** A4 fires PRE; once a Bash command executes, the deny window has closed.
- **Bash command AST parsing.** A4 uses regex over `tool_input.command`. AST-shaped command parsing (handling shell-escaping, command substitution, eval edge cases) is out of A4 scope. If regex false-positive rate becomes load-bearing, a future amendment may extend.
- **MCP tool gates.** A4 does not gate `mcp__<server>__<tool>` matchers. A future amendment may extend to specific MCP tools (e.g., the Telegram-reply tool may want a "no leakage of internal narration" gate).
- **WebFetch / WebSearch gates.** Distinct surface; out of A4. A future amendment may add (e.g., a "deny WebFetch when prompt mentions credential exfiltration" classifier).
- **NotebookEdit gate.** Same matcher family as Edit/Write but distinct envelope; A2+A3 don't cover it; A4 doesn't either. Future amendment territory.
- **`SubagentStop` hook auditing.** A4 covers the dispatch (PreToolUse Task) but not the agent's final report. A future amendment may add Stop-hook contributors that audit final reports for halt-and-surface markers (rule 9 in the programme inventory; programme deferred per "🔴 — phrasing-detection is unreliable").
- **Direction-B test-without-implementation refusal.** Distinct surface from A3 + A4 per FIDRAFT line 145; A4 does not gate the test-without-impl direction.
- **Test-deletion gate.** Per FIDRAFT line 149 — Bash `rm` of test files is destructive but differs from secret/blast-radius. Out of A4 scope.
- **Audit-log rotation.** Per FIDRAFT line 147. A4 inherits A2+A3's deferral.
- **Cross-amendment manifest queries / observability dashboards.** A4 ships per-fire NDJSON logs; reporting consumers are downstream amendments.
- **Helper-library expansion beyond what A4 needs.** Adding helpers a future amendment might want but A4 doesn't is out of A4 scope.
- **Settings.json migration on existing workspaces.** A4's first-run-helper wires the new PreToolUse stanzas into freshly-bootstrapped workspaces. Existing workspaces' settings.json files may need a re-merge pass; the existing `merge_user_prompt_submit` / `merge_session_start` / `merge_pre_tool_use` precedent handles this for re-bootstrap (the amendment #45/#46/A2/A3 pattern). The builder confirms re-merge is idempotent.
- **Persona-side surfacing of A4 deny diagnostics.** The model receives `permissionDecisionReason` natively. A4 does not include persona-prompt edits.
- **Composition with FIDRAFT-130 corpus-inlining.** Distinct surface.
- **Composition with FIDRAFT-151 dispatcher-side test-stub authoring.** Adjacent (both touch dispatch wrapper); A4 ships only the gate, not the auto-stub authoring.
- **`pos-amend` in-progress detection (B3 enrichment).** AC.BAG.4 invokes `pos-amend apply --dry-run`. A future enrichment could detect pos-amend already in-progress (lockfile present) and short-circuit. Out of A4.
- **Programme A5 (any future structural-enforcement amendments).** A4 closes the named programme. Future amendments are scoped fresh.

---

## 8. Halt triggers

Halt and surface (do not silently extend) when any of the following fires:

1. **A1 substrate gap.** If A4's design surfaces a missing field A1 doesn't provide → halt; A1.1 corrective. Specifically: if `manifest_rows_for_ac` doesn't return rows in a shape A4 needs for T3; if the active-scope sentinel reader doesn't expose `bindings`/`scope_id`/`created_at` the way A4's evaluate functions consume; if `workspace_mode` doesn't expose the two-string contract A4 expects. Verification at build start by re-reading A1 readers against A4's needs.

2. **A2/A3 helper incompatibility.** If `_gate_helpers.py` cannot be extended with `is_secret_commit_command` + `is_blast_radius_command` without breaking A2's or A3's existing imports → halt. Specifically: if the import order changes the lazy-import pattern; if signature-shape conflicts arise; if test fixtures monkey-patch paths invalidate. Verification: dry-run the helper extension before authoring A4's gates.

3. **MultiEdit semantics changed.** A2/A3's empirical answer (single `file_path` at top-level) is for Edit/Write/MultiEdit; A4's matcher set is Bash/Task. If `tool_input.command` for Bash or `tool_input.prompt` + envelope `cwd` for Task differs from documented shape, halt.

4. **Existing PreToolUse hook collision.** Settings.json now has FOUR pos-v2-owned PreToolUse entries (A2 + A3 + A4_bash + A4_task) plus user-authored entries. The multi-contributor merge must preserve user state byte-for-byte; if the marker tuple extension breaks A2's/A3's existing `*_settings_merge.py` tests, halt.

5. **Surrounding-code ODD §2.5 violation.** The hook scripts' adjacent modules (`first_run_settings.py`, `first_run_helper.py`, `_gate_helpers.py`) may contain pre-existing §2.5 violations the build's verification pass uncovers — particularly during the helper-library extension. Halt-and-surface per the dispatch's explicit ODD-violation clause.

6. **Outcome-resistant AC.** If during builder plan authoring some A4 behaviour resists outcome-shaping (a method prescription is the only natural form), halt and signal. Specifically: AC.BAG.4's "manifest discovery strategy" is method per ODD §7.4 (named); but if the discovery surfaces a substrate gap (no canonical way to map active scope → manifest path), halt.

7. **Architecture creep — multi-tenant gate framework.** If during build the builder concludes a single multi-tenant gate framework dispatcher (rather than per-amendment hooks with shared helpers) is the right shape, halt — the locked programme research + A2/A3 research + A4 research all recommend per-amendment hooks. The default in this plan is per-matcher hooks with shared `_gate_helpers.py`.

8. **Architecture creep — hook-chain ordering across 5 matchers.** With Edit/Write/MultiEdit (A2 + A3 stanzas) + Bash (A4_bash) + Task (A4_task), `hooks.PreToolUse` carries four entries with two distinct matcher sets. If during build the builder discovers Claude Code's matcher merge semantics behave differently than A2's empirical answer (matcher entries are independent; sequential evaluation within a matcher; cross-matcher non-interference), halt — the assumption is load-bearing for AC.A4.settings_merge.

9. **D-A4.5 partition contradiction.** If during build a Bash command class surfaces that doesn't cleanly fit UNIVERSAL or DEV-MODE-only — e.g., `git checkout main` from a subagent context — halt and signal back to owner. The default in this plan covers the named eight classes (B1–B5 + T1–T3); novel classes need explicit ruling.

10. **Override mechanism abuse risk.** If during build the env-var override for B1/B3/B4 (D-A4.6) surfaces as a vector for B2/B5 bypass through a parsing edge case, halt — hard constraint 18 forbids the override admitting universal blast-radius/secret checks.

11. **Substrate-fence breach.** Per constraint 1: any source-edit need outside `framework/hands-off-lifecycle/{hooks,tests,seals}/` halts. Specifically: any edit to `framework/objective-tracker/`, `framework/loam-mode/`, or any other sealed component → halt.

12. **AC.OBG.x / AC.TDG.x regression in A4's diff.** The `_gate_helpers.py` extension and the multi-contributor `merge_pre_tool_use` extension could subtly affect A2 or A3 behaviour. Halt if any AC.OBG.x or AC.TDG.x test fails post-A4-build; this is the regression contract.

13. **Self-bootstrap fails.** Per hard constraint 15: the build agent's bootstrap order (manifest rows first, A4 tests second, A4 source third) must be followed. If the agent's own first source edit fails A2/A3 (e.g., manifest rows missing from chicken-and-egg, or test files for AC.BAG.x absent), halt — A4's own build is structurally blocked.

14. **Dispatch staleness (meta — A4's own dispatch).** The pre-flight named in the header catches A4-already-shipped scenarios. If §14 below contains commit SHAs at dispatch time, halt.

15. **Tool-name divergence.** If verification at build start reveals Claude Code's actual matcher tool name for Agent dispatch is `Agent` not `Task` (or vice versa), halt — the matcher in the settings stanza must be exactly correct.

---

## 9. Decisions for owner (only genuinely uncertain)

The five programme-level D-decisions are LOCKED 2026-04-26 (see header) and not surfaced here. **Eight decisions are surfaced for owner ruling**, with recommendation per `feedback_summarize_and_surface_decisions`:

### D-A4.1 — Firing layer

- **Question:** PreToolUse Bash + Task matchers (Candidate A) vs alternatives B/C/D.
- **Recommendation:** **Candidate A.** Mirrors A2/A3; native Claude primitive; subagent-inheriting.
- **Caveat:** if owner picks anything else, every AC reshapes.

### D-A4.2 — Refusal mechanism

- **Question:** `permissionDecision: deny` + structured reason (Candidate α) vs alternatives.
- **Recommendation:** **Candidate α.** No deviation from A2/A3.

### D-A4.3 — Bash hook script layout

- **Question:** single `bash_guard.py` for B1–B5, OR split universal/DEV-MODE.
- **Recommendation:** **single script.** Internal partition is cheap; bundling is structural here.

### D-A4.4 — Task hook script layout

- **Question:** single `agent_guard.py` for T1–T3, OR split per failure class.
- **Recommendation:** **single script.** Same rationale as D-A4.3.

### D-A4.5 — Universal-vs-DEV-MODE partition table (HIGH-STAKES)

- **Question:** which Bash + Task failure classes fire UNIVERSALLY (NORMAL USE workspaces too) vs DEV-MODE-only.
- **Recommendation:** UNIVERSAL = B2 (secret-commit) + B5 (blast-radius). DEV-MODE-only = B1 (amend), B3 (pos-amend dry-run), B4 (wrong-tree-write), T1 (wrong-WD), T2 (length), T3 (staleness).
- **Why:** secret leakage + mass-destructive commands are user-protective regardless of workspace; everything else is pos-v2-dev-specific where DEV-MODE bit gates correctly.
- **Caveat:** if owner reclassifies any class, the corresponding AC reshapes. The most likely reclassification: B1 → UNIVERSAL (block --amend in any subagent context, not just DEV MODE) — defensible if the operator never amends in derived workspaces.

### D-A4.6 — Override mechanism for DEV-MODE-only Bash gates

- **Question:** how does the operator bypass B1/B3/B4 for legitimate triage workflows?
- **Recommendation:** **env var `POS_BASH_GUARD_ALLOW=1`** scoped to the parent shell. Admits ONLY B1/B3/B4 — UNIVERSAL checks (B2, B5) are NOT bypassable.
- **Why:** cheapest correct shape; programme research's named pattern; structural (gate reads env var deterministically); no persistent state.
- **Alternatives:** sentinel file (more state to manage); no override (operator can't triage). Env var is recommended.

### D-A4.7 — Length threshold for T2 (method-enumerated prompt)

- **Question:** prompt-length threshold above which the Task gate denies for "method-enumerated dispatch" (CDC: scope-only-dispatch).
- **Recommendation:** **2500 characters.** Locked programme research §2 row 5 named.
- **Why:** most well-formed scope-only-dispatch prompts are 1000–2200 chars; 2500 catches 3000+ outliers.
- **Caveat:** owner may rule a different threshold; the value is named in AC.AG.2 (auditable), not method per ODD §7.4.

### D-A4.8 — T3 detection method

- **Question:** how does the Task gate detect "stale dispatch"?
- **Recommendation:** **union of amendment-number regex + AC-id regex + manifest-table query, with git-log fallback.** Matches both writing styles + handles fresh-workspace mid-bootstrap.
- **Why:** different prompt styles; manifest is the canonical record (D3); git-log fallback is the safety net.
- **Alternatives:** regex-only (no manifest read; misses sealed amendments not in current branch); manifest-only (misses fresh-workspace cases); git-log only (reintroduces brittleness D3 chose to avoid).

### Surfaced for owner ruling: 8 (D-A4.1 through D-A4.8).

(D-A4.9 + D-A4.10 are method per ODD §7.4 — builder defaults are NDJSON at `<workspace>/workspace/.pos/bash-guard.log` + `<workspace>/workspace/.pos/agent-guard.log`, and the curated regex deny-list per the named patterns in §4 + research §1.1 / §4. Sibling amendments may relocate.)

---

## 10. Risks

- **R1 — Bash regex false positives.** `git commit --amend` matches a legitimate operator amend; `rm -rf <path>` matches a legitimate scratch deletion; secret-file regex matches `.env-example`. Mitigation: each regex is paired with a carve-out (env-var override admits B1/B3/B4; explicit allowlist for `\.env[.-]example`; `<workspace>/.scratch/**` admitted under blast-radius). Builder records exact regex + carve-out interaction in §14.
- **R2 — Task envelope shape divergence.** Locked programme research §5.2 noted "Agent (or Task)". Mitigation: builder verifies `tool_name` value at build start.
- **R3 — `cwd` in envelope, not in Task `tool_input`.** Confirmed by docs convention. T1 reads parent envelope `cwd`. Risk: if Claude Code's Task envelope changes the cwd location, T1 reshapes.
- **R4 — Universal gates short-circuit on mode-bit unreadable.** Verified the architecture: universal gates (B2, B5) fire BEFORE the mode-bit read. If the mode bit is unreadable, universal gates STILL fire correctly. DEV-MODE-only gates short-circuit to allow (fail-closed-to-permissive at substrate boundary). Architecture is correct.
- **R5 — Hook-chain ordering for PreToolUse with FOUR matcher entries.** Claude Code admits multiple matcher entries; each fires only on its matching tool. No cross-matcher interaction. Risk surfaces only if the merge function corrupts the outer list during multi-contributor merge — A2's + A3's existing tests are the regression contract.
- **R6 — Subagent context detection (B1) imperfect.** Active-scope-sentinel-presence proxy misses main-session-with-active-scope edge case. Mitigation: env-var override + explicit diagnostic naming the proxy. Future amendment may refine via Claude Code's `CLAUDE_AGENT_TYPE` env var if it becomes available.
- **R7 — Bash command parsing brittleness.** Heredocs / command substitution / multi-statement (`a; b; rm -rf .`) may evade regex. Mitigation: regex deny-list is conservative (matches more than strictly required); false-positive direction is "deny rather than allow"; the conservative direction is correct for blast-radius / secret.
- **R8 — Override mechanism abuse.** Env-var override admits ONLY B1/B3/B4; constraint 18 + AC.BAG.1 + AC.BAG.2 enforce UNIVERSAL gates ignoring the env var. Tests cover this property explicitly.
- **R9 — Audit-log file proliferation (4 logs total: A2 + A3 + A4_bash + A4_task).** FIDRAFT-147 captures the rotation amendment.
- **R10 — Settings.json multi-contributor merge growth.** Outer list grows from 2 to 4 entries; marker tuple grows from 2 to 4. A3's multi-contributor extension generalises naturally; A2's + A3's existing settings-merge tests are the regression contract.
- **R11 — Bootstrap order chicken-and-egg (inherited).** Manifest rows for A4 ACs registered BEFORE A4 source edits; A4 tests authored BEFORE A4 source files (so A3's TDD-guard admits the source edits when they happen). Discipline canonical from A2/A3.
- **R12 — Hook latency on command-bursts.** A build that runs 50 Bash commands in a short span pays the gate cost 50×. Target < 10ms p95 means total burst overhead < 0.5s — acceptable. Mitigation: AC.BAG.6's no-op path is the cheap case; only matched commands pay the full deny-decision cost.
- **R13 — D-A4.5 partition reclassification cascade.** If owner reclassifies B1 (or any class), the corresponding AC reshapes AND the helper-library architecture may need to relocate the classifier (e.g., a UNIVERSAL B1 means `is_amend_command` joins the universal classifiers in `_gate_helpers.py`). Builder records the ripple in §14 if reclassification happens.
- **R14 — `pos-amend apply --dry-run` invocation cost (B3).** AC.BAG.4 invokes pos-amend per matching commit. pos-amend's dry-run is ~1-3s typically. The gate's per-commit cost includes this; for amendment-shape commits this is the right cost (the dry-run IS the work). For non-amendment commits the gate doesn't fire (no match). Risk surfaces if the regex incorrectly matches non-amendment commits → 1-3s wasted per fire. Mitigation: regex is anchored on the sealed-component-list pattern; AC.BAG.4 names the constraint.

---

## 11. Bookkeeping

- **Plan-doc:** this file at `docs/rebuild/plans/structural-enforcement-a4-bash-and-agent-context-guards.md`.
- **Research artefact:** `docs/rebuild/plans/research/structural-enforcement-a4-bash-and-agent-context-guards-research.md` (this dispatch).
- **Programme research:** `docs/rebuild/plans/research/structural-enforcement-of-critical-requirements-research.md` (locked 2026-04-26; governs).
- **A1 plan (sealed substrate):** `docs/rebuild/plans/structural-enforcement-a1-substrate.md`.
- **A2 plan (sealed sibling gate):** `docs/rebuild/plans/structural-enforcement-a2-objective-binding-gate.md`.
- **A3 plan (sealed sibling gate + helper-library precedent):** `docs/rebuild/plans/structural-enforcement-a3-tdd-guard.md`.
- **A3 builder plan (D-build precedent A4 mirrors):** `docs/rebuild/plans/structural-enforcement-a3-tdd-guard.builder-plan.md`.
- **Builder plan:** to be authored by the build agent post-owner-approval at `docs/rebuild/plans/structural-enforcement-a4-bash-and-agent-context-guards.builder-plan.md`. Contains files-touched, symbol-level details, AC-to-test mapping, D-build choices (decision-tree shape, exact regex deny-lists, env-var override naming, manifest-discovery strategy, prompt-pattern detection regex, multi-contributor merge marker tuple ordering), §2.5 reverse-direction audit, halt-trigger checks, pos-amend bookkeeping flow, helper-library extension equivalence verification (regression contract for A2 + A3).
- **Manifest:** authored alongside the builder plan at `docs/rebuild/plans/structural-enforcement-a4-bash-and-agent-context-guards.manifest.yaml`. Single-component manifest (`hands-off-lifecycle`); `frozen_baseline: true` (H19 frozen since project-start). Universal-paths block as standard.
- **Pos-amend bookkeeping flow** (per `feedback_dispatch_explicit_pos_amend_apply`):
  1. Author manifest at `docs/rebuild/plans/structural-enforcement-a4-bash-and-agent-context-guards.manifest.yaml` with the correct BASELINE (HEAD~1 of the upcoming amendment commit per the established #29/#34/.../#71 pattern).
  2. **Build-time manifest-row registration** (hard constraint 15): build agent's first action is `tracker.register_source_binding(component="hands-off-lifecycle", ac_id="AC.BAG.x" / "AC.AG.x" / "AC.A4.x", source_path_glob="...")` for each AC. Without this, A2 denies the first source edit (chicken-and-egg).
  3. **Test files authored before source files.** A4's tests (test_AC_BAG_1_*.py through test_AC_BAG_S_*.py + test_AC_AG_1_*.py through test_AC_AG_5_*.py + test_AC_A4_settings_merge.py + test_AC_A4_S_*.py) authored BEFORE the source files (`bash_guard.py`, `agent_guard.py`, `_gate_helpers.py` extensions, `first_run_settings.py` extensions, `first_run_helper.py` extensions). This satisfies BOTH A2's gate (rows-registered → admit) AND A3's own gate (tests-exist-before-source for new ACs → admit).
  4. Author all source edits + tests; commit as the amendment commit on branch `pos-v2`.
  5. `pos-amend apply --dry-run <manifest>` — must exit 0.
  6. `pos-amend apply <manifest>` — advances BASELINE literals + widens seal-diff bindings + writes SEAL_COMMIT sidecars.
  7. `pos-amend seal --plan-doc /Users/lukeivers/ivers-corp-pos-v2/docs/rebuild/plans/structural-enforcement-a4-bash-and-agent-context-guards.builder-plan.md <manifest>` — runs the scoped test sweep, creates the seal commit, advances SEAL_COMMIT to the seal commit, appends builder-plan §SHA backfill follow-up commit.
  8. Verify: `pos-amend apply --dry-run <manifest>` exits 0 against post-seal HEAD.
- **Seal-diff window:** BASELINE = HEAD~1 of amendment commit (set in builder plan after dispatch). Allowed paths under the window: `framework/hands-off-lifecycle/{hooks,tests,seals}/` plus universal admissions.
- **Programme tracking:** A4 closes the four-amendment programme. After A4 seals, the programme's surface (substrate + 3 gate-matchers covering Edit/Write/MultiEdit/Bash/Task) is end-to-end observable. Future structural-enforcement amendments are scoped fresh (e.g., A5 if a new failure class warrants).
- **Test scope per amendment-dispatch CDC speedups:** narrow pre-amendment test scope to `framework/hands-off-lifecycle/tests/` (covers AC.OBG.x + AC.TDG.x regression too) + `framework/objective-tracker/tests/` (consumer-only sanity check that A1's substrate API still works). Skip pre-seal full-suite rerun (sidecar-only edits between amendment and seal). Inline odd-methodology snippets into the dispatch brief.

---

## 12. References

- Locked programme research: `docs/rebuild/plans/research/structural-enforcement-of-critical-requirements-research.md`
- A4 research (sibling): `docs/rebuild/plans/research/structural-enforcement-a4-bash-and-agent-context-guards-research.md`
- A1 plan (sealed; substrate this builds on): `docs/rebuild/plans/structural-enforcement-a1-substrate.md`
- A2 plan (sealed; sibling gate, single-matcher precedent): `docs/rebuild/plans/structural-enforcement-a2-objective-binding-gate.md`
- A3 plan (sealed; sibling gate, helper-library precedent): `docs/rebuild/plans/structural-enforcement-a3-tdd-guard.md`
- A3 builder plan (D-build precedent): `docs/rebuild/plans/structural-enforcement-a3-tdd-guard.builder-plan.md`
- A1 substrate code (read-only inputs):
  - `framework/objective-tracker/src/runtime.py` (`manifest_rows_for_ac` — used by AC.AG.3)
  - `framework/hands-off-lifecycle/hooks/active_scope_sentinel.py` (`read_active_scope_sentinel` — used by AC.BAG.3 subagent-context detection + AC.AG.1 surface mention)
  - `framework/hands-off-lifecycle/hooks/corpus_load_sentinel.py` (`workspace_mode` — used by all DEV-MODE-only checks)
- A2/A3 gate code (the precedent A4 extends):
  - `framework/hands-off-lifecycle/hooks/_gate_helpers.py` (the shared library — A4 EXTENDS with two new functions)
  - `framework/hands-off-lifecycle/hooks/objective_binding_gate.py` (A2 — A4 does NOT modify; behaviour is regression-contracted)
  - `framework/hands-off-lifecycle/hooks/tdd_guard.py` (A3 — A4 does NOT modify; behaviour is regression-contracted)
  - `framework/hands-off-lifecycle/hooks/first_run_settings.py` (`merge_pre_tool_use`, `_POS_V2_PRE_TOOL_USE_COMMAND_MARKERS` — A4 extends marker tuple)
  - `framework/hands-off-lifecycle/hooks/first_run_helper.py` (`_objective_binding_gate_stanza`, `_tdd_guard_stanza`, `_maybe_merge_pre_tool_use` — A4 adds `_bash_guard_stanza`, `_agent_guard_stanza`; extends `_maybe_merge_pre_tool_use` to compose 4-element list)
- ODD methodology: `docs/odd-methodology.md` (§2.5 reverse direction; §3.3 one-criterion-per-behaviour; §5.1 structural-over-advisory; §5.1.1 relocate-vs-eliminate test; §7.4 flagged inferences; §8.1 authoring-time violations; §8.2 review-time violations)
- ODD-in-pos: `docs/odd-in-pos.md` (§10.3 frozen-both-endpoints baseline pattern — for AC.A4.S seal-diff invariant)
- VALUE_PROPOSITION: `docs/rebuild/VALUE_PROPOSITION.md` (Lens 2 anchor)
- FUTURE_IDEAS: `docs/rebuild/FUTURE_IDEAS.md` Idea 1 (programme), Idea 8 (structural context-load gate)
- FIDRAFT items A4 closes (directly or partially):
  - line 136 (main-session-write-prevention) → CLOSED by AC.BAG.5
  - line 143 (pre-dispatch staleness) → CLOSED by AC.AG.3
- FIDRAFT items A4 composes-with (does not close):
  - line 130 (corpus-inlining): distinct surface
  - line 145 (Direction-B test-without-impl): distinct surface
  - line 147 (audit-log rotation): A4 inherits A2+A3 deferral
  - line 149 (test-deletion gate): out of A4 scope
  - line 151 (dispatcher-side test-stub authoring): adjacent
- Memory-bullet feedback rules carried forward:
  - `feedback_no_amend_in_agent_dispatches` — closed (DEV-MODE) by AC.BAG.3
  - `feedback_always_specify_wd_in_dispatches` — closed (DEV-MODE) by AC.AG.1
  - `feedback_dispatch_explicit_pos_amend_apply` — closed (DEV-MODE) by AC.BAG.4
  - `feedback_agent_prompts_scope_only` — partially closed (DEV-MODE, length-only) by AC.AG.2
  - `feedback_verify_dispatch_before_sending` — closed (DEV-MODE) by AC.AG.3
  - `feedback_subagent_odd_violation_halt` — applied (halt-and-surface clauses §8)
  - `feedback_amendment_dispatch_speedups` — applied (test scope narrowed in §11)
  - `feedback_serialize_amendment_builds` — A4 serialises after A3
  - `feedback_summarize_and_surface_decisions` — applied (§9 surface with recommendations)
  - `feedback_always_specify_wd_in_dispatches` — applied (WD `/Users/lukeivers/ivers-corp-pos-v2/`)
  - `feedback_verify_post_amendment_state` — applied (read post-A3 code shape before A4 design — verified `_gate_helpers.py` + `tdd_guard.py` + multi-contributor `merge_pre_tool_use` directly)
- Claude Code hooks docs: https://code.claude.com/docs/en/hooks (PreToolUse decision-control surface; matchers admitting Bash + Task; `permissionDecision`; `permissionDecisionReason`; envelope `cwd` field)

---

## 14. Method-decision register (post-build, builder-backfilled)

Method-level decisions made during the build land here at seal time per `pos-amend seal --plan-doc` convention. Empty at plan-author time.

### Commit SHAs

- Amendment commit: `f1ae42beb052e1c89403f6bf50a28d3006e9391f` —
  `feat(structural-enforcement-a4): Bash/Agent-context guards (PreToolUse Bash + Task; secret-commit + blast-radius universal; amend-in-subagent + pos-amend-dry-run + wrong-tree-write DEV-MODE-only; wrong-WD + method-enumerated + stale-dispatch DEV-MODE-only)`
- Seal commit: `052c9b72cdd11695568c934331ede86ce5f4dad4` —
  `chore(seals): structural-enforcement A4 Bash/Agent-context guards (PreToolUse Bash + Task; secret-commit + blast-radius universal; --amend in subagent + pos-amend-dry-run + wrong-tree-write DEV-MODE-only; wrong-WD-dispatch + method-enumerated-prompt + stale-dispatch DEV-MODE-only; helper-library extension; multi-contributor PreToolUse merge to four-element outer list; NDJSON audit logs) — hands-off-lifecycle at f1ae42b`
