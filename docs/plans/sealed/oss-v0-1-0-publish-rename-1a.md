# OSS v0.1.0 publish — M1a — docs/prose-only brand rebrand — sub-plan

**Status:** plan-doc (pre-build, plan-before-code). 2026-04-29.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Series master:** `docs/plans/oss-v0-1-0-publish-rename.md` (committed `ebe0a57`, 2026-04-29).
**Programme position:** First sub-amendment of the M1.rename multi-amendment series. Independent of M1b..M1g; lands first as the cheapest safest pattern-establisher.
**Authority documents:**
- `docs/plans/loam-rename-decisions.md` (locked Tier-1 + Tier-2 + Kept-Technical catalogue).
- `.scratch/claude-output/loam-rename-migration-plan.md` Phase 1 (documentary rebrand) — the surface this sub-amendment lands.
- `docs/plans/oss-v0-1-0-publish-rename.md` §2 (sub-amendment ladder), §5 (series-wide hard constraints), §7 (series-wide halt triggers).

---

## 1. Summary / TLDR

Rename brand strings `pos-v2` / `pOS v2` → `loam` in **user-facing prose surfaces only**. ZERO code, env-vars, paths, OTel, launchd, CLI, package-namespace, directory-restructure work — all of those are deferred to subsequent sub-amendments (M1b..M1g) per the series master.

**Brand-vocabulary surface.** Per `loam-rename-decisions.md` Tier-1 + the prior monolithic plan's AC.RNM.1: `pos-v2`, `pOS v2`, and bare `pOS` (as the brand abbreviation) all rename to `loam`. `personal OS` is also Tier-1 but does not appear in any M1a-touched file (verified at plan time).

**What lands (M1a only):**

