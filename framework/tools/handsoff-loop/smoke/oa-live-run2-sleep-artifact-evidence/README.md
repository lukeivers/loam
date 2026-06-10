# OA live run 2 (post-heartbeat-fix) — preserved evidence

Second full live run of the assembled general path (2026-06-09
23:30–23:41 CDT, same rec-league ask as run 1, executed AFTER the
`60d886a5` heartbeat-coverage fix). Preserved because its apparent
AC.PRG.OA failure diagnosed a real measurement bug — in the AUDIT,
not the heartbeat wrapper:

1. **The 415.1s "gap" was 355s of system sleep, not wrapper
   silence.** The audit reported max user-visible gap 415.1s
   (> the 120s bound) during the `planning` stage. Tier-0 evidence
   that no active silence occurred:
   - `run_summary.json`: `wall_clock_s` (monotonic) = **298.7s** vs
     the record's wall-clock span = **651.0s** — a 352.3s deficit
     only OS suspension produces.
   - `pmset_sleep_window.log`: macOS entered **Maintenance Sleep at
     23:32:51 for 355 secs**, DarkWake 23:38:46 — exactly inside the
     planning window (planning narrate 23:31:53 → gate frozen
     23:38:49). 651.0 − 355 ≈ 296 ≈ the 298.7s monotonic run time.
   - Active planning time ≈ 63s — UNDER the 120s bound; no heartbeat
     was due. The heartbeat scheduler runs on the monotonic clock,
     which (like the suspended process itself) does not advance
     during system sleep.

2. **The heartbeat fix is confirmed working in this same run:** the
   building leg's heartbeat fired at exactly 120.0s with the
   post-fix wording ("Still working — progress is actively landing
   on disk (newest artifact mtime 2.5s ago)").

The call (AC.PRG.1's text already scopes the bound to "while work is
active"): the audit measured silence on the wall clock, which counts
OS-suspension as silence — a breach no watching human experienced
and no emitter could physically have prevented (the emitter is
suspended too). Fixed at the implementation: run-record events carry
`ts_mono`; `audit_progress` checks the bound on the monotonic clock
and still reports the wall-clock max gap (`max_gap_wall_s`) so
suspension stays visible, never hidden. The AC text was NOT loosened.

Run 2's other outcome, for the record: terminal **done** — the
generated scheduler tool passed its frozen gate AND the held-out
anti-overfit check this time. Wall-clock 651.0s (355s asleep).

Files: `run_record.jsonl`, `run_summary.json` (run-of-origin: this
run), `pmset_sleep_window.log` (the system power log lines covering
the run window, captured 2026-06-10).
