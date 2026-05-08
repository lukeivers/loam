# v0.3.0 master plan — Documented features work as advertised AND terminology is consistent

**Status:** master plan-doc; plan-before-code per `feedback_plan_before_code`. Authored 2026-05-08 (Sonnet, master-plan-author dispatch).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.
**Parent authority:** `docs/release-roadmap.md` §3 v0.3.0 — AUTHORITATIVE for objective + ACs + constraints + estimated AI-time.
**Always-load grounding:** `docs/odd-llm-grounding.lean.md`. The §self-checks 1–5 in §8 of that doc were applied to every "objective" / "AC" / "constraint" / "capability" named in this plan-doc; §10 below records the self-check pass.

**Predecessor commits:**
- v0.2.5.1 SHIPPED — apply `b1d5f1e`, seal `7a06034`.
- `docs/release-roadmap.md` HEAD `037aa58` (post v0.6.1 / v0.7.0 C1 reverts; foundation-docs absorbed into v0.3.0 per Luke 2026-05-08).
- `docs/release-versioning-policy.md`, `docs/odd-semver-pinning.md`, `docs/leverage-discipline.md` — sibling methodology + policy docs.
- `docs/plans/v0-3-0-master-plan-authoring-plan.md` — plan-for-the-plan (AC.V030MP.1–7).
- `docs/plans/research/pos3-forward-staging-promotion-classification.md` — foundation-docs research input.
- `docs/plans/foundation-revision-rebuild.md` — FR.1/FR.2/FR.3 plan absorbed into C3.

**Quality bar (META-FRAMEWORK class):** v0.3.0 doesn't ship new user-visible capability. It UNBLOCKS every subsequent minor by making canonical surface honest. A stranger cloning loam at v0.3.0 must verify every named capability operates per docs, hit consistent terminology, and never see "rebuild" residue or graphiti segregation. **No partial close.**

---

## Principles applied this turn

- **CHANNEL** — terminal dispatcher.
- **AUTONOMY** — settle planning decisions; only escalate critical / public-action / financial.
- **F2 RUTHLESS FEEDBACK** — §10 honest doubts surface real tensions.
- **LOCKED-DESIGN-NOT-LICENSE** — release-roadmap §3 v0.3.0 is the locked design at this depth.
- **ODD §2.5** — every named cycle ladders to §2 source-of-truth; per-cycle plan-docs tighten + bind to tests at build time.
- **WD-IN-DISPATCHES** — confirmed at start; propagated to every cycle dispatch brief stub.
- **PLAN-BEFORE-CODE** — sub-plan-doc stubs land in the same commit as this master plan.
- **SCOPE-ONLY** — method specifications (specific scrub regex, FBE.7 verification mechanism, glossary term prose, audit-doc format) are cycle plan-doc responsibility.
- **NEW-SCHEMA OPPORTUNITY** — manifest YAMLs schema v3; seal commits short-form.
- **SWARMING (Lens 5)** — seven cycles each strictly tighter than parent; further decomposition adds only coordination overhead. `max_planner_depth: 1`.
- **TIGHT-VS-LOOSE SCOPE (F4)** — cycle count, ordering, foundation-docs reframe, no-rebuild-terminology, F1a-out-of-scope are TIGHT; per-cycle method choices are LOOSE.
- **TIME-CLAIMS-DISCIPLINE** — AI-time bands per rubric (`wall_clock_minutes ≈ tool_calls × 0.1–0.15`).
- **TEST-AGAINST-OPERATIONAL-OBJECTIVE-BEFORE-ESCALATING** — operational objective is unblocking v0.4.0+ via honest documented surface.
- **NO ANTHROPIC API KEY** — verified in Cycle 6.

---

## §1 — Executive summary

v0.3.0 is the **META-FRAMEWORK foundational-investment minor**. It does not deliver new user-visible capability — it makes the canonical surface honest enough that v0.4.0+ can ladder up safely. Objective sentence (verbatim from `docs/release-roadmap.md` §3): "Loam's documented features work as advertised AND loam's terminology is consistent across forward-looking surface."

**Theme.** Truth-up. Strip residue (rebuild/, graphiti). Codify principles canonically (foundation-docs gap-fill). Verify operational claims (feature-honesty audit). Tighten language (terminology + glossary). Close debt (lint + F3/F4 + cross-mode-debt).

**Foundation-docs absorption.** Per Luke 2026-05-08 ruling, foundation-docs work (formerly mis-framed as v0.6.1 then v0.7.0 Cycle 1, both reverted) absorbs into v0.3.0 because it's the same feature-honesty defect class. R3 reframe: NO new `principles.md` or `odd-principles.md` document; gap-fill into existing surfaces (CLAUDE.md Lens 4/5 + `principle-derivation-map.md` + `odd-methodology.md` + `odd-in-loam.md` re-author). R4: F1a-installer stays fork-only / out-of-scope.

