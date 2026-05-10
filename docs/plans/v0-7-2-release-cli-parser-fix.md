# v0.7.2 PATCH — release-CLI `acs-verified` gate parser-scoping fix (defect-closure)

**Status:** plan-only at authoring time. Plan-before-code per `feedback_plan_before_code`. Owner pre-ratified scope via Telegram 10672.
**Slug:** `v0-7-2-release-cli-parser-fix`.
**Date authored:** 2026-05-10.
**Class:** **PATCH** per `docs/release-versioning-policy.md`. No new outcome capability — closes a defect in v0.6.0's shipped release-CLI gate (specifically the `acs-verified` gate parser scoping). The defect was discovered + worked around at v0.7.1 publish-time (cross-references rewritten as prose to satisfy the over-greedy parser); v0.7.2 fixes the parser AND restores the AC-ID precision lost to the workaround.
**Predecessor:** v0.7.1 (sealed `cdae8ed`, awaiting publish — `feedback_build_forward_on_publish_pending` permits dispatching the next cycle while v0.7.1 publish queue catches up).
**Working directory:** `/Users/lukeivers/loam/`.
**Owner authorization:** dispatched 2026-05-10; covers plan-doc authoring + build + seal. Publish remains owner-asked per ASK-FIRST.

---

## §1 — Outcome shape (the "why")

The `acs-verified` gate in `framework/tools/loam/src/loam_cli/release/gates.py` (lines 136-217) currently scans the WHOLE plan-doc body for any `AC.<scope>.<n>` token + asserts each is GREEN-marked in the §status section. The scan is too greedy: cross-reference AC IDs in §6 (out-of-scope explanations) and §8 (predecessor dependencies) are treated as in-scope ACs requiring §status-verdicts.

v0.7.1 publish hit this twice:
- **AC.NTU.6** referenced in §6 as out-of-scope follow-on from v0.7.0 → parser flagged it as missing-from-§status.
- **AC.V060.7** referenced in §8 as v0.6.0's dogfood AC the v0.7.1 publish itself uses → parser flagged it as missing-from-§status.

Worked around at v0.7.1 by rewriting the cross-references as prose ("v0.7.0's deeper F-DESIGN finding" / "v0.6.0's dogfood AC"). The rewrites satisfy the parser but lose AC-ID precision in the cross-references. Captured at publish-time in `docs/FUTURE_IDEAS_DRAFT.md` line 232 as a v0.8.0+ candidate; activation gate names "next instance of cross-reference-AC-ID parser-RED (whichever is sooner)" — that activation gate fires at v0.7.2 because the workaround pollutes the next version's plan-doc authoring loop too.

**Aggregate effect:** plan-doc authors can use AC-ID precision in cross-references (§6 / §8 / anywhere outside §4) without the parser flagging them as missing-from-§status. The v0.7.1 plan-doc's prose rewrites get reverted to AC-ID form. The release-CLI gate becomes correct (matches the documented intent — "verify the in-scope ACs are GREEN"; in-scope is defined by §4 per the plan-doc convention).

**Why patch (not minor).** Per `docs/release-versioning-policy.md`, MINORs add outcome capability; PATCHes close defects within an already-shipped outcome. The release-CLI's `acs-verified` gate already exists (shipped at v0.6.0); v0.7.2 fixes how it scopes its scan. No new gate, no new CLI verb, no new user-facing capability.

## §2 — Prime objective ladder

```
VALUE_PROPOSITION.md prime objective
   └─ "primary persona is a translation layer between the user's
       natural-language intent and AI-effective execution"
        └─ documented features work as advertised (v1.0 quality-bar
            criterion #1 — closed at v0.7.1 across docs/install/CLI;
            extends to release-CLI gates being correct, not just
            present)
             └─ release-CLI `acs-verified` gate scopes its AC-ID
                 scan to §4 (the documented in-scope AC location)
                  └─ AC.READYP.1 (parser scope-restriction)
                  └─ AC.READYP.2 (restore AC-ID precision in v0.7.1
                      plan-doc)
                  └─ AC.READYP.3 (test fixture for fixed parser)
                  └─ AC.READYP.4 (outcome-altitude probe — run
                      `loam release v0.7.2 --dry-run` against
                      v0.7.2's own plan-doc)
```

