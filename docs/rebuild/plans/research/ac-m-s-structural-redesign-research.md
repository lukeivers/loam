# AC.M.S structural redesign — first-principles research

**Trigger:** `odd-methodology.md` §4.5 — N≥2 hotfixes against the same
sealed-component test within the architecture-review threshold.
AC.M.S has paid the widening tax at amendment #50 (`6c90b9c`),
amendment #52 (`5acbd4e`), D-migration D.1 (transitional admission
on amendment #61), D-migration D.2 (`522f933` — explicit "loose-AC
tightening" admission), amendment #67 (H19 admission of `data`
infrastructure tagged onto AC.M.S), and amendment #68 (`45e8fbc` —
capability-corpus tree). Six widenings against one test. Past §4.5
threshold by ~3x; the gap is structural, not AC-level.

**Captured in:** `docs/rebuild/FUTURE_IDEAS_DRAFT.md` ("AC.M.S
structural brittleness — per-component SEAL_COMMIT vs per-amendment
fence mismatch", 2026-04-27).

---

## 1. Summary

The AC.M.S test in `framework/primary-persona/tests/test_AC_M_S_seal_diff_window.py`
is structurally mis-shaped. It declares itself as amendment #48's
fence (`allowed_prefixes` = paths #48 was authorised to touch), but
its diff window is `BASELINE..SEAL_COMMIT` where SEAL_COMMIT is the
floating per-COMPONENT sidecar that advances on every primary-
persona-touching amendment. Every legitimate post-#48 amendment
extends the window with paths the floating sidecar admitted, so the
test must be widened on every amendment that crosses primary-persona's
surface.

The same test shape EXISTS CORRECTLY for AC.45.S
(`framework/hands-off-lifecycle/tests/test_AC45_S_seal_diff_window.py`),
AC.SE.S (objective-tracker + hands-off-lifecycle), and AC.A.S, AC.E.S,
AC.B.S — they all freeze BOTH endpoints to the originating amendment's
window. The fix is well-precedented: convert AC.M.S to the
per-invariant BASELINE pattern (ODD §10.3) by pinning both BASELINE
and SEAL_COMMIT to amendment #48's exact window
(`de5fe11..452e7d4`), with the `allowed_prefixes` reverted to #48's
original fence text.

**Recommendation: Option C (per-invariant pinned-both-endpoints).**
This eliminates the failure class (per ODD §5.1.1) — no future code
change can re-introduce AC.M.S widening pressure because the test's
diff window is closed at #48's seal commit. Migration cost is low:
no SHA backfill needed (#48's window is in git history), no other
sealed components touched, no in-flight amendments at risk.

---

## 2. What invariant is AC.M.S supposed to protect?

Read in two ways. The current code suggests one reading; the test's
docstring + the originating plan suggest another.

### 2.1 The reading the code currently encodes

"Across the BASELINE → live-SEAL_COMMIT window of primary-persona,
the cumulative set of touched paths stays within an ever-widening
allowlist that started as #48's fence and grows with every
subsequent admission."

This is structurally identical to a cumulative-admissibility check
(ODD §10.1, frozen BASELINE) — except AC.M.S floats the SEAL_COMMIT
endpoint instead of expanding the allowlist with each amendment.
The floating-SEAL_COMMIT shape is wrong for cumulative-admissibility:
the test name says "amendment #48 fence" but the assertion is
"every primary-persona amendment ever has stayed within the
cumulative allowlist." The names disagree with the semantics.

### 2.2 The reading the docstring + plan encode

From the test's module docstring + the original locked plan §5
(amendment #48 plan, `docs/rebuild/plans/memory-system-live-client-
and-stop-hook-write.md` §AC.M.S):

> `git diff --name-only BASELINE..SEAL_COMMIT` shows only paths
> under: `primary-persona/src/`, `primary-persona/tests/`,
> `primary-persona/pyproject.toml`, `hands-off-lifecycle/hooks/`,
> `hands-off-lifecycle/tests/`, and the universal-paths admissions.

This is a **point-in-time invariant** (ODD §10.3) about amendment
#48's window: "during amendment #48's seal-diff window, only #48's
declared surfaces were touched." The fence was authored at amendment
authoring time; it is fixed by what #48 was scoped to do; the
window's upper bound is #48's seal commit (the moment the amendment
landed); the window's lower bound is #48's BASELINE (`de5fe11`).

This is the same shape as AC7-on-telegram-interface (the canonical
per-invariant prototype, `7d27f00`), AC.45.S, AC.SE.S, AC.A.S, AC.E.S,
AC.B.S.

### 2.3 The disagreement is the bug

Reading 2.1 (what the code does today) and reading 2.2 (what the
test name + docstring + plan say) are different invariants. AC.M.S
ships reading 2.1 because the test was authored to mirror
`test_no_sealed_amendments.py`'s floating-endpoint pattern, but
its CONTENT (the named-fence allowlist scoped to amendment #48's
admissions) is reading 2.2's content. The two were composed without
noticing they protect different things.

The §4.5-triggering observation: every amendment that legitimately
touches primary-persona's surface trips the test. Reading 2.1 should
not trip on legitimate amendments — by definition the floating
window admits paths admitted by `test_no_sealed_amendments.py`'s
own widening. So why does AC.M.S keep tripping?

Because AC.M.S's allowlist is **#48's fence** (reading 2.2's
content) — it does NOT inherit `test_no_sealed_amendments.py`'s
allowlist; it has its own narrower one. The floating-window math
(reading 2.1's behaviour) keeps admitting paths AC.M.S's narrower
allowlist doesn't recognise. The test is a hybrid of two invariants;
neither is well-formed.

---

## 3. Architectural-creep check — is the gap wider than AC.M.S?

Before recommending a fix scoped to AC.M.S, verify the gap doesn't
exist on every component's `test_no_sealed_amendments.py` or every
sibling AC.X.S.

### 3.1 Sibling AC.X.S tests — already correctly shaped

Read each:

| Test | Window endpoints | Pattern |
|------|-------------------|---------|
| `test_AC_M_S_seal_diff_window.py` | floating `BASELINE..SEAL_COMMIT` | **broken** (this research) |
| `test_AC45_S_seal_diff_window.py` | manifest baseline → hardcoded `_AMENDMENT_45_SEAL_COMMIT = 0702d25...` | per-invariant frozen-both ✓ |
| `test_AC_SE_S_seal_diff_window.py` (objective-tracker) | manifest baseline → hardcoded `97f7829...` | per-invariant frozen-both ✓ |
| `test_AC_SE_S_seal_diff_window.py` (hands-off-lifecycle) | (mirrors objective-tracker) | per-invariant frozen-both ✓ |
| `test_AC_A_S_seal_diff_single_component_scope.py` | (similar; manifest-rooted) | per-invariant ✓ |
| `test_AC_E_S_seal_diff_single_component_scope.py` (workspace-bootstrap) | (similar) | per-invariant ✓ |
| `test_AC_B_S_seal_diff.py` (loam-mode) | (similar) | per-invariant ✓ |

AC.45.S in particular carries a docstring documenting that exact bug:

> "Amendment #46 §2.5 fix: the original v1 of this test diffed
> `BASELINE..HEAD` rather than `BASELINE..SEAL_COMMIT`. That made
> the diff window expand monotonically as later amendments landed
> — intervening commits naturally fell outside #45's admission set,
> breaking the test on every later seal cycle."

Amendment #46 fixed AC.45.S's variant. AC.M.S is the same bug,
**still on disk**, simply unaddressed. The architectural gap was
recognised and corrected in #46 for one test; AC.M.S was never
back-converted.

### 3.2 `test_no_sealed_amendments.py` (the cumulative seal-diff test) — correctly shaped

`test_no_sealed_amendments.py`'s contract is "across the floating
amendment window, only known component prefixes were touched." That
test's allowlist is INTENTIONALLY broad (top-level component
buckets) and INTENTIONALLY widened on every amendment (each
component's bucket is admitted; each cross-cutting plan path is
admitted). Floating-SEAL_COMMIT + monotonically-growing-allowlist
is the right shape for that contract.

The contamination check (§10.2) and AC.M.S (§10.3) protect different
invariants. The contamination check's broad-allowlist + floating-
endpoint composition is correct; AC.M.S's narrow-allowlist +
floating-endpoint composition is the bug.

### 3.3 Conclusion: the gap is AC.M.S-only

No architectural creep. The plan can scope to AC.M.S exclusively;
no other sealed-component fence needs touching. (See §6 for the
adjacent ODD §10 doc clarification — that's a doc-only edit, not
new architecture.)

---

## 4. Candidate fixes enumerated

### Option A — Lock diff window to amendment #48's frozen window (FUTURE_IDEAS_DRAFT.md (i))

**How:** replace `_seal_commit()` and `_baseline()` resolution with
hardcoded SHAs. Pin `BASELINE = "de5fe11"` and
`SEAL_COMMIT = "452e7d4"`. Revert `allowed_prefixes` to amendment
#48's original fence text (the narrower set: `primary-persona/src/`,
`primary-persona/tests/`, `primary-persona/pyproject.toml`,
`hands-off-lifecycle/hooks/`, `hands-off-lifecycle/tests/`,
`hands-off-lifecycle/seals/`, `docs/rebuild/plans/`,
`docs/rebuild/plans/research/`, plus universal-paths files —
exactly what amendment #48's locked plan §AC.M.S declared).

**Invariant protected:** "during amendment #48's seal-diff window
(`de5fe11..452e7d4`), only #48's declared surfaces were touched."
Point-in-time fact, never re-evaluated.

**Failure classes caught:**
- A future amendment cannot retroactively fabricate a commit inside
  #48's window with surfaces #48 didn't admit (git history is
  immutable; any reflog tampering shows up as a different SHA).
- Reviewers reading the test years from now know exactly what #48
  was authorised to touch.

**Failure classes missed:**
- Anything outside #48's window is not AC.M.S's concern (which is
  CORRECT — that's the point). The cumulative seal-diff is
  `test_no_sealed_amendments.py`'s job; the per-amendment
  contamination check is the floating sidecar's job; the
  per-amendment fence-fidelity is per-invariant ACs like AC.M.S /
  AC.45.S / AC.SE.S.

**Eliminates vs relocates (ODD §5.1.1):** ELIMINATES.
- Both endpoints are constant SHAs. No mechanism advances either.
- A future maintainer cannot re-introduce widening pressure on
  AC.M.S because the diff window is closed. There is no rule to
  forget.
- Any later amendment touches its own per-invariant AC (AC.X.S of
  whichever amendment it is). AC.M.S is closed.

**Implementation cost:**
- Edit one test file (~150 LOC → ~80 LOC; net simplification).
- Constants resolve from amendment #48's known SHAs (research-doc
  evidence below; both endpoints in git log).
- No `pos-amend` schema change.
- No other sealed component touched.
- No migration of already-landed amendments needed (they don't
  re-evaluate AC.M.S after seal).

**Migration path:**
- Amendment commit edits the test in place.
- BASELINE remains anchored to `de5fe11`; SEAL_COMMIT pinned to
  `452e7d4`.
- The `pos-amend apply` step on this amendment must SKIP the
  AC.M.S test's prefix-tuple-widening pass (it does nothing —
  the tuple no longer participates in cross-amendment admissions).
  This requires either (a) the test using a recognisable
  `_AMENDMENT_*` constant naming convention pos-amend ignores, or
  (b) a per-test `frozen_window: true` marker mirroring the
  `frozen_baseline: true` precedent (amendment #23).

### Option B — Per-amendment frozen SEAL_COMMIT alongside the floating one (FUTURE_IDEAS_DRAFT.md (ii))

**How:** introduce a second SEAL_COMMIT-like sidecar named
`SEAL_COMMIT.amendment-48` (or similar), pinned to #48's seal
commit, never advanced. AC.M.S's `_seal_commit()` reads this new
sidecar instead of the live floating sidecar. `_baseline()`
similarly pins to a per-amendment manifest baseline.

**Invariant protected:** same as Option A — point-in-time on #48's
window.

**Differences from A:**
- Endpoints live on disk (sidecar), not in code constants.
- `pos-amend apply` would need to know to NEVER advance the
  per-amendment sidecar.
- Other components could use the same pattern.

**Eliminates vs relocates (ODD §5.1.1):** RELOCATES.
- A future maintainer who introduces a new per-amendment AC.X.S
  must remember to author the per-amendment sidecar AND remember
  to mark it as "never-advance" in the pos-amend manifest.
  Forgotten, the failure mode (advancing endpoint silently
  re-scopes the proof) returns.
- The mechanism shifts the burden from "remember the rule" to
  "remember to author the sidecar correctly," which is a different
  rule on the same failure class.

**Implementation cost:**
- New sidecar file per amendment that needs per-invariant pinning.
- pos-amend schema extension (per-component or per-test
  `frozen_seal_commit: bool` marker).
- Tool tests for the new advance-or-skip path.
- Backfill: amendment #48 needs the sidecar authored retroactively
  (`framework/primary-persona/tests/SEAL_COMMIT.amendment-48`
  containing `452e7d4...`).
- Other already-landed AC.X.S tests don't need the new sidecar —
  they hardcode SHAs in code, which is fine; only AC.M.S is the
  outlier.

**When it'd be the right call:**
- If many tests needed point-in-time pinning AND if living-on-disk
  endpoints had a robustness advantage over in-code constants.
- Neither is true here. The other AC.X.S tests use in-code
  constants successfully; introducing a sidecar mechanism for one
  failing test is over-engineering.

### Option C — Per-invariant BASELINE pattern (ODD §10.3 — what the other AC.X.S tests already use)

**How:** rewrite AC.M.S as a single function with hardcoded
amendment-#48 SHAs, mirroring AC.45.S / AC.SE.S verbatim:

```python
_AMENDMENT_48_BASELINE = "de5fe11e48d848332db339273cabe6ca0c3faa69"
_AMENDMENT_48_SEAL_COMMIT = "452e7d45feb63d4024d7d6bd123b65f1e5da7ffe"

_ALLOWED_PREFIXES: tuple[str, ...] = (
    "primary-persona/src/",
    "primary-persona/tests/",
    "primary-persona/pyproject.toml",
    "hands-off-lifecycle/hooks/",
    "hands-off-lifecycle/tests/",
    "hands-off-lifecycle/seals/",
    "docs/rebuild/plans/",
    "docs/rebuild/plans/research/",
)
_ALLOWED_FILES: frozenset[str] = frozenset({
    "CLAUDE.md",
    "docs/odd-in-pos.md",
    "docs/odd-methodology.md",
    "docs/rebuild/FUTURE_IDEAS.md",
})

def test_AC_M_S_seal_diff_within_amendment_48_fence() -> None:
    out = subprocess.check_output(
        ["git", "diff", "--name-only",
         f"{_AMENDMENT_48_BASELINE}..{_AMENDMENT_48_SEAL_COMMIT}"],
        cwd=REPO_ROOT, text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]
    offending = [
        p for p in changed
        if not any(p.startswith(pref) for pref in _ALLOWED_PREFIXES)
        and p not in _ALLOWED_FILES
    ]
    assert offending == [], (
        f"AC.M.S violation: paths outside the amendment #48 fence: "
        f"{offending}"
    )
```

**This is functionally Option A with the test fully aligned to the
project's existing per-invariant pattern.** The difference from A is
purely cosmetic (constant naming + comment-block pointing to ODD
§10.3 instead of inventing a new pattern). C is the recommended
shape because it's identical to existing canonical examples.

**Invariant protected:** point-in-time, "during #48's window, only
#48's declared surfaces were touched."

**Failure classes caught + missed + eliminates vs relocates:**
identical to Option A. ELIMINATES the widening-pressure failure
class.

**Implementation cost:** lower than Option A (no naming
convention design needed; just mirror AC.45.S):
- ~70 LOC deleted; ~60 LOC added in the more compact shape.
- No pos-amend tool changes (the existing AC.45.S, AC.SE.S, AC.A.S
  etc. tests live alongside pos-amend without special handling
  because they don't expose tunable SEAL_COMMIT-like constants for
  the tool to advance — they hardcode SHAs in private
  `_AMENDMENT_*` names, which the tool's regex doesn't match).
- The current SEAL_COMMIT-sidecar resolver (`_seal_commit()`) is
  removed from the test; the live sidecar is read only by
  `test_no_sealed_amendments.py` going forward.
- The current `_baseline()` indirection (which read BASELINE from
  the sibling `test_no_sealed_amendments.py`) is removed.

**Migration path:** clean.
- One test-file rewrite. No SHA backfill across other amendments
  (the test's correctness depends only on #48's two SHAs, which
  are in the historical git log).
- No retroactive amendment to #50, #52, D.1, D.2, #67, or #68 —
  those amendments paid the AC.M.S widening tax in their own
  diffs, but those widenings simply become dead code (the
  `allowed_prefixes` tuple no longer exists in the new test
  shape). The git history of those amendments is unchanged; the
  test that validated them widening their fences is replaced.
- The amendment that lands Option C must explicitly admit the
  edits to `test_AC_M_S_seal_diff_window.py` in its own
  `test_no_sealed_amendments.py` allowlist (which already admits
  `framework/primary-persona/tests/`).

### Option D — Prune AC.M.S; replace with manifest-driven fence-checks-the-manifest (FUTURE_IDEAS_DRAFT.md (iii) variant)

**How:** delete AC.M.S as a stand-alone test. Replace with a
`pos-amend`-side validation that the per-amendment `manifest.yaml`'s
declared `extra_allowed_prefixes` + `extra_allowed_files` exactly
match the diff between the manifest's `baseline:` field and the
amendment's seal commit. The validation runs at `pos-amend seal`
time, not as a post-hoc test.

**Invariant protected:** "the amendment's manifest correctly declared
its scope before the amendment landed."

**Failure classes caught:**
- An amendment that touches paths outside its declared scope is
  caught at seal time.

**Failure classes missed:**
- A historical record of "amendment #48 was authorised to touch
  exactly X" is no longer asserted in the test tree. The audit
  trail moves into the manifest history, which is harder to
  navigate than a named test.

**Eliminates vs relocates (ODD §5.1.1):** RELOCATES.
- The test moves from per-component test tree into the pos-amend
  tool. A future maintainer of pos-amend who breaks the validator
  re-introduces the failure mode (manifest scope drifts from
  reality, no test catches it).
- The structural enforcement is now at one chokepoint instead of
  per-component, but the chokepoint is rule-shaped: "remember to
  add this validation to pos-amend seal." If the validation is
  removed, no test catches the regression.

**Implementation cost:**
- pos-amend tool gains a new validate-on-seal step.
- Every amendment's manifest now needs scope-completeness
  guarantees.
- All AC.X.S tests (not just AC.M.S) become candidates for
  retirement, which is wider scope than this research's trigger.
- Re-shapes the per-invariant BASELINE convention — moves the
  point-in-time fence from test code into manifest data.

**When it'd be the right call:**
- If AC.X.S tests were systematically painful (six of them; six
  pieces of largely identical code). They're not — the others are
  stable; only AC.M.S is broken.
- This option re-architects the right thing for the wrong reason.
  The per-invariant BASELINE convention is sound; AC.M.S just
  doesn't follow it.

### Option E — Replace AC.M.S with a fence-shape that's stable: assert that the manifest's declared admissions superset the diff (FUTURE_IDEAS_DRAFT.md (iii) ALT)

**How:** AC.M.S becomes "every path in the BASELINE..SEAL_COMMIT
window is admitted by the union of the manifest's declared
prefixes/files PLUS the cumulative `test_no_sealed_amendments.py`
allowlist." The test reads the live floating sidecar but compares
against a dynamically-computed allowlist (the manifest's declared
scope at that amendment's time, plus universals).

**Invariant protected:** "the live primary-persona window has not
exceeded its declared scope at any amendment along the way."

**Failure classes caught:**
- Same as Option A on the current amendment.

**Failure classes missed:**
- The point-in-time fact about #48's window is no longer asserted
  (the assertion is now about the live cumulative window).

**Eliminates vs relocates:** RELOCATES.
- Failure mode shifts from "remember to widen AC.M.S allowlist"
  to "remember the manifest declared scope correctly at each
  amendment."
- This is a worse trade because the manifest is amendment-scoped
  and gets garbage-collected after the amendment seals; reading
  cumulative manifest state is non-trivial.

**Implementation cost:** high.
- Cross-amendment manifest reading.
- Significantly more code than the other options.
- Likely to introduce new edge cases.

---

## 5. Recommendation: Option C

**Why C over A:** identical semantics; C aligns with the existing
project canon (AC.45.S, AC.SE.S, AC.A.S, AC.E.S, AC.B.S) verbatim.
A reader who understands AC.45.S immediately understands AC.M.S
under C; under A they'd need to learn a new naming convention.

**Why C over B:** B introduces sidecar machinery + pos-amend schema
extension to solve a problem the canonical pattern (in-code SHAs)
already solves cleanly. ODD §5.1.1 prefers the option that
eliminates the failure class with less mechanism. C's two SHA
constants beat B's sidecar-plus-tool-flag for the same outcome.

**Why C over D:** D re-architects six tests to fix one. Its
elimination claim is weaker (the rule moves into pos-amend tool;
removing the validator removes the protection); C's elimination
claim is unconditional (the SHAs are constants in code, never
re-evaluated).

**Why C over E:** E re-introduces drift surfaces (cumulative
manifest reading, complex allowlist computation) to defend against
a problem (point-in-time invariant erosion) C eliminates by
construction.

---

## 6. Adjacent ODD §10 documentation clarification

`odd-methodology.md` §10 introduces the per-invariant BASELINE
convention but the §10.3 code template freezes only BASELINE; the
SEAL endpoint is left implicit ("amendment_9_seal" appears in the
example but isn't named as part of the convention). `odd-in-pos.md`
§10.3 carries the same template.

In practice, every existing per-invariant test (AC.45.S, AC.SE.S,
etc.) freezes BOTH endpoints. The convention's content is correct;
the template's wording could be tightened to name "frozen-both-
endpoints" explicitly.

This is an opportunistic doc tightening (per ODD §4 / the
loose-AC-text-fix convention applied to a methodology doc). The
plan should include this as a small-scope §10.3 rewording so
future per-invariant ACs author with frozen-both-endpoints by
default.

This change is doc-only, fits inside the same amendment, does not
expand the fence (admitted via universal-paths), and prevents a
future author from authoring another floating-endpoint per-invariant
test by misreading the template.

---

## 7. Migration path

Required actions:

1. Rewrite `framework/primary-persona/tests/test_AC_M_S_seal_diff_window.py`
   to mirror AC.45.S / AC.SE.S verbatim. Hardcode amendment #48's
   BASELINE (`de5fe11`) and SEAL_COMMIT (`452e7d4`). Allowlist
   reverts to amendment #48's original locked-plan §AC.M.S fence
   (no D.1 / D.2 / #67 / #68 transitional admissions; those are
   no longer relevant once the window is pinned).
2. Tighten `docs/odd-methodology.md` §10.3 + `docs/odd-in-pos.md`
   §10.3 template wording to name "frozen-both-endpoints" as the
   convention default. Doc-only.
3. Run the full primary-persona test suite (the test must pass
   against #48's window, exactly as it would have at #48's seal
   time).
4. Run `test_no_sealed_amendments.py` on primary-persona (the
   floating-sidecar contamination check is unchanged; it admits
   primary-persona/tests/ edits via the existing allowlist).

Not required:

- No SHA backfill across already-landed amendments (#50, #52,
  D.1, D.2, #67, #68). Their widening commits (`6c90b9c`,
  `5acbd4e`, `522f933`, `45e8fbc`) become historical artefacts
  of a since-removed widening surface; their git diffs are
  unchanged.
- No `pos-amend` schema change.
- No other sealed components touched.

---

## 8. Verified amendment-#48 endpoints

From git log + the amendment-48 plan + the §14 method-decision
register:

- **BASELINE** (`baseline:` field in
  `docs/rebuild/plans/memory-system-live-client-and-stop-hook-write.manifest.yaml`):
  `de5fe11e48d848332db339273cabe6ca0c3faa69`. Pre-amendment-#48
  tip; immediately precedes commit `74cdf4e` (#48's primary
  feat-commit).
- **Amendment commit** (#48 feat): `a193c32ce4e98186c2b341d7dbe191961db69892`.
  (Note: this is the BASELINE-bump chore; the #48 feat is
  `74cdf4e`. The §14 register names `a193c32` as the
  "amendment commit" because pos-amend records the BASELINE-
  advancing commit as the per-amendment SHA. For AC.M.S
  purposes, the upper bound is the seal commit, not the feat
  commit.)
- **Seal commit** (#48 chore-seal): `452e7d45feb63d4024d7d6bd123b65f1e5da7ffe`.
  Per the §14 method-decision register entry confirmed in
  commit `052b49b`'s diff.

The window `de5fe11..452e7d4` is what AC.M.S should diff. Every
path in that window's git output is admissible against #48's
locked-plan §AC.M.S fence (verifiable: that exact assertion was
green when #48 sealed; pinning re-asserts the same fact).

---

## 9. Halt signals encountered

- **None on architectural creep.** §3 confirms the gap is
  AC.M.S-specific; sibling AC.X.S tests are correctly shaped.
- **None on migration ambiguity.** §7 + §8 list no SHAs that need
  backfilling beyond amendment #48's two SHAs, both of which are
  recoverable from canonical's git log.
- **None on fence ambiguity.** The plan's amendment touches only
  `framework/primary-persona/tests/test_AC_M_S_seal_diff_window.py`
  + the two ODD docs (`docs/odd-methodology.md`,
  `docs/odd-in-pos.md`). All within `primary-persona`'s sealed
  fence + universal-paths admissions.

---

## 10. Open questions

None resolved by the dispatcher. The recommendation is unambiguous
from the canonical tree's evidence (six existing AC.X.S tests
already implement Option C's pattern; AC.45.S explicitly documents
the exact bug and its fix; ODD §10 names the convention).

---

## 11. References

- `framework/primary-persona/tests/test_AC_M_S_seal_diff_window.py` —
  the broken test.
- `framework/hands-off-lifecycle/tests/test_AC45_S_seal_diff_window.py` —
  the canonical Option-C example with the docstring documenting
  this exact bug class.
- `framework/objective-tracker/tests/test_AC_SE_S_seal_diff_window.py`,
  `framework/hands-off-lifecycle/tests/test_AC_SE_S_seal_diff_window.py`,
  `framework/primary-persona/tests/test_AC_A_S_seal_diff_single_component_scope.py`,
  `framework/workspace-bootstrap/tests/test_AC_E_S_seal_diff_single_component_scope.py`,
  `framework/tools/loam-mode/tests/test_AC_B_S_seal_diff.py` —
  five additional Option-C-shape examples.
- `docs/odd-methodology.md` §4.5 — N≥2 hotfix architecture-
  review trigger.
- `docs/odd-methodology.md` §5.1.1 — relocate-vs-eliminate.
- `docs/odd-methodology.md` §10 (and `docs/odd-in-pos.md` §10.3) —
  per-invariant BASELINE convention.
- `docs/rebuild/plans/memory-system-live-client-and-stop-hook-write.md`
  §AC.M.S — amendment #48's original AC.M.S text (the fence
  Option C reverts the allowlist to).
- `docs/rebuild/plans/amendment-23-frozen-h19-per-invariant-baseline.md` —
  the canonical introduction of frozen-vs-floating BASELINE.
- `docs/rebuild/FUTURE_IDEAS_DRAFT.md` ("AC.M.S structural
  brittleness") — the originating capture.
