# Plan — Harness landscape research + gap analysis + roadmap re-rank

**Authored:** 2026-05-08.
**Status:** plan first per the plan-before-code rule.

---

## Objective

A three-stage research artefact that:
1. **Surveys** AI-harness / agent-framework / agent-product developments over the past two weeks (~2026-04-22 through 2026-05-08).
2. **Gap-analyses** loam's current capabilities + roadmap against what others have shipped or are trending toward.
3. **Re-issues** loam's version targets, re-ranked using loam's value-prop as the prioritization filter — items that either (a) advance the primary value-prop strongly, or (b) demonstrate progress + draw external attention, rise to earlier minors. Items that fail both demote (or drop to backlog).

Output informs whether the current `docs/release-roadmap.md` (just authored) needs reordering OR whether the rank order survives the trend-aware re-evaluation.

## Constraints

- **Loam's value-prop is the prioritization filter.** From `docs/VALUE_PROPOSITION.md`: (1) primary-persona test = does this reduce translation burden between user's natural-language intent and AI-effective execution? (2) harness test = does this add to the toolkit the primary persona can draw from? Anything that fails either test is a redesign candidate.
- **Loam's architectural commitments hold.** Subscription-only via `claude -p`; no Anthropic API key anywhere; no migration to OpenRouter or multi-provider; Claude-Code-attached harness is the substrate. Trends incompatible with these constraints get noted but not adopted.
- **Software-as-deliverable framing.** Loam's prime objective is helping people use LLMs to build software. Trends in agent products that don't ladder up to this can be observed but should NOT pull rank in the re-issued roadmap.
- **External attention has standalone value.** Not just for vanity — external visibility recruits potential co-maintainers (mitigates the bus-factor-1 risk named in FUTURE_IDEAS Idea 12) AND pulls real users (gives loam calibration data the codebase can't generate alone).
- **Past-two-weeks scope.** Research is RECENT — 2026-04-22 through 2026-05-08. Older shipments are background context but not the primary surface.
- **No "rebuild" terminology.** Loam is its own project.

## Acceptance criteria

1. **AC.HL.1 — Stage 1 research deliverable.** Coverage of: Claude Code w/ Conference releases (already captured at `<workspace>/.scratch/claude-output/claude-conference-features-2026-05-06.md` — read + extend); Anthropic Managed Agents shipments (Outcomes, multi-agent, Dreaming); LangChain / LangGraph; CrewAI; AutoGen; Smolagents (HuggingFace); Aider, Cursor, Cline, Devin/Cognition, Replit Agent, Anthropic Computer Use, Anysphere updates; SWE-bench leaderboard movements; ProgramBench leaderboard; published agent papers (arXiv past 2 weeks). Each entry: feature/release, date, source URL, one-sentence summary. Cap at ≥10 distinct shipments to make the trend surface useful.
2. **AC.HL.2 — Trend distillation.** From the Stage 1 surface, name 4-7 trend lines. Each trend: name, evidence (≥2 shipments), single-sentence framing of what it means for harness builders. Distinguish "everyone is shipping this" trends from "marginal experimentation" trends.
3. **AC.HL.3 — Gap analysis vs loam.** For each Stage 2 trend: (a) does loam currently have a comparable capability? (b) is it on loam's existing roadmap? (c) if yes-on-roadmap, is the position correct relative to the trend's velocity? (d) if no, is loam's architectural constraint (subscription-only, claude -p, no API key) the reason for the gap, or is it a genuine miss? Each trend gets a verdict: HAS / ROADMAPPED / GAP-INTENTIONAL / GAP-MISS.
4. **AC.HL.4 — Roadmap re-rank deliverable.** Given the gap-analysis verdicts, propose adjustments to `docs/release-roadmap.md`: which items move earlier (high-leverage gaps), which stay where they are (correctly positioned), which move later or drop (low-leverage despite trend). Adjustments are PROPOSED, not applied — the roadmap doc itself stays untouched until owner ratifies.
5. **AC.HL.5 — Both ranking criteria applied.** Each re-rank decision documents which criterion drove it: (a) value-prop advancement, (b) external visibility leverage. A re-rank that doesn't satisfy either gets explicit rationale.
6. **AC.HL.6 — F2 RF tension surfaced.** At least one tension named explicitly (e.g., "trend X is everywhere but contradicts loam's subscription-only constraint — adopt anyway? defer? differentiate?"). Resolved or deferred to owner ruling, not glossed.
7. **AC.HL.7 — External visibility lever named concretely.** ≥3 specific moves loam could make in the next 1-3 minor versions that would meaningfully draw attention: e.g., ship a public benchmark submission; publish a methodology paper; release a high-leverage demo video; etc. Each scored against the value-prop tests.
8. **AC.HL.8 — Authority chain cited.** `docs/VALUE_PROPOSITION.md`; `docs/release-roadmap.md`; `docs/release-versioning-policy.md`; `docs/odd-semver-pinning.md`; existing scratch artefacts (Eric run issues; Claude conference research; ProgramBench experiment).
9. **AC.HL.9 — Word count 3000-5000.** Substantial enough to cover three stages; tight enough to be readable in one sitting.

## Out of scope

- Don't author any code. Output is research + analysis + recommendation.
- Don't apply roadmap changes — the existing `docs/release-roadmap.md` stays untouched. Recommendations are proposed; the dispatcher (or owner) ratifies before any roadmap edits land.
- Don't broaden to non-AI-harness comparisons (e.g., Linux containerization, Kubernetes, etc.). Loam-adjacent only.
- Don't propose architectural changes that contradict loam's subscription-only / no-API-key constraints. Trends incompatible with those are noted as "incompatible with current architecture" not "loam should adopt."

## Authority chain

- `docs/VALUE_PROPOSITION.md` (the prioritization filter)
- `docs/release-roadmap.md` (current target ordering)
- `docs/release-versioning-policy.md` + `docs/odd-semver-pinning.md` (versioning + outcome-target shape)
- `<workspace>/.scratch/claude-output/claude-conference-features-2026-05-06.md` (recent Anthropic shipments — read first; extend rather than re-research)
- `<workspace>/.scratch/claude-output/programbench-loam-benchmark-v0.md` (a benchmark loam could submit to)
- `<workspace>/.scratch/claude-output/eric-run-issues-friday-processing.md` (real-user feedback context)
- `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_no_anthropic_api_key.md` (architectural constraint)

## Output

Write to `docs/plans/research/harness-landscape-and-roadmap-rerank.md`. Commit but do NOT push. NEW commit, no --amend.

## Halt-and-surface

WD mismatch. Authority doc missing. Word count <2700 or >5300 (means scope drift). Push or tag attempt. The agent finds that the research surface is too sparse to support the gap-analysis stage (means the past-two-weeks scope was too narrow); surface for owner ruling on widening to a longer window. The agent finds that adopting a major trend would require relaxing the subscription-only constraint; surface explicitly rather than recommend silently.
