---
description: "Recover when a pre-commit / pre-push hook fires a violation against the local working tree. Operator-facing walk — distinct from the agent-side audit-finding-triage. Two routes — (a) ratify the violation as a deliberate exception (override commit per the contract-update protocol), or (b) revisit the AC the hook cited (the AC was wrong; tighten / loosen / remove). The walk pins the decision so the persona doesn't bypass-and-forget. Use whenever a local hook (loam pr-safety pre-commit / pre-push, loam amend seal post-checks, or any hook installed by the dev-sdlc plugin or the workspace's CI surface) blocks a commit / push and the persona is the operator deciding what to do next."
---

# hook-violation-recovery

Hooks are the loam-side enforcement of contracts (PR-safety,
sealed-component invariants, audit-trail floor). When a hook
fires, the persona has three failure modes if the recovery
walk isn't codified:

1. **Bypass-and-forget.** `--no-verify` ships the regression;
   the contract is hollowed silently.
2. **Spin on the failure.** Persona retries the same commit
   without understanding why the hook fired; same failure
   loops.
3. **Disable the hook.** The hook surface is removed instead
   of resolving the underlying violation.

This skill replaces those failure modes with a deliberate
two-route walk: ratify the exception OR revisit the AC. Each
route has bookkeeping that prevents silent drift. Distinct
from `audit-finding-triage` (which is the dispatcher-side
response when an agent surfaces a halt-and-surface finding);
this skill is the OPERATOR-side response when the persona is
the one staring at the failed commit.

## What this skill captures

The two-route recovery walk:

```
[Hook fires violation]
        ↓
    [Read hook output — what AC / what surface / what file?]
        ↓
    [Decide: is the violation a real regression, OR is the AC
     too strict / wrong / out of date?]
        ↓
    ┌───────────────────┴───────────────────┐
    ↓                                       ↓
[Route A: Ratify]                     [Route B: Revisit AC]
- The violation is deliberate.        - The AC was wrong / too strict.
- Override commit per                 - Author a contract-update commit
  contract-update protocol.             OR a sealed-amendment cycle to
- Audit-log captures owner +            tighten/loosen/remove the AC.
  rationale + original-AC +           - New AC must pass the smoke gate
  ratification timestamp.               + per-AC verification.
- Re-run hook → passes.               - Re-run hook → passes against
                                        revised contract.
```

The required parts:

1. **Read the hook output FULLY.** Hook violations cite the AC
   (e.g., `AC.PRSG.4`), the surface (file path + line), and the
   reason (e.g., "VERIFIED AC touched without override"). Don't
   skim — the output is the diagnostic.
2. **Test the violation against the operational objective.**
   Did the diff genuinely regress the AC's behaviour? OR is
   the AC too strict (false positive — diff is unrelated to the
   AC's intent)? OR is the AC out of date (the contract drifted
   from the actual behaviour the project supports)?
3. **Choose route A or route B.** No third option. Bypass-and-
   forget is NOT a valid route — `--no-verify` without an
   override-commit + audit-trail entry is a silent contract
   violation.
