# pOS Rebuild — State

**Created:** 2026-04-17 16:30 CDT. **Status:** Scaffolded, awaiting spec lockdown before first research plan.

This directory tracks the parallel rebuild of pOS against the new objectives spec. It runs deliberately *outside* the existing orchestrator — no `bin/orch` involvement, no workflows, no tasks, no existing specialist personas. Dispatch happens via general-purpose Agent invocations only after the owner has approved the artifact each agent is working against.

---

## Governing documents

- **Objectives spec** (authoritative — the contract being built against): `docs/rebuild/spec/pos-v2-objectives-spec.md`
- **Rebuild proposal** (approach, phases, principles): `docs/rebuild/spec/pos-v2-rebuild-proposal.md`

---

## Governing rules (short form — full versions live in the proposal)

1. **Five-gate chain per component:** research plan → research doc → proposal → handoff brief → dispatch. The owner approves the research plan, approves the proposal, and reviews the brief before dispatch.
2. **No deviation from approved proposals.** Executors halt and signal a named failure if they cannot comply; the primary persona picks up the signal, reviews with the owner, adjusts the proposal, restarts.
3. **ODD (Objective-Driven Design)** is the test methodology. Tests are authored against objectives, not behaviours. Negative cases are re-extended *up* the objective chain as new positive objectives, not buried as exception branches.
4. **pOS core ships zero personas.** Primary-persona primitive is contract + loader + validator; workspaces supply the content.
5. **Nothing is worked unless the owner has seen what it is being worked against before work starts.**
6. **Implementation language is Python.** (Ruling recorded 2026-04-18 09:18.) The original workspace global default of Ruby applies to the prior pOS stack only. The new pOS is Python-native.
7. **Background-work awareness — primary persona never loses track.** (Principle recorded 2026-04-18 13:51.) All work dispatched to any background process — subagent, orchestrator, cron, scheduled task — must be monitored such that the primary persona knows at all times whether it's been picked up, is progressing, has stuck, has finished, or needs review. The rule: an interactive session must never lose awareness of active background work and let the system go fallow. Scope-of-work primitive provides the emission and query surface (state events, `list(filter)`, pyee subscription); the background-work-monitor component that actively feeds the primary persona is designed alongside the primary-persona-loader in Phase 1.
8. **Test infrastructure is a separate dependency category from runtime.** (Ruling recorded 2026-04-18 14:27.) Permitted test-only dependencies (e.g. `pytest`, `pytest-asyncio`) may be added without halt-and-signal, provided they are not imported by runtime code and match infrastructure choices already established on `pos-v2`. Runtime dependencies remain strictly governed by the per-component brief's permitted list.
9. **200-line file rule does not apply to new pOS until new-pOS standards are authored.** (Ruling recorded 2026-04-18 14:27, applied retroactively.) The previous workspace `CLAUDE.md` rule constraining files to 200 lines was authored against Ruby and prior-pOS conventions. New-pOS code is governed by its own standards (Python idioms, cohesion-first), which will be authored as part of Phase 0 tidy-up. Until then, file-length is a judgment call by the builder with documented rationale for residuals.

---

## Component state machine

```
backlog
  → research_planned       research plan authored, sent for approval
  → research_approved      research plan approved
  → research_done          research document produced
  → proposed               proposal authored, sent for approval
  → proposal_approved      proposal approved
  → brief_drafted          handoff brief drafted, sent for review
  → brief_reviewed         handoff brief reviewed
  → in_work                agent dispatched per brief; work in progress
  → complete  |  blocked   gate met, or agent halted per deviation rule
```

---

## Layout inside this directory

```
docs/rebuild/
├── STATE.md                      ← this file (top-level at-a-glance)
└── components/
    └── [component-name]/
        ├── component.md          ← state + links to artifacts + history
        ├── research-plan.md      ← authored before research
        ├── research.md           ← produced by the research agent
        ├── proposal.md           ← authored from research; approved before dispatch
        ├── brief.md              ← handoff brief; reviewed before dispatch
        └── outputs/              ← any deliverables produced by the executing agent
```

Each component is self-contained in its own subdirectory. Nothing in this tree calls into the prior orchestrator or uses prior-pOS personas.

---

## Components

| Component | State | Related phase | Last action | Awaiting |
|-----------|-------|---------------|-------------|----------|
| Memory system | COMPLETE | Phase 2 | Sealed 2026-04-18 12:08 | — (follow-ons pending primitives that reference it) |
| Scope-of-work primitive | COMPLETE | Phase 1 | Sealed 2026-04-18 14:27 | — |
| Primary-persona layer (loader + monitor + autonomous authoring) | COMPLETE | Phase 1 | Sealed 2026-04-18 18:43; v1.2 addendum landed | — |
| Objective tracker | COMPLETE | Phase 1 (final) | Sealed 2026-04-18 19:56 | **PHASE 1 CLOSED** |
| Session-resilient orchestrator | COMPLETE | Phase 2 | Sealed 2026-04-19 08:40 | — |
| Graceful degradation | COMPLETE | Phase 2 | Sealed 2026-04-19 10:02 | — (memory blind-spot logged to BACKLOG.md) |
| Observability aggregator | COMPLETE | Phase 2 | Sealed 2026-04-19 11:24 | — |
| Self-upgrade framework | COMPLETE | Phase 2 (final) | Sealed 2026-04-19 14:12 | **PHASE 2 CLOSED** |
| Safety layer | COMPLETE | Phase 3 | Sealed 2026-04-19 17:22 CDT | — |
| Reversibility primitive | COMPLETE | Phase 3 | Sealed 2026-04-20 08:19 CDT | — |
| Cost governance | COMPLETE | Phase 3 | Sealed 2026-04-20 10:48 CDT | — |
| Self-correction loop | COMPLETE | Phase 3 (final) | Sealed 2026-04-20 12:21 CDT | **PHASE 3 CLOSED** |
| Workspace bootstrap | COMPLETE | Phase 4 (opener) | Sealed 2026-04-20 15:20 CDT; seal-ritual commit `aab5800` | — |
| Domain-workspace migration | `shelved` | Phase 4 | Bypassed 15:38 CDT — greenfield + manual curation is the actual intent | — (no pending work) |
| Foundation audit | COMPLETE | Phase 4 (second) | Sealed 2026-04-21 10:09 CDT (Option A). Four commits: checkpoint `86cb261`, F1 `55ab3e1`, F2 `af99046`, F3+BACKLOG `8e2b8f1`. B/C preserved in BACKLOG. | — |

Component directory: `components/memory-system/`

---

## Pending owner actions

- **Review the three ODD documents** with consolidated open questions. All three landed and committed. Doc 1 (`pos-v2/docs/odd-methodology.md`, 608 lines, commit `4fd60d8`); Doc 3 (`pos-v2/docs/odd-in-pos.md`, 673 lines, commit `492b5c2`); Doc 2 (workspace `content/odd-manifesto.md`, 3081 words, commit `e7597f1`). Seven open questions across the three — surfaced in-session 2026-04-21 10:38.

---

## Change log

- **2026-04-17 16:30 CDT** — directory scaffolded; STATE.md seeded; empty `components/` created; dispatch mechanism approved (file-based state, general-purpose Agent tool, zero orchestrator involvement).
- **2026-04-17 16:31 CDT** — objectives spec locked at v1.0.
- **2026-04-17 16:32 CDT** — memory system component created (`components/memory-system/`); research plan drafted; state `research_planned`; awaiting approval.
