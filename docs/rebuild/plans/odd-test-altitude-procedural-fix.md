# ODD test-altitude procedural fix — L1 + L2 + L3-conditional

**Slug:** `odd-test-altitude-procedural-fix`
**Date authored:** 2026-05-05.
**Parent master plan:** N/A (methodology fix, not a v0.2.x cycle).
**Predecessor cycles:** v0.2.4 SHIPPED at `4f54649` (all v0.2.4 cycles sealed; methodology fix lands independently of v0.2.5 corrective in flight).
**Component fence:** `plugins/dev-sdlc/skills/` (3 existing SKILLs edited + 1 new SKILL added) + `docs/odd-llm-grounding.lean.md` (lean grounding doc) — universal-paths admit `docs/`.

## §1 — Outcome shape (the "why")

Three failures observed (v0.2.1 F1, v0.2.1 F2, v0.2.5 F1) all shipped with cycle ACs green; real-world outcomes broke at the release-level HARD smoke gate, requiring corrective amendments. ODD §2.5 enforces traceability across altitudes but doesn't enforce that each AC SET includes a probe at outcome-altitude — so an AC set can pass §2.5 while collectively missing the user-facing outcome.

This fix lands four artefacts that close the procedural gap going forward:

- Pin: every AC set includes ≥1 AC explicitly marked at outcome-altitude (verified by a test invoking the production entry-point, no pre-arrangement bypass).
- Pin: pre-arrangement detection rubric distinguishes STUB-class tests (implementation-altitude only) from OUTCOME-class tests.
- Pin: risk-band classifier (Luke 2026-05-05) governs HARD per-cycle vs release-gate HARD — production-facing surface gets HARD per-cycle; pure-internal refactor / docs can defer.
- Pin: the rule is durable across sessions (memory file) and propagates into plan-author + dispatch-brief surfaces (3 SKILL updates + 1 new SKILL).

## §2 — Lens checks (per CLAUDE.md design lenses)

