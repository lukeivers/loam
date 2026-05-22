# Amendment #144 — Closed-loop engagement canonical promotion: intent-classifier hook + persona/hook reconciliation + fresh-workspace SKILL discovery audit

**Status:** plan-doc, plan-before-code. Authored 2026-05-21 by `loam-plan-author` subagent per dispatch from owner (TG 11808 build-strategy delegation + TG 11878 closed-loop-engagement directive + TG 11881 slash-command-not-user-facing ruling + TG 11885 proceed-on-your-own ratification).
**Working directory:** `/Users/lukeivers/loam/`.
**Predecessor (load-bearing):** amendment #143 publish-state commit `b2b46a22b0cbdc7580bd9d612015362e682ac9cb` (current HEAD post-publish — `docs(readme): bump current-release to v0.12.20 (amendment #143 tier-1 retroactive sweep follow-on + live sweep)`). Per `D-PASH.BASELINE-WALK` (amendment #142 Scope B): walked forward from #143's seal `f83260f`; found NO `chore(amend-fixup):` commits between `f83260f` and `b2b46a2`; defaulted BASELINE to the publish-state commit `b2b46a2`. **Verified by direct `git rev-parse HEAD` + `git log --oneline f83260f..b2b46a2 --grep='^chore(amend-fixup)'` (empty result).**
**Parent capture:** Today's session uncovered an architectural gap in closed-loop engagement: pos3-local has a working `intent_classifier_inbound.py` UserPromptSubmit hook + a manually-symlinked `handsoff-loop` SKILL into `.claude/skills/`, and a patched persona prompt translate-inbound stanza. Canonical loam ships ONE of these three (the persona prompt stanza) but NOT the hook. The other two pieces (SKILL symlinks + intent classifier) determine whether non-tech users in fresh workspaces engage closed-loop methodology on soft prompts. Tier-0 verification surfaced one critical finding: canonical loam's `_symlink_plugin_skills` (v0.1.7 / AC.LAYERED.2) ALREADY symlinks every plugin-shipped SKILL into `.claude/skills/<name>` at fresh-workspace scaffold time. Fresh workspaces ALREADY get full plugin-skill discovery. The gap is the intent-classifier hook + a persona/hook prescription reconciliation, NOT a SKILL-discovery scaffolding gap.
**Quality bar:** multi-component amendment (`primary-persona` for hook authoring + CLI subcommand + persona prompt edit; `hands-off-lifecycle` for multi-contributor `merge_user_prompt_submit` generalization analogous to amendment #45's SessionStart). Three AC sub-families (AC.CLE.HOOK / AC.CLE.RECONCILE / AC.CLE.SCAFFOLD-AUDIT) per scope + one outcome-altitude smoke (AC.CLE.S) exercising the end-to-end engagement path: fresh workspace scaffolds → SKILL is discoverable → soft user prompt arrives → hook injects classification → persona engages `handsoff-loop` SKILL.

---

## §1. Objective / Summary / TL;DR

Close the closed-loop-engagement architectural gap surfaced this session — non-tech users in fresh workspaces typing soft phrasing (*"I want a tool that does X. show me it works"*) must engage the closed-loop methodology (`handsoff-loop` SKILL) without the user knowing or typing any slash command. Three merged scopes:

1. **Scope A — promote the pos3-local `intent_classifier_inbound.py` UserPromptSubmit hook to canonical primary-persona.** Today's pos3 hook (at `.claude/hooks/intent_classifier_inbound.py`) classifies user prompts as `build-with-verification` / `pure-question` / `tiny-tweak` / `ambiguous` via deterministic regex (no LLM call, <5ms), and on `build-with-verification` emits `additionalContext` that prepends to the model context with a directive to invoke the `handsoff-loop` SKILL. The hook is structural enforcement of the persona prompt's translate-inbound stanza (lines 397-454 of canonical `prompt.md`); the persona prompt alone proved insufficient across four iterations of the Eric-demo smoke. **Promote:** copy the hook source into a canonical home under `framework/primary-persona/` (most likely `framework/primary-persona/src/loam/primary_persona/intent_classifier.py` with a wrapping CLI subcommand); wire it into the UserPromptSubmit stanza alongside the existing `primary_persona.cli user-prompt-submit` entry; generalize `merge_user_prompt_submit` to multi-contributor (mirroring amendment #45's SessionStart generalization at #45.2/#45.3).

2. **Scope B — reconcile the persona-prompt translate-inbound stanza with the intent-classifier hook's `additionalContext` prescription.** Canonical persona prompt lines 433-443 prescribe: *"When the build-with-verification intent classifier fires, my FIRST move is to invoke the matching SKILL by typing its slash command verbatim into my response — `/handsoff-loop`."* Today's pos3 hook template prescribes the OPPOSITE: *"the slash command is available as a backup invocation if auto-load doesn't fire; otherwise it's redundant + leaks to the user's chat view."* Owner ruling TG 11881 codifies the hook's stance: slash command is not user-facing. The two prescriptions are in direct conflict at the structural-enforcement layer. **Reconcile:** rewrite the persona prompt's translate-inbound stanza to match the hook's prescription (no verbatim slash command; persona FOLLOWS the auto-loaded SKILL's procedure). The persona prompt's translate-inbound stanza remains the documented version of the rule; the hook is the structural backstop; both speak the same prescription.

3. **Scope C — audit + document the fresh-workspace SKILL discovery path; produce an operator-facing rescaffold mechanism for pre-existing workspaces (pos3 case).** Tier-0 verification: canonical loam's `_symlink_plugin_skills` (`framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py:1224`) already symlinks every plugin-shipped SKILL (all 21 in `plugins/loam-skills/skills/`) into the fresh workspace's `.claude/skills/<name>/`. AC.LAYERED.2 + AC.LAYERED.3 + AC.LAYERED.4 cover the collision semantics. Fresh workspaces ALREADY get the discovery; this is NOT a canonical gap. **However**, pos3 was scaffolded before v0.1.7 landed AND first-run scaffolding is idempotent (won't re-run), so pos3's `.claude/skills/` carries only the manual `handsoff-loop` symlink + three workspace-local SKILLs. The gap is operator-side (existing workspaces don't auto-upgrade) not scaffolder-side. **Audit deliverable:** add a release-process check (AC.CLE.SCAFFOLD-AUDIT.1) that asserts the canonical scaffold-output set includes `handsoff-loop` discoverability AND the other 20 plugin-shipped SKILLs. **Operator-facing rescaffold:** add a one-shot `loam workspace rescaffold-skills` CLI verb (or extend an existing `loam workspace` surface) that re-runs `_symlink_plugin_skills` against an existing workspace; idempotent + collision-aware per the existing AC.LAYERED rules. This is the operator's recovery path when a pre-v0.1.7 workspace finds itself with missing plugin SKILLs.

**Shape decision: merged single amendment** (per F4 scope-confidence + Lens 5 swarming stopping criterion). The three scopes are scope-disjoint at the AC family level (.HOOK / .RECONCILE / .SCAFFOLD-AUDIT) but causally linked: Scope A's hook prescribes "no slash command needed" — Scope B has to reconcile the persona prompt or the persona will type `/handsoff-loop` AGAINST the hook's `additionalContext` (the two would race at runtime); Scope C's audit verifies that Scope A's hook actually fires in a fresh workspace (the SKILL must be discoverable for the hook's `additionalContext` to land on a SKILL Claude Code can match). Splitting yields three apply+seal cycles where merging yields one. Multi-component fence (`primary-persona` for the hook + persona-prompt edit; `hands-off-lifecycle` for the UserPromptSubmit multi-contributor generalization; `workspace-bootstrap` for the rescaffold CLI verb in Scope C; `release-process` consumer doc for the audit) follows the surfaces touched.

**Owner-ratification record (per `feedback_record_owner_ratification_before_dispatch`):**

| msg-ID | ts (UTC, ~) | Owner ruling |
|---|---|---|
| TG 11808 | 2026-05-21T~16:14Z | Build-strategy delegation — persona dispatches build work autonomously on in-scope authorized items. |
| TG 11878 | 2026-05-21T~23:00Z | Closed-loop engagement directive: non-tech users typing soft prompts must engage closed-loop methodology in fresh workspaces. |
| TG 11881 | 2026-05-21T~23:10Z | Slash command is NOT user-facing — `/handsoff-loop` typed verbatim into the persona response would leak to the user's chat view. The persona should not type it; auto-load is the path. |
| TG 11885 | 2026-05-21T~23:20Z | Proceed-on-your-own autonomy ratification for this amendment cycle. |

**Pre-flight verification (Tier-0 at canonical HEAD `b2b46a2`, 2026-05-21):**

- **`git rev-parse HEAD` returned `b2b46a22b0cbdc7580bd9d612015362e682ac9cb`.** Full SHA verified by direct `git rev-parse` invocation. Recorded as BASELINE in the paired manifest. **Verified by direct shell invocation.**
- **`git log --oneline f83260f..b2b46a2 --grep='^chore(amend-fixup)'` returned empty.** No fixup commits between #143 seal `f83260f` and publish-state `b2b46a2`. BASELINE walk-forward lands on publish-state per #142 Scope B's convention. **Verified.**
- **`_symlink_plugin_skills` already exists in canonical:** `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py:1224-1310`. Symlinks every plugin's `plugins/<plugin>/skills/<name>/` directory (provided `SKILL.md` is present) into `<workspace>/.claude/skills/<name>` as a directory symlink. Idempotent; raises `PluginSkillCollisionError` on workspace-local override OR cross-plugin name collision per AC.LAYERED.3 / .4. **Verified by direct read.**
- **`plugins/loam-skills/skills/` ships 21 SKILLs** including `handsoff-loop`. **Verified by `ls plugins/loam-skills/skills/`.** All ship `SKILL.md` (required by the symlinker; flat-file `<name>.md` shapes are out-of-fence per the line 1264 comment).
- **`intent_classifier_inbound.py` does NOT exist anywhere in canonical loam.** `grep -rn 'intent_classifier' framework/ plugins/ --include='*.py'` returns empty. Only the pos3-local copy exists at `/Users/lukeivers/pos3/.claude/hooks/intent_classifier_inbound.py` (today's patches). **Verified.**
- **Persona prompt translate-inbound stanza already exists** at `framework/primary-persona/templates/persona-template/prompt.md:397-454`. The conflict cited in Scope B is between lines 433-443 (verbatim slash command directive) and the hook's `CANONICAL_FORM_TEMPLATE` (the "no slash command typing required" prescription). **Verified by direct read.**
- **`merge_user_prompt_submit` is single-contributor:** `framework/hands-off-lifecycle/hooks/first_run_settings.py:437-511`. AC46.6 explicitly defers multi-contributor generalization as "a future amendment analogous to #45's SessionStart registry." Scope A is that future amendment. **Verified by direct read + comment confirmation.**
- **`_LOAM_USER_PROMPT_SUBMIT_COMMAND_MARKERS` is single-element** (line 135-139 of `first_run_settings.py`): `("primary_persona.cli user-prompt-submit", "primary_persona.cli user_prompt_submit", "-m loam.primary_persona")` — three substring variants of the same single contributor. Multi-contributor generalization will extend this tuple to recognize the intent-classifier marker alongside the persona's CLI marker. **Verified.**
- **Amendment #45's SessionStart multi-contributor pattern at `_compose_inner_hooks` (line 207-222)** is the reference shape Scope A's UserPromptSubmit generalization follows. Base hook + `extra_inner_hooks: list[dict[str, Any]] | None` parameter; `[base] + extras` composition; empty/None preserves byte-identical legacy shape. **Verified.**
- **Pos3-local existing UserPromptSubmit chain has FIVE hooks** at `/Users/lukeivers/pos3/.claude/settings.json:23-58`: `primary_persona.cli user-prompt-submit` → `principle_reminder.py` → `autonomy_baseline_reset.py` → `queue_status_inject.py` → `intent_classifier_inbound.py`. Only the first IS pos-v2-owned per the canonical marker set; the other four are pos3-local hooks NOT promoted to canonical. Scope A promotes only the intent-classifier (the only one with closed-loop-engagement relevance); the other three pos3-local hooks stay pos3-local. **Verified.**
- **Test fixtures for AC.LAYERED.2/.3/.4** exist at `framework/workspace-bootstrap/tests/test_AC_LAYERED_2_skill_symlink_registration.py` and `test_AC_LAYERED_3_4_skill_collision_halt.py`. The Scope C rescaffold-CLI verb reuses the same `_symlink_plugin_skills` body + raises the same `PluginSkillCollisionError`; new tests for AC.CLE.SCAFFOLD-AUDIT will compose alongside these. **Verified by direct ls.**
- **One pre-existing untracked plan-only file** in working tree: per amendment #143's tail-state, no leftover files expected; canonical is clean. **Verified.**

---

## §2. Predecessors / context

- **Amendment #45** (multi-contributor SessionStart, sealed at the seal commit referenced in `seals/SEAL_COMMIT.true-first-run`). Established the reference shape for SessionStart's multi-contributor envelope (`extra_inner_hooks` parameter, `_compose_inner_hooks` helper, base + extras composition). Scope A's UserPromptSubmit generalization is the analogous extension AC46.6 explicitly anticipated. THIS amendment closes AC46.6's deferred work.
- **Amendment #46** (primary-persona session-start + UserPromptSubmit emitters, sealed). Established `merge_user_prompt_submit` and the `primary_persona.cli user-prompt-submit` contributor. AC46.6 deferred multi-contributor generalization. Scope A extends `merge_user_prompt_submit` with `extra_inner_hooks` per the AC46.6 deferred shape.
- **Amendment v0.1.7 Cycle 3** (layered skill discovery, sealed). Established `_symlink_plugin_skills` (AC.LAYERED.2) + `PluginSkillCollisionError` (AC.LAYERED.3/.4). Scope C's rescaffold-CLI verb composes on top of this existing function; no semantic change to the symlinking — just an operator-callable entry point for pre-existing workspaces.
- **Amendment #142 / D-PASH.BASELINE-WALK** (sealed at `f99827d`, publish-state `b278cc6`). Established the BASELINE walk-forward discipline this amendment dogfoods at its own baseline computation.
- **Persona prompt translate-inbound stanza** at `framework/primary-persona/templates/persona-template/prompt.md:397-454`. Authored earlier this session in canonical (today's earlier work referenced in the dispatch brief). Scope B revises lines 433-443 to remove the verbatim-slash-command directive that conflicts with the hook's prescription. The rest of the stanza (the translation discipline itself, lines 397-432 + 444-454) remains.
- **No other amendment between #46 and #143 has touched the UserPromptSubmit merge path or the translate-inbound stanza in a way that would conflict.** Verified by `git log --oneline --grep='UserPromptSubmit\|intent[_-]classifier\|translate.inbound' 46..b2b46a2` (manual review).

---

## §3. Scope

**In-scope (the three merged sub-scopes):**

**Scope A — promote `intent_classifier_inbound.py` to canonical primary-persona:**

- Author new canonical hook module. **Method-decision per D-CLE.HOOK-LOCATION:** the hook lives at `framework/primary-persona/src/loam/primary_persona/intent_classifier.py` (the classifier + the `additionalContext` template) as a Python module importable from the primary-persona package, NOT as a top-level script in `framework/primary-persona/hooks/` or `plugins/loam-skills/hooks/`. **Reason:** the persona prompt's translate-inbound stanza is canonical primary-persona surface; the hook IS structural enforcement of that stanza; co-locating the classifier with the persona keeps the discipline + its enforcement in one place. **Trade-off:** the hook needs a CLI entry point to be invoked from settings.json — adds a new subcommand `intent-classifier` to the `primary_persona.cli` parser. **Composes with existing primary-persona CLI shape** (the current `user-prompt-submit` / `session-start` / `stop` / `trait-reflection-stop` subcommand chain).

- Add CLI subcommand. Wire `primary_persona.cli intent-classifier` into the existing `cli.py` parser (sibling to `user-prompt-submit`). The subcommand reads Claude Code's UserPromptSubmit JSON envelope from stdin; the body delegates to the new `intent_classifier` module's `main()` function. **Method-decision per D-CLE.HOOK-CLI-SHAPE:** subcommand parameter shape matches `user-prompt-submit` (no extra args; reads stdin, writes JSON to stdout per Claude Code's hook contract). Reuses the existing CLI's argparse infrastructure + workspace-root resolution helper. **Verified shape:** `framework/primary-persona/src/loam/primary_persona/cli.py:80-82` shows the existing pattern.

- Generalize `merge_user_prompt_submit` to multi-contributor. Mirror amendment #45's SessionStart pattern at `framework/hands-off-lifecycle/hooks/first_run_settings.py:_compose_inner_hooks` (line 207-222). New signature: `merge_user_prompt_submit(*, settings_path, base_entry, extra_inner_hooks=None, now_iso=None)`. When `extra_inner_hooks` is None/empty: write `[base_entry]` (byte-identical to current single-contributor shape — preserves AC46.5 backwards compat). When non-empty: write `[base_entry, *extra_inner_hooks]` (base IS the persona's existing user-prompt-submit hook; extras compose after). Update `_LOAM_USER_PROMPT_SUBMIT_COMMAND_MARKERS` to include the new intent-classifier marker substring (`primary_persona.cli intent-classifier`). **Method-decision per D-CLE.MARKER-SHAPE:** marker set extension follows the same alphabetical+CLI-subcommand pattern as the existing entries; no other shape change.

- Update primary-persona's UserPromptSubmit contribution helper (the caller that builds the `new_entry` for `merge_user_prompt_submit`). Add the intent-classifier inner hook as an `extra_inner_hooks` entry. **Method-decision per D-CLE.CONTRIBUTOR-WIRING:** the intent-classifier IS a primary-persona-owned contributor (lives in `primary_persona/`); the wiring stays inside primary-persona's contribution adapter (`framework/primary-persona/src/loam/primary_persona/adapters/` if that pattern exists, otherwise inline in the existing user-prompt-submit emitter). Per amendment #46 §6, the persona's user-prompt-submit emitter is the single source of truth for the persona's UserPromptSubmit contribution; extending it with `extra_inner_hooks=[intent_classifier_entry]` keeps the discipline.

- Test files. New tests at `framework/primary-persona/tests/`:
  - `test_AC_CLE_HOOK_1_classifier_classifies_build_with_verification.py` — unit test exercising the classifier against the eight reference soft phrasings ("I want a tool that does X", "build me a thing", "show me it works", "prove it works", etc.) + verifies anti-trigger cases ("what does X do", "rename this variable") return non-build-with-verification.
  - `test_AC_CLE_HOOK_2_additional_context_template_renders.py` — unit test verifying the `additionalContext` template body matches the expected shape (mentions `handsoff-loop`, mentions no-slash-command-typing, mentions inline-build-is-Lens-2-violation).
  - `test_AC_CLE_HOOK_3_cli_subcommand_writes_hook_output.py` — integration test invoking `python -m loam.primary_persona.cli intent-classifier` with a stdin JSON envelope; verifies stdout is valid Claude Code hookSpecificOutput JSON.
  - `test_AC_CLE_HOOK_4_user_prompt_submit_merge_multi_contributor.py` — `hands-off-lifecycle` test: invoke generalized `merge_user_prompt_submit` with `extra_inner_hooks=[intent_classifier_entry]`; verify settings.json carries both inner hooks in order.

**Scope B — reconcile persona-prompt translate-inbound stanza with hook prescription:**

- Edit `framework/primary-persona/templates/persona-template/prompt.md:433-454`. Replace the verbatim-slash-command directive with the hook-aligned prescription: *"When the build-with-verification intent classifier fires (the UserPromptSubmit hook injects the classification + matching SKILL directive into my context), I follow the auto-loaded SKILL's procedure. I do NOT type the SKILL's slash command verbatim in my response — slash commands are persona-internal mechanism, NOT user-facing output. Auto-load via Claude Code's SKILL matcher is the canonical path; the slash command exists as a manual backup invocation, never as the routing mechanism."*

- **Method-decision per D-CLE.RECONCILE-DIRECTION:** rewrite persona prompt to match the hook prescription, NOT vice versa. **Reason:** TG 11881 ruled that slash commands are not user-facing; the hook's `CANONICAL_FORM_TEMPLATE` already encodes that ruling at the structural-enforcement layer; the persona prompt's verbatim-slash-command instruction predates the ruling and is the surface to update. **Trade-off:** the auto-load path requires Claude Code's SKILL matcher to fire on `additionalContext` — verified by today's session experience (the Skill tool's available-skills list IS populated by Claude Code's matcher reading the SKILL.md files in `.claude/skills/`; `additionalContext` injection plus matcher discovery is the canonical engagement path).

- Tests. **Method-decision per D-CLE.RECONCILE-TEST:** the persona prompt is canonical-template prose; the test asserts the conflicting prescription is absent + the reconciled prescription is present, NOT semantic equivalence. New test at `framework/primary-persona/tests/test_AC_CLE_RECONCILE_1_persona_prompt_no_verbatim_slash_command.py` — asserts `prompt.md` does NOT contain the string `/handsoff-loop` in a directive-to-type context (use a focused substring search like `"typing its slash command verbatim"` — the negative assertion), AND DOES contain the reconciled prescription (substring `"auto-loaded SKILL's procedure"` or equivalent canonical phrase).

**Scope C — fresh-workspace SKILL discovery audit + operator rescaffold:**

- Audit: extend `framework/workspace-bootstrap/tests/test_AC_LAYERED_2_skill_symlink_registration.py` (or add a sibling test) with an explicit `handsoff-loop` discoverability assertion. New test at `framework/workspace-bootstrap/tests/test_AC_CLE_SCAFFOLD_AUDIT_1_handsoff_loop_discoverable_post_scaffold.py` — runs `first_run_scaffold` against a tmpfs workspace pointing at the canonical plugins/ tree; asserts `<workspace>/.claude/skills/handsoff-loop/SKILL.md` is reachable (symlink → real file) AND that the file content matches `plugins/loam-skills/skills/handsoff-loop/SKILL.md`.

- Operator rescaffold CLI verb. **Method-decision per D-CLE.RESCAFFOLD-LOCATION:** add a `loam workspace rescaffold-skills` subcommand to the existing `loam workspace` CLI surface (or to the closest existing operator surface — Tier-0 verification at build time will name the right module). The subcommand body invokes `_symlink_plugin_skills(Path.cwd())` against the current workspace; raises the existing `PluginSkillCollisionError` on collision (operator resolves). **Reason:** `loam workspace` is the existing operator-facing CLI; adding a new top-level command would proliferate surface. **Trade-off:** if `loam workspace` doesn't exist as a verb in `loam_cli`, the next-best home is `loam amend ...` or a new `loam scaffold ...`. **Method-decision deferred** — Tier-0 verification at build time picks the cleanest existing operator surface; default is `loam workspace rescaffold-skills` if `loam workspace` exists, else `loam scaffold rescaffold-skills`.

- Test for rescaffold. New test at `framework/workspace-bootstrap/tests/test_AC_CLE_SCAFFOLD_AUDIT_2_rescaffold_idempotent.py` — sets up a tmpfs workspace with a partial set of symlinked SKILLs (mimics pre-v0.1.7 pos3 state); invokes the rescaffold CLI verb; verifies all 21 plugin-shipped SKILLs are now symlinked + the pre-existing partial set survived (idempotency + operator-override preservation).

- Audit doc update. Append to `docs/release-process.md` (or the canonical release-process surface) a sentence under fresh-workspace verification: *"Verify `_symlink_plugin_skills` symlinks `handsoff-loop` into `.claude/skills/handsoff-loop/` from session-zero (closed-loop engagement gate)."* **Method-decision per D-CLE.RELEASE-PROCESS-DOC:** one-sentence addition, not a new section. Per amendment #142's plan-docs.md hygiene precedent, release-process additions are minimal-surface.

**Out-of-scope (explicitly):**

- The four pos3-local UserPromptSubmit hooks NOT promoted: `principle_reminder.py`, `autonomy_baseline_reset.py`, `queue_status_inject.py`. These are pos3-local discipline hooks (principle self-reminder, autonomy directives, queue surfacing). None of them gate closed-loop engagement; they're orthogonal pos3-local enrichments. **Promotion of these to canonical is a separate amendment cycle** — surfaced here for capture but explicitly deferred. Add to FIDRAFT post-seal.

- The pos3-local Stop chain (`channel_rule_check.py`, `agent_outcome_capture.py`, `autonomy_continuation.py`) — same reasoning; not gating closed-loop engagement.

- The PreToolUse hooks (`translation_jargon_check.py`, `no_closing_line_permission_ask.py`, `filler_posture_check.py`, `idle_close_without_dispatch_check.py`) — same.

- Modifying Claude Code's actual SKILL auto-load matcher behavior. Out of scope (third-party); we compose on top of it.

- Renaming or restructuring the existing 21 plugin SKILLs. Out of scope; the SKILLs work as-shipped.

- Backfilling pos3's `.claude/skills/` automatically. The rescaffold verb (Scope C) IS the operator's path; pos3 is the operator running the verb at their convenience.

---

## §4. Acceptance criteria

| AC ID | Outcome | Verification | Outcome-altitude |
|---|---|---|---|
| **AC.CLE.HOOK.1** | The intent-classifier module classifies a soft `"I want a tool that does X. show me it works"` prompt as `build-with-verification`. | Unit test in `test_AC_CLE_HOOK_1_classifier_classifies_build_with_verification.py` exercises the classifier against ≥8 reference soft phrasings (the eight from the persona prompt translate-inbound stanza line 401-405) + ≥3 anti-trigger cases ("what does X do", "rename Y", "explain Z"); asserts correct classification per case. | false (unit) |
| **AC.CLE.HOOK.2** | When the classifier fires `build-with-verification`, the hook emits a JSON `hookSpecificOutput` with an `additionalContext` field whose body references `handsoff-loop` SKILL + does NOT prescribe verbatim slash-command typing. | Unit test in `test_AC_CLE_HOOK_2_additional_context_template_renders.py` invokes the hook's `main()` against a synthetic stdin payload; parses the stdout JSON; asserts `hookSpecificOutput.additionalContext` is non-empty, contains substring `handsoff-loop`, contains substring `auto-load` or `auto-loaded`, does NOT contain `/handsoff-loop` as a verbatim-type-this directive. | false (unit) |
| **AC.CLE.HOOK.3** | The `primary_persona.cli intent-classifier` subcommand reads UserPromptSubmit JSON from stdin and writes valid hook output JSON to stdout. | Integration test in `test_AC_CLE_HOOK_3_cli_subcommand_writes_hook_output.py` invokes the CLI subcommand as `subprocess.run([sys.executable, '-m', 'loam.primary_persona.cli', 'intent-classifier'], input=<json>, capture_output=True)`; asserts stdout parses as JSON with the expected hook-output shape. | false (integration) |
| **AC.CLE.HOOK.4** | Generalized `merge_user_prompt_submit` with `extra_inner_hooks=[intent_classifier_entry]` writes a settings.json whose `hooks.UserPromptSubmit[0].hooks` array contains BOTH the persona's user-prompt-submit entry AND the intent-classifier entry, in that order. | Integration test in `test_AC_CLE_HOOK_4_user_prompt_submit_merge_multi_contributor.py` writes a fresh settings.json via the generalized merger; parses it back; asserts the inner hooks list shape + ordering. Composes alongside the existing AC46.5 single-contributor test (which must still pass — backwards compat). | false (integration) |
| **AC.CLE.RECONCILE.1** | The canonical persona prompt at `framework/primary-persona/templates/persona-template/prompt.md` does NOT prescribe typing `/handsoff-loop` (or any other SKILL's slash command) verbatim into the persona's response, and DOES prescribe following the auto-loaded SKILL's procedure on build-with-verification intent. | Test in `test_AC_CLE_RECONCILE_1_persona_prompt_no_verbatim_slash_command.py` reads `prompt.md`; asserts the verbatim-slash-command directive substring is absent + the reconciled-prescription substring is present. | false (doc lint) |
| **AC.CLE.SCAFFOLD-AUDIT.1** | A fresh workspace scaffolded via `first_run_scaffold` against the canonical plugins/ tree has `<workspace>/.claude/skills/handsoff-loop/SKILL.md` reachable (symlink resolves) with content matching `plugins/loam-skills/skills/handsoff-loop/SKILL.md`. | Integration test in `test_AC_CLE_SCAFFOLD_AUDIT_1_handsoff_loop_discoverable_post_scaffold.py` runs the scaffold in a tmpfs workspace + asserts the symlink + content equality. Composes alongside the existing AC.LAYERED.2 test (which exercises the general case; this asserts the specific handsoff-loop case). | false (integration) |
| **AC.CLE.SCAFFOLD-AUDIT.2** | The operator rescaffold-skills CLI verb, run against a pre-existing workspace missing some plugin-shipped SKILL symlinks, ends with all 21 SKILLs symlinked AND any pre-existing operator-customized SKILL directories (non-symlink dirs at the target path) untouched (the rescaffold raises `PluginSkillCollisionError` rather than overwriting, per AC.LAYERED.3). | Integration test in `test_AC_CLE_SCAFFOLD_AUDIT_2_rescaffold_idempotent.py` sets up a partial-symlink + one-collision tmpfs workspace; invokes the rescaffold CLI verb (or its underlying function); asserts the partial set is completed AND the collision raises. | false (integration) |
| **AC.CLE.S** | A synthetic end-to-end test scaffolds a fresh workspace against the canonical plugins/ tree, writes a settings.json with the generalized UserPromptSubmit chain (persona + intent-classifier), simulates a soft user prompt arriving via the UserPromptSubmit hook JSON envelope, invokes the intent-classifier subprocess, verifies the resulting `additionalContext` would inject the closed-loop directive into the persona's context AND the `handsoff-loop` SKILL is discoverable from the scaffolded `.claude/skills/`. | Outcome-altitude integration test in `test_AC_CLE_S_outcome_altitude_closed_loop_engagement_path.py` — scaffolds a tmpfs workspace, writes settings.json via the generalized merger, invokes the intent-classifier CLI subprocess with a synthetic build-with-verification prompt envelope; asserts stdout JSON shape + `.claude/skills/handsoff-loop/SKILL.md` is readable. This is the prime-objective ladder: AC.PO.1 + AC.PO.2 in VALUE_PROPOSITION.md depend on non-tech users being able to invoke loam's full power via plain language; this test is the structural verification that the full path engages on a fresh workspace. | **true (outcome-altitude per `feedback_test_outcome_altitude_required`)** |

**AC ladder-up (per `feedback_value_proposition_as_prime_objective`):**

- AC.CLE.HOOK.* ladders to AC.PO.1 (translation-layer reduces translation burden) — the hook converts soft user phrasing into the canonical SKILL-trigger form structurally.
- AC.CLE.RECONCILE.1 ladders to AC.PO.1 + AC.PO.2 — removing the slash-command-leak makes the closed-loop methodology actually user-invisible.
- AC.CLE.SCAFFOLD-AUDIT.* ladders to AC.PO.2 (harness gives the persona the right toolkit) — without the SKILL being discoverable, the persona has nothing to invoke.
- AC.CLE.S is the prime-objective verification: outcome-altitude check that the full end-to-end path engages.

---

## §5. Sealed-component fence

This amendment touches FOUR sealed components:

- **`primary-persona`** — new intent-classifier module + CLI subcommand wiring + persona-prompt edit. Seal-diff window covers `framework/primary-persona/src/loam/primary_persona/` + `framework/primary-persona/templates/persona-template/` + `framework/primary-persona/tests/`.
- **`hands-off-lifecycle`** — multi-contributor generalization of `merge_user_prompt_submit` + marker-set extension + new tests. Seal-diff window covers `framework/hands-off-lifecycle/hooks/first_run_settings.py` + `framework/hands-off-lifecycle/tests/`. **`frozen_baseline: true`** per amendment #23 H19 pin.
- **`workspace-bootstrap`** — new rescaffold-skills CLI verb (or wherever the operator surface lives) + new AC.CLE.SCAFFOLD-AUDIT tests. Seal-diff window covers `framework/workspace-bootstrap/src/loam/workspace_bootstrap/` (CLI module to be named at build time) + `framework/workspace-bootstrap/tests/`.
- **Universal-paths admission** for the cross-component documentation: `docs/plans/` + `docs/release-process.md` (Scope C's audit-doc edit) + `CLAUDE.md` (if a reference to the closed-loop engagement path lands there) + `docs/FUTURE_IDEAS.md` (FIDRAFT entries for the deferred pos3-local hook promotions).

---

## §6. Halt triggers

The builder halts and surfaces if:

1. **Tier-0 verification at build start reveals canonical `_symlink_plugin_skills` is NOT actually running at scaffold time** (i.e., the v0.1.7 line 819 invocation has regressed or been disabled). Halt with the verification command + result; Scope C's audit AC is no longer the right ladder-up. Owner rules whether to re-enable + re-test or re-scope.

2. **Tier-0 verification reveals an existing `framework/primary-persona/src/loam/primary_persona/intent_classifier.py`** that wasn't surfaced by the pre-flight grep. Conflict + halt to clarify whether to extend or replace.

3. **The amendment #45 SessionStart multi-contributor reference shape doesn't directly translate** to UserPromptSubmit because of a UserPromptSubmit-specific schema constraint Tier-0 missed (e.g., Claude Code's UserPromptSubmit dispatch semantics differ from SessionStart's fan-out). Halt with the empirical observation + the Claude Code hook doc reference; owner rules on workaround.

4. **The Scope C operator rescaffold CLI verb has no clean home in any existing `loam_cli` module** — neither `loam workspace ...` nor `loam scaffold ...` exists as a verb surface. Halt and surface: either add a new top-level verb (proliferation cost) or extend an unintuitive surface (cohesion cost). Owner rules.

5. **A pos3-local intent-classifier behavior surfaces during test authoring that wasn't captured in today's hook patches** (e.g., a UserPromptSubmit field name variant that the pos3 code accommodates but canonical migration would drop). Halt with the specific case; either widen the canonical hook to match or surface as a Scope-A-out-of-scope and document.

6. **AC.CLE.S (outcome-altitude) reveals that the `additionalContext` injection alone doesn't reliably trigger Claude Code's SKILL matcher** — i.e., the auto-load path requires more than just `additionalContext` (e.g., requires the user's literal prompt to also match the SKILL description). This is an empirical finding about Claude Code's matcher behavior. Halt with the test result + the additional mechanism observed (e.g., prompt-augmentation rather than additionalContext-only); rescope or extend to include the matcher-engagement piece.

7. **The `merge_user_prompt_submit` multi-contributor generalization breaks AC46.5's existing test** in a way that's not backwards-compat-equivalent at the empty-extras default. Halt and surface; rework the generalization to preserve byte-identical output.

8. **A merge conflict or unexpected test failure surfaces during apply** that the plan didn't anticipate. Standard ODD halt-and-surface per the existing builder discipline.

---

## §7. Ship shape

Single-amendment, single seal cycle. Commit ladder:

1. `<plan-doc + manifest commit (this manifest)>` — durable record of plan + owner-ratification trail.
2. `<source-edits + tests commit>` — patches to:
   - `framework/primary-persona/src/loam/primary_persona/intent_classifier.py` (NEW)
   - `framework/primary-persona/src/loam/primary_persona/cli.py` (new subcommand wiring)
   - `framework/primary-persona/src/loam/primary_persona/adapters/...` (extend the persona's user-prompt-submit contribution to pass `extra_inner_hooks=[intent_classifier_entry]`)
   - `framework/primary-persona/templates/persona-template/prompt.md` (Scope B persona-prompt edit at lines 433-454)
   - `framework/hands-off-lifecycle/hooks/first_run_settings.py` (Scope A generalization of `merge_user_prompt_submit` + `_LOAM_USER_PROMPT_SUBMIT_COMMAND_MARKERS` extension)
   - `framework/workspace-bootstrap/src/loam/workspace_bootstrap/...` (Scope C rescaffold CLI verb; specific module Tier-0-named at build time)
   - `docs/release-process.md` (Scope C audit-doc one-sentence addition)
   - `framework/primary-persona/tests/test_AC_CLE_HOOK_*.py` (4 new test files)
   - `framework/primary-persona/tests/test_AC_CLE_RECONCILE_1_*.py` (1 new test file)
   - `framework/hands-off-lifecycle/tests/test_AC_CLE_HOOK_4_*.py` (1 new test file — UserPromptSubmit merge multi-contributor)
   - `framework/workspace-bootstrap/tests/test_AC_CLE_SCAFFOLD_AUDIT_*.py` (2 new test files)
   - `framework/workspace-bootstrap/tests/test_AC_CLE_S_outcome_altitude_*.py` (1 new test file — outcome-altitude smoke)
   - **Per amendment #142 D-PASH.METHOD-DOC: the source-edit commit MUST land BEFORE `loam amend apply`.** Apply runs against committed HEAD per `apply.py:158`. THIS amendment dogfoods that discipline at its own build.
3. `<loam amend apply auto-commit>` — apply step writes its admitted-prefixes audit.
4. `<loam amend seal deterministic seal commit>` — runs the four-component pytest suite (primary-persona + hands-off-lifecycle + workspace-bootstrap + dev-sdlc as applicable per scope). T1.4 archives this plan-doc + manifest to `docs/plans/sealed/amendment-144-closed-loop-engagement-canonical-promotion.{md,manifest.yaml}` (dogfood: this amendment's own plan-doc moves to sealed/ at seal time per the canonical T1.4 convention; SKILL prose at `plugins/dev-sdlc/docs/conventions/plan-docs.md` line 50 prescribes this form). §14 auto-backfill via #141's decoupled path (per amendment-141 D-SCT.SHAPE, runs unconditionally on seal when `--plan-doc` is supplied).
5. `<§14 backfill commit>` — auto-embedded by `_finalize` step (h) per amendment-141's decoupled path; populates D-CLE.* SHAs.

Per `feedback_record_owner_ratification_before_dispatch`: §1 carries the durable owner-ratification record (TG 11808 / 11878 / 11881 / 11885). The plan-doc + manifest commit (step 1) IS the durable artefact the builder Tier-0-verifies before dispatching the build.

---

## §8. Risks + mitigations

| Risk | Mitigation |
|---|---|
| `additionalContext` injection doesn't reliably engage Claude Code's SKILL matcher → AC.CLE.S RED. | Halt trigger #6 names this case. Empirical evidence from today's session (Skill tool's available-skills list IS populated when `.claude/skills/<name>/SKILL.md` is reachable) suggests the matcher does engage, but if AC.CLE.S surfaces a different mechanism (prompt-augmentation, conditional injection on user-prompt-match), the halt routes to owner. |
| Multi-contributor `merge_user_prompt_submit` regresses AC46.5 backwards compat. | The empty-extras default returns byte-identical output (`[base_entry]`); test AC46.5 must remain green. Halt trigger #7 names this case. |
| The pos3-local hook copies absolute paths (`/Users/lukeivers/pos3/...`) and a naïve canonical migration would carry them. | The canonical hook uses `${LOAM_REPO}` env-var substitution + `${WORKSPACE_ROOT}` patterns mirroring `hands-off-lifecycle/hooks/settings.json.fragment`. The promoted classifier is pure-Python stdlib; the only path-bearing surface is the settings.json entry, which uses the same env-var pattern as the existing primary-persona entries. |
| Persona prompt edit at lines 433-454 inadvertently breaks an existing primary-persona test asserting the verbatim-slash-command directive. | Scope B's AC.CLE.RECONCILE.1 test IS the new assertion; existing tests asserting the OLD directive are necessarily failing post-edit and need updating in the same source-edit commit. Pre-flight: scan `framework/primary-persona/tests/` for assertions on `prompt.md` content; surface any conflicts at build start. |
| Scope C's rescaffold CLI verb doesn't have a clean operator-facing home in `loam_cli`. | Halt trigger #4 names this. Default at the plan layer is `loam workspace rescaffold-skills`; build-time Tier-0 picks the right home. |
| The plan-doc itself is archived via Scope C's T1.4 rename at seal time, but the rename happens DURING seal AFTER the plan-doc commit already landed. | This is the same dogfood case amendments #137-#143 navigated. The seal-step's plan-archive runs `git mv` from `docs/plans/<slug>.md` to `docs/plans/sealed/<slug>.md`; the prior plan-doc commit is the historical record; the rename commit IS the archival event. No special handling required. |

---

## §9. Test scope

- **Unit:** classifier behavior (AC.CLE.HOOK.1), `additionalContext` template body (AC.CLE.HOOK.2), persona prompt content (AC.CLE.RECONCILE.1) — 3 tests.
- **Integration:** CLI subcommand stdin/stdout (AC.CLE.HOOK.3), UserPromptSubmit merge multi-contributor (AC.CLE.HOOK.4), fresh-scaffold handsoff-loop discoverability (AC.CLE.SCAFFOLD-AUDIT.1), rescaffold-skills idempotency + collision (AC.CLE.SCAFFOLD-AUDIT.2) — 4 tests.
- **Outcome-altitude:** end-to-end closed-loop engagement path (AC.CLE.S) — 1 test.
- **Backwards compat:** existing AC46.5 (single-contributor `merge_user_prompt_submit`) must still pass; AC.LAYERED.2/.3/.4 (existing skill-symlink registration) must still pass. **Pre-flight:** run the existing primary-persona + hands-off-lifecycle + workspace-bootstrap pytest suites against HEAD `b2b46a2` and record the green baseline; the new tests + edits must keep them green.

Total new tests: 8. Total backwards-compat-protected existing tests: ≥3 named (AC46.5, AC.LAYERED.2, AC.LAYERED.3). Full pytest suite per touched component runs at seal time.

---

## §10. F2 Ruthless Feedback

**Honest doubts + design risks I'm naming explicitly:**

1. **The Scope B reconciliation MAY have a second cohort of conflicts the pre-flight didn't surface.** The persona prompt has 1,400+ lines (`wc -l prompt.md` returned that order of magnitude in earlier reads); other directives or examples elsewhere in the prompt MAY also reference verbatim-slash-command typing or otherwise conflict with the hook's prescription. Build-time Tier-0 must `grep -n` the full prompt for `/handsoff-loop`, `slash command`, `verbatim`, etc. and rewrite ALL matches consistently. If the grep surfaces a non-trivial second cohort, that's a halt-and-surface candidate (Scope B widens, or split into a separate amendment).

2. **The `additionalContext` injection mechanism is documented (Claude Code hook docs cited in the pos3 hook's docstring) but the EMPIRICAL engagement of SKILL auto-load via `additionalContext` is not directly verified.** Today's session demonstrated SKILL discovery (the Skill tool's list IS populated), but the matcher firing ON the `additionalContext` payload (vs on the user's literal prompt) is the open question. AC.CLE.S is the empirical check; halt trigger #6 names the fallback. **The risk is that the closed-loop engagement path requires Claude Code matcher behavior we don't have direct evidence of.** Tier-0 evidence at build time: try to find a Claude Code-internal test or docs example showing `additionalContext` engaging the matcher; if none, the outcome-altitude test IS the evidence (binary; n=1 is sufficient for an architectural question per `feedback_n1_architectural_vs_n3_statistical`).

3. **The pos3-local hook copies + builds an additional context block that prescribes "DO NOT build inline" and "DO NOT negotiate the intent classification."** This is strong forcing language. The persona prompt's existing translate-inbound stanza (which Scope B is editing) is softer ("the user's soft phrasing was not a request to avoid the closed-loop machinery"). The hook's structural forcing IS stronger than the persona prompt allows by intention — the hook is the BACKSTOP for when the persona prompt's softer prescription fails. **Risk:** if the persona prompt's softer prescription is the canonical voice, and the hook is the structural backstop, the two prescriptions should remain DIFFERENT in tone (soft prose in prompt; hard forcing in hook). Scope B's reconciliation should align the SUBSTANCE (no verbatim slash command) but preserve the VOICE difference. **Plan revision:** Scope B's edit at lines 433-454 should remove the `/handsoff-loop` verbatim instruction but keep the soft prose voice — the hook's hard forcing language is a separate surface that handles the "but the persona ignored it anyway" case structurally.

4. **The amendment #46 deferred work (AC46.6 — multi-contributor UserPromptSubmit) has been outstanding since #46 sealed.** This amendment closes it. **Risk:** if any post-#46 amendment relies implicitly on the single-contributor shape (e.g., a test that asserts `len(hooks.UserPromptSubmit[0].hooks) == 1`), the generalization breaks it. Pre-flight at build time: `grep -rn 'UserPromptSubmit' framework/ --include='*.py'` + read any test that asserts on the inner-hooks list length. Any such test gets updated alongside.

5. **The Scope C rescaffold-skills CLI verb has a subtle UX question: when an operator runs it, does it ONLY add missing symlinks, or does it ALSO update existing symlinks that point at stale targets?** The existing `_symlink_plugin_skills` is idempotent BUT (lines 1286-1293) treats an existing symlink as "already a symlink — leave alone." So a stale symlink (pointing at a plugin SKILL that no longer exists, or a renamed SKILL) does NOT get refreshed. **Risk:** the rescaffold verb is positioned as "fix my workspace's plugin SKILL discovery" — but it WON'T fix stale symlinks. **Recommendation:** Scope C's rescaffold verb body is `_symlink_plugin_skills(Path.cwd())` as-is — the same semantics as fresh-scaffold. Stale-symlink refresh is a separate concern (call it `--refresh-stale` flag, or a separate amendment). Document the limitation in the CLI verb's docstring + halt-and-surface tests.

6. **F2 on the dispatch brief itself:** the brief named three "options to investigate at plan-author time" for Scope A (symlink / plugin path config / copy). **Tier-0 verification answered this question definitively** — canonical loam ALREADY uses symlink (`_symlink_plugin_skills` is the existing implementation, and it works). The brief framed an open question that wasn't open; the answer was already in the codebase. This is fine — the brief is the dispatcher's hypothesis; the plan-author's job is Tier-0 verification. **Surfaced for the dispatcher's calibration:** the SKILL-discovery question for fresh workspaces is solved; the gap is for pre-existing workspaces (the pos3 case) + the intent-classifier hook itself. The brief's framing slightly mismatched the actual gap; this plan-doc corrects the framing.

---

## §11. Provenance / source citations

- **Canonical HEAD verification:** `git rev-parse HEAD` → `b2b46a22b0cbdc7580bd9d612015362e682ac9cb`. **Tier-0 direct shell invocation.**
- **`_symlink_plugin_skills` reference:** `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py:1224-1310`. **Tier-0 direct read.**
- **AC.LAYERED.2/.3/.4 reference tests:** `framework/workspace-bootstrap/tests/test_AC_LAYERED_2_skill_symlink_registration.py` + `test_AC_LAYERED_3_4_skill_collision_halt.py`. **Tier-0 direct ls.**
- **`merge_user_prompt_submit` single-contributor reference:** `framework/hands-off-lifecycle/hooks/first_run_settings.py:437-511`. **Tier-0 direct read.**
- **Amendment #45 multi-contributor reference:** `_compose_inner_hooks` at `framework/hands-off-lifecycle/hooks/first_run_settings.py:207-222`. **Tier-0 direct read.**
- **Pos3-local intent-classifier source:** `/Users/lukeivers/pos3/.claude/hooks/intent_classifier_inbound.py`. **Tier-0 direct read.**
- **Pos3-local settings.json UserPromptSubmit chain:** `/Users/lukeivers/pos3/.claude/settings.json:23-58`. **Tier-0 direct read.**
- **Persona prompt translate-inbound stanza:** `framework/primary-persona/templates/persona-template/prompt.md:397-454`. **Tier-0 direct read.**
- **Canonical plugin SKILL inventory:** `plugins/loam-skills/skills/` — 21 SKILLs including `handsoff-loop`. **Tier-0 direct ls.**
- **Plan-doc convention:** `plugins/dev-sdlc/docs/conventions/plan-docs.md`. **Tier-0 direct read.**
- **Amendment #143 precedent for plan-doc shape:** `docs/plans/sealed/amendment-143-tier1-retroactive-sweep-followup.md`. **Tier-0 direct read.**
- **Amendment #46 manifest precedent for UserPromptSubmit components:** `docs/plans/amendment-46-persona-session-start-turn-start-emitters.manifest.yaml`. **Tier-0 direct read.**
- **Owner ratification msg-IDs:** TG 11808 / 11878 / 11881 / 11885 per dispatch brief.

---

## §14. Method-decision register (populated at build time)

| Decision ID | Rationale | Build-time SHA |
|---|---|---|
| **D-CLE.HOOK-LOCATION** | Hook module lives at `framework/primary-persona/src/loam/primary_persona/intent_classifier.py` — co-located with the persona prompt's translate-inbound stanza it structurally enforces. Wired via new `intent-classifier` CLI subcommand. | _(build-time)_ |
| **D-CLE.HOOK-CLI-SHAPE** | CLI subcommand mirrors `user-prompt-submit` shape (no args; stdin → stdout JSON). Reuses argparse infrastructure. | _(build-time)_ |
| **D-CLE.MARKER-SHAPE** | `_LOAM_USER_PROMPT_SUBMIT_COMMAND_MARKERS` extended with `primary_persona.cli intent-classifier` substring; preserves alphabetical+CLI-subcommand pattern. | _(build-time)_ |
| **D-CLE.CONTRIBUTOR-WIRING** | Intent-classifier wired as `extra_inner_hooks` entry inside primary-persona's existing user-prompt-submit emitter; persona owns its own contribution. | _(build-time)_ |
| **D-CLE.RECONCILE-DIRECTION** | Persona prompt rewritten to match hook prescription (no verbatim slash command); TG 11881 ruling is authoritative; hook is the structural-enforcement source of truth. | _(build-time)_ |
| **D-CLE.RECONCILE-TEST** | Persona prompt test asserts negative (verbatim-slash-command substring absent) + positive (reconciled-prescription substring present) — content-lint shape, not semantic equivalence. | _(build-time)_ |
| **D-CLE.RESCAFFOLD-LOCATION** | Operator rescaffold-skills CLI verb lives at `loam workspace rescaffold-skills` (or closest existing operator surface; build-time Tier-0 names the right module). Body invokes `_symlink_plugin_skills(Path.cwd())`. | _(build-time)_ |
| **D-CLE.RELEASE-PROCESS-DOC** | One-sentence addition to `docs/release-process.md` under fresh-workspace verification; minimal-surface per amendment #142 precedent. | _(build-time)_ |
| **D-CLE.BASELINE-WALK** | BASELINE walked forward from #143 seal `f83260f`; no fixup commits; defaulted to publish-state `b2b46a2`. Dogfoods amendment #142 D-PASH.BASELINE-WALK. | _(build-time)_ |
| **D-CLE.SOURCE-EDIT-COMMIT-BEFORE-APPLY** | Source-edits commit lands BEFORE `loam amend apply`. Dogfoods amendment #142 D-PASH.METHOD-DOC (apply runs against committed HEAD per apply.py:158). | _(build-time)_ |

---

## §15. Backwards-compat verification

The following existing tests MUST remain green post-amendment:

- `framework/hands-off-lifecycle/tests/test_AC46_5_supervisor_stanza_carries_persona_session_start_hook.py` — AC46.5 single-contributor merge backwards compat. Empty-extras default to `merge_user_prompt_submit` returns byte-identical legacy output.
- `framework/hands-off-lifecycle/tests/test_AC46_5_first_run_stanza_carries_persona_session_start_hook.py` — same.
- `framework/hands-off-lifecycle/tests/test_AC45_5_backwards_compat_preserved.py` — amendment #45 SessionStart backwards compat (verifies the reference shape Scope A follows didn't regress on its own pattern).
- `framework/workspace-bootstrap/tests/test_AC_LAYERED_2_skill_symlink_registration.py` — `_symlink_plugin_skills` reference test (Scope C reuses the function body unchanged; this must stay green).
- `framework/workspace-bootstrap/tests/test_AC_LAYERED_3_4_skill_collision_halt.py` — collision semantics (Scope C's rescaffold-skills verb inherits these; must stay green).
- `framework/workspace-bootstrap/tests/test_AC_SKILLS_BUG_1_loam_skills_in_default_bootstrap.py` — `plugins/loam-skills/` is named in default bootstrap.yaml comment block (this amendment doesn't touch that comment; defensive).

Pre-flight baseline run at build start: `pytest framework/primary-persona/tests/ framework/hands-off-lifecycle/tests/ framework/workspace-bootstrap/tests/` against HEAD `b2b46a2`. Record green count. Post-build pre-seal: same suite must show green count ≥ baseline (new tests add to count; no regressions).

---

## §16. Halt-and-surface findings (populated post-build by builder)

_To be filled by the builder at build time per the existing convention. Initial entries from plan-author Tier-0 verification:_

**§16 plan-author finding #1:** **The dispatch brief framed three SKILL-discovery options (symlink / copy / plugin-path config) as a build-time decision.** Tier-0 verification revealed the answer is already in the codebase — `_symlink_plugin_skills` (v0.1.7 AC.LAYERED.2) already symlinks every plugin SKILL into `.claude/skills/`. The dispatch brief's framing slightly mismatched the actual gap. Resolution: plan-doc reframes Scope C as "audit + rescaffold for pre-existing workspaces," not "design SKILL discovery from scratch." No owner ruling needed — the framing correction IS the plan-author's job per ODD §2.5.

**§16 plan-author finding #2:** **The pos3-local intent-classifier hook's `CANONICAL_FORM_TEMPLATE` directly contradicts the canonical persona prompt's translate-inbound stanza at lines 433-443 of `prompt.md`.** TG 11881 codifies the hook's stance (slash commands not user-facing); the persona prompt predates the ruling. Resolution: Scope B reconciles by rewriting the persona prompt; the hook's prescription is the authoritative direction per the owner ruling.

**§16 plan-author finding #3:** **Pos3's `.claude/skills/` contains only ONE plugin-shipped SKILL** (the manual `handsoff-loop` symlink added today). Canonical loam ships 21. The gap is operator-side (pos3 was scaffolded pre-v0.1.7 + scaffold is idempotent), not canonical-side. Scope C's operator rescaffold-skills CLI verb IS the recovery path; the pos3 case isn't a fresh-workspace bug.

**§16 plan-author finding #4:** **The dispatch brief's halt-trigger #4 ("auto-load test reveals SKILL auto-load isn't reliable from soft prompts") is the load-bearing empirical uncertainty.** Today's session demonstrated Claude Code populates the Skill tool's available-skills list from `.claude/skills/<name>/SKILL.md` discovery — but does the matcher fire ON `additionalContext` injection vs ON the user's literal prompt? AC.CLE.S is the n=1 architectural verification per `feedback_n1_architectural_vs_n3_statistical`. If the test surfaces a different mechanism, halt trigger #6 routes to owner.

**§16 plan-author finding #5:** **The pos3-local hook chain has FOUR non-promoted hooks** (`principle_reminder.py`, `autonomy_baseline_reset.py`, `queue_status_inject.py`, plus pos3's own four PreToolUse hooks for jargon-check / closing-line / filler / idle-close). None of them gate closed-loop engagement, but they ARE general-purpose discipline enforcement that other operators might want. **Recommendation:** add FIDRAFT entry post-seal: "Evaluate canonical promotion of pos3-local discipline hooks (principle_reminder / autonomy_baseline / queue_status / translation_jargon / no_closing_line / filler_posture / idle_close) — out of scope for amendment #144 closed-loop-engagement focus."

---

## Provenance trail (per the §11 convention)

Every load-bearing source named in the plan-doc has been verified by direct shell invocation or direct file read at canonical HEAD `b2b46a2` between 2026-05-21T~23:30Z and 2026-05-21T~23:50Z. The plan-author subagent did not transcribe SHAs or line numbers from the dispatch brief without verification; the brief's pointers were used as starting points + verified independently.

Owner ratification record per `feedback_record_owner_ratification_before_dispatch`: §1 carries the four msg-IDs (TG 11808 / 11878 / 11881 / 11885). The plan-doc commit IS the durable artefact the builder Tier-0-verifies before dispatching the build — per the discipline, a builder finding "pending" status here is correct to halt; "ratified" status with the four-row table is correct to proceed.
