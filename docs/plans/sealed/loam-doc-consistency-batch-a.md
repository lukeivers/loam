# loam-doc-consistency-batch-a — Doc-only consistency fixes (Batch A)

**Status:** plan-doc, plan-before-code. Authored 2026-05-22 by `loam-plan-author` agent (background dispatch).
**Working directory:** `/Users/lukeivers/loam/`.
**Parent capture:** loam-fresh-install-consistency-review-2026-05-23 (research artefact at `workspace/.scratch/claude-output/loam-fresh-install-consistency-review-2026-05-23.md`, captured by `loam-researcher` per Telegram 12002; persona-side persist at the same path).
**Predecessor (load-bearing):** amendment #144 publish-state commit `1d40311` (current main HEAD, `docs: bump current-release to v0.12.21 (amendment #144 closed-loop engagement canonical promotion) + F-D1-SNAPSHOT-DRIFT capture`). Build agent walks forward at apply-time per #142 D-PASH.BASELINE-WALK; no `chore(amend-fixup):` commits expected between #144's seal and HEAD.
**Quality bar:** PATCH-class, doc-only sweep; multi-surface fence (`docs/` + `plugins/loam-skills/pyproject.toml` + `README.md`); no behavior change for any production code path; no test changes except one new outcome-altitude assertion test.

---

## §1. Objective / Summary / TL;DR

Land Batch A of the loam fresh-install consistency review findings — five doc-only fixes that close two MAJOR docs-vs-reality drifts (review §7 items 1 + 3) plus three MINOR cosmetics (items 6 + 7 + 8) in a single tiny amendment cycle. The review identified these five as bundle-eligible because none touches code, tests, or other plugins, and each fix's content is unambiguous from the review's Tier-0 evidence.

**Pre-flight Tier-0 verification (this turn — every finding re-checked against canonical source):**

| Review finding | Tier-0 re-check this turn | Verdict |
|---|---|---|
| Item 1 — `docs/install-from-source.md:78` lists `pip install -e ./framework/binary-observation-harness` | `Read` confirms line 78 carries the literal `pip install -e ./framework/binary-observation-harness`; `Bash ls framework/ | grep -i binary` returns no match (directory does not exist); `Bash grep binary-observation-harness install-from-source.txt` returns no match (the canonical install manifest has no such entry). | **CONFIRMED** — finding accurate; fix is one-line deletion. |
| Item 3 — `docs/architecture.md:85-102` Skills + MCP section | `Read` lines 80-110 confirm verbatim: "loam ships no required MCP servers in v0.1.0" (line 84) + "loam does not ship skills directly in v0.1.0" (line 92) + "Dev/SDLC plugin contributes a `start-project` skill that the primary persona can invoke when the intent matches" (lines 93-94). `Bash find plugins/loam-skills/skills -name SKILL.md` returns 20 files. `Bash find plugins/dev-sdlc/skills -name SKILL.md` returns 15 layered SKILLs (NOT 16 as the review claimed — see §10 F1 below for the calibration correction). | **CONFIRMED with calibration note** — fix is rewrite of Skills section; F1 corrects the 16 → 15 count. |
| Item 6 — `plugins/loam-skills/pyproject.toml:8` description says "five SKILL.md packages" | `Read` confirms line 8 carries literal "five SKILL.md packages capturing loam's load-bearing translation patterns (memory-recall, scope-decompose, dispatch-with-gates, onboarding-conversation, session-handoff)". Actual count = 20 per item 3 verification. | **CONFIRMED** — fix is description rewrite. |
| Item 7 — README quickstart doesn't mention onboarding ritual | `Read` README lines 32-50 confirm the quickstart's four steps stop at `claude` invocation; no callout about the interactive 6-question ritual that fires post-`loam init`. `getting-started.md` §4½ does document the ritual (per review §2 row 11). | **CONFIRMED** — fix is one-line addition to step 3 area. |
| Item 8 — README anachronistic parentheticals | `Read` README lines 158-164 confirm `*(authored alongside this README in the v0.1.0 docs lane.)*` on both `docs/architecture.md` (line 160-161) and `docs/getting-started.md` (line 162-164). | **CONFIRMED** — fix is parenthetical removal or rewrite. |

All five findings independently verified at Tier-0 this turn. The one calibration correction (dev-sdlc SKILL count is 15, not 16) is recorded in §10 F1 and does not alter the fix shape — item 3's rewrite states the loam-skills count (20) authoritatively + the dev-sdlc count by re-derivation at build-time, NOT by copying the review's 16 verbatim.

