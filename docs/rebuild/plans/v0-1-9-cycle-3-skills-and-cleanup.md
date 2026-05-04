# v0.1.9 Cycle 3 — 6 dev-sdlc SKILLs (second pass) + audit-allowlist cleanup

**Slug:** `v0-1-9-cycle-3-skills-and-cleanup`
**Date authored:** 2026-05-04.
**Parent master plan:** `docs/rebuild/plans/v0-1-9-master-plan.md` §4 Cycle 3 (sealed at `b01d3eb`).
**Predecessor cycles:** v0.1.9 Cycle 1 (`790807d`) + Cycle 2 (`0dc557e`).
**Component fence:** single-component fence on `plugins/dev-sdlc/`.

---

## §1 — Outcome shape (the "why")

The first pass (v0.1.8 Cycle 5, sealed `e4512b9`) shipped 6 dev-sdlc SKILLs covering the highest-leverage rituals (loam-amend-cycle, dispatch-brief-authoring, plan-before-code-author, fidraft-capture, front-load-principle-walk, audit-finding-triage). The layered-skills research §5 second-pass list (lines 506–511) named 6 more rituals worth codifying as discoverable SKILLs:

1. `seal-narrative-writer` — the short-form seal narrative shape post-amendment-2 (summary + plan-doc reference, NOT a duplicate).
2. `plan-docs-author` — plan-doc authoring per the dev-sdlc methodology (objective + scope + ACs + halt triggers + §14 method-decision register with `## 14.` heading).
3. `hook-violation-recovery` — recovery walk when a pre-commit / pre-push hook fires a violation (route to ratification vs revisit AC).
4. `component-scaffold-author` — authoring a NEW component scaffold (pyproject.toml + src/ + tests/ + seals/ + README) from the standard template.
5. `graceful-fallthrough-with-detection` — graceful-degradation pattern: every fallback path includes detection so silent failures get surfaced.
6. `loam-amend-status-quick` — quick-status check on the amendment cycle's progress (which commits landed, what's left, current AC coverage).

Plus an audit-allowlist cleanup: shrink `KNOWN_CROSS_MODE_DEBT` in `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_references.py` from 5 to 1 entry — the 4 stale entries (1× primary-persona prompt template + 3× workspace-sync README) genuinely have zero source-file matches at master-plan-author time; the 5th entry (memory-system/launchd) is a still-valid pending-debt and stays. FIDRAFT line 143 closes on this seal.

After this cycle seals, all 12 dev-sdlc SKILLs are auto-discoverable (8 base loam-skills + 12 = 20 total), and v0.1.9 closes with the release-level SOFT smoke gate per master plan §5.

The deeper objective: `feedback_durable_capture_for_planned_work` + `feedback_dispatch_brief_authoring` + the broader observation that ritualised authoring discipline is teachable to fresh-session personas only when codified at a discoverable surface. Six more SKILLs raise the floor on what a stranger running `claude` with the dev-sdlc plugin enabled can execute correctly without re-deriving from memory feedback files.

---

## §2 — Lens checks (per CLAUDE.md design lenses)

**Lens 1 — Claude-leverage-first.** SKILL packages compose on Anthropic's native SKILL discovery (frontmatter + body shape per https://code.claude.com/docs/en/skills). The auto-symlink mechanism is v0.1.7 Cycle 3 (`bcf699a`) — load-bearing. We do NOT re-implement skill discovery; we author content that the existing primitive serves. ✓

**Lens 2 — Harness + primary-persona value.** Each SKILL reduces the translation burden between "Luke wants the amendment cycle to ship correctly" and "the agent executes the ritual without re-deriving steps." Adds to the dev-sdlc primary persona's toolkit — every SKILL is a pre-built lever the persona can pull when the trigger condition fires. ✓

**Lens 3 — ODD authoring.** Every SKILL.md and the audit-allowlist edit map to a named AC (AC.SKILLS-DSDLC2.1..8 + AC.AUDIT-CLEANUP.1..3). No non-objective code. ✓

**Lens 4 — Prompt scope ↔ confidence.** High confidence in the right outcome shape (first pass at v0.1.8 Cycle 5 verified the 6-section body pattern works). Tight scope per master plan §4 Cycle 3 dispatch brief. The SKILL bodies have method-freedom inside the section structure (length, examples, depth) — tight scope, not method-in-acceptance. ✓

