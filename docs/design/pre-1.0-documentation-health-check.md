# loam — Pre-1.0 Documentation Health Check

**Date:** 2026-06-01
**Status:** COMPLETE — fixes applied to non-sealed docs; sealed-doc + judgment-call items surfaced below.
**Owner:** Luke Ivers
**Author:** `loam-documenter` (dispatched per Telegram 13408)
**Working tree:** `/Users/lukeivers/loam` (main, HEAD `044251d8` at audit start)
**Doc class:** audit / health-check report

---

## Headline

The docs are in **good shape overall** — not the heavy drift the dispatch
anticipated. The README install path, version surfaces, getting-started, the
roadmap reconciliation (§2–§6), and all 4 new design docs are accurate. The
real drift is concentrated in **two surfaces**: (1) two shipped runtime
components (`state-migration-engine`, `protection-matrix`) that crept in
without their install-graph line / README count / component page, and (2) a
**stale one-line header summary** on STATE.md (the change-log *body* is current;
only the frozen header values lagged).

**Single most important issue for the owner:** the README "current public
release is v0.14.0" claim is **CORRECT** per git refs — but STATE.md's own
prose (line 129) still says v0.14.0's "tag-push HELD for owner," which is now a
stale historical clause (the `v0.14.0` tag IS on `origin/main`). Trust git refs,
not STATE prose, on publish state. **No doc anywhere claims 1.0 is shipped** —
that critical check is clean.

**Docs audited:** 14 primary surfaces — README.md, install-from-source.txt,
docs/install-from-source.md, docs/STATE.md, docs/plans/loam-roadmap.md,
docs/getting-started.md, docs/positioning.md, docs/VALUE_PROPOSITION.md, the
3 new design docs + the shared-artefact catalogue, the dev-mode-manifest, and
the dev-sdlc CDC/SKILL surfaces named in the dispatch — plus version surfaces
across ~10 pyproject.toml files + ACTIVE_MINOR + the meta-package.

---

## FIXED directly (non-sealed top-level docs) — one commit

