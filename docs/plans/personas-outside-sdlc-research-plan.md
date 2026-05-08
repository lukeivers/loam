# Plan — Research: personas outside the SDLC plugin

**Authored:** 2026-05-08.
**Status:** plan first, then dispatch (per the plan-before-code rule the dispatcher just re-recommitted to).

---

## Objective

A research + recommendation doc that answers: **should loam add personas outside the dev-sdlc plugin (e.g., for planning, research, communication, knowledge, finance, creative, etc.)? If yes, which ones, and what is each persona's value-prop relative to the primary persona's translation-layer role?**

The output informs whether v0.6.0+ (or a different version) should include a "plugin persona expansion" outcome, or whether new personas are speculative-enough to live in backlog.

## Constraints

- **Lens 1 — Claude-leverage-first.** Claude Code's native subagent mechanism is the substrate. Any persona proposal must specify how it leans on or extends Claude's subagent primitives, not re-implement them.
- **Lens 2 — primary-persona translation layer.** The primary persona is the user-facing translation surface. Sub-personas exist to give the primary a tool to dispatch to, not to surface directly to the user. A proposed persona that adds a user-facing surface in addition to (or instead of) translating-via-the-primary needs explicit rationale.
- **Software-as-deliverable framing for any dev-shaped suggestions.** Loam's prime objective is helping people use LLMs to build software (where "software" generalises to "the artefact the user wants made"). Persona proposals that don't ladder up to a user-deliverable are suspect.
- **No "rebuild" terminology.**
- **Composes with existing Sealed personas at dev-sdlc** (loam-builder / loam-plan-author / loam-researcher / loam-reviewer / loam-documenter, shipped v0.1.7). Don't propose duplicates; propose complements or adjacents.

## Acceptance criteria

1. **AC.PR.1 — Current persona shape surveyed.** Doc names the primary persona + the 5 dev-sdlc subagent personas with one-sentence value-prop each. Sources: `personas/`, `plugins/dev-sdlc/agents/`, STATE.md v0.1.7 entry.
2. **AC.PR.2 — Candidate non-SDLC domains enumerated.** Doc names ≥5 candidate domains (e.g., planning beyond SDLC, research, communication/email, knowledge management, finance, creative writing, household ops, legal, etc.) with brief value-prop sketch per domain. Sources: FUTURE_IDEAS Idea 3 (initial plugin suite).
3. **AC.PR.3 — Per-candidate analysis.** For each candidate domain, the doc covers: (a) what does a dedicated persona add that doesn't exist today? (b) does adding it reduce translation burden for the primary persona, or duplicate the primary's role? (c) what Claude-Code primitive does it lean on? (d) what's the smallest viable shape (one persona vs a 5-persona set as in dev-sdlc)?
4. **AC.PR.4 — Recommendation.** Doc concludes with: which (if any) candidate personas are worth adding now (mapped to a version target); which are speculative (backlog); which would dilute the primary's translation role and should NOT be added. Each verdict has a one-sentence rationale.
5. **AC.PR.5 — F2 RF tension surfaced.** Doc names at least one tension explicitly (e.g., "more personas = more dispatch overhead vs more specialised expertise"; "primary translates everything = single bottleneck vs delegation = primary's coherence loss"). Resolves or defers the tension explicitly; doesn't gloss.
6. **AC.PR.6 — Word count 1500–3000.** Tight; not a treatise.
7. **AC.PR.7 — Authority chain cited.** `docs/rebuild/VALUE_PROPOSITION.md` (Lens 2 + primary-persona role); CLAUDE.md (Lens 1 — Claude-leverage); FUTURE_IDEAS Idea 3 (plugin suite framing); STATE.md v0.1.7 (existing persona shape).

## Out of scope

- Don't author any new persona files. The output is research + recommendation, not implementation.
- Don't propose deep changes to the primary persona's contract. The persona-expansion question is about WHAT'S BEYOND the primary, not refactoring the primary.
- Don't survey persona shapes in other AI-agent ecosystems (LangChain, CrewAI, etc.). Loam is Claude-attached; the survey is internal-to-loam.
- Don't author the version-roadmap entry; the dispatcher folds the recommendation into the release-roadmap when both land.

## Authority chain

- `docs/rebuild/VALUE_PROPOSITION.md` (primary-persona translation layer)
- `CLAUDE.md` at repo root (Lens 1, Lens 2, Lens 5)
- `docs/rebuild/FUTURE_IDEAS.md` Idea 3 (initial plugin suite — Luke's framing of multiple plugin domains beyond dev-sdlc)
- `docs/rebuild/STATE.md` v0.1.7 entry (existing 5 dev-sdlc subagent personas)
- `personas/` directory (primary persona contract + prompt)
- `plugins/dev-sdlc/agents/` (the 5 subagent personas as shipped)

## Output

Write to `docs/plans/research/personas-outside-sdlc.md`. **Commit but do NOT push.** Held for dispatcher review of the research findings.

## Halt-and-surface

WD mismatch. Authority doc missing. Word count <1300 or >3300 (means scope drift). Push or tag attempt. The agent finds that the existing persona shape contradicts the brief's framing in a way that requires owner ruling rather than just restating.
