---
description: Detect and prevent the failure mode where ACs pass at implementation-altitude but the user-facing outcome breaks on real-world inputs. Apply at AC-authoring time (every AC set includes ≥1 outcome-altitude AC), at test-authoring time (does this test pre-arrange state the production code would produce — STUB-class), and at test-review time (risk-band classifier governs whether HARD per-cycle is required vs deferral to release-gate). Composes on `docs/odd-llm-grounding.lean.md` "Outcome-altitude AC requirement" section + ODD §2.5 (every line maps to an AC). Use whenever authoring ACs, authoring tests for ACs, reviewing tests, or evaluating cycle-seal readiness for production-facing surface.
---

# odd-test-altitude-discipline

ODD §2.5 enforces traceability across altitudes — every line of code, branch, and test maps to a named AC. It does NOT enforce that each AC SET includes a probe at outcome-altitude. Three failures observed in v0.2.1 (F1, F2) and v0.2.5 (F1) shipped with all cycle ACs green; the real-world failures surfaced only at the release-level HARD smoke gate, requiring corrective amendments.

This skill is the procedural prevention. It carries:

1. The pre-arrangement detection rubric (when is a test STUB-class?).
2. The risk-band classifier (when does HARD per-cycle apply, vs release-gate deferral?).
3. Concrete examples of pre-arrangement bypass (the v0.2.5 SOFT smoke is the canonical anti-example).
4. The four trigger-points where this skill loads.

## Pre-arrangement detection rubric

When reviewing a test, ask:

> **"Does this test write state that the production code under test would normally produce?"**

If yes → the test is **STUB-class**. STUB tests can satisfy implementation-altitude ACs but **NEVER outcome-altitude ACs**.

The rule applies regardless of how the pre-arrangement is staged:

- Direct YAML / JSON / file write into the extraction-dir before the CLI is invoked.
- Fixture factory that pre-populates a database table the production code would have written.
- `tmp_path` setup that constructs a directory tree the production walk would have built.
- Stub-client that returns canned responses standing in for the LLM call the production path would make.
- Mock that injects values where the production code would have computed them from inputs.

A test is **OUTCOME-class** when:

1. It invokes the production entry-point the user invokes (CLI command + flags / API endpoint / dispatch surface) — not a private helper.
2. Inputs to the entry-point are realistic-shape (real fixture / canonical sample) — not pre-computed downstream artefacts.
3. The test asserts on the artefacts the production code produces (files written, exit code, stdout, response payload, side-effects) — not on whether internal helpers were called.

Pre-arrangement detection sub-rule for AC-authoring: when authoring an AC, ask "what would the user observe if this AC was satisfied?" The verification surface for the AC must produce that exact observation, end-to-end, without pre-arrangement.

## Risk-band classifier — the L3-conditional rule

Owner ruling 2026-05-05 (Telegram 10188): HARD per-cycle is **NOT blanket**. It conditions on risk band — production-facing surface gets HARD per-cycle; pure-internal refactor with no observable change can rely on release-gate HARD.

**HARD per-cycle REQUIRED** when the cycle touches any of:

- A CLI command or CLI flag the user invokes.
- A plugin surface (SKILL, persona, hook contract) the user composes with.
- A user-visible artefact (file written into the workspace, output rendered to terminal, error message displayed).
- A config schema the user authors against (manifest fields, bootstrap.yaml fields, plugin config).
- A persistence schema that crosses session boundaries (stored YAML / DB row the next session reads).

**Release-gate HARD acceptable** when the cycle touches only:

- Internal data structures with no observable shape change at the user-facing surface.
- Pure-function refactors where inputs and outputs are unchanged.
- Test-only edits (fixture renames, helper extraction) with no production code impact.
- Documentation (this very fix is doc + SKILL only — release-gate HARD acceptable).

