# readme-ac3-synonym-list-widening — per-work-item plan-doc

**Status:** ratified 2026-05-24 per dispatcher recommendation-ruling
(builder's halt-and-surface from prior README cycle ratified as
Option 1 / "doc-only test-widening corrective"). Authored 2026-05-24
by `loam-builder` subagent.
**Working directory:** `/Users/lukeivers/loam/` (canonical loam tree).
**Parent plan:** `docs/plans/sealed/readme-restructure-decision-doc-positioning.md`
(predecessor cycle; §14 D-build.README.2 names this corrective).
**Predecessor seal:** `a39d5ce` (workspace-bootstrap at `cf5b0c1`).
**Companion empirical evidence:**
`.scratch/claude-output/readme-restructure-ac3-smoke-2026-05-24.md` —
4 live `claude -p` runs against the sealed README; 4/4 returned
semantically-correct shape; wrapper PASS-rate 1/4 (25%) due to
synonym-list narrowness.

**Quality bar:** doc-only-corrective cycle (test wrapper widening,
no production-code edit, no README edit). Single AC, ~10-15 min
AI-time per the duration rubric.

---

## §1 — Principles applied this turn

- **CHANNEL** — inline to dispatcher (plan-doc on disk; brief report).
- **F2 RUTHLESS FEEDBACK** — §10 carries the honest doubt about whether
  synonym widening reaches the actual root cause.
- **ODD §2.5** — the single AC ladders to the predecessor's AC.README.3
  outcome target; the edit maps 1:1 to the AC.
- **LOOSE-AC-TEXT → FIX THE AC, NOT THE IMPLEMENTATION**
  (`feedback_loose_AC_text_fix_AC_not_implementation`) — load-bearing.
  Implementation (README) is correct + intent-matching; test wrapper's
  literal-keyword list is the loose codification.
- **PROMPT SCOPE ↔ CONFIDENCE (F4)** — high confidence (the 4 captured
  outputs are Tier-0 empirical evidence; the synonym widening is
  exactly the keywords the model produced). Tight scope, tight ACs.
- **LOCKED-DESIGN-NOT-LICENSE** — predecessor's wrapper is revisitable;
  builder's halt-and-surface is the trigger.
- **INFORMATION-TRUST-ORDERING** — Tier-0 (the 4 captured `claude -p`
  outputs in the smoke writeup) outranks Tier-2 (synonym lists picked
  at wrapper-authoring time without empirical phrasing data).
- **OUTPUT-TO-DISK** — plan-doc to disk; inline summary in report.
- **NO sub-agents.**

---

## §2 — Summary / TL;DR

**What ships:** widened synonym lists in
`framework/workspace-bootstrap/tests/test_AC_README_3_outcome_altitude_first_touch_comprehension.py`.

**One change (one cycle, one AC, scope = single test file only):**

Widen the `harness_synonyms` and `persona_synonyms` tuples in the AC
test wrapper to cover the variants `claude -p` empirically produces:

- `harness_synonyms`: add `"layer"` (sub for harness; appeared in
  runs 1, 2, 3, 4 — all 4 runs used "layer" or both "layer" + a
  harness-class word).
- `persona_synonyms`: add `"translates"`, `"translating"`,
  `"translation"` (descriptive sub for persona-as-translator function;
  appeared in 4/4 runs as the operational description of the persona's
  role even when the literal word "persona" was used).

**What does NOT change:**

- The README content (already semantically correct; 4/4 runs extracted
  the intended shape).
- The AC.README.3 prompt template (still asks the same two questions).
- The `claude` synonym list (every run named "claude" literally).
- The Q2 verdict logic (YES/NO/UNCLEAR check unchanged; the runs that
  reached Q2 returned coherent verdicts).
- The outcome-altitude tag (still `outcome-altitude: true`).

**Named decisions baked into this plan:**

