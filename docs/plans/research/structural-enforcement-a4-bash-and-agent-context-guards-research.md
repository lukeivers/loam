# Structural enforcement — A4: Bash/Agent-context guards — Research

**Author:** main-session research+plan dispatch
**Date:** 2026-04-28
**Spec binding:** `docs/spec/pos-v2-objectives-spec.md` line 134–135 — same binding A1+A2+A3 satisfy. A4 closes the four-amendment programme.
**Locked programme research:** `docs/plans/research/structural-enforcement-of-critical-requirements-research.md` (2026-04-26).
**A2 research:** `docs/plans/research/structural-enforcement-a2-objective-binding-gate-research.md`.
**A3 research:** `docs/plans/research/structural-enforcement-a3-tdd-guard-research.md`.
**Programme-level locks (carried forward):** D1 dev-discipline carve-outs; D2 TDD-guard scoped to re-extension-with-new-AC; D3 manifest extends `objective-tracker`; **D4 secret/blast-radius gates UNIVERSAL, ODD-discipline gates DEV-MODE-only** (governs A4 directly); D5 KEEP-ADVISORY list of 10.
**Pre-flight verification:** `git log --grep="A4|bash.guard|agent.guard|bash-and-agent"` returns no A4 amendment commit; `ls docs/plans/ | grep -iE "a4|bash.guard|agent.guard"` returns nothing matching `structural-enforcement-a4-*` other than this artefact and its sibling plan-doc. CLEAN at authoring time.

---

## 0. Summary (read first)

A4 is the FINAL gate amendment in the structural-enforcement programme. After A1's substrate (sentinel, manifest, mode-bit), A2's binding gate, and A3's TDD-guard, A4 extends the gate pattern to **two new tool surfaces** — `Bash` and `Task` (Claude Code's Agent-dispatch tool name; "Agent" is the persona-side label, "Task" is the actual hook-event tool name confirmed by the locked programme research §5.2).

A4 is structurally distinct from A2/A3 in three ways:

