# loam v1.10.0 — CHANGELOG

**Class:** MINOR over published v1.9.1 (`next_MINOR(v1.9.1) = v1.10.0`).
**Quality tag:** END-USER — a new thing a loam user can do that they could
not do before.
**Migration:** `no-op` (`docs/state-migrations/v1-10-0-adversarial-review.migration.yaml`).
**Plan-doc:** `docs/plans/v1-10-0-adversarial-review.md`.

> **Objective —** A loam user can get a genuinely harsh, evidence-bound
> adversarial review of any artifact, on demand. Point loam at one artifact
> plus what it is supposed to accomplish and get back a validated,
> plain-language review whose harshness comes from how the review is
> built, not from asking a model to be brutal.

---

## Headline — adversarial review, on demand

Ask for it in plain language — "do an adversarial review of this proposal",
"tear this apart before I send it", "red-team my plan doc", "poke holes in
this" — and the new `adversarial-review` SKILL drives loam's standing
review capability and hands back the findings in plain English. You supply
the artifact and what it is meant to do; loam runs the review and translates
the result.

This closes a real gap. loam already had a lighter document pass
(`document-trust-review`) and a sealed-cycle conformance check
(`loam-reviewer`), but nothing that would take an arbitrary artifact and
try, hard and honestly, to break it against its own goal. Now it does.

The capability ships as a new component, `framework/adversarial-review/`,
at 0.1.0 and out of the install graph and lockstep set this cut — the same
way every new component has entered over the last several minors. The
`adversarial-review` SKILL is added to the loam-skills plugin so Claude
discovers it automatically.

## Why the review is actually harsh (and not theater)

AI review goes soft in predictable ways: it agrees with the author, prefers
its own writing, floods you with generic "could be more robust" notes,
invents flaws, and collapses to consensus when you run a panel. Every one of
those is countered by construction, not by a prompt telling the model to be
mean:

- **The critic never sees your world.** It is seeded with the artifact, its
  stated objective, the review method, and nothing else — not your
  conversation, not your own reasoning, not who wrote it. Sycophancy rides
  the author's context; the critic does not get that context.
- **It works out what a good artifact needs before it reads yours.** The
  "what should be here" step runs in a separate context that has never seen
  the artifact, then a second step reads your artifact and finds the gap. A
  criticism the critic derived itself is one it actually holds.
- **A flaw has to survive a fact-check before it can block.** Every finding
  is re-checked against ground truth. Ones that fail the check are kept
  visible but marked unconfirmed and cannot block. Recall stays high; the
  precision is spent in validation, never by making the critic timid.
- **A pass is not a rubber stamp.** A PASS is rejected as malformed unless it
  names its single strongest surviving objection and what the review could
  not check. Zero findings on a real artifact is treated as a reason to
  suspect the review, not a clean bill.
- **Generic notes are excluded from the verdict**, and every spawned critic
  runs through loam's sealed isolated-spawn path, so a review never quietly
  loads the operator's plugins and kills a live session.
- **The reviewer measures itself.** A seeded-flaw calibration reads back a
  catch rate, so "the review ran and looked harsh" can be checked against
  "the review actually caught the planted flaws". The shipped proof caught
  all of them.

Two depth settings: STANDARD (the default floor, one two-phase critic plus
validation and verdict) and DEEP for high-stakes work (several isolated
critics on different angles plus a separate judge that keeps their
disagreements, never a free-for-all panel).

## The automatic blocking gate ships OFF, on purpose

There is a second mode built in: a gate that fires at a boundary (a ship, a
seal, a send) and blocks on a failing verdict. It is present but switched
off, and it is not what this release is for. The supported outcome is the
manual, on-demand review.

The gate stays off until it earns activation, and the bar is written down:
its recall is proven, but its precision is not. Before it is ever allowed to
block real work, someone has to measure how often it would block a
genuinely clean artifact. A gate that blocks good work is worse than no
gate. Turning it on is a separate, owner-approved step, and the boundary
wiring is a separate build.

## Honesty flags

- The harshness is structural, but the model legs are still model legs. The
  guarantees loam can make it keeps — artifact-blind derivation, validation
  before blocking, a named residual on every pass, a measured catch rate.
  What it cannot promise is that a language model never misses.
- The auto-blocking gate is experimental and unwired. Do not read "loam has
  an adversarial-review gate" as "loam blocks your ships." It does not, and
  will not until the precision bar above is met and an owner turns it on.
- Calibration proves recall on a seeded set; it does not prove the reviewer
  catches every real-world flaw class. It is evidence the review is not
  hollow, not a guarantee of completeness.

## Versioning

- Lockstep bump: `docs/ACTIVE_MINOR` 1.9.0 → 1.10.0, the 31 in-scope
  `pyproject.toml` versions 1.9.0 → 1.10.0, and the `loam --version` literal
  1.9.0 → 1.10.0, in one prep commit.
- Out of lockstep this cut: `adversarial-review` (0.1.0, out of graph), the
  one new component, per the standing precedent for new components.
- Zero breaking changes. The release is purely additive: a new component and
  a new skill. No existing surface is removed or changed.

## Standing debt

Shipping the new component out of the install graph and lockstep continues
the pattern of recent minors; folding the accumulated new components in is a
named future item, not permanent drift. The two pos3-workspace channel
changes that rode the same source branch (notification routing and a
message-hook fix) are runtime configuration, not product, and were
deliberately left out of this release.
