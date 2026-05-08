---
description: Quick-status check on the current amendment cycle — which commits landed, what's left, current AC coverage, sweep-test result, sealed-component sidecar state. Diagnostic surface when a cycle goes sideways or when a fresh-session persona inherits a partial cycle. Reads the working-tree state (git log, plan-doc §14 backfill, manifest baseline, sidecar SHAs, smoke outcome) and emits a 5–10 line summary. Use when (a) inheriting a partial amendment cycle in a new session, (b) the cycle hit a halt-trigger and the persona needs to assess where to resume, (c) reviewing in-flight progress mid-build.
---

# loam-amend-status-quick

Amendment cycles in loam follow a 5-commit ladder: plan-doc
→ source-edit feat (BASELINE) → manifest+apply → seal → §14
backfill. When the cycle proceeds linearly, status is obvious
from the most recent commit message. But cycles often pause
mid-ladder — halt-triggers fire, sessions end, agents
return findings, the build agent surfaces a question.

A fresh-session persona inheriting a partial cycle, or the
operator returning to a paused build, needs to answer:
"Where am I in the ladder? What landed? What's left? What's
the cycle's progress? Which ACs are satisfied? Did sweep
tests pass last time?"

This skill captures the diagnostic walk to answer those
questions in ~30 seconds without re-reading the entire
plan-doc.

## What this skill captures

The quick-status walk + the summary shape:

```
[Walk]
1. git log -10 --oneline → identify the most recent cycle's
   commits.
2. Read the cycle's manifest baseline: field → know which
   source-edit-feat is the BASELINE.
3. Read the cycle's plan-doc §14 Commit SHAs → know what
   apply / seal / backfill commits have landed.
4. Read the sidecar SEAL_COMMIT for the affected component
   → know what SHA the sealed state is currently pinned to.
5. Run `loam amend apply --dry-run <manifest>` → know if the
   tree is clean post-seal.
6. Walk plan-doc §4 → count satisfied ACs vs total.
7. Walk plan-doc §6 → check smoke-outcome was recorded.

[Summary]
Cycle:        <slug>
Plan doc:     <path> (§14 has N of M Commit SHAs filled)
Source-edit:  <BASELINE SHA from manifest>
Apply:        <APPLY SHA or "not yet">
Seal:         <SEAL SHA or "not yet">
§14 backfill: <BACKFILL SHA or "not yet">
Sidecar:      <component> pinned at <SEAL_COMMIT SHA>
Apply --dry-run: clean / not clean
ACs:          <X> of <Y> satisfied per plan-doc §4
Smoke:        <status from plan-doc §6 or manifest
              smoke_outcome>
Next step:    <derived from ladder position — see decision
              table below>
```

The required parts:

1. **Identify the cycle slug.** From the most recent
   `docs(plans):` / `feat(<comp>):` / `chore(amend):` /
   `chore(seals):` commit messages. Slug is in the commit
   message body.
2. **Identify ladder position.** Which of the 5 commits
   have landed? Walk:
   - Plan-doc commit lands first (`docs(plans):` with the
     plan-doc + manifest).
   - Source-edit feat lands second (`feat(<comp>):` with
     the source changes).
   - Manifest+apply lands third (`chore(amend):` with the
     merged manifest+apply).
   - Seal lands fourth (`chore(seals):` with sidecar +
     narrative).
   - §14 backfill lands fifth (`docs(plans): record <slug>
     commit SHAs in method-decision register`).
3. **Identify ACs satisfied.** Walk plan-doc §4. For each
   AC, check if the corresponding test exists + passes (the
   per-AC test shape per `feedback_dispatch_brief_
   authoring`).
4. **Identify sweep-test result.** Read manifest's
   `smoke_outcome` field (post-seal) OR the plan-doc §6
   smoke section (pre-seal). If the field/section is
   placeholder, sweep didn't run yet.
5. **Identify sidecar SHA.** Read `<component>/tests/
   SEAL_COMMIT` for each component in the cycle's manifest
   `components:` block. The SHA pinned there is the most
   recently sealed state.
6. **Run `loam amend apply --dry-run <manifest>`.** Verifies
   tree-vs-sidecar consistency. Output `clean` means tree
   matches sidecar; `not clean` means working-tree changes
   exist beyond what the sidecar pins.
