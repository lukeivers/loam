# ODD methodology paper publish — case-study altitude artefact

**Status:** plan-only at authoring time. Plan-before-code per `feedback_plan_before_code`.
**Slug:** `odd-paper-methodology-publish`. Scope-descriptive per `feedback_version_numbers_at_release_time`; no version in the slug. Version assigned at release-time from `(current_published, class)`.
**Date authored:** 2026-05-13.
**Class (preliminary; confirmed at release-time):** MINOR per `docs/release-versioning-policy.md` — adds a new artefact category (`docs/papers/`) and a new aspect of the project's user-visible surface (peer-reviewable methodology documentation with empirical case-study observations). Not a defect-closure within a prior shipped outcome; the paper is a brand-new artefact. The class call gets re-confirmed at release-time per the runtime-version-derivation rule; if the built artefact diverges from this plan (e.g., paper ships as a thin index page rather than full case-study) the class call gets re-derived from what shipped.
**Predecessor:** v0.8.1 SHIPPED PUBLIC 2026-05-10 (tag `v0.8.1`, annotated `bdc2e81`; seal `9411061`).
**Working directory:** `/Users/lukeivers/loam/`.
**Owner authorization:** Telegram 11074 ("Paper first") on 2026-05-13, in response to dispatcher surfacing the paper-first vs §4-restructure-first sequencing question (Telegram 11073). Build authorization covers plan-doc + source-edit + apply + seal + HARD smoke. Publish remains owner-asked per ASK-FIRST.

---

## §1 — Outcome shape (the "why")

The ODD methodology has been the central practice underlying loam's build cadence since v0.2.2 (when `docs/odd-llm-grounding.lean.md` started auto-loading at every fresh DEV-mode session). It has shaped every shipped minor since then: the ladder from VALUE_PROPOSITION → ACs → outcome-altitude probe is the spine of how every plan-doc in `docs/plans/` is authored. The methodology has been documented operationally inside loam (the SKILL bundle, the dispatch-brief authoring discipline, the principle-derivation map) but has never been written up as an artefact that can be circulated to readers outside loam.

This publish lands that artefact. The paper at `docs/papers/odd-methodology.md` is a case-study report — not a venue-submitted methodology paper — covering: (a) what ODD proposes; (b) what was observed across the ProgramBench-derivative empirical investigation (5 tasks: yj, csview, gron, htmlq, figlet; n=4 reps on yj for statistical anchor, n=1 reps on the others for architectural verification); (c) what the case-study data does and does not support; (d) what would be needed to convert case observations into population-level methodology claims.

After this publish lands:

- A new reader landing on the loam README can find the methodology paper from a top-level "Read this for context" link.
- External readers (researchers, methodology practitioners, would-be loam contributors) have a self-contained artefact to evaluate ODD on its own terms before engaging with loam itself.
- The `docs/papers/` directory exists as a category for future case-study / methodology / empirical-finding writeups; future case-study artefacts ladder under that category rather than scattering across `docs/`.

Why MINOR rather than PATCH: PATCH per the policy doc is "backwards-compatible fixes for the named outcome of the current minor." No prior shipped minor named "methodology paper available" as its outcome; the v0.8.1 PATCH closed walker-fix defects within v0.8.0's honesty-cleanup outcome. This work is a new outcome shape — "loam publishes a peer-reviewable methodology paper documenting ODD with empirical case-study observations" — that meets the MINOR definition. The runtime-derivation rule (`feedback_version_numbers_at_release_time`) confirms this at release-time by computing `next_MINOR(v0.8.1)`.

---

## §2 — Prime objective ladder