The two VALUE_PROPOSITION tests:
- **Primary-persona test** — every AC reduces translation burden by removing a defect that would force the plan-doc author to translate around (rewriting cross-references as prose to dodge a parser-scoping bug; figuring out why a perfectly-valid §6/§8 cross-reference triggers a `acs-verified` RED).
- **Harness test** — every AC sharpens an existing primitive (the `acs-verified` gate parser becomes scope-correct; the `READYP` test fixture extends the test corpus).

## §3 — Component fence

**Single-component PATCH.** Touched component: `framework/tools/loam/` (the release-CLI parser + its test corpus).

**PRIMARY:** `framework/tools/loam/`
- `framework/tools/loam/src/loam_cli/release/gates.py` — `check_acs_verified` parser scope-restriction (AC.READYP.1).
- `framework/tools/loam/tests/test_AC_V060_2_pre_publish_gates.py` — extended test pair for the section-scoped scan (AC.READYP.3) plus updates to the existing tests' `staged_repo` fixture if needed to preserve their semantics.
- `framework/tools/loam/tests/conftest.py` — fixture extension if the existing `staged_repo` shape needs a §6 / §8 section to drive the new tests; otherwise untouched.

**Universal-admission docs:**
- `docs/plans/v0-7-1-v1-0-readiness-cleanup.md` — revert the prose rewrites at lines 169 + 190 to AC-ID form (AC.READYP.2). Note: this edit lands on the predecessor's plan-doc — the plan-doc is post-seal but still mutable for accuracy fixes per the historical doc-edit pattern (e.g., v0.7.0 §status backfill landed post-seal at `c7b3717`).
- `docs/plans/v0-7-2-release-cli-parser-fix.md` (this file).
- `docs/plans/v0-7-2-release-cli-parser-fix.manifest.yaml`.
- `docs/STATE.md` — v0.7.2 SHIPPED LOCAL row added at end-of-build.
- `docs/release-roadmap.md` — v0.7.2 §2-shipped row added with seal SHA at end-of-build.
- `docs/experiments/v0-7-2-hard-smoke.md` — HARD smoke writeup for the v0.7.2 publish gate.
- `docs/FUTURE_IDEAS_DRAFT.md` — mark the line-232 capture as RESOLVED at v0.7.2.

**Untouched:** all other components. No new components; no new files outside the universal-admission set above.

## §4 — Acceptance criteria

