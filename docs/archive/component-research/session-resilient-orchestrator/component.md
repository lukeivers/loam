# Component — Session-Resilient Orchestrator

**Created:** 2026-04-18 19:57 CDT. **State:** ✅ **COMPLETE — sealed 2026-04-19 08:40 CDT.** All D0–D10 shipped on `pos-v2` across 11 atomic commits; 56 orchestrator tests green; all Phase 1 test suites still green (scope-of-work 77+1 skipped, objective-tracker 86, primary-persona 101, memory 30); launchd plist uninstalled at end. First Phase 2 component complete.

---

## Parent objective (from spec v1.0 Foundational layer)

> **Session-resilient.** A separate mechanism outside Claude sessions manages and executes work that survives session end, auto-starts and auto-stops with the system, and self-heals when it dies or gets stuck. Specific mechanisms exist for keeping context and functionality across compaction events and session stop/start.
>
> Acceptance:
> - Work queued before a session ends completes after session restart without user intervention.
> - Tasks survive system restart (laptop reboot, Claude CLI exit) and resume cleanly.
> - A process killed mid-run either self-heals (restarts) or is marked failed with recoverable state within a bounded window.
> - Compaction events preserve persona identity, active work items, and pending decisions — verified against a maintained compaction-survival list.

## Why this component is next

1. **Phase 1 primitives are libraries on disk until this runs.** Memory, scope-of-work, primary-persona layer, and objective tracker all exist but nothing orchestrates them into a running pOS. The orchestrator is the process layer that takes primitives from-library to at-runtime.
2. **Objective-tracker's `bind_scope` enforcement lives here.** The orchestrator is the dispatch-layer boundary that calls `bind_scope` before activating any scope.
3. **Graceful degradation (another Phase 2 item) may fold in here** since the orchestrator is where Claude API calls route through. The research should decide whether graceful degradation is a separate component or a sub-module.

## Artifacts

- `research-plan.md` — drafted 2026-04-18; awaiting owner's approval
- `research.md` — not yet produced
- `proposal.md` — not yet produced
- `brief.md` — not yet produced
- `outputs/` — empty

## History

