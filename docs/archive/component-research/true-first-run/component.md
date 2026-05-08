# Component — True First-Run

**Created:** 2026-04-22 07:16 CDT. **State:** ✅ **COMPLETE — sealed 2026-04-22 08:46 CDT.** Build commit `96f8e17` on pos-v2; SEAL_COMMIT update `e1686e1`. 21 T-criteria green in both shared and memory-system own venvs; all 13 sealed-component regression suites green; build wall-clock ~24 min actual (per `duration_ms: 1431361`) against 60–95 min estimate. Two halt-signals surfaced by the build agent and accepted: H19 SEAL_COMMIT-pin retrofit (same class as `f94d602` / `aab5800`); FUTURE_IDEAS bundled into component commit.

**Phase 5, second component.** Sister to `hands-off-lifecycle`. Closes the gap between "foundation-complete" and "clone-and-open-a-session-and-it-just-works."

---

## Outcome

When a user clones pos-v2 into a fresh directory and opens a Claude Code session in that directory, the full system comes up on its own — no venv creation, no `pip install`, no `.claude/settings.json` authorship, no plist-template substitution performed by the user. The SessionStart hook itself handles all four.

## Context

Surfaced immediately after the hands-off-lifecycle seal when Eve inspected a freshly-cloned workspace and found four genuine first-run gaps the prior component's scope did not close. Owner ruled at 2026-04-22 07:15: *"option b. i want to have the authentic clean start experience."* — committing to a proper component cycle rather than a one-off manual patch on a single owner's machine.

## Load-bearing constraint

The fourth lens (zero manual lifecycle management, ever) is not honoured by hands-off-lifecycle alone. This component closes that gap. The pos-v2 value-proposition depends on it: non-technical users do not know what a venv is, what a plist is, or what `.claude/settings.json` is. The claim that pos-v2 is runnable by them is contingent on this component landing.

## Artifacts

- `research-plan.md` — drafted 2026-04-22; awaiting G1
- `research.md` — not yet produced
- `proposal.md` — not yet produced
- `brief.md` — not yet produced
- `outputs/` — empty

## History

- 2026-04-22 07:16 CDT — component created immediately after hands-off-lifecycle seal. Research plan drafted in-turn. Awaiting G1.
