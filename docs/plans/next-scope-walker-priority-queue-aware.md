# Next-scope walker priority-queue-aware PATCH

**Status:** plan-only at authoring time. Plan-before-code per `feedback_plan_before_code`. Owner ratification: dispatch brief from dispatcher 2026-05-14 explicitly authorises closure of FIDRAFT F-NEXT-SCOPE-EMPTY-§4 (captured 2026-05-14 from v0.10.1 publish output; activation gate: pre-v1.0 release-CLI consistency sweep). This PATCH executes that closure.
**Slug:** `next-scope-walker-priority-queue-aware` (scope-descriptive; no version pre-baked per `feedback_version_numbers_at_release_time`).
**Date authored:** 2026-05-14.
**Class:** **PATCH** per `docs/release-versioning-policy.md`. Helper-internal walker change inside the existing `loam release` post-ship review surface (the `_read_roadmap_priority_queue` helper at `framework/tools/loam/src/loam_cli/release/post_ship.py:56-112`). No public API change. No new outcome capability — restores an operator-facing surface that regressed at v0.10.0 when §4's structure changed but the walker wasn't updated. Trace-data layer (operator informational output) only.
**Predecessor:** v0.10.4 PATCH SHIPPED PUBLIC (sealed `aa78baf`; published `4a94c4d`). Build-forward per `feedback_build_forward_on_publish_pending`.
**Working directory:** `/Users/lukeivers/loam/`.
**Version derivation:** at release-time per `feedback_version_numbers_at_release_time`: `next_PATCH(v0.10.4) = v0.10.5`. Plan-doc slug scope-descriptive (no version pre-baked); AC family scope-descriptive (`AC.NSWP.*` for `next-scope-walker-priority-queue-aware`).

---

## §1 — Outcome shape (the "why")

The release CLI's post-ship review block (`framework/tools/loam/src/loam_cli/release/post_ship.py`) surfaces a "Next-scope proposal" naming the next-build candidate's objective + class hint + fence. The walker reads `docs/release-roadmap.md` §4 and currently looks for `### v0.X.Y — <objective>` headings (the pre-restructure shape). After v0.10.0's `release-roadmap-priority-queue-restructure` MINOR (sealed `c71b2fa`; published `5dcc630`), §4 was restructured: pre-numbered version headings were replaced with a priority-ordered candidate queue using `### Candidate N — \`<slug>\` — <title>` headings, with a `**Slug:** \`<slug>\`. **Class:** <class>` line immediately following each candidate heading.

Pre-source-edit baseline (empirical, captured 2026-05-14 via `loam release v0.10.4 --plan-doc docs/plans/otel-tracer-version-honesty.md --dry-run`):

```
== Next-scope proposal ==

Next objective: (no entries in §4)
Class hint: (no entries in §4)
Fence: (no entries in §4)
```

Today's §4 carries 6 candidates in priority order:

1. `binary-usage-observation-harness` — Loam builds software from minimal input — Class: MINOR (END-USER) — line 187
2. `principle-foundation-structural-enforcement` — Loam's principle foundation is named and structurally enforced — Class: MINOR (META-FRAMEWORK) — line 232
3. `negative-alignment-detection` — Loam catches code that contradicts its own contract — Class: MINOR (END-USER) — line 280
4. `deep-personalization` — Loam's deep personalization through interaction capture — Class: MINOR (END-USER) — line 315
5. `plugin-suite-expansion` — Plugin suite expansion (one MINOR per plugin) — Class: per-plugin MINOR (END-USER) — line 354
6. `v1.0.0-stability-gate` — Loam is stable — Class: MAJOR (MIXED) — line 378

After this PATCH, the walker:

1. Reads `### Candidate N — \`<slug>\` — <title>` headings inside §4 (skipping `### §4-prelude` and any other `### `-but-not-`### Candidate `-prefixed sub-sections).
2. Picks the FIRST candidate (queue order = priority order per §4's authoring discipline; line 136: "Order in the queue reflects current priority decision; first item is 'next to build.'").
3. Surfaces the candidate's slug + title as the "Next objective", the class from the `**Slug:** ... **Class:** ...` line as "Class hint", and a fence pointer naming the slug.
4. When §4 has zero candidates (genuinely empty queue), surfaces an explicit "queue empty — author next candidate before next cycle" message rather than the misleading legacy "(no entries in §4)" string (which read like a parser bug, not an empty queue).

Closes F-NEXT-SCOPE-EMPTY-§4. Composes with v0.10.0 priority-queue-restructure MINOR (the change that surfaced this; the FIDRAFT capture noted: "the post-ship hook wasn't updated when the restructure DID ship").

---

## §2 — Prime objective ladder

```
VALUE_PROPOSITION.md prime objective
   └─ "primary persona is a translation layer between the user's
       natural-language intent and AI-effective execution"
        └─ documented features work as advertised + documented-state
           matches actual-state (v1.0 quality-bar criterion #1)
             └─ release-CLI's post-ship review block surfaces an
                accurate next-scope proposal for the operator (the
                "what's next?" surface that informs the next cycle's
                first dispatch)
                  └─ AC.NSWP.1 (walker reads the v0.10.0 §4 candidate-queue
                                  structure and surfaces the top-priority
                                  candidate's slug/title + class + fence
                                  — closes F-NEXT-SCOPE-EMPTY-§4 at the
                                  populated-queue case)
                  └─ AC.NSWP.2 (walker emits a structurally-honest
                                  "queue empty" message when §4 has zero
                                  candidates — replaces the misleading
                                  legacy "(no entries in §4)" output that
                                  read like a parser bug)
                  └─ AC.NSWP.3 (existing tests asserting on the pre-v0.10.0
                                  `### vX.Y.Z` heading shape are updated
                                  to assert on the new candidate-queue
                                  shape)
                  └─ AC.NSWP.4 (outcome-altitude dogfood probe — runs
                                  the release CLI's dry-run against the
                                  live canonical roadmap with the patched
                                  walker; confirms the actual surfaced
                                  candidate matches the live §4 queue's
                                  first candidate)
                  └─ AC.NSWP.S (seal-diff: only the named walker file +
                                  affected test file + plan-doc + manifest +
                                  smoke writeup + STATE/roadmap/FIDRAFT admin +
                                  dev-sdlc seal anchor artefacts touched)
