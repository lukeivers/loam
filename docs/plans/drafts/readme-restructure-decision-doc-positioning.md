# readme-restructure-decision-doc-positioning — per-work-item plan-doc

**Status:** per-work-item plan-doc, plan-before-code, **RATIFIED 2026-05-24** per maintainer recommendation-bundle implicit-yes (Telegrams 12310 + 12311). All 4 named decisions (D-README.LEAD / .AUDIENCE-SEGMENTS / .SECTION-ORDER / .LENGTH-DELTA) ratified per plan-author recommendation. Build dispatch awaits separate owner go-ahead. Authored 2026-05-24 by `loam-plan-author` subagent.
**Working directory:** `/Users/lukeivers/loam/` (canonical loam tree).
**Parent plan:** `docs/plans/drafts/everything-claude-code-absorption-master-plan.md` (Wave 1 entry P4 — "README-as-decision-doc framing", lines 134–145).
**Parent ratification:** Telegram 12301 maintainer ruling "B" (Wave 1 bundle approved — security-hooks-bundle + strategic-compact SKILL + token-defaults SKILL + this README work).
**Predecessor plan-doc shape exemplar:** `docs/plans/v0-1-6-production-safety-and-base-skills.md` (multi-cycle sub-plan-doc — header, summary, placement, halt-and-surface, spec-objective placement, ACs with families, build steps, OOS, halt triggers, bookkeeping).
**Companion research (load-bearing):**
- ECC README structural analysis (WebFetch 2026-05-24 against `https://raw.githubusercontent.com/affaan-m/everything-claude-code/main/README.md` — opens with positioning ("harness-native operator system for agentic work"), philosophy → guides → changelog → Quick Start ~25% down, no explicit "is this for you?" section, hybrid manifesto/manual/reference voice).
- `docs/VALUE_PROPOSITION.md` (load-bearing for what the positioning claim should be — two tests + 12-hour example + the translation-burden frame).
- Current `README.md` (canonical loam; `## Why` at line 19; positioning summary in lines 3–17; install at line 32; design lenses at line 102 — already partially decision-doc-shaped, restructure is incremental).

**Quality bar:** doc-only cycle. No code. Single small amendment (one cycle, three ACs, scope-descriptive AC IDs `AC.README.*`). 15–25 min AI-time per the duration rubric (small-scope authoring + smoke).

---

## §1 — Principles applied this turn

- **CHANNEL** — output is a plan-doc on disk; inline report to dispatcher names path + summary + named decisions.
- **F2 RUTHLESS FEEDBACK** — §10 carries honest doubts; one design-risk named explicitly (positioning-summary length tension).
- **ODD §2.5** — every AC ladders to AC.PO (per `feedback_value_proposition_as_prime_objective`); every build step maps to a named AC; no non-objective edits.
- **PLAN-BEFORE-CODE** — load-bearing; no `README.md` touch in this plan; builder dispatch authors the change against this contract.
- **AGENT-PROMPTS-SCOPE-ONLY** — this plan-doc carries method (the section reordering + the "Is this for you?" subsection shape); the eventual builder dispatch carries scope-only.
- **SCOPE-DESCRIPTIVE AC IDs** — `AC.README.1/2/3` (per `feedback_scope_descriptive_ac_ids`, no version pre-baking).
- **CLAIM-OR-CITE** — every claim about ECC cites WebFetch result; every claim about loam cites `README.md` line range or `docs/` path.
- **PROMPT SCOPE ↔ CONFIDENCE (F4)** — high confidence in outcome shape (audience-routing + positioning hoist + "is this for you?" subsection); ACs tight; method-in-AC test passed below.
- **LOCKED-DESIGN-NOT-LICENSE** — current README shape is revisitable; the maintainer ratification of Wave 1 is the license for the change.
- **OUTPUT-TO-DISK** — plan-doc to disk per output-conventions; inline summary in dispatch report.
- **NO sub-agents.**

---

## §2 — Summary / TL;DR

**What ships:** a restructured `README.md` that audience-routes on first read.

