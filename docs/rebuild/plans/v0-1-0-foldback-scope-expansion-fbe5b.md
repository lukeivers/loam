# FBE.5b sub-plan — make `<workspace>/.claude/` actually scaffold

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-03.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` (FBE.5b row to be backfilled in §8 register; see end-of-doc note in §1).
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md`.
**Predecessors:** FBE.{1,2,2b,3,4,5,7} all sealed (`21b9480`, `8d2b770`, `47ccb3a`, `becf183`, `99c03a6`, `bc56f0d`, `a102bde`).
**BASELINE (pre-build tip):** `15fe647` — current canonical pos-v2 HEAD (the FBE.2b parent §8 backfill commit).

---

## 1. Summary / TLDR

FBE.5's Surface #7 documented a §2.5 violation: `loam init` prints `"  .claude/    ← scaffolded (Claude Code expects this here)"` to the user, but no code path actually creates `<workspace>/.claude/` on disk. Verified at:

- `framework/loam-init/src/loam/loam_init/cli.py:128` — CLI claims it.
- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py:508` — `claude_dir = new_ws_path / ".claude"` is computed (and returned in `BootstrapResult`), but no `mkdir` call exists for it.
- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py:943-944` — the auto-scaffolded `<workspace>/.gitignore` already whitelists `!.claude` + `!.claude/**` for tracking.

Real v0.1.0 BLOCKER: FBE.6's planned extended smoke (parent plan §4 FBE.6.3) explicitly checks `ls /tmp/loam-fbe6-test-ws/{framework,workspace,.claude}` — without a fix it will fail. Stranger-clone install that doesn't scaffold `.claude/` doesn't load the persona properly when they run `claude` from inside the workspace (Lens 2 violation).

**Dispatcher (Luke, owner) rules MINIMAL scope:** `mkdir <workspace>/.claude/` + write a default `settings.json`. Explicitly NOT full hooks-pointing-at-framework + agents/ subdir + persona seed; that's v0.1.x territory.

This is purely "make the existing lie true" — single-file source change in `bootstrap_new_workspace`, no new ports/deps/components.

**Note on §8 register backfill:** the parent foldback plan-doc names FBE.5b only in the closing line ("Remaining sequence: FBE.5b ... if dispatched"). Full §8 register entry will be added at backfill time via the universal-paths admission (post-seal commit, mirroring FBE.2b precedent).

---

## 2. Halt-and-surface BEFORE build

### Surface #1 (no halt — recorded; minimum-content for `settings.json` is `{}`)

Survey of existing Claude Code workspace `.claude/settings.json` files on this dev host shows they are all rich (agent + permissions + hooks). However, Claude Code's documented behaviour is: any project-level `.claude/settings.json` is consumed if present; the file may be empty JSON (`{}`). Empty `{}` is valid and unambiguously says "no project-level overrides; defer to user-level settings + Claude Code defaults". The dispatcher's brief explicitly authorises `{}` as the "minimum if Claude Code accepts it" outcome.

**Verification approach:** ship `{}` (with a trailing newline + 2-space indent — the conventional shape so a human or automation editing it later doesn't see a stylistic surprise). Empirically verified that JSON parsers (and Claude Code, per its documented permissive-merge semantics) accept `{}`. Adding any field beyond `{}` would be a substantive opinion (e.g. picking an `agent` handle other than the ones the workspace's persona scaffold installs) — out of scope for "minimal" per the dispatcher's brief.

### Surface #2 (no halt — recorded; idempotency contract)

`bootstrap_new_workspace` is called both fresh AND with `init_existing=True` (the `--init-existing` re-scaffold path). The `mkdir(claude_dir, exist_ok=True)` + conditional `settings.json` write must be idempotent — re-invocation on a workspace whose `.claude/settings.json` already exists must NOT overwrite it (the operator may have customised it after first scaffold). Idempotency follows the `_write_workspace_gitignore` precedent (lines 948-961 of `first_run_scaffold.py`): "scaffold if absent, else no-op". This composes with AC.D.4.2 (init-existing is idempotent) — the existing `test_AC_D_4_2_init_existing_is_idempotent` test will catch a regression here.