```

The two VALUE_PROPOSITION tests:

- **Primary-persona test** — the post-ship next-scope proposal IS the operator-facing translation surface that turns "what should the next cycle be?" into "the top-priority queue entry is X with class hint Y and fence Z." The walker bug stripped this surface for every publish since v0.10.0; restoring it returns the surface to its intended translation function.
- **Harness test** — no harness extension; closes a defect within the existing post-ship review surface (the `_read_roadmap_priority_queue` helper contract).

Composes with: v0.10.0 `release-roadmap-priority-queue-restructure` (the MINOR that surfaced this — restructured §4 from pre-numbered headings to candidate-queue without updating the walker; this PATCH closes the gap), `feedback_loose_AC_text_fix_AC_not_implementation` (AC.NSWP.2 text was sharpened doc-only at plan-time after empirically observing the misleading "(no entries in §4)" was distinct from "(no §4 mapped-versions section)" — the walker had two separate placeholder branches and the queue-empty case maps to the former).

Composes with: F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH discipline (verified empirically: only one reference to F-NEXT-SCOPE-EMPTY-§4 exists in `docs/`, the entry itself; no dependent FIDRAFT entries reference it as a blocker / dep / unblocker; no flip-on-unblock action needed beyond the entry itself).

---

## §3 — Component fence

**PATCH spans one production file (`framework/tools/loam/src/loam_cli/release/post_ship.py`) + one test file (`framework/tools/loam/tests/test_AC_V060_6_post_ship_review.py`).** Seal anchor: dev-sdlc (matches the v0.10.x precedent for release-CLI helper changes — the release-CLI lives at `framework/tools/loam/` and is the canonical example of a "single-component PATCH with dev-sdlc seal anchor"). v0.10.2 + v0.10.3 + v0.7.x family all used this anchor for release-CLI helper extensions.

**PRIMARY (1 production file):**

- `framework/tools/loam/src/loam_cli/release/post_ship.py` — `_read_roadmap_priority_queue()` helper rewritten: replace `### v0.X.Y — <objective>` regex with logic walking `### Candidate N — \`<slug>\` — <title>` headings inside §4; pick first; extract slug + title + class line. Update the empty-queue placeholder strings to the new "queue empty — author next candidate" message.

**PRIMARY (1 test file):**

- `framework/tools/loam/tests/test_AC_V060_6_post_ship_review.py` — `test_proposal_carries_next_objective_class_and_fence` updated: the conftest `staged_repo` fixture's roadmap (lines 113-115) carries the legacy `### v0.7.0 — next things land here` shape; this test currently asserts on that shape (`"next things land here" in p.next_objective` + `"v0.7.0" in p.next_ac_or_fence`). Updated to assert against the new candidate-queue shape after the conftest fixture is updated. Other 6 tests in the file (placeholder + pre/post-1.0 eval + format + runner-emits) verify behaviour unaffected by the walker structure change and stay as-is.

**PRIMARY (1 conftest update):**

- `framework/tools/loam/tests/conftest.py` — `staged_repo` fixture's roadmap body (lines 105-116) updated: `## §4 Mapped versions` heading + `### v0.7.0 — next things land here` heading replaced with `## §4 Priority-ordered candidate queue` + a `### Candidate 1 — \`fixture-candidate\` — Fixture next-scope target` heading + a `**Slug:** \`fixture-candidate\`. **Class:** MINOR (FIXTURE).` line, mirroring the live canonical §4 structure. This is the single point that makes the fixture roadmap match the v0.10.0+ structure the walker is now coded against.

**PRIMARY (smoke writeup):**

- `docs/experiments/next-scope-walker-priority-queue-aware-hard-smoke.md` — slug-named per `F-CYCLE-ARTEFACT-SLUG-NAMING`. Outcome-altitude dogfood probe: capture verbatim before/after `loam release` dry-run output against the live canonical roadmap (before = "(no entries in §4)" shape from cycle-start baseline; after = top-candidate slug `binary-usage-observation-harness` + class `MINOR (END-USER)` + slug-fence pointer).

**SECONDARY (admin docs — universal-admission):**

- `docs/STATE.md` — append v0.10.5 row to §2 (Change log section).
- `docs/release-roadmap.md` — append v0.10.5 row to §2 + v0.10.5 standalone bold entry to §3 Active version.
- `docs/FUTURE_IDEAS_DRAFT.md` — flip F-NEXT-SCOPE-EMPTY-§4 entry to RESOLVED (status flip; entry preserved for audit trail).

**TERTIARY (cycle bookkeeping):**

