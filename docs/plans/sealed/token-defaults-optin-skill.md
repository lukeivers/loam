# Token-optimization defaults documenter + opt-in writer SKILL

**Status:** per-work-item plan-doc, plan-before-code, **RATIFIED 2026-05-24** per maintainer recommendation-bundle implicit-yes (Telegrams 12310 + 12311). All 4 named questions (Q1 docs-section-placement / Q2 settings-env-merge / Q3 preview-diff-approval / Q4 undo-out-of-scope) ratified per plan-author recommendation. Build dispatch awaits separate owner go-ahead. Authored 2026-05-24 by `loam-plan-author` subagent.
**Working directory:** `/Users/lukeivers/loam/` (canonical loam tree).
**Parent plan:** `docs/plans/drafts/everything-claude-code-absorption-master-plan.md` §5 (Wave-1 work-item WI-3) + §4 D-TOKEN.ENFORCE.
**Maintainer ruling already in place:** D-TOKEN.ENFORCE per Telegram 12301 — three-part: (a) document in `docs/getting-started.md`; (b) author opt-in SKILL the persona invokes on user cost-signal; (c) REJECT auto-mutation of `~/.claude/settings.json` on install.
**Predecessor seal:** none required — additive surface; composes with existing `docs/getting-started.md` + existing `plugins/loam-skills/skills/` plugin shape.
**Quality bar:** build-ready plan-doc. Maintainer ratifies; builder dispatches against this contract; no methodology re-derivation at build-time.

---

## Principles applied this turn

- **PLAN-BEFORE-CODE** — load-bearing; no source touched in this dispatch.
- **AGENT-PROMPTS-SCOPE-ONLY** — ACs are outcome-shape; method (which Python lib for YAML/JSON merge, which SKILL frontmatter exact text, which prose phrasing in docs section) is the builder's call.
- **ODD §2.5** — every section of the plan-doc binds to a named AC in §4; every AC ladders to AC.PO.1 + AC.PO.2 (VALUE_PROPOSITION primary-persona + harness tests).
- **SCOPE-DESCRIPTIVE AC IDs** — AC.TOKEN.1 .. AC.TOKEN.5 + AC.TOKEN.S (outcome-altitude). NOT version-packed.
- **F2 RUTHLESS FEEDBACK** — §10 names two honest doubts (the SKILL's invocation criteria are loose; the cost-savings percentages are ECC's claims not loam-measured).
- **CLAIM-OR-CITE** — every cost-savings number cites the ECC README WebFetch verification 2026-05-24; every loam-internal claim cites a file path.
- **F4 SCOPE ↔ CONFIDENCE** — AC outcome-shapes TIGHT (high confidence in outcome); implementation method LOOSE (builder's call); docs prose phrasing LOOSE (builder's call within constraint that the 4 recommended settings + rationales are present).
- **LENS-1 CLAUDE-LEVERAGE-FIRST** — composes against Claude Code's native `~/.claude/settings.json` hierarchy; uses the SKILL primitive (no custom invocation surface).
- **LENS-2 HARNESS + PRIMARY-PERSONA VALUE** — primary-persona test: SKILL absorbs the technical detail (user says "loam is expensive" → persona handles the optimization). Harness test: adds a SKILL to the toolkit the persona invokes on cost-signal.
- **NO sub-agents.** This dispatch is plan-authoring only.

---

## §1 — Objective

Make loam's recommended token-optimization defaults (Sonnet default, MAX_THINKING_TOKENS cap, earlier auto-compact, MCP/tool caps) accessible to users via two complementary surfaces:

1. **A documented preset** in `docs/getting-started.md` so users discovering loam via the docs surface see the recommended settings + their cost-rationale before they hit cost pain.
2. **An opt-in SKILL** at `plugins/loam-skills/skills/cost-optimised-defaults/SKILL.md` the persona invokes when it detects a user cost-signal ("loam is expensive", "tokens are burning", "let's cut costs", "what should my settings be") — the SKILL presents the recommended settings, awaits explicit user approval, and on approval merges them into `~/.claude/settings.json` non-destructively (existing keys preserved).

**Explicitly out of objective:** auto-mutating `~/.claude/settings.json` on install. Per D-TOKEN.ENFORCE: user-config sovereignty + non-tech-user-surprise rules out silent mutation; the SKILL is the surface that respects sovereignty (explicit approval) while still absorbing the translation burden (the persona handles the technical detail).

---

## §2 — Predecessors / context

