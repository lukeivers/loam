# Core Development Conventions (CDCs)

> These CDCs are dev-specific machinery that governs how *we* build pOS v2.
> Pre-M6b.0 they lived in `docs/rebuild/FUTURE_IDEAS.md`'s "temporary parking"
> section under the master rule "until the Dev/SDLC plugin (Idea 3) exists,
> this file is their temporary home; when the plugin lands, they migrate
> there." The plugin landed at M6a; M6b.0 executed the migration.

Each file in this directory is a single CDC. The order below preserves the
authoring chronology in `FUTURE_IDEAS.md` for traceability.

| # | File | Title |
|---|------|-------|
| 1 | `step-by-step-when-system-cannot-act.md` | Step-by-step when the system cannot act |
| 2 | `plan-before-code.md` | Plan before code, always |
| 3 | `background-agents-default.md` | Run all execution work through background agents / subagents |
| 4 | `scope-only-dispatch.md` | Scope-only dispatch to delegated agents |
| 5 | `setup-scripts-self-retire.md` | Setup scripts self-retire on success |
| 6 | `research-before-plan.md` | Research before plan for non-trivial new work |
| 7 | `shutdown-path-broad-catch.md` | Shutdown-path broad-catch exception |
| 8 | `audit-finding-triage.md` | Audit-finding triage by severity |
| 9 | `amendment-dispatch-test-scope.md` | Amendment-dispatch test & context scope |
| 10 | `529-overload-recovery.md` | 529 overload recovery |