4. **Route A — Ratify.** The violation is deliberate (e.g., the
   PR is the override-commit that updates the contract). Path:
   - Author the commit with the override-recognition shape (per
     v0.1.9 Cycle 1 protocol): `Loam-Override:` trailer OR
     `contract-update:` commit-message prefix OR `--override`
     flag at gate-invocation time.
   - Audit-log captures (timestamp, owner, rationale,
     original-AC, new-AC, ratification SHA).
   - Re-run the hook → passes (the override-recognition path
     bypasses the gate's HARD-BLOCK).
5. **Route B — Revisit AC.** The AC was wrong. Path:
   - Author a contract-update commit OR a sealed-amendment
     cycle (depending on whether the AC lives in a banded
     contract or in a plan-doc §4).
   - For banded contracts (`<workspace>/.loam/extractions/
     <project>/contract-draft.md`): tighten / loosen / remove
     the AC; re-run the smoke gate; the new AC must satisfy
     per-AC verification.
   - For plan-doc ACs (sealed components): per
     `feedback_loose_AC_text_fix_AC_not_implementation`, when
     impl matches intent and AC text is loose, tighten the AC
     (doc-only) after verifying nothing pending depends on the
     loose reading. Author as a small follow-on amendment, NOT
     `--amend`.
   - Re-run hook against revised contract → passes.
6. **Bookkeeping closes the loop.**
   - Route A: audit-log entry; PR description's
     Override-history section captures the ratification.
   - Route B: amendment cycle's §14 method-decision register
     records the AC change; FIDRAFT entry if the change reveals
     a pattern worth capturing.
7. **Never `--no-verify` without route A or route B.** The
   audit-trail floor requires every contract violation to be
   either ratified or revisited; bypassed-and-forgotten is the
   silent-contract-hollowing failure mode this walk prevents.

## When to use

Trigger conditions:

- A pre-commit hook (loam pr-safety, husky-installed, or
  custom) fires a violation locally and prevents `git commit`.
- A pre-push hook fires a violation and prevents `git push`.
- A `loam amend seal` post-check fires and prevents the seal
  commit from landing.
- A CI workflow (GitHub Actions / GitLab CI / CircleCI) fires
  a gate violation and the persona is locally reproducing the
  failure.
- The persona is reviewing a teammate's hook violation in a
  pairing session (the same recovery walk applies).

Skip when:

- The hook fired correctly + the persona's diff is the actual
  regression to revert (the recovery is `git restore` /
  re-author the diff; no contract walk needed).
- The hook fired due to environment misconfiguration (missing
  dependency, wrong Python version) — fix the environment;
  the contract is fine.
- The hook is a flaky non-loam external surface (e.g., a
  network-dependent linter timing out) — different shape;
  re-run after network recovers; not a contract violation.

## How the persona applies it

1. **Read the hook output FULLY.** Don't `--no-verify` until
   you've understood what AC fired and why.
2. **Identify the cited AC.** Hook output names the AC (e.g.,
   `AC.PRSG.4 — VERIFIED AC touched without override`). Locate
   the AC in the relevant contract (banded contract for
   PR-safety, plan-doc §4 for sealed-component cycles).
3. **Test against the operational objective.** Does the diff
   genuinely regress the AC's behaviour? Three signals:
   - **Reversibility** — is the diff easily revertible if the
     hook is right? High-reversibility diffs lean route A
     (ratify if the diff is deliberate); low-reversibility
     leans route B (probably AC is wrong; revisit).
   - **Blast radius** — narrow diffs (single function) lean
     route A or B by intent; broad diffs (cross-component
     refactor) deserve a slower walk because the contract is
     more likely to be misaligned.
   - **AC confidence band** — VERIFIED ACs (anchored to passing
     tests) lean route A (the AC is solid; the diff is the
     deliberate exception); HYPOTHESISED ACs lean route B (the
     AC is the suspect).
4. **Choose route A or B.**
5. **Route A: author the override commit.**
   - For PR-safety gate: use `Loam-Override:` trailer with
     rationale, OR `contract-update:` prefix, OR `--override`
     flag.
   - The override-recognition path emits an audit-log entry
     automatically.
   - Re-run the hook locally to confirm it passes.
6. **Route B: revisit the AC.**
   - For banded contract: edit the AC entry; re-run smoke
     gate; verify the revised AC.
   - For sealed-component plan-doc AC: author a small
     follow-on amendment cycle that updates §4; tighten /
     loosen / remove per the actual intent.
7. **Close the loop.**
   - Route A: PR description's Override-history section
     captures the ratification; the PR's audit-log excerpt
     section shows the entry.
   - Route B: the amendment cycle's seal commit captures
     the AC change; §14 records the decision.
8. **Never bypass-and-forget.** `--no-verify` without route
   A or B is the failure mode this walk prevents. If route
   A or B feels too heavy for a one-off case, the right
   answer is route A (the override-commit IS the lightweight
   ratification path).

### Decision signals (per M5 conflict-resolution)

The route-A vs route-B decision is signal-driven per
`feedback_principle_conflict_resolution_multi_signal`:

- **AC confidence band (most-load-bearing).** VERIFIED →
  route A more often; HYPOTHESISED → route B more often.
- **Diff intent.** Deliberate behavior change → route A;
  unintended regression → route B if the AC is wrong, or
  revert if the AC is right.
- **Time pressure.** Urgent + reversible + narrow → route A
  is faster; non-urgent → route B's heavier amendment is
  worth doing right.
- **Scope-confidence (F4).** High confidence the AC is right
  → route A. Low confidence → route B.
- **Information asymmetry.** When the operator has context
  the original AC author didn't (e.g., a new operational
  constraint), route B is the documentation surface for the
  new context.

