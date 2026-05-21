# Plan — AC.M.S structural redesign (per-invariant frozen-both-endpoints)

**Trigger:** ODD §4.5 (N≥2 hotfix architecture-review threshold).
AC.M.S has been widened ~6 times since amendment #48 sealed.

**Research doc:** `docs/plans/research/ac-m-s-structural-redesign-research.md`.

**Recommended option (per research §5):** Option C — convert AC.M.S
to the per-invariant BASELINE pattern (ODD §10.3) with both endpoints
frozen to amendment #48's window (`de5fe11..452e7d4`). Same shape as
existing canonical examples (AC.45.S, AC.SE.S, AC.A.S, AC.E.S, AC.B.S).

---

## 1. Summary

One amendment. Rewrites `framework/primary-persona/tests/test_AC_M_S_seal_diff_window.py`
to mirror AC.45.S verbatim: hardcoded `_AMENDMENT_48_BASELINE` +
`_AMENDMENT_48_SEAL_COMMIT` constants, allowlist reverted to
amendment #48's locked-plan §AC.M.S fence text. Adjacent doc-only
tightening of `odd-in-pos.md` §10.3 to name "frozen-both-endpoints"
as the convention default (preventing re-occurrence of the same bug
class in a future per-invariant test).

**Build-time tightening (loose-AC fix per ODD §4 / global feedback
"Loose AC text → fix the AC"):** the plan and research initially
named both `odd-methodology.md` §10.3 and `odd-in-pos.md` §10.3 as
edit targets; empirical inspection at build time shows
`odd-methodology.md` has no §10.3 (its §10 is "Where this fits", end
of doc; the per-invariant BASELINE convention lives entirely in
`odd-in-pos.md` §10). The plan's intent was "tighten the docs that
carry the convention"; only `odd-in-pos.md` carries it. AC.MS-fix.6
is tightened to name only `odd-in-pos.md` §10.3 below.

Eliminates (per ODD §5.1.1) the AC.M.S widening-pressure failure
class — no future code change can re-introduce widening pressure
because the diff window is closed at #48's seal commit.

Touches one sealed component (`primary-persona`) and two
universal-admitted docs. No `pos-amend` schema change. No
backfill across other amendments.

---

## 2. Objective

`framework/primary-persona/tests/test_AC_M_S_seal_diff_window.py`
asserts a point-in-time invariant about amendment #48's sealed
window: only paths under amendment #48's declared fence appear in
`git diff --name-only de5fe11..452e7d4`. The test's diff window is
frozen at both endpoints; subsequent amendments cannot alter the
test's assertion.

Adjacent: `docs/odd-in-pos.md` §10.3 template wording explicitly
names the frozen-both-endpoints convention; the code template
freezes both BASELINE and SEAL constants (not BASELINE only).
(`docs/odd-methodology.md` was named in the original plan and
research but does not carry a §10.3 — see §1 build-time tightening.)

---

## 3. Acceptance criteria

### AC.MS-fix.1 — AC.M.S diff window is frozen at both endpoints

`test_AC_M_S_seal_diff_window.py` defines two module-level constants
(`_AMENDMENT_48_BASELINE`, `_AMENDMENT_48_SEAL_COMMIT`) holding
amendment #48's BASELINE SHA (`de5fe11e48d848332db339273cabe6ca0c3faa69`)
and amendment #48's seal commit SHA (`452e7d45feb63d4024d7d6bd123b65f1e5da7ffe`)
respectively. The test diffs against these constants, not against
the live `SEAL_COMMIT` sidecar or a sibling-test BASELINE indirection.
Removed: the previous `_seal_commit()` resolver and `_baseline()`
read-from-sibling indirection.

### AC.MS-fix.2 — AC.M.S allowlist reverts to amendment #48's locked-plan fence

The test's allowed-prefixes tuple + allowed-files set match
amendment #48's locked-plan §AC.M.S fence text verbatim, modulo
the `framework/` prefix that D.1 introduced (path-prefix preserved
because the historical window's diff output uses pre-D.1 paths;
verified at AC.MS-fix.5). No D.1, D.2, #67, or #68 transitional
admissions remain — every prefix or file in the test must trace
back to amendment #48's plan §AC.M.S.

