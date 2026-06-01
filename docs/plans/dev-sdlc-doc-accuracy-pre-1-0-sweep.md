# dev-sdlc doc-accuracy pre-1.0 sweep

**Status:** SEALED (`e335e6f9`) — sealed dev-sdlc single-component amendment
**Working tree:** `/Users/lukeivers/loam` (main)
**Fence:** single-component — `dev-sdlc` (sealed, at `plugins/dev-sdlc/`)
**Class:** doc-only accuracy fix (no production code; no behaviour change)
**Owner ratification:** Luke, Telegram 13414 ("when you're done with the doc
changes I mentioned, go ahead and publish") + task #58 /
`docs/design/pre-1.0-documentation-health-check.md` §A.

---

## §1 — Prime-objective ladder

A clean 1.0 ships docs that do not contradict ground truth. Three stale
references inside the sealed `dev-sdlc` plugin were surfaced by the pre-1.0
documentation health check (`docs/design/pre-1.0-documentation-health-check.md`
§A items 1–3). They are inside the sealed fence, so they land through a
`loam amend` cycle (NOT out-of-band) per the amendment-cycle convention. This
ladders to the VALUE_PROPOSITION prime objective via doc-accuracy: a user
reading the dev-sdlc methodology docs at 1.0 must not be sent to a wrong line
number or told a provably-wrong component count.

## §2 — Ratified rulings

- The cycle lands through `loam amend apply` + `loam amend seal` on the
  `dev-sdlc` fence (the three target files are all under `plugins/dev-sdlc/`,
  the sealed component's tree). NEVER `git commit --amend`.
- BASELINE = the current dev-sdlc seal `5d53983` (the most-recent dev-sdlc seal,
  ancestor of HEAD); the apply step pins the seal-diff window
  `BASELINE..SEAL_COMMIT`.
- The historical "thirteen-component" prose at `odd-in-loam.md:589` and `:601`
  is accurate historical record (the foundation-audit era literally walked
  thirteen components) and is PRESERVED. Only the present-tense walkthrough
  claim at `:31` is corrected.

## §3 — Fence

Single-component fence: `dev-sdlc` (`plugins/dev-sdlc/`). Seal-test:
`plugins/dev-sdlc/tests/test_no_sealed_amendments.py`; sidecar
`plugins/dev-sdlc/tests/SEAL_COMMIT`. All edits confined to three files under
`plugins/dev-sdlc/docs/` + `plugins/dev-sdlc/skills/`.

## §4 — Acceptance criteria

### AC.DSDA.1 — apply.py line-ref corrected across every present-tense surface

No present-tense methodology surface under `plugins/dev-sdlc/` cites
`apply.py:158` for the committed-HEAD binding; every one cites the actual
current location of `head_sha = _git_head_sha(repo_root)`, which is
**`apply.py:269`** (verified Tier-0: `grep -n "head_sha = _git_head_sha"
apply.py` → line 269). Surfaces corrected:
`plugins/dev-sdlc/docs/conventions/amendment-cycle.md`,
`plugins/dev-sdlc/docs/conventions/commit-ladder.md`, and the AC.PASH.C.1
test's docstring/message prose at
`plugins/dev-sdlc/tools/loam-amend/tests/test_AC_PASH_C_1_methodology_prescribes_ordering.py`
(lines 64 + 83 — prose only; the test's anchor regex `apply\.py(?::\d+|\b)`
already matched any line number, so the assertion stays green).

**Scope-widening note (F2):** the dispatch named two surfaces (amendment-cycle.md
+ the SKILL). A Tier-0 grep at build-time found two MORE present-tense instances
of the identical stale ref — `commit-ladder.md:12` (the third surface of the
same methodology trio the AC.PASH.C.1 test fences) and the test's own prose.
Leaving them re-seeds the exact inaccuracy this amendment removes; all are
in-fence (`plugins/dev-sdlc/`), identical-class, doc-only. Widened in-cycle and
named here rather than silently extended.

### AC.DSDA.2 — apply.py line-ref corrected in the SKILL

`plugins/dev-sdlc/skills/loam-amend-cycle/SKILL.md` no longer cites
`apply.py:158` for the same binding; it cites `apply.py:269`.

### AC.DSDA.3 — stale present-tense component count removed

`plugins/dev-sdlc/docs/odd-in-loam.md:31` no longer asserts "four of the
**thirteen** sealed components of loam." The brittle present-tense count is
removed (the live roster has grown past thirteen — the dev-mode-manifest names
15 framework sealed components plus state-migration-engine, protection-matrix,
and the dev-sdlc plugin packages). The walkthrough still names its four
examples; it just stops pinning a stale total. Historical-record uses of
"thirteen" at `:589` / `:601` are PRESERVED (accurate as-of-foundation-audit).

### AC.DSDA.S — outcome-altitude smoke

`python3.13 -m pytest plugins/dev-sdlc/tests/ -q` returns 0 failures + 0
collection errors against the post-amendment HEAD (pre-existing skips
admissible), AND `grep -rn "apply.py:158" plugins/dev-sdlc/` returns zero
matches, AND `grep -n "thirteen sealed components" plugins/dev-sdlc/docs/odd-in-loam.md`
returns zero matches.

## §5 — Out of scope

- Any edit under `plugins/dev-sdlc/src/` (the Python package is unchanged).
- The historical "thirteen" references at `odd-in-loam.md:589` / `:601`.
- The v1.0.0 version bump (separate, non-sealed, direct-commit per precedent).

## §6 — Build steps

1. Plan + manifest commit (this doc + the manifest).
2. Source-edits commit: the three one-line doc fixes.
3. `loam amend apply` auto-commit.
4. `loam amend seal` deterministic seal commit.
5. §14 SHA backfill (if not auto-folded by the seal regex).

## §14 — Method-decision register

| Decision | Resolution |
|---|---|
| D-DSDA.1 | Correct apply.py:158 → apply.py:269 (Tier-0 grep verified). |
| D-DSDA.1b | Scope widened in-cycle to ALL present-tense surfaces (commit-ladder.md + the AC.PASH.C.1 test prose) beyond the two the dispatch named — identical-class, in-fence, doc-only; named in §4 AC.DSDA.1 per F2 (not silently extended). |
| D-DSDA.2 | Drop the brittle present-tense count rather than re-pin a new number (per the health-check guidance "re-point to the live roster rather than pinning a possibly-wrong count"; avoids a future stale-count recurrence). |
| D-DSDA.3 | Preserve historical "thirteen" at :589/:601 (accurate as-of-time record). |

| SHA | Commit |
|---|---|
| `eafa1a12` | plan-doc + manifest (`docs(plans):`) |
| `be4d6604` | source-edits / BASELINE (`fix(dev-sdlc):`) |
| `5a5c29a5` | `loam amend apply` auto-commit |
| `e335e6f9` | `loam amend seal` deterministic seal commit |

**Cycle outcome:** SEALED at `e335e6f9`. Seal-test
`plugins/dev-sdlc/tests/test_no_sealed_amendments.py` green; post-seal
`loam amend apply --dry-run` clean. Grep proofs: `apply.py:158` in
`plugins/dev-sdlc/` = 0; `thirteen sealed components` in `odd-in-loam.md` = 0.

§status — AC verdicts: AC.DSDA.1 GREEN; AC.DSDA.2 GREEN; AC.DSDA.3 GREEN;
AC.DSDA.S GREEN.
