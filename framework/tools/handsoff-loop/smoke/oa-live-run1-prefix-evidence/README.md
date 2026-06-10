# OA live run 1 (pre-heartbeat-fix) — preserved evidence

First full live run of the assembled general path (2026-06-09
23:14–23:30 CDT, ask: rec-league round-robin scheduler — off the
back-office trio by design). Preserved because two of its outcomes
are load-bearing evidence:

1. **The AC.PRG.OA failure that found a real bug.** Max user-visible
   gap 286.1s (> the 120s heartbeat bound) during the `planning`
   stage: heartbeats originally wrapped only the build leg, so the
   minutes-long research/generation legs ran silent. Fixed in commit
   `60d886a5` (heartbeats wrap all three long legs). This run's
   record is the bug's Tier-0 evidence. Unverifiable claims: 0.

2. **The anti-overfit machinery firing for real.** The generated
   round-robin tool PASSED the primary gate fixture (6 teams, even)
   and FAILED the held-out fixture (5 teams, odd → BYE handling):
   `FAIL: [N2] Round 1: expected 3 matches, got 2`. Terminal:
   honest-negative (attempt-bound after 3 verification-gated
   re-drives), reported straight — exactly the designed behavior the
   June-8 demo faked around. Wall-clock: 923.5s.

Files: `run_record.jsonl` (the narrated/audited record),
`run_summary.json` (full evidence), `final_verify.json` (the
independent check's exits + tails, run-of-origin: this run).
