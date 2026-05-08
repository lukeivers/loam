# FBE.8 sub-plan — close FBE.6 reviewer BLOCKERs + HIGH cosmetics + FBE.6 seal-debt

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-03.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/plans/v0-1-0-foldback-scope-expansion.md` (FBE.8 row to be backfilled in §8 register at completion).
**Programme master:** `docs/plans/oss-v0-1-0-publish.md`.
**Predecessors:** FBE.{1,2,2b,2c,3,4,5,5b,7} all sealed (`21b9480`, `8d2b770`, `47ccb3a`, `1d6ff13`, `becf183`, `99c03a6`, `bc56f0d`, `48bb7e2`, `a102bde`); FBE.6 apply landed at `364c37d`; FBE.6 seal HALTED on Surface FBE.6 #6 pre-existing debt; parent §8 backfill for FBE.6 outcome at `194798e`.
**BASELINE (pre-build tip):** `194798e` — current canonical pos-v2 HEAD (the FBE.6 §8 backfill commit).

---

## 1. Summary / TLDR

FBE.8 closes the FBE.6 FOLDBACK and the pre-existing FBE.4/FBE.5 seal-debt that blocked FBE.6's seal commit. Four buckets, all narrowly scoped:

1. **Bucket 1 — README + getting-started.md install flow.** The current docs say `pip install -e framework/tools/loam` then `loam init .` — this fails because `loam-init` is a separate package. Fix: redirect both docs to `pip install -r install-from-source.txt` (the FBE.4-ratified install entry point). Doc-only edits, surgical to the install lines + adjacent prose.
2. **Bucket 2 — `framework/tools/loam/` dev-vocabulary scrub.** `README.md`, `__init__.py`, `cli.py` carry `pos-amend` / `loam-amend` / `Phase 4` / amendment-number references that FBE.5's scrub didn't include. Same vocabulary substitution FBE.5 used.
3. **Bucket 3 — Two cosmetic HIGHs.** `framework/primary-persona/pyproject.toml` comment block (amendment numbers + memory-graphiti); `framework/primary-persona/src/loam/primary_persona/session_start_gate.py` line 60 area (`docs/rebuild/` reference visible to public users).
4. **Bucket 4 — FBE.6 seal-debt closure.** H19 admit-list missing FBE.4's `install-from-source.txt` (single addition); HC#4 byte-content samples for the two pyprojects FBE.5 edited but didn't retire-and-rebaseline (2 SHA literal updates + comment additions). Both pre-existed on FBE.5b's seal `48bb7e2`; FBE.6 didn't introduce them but its seal was blocked by them.

Every edit maps to a named AC. ODD §2.5 negative AC: nothing else.

**Sealed-component fence (verified at sub-plan time, see §6 file-by-file map):**
- `framework/tools/loam/` — Bucket 2 (loam-cli README + 2 source docstrings/comments).
- `framework/primary-persona/` — Bucket 3 (pyproject comment scrub + session_start_gate.py comment scrub).
- `framework/scope-of-work/` — Bucket 4 byte-content sample retire-and-rebaseline (only its sample line in HOL's HC#4 test, NOT scope-of-work source itself).
- `framework/hands-off-lifecycle/` — Bucket 4 (H19 admit-list addition + HC#4 sample SHA updates land in HOL test files).
- README.md + `docs/getting-started.md` — Bucket 1 (universal-paths admission, both pre-admitted in workspace-bootstrap fence-test's `allowed_files` per FBE.2c precedent).

---

## 2. Halt-and-surface BEFORE build

### Surface #1 (no halt — recorded; install-from-source.txt is the v0.1.0 entry point per FBE.4's ratification)

The dispatcher's brief explicitly names `pip install -r install-from-source.txt` as the working flow (BLOCKER-FBE6.1 evidence). FBE.4 ratified this as the v0.1.0 install entry point (commit `cfc9ed4`); `docs/install-from-source.md` carries the prose guide; the README + getting-started.md just don't mention it. Bucket 1 is doc-only — point both docs at `install-from-source.txt`. README's quickstart `pip install -e framework/tools/loam` line replaces with `pip install -r install-from-source.txt`. Getting-started.md's "Five-step bootstrap" §2 retitles + replaces the install line; the surrounding prose paragraph (lines 64-78 area, "The loam CLI is shipped inside the cloned framework tree...") rewrites to describe the in-tree `-r install-from-source.txt` walk; the troubleshooting note at lines 169-172 ("`loam: command not found` after `pip install -e framework/tools/loam`") updates the trigger-command reference.

### Surface #2 (no halt — recorded; loam-cli README is heavy — full rewrite vs surgical scrub trade-off)

`framework/tools/loam/README.md` is 511 lines, titled "loam (amend subcommand)", and is heavily structured around the dev-side amend workflow. Two viable shapes for Bucket 2:

- **Path A (surgical scrub):** keep the README's structure; substitute vocabulary (`pos-amend` → `loam amend`; `pos-v2 workspace` → `loam workspace`; `Amendment #N` / `M1g` references → drop or rephrase user-facingly; `docs/plans/...` cross-links → drop). Easier to verify; preserves the substantial dev-side reference value for anyone reading the source.
- **Path B (full rewrite as public-facing surface):** start over with a short stranger-facing summary (`loam` is the unified CLI; `loam amend` is the dev-mode subcommand; see `docs/install-from-source.md` for install). Cleaner stranger experience; loses the structured reference.