| ID | Decision | Rationale |
|---|---|---|
| **D-CORRECTIVE.SYNONYMS** | Widen synonym lists to add "layer" + translation-verbs. | Empirically the exact terms `claude -p` produced in 4/4 captured runs; per `feedback_loose_AC_text_fix_AC_not_implementation` the test wrapper's literal-keyword list is the loose codification while the README is correct. |
| **D-CORRECTIVE.VERIFICATION** | Replay the 4 captured outputs as inline fixtures rather than re-running live `claude -p`. | Tier-0 evidence is already captured in the smoke writeup; re-running burns ~30s + cost per run with no additional information value. The 4 captured outputs are deterministic test fixtures the widened wrapper must accept. The live `claude -p` test remains env-gated behind `LOAM_AC_README_3_LIVE=1` and is unchanged in behaviour for live invocation. |
| **D-CORRECTIVE.FIXTURE-SHAPE** | Fixtures live as parametrized inline test data in a new sibling test function in the same test file. | Avoids creating a new fixtures/ subdirectory or a separate test file for a single-purpose verification. Keeps the corrective small + locally readable. The new function runs in the seal-time pytest pass (not env-gated) since it doesn't invoke `claude -p`. |

**F2 Ruthless Feedback on scope realism:** the change is genuinely
small (3-4 lines edited + 1 new test function ~30 lines). The
confidence is high — the captured outputs literally show the exact
keywords. The honest doubt (§10) is whether literal-keyword-with-wider-
synonyms is the right wrapper SHAPE at all, vs an LLM-as-judge
(Option 2 from the smoke writeup). The dispatcher ruled Option 1
explicitly; this plan-doc executes Option 1.

---

## §3 — Placement decisions

| Item | Placement | Rationale |
|---|---|---|
| Test wrapper edit | `framework/workspace-bootstrap/tests/test_AC_README_3_outcome_altitude_first_touch_comprehension.py` | Single file in scope. The component anchor; no fence admission needed. |
| Plan-doc | `docs/plans/readme-ac3-synonym-list-widening.md` | Per pos-v2 convention (sealed-target relocation to `docs/plans/sealed/` on seal). |
| Manifest | `docs/plans/readme-ac3-synonym-list-widening.manifest.yaml` | Same pattern as predecessor. |

**Fence:** single-component anchor on `framework/workspace-bootstrap/`.
The edited test file lives inside the anchor directly; no
`extra_allowed_prefixes` needed.

---

## §4 — Halt-and-surface BEFORE build

### Surface #1 (decision recorded autonomously — synonym list contents)

**Decision:** harness synonyms widen to
`("harness", "framework", "scaffold", "substrate", "layer")`; persona
synonyms widen to `("persona", "agent", "assistant", "translates",
"translating", "translation")`. Claude synonyms unchanged
(`("claude",)` — all 4 runs named it literally).

### Surface #2 (decision recorded autonomously — fixture-shape)

**Decision:** 4 captured outputs replayed inline as `pytest.parametrize`
test data on a new function
`test_widened_synonym_check_accepts_observed_claude_p_phrasings`.
Lives in the same test file as the existing
`test_first_touch_comprehension_smoke_via_claude_p`. NOT gated behind
`LOAM_AC_README_3_LIVE=1` — runs every pytest pass because no
`claude -p` invocation needed.

### Surface #3 (HALT if triggered — widened wrapper still fails on captured outputs)