**Cycle count: seven**, serialized per `feedback_serialize_amendment_builds`:

1. **Cycle 1 — rebuild-collapse + reference scrub** (~5300 refs).
2. **Cycle 2 — Graphiti rip-out + FBE.7 memory pivot.**
3. **Cycle 3 — Foundation-docs gap-fill** (principle-derivation-map port; Lens 4/5 merge; F1b/F1c re-author).
4. **Cycle 4 — Lint pass + KNOWN_CROSS_MODE_DEBT shrinkage + F3/F4 closures.**
5. **Cycle 5 — Terminology consistency + glossary publication** (11 canonical terms).
6. **Cycle 6 — Feature-honesty audit + memory FBE.7 verification + claude -p discipline + ODD-conformance sweep.**
7. **Cycle 7 — Release-level smoke gate + STATE.md SHIPPED rollup.**

**AI-time band (per rubric).** Per-cycle midpoints: C1 ~75 min; C2 ~120 min; C3 ~120 min; C4 ~90 min; C5 ~75 min; C6 ~150 min; C7 ~30 min. **Aggregate 8.5–14 hr; midpoint ~11 hr.** Owner gate-review time separate (~70 min across 7 ratifications). Upper edge of parent §3 estimate (6.5–12 hr); foundation-docs absorption + 5300-ref scrub shift the upper band.

**Dependencies.** Inherits all v0.2.5.1 state. Within-minor cycle dependencies named in §3.

**What closes the release.** Seven cycles sealed + C7 release-level smoke gate green: feature-honesty audit 100% match; `ruff` + `mypy` exit 0; `KNOWN_CROSS_MODE_DEBT` strictly decreases; no `docs/rebuild/` files; no graphiti residue; glossary published; `claude -p --strict-mcp-config` invariant verified; FBE.7 stranger-clone passes. If any cycle ships partial, halt and surface.

---

## §2 — Scope source-of-truth

Pulled from `docs/release-roadmap.md` §3 v0.3.0 + composed with foundation-revision-rebuild plan (now absorbed into Cycle 3) + pos3 forward-staging classification research + v0.2.5.1 closing FIDRAFT entries.

### From release-roadmap §3 v0.3.0 (verbatim AC mapping)

| AC | Source-of-truth | Cycle |
|---|---|---|
| AC.V030.1 — Feature-honesty audit at outcome path | `docs/v0-3-0-feature-honesty-audit.md` (NEW) | Cycle 6 |
| AC.V030.2 — Graphiti rip-out | `framework/memory-system/` + `install-from-source.txt` | Cycle 2 |
| AC.V030.3 — Memory FBE.7 stranger-clone verification | Stop hook persists; UserPromptSubmit retrieves | Cycle 2 (impl) + Cycle 6 (verification) |
| AC.V030.4 — `claude -p --strict-mcp-config` regression scan | Repo-wide grep + invariant test | Cycle 6 |
| AC.V030.5 — ODD-conformance sweep on framework components | Per-component objectives.yaml or named exemption | Cycle 6 |
| AC.V030.6 — Lint pass clean | `ruff check framework/ plugins/` + `mypy` | Cycle 4 |
| AC.V030.7 — Terminology + glossary | `docs/glossary.md` (NEW) + sweep | Cycle 5 |
| AC.V030.8 — `docs/rebuild/` collapse | No file under `docs/rebuild/`; redirects preserve | Cycle 1 |
| AC.V030.9 — F3 + F4 close | odd-extractor `_SKIP_DIR_NAMES`; v0.2.1 corrective F1 doc-drift | Cycle 4 |
| AC.V030.10 — KNOWN_CROSS_MODE_DEBT shrinkage | Allowlist count strictly decreases | Cycle 4 |

### Foundation-docs absorption (Cycle 3 scope detail)

Per Luke 2026-05-08 reframe, foundation-docs work absorbs into v0.3.0 Cycle 3 with the following fence:

- **NEW** — `framework/docs/design/principle-derivation-map.md` (port from pos3; AC.FR.1.4 of foundation-revision-rebuild plan).
- **MERGE** — `CLAUDE.md` Lens 4 + Lens 5 append (port from pos3 `framework/CLAUDE.md`).
- **RE-AUTHOR** — `plugins/dev-sdlc/docs/odd-methodology.md` (F1b; pos3 draft + canonical v0.1.8/v0.2.3 surface widening as research input).
- **RE-AUTHOR** — `plugins/dev-sdlc/docs/odd-in-loam.md` (F1c; pos3 draft as research input).
- **EXCLUDED** — `framework/docs/principles/principles.md` and `framework/docs/principles/odd-principles.md` (R3 reframe; gap-fill into existing surfaces, no new principles tier).
- **EXCLUDED** — pos3 `first_run_scaffold.py` F1a-installer + paired test (R4; fork-only; surface as FIDRAFT for future minor if/when triggered).

