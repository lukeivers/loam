# v0.3.0 Cycle 5 — Terminology consistency + glossary publication

**Status:** Sub-plan-doc, finalised at cycle-dispatch time per `plan-docs-author` SKILL master-vs-sub-plan trim discipline.
**Slug:** `v0-3-0-cycle-5-terminology-consistency-and-glossary`
**Date authored:** 2026-05-08. **Finalised at dispatch:** 2026-05-08.
**Parent master plan:** `docs/plans/v0-3-0-master-plan.md` §3 Cycle 5.
**Predecessor cycles:** C1 sealed `459c7fc` (rebuild-collapse + reference scrub); C2 sealed `013553e` (graphiti rip-out); C3 sealed `be48b34` (foundation-docs gap-fill); C4 sealed `7afb648` (lint pass + cross-mode-debt + F3/F4).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## §1 — Outcome shape (the "why")

Loam-aligned names (substrate / seed / cultivar / growth / amend / seal / contract / objective / capability / banded AC / ratification) used consistently with single canonical definitions. Glossary published at `docs/glossary.md`. A stranger cloning loam at v0.3.0 sees consistent terminology; no "is 'amend' the same as 'patch'?" cognitive bump; cross-references resolve.

The 11 canonical terms divide into three semantic clusters:

- **Loam-metaphor cluster** (substrate, seed, cultivar, growth) — the project's identity metaphor; loam = the enriched medium, seed = user intent, cultivar = the grown agent, growth = how the agent compounds across sessions.
- **Sealed-component-cycle cluster** (amend, seal) — the operational vocabulary of how loam itself is built.
- **ODD cluster** (contract, objective, capability, banded AC, ratification) — the methodology vocabulary used across plans, docs, and SKILLs.

## §2 — Authority sources

Definitions are derived from existing canonical sources, not invented. The glossary records the canonical definition + cross-refs the source-of-truth doc. No new semantics introduced.

| Term | Authority source |
|---|---|
| substrate / seed / cultivar / growth | `docs/FUTURE_IDEAS.md` Idea 12 (loam-rename rationale) + `docs/spec/loam-objectives-spec.md` ("pOS as a seed" addendum) + `docs/VALUE_PROPOSITION.md` (harness/persona framing) |
| amend / seal | `plugins/dev-sdlc/skills/loam-amend-cycle/SKILL.md` + `docs/dev-mode-getting-started.md` §"Run amendment cycles via `loam amend`" |
| contract | `docs/architecture.md` §"The primary-persona contract" + `plugins/dev-sdlc/docs/odd-methodology.md` §1.1 + §2.4-2.5 |
| objective / capability | `docs/odd-llm-grounding.lean.md` §"Four altitudes" + `plugins/dev-sdlc/docs/odd-methodology.md` §1.1 |
| banded AC | `plugins/dev-sdlc/docs/odd-methodology.md` §11 (Confidence bands for derived ACs; VERIFIED / PLAUSIBLE / HYPOTHESISED) |
| ratification | `plugins/dev-sdlc/docs/odd-methodology.md` §11.3 (Promotion and demotion workflow) |

## §3 — Component fence

PRIMARY: `docs/glossary.md` (NEW).

Universal admissions (doc-only edits):
- `docs/` (root + subdirs forward-looking docs only).
- `framework/*/docs/` (per-component docs that use the canonical terms).
- `plugins/dev-sdlc/docs/` (methodology docs).
- `plugins/dev-sdlc/skills/*/SKILL.md` (when the SKILL frontmatter or body uses canonical terms).
- `CLAUDE.md` (root canonical).

Read-only:
- Source code identifiers — no code-level rename refactors (parent §7 OOS).
- Sealed-component source files — no `feat()` / `chore()` to source code.
- `docs/archive/` — historical content frozen.
- `docs/plans/` historical plan-docs — frozen at seal-time; only this cycle's plan-doc is live.

## §4 — AC family — `AC.TGL.*`

`AC.TGL.1` — Glossary published at `docs/glossary.md`. **Test:** `test -f docs/glossary.md` returns 0 (file exists).