- `docs/plans/next-scope-walker-priority-queue-aware.md` — this file.
- `docs/plans/next-scope-walker-priority-queue-aware.manifest.yaml` — schema-v3 manifest.
- `plugins/dev-sdlc/seals/SEAL_COMMIT.next-scope-walker-priority-queue-aware` — seal narrative.
- `plugins/dev-sdlc/tests/SEAL_COMMIT` — sidecar bump (auto at seal-time).
- `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` — BASELINE pointer auto-bump (auto at seal-time per dev-sdlc-anchored amendment convention; pre-included in AC.NSWP.S allow-list per the plan-doc-template-auto-bump-fence convention).

**Out of fence:**

- Any change beyond the walker helper at `framework/tools/loam/src/loam_cli/release/post_ship.py` and the test/conftest updates needed to align with it (HARD HALT #1).
- Changing the §4 candidate-queue structure itself (this PATCH updates the WALKER to match the structure, not the structure).
- Adding new fields to candidates (slug + title + class is the existing surface; this PATCH reads what's there).
- Changing post-publish backfill or any other release-CLI surface (post_publish_backfill.py, runner.py, gates.py, cli.py, notes.py — all untouched).
- Major-release eval branching (`_major_release_eval`), FIDRAFT recent reader (`_read_fidraft_recent`), or `format_proposal` shape — all untouched.
- Any pyproject.toml bumps (PATCH rides predecessor MINOR per AC.HONEST.1 / D-NFCLEAN.4 / D-SDPD / v0.8.3 / v0.10.1 / v0.10.2 / v0.10.3 / v0.10.4 precedent).
- `git commit --amend` (HARD HALT #4).
- Edits outside fence = halt.

---

## §4 — Acceptance criteria (`AC.NSWP.*`)

Each AC maps to a verifiable acceptance signal. Method stays builder's call.

### AC.NSWP.1 — Walker reads v0.10.0 §4 candidate-queue structure and surfaces top-priority candidate

`_read_roadmap_priority_queue()` walks §4 looking for `### Candidate N — \`<slug>\` — <title>` headings (regex tolerant to `—` em-dash or `-` hyphen separator and to whitespace variation; the live canonical roadmap uses em-dash); picks the FIRST such heading after the §4 boundary (inclusive of `### §4-prelude` skipping); extracts the slug from the backtick-delimited segment and the title from the post-second-separator segment; reads the immediately-following `**Slug:** \`<slug>\`. **Class:** <class>.` line to extract the class string. The proposal block's `next_objective` field carries `<slug> — <title>`; `next_class` carries the parenthesized class string (e.g., `MINOR (END-USER)`); `next_ac_or_fence` carries `see docs/release-roadmap.md §4 candidate \`<slug>\``.

**Verdict GREEN if:** running the post-ship build_proposal helper against the live canonical `docs/release-roadmap.md` (or any roadmap fixture carrying the v0.10.0+ candidate-queue structure) returns a proposal whose `next_objective` contains the top candidate's slug, whose `next_class` contains a recognizable class token (`MINOR` / `MAJOR` / `PATCH`), and whose `next_ac_or_fence` contains the slug.

**Verdict YELLOW if:** the walker correctly identifies the candidate but mis-extracts one of slug/title/class (partial-extraction fault).

**Verdict RED if:** the walker still emits the "(no entries in §4)" placeholder OR emits the legacy `### v0.X.Y` matcher's output OR fails to identify the first candidate when one exists.

`outcome-altitude: false` (function-altitude verification — assertion is on the helper's return value).

### AC.NSWP.2 — Empty-queue case emits structurally-honest message

When §4 exists but contains zero `### Candidate N` headings (genuinely empty queue — e.g., between MINORs when the previous queue is fully consumed and the next batch hasn't been authored), the walker emits an explicit "queue empty — author next candidate before next cycle" string (or equivalent operator-readable wording naming the action) for `next_objective` / `next_class` / `next_ac_or_fence`. The legacy "(no entries in §4)" string is removed — it was misleading post-v0.10.0 because §4 always has content (the prelude + queue header), it just may have zero candidates in the queue.

The two existing placeholder branches are clarified: the "roadmap not found" branch stays (file genuinely missing); the "no §4 mapped-versions section" branch text is updated to reflect post-v0.10.0 reality (the section is now named "Priority-ordered candidate queue", not "Mapped versions") and only fires when `## §4` itself can't be located.

**Verdict GREEN if:** synthesizing a roadmap fixture with `## §4 Priority-ordered candidate queue` heading + non-candidate prose body + zero `### Candidate N` headings, the walker returns a proposal whose `next_objective` carries the explicit empty-queue message naming the operator action.

**Verdict YELLOW if:** the message exists but uses ambiguous wording that doesn't name the action ("queue is empty" without "author next candidate").

**Verdict RED if:** the empty-queue case still returns the legacy "(no entries in §4)" or any other parser-bug-style placeholder that conflates "the parser is broken" with "the queue is genuinely empty."

`outcome-altitude: false`.

### AC.NSWP.3 — Pre-v0.10.0 `### vX.Y.Z` heading shape no longer expected; tests updated

The conftest `staged_repo` fixture (`framework/tools/loam/tests/conftest.py:105-116`) currently scaffolds a roadmap with the legacy `### v0.7.0 — next things land here` heading shape. The fixture is updated to scaffold the v0.10.0+ candidate-queue structure (`### Candidate 1 — \`fixture-candidate\` — Fixture next-scope target` + `**Slug:** \`fixture-candidate\`. **Class:** MINOR (FIXTURE).`). The test `test_proposal_carries_next_objective_class_and_fence` is updated to assert against the new shape (`"fixture-candidate" in p.next_objective` + `"MINOR" in p.next_class` + `"fixture-candidate" in p.next_ac_or_fence`). Other 6 tests in the file (`test_proposal_handles_missing_roadmap_with_placeholders`, `test_pre_1_0_major_eval_returns_pre_1_0`, `test_post_1_0_major_eval_returns_review_needed`, `test_format_proposal_renders_full_block`, `test_runner_emits_proposal_on_successful_publish`, `test_runner_emits_proposal_on_dry_run`) are unaffected by the walker shape change (they verify orthogonal behavior — placeholder branches, major-release eval, format function, runner integration) and stay as-is.

A NEW test is added at the same path: `test_proposal_handles_empty_candidate_queue` verifies AC.NSWP.2's empty-queue message by scaffolding a roadmap fixture with `## §4` heading + prose body + zero `### Candidate N` headings.

**Verdict GREEN if:** all 7 existing tests in `test_AC_V060_6_post_ship_review.py` PASS (the 1 updated + 6 unchanged), AND the 1 new test for empty-queue case PASSES, AND the full release-CLI test suite (~98 tests; pre-cycle baseline) PASSES with no regression.

**Verdict YELLOW if:** all updated/new tests pass but a non-walker test in the release-CLI suite breaks for an unrelated reason — investigate, then halt-and-surface if not traceable to this PATCH.

**Verdict RED if:** any updated test or new test fails OR any pre-existing release-CLI test that PASSED at cycle-start now fails.

`outcome-altitude: false` (test-runner verdict; the runner integration tests in this same file cover the runtime invocation path).

### AC.NSWP.4 — Outcome-altitude dogfood probe (live-canonical-roadmap dry-run before vs after)

Live runtime probe runs `loam release v0.10.4 --plan-doc docs/plans/otel-tracer-version-honesty.md --dry-run` (any sealed-public version + plan-doc that satisfies the gates) BEFORE the source edit and captures the actual `Next-scope proposal` block — the "(no entries in §4)" shape from the cycle-start baseline. After the source edit, re-runs the same command (after re-installing the loam CLI from source so the patched walker is the one running) and captures the new output: the top candidate's slug + title + class + slug-fence pointer. Documented at `docs/experiments/next-scope-walker-priority-queue-aware-hard-smoke.md` (slug-named per `F-CYCLE-ARTEFACT-SLUG-NAMING`) with verbatim before/after outputs.

The probe runs against the LIVE canonical `docs/release-roadmap.md` (not a synthetic fixture). The synthetic-fixture verification path is AC.NSWP.3's domain (test suite); AC.NSWP.4 is the outcome-altitude check that the change actually propagates from source through the installed CLI to operator-facing stdout.

**Verdict GREEN if:** smoke writeup at the slug-named path documents the probe with verbatim before/after output. Before-output contains "(no entries in §4)" (or equivalent legacy placeholder); after-output contains `binary-usage-observation-harness` (the live §4's current top candidate) + a recognizable class token + a slug-fence pointer.

**Verdict YELLOW if:** writeup exists but uses a non-runtime grep-only verification — would duplicate AC.NSWP.1 without adding outcome-altitude value.

**Verdict RED if:** writeup absent OR runtime probe still shows "(no entries in §4)" after edit (regression — source edit didn't actually propagate through `pip install`).

`outcome-altitude: true` (runtime invocation against the production-shipped CLI binary).

### AC.NSWP.S — Seal-diff discipline

`git diff --name-only <plan-commit>..<seal-commit>` shows changes ONLY under:

- `framework/tools/loam/src/loam_cli/release/post_ship.py`
- `framework/tools/loam/tests/test_AC_V060_6_post_ship_review.py`
- `framework/tools/loam/tests/conftest.py`
- `docs/experiments/next-scope-walker-priority-queue-aware-hard-smoke.md`
- `docs/STATE.md`
- `docs/release-roadmap.md`
- `docs/FUTURE_IDEAS_DRAFT.md`
- `docs/plans/next-scope-walker-priority-queue-aware.md`
- `docs/plans/next-scope-walker-priority-queue-aware.manifest.yaml`
- `plugins/dev-sdlc/seals/SEAL_COMMIT.next-scope-walker-priority-queue-aware`
- `plugins/dev-sdlc/tests/SEAL_COMMIT`
- `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` (BASELINE pointer auto-bump at seal-time — bookkeeping; pre-included in this allow-list per the plan-doc-template-auto-bump-fence convention)

NO entries in pyproject.toml; NO entries in any framework/* component beyond `framework/tools/loam/`; NO `__version__` updates; NO entries in any non-named source file.

**Verdict GREEN if:** `git diff --name-only <plan-commit>..<seal-commit>` matches the allow-list above with zero unlisted entries.

**Verdict YELLOW if:** all entries match BUT a benign extra (e.g., a docs/ entry not in the allow-list) appears — tighten allow-list doc-only post-build per `feedback_loose_AC_text_fix_AC_not_implementation` if intent matched.

**Verdict RED if:** any entry outside fence appears (e.g., pyproject.toml bump, post_publish_backfill.py edit, runner.py edit).

`outcome-altitude: false`.

---

## §5 — Decisions builder rules at build time

### D-NSWP.1 — Top-priority = first `### Candidate N` heading in §4 (queue-order = priority-order)

The §4 prelude (line 136) states: "Order in the queue reflects current priority decision; first item is 'next to build.'" There is no separate ranking signal — queue order IS priority order by §4's authoring discipline. The walker picks the FIRST `### Candidate N — \`<slug>\` — <title>` heading after `## §4` (skipping `### §4-prelude` and any other `### `-but-not-`### Candidate `-prefixed sub-sections like `### Items explicitly in backlog`).

**Ruling:** first-Candidate-heading-wins. No ambiguity; the §4 authoring discipline is explicit.

### D-NSWP.2 — Heading regex tolerates em-dash and hyphen separators

Live canonical §4 uses em-dash (`—`, U+2014) between Candidate-N and slug and between slug and title (e.g., `### Candidate 1 — \`binary-usage-observation-harness\` — Loam builds software from minimal input`). The pre-existing walker regex tolerated both (`[—-]`) for the legacy version-heading shape. The new walker regex preserves the same tolerance for the new candidate-heading shape. Slug is captured from the backtick-delimited segment between the two separators; title is captured from the post-second-separator segment.

**Ruling:** regex pattern `r"(?m)^###\s+Candidate\s+\d+\s*[—-]\s*` `\` `(?P<slug>[a-z0-9-]+)\` `\s*[—-]\s*(?P<title>.+)$"`. The class line follows: `r"(?m)^\*\*Slug:\*\*\s*\`(?P<slug2>[a-z0-9-]+)\`\.\s*\*\*Class:\*\*\s*(?P<class>[^.\n]+?)\.?\s*$"` (anchored within a few lines after the candidate heading; tolerates trailing period or newline).

### D-NSWP.3 — Class extraction: full class line parenthesized form preserved

Live canonical class lines use: `**Class:** MINOR (END-USER).` / `**Class:** MINOR (META-FRAMEWORK).` / `**Class:** MAJOR (MIXED) — structurally pinned at v1.0.0 ...`. The walker preserves the parenthesized full form (e.g., `MINOR (END-USER)`) up to the first period or em-dash; this is informationally richer than just `MINOR` and matches the operator's mental model when reading §4 directly.

**Ruling:** capture from `**Class:** ` to the first `.` or first ` — ` (whichever comes first); strip trailing whitespace. Falls back to "(class not parsed)" placeholder if the class line is missing or malformed.

### D-NSWP.4 — Empty-queue placeholder text

The legacy "(no entries in §4)" placeholder conflates two distinct cases: (a) the §4 section can't be located at all (parser fault or missing `## §4` heading); (b) §4 exists but has zero queue entries (genuinely empty queue between MINORs). Post-v0.10.0, case (b) is the operationally meaningful case — case (a) only fires if `release-roadmap.md` itself is structurally broken.

**Ruling:** distinct messages for the two cases:
- Roadmap missing → `(roadmap not found)` (preserved as-is — no behavior change)
- §4 heading missing → `(no §4 candidate-queue section)` (updated from "(no §4 mapped-versions section)" to match the post-v0.10.0 section name)
- §4 exists but zero candidates → `queue empty — author next candidate before next cycle` (new; replaces legacy "(no entries in §4)" for the empty-queue case)

### D-NSWP.5 — Single dev-sdlc seal anchor (release-CLI helper convention)

Matches v0.10.2 / v0.10.3 / v0.7.x precedent for release-CLI helper PATCHes — single-component change inside `framework/tools/loam/`, dev-sdlc seal anchor admits it via the existing universal-paths admission shape.

**Ruling:** dev-sdlc seal anchor.

### D-NSWP.6 — pyproject.toml versions stay at 0.10.0 (PATCH discipline)

Per AC.HONEST.1 / D-NFCLEAN.4 / D-SDPD / v0.8.3 / v0.10.1 / v0.10.2 / v0.10.3 / v0.10.4 precedent: PATCHes ride the predecessor MINOR's per-component-version. v0.10.0 bumped all 30 component pyprojects from 0.9.0 → 0.10.0. v0.10.5 (this PATCH) does NOT touch any pyproject.toml.

**Ruling:** zero pyproject.toml edits.

### D-NSWP.7 — `_PRE_1_0_PATTERN` and `_major_release_eval` untouched

The walker change is scoped to `_read_roadmap_priority_queue()`. The `_major_release_eval()` helper, the `_PRE_1_0_PATTERN` regex, the `_read_fidraft_recent()` helper, the `format_proposal()` formatter, and the `NextScopeProposal` dataclass shape all stay verbatim. Any change to those would be scope-creep.

**Ruling:** scope to the queue-walker only; touch no other helper.

---

## §6 — Out of scope (explicit)

- Any change to the §4 candidate-queue structure itself (this PATCH updates the WALKER to match the structure, not the structure).
- Adding new fields to candidates (slug + title + class is the existing surface; this PATCH reads what's there).
- Changing post-publish backfill (`post_publish_backfill.py` — separate surface, separate cycles).
- Changing the runner (`runner.py`), gates (`gates.py`), CLI dispatch (`cli.py`), or notes (`notes.py`) — all orthogonal to walker.
- Changing the `NextScopeProposal` dataclass shape, `format_proposal()` rendering, `_read_fidraft_recent()` helper, `_major_release_eval()` major-release eval logic, or `_PRE_1_0_PATTERN` regex.
- Restructuring §4 in any way (this PATCH is structurally read-only against §4's content).
- Bumping any component's pyproject.toml version (D-NSWP.6).
- Adding a `--plan-doc` flag, gate, or any new CLI surface.
- Touching `framework/tools/loam/src/loam_cli/release/post_publish_backfill.py` or any backfill helper (the previous v0.10.x PATCH chain owned that surface; this PATCH is post_ship.py-scoped).
- The 5 other `release/*.py` modules beyond post_ship.py.
- Any other FIDRAFT entry beyond F-NEXT-SCOPE-EMPTY-§4 (verified empirically: no other FIDRAFT references F-NEXT-SCOPE-EMPTY-§4 as a blocker / dep / unblocker).

---

## §7 — HARD HALTs (build-time)

1. **Out-of-fence edit discovered as necessary mid-build.** If any line beyond the named files needs to change for correctness, halt and surface for owner ruling. Do NOT silently extend scope.
2. **Empirical-recheck-before-halt discipline.** If you reach a "this is impossible" / "structurally infeasible" conclusion, run the 4-step discipline: state evidence; ≥3 alternative hypotheses; empirically test each; halt only after confirmation of structural infeasibility.
3. **Halt-and-surface ODD violations** including in surrounding code per `feedback_subagent_odd_violation_halt`. If a non-target line in the named files violates ODD §2.5 (non-objective code), surface as halt-and-surface finding in §status; do NOT silently fix.
4. **No `--amend`** per `feedback_no_amend_in_agent_dispatches`. If a corrective is needed post-source-edit, create a NEW commit. The collapse of audit trail via `--amend` is forbidden.
5. **Test regression you cannot trace to your edit.** If the release-CLI test suite (98 tests baseline) fails post-edit and the failure mode is not obviously the walker change, halt and surface.
6. **§4 heading-ordering ambiguous.** If the §4 priority-ordering signal is ambiguous (multiple candidates with no clear top-priority signal), halt and surface for owner ruling. (Pre-empted at plan-time per D-NSWP.1: queue order = priority order; no ambiguity.)
7. **Walker change touches non-walker code.** If the change requires touching `runner.py`, `gates.py`, `cli.py`, `post_publish_backfill.py`, `notes.py`, or the `NextScopeProposal` dataclass shape, halt and surface scope-creep.

---

## §8 — Dependencies

- v0.10.4 PATCH SHIPPED PUBLIC (sealed `aa78baf`; published `4a94c4d`; predecessor for build-forward per `feedback_build_forward_on_publish_pending`).
- v0.10.0 MINOR (`release-roadmap-priority-queue-restructure` — the change that surfaced this defect by restructuring §4 from `### vX.Y.Z` headings to `### Candidate N — \`<slug>\`` headings).
- v0.6.0 release-CLI substrate (the `loam release` verb + post-ship review block this PATCH extends).
- v0.7.4 / v0.10.1 / v0.10.2 / v0.10.3 release-CLI gate stack (release-CLI gates ready for scope-descriptive plan-doc paths via the `--plan-doc` flag — used at AC.NSWP.4 dogfood probe).
- F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH discipline (captured 2026-05-14 d9776ba) — verified empirically that no other FIDRAFT entries reference F-NEXT-SCOPE-EMPTY-§4 as a blocker / dep / unblocker.

---

## §9 — Estimated AI-time

| Stage | Estimated band | Midpoint |
|---|---|---|
| Plan-doc + manifest authoring | 15-25 min | ~20 min |
| Source-edit (walker rewrite + conftest fixture update + test update + 1 new test + slug-named smoke writeup with dogfood probe + STATE/roadmap admin + FIDRAFT flip) | 15-25 min | ~20 min |
| `loam amend validate` + manifest baseline backfill + `apply` + `seal` | 5-10 min | ~7 min |
| §13 §status backfill commit + roadmap-row seal-SHA backfill | 3-5 min | ~4 min |
| **Total** | **~38-65 min** | **~51 min** |

In-band against the FIDRAFT capture's 30-60 min band (~45 min midpoint). Slightly under-band on the lower edge because the walker change is structurally narrow (regex swap + extraction logic change) and the test surface is small (1 fixture update + 1 test update + 1 new test). Per `feedback_duration_estimation_rubric`: tool-call estimate ~250-400 calls × 0.1-0.15 min/call = 25-60 min raw; ~45 min midpoint accounts for parallel tool calls reducing critical path.

Owner gate-review time is separate (depends on dispatcher availability for publish ratification per ASK-FIRST).

---

## §11 — Authority chain

1. `docs/release-versioning-policy.md` (PATCH classification)
2. `feedback_version_numbers_at_release_time` (version derived at build-commence-time; `next_PATCH(v0.10.4) = v0.10.5`)
3. `feedback_scope_descriptive_ac_ids` (AC family `AC.NSWP.*`; slug `next-scope-walker-priority-queue-aware`)
4. `feedback_plan_before_code` (plan-doc + manifest BEFORE source edits)
5. v0.10.0 `release-roadmap-priority-queue-restructure` MINOR (the change that surfaced this defect)
6. v0.6.0 release-CLI substrate (the post-ship review surface this PATCH extends)
7. F-NEXT-SCOPE-EMPTY-§4 FIDRAFT (the entry this PATCH closes)
8. F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH (discipline for flipping dependent FIDRAFT entries when an unblocker lands; verified no dependents exist)
9. F-CYCLE-ARTEFACT-SLUG-NAMING (slug-named smoke writeup at `docs/experiments/next-scope-walker-priority-queue-aware-hard-smoke.md`)
10. `feedback_loose_AC_text_fix_AC_not_implementation` (D-NSWP.4 distinguishes the two empty-queue placeholder branches doc-only at plan-time)
11. `feedback_subagent_odd_violation_halt` (HARD HALT #3)
12. `feedback_no_amend_in_agent_dispatches` (HARD HALT #4)
13. `feedback_duration_estimation_rubric` (§9)
14. `feedback_build_forward_on_publish_pending` (§8 — v0.10.4 sealed-public; v0.10.5 builds forward)

---

## §12 — Source items (FIDRAFT entries closed by this PATCH)

- **F-NEXT-SCOPE-EMPTY-§4** (`docs/FUTURE_IDEAS_DRAFT.md:276`) — captured 2026-05-14 from v0.10.1 publish output. Activation gate: "pre-v1.0 release-CLI consistency sweep OR sooner if Luke uses next-scope-proposal operationally + the empty output is friction." This PATCH dispatches against the first activation gate (pre-v1.0 release-CLI consistency sweep). Status flips to RESOLVED in §source-edit commit; entry preserved with RESOLVED block citing this plan-doc + smoke writeup paths.

---

## §13 — §status

**Build cycle:** SHIPPED LOCAL 2026-05-14. Single-cycle PATCH closing FIDRAFT F-NEXT-SCOPE-EMPTY-§4 via `_read_roadmap_priority_queue` walker rewrite at `framework/tools/loam/src/loam_cli/release/post_ship.py:56-138` (regex updated from legacy `### vX.Y.Z` shape to v0.10.0+ `### Candidate N — \`<slug>\` — <title>` candidate-queue shape; class extraction from immediately-following `**Slug:** ... **Class:** ...` line; three distinct empty-queue placeholder branches per D-NSWP.4); conftest fixture updated to scaffold v0.10.0+ §4 shape; one test updated; one new test added covering the empty-queue case; slug-named smoke writeup with before/after live-canonical dogfood probe; STATE/roadmap/FIDRAFT admin. Sealed local; awaiting dispatcher dogfood publish per ASK-FIRST.

**Plan-doc commits:** plan-doc + manifest `ac946a6`; source-edit (walker rewrite + conftest fixture update + 1 test update + 1 new test + slug-named smoke writeup with before/after dogfood probe + STATE/roadmap admin + F-NEXT-SCOPE-EMPTY-§4 RESOLVED) `e3ab0c7`; manifest baseline backfill `74f3f19`; apply auto-commit (BASELINE + sidecar bump to `e3ab0c7`) `96b0bfe`; seal commit (deterministic seal) `da53584`.

### AC verdict matrix

| AC | Verdict | Evidence |
|---|---|---|
| AC.NSWP.1 — Walker reads v0.10.0 §4 candidate-queue structure and surfaces top-priority candidate | GREEN | Live-canonical probe (smoke writeup §3.2): `build_proposal(repo_root, "v0.10.4")` returns `next_objective="binary-usage-observation-harness — Loam builds software from minimal input"`, `next_class="MINOR (END-USER)"`, `next_ac_or_fence="see docs/release-roadmap.md §4 candidate \`binary-usage-observation-harness\`"`. Walker regex updated to `r"(?m)^###\s+Candidate\s+\d+\s*[—-]\s*\`(?P<slug>[a-z0-9.-]+)\`\s*[—-]\s*(?P<title>.+)$"` matching live canonical §4 shape; class extracted from `**Slug:** ... **Class:** ...` line via `r"(?m)^\*\*Slug:\*\*\s*\`[a-z0-9.-]+\`\.\s*\*\*Class:\*\*\s*(?P<class>[^.\n]+?)(?:\.\s*$|\s+—.*$|\s*$)"`. |
| AC.NSWP.2 — Empty-queue case emits structurally-honest message | GREEN | New `test_proposal_handles_empty_candidate_queue` (smoke writeup §3.3): synthetic-fixture roadmap with `## §4` heading + zero `### Candidate N` headings produces `next_objective="queue empty — author next candidate before next cycle"` (and same for `next_class` / `next_ac_or_fence`); legacy "(no entries in §4)" placeholder removed (test asserts `"(no entries in §4)" not in p.next_objective`). Per D-NSWP.4, the three placeholder branches are now distinct: roadmap-missing → `(roadmap not found)`; §4-section-missing → `(no §4 candidate-queue section)`; queue-empty → `queue empty — author next candidate before next cycle`. |
| AC.NSWP.3 — Pre-v0.10.0 `### vX.Y.Z` heading shape no longer expected; tests updated | GREEN | 8/8 post_ship tests PASS (smoke writeup §2.1): 7 pre-existing (1 updated `test_proposal_carries_next_objective_class_and_fence` asserting on the new shape: `"fixture-candidate" in p.next_objective` + `"FIXTURE" in p.next_class`; 6 unchanged orthogonal-behavior tests) + 1 new `test_proposal_handles_empty_candidate_queue`. Conftest `staged_repo` fixture's roadmap §4 body updated from legacy `### v0.7.0 — next things land here` to `## §4 Priority-ordered candidate queue` + `### Candidate 1 — \`fixture-candidate\` — Fixture next-scope target` + `**Slug:** \`fixture-candidate\`. **Class:** MINOR (FIXTURE).`. 78/78 release-CLI tests GREEN excluding 7 pre-existing Python-3.9 entry-point F-TF artefacts (verified pre-existing via `git stash` baseline at plan-doc commit `ac946a6`). |
| AC.NSWP.4 — Outcome-altitude dogfood probe (live-canonical-roadmap dry-run before vs after) | GREEN | Slug-named smoke writeup at `docs/experiments/next-scope-walker-priority-queue-aware-hard-smoke.md` §3 documents verbatim before vs after `Next-scope proposal` blocks captured against the LIVE canonical `docs/release-roadmap.md`. Before (cycle-start baseline at v0.10.4 seal `aa78baf`): `Next objective: (no entries in §4)` / `Class hint: (no entries in §4)` / `Fence: (no entries in §4)`. After (post-source-edit at commit `e3ab0c7`): `Next objective: binary-usage-observation-harness — Loam builds software from minimal input` / `Class hint: MINOR (END-USER)` / `Fence: see docs/release-roadmap.md §4 candidate \`binary-usage-observation-harness\``. The change propagated through `pip install -e .` (the homebrew `loam` binary loads `loam_cli` from the edited source tree directly). |
| AC.NSWP.S — Seal-diff discipline | GREEN | `git diff --name-only ac946a6..da53584` shows changes only under: `framework/tools/loam/src/loam_cli/release/post_ship.py` (walker rewrite); `framework/tools/loam/tests/conftest.py` (fixture update); `framework/tools/loam/tests/test_AC_V060_6_post_ship_review.py` (1 test updated + 1 new); `docs/experiments/next-scope-walker-priority-queue-aware-hard-smoke.md` (slug-named smoke writeup); universal-admission docs (`docs/STATE.md` + `docs/release-roadmap.md` + `docs/FUTURE_IDEAS_DRAFT.md`); plan-doc + manifest (`docs/plans/next-scope-walker-priority-queue-aware.{md,manifest.yaml}`); dev-sdlc seal anchor artefacts (seal narrative `plugins/dev-sdlc/seals/SEAL_COMMIT.next-scope-walker-priority-queue-aware` + `plugins/dev-sdlc/tests/SEAL_COMMIT` sidecar bump + `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` BASELINE pointer auto-bump — pre-included in §3 allow-list per the plan-doc-template-auto-bump-fence convention). NO entries in pyproject.toml; NO entries in any framework/* component beyond `framework/tools/loam/`; NO `__version__` updates. |

### AI-time actuals

| Stage | Estimated (§9) | Actual |
|---|---|---|
| Plan-doc + manifest authoring | 15-25 min | ~18 min |
| Source-edit (walker rewrite + conftest fixture update + 1 test update + 1 new test + slug-named smoke writeup with dogfood probe + STATE/roadmap admin + FIDRAFT flip) | 15-25 min | ~22 min |
| `loam amend validate` + manifest baseline backfill + `apply` + `seal` (incl. one stash for unrelated `uv.lock`) | 5-10 min | ~5 min |
| §13 §status backfill commit + roadmap-row seal-SHA backfill | 3-5 min | ~4 min |
| **Total** | **~38-65 min** | **~49 min** |

In-band — landed cleanly without HARD HALTs; one minor stash for unrelated untracked `framework/tools/loam/uv.lock` before seal (restored post-seal).

### Halt-and-surface findings

**No HARD HALTs fired in-cycle.**

**Pre-existing-test-failure clarification:** 7 tests fail in the release-CLI suite (`test_AC_V060_1_release_cli_dispatch.py` ×3, `test_AC_OSS_M6_6_loam_cli_subcommand_discovery.py` ×3, `test_AC_SDPD_plan_doc_flag.py` ×1) due to Python 3.9's `entry_points()` API not accepting `group=` kwarg. Verified pre-existing via `git stash` baseline at plan-doc commit `ac946a6` — same 7 failures. F-TF-* class environment artefact (Python 3.9 vs 3.11+ stdlib API mismatch); NOT in F-NEXT-SCOPE-EMPTY-§4 scope. Production `loam` binary uses Python 3.13 where these tests pass.

**Empirical-recheck-before-halt discipline:** never fired (the walker rewrite had an unambiguous fix-target derivable from the FIDRAFT capture's proposed-shape line + plan-doc D-NSWP.{1,2,3,4} rulings).

**One AC text disambiguation at plan-time** (per `feedback_loose_AC_text_fix_AC_not_implementation`): D-NSWP.4 distinguished the three placeholder branches (roadmap-missing, §4-section-missing, queue-empty) instead of conflating them as the legacy implementation did. Doc-only at plan-time; no post-build adjustment needed.

**One FIDRAFT entry flipped to RESOLVED:** F-NEXT-SCOPE-EMPTY-§4 at `docs/FUTURE_IDEAS_DRAFT.md:276`; entry preserved with RESOLVED block citing this PATCH cycle's plan-doc + smoke writeup paths.

**No new FIDRAFT entries captured.**

**F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH discipline verified:** `grep -rn "F-NEXT-SCOPE-EMPTY-§4" docs/` returned 1 reference (the entry itself). No other FIDRAFT entries reference F-NEXT-SCOPE-EMPTY-§4 as a blocker / dep / unblocker; no flip-on-unblock action needed beyond the entry itself.

---

## §14 — Method decisions

Plan-doc's §5 names the build-time decisions (D-NSWP.{1,2,3,4,5,6,7}). Each is a deterministic ruling at plan-time; no in-flight builder rulings expected unless a HARD HALT fires.