### AC.MS-fix.3 — AC.M.S test passes against amendment #48's window

`pytest framework/primary-persona/tests/test_AC_M_S_seal_diff_window.py`
runs from the repository root, exits 0, and the single test function
asserts no offending paths.

### AC.MS-fix.4 — `test_no_sealed_amendments.py` continues to pass

`pytest framework/primary-persona/tests/test_no_sealed_amendments.py`
exits 0 unchanged; the floating-SEAL_COMMIT contamination check on
primary-persona is not affected by the AC.M.S rewrite (the live
sidecar is no longer read by AC.M.S, but is still read by the
contamination test).

### AC.MS-fix.5 — Pre-D.1 path-prefix correctness for the historical window

`git diff --name-only de5fe11..452e7d4` is empirically verified to
emit paths under the PRE-D.1 layout (`primary-persona/`,
`hands-off-lifecycle/`), not the post-D.1 layout (`framework/...`).
The allowlist matches that pre-D.1 path shape exactly. The test
passes (AC.MS-fix.3) precisely because the historical window's
output is pre-D.1.

### AC.MS-fix.6 — ODD §10.3 doc clarification: frozen-both-endpoints named

`docs/odd-in-pos.md` §10.3 explicitly names "frozen-both-endpoints"
as the per-invariant default (distinct from §10.1's
frozen-BASELINE-only). The code template freezes BOTH endpoints.
A new author reading the convention writes a frozen-both-endpoints
test by default; floating-endpoint per-invariant assertions are not
the documented default shape.

`docs/odd-methodology.md` carries no per-invariant section (its §10
is "Where this fits"); no edit there. See §1 for build-time
tightening rationale.

### AC.MS-fix.7 — Behaviour-count match (ODD §3.3 forward + §2.5 reverse)

The plan declares 6 behaviours (AC.MS-fix.1 through AC.MS-fix.6);
each maps 1:1 to an AC. Reverse: the amendment diff contains
exactly the test rewrite + the two doc edits + this plan + manifest;
every code/doc path traces to a named AC. No orphan code, no orphan
doc edits.

### AC.MS-fix.S — Seal-diff window confined to declared fence

`git diff --name-only BASELINE..SEAL_COMMIT` (where BASELINE is the
manifest's declared baseline and SEAL_COMMIT is the sidecar value
post-seal) shows only paths under:

- `framework/primary-persona/tests/`
- `docs/odd-methodology.md` (universal-admission file)
- `docs/odd-in-pos.md` (universal-admission file)
- `docs/plans/` + `docs/plans/research/` (universal
  prefix)
- `framework/primary-persona/seals/` (seal narrative target)
- `framework/primary-persona/tests/SEAL_COMMIT` (sidecar advance,
  via pos-amend)
- `CLAUDE.md`, `docs/FUTURE_IDEAS.md` only if a relevant
  capture/append lands (not anticipated; halt-signal if a
  larger surface is needed).

This AC.MS-fix.S is itself a per-invariant frozen-both-endpoints
assertion. The test that verifies it (`test_AC_MS_fix_S_seal_diff_window.py`
or appended to AC.M.S file as a second test fn — builder's call)
hardcodes both endpoints to THIS amendment's window, not the live
floating sidecar — exactly mirroring the convention this amendment
codifies.

---

## 4. Constraints

### 4.1 Budget
Single amendment, scoped to one sealed component (`primary-persona`)
plus two doc edits. Estimated ≤ 100 LOC net change to test file
(rewriting at ~80 LOC from current ~150); ≤ 30 LOC per doc edit.
Build wall-clock ≤ 30 minutes for a background agent (one test
rewrite + two doc edits + pos-amend cycle).

### 4.2 Reversibility class
Fully reversible. The rewritten test asserts a strict subset of
the previous test's contract (the previous test was a hybrid of
two invariants; the new test asserts the well-formed half). If
the amendment lands and a defect surfaces, revert restores the
prior (broken) test which still passes today only because of
six historical widenings.

### 4.3 Dependency fence
- `primary-persona` — sealed; this amendment is authorised to
  touch `framework/primary-persona/tests/` only.