7. **Derive the next step.** From ladder position:
   - Pre-plan-doc → author plan-doc + manifest (use
     `plan-docs-author` skill).
   - Plan-doc landed, no source-edit → build the source
     edits per §3 fence + §4 ACs.
   - Source-edit landed, no apply → run `loam amend apply`.
   - Apply landed, no seal → run `loam amend seal`.
   - Seal landed, no §14 backfill → backfill apply + seal
     SHAs in plan-doc §14 + master-plan §9.
   - All 5 landed → cycle complete; verify release-level
     smoke if applicable.

### Next-step decision table

| Ladder position | Most-recent commit kind | Next action |
|---|---|---|
| 0 — pre-plan | (any) | author plan-doc + manifest; commit `docs(plans):` |
| 1 — plan-doc only | `docs(plans):` for slug | build source edits in fence; commit `feat(<comp>):` |
| 2 — source-edit | `feat(<comp>):` (BASELINE) | update manifest baseline if placeholder; run `loam amend apply` |
| 3 — apply | `chore(amend):` for slug | run `loam amend seal` |
| 4 — seal | `chore(seals):` for slug | backfill plan-doc §14 + master-plan §9 |
| 5 — backfill done | `docs(plans): record ... §9` | cycle complete; release-level smoke if final cycle |
| halt-state | (any halt-trigger surface) | route per `audit-finding-triage` |

## When to use

Trigger conditions:

- A new session inherits an in-flight amendment cycle from a
  prior session — first action is the quick-status walk.
- The cycle hit a halt-trigger mid-build and the persona
  needs to assess where to resume.
- The build agent returned with halt-and-surface findings
  and the dispatcher needs to size the remaining work.
- Reviewing a PR that includes amendment-cycle commits —
  verify the ladder is complete + correct before approving.
- An audit / retrospective on a closed cycle — verify all
  5 commits landed in correct order.
- Diagnosing why `loam amend apply` or `loam amend seal`
  is failing — quick-status surfaces the upstream gap (e.g.,
  manifest baseline still placeholder, sidecar drift).

Skip when:

- The cycle is fully complete (all 5 commits landed +
  release-level smoke green) — full-status would be more
  appropriate (master-plan §9 row + release-level rollup
  status).
- The cycle hasn't started (no plan-doc) — different shape;
  start with `plan-docs-author` skill.
- The session is mid-build with no halt — the persona is
  in flow; quick-status interrupts unnecessarily. Apply at
  resume points, not mid-step.

## How the persona applies it

1. **Identify the slug.** `git log -10 --oneline` → look for
   the most recent cycle slug in commit messages. Or, if
   inheriting a session with context, the slug may be in
   the dispatch brief / status file.
