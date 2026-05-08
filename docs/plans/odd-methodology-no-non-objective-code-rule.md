# Plan — ODD methodology doc edits: explicit "no non-objective code" rule

**Work item:** Chore commit — document edits only. No source code changed.
**Authored:** 2026-04-22 (this session).
**Status:** Plan written retroactively (edits already made; plan documents what landed).

---

## Objective

Make the "only build what the objectives require" principle explicit in
the canonical ODD documentation. Previously implicit across §2.4
(forbidden method), §4 (re-extension), §8.2.8 (silent exception
branches), but never stated as a standalone positive rule. Luke's
2026-04-22 ruling: "this is the entire fucking point of ODD. the system
does what is required to deliver the objectives. not to deliver
non-objectives."

## Acceptance criteria satisfied

These edits are documentation-only; the "acceptance" is that future
readers of the ODD docs see the rule explicitly rather than having to
infer it from adjacent sections.

- AC-1: `docs/odd-methodology.md` contains a new §2.5 ("Forbidden: code
  for cases the objectives do not name") positively stating the rule,
  with anti-patterns and remediation paths.
- AC-2: `docs/odd-methodology.md` §8.2 reviewer-checklist gains a new
  rule #9 for code without backing objective (renumbering subsequent
  items 9→10, 10→11, 11→12, 12→13).
- AC-3: `docs/odd-methodology.md` §9 quick-reference card gains a new
  block "Building only what the objectives require (§2.5)."
- AC-4: `docs/odd-methodology.md` §9 "Reviewing built work" gains a
  new step 3 for the §2.5 reverse-direction check.
- AC-5: `docs/odd-in-pos.md` §9 gains a new §9.7 with the Linux-code
  incident as the referenced case — worked example of the rule.
- AC-6: `docs/FUTURE_IDEAS.md` gains a new Core Development
  Convention "plan before code, always" (companion rule surfaced
  alongside §2.5 during the same session).

## Files changed

- `docs/odd-methodology.md` — §2.5 added, §8.2 rule list expanded + renumbered, §9 reference card expanded.
- `docs/odd-in-pos.md` — §9.7 added.
- `docs/FUTURE_IDEAS.md` — new Core Development Convention inserted before "setup scripts self-retire on success."

## Validation

Doc-only changes — no code behaviour affected, no tests to run.

Verification:
- `git diff --stat HEAD` shows changes confined to the three docs above.
- The three documents are self-consistent: §2.5 in odd-methodology.md
  is cross-referenced by §9.7 in odd-in-pos.md and by the "plan before
  code" CDC in FUTURE_IDEAS.md.

## Halt triggers

- If git status shows any changed file outside the three listed above, halt.
- If any sealed component's `test_no_sealed_amendments.py` would fail against the diff, halt. (Expectation: seal tests pass because the paths `docs/odd-methodology.md`, `docs/odd-in-pos.md`, `docs/FUTURE_IDEAS.md` are not under any sealed component's allowed-prefix claim — but these are top-level docs that have been edited in prior chore commits without reopening seals, consistent with Q1 ruling on doc-only edits.)

## ODD compliance check

This is a doc-only commit; the rule being added (§2.5) is itself the ODD-compliance framing. No tests, no source code. The commit adds to the authoritative contract of the methodology; it does not create new components or amendments.