### NOT in scope at v0.3.0

- Code-gen-from-objectives → v0.4.0.
- Binary-usage observation harness → v0.5.0.
- Non-tech-user ergonomics → v0.6.0.
- Structural enforcement of principles via hooks → v0.7.0 (FR.1/FR.2/FR.3 named primitives + F6 Stop-hook contributor).
- F1a-installer (universal-vs-local principles install) → fork-only / FIDRAFT.
- New principles-tier document → R3 reframe; gap-fill only.
- Graphiti re-implementation → backlog (Luke explicit ruling; trigger if FBE.7 proves operationally inadequate).
- v0.3.0 tag push → owner action separate from cycle ladder; Cycle 7 ratifies; push waits for owner.

### Connection to v0.4.0+

v0.3.0 enables: honest README + getting-started so v0.4.0 code-gen lands against a verified extraction surface; lint-clean Python so new surface lands without inherited debt; consistent terminology so new prose composes; canonical principles + foundation-docs so v0.7.0 structural enforcement has named primitives.

---

## §3 — Cycle decomposition (light per-cycle entry per trim discipline)

Each cycle's full AC enumeration lives in its sub-plan-doc stub at `docs/plans/v0-3-0-cycle-N-<slug>.md`. The stubs land in the same commit as this master plan and finalize at cycle-dispatch time per `plan-docs-author` SKILL master-plan-vs-sub-plan trim discipline.

### Cycle 1 — `docs/rebuild/` collapse + reference scrub

- **Theme.** "Rebuild" is a finished phase; v0.3.0 collapses the subtree so canonical doc-tree has one root.
- **Scope-tightening.** Parent covers feature-honesty + terminology + foundation-docs + lint + audit; C1 narrows to "no `docs/rebuild/` directory exists; ~5300 cross-references resolve to new canonical paths; redirects preserve link integrity for 6 months."
- **Fence.** PRIMARY `docs/rebuild/`. Universal admissions: cross-reference rewrites in `framework/`, `plugins/`, `CLAUDE.md`, `README.md`, root `docs/*.md`. Read-only: sealed-component source code.
- **AC family seed.** `AC.RBC.*` — directory-subtree migration; per-content placement (spec/components/design/plans/archive); cross-reference rewrite (~5300 refs); redirect / archive-pointer mechanism; STATE.md + FUTURE_IDEAS.md grep-discoverable; no broken-link regressions.
- **Smoke.** D1 n/a; D2 `find docs/rebuild/ -type f | wc -l` returns 0; D3/D4/D6 n/a; D5 `grep -rn docs/rebuild .` returns 0 or only-archive-pointer matches.
- **Dependencies.** None (first cycle).
- **Out-of-scope.** No `docs/` reorganization beyond rebuild-subtree absorption; no content edits beyond reference rewrites.
- **AI-time.** ~60–90 min (~500–750 tool calls).

### Cycle 2 — Graphiti rip-out + FBE.7 memory pivot

- **Theme.** Graphiti-the-component is removed; FBE.7 file-backed approach (Stop persists, UserPromptSubmit retrieves) replaces it. Re-implementation is backlog per Luke 2026-05-08.
- **Scope-tightening.** Parent names graphiti rip-out as one AC; C2 narrows to "`framework/memory-system/` no longer references graphiti-core; venv segregation removed; install-from-source.txt graphiti line removed; FBE.7 path implemented; memory tests green on the new path."
- **Fence.** PRIMARY `framework/memory-system/`. Secondary `install-from-source.txt`; cross-references in `framework/`, `plugins/`, root `docs/`. Universal admissions: hook-related code in `framework/primary-persona/` if memory-system surfaces are invoked.
- **AC family seed.** `AC.GRX.*` — directory pruning (launchd plist + `.venv`); install-from-source removal; cross-reference scrub (~60+ refs); FBE.7 implementation (Stop persists; UserPromptSubmit retrieves); workspace state cleanup (`kuzu_db.wal` / graphiti-service logs); memory-system tests green on FBE.7.
- **Smoke.** D1 fresh `framework/memory-system/` install (no graphiti deps); D2 memory test suite green; D3 n/a; D4 launchd-plist absence; D5 deferred to C6 stranger-clone outcome AC; D6 audit-log entries on memory write/read.
- **Dependencies.** None (parallelizable with C1 in principle; serialized per `feedback_serialize_amendment_builds`).
- **Out-of-scope.** Graphiti re-implementation (backlog); memory system feature additions beyond FBE.7 (v0.9.0).
- **AI-time.** ~90–150 min (~750–1250 tool calls).

