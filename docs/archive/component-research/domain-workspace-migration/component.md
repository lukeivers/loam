# Component — Domain-Workspace Migration

**Created:** 2026-04-20 15:29 CDT. **State:** `shelved` — ruling recorded 2026-04-20 15:38: "my intent is to start fresh and manually pull things over as i need them. i think this can be handled later entirely. we don't need this right now." the primary persona had misread intent as "orchestrate a wave-based migration"; the owner's actual intent is greenfield + manual curation.

Kept as reference in case a future automated migration is wanted; not a pending component.

---

## Parent objective (Phase 4, derived from "does it solve the owner's actual problem")

Migrate the owner's the existing workspace at `the existing workspace root` into a running pOS-v2 workspace such that the owner can use the new pOS for real work, with the foundational layer composed by workspace-bootstrap doing its job against real personas, real memory, real close-associates, real configs, real calendar + email integrations. This is the honest end-to-end test that Phase 1–4 promised — any unknowns in the ten sealed components' real-world fit surface here; any awkwardness in the extension protocol surfaces here.

**This component is structurally different from all prior components.** Prior components built framework; this one migrates content. The five-gate chain adapts: research produces a migration audit + wave-scoping recommendation; proposal approves wave-1 scope; build is mechanical migration + workspace-local adapter authoring; acceptance is "the owner can use it."

## Scope expectation — wave-based migration

recommendation, subject to ruling recorded in the research plan: **migrate in waves.** Big-bang migration of ~23 personas + years of memory + cron jobs + close-associate list + product registries + the nested sub-workspace is the universal pattern that goes wrong. Wave-1 is the minimum that gets the owner actually using the new pOS for real work; subsequent waves add progressively more content. The research plan enumerates wave-1 vs deferred.

## Artifacts

- `research-plan.md` — drafted 2026-04-20; awaiting owner's approval
- `research.md` (the migration audit) — not yet produced
- `proposal.md` (wave-1 scope decision) — not yet produced
- `brief.md` — not yet produced
- `outputs/` — empty

## History

- 2026-04-20 15:29 CDT — component created (Phase 4 second component, follows sealed workspace-bootstrap). Research plan drafted. Frames the task as "migration audit + wave-scoping recommendation" rather than a build; the five-gate chain adapts to content-migration rather than component-build.
- 2026-04-20 15:38 CDT — bypassed the component: "my intent is to start fresh and manually pull things over as i need them. i think this can be handled later entirely. we don't need this right now." Component shelved before research dispatch. The five-gate chain caught the intent misread at the plan stage — which is what the gate exists for. misread recorded in memory: the owner's "start greenfield" from Phase 1 opening (2026-04-18) meant manual curation, not orchestrated migration. No agent time spent.
