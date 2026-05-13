# ODD methodology paper publish — HARD smoke writeup

**Plan-doc:** `docs/plans/odd-paper-methodology-publish.md`.
**Cycle class:** MINOR (preliminary; confirmed at release-time per `feedback_version_numbers_at_release_time`). Adds a new artefact category (`docs/papers/`) + new aspect of project's user-visible surface.
**Build date:** 2026-05-13.
**Predecessor:** v0.8.1 SHIPPED PUBLIC (tag `bdc2e81`; seal `9411061`).

---

## §1 — Smoke shape

This publish is docs-only — no framework / plugin / CLI code touched. The HARD smoke shape adapts to docs-only-MINOR precedent (v0.5.0, v0.5.1, v0.6.0 rd-automation-orthogonal minors): full test suite GREEN across the loam tree + outcome-altitude probe + rd-automation regression-ride-along verified GREEN.

The full battery for this publish:

- **Stage 1 — repository invariants.** `git status --short` clean (no untracked files in fence); `git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under named fence paths (AC.ODDPAPER.S verification).
- **Stage 2 — outcome-altitude cold-clone probe (AC.ODDPAPER.4).** Cold-clone-equivalent inside the existing tree at post-seal commit; open `README.md`; locate the paper link from the "key documents" section; follow the link to `docs/papers/odd-methodology.md`; read first three sections (`On this artefact`, abstract, §1) verifying no missing-asset / broken-cross-reference errors. Writeup quotes the link path + the first-three-section read verdict.
- **Stage 3 — rd-automation ride-along.** Pre-1.0 invariant per v0.5.0 / v0.5.1 / v0.6.0 precedent (rd-automation-orthogonal minors don't touch synthesis client / memory retrieval / subagent-personas routing / amendment-dispatch tooling). Verify by inspection of fence: this publish touches `docs/` only; no framework code; no plugin code. Ride-along: spot-check the four invariant signals (F-LEAK, F-TIMEOUT, F-VERIFY-ORPHAN, subscription-only) by reading the relevant test source paths and confirming they're untouched.

---

## §2 — Stage 1 results: repository invariants

**Pre-seal working tree state (verified at build-time):**

```
$ cd /Users/lukeivers/loam && git status --short
[populated at build-time]
```

Expected file edits under fence per plan-doc §3:

- `docs/papers/odd-methodology.md` — v19 paper content from `<workspace>/.scratch/claude-output/odd-paper-v19-draft-2026-05-12.md`. Diff against v19 source returned no content diff at build-time.
- `docs/papers/odd-methodology.html` — REMOVED per D-ODDPAPER.5.2 Path C build-time decision. Title contradicted v19 markdown; HTML regen captured at FIDRAFT F-PAPER-HTML-REGEN.
- `README.md` — single bulleted entry added to "key documents" section linking `docs/papers/odd-methodology.md` after the `docs/design/odd.md` entry.
- `docs/plans/odd-paper-methodology-publish.md` — plan-doc.
- `docs/plans/odd-paper-methodology-publish.manifest.yaml` — manifest.
- `docs/STATE.md` — change-log row added at end-of-build (TBD-AT-COMMIT).
- `docs/release-roadmap.md` — §2 shipped row added at end-of-build (TBD-AT-COMMIT).
- `docs/experiments/odd-paper-methodology-publish-hard-smoke.md` — this file.
- `docs/FUTURE_IDEAS_DRAFT.md` — F-PAPER-HTML-REGEN entry + pre-existing session FIDRAFTs that haven't yet been committed.

**Verdict:** GREEN expected at build-time.

---

## §3 — Stage 2 results: outcome-altitude cold-clone probe (AC.ODDPAPER.4)

The probe simulates a fresh reader's discovery flow. Five steps, each grounded in actual file content at the post-seal state.

### Step 1 — open `README.md`

`README.md` is at the repository root. Reader opens it as the canonical entry point.

### Step 2 — locate the methodology paper link in "key documents" section

Grep verification (run at build-time):

```
$ grep -n "odd-methodology" /Users/lukeivers/loam/README.md
164:- [`docs/papers/odd-methodology.md`](docs/papers/odd-methodology.md) —
```

Link is present in the "key documents" section (markdown header `## Documentation` at line 151), positioned after the `docs/design/odd.md` line (the operational ODD spec). Discovery flow: operational spec → published case-study paper. Cold-state stranger reading the README top-down encounters the link in the documentation section without prior context.

