# Example plan-doc — Routines-driven background dispatch

**Status:** EXAMPLE / non-load-bearing reference. This plan-doc is illustrative — it demonstrates the composition pattern named in `feedback_routines_runtime_layer.md` (memory feedback) + `docs/plans/v0-4-0-cycle-3-substrate-composition-routines-codereview-outcomes.md` (cycle plan). Not consumed by `loam amend apply` / `loam amend seal`. NOT a real cycle.
**Date authored:** 2026-05-08 (v0.4.0 Cycle 3).
**Composes on:** `feedback_routines_runtime_layer.md` (Routines runtime layer guidance).

---

## §1 — Outcome shape (the example's "why")

This example shows a plan-doc with a step that uses **Claude Code Routines** as the runtime layer for an async background dispatch — the canonical "wake up to PRs ready" pattern. The example uses a hypothetical "nightly typo sweep" cycle: every night, scan the repo for typos in markdown files, open a PR if any are found.

The pattern generalizes to any plan-doc step where the work:

1. Runs without foreground supervision.
2. Lands a discoverable artefact (PR, commit, file) the user reviews on their schedule.
3. Composes on Claude-native runtime rather than ad-hoc background-Bash orchestration.

## §2 — Verified-live Routines invocation surface

Per the v0.4.0 C3 verification at HEAD (`claude --version` `2.1.128`):

- **`claude agents`** subcommand — *"Manage background and configured agents."* Use for ad-hoc background-agent dispatches.
- **`/schedule` SKILL** — *"Create, update, list, or run scheduled remote agents (routines) that execute on a cron schedule."* Use for cron-scheduled "wake up to PRs ready" Routines.

The conference research at `<workspace>/.scratch/claude-output/claude-conference-features-2026-05-06.md` §1 #4 named the verb as `claude routine create`. **That verb does not exist at HEAD.** This example uses the verified-live `/schedule` SKILL surface; if a future release adds the literal `claude routine create` alias, this example's invocation line updates without altering the pattern.

## §3 — Example plan-step shape

Inside a real plan-doc's §4 AC family, a Routines-driven step would look like this:

```
- AC.NTL.1 — Nightly typo sweep runs on cron schedule.
  Invoke `/schedule` SKILL at plan-doc commit time with:
    name: "nightly-typo-sweep"
    schedule: "0 3 * * *"     # 3am every day
    command: "loam typo-scan --open-pr-if-found"
    timeout_minutes: 15
  The Routine runs autonomously; if typos are found, it opens
  a PR labeled `auto/typo-sweep`. The user reviews on their
  schedule. AC.NTL.1 is verified by checking the schedule
  list (`/schedule list`) returns the named entry.
- AC.NTL.2 — Routine completion lands a reviewable PR artefact.
  Outcome-altitude: when the Routine finds typos, the
  resulting PR exists in `gh pr list --label auto/typo-sweep`
  with a non-empty body. When no typos are found, the
  Routine exits 0 without opening a PR.
```

## §4 — Why this composition is correct

Per `feedback_routines_runtime_layer.md`'s "When to compose Routines" rubric, this example matches all three positive conditions:

1. The work runs without holding the foreground session open (cron-scheduled, 3am).
2. The work is resumable (typo scan operates on tracked repo state; subsequent runs see new commits).
3. The completion signal lands as a PR (file artefact) the user reviews at their convenience.

It avoids all three negative conditions:

- Not synchronous-and-short (full repo scan can take >1 min on large repos).
- Doesn't need mid-flight user input (the Routine commits-and-PRs autonomously).
- Has compute (typo-scan tool runs).

## §5 — Graceful degradation

If `/schedule` SKILL is not available in the current session (e.g., older `claude` binary, or a stranger running raw Claude without the schedule SKILL plugin), the plan-doc falls back to:

- **Background-Bash via `&` + completion notification.** The user's loam wrapper (or a hand-rolled cron entry) invokes `claude -p` directly with the typo-scan instruction. Completion notification routes through the same surface (PR / commit) but without the `/schedule` SKILL's lifecycle management.
- **Detection:** the plan-doc's pre-build halt-and-surface step checks `claude --help` + the available-skills list; if `/schedule` isn't present, the dispatch substitutes the fallback inline. Per `graceful-fallthrough-with-detection` SKILL.

## §6 — Composition with other plan-doc surfaces

- **plan-docs-author SKILL** — this example is itself authored per the SKILL's section discipline (skipping the load-bearing §s for non-cycle examples).
- **dispatch-brief-authoring SKILL** — when the Routine runs, its sub-agent dispatch follows the brief shape: principles + WD + scope-only + halt triggers + reply contract. The Routine is dispatch-driven; the brief is the dispatch's payload.
- **`feedback_no_anthropic_api_key.md`** — `/schedule` runs Routines on the same subscription auth as `claude -p`; no API key needed; subscription-only invariant preserved.
- **`feedback_pause-on-Telegram-outage`** — if Telegram is down, the Routine itself runs (no Telegram dependency for cron scheduling), but if the Routine attempts to surface results to the user via Telegram and fails, the pause-on-outage rule applies — the Routine pauses dispatch of further work until Telegram is reachable.

## §7 — Out of scope (this example)

- Real implementation of a "nightly typo sweep" feature — this is illustrative, not a v0.4.0 deliverable.
- Routines orchestration across workspaces — out of scope per `feedback_routines_runtime_layer.md` §"Out of scope".
- Routines + Outcomes runtime stack — Outcomes is API-only; subscription-only loam users can't stack; documented in `docs/design/odd-vs-outcomes.md`.

## §8 — Provenance

- `feedback_routines_runtime_layer.md` — the memory rule this example illustrates.
- `<workspace>/.scratch/claude-output/claude-conference-features-2026-05-06.md` §1 #4 + §3 — Routines as substrate.
- `docs/plans/v0-4-0-cycle-3-substrate-composition-routines-codereview-outcomes.md` §5 — verified-live CLI surface finding.
- `docs/release-roadmap.md` §3 v0.4.0 AC.V040.2 — Routines integration objective.
- `claude --help` empirical verification at HEAD `2.1.128` (2026-05-08).