### Surface #3 (no halt — recorded; the existing `test_AC_D_4_1_local_path_form` test asserts `.claude_dir` location but NOT existence)

The current test at `framework/workspace-bootstrap/tests/test_pos_new_workspace.py:192-197` carries an inline comment: `"The scaffold doesn't create .claude/ directly today (it's part of workspace-bootstrap's separate path); verify .claude_dir is named at the right location even if the directory itself isn't yet populated"`. Post-FBE.5b the directory IS created — the comment becomes stale and the assertion can be tightened from "is named" to "is named AND exists with settings.json present". This is part of FBE.5b's AC surface (AC.FBE.5b.3 — see §4); not a halt.

### Surface #4 (no halt — recorded; CLI prose at `cli.py:128` becomes truthful, no edit needed)

The CLI message at `framework/loam-init/src/loam/loam_init/cli.py:128` ("  .claude/    ← scaffolded (Claude Code expects this here)") becomes accurate post-fix; same for `pos-new-workspace`'s mirror message at `new_workspace.py:724`. No CLI prose edit needed — the prose was correct in intent, the implementation was the lie. ODD §2.5 outcome: CLI claim and runtime behaviour now align.

### Surface #5 (no halt — recorded; FBE.6 extended-smoke `ls` check now passes)

The parent plan §4 FBE.6.3 step-list contains `ls /tmp/loam-fbe6-test-ws/{framework,workspace,.claude}` as the post-`loam init` verification. Pre-FBE.5b this would fail (`.claude/` absent). Post-FBE.5b it passes. This is the operational reason FBE.5b is being dispatched separately ahead of FBE.6: FBE.6 is gated on this fix.

---

## 3. Spec-objective placement

**Binds to:**
- **AC.PO.1 + AC.PO.2** (prime objective per `docs/rebuild/VALUE_PROPOSITION.md`) — closing the "stranger-clone install + first-run looks right but Claude Code session-start doesn't find a workspace `.claude/`" failure mode that Lens 2's primary-persona test exposes.
- **Reviewer foldback Surface #7 (FBE.5 status)** — recorded as "FBE.6 reviewer-flag candidate or FUTURE_IDEAS_DRAFT candidate"; dispatcher upgraded it to its own FBE step (FBE.5b) once the FBE.6.3 smoke dependency was named.
- **AC.FBE.5b.* (this plan §4)** — every AC ladders to the same parent.

**Ladders to:** AC.FBE.5b.* → AC.FBE.6.3 (extended smoke) → AC.OSS-M11a.* (FBE.6 reviewer GO) → M12 publish-flip → AC.PO.1 + AC.PO.2.

---

## 4. Acceptance criteria (FBE.5b.*)

