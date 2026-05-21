# Amendment #138 — dev-sdlc test directory cleanup (PMR stale path + SKILL.md YAML scalar shape)

**Status:** plan-doc, plan-before-code. Authored 2026-05-21 by the `loam-plan-author` subagent (background dispatch from the persona).
**Working directory:** `/Users/lukeivers/loam/` (canonical loam tree).
**Quality bar:** single-component change, ≤6 ACs + 1 outcome-altitude smoke; no method-in-AC; behavior-preserving (test-and-doc cleanup only — no production-code change to the `loam.plugins.dev_sdlc` package).

---

## §0. NARROWING ADDENDUM (2026-05-21, post-builder F2 halt — Telegram 11852)

**This amendment was narrowed from its original two-scope authoring to SKILL-frontmatter-only.** The PMR scope (AC.DSTC.PMR.{1,2}) is DEFERRED to a separate follow-on amendment because the builder's first cycle surfaced a structural test-corpus contradiction the plan-author's pre-flight missed:

After deleting the `framework/memory-system/` manifest entries (Scope A's intended fix), `test_AC_PMR_4_every_always_loaded_glob_resolves` exposed a second stale entry — `data/` (root at L66 + glob at L124). The `data/` directory was deleted from canonical at commit `39cfbb1` (2026-04-28). But two PMR_4 tests MUTUALLY CONTRADICT on the `data/` case:

- `test_AC_PMR_4_every_always_loaded_glob_resolves` requires every glob to expand to a non-empty match-set.
- `test_AC_PMR_4_data_stays_top_level` requires `data/**` to stay in the `always_loaded` block.

No manifest-only edit satisfies both. Resolution requires either (a) test-corpus edit (out of this amendment's fence per §5) or (b) a sentinel `data/` directory creation (architectural decision). Neither is in this amendment's authorized scope.

**Narrowed scope for the in-flight build:**
- IN: AC.DSTC.SKILLS.{1,2,3,4} + AC.DSTC.S (smoke scoped to SKILL fix only, NOT the full directory).
- DEFERRED: AC.DSTC.PMR.{1,2} — re-scoped in a separate amendment that names the test-corpus resolution explicitly.
- The narrowed outcome-altitude smoke admits the 2 pre-existing PMR failures as known-and-deferred (not regressions introduced by this amendment).

**Persona ratification of the narrowing (TG 11852):** under owner build-strategy delegation TG 11808 + 11850; the narrowing preserves the SKILL-frontmatter delta (9-of-11 failures cleared) and queues the PMR/data work as its own ratified follow-on rather than ad-hoc extending this amendment's fence.

---

## §1. Objective / Summary / TL;DR

Bring `plugins/dev-sdlc/tests/` to green so future seal-tool work (notably the unwritten seal-tool hygiene pair — F-SEAL-PLUGINS-TESTS-SKIPPED + F-SEAL-DIRTY-TREE-CHECK-AFTER-PLAN-ARCHIVE — which will invoke the full test suite for plugins/-tree components) lands on a clean baseline. Two concrete fixes:

1. **PMR_3 stale path refs** — `plugins/dev-sdlc/dev-mode-manifest.yaml` carries `framework/memory-system/` (root entry at L49 + glob at L97); that directory was deleted at `b92aaea` (v0.3.0 graphiti rip-out). Delete the two entries from the manifest. Test `test_AC_PMR_3_dev_mode_manifest_roots_realigned.py` then asserts every remaining root + glob resolves.
2. **SKILL.md YAML scalar shape** — `plan-before-code-author/SKILL.md` + `plan-docs-author/SKILL.md` each carry a long single-line `description:` value containing English colons (`"applied 2026-05-05:"`, `"Distinct from `plan-before-code-author`: ..."`) that PyYAML's flow scanner reads as inline key/value separators, raising `yaml.scanner.ScannerError: mapping values are not allowed here`. Rewrite each `description:` as a `>-` (folded, strip-trailing-newline) block scalar so internal colons stay part of the string. 9 currently-failing tests across 4 test files clear on the same fix.

**Why now:** Tier-0 verification with the workspace venv's Python 3.13 (`.venv/bin/python` → `python3.13`, which is what the seal-tool uses per `_run_pytest` in `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/seal.py:284`) shows **11 failures** in `plugins/dev-sdlc/tests/`: 2 PMR + 9 SKILLS. The 6 OSS_M6 collection errors the dispatch brief flagged are a Python-version artifact — they disappear under Python 3.13 because the package's `requires-python = ">=3.13"`. Under the seal-tool's actual invocation path (venv-python), OSS_M6 already collects and runs. No product code needs authoring.

**Pre-flight Tier-0 evidence (verifiable from this commit):**

| Check | Command | Result |
|---|---|---|
| Canonical WD + HEAD | `cd /Users/lukeivers/loam && git log --oneline -1` | `30fd65d docs(readme): bump current-release to v0.12.14` |
| Last sealed amendment | `ls docs/plans/sealed/amendment-13*.md` | #134, #135, #136, #137 (no #138 — this IS the next) |
| memory-system deletion | `git log --all --oneline --diff-filter=D -- framework/memory-system` | `b92aaea chore(v0.3.0): Cycle 2 — delete framework/memory-system/` |
| memory-system absence | `ls framework/memory-system 2>&1` | `No such file or directory` |
| Manifest stale refs | `grep -n 'memory-system' plugins/dev-sdlc/dev-mode-manifest.yaml` | `49: - framework/memory-system/` + `97: - glob: "framework/memory-system/**"` |
| SKILL.md parse fail | `python3.13 -c "import yaml; yaml.safe_load(open('plugins/dev-sdlc/skills/plan-docs-author/SKILL.md').read().split('---')[1])"` | `ScannerError: mapping values are not allowed here … line 1, column 616` |
| SKILL.md present | `ls plugins/dev-sdlc/skills/{plan-docs-author,plan-before-code-author}/SKILL.md` | both exist |
| Seal-tool python | `cat .venv/bin/python` (symlink target) | `/opt/homebrew/opt/python@3.13/bin/python3.13` |
| OSS_M6 under py3.13 | `python3.13 -m pytest plugins/dev-sdlc/tests/ --co -q` | 259 tests collect, **0 errors** |
| Failure shape under py3.13 | `python3.13 -m pytest plugins/dev-sdlc/tests/ -q` | **11 failed, 241 passed, 7 skipped** (2 PMR + 9 SKILLS, all SKILLS via the same YAML scalar shape) |
| `loam.plugins.dev_sdlc.contribution` exists | `python3.13 -c "import loam.plugins.dev_sdlc.contribution; print(__file__)"` | `plugins/dev-sdlc/src/loam/plugins/dev_sdlc/contribution.py` (the module the brief feared missing IS PRESENT) |

**Owner-ratification record (per `feedback_record_owner_ratification_before_dispatch`):**

| msg-ID | ts (UTC) | Owner ruling |
|---|---|---|
| TG 11808 | 2026-05-21T16:14:01Z | Build-strategy delegation |
| TG 11837 | 2026-05-21 | Durable-autonomy directive |
| TG 11840 | 2026-05-21 | Autonomous queue pickup ratified |
| TG 11847 | 2026-05-21 | Queue-merge-check directive |
| TG 11850 | 2026-05-21 | Persona ruling on Option 1 + corrected scope after the previous plan-author's F2 halt |

The msg-IDs are dispatcher-supplied; if the build agent reads `docs/STATE.md` or scrollback and finds different timestamps, the build agent corrects per its own Tier-0 lookup.

---

## §2. Predecessors / context

- **Predecessor (load-bearing):** amendment #137 seal at `43d1ded` (legacy `pos-amend` name docs-corpus sweep — the most-recent sealed amendment). Manifest BASELINE points there.
- **Parent capture:** FIDRAFT entries F-SEAL-PLUGINS-TESTS-SKIPPED + F-SEAL-DIRTY-TREE-CHECK-AFTER-PLAN-ARCHIVE in `docs/FUTURE_IDEAS_DRAFT.md` (lines 322 + 324). Those will be promoted in a separate amendment (the unwritten seal-tool hygiene pair) — THIS amendment is the prerequisite that makes that future amendment's seal-step automation able to run plugins/-tree pytest cleanly.
- **Sibling caprtures (out of scope):** F-COCITATION-EXTRACTOR-HEURISTIC-FRAGILE (capture-only, low severity, separate substrate).

---

## §3. Scope

**In-scope:**
1. Delete `framework/memory-system/` root entry + glob from `plugins/dev-sdlc/dev-mode-manifest.yaml`.
2. Rewrite the `description:` field in both `plugins/dev-sdlc/skills/plan-docs-author/SKILL.md` and `plugins/dev-sdlc/skills/plan-before-code-author/SKILL.md` as a `>-` block scalar so internal colons parse correctly. Body of each SKILL.md unchanged.
3. Verify the resulting `description:` text remains ≤ `DESCRIPTION_MAX_CHARS = 1536` (the cap baked into both SKILL discovery tests).

**Out-of-scope:**
- Any change to the `loam.plugins.dev_sdlc` package source under `plugins/dev-sdlc/src/`.
- Any change to test files under `plugins/dev-sdlc/tests/` (the tests are already written correctly — they're verifying the fixes this amendment lands; no test edits needed).
- The seal-tool hygiene pair itself (F-SEAL-PLUGINS-TESTS-SKIPPED + F-SEAL-DIRTY-TREE-CHECK) — separate amendment with its own scope.
- Any sweep of orphan `framework/` directories the manifest doesn't include (`binary-observation-harness`, `claude-p-client`, `loam-init`, `per-project-pm`, `principle-foundation` — see §10 RF #2; that's an AC.F5 audit, not this amendment's surface).
- Any other oversized-YAML-manifest-field cleanup that surfaces at `loam amend seal` time rather than inside the test suite (per the dispatch brief; that work stays queued separately).

---

## §4. Acceptance criteria

| AC ID | Outcome (what's observable) | Verification |
|---|---|---|
| **AC.DSTC.PMR.1** | `framework/memory-system/` no longer appears in `plugins/dev-sdlc/dev-mode-manifest.yaml`'s `roots:` block; every remaining `roots:` entry resolves to an existing on-disk path under the canonical workspace. | `test_AC_PMR_3_dev_mode_manifest_roots_realigned.py::test_AC_PMR_3_every_root_resolves_on_disk` passes. |
| **AC.DSTC.PMR.2** | `framework/memory-system/**` no longer appears in the manifest's `always_loaded:` block; every remaining glob expands to a non-empty match-set against the canonical workspace tree. | `test_AC_PMR_3_dev_mode_manifest_roots_realigned.py::test_AC_PMR_4_every_always_loaded_glob_resolves` passes. |
| **AC.DSTC.SKILLS.1** | The frontmatter of `plugins/dev-sdlc/skills/plan-before-code-author/SKILL.md` parses as a valid YAML mapping with `description:` returning a non-empty string ≤ 1536 chars. | `test_AC_SKILLS_DSDLC1_3_plan_before_code_author_skill_present.py::test_skill_frontmatter_valid_with_description` + `::test_skill_body_non_empty` + `::test_skill_body_mentions_plan_skeleton_terms` all pass. |
| **AC.DSTC.SKILLS.2** | The frontmatter of `plugins/dev-sdlc/skills/plan-docs-author/SKILL.md` parses as a valid YAML mapping with `description:` returning a non-empty string ≤ 1536 chars. | `test_AC_SKILLS_DSDLC2_2_plan_docs_author_skill_present.py::test_skill_frontmatter_valid_with_description` + `::test_skill_body_non_empty` + `::test_skill_body_mentions_plan_docs_terms` all pass. |
| **AC.DSTC.SKILLS.3** | All 6 v0.1.8-Cycle-5 SKILLs parse as valid YAML at the canonical discovery path. | `test_AC_SKILLS_DSDLC1_7_all_six_skills_discovered.py::test_each_expected_skill_has_valid_frontmatter[plan-before-code-author]` passes (the other 5 already pass per pre-flight). |
| **AC.DSTC.SKILLS.4** | All 15 dev-sdlc SKILLs parse as valid YAML at the canonical discovery path. | `test_AC_SKILLS_DSDLC2_7_all_twelve_skills_discovered.py::test_each_expected_skill_has_valid_frontmatter[plan-before-code-author]` + `[plan-docs-author]` both pass. |
| **AC.DSTC.S** | **Outcome-altitude smoke:** `python3.13 -m pytest plugins/dev-sdlc/tests/ -q` against the post-amendment HEAD returns **0 failures + 0 collection errors** (the 7 pre-existing skips are admissible — they're not failures). | Direct pytest invocation. |

All ACs are outcome-shape: each asserts a measurable property of the post-amendment artefact, not a method. The method test passes (the regex `r"\Aac\.dstc\..*"` is satisfied by something other than the methods named in §5 — e.g., a future maintainer could fix the YAML parse by changing the description to a single-line scalar with all colons escaped via `:`, satisfying SKILLS.1-4 without using `>-`; the AC text doesn't prescribe the method).

**Outcome-altitude classification:** AC.DSTC.S satisfies the `feedback_test_outcome_altitude_required` rule — it invokes the production verification path (pytest against the full directory) with no pre-arranged state; the test passes only if every individual AC's check passes plus no surprise breakage occurred.

---

## §5. Sealed-component fence

**Component touched:** `dev-sdlc` (the sealed component at `plugins/dev-sdlc/`).

**Surfaces edited:**
1. `plugins/dev-sdlc/dev-mode-manifest.yaml` — two-line delete (roots L49 + always_loaded glob L97).
2. `plugins/dev-sdlc/skills/plan-before-code-author/SKILL.md` — frontmatter `description:` rewrite (body unchanged).
3. `plugins/dev-sdlc/skills/plan-docs-author/SKILL.md` — frontmatter `description:` rewrite (body unchanged).

**Universal admissions:**
- `docs/plans/` (this plan-doc + manifest; archives to `docs/plans/sealed/` on seal per T1.4).

**Out of fence (halt-and-surface trigger — see §7):**
- Any other component under `framework/` or `plugins/`.
- Any file under `plugins/dev-sdlc/` outside the three surfaces named above.
- The `loam.plugins.dev_sdlc` package source under `plugins/dev-sdlc/src/`.

---

## §6. Build steps (method-level guidance — builder's call per ODD §1.1)

1. **Plan-doc + manifest land** (this commit).
2. **Source edit 1 — `dev-mode-manifest.yaml`:** delete the two `framework/memory-system/` lines. Verify by `python3.13 -m pytest plugins/dev-sdlc/tests/test_AC_PMR_3_dev_mode_manifest_roots_realigned.py -v` showing the PMR_3 + PMR_4 cases green.
3. **Source edit 2 — `plan-before-code-author/SKILL.md`:** rewrite `description: <long-line>` as:
   ```yaml
   description: >-
     <same content as the current single-line value, line-broken at sensible
     points; the `>-` folded scalar joins broken lines with a single space
     and strips the trailing newline so the parsed value is identical to
     the current intended value modulo whitespace normalization>
   ```
   Verify by `python3.13 -c "import yaml, re; t = open('…SKILL.md').read(); m = re.match(r'\\A---\\s*\\n(.*?)\\n---\\s*\\n(.*)\\Z', t, re.DOTALL); fm = yaml.safe_load(m.group(1)); print('len:', len(fm['description']))"` — passes parse + length ≤ 1536.
4. **Source edit 3 — `plan-docs-author/SKILL.md`:** same shape as edit 2.
5. **Touched-tests run.** `python3.13 -m pytest plugins/dev-sdlc/tests/test_AC_PMR_3_*.py plugins/dev-sdlc/tests/test_AC_SKILLS_DSDLC1_3_*.py plugins/dev-sdlc/tests/test_AC_SKILLS_DSDLC2_2_*.py plugins/dev-sdlc/tests/test_AC_SKILLS_DSDLC1_7_*.py plugins/dev-sdlc/tests/test_AC_SKILLS_DSDLC2_7_*.py -v` — every previously-failing case green.
6. **Pre-seal full directory run.** `python3.13 -m pytest plugins/dev-sdlc/tests/ -q` — verifies AC.DSTC.S. **Expected:** 0 failures, 0 errors, ~241+11=252 passed, 7 skipped (this is the outcome-altitude smoke).
7. **`loam amend apply`** — auto-commit per ergonomics.
8. **`loam amend seal --plan-doc docs/plans/amendment-138-dev-sdlc-test-directory-cleanup.md`** — deterministic seal commit. The seal-tool's own pre-seal pytest run on the `dev-sdlc` component uses `.venv/bin/python -m pytest` (Python 3.13) per `_run_pytest`, which is exactly the same path step 6 verified — so the seal-step's test run is precondition-met. (Caveat: F-SEAL-PLUGINS-TESTS-SKIPPED says the per-component test run silently skips for plugins/-tree components today; that doesn't BLOCK this seal — it means the seal-step won't add additional verification beyond what step 6 already did. The seal still proceeds.)
9. **Section-14 auto-backfill** uses the canonical `## §14 — Method-decision register` heading (post-#136 widening); no manual fallback expected.

---

## §7. Halt triggers (in-flight)

1. Source edits leak outside the three surfaces named in §5.
2. The `>-` rewrite of either SKILL.md's `description:` causes the resulting parsed string to exceed `DESCRIPTION_MAX_CHARS = 1536` (the test would fail; would need to trim the description, which is doc-content change — surface to dispatcher before committing).
3. After step 2, the body-content tests (`test_skill_body_mentions_plan_skeleton_terms` / `test_skill_body_mentions_plan_docs_terms`) still fail — would indicate the loader can now parse frontmatter but the body is genuinely missing required terms; halt-and-surface (would need a body edit, which is doc-content change beyond YAML scalar shape).
4. Step 6's full-directory pytest reveals an unanticipated failure outside PMR + SKILLS — would indicate either a flaky test, an unrelated regression introduced by an unrelated commit, or a real product issue that requires its own amendment. Halt-and-surface; do not silently widen scope.
5. **OSS_M6 regression under py3.13.** If `python3.13 -m pytest plugins/dev-sdlc/tests/test_AC_OSS_M6_*.py` returns failures (not just collection errors) at step 6, the OSS_M6 surface has a real bug. Halt-and-surface — the dispatch brief named OSS_M6 as one of the original scopes; the persona may want to widen this amendment to include the fix, OR keep this amendment narrow and dispatch a follow-up.
6. **Manifest auto-backfill fails** at seal time (the post-#136 widened regex should match `## §14`; if it doesn't, separate amendment needed against seal-tool — out of scope here).

---

## §8. Out of scope (deferred)

- **The seal-tool hygiene pair** (F-SEAL-PLUGINS-TESTS-SKIPPED + F-SEAL-DIRTY-TREE-CHECK-AFTER-PLAN-ARCHIVE). Promoted to its own amendment (likely next-up after this one).
- **Oversized YAML manifest field cap** (the brief's original Scope C). Stays in queue as `ws-loam-amend-oversized-manifest-field-cleanup`.
- **F5 orphan audit on `framework/` subdirs not in the manifest** (`binary-observation-harness`, `claude-p-client`, `loam-init`, `per-project-pm`, `principle-foundation` — see §10 RF #2). Would be its own AC.F5 audit pass.
- **The cocitation-extractor heuristic** (F-COCITATION-EXTRACTOR-HEURISTIC-FRAGILE). Separate substrate.

---

## §9. Bookkeeping (post-seal)

- **`docs/STATE.md`** — status-line update naming amendment #138 sealed at `<seal-SHA>` + closing the dependency the seal-tool hygiene pair amendment was waiting on.
- **`docs/FUTURE_IDEAS_DRAFT.md`** — no closure (the parent FIDRAFTs F-SEAL-PLUGINS-TESTS-SKIPPED + F-SEAL-DIRTY-TREE-CHECK remain open; this amendment is their PREREQUISITE, not their closure).
- **`docs/release-roadmap.md`** — no entry needed (test-cleanup is patch-class hygiene).
- **§14 of this plan-doc** — backfilled by `loam amend seal` (canonical `## §14 — Method-decision register` heading; post-#136 regex widening matches; no manual fallback expected).

---

## §10. F2 Ruthless Feedback (honest doubts + corrections to dispatch brief)

1. **F2 on dispatch brief — Scope C framing was incorrect.** The brief asserted OSS_M6 collection errors stem from "module path stale / module missing / pyproject install-discovery issue" and asked the plan-author to pre-flight + decide between (i) update imports, (ii) wire missing exports, or (iii) halt as product-work. Tier-0 evidence (the workspace venv at `.venv/bin/python → python3.13` resolves all 6 collection errors immediately, with all 6 OSS_M6 tests collecting and the underlying `loam.plugins.dev_sdlc.contribution` module importing cleanly) shows the collection errors are an artifact of the `pyenv` shim defaulting to Python 3.9.17 — the package requires `>=3.13`. **No code change is needed for OSS_M6.** The amendment scope drops from three concerns to two; this is a tighter, faster cycle than the brief anticipated. (Method-decision D-DSTC.OSS-M6-RESOLUTION = "no action; pre-flight resolves the question").
2. **F2 on dispatch brief — orphans in `framework/` not in the manifest.** Tier-0: `framework/` contains 22 subdirs; the manifest's `roots:` block lists 16 component-dirs + `tools/` + `first-run-inventory.yaml`. **NOT in the manifest at all:** `binary-observation-harness/`, `claude-p-client/`, `loam-init/`, `per-project-pm/`, `principle-foundation/`. The manifest's AC.F5 invariant (every workspace path under `roots:` matched by exactly one partition) wouldn't be violated by these omissions (they're not under any current root), but they're effectively partition-orphans. **Recommendation:** out of scope here; raise as a separate FIDRAFT or AC.F5 audit pass. Surfacing for dispatcher awareness.
3. **F2 on dispatch brief — the replacement-path claim was incorrect.** The brief said "memory implementation lives inside `framework/primary-persona/` per amendment #134's fence correction." Tier-0 contradicts: `framework/memory-system/` was DELETED at `b92aaea` (v0.3.0 Cycle 2 graphiti rip-out), not absorbed. `framework/primary-persona/` consumes memory via a callable provider (loose coupling, per `framework/primary-persona/docs/relationship-map.md`). The correct fix is **deletion of the manifest entries**, not relocation to `framework/primary-persona/`. (This contradicts a load-bearing claim in the brief; surfacing per F2.)
4. **F2 on dispatch brief — amendment #138 doesn't exist on disk.** The brief asserted "Amendment #138 plan-doc lives at the NON-SEALED path: `/Users/lukeivers/loam/docs/plans/amendment-138-loam-amend-seal-tool-hygiene-pair.md` (NOT in sealed/ — it's in-flight, halted at seal)." Tier-0: no such file exists at any path; the most recent sealed amendment is #137 (`docs/plans/sealed/amendment-137-…md`); the seal-tool hygiene pair lives in `docs/FUTURE_IDEAS_DRAFT.md` as FIDRAFTs, not yet promoted to a plan-doc. **Conclusion:** this amendment IS #138 (the next-up number after #137), not #139. Plan-doc filename `amendment-138-dev-sdlc-test-directory-cleanup.md` reflects the Tier-0 reality. The framing that "this amendment unblocks #138's seal" reverses to "this amendment IS #138 and clears a prerequisite for the future seal-tool hygiene amendment (which will be #139 or later)."
5. **Doubt — the column-position drift between the test's quoted column (493) and the actual scanner column (616).** Pre-flight shows the SKILL.md `description:` for `plan-docs-author` is 981 chars long (was apparently ~610 when the failure message was first observed in the brief); the description has been edited since. The fix (block-scalar rewrite) is robust to length changes — the YAML structure is what matters, not the column. Low-risk.
6. **Doubt — colons inside the `>-` block scalar.** YAML's block-scalar parsing strips off all flow-context semantics for colons; verified by direct test: `python3.13 -c "import yaml; print(yaml.safe_load('description: >-\\n  has: colons: inside: it'))"` returns `{'description': 'has: colons: inside: it'}` correctly. The fix WORKS by construction.
7. **F2 — should this amendment ALSO ship a regression test that catches a future `description:` field that breaks YAML parsing?** Argument-for: the failure surfaced organically; the same shape will recur. Argument-against: the existing SKILL discovery tests (`test_AC_SKILLS_DSDLC1_7` + `test_AC_SKILLS_DSDLC2_7`) ALREADY do `yaml.safe_load(frontmatter)` on every SKILL — so any future YAML-malformed `description:` would surface at the same test-pair on the next build. The regression-test surface already exists; no new test needed. (Tight-scope per F4: confidence is high that the existing tests are sufficient.)
8. **Doubt — does the `dev-mode-manifest.yaml` carry any OTHER stale entry the test suite doesn't catch?** Verified via the `roots:` block scan — every other root resolves. The PMR_4 always_loaded glob block also passes for all entries except `framework/memory-system/**`. Low-risk; the test IS the audit.

---

## §11. Provenance trail

- **Plan-doc convention:** `plugins/dev-sdlc/docs/conventions/plan-docs.md` (the canonical authoring shape).
- **Recent exemplar (single-component, regex-fix shape):** `docs/plans/sealed/amendment-136-loam-amend-seal-section-14-backfill-regex-widening.md`.
- **Recent exemplar (cross-component sweep):** `docs/plans/sealed/amendment-137-legacy-pos-amend-name-docs-corpus-sweep.md`.
- **Parent FIDRAFTs:** `docs/FUTURE_IDEAS_DRAFT.md` L322 (F-SEAL-PLUGINS-TESTS-SKIPPED) + L324 (F-SEAL-DIRTY-TREE-CHECK-AFTER-PLAN-ARCHIVE).
- **memory-system deletion commit:** `b92aaea chore(v0.3.0): Cycle 2 — delete framework/memory-system/ (graphiti rip-out)`.
- **Seal-tool python invocation path:** `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/seal.py:284-302` (`_run_pytest` uses `.venv/bin/python -m pytest`).
- **Workspace venv python target:** `.venv/bin/python → /opt/homebrew/opt/python@3.13/bin/python3.13`.
- **Plugin pyproject requires-python:** `plugins/dev-sdlc/pyproject.toml` L11 `requires-python = ">=3.13"`.

---

## §14. Method-decision register (placeholder — populated by builder)

| Decision | Recommendation | Ratified by | Authority |
|---|---|---|---|
| **D-DSTC.PMR-FIX** | Delete the two `framework/memory-system/` lines from `dev-mode-manifest.yaml`. **Recommend: ratify.** Pre-flight Tier-0 evidence shows the directory was deleted (not relocated) at `b92aaea`; deletion is the correct cleanup. | persona (build-strategy delegation TG 11808) | Plan-author Tier-0 verified. |
| **D-DSTC.SKILLS-FRONTMATTER** | Rewrite each affected `description:` field as a `>-` (folded, strip-trailing-newline) block scalar; body content unchanged. **Recommend: ratify.** Preserves the long-form description without escape-character whack-a-mole; verified by direct YAML parse test. | persona (build-strategy delegation TG 11808) | Plan-author Tier-0 verified. |
| **D-DSTC.OSS-M6-RESOLUTION** | **No action.** Pre-flight Tier-0 evidence shows the 6 collection errors are a Python-version artifact (pyenv shim defaulting to 3.9.17 while the package requires `>=3.13`); the seal-tool's `_run_pytest` uses `.venv/bin/python` which is Python 3.13, so OSS_M6 already collects and runs cleanly under the production verification path. **Recommend: ratify.** | persona (build-strategy delegation TG 11808 — explicit halt-and-surface trigger in the dispatch brief; resolution is "no action needed" rather than triggering the product-work halt). | Plan-author Tier-0 verified. |
| **D-DSTC.AC-LADDER** | AC families: `AC.DSTC.PMR.{1,2}` + `AC.DSTC.SKILLS.{1..4}` + `AC.DSTC.S` (outcome-altitude smoke). **Recommend: ratify.** | persona (build-strategy delegation TG 11808) | Plan-author convention (scope-descriptive AC IDs per the M5 ratification 2026-05-09). |

**Commit SHAs (manual backfill — seal-tool's auto-backfill did not fire due to post-seal dry-run halt; F2 surface in §16):**

- Plan-doc commits: `f7008fd` (initial plan + manifest) + `c1880ce` (NARROWING ADDENDUM)
- Source-edit commit: `1da9350` — `fix(dev-sdlc): SKILL.md description fields as >- block scalar (AC.DSTC.SKILLS.1-4)`
- Amendment commit: `a6fd874` — `chore(amend): amendment-138-dev-sdlc-test-directory-cleanup apply — dev-sdlc BASELINE+sidecar bump to 43d1ded`
- Seal commit: `01e63ac` — `chore(seals): amendment-138-dev-sdlc-test-directory-cleanup — dev-sdlc at a6fd874`
- Corrective fixup commit: `26f3a9e` — `chore(amend-fixup): remove orphan dev-sdlc file from #138 seal commit` (cleanup of seal-tool's misinterpretation of `narrative.target: dev-sdlc` as a write-path — see §16 finding #2)

---

## §15. Backwards-compat verification

- **All non-touched tests in `plugins/dev-sdlc/tests/`** continue to pass (currently 241 pass under py3.13; this amendment changes only test EXPECTATIONS by fixing the artefacts the tests audit — no test-code change).
- **All other components' tests** untouched; cross-component seal-diff sweep at step 8 verifies no diff leaked into other sealed components.
- **The `loam.plugins.dev_sdlc` Python package** is unchanged (no edit under `plugins/dev-sdlc/src/`). Import behavior + entry-point discovery unchanged.
- **The SKILL.md auto-discovery mechanism** (`_symlink_plugin_skills` at `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py`) reads the SKILL.md FILE PATH, not its content shape; the `>-` rewrite doesn't change file presence; behavior unchanged.

---

## §17. Composition (M5 derivation line)

- **Composes with** `feedback_record_owner_ratification_before_dispatch` — the §1 ratification table records the five msg-IDs durably before the build agent dispatches off this commit.
- **Composes with** `feedback_information_trust_ordering` — the §10 RF #3 + #4 corrections to the dispatch brief are direct applications of Tier-0-over-Tier-2 (the plan-author's empirical file-system check overrode the dispatcher's recall-based claims).
- **Composes with** `feedback_loose_AC_text_fix_AC_not_implementation` — the AC text is outcome-shape; method (deletion vs relocation, `>-` vs escaped colons) is the builder's call.
- **Composes with** `feedback_dispatch_explicit_loam_amend_apply` — the §6 step 7 names `loam amend apply` as the bookkeeping mechanism.
- **Composes with** `feedback_test_outcome_altitude_required` — AC.DSTC.S is the outcome-altitude AC for the cycle (full-directory pytest, no pre-arranged state).
- **Composes with** the post-#136 seal-tool widening — the §14 backfill uses the canonical `## §14 — Method-decision register` heading; no manual fallback expected.
- **Independent of** F4 (this amendment's scope is small enough that scope-confidence-tightening doesn't drive any structural decision).
- **PREREQUISITE OF** the unwritten seal-tool hygiene pair amendment (F-SEAL-PLUGINS-TESTS-SKIPPED + F-SEAL-DIRTY-TREE-CHECK-AFTER-PLAN-ARCHIVE) — that amendment will exercise the full plugins/dev-sdlc test suite via the seal-step automation; without this cleanup, that exercise would fail on baseline.

---

## §16. Halt-and-surface findings (build-agent backfill)

Backfilled by `loam-builder` subagent post-seal per `feedback_subagent_odd_violation_halt` + F2 Ruthless Feedback. Surfaces beyond the plan-author + first-builder findings:

1. **F2 — manifest narrative.target field was authored as `dev-sdlc` (component name) instead of a file path.** The seal-tool interpreted `narrative.target` as a write-target and dumped the 2778-byte narrative body to a literal file at `<repo-root>/dev-sdlc`. Compare #137's manifest (`narrative.target: docs/plans/sealed/amendment-137-….md`). **Effect:** seal commit `01e63ac` added an orphan `dev-sdlc` file at repo root; post-seal `loam amend apply --dry-run` flagged `MISSING_ADMISSION: dev-sdlc`. **Recovery:** corrective fixup commit `26f3a9e` removed the orphan. **Alternative recommended:** plan-author SKILL's manifest-template should emit `narrative.target: docs/plans/sealed/<slug>.md` by default, not the component name. Per `feedback_loose_AC_text_fix_AC_not_implementation` and `feedback_information_trust_ordering`, this is a plan-author surface gap that warrants a follow-up patch to the manifest template.

2. **F2 — seal-tool's `--plan-doc` §14 auto-backfill DID NOT fire** because the seal command halted at post-seal dry-run (the orphan-file MISSING_ADMISSION halt). The plan-doc §6 step 9's expectation ("no manual fallback expected") was unmet. **Recovery:** manual SHA backfill in §14 (this commit). **Composition with the post-#136 seal-tool widening:** the §14 heading regex matched, but the auto-backfill step is GATED on the post-seal dry-run passing. A future seal-tool patch should either (a) decouple §14 backfill from post-seal verification, or (b) auto-retry §14 backfill after corrective fixup commits land. F2 on the plan-doc's "no manual fallback expected" claim — that claim assumes post-seal dry-run clean, which the narrative.target bug above broke.

3. **F2 — workflow ordering misstep during the first build attempt (recovered).** The builder ran `loam amend apply` BEFORE committing the SKILL.md source edits, expecting the apply auto-commit to pick up working-tree edits. It does NOT — `loam amend apply` advances sidecar bookkeeping only against the committed HEAD. Recovery: `git reset --mixed` to pre-apply state (no `--amend`; branch unpushed, local-only history adjustment), then the proper ladder: source-edit commit → apply → seal. This is a builder-side discipline gap; the plan-doc §6 build steps name "2. Source edit 1 ... 7. loam amend apply" but the IMPLICIT ordering — source edits must be COMMITTED before apply — should be made explicit in the methodology. **Composition:** `feedback_dispatch_explicit_loam_amend_apply` names the apply step but doesn't surface the source-must-be-committed prerequisite.

4. **Narrowed AC.DSTC.S smoke confirmed.** Final pytest: 250 passed (was 241 pre-amendment) + 7 skipped + 2 failed. The 2 failures are the known-deferred PMR cases (test_AC_PMR_3_every_root_resolves_on_disk + test_AC_PMR_4_every_always_loaded_glob_resolves) admitted per §0 NARROWING ADDENDUM. 9 SKILL failures cleared (4 SKILL AC families satisfied: AC.DSTC.SKILLS.{1,2,3,4} all green). 0 new regressions, 0 collection errors.

5. **Component fence held.** The seal-test `test_only_dev_sdlc_changed` passed against the SEAL_COMMIT sidecar (`a6fd874`). The orphan `dev-sdlc` file landed in the seal commit but the sidecar pins to the apply commit, so the seal-test's diff window predates the orphan. The corrective fixup commit (`26f3a9e`) removes the orphan in a post-seal HEAD-only state.