- 2026-04-18 19:57 CDT — component created after Phase 1 closure; research plan drafted; awaiting owner's approval before research begins.
- 2026-04-18 23:23 CDT — owner approved research plan ("do it"). General-purpose Agent dispatched.
- 2026-04-18 ~23:47 CDT — Stream idle timeout on the first dispatch after ~24 minutes / 32 tool calls. Likely cause: the owner's machine sleeping/dying during the run. No research.md written; web-research work lost. Re-dispatched fresh 2026-04-19 06:59 CDT on the owner's return.
- 2026-04-19 ~07:08 CDT — Retry dispatch returned after ~9 minutes / 31 tool calls. Research doc at `research.md` (1,362 lines). Key recommendations: single long-lived Python asyncio process via launchd (macOS) / systemd-user (Linux); interactive Claude session is a peer process via Unix-domain-socket JSON-RPC (orchestrator does not host the session); primary-persona layer's monitor coroutine runs INSIDE the orchestrator process (justified by pyee-emitter locality and compaction-survival needs); **graceful degradation is a SEPARATE Phase 2 component, not a sub-module** (rationale: degradation is LLM-judged policy, orchestrator is deterministic plumbing); `bind_scope` dispatch sequence fully specified. Two advisory items for owner's proposal-phase review (not halts): orchestrator owns a small local SQLite for its own heartbeats/compaction-flags/bind_refused log (separate from Phase 1 stores); scope callback re-registration on restart relies on a workspace-supplied `~/.pos/bootstrap.py` convention. No spec criteria flagged unsatisfiable. Complexity estimate: 600–750 AI-minutes (larger than Phase 1 primitives because it integrates four of them and introduces process lifecycle + session separation + restart semantics for the first time).
- 2026-04-19 07:11 CDT — owner approved research recommendations ("do it").
- 2026-04-19 07:16 CDT — Proposal drafted at `proposal.md`. Ten deliverables (D1 process skeleton + D2 launchd/systemd supervision + D3 Unix-socket JSON-RPC server + D4 monitor hosting + D5 bind_scope dispatch layer + D6 local SQLite for orchestrator state + D7 restart-semantics behaviour + D8 compaction-survival integration + D9 OTel emission + D10 bundled docs + prototyping addendum). Three the primary persona leans (launchd throttle 30s, awareness-pull 100ms hard-ceiling with cache fallback, bootstrap.py-missing refuses to start). Three primary-persona inferences flagged. Awaiting ruling recorded.
- 2026-04-19 07:23 CDT — owner approved ("i agree with your leans. lets do it"). All three the primary persona leans accepted.
- 2026-04-19 07:26 CDT — Handoff brief drafted at `brief.md`. Covers D1–D10; the owner's nine baked-in decisions named explicitly (process model, launchd throttle 30s, peer-session IPC, monitor-in-orchestrator, awareness 100ms hard-ceiling with cache, graceful-degradation separate, bind_scope dispatch responsibility, local SQLite at ~/.pos/, bootstrap.py-missing fail-closed). Three primary-persona inferences flagged (launchd-primary-platform, Unix-socket-JSON-RPC substrate, ~/.pos/ as default config dir). Awaiting owner's review before dispatch.
- 2026-04-19 07:26 CDT — owner approved brief ("approve to dispatch"). General-purpose Agent dispatched for D1–D10 full build.
- 2026-04-19 ~07:28 CDT — Agent halted pre-build after reading brief/proposal + spot-checking 4 Phase 1 source files. Three concerns: (1) Python toolchain gap — machine's default Python is 3.9, Phase 1 requires ≥3.11, no venv with deps exists, acceptance tests can't run without env setup; (2) launchd plist installation is a real mutation to the owner's machine's startup state (agent reads as Tier C per brief but wants explicit confirmation before installing a daemon); (3) execution-budget realism — the proposal's 600–750-minute estimate genuinely is the largest build of the rebuild; single response can't produce full D1–D10 without corner-cutting that halt-on-deviation forbids. Agent recommendation: sub-brief approach (D1+D2+D3 first, then subsequent dispatches). No code, no commits, no launchd install. Awaiting ruling recorded.
- 2026-04-19 07:59 CDT — the owner's rulings: (1) use Python 3.13 as dev target — install via pyenv, create venv, install Phase 1 deps + pytest/pytest-asyncio; Phase 1's `requires-python=">=3.11"` floor stays (3.13 is compatible); (2) launchd test is authorised, but the plist must be uninstalled at end of build — we're building not running; (3) single-build approved with halt-and-resume discipline. Fresh dispatch with clarifications baked in.
- 2026-04-19 ~08:34 CDT — Agent returned. All D0–D10 complete across 11 atomic commits on `pos-v2`: D0 env (`839cf7e`), D1 skeleton (`09cb263`), D2 launchd/systemd (`c7d4ae6`), D3 Unix-socket JSON-RPC (`0fb35ed`), D4 monitor hosting (`5c1e708`), D5 bind_scope dispatch (`9200ba2`), D6 local SQLite (`af2f3ed`), D7 restart-semantics (`5963d69`), D8 compaction IPC (`db7fc58`), D9 OTel (`c08bcf3`), D10 docs + measurement addenda (`7233a70`). Orchestrator tests: 56 passing. Phase 1 regressions: all still green (no amendments). launchd measurements: throttle verified behaviourally — first boot 0.008s, SIGKILL 7.15s (inside minimum-runtime gate), SIGSEGV 0.007s, SIGABRT 0.008s, rapid-crash shots 2 and 3 honoured the 30s throttle (30.10s, 30.02s). IPC latency: p95 <1ms for ping, <10ms for awareness pull on Apple M-series (order-of-magnitude headroom on both budgets). Cache-fallback verified. launchd plist uninstalled at end per ruling 2 — `launchctl list | grep com.pos.orchestrator` empty. One inline fix surfaced and documented: `os.kill` returns EPERM against a launchd-managed PID from a non-root user session; measurement script switched to `launchctl kill SIGNAME gui/<uid>/<label>`. No halts. Complexity: original estimate 600–750 AI-minutes; actual across both dispatches fits well inside that.