AC family `AC.FBE.5b.*` — collision-safe (verified: no prior amendment uses `AC.FBE.5b.*`).

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.FBE.5b.1** | After `bootstrap_new_workspace(...)` returns successfully, `<new-ws-path>/.claude/` exists as a directory. | `(new_ws / ".claude").is_dir()` in the AC.D.4.1 local-path test post-FBE.5b. |
| **AC.FBE.5b.2** | After `bootstrap_new_workspace(...)` returns successfully, `<new-ws-path>/.claude/settings.json` exists, contains valid JSON parsing to `{}` (an empty object), and is mode `0o644`. | `json.loads((new_ws / ".claude" / "settings.json").read_text()) == {}` and `(new_ws / ".claude" / "settings.json").stat().st_mode & 0o777 == 0o644`. |
| **AC.FBE.5b.3** | Idempotency: calling `bootstrap_new_workspace(..., init_existing=True)` on an already-bootstrapped workspace does NOT overwrite an operator-customised `.claude/settings.json`. The "scaffold if absent" pattern is structural. | New test (`test_AC_FBE_5b_3_init_existing_preserves_claude_settings`) — first invocation; mutate `.claude/settings.json` to a non-`{}` payload; second invocation with `init_existing=True`; assert content unchanged. |
| **AC.FBE.5b.4** | Smoke verification: `loam init /tmp/test-fbe5b-ws --from /Users/lukeivers/ivers-corp-pos-v2/` (invoked from a fresh shell against the post-seal canonical tree) succeeds with exit 0 AND produces `/tmp/test-fbe5b-ws/.claude/settings.json` (the file content is `{}` plus newline; the directory permissions are operator-readable). Cleanup the test workspace post-verify. | Manual shell invocation against `/Users/lukeivers/ivers-corp-pos-v2/.venv/bin/loam`; capture stdout + exit code + post-invocation `cat /tmp/test-fbe5b-ws/.claude/settings.json` + cleanup. Result documented in the FBE.5b status file. |
| **AC.FBE.5b.5** | Negative AC — no scope expansion. The fix touches ONLY `bootstrap_new_workspace` (one new helper or two-line addition) + the existing AC.D.4.1 test (tighten the comment + assertion) + ONE new idempotency test. Specifically NOT touched: hooks (no SessionStart/Stop/UserPromptSubmit hook entries written into the scaffolded `settings.json`), `.claude/agents/` subdir (not created), `.claude/personas/` subdir (not created), any other Claude-Code-discoverable directory. | `git diff BASELINE..SEAL_COMMIT --stat` shows changes only in: `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py`, `framework/workspace-bootstrap/tests/test_pos_new_workspace.py` (existing test tighten + ONE new test), `framework/workspace-bootstrap/tests/SEAL_COMMIT` + `framework/workspace-bootstrap/tests/SEAL_COMMIT.notes`, `framework/workspace-bootstrap/tests/test_no_sealed_amendments.py` (BASELINE bump), and the plan/manifest files. |
| **AC.FBE.5b.6** | The CLI summary message at `framework/loam-init/src/loam/loam_init/cli.py:128` and `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py:724` ("  .claude/    ← scaffolded (Claude Code expects this here)") becomes truthful at runtime; no edit to the messages themselves needed. | Smoke (AC.FBE.5b.4) verifies the message + the actual on-disk shape; the message stayed the same line-for-line; `git diff BASELINE..SEAL_COMMIT -- framework/loam-init/` shows zero changes; `git diff BASELINE..SEAL_COMMIT -- framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py` shows no edit to the cli_main success-summary block (lines 707-742). |
| **AC.FBE.5b.S** | Sealed-component fence: SINGLE component, `framework/workspace-bootstrap/`. The fix lives in `bootstrap_new_workspace` (workspace-bootstrap is the right fence per ODD discipline — the place where the lie currently lives, not a NEW codepath in loam-init). | `git diff BASELINE..SEAL_COMMIT --name-only` produces only paths under: (a) `framework/workspace-bootstrap/`, (b) `docs/rebuild/plans/` (sub-plan + manifest + parent backfill via universal prefix). |

**ACs deliberately out of scope (NOT in FBE.5b):**
- Hooks pointing at framework code (any `PreToolUse` / `UserPromptSubmit` / `Stop` / `PreCompact` / etc. entries — v0.1.x territory).
- `.claude/agents/` subdirectory + agent definitions.
- `.claude/personas/` or `.claude/skills/` subdirectories.
- Any settings.json key beyond the bare `{}` (e.g. `agent`, `permissions`, `enabledMcpjsonServers` — opinions out of scope).
- Edits to the loam-init CLI summary prose (the prose was correct in intent; the runtime was the lie).
- Edits to `framework/loam-init/` source — the fix lives in workspace-bootstrap (the actual scaffold owner per fence discipline).

---

## 5. Three-lens analysis

### Lens 1 — Claude-leverage-first
The fix is *exactly* a Claude-leverage primitive: scaffolding the directory Claude Code expects at workspace root so the harness composes cleanly. Pre-fix, Claude Code can't find a workspace-level `.claude/`; post-fix it does. Lens 1 PASS — the entire fix's existence is to make Claude Code's existing workspace-discovery primitive work at the documented location.

