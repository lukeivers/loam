# Component — Self-Upgrade Framework

**Created:** 2026-04-19 11:25 CDT. **State:** ✅ **COMPLETE — sealed 2026-04-19 14:12 CDT.** All D1–D10 landed; 120/120 tests green; zero sealed-component regressions; seven atomic commits on `pos-v2`; destructive-test runbook passed; clause-(g) self-correction caught during runbook validation. **Phase 2 closes on this seal** — eight components sealed total (4 primitives + 4 foundational).

---

## Parent objective (from spec v1.0 Foundational layer + v1.1 R1)

> **Self-upgrade without disruption.** pOS can upgrade its own framework — hooks, rules, orchestrator, skills — without disrupting the user's running configuration. Personas, memory, workflows, projects survive unchanged. Breaking contract changes surface explicitly with a named migration path rather than silently applying.
>
> Acceptance — after a framework upgrade, *all* of the following hold:
> (a) any active session continues without restart or re-authentication;
> (b) all personas load unchanged and pass their compaction-survival checks;
> (c) memory/daily entries are byte-identical to pre-upgrade *(v1.1 R1 refinement: replaced with semantic round-trip equivalence — pre-upgrade probe queries produce the same answers when replayed post-upgrade; a drift report measures deviation against a declared threshold for pass/fail; a substrate-level snapshot preserves physical reversibility alongside the semantic test)*;
> (d) all in-flight tasks are preserved with correct state;
> (e) any upgrade containing a breaking change to a framework contract surfaces explicitly in the upgrade output with a named migration path;
> (f) the upgrade itself is reversible — the previous framework version can be restored from a preserved snapshot;
> (g) every pOS change included in the upgrade is actually installed — none are silently skipped to avoid overwriting user customisations; installation is verifiable post-upgrade via a check that confirms each expected change is in place; when a change cannot be applied due to conflict with user customisation, the conflict is surfaced with explicit resolution options rather than silently dropped.

## Why this component is next

1. **Every sealed component has its own R1 semantic round-trip test.** The framework wraps them — runs each component's probe set pre-upgrade, replays post-upgrade, assesses drift. Without this component, upgrades remain a manual discipline; with it, they're a verified-atomic framework operation.
2. **Completes Phase 2 foundational.** This is the last item. Phase 2 closes when it ships.
3. **The seven-clause acceptance is already in owner's words** (from memory-system's earlier proposal addendum). The framework's job is enforcing all seven simultaneously, not re-specifying.

## Artifacts

- `research-plan.md` — drafted 2026-04-19; awaiting owner's approval
- `research.md` — not yet produced
- `proposal.md` — not yet produced
- `brief.md` — not yet produced
- `outputs/` — empty

## History

- 2026-04-19 11:25 CDT — component created; research plan drafted; awaiting owner's approval before research begins.
- 2026-04-19 11:28 CDT — owner approved research plan ("go"). General-purpose Agent dispatched.
- 2026-04-19 ~11:37 CDT — Research returned with 3 halt signals, ruling recorded 11:52.
- 2026-04-19 11:57 CDT — Proposal drafted.
- 2026-04-19 11:57 CDT — ruling recorded on 2 open questions (notify user yes; `auto_update_mode` configurable).
- 2026-04-19 12:00 CDT — Brief drafted.
- 2026-04-19 12:12 CDT — owner approved brief. Background Agent dispatched.
- 2026-04-19 ~12:37 CDT — Agent returned after ~25 min wall-clock. All D1–D10 complete across 7 atomic commits: `347b986` (D1+D7 manifest + conflict-report schemas), `43f6eaa` (D3+D4 snapshot + probe), `b3a39f1` (D5 orchestrator control + config), `06125d0` (D6 clause checks a–g), `bc72026` (D5+D6+D8+D9 upgrade flow + rollback + OTel + notification), `8299d47` (D2 CLI + pre-install conflict detection), `9e15379` (D10 docs + runbook). **120/120 tests passing.** All seven sealed components still at baseline (verified by `git diff --stat` showing only `self-upgrade/` paths). Symlink swap latency: p50 0.168 ms, p99 0.414 ms — well under any atomicity threshold. One material design improvement during runbook validation: initial `restore_substrate_snapshots` silently-skipped missing snapshot dirs (exactly the clause-g anti-pattern); hardened to raise `FileNotFoundError` with a clear diagnostic. Destructive-test runbook at `self-upgrade/scripts/destructive_test_runbook.sh` executed manually: PASSED all five verification steps.
- 2026-04-19 ~11:37 CDT — Agent returned after ~8 minutes / 46 tool calls. Research doc written. Recommended upgrade-unit: release tag (`pos-v2-vX.Y.Z`) backed by commit sha + per-release YAML manifest (`pos-release.yml`) enumerating files with sha256, per-component schema versions, breaking changes, migrations. Rollback atomicity: whole-upgrade atomic (partial acceptance rejected — components are coupled). Self-referential orchestrator upgrade: external CLI, no unseal needed (existing SIGTERM + graceful shutdown sufficient). Conflict report: YAML with enumerated resolutions; `skipped` structurally not a valid resolution (enforced by schema, not convention). Complexity 450–650 AI-minutes → ~45–65 min wall-clock, with physical floor on launchctl restart + Kuzu snapshot durations. Three halt signals: (1) aggregator has no named `snapshot_probe()` surface despite research-plan's implication — the primary persona's calibration miss; researcher recommends framework owns the aggregator probe set, no sealed-component amendment; (2) research-plan said "eight sealed components," STATE.md says seven — my error, the actual count is seven; (3) failed-rollback path is untestable in CI without destructive failure injection — proposal must decide prototype-only vs. harness.