The four-step process from M5: name the conflict (route A
vs route B), name signals, make the call, surface if
non-obvious.

## Graceful degradation

When raw Claude Code without loam pr-safety / loam amend:

- The two-route walk applies to ANY hook surface (husky-
  installed, custom git hooks, CI gates). Substitute
  `Loam-Override:` trailer with the project's local
  override-recognition pattern (e.g., `[skip-ci]`,
  `--no-verify` with a logged rationale, a teammate's
  ratification comment).
- The audit-trail floor's "every violation logged" still
  applies even without the loam audit-log surface — log to
  `CHANGELOG.md`, GitHub issue comment, or Notion doc.
- Detection on fallback: if `--no-verify` is being used as
  the recovery action without ANY ratification surface, the
  graceful degradation has hollowed the contract. Surface
  the silent-bypass risk inline. See
  `graceful-fallthrough-with-detection` for the wider
  pattern.

## Composition

- **`audit-finding-triage` skill** — the dispatcher-side
  mirror. When a build agent surfaces a hook-violation
  finding, the triage routes (in-scope-resolve =
  dispatcher's route A; in-scope-defer = route B with
  follow-on cycle; out-of-scope-FIDRAFT = neither route
  applies cleanly).
- **`loam-amend-cycle` skill** — when route B requires a
  sealed-amendment cycle to update a plan-doc §4 AC, the
  amendment-cycle ladder is the execution surface.
- **`feedback_loose_AC_text_fix_AC_not_implementation`** —
  the canonical case for route B: when impl matches intent
  but AC text is loose, fix the AC (not the impl).
- **`feedback_no_amend_in_agent_dispatches`** — applies in
  route B: AC repair is a NEW corrective amendment, never
  `git commit --amend`.
- **`feedback_locked_design_not_license_for_bad_outcomes`** —
  if the cited AC is a "locked design" producing a bad
  outcome, route B is the right path; "it's the locked
  design" is not a terminator.
- **`feedback_subagent_odd_violation_halt`** — agents must
  halt and surface ODD violations; this skill is what the
  operator does WHEN they halt-and-surface a hook-fire to
  the operator.
- **PR-safety gate (v0.1.9 Cycle 1, sealed `790807d`)** —
  the hook surface this skill most often recovers from. The
  gate's override-recognition protocol IS route A.
- **`graceful-fallthrough-with-detection` skill** — the
  meta-pattern: every fallback path (including the
  bypass-without-ratification non-route) must include
  detection. This skill IS the detection for hook-bypass.

## Out of scope

- The hook installation mechanism — lives in v0.1.9 Cycle 2
  (`0dc557e`) hook installers; this skill assumes hooks are
  already installed.
- The PR-safety gate's per-band decision matrix internals —
  lives in `plugins/dev-sdlc/pr-safety/` source; this skill
  references the protocol but doesn't enumerate the matrix.
- Banded-contract authoring — lives in v0.1.8 Cycle 4a/4b
  ODD-extraction surfaces; this skill assumes a contract
  exists.
- Multi-operator team conventions — when route A or B
  requires teammate ratification, the team's ratification
  protocol (PR review, slack approval) is project-local;
  this skill captures the operator-side single-developer
  walk.
- Bypass under emergency-incident pressure (e.g.,
  production-down recovery) — different threat model;
  surface inline and follow up post-incident with route A
  (post-hoc ratification commit) or route B (incident
  retrospective informs the AC update).
- Hook-flakiness diagnosis — if the hook fires
  intermittently, the issue is the hook's determinism;
  different shape from contract violation; route to
  test-flakiness debugging.