### Lens 2 — Harness + primary-persona value
- **Primary-persona test:** PASS. Removes the friction of "stranger clones loam, runs `loam init`, then `cd <ws> && claude` and the persona doesn't load because `.claude/` is missing". Translation burden drops materially.
- **Harness test:** PASS. The toolkit gains a structural promise — the `.claude/` path is reliably present after `loam init`, so future amendments (hooks, agents, persona seeds) have a stable target to compose on.

### Lens 3 — ODD authoring
Outcome ACs only (§4); method (which exact helper function shape, where in `bootstrap_new_workspace`'s flow the call goes) is the builder's call but constrained by the existing `_write_workspace_gitignore` shape (mirror it). The CLI prose claim's truthfulness is the prime outcome; "use a helper named `_scaffold_claude_dir`" is method, NOT in the AC text.

### Lens 4 — Prompt scope ↔ confidence
High confidence in outcome shape: dispatcher named the AC set + the minimum-content rule + the smoke verification. Tight scope. Method is inferable from constraints (the existing `_write_workspace_gitignore` is the mirror; `mkdir(..., exist_ok=True)` + conditional write is one short helper).

### Lens 5 — Swarming
FBE.5b is a leaf. ACs do not partition further: each binds to a single observable surface (directory existence, file content, idempotency, smoke, fence diff). No sub-decomposition; the source change is ~10 LOC + 1 new test + 1 existing-test tighten.

---

## 6. File-by-file map

### Source change (in fence — `framework/workspace-bootstrap/`):

- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py` — add a helper function `_scaffold_claude_dir(claude_dir: Path) -> bool` mirroring `_write_workspace_gitignore`'s shape (in `first_run_scaffold.py:948-961`): create `claude_dir` if absent (`mkdir(parents=True, exist_ok=True)`); write `settings.json` if absent; return `True` if newly created, `False` otherwise. Call it from `bootstrap_new_workspace` AFTER step 6 (the `run_first_run_scaffold` invocation) so the workspace-state directory is fully scaffolded first. The returned `BootstrapResult.claude_dir` field already exists (line 580); no signature change.

  Helper content (method-level, shown for plan-doc completeness — builder may refine):
  ```python
  _CLAUDE_SETTINGS_JSON_TEMPLATE = "{}\n"

  def _scaffold_claude_dir(claude_dir: Path) -> bool:
      """Scaffold ``<workspace>/.claude/`` if absent.

      Idempotent: if ``settings.json`` already exists, leaves it
      untouched (the operator may have customised it). Returns True
      iff the directory was newly created OR the settings.json was
      newly written.
      """
      created = False
      if not claude_dir.exists():
          claude_dir.mkdir(parents=True, exist_ok=True)
          created = True
      settings = claude_dir / "settings.json"
      if not settings.exists():
          settings.write_text(_CLAUDE_SETTINGS_JSON_TEMPLATE,
                              encoding="utf-8")
          settings.chmod(0o644)
          created = True
      return created
  ```

  Invocation site: in `bootstrap_new_workspace`, after the `run_first_run_scaffold` block (after the line that catches `Exception` and re-raises `ScaffoldFailedError`), BEFORE the `return BootstrapResult(...)` block — i.e. between line ~574 and line ~576 (pre-FBE.5b numbering). Single new line: `_scaffold_claude_dir(claude_dir)`.

### Test changes (in fence):

- `framework/workspace-bootstrap/tests/test_pos_new_workspace.py` — tighten the AC.D.4.1 local-path test (`test_AC_D_4_1_local_path_form_produces_d_shape`, lines 192-197 pre-FBE.5b): replace the inline comment `"The scaffold doesn't create .claude/ directly today..."` with the post-FBE.5b reality + add a positive `assert (new_ws / ".claude").is_dir()` assertion + `assert (new_ws / ".claude" / "settings.json").exists()` + `assert json.loads(...) == {}`. Add `import json` if absent. (`feedback_loose_AC_text_fix_AC_not_implementation` precedent — tighten the AC text once the implementation matches the intent.)

- `framework/workspace-bootstrap/tests/test_pos_new_workspace.py` — ADD a new test `test_AC_FBE_5b_3_init_existing_preserves_claude_settings` covering AC.FBE.5b.3 idempotency: bootstrap fresh; mutate `<new-ws>/.claude/settings.json` to a non-`{}` payload (e.g. `{"agent": "test-handle"}`); re-invoke with `init_existing=True`; assert the file's content survived unchanged.

### Sidecar bumps within sealed-component fence (1 total):

- `framework/workspace-bootstrap/tests/SEAL_COMMIT` advances to FBE.5b seal SHA via `loam amend seal`.
- `framework/workspace-bootstrap/tests/test_no_sealed_amendments.py` BASELINE literal bumps via `loam amend apply` (mirrors FBE.5 precedent — apply rewrites `BASELINE = ...` to the pre-apply tip).
- Narrative file at `framework/workspace-bootstrap/tests/SEAL_COMMIT.notes` (single fence component → narrative target is the fence's own sidecar notes file; this is the first FBE-step where workspace-bootstrap is a single-fence amendment, so no shared narrative target with other components).

### Plan-doc + manifest (universal_paths.prefixes: `docs/rebuild/plans/`):

- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe5b.md` (this file).
- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe5b.manifest.yaml`.

### Parent plan-doc backfill (post-seal, separate commit):

- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` — §8 method-decision register: ADD a new `### FBE.5b — <workspace>/.claude/ scaffold gap closed` subsection with apply commit SHA + seal commit SHA + verification summary; also update the closing "Remaining sequence:" line to drop FBE.5b (now done) and lead with FBE.6.

**TOTAL fence diff:** ~15 LOC source addition (one helper + one call site + one constant + import-line touchups if any) + 1 existing test tighten (~5 lines) + 1 new test (~25 lines) + 1 sidecar `SEAL_COMMIT` bump + 1 BASELINE literal bump + 1 SEAL_COMMIT.notes narrative + plan-doc + manifest YAML + parent plan §8 backfill.

---

## 7. Smoke verification

**Smoke (AC.FBE.5b.4):** runs POST-seal so it exercises the seal-bumped tree.

```
# Smoke proper
rm -rf /tmp/test-fbe5b-ws
/Users/lukeivers/ivers-corp-pos-v2/.venv/bin/loam init /tmp/test-fbe5b-ws \
    --from /Users/lukeivers/ivers-corp-pos-v2/
echo "Exit: $?"

# Verify scaffolded structure
ls /tmp/test-fbe5b-ws/.claude/
cat /tmp/test-fbe5b-ws/.claude/settings.json

# Cleanup
rm -rf /tmp/test-fbe5b-ws
```

Expect:
- `loam init` exits 0.
- `/tmp/test-fbe5b-ws/.claude/settings.json` exists, contains `{}` + newline.
- The CLI summary printed `"  .claude/    ← scaffolded (Claude Code expects this here)"` and the file system agrees.

**Failure modes:**
- `loam init` exits non-zero → regression (FBE.5b broke an upstream contract). Halt; surface; do not iterate.
- `/tmp/test-fbe5b-ws/.claude/` missing post-invocation → fix didn't land; halt.
- `settings.json` content is anything other than `{}\n` → method drift from the AC; halt.

---

## 8. Hard constraints

- 1 sealed-component sidecar in fence (workspace-bootstrap). Single source change + 1 existing test tighten + 1 new test.
- No new external runtime deps.
- No `git commit --amend` per `feedback_no_amend_in_agent_dispatches`.
- `loam amend apply` invoked BEFORE seal commit per `feedback_dispatch_explicit_pos_amend_apply`.
- AC-prefix `AC.FBE.5b.*` (collision-safe).
- Auto-memory `MEMORY.md` NOT touched.
- Component-scoped test rerun per `feedback_amendment_dispatch_speedups`: only `framework/workspace-bootstrap/tests/` runs post-seal.
- Per FBE.4/FBE.5 partner-prefix gap precedent: workspace-bootstrap was the partner-prefix-compliant component during FBE.5's fence-fifteen; single-component FBE.5b should not trigger the gap (the apply tool's derivation `framework/<name>/` matches `framework/workspace-bootstrap/`). If it does surface, apply corrective hand-admit per FBE.4 recipe.
- Negative AC.FBE.5b.5: no scope expansion (no hooks, no agents/, no persona seed). The fix is purely "make the existing CLI claim true."
- ODD §2.5 — every line of the fix maps to AC.FBE.5b.{1,2,3}. No defensive code for cases ACs don't name.