```
VALUE_PROPOSITION.md prime objective
   └─ "primary persona is a translation layer between the user's
       natural-language intent and AI-effective execution; the harness
       is the toolkit the primary persona draws from"
        └─ external readers can evaluate the methodology underlying
           that translation layer before engaging with loam itself
            └─ a self-contained methodology paper exists at a
               canonical project location, linked from the project
               entry-point, with claim-or-cite + arithmetic-verified
               + case-study-altitude framing already applied
                └─ AC.ODDPAPER.1 — paper artefact present at canonical
                                    path; content matches v19 final
                                    (case-study altitude; claim-or-cite
                                    discipline; arithmetic-verified
                                    statistics)
                └─ AC.ODDPAPER.2 — README links the paper from the
                                    "key documents" section so a fresh
                                    reader can discover it from the
                                    project entry-point
                └─ AC.ODDPAPER.3 — HTML rendering present alongside the
                                    markdown source for readers who
                                    prefer rendered viewing
                └─ AC.ODDPAPER.4 (outcome-altitude) — cold-clone stranger
                                    probe: fresh clone of the post-seal
                                    state, open README, follow the paper
                                    link, paper renders + first three
                                    sections readable end-to-end without
                                    missing-asset / broken-link errors
                └─ AC.ODDPAPER.S — seal-diff discipline
```

Two VALUE_PROPOSITION tests:

- **Primary-persona test** — every AC reduces translation burden for the user by making one more aspect of the harness legible to an external evaluator. AC.ODDPAPER.2's README link reduces the burden of "how do I evaluate this methodology before adopting?" — the reader follows one link.
- **Harness test** — `docs/papers/` is a new category in the project's documentation toolkit; the primary persona draws from this category when future case-study reports ship. The category didn't exist before this publish.

---

## §3 — Component fence

**Single-cycle MINOR.** Touched surface: `docs/papers/` (new category) + `README.md` (link addition) + universal-admission docs (STATE.md, release-roadmap.md, experiments writeup, FIDRAFT updates).

