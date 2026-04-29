# OSS v0.1.0 publish — M1a — docs/prose-only brand rebrand — sub-plan

**Status:** plan-doc (pre-build, plan-before-code). 2026-04-29.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Series master:** `docs/rebuild/plans/oss-v0-1-0-publish-rename.md` (committed `ebe0a57`, 2026-04-29).
**Programme position:** First sub-amendment of the M1.rename multi-amendment series. Independent of M1b..M1g; lands first as the cheapest safest pattern-establisher.
**Authority documents:**
- `docs/rebuild/plans/loam-rename-decisions.md` (locked Tier-1 + Tier-2 + Kept-Technical catalogue).
- `.scratch/claude-output/loam-rename-migration-plan.md` Phase 1 (documentary rebrand) — the surface this sub-amendment lands.
- `docs/rebuild/plans/oss-v0-1-0-publish-rename.md` §2 (sub-amendment ladder), §5 (series-wide hard constraints), §7 (series-wide halt triggers).

---

## 1. Summary / TLDR

Rename brand strings `pos-v2` / `pOS v2` → `loam` in **user-facing prose surfaces only**. ZERO code, env-vars, paths, OTel, launchd, CLI, package-namespace, directory-restructure work — all of those are deferred to subsequent sub-amendments (M1b..M1g) per the series master.

**Brand-vocabulary surface.** Per `loam-rename-decisions.md` Tier-1 + the prior monolithic plan's AC.RNM.1: `pos-v2`, `pOS v2`, and bare `pOS` (as the brand abbreviation) all rename to `loam`. `personal OS` is also Tier-1 but does not appear in any M1a-touched file (verified at plan time).

**What lands (M1a only):**

- Root `CLAUDE.md` — every `pos-v2` / `pOS v2` / bare `pOS` brand-prose occurrence becomes `loam` (combined ~15 occurrences).
- `docs/rebuild/VALUE_PROPOSITION.md` — prose rebrand (combined ~11 occurrences).
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
- Spec filename changes (`docs/rebuild/spec/pos-v2-*.md` filename rename) — M1e.
- `docs/odd-in-pos.md` filename change — M1e (content prose updates land here in M1a).
- `STATE.md`, `BACKLOG.md`, `FUTURE_IDEAS.md`, `FUTURE_IDEAS_DRAFT.md` — historical-narrative-heavy live docs; deferred (likely a follow-on docs sweep at M9 scrub or its own sub-amendment).
- `docs/rebuild/plans/*.md` — historical method-record; preserved for accuracy.
- Path strings of form `/Users/lukeivers/ivers-corp-pos-v2/...` — directory rename is M9-deferred per `oss-v0-1-0-publish.md` §6.
- `pos-new-workspace`, `pos-amend`, etc. CLI binary names in prose — those rename in M1g (CLI rename).

**Sealed-component fence (preliminary; exhaustive in §11):** five sealed components whose `framework/<comp>/README.md` is touched: objective-tracker, workspace-bootstrap, hands-off-lifecycle, scope-of-work, workspace-sync. Plus universal-paths admissions for `CLAUDE.md`, `docs/rebuild/plans/`, `docs/odd-in-pos.md`, `docs/odd-methodology.md`, `docs/rebuild/FUTURE_IDEAS.md`, `docs/rebuild/FUTURE_IDEAS_DRAFT.md`. Plus a one-off admission for `docs/CLAUDE_CAPABILITIES.md`, `docs/duration-estimation-rubric.md`, `docs/rebuild/VALUE_PROPOSITION.md` (or whichever already appear in the standard universal admissions list — verify at apply time).

**Estimate:** 30–45 min AI-time per the duration rubric (mechanical-substitution-only category; small fence; no source-tests to run because no source touched).

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Named spec objectives this sub-amendment satisfies:**

- **AC.OSS.5** (`oss-v0-1-0-publish.md` §3) — *"Documentary rebrand complete in public artefacts"* — partial; M1a closes the prose-only portion. Subsequent sub-amendments close the code-side portion.
- **AC.PO.1** (VALUE_PROPOSITION primary-persona test) — single-syllable identity (`loam`) reduces the user's translation-burden vocabulary in the first surface they read (READMEs, root CLAUDE.md). Partial — full closure when the CLI binary also renames at M1g.

**Sealed-component fence (preliminary — see §11 for the exhaustive list):**