Five ACs. AC IDs use the scope-descriptive `READYP` family per `feedback_scope_descriptive_ac_ids` ("READYP" = "v1.0-readiness parser"; sibling family to v0.7.1's `READY`).

### AC.READYP.1 — Parser scope-restriction to §4 — Acceptance criteria

**What:** The `acs-verified` gate's AC-ID scan is restricted to the plan-doc's `## §4 — Acceptance criteria` section body (between that heading and the next `## §<n>` heading boundary). AC IDs appearing in any other section (§1 prime-objective ladder, §6 out-of-scope, §8 dependencies, §11 authority chain, §13 §status, etc.) are NOT treated as in-scope ACs requiring §status verdicts.

**Acceptance:**
- The `check_acs_verified` function in `framework/tools/loam/src/loam_cli/release/gates.py` parses the plan-doc body for the §4 heading first, extracts the slice between that heading and the next `## §<n>` boundary, then runs the existing AC-ID regex against that slice ONLY.
- The existing §status-scan logic (looking for AC IDs near GREEN markers within 240 chars) is unchanged — that scan still runs against the §status section body.
- The §status section itself can contain cross-reference AC IDs to other versions' ACs (e.g., v0.7.0's AC.NTU.S in v0.7.1's §status acknowledging predecessor dependency); those are not flagged because they're not in §4.
- Heading recognition is permissive: matches `## §4 — Acceptance criteria` (em-dash) AND `## §4 - Acceptance criteria` (hyphen) AND `## §4 Acceptance criteria` (no separator) — the existing plan-doc corpus uses all three shapes (see v0.6.0 conftest fixture using `## §4 Acceptance criteria` vs v0.7.1 using `## §4 — Acceptance criteria`).
- If the §4 heading is absent (older plan-doc shape), the gate returns RED with a corrective hint naming the missing section. (No fall-back to whole-doc scan — that would silently re-introduce the defect.)

### AC.READYP.2 — Restore AC-ID precision in v0.7.1 plan-doc

**What:** Revert the prose rewrites that v0.7.1 used to dodge the parser. Two edits in `docs/plans/v0-7-1-v1-0-readiness-cleanup.md`:
- Line 169 (§6 out-of-scope): `**v0.7.0's deeper F-DESIGN finding** (Q4/Q5 dev-intent conditional surfacing)` → `**AC.NTU.6 deeper F-DESIGN finding** (Q4/Q5 dev-intent conditional surfacing)`.
- Line 190 (§8 dependencies): `the publish ritual for v0.7.1 will use the same `loam release` CLI (per v0.6.0's dogfood AC; second use of the verb post-v0.7.0)` → `the publish ritual for v0.7.1 will use the same `loam release` CLI (per AC.V060.7 dogfood; second use of the verb post-v0.7.0)`.

**Acceptance:**
- Both edits land in the v0.7.1 plan-doc body.
- After the AC.READYP.1 fix lands, running `loam release v0.7.1 --dry-run` (a dry-run probe — does NOT publish) returns GREEN on the `acs-verified` gate. (The v0.7.1 plan-doc's §4 declares 10 ACs (`AC.READY.{1-9,S}`); §status backfills all 10 GREEN. Cross-references in §6 + §8 to AC.NTU.6 + AC.V060.7 are now ignored by the scoped parser.)
- Verification probe: `git diff` on v0.7.1 plan-doc shows the two cross-reference fixes only; no other v0.7.1 plan-doc lines change.

### AC.READYP.3 — Test fixture covers section-scoped scan (positive + negative)

**What:** Test pair for the fixed parser added to `framework/tools/loam/tests/test_AC_V060_2_pre_publish_gates.py`:
- **Positive test** — fixture plan-doc has §4 with 2 in-scope ACs (e.g., `AC.READYP.X.1` + `AC.READYP.X.2`) AND cross-reference AC IDs in §6 (`AC.OTHER.1`) AND §8 (`AC.OTHER.2`); §status marks the 2 in-scope ACs GREEN; gate returns GREEN.
- **Negative test** — same fixture but §status omits one of the §4-declared ACs; gate returns RED with the missing-AC name in the message.

The existing test pair (`test_acs_verified_green_when_status_marks_each_ac_green` + `test_acs_verified_red_when_status_omits_an_ac`) continues to pass — the existing `staged_repo` fixture's plan-doc body uses `## §4 Acceptance criteria` heading with two `AC.V060.<n>` ACs, all marked GREEN in `## §13 §status`. The fix is backwards-compatible with the existing fixture shape.

**Acceptance:**
- New test functions land at `test_AC_V060_2_pre_publish_gates.py` (e.g., `test_acs_verified_ignores_cross_references_in_other_sections` + `test_acs_verified_red_when_section_4_ac_missing_from_status`).
- New tests assert: positive returns ok=True; negative returns ok=False AND message names the specific missing AC.
- The whole `test_AC_V060_2_*` test module passes (`pytest framework/tools/loam/tests/test_AC_V060_2_pre_publish_gates.py -v` → all GREEN).

`outcome-altitude: false` — implementation-altitude AC (test against function signature; not a real-execution probe).

### AC.READYP.4 — Outcome-altitude probe (`loam release v0.7.2 --dry-run` against this plan-doc)

**What:** Real-execution probe against the production CLI binary. After AC.READYP.1 lands and the v0.7.2 plan-doc itself is in place, run `loam release v0.7.2 --dry-run` from the repo root. The `acs-verified` gate must report GREEN naming the 5 in-scope ACs (`AC.READYP.{1-4,S}`); it must NOT name any cross-reference AC IDs from §6 / §8 / §11 / §13 in the report.

**Acceptance:**
- `loam release v0.7.2 --dry-run` runs to completion without crashing.
- The `acs-verified` gate line in the report says GREEN.
- The gate's message specifies `5 AC(s) marked GREEN` (matches the §4 declared count: AC.READYP.1, AC.READYP.2, AC.READYP.3, AC.READYP.4, AC.READYP.S).
- Probe is documented in `docs/experiments/v0-7-2-hard-smoke.md` with the literal CLI invocation + the gate report excerpt + the GREEN verdict line.

`outcome-altitude: true` per `feedback_test_outcome_altitude_required` — invokes production entry-point (the actual `/opt/homebrew/bin/loam release` binary built from this build) against realistic input (this very plan-doc). Risk band: **production-facing release-CLI** — this gate determines whether v1.0 ship-readiness assertions hold; HARD per-cycle REQUIRED.

### AC.READYP.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under:

- `framework/tools/loam/src/loam_cli/release/gates.py` (AC.READYP.1)
- `framework/tools/loam/tests/test_AC_V060_2_pre_publish_gates.py` (AC.READYP.3)
- `framework/tools/loam/tests/conftest.py` — only if AC.READYP.3 needs a fixture extension; otherwise untouched
- `docs/plans/v0-7-1-v1-0-readiness-cleanup.md` (AC.READYP.2 — universal-admission)
- `docs/plans/v0-7-2-release-cli-parser-fix.md` (this file — universal-admission)
- `docs/plans/v0-7-2-release-cli-parser-fix.manifest.yaml` (universal-admission)
- `docs/STATE.md` (universal-admission; v0.7.2 SHIPPED LOCAL rollup)
- `docs/release-roadmap.md` (universal-admission; v0.7.2 §2-shipped row)
- `docs/experiments/v0-7-2-hard-smoke.md` (universal-admission; AC.READYP.4 writeup)
- `docs/FUTURE_IDEAS_DRAFT.md` (universal-admission; mark line-232 capture RESOLVED at v0.7.2)
- Component sidecar + narrative file (managed by `loam amend apply` / `loam amend seal`)

Sidecar advances per sealed-component-cycle ritual via `loam amend apply` then `loam amend seal`.

## §5 — Decisions builder rules at build time

- **D-READYP.1.a (heading-recognition tolerance):** match `## §4 — Acceptance criteria` (em-dash) AND `## §4 - Acceptance criteria` (hyphen) AND `## §4 Acceptance criteria` (no separator). Builder rules the exact regex shape — recommended `re.compile(r"^##\s*§4\b.*Acceptance\s+criteria", re.MULTILINE | re.IGNORECASE)`. Switch only if a prior plan-doc in the corpus uses a shape this regex misses (verify by `grep -rn "^## §4" docs/plans/`).
- **D-READYP.1.b (no fall-back):** if §4 heading absent, return RED with corrective hint (do NOT silently fall back to whole-doc scan — that re-introduces the defect). Hint text: "plan-doc at <path> has no `## §4 — Acceptance criteria` heading; the `acs-verified` gate scopes the AC-ID scan to §4 per the plan-doc convention. Add the heading + author the in-scope ACs there; re-run." The dispatch brief's plan-time confidence: this hint is correct because every plan-doc in the corpus uses §4 for ACs.
- **D-READYP.3 (fixture choice):** if the existing `staged_repo` fixture's plan-doc body needs to grow §6 + §8 sections to drive the cross-reference-ignored test, builder extends `conftest.py` minimally. Default = author the new test's fixture inline (within the test function) so the existing `staged_repo` shape stays untouched and existing tests' semantics are preserved. Switch to conftest extension only if inline-fixture verbosity exceeds ~30 lines (output-to-disk threshold for fixture body).
- **D-READYP.2 (revert mechanism):** straight string-replacement on the v0.7.1 plan-doc lines named in AC.READYP.2; verify by `git diff docs/plans/v0-7-1-v1-0-readiness-cleanup.md` showing exactly two changed lines (the two cross-references).
- **D-READYP.4 (probe location):** the `loam release v0.7.2 --dry-run` invocation lands in `docs/experiments/v0-7-2-hard-smoke.md` §1 (the canonical HARD smoke writeup location). Captures: invocation command, exit code, full gate-report stdout, GREEN verdict line.

## §6 — Out of scope (explicit)

- **Other parser brittleness in the release-CLI** (e.g., §13 §status heading literal-form requirement, hard-coded version-slug regex shape, seal-SHA extraction proximity rules) — captured at `docs/FUTURE_IDEAS_DRAFT.md` as a "release-CLI parser brittleness" family. The cross-reference-scoping defect is the second instance; v0.7.2 closes the second instance only. Other instances stay capture-only until they fire RED.
- **Public-surface manifest structural enforcement** (the v0.8.0+ candidate captured at FUTURE_IDEAS_DRAFT line 230) — separate work.
- **AC.NTU.6 deeper F-DESIGN finding** — that's still a follow-on amendment from v0.7.0; v0.7.2 only restores its AC-ID in the v0.7.1 cross-reference, does NOT close the F-DESIGN itself.
- **AC.V060.7 dogfood second-use** — v0.7.1's publish ritual uses the verb (per AC.V060.7); v0.7.2 only restores the AC-ID in the v0.7.1 cross-reference.
- **CLI extension to add a new gate** — every new gate is MINOR-class; out of patch scope.
- **Plan-doc convention changes** — the §4 heading IS the convention being enforced; v0.7.2 makes the parser match the convention, not vice versa.
- **Anthropic API key paths** (per architectural constraint, never).
- **Multi-LLM via OpenRouter** (per architectural constraint, backlog only).

## §7 — HARD HALTs (build-time)

Halt-and-surface to dispatcher (return owner-call) — do NOT proceed past — on any of:

1. AC.READYP.4 outcome-altitude probe RED. The fixed parser fails the dogfood probe against this plan-doc. Halt; surface as F-DESIGN candidate (parser fix doesn't actually close the defect).
2. ODD §2.5 violation in your work OR surrounding code (per `feedback_subagent_odd_violation_halt`).
3. Wrong-tree-write (any edit lands at a path outside `/Users/lukeivers/loam/`).
4. Any reach for ASK-FIRST class actions: `cd` outside `/Users/lukeivers/loam/`, `git push`, `git tag`, `git commit --amend` (per `feedback_no_amend_in_agent_dispatches`). Immediate halt.
5. Wall-clock exceeds upper band (90 min midpoint ~60 min) by >2× → 180 min wall-clock (~3 hr; matches dispatch brief's surface threshold). Halt with current state.
6. Discovery that the parser fix breaks an existing test or other gate behavior (e.g., `acs-verified` GREEN test starts returning RED; or `seal-reachable` parser starts misbehaving because the `re.search` calls share state somehow). Halt; surface; do NOT extend scope to fix downstream — that's MINOR-class.
7. Discovery that the §4 heading shape varies more than the three forms named in D-READYP.1.a across the existing plan-doc corpus. Halt; surface variant; let dispatcher rule on heading-tolerance scope.
8. Discovery that AC.READYP.2's cross-reference revert breaks anything (e.g., another script consumes the v0.7.1 plan-doc and parses on the prose form). Halt; surface; defer revert to dispatcher decision.
9. Any reach for an Anthropic API key path (per `feedback_no_anthropic_api_key`). Immediate halt.

## §8 — Dependencies

- **v0.7.1** — SOFT on commit-graph (sealed `cdae8ed`, awaiting publish). Per `feedback_build_forward_on_publish_pending`, v0.7.2 builds forward without waiting for v0.7.1 publish; v0.7.1 ships first when the dispatcher publishes, then v0.7.2.
- **v0.6.0 (concrete release process)** — HARD. v0.7.2 fixes a parser inside the v0.6.0-shipped gate substrate; v0.7.2 cannot land without v0.6.0's `check_acs_verified` function existing.
- **`docs/release-versioning-policy.md`** — SOFT. PATCH-class declaration grounded in the policy.
- **`feedback_scope_descriptive_ac_ids`** — SOFT. Drives the `READYP` AC ID family choice over `V072.*`.
- **`feedback_build_forward_on_publish_pending`** — SOFT. Justifies dispatching v0.7.2 while v0.7.1 awaits publish.
- **No external service dependencies.**
- **No new Python packages** (subscription-only constraint).

## §9 — Estimated AI-time

Per `feedback_duration_estimation_rubric` — single-component PATCH; tight per-AC scope; one parser function + one test pair + one plan-doc revert + one outcome-altitude probe. Defect-closure (no design exploration); confidence in outcome shape is high (Lens 4 — tight scope appropriate).

| Stage | Band | Midpoint |
|---|---|---|
| Plan-doc + manifest authoring (this file) | 10-20 min | 15 min |
| AC.READYP.1 — parser scope-restriction | 10-15 min | 12 min |
| AC.READYP.3 — test pair (positive + negative) | 10-15 min | 12 min |
| AC.READYP.2 — v0.7.1 plan-doc revert | 2-5 min | 3 min |
| AC.READYP.4 — outcome-altitude probe + writeup | 10-15 min | 12 min |
| FUTURE_IDEAS_DRAFT capture-resolved mark | 2-3 min | 2 min |
| Plan-doc §13 backfill + STATE/roadmap admin + manifest apply + seal | 15-25 min | 20 min |
| **Total v0.7.2 build** | **59-98 min (~1-1.6 hr)** | **~76 min (~1.3 hr)** |

The dispatch brief estimates 30-90 min midpoint ~60 min. Plan-time revision: **59-98 min midpoint ~76 min**. Defensible: the dispatch midpoint sits inside the plan band; minor lean upward reflects v0.7.1 actuals showing apply+seal stages take ~18 min combined, plus the cross-reference revert checking gets a few minutes for verification. If the v0.7.1 plan-doc revert is genuinely 2-line-only and probe runs clean first try, the lower band (~60 min) is reachable.

Owner gate-review separate (publish per ASK-FIRST after seal).

## §11 — Authority chain

- `docs/FUTURE_IDEAS_DRAFT.md` line 232 — the v0.7.1 publish-time finding capture; v0.7.2 closes it (mark RESOLVED).
- `docs/plans/v0-7-1-v1-0-readiness-cleanup.md` — the predecessor whose prose-rewrite workaround AC.READYP.2 reverts.
- `docs/release-versioning-policy.md` — PATCH-class declaration ground.
- `framework/tools/loam/src/loam_cli/release/gates.py` lines 136-217 — the function v0.7.2 modifies.
- `framework/tools/loam/tests/test_AC_V060_2_pre_publish_gates.py` lines 72-110 — the existing test pair v0.7.2 extends.
- Memory rules: `feedback_scope_descriptive_ac_ids.md` (AC.READYP.* not AC.V072.*), `feedback_plan_before_code.md` (this plan-doc IS the gate), `feedback_no_amend_in_agent_dispatches.md` (HARD HALT #4), `feedback_no_anthropic_api_key.md` (HARD HALT #9), `feedback_subagent_odd_violation_halt.md` (HARD HALT #2), `feedback_duration_estimation_rubric.md` (§9), `feedback_build_forward_on_publish_pending.md` (§8 build-forward justification), `feedback_test_outcome_altitude_required.md` (AC.READYP.4 risk-band).

## §13 — §status

Backfilled at end-of-build per the §status convention. AC verdict matrix + commit SHAs + AI-time actuals + halt-and-surface findings recorded here post-seal.