- **D-TOKEN.ENFORCE ratification** (maintainer ruling, Telegram 12301) — three-part directive: document + opt-in SKILL + reject auto-mutation.
- **Parent absorption plan** at `docs/plans/drafts/everything-claude-code-absorption-master-plan.md` §3.1 P3 + §4 D-TOKEN.ENFORCE + §5 WI-3 — establishes the framing (loam absorbs ECC's settings recommendations, NOT ECC's auto-write mechanism).
- **ECC source** verified via WebFetch 2026-05-24 against `https://raw.githubusercontent.com/affaan-m/everything-claude-code/main/README.md`:
  - `model: sonnet` — claimed ~60% cost reduction; handles 80%+ of coding tasks.
  - `MAX_THINKING_TOKENS=10000` — claimed ~70% reduction in hidden thinking cost per request.
  - `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50` — "Compacts earlier — better quality in long sessions".
  - `ECC_CONTEXT_MONITOR_COST_WARNINGS=off` — ECC-specific; NOT absorbed (loam has no equivalent env var).
  - Discipline guidance: <10 MCPs per project; <80 active tools; `/clear` between unrelated tasks; `/compact` at logical task boundaries; `/cost` monitoring.
- **Loam memory rule** `feedback_compact_clear_decision_heuristic.md` — the token-cost-aware compact/clear/continue heuristic already in the corpus; composes with this work-item (the heuristic informs WHEN to use the discipline; this SKILL+docs surface installs the SETTINGS that make the heuristic effective).
- **Loam global instruction** (per `~/.claude/CLAUDE.md` Token efficiency section) — "Sonnet for routine tasks; Opus only for complex architectural decisions" is already established as discipline for the maintainer's own usage; this work-item generalises that discipline to a user-facing surface.

---

## §3 — Scope

### In-scope

1. New documentation section in `docs/getting-started.md` titled "Token-optimization defaults" (or scope-equivalent header) located AFTER the five-step bootstrap (§5 region) — the user is past install + onboarding before they hit cost concerns. Section lists the 4 absorbed recommended settings (Sonnet default, `MAX_THINKING_TOKENS=10000`, `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50`, `<10 MCPs / <80 tools` discipline) with one-sentence rationale per setting + a single-line "or run `/skill cost-optimised-defaults` to have loam apply them on approval" pointer to the SKILL.
2. New SKILL bundle at `plugins/loam-skills/skills/cost-optimised-defaults/SKILL.md` with:
   - frontmatter `description` carrying invocation criteria (user cost-signal patterns; explicit `/skill` invocation; persona-detected cost-pain context);
   - body documenting the four recommended settings, the SKILL's user-approval flow ("I will write these to your `~/.claude/settings.json`: ... — proceed?"), the non-destructive merge guarantee (existing keys preserved), and the toggle-back-off instructions (user can undo by removing the keys).
