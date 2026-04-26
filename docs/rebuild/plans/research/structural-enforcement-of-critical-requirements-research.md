# Structural Enforcement of Critical Requirements — Research

**Author:** main-session research dispatch
**Date:** 2026-04-26
**Spec binding:** `docs/rebuild/spec/pos-v2-objectives-spec.md` line 134–135 — *"Deterministic (tiered)"* objective, additional acceptance: *"(a) for any decision currently implemented as a rule/prompt where a deterministic hook/script could produce the same outcome, an audit surfaces it; (b) any arbitrary decision (no rubric cited) surfaces as a lint failure pending rubric definition."* This research is the audit surface clause-(a) requires; the implementation work that follows is the structural promotion programme it triggers.
**Owner directive (locked 2026-04-26):** *"Structural enforcement of critical guards and user-defined hard requirements is always going to trump rules in files and memories."*

---

## Summary

1. **Inventory:** 27 advisory rules currently in force across `~/.claude/CLAUDE.md`, project `CLAUDE.md`, `CLAUDE.dev.md`, `docs/odd-methodology.md`, `docs/odd-in-pos.md`, FUTURE_IDEAS CDCs, and 25 user-memory feedback files. 14 are candidates for structural promotion (PROMOTE), 6 are candidates if their cost falls or volume rises (DEFER), 7 are inherently advisory (KEEP-ADVISORY — voice/tone/judgment-shaped).
2. **Luke's two named candidates** (PreToolUse objective-binding gate + TDD-guard test-pinned-to-objective) are both feasible. The first is a single-amendment shape (~2-3d build); the second is a two-amendment shape (~4-6d build) that depends on the first because it needs the same objective-manifest substrate. Both lean cleanly on Claude Code's `PreToolUse` hook + `tool_input.file_path` matching.
3. **8 high-leverage structural promotions** identified beyond Luke's two. Top three by leverage × inverse-cost: (a) Bash `git commit --amend` blocker for agent context (1-line hook, prevents `feedback_no_amend_in_agent_dispatches` violations forever); (b) PreToolUse WD-verification gate on agent dispatches (catches the orphaned-pos3-commit class once and forever — `feedback_always_specify_wd_in_dispatches`); (c) PostToolUse `pos-amend apply --dry-run` exit-0 gate on amendment commits (already mechanically required by social rule; promote to a hook so a forgotten check fails the commit, not a future audit).
4. **Recommended amendment programme** is a 4-amendment chain — A1 foundational hook-registration substrate + objective manifest, A2 + A3 the two named gates landing on that substrate, A4 a batch of low-cost high-leverage Bash/agent-context guards. Estimated total cost ~9-14d wall-clock at one amendment per dispatch with serialisation per `feedback_serialize_amendment_builds`.
5. **Decisions surfaced for owner ruling:** 5 (numbered §11 below). Highest-stakes: D1 (does the objective-binding gate apply to ALL Edit/Write tool calls in pos-v2 dev work, or only to source-tree edits — i.e., are CLAUDE.md / docs / plans gated too?). D2 (does the TDD-guard apply to amendment work or only to net-new sealed-component scopes?). D3 (the manifest format for the objective registry — extend the existing `objective-tracker` SQLite store, or a flat YAML-per-component artefact?). D4 (workspace partition — gates run in DEV MODE only, never NORMAL USE?). D5 (what to KEEP-ADVISORY explicitly to short-circuit future "should this be structural?" debates).

---

## 1. Background — what changed today

ODD methodology §5 establishes structural-over-advisory as the design preference. The methodology gives one canonical worked example (clause (g) of self-upgrade) and one reach-for default (Pydantic + `@model_validator`), but it does not enumerate which existing pos-v2 advisory rules are candidates for promotion. The design surface — Claude Code hooks (`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`, `PreCompact`, plus 21 others), MCP server hooks, slash commands — has expanded considerably since the methodology was authored. The methodology's spec acceptance at line 135 already named the audit ("for any decision currently implemented as a rule/prompt where a deterministic hook/script could produce the same outcome, an audit surfaces it") but no audit had been run.

Today's owner directive promotes the audit from acceptance-criterion-pending to active design programme. Two named candidates landed simultaneously with the directive (PreToolUse objective-binding gate; TDD-guard test-pinned-to-objective). This research artefact is the audit; the amendments that follow are its remediation.

---

## 2. Inventory — advisory rules currently in force

Full rule table follows. Sources: `~/.claude/CLAUDE.md`, `/Users/lukeivers/ivers-corp-pos-v2/CLAUDE.md`, `CLAUDE.dev.md`, `docs/odd-methodology.md`, `docs/odd-in-pos.md`, `docs/rebuild/FUTURE_IDEAS.md` CDCs, 25 user-memory feedback bullets at `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_*.md`.

Cost legend: 🟢 ≤1d build, 🟡 1-3d build, 🔴 >3d build (or significant new substrate).
Leverage legend: ⭐⭐⭐ violation costs work + violates a recurring failure mode, ⭐⭐ violation occasionally costs work, ⭐ low-frequency or low-impact violation.