**Three changes (one cycle, one amendment, scope = `README.md` only):**
1. **Hoist a tightened one-paragraph positioning summary into the lead position** (replaces the current 3-paragraph open at lines 3–17). The current open already names the harness shape; tightened version foregrounds it in one ~60-word paragraph + a one-line italicised pitch, then routes to detail rather than carrying detail inline.
2. **Insert a new "Is this for you?" subsection** between the lead positioning and `## Why`. Three reader-segments named in plain English (non-technical user looking for a Claude that remembers / Claude Code user wanting structural safety / contributor evaluating the methodology); each segment gets a one-sentence "you'll want loam if..." + a one-sentence "you probably won't want loam if...". Function = audience-routing as defined by the ECC README pattern, adapted to loam's actual reader-segments.
3. **Re-order the section sequence to Why → For whom → How → What ships → Lenses → Workflow → Status → Docs.** Today's sequence is Why → Quickstart (How) → What → Lenses → Workflow → Status → Docs. The two changes: hoist positioning before Why (subsumed into the new lead paragraph), and insert "For whom" after Why and before Quickstart so audience routing happens BEFORE install instructions (ECC's "why → how → what" rhetorical arc, adapted to loam).

**What does NOT change:**
- Quickstart command sequence — preserved verbatim. Existing two-copies-on-disk note (lines 65–78) preserved verbatim; the install pain is real and the note is honest.
- "What ships" table (lines 80–100) — preserved verbatim.
- "Design lenses" (lines 102–119), "Workflow chain" (lines 120–142), "Status" (lines 143–155), "Documentation" / "Contributing" / "Security" / "License" — preserved verbatim.

**Named decisions baked into this plan (with recommendations):**