**Lens 5 — Swarming.** The 6 SKILLs share shape; per Lens 5 stopping criterion, decomposing into 6 sub-dispatches adds only coordination overhead without tightening any subtask's AC (each SKILL's AC is already at irreducible single-file shape). Stays as a single sealed-component build. Audit-allowlist edit is part of the same single-component fence. ✓

---

## §3 — Single-component fence

Single-component fence on `plugins/dev-sdlc/`. Two surfaces inside the fence:

- **6 new SKILL.md packages** at `plugins/dev-sdlc/skills/<name>/SKILL.md`:
  - `seal-narrative-writer/`
  - `plan-docs-author/`
  - `hook-violation-recovery/`
  - `component-scaffold-author/`
  - `graceful-fallthrough-with-detection/`
  - `loam-amend-status-quick/`
- **`KNOWN_CROSS_MODE_DEBT` shrink** from 5 to 1 entry at `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_references.py`.
- **Regression tests** at `plugins/dev-sdlc/tests/`:
  - `test_AC_SKILLS_DSDLC2_1_seal_narrative_writer_skill_present.py`
  - `test_AC_SKILLS_DSDLC2_2_plan_docs_author_skill_present.py`
  - `test_AC_SKILLS_DSDLC2_3_hook_violation_recovery_skill_present.py`
  - `test_AC_SKILLS_DSDLC2_4_component_scaffold_author_skill_present.py`
  - `test_AC_SKILLS_DSDLC2_5_graceful_fallthrough_with_detection_skill_present.py`
  - `test_AC_SKILLS_DSDLC2_6_loam_amend_status_quick_skill_present.py`
  - `test_AC_SKILLS_DSDLC2_7_all_twelve_skills_discovered.py` (extends Cycle-5 walk to include both passes)

No edits to other components. `docs/rebuild/plans/` admitted via `universal_paths` for the plan-doc paper trail. STATE.md / odd-methodology / CLAUDE.md left untouched at cycle-time (release-level rollup happens post-smoke-gate).

---

## §4 — AC family

### `AC.SKILLS-DSDLC2.*` (SKILL packages)

- **AC.SKILLS-DSDLC2.1 — `seal-narrative-writer` SKILL.md.** File at canonical path; YAML frontmatter with non-empty `description` ≤1536 chars; non-empty markdown body; body covers the short-form seal narrative shape (mentions `summary` / `plan-doc` / `narrative` / `seal`). Composes with `loam-amend-cycle`.
- **AC.SKILLS-DSDLC2.2 — `plan-docs-author` SKILL.md.** File at canonical path; frontmatter valid; body covers the plan-doc structural skeleton (mentions `objective` / `acceptance` / `halt` / `method-decision`). Composes with `plan-before-code-author`.
- **AC.SKILLS-DSDLC2.3 — `hook-violation-recovery` SKILL.md.** File at canonical path; frontmatter valid; body covers the recovery walk (mentions `hook` / `violation` / `ratification` / `revisit`). Composes with `audit-finding-triage`.
- **AC.SKILLS-DSDLC2.4 — `component-scaffold-author` SKILL.md.** File at canonical path; frontmatter valid; body covers the new-component scaffold (mentions `pyproject` / `tests` / `seals` / `scaffold`). Composes with `loam-amend-cycle`.
- **AC.SKILLS-DSDLC2.5 — `graceful-fallthrough-with-detection` SKILL.md.** File at canonical path; frontmatter valid; body covers the pattern (mentions `fallback` / `degradation` / `detection` / `surface`). Composes with `audit-finding-triage`.
- **AC.SKILLS-DSDLC2.6 — `loam-amend-status-quick` SKILL.md.** File at canonical path; frontmatter valid; body covers the quick-status check (mentions `status` / `commit` / `coverage` / `progress`). Composes with `loam-amend-cycle`.
- **AC.SKILLS-DSDLC2.7 — All 12 dev-sdlc SKILLs auto-discoverable.** Walking `plugins/dev-sdlc/skills/` yields exactly the 12 expected SKILL package directories (6 from v0.1.8 Cycle 5 first pass + 6 from this cycle), each containing a valid `SKILL.md`. Each package has valid YAML frontmatter with non-empty description ≤1536 chars.
- **AC.SKILLS-DSDLC2.8 — Regression test per SKILL.** ≥7 new pytest files in `plugins/dev-sdlc/tests/`: 6 per-SKILL presence tests + 1 cross-check walk. Each per-SKILL test asserts file existence, frontmatter validity, body non-empty, and key terms present.