`AC.TGL.2` — Glossary contains exactly 11 H2 entries, one per canonical term, in the cluster-grouped order named in §1. **Test:** `grep -c "^## " docs/glossary.md` returns 11 (or ≥11 if non-term H2 sections like "Reading guide" are added; in practice exactly 11 term entries). **Outcome-altitude AC:** glossary ENTRIES count = 11; verified by entry-name sweep, not just H2 count.

`AC.TGL.3` — Each glossary entry carries a single canonical definition (one paragraph, ≤6 sentences) + an "Authority" line cross-referencing the source-of-truth doc per §2 + (where applicable) a "See also" line linking related terms within the glossary. **Test:** every H2-introduced section has both an "Authority" line and ≥1 sentence of definition.

`AC.TGL.4` — Glossary is cross-linked from the load-bearing entry-points: `docs/getting-started.md`, `docs/architecture.md`, `docs/dev-mode-getting-started.md`, `docs/odd-llm-grounding.lean.md`. **Test:** `grep -l "docs/glossary.md\|glossary.md" docs/getting-started.md docs/architecture.md docs/dev-mode-getting-started.md docs/odd-llm-grounding.lean.md` returns all four files.

`AC.TGL.5` — Drift fixes — any forward-looking doc using a canonical term in a way that contradicts the glossary's definition is updated to align. **Test:** Identified drift instances (named in §6 below) are corrected; no NEW drift introduced.

`AC.TGL.6` — Master plan §11 SHA register backfilled with C5 apply + seal SHAs. **Test:** Master plan §11 row "5 — terminology-consistency-and-glossary" no longer reads `(pending)`.

## §5 — Build order (method left to builder; this is sequencing only)

1. Author plan-doc (this commit).
2. Write `docs/glossary.md` with 11 entries.
3. Cross-link from the four entry-point docs (AC.TGL.4).
4. Targeted drift fix sweep (AC.TGL.5).
5. Manifest YAML (schema v3) + sidecar bumps for any sealed-component docs touched (none expected; doc-only is universal-admission).
6. `loam amend apply --plan-doc <plan> <manifest>`.
7. `loam amend seal --plan-doc <plan> <manifest>`.
8. §14 backfill commit with apply + seal SHAs.

## §6 — Drift fixes targeted by this cycle (AC.TGL.5)

A full sweep of 5300+ "amend" / "seal" usages is NOT in scope — most usages are correct technical usages of well-defined terms. The targeted drift fixes are:

- **Glossary cross-links** in the four entry-point docs (AC.TGL.4) — zero, one, or no glossary cross-links currently exist; cycle adds them.
- **No new drift introduced** — the glossary itself uses canonical definitions sourced from §2 authority docs; no novel semantics drift from the existing canonical surface.
- **Spot-check drift** — if during write the builder discovers a forward-looking doc that uses a canonical term in a way that contradicts the glossary's authority definition, fix in this cycle. Surface the count in the build report.

Out of scope at this cycle: bulk find-replace across all 5300+ "seal" usages (most are correct); per-plugin glossaries (parent §7); code-level renames (parent §7).

## §7 — Out of scope (parent + cycle additions)

- Code-level rename refactors (terms inside source code identifiers).
- Plugin-specific terminology (per-plugin glossaries land if/when needed).
- New term creation beyond the 11 canonical terms (additions land in future minors).
- Translation / localization (English-only at v0.3.0).
- Bulk find-replace across 5300+ "amend"/"seal" usages — most are correct; targeted drift fix only.
- Editing `docs/archive/` (frozen historical content) or `docs/plans/` historical plan-docs (frozen at seal-time).

## §8 — Smoke (REALISTIC CONDITION)

Per master plan §6 cycle-altitude smoke. D1 n/a; D2 `grep -c "^## " docs/glossary.md` returns ≥11 + four entry-point docs cross-link the glossary; D3/D4/D5/D6 n/a.

## §9 — Halt-and-surface triggers (in-flight)