3. A settings-merge implementation (location at builder's call — likely a small Python helper colocated with the SKILL bundle or under `plugins/loam-skills/`; could also be invoked inline by the persona via Bash + Python one-liner) that:
   - reads existing `~/.claude/settings.json` (preserving content if file absent → start empty object);
   - merges the recommended keys WITHOUT overwriting any pre-existing user values for those keys (collision policy: surface conflicts to the user, accept user's choice per-key);
   - writes atomically (write-temp-then-rename) so partial writes can't corrupt the file;
   - emits a structured diagnostic listing keys written + keys preserved-due-to-conflict.
4. One outcome-altitude smoke test (per `feedback_test_outcome_altitude_required`) that invokes the production SKILL dispatch path with no pre-arranged state and verifies end-to-end behaviour.
5. STATE.md / roadmap bookkeeping line referencing this work-item's seal (per `docs/plans/v0-1-x-roadmap.md` shape).

### Out-of-scope (explicit)

- **Auto-mutation of `~/.claude/settings.json` on install** — D-TOKEN.ENFORCE rules out. The SKILL is the ONLY mutation surface; install-time scripts MUST NOT touch user settings.
- **Mutation of loam's own dispatch defaults** — loam already prefers Sonnet for its internal dispatches (per `~/.claude/CLAUDE.md` Token efficiency); no change there.
- **Auto-firing of the SKILL on cost-signal detection** — the SKILL describes the invocation criteria but the persona makes the call to invoke it; no hook that auto-invokes. (A future Wave-2-or-later enhancement could add a SessionStart cost-signal hook; out of this work-item.)
- **`ECC_CONTEXT_MONITOR_COST_WARNINGS=off`** — ECC-specific env var; loam has no equivalent monitor; absorbing the recommendation as-is would set a no-op env var. Skip.
- **Per-workspace overrides** — only `~/.claude/settings.json` (user-global) is in scope. Workspace-local `.claude/settings.json` overrides are user's call to configure separately if desired.
- **Cost-measurement / telemetry of post-write savings** — the SKILL surfaces ECC's claimed-savings numbers (cited as such); it does not measure loam-specific savings. Cost-measurement is a separate work-item (FIDRAFT candidate, surfaced §11).
- **Changes to `/cost`, `/clear`, `/compact` Claude-built-in commands** — those are Claude Code primitives; loam composes against them but does not modify them.
- **Migration tooling for existing settings.json files with deprecated/legacy keys** — the merge is forward-only; users with manually-set legacy keys keep them (conflict-surface per-key).

---

## §4 — Acceptance criteria

Each AC is outcome-shape; each ladders to the prime objective (AC.PO.1 primary-persona translation-burden + AC.PO.2 harness toolkit per `docs/VALUE_PROPOSITION.md`); each is one-test-per-criterion; each passes the method-in-AC test (the AC could be satisfied by more than one implementation).

| AC ID | Outcome | Verification | Ladders to |
|---|---|---|---|
| **AC.TOKEN.1** | A "Token-optimization defaults" section exists in `docs/getting-started.md` listing the 4 recommended settings (Sonnet default, `MAX_THINKING_TOKENS=10000`, `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50`, MCP/tool caps) with a one-sentence rationale per setting and a one-line pointer to the SKILL. | Test reads `docs/getting-started.md` post-build; greps for each of the 4 setting names + the SKILL-pointer string; asserts presence; asserts the section header appears AFTER the five-step bootstrap headers. | AC.PO.1 (primary-persona translation-burden — docs absorbs the technical detail in plain prose for the docs-first user discovery path). |
| **AC.TOKEN.2** | A SKILL bundle exists at `plugins/loam-skills/skills/cost-optimised-defaults/SKILL.md` with valid frontmatter (`description` field present + non-empty) that describes the invocation criteria (user cost-signal patterns + explicit `/skill` invocation). | Test reads `SKILL.md`; parses frontmatter; asserts `description` exists, non-empty, names at least one cost-signal trigger pattern. SKILL discoverable via the standard skill-discovery surface (existence of file at canonical path is necessary + sufficient per the SKILL plugin shape). | AC.PO.2 (harness toolkit — SKILL adds to the toolkit the persona invokes on cost-signal). |
| **AC.TOKEN.3** | The settings-merge mechanism preserves existing user keys in `~/.claude/settings.json` when writing recommended values — never silently overwrites. | Test fixture: write a `~/.claude/settings.json` with a non-loam user key (e.g., `theme: "dark"`); invoke the merge mechanism with user approval; assert post-merge file contains both the user's pre-existing key AND the recommended keys; assert no key value silently overwritten (any collision on a recommended key MUST be surfaced to the user via diagnostic + accept user's choice). | AC.PO.1 (sovereignty preservation IS translation-burden absorption — user doesn't need to know what's safe to write). |
| **AC.TOKEN.4** | The SKILL describes an explicit user-approval flow before any write: SKILL presents the proposed keys + values to the user; awaits explicit approval ("yes" / "proceed" / equivalent); writes only on approval; on rejection emits a "no changes" diagnostic + exits without write. | Test invokes the SKILL with simulated user rejection input; asserts no write to `~/.claude/settings.json`; asserts diagnostic emitted naming "no changes". Test invokes with simulated approval input; asserts write occurs. | AC.PO.1 (user-config sovereignty preserved per D-TOKEN.ENFORCE). |
| **AC.TOKEN.5** | Install-time scripts (per `install-from-source.txt` + any post-install hooks) do not touch `~/.claude/settings.json`. | Test: run a fresh-install fixture (clean `~/.claude/` for the test user OR isolated `HOME` via env override per test isolation patterns); run install per `install-from-source.txt`; assert `~/.claude/settings.json` either remains absent OR retains its pre-install content byte-identical. | AC.PO.1 + the explicit out-of-scope item per §3 (auto-mutation rejected). Negative AC — verifies an absence. |
| **AC.TOKEN.S** *(outcome-altitude)* | Synthetic end-to-end session: a fresh loam workspace, simulated user cost-signal in chat ("loam is expensive — what can I do?"), persona invokes the cost-optimised-defaults SKILL, SKILL presents the 4 recommended settings, user approves via simulated input, `~/.claude/settings.json` updated with the 4 keys, pre-existing user keys preserved, structured diagnostic emitted naming each key written. Test calls the production persona dispatch path with NO pre-arranged state (no fixture stubbing of the persona's SKILL-invocation step; no mock of the merge logic). | Test driver spawns a fresh-workspace persona session, injects the cost-signal message, captures the persona's SKILL-invocation, captures the SKILL output, captures the merge result, asserts each behaviour. Per `feedback_test_outcome_altitude_required` — invokes production entry-point with no pre-arranged state. | AC.PO.1 + AC.PO.2 jointly. |

**Method-in-AC self-check:** every AC above can be satisfied by more than one implementation (Python merge vs Bash+jq merge for AC.TOKEN.3; markdown section anywhere within `getting-started.md` so long as it satisfies the position constraint for AC.TOKEN.1; YAML vs JSON frontmatter for AC.TOKEN.2 — all builder's call). The AC pins the OUTCOME, not the method. Per `feedback_loose_AC_text_fix_AC_not_implementation`, if the builder discovers loose AC text at build-time, fix the AC doc-only after verifying nothing else depends on the loose reading; do NOT tighten implementation arbitrarily.

---

## §5 — Sealed-component fence

Single-component fence: **`workspace-bootstrap`** (anchor pattern confirmed via `docs/plans/sealed/handsoff-loop-real-build.manifest.yaml` precedent — same anchor used for the recent persona-invocable SKILL bundle landing).

**Anchor rationale:** `workspace-bootstrap`'s LIVE seal-test (`framework/workspace-bootstrap/tests/test_no_sealed_amendments.py`) admits every surface this work-item touches:
- `plugins/loam-skills/` (the SKILL bundle) — admitted prefix verified against the precedent manifest.
- `docs/getting-started.md` — admitted via universal-paths (docs is universal-prefix surface per amendment #22 ruling #3 + the manifest convention in `plugins/dev-sdlc/docs/conventions/plan-docs.md` §3).
- `docs/plans/` — admitted via universal prefix (plan-doc + manifest land here).
- `docs/STATE.md` + `docs/plans/v0-1-x-roadmap.md` — admitted via universal files for the bookkeeping backfill.

The `loam-skills` plugin's OWN seal-test is stale (predates the `docs/rebuild/` → `docs/` migration); using `workspace-bootstrap` as the anchor mirrors the `handsoff-loop-real-build` precedent and `subloam-driver-fix` precedent. Builder MUST verify the seal-test still admits the named prefixes at apply-time (cheap re-check via `cat framework/workspace-bootstrap/tests/test_no_sealed_amendments.py | grep plugins/loam-skills/`); if a tree change has intervened, halt-and-surface per §6.

`extra_allowed_prefixes`: EMPTY. No sealed-source edit outside the workspace-bootstrap anchor.

---

## §6 — Halt triggers

If any of these fire during the build cycle, the builder halts and surfaces to the dispatcher BEFORE continuing:

1. **`~/.claude/settings.json` merge logic accidentally overwrites a user key in a smoke-test scenario** — halt; the AC.TOKEN.3 sovereignty guarantee is load-bearing; surface the failing case for design review.
2. **The SKILL's invocation criteria, on dry-run review, would trigger on benign user utterances** (false-positive rate > ~1 per 10 sessions in synthetic dry-run) — halt; the SKILL must be discoverable on real cost-signals without auto-firing on chatty cost-mentions; tighten the trigger phrasing in the SKILL frontmatter.
3. **The `workspace-bootstrap` seal-test no longer admits one of the named prefixes** at apply-time (tree state has changed since this plan was authored) — halt; surface; decide between (a) re-anchor to a different component, (b) widen `workspace-bootstrap`'s admitted prefixes via a separate dispatch, (c) surface to maintainer for a third path.
4. **The outcome-altitude smoke (AC.TOKEN.S) cannot be authored without pre-arranged state** (e.g., the persona-dispatch-path can't be invoked in test isolation without mocks) — halt per `feedback_test_outcome_altitude_required`; surface; the AC class is load-bearing per the memory rule, never reduce to structural-only.
5. **The ECC-cited cost-savings percentages turn out to be unverifiable or load-bearing-incorrect** at build-time when the docs section is authored — halt; rephrase the docs section to attribute the claim to ECC ("ECC reports ~60% cost reduction; loam has not independently verified") rather than restate as loam's measured claim. Per `feedback_claim_or_cite_no_fake_sources`.
6. **A pre-build maintainer ruling on Q1-Q3 below (§8) lands that changes the work-item shape** — halt; re-author the affected section.

---

## §7 — Ship shape

Single-amendment work-item; no sub-amendment series. Commit ladder:

1. **Source-edit commit** (BASELINE for the seal-diff window): add docs section + SKILL bundle + merge mechanism + tests.
2. **`loam amend apply` commit** (manifest-driven; standard).
3. **Seal commit** (narrative per §9 below + §14 SHA register backfill).
4. **STATE.md + roadmap backfill** (universal-file edit per §3).

Wall-clock estimate: 2–4 hours AI-time (cost band: sm per parent plan §5 WI-3). Verified-against-rubric per `feedback_duration_estimation_rubric.md` — ~15-25 tool calls × 0.1-0.15 wall-clock/call. Maintainer gate-review: separate (depends on availability).

**Post-seal verification:** read the SKILL frontmatter from a fresh shell to confirm it discoverable; read the docs section from a fresh shell to confirm it renders; run the smoke test (AC.TOKEN.S) end-to-end.

---

## §8 — Open questions for maintainer ratification

Ranked by criticality per `feedback_one_question_at_a_time`. Most likely answerable from this plan-doc without a separate Telegram round; surface only if maintainer wants to overrule the recommendation.

### Q1 (CRITICAL) — Does the docs section live in `docs/getting-started.md` or a separate `docs/cost-optimization.md`?

**Recommendation:** `docs/getting-started.md`, AFTER the five-step bootstrap. Rationale: the user-discovery surface IS getting-started; a separate cost-optimization doc page is a click further from the user-first-touch and would be missed by the docs-first user discovery path. The section can be short (~10 lines + SKILL pointer) without bloating getting-started.

**Reversibility:** High. Doc page is easy to split later if it grows.

### Q2 (IMPORTANT) — Should the SKILL merge BOTH env-var settings (`MAX_THINKING_TOKENS`, `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`) AND `model: sonnet` to `~/.claude/settings.json`, or only the settings.json-shaped keys and leave env vars to docs?

**Recommendation:** Merge ALL FOUR to `~/.claude/settings.json` (the file supports an `env:` key for environment variables per Claude Code's settings hierarchy; both env vars and model defaults can co-exist in the same file). Single mutation surface = simpler user mental model + simpler rollback.

**Open sub-question:** Verify Claude Code's `settings.json` `env:` field shape at build-time (cheap WebFetch to `https://docs.claude.com/en/docs/claude-code/settings`). If env vars don't live in settings.json, the docs section must instruct the user to set env vars separately (shell profile) and the SKILL writes only the model + non-env settings.

### Q3 (NORMAL) — Should the SKILL include a "preview the diff before approval" step?

**Recommendation:** Yes — the approval flow names the EXACT new keys + values + any collision-keys before asking "proceed?". Adds ~5 lines to the SKILL body; high-leverage for user trust.

**Reversibility:** High.

### Q4 (NORMAL) — Does the SKILL support an "undo" / "revert to pre-merge state" command?

**Recommendation:** Out-of-scope for this work-item. The SKILL's diagnostic names each key written; user can manually delete the keys to revert. A follow-up SKILL (`cost-optimised-defaults-undo`) is a FIDRAFT candidate if user demand surfaces. Adding undo to this work-item bloats the AC ladder.

---

## §9 — Seal narrative (drafted; builder finalizes at seal-time)

```
Token-optimization defaults documenter + opt-in writer SKILL

Loam absorbs ECC's recommended token-optimization settings (Sonnet default,
MAX_THINKING_TOKENS=10000, CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50, MCP/tool caps)
via two complementary surfaces:

1. A documented preset in docs/getting-started.md so docs-first user discovery
   sees the recommended settings with rationale before they hit cost pain.
2. An opt-in SKILL at plugins/loam-skills/skills/cost-optimised-defaults/ that
   the persona invokes on user cost-signal; presents the settings + awaits
   explicit user approval before merging into ~/.claude/settings.json
   non-destructively (existing keys preserved).

Per D-TOKEN.ENFORCE (maintainer ruling TG 12301): NO auto-mutation of
~/.claude/settings.json on install. User-config sovereignty preserved; SKILL
is the only mutation surface and writes only on explicit user approval.

Composes with Lens-1 (Claude settings.json hierarchy primitive), Lens-2 (SKILL
absorbs technical detail for the persona's translation-layer job), and the
existing feedback_compact_clear_decision_heuristic memory rule (the heuristic
informs WHEN to apply the discipline; the SKILL+docs install the SETTINGS that
make the discipline effective).

Single-component fence: framework/workspace-bootstrap/. ECC cost-savings
percentages attributed to ECC, not restated as loam-measured.
```

---

## §10 — F2 Ruthless Feedback (honest doubts)

1. **The SKILL's invocation criteria are inherently loose.** "User signals cost-awareness" is a fuzzy class. The frontmatter `description` will enumerate trigger patterns ("loam is expensive", "tokens are burning", "what should my settings be", explicit `/skill cost-optimised-defaults` invocation), but the persona's actual invocation decision is judgement-bound. False-negative (persona misses the signal) is the worse failure mode than false-positive (persona invokes unnecessarily — user can just say "no thanks"); design accordingly. Halt trigger §6.2 catches the false-positive case; the false-negative case is unmeasurable without user telemetry (out of scope).

2. **The ECC-cited cost-savings percentages (60% / 70%) are ECC's claims, not loam-measured.** The docs section MUST attribute them to ECC (per CLAIM-OR-CITE). Loam has not benchmarked Sonnet-vs-Opus cost savings on loam-typical workloads. Risk: user sees "60% savings" in loam docs, applies the settings, sees less savings (or more — both possible), feels misled. Mitigation: docs section uses attribution language ("ECC reports", "as documented in ECC's settings table"); FIDRAFT capture for a future loam-specific cost-measurement work-item (§11).

3. **The non-destructive merge guarantee has a sharp edge case.** A user who has already set ONE of the recommended keys to a different value (e.g., `MAX_THINKING_TOKENS=20000` because they prefer deeper thinking) sees the SKILL surface the collision, accepts loam's recommended `10000`, and silently loses their preferred value. Per AC.TOKEN.3 the SKILL surfaces collisions BUT the user might rubber-stamp "approve" without reading carefully. Mitigation: the approval flow MUST list collision-keys with their existing value AND the recommended value side-by-side, not just "approve all". This is currently a recommendation in §3 in-scope item 3 + Q3 above; the AC ladder doesn't pin it. Consider tightening AC.TOKEN.4 at build-time if the build surfaces the gap.

4. **The recommendation to merge env vars into `~/.claude/settings.json` (Q2) depends on Claude Code's settings.json schema accepting them.** If it doesn't (Claude Code's env-var surface is shell-env-only), the SKILL must EITHER write to a shell profile (high-blast-radius — modifying user's `.zshrc` is far more invasive than settings.json) OR fall back to docs-only for env vars (split UX). Verify-at-build-time per Q2 sub-question; halt-and-surface if assumption breaks.

5. **The "opt-in SKILL" framing assumes the user understands what a SKILL is.** Non-tech users in particular may not know what `/skill cost-optimised-defaults` means as a command-line invocation. The SKILL is also auto-discoverable (persona invokes on cost-signal detection without explicit command), which mitigates — but the docs section pointer ("or run `/skill cost-optimised-defaults`") may confuse first-touch readers. Alternative phrasing: "or ask loam to apply these for you — it'll surface the options + ask before changing anything." Builder's call; AC.TOKEN.1 pins the pointer's presence but not its exact wording.

6. **F4 scope-confidence self-check on this plan-doc.** §4 ACs are TIGHT (high confidence on the outcome shapes — each AC's outcome is well-bounded by ECC's documented surface + D-TOKEN.ENFORCE constraints). §3 in-scope item 3 (settings-merge mechanism) is INTENTIONALLY LOOSE on implementation (Python helper vs Bash one-liner vs SKILL-embedded — builder's call); the constraints (non-destructive, atomic, diagnostic-emitting) pin the outcome without pinning the method. §6 halt triggers are TIGHT (specific failure modes; each carries a named action). §8 open questions are LOOSE (alternatives + recommendation). Mix matches the confidence shape per F4.

---

## §11 — FIDRAFT capture (for maintainer to graduate or discard)

- **F-LOAM-COST-MEASUREMENT** — §10 doubt #2 surfaces the need for loam-specific cost-savings measurement. A follow-up work-item could instrument a sample loam workload (e.g., 10 typical persona dispatches) before + after applying the recommended settings, surface the measured delta, replace the docs section's ECC-attributed numbers with loam-measured numbers. Cost band: sm-md. Composes with the existing `framework/cost-governance/` component.
- **F-COST-OPTIMISED-DEFAULTS-UNDO** — §8 Q4 surfaces undo as out-of-scope; a follow-up SKILL `cost-optimised-defaults-undo` could reverse the merge if user requests. Captured per `feedback_durable_capture_for_planned_work`; graduate on first user request.
- **F-COST-SIGNAL-AUTOFIRE-HOOK** — §3 explicitly out-of-scope: a SessionStart or UserPromptSubmit hook that detects cost-signal patterns and auto-invokes the SKILL. Out-of-scope here per minimum-surface discipline; FIDRAFT candidate for a future hooks-bundle work-item (composes with parent plan WI-2 security hooks).

---

## §12 — Provenance trail

All citations Tier-0 verified (file-read or WebFetch) on 2026-05-24.

**Maintainer directives:**
- Telegram 12301 (2026-05-24) — D-TOKEN.ENFORCE three-part ratification ("B": document + opt-in SKILL + reject auto-mutation).
- Telegram 12235 / 12240 / 12242 — parent absorption plan framing (non-tech-user audience; absorb-the-useful; drop AGENTS.md).

**ECC source (verified 2026-05-24 via WebFetch):**
- `https://raw.githubusercontent.com/affaan-m/everything-claude-code/main/README.md` — "Token Optimization & Cost Management" section — 4 settings + claimed-savings percentages + MCP/tool caps + `/clear`/`/compact`/`/cost` discipline.

**Loam sources (verified 2026-05-24 via Read/Bash):**
- `/Users/lukeivers/loam/CLAUDE.md` — 7 lenses; Token efficiency global discipline.
- `/Users/lukeivers/loam/docs/VALUE_PROPOSITION.md` — primary persona as translation layer (AC.PO.1 + AC.PO.2 source).
- `/Users/lukeivers/loam/docs/getting-started.md` — current shape (5-step bootstrap + onboarding ritual + workflow chain); confirmed no existing token-optimization section.
- `/Users/lukeivers/loam/plugins/loam-skills/skills/` — 22 existing SKILL bundles; confirmed `cost-optimised-defaults/` absent; SKILL shape exemplars: `translation-discipline/SKILL.md`, `precompact-hook/SKILL.md`.
- `/Users/lukeivers/loam/plugins/dev-sdlc/docs/conventions/plan-docs.md` — plan-doc shape (§1-§16 convention; AC-ID scope-descriptive ruling; universal-paths admission per amendment #22).
- `/Users/lukeivers/loam/docs/plans/sealed/handsoff-loop-real-build.manifest.yaml` — sealed-component fence precedent for `workspace-bootstrap` anchor admitting `plugins/loam-skills/` + `docs/plans/` + `docs/STATE.md`.
- `/Users/lukeivers/loam/docs/plans/drafts/everything-claude-code-absorption-master-plan.md` — parent plan §3.1 P3 + §4 D-TOKEN.ENFORCE + §5 WI-3 binding contract.

**Memory rules referenced:**
- `feedback_compact_clear_decision_heuristic.md` — composes with the SKILL (heuristic informs WHEN; SKILL installs SETTINGS).
- `feedback_test_outcome_altitude_required.md` — AC.TOKEN.S compliance source.
- `feedback_loose_AC_text_fix_AC_not_implementation.md` — build-time guidance if AC text turns out loose.
- `feedback_claim_or_cite_no_fake_sources.md` — docs section attribution of ECC-cited savings percentages.
- `feedback_durable_capture_for_planned_work.md` — FIDRAFT graduation pattern.
- `feedback_summarize_and_surface_decisions.md` — §1 + §8 format.
- `feedback_one_question_at_a_time.md` — §8 ranking.
- `feedback_duration_estimation_rubric.md` — §7 wall-clock band.
- `feedback_no_amend_in_agent_dispatches.md` — builder discipline reminder.
- `feedback_subagent_odd_violation_halt.md` — builder MUST halt on ODD violations discovered in this work-item OR surrounding code.

**Lens references:**
- L1 Claude-leverage-first — composes against `~/.claude/settings.json` hierarchy primitive + SKILL primitive.
- L2 Harness + primary-persona value — both tests satisfied (translation-burden absorption + toolkit addition).
- L3 ODD authoring — outcome-shape ACs + builder's-call method.
- L4 Prompt scope ↔ confidence — TIGHT on ACs, LOOSE on implementation per §10 doubt #6.
- L7 Ruthless Feedback — §10 honest doubts.

---

## §14 — Method-decision register (placeholder)

Populated at build time by the builder. Expected D-build.* entries:

- **D-build.TOKEN.1** — merge-implementation choice (Python helper vs Bash one-liner vs SKILL-embedded inline-Python). Recommendation: Python helper colocated with SKILL bundle (`plugins/loam-skills/skills/cost-optimised-defaults/merge.py`); single import; easy test isolation.
- **D-build.TOKEN.2** — env-vars-in-settings.json question (Q2 verification at build-time).
- **D-build.TOKEN.3** — SKILL frontmatter exact invocation-trigger phrasing.
- **D-build.TOKEN.4** — collision-display format in the approval flow.

SHAs backfilled by `loam amend seal --plan-doc` per convention §5.

---

### Commit SHAs

- Amendment commit: `b0f44fa540cdb561e0ba6769511be7d2530a7533` —
  `chore(amend): token-defaults-optin-skill manifest+apply — workspace-bootstrap BASELINE+sidecar bump to cc994fa`
- Seal commit: `e4c31231d133a23fb40e952d118773cfc4484b05` —
  `chore(seals): token-defaults-optin-skill — workspace-bootstrap at b0f44fa`
## §15 — Backwards-compat verification

Existing tests that MUST still pass post-seal:
- All `framework/workspace-bootstrap/tests/test_no_sealed_amendments.py` — seal-diff window verification.
- All existing `plugins/loam-skills/skills/*/` SKILL-discovery tests (if any) — confirm new SKILL doesn't shadow or collide with existing SKILL names.
- All existing `docs/getting-started.md` doc-lint / link-check tests (if any) — confirm new section doesn't break doc rendering.
- All existing `~/.claude/settings.json` consumer tests (if loam has any covering its own dispatch settings reading) — confirm no consumer breaks on new keys present in settings.

---

## §16 — Halt-and-surface findings (this plan-authoring turn)

Raised + ruled this turn:

1. **Anchor verification.** Used `workspace-bootstrap` per the `handsoff-loop-real-build.manifest.yaml` precedent (same plan-doc shape, same kind of `plugins/loam-skills/` + `docs/getting-started.md` surfaces). Builder MUST re-verify at apply-time per §6.3.
2. **`ECC_CONTEXT_MONITOR_COST_WARNINGS=off` absorption decision.** Skipped per §3 out-of-scope: ECC-specific env var with no loam equivalent; absorbing as-is would set a no-op env var. Decision recorded autonomously per operational-objective test — the operational objective is to absorb settings that meaningfully reduce loam cost; ECC's no-op-for-loam env var fails the test trivially.
3. **`docs/cost-optimization.md` vs section-in-getting-started decision.** Surfaced as Q1 §8 (CRITICAL); recommendation is section-in-getting-started; maintainer may overrule.
4. **Env-vars-in-settings.json verification.** Surfaced as Q2 §8 (IMPORTANT) + open sub-question; recommendation is merge ALL FOUR; builder verifies Claude Code's settings.json schema at apply-time per Q2 sub-question.
5. **Outcome-altitude smoke design constraint.** §6.4 halt trigger captures the load-bearing requirement per `feedback_test_outcome_altitude_required`; AC.TOKEN.S is the named outcome-altitude AC.
6. **Cost-savings attribution language.** §10 doubt #2 + §6.5 halt trigger; docs section MUST attribute to ECC; loam-specific measurement is FIDRAFT.

---

## §17 — Authoring trail

Authored 2026-05-24 by `loam-plan-author` subagent, dispatched by the master-absorption-plan dispatcher per the D-TOKEN.ENFORCE ratification (Telegram 12301 / "B" ruling). Working directory verified: `/Users/lukeivers/loam/`. WD-as-literal-first-action discipline per `feedback_dispatch_cd_literal_first_action` honored (this dispatch's first tool call was `cd /Users/lukeivers/loam && pwd`).

Plan-doc ratification: pending. Build dispatches against this contract on maintainer ratification + any Q1-Q4 (§8) rulings.

# Token-optimization defaults documenter + opt-in writer SKILL

Loam absorbs ECC's recommended token-optimization settings (Sonnet
default, MAX_THINKING_TOKENS=10000, CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50,
MCP/tool caps) via two complementary surfaces: a documented preset in
docs/getting-started.md so docs-first user discovery sees the
recommended settings + their cost-rationale before they hit cost pain,
and an opt-in SKILL at plugins/loam-skills/skills/cost-optimised-
defaults/ that the persona invokes on user cost-signal, presents the
settings + awaits explicit user approval, and on approval merges them
into ~/.claude/settings.json non-destructively (existing user keys
preserved; collisions surfaced + accept user's choice; atomic
write-temp-then-rename).

Per D-TOKEN.ENFORCE (maintainer ruling Telegram 12301 / "B"): NO
auto-mutation of ~/.claude/settings.json on install — user-config
sovereignty preserved; SKILL is the only mutation surface and writes
only on explicit user approval. Install-time scripts verified not to
touch ~/.claude/settings.json (AC.TOKEN.5 negative AC).

Surface added:
  - docs/getting-started.md — "Token-optimization defaults" section
    after the five-step bootstrap; lists the 4 recommended settings
    with one-sentence rationale per setting (ECC cost-savings
    percentages attributed to ECC explicitly per CLAIM-OR-CITE — loam
    has not independently measured); single-line pointer to the SKILL.
  - plugins/loam-skills/skills/cost-optimised-defaults/SKILL.md —
    opt-in SKILL with frontmatter naming invocation criteria (user
    cost-signal patterns + explicit /skill invocation); body
    documenting the four settings, user-approval flow, non-destructive
    merge guarantee, toggle-back-off instructions.
  - plugins/loam-skills/skills/cost-optimised-defaults/merge.py
    (location at builder's call per D-build.TOKEN.1) — settings-merge
    implementation: reads existing settings.json (preserves content if
    absent), merges recommended keys WITHOUT overwriting pre-existing
    user values (collisions surfaced + accept user's choice per-key),
    writes atomically (temp-then-rename), emits structured diagnostic.
  - plugins/loam-skills/skills/cost-optimised-defaults/tests/ — one
    test file per AC (AC.TOKEN.1 / .2 / .3 / .4 / .5 / .S); AC.TOKEN.S
    is the outcome-altitude smoke invoking the production persona-
    dispatch path with no pre-arranged state.

Composes with Lens-1 (Claude Code ~/.claude/settings.json hierarchy
primitive + SKILL primitive — no custom invocation surface), Lens-2
(primary-persona translation-burden absorption: user says "loam is
expensive" → persona handles the technical detail; SKILL added to the
persona's toolkit), the existing feedback_compact_clear_decision_
heuristic memory rule (heuristic informs WHEN to apply discipline;
SKILL+docs install the SETTINGS that make the discipline effective),
and the global Token-efficiency discipline in ~/.claude/CLAUDE.md
(this generalises maintainer-only discipline to a user-facing surface).

Single-component fence: framework/workspace-bootstrap/. NOT merged to
main, NOT pushed, NOT published, NOT tagged — sealed-local-on-branch
is the deliverable; origin/main unchanged. NO Anthropic API key — all
smoke + dispatch via real claude binary per feedback_no_anthropic_api_key.
No version bump (version derives at release-time per feedback_version_
numbers_at_release_time).
