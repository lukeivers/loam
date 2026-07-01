# wvs-hook-event-name-fix — work-visibility hook missing `hookEventName` field

## §1 Objective

Fix a Claude Code hook-JSON validation bug in the work-visibility refresh
hook. `hooks_work_visibility.py::run()` returns a `hookSpecificOutput` dict on
all three return paths (workspace-root-missing, non-empty in-context block,
exception fail-closed) WITHOUT the required `hookEventName` field, causing
Claude Code to reject the hook output with:

> Hook JSON output validation failed — hookSpecificOutput is missing required
> field hookEventName

Observed live in a production session on the non-empty-block path
(UserPromptSubmit event).

## §2 Scope / fence

Single-component fence: `primary-persona`.

**In fence:**
- `framework/primary-persona/src/loam/primary_persona/hooks_work_visibility.py`
  (`run` / `main` — the only site where the output dict is constructed)
- `framework/primary-persona/tests/` — new regression test files (AC.WVS-HOOK-EN.*)
  and the minimal fix to pre-existing FRESH.2 test assertions that verified the
  buggy output shape

**Out of fence (do NOT touch):**
- `work_visibility_presenters.py` — the shim passes run()'s return dict upward;
  no change needed there
- `work_visibility.py` aggregator
- Any other component

The thin shim `hooks/work_visibility_hook.py` requires no change — it delegates
`main()` directly to the logic module and the event name is already in the
envelope by the time `run()` receives it.

## §3 Halt-before-build checks

- WD: `/Users/lukeivers/loam` — must match
- Plan-doc authored before any source edit (this file)
- No out-of-fence dependencies on the fix path

Halt triggers during build:
- Any source edit outside the fence
- A seal-test failure unrelated to this amendment's edits
- An ODD violation in adjacent code (surface, do not silently fix)

## §4 Named decisions

**D-EN.1** — Where to inject `hookEventName`

Inside `hookSpecificOutput`, not as a top-level key. Claude Code's error names
the missing field within hookSpecificOutput. Structure:
```json
{"hookSpecificOutput": {"hookEventName": "<event>", "additionalContext": "..."}}
```

**D-EN.2** — Event name source

`envelope["hook_event_name"]` — the standard Claude Code envelope field.
NOT hardcoded (the hook fires on ≥4 event types: SessionStart / PreCompact /
UserPromptSubmit / PostToolUse).

**D-EN.3** — Fallback when event name absent

Emit `{}` (bare empty dict, no `hookSpecificOutput`) rather than a partially-
formed dict. Malformed output is worse than no output. The fail-closed contract
(AC.WVS-FRESH.2 — never raise out of a hook) is preserved regardless.

**D-EN.4** — Existing FRESH.2 test assertions

Two assertions in `test_AC_WVS_FRESH_2_persona_owned.py` verified the old
buggy output shape:
- `test_AC_WVS_FRESH_2_hook_fail_closed_on_bad_envelope` asserted
  `output["hookSpecificOutput"]["additionalContext"] == ""`; after the fix,
  `run({"garbage": True})` returns `{}` (no event name → no hookSpecificOutput).
  Update to assert `"hookSpecificOutput" not in output`.
- `test_AC_WVS_FRESH_2_hook_cli_exits_zero` asserted `"hookSpecificOutput" in
  payload` against an envelope with no `hook_event_name`; after the fix, the
  output is `{}`. Update to assert only `returncode == 0` and valid JSON
  (the hook's actual contract here).

These are in-fence corrections, not out-of-fence drift.

## §5 Acceptance criteria

**AC.WVS-HOOK-EN.1** — For each of the 4 registered event types
(SessionStart / PreCompact / UserPromptSubmit / PostToolUse) and for the normal
return path (workspace root resolvable, in-context block returned), when
`hook_event_name` is present in the envelope, `run()` returns a dict with
`hookSpecificOutput.hookEventName == envelope["hook_event_name"]`.

**AC.WVS-HOOK-EN.2** — When `hook_event_name` is absent from the envelope (or
is not a non-empty string), `run()` returns `{}` — no `hookSpecificOutput` —
regardless of return path (root-missing, normal, exception).

**AC.WVS-HOOK-EN.3 (workspace-root-missing path)** — When the envelope carries
a valid `hook_event_name` but the workspace root cannot be resolved
(`workspace.project_dir` and `cwd` both absent), `run()` returns
`{"hookSpecificOutput": {"hookEventName": event_name, "additionalContext": ""}}`.

**AC.WVS-HOOK-EN.4 (exception/fail-closed path)** — When an exception is
raised inside the `try` block (after `hook_event_name` is extracted), the
except handler returns a dict with `hookSpecificOutput.hookEventName` equal to
the extracted event name (if present) or `{}` (if absent); always exits 0.
The test triggers the exception path by corrupting the workspace root resolver.

**AC.WVS-HOOK-EN.5 (outcome-altitude ★)** — The exact production failure path:
a realistic UserPromptSubmit envelope carrying a non-empty work-visibility state
is fed through `main()` (the CLI entry-point, identical to the production
spawn). The stdout JSON must have `hookSpecificOutput.hookEventName ==
"UserPromptSubmit"` and `additionalContext` non-empty. Outcome-altitude:
`main()` is called directly (in-process) — the complete production code path
with no scaffolding beyond the envelope. STUB-class tests do NOT satisfy this.

outcome-altitude:true: AC.WVS-HOOK-EN.5

**Regression gate (per dispatch):** The new tests MUST fail against the
pre-fix source; verified by the test author before commit.

## §6 Build steps

1. Author this plan-doc.
2. Author the manifest (`wvs-hook-event-name-fix.manifest.yaml`).
3. Commit plan + manifest.
4. Edit `hooks_work_visibility.py`: extract event name at top of `run()`;
   introduce `_wrap_output(event_name, additional_context)` helper; update all
   three return paths to use it.
5. Update two assertions in `test_AC_WVS_FRESH_2_persona_owned.py` (D-EN.4).
6. Author `test_AC_WVS_HOOK_EN_1_event_name_propagated.py` (AC.WVS-HOOK-EN.1
   + AC.WVS-HOOK-EN.3).
7. Author `test_AC_WVS_HOOK_EN_2_no_hookspecific_without_event_name.py`
   (AC.WVS-HOOK-EN.2 + AC.WVS-HOOK-EN.4).
8. Author `test_AC_WVS_HOOK_EN_3_outcome_altitude_main.py` (AC.WVS-HOOK-EN.5).
9. Run touched tests. Fix if red. No test loosening.
10. Commit source + test edits (feat/fix commits, before apply).
11. `loam amend validate` — schema passes.
12. `loam amend apply` — apply commit lands.
13. `loam amend seal` — seal commit lands.
14. Backfill: STATE.md change-log + docs/plans/loam-roadmap.md §8 register.

## §7 Out of scope

- Any change to `work_visibility_presenters.py`, `work_visibility.py`
- Any change to `hooks/work_visibility_hook.py` (the shim is correct as-is)
- Any change to `.claude/settings.json` hook wiring
- Any new AC not listed in §5

## §8 Method-decision register

| Decision | Recommendation | Rationale |
|---|---|---|
| D-EN.1 hookEventName location | Inside hookSpecificOutput | Claude Code error text names it there |
| D-EN.2 Event name source | `envelope["hook_event_name"]` | Only correct source for multi-event hook |
| D-EN.3 Missing event name | Emit `{}` | Malformed output worse than empty |
| D-EN.4 Existing test updates | Update 2 assertions | They verified the bug, not the contract |