| File | Fix |
|---|---|
| `install-from-source.txt` | Added the missing `-e ./framework/protection-matrix` line. The component ships the `loam guards` verb (registers a `loam.cli.subcommands` entry-point) but was absent from the install graph — a fresh source install had **no `loam guards` verb**. Same install-completeness class the file already fixed for `state-migration-engine`. |
| `README.md` | (a) PyPI caveat (lines 84-87) rewritten: the old "a future minor will ship from PyPI" is superseded in *form* — the `pipx install loam` meta-package is now built + proven against a local wheelhouse — but the public PyPI flip has NOT happened, so the source-clone path is still the one that works today. New text states both truthfully. (b) "Eighteen runtime components" → "Twenty" + added `state-migration-engine` + `protection-matrix` rows to the What-Ships table. (c) "per-component references for all eighteen" reworded — `docs/components/` is missing pages for those two newest components. |
| `docs/STATE.md` | Header (line 3) refreshed: `Last refresh: 2026-05-24` → `2026-06-01`; the frozen "All thirteen sealed components built; currently #154" status summary corrected (thirteen is provably wrong; latest sealed amendment is #181) and re-pointed to the live roster rather than pinning a possibly-wrong count. The change-log **body** was already current (rich 2026-06-01 #179-#181 entry at line 115) — only the header summary lagged. |
| `docs/plans/loam-roadmap.md` | Flatten row (line 120): the `framework/framework` cosmetic-doubling target **does not exist in the canonical tree** (`find` returns nothing). Row retitled to "PyPI publish / conventional install," flatten flagged stale-with-note (don't schedule a flatten cycle for a directory that isn't there), PyPI half preserved as the only live work. |

Commit: see SHA returned to the dispatcher.

---

## MUST-FIX-BEFORE-1.0 — still open (owner / sealed-amendment surface)

### A. Sealed-component doc fixes (need a follow-on `loam amend` cycle — do NOT edit out-of-band)

These are inside `plugins/dev-sdlc/` (sealed fence). All are stale line-refs /
counts the dev-sdlc review named; each is a one-character-class fix but lands
through an amendment:

1. **`plugins/dev-sdlc/docs/conventions/amendment-cycle.md:14`** — cites
   `apply.py:158` for the committed-HEAD binding. The binding
   (`head_sha = _git_head_sha(repo_root)`) is at **`apply.py:269`**. Stale ref.
2. **`plugins/dev-sdlc/.../loam-amend-cycle/SKILL.md:57`** — same `apply.py:158`
   stale ref; same correct target `apply.py:269`.
3. **`plugins/dev-sdlc/docs/odd-in-loam.md:31`** — "four of the **thirteen**
   sealed components of loam." Component roster has grown well past thirteen
   (≥18 installable framework components + the plugin). The dev-mode-manifest
   (`plugins/dev-sdlc/dev-mode-manifest.yaml`) is the live roster; the prose
   count is stale. (The matching SKILL prose the dispatch named carries the same
   number — sweep both in the amendment.)

**Recommendation:** bundle 1-3 into ONE small dev-sdlc doc-only amendment
(single fence, doc-only, no production code) before the 1.0 cut. Cheap; one
cycle.

### B. Component-page gap (non-sealed, but generative — surface not grind)

`docs/components/` documents 18 components but is **missing pages for
`state-migration-engine` and `protection-matrix`** — both shipped runtime
components with user-facing verbs (`loam migrate`, `loam guards`). The README
now points readers to STATE.md/roadmap as the interim source, but a clean 1.0
wants two short component reference pages matching the existing
`docs/components/*.md` shape. This is doc authoring (not a mechanical fix), so I
did NOT grind it in-thread — **recommend a short follow-on documenter dispatch**
to author the two pages from the sealed components' surfaces.

### C. STATE.md change-log backfill (non-sealed, generative — surface)

The header is fixed, but the change-log is **missing dedicated entries for part
of the 2026-05-30/31 arc** the roadmap marks DONE: state-migration-engine seal,
protection-matrix/guards, the STATE-OF-LOAM/`loam audit` (N2) slice, and
auto-upgrade (#163). The v0.14.0 entry (05-29) and the #179-#181 entry (06-01)
are present and detailed; the gap is the middle of the arc. Backfilling ~6-8
detailed change-log entries is generative authoring — **recommend a follow-on
dispatch** rather than an in-thread grind. Not strictly 1.0-blocking (git refs
are the authoritative published-state record per
`feedback_published_state_only_from_git_refs`), but a clean 1.0 STATE.md should
not have a hole in the middle of its biggest week.

---

## Version coherence (reported, NOT bumped — release-cut is owner-gated)

Largely **coherent at 0.14.0 lockstep**. Two intentional outliers, both
documented:

- `framework/state-migration-engine` at **0.13.0** while siblings are 0.14.0 —
  documented as intentional skew in `install-from-source.txt:103` (the unpinned
  inter-component editable deps absorb it). Not a defect.
- `framework/protection-matrix` at **0.1.0** — the newest component, on its own
  early version line. Will fold into lockstep at the next release-cut. Flag for
  the cut, do not bump now.

The dev-sdlc-review-named "plugin 0.14.0 vs sub-packages 0.1.8/0.1.9" drift is
**RESOLVED** — all dev-sdlc sub-packages (odd-extractor, loam-amend, pr-safety,
loam-mode) now read 0.14.0. No action.

The meta-package (`framework/loam-init/meta/pyproject.toml`) is at 0.14.0 and
correctly declares itself dependencies-only (zero packages, PEP-420 namespace
preserved). Accurate.

---

## Clean (verified, no drift) — for the record

- **No "1.0 shipped/published" claim anywhere.** The critical check passes. The
  onboarding smoke writeup says the four-step loop is "READY"/"earns the 1.0
  label" but nothing claims 1.0 is cut.
- **README Quickstart** install steps match `install-from-source.txt` and work
  today (source-clone path). The `loam odd-extract` workflow-chain table is
  accurate — the verb IS registered (by `loam-odd-extractor`'s entry-point).
- **All 4 new design docs** (shared-artefact-quality-catalogue,
  dev-sdlc-1.0-readiness-and-roadmap, loam-plugin-product-architecture) carry
  explicit `FORWARD / 1.1+ / READ-ONLY / nothing built / owner-gated follow-on`
  status banners in their headers. No reader would mistake them for shipped
  features. Clean.
- **Roadmap §2–§6** is internally consistent and reconciled against the git ref
  graph (dated 2026-05-31); DONE/IN-FLIGHT/NEXT-UP rows match reality (FBM-LIVE,
  migration engine, N1-N4, onboarding, foundation-polish, self-recovery all
  correctly marked). The only stale row was the flatten target (fixed).
- **getting-started.md** references `v0.1.0` as "the supported surface" in 3
  spots (lines 15, 28, 78) — these read as *original-release-era* framing, not
  false current-version claims, and are arguably accurate (the v0.1.0 surface
  *constraints* — Claude-Code-only, macOS/Linux, source-install — still hold).
  Left as-is; flag for owner if a version-neutral rephrase is wanted before 1.0.
  Borderline, not a clear inaccuracy.
- **README links** all resolve (`docs/release-roadmap.md`, `docs/positioning.md`,
  `docs/architecture.md`, etc. all present).

---

## Method note

Every "this is wrong" finding above cites file:line + the ground truth it
contradicts (code path, git ref, or actual current value), per
information-trust / claim-or-cite. Where the correct value was a judgment call
(exact sealed-component count, getting-started v0.1.0 framing), I surfaced it
rather than fabricate a number. Published-state claims were verified against git
refs, not artefact prose — which corrected my own initial misread of v0.14.0's
publish state mid-audit.
