# pOS Rebuild — State

**Created:** 2026-04-17 16:30 CDT. **Last refresh:** 2026-04-29. **Status:** All thirteen sealed components built (Phase 1–4); amendment cycle active (currently #75). D-architecture commitment 2026-04-26; workspace-sync migration to git-shaped sync landed via #58–#75 series. **OSS publish (loam v0.1.0) work-plan activated 2026-04-29** at `docs/rebuild/plans/oss-v0-1-0-publish.md` after Idea 12's three open rulings closed: dormancy-rename pre-launch, Dev/SDLC plugin only at v1, public repo at `lukeivers/loam`.

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
10. **D-A1 hybrid architecture lock** (ruling 2026-04-26): pos-v2
    framework code follows Architecture B (workspace-sync pulls
    framework into the workspace's framework/ directory under D);
    the user-facing `pos` CLI binary follows Architecture A (global
    install via pipx per FUTURE_IDEAS Idea 13's β.3). Workspace
    state stays at the workspace root, not under framework/.
11. **Workspace-sync mechanism is migrating** (commitment 2026-04-27):
    the resolve→stage→apply pipeline with `sync-protected.yaml` class
    envelopes is being replaced by `git fetch + git merge --ff-only`
    against a tracking branch, with the LLM resolver demoted to a
    rare-conflict fallback. β.1 (workspace canonical-source config,
    sealed #58) and α-hotfix-1+2 (#59, #60) are the most recent
    amendments. β.2 (`pos-new-workspace` bootstrap) absorbs into D's
    migration; β.3 (global pipx install) remains independent.

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
| **Amendment cycle 2026-04-21 → present** | ACTIVE | post-Phase-4 | ~75 amendments across all components since the foundation audit; pos-amend CLI introduced #22; frozen-H19 BASELINE convention #23; loam rename tabled #23 era then un-tabled #75-era; two-modes-and-multi-workspace master-plan (#34+) with sub-plans A/E/B/F sealed and C/D/G deferred under Idea 13; workspace-sync milestone #56 closed-then-reopened by D-decision; α-hotfix-1+2 (#59, #60); D-cutover #67–68 (framework/+workspace/ split); A4 structural-enforcement #72; corpus-inlining SessionStart hook #73; dispatcher-side test-stub authoring #74; A1 substrate timestamp normalization #75. | — |
| **OSS publish (loam v0.1.0)** | ACTIVE | post-amendment-cycle | Activated 2026-04-29 after Idea-12 rulings closed; master plan at `docs/rebuild/plans/oss-v0-1-0-publish.md`. Includes Phase-1 documentary rebrand (Idea 10), Tier-2 dormancy rename pre-launch, Dev/SDLC plugin at v1, publish-mode partition, public docs scaffold, synthesis dry-run, publish to `lukeivers/loam`. | gate reviews at M5/M8/M9 |

Component directory: `components/memory-system/`

---

## Pending owner actions

- **(Refresh in progress 2026-04-27 — this section is now primary persona's responsibility to keep current.)** Prior pending action — three-ODD-document review — closed; documents committed (`4fd60d8`, `492b5c2`, `e7597f1`).
- **Workspace-sync spec-level objective backing** (halt-and-surface from corpus review 2026-04-27): `workspace-sync` exists as a sealed component (#56) without a spec-level objective in v1.0/v1.1/v1.2 explicitly naming "framework workspaces stay synced with canonical." Three options: (a) v1.3 addendum naming it; (b) a v1.1-style refinement clarifying it falls under U1's self-upgrade umbrella; (c) declare it dev-mode-only machinery. Awaiting owner ruling.

---

## Change log

- **2026-04-17 16:30 CDT** — directory scaffolded; STATE.md seeded; empty `components/` created; dispatch mechanism approved (file-based state, general-purpose Agent tool, zero orchestrator involvement).
- **2026-04-17 16:31 CDT** — objectives spec locked at v1.0.
- **2026-04-17 16:32 CDT** — memory system component created (`components/memory-system/`); research plan drafted; state `research_planned`; awaiting approval.
- **2026-04-21** — foundation audit closed (Option A); seal commit `aab5800`. Workspace-bootstrap-era residuals captured in BACKLOG.md.
- **2026-04-21** — ODD methodology + odd-in-pos + value-prop landed (`4fd60d8`, `492b5c2`, `e7597f1`).
- **2026-04-22** — Linux-violation incident; ODD §2.5 explicit "no non-objective code" rule codified; plan-before-code CDC introduced.
- **2026-04-23** — pos-amend CLI introduced (amendment #22); frozen-H19 BASELINE + per-invariant-BASELINE convention (#23); loam rename tabled.
- **2026-04-25** — dev-mode partition (sub-plan F) sealed; FUTURE_IDEAS_DRAFT.md added as no-overhead capture surface.
- **2026-04-26** — D-A1 hybrid architecture lock (governing rule #10 added).
- **2026-04-27** — workspace-sync milestone closed-then-reopened by D commitment over D′; α-hotfix-1 (#59) + α-hotfix-2 (#60) closed correctness bugs of the verdict-without-stage class; β.1 sealed (#58); β.2 absorbed into D's migration; β.3 (global pipx install) remains independent.
- **2026-04-27** — corpus review applied (this refresh): STATE.md header + governing rules #10/#11 + component-table amendment-cycle row + pending-owner-actions replacement + this change-log block; methodology + odd-in-pos + FUTURE_IDEAS sharpened. See `docs/rebuild/plans/research/corpus-review-2026-04-27.md`.
- **2026-04-29** — OSS publish (loam v0.1.0) work-plan activated. Idea-12 three open rulings closed (pre-launch dormancy / Dev-SDLC-only at v1 / `lukeivers/loam` repo). Idea 10 un-tabled (prerequisites met at #75). Idea 12 marked ACTIVE with rulings recorded inline. STATE refreshed (amendment count #60→#75; OSS-publish row added). Channel rules locked globally (Telegram-only + pause-on-outage). AI-time estimation rule added to global CLAUDE.md. FUTURE_IDEAS_DRAFT cleanup application + master plan authoring + public-docs scaffold dispatched for execution.