**PRIMARY:**
- `docs/papers/odd-methodology.md` — paper artefact, v19 final draft staged from `<workspace>/.scratch/claude-output/odd-paper-v19-draft-2026-05-12.md`. ~15,200 words, 629 lines, case-study altitude with explicit framing in §"On this artefact". Claim-or-cite discipline applied (5 real citations: Beck 2002, North March 2006, Wynne+Hellesøy 2012, Zave+Jackson 1997 IEEE TSE 6(1):1-30, Yang et al. 2026 ProgramBench arXiv:2605.03546; no fabricated sources). Arithmetic-verified (pre-substrate yj mean 23.06% sd 18.83pp from re-derivation of the 4 listed reps; substrate yj mean 47.09% sd 2.77pp).
- `docs/papers/odd-methodology.html` — REMOVED per D-ODDPAPER.5.2 Path C (staged HTML is from earlier iteration; title doesn't match v19; ship markdown-only and capture HTML regeneration as FIDRAFT).
- `README.md` — add a single bulleted entry under the "key documents" section linking `docs/papers/odd-methodology.md` with a one-sentence description.

**Universal-admission docs (per amendment #22 ruling #3):**
- `docs/plans/odd-paper-methodology-publish.md` (this file).
- `docs/plans/odd-paper-methodology-publish.manifest.yaml`.
- `docs/STATE.md` — new "SHIPPED LOCAL" row added at end-of-build for the derived version.
- `docs/release-roadmap.md` — new §2-shipped row added at end-of-build for the derived version.
- `docs/experiments/odd-paper-methodology-publish-hard-smoke.md` — HARD smoke writeup covering AC.ODDPAPER.4 outcome-altitude probe.
- `docs/FUTURE_IDEAS_DRAFT.md` — already has session FIDRAFT entries staged (uncommitted); commit alongside this build.

**Per-component version bump (correction at build-time):** the AC.HONEST.1 discipline from v0.8.0 specifies that component `pyproject.toml` versions advance with shipped MINORs going forward — independent of whether framework code is touched. The discipline is "every MINOR ships a coherent per-component version surface" (the surface that `loam --version` and component-level metadata expose). This publish is MINOR, so the 30 pyproject.toml files (18 framework components + 6 framework/tools auxiliary packages + 6 plugin packages) bump from 0.8.0 → 0.9.0, plus the 4 `__version__` strings (`framework/tools/loam/`, `framework/loam-init/`, `framework/tools/orphan-plist-cleanup/`, `framework/workspace-sync/`) bump to 0.9.0. Initial plan-doc draft incorrectly excluded these per-component bumps; corrected at build-time. (PATCHes still ride predecessor MINOR's version per D-NFCLEAN.4 v0.8.1.)

**Untouched:** all framework code (excluding pyproject.toml metadata), all plugin code (excluding pyproject.toml metadata), all tests, all CLI surface (excluding `__version__` strings). The paper publish doesn't change behavioural surface in any component; the only changes outside `docs/` are the per-component version metadata bumps.

**Out of fence:** seal directories; `docs/spec/` files; the §4 restructure of `docs/release-roadmap.md` (separate plan-doc at `docs/plans/release-roadmap-priority-queue-restructure.md`, runs as the next build cycle after this one).

---

## §4 — Acceptance criteria

Three ACs plus seal-diff (AC.ODDPAPER.3 removed at build-time per D-ODDPAPER.5.2 Path C; see below). AC IDs use scope-descriptive `ODDPAPER` family per `feedback_scope_descriptive_ac_ids`.

### AC.ODDPAPER.1 — Paper artefact present at canonical path with v19-final content

**What:** `docs/papers/odd-methodology.md` exists and matches the v19 final draft at `<workspace>/.scratch/claude-output/odd-paper-v19-draft-2026-05-12.md`. Content carries the case-study-altitude framing (explicit "On this artefact" §; H-MAJOR-1 abstract caveat; H-MAJOR-2 §5B.2 "coincides with" not "is attributable to"; A-MAJOR-1 §2.4 capability sub-table with outer-objective context). Citations are all real per claim-or-cite discipline (no Wang et al. / Liu et al. fabrications). Arithmetic is verified (pre-substrate yj mean 23.06% sd 18.83pp; substrate yj mean 47.09% sd 2.77pp).

**Verdict:** GREEN if file present at canonical path AND `diff <workspace>/.scratch/claude-output/odd-paper-v19-draft-2026-05-12.md docs/papers/odd-methodology.md` returns no diff (or only frontmatter/path-normalization diffs). YELLOW if file present but minor formatting drift from v19. RED if file absent OR substantive content drift OR fabricated-source regression.

**Test:** doc-level structural assertion (manual review at build-time + diff against v19 source).

`outcome-altitude: false` (substrate; necessary for AC.ODDPAPER.4 probe).

### AC.ODDPAPER.2 — README links the paper from "key documents" section

**What:** `README.md` "key documents" section (currently lines ~152-166) gains one bulleted entry linking `docs/papers/odd-methodology.md` with a one-sentence description naming what the paper is (case-study report; methodology underlying loam's build cadence; ProgramBench-derivative empirical observations). Entry placed after the `docs/design/odd.md` line (the operational methodology spec) so the discovery flow reads: operational spec → published case-study paper.

**Verdict:** GREEN if README contains a link to `docs/papers/odd-methodology.md` from the "key documents" section AND the description is one sentence AND placement is after the `docs/design/odd.md` entry. YELLOW if link present but description multi-sentence or placement different. RED if link absent.

**Test:** grep `README.md` for `docs/papers/odd-methodology.md`; verify count == 1; verify position relative to the `docs/design/odd.md` line.

`outcome-altitude: false` (necessary substrate for the AC.ODDPAPER.4 cold-clone discovery flow).

### AC.ODDPAPER.3 — REMOVED at build-time per D-ODDPAPER.5.2 (Path C)

**Build-time decision (2026-05-13):** the staged `docs/papers/odd-methodology.html` is from an earlier iteration of the paper — title reads "Outcome-Altitude Acceptance for LLM-Authored Software" while the v19 markdown title is "Methodology Description and Case-Study Observations from LLM-Authored Software." Regenerating HTML to match v19 is non-trivial (custom CSS template; ~32KB hand-styled); pandoc not installed on dispatcher's machine. Dropping HTML rendering from this publish ships markdown-only — GitHub renders markdown natively for external readers, and the markdown source is the canonical content. The stale HTML file gets removed from `docs/papers/` as part of the source-edit to prevent the title-contradiction reading a stranger would otherwise experience. HTML regeneration captured as FIDRAFT entry for a follow-on cycle.

`outcome-altitude: n/a` (AC removed).

### AC.ODDPAPER.4 — Outcome-altitude cold-clone stranger probe

**What:** Cold-clone of the post-seal commit (or a temporary worktree pointing at it) reproduces the discovery flow a fresh reader would experience: (1) open `README.md`; (2) locate the methodology paper link from the "key documents" section without prior knowledge of the file path; (3) follow the link to `docs/papers/odd-methodology.md`; (4) read the first three sections (`On this artefact`, abstract, §1 outcome shape) without missing-asset errors or broken cross-references; (5) note whether the paper's case-study-altitude framing is legible to an external reader.

Probe documented at `docs/experiments/odd-paper-methodology-publish-hard-smoke.md` covering: cold-clone command + path; README "key documents" section quoted; click-through-equivalent grep-walk from README to paper; first-three-section read verdict; any cross-reference resolution failures.

**Verdict:** GREEN if all 5 steps complete cleanly AND the writeup quotes the link path + the first-three-section read verdict. YELLOW if probe completes but 1-2 steps surface fixable nits (e.g., one cross-reference broken). RED if probe cannot complete OR README link is unfindable from cold state OR paper has structural rendering breakage.

**Test:** outcome-altitude probe; runs at HARD smoke time against rd-automation precedent. Writeup is the verifiable deliverable.

`outcome-altitude: true` per `feedback_test_outcome_altitude_required` — real cold-clone, real reader-discovery simulation, real first-three-section read against canonical content. Not a stubbed walkthrough.

### AC.ODDPAPER.S — Seal-diff

**What:** Sealed-component cycle ritual; sidecar advances; `git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under the named fence (`docs/papers/` + `README.md` + universal-admission docs). Out-of-fence diffs = halt + rewind.

`outcome-altitude: false` (process invariant).

---

## §5 — Decisions builder rules at build time

### D-ODDPAPER.5.1 — Class confirmation at release-time

The preliminary class call in this plan-doc is MINOR. The build proceeds under MINOR-class assumptions (universal-admission docs reflect MINOR). At release-time, when invoking `loam release <version>`, the builder re-confirms the class against what actually shipped + derives the version per `next_number = bump(current_published, class)`. If the build came out smaller than planned (e.g., paper landed without the README link), the class call reduces to PATCH and the version derives differently.

### D-ODDPAPER.5.2 — HTML regeneration vs commit-as-is

**Resolved at build-time (2026-05-13): Path C — drop HTML from this publish.**

The staged `docs/papers/odd-methodology.html` (32KB, committed `cfcb03f`) is from an earlier paper iteration — title doesn't match v19. Three candidate paths:

- **Path A:** commit the staged HTML as-is. Rejected — stale title would contradict the v19 markdown for any reader following the link.
- **Path B:** regenerate HTML from v19 markdown via pandoc. Rejected — pandoc not installed on dispatcher's machine; custom CSS template would need re-application.
- **Path C (selected):** remove the stale HTML file from `docs/papers/`; ship markdown-only. GitHub renders markdown natively; the markdown source is canonical content. HTML regeneration captured as FIDRAFT entry for follow-on cycle.

AC.ODDPAPER.3 removed; AC count down from 4 to 3.

### D-ODDPAPER.5.3 — STATE/roadmap row content shape

Universal-admission rows in STATE.md + release-roadmap.md follow the existing convention from v0.8.0 / v0.8.1 (slug + objective sentence + seal SHA + commit list). The version number in the row header gets filled in AFTER the release-CLI run derives the number — at plan-time and source-edit time the row header carries placeholder `vX.Y.Z` to be filled by post-publish backfill (or by the build-time author if the version is determined at apply-time).

---

## §6 — Out of scope (explicit)

- **§4 restructure of `docs/release-roadmap.md`.** That work has its own plan-doc at `docs/plans/release-roadmap-priority-queue-restructure.md` (committed `b269d8e` on 2026-05-09 against Telegram 10557; never built). Runs as a separate build cycle after this one. Stripping pre-numbered entries from §4 is NOT part of this publish.
- **Renaming historical plan-doc filenames with version-packed slugs.** `docs/plans/v0-X-Y-*.md` files retain their version-packed names. The scope-descriptive-slug discipline applies to forward-looking plan-docs (this one); historical filenames are records of what shipped and stay as-is per the immutability convention in the priority-queue-restructure plan-doc §3.
- **Other untracked plan-docs in the working tree.** `docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md` is a separate piece of work; not committed as part of this build. (Stash-or-leave decision is the builder's call; if leaving uncommitted, the clean-tree gate will RED at release time and the file must be moved to `.scratch/` or stashed first.)
- **Methodology paper content edits beyond v19 final.** v19 was the last reviewer-pass output; further content iteration is out of scope. If reviewer raises a new finding during this build, it lands as a FIDRAFT entry, not a v20.

---

## §7 — HARD HALTs (build-time)

- **Citation regression.** If any citation in the staged paper fails real-source verification (claim-or-cite discipline), halt + surface. The v19 draft is already cite-verified; this is a regression guard.
- **Arithmetic regression.** If any statistic in the staged paper fails recomputation against its source data, halt + surface.
- **Out-of-fence diff at seal time.** If `git diff --name-only BASELINE..SEAL_COMMIT` shows changes outside `docs/papers/` + `README.md` + universal-admission paths, halt + rewind.
- **README link placement drift.** If the README "key documents" section structure has changed since plan authoring (different ordering, different section name), surface for re-positioning rather than auto-inserting in a structurally-wrong location.
- **HTML rendering broken in either system theme.** If the cold-clone probe surfaces unreadable text in either light or dark mode, halt for theming fix before seal.

---

## §8 — Dependencies

- **v0.8.1 SHIPPED PUBLIC** (tag `bdc2e81`; seal `9411061`). This publish's predecessor; `current_published` for release-time derivation.
- **v19 final draft at `<workspace>/.scratch/claude-output/odd-paper-v19-draft-2026-05-12.md`.** Source of truth for paper content; AC.ODDPAPER.1 diffs against it.
- **`feedback_claim_or_cite_no_fake_sources.md`** (captured Telegram 11000). Discipline applied in v15-v19 citation cleanups; regression guard at HARD HALT layer.
- **`feedback_arithmetic_verification.md`** (captured Telegram 11019). Discipline applied in v5-v19 arithmetic corrections; regression guard at HARD HALT layer.
- **`feedback_version_numbers_at_release_time.md`** (captured 2026-05-13, Telegram 11071). This plan-doc's own discipline (scope-descriptive slug, version-at-release-time).
- **`feedback_dynamic_theme_for_generated_documents.md`**. HTML rendering theme requirement for AC.ODDPAPER.3.
- **`feedback_test_outcome_altitude_required.md`**. AC.ODDPAPER.4 is the outcome-altitude probe satisfying this rule.

---

## §9 — Estimated AI-time

Per `feedback_duration_estimation_rubric` (10-15s per tool call wall-clock):

- Plan-doc + manifest authoring: ~5-10 min (in progress, this file).
- Source-edit commit (paper + README + HTML verification + universal-admission docs): ~10-15 min.
- Apply (`loam amend apply`): ~2-3 min.
- Seal (`loam amend seal`): ~2-3 min.
- HARD smoke against rd-automation: ~5-8 min (precedent: v0.8.1 HARD smoke ran ~230-335s).
- Outcome-altitude probe + writeup: ~5-10 min.
- STATE/roadmap admin: ~5 min.

**Midpoint estimate: ~45 min build-time.** Plus owner-gated publish step (release-CLI dry-run → push → public flip).

---

## §11 — Authority chain

- Owner authorization: Telegram 11074 (2026-05-13) — "Paper first."
- Dispatcher: primary persona on the loam canonical branch (current session).
- Class call: dispatcher at plan-time (MINOR preliminary); re-confirmed at release-time per `feedback_version_numbers_at_release_time`.
- Build authorization scope: plan-doc + source-edit + apply + seal + HARD smoke. Publish (release-CLI run + `git push origin <tag>` + public flip) remains owner-gated per ASK-FIRST.

---

## §13 — §status (post-build backfill)

### AC verdict matrix

| AC | Verdict | Evidence |
|---|---|---|
| AC.ODDPAPER.1 | GREEN | `diff <workspace>/.scratch/claude-output/odd-paper-v19-draft-2026-05-12.md docs/papers/odd-methodology.md` returns no diff at build-time. Paper at canonical path with case-study altitude framing + 5 verified citations + arithmetic-verified statistics. Source-edit commit `c1f7089`. |
| AC.ODDPAPER.2 | GREEN | `grep -n "odd-methodology" README.md` returns `164:- [\`docs/papers/odd-methodology.md\`](docs/papers/odd-methodology.md) —`. Link present in "key documents" section, positioned after the `docs/design/odd.md` entry. Source-edit commit `c1f7089`. |
| AC.ODDPAPER.3 | REMOVED | Build-time D-ODDPAPER.5.2 Path C — stale HTML removed in plan-doc commit `1a8da67` (`delete mode 100644 docs/papers/odd-methodology.html`); ship markdown-only; HTML regen captured as FIDRAFT F-PAPER-HTML-REGEN. |
| AC.ODDPAPER.4 | GREEN | Outcome-altitude cold-clone probe writeup at `docs/experiments/odd-paper-methodology-publish-hard-smoke.md`. Five-step discovery flow verified at post-source-edit state: open README → locate link (line 164) → follow to `docs/papers/odd-methodology.md` → read first three sections (`On this artefact`, abstract, §1) → case-study-altitude framing legibility confirmed. Source-edit commit `c1f7089`. |
| AC.ODDPAPER.S | GREEN | Seal commit `4a4535f` advances `plugins/dev-sdlc/tests/SEAL_COMMIT` sidecar. `git diff --name-only c1f7089..4a4535f` shows only seal-narrative + sidecar advancement (no out-of-fence changes). Apply auto-commit `029fc69`; seal `4a4535f`. |

### AI-time actuals

TBD-AT-BUILD.

### Halt-and-surface findings

TBD-AT-BUILD.

---

## §14 — Method decisions

### Commit SHAs

- Plan-doc + manifest + HTML deletion (D-ODDPAPER.5.2 Path C side-effect): `1a8da67`.
- Source-edit batch (paper + README link + 30 pyproject 0.8.0→0.9.0 bumps + 4 `__version__` bumps + STATE.md row + release-roadmap.md §2 row + experiments writeup + FIDRAFT F-PAPER-HTML-REGEN): `c1f7089`.
- Manifest baseline backfill + smoke_outcome tightening: `afaa26c`.
- Apply auto-commit (BASELINE → c1f7089; allowed_prefixes += docs/papers/; SEAL_COMMIT → c1f7089): `029fc69`.
- Seal: `4a4535f`.
- §status backfill (this commit): TBD-AT-COMMIT.
- Release tag (derived version v0.9.0): TBD-AT-RELEASE-TIME (owner-gated publish).

### Build-time decision deviations

- **D-ODDPAPER.5.2 resolved Path C (not Path A or B):** the staged `docs/papers/odd-methodology.html` was from an earlier paper iteration (title contradicted v19); pandoc not installed on dispatcher's machine; HTML regen non-trivial. Dropped HTML from publish; shipped markdown-only. HTML regen captured at FIDRAFT F-PAPER-HTML-REGEN. AC.ODDPAPER.3 removed; AC count down from 4 to 3.
- **§3 fence corrected at build-time to include pyproject.toml bumps:** initial plan-doc draft incorrectly excluded per-component version bumps; AC.HONEST.1 discipline (v0.8.0) specifies MINORs bump per-component versions independent of whether framework code is touched. Source-edit corrected fence by including 30 pyproject + 4 `__version__` bumps. Plan-doc §3 updated to reflect this at build-time.
- **Untracked out-of-scope file stashed at seal-time:** `docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md` triggered `loam amend seal`'s dirty-tree halt; stashed before re-running seal. Stash entry recoverable post-publish.