Five sealed components touched (READMEs only; no source/test edits): objective-tracker, workspace-bootstrap, hands-off-lifecycle, scope-of-work, workspace-sync.

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

Every brand-prose occurrence in `docs/rebuild/VALUE_PROPOSITION.md` post-amendment reads `loam`. The heading "pOS v2 — Value Proposition" becomes "loam — Value Proposition". Bare-`pOS` prose ("the problem pOS is closing", "an earlier pOS release") becomes the loam form.

**Outcome:** `grep -cE '\bpos-v2\b|\bpOS v2\b|\bpOS\b' docs/rebuild/VALUE_PROPOSITION.md` returns `0`.

### AC.RNM-1a.3 — CLAUDE_CAPABILITIES rebrands cleanly

Every brand-prose occurrence in `docs/CLAUDE_CAPABILITIES.md` post-amendment reads `loam`. This is the largest file of M1a's surface (~96 + 6 prose-references); the rename is mechanical substitution.

**Outcome:** `grep -cE '\bpos-v2\b|\bpOS v2\b|\bpOS\b' docs/CLAUDE_CAPABILITIES.md` returns `0`.

### AC.RNM-1a.4 — duration-estimation-rubric rebrands cleanly

Every brand-prose occurrence in `docs/duration-estimation-rubric.md` post-amendment reads `loam`. The heading "Duration estimation rubric for AI-driven pos-v2 tasks" becomes "Duration estimation rubric for AI-driven loam tasks".

**Outcome:** `grep -cE '\bpos-v2\b|\bpOS v2\b|\bpOS\b' docs/duration-estimation-rubric.md` returns `0`.

### AC.RNM-1a.5 — odd-methodology + odd-in-pos prose rebrand

