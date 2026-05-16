# Hands-off loop — real build (in-repo build-spine)

**Class:** ODD-shaped build plan + §14 SHA register.
**Binding contract:** `pos3/workspace/.scratch/claude-output/handsoff-loop-real-build-plan-2026-05-16.md`
(authored 2026-05-16, owner-greenlit, D-UNIT ratified Telegram 11391).
This in-repo doc is the ODD-faithful build-spine of that contract; the
contract is authoritative for objective/fence/ACs and is not re-derived
here.

**Builds on (do NOT re-prove — AC.FOUND.0):**
`pos3/.../handsoff-loop-minimal-probe-2026-05-16.md` — Tier-0
verified-empirical: the decompose → scoped-dispatch → judge loop LIVES at
unit scale. This build composes ON that result and adds NO step that
re-proves it.

**Claude-surface ground truth:**
`pos3/.../claude-code-primitive-surface-2026-05-16.md` (binary 2.1.143;
`/goal` real since v2.1.139; `--output-format json` present; `claude -p`
sub-agent is loam's NO-API-KEY dispatch primitive).

**Prime objective it ladders to:** `framework/docs/VALUE_PROPOSITION.md`
(the two tests — primary-persona translation-burden + harness toolkit).

---

## §1 — Objective

Build the real orchestrated hands-off loop: a non-technical user states
intent in plain language, walks away, comes back to real verified work —
the loop being *loam's own build methodology run for the user* (plan →
decompose into scoped sub-tasks → dispatch → judge against frozen
acceptance → honest done/dead verdict), packaged so the primary persona
invokes it as one capability. The proven core (probe §6) is in scope as
foundation, **out of scope as a thing to re-prove (AC.FOUND.0)**.

## §2 — Fence (sealed-component)

Seal anchor: **`workspace-bootstrap`** (`framework/workspace-bootstrap/
tests/test_no_sealed_amendments.py`, BASELINE `356ec07`). Its LIVE
seal-test admits every surface this build touches:
`plugins/loam-skills/` (the persona-invocable skill bundle —
AC.A.1), `framework/hands-off-lifecycle/` + `/seals/` (component +
narrative target), `framework/tools/` (executable orchestration + judge
+ intake scripts), `docs/plans/` + `docs/STATE.md` (plan + backfill).

Anchor rationale (autonomously resolved per operational-objective test,
recorded for the register): the `loam-skills` plugin's *own* seal-test is
stale — it predates the repo-wide `docs/rebuild/`→`docs/` path migration
and would false-fail on `docs/plans/`. The objective requires the
orchestrator be *skill-shaped + persona-invocable* (satisfied by the
bundle living under the `workspace-bootstrap`-admitted
`plugins/loam-skills/` prefix), NOT that `loam-skills` be the seal
anchor. Mirrors the `subloam-driver-fix` precedent that sealed cleanly
against `workspace-bootstrap` on this exact branch tip.

In scope: a packaged orchestration mechanism (skill-shaped); an intake
leg (plain-language intent → machine-checkable acceptance + one approval
gate); the two phase end-tests and their honest-negative outcomes.

Out of scope (explicit): re-proving the core decompose→dispatch→judge
loop (AC.FOUND.0); scale-hardening beyond what each phase end-test
requires; ProgramBench / subloam-driver; canonical `main` mutation /
push / publish / tag (LOCAL SEAL ONLY).

## §3 — Acceptance ladder (verbatim from the binding contract §3)

Outcome-shape; each carries the contract's satisfiability note. The
honest-negative is a first-class AC-satisfying outcome for every
phase-gating AC by construction.

- **AC.FOUND.0** — Build treats the probe core-loop result as
  established; no AC/sub-task/test re-proves decompose→dispatch→judge at
  unit scale. *Fence guard — verifies an absence.*
- **AC.A.1** — Packaged invocability: orchestration invocable by the
  persona as one capability (no human hand-driving decompose/dispatch/
  judge), demonstrated on a real non-toy task of probe class-or-harder.
- **AC.A.2** — Frozen unseen done: machine-checkable acceptance authored
  + frozen + hash-pinned BEFORE any sub-agent runs; seen by no sub-agent
  and no per-sub-task judge — carried THROUGH the packaging.
- **AC.A.3** — Independent + adversarial verification: the "done" verdict
  is an independent tool-executing check on the produced artefact PLUS an
  anti-overfit check on held-out inputs absent from every brief + judge —
  carried through the packaging.
- **AC.A.4** — Fidelity verdict (Phase A end-test): definite,
  evidence-backed verdict on *"does the packaged mechanism orchestrate as
  cleanly as the hand-run probe?"* on named dimensions ≥ (i) reached
  frozen done without human loop-driving; (ii) no silent regression
  across composed sub-tasks; (iii) honest-negative still fires when a
  sub-task can't be done; (iv) cost/wall-clock within the stated band. A
  definite negative is plan-success, reported straight, never retried.