---

## 9. Out of scope (per ODD §2.5)

- Hooks pointing at framework code (`SessionStart`, `Stop`, `UserPromptSubmit`, `PreCompact`, etc.) — v0.1.x.
- `.claude/agents/` subdirectory + agent definitions — v0.1.x.
- `.claude/personas/` / `.claude/skills/` / `.claude/commands/` subdirectories — v0.1.x.
- Any settings.json key beyond `{}` (`agent`, `permissions`, `enabledMcpjsonServers`, etc.).
- Edits to the loam-init CLI summary prose (the prose was correct; the runtime was the lie).
- Edits to `framework/loam-init/src/` source (fix lives in workspace-bootstrap).
- Behaviour code edits anywhere else.

---

## 10. Halt-and-surface (during build)

Per `feedback_subagent_odd_violation_halt`:

- **HT-1:** Fix touches `framework/loam-init/` source (wrong fence — the lie lives in workspace-bootstrap, not loam-init). Halt; surface; reread §1 source trace.
- **HT-2:** `loam init` smoke (AC.FBE.5b.4) returns non-zero. Halt; surface; FBE.1/FBE.5/FBE.5b regression candidate.
- **HT-3:** Minimum settings.json content turns out non-trivial (Claude Code requires more than `{}`). Halt; surface; the "minimal" framing might need re-decision per dispatcher's halt trigger.
- **HT-4:** Sealed-component fence breach beyond `framework/workspace-bootstrap/`. Halt; surface; the fix should be single-fence per §1.
- **HT-5:** Scope expansion temptation lands (e.g. agent named in scaffolded settings.json). Halt; surface; AC.FBE.5b.5 violation.
- **HT-6:** `loam amend apply` rejects the manifest. Halt; surface; manifest shape may need adjustment.
- **HT-7:** `loam amend seal` rejects the seal. Halt; surface; usually a touched-file outside fence + universal admissions; if partner-prefix gap recurs (per FBE.4 precedent `0c4d9a0`), apply hand-corrective.
- **HT-8:** Surrounding-code ODD §2.5 violation discovered in any touched file. Halt; surface; do NOT silently extend or fix in-band.
- **HT-9:** Wall-time exceeds 50 min. Halt with partial findings.
- **HT-10:** WD drifts to pos3. Halt immediately.