| # | Rule (one-line) | Source | Failure mode if violated | Structural candidate | Cost | Leverage | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | Every line of code/branch/test maps to a named AC backing a named objective (§2.5) | odd-methodology §2.5; `feedback_odd_no_non_objective_code` | Non-objective code accumulates silently; ratchets violations into amendment surface (Linux/systemd #6 incident) | **PreToolUse Edit/Write hook requires `objective:AC` declaration on the diff** (Luke's named candidate #1) | 🟡 (needs objective manifest) | ⭐⭐⭐ | **PROMOTE** — A2 |
| 2 | Test pinned to a named objective written before the code that satisfies it | NEW (Luke 2026-04-26) | Code authored to non-existent contract; AC drift | **PreToolUse Edit/Write on non-test source-tree files requires matching `test_<AC>_*.py` exists + last-modified before file** (Luke's candidate #2) | 🔴 (TDD-guard semantics) | ⭐⭐⭐ | **PROMOTE** — A3 |
| 3 | Plan exists at `docs/rebuild/plans/<name>.md` BEFORE source edits begin | FUTURE_IDEAS CDC; `feedback_plan_before_code` | Code ships without AC alignment; ODD violations land in seal cycle; 3 RED components in 2026-04-22 audit traced here | **PreToolUse Edit/Write on source tree refuses if no plan file matches the touched component** (composition with #1) | 🟡 | ⭐⭐⭐ | **PROMOTE** — A2 (subsumed) |
| 4 | Background-agent default for execution work; main-session is interactive | FUTURE_IDEAS CDC; `feedback_background_agents`, `feedback_background_default_for_authoring` | Channel blocks; user can't redirect mid-flight | **PreToolUse Bash hook denies long-running execution patterns (test runs, builds, multi-file edits) in main session unless wrapped via Agent dispatch** | 🔴 (heuristic for "long-running" is fuzzy; risks false positives) | ⭐⭐ | **DEFER** — A4 candidate; tag for later research |
| 5 | Scope-only dispatch: handoff carries objective+scope+constraints+halt+ODD-check, never files/symbols/AC-text/file-layout | FUTURE_IDEAS CDC; `feedback_agent_prompts_scope_only` | Plan reduced to paperwork; receiving agent's planning step bypassed | **PreToolUse on `Agent` tool: lint dispatch prompt for forbidden tokens (file paths, "AC1:", numbered step lists)** | 🔴 (NLP linting of free-text prompts is high-FP) | ⭐⭐ | **DEFER** — A4 candidate; cheap version: hard-deny prompts >2500 chars |
| 6 | Working directory specified in agent dispatches (canonical pos-v2 = `/Users/lukeivers/ivers-corp-pos-v2/`) | `feedback_always_specify_wd_in_dispatches` | Commits orphaned in pos3; full re-do required (incident: scope-only-dispatch CDC commit `d2e8772`) | **PreToolUse on `Agent` tool: refuse if dispatch lacks explicit `cwd` declaration matching pos-v2 canonical path when `tool_input.prompt` mentions pos-v2 surfaces** | 🟢 (regex on prompt) | ⭐⭐⭐ | **PROMOTE** — A4 |
| 7 | No `git commit --amend` in background-agent context | `feedback_no_amend_in_agent_dispatches` | Audit trail collapsed; dangling reflog; Git Safety Protocol violated (incident: Step-7 build agent commit `d25eef5`) | **PreToolUse Bash hook regex-blocks `git commit --amend` when `CLAUDE_AGENT_TYPE` env or subagent context is set** | 🟢 (one regex) | ⭐⭐⭐ | **PROMOTE** — A4 |
| 8 | `pos-amend apply --dry-run` exit-0 prereq for amendment commits | FUTURE_IDEAS CDC (#22); `feedback_dispatch_explicit_pos_amend_apply` | Sidecar/BASELINE drift; manual error in pos-amend bookkeeping | **PreToolUse Bash hook intercepts `git commit -m "feat(<sealed>)..."` matching amendment shape, runs `pos-amend apply --dry-run`, denies on exit ≠ 0** | 🟡 (commit-message classification) | ⭐⭐⭐ | **PROMOTE** — A4 |
| 9 | Subagent halt-and-surface on ODD violations (own work + surrounding code) | `feedback_subagent_odd_violation_halt` | Violations propagate silently across dispatches | **`SubagentStop` hook scans agent-final-report for required halt-and-surface phrasing; if violation patterns detected without surface marker, fails the stop** | 🔴 (phrasing-detection is unreliable) | ⭐⭐ | **DEFER** — keep advisory; revisit if violations recur |
| 10 | Session-start corpus loaded before any non-trivial pos-v2 turn | `feedback_session_start_discipline`; `CLAUDE.dev.md` §1 | Decisions made on incomplete context; failures recur | **`SessionStart` hook + `UserPromptSubmit` hook: inject `additionalContext` containing the required corpus + a sentinel; subsequent `PreToolUse` Edit/Write on pos-v2 source refuses unless corpus-loaded sentinel present** (already named as FUTURE_IDEAS Idea 8) | 🟡 (well-scoped; already researched) | ⭐⭐⭐ | **PROMOTE** — A1 (substrate) |
| 11 | Verify dispatch is the right action before sending (grep + read first) | `feedback_verify_dispatch_before_sending` | Mis-targeted fix-it dispatch; wasted agent budget | None — judgment-shaped pre-dispatch reasoning, not a tool-call surface | — | ⭐⭐ | **KEEP-ADVISORY** |
| 12 | Verify post-amendment state from code, not prior-agent reports | `feedback_verify_post_amendment_state` | Plan-reality contradiction; downstream agent halts (#29 → D5 incident, ~10min loss) | Partial — could add `pos-amend status` projection that always reads disk SHAs, but can't force the consumer to call it | — | ⭐⭐ | **KEEP-ADVISORY** + tooling |
| 13 | Critical thinking on deviations — enumerate, score, pick balance | `feedback_critical_thinking_on_deviations` | First-viable resolution chosen; outcome × cost not weighted | None — meta-reasoning rule | — | ⭐⭐ | **KEEP-ADVISORY** |
| 14 | Asymmetric problem solving — surface high-leverage points proactively | `feedback_asymmetric_problem_solving` | Repeating patterns + boilerplate not collapsed | None — observation-shaped rule | — | ⭐⭐ | **KEEP-ADVISORY** |
| 15 | Loose AC text → fix the AC, not the implementation | `feedback_loose_AC_text_fix_AC_not_implementation` | Code retrofitted to wrong literal AC; method-in-AC drift | None — judgment-shaped post-build review rule | — | ⭐ | **KEEP-ADVISORY** |
| 16 | Strict autonomy — don't pause on already-authorized work | `feedback_strict_autonomy_no_pause_for_authorized_work` | Discretionary check-in; user friction on redirect | None — turn-shape rule, not tool-shape | — | ⭐⭐ | **KEEP-ADVISORY** |
| 17 | Summarize and surface decisions, don't ask owner to read full docs | `feedback_summarize_and_surface_decisions` | Owner pays attention cost reading inline plans | Partial — `Stop` hook could check final response length vs. presence of file-path reference, but the right shape is already enforced by output-conventions §40-line/400-word rule | 🟡 | ⭐ | **DEFER** — output-conventions already covers; revisit if violations recur |
| 18 | Task-tracking discipline — pending items go to TaskCreate, not chat | `feedback_task_tracking_discipline` | Pending items lost in chat history | Partial — `Stop` hook could regex final response for "TODO:", "follow up:", "next:" patterns and refuse stop if no `TaskCreate` invoked in turn | 🟡 (heuristic) | ⭐⭐ | **DEFER** — A4 candidate; cheap version: nudge in `additionalContext` not block |
| 19 | Output >40 lines / >400 words → write to disk, reference path | project `CLAUDE.md` Output conventions | Context tokens wasted; compaction loses content | **`Stop` hook counts response lines/words; refuses stop if threshold exceeded and no file-path reference present** | 🟡 (line-count heuristic; UI text vs. content) | ⭐⭐ | **DEFER** — A4 candidate |
| 20 | Serialize amendment builds in same working tree | `feedback_serialize_amendment_builds` | Index.lock race; corrupted seals | **PreToolUse on `Agent` tool: read existing dispatch lockfile in `.scratch/`; refuse if another build agent is in flight** | 🟡 | ⭐⭐ | **DEFER** — A4 candidate (rare condition; agent-tool count is small) |
| 21 | Amendment dispatch speedups (narrow tests, skip pre-seal full rerun, inline methodology) | `feedback_amendment_dispatch_speedups` | Wall-clock 25-40% slower; widens 529-exposure window | None directly — these are dispatch-prompt content, not tool-call shapes | — | ⭐ | **KEEP-ADVISORY** + dispatch template |
| 22 | NEVER commit secrets or .env files | global `~/.claude/CLAUDE.md` | Secret leakage to public history; high-blast-radius irreversible | **PreToolUse Bash hook regex-blocks `git add .env*`, `git commit` when staged paths match secret patterns** (this is a literal Claude Code docs example) | 🟢 | ⭐⭐⭐ (irreversible blast radius) | **PROMOTE** — A4 |
| 23 | After every correction, update the relevant CLAUDE.md so the mistake doesn't repeat | global `~/.claude/CLAUDE.md` | Same mistake recurs; memory bullet spawn explosion | None directly — judgment-shaped recall | — | ⭐ | **KEEP-ADVISORY** |
| 24 | Lead with the answer; numbered lists; no filler; one next action | global `~/.claude/CLAUDE.md` | Communication friction; ADHD/attention cost on Luke | None — voice/tone shape | — | ⭐ | **KEEP-ADVISORY** |
| 25 | Sonnet for routine tasks; Opus only for architecture | global `~/.claude/CLAUDE.md` | Token cost inflation | Partial — could be a per-task model-routing rubric, but model-choice is largely outside hook surface | — | ⭐ | **KEEP-ADVISORY** |
| 26 | ODD/CDC scope — pos-v2 dev only; suggested in derived workspaces | `feedback_odd_cdc_scope` | Over-applied CDC violations on pos3-local edits | **All structural gates predicate on workspace mode** (DEV MODE = enforce; NORMAL USE = silent) — single workspace-mode bit gates the whole programme | 🟢 (one bit; already named in `CLAUDE.dev.md`) | ⭐⭐⭐ (correctness — without this every gate fires in derived workspaces) | **PROMOTE** — A1 (substrate prereq) |
| 27 | FUTURE_IDEAS_DRAFT.md is the no-overhead capture surface; agents surface to chat, parent appends | `feedback_future_ideas_draft_workflow` | Ideas drift away; recapture cost | None directly — capture-discipline rule | — | ⭐ | **KEEP-ADVISORY** |

**Counts:**

- PROMOTE: 8 (rules #1, 2, 3, 6, 7, 8, 10, 22, 26 — note #3 is subsumed into #1's gate)
- DEFER (eligible if cost falls or violations recur): 6 (rules #4, 5, 9, 17, 18, 19, 20)
- KEEP-ADVISORY: 7 (rules #11, 12, 13, 14, 15, 16, 21, 23, 24, 25, 27 — voice / judgment / capture-discipline shapes)

**High-leverage promotions count: 8** (PROMOTE row).

---

## 3. Luke's named candidate #1 — PreToolUse objective-binding gate

### 3.1 Trigger surface

`PreToolUse` matcher on `Edit|Write` tools. Source-tree paths only — DEV MODE workspace gate (rule #26 above). Excluded paths:

- `docs/**` — the dev-discipline carve-out; CLAUDE.md, FUTURE_IDEAS, plans, research are dev-discipline edits, not sealed-component work, and they don't need objective-binding (they ARE the objective binding for the code that comes after).
- `.scratch/**` — ephemeral.
- `tools/**` — already partitioned as dev-discipline per `CLAUDE.dev.md`.
- `tests/**` outside a sealed component — fixtures and helpers; revisit per D2 below.

Included paths: every sealed-component source dir (`safety-layer/src/**`, `cost-governance/src/**`, etc.) plus their per-component tests.

### 3.2 Validation mechanism

The gate checks the file-path against an objective manifest. The manifest is the new substrate this amendment introduces (decision D3 below — extend existing `objective-tracker` SQLite store, or a flat YAML-per-component artefact). For each touched file it requires either:

- The most-recent commit message in the local branch with a `Component-AC: <component>/<AC-id>` trailer matching a manifest entry, OR
- An active `pos-amend` manifest in `docs/rebuild/plans/amendment-<N>-<slug>.manifest.yaml` declaring the component+AC pair, OR
- A `.scope-of-work` sentinel in `.scratch/active-scopes/<scope-id>.yaml` declaring the AC-binding for the active scope.

The third path is the run-loop binding — when an agent (background or main) authors a plan at `docs/rebuild/plans/<name>.md`, the plan's frontmatter writes the sentinel; the gate consults it on subsequent edits.

### 3.3 Failure shape

Hook returns:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "ODD §2.5 — file <path> has no AC binding. Declare the AC in docs/rebuild/plans/<scope>.md or set .scratch/active-scopes/<scope>.yaml. Or, if this edit is dev-discipline (docs/CLAUDE.md/plans), retry on a docs/ path."
  }
}
```

Hard-deny, not warn. The directive locked 2026-04-26 says structural enforcement *trumps* advisory; warning shape is advisory.

### 3.4 Interaction with autonomous agents

Every dispatched agent inherits the hook (Claude Code applies project-level hooks to subagents). When the agent reads its scope brief, the brief points at the plan path; the agent's first move is reading the plan, which contains the AC binding; the gate queries the binding when the agent's first Edit fires. No agent-side change required — the gate is invisible to compliant agents and visible only to drift.

### 3.5 Audit trail

Each gate decision writes to `.scratch/structural-enforcement.jsonl` with `{ts, file, ac_binding, decision, reason}`. Periodic rollup into `objective-tracker` events (composes naturally with the existing event store) gives a queryable history: "show me every Edit that landed without an AC binding in the last 30 days." Acceptance for spec-line-135-(a) is satisfied directly by this audit log — the audit IS the surface clause-(a) named.

### 3.6 Cost estimate

🟡 — 2-3d wall-clock. Substrate: objective manifest (existing `objective-tracker` provides 80% of it). Hook: ~150 lines Python over the SessionStart pattern already in `hands-off-lifecycle/hooks/`. Tests: per-AC coverage of the gate's deny/allow paths, including the dev-discipline carve-out.

---

## 4. Luke's named candidate #2 — TDD-guard test-pinned-to-objective

### 4.1 Trigger surface

`PreToolUse` matcher on `Edit|Write`, file-path matches a sealed-component non-test source tree (`safety-layer/src/**` excluding `safety-layer/src/**/test_*.py`). Test-tree edits, dev-discipline paths, and infra dirs are excluded.

### 4.2 Existence + ordering check

The gate computes the AC the file binds to (via #1's manifest), then looks for a matching test:

- Pattern: `<component>/tests/test_<AC-id>_*.py` (matches the existing pos-v2 convention `test_A20_*`, `test_C14_*`, `test_B18_*`).
- The test file's git history must show its first introduction commit BEFORE the source file's first introduction commit for the same AC, OR (during build) the test file must already exist on disk with a non-empty `test_<AC>_*` function.

For amendment work: the AC is new; the test must already exist on disk for that AC before the source edit fires. This matches re-extension semantics (§4 of odd-methodology) — when an amendment adds A20, the A20 test is authored before the A20 code. The gate enforces ordering deterministically.

### 4.3 Re-extension scenario

When a builder discovers a gap during build (canonical safety-layer A20 case), the re-extension is: (a) add A20 to the proposal/plan, (b) write `test_A20_*.py` with a failing test, (c) write the code that satisfies A20. The gate, fired on (c), now passes because (b) wrote the test first. The gate enforces the sequence ODD §4 already requires.

### 4.4 Failure shape

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "TDD-guard — file <path> binds AC <AC-id> but no test_<AC-id>_*.py exists in <component>/tests/. Author the test first (red), then retry the edit."
  }
}
```

### 4.5 Interaction with autonomous agents + amendment scenarios

Same as #3.4 above — agents inherit. Amendment-specific: the existing `pos-amend apply --dry-run` already validates manifest shape; this hook composes by adding a per-AC test-existence check.

### 4.6 Cost estimate

🔴 — 3-4d wall-clock. The existence check is cheap; the ordering check (git log scan of test introduction vs source introduction) is the expensive part. Edge case: source-file edits that touch multiple ACs (a single function satisfies A4 and A5). Decision D2 below — does the gate require all referenced ACs to have tests, or just the *primary* AC the file is being added under? Recommended: all referenced ACs (matches the strict reading of TDD-guard).

### 4.7 Dependency on #1

This gate cannot run without #1's manifest. A2 lands first; A3 builds on A2.

---

## 5. High-leverage structural promotions beyond Luke's two

Surfaced via the rule-inventory leverage × inverse-cost ranking. Top 8 below; full list in §2.

### 5.1 PROMOTE — Bash hook blocking `git commit --amend` in agent context

**Rule binding:** #7. **Cost:** 🟢 (one regex). **Leverage:** ⭐⭐⭐ (incident: `d25eef5` rewrote `b966306`, audit trail collapsed).

**Hook shape:** `PreToolUse` matcher `Bash`, regex on `tool_input.command` for `git commit\s+(.*\s+)?--amend`, deny when `$CLAUDE_AGENT_TYPE` env is set or current process tree includes a parent named `claude-agent`. Single-file hook; ~30 LOC.

**Why high-leverage:** The rule has been violated at least once (Step-7 commit incident). It's a simple regex. Once landed, the violation is structurally impossible from agent context. Same pattern blocks `git push --force`, `git reset --hard`, `rm -rf` — extend with a curated dangerous-Bash deny-list while at it.

### 5.2 PROMOTE — PreToolUse WD-verification gate on Agent tool

**Rule binding:** #6. **Cost:** 🟢 (regex on prompt). **Leverage:** ⭐⭐⭐ (incident: scope-only-dispatch CDC commit `d2e8772` orphaned in pos3).

**Hook shape:** `PreToolUse` matcher `Agent` (or `Task` — Claude Code's actual tool name), check `tool_input.prompt` contains pos-v2 surface mentions (`docs/rebuild/`, `<component>/src/`, `pos-amend`, `seal commit`); if so, require `tool_input.cwd` to be set and to match `/Users/lukeivers/ivers-corp-pos-v2/`. Deny otherwise.

**Why high-leverage:** Recovered orphan commits cost ~10-30min each; this fires once per dispatch and prevents the entire incident class. Pairs naturally with #5.1 in a single Bash/Agent-context hook bundle.

### 5.3 PROMOTE — `pos-amend apply --dry-run` exit-0 gate on amendment commits

**Rule binding:** #8. **Cost:** 🟡 (commit-message classification). **Leverage:** ⭐⭐⭐ (sidecar/BASELINE drift catastrophic).

**Hook shape:** `PreToolUse` matcher `Bash`, intercept commands matching `git commit -m "(feat|fix|chore|seal)\(<sealed-component>\)"`. If matched, run `pos-amend apply --dry-run` in canonical pos-v2; deny on exit ≠ 0; `additionalContext` reports the failure detail.

**Why high-leverage:** `pos-amend apply --dry-run` is already social-rule mandatory per amendment #22. The social rule is enforced by agents reading the README + memory bullets. A skipped dry-run currently surfaces only at audit time. Promoting to structural means a skipped check fails the commit, not a future audit.

### 5.4 PROMOTE — Structural context-load gate (FUTURE_IDEAS Idea 8)

**Rule binding:** #10. **Cost:** 🟡 (well-scoped; designed). **Leverage:** ⭐⭐⭐ (every session re-discovers the corpus; failures recur).

**Hook shape:** `SessionStart` hook injects required-corpus list into `additionalContext` plus a sentinel timestamp. Subsequent `PreToolUse` Edit/Write on pos-v2 source refuses if no `Read` tool calls touched the corpus paths in the current session. Composition with #1 and #2: the substrate for "agent loaded the corpus" is the same as the substrate for "agent declared an AC" — store both as session-scoped sentinels in `.scratch/session-state/<session-id>.json`.

**Why high-leverage:** Incident: 2026-04-23 install-status check that ballooned into design-decision territory without corpus loaded. Pattern recurs every session-start. Idea 8 is already in FUTURE_IDEAS; this research promotes it from idea to amendment.

### 5.5 PROMOTE — Workspace-mode partition (DEV MODE / NORMAL USE)

**Rule binding:** #26. **Cost:** 🟢 (one bit). **Leverage:** ⭐⭐⭐ (correctness gate for the whole programme).

**Hook shape:** `dev-mode-manifest.yaml` (already exists per `CLAUDE.dev.md`) carries a single `mode: dev-mode | normal-use` bit. Every gate above is no-op when mode = `normal-use`. Without this, every gate would fire in derived workspaces (pos3, eval clones) where ODD/CDCs are suggested-not-required — a false-positive fountain.

**Why high-leverage:** Without it, the entire structural-enforcement programme is wrong-shaped. With it, the programme respects the dev/normal partition the methodology already names.

### 5.6 PROMOTE — Bash hook blocking secret-file commits

**Rule binding:** #22. **Cost:** 🟢. **Leverage:** ⭐⭐⭐ (irreversible blast radius — secret leakage to public history).

**Hook shape:** `PreToolUse` matcher `Bash`, regex on `git add` / `git commit` for paths matching `\.env(?:\..+)?$|credentials\.json$|\.aws/credentials$|.*\.pem$|.*\.key$`. Deny + show curated list of detected paths. Already named as a literal example in Claude Code hooks docs; this is the lowest-friction high-leverage hook to ship.

**Why high-leverage:** Currently advisory in global CLAUDE.md (#22). Single mistake is irreversible. Single-amendment ship.

### 5.7 PROMOTE — PreToolUse plan-file existence check (composed with #1)

**Rule binding:** #3. **Cost:** subsumed into A2.

**Hook shape:** the same gate that verifies AC binding in #1 also verifies a plan file exists at `docs/rebuild/plans/<scope>.md`. If the active scope sentinel says `scope: amendment-N-foo`, the plan path must resolve. No additional hook surface — same hook, additional check.

**Why high-leverage:** Plan-before-code CDC has been violated multiple times (3 RED components). Free-rides on #1's substrate.

### 5.8 DEFER → revisit — Stop-hook output-conventions enforcement

**Rule binding:** #19 (output >40 lines / >400 words to disk). **Cost:** 🟡. **Leverage:** ⭐⭐.

**Why defer:** Heuristic boundaries (UI rendering vs. content text) make false positives likely. Currently no measured violation rate; promote only if violations recur post-A4.

---

## 6. Recommended amendment programme

Four amendments. Sequenced, with explicit dependency notes. Estimated wall-clock at one amendment per dispatch with `feedback_serialize_amendment_builds` (no parallel builds in canonical tree): ~9-14d total.

### 6.1 Amendment A1 — `structural-enforcement-substrate`

**Scope:** establish the hook-registration pattern + the workspace-mode partition + the active-scope sentinel surface + the corpus-loaded sentinel. No user-visible gates yet — this amendment lands the substrate every subsequent gate composes on.

**Specifically lands:**

- A new component or sub-component under `hands-off-lifecycle/hooks/structural/` (or a sealed `structural-enforcement/` peer — D3 below). Gate runtime + JSON-schema for sentinels.
- `dev-mode-manifest.yaml` mode-bit consumption (the file exists; this amendment makes it load-bearing).
- `SessionStart` hook addition (composes with the existing first-run hook): writes corpus-required-paths + session-id sentinel to `.scratch/session-state/<session-id>.json`.
- Active-scope sentinel writer (a small `pos-scope` CLI or a pos-amend extension that creates `.scratch/active-scopes/<scope-id>.yaml` from a plan-file frontmatter).
- The objective manifest substrate — extend `objective-tracker` schema with a `(component, ac_id, source_path_glob)` table, OR add a simple `<component>/.objectives.yaml` artefact (D3).

**Acceptance criteria** (skeleton — full list authored in proposal):

- AC.SE.1: SessionStart hook writes the session sentinel within 200ms p95.
- AC.SE.2: `pos-scope start --scope <id> --plan <path>` creates the active-scope sentinel; plan-file frontmatter declares `binds: [{component, ac_id}]`.
- AC.SE.3: Workspace-mode partition is honored — gates query the mode bit before any decision; `mode: normal-use` short-circuits to allow.
- AC.SE.4: Sentinel files are gitignored.
- AC.SE.5: A test workspace with `mode: dev-mode` and a missing sentinel file produces no false-positive gate denials (this amendment lands no gates).

**Cost:** 🟡-🔴, 3-4d. Depends on D3.

**Dependencies:** None blocking, but pulls in `objective-tracker` for D3-(option-A).

### 6.2 Amendment A2 — `objective-binding-gate`

**Scope:** Luke's named candidate #1 — the PreToolUse hook that requires Edit/Write to a sealed-component source path declare an AC binding via the substrate from A1.

**Acceptance criteria** (skeleton):

- AC.OBG.1: Edit on `<component>/src/**` with no active-scope sentinel and no commit-trailer binding deny-blocks the tool call.
- AC.OBG.2: Edit on `docs/**`, `.scratch/**`, `tools/**` (dev-discipline paths) bypasses the gate.
- AC.OBG.3: Edit when `mode: normal-use` bypasses the gate.
- AC.OBG.4: Audit log writes a `(ts, file, ac_binding, decision, reason)` row per gate decision; `objective-tracker` projection consumes the rows.
- AC.OBG.5: Re-extension shape (new AC mid-build) — a plan-file frontmatter update + sentinel rewrite, followed by the source edit, passes the gate.

**Cost:** 🟡, 2-3d.

**Dependencies:** A1 must seal first.

### 6.3 Amendment A3 — `tdd-guard-test-first`

**Scope:** Luke's named candidate #2 — PreToolUse hook on non-test source-tree files requiring matching `test_<AC>_*.py` to exist on disk (and, where the AC is being authored fresh in this amendment, to predate the source-file's first introduction in git history).

**Acceptance criteria** (skeleton):

- AC.TDG.1: Edit on `<component>/src/foo.py` binding AC X with no `<component>/tests/test_<X>_*.py` deny-blocks.
- AC.TDG.2: Edit on `<component>/src/foo.py` binding AC X where the test exists with a `test_<X>_*` function (any body) allows.
- AC.TDG.3: Re-extension scenario — new AC added mid-build; test authored before source edit; gate passes.
- AC.TDG.4: Edit on `<component>/tests/**` is bypassed (the gate doesn't apply to test edits themselves).
- AC.TDG.5: Multi-AC source files — all bound ACs require matching tests (D2 below).

**Cost:** 🔴, 3-4d.

**Dependencies:** A2 must seal first (the manifest + binding mechanism is shared).

### 6.4 Amendment A4 — `bash-and-agent-context-guards`

**Scope:** the bundle of low-cost high-leverage Bash/Agent-context guards — `git commit --amend` blocker (#7), Agent-tool WD-verification gate (#6), `pos-amend apply --dry-run` commit-time gate (#8), secret-file commit blocker (#22). Optionally include #4/#5/#18/#19/#20 deferred candidates if their cost has fallen post-A1.

**Acceptance criteria** (skeleton):

- AC.BAG.1: `git commit --amend` from an agent context deny-blocks; from main session passes (with the existing user authorization).
- AC.BAG.2: `Agent` tool dispatch with pos-v2 prompt content + missing/wrong `cwd` deny-blocks.
- AC.BAG.3: `git commit` with secret-pattern paths deny-blocks.
- AC.BAG.4: `git commit -m "feat(<sealed>)..."` triggers `pos-amend apply --dry-run`; non-zero exit deny-blocks the commit.

**Cost:** 🟡, 1-2d (mostly the commit-message classifier + integration tests).

**Dependencies:** A1 (workspace-mode partition).

### 6.5 Total programme

| Amendment | Slug | Cost | Depends on |
|---|---|---|---|
| A1 | `structural-enforcement-substrate` | 3-4d | — |
| A2 | `objective-binding-gate` | 2-3d | A1 |
| A3 | `tdd-guard-test-first` | 3-4d | A2 |
| A4 | `bash-and-agent-context-guards` | 1-2d | A1 |

Total: 9-13d wall-clock, serialised.

A4 can run in parallel with A2/A3 in principle (touches different surfaces) — but per `feedback_serialize_amendment_builds` parallel builds in the canonical tree are forbidden until pos-amend worktree-isolation is verified. Default: serialise.

---

## 7. Three-lens analysis

### 7.1 Lens 1 — Claude-leverage-first

Every amendment in this programme leans cleanly on Claude Code primitives:

- A1: `SessionStart` hook + workspace-mode bit (already a Claude Code project-config primitive).
- A2: `PreToolUse` hook + `Edit`/`Write` matcher + `permissionDecision: "deny"` + `additionalContext` for the failure reason.
- A3: `PreToolUse` hook + `Edit`/`Write` matcher; same surface as A2.
- A4: `PreToolUse` hook + `Bash` matcher + `Agent` matcher.

Required research question: *"What Claude capability does this lean on or extend?"* — the answer is "every Claude Code hook event the framework documents." The programme is composed of Claude-native primitives end-to-end; nothing is re-implemented from scratch. The only custom code is the substrate (objective manifest, sentinel files, gate decision logic), which is what the hooks call into.

The asymmetric finding: **the entire structural-enforcement programme is Claude-leverage-shaped because Claude Code's hook surface IS the structural-enforcement surface.** Once that's seen, the programme stops being "we should be more disciplined" (advisory) and becomes "we should turn the discipline we already practice into hook configurations" (structural). That asymmetry is the directive itself, restated.

### 7.2 Lens 2 — Harness + primary-persona value

- **Primary-persona test:** does this reduce the translation burden between the user's natural-language intent and AI-effective execution? **Yes.** Today the primary persona's translation toolkit includes "remember the 27 advisory rules and apply them to every dispatch / every edit / every commit." Structural promotion moves the rules out of memory and into the hook substrate; the persona's translation work narrows to the Lens-1/Lens-2 design choices, not the bookkeeping discipline. Net translation burden: significantly reduced.
- **Harness test:** does this add to the toolkit the primary persona can draw from? **Yes.** The substrate (objective manifest, active-scope sentinel, corpus-load sentinel) is itself a toolkit primitive: a new persona dispatch can interrogate "what AC am I working on?" structurally, and the substrate answers. Future amendments compose on the substrate (the workspace-mode bit, the scope sentinel, the manifest schema all become reusable harness primitives). The harness gains four new primitives this programme.

Both Lens 2 tests pass. The programme is high-value.

### 7.3 Lens 3 — ODD authoring

Every amendment is structurally shaped, not advisory. Every gate is a deterministic check (decision yields the same verdict on the same state, every run, no model inference). Every gate's failure shape is a structured deny + reason text. The programme materializes the methodology's "structural over advisory" principle directly — in pos-v2's own dev workflow, applied to pos-v2's own dev rules.

The programme's own ACs (skeleton above) follow ODD authoring: outcome-shaped, deterministic, one-AC-per-behaviour. The full proposals will tighten the skeletons.

---

## 8. Spec-objective binding (per CLAUDE.md §2.5)

This research artefact and the amendment programme it triggers satisfy the `pos-v2-objectives-spec.md` line 134–135 *Deterministic (tiered)* objective's additional acceptance:

> *(a) for any decision currently implemented as a rule/prompt where a deterministic hook/script could produce the same outcome, an audit surfaces it; (b) any arbitrary decision (no rubric cited) surfaces as a lint failure pending rubric definition.*

Acceptance (a) is satisfied directly: §2 of this artefact IS the audit. Each PROMOTE row is a "rule/prompt where a deterministic hook/script could produce the same outcome." The amendment programme in §6 is the remediation programme spec-line-135-(a) implies.

Acceptance (b) — "arbitrary decision surfaces as a lint failure" — is satisfied incidentally by A4's audit-log writer: every gate decision (allow/deny + reason) is logged; arbitrary decisions surface naturally because they fail to bind to an AC and the deny+reason is the lint output.

The two named candidates (Luke's PreToolUse objective-binding gate + TDD-guard) are the two highest-leverage entries in the audit, so the programme correctly leads with them.

---

## 9. Halt-and-surface findings

- **No required new top-level objective.** The programme satisfies an existing spec acceptance (line 135-(a)) and the prime-objective AC.PO.1 (translation-burden reduction) + AC.PO.2 (harness-toolkit expansion). No new top-level objective is required.
- **No ODD violation in surrounding code surfaced during research.** The advisory rules being audited are themselves not code — they're prose rules in CLAUDE.md / memory files / FUTURE_IDEAS. The amendment programme structurally enforces them; it does not extend or amend code that itself violates ODD.
- **No required source-edit outside primary-persona / hands-off-lifecycle / workspace-bootstrap.** The substrate naturally lands in `hands-off-lifecycle/hooks/structural/` (composes with the existing first-run hook surface) — that's a sealed-component amendment within an already-permitted boundary. Optionally A1 could create a new sealed `structural-enforcement/` peer; D3 below names this.

No halt required.

---

## 10. Decisions surfaced for owner ruling

Every decision is named with a recommended default per `feedback_summarize_and_surface_decisions`.

### D1 — Scope of the objective-binding gate (#1)

**Question:** does the PreToolUse Edit/Write objective-binding gate apply to ALL pos-v2 source-tree edits, or only to sealed-component source edits?

**Options:**

- **(a)** All `<component>/**` edits (including tests, fixtures, docs). Strictest reading.
- **(b)** Only `<component>/src/**` edits — exclude tests, fixtures, sealed-component-internal docs.
- **(c)** Only `<component>/src/**` AND `<component>/tests/**`, exclude fixtures/docs.
- **(d)** As (b) AND with explicit dev-discipline carve-outs for `docs/**`, `tools/**`, `.scratch/**`, `CLAUDE*.md`.

**Recommendation:** **(d)**. The dev-discipline carve-out matches `feedback_odd_cdc_scope` ("ODD/CDC scope — pos-v2 dev only, not derived workspaces") applied recursively — `docs/`, `tools/`, `CLAUDE*.md` are themselves the binding artefacts the gate references; they don't need to be gate-bound themselves. Tests are gated by A3 (TDD-guard) and don't need this gate.

### D2 — Scope of TDD-guard for amendment work (#2)

**Question:** does TDD-guard require tests-first for amendments to existing sealed components, or only for net-new sealed-component scopes?

**Options:**

- **(a)** All edits to sealed-component source require matching test, regardless of amendment vs new.
- **(b)** Only net-new scopes (where the source file is new); amendments to existing source bypass.
- **(c)** Amendments require test-first only when adding a new AC (re-extension); in-AC modifications bypass.

**Recommendation:** **(c)**. Matches odd-methodology §4 re-extension exactly — when an amendment introduces a new AC (e.g., A20 added to safety-layer mid-build), the test for that AC must precede the code. In-AC bug fixes don't add a new contract; they refine existing code against an existing test. Option (a) is over-strict (every refactor requires touching the test); option (b) is under-strict (re-extension is the canonical case the gate exists for).

### D3 — Objective manifest substrate

**Question:** where does the `(component, ac_id, source_path_glob)` registry live?

**Options:**

- **(a)** Extend `objective-tracker` SQLite store with a new table. Pro: single source of truth, queryable. Con: requires sealed-component amendment to objective-tracker.
- **(b)** Per-component `<component>/.objectives.yaml` flat file. Pro: lives next to the component; no central store amendment. Con: 13 files to maintain; gate has to read all of them per query.
- **(c)** Plan-file frontmatter only — no separate manifest. The gate consults the active-scope sentinel which contains the binding. Pro: simplest. Con: no cross-amendment registry; can't query "show me all ACs A20 covers across components."

**Recommendation:** **(a)**, extending objective-tracker. The component already exists, already stores `ObjectiveSpec`, already has an event store and a projection layer (per the existing `src/spec.py`, `store.py`, `projection.py`). Adding a `(component, ac_id, source_path_glob)` table is a natural extension. Pairs with FUTURE_IDEAS Idea 16 ("tracker public API for source-commit rewriting") — same direction of travel.

### D4 — Workspace partition

**Question:** do gates run in DEV MODE only? Or are some gates universal (e.g., secret-file commit blocker)?

**Options:**

- **(a)** All gates DEV MODE only — `mode: normal-use` short-circuits everything to allow.
- **(b)** All gates DEV MODE only EXCEPT the secret-file commit blocker (#22), which is universally protective.
- **(c)** Universal gates: secret-file blocker + dangerous-Bash blocker (`rm -rf /`, `git push --force` to main). DEV-MODE-only gates: everything else.

**Recommendation:** **(c)**. Secret-file leakage and `rm -rf /`-class blast radius are user-protective regardless of dev/normal mode; they're the global CLAUDE.md rules anyway, so they ladder up to user-safety rather than ODD-discipline. ODD-discipline gates are DEV-MODE-only.

### D5 — Explicit KEEP-ADVISORY list (short-circuit future debates)

**Question:** which rules are formally KEEP-ADVISORY so future "should this be structural?" debates don't re-litigate them?

**Recommendation (10 KEEP-ADVISORY rules):**

- #11 Verify dispatch is the right action — judgment-shaped pre-dispatch reasoning, no tool surface.
- #12 Verify post-amendment state from code — judgment-shaped post-build review.
- #13 Critical thinking on deviations — meta-reasoning.
- #14 Asymmetric problem solving — observation-shaped.
- #15 Loose AC text → fix the AC — post-build judgment.
- #16 Strict autonomy — turn-shape, not tool-shape.
- #21 Amendment dispatch speedups — dispatch-prompt content, not tool-call shape.
- #23 Update CLAUDE.md after corrections — recall-shaped.
- #24 Lead with the answer / numbered lists / no filler — voice/tone.
- #25 Sonnet for routine tasks — model-routing rubric.
- #27 FUTURE_IDEAS_DRAFT capture — capture-discipline.

Record in CLAUDE.dev.md or the CDCs section of FUTURE_IDEAS.md as "rules that are inherently advisory; not candidates for structural promotion." This forecloses re-litigation.

---

## 11. Open questions for owner

Beyond the 5 numbered decisions above, two adjacent matters surfaced during research that may want owner input but are not load-bearing for the programme:

- **Q1:** is `structural-enforcement/` a new sealed peer component, or a sub-component within `hands-off-lifecycle/`? Bears on D3-(a) integration. Recommendation: sub-component within `hands-off-lifecycle/hooks/structural/`. Composes with first-run-hook + agent-file-authoring substrate already there.
- **Q2:** does the audit log (§3.5) get retained indefinitely, or rolled up into objective-tracker events with periodic JSONL truncation? Recommendation: latter — JSONL is the streaming write surface; objective-tracker is the durable surface; weekly rollup + truncation.

Neither blocks A1 dispatch. Both can be answered in A1's proposal.

---

## 12. Cross-references

- `docs/odd-methodology.md` §5 (structural over advisory; clause-(g) pattern; Pydantic + model_validators reach-for default)
- `docs/odd-in-pos.md` §4 (clause-(g) worked example)
- `docs/rebuild/spec/pos-v2-objectives-spec.md` line 134–135 (Tiered determinism objective + audit-on-rule-where-hook-would-work acceptance)
- `docs/rebuild/VALUE_PROPOSITION.md` (AC.PO.1 + AC.PO.2; Lens 2)
- `docs/rebuild/FUTURE_IDEAS.md` Idea 8 (structural context-load gate — promoted to A1 in this programme)
- `CLAUDE.dev.md` (DEV MODE / NORMAL USE partition; dev-mode-manifest.yaml — the workspace-mode bit substrate)
- `tools/pos-amend/README.md` (amendment-cycle bookkeeping; dry-run gate composes with A4)
- `objective-tracker/src/spec.py` and `store.py` (existing substrate D3-(a) extends)
- `~/.claude/projects/-Users-lukeivers-pos3/memory/MEMORY.md` (the 25 feedback bullets audited in §2)
- Claude Code hook docs (https://code.claude.com/docs/en/hooks) — 28 hook events; PreToolUse decision-control surface; SessionStart additionalContext

---

*End of research artefact.*