2. **Read the manifest's `baseline:` field.** `cat docs/
   rebuild/plans/<slug>.manifest.yaml | grep baseline`.
   Placeholder string → source-edit feat hasn't landed yet.
   Real SHA → source-edit landed.
3. **Read the plan-doc §14 Commit SHAs section.** `grep -A
   20 "Commit SHAs" docs/plans/<slug>.md`. Each line
   either has a SHA or `<TBD>`.
4. **Identify which commits landed.** `git log --oneline -20
   --grep=<slug>` returns every commit referencing the slug.
   Match against the 5-commit ladder.
5. **Read the sidecar SEAL_COMMIT.** `cat <component>/tests/
   SEAL_COMMIT` for each component in `manifest.components`.
   The SHA pinned there is the sealed state.
6. **Run `loam amend apply --dry-run <manifest>`.** Output
   tells you if the tree is clean (matches sidecar) or
   not (has staged-but-not-sealed changes).
7. **Walk plan-doc §4.** Count ACs; for each, check the
   per-AC test file exists at `<component>/tests/test_AC_
   <FAMILY>_<index>_*.py`. If pytest is available, run
   the per-AC tests to verify pass/fail.
8. **Walk plan-doc §6 + manifest smoke_outcome.**
   Pre-seal: §6 has the planned dimensions but no
   outcome. Post-seal: manifest's smoke_outcome captures
   the result.
9. **Emit the summary.** ~10 lines. Cycle slug + ladder
   position + AC coverage + sweep status + next step.
   Inline in the chat reply OR write to status file at
   `<workspace>/.scratch/claude-output/<slug>-status-
   <date>.md`.
10. **Apply the next-step decision table.** Map ladder
    position to next action. If a halt-trigger surface
    appears, route per `audit-finding-triage`.

### Heuristics for partial-cycle recovery

When inheriting a cycle mid-flight, common gaps:

- **Manifest baseline placeholder + source-edit landed.**
  → update manifest's `baseline:` field with the
  source-edit SHA; commit as a small `docs(plans):`
  follow-up; THEN run `loam amend apply`.
- **Apply landed but seal failed.** → check sweep-test
  output; the seal command's output names the failing
  test. Fix the test (in a new corrective commit, never
  `--amend`); re-run seal.
- **Seal landed but §14 backfill missing.** → just author
  the §14 backfill commit; nothing else needed.
- **Plan-doc landed, source-edit landed, but no apply
  attempted.** → run `loam amend validate` first; if
  validation fails, fix the manifest in a follow-up
  commit; THEN apply.
- **Multiple cycle slugs visible in recent commits.** →
  check whether the cycles are independent (different
  components) or one is the master plan + cycles. If
  master plan, the per-cycle ladders are independent;
  apply this skill per-cycle.

## Graceful degradation

When raw Claude Code without loam dev-sdlc plugin:

- The 5-commit ladder doesn't apply (no `loam amend
  apply` / `seal`); substitute with the project's
  equivalent rollup ritual (CHANGELOG.md update +
  feature-flag flip + release tag).
- The quick-status walk still applies: which commits
  landed, what's left, current AC coverage. Substitute
  sidecar / manifest reads with whatever paper-trail
  surface the project uses.
- The detection clause: if the project lacks ANY
  paper-trail surface, the quick-status walk degrades
  to "what does git log say?" — surface this gap
  inline. See `graceful-fallthrough-with-detection`.

## Composition

- **`loam-amend-cycle` skill** — the wider ladder. This
  skill is the diagnostic against the ladder; that skill
  is the construction of the ladder. Use this skill to
  observe ladder state; use that skill to advance ladder
  state.
- **`audit-finding-triage` skill** — when quick-status
  surfaces a halt-state, the triage routes the recovery.
- **`hook-violation-recovery` skill** — when the
  diagnostic surfaces a hook firing as the halt cause,
  hook-violation-recovery is the route.
- **`graceful-fallthrough-with-detection` skill** — the
  meta-pattern that the diagnostic walk applies (the
  walk IS the detection surface for "cycle pauses
  silently").
- **`plan-docs-author` skill** — quick-status is read-
  only against the plan-doc; if the plan-doc itself is
  the gap, plan-docs-author is the next-step surface.
- **`seal-narrative-writer` skill** — quick-status reads
  the post-seal narrative; that skill authors it.
- **`feedback_specific_claims_verified_or_marked_guess`** —
  the quick-status output must distinguish "verified
  empirically" (read from disk just now) from "stated
  in plan-doc but not re-checked"; conflating them is
  the calibration gap that skill prevents.
- **`feedback_no_amend_in_agent_dispatches`** — if
  quick-status reveals a need for corrective action
  (manifest baseline drift, plan-doc typo), the
  correction is a NEW commit, never `--amend`.

## Out of scope

- Full cycle audit (every test ever run, every dispatch
  message, every halt-and-surface finding) — different
  surface; this skill is the 30-second walk, not the
  forensic deep-dive.
- Cross-cycle status (release-level rollup across
  multiple cycles) — lives in master-plan §9; this skill
  is per-cycle.
- The mechanics of `loam amend apply` / `loam amend
  seal` themselves — lives in `loam-amend-cycle`; this
  skill READS the artefacts those commands produce.
- Sealed-component sidecar internals (how SEAL_COMMIT
  is structured, tests/SEAL_COMMIT.notes shape) — lives
  in dev-sdlc methodology; this skill reads the SHA but
  doesn't enumerate the file format.
- Master-plan-level dispatch tracking — different
  surface; this skill is single-cycle scope.
- AC-level test execution under multi-component cycles
  — when the cycle spans 2+ components, the AC walk
  applies per-component; this skill names that but
  doesn't enumerate multi-component edge cases.
- Recovery from corrupted git state (detached HEAD,
  unmerged paths, dirty stash) — different shape;
  surface the corruption inline + route to git-recovery
  procedures (out-of-scope for amendment-cycle status).