**Decision (autonomous, builder's call per ODD §1.1):** **Path A — surgical scrub.** Rationale: (a) the README is admitted by FBE.2 to ship; rewriting it removes legitimate reference value the dev-side audience uses; (b) the dispatcher's brief names "scrub" not "rewrite" ("Same scrub vocabulary FBE.5 used"); (c) Path A is verifiable via the same `git grep` invocations FBE.5 used; (d) Path B introduces a substantive opinion shift (what should the loam-cli README say to strangers?) that's larger than FBE.8's stated scope. Path B candidate: FUTURE_IDEAS_DRAFT entry "loam-cli README rewrite as public-facing surface (v0.1.x doc-quality lane)".

### Surface #3 (no halt — recorded; pyproject comment block — full removal vs vocabulary scrub)

`framework/primary-persona/pyproject.toml` lines 16-22 carry an 8-line comment block referencing "Amendment #48", "amendment #47", "memory-graphiti service", `<workspace>/.mcp.json`, `memory-system/.venv`, and "D5: floating bound risks protocol drift". The block annotates the `mcp==1.27.0` pin, explaining its origin. Two shapes:

- **Path A (vocabulary scrub):** drop amendment numbers + memory-graphiti references; keep the pin-rationale prose ("Pinned to 1.27.0 to match the host MCP service version; update in lockstep with that service's pin").
- **Path B (full removal):** drop the entire comment block; the pin alone is sufficient.

**Decision (autonomous, builder's call per ODD §1.1):** **Path A — vocabulary scrub.** Rationale: the pin-rationale prose has structural value for anyone debugging an `mcp` version mismatch; dropping the entire block removes legitimate operational context. The dispatcher's brief language is "scrub" — Path A matches.

### Surface #4 (no halt — recorded; session_start_gate.py comment refers to two surfaces)

Lines 56-66 carry the `_FALLBACK_BASELINE_PATHS` comment block referencing "docs/odd-methodology.md", "docs/odd-in-loam.md", "docs/VALUE_PROPOSITION.md", "docs/STATE.md", "docs/rebuild/** = excluded entirely", "publish-mode manifest", "M-FBM" — multiple dev-only path leaks. Lines 164-169 also contain `docs/plans/` references in the docstring of `enumerate_amendments_in_flight`. The dispatcher's brief names "session_start_gate.py contains `docs/rebuild/` reference" — singular. **Decision:** scrub BOTH locations (lines ~56-66 fallback-baseline comment block AND the docstring at lines 164-169) within the named bucket — both are visible to public users reading the source, both reference `docs/rebuild/` which doesn't exist in synth, and the surrounding scope is the same comment-prose-cleanup act. Within "adjacent prose" per dispatcher's halt-trigger #3.

### Surface #5 (no halt — recorded; H19 admit-list addition is single-line; HC#4 retire-and-rebaseline is 2-SHA replace)

Verified at FBE.6 status time (Surface FBE.6 #6) and re-verified pre-build:

- **H19:** `framework/hands-off-lifecycle/tests/test_cross_cutting.py` line 134 area (the `allowed = { ... }` literal in `test_H19_diff_scope_covers_only_approved_surfaces`) carries top-level admissions for README.md, .claude, docs, framework, etc. Adding `"install-from-source.txt"` to the set (single line addition + brief comment) closes FBE.4's gap. The path was added at FBE.4's source delta `cfc9ed4` but never made it into H19's admit list.
- **HC#4:** `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py` lines 144-148 (primary-persona/pyproject.toml expected SHA) + lines 203-207 (scope-of-work/pyproject.toml expected SHA). FBE.5's source delta `8032348` edited both pyprojects' `description` fields; FBE.5 didn't update these expected SHAs. Replace `"0181ab99..."` with the current actual SHA `"50b0c15cb7f028f636dbf3816f6cf2cdcc1f71afb2d97c2f23e4b5406405c28f"` (primary-persona) and `"1f97cf7a..."` with `"f847bf944381f8efadb873cd1199782a4cb5b2450afd7be081445064b41f0305"` (scope-of-work). Add an FBE.5/FBE.8-attribution comment line per the file's existing comment-style pattern.

Both edits land in HOL's test file (`framework/hands-off-lifecycle/tests/`) — fence component is `hands-off-lifecycle`. Bucket 3's primary-persona pyproject scrub edit happens BEFORE the HC#4 sample update (so the sample captures the post-FBE.8 byte content; if the order reversed, the SHA would re-stale immediately).

### Surface #6 (no halt — recorded; primary-persona pyproject scrub causes a 3rd SHA bump on the same file)

The HC#4 sample for primary-persona/pyproject.toml will need to capture the byte content AFTER FBE.8's Bucket 3 comment-scrub edit, NOT just FBE.5's pre-FBE.8 description-only edit. Sequencing: edit primary-persona/pyproject.toml comment first → compute new SHA → write that SHA into HC#4 sample. Same for scope-of-work — but Bucket 3 doesn't touch scope-of-work source (the scope-of-work pyproject scrub already landed in FBE.5). Scope-of-work SHA captures the FBE.5 post-edit state (current actual SHA `f847bf94...` per `python3 -c "import hashlib; ..."`).

### Surface #7 (no halt — recorded; partner-prefix gap precedent — apply tool may need hand-corrective)

Per FBE.4 (`0c4d9a0`) and FBE.5 (`e20445f`): `loam amend apply` derives `partner_prefixes` assuming `framework/<name>/` shape. FBE.8's fence components: `framework/tools/loam/`, `framework/primary-persona/`, `framework/hands-off-lifecycle/`. All canonical `framework/<name>/` shape. `framework/tools/loam/` may again surface the "loam-cli's prefix is `framework/tools/loam/` not `framework/loam/`" gap (per FBE.5 corrective `e20445f` precedent). Strategy: run `loam amend apply` first; if it derives wrong prefix and the seal fails on partner-prefix, apply hand-corrective per FBE.4/FBE.5 precedent. Build-time vigilance, not pre-build halt.

### Surface #8 (no halt — recorded; seal-narrative target — HOL canonical for FBE.x)

Prior FBE.x seals used `framework/hands-off-lifecycle/seals/SEAL_COMMIT.<slug>` (FBE.6 wrote `SEAL_COMMIT.v0-1-0-foldback-fbe6`). FBE.8 follows the same pattern: narrative anchor at `framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe8`. NEW file. Lands inside the `hands-off-lifecycle` fence component (H19's admit-list update + this new seal-anchor file land in the same fence).

---

## 3. Spec-objective placement

**Binds to:**
- **AC.PO.1 + AC.PO.2** (prime objective per `docs/VALUE_PROPOSITION.md`) — closing the "stranger reads README, runs the documented install, reaches an empty subcommand list" failure mode (BLOCKER-FBE6.1) AND the "stranger reads loam-cli's source dir README and is confused by amendment vocabulary" mode (BLOCKER-FBE6.2). v0.1.0 GO blocks on both.
- **FBE.6 reviewer BLOCKERs** (per FBE.6 status §Reviewer verdict + FBE.6 sweep report §4) — BLOCKER-FBE6.1 + BLOCKER-FBE6.2 + HIGH-FBE6.1 + HIGH-FBE6.2.
- **Surface FBE.6 #6** (FBE.6 status §Halt-and-surface) — pre-existing FBE.4 H19 admit gap + FBE.5 HC#4 retire-and-rebaseline gap; both blocked FBE.6's seal commit.
- **AC.FBE.8.* (this plan §4)** — every AC ladders to the same parent.

**Ladders to:** AC.FBE.8.* → FBE.6b (re-runs sweep + smoke + reviewer post-FBE.8) → M12 publish-flip → AC.PO.1 + AC.PO.2.

---

## 4. Acceptance criteria (FBE.8.*)

AC family `AC.FBE.8.*` — collision-safe (no prior amendment uses `AC.FBE.8.*`).

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.FBE.8.1** (Bucket 1) | README.md and `docs/getting-started.md` install flow describes `pip install -r install-from-source.txt` as the install step (replacing the `pip install -e framework/tools/loam` flow). Edits stay surgical to the install lines + immediately-adjacent prose; the surrounding section structure (Quickstart / Five-step bootstrap) preserved. | (a) `git grep -F "pip install -r install-from-source.txt" README.md docs/getting-started.md` returns ≥1 hit per file; (b) `git grep -F "pip install -e framework/tools/loam" README.md docs/getting-started.md` returns 0 hits (the broken flow is gone); (c) Smoke (AC.FBE.8.7 below) verifies the documented flow now actually works end-to-end. |
| **AC.FBE.8.2** (Bucket 2 — README) | `framework/tools/loam/README.md` no longer contains `pos-amend`, `loam-amend` (as standalone command name vs `loam amend` subcommand reference), `Amendment #N`, `M1g`, `M-series`, `pOS v2`, `pos-v2 workspace`, `loam-rename-decisions.md`, `docs/plans/` literal references. The README's amend-subcommand reference value preserved (Path A surgical scrub per Surface #2). | `git grep -E "pos-amend|loam-amend [^s]|Amendment #|M1g|M-series|pOS v2|pos-v2 workspace|loam-rename-decisions|docs/rebuild/" framework/tools/loam/README.md` returns 0 hits. |
| **AC.FBE.8.3** (Bucket 2 — sources) | `framework/tools/loam/src/loam_cli/__init__.py` and `framework/tools/loam/src/loam_cli/cli.py` no longer contain `pos-amend`, `Amendment #N`, `M1g`, `loam-rename-decisions.md`, `docs/plans/`, `plugins/dev-sdlc/tools/loam-amend/` (the path leak in cli.py line 16) literal references. Public-facing module docstrings preserved in shape. | `git grep -E "pos-amend|Amendment #|M1g|loam-rename-decisions|docs/rebuild/|plugins/dev-sdlc/tools/" framework/tools/loam/src/loam_cli/__init__.py framework/tools/loam/src/loam_cli/cli.py` returns 0 hits. |
| **AC.FBE.8.4** (Bucket 3 — primary-persona pyproject) | `framework/primary-persona/pyproject.toml` no longer contains `Amendment #N`, `amendment #N`, `memory-graphiti`, `memory-system/.venv`, `<workspace>/.mcp.json` literal references in any comment block. Pin-rationale prose preserved (per Surface #3 Path A). The `description` field is unchanged from FBE.5's post-scrub state. | `git grep -E "Amendment #|amendment #|memory-graphiti|memory-system/.venv|<workspace>/.mcp.json" framework/primary-persona/pyproject.toml` returns 0 hits. `git diff BASELINE..SEAL_COMMIT -- framework/primary-persona/pyproject.toml` shows changes only inside the targeted comment block (no `description` edit, no `dependencies` shape edit). |
| **AC.FBE.8.5** (Bucket 3 — session_start_gate.py) | `framework/primary-persona/src/loam/primary_persona/session_start_gate.py` comment + docstring scrub removes `docs/rebuild/` literal references in the lines 56-66 fallback-baseline comment block AND the lines 164-169 `enumerate_amendments_in_flight` docstring. Behaviour preserved (the `docs/plans/` lookup logic is in CODE not docstring; only prose changes). | `git grep -F "docs/rebuild" framework/primary-persona/src/loam/primary_persona/session_start_gate.py` returns 0 hits. `git diff BASELINE..SEAL_COMMIT -- framework/primary-persona/src/loam/primary_persona/session_start_gate.py` shows only comment + docstring edits (no Python expression / function-body edits). |
| **AC.FBE.8.6** (Bucket 4 — H19 + HC#4) | (a) H19 admit list at `framework/hands-off-lifecycle/tests/test_cross_cutting.py` `test_H19_diff_scope_covers_only_approved_surfaces` includes `"install-from-source.txt"` in the `allowed = { ... }` set; (b) HC#4 byte-content samples at `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py` for `framework/primary-persona/pyproject.toml` and `framework/scope-of-work/pyproject.toml` carry the post-FBE.8 actual SHAs (primary-persona captures FBE.8's Bucket 3 comment scrub; scope-of-work captures FBE.5's pre-existing description scrub). | (a) `git grep -F '"install-from-source.txt"' framework/hands-off-lifecycle/tests/test_cross_cutting.py` returns ≥1 hit; (b) `pytest framework/hands-off-lifecycle/tests/test_cross_cutting.py::test_H19_diff_scope_covers_only_approved_surfaces framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py -x -q` exits 0 against the post-FBE.8 tree. |
| **AC.FBE.8.7** (smoke verify) | Stranger-clone smoke against post-FBE.8 canonical HEAD verifies the README's documented install flow now actually works: `git clone <canonical>; cd <name>; python3.13 -m venv .venv; .venv/bin/pip install -r install-from-source.txt; .venv/bin/loam --version; .venv/bin/loam init <test-ws> --from <clone>` exits 0 at every step; produces `loam 0.1.0`, runnable workspace shape (`framework/`, `workspace/`, `.claude/settings.json={}`), `~/.loam/{dormancy.sqlite, logs/}` scaffolded. | Shell sequence run against the post-FBE.8 canonical HEAD; transcript captured in the FBE.8 status file. (Equivalent to the FBE.6 AC.FBE.6.3 smoke; verifies AC.FBE.8.1 in user-visible terms.) |
| **AC.FBE.8.8** (negative AC — scope discipline) | Edits stay strictly within the four-bucket scope. NO behaviour changes; NO architecture changes; NO test refactors beyond the 2 byte-content sample SHA updates + 1 H19 admit-list addition + 1 narrative-anchor file. NO broader README rewrites; NO doc edits beyond the install-flow lines + adjacent prose. | `git diff BASELINE..SEAL_COMMIT --name-only` produces ONLY paths under: (a) `framework/tools/loam/` (Bucket 2); (b) `framework/primary-persona/` (Bucket 3); (c) `framework/hands-off-lifecycle/` (Bucket 4 + sub-plan seal narrative); (d) `README.md`, `docs/getting-started.md` (Bucket 1, universal-paths admission); (e) `docs/plans/` (sub-plan + manifest + parent §8 backfill via universal prefix admission). |
| **AC.FBE.8.S** (sealed-component fence) | Sealed-component fence: 3 components — `framework/tools/loam/`, `framework/primary-persona/`, `framework/hands-off-lifecycle/`. Plus universal-paths admissions for `README.md` + `docs/getting-started.md` + `docs/plans/`. Every component's diff is sidecar bump + BASELINE bump + the named edits per AC.FBE.8.{2,3,4,5,6}. | `git diff BASELINE..SEAL_COMMIT --name-only` matches the AC.FBE.8.8 path-set; each fence component's `tests/SEAL_COMMIT` advances via `loam amend seal`; each fence component's `tests/test_no_sealed_amendments.py` BASELINE bumps via `loam amend apply`. |

**ACs deliberately out of scope (NOT in FBE.8):**
- Behaviour code edits anywhere (negative AC.FBE.8.8).
- Broader README rewrite (Surface #2 Path B candidate; FUTURE_IDEAS_DRAFT for v0.1.x doc-quality lane).
- Other dev-only tool description scrubs (FBE.5 Surface #1 deferred set; not in FBE.8 scope).
- M12 publish-flip (gated behind FBE.6b GO).
- FBE.6b re-runs (separate dispatch post-FBE.8 seal).

---

## 5. Three-lens analysis

### Lens 1 — Claude-leverage-first
The fix shape is doc-only + cosmetic source scrub + test admit-list update — no Claude-native primitive to lean on, no extension surface. Lens 1 is informational here: FBE.8 doesn't add Claude-leverage; it removes friction blocking the v0.1.0 publish that itself enables Claude-leverage primitives downstream. Lens 1 PASS by composition (every prior FBE.x amendment paid the Lens 1 cost; FBE.8 closes their cycle).

### Lens 2 — Harness + primary-persona value
- **Primary-persona test:** PASS. The four buckets together are the difference between "stranger reads README, runs the documented install, hits exit-2 within 30s" and "stranger reads README, runs the documented install, reaches a working `loam --version` + first-session greeting". Translation burden drops materially (the README's literal commands now work).
- **Harness test:** PASS by composition. The toolkit gains nothing new structurally, but the install path that delivers the toolkit becomes truthful — the harness is reachable.

### Lens 3 — ODD authoring
Outcome ACs only (§4); method (which exact line to edit, which exact phrasing to substitute) is the builder's call but constrained by the FBE.5 vocabulary substitution table + the file-by-file map below. Per ODD §2.5: every line of the diff maps to AC.FBE.8.{1,2,3,4,5,6}. No defensive code; no other doc edits.

### Lens 4 — Prompt scope ↔ confidence
High confidence in outcome shape: the dispatcher's brief named the 4 buckets explicitly + the precise files + the verification mechanism. Tight scope. The single uncertainty point is whether the loam-cli README scrub is "surgical" or "rewrite" (Surface #2) — resolved by Path A per the brief's "scrub" framing + reference-value preservation.

### Lens 5 — Swarming
FBE.8 has natural decomposition opportunities (4 buckets are independent), but every bucket's edit is small enough that decomposition adds only coordination overhead — running all 4 buckets in one main-thread sequence is faster than spawning 4 sub-agents. Per F3 stopping criterion: stop when split adds only coordination overhead. `max_planner_depth = 0` (single-agent build). Model = Sonnet (default; no rationale needed).

---

## 6. File-by-file map

### Bucket 1 — README.md + docs/getting-started.md (universal admission)

**`README.md`:**
- Quickstart block at lines 31-45: replace step 2 (`pip install -e framework/tools/loam`) with `pip install -r install-from-source.txt`. Step 3 (`loam init .`) preserved. Single-line install change + adjacent prose minor refresh ("Install loam and its components" → "Install loam from the cloned tree" or similar).

**`docs/getting-started.md`:**
- Section §2 ("Install the loam CLI") at lines 63-78: rewrite to point at `install-from-source.txt` (Python 3.13 venv + `pip install -r install-from-source.txt`). Drop the "global pipx-style install will land in a later v0.1.x" parenthetical (no longer accurate; the in-tree path IS the v0.1.0 install path). Reference `docs/install-from-source.md` for the prose guide / troubleshooting.
- Common-first-run-problems at lines 169-172: update the trigger-command reference (`pip install -e framework/tools/loam` → `pip install -r install-from-source.txt`).

**Edit scope:** stays within named install-flow lines + immediately-adjacent prose. NO architectural restatement; NO Quickstart restructure; NO new sections.

### Bucket 2 — framework/tools/loam/ (single fence component)

**`framework/tools/loam/README.md`:**
- Title: "loam (amend subcommand)" → "loam — unified CLI for the loam framework" (or "loam — amend subcommand reference" — public-facing framing without `pos-amend` baggage).
- Opening prose lines 1-10: rewrite to drop "Amendment-dispatch tooling for pos-v2" (`pos-v2`-vocab) + the `docs/plans/amendment-22-pos-amend-cli.md` cross-link + the `/tmp/claude-output/...` cross-link. Replace with public-facing summary ("`loam amend` is the dev-mode amendment-dispatch subcommand of the unified `loam` CLI").
- "Run" block lines 13-86: substitute `pos-v2 workspace` → `loam workspace`; preserve the `.venv/bin/loam` invocation pattern + the `loam amend` subcommand surface; drop "M1g sealing time" / "post-rename" framing if present.
- "Manifest schema (v1)" + "Manifest schema (v2)" + "Usage example" + remaining sections: substitute `pos-amend` → `loam amend`; `Amendment #N` → drop or rephrase ("an amendment" generic); `M-series` references → drop. Preserve technical content (manifest fields, exit codes, subcommand surface).
- Cross-references to `docs/plans/...` and `docs/archive/component-research/...`: drop or replace with the closest public-facing equivalent (e.g. `docs/install-from-source.md` for the install context). The dev-only docs don't ship in synth; cross-linking them from a shipping README is the leak.

**`framework/tools/loam/src/loam_cli/__init__.py`:**
- Module docstring (lines 1-14): replace "pos-amend CLI per loam-rename-decisions.md Tier-1 #6" → "the amendment-dispatch tooling provided by the dev-sdlc plugin"; drop "M1g sealing time" / "M1g rename plan" references; drop the cross-link to `docs/plans/oss-v0-1-0-publish-rename-1g.md` and `docs/plans/amendment-22-pos-amend-cli.md`. Public-facing one-paragraph docstring.
- `__version__ = "0.1.0"` preserved verbatim.

**`framework/tools/loam/src/loam_cli/cli.py`:**
- Module docstring (lines 1-26): scrub the `loam-amend` reference (line 16: "is itself shipped by the dev-sdlc plugin at `plugins/dev-sdlc/tools/loam-amend/`") — rephrase as "The `loam amend` subcommand is provided by the dev-sdlc plugin"; drop the in-tree path leak (`plugins/dev-sdlc/tools/loam-amend/`) — the entry-point group reference is sufficient.
- Code body (functions `_discover_subcommand_builders`, `_build_parser`, `main`): inline comments at lines 56-58 reference "plan §11 finding #2" — drop that cross-reference (dev-only paper trail; replace with the in-prose intent: "discovery failures must not break top-level invocation").
- Behaviour preserved verbatim (no Python expression or function-body logic change).

### Bucket 3 — framework/primary-persona/ (single fence component)

**`framework/primary-persona/pyproject.toml`:**
- Comment block at lines 16-22 (the 8-line `mcp==1.27.0` annotation): scrub `Amendment #48`, `amendment #47`, `memory-graphiti service`, `<workspace>/.mcp.json`, `memory-system/.venv`, `D5: floating bound risks protocol drift`. Preserve the pin-rationale prose ("Pinned to 1.27.0 to match the host MCP service's pin; update in lockstep with that service.").
- `description = "Primary-persona layer for loam — ..."` preserved verbatim from FBE.5's post-scrub state.
- `dependencies = [...]` shape preserved (the `mcp==1.27.0` pin and the `loam-scope-of-work` bare-name dep stay).

**`framework/primary-persona/src/loam/primary_persona/session_start_gate.py`:**
- Comment block at lines 53-67 (the `_FALLBACK_BASELINE_PATHS` annotation): scrub `docs/odd-methodology.md`, `docs/odd-in-loam.md`, `docs/VALUE_PROPOSITION.md`, `docs/STATE.md`, `docs/rebuild/** = excluded entirely`, `publish-mode manifest`, `M-FBM`, `AC.OSS.3`. Replace with public-facing prose ("Fallback baseline paths used when CLAUDE.md is absent or its session-start-discipline section is unparseable. Defence-in-depth only; the dynamic CLAUDE.md parse is the authoritative path.").
- `_FALLBACK_BASELINE_PATHS = ("docs/design/odd.md",)` tuple preserved verbatim.
- Docstring at lines 162-169 (`enumerate_amendments_in_flight`): scrub `docs/plans/` reference. Rewrite as "Return sorted amendment-*.md paths under the workspace's plan directory" without the dev-tree-specific path literal.
- Behaviour preserved (no Python expression change).

### Bucket 4 — framework/hands-off-lifecycle/ (single fence component)

**`framework/hands-off-lifecycle/tests/test_cross_cutting.py`:**
- `test_H19_diff_scope_covers_only_approved_surfaces` at line 134 area (the `allowed = { ... }` literal): add `"install-from-source.txt"` to the set, with a one-line comment per the file's existing comment style ("FBE.4 (sealed at `99c03a6`) — admitted at H/L's first opportunity per ODD §10's per-invariant-BASELINE convention; the file lives at the canonical root and was added by FBE.4's source delta `cfc9ed4`."). Single addition.

**`framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py`:**
- Line 148 (primary-persona/pyproject.toml expected SHA): `"0181ab99319a19bd70f262d030d60f0fe74ab325d833706ba33c1bc656cb1ca2"` → POST-FBE.8 actual SHA (computed at build time AFTER Bucket 3's primary-persona/pyproject.toml comment scrub lands). Add an `# FBE.5 SHA bump (description scrub) + FBE.8 SHA bump (comment block scrub) — ODD §4 in-band retire-and-rebaseline per `feedback_loose_AC_text_fix_AC_not_implementation`.` comment line per the file's existing convention.
- Line 206 (scope-of-work/pyproject.toml expected SHA): `"1f97cf7a380d1876b416b8a88f06264398296ae176c797ccb0695d8bc6f481cc"` → `"f847bf944381f8efadb873cd1199782a4cb5b2450afd7be081445064b41f0305"` (the verified actual SHA per current FBE.5-post tree). Add an `# FBE.5 SHA bump (description scrub) — ODD §4 in-band retire-and-rebaseline.` comment line.

**`framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe8`:**
- NEW file. Narrative anchor for FBE.8's seal commit. Content captures: 4 buckets closed, AC surface, scope-discipline negative AC, cross-link to FBE.6 status + FBE.6 sweep report.

### Plan-doc + manifest (universal_paths.prefixes: `docs/plans/`)

- `docs/plans/v0-1-0-foldback-scope-expansion-fbe8.md` (this file, NEW commit).
- `docs/plans/v0-1-0-foldback-scope-expansion-fbe8.manifest.yaml` (NEW commit).

### Parent plan-doc backfill (post-seal, separate commit)

- `docs/plans/v0-1-0-foldback-scope-expansion.md` §8 — ADD a new `### FBE.8 — close FBE.6 reviewer BLOCKERs + HIGH cosmetics + FBE.6 seal-debt` subsection with apply commit SHA + seal commit SHA + AC surface + verification summary; update the closing "Remaining sequence:" line to drop FBE.8 (now done) and lead with FBE.6b.

### Sidecar bumps within sealed-component fence (3 total)

- `framework/tools/loam/tests/SEAL_COMMIT` advances to FBE.8 seal SHA via `loam amend seal`; `framework/tools/loam/tests/test_no_sealed_amendments.py` BASELINE literal bumps via `loam amend apply`.
- `framework/primary-persona/tests/SEAL_COMMIT` advances + BASELINE bumps via apply.
- `framework/hands-off-lifecycle/tests/SEAL_COMMIT` advances + (per H19 frozen-baseline convention) BASELINE does NOT bump (per amendment #23 frozen-BASELINE design + FBE.6 manifest precedent setting `frozen_baseline: true` for HOL).

**TOTAL fence diff:** ~30-50 LOC source/doc/test edits across 7 files + 3 sidecar bumps + 1 BASELINE bump + 1 NEW seal-narrative file + plan-doc + manifest YAML + parent plan §8 backfill.

---

## 7. Smoke verification

**Smoke (AC.FBE.8.7):** runs POST-seal so it exercises the seal-bumped tree.

```bash
# Smoke proper (mirrors AC.FBE.6.3's flow)
cd /tmp && rm -rf loam-fbe8-test loam-fbe8-test-ws
git clone --branch <branch> --single-branch \
  /Users/lukeivers/ivers-corp-pos-v2 loam-fbe8-test
cd loam-fbe8-test
python3.13 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r install-from-source.txt
.venv/bin/loam --version
.venv/bin/loam init /tmp/loam-fbe8-test-ws --from /tmp/loam-fbe8-test
ls /tmp/loam-fbe8-test-ws/{framework,workspace,.claude}
ls ~/.loam/

# Cleanup
rm -rf /tmp/loam-fbe8-test /tmp/loam-fbe8-test-ws
```

Expect:
- Every step exits 0.
- `.venv/bin/loam --version` prints `loam 0.1.0`.
- `loam init` produces a runnable workspace shape (`framework/`, `workspace/personas/primary/`, `.claude/settings.json={}`).
- `~/.loam/` shows `dormancy.sqlite` + `logs/`.

**Failure modes:**
- Any step exits non-zero → halt; surface; do not iterate (FBE.6's smoke worked end-to-end on the dispatcher's flow; FBE.8 only changes the documented entry point — if it breaks, something else regressed).

---

## 8. Hard constraints

- 3 sealed-component sidecars in fence (`framework/tools/loam/`, `framework/primary-persona/`, `framework/hands-off-lifecycle/`) + universal-paths admission for README.md + docs/getting-started.md + docs/plans/.
- No new external runtime deps.
- No `git commit --amend` per `feedback_no_amend_in_agent_dispatches`.
- `loam amend apply` invoked BEFORE seal commit per `feedback_dispatch_explicit_pos_amend_apply`.
- AC-prefix `AC.FBE.8.*` (collision-safe).
- Auto-memory `MEMORY.md` NOT touched.
- Component-scoped test rerun per `feedback_amendment_dispatch_speedups`: only the 3 fence components' tests run post-seal.
- Per FBE.4/FBE.5 partner-prefix gap precedent: `framework/tools/loam` may surface the same gap (apply tool derives `framework/loam/` not `framework/tools/loam/`); apply hand-corrective if it recurs.
- HOL fence carries `frozen_baseline: true` per FBE.6 + amendment #23 convention.
- Negative AC.FBE.8.8: no scope expansion beyond the 4 buckets; no broader README rewrite; no behaviour code edits.
- ODD §2.5 — every line of the diff maps to AC.FBE.8.{1..6}. No defensive code for cases ACs don't name.

---

## 9. Out of scope (per ODD §2.5)

- Behaviour code edits anywhere (negative AC.FBE.8.8).
- Broader README rewrites (loam-cli README full-rewrite is FUTURE_IDEAS_DRAFT candidate per Surface #2 Path B).
- Other dev-only tool pyproject `description` scrubs (FBE.5 Surface #1 deferred set).
- Edits to other components' source files beyond Bucket 3's two primary-persona files.
- M12 publish-flip — gated behind FBE.6b GO; separate dispatch.
- FBE.6b sweep + smoke + reviewer re-run — separate dispatch post-FBE.8 seal.
- Backfilling FBE.6's pending seal commit — FBE.6b path forward per FBE.6 status §Path forward Decision C.

---

## 10. Halt-and-surface (during build)

Per `feedback_subagent_odd_violation_halt`:

- **HT-1:** WD drifts to pos3 → halt immediately.
- **HT-2:** Scope expands beyond the 4 buckets → halt + surface.
- **HT-3:** Doc edits drift beyond the install-flow lines + adjacent prose → halt + surface.
- **HT-4:** More than 4 BLOCKER+HIGH items from FBE.6 surface during build → halt + surface; FBE.8 might be the wrong shape.
- **HT-5:** Sealed-component fence breach beyond plan-named (the 3 fence components + the universal admissions) → halt + surface.
- **HT-6:** Partner-prefix bug recurs → apply hand-corrective per FBE.4/FBE.5 precedent (`0c4d9a0` / `e20445f`).
- **HT-7:** Build cycle exceeds 80 min wall-clock → halt with partial findings.
- **HT-8:** Post-edit smoke (AC.FBE.8.7) regresses (any step exits non-zero) → halt + surface.
- **HT-9:** ODD §2.5 violation discovered in any touched file → halt + surface; do NOT silently extend or fix in-band.

---

## 11. Risks

- **Risk: HC#4 SHA recompute drift.** If the primary-persona pyproject is edited multiple times during build (e.g. iterative scrub passes), the captured SHA would re-stale. Mitigation: edit primary-persona/pyproject.toml comment exactly once; THEN compute SHA; THEN write into HC#4 sample. Ordered ladder per Sequencing §12.
- **Risk: loam-cli README surgical scrub leaks dev vocabulary on subtle phrasings.** FBE.5's grep hit some literals but not all of them; the same risk applies here. Mitigation: AC.FBE.8.2's verification grep covers the named literals; run iteratively against the README until grep returns 0 hits.
- **Risk: Partner-prefix gap recurs for `framework/tools/loam`.** Per FBE.5 corrective `e20445f` precedent. Mitigation: apply with watchful eye; hand-correct if needed; document in seal narrative.
- **Risk: Bucket 1 doc edits accidentally restructure surrounding prose.** Mitigation: AC.FBE.8.1's verification grep + AC.FBE.8.8's diff scope check; iterate until both pass.
- **Risk: HOL frozen_baseline policy interaction.** Per amendment #23 + FBE.6 manifest, HOL's `BASELINE` literal in `test_cross_cutting.py` is frozen at project-start. Adding `install-from-source.txt` to the admit list does NOT need a BASELINE bump (the H19 admit set widens, BASELINE stays). Mitigation: manifest sets `frozen_baseline: true` for HOL.

---

## 12. Sequencing (commit ladder)

1. **Plan-doc commit** (this file authored alone, NEW commit).
2. **Bucket 2 source edit commit** — single commit covering `framework/tools/loam/README.md` + `framework/tools/loam/src/loam_cli/__init__.py` + `framework/tools/loam/src/loam_cli/cli.py` scrub.
3. **Bucket 3 source edit commit** — single commit covering `framework/primary-persona/pyproject.toml` comment scrub + `framework/primary-persona/src/loam/primary_persona/session_start_gate.py` scrub.
4. **Bucket 4 H19 admit + recompute SHA + Bucket 4 HC#4 sample update commit** — single commit covering: H19 admit-list addition (`install-from-source.txt`) + post-Bucket-3 SHA recompute for primary-persona/pyproject.toml + scope-of-work/pyproject.toml SHA replacement (FBE.5 retire-and-rebaseline) + FBE.8 narrative anchor file (`framework/hands-off-lifecycle/seals/SEAL_COMMIT.v0-1-0-foldback-fbe8`).
5. **Bucket 1 doc edit commit** — single commit covering `README.md` + `docs/getting-started.md` install-flow updates.
6. **Manifest commit** — author `docs/plans/v0-1-0-foldback-scope-expansion-fbe8.manifest.yaml` (3 components: tools/loam, primary-persona, hands-off-lifecycle; HOL `frozen_baseline: true`).
7. **`loam amend apply`** — invoke against the manifest. Produces apply-bookkeeping commit (BASELINE bumps in tools/loam + primary-persona; HOL BASELINE preserved per frozen_baseline; all 3 sidecars advance to BASELINE).
8. **Corrective commit (if partner-prefix gap recurs)** — per FBE.4/FBE.5 precedent.
9. **`loam amend seal`** — produces deterministic seal commit; sidecars advance to seal SHA; narrative appends.
10. **Smoke verification (AC.FBE.8.7)** — POST-seal; verify shipped behaviour against the seal-bumped tree.
11. **Parent plan-doc backfill** — `docs/plans/v0-1-0-foldback-scope-expansion.md` §8 add `### FBE.8` subsection with apply + seal SHAs (separate NEW commit; admitted via `docs/plans/` universal prefix).
12. **Status file write** — `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe8-status-2026-05-03.md` with seal report.

NO `git commit --amend` at any point. NO push to any remote.

---

## 13. References

- **FBE.6 status (Surfaces FBE.6 #1-#6 origin):** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe6-status-2026-05-03.md`.
- **FBE.6 sweep report (BLOCKERs + HIGHs origin):** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-0-foldback-fbe6-sweep-report.md`.
- **FBE.6 sub-plan:** `docs/plans/v0-1-0-foldback-scope-expansion-fbe6.md`.
- **Parent plan:** `docs/plans/v0-1-0-foldback-scope-expansion.md` §8 register FBE.6 row + closing line.
- **FBE.5 sub-plan + manifest (vocabulary substitution table + scrub precedent):** `docs/plans/v0-1-0-foldback-scope-expansion-fbe5.{md,manifest.yaml}`.
- **FBE.4 sub-plan + commit `cfc9ed4` (install-from-source.txt origin):** `docs/plans/v0-1-0-foldback-scope-expansion-fbe4.{md,manifest.yaml}`.
- **FBE.4 partner-prefix corrective `0c4d9a0` + FBE.5 corrective `e20445f` (precedent for partner-prefix gap recovery).**
- **HOL H19 + HC#4 test files:** `framework/hands-off-lifecycle/tests/{test_cross_cutting.py, test_d1_byte_content_match.py}`.
- **install-from-source.txt:** `install-from-source.txt` (canonical root).
- **Memory bullets honoured:**
  - `feedback_plan_before_code` (this is the plan; no code yet).
  - `feedback_no_amend_in_agent_dispatches` (commit ladder uses NEW commits only).
  - `feedback_dispatch_explicit_pos_amend_apply` (apply step explicit in §12).
  - `feedback_subagent_odd_violation_halt` (HT-1 through HT-9).
  - `feedback_amendment_dispatch_speedups` (test rerun scoped to fence components only).
  - `feedback_summarize_and_surface_decisions` (Surfaces 1-8 explicit).
  - `feedback_specific_claims_verified_or_marked_guess` (every "verified at" claim has a path/line citation; SHAs computed empirically not guessed).
  - `feedback_loose_AC_text_fix_AC_not_implementation` (HC#4 retire-and-rebaseline pattern is exactly this rule).
  - `feedback_critical_thinking_on_deviations` (Surface #2 + #3 weighed Path A vs Path B by outcome × cost × risk).
  - `feedback_value_proposition_as_prime_objective` (Buckets 1-4 ladder to AC.PO.1 + AC.PO.2 via FBE.6b → M12).
  - `feedback_principle_conflict_resolution_multi_signal` (Surface #2 Path A vs Path B resolved via the multi-signal process).

---

## 14. AI-time band

- Predicted: **30–60 min, midpoint 45 min**; dispatch hard cap 80 min.
- Justification: 4 small buckets across 7 files + 3 sidecar bumps + 1 narrative file + manifest YAML + apply (3-fence; partner-prefix watchful eye) + seal + smoke + parent §8 backfill + status file. Per rubric: 3-component amendment with surgical scrubs is closer to 30-45 min midpoint; widen upper bound for the smoke verification + potential partner-prefix corrective.

---

## 15. Method-decision register (post-build)

(Populated as commits land.)

- Plan-doc commit: `<TBD>`.
- Bucket 2 source edit commit: `<TBD>`.
- Bucket 3 source edit commit: `<TBD>`.
- Bucket 4 H19 + HC#4 + narrative commit: `<TBD>`.
- Bucket 1 doc edit commit: `<TBD>`.
- Manifest commit: `<TBD>`.
- Apply commit: `<TBD>`.
- Corrective commit (if needed): `<TBD>`.
- Seal commit: `<TBD>`.
- Parent plan-doc §8 backfill commit: `<TBD>`.

---

*End of FBE.8 sub-plan-doc. Ready to build.*