### Cycle 3 — Foundation-docs gap-fill (port + merge + re-author)

- **Theme.** Canonical principles referenced in docs that don't have canonical text. C3 ports the principle-derivation-map, merges Lens 4 + 5 into CLAUDE.md, and re-authors odd-methodology + odd-in-loam against pos3 drafts as research input.
- **Scope-tightening.** Parent names feature-honesty + terminology + foundation-docs + lint + audit; C3 narrows to "F4/F3/F2/M5 principles are codified in canonical session-start corpus + project-bridge tier reflects v0.1.8 / v0.2.3 surface widening."
- **Fence.** PRIMARY: `framework/docs/design/principle-derivation-map.md` (NEW); `CLAUDE.md` (MERGE — Lens 4 + 5 append); `plugins/dev-sdlc/docs/odd-methodology.md` (RE-AUTHOR — F1b); `plugins/dev-sdlc/docs/odd-in-loam.md` (RE-AUTHOR — F1c). Universal admissions: cross-references resolved.
- **AC family seed.** `AC.FDG.*` — principle-derivation-map port (~358 lines; 28 corpus feedback memories + F2/F3/M5); CLAUDE.md Lens 4/5 additive append (no edits to existing); F1b odd-methodology re-author with v0.1.8/v0.2.3 forward-merge (confidence bands, Ruby/Rails + JS/TS adapters, multi-source synthesis); F1c odd-in-loam re-author (project-bridge framing); Lens 4 cross-reference resolves; NO new principles tier document; F1a-installer fork-only.
- **Smoke.** D1 n/a; D2 `grep -n principle-derivation-map CLAUDE.md` returns Lens 4 cross-reference + file exists; D3/D4/D6 n/a; D5 session-start grounding-doc loader auto-loads new content.
- **Dependencies.** C1 (paths stable for `framework/docs/design/`).
- **Out-of-scope.** New principles tier document (R3 reframe); F1a-installer + test (R4; fork-only); structural enforcement of principles (v0.7.0).
- **AI-time.** ~90–150 min (~750–1250 tool calls; F1b is a 1027-line re-author, F1c is 731-line, principle-derivation-map is 358-line port).

### Cycle 4 — Lint pass + cross-mode-debt shrinkage + F3/F4 closures

- **Theme.** Close out language-tooling debt + named-FIDRAFT items so the lint discipline runs clean every push.
- **Scope-tightening.** Parent names lint + cross-mode-debt + F3/F4 as separate ACs; C4 bundles since each is small (~15–30 min) and shares the code-cleanup theme.
- **Fence.** PRIMARY `framework/` + `plugins/` (lint-fix sweep). Secondary `plugins/dev-sdlc/odd-extractor/` for F3 (`_SKIP_DIR_NAMES` extension). Tertiary methodology surface for F4 v0.2.1 corrective F1 seal-text doc-drift. Universal admissions: `KNOWN_CROSS_MODE_DEBT` allowlist file.
- **AC family seed.** `AC.LDC.*` — `ruff check framework/ plugins/` exit 0; `mypy` exit 0; `KNOWN_CROSS_MODE_DEBT` strictly decreases (target zero); F3 closure (odd-extractor analyze adds `framework/` to `_SKIP_DIR_NAMES`); F4 v0.2.1 corrective F1 seal-text doc-drift resolved.
- **Smoke.** D1 n/a; D2 `ruff` + `mypy` exit 0 + `pytest` green on F3/F4 closure tests; D3/D4/D5/D6 n/a.
- **Dependencies.** C1 (lint sweep clean post-collapse).
- **Out-of-scope.** Type-system migration beyond `mypy` named profile; test-suite restructuring; new ruff/mypy rule additions beyond default profile.
- **AI-time.** ~60–120 min (~500–1000 tool calls; lint-fix iteration variable based on existing violation count).

### Cycle 5 — Terminology consistency + glossary publication

- **Theme.** Loam-aligned names (substrate / seed / cultivar / amend / seal) used consistently with single definitions; glossary-published; ad-hoc usages collapse.
- **Scope-tightening.** Parent names "terminology consistent across forward-looking surface"; C5 narrows to "`docs/glossary.md` exists with 11 canonical terms; doc-only sweep replaces ad-hoc usages; references resolve."
- **Fence.** PRIMARY `docs/glossary.md` (NEW). Universal admissions: doc-only edits across `docs/`, `framework/docs/`, `plugins/`-docs.
- **AC family seed.** `AC.TGL.*` — glossary contains 11 terms (substrate / seed / cultivar / growth / amend / seal / contract / objective / capability / banded AC / ratification); each term single canonical definition + cross-references; doc-only sweep; no orphaned definitions.
- **Smoke.** D1 n/a; D2 `grep -c "^## " docs/glossary.md` returns ≥11; D3/D4/D5/D6 n/a.
- **Dependencies.** C1 (paths stable).
- **Out-of-scope.** Code-level rename refactors; plugin-specific terminology (per-plugin glossaries if/when needed).
- **AI-time.** ~60–90 min (~500–750 tool calls).