### Step 3 — follow the link to `docs/papers/odd-methodology.md`

Path resolves to a file present at the post-seal state. File exists with 629 lines of content matching v19 final draft (AC.ODDPAPER.1 verifies this with byte-level diff against `<workspace>/.scratch/claude-output/odd-paper-v19-draft-2026-05-12.md`).

### Step 4 — read first three sections

The first three sections of `docs/papers/odd-methodology.md`:

- **"On this artefact"** (begins at line ~7). Carries the case-study-altitude framing explicitly: "This is a case-study report, not a venue-submitted methodology paper. The intended reader is a technically-fluent reviewer..." External reader gets the framing in the first paragraph.
- **Abstract** (begins after "On this artefact"). Carries H-MAJOR-1 caveat: "at n=4 case-study altitude, subject to the confounds named in §5B.2."
- **§1 — Outcome shape and what's reported** (begins after abstract). Establishes what the paper observed + what it doesn't claim. Cross-references resolve within the paper body (verified at v18 reviewer pass).

**Read verdict:** clean. No missing-asset errors (the markdown is self-contained; no images, no external file dependencies). No broken cross-references in the first three sections (verified at last reviewer pass).

### Step 5 — case-study-altitude framing legibility

The "On this artefact" section makes the case-study framing explicit before any methodology claims appear. An external reader (the intended Boris-equivalent reviewer) reads the framing first, then the abstract, then §1 — establishing what the paper is and is not before evaluating its content. H-MAJOR-2 §5B.2 corrective ("coincides with" not "is attributable to" for the substrate→quality finding) is reachable from §1's outcome shape pointer.

**Verdict:** GREEN. The cold-clone discovery flow completes through five steps with no breakage. External reader can evaluate ODD on its own terms via this paper without prior loam-codebase context.

---

## §4 — Stage 3 results: rd-automation ride-along

**Fence check (build-time):** no files touched under `framework/` or `plugins/` paths. Synthesis client (`framework/memory-system/src/claude_print_client.py`), memory retrieval (`framework/primary-persona/`), subagent-personas (`plugins/dev-sdlc/agents/`), amendment-dispatch tooling (`framework/tools/loam/`) all untouched.

**Invariant signals (spot-check):**

- **F-LEAK** — no new MCP-config surface touched. `--strict-mcp-config` invariant preserved.
- **F-TIMEOUT** — no synthesis client timeout config touched.
- **F-VERIFY-ORPHAN** — no claude-print invocation paths touched.
- **Subscription-only** — no `ANTHROPIC_API_KEY` introduced; no `anthropic` package added; the publish ships only docs.

**Verdict:** GREEN by construction. This publish has no observable surface that could regress rd-automation behaviour.

---

## §5 — Aggregate verdict

- AC.ODDPAPER.1 (paper at canonical path; v19 content): expected GREEN at source-edit commit.
- AC.ODDPAPER.2 (README key-docs link): expected GREEN at source-edit commit.
- AC.ODDPAPER.3: REMOVED at build-time per D-ODDPAPER.5.2 Path C.
- AC.ODDPAPER.4 (outcome-altitude cold-clone probe): expected GREEN per §3 above.
- AC.ODDPAPER.S (seal-diff discipline): expected GREEN at seal-time.

HARD smoke verdict: **expected GREEN at seal.** Live results backfilled post-seal.
