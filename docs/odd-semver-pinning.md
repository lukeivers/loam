# ODD ↔ SemVer Pinning

**Status:** methodology — names a structural composition that already governs
loam's release shape. Reference, not novel rule.

Both [SemVer policy](release-versioning-policy.md) and [ODD methodology](../plugins/dev-sdlc/docs/odd-methodology.md)
assume the same property but neither states it: **a SemVer minor version is
structurally identical to an ODD-shape work cycle.** The same four slots
appear in both — objective, constraints, acceptance criteria, method left
to the builder — and the failure modes one document warns against are the
failure modes the other prevents. Naming the composition keeps the two
surfaces coherent as loam evolves.

---

## §1 Why this composition matters

Versions are how strangers understand what loam can do. ODD is how loam's
authors know what they're building. If the two surfaces drift — a release
ships features that trace to no named objective, or a minor's notes name
an outcome no AC verified — the version number stops carrying information.
SemVer becomes calendar-shaped; ODD becomes paperwork.

Linking them ensures every minor's name answers a stranger's first question:
*"what can I do with this version that I couldn't do with the last one?"*
And every minor's release-gate answers the second: *"how do I know it works?"*

---

## §2 Structural mapping — the minor as ODD cycle

Each minor release carries:

| Slot | SemVer policy term | ODD methodology term |
|---|---|---|
| Outcome | "objective target — single sentence stating what a user can now do" (§versioning-policy.what-goes-in-a-minor) | Objective (state of the world to make true) |
| Bounds | "backwards-compatible additions only" + loam architectural commitments (subscription-only, no API keys, sealed-component fence) | Constraints (budget, dependency fence, fail-closed direction) |
| Verification | "verifiable conditions for declaring the minor complete" | Acceptance criteria (deterministic, test-shaped) |
| Realisation | which components touch, which features ship | Method (the builder's call) |

Worked example (planned). The next minor's stated objective is *"loam's
documented features work as advertised"* — single outcome sentence per the
versioning policy. As an ODD cycle, that decomposes into ACs of the shape
*"every documented capability X has a release-gate test invoking the
production code path that proves X holds."* The constraint slot inherits
loam-wide architectural commitments (subscription-only auth via `claude -p`;
no Anthropic API key anywhere; sealed-component fence). The method slot —
which docs get audited first, which gaps file as follow-up minors vs.
patches — is the builder's call inside the cycle.

---

## §3 Patches as defect-closure cycles

A patch is itself a small ODD cycle, but with one structural difference:
the patch inherits its parent minor's objective. A patch cannot introduce
new objective. If a "patch" needs new capability to fix, it's a minor.

Worked example. v0.2.5.1 closed three production-path defects Eric
surfaced installing v0.2.5 against rd-automation: F-LEAK (off-limits
directory filenames leaking into synthesis prompts), F-TIMEOUT (180s
synthesis timeout, no override), F-VERIFY-ORPHAN (verify stage halting
on cascade-orphan capabilities). The patch's implicit objective was
"restore v0.2.5's named outcome to working state." Each defect mapped to
one or more new ACs (AC.V025-1.1 through AC.V025-1.5), each backed by
tests including one outcome-altitude integration test against the
rd-automation fixture. No new capability shipped; the patch only closed
defects in the parent's stated outcome.

---

## §4 Outcome-altitude AC requirement at release-gate

The procedural amendment [shipped 2026-05-05](../plugins/dev-sdlc/skills/odd-test-altitude-discipline/SKILL.md)
established that every AC set must include at least one outcome-altitude
AC — verified by a test that invokes the production code path with no
pre-arrangement. At the release-gate, this requirement applies at the
minor level: each minor's HARD smoke must verify the named outcome with a
test that exercises the production CLI/API/dispatch surface a real user
would touch, on real-world inputs, with no monkeypatched stubs and no
pre-staged fixtures the production code would normally produce.

The v0.2.5 trajectory is the canonical instance. Three SOFT smokes against
synthetic fixtures shipped GREEN; the HARD smoke against rd-automation
shipped RED four times in succession, each run excavating a different
production-path defect (F1 PR-safety contract-draft writes; F2 language
detection skipping `framework/`; F8 LLM-emitted VERIFIED bands violating
the two-source rule; F-DESIGN-1/2/3 fixture-PM authoring + extraction-dir
resolution + phantom-subcommand error message). Synthetic-fixture SOFT
smokes never would have surfaced any of them. The outcome-altitude HARD
smoke against a real-world target is the load-bearing release-gate for
every minor, not an optional polish step.

---

## §5 1.0.0 as a global outcome AC

The MAJOR jump from `0` to `1` is itself an ODD-shaped milestone. Its
objective is named in [§versioning-policy.when-1.0.0-ships](release-versioning-policy.md#when-100-ships):
loam reaches a state where (a) all documented features work as advertised,
verified by a stranger cloning the repo and following install instructions;
(b) one real user has shipped real software with loam, not a smoke-test
fixture; (c) loam commits to 6-month backwards-compatibility from ship date;
(d) the plugin contract is stable across the 0.x compatibility window.

Those four criteria are the outcome-altitude ACs for the 1.0.0 cycle. They
cannot be satisfied by adding more capability or by refactoring internals;
they can only be satisfied by the system as a whole behaving the way the
docs claim. The 1.0.0 jump is a quality-bar event, not a calendar event,
because the only way to verify it is by exercising the same production
surfaces a stranger would touch.

---

## §6 Operational consequences

Three concrete effects on day-to-day work:

1. **Release notes shape.** Every line in a minor's release notes maps to
   an AC the cycle closed (ODD §2.5 strict mapping rule, applied to the
   release artefact). No ad-hoc "we also fixed some things" entries; if
   it's worth mentioning, it's worth an AC. Ad-hoc entries indicate code
   that lacks a named contract — the §2.5 reverse-direction failure.

2. **ODD-shaped retrospective on each minor.** When a minor closes, the
   retrospective compares the named outcome against the achieved outcome
   on the same observable axis. Did the named outcome ship? Did the AC
   set verify it at outcome-altitude? Did any defect surface that the
   ACs missed? Defects-discovered-after-release feed forward as new ACs
   in the patch cycle (per §3) or new objectives in a later minor (per
   ODD §4 re-extension).

3. **Discipline at planning time.** When a planned minor's objective
   sentence reads as a feature list — "ship X, Y, and Z" — the planner
   re-extends. The required question is *"what's the outcome ladder X,
   Y, and Z serve?"* If there's a single outcome the three features all
   ladder to, that's the minor's name. If there isn't, the work is two
   minors (or three) and the planning forces an honest split.

The framing "version = objective" forces honest scope. The discipline is
borrowed from ODD §4 re-extension: discovered scope-misalignment is never
buried; it's promoted to a named objective and tracked.

---

## §7 Versioning is itself versioned

The versioning policy doc is mutable. Bumps to its own rules document
themselves as policy revisions, not as silent precedent. Re-extension
discipline applies: a discovered shortcoming in the rules gets promoted
to an explicit revision with a documented rationale, never patched-in-place
without a trail. This document — naming a composition both docs imply —
is itself a doc-level re-extension under that rule.

---

**Authority chain:** [release-versioning-policy.md](release-versioning-policy.md)
governs digit semantics; [odd-methodology.md](../plugins/dev-sdlc/docs/odd-methodology.md)
governs work-cycle shape; [odd-llm-grounding.lean.md](odd-llm-grounding.lean.md)
governs altitude self-checks. This document names the composition; when
the three disagree on mechanics, the relevant authority doc wins.
