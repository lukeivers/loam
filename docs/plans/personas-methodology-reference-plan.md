# Plan — Personas methodology reference doc

**Authored:** 2026-05-08.
**Status:** plan first per the plan-before-code rule.

---

## Objective

A reference doc that names **what makes a persona valuable, when to add one, and when not to.** The doc serves as the explicit framework loam authors against when proposing or rejecting new personas — at any plugin or framework layer, including per-language personas within dev-sdlc, persona expansion outside dev-sdlc, or refinement of the primary persona's contract.

The doc is methodology-tier (alongside ODD methodology + release-versioning policy + ODD-SemVer pinning). It lands at `docs/personas-methodology.md` and informs every subsequent persona-shape decision loam makes.

## Constraints

- **Luke's framing (2026-05-08):** personas are valuable because they create a more CONSTRAINED space for using the LLM to produce certain outcomes. Per-programming-language personas within dev-sdlc are the canonical example — each has tighter constraints on how it "thinks" when programming.
- **Composes with Lens 4 (prompt scope ↔ confidence).** A persona is a constrained-scope pre-built template; the primary persona is broad-scope, sub-personas are narrow-scope. The doc names this composition explicitly.
- **Composes with Lens 1 (Claude-leverage-first).** Personas in loam are implemented via Claude Code's subagent mechanism. The doc names the seam.
- **Composes with Lens 2 (primary-persona translation layer).** Sub-personas exist to give the primary a tool to dispatch to, not to surface directly to the user. The doc reaffirms this division.
- **Concrete examples from existing loam personas.** The primary persona at `personas/primary/`; the 5 dev-sdlc subagents at `plugins/dev-sdlc/agents/` shipped v0.1.7 (loam-builder / loam-plan-author / loam-researcher / loam-reviewer / loam-documenter). Use these as case studies.
- **No "rebuild" terminology.**
- **Length:** target 1500–2500 words. Reference-doc tight; not a treatise.
- **Tone:** technical-research; loam-internal-but-shareable.

## Acceptance criteria

1. **AC.PM.1 — What is a persona in loam.** Doc names the formal definition: a persona is the pairing of a **persona contract** (machine-readable YAML at `personas/<name>/contract.yaml`) + a **prompt** (free-prose markdown at `personas/<name>/prompt.md` or equivalent) loaded into Claude Code's subagent context. Names how it differs from a SKILL (skills are body-loaded-on-trigger; personas are full-context-set-at-dispatch).
2. **AC.PM.2 — Why personas are valuable (constraint-narrowing).** Doc names the constraint-narrowing framing per Luke 2026-05-08: a persona narrows the LLM's probability mass over agent trajectories more aggressively than a generic prompt can. Composes with Lens 4 explicitly.
3. **AC.PM.3 — When to add a persona.** Doc names ≥4 concrete signals that a new persona pays off: (a) domain has consistent shape with repeatable work patterns; (b) primary persona over-generalises and produces drift on this domain; (c) tighter constraints would meaningfully change the trajectory distribution; (d) the work is dispatched-to-frequently-enough to amortise the persona's authoring cost. Each signal gets a worked example from loam or a hypothetical.
4. **AC.PM.4 — When NOT to add a persona.** Doc names ≥3 anti-signals: (a) work is too varied / one-shot to amortise; (b) primary persona already handles it well; (c) the proposed persona would surface directly to the user (violates Lens 2's translation-via-primary rule); (d) the proposed persona duplicates an existing one's role.
5. **AC.PM.5 — Decision rubric.** Doc gives a 4-7 question rubric a future authoring agent walks before proposing a new persona. Output of the rubric is a recommendation: "add this persona" / "extend an existing one" / "primary handles it; reject."
6. **AC.PM.6 — Per-language personas worked example.** Doc covers Luke's 2026-05-08 example explicitly: per-programming-language personas inside dev-sdlc (e.g., `loam-builder-python` / `loam-builder-typescript` / `loam-builder-ruby`). Walks the rubric for this case; concludes with the right shape (extend existing? new sub-personas? refine the language-adapter dispatch instead?).
7. **AC.PM.7 — Existing-persona-shape audit.** Doc surveys the current 6 loam personas (1 primary + 5 dev-sdlc subagents) against the rubric. Each persona has a one-sentence value-prop + a one-sentence why-it-passes-the-rubric. This validates the rubric against shipped reality.
8. **AC.PM.8 — Authority chain cited.** `CLAUDE.md` (Lenses 1, 2, 4); `docs/rebuild/VALUE_PROPOSITION.md` (primary translation layer); `personas/primary/`; `plugins/dev-sdlc/agents/`; `docs/rebuild/STATE.md` v0.1.7 entry; `docs/rebuild/FUTURE_IDEAS.md` Idea 3 (plugin suite framing).
9. **AC.PM.9 — Word count 1500–2500.** Verified by `wc -w`.
10. **AC.PM.10 — F2 RF tension surfaced.** Name at least one tension (e.g., "more personas = better constraints vs more dispatch overhead + drift between personas"; "primary translates everything = single coherent voice vs delegation = primary's coherence loss"). Resolve or defer; don't gloss.

## Out of scope

- Don't propose specific new personas. The doc is the framework; specific persona proposals come AFTER the framework lands and pass the rubric in their own follow-on work.
- Don't refactor the existing personas. The doc audits them but doesn't change them.
- Don't author the persona-expansion-outside-SDLC research. That's a follow-on (BLOCKED-BY this doc).
- Don't survey other AI-agent ecosystems' persona patterns. Loam is Claude-attached; the framework is internal-to-loam.

## Authority chain

- `CLAUDE.md` at repo root (Lens 1 Claude-leverage-first; Lens 2 harness + primary-persona value; Lens 4 prompt scope ↔ confidence)
- `docs/rebuild/VALUE_PROPOSITION.md` (primary persona's translation-layer role)
- `personas/primary/contract.yaml` + `personas/primary/prompt.md` (canonical persona shape)
- `plugins/dev-sdlc/agents/` (the 5 subagent personas as shipped)
- `docs/rebuild/STATE.md` v0.1.7 entry (current persona-shape state)
- `docs/rebuild/FUTURE_IDEAS.md` Idea 3 (plugin suite framing — implies persona-domain expansion)

## Output

Write to `docs/personas-methodology.md`. Commit but do NOT push. NEW commit, no --amend.

## Halt-and-surface

WD mismatch. Authority doc missing. Word count <1300 or >2700 (means scope drift). Push or tag attempt. The agent finds that the existing persona shape (primary + 5 dev-sdlc) doesn't survive the rubric — surface for owner ruling rather than retrofit the rubric to fit. The agent finds that Lens 4 + Luke's constraint-narrowing framing are in tension — surface explicitly for resolution.