1. WD mismatch — immediate halt.
2. Cycle scope expansion beyond §3 fence — halt.
3. A canonical term has multiple legitimate definitions in canonical sources requiring owner ruling — halt + surface in build report.
4. Push or `--amend` attempt — immediate halt.
5. Glossary collides with existing doc that already has equivalent content — halt + surface (verified absent at dispatch start: `find docs -maxdepth 3 -name "glossary*" -o -name "GLOSSARY*"` returned empty).
6. Commit touches files outside `docs/` + relevant `SKILL.md`s + READMEs — halt.

## §10 — F2 RF gaps surfaced this cycle

1. **The 11-term list excludes "harness" and "primary persona".** Both are core loam vocabulary (see `docs/architecture.md` "The one-line shape"). The master plan §3 Cycle 5 explicitly locks the list at 11; foundation-docs (C3 sealed `be48b34`) is where harness + persona are codified at altitude. C5 cross-references those docs from the glossary's "See also" lines but does not claim ownership of those terms. If owner rules differently at review, persona/harness can be added in a v0.3.1 doc-only patch.
2. **"Banded AC" as a glossary term, not "AC".** Plain "AC" (acceptance criterion) is defined exhaustively in `docs/odd-llm-grounding.lean.md` + `plugins/dev-sdlc/docs/odd-methodology.md` §3. The 11-term list names "banded AC" specifically because the band-vs-non-band distinction (extractor-derived vs hand-authored) is the load-bearing semantic newcomer. The glossary entry for "banded AC" cross-references plain AC in the methodology doc.
3. **"Growth" is the weakest term in the cluster.** It appears in `docs/FUTURE_IDEAS.md` Idea 12 ("seed / cultivar / growth metaphor") but does not have a strong canonical operational definition like "amend" or "ratification". The glossary entry frames "growth" descriptively (the metaphor for how the cultivar compounds across sessions) rather than operationally. If owner rules the term doesn't earn glossary inclusion, drop to 10 entries (doc-only patch).

## §11 — Provenance trail

- Master plan `docs/plans/v0-3-0-master-plan.md` §3 Cycle 5 (commit `a8838a9`).
- Release-roadmap `docs/release-roadmap.md` §3 v0.3.0 AC.V030.7.
- Authority sources per §2 above.

## §14 — Method-decision record (backfilled at seal)

| Decision | Choice | Rationale |
|---|---|---|
| Glossary location | `docs/glossary.md` (root of `docs/`) | Cross-cuts every doc cluster; not component-specific. Top-level placement matches `docs/architecture.md`, `docs/getting-started.md` altitude. |
| Entry order | Cluster-grouped (loam-metaphor → sealed-component → ODD) | Matches semantic relatedness; reading order mirrors a stranger's discovery path (project identity → operational cycle → methodology). |
| Cross-link entry-points | 4 (`getting-started`, `architecture`, `dev-mode-getting-started`, `odd-llm-grounding.lean`) | Load-bearing first-read docs for each cluster's audience. Other docs cross-link by their own internal authority refs already. |
| "harness" + "primary persona" | NOT in glossary; cross-referenced from "See also" | Master plan §3 Cycle 5 locks list at 11. Both terms have full-doc canonical definitions in `architecture.md` (`harness`) + `architecture.md` + `personas-methodology.md` (`primary persona`); glossary doesn't double-codify. |
| Drift sweep scope | Targeted (entry-point cross-links + spot-check) | Bulk find-replace would burn ~50× more tool calls without tightening any AC; most existing "amend"/"seal" usages are correct technical usage. Master plan §3 Cycle 5 AI-time band 60–90 min would not accommodate bulk sweep. |
| `loam amend apply` + `seal` | Used despite doc-only universal-admission | Plan-doc authoring discipline: every cycle uses the canonical commit ladder for traceability. Manifest carries no sealed-component fences (universal-admission only); apply + seal land empty manifests for the bookkeeping commit ladder. |
| Apply SHA | (pending — backfilled at seal) | |
| Seal SHA | (pending — backfilled at seal) | |
