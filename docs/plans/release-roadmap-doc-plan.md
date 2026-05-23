# Plan — Release roadmap doc

**Authored:** 2026-05-08 (retroactive; the dispatch ran first; this captures what the plan WOULD have said).
**Status:** in-flight at agent `a8785ea8a8ffa2209`. Gap-check appended once landed.

---

## Objective

A canonical forward-looking release plan that maps every non-backlog idea/finding/pending-work-item to a version target where the version IS an objective sentence + acceptance criteria. The roadmap replaces existing per-release master plans (the v0.1.x roadmap + the ODD-rebuild master plan) as the canonical forward-looking artefact loam authors against.

A reader of `docs/release-roadmap.md` answers: "what does the next minor commit to delivering?" "what are the AC for declaring it done?" "what's after that?" "what's not on the plan at all (backlog)?"

## Constraints

- **Software-as-deliverable framing.** Loam's prime objective is helping people use LLMs to build software. Reverse-ODD extraction is a SCAFFOLD that places initial boundaries on what gets built; working code is the deliverable. v0.4.0+ entries reflect this framing explicitly.
- **Versions as objective targets, not feature lists.** Each version's name IS an outcome sentence ("loam helps you ship working code from extracted objectives"). Multiple ideas roll up under one version's outcome. Don't map individual features to versions; map them to outcomes.
- **Map EVERY non-backlog item to a version.** No artificial cap on the number of versions. If more items surface, recalculate.
- **Backlog is "maybe-someday."** Items going to backlog explicitly per Luke 2026-05-08: graphiti re-implementation; multi-LLM via OpenRouter; M-GMP plugin-shaped graphiti.
- **Specific carve-outs:** graphiti rip-out goes IN the version file (likely v0.3.0). Eric re-engagement is external action.
- **NO "rebuild" terminology.** Loam is its own project. The doc lands at `docs/release-roadmap.md` (not `docs/rebuild/...`).
- **AI-time bands per the rubric.** `wall_clock_minutes ≈ tool_calls × 0.1–0.15`; 10–50× faster than human-developer estimates. Calibration anchor: a comparable long-form authoring task ran 13 min wall-clock at ~76 tool calls.
- **Composes with `docs/release-versioning-policy.md` + `docs/odd-semver-pinning.md`.** Cites both; doesn't restate.
- **Length:** target 3000–5000 words.
- **Loam-aligned terminology consistent.** substrate / seed / cultivar / amend / seal used with single definitions where used.

## Acceptance criteria

1. **AC.RR.1 — §1 Framing.** Names versions as objective targets; cites versioning policy + ODD-SemVer pinning.
2. **AC.RR.2 — §2 Shipped.** Concise summary of v0.1.0 → v0.2.5.1 from STATE.md, one objective sentence per minor.
3. **AC.RR.3 — §3 Active version (v0.3.0).** Full ODD shape: objective sentence + constraints + AC + scope items + AI-time band + dependencies. v0.3.0's outcome must be the feature-honesty + terminology-consistency umbrella per Luke 2026-05-08 ruling.
4. **AC.RR.4 — §4 Mapped versions (v0.4.0+).** Every non-backlog item from the source aggregation maps to a named version. Each version entry includes objective sentence + source items + constraints + AC + AI-time band + dependencies.
5. **AC.RR.5 — §5 Backlog reference.** Pointer to FUTURE_IDEAS.md as the maybe-someday list; explicit allocation of items going to backlog per Luke 2026-05-08.
6. **AC.RR.6 — §6 External actions.** Non-version work named: Eric re-engagement, ProgramBench leaderboard submission as the action.
7. **AC.RR.7 — Source aggregation completeness.** Every source surveyed: STATE.md, FUTURE_IDEAS.md (26 ideas), FUTURE_IDEAS_DRAFT.md, BACKLOG.md, the three workspace/.scratch/claude-output/* artefacts (Eric run issues; Claude conference research; ProgramBench experiment shape), TaskList pending items #8/9/10/11/22/25/26/30/34-37/55, this-session-discussed items not yet captured (paper push, graphiti rip-out, memory honesty audit, conference compositions). No source unaccounted-for.
8. **AC.RR.8 — No "rebuild" terminology in body.** Verified by grep.
9. **AC.RR.9 — Word count 3000–5000.** Verified by `wc -w`.
10. **AC.RR.10 — Each version entry has an outcome sentence (not a feature list).** A reviewer reading the version names should see what a user can newly do, not what was built.

## Out of scope

- Don't author the actual builds for any version. The roadmap names the work; the work is dispatched per-version with its own plan-doc when the time comes.
- Don't move existing `docs/rebuild/` artefacts. That's v0.3.0 work; the roadmap names it but doesn't execute.
- Don't touch the FUTURE_IDEAS.md curated entries. The roadmap REFERENCES them; explicit additions to backlog (per Luke 2026-05-08) get appended in a follow-on FUTURE_IDEAS.md update.
- Don't push to remote. Held for dispatcher commit.

## Authority chain

- `docs/release-versioning-policy.md` (the SemVer commitment)
- `docs/odd-semver-pinning.md` (the ODD ↔ SemVer composition methodology)
- `docs/STATE.md` (current shipped state through v0.2.5.1; will move in v0.3.0)
- `docs/FUTURE_IDEAS.md` (26 numbered curated ideas)
- `docs/FUTURE_IDEAS_DRAFT.md` (no-overhead capture)
- `docs/BACKLOG.md` (post-foundation-audit residual)
- `docs/VALUE_PROPOSITION.md` (loam's prime objective)
- `plugins/dev-sdlc/docs/odd-methodology.md` (ODD canonical spec — note: NOT at top-level docs/)
- This-session artefacts at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/` (Eric run issues; Claude conference; ProgramBench v0)

---

## Gap-check (post-landing)

Pending agent completion. Once `docs/release-roadmap.md` lands, this section gets filled with the AC-by-AC verdict + any misses surfaced.

Things I'll specifically check for:
- Did the agent get the ODD methodology path right (`plugins/dev-sdlc/docs/odd-methodology.md`, NOT top-level)? My ODD+SemVer brief had it wrong; that agent corrected. This brief might have inherited the wrong path.
- Did the agent map every source item from AC.RR.7's exhaustive list? The risk is items getting silently dropped (FIDRAFT entries are dense; easy to miss).
- Is each version's name an outcome sentence (AC.RR.10)? The risk is feature-list framing creeping back in.
- Did v0.3.0 absorb the directory-rename scope per Luke 2026-05-08? My brief sketched it; agent should have it.
- AI-time bands actually use the rubric, not human-developer-time? The long-form-authoring calibration anchor is in the brief; agent should apply it consistently.
- Software-as-deliverable framing for v0.4.0+? Risk: extraction-as-deliverable framing slips back in.