Risk-band assessment goes into the plan-doc §6 smoke section. If the answer is "HARD per-cycle required," the plan-doc enumerates the HARD probe (real fixture + production entry-point + outcome-artefact assertion) as a §6 D-dimension or as an explicit per-cycle release smoke. If the answer is "release-gate HARD acceptable," the plan-doc says so explicitly with a one-line rationale (so the reviewer doesn't have to re-derive).

**Worked example — HARD per-cycle required:** v0.2.4 Cycle 3 added the `--build-next` CLI flag (production-facing surface). HARD per-cycle would be: invoke `loam odd-extract build-next <fresh-workspace>` against a real fixture, assert the ranked-candidate list is produced. The cycle did not author such a probe; the SOFT release smoke pre-arranged the inputs (the v0.2.5 F1 failure mode).

**Worked example — release-gate HARD acceptable:** the present cycle (ODD test-altitude procedural fix) adds a doc section + a SKILL + a memory file + edits to existing SKILLs. No code changes. Production behavior is unaffected. Release-gate HARD (existing dev-sdlc test sweep) is sufficient.

## Concrete pre-arrangement bypass — anti-example

The v0.2.5 SOFT release-level smoke (`AC.PERSONA-PULL.4`) writes canned `objectives.yaml` + `backing-map.yaml` directly into the extraction-dir before invoking `--gaps` and `--build-next`. The CLI's actual synthesis path (where the LLM client wires through) is never exercised. All v0.2.3 + v0.2.4 cycle ACs passed; the production CLI ships empty `objectives.yaml` on real-world repos.

**Why it's STUB-class:** the synthesis stage is upstream of the gap-analysis stage; pre-writing the synthesis output bypasses the synthesis production path. The test invokes the CLI surface (looks like an integration test) but the upstream production code never runs.

**The corrective:** the v0.2.5 corrective C1+C2 (in flight) wires the synthesis client through the CLI and exercises end-to-end. The procedural fix here (this skill) prevents the same shape from being authored INTO future cycles.

The SOFT smoke fixture lives at the v0.2.4 cycle-3 sub-plan-doc; do not rewrite it here — the prevention is procedural going forward, not retroactive.

## When this skill loads

Four trigger-points pin this skill to load:

1. **AC-authoring time (`plan-docs-author` / `plan-before-code-author`).** When authoring §4 ACs in a sub-plan-doc or master plan, every AC set goes through the outcome-altitude requirement check. The plan-author SKILLs reference this skill by path.
2. **Dispatch-brief authoring time (`dispatch-brief-authoring`).** The seed AC family in the dispatch brief carries the outcome-altitude marker so the build agent knows the contract at plan-author time. The dispatch-brief SKILL references this skill in its AC-authoring guidance section.
3. **Test-authoring time (any new pytest / integration / smoke test).** When an agent or persona authors a test, run the pre-arrangement detection rubric on it. STUB-class tests are valid for implementation-altitude ACs; never for outcome-altitude ACs.
4. **Test-review / cycle-seal-readiness time (any test PR / pre-seal review).** Before a cycle seals, walk the AC family: each outcome-altitude AC has an OUTCOME-class verification test. STUB-class tests on outcome-altitude ACs are halt-and-surface findings.

## Composition

- **`docs/odd-llm-grounding.lean.md` "Outcome-altitude AC requirement"** — the canonical statement of the rule; this skill is its operationalisation.
- **`feedback_test_outcome_altitude_required.md`** (memory file) — the cross-session persistence layer; loads on every fresh session-start to keep the rule active.
- **`plan-docs-author` SKILL** — references this skill in its §4 AC-authoring guidance.
- **`plan-before-code-author` SKILL** — same shape; structural skeleton's §4 enforces the marker.
- **`dispatch-brief-authoring` SKILL** — references this skill in its seed AC family guidance.
- **`feedback_plan_before_code`** — the hard rule that plan-doc precedes code; this skill specifies what makes the plan-doc's §4 outcome-altitude-honest.
- **`feedback_loose_AC_text_fix_AC_not_implementation`** — composes when post-build review finds an AC at the wrong altitude. Doc-only corrective: tighten the AC text or add an outcome-altitude AC sibling, then verify nothing pending depends on the loose reading.
- **ODD §2.5** — strict mapping (every line maps to an AC). This skill closes the altitude gap §2.5 alone doesn't catch.

## Out of scope

- Re-doing past cycles' ACs. Sunk-cost; sealed; corrective amendments handle leakage as discovered.
- Authoring example HARD-per-cycle tests for any specific component. Per-cycle HARD probes get authored when the next production-facing cycle is dispatched.
- Layer 3 blanket per-cycle HARD smoke. Owner ruling 2026-05-05: HARD per-cycle conditions on risk band, not blanket. The classifier above is the operational form.
- The principle-conflict resolution four-step process (M5; lives in `feedback_principle_conflict_resolution_multi_signal`) — that skill is the meta-procedural; this skill is the specific-procedural.