**Operational-objective test (per `feedback_test_against_operational_objective_before_escalating`):** the operational objective is "close five empirically-verified docs-vs-reality drifts in a single tiny doc-only cycle"; each finding's fix shape is implied by the Tier-0 evidence; no critical-call / public-action / financial decision is in scope. **Autonomous build dispatch** is the right next step after this plan-doc + manifest land; no owner escalation needed for the build itself.

**Owner-ratification record (per `feedback_record_owner_ratification_before_dispatch`):**

| msg-ID | ts (UTC) | Ruling |
|---|---|---|
| TG 12002 | 2026-05-22 | Owner ratified the consistency-review dispatch; research artefact captured. |
| (this plan-doc) | 2026-05-22 | Plan-author records the five-finding Batch A bundle + fix shape. Builder dispatch follows after plan + manifest land. |

Owner-ratification of the build itself is the dispatcher's call after this plan-doc commits; the plan-doc + manifest land first (durable surface), then the build dispatches against the recorded artefact per the discipline.

---

## §2. Scope

### In-scope

1. **`docs/install-from-source.md`** — delete line 78 (`pip install -e ./framework/binary-observation-harness`). The component does not exist on disk and is not referenced in `install-from-source.txt`. **AC.BAFI.INSTALL.**
2. **`docs/architecture.md`** — rewrite the Skills section (lines 89-94) to reflect current reality:
   - loam-skills plugin ships 20 SKILLs (memory-recall, scope-decompose, dispatch-with-gates, onboarding-conversation, session-handoff, plus 15 more — the rewrite names the count, not the enumeration, to stay count-stable as the corpus grows);
   - dev-sdlc plugin ships an additional set of layered SKILLs (count derived at build-time from `find plugins/dev-sdlc/skills -name SKILL.md`);
   - both plugins' layered SKILLs are auto-discovered via Claude Code's `.claude/skills/` directory after `loam init` symlinks them at scaffold time (via `_symlink_plugin_skills` in `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py`);
   - the flat-shape `plugins/dev-sdlc/skills/start-project.md` is intentionally NOT auto-symlinked (per `docs/design/layered-skill-architecture.md:194-196`) — the rewrite either omits `start-project` entirely OR states its flat-shape non-discoverability accurately.

   The MCP claim at line 84-87 ("loam ships no required MCP servers in v0.1.0") is **out of scope for Batch A** — the review identified it as a separate stale-framing issue (review §6 row 6) and the fix shape (telegram-interface MCP composition is load-bearing per review §5) needs separate scope ruling. Batch A touches only the Skills section. **AC.BAFI.ARCH.**
3. **`plugins/loam-skills/pyproject.toml`** — rewrite line 8's description field to be count-neutral (e.g., "SKILL.md packages capturing loam's load-bearing translation patterns") OR carry the accurate count (20) without enumerating each SKILL by name. Count-neutral is preferred because it stays correct as the corpus grows. **AC.BAFI.PYPROJ.**
4. **`README.md` quickstart section** — add a one-line callout after step 3 (line 49) noting that an interactive 6-question onboarding ritual fires on first run, with `LOAM_ONBOARDING_SKIP=1` as the skip mechanism. **AC.BAFI.QUICK.**
5. **`README.md` Documentation section** — remove the anachronistic parentheticals `*(authored alongside this README in the v0.1.0 docs lane.)*` on the `docs/architecture.md` link (lines 160-161) AND the `docs/getting-started.md` link (lines 162-164). Replace with substantive descriptors only if the descriptor adds value; otherwise delete the parenthetical entirely. **AC.BAFI.DOCS.**

### Out-of-scope (explicitly NOT in this amendment)