In `docs/odd-methodology.md`, the example phrase plus the bare-`pOS` brand-narrative references update to `loam` (or to brand-neutral phrasing where a methodological example is intended to be brand-agnostic — builder's call within the AC bound).

In `docs/odd-in-pos.md`, content-prose brand references (`pos-v2`, `pOS v2`, `pOS`) become `loam`. The filename `odd-in-pos.md` itself does NOT change in M1a (filename change is M1e).

**Outcome:** `grep -cE '\bpos-v2\b|\bpOS v2\b|\bpOS\b' docs/odd-methodology.md docs/odd-in-pos.md` returns `0` for prose occurrences.

### AC.RNM-1a.6 — Per-component README prose rebrand

In each of the five touched component READMEs (`framework/objective-tracker/README.md`, `framework/scope-of-work/README.md`, `framework/hands-off-lifecycle/README.md`, `framework/workspace-bootstrap/README.md`, `framework/workspace-sync/README.md`), every brand-prose occurrence (`pos-v2`, `pOS v2`, `pOS`) becomes `loam`. **Path strings** of form `/Users/lukeivers/ivers-corp-pos-v2/...` STAY (directory rename is M9-deferred). **CLI binary names** like `pos-amend`, `pos-new-workspace`, `pos-publish-framework-only` STAY (CLI rename is M1g; binary-name rename is M1c-class). Note: `pos-new-workspace` contains the substring `pos` but the bare-`pOS` regex `\bpOS\b` is case-sensitive and would NOT match `pos-new-workspace`; nonetheless verify post-edit that no CLI-binary substring was incidentally caught.

**Outcome:** in each of the five READMEs, the post-amendment file reads `loam` for every brand-prose occurrence; **path-string** and **CLI-binary-name** references are unchanged. Verification per file: `grep -cE '\bpos-v2\b|\bpOS v2\b|\bpOS\b' <readme>` returns `0`; manual diff confirms only prose-context substitutions.

### AC.RNM-1a.7 — No code, env-var, OTel, launchd, CLI, namespace, or directory changes

Negative AC. The amendment's git-diff includes ZERO touches outside the named docs/prose surfaces. Specifically:

- No `framework/<comp>/src/**` edits.
- No `framework/<comp>/tests/**` edits.
- No `framework/tools/**` source edits (only `framework/tools/loam-mode/**` is excluded too unless a docs-only rename of a content file applies — verify pre-edit).
- No `pyproject.toml` edits.
- No `.claude/settings*.json` edits.
- No `.plist` edits.
- No `framework/<comp>/launchd/**` edits.
- No `~/.pos/` or `POS_V2_*` rewrites in any file.
- No `pos.*` OTel-emit-site rewrites.
- No file-rename / file-delete / file-create operations (this AC enforces docs-only edits to existing files; if a new file becomes structurally necessary, halt-and-surface per §10.4).

**Outcome:** `git diff <baseline>..<feature-commit> --stat` shows changes only in: `CLAUDE.md`, `docs/rebuild/VALUE_PROPOSITION.md`, `docs/CLAUDE_CAPABILITIES.md`, `docs/duration-estimation-rubric.md`, `docs/odd-methodology.md`, `docs/odd-in-pos.md`, `framework/objective-tracker/README.md`, `framework/scope-of-work/README.md`, `framework/hands-off-lifecycle/README.md`, `framework/workspace-bootstrap/README.md`, `framework/workspace-sync/README.md`, plus the plan-doc + manifest under `docs/rebuild/plans/`.

### AC.RNM-1a.S — Sealed-component fence narrows to docs-only

Five-component sealed amendment commit lands per `pos-amend apply` + `pos-amend seal` convention (using the still-`pos-amend` CLI; this is many sub-amendments before M1g's CLI rename). The amendment manifest YAML lists five components (objective-tracker, workspace-bootstrap, hands-off-lifecycle, scope-of-work, workspace-sync) with `frozen_baseline: false` for the four non-H19 + `frozen_baseline: true` for hands-off-lifecycle (H19 frozen-baseline is preserved; M1a does NOT touch H19-pinned source paths because the README is NOT in H19's byte-content sample). The `seal_diff` allowed_prefixes admit `framework/<comp>/` for each touched component plus the universal paths.

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
- **Filenames stay** — `docs/odd-in-pos.md`, `docs/rebuild/spec/pos-v2-*.md` filenames don't change. Filename changes are M1e.
- **STATE.md, BACKLOG.md, FUTURE_IDEAS.md, FUTURE_IDEAS_DRAFT.md** are NOT touched in M1a — historical-narrative-heavy live docs; deferred to a follow-on sub-amendment or M9 scrub.
- **`docs/rebuild/plans/*.md`** are NOT touched in M1a — historical method-record preserved.
- **No `git commit --amend`** (`feedback_no_amend_in_agent_dispatches`).
- **`pos-amend apply` runs BEFORE the seal commit.**
- **H19 retirement does NOT happen in M1a.** M1a does not touch any path in H19's frozen byte-content sample (verify pre-build that none of the five touched READMEs are pinned by H19).

---

## 6. Out of scope (named explicitly per ODD §2.5)

(See §1 for the full list. Re-named here for ODD §2.5 compliance.)

- All work deferred to M1b..M1g (env-vars, paths, launchd, OTel, namespace pivot, dormancy, CLI rename).
- All work deferred to M9 (path-string `/Users/lukeivers/ivers-corp-pos-v2/...` rename, repo directory rename).
- `STATE.md`, `BACKLOG.md`, `FUTURE_IDEAS.md`, `FUTURE_IDEAS_DRAFT.md` — historical-narrative-heavy live docs; M1a defers because each has many filename-references and historical-narrative content where surgical separation costs more than it saves; a later M1-series-internal sub-amendment or M9 scrub closes them.
- `docs/rebuild/plans/*.md` — historical method-record.
- `docs/rebuild/dev-mode-manifest.yaml` — not user-facing prose.
- Spec files at `docs/rebuild/spec/` — M1e (filename change drives the content-prose update).
- Any new file authoring beyond the plan-doc + manifest YAML required for the amendment.

---

## 7. Implementation order (suggested — builder's call to refine)

1. **Pre-flight verification.** `git log --grep="loam.*rename.*M1a\|RNM-1a"` returns nothing prior; `ls docs/rebuild/plans/ | grep oss-v0-1-0-publish-rename-1a` returns this plan-doc only. Verify the canonical tree: `pwd` returns `/Users/lukeivers/ivers-corp-pos-v2`; `git rev-parse --abbrev-ref HEAD` returns `pos-v2`. Halt-and-surface if any check fires.
2. **BASELINE pin.** Pin to the master-plan-revision commit `ebe0a57` (or HEAD at dispatch time, whichever is later). Author the manifest YAML at `docs/rebuild/plans/oss-v0-1-0-publish-rename-1a.manifest.yaml`.
3. **Plan-doc commit.** This plan-doc lands as a doc-only commit (or together with the feature commit per `pos-amend apply` convention). Recommendation: plan-doc commits standalone before the feature commit so the plan is in the tree when `pos-amend apply` runs.
4. **Phase A — root + docs/ surface.** Mechanical sed-or-equivalent on `CLAUDE.md`, `docs/rebuild/VALUE_PROPOSITION.md`, `docs/CLAUDE_CAPABILITIES.md`, `docs/duration-estimation-rubric.md`, `docs/odd-methodology.md`, `docs/odd-in-pos.md`. Post-edit grep verifies AC.RNM-1a.1 .. .5 outcomes.
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

**Findings during plan authoring:**

1. **(Not blocking — pre-emptive scope guard.) `STATE.md`, `BACKLOG.md`, `FUTURE_IDEAS.md`, `FUTURE_IDEAS_DRAFT.md` carry both live and historical brand-prose.** Surgical separation in M1a costs more than the prose-rebrand benefit (the user sees a half-rebranded STATE.md, which is worse than waiting for a later sub-amendment or M9 scrub to land the full rebrand). M1a explicitly defers. Recorded in §6.

2. **(Not blocking — pre-emptive scope guard.) Per-component README path-string and CLI-binary-name references.** A global `pos-v2 → loam` sed would over-reach into path strings (which are M9-deferred) and CLI binary names (M1g-deferred). M1a uses targeted edits, not global sed; documented in §9 Risk 1.

3. **(Not blocking — verification step.) H19 byte-content sample crosses M1a's surface?** Plan-time check: the H19 frozen-baseline byte-content sample (per amendment #23) pins specific files in `framework/hands-off-lifecycle/` and possibly other components. Need to verify pre-build that NONE of the five M1a-touched READMEs are in the H19 sample. Halt-trigger §8.6 fires if they are. **Builder action pre-Phase B:** read `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py` (or the equivalent H19 byte-content test) and confirm no M1a README is pinned.

4. **(FUTURE_IDEAS_DRAFT — pre-emptive.)** Plan-time observation: a recurring pattern across the M1.rename series is "selective rename — change brand-prose, keep path-strings/CLI-names". A future improvement would be a `loam-rename-helper` script in `framework/tools/` that takes a file and a list of lines/regions and applies the rename only to the prose portions, preserving paths and CLI names. Captured here for the build agent to surface to FIDRAFT post-build (do NOT extend M1a scope to add it).

5. **(No ODD §2.5 violation found in surrounding code/docs at plan-authoring time.)** The mechanical rename is the rename; no defensive `if`s without backing AC; no behaviour changes.

6. **(No methodology breach in plan structure.)** ACs are outcome-shape, deterministic, behaviour-count-checked. AC.RNM-1a.7 (negative AC enforcing the docs-only fence) is the explicit ODD §2.5 reverse-direction protection.

**Halt summary.** No blocking findings. One verification step (finding #3) is the builder's pre-Phase-B action; if it fires, halt-trigger §8.6 takes over.

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

(populated by `pos-amend seal --plan-doc <ABSOLUTE PATH>` per the seal-automation extension. ABSOLUTE path required to avoid the `Path.relative_to` crash documented at commit `75c4d73`. The plan-doc commit + amendment feature commit + apply commit + seal commit each appear here on completion.)

### Dependents cleared to dispatch

(post-build — M1b dispatch cleared once M1a seals)

---

## 13. References

- **Series master:** `docs/rebuild/plans/oss-v0-1-0-publish-rename.md` (committed `ebe0a57`).
- **Authority documents (inherited from series master):**
  - `docs/rebuild/plans/loam-rename-decisions.md` (locked Tier-1 + Tier-2 + Kept-Technical catalogue).
  - `.scratch/claude-output/loam-rename-migration-plan.md` Phase 1.
- **STATE.md** — governing rules.
- **ODD methodology + ODD-in-pos:** `docs/odd-methodology.md`, `docs/odd-in-pos.md`.
- **VALUE_PROPOSITION:** `docs/rebuild/VALUE_PROPOSITION.md`.
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
  - `docs/rebuild/plans/amendment-27-stale-launchd-readme-cleanup.manifest.yaml` (single-component README rebrand precedent).
  - `docs/rebuild/plans/a1-substrate-timestamp-format-normalization.manifest.yaml` (three-component fence with H19-frozen on hands-off-lifecycle).
- **`pos-amend` tool:** `framework/tools/pos-amend/` (M1a is built using this CLI; rename to `loam amend` is M1g).
