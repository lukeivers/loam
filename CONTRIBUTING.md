# Contributing to loam

Thanks for considering a contribution. loam is a small project run by
one maintainer on a personal account; small, well-scoped contributions
are the most useful kind.

This document covers: what loam expects from a contribution, how to
shape an issue or pull request, the methodology loam practices
internally and asks contributors to read briefly, and the sign-off
model.

---

## Before you open an issue or PR

1. **Read [`docs/positioning.md`](docs/positioning.md).** Most
   contribution friction comes from a mismatch between what loam is
   and what a contributor wishes loam was. The positioning doc is the
   pitch and the non-goals; it is short.
2. **Skim [`docs/design/odd.md`](docs/design/odd.md).** loam practices
   Objective-Driven Design (ODD) natively. You do not need to be an
   ODD expert to contribute, but a one-paragraph familiarity with the
   "objective + acceptance criterion + builder picks the method"
   shape will save you and the reviewer time.
3. **Search existing issues.** loam tracks ideas, gaps, and known
   limitations on the GitHub issue tracker. If you are reporting a
   bug or proposing a feature, it may already be open.

## What loam expects from a contribution

loam asks every non-trivial contribution to carry, in some form:

- **An objective.** What state of the world should be true after this
  change lands? One sentence is fine.
- **At least one acceptance criterion.** How would a reviewer
  deterministically check the objective is met? "The test in
  `tests/test_X.py` passes" is a perfectly good AC if the test
  asserts the outcome, not the implementation detail.
- **A constraint envelope.** What may be touched, what may not.
  Sealed components are sealed for a reason — see "Sealed components"
  below. If your change crosses a sealed-component boundary, the PR
  description should name that explicitly.
- **A halt trigger for autonomous reviewers.** If your contribution
  is large or experimental, name the conditions under which a
  reviewer should halt and surface concerns rather than continue —
  e.g. "halt if the test surface grows beyond N modules without a
  proportional AC growth."

For a typo fix, a docs clarification, or a one-line bug fix, the
above can be implicit (the objective is "this typo is gone"; the AC
is "the typo is gone"). For anything that touches runtime behaviour,
write the four points down in the PR description.

## How to shape a pull request

1. **Branch from `main`.** Name the branch something descriptive:
   `fix/memory-sidecar-restart-race`, `feat/dev-sdlc-template-set`.
2. **Keep PRs scoped.** One objective per PR, ideally. If your
   change has two distinct outcomes, two PRs review faster than one.
3. **Tests are part of the change.** Every new behaviour needs a
   test that asserts the outcome. Tests that re-assert the
   implementation (specific class names, internal structures) tend
   to fight refactors; tests that assert observable outcome do not.
4. **Run the touched component's test suite before pushing.** loam
   is a Python project; each component carries its own pyproject and
   test suite. The component's `README.md` (where present) names the
   commands.
5. **Write the commit message in the project's style.** loam uses a
   conventional-commits-adjacent style: `feat(<component>): ...`,
   `fix(<component>): ...`, `docs(<area>): ...`, `chore(<area>): ...`.
   The body explains the why; the title explains the what. See
   recent `git log` for examples.

## Sealed components

Several loam components are **sealed**: their public contract is
locked, their tests-of-record are pinned to a baseline commit, and
changes inside the sealed surface go through an *amendment* shape
(name the amendment, name the AC the amendment adds or sharpens, run
the seal-diff test). The amendment workflow is internal-development
machinery; external contributors do not need to know how it works,
but they do need to know that PRs touching a sealed component will be
asked to either:

- frame the change as an amendment (the maintainer can help),
- relocate the change to an unsealed surface (often the right
  answer), or
- be rejected as out of scope for the contribution shape.

The shipping components in v0.1.0 are listed in
[`docs/architecture.md`](docs/architecture.md). If you are unsure
whether a component is sealed, ask in the PR or open an issue first.

## Methodology — ODD in one paragraph

Work in loam is defined by its observable outcome (objective) plus
deterministic checks (acceptance criteria) plus method-bounding
constraints. The author of the objective does not prescribe the
method; the builder picks it. Discovered gaps are re-extended up the
objective chain as new positive ACs, not buried as silent exception
branches. Failures during build are halt-and-signal, not push-through.
Structural enforcement (Pydantic schemas, type constructors, refusal
at construction) is preferred over advisory prose where structure can
reach. The full short-form is at
[`docs/design/odd.md`](docs/design/odd.md).

## Sign-off model

loam uses [Developer Certificate of Origin (DCO)](https://developercertificate.org/)
sign-off on every commit. Sign your commits with `git commit -s`; the
trailer

```
Signed-off-by: Your Name <your.email@example.com>
```

certifies you have the right to submit the work under the project's
license (Apache-2.0).

CLAs are not required.

## License

By contributing, you agree your contributions are licensed under the
[Apache License, Version 2.0](LICENSE).

## Code of Conduct

loam follows a Code of Conduct that all contributors and maintainers
are expected to read. The document lives at `CODE_OF_CONDUCT.md`
(authored alongside the v0.1.0 license-and-governance scaffold).

## A note on cadence

The maintainer is one person with a real-world energy budget. PR
review may take days; issue triage may take longer. Small,
self-contained PRs are reviewed faster than large ones. Issues that
include a reproduction (steps + observed vs expected) are triaged
faster than issues that ask the maintainer to imagine the failure
mode.

If the project goes quiet for an extended period, that is the
maintainer's life, not a comment on your contribution. Patient
contributions are appreciated.

## Where to go next

- [`docs/positioning.md`](docs/positioning.md) — what loam is and is
  not.
- [`docs/architecture.md`](docs/architecture.md) — component map.
- [`docs/design/odd.md`](docs/design/odd.md) — methodology in 200
  lines.
- [`SECURITY.md`](SECURITY.md) — vulnerability reporting.
- [`LICENSE`](LICENSE) — Apache-2.0.