- **AC.B.1** — Fuzzy-intent input: tested on a genuinely under-specified
  plain-language intent (not the probe's frozen spec); the
  under-specification documented.
- **AC.B.2** — Elicit-the-minimum gate: where intent is too thin, elicit
  only the missing decisions in plain language, bounded so the user is
  not turned into a spec author.
- **AC.B.3** — Plain-language acceptance + exactly one plain-English
  approval gate before any build; no jargon/AC-IDs/spec-syntax surfaced.
- **AC.B.4** — Derived-done machine-checkable AND faithful: independent
  check that the derived acceptance, if met, satisfies a reasonable
  reading of the original ask (guards checkable-but-wrong).
- **AC.B.5** — Intake verdict (Phase B end-test): definite,
  evidence-backed verdict on *"can fuzzy plain-language intent be turned
  into a faithful machine-checkable done reliably enough?"* on named
  dimensions (i)–(iv). A definite negative is plan-success, reported
  straight, never retried. (Contract §10 flags this the risk most likely
  to retire negative — expected-possible, the plan working.)
- **AC.C.1** — End-to-end hands-off, **gated** on A and B both positive.
  If either retired negative this AC is *not attempted* — gated, not
  failed.
- **AC.HL.S** — Seal-diff window: BASELINE..seal touches only
  `workspace-bootstrap`-admitted surfaces (fence integrity).

## §4 — Phase sequencing + honest-negative discipline

```
Foundation (probe §6, asserted)  →  Phase A  →  Phase B  →  Tier C
   [verified, NOT re-run]          (fidelity)  (intent→done)  (gated)
                                       │            │
                                       ▼            ▼
                              §10.5 honest verdict  §10.5 honest verdict
                              (pos OR neg = plan    (pos OR neg = plan
                               success; NO retry)    success; NO retry)
```

A before B (B's intake feeds the loop A packages). If A retires negative,
B still runs against the probe-proven hand-run core. Gating is Tier C
only. Every phase-gating AC is constructed so a definite negative
*satisfies* it — a builder physically cannot convert this to
build-and-assume without rewriting the ACs.

## §5 — Named decisions (resolved — do not reopen)

- **D-UNIT** (RATIFIED, Telegram 11391): one unit = one user-approved
  plain-language objective with one frozen machine-checkable acceptance
  set; the loop decomposes internally into scoped sub-tasks but the unit
  the user sees/approves/is-judged-on is the whole objective.
- **D-COST-BAND** (ADOPTED): $2–8 / ≤20 min sub-agent wall-clock per
  phase end-test; JSON cost-accounting ENABLED (`--output-format json`)
  so cost is measured not estimated — closes the probe's instrumentation
  gap. Tunable.
- **D-NEG-DEPTH** (ADOPTED): a negative verdict names the failure class +
  cites evidence (dimension, observation); it does NOT root-cause or
  propose a fix.

## §6 — Build method (builder's call, ODD §2.5 — every artefact → a named AC)

Method is the builder's; this records it for the register. Surfaces:

- `framework/tools/handsoff-loop/` — executable orchestration package
  (`orchestrator.py` decompose→dispatch→judge driver composing the
  probe-proven mechanism; `intake.py` intent→checkable-done leg;
  `verify.py` frozen-unseen independent + anti-overfit judge;
  `goal_drive.py` the `/goal`-under-`-p` drive/stop leg wiring;
  `cli.py`). → AC.A.1/.2/.3, AC.B.1–.4.
- `plugins/loam-skills/skills/handsoff-loop/SKILL.md` — the
  persona-invocable packaging (auto-surfaces; one capability;
  delegates to the tools package). → AC.A.1.
- `framework/hands-off-lifecycle/tests/test_AC_HL_*.py` — one test file
  per AC; deterministic structural ACs run in the seal sweep; the two
  phase end-tests (AC.A.4, AC.B.5) are real-`claude -p` driven and
  produce captured verdict tables. → every AC.
- `framework/hands-off-lifecycle/seals/SEAL_COMMIT.handsoff-loop-real-build`
  — seal narrative.

`/goal` composition (Lens-1, contract §7): `/goal` drives the
keep-going-until-done leg under `claude -p` (condition ≤4,000 chars);
loam's tool-executing `verify.py` decides — its surfaced exit code is
what `/goal`'s Haiku transcript-only evaluator keys off, never sub-agent
prose. `/goal` drives; the loam-built independent check decides. The
phase-A end-test AC.A.4(i) is the exact test of whether this composition
holds in the packaged mechanism.

## §7 — ODD self-check

Every AC outcome-shape + satisfiability-noted (contract §3). Every AC
ladders to a named VALUE_PROPOSITION test. Honest-negative structurally
AC-satisfying, not an exception. Fence explicit; re-proving the core
named a scope violation (AC.FOUND.0). No method-in-AC.

## §8 — In-flight halt triggers (contract halt-and-surface)

1. Boundedness premise breaks (a phase needs architecture, not the
   bounded work the plan asserts) → §10.5 finding, HALT, surface.
2. ODD violation in this work OR surrounding code beyond what the plan
   names → name it (file:line), do not extend.
3. Canonical `main` mismatched/reverted, frozen-acceptance integrity
   broken, amend ritual cannot proceed cleanly → HALT, report.
4. A phase end-test cannot be run honestly (env blocks real sub-agent
   dispatch / real verification) → HALT, report; no weaker proxy.

## §14 — Method-decision register + commit SHAs

Method decisions: D-UNIT/D-COST-BAND/D-NEG-DEPTH per §5 (resolved
upstream). Anchor-selection decision recorded in §2.

### Commit SHAs

*(Backfilled by `loam amend seal --plan-doc` after the seal commit
lands.)*
