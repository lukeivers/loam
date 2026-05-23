# loam-skills-start-project-discoverable — Promote `start-project` SKILL to discoverable subdirectory shape

**Status:** plan-doc, plan-before-code. Authored 2026-05-22 by `loam-plan-author` agent (background dispatch).
**Working directory:** `/Users/lukeivers/loam/`.
**Parent capture:** loam-fresh-install-consistency-review-2026-05-23 (research artefact at `pos3/workspace/.scratch/claude-output/loam-fresh-install-consistency-review-2026-05-23.md`).
**Predecessor (load-bearing):** Batch A apply commit `140767c` (feat(amendment-145): Batch A doc-only consistency fixes), pending seal. This amendment LANDS AFTER Batch A's seal completes — the architecture.md edit restoration here would conflict with an unsealed Batch A apply, so the build agent verifies Batch A is sealed before applying.
**Working baseline candidate:** the seal commit produced by Batch A's `loam amend seal` (TBD; walked at apply-time per #142 D-PASH.BASELINE-WALK).
**Quality bar:** PATCH-class corrective amendment; load-bearing structural relocation (`git mv` of one file) + one outcome-altitude AC + four supporting ACs; restores a deleted architecture.md reference with refined wording.

---

## §1. Objective / Summary / TL;DR

The `start-project` SKILL has been silently undiscoverable since v0.1.0 ship. AC.OSS-M6.9 text explicitly requires "discoverable + invocable" but the test shipped at v0.1.0 only verified file-existence + frontmatter + a manual reader-fall-through simulation — it never verified the SKILL actually reaches `<workspace>/.claude/skills/` in a fresh workspace. When the auto-symlinker `_symlink_plugin_skills` shipped at v0.1.7 AC.LAYERED.2, it walked per-directory shape only; flat-file `<plugin>/skills/<name>.md` was explicitly out-of-fence. The flat-shape start-project SKILL silently failed to discover from that point forward, and nobody noticed because no outcome-altitude test existed.