### Cycle 6 — Feature-honesty audit + memory FBE.7 verification + `claude -p` discipline + ODD-conformance sweep

- **Theme.** Verify documented surface against operational reality. Stranger-perspective. Last cycle to validate everything else landed correctly.
- **Scope-tightening.** Parent has 4 distinct verification ACs (V030.1, V030.3, V030.4, V030.5); C6 bundles since each is a verification pass against already-shipped surface and they share the audit-altitude theme.
- **Fence.** PRIMARY `docs/v0-3-0-feature-honesty-audit.md` (NEW). Read-only across README, getting-started docs, sealed-component surface, `framework/` components, `plugins/` source (`claude -p` invocations), stranger-clone workspace state. Tertiary: per-component `objectives.yaml` or named exemption; tracked-allowlist for ODD-orphans.
- **AC family seed.** `AC.FHA.*` — stranger-clone audit deliverable; 100% match between named capabilities and sealed-component surface (or named exemption); FBE.7 stranger-clone verification (cold install → session → /clear → next session retrieves prior); `claude -p --strict-mcp-config` invariant test on every loam subprocess; ODD-conformance sweep (per-component `objectives.yaml` or named exemption); orphan triage.
- **Smoke.** D1 fresh-install on stranger-clone; D2 audit-doc cross-references resolve; D3/D4 n/a; D5 FBE.7 cross-session verification (load-bearing outcome); D6 audit-log entries on memory paths.
- **Dependencies.** C1–C5 sealed.
- **Out-of-scope.** New feature additions surfaced during audit (FIDRAFT or future minor); new ODD-conformance enforcement mechanisms (v0.7.0).
- **AI-time.** ~120–180 min (~1000–1500 tool calls).

### Cycle 7 — Release-level smoke gate + STATE.md SHIPPED rollup

- **Theme.** v0.3.0 SHIPPED sealing event. Master plan §3 collapses to STATE.md §2 with seal anchor; release-roadmap updated.
- **Scope-tightening.** Parent names release-level smoke gate; C7 narrows to "release-roadmap §3 v0.3.0 → §2 with seal SHA + apply SHA; STATE.md SHIPPED rollup row added; aggregate cycle-count + tests-green count + smoke verdict named."
- **Fence.** PRIMARY `docs/release-roadmap.md` (§3 → §2 collapse). Secondary `docs/STATE.md` (or post-C1 equivalent path; likely `docs/STATE.md`). Universal admissions: master plan §11 SHA register backfill.
- **AC family seed.** `AC.SHIP.*` — release-roadmap §3 → §2 collapse; STATE.md SHIPPED row (objective sentence + seal anchor); aggregate cycle count = 7; aggregate tests-green count; aggregate smoke verdict; tag-push owner-action-separate.
- **Smoke.** Inherited from C6.
- **Dependencies.** C1–C6 sealed.
- **Out-of-scope.** Tag push, GitHub Releases `--latest`, public-remote push (all owner actions).
- **AI-time.** ~20–45 min (~150–375 tool calls).

### Cycle ladder summary table

| Cycle | Slug | AI-time band | Dependency |
|---|---|---|---|
| 1 | rebuild-collapse-and-reference-scrub | 60–90 min | none (first) |
| 2 | graphiti-ripout-and-fbe7 | 90–150 min | none (parallelizable; serialized per discipline) |
| 3 | foundation-docs-gap-fill | 90–150 min | C1 (paths stable) |
| 4 | lint-pass-cross-mode-debt-f3-f4 | 60–120 min | C1 (lint sweep clean post-collapse) |
| 5 | terminology-consistency-and-glossary | 60–90 min | C1 (paths stable) |
| 6 | feature-honesty-audit-and-verification | 120–180 min | C1–C5 (validates everything landed) |
| 7 | release-level-smoke-gate-and-ship | 20–45 min | C1–C6 (sealed) |

**Aggregate band: 500–825 min ≈ 8.5–14 hr AI-time.** Midpoint ~11 hr. Owner gate-review time separate (~70 min total across 7 cycle ratifications).

---

## §4 — Per-cycle dispatch briefs (stub)

Per-cycle dispatch briefs are authored inline at dispatch time per the `dispatch-brief-authoring` SKILL. Source-of-truth for fence + ACs + smoke + AI-time + out-of-scope lives at §3 above + the cycle sub-plan-doc. Common shape: WD `/Users/lukeivers/ivers-corp-pos-v2/`; LOAD `docs/odd-llm-grounding.lean.md` FIRST; principles per dispatch-brief-authoring SKILL; manifest schema v3; loam amend apply (NOT `--amend`); single semantic commit per cycle (ladder per cycle: plan-doc commit → source-edit commit → apply commit → seal commit → §14 backfill commit); short-form seal; §14 backfill separate; master plan §9 backfill on seal.