1. **Two matchers, not one.** A2/A3 share the `Edit|Write|MultiEdit` matcher set. A4 adds `Bash` and `Task`. Each matcher is a separate stanza in settings.json; each fires its own decision logic against its own `tool_input` shape. Bundling them into one stanza is impossible (Claude Code's matcher field is regex-over-tool-name; one hook script per tool surface).
2. **Mode-aware partition is non-trivial (D4).** A2 and A3 are entirely DEV-MODE-only. A4 has a mixed partition: `git push --force` blocking, `rm -rf` outside `.scratch/` blocking, secret-file commit blocking are **universal** (NORMAL USE workspaces too — these are user-protective regardless of mode). `pos-amend apply --dry-run` exit-0 commit-time enforcement, dispatch-WD-verification, dispatch-staleness verification are **DEV-MODE-only** (ODD-discipline). The single hook script must implement both partitions correctly.
3. **More acceptance criteria.** ODD §3.3 (one criterion per behaviour) means the Bash-side and Task-side behaviours each get their own AC; bundling violates one-criterion-per-behaviour. Conservative estimate: 12–14 ACs (vs A2's 8 and A3's 9), driven by the partition + the matcher count.

**Recommended firing layer:** `PreToolUse` Bash matcher + `PreToolUse` Task matcher; deny via `permissionDecision: "deny"` + structured `permissionDecisionReason`; reuses A3-extracted `_gate_helpers.py`; adds two universal-only helpers (blast-radius classifier, secret-pattern classifier) that A4 introduces. Hard cutover; NDJSON audit log per gate; A2/A3-pattern-symmetric.

**Decisions for owner:** 8 surfaced (D-A4.1 through D-A4.8). Highest-stakes: D-A4.5 (the universal-vs-DEV-MODE partition table itself — exactly which Bash command classes and which Task dispatch checks fire universally).

**Halt-and-surface findings:** none. Pre-flight clean; A1/A2/A3 substrate is sufficient for A4; no architecture-creep surfaced; helper-library extends cleanly.

---

## 1. The two tool surfaces — what A4 actually gates

### 1.1 Bash gate — what's in scope

`PreToolUse` matcher `Bash`, fires on every `Bash` tool call. `tool_input` carries `command` (the exact shell string Claude Code is about to execute). The gate inspects the command and decides allow / deny.

**Five candidate failure classes** identified across the locked programme research §5.1 / §5.3 / §5.6 + the FIDRAFT captures (lines 130, 136, 143, 149) + the rule inventory (rules 7, 8, 22):

- **B1 — `git commit --amend` from agent context.** Blast-radius blocker for the agent-side `feedback_no_amend_in_agent_dispatches` rule. Incident SHA: `d25eef5` rewrote `b966306`. Universal-or-DEV-MODE? — see D-A4.5 (recommended: **DEV-MODE-only**; main-session retains amend authority because the operator may legitimately amend).
- **B2 — Secret-file commit.** Universal blocker per programme D4. Patterns: `\.env(?:\..+)?`, `credentials\.json`, `\.aws/credentials`, `.*\.pem$`, `.*\.key$`, `id_rsa$`, etc. Fires on `git add`, `git commit`, `git stash`. Universal: secret leakage is irreversible; mode does not change the failure class.
- **B3 — `pos-amend apply --dry-run` exit-0 commit-time enforcement.** DEV-MODE-only. Intercepts `git commit -m "(feat|fix|chore|seal)\(<sealed-component>\)"` patterns; runs `pos-amend apply --dry-run` in canonical pos-v2; deny on exit ≠ 0. Programme research §5.3 named this as a high-leverage promotion.
- **B4 — Wrong-tree-write via `cd <workspace>/framework && ...`.** Closes the FIDRAFT-136 "main-session-write-prevention" recurring failure (3+ instances this session). A4's Bash branch detects `cd <X>/framework/` patterns where the active-scope sentinel says canonical is the work-target. DEV-MODE-only (the failure mode is workspace-mode-specific).
- **B5 — Blast-radius destructive commands.** Universal. `git push --force` to `pos-v2`/`main`; `rm -rf` outside `<workspace>/.scratch/`; `chmod -R 777 ~`; `dd if=...of=/dev/...`. Programme research §5.1 named the family as a "curated dangerous-Bash deny-list."

### 1.2 Task gate — what's in scope

`PreToolUse` matcher `Task`, fires on every Agent dispatch. `tool_input` carries `prompt` (the dispatch's prompt body), `description` (the short description Claude Code uses for UI), `subagent_type` (the agent handle), and **does NOT carry `cwd`** in the documented Claude Code envelope — `cwd` is the parent session's `cwd`, inherited by the subagent. This is critical: WD-verification is by the parent's `cwd` (the envelope's top-level `cwd`), not by a `tool_input.cwd` field.

**Three candidate failure classes** identified across programme research §5.2 + rule 6 + FIDRAFT-143:

- **T1 — Wrong-WD dispatch.** Closes `feedback_always_specify_wd_in_dispatches` + the orphan-commit-in-pos3 incident class (SHA `d2e8772`). When the dispatch prompt mentions pos-v2 surfaces (`docs/rebuild/`, `framework/<comp>/src/`, `pos-amend`, "seal commit", or contains the canonical pos-v2 path string `/Users/lukeivers/ivers-corp-pos-v2/`), the parent session's `cwd` must be the canonical pos-v2 path. Else: deny + name the canonical path. DEV-MODE-only (the rule is pos-v2-dev-specific).
- **T2 — Method-enumerated prompt (scope-only-dispatch CDC).** Closes rule 5 + `feedback_agent_prompts_scope_only`. Detection candidates: prompt length > 2500 chars (the locked programme research's "cheap version"); prompt contains forbidden tokens (`AC.\w+\.\d+:`, `Step \d+:`, file-path enumeration like `framework/<comp>/<file>.py`). The locked programme deferred the full NLP linter (research §2 row 5: "🔴 — NLP linting of free-text prompts is high-FP"). A4 ships only the **length-only** check (cheap, deterministic, owner-rulable threshold). DEV-MODE-only.
- **T3 — Dispatch-staleness verification.** Closes FIDRAFT-143 (the A1-build halt-and-surface scenario where the dispatcher sent an A1-substrate dispatch even though A1 had already shipped). When the dispatch prompt mentions an amendment number (`amendment #N`) or an AC ID (`AC.<X>.<Y>`), query A1's manifest table for sealed `(component, ac_id)` rows OR query `git log --grep="amendment #N"` for sealed amendment commits; deny if the dispatch re-targets an already-sealed scope. DEV-MODE-only.

### 1.3 What A4 explicitly does NOT gate

- **PostToolUse hooks.** A4 fires PRE — once Claude Code has executed a Bash command, the deny window has closed. The `pos-amend apply --dry-run` enforcement (B3) intercepts the commit BEFORE it lands in git history, not after.
- **Bash command parsing AST.** A4 uses regex over the command string. Shell parsing is non-deterministic in edge cases (heredocs, command substitution, eval); the regex deny-list is conservative (matches more than strictly required) and the carve-outs are explicit. Defer AST-shaped command parsing to a future amendment if regex false-positive rate becomes load-bearing.
- **Subagent-side gates.** A4's Task gate fires on the PARENT session's dispatch tool call. Inside the subagent, Claude Code applies project-level hooks (PreToolUse Edit/Write/MultiEdit etc.) per the documented inheritance — A2 + A3 already cover the subagent's edit surface; A4 covers the subagent's Bash surface (Bash hooks inherit too).
- **MCP tool calls** (any `mcp__<server>__<tool>` matcher). Out of A4 scope — not blast-radius or ODD-discipline by default. A future amendment may extend.

---

## 2. Firing layer — alternatives evaluated

### 2.1 Candidate A — `PreToolUse` matchers `Bash` + `Task` (recommended)

Native Claude Code primitive. Two stanzas in settings.json's `hooks.PreToolUse` array, alongside A2's + A3's Edit|Write|MultiEdit stanzas. Subagent-inheriting (every dispatched build agent's Bash + Task tool calls fire the same hooks). Symmetric with A2/A3 architecturally. Refusal via `hookSpecificOutput.permissionDecision: "deny"` + structured reason. The reason text appears to the model as `additionalContext`; the model adjusts.

**Why this works:**

- One hook script per matcher = clean separation of decision logic. The Bash hook reads `tool_input.command`; the Task hook reads `tool_input.prompt` + envelope `cwd`. No cross-matcher interference.
- The `_gate_helpers.py` library extracted by A3 already exposes the readers A4 needs (mode bit, sentinel, tracker, audit log). A4 extends with two new helper functions (blast-radius classifier, secret-pattern classifier) — no architectural creep.
- Multi-contributor `merge_pre_tool_use` (extended by A3 to handle the A2+A3 list) generalises naturally to A2+A3+A4_bash+A4_task. The marker tuple `_POS_V2_PRE_TOOL_USE_COMMAND_MARKERS` adds two more substrings.

### 2.2 Candidate B — single multi-tool stanza

A single PreToolUse stanza with matcher `Bash|Task|Edit|Write|MultiEdit` and a single hook script that branches on `tool_name`. Rejected: the matcher field admits regex but not arbitrary multi-tool dispatch within a single hook process; the hook script would have to fork on `tool_name` internally, conflating four decision-logics in one file. ODD §5.1 (structural over advisory) applied recursively — separating the stanzas is structural, conflating them is advisory ("the script will branch on tool name").

### 2.3 Candidate C — PostToolUse for `pos-amend apply --dry-run` (B3 only)

For B3 specifically: a PostToolUse hook on `Bash` that fires AFTER the commit lands and runs `pos-amend apply --dry-run`; if exit ≠ 0, the hook surfaces a structured warning (Claude Code's PostToolUse cannot revert the commit). Rejected: relocate-not-eliminate per ODD §5.1.1 (the commit is in history; the warning is advisory). PreToolUse is the structural shape — deny the commit before it lands.

### 2.4 Candidate D — pos-amend pre-commit git hook

For B3: a `.git/hooks/pre-commit` script run by git itself before the commit lands. Rejected: lives outside Claude Code's hook surface, not subagent-inheriting (subagent commits via `git commit` do hit `.git/hooks/pre-commit`, BUT the Claude Code hook surface is the canonical structural-enforcement surface per the locked programme research §7.1; bypassing it for one gate is architectural inconsistency). Also: not portable — `.git/hooks/` lives in `.git/`, which is per-clone, not committed; every fresh clone needs a setup script.

### 2.5 Recommendation

**Candidate A.** The pattern is set by A2/A3; A4 extends, doesn't deviate.

---

## 3. Refusal mechanism — alternatives evaluated

### 3.1 Candidate α — `permissionDecision: "deny"` + structured `permissionDecisionReason` (recommended)

Mirrors A2/A3 exactly. Native Claude Code surface. Reason text is structured-natural-language: opens with the failure class (e.g., "secret-file in commit set", "wrong-tree dispatch", "amendment #71 already sealed"), names what failed, names the repair. Visible to model + operator.

### 3.2 Candidate β — exit code 2 + stderr

Less structured. Locked programme research §3.2 already rejected this for A2; same reasoning applies.

### 3.3 Candidate γ — allow-with-warning via `additionalContext`

Advisory in structural clothing. Programme D4 + the directive lock 2026-04-26 forbid this for ODD-discipline gates AND for blast-radius/secret gates (where allow-with-warning still admits the destructive action — clearly wrong for `rm -rf ~`).

### 3.4 Recommendation

**Candidate α.** No deviation from A2/A3.

---

## 4. The mode-aware partition — D4 applied per failure class

The single highest-stakes design decision in A4. Programme D4 declares: secret/blast-radius gates UNIVERSAL; ODD-discipline gates DEV-MODE-only. Each failure class B1–B5 + T1–T3 must be classified.

### 4.1 Universal candidates (fire in NORMAL USE too)

The classification test: *"if this fires in a derived workspace (pos3 / eval clone / unrelated user repo), is the user protected or hindered?"*

- **B2 — Secret-file commit.** Universal. Secret leakage is irreversible regardless of workspace. The user is always protected by the gate. Rule 22 in the global `~/.claude/CLAUDE.md` ("NEVER commit secrets or .env files") is universal by authorship.
- **B5 — Blast-radius destructive commands.**
  - `git push --force` to `pos-v2` / `main`: universal. Force-pushing to a protected branch destroys history; mode does not change the consequence.
  - `rm -rf <path>` where path is OUTSIDE `<workspace>/.scratch/` AND `/tmp/`: universal. Destructive deletion outside ephemeral dirs is user-harming regardless of mode.
  - `chmod -R 777 ~` / `chmod -R 0 ~`: universal. Mass permission damage.
  - `dd if=...of=/dev/...`: universal. Disk-overwrite class.
  - `curl <url> | bash` / `curl <url> | sh`: ARGUABLY universal (executing remote code is a class of risk). Programme research did not name this; surfaced for D-A4.5 ruling. Recommendation: **include in the universal list** — same shape as the rest of the family.

### 4.2 DEV-MODE-only candidates

- **B1 — `git commit --amend`.** DEV-MODE-only.
  - Rationale: `feedback_no_amend_in_agent_dispatches` is a pos-v2-dev rule (preserves the audit trail of corrective commits). In NORMAL USE, the operator may legitimately amend (e.g., a fixup before pushing a PR). The gate would falsely deny legitimate amend operations in derived workspaces.
  - Sub-rule: even in DEV MODE, the gate must distinguish "main session" (operator-driven; allowed if the operator means it) from "subagent" (build-agent context; forbidden by the rule). Detection: the dispatch envelope itself doesn't carry `is_subagent`; A4 can detect via the `cwd` + the active-scope sentinel state (sentinel-present = subagent dispatched against an active scope), OR via Claude Code's documented `CLAUDE_AGENT_TYPE` env var if it surfaces in the hook process. **Both signals are imperfect**; A4 ships the **conservative shape** — block `--amend` when an active-scope sentinel is present (the dispatcher-authored sentinel marks the agent-context window). Operator can bypass by removing the sentinel or by allow-listing the command.
- **B3 — `pos-amend apply --dry-run` commit gate.** DEV-MODE-only. The rule is pos-v2-bookkeeping-specific.
- **B4 — Wrong-tree-write via `cd ... framework`.** DEV-MODE-only. The failure mode is workspace-mode-specific (canonical pos-v2 vs derived workspaces with mirror `framework/`).
- **T1, T2, T3 — Task-gate failure classes.** All DEV-MODE-only. Each is pos-v2-dev-specific.

### 4.3 Implementation shape

Each gate's first action is the mode-bit read. Gates with a "universal" leg branch on the result of the mode read:

```
mode = read_workspace_mode_or_normal_use(workspace_root)
# Universal-only checks fire regardless of mode:
if is_secret_commit(command): deny(secret)
if is_blast_radius(command): deny(blast)
# DEV-MODE-only checks fire only when mode == dev-mode:
if mode != "dev-mode": return allow()
if is_amend_in_subagent_context(...): deny(amend)
# ... etc
```

The cheap path (NORMAL USE, no universal trigger) returns allow after two regex checks (~tens-of-microseconds). The expensive path (DEV MODE with sentinel + tracker reads) is bounded by the same envelope as A2/A3 (~50ms p95).

---

## 5. Composition with A3-extracted `_gate_helpers.py`

Verified at research time by reading `framework/hands-off-lifecycle/hooks/_gate_helpers.py` (sealed at amendment #71, a52e04a). The helper library exposes:

- `WORKSPACE_STATE_SUBDIR`, `POS_SUBDIR` — path constants. **A4 reuses verbatim.**
- `_CARVE_OUT_PREFIXES`, `_CARVE_OUT_FILES`, `is_carve_out_path(...)` — dev-discipline carve-outs. **A4 reuses for B4 (wrong-tree-write detection inverts the check; a `cd framework/` is suspicious only when the path is NOT in the carve-out set).** No extension needed for the carve-out itself.
- `workspace_relative(...)` — path canonicaliser. **A4 reuses for B4 + B5** (resolving the target path of `rm -rf` to determine if it's outside `.scratch/`).
- `read_workspace_mode_or_normal_use(...)` — fail-closed-to-permissive mode reader. **A4 reuses verbatim** as the partition gate.
- `read_active_scope_sentinel_or_none(...)` — sentinel reader. **A4 reuses for B1 (subagent-context detection) + T1 (WD-verification: the sentinel's `plan_path` must be workspace-relative within canonical) + T3 (dispatch-staleness: the sentinel's bindings are checked against tracker rows).**
- `open_tracker_or_none(...)` — tracker opener with venv path-fix. **A4 reuses for T3 (manifest-row-for-AC query).**
- `audit_log_path(...)`, `append_audit_line(...)` — NDJSON audit-log shape. **A4 reuses verbatim.** Two new log filenames: `bash-guard.log` and `agent-guard.log`.
- `now_iso_z()` — timestamp. **A4 reuses verbatim.**

**A4 introduces two new helper functions** in `_gate_helpers.py`:

- `is_secret_commit_command(command: str) -> tuple[bool, list[str]]` — regex-based detection of secret-file paths in a git-add/git-commit/git-stash command. Returns `(matched, list of detected paths)` so the deny reason can name the offenders.
- `is_blast_radius_command(command: str, workspace_root: Path) -> tuple[bool, str]` — regex-based detection of blast-radius destructive patterns (the curated deny-list). Returns `(matched, reason_class)` where `reason_class` is one of `"git-push-force-protected", "rm-rf-outside-scratch", "chmod-recursive-home", "dd-to-device", "curl-pipe-shell"`.

These two helpers are universal-applicable (no mode-bit dependency); placing them in `_gate_helpers.py` lets a future amendment (e.g., a SubagentStop hook auditing the agent's Bash history) reuse them.

**No A3 helper incompatibility surfaced.** The library shape extends cleanly.

---

## 6. Acceptance-criteria sketch

A4's ACs are organized by failure class. Conservative count: 12 behaviours + 1 seal-diff invariant = **13 ACs**. Per ODD §3.3 each behaviour gets its own AC; bundling B1+B2+B5 into "AC.BAG.bash-deny" is a violation.

Behaviour list (forward direction; reverse audit is the builder's at build time):

| # | Behaviour | Mode | Failure class | Candidate AC |
|---|---|---|---|---|
| 1 | Bash gate denies secret-file commit (any mode) | UNIVERSAL | B2 | AC.BAG.1 |
| 2 | Bash gate denies blast-radius destructive command (any mode) | UNIVERSAL | B5 | AC.BAG.2 |
| 3 | Bash gate denies `--amend` in subagent context (DEV MODE) | DEV-MODE | B1 | AC.BAG.3 |
| 4 | Bash gate denies amendment-shape commit when `pos-amend apply --dry-run` fails (DEV MODE) | DEV-MODE | B3 | AC.BAG.4 |
| 5 | Bash gate denies `cd <ws>/framework && <write>` from main session against canonical work-target (DEV MODE) | DEV-MODE | B4 | AC.BAG.5 |
| 6 | Bash gate is no-op for non-targeted commands in NORMAL USE (mode short-circuit) | UNIVERSAL-LEG | — | AC.BAG.6 |
| 7 | Task gate denies dispatch with pos-v2 prompt content + wrong session `cwd` (DEV MODE) | DEV-MODE | T1 | AC.AG.1 |
| 8 | Task gate denies dispatch whose prompt exceeds the length threshold (DEV MODE) | DEV-MODE | T2 | AC.AG.2 |
| 9 | Task gate denies dispatch whose prompt re-targets a sealed `(component, ac_id)` (DEV MODE) | DEV-MODE | T3 | AC.AG.3 |
| 10 | Task gate is no-op in NORMAL USE | UNIVERSAL-LEG | — | AC.AG.4 |
| 11 | Both gates emit deterministic NDJSON audit lines per fire | UNIVERSAL | — | AC.BAG.7 + AC.AG.5 (two ACs — separate logs) |
| 12 | Settings.json multi-contributor merge admits A2+A3+A4_bash+A4_task | UNIVERSAL | — | AC.A4.settings_merge |
| 13 | Seal-diff confined to fence | UNIVERSAL | — | AC.A4.S |

**Total: 13 ACs (or 14 if AC.AG.5 is counted separately from AC.BAG.7 — both audit-log behaviours are structurally the same shape).** Behaviour-count target is 12 named behaviours + 1 seal-diff invariant = 13 ACs minimum.

The `AC.BAG.x` and `AC.AG.x` prefixes are recommended (Bash-And-Guards / Agent-Guards) but final naming is the plan-doc's call. ODD §3.3: bundling Bash + Agent into one AC.A4.deny is a violation; the matcher is different + the failure class is different + the decision data is different.

---

## 7. Migration shape

A4 lands; existing in-flight Claude Code sessions face the new gates. Cutover analysis:

- **B2 (secret-file commit).** Universal. No migration concern — the gate is user-protective in every workspace; first fire is the operator's "oh, I tried to commit a .env" moment with the diagnostic naming the offenders.
- **B5 (blast-radius).** Universal. Carve-outs explicit in the deny-list (the `<workspace>/.scratch/` exclusion for `rm -rf` is the main one). Operator pain ~zero in well-formed workflows; first fire is intentional-or-buggy `rm -rf ~/something` that the gate denies and surfaces.
- **B1 (`--amend`).** DEV-MODE-only. Operator bypass: remove the active-scope sentinel before amending. A4's diagnostic names this repair.
- **B3 (`pos-amend apply --dry-run`).** DEV-MODE-only. Existing builds that already run dry-run as social rule pass cleanly. The first DEV MODE commit that skips the dry-run fails the gate; diagnostic names the command. Operator pain ~zero — every existing build does this.
- **B4 (wrong-tree-write).** DEV-MODE-only. Operators writing to canonical via `cd <pos3>/framework && ...` (the FIDRAFT-136 failure mode) face deny on first fire. Diagnostic names canonical pos-v2 path as the right target. **The most operator-disrupting gate** because pos3 sessions occasionally do legitimate framework edits via main-session for triage; the carve-out admits a `--allow-this-write` env var or sentinel for explicit override. (See D-A4.7.)
- **T1/T2/T3 (dispatch gates).** DEV-MODE-only. T1 fires when an operator dispatches against pos-v2 from pos3 (the orphan-commit class). T2 fires on prompts exceeding the length threshold. T3 fires on stale dispatches (the FIDRAFT-143 scenario). All three name the repair in the diagnostic.

**Hard cutover** (Shape α from the A2 research) recommended. Soft cutover (grace period, log-only) is rule-shaped per ODD §5.1.1.

---

## 8. Composition with FIDRAFT items

A4 satisfies (directly or partially) these in-flight FIDRAFT captures:

- **FIDRAFT line 130 — corpus-inlining in SessionStart.** Distinct surface; A4 does not consume corpus state. No interaction.
- **FIDRAFT line 136 — main-session-write-prevention.** **Closed by AC.BAG.5 (B4 — wrong-tree-write via Bash).** A4's Bash branch catches `cd <ws>/framework && <write>`; A2's Edit branch already covers direct Edit on `<ws>/framework/`. Together the two gates close the failure class fully.
- **FIDRAFT line 143 — pre-dispatch staleness verification.** **Closed by AC.AG.3 (T3).** A4's Task branch queries A1's manifest table for sealed `(component, ac_id)` rows; if the dispatch's prompt re-targets a sealed row, deny. The exact prompt-pattern detection (regex over `amendment #N` and `AC.\w+\.\w+`) is method per ODD §7.4.
- **FIDRAFT line 145 — Direction-B test-without-implementation.** Out of A4 scope; the FIDRAFT capture itself notes a `Stop` hook is the right surface, not PreToolUse.
- **FIDRAFT line 147 — audit-log rotation.** A4 ships two more append-only NDJSON logs; rotation deferred (same pattern as A2/A3).
- **FIDRAFT line 149 — test-deletion gate.** Out of A4 scope (Bash `rm` of test files is destructive but differs from the secret/blast-radius family — different decision data). Future amendment territory.
- **FIDRAFT line 151 — dispatcher-side test-stub authoring.** A4 composes with the dispatch-staleness check (T3) — both touch the dispatch wrapper's surface. Adjacent but distinct.

---

## 9. Decisions surfaced for owner ruling

Eight decisions surfaced. Recommendations included per `feedback_summarize_and_surface_decisions`. (D-A4.5 + D-A4.6 are the high-stakes ones — partition table + carve-outs.)

### D-A4.1 — Firing layer

- **Question:** PreToolUse Bash + Task matchers (Candidate A) vs alternatives B/C/D.
- **Recommendation:** **Candidate A.** Mirrors A2/A3; native Claude primitive; subagent-inheriting; symmetric.
- **Caveat:** if owner picks anything other than A, every AC reshapes.

### D-A4.2 — Refusal mechanism

- **Question:** `permissionDecision: deny` + structured reason (Candidate α) vs alternatives β/γ.
- **Recommendation:** **Candidate α.** No deviation from A2/A3.

### D-A4.3 — Bash hook script layout

- **Question:** single `bash_guard.py` script handling all five Bash failure classes (B1–B5), OR split into `bash_blast_radius_guard.py` (universal B2+B5) and `bash_dev_discipline_guard.py` (DEV-MODE B1+B3+B4)?
- **Recommendation:** **single script `bash_guard.py`**. The internal mode-bit branch is cheap; splitting forces two settings.json entries, two audit logs, two deny-message styles. Bundling is structural here (one gate, one decision-tree) whereas Bash + Task are structurally different (different `tool_input` shape).
- **Alternatives:** the split shape is ergonomically cleaner if the universal-vs-DEV-MODE partition surfaces enforcement differences; either way is method per ODD §7.4.

### D-A4.4 — Task hook script layout

- **Question:** single `agent_guard.py` for T1+T2+T3, OR split per failure class?
- **Recommendation:** **single `agent_guard.py`**. Same rationale as D-A4.3.

### D-A4.5 — Universal-vs-DEV-MODE partition table (HIGH-STAKES)

The exact classification of each failure class.

| Class | Description | Recommendation | Rationale |
|---|---|---|---|
| B1 | `git commit --amend` | **DEV-MODE-only** + only in subagent-context (sentinel-present) | Main-session amend is legitimate; DEV-MODE-only avoids false-deny on derived-workspace operator workflows |
| B2 | Secret-file commit (`.env`, `*.pem`, `id_rsa`, etc.) | **UNIVERSAL** | Irreversible blast radius; user-protective in every workspace |
| B3 | `pos-amend apply --dry-run` exit-0 commit gate | **DEV-MODE-only** | pos-v2-bookkeeping rule; pos-amend doesn't exist in derived workspaces |
| B4 | Wrong-tree-write `cd <ws>/framework && <write>` | **DEV-MODE-only** | Workspace-mode-specific (canonical vs mirror) |
| B5 | Blast-radius destructive commands | **UNIVERSAL** | Mass-destructive class; user-protective everywhere |
| T1 | Wrong-WD dispatch | **DEV-MODE-only** | pos-v2-dev-specific |
| T2 | Method-enumerated prompt (length-only) | **DEV-MODE-only** | pos-v2-dev CDC |
| T3 | Dispatch-staleness verification | **DEV-MODE-only** | Manifest-table substrate is pos-v2-only |

**Caveat:** if owner reclassifies B1 (e.g., "block --amend universally — main-session-amend is rare and the operator can bypass via env-var"), AC.BAG.3 reshapes.

### D-A4.6 — Carve-outs / explicit override mechanism

The most operator-friction-prone gate is B4 (wrong-tree-write). Some main-session triage workflows legitimately edit `<workspace>/framework/` (e.g., reverting a bad sync). Operator override candidates:

- **(a) Env var.** `POS_BASH_GUARD_ALLOW=1` set in the parent shell allows the gate to skip. Operator-trustable; per-session.
- **(b) Sentinel file.** `<workspace>/.pos/bash-guard-allow.json` with a TTL. More state to manage.
- **(c) No override.** The carve-out is the existing dev-discipline list (`docs/`, `tools/`, etc.); for any other path, the gate is hard. Operator must commit-then-redirect via canonical.

**Recommendation:** **(a) env var**. Cheapest correct shape. Scoped to the operator's intent; structural (the gate reads the env var deterministically); no persistent state. Programme research's pattern for blast-radius carve-outs is the env-var direction (the locked research §5.1 names `$CLAUDE_AGENT_TYPE` env-var detection for B1).

### D-A4.7 — Length threshold for T2 (method-enumerated prompt)

- **Question:** prompt-length threshold for the T2 deny.
- **Recommendation:** **2500 chars** (the locked programme research's named cheap-version threshold). Most well-formed scope-only-dispatch prompts are 1000–2200 chars; the threshold catches the 3000+ method-enumerated outliers.
- **Caveat:** owner may rule a different threshold; this is method per ODD §7.4 if the value isn't pinned in the AC. **Recommended to NAME the threshold in AC.AG.2** so it's auditable (not method-shaped).

### D-A4.8 — T3 detection method

- **Question:** how does the Task gate detect "stale dispatch"?
  - **(a)** Regex on the dispatch prompt for `amendment #(\d+)` + manifest-table query for sealed rows in that amendment's component.
  - **(b)** Regex on the prompt for `AC\.\w+\.\w+` + manifest-table query for that exact AC's sealed status.
  - **(c)** Both (a) and (b); union of refusal conditions.
  - **(d)** `git log --grep="amendment #(\d+)"` instead of (a)'s manifest query (uses git history rather than the manifest substrate).
- **Recommendation:** **(c)**, both. The two patterns catch different writing styles ("dispatch the A1 substrate build" → no amendment number AND no AC ID, falls through; "dispatch amendment #51" → matches (a); "register AC.SE.1 for the manifest table" → matches (b)). Either alone misses cases.
- **Caveat:** (d) is substrate-independent (works without A1's manifest), but the manifest is the canonical record per programme D3 — using git log alone reintroduces the brittleness D3 chose to avoid.

---

## 10. Risks

- **R1 — Bash regex false positives.** `git commit --amend` regex catches the legitimate amend; `rm -rf <path>` regex on a path under `.scratch/` should be admitted; secret-file regex on `*.env-example` should be admitted. Mitigation: each regex is paired with a carve-out check (paths admitted by `is_carve_out_path` or by an explicit allowlist; the secret regex admits files matching `\.env[.-]example$`). Builder records the exact carve-out interaction in §14 of the plan.
- **R2 — Task envelope shape divergence.** The locked programme research §5.2 noted "Agent (or Task — Claude Code's actual tool name)" — the docs evolve. Mitigation: builder verifies the actual `tool_name` value at build start by reading `framework/hands-off-lifecycle/hooks/objective_binding_gate.py` (which shows the Edit/Write/MultiEdit envelope) + Claude Code docs at https://code.claude.com/docs/en/hooks. If the tool name is `Agent` not `Task`, A4's matcher reshapes.
- **R3 — `cwd` not in Task `tool_input`.** Confirmed by reading the Claude Code hook docs convention — `cwd` is a top-level envelope field, not in `tool_input`. T1 reads the parent `cwd` and verifies against canonical pos-v2 path. If the canonical path on a future maintainer's machine differs, the check needs a per-machine config — but the canonical path is hardcoded throughout the existing codebase (e.g., the dispatch-template defaults), so the assumption is consistent.
- **R4 — Mode-bit fail-closed-to-permissive direction means universal gates ALSO short-circuit when mode unreadable.** Wait — the universal gates fire BEFORE the mode-bit read. The decision-tree shape is: (a) parse Bash command; (b) check secret + blast-radius (universal — fire regardless); (c) read mode bit; (d) DEV-MODE checks. If the mode bit unreadable, (a)+(b) still fire correctly — the universal gates are independent. **Verified the architecture is correct.**
- **R5 — Hook-chain ordering for PreToolUse with FOUR matchers (Edit|Write|MultiEdit, Bash, Task).** Claude Code admits multiple matcher entries; each fires only on its matching tool. No interaction (Edit's matcher doesn't admit Bash; Bash's matcher doesn't admit Edit). The settings.json list order matters only WITHIN a single matcher; Bash and Task gates are independent stanzas with no chain-ordering interaction.
- **R6 — Subagent context detection (B1).** The active-scope-sentinel-presence proxy is imperfect (a main-session run AGAINST an active scope would also have the sentinel). Better signals: `CLAUDE_AGENT_TYPE` env var (named in programme research §5.1); current-process-tree parent-named-`claude-agent` (POSIX `os.getppid()` walk). All three are imperfect; the locked programme research suggests both env-var and process-tree as adjuncts. **Recommendation:** A4 uses the sentinel-present signal (cheapest, deterministic, no Claude Code env-var contract dependency); a future amendment may refine if false-positive rate becomes load-bearing.
- **R7 — Bash command parsing brittleness.** Heredocs (`bash -c 'cd framework && rm -rf .'` could escape detection if the regex doesn't normalize whitespace). Mitigation: each regex is anchored on the COMMAND itself (the `tool_input.command` string before Bash interprets it), and Claude Code's Bash tool passes the full string to the hook. The regex deny-list is conservative — false-positives admit fewer commands rather than allow more.
- **R8 — Override mechanism abuse.** Env-var bypass (D-A4.6) means an operator who wants to commit a secret can `POS_BASH_GUARD_ALLOW=1 git commit ...`. Mitigation: the override applies ONLY to DEV-MODE-only gates (B1, B3, B4); B2 and B5 (universal blast-radius/secret) are NOT bypassable by the env var. AC.BAG.1 and AC.BAG.2 explicitly enumerate the no-override property.
- **R9 — Audit-log file proliferation.** A4 adds two more NDJSON logs. Total now: A2's `objective-binding-gate.log` + A3's `tdd-guard.log` + A4's `bash-guard.log` + A4's `agent-guard.log`. FIDRAFT-147 captures the rotation amendment as a future need.
- **R10 — Settings.json multi-contributor merge growth.** With A4's two stanzas, the outer `hooks.PreToolUse` array grows from `[A2, A3]` to `[A2, A3, A4_bash, A4_task]`. The marker tuple grows from 2 to 4 entries. The `merge_pre_tool_use` function already handles the multi-contributor case (extended by A3); A4 is consumer-only.

---

## 11. Halt-and-surface findings (research-time)

None. Pre-flight clean (no A4 commits, no A4 plan-docs). A1/A2/A3 substrate is verified to support A4 without amendment to the substrate. `_gate_helpers.py` extends cleanly. The 4-amendment programme structure is preserved (A4 closes it).

**ODD violations in surrounding code surfaced during research:** none. The `objective_binding_gate.py` post-A3-refactor + `tdd_guard.py` shapes cleanly; no §2.5 violations in the helper-library extraction; the multi-contributor merge function `merge_pre_tool_use` is idempotent and well-shaped.

---

## 12. References

- Locked programme research: `docs/plans/research/structural-enforcement-of-critical-requirements-research.md`
- A2 plan (sealed): `docs/plans/structural-enforcement-a2-objective-binding-gate.md`
- A2 research: `docs/plans/research/structural-enforcement-a2-objective-binding-gate-research.md`
- A3 plan (sealed): `docs/plans/structural-enforcement-a3-tdd-guard.md`
- A3 research: `docs/plans/research/structural-enforcement-a3-tdd-guard-research.md`
- A3 builder plan: `docs/plans/structural-enforcement-a3-tdd-guard.builder-plan.md`
- A1 substrate code:
  - `framework/objective-tracker/src/runtime.py` (manifest-row APIs `manifest_rows_for_ac`, `manifest_rows_matching_source_path`, `register_source_binding`)
  - `framework/hands-off-lifecycle/hooks/active_scope_sentinel.py` (`ActiveScopeSentinel`, `read_active_scope_sentinel`)
  - `framework/hands-off-lifecycle/hooks/corpus_load_sentinel.py` (`workspace_mode`)
- A2/A3 gate code (the precedent A4 extends):
  - `framework/hands-off-lifecycle/hooks/_gate_helpers.py` (the shared library — A4 reuses + extends)
  - `framework/hands-off-lifecycle/hooks/objective_binding_gate.py`
  - `framework/hands-off-lifecycle/hooks/tdd_guard.py`
  - `framework/hands-off-lifecycle/hooks/first_run_settings.py` (`merge_pre_tool_use`, `_POS_V2_PRE_TOOL_USE_COMMAND_MARKERS`)
  - `framework/hands-off-lifecycle/hooks/first_run_helper.py` (`_objective_binding_gate_stanza`, `_tdd_guard_stanza`, `_maybe_merge_pre_tool_use`)
- ODD methodology: `docs/odd-methodology.md` (§2.5, §3.3, §5.1, §5.1.1, §7.4, §8.1, §8.2)
- ODD-in-pos: `docs/odd-in-pos.md` (§10.3 frozen-both-endpoints)
- VALUE_PROPOSITION: `docs/VALUE_PROPOSITION.md`
- FUTURE_IDEAS_DRAFT items composed with: lines 136 (main-session-write-prevention → AC.BAG.5), 143 (dispatch-staleness → AC.AG.3), 147 (audit-log rotation), 149 (test-deletion gate — out of A4), 151 (dispatcher-side test-stub authoring — adjacent)
- Memory-bullet feedback rules:
  - `feedback_no_amend_in_agent_dispatches` — closed (DEV-MODE) by AC.BAG.3
  - `feedback_always_specify_wd_in_dispatches` — closed (DEV-MODE) by AC.AG.1
  - `feedback_dispatch_explicit_pos_amend_apply` — closed (DEV-MODE) by AC.BAG.4
  - `feedback_agent_prompts_scope_only` — partially closed (DEV-MODE, length-only) by AC.AG.2
  - `feedback_subagent_odd_violation_halt` — adjacent; A4 itself dispatches with explicit halt-and-surface
  - `feedback_summarize_and_surface_decisions` — applied (§9 decisions surfaced with recommendations)

---

*End of research artefact.*