Batch A (amendment #145, apply commit `140767c` pending seal) accepted the silent-undiscoverable state and DELETED the `start-project` reference from `docs/architecture.md` (per D-BAFI.START-PROJECT cited at the apply-commit body). Luke's F2: why isn't FIXING the SKILL one of the options?

This amendment fixes it. Five-item scope:

1. **`git mv plugins/dev-sdlc/skills/start-project.md plugins/dev-sdlc/skills/start-project/SKILL.md`** — promotes to the subdirectory shape the auto-symlinker walks.
2. **Update `test_AC_OSS_M6_9_start_project_skill_shipped.py`** — repoint `SKILL_PATH` at the new location; relax frontmatter assertion that asserts `name == "start-project"` (the subdirectory name now provides identity per the Anthropic spec).
3. **Add outcome-altitude AC + test for actual discoverability** — invoke `_symlink_plugin_skills` against a synthetic workspace where `plugins/dev-sdlc/skills/start-project/SKILL.md` is staged; assert the resulting `<workspace>/.claude/skills/start-project/SKILL.md` symlink exists + resolves. Closes the gap AC.OSS-M6.9's text always required but the original test never delivered.
4. **Restore the `docs/architecture.md` reference Batch A deleted** — refined wording naming the SKILL by its now-discoverable shape.
5. **Update collateral references** — five additional sites hard-code or describe the flat-shape (`test_AC_LAYERED_2_skill_symlink_registration.py`, `plugins/dev-sdlc/README.md`, two DSDLC test docstrings, `docs/design/layered-skill-architecture.md`). Each gets a minimal touch to reflect the now-correct subdirectory shape (or to retain flat-shape as a hypothetical example separated from the real-tree claim).

Net effect after Batch A seal + this seal: the architecture.md reference is preserved-with-correction (Batch A deleted → this restores with refined wording); the SKILL becomes auto-symlinked + discoverable in fresh workspaces; the contract AC.OSS-M6.9 always claimed is finally enforced at outcome-altitude; collateral docs reflect reality.

---

## §2. Predecessors / context

**Sealed predecessors (load-bearing):**
- `21c1ddf` — Batch A plan-doc + manifest commit.
- `140767c` — Batch A apply commit (pending seal at plan-authoring time; this amendment's apply MUST wait for Batch A's seal).
- Whatever Batch A's seal SHA turns out to be — this amendment's `baseline:` points there.

**Conceptual predecessors:**
- `oss-v0-1-0-publish-dev-sdlc-plugin.md` (AC.OSS-M6.9 origin; sealed at v0.1.0 ship). Text: "discoverable + invocable." Test downsized: file-existence + frontmatter + manual reader-fall-through simulation. Verified Tier-0 by reading the original plan-doc §4 AC.OSS-M6.9 entry (`docs/plans/oss-v0-1-0-publish-dev-sdlc-plugin.md:246-254`).
- `v0-1-7-cycle-3-...` (AC.LAYERED.{2,3,4} symlinker shipped at `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py:1224-1310`). Per-directory walk only; flat-file explicitly skipped at line 1264.
- `loam-fresh-install-consistency-review-2026-05-23.md` — surfaced the broken contract (review §7 item 3).

---

## §3. Scope

### In scope (sealed-component fence)

- `plugins/dev-sdlc/` (load-bearing):
  - `plugins/dev-sdlc/skills/start-project.md` — DELETE (via `git mv`).
  - `plugins/dev-sdlc/skills/start-project/SKILL.md` — NEW (moved from above).
  - `plugins/dev-sdlc/tests/test_AC_OSS_M6_9_start_project_skill_shipped.py` — UPDATE (repoint SKILL_PATH + tighten ACs).
  - `plugins/dev-sdlc/tests/test_AC_SPDISC_DSCV_start_project_auto_symlinked.py` — NEW (outcome-altitude discoverability test).
  - `plugins/dev-sdlc/README.md` — UPDATE (line 26 reference shape).
  - `plugins/dev-sdlc/tests/test_AC_SKILLS_DSDLC1_7_all_six_skills_discovered.py` — UPDATE (docstring line 6).
  - `plugins/dev-sdlc/tests/test_AC_SKILLS_DSDLC2_7_all_twelve_skills_discovered.py` — UPDATE (docstring line 8).
- `framework/workspace-bootstrap/`:
  - `framework/workspace-bootstrap/tests/test_AC_LAYERED_2_skill_symlink_registration.py` — UPDATE (lines 206-240; the skip-flat-file test mirrors the real-tree shape via a comment; the test's logic stays valid as a hypothetical, but the comment naming `start-project.md` as the real-tree example becomes false — comment update).
- Universal admissions (per amendment #22 ruling #3):
  - `docs/architecture.md` — RESTORE the start-project reference Batch A deleted (with refined wording naming subdirectory shape + auto-symlinker mechanism).
  - `docs/design/layered-skill-architecture.md` — UPDATE line 196 (the flat-file out-of-fence example using `plugins/dev-sdlc/skills/start-project.md` is no longer real; rewrite as a hypothetical or use a different example).
  - `docs/plans/loam-skills-start-project-discoverable.md` (this plan-doc).
  - `docs/plans/loam-skills-start-project-discoverable.manifest.yaml` (this amendment's manifest).

### Out of scope (deferred)

- **Touching the SKILL body content.** The body at `plugins/dev-sdlc/skills/start-project.md` lines 6-60 stays byte-identical (only the file location moves). Any wording revision is a separate amendment.
- **Migrating other flat-shape skills.** No flat-shape skills exist in canonical loam outside `start-project.md` (verified via grep this turn). Hypothetical future flat-shape skills are out of fence.
- **Revising AC.LAYERED.2's skip-flat-file test logic.** The test's behaviour (flat-file skipped) is correct per Anthropic's per-directory discovery spec; the test stays. Only the comment example changes.
- **Re-running the layered-skill-architecture.md design doc for currency.** Beyond the one-line correction at line 196, the doc stays as-is; broader-currency review is a separate dispatch if surfaced.
- **MCP section in architecture.md.** Per Batch A's D-BAFI.ARCH-SCOPE (separate amendment).
- **Tightening AC.OSS-M6.9's text language.** The text "discoverable + invocable" is correct and stays; only the verification AC ladder tightens. Per `feedback_loose_AC_text_fix_AC_not_implementation`, the test was loose (file-existence only, not outcome-altitude); fixing the test, not the AC text, is the right discipline.

---

## §4. Acceptance criteria

### AC.SPDISC.* family — start-project promotion + discoverability

| AC ID | Outcome (deterministic, single-test-per-criterion) | Verification |
|---|---|---|
| **AC.SPDISC.MV** | `plugins/dev-sdlc/skills/start-project.md` does NOT exist; `plugins/dev-sdlc/skills/start-project/SKILL.md` exists with byte-identical body to the previous flat-file content (modulo the YAML frontmatter which may have the redundant `name:` field stripped). | Test: `test_AC_SPDISC_MV_flat_shape_removed_subdir_present.py` asserts `not (skills/start-project.md).exists()` AND `(skills/start-project/SKILL.md).is_file()` AND body section headers (`## What this skill does`, `## Underlying mechanics`, `## Operator surface`, `## Composition`) are preserved verbatim. |
| **AC.SPDISC.DSCV** | `_symlink_plugin_skills` walked against a synthetic workspace staging `plugins/dev-sdlc/skills/start-project/SKILL.md` produces a symlink at `<workspace>/.claude/skills/start-project` pointing at the absolute path of the plugin's skill directory; the resulting `<workspace>/.claude/skills/start-project/SKILL.md` is a readable file (resolves through the symlink). **OUTCOME-ALTITUDE per `feedback_test_outcome_altitude_required`.** | Test: `test_AC_SPDISC_DSCV_start_project_auto_symlinked.py` constructs a tmpfs workspace with the canonical plugins/dev-sdlc/skills/ tree staged (NOT mocked — actually copies the staged SKILL.md from the canonical tree), invokes the production `_symlink_plugin_skills(workspace)` entry-point with NO pre-arranged `.claude/skills/` state, asserts the symlink exists + the SKILL.md is readable through it + `tuple` return value contains `<workspace>/.claude/skills/start-project`. RED-on-mutation: temporarily revert the `git mv` and assert the test fails. |
| **AC.SPDISC.OSSM69** | The renamed file (now at subdirectory shape) still passes the original AC.OSS-M6.9 contract: frontmatter parses, `description` field present + non-empty + names "Dev/SDLC", body names `start_project` API + `loam project` operator surface. | Test (updated): `test_AC_OSS_M6_9_start_project_skill_shipped.py` with `SKILL_PATH = ... / "skills" / "start-project" / "SKILL.md"`. The `frontmatter.get("name") == "start-project"` assertion either (a) stays if the `name:` field is retained for v0.1.0 contract continuity, OR (b) is removed if D-SPDISC.NAME-FIELD rules to drop the redundant field. The reader-fall-through test (`test_skill_resolves_via_workspace_root_path_lookup`) updates its `rel` constant to the new subdirectory path. |
| **AC.SPDISC.ARCH** | `docs/architecture.md` `### Skills` section names the `start-project` SKILL by name as the Dev/SDLC plugin's user-facing intent-routing surface, AND names the auto-symlink discovery mechanism that makes it reachable in fresh workspaces (parallel to the existing wording for `loam-skills` and `dev-sdlc` SKILL bundles). | Test: `test_AC_SPDISC_ARCH_start_project_referenced.py` reads `docs/architecture.md`; asserts substring `start-project` is present in the Skills section AND `Dev/SDLC` is named alongside it AND the auto-symlink mechanism (`_symlink_plugin_skills` or equivalent phrasing) is referenced. |
| **AC.SPDISC.COLLAT** | Collateral references reflect subdirectory shape: (a) `plugins/dev-sdlc/README.md` line 26 region names `plugins/dev-sdlc/skills/start-project/SKILL.md` (or equivalent subdirectory-shape phrasing); (b) `docs/design/layered-skill-architecture.md` line 196 region no longer cites `plugins/dev-sdlc/skills/start-project.md` as the real-tree flat-shape example; (c) the two DSDLC test docstrings (`test_AC_SKILLS_DSDLC1_7_...py:6`, `test_AC_SKILLS_DSDLC2_7_...py:8`) no longer assert "in addition to the flat-file `start-project.md`"; (d) `test_AC_LAYERED_2_skill_symlink_registration.py:213` docstring comment "Mirrors plugins/dev-sdlc/skills/start-project.md (real-tree shape that exists today)" updates to reflect that flat-shape no longer exists in the real tree (the test logic — flat-file IS skipped — remains valid as a hypothetical contract). | Test: `test_AC_SPDISC_COLLAT_collateral_refs_updated.py` reads each of the four files; asserts each (a)/(b)/(c)/(d) condition with the specific substring expectations encoded. RED-on-mutation: revert any one collateral and assert that test case fails. |
| **AC.SPDISC.S** | End-to-end: a fresh workspace produced by `run_first_run_scaffold` (or the moral equivalent invoked through the canonical `loam init` path) carries `<workspace>/.claude/skills/start-project/SKILL.md` reachable as a normal file (symlink-resolved). | Smoke test: `test_AC_SPDISC_S_fresh_workspace_discoverability.py` invokes the production fresh-scaffold entry-point against a tmpfs workspace, asserts the SKILL surfaces. **OUTCOME-ALTITUDE** (no pre-arranged `.claude/skills/` state, production entry-point invoked, real `_symlink_plugin_skills` walk). |

### AC ladder-up (per §4 of the plan-docs convention)

- AC.SPDISC.* → AC.OSS-M6.9 (the v0.1.0 contract being honoured) → AC.OSS.6 (Claude-leverage surface per the OSS publish master plan) → AC.PO.1 (translation-burden — the SKILL is intent-routing for first-click users; broken discoverability IS unmet translation-burden reduction) + AC.PO.2 (harness toolkit — the SKILL is one of the toolkit primitives the persona invokes).

---

## §5. Sealed-component fence

Single-cycle, two-component fence:

- **`plugins/dev-sdlc/`** — load-bearing component (the SKILL move, the updated AC.OSS-M6.9 test, two new tests, README + two test docstrings).
- **`framework/workspace-bootstrap/`** — secondary (one test docstring comment update at `test_AC_LAYERED_2_skill_symlink_registration.py`).

Universal admissions: `docs/architecture.md`, `docs/design/layered-skill-architecture.md`, `docs/plans/`.

---

## §6. Halt triggers (in-flight)

- **WD drifts** → halt + surface.
- **Batch A not sealed at apply-time** → halt; do NOT apply until Batch A's seal commit lands. Architecture.md edits will conflict with an unsealed Batch A apply.
- **Existing SKILL body content is non-byte-identical post-move** (modulo the optional `name:` frontmatter field per D-SPDISC.NAME-FIELD) → halt; the move should be pure relocation.
- **`_symlink_plugin_skills` mechanism deviates from §10 D-SPDISC.MECHANISM expectation** (e.g., walks a different path; requires plugin metadata declaration) → halt + RF.
- **Cross-plugin name collision** — if `start-project` somehow exists in any other plugin's `skills/` (verified via grep this turn: no other matches), `_symlink_plugin_skills` will raise `PluginSkillCollisionError`. Halt + surface.
- **AC.SPDISC.DSCV test fails RED-on-mutation** (reverting the `git mv` doesn't break the test) → halt; the test is not at outcome-altitude per `feedback_test_outcome_altitude_required`.
- **Additional hard-coded flat-shape references discovered at build-time** (beyond the five named in §3) → halt + surface; scope might need to widen.
- **The SKILL's frontmatter has any property that requires per-directory shape to differ from current flat-file content** (e.g., `allowed-tools` field that depends on subdirectory companion files) → halt + RF (the current frontmatter has only `name` + `description`; no companion-file dependencies; verified Tier-0).

---

## §7. Ship shape (single-cycle commit ladder)

1. Plan-doc + manifest commit (this file + the manifest YAML, single commit).
2. Source-edit commit: `git mv` the SKILL file + update tests + README + design doc + architecture.md.
3. `loam amend apply` auto-commit.
4. `loam amend seal` deterministic seal commit.

Single cycle; single component-pair fence; no sub-amendment ladder.

---

## §8. Backwards-compat verification

Tests that MUST still pass post-amendment:

- All `plugins/dev-sdlc/tests/test_AC_SKILLS_DSDLC{1,2}_7_*` SKILL bundle tests (existing 15-SKILL bundle is independent of start-project; the start-project SKILL is at the plugin's top-level `skills/` but NOT in the EXPECTED_SKILLS list of either DSDLC test). However: post-promotion to subdirectory shape, the `test_all_twelve_dev_sdlc_skills_discovered` assertion at `test_AC_SKILLS_DSDLC2_7_*.py:127-141` walks `SKILLS_DIR.iterdir()` for `p.is_dir() and (p / "SKILL.md").is_file()` — this WILL pick up the newly-created `start-project/` directory, growing the discovered set to 16 while EXPECTED_SKILLS stays at 15. **The test will FAIL after the move unless EXPECTED_SKILLS is updated to include `start-project`.** This is a load-bearing scope addition: AC.SPDISC.DSDLC-LIST in §4 (sub-AC; admits start-project into EXPECTED_SKILLS in both DSDLC1.7 and DSDLC2.7 tests).
- All `framework/workspace-bootstrap/tests/test_AC_LAYERED_*` tests (the symlinker contract is unchanged; the skip-flat-file test still passes — it builds its own synthetic flat-file in tmpfs).
- All `plugins/dev-sdlc/tests/test_AC_OSS_M6_9_*` tests (updated SKILL_PATH; same four-assertion shape).
- Architecture.md tests added by Batch A (`test_AC_BAFI_S_post_fix_state.py` — verify which substring assertions it makes about architecture.md; if it asserts `start-project` is ABSENT from architecture.md, that assertion needs revision per AC.SPDISC.ARCH).

**Halt trigger added (§6 addendum):** if `test_AC_BAFI_S_post_fix_state.py` asserts `start-project` absence from architecture.md, halt + RF before the apply — the Batch A seal carries that assertion; this amendment's reference-restoration would break it. Resolution options: (a) update the BAFI test as part of this amendment (preferred — single semantic correction); (b) halt and surface for ruling.

---

## §10. Method-decision register (populated at build time)

Placeholders for builder narration; SHAs backfilled by `loam amend seal --plan-doc`:

- **D-SPDISC.MV-METHOD** — `git mv` vs delete+create. Recommendation: `git mv` so git history preserves the relocation. **Recommended ruling at plan-author time: USE `git mv`.**
- **D-SPDISC.NAME-FIELD** — frontmatter `name: start-project` field stays vs drops. Recommendation: STAYS for v0.1.0 contract continuity (the AC.OSS-M6.9 test asserts it; removing requires test surgery without semantic benefit). The Anthropic spec doesn't require it, but neither does it forbid; subdirectory-name and frontmatter-name agreeing is benign. **Recommended ruling: STAYS.**
- **D-SPDISC.ARCH-WORDING** — how to phrase the restored architecture.md reference. Recommendation: restore parallel to the existing loam-skills / dev-sdlc paragraph: "The Dev/SDLC plugin additionally contributes a user-facing `start-project` SKILL (at `plugins/dev-sdlc/skills/start-project/SKILL.md`) for first-click intent routing — auto-symlinked into `<workspace>/.claude/skills/start-project/` at scaffold time by the same `_symlink_plugin_skills` mechanism." **Recommended ruling: PARALLEL-PARAGRAPH ADDITION.**
- **D-SPDISC.LAYERED-DOC-WORDING** — `docs/design/layered-skill-architecture.md:196`. Recommendation: replace `plugins/dev-sdlc/skills/start-project.md` with a hypothetical / generic example (e.g., `plugins/<some-plugin>/skills/<some-skill>.md`) since no real-tree flat-shape skills exist post-this-amendment. **Recommended ruling: HYPOTHETICAL EXAMPLE.**
- **D-SPDISC.LAYERED-2-TEST-COMMENT** — `test_AC_LAYERED_2_skill_symlink_registration.py:213` comment. Recommendation: rewrite as "Mirrors the historical pre-promotion shape (`plugins/dev-sdlc/skills/start-project.md` existed at v0.1.0; promoted to subdirectory shape at amendment #N+1) so the skip-flat-file contract remains exercised against a realistic input shape." **Recommended ruling: HISTORICAL-CONTEXT COMMENT.**
- **D-SPDISC.MECHANISM** — confirm `_symlink_plugin_skills` is the load-bearing mechanism. **VERIFIED Tier-0 at plan-author time** via read of `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py:1224-1310`. Walks `plugins/*/skills/*/SKILL.md` only; flat-file shapes skipped at line 1264.
- **D-SPDISC.BAFI-TEST-COLLISION** — whether Batch A's `test_AC_BAFI_S_post_fix_state.py` asserts `start-project` absence from architecture.md. **VERIFICATION DEFERRED to builder** (read at apply-time post-Batch-A-seal). If it does, builder updates that test as part of this amendment's source-edit commit (preferred path; semantic correction in the corrective amendment is on-shape).

---

## §11. Backwards-compat additional concern (raised from §8)

The DSDLC2.7 test's `test_all_twelve_dev_sdlc_skills_discovered` enforces exact-match equality against EXPECTED_SKILLS. Post-promotion the discovered set grows by 1. This is a load-bearing additional scope item — captured as the implicit AC.SPDISC.DSDLC-LIST (or merge into AC.SPDISC.COLLAT — builder's call which collateral AC to attach it to). The decision matters because it slightly grows the test edit scope; surfaced explicitly here per F2 Ruthless Feedback.

**Recommended placement: merge into AC.SPDISC.COLLAT** — the EXPECTED_SKILLS update is collateral to the relocation, not a separate semantic AC. AC.SPDISC.COLLAT's verification grows by one sub-assertion: `EXPECTED_SKILLS` in `test_AC_SKILLS_DSDLC{1,2}_7_*.py` includes `start-project`.

---

## §14. Method-decision register

(See §10. Single section; renumbering avoided to keep the recommendations + the build-time SHA backfill co-located.)

---

## §15. Backwards-compat verification

See §8 + §11 above.

---

## §16. Halt-and-surface findings (plan-authoring time)

### Finding #1 — AC.OSS-M6.9's original sealed plan-doc text DID specify "discoverable + invocable" (verified Tier-0)

The dispatcher's brief asked: "if AC.OSS-M6.9's original sealed plan-doc text REQUIRED the flat-shape specifically (e.g., for some reason that's no longer apparent), halt + surface."

**Verification result (Tier-0):** read `docs/plans/oss-v0-1-0-publish-dev-sdlc-plugin.md:246-254`. Text says "discoverable + invocable" (correct) AND specifies the verification as "the persona's skill-discovery code (per `_resolve_corpus_path`) finds it." The reader-fall-through mechanism was the v0.1.0 verification; the auto-symlinker (`_symlink_plugin_skills`) didn't exist until v0.1.7 AC.LAYERED.2. The flat-shape was correct AT THE TIME (v0.1.0) — became broken-by-divergence when v0.1.7 shipped a per-directory-only auto-symlinker without revisiting the v0.1.0 flat-shape SKILL.

**Implication:** the failure was missed at v0.1.7 ship (no test detected that AC.LAYERED.2 broke AC.OSS-M6.9's effective discoverability), not at v0.1.0 ship. AC.OSS-M6.9's test was loose (no outcome-altitude check) — but at v0.1.0 the looseness was tolerable because the reader-fall-through mechanism actually worked. The looseness became load-bearing at v0.1.7 when the discovery surface changed without test coverage of the divergence.

**Ruling (autonomous per `feedback_locked_design_not_license_for_bad_outcomes`):** the original AC text is correct + stays; the original test is loose-by-divergence and gets tightened by AC.SPDISC.DSCV (outcome-altitude). The locked v0.1.0 design (flat-shape SKILL) is revisitable when its outcomes turn out bad post-v0.1.7. NO escalation needed; the dispatcher's autonomous ruling (per `feedback_test_against_operational_objective_before_escalating`) is to proceed with the promotion.

### Finding #2 — FIVE additional collateral references hard-code or describe the flat-shape

Beyond the test file the dispatcher named (`test_AC_OSS_M6_9_*.py`), grep finds:

1. `framework/workspace-bootstrap/tests/test_AC_LAYERED_2_skill_symlink_registration.py:206-240` (test docstring + asserts using `start-project.md` as the canonical flat-shape example; test logic stays valid but comment example becomes false post-promotion).
2. `plugins/dev-sdlc/README.md:26` (user-facing reference; describes the flat-shape path).
3. `plugins/dev-sdlc/tests/test_AC_SKILLS_DSDLC1_7_all_six_skills_discovered.py:6` (docstring claims "in addition to the flat-file `start-project.md` shipped with v0.1.0").
4. `plugins/dev-sdlc/tests/test_AC_SKILLS_DSDLC2_7_all_twelve_skills_discovered.py:8` (same docstring claim).
5. `docs/design/layered-skill-architecture.md:196` (design doc cites `plugins/dev-sdlc/skills/start-project.md` as the canonical real-tree flat-file out-of-fence example).

PLUS additional user-facing references that describe the SKILL conceptually but don't hard-code shape:

6. `docs/components/objective-tracker.md:38` (mentions `start-project` skill; no path).
7. `docs/plugins/dev-sdlc.md:26,54,73` (mentions `start-project` skill; no path).

**Implication for scope:** items 1-5 are in fence (collateral updates per AC.SPDISC.COLLAT). Items 6-7 are conceptual references; their wording is unaffected by shape change — out-of-fence-for-this-amendment.

### Finding #3 — DSDLC2.7 test will FAIL after the move unless EXPECTED_SKILLS is updated

Captured in §8 + §11 above. Tier-0 read of `test_AC_SKILLS_DSDLC2_7_all_twelve_skills_discovered.py:127-141` confirms exact-match equality assertion. Scope grows by one EXPECTED_SKILLS update (merged into AC.SPDISC.COLLAT). **No halt needed — surfaced + handled within fence.**

### Finding #4 — Batch A's `test_AC_BAFI_S_post_fix_state.py` may assert architecture.md `start-project` ABSENCE (verification deferred to builder)

Captured in §10 D-SPDISC.BAFI-TEST-COLLISION above. **No plan-author-time halt** — the verification is empirically straightforward at apply-time; if the assertion exists, builder updates the BAFI test as part of this amendment's source-edit commit (preferred path; on-shape semantic correction). If for some reason that update is contentious at apply-time, builder halts + surfaces per §6.

### Finding #5 — Sequencing with Batch A seal is load-bearing (not just preferred)

The dispatcher's brief said "this amendment LANDS AFTER Batch A seals + Batch A-FIX seals." Promoted to a HARD halt trigger in §6: if Batch A is unsealed at apply-time, halt; do NOT apply (architecture.md conflict guaranteed).

---

## §12. Provenance trail

| Claim | Source | Tier |
|---|---|---|
| `start-project.md` is currently flat-shape | `ls plugins/dev-sdlc/skills/start-project.md` (file exists, 2421 bytes, mtime 2026-05-09 15:07) | Tier-0 |
| `_symlink_plugin_skills` walks subdirectory shape only | `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py:1262-1267` (`if not skill_dir.is_dir(): continue # Skip flat-file <plugin>/skills/<name>.md shapes`) | Tier-0 |
| `_symlink_plugin_skills` shipped at v0.1.7 AC.LAYERED.2 | `plugins/dev-sdlc/tests/test_AC_SKILLS_DSDLC1_7_*.py:9-13` ("v0.1.7 Cycle 3 (`bcf699a`) added `_symlink_plugin_skills()`") | Tier-1 (citation by AC name) |
| AC.OSS-M6.9 text says "discoverable + invocable" | `docs/plans/oss-v0-1-0-publish-dev-sdlc-plugin.md:246-254` | Tier-0 |
| AC.OSS-M6.9 verification was downsized to reader-fall-through | `docs/plans/oss-v0-1-0-publish-dev-sdlc-plugin.md:252` ("a unit test asserts the skill file exists + parses frontmatter + the persona's skill-discovery code (per `_resolve_corpus_path`) finds it") + the existing test file's contents | Tier-0 |
| Batch A apply commit DELETED the `start-project` reference from architecture.md | `git show 140767c -- docs/architecture.md` shows the `-` lines for the original wording | Tier-0 |
| AC.LAYERED.2 skip-flat-file test mirrors real-tree shape via comment | `framework/workspace-bootstrap/tests/test_AC_LAYERED_2_skill_symlink_registration.py:213` ("Mirrors plugins/dev-sdlc/skills/start-project.md (real-tree shape that exists today)") | Tier-0 |
| Symlinker mechanism path (per the brief: `first_run_scaffold.py:_symlink_plugin_skills`) was almost-correct: actual path includes `adapters/` subdirectory | `find framework/workspace-bootstrap -name "first_run_scaffold*"` returns `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py` | Tier-0 |
| AC.OSS-M6.9 frontmatter test asserts `name == "start-project"` | `plugins/dev-sdlc/tests/test_AC_OSS_M6_9_*.py:42` | Tier-0 |
| DSDLC2.7 test asserts exact-equality against EXPECTED_SKILLS | `plugins/dev-sdlc/tests/test_AC_SKILLS_DSDLC2_7_*.py:127-141` | Tier-0 |
| No other flat-shape SKILLs exist in canonical loam | `grep -rn "skills/.*\.md" --include="*.py" --include="*.md"` finds only `start-project.md` references (verified this turn) | Tier-0 |

---

## §13. F2 Ruthless Feedback (honest doubts)

1. **The autonomous resolution path here treats the dispatcher's framing as correct.** The dispatcher said "the flat-shape was an accident, not a design choice." Finding #1 above adds nuance: at v0.1.0, flat-shape was correct (the reader-fall-through mechanism worked); at v0.1.7, divergence was introduced silently. This is not "accident" in the simple sense — it's "missed regression at v0.1.7 ship." The corrective is the same (promote), but the framing in the audit trail should be honest: this amendment closes a regression introduced at v0.1.7, not a v0.1.0 bug.

2. **AC.SPDISC.DSCV's outcome-altitude shape is the highest-risk item to author correctly.** The test must invoke the production `_symlink_plugin_skills` entry-point against a real synthetic tree (not mocked). Builder must verify RED-on-mutation (revert the `git mv`; test fails) before declaring the AC met. The risk: a STUB-style test that bypasses `_symlink_plugin_skills` and asserts the symlink directly via `os.symlink` is method-shaped, not outcome-shaped. The AC text is explicit on this; the builder dispatch brief should reinforce.

3. **Restoring architecture.md while Batch A is still pending seal is a non-trivial coordination concern.** §6 names it as a HARD halt; §11 surfaces the BAFI test assertion-collision risk. If Batch A re-rolls or revises before sealing, this amendment's plan may need a re-author. Worth surfacing to the dispatcher: this amendment is downstream-fragile on Batch A's seal shape.

4. **The DSDLC2.7 test exact-equality assertion has been historically growing** (15 expected entries; growth in §10 D-SPDISC.MECHANISM context). Each amendment that adds a SKILL has had to touch this test. Worth a FIDRAFT capture: is the exact-equality assertion the right shape, or should it be subset-equality? Out-of-fence for this amendment, but the friction-cost is recurrent.

5. **The original AC.OSS-M6.9 plan-doc says "the skill is discoverable via the workspace's skill loader (per Idea 26's reader-fall-through composition — plugin-shipped skills resolve through `_resolve_corpus_path`)."** That mechanism — `_resolve_corpus_path` reader-fall-through — is still present per Idea 26 (citation in the original plan-doc). Question: did the flat-shape SKILL ever actually fail discoverability via the reader-fall-through path? Or did v0.1.7 ship a SECOND discovery surface (the auto-symlinker) that became dominant, leaving the reader-fall-through dormant? **This nuance does not change the corrective** (subdirectory shape ships through BOTH mechanisms and is the correct fix), but it affects the audit trail honesty. Surfaced for the builder to verify at apply-time if relevant to the seal narrative.

---

## §17. Plan-doc convention compliance footer

This plan-doc follows the canonical shape per `plugins/dev-sdlc/docs/conventions/plan-docs.md`:

- AC IDs scope-descriptive (AC.SPDISC.*), not version-packed. Per the 2026-05-09 ratification (Telegram 10644) + `feedback_scope_descriptive_ac_ids`.
- §14 method-decision register placeholder (collapsed into §10 to keep recommendations + SHA backfill co-located).
- §15 backwards-compat verification (collapsed into §8 + §11 for the same reason).
- §16 halt-and-surface findings.
- Provenance trail (§12) with Tier-tagged citations.
- F2 Ruthless Feedback (§13) named gaps + design risks.
- Halt-and-surface-before-build decisions named WITH recommendations per `feedback_summarize_and_surface_decisions`.

# loam-skills-start-project-discoverable — apply ladder

2026-05-22. Sealed-component PATCH amendment correcting the
Batch A (amendment #145) over-deletion + closing the silent
discoverability regression introduced at v0.1.7 ship.

Plan: `docs/plans/loam-skills-start-project-discoverable.md`.

Scope (per plan §3 / §5): two-component fence on
`plugins/dev-sdlc/` (load-bearing — the SKILL relocation +
test updates + README touch + two DSDLC test docstring updates)
+ `framework/workspace-bootstrap/` (secondary — one
AC.LAYERED.2 test docstring comment update). Universal
admissions: `docs/architecture.md` (reference restoration),
`docs/design/layered-skill-architecture.md` (line 196 example
rewrite).

Single-cycle, single-seal ladder per §7 of the plan-doc.

AC families (full text in plan §4):

  - AC.SPDISC.MV — `git mv` flat → subdirectory; body byte-
    identical.
  - AC.SPDISC.DSCV — OUTCOME-ALTITUDE discoverability via
    `_symlink_plugin_skills` against synthetic tmpfs workspace.
  - AC.SPDISC.OSSM69 — original v0.1.0 AC.OSS-M6.9 contract
    still satisfied at the relocated path.
  - AC.SPDISC.ARCH — docs/architecture.md reference restored
    with refined wording naming the subdirectory shape +
    auto-symlink mechanism.
  - AC.SPDISC.COLLAT — collateral updates across 5 sites +
    EXPECTED_SKILLS admission in both DSDLC tests.
  - AC.SPDISC.S — smoke: fresh workspace via production
    fresh-scaffold entry-point carries the discoverable SKILL.

Method-level choices (recommendations in plan §10; rulings
backfilled at build time):

  - D-SPDISC.MV-METHOD — `git mv` recommended (history).
  - D-SPDISC.NAME-FIELD — frontmatter `name:` stays.
  - D-SPDISC.ARCH-WORDING — parallel-paragraph addition.
  - D-SPDISC.LAYERED-DOC-WORDING — hypothetical example.
  - D-SPDISC.LAYERED-2-TEST-COMMENT — historical-context
    wording.
  - D-SPDISC.MECHANISM — Tier-0-verified at plan-time
    (`_symlink_plugin_skills` walks per-directory; flat-file
    skipped at line 1264 of
    `framework/workspace-bootstrap/src/loam/workspace_bootstrap/
    adapters/first_run_scaffold.py`).
  - D-SPDISC.BAFI-TEST-COLLISION — verification at apply-time;
    builder updates Batch A's BAFI test in this amendment's
    source-edit commit if collision detected.

Predecessor commits (per plan §2):
  - 21c1ddf — Batch A plan-doc + manifest commit.
  - 140767c — Batch A apply commit (pre-seal at plan-author
              time).
  - <Batch A seal SHA> — baseline for this amendment.

Audit-trail honesty (per plan §13 finding #1): this amendment
closes a regression introduced at v0.1.7 AC.LAYERED.2 ship,
not a v0.1.0 bug. At v0.1.0 the flat-shape SKILL was
discoverable via `_resolve_corpus_path` reader-fall-through;
v0.1.7's `_symlink_plugin_skills` per-directory-only walk
introduced the divergence silently. The original AC.OSS-M6.9
test was loose-by-divergence (outcome-altitude gap that
became load-bearing at v0.1.7), not loose-at-authoring.

BASELINE — Batch A seal SHA (backfilled at apply-time). Two-
component fence on `plugins/dev-sdlc/` +
`framework/workspace-bootstrap/`. Sidecars advance to this
amendment's seal SHA at apply time.