---

## §5 — Halt-and-surface BEFORE build (recorded autonomous decisions)

1. **WD confirmed at start.** `pwd` returned `/Users/lukeivers/ivers-corp-pos-v2`. Per `feedback_always_specify_wd_in_dispatches.md`.
2. **Foundation-docs absorption ratified.** Per Luke 2026-05-08, foundation-docs work absorbs into v0.3.0 Cycle 3 (formerly mis-framed as v0.6.1 then v0.7.0 Cycle 1, both reverted). R3 reframe (no new `principles.md`) + R4 (F1a-installer fork-only) hold.
3. **Cycle count locked at 7.** Each cycle's AC is strictly tighter than parent v0.3.0; further decomposition adds only coordination overhead. `max_planner_depth: 1`.
4. **Cycle ordering locked.** C1 first (paths); C2 parallelizable in principle but serialized per discipline; C3/C4/C5 depend on C1; C6 depends on C1–C5; C7 depends on C1–C6.
5. **Sub-plan-doc stubs land in same commit as master plan.** Per master-plan-vs-sub-plan trim discipline; full AC enumeration finalizes at cycle-dispatch time.
6. **No `--amend` in any cycle dispatch.** Per `feedback_no_amend_in_agent_dispatches.md`. Corrective commits land as NEW commits.
7. **No tag push at master-plan landing.** v0.3.0 tag waits for Cycle 7 + owner action separate.
8. **No "rebuild" terminology in any new content.** Cycle 1's job is to scrub existing references; no new content (this master plan + 7 stubs) carries "rebuild" outside historical citation.
9. **Software-as-deliverable framing held.** v0.3.0 is META-FRAMEWORK foundational-investment that unblocks v0.4.0+ code-gen-from-objectives (the prime-deliverable shape per VALUE_PROPOSITION.md).
10. **NO Anthropic API key in any cycle.** Cycle 6's `claude -p` discipline regression scan verifies the invariant on every loam subprocess.

---

## §6 — Smoke (REALISTIC CONDITION — applicable dimensions per smoke-test-discipline.md)

Master-plan altitude smoke gate runs in Cycle 7; per-cycle smoke runs at each cycle's seal. Aggregate dimensions:

- **D1 cold-state** — verified by Cycle 6 stranger-clone fresh-install verification (FBE.7 path).
- **D2 steady-state** — verified by Cycle 4 lint-pass green + Cycle 6 audit-doc cross-references resolve + per-cycle test-suite green sweeps.
- **D3 restart** — n/a (doc-and-lint cycles); inherited from v0.2.5.1 for any service-shaped path.
- **D4 reboot** — verified by Cycle 2 launchd-plist absence (graphiti rip-out).
- **D5 cross-session** — verified by Cycle 6 FBE.7 stranger-clone (cold → session → /clear → session retrieves prior).
- **D6 telemetry-floor** — verified by Cycle 6 audit-log entry verification on memory paths.

**Full-suite green sweep clause.** Cycle 7 release-level smoke confirms `pytest` green + `ruff` exit 0 + `mypy` exit 0 + `find docs/rebuild/ -type f` returns 0 + `grep -rn 'graphiti' framework/memory-system/` returns 0 (or named install-from-source negative match) + audit-doc cross-references all resolve + glossary contains 11 terms.

---

## §7 — Out of scope (explicit deferrals)

- v0.4.0 code-gen-from-objectives, ProgramBench v0 docs-only baseline, Routines integration.
- v0.5.0 binary-usage observation harness.
- v0.6.0 non-tech-user surface, channel-config slot, memory-doc template.
- v0.7.0 structural enforcement of principles via hooks/skills/Stop-hook contributors (FR.1/FR.2/FR.3 named primitives + F6 + meta-decision-haiku SKILL).
- F1a-installer (universal-vs-local principles install) — fork-only; FIDRAFT for future minor.
- New `principles.md` / `odd-principles.md` document (R3 reframe; gap-fill into existing surfaces).
- Graphiti re-implementation — backlog (Luke explicit 2026-05-08; trigger if FBE.7 proves operationally inadequate at production-stake usage).
- Code-level rename refactors (terms inside source code identifiers).
- v0.3.0 tag push (owner action separate).

---

## §8 — Halt triggers (in-flight)

Conditions that fire during cycle execution stop the build for surface-and-RF (not master-plan-author halts; those go to §5 above):