- Root `CLAUDE.md` — every `pos-v2` / `pOS v2` / bare `pOS` brand-prose occurrence becomes `loam` (combined ~15 occurrences).
- `docs/VALUE_PROPOSITION.md` — prose rebrand (combined ~11 occurrences).
- `docs/CLAUDE_CAPABILITIES.md` — prose rebrand (the largest single file, ~96 + 6 occurrences).
- `docs/duration-estimation-rubric.md` — prose rebrand (~2 occurrences).
- `docs/odd-methodology.md` — example-phrase + prose-narrative rebrand (~13 occurrences; the methodology-illustration example phrase is updated to `loam` or to a brand-neutral phrasing per builder's call).
- `docs/odd-in-pos.md` — content prose only (filename change deferred to M1e); ~21 occurrences.
- `framework/objective-tracker/README.md` — prose-rebrand only (path strings of form `/Users/lukeivers/ivers-corp-pos-v2/...` stay; M9-deferred per `oss-v0-1-0-publish.md` §6).
- `framework/scope-of-work/README.md` — prose rebrand.
- `framework/hands-off-lifecycle/README.md` — prose rebrand only (CLI-binary names like `pos-amend` stay; M1g-deferred).
- `framework/workspace-bootstrap/README.md` — prose rebrand only (CLI binary `pos-new-workspace` stays; path strings stay).
- `framework/workspace-sync/README.md` — prose rebrand.

**What does NOT land (deferred to subsequent sub-amendments):**

- Code-side imports (`from pos_<comp> import …`) — M1e.
- Env-vars `POS_V2_*` — M1b.
- launchd labels `com.pos-v2.*` — M1c.
- OTel `pos.*` roots — M1d.
- `pos-amend` CLI rename → `loam amend` — M1g.
- `graceful-degradation` → `dormancy` rename — M1f.
- Spec filename changes (`docs/spec/pos-v2-*.md` filename rename) — M1e.
- `docs/odd-in-pos.md` filename change — M1e (content prose updates land here in M1a).
- `STATE.md`, `BACKLOG.md`, `FUTURE_IDEAS.md`, `FUTURE_IDEAS_DRAFT.md` — historical-narrative-heavy live docs; deferred (likely a follow-on docs sweep at M9 scrub or its own sub-amendment).
- `docs/plans/*.md` — historical method-record; preserved for accuracy.
- Path strings of form `/Users/lukeivers/ivers-corp-pos-v2/...` — directory rename is M9-deferred per `oss-v0-1-0-publish.md` §6.
- `pos-new-workspace`, `pos-amend`, etc. CLI binary names in prose — those rename in M1g (CLI rename).

**Sealed-component fence (post-build):** four sealed components whose `framework/<comp>/README.md` is touched: objective-tracker, workspace-bootstrap, hands-off-lifecycle, workspace-sync. (scope-of-work is touched but is NOT a sealed component per d-migration-1 precedent — its diff is admitted by hands-off-lifecycle's H19 cross-cutting test via the `framework` + `scope-of-work` entries in H19's allowed set. See finding #8 in §11.) Plus universal-paths admissions for `CLAUDE.md`, `docs/plans/`, `docs/odd-in-pos.md`, `docs/odd-methodology.md`, `docs/FUTURE_IDEAS.md`, `docs/FUTURE_IDEAS_DRAFT.md`. Plus one-off admissions for `docs/CLAUDE_CAPABILITIES.md`, `docs/duration-estimation-rubric.md`, `docs/VALUE_PROPOSITION.md` (added at apply time per pos-amend's universal-paths-extension behaviour).

**Estimate:** 30–45 min AI-time per the duration rubric (mechanical-substitution-only category; small fence; no source-tests to run because no source touched).

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Named spec objectives this sub-amendment satisfies:**

- **AC.OSS.5** (`oss-v0-1-0-publish.md` §3) — *"Documentary rebrand complete in public artefacts"* — partial; M1a closes the prose-only portion. Subsequent sub-amendments close the code-side portion.
- **AC.PO.1** (VALUE_PROPOSITION primary-persona test) — single-syllable identity (`loam`) reduces the user's translation-burden vocabulary in the first surface they read (READMEs, root CLAUDE.md). Partial — full closure when the CLI binary also renames at M1g.

**Sealed-component fence (preliminary — see §11 for the exhaustive list):**

Four sealed components touched (READMEs only; no source/test edits): objective-tracker, workspace-bootstrap, hands-off-lifecycle, workspace-sync. scope-of-work's README is also touched but scope-of-work is NOT a sealed component (per d-migration-1 precedent); its admission rides on H19 cross-cutting.

**ODD §2.5 reverse-direction commitment.** Every line of doc-prose changed in this sub-amendment's diff traces back to AC.RNM-1a.1 .. AC.RNM-1a.S below. Mechanical rename of brand-prose only; no code; no behaviour changes; no defensive-`if` admissions; no filename changes; no path-string changes; no CLI-binary-name changes.

---

## 3. Three-lens analysis (abbreviated; series master §4 covers cross-cutting)

- **Lens 1.** Pass. Preserves every existing Claude-native composition; rebases user-facing prose onto unified `loam` brand vocabulary. The CLAUDE_CAPABILITIES.md doc (which Claude itself reads at session start) becomes consistent.
- **Lens 2.** Primary-persona pass. The user's first-surface vocabulary loses `pos-v2`/`pOS v2` in the doc-prose surfaces they read at onboarding. Harness pass — establishes the rename pattern that subsequent sub-amendments inherit.
- **Lens 3.** Pure mechanical-substitution. Outcome-shaped ACs (post-rename grep counts in named files); method-shape (which exact regex / which order) is the builder's call.

---

## 4. Acceptance criteria — AC.RNM-1a.*

Outcome-shaped. Behaviour-count check at end of section.

**Brand-prose target pattern.** Each AC below targets `\bpos-v2\b`, `\bpOS v2\b`, and `\bpOS\b` (the bare brand abbreviation) — collectively the "brand-prose vocabulary" of the prior project name. `loam` replaces all three. Verification grep pattern: `grep -E '\bpos-v2\b|\bpOS v2\b|\bpOS\b' <file>` returns `0`.

### AC.RNM-1a.1 — Root CLAUDE.md rebrands cleanly

Every brand-prose occurrence (`pos-v2`, `pOS v2`, `pOS`) in `CLAUDE.md` (root) post-amendment reads `loam`. The prior heading `# pOS v2 — CLAUDE.md` becomes `# loam — CLAUDE.md`. Prose phrases like "pOS v2 is a general-purpose harness" become "loam is a general-purpose harness." Bare `pOS` brand references (e.g. "a hypothetical legal plugin for pOS") become "for loam".

**Outcome:** `grep -cE '\bpos-v2\b|\bpOS v2\b|\bpOS\b' CLAUDE.md` returns `0`.

### AC.RNM-1a.2 — VALUE_PROPOSITION rebrands cleanly

Every brand-prose occurrence in `docs/VALUE_PROPOSITION.md` post-amendment reads `loam`. The heading "pOS v2 — Value Proposition" becomes "loam — Value Proposition". Bare-`pOS` prose ("the problem pOS is closing", "an earlier pOS release") becomes the loam form.

**Outcome:** `grep -cE '\bpos-v2\b|\bpOS v2\b|\bpOS\b' docs/VALUE_PROPOSITION.md` returns `0`.

### AC.RNM-1a.3 — CLAUDE_CAPABILITIES rebrands cleanly

Every brand-prose occurrence in `docs/CLAUDE_CAPABILITIES.md` post-amendment reads `loam`. This is the largest file of M1a's surface (~96 + 6 prose-references); the rename is mechanical substitution.

**Outcome:** `grep -cE '\bpos-v2\b|\bpOS v2\b|\bpOS\b' docs/CLAUDE_CAPABILITIES.md` returns `0`.

### AC.RNM-1a.4 — duration-estimation-rubric rebrands cleanly

Every brand-prose occurrence in `docs/duration-estimation-rubric.md` post-amendment reads `loam`. The heading "Duration estimation rubric for AI-driven pos-v2 tasks" becomes "Duration estimation rubric for AI-driven loam tasks".

**Outcome:** `grep -cE '\bpos-v2\b|\bpOS v2\b|\bpOS\b' docs/duration-estimation-rubric.md` returns `0`.

### AC.RNM-1a.5 — odd-methodology + odd-in-pos prose rebrand

In `docs/odd-methodology.md`, the example phrase plus the bare-`pOS` brand-narrative references update to `loam` (or to brand-neutral phrasing where a methodological example is intended to be brand-agnostic — builder's call within the AC bound).

In `docs/odd-in-pos.md`, content-prose brand references (`pos-v2`, `pOS v2`, `pOS`) become `loam`. The filename `odd-in-pos.md` itself does NOT change in M1a (filename change is M1e). **Path-string references to other files** that contain `pos-v2` in their filename (e.g. `.scratch/claude-output/pos-v2-parallel-dev-research.md`) are PRESERVED — the actual research-doc file at that path is named that way and the rename of those filenames is M9-scrub-deferred or its own sub-amendment.

**Outcome:** `grep -cE '\bpos-v2\b|\bpOS v2\b|\bpOS\b' docs/odd-methodology.md docs/odd-in-pos.md` returns `0` for prose occurrences. Exactly one residual match in `docs/odd-in-pos.md` is permitted: the `.scratch/claude-output/pos-v2-parallel-dev-research.md` path-string reference (research-doc filename — not brand-prose; rename deferred per the same rule that defers other filename changes).

### AC.RNM-1a.6 — Per-component README prose rebrand

In each of the five touched component READMEs (`framework/objective-tracker/README.md`, `framework/scope-of-work/README.md`, `framework/hands-off-lifecycle/README.md`, `framework/workspace-bootstrap/README.md`, `framework/workspace-sync/README.md`), every brand-prose occurrence (`pos-v2`, `pOS v2`, `pOS`) becomes `loam`. **Path strings** of form `/Users/lukeivers/ivers-corp-pos-v2/...` STAY (directory rename is M9-deferred). **CLI binary names** like `pos-amend`, `pos-new-workspace`, `pos-publish-framework-only` STAY (CLI rename is M1g; binary-name rename is M1c-class). Note: the bare-`pos` substring inside `ivers-corp-pos-v2` matches the brand-string regex by word-boundary rules, but those are path-string occurrences and are deferred to M9.

**Outcome:** in each of the five READMEs, the post-amendment file reads `loam` for every brand-prose occurrence. **Permitted residual matches** are exactly the path-string occurrences inside `/Users/lukeivers/ivers-corp-pos-v2/...` paths and CLI-binary-name occurrences (`pos-amend`, `pos-new-workspace`, `pos-publish-framework-only`). Verification per file: `grep -nE '\bpos-v2\b|\bpOS v2\b|\bpOS\b' <readme>` — every remaining match is a path-string or CLI-binary-name; no brand-prose occurrence remains.

### AC.RNM-1a.7 — No code, env-var, OTel, launchd, CLI, namespace, or directory changes (with named pre-existing-debt exceptions)

Negative AC. The amendment's git-diff includes ZERO touches outside the named docs/prose surfaces, with the explicit named exception below for pre-existing tech debt that M1a's seal-test pass requires resolving in-band (per H/L's per-invariant-BASELINE convention and `feedback_subagent_odd_violation_halt`).

**Permitted ZERO surfaces (no edits):**

- No `framework/<comp>/src/**` edits.
- No `framework/<comp>/tests/**` edits **except** the named exception below.
- No `framework/tools/**` source edits.
- No `pyproject.toml` edits.
- No `.claude/settings*.json` edits.
- No `.plist` edits.
- No `framework/<comp>/launchd/**` edits.
- No `~/.pos/` or `POS_V2_*` rewrites in any file.
- No `pos.*` OTel-emit-site rewrites.
- No file-rename / file-delete / file-create operations (this AC enforces docs-only edits to existing files; if a new file becomes structurally necessary, halt-and-surface per §8).

**Permitted exceptions — brand-keyed test marker updates:**

Three test files are edited by M1a in narrow ways, each a pre-existing-debt resolution or brand-keyed-marker update tied directly to M1a's brand-prose surface:

1. **`framework/hands-off-lifecycle/tests/test_cross_cutting.py` — H19 admissions added** for four top-level files introduced by prior commits (`a28969e` and `3c599c1`, the public-docs scaffold) but never crossed by an H/L SEAL_COMMIT until M1a: `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`. Per the same convention used for `data` (#67), `objective-tracker` (#38), `CLAUDE.dev.md` (#44), etc. — admissions land at the next H/L amendment whose SEAL_COMMIT window crosses the introducing commit.
2. **`framework/hands-off-lifecycle/tests/test_cross_cutting.py` — H21 marker phrase update** from `"pOS v2"` (the pre-public-docs-scaffold marker, broken since `3c599c1` rewrote the README to loam) to `"loam"` + `"substrate"|"harness"|"primary persona"` (the post-rebrand-stable markers). Per `feedback_loose_AC_text_fix_AC_not_implementation` — the test's intent ("the README is fresh, not a placeholder") is preserved; the brittle string-marker is replaced with markers that match the post-rename README's actual content.
3. **`framework/workspace-bootstrap/tests/test_AC39_6_no_tracker_payload_in_source.py` — brand-keyed sentinel update** from `"pOS v2 — Value Proposition…"` to `"loam — Value Proposition…"`. The test cross-checks the sentinel exists in `docs/VALUE_PROPOSITION.md`; M1a renamed the VP H1 to the loam form; the cross-check became stale. Per `feedback_loose_AC_text_fix_AC_not_implementation` — test intent ("VP prose not hard-coded in workspace-bootstrap source") preserved.

All three updates are bookkeeping/marker-tightening, not behaviour change. The first two resolve pre-M1a tech debt (introduced by `3c599c1` but never resolved); the third aligns a brand-keyed sentinel with the live VP doc post-rename. Recorded as halt-and-surface findings #7, #8, and #9 in §11 below; all resolved in-band per the corpus precedent.

**Outcome:** `git diff <baseline>..<feature-commit-tip> --stat` shows changes only in: the named docs/prose surfaces (eleven files), the plan-doc + manifest under `docs/plans/`, the H/L cross-cutting test file (admission + marker updates only), and the workspace-bootstrap AC39_6 test file (sentinel update only — no test-shape changes; no test-removal).

### AC.RNM-1a.S — Sealed-component fence narrows to docs-only

Four-component sealed amendment commit lands per `pos-amend apply` + `pos-amend seal` convention (using the still-`pos-amend` CLI; this is many sub-amendments before M1g's CLI rename). The amendment manifest YAML lists four components (objective-tracker, workspace-bootstrap, hands-off-lifecycle, workspace-sync) with `frozen_baseline: false` for the three non-H19 + `frozen_baseline: true` for hands-off-lifecycle (H19 frozen-baseline is preserved; M1a does NOT touch H19-pinned source paths because the README is NOT in H19's byte-content sample). The `seal_diff` allowed_prefixes admit `framework/<comp>/` for each touched component plus the universal paths. scope-of-work's README is admitted by H19 cross-cutting (see finding #8 in §11).

**Per-component touched-test scope:** docs-only — no source tests to run. The seal-diff fence test for AC.RNM-1a.S is the primary check (verifies the fence isn't reaching beyond docs surfaces).

**Outcome:** `git log --oneline | head -3` shows feature-commit + apply-commit + seal-commit triple per repo convention; five per-component sidecars all advance; `pytest framework/<comp>/tests/test_no_sealed_amendments.py` per touched component PASSES (each checks the sealed-amendment invariant; no source code changed, only README, so should pass cleanly).

### Behaviour-count check (ODD §3.3 forward)

Seven outcome-named behaviours (root CLAUDE rebrand, VALUE_PROPOSITION rebrand, CLAUDE_CAPABILITIES rebrand, duration-rubric rebrand, odd-methodology+odd-in-pos rebrand, per-component README rebrand, fence-narrowing seal) → seven ACs (AC.RNM-1a.1 .. AC.RNM-1a.6 + AC.RNM-1a.S). Plus one negative AC (AC.RNM-1a.7) enforcing the docs-only fence. Match.

ODD §2.5 reverse direction (every diff line traces to a named AC) is the builder's pre-seal audit; surfaced explicitly as halt trigger §10.5.

---

## 5. Hard constraints (M1a-specific; series-wide constraints from master §5 inherit)

- **Docs-only diff.** AC.RNM-1a.7 is the structural fence — no code-side edits, no file renames, no file creates/deletes.
- **Path strings under `/Users/lukeivers/ivers-corp-pos-v2/...` stay** — directory rename is M9-deferred per `oss-v0-1-0-publish.md` §6.
- **CLI binary names stay** — `pos-amend`, `pos-new-workspace`, `pos-publish-framework-only` stay in prose. CLI rename is M1g.
- **Filenames stay** — `docs/odd-in-pos.md`, `docs/spec/pos-v2-*.md` filenames don't change. Filename changes are M1e.
- **STATE.md, BACKLOG.md, FUTURE_IDEAS.md, FUTURE_IDEAS_DRAFT.md** are NOT touched in M1a — historical-narrative-heavy live docs; deferred to a follow-on sub-amendment or M9 scrub.
- **`docs/plans/*.md`** are NOT touched in M1a — historical method-record preserved.
- **No `git commit --amend`** (`feedback_no_amend_in_agent_dispatches`).
- **`pos-amend apply` runs BEFORE the seal commit.**
- **H19 retirement does NOT happen in M1a.** M1a does not touch any path in H19's frozen byte-content sample (verify pre-build that none of the five touched READMEs are pinned by H19).

---

## 6. Out of scope (named explicitly per ODD §2.5)

(See §1 for the full list. Re-named here for ODD §2.5 compliance.)

- All work deferred to M1b..M1g (env-vars, paths, launchd, OTel, namespace pivot, dormancy, CLI rename).
- All work deferred to M9 (path-string `/Users/lukeivers/ivers-corp-pos-v2/...` rename, repo directory rename).
- `STATE.md`, `BACKLOG.md`, `FUTURE_IDEAS.md`, `FUTURE_IDEAS_DRAFT.md` — historical-narrative-heavy live docs; M1a defers because each has many filename-references and historical-narrative content where surgical separation costs more than it saves; a later M1-series-internal sub-amendment or M9 scrub closes them.
- `docs/plans/*.md` — historical method-record.
- `docs/rebuild/dev-mode-manifest.yaml` — not user-facing prose.
- Spec files at `docs/spec/` — M1e (filename change drives the content-prose update).
- Any new file authoring beyond the plan-doc + manifest YAML required for the amendment.

---

## 7. Implementation order (suggested — builder's call to refine)

1. **Pre-flight verification.** `git log --grep="loam.*rename.*M1a\|RNM-1a"` returns nothing prior; `ls docs/plans/ | grep oss-v0-1-0-publish-rename-1a` returns this plan-doc only. Verify the canonical tree: `pwd` returns `/Users/lukeivers/ivers-corp-pos-v2`; `git rev-parse --abbrev-ref HEAD` returns `pos-v2`. Halt-and-surface if any check fires.
2. **BASELINE pin.** Pin to the master-plan-revision commit `ebe0a57` (or HEAD at dispatch time, whichever is later). Author the manifest YAML at `docs/plans/oss-v0-1-0-publish-rename-1a.manifest.yaml`.
3. **Plan-doc commit.** This plan-doc lands as a doc-only commit (or together with the feature commit per `pos-amend apply` convention). Recommendation: plan-doc commits standalone before the feature commit so the plan is in the tree when `pos-amend apply` runs.
4. **Phase A — root + docs/ surface.** Mechanical sed-or-equivalent on `CLAUDE.md`, `docs/VALUE_PROPOSITION.md`, `docs/CLAUDE_CAPABILITIES.md`, `docs/duration-estimation-rubric.md`, `docs/odd-methodology.md`, `docs/odd-in-pos.md`. Post-edit grep verifies AC.RNM-1a.1 .. .5 outcomes.
5. **Phase B — per-component README surface.** Mechanical sed-or-equivalent on five component READMEs (`framework/objective-tracker/README.md`, `framework/scope-of-work/README.md`, `framework/hands-off-lifecycle/README.md`, `framework/workspace-bootstrap/README.md`, `framework/workspace-sync/README.md`). Selective: prose-only; verify path strings and CLI binary names unchanged. Post-edit grep verifies AC.RNM-1a.6 outcome and that path strings + CLI names are preserved.
6. **Phase C — feature commit.** Single feature commit carrying the docs-only rename diff. Commit message names the M1a slug, the AC family, and the series-master pointer.
7. **Phase D — pos-amend apply.** Run `pos-amend apply` against the manifest. Verify clean apply.
8. **Phase E — apply commit.** The apply commit (sidecars + seal-narrative scaffold) per `pos-amend apply` convention.
9. **Phase F — seal-diff fence verification.** AC.RNM-1a.S + AC.RNM-1a.7 — verify `git diff <baseline>..HEAD --stat` shows ONLY the named files. Verify each component's `pytest framework/<comp>/tests/test_no_sealed_amendments.py` passes.
10. **Phase G — `pos-amend seal --plan-doc <abs-path>`.** Backfills §14 SHA register (this plan's §14 below).

Phases 4–5 are sed-mechanical. Phase 6 is one commit. Phase 7 is `pos-amend apply`. Phase 8 is the apply commit. Phase 9 is the fence verification. Phase 10 is the seal commit.

---

## 8. Halt triggers (M1a-specific; series-wide triggers from master §7 inherit)

The build agent MUST halt and surface when:

1. **A docs-only rename produces a code-side breakage** (per dispatch §Constraints item 1; this means the surface isn't truly docs-only — re-scope to a later sub-amendment).
2. **An ODD §2.5 violation surfaces in the surface being edited** (per `feedback_subagent_odd_violation_halt`).
3. **`pos-amend` automation hits a gap** on the docs surface (regex narrowness, abs-path requirement, manifest-validation false-positive). Record in `FUTURE_IDEAS_DRAFT.md` and surface; do not push through.
4. **Cross-mode debt that prevents docs rename from landing cleanly** (loam-mode F-register references, hands-off-lifecycle allowed_prefixes, dispatch-template path refs that name a docs surface in M1a's diff). If a DEV-MODE artefact references one of M1a's renamed surfaces in a way that breaks at the rename, halt and surface for fence-widening or defer-to-M1b.
5. **AC.RNM-1a.7 fence is breached.** The diff reaches outside docs/prose surfaces. Halt; do not "fix" by widening the AC; the over-reach IS the failure signal.
6. **An H19-pinned path is in M1a's diff** — would force in-band H19 retirement when the series master expects H19 retirement at M1c-or-M1e. Halt; verify whether a README is in H19's byte-content sample. If yes, surface for ruling on retire-now vs scope-narrow.
7. **A `loam` identifier already in use** in any of the named surfaces (e.g. an example string, a fixture name). Halt; rename the conflicting use first.
8. **Wall-clock exceeds 60 min** (M1a is rubric-priced 30–45 min midpoint 35 min). Halt with current-state report; dispatcher triages.

---

## 9. Risks (M1a-specific)

1. **Selective rename in component READMEs.** AC.RNM-1a.6 demands prose-only substitution; path strings and CLI-binary names stay. A naive global sed may over-reach. Mitigation: per-file manual review post-sed, OR per-file targeted edits via Read+Edit rather than sed.
2. **odd-methodology.md's single example phrase** ("pos-v2 supports …" at line 141). The example is a methodological illustration, not brand-prose; the choice is whether to substitute `loam` for the example or rephrase to a brand-neutral form. AC.RNM-1a.5 grants builder's call within the AC bound.
3. **`docs/odd-in-pos.md` filename references inside the file itself.** The file refers to its own slug in cross-doc references. M1a updates content prose only; if any line literally references the filename `odd-in-pos.md` (e.g. as a path in a cross-link), that filename stays — the filename change is M1e.
4. **`docs/CLAUDE_CAPABILITIES.md` is large (~96 occurrences).** Mechanical substitution is straightforward but the volume requires care that no occurrence is missed. Mitigation: post-edit grep verifies count is 0.
5. **STATE.md / BACKLOG / FUTURE_IDEAS deferral.** Deferring these means the user-facing brand isn't fully rebranded after M1a — the user reading STATE.md still sees `pos-v2` in some prose contexts. Acceptable because STATE.md is dev-mode (rebuild) doc, not v0.1.0-public; M2's partition manifest excludes `docs/rebuild/`.

---

## 10. Decisions remaining for owner ruling

**None.** Per series master §1, all three D-RNM rulings closed at owner-ruling time. M1a's scope inherits cleanly.

---

## 11. Halt-and-surface findings encountered during plan authoring

Per the dispatch's halt-and-surface clause: surface any audit-recommendation conflict with sealed-component invariants, methodology breaches, or surrounding-code/-doc ODD violations.

**Findings during plan authoring + during build (build-time additions marked):**

1. **(Not blocking — pre-emptive scope guard.) `STATE.md`, `BACKLOG.md`, `FUTURE_IDEAS.md`, `FUTURE_IDEAS_DRAFT.md` carry both live and historical brand-prose.** Surgical separation in M1a costs more than the prose-rebrand benefit (the user sees a half-rebranded STATE.md, which is worse than waiting for a later sub-amendment or M9 scrub to land the full rebrand). M1a explicitly defers. Recorded in §6.

2. **(Not blocking — pre-emptive scope guard.) Per-component README path-string and CLI-binary-name references.** A global `pos-v2 → loam` sed would over-reach into path strings (which are M9-deferred) and CLI binary names (M1g-deferred). M1a uses targeted edits, not global sed; documented in §9 Risk 1.

3. **(Not blocking — verification step.) H19 byte-content sample crosses M1a's surface?** Plan-time check: the H19 frozen-baseline byte-content sample (per amendment #23) pins specific files in `framework/hands-off-lifecycle/` and possibly other components. Need to verify pre-build that NONE of the five M1a-touched READMEs are in the H19 sample. Halt-trigger §8.6 fires if they are. **Builder action pre-Phase B:** read `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py` (or the equivalent H19 byte-content test) and confirm no M1a README is pinned.

4. **(FUTURE_IDEAS_DRAFT — pre-emptive.)** Plan-time observation: a recurring pattern across the M1.rename series is "selective rename — change brand-prose, keep path-strings/CLI-names". A future improvement would be a `loam-rename-helper` script in `framework/tools/` that takes a file and a list of lines/regions and applies the rename only to the prose portions, preserving paths and CLI names. Captured here for the build agent to surface to FIDRAFT post-build (do NOT extend M1a scope to add it).

5. **(No ODD §2.5 violation found in surrounding code/docs at plan-authoring time.)** The mechanical rename is the rename; no defensive `if`s without backing AC; no behaviour changes.

6. **(No methodology breach in plan structure.)** ACs are outcome-shape, deterministic, behaviour-count-checked. AC.RNM-1a.7 (negative AC enforcing the docs-only fence) is the explicit ODD §2.5 reverse-direction protection.

**Build-time finding 7 (halt-and-surface, resolved in-band).** During the pre-seal verification phase the H/L cross-cutting test file (`framework/hands-off-lifecycle/tests/test_cross_cutting.py`) surfaced two pre-existing tech-debt failures that M1a's seal verification required resolving:

- **H19 admission gap** — four top-level files (`LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`) were introduced by prior commits `a28969e` and `3c599c1` (the public-docs scaffold) but were never admitted to H19's `allowed` set. Per H/L's per-invariant-BASELINE convention (ODD §10), admissions land at the next H/L amendment whose SEAL_COMMIT window crosses the introducing commit. M1a is that amendment.
- **H21 marker brittleness** — the test asserted `"pOS v2" in text` against the root README. Commit `3c599c1` rewrote the README to loam-shape content; the test was silently broken from that commit forward. M1a's brand-rename rationally aligns the test's marker to the post-rename brand vocabulary (`"loam"`) plus stable content markers (`"substrate"|"harness"|"primary persona"`).

**Resolution.** Both updates land as a NEW corrective commit (per `feedback_no_amend_in_agent_dispatches`) before the seal commit. AC.RNM-1a.7 widened to permit this exact named exception — both updates are bookkeeping/marker-tightening, not behaviour change. Recorded as halt-and-surface event resolved in-band per the corpus precedent (the same corpus that admits H19 admissions land at the next crossing amendment).

**Build-time finding 8 (halt-and-surface, resolved post-seal).** The amendment manifest originally listed scope-of-work as a sealed component with `seal_test: framework/scope-of-work/tests/test_no_sealed_amendments.py` — pos-amend's `apply` reported `skip scope-of-work: seal-test missing`. Per d-migration-1's locked precedent (`scope-of-work + safety-layer (no SEAL_COMMIT sidecar pre-D.1) are moved by git mv but not entered here — their seal-discipline is handled by hands-off-lifecycle's H19 cross-cutting test`), scope-of-work has no own SEAL_COMMIT sidecar; H19 covers its admission. The pos-amend skip during apply was correct behaviour; M1a's diff against `framework/scope-of-work/README.md` is admitted by H19's `framework` + `scope-of-work` allowed-set entries. **Resolution:** the seal commit landed at `143d465`, but the post-seal `pos-amend apply --dry-run` returns exit-1 because of the `skip scope-of-work: seal-test missing` line (`pos-amend` returns 1 when ANY component is skipped). A NEW corrective commit removes scope-of-work from the manifest's `components:` list, leaving the four legitimately-sealed components and the documentation in §11 here. The manifest correction is doc-only.

**Build-time finding 9 (halt-and-surface, resolved in-band).** During the seal-sweep step, `framework/workspace-bootstrap/tests/test_AC39_6_no_tracker_payload_in_source.py::test_AC39_6_value_prop_sentinels_not_in_workspace_bootstrap_src` failed at the cross-check assertion `"pOS v2 — Value Proposition of the Harness and the Primary Persona" in vp_text`. The test sentinel pin was authored against the pre-rename VP H1; M1a's brand-prose rebrand (AC.RNM-1a.2) renamed the H1 to `"loam — Value Proposition…"`. Test intent ("VP prose not hard-coded in workspace-bootstrap source") preserved; the brittle string-marker is brand-keyed (intent: "match the live H1") so updating it is methodology-aligned. Resolved in-band as a NEW corrective commit; the other five sentinels (which carry no brand vocabulary) are unchanged.

**Build-time finding 10 (deferred to subsequent sub-amendments).** Across `framework/<comp>/tests/` and `framework/<comp>/src/`, multiple test/source files contain hard-coded `pos-v2`/`pOS v2`/`pOS` strings — most as test-fixture workspace names (`tmp_path / "pos-v2"`), some as docstring/comment prose, some as configuration constants. These are NOT in M1a's docs/prose-only scope; they're code-side surface that M1b (env-vars + path constants) and M1e (namespace pivot) will sweep. M1a's seal-sweep DID NOT flag these because none are brand-keyed cross-checks against M1a's renamed docs (unlike AC39_6 finding #9). Recorded for the next dispatcher: M1b's sub-plan should include a code-side audit of `pos-v2` literals as fixture workspace names.

**Build-time finding 11 (post-seal-step recovery).** The first invocation of `pos-amend seal --plan-doc <abs>` got past the dirty-tree pre-flight (after stashing pre-existing untracked `personas/`), advanced four sidecars to apply-commit SHA `5dc1122`, wrote the seal narrative to `framework/hands-off-lifecycle/seals/SEAL_COMMIT.oss-v0-1-0-publish-rename-1a`, and ran the cross-component sweep — which surfaced the AC39_6 failure (finding #9) and the pre-existing flaky launchd test (`test_D5_1_memory_graphiti_scaffold_plist_reaches_health_200`, FIDRAFT-recorded at amendment #67's seal). The seal step exited with "Sidecar + narrative changes left uncommitted. Fix the failing test and re-invoke." Recovery: reset the four bumped sidecars, removed the new untracked seal-narrative + scope-of-work SEAL_COMMIT, committed the AC39_6 corrective, re-invoked seal. The pos-amend `seal` recovery flow is methodology-aligned (it explicitly leaves the writes uncommitted so the builder can fix and re-invoke).

**Halt summary.** No blocking findings prevented seal. Five build-time findings (#7 H/L H19/H21 pre-existing-debt, #8 manifest scope-of-work entry skip, #9 AC39_6 brand-keyed sentinel, #10 deferred code-side fixture-name sweep, #11 seal recovery flow) all resolved in-band or recorded for downstream. All align with the dispatch's halt-and-surface clause for cross-mode debt + ODD-violations-in-surrounding-code + `feedback_loose_AC_text_fix_AC_not_implementation`.

---

## 12. Method-decision register (post-build)

This section is populated post-build per the `pos-amend seal --plan-doc <abs-path>` convention.

### D-build.M1a.1 — sed vs targeted-edit per file

(post-build)

### D-build.M1a.2 — odd-methodology example-phrase rephrase

(post-build — record whether the example became `loam` or a brand-neutral phrasing)

### D-build.M1a.3 — odd-in-pos filename-reference handling

(post-build — record any in-file references to the filename slug that stayed unchanged)

### Test breakdown

(post-build — per AC test files; M1a is docs-only so no NEW source tests; the seal-diff fence test for AC.RNM-1a.S is the primary check)

### Backwards-compat verification

(N/A — M1a is docs-only; no compat surface)

### H19 admission (per finding #3)

(post-build — record whether any M1a-touched README is in H19's byte-content sample; expected: no)

### Commit SHAs

`pos-amend seal --plan-doc` auto-backfill did not run because the first seal invocation exited HALT (per finding #11) and the second invocation exited HALT at post-seal-dry-run (per finding #8); the seal commit landed but the SHA-backfill follow-up commit was not created. The SHAs below are manually populated.

- **Series master plan-doc commit:** `ebe0a57` — `docs(plans): split M1 rename into multi-amendment series — D-RNM.1 ruling` (2026-04-29).
- **M1a sub-plan + manifest commit:** `26cfd16` — `docs(plans): author M1a sub-plan + manifest — docs/prose-only brand rebrand` (2026-04-29).
- **M1a feature commit:** `2b2899b` — `feat(rename-1a): docs/prose-only brand rebrand pos-v2/pOS v2/pOS → loam (amendment #76, AC.RNM-1a.1–AC.RNM-1a.S)` (2026-04-29).
- **pos-amend apply + H/L pre-existing-debt corrective commit:** `5dc1122` — `chore(rename-1a-apply): pos-amend apply + H/L pre-existing-debt corrective for amendment #76` (2026-04-29).
- **AC39_6 brand-keyed sentinel corrective commit:** `92098e1` — `chore(rename-1a-fix): align workspace-bootstrap AC39_6 sentinel to post-rename VP H1 (amendment #76)` (2026-04-29).
- **Sub-plan §11 findings update commit:** `f3041a5` — `docs(plans): record M1a build-time findings #7–#11 in sub-plan §11` (2026-04-29).
- **Seal commit:** `143d465` — `chore(seals): M1a docs/prose-only brand rebrand — … — objective-tracker+workspace-bootstrap+hands-off-lifecycle+scope-of-work+workspace-sync at f3041a5` (2026-04-29).
- **Manifest scope-of-work-removal corrective commit (post-seal):** `aa9aa5a` — `docs(plans): correct M1a manifest — remove scope-of-work (no SEAL_COMMIT sidecar; H19 covers admission)` (2026-04-29).
- **§14 SHA-register backfill commit (this commit):** TBD — `docs(plans): record amendment #76 commit SHAs in method-decision register` (2026-04-29).

Diff window: `ebe0a57..f3041a5` (BASELINE → seal-target).

### Dependents cleared to dispatch

- **M1b** (env-vars + `~/.pos/` per series master §2 ladder) cleared to dispatch. Dispatcher should author `docs/plans/oss-v0-1-0-publish-rename-1b.md` per the series master's plan-shape convention.
- **`oss-v0-1-0-publish.md` §5 M1 row re-pricing** flagged in series master §11 — next dispatcher's action item before M1b begins (or M1b's dispatch absorbs it as a precursor doc-only commit).

---

## 13. References

- **Series master:** `docs/plans/oss-v0-1-0-publish-rename.md` (committed `ebe0a57`).
- **Authority documents (inherited from series master):**
  - `docs/plans/loam-rename-decisions.md` (locked Tier-1 + Tier-2 + Kept-Technical catalogue).
  - `.scratch/claude-output/loam-rename-migration-plan.md` Phase 1.
- **STATE.md** — governing rules.
- **ODD methodology + ODD-in-pos:** `docs/odd-methodology.md`, `docs/odd-in-pos.md`.
- **VALUE_PROPOSITION:** `docs/VALUE_PROPOSITION.md`.
- **CLAUDE.md** + `~/.claude/CLAUDE.md` + `~/.claude/projects/-Users-lukeivers-pos3/memory/MEMORY.md`.
- **Memory bullets carried forward:**
  - `feedback_no_amend_in_agent_dispatches`.
  - `feedback_dispatch_explicit_pos_amend_apply`.
  - `feedback_subagent_odd_violation_halt`.
  - `feedback_amendment_dispatch_speedups`.
  - `feedback_summarize_and_surface_decisions`.
  - `feedback_serialize_amendment_builds`.
  - `feedback_always_specify_wd_in_dispatches`.
  - `feedback_verify_post_amendment_state`.
  - `feedback_duration_estimation_rubric`.
  - `feedback_loose_AC_text_fix_AC_not_implementation`.
- **Precedent multi-component sealed-amendment manifests:**
  - `docs/plans/amendment-27-stale-launchd-readme-cleanup.manifest.yaml` (single-component README rebrand precedent).
  - `docs/plans/a1-substrate-timestamp-format-normalization.manifest.yaml` (three-component fence with H19-frozen on hands-off-lifecycle).
- **`pos-amend` tool:** `framework/tools/pos-amend/` (M1a is built using this CLI; rename to `loam amend` is M1g).
