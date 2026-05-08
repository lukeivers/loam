# Plan — Leverage-discipline reference doc

**Authored:** 2026-05-08.
**Status:** plan first per the plan-before-code rule.

---

## Objective

A reference doc that names the **discipline by which loam stays on the highest-leverage development path**: what inputs we monitor, what decisions we make from them, on what cadence, and what counts as "highest leverage" in the first place. The doc serves as the explicit framework loam authors against when prioritising work — informing the release roadmap's next-version selections, identifying when to drop in-flight items, and surfacing when external trends should pull rank ordering forward.

The doc is methodology-tier (alongside ODD methodology + release-versioning policy + ODD-SemVer pinning + personas methodology). It lands at `docs/leverage-discipline.md` and informs every subsequent prioritisation decision.

## Constraints

- **Loam's value-prop is the load-bearing measure of leverage.** From `docs/rebuild/VALUE_PROPOSITION.md`: (1) primary-persona test = does this reduce translation burden? (2) harness test = does this add to the toolkit the persona draws from? Anything that fails both fails leverage even if it looks productive.
- **External attention has standalone value.** Not vanity — visibility recruits potential co-maintainers (mitigates bus-factor-1 risk per FUTURE_IDEAS Idea 12) AND pulls real users (gives loam calibration data the codebase can't generate alone). The doc names this as a legitimate leverage axis distinct from value-prop advancement.
- **Loam's architectural commitments hold.** Subscription-only via `claude -p`; no Anthropic API key; Claude-Code-attached harness. Trends incompatible with these get noted but don't pull rank.
- **No "rebuild" terminology.** Loam is its own project.
- **Length:** target 2000-3500 words. Reference-doc thorough; not a treatise.
- **Tone:** technical-research; loam-internal-but-shareable.

## Acceptance criteria

1. **AC.LD.1 — Inputs we monitor.** Doc names ≥6 inputs that feed leverage decisions: (a) industry research (frameworks, agent products, recent papers); (b) real-user feedback (Eric-class signals; ProgramBench scores; OSS issue activity); (c) internal feature-honesty audits; (d) benchmark performance shifts; (e) value-prop drift / stress-test signals; (f) cost-leverage retrospective per-version; (g) bus-factor-1 vulnerability indicators; (h) maintainer (Luke's) energy + availability. Each input: how we capture it, how we surface it for decision-making, who acts on it.
2. **AC.LD.2 — Decisions the discipline drives.** Doc names what decisions are MADE using these inputs: roadmap re-rank; minor-deferral; minor-drop-to-backlog; backlog-promotion; new-version-creation; architectural pivot; methodology amendment; whether to spend a cycle on a benchmark vs a feature.
3. **AC.LD.3 — Cadence.** Doc names review cadences: weekly (industry-trend pulse — Luke's Friday-morning idea; lightweight scan); per-minor-shipment retrospective (cost-vs-leverage post-mortem; what we learned about value-prop alignment); quarterly strategic (multi-version horizon; do the value-prop tests still match reality?).
4. **AC.LD.4 — "Highest leverage" measurement.** Doc names ≥4 measures: (a) value-prop test scores (primary-persona translation burden delta; harness toolkit expansion); (b) external-attention metrics (GitHub stars; releases adopted; mentions); (c) user-retention signals (real users running loam past a one-time install); (d) methodology export (loam's ideas adopted by other projects). Distinguishes load-bearing measures from informational ones.
5. **AC.LD.5 — Anti-leverage signals.** Doc names ≥3 patterns that LOOK productive but aren't leverage: (a) capability-build that no user reaches; (b) infrastructure investment without adoption signal; (c) industry-trend chasing that breaks architectural commitments; (d) feature-creep without value-prop alignment; (e) re-doing recently-shipped work for cosmetic-only reasons.
6. **AC.LD.6 — Decision rubric.** Doc gives a 5-7 question rubric the persona / Luke walks before commiting to a work item. Output: GO (work item ladders to value-prop or external visibility with clear measurement); DEFER (right work, wrong time); DROP (looks productive but doesn't ladder).
7. **AC.LD.7 — Bus-factor-1 mitigation explicit.** Doc names how the leverage discipline composes with bus-factor mitigation: external-attention work isn't optional decoration; it's risk mitigation. The doc surfaces this honestly rather than treating bus-factor as separate.
8. **AC.LD.8 — F2 RF tension surfaced.** At least one tension named explicitly. Examples: (a) external-attention work vs deep-build work — both leverage axes, sometimes pulling opposite directions; (b) industry-trend-following vs architectural-constraint-defending; (c) Luke's-energy as input — when Luke is depleted, the highest-leverage path may NOT be the most productive-looking one. Resolved or deferred to owner ruling.
9. **AC.LD.9 — Composition with the existing methodology stack.** Doc cites the four prior methodology docs (ODD methodology + release-versioning policy + ODD-SemVer pinning + personas methodology) and names how leverage-discipline composes — it's the LAYER ABOVE that decides which work the other methodologies execute against.
10. **AC.LD.10 — Word count 2000-3500.** Verified by `wc -w`.

## Out of scope

- Don't propose specific roadmap re-ranks. The leverage-discipline doc is the framework; specific re-ranks are output of applying it (the harness-landscape research dispatch in flight is the FIRST application).
- Don't propose specific methodology amendments. Same: the framework names that amendments are an output; specific amendments come from applying the framework.
- Don't author cron jobs / automation for the cadences. The doc names cadences; the implementation is a follow-on if and when the discipline beds in.
- Don't survey other projects' release-discipline docs (Linux kernel, Rust release process, etc.). Loam-specific discipline drawn from loam's value-prop.

## Authority chain

- `docs/rebuild/VALUE_PROPOSITION.md` (the load-bearing measure)
- `docs/release-roadmap.md` (current ranking; will be re-ranked using this discipline)
- `docs/release-versioning-policy.md` (SemVer commitment)
- `docs/odd-semver-pinning.md` (versions as objective targets)
- `docs/personas-methodology.md` (persona-shape decisions)
- `docs/rebuild/FUTURE_IDEAS.md` Idea 12 (open-source launch + bus-factor-1 framing)
- `docs/plans/research/harness-landscape-and-roadmap-rerank-plan.md` (the in-flight research dispatch — will be the first input the leverage-discipline framework consumes)

## Output

Write to `docs/leverage-discipline.md`. Commit but do NOT push. NEW commit, no --amend.

## Halt-and-surface

WD mismatch. Authority doc missing. Word count <1800 or >3700 (means scope drift). Push or tag attempt. The agent finds that "external attention" and "value-prop advancement" are in genuine tension that can't be resolved at framework-level — surface for owner ruling rather than collapse. The agent finds that loam's existing methodology stack already covers leverage-discipline implicitly and the doc would duplicate — surface that finding.