1. Any cycle's actual AI-time exceeds upper band by >50% — surface for owner ruling on scope split or carry to v0.3.1.
2. Any cycle's AC count grows beyond what the sub-plan-doc seeds — surface for ODD §2.5 violation triage.
3. Cycle 6 feature-honesty audit reports < 100% match without named exemption — surface for owner ruling on whether the gap is a real feature gap (close as PATCH within v0.3.0) or a docs-claim gap (rewrite docs).
4. Cycle 4 lint pass fails after 3 fix iterations — surface for owner ruling on lint-rule scope or named exemption.
5. Cycle 2 FBE.7 verification fails on stranger-clone — surface for owner ruling on whether to ship v0.3.0 with memory-system in a degraded state (named exemption) or block on FBE.7 fix.
6. Cycle 3 odd-methodology re-author can't merge v0.1.8/v0.2.3 forward without semantic loss — surface for owner ruling on partial re-author + carry-forward residue.
7. Push or `--amend` attempt in any cycle — immediate halt; corrective NEW commit + RF surface.

---

## §9 — Bookkeeping

- **pos-amend usage.** Every cycle that touches sealed-component fences uses `loam amend apply` (NOT `--amend`); manifest schema v3; sealed-component fence per cycle's plan-doc §3.
- **Plan-doc commit ladder per cycle.** (1) plan-doc commit (`docs(plans):`); (2) source-edit commit (`feat(<comp>):` / `chore(<comp>):` / `docs(<surface>):` per content); (3) apply commit (`chore(amend):`); (4) seal commit (`chore(seals):` short-form); (5) §14 backfill commit (`docs(plans): record v0-3-0-cycle-N commit SHAs`).
- **§14 backfill.** Each cycle's sub-plan-doc §14 records the 5 commit SHAs post-seal. Master plan §11 (this doc, below) holds the canonical SHA register table — backfilled per cycle.
- **Master plan §9 SHA register.** Per-cycle Apply / Seal SHAs land at master plan §11 below as cycles seal. STATE.md SHIPPED row summarizes (cycle count + key seal SHAs + tests-green count + smoke verdict) without repeating the full ladder.
- **Tag-push policy.** v0.3.0 tag waits for Cycle 7 + owner action separate. No tag push in any cycle.
- **No `--amend`** in any cycle. Corrective commits = NEW commits.

---

## §10 — F2 Ruthless Feedback (gaps named this turn)

1. **Cycle count at upper edge of 1-3 hr target.** Per parent AC.V030MP.2. C2/C3 (90–150 min) and C6 (120–180 min) sit at or above the 3-hr ceiling at upper band. Each is bundled because sub-decomposition adds only coordination overhead. If any exceeds 3 hr at dispatch, halt-trigger §8.1 fires; C6 could split into C6a (audit + claude -p + ODD-conformance) and C6b (FBE.7 + ratification).
2. **Foundation-docs absorption increases v0.3.0 scope materially.** Parent estimate 6.5–12 hr becomes 8.5–14 hr with C3 absorption. Still within upper-band; META-FRAMEWORK class accepts foundational-investment cost. If actuals exceed 14 hr, retrospective considers whether foundation-docs warrant their own minor (v0.3.1).
3. **Cycle 1 touches ~5300 references.** Bulk-edit-shaped but volume creates regression risk. C1 sub-plan-doc bakes redirect / archive-pointer mechanism into AC; C6 cross-reference-resolution verification catches regressions. 5300 refs may include indirect references via templates / generators; surface to C1 dispatch.
4. **Cycle 4 bundling (lint + cross-mode-debt + F3/F4).** Three semi-orthogonal items in one cycle; each individually small. If lint-pass iteration burns more than expected, F3/F4 closures could starve; halt-trigger §8.4 catches.
5. **Cycle 5 tightly coupled to Cycle 1 paths.** Glossary references canonical paths post-collapse. If C1 reorganization differs from master-plan expectation, C5 plan-doc updates. Serial dependency named in §3.
6. **No new principles tier document.** R3 reframe holds per Luke 2026-05-08. If v0.7.0 structural enforcement later wants a single canonical principles document, gap-fill-into-existing-surfaces may need consolidation forward. That's v0.7.0's plan-author's problem.
7. **Cycle 6 stranger-clone verification has external dependency.** Fresh machine or sandboxed-equivalent. C6 sub-plan-doc names verification mechanism (Docker-equivalent or actual fresh machine). If stranger-clone verification can't execute at AI-time, the AC moves to release-roadmap §6 owner-action-line and C6 names that explicitly.

---

## §11 — Provenance trail + canonical SHA register

### Provenance trail

