# Plan — ODD ↔ SemVer pinning doc

**Authored:** 2026-05-08 (retroactive; the dispatch ran first; this captures what the plan WOULD have said).
**Status:** doc landed at `docs/odd-semver-pinning.md` (commit `0609b14`); gap-check below.

---

## Objective

A methodology doc that names the structural composition between SemVer minor versions and ODD outcome statements, so loam's release shape and methodology stay coherent. The doc lets a reader of any release artefact (release notes, plan-doc, tag annotation) understand what the release commits to and how completion is measured — without needing to hold both the SemVer policy and the ODD methodology in their head at once.

## Constraints

- **Authority chain:** the doc composes on `docs/release-versioning-policy.md` (SemVer commitment + 1.0.0 criteria) and `plugins/dev-sdlc/docs/odd-methodology.md` (canonical ODD spec) + `docs/odd-llm-grounding.lean.md` (the lean prime, including §6 outcome-altitude AC requirement). It does NOT restate their content; it cites + composes.
- **Length:** target 600–1200 words. Tight is the goal.
- **Tone:** technical-research; loam-internal-but-shareable. Less austere than the Anthropic-audience methodology paper; more pragmatic.
- **Worked examples:** at least one for the structural mapping, one for patch semantics. Use real loam history (v0.2.5 trajectory, v0.2.5.1 patch shape).
- **No "rebuild" terminology** — loam is its own project.
- **Subscription-only constraint** flows in as one of the architectural constraints inherited at the loam-architecture level.

## Acceptance criteria

1. **AC.OS.1 — Structural mapping named.** Doc names "minor = ODD cycle (objective + constraints + AC + implementation)" with at least one worked example using a real or planned loam minor.
2. **AC.OS.2 — Patch semantics covered.** Doc names "patches close defects against the parent minor's named outcome; patches do not introduce new objective; if it requires new capability, it's a minor not a patch." Worked example using v0.2.5.1.
3. **AC.OS.3 — Outcome-altitude AC at release-gate.** Doc names that each minor's release-gate must include an outcome-altitude HARD smoke per the procedural amendment shipped 2026-05-05. Cites the v0.2.5 4-RED trajectory as the lesson source.
4. **AC.OS.4 — 1.0.0 as global outcome AC.** Doc names the 1.0.0 jump as itself an outcome-altitude AC enumerated in the versioning policy; treats it as ODD-shaped milestone not a calendar event.
5. **AC.OS.5 — Operational consequences named.** Doc covers what changes in practice: release notes structure, planning-time discipline, retrospective shape after a minor ships.
6. **AC.OS.6 — Word count 600–1200.** Verified by `wc -w`.
7. **AC.OS.7 — Authority chain cited.** Doc references the three canonical docs by path (versioning policy + ODD methodology + lean grounding) with correct paths.

## Out of scope

- The doc does NOT restate the ODD spec or the SemVer policy. It composes them.
- The doc does NOT prescribe new methodology beyond making the composition explicit. Anything that requires a methodology change goes to its own future amendment.
- The doc does NOT cover non-loam version schemes (calendar versioning, marketing versioning, etc.). It is loam-specific.

## Authority chain

- `docs/release-versioning-policy.md` (companion; SemVer commitment)
- `plugins/dev-sdlc/docs/odd-methodology.md` (ODD canonical spec)
- `docs/odd-llm-grounding.lean.md` (lean prime + §6 outcome-altitude requirement)
- `docs/papers/odd-methodology.md` (Anthropic-audience paper for tone calibration)

---

## Gap-check (post-landing)

Doc landed at `docs/odd-semver-pinning.md`, commit `0609b14`, 1197 words.

Section-by-section vs ACs:

| AC | Required | Landed | Verdict |
|---|---|---|---|
| AC.OS.1 | Structural mapping + worked example | §2 (minor as ODD cycle, v0.3.0 worked example) | ✓ |
| AC.OS.2 | Patch semantics + worked v0.2.5.1 | §3 (defect-closure cycles, v0.2.5.1 worked example) | ✓ |
| AC.OS.3 | Outcome-altitude AC at release-gate + v0.2.5 lesson | §4 (4-RED trajectory cited) | ✓ |
| AC.OS.4 | 1.0.0 as global outcome AC | §5 (criteria enumerated, ODD-shaped milestone framing) | ✓ |
| AC.OS.5 | Operational consequences | §6 + §7 (planning-time discipline, release-notes structure, "versioning is versioned") | ✓ |
| AC.OS.6 | Word count 600–1200 | 1197 (within band; trimmed twice from 1234 to clear the 1200 ceiling) | ✓ |
| AC.OS.7 | Authority chain cited | Footer cites versioning-policy + odd-methodology (correct path: `plugins/dev-sdlc/docs/odd-methodology.md`) + lean grounding | ✓ |

**No misses against the plan.** The agent caught one path correction in flight (`docs/odd-methodology.md` → `plugins/dev-sdlc/docs/odd-methodology.md`) which my brief had wrong; the agent's correction is the right one and the plan should have named that path correctly. F2 RF tension considered + resolved in §6 per the agent's reply.

**Adjacent miss the plan would have caught earlier:** none surfaced. The §6 "operational consequences" section is the most subjective; a reviewer might want it tighter or more concrete, but it satisfies AC.OS.5 as written.

Verdict: doc ships. Plan-doc lands as audit-trail artefact.