- `docs/odd-in-pos.md` — universal file (admitted per amendment
  #22 ruling #3); edited (§10.3 tightening). `docs/odd-methodology.md`
  is universal-admitted but not edited (no §10.3 to tighten; see §1).
- `docs/plans/` — universal prefix (this plan + manifest).
- No other sealed component may be touched. **Halt-and-signal if
  any other component's surface is touched.**
- No `pos-amend` tool changes (per research §4 Option C
  comparison; tool-side changes are Option B's territory and
  rejected).

### 4.4 Authority bound
Builder may:
- Choose internal helper-function structure in the rewritten test
  (one function vs split; named constants vs inline; etc.).
- Choose exact wording of the §10.3 doc clarification provided
  the named-named "frozen-both-endpoints" convention is established
  and the template freezes both endpoints.
- Choose whether AC.MS-fix.S lives as a second test function in
  the same file or a new file; the per-invariant contract is the
  same.

Builder must NOT:
- Add a `pos-amend` schema field.
- Touch any sealed component other than `primary-persona`.
- Restore any of the post-#48 widening admissions
  (`framework/primary-persona/src/`, `framework/workspace-sync/`,
  `framework/self-upgrade/`, `framework/tools/`,
  `docs/capability-corpus/`, etc.) to the AC.M.S
  allowlist — those were admissions of the broken pattern.

### 4.5 Fail-closed direction
If the historical window `de5fe11..452e7d4` empirically emits a
path the locked-plan §AC.M.S fence does NOT admit (e.g. an
unexpected change to a sibling component during #48's window),
the build halts and surfaces the discrepancy. The plan's content
of AC.MS-fix.2 + AC.MS-fix.5 is provisional on the historical
diff matching the locked plan; if it doesn't, an architecture-
shape question is open.

---

## 5. Halt triggers

The builder MUST halt and surface, not push through, when:

1. **Historical-window diff exceeds the locked-plan fence.** Running
   `git diff --name-only de5fe11..452e7d4` from canonical's tree
   emits a path the AC.MS-fix.2 allowlist does not admit. Halt;
   surface to dispatcher; the plan's allowlist may need a
   one-time admission that should be authored explicitly with
   research-doc-grade rationale.
2. **Sibling AC.X.S tests reveal a widely-shared structural gap.**
   If during the build the agent observes that AC.45.S, AC.SE.S,
   AC.A.S, AC.E.S, or AC.B.S have any analogous floating-endpoint
   defect, halt; surface to dispatcher; this amendment's scope
   narrows the architectural question to one test, but if siblings
   are also broken the plan needs to expand or defer.
3. **`pos-amend apply` mishandles the test's removed
   `allowed_prefixes` tuple.** The `pos-amend apply` regex
   currently widens in-function `allowed_prefixes` literals
   (FUTURE_IDEAS_DRAFT capture: amendment #50 corrective
   `6c90b9c`). With the literal removed, `apply` must do nothing
   to the test file. If `apply` errors or alters the file
   unexpectedly, halt; surface; the regex may need a no-match
   exit-clean path.
4. **ODD violations in the build's own work.** Method-in-AC,
   behaviour-count mismatch, missing halt trigger, orphan code.
   Self-check before seal; halt if any check fails.
5. **Architecture creep.** If the build surfaces evidence that
   `test_no_sealed_amendments.py`'s pattern is wrong, halt; that's
   a bigger architectural question and out of scope.

---

## 6. Method (suggested — builder's call to refine)

The shape that mirrors AC.45.S verbatim:

```python
"""AC.M.S — seal-diff fence for amendment #48's window.

Per ODD §10.3 per-invariant BASELINE convention (frozen-both-
endpoints). The window is amendment #48's seal-diff window
(de5fe11..452e7d4), pinned for the project's lifetime. The
allowlist matches amendment #48's locked-plan §AC.M.S fence text;
no post-#48 widenings remain.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

_AMENDMENT_48_BASELINE = "de5fe11e48d848332db339273cabe6ca0c3faa69"
_AMENDMENT_48_SEAL_COMMIT = "452e7d45feb63d4024d7d6bd123b65f1e5da7ffe"

_ALLOWED_PREFIXES: tuple[str, ...] = (
    "primary-persona/src/",
    "primary-persona/tests/",
    "primary-persona/pyproject.toml",
    "hands-off-lifecycle/hooks/",
    "hands-off-lifecycle/tests/",
    "hands-off-lifecycle/seals/",
    "docs/plans/",
    "docs/plans/research/",
)
_ALLOWED_FILES: frozenset[str] = frozenset({
    "CLAUDE.md",
    "docs/odd-in-pos.md",
    "docs/odd-methodology.md",
    "docs/FUTURE_IDEAS.md",
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

The builder is free to adjust naming, comment style, and file
layout. The contract is the AC list, not this snippet.

The §10.3 doc clarification (in `odd-in-pos.md` only — methodology
doc has no §10.3) is similarly small: tighten the template (which
already shows BOTH endpoints as constants, but names the convention
only as "per-invariant BASELINE") to name "frozen-both-endpoints"
explicitly as the default and clarify that the SEAL endpoint is
frozen alongside BASELINE.

---

## 7. Bookkeeping (`pos-amend` manifest stub)

Single component:

```yaml
schema_version: 1
amendment_slug: ac-m-s-structural-redesign
plan: docs/plans/ac-m-s-structural-redesign.md
baseline: <pre-amendment-tip-sha>   # captured at dispatch

components:
  - name: primary-persona
    seal_test: framework/primary-persona/tests/test_no_sealed_amendments.py
    sidecar: framework/primary-persona/tests/SEAL_COMMIT
    frozen_baseline: false
    extra_allowed_prefixes: []
    extra_allowed_files: []

universal_paths:
  prefixes:
    - docs/plans/
    - docs/plans/research/
  files:
    - docs/odd-methodology.md
    - docs/odd-in-pos.md
    - CLAUDE.md
    - docs/FUTURE_IDEAS.md

narrative:
  target: framework/primary-persona/seals/SEAL_COMMIT.ac-m-s-structural-redesign
  body: |
    (builder fills at seal time per pos-amend seal --plan-doc;
     describe the AC.M.S structural redesign + the §10.3 doc
     tightening + the elimination claim per ODD §5.1.1.)
```

`hands-off-lifecycle` is NOT in components. The original AC.M.S
admitted hands-off-lifecycle paths (because amendment #48 touched
both components), but THIS amendment doesn't touch hands-off-
lifecycle code — only the test rewrite + doc edits. If
`hands-off-lifecycle/tests/SEAL_COMMIT` would need advancing for
H19's frozen-BASELINE-list update (because the test removed the
floating-sidecar dependency), evaluate at apply time; not
anticipated.

---

## 8. Out of scope

- Retiring AC.45.S, AC.SE.S, AC.A.S, AC.E.S, or AC.B.S — those
  are correctly shaped (research §3.1).
- Modifying `test_no_sealed_amendments.py` — its floating-sidecar
  pattern is correct for cumulative-admissibility (research §3.2).
- Modifying `pos-amend` to handle per-test frozen sidecars
  (Option B; rejected per research §5).
- Manifest-schema-driven validation replacing AC.X.S
  (Option D; rejected per research §5).
- Backfilling SHA pins into already-landed amendments' AC.X.S
  tests (none need it; only amendment #48's #48-specific test
  is broken).
- Restoring or "preserving" the post-#48 widening admissions —
  they were the broken-pattern's tax, not the well-formed
  invariant's content.

---

## 9. Implementation order (suggested — builder's call to refine)

1. Verify the historical diff against the locked plan: run
   `git diff --name-only de5fe11..452e7d4` from canonical; confirm
   every emitted path matches `_ALLOWED_PREFIXES` ∪ `_ALLOWED_FILES`.
   If any path doesn't match, halt per §5 trigger 1.
2. Author plan + manifest (this doc + manifest yaml).
3. `pos-amend validate` + `pos-amend apply --dry-run` → exit 0.
4. `pos-amend apply` → advances the BASELINE in
   `test_no_sealed_amendments.py` only (the AC.M.S file's
   in-function `allowed_prefixes` no longer exists; the apply
   regex must no-op on it cleanly, per §5 trigger 3).
5. Rewrite `test_AC_M_S_seal_diff_window.py` per the AC list +
   suggested method shape.
6. Edit `docs/odd-in-pos.md` §10.3 to name frozen-both-endpoints
   + tighten the template + clarify SEAL is also frozen. (No
   edit to `odd-methodology.md` — it carries no §10.3; see §1
   build-time tightening.)
7. (was: methodology-doc edit; dropped at build time per §1
   tightening.)
8. Run primary-persona test suite + sealed-component
   contamination check.
9. ODD §2.5 reverse audit on the diff.
10. **Amendment commit:**
    `feat(primary-persona, docs): AC.M.S structural redesign — frozen-both-endpoints per-invariant pin (AC.MS-fix.1–AC.MS-fix.S)`.
11. `pos-amend seal` → advances sidecar + appends narrative.
12. **Seal commit:**
    `chore(seals): ac-m-s-structural-redesign — frozen-both-endpoints AC.M.S — primary-persona at <amendment-sha>`.
13. Post-seal: ODD §2.5 self-audit; verify the new AC.M.S still
    asserts (now against the post-seal version of itself, which
    is unchanged because it's frozen-both-endpoints).

---

## 10. Behaviour-count check (ODD §3.3 forward)

| # | Declared behaviour | AC |
|---|--------------------|-----|
| 1 | Diff window endpoints frozen as constants | AC.MS-fix.1 |
| 2 | Allowlist reverted to #48's locked-plan fence | AC.MS-fix.2 |
| 3 | Test passes against #48's window | AC.MS-fix.3 |
| 4 | Contamination check unaffected | AC.MS-fix.4 |
| 5 | Pre-D.1 path-prefix correctness verified | AC.MS-fix.5 |
| 6 | §10.3 doc names frozen-both-endpoints | AC.MS-fix.6 |
| cross-cutting | ODD §2.5 forward+reverse coverage | AC.MS-fix.7 |
| cross-cutting | Seal-diff window respected (frozen-both) | AC.MS-fix.S |

6 behaviours, 8 ACs (two cross-cutting). No method-in-AC.

---

## 11. Risks

1. **Historical window contains a surprise.** Running the diff at
   build-time may reveal a path #48's locked plan didn't admit.
   Mitigation: §5 halt trigger 1; surface for ruling.
2. **`pos-amend apply` regex change.** With `allowed_prefixes`
   removed from the AC.M.S test, the in-function-literal-widening
   regex must no-op cleanly. If it errors, the FUTURE_IDEAS_DRAFT
   capture about regex limitations gets exercised. Mitigation: §5
   halt trigger 3; surface.
3. **Sibling tests turn out broken.** Research §3.1 inspected
   each; should the build observe a sibling that's actually
   floating-endpoint, surface (§5 halt trigger 2). Plan would
   then expand or defer the sibling fix.
4. **§10.3 doc tightening conflicts with another amendment in
   flight.** Unlikely (no amendment in flight is touching
   methodology docs per `docs/plans/`'s in-flight scan),
   but check at dispatch.

---

## 12. References

- Research doc: `docs/plans/research/ac-m-s-structural-redesign-research.md`.
- `framework/primary-persona/tests/test_AC_M_S_seal_diff_window.py` — current
  broken test.
- `framework/hands-off-lifecycle/tests/test_AC45_S_seal_diff_window.py` — canonical
  Option-C example.
- `docs/plans/memory-system-live-client-and-stop-hook-write.md` —
  amendment #48's locked plan + AC.M.S fence text.
- `docs/odd-methodology.md` §4.5, §5.1.1, §10.
- `docs/odd-in-pos.md` §10.3.
- `docs/plans/amendment-23-frozen-h19-per-invariant-baseline.md` —
  the canonical introduction of the convention.
- `docs/FUTURE_IDEAS_DRAFT.md` — originating capture
  ("AC.M.S structural brittleness").

---

## 13. ODD self-check before dispatch

- §8.1.1 method-in-acceptance: scanned. ACs name observable
  state ("constants exist", "test passes", "diff emits", "doc
  contains") not method ("uses pytest", "via Pydantic", "implements
  visitor"). ✓
- §8.1.2 behaviour-count: 6 declared behaviours ↔ 8 ACs (with
  two cross-cutting); see §10. ✓
- §8.1.3 missing acceptance: every objective sentence has a
  numbered AC. ✓
- §8.1.4 advisory-shaped acceptance: no "should be readable" /
  "should be helpful" criteria. ✓
- §8.1.5 procedure in objective: §6 is suggested method, marked
  as such; §9 is suggested order, marked as such. The objective
  in §2 is end-state. ✓
- §8.1.6 unbounded scope: budget (§4.1), reversibility (§4.2),
  dependency fence (§4.3), authority bound (§4.4), fail-closed
  (§4.5) all named. ✓
- §8.1.7 missing halt trigger: §5 lists 5. ✓
- §2.5 reverse direction: AC.MS-fix.7 names the reverse audit
  explicitly; the diff at build time will trace test rewrite →
  AC.MS-fix.1+.2+.5; doc edits → AC.MS-fix.6; manifest+plan →
  ODD §2.5 paper-trail; seal narrative → §AC.MS-fix.S. ✓

---

## 14. Method-decision register (post-build, builder-backfilled)

Method-level decisions made during the build land here at seal time
per `pos-amend seal --plan-doc` convention.

### Method decisions

- **Loose-AC tightening (§4 ODD / global feedback):** plan + research
  named both `docs/odd-methodology.md` §10.3 and `docs/odd-in-pos.md`
  §10.3 as edit targets. Empirical inspection at build time showed
  `docs/odd-methodology.md` carries no §10.3 (its §10 is "Where this
  fits"; the per-invariant BASELINE convention lives entirely in
  `docs/odd-in-pos.md` §10). Tightened AC.MS-fix.6 + plan §1, §2, §6,
  §9 to drop the methodology-doc edit; documented in §1 build-time
  tightening block. AC.MS-fix.6's intent ("name frozen-both-endpoints
  in the doc carrying the convention") is preserved; only the
  factually wrong second target is removed.

- **AC.MS-fix.S authoring pattern:** the seal SHA isn't knowable at
  amendment-author time. AC.MS-fix.S authored with a placeholder
  sentinel `__POST_SEAL_CORRECTIVE__` for `_AMENDMENT_69_SEAL_COMMIT`
  and a sentinel-branch early-return; corrective commit `19976d8`
  fills the constant with the actual seal SHA `3be9a78` immediately
  after `pos-amend seal` lands. Pattern is reusable for future
  per-invariant seal-diff fences that include the amendment's own
  window (mirrors AC.45.S, but AC.45.S was authored AFTER its seal
  via the §2.5 fix at amendment #46; this amendment authors its own
  seal-diff fence inline with the convention it codifies).

- **Workspace/ stash before seal:** untracked `workspace/` dir (local
  workspace-bootstrap output) tripped `pos-amend seal`'s dirty-tree
  pre-flight. Stashed via `git stash push -u -m ... -- workspace/`
  before seal; restored via `git stash pop` post-seal. Captured for
  `FUTURE_IDEAS_DRAFT` (gitignore `workspace/` at canonical's tree
  to avoid the recurring stash dance — see §6).

### Commit SHAs

- Amendment commit: `05ebce7a7f3f24f2601f1ea7cb22b466b94c6f18` —
  `feat(primary-persona,docs): AC.M.S structural redesign — frozen-both-endpoints per-invariant pin (amendment #69, AC.MS-fix.1–AC.MS-fix.S)`
- Seal commit: `3be9a783fe2cf95315780c835f0d10bb7e0bf6bb` —
  `chore(seals): ac-m-s-structural-redesign — frozen-both-endpoints AC.M.S — eliminates widening-pressure failure class per ODD §5.1.1 — primary-persona at 05ebce7`
- §14 backfill commit: `d87777d` — `docs(plans): record amendment #69 commit SHAs in method-decision register`
- AC.MS-fix.S corrective commit: `19976d8` —
  `fix(primary-persona): fill AC.MS-fix.S seal SHA post-amendment-#69 seal`
  (fills `_AMENDMENT_69_SEAL_COMMIT` with the actual seal SHA;
  removes the placeholder-sentinel branch).