- `docs/release-roadmap.md` §3 v0.3.0 — AUTHORITY for objective, ACs, constraints, AI-time bands.
- `docs/release-versioning-policy.md` — SemVer commitment + class tags + quality gate.
- `docs/odd-semver-pinning.md` — cycle-vs-minor composition rules.
- `docs/leverage-discipline.md` — rubric for cycle prioritization.
- `plugins/dev-sdlc/skills/plan-docs-author/SKILL.md` — canonical plan-doc shape.
- `plugins/dev-sdlc/skills/dispatch-brief-authoring/SKILL.md` — cycle dispatch shape.
- `docs/plans/research/pos3-forward-staging-promotion-classification.md` — foundation-docs research input.
- `docs/plans/foundation-revision-rebuild.md` — FR.1/FR.2/FR.3 plan absorbed into C3.
- `docs/plans/v0-3-0-master-plan-authoring-plan.md` — plan-for-the-plan; AC.V030MP.1–7.

### Canonical SHA register (backfilled as cycles seal)

| Cycle | Apply SHA | Seal SHA |
|---|---|---|
| 1 — rebuild-collapse-and-reference-scrub | `e80437b` | `459c7fc` |
| 2 — graphiti-ripout-and-fbe7 | `39094ea` | `013553e` |
| 3 — foundation-docs-gap-fill | `ad12cc1` | `be48b34` |
| 4 — lint-pass-cross-mode-debt-f3-f4 | (pending) | (pending) |
| 5 — terminology-consistency-and-glossary | (pending) | (pending) |
| 6 — feature-honesty-audit-and-verification | (pending) | (pending) |
| 7 — release-level-smoke-gate-and-ship | (pending) | (pending) |

---

## §12 — Acceptance gate (pre-cycle conditions)

- [x] Master plan + 7 cycle stubs land in one commit.
- [x] 7 cycles in dependency order; each entry: theme + scope-tightening + fence + AC seed + smoke + deps + OOS + AI-time.
- [x] Word count within 2500–4500 target.
- [x] Foundation-docs absorption (C3); R3 reframe; R4 F1a fork-only — all named.
- [x] No "rebuild" framing in new prose; no Anthropic API key in any cycle.
- [x] Composes with release-roadmap §3 (references; doesn't duplicate).
- [x] §10 F2 RF surfaces 7 honest doubts; §8 halt triggers named.
- [x] §9 bookkeeping per `loam amend` + schema v3 + commit-ladder + tag-push policy.

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

| Decision | Choice | Rationale |
|---|---|---|
| Cycle count | 7 | Each cycle's AC strictly tighter than parent v0.3.0; further decomposition adds only coordination overhead (Lens 5). C4 + C6 bundle 2–4 semi-orthogonal items because per-item decomposition would add micro-cycles with no AC tightening. |
| Cycle ordering | C1 first (paths); C2 service-altitude; C3/C4/C5 depend on C1; C6 depends on C1–C5; C7 final | C1 stabilizes paths so all subsequent cycles reference canonical post-collapse paths. C6 is the validation pass. C7 is the sealing-event ceremony. |
| Foundation-docs absorption | Into C3 (not separate v0.3.1) | Per Luke 2026-05-08. Same feature-honesty defect class as parent v0.3.0 outcome. |
| F1a-installer scope | OUT OF SCOPE (fork-only / FIDRAFT) | Per parent R4 + foundation-revision-rebuild §D9. |
| New `principles.md` / `odd-principles.md` | OUT OF SCOPE (R3 reframe; gap-fill only) | Per Luke 2026-05-08. Pos3 draft is RESEARCH INPUT only; gap-fill into existing surfaces. |
| Sub-plan-doc stub timing | Stubs land in same commit as master plan | Per `plan-docs-author` SKILL master-vs-sub-plan trim discipline. Full AC enumeration finalizes at cycle-dispatch time. |
| C4 bundling (lint + debt + F3/F4) | Bundled | Each item ~15–30 min; avoids 3 micro-cycles with no AC tightening. |
| C6 bundling (audit + claude -p + FBE.7 + ODD-conformance) | Bundled | All four are verification passes against already-shipped surface; share the audit-altitude theme. F2 RF §10.1 surfaces honest doubt; halt §8.5 catches FBE.7 failure for split decision. |
| C7 separate from C6 | Separate | C6 is validation; C7 is sealing ceremony. Separating preserves per-minor sealing convention. |
| AI-time bands per cycle | Range + midpoint per `wall_clock_minutes ≈ tool_calls × 0.1–0.15` | Per duration-estimation-rubric. Aggregate 8.5–14 hr; midpoint ~11 hr. |
| `max_planner_depth` | 1 | Per Lens 5. Cycle plan-doc author may decompose at dispatch time if confidence drops. |
| No "rebuild" terminology in body | Held | Per parent constraint. Historical references unavoidable (C1's job to scrub); no NEW prose carries "rebuild" framing. |
| Tag-push policy | Owner-action-separate; no tag push in any cycle | Per `docs/release-versioning-policy.md` §Tagging. |