**Halt:** if the widened synonym lists STILL fail any of the 4 captured
outputs (i.e., the widening doesn't address the empirical narrowness),
halt + surface. Would mean either: (a) the synonym lists need further
widening (which becomes a never-ending chase — escalate to Option 2
LLM-as-judge); or (b) the captured outputs themselves carry phrasing
I haven't accounted for. Either way, dispatcher rules.

### Surface #4 (HALT if triggered — README content has regressed)

**Halt:** if a freshly-invoked `claude -p` run (env-gated, optional
verification at builder's call) returns content that fails BOTH the
original AND the widened synonym lists, halt + surface. Would mean the
README has regressed since the prior sealing, OR the model behaviour
has drifted, OR the prompt template is no longer extracting the shape.
This is a defensive halt; the captured outputs are the primary
evidence for AC pass.

---

## §5 — Spec-objective placement

**Binds to:**

- **AC.PO.1** (prime objective primary-persona test) — same as
  predecessor cycle. The README's first-touch comprehension is the
  AC.PO.1 surface; widening the wrapper restores the wrapper's
  fidelity to the operational outcome.
- **AC.README.3** (predecessor cycle; sealed) — the outcome-target.
  This corrective doesn't change the AC's intent; it tightens the
  wrapper to actually pass when the intent is met.

**Ladders to:** `AC.README3.SYN → AC.README.3 (predecessor) → AC.PO.1`.

---

## §6 — Acceptance criteria

### `AC.README3.SYN.*` family — README AC.3 synonym list widening

- **AC.README3.SYN.1 — Widened synonym lists accept all 4 captured
  outputs.** A new test function in the AC.README.3 test wrapper file
  parametrizes the 4 captured `claude -p` outputs (Q1 phrasings from
  the 2026-05-24 smoke runs) and runs the wrapper's
  `_names_any(q1, harness_synonyms) AND _names_any(q1, claude_synonyms)
  AND _names_any(q1, persona_synonyms)` check against each. All 4 pass.

  *Method-in-AC test:* the AC fixes the OUTCOME (the widened wrapper
  must accept the 4 empirical outputs) without naming HOW to widen the
  synonyms specifically. Alternative widening shapes that pass all 4
  satisfy the AC. PASSED.

  *Outcome-altitude tag:* outcome-altitude is inherited from the
  predecessor's AC.README.3 — this corrective doesn't shift the
  outcome-altitude designation. The fixture-based test is a STUB-class
  verification that the wrapper recognizes empirically-observed
  phrasings; the actual outcome-altitude smoke (live `claude -p`)
  remains the env-gated test and is unchanged.

### `AC.README3.SYN.S` — fence (single-cycle, single-file)

- Cycle fence: single test file
  (`framework/workspace-bootstrap/tests/test_AC_README_3_outcome_altitude_first_touch_comprehension.py`).
  Plus `docs/plans/<this-slug>.md` + `docs/plans/<this-slug>.manifest.yaml`
  (universal admission for the plan-doc + manifest).

---

## §7 — Build steps (method-level guidance; builder's call per ODD §1.1)

### Single cycle (doc-only test wrapper widening)

1. **Plan-doc + manifest authored** (this file + sibling manifest).
2. **Source edit:** widen `harness_synonyms` tuple + `persona_synonyms`
   tuple in the AC.README.3 test file per Surface #1.
3. **New test function authored:**
   `test_widened_synonym_check_accepts_observed_claude_p_phrasings` —
   parametrized over the 4 captured Q1 outputs from the smoke writeup;
   runs the same `_names_any` check the live test runs (factored as a
   helper if needed); asserts pass for all 4.
4. **Touched test run:** `pytest framework/workspace-bootstrap/tests/test_AC_README_3_outcome_altitude_first_touch_comprehension.py`
   — the new test function runs (the existing live-only test is skipped
   per its env-gate). New test passes.
5. **`loam amend validate`** — schema-lint passes.
6. **`loam amend apply`** — auto-commit lands.
7. **`loam amend seal`** — deterministic seal commit.
8. **Backfill:** STATE.md gets a brief line; predecessor plan-doc
   §14 gets a "see corrective" pointer (NO — actually the corrective
   plan-doc references the predecessor, not vice versa; the predecessor
   is sealed and shouldn't be re-edited).

---

## §8 — Out of scope (deferred)

- **README.md edits** — explicitly NOT changed. The README's content
  is empirically correct.
- **LLM-as-judge wrapper redesign** (Option 2 from the smoke writeup)
  — dispatcher ruled Option 1; deferred unless Surface #3 fires.
- **Re-running live `claude -p` smoke** — optional at builder's call
  per Surface #4; the 4 captured outputs are sufficient evidence.
- **Refactoring the wrapper to share helper code** with the
  parametrized test — not required; the `_names_any` helper is already
  factored. If duplication arises, builder may extract a module-level
  helper; otherwise leave as-is.
- **AC ID rename** — `AC.README3.SYN.*` is scope-descriptive per
  `feedback_scope_descriptive_ac_ids`; no rename needed.

---

## §9 — Halt triggers (in-flight)

- **WD drifts** from `/Users/lukeivers/loam/` → halt + surface.
- **Widened wrapper still fails any of the 4 captured outputs** →
  halt + surface (Surface #3).
- **Fence breach** (edit outside the single test file) → halt + surface.
- **Seal-test fails** for reasons unrelated to this corrective →
  halt + surface (pre-existing fence breach surfaced by the seal).

---

## §10 — F2 Ruthless Feedback (honest doubts)

1. **Synonym widening is a literal-keyword arms race.** Adding "layer"
   + translation-verbs addresses the 4 captured outputs, but the next
   `claude -p` invocation may produce yet a third phrasing variant
   ("middleware"? "bridge"? "shim"?). The fundamental fragility is the
   literal-keyword wrapper SHAPE, not the specific keyword set.
   Option 2 (LLM-as-judge) would address the SHAPE; this corrective
   addresses the immediate symptom. Surfacing so dispatcher knows
   future smoke failures may need Option 2 escalation.

2. **The 4 captured outputs are a small sample.** 4 runs is enough to
   show the wrapper is too narrow (we've observed the failure), but
   not enough to guarantee the widened wrapper will be wide enough
   for the next 4 runs. Per `feedback_n1_architectural_vs_n3_statistical`
   this is the architectural-question shape (does intervention X work?)
   not the statistical-confidence shape; n=4 is sufficient for the
   architectural question "is the wrapper too narrow?". For confidence
   in the widened wrapper, a future ~10 live runs would be informative
   (deferred — out of scope for this 10-15 min corrective).

3. **The fixture-based test is a STUB-class verification.** It tests
   that the wrapper recognizes empirically-observed phrasings; it does
   NOT re-test the README's first-touch comprehension (the
   outcome-altitude AC). The live `claude -p` smoke remains the actual
   outcome-altitude test and is unchanged. The fixture-based test is
   bookkeeping for the wrapper's behaviour, not the outcome.

---

## §11 — Bookkeeping

On seal:

- `loam amend apply` then `loam amend seal` (no `git commit --amend`
  per `feedback_no_amend_in_agent_dispatches`).
- Semantic commit message: "test(workspace-bootstrap): widen
  AC.README.3 wrapper synonym lists to accept observed claude -p
  phrasings (corrective)" or builder's choice.
- Backfill STATE.md with the seal SHA.
- Plan-doc relocates from `docs/plans/` to `docs/plans/sealed/` on
  seal per pos-v2 convention.

---

## §12 — Provenance trail

| Claim | Source |
|---|---|
| Predecessor cycle seal (`a39d5ce` on `cf5b0c1`) | `git log` HEAD-1 + `docs/plans/sealed/readme-restructure-decision-doc-positioning.manifest.yaml` |
| D-build.README.2 names this corrective | `docs/plans/sealed/readme-restructure-decision-doc-positioning.md` §14 |
| 4 captured `claude -p` Q1 outputs + wrapper PASS-rate 1/4 | `.scratch/claude-output/readme-restructure-ac3-smoke-2026-05-24.md` Runs 1-4 |
| Dispatcher ruled Option 1 (synonym widening) | Dispatch brief 2026-05-24 (this turn) |
| Loose-AC-text → fix AC, not implementation | `feedback_loose_AC_text_fix_AC_not_implementation` |
| Scope-descriptive AC IDs | `feedback_scope_descriptive_ac_ids` |
| No --amend in agent dispatches | `feedback_no_amend_in_agent_dispatches` |
| n=1 architectural vs n=3 statistical | `feedback_n1_architectural_vs_n3_statistical` |

---

## §14 — Method decisions (populated at build time)

### Commit SHAs

- Source-edit batch: `3bfe5974e671ddf563209a0535795ed2f10636f5` —
  `test(workspace-bootstrap): widen AC.README.3 wrapper synonym lists to accept observed claude -p phrasings (AC.README3.SYN.1)`.
  Contains the test-file widening + new parametrized test +
  `_check_q1_concepts` helper extraction, plus the corrective plan-doc.
- Apply commit: `d5c87cd` —
  `chore(amend): readme-ac3-synonym-list-widening manifest+apply — workspace-bootstrap BASELINE+sidecar bump to 9146ea4`.
  Manifest+sidecar bookkeeping. NOTE: per D-build.README.4 in the
  predecessor plan-doc, the canonical pattern is source-edit-batch-FIRST
  then apply; this corrective inverted the order (apply landed first,
  source-edit batch second) and got the same outcome (the seal collapses
  both into the deterministic seal commit). The inversion is functionally
  equivalent but the manifest's BASELINE field points to the predecessor's
  STATE-backfill commit (`9146ea4`), one commit older than the
  source-edit batch (`3bfe597`). No functional regression; future
  doc-only cycles should source-edit-batch-first to match canonical
  pattern (same D-build.README.4 note as predecessor).
- Seal commit: `0a76e1269223fca6c171802ab37aea9a59c3f476` —
  `chore(seals): readme-ac3-synonym-list-widening — workspace-bootstrap at 3bfe597`.
  Deterministic seal collapsed the predecessor's still-pending
  bookkeeping commits (`a39d5ce`, `ea86916`, `9146ea4`) + this
  corrective's apply (`d5c87cd`) + source-edit batch (`3bfe597`) into
  one clean seal commit on top of `64c8f24`. Diff window: `9146ea4 ..
  3bfe597`. Cross-component sweep 16/17 GREEN (1 skipped — scope-of-work
  has no recognised seal-diff test).

### Build-time decision deviations

- **D-build.SYN.1 — Run 3 not included as fixture.** The 4-run smoke
  writeup (Runs 1, 2, 3, 4) quoted verbatim Q1 outputs for Runs 1, 2,
  and 4 only. Run 3 was the only PASS in the original wrapper, and its
  Q1 was summarized as "cleanly contained both harness + persona
  synonyms" without verbatim quote. Including Run 3 would have required
  fabricating a Q1 text (Tier-3 self-output dressed as Tier-0 empirical
  data — forbidden by `feedback_claim_or_cite_no_fake_sources`).
  Parametrizing over Runs 1, 2, 4 — the empirically-failing pre-widening
  outputs — IS the load-bearing test: if the widened wrapper passes all
  3 failing pre-widening outputs, the AC is met. Run 3 already passes
  the pre-widening wrapper so it isn't load-bearing for this corrective.
- **D-build.SYN.2 — Apply-then-source-edit ordering (inversion of
  canonical).** Per D-build.README.4 from predecessor (same pattern):
  apply commit landed first, source-edit batch second. Functionally
  equivalent; seal collapses both. Same future-correction note as
  predecessor.
- **D-build.SYN.3 — `--allow-untracked-globs` for unrelated in-flight
  plan-docs.** Same pattern as predecessor's D-build.README.3: working
  tree carried three unrelated untracked plan-docs at seal time
  (everything-claude-code-absorption-master-plan,
  token-defaults-optin-skill, promote-multi-channel-extractor-and-
  iteration-loop-family). Sealed with
  `--allow-untracked-globs "docs/plans/drafts/*" --allow-untracked-globs "docs/plans/promote-*"`.
  Patterns did NOT stage or commit the unrelated paths. No fence
  contamination.

---

*Plan-doc authored 2026-05-24 by `loam-builder` subagent under the
canonical loam tree. SEALED LOCAL 2026-05-24 at seal `0a76e12`.*