---

## 11. Risks

- **Risk: Claude Code requires more than `{}` in settings.json.** Mitigation: ship `{}`; if Claude Code emits a warning on session-start, surface it (HT-3); the dispatcher can re-rule.
- **Risk: Existing AC.D.4.1 test's comment was correct: scaffold "doesn't create .claude/ directly today" — tightening it might surface a coupling we missed.** Mitigation: the comment was descriptive of the bug, not prescriptive of the design. Tightening is the correct response per `feedback_loose_AC_text_fix_AC_not_implementation`.
- **Risk: `loam amend apply` partner-prefix gap recurs.** Mitigation: workspace-bootstrap's prefix is the canonical `framework/<name>/` shape — apply tool should derive cleanly; apply with watchful eye, hand-correct if needed.
- **Risk: Test-only override paths** (`tracker_seed_runner=`, `service_manager_dir_override=`, etc.) **don't exercise the new helper.** Mitigation: the helper is unconditional in `bootstrap_new_workspace`'s flow (post-scaffold, pre-return) — every test that calls `bootstrap_new_workspace` will exercise it.

---

## 12. Sequencing (commit ladder)

1. **Plan-doc commit** (this file authored alone, NEW commit).
2. **Source + test edit commit** — single commit covering: source-side helper addition + invocation site + existing AC.D.4.1 test tighten + NEW idempotency test.
3. **Manifest commit** — author `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe5b.manifest.yaml` (single component in `components:` block: workspace-bootstrap).
4. **`loam amend apply`** — invoke against the manifest. Produces apply-bookkeeping commit (BASELINE bumps in workspace-bootstrap's `test_no_sealed_amendments.py`; sidecar `SEAL_COMMIT` advances to BASELINE).
5. **`loam amend seal`** — produces deterministic seal commit; sidecar `SEAL_COMMIT` advances to seal SHA; narrative file written at `framework/workspace-bootstrap/tests/SEAL_COMMIT.notes`.
   - **If seal fails on partner-prefix gap (Surface #3 of FBE.5):** apply corrective hand-admit per FBE.4 recipe (`0c4d9a0`) — single-file edit to the offending fence-test's `allowed_prefixes`; commit; re-run seal.
6. **Smoke verification (AC.FBE.5b.4)** — POST-seal; verify shipped behaviour against the seal-bumped tree.
7. **Parent plan-doc backfill** — `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` §8 add `### FBE.5b` subsection with apply + seal SHAs + drop FBE.5b from the closing "Remaining sequence:" line (separate NEW commit; admitted via `docs/rebuild/plans/` universal prefix).
8. **Status file write** — `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe5b-status-2026-05-03.md` with seal report.

NO `git commit --amend` at any point. NO push to any remote.

---

## 13. References

- **Parent plan:** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` (FBE.5b named in closing line; §8 register backfilled at completion).
- **FBE.5 status (Surface #7 origin):** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe5-status-2026-05-03.md`.
- **FBE.5 sub-plan (Surface #7 framing):** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe5.md` §2 Surface #7.
- **Source-trace evidence:**
  - `framework/loam-init/src/loam/loam_init/cli.py:128` (CLI claim).
  - `framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py:508` (claude_dir computed, never mkdir-ed).
  - `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py:943-944` (.gitignore already whitelists .claude).
  - `framework/workspace-bootstrap/tests/test_pos_new_workspace.py:192-197` (existing test asserts location, comment acknowledges the gap).
- **FBE.5 sub-plan / manifest (single-fence ladder precedent):** FBE.2b's `pos-publish-framework-only` single-fence shape is the closest mirror; FBE.5b uses workspace-bootstrap as the single-fence component.
- **Memory bullets honoured:**
  - `feedback_plan_before_code` (this is the plan; no code yet).
  - `feedback_no_amend_in_agent_dispatches` (commit ladder uses NEW commits only).
  - `feedback_dispatch_explicit_pos_amend_apply` (apply step explicit in §12).
  - `feedback_subagent_odd_violation_halt` (HT-1 through HT-10).
  - `feedback_amendment_dispatch_speedups` (test rerun scoped to fence component only).
  - `feedback_summarize_and_surface_decisions` (Surfaces 1-5 explicit).
  - `feedback_specific_claims_verified_or_marked_guess` (every "verified at" claim has a path/line citation).
  - `feedback_loose_AC_text_fix_AC_not_implementation` (AC.D.4.1 test's stale comment + assertion tightened post-FBE.5b).
  - `feedback_critical_thinking_on_deviations` (Surface #1 weighed `{}` vs richer settings.json by outcome × cost × risk).

---

## 14. AI-time band

- Predicted: **15–25 min, midpoint 20 min**; dispatch hard cap 50 min.
- Justification: ~15 LOC source addition (one helper + one call site + one constant) + 1 existing test tighten + 1 new test (~25 lines) + 1 sidecar bump + manifest YAML + apply (single-fence — fastest case) + seal + smoke + parent §8 backfill + status file. Per rubric: amendment-build (single-component, single-source-file, modest test addition) → 10–20 min midpoint 15; widen upper bound for the smoke verification + parent §8 backfill.

---

## 15. Method-decision register (post-build)

(Populated as commits land.)

- Plan-doc commit: `<TBD>`.
- Source + test edit commit: `<TBD>`.
- Manifest commit: `<TBD>`.
- Apply commit: `<TBD>`.
- Corrective commit (if needed): `<TBD>`.
- Seal commit: `<TBD>`.
- Parent plan-doc §8 backfill commit: `<TBD>`.

---

*End of FBE.5b sub-plan-doc. Ready to build.*