- **Lens 1 — Claude-leverage-first.** PASS. Composes with the existing SKILL ecosystem (plan-docs-author / plan-before-code-author / dispatch-brief-authoring); does not re-implement.
- **Lens 2 — Harness + primary-persona value.** PASS. Reduces translation burden by giving the persona an operational rubric for AC-altitude classification; adds to the harness toolkit (1 new SKILL + 3 SKILL extensions + 1 doc section + 1 memory rule).
- **Lens 3 — ODD authoring.** PASS. Outcome shape pinned in §1; ACs in §4 each map to a named verification surface; method (specific text in each artefact) is the builder's call.
- **Lens 4 — Prompt scope ↔ confidence.** PASS. High confidence in the rule shape (3 worked instances + Luke's ruling on the L3-conditional reframe); scope is tight (4 named artefacts + named ACs + named verification per AC). No room for the agent to wander.
- **Lens 5 — Swarming.** Single-shot dispatch; no sub-decomposition. Pre-arrangement detection + risk-band classifier are independent rules that compose; no benefit from parallel sub-agents.

## §3 — Single-component fence

In scope:

- `docs/odd-llm-grounding.lean.md` — add "Outcome-altitude AC requirement" section before "Use sequence."
- `plugins/dev-sdlc/skills/odd-test-altitude-discipline/SKILL.md` — NEW SKILL.
- `plugins/dev-sdlc/skills/plan-docs-author/SKILL.md` — extend §4 AC-family authoring guidance + composition.
- `plugins/dev-sdlc/skills/plan-before-code-author/SKILL.md` — extend §4 AC-family authoring guidance + composition.
- `plugins/dev-sdlc/skills/dispatch-brief-authoring/SKILL.md` — extend acceptance-criteria slot.
- `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_test_outcome_altitude_required.md` — NEW memory rule.
- `~/.claude/projects/-Users-lukeivers-pos3/memory/MEMORY.md` — index reference inline.
- `docs/rebuild/STATE.md` — methodology-fix entry inline (post-seal).

Out of fence:

- All code under `plugins/dev-sdlc/odd-extractor/` (no code changes).
- All `framework/` (no framework code or tests touched).
- v0.2.5 corrective C1+C2 in flight — separate dispatch, separate commits.
- Master plan §3 release table — this is a methodology fix, not a v0.2.x release.

## §4 — AC family — `AC.OAA.*`

| AC | outcome-altitude | Acceptance |
|---|---|---|
| **AC.OAA.1** | true | `docs/odd-llm-grounding.lean.md` has a new section "Outcome-altitude AC requirement" stating: every AC set MUST include ≥1 AC at outcome-altitude; outcome-altitude AC is verified by test invoking production entry-point, no pre-arrangement of state production code would produce, produces real outcome artefact; AC schema marks `outcome-altitude: true|false`. Word-count delta ≤150 for the new section. **Verification:** `grep -c "outcome-altitude" docs/odd-llm-grounding.lean.md` ≥3; `wc -w` of new section ≤150. |
| **AC.OAA.2** | true | `plugins/dev-sdlc/skills/odd-test-altitude-discipline/SKILL.md` exists with description front-matter triggering on AC-authoring / test-authoring / test-review; ≥4 sections covering pre-arrangement detection rubric + risk-band classifier + concrete pre-arrangement-bypass example + 4 trigger-points. **Verification:** SKILL.md present at the named path; `grep -c "^## " SKILL.md` ≥4; description front-matter mentions "AC-authoring time" + "test-authoring time" + "test-review." |
| **AC.OAA.3** | true | `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_test_outcome_altitude_required.md` exists capturing the failure pattern (3 instances) + procedural rule + pre-arrangement sub-rule + risk-band sub-rule + composition with ODD §2.5 / `feedback_plan_before_code` / `feedback_loose_AC_text_fix_AC_not_implementation`; MEMORY.md index references it inline. **Verification:** memory file present; `grep -l "feedback_test_outcome_altitude_required" MEMORY.md` returns hit. |
| **AC.OAA.4** | true | `plan-docs-author` SKILL + `plan-before-code-author` SKILL + `dispatch-brief-authoring` SKILL all grep-positive for "outcome-altitude"; each SKILL references the new `odd-test-altitude-discipline` SKILL by path. **Verification:** `grep -l outcome-altitude plugins/dev-sdlc/skills/{plan-docs-author,plan-before-code-author,dispatch-brief-authoring}/SKILL.md` returns 3 paths. |
| **AC.OAA.5** | false | No code changes; no regressions. **Verification:** `git status` shows only doc + SKILL + memory + plan-doc + manifest files modified (no `.py` / `.ts` / `.js` files). Existing test sweep unaffected (release-gate HARD acceptable per risk-band classifier — this fix is doc-only). |

ACs map to artefacts; every artefact is an outcome-altitude probe (grep / file-presence / content-check on the production surface the user invokes).

## §5 — Halt-and-surface BEFORE build (recorded autonomous decisions)

- **WD verification.** `pwd` confirms `/Users/lukeivers/ivers-corp-pos-v2/` per dispatch halt-condition.
- **Pre-existing modifications in tree.** v0.2.5 corrective C1+C2 in flight (interview.py / cli.py / test_AC_V025_C1_C2 modifications + new test). My commit is scoped via explicit `git add` of only my four artefacts + plan-doc + manifest. No `git add -A`.
- **No prior art on `outcome-altitude` SKILL.** Searched `plugins/*/skills/` and `docs/`; term is in use across plan-docs (extraction quality language) but no SKILL or memory rule exists for the test-altitude procedural rule. Adding new SKILL is correct (no duplication).
- **SKILL home — `plugins/dev-sdlc/skills/`** (production-tier SKILLs). Confirmed by inspection of existing SKILL homes: 13 dev-sdlc SKILLs + 10 loam-skills SKILLs; this is a dev-mode procedural rule → dev-sdlc home.
- **Lean doc lacks §-numbering convention.** Used flat heading "Outcome-altitude AC requirement" rather than fabricating §6; matches existing doc convention. Dispatch said "§6 (or whatever the next-numbered section is)" — flat heading is the existing convention.
- **Manifest schema for doc-only methodology fix.** Schema v3 with `dev-sdlc` component. No baseline source-edit because there's no source code; the plan-doc commit + apply commit + seal commit form the audit trail.

## §6 — Smoke (REALISTIC CONDITION)

- **D1 cold-state.** n/a structurally — doc + SKILL files are static markdown read on session-start; no runtime state to cold-start.
- **D2 steady-state.** Verified — `grep -c "outcome-altitude"` returns expected hits across all 4 file paths; AC verifications run from the doc surface.
- **D3 restart.** n/a structurally — no daemon / no in-flight state.
- **D4 reboot.** n/a structurally — markdown files survive reboot trivially.
- **D5 cross-session.** Verified — memory file at `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_test_outcome_altitude_required.md` loads on every fresh session-start via Anthropic auto-memory mechanism; MEMORY.md index references it inline so it appears in session-start corpus.
- **D6 telemetry-floor.** n/a structurally — no audit-log surface affected (this is doc + SKILL; no code emitting events).
- **Full-suite green sweep.** Release-gate HARD acceptable per risk-band classifier (this fix is doc + SKILL + memory only; no production code path affected). Existing dev-sdlc test sweep at HEAD (4f54649) remains green; seal-test confirms no regression.

## §7 — Out of scope

Per dispatch:

- Re-doing past cycles' ACs (sunk-cost; sealed; correctives handle leakage).
- Authoring example HARD-per-cycle tests for any specific component (per-cycle HARD probes get authored when next production-facing cycle dispatches).
- Modifying v0.2.5 corrective C1+C2 in flight (separate dispatch).
- Pushing pos-v2 → lukeivers/loam:main (held until v0.2.5 GREEN).
- Tagging anything.
- Eric outreach.
- Broadening scope beyond L1+L2+L3-conditional (any additional ODD-shaped problem → halt-and-surface, no extension).

## §8 — Halt triggers (in-flight)

- WD drift (≠ `/Users/lukeivers/ivers-corp-pos-v2`).
- Lean doc word-count delta >150 words (means §6 too verbose; trim).
- New SKILL conflicts with existing prior art (search `plugins/*/skills/` first; if found, EXTEND don't duplicate).
- Memory rule conflicts with existing rule (read MEMORY.md; cross-reference).
- `loam amend apply` or `loam amend seal` errors.
- Any push attempt.
- Code change sneaks in (this is doc-only).

## §9 — Bookkeeping

- Manifest: `docs/rebuild/plans/odd-test-altitude-procedural-fix.manifest.yaml` (schema v3).
- Component: `dev-sdlc` (single-component sweep at seal time; SKILLs live under this component).
- Universal admissions: `docs/rebuild/plans/` for plan-doc paper trail + `docs/odd-llm-grounding.lean.md` for the methodology surface.
- Commit ladder:
  1. Plan-doc + manifest commit (`docs(plans): odd-test-altitude-procedural-fix`).
  2. Source-edit commit covering the 5 artefact files (`docs(skills,grounding): outcome-altitude AC requirement + odd-test-altitude-discipline SKILL`).
  3. `loam amend apply <manifest>` lands as merged manifest+apply commit per AC.DPS1.6.
  4. `loam amend seal --plan-doc <abs path> <manifest>` lands as deterministic seal commit.
  5. STATE.md methodology-fix entry inline (separate `docs(state):` commit).
- Tag policy: NOT pushed. Methodology fix; ships independent of v0.2.x release tags.
- §14 backfill: post-seal, fill in the `### Commit SHAs` block.

## §10 — F2 Ruthless Feedback (gaps named this turn)

1. **Memory file is at pos3 path, not pos-v2 path.** Memory rules live globally under `~/.claude/projects/-Users-lukeivers-pos3/memory/` per existing convention. The memory layer is global to the user, not project-local; pos-v2 work loads it via session-start corpus from the global path. Mitigation: this is the existing convention; new file follows it.
2. **No HARD per-cycle probe added for THIS cycle.** This cycle is doc + SKILL only — risk-band classifier puts it in "release-gate HARD acceptable" band. The procedural rule applies forward; this cycle doesn't retroactively probe itself. Mitigation: AC.OAA.1-5 are all outcome-altitude (file presence + grep counts on the production surface = the SKILL files / doc that future readers will load); the verification IS the outcome.
3. **Three SKILL updates may drift over time.** If `plan-docs-author` or `plan-before-code-author` get edited later without preserving the outcome-altitude reference, the rule weakens. Mitigation: memory file `feedback_test_outcome_altitude_required.md` is the durable anchor; SKILLs cite it. If a SKILL drifts, the memory rule keeps the discipline alive and a follow-up correction restores the SKILL reference.
4. **Risk-band classifier list is concrete but not exhaustive.** Edge cases (e.g., a SKILL change that doesn't surface to the user but changes downstream agent behavior) might fall between bands. Mitigation: the SKILL says "production-facing surface" with examples, not a closed enumeration; reviewers extend the list in follow-up amendments as edge cases surface.

## §11 — Provenance trail

- `workspace/.scratch/claude-output/odd-test-altitude-procedural-gap-analysis.md` — gap analysis with 3 worked instances + 3 fix layers + recommendation.
- Owner ruling on L3-conditional reframe: Luke 2026-05-05 Telegram 10188 ("shouldn't need to be default. Can align with things like production facing, etc.").
- v0.2.4 SHIPPED rollup `4f54649`.
- `docs/odd-llm-grounding.lean.md` HEAD (pre-edit) — 723 words.
- ODD §2.5 (lean doc + verbose derivation): every line of code/branch/test maps to a named AC.
- `feedback_plan_before_code` — every build writes a plan-doc to `docs/rebuild/plans/<slug>.md` BEFORE code.
- `feedback_loose_AC_text_fix_AC_not_implementation` — post-build wrong-altitude AC → tighten doc, not retrofit code.
- `feedback_subagent_odd_violation_halt` — halt-and-surface on adjacent ODD violations.

## §12 — Acceptance gate

1. Plan-doc authored at `docs/rebuild/plans/odd-test-altitude-procedural-fix.md`.
2. Manifest authored at `docs/rebuild/plans/odd-test-altitude-procedural-fix.manifest.yaml` (schema v3).
3. AC family AC.OAA.1-5 enumerated with `outcome-altitude` markers.
4. All four artefacts authored: lean doc section / new SKILL / 3 SKILL extensions / memory file + MEMORY.md index.
5. Smoke dimensions covered (D2 + D5 verified; D1/D3/D4/D6 n/a structurally; release-gate HARD acceptable per risk-band classifier).
6. Halt triggers named.
7. F2 RF surfaced (4 gaps).
8. Provenance trail cited.
9. §14 method-decision record present with `## 14.` literal heading.
10. Tag-push policy named (NOT pushed).

## 14. Method-decision record

| Decision | Choice | Rationale |
|---|---|---|
| Section heading shape in lean doc | Flat heading "Outcome-altitude AC requirement" before "Use sequence" | Lean doc has no §-numbering convention; existing headings are flat. Matches doc style. |
| SKILL home | `plugins/dev-sdlc/skills/odd-test-altitude-discipline/` | Production-tier dev-mode SKILLs live in dev-sdlc per dispatch guidance; loam-skills is base/universal-tier. |
| Memory file location | `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_test_outcome_altitude_required.md` | Existing convention for global user-level memory rules; loads cross-session via Anthropic auto-memory. |
| AC schema marker | `outcome-altitude: true|false` field per AC | Dispatch guidance specified marker; explicit boolean simplifies grep + automated review. |
| L3 reframe | NOT blanket per-cycle HARD; conditional on risk band per Luke 2026-05-05 ruling | Owner ruling was explicit; production-facing surface gets HARD per-cycle, internal/docs defer to release-gate HARD. |
| 3 SKILL updates | All three SKILLs reference new SKILL by absolute path under `plugins/dev-sdlc/skills/` | Path-stable references survive SKILL bundle reorganization more reliably than name-only refs. |
| Manifest baseline | Pin to source-edit commit (the 5-file artefact commit) | Matches existing manifest convention; schema v3 expects baseline pointer. |
| Plan-doc + manifest as single docs(plans) commit | Yes | Plan-before-code gate per `feedback_plan_before_code`. |
| Skip §0 in plan-doc | Yes | Dispatch's scope is unambiguous; §0 optional per `plan-before-code-author` SKILL. |

### Commit SHAs

- Amendment commit: `16d6e508f6792b46b90f8e0bcfc5aa1365359920` —
  `chore(amend): odd-test-altitude-procedural-fix manifest+apply — dev-sdlc BASELINE+sidecar bump to a75e2b0`
- Seal commit: `a9bc524be71b794ad68596a05612446a0c6352f0` —
  `chore(seals): odd-test-altitude-procedural-fix — dev-sdlc at 16d6e50`