| ID | Decision | Recommendation | Rationale |
|---|---|---|---|
| **D-README.LEAD** | Replace the 3-paragraph current open with one ~60-word positioning paragraph + the existing italicised one-line pitch. | **Recommended.** Reader-time-to-pitch drops from ~45 seconds (three paragraphs to absorb the harness-attached + persona-translation + cultivate-substrate framing) to ~10 seconds. The detail moves to `docs/positioning.md` (already linked at line 28). |
| **D-README.AUDIENCE-SEGMENTS** | Which reader-segments to route in "Is this for you?" | **Three segments: (1) non-technical user who wants a Claude that remembers / persists / governs itself; (2) Claude Code power-user who wants structural safety + cost governance + autonomous continuity layered on top; (3) contributor/researcher evaluating the methodology (ODD, principle-conflict resolution, swarming, etc.).** Rationale: (1) maps directly to VALUE_PROPOSITION's primary translation-burden frame; (2) maps to the harness-extends-toolkit frame; (3) maps to the maintainer's actual current contributor pipeline (per README line 152 "review-circle expansion is the project's biggest non-technical need"). Each gets a YES-signal sentence + a NO-signal sentence (the NO-signal half is honest: "you probably won't want loam if you want a thin agent that doesn't scaffold a workspace" — that's the locked design choice articulated at `docs/design/why-loam-scaffolds.md`). |
| **D-README.SECTION-ORDER** | Where does "For whom" insert in the sequence? | **After Why, before Quickstart.** Routing must happen BEFORE install instructions — installing-and-then-bouncing is exactly the failure mode the section prevents. Putting it after Quickstart defeats the purpose; putting it before Why fragments the why-paragraph. |
| **D-README.LENGTH-DELTA** | Net README length change tolerated? | **Net-neutral to net-shorter.** The new lead is shorter (-2 paragraphs); the new "For whom" subsection adds ~120 words (6 sentences × 3 segments + one section header + one transition line). Net delta: roughly -0 to -40 words. Hard ceiling: README MUST NOT exceed current length by more than 5%. |

**F2 Ruthless Feedback on scope realism:** the scope-confidence is high (this is a 30-line markdown edit; no code; no contracts; no test plumbing). The honest doubt is in §10 — the audience-segments choice is genuinely subjective and the maintainer might want a different cut. The plan-doc names the three I'd pick + asks for ratification of THAT cut specifically (one question, at the right altitude — per `feedback_one_question_at_a_time`).

---

## §3 — Placement decisions

| Item | Placement | Rationale |
|---|---|---|
| `README.md` edits | `/Users/lukeivers/loam/README.md` (repo root) | Single file in scope. Cannot live anywhere else. |
| Builder plan-doc (eventual) | `docs/plans/<scope-slug>.builder-plan.md` per existing convention (e.g. `amendment-N-readme-decision-doc-positioning.builder-plan.md`) | Builder dispatch authors against this plan-doc; new builder plan-doc spawned at build time per pos-v2 amendment convention. |
| Manifest (eventual) | `docs/plans/<scope-slug>.manifest.yaml` | Single-file fence: `README.md` only. Plus `docs/plans/` for the manifest itself. |

**Fence (eventual cycle):** `README.md` + `docs/plans/<this-plan-slug>.builder-plan.md` + `docs/plans/<this-plan-slug>.manifest.yaml`. Single-component fence in spirit (no `framework/` or `plugins/` touched).

---

## §4 — Halt-and-surface BEFORE build

### Surface #1 (decision recorded autonomously — lead-paragraph word budget)

**Decision:** The new lead positioning paragraph targets **55–70 words** (currently the open at lines 3–17 runs ~150 words across 3 paragraphs + a 2-line italicised pitch). Hard ceiling: 80 words. Below the floor, the paragraph loses the harness-attached / persona-translation / substrate framing; above the ceiling, the audience-routing benefit erodes. The italicised one-line pitch (current lines 14–17) is **preserved verbatim** as the post-paragraph anchor.

### Surface #2 (decision recorded autonomously — "Is this for you?" subsection rendering)

**Decision:** rendered as `### Is this for you?` (H3) immediately under `## Why` (H2), NOT as its own H2. Rationale: it's an extension of the Why section's positioning function, not an independent top-level concern. Each of the three reader-segments gets a bold-led one-line YES-signal + a one-line NO-signal:

```
**Non-technical user looking for a Claude that remembers and handles itself.** You'll want loam if you want one trusted persona that holds state across sessions, books work to run on schedule, and refuses unsafe actions structurally. You probably won't want loam if you want a tool you launch on demand and forget between sessions.

**Claude Code power-user adding harness on top.** You'll want loam if you want persistent memory, cost ceilings, autonomous background work, and structural safety gates layered on the Claude Code session you already run. You probably won't want loam if your Claude Code workflow is already shaped around stateless one-off tasks.

**Contributor or researcher evaluating the methodology.** You'll want loam if Objective-Driven Design, principle-conflict resolution, and swarming-as-recursive-decomposition look like the right shape to study or extend. You probably won't want loam if you want a turn-key product with documented integration points and no opinions about how work is authored.
```

(Exact prose to be authored by the builder; the above is the shape contract, not the verbatim text.)

### Surface #3 (decision recorded autonomously — section order)

**Decision:** Final section order top-to-bottom:

1. `# loam` (H1 title)
2. Lead positioning paragraph (one para, ~55-70 words) + italicised one-line pitch
3. `## Why`
4. `### Is this for you?` (H3 under Why)
5. `## Quickstart`
6. `## What ships`
7. `## Design lenses`
8. `## Workflow chain`
9. `## Status`
10. `## Documentation`
11. `## Contributing`
12. `## Security`
13. `## License`

Items 5–13 preserve current order exactly (only items 1–4 change).

### Surface #4 (decision recorded autonomously — out-of-scope preservation)

**Decision:** The "two copies of loam source on disk" note (current lines 65–78) is preserved verbatim. It is honest, accurate, and acknowledges install pain that the marketplace-install absorption (P7 in master plan, Wave 2) will eventually resolve. Editing it would mask reality before the resolution ships — `feedback_workaround_masks_rootcause_urgency` applies in reverse (don't sanitise the note out before the root-cause fix ships).

### Surface #5 (HALT if triggered — net length grows >5%)

**Halt:** if the proposed edit grows the README net length by more than 5% of current line count (current `wc -l README.md` = 185 lines verified 2026-05-24; ceiling = 194 lines), halt the build and surface. The audience-routing benefit collapses if the README itself grows the install-friction it's meant to reduce.

---

## §5 — Spec-objective placement

**Binds to:**

- **AC.PO.1 + AC.PO.2** (prime objective per `docs/VALUE_PROPOSITION.md`, per `feedback_value_proposition_as_prime_objective`).
  - **Primary-persona test:** reduces translation burden — the README is the user's FIRST contact with loam (before the persona is running). A reader who bounces on a manual-shaped README never reaches the persona; the audience-routing change reduces "install + don't understand" bounce, which IS translation burden absorbed at the front door.
  - **Harness test:** the README is not a persona tool, so the harness-test doesn't fire directly. The change is primary-persona-test-only — accepted under the high-bar rule for harness-test failure cases ("a feature that fails the primary-persona test may still be right occasionally — some work genuinely requires the user to make the execution choice"; reversed here — the change passes primary-persona; harness-test N/A for documentation).
- **Master plan §3.1 P4** (lines 134–145 of `everything-claude-code-absorption-master-plan.md`) — pattern absorbed: audience-routing decision-doc README framing from ECC, adapted to loam's actual reader-segments.

**Ladders to:** `AC.README.* → Wave 1 absorption bundle → master absorption plan → AC.PO.1/AC.PO.2`.

---

## §6 — Acceptance criteria

### `AC.README.*` family — README decision-doc restructure

- **AC.README.1 — Lead positioning paragraph + italicised pitch present, within word budget.** The README's content between the H1 title (`# loam`) and the first H2 (`## Why`) is a single paragraph between 55 and 80 words inclusive, followed by an italicised blockquote one-line pitch. Test: parse `README.md` markdown; locate the H1-to-first-H2 region; word-count the non-italicised paragraph; assert in `[55, 80]`; locate exactly one blockquote in the region; assert it contains exactly one italicised line.

  *Method-in-AC test:* the AC fixes the OUTCOME (word-budget paragraph + a pitch quote) without naming HOW to phrase either. A different phrasing of the same shape satisfies the AC. PASSED.

- **AC.README.2 — "Is this for you?" subsection present under Why, with three labelled reader-segments each carrying YES and NO signals.** The README contains an H3 `### Is this for you?` heading positioned immediately after the `## Why` section's lead content and before the `## Quickstart` H2. The subsection body contains exactly three bold-led reader-segment blocks. Each block contains the strings "You'll want loam if" AND "You probably won't want loam if" (case-insensitive). Test: markdown-parse the README; locate the H3 by literal heading text; assert it falls between `## Why` and `## Quickstart`; assert three bold-paragraph blocks; assert both signal-phrases per block.

  *Method-in-AC test:* the AC fixes WHAT each segment-block must contain (a YES signal and a NO signal in named phrasing) and WHERE the subsection sits (between Why and Quickstart). It does NOT fix which three segments to name, which exact prose to write, or how to phrase the segments. Alternative segment cuts and prose satisfy the AC. PASSED.

- **AC.README.3 — `outcome-altitude: true` — non-developer first-touch comprehension smoke.** A reader unfamiliar with loam can identify, from the first 25 lines of `README.md` alone (no scrolling, no clicking links), (a) what loam is in one sentence and (b) whether they are a target user. Smoke procedure: a fresh `claude -p` session is given ONLY the first 25 lines of `README.md` as input plus the prompt "In one sentence each: (1) what does this tool do? (2) is this for someone who has never used Claude Code? Answer YES/NO/UNCLEAR plus a reason." Assert that the response to (1) names "harness", "Claude", and "persona" or close synonyms; assert that the response to (2) is YES or NO with a coherent reason (UNCLEAR is a fail). Records to a status-file path captured at build time.

  *Method-in-AC test:* outcome-altitude per `feedback_test_outcome_altitude_required`. The AC invokes the production entry-point (the README itself) with no pre-arranged state (a fresh `claude -p` session). It does NOT prescribe the README's phrasing — it tests whether a fresh reader extracts the shape regardless of phrasing. PASSED.

  *Outcome-altitude tag:* `outcome-altitude: true`. (Per `feedback_test_outcome_altitude_required` — every AC set carries ≥1 outcome-altitude AC; this one. The first two are STUB-class structural-shape tests that don't satisfy the outcome-altitude requirement on their own.)

### `AC.README.S` — fence (single-cycle, single-file)

- Cycle fence: `README.md` only. Plus `docs/plans/<this-slug>.builder-plan.md` + `docs/plans/<this-slug>.manifest.yaml` (universal admission for the plan-doc + manifest themselves).

---

## §7 — Build steps (method-level guidance; builder's call per ODD §1.1)

### Single cycle (doc-only)

1. **Plan-doc lands** (this file at `docs/plans/drafts/readme-restructure-decision-doc-positioning.md`).
2. **Maintainer ratification** of the named decisions in §2 (D-README.LEAD, D-README.AUDIENCE-SEGMENTS, D-README.SECTION-ORDER, D-README.LENGTH-DELTA). On ratification, the plan-doc status flips to ratified and the file relocates from `drafts/` to `docs/plans/` (per pos-v2 convention).
3. **Builder dispatch** with this plan-doc as the contract. Dispatch carries scope-only (per `feedback_agent_prompts_scope_only`): "author the README edits per AC.README.{1,2,3} against the section-order in Surface #3 and the word-budget in Surface #1. Halt-and-surface any AC you cannot satisfy outcome-shape."
4. **Manifest authored** by builder: `docs/plans/<this-slug>.manifest.yaml` — single-file fence: `README.md`.
5. **Source edits** (builder; in order):
   - Replace `README.md` lines 3–17 (current open + italicised pitch) with the new ~60-word lead paragraph + preserved italicised pitch line (Surface #1).
   - Insert `### Is this for you?` H3 subsection immediately after the existing `## Why` paragraph (current ends at line 30, before the `## Quickstart` H2 at line 32), per Surface #2.
   - No other edits to `README.md`. No edits to any other file in the fence.
6. **Tests authored** (builder; new file `tests/test_AC_README_{1,2,3}_*.py` or co-located with similar README/docs tests if a precedent exists — builder's call). Note: this is the canonical loam tree which currently has no `tests/` at the root level for README; the AC.README.1 + AC.README.2 tests may need a new directory or to live as a small script under `scripts/` invoked via Make or CI. Builder surfaces the test-placement decision if unclear.
7. **Touched tests run** (only the three new tests + any existing doc-lint tests if present).
8. **`loam amend apply`** (per `feedback_dispatch_explicit_loam_amend_apply`) — single auto-commit.
9. **`loam amend seal`** — deterministic seal commit.
10. **AC.README.3 smoke** — execute the outcome-altitude smoke described in AC.README.3; record to status-file at `<workspace>/.scratch/claude-output/readme-restructure-ac3-smoke-<date>.md`.

---

## §8 — Out of scope (deferred)

- **Edits to `docs/positioning.md`, `docs/architecture.md`, `docs/getting-started.md`** — none in scope. The lead paragraph references `docs/positioning.md` for detail; no change to the linked doc.
- **Removing the two-copies-on-disk note** (current README lines 65–78) — preserved verbatim per Surface #4. Deferred to whenever marketplace-install (master plan P7, Wave 2) ships.
- **Adding a marketplace-install Quick Start path** — deferred to Wave 2 (P7 / D-MARKETPLACE in master plan).
- **Adding a "Token Optimization" subsection** — that absorption is P3 in master plan (also Wave 1, separate plan-doc — the token-defaults SKILL with a docs section in `docs/getting-started.md`, not in README).
- **Restructuring the "What ships" component table** (current lines 80–100) — preserved verbatim. A separate cycle could absorb component-table improvements; not in this fence.
- **Adding a changelog section** — ECC's README has one; loam's lives at `docs/release-roadmap.md` and shouldn't duplicate. Deferred indefinitely.
- **AGENTS.md or cross-tool support documentation** — explicitly rejected at master-plan level (P23) per maintainer ruling TG 12242. Not deferred — closed.
- **Updating the README to use shields.io badges or a hero image** — out of scope; aesthetic-only, no audience-routing impact.

---

## §9 — Halt triggers (in-flight)

- **WD drifts** from `/Users/lukeivers/loam/` → halt + surface.
- **Net README length grows >5%** (current 185 lines; ceiling 194) → halt + surface (Surface #5).
- **The lead paragraph cannot land in the 55–80 word budget while preserving the harness/persona/substrate framing** → halt + surface (the word budget may need maintainer revision; do NOT silently overshoot).
- **A reader-segment cannot be authored with a clean YES + NO signal without compromising one of the three D-README.AUDIENCE-SEGMENTS cuts** → halt + surface (the segment cut may need revision; do NOT silently merge segments).
- **AC.README.3 smoke returns UNCLEAR on either question** → halt + surface (the lead 25 lines aren't doing the audience-routing work the change is supposed to do; needs rework before seal).
- **Any test fails on the sealed state** → halt + RF the conflict (per `feedback_subagent_odd_violation_halt`).

---

## §10 — F2 Ruthless Feedback (honest doubts)

1. **The three reader-segments are a subjective cut.** I'm naming non-tech-user / Claude Code power-user / contributor-researcher because those map directly to the VALUE_PROPOSITION translation-burden frame, the L1 Claude-leverage frame, and the maintainer's stated current pipeline need (line 152: "review-circle expansion is the project's biggest non-technical need"). A different cut is defensible — e.g., "ADHD/exec-function user / autonomous-work needer / pure-tool user" or "indie hacker / enterprise / researcher". The maintainer should rule on the cut as D-README.AUDIENCE-SEGMENTS specifically. If the maintainer wants a different cut, swap the §4 Surface #2 prose and re-ratify; nothing else in the plan changes.

2. **The word-budget for the lead is tight.** 55–80 words is enough to name harness + Claude-attached + persona-translation, but not enough to also name the substrate-cultivation metaphor, the always-on hooks, the autonomous-continuity claim, or the structural-safety claim. The lead paragraph WILL lose some of what the current 3-paragraph open carries. The trade is reader-time-to-pitch vs detail; the master plan ratified this as a Wave 1 quick win, so I'm trusting the prior decision. If the paragraph genuinely can't carry the load, the halt-trigger in §9 fires and the maintainer rules.

3. **The "you probably won't want loam if..." sentences risk reading as defensive.** The shape is honest (calling out the locked-design scaffold choice from `docs/design/why-loam-scaffolds.md`; calling out the existing-Claude-Code-workflow-already-shaped audience; calling out the no-turnkey-product reality). But the prose has to land NOT as apology, NOT as gate-keeping, but as service-to-the-reader ("if you're looking for X, loam is the wrong shape; here's what you might want instead"). The AC doesn't pin this — it's a craft-of-prose risk the builder absorbs. Surfacing it here so the builder is aware before drafting.

4. **AC.README.3 (outcome-altitude smoke) uses `claude -p` as the comprehension probe.** That's a Tier-1 source of "did a fresh reader extract the shape", but it's not a human reader. A non-tech-user-fresh-reader is the ACTUAL outcome target; the LLM probe is a proxy. The proxy is cheap, repeatable, and gates the seal — it's the right shape for the size of the change. A real-user comprehension test (e.g., asking three Telegram-channel non-tech contacts to read the lead 25 lines and answer the two questions) would be Tier-0 evidence; out of scope for a 15-25 min cycle. Capturing in §13 as future-work consideration if the LLM probe turns out to be a poor proxy.

5. **The change does not address the actual highest-leverage README friction — the install instructions themselves.** The Quickstart is preserved verbatim per scope. The four-step install + two-copies-on-disk pain is the real bounce point for non-tech users; this restructure routes them BEFORE they hit it but doesn't FIX it. The fix is master-plan P7 (marketplace install, Wave 2). Surfacing here so the maintainer knows this restructure is necessary-not-sufficient, and the actual install-friction fix is queued separately.

---

## §11 — Bookkeeping

On seal:

- `loam amend apply` on the cycle (NOT `git commit --amend`; create NEW corrective commits if a file is missed — per `feedback_no_amend_in_agent_dispatches`).
- Single semantic commit message: "docs(README): restructure for audience-routing decision-doc framing (P4 Wave 1)" or builder's choice (commit-message convention is builder's call per ODD §1.1 once it satisfies the project's commit-message style).
- Backfill `docs/plans/drafts/everything-claude-code-absorption-master-plan.md` Wave 1 status with the apply + seal SHAs for P4.
- Status file recorded at `<workspace>/.scratch/claude-output/readme-restructure-ac3-smoke-<date>.md` (the AC.README.3 smoke).
- Move this plan-doc from `docs/plans/drafts/` to `docs/plans/` on maintainer ratification (pre-build); update the status header from "DRAFT" to "ratified — building" then "sealed" post-seal.

---

## §12 — Provenance trail

| Claim | Source |
|---|---|
| Master-plan P4 entry (README-as-decision-doc framing) | `docs/plans/drafts/everything-claude-code-absorption-master-plan.md` lines 134–145 |
| Maintainer ratification of Wave 1 bundle including this work | Telegram message 12301 ("B") |
| Current README lead at lines 3–17 (3 paragraphs + italicised pitch) | `README.md` lines 3–17 |
| Current `## Why` at line 19 | `README.md` line 19 |
| Current Quickstart at line 32 | `README.md` line 32 |
| Current two-copies-on-disk note at lines 65–78 | `README.md` lines 65–78 |
| Current "What ships" table at lines 80–100 | `README.md` lines 80–100 |
| Current "Design lenses" at lines 102–119 | `README.md` lines 102–119 |
| README total length (185 lines) | `wc -l README.md` at HEAD 2026-05-24 |
| ECC README opens with positioning ("harness-native operator system for agentic work"), philosophy → guides → changelog → Quick Start ~25% down | WebFetch 2026-05-24 against `https://raw.githubusercontent.com/affaan-m/everything-claude-code/main/README.md` |
| ECC README has no explicit "is this for you?" section | Same WebFetch — confirmed "No explicit 'is this for you?' section exists" |
| ECC README rhetorical arc is "why → how → what" rather than "what → how → why" | Same WebFetch — confirmed "moves from why → how → what rather than the traditional what → how → why" |
| VALUE_PROPOSITION's two tests are the prime objective | `docs/VALUE_PROPOSITION.md` lines 56–74 + `feedback_value_proposition_as_prime_objective` |
| Audience-routing is a translation-burden reducer (primary-persona test passes for documentation) | `docs/VALUE_PROPOSITION.md` lines 17–32 (translation-layer definition) |
| Why-loam-scaffolds is a locked-design choice articulated separately | `docs/design/why-loam-scaffolds.md` (referenced from README line 30) |
| Maintainer's stated current pipeline need is review-circle expansion | `README.md` line 152 |
| Plan-doc shape exemplar (header / summary / placement / halt-and-surface / spec-objective / ACs / build steps / OOS / halt triggers / bookkeeping) | `docs/plans/v0-1-6-production-safety-and-base-skills.md` (full file) |
| Maintainer ruled out AGENTS.md / cross-tool support | Telegram 12242 (per master-plan P23 record) |
| Outcome-altitude AC requirement | `feedback_test_outcome_altitude_required` |
| Scope-descriptive AC ID convention | `feedback_scope_descriptive_ac_ids` |
| Loose AC text fix → fix AC, not implementation | `feedback_loose_AC_text_fix_AC_not_implementation` (applies if AC.README.* prove loose post-build) |

---

*Plan-doc authored 2026-05-24 by `loam-plan-author` subagent under the canonical loam tree. Awaiting maintainer ratification of the four named decisions in §2 before builder dispatch.*