### `AC.AUDIT-CLEANUP.*` (audit-allowlist cleanup)

- **AC.AUDIT-CLEANUP.1 — `KNOWN_CROSS_MODE_DEBT` shrunk to exactly the one valid entry.** The set literal in `test_partition_references.py` contains exactly the `framework/memory-system/launchd/README.md → docs/rebuild/components/true-first-run/research.md` entry; the 4 stale entries (1× primary-persona prompt + 3× workspace-sync README) are removed.
- **AC.AUDIT-CLEANUP.2 — `test_AC_F3_always_loaded_no_dev_refs` passes after the shrink.** No test regression; the audit scan against the live tree yields exactly 1 cross-mode reference (the memory-system entry) which is then absorbed by the shrunk allowlist; the equality check (flagged == allowlist) passes.
- **AC.AUDIT-CLEANUP.3 — Source-file scan of removed pairs returns zero matches.** Empirical post-edit verification: grep for each of the 4 removed (source, target) pairs in the live source files returns 0 matches. (Pre-flight already verified at master-plan-author time; this AC re-verifies at cycle-build-time per master plan §7.8 honest-doubt mitigation.)

---

## §5 — Halt-and-surface BEFORE build (recorded autonomous decisions)

Per `feedback_strict_autonomy_no_pause_for_authorized_work` + master plan halt-trigger discipline.

