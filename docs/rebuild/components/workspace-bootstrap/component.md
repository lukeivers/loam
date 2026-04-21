# Component — Workspace Bootstrap

**Created:** 2026-04-20 13:57 CDT. **State:** ✅ **COMPLETE — sealed 2026-04-20 15:20 CDT.** Build commit `33e4cc0` on `pos-v2`; seal-ritual commit `aab5800` populates the SEAL_COMMIT sidecars (retroactive for self-correction, on-time for workspace-bootstrap); 57/57 bootstrap tests passing; 794 tests green across all eleven components; zero sealed-component deltas; ~50 min wall-clock (upper band, inside red line). **Phase 4 opens on this seal.**

---

## Parent objective (Phase 4, derived from Phase 3 close)

> **Workspace bootstrap.** A pOS workspace starts by composing the ten sealed foundational components into a running orchestrator + gate chain. The bootstrap component is the framework that assembles this composition, plus the adapter bundle for the foundational ten, plus the extension protocol that future Phase 4+ components use to register themselves without amending bootstrap.
>
> Acceptance:
> - A workspace configured with a `bootstrap.yaml` listing the ten foundational components starts an orchestrator with the three-gate chain wired in the correct order (safety outermost, reversibility middle, cost innermost, orchestrator `orig_activate` at core), self-correction subscribed, primary persona loaded, observability aggregator routing.
> - A new Phase 4+ component can register itself into bootstrap via a published extension protocol (packaging entry-points and/or `bootstrap.yaml` declaration) without any change to the bootstrap package.
> - Ordering declarations on contributions (e.g. "wrap activate_scope after X") are resolved by the framework's ordering engine; unsatisfiable orderings fail-closed at boot with a clear diagnostic.
> - The existing orchestrator-level `~/.pos/bootstrap.py` primitive either composes into this component or is subsumed without regression.

## Why this component is Phase 4's opener

1. **End-to-end proof-of-concept.** The ten sealed components have only been tested per-component; a workspace bootstrap is the first true integration. Any missed seams surface here.
2. **Plugin-host from day one.** the owner's analysis 2026-04-20 13:48 established that future Phase 4+ components (onboarding, dashboard, domain-workspace content, close-associate allowlist additions, seed data) all want to register at bootstrap. Monolithic bootstrap would force repeated unsealing; plugin-host from day one avoids that.
3. **Prerequisite for everything else in Phase 4.** Onboarding, dashboard, domain-workspace migration, backlog-tidy patches all need a running workspace to land against. Bootstrap unblocks the rest.

## Artifacts

- `research-plan.md` — drafted 2026-04-20; awaiting owner's approval
- `research.md` — not yet produced
- `proposal.md` — not yet produced
- `brief.md` — not yet produced
- `outputs/` — empty

## History

- 2026-04-20 13:57 CDT — component created (Phase 4's first component, follows sealed Phase 3 Foundational layer); research plan drafted; awaiting owner's approval before research begins.
- 2026-04-20 13:59 CDT — owner approved plan ("approve"). Background research agent dispatched.
- 2026-04-20 14:12 CDT — research agent returned after ~12 min wall-clock. Two-layer architecture held; extension protocol shape is entry-points-for-availability + `bootstrap.yaml`-for-enablement hybrid, declarative Pydantic `ContributionMetadata`, three-phase DAG with Kahn's topo sort. Four structural findings surfaced as halt signals but none blocking: (1) memory-system is a FastAPI sidecar not in-process, adapter launches/verifies it; (2) self-upgrade is a CLI, adapter is a readiness probe; (3) graceful-degradation, primary-persona monitor, objective-tracker, scope-of-work are already constructed inside `orchestrator._startup()` — adapters must not re-construct, only reference off host attributes; (4) stale docstring in `reversibility-primitive/src/ipc_wiring.py:8` claims wrong wrap order (code correct; cosmetic defect).
- 2026-04-20 14:28 CDT — the owner pushed back on the primary persona's default-against-unseal posture ("we're avoiding unsealing to fix"). the primary persona reconsidered each finding on merits. Recommended: unseal docstring (clear correctness fix), unseal orchestrator to extract four constructed components into uniform adapters (clearest architectural case), research memory-sidecar rationale before deciding, leave self-upgrade CLI as-is.
- 2026-04-20 14:33 CDT — ruling recorded: docstring fix YES, memory-sidecar LEAVE, orchestrator extract "way over the top" — declined, self-upgrade LEAVE. The no-op declaration adapters for scope_of_work + objective_tracker (the second advisory question) accepted.
- 2026-04-20 14:34 CDT — reversibility docstring fix landed on commit `ac48a7b`. 43/43 reversibility tests still green. Bootstrap baseline is now `ac48a7b`.
- 2026-04-20 14:38 CDT — proposal drafted at `proposal.md`. Encodes the owner's five rulings as locked inputs, enumerates 24 ODD acceptance criteria (B1–B24), flags 8 primary-persona inferences for the builder to challenge, locks `-32080..-32089` error-code range, documents twelve-adapter bundle (8 in-orchestrator + 2 declaration-only + 2 non-standard + 1 escape-hatch + 1 sidecar-launcher + 1 CLI-probe = actually 12 with the asymmetry accepted and absorbed by the extension protocol). Awaiting owner's approval.
- 2026-04-20 14:41 CDT — owner flagged over-specification in the proposal ("suggested file layout seems like over-specification"). the primary persona did a full clean pass: cut "suggested file layout" section entirely; cut phase-to-B-criteria test-mapping; stripped algorithm choices (no "Kahn's"), primitive choices (no "asyncio.TaskGroup"), specific function names, specific attribute names from §3 and §4. ~60 lines shorter. Lesson tucked into memory — no more suggested-file-layout sections in any future proposal. Proposal re-opened for owner's review.
- 2026-04-20 14:46 CDT — owner approved the trimmed proposal ("approve").
- 2026-04-20 14:47 CDT — handoff brief drafted at `brief.md`. Points builder at proposal as authoritative; names three sealed surfaces for verify-against-code; locks extension-protocol acid test (B18) as the contract's load-bearing test; seal-test pattern `SEAL_COMMIT` sidecar-file with baseline `ac48a7b`; halt-at-55-min with two named scope-creep classes. Awaiting owner's review before dispatch.
- 2026-04-20 14:49 CDT — owner approved brief ("approve"). Background build agent dispatched.
- 2026-04-20 15:15 CDT — Agent returned after ~50 min wall-clock (upper band, inside red line). Commit `33e4cc0` on `pos-v2`: 57 files in `workspace-bootstrap/`. 57/57 tests passing. Two primary-persona inference challenges legitimately caught and implemented: (1) `after=` declarations on the three wraps were inverted in the proposal — builder verified against sealed cost-governance integration test and implemented the correct order; (2) `pos upgrade --version` doesn't work (upgrade is subcommand-with-args, `pos` has no top-level `--version`) — builder substituted `pos --help`. B18 extension-protocol acid test passes. Observed pre-existing issue: self-correction's SEAL_COMMIT sidecar was never populated at its seal yesterday, causing its no-amendments test to fail against any later HEAD.
- 2026-04-20 15:20 CDT — owner approved seal + retrofit plan. Seal-ritual commit `aab5800` landed: populated `self-correction/tests/SEAL_COMMIT` with `65acb97` (retroactive fix) and `workspace-bootstrap/tests/SEAL_COMMIT` with `33e4cc0` (on-time). Full regression re-run: 794 tests green across all eleven components. **Workspace-bootstrap sealed.** Phase 4 opens on this component.
