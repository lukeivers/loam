# v0.4.0 Cycle 3 — Substrate composition: Routines + Code Review + Outcomes-pattern ADR (STUB)

**Status:** stub sub-plan-doc; finalizes at cycle-dispatch time per `plan-docs-author` SKILL master-vs-sub-plan trim discipline.
**Slug:** `v0-4-0-cycle-3-substrate-composition-routines-codereview-outcomes`
**Date authored:** 2026-05-08.
**Parent master plan:** `docs/plans/v0-4-0-master-plan.md` §3 Cycle 3.
**Predecessor cycles:** C1 + C2 sealed (serial discipline; C3 is doc/SKILL/ADR work that doesn't structurally depend on C1+C2 but serializes per `feedback_serialize_amendment_builds`).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## §1 — Outcome shape (the "why")

C3 closes three small substrate-composition deliverables that share the "compose-on-Claude-substrate" theme. Per the conference research at `<workspace>/.scratch/claude-output/claude-conference-features-2026-05-06.md`, three Claude Code primitives shipped in the past two weeks that loam composes on rather than reimplements:

1. **Routines** (Released; `claude routine create`) — runtime layer for background-agent dispatches.
2. **Code Review** (`claude code review`, Released) — plan-step primitive.
3. **Outcomes** (Managed Agents, public beta) — runtime grader analogue to ODD's authoring-time discipline. **API-keyed; loam-on-subscription cannot directly compose**, so this is a documented architectural divergence ADR rather than an integration.

The bundle is intentional per Lens 5 stopping criterion: each individually 15-30min, three together 45-90min, per-AC sub-cycles add coordination overhead with no AC tightening.

## §2 — Prime objective ladder

VALUE_PROPOSITION.md prime objective → v0.4.0 §3 outcome → AC.V040.2 (Routines) + AC.V040.3 (Code Review) + AC.V040.5 (Outcomes ADR) → C3 ACs below.

## §3 — Component fence

PRIMARY (Routines, AC.V040.2):
- A memory feedback file (`feedback_routines_runtime_layer.md` at `~/.claude/projects/-Users-lukeivers-pos3/memory/` or named loam-canonical equivalent) documenting the pattern.
- 1 example plan-doc invoking `claude routine create` (or whatever the verified-live name is at C3 dispatch — halt-and-surface if name differs from conference research).

PRIMARY (Code Review, AC.V040.3):
- `plugins/dev-sdlc/skills/plan-docs-author/SKILL.md` gains a "compose-on-claude-code-review" section.
- 1 example plan-doc demonstrates the composition.

PRIMARY (Outcomes ADR, AC.V040.5):
- `docs/design/odd-vs-outcomes.md` (NEW).

Universal admissions: cross-references in `CLAUDE.md` if Routines becomes a named primitive at this cycle; `docs/release-roadmap.md` §3 v0.4.0 line "Compose on `claude code review` + `claude code security review`" already names the composition (no edit; ADR cross-references resolve).

Read-only: sealed-component source code; `plugins/dev-sdlc/skills/dispatch-brief-authoring/SKILL.md`.

## §4 — AC family seed `AC.SUB.*`

- `AC.SUB.1` — Routines pattern memory feedback file exists + names invocation shape (`claude routine create <pattern>` or verified-live equivalent). `outcome-altitude: false`.
- `AC.SUB.2` — 1 example plan-doc invokes `claude routine create`; cross-reference resolves. `outcome-altitude: true` (the example must actually invoke a Routines call, not just describe one).
- `AC.SUB.3` — `plugins/dev-sdlc/skills/plan-docs-author/SKILL.md` gains "compose-on-claude-code-review" section; section names invocation shape + when-to-compose conditions. `outcome-altitude: false`.
- `AC.SUB.4` — 1 example plan-doc demonstrates Code Review composition; cross-reference resolves. `outcome-altitude: true`.
- `AC.SUB.5` — `docs/design/odd-vs-outcomes.md` exists; names ODD as authoring-time discipline + Outcomes as runtime grader; documents stack-when-both-available shape; names API-key-vs-subscription divergence as a deliberate architectural choice with rationale (NOT a deficiency). `outcome-altitude: false`.
- `AC.SUB.6` — ADR cross-references resolve from `docs/release-roadmap.md` §3 v0.4.0 entry. `outcome-altitude: true` (the ADR is part of v0.4.0's documented deliverable surface; resolution from the canonical entry is the verifiable outcome).

## §5 — Build dispatch brief

Build dispatch brief authored inline by dispatcher at dispatch time per `dispatch-brief-authoring` SKILL.

## §7 — Out of scope

- Multi-Agent / Dreaming / Webhooks substrate composition (API-keyed; OUT OF SCOPE per `feedback_no_anthropic_api_key.md`).
- Routines as a structurally-enforced loam primitive (v0.7.0 structural-enforcement substrate).
- Code Review composition beyond the named SKILL guidance + 1 example (additional examples may land as separate cycles or via FIDRAFT).
- BYOK divergence beyond the Outcomes-pattern ADR (T7 tension surfaced in harness-landscape research §4; F2 RF only at v0.4.0).

## §10 — F2 RF gaps to surface at dispatch

- Verify `claude routine create` exists at C3 dispatch time — run `claude --help` + check Anthropic docs at dispatch; halt-and-surface if invocation name differs.
- Outcomes ADR tone — the ADR must name the API-key-vs-subscription divergence as deliberate (translation-burden-reduction story per VALUE_PROPOSITION) rather than as a missing-capability gap. Surface for plan-doc author at dispatch.
- Memory feedback file path — `~/.claude/projects/...` is pos3-local; loam-canonical path may differ. Surface for ruling at dispatch.

## §11 — Provenance trail

Master plan §3 Cycle 3; release-roadmap §3 v0.4.0 AC.V040.2 + V040.3 + V040.5; `<workspace>/.scratch/claude-output/claude-conference-features-2026-05-06.md` §1 cells #1, #4, #5 + §3 Lens-1 alignment table; `docs/plans/research/harness-landscape-and-roadmap-rerank.md` §4 Tension #1 (BYOK divergence rationale).

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Method-decision record finalized at C3 plan-doc dispatch time.

### Post-seal SHA register

| Commit | SHA |
|---|---|
| Plan-doc commit | (pending) |
| Source-edit commit | (pending) |
| Apply commit | (pending) |
| Seal commit | (pending) |
| §14 backfill commit | (pending) |