1. **WD confirmation.** `pwd` confirms `/Users/lukeivers/ivers-corp-pos-v2`. Done at turn-start.
2. **Predecessors sealed.** Cycle 1 (`790807d`) + Cycle 2 (`0dc557e`) verified at the start. v0.1.7 Cycle 3 (`bcf699a`) verified as predecessor.
3. **First-pass SKILLs verified existent.** `plugins/dev-sdlc/skills/` listing confirmed: 6 directories from v0.1.8 Cycle 5 + the flat-file `start-project.md` from v0.1.0.
4. **Audit-allowlist pre-flight re-verified.** Empirical grep at cycle-build-time: 4 stale pairs match 0 in source; 1 valid pair (memory-system) matches 1.
5. **Section-body shape locked to first-pass pattern.** 6 sections — `What captures / When to use / How persona applies it / Graceful degradation / Composition / Out of scope`. Lens 4 high-confidence → adopt verified pattern.
6. **Test granularity locked to per-AC convention.** 7 new test files — one per SKILL + one cross-check walk, mirroring v0.1.8 Cycle 5's pattern.
7. **No `_common/`-style helper.** Each SKILL is self-contained; no cross-skill code sharing.
8. **No sub-dispatches.** Single-agent build per Lens 5 stopping criterion (sub-dispatches add coordination overhead without tightening any subtask's AC).

---

## §6 — Smoke (REALISTIC CONDITION — all 6 dimensions per smoke-test-discipline.md §6)

- **D1 cold-state.** Fresh canonical workspace shows all 12 dev-sdlc SKILLs in `/` menu. Verified by `test_AC_SKILLS_DSDLC2_7_all_twelve_skills_discovered.py` walking `plugins/dev-sdlc/skills/` + asserting each contains a valid SKILL.md. Inherited from layered-skill mechanism (auto-symlink at first-run scaffold per v0.1.7 Cycle 3 `bcf699a`). Audit-allowlist shrunk to 1 entry.
- **D2 steady-state.** SKILLs survive across N (≥5) sessions; allowlist test stable. Inherited structurally — the SKILL files are persistent on-disk state; `test_AC_F3_always_loaded_no_dev_refs` is deterministic given a fixed source tree.
- **D3 restart.** Process restart preserves SKILL discovery (no long-running daemon involved; one-shot scaffold). Inherited from filesystem persistence.
- **D4 reboot.** macOS reboot equivalent — filesystem state survives. Inherited from filesystem persistence; no launchd dependency for SKILL surface.
- **D5 cross-session.** SKILLs visible after `/clear`. Most-load-bearing dimension. Inherited from Anthropic's native discovery primitive; verified at v0.1.7 Cycle 3 mechanism level.
- **D6 telemetry-floor.** SKILL discovery events emit per layered-skill audit-trail floor (inherited from v0.1.7 Cycle 3 + audit-trail discipline at v0.1.6 Cycle 1).

PLUS: full-suite green sweep — at least 501 dev-sdlc parent tests at HEAD `e4512b9` (Cycle 5 seal) all pass post-Cycle-3; halt + surface on any regression. This cycle adds ~7 new test functions; expected post-cycle test count ≥508.

PLUS: release-level SOFT smoke gate (master plan §5) runs AFTER this cycle seals — separate from this amendment cycle's smoke.

---

## §7 — Out of scope (Cycle 3)

- Continuous codebase-watch → v0.2.0 (per master plan §3 + research §6).
- Auto-skill-creation mechanism → v0.2.0.
- Promotion rubric (which SKILLs merit graduation to a base loam-skills shape) → v0.2.1.
- Real OSS PR-safety smoke → v0.2.1 release-gate.
- Memory-system/launchd/README.md scrub → future memory-system amendment (the 1 remaining allowlist entry stays).
- Adding more than 6 SKILLs in this cycle (the second-pass list locked at 6 per layered-skills §5).
- SKILL body length / example count / cross-skill linking depth — method-freedom per Lens 4 tight scope; the AC pins the body covers the ritual + key terms but does not pin length.

---

## §8 — Halt triggers (in-flight)

- WD drifts → halt + surface.
- Plan-doc not authored before code → halt.
- Any SKILL frontmatter invalid → halt + RF.
- Any SKILL body is a stub or aspirational placeholder → halt + RF (quality bar — first pass set the precedent, every body covers the FULL ritual).
- Audit-allowlist edit removes the still-valid memory-system entry → halt + RF.
- `test_AC_F3_always_loaded_no_dev_refs` fails post-edit → halt + RF (the failure says either I removed an entry that's still in source, OR a new cross-mode reference appeared since pre-flight).
- Live `/` menu fails to show any of the 12 → halt (this is the ship-test).
- Cycle exceeds 5 hours wall-clock → halt + describe.
- ODD violations in surrounding code → halt + surface.
- More than 3 escalations needed → halt + describe.
- Release-level smoke fails on any dimension → halt + surface; do NOT mark v0.1.9 SHIPPED.

---

## §9 — Bookkeeping

- pos-amend apply (NOT `git commit --amend`) per `feedback_no_amend_in_agent_dispatches`.
- Manifest schema v3.
- Single semantic commit (merged manifest+apply per AC.DPS1.6).
- Short-form seal commit per AC.DPS2.{1,4,6}.
- §14 method-decision-register backfill in a separate post-seal commit.
- Backfill master plan §9 row for Cycle 3 (apply + seal SHAs).
- Backfill v0.1.9 release-level rows (STATE.md + roadmap §8 + eric-final-delivery §2) with all 3 cycle SHAs + SHIPPED status — only AFTER release-level smoke passes.
- Close FIDRAFT line 143 entry (audit-allowlist drift) on seal — note Cycle 3 seal SHA.
- DO NOT push tags. v0.1.9 sits as a local release.

---

## §10 — F2 Ruthless Feedback (gaps named this turn)

**10.1 — `loam-amend-status-quick` may have low fire-rate.** Per master plan §7.7, operators rarely query status interactively. Mitigation: ship as-named (full-12 commitment per parent §2); even low-fire-rate SKILLs raise the floor for fresh-session personas who DO need to query status when a cycle goes sideways. Body emphasises the diagnostic-when-stuck use case.

**10.2 — `component-scaffold-author` fire-rate is rare.** New components are rare events. Mitigation: when they DO happen, the cost of getting the scaffold wrong is high (sealing-readiness + sidecar shape + manifest schema). The SKILL is cheap insurance against the high-cost rare event.

**10.3 — `hook-violation-recovery` ritual is operator-driven.** Different from the agent-side dispatch. Mitigation: SKILL body explicitly names the operator-vs-agent split; `audit-finding-triage` is the dispatcher-side response, this SKILL is the operator-side response when a hook fires locally.

**10.4 — `seal-narrative-writer` may overlap with `loam-amend-cycle` step 6.** Mitigation: `loam-amend-cycle` covers the WHOLE ladder; this SKILL drills into the seal-narrative-specific shape post-amendment-2 (short-form per dev-pattern-simplifications-2 sealed at `df3f50f`). Composes-with section names the relationship.

**10.5 — `graceful-fallthrough-with-detection` is a coding pattern, not an authoring ritual.** Different shape from the other 5. Mitigation: codify as a SKILL anyway — the Anthropic SKILL primitive handles both ritual and pattern shapes. Body emphasises the detection clause (the load-bearing piece that distinguishes this from plain graceful-fallback).

**10.6 — `plan-docs-author` overlaps with first-pass `plan-before-code-author`.** Mitigation: first-pass covers the ODD-shaped plan-doc skeleton (the WHEN); this SKILL drills into the AUTHORING execution per the dev-sdlc methodology (the HOW-of-authoring with §14 method-decision register specifically). Composes-with section makes the layered relationship explicit.

---

## §11 — Provenance trail

- **Master plan source:** `docs/rebuild/plans/v0-1-9-master-plan.md` §4 Cycle 3 dispatch brief (sealed at `b01d3eb`).
- **Cycle 1 (predecessor):** sealed `790807d`; PR-safety gate engine + override workflow.
- **Cycle 2 (predecessor):** sealed `0dc557e`; hook installers + 3 CI templates + provenance-traceable PR description.
- **v0.1.8 Cycle 5 (first-pass SKILLs):** sealed `e4512b9`; 6 dev-sdlc SKILLs; pattern reference for body shape + test pattern.
- **v0.1.7 Cycle 3 (layered-skill discovery mechanism):** sealed `bcf699a`; auto-symlink primitive load-bearing for AC.SKILLS-DSDLC2.7.
- **dev-pattern-simplifications-2 (short-form seal narrative):** sealed `df3f50f`; reference for `seal-narrative-writer` body content.
- **Layered-skills research §5 (12-SKILL list, second-pass at lines 506–511):** `docs/rebuild/plans/layered-skill-story-research-2026-05-04.md`.
- **FIDRAFT line 143 (audit-allowlist drift):** captured 2026-05-04 during v0.1.8 Cycle 5 release-level smoke; graduates here.
- **Empirical pre-flight (audit-allowlist staleness verified at master-plan-author time):** 4 pairs match 0; 1 valid match. Re-verified at cycle-build-time per AC.AUDIT-CLEANUP.3.
- **Pre-cycle baseline:** 501 dev-sdlc parent tests at HEAD `e4512b9` (post-Cycle-5 sweep result).
- **Quality bar (Luke directive 2026-05-04):** master plan §1 verbatim; turn-dispatch quality bar.
- **Smoke-test discipline:** `plugins/dev-sdlc/docs/smoke-test-discipline.md`.
- **Schema v3:** `docs/rebuild/plans/dev-pattern-simplifications-1.md` (DPS1) + `dev-pattern-simplifications-2.md` (DPS2).
- **Lens 5 (swarming):** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_swarming_recursive_decomposition.md` + framework/CLAUDE.md.

---

## §12 — Acceptance gate

Per master plan §4 Cycle 3 dispatch brief halt-triggers:

1. WD = canonical pos-v2 — done.
2. Predecessors sealed (Cycle 1 + Cycle 2 + v0.1.7 Cycle 3) — done.
3. First-pass SKILLs verified existent (6 dirs at `plugins/dev-sdlc/skills/`) — done.
4. Audit-allowlist pre-flight re-verified empirically — done.
5. Plan-doc authored BEFORE code — this file (current commit lands first; source-edit follows).
6. Manifest schema v3 — see `.manifest.yaml` companion.
7. AC families locked at §4 — done.
8. Method-decision register populated at §14 — done (below).
9. Smoke dimensions covered (all 6) — done at §6.
10. Bookkeeping discipline named — done at §9.

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Per AC.D-sa.7, every plan-doc that selects non-default methods records the decision + rationale. This cycle's method-level decisions:

| Decision | Choice | Rationale |
|---|---|---|
| SKILL frontmatter shape | `description`-only (no `name` field) | Mirrors v0.1.8 Cycle 5 first-pass + the 8 sealed loam-skills SKILLs. Anthropic's schema treats the directory name as the skill identifier (verified at `plugins/loam-skills/skills/*/SKILL.md` + `plugins/dev-sdlc/skills/*/SKILL.md`). Lens 4 high-confidence → adopt verified pattern. |
| SKILL body section ordering | `What captures / When to use / How persona applies it / Graceful degradation / Composition / Out of scope` | Verified-working pattern across 8+6 sealed SKILLs. Lens 4 high-confidence → no deviation. |
| Test file granularity | One test file per AC (7 new test files) | Mirrors dev-sdlc plugin's existing convention (e.g., `test_AC_SKILLS_DSDLC1_*`). Per-AC granularity makes test failures map cleanly to ACs. |
| AC.SKILLS-DSDLC2.7 walk constant | `EXPECTED_SKILLS = [<6 first-pass> + <6 second-pass>] = 12 entries` | Mirrors first-pass `test_AC_SKILLS_DSDLC1_7_all_six_skills_discovered.py` shape. The cross-check asserts no orphan directories with SKILL.md beyond the 12. |
| Universal admissions | `docs/rebuild/plans/` only | No `odd-methodology.md` edit needed (this cycle ships SKILLs + an allowlist trim, not methodology); STATE.md / eric-final / roadmap rollup happens post-release-level-smoke per §9. Minimum fence per ODD discipline. |
| `_common/`-style helper for SKILLs? | NO | Each SKILL is self-contained; no cross-skill helper code. The first-pass set the precedent; second pass mirrors. |
| Dispatch model tier | Sonnet (default) | Master plan §4 Cycle 3 brief: "(none — Sonnet default)" — this plan-doc inherits. No model-rationale line required per swarming-discipline. |
| Decomposition into 6 sub-dispatches? | NO | Per Lens 5 stopping criterion: 6 SKILLs share shape; sub-dispatching adds coordination overhead without tightening any subtask's AC. Single-component-build serialization per `feedback_serialize_amendment_builds` also forbids parallel builds without worktree isolation. |
| Audit-allowlist edit shape | 4-line removal from set literal; one-liner per removed pair | Smallest possible diff. The remaining `memory-system/launchd/README.md → true-first-run/research.md` entry stays (still-valid pending-debt per pre-flight + master plan §7.8). |
| Audit-allowlist comment update | Yes — refresh the comment block above `KNOWN_CROSS_MODE_DEBT` to reflect post-Cycle-3 state (4 prior entries graduated; only memory-system remains; close note references Cycle 3 seal SHA at backfill time) | Without comment refresh, the comment still reads as if 5 entries are pending; future readers would confuse the state. Comment refresh is part of the same edit. |
| Skip release-level smoke? | NO — SOFT gate per Decision R | Master plan §5: SOFT gate at v0.1.9 but quality-bar-non-negotiable applies. All 6 dimensions exercised; backfill SHIPPED only after smoke green. |

---

### Commit SHAs

(Reserved — backfill on apply + seal.)

- Plan-doc commit: `<TBD>` — `docs(plans): v0.1.9 Cycle 3 sub-plan + manifest — 6 dev-sdlc SKILLs second pass + audit-allowlist cleanup`
- Source-edit commit (BASELINE): `<TBD>` — `feat(dev-sdlc): 6 dev-sdlc SKILL packages second pass + audit-allowlist cleanup (v0.1.9 Cycle 3)`
- Amendment commit: `<TBD>` — `chore(amend): v0-1-9-cycle-3-skills-and-cleanup manifest+apply — dev-sdlc BASELINE+sidecar bump to <BASELINE>`
- Seal commit: `<TBD>` — `chore(seals): v0-1-9-cycle-3-skills-and-cleanup — dev-sdlc at <BASELINE>`
- §14 backfill commit: `<TBD>` — `docs(plans): record v0-1-9-cycle-3-skills-and-cleanup commit SHAs in method-decision register`
