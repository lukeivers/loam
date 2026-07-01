# wvs-hook-event-name-fix — work-visibility hook hookEventName field

Per docs/plans/wvs-hook-event-name-fix.md.
`hooks_work_visibility.py::run()` returned `hookSpecificOutput` on all
three return paths (workspace-root-missing / normal / exception) WITHOUT
the required `hookEventName` field. Claude Code rejected every hook
output with "hookSpecificOutput is missing required field hookEventName"
and discarded the contribution. Observed live on the non-empty-block path
(UserPromptSubmit event).

THE FIX: `run()` extracts `hook_event_name` from the envelope at the
top of the function. A helper `_wrap_output(event_name, additional_context)`
builds the response: when the event name is a non-empty string, returns
`{"hookSpecificOutput": {"hookEventName": event_name, "additionalContext":
additional_context}}`; when absent, returns `{}` (no `hookSpecificOutput`)
so nothing malformed is ever printed. All three return paths now route
through this helper. Fail-closed contract (AC.WVS-FRESH.2 — never raise)
preserved.

Two pre-existing FRESH.2 test assertions verified the buggy output shape
and are corrected to match the fixed contract (in-fence, not out-of-fence
drift).

ACs: AC.WVS-HOOK-EN.1 (event name propagated, normal path, all 4 event
types), AC.WVS-HOOK-EN.2 (no hookSpecificOutput when event name absent,
all paths), AC.WVS-HOOK-EN.3 (workspace-root-missing path with event name
present), AC.WVS-HOOK-EN.4 (exception/fail-closed path), AC.WVS-HOOK-EN.5
★ outcome-altitude (realistic UserPromptSubmit envelope through main() —
the exact production failure, verified via the real entry-point with
non-empty work-visibility state).

Fence: primary-persona (source + tests). No shim change needed (the shim
delegates to run() and the envelope is unchanged).

Predecessor: 6cf995ef (dev-build-deploy spine P1 LOCAL — STATE + roadmap
backfill).
