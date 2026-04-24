# Research plan — workspace-bootstrap plist env vars (D5)

**Status:** research-plan for the D5 amendment cycle. Authored 2026-04-24. Sibling to D4's research plan — runs in parallel; disjoint sealed components.

**Session-start corpus:** research agent reads the five mandatory paths in `CLAUDE.md`'s session-start-discipline section first. Component-scoped reads: `docs/rebuild/components/workspace-bootstrap/`, `hands-off-lifecycle/hooks/first_run_scaffold*.py` (where the plist template lives).

---

## 1. Context

The 2026-04-23 pos3 session found `workspace-bootstrap`'s first-run scaffold emits a launchd plist whose `EnvironmentVariables` contains only `PYTHONUNBUFFERED=1`. No `PATH`, `USER`, `HOME`. Under launchd's default `PATH=/usr/bin:/bin:/usr/sbin:/sbin`, the spawned service cannot resolve `claude` (required by amendment #8's `ClaudePrintLLMClient`). Manual mitigation (editing the plist to add PATH+USER+HOME) was proven functional in-session. The research question is what the scaffold should emit, how to test that emission, and whether the gap extends to plists other than `memory-graphiti`.

## 2. Questions for the research agent

1. **What minimum env vars must the plist `EnvironmentVariables` dict contain** for the memory-graphiti service to reach `/health` → 200 end-to-end on a fresh clone? Confirm `PATH` + `USER` + `HOME` are sufficient; or identify any additional vars required (e.g., `TMPDIR`, `LANG`) through empirical testing in the canonical tree.
2. **Do other scaffold-emitted plists have the same env-var gap?** The scaffold emits plists for memory-graphiti AND orchestrator (at least). The orchestrator may have different requirements (it uses UNIX sockets not HTTP; it may not spawn scrubbed-env subprocesses). Identify each plist's env requirements and whether they're currently satisfied.
3. **Should USER be emitted explicitly, or inherited from launchd's session context?** launchd's gui domain normally sets USER automatically for user services; the session observed it was NOT set in the pos3 service's env (`launchctl print` showed `inherited environment = { }`). Research whether this is a launchd configuration concern, a plist-shape concern, or a macOS version artifact — then decide if explicit emission is the right answer or if we should investigate why inheritance failed.
4. **What test shape proves "emitted plist actually reaches /health OK end-to-end" at seal time?** B18's pattern (the workspace-bootstrap proposal's "synthetic contribution exercises the protocol") applies here: a seal test that actually loads the emitted plist via launchctl and waits for `/health` is the right shape. But the practical question is how to make that test deterministic (sandboxed launchctl? a fake-launchd harness? a pure-Python plist-shape validator plus a separate integration test?). Research surfaces the options; the amendment plan decides.
5. **Does this work compose with D4?** D4 widens the env-scrubber's allowlist; D5 widens what the plist supplies. Both are needed — the scrubber drops whatever the plist doesn't provide, so the union of both fixes is required. Confirm the composition and name any failure modes where D4 alone or D5 alone might appear to work but miss cases (e.g., if a user has non-launchd contexts that invoke the service directly).

## 3. Scope

- Read-only research. No source edits. No scaffold runs that mutate disk outside a sandboxed temp dir.
- Working directory `/Users/lukeivers/ivers-corp-pos-v2/`.
- Empirical probing allowed: the agent may instantiate a temporary launchd service in a sandbox to verify env-var effects (bootout in teardown).
- Cap: ~400 lines research doc.

## 4. Halt triggers

1. **A second sealed component beyond workspace-bootstrap needs touching.** Halt; owner decides.
2. **Test-shape requires method-in-acceptance** (e.g., only way to prove emission is "the plist contains the literal string `<key>USER</key>`"). Halt; owner rules.
3. **Launchd's inheritance behaviour turns out to be the root cause** (i.e., explicit emission is a workaround and the real fix is a launchd config change). Halt; owner rules on workaround-ship vs root-cause-fix.
4. **ODD break detected as strongly required.** Halt and signal.

## 5. Acceptance (research-plan gate)

Research document answering §2.1–§2.5 with evidence and per-question implication for the amendment plan.

## 6. CDC adherence

Same shape as D4's research plan (plan-before-code, research-before-plan, scope-only, background-agent-default). Parallel dispatch with D4 permitted per amendment #23's per-invariant baseline — disjoint sealed components (memory-system vs workspace-bootstrap).