1. **Other findings from the consistency review** — items 2 (STATE.md + release-roadmap backfill), 4 (version-pinned framing sweep), 5 (per-component pyproject.toml version bumps), 9 (architecture.md "v0.1.0" anchoring), 10 (getting-started.md `--from` PyPI claim). Each warrants its own scope; items 2 + 5 specifically need code-aware verification (the `post_publish_backfill` helper's behavior; per-component version-bump sweep test).
2. **Code changes** — no source-code edits land in Batch A. The fixes are pure docs + one pyproject metadata field.
3. **Test changes** — except for one optional outcome-altitude assertion (AC.BAFI.S below); no existing tests altered.
4. **Other plugins** — no `plugins/dev-sdlc/`, `plugins/cron-interface/`, or other plugin edits.
5. **The MCP framing in architecture.md lines 84-87** — flagged for a separate amendment; the telegram-interface MCP composition story needs more scope than Batch A admits.

---

## §3. Sealed-component fence

Batch A touches only documentation + one pyproject metadata field; the changes cross **no production-code component boundaries**. The fence is structured as universal-paths admissions across all components rather than per-component entries, because no component's source tree changes.

**Universal admissions (per amendment #22 ruling #3 — admitted across all components):**

- `docs/` — for items 1 + 2 (install-from-source.md + architecture.md edits) + this plan-doc + manifest archival to `docs/plans/sealed/`.
- `README.md` — for items 7 + 8 (top-level README quickstart + Documentation section).
- `plugins/loam-skills/pyproject.toml` — for item 6 (loam-skills plugin description field).

**Components in fence:** none with per-component seal-test entries — the changes are all under universal admissions. The manifest may need ONE component entry to satisfy the loam-amend tool's structural requirement of ≥1 component (TBD by builder at apply-time — if the tool rejects empty `components:`, use `loam-skills` as the placeholder since its pyproject is touched). **D-BAFI.FENCE-SHAPE** in §14 records the build-time resolution.

**Out of fence (halt-and-surface trigger):**

- Any framework source-code edit (e.g., editing `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py` to reflect the architecture.md rewrite would be code-touching — out of scope).
- Any other plugin's tree.
- Any test file edit except the optional new `test_AC_BAFI_S_post_fix_state.py` for AC.BAFI.S.
- Any version-bump on any pyproject.toml beyond `plugins/loam-skills/pyproject.toml`'s description field (versioning is review item 5, separate amendment).

---

## §4. Acceptance criteria

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.BAFI.INSTALL** | `docs/install-from-source.md` no longer contains the literal line `pip install -e ./framework/binary-observation-harness`. The surrounding Tier A enumeration reads cleanly (no orphaned blank line, no broken tier comment). | `Bash grep -c 'binary-observation-harness' docs/install-from-source.md` returns 0; `Read` confirms the Tier A block reads cleanly post-edit. |
| **AC.BAFI.ARCH** | `docs/architecture.md` Skills section (currently lines 89-94) accurately describes what ships: loam-skills plugin contributes N SKILLs (N derived at build-time from `find plugins/loam-skills/skills -name SKILL.md \| wc -l`); dev-sdlc plugin contributes M layered SKILLs (M derived at build-time from `find plugins/dev-sdlc/skills -mindepth 2 -name SKILL.md \| wc -l`); both auto-discovered via Claude Code's `.claude/skills/` after first-run symlinking by `_symlink_plugin_skills`. The `start-project` SKILL claim is removed OR replaced with a flat-shape non-discoverability note. The MCP claim (lines 84-87) is NOT touched (out of scope). | `Bash grep 'start-project' docs/architecture.md` returns 0 OR the surviving reference is explicitly about flat-shape non-discoverability; `Bash grep -E 'loam does not ship skills directly' docs/architecture.md` returns 0; `Read` confirms the new Skills section names the loam-skills + dev-sdlc count + the `_symlink_plugin_skills` mechanism. |
| **AC.BAFI.PYPROJ** | `plugins/loam-skills/pyproject.toml` line 8 (`description` field) no longer claims "five SKILL.md packages" + no longer enumerates the legacy five-name list. The new description is count-neutral OR carries the accurate count. The package name + version + `requires-python` + dependencies are unchanged. | `Bash grep -E 'five SKILL\|memory-recall.*scope-decompose.*dispatch-with-gates' plugins/loam-skills/pyproject.toml` returns 0; `python -c "import tomllib; print(tomllib.load(open('plugins/loam-skills/pyproject.toml','rb'))['project']['name'])"` returns `loam-plugin-loam-skills` (package metadata still parseable). |
| **AC.BAFI.QUICK** | `README.md` quickstart section (currently lines 32-50) carries a one-line callout after step 3 (`loam init ~/loam-workspace`) noting that an interactive 6-question onboarding ritual fires on first run, with `LOAM_ONBOARDING_SKIP=1` as the skip mechanism. The callout is concise (≤2 lines), grammatically integrated with the surrounding numbered steps, and does NOT renumber the existing 4 steps. | `Bash grep -E 'LOAM_ONBOARDING_SKIP\|onboarding ritual\|6.question' README.md` returns ≥1 match in the quickstart section; `Read` confirms step numbering 1-4 still intact. |
| **AC.BAFI.DOCS** | `README.md` Documentation section (currently lines 155-173) no longer contains the literal `*(authored alongside this README in the v0.1.0 docs lane.)*` on either the `docs/architecture.md` link or the `docs/getting-started.md` link. The link text + URL targets are unchanged; only the parenthetical is removed or replaced. | `Bash grep -c 'authored alongside this README in the v0.1.0 docs lane' README.md` returns 0; `Bash grep -c 'docs/architecture.md' README.md` returns ≥1 (link target preserved); `Bash grep -c 'docs/getting-started.md' README.md` returns ≥1 (same). |
| **AC.BAFI.S** | **Outcome-altitude smoke**: a single post-edit assertion verifies the corrected state of all five files in one production-altitude read pass. Authored as `plugins/loam-skills/tests/test_AC_BAFI_S_post_fix_state.py` (placeholder location — builder may relocate per fence shape ruling at apply-time per D-BAFI.FENCE-SHAPE). The test reads each of the five touched files from the repo root, asserts the corrected content is present + the stale content is absent. No pre-arranged state; production-altitude file-read entry-points only. | Test passes against the post-amendment tree; test FAILS against the pre-amendment tree (RED-on-regression mutation proof — the test would fail if any of the five edits were reverted). |

**Outcome-altitude AC mark:** `AC.BAFI.S` is `outcome-altitude: true` per `feedback_test_outcome_altitude_required` — invokes file-system reads against the actual repo paths with no pre-arranged state; measures the end-state of the five-file corpus across the whole amendment, not per-file mechanics.

**Method-in-AC test passed (per ODD §2.5):** can each AC be satisfied by a method other than the one I have in mind? Yes — AC.BAFI.INSTALL can be satisfied by sed-deleting the line, manually editing, or replacing with a corrected component name; AC.BAFI.ARCH can be satisfied by the proposed rewrite, by a different rewrite that still names the counts + mechanism, or by linking to a separate Skills section in the components doc; AC.BAFI.PYPROJ admits count-neutral OR accurate-count wording; AC.BAFI.QUICK admits any concise callout that names the env var; AC.BAFI.DOCS admits parenthetical deletion OR replacement; AC.BAFI.S admits any test that reads the five files + asserts the corrected state. Method is the builder's call.

---

## §5. Build steps

Method-level guidance only; builder's call per ODD §1.1.

1. **Plan-doc + manifest commit** (this file + its manifest YAML).
2. **Pre-edit verification commit (optional)** — builder may capture the pre-edit grep counts for each AC's stale-content marker (`binary-observation-harness`, `five SKILL`, `start-project` in architecture.md, `LOAM_ONBOARDING_SKIP` absence in README, `v0.1.0 docs lane` count = 2) to a build-side scratch file. Optional because the AC verifications are deterministic from the post-edit state alone.
3. **Per-AC source edits** — builder may group into a single source-edit commit OR per-AC commits. Per-AC is cleaner for the §14 register but a single commit is acceptable for ≤5 small edits.
4. **AC.BAFI.S test authoring** — `tests/test_AC_BAFI_S_post_fix_state.py` at the location resolved by D-BAFI.FENCE-SHAPE. Test reads the five files and asserts corrected content present + stale content absent.
5. **`loam amend apply`** (auto-commit).
6. **Component test runs** — `pytest <fence-component>/tests/` for whatever component winds up holding the AC.BAFI.S test + a re-run of any test suite affected by the fence (likely just the holder component's seal-test).
7. **`loam amend seal`** — deterministic seal commit; T1.4 archives plan-doc + manifest to `docs/plans/sealed/` per the post-#134 plan_archive.py integration (#143 Strategy 1 match on full slug `loam-doc-consistency-batch-a`).
8. **§14 backfill** — auto-embedded by `loam amend seal`'s `_finalize` step per amendment #141's decoupled path.

---

## §6. Halt triggers

The build agent **must halt and surface** on:

1. **Pre-edit grep reveals a finding's stale-content marker is NOT present** at the line/file the plan names (e.g., `binary-observation-harness` is already gone from line 78; or `five SKILL` is already gone from pyproject.toml line 8) — indicates someone landed a fix between the review and this amendment; halt and surface for re-scope.
2. **A finding's fix turns out to require more than the plan named** — e.g., item 1's deletion breaks the surrounding Tier A enumeration's tier comment; item 3's Skills rewrite cannot be cleanly bounded to lines 89-94 without touching the MCP section (lines 84-87); item 7's callout cannot fit in ≤2 lines without renumbering. Halt and surface for ruling on scope expansion vs decomposition into a Batch A1 + A2.
3. **The `_symlink_plugin_skills` symbol path drifted** (e.g., the function was renamed or moved after the review's verification) — the architecture.md rewrite cites this symbol path; halt if the citation would be stale.
4. **A SKILL count drift** between this plan's pre-flight numbers (loam-skills = 20, dev-sdlc = 15) and the build-time `find` numbers — re-derive the counts at build-time per AC.BAFI.ARCH verification rather than trusting plan-time numbers (per `feedback_specific_claims_verified_or_marked_guess`); halt if the build-time count differs by >2 from the pre-flight number (signals a recent unsealed change).
5. **The AC.BAFI.S test cannot be placed inside any sealed-component fence cleanly** — fall back to placing it at a universal `tests/` location admitted by the manifest; halt only if no placement satisfies the fence.
6. **The fence requires a per-component seal-test entry but the tool rejects the universal-only shape** — surface for fence-shape ruling per D-BAFI.FENCE-SHAPE.

---

## §7. Ship shape

Single PATCH-class amendment, five AC-family edits + one outcome-altitude test, one apply/seal cycle. No sub-amendment split — each AC's outcome is strictly tighter than the parent (single-file scope), and splitting would add coordination overhead without tightening any AC further (per Lens 5 stopping criterion).

**Estimated AI-time (per `feedback_duration_estimation_rubric`):** 15-25 min midpoint ~20 min. Drivers: five small edits (≤2-3 lines each except item 3 which is ~6-8 lines), one new test file (~30-50 lines), apply + seal cycle. AC.BAFI.S is the dominant cost driver because it requires reading + asserting against five files.

---

## §8. (reserved — risks / cross-references)

---

## §9. Bookkeeping

- **STATE.md** update at seal time: amendment `loam-doc-consistency-batch-a` sealed; review §7 items 1, 3, 6, 7, 8 RESOLVED.
- **`workspace/.scratch/claude-output/loam-fresh-install-consistency-review-2026-05-23.md`** (the parent research artefact) — no edit; the artefact stays as-authored as the durable surface this amendment closed against.
- **Review §7 items 2, 4, 5, 9, 10** remain open as separate-amendment candidates; surface to FIDRAFT or next-batch dispatch per owner's call.

---

## §10. Halt-and-surface findings (raised at plan-authoring time)

These are F2 Ruthless Feedback notes from the plan-authoring pass. Each surfaces a disagreement, evidence, and an alternative.

### F1. Calibration correction: dev-sdlc layered-SKILL count is 15, not 16.

- **Claim:** Dispatch brief stated "dev-sdlc plugin ships 16 additional SKILLs". My Tier-0 re-check this turn (`Bash find plugins/dev-sdlc/skills -mindepth 2 -name SKILL.md | wc -l`) returns **15**.
- **Evidence:** Enumeration: audit-finding-triage, component-scaffold-author, dispatch-brief-authoring, fidraft-capture, front-load-principle-walk, graceful-fallthrough-with-detection, hook-violation-recovery, loam-amend-cycle, loam-amend-status-quick, odd-test-altitude-discipline, plan-before-code-author, plan-docs-author, seal-narrative-writer, skill-promotion-review, subagent-routing. That's 15 layered SKILLs. The flat-shape `start-project.md` is a 16th SKILL by file count but is NOT auto-symlinked per `docs/design/layered-skill-architecture.md:194-196`, so it does NOT contribute to the discoverable-in-fresh-workspace count.
- **Alternative:**
  - **Option 1 (recommended):** AC.BAFI.ARCH derives the counts at build-time via `find` (per the AC's verification clause), not by copying plan-time numbers. The plan-time numbers (loam-skills=20, dev-sdlc=15) are calibration anchors, not load-bearing values.
  - **Option 2:** Hard-code the counts in the plan-doc + match-at-build-time. Brittle if a SKILL lands between plan and build.
- **Decision (autonomous per operational-objective test):** Option 1. The objective is "accurate Skills section in architecture.md"; deriving counts at build-time IS accuracy. The plan-time count is a sanity-check anchor, not a contract.

### F2. The `start-project.md` SKILL exists — review framing "no `start-project` SKILL exists" is overstated.

- **Claim:** Dispatch brief stated "no `start-project` SKILL exists" (in the item 3 description). My Tier-0 re-check this turn (`Bash grep -rn "start-project" plugins/dev-sdlc/skills/`) confirms `plugins/dev-sdlc/skills/start-project.md` IS present with valid frontmatter (lines 1-4).
- **Evidence:** The file is a flat-shape SKILL (sibling to the layered-SKILL subdirectories). `docs/design/layered-skill-architecture.md:194-196` explicitly states flat-shape SKILLs are out-of-fence for auto-symlinking, so the file exists but is NOT discoverable in a fresh workspace. The architecture.md claim "the primary persona can invoke" it is therefore **practically false** (the persona can't invoke it from a fresh workspace) but **literally true** (the file exists at the cited path).
- **Alternative:**
  - **Option 1 (recommended):** AC.BAFI.ARCH rewrite removes the `start-project` claim entirely. The Skills section names what IS discoverable (loam-skills + dev-sdlc layered SKILLs); the flat-shape file is an architectural-decision detail that doesn't belong in user-facing architecture docs.
  - **Option 2:** AC.BAFI.ARCH rewrite keeps a `start-project` reference but annotates it as "flat-shape; not auto-symlinked; documented separately at docs/design/layered-skill-architecture.md". Loads more cognitive surface on the user for marginal informational value.
  - **Option 3:** Out-of-scope for Batch A — the flat-vs-layered distinction is its own scope; the Skills section can be left ambiguous until that's resolved. Loses the fix value.
- **Decision (autonomous):** Option 1. The dispatching review's framing was directionally correct (the user-facing claim is wrong); the precise wording ("no SKILL exists") is overstated but the corrective action is the same. **Recommendation:** ratify Option 1 — Skills section names loam-skills + dev-sdlc counts + the symlink mechanism; no mention of `start-project`.

### F3. The MCP claim at architecture.md lines 84-87 is in the same Skills+MCP block — clean fence on the rewrite needs care.

- **Claim:** The Skills section (lines 89-94) lives immediately below the MCP section (lines 82-87). Both are stale-framing per the review (§6 row 6 flags the MCP claim too). The line ranges are adjacent.
- **Evidence:** `Read docs/architecture.md` lines 80-102 confirms the two sections are sibling-headed (`### MCP` at line 82, `### Skills` at line 89). Editing only the Skills section is mechanically straightforward (heading boundary is unambiguous), but a reader will see the stale MCP claim immediately above the fixed Skills claim — visually inconsistent.
- **Alternative:**
  - **Option 1 (recommended):** Batch A fixes only Skills (AC.BAFI.ARCH bounded to lines 89-94); MCP fix lands in a separate amendment that handles the telegram-interface MCP composition story properly.
  - **Option 2:** Expand Batch A to include MCP fix. Cost: review §7 listed MCP as item 4 in the v0.1.0 framing sweep (line 122 of the review), not as a Batch A item. Expanding here re-scopes the bundle and breaks the "≤30 min, doc-only, no surprises" contract that justified Batch A's existence.
  - **Option 3:** Leave both. Loses Batch A's value.
- **Decision (autonomous):** Option 1. The operational objective is "land the five Batch A findings"; expanding to include MCP is out-of-scope drift. The visual inconsistency is acknowledged + surfaced; a follow-up amendment closes it. **Recommendation:** ratify Option 1 — Batch A holds the line at Skills-only.

### F4. AC.BAFI.S test placement is fence-dependent.

- **Claim:** No production-code component is touched. The AC.BAFI.S test needs a home; placing it in any sealed component creates a fence-entry for that component just to host the test.
- **Evidence:** The `loam-amend apply` tool's manifest schema (per `framework/tools/loam/README.md` + the manifest exemplars at amendment #143) admits `components: []` only if the manifest still has a fence-shape-rule satisfied. Per #137's pattern, sometimes the right answer is a single placeholder component whose seal-test is the only one to run.
- **Alternative:**
  - **Option 1 (recommended at apply-time):** Place AC.BAFI.S in `plugins/loam-skills/tests/` because Batch A already touches `plugins/loam-skills/pyproject.toml`. The fence entry for loam-skills exists naturally for item 6. Single component fence, no extra entries.
  - **Option 2:** Place at a universal `tests/` location at repo root (e.g., `tests/test_AC_BAFI_S_post_fix_state.py`) — admitted by universal_paths. Cleaner conceptually but requires the loam-amend tool to admit `tests/` as a universal prefix.
  - **Option 3:** Skip AC.BAFI.S entirely; rely on per-AC manual greps. Violates `feedback_test_outcome_altitude_required` (the corpus rule requires ≥1 outcome-altitude AC per AC set, verified by a test).
- **Decision (autonomous):** Option 1 is the build-time recommendation; D-BAFI.FENCE-SHAPE in §14 records the apply-time resolution. **Recommendation:** ratify Option 1.

### F5. The five items are tightly bundle-eligible per the review's own claim.

- **Claim:** Review §7 operational note states "items 1, 3, 6, 7, 8 can land in one tiny doc-only amendment (≤30 min)". My pre-flight verification this turn confirms the bundle holds: no item's fix requires another item's fix as predecessor; no item touches another item's surface; the five touched paths are disjoint (`docs/install-from-source.md`, `docs/architecture.md`, `plugins/loam-skills/pyproject.toml`, `README.md` quickstart, `README.md` Documentation — the last two share a file but disjoint sections).
- **Evidence:** The five-file fence + the per-AC verification's structural orthogonality.
- **Alternative:** None — bundle as designed.

### F6. No method-in-AC trap (per ODD §2.5).

- **Test passed:** Per §4 table. Each AC names the OUTCOME (corrected file state) without prescribing the EDIT METHOD (sed vs manual vs IDE refactor). AC.BAFI.S names the verification mechanism (file-read assertion at production altitude) because that IS the outcome (the corpus has the corrected state) — the test's existence is the AC's surface, not method-in-AC.

### F7. Lens 5 — no sub-amendment split.

- **Claim:** Five ACs inside one amendment is sufficient decomposition.
- **Evidence:** Each AC's outcome is strictly tighter than the parent (single-file scope). Splitting into per-AC sub-amendments would add 4-5 sub-amendment manifests + plan-docs without tightening any AC further. Stopping criterion met.

---

## §14. Method-decision register

> Populated at build time by the build agent; back-filled with seal SHAs by `loam amend seal` per amendment #141's decoupled path.

### D-BAFI.AC-LADDER — 5 fix ACs + 1 outcome-altitude smoke.

- **Decision:** AC.BAFI.{INSTALL, ARCH, PYPROJ, QUICK, DOCS} cover the five review items; AC.BAFI.S is the outcome-altitude smoke per the corpus rule.
- **Rationale:** One AC per review item preserves the review's structure + makes per-item green/red attribution clean. AC.BAFI.S satisfies `feedback_test_outcome_altitude_required` by reading the actual post-amendment file state at production altitude.
- **Recommendation:** Ratified inline by this plan-doc.

### D-BAFI.FENCE-SHAPE — Universal-paths-only fence shape.

- **Decision:** Manifest uses universal_paths admissions (`docs/`, `README.md`, `plugins/loam-skills/pyproject.toml`) rather than per-component seal-test entries. If `loam amend apply` requires ≥1 component entry, use `loam-skills` as the placeholder (the only component whose tree is touched non-document-only via pyproject.toml).
- **Rationale:** No production-code component is touched. Forcing a multi-component fence entry for each universal admission inflates the manifest without enforcement value.
- **Recommendation:** Build-time resolution per F4 above. **Owner ruling needed:** none — recommendation IS the decision per `feedback_test_against_operational_objective_before_escalating`.

### D-BAFI.ARCH-SCOPE — Skills section only; MCP section deferred.

- **Decision:** AC.BAFI.ARCH bounded to lines 89-94 (Skills section); the MCP claim at lines 84-87 is out-of-scope for Batch A.
- **Rationale:** Per F3. The MCP fix needs separate scope ruling on the telegram-interface composition story.
- **Recommendation:** Ratify. MCP fix tracked as a separate amendment candidate.

### D-BAFI.START-PROJECT — Remove `start-project` claim entirely from architecture.md.

- **Decision:** AC.BAFI.ARCH rewrite removes the `start-project` reference (Option 1 per F2). The flat-vs-layered distinction is an architectural detail that doesn't belong in user-facing architecture docs.
- **Rationale:** Per F2. The dispatching review's framing was directionally correct; the practical claim "the primary persona can invoke" is false because the flat-shape SKILL is not auto-symlinked.
- **Recommendation:** Ratify.

### D-BAFI.COUNT-DERIVATION — SKILL counts derived at build-time, not copied from plan-time.

- **Decision:** AC.BAFI.ARCH verification clause derives the loam-skills + dev-sdlc layered-SKILL counts via `find` at build-time. The plan-time numbers (20 + 15) are calibration anchors, not contract values.
- **Rationale:** Per F1. Per `feedback_specific_claims_verified_or_marked_guess`, counts re-derived at the actual use-point.
- **Recommendation:** Ratify.

### D-BAFI.PYPROJ-NEUTRAL — Count-neutral description preferred over hard-coded count.

- **Decision:** AC.BAFI.PYPROJ rewrite prefers count-neutral wording (e.g., "SKILL.md packages capturing loam's load-bearing translation patterns") over a literal count ("20 SKILL.md packages") because the corpus grows.
- **Rationale:** Future SKILL additions don't re-stale the description.
- **Recommendation:** Ratify.

### D-BAFI.RESERVED — additional method decisions named at build-time.

- (build-agent backfill — slot reserved for any decisions the builder makes during edit that the plan didn't pre-resolve)

---

### Commit SHAs

- Amendment commit: `d5b022fd4439bad4afecb3f18e6f57188c4aaddb` —
  `docs(plans): author A-PROMOTE-START-PROJECT plan-doc + manifest`
- Seal commit: `6b82a620a804f956c6bb075b6fa10333e4df720f` —
  `chore(seals): Doc-only consistency fixes (Batch A) — closes 5 findings from the loam-fresh-install-consistency-review-2026-05-23 research artefact (review §7 items 1, 3, 6, 7, 8) in a single tiny doc-only PATCH amendment.`
## §15. Backwards-compat verification

- **No production-code behavior changes.** Five doc-only edits + one pyproject metadata field + one new test file.
- **All existing component tests must still pass post-edit.** The only fence-touched component is loam-skills (via pyproject.toml description field); `pytest plugins/loam-skills/tests/` must stay green.
- **README link targets are preserved** — AC.BAFI.DOCS removes parentheticals but does NOT alter the `docs/architecture.md` or `docs/getting-started.md` link URLs.
- **`install-from-source.txt` is unchanged** — AC.BAFI.INSTALL deletes a line from `docs/install-from-source.md` (the prose guide), not from the canonical install manifest `install-from-source.txt` at repo root. The two files are different surfaces; the canonical manifest has no `binary-observation-harness` entry already (pre-flight verified this turn).

---

## §16. Halt-and-surface findings (build-agent backfill — reserved for build-time additions)

- (build-agent populates if any in-flight halt fires during the build)

---

## §17. Provenance trail

- Parent research artefact — `workspace/.scratch/claude-output/loam-fresh-install-consistency-review-2026-05-23.md` (the dispatching review by `loam-researcher`).
- Owner trigger — Telegram 12002 (ratified the consistency-review dispatch).
- Pre-flight Tier-0 verification — this turn, per §1 table (each of the five findings re-checked against canonical source).
- Plan-doc convention — `plugins/dev-sdlc/docs/conventions/plan-docs.md`.
- Exemplar canonical-shape — `docs/plans/sealed/amendment-137-legacy-pos-amend-name-docs-corpus-sweep.md` (most-recent doc-only sealed amendment with `outcome-altitude: true` AC; same shape pattern).
- Layered-skill out-of-fence ruling for flat-shape SKILLs — `docs/design/layered-skill-architecture.md:194-196`.
- Symlink mechanism cited in AC.BAFI.ARCH — `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py:1224` (`_symlink_plugin_skills` function definition).
- Outcome-altitude AC rule — `feedback_test_outcome_altitude_required`.
- Scope-descriptive AC ID convention — `feedback_scope_descriptive_ac_ids` (AC.BAFI.* uses Batch-A-Fresh-Install abbreviation, not version-packed).
- Verified-before-claim discipline — `feedback_specific_claims_verified_or_marked_guess` (drove the per-finding Tier-0 re-check + F1 calibration correction + F2 framing correction).
- Operational-objective autonomy test — `feedback_test_against_operational_objective_before_escalating` (drove the autonomous-build-dispatch ruling without owner escalation).

Doc-only consistency fixes (Batch A) — closes 5 findings from
the loam-fresh-install-consistency-review-2026-05-23 research
artefact (review §7 items 1, 3, 6, 7, 8) in one tiny PATCH
amendment.

AC.BAFI.INSTALL — docs/install-from-source.md line 78 deletion
(binary-observation-harness component does not exist on disk;
not in install-from-source.txt). AC.BAFI.ARCH — docs/architecture
.md Skills section rewrite: accurate loam-skills + dev-sdlc
layered-SKILL counts (derived at build-time); start-project
reference removed (flat-shape not auto-symlinked per layered-
skill-architecture.md:194-196); _symlink_plugin_skills mechanism
cited; MCP section NOT touched (separate amendment). AC.BAFI.
PYPROJ — plugins/loam-skills/pyproject.toml description rewrite
from hardcoded "five SKILL.md packages" to count-neutral wording
(corpus grows). AC.BAFI.QUICK — README.md quickstart one-line
callout after step 3 about the 6-question onboarding ritual +
LOAM_ONBOARDING_SKIP=1 skip env. AC.BAFI.DOCS — README.md
Documentation section anachronistic v0.1.0-docs-lane
parentheticals removed from architecture.md + getting-started.md
links (URLs preserved). AC.BAFI.S — outcome-altitude smoke
reads the five files + asserts corrected state present, stale
absent (RED-on-regression mutation proof).

Five plan-author halt-and-surface findings (plan §10) surfaced
+ autonomous-decision-recorded per `feedback_test_against_
operational_objective_before_escalating`: F1 (dev-sdlc count
16 → 15 calibration correction; counts derived at build-time
per D-BAFI.COUNT-DERIVATION); F2 (start-project SKILL exists
but not auto-symlinked; architecture.md reference removed per
D-BAFI.START-PROJECT); F3 (MCP section deferred to separate
amendment per D-BAFI.ARCH-SCOPE); F4 (AC.BAFI.S placement at
plugins/loam-skills/tests/ per D-BAFI.FENCE-SHAPE); F5 (bundle
holds — five-file fence is disjoint).

Cosmetic + accuracy hygiene; no behavior change for any
production code path. Composes with amendment #137 (same
structural shape — doc-only sweep with outcome-altitude smoke).
Closes review §7 items 1, 3, 6, 7, 8; leaves items 2, 4, 5, 9,
10 as separate-amendment candidates per plan §9.
